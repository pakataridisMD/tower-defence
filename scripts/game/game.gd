class_name Game
extends Node
## One run of the game. Builds the simulation from the loaded data, steps it at a fixed rate and
## connects the board, the HUD and the skill web.
##
## Command line options, given after `--`:
##   --autoplay     the scripted AutoPlayer plays the run at top speed, for footage and smoke tests.
##   --quit-at-end  quit shortly after the run ends. Used with --autoplay by the CI smoke test.

const BOARD_OFFSET := Vector2(24, 96)
const SPEEDS: Array[int] = [1, 2, 3]
## Most simulation steps in one frame. A frame that needs more drops the rest, so one slow
## frame cannot snowball into a slower one.
const MAX_STEPS_PER_FRAME := 12
const MENU_SCENE := "res://scenes/main.tscn"
const CAMPAIGN_SCENE := "res://scenes/campaign/campaign_map.tscn"
## Seconds the autoplayer waits at each point of a break, so footage shows the build phase.
const BOT_BREAK := 1.5
const BOT_WEB_OPEN := 0.8
const BOT_WEB_SHOW := 1.2

var sim: RunSim
var board: BoardView
var hud: Hud
var web: SkillWebView
var audio: GameAudio
var music: BattleMusic
var paused := false
## Set before the node enters the tree, or with --autoplay.
var autoplay := false
var quit_at_end := false

var _speed_index := 0
var _accumulator := 0.0
var _max_steps := MAX_STEPS_PER_FRAME
var _bot: AutoPlayer
var _bot_wait := BOT_BREAK
var _bot_spent := false


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	autoplay = autoplay or args.has("--autoplay")
	quit_at_end = quit_at_end or args.has("--quit-at-end")
	sim = RunSim.new(Progress.run_config())
	_build_views()
	_connect_signals()
	if autoplay:
		_bot = AutoPlayer.for_sim(sim)
		_speed_index = SPEEDS.size() - 1
		_max_steps = 600
		hud.speed = SPEEDS[_speed_index]


func _build_views() -> void:
	board = BoardView.new()
	board.position = BOARD_OFFSET
	board.setup(sim)
	add_child(board)

	audio = GameAudio.new()
	add_child(audio)
	audio.setup(sim, BOARD_OFFSET)
	music = BattleMusic.new()
	add_child(music)
	music.setup(sim)

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
	web.subtitle = "Take nodes to unlock towers and make them stronger. You earn a point for every wave you clear. " + \
		"The core nodes of two elements unlock their dual tower, and of three their triple. " + \
		"Right-click refunds a node taken in this break, until you start the next wave."
	web.can_refund = sim.can_refund_node
	web.hide()
	web_layer.add_child(web)


func _connect_signals() -> void:
	hud.start_wave_pressed.connect(_start_wave)
	hud.web_pressed.connect(_toggle_web)
	hud.speed_pressed.connect(_cycle_speed)
	hud.tower_chosen.connect(_choose_tower)
	hud.skill_pressed.connect(_skill_button)
	hud.sell_pressed.connect(_sell_selected)
	hud.level_up_pressed.connect(_level_up_selected)
	hud.ascend_pressed.connect(_ascend_selected)
	hud.hybrid_pressed.connect(_hybrid_selected)
	hud.play_again_pressed.connect(func() -> void: get_tree().reload_current_scene())
	hud.menu_pressed.connect(func() -> void: get_tree().change_scene_to_file(MENU_SCENE))
	hud.campaign_pressed.connect(func() -> void: get_tree().change_scene_to_file(CAMPAIGN_SCENE))
	hud.next_stage_pressed.connect(_play_next_stage)
	hud.hero_pressed.connect(_hero_button)
	hud.move_pressed.connect(_move_selected)
	board.hero_aimed.connect(_cast_hero)
	sim.hero_summoned.connect(_on_hero_summoned)
	board.selection_changed.connect(func(tower: SimTower) -> void: hud.selected = tower)
	board.placement_failed.connect(func(reason: String) -> void: hud.show_message(reason, UiStyle.BAD))
	board.skill_aimed.connect(_cast_skill)
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
	if paused or web.visible or sim.state != RunSim.State.WAVE:
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
	if key != null and key.pressed and not key.echo and key.keycode == KEY_TAB and not web.visible:
		hud.cycle_shop_tier()
		get_viewport().set_input_as_handled()


## Keys: Space starts the wave, T opens the skill web, F changes speed, P pauses, Esc backs out,
## 1-9 pick a tower from the open shop page (Tab turns the page), Q W E A S D cast the skills,
## F1 to F4 summon the heroes and then use their abilities, Z X C V B N press the selected tower's
## upgrade buttons, and Delete sells it.
func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_SPACE:
			_start_wave()
		KEY_T:
			_toggle_web()
		KEY_F:
			_cycle_speed()
		KEY_P:
			_toggle_pause()
		KEY_ESCAPE:
			_escape()
		KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9:
			if not web.visible:
				_choose_tower(hud.tower_for_hotkey(key.keycode - KEY_0))
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


func _toggle_pause() -> void:
	if sim.is_over():
		return
	paused = not paused
	hud.paused = paused
	SoundPlayer.sfx(&"ui_pause" if paused else &"ui_resume")


## Esc backs out of whatever is open: the web, then aiming, placing, the selection, then pause.
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
		_toggle_pause()


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
	hud.show_end(won, meta_points)
	if sim.config.stage != null:
		var result := Progress.record_stage(sim)
		var next := Progress.meta.stage_after(sim.config.stage.id)
		hud.show_stage_result(result, next != null and Progress.meta.is_stage_unlocked(next.id))
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
		get_tree().reload_current_scene()
	else:
		get_tree().change_scene_to_file(CAMPAIGN_SCENE)


# --- Autoplay ------------------------------------------------------------------

## Plays each break like a person would: open the web, take nodes, close it, build, start. During
## a wave it casts the skills.
func _drive_bot(delta: float) -> void:
	if sim.state != RunSim.State.BUILDING:
		_bot_wait = BOT_BREAK
		if not paused and not web.visible:
			_bot.use_skills()
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
