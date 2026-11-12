extends GutTest
## Enemy caves that break open every 4 or 5 waves: when they open, where (far from the city and from
## every other spawn, a short dig from a road), that nothing can be built on them, that enemies come
## out of them, and that a saved run keeps them.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _sim(map_id: StringName, seed := 0) -> RunSim:
	var config := RunConfig.from_registry(registry, map_id)
	config.cave_seed = seed
	return RunSim.new(config)


## Clears waves by hand (no enemies need to walk) until the run has `count` caves or the wave set ends.
func _clear_waves_until_caves(sim: RunSim, count: int) -> void:
	for i in 60:
		if sim.caves.size() >= count or sim.is_over():
			return
		sim.state = RunSim.State.WAVE
		sim._finish_wave()


func test_the_first_cave_comes_after_four_or_five_waves() -> void:
	for seed in range(1, 21):
		var sim := _sim(&"switchback", seed)
		assert_between(sim.next_cave_wave, 5, 6, "seed %d" % seed)
		var first := sim.next_cave_wave
		while sim.wave_number() < first - 1:
			sim.state = RunSim.State.WAVE
			sim._finish_wave()
		assert_eq(sim.caves.size(), 0, "no cave before its wave")
		sim.state = RunSim.State.WAVE
		sim._finish_wave()
		assert_eq(sim.caves.size(), 1, "the cave opens in the break before wave %d" % first)
		assert_eq(sim.caves[0].wave, first)
		assert_between(sim.next_cave_wave - first, Caves.EVERY_MIN, Caves.EVERY_MAX)


func test_caves_keep_away_from_the_city_and_every_spawn() -> void:
	var map_ids: Array[StringName] = [&"switchback", &"serpentine", &"c_ember_2", &"c_void_4", &"c_converge_3", &"thornwild"]
	for map_id in map_ids:
		for seed in [3, 77, 1234]:
			var sim := _sim(map_id, seed)
			var map := sim.config.map
			_clear_waves_until_caves(sim, Caves.MAX_CAVES)
			assert_gt(sim.caves.size(), 0, "%s seed %d opened a cave" % [map_id, seed])
			for cave in sim.caves:
				var at := map.cell_center(cave.cell)
				for lane in map.lane_count():
					var points := map.path_points(lane)
					assert_gte(at.distance_to(points[points.size() - 1]), Caves.BASE_DISTANCE * map.cell_size,
							"%s cave %s far from the city" % [map_id, cave.cell])
					assert_gte(at.distance_to(points[0]), Caves.SPAWN_DISTANCE * map.cell_size,
							"%s cave %s far from road start %d" % [map_id, cave.cell, lane])
				for other in sim.caves:
					if other != cave:
						assert_gte(at.distance_to(map.cell_center(other.cell)), Caves.SPAWN_DISTANCE * map.cell_size,
								"%s caves %s and %s apart" % [map_id, cave.cell, other.cell])
				assert_between(cave.dig.size(), Caves.DIG_MIN, Caves.DIG_MAX, "%s dig length" % map_id)
				for cell in cave.cells:
					assert_true(map.is_inside(cell))
					# Only the cave's own dig leaves the mound.
					assert_eq(sim.is_path(cell), cave.dig.has(cell), "%s mound %s off the road" % [map_id, cell])
					assert_null(sim.landmark_at(cell), "%s mound %s off the camps and city" % [map_id, cell])
				# The horde walks out of the mouth, along the dig and onto most of a road, to its end.
				var curve := sim.lane_curves[cave.lane]
				assert_almost_eq(curve.sample_baked(0.0), at, Vector2.ONE)
				var joined := sim.lane_curves[cave.joins_lane]
				var end := joined.sample_baked(sim.lane_lengths[cave.joins_lane])
				assert_almost_eq(curve.sample_baked(sim.lane_lengths[cave.lane]), end, Vector2(2, 2))
				assert_gte(sim.lane_lengths[cave.joins_lane] - cave.join_offset,
						sim.lane_lengths[cave.joins_lane] * Caves.ROAD_LEFT - 1.0)


func test_no_more_than_the_cap_and_none_in_an_assault() -> void:
	var sim := _sim(&"switchback", 9)
	sim.config.endless = true
	_clear_waves_until_caves(sim, 99)
	assert_lte(sim.caves.size(), Caves.MAX_CAVES)
	assert_eq(sim.next_cave_wave, 0, "no cave waits once the cap is reached")
	var assault := _sim(&"c_assault_1")
	if assault.is_assault():
		assert_false(assault.caves_come())
		assert_eq(assault.next_cave_wave, 0)


func test_nothing_can_be_built_on_a_cave_or_its_dig() -> void:
	var sim := _sim(&"switchback", 5)
	_clear_waves_until_caves(sim, 1)
	sim.gold = 99999
	sim.allocate_node(&"fire_entry")
	assert_eq(sim.placement_error(&"fire_brazier", sim.caves[0].cell), "An enemy cave yawns here")
	var cave := sim.caves[0]
	for cell in cave.cells:
		assert_false(sim.can_place(&"fire_brazier", cell), "mound %s" % cell)
		assert_eq(sim.cave_at(cell), cave)
	for cell in cave.dig:
		assert_true(sim.is_path(cell))
		assert_false(sim.can_place(&"fire_brazier", cell), "dig %s" % cell)


func test_the_dig_goes_around_towers() -> void:
	var sim := _sim(&"switchback", 11)
	sim.gold = 999999
	sim.allocate_node(&"fire_entry")
	# Build over a lot of the open ground first.
	var built: Dictionary[Vector2i, bool] = {}
	for x in range(0, sim.config.map.grid_size.x, 4):
		for y in range(0, sim.config.map.grid_size.y, 4):
			var cell := Vector2i(x, y)
			if sim.place_tower(&"fire_brazier", cell) != null:
				built[cell] = true
	_clear_waves_until_caves(sim, 2)
	assert_gt(sim.caves.size(), 0, "a cave still finds room")
	for cave in sim.caves:
		for cell in cave.dig:
			assert_false(built.has(cell), "dig %s goes around the towers" % cell)
		for cell in cave.cells:
			assert_false(built.has(cell), "mound %s is not on a tower" % cell)


func test_the_horde_comes_out_of_the_cave() -> void:
	var sim := _sim(&"switchback", 21)
	_clear_waves_until_caves(sim, 1)
	var cave := sim.caves[0]
	sim.start_next_wave()
	var from_cave := 0
	for i in 3000:
		sim.step(RunSim.STEP * 4.0)
		for enemy in sim.enemies:
			if enemy.lane == cave.lane:
				from_cave += 1
		if from_cave > 0 or sim.state != RunSim.State.WAVE:
			break
	assert_gt(from_cave, 0, "enemies walk out of the cave")


func test_the_same_seed_gives_the_same_caves_and_a_new_seed_moves_them() -> void:
	var a := _sim(&"c_ember_2", 42)
	var b := _sim(&"c_ember_2", 42)
	_clear_waves_until_caves(a, 2)
	_clear_waves_until_caves(b, 2)
	assert_eq(a.caves.size(), b.caves.size())
	for i in a.caves.size():
		assert_eq(a.caves[i].cell, b.caves[i].cell)
	var moved := false
	for seed in range(100, 110):
		var c := _sim(&"c_ember_2", seed)
		_clear_waves_until_caves(c, 1)
		moved = moved or c.caves[0].cell != a.caves[0].cell
	assert_true(moved, "other runs get caves elsewhere")


func test_a_saved_run_keeps_its_caves() -> void:
	var sim := _sim(&"switchback", 33)
	_clear_waves_until_caves(sim, 2)
	assert_eq(sim.caves.size(), 2)
	var data := RunSnapshot.capture(sim)
	var parsed: Dictionary = JSON.parse_string(JSON.stringify(data))
	var thawed := _sim(&"switchback", 999)
	assert_gte(RunSnapshot.restore(thawed, parsed), 0)
	assert_eq(thawed.caves.size(), 2)
	for i in 2:
		assert_eq(thawed.caves[i].cell, sim.caves[i].cell)
		assert_eq(thawed.caves[i].dig, sim.caves[i].dig)
		assert_eq(thawed.caves[i].lane, sim.caves[i].lane)
		assert_almost_eq(thawed.lane_lengths[thawed.caves[i].lane], sim.lane_lengths[sim.caves[i].lane], 0.5)
	assert_eq(thawed.next_cave_wave, sim.next_cave_wave)
	# The next cave opens in the same place in both.
	_clear_waves_until_caves(sim, 3)
	_clear_waves_until_caves(thawed, 3)
	if sim.caves.size() >= 3:
		assert_eq(thawed.caves[2].cell, sim.caves[2].cell)
