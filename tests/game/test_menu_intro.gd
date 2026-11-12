extends GutTest
## The studio splash when the game opens (StudioSplash) and the title screen's music (MenuMusic),
## with its saved on/off switch in Settings > Sound.


func before_each() -> void:
	AudioSettings.reset_to_defaults()


func after_all() -> void:
	AudioSettings.reset_to_defaults()


func _splash() -> StudioSplash:
	var splash := StudioSplash.new()
	splash.play_anyway = true
	splash.leave_to_menu = false
	add_child_autofree(splash)
	return splash


func test_the_game_opens_on_the_splash() -> void:
	assert_eq(ProjectSettings.get_setting("application/run/main_scene"), "res://scenes/splash.tscn")
	var scene := load("res://scenes/splash.tscn") as PackedScene
	assert_not_null(scene)


func test_bot_and_headless_runs_skip_the_splash() -> void:
	# GUT runs headless, so a real launch like this one goes straight to the title screen.
	assert_true(StudioSplash.should_skip())


func test_the_timeline_is_in_order_and_the_sound_matches_it() -> void:
	assert_lt(StudioSplash.FUSE_LIT, StudioSplash.HIT)
	assert_lt(StudioSplash.HIT, StudioSplash.LOGO_IN)
	assert_lt(StudioSplash.LOGO_IN, StudioSplash.FADE_OUT)
	assert_lt(StudioSplash.FADE_OUT, StudioSplash.LENGTH)
	var sound := load(StudioSplash.SOUND) as AudioStream
	assert_not_null(sound, "the splash sound (tools/sfx/intro.py)")
	if sound != null:
		assert_almost_eq(sound.get_length(), StudioSplash.LENGTH, 0.1, "the sound is cut to the splash's length")


func test_the_bomb_bursts_and_the_name_is_forged() -> void:
	var splash := _splash()
	var ended := [false]
	splash.finished.connect(func() -> void: ended[0] = true)
	var steps := int(StudioSplash.HIT / 0.05) + 1
	for i in steps:
		splash.advance(0.05)
	assert_true(splash._exploded, "the bomb has gone off by the hit")
	assert_false(splash._bomb.visible)
	for i in int((StudioSplash.LOGO_IN - splash.time) / 0.05) + 2:
		splash.advance(0.05)
	assert_true(splash._logo.visible, "the studio's name appears after the blast")
	assert_eq(splash._name.text, "PASIV")
	assert_eq(splash._studio.text, "PRODUCTION")
	for i in int((StudioSplash.LENGTH - splash.time) / 0.05) + 2:
		splash.advance(0.05)
	assert_true(ended[0], "it ends on its own")


func test_any_key_or_click_skips_it() -> void:
	var splash := _splash()
	splash.advance(StudioSplash.SKIP_GUARD + 0.1)
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	splash._input(click)
	assert_true(splash.skipping)
	var ended := [false]
	splash.finished.connect(func() -> void: ended[0] = true)
	for i in int(StudioSplash.SKIP_FADE / 0.05) + 2:
		splash.advance(0.05)
	assert_true(ended[0], "a skip ends it within the short fade")
	assert_lt(splash.time, StudioSplash.HIT, "long before the full length")


func test_a_click_in_the_first_moment_does_not_skip() -> void:
	var splash := _splash()
	var key := InputEventKey.new()
	key.keycode = KEY_SPACE
	key.pressed = true
	splash._input(key)
	assert_false(splash.skipping)


func test_menu_music_is_on_until_turned_off_and_is_saved_with_the_audio() -> void:
	assert_true(AudioSettings.menu_music_on())
	AudioSettings.set_menu_music(false)
	assert_false(AudioSettings.menu_music_on())
	AudioSettings.reset_to_defaults()
	assert_true(AudioSettings.menu_music_on())


func test_settings_switch_turns_the_menu_music_off_and_on() -> void:
	var page := SettingsPage.new()
	add_child_autofree(page)
	assert_true(page.menu_music.button_pressed)
	page.menu_music.button_pressed = false
	assert_false(AudioSettings.menu_music_on())
	AudioSettings.set_menu_music(true)
	page.refresh()
	assert_true(page.menu_music.button_pressed)


func test_menu_music_fades_out_and_stops_when_turned_off() -> void:
	var music := MenuMusic.new()
	add_child_autofree(music)
	assert_not_null(music.player, "the music file loads")
	if music.player == null:
		return
	assert_eq(music.player.bus, &"Music")
	music._process(MenuMusic.FADE_IN + 0.1)
	assert_almost_eq(music.level, 1.0, 0.001)
	AudioSettings.set_menu_music(false)
	music._process(MenuMusic.FADE_OUT + 0.1)
	assert_almost_eq(music.level, 0.0, 0.001)
	assert_false(music.player.playing)
	AudioSettings.set_menu_music(true)
	music._process(0.1)
	assert_true(music.player.playing, "back on when turned on again")
