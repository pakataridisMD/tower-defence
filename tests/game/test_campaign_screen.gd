extends GutTest
## The campaign map and a campaign stage's end screen. Progress is kept in memory.

const CAMPAIGN_SCENE := preload("res://scenes/campaign/campaign_map.tscn")
const GAME_SCENE := preload("res://scenes/game/game.tscn")


func _open_campaign(profile: PlayerProfile = null) -> CampaignScreen:
	CampaignScreen.intro_played = true
	Progress.use_memory_profile(profile)
	var screen := CAMPAIGN_SCENE.instantiate() as CampaignScreen
	add_child_autofree(screen)
	await wait_process_frames(2)
	return screen


func _begin_button(screen: Control) -> Button:
	for button: Button in screen.find_children("*", "Button", true, false):
		if button.text in ["Begin stage", "Play again", "Locked"]:
			return button
	return null


func test_a_new_player_starts_on_a_first_stage() -> void:
	var screen := await _open_campaign()
	assert_eq(Progress.meta.registry.campaign_of(screen.selected).stage_index(screen.selected), 0)
	assert_false(_begin_button(screen).disabled)


func test_every_stage_has_a_spot_and_can_be_picked() -> void:
	var screen := await _open_campaign()
	var spots: Array[Vector2] = []
	for stage_id: StringName in DataRegistry.stages:
		var at := screen.stage_position(stage_id)
		assert_ne(at, Vector2.ZERO, "%s is on the map" % stage_id)
		assert_eq(screen.stage_at(at), stage_id, "clicking %s picks it" % stage_id)
		assert_false(spots.has(at), "%s has its own spot" % stage_id)
		spots.append(at)


func test_every_stage_has_a_medallion_and_a_city_on_the_world_map() -> void:
	var screen := await _open_campaign()
	for stage_id: StringName in DataRegistry.stages:
		assert_true(screen._medals.has(stage_id), "%s has a medallion" % stage_id)
		assert_not_null(screen._medals.get(stage_id), "%s's medallion art loads" % stage_id)
		var spot: Dictionary = screen._spots.get(String(stage_id), {})
		assert_true(spot.has("medal") and spot.has("city_top"), "%s has a place on the map" % stage_id)
	assert_not_null(screen._map, "the painted map loads")
	assert_eq(screen._labels.size(), 8, "six lands, the Heartland and the citadel are named")


func test_zoom_stops_at_the_whole_world_and_the_closest_view() -> void:
	var screen := await _open_campaign()
	for i in 6:
		screen.zoom_step(-1)
		screen._process(1.0)
	assert_almost_eq(screen.zoom, screen._fit_zoom(), 0.001)
	var view := screen.view_rect()
	assert_true(view.has_point(screen.map_to_screen(Vector2(10, 10))), "the whole world fits in view")
	assert_true(view.has_point(screen.map_to_screen(screen._map_size - Vector2(10, 10))))
	for i in 6:
		screen.zoom_step(1)
		screen._process(1.0)
	assert_almost_eq(screen.zoom, CampaignScreen.ZOOMS[-1], 0.001)
	# However far the map is dragged, it still covers the view.
	screen.center = Vector2(-5000, 90000)
	screen._clamp_view()
	assert_true(screen.screen_to_map(view.position).x >= -0.01 and screen.screen_to_map(view.end).y <= screen._map_size.y + 0.01)


func test_picking_a_stage_brings_it_into_view() -> void:
	var screen := await _open_campaign()
	screen.show_whole_world()
	screen._process(1.0)
	screen.select(&"water_3")
	screen._process(1.0)
	assert_gte(screen.zoom, CampaignScreen.ZOOMS[1] - 0.001)
	assert_true(screen.view_rect().has_point(screen.stage_position(&"water_3")))
	screen.step_stage(1)
	assert_eq(screen.selected, &"water_4")
	screen.step_stage(-2)
	assert_eq(screen.selected, &"water_2")


func test_locked_stages_cannot_begin() -> void:
	var screen := await _open_campaign()
	screen.select(&"converge_3")
	assert_true(_begin_button(screen).disabled)
	screen.begin()
	assert_true(Progress.active_stage.is_empty() or Progress.active_stage != &"converge_3")


func test_a_won_stage_shows_its_stars_and_opens_the_next() -> void:
	Progress.use_memory_profile()
	assert_true(Progress.play_stage(&"ember_1"))
	var game := GAME_SCENE.instantiate() as Game
	add_child_autofree(game)
	await wait_process_frames(2)
	assert_eq(game.sim.config.stage.id, &"ember_1")
	assert_true(game.sim.tree.is_allocated(&"fire_entry"))
	game.sim.wave_index = game.sim.total_waves() - 1
	game.sim._end_run(true)
	await wait_process_frames(2)
	assert_eq(Progress.meta.stars(&"ember_1"), 3)
	assert_true(Progress.meta.is_stage_unlocked(&"ember_2"))
	var next: Button = null
	for button: Button in game.hud.find_children("*", "Button", true, false):
		if button.text == "Next stage":
			next = button
	assert_not_null(next)
	assert_true(next.visible)


func test_stages_with_a_boss_are_marked_for_the_red_glow() -> void:
	var screen := await _open_campaign()
	assert_true(screen.has_boss(&"ember_2"), "a Herald leads ember_2's last wave")
	assert_true(screen.has_boss(&"ember_4"), "the land's Warden")
	assert_true(screen.has_boss(&"assault_1"), "Vael-Orrun")
	assert_false(screen.has_boss(&"ember_1"), "no boss on the first stage")
