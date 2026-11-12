class_name AutoPlayer
extends RefCounted
## A scripted player that plays the way a careful person would: it takes nodes in a set order,
## builds where a tower covers the most road, levels a well-placed tower when that buys more than
## another tower would, and casts every skill it has when there is a crowd to hit. Tests use it to
## check that a full run can be won, the campaign is tuned against it, and the game runs it with
## the --autoplay flag to record footage without a human.

const DEFAULT_NODES: Array[StringName] = [
	&"fire_entry", &"storm_entry", &"fire_cw", &"storm_ccw", &"bridge_plasma",
	&"fire_core", &"storm_core", &"fire_notable", &"storm_cw", &"storm_notable",
	&"nature_entry", &"nature_ccw", &"bridge_thornstorm", &"fire_ccw",
	&"nature_core", &"nature_notable", &"nature_cw",
]
const DEFAULT_TOWERS: Array[StringName] = [
	&"hybrid_plasma", &"fire_brazier", &"storm_spire", &"hybrid_thornstorm", &"nature_thornbush",
]
## Spacing of the points used to measure how much path a cell covers.
const PATH_SAMPLE_SPACING := 32.0
## Simulation steps between looks at the skills, so the bot costs little during a wave.
const SKILL_CHECK_STEPS := 12
## Enemies an aimed skill should reach, and enemies on the board before a skill for the whole
## board is worth casting. A boss is always worth it.
const SKILL_CROWD := 4
const SKILL_BOARD_CROWD := 6
## A skill that pushes enemies back is kept for when one is this far along its road.
const SKILL_PUSH_PROGRESS := 0.65
## Simulation steps between building rounds while waves roll in without a break.
const BUILD_IN_WAVE_STEPS := 120
## What the bot expects an ascension to add to a tower's damage, as a share.
const ASCEND_GAIN := 0.35

var sim: RunSim
## Tree nodes to take, in order. A node that cannot be taken yet is retried next time.
var node_priority: Array[StringName] = []
## Towers to build, best first. The bot builds the first unlocked one it can afford.
var tower_priority: Array[StringName] = []
var max_towers := 40
## Turn off to make the bot play like a beginner: no levels, no skills.
var upgrades := true
var skills := true
## Turn on to have the bot buy skill levels with gold it can spare (it keeps half for towers).
## Off by default, so the campaign is tuned against towers and plain skills.
var skill_upgrades := false
## Gold the bot spent on skill levels this run.
var skill_gold := 0
## Turn off to leave the heroes unsummoned.
var heroes := true
## Turn off to stop the bot at the top level instead of ascending.
var ascends := true
## Turn off to leave the counter-attack's units unmustered.
var musters := true
## The order the bot musters troops in the counter-attack, round and round. Champions come first
## whenever one is ready.
var muster_plan: Array[StringName] = [
	&"footman", &"crossbowman", &"pikeman", &"tide_priestess", &"ironbreaker", &"banner_bearer",
	&"battering_ram", &"footman", &"root_archer", &"ember_knight", &"lantern_cleric", &"sunstone_catapult",
	&"spire_golem", &"firebrand", &"pearl_marine", &"stormcaller", &"gale_lancer", &"griffin_rider",
	&"veil_blade", &"hollow_hunter", &"warhound",
]
## The road the bot marches on. Its army stays together.
var muster_lane := 0
## How far the bot trusts an upgrade against a new tower. At 1 it takes its own sums at face value;
## lower leans toward building more towers.
var upgrade_bias := 0.6

var _path_samples := PackedVector2Array()
var _caves_seen := 0
var _coverage_cache: Dictionary[Vector3i, int] = {}
var _skill_wait := 0
var _muster_wait := 0
var _build_wait := 0
var _muster_next := 0


func _init(
		p_sim: RunSim,
		p_nodes: Array[StringName] = DEFAULT_NODES,
		p_towers: Array[StringName] = DEFAULT_TOWERS
) -> void:
	sim = p_sim
	node_priority = p_nodes
	tower_priority = p_towers
	for lane in sim.lane_curves.size():
		var offset := 0.0
		while offset <= sim.lane_lengths[lane]:
			_path_samples.append(sim.lane_curves[lane].sample_baked(offset))
			offset += PATH_SAMPLE_SPACING


## A bot with a plan that fits the run: in a campaign stage it drafts the home element and its
## neighbours, otherwise it plays the default Fire, Storm and Nature plan.
static func for_sim(p_sim: RunSim) -> AutoPlayer:
	var stage := p_sim.config.stage
	var bot: AutoPlayer
	if stage == null or stage.allowed_elements.is_empty():
		bot = AutoPlayer.new(p_sim)
	else:
		var plan := plan_for_elements(p_sim.config, stage.allowed_elements[0])
		bot = AutoPlayer.new(p_sim, plan[0], plan[1])
	# An assault is long and pushes across the whole map, so it takes more towers.
	if p_sim.is_assault():
		bot.max_towers = 100 if p_sim.is_counter_assault() else 70
	return bot


## Node and tower priorities built around one home element and its two neighbours on the ring:
## [nodes, towers]. Works from the tree data, so it follows any renamed nodes.
static func plan_for_elements(config: RunConfig, home: StringName) -> Array:
	var ring := config.element_index(home)
	var ids: Array[StringName] = []
	for offset in [0, 1, -1]:
		for element: ElementData in config.elements.values():
			if element.ring_index == posmod(ring + offset, ElementData.RING_SIZE):
				ids.append(element.id)
	var h := ids[0]
	var n := ids[1]
	var p := ids[2]
	var nodes: Array[StringName] = [
		StringName("%s_entry" % h), StringName("%s_entry" % n), StringName("%s_cw" % h), StringName("%s_ccw" % n),
		_bridge(config, h, n), StringName("%s_core" % h), StringName("%s_core" % n), StringName("%s_notable" % h),
		StringName("%s_ccw" % h), StringName("%s_entry" % p), StringName("%s_cw" % p), _bridge(config, p, h),
		StringName("%s_cw" % n), StringName("%s_notable" % n), StringName("%s_core" % p), StringName("%s_notable" % p),
		StringName("%s_ccw" % p),
	]
	var towers: Array[StringName] = []
	for pair: Array in [[h, n], [p, h]]:
		var hybrid := _hybrid(config, pair[0], pair[1])
		if not hybrid.is_empty():
			towers.append(hybrid)
	var bases: Array[TowerData] = []
	for tower: TowerData in config.towers.values():
		if not tower.is_hybrid() and not tower.is_longshot() and (tower.elements.has(h) or tower.elements.has(n) or tower.elements.has(p)):
			bases.append(tower)
	bases.sort_custom(func(a: TowerData, b: TowerData) -> bool: return value_for_gold(a) > value_for_gold(b))
	for tower in bases:
		towers.append(tower.id)
	return [nodes, towers]


## A rough damage per second per gold, for the bot's building order.
static func value_for_gold(tower: TowerData) -> float:
	var hits := 1.0 + tower.chain_count + (1.5 if tower.splash_radius > 0.0 else 0.0)
	var dot := 0.0
	for effect in tower.status_effects:
		dot += effect.damage_per_second
	return (tower.damage * tower.attacks_per_second * hits + dot) / float(tower.cost)


## The bridge node between two neighbouring elements' regions, or an empty id.
static func _bridge(config: RunConfig, a: StringName, b: StringName) -> StringName:
	var hybrid := _hybrid(config, a, b)
	for node_data in config.tree_nodes:
		if node_data.kind == TreeNodeData.Kind.BRIDGE and node_data.unlocks_towers.has(hybrid):
			return node_data.id
	return &""


## The hybrid tower of two elements unlocked by a bridge, or an empty id.
static func _hybrid(config: RunConfig, a: StringName, b: StringName) -> StringName:
	for tower: TowerData in config.towers.values():
		if tower.is_hybrid() and tower.elements.has(a) and tower.elements.has(b) and tower.requires_nodes.is_empty():
			return tower.id
	return &""


## One step of play: builds and starts the wave in a break, casts skills during a wave. Call it
## before every simulation step.
func act() -> void:
	if sim.state == RunSim.State.BUILDING:
		# The final level counts its breaks down: wait them out as a person would, building.
		if sim.is_counter_assault() and sim.break_time_left >= 0.0:
			spend_points()
			build_towers()
			sim.tick_break(RunSim.STEP)
			return
		play_build_phase()
	elif sim.state == RunSim.State.WAVE:
		use_skills()
		play_wave_step()


## What the bot does in a wave besides its skills: in the final level it builds while the waves roll
## in and musters its army in the counter-attack. Cheap to call every step.
func play_wave_step() -> void:
	if sim.state != RunSim.State.WAVE:
		return
	muster_army()
	# The final assault's waves roll into each other with no break: build while they come.
	if sim.rolls_on():
		_build_wait -= 1
		if _build_wait <= 0:
			_build_wait = BUILD_IN_WAVE_STEPS
			spend_points()
			build_towers()


## In the counter-attack: musters every champion who is ready, then troops in the plan's order.
func muster_army() -> void:
	if not musters or not sim.counter_started or sim.is_over():
		return
	_muster_wait -= 1
	if _muster_wait > 0:
		return
	_muster_wait = SKILL_CHECK_STEPS
	for ally in sim.ally_list():
		if ally.is_champion() and sim.muster_error(ally.id, muster_lane).is_empty():
			sim.muster(ally.id, muster_lane)
	if muster_plan.is_empty():
		return
	for i in muster_plan.size():
		var id := muster_plan[(_muster_next + i) % muster_plan.size()]
		if not sim.config.allies.has(id):
			continue
		if sim.muster_error(id, muster_lane).is_empty():
			sim.muster(id, muster_lane)
			_muster_next = (_muster_next + i + 1) % muster_plan.size()
			return
		# Wait for the next one in the plan if it only lacks gold, so cheap troops do not crowd out
		# the war machines.
		if sim.muster_cooldown_left(id) <= 0.0 and sim.gold < sim.ally_price(id):
			return


## Spend points and gold, then start the next wave. Does nothing unless the sim is building.
func play_build_phase() -> void:
	if sim.state != RunSim.State.BUILDING:
		return
	spend_points()
	upgrade_skills()
	build_towers()
	sim.start_next_wave()


## Buys the next level of the lowest open skill while that leaves at least as much gold again for
## towers.
func upgrade_skills() -> void:
	if not skill_upgrades:
		return
	while true:
		var best: StringName = &""
		for skill in sim.skill_list():
			if not sim.is_skill_unlocked(skill.id) or sim.skill_upgrade_cost(skill.id) < 0:
				continue
			if best.is_empty() or sim.skill_level(skill.id) < sim.skill_level(best):
				best = skill.id
		if best.is_empty() or sim.gold < sim.skill_upgrade_cost(best) * 2:
			return
		skill_gold += sim.skill_upgrade_cost(best)
		sim.upgrade_skill(best)


## Casts every skill that is ready and has something worth hitting. Cheap to call every step.
func use_skills() -> void:
	if not skills or sim.state != RunSim.State.WAVE:
		return
	_skill_wait -= 1
	if _skill_wait > 0:
		return
	_skill_wait = SKILL_CHECK_STEPS
	var alive: Array[SimEnemy] = []
	var boss := false
	var furthest := 0.0
	for enemy in sim.enemies:
		# Nothing lands on a fallen grunt or a phased runner, so no skill is spent on them.
		if not enemy.alive or enemy.untouchable():
			continue
		alive.append(enemy)
		boss = boss or enemy.data.tags.has(&"boss")
		furthest = maxf(furthest, enemy.progress / maxf(1.0, sim.lane_lengths[enemy.lane]))
	if alive.is_empty():
		return
	for skill in sim.skill_list():
		if not sim.skill_error(skill.id).is_empty():
			continue
		if skill.is_targeted():
			var aim := _best_aim(skill, alive)
			if aim.z >= SKILL_CROWD or aim.z < 0.0:
				sim.use_skill(skill.id, Vector2(aim.x, aim.y))
		elif skill.knockback > 0.0:
			if furthest >= SKILL_PUSH_PROGRESS:
				sim.use_skill(skill.id)
		elif boss or alive.size() >= SKILL_BOARD_CROWD:
			sim.use_skill(skill.id)
	_use_hero_abilities(alive, boss, furthest)


## Summons every hero in the party that is not on the field yet, where it covers the most road.
func summon_heroes() -> void:
	if not heroes:
		return
	for hero in sim.party:
		if sim.hero_tower(hero.id) != null:
			continue
		var best := Vector2i(-1, -1)
		var best_score := 0
		var grid := sim.config.map.grid_size
		for x in grid.x:
			for y in grid.y:
				var cell := Vector2i(x, y)
				if not sim.summon_error(hero.id, cell).is_empty():
					continue
				var score := coverage(cell, hero.attack.attack_range)
				if score > best_score:
					best_score = score
					best = cell
		if best.x >= 0:
			sim.summon_hero(hero.id, best)


## Casts each summoned hero's ability when it would do the most good.
func _use_hero_abilities(alive: Array[SimEnemy], boss: bool, furthest: float) -> void:
	if not heroes:
		return
	for tower in sim.hero_towers():
		if not sim.hero_ability_error(tower.hero.id).is_empty():
			continue
		var ability := tower.hero_ability()
		var radius := ability.radius_cells * sim.config.map.cell_size
		match ability.target:
			HeroAbility.Target.AIMED:
				var skill := SkillData.new()
				skill.radius = radius
				var aim := _best_aim(skill, alive)
				if aim.z >= SKILL_CROWD or aim.z < 0.0:
					sim.use_hero_ability(tower.hero.id, Vector2(aim.x, aim.y))
			HeroAbility.Target.SELF:
				var near := 0
				for enemy in alive:
					if enemy.position.distance_to(tower.position) <= radius:
						near += 1
				if near >= SKILL_CROWD:
					sim.use_hero_ability(tower.hero.id)
			_:
				var saves_lives := ability.ward or ability.send_to_start or ability.knockback > 0.0 or ability.hold_seconds > 0.0
				if saves_lives:
					if furthest >= SKILL_PUSH_PROGRESS:
						sim.use_hero_ability(tower.hero.id)
				elif boss or alive.size() >= SKILL_BOARD_CROWD:
					sim.use_hero_ability(tower.hero.id)


## Where an aimed skill reaches the most enemies: (x, y, how many). A boss in reach makes the
## count -1, which always casts.
func _best_aim(skill: SkillData, alive: Array[SimEnemy]) -> Vector3:
	# A skill that takes a moment to land (a falling meteor) is aimed where they will be by then.
	var at: Array[Vector2] = []
	for enemy in alive:
		at.append(_ahead(enemy, skill.impact_delay))
	var radius := sim.skill_radius(skill.id)
	var best := Vector3.ZERO
	for i in alive.size():
		var count := 0
		var boss := false
		for j in alive.size():
			if at[j].distance_squared_to(at[i]) <= radius * radius:
				count += 1
				boss = boss or alive[j].data.tags.has(&"boss")
		if boss:
			return Vector3(at[i].x, at[i].y, -1.0)
		if count > best.z:
			best = Vector3(at[i].x, at[i].y, count)
	return best


## Where an enemy will be after `seconds` if it keeps walking.
func _ahead(enemy: SimEnemy, seconds: float) -> Vector2:
	if seconds <= 0.0 or enemy.lane >= sim.lane_curves.size() or enemy.has_status(&"stun"):
		return enemy.position
	var curve := sim.lane_curves[enemy.lane]
	return curve.sample_baked(minf(enemy.progress + enemy.speed() * seconds, sim.lane_lengths[enemy.lane]))


## Takes the planned nodes in order, with the nodes on the way to each, saving up for the next one
## when it costs more than the bot has. Once every planned node is taken (or out of reach), the rest of the points go on the cheapest open nodes of the planned
## elements, nearest the Origin first. Keystones are left alone: they need a plan of their own.
func spend_points() -> void:
	while sim.tree.points > 0:
		var target := _next_planned_node()
		if target.is_empty():
			target = _cheapest_open_node()
		# A planned node it cannot afford yet is saved up for, as a person would.
		if target.is_empty() or not sim.allocate_node(target):
			return


## The first planned node not yet taken that can still be reached, or empty when the plan is done.
func _next_planned_node() -> StringName:
	for id in node_priority:
		if not sim.tree.is_allocated(id) and sim.tree.path_cost(id) >= 0:
			return id
	return &""


func _cheapest_open_node() -> StringName:
	var regions: Dictionary[StringName, bool] = {}
	for id in node_priority:
		if sim.tree.graph.has_node_id(id):
			regions[sim.tree.graph.node(id).region] = true
	var best: StringName = &""
	var best_key := Vector2(INF, INF)
	for id in sim.tree.graph.ids():
		var data := sim.tree.graph.node(id)
		if data.kind == TreeNodeData.Kind.KEYSTONE or not sim.tree.can_allocate(id):
			continue
		if not data.region.is_empty() and not regions.has(data.region):
			continue
		var key := Vector2(data.cost, data.position.length())
		if key.x < best_key.x or (key.x == best_key.x and key.y < best_key.y):
			best_key = key
			best = id
	return best


## Spends the gold, best buy first: another tower where it covers the most road, or a level (or
## an ascension) for a tower that already stands in a good spot.
func build_towers() -> void:
	_see_new_caves()
	summon_heroes()
	for purchase in 400:
		var tower_id := _affordable_tower() if sim.towers.size() < max_towers else &""
		var cell := best_cell(tower_id) if not tower_id.is_empty() else Vector2i(-1, -1)
		var build_value := 0.0
		if cell.x >= 0:
			var data: TowerData = sim.config.towers[tower_id]
			var reach := data.stat_with(&"attack_range", sim.modifiers())
			build_value = power(data) * coverage(cell, reach) / float(sim.tower_price(tower_id))
		var upgrade := _best_upgrade()
		if upgrade != null and upgrade.value > build_value:
			if upgrade.ascendancy.is_empty():
				sim.level_up(upgrade.tower)
			else:
				sim.ascend(upgrade.tower, upgrade.ascendancy)
		elif build_value <= 0.0 or sim.place_tower(tower_id, cell) == null:
			return


## A level or an ascension the bot can pay for, and what it buys per gold.
class Upgrade:
	var tower: SimTower
	## Empty for a level.
	var ascendancy: StringName
	var value := 0.0


## The upgrade that adds the most damage over the road per gold, or null if none can be paid for.
## A level adds to the tower's own hits (not to its burn or poison) and to its range.
func _best_upgrade() -> Upgrade:
	if not upgrades:
		return null
	var best: Upgrade = null
	for tower in sim.towers:
		if tower.is_hero():
			continue
		var gain := 0.0
		var price := 0
		var ascendancy: StringName = &""
		var direct := direct_power(tower.data)
		var lasting := power(tower.data) - direct
		var now := (direct * (1.0 + SimTower.DAMAGE_PER_LEVEL * (tower.level - 1)) + lasting) \
				* coverage(tower.cell, tower.attack_range)
		if tower.level < SimTower.MAX_LEVEL:
			var reach := tower.attack_range * (1.0 + SimTower.RANGE_PER_LEVEL * tower.level) \
					/ (1.0 + SimTower.RANGE_PER_LEVEL * (tower.level - 1))
			gain = (direct * (1.0 + SimTower.DAMAGE_PER_LEVEL * tower.level) + lasting) * coverage(tower.cell, reach) - now
			price = tower.level_up_price()
		elif ascends and tower.can_ascend() and not tower.data.ascendancies.is_empty():
			var option := tower.data.ascendancies[0]
			gain = now * ASCEND_GAIN
			price = tower.ascend_price(option)
			ascendancy = option.id
		if price <= 0 or sim.gold < price:
			continue
		var value := gain * upgrade_bias / float(price)
		if best == null or value > best.value:
			best = Upgrade.new()
			best.tower = tower
			best.ascendancy = ascendancy
			best.value = value
	return best


## A tower type's rough damage per second from its own hits, before levels: no burn or poison.
static func direct_power(tower: TowerData) -> float:
	var hits := 1.0 + tower.chain_count + (1.5 if tower.splash_radius > 0.0 else 0.0)
	return tower.damage * tower.attacks_per_second * hits


## A tower type's rough damage per second, before levels.
static func power(tower: TowerData) -> float:
	return value_for_gold(tower) * float(tower.cost)


## The free cell where this tower covers the most path, or (-1, -1) if none is free.
func best_cell(tower_id: StringName) -> Vector2i:
	var data: TowerData = sim.config.towers[tower_id]
	var reach := data.stat_with(&"attack_range", sim.modifiers())
	var best := Vector2i(-1, -1)
	var best_score := 0
	var grid := sim.config.map.grid_size
	for x in grid.x:
		for y in grid.y:
			var cell := Vector2i(x, y)
			if not sim.can_place(tower_id, cell):
				continue
			var score := coverage(cell, reach) + siege_value(cell, reach)
			if score > best_score:
				best_score = score
				best = cell
	return best


## In an assault, a cell that reaches a building of the enemy base which can be hurt now is worth
## as much as this many path samples, so the bot pushes its towers toward the fortress.
const SIEGE_WEIGHT := 60


## Extra score for a cell whose tower would reach a building that can be hurt now.
func siege_value(cell: Vector2i, reach: float) -> int:
	if not sim.is_assault():
		return 0
	var center := sim.config.map.cell_center(cell)
	var score := 0
	for structure in sim.structures:
		if sim.is_vulnerable(structure) and structure.position.distance_to(center) <= reach:
			score += SIEGE_WEIGHT
	return score


## A new cave's dig is road worth covering too (the rest of its lane is a road already sampled).
## Polled rather than connected: a signal from the sim back to the bot would keep both alive.
func _see_new_caves() -> void:
	while _caves_seen < sim.caves.size():
		_add_dig(sim.caves[_caves_seen])
		_caves_seen += 1


func _add_dig(cave: Caves.Cave) -> void:
	var dig := Curve2D.new()
	for point in cave.dig_points:
		dig.add_point(point)
	var offset := 0.0
	while offset <= dig.get_baked_length():
		_path_samples.append(dig.sample_baked(offset))
		offset += PATH_SAMPLE_SPACING
	_coverage_cache.clear()


## How many path sample points lie within reach of a cell's centre.
func coverage(cell: Vector2i, reach: float) -> int:
	var key := Vector3i(cell.x, cell.y, roundi(reach))
	if _coverage_cache.has(key):
		return _coverage_cache[key]
	var center := sim.config.map.cell_center(cell)
	var reach_squared := reach * reach
	var count := 0
	for point in _path_samples:
		if point.distance_squared_to(center) <= reach_squared:
			count += 1
	_coverage_cache[key] = count
	return count


func _affordable_tower() -> StringName:
	for id in tower_priority:
		if sim.is_unlocked(id) and sim.gold >= sim.tower_price(id):
			return id
	return &""
