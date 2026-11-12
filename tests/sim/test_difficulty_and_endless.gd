extends GutTest
## The difficulty ladder (each level doubles the one before in numbers and health) and the endless
## skirmish (the horde doubles every RunSim.ENDLESS_STEP waves).

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"switchback"

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _sim(difficulty: StringName = &"normal", endless := false) -> RunSim:
	var config := RunConfig.from_registry(registry, MAP)
	config.difficulty = registry.difficulties.get(difficulty)
	config.endless = endless
	return RunSim.new(config)


## Ends the wave being fought at once, as if every enemy had fallen.
func _clear_wave(sim: RunSim) -> void:
	sim.start_next_wave()
	sim._spawner.stop()
	sim.enemies.clear()
	sim.step(RunSim.STEP)


func _crowd(wave: WaveData) -> int:
	var total := 0
	for group in wave.groups:
		var data: EnemyData = registry.enemies.get(group.enemy)
		if data == null or not data.tags.has(&"boss"):
			total += group.count
	return total


func test_every_level_doubles_the_one_before() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var levels := meta.difficulties_in_order()
	assert_gte(levels.size(), 4, "Normal and at least three harder levels")
	assert_eq(levels[0].id, &"normal")
	assert_eq(levels[0].enemy_health_multiplier, 1.0)
	assert_eq(levels[0].enemy_count_multiplier, 1.0)
	for i in range(1, levels.size()):
		var before := levels[i - 1]
		var level := levels[i]
		assert_almost_eq(level.enemy_health_multiplier, before.enemy_health_multiplier * 2.0, 0.001, String(level.id))
		assert_almost_eq(level.enemy_count_multiplier, before.enemy_count_multiplier * 2.0, 0.001, String(level.id))
		assert_gt(level.meta_point_multiplier, before.meta_point_multiplier, "harder levels pay more")


func test_every_level_is_unlocked_by_a_talent_except_normal() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	for level in meta.difficulties_in_order():
		if level.id == &"normal":
			assert_true(meta.is_difficulty_unlocked(level.id))
		else:
			assert_false(meta.is_difficulty_unlocked(level.id), "%s starts locked" % level.id)
			assert_not_null(meta.unlocked_by(&"unlocks_difficulties", level.id), "%s has a talent" % level.id)


func test_a_scaled_group_has_more_enemies_in_the_same_time() -> void:
	var group := SpawnGroup.new()
	group.count = 12
	group.spawn_interval = 0.6
	for pattern in [SpawnGroup.Pattern.STREAM, SpawnGroup.Pattern.PACKS, SpawnGroup.Pattern.SURGE]:
		group.pattern = pattern
		group.pack_size = 4
		var doubled := group.scaled(2.0)
		assert_eq(doubled.count, 24)
		assert_almost_eq(doubled.duration(), group.duration(), group.duration() * 0.15, "pattern %d" % pattern)
		assert_eq(group.count, 12, "the original is left alone")
	group.pattern = SpawnGroup.Pattern.PACKS
	assert_eq(group.scaled(2.0).pack_size, 8, "packs grow instead of coming more often")


func test_grim_brings_twice_the_enemies_with_twice_the_health() -> void:
	var normal := _sim(&"normal")
	var grim := _sim(&"hard")
	var wave := grim.current_wave()
	assert_eq(grim.wave_as_it_comes().enemy_count(), wave.enemy_count() * 2)
	assert_almost_eq(grim.health_growth(), normal.health_growth() * 2.0, 0.001)
	grim.start_next_wave()
	var spawned := 0
	var elapsed := 0.0
	while not grim._spawner.is_finished() and elapsed < 300.0:
		grim._spawner.advance(0.5)
		elapsed += 0.5
	# The wave lasts about as long as on Normal: its enemies come closer together.
	assert_almost_eq(grim._spawner.spawn_window(), wave.spawn_window(), wave.spawn_window() * 0.2)
	assert_eq(grim._spawner.remaining(), 0)


func test_bosses_are_not_doubled() -> void:
	var sim := _sim(&"merciless")
	sim.wave_index = sim.total_waves() - 1
	var wave := sim.current_wave()
	assert_true(wave.is_boss)
	var bosses := func(w: WaveData) -> int:
		var count := 0
		for group in w.groups:
			var data: EnemyData = registry.enemies.get(group.enemy)
			if data != null and data.tags.has(&"boss"):
				count += group.count
		return count
	assert_gt(bosses.call(wave), 0)
	assert_eq(bosses.call(sim.wave_as_it_comes()), bosses.call(wave))


func test_a_huge_horde_comes_as_fewer_stronger_enemies() -> void:
	var sim := _sim(&"oblivion")
	sim.wave_index = sim.total_waves() - 2
	var wave := sim.current_wave()
	var wanted := _crowd(wave) * 16
	assert_gt(wanted, RunSim.MAX_WAVE_ENEMIES, "this wave is big enough to hit the cap")
	sim.start_next_wave()
	var came := _crowd(sim.wave_as_it_comes())
	assert_lte(came, RunSim.MAX_WAVE_ENEMIES + wave.groups.size())
	# The same total health: fewer enemies, each that much stronger.
	assert_almost_eq(came * sim._crowd_health, float(wanted), wanted * 0.05)


func test_a_normal_skirmish_ends_after_its_last_wave() -> void:
	var sim := _sim()
	sim.wave_index = sim.total_waves() - 1
	_clear_wave(sim)
	assert_eq(sim.state, RunSim.State.WON)


func test_an_endless_skirmish_goes_on_past_the_last_wave() -> void:
	var sim := _sim(&"normal", true)
	assert_true(sim.is_endless())
	var count := sim.total_waves()
	sim.wave_index = count - 1
	_clear_wave(sim)
	assert_eq(sim.state, RunSim.State.BUILDING)
	assert_eq(sim.wave_number(), count + 1)
	# Past the set, its last ENDLESS_LOOP waves come round again: the Warden ends every loop.
	for i in RunSim.ENDLESS_LOOP:
		assert_eq(sim.current_wave(), sim.config.wave_set.waves[count - RunSim.ENDLESS_LOOP + i])
		_clear_wave(sim)
	assert_eq(sim.state, RunSim.State.BUILDING)
	assert_true(sim.config.wave_set.waves[count - 1].is_boss)


func test_the_endless_horde_doubles_every_five_waves() -> void:
	var sim := _sim(&"normal", true)
	assert_eq(RunSim.ENDLESS_STEP, 5)
	assert_eq(sim.endless_multiplier(1), 1.0)
	assert_eq(sim.endless_multiplier(5), 1.0)
	assert_eq(sim.endless_multiplier(6), 2.0)
	assert_eq(sim.endless_multiplier(11), 4.0)
	assert_eq(sim.endless_multiplier(21), 16.0)
	var plain := _sim()
	sim.wave_index = 5
	plain.wave_index = 5
	assert_almost_eq(sim.health_growth(), plain.health_growth() * 2.0, 0.001, "wave 6: twice the health")
	assert_eq(sim.wave_as_it_comes().enemy_count(), plain.current_wave().enemy_count() * 2, "and twice the enemies")


func test_endless_stacks_with_the_difficulty() -> void:
	var sim := _sim(&"hard", true)
	sim.wave_index = 5
	assert_almost_eq(sim.enemy_count_multiplier(), 4.0, 0.001)


func test_campaign_stages_are_never_endless() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	meta.set_endless(true)
	var config := meta.stage_config(&"ember_1")
	assert_false(RunSim.new(config).is_endless())
	assert_true(RunSim.new(meta.run_config()).is_endless())


func test_endless_keeps_its_own_record_and_best_wave() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	meta.set_endless(true)
	var sim := RunSim.new(meta.run_config())
	sim.wave_index = 17
	sim.state = RunSim.State.LOST
	assert_eq(MetaProgress.record_key(sim), StringName("endless:%s" % sim.config.map.id))
	assert_gt(meta.record_run(sim), 0)
	assert_eq(meta.endless_best(sim.config.map.id), 17)
	var saved := PlayerProfile.from_dict(meta.profile.to_dict())
	assert_true(saved.last_endless)
	assert_eq(saved.endless_best.get(sim.config.map.id, 0), 17)


func test_a_saved_endless_run_stays_endless() -> void:
	var sim := _sim(&"hard", true)
	sim.wave_index = 7
	var run := RunSnapshot.capture(sim)
	assert_true(run.get("endless", false))
	assert_eq(run.get("difficulty"), "hard")
	var info := Progress.slot_info(run)
	assert_eq(info.get("where"), "Endless skirmish")
	assert_string_contains(SavesPage.SlotRow.details(info), "Wave 8")
	assert_false(SavesPage.SlotRow.details(info).contains("Wave 8 of"), "an endless run has no last wave")
	assert_false(RunSnapshot.capture(_sim(&"hard")).get("endless", true))


func test_the_hardest_levels_start_with_more_gold() -> void:
	var normal := _sim(&"normal")
	assert_eq(_sim(&"merciless").gold, normal.gold)
	assert_eq(_sim(&"nightmare").gold, normal.gold * 4)
	assert_eq(_sim(&"oblivion").gold, normal.gold * 8)
