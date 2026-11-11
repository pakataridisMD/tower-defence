extends GutTest
## Spawn patterns (streams, packs, surges, scatter), how a wave shares its packs out over the roads,
## and the shape of the generated waves: long, in several beats, and growing through a stage.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")


func _group(pattern: SpawnGroup.Pattern, count: int, interval: float) -> SpawnGroup:
	var group := SpawnGroup.new()
	group.enemy = &"grunt"
	group.pattern = pattern
	group.count = count
	group.spawn_interval = interval
	return group


func _wave(groups: Array[SpawnGroup]) -> WaveData:
	var wave := WaveData.new()
	wave.groups = groups
	return wave


## Runs the spawner to the end and returns every spawn in order.
func _drain(spawner: WaveSpawner) -> Array[WaveSpawner.Spawn]:
	var all: Array[WaveSpawner.Spawn] = []
	for i in 100000:
		if spawner.is_finished():
			break
		all.append_array(spawner.advance(0.05))
	return all


func test_a_stream_is_evenly_spaced() -> void:
	var times := _group(SpawnGroup.Pattern.STREAM, 4, 0.8).spawn_times()
	assert_eq(times.size(), 4)
	for i in 4:
		assert_almost_eq(times[i], i * 0.8, 0.001)


func test_packs_come_close_together_with_a_pause_between() -> void:
	var group := _group(SpawnGroup.Pattern.PACKS, 9, 0.3)
	group.pack_size = 3
	group.pack_gap = 4.0
	var times := group.spawn_times()
	assert_eq(times.size(), 9)
	assert_almost_eq(times[1] - times[0], 0.3, 0.001, "inside a pack")
	assert_almost_eq(times[3] - times[2], 4.3, 0.001, "between packs")
	assert_almost_eq(times[6] - times[5], 4.3, 0.001)
	assert_eq(group.pack_of(2), 0)
	assert_eq(group.pack_of(3), 1)
	assert_almost_eq(group.duration(), 6 * 0.3 + 2 * 4.3, 0.001)


func test_a_surge_gets_faster_and_faster() -> void:
	var times := _group(SpawnGroup.Pattern.SURGE, 10, 1.0).spawn_times()
	var first := times[1] - times[0]
	var last := times[9] - times[8]
	assert_gt(first, 1.5, "starts slow")
	assert_lt(last, 0.5, "ends fast")
	for i in range(2, 10):
		assert_true(times[i] - times[i - 1] < times[i - 1] - times[i - 2] + 0.0001, "never slows down")


func test_scatter_is_uneven_but_always_the_same() -> void:
	var group := _group(SpawnGroup.Pattern.SCATTER, 30, 1.0)
	var times := group.spawn_times(7)
	assert_eq(times, group.spawn_times(7), "the same wave scatters the same way every time")
	var gaps: Array[float] = []
	for i in range(1, times.size()):
		var gap := times[i] - times[i - 1]
		assert_between(gap, 0.25 - 0.001, 1.75 + 0.001)
		gaps.append(gap)
	assert_gt(gaps.max() - gaps.min(), 0.5, "the gaps differ")


func test_packs_share_out_over_the_roads_one_pack_at_a_time() -> void:
	var group := _group(SpawnGroup.Pattern.PACKS, 12, 0.2)
	group.pack_size = 4
	var spawner := WaveSpawner.new()
	spawner.start(_wave([group]), 3)
	var spawns := _drain(spawner)
	assert_eq(spawns.size(), 12)
	for pack in 3:
		var lane := spawns[pack * 4].lane
		for i in 4:
			assert_eq(spawns[pack * 4 + i].lane, lane, "a pack keeps to one road")
	assert_ne(spawns[0].lane, spawns[4].lane, "the next pack takes another road")
	assert_ne(spawns[4].lane, spawns[8].lane)


func test_a_stream_shares_out_one_enemy_at_a_time_and_a_set_lane_holds() -> void:
	var shared := _group(SpawnGroup.Pattern.STREAM, 4, 0.5)
	var flank := _group(SpawnGroup.Pattern.STREAM, 3, 0.5)
	flank.lane = 1
	flank.start_delay = 10.0
	var far := _group(SpawnGroup.Pattern.STREAM, 1, 0.5)
	far.lane = 5
	far.start_delay = 20.0
	var spawner := WaveSpawner.new()
	spawner.start(_wave([shared, flank, far]), 2)
	var spawns := _drain(spawner)
	assert_eq(spawns.size(), 8)
	assert_ne(spawns[0].lane, spawns[1].lane)
	for i in range(4, 7):
		assert_eq(spawns[i].lane, 1)
	assert_eq(spawns[7].lane, 1, "a lane the map does not have falls back to its last one")
	assert_almost_eq(spawner.spawn_window(), 20.0, 0.001)


func test_spawns_come_out_in_time_order_across_groups() -> void:
	var a := _group(SpawnGroup.Pattern.STREAM, 5, 1.0)
	var b := _group(SpawnGroup.Pattern.PACKS, 6, 0.2)
	b.pack_size = 3
	b.start_delay = 0.5
	var wave := _wave([a, b])
	var spawner := WaveSpawner.new()
	spawner.start(wave)
	assert_eq(spawner.remaining(), 11)
	assert_eq(_drain(spawner).size(), 11)
	assert_almost_eq(wave.spawn_window(), maxf(4.0, 0.5 + b.duration()), 0.001)


# --- The generated waves -------------------------------------------------------------

func test_campaign_waves_are_long_and_come_in_several_beats() -> void:
	var registry: Node = autofree(DataRegistryScript.new())
	registry.reload()
	for stage: StageData in registry.stages.values():
		var waves: WaveSet = registry.wave_sets[registry.maps[stage.map].wave_set]
		var first := waves.waves[0]
		var late := waves.waves[waves.waves.size() - 2]
		# The first wave is a short warm-up; the late ones take a good while (they used to be over in
		# ten or fifteen seconds).
		assert_gt(first.spawn_window(), 8.0, "%s: even the first wave takes a while" % stage.id)
		assert_gt(late.spawn_window(), 30.0, "%s: late waves are long" % stage.id)
		assert_gt(late.spawn_window(), first.spawn_window() * 1.5, "%s: waves grow longer" % stage.id)
		for wave in waves.waves:
			var patterns := {}
			for group in wave.groups:
				patterns[group.pattern] = true
			assert_gt(wave.groups.size(), 3, "%s: a wave has several beats" % stage.id)
			assert_gt(patterns.size(), 1, "%s: a wave mixes rhythms" % stage.id)
			assert_false(wave.description.is_empty(), "%s: the HUD can say how the wave comes" % stage.id)


func test_waves_on_maps_with_several_roads_attack_down_set_lanes() -> void:
	var registry: Node = autofree(DataRegistryScript.new())
	registry.reload()
	for stage: StageData in registry.stages.values():
		var map: MapData = registry.maps[stage.map]
		if map.lane_count() < 2:
			continue
		var flanks := 0
		for wave in (registry.wave_sets[map.wave_set] as WaveSet).waves:
			for group in wave.groups:
				if group.lane > 0:
					flanks += 1
		assert_gt(flanks, 0, "%s: some groups come down a side road" % stage.id)
