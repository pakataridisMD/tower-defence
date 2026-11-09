class_name Hud
extends Control
## The run's interface: top bar, tower shop, selected tower panel, messages and the end screen.
## It reads the simulation every frame and reports button presses through signals.

signal start_wave_pressed
signal web_pressed
signal speed_pressed
signal tower_chosen(tower_id: StringName)
signal sell_pressed
signal level_up_pressed
signal ascend_pressed(ascendancy_id: StringName)
signal hybrid_pressed(hybrid_id: StringName)
signal play_again_pressed
signal menu_pressed
signal campaign_pressed
signal next_stage_pressed

const TOP_BAR_HEIGHT := 72.0
const SIDE_PANEL_X := 1584.0

var sim: RunSim
var speed := 1
var paused := false
var selected: SimTower

var _gold: Label
var _lives: Label
var _wave: Label
var _next: RichTextLabel
var _web_button: Button
var _speed_button: Button
var _wave_button: Button
var _tower_buttons: Dictionary[StringName, Button] = {}
var _info: RichTextLabel
var _sell_button: Button
## Level, ascendancy and hybrid buttons for the selected tower, rebuilt when the choices change.
var _actions: VBoxContainer
var _actions_key := ""
var _message: Label
var _message_time := 0.0
var _end_panel: PanelContainer
var _end_title: Label
var _end_stats: Label
var _end_meta: Label
var _end_stage: RichTextLabel
var _campaign_button: Button
var _next_stage_button: Button


func setup(p_sim: RunSim) -> void:
	sim = p_sim
	theme = UiStyle.make_theme()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	_build_top_bar()
	_build_side_panel()
	_build_message()
	_build_end_panel()
	sim.wave_cleared.connect(_on_wave_cleared)
	sim.wave_started.connect(func(number: int) -> void: show_message("Wave %d" % number))


func show_message(text: String, color: Color = UiStyle.TEXT) -> void:
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
	bar.position = Vector2(12, 8)
	bar.size = Vector2(1896, TOP_BAR_HEIGHT)
	add_child(bar)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 28)
	bar.add_child(row)
	_gold = UiStyle.label("", 26, UiStyle.GOLD)
	_lives = UiStyle.label("", 26, UiStyle.LIFE)
	_wave = UiStyle.label("", 26)
	for item: Label in [_gold, _lives, _wave]:
		item.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		row.add_child(item)
	_next = RichTextLabel.new()
	_next.bbcode_enabled = true
	_next.fit_content = true
	_next.scroll_active = false
	_next.autowrap_mode = TextServer.AUTOWRAP_OFF
	_next.custom_minimum_size = Vector2(620, 0)
	_next.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_next.add_theme_font_size_override("normal_font_size", 21)
	_next.add_theme_font_size_override("bold_font_size", 21)
	row.add_child(_next)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(spacer)
	_web_button = UiStyle.button("", 21)
	_web_button.pressed.connect(func() -> void: web_pressed.emit())
	_speed_button = UiStyle.button("", 21)
	_speed_button.pressed.connect(func() -> void: speed_pressed.emit())
	_wave_button = UiStyle.button("", 21)
	_wave_button.pressed.connect(func() -> void: start_wave_pressed.emit())
	for item: Button in [_web_button, _speed_button, _wave_button]:
		row.add_child(item)


func _build_side_panel() -> void:
	var panel := PanelContainer.new()
	panel.position = Vector2(SIDE_PANEL_X, 96)
	panel.size = Vector2(324, 960)
	add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	column.add_child(UiStyle.label("Towers", 26))
	# A grid of tower pictures: base towers on top, then the hybrids unlocked so far.
	# Names and details are in the tooltips.
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	column.add_child(grid)
	var number := 1
	for tower_id in _shop_order():
		var data: TowerData = sim.config.towers[tower_id]
		var colors: Array[Color] = []
		for element_id in data.elements:
			colors.append(sim.config.element_color(element_id))
		var button := UiStyle.button("", 16)
		button.icon = UiStyle.element_icon(colors)
		button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		button.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		button.custom_minimum_size = Vector2(72, 64)
		var picture := BoardArt.tower_picture(tower_id)
		if picture != null:
			# The tower's own pixel art, at one screen pixel per art pixel.
			button.icon = picture
			button.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			button.custom_minimum_size = Vector2(72, picture.get_height() + 30)
		button.clip_text = true
		button.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
		button.pressed.connect(func() -> void: tower_chosen.emit(tower_id))
		# Number keys pick the six base towers.
		button.set_meta(&"hotkey", number if not data.is_hybrid() and number <= 9 else 0)
		grid.add_child(button)
		_tower_buttons[tower_id] = button
		number += 1
	column.add_child(HSeparator.new())
	_info = RichTextLabel.new()
	_info.bbcode_enabled = true
	_info.fit_content = true
	_info.scroll_active = false
	_info.add_theme_font_size_override("normal_font_size", 18)
	_info.add_theme_font_size_override("bold_font_size", 22)
	column.add_child(_info)
	_actions = VBoxContainer.new()
	_actions.add_theme_constant_override("separation", 6)
	column.add_child(_actions)
	_sell_button = UiStyle.button("", 20)
	_sell_button.pressed.connect(func() -> void: sell_pressed.emit())
	column.add_child(_sell_button)


func _build_message() -> void:
	_message = UiStyle.label("", 30)
	_message.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_message.position = Vector2(24, 108)
	_message.size = Vector2(1536, 40)
	_message.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_message)


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


## Base towers first in ring order, then hybrids.
func _shop_order() -> Array[StringName]:
	var ids: Array[StringName] = []
	ids.assign(sim.config.towers.keys())
	var rank := func(id: StringName) -> int:
		var data: TowerData = sim.config.towers[id]
		var first := sim.config.element_index(data.elements[0]) if not data.elements.is_empty() else 0
		if not data.is_hybrid():
			return first
		return 100 + first * 10 + sim.config.element_index(data.elements[1])
	ids.sort_custom(func(a: StringName, b: StringName) -> bool: return rank.call(a) < rank.call(b))
	return ids


func tower_for_hotkey(number: int) -> StringName:
	for tower_id in _tower_buttons:
		if _tower_buttons[tower_id].get_meta(&"hotkey") == number:
			return tower_id
	return &""


# --- Refresh -------------------------------------------------------------------

func _refresh() -> void:
	_gold.text = "Gold %d" % sim.gold
	_lives.text = "Lives %d" % sim.lives
	_wave.text = "Wave %d / %d" % [sim.wave_number(), sim.total_waves()]
	var difficulty := sim.config.difficulty
	if difficulty != null and difficulty.order > 0:
		_wave.text += "  ·  " + difficulty.display_name
	if sim.config.stage != null:
		_wave.text += "  ·  " + sim.config.stage.display_name
	_next.text = _wave_text()
	var points := sim.tree.points
	_web_button.text = "Skill web (T)" + ("  ·  %d point%s" % [points, "" if points == 1 else "s"] if points > 0 else "")
	_speed_button.text = "Paused (P)" if paused else "Speed %dx (F)" % speed
	_wave_button.disabled = sim.state != RunSim.State.BUILDING
	match sim.state:
		RunSim.State.BUILDING:
			_wave_button.text = "Start wave (Space)"
		RunSim.State.WAVE:
			_wave_button.text = "Wave in progress"
		_:
			_wave_button.text = "Run over"
	for tower_id in _tower_buttons:
		_refresh_tower_button(tower_id, _tower_buttons[tower_id])
	_refresh_info()


func _wave_text() -> String:
	var wave := sim.current_wave()
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
	var boss := " [b][color=#e8c547]BOSS[/color][/b]" if wave.is_boss else ""
	if mixed:
		return "%s: [b]Mixed wave[/b]%s  ·  every group has its own element  ·  %s" % [label, boss, ", ".join(parts)]
	if element == null:
		return "%s:%s %s" % [label, boss, ", ".join(parts)]
	var opposite := _element_at(ElementRules.opposite_index(element.ring_index))
	return "%s: [color=#%s][b]%s wave[/b][/color]%s  ·  weak to [color=#%s]%s[/color]  ·  %s" % [
		label, element.color.to_html(false), element.display_name, boss,
		opposite.color.to_html(false) if opposite else "ffffff", opposite.display_name if opposite else "?",
		", ".join(parts)]


func _element_at(ring_index: int) -> ElementData:
	for element: ElementData in sim.config.elements.values():
		if element.ring_index == ring_index:
			return element
	return null


func _refresh_tower_button(tower_id: StringName, button: Button) -> void:
	var data: TowerData = sim.config.towers[tower_id]
	var price := sim.tower_price(tower_id)
	var hotkey: int = button.get_meta(&"hotkey")
	var key := "%d · " % hotkey if hotkey > 0 else ""
	# Hybrids stay out of the shop until they are unlocked, so the panel only grows as the run does.
	button.visible = not data.is_hybrid() or sim.is_unlocked(tower_id)
	if not sim.is_unlocked(tower_id):
		button.text = "Locked"
		button.tooltip_text = "%s (%s)\n%s\n%s" % [data.display_name, _element_names(data), data.description, _unlock_hint(tower_id)]
		button.disabled = true
	else:
		button.text = "%s%dg" % [key, price]
		button.tooltip_text = "%s (%s)\n%s" % [data.display_name, _element_names(data), data.description]
		button.disabled = sim.gold < price or sim.is_over()


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
		_info.text = "[b]How to play[/b]\n" + \
			"Open the skill web (T) and take an element to unlock its tower. " + \
			"Pick a tower, then click an empty tile to build it. Shift-click builds several; right-click cancels.\n\n" + \
			"Click a tower to level it up. At level %d it can ascend into one of two specialisations, " % SimTower.MAX_LEVEL + \
			"and a base tower can turn into a hybrid once its bridge is taken.\n\n" + \
			"Each wave resists its own element and is weak to the opposite one, so mix elements.\n\n" + \
			_stage_rules() + \
			"Space: start wave · F: speed · P: pause · 1-6: towers"
		_sell_button.hide()
		_set_actions([])
		return
	var tower := selected
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
		lines.append("Chains to %d more (−%d%% per jump)" % [tower.chain_count, roundi(tower.chain_falloff * 100.0)])
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
	_sell_button.text = "Sell for %dg" % sim.sell_value(tower)
	_sell_button.show()
	_refresh_actions(tower)


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
				"%s (%s)\n%s\nKeeps its level." % [data.display_name, _element_names(data), data.description],
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
		var button := UiStyle.button(choice[2], 18)
		button.tooltip_text = choice[3]
		button.clip_text = true
		button.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
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


# --- Events --------------------------------------------------------------------

func _on_wave_cleared(number: int, points: int, gold: int) -> void:
	if sim.is_over():
		return
	var text := "Wave %d cleared  ·  +%d gold" % [number, gold]
	if points > 0:
		text += "  ·  +%d skill point%s" % [points, "" if points == 1 else "s"]
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
	_end_stage.text = "\n".join(lines)
	_end_stage.show()
	_campaign_button.show()
	_next_stage_button.visible = next_stage_open


## The win or lose panel, with the run's numbers and the meta points it paid.
func show_end(won: bool, meta_points: int) -> void:
	_end_title.text = "Victory" if won else "Defeat"
	_end_title.add_theme_color_override("font_color", UiStyle.GOOD if won else UiStyle.BAD)
	_end_stats.text = "Waves cleared: %d of %d\nEnemies killed: %d\nLives left: %d\nGold earned: %d" % [
		sim.wave_index, sim.total_waves(), sim.kills, sim.lives, sim.gold_earned]
	_end_meta.text = "+%d meta point%s. Spend them in the meta tree from the main menu." % [
		meta_points, "" if meta_points == 1 else "s"]
	_end_panel.show()
