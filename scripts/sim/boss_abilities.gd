class_name BossAbilities
extends RefCounted
## The bosses' own abilities in a run (see EnemyData, group "Boss abilities"): healing, a barrier
## that soaks up damage, binding the strongest towers, and the overlord's fireball that destroys a
## tower and leaves a burning ruin on its cell until the wave ends.
##
## Every ability, and the older boss tricks, is announced on RunSim.boss_ability so the board can
## draw it and the boss can shout.

## Seconds a fireball flies from the boss's hand to the tower.
const FIREBALL_FLIGHT := 1.4

## The run, held weakly: the run owns this, and a strong reference both ways would never be freed.
var _sim_ref: WeakRef
var _sim: RunSim:
	get:
		return _sim_ref.get_ref() as RunSim
## Fireballs in the air: [boss, tower, seconds left].
var _fireballs: Array[Array] = []
## Cells where a destroyed tower burns, until the wave ends.
var ruins: Dictionary[Vector2i, bool] = {}


func _init(sim: RunSim) -> void:
	_sim_ref = weakref(sim)


## True where a destroyed tower's ruin still burns: nothing can be built there until the wave ends.
func is_ruin(cell: Vector2i) -> bool:
	return ruins.has(cell)


## Fireballs in the air, for the board: [boss, tower, seconds left].
func fireballs() -> Array[Array]:
	return _fireballs


func tick(delta: float) -> void:
	for enemy in _sim.enemies:
		if not enemy.alive or enemy.transforming > 0.0 or enemy.fleeing or enemy.structure:
			continue
		var data := enemy.data
		if enemy.barrier_left > 0.0:
			enemy.barrier_left -= delta
			if enemy.barrier_left <= 0.0:
				enemy.barrier_left = 0.0
				enemy.barrier = 0.0
		# A stunned or rooted boss still heals and shields, but cannot bind or hurl fire.
		var held := enemy.has_status(&"stun") or enemy.has_status(&"root")
		if data.heal_interval > 0.0 and data.heal_amount > 0.0:
			enemy.heal_timer -= delta
			if enemy.heal_timer <= 0.0 and enemy.health < enemy.max_health:
				enemy.heal_timer = data.heal_interval
				_heal(enemy)
		if data.shield_interval > 0.0 and data.shield_amount > 0.0:
			enemy.shield_timer -= delta
			if enemy.shield_timer <= 0.0:
				enemy.shield_timer = data.shield_interval
				enemy.barrier = enemy.max_health * data.shield_amount
				enemy.barrier_left = maxf(0.5, data.shield_duration)
				_sim.boss_ability.emit(enemy, &"shield", [])
		if data.bind_interval > 0.0 and data.bind_duration > 0.0 and not held:
			enemy.bind_timer -= delta
			if enemy.bind_timer <= 0.0:
				var bound := _bind(enemy)
				# With nothing in reach it tries again soon.
				enemy.bind_timer = data.bind_interval if not bound.is_empty() else 1.0
		if data.doom_interval > 0.0 and not held:
			enemy.doom_timer -= delta
			if enemy.doom_timer <= 0.0:
				var target := _doom_target(enemy)
				enemy.doom_timer = data.doom_interval if target != null else 1.0
				if target != null:
					_fireballs.append([enemy, target, FIREBALL_FLIGHT])
					_sim.boss_ability.emit(enemy, &"fireball", [target])
	_fly(delta)


## Heals a share of its life; burns and poison halve it.
func _heal(enemy: SimEnemy) -> void:
	var share := enemy.data.heal_amount
	if enemy.has_status(&"burn") or enemy.has_status(&"poison"):
		share *= 0.5
	enemy.health = minf(enemy.max_health, enemy.health + enemy.max_health * share)
	_sim.boss_ability.emit(enemy, &"heal", [])


## Binds the strongest towers within reach that are not bound or silenced already. Returns them.
func _bind(enemy: SimEnemy) -> Array[SimTower]:
	var data := enemy.data
	var reach := data.bind_radius * data.bind_radius if data.bind_radius > 0.0 else INF
	var free: Array[SimTower] = []
	for tower in _sim.towers:
		if tower.silenced <= 0.0 and tower.position.distance_squared_to(enemy.position) <= reach:
			free.append(tower)
	free.sort_custom(func(a: SimTower, b: SimTower) -> bool: return _strength(a) > _strength(b))
	var bound: Array[SimTower] = []
	for tower in free.slice(0, maxi(1, data.bind_count)):
		tower.silenced = maxf(tower.silenced, data.bind_duration)
		bound.append(tower)
	if not bound.is_empty():
		_sim.boss_ability.emit(enemy, &"bind", bound)
	return bound


## The tower the fireball goes for: the strongest in reach, never a hero.
func _doom_target(enemy: SimEnemy) -> SimTower:
	var reach := enemy.data.doom_radius * enemy.data.doom_radius if enemy.data.doom_radius > 0.0 else INF
	var best: SimTower = null
	for tower in _sim.towers:
		if tower.is_hero() or tower.position.distance_squared_to(enemy.position) > reach:
			continue
		if _is_targeted(tower):
			continue
		if best == null or _strength(tower) > _strength(best):
			best = tower
	return best


func _is_targeted(tower: SimTower) -> bool:
	for ball in _fireballs:
		if ball[1] == tower:
			return true
	return false


static func _strength(tower: SimTower) -> float:
	return tower.damage * tower.attacks_per_second


func _fly(delta: float) -> void:
	if _fireballs.is_empty():
		return
	var flying: Array[Array] = []
	for ball in _fireballs:
		ball[2] -= delta
		if ball[2] > 0.0:
			flying.append(ball)
			continue
		var tower: SimTower = ball[1]
		# Sold while the fire flew: the ball bursts on empty ground.
		if not _sim.towers.has(tower):
			continue
		_sim.destroy_tower(tower)
		ruins[tower.cell] = true
		_sim.boss_ability.emit(ball[0], &"destroy_tower", [tower])
	_fireballs = flying


## Takes damage off the barrier first and returns what gets through.
func absorb(enemy: SimEnemy, amount: float) -> float:
	if enemy.barrier <= 0.0:
		return amount
	var soaked := minf(enemy.barrier, amount)
	enemy.barrier -= soaked
	if enemy.barrier <= 0.0:
		enemy.barrier = 0.0
		enemy.barrier_left = 0.0
		_sim.boss_ability.emit(enemy, &"shield_break", [])
	return amount - soaked


## The wave is over: the ruins stop burning and the fire in the air goes out.
func clear() -> void:
	ruins.clear()
	_fireballs.clear()
