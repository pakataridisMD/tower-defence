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

enum State { BUILDING, WAVE, WON, LOST }

## Simulation step used by the game scene. Tests may use bigger steps.
const STEP := 1.0 / 60.0
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
## Next lane for groups that share their enemies out over every lane.
var _lane_turn := 0
## Enemies split off or summoned during a step, added once the step's loops are done.
var _arrivals: Array[SimEnemy] = []
## Seconds of wave time until each skill can be used again, by skill id.
var _skill_cooldowns: Dictionary[StringName, float] = {}
## Seconds left on each skill whose modifiers are still running, by skill id.
var _skill_time: Dictionary[StringName, float] = {}


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
	_refresh_modifiers()


# --- Queries -----------------------------------------------------------------

func total_waves() -> int:
	return config.wave_set.waves.size()


## The wave being fought, or the next one while building. Null once the run is over.
func current_wave() -> WaveData:
	var index := wave_index
	if index >= total_waves():
		return null
	return config.wave_set.waves[index]


## 1-based number of the current or next wave.
func wave_number() -> int:
	return mini(wave_index + 1, total_waves())


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
	for enemy in enemies:
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
	if tower == null or tower.ascendancy != null:
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
	return floori(tower.price_paid * clampf(run_stat(&"sell_refund", config.rules.sell_refund), 0.0, 1.0))


## A run-wide number, such as gold per wave, after the meta tree's and the skill web's bonuses.
func run_stat(stat: StringName, base: float) -> float:
	return StatCalculator.compute(stat, base, _modifiers)


func sell_tower(tower: SimTower) -> int:
	if not towers.has(tower):
		return 0
	var refund := sell_value(tower)
	gold += refund
	towers.erase(tower)
	_tower_at.erase(tower.cell)
	_recompute_towers()
	changed.emit()
	return refund


func start_next_wave() -> bool:
	if state != State.BUILDING or wave_index >= total_waves():
		return false
	var wave := current_wave()
	state = State.WAVE
	time_in_wave = 0.0
	_wave_element = config.element_index(wave.element)
	_spawner.start(wave)
	_taken_this_break.clear()
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
	if _spawner.is_finished() and enemies.is_empty():
		_finish_wave()


func _spawn(delta: float) -> void:
	var multiplier := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	var wave := current_wave()
	if wave != null:
		multiplier *= wave.health_multiplier
	for group in _spawner.advance(delta):
		var data: EnemyData = config.enemies.get(group.enemy)
		if data == null:
			continue
		var lane := group.lane
		if lane < 0:
			lane = _lane_turn
			_lane_turn = (_lane_turn + 1) % lane_curves.size()
		var element := _wave_element
		if not group.element.is_empty():
			element = config.element_index(group.element)
		enemies.append(_make_enemy(data, multiplier, mini(lane, lane_curves.size() - 1), element, 0.0))


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


func _move_enemies(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		enemy.progress += enemy.speed() * delta
		if enemy.progress >= lane_lengths[enemy.lane]:
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


## Healing, summoning and changing element.
func _tick_traits(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		var data := enemy.data
		if enemy.is_regenerating() and enemy.health < enemy.max_health:
			enemy.health = minf(enemy.max_health, enemy.health + enemy.max_health * data.regen_per_second * delta)
		if data.summon_interval > 0.0 and not data.summon.is_empty():
			enemy.summon_timer -= delta
			if enemy.summon_timer <= 0.0:
				enemy.summon_timer += data.summon_interval
				_release_from(enemy, data.summon, data.summon_count)
		if data.prismatic_interval > 0.0:
			enemy.prism_timer -= delta
			if enemy.prism_timer <= 0.0:
				enemy.prism_timer += data.prismatic_interval
				enemy.element = (maxi(enemy.element, 0) + 1) % ElementData.RING_SIZE


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
				if not enemy.alive:
					break
			status.time_left -= delta
			if status.time_left <= 0.0:
				enemy.statuses.erase(kind)
				if kind == &"stun":
					enemy.stun_immunity = SimEnemy.STUN_IMMUNITY


func _rebuild_hash() -> void:
	_hash.clear()
	for enemy in enemies:
		if enemy.alive:
			_hash.insert(enemy)


func _update_towers(delta: float) -> void:
	for tower in towers:
		tower.cooldown -= delta
		if tower.cooldown > 0.0:
			continue
		var target := _find_target(tower)
		if target == null:
			tower.cooldown = 0.0
			continue
		_attack(tower, target)
		tower.cooldown += CombatMath.attack_interval(tower.attacks_per_second)


## The enemy in range that is closest to leaving the map.
func _find_target(tower: SimTower) -> SimEnemy:
	var best: SimEnemy = null
	var best_left := INF
	for enemy in _hash.query(tower.position, tower.attack_range):
		var left := distance_to_exit(enemy)
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
	if not enemy.alive:
		return
	var multiplier := ElementRules.damage_multiplier(tower.element_indices, enemy.element)
	_damage(enemy, CombatMath.hit_damage(damage, multiplier, enemy.effective_armour(), enemy.damage_taken_bonus()), tower)
	if enemy.alive:
		for spec in tower.effects:
			enemy.apply_status(spec, tower, multiplier)
		if tower.knockback > 0.0 and enemy.knock_back(tower.knockback) > 0.0:
			enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)


func _damage(enemy: SimEnemy, amount: float, source: SimTower) -> void:
	if not enemy.alive or amount <= 0.0:
		return
	var dealt := minf(amount, enemy.health)
	enemy.health -= amount
	if source != null:
		source.damage_dealt += dealt
	if enemy.health <= 0.0:
		_kill(enemy, source)


func _kill(enemy: SimEnemy, killer: SimTower) -> void:
	enemy.alive = false
	kills += 1
	var bounty := enemy.data.bounty
	if killer != null:
		killer.kills += 1
		bounty += killer.bounty_bonus
	gold += bounty
	gold_earned += bounty
	_spread_statuses(enemy)
	if enemy.data.split_count > 0 and not enemy.data.split_into.is_empty():
		_release_from(enemy, enemy.data.split_into, enemy.data.split_count)
	enemy_killed.emit(enemy, killer, bounty)


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
	if wave_index >= total_waves():
		_end_run(true)
	else:
		state = State.BUILDING
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
	_recompute_towers()


## Recomputes every tower's stats, then hands out Void auras: each tower gets the strongest aura
## from another tower in range. Auras never boost the tower giving them.
func _recompute_towers() -> void:
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


func _new_id() -> int:
	_next_id += 1
	return _next_id
