extends GutTest
## The main menu and the meta tree screen, driven like a player would. Progress is kept in memory,
## so these tests never read or write a real save.

const MENU_SCENE := preload("res://scenes/main.tscn")
const META_TREE_SCENE := preload("res://scenes/meta/meta_tree.tscn")


func _use_profile(points_earned: int, nodes: Array[StringName] = []) -> void:
	var profile := PlayerProfile.new()
	profile.meta_points_earned = points_earned
	profile.meta_nodes = nodes
	Progress.use_memory_profile(profile)


func _open(scene: PackedScene) -> Control:
	var screen: Control = scene.instantiate()
	add_child_autofree(screen)
	await wait_process_frames(2)
	return screen


## Positions are in the game's canvas coordinates, whatever the window size.
func _click(at: Vector2, button: MouseButton = MOUSE_BUTTON_LEFT) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = at
	get_tree().root.push_input(motion, true)
	var press := InputEventMouseButton.new()
	press.button_index = button
	press.pressed = true
	press.position = at
	get_tree().root.push_input(press, true)
	var release := press.duplicate() as InputEventMouseButton
	release.pressed = false
	get_tree().root.push_input(release, true)


## GUT's output window can cover parts of the screen during test runs, so buttons are pressed
## directly once they are checked to be pressable.
func _press(button: Button) -> void:
	assert_true(button.is_visible_in_tree() and not button.disabled, "'%s' should be pressable" % button.text)
	button.pressed.emit()


## Picks a toggle button the way a click does: it turns on, and its group turns the others off.
func _pick(button: Button) -> void:
	assert_true(button.is_visible_in_tree() and not button.disabled, "'%s' should be pickable" % button.text)
	button.button_pressed = true


func _buttons(screen: Control) -> Array[Button]:
	var result: Array[Button] = []
	result.assign(screen.find_children("*", "Button", true, false))
	return result


func _button_starting_with(screen: Control, text: String) -> Button:
	for button in _buttons(screen):
		if button.text.begins_with(text):
			return button
	return null


# --- Meta tree screen --------------------------------------------------------------

func test_clicking_a_meta_node_takes_it_and_spends_points() -> void:
	_use_profile(5)
	var screen = await _open(META_TREE_SCENE)
	_click(screen.web.screen_position(&"command_gold"))
	assert_true(Progress.meta.tree.is_allocated(&"command_gold"))
	assert_has(Progress.meta.profile.meta_nodes, &"command_gold")
	assert_eq(Progress.meta.points(), 3, "War Chest costs 2")


func test_a_node_without_enough_points_is_not_taken() -> void:
	_use_profile(1)
	var screen = await _open(META_TREE_SCENE)
	_click(screen.web.screen_position(&"mastery_range"))
	assert_false(Progress.meta.tree.is_allocated(&"mastery_range"), "it costs 3")
	assert_eq(Progress.meta.points(), 1)


func test_right_click_refunds_a_meta_node_any_time() -> void:
	_use_profile(5, [&"command_gold"])
	var screen = await _open(META_TREE_SCENE)
	_click(screen.web.screen_position(&"command_gold"), MOUSE_BUTTON_RIGHT)
	assert_false(Progress.meta.tree.is_allocated(&"command_gold"))
	assert_eq(Progress.meta.points(), 5)


func test_refund_all_needs_a_second_click() -> void:
	_use_profile(5, [&"command_gold", &"command_purse"])
	var screen = await _open(META_TREE_SCENE)
	_press(screen.refund_all)
	assert_true(Progress.meta.tree.is_allocated(&"command_purse"), "the first click only asks")
	_press(screen.refund_all)
	assert_eq(Progress.meta.profile.meta_nodes.size(), 0)
	assert_eq(Progress.meta.points(), 5)
	assert_true(screen.refund_all.disabled, "nothing left to refund")


# --- Main menu -----------------------------------------------------------------------

func _key(keycode: Key) -> void:
	var press := InputEventKey.new()
	press.keycode = keycode
	press.pressed = true
	get_tree().root.push_input(press)


func test_a_new_player_sees_locked_maps_and_levels() -> void:
	_use_profile(0)
	var menu = await _open(MENU_SCENE)
	menu.open_page(&"skirmish")
	var serpentine := _button_starting_with(menu, "Serpentine")
	assert_not_null(serpentine)
	assert_true(serpentine.disabled)
	assert_string_contains(serpentine.tooltip_text, "Talents")
	assert_true(_button_starting_with(menu, "Grim").disabled)
	assert_true(_button_starting_with(menu, "Oblivion").disabled)
	assert_false(_button_starting_with(menu, "Cinderfall").disabled, "the land maps are open from the start")
	assert_true(_button_starting_with(menu, "Switchback").button_pressed)


func test_picking_an_unlocked_map_and_level_sets_up_the_next_run() -> void:
	_use_profile(20, [&"expedition_serpentine", &"expedition_scouts", &"expedition_hardened", &"expedition_hard"])
	var menu = await _open(MENU_SCENE)
	menu.open_page(&"skirmish")
	_pick(_button_starting_with(menu, "Serpentine"))
	_pick(_button_starting_with(menu, "Grim"))
	assert_false(_button_starting_with(menu, "Switchback").button_pressed, "one map at a time")
	var config := Progress.run_config()
	assert_eq(config.map.id, &"serpentine")
	assert_eq(config.difficulty.id, &"hard")
	assert_eq(Progress.meta.profile.last_map, &"serpentine")
	assert_false(config.endless)
	_pick(_button_starting_with(menu, "Endless"))
	assert_true(Progress.run_config().endless)
	assert_true(Progress.meta.profile.last_endless)


func test_the_talents_button_shows_unspent_points() -> void:
	_use_profile(7)
	var menu = await _open(MENU_SCENE)
	assert_eq(menu.buttons[&"talents"].text, "Talents")
	assert_string_contains(menu.buttons[&"talents"].note, "7 points")


func test_the_title_screen_has_every_entry() -> void:
	_use_profile(0)
	var menu = await _open(MENU_SCENE)
	for id: StringName in [&"campaign", &"skirmish", &"heroes", &"talents", &"codex", &"settings", &"credits", &"quit"]:
		assert_true(menu.buttons.has(id), "%s is on the menu" % id)
		assert_true(menu.buttons[id].is_visible_in_tree())
	assert_false(menu.buttons.has(&"continue"), "nothing to continue before the first win")


func test_continue_offers_the_next_stage_of_the_furthest_land() -> void:
	_use_profile(0)
	var campaign: CampaignData = Progress.meta.campaigns_in_order()[0]
	Progress.meta.profile.stage_stars[campaign.stages[0].id] = 2
	var menu = await _open(MENU_SCENE)
	assert_true(menu.buttons.has(&"continue"))
	assert_eq(menu.continue_stage, campaign.stages[1].id)


func test_every_page_opens_and_esc_comes_back() -> void:
	_use_profile(0)
	var menu = await _open(MENU_SCENE)
	for id: StringName in [&"skirmish", &"heroes", &"codex", &"settings", &"credits"]:
		_press(menu.buttons[id])
		await wait_process_frames(1)
		assert_eq(menu.page, id)
		assert_true(menu.pages[id].visible)
		assert_false(menu.buttons[&"campaign"].is_visible_in_tree(), "the title menu hides behind a page")
		_key(KEY_ESCAPE)
		await wait_process_frames(1)
		assert_eq(menu.page, &"", "Esc goes back from %s" % id)
		assert_true(menu.buttons[&"campaign"].is_visible_in_tree())


func test_keys_open_pages_and_esc_asks_before_quitting() -> void:
	_use_profile(0)
	var menu = await _open(MENU_SCENE)
	_key(KEY_H)
	await wait_process_frames(1)
	assert_eq(menu.page, &"heroes")
	_key(KEY_ESCAPE)
	_key(KEY_K)
	await wait_process_frames(1)
	assert_eq(menu.page, &"codex")
	_key(KEY_ESCAPE)
	_key(KEY_ESCAPE)
	await wait_process_frames(1)
	assert_true(menu.quit_dialog.visible, "Esc on the title screen asks first")
	_key(KEY_ESCAPE)
	await wait_process_frames(1)
	assert_false(menu.quit_dialog.visible, "and Esc again stays")


func test_the_heroes_page_takes_a_hero_into_the_party() -> void:
	_use_profile(0)
	var menu = await _open(MENU_SCENE)
	menu.open_page(&"heroes")
	var heroes: HeroesPage = menu.pages[&"heroes"]
	# Bring every hero, so some are left out of the three-hero party.
	for hero in Progress.meta.heroes_in_order():
		for stage_id in [hero.joins_after, hero.arrives_in]:
			if not stage_id.is_empty():
				Progress.meta.profile.stage_stars[stage_id] = 1
	heroes.refresh()
	var outside: HeroData = null
	for hero in Progress.meta.joined_heroes():
		if not Progress.meta.party().has(hero):
			outside = hero
	assert_not_null(outside)
	heroes.select(outside.id)
	assert_eq(heroes.party_button.text, "Take into battle")
	_press(heroes.party_button)
	assert_true(Progress.meta.party().has(outside), "the button takes them into the party")
	assert_eq(heroes.party_button.text, "Leave behind")
	Progress.meta.profile.stage_stars.clear()
	heroes.refresh()
	var locked: HeroData = Progress.meta.heroes_in_order()[-1]
	heroes.select(locked.id)
	assert_true(heroes.party_button.disabled, "a hero who has not joined cannot be taken")


func test_the_codex_lists_towers_enemies_and_elements() -> void:
	_use_profile(0)
	var menu = await _open(MENU_SCENE)
	menu.open_page(&"codex")
	var codex: CodexPage = menu.pages[&"codex"]
	for tab in CodexPage.TABS.size():
		codex.show_tab(tab)
		await wait_process_frames(1)
		assert_false(codex.selected.is_empty(), "tab %s shows an entry" % CodexPage.TABS[tab])
	assert_true(DataRegistry.elements.has(codex.selected))


func test_the_settings_page_sets_the_volume() -> void:
	_use_profile(0)
	AudioSettings.reset_to_defaults()
	var menu = await _open(MENU_SCENE)
	menu.open_page(&"settings")
	var settings: SettingsPage = menu.pages[&"settings"]
	settings.sliders[&"Music"].value = 40
	assert_almost_eq(AudioSettings.volume(&"Music"), 0.4, 0.001)
	settings.mutes[&"Music"].button_pressed = true
	assert_true(AudioSettings.is_muted(&"Music"))
	AudioSettings.reset_to_defaults()
	assert_eq(settings.developer_label.text, "Developed by Pasiv Production  (Doctor Paris and Thanos)")
