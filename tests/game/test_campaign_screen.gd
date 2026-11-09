extends GutTest
## The campaign map and a campaign stage's end screen. Progress is kept in memory.

const CAMPAIGN_SCENE := preload("res://scenes/campaign/campaign_map.tscn")
const GAME_SCENE := preload("res://scenes/game/game.tscn")


func _open_campaign(profile: PlayerProfile = null) -> CampaignScreen:
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
