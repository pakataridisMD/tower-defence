extends GutTest
## The ten save slots: saving and loading from the main menu and from the Esc menu during a run.
## Tests keep slots in memory (Progress.use_memory_profile) and never change scene.

const GAME_SCENE := preload("res://scenes/game/game.tscn")
const MENU_SCENE := preload("res://scenes/main.tscn")
const CELL := Vector2i(3, 3)

var game: Game


func before_each() -> void:
	Progress.use_memory_profile()


func after_each() -> void:
	Progress.use_memory_profile()


func _start_game() -> Game:
	game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	# Loading would change scene: note the slot instead.
	for connection in game.saves_page.load_confirmed.get_connections():
		game.saves_page.load_confirmed.disconnect(connection["callable"])
	return game


func _menu() -> MainMenu:
	var menu: MainMenu = MENU_SCENE.instantiate()
	add_child_autofree(menu)
	await wait_process_frames(1)
	for connection in (menu._page(&"saves") as SavesPage).load_confirmed.get_connections():
		(menu.pages[&"saves"] as SavesPage).load_confirmed.disconnect(connection["callable"])
	return menu


func _press(button: Button) -> void:
	assert_true(button.is_visible_in_tree() and not button.disabled, "'%s' should be pressable" % button.text)
	button.pressed.emit()


## A tower somewhere it can stand, after taking the first node it needs.
func _build_something(sim: RunSim) -> SimTower:
	sim.gold = 5000
	sim.tree.points = 5
	for node: StringName in [&"fire_entry", &"water_entry", &"earth_entry"]:
		sim.allocate_node(node)
	for tower_id: StringName in sim.config.towers:
		if not sim.is_unlocked(tower_id):
			continue
		for x in sim.config.map.grid_size.x:
			for y in sim.config.map.grid_size.y:
				var built := sim.place_tower(tower_id, Vector2i(x, y))
				if built != null:
					return built
	fail_test("no tower could be built")
	return null


func test_there_are_ten_slots_and_they_start_empty() -> void:
	assert_eq(SaveSlots.COUNT, 10)
	for slot in range(1, 11):
		assert_false(Progress.has_slot(slot))
	assert_false(Progress.has_slot(0))
	assert_false(Progress.has_slot(11))


func test_a_menu_save_keeps_the_progress_and_loading_brings_it_back() -> void:
	Progress.meta.profile.stage_stars[&"ember_1"] = 3
	assert_eq(Progress.save_to_slot(4), OK)
	var info := Progress.slots.info(4)
	assert_eq(info["kind"], "progress")
	assert_eq(info["stars"], 3)
	assert_gt(int(info["saved_at"]), 0)
	assert_false(SaveSlots.date_text(info["saved_at"]).is_empty())
	# Play on, then go back.
	Progress.meta.profile.stage_stars[&"ember_2"] = 2
	assert_false(Progress.load_from_slot(4), "a progress save has no run to open")
	assert_eq(Progress.meta.profile.stage_stars.get(&"ember_1", 0), 3)
	assert_false(Progress.meta.profile.stage_stars.has(&"ember_2"), "progress after the save is gone")
	assert_true(Progress.pending_run.is_empty())


func test_the_esc_menu_saves_the_run_and_a_load_puts_it_back() -> void:
	await _start_game()
	var tower := _build_something(game.sim)
	var gold := game.sim.gold
	game.open_pause_menu()
	_press(game.pause_menu.save_button)
	assert_true(game.saves_page.visible)
	assert_eq(game.saves_page.mode, &"save")
	_press(game.saves_page.rows[1].action_button)
	assert_true(Progress.has_slot(2))
	var info := Progress.slots.info(2)
	assert_eq(info["kind"], "run")
	assert_eq(info["wave"], 1)
	assert_eq(info["gold"], gold)
	assert_eq(game.saves_page.rows[1].action_button.text, "Overwrite")
	assert_string_contains(game.saves_page.rows[1].detail_label.text, "WAVE 1 OF")

	# A new run from the save.
	assert_true(Progress.load_from_slot(2))
	assert_false(Progress.pending_run.is_empty())
	var loaded: Game = GAME_SCENE.instantiate()
	add_child_autofree(loaded)
	await wait_process_frames(2)
	assert_true(Progress.pending_run.is_empty(), "the run is put back once")
	assert_eq(loaded.sim.gold, gold)
	var back := loaded.sim.tower_at(tower.cell)
	assert_not_null(back, "the tower is back")
	assert_eq(back.data.id, tower.data.id)
	assert_eq(loaded.sim.state, RunSim.State.BUILDING)


func test_a_save_during_a_wave_keeps_the_start_of_the_wave() -> void:
	await _start_game()
	_build_something(game.sim)
	var gold := game.sim.gold
	game._start_wave()
	assert_eq(game.sim.state, RunSim.State.WAVE)
	for i in 120:
		game.sim.step(RunSim.STEP)
	game.sim.gold += 999
	var snapshot := game.run_snapshot()
	assert_eq(RunSnapshot.wave_number(snapshot), 1)
	assert_eq(int(snapshot["gold"]), gold, "the gold the wave began with")
	game.open_saves(&"save")
	assert_string_contains(game.saves_page.note_label.text, "break before wave 1")


func test_overwriting_and_loading_ask_first() -> void:
	await _start_game()
	game.open_saves(&"save")
	var page := game.saves_page
	_press(page.rows[0].action_button)
	assert_true(Progress.has_slot(1))
	assert_false(page.is_asking(), "an empty slot saves at once")
	_press(page.rows[0].action_button)
	assert_true(page.is_asking(), "a full slot asks before it is written over")
	assert_true(page.handle_key(KEY_ESCAPE))
	assert_false(page.is_asking())
	var loads: Array[String] = []
	page.load_confirmed.connect(func(key: String) -> void: loads.append(key))
	page.show_mode(&"load")
	assert_true(page.rows[1].action_button.disabled, "an empty slot cannot be loaded")
	_press(page.rows[0].action_button)
	assert_true(page.is_asking())
	assert_eq(loads, [] as Array[String], "nothing loads before yes")
	page.handle_key(KEY_ENTER)
	assert_eq(loads, ["slot_01"] as Array[String])


func test_esc_closes_the_saves_and_goes_back_to_the_menu() -> void:
	await _start_game()
	game.open_pause_menu()
	game.open_saves(&"load")
	var esc := InputEventKey.new()
	esc.keycode = KEY_ESCAPE
	esc.pressed = true
	get_tree().root.push_input(esc, true)
	assert_false(game.saves_page.visible)
	assert_true(game.pause_menu.visible, "back on the Esc menu")
	assert_true(game.paused)


func test_the_main_menu_lists_the_slots_and_deletes_one() -> void:
	Progress.save_to_slot(3)
	var menu := await _menu()
	assert_eq(menu.buttons[&"saves"].note, "1 saved")
	menu.open_saves(&"load")
	var page := menu.pages[&"saves"] as SavesPage
	assert_true(page.visible)
	assert_eq(page.rows.size(), 10)
	assert_eq(page.rows[2].title_label.text, "Campaign progress")
	assert_eq(page.rows[0].title_label.text, "Empty slot")
	_press(page.rows[2].delete_button)
	assert_true(page.is_asking())
	page.confirm()
	assert_false(Progress.has_slot(3))
	assert_eq(page.rows[2].title_label.text, "Empty slot")


func test_number_keys_pick_slots() -> void:
	await _start_game()
	game.open_saves(&"save")
	var page := game.saves_page
	page.handle_key(KEY_0)
	assert_true(Progress.has_slot(10), "0 is slot 10")
	page.handle_key(KEY_5)
	assert_true(Progress.has_slot(5))


func test_the_title_screen_only_loads() -> void:
	var menu := await _menu()
	menu.open_saves(&"save")
	var page := menu.pages[&"saves"] as SavesPage
	assert_eq(page.mode, &"load", "saving happens in battle, and by itself")
	assert_false(page.save_tab.visible)


func test_a_new_game_is_a_playthrough_of_its_own_and_the_old_one_keeps_its_autosave() -> void:
	Progress.meta.profile.stage_stars[&"ember_1"] = 3
	Progress.select_difficulty(Progress.meta.selected_difficulty)
	Progress.autosave()
	assert_eq(Progress.meta.profile.playthrough_name, "Game 1")
	Progress.new_game()
	assert_eq(Progress.meta.profile.playthrough_id, 2)
	assert_eq(Progress.meta.profile.playthrough_name, "Game 2")
	assert_true(Progress.meta.profile.stage_stars.is_empty(), "a new game starts from nothing")
	assert_eq(Progress.slots.autosave_ids(), [2, 1] as Array[int], "both games have an autosave, newest first")
	assert_false(Progress.load_autosave(1), "Game 1 was between battles")
	assert_eq(Progress.meta.profile.playthrough_id, 1)
	assert_eq(Progress.meta.profile.stage_stars.get(&"ember_1", 0), 3, "Game 1 is back")
	Progress.new_game()
	assert_eq(Progress.meta.profile.playthrough_id, 3, "numbers are never reused")


func test_a_battle_autosaves_at_every_break_and_continue_goes_back_into_it() -> void:
	await _start_game()
	var key := Progress.continue_key()
	assert_eq(key, SaveSlots.auto_key(1), "the battle autosaves as it opens")
	var tower := _build_something(game.sim)
	game._start_wave()
	var t := 0.0
	while game.sim.state == RunSim.State.WAVE and t < 300.0:
		game.sim.step(0.05)
		t += 0.05
	assert_eq(game.sim.state, RunSim.State.BUILDING)
	var info := Progress.slots.info_key(key)
	assert_eq(info["kind"], "run")
	assert_eq(info["wave"], 2, "saved at the break after wave 1")
	var menu := await _menu()
	assert_eq(menu.continue_save, key, "Continue goes back into the battle")
	assert_true(menu.buttons.has(&"continue"))
	assert_true(Progress.load_save(key))
	assert_eq(int(Progress.pending_run["wave_index"]), 1)
	var cells: Array = []
	for entry: Dictionary in Progress.pending_run["towers"]:
		cells.append(entry["cell"])
	assert_has(cells, [tower.cell.x, tower.cell.y])


func test_a_finished_run_leaves_the_autosave_between_battles() -> void:
	await _start_game()
	game.sim.lives = 1
	game.sim._end_run(false)
	var info := Progress.slots.info_key(Progress.continue_key())
	assert_eq(info["kind"], "progress")
