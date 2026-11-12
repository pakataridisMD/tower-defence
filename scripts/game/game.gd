class_name Game
extends Node
## One run of the game. Builds the simulation from the loaded data, steps it at a fixed rate and
## connects the board, the HUD and the skill web.
##
## Command line options, given after `--`:
##   --autoplay     the scripted AutoPlayer plays the run at top speed, for footage and smoke tests.
##   --quit-at-end  quit shortly after the run ends. Used with --autoplay by the CI smoke test.

## Where the board sat before maps could be bigger than the screen. BoardCamera places it now.
const BOARD_OFFSET := Vector2(24, 96)
const SPEEDS: Array[int] = [1, 2, 3]
## Most simulation steps in one frame. A frame that needs more drops the rest, so one slow
## frame cannot snowball into a slower one.
const MAX_STEPS_PER_FRAME := 12
const MENU_SCENE := "res://scenes/main.tscn"
## The skill web's ring threads, drawn as dotted circles behind its nodes (see tools/web/gen_skill_web.py).
const WEB_RING_RADII: Array[float] = [385.0, 640.0, 895.0, 1150.0]
const CAMPAIGN_SCENE := "res://scenes/campaign/campaign_map.tscn"
## Seconds the autoplayer waits at each point of a break, so footage shows the build phase.
const BOT_BREAK := 1.5
const BOT_WEB_OPEN := 0.8
const BOT_WEB_SHOW := 1.2

## Bloom, grade and vignette over the board, under the HUD.
const POST_SHADER := preload("res://assets/shaders/board_post.gdshader")

var sim: RunSim
var board: BoardView
var post_layer: CanvasLayer
## Pans and zooms the board.
var camera: BoardCamera
var hud: Hud
var web: SkillWebView
var story: Story
var story_overlay: StoryOverlay
## The cinematic playing over the run, or null.
var cinematic: CinematicPlayer
var audio: GameAudio
## Boss moves and battle lines.
var bosses: BossDirector
## The army's shouts in the counter-attack.
var army_voice: ArmyVoice
var music: BattleMusic
var paused := false
var audio_panel: AudioPanel
var _paused_before_audio := false
## The Esc menu: resume, save, load, audio, main menu, quit.
var pause_menu: PauseMenu
## Saved games, opened from the Esc menu over it.
var saves_page: SavesPage
## The run as it was in the last break (see RunSnapshot), for a save made during a wave.
var break_snapshot: Dictionary = {}
## Set before the node enters the tree, or with --autoplay.
var autoplay := false
var quit_at_end := false

var _speed_index := 0
var _accumulator := 0.0
var _max_steps := MAX_STEPS_PER_FRAME
var _bot: AutoPlayer
var _bot_wait := BOT_BREAK
var _bot_spent := false
var _cinematic_layer: CanvasLayer
## Cinematics to play once the player leaves the end screen: the stage's own scene and plot beats.
var _story_after: Array[StringName] = []


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	autoplay = autoplay or args.has("--autoplay")
	quit_at_end = quit_at_end or args.has("--quit-at-end")
	sim = RunSim.new(Progress.run_config())
	var loaded := _restore_saved_run()
	story = Story.shared()
	_build_views()
	_build_story()
	_connect_signals()
	if autoplay:
		_bot = AutoPlayer.for_sim(sim)
		_speed_index = SPEEDS.size() - 1
		_max_steps = 600
		hud.speed = SPEEDS[_speed_index]
	if loaded:
		hud.show_message("Game loaded: wave %d. Start the wave when you are ready." % sim.wave_number(), UiStyle.GOLD)


## Puts back a run loaded from a save slot (Progress.pending_run), before the views are built.
func _restore_saved_run() -> bool:
	if Progress.pending_run.is_empty():
		return false
	var run := Progress.pending_run
	Progress.pending_run = {}
	var refund := RunSnapshot.restore(sim, run)
	if refund > 0:
		push_warning("%d gold paid back for towers that no longer fit the map." % refund)
	return refund >= 0


## The run to keep in a save slot: as it is in a break, or as it was at the end of the last break
## (the start of this wave, or of the first of the final assault's waves that roll into each other).
## Empty once the run is over: a save then keeps the campaign progress only.
func run_snapshot() -> Dictionary:
	if sim.is_over():
		return {}
	if sim.state == RunSim.State.BUILDING:
		return RunSnapshot.capture(sim)
	return break_snapshot


## Autosaves the run as it is at the start of a break (and when the battle opens), with the progress.
## Continue on the title screen picks it up from there. The bot's runs keep theirs in memory.
func _autosave() -> void:
	if sim.state != RunSim.State.BUILDING or sim.is_over():
		return
	Progress.autosave_run = RunSnapshot.capture(sim)
	Progress.autosave()


## Keeps the run as it is after every change made in a break, so the last one is at hand once the
## wave has started.
func _remember_break() -> void:
	if sim.state == RunSim.State.BUILDING:
		break_snapshot = RunSnapshot.capture(sim)


func _build_views() -> void:
	board = BoardView.new()
	board.position = BOARD_OFFSET
	board.setup(sim)
	add_child(board)
	camera = BoardCamera.new()
	add_child(camera)
	camera.setup(board, sim.config.map.size_in_pixels())
	board.view_rect = BoardCamera.VIEW_RECT
	if board.art != null:
		BossFx.new().setup(sim, board.art)
	sim.boss_ability.connect(_on_boss_ability)

	audio = GameAudio.new()
	add_child(audio)
	audio.setup(sim, BOARD_OFFSET)
	audio.board = board
	music = BattleMusic.new()
	add_child(music)
	music.setup(sim)
	bosses = BossDirector.new()
	add_child(bosses)
	bosses.setup(sim, board.art)
	army_voice = ArmyVoice.new()
	add_child(army_voice)
	army_voice.setup(sim, board)

	post_layer = CanvasLayer.new()
	post_layer.name = "BoardPost"
	add_child(post_layer)
	var post := ColorRect.new()
	post.position = BoardCamera.VIEW_RECT.position
	post.size = BoardCamera.VIEW_RECT.size
	post.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var post_material := ShaderMaterial.new()
	post_material.shader = POST_SHADER
	post.material = post_material
	post_layer.add_child(post)

	var hud_layer := CanvasLayer.new()
	add_child(hud_layer)
	hud = Hud.new()
	hud_layer.add_child(hud)
	hud.setup(sim)

	var web_layer := CanvasLayer.new()
	web_layer.layer = 2
	add_child(web_layer)
	web = SkillWebView.new()
	web.title = "Skill web"
	var rules := sim.config.rules
	web.subtitle = ("Take nodes to unlock towers and make them stronger. Every wave you clear pays %d points, and " +
		"nodes cost more the further out they are. Click a far node to take the whole way to it. The core nodes of " +
		"two elements unlock their dual tower, and of three their triple. Right-click refunds a node taken in this " +
		"break, from the tip inward.") % rules.tree_points_per_wave
	web.navigable = true
	web.takes_paths = true
	web.ring_radii = WEB_RING_RADII
	web.count_noun = "nodes"
	web.close_text = "Close (T)"
	web.can_refund = sim.can_refund_node
	var whole_web := UiStyle.button("Whole web (F)", 20)
	whole_web.pressed.connect(func() -> void: web.show_whole_tree())
	web.add_header_button(whole_web)
	web.hide()
	web_layer.add_child(web)

	var pause_layer := CanvasLayer.new()
	pause_layer.layer = 3
	add_child(pause_layer)
	pause_menu = PauseMenu.new()
	pause_menu.hide()
	pause_layer.add_child(pause_menu)

	var saves_layer := CanvasLayer.new()
	saves_layer.layer = 3
	add_child(saves_layer)
	# The battle shows only faintly behind the slots.
	var saves_shade := ColorRect.new()
	saves_shade.color = Color(0.03, 0.02, 0.05, 0.82)
	saves_shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	saves_shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	saves_shade.hide()
	saves_layer.add_child(saves_shade)
	saves_page = SavesPage.new()
	saves_page.visibility_changed.connect(func() -> void: saves_shade.visible = saves_page.visible)
	saves_page.theme = UiStyle.menu_theme()
	saves_page.process_mode = Node.PROCESS_MODE_ALWAYS
	saves_page.run_source = run_snapshot
	saves_page.hide()
	saves_layer.add_child(saves_page)

	# Above the pause menu, which opens it.
	var audio_layer := CanvasLayer.new()
	audio_layer.layer = 4
	add_child(audio_layer)
	audio_panel = AudioPanel.new()
	audio_panel.hide()
	audio_panel.closed.connect(_close_audio)
	audio_layer.add_child(audio_panel)


func _connect_signals() -> void:
	hud.start_wave_pressed.connect(_start_wave)
	hud.web_pressed.connect(_toggle_web)
	hud.speed_pressed.connect(_cycle_speed)
	hud.audio_pressed.connect(_open_audio)
	hud.pause_menu_pressed.connect(open_pause_menu)
	pause_menu.resume_requested.connect(close_pause_menu)
	pause_menu.audio_requested.connect(_open_audio)
	pause_menu.leave_requested.connect(_leave_from_menu)
	pause_menu.saves_requested.connect(open_saves)
	saves_page.back_requested.connect(close_saves)
	saves_page.load_confirmed.connect(_load_save)
	sim.changed.connect(_remember_break)
	_remember_break()
	sim.wave_cleared.connect(func(_n: int, _p: int, _g: int) -> void: _autosave())
	_autosave()
	hud.tower_chosen.connect(_choose_tower)
	hud.skill_pressed.connect(_skill_button)
	hud.sell_pressed.connect(_sell_selected)
	hud.level_up_pressed.connect(_level_up_selected)
	hud.ascend_pressed.connect(_ascend_selected)
	hud.hybrid_pressed.connect(_hybrid_selected)
	hud.play_again_pressed.connect(func() -> void: get_tree().reload_current_scene())
	hud.menu_pressed.connect(func() -> void: _leave(MENU_SCENE))
	hud.campaign_pressed.connect(func() -> void: _leave(CAMPAIGN_SCENE))
	hud.next_stage_pressed.connect(_play_next_stage)
	hud.hero_pressed.connect(_hero_button)
	hud.move_pressed.connect(_move_selected)
	hud.muster_pressed.connect(_muster)
	board.hero_aimed.connect(_cast_hero)
	sim.hero_summoned.connect(_on_hero_summoned)
	board.selection_changed.connect(func(tower: SimTower) -> void: hud.selected = tower)
	board.placement_failed.connect(func(reason: String) -> void: hud.show_message(reason, UiStyle.BAD))
	board.skill_aimed.connect(_cast_skill)
	camera.blocked_when = _board_frozen
	web.close_requested.connect(_close_web)
	web.node_clicked.connect(func(id: StringName) -> void: sim.allocate_node(id))
	web.node_refund_requested.connect(func(id: StringName) -> void: sim.refund_node(id))
	sim.run_ended.connect(_on_run_ended)


func _process(delta: float) -> void:
	if _bot != null:
		_drive_bot(delta)
	# A skill can only be aimed while there is a wave to cast it on.
	if not board.aiming.is_empty() and sim.state != RunSim.State.WAVE:
		board.cancel_aiming()
	if not board.aiming_hero.is_empty() and sim.state != RunSim.State.WAVE:
		board.cancel_hero_actions()
	if board.moving != null and sim.state != RunSim.State.BUILDING:
		board.cancel_hero_actions()
	hud.aiming = board.aiming
	hud.aiming_hero = board.aiming_hero
	hud.summoning = board.summoning
	if paused or web.visible or cinematic != null:
		_accumulator = 0.0
		return
	if sim.state == RunSim.State.BUILDING and sim.break_time_left >= 0.0 and _bot == null:
		# In an assault the next wave comes on its own after a short break.
		if sim.tick_break(delta * SPEEDS[_speed_index]):
			_close_web()
	if sim.state != RunSim.State.WAVE:
		_accumulator = 0.0
		return
	_accumulator += delta * SPEEDS[_speed_index]
	var steps := 0
	while _accumulator >= RunSim.STEP:
		if steps >= _max_steps:
			_accumulator = 0.0
			break
		sim.step(RunSim.STEP)
		_accumulator -= RunSim.STEP
		steps += 1


## Tab is handled before the interface sees it, or it would move the keyboard focus instead.
func _input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_TAB and not web.visible \
			and not pause_menu.visible:
		if _mustering():
			SoundPlayer.sfx(&"ui_tab")
			hud.muster.cycle_page()
		else:
			hud.cycle_shop_tier()
		get_viewport().set_input_as_handled()


## Keys: Space starts the wave, T opens the skill web, F changes speed, P pauses, O opens the audio
## settings, M mutes everything, Esc backs out and then opens the pause menu,
## 1-9 pick a tower from the open shop page (Tab turns the page), Q W E A S D cast the skills,
## F1 to F4 summon the heroes and then use their abilities, Z X C V B N press the selected tower's
## upgrade buttons, and Delete sells it.
func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo or cinematic != null or audio_panel.visible:
		return
	if saves_page.visible:
		# Handled first: loading a slot takes the game out of the tree.
		get_viewport().set_input_as_handled()
		if not saves_page.handle_key(key.keycode) and key.keycode in [KEY_ESCAPE, KEY_BACKSPACE]:
			close_saves()
		return
	if pause_menu.visible:
		# Handled first: leaving the run takes the game out of the tree (and away from its viewport).
		get_viewport().set_input_as_handled()
		_pause_menu_key(key.keycode)
		return
	match key.keycode:
		KEY_SPACE:
			_start_wave()
		KEY_O:
			_open_audio()
		KEY_M:
			_toggle_mute()
		KEY_T:
			_toggle_web()
		KEY_F:
			_cycle_speed()
		KEY_P:
			_toggle_pause()
		KEY_ESCAPE:
			_escape()
		KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0:
			if web.visible:
				pass
			elif _mustering():
				_muster(hud.muster.ally_for_hotkey(MusterBar.KEYS.find(key.keycode)))
			elif key.keycode != KEY_0:
				_choose_tower(hud.tower_for_hotkey(key.keycode - KEY_0))
		KEY_R:
			if _mustering():
				hud.muster.cycle_road()
		KEY_DELETE, KEY_BACKSPACE:
			if not web.visible:
				_sell_selected()
		KEY_F1, KEY_F2, KEY_F3, KEY_F4:
			if not web.visible:
				_hero_key(hud.hero_for_hotkey(Hud.HERO_KEYS.find(key.keycode)))
		_:
			var skill := Hud.SKILL_KEYS.find(key.keycode)
			var action := Hud.ACTION_KEYS.find(key.keycode)
			if web.visible or (skill < 0 and action < 0):
				return
			if skill >= 0:
				_skill_key(hud.skill_for_hotkey(skill))
			elif board.selected != null:
				hud.press_action(action)
	get_viewport().set_input_as_handled()


# --- Actions -------------------------------------------------------------------

## True while something covers the board, so the camera leaves it where it is.
func _board_frozen() -> bool:
	return web.visible or pause_menu.visible or saves_page.visible or audio_panel.visible or cinematic != null


func _start_wave() -> void:
	if sim.start_next_wave():
		_close_web()
		paused = false
		hud.paused = false


func _toggle_web() -> void:
	if web.visible:
		_close_web()
	elif not sim.is_over():
		board.cancel_placing()
		board.cancel_aiming()
		board.cancel_hero_actions()
		web.show_tree(sim.tree, SkillWebView.element_regions(sim.config.elements))
		SoundPlayer.sfx(&"ui_open")


func _close_web() -> void:
	if web.visible:
		SoundPlayer.sfx(&"ui_close")
	web.hide()


func _cycle_speed() -> void:
	_speed_index = (_speed_index + 1) % SPEEDS.size()
	hud.speed = SPEEDS[_speed_index]
	SoundPlayer.sfx(&"ui_toggle")


## The audio settings pause the run while they are open.
func _open_audio() -> void:
	if audio_panel.visible:
		return
	_paused_before_audio = paused
	paused = true
	hud.paused = true
	audio_panel.refresh()
	audio_panel.show()


func _close_audio() -> void:
	# Opened from the pause menu, the run keeps waiting until the menu is closed too.
	paused = (_paused_before_audio and not sim.is_over()) or pause_menu.visible
	hud.paused = paused


func _toggle_mute() -> void:
	var muted := AudioSettings.toggle_mute_all()
	hud.show_message("Sound off (M)" if muted else "Sound on", UiStyle.TEXT_DIM if muted else UiStyle.TEXT)


func _toggle_pause() -> void:
	if sim.is_over():
		return
	paused = not paused
	hud.paused = paused
	SoundPlayer.sfx(&"ui_pause" if paused else &"ui_resume")


## Esc backs out of whatever is open: the web, then aiming, placing, the selection, and then
## opens the pause menu.
func _escape() -> void:
	if web.visible:
		_close_web()
	elif board.has_hero_action():
		board.cancel_hero_actions()
	elif not board.aiming.is_empty():
		board.cancel_aiming()
	elif not board.placing.is_empty():
		board.cancel_placing()
	elif board.selected != null:
		board.select(null)
	else:
		open_pause_menu()


# --- Pause menu ----------------------------------------------------------------

## Opens the Esc menu. The run waits while it is open.
func open_pause_menu() -> void:
	if pause_menu.visible:
		return
	board.cancel_placing()
	board.cancel_aiming()
	board.cancel_hero_actions()
	_close_web()
	paused = true
	hud.paused = true
	var stage := sim.config.stage
	var where := stage.display_name if stage != null else sim.config.map.display_name
	pause_menu.open(where, stage != null, sim.is_over())
	SoundPlayer.sfx(&"ui_pause")


## Resume: the run goes on, even if it was paused with P before the menu opened.
func close_pause_menu() -> void:
	if not pause_menu.visible:
		return
	pause_menu.hide()
	paused = false
	hud.paused = false
	SoundPlayer.sfx(&"ui_resume")


## Keys while the menu is open: Esc resumes (or steps back from "Leave the run?"), Enter says yes
## to leaving, O opens the audio settings and M mutes. Every other key waits until the menu closes.
func _pause_menu_key(keycode: Key) -> void:
	match keycode:
		KEY_ESCAPE:
			if pause_menu.is_confirming():
				pause_menu.back()
			else:
				close_pause_menu()
		KEY_ENTER, KEY_KP_ENTER:
			pause_menu.confirm()
		KEY_O:
			if not pause_menu.is_confirming():
				_open_audio()
		KEY_S:
			if not pause_menu.is_confirming():
				open_saves(&"save")
		KEY_L:
			if not pause_menu.is_confirming():
				open_saves(&"load")
		KEY_M:
			_toggle_mute()


## Closing the window (or Cmd+Q on a Mac) during a run opens the pause menu and asks before
## quitting, so a run is never lost to a stray click. The menu then offers Exit to main menu too.
func _notification(what: int) -> void:
	if what != NOTIFICATION_WM_CLOSE_REQUEST or not is_inside_tree():
		return
	if autoplay or pause_menu == null:
		get_tree().quit()
		return
	open_pause_menu()
	pause_menu.ask_to_leave(&"quit")


func _enter_tree() -> void:
	get_tree().set_auto_accept_quit(false)


func _exit_tree() -> void:
	get_tree().set_auto_accept_quit(true)


# --- Saved games -----------------------------------------------------------------

## Opens Saved games over the Esc menu, on its Save or Load tab. The run stays paused.
func open_saves(mode: StringName) -> void:
	if not pause_menu.visible:
		open_pause_menu()
	var wave := RunSnapshot.wave_number(run_snapshot()) if not sim.is_over() else 0
	if sim.is_over():
		saves_page.save_note = "This run is over: a save keeps your campaign progress only."
	elif sim.state == RunSim.State.BUILDING:
		saves_page.save_note = "A save keeps this run as it is now, before wave %d." % wave
	else:
		saves_page.save_note = "A save keeps this run as it was in the break before wave %d." % wave
	saves_page.load_note = "Loading leaves this run and replaces your progress with the saved one."
	saves_page.open(mode)
	SoundPlayer.sfx(&"ui_open")


func close_saves() -> void:
	if not saves_page.visible:
		return
	saves_page.close_dialog()
	saves_page.hide()
	SoundPlayer.sfx(&"ui_close")


## Loads a save the player said yes to (a SaveSlots key): a saved run starts the battle again where
## it was saved, and a save without a run goes to the title screen.
func _load_save(key: String) -> void:
	if not Progress.slots.has_key(key):
		return
	var has_run := Progress.load_save(key)
	if not has_run:
		MainMenu.notice = "Loaded %s." % Progress.meta.profile.playthrough_name
	get_tree().change_scene_to_file(scene_file_path if has_run and not scene_file_path.is_empty() else MENU_SCENE)


func _leave_from_menu(scene: StringName) -> void:
	match scene:
		&"quit":
			get_tree().quit()
		&"campaign":
			_leave(CAMPAIGN_SCENE)
		_:
			_leave(MENU_SCENE)


func _choose_tower(tower_id: StringName) -> void:
	if tower_id.is_empty() or sim.is_over():
		return
	if not sim.is_unlocked(tower_id):
		hud.show_message("Unlock this tower in the skill web first (T)", UiStyle.BAD)
	elif sim.gold < sim.tower_price(tower_id):
		hud.show_message("Not enough gold", UiStyle.BAD)
	else:
		board.begin_placing(tower_id)


## A skill's button: starts aiming it, or stops if it is already being aimed. A skill that needs
## no aiming is cast straight away.
func _skill_button(skill_id: StringName) -> void:
	if board.aiming == skill_id:
		board.cancel_aiming()
	else:
		_begin_skill(skill_id)


## A skill's key: like its button, but pressing it again while aiming casts where the mouse is.
## True while the muster bar of the counter-attack is up: the number keys and Tab muster units then.
func _mustering() -> bool:
	return hud.muster != null and hud.muster.visible


## Sends a squad up the chosen road, or says why it cannot go.
func _muster(ally_id: StringName) -> void:
	if ally_id.is_empty():
		return
	var lane := hud.muster.target_lane()
	var error := sim.muster_error(ally_id, lane)
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
		return
	sim.muster(ally_id, lane)
	SoundPlayer.sfx(&"ui_confirm")


func _skill_key(skill_id: StringName) -> void:
	if skill_id.is_empty():
		return
	if board.aiming == skill_id and board.mouse_inside():
		_cast_skill(skill_id, board.mouse_point())
	else:
		_begin_skill(skill_id)


func _begin_skill(skill_id: StringName) -> void:
	var error := sim.skill_error(skill_id)
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
		return
	var skill: SkillData = sim.config.skills[skill_id]
	if skill.is_targeted():
		board.begin_aiming(skill_id)
		SoundPlayer.sfx(&"skill_aim")
		hud.show_message("%s: click where it should land" % skill.display_name)
	else:
		_cast_skill(skill_id, Vector2.ZERO)


func _cast_skill(skill_id: StringName, at: Vector2) -> void:
	var error := sim.skill_error(skill_id)
	board.cancel_aiming()
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
	elif sim.use_skill(skill_id, at):
		var skill: SkillData = sim.config.skills[skill_id]
		hud.show_message(skill.display_name, sim.config.element_color(skill.element).lightened(0.35))


## A hero's portrait: summons the hero if it is not on the field yet, else uses its ability.
## Clicking it again while placing or aiming stops.
func _hero_button(hero_id: StringName) -> void:
	if board.summoning == hero_id or board.aiming_hero == hero_id:
		board.cancel_hero_actions()
	else:
		_begin_hero(hero_id)


## A hero's key: like its portrait, but pressed again while aiming it casts where the mouse is.
func _hero_key(hero_id: StringName) -> void:
	if hero_id.is_empty():
		return
	if board.aiming_hero == hero_id and board.mouse_inside():
		_cast_hero(hero_id, board.mouse_point())
	elif board.summoning == hero_id:
		board.cancel_hero_actions()
	else:
		_begin_hero(hero_id)


func _begin_hero(hero_id: StringName) -> void:
	if sim.is_over():
		return
	var hero := sim.hero_data(hero_id)
	if hero == null:
		return
	if sim.hero_tower(hero_id) == null:
		board.begin_summoning(hero_id)
		hud.show_message("%s: click a free tile to summon" % hero.display_name)
		return
	var error := sim.hero_ability_error(hero_id)
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
		return
	var ability := sim.hero_tower(hero_id).hero_ability()
	if ability.is_aimed():
		board.begin_hero_aiming(hero_id)
		SoundPlayer.sfx(&"skill_aim")
		hud.show_message("%s: click where it should land" % ability.display_name)
	else:
		_cast_hero(hero_id, Vector2.ZERO)


func _cast_hero(hero_id: StringName, at: Vector2) -> void:
	var error := sim.hero_ability_error(hero_id)
	board.cancel_hero_actions()
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
		return
	var tower := sim.hero_tower(hero_id)
	var ability := tower.hero_ability()
	if sim.use_hero_ability(hero_id, at):
		hud.show_message("%s  ·  %s" % [ability.display_name, _bark(tower.hero)], UiStyle.GOLD)


func _move_selected() -> void:
	var tower := board.selected
	if tower == null or not tower.is_hero():
		return
	var error := sim.move_error(tower, Vector2i(-1, -1)) if sim.state != RunSim.State.BUILDING or tower.moved_this_break else ""
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
		return
	board.begin_moving(tower)
	hud.show_message("%s: click a free tile to march to" % tower.hero.display_name)


## Tells the player when a boss binds or burns down their towers, and lets go of a destroyed one.
func _on_boss_ability(boss: SimEnemy, ability: StringName, targets: Array) -> void:
	match ability:
		&"fireball":
			hud.show_message("%s hurls fire at your %s! Sell it now or lose it." % [boss.data.display_name,
					(targets[0] as SimTower).data.display_name], UiStyle.BAD)
		&"destroy_tower":
			var tower: SimTower = targets[0]
			if board.selected == tower:
				board.select(null)
			hud.show_message("%s destroyed your %s" % [boss.data.display_name, tower.data.display_name], UiStyle.BAD)
		&"bind":
			hud.show_message("%s binds %d of your towers" % [boss.data.display_name, targets.size()], UiStyle.BAD)


func _on_hero_summoned(tower: SimTower) -> void:
	hud.show_message("%s: \"%s\"" % [tower.hero.display_name, _bark(tower.hero)], UiStyle.GOLD)


static func _bark(hero: HeroData) -> String:
	return hero.barks[randi() % hero.barks.size()] if not hero.barks.is_empty() else hero.title


func _sell_selected() -> void:
	var tower := board.selected
	if tower == null:
		return
	if tower.is_hero():
		hud.show_message("Heroes cannot be sold", UiStyle.BAD)
		return
	var refund := sim.sell_tower(tower)
	board.select(null)
	hud.show_message("Sold for %d gold" % refund, UiStyle.GOLD)


func _level_up_selected() -> void:
	var tower := board.selected
	if tower == null:
		return
	var error := sim.level_up_error(tower)
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
	elif sim.level_up(tower):
		hud.show_message("%s reached level %d" % [tower.data.display_name, tower.level], UiStyle.GOOD)


func _ascend_selected(ascendancy_id: StringName) -> void:
	var tower := board.selected
	if tower == null:
		return
	var error := sim.ascend_error(tower, ascendancy_id)
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
	elif sim.ascend(tower, ascendancy_id):
		hud.show_message("%s ascended: %s" % [tower.data.display_name, tower.ascendancy.display_name], UiStyle.GOLD)


func _hybrid_selected(hybrid_id: StringName) -> void:
	var tower := board.selected
	if tower == null:
		return
	var error := sim.hybrid_upgrade_error(tower, hybrid_id)
	if not error.is_empty():
		hud.show_message(error, UiStyle.BAD)
	elif sim.upgrade_to_hybrid(tower, hybrid_id):
		hud.show_message("Became %s" % tower.data.display_name, UiStyle.GOOD)


func _on_run_ended(won: bool) -> void:
	board.cancel_placing()
	board.cancel_aiming()
	board.cancel_hero_actions()
	_close_web()
	var meta_points := Progress.record_run(sim)
	hud.show_end(won, meta_points, Progress.meta.last_run_note)
	if sim.config.stage != null:
		var result := Progress.record_stage(sim)
		var next := Progress.meta.stage_after(sim.config.stage.id)
		hud.show_stage_result(result, next != null and Progress.meta.is_stage_unlocked(next.id))
		_story_after_run(won, result)
		if won:
			audio.play_stars(result.get("stars", 0))
		if autoplay:
			print("Autoplay stage %s: %d stars" % [sim.config.stage.id, result["stars"]])
	if autoplay:
		print("Autoplay run ended: %s after %d of %d waves on %s, %d lives left, %d kills, %d towers, +%d meta points" % [
			"won" if won else "lost", sim.wave_index, sim.total_waves(), sim.config.map.display_name, sim.lives,
			sim.kills, sim.towers.size(), meta_points])
		if Progress.persist:
			print("Progress saved to %s" % ProjectSettings.globalize_path(Progress.save_path))
	if quit_at_end:
		get_tree().create_timer(1.0).timeout.connect(func() -> void: get_tree().quit())


func _play_next_stage() -> void:
	var next := Progress.meta.stage_after(sim.config.stage.id) if sim.config.stage != null else null
	if next != null and Progress.play_stage(next.id):
		var scenes := _story_after.duplicate()
		for id in Progress.meta.story_before_stage(story, next.id):
			if not scenes.has(id):
				scenes.append(id)
		_story_after.clear()
		Progress.play_story(get_tree(), scenes, scene_file_path)
	else:
		_leave(CAMPAIGN_SCENE)


## Leaves the run for another screen, first playing the story the run unlocked.
func _leave(scene: String) -> void:
	var scenes := _story_after.duplicate()
	_story_after.clear()
	if autoplay:
		scenes.clear()
	Progress.play_story(get_tree(), scenes, scene)


# --- Story ---------------------------------------------------------------------

func _build_story() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 1
	add_child(layer)
	story_overlay = StoryOverlay.new()
	layer.add_child(story_overlay)
	story_overlay.setup(sim, story)
	_cinematic_layer = CanvasLayer.new()
	_cinematic_layer.layer = 5
	add_child(_cinematic_layer)
	sim.wave_started.connect(_on_wave_started_story)
	sim.phase_changed.connect(_on_phase_changed_story)
	var stage := sim.config.stage
	if stage != null and board.art != null and not stage.is_assault():
		# After the midpoint the lands are fought in the Long Night.
		var land := sim.config.campaign != null and not sim.config.campaign.element.is_empty()
		if land and story.night_from_stages_won > 0 and Progress.meta.stages_won() >= story.night_from_stages_won:
			board.art.light_override = DayNight.NIGHT
			board.art.day_night.set_target(DayNight.NIGHT)
			board.art.day_night.snap()


## Plays cinematics over the run, which waits until they are done. The bot skips them.
func play_cinematics(ids: Array[StringName]) -> void:
	if ids.is_empty() or autoplay:
		for id in ids:
			Progress.mark_seen(id)
		return
	if cinematic != null:
		cinematic.queue.append_array(ids)
		return
	board.cancel_placing()
	board.cancel_aiming()
	_close_web()
	cinematic = CinematicPlayer.new()
	cinematic.change_scene_when_done = false
	cinematic.story = story
	cinematic.queue = ids.duplicate()
	# The battle music holds while the story's own music plays.
	if music != null and music.player != null:
		music.player.stream_paused = true
	cinematic.finished.connect(func() -> void:
		cinematic.queue_free()
		cinematic = null
		if music != null and music.player != null:
			music.player.stream_paused = false)
	_cinematic_layer.add_child(cinematic)


func _on_wave_started_story(number: int) -> void:
	var stage := sim.config.stage
	if stage == null:
		return
	var id := story.scene_at_wave(stage.id, number)
	if id.is_empty():
		return
	# A scene in the middle of a stage turns the night: in the siege of Solenne, the dawn comes.
	if board.art != null:
		board.art.light_override = DayNight.DAWN
	if not Progress.meta.has_seen(id):
		play_cinematics([id])


func _on_phase_changed_story(phase: int) -> void:
	var movement := story.assault_movement(phase)
	var id := StringName(str(movement.get("cinematic", "")))
	if not id.is_empty() and story.has_cinematic(id):
		play_cinematics([id])


## After a stage: the city it cost (or saved), and which cinematics come next.
func _story_after_run(won: bool, result: Dictionary) -> void:
	var stage := sim.config.stage
	var city := story.city(stage.id)
	if won:
		if not city.is_empty():
			var saved: bool = city.get("saved", false)
			var line := str(city.get("fall_text", ""))
			hud.show_story_note(("%s is saved. %s" if saved else "%s has fallen. %s") % [city.get("name", ""), line])
		_story_after = Progress.meta.story_after_stage(story, stage.id)
		if not _story_after.is_empty():
			hud.show_story_note("[color=#%s]The story continues when you leave this screen.[/color]" % UiStyle.GOLD.to_html(false))
	else:
		var lost := story.lost_scene(stage.id)
		if not lost.is_empty():
			play_cinematics([lost])


# --- Autoplay ------------------------------------------------------------------

## Plays each break like a person would: open the web, take nodes, close it, build, start. During
## a wave it casts the skills.
func _drive_bot(delta: float) -> void:
	if sim.state != RunSim.State.BUILDING:
		_bot_wait = BOT_BREAK
		if not paused and not web.visible:
			_bot.use_skills()
			_bot.play_wave_step()
		return
	_bot_wait -= delta
	if _bot_wait > 0.0:
		return
	if web.visible:
		if not _bot_spent:
			_bot.spend_points()
			_bot_spent = true
			_bot_wait = BOT_WEB_SHOW
		else:
			_close_web()
			_bot_wait = 0.3
		return
	if sim.tree.points > 0 and not _bot_spent:
		_toggle_web()
		_bot_wait = BOT_WEB_OPEN
		return
	_bot.build_towers()
	_bot_spent = false
	_start_wave()
