extends GutTest
## The weather over the maps: every map has wind, some missions get a few waves of rain, storm, snow,
## ash or dust, and the board draws it (falling weather, snow settling, lightning, the trees bowing).

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const GAME_SCENE := preload("res://scenes/game/game.tscn")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func test_each_map_always_gets_the_same_weather() -> void:
	for map_id: StringName in registry.maps:
		var map: MapData = registry.maps[map_id]
		var first := Weather.for_map(map)
		var again := Weather.for_map(map)
		assert_eq(first.has_spells, again.has_spells, "%s spells" % map_id)
		assert_eq(first.wind_dir, again.wind_dir, "%s wind" % map_id)
		for n in range(1, 41):
			assert_eq(first.kind_at(n), again.kind_at(n), "%s wave %d" % [map_id, n])


func test_spells_last_a_few_waves_and_fit_the_land() -> void:
	var with_spells := 0
	for map_id: StringName in registry.maps:
		var map: MapData = registry.maps[map_id]
		var weather := Weather.for_map(map)
		assert_gt(weather.wind, 0.0, "%s has wind" % map_id)
		assert_gt(absf(weather.wind_dir.x), 0.9, "%s: the wind blows across the map" % map_id)
		var spells := weather.spells(40)
		if not weather.has_spells:
			assert_eq(spells.size(), 0, "%s stays clear" % map_id)
			continue
		with_spells += 1
		assert_gt(spells.size(), 0, "%s has weather" % map_id)
		var allowed: Array = Weather.SPELLS[weather.biome]
		for spell: Array in spells:
			assert_true(spell[0] in allowed, "%s: %s fits its land" % [map_id, Weather.describe(spell[0])])
			var length: int = spell[2] - spell[1] + 1
			assert_between(length, 2, 3, "%s: a spell lasts two or three waves" % map_id)
		# The first spell comes early, so the player sees it in the first few waves.
		assert_between(int(spells[0][1]), 3, 5, "%s first spell" % map_id)
		assert_eq(weather.kind_at(1), Weather.Kind.CLEAR, "%s opens clear" % map_id)
	assert_gt(with_spells, registry.maps.size() / 2, "most missions get some weather")


func test_storm_and_frozen_lands_always_get_their_weather() -> void:
	var storm := Weather.make(&"any_storm_map", &"storm")
	var water := Weather.make(&"any_water_map", &"water")
	assert_true(storm.has_spells)
	assert_true(water.has_spells)
	for spell: Array in water.spells(40):
		assert_true(Weather.is_snow(spell[0]), "the frozen shore gets snow")
	assert_gt(storm.wind, Weather.make(&"any_storm_map", &"void").wind, "the storm land is windier")


func test_weather_keeps_coming_in_endless_runs() -> void:
	var weather := Weather.make(&"endless_test", &"nature")
	var spells := weather.spells(400)
	assert_gt(spells.size(), 10, "spells keep rolling in long after wave 40")
	assert_gt(int(spells[-1][1]), 300)


func test_the_board_draws_wind_and_weather() -> void:
	Progress.use_memory_profile()
	var game: Game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	var art: BoardArt = game.board.art
	var sky := art.weather
	assert_not_null(sky, "the board has weather")

	# Snow: the flakes fall, the light turns cold and the snow settles on the ground.
	sky.force(Weather.Kind.SNOW)
	await wait_process_frames(3)
	assert_eq(sky.kind, Weather.Kind.SNOW)
	assert_gt(sky.snow_cover, 0.3, "snow lies on the ground")
	assert_true(sky._cover.visible)
	assert_gt(sky.wind_now, sky.weather.wind, "the wind rises with the weather")

	# A thunderstorm: dark light, a wet ground and lightning.
	sky.force(Weather.Kind.STORM)
	await wait_process_frames(2)
	var tint := sky.ambient_tint()
	assert_lt(tint.v, 0.8, "storm light is dark")
	assert_lt(sky.sun_scale(), 0.5, "clouds hide the sun")
	assert_lt(art._ground.modulate.v, 0.95, "the ground is wet")
	var lines_before := _count_lines(sky)
	sky.strike(game.sim.config.map.size_in_pixels() / BoardArt.SCALE / 2.0)
	assert_gt(_count_lines(sky), lines_before, "the bolt is drawn")
	assert_gt(sky.ambient_tint().v, tint.v, "the sky flashes")

	# Letting the waves decide again, the weather fades back out to the mission's own.
	sky.force(-1)
	sky.intensity = 0.05
	sky.update(1.0)
	assert_eq(sky.kind, sky.weather.kind_at(game.sim.wave_number()), "back to the mission's weather")

	# A gust front sweeps downwind across the map.
	sky._gust_wait = 0.0
	sky.update(0.016)
	var start := sky.gust().x
	sky.update(0.5)
	assert_gt(sky.gust().x, start, "the gust moves downwind")
	assert_gt(sky.gust().y, 0.0, "the gust pushes")


func _count_lines(node: Node) -> int:
	var count := 1 if node is Line2D else 0
	for child in node.get_children():
		count += _count_lines(child)
	return count
