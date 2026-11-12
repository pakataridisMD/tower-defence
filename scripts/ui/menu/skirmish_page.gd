class_name SkirmishPage
extends MenuPage
## Skirmish: pick a map, a difficulty level and the mode (the map's waves, or endless), then play
## one run. Locked maps and levels are greyed out, and their tooltip says which talent opens them.

signal play_requested

const CARD_SIZE := Vector2(216, 236)

const WAVES_TEXT := "Fight the map's waves, a Warden at the end. Win by holding to the last."
const ENDLESS_TEXT := "The waves never stop. The horde starts at half strength and grows a little with every wave, in numbers and in health. How long can you hold?"

var _difficulty_text: Label
var _mode_text: Label
var _record: Label
var play_button: MenuItemButton


func _init() -> void:
	super("Skirmish", "One map, one run. Build, fuse, survive.")
	var meta := Progress.meta

	var maps_panel := add_panel(Vector2(0, 0), Vector2(720, 852))
	var maps_column := VBoxContainer.new()
	maps_column.add_theme_constant_override("separation", 16)
	maps_panel.add_child(maps_column)
	maps_column.add_child(UiStyle.menu_label("MAPS", "small", 16, UiStyle.MENU_GOLD))
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 16)
	grid.add_theme_constant_override("v_separation", 16)
	maps_column.add_child(grid)
	var map_group := ButtonGroup.new()
	for map in meta.maps_in_order():
		var unlocked := meta.is_map_unlocked(map.id)
		var card := UiStyle.menu_choice(map.display_name, map_group, 40)
		card.custom_minimum_size = CARD_SIZE
		card.icon = _ground(map.id)
		card.expand_icon = true
		card.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		card.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		card.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		card.disabled = not unlocked
		card.button_pressed = map.id == meta.selected_map
		if not unlocked:
			card.tooltip_text = MainMenu.unlock_hint(&"unlocks_maps", map.id)
			card.add_theme_color_override("icon_disabled_color", Color(0.25, 0.22, 0.32))
			var lock := TextureRect.new()
			lock.texture = UiStyle.menu_art("lock")
			lock.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
			lock.position = Vector2(CARD_SIZE.x * 0.5 - 14, 92)
			lock.size = Vector2(28, 34)
			lock.stretch_mode = TextureRect.STRETCH_SCALE
			lock.mouse_filter = Control.MOUSE_FILTER_IGNORE
			card.add_child(lock)
		var map_id := map.id
		card.toggled.connect(func(on: bool) -> void:
			if on:
				Progress.select_map(map_id)
				_show_record())
		grid.add_child(card)

	var rules_panel := add_panel(Vector2(744, 0), Vector2(1080, 852))
	var rules := VBoxContainer.new()
	rules.add_theme_constant_override("separation", 18)
	rules_panel.add_child(rules)
	rules.add_child(UiStyle.menu_label("RULES", "small", 16, UiStyle.MENU_GOLD))
	rules.add_child(UiStyle.menu_label("Difficulty", "button", 40))
	var level_row := HBoxContainer.new()
	level_row.add_theme_constant_override("separation", 12)
	var level_group := ButtonGroup.new()
	for level in meta.difficulties_in_order():
		var unlocked := meta.is_difficulty_unlocked(level.id)
		var choice := UiStyle.menu_choice(level.display_name, level_group, 32)
		choice.custom_minimum_size = Vector2(196, 56)
		choice.disabled = not unlocked
		choice.button_pressed = level.id == meta.selected_difficulty
		choice.tooltip_text = level.description if unlocked else MainMenu.unlock_hint(&"unlocks_difficulties", level.id)
		var level_id := level.id
		choice.toggled.connect(func(on: bool) -> void:
			if on:
				Progress.select_difficulty(level_id)
				_show_difficulty())
		level_row.add_child(choice)
	rules.add_child(level_row)
	_difficulty_text = UiStyle.menu_label("", "body", 32, UiStyle.MENU_DIM)
	_difficulty_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_difficulty_text.custom_minimum_size = Vector2(1000, 0)
	rules.add_child(_difficulty_text)
	rules.add_child(UiStyle.menu_label("Mode", "button", 40))
	var mode_row := HBoxContainer.new()
	mode_row.add_theme_constant_override("separation", 12)
	var mode_group := ButtonGroup.new()
	for endless in [false, true]:
		var choice := UiStyle.menu_choice("Endless" if endless else "Waves", mode_group, 32)
		choice.custom_minimum_size = Vector2(196, 56)
		choice.button_pressed = meta.endless == endless
		choice.tooltip_text = ENDLESS_TEXT if endless else WAVES_TEXT
		choice.toggled.connect(func(on: bool) -> void:
			if on:
				Progress.set_endless(endless)
				_show_difficulty()
				_show_record())
		mode_row.add_child(choice)
	rules.add_child(mode_row)
	_mode_text = UiStyle.menu_label("", "body", 32, UiStyle.MENU_DIM)
	_mode_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_mode_text.custom_minimum_size = Vector2(1000, 0)
	rules.add_child(_mode_text)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	rules.add_child(spacer)
	_record = UiStyle.menu_label("", "small", 16, UiStyle.MENU_DIM)
	rules.add_child(_record)
	var note := UiStyle.menu_label("More maps and harder levels open up in Talents.", "body", 32, UiStyle.MENU_DIM)
	note.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	note.custom_minimum_size = Vector2(1000, 0)
	rules.add_child(note)
	play_button = MenuItemButton.new("Play skirmish", "Enter")
	play_button.custom_minimum_size = Vector2(0, 88)
	play_button.add_theme_font_size_override("font_size", 50)
	play_button.add_theme_stylebox_override("normal", UiStyle.menu_button_box("hover"))
	play_button.pressed.connect(func() -> void: play_requested.emit())
	rules.add_child(play_button)
	refresh()


func refresh() -> void:
	_show_difficulty()
	_show_record()


func _show_difficulty() -> void:
	var picked: DifficultyData = DataRegistry.difficulties.get(Progress.meta.selected_difficulty)
	_difficulty_text.text = picked.description if picked != null else ""
	_mode_text.text = ENDLESS_TEXT if Progress.meta.endless else WAVES_TEXT


func _show_record() -> void:
	var profile := Progress.meta.profile
	if profile.runs_played == 0:
		_record.text = "NO RUNS YET. EVERY RUN EARNS TALENT POINTS, WON OR LOST."
	else:
		_record.text = "BEST %d WAVES  -  %d RUNS  -  %d WINS" % [profile.best_waves, profile.runs_played, profile.runs_won]
	if Progress.meta.endless:
		var best := Progress.meta.endless_best(Progress.meta.selected_map)
		_record.text = "ENDLESS BEST HERE: %s" % ("WAVE %d" % best if best > 0 else "NOT PLAYED YET")


static func _ground(map_id: StringName) -> Texture2D:
	var path := "res://assets/art/game/ground/%s.png" % map_id
	return load(path) if ResourceLoader.exists(path) else null
