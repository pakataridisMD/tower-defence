extends GutTest
## Each kind of the horde's rank and file has its own power: grunts rise once, runners phase out,
## brutes drive the horde on, menders heal it, splitters turn to stone, the warded block hits and the
## Warden breathes fire on towers.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _sim(groups: Array[SpawnGroup]) -> RunSim:
	var config := RunConfig.from_registry(registry, &"switchback")
	var wave := WaveData.new()
	wave.element = &"fire"
	wave.groups = groups
	var waves := WaveSet.new()
	waves.id = &"test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	config.wave_set = waves
	var sim := RunSim.new(config)
	sim.tree.points = 20
	sim.gold = 5000
	return sim


func _group(enemy: StringName, count: int = 1) -> SpawnGroup:
	var group := SpawnGroup.new()
	group.enemy = enemy
	group.count = count
	group.spawn_interval = 0.1
	return group


func _spawn_all(sim: RunSim) -> void:
	sim.start_next_wave()
	for i in 120:
		sim._spawn(RunSim.STEP)
	# Only a share of some kinds carry their power, picked by id; the enemies under test all do.
	for enemy in sim.enemies:
		enemy.has_power = true
		enemy.shield_up = enemy.data.power == &"block"


func _effect(kind: StringName) -> StatusEffectData:
	var spec := StatusEffectData.new()
	spec.kind = kind
	spec.duration = 5.0
	spec.damage_per_second = 0.0
	return spec


func _tower(sim: RunSim, at: Vector2, damage: float) -> SimTower:
	var data: TowerData = registry.towers.values()[0]
	var tower := SimTower.new(sim._new_id(), data, Vector2i.ZERO, at, 0, [] as Array[int])
	tower.damage = damage
	return tower


## Ticks the powers for `seconds` in small steps.
func _tick(sim: RunSim, seconds: float) -> void:
	var left := seconds
	while left > 0.0:
		sim._tick_powers(minf(0.05, left))
		left -= 0.05


func test_every_rank_and_file_enemy_has_a_power() -> void:
	for id: StringName in [&"grunt", &"runner", &"brute", &"mender", &"splitter", &"warded", &"warden"]:
		var data: EnemyData = registry.enemies[id]
		assert_false(data.power.is_empty(), "%s has a power" % id)
		assert_false(data.power_text().is_empty(), "%s explains its power" % id)


func test_a_grunt_falls_then_rises_once() -> void:
	var sim := _sim([_group(&"grunt")])
	_spawn_all(sim)
	var grunt := sim.enemies[0]
	var seen: Array[StringName] = []
	sim.enemy_power.connect(func(_e: SimEnemy, power: StringName, _t: Array) -> void: seen.append(power))
	sim._damage(grunt, 99999.0, null)
	assert_true(grunt.alive, "it falls instead of dying")
	assert_true(grunt.untouchable())
	assert_eq(grunt.speed(), 0.0, "a heap of bones does not walk")
	assert_eq(sim.kills, 0)
	sim._damage(grunt, 99999.0, null)
	assert_true(grunt.alive, "nothing hurts it while it is down")
	_tick(sim, grunt.data.power_duration + 0.1)
	assert_false(grunt.untouchable(), "it stands again")
	assert_almost_eq(grunt.health, grunt.max_health * grunt.data.power_amount, 0.01)
	assert_eq(seen, [&"fall", &"rise"] as Array[StringName])
	sim._damage(grunt, 99999.0, null)
	assert_false(grunt.alive, "the second time it stays dead")
	assert_eq(sim.kills, 1)


func test_a_burning_grunt_stays_down() -> void:
	var sim := _sim([_group(&"grunt")])
	_spawn_all(sim)
	var grunt := sim.enemies[0]
	grunt.apply_status(_effect(&"burn"), null, 1.0)
	sim._damage(grunt, 99999.0, null)
	assert_false(grunt.alive)


func test_a_runner_phases_out_when_struck_and_shots_pass_through() -> void:
	var sim := _sim([_group(&"runner")])
	_spawn_all(sim)
	var runner := sim.enemies[0]
	runner.power_timer = 0.0
	sim._damage(runner, 1.0, null)
	assert_true(runner.is_phased(), "the blow lands, then it phases")
	var before := runner.health
	sim._damage(runner, 10.0, null)
	assert_eq(runner.health, before, "nothing hits it")
	sim._rebuild_hash()
	assert_true(sim._hash.query(runner.position, 50.0).is_empty(), "towers cannot aim at it")
	assert_gt(runner.speed(), 0.0, "it keeps running")
	_tick(sim, runner.data.power_duration + 0.1)
	assert_false(runner.is_phased())
	sim._damage(runner, 10.0, null)
	assert_lt(runner.health, before)
	assert_false(runner.is_phased(), "not again until it has gathered itself")


func test_stunned_enemies_cannot_use_powers() -> void:
	var sim := _sim([_group(&"runner")])
	_spawn_all(sim)
	var runner := sim.enemies[0]
	runner.apply_status(_effect(&"stun"), null, 1.0)
	runner.power_timer = 0.0
	sim._damage(runner, 1.0, null)
	assert_false(runner.is_phased())


func test_a_brute_war_cry_drives_the_horde_on() -> void:
	var sim := _sim([_group(&"brute"), _group(&"grunt")])
	_spawn_all(sim)
	var brute := sim.enemies[0]
	var grunt := sim.enemies[1]
	var calm := grunt.speed()
	brute.power_timer = 0.0
	_tick(sim, 0.05)
	assert_almost_eq(grunt.speed(), calm * (1.0 + brute.data.power_amount), 0.01, "faster")
	assert_almost_eq(brute.speed(), brute.base_speed, 0.01, "not the brute itself")
	_tick(sim, brute.data.power_duration + 0.1)
	assert_almost_eq(grunt.speed(), calm, 0.01, "it wears off")


func test_a_mender_heals_the_hurt_but_not_the_burning() -> void:
	var sim := _sim([_group(&"mender"), _group(&"brute"), _group(&"grunt")])
	_spawn_all(sim)
	var mender := sim.enemies[0]
	var brute := sim.enemies[1]
	var grunt := sim.enemies[2]
	brute.health = brute.max_health * 0.5
	grunt.health = grunt.max_health * 0.5
	grunt.apply_status(_effect(&"burn"), null, 1.0)
	mender.power_timer = 0.0
	_tick(sim, 0.05)
	assert_almost_eq(brute.health, brute.max_health * (0.5 + mender.data.power_amount), 0.01)
	assert_eq(grunt.health, grunt.max_health * 0.5, "burning, so no healing")
	mender.apply_status(_effect(&"poison"), null, 1.0)
	var before := brute.health
	_tick(sim, mender.data.power_interval + 0.1)
	assert_eq(brute.health, before, "a poisoned mender cannot heal")


func test_a_mender_waits_for_someone_to_be_hurt() -> void:
	var sim := _sim([_group(&"mender")])
	_spawn_all(sim)
	var mender := sim.enemies[0]
	var casts := [0]
	sim.enemy_power.connect(func(_e: SimEnemy, _p: StringName, _t: Array) -> void: casts[0] += 1)
	_tick(sim, 10.0)
	assert_eq(casts[0], 0)
	mender.health = mender.max_health * 0.5
	_tick(sim, 0.1)
	assert_eq(casts[0], 1, "it heals as soon as it is needed")


func test_a_splitter_turns_to_stone_when_struck() -> void:
	var sim := _sim([_group(&"splitter")])
	_spawn_all(sim)
	var splitter := sim.enemies[0]
	splitter.power_timer = 0.0
	sim._damage(splitter, 10.0, null)
	assert_true(splitter.is_hardened())
	assert_eq(splitter.speed(), 0.0, "stone stands still")
	var before := splitter.health
	sim._damage(splitter, 10.0, null)
	assert_almost_eq(before - splitter.health, 10.0 * (1.0 - splitter.data.power_amount), 0.01)
	_tick(sim, splitter.data.power_duration + 0.1)
	assert_false(splitter.is_hardened())
	sim._damage(splitter, 1.0, null)
	assert_false(splitter.is_hardened(), "not again until it is ready")


func test_a_warded_shield_blocks_one_hit_then_comes_back() -> void:
	var sim := _sim([_group(&"warded")])
	_spawn_all(sim)
	var warded := sim.enemies[0]
	assert_true(warded.shield_up, "it starts with its shield up")
	var source := _tower(sim, Vector2.ZERO, 30.0)
	var before := warded.health
	sim._hit(source, warded, 30.0)
	assert_eq(warded.health, before, "blocked")
	assert_false(warded.shield_up)
	sim._hit(source, warded, 30.0)
	assert_lt(warded.health, before, "the next one lands")
	_tick(sim, warded.data.power_interval + 0.1)
	assert_true(warded.shield_up, "the shield comes back")


func test_the_warden_breathes_fire_on_the_strongest_tower() -> void:
	var sim := _sim([_group(&"warden")])
	_spawn_all(sim)
	var warden := sim.enemies[0]
	var weak := _tower(sim, warden.position + Vector2(64, 0), 5.0)
	var strong := _tower(sim, warden.position + Vector2(0, 96), 50.0)
	var far := _tower(sim, warden.position + Vector2(2000, 0), 500.0)
	sim.towers.append_array([weak, strong, far])
	warden.power_timer = 0.0
	_tick(sim, 0.05)
	assert_gt(strong.silenced, 0.0, "the strongest tower in reach burns")
	assert_eq(weak.silenced, 0.0)
	assert_eq(far.silenced, 0.0, "out of reach")
