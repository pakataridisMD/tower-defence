extends GutTest
## The enemy war camps where the roads start and the defended city where they end: where they stand,
## that nothing can be built on them, and that the board draws them as living places.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const GAME_SCENE := preload("res://scenes/game/game.tscn")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _sim(map_id: StringName) -> RunSim:
	return RunSim.new(RunConfig.from_registry(registry, map_id))


func _edge_end(map: MapData, lane: int, first: bool) -> bool:
	var points := map.path_points(lane)
	var end := points[0] if first else points[points.size() - 1]
	return not Rect2(Vector2.ZERO, map.size_in_pixels()).has_point(end)


func test_every_road_from_the_edge_starts_in_a_camp_and_ends_in_the_city() -> void:
	for map_id: StringName in registry.maps:
		var sim := _sim(map_id)
		var map := sim.config.map
		for lane in map.lane_count():
			var camp := false
			var city := false
			for site in sim.landmarks:
				if site.lanes.has(lane):
					camp = camp or site.kind == &"camp"
					city = city or site.kind == &"city"
			assert_eq(camp, _edge_end(map, lane, true), "%s lane %d camp" % [map_id, lane])
			assert_eq(city, _edge_end(map, lane, false), "%s lane %d city" % [map_id, lane])


func test_sites_stand_on_free_ground_inside_the_map() -> void:
	for map_id: StringName in registry.maps:
		var sim := _sim(map_id)
		var seen: Dictionary[Vector2i, bool] = {}
		for site in sim.landmarks:
			assert_gt(site.cells.size(), 2, "%s %s at %s has room" % [map_id, site.kind, site.anchor])
			for cell in site.cells:
				assert_true(sim.config.map.is_inside(cell), "%s %s inside the map" % [map_id, cell])
				assert_false(sim.is_path(cell), "%s %s off the road" % [map_id, cell])
				assert_false(seen.has(cell), "%s %s belongs to one site" % [map_id, cell])
				seen[cell] = true
				assert_between(site.depth_of(cell), 0, Landmarks.DEPTH - 1)
				assert_between(absi(site.side_of(cell)), 1, Landmarks.HALF_WIDTH)
		for structure in sim.structures:
			assert_null(sim.landmark_at(sim.config.map.cell_at(structure.position)), "%s structure cell is free" % map_id)


func test_nothing_can_be_built_on_a_camp_or_the_city() -> void:
	var sim := _sim(&"switchback")
	sim.gold = 9999
	sim.allocate_node(&"fire_entry")
	assert_eq(sim.landmarks.size(), 2, "one camp and one city")
	for site in sim.landmarks:
		var cell := site.cells[0]
		var expected := "The enemy's war camp stands here" if site.kind == &"camp" else "The city stands here"
		assert_eq(sim.placement_error(&"fire_brazier", cell), expected)
		assert_null(sim.place_tower(&"fire_brazier", cell))
		assert_eq(sim.landmark_at(cell), site)


func test_city_names_come_from_the_story() -> void:
	assert_eq(LandmarkArt.city_name_for(registry.maps[&"c_ember_1"]), "Kethra")
	assert_eq(LandmarkArt.city_name_for(registry.maps[&"c_converge_3"]), "Solenne")
	assert_eq(LandmarkArt.city_name_for(registry.maps[&"switchback"]), "Haven", "skirmish maps defend a plain town")


func test_every_land_has_city_art() -> void:
	assert_true(LandmarkArt.has_art(), "landmarks.json exists (run tools/art/landmarks/gen_landmarks.py)")
	var biomes: Array = LandmarkArt.info().get("biomes", [])
	for map_id: StringName in registry.maps:
		assert_true(biomes.has(String(registry.maps[map_id].biome)), "city art for biome %s" % registry.maps[map_id].biome)
	for biome: String in biomes:
		for name in ["house_%s_0" % biome, "house_%s_1" % biome, "house_%s_2" % biome, "gatetower_" + biome, "wall_" + biome, "well_" + biome]:
			assert_false(LandmarkArt.piece(name).is_empty(), "piece " + name)
			assert_true(ResourceLoader.exists(LandmarkArt.ART + name + ".png"), name + ".png")
			assert_true(ResourceLoader.exists(LandmarkArt.ART + name + "_n.png"), name + "_n.png")


func test_board_brings_the_camp_and_city_to_life() -> void:
	Progress.use_memory_profile()
	var game: Game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	var landmarks: LandmarkArt = game.board.art.landmarks
	assert_not_null(landmarks, "the board draws the camps and the city")
	assert_gt(landmarks.house_count(), 2, "the city has houses")
	assert_gt(landmarks.walker_count(), 6, "people walk about the camp and the city")
	assert_eq(landmarks.burning_count(), 0, "no house burns while every life is left")
	game.sim.lives = game.sim.starting_lives / 2
	await wait_process_frames(2)
	assert_gt(landmarks.burning_count(), 0, "houses burn as lives are lost")
	assert_lt(landmarks.burning_count(), landmarks.house_count(), "but not all of them at half lives")
