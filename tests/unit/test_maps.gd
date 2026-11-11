extends GutTest
## The maps are big, winding and have spawn holes (see tools/campaign/maps.py).

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
## The maps used to be 24 x 15 cells.
const OLD_AREA := 24 * 15

var registry: Node


func before_all() -> void:
	registry = DataRegistryScript.new()
	registry.reload()


func after_all() -> void:
	registry.free()


func test_every_map_is_about_three_times_the_old_size() -> void:
	for map: MapData in registry.maps.values():
		var area := map.grid_size.x * map.grid_size.y
		assert_true(area >= OLD_AREA * 3, "%s is %s cells" % [map.id, map.grid_size])


func test_every_road_curves_and_is_valid() -> void:
	for map: MapData in registry.maps.values():
		assert_eq(map.path_errors(), PackedStringArray(), "%s has valid roads" % map.id)
		for lane in map.lane_count():
			var line := map.lane_curve(lane)
			assert_gt(line.size(), 4, "%s lane %d has a curve" % [map.id, lane])
			var slanted := 0
			for i in range(1, line.size()):
				var step := line[i] - line[i - 1]
				if absf(step.x) > 0.05 and absf(step.y) > 0.05:
					slanted += 1
			assert_gt(slanted, 3, "%s lane %d bends" % [map.id, lane])


func test_spawn_holes_start_on_the_board_and_join_a_road() -> void:
	var with_holes := 0
	for map: MapData in registry.maps.values():
		if not map.hole_lanes.is_empty():
			with_holes += 1
		var exits := {}
		for lane in map.lane_count():
			if not map.is_spawn_hole(lane):
				var points := map.lane_waypoints(lane)
				exits[points[points.size() - 1]] = true
		for lane in map.hole_lanes:
			var points := map.lane_waypoints(lane)
			assert_true(map.is_inside(points[0]), "%s hole %d is on the board" % [map.id, lane])
			assert_true(exits.has(points[points.size() - 1]), "%s hole %d leads to an exit" % [map.id, lane])
	assert_gt(with_holes, registry.maps.size() / 2, "most maps have a spawn hole")


func test_the_road_leaves_room_to_build() -> void:
	for map: MapData in registry.maps.values():
		var road := map.path_cells()
		var free := 0
		for x in map.grid_size.x:
			for y in map.grid_size.y:
				if not road.has(Vector2i(x, y)):
					free += 1
		var share := float(free) / float(map.grid_size.x * map.grid_size.y)
		assert_true(share > 0.45 and share < 0.95, "%s: %d%% of the ground is free" % [map.id, roundi(share * 100.0)])


func test_enemies_walk_the_curve() -> void:
	var map: MapData = registry.maps[&"c_ember_1"]
	var points := map.path_points(0)
	assert_eq(points.size(), map.curve.size())
	assert_almost_eq(points[1], (map.curve[1] + Vector2(0.5, 0.5)) * map.cell_size, Vector2(0.01, 0.01))
	var sim := RunSim.new(RunConfig.from_registry(registry, &"switchback"))
	var waypoints := sim.config.map.lane_waypoints(0)
	assert_gt(sim.lane_lengths[0], sim.config.map.cell_center(waypoints[0]).distance_to(
		sim.config.map.cell_center(waypoints[waypoints.size() - 1])) * 1.5, "the road winds")
