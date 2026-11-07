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
	assert_eq(Progress.meta.points(), 4)


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
	_use_profile(5, [&"command_gold", &"command_lives"])
	var screen = await _open(META_TREE_SCENE)
	_press(screen.refund_all)
	assert_true(Progress.meta.tree.is_allocated(&"command_lives"), "the first click only asks")
	_press(screen.refund_all)
	assert_eq(Progress.meta.profile.meta_nodes.size(), 0)
	assert_eq(Progress.meta.points(), 5)
	assert_true(screen.refund_all.disabled, "nothing left to refund")


# --- Main menu -----------------------------------------------------------------------

func test_a_new_player_sees_locked_maps_and_levels() -> void:
	_use_profile(0)
	var menu = await _open(MENU_SCENE)
	var serpentine := _button_starting_with(menu, "Serpentine")
	assert_not_null(serpentine)
	assert_true(serpentine.disabled)
	assert_string_contains(serpentine.tooltip_text, "meta tree")
	assert_true(_button_starting_with(menu, "Hard").disabled)
	assert_true(_button_starting_with(menu, "Switchback").button_pressed)


func test_picking_an_unlocked_map_and_level_sets_up_the_next_run() -> void:
	_use_profile(20, [&"expedition_serpentine", &"expedition_hard"])
	var menu = await _open(MENU_SCENE)
	_pick(_button_starting_with(menu, "Serpentine"))
	_pick(_button_starting_with(menu, "Hard"))
	assert_false(_button_starting_with(menu, "Switchback").button_pressed, "one map at a time")
	var config := Progress.run_config()
	assert_eq(config.map.id, &"serpentine")
	assert_eq(config.difficulty.id, &"hard")
	assert_eq(Progress.meta.profile.last_map, &"serpentine")


func test_the_meta_tree_button_shows_unspent_points() -> void:
	_use_profile(7)
	var menu = await _open(MENU_SCENE)
	assert_not_null(_button_starting_with(menu, "Meta tree"))
	assert_string_contains(_button_starting_with(menu, "Meta tree").text, "7 points to spend")
