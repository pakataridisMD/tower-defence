extends GutTest
## Elemental affinities (ElementRules.PROFILES): weak to the opposite element, immune to some, and
## Hulking elites (SpawnGroup.elite) that only the opposite element cuts deep.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const FIRE := 0
const STORM := 1
const NATURE := 2
const WATER := 3
const EARTH := 4
const VOID := 5

var registry: Node
var immune_hits: Array = []


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	immune_hits = []


func _sim(groups: Array[SpawnGroup], element: StringName = &"water") -> RunSim:
	var config := RunConfig.from_registry(registry, &"switchback")
	var wave := WaveData.new()
	wave.element = element
	wave.groups = groups
	var waves := WaveSet.new()
	waves.id = &"test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	config.wave_set = waves
	var sim := RunSim.new(config)
	sim.enemy_immune.connect(func(e: SimEnemy, t: SimTower) -> void: immune_hits.append([e, t]))
	return sim


func _group(enemy: StringName, count: int = 1, elite := false) -> SpawnGroup:
	var group := SpawnGroup.new()
	group.enemy = enemy
	group.count = count
	group.spawn_interval = 0.1
	group.elite = elite
	return group


func _spawn_all(sim: RunSim) -> void:
	sim.start_next_wave()
	for i in 100:
		sim._spawn(RunSim.STEP)


func _tower(sim: RunSim, elements: Array[int], at: Vector2) -> SimTower:
	var data: TowerData = registry.towers.values()[0]
	var tower := SimTower.new(sim._new_id(), data, Vector2i.ZERO, at, 0, elements)
	tower.damage = 100.0
	tower.attack_range = 300.0
	tower.splash_radius = 0.0
	tower.armour_ignore = 0.0
	sim.towers.append(tower)
	return tower


func _ints(values: Array) -> Array[int]:
	var result: Array[int] = []
	result.assign(values)
	return result


func test_profiles_by_ring_steps() -> void:
	assert_eq(ElementRules.steps(FIRE, WATER), 3)
	assert_eq(ElementRules.steps(FIRE, VOID), 1)
	assert_eq(ElementRules.steps(STORM, VOID), 2)
	assert_eq(ElementRules.damage_multiplier(_ints([FIRE]), FIRE, ElementRules.ATTUNED), 0.0)
	assert_eq(ElementRules.damage_multiplier(_ints([WATER]), FIRE, ElementRules.ATTUNED), 2.0)
	assert_eq(ElementRules.damage_multiplier(_ints([STORM]), FIRE, ElementRules.WARDED), 0.5)
	assert_eq(ElementRules.damage_multiplier(_ints([NATURE]), FIRE, ElementRules.WARDED), 1.0)
	assert_eq(ElementRules.damage_multiplier(_ints([WATER]), FIRE, ElementRules.TANK), 2.0)
	assert_eq(ElementRules.damage_multiplier(_ints([EARTH]), FIRE, ElementRules.TANK), 0.6)
	assert_eq(ElementRules.immunities(FIRE, ElementRules.WARDED), _ints([FIRE]))
	assert_true(ElementRules.immunities(FIRE, ElementRules.PLAIN).is_empty())


func test_a_hybrid_is_never_fully_stopped() -> void:
	# Fire + Water against an attuned Fire enemy: half of nothing and half of double.
	assert_eq(ElementRules.damage_multiplier(_ints([FIRE, WATER]), FIRE, ElementRules.ATTUNED), 1.0)


func test_an_immune_enemy_takes_nothing_and_says_so() -> void:
	var sim := _sim([_group(&"brinecaller")])
	_spawn_all(sim)
	var caller := sim.enemies[0]
	assert_eq(caller.affinity, ElementRules.ATTUNED)
	assert_eq(caller.element, WATER)
	var water := _tower(sim, _ints([WATER]), caller.position)
	var slow := StatusEffectData.new()
	slow.kind = &"slow"
	slow.slow = 0.5
	slow.duration = 3.0
	water.effects = [slow] as Array[StatusEffectData]
	var before := caller.health
	sim._hit(water, caller, 100.0)
	assert_eq(caller.health, before, "water does nothing to a Brinecaller")
	assert_true(caller.statuses.is_empty(), "nor do its effects")
	assert_eq(immune_hits.size(), 1)
	var fire := _tower(sim, _ints([FIRE]), caller.position)
	sim._hit(fire, caller, 10.0)
	assert_almost_eq(before - caller.health, 20.0, 0.01, "fire does double")


func test_towers_do_not_aim_at_what_they_cannot_hurt() -> void:
	var sim := _sim([_group(&"brinecaller")])
	_spawn_all(sim)
	var caller := sim.enemies[0]
	sim._rebuild_hash()
	var water := _tower(sim, _ints([WATER]), caller.position)
	var fire := _tower(sim, _ints([FIRE]), caller.position)
	assert_null(sim._find_target(water))
	assert_eq(sim._find_target(fire), caller)


func test_a_plain_enemy_keeps_the_old_rule() -> void:
	var sim := _sim([_group(&"grunt")], &"fire")
	_spawn_all(sim)
	var grunt := sim.enemies[0]
	assert_eq(grunt.affinity, ElementRules.PLAIN)
	assert_eq(grunt.element_multiplier(_ints([FIRE])), 0.5)
	assert_eq(grunt.element_multiplier(_ints([WATER])), 1.5)
	assert_eq(grunt.weakness_multiplier(), 1.5)


func test_a_hulking_elite_is_a_tank() -> void:
	var sim := _sim([_group(&"grunt"), _group(&"grunt", 1, true)], &"fire")
	_spawn_all(sim)
	var plain: SimEnemy = sim.enemies[0]
	var elite: SimEnemy = sim.enemies[1]
	assert_false(plain.elite)
	assert_true(elite.elite)
	assert_almost_eq(elite.max_health, plain.max_health * SimEnemy.ELITE_HEALTH, 0.01)
	assert_eq(elite.armour, plain.armour + SimEnemy.ELITE_ARMOUR)
	assert_almost_eq(elite.base_speed, plain.base_speed * SimEnemy.ELITE_SPEED, 0.01)
	assert_eq(elite.affinity, ElementRules.TANK)
	assert_eq(elite.bounty(), plain.data.bounty * SimEnemy.ELITE_BOUNTY)
	assert_eq(elite.leak_damage(), plain.data.leak_damage * SimEnemy.ELITE_LEAK)
	assert_eq(elite.display_name(), "Hulking Grunt")
	assert_eq(elite.element_multiplier(_ints([WATER])), 2.0)
	assert_eq(elite.element_multiplier(_ints([STORM])), 0.6)


func test_every_affinity_in_the_data_is_known() -> void:
	var counts := {}
	for enemy: EnemyData in registry.enemies.values():
		assert_true(ElementRules.PROFILES.has(enemy.affinity), "%s has a known affinity" % enemy.id)
		counts[enemy.affinity] = counts.get(enemy.affinity, 0) + 1
	for profile in [ElementRules.ATTUNED, ElementRules.WARDED, ElementRules.TANK]:
		assert_gt(counts.get(profile, 0), 3, "several kinds are %s" % profile)


func test_the_campaign_brings_hulking_elites() -> void:
	var waves: WaveSet = load("res://data/waves/c_ember_2.tres")
	var elites := 0
	for wave in waves.waves:
		for group in wave.groups:
			if group.elite:
				elites += group.count
	assert_gt(elites, 0)
