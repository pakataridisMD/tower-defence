extends GutTest
## The weather over the maps: every map has wind, each run rolls one or two short spells of rain, storm,
## snow, ash or dust that fit the land, and the board draws it (falling weather, snow settling,
## lightning, the trees bowing) with a screen-wide layer, a badge and a banner so it is plain to see.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const GAME_SCENE := preload("res://scenes/game/game.tscn")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func test_each_map_keeps_its_wind_but_rolls_new_weather() -> void:
	for map_id: StringName in registry.maps:
		var map: MapData = registry.maps[map_id]
		var first := Weather.for_map(map, 20)
		var again := Weather.for_map(map, 20)
		assert_eq(first.wind_dir, again.wind_dir, "%s wind" % map_id)
		assert_eq(first.wind, again.wind, "%s wind strength" % map_id)
	# The same dice give the same weather; different runs roll different weather.
	var a := Weather.make(&"c_nature_2", &"nature", 20, 7)
	var b := Weather.make(&"c_nature_2", &"nature", 20, 7)
	assert_eq(a.plan, b.plan, "a fixed seed gives the same weather")
	var plans := {}
	for i in 30:
		plans[str(Weather.make(&"c_nature_2", &"nature", 20).plan)] = true
	assert_gt(plans.size(), 5, "each run rolls its own weather")


func test_at_most_two_spells_of_one_or_two_waves() -> void:
	for land: StringName in Weather.SPELLS:
		for waves in [6, 8, 10, 12, 14, 20, 40]:
			for roll in 40:
				var weather := Weather.make(&"rolled", land, waves, roll * 31 + waves)
				var spells := weather.plan
				var where := "%s, %d waves, roll %d" % [land, waves, roll]
				assert_between(spells.size(), 1, Weather.MAX_SPELLS, "%s: one or two spells" % where)
				var last_end := 0
				for spell: Array in spells:
					var length: int = int(spell[2]) - int(spell[1]) + 1
					assert_between(length, 1, 2, "%s: a spell lasts one or two waves" % where)
					assert_gte(int(spell[1]), Weather.FIRST_WAVE, "%s: wave 1 is clear" % where)
					assert_lte(int(spell[2]), waves, "%s: inside the level" % where)
					if last_end > 0:
						assert_gt(int(spell[1]), last_end + Weather.GAP, "%s: clear waves between spells" % where)
					last_end = int(spell[2])
				assert_eq(weather.kind_at(1), Weather.Kind.CLEAR, "%s opens clear" % where)
				# Count the waves with weather straight from kind_at too.
				var stormy := 0
				for n in range(1, waves + 30):
					if weather.kind_at(n) != Weather.Kind.CLEAR:
						stormy += 1
				assert_lte(stormy, Weather.MAX_SPELLS * Weather.MAX_WAVES, "%s: no more than four waves of weather" % where)
	# Both one and two spells come up.
	var counts := {}
	for roll in 60:
		counts[Weather.make(&"rolled", &"nature", 14, roll).plan.size()] = true
	assert_true(counts.has(1) and counts.has(2), "some levels get one spell, some two")


func test_only_weather_that_fits_the_land() -> void:
	var never := {
		&"fire": [Weather.Kind.SNOW, Weather.Kind.BLIZZARD, Weather.Kind.RAIN, Weather.Kind.STORM],
		&"water": [Weather.Kind.ASH, Weather.Kind.DUST, Weather.Kind.RAIN, Weather.Kind.STORM],
		&"earth": [Weather.Kind.SNOW, Weather.Kind.BLIZZARD, Weather.Kind.ASH],
		&"nature": [Weather.Kind.ASH, Weather.Kind.DUST, Weather.Kind.SNOW, Weather.Kind.BLIZZARD],
		&"storm": [Weather.Kind.ASH, Weather.Kind.DUST],
		&"void": [Weather.Kind.SNOW, Weather.Kind.BLIZZARD, Weather.Kind.RAIN, Weather.Kind.DUST],
	}
	for land: StringName in never:
		var allowed := Weather.allowed(land)
		for kind: Weather.Kind in never[land]:
			assert_false(kind in allowed, "no %s in the %s lands" % [Weather.describe(kind), land])
	for map_id: StringName in registry.maps:
		var map: MapData = registry.maps[map_id]
		for roll in 20:
			var weather := Weather.make(map.id, map.biome, 14, roll)
			for spell: Array in weather.plan:
				assert_true(spell[0] in Weather.allowed(weather.biome),
						"%s: %s fits its land" % [map_id, Weather.describe(spell[0])])
	assert_gt(Weather.make(&"any_storm_map", &"storm").wind, Weather.make(&"any_storm_map", &"void").wind,
			"the storm land is windier")


func test_no_weather_past_the_level_in_endless_runs() -> void:
	var weather := Weather.make(&"endless_test", &"nature", 20, 3)
	for n in range(21, 400):
		assert_eq(weather.kind_at(n), Weather.Kind.CLEAR, "wave %d is clear" % n)
		if weather.kind_at(n) != Weather.Kind.CLEAR:
			break


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

	# It is plain to see: the screen-wide layer shows the storm, the corner badge names it and a banner
	# announced it as it broke.
	await wait_process_frames(2)
	var overlay := game.weather_overlay
	assert_not_null(overlay, "the battle view has a weather layer")
	assert_true(overlay.visible, "the weather layer shows")
	assert_eq(int(overlay.param(&"kind")), int(Weather.Kind.STORM))
	assert_gt(float(overlay.param(&"intensity")), 0.9, "at full strength")
	var badge := game.hud.weather_badge
	assert_not_null(badge, "the HUD has a weather badge")
	assert_true(badge.badge_visible(), "the badge shows while it rains")
	assert_eq(badge._title.text, "Thunderstorm")
	assert_string_contains(badge.banner_text(), "THUNDERSTORM", "the banner announces it")

	# Letting the waves decide again, the weather fades back out to the mission's own.
	sky.force(-1)
	sky.intensity = 0.05
	sky.update(1.0)
	assert_eq(sky.kind, sky.weather.kind_at(game.sim.wave_number()), "back to the mission's weather")
	await wait_process_frames(2)
	if sky.kind == Weather.Kind.CLEAR:
		assert_false(badge.badge_visible(), "the badge hides when the sky clears")
		assert_false(overlay.visible, "and so does the weather layer")

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
