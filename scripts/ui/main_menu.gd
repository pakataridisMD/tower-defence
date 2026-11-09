extends Control
## The title screen. Open the campaign, or pick a map and a difficulty level for a skirmish run; open
## the meta tree or the data check, or quit. Starts a run straight away when the game is launched
## with --autoplay (add --stage=<id> to play a campaign stage, open or not).

const GAME_SCENE := "res://scenes/game/game.tscn"
const META_TREE_SCENE := "res://scenes/meta/meta_tree.tscn"
const DATA_CHECK_SCENE := "res://scenes/debug/data_check.tscn"
const ART_TEST_SCENE := "res://scenes/demos/fire_tower_lighting.tscn"
const CAMPAIGN_SCENE := "res://scenes/campaign/campaign_map.tscn"
const RING_CENTER := Vector2(1340, 500)
const RING_RADIUS := 230.0
const ELEMENT_RADIUS := 44.0

var _font: Font
var _elements: Array[ElementData] = []
var _difficulty_text: Label


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
	_build_menu()


func _build_menu() -> void:
	var meta := Progress.meta
	var column := VBoxContainer.new()
	column.position = Vector2(160, 90)
	column.add_theme_constant_override("separation", 14)
	add_child(column)
	column.add_child(UiStyle.label("Tower Defence 2D", 72))
	column.add_child(UiStyle.label("Prototype build", 26, UiStyle.TEXT_DIM))
	_add_gap(column, 12)
	_add_button(column, _campaign_text(), 32, open_campaign)
	_add_gap(column, 4)
	column.add_child(UiStyle.label("Skirmish", 26))

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
	_difficulty_text = UiStyle.label("", 18, UiStyle.TEXT_DIM)
	column.add_child(_difficulty_text)
	_show_difficulty()
	if anything_locked:
		column.add_child(UiStyle.label("Locked maps and difficulty levels open up in the meta tree.", 18, UiStyle.TEXT_DIM))
	_add_button(column, "Play skirmish", 24, _play)
	_add_gap(column, 4)

	var points := meta.points()
	var meta_text := "Meta tree"
	if points > 0:
		meta_text += "  ·  %d point%s to spend" % [points, "" if points == 1 else "s"]
	_add_button(column, meta_text, 24, func() -> void: get_tree().change_scene_to_file(META_TREE_SCENE))
	_add_button(column, "Data check", 20, func() -> void: get_tree().change_scene_to_file(DATA_CHECK_SCENE))
	_add_button(column, "Art test: lit Fire tower", 20, func() -> void: get_tree().change_scene_to_file(ART_TEST_SCENE))
	_add_button(column, "Quit", 20, func() -> void: get_tree().quit())
	_add_gap(column, 12)
	column.add_child(UiStyle.label(_records_text(), 18, UiStyle.TEXT_DIM))


func _add_gap(column: VBoxContainer, height: float) -> void:
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, height)
	column.add_child(gap)


func _add_button(column: VBoxContainer, text: String, font_size: int, action: Callable) -> void:
	var button := UiStyle.button(text, font_size)
	button.custom_minimum_size = Vector2(420, 64 if font_size > 28 else 52)
	button.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	button.pressed.connect(action)
	column.add_child(button)


## A row of toggle buttons for picking one choice. Each choice is [id, name, unlocked, hint]. Locked
## choices are greyed out, and their hint says where to unlock them.
func _choice_row(title: String, choices: Array[Array], selected: StringName, pick: Callable) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	var label := UiStyle.label(title, 22, UiStyle.TEXT_DIM)
	label.custom_minimum_size = Vector2(130, 0)
	row.add_child(label)
	var group := ButtonGroup.new()
	for choice in choices:
		var id: StringName = choice[0]
		var unlocked: bool = choice[2]
		var button := UiStyle.choice_button(choice[1] if unlocked else "%s (locked)" % choice[1], group)
		button.custom_minimum_size = Vector2(150, 48)
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


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode in [KEY_ENTER, KEY_KP_ENTER, KEY_SPACE]:
		get_viewport().set_input_as_handled()
		_play()


## The element ring: neighbours fuse into hybrids, opposites are linked by a dashed line.
func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), UiStyle.BACKGROUND)
	if _elements.is_empty():
		return
	draw_arc(RING_CENTER, RING_RADIUS, 0.0, TAU, 96, Color(1, 1, 1, 0.12), 3.0, true)
	for element in _elements:
		var opposite := ElementRules.opposite_index(element.ring_index)
		if opposite > element.ring_index:
			draw_dashed_line(_ring_point(element.ring_index), _ring_point(opposite), Color(1, 1, 1, 0.1), 2.0, 12.0)
	for element in _elements:
		var at := _ring_point(element.ring_index)
		draw_circle(at, ELEMENT_RADIUS + 3.0, Color(0, 0, 0, 0.35))
		draw_circle(at, ELEMENT_RADIUS, element.color)
		_draw_element_name(element, at)
	var caption_at := RING_CENTER + Vector2(-330, RING_RADIUS + 150)
	draw_multiline_string(_font, caption_at,
		"Six elements on a ring. Neighbours fuse into hybrid towers. " +
		"Each wave resists its own element and takes 50% more damage from the opposite one.",
		HORIZONTAL_ALIGNMENT_CENTER, 660, 22, -1, UiStyle.TEXT_DIM)


## Puts the name just outside the circle: above or below it at the top and bottom of the
## ring, and beside it on the left and right.
func _draw_element_name(element: ElementData, at: Vector2) -> void:
	var outward := (at - RING_CENTER).normalized()
	var anchor := at + outward * (ELEMENT_RADIUS + 16.0)
	var width := _font.get_string_size(element.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 26).x
	var x := anchor.x - width * 0.5
	if outward.x > 0.3:
		x = anchor.x
	elif outward.x < -0.3:
		x = anchor.x - width
	var baseline := anchor.y + 9.0 + outward.y * 12.0
	draw_string(_font, Vector2(x, baseline), element.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 26, UiStyle.TEXT)


func _ring_point(ring_index: int) -> Vector2:
	return RING_CENTER + Vector2.from_angle(-PI / 2.0 + TAU * ring_index / ElementData.RING_SIZE) * RING_RADIUS
