class_name RunSim
extends RefCounted
## The rules of one run with no rendering. The game scene draws this state every frame,
## and tests drive it directly with step().

signal changed
signal wave_started(wave_number: int)
signal wave_cleared(wave_number: int, tree_points: int, gold: int)
signal enemy_killed(enemy: SimEnemy, killer: SimTower, bounty: int)
signal enemy_leaked(enemy: SimEnemy)
signal chain_fired(tower: SimTower, points: PackedVector2Array)
## A tower fired: a shot left it, or its chain jumped. Used for sound.
signal tower_attacked(tower: SimTower, target: SimEnemy)
signal projectile_landed(projectile: SimProjectile)
signal run_ended(won: bool)
## A skill was cast. `at` is the point picked on the board, or the board's centre for a skill
## that reaches everything.
signal skill_used(skill: SkillData, at: Vector2)
## A boss came onto the board, walking in or released by another enemy.
signal boss_arrived(enemy: SimEnemy)
## A boss silenced these towers.
signal towers_silenced(boss: SimEnemy, silenced: Array[SimTower])
## An enemy used its power (see EnemyData.power), or something happened to it: &"fall" and &"rise"
## for a grunt that falls and stands again, &"shield" when a shield comes up and &"block" when it
## stops a hit. `targets` holds the allies it healed or drove on, or the tower it burned or blocked.
signal enemy_power(enemy: SimEnemy, power: StringName, targets: Array)
## An enemy jumped forward along its road, from one point to another.
signal enemy_blinked(enemy: SimEnemy, from: Vector2)
## A boss escaped the board when badly hurt (see EnemyData.escape_below).
signal enemy_escaped(enemy: SimEnemy)
## A building of the enemy base fell in an assault.
signal structure_destroyed(structure: SimEnemy)
## Every building of an assault phase fell. `phase` is the new phase; above the stage's last phase
## once the whole base is down.
signal phase_changed(phase: int)
## A hero was placed on the board, or marched to a new cell.
signal hero_summoned(tower: SimTower)
signal hero_moved(tower: SimTower)
## A hero used its ability. `points` are where it landed: the point picked, the hero, the crowds hit
## or, for one that reaches every enemy, the board's centre.
signal hero_ability_used(tower: SimTower, ability: HeroAbility, points: PackedVector2Array)
## A hero joined the party during the run (Oswin at the capital).
signal hero_arrived(hero: HeroData)
signal hero_leveled(tower: SimTower)

enum State { BUILDING, WAVE, WON, LOST }

## Simulation step used by the game scene. Tests may use bigger steps.
const STEP := 1.0 / 60.0
## In an assault, every this many attacks a tower in reach of a building it can hurt shoots the
## building, even with enemies in range, so the siege moves on during a crowded wave.
const SIEGE_EVERY := 3
## How far a dying enemy's poison can jump.
const POISON_SPREAD_RANGE := 160.0

var config: RunConfig
var state := State.BUILDING
var gold := 0
var lives := 0
## Lives at the start of the run, for the campaign's stars.
var starting_lives := 0
## Waves cleared so far. The next wave to start is wave_index + 1.
var wave_index := 0
var tree: TreeState
var enemies: Array[SimEnemy] = []
var towers: Array[SimTower] = []
var projectiles: Array[SimProjectile] = []
## The main road (lane 0). Maps with several entrances have one curve per lane in lane_curves.
var path_curve := Curve2D.new()
var path_length := 0.0
var lane_curves: Array[Curve2D] = []
var lane_lengths: PackedFloat32Array = []
var time_in_wave := 0.0
## Buildings of the enemy base in an assault, standing or fallen. Empty in any other run.
var structures: Array[SimEnemy] = []
## The assault phase being fought, from 1. Buildings of later phases cannot be hurt yet.
var structure_phase := 1
## True once every building of the enemy base has fallen.
var citadel_fallen := false
## Seconds until the next wave starts on its own, or below 0 when nothing is counting down.
var break_time_left := -1.0

var kills := 0
var leaks := 0
var gold_earned := 0

var _path_cells: Dictionary[Vector2i, bool] = {}
var _tower_at: Dictionary[Vector2i, SimTower] = {}
var _spawner := WaveSpawner.new()
var _hash := SpatialHash.new(128.0)
var _next_id := 1
var _taken_this_break: Dictionary[StringName, bool] = {}
var _modifiers: Array[Modifier] = []
var _wave_element := -1
## Enemies split off or summoned during a step, added once the step's loops are done.
var _arrivals: Array[SimEnemy] = []
## Seconds of wave time until each skill can be used again, by skill id.
var _skill_cooldowns: Dictionary[StringName, float] = {}
## Seconds left on each skill whose modifiers are still running, by skill id.
var _skill_time: Dictionary[StringName, float] = {}
## Roads whose gate has fallen in an assault: nothing more comes down them.
var _closed_lanes: Dictionary[int, bool] = {}
var _structure_cells: Dictionary[Vector2i, SimEnemy] = {}
## The enemy's war camps and the defended city (see Landmarks).
var landmarks: Array[Landmarks.Site] = []
## Cells the camps and the city stand on, to the site on each.
var _landmark_cells: Dictionary[Vector2i, Landmarks.Site] = {}
## The heroes the player can summon in this run, in key order.
var party: Array[HeroData] = []
## Summoned heroes by hero id.
var _heroes_on_board: Dictionary[StringName, SimTower] = {}
## Hero abilities still running: each a HeroAbility and its seconds left, in [ability, time, tower].
var _hero_effects: Array[Array] = []
## Ground that bursts later: [seconds left, point, radius in pixels, damage, tower].
var _bursts: Array[Array] = []
## Lives given back by kills during the running hero abilities, so each keeps to its cap.
var _lives_from_kills := 0


func _init(p_config: RunConfig) -> void:
	config = p_config
	var rules := config.rules
	var base_gold := rules.starting_gold
	var base_lives := rules.starting_lives
	if config.stage != null:
		base_gold = config.stage.starting_gold if config.stage.starting_gold > 0 else base_gold
		base_lives = config.stage.starting_lives if config.stage.starting_lives > 0 else base_lives
	gold = roundi(StatCalculator.compute(&"starting_gold", base_gold, config.run_modifiers))
	lives = roundi(StatCalculator.compute(&"starting_lives", base_lives, config.run_modifiers))
	starting_lives = lives
	var start_points := roundi(StatCalculator.compute(&"starting_tree_points", rules.starting_tree_points, config.run_modifiers))
	tree = TreeState.new(TreeGraph.new(config.tree_nodes), start_points)
	tree.lock(config.locked_tree_nodes)
	tree.grant(config.granted_tree_nodes)
	for lane in config.map.lane_count():
		var curve := Curve2D.new()
		for point in config.map.path_points(lane):
			curve.add_point(point)
		lane_curves.append(curve)
		lane_lengths.append(curve.get_baked_length())
	path_curve = lane_curves[0]
	path_length = lane_lengths[0]
	_path_cells = config.map.path_cells()
	_place_structures()
	_place_landmarks()
	for hero in config.heroes:
		if hero != null and not party.has(hero) and party.size() < HeroData.MAX_PARTY:
			party.append(hero)
	_refresh_modifiers()


# --- Queries -----------------------------------------------------------------

func total_waves() -> int:
	return config.wave_set.waves.size()


## The wave being fought, or the next one while building. Null once the run is over. In an assault
## the last wave repeats until the enemy base falls.
func current_wave() -> WaveData:
	var index := wave_index
	if index >= total_waves():
		if is_assault() and not is_over() and total_waves() > 0:
			return config.wave_set.waves[total_waves() - 1]
		return null
	return config.wave_set.waves[index]


## 1-based number of the current or next wave. In an assault it keeps counting past the wave set,
## and enemy health keeps growing with it.
func wave_number() -> int:
	if is_assault():
		return wave_index + 1
	return mini(wave_index + 1, total_waves())


## True when the run is an assault on the enemy base: it is won by bringing down its buildings.
func is_assault() -> bool:
	return not structures.is_empty()


func total_phases() -> int:
	var count := 0
	for structure in structures:
		count = maxi(count, structure.phase)
	return count


## Buildings of a phase still standing.
func structures_left(phase: int) -> Array[SimEnemy]:
	var result: Array[SimEnemy] = []
	for structure in structures:
		if structure.alive and structure.phase == phase:
			result.append(structure)
	return result


## A building can be hurt once every building of the phases before its own has fallen.
func is_vulnerable(structure: SimEnemy) -> bool:
	return structure.alive and structure.phase <= structure_phase


## True when nothing more comes down this road, because its gate has fallen.
func is_lane_closed(lane: int) -> bool:
	return _closed_lanes.has(lane)


## The rightmost column towers may be built in now, or -1 for the whole map.
func build_limit() -> int:
	if config.stage == null or config.stage.build_columns.is_empty():
		return -1
	var index := structure_phase - 1
	if index >= config.stage.build_columns.size():
		return -1
	return config.stage.build_columns[index]


## The living boss with the most health left, for the boss health bar. Buildings are not counted.
func strongest_boss() -> SimEnemy:
	var best: SimEnemy = null
	for enemy in enemies:
		if enemy.alive and enemy.data.tags.has(&"boss") and (best == null or enemy.max_health > best.max_health):
			best = enemy
	return best


func is_over() -> bool:
	return state == State.WON or state == State.LOST


func modifiers() -> Array[Modifier]:
	return _modifiers


func tower_price(tower_id: StringName) -> int:
	var data: TowerData = config.towers.get(tower_id)
	if data == null:
		return 0
	return maxi(1, roundi(StatCalculator.compute(&"cost", data.cost, _modifiers, data.all_tags())))


func is_unlocked(tower_id: StringName) -> bool:
	if tree.unlocked_towers().has(tower_id):
		return true
	var data: TowerData = config.towers.get(tower_id)
	if data == null or data.requires_nodes.is_empty():
		return false
	for node_id in data.requires_nodes:
		if not tree.is_allocated(node_id):
			return false
	return true


func tower_at(cell: Vector2i) -> SimTower:
	return _tower_at.get(cell)


# --- Skills ------------------------------------------------------------------

## Every skill of the run, in ring order of their elements.
func skill_list() -> Array[SkillData]:
	var result: Array[SkillData] = []
	result.assign(config.skills.values())
	result.sort_custom(func(a: SkillData, b: SkillData) -> bool:
		var first := config.element_index(a.element)
		var second := config.element_index(b.element)
		return first < second if first != second else String(a.id) < String(b.id))
	return result


## A skill opens when its skill web node is taken.
func is_skill_unlocked(skill_id: StringName) -> bool:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null:
		return false
	return skill.requires_node.is_empty() or tree.is_allocated(skill.requires_node)


## The skill's full cooldown in seconds, after modifiers.
func skill_cooldown(skill_id: StringName) -> float:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null:
		return 0.0
	return maxf(1.0, StatCalculator.compute(&"skill_cooldown", skill.cooldown, _modifiers, skill.all_tags()))


## Seconds of wave time until the skill is ready again. 0 when it is ready.
func skill_cooldown_left(skill_id: StringName) -> float:
	return _skill_cooldowns.get(skill_id, 0.0)


## Seconds left on a skill's lasting effect, such as faster attacks. 0 when it is not running.
func skill_time_left(skill_id: StringName) -> float:
	return _skill_time.get(skill_id, 0.0)


## Why a skill cannot be cast now, or an empty string if it can.
func skill_error(skill_id: StringName) -> String:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null:
		return "Unknown skill"
	if is_over():
		return "The run is over"
	if not is_skill_unlocked(skill_id):
		var node_data := tree.graph.node(skill.requires_node)
		if tree.is_locked(skill.requires_node):
			return "%s is closed in this run" % skill.display_name
		return "Take %s in the skill web to open %s" % [node_data.display_name if node_data != null else String(skill.requires_node), skill.display_name]
	if state != State.WAVE:
		return "Skills can only be used during a wave"
	var left := skill_cooldown_left(skill_id)
	if left > 0.0:
		return "%s is ready in %d s" % [skill.display_name, ceili(left)]
	return ""


## Casts a skill at a point on the board (ignored by skills that reach everything). Returns false
## and does nothing if it cannot be cast now.
func use_skill(skill_id: StringName, at: Vector2 = Vector2.ZERO) -> bool:
	if not skill_error(skill_id).is_empty():
		return false
	var skill: SkillData = config.skills[skill_id]
	_skill_cooldowns[skill_id] = skill_cooldown(skill_id)
	var elements: Array[int] = []
	if config.element_index(skill.element) >= 0:
		elements.append(config.element_index(skill.element))
	# Skill damage keeps pace with enemy health, wave by wave.
	var growth := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	var damage := StatCalculator.compute(&"skill_damage", skill.damage, _modifiers, skill.all_tags()) * growth
	var effects: Array[StatusEffectData] = []
	for spec in skill.status_effects:
		var scaled := spec.duplicate() as StatusEffectData
		scaled.damage_per_second *= growth
		effects.append(scaled)
	var targets: Array[SimEnemy] = enemies.duplicate()
	for structure in structures:
		if is_vulnerable(structure):
			targets.append(structure)
	for enemy in targets:
		if not enemy.alive or (skill.is_targeted() and enemy.position.distance_to(at) > skill.radius):
			continue
		var multiplier := ElementRules.damage_multiplier(elements, enemy.element)
		if damage > 0.0:
			_damage(enemy, CombatMath.hit_damage(damage, multiplier, enemy.effective_armour(), enemy.damage_taken_bonus()), null)
		if not enemy.alive:
			continue
		for spec in effects:
			enemy.apply_status(spec, null, multiplier)
		if skill.knockback > 0.0 and enemy.knock_back(skill.knockback) > 0.0:
			enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)
	if skill.duration > 0.0 and not skill.modifiers.is_empty():
		_skill_time[skill_id] = skill.duration
		_refresh_modifiers()
	skill_used.emit(skill, at if skill.is_targeted() else config.map.size_in_pixels() * 0.5)
	changed.emit()
	return true


func _tick_skills(delta: float) -> void:
	for skill_id: StringName in _skill_cooldowns.keys():
		_skill_cooldowns[skill_id] = maxf(0.0, _skill_cooldowns[skill_id] - delta)
	var ended := false
	for skill_id: StringName in _skill_time.keys():
		_skill_time[skill_id] -= delta
		if _skill_time[skill_id] <= 0.0:
			_skill_time.erase(skill_id)
			ended = true
	if ended:
		_refresh_modifiers()


func _place_landmarks() -> void:
	landmarks = Landmarks.find(config.map, is_path, func(cell: Vector2i) -> bool: return _structure_cells.has(cell))
	for site in landmarks:
		for cell in site.cells:
			_landmark_cells[cell] = site


## The camp or city standing on a cell, or null.
func landmark_at(cell: Vector2i) -> Landmarks.Site:
	return _landmark_cells.get(cell)


func is_path(cell: Vector2i) -> bool:
	return _path_cells.has(cell)


func path_cell_list() -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	result.assign(_path_cells.keys())
	return result


## Why a tower cannot go on a cell, or an empty string if it can.
func placement_error(tower_id: StringName, cell: Vector2i) -> String:
	if is_over():
		return "The run is over"
	if not config.towers.has(tower_id):
		return "Unknown tower"
	if not is_unlocked(tower_id):
		return "Unlock this tower in the skill web first"
	if not config.map.is_inside(cell):
		return "Outside the map"
	if is_path(cell):
		return "Towers cannot go on the path"
	if _structure_cells.has(cell):
		return "The enemy's building stands here"
	if _landmark_cells.has(cell):
		return "The enemy's war camp stands here" if _landmark_cells[cell].kind == &"camp" else "The city stands here"
	var limit := build_limit()
	if limit >= 0 and cell.x > limit:
		return "The enemy still holds this ground: bring down its buildings first"
	if _tower_at.has(cell):
		return "There is already a tower here"
	if gold < tower_price(tower_id):
		return "Not enough gold"
	return ""


func can_place(tower_id: StringName, cell: Vector2i) -> bool:
	return placement_error(tower_id, cell).is_empty()


## Refunds are allowed for nodes taken since the last wave started, until the next one starts.
func can_refund_node(id: StringName) -> bool:
	return state == State.BUILDING and _taken_this_break.has(id) and tree.can_refund(id)


## Pixels an enemy still has to walk to leave the map.
func distance_to_exit(enemy: SimEnemy) -> float:
	return lane_lengths[enemy.lane] - enemy.progress


## Element index of the wave being fought or about to start, or -1.
func wave_element() -> int:
	var wave := current_wave()
	return config.element_index(wave.element) if wave != null else -1


# --- Player actions ----------------------------------------------------------

func place_tower(tower_id: StringName, cell: Vector2i) -> SimTower:
	if not can_place(tower_id, cell):
		return null
	var data: TowerData = config.towers[tower_id]
	var price := tower_price(tower_id)
	var indices: Array[int] = []
	for element_id in data.elements:
		indices.append(config.element_index(element_id))
	var tower := SimTower.new(_new_id(), data, cell, config.map.cell_center(cell), price, indices)
	gold -= price
	towers.append(tower)
	_tower_at[cell] = tower
	_recompute_towers()
	changed.emit()
	return tower


## Towers a built tower can turn into: unlocked ones with exactly one more element that keep all
## of its own. A base tower becomes a dual, and a dual becomes a triple. Ascended towers stay as they are.
func hybrid_options(tower: SimTower) -> Array[StringName]:
	var result: Array[StringName] = []
	if tower == null or tower.ascendancy != null or tower.is_hero():
		return result
	var own := tower.data.elements
	for id: StringName in config.towers:
		var data: TowerData = config.towers[id]
		if data.elements.size() != own.size() + 1 or not is_unlocked(id):
			continue
		if own.all(func(element_id: StringName) -> bool: return data.elements.has(element_id)):
			result.append(id)
	result.sort_custom(func(a: StringName, b: StringName) -> bool: return String(a) < String(b))
	return result


## Gold to turn a built base tower into a hybrid: the hybrid's price minus what the tower cost.
func hybrid_upgrade_price(tower: SimTower, hybrid_id: StringName) -> int:
	return maxi(0, tower_price(hybrid_id) - tower.type_price)


## Why a tower cannot become this hybrid, or an empty string if it can.
func hybrid_upgrade_error(tower: SimTower, hybrid_id: StringName) -> String:
	if is_over():
		return "The run is over"
	if not towers.has(tower):
		return "Unknown tower"
	if tower.ascendancy != null:
		return "Ascended towers cannot change"
	if not hybrid_options(tower).has(hybrid_id):
		return "This tower cannot become that tower"
	if gold < hybrid_upgrade_price(tower, hybrid_id):
		return "Not enough gold"
	return ""


## Turns a base tower into a hybrid in place, paying the difference in price.
func upgrade_to_hybrid(tower: SimTower, hybrid_id: StringName) -> bool:
	if not hybrid_upgrade_error(tower, hybrid_id).is_empty():
		return false
	var data: TowerData = config.towers[hybrid_id]
	var price := hybrid_upgrade_price(tower, hybrid_id)
	gold -= price
	var indices: Array[int] = []
	for element_id in data.elements:
		indices.append(config.element_index(element_id))
	tower.change_type(data, indices, tower.type_price + price, price)
	_recompute_towers()
	changed.emit()
	return true


## Why a tower cannot go up a level, or an empty string if it can.
func level_up_error(tower: SimTower) -> String:
	if is_over():
		return "The run is over"
	if not towers.has(tower):
		return "Unknown tower"
	if tower.is_hero():
		return "Heroes grow a level for every wave they fight"
	if tower.level >= SimTower.MAX_LEVEL:
		return "Already at the top level"
	if gold < tower.level_up_price():
		return "Not enough gold"
	return ""


func level_up(tower: SimTower) -> bool:
	if not level_up_error(tower).is_empty():
		return false
	var price := tower.level_up_price()
	gold -= price
	tower.price_paid += price
	tower.level += 1
	_recompute_towers()
	changed.emit()
	return true


## Why a tower cannot take this ascendancy, or an empty string if it can.
func ascend_error(tower: SimTower, ascendancy_id: StringName) -> String:
	if is_over():
		return "The run is over"
	if not towers.has(tower):
		return "Unknown tower"
	if tower.is_hero():
		return "Heroes cannot ascend"
	if tower.ascendancy != null:
		return "Already ascended"
	if tower.level < SimTower.MAX_LEVEL:
		return "Reach level %d first" % SimTower.MAX_LEVEL
	var option := tower.data.ascendancy(ascendancy_id)
	if option == null:
		return "Unknown ascendancy"
	if gold < tower.ascend_price(option):
		return "Not enough gold"
	return ""


func ascend(tower: SimTower, ascendancy_id: StringName) -> bool:
	if not ascend_error(tower, ascendancy_id).is_empty():
		return false
	var option := tower.data.ascendancy(ascendancy_id)
	var price := tower.ascend_price(option)
	gold -= price
	tower.price_paid += price
	tower.ascendancy = option
	_recompute_towers()
	changed.emit()
	return true


func sell_value(tower: SimTower) -> int:
	if tower.is_hero():
		return 0
	return floori(tower.price_paid * clampf(run_stat(&"sell_refund", config.rules.sell_refund), 0.0, 1.0))


## A run-wide number, such as gold per wave, after the meta tree's and the skill web's bonuses.
func run_stat(stat: StringName, base: float) -> float:
	return StatCalculator.compute(stat, base, _modifiers)


func sell_tower(tower: SimTower) -> int:
	if not towers.has(tower) or tower.is_hero():
		return 0
	var refund := sell_value(tower)
	gold += refund
	towers.erase(tower)
	_tower_at.erase(tower.cell)
	_recompute_towers()
	changed.emit()
	return refund


func start_next_wave() -> bool:
	if state != State.BUILDING or current_wave() == null:
		return false
	var wave := current_wave()
	state = State.WAVE
	time_in_wave = 0.0
	break_time_left = -1.0
	_wave_element = config.element_index(wave.element)
	_spawner.start(wave, lane_curves.size())
	_taken_this_break.clear()
	for tower in _heroes_on_board.values():
		tower.moved_this_break = false
	for hero in config.arriving_heroes:
		if hero != null and hero.arrives_at_wave == wave_number() and not party.has(hero):
			party.append(hero)
			hero_arrived.emit(hero)
	wave_started.emit(wave_number())
	changed.emit()
	return true


func allocate_node(id: StringName) -> bool:
	if is_over() or not tree.allocate(id):
		return false
	if state == State.BUILDING:
		_taken_this_break[id] = true
	_refresh_modifiers()
	changed.emit()
	return true


func refund_node(id: StringName) -> bool:
	if not can_refund_node(id) or not tree.refund(id):
		return false
	_taken_this_break.erase(id)
	_refresh_modifiers()
	changed.emit()
	return true


# --- Simulation --------------------------------------------------------------

func step(delta: float) -> void:
	if state != State.WAVE:
		return
	time_in_wave += delta
	_tick_skills(delta)
	_tick_heroes(delta)
	_spawn(delta)
	_move_enemies(delta)
	if state != State.WAVE:
		return
	_tick_statuses(delta)
	_tick_traits(delta)
	_rebuild_hash()
	_update_towers(delta)
	_update_projectiles(delta)
	_remove_dead()
	if not _arrivals.is_empty():
		enemies.append_array(_arrivals)
		_arrivals.clear()
	if state != State.WAVE:
		return
	if citadel_fallen and not _overlord_alive():
		_end_run(true)
		return
	if _spawner.is_finished() and enemies.is_empty():
		_finish_wave()


## Counts down the break before a wave that starts on its own. Call it while building; the game
## does so every frame. Returns true when it started the wave.
func tick_break(delta: float) -> bool:
	if state != State.BUILDING or break_time_left < 0.0:
		return false
	break_time_left -= delta
	if break_time_left <= 0.0:
		return start_next_wave()
	return false


func _spawn(delta: float) -> void:
	var multiplier := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	var wave := current_wave()
	if wave != null:
		multiplier *= wave.health_multiplier
	for spawn in _spawner.advance(delta):
		var group := spawn.group
		var data: EnemyData = config.enemies.get(group.enemy)
		if data == null:
			continue
		var lane := _open_lane(spawn.lane)
		var element := _wave_element
		if not group.element.is_empty():
			element = config.element_index(group.element)
		var enemy := _make_enemy(data, multiplier, lane, element, 0.0)
		enemies.append(enemy)
		if data.tags.has(&"boss"):
			boss_arrived.emit(enemy)


## The lane itself if its gate still stands, otherwise the next open one. If every road is closed
## the enemies still come down the first one.
func _open_lane(lane: int) -> int:
	if _closed_lanes.is_empty():
		return lane
	for offset in lane_curves.size():
		var candidate := (lane + offset) % lane_curves.size()
		if not _closed_lanes.has(candidate):
			return candidate
	return lane


## A new enemy on a lane. An enemy with its own element keeps it whatever the wave.
func _make_enemy(data: EnemyData, multiplier: float, lane: int, element: int, progress: float) -> SimEnemy:
	var enemy := SimEnemy.new(_new_id(), data, multiplier)
	enemy.lane = lane
	enemy.element = config.element_index(data.element) if not data.element.is_empty() else element
	enemy.progress = maxf(0.0, progress)
	enemy.position = lane_curves[lane].sample_baked(enemy.progress)
	return enemy


## Enemies that come out of another: splitting on death, or summoned by a boss. They appear a little
## behind it on its lane, with its strength and element.
func _release_from(parent: SimEnemy, enemy_id: StringName, count: int) -> void:
	var data: EnemyData = config.enemies.get(enemy_id)
	if data == null:
		return
	for i in count:
		var child := _make_enemy(data, parent.health_multiplier, parent.lane, parent.element, parent.progress - 14.0 * i)
		_arrivals.append(child)
		if data.tags.has(&"boss"):
			boss_arrived.emit(child)


func _move_enemies(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		enemy.progress += enemy.speed() * delta
		if enemy.progress >= lane_lengths[enemy.lane] and is_warded():
			# Last Light: the gate throws it back to the start of its road.
			enemy.progress = 0.0
			enemy.position = lane_curves[enemy.lane].sample_baked(0.0)
		elif enemy.progress >= lane_lengths[enemy.lane]:
			enemy.alive = false
			enemy.leaked = true
			leaks += 1
			lives -= enemy.data.leak_damage
			enemy_leaked.emit(enemy)
			if lives <= 0:
				lives = 0
				_end_run(false)
				return
		else:
			enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)


## Healing, summoning and changing element, the horde's powers and the bosses' tricks.
func _tick_traits(delta: float) -> void:
	_tick_boss_tricks(delta)
	_tick_powers(delta)
	# Buildings only call up the horde while the wave is still marching in, so a wave can end.
	if not _spawner.is_finished():
		for structure in structures:
			if structure.alive and is_vulnerable(structure):
				_tick_summons(structure, delta)
	for enemy in enemies:
		if not enemy.alive:
			continue
		var data := enemy.data
		if enemy.is_regenerating() and enemy.health < enemy.max_health:
			enemy.health = minf(enemy.max_health, enemy.health + enemy.max_health * data.regen_per_second * delta)
		_tick_summons(enemy, delta)
		if data.prismatic_interval > 0.0:
			enemy.prism_timer -= delta
			if enemy.prism_timer <= 0.0:
				enemy.prism_timer += data.prismatic_interval
				enemy.element = (maxi(enemy.element, 0) + 1) % ElementData.RING_SIZE


func _tick_summons(enemy: SimEnemy, delta: float) -> void:
	var data := enemy.data
	if data.summon_interval > 0.0 and not data.summon.is_empty():
		enemy.summon_timer -= delta
		if enemy.summon_timer <= 0.0:
			enemy.summon_timer += data.summon_interval
			_release_from(enemy, data.summon, data.summon_count)


## Shields, silences, blinks and rage. Buildings of the enemy base use them too, once they can be hurt.
func _tick_boss_tricks(delta: float) -> void:
	var casters: Array[SimEnemy] = []
	for enemy in enemies:
		if enemy.alive:
			enemy.ward = 0.0
			casters.append(enemy)
	for structure in structures:
		if is_vulnerable(structure):
			casters.append(structure)
	for caster in casters:
		var data := caster.data
		if data.escape_below > 0.0 and caster.health < caster.max_health * data.escape_below:
			caster.alive = false
			caster.escaped = true
			enemy_escaped.emit(caster)
			continue
		if data.enrage_below > 0.0 and not caster.enraged and caster.health < caster.max_health * data.enrage_below:
			caster.enraged = true
		if data.ward_radius > 0.0 and data.ward_reduction > 0.0:
			var reach := data.ward_radius * data.ward_radius
			for other in enemies:
				if other != caster and other.alive and other.position.distance_squared_to(caster.position) <= reach:
					other.ward = maxf(other.ward, clampf(data.ward_reduction, 0.0, 0.9))
		if data.silence_interval > 0.0 and data.silence_radius > 0.0:
			caster.silence_timer -= delta
			if caster.silence_timer <= 0.0:
				caster.silence_timer += data.silence_interval
				_silence_towers(caster)
		if data.blink_interval > 0.0 and data.blink_distance > 0.0 and not caster.structure \
				and not caster.has_status(&"stun"):
			caster.blink_timer -= delta
			if caster.blink_timer <= 0.0:
				caster.blink_timer += data.blink_interval
				var from := caster.position
				# A blink never carries it out of the map: it stops a little short of the exit.
				var room := lane_lengths[caster.lane] - 64.0 - caster.progress
				var jump := minf(data.blink_distance, room)
				if jump > 0.0:
					caster.progress += jump
					caster.position = lane_curves[caster.lane].sample_baked(caster.progress)
					enemy_blinked.emit(caster, from)


## Each kind of enemy's own power. See EnemyData.power.
func _tick_powers(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		var data := enemy.data
		enemy.haste_left = maxf(0.0, enemy.haste_left - delta)
		if enemy.downed > 0.0:
			enemy.downed -= delta
			if enemy.downed <= 0.0:
				enemy.downed = 0.0
				enemy.risen = true
				enemy.health = enemy.max_health * clampf(data.power_amount, 0.05, 1.0)
				enemy_power.emit(enemy, &"rise", [])
			continue
		if not enemy.has_power:
			continue
		enemy.power_left = maxf(0.0, enemy.power_left - delta)
		enemy.power_timer = maxf(0.0, enemy.power_timer - delta)
		if enemy.power_timer > 0.0 or not enemy.can_use_power():
			continue
		match data.power:
			&"war_cry":
				var driven: Array = []
				for ally in _allies_near(enemy, data.power_radius):
					# It drives the lesser ranks on: not runners, already as fast as they go, nor
					# brutes, its own kind.
					if not ally.data.tags.has(&"fast") and ally.data.power != &"war_cry":
						driven.append(ally)
				for ally: SimEnemy in driven:
					ally.haste = maxf(ally.haste if ally.haste_left > 0.0 else 0.0, data.power_amount)
					ally.haste_left = maxf(ally.haste_left, data.power_duration)
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"war_cry", driven)
			&"mend":
				# A healer on fire or sick with poison cannot mend anyone.
				if enemy.has_status(&"burn") or enemy.has_status(&"poison"):
					continue
				var healed: Array = []
				for ally in _allies_near(enemy, data.power_radius):
					if ally.health < ally.max_health and not ally.data.tags.has(&"boss") \
							and not ally.has_status(&"burn") and not ally.has_status(&"poison"):
						ally.health = minf(ally.max_health, ally.health + ally.max_health * data.power_amount)
						healed.append(ally)
				# It waits for someone to be hurt, so every pulse heals.
				if not healed.is_empty():
					enemy.power_timer = data.power_interval
					enemy_power.emit(enemy, &"mend", healed)
			&"block":
				if not enemy.shield_up:
					enemy.shield_up = true
					enemy_power.emit(enemy, &"shield", [])
			&"breath":
				var target := _strongest_tower_near(enemy.position, data.power_radius)
				if target != null:
					target.silenced = maxf(target.silenced, data.power_duration)
					enemy.power_timer = data.power_interval
					enemy_power.emit(enemy, &"breath", [target])


## Living, touchable enemies within `radius` of `caster`, the caster too.
func _allies_near(caster: SimEnemy, radius: float) -> Array[SimEnemy]:
	var found: Array[SimEnemy] = []
	var reach := radius * radius
	for other in enemies:
		if other.alive and other.downed <= 0.0 and other.position.distance_squared_to(caster.position) <= reach:
			found.append(other)
	return found


## The tower that hits hardest within `radius` of `at`, or null.
func _strongest_tower_near(at: Vector2, radius: float) -> SimTower:
	var best: SimTower = null
	var reach := radius * radius
	for tower in towers:
		if tower.position.distance_squared_to(at) > reach:
			continue
		if best == null or tower.damage * tower.attacks_per_second > best.damage * best.attacks_per_second:
			best = tower
	return best


func _silence_towers(caster: SimEnemy) -> void:
	var hit: Array[SimTower] = []
	var reach := caster.data.silence_radius * caster.data.silence_radius
	for tower in towers:
		if tower.position.distance_squared_to(caster.position) <= reach:
			tower.silenced = maxf(tower.silenced, caster.data.silence_duration)
			hit.append(tower)
	if not hit.is_empty():
		towers_silenced.emit(caster, hit)


func _tick_statuses(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		enemy.stun_immunity = maxf(0.0, enemy.stun_immunity - delta)
		for kind: StringName in enemy.statuses.keys():
			var status: SimStatus = enemy.statuses[kind]
			var dps := status.damage_per_second()
			if dps > 0.0:
				_damage(enemy, dps * minf(delta, status.time_left), status.source)
				# Dead, or fallen in a heap with its statuses gone.
				if not enemy.alive or enemy.downed > 0.0:
					break
			status.time_left -= delta
			if status.time_left <= 0.0:
				enemy.statuses.erase(kind)
				if kind == &"stun":
					enemy.stun_immunity = SimEnemy.STUN_IMMUNITY


func _rebuild_hash() -> void:
	_hash.clear()
	for enemy in enemies:
		if enemy.alive and not enemy.untouchable():
			_hash.insert(enemy)
	for structure in structures:
		if is_vulnerable(structure):
			_hash.insert(structure)


func _update_towers(delta: float) -> void:
	for tower in towers:
		if tower.silenced > 0.0:
			tower.silenced = maxf(0.0, tower.silenced - delta)
			continue
		tower.cooldown -= delta
		if tower.cooldown > 0.0:
			continue
		var target := _find_target(tower)
		if target == null:
			tower.cooldown = 0.0
			continue
		_attack(tower, target)
		tower.cooldown += CombatMath.attack_interval(tower.attacks_per_second)


## The enemy in range that is closest to leaving the map. Buildings of the enemy base come last,
## except for a siege shot now and then.
func _find_target(tower: SimTower) -> SimEnemy:
	tower.shots += 1
	if not structures.is_empty() and tower.shots % SIEGE_EVERY == 0:
		for structure in structures:
			if is_vulnerable(structure) and structure.position.distance_to(tower.position) <= tower.attack_range:
				return structure
	var best: SimEnemy = null
	var best_left := INF
	for enemy in _hash.query(tower.position, tower.attack_range):
		var left := distance_to_exit(enemy) if not enemy.structure else 1.0e9 + enemy.health
		if left < best_left:
			best_left = left
			best = enemy
	return best


func _attack(tower: SimTower, target: SimEnemy) -> void:
	tower_attacked.emit(tower, target)
	if tower.chains():
		_fire_chain(tower, target)
		return
	var shot := SimProjectile.new()
	shot.position = tower.position
	shot.target = target
	shot.target_point = target.position
	shot.speed = tower.projectile_speed
	shot.source = tower
	shot.damage = tower.damage
	shot.splash_radius = tower.splash_radius
	projectiles.append(shot)


func _fire_chain(tower: SimTower, first: SimEnemy) -> void:
	var points := PackedVector2Array([tower.position])
	var hit: Dictionary[int, bool] = {}
	var current := first
	for jump in range(tower.chain_count + 1):
		points.append(current.position)
		hit[current.id] = true
		_hit(tower, current, CombatMath.chain_damage(tower.damage, tower.chain_falloff, jump))
		var next: SimEnemy = null
		var best_distance := INF
		for candidate in _hash.query(current.position, tower.chain_range):
			if hit.has(candidate.id):
				continue
			var distance := candidate.position.distance_squared_to(current.position)
			if distance < best_distance:
				best_distance = distance
				next = candidate
		if next == null:
			break
		current = next
	chain_fired.emit(tower, points)


func _update_projectiles(delta: float) -> void:
	for shot in projectiles:
		if shot.target != null and shot.target.alive:
			shot.target_point = shot.target.position
		var travel := shot.speed * delta
		if shot.position.distance_to(shot.target_point) <= travel:
			shot.position = shot.target_point
			_land(shot)
		else:
			shot.position = shot.position.move_toward(shot.target_point, travel)
	var flying: Array[SimProjectile] = []
	for shot in projectiles:
		if not shot.done:
			flying.append(shot)
	projectiles = flying


func _land(shot: SimProjectile) -> void:
	shot.done = true
	if shot.splash_radius > 0.0:
		for enemy in _hash.query(shot.position, shot.splash_radius):
			_hit(shot.source, enemy, shot.damage)
	elif shot.target != null and shot.target.alive:
		_hit(shot.source, shot.target, shot.damage)
	projectile_landed.emit(shot)


func _hit(tower: SimTower, enemy: SimEnemy, damage: float) -> void:
	if not enemy.alive or enemy.untouchable():
		return
	if enemy.shield_up:
		# The shield takes the whole hit, effects and all, and breaks.
		enemy.shield_up = false
		enemy.power_timer = enemy.data.power_interval
		enemy_power.emit(enemy, &"block", [tower])
		return
	var multiplier := _element_multiplier(tower, enemy)
	var armour := enemy.effective_armour() * (1.0 - tower.armour_ignore)
	_damage(enemy, CombatMath.hit_damage(damage, multiplier, armour, enemy.damage_taken_bonus()), tower)
	if enemy.alive:
		for spec in tower.effects:
			enemy.apply_status(spec, tower, multiplier)
		if tower.knockback > 0.0 and enemy.knock_back(tower.knockback) > 0.0:
			enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)


func _damage(enemy: SimEnemy, amount: float, source: SimTower) -> void:
	if not enemy.alive or amount <= 0.0 or enemy.untouchable():
		return
	if enemy.ward > 0.0:
		amount *= 1.0 - enemy.ward
	if enemy.is_hardened():
		amount *= 1.0 - clampf(enemy.data.power_amount, 0.0, 0.95)
	var dealt := minf(amount, enemy.health)
	enemy.health -= amount
	if source != null:
		source.damage_dealt += dealt
	if enemy.health <= 0.0:
		if enemy.data.power == &"rise" and enemy.has_power and not enemy.risen and not enemy.has_status(&"burn"):
			_fall(enemy)
			return
		_kill(enemy, source)
	elif (enemy.data.power == &"harden" or enemy.data.power == &"phase") and enemy.has_power \
			and enemy.power_timer <= 0.0 and enemy.can_use_power():
		# Struck, it turns to stone or slips out of the world for a moment.
		enemy.power_left = enemy.data.power_duration
		enemy.power_timer = enemy.data.power_interval + enemy.data.power_duration
		enemy_power.emit(enemy, enemy.data.power, [])


## A grunt that would have died falls in a heap instead, out of reach, and rises a little later.
func _fall(enemy: SimEnemy) -> void:
	enemy.health = 0.0
	enemy.downed = maxf(0.1, enemy.data.power_duration)
	enemy.statuses.clear()
	enemy.haste_left = 0.0
	enemy_power.emit(enemy, &"fall", [])


func _kill(enemy: SimEnemy, killer: SimTower) -> void:
	enemy.alive = false
	kills += 1
	var bounty := enemy.data.bounty
	if killer != null:
		killer.kills += 1
		bounty += killer.bounty_bonus
	bounty = roundi(bounty * gold_multiplier())
	_lives_for_kill()
	gold += bounty
	gold_earned += bounty
	_spread_statuses(enemy)
	if enemy.data.split_count > 0 and not enemy.data.split_into.is_empty():
		_release_from(enemy, enemy.data.split_into, enemy.data.split_count)
	enemy_killed.emit(enemy, killer, bounty)
	if enemy.structure:
		_on_structure_fallen(enemy)


## Notables such as Inferno and Blight pass a dying enemy's burn or poison to its neighbours.
func _spread_statuses(dead: SimEnemy) -> void:
	var burn: SimStatus = dead.statuses.get(&"burn")
	if burn != null and burn.source != null and burn.source.burn_spread_radius > 0.0:
		var spec := burn.source.effect_spec(&"burn")
		if spec != null:
			for enemy in _hash.query(dead.position, burn.source.burn_spread_radius):
				enemy.apply_status(spec, burn.source, burn.element_multiplier)
	var poison: SimStatus = dead.statuses.get(&"poison")
	if poison != null and poison.source != null and poison.source.poison_spread_count > 0:
		var spec := poison.source.effect_spec(&"poison")
		if spec != null:
			var origin := dead.position
			var nearby := _hash.query(origin, POISON_SPREAD_RANGE)
			var closer := func(a: SimEnemy, b: SimEnemy) -> bool: return a.position.distance_squared_to(origin) < b.position.distance_squared_to(origin)
			nearby.sort_custom(closer)
			for i in mini(poison.source.poison_spread_count, nearby.size()):
				nearby[i].apply_status(spec, poison.source, poison.element_multiplier)


func _remove_dead() -> void:
	var living: Array[SimEnemy] = []
	for enemy in enemies:
		if enemy.alive:
			living.append(enemy)
	enemies = living


func _finish_wave() -> void:
	var finished := current_wave()
	wave_index += 1
	var rules := config.rules
	var points := rules.tree_points_after_wave(wave_index, false)
	if finished.is_boss:
		points += roundi(run_stat(&"tree_points_per_boss", rules.tree_points_per_boss))
	tree.points += points
	var bonus := roundi(run_stat(&"gold_per_wave", rules.gold_per_wave))
	gold += bonus
	gold_earned += bonus
	projectiles.clear()
	_bursts.clear()
	_level_heroes()
	if wave_index >= total_waves() and not is_assault():
		_end_run(true)
	else:
		state = State.BUILDING
		if config.stage != null and config.stage.auto_wave_delay > 0.0:
			break_time_left = config.stage.auto_wave_delay
	wave_cleared.emit(wave_index, points, bonus)
	changed.emit()


func _end_run(won: bool) -> void:
	state = State.WON if won else State.LOST
	projectiles.clear()
	run_ended.emit(won)
	changed.emit()


func _refresh_modifiers() -> void:
	_modifiers.clear()
	_modifiers.append_array(config.run_modifiers)
	_modifiers.append_array(tree.modifiers())
	for skill_id: StringName in _skill_time:
		var skill: SkillData = config.skills.get(skill_id)
		if skill != null:
			_modifiers.append_array(skill.modifiers)
	for effect in _hero_effects:
		_modifiers.append_array((effect[0] as HeroAbility).modifiers)
	_recompute_towers()


## Recomputes every tower's stats, then hands out Void auras: each tower gets the strongest aura
## from another tower in range. Auras never boost the tower giving them.
func _recompute_towers() -> void:
	_apply_hero_auras()
	for tower in towers:
		tower.aura_bonus = 0.0
		tower.recompute(_modifiers)
	var givers: Array[SimTower] = []
	for tower in towers:
		if tower.aura_radius > 0.0 and tower.aura_damage > 0.0:
			givers.append(tower)
	if givers.is_empty():
		return
	for tower in towers:
		var best := 0.0
		for giver in givers:
			if giver != tower and giver.position.distance_to(tower.position) <= giver.aura_radius:
				best = maxf(best, giver.aura_damage)
		if best > 0.0:
			tower.aura_bonus = best
			tower.recompute(_modifiers)


# --- Assault -------------------------------------------------------------------

## Raises the buildings of an assault stage's enemy base. They stand on their road's first point
## (so whatever they release walks that road), but are drawn and targeted on their own cell.
func _place_structures() -> void:
	if config.stage == null:
		return
	var multiplier := config.wave_set.health_multiplier(1) * config.enemy_health_multiplier()
	for spec in config.stage.structures:
		var data: EnemyData = config.enemies.get(spec.enemy) if spec != null else null
		if data == null:
			continue
		var lane := clampi(spec.lane, 0, lane_curves.size() - 1)
		var structure := _make_enemy(data, multiplier, lane, config.element_index(data.element), 0.0)
		structure.structure = true
		structure.phase = maxi(1, spec.phase)
		structure.closes_lanes = spec.closes_lanes
		structure.releases = spec.releases
		structure.release_health = spec.release_health
		structure.position = config.map.cell_center(spec.cell)
		structures.append(structure)
		_structure_cells[spec.cell] = structure


func _on_structure_fallen(structure: SimEnemy) -> void:
	for lane in structure.closes_lanes:
		_closed_lanes[lane] = true
	# What comes out of a fallen building is as strong as the wave being fought.
	var multiplier := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	for i in structure.releases.size():
		var data: EnemyData = config.enemies.get(structure.releases[i])
		if data == null:
			continue
		var released := _make_enemy(data, multiplier * structure.release_health, structure.lane, structure.element, 0.0)
		# They come out one after another: each waits a little behind the one before.
		released.progress = -90.0 * i
		_arrivals.append(released)
		if data.tags.has(&"boss"):
			boss_arrived.emit(released)
	for cell: Vector2i in _structure_cells.keys():
		if _structure_cells[cell] == structure:
			_structure_cells.erase(cell)
	structure_destroyed.emit(structure)
	var advanced := false
	while structure_phase <= total_phases() and structures_left(structure_phase).is_empty():
		structure_phase += 1
		advanced = true
	if structure_phase > total_phases():
		citadel_fallen = true
		# The horde breaks when its citadel falls: nothing more marches in, and whatever the last
		# building released is the final fight.
		_spawner.stop()
	if advanced:
		_recompute_towers()
		phase_changed.emit(structure_phase)


## True while anything released by the last building (the overlord) still walks.
func _overlord_alive() -> bool:
	for enemy in enemies:
		if enemy.alive and enemy.data.tags.has(&"overlord"):
			return true
	for enemy in _arrivals:
		if enemy.alive and enemy.data.tags.has(&"overlord"):
			return true
	return false


func _new_id() -> int:
	_next_id += 1
	return _next_id


# --- Heroes --------------------------------------------------------------------

## The element factor of a hit. Prismatic attackers (Seraphel, Oswin) always strike the element
## each enemy is weakest to.
func _element_multiplier(tower: SimTower, enemy: SimEnemy) -> float:
	if tower.tags.has(&"prismatic"):
		return ElementRules.OPPOSITE_ELEMENT_MULTIPLIER if enemy.element >= 0 else 1.0
	return ElementRules.damage_multiplier(tower.element_indices, enemy.element)


func hero_data(hero_id: StringName) -> HeroData:
	for hero in party:
		if hero.id == hero_id:
			return hero
	return null


## The summoned hero, or null while it is still waiting to be summoned.
func hero_tower(hero_id: StringName) -> SimTower:
	return _heroes_on_board.get(hero_id)


func hero_towers() -> Array[SimTower]:
	var result: Array[SimTower] = []
	for hero in party:
		if _heroes_on_board.has(hero.id):
			result.append(_heroes_on_board[hero.id])
	return result


## Pixels from a hero to the towers its aura reaches.
func hero_aura_radius() -> float:
	return HeroData.AURA_CELLS * config.map.cell_size


func _cell_error(cell: Vector2i) -> String:
	if not config.map.is_inside(cell):
		return "Outside the map"
	if is_path(cell):
		return "Heroes stand beside the road, not on it"
	if _landmark_cells.has(cell):
		return "The enemy's war camp stands here" if _landmark_cells[cell].kind == &"camp" else "The city stands here"
	if _tower_at.has(cell):
		return "There is already a tower here"
	return ""


## Why a hero cannot be summoned onto a cell, or an empty string if it can.
func summon_error(hero_id: StringName, cell: Vector2i) -> String:
	if is_over():
		return "The run is over"
	var hero := hero_data(hero_id)
	if hero == null:
		return "That hero is not in your party"
	if _heroes_on_board.has(hero_id):
		return "%s is already on the field" % hero.display_name
	return _cell_error(cell)


## Summons a hero onto a free cell, for free. Each hero comes once per run.
func summon_hero(hero_id: StringName, cell: Vector2i) -> SimTower:
	if not summon_error(hero_id, cell).is_empty():
		return null
	var hero := hero_data(hero_id)
	var indices: Array[int] = []
	for element_id in hero.attack.elements:
		indices.append(config.element_index(element_id))
	var tower := SimTower.new(_new_id(), hero.attack, cell, config.map.cell_center(cell), 0, indices)
	tower.hero = hero
	towers.append(tower)
	_tower_at[cell] = tower
	_heroes_on_board[hero_id] = tower
	_recompute_towers()
	hero_summoned.emit(tower)
	changed.emit()
	return tower


## Why a hero cannot march to a cell now, or an empty string if it can.
func move_error(tower: SimTower, cell: Vector2i) -> String:
	if is_over():
		return "The run is over"
	if tower == null or not tower.is_hero() or not towers.has(tower):
		return "Only heroes can move"
	if state != State.BUILDING:
		return "Heroes can only move between waves"
	if tower.moved_this_break:
		return "%s has already moved this break" % tower.hero.display_name
	if cell == tower.cell:
		return "%s is already there" % tower.hero.display_name
	return _cell_error(cell)


## Marches a hero to a new cell. A hero can move once in each break.
func move_hero(tower: SimTower, cell: Vector2i) -> bool:
	if not move_error(tower, cell).is_empty():
		return false
	_tower_at.erase(tower.cell)
	tower.cell = cell
	tower.position = config.map.cell_center(cell)
	tower.moved_this_break = true
	_tower_at[cell] = tower
	_recompute_towers()
	hero_moved.emit(tower)
	changed.emit()
	return true


## Why the hero's ability cannot be used now, or an empty string if it can.
func hero_ability_error(hero_id: StringName) -> String:
	if is_over():
		return "The run is over"
	var hero := hero_data(hero_id)
	if hero == null:
		return "That hero is not in your party"
	var tower := hero_tower(hero_id)
	if tower == null:
		return "Summon %s first" % hero.display_name
	if state != State.WAVE:
		return "Abilities can only be used during a wave"
	if tower.ability_cooldown > 0.0:
		return "%s is ready in %d s" % [tower.hero_ability().display_name, ceili(tower.ability_cooldown)]
	return ""


## Uses a summoned hero's ability. `at` is the point picked for an aimed one. Returns false and
## does nothing if it cannot be used now.
func use_hero_ability(hero_id: StringName, at: Vector2 = Vector2.ZERO) -> bool:
	if not hero_ability_error(hero_id).is_empty():
		return false
	var tower := hero_tower(hero_id)
	var ability := tower.hero_ability()
	tower.ability_cooldown = ability.cooldown
	var radius := ability.radius_cells * config.map.cell_size
	var points := PackedVector2Array()
	match ability.target:
		HeroAbility.Target.AIMED:
			points.append(at)
		HeroAbility.Target.SELF:
			points.append(tower.position)
		HeroAbility.Target.CROWDS:
			points = crowded_points(ability.strikes, radius)
	var hits := 0
	var strikes := 1 if ability.target == HeroAbility.Target.CROWDS else maxi(1, ability.strikes)
	for strike in strikes:
		if ability.target == HeroAbility.Target.BOARD:
			for enemy in enemies:
				hits += _ability_hit(tower, ability, enemy)
		else:
			for point in points:
				for enemy in enemies:
					if enemy.position.distance_to(point) <= radius:
						hits += _ability_hit(tower, ability, enemy)
	if ability.burst_damage > 0.0:
		for point in points:
			_bursts.append([maxf(ability.hold_seconds, 0.1), point, radius, ability.burst_damage * _ability_growth(), tower])
	if ability.heal_lives > 0:
		lives = maxi(lives, mini(lives + ability.heal_lives, starting_lives))
	if ability.resets_skills:
		_skill_cooldowns.clear()
	if ability.resets_heroes:
		for other: SimTower in _heroes_on_board.values():
			if other != tower:
				other.ability_cooldown = 0.0
	if ability.duration > 0.0:
		_hero_effects.append([ability, ability.duration, tower])
		if ability.lives_per_kill > 0:
			_lives_from_kills = 0
		_refresh_modifiers()
	if points.is_empty():
		points.append(config.map.size_in_pixels() * 0.5)
	hero_ability_used.emit(tower, ability, points)
	changed.emit()
	return true


## Ability damage keeps pace with enemy health, as skill damage does.
func _ability_growth() -> float:
	return config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()


## One enemy struck by a hero's ability. Returns 1 if it was there to be hit.
func _ability_hit(tower: SimTower, ability: HeroAbility, enemy: SimEnemy) -> int:
	if not enemy.alive:
		return 0
	var boss := enemy.data.tags.has(&"boss")
	if ability.execute_below > 0.0 and not boss and enemy.health <= enemy.max_health * ability.execute_below:
		_damage(enemy, enemy.health + 1.0, tower)
		return 1
	var multiplier := _element_multiplier(tower, enemy)
	if ability.hits_weakness:
		multiplier = ElementRules.OPPOSITE_ELEMENT_MULTIPLIER if enemy.element >= 0 else 1.0
	if ability.damage > 0.0:
		var damage := ability.damage * _ability_growth() * (ability.boss_damage_multiplier if boss else 1.0)
		_damage(enemy, CombatMath.hit_damage(damage, multiplier, enemy.effective_armour(), enemy.damage_taken_bonus()), tower)
		if not enemy.alive:
			return 1
	for spec in ability.status_effects:
		var scaled := spec.duplicate() as StatusEffectData
		scaled.damage_per_second *= _ability_growth()
		enemy.apply_status(scaled, tower, multiplier)
	if ability.hold_seconds > 0.0:
		var hold := StatusEffectData.new()
		if boss:
			hold.kind = &"slow"
			hold.slow = 0.6
		else:
			hold.kind = &"root"
		hold.duration = ability.hold_seconds
		enemy.apply_status(hold, tower, multiplier)
	if ability.send_to_start and (ability.send_bosses or not boss):
		enemy.progress = 0.0
		enemy.position = lane_curves[enemy.lane].sample_baked(0.0)
	elif ability.knockback > 0.0 and enemy.knock_back(ability.knockback) > 0.0:
		enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)
	return 1


## Up to `count` points that each cover the most enemies within `radius`, no enemy counted twice.
func crowded_points(count: int, radius: float) -> PackedVector2Array:
	var result := PackedVector2Array()
	var taken: Dictionary[int, bool] = {}
	for i in count:
		var best := -1
		var best_point := Vector2.ZERO
		for enemy in enemies:
			if not enemy.alive or taken.has(enemy.id):
				continue
			var near := 0
			for other in enemies:
				if other.alive and not taken.has(other.id) and other.position.distance_to(enemy.position) <= radius:
					near += 1
			if near > best:
				best = near
				best_point = enemy.position
		if best <= 0:
			break
		result.append(best_point)
		for enemy in enemies:
			if enemy.position.distance_to(best_point) <= radius:
				taken[enemy.id] = true
	return result


func _tick_heroes(delta: float) -> void:
	for tower: SimTower in _heroes_on_board.values():
		tower.ability_cooldown = maxf(0.0, tower.ability_cooldown - delta)
	if not _hero_effects.is_empty():
		var running: Array[Array] = []
		for effect in _hero_effects:
			effect[1] -= delta
			if effect[1] > 0.0:
				running.append(effect)
		if running.size() != _hero_effects.size():
			_hero_effects = running
			_refresh_modifiers()
	if not _bursts.is_empty():
		var waiting: Array[Array] = []
		for burst in _bursts:
			burst[0] -= delta
			if burst[0] > 0.0:
				waiting.append(burst)
				continue
			for enemy in enemies:
				if enemy.alive and enemy.position.distance_to(burst[1]) <= burst[2]:
					_damage(enemy, CombatMath.hit_damage(burst[3], 1.0, enemy.effective_armour(), enemy.damage_taken_bonus()), burst[4])
		_bursts = waiting


## Kills pay this many times their gold while an ability such as Eclipse runs.
func gold_multiplier() -> float:
	var result := 1.0
	for effect in _hero_effects:
		result = maxf(result, (effect[0] as HeroAbility).gold_multiplier)
	return result


## True while an ability such as Last Light keeps enemies from leaking.
func is_warded() -> bool:
	for effect in _hero_effects:
		if (effect[0] as HeroAbility).ward:
			return true
	return false


## Seconds left on a hero's running ability, or 0.
func hero_effect_time(hero_id: StringName) -> float:
	var left := 0.0
	for effect in _hero_effects:
		if (effect[2] as SimTower).hero.id == hero_id:
			left = maxf(left, effect[1])
	return left


func _lives_for_kill() -> void:
	for effect in _hero_effects:
		var ability: HeroAbility = effect[0]
		if ability.lives_per_kill > 0 and _lives_from_kills < ability.lives_per_kill_max:
			var gain := mini(ability.lives_per_kill, ability.lives_per_kill_max - _lives_from_kills)
			_lives_from_kills += gain
			lives += gain
			return


## Every hero on the field gains a level for the wave it fought, and Elowen's aura gives lives back.
func _level_heroes() -> void:
	_hero_effects.clear()
	for tower: SimTower in _heroes_on_board.values():
		if tower.hero_level < HeroData.MAX_LEVEL:
			tower.hero_level += 1
			hero_leveled.emit(tower)
		var hero := tower.hero
		if hero.aura_lives_per_towers > 0:
			var near := 0
			for other in towers:
				if not other.is_hero() and other.position.distance_to(tower.position) <= hero_aura_radius():
					near += 1
			lives += mini(near / hero.aura_lives_per_towers, hero.aura_lives_max)
	_refresh_modifiers()


## Gives every tower the auras of the heroes near it, and every hero the levels Ilyra's aura adds.
func _apply_hero_auras() -> void:
	var bonus_levels := 0
	for tower: SimTower in _heroes_on_board.values():
		bonus_levels += tower.hero.aura_hero_levels
	var radius := hero_aura_radius()
	for tower in towers:
		tower.hero_aura.clear()
		if tower.is_hero():
			tower.hero_level_bonus = bonus_levels
			continue
		for hero: SimTower in _heroes_on_board.values():
			if not hero.hero.aura.is_empty() and hero.position.distance_to(tower.position) <= radius:
				tower.hero_aura.append_array(hero.hero.aura)
