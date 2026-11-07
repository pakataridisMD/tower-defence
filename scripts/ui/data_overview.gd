extends Control
## Debug screen, opened from the main menu. Lists the loaded game data and any data errors,
## so a broken data file is easy to spot.

const BACKGROUND_COLOR := UiStyle.BACKGROUND
const TEXT_COLOR := UiStyle.TEXT
const ERROR_COLOR := UiStyle.BAD
const SUCCESS_COLOR := UiStyle.GOOD
const MENU_SCENE := "res://scenes/main.tscn"


func _ready() -> void:
	theme = UiStyle.make_theme()
	var background := ColorRect.new()
	background.color = BACKGROUND_COLOR
	background.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(background)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side: String in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_" + side, 64)
	add_child(margin)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 16)
	margin.add_child(column)

	column.add_child(_label("Data check", 56, TEXT_COLOR))
	column.add_child(_label("Everything the game loaded from the data folder.", 24, UiStyle.TEXT_DIM))
	for line in _summary_lines():
		column.add_child(_label(line, 28, TEXT_COLOR))

	var errors: PackedStringArray = DataRegistry.validate()
	if errors.is_empty():
		column.add_child(_label("No data errors.", 28, SUCCESS_COLOR))
	else:
		column.add_child(_label("%d data errors:" % errors.size(), 28, ERROR_COLOR))
		for error in errors:
			column.add_child(_label(error, 22, ERROR_COLOR))
			push_error(error)

	var back := UiStyle.button("Back to menu (Esc)", 22)
	back.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	back.pressed.connect(_back)
	column.add_child(back)


func _back() -> void:
	get_tree().change_scene_to_file(MENU_SCENE)


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key != null and key.pressed and key.keycode == KEY_ESCAPE:
		get_viewport().set_input_as_handled()
		_back()


func _summary_lines() -> PackedStringArray:
	var element_names: PackedStringArray = []
	var sorted_elements: Array[ElementData] = []
	sorted_elements.assign(DataRegistry.elements.values())
	sorted_elements.sort_custom(func(a: ElementData, b: ElementData) -> bool: return a.ring_index < b.ring_index)
	for element in sorted_elements:
		element_names.append(element.display_name)

	var tower_names: PackedStringArray = []
	for tower: TowerData in DataRegistry.towers.values():
		tower_names.append(tower.display_name)

	var wave_count := 0
	for wave_set: WaveSet in DataRegistry.wave_sets.values():
		wave_count += wave_set.waves.size()

	return PackedStringArray([
		"Elements: %d (%s)" % [element_names.size(), ", ".join(element_names)],
		"Towers: %d (%s)" % [tower_names.size(), ", ".join(tower_names)],
		"Enemies: %d" % DataRegistry.enemies.size(),
		"Wave sets: %d, with %d waves in total" % [DataRegistry.wave_sets.size(), wave_count],
		"In-run tree nodes: %d" % DataRegistry.in_run_tree_nodes.size(),
		"Maps: %d" % DataRegistry.maps.size(),
	])


func _label(text: String, size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	return label
