class_name Hud
extends Control
## The run's interface: top bar, tower shop, selected tower panel, messages and the end screen.
## It reads the simulation every frame and reports button presses through signals.

signal start_wave_pressed
signal web_pressed
signal speed_pressed
signal audio_pressed
## The Menu button: opens the pause menu (also Esc).
signal pause_menu_pressed
signal tower_chosen(tower_id: StringName)
signal skill_pressed(skill_id: StringName)
## The player wants the skill's next level (its small button under it, or Shift and its key).
signal skill_upgrade_pressed(skill_id: StringName)
signal sell_pressed
signal level_up_pressed
signal ascend_pressed(ascendancy_id: StringName)
signal hybrid_pressed(hybrid_id: StringName)
signal play_again_pressed
signal menu_pressed
signal campaign_pressed
signal next_stage_pressed
## A hero's portrait was clicked: summon it, or use its ability.
signal hero_pressed(hero_id: StringName)
## The selected hero's Move button.
signal move_pressed
## A unit picked in the muster bar of the counter-attack.
signal muster_pressed(ally_id: StringName)

const TOP_BAR_HEIGHT := 72.0
const SIDE_PANEL_X := 1584.0
const SIDE_PANEL_SIZE := Vector2(324, 960)
## Tallest the shop grid gets before it scrolls.
const SHOP_MAX_HEIGHT := 292.0
const SHOP_COLUMNS := 4
const SHOP_BUTTON_WIDTH := 68.0
## Keys for the skills, laid out on the panel as they are on the keyboard: Q W E over A S D.
const SKILL_KEYS: Array[Key] = [KEY_Q, KEY_W, KEY_E, KEY_A, KEY_S, KEY_D]
## Keys for the selected tower's upgrade buttons, top to bottom.
const ACTION_KEYS: Array[Key] = [KEY_Z, KEY_X, KEY_C, KEY_V, KEY_B, KEY_N]
## Keys for the heroes in the party, in order. The fourth is for a hero who arrives mid-run.
const HERO_KEYS: Array[Key] = [KEY_F1, KEY_F2, KEY_F3, KEY_F4]
const HERO_BUTTON_SIZE := Vector2(54, 56)

var sim: RunSim
var speed := 1
var paused := false
var selected: SimTower
## The skill the player is aiming on the board, or empty. Set by the game.
var aiming: StringName = &""
## The hero being summoned, or whose ability is being aimed. Set by the game.
var summoning: StringName = &""
var aiming_hero: StringName = &""

var _hero_row: HBoxContainer
var _hero_buttons: Dictionary[StringName, KeyButton] = {}

var _top_bar: PanelContainer
var _side_panel: PanelContainer
var _gold: Label
var _lives: Label
var _wave: Label
var _stage: Label
var _next: RichTextLabel
var _web_button: Button
var _speed_button: Button
var _wave_button: Button
var _tower_buttons: Dictionary[StringName, KeyButton] = {}
## Tower ids in the order the shop shows them.
var _shop_ids: Array[StringName] = []
## Which shop tab is open: 1 for base towers, 2 for duals, 3 for triples.
var _shop_tier := 1
var _tier_tabs: Dictionary[int, Button] = {}
var _shop_scroll: ScrollContainer
var _shop_grid: GridContainer
var _skill_buttons: Dictionary[StringName, KeyButton] = {}
## The small level-up button under each skill.
var _skill_upgrades: Dictionary[StringName, Button] = {}
## Skill ids in the order of their keys.
var _skill_ids: Array[StringName] = []
var _info: RichTextLabel
var _sell_button: Button
## Level, ascendancy and hybrid buttons for the selected tower, rebuilt when the choices change.
var _actions: VBoxContainer
var _actions_key := ""
var _message: Label
## "Next wave in 12 s" over the board while a break counts down to a wave that starts on its own.
var _countdown: Label
var _message_time := 0.0
var _menu_button: Button
var _end_panel: PanelContainer
var _end_title: Label
var _end_stats: Label
var _end_meta: Label
var _end_stage: RichTextLabel
var _campaign_button: Button
var _next_stage_button: Button
## The muster bar of the final assault's counter-attack, or null in any other stage.
var muster: MusterBar


func setup(p_sim: RunSim) -> void:
	sim = p_sim
	theme = UiStyle.hud_theme()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_top_bar()
	_build_side_panel()
	_build_message()
	_build_muster()
	_build_end_panel()
	# Everything in the HUD, and whatever it adds later (hero buttons, choices), uses the pixel fonts.
	UiStyle.pixel_fonts(self)
	get_tree().node_added.connect(_on_node_added)
	sim.wave_cleared.connect(_on_wave_cleared)
	sim.wave_started.connect(_announce_wave)


func _on_node_added(node: Node) -> void:
	if node is Control and is_ancestor_of(node):
		UiStyle.pixel_fonts.call_deferred(node)


## "Wave 7", and on a second line how it comes: "Runner packs, a flank attack and a closing surge."
func _announce_wave(number: int) -> void:
	var wave := sim.current_wave()
	var text := "Wave %d" % number
	if wave != null and not wave.description.is_empty():
		text += "\n" + wave.description
	# Every tenth wave of an endless run says how strong the horde has grown.
	if sim.is_endless() and number > 1 and number % 10 == 0:
		text += "\nThe horde has grown: %d%% numbers, %d%% health" % [
			roundi(sim.endless_multiplier() * 100.0), roundi(sim.endless_multiplier() * 100.0)]
	show_message(text)
	_message_time = 4.0


## Shows how long the break has left before the next wave starts on its own.
func _refresh_countdown() -> void:
	var counting := sim.state == RunSim.State.BUILDING and sim.break_time_left >= 0.0
	_countdown.visible = counting
	if not counting:
		return
	var seconds := ceili(sim.break_time_left)
	if paused:
		_countdown.text = "Next wave in %d s  (paused)" % seconds
	else:
		_countdown.text = "Next wave in %d s  -  Space to start now" % seconds
	_countdown.add_theme_color_override("font_color", UiStyle.GOLD if seconds <= 5 else UiStyle.TEXT)


func show_message(text: String, color: Color = UiStyle.TEXT) -> void:
	if color == UiStyle.BAD:
		SoundPlayer.sfx(&"ui_error")
	_message.text = text
	_message.add_theme_color_override("font_color", color)
	_message_time = 2.2


func _process(delta: float) -> void:
	if sim == null:
		return
	_message_time = maxf(0.0, _message_time - delta)
	_message.modulate.a = clampf(_message_time / 0.5, 0.0, 1.0)
	_refresh()


# --- Layout --------------------------------------------------------------------

func _build_top_bar() -> void:
	var bar := PanelContainer.new()
	bar.theme_type_variation = &"SlimPanel"
	bar.position = Vector2(12, 8)
	bar.size = Vector2(1896, TOP_BAR_HEIGHT)
	add_child(bar)
	_top_bar = bar
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	bar.add_child(row)
	# Every item has a set width, so a long wave description can never push the buttons off the screen.
	_gold = _stat(row, &"coin", UiStyle.GOLD, 78, "Gold")
	_lives = _stat(row, &"heart", UiStyle.LIFE, 54, "Lives")
	_wave = _fixed_label(row, 24, UiStyle.TEXT, 140)
	_stage = _fixed_label(row, 18, UiStyle.TEXT_DIM, 200 if sim.party.is_empty() else 120)
	_hero_row = HBoxContainer.new()
	_hero_row.add_theme_constant_override("separation", 4)
	row.add_child(_hero_row)
	for hero in sim.party:
		_add_hero_button(hero)
	sim.hero_arrived.connect(_on_hero_arrived)
	_next = RichTextLabel.new()
	_next.bbcode_enabled = true
	_next.scroll_active = false
	_next.autowrap_mode = TextServer.AUTOWRAP_OFF
	_next.custom_minimum_size = Vector2(200, 52)
	_next.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_next.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_next.add_theme_font_size_override("normal_font_size", 17)
	_next.add_theme_font_size_override("bold_font_size", 17)
	row.add_child(_next)
	_web_button = _bar_button(row, 268)
	_web_button.pressed.connect(func() -> void: web_pressed.emit())
	_speed_button = _bar_button(row, 140)
	_speed_button.pressed.connect(func() -> void: speed_pressed.emit())
	var audio_button := _bar_button(row, 112)
	audio_button.text = "Audio (O)"
	audio_button.tooltip_text = "Volume and mute for music, effects, interface and voices. M mutes everything."
	audio_button.pressed.connect(func() -> void: audio_pressed.emit())
	_wave_button = _bar_button(row, 206)
	_wave_button.pressed.connect(func() -> void: start_wave_pressed.emit())
	_menu_button = _bar_button(row, 118)
	_menu_button.text = "Menu (Esc)"
	_menu_button.tooltip_text = "Pause the run: resume, exit to the main menu, audio settings, or quit to the desktop."
	_menu_button.pressed.connect(func() -> void: pause_menu_pressed.emit())


## A number in the top bar with its icon in front, such as the gold.
func _stat(row: HBoxContainer, icon_name: StringName, color: Color, width: float, hint: String) -> Label:
	var pair := HBoxContainer.new()
	pair.add_theme_constant_override("separation", 6)
	pair.tooltip_text = hint
	row.add_child(pair)
	var icon := TextureRect.new()
	icon.texture = TreeArt.icon(icon_name)
	icon.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	icon.custom_minimum_size = Vector2(28, 28)
	icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pair.add_child(icon)
	var label := UiStyle.label("", 26, color)
	label.custom_minimum_size = Vector2(width, 0)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.clip_text = true
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	pair.add_child(label)
	return label


func _fixed_label(row: HBoxContainer, font_size: int, color: Color, width: float) -> Label:
	var label := UiStyle.label("", font_size, color)
	label.custom_minimum_size = Vector2(width, 0)
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.clip_text = true
	label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	label.mouse_filter = Control.MOUSE_FILTER_PASS
	row.add_child(label)
	return label


func _bar_button(row: HBoxContainer, width: float) -> Button:
	var button := UiStyle.button("", 24)
	button.custom_minimum_size = Vector2(width, 0)
	button.clip_text = true
	row.add_child(button)
	return button


func _build_side_panel() -> void:
	var panel := PanelContainer.new()
	panel.theme_type_variation = &"SlimPanel"
	panel.position = Vector2(SIDE_PANEL_X, 96)
	panel.size = SIDE_PANEL_SIZE
	panel.clip_contents = true
	add_child(panel)
	_side_panel = panel
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 7)
	panel.add_child(column)
	column.add_child(_heading("Towers", "1-9 pick  ·  Tab next page"))
	# Tabs for base towers, duals and triples; hybrids only show once they are unlocked.
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 5)
	column.add_child(tabs)
	for tier in [1, 2, 3]:
		var tab := UiStyle.key_button("", 15)
		tab.toggle_mode = true
		tab.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		tab.custom_minimum_size = Vector2(0, 30)
		tab.clip_text = true
		# The open tab wears the gold frame.
		tab.add_theme_stylebox_override("pressed", UiStyle.menu_button_box("picked", 5, 4))
		tab.add_theme_stylebox_override("hover_pressed", UiStyle.menu_button_box("picked", 5, 4))
		tab.pressed.connect(show_shop_tier.bind(tier))
		tabs.add_child(tab)
		_tier_tabs[tier] = tab
	# A grid of tower pictures. Names and details are in the tooltips.
	_shop_scroll = ScrollContainer.new()
	_shop_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(_shop_scroll)
	var grid := GridContainer.new()
	grid.columns = SHOP_COLUMNS
	grid.add_theme_constant_override("h_separation", 5)
	grid.add_theme_constant_override("v_separation", 5)
	_shop_scroll.add_child(grid)
	_shop_grid = grid
	_shop_ids = _shop_order()
	# Every button is as tall as the tallest tower, so the towers stand on one line.
	var tallest := 0
	for tower_id in _shop_ids:
		var art := BoardArt.tower_picture(tower_id)
		if art != null:
			tallest = maxi(tallest, art.get_height())
	for tower_id in _shop_ids:
		var data: TowerData = sim.config.towers[tower_id]
		var colors: Array[Color] = []
		for element_id in data.elements:
			colors.append(sim.config.element_color(element_id))
		var button := UiStyle.key_button("", 15)
		button.icon = UiStyle.element_icon(colors)
		button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		button.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		button.custom_minimum_size = Vector2(SHOP_BUTTON_WIDTH, 60)
		var picture := BoardArt.tower_picture(tower_id)
		if picture != null:
			# The tower's own pixel art, at one screen pixel per art pixel.
			var gap := float(tallest - picture.get_height())
			var padded := AtlasTexture.new()
			padded.atlas = picture
			padded.region = Rect2(Vector2.ZERO, picture.get_size())
			padded.margin = Rect2(0, gap, 0, gap)
			button.icon = padded
			button.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			button.custom_minimum_size = Vector2(SHOP_BUTTON_WIDTH, tallest + 24)
		button.clip_text = true
		button.pressed.connect(func() -> void: tower_chosen.emit(tower_id))
		grid.add_child(button)
		_tower_buttons[tower_id] = button
	column.add_child(HSeparator.new())
	_build_skills(column)
	column.add_child(HSeparator.new())
	# The selected tower, or the help text. It scrolls when a tower has a lot to say.
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(scroll)
	var details := VBoxContainer.new()
	details.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	details.add_theme_constant_override("separation", 6)
	scroll.add_child(details)
	_info = RichTextLabel.new()
	_info.bbcode_enabled = true
	_info.fit_content = true
	_info.scroll_active = false
	_info.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_info.add_theme_font_size_override("normal_font_size", 16)
	_info.add_theme_font_size_override("bold_font_size", 19)
	_info.add_theme_font_size_override("italics_font_size", 16)
	details.add_child(_info)
	_actions = VBoxContainer.new()
	_actions.add_theme_constant_override("separation", 5)
	details.add_child(_actions)
	_sell_button = UiStyle.key_button("", 18)
	_sell_button.custom_minimum_size = Vector2(0, 38)
	_sell_button.pressed.connect(func() -> void: sell_pressed.emit())
	column.add_child(_sell_button)


## A section title with a dim note beside it, such as the keys that work there.
func _heading(title: String, note: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_child(UiStyle.menu_title(title, 32))
	var hint := UiStyle.label(note, 14, UiStyle.TEXT_DIM)
	hint.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	hint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	hint.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	hint.clip_text = true
	row.add_child(hint)
	return row


## One button per skill, three to a row like their keys.
func _build_skills(column: VBoxContainer) -> void:
	var skills := sim.skill_list()
	if skills.is_empty():
		return
	column.add_child(_heading("Skills", "Shift+key levels up"))
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 5)
	grid.add_theme_constant_override("v_separation", 5)
	column.add_child(grid)
	for skill in skills:
		var skill_id := skill.id
		var button := UiStyle.key_button(skill.display_name, 14)
		button.icon = UiStyle.art("skill_" + String(skill_id))
		button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		button.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		button.custom_minimum_size = Vector2(97, 62)
		button.clip_text = true
		if _skill_ids.size() < SKILL_KEYS.size():
			button.key_text = OS.get_keycode_string(SKILL_KEYS[_skill_ids.size()])
		button.pressed.connect(func() -> void: skill_pressed.emit(skill_id))
		var cell := VBoxContainer.new()
		cell.add_theme_constant_override("separation", 2)
		cell.add_child(button)
		var upgrade := UiStyle.button("", 13)
		upgrade.theme_type_variation = &"CompactButton"
		upgrade.custom_minimum_size = Vector2(97, 22)
		upgrade.clip_text = true
		upgrade.pressed.connect(func() -> void: skill_upgrade_pressed.emit(skill_id))
		cell.add_child(upgrade)
		grid.add_child(cell)
		_skill_buttons[skill_id] = button
		_skill_upgrades[skill_id] = upgrade
		_skill_ids.append(skill_id)


func _build_muster() -> void:
	if not sim.is_counter_assault() or sim.config.allies.is_empty():
		return
	muster = MusterBar.new()
	muster.setup(sim)
	muster.position = Vector2(24, 912)
	muster.size = Vector2(1536, 144)
	muster.muster_pressed.connect(func(ally_id: StringName) -> void: muster_pressed.emit(ally_id))
	add_child(muster)


func _build_message() -> void:
	_message = UiStyle.label("", 30)
	_message.add_theme_color_override("font_outline_color", UiStyle.MENU_INK)
	_message.add_theme_constant_override("outline_size", 8)
	_message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_message.position = Vector2(24, 108)
	_message.size = Vector2(1536, 90)
	_message.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_message)
	_countdown = UiStyle.label("", 26)
	_countdown.add_theme_color_override("font_outline_color", UiStyle.MENU_INK)
	_countdown.add_theme_constant_override("outline_size", 8)
	_countdown.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_countdown.position = Vector2(24, 196)
	_countdown.size = Vector2(1536, 40)
	_countdown.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_countdown.hide()
	add_child(_countdown)


func _build_end_panel() -> void:
	_end_panel = PanelContainer.new()
	_end_panel.position = Vector2(500, 230)
	_end_panel.size = Vector2(680, 440)
	_end_panel.hide()
	add_child(_end_panel)
	var column := VBoxContainer.new()
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_theme_constant_override("separation", 18)
	_end_panel.add_child(column)
	_end_title = UiStyle.label("", 48)
	_end_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_end_title)
	_end_stats = UiStyle.label("", 22, UiStyle.TEXT_DIM)
	_end_stats.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_end_stats)
	_end_meta = UiStyle.label("", 22, UiStyle.GOLD)
	_end_meta.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_end_meta.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_end_meta.custom_minimum_size = Vector2(500, 0)
	column.add_child(_end_meta)
	_end_stage = RichTextLabel.new()
	_end_stage.bbcode_enabled = true
	_end_stage.fit_content = true
	_end_stage.scroll_active = false
	_end_stage.custom_minimum_size = Vector2(540, 0)
	_end_stage.add_theme_font_size_override("normal_font_size", 22)
	_end_stage.add_theme_font_size_override("bold_font_size", 26)
	_end_stage.hide()
	column.add_child(_end_stage)
	var buttons := HBoxContainer.new()
	buttons.alignment = BoxContainer.ALIGNMENT_CENTER
	buttons.add_theme_constant_override("separation", 16)
	column.add_child(buttons)
	var again := UiStyle.button("Play again", 22)
	again.pressed.connect(func() -> void: play_again_pressed.emit())
	var menu := UiStyle.button("Main menu", 22)
	menu.pressed.connect(func() -> void: menu_pressed.emit())
	buttons.add_child(again)
	_next_stage_button = UiStyle.button("Next stage", 22)
	_next_stage_button.pressed.connect(func() -> void: next_stage_pressed.emit())
	_next_stage_button.hide()
	buttons.add_child(_next_stage_button)
	_campaign_button = UiStyle.button("Campaign map", 22)
	_campaign_button.pressed.connect(func() -> void: campaign_pressed.emit())
	_campaign_button.hide()
	buttons.add_child(_campaign_button)
	buttons.add_child(menu)


## Opens a shop tab: 1 for base towers, 2 for duals, 3 for triples.
func show_shop_tier(tier: int) -> void:
	_shop_tier = clampi(tier, 1, 3)
	_shop_scroll.scroll_vertical = 0


## Opens the next shop tab that has a tower in it, wrapping round to the base towers.
func cycle_shop_tier() -> void:
	SoundPlayer.sfx(&"ui_tab")
	for step in [1, 2, 3]:
		var tier: int = (_shop_tier - 1 + step) % 3 + 1
		for tower_id in _shop_ids:
			var data: TowerData = sim.config.towers[tower_id]
			if data.elements.size() == tier and (tier == 1 or sim.is_unlocked(tower_id)):
				show_shop_tier(tier)
				return


func shop_tier() -> int:
	return _shop_tier


## Base towers first in ring order, then the long-range towers, then duals, then triples.
func _shop_order() -> Array[StringName]:
	var ids: Array[StringName] = []
	ids.assign(sim.config.towers.keys())
	var rank := func(id: StringName) -> int:
		var data: TowerData = sim.config.towers[id]
		var indices: Array[int] = []
		for element_id in data.elements:
			indices.append(sim.config.element_index(element_id))
		indices.sort()
		var weights: Array[int] = [100, 10, 1]
		var value := data.elements.size() * 1000
		if data.is_longshot():
			value += 600
		for i in indices.size():
			value += indices[i] * weights[i]
		return value
	ids.sort_custom(func(a: StringName, b: StringName) -> bool: return rank.call(a) < rank.call(b))
	return ids


## True for towers on the open shop tab. Hybrids stay out of the shop until they are unlocked, so
## the panel only grows as the run does.
func _in_open_tab(tower_id: StringName) -> bool:
	var data: TowerData = sim.config.towers[tower_id]
	return data.elements.size() == _shop_tier and (not data.is_hybrid() or sim.is_unlocked(tower_id))


## The tower a number key picks: the n-th one on the open tab, counted from 1.
func tower_for_hotkey(number: int) -> StringName:
	var count := 0
	for tower_id in _shop_ids:
		if _in_open_tab(tower_id):
			count += 1
			if count == number:
				return tower_id
	return &""


## The level-up button under a skill, for tests and screenshots.
func skill_upgrade_button(skill_id: StringName) -> Button:
	return _skill_upgrades.get(skill_id)


## The skill on the n-th skill key, counted from 0, or an empty id.
func skill_for_hotkey(index: int) -> StringName:
	return _skill_ids[index] if index >= 0 and index < _skill_ids.size() else &""


## Presses the n-th upgrade button of the selected tower, counted from 0, as its key does. A
## button that cannot be paid for still reports the press, so the game can say why.
func press_action(index: int) -> bool:
	if index < 0 or index >= _actions.get_child_count():
		return false
	var button := _actions.get_child(index)
	_on_action_pressed(button.get_meta(&"action"), button.get_meta(&"id"))
	return true


# --- Heroes --------------------------------------------------------------------

## A hero's portrait in the top bar: its key, its level and its ability's cooldown.
func _add_hero_button(hero: HeroData) -> void:
	var hero_id := hero.id
	var button := UiStyle.key_button("", 14)
	button.icon = hero_portrait(hero_id)
	button.expand_icon = true
	button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	button.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	button.custom_minimum_size = HERO_BUTTON_SIZE
	var index := _hero_buttons.size()
	if index < HERO_KEYS.size():
		button.key_text = OS.get_keycode_string(HERO_KEYS[index])
	button.pressed.connect(func() -> void: hero_pressed.emit(hero_id))
	_hero_row.add_child(button)
	_hero_buttons[hero_id] = button


## The hero in a party slot, counted from 0, or an empty id.
func hero_for_hotkey(index: int) -> StringName:
	return sim.party[index].id if index >= 0 and index < sim.party.size() else &""


static func hero_portrait(hero_id: StringName) -> Texture2D:
	var path := "res://assets/art/heroes/portraits/%s.png" % hero_id
	return load(path) if ResourceLoader.exists(path) else null


func _on_hero_arrived(hero: HeroData) -> void:
	_add_hero_button(hero)
	var key := OS.get_keycode_string(HERO_KEYS[mini(sim.party.size() - 1, HERO_KEYS.size() - 1)])
	show_message("%s has come back! Summon him with %s" % [hero.display_name, key], UiStyle.GOLD)


func _hero_color(hero: HeroData) -> Color:
	return sim.config.element_color(hero.element) if not hero.element.is_empty() else UiStyle.GOLD


func _refresh_heroes() -> void:
	for hero in sim.party:
		var button: KeyButton = _hero_buttons.get(hero.id)
		if button == null:
			continue
		var tower := sim.hero_tower(hero.id)
		button.disabled = sim.is_over()
		if tower == null:
			button.modulate = Color(1, 1, 1, 0.7)
			button.badge_text = ""
			button.cooldown = 0.0
			button.cooldown_text = ""
			button.outline = UiStyle.GOLD if summoning == hero.id else Color(0, 0, 0, 0)
			button.tooltip_text = "%s, %s\n%s\nNot on the field yet: click (or press %s), then click a free tile to summon. Free." % [
				hero.display_name, hero.title, hero.blurb, button.key_text]
			continue
		button.modulate = Color.WHITE
		button.badge_text = "%d" % tower.hero_level_now()
		var ability := tower.hero_ability()
		var left := tower.ability_cooldown
		button.cooldown = left / ability.cooldown if left > 0.0 else 0.0
		button.cooldown_text = "%d" % ceili(left) if left > 0.0 else ""
		if aiming_hero == hero.id:
			button.outline = UiStyle.GOLD
		elif sim.hero_effect_time(hero.id) > 0.0:
			button.outline = _hero_color(hero).lightened(0.3)
		else:
			button.outline = Color(0, 0, 0, 0)
		button.tooltip_text = "%s  ·  Level %d\n%s: %s\nReady again after %d s  ·  Key: %s" % [
			hero.display_name, tower.hero_level_now(), ability.display_name, ability.description, roundi(ability.cooldown), button.key_text]


func _hero_info(tower: SimTower) -> String:
	var hero := tower.hero
	var color := _hero_color(hero).lightened(0.25).to_html(false)
	var lines: PackedStringArray = []
	lines.append("[b][color=#%s]%s[/color][/b]" % [color, hero.display_name])
	lines.append("[i]%s[/i]" % hero.title)
	lines.append("Level %d / %d  ·  a level for every wave fought" % [tower.hero_level_now(), HeroData.MAX_LEVEL])
	lines.append("Damage %.1f  ·  %.2f attacks/s" % [tower.damage, tower.attacks_per_second])
	lines.append("Range %d" % roundi(tower.attack_range))
	lines.append(hero.attack.description)
	lines.append("")
	lines.append("[b]Aura[/b] (towers within %d cells): %s" % [roundi(HeroData.AURA_CELLS), hero.aura_text])
	var ability := tower.hero_ability()
	lines.append("[b]%s[/b]: %s" % [ability.display_name, ability.description])
	if tower.hero_level_now() < HeroData.ULTIMATE_LEVEL:
		lines.append("[color=#%s]At level %d: %s[/color]" % [UiStyle.TEXT_DIM.to_html(false), HeroData.ULTIMATE_LEVEL, hero.ultimate_text])
	lines.append("")
	lines.append("Kills %d  ·  Damage %d" % [tower.kills, roundi(tower.damage_dealt)])
	return "\n".join(lines)


# --- Refresh -------------------------------------------------------------------

func _refresh() -> void:
	_gold.text = "%d" % sim.gold
	_gold.get_parent().tooltip_text = _gold_hint()
	_lives.text = "%d" % sim.lives
	if sim.is_endless():
		_wave.text = "Wave %d" % sim.wave_number()
	else:
		_wave.text = "Wave %d / %d" % [mini(sim.wave_number(), sim.total_waves()), sim.total_waves()]
	var where: PackedStringArray = []
	if sim.is_endless():
		where.append("Endless %d%%" % roundi(sim.endless_multiplier() * 100.0))
	var difficulty := sim.config.difficulty
	if difficulty != null and difficulty.order > 0:
		where.append(difficulty.display_name)
	if sim.config.stage != null:
		where.append(sim.config.stage.display_name)
	_stage.text = "  ·  ".join(where)
	_stage.tooltip_text = _stage.text
	_stage.visible = not where.is_empty()
	_next.text = _wave_text()
	_next.tooltip_text = _next.get_parsed_text()
	# How the wave comes: its beats, in words.
	var wave := sim.current_wave()
	if wave != null and not wave.description.is_empty():
		_next.tooltip_text += "\n" + wave.description
	var points := sim.tree.points
	_web_button.text = "Skill web (T)" + ("  ·  %d to spend" % points if points > 0 else "")
	_web_button.add_theme_color_override("font_color", UiStyle.GOLD if points > 0 else UiStyle.TEXT)
	_speed_button.text = "Paused (P)" if paused else "Speed %dx (F)" % speed
	_wave_button.disabled = sim.state != RunSim.State.BUILDING
	match sim.state:
		RunSim.State.BUILDING:
			_wave_button.text = "Start wave (Space)"
		RunSim.State.WAVE:
			_wave_button.text = "Wave in progress"
			if sim.rolls_on() and sim.next_wave_in() > 0.0:
				_wave_button.text = "Next wave in %d s" % ceili(sim.next_wave_in())
			elif sim.counter_started:
				_wave_button.text = "Counter-attack!"
		_:
			_wave_button.text = "Run over"
	_refresh_countdown()
	var number := 0
	for tower_id in _shop_ids:
		var shown := _in_open_tab(tower_id)
		if shown:
			number += 1
		_refresh_tower_button(tower_id, _tower_buttons[tower_id], number if shown and number <= 9 else 0)
	_refresh_shop_tabs()
	_refresh_skills()
	_refresh_heroes()
	_refresh_info()


## The gold's tooltip: how the savings bonus works and what the gold held now would earn.
func _gold_hint() -> String:
	var rules := sim.config.rules
	var share := roundi(sim.run_stat(&"savings_bonus", rules.savings_bonus) * 100.0)
	return "Gold\nSavings bonus: clearing a wave pays %d%% of the gold you kept (at most %d this wave, rising 8%% a wave).\nRight now: +%d gold" % [
		share, sim.savings_cap_now(), sim.savings_bonus_now()]


## "Savings +N" for the top bar while a wave is being fought, or nothing.
func _savings_text() -> String:
	if sim.state != RunSim.State.WAVE:
		return ""
	var bonus := sim.savings_bonus_now()
	if bonus <= 0:
		return ""
	return "  ·  [color=#%s]Savings +%d[/color]" % [UiStyle.GOLD.to_html(false), bonus]


func _wave_text() -> String:
	var wave := sim.wave_as_it_comes()
	if wave == null:
		return ""
	var element: ElementData = sim.config.elements.get(wave.element)
	var counts: Dictionary[StringName, int] = {}
	var mixed := false
	for group in wave.groups:
		counts[group.enemy] = counts.get(group.enemy, 0) + group.count
		mixed = mixed or (not group.element.is_empty() and group.element != wave.element)
	var parts: PackedStringArray = []
	for enemy_id in counts:
		var enemy: EnemyData = sim.config.enemies.get(enemy_id)
		var part := "%d %s" % [counts[enemy_id], enemy.display_name if enemy else String(enemy_id)]
		# Wardens keep their own element whatever the wave, and the Sundered Heart changes its own.
		var own: ElementData = sim.config.elements.get(enemy.element) if enemy != null else null
		if own != null:
			part += " ([color=#%s]%s[/color])" % [own.color.to_html(false), own.display_name]
		elif enemy != null and enemy.prismatic_interval > 0.0:
			part += " (every element)"
		parts.append(part)
	var label := "Now" if sim.state == RunSim.State.WAVE else "Next"
	var boss := (" [b][color=#e8c547]BOSS[/color][/b]" if wave.is_boss else "") + _savings_text()
	# Two lines: what the wave is, then who is in it.
	if mixed:
		return "%s: [b]Mixed wave[/b]%s  ·  every group has its own element\n%s" % [label, boss, ", ".join(parts)]
	if element == null:
		return "%s:%s\n%s" % [label, boss, ", ".join(parts)]
	var opposite := _element_at(ElementRules.opposite_index(element.ring_index))
	return "%s: [color=#%s][b]%s wave[/b][/color]%s  ·  weak to [color=#%s]%s[/color]\n%s" % [
		label, element.color.to_html(false), element.display_name, boss,
		opposite.color.to_html(false) if opposite else "ffffff", opposite.display_name if opposite else "?",
		", ".join(parts)]


func _element_at(ring_index: int) -> ElementData:
	for element: ElementData in sim.config.elements.values():
		if element.ring_index == ring_index:
			return element
	return null


func _refresh_shop_tabs() -> void:
	var unlocked := {1: 0, 2: 0, 3: 0}
	for tower_id in _tower_buttons:
		var data: TowerData = sim.config.towers[tower_id]
		if not data.is_hybrid() or sim.is_unlocked(tower_id):
			unlocked[data.elements.size()] += 1
	var names := {1: "Base", 2: "Duals", 3: "Triples"}
	for tier: int in _tier_tabs:
		var tab := _tier_tabs[tier]
		tab.text = names[tier] if tier == 1 else "%s %d" % [names[tier], unlocked[tier]]
		tab.set_pressed_no_signal(tier == _shop_tier)
		tab.tooltip_text = "" if unlocked[tier] > 0 else \
				("Take a bridge node, or the core nodes of two elements, to unlock dual towers." if tier == 2 \
				else "Take the core nodes of three elements to unlock their triple tower.")
	# The grid scrolls once a tab holds more towers than fit above the tower panel.
	_shop_scroll.custom_minimum_size.y = minf(_shop_grid.get_combined_minimum_size().y, SHOP_MAX_HEIGHT)


func _refresh_tower_button(tower_id: StringName, button: KeyButton, hotkey: int) -> void:
	var data: TowerData = sim.config.towers[tower_id]
	var price := sim.tower_price(tower_id)
	button.visible = _in_open_tab(tower_id)
	button.key_text = "%d" % hotkey if hotkey > 0 else ""
	var key := "\nKey: %d" % hotkey if hotkey > 0 else ""
	if not sim.is_unlocked(tower_id):
		button.text = "Lock"
		button.tooltip_text = "%s (%s)\n%s\n%s" % [data.display_name, _element_names(data), data.description, _unlock_hint(tower_id)]
		button.disabled = true
	else:
		button.text = "%dg" % price
		button.tooltip_text = "%s (%s)  ·  %d gold\n%s%s" % [data.display_name, _element_names(data), price, data.description, key]
		button.disabled = sim.gold < price or sim.is_over()


func _refresh_skills() -> void:
	for skill_id in _skill_ids:
		var button := _skill_buttons[skill_id]
		var skill: SkillData = sim.config.skills[skill_id]
		var unlocked := sim.is_skill_unlocked(skill_id)
		var left := sim.skill_cooldown_left(skill_id)
		button.disabled = not unlocked or sim.is_over()
		button.modulate = Color.WHITE if unlocked else Color(1, 1, 1, 0.45)
		button.cooldown = left / sim.skill_cooldown(skill_id) if left > 0.0 else 0.0
		button.cooldown_text = "%d" % ceili(left) if left > 0.0 else ""
		if aiming == skill_id:
			button.outline = UiStyle.GOLD
		elif sim.skill_time_left(skill_id) > 0.0:
			button.outline = sim.config.element_color(skill.element).lightened(0.3)
		else:
			button.outline = Color(0, 0, 0, 0)
		button.tooltip_text = _skill_tooltip(skill, unlocked, button.key_text)
		_refresh_skill_upgrade(skill, unlocked, button.key_text)


## The level-up button under a skill: its level and the gold for the next, or that it is at its last.
func _refresh_skill_upgrade(skill: SkillData, unlocked: bool, key: String) -> void:
	var upgrade: Button = _skill_upgrades.get(skill.id)
	if upgrade == null:
		return
	var level := sim.skill_level(skill.id)
	var cost := sim.skill_upgrade_cost(skill.id)
	upgrade.text = "Lv%d  MAX" % level if cost < 0 else "Lv%d  +%dg" % [level, cost]
	upgrade.disabled = not sim.skill_upgrade_error(skill.id).is_empty()
	upgrade.modulate = Color.WHITE if unlocked else Color(1, 1, 1, 0.45)
	var lines: PackedStringArray = []
	lines.append("%s, level %d of %d" % [skill.title_at(level), level, skill.max_level()])
	if cost < 0:
		lines.append("At its last level.")
	else:
		var next := skill.rank(level + 1)
		lines.append("Next: %s (%d gold)" % [skill.title_at(level + 1), cost])
		lines.append(next.description)
		if not key.is_empty():
			lines.append("Key: Shift+%s" % key)
		var error := sim.skill_upgrade_error(skill.id)
		if not error.is_empty():
			lines.append(error)
	upgrade.tooltip_text = "\n".join(lines)


func _skill_tooltip(skill: SkillData, unlocked: bool, key: String) -> String:
	var element: ElementData = sim.config.elements.get(skill.element)
	var lines: PackedStringArray = []
	var level := sim.skill_level(skill.id)
	lines.append("%s (%s), level %d" % [skill.title_at(level), element.display_name if element else String(skill.element), level])
	lines.append(skill.description)
	if level > 1:
		for step in range(2, level + 1):
			lines.append("+ %s: %s" % [skill.title_at(step), skill.rank(step).description])
	lines.append("Ready again after %d s%s" % [roundi(sim.skill_cooldown(skill.id)), "  ·  Key: " + key if not key.is_empty() else ""])
	if skill.is_targeted():
		lines.append("Click it (or press its key), then click the board. Pressing the key again casts where the mouse is.")
	if not unlocked and sim.tree.is_locked(skill.requires_node):
		lines.append("Closed in this run.")
	elif not unlocked:
		var node_data := sim.tree.graph.node(skill.requires_node)
		lines.append("Locked: take %s in the skill web." % (node_data.display_name if node_data != null else String(skill.requires_node)))
	return "\n".join(lines)


func _element_names(data: TowerData) -> String:
	var names: PackedStringArray = []
	for element_id in data.elements:
		var element: ElementData = sim.config.elements.get(element_id)
		names.append(element.display_name if element else String(element_id))
	return " + ".join(names)


## Where a locked tower is unlocked: a skill web node, or the meta tree when that node is locked too.
func _unlock_hint(tower_id: StringName) -> String:
	var data: TowerData = sim.config.towers[tower_id]
	if not data.requires_nodes.is_empty():
		var needed: PackedStringArray = []
		for node_data in sim.config.tree_nodes:
			if data.requires_nodes.has(node_data.id):
				needed.append(node_data.display_name)
		return "Unlock: take %s" % " and ".join(needed)
	for node_data in sim.config.tree_nodes:
		if node_data.unlocks_towers.has(tower_id):
			if sim.tree.is_locked(node_data.id):
				return "Unlock in the meta tree"
			return "Unlock: %s" % node_data.display_name
	return "Locked"


func _refresh_info() -> void:
	if selected == null or not sim.towers.has(selected):
		_info.text = _help_text()
		_sell_button.hide()
		_set_actions([])
		return
	var tower := selected
	if tower.is_hero():
		_info.text = _hero_info(tower)
		_sell_button.hide()
		_refresh_actions(tower)
		return
	var lines: PackedStringArray = []
	var title := tower.data.display_name
	if tower.ascendancy != null:
		title = "%s · %s" % [tower.ascendancy.display_name, title]
	lines.append("[b]%s[/b]" % title)
	lines.append("%s  ·  Level %d / %d" % [_element_names(tower.data), tower.level, SimTower.MAX_LEVEL])
	lines.append("Damage %.1f  ·  %.2f attacks/s" % [tower.damage, tower.attacks_per_second])
	lines.append("Range %d" % roundi(tower.attack_range))
	if tower.splash_radius > 0.0:
		lines.append("Splash radius %d" % roundi(tower.splash_radius))
	if tower.chains():
		var falloff := roundi(tower.chain_falloff * 100.0)
		lines.append("Chains to %d more" % tower.chain_count + (" (−%d%% per jump)" % falloff if falloff > 0 else ""))
	if tower.knockback > 0.0:
		lines.append("Pushes enemies back %d" % roundi(tower.knockback))
	if tower.aura_radius > 0.0 and tower.aura_damage > 0.0:
		lines.append("Aura: +%d%% damage to towers within %d" % [roundi(tower.aura_damage * 100.0), roundi(tower.aura_radius)])
	if tower.aura_bonus > 0.0:
		lines.append("[color=#c8a0ff]Empowered: +%d%% damage[/color]" % roundi(tower.aura_bonus * 100.0))
	for spec in tower.effects:
		lines.append(_effect_text(spec))
	if tower.ascendancy != null:
		lines.append("[i]%s[/i]" % tower.ascendancy.description)
	lines.append("")
	lines.append("Kills %d  ·  Damage %d" % [tower.kills, roundi(tower.damage_dealt)])
	_info.text = "\n".join(lines)
	_sell_button.text = "Sell for %dg (Del)" % sim.sell_value(tower)
	_sell_button.show()
	_refresh_actions(tower)


## What to do and which keys do it, shown while no tower is selected.
func _help_text() -> String:
	var dim := UiStyle.TEXT_DIM.to_html(false)
	var gold := UiStyle.GOLD.to_html(false)
	var keys: Array[Array] = [
		["T", "skill web"], ["F1 F2 F3", "heroes"], ["1-9", "pick a tower"], ["Tab", "next tower page"], ["Q W E  A S D", "skills"],
		["Z X C V", "upgrade the tower"], ["Del", "sell the tower"], ["Space", "start the wave"],
		["F", "speed"], ["P", "pause"], ["O", "audio"], ["M", "mute"], ["Esc", "menu, exit"],
	]
	var lines: PackedStringArray = []
	lines.append("[b]How to play[/b]")
	lines.append("Take an element in the skill web: it opens that element's tower and its skill.")
	lines.append("Pick a tower and click a free tile. Shift-click builds several.")
	lines.append("Click a tower to level it up, to ascend it at level %d or to fuse it." % SimTower.MAX_LEVEL)
	lines.append("A wave resists its own element and is weak to the opposite one.")
	lines.append("")
	var rules := _stage_rules()
	if not rules.is_empty():
		lines.append(rules.strip_edges())
		lines.append("")
	lines.append("[b]Keys[/b]")
	for pair in keys:
		lines.append("[color=#%s]%s[/color]  [color=#%s]%s[/color]" % [gold, pair[0], dim, pair[1]])
	return "\n".join(lines)


static func _effect_text(spec: StatusEffectData) -> String:
	match spec.kind:
		&"slow":
			return "Slows by %d%% for %.1fs" % [roundi(spec.slow * 100.0), spec.duration]
		&"stun":
			return "Stuns for %.1fs" % spec.duration
		&"curse":
			return "Curse: +%d%% damage taken for %.1fs" % [roundi(spec.damage_taken * 100.0), spec.duration]
		&"shatter":
			return "Shatter: −%.1f armour per stack, up to %d" % [spec.armour_reduction, spec.max_stacks]
	return "%s %.1f/s for %.1fs, up to %d stacks" % [String(spec.kind).capitalize(), spec.damage_per_second, spec.duration, spec.max_stacks]


## One entry per upgrade button: [kind, id, label, tooltip, error].
func _upgrade_choices(tower: SimTower) -> Array:
	var choices := []
	if tower.is_hero():
		var hero_id := tower.hero.id
		var key := _hero_buttons[hero_id].key_text if _hero_buttons.has(hero_id) else ""
		var ability := tower.hero_ability()
		choices.append([&"ability", hero_id, "%s  ·  %s" % [ability.display_name, key], ability.description,
				sim.hero_ability_error(hero_id)])
		var move_error := sim.move_error(tower, Vector2i(-1, -1)) if sim.state != RunSim.State.BUILDING or tower.moved_this_break else ""
		choices.append([&"move", hero_id, "Move  ·  once per break", "Pick a free tile to march to. Only between waves, once each break.",
				move_error])
		return choices
	if tower.level < SimTower.MAX_LEVEL:
		choices.append([&"level", &"", "Level %d  ·  %dg" % [tower.level + 1, tower.level_up_price()],
				"+%d%% more damage and +%d%% range per level." % [roundi(SimTower.DAMAGE_PER_LEVEL * 100.0), roundi(SimTower.RANGE_PER_LEVEL * 100.0)],
				sim.level_up_error(tower)])
	elif tower.can_ascend():
		for option in tower.data.ascendancies:
			choices.append([&"ascend", option.id, "Ascend: %s  ·  %dg" % [option.display_name, tower.ascend_price(option)],
					option.description + "\nAscending is final.", sim.ascend_error(tower, option.id)])
	for hybrid_id in sim.hybrid_options(tower):
		var data: TowerData = sim.config.towers[hybrid_id]
		choices.append([&"hybrid", hybrid_id, "Become %s  ·  %dg" % [data.display_name, sim.hybrid_upgrade_price(tower, hybrid_id)],
				"%s (%s)\n%s\nKeeps its level and its record." % [data.display_name, _element_names(data), data.description],
				sim.hybrid_upgrade_error(tower, hybrid_id)])
	return choices


func _refresh_actions(tower: SimTower) -> void:
	var choices := _upgrade_choices(tower)
	_set_actions(choices)
	for i in choices.size():
		var button := _actions.get_child(i) as Button
		var error: String = choices[i][4]
		button.disabled = not error.is_empty()


func _set_actions(choices: Array) -> void:
	var key := ""
	for choice: Array in choices:
		key += "%s|" % choice[2]
	if key == _actions_key:
		return
	_actions_key = key
	for child in _actions.get_children():
		_actions.remove_child(child)
		child.queue_free()
	for choice: Array in choices:
		var button := UiStyle.key_button(choice[2], 16)
		button.custom_minimum_size = Vector2(0, 36)
		button.tooltip_text = choice[3]
		button.clip_text = true
		button.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		if _actions.get_child_count() < ACTION_KEYS.size():
			button.key_text = OS.get_keycode_string(ACTION_KEYS[_actions.get_child_count()])
		var kind: StringName = choice[0]
		var id: StringName = choice[1]
		button.set_meta(&"action", kind)
		button.set_meta(&"id", id)
		button.pressed.connect(_on_action_pressed.bind(kind, id))
		_actions.add_child(button)


func _on_action_pressed(kind: StringName, id: StringName) -> void:
	match kind:
		&"level":
			level_up_pressed.emit()
		&"ascend":
			ascend_pressed.emit(id)
		&"hybrid":
			hybrid_pressed.emit(id)
		&"ability":
			hero_pressed.emit(id)
		&"move":
			move_pressed.emit()


# --- Events --------------------------------------------------------------------

func _on_wave_cleared(number: int, points: int, gold: int) -> void:
	if sim.is_over():
		return
	var text := "Wave %d cleared  ·  +%d gold" % [number, gold]
	if sim.last_savings_bonus > 0:
		text += " (%d savings bonus)" % sim.last_savings_bonus
	if points > 0:
		text += "  ·  +%d skill point%s" % [points, "" if points == 1 else "s"]
	if not sim.caves.is_empty() and sim.caves[-1].wave == number + 1:
		# A cave broke open in this break: say so, and keep the message up a while.
		text += "\nThe ground splits open: a new enemy cave! From the next wave the horde pours out of it too."
		show_message(text, UiStyle.LIFE)
		_message_time = 6.0
		return
	show_message(text, UiStyle.GOOD)


## The stage's rules, as a paragraph for the help text. Empty outside the campaign.
func _stage_rules() -> String:
	var stage := sim.config.stage
	if stage == null or stage.rule_text.is_empty():
		return ""
	return "[b]%s[/b]\n%s\n\n" % [stage.display_name, "\n".join(stage.rule_text)]


## Adds a campaign stage's result to the end panel: stars, the first-win bonus and, when this win
## finished the campaign, its reward. next_stage_open shows the Next stage button.
func show_stage_result(result: Dictionary, next_stage_open: bool) -> void:
	var stage := sim.config.stage
	if stage == null:
		return
	var stars: int = result.get("stars", 0)
	var best: int = result.get("best", 0)
	var lines: PackedStringArray = []
	lines.append("[center][color=#%s]%s[/color][color=#5a6275]%s[/color][/center]" % [
		UiStyle.GOLD.to_html(false), "★ ".repeat(stars).strip_edges(), (" ★".repeat(3 - stars)) if stars < 3 else ""])
	if stars > 0 and best > stars:
		lines.append("[center]Your best here is %d stars.[/center]" % best)
	var first: int = result.get("first_clear_points", 0)
	if first > 0:
		lines.append("[center][color=#%s]First win: +%d meta points[/color][/center]" % [UiStyle.GOLD.to_html(false), first])
	if result.get("campaign_complete", false) and sim.config.campaign != null:
		var campaign := sim.config.campaign
		lines.append("[center][b][color=#%s]%s complete![/color][/b]\n%s: %s[/center]" % [
			UiStyle.GOOD.to_html(false), campaign.display_name, campaign.reward_name, campaign.reward_description])
	for hero: HeroData in result.get("heroes_joined", []):
		lines.append("[center][b][color=#%s]%s joins you![/color][/b]\n%s[/center]" % [
			UiStyle.GOLD.to_html(false), hero.display_name, hero.blurb])
	_end_stage.text = "\n".join(lines)
	_end_stage.show()
	_campaign_button.show()
	_next_stage_button.visible = next_stage_open


## Adds a line of story under the stage result, such as the city lost or saved.
func show_story_note(text: String) -> void:
	if text.is_empty():
		return
	var line := "[center][i]%s[/i][/center]" % text
	_end_stage.text = line if _end_stage.text.is_empty() else _end_stage.text + "\n" + line
	_end_stage.show()


## The win or lose panel, with the run's numbers and the meta points it paid, and why (`note`:
## a new record, a replay reward, or no new record).
func show_end(won: bool, meta_points: int, note := "") -> void:
	_end_title.text = "Victory" if won else "Defeat"
	_end_title.add_theme_color_override("font_color", UiStyle.GOOD if won else UiStyle.BAD)
	var waves := "%d of %d" % [sim.wave_index, sim.total_waves()]
	if sim.is_endless():
		waves = "%d (endless)" % sim.wave_index
	_end_stats.text = "Waves cleared: %s\nEnemies killed: %d\nLives left: %d\nGold earned: %d" % [
		waves, sim.kills, sim.lives, sim.gold_earned]
	_end_meta.text = "+%d meta point%s. Spend them in Talents from the main menu." % [
		meta_points, "" if meta_points == 1 else "s"]
	if not note.is_empty():
		_end_meta.text += "\n" + note
	_end_panel.show()
