extends Control
## The title screen. Open the campaign, or pick a map and a difficulty level for a skirmish run; open
## the meta tree or the data check, or quit. Starts a run straight away when the game is launched
## with --autoplay (add --stage=<id> to play a campaign stage, open or not).

const GAME_SCENE := "res://scenes/game/game.tscn"
const META_TREE_SCENE := "res://scenes/meta/meta_tree.tscn"
const DATA_CHECK_SCENE := "res://scenes/debug/data_check.tscn"
const ART_TEST_SCENE := "res://scenes/demos/fire_tower_lighting.tscn"
const CAMPAIGN_SCENE := "res://scenes/campaign/campaign_map.tscn"
## The backdrop is drawn at three screen pixels per picture pixel.
const BACKDROP_SCALE := 3.0
## The ring the six base towers stand on in the backdrop, in backdrop pixels. The same numbers are
## in tools/art/gen_ui_art.py, which paints the backdrop.
const RING_CENTER := Vector2(452, 168)
const RING_RADII := Vector2(104, 70)
const BUTTON_WIDTH := 540.0

var _font: Font
var _elements: Array[ElementData] = []
var _difficulty_text: Label
var _time := 0.0
## Soft lights that breathe over the towers in the backdrop.
var _glows: Control


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if OS.get_cmdline_user_args().has("--autoplay"):
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--stage="):
				Progress.active_stage = StringName(arg.trim_prefix("--stage="))
		get_tree().change_scene_to_file.call_deferred(GAME_SCENE)
		return
	_font = ThemeDB.fallback_font
	theme = UiStyle.make_theme()
	_elements.assign(DataRegistry.elements.values())
	_elements.sort_custom(func(a: ElementData, b: ElementData) -> bool: return a.ring_index < b.ring_index)
	_build_scene()
	_build_menu()


func _process(delta: float) -> void:
	_time += delta
	if _glows != null:
		_glows.queue_redraw()


## The picture behind the menu, the breathing lights on it and the element names under the towers.
func _build_scene() -> void:
	var backdrop := Control.new()
	backdrop.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	backdrop.mouse_filter = Control.MOUSE_FILTER_IGNORE
	backdrop.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	backdrop.draw.connect(_draw_backdrop.bind(backdrop))
	add_child(backdrop)
	_glows = Control.new()
	_glows.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_glows.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_glows.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var additive := CanvasItemMaterial.new()
	additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	_glows.material = additive
	_glows.draw.connect(_draw_glows)
	add_child(_glows)
	var names := Control.new()
	names.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	names.mouse_filter = Control.MOUSE_FILTER_IGNORE
	names.draw.connect(_draw_names.bind(names))
	add_child(names)


func _build_menu() -> void:
	var meta := Progress.meta
	var logo := UiStyle.art("logo")
	if logo != null:
		var title := TextureRect.new()
		title.texture = logo
		title.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		title.stretch_mode = TextureRect.STRETCH_SCALE
		title.position = Vector2(66, 34)
		title.size = logo.get_size() * BACKDROP_SCALE
		title.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(title)
	else:
		var title := UiStyle.label("Tower Defence 2D", 72)
		title.position = Vector2(72, 30)
		add_child(title)
	var tagline := UiStyle.label("Six elements, one road. Prototype build.", 20, UiStyle.TEXT_DIM)
	tagline.position = Vector2(78, 130)
	add_child(tagline)

	var panel := PanelContainer.new()
	panel.position = Vector2(72, 172)
	panel.add_theme_stylebox_override("panel", UiStyle.panel_box(24, 20))
	add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	panel.add_child(column)
	_add_button(column, _campaign_text(), 30, "C", open_campaign)
	_add_gap(column, 2)
	column.add_child(UiStyle.label("Skirmish", 24))

	var anything_locked := false
	var maps: Array[Array] = []
	for map in meta.maps_in_order():
		var unlocked := meta.is_map_unlocked(map.id)
		anything_locked = anything_locked or not unlocked
		maps.append([map.id, map.display_name, unlocked, "" if unlocked else _hint(&"unlocks_maps", map.id)])
	column.add_child(_choice_row("Map", maps, meta.selected_map, Progress.select_map))

	var levels: Array[Array] = []
	for level in meta.difficulties_in_order():
		var unlocked := meta.is_difficulty_unlocked(level.id)
		anything_locked = anything_locked or not unlocked
		var hint := level.description if unlocked else _hint(&"unlocks_difficulties", level.id)
		levels.append([level.id, level.display_name, unlocked, hint])
	column.add_child(_choice_row("Difficulty", levels, meta.selected_difficulty, _pick_difficulty))
	_difficulty_text = _note("")
	column.add_child(_difficulty_text)
	_show_difficulty()
	if anything_locked:
		column.add_child(_note("Locked maps and difficulty levels open up in the meta tree."))
	_add_button(column, "Play skirmish", 24, "Enter", _play)
	_add_gap(column, 2)

	var points := meta.points()
	var meta_text := "Meta tree"
	if points > 0:
		meta_text += "  ·  %d point%s to spend" % [points, "" if points == 1 else "s"]
	_add_button(column, meta_text, 24, "M", open_meta_tree)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	column.add_child(row)
	for entry: Array in [["Data check", DATA_CHECK_SCENE], ["Art test", ART_TEST_SCENE]]:
		var scene: String = entry[1]
		var small := UiStyle.button(entry[0], 18)
		small.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		small.pressed.connect(func() -> void: get_tree().change_scene_to_file(scene))
		row.add_child(small)
	var quit := UiStyle.button("Quit", 18)
	quit.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	quit.pressed.connect(func() -> void: get_tree().quit())
	row.add_child(quit)
	_add_gap(column, 2)
	column.add_child(_note(_records_text()))


## A dim line of small text that wraps inside the menu panel.
func _note(text: String) -> Label:
	var label := UiStyle.label(text, 17, UiStyle.TEXT_DIM)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	label.custom_minimum_size = Vector2(BUTTON_WIDTH, 0)
	return label


func _add_gap(column: VBoxContainer, height: float) -> void:
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, height)
	column.add_child(gap)


## A wide menu button that shows its key in the corner.
func _add_button(column: VBoxContainer, text: String, font_size: int, key: String, action: Callable) -> void:
	var button := KeyButton.new()
	button.text = text
	button.key_text = key
	button.focus_mode = Control.FOCUS_NONE
	button.add_theme_font_size_override("font_size", font_size)
	button.custom_minimum_size = Vector2(BUTTON_WIDTH, 64 if font_size > 28 else 52)
	button.pressed.connect(action)
	column.add_child(button)


## A row of toggle buttons for picking one choice. Each choice is [id, name, unlocked, hint]. Locked
## choices are greyed out, and their hint says where to unlock them.
func _choice_row(title: String, choices: Array[Array], selected: StringName, pick: Callable) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	var label := UiStyle.label(title, 22, UiStyle.TEXT_DIM)
	label.custom_minimum_size = Vector2(110, 0)
	row.add_child(label)
	var group := ButtonGroup.new()
	for choice in choices:
		var id: StringName = choice[0]
		var unlocked: bool = choice[2]
		var button := UiStyle.choice_button(choice[1] if unlocked else "%s (locked)" % choice[1], group)
		button.custom_minimum_size = Vector2(134, 46)
		button.button_pressed = id == selected
		button.disabled = not unlocked
		button.tooltip_text = choice[3]
		button.toggled.connect(func(on: bool) -> void:
			if on:
				pick.call(id))
		row.add_child(button)
	return row


func _pick_difficulty(id: StringName) -> void:
	Progress.select_difficulty(id)
	_show_difficulty()


func _show_difficulty() -> void:
	var picked: DifficultyData = DataRegistry.difficulties.get(Progress.meta.selected_difficulty)
	_difficulty_text.text = picked.description if picked != null else ""


## Where to unlock a locked map or difficulty level, such as "Unlock it in the meta tree: Hard Mode
## (Expeditions)."
func _hint(field: StringName, id: StringName) -> String:
	var node := Progress.meta.unlocked_by(field, id)
	if node == null:
		return ""
	var branch: String = MetaProgress.BRANCH_NAMES.get(node.region, "")
	if branch.is_empty():
		return "Unlock it in the meta tree: %s." % node.display_name
	return "Unlock it in the meta tree: %s (%s)." % [node.display_name, branch]


func _records_text() -> String:
	var profile := Progress.meta.profile
	if profile.runs_played == 0:
		return "No runs yet. Every run earns meta points, won or lost."
	return "Runs %d  ·  Wins %d  ·  Best %d waves  ·  %d enemies defeated" % [
		profile.runs_played, profile.runs_won, profile.best_waves, profile.enemies_killed]


func _play() -> void:
	Progress.play_skirmish()
	get_tree().change_scene_to_file(GAME_SCENE)


func open_campaign() -> void:
	get_tree().change_scene_to_file(CAMPAIGN_SCENE)


func open_meta_tree() -> void:
	get_tree().change_scene_to_file(META_TREE_SCENE)


func _campaign_text() -> String:
	var meta := Progress.meta
	var earned := 0
	var total := 0
	for campaign in meta.campaigns_in_order():
		earned += meta.campaign_stars(campaign)
		total += campaign.stages.size() * 3
	if earned == 0:
		return "Campaign"
	return "Campaign  ·  %d / %d ★" % [earned, total]


## Enter or Space plays a skirmish, C opens the campaign and M the meta tree.
func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_ENTER, KEY_KP_ENTER, KEY_SPACE:
			_play()
		KEY_C:
			open_campaign()
		KEY_M:
			open_meta_tree()
		_:
			return
	get_viewport().set_input_as_handled()


# --- The picture -----------------------------------------------------------------

## Where an element's tower stands in the backdrop, in screen pixels.
func _ring_point(ring_index: int) -> Vector2:
	var angle := -PI / 2.0 + TAU * ring_index / ElementData.RING_SIZE
	return (RING_CENTER + Vector2(cos(angle), sin(angle)) * RING_RADII) * BACKDROP_SCALE


func _draw_backdrop(on: Control) -> void:
	on.draw_rect(Rect2(Vector2.ZERO, size), UiStyle.BACKGROUND)
	var picture := UiStyle.art("menu_backdrop")
	if picture != null:
		on.draw_texture_rect(picture, Rect2(Vector2.ZERO, picture.get_size() * BACKDROP_SCALE), false)
		return
	# Without the picture: the ring as plain circles.
	for element in _elements:
		on.draw_circle(_ring_point(element.ring_index) - Vector2(0, 60), 44.0, element.color)


## A soft light over every tower that swells and fades, each in its own time.
func _draw_glows() -> void:
	var glow := TreeArt.texture("glow")
	if glow == null or UiStyle.art("menu_backdrop") == null:
		return
	for element in _elements:
		var breath := 0.5 + 0.5 * sin(_time * 1.3 + element.ring_index * 1.9)
		var reach := glow.get_size() * BACKDROP_SCALE * (1.5 + 0.25 * breath)
		var at := _ring_point(element.ring_index) - Vector2(0, 46.0 * BACKDROP_SCALE)
		_glows.draw_texture_rect(glow, Rect2(at - reach * 0.5, reach), false, Color(element.color.lightened(0.2), 0.16 + 0.12 * breath))


## The element names under their towers, and what the ring means.
func _draw_names(on: Control) -> void:
	for element in _elements:
		var at := _ring_point(element.ring_index) + Vector2(0, 30)
		var width := _font.get_string_size(element.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 24).x
		_outlined(on, Vector2(at.x - width * 0.5, at.y), element.display_name, 24, element.color.lightened(0.45))
	var lines: PackedStringArray = [
		"Six elements on a ring. Neighbours fuse into dual towers, and three make a triple.",
		"Each wave resists its own element and takes 50% more damage from the opposite one.",
	]
	var middle := RING_CENTER.x * BACKDROP_SCALE
	for i in lines.size():
		var width := _font.get_string_size(lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 21).x
		_outlined(on, Vector2(middle - width * 0.5, 1012.0 + i * 30.0), lines[i], 21, UiStyle.TEXT)


func _outlined(on: Control, at: Vector2, text: String, font_size: int, color: Color) -> void:
	on.draw_string_outline(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, 8, Color(0.02, 0.03, 0.06, 0.85))
	on.draw_string(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)
