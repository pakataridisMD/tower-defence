extends GutTest
## Drives the real game scene with simulated key presses and clicks, the way a player would.

const GAME_SCENE := preload("res://scenes/game/game.tscn")

var game: Game
## A cell of road near where it enters the board, and an empty tile of grass next to it.
var path_cell := Vector2i(-1, -1)
var grass_cell := Vector2i(-1, -1)


func before_each() -> void:
	Progress.use_memory_profile()
	game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	_find_cells()


func _find_cells() -> void:
	var map := game.sim.config.map
	for point in map.path_points(0):
		var cell := map.cell_at(point)
		if map.is_inside(cell) and cell.x >= 2 and cell.y >= 2:
			path_cell = cell
			break
	for reach in range(1, 4):
		for offset: Vector2i in [Vector2i(0, reach), Vector2i(0, -reach), Vector2i(reach, 0), Vector2i(-reach, 0)]:
			var cell := path_cell + offset
			if grass_cell.x < 0 and map.is_inside(cell) and not game.sim.is_path(cell):
				grass_cell = cell
	assert_true(game.sim.is_path(path_cell), "found the road")
	assert_true(grass_cell.x >= 0, "found grass beside it")


## Positions are in the game's 1920x1080 canvas coordinates, whatever the window size.
func _push(event: InputEvent) -> void:
	get_tree().root.push_input(event, true)


func _key(keycode: Key) -> void:
	var press := InputEventKey.new()
	press.keycode = keycode
	press.pressed = true
	_push(press)
	var release := press.duplicate() as InputEventKey
	release.pressed = false
	_push(release)


func _click(at: Vector2, button: MouseButton = MOUSE_BUTTON_LEFT) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = at
	_push(motion)
	var press := InputEventMouseButton.new()
	press.button_index = button
	press.pressed = true
	press.position = at
	_push(press)
	var release := press.duplicate() as InputEventMouseButton
	release.pressed = false
	_push(release)


func _click_cell(cell: Vector2i, button: MouseButton = MOUSE_BUTTON_LEFT) -> void:
	_click(game.board.to_global(game.sim.config.map.cell_center(cell)), button)


## GUT's own output window covers the side panel during test runs and would catch a simulated
## click there, so HUD buttons are pressed directly once they are checked to be pressable.
func _press(button: Button) -> void:
	assert_true(button.is_visible_in_tree() and not button.disabled, "'%s' should be pressable" % button.text)
	button.pressed.emit()


func _open_web() -> void:
	_key(KEY_T)
	await wait_process_frames(1)


# --- Skill web -----------------------------------------------------------------

func test_t_opens_and_closes_the_skill_web() -> void:
	_key(KEY_T)
	assert_true(game.web.visible)
	_key(KEY_T)
	assert_false(game.web.visible)


func test_clicking_a_web_node_takes_it() -> void:
	await _open_web()
	_click(game.web.screen_position(&"fire_entry"))
	assert_true(game.sim.tree.is_allocated(&"fire_entry"))
	assert_true(game.sim.is_unlocked(&"fire_brazier"))


func test_right_click_refunds_a_node_taken_this_break() -> void:
	await _open_web()
	_click(game.web.screen_position(&"fire_entry"))
	_click(game.web.screen_position(&"fire_entry"), MOUSE_BUTTON_RIGHT)
	assert_false(game.sim.tree.is_allocated(&"fire_entry"))
	assert_eq(game.sim.tree.points, 1)


func test_nodes_cannot_be_refunded_once_the_wave_starts() -> void:
	await _open_web()
	_click(game.web.screen_position(&"fire_entry"))
	_key(KEY_SPACE)
	assert_false(game.web.visible, "starting a wave closes the web")
	await _open_web()
	_click(game.web.screen_position(&"fire_entry"), MOUSE_BUTTON_RIGHT)
	assert_true(game.sim.tree.is_allocated(&"fire_entry"))


func test_escape_closes_the_web() -> void:
	await _open_web()
	_key(KEY_ESCAPE)
	assert_false(game.web.visible)


# --- Building and selling --------------------------------------------------------

func test_a_hotkey_and_a_click_build_a_tower() -> void:
	game.sim.allocate_node(&"fire_entry")
	var gold := game.sim.gold
	_key(KEY_1)
	assert_eq(game.board.placing, &"fire_brazier")
	_click_cell(grass_cell)
	assert_not_null(game.sim.tower_at(grass_cell))
	assert_eq(game.sim.gold, gold - game.sim.tower_price(&"fire_brazier"))
	assert_eq(game.board.placing, &"", "a plain click builds one tower and stops placing")


func test_the_tower_button_starts_placing() -> void:
	game.sim.allocate_node(&"fire_entry")
	await wait_process_frames(1)
	_press(game.hud._tower_buttons[&"fire_brazier"])
	assert_eq(game.board.placing, &"fire_brazier")


func test_locked_towers_cannot_be_picked() -> void:
	_key(KEY_1)
	assert_eq(game.board.placing, &"")


func test_clicking_the_path_does_not_build() -> void:
	game.sim.allocate_node(&"fire_entry")
	_key(KEY_1)
	_click_cell(path_cell)
	assert_null(game.sim.tower_at(path_cell))
	assert_eq(game.board.placing, &"fire_brazier", "still placing after a failed click")


func test_right_click_cancels_placing() -> void:
	game.sim.allocate_node(&"fire_entry")
	_key(KEY_1)
	_click_cell(grass_cell, MOUSE_BUTTON_RIGHT)
	assert_eq(game.board.placing, &"")
	assert_null(game.sim.tower_at(grass_cell))


func test_selecting_and_selling_a_tower() -> void:
	game.sim.allocate_node(&"fire_entry")
	var tower := game.sim.place_tower(&"fire_brazier", grass_cell)
	var gold := game.sim.gold
	_click_cell(grass_cell)
	assert_eq(game.board.selected, tower)
	assert_eq(game.hud.selected, tower)
	await wait_process_frames(1)
	_press(game.hud._sell_button)
	assert_null(game.sim.tower_at(grass_cell))
	assert_eq(game.sim.gold, gold + game.sim.sell_value(tower))
	assert_null(game.board.selected)


func _action_button(kind: StringName, id: StringName = &"") -> Button:
	for child in game.hud._actions.get_children():
		if child.get_meta(&"action") == kind and (id.is_empty() or child.get_meta(&"id") == id):
			return child as Button
	return null


func test_the_tower_panel_levels_up_and_ascends() -> void:
	game.sim.allocate_node(&"fire_entry")
	game.sim.gold = 2000
	var tower := game.sim.place_tower(&"fire_brazier", grass_cell)
	_click_cell(grass_cell)
	for level in [2, 3]:
		await wait_process_frames(1)
		_press(_action_button(&"level"))
		assert_eq(tower.level, level)
	await wait_process_frames(1)
	assert_null(_action_button(&"level"), "no level button at the top level")
	_press(_action_button(&"ascend", &"hearth"))
	assert_eq(tower.ascendancy.id, &"hearth")
	await wait_process_frames(1)
	assert_eq(game.hud._actions.get_child_count(), 0, "nothing left to buy")


func test_the_tower_panel_turns_a_base_tower_into_a_hybrid() -> void:
	game.sim.tree.points = 10
	for id: StringName in [&"fire_entry", &"fire_cw", &"storm_entry", &"storm_ccw", &"bridge_plasma"]:
		game.sim.allocate_node(id)
	game.sim.gold = 2000
	var tower := game.sim.place_tower(&"storm_spire", grass_cell)
	_click_cell(grass_cell)
	await wait_process_frames(1)
	_press(_action_button(&"hybrid", &"hybrid_plasma"))
	assert_eq(tower.data.id, &"hybrid_plasma")
	assert_eq(game.sim.tower_at(grass_cell), tower)
	await wait_process_frames(2)
	assert_eq(game.board.art._towers[tower.id].data_id, &"hybrid_plasma", "the board redraws the tower as its new type")


func test_shop_tabs_show_duals_and_triples_once_unlocked() -> void:
	game.sim.tree.points = 20
	game.sim.gold = 2000
	for element: String in ["fire", "storm", "nature"]:
		game.sim.allocate_node(StringName(element + "_entry"))
		game.sim.allocate_node(StringName(element + "_core"))
	await wait_process_frames(2)
	var triple: Button = game.hud._tower_buttons[&"triple_cinderstorm"]
	assert_false(triple.visible, "the shop opens on the base towers")
	assert_string_contains(game.hud._tier_tabs[3].text, "1")
	game.hud.show_shop_tier(3)
	await wait_process_frames(2)
	assert_true(triple.visible)
	assert_false(game.hud._tower_buttons[&"triple_starfall"].visible, "still locked")
	assert_false(game.hud._tower_buttons[&"fire_brazier"].visible, "base towers are on their own tab")
	_press(triple)
	assert_eq(game.board.placing, &"triple_cinderstorm")
	game.hud.show_shop_tier(2)
	await wait_process_frames(2)
	assert_true(game.hud._tower_buttons[&"hybrid_wildfire"].visible, "Fire and Nature cores unlock Wildfire")


# --- Hotkeys -------------------------------------------------------------------------

func test_tab_turns_the_shop_page_and_numbers_pick_from_it() -> void:
	game.sim.tree.points = 20
	game.sim.gold = 2000
	for id: StringName in [&"fire_entry", &"fire_cw", &"storm_entry", &"storm_ccw", &"bridge_plasma"]:
		game.sim.allocate_node(id)
	_key(KEY_TAB)
	assert_eq(game.hud.shop_tier(), 2)
	_key(KEY_1)
	assert_eq(game.board.placing, &"hybrid_plasma", "1 picks the first tower on the open page")
	_key(KEY_TAB)
	assert_eq(game.hud.shop_tier(), 1, "no triple is unlocked, so Tab goes back to the base towers")
	_key(KEY_2)
	assert_eq(game.board.placing, &"storm_spire")


func test_keys_upgrade_and_sell_the_selected_tower() -> void:
	game.sim.allocate_node(&"fire_entry")
	game.sim.gold = 2000
	var tower := game.sim.place_tower(&"fire_brazier", grass_cell)
	_click_cell(grass_cell)
	await wait_process_frames(2)
	assert_eq((game.hud._actions.get_child(0) as KeyButton).key_text, "Z")
	_key(KEY_Z)
	assert_eq(tower.level, 2)
	_key(KEY_DELETE)
	assert_null(game.sim.tower_at(grass_cell))


# --- Skills --------------------------------------------------------------------------

func _move_mouse_to(cell: Vector2i) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = game.board.to_global(game.sim.config.map.cell_center(cell))
	_push(motion)


func test_a_skill_key_aims_and_a_click_casts() -> void:
	game.sim.allocate_node(&"fire_entry")
	_key(KEY_Q)
	assert_eq(game.board.aiming, &"", "skills wait for a wave")
	_key(KEY_SPACE)
	_key(KEY_Q)
	assert_eq(game.board.aiming, &"meteor")
	_click_cell(path_cell)
	assert_eq(game.board.aiming, &"")
	assert_gt(game.sim.skill_cooldown_left(&"meteor"), 0.0)
	_key(KEY_Q)
	assert_eq(game.board.aiming, &"", "it is cooling down")


func test_a_skill_key_pressed_twice_casts_at_the_mouse() -> void:
	game.sim.allocate_node(&"fire_entry")
	_key(KEY_SPACE)
	_move_mouse_to(path_cell)
	_key(KEY_Q)
	assert_eq(game.board.aiming, &"meteor")
	_key(KEY_Q)
	assert_eq(game.board.aiming, &"")
	assert_gt(game.sim.skill_cooldown_left(&"meteor"), 0.0)


func test_a_skill_that_needs_no_aim_is_cast_by_its_key() -> void:
	game.sim.allocate_node(&"storm_entry")
	_key(KEY_SPACE)
	_key(KEY_W)
	assert_eq(game.board.aiming, &"")
	assert_gt(game.sim.skill_time_left(&"surge"), 0.0)


func test_escape_and_right_click_stop_aiming() -> void:
	game.sim.allocate_node(&"fire_entry")
	_key(KEY_SPACE)
	_key(KEY_Q)
	_key(KEY_ESCAPE)
	assert_eq(game.board.aiming, &"")
	assert_false(game.paused, "Esc stopped the aiming, not the game")
	_key(KEY_Q)
	_click_cell(grass_cell, MOUSE_BUTTON_RIGHT)
	assert_eq(game.board.aiming, &"")
	assert_eq(game.sim.skill_cooldown_left(&"meteor"), 0.0, "nothing was cast")


func test_skill_buttons_show_their_key_and_cooldown() -> void:
	game.sim.allocate_node(&"fire_entry")
	await wait_process_frames(2)
	var button: KeyButton = game.hud._skill_buttons[&"meteor"]
	assert_eq(button.key_text, "Q")
	assert_false(button.disabled)
	assert_true(game.hud._skill_buttons[&"surge"].disabled, "locked until Storm is taken")
	_key(KEY_SPACE)
	_press(button)
	assert_eq(game.board.aiming, &"meteor")
	_press(button)
	assert_eq(game.board.aiming, &"", "pressing the button again puts the skill away")
	assert_true(game.sim.use_skill(&"meteor", Vector2(100, 100)))
	await wait_process_frames(2)
	assert_gt(button.cooldown, 0.9)
	assert_eq(button.cooldown_text, str(roundi(game.sim.skill_cooldown(&"meteor"))))


# --- Layout --------------------------------------------------------------------------

## The top bar and the side panel used to run off the screen when they had a lot to show.
func test_the_hud_stays_on_the_screen_at_its_busiest() -> void:
	game.sim.tree.points = 40
	game.sim.gold = 99999
	for element: String in ["fire", "storm", "nature", "water", "earth", "void"]:
		game.sim.allocate_node(StringName(element + "_entry"))
		game.sim.allocate_node(StringName(element + "_core"))
	game.sim.wave_index = game.sim.total_waves() - 1
	game.sim.place_tower(&"fire_brazier", grass_cell)
	_click_cell(grass_cell)
	var hud := game.hud
	var screen := Rect2(0, 0, 1920, 1080)
	for tier in [1, 2, 3]:
		hud.show_shop_tier(tier)
		await wait_process_frames(4)
		assert_eq(hud._top_bar.size.x, 1896.0, "the top bar keeps its width")
		assert_eq(hud._side_panel.size, Hud.SIDE_PANEL_SIZE, "the side panel keeps its size on page %d" % tier)
		var bar := hud._top_bar.get_global_rect()
		for control: Control in [hud._gold, hud._wave, hud._next, hud._web_button, hud._speed_button, hud._wave_button]:
			assert_true(bar.encloses(control.get_global_rect()), "%s is inside the top bar" % control.name)
		var side := hud._side_panel.get_global_rect()
		assert_true(screen.encloses(side))
		assert_true(side.encloses(hud._sell_button.get_global_rect()), "the sell button is inside the side panel")
		var shown := 0
		for button: KeyButton in hud._tower_buttons.values():
			if button.visible:
				shown += 1
				var rect := button.get_global_rect()
				assert_true(rect.position.x >= side.position.x and rect.end.x <= side.end.x,
						"a tower button fits the panel's width on page %d" % tier)
		assert_gt(shown, 5)
		for button: KeyButton in hud._skill_buttons.values():
			assert_true(side.encloses(button.get_global_rect()), "%s fits the side panel" % button.text)


# --- Waves, speed and pause ------------------------------------------------------

func test_space_starts_the_wave_and_time_moves() -> void:
	_key(KEY_SPACE)
	assert_eq(game.sim.state, RunSim.State.WAVE)
	await wait_seconds(0.2)
	assert_gt(game.sim.time_in_wave, 0.0)


func test_pause_stops_the_simulation() -> void:
	_key(KEY_SPACE)
	_key(KEY_P)
	await wait_seconds(0.2)
	assert_eq(game.sim.time_in_wave, 0.0)
	_key(KEY_P)
	await wait_seconds(0.2)
	assert_gt(game.sim.time_in_wave, 0.0)


func test_the_open_web_pauses_the_wave() -> void:
	_key(KEY_SPACE)
	await _open_web()
	var time := game.sim.time_in_wave
	await wait_seconds(0.2)
	assert_eq(game.sim.time_in_wave, time)


func test_f_cycles_the_speed() -> void:
	assert_eq(game.hud.speed, 1)
	_key(KEY_F)
	assert_eq(game.hud.speed, 2)
	_key(KEY_F)
	_key(KEY_F)
	assert_eq(game.hud.speed, 1)


# --- Camera --------------------------------------------------------------------------

func _settle_camera() -> void:
	for i in 40:
		game.camera._process(0.05)


func test_the_whole_map_shows_at_the_start() -> void:
	var map_size := game.sim.config.map.size_in_pixels() * game.board.scale
	assert_true(game.camera.shows_all())
	assert_true(BoardCamera.VIEW_RECT.encloses(Rect2(game.board.position, map_size)), "the map fits the view")
	assert_true(map_size.x > BoardCamera.VIEW_RECT.size.x * 0.75, "and fills most of it")


func test_the_wheel_zooms_in_on_the_cursor_and_home_shows_everything() -> void:
	var cell := Vector2i(10, 10)
	var at := game.board.to_global(game.sim.config.map.cell_center(cell))
	var before := game.board.scale.x
	var wheel := InputEventMouseButton.new()
	wheel.button_index = MOUSE_BUTTON_WHEEL_UP
	wheel.pressed = true
	wheel.position = at
	_push(wheel)
	_settle_camera()
	assert_gt(game.board.scale.x, before, "zoomed in")
	assert_almost_eq(game.board.to_global(game.sim.config.map.cell_center(cell)), at, Vector2(2, 2),
		"the cell under the cursor stays there")
	assert_false(game.camera.shows_all())
	_key(KEY_HOME)
	assert_true(game.camera.shows_all())


func test_panning_stops_at_the_edge_of_the_map() -> void:
	game.camera.set_view(1.0, Vector2.ZERO)
	game.camera.pan(Vector2(5000, 5000))
	assert_eq(game.board.position, BoardCamera.VIEW_RECT.position, "the top-left corner stops at the view's corner")
	game.camera.pan(Vector2(-9000, -9000))
	var far_corner := game.board.to_global(game.sim.config.map.size_in_pixels())
	assert_almost_eq(far_corner, BoardCamera.VIEW_RECT.end, Vector2(1, 1), "and so does the bottom-right")


func test_clicks_still_land_on_the_right_cell_when_zoomed_in() -> void:
	game.sim.allocate_node(&"fire_entry")
	game.camera.set_view(2.0, game.sim.config.map.cell_center(grass_cell))
	_key(KEY_1)
	_click_cell(grass_cell)
	assert_not_null(game.sim.tower_at(grass_cell))
