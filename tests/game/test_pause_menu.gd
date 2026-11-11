extends GutTest
## The Esc menu during a run: it pauses the run, resumes it, opens the audio settings and asks
## once before leaving a run that is still going.

const GAME_SCENE := preload("res://scenes/game/game.tscn")

var game: Game
var left_for: Array[StringName] = []


func before_each() -> void:
	Progress.use_memory_profile()
	left_for.clear()


func _start(party: Array[StringName] = []) -> void:
	for stage_id: StringName in [&"ember_2", &"ember_4", &"converge_3"]:
		if not party.is_empty():
			Progress.meta.profile.stage_stars[stage_id] = 1
	if not party.is_empty():
		Progress.meta.profile.hero_party = party
	game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	# Never change scene or quit inside the test run: note where the menu would have gone instead.
	for connection in game.pause_menu.leave_requested.get_connections():
		game.pause_menu.leave_requested.disconnect(connection["callable"])
	game.pause_menu.leave_requested.connect(func(scene: StringName) -> void: left_for.append(scene))


func _key(keycode: Key) -> void:
	var press := InputEventKey.new()
	press.keycode = keycode
	press.pressed = true
	get_tree().root.push_input(press, true)
	var release := press.duplicate() as InputEventKey
	release.pressed = false
	get_tree().root.push_input(release, true)


func _press(button: Button) -> void:
	assert_true(button.is_visible_in_tree() and not button.disabled, "'%s' should be pressable" % button.text)
	button.pressed.emit()


func test_escape_opens_the_menu_and_pauses_the_run() -> void:
	await _start()
	_key(KEY_SPACE)
	_key(KEY_ESCAPE)
	assert_true(game.pause_menu.visible)
	assert_true(game.paused)
	await wait_seconds(0.2)
	assert_eq(game.sim.time_in_wave, 0.0, "no time passes while the menu is open")
	_key(KEY_ESCAPE)
	assert_false(game.pause_menu.visible, "Esc again resumes")
	assert_false(game.paused)
	await wait_seconds(0.2)
	assert_gt(game.sim.time_in_wave, 0.0)


func test_escape_backs_out_of_placing_before_opening_the_menu() -> void:
	await _start()
	game.sim.allocate_node(&"fire_entry")
	game.board.begin_placing(&"fire_brazier")
	_key(KEY_ESCAPE)
	assert_true(game.board.placing.is_empty())
	assert_false(game.pause_menu.visible, "the first Esc only stops placing")
	_key(KEY_ESCAPE)
	assert_true(game.pause_menu.visible)


func test_resume_goes_on_even_after_p() -> void:
	await _start()
	_key(KEY_SPACE)
	_key(KEY_P)
	_key(KEY_ESCAPE)
	_press(game.pause_menu.resume_button)
	assert_false(game.pause_menu.visible)
	assert_false(game.paused)


func test_the_hud_menu_button_opens_it() -> void:
	await _start()
	_press(game.hud._menu_button)
	assert_true(game.pause_menu.visible)


func test_other_keys_wait_while_the_menu_is_open() -> void:
	await _start()
	_key(KEY_ESCAPE)
	_key(KEY_SPACE)
	_key(KEY_T)
	assert_eq(game.sim.state, RunSim.State.BUILDING, "Space does not start a wave behind the menu")
	assert_false(game.web.visible)


func test_audio_settings_open_over_the_menu_and_close_back_to_it() -> void:
	await _start()
	_key(KEY_SPACE)
	_key(KEY_ESCAPE)
	_key(KEY_O)
	assert_true(game.audio_panel.visible)
	_key(KEY_ESCAPE)
	assert_false(game.audio_panel.visible, "Esc closes the audio settings first")
	assert_true(game.pause_menu.visible, "and the menu is still there")
	assert_true(game.paused, "so the run still waits")
	_press(game.pause_menu.audio_button)
	assert_true(game.audio_panel.visible)
	game.audio_panel.close_panel()
	assert_true(game.pause_menu.visible)
	assert_true(game.paused)


func test_main_menu_asks_once_before_leaving_a_run() -> void:
	await _start()
	_key(KEY_ESCAPE)
	_press(game.pause_menu.menu_button)
	assert_true(game.pause_menu.is_confirming())
	assert_eq(left_for, [] as Array[StringName], "nothing happens until Leave is pressed")
	assert_true(game.pause_menu.leave_button.is_visible_in_tree())
	assert_false(game.pause_menu.menu_button.is_visible_in_tree())
	_key(KEY_ESCAPE)
	assert_false(game.pause_menu.is_confirming(), "Esc steps back from the question")
	assert_true(game.pause_menu.visible, "without closing the menu")
	_press(game.pause_menu.menu_button)
	_press(game.pause_menu.leave_button)
	assert_eq(left_for, [&"menu"] as Array[StringName])


func test_quit_asks_and_then_quits() -> void:
	await _start()
	_key(KEY_ESCAPE)
	_press(game.pause_menu.quit_button)
	_press(game.pause_menu.stay_button)
	assert_false(game.pause_menu.is_confirming())
	assert_eq(left_for, [] as Array[StringName])
	_press(game.pause_menu.quit_button)
	_press(game.pause_menu.leave_button)
	assert_eq(left_for, [&"quit"] as Array[StringName])


func test_leaving_a_finished_run_needs_no_question() -> void:
	await _start()
	game.sim._end_run(false)
	await wait_process_frames(1)
	assert_true(game.sim.is_over())
	game.open_pause_menu()
	_press(game.pause_menu.menu_button)
	assert_eq(left_for, [&"menu"] as Array[StringName])


func test_the_campaign_button_shows_only_in_a_campaign_stage() -> void:
	await _start()
	game.open_pause_menu()
	assert_false(game.pause_menu.campaign_button.visible, "a skirmish has no campaign map to go back to")


func test_the_menu_fits_the_screen_and_the_menu_button_fits_the_bar() -> void:
	await _start([&"tamsin", &"brannoc", &"ignar"])
	assert_eq(game.sim.party.size(), 3, "a full party, the busiest top bar")
	game.open_pause_menu()
	await wait_process_frames(2)
	# The headless test window stretches the canvas taller than 1080, so check the panel's size and
	# that it sits in the middle.
	var panel := game.pause_menu.resume_button.get_parent().get_parent().get_parent() as Control
	var rect := panel.get_global_rect()
	assert_true(rect.size.x <= 1920.0 and rect.size.y <= 1000.0, "the menu fits a 1920x1080 screen: %s" % rect.size)
	var view := game.pause_menu.get_viewport_rect()
	assert_almost_eq(rect.get_center(), view.get_center(), Vector2(2, 2), "the menu is in the middle")
	for button: Button in [game.pause_menu.resume_button, game.pause_menu.audio_button,
			game.pause_menu.menu_button, game.pause_menu.quit_button]:
		assert_true(rect.encloses(button.get_global_rect()), "%s is inside the menu" % button.text)
	var bar := game.hud._top_bar.get_global_rect()
	assert_eq(game.hud._top_bar.size.x, 1896.0, "the top bar keeps its width")
	for control: Control in [game.hud._menu_button, game.hud._wave_button, game.hud._next]:
		assert_true(bar.encloses(control.get_global_rect()), "%s is inside the top bar" % control.name)
