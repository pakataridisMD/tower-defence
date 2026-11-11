extends GutTest
## The audio settings: each bus's volume and mute, the music duck on top of the player's music
## volume, the settings panel, and opening it from a run.

const GAME_SCENE := preload("res://scenes/game/game.tscn")


func before_each() -> void:
	AudioSettings.reset_to_defaults()


func after_all() -> void:
	AudioSettings.reset_to_defaults()


func _db(bus: StringName) -> float:
	return AudioServer.get_bus_volume_db(AudioServer.get_bus_index(bus))


func _muted(bus: StringName) -> bool:
	return AudioServer.is_bus_mute(AudioServer.get_bus_index(bus))


func _key(keycode: Key) -> void:
	var press := InputEventKey.new()
	press.keycode = keycode
	press.pressed = true
	get_tree().root.push_input(press, true)
	var release := press.duplicate() as InputEventKey
	release.pressed = false
	get_tree().root.push_input(release, true)


func test_tests_never_write_the_players_settings_file() -> void:
	assert_false(AudioSettings.persist)


func test_every_setting_has_a_real_bus() -> void:
	for entry in AudioSettings.BUSES:
		assert_gte(AudioServer.get_bus_index(entry[0]), 0, "bus %s" % entry[0])


func test_a_volume_sets_its_bus() -> void:
	AudioSettings.set_volume(&"Sfx", 0.5)
	assert_almost_eq(_db(&"Sfx"), linear_to_db(0.5), 0.01)
	assert_false(_muted(&"Sfx"))
	AudioSettings.set_volume(&"Sfx", 0.0)
	assert_true(_muted(&"Sfx"), "zero is silent")


func test_mute_keeps_the_volume() -> void:
	AudioSettings.set_volume(&"Ui", 0.6)
	AudioSettings.set_muted(&"Ui", true)
	assert_true(_muted(&"Ui"))
	AudioSettings.set_muted(&"Ui", false)
	assert_false(_muted(&"Ui"))
	assert_almost_eq(AudioSettings.volume(&"Ui"), 0.6, 0.001)


func test_mute_all_toggles_the_master_bus() -> void:
	assert_true(AudioSettings.toggle_mute_all())
	assert_true(_muted(&"Master"))
	assert_false(AudioSettings.toggle_mute_all())
	assert_false(_muted(&"Master"))


func test_the_music_duck_sits_on_top_of_the_players_music_volume() -> void:
	AudioSettings.set_volume(&"Music", 0.5)
	SoundPlayer.instance._set_duck(-6.0)
	assert_almost_eq(_db(&"Music"), linear_to_db(0.5) - 6.0, 0.01)
	SoundPlayer.instance._set_duck(0.0)
	assert_almost_eq(_db(&"Music"), linear_to_db(0.5), 0.01)


func test_the_panel_changes_the_settings() -> void:
	var panel: AudioPanel = add_child_autofree(AudioPanel.new())
	assert_eq(panel.sliders.size(), AudioSettings.BUSES.size())
	panel.sliders[&"Music"].value = 30
	assert_almost_eq(AudioSettings.volume(&"Music"), 0.3, 0.001)
	panel.mutes[&"Voice"].button_pressed = true
	assert_true(AudioSettings.is_muted(&"Voice"))
	panel.close_panel()
	assert_false(panel.visible)


func test_o_opens_the_audio_settings_in_a_run_and_pauses_it() -> void:
	Progress.use_memory_profile()
	var game: Game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	_key(KEY_O)
	assert_true(game.audio_panel.visible)
	assert_true(game.paused, "the run waits while the settings are open")
	_key(KEY_ESCAPE)
	assert_false(game.audio_panel.visible)
	assert_false(game.paused, "and goes on when they close")
	_key(KEY_M)
	assert_true(AudioSettings.is_muted(&"Master"), "M mutes everything")
	_key(KEY_M)
	assert_false(AudioSettings.is_muted(&"Master"))
