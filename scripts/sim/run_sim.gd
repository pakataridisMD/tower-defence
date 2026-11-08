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
signal projectile_landed(projectile: SimProjectile)
signal run_ended(won: bool)

enum State { BUILDING, WAVE, WON, LOST }

## Simulation step used by the game scene. Tests may use bigger steps.
const STEP := 1.0 / 60.0
## How far a dying enemy's poison can jump.
const POISON_SPREAD_RANGE := 160.0

var config: RunConfig
var state := State.BUILDING
var gold := 0
var lives := 0
## Waves cleared so far. The next wave to start is wave_index + 1.
var wave_index := 0
var tree: TreeState
var enemies: Array[SimEnemy] = []
var towers: Array[SimTower] = []
var projectiles: Array[SimProjectile] = []
var path_curve := Curve2D.new()
var path_length := 0.0
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


func _init(p_config: RunConfig) -> void:
	config = p_config
	var rules := config.rules
	gold = roundi(StatCalculator.compute(&"starting_gold", rules.starting_gold, config.run_modifiers))
	lives = roundi(StatCalculator.compute(&"starting_lives", rules.starting_lives, config.run_modifiers))
	var start_points := roundi(StatCalculator.compute(&"starting_tree_points", rules.starting_tree_points, config.run_modifiers))
	tree = TreeState.new(TreeGraph.new(config.tree_nodes), start_points)
	tree.lock(config.locked_tree_nodes)
	for point in config.map.path_points():
		path_curve.add_point(point)
	path_length = path_curve.get_baked_length()
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
	return tree.unlocked_towers().has(tower_id)


func tower_at(cell: Vector2i) -> SimTower:
	return _tower_at.get(cell)


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
	tower.recompute(_modifiers)
	gold -= price
	towers.append(tower)
	_tower_at[cell] = tower
	changed.emit()
	return tower


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
	_spawn(delta)
	_move_enemies(delta)
	if state != State.WAVE:
		return
	_tick_statuses(delta)
	_rebuild_hash()
	_update_towers(delta)
	_update_projectiles(delta)
	_remove_dead()
	if _spawner.is_finished() and enemies.is_empty():
		_finish_wave()


func _spawn(delta: float) -> void:
	var multiplier := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	for enemy_id in _spawner.advance(delta):
		var data: EnemyData = config.enemies.get(enemy_id)
		if data == null:
			continue
		var enemy := SimEnemy.new(_new_id(), data, multiplier)
		enemy.position = path_curve.sample_baked(0.0)
		enemies.append(enemy)


func _move_enemies(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		enemy.progress += enemy.speed() * delta
		if enemy.progress >= path_length:
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
			enemy.position = path_curve.sample_baked(enemy.progress)


func _tick_statuses(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive or enemy.statuses.is_empty():
			continue
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


## The enemy in range that is furthest along the path.
func _find_target(tower: SimTower) -> SimEnemy:
	var best: SimEnemy = null
	for enemy in _hash.query(tower.position, tower.attack_range):
		if best == null or enemy.progress > best.progress:
			best = enemy
	return best


func _attack(tower: SimTower, target: SimEnemy) -> void:
	tower.facing = (target.position - tower.position).angle()
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
	var multiplier := ElementRules.damage_multiplier(tower.element_indices, _wave_element)
	_damage(enemy, CombatMath.hit_damage(damage, multiplier, enemy.armour, enemy.damage_taken_bonus()), tower)
	if enemy.alive:
		for spec in tower.effects:
			enemy.apply_status(spec, tower, multiplier)


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
	for tower in towers:
		tower.recompute(_modifiers)


func _new_id() -> int:
	_next_id += 1
	return _next_id
