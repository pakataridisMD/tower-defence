extends GutTest
## Switching between full screen and a window: F11 / Alt+Enter / Cmd+Ctrl+F from anywhere, the
## title screen button, the Esc menu button and the Settings picks all agree.

var _was: bool


func before_each() -> void:
	Progress.use_memory_profile()
	_was = VideoSettings.fullscreen


func after_each() -> void:
	VideoSettings.fullscreen = _was


func _press(keycode: Key, alt := false, ctrl := false, meta := false) -> void:
	var press := InputEventKey.new()
	press.keycode = keycode
	press.alt_pressed = alt
	press.ctrl_pressed = ctrl
	press.meta_pressed = meta
	press.pressed = true
	get_tree().root.push_input(press, true)
	var release := press.duplicate() as InputEventKey
	release.pressed = false
	get_tree().root.push_input(release, true)


func test_toggle_keys() -> void:
	VideoSettings.fullscreen = true
	_press(KEY_F11)
	assert_false(VideoSettings.fullscreen, "F11 leaves full screen")
	_press(KEY_ENTER, true)
	assert_true(VideoSettings.fullscreen, "Alt+Enter goes back to full screen")
	_press(KEY_F, false, true, true)
	assert_false(VideoSettings.fullscreen, "Cmd+Ctrl+F switches too")
	_press(KEY_F)
	_press(KEY_ENTER)
	assert_false(VideoSettings.fullscreen, "plain F and Enter do nothing")


func test_toggle_text() -> void:
	VideoSettings.fullscreen = true
	assert_string_starts_with(VideoSettings.toggle_text(), "Exit full screen")
	VideoSettings.fullscreen = false
	assert_string_starts_with(VideoSettings.toggle_text(), "Full screen")


func test_title_screen_button() -> void:
	VideoSettings.fullscreen = false
	var menu := MainMenu.new()
	add_child_autofree(menu)
	await wait_process_frames(1)
	assert_not_null(menu.fullscreen_button)
	menu.fullscreen_button.pressed.emit()
	assert_true(VideoSettings.fullscreen)
	assert_string_starts_with(menu.fullscreen_button.text, "Exit full screen")
	_press(KEY_F11)
	assert_string_starts_with(menu.fullscreen_button.text, "Full screen", "the key updates the button")
	menu.open_page(&"settings")
	var settings: SettingsPage = menu.pages[&"settings"]
	assert_true(settings._mode_buttons[1].button_pressed, "Settings shows Windowed")
	_press(KEY_F11)
	assert_true(settings._mode_buttons[0].button_pressed, "Settings follows the key")


func test_pause_menu_button() -> void:
	VideoSettings.fullscreen = true
	var pause := PauseMenu.new()
	add_child_autofree(pause)
	pause.open("", false, false)
	assert_string_starts_with(pause.fullscreen_button.text, "Exit full screen")
	pause.fullscreen_button.pressed.emit()
	assert_false(VideoSettings.fullscreen)
	assert_string_starts_with(pause.fullscreen_button.text, "Full screen")
