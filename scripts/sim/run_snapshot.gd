class_name RunSnapshot
extends RefCounted
## A run frozen between waves, as plain data that fits in a save slot: what the player built, the
## gold, lives and skill web, the heroes on the field and how much of the enemy base still stands.
##
## A run is only ever frozen in a break, while nothing walks the board. Game keeps the last break's
## snapshot, so a save made during a wave goes back to the break before it.
## Enemies, shots and effects in flight are never stored. Thawing builds a fresh RunSim from the same
## stage or map and puts it all back, ready for the player to start the next wave.
##
## Everything is stored by id, so a save still loads after an update changes numbers. A tower whose
## kind no longer exists, or whose cell is no longer free, is sold back for what it cost.

const VERSION := 1
## A tower's timers that run on from one wave into the next: its attack cooldown, a boss's silence and
## the horde's fog, nets and eclipses. Kept by name, so one that goes away in an update is skipped.
const TOWER_TIMERS: Array[String] = ["cooldown", "silenced", "fog_left", "fog", "net_left", "net", "eclipse_left",
		"eclipse"]


## What a run looks like now. Call it in a break: during a wave, what walks the board is lost.
static func capture(sim: RunSim) -> Dictionary:
	var config := sim.config
	var towers: Array = []
	for tower in sim.towers:
		var entry := {
			"id": tower.id,
			"cell": [tower.cell.x, tower.cell.y],
			"kills": tower.kills,
			"damage_dealt": tower.damage_dealt,
			"shots": tower.shots,
		}
		for timer in TOWER_TIMERS:
			var value: Variant = tower.get(timer)
			if value is float and value != 0.0:
				entry[timer] = value
		if tower.is_hero():
			entry["hero"] = String(tower.hero.id)
			entry["hero_level"] = tower.hero_level
			entry["ability_cooldown"] = tower.ability_cooldown
			entry["moved"] = tower.moved_this_break
		else:
			entry["type"] = String(tower.data.id)
			entry["level"] = tower.level
			entry["ascendancy"] = String(tower.ascendancy.id) if tower.ascendancy != null else ""
			entry["price_paid"] = tower.price_paid
			entry["type_price"] = tower.type_price
		towers.append(entry)
	var party: Array[String] = []
	for hero in sim.party:
		party.append(String(hero.id))
	var structures: Array = []
	for structure in sim.structures:
		structures.append({"health": structure.health, "alive": structure.alive})
	var closed: Array[int] = []
	for lane: int in sim._closed_lanes:
		closed.append(lane)
	return {
		"version": VERSION,
		"stage": String(config.stage.id) if config.stage != null else "",
		"map": String(config.map.id) if config.map != null else "",
		"difficulty": String(config.difficulty.id) if config.difficulty != null else "",
		"endless": sim.is_endless(),
		"wave_index": sim.wave_index,
		"next_id": sim._next_id,
		"lane_turn": sim._spawner._lane_turn,
		"gold": sim.gold,
		"lives": sim.lives,
		"starting_lives": sim.starting_lives,
		"kills": sim.kills,
		"leaks": sim.leaks,
		"gold_earned": sim.gold_earned,
		"break_time_left": sim.break_time_left if sim.state == RunSim.State.BUILDING else -1.0,
		"tree": {
			"points": sim.tree.points,
			"nodes": _strings(sim.tree.allocated_ids()),
			"taken_this_break": _strings(sim._taken_this_break.keys()),
		},
		"party": party,
		"towers": towers,
		"skill_cooldowns": _string_keys(sim._skill_cooldowns),
		"skill_time": _string_keys(sim._skill_time),
		"skill_levels": _string_keys(sim.skill_levels),
		"structures": structures,
		"structure_phase": sim.structure_phase,
		"citadel_fallen": sim.citadel_fallen,
		"closed_lanes": closed,
	}


## The wave the run goes on from once thawed (1-based), for slot labels.
static func wave_number(data: Dictionary) -> int:
	return int(data.get("wave_index", 0)) + 1


## Puts a stored run back into a fresh RunSim built from the same stage or map. The sim waits in a
## break for the player to start the wave. Returns the gold paid back for towers that could not be
## put back (0 when everything fitted), or -1 if the data is not a run at all.
static func restore(sim: RunSim, data: Dictionary) -> int:
	if not data.has("wave_index") or not data.get("towers") is Array:
		return -1
	var config := sim.config
	sim.state = RunSim.State.BUILDING
	var last := sim.total_waves() - 1 if not sim.is_assault() else 1 << 20
	sim.wave_index = clampi(_int(data, "wave_index"), 0, maxi(0, last))
	sim.gold = maxi(0, _int(data, "gold"))
	sim.lives = maxi(1, _int(data, "lives", sim.lives))
	sim.starting_lives = maxi(sim.lives, _int(data, "starting_lives", sim.starting_lives))
	sim.kills = maxi(0, _int(data, "kills"))
	sim.leaks = maxi(0, _int(data, "leaks"))
	sim.gold_earned = maxi(0, _int(data, "gold_earned"))
	var wait := float(data.get("break_time_left", -1.0))
	sim.break_time_left = wait if wait > 0.0 else -1.0

	# The skill web: take the stored nodes in any order that links up, then set the points left.
	var tree_data: Dictionary = data.get("tree", {}) if data.get("tree") is Dictionary else {}
	sim.tree.points = 1 << 30
	sim.tree.restore(_names(tree_data.get("nodes", [])))
	sim.tree.points = maxi(0, _int(tree_data, "points"))
	sim._taken_this_break.clear()
	for id in _names(tree_data.get("taken_this_break", [])):
		if sim.tree.is_allocated(id):
			sim._taken_this_break[id] = true

	# Heroes who joined during the run come back to the party first, so their towers can follow.
	var known: Array[HeroData] = []
	known.append_array(config.heroes)
	known.append_array(config.arriving_heroes)
	for id in _names(data.get("party", [])):
		for hero in known:
			if hero != null and hero.id == id and not sim.party.has(hero) and sim.party.size() < HeroData.MAX_PARTY:
				sim.party.append(hero)

	var refund := 0
	for entry: Variant in data.get("towers", []):
		if entry is Dictionary:
			refund += _restore_tower(sim, entry)
	sim.gold += refund
	# Ids decide ties between equal targets, so the run goes on with the ids it had.
	sim._next_id = maxi(sim._next_id, _int(data, "next_id"))
	# Waves that share their packs out over the roads carry on from the road the last one ended on.
	sim._spawner._lane_turn = clampi(_int(data, "lane_turn"), 0, maxi(0, sim.lane_curves.size() - 1))

	for id: Variant in _dict(data, "skill_cooldowns"):
		if config.skills.has(StringName(id)):
			sim._skill_cooldowns[StringName(id)] = maxf(0.0, float(data["skill_cooldowns"][id]))
	for id: Variant in _dict(data, "skill_time"):
		if config.skills.has(StringName(id)) and float(data["skill_time"][id]) > 0.0:
			sim._skill_time[StringName(id)] = float(data["skill_time"][id])
	# Skill levels bought with gold (saves from before levels existed have none: every skill at 1).
	for id: Variant in _dict(data, "skill_levels"):
		var skill: SkillData = config.skills.get(StringName(id))
		if skill != null:
			sim.skill_levels[skill.id] = clampi(int(data["skill_levels"][id]), 1, skill.max_level())
	for id: StringName in sim._skill_time:
		sim._skill_mods[id] = sim._scaled_modifiers(config.skills[id], sim.skill_level(id))

	var stored: Variant = data.get("structures", [])
	if stored is Array:
		for i in mini(stored.size(), sim.structures.size()):
			var entry: Variant = stored[i]
			if not entry is Dictionary:
				continue
			var structure := sim.structures[i]
			structure.health = clampf(float(entry.get("health", structure.health)), 0.0, structure.max_health)
			if entry.get("alive", true) == false or structure.health <= 0.0:
				structure.alive = false
				structure.health = 0.0
				for cell: Vector2i in sim._structure_cells.keys():
					if sim._structure_cells[cell] == structure:
						sim._structure_cells.erase(cell)
	sim.structure_phase = maxi(1, _int(data, "structure_phase", 1))
	sim.citadel_fallen = data.get("citadel_fallen", false) == true
	var closed: Variant = data.get("closed_lanes", [])
	if closed is Array:
		for lane: Variant in closed:
			if (lane is int or lane is float) and int(lane) >= 0 and int(lane) < sim.lane_curves.size():
				sim._closed_lanes[int(lane)] = true
	sim._refresh_modifiers()
	sim.changed.emit()
	return refund


## Puts one tower or hero back. Returns the gold to pay back when it cannot stand any more.
static func _restore_tower(sim: RunSim, entry: Dictionary) -> int:
	var config := sim.config
	var cell_data: Variant = entry.get("cell", [])
	if not cell_data is Array or cell_data.size() < 2:
		return _paid(entry)
	var cell := Vector2i(int(cell_data[0]), int(cell_data[1]))
	var free := config.map.is_inside(cell) and not sim.is_path(cell) and sim.tower_at(cell) == null \
			and sim.landmark_at(cell) == null and not sim._structure_cells.has(cell)
	var hero_id := StringName(str(entry.get("hero", "")))
	if not hero_id.is_empty():
		var hero := sim.hero_data(hero_id)
		if hero == null or not free or sim.hero_tower(hero_id) != null:
			return 0
		var tower := sim.summon_hero(hero_id, cell)
		if tower == null:
			return 0
		tower.hero_level = clampi(_int(entry, "hero_level", 1), 1, HeroData.MAX_LEVEL)
		tower.ability_cooldown = maxf(0.0, float(entry.get("ability_cooldown", 0.0)))
		tower.moved_this_break = entry.get("moved", false) == true
		_restore_record(tower, entry)
		return 0
	var data: TowerData = config.towers.get(StringName(str(entry.get("type", ""))))
	if data == null or not free:
		return _paid(entry)
	var indices: Array[int] = []
	for element_id in data.elements:
		indices.append(config.element_index(element_id))
	var type_price := maxi(1, _int(entry, "type_price", sim.tower_price(data.id)))
	var tower := SimTower.new(sim._new_id(), data, cell, config.map.cell_center(cell), type_price, indices)
	tower.price_paid = maxi(type_price, _int(entry, "price_paid", type_price))
	tower.level = clampi(_int(entry, "level", 1), 1, SimTower.MAX_LEVEL)
	var ascendancy_id := StringName(str(entry.get("ascendancy", "")))
	if not ascendancy_id.is_empty() and tower.level >= SimTower.MAX_LEVEL:
		tower.ascendancy = data.ascendancy(ascendancy_id)
	_restore_record(tower, entry)
	sim.towers.append(tower)
	sim._tower_at[cell] = tower
	return 0


static func _restore_record(tower: SimTower, entry: Dictionary) -> void:
	if entry.get("id") is int or entry.get("id") is float:
		tower.id = int(entry["id"])
	for timer in TOWER_TIMERS:
		var value: Variant = entry.get(timer)
		if (value is float or value is int) and tower.get(timer) is float:
			tower.set(timer, float(value))
	tower.kills = maxi(0, _int(entry, "kills"))
	tower.damage_dealt = maxf(0.0, float(entry.get("damage_dealt", 0.0)))
	tower.shots = maxi(0, _int(entry, "shots"))


## What a tower that cannot come back is worth: everything paid for it.
static func _paid(entry: Dictionary) -> int:
	return maxi(0, _int(entry, "price_paid"))


static func _int(data: Dictionary, key: String, fallback: int = 0) -> int:
	var value: Variant = data.get(key, fallback)
	return int(value) if value is int or value is float else fallback


static func _dict(data: Dictionary, key: String) -> Dictionary:
	var value: Variant = data.get(key, {})
	return value if value is Dictionary else {}


static func _names(source: Variant) -> Array[StringName]:
	var result: Array[StringName] = []
	if source is Array:
		for id: Variant in source:
			if id is String and not (id as String).is_empty():
				result.append(StringName(id))
	return result


static func _strings(ids: Array) -> Array[String]:
	var result: Array[String] = []
	for id: Variant in ids:
		result.append(String(id))
	return result


static func _string_keys(source: Dictionary) -> Dictionary:
	var result := {}
	for id: Variant in source:
		result[String(id)] = source[id]
	return result
