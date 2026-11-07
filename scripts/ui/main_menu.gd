extends Control
## The title screen. Starts a run, opens the data check, or quits. Starts a run straight away
## when the game is launched with --autoplay.

const GAME_SCENE := "res://scenes/game/game.tscn"
const DATA_CHECK_SCENE := "res://scenes/debug/data_check.tscn"
const RING_CENTER := Vector2(1340, 500)
const RING_RADIUS := 230.0
const ELEMENT_RADIUS := 44.0

var _font: Font
var _elements: Array[ElementData] = []


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if OS.get_cmdline_user_args().has("--autoplay"):
		_play.call_deferred()
		return
	_font = ThemeDB.fallback_font
	theme = UiStyle.make_theme()
	_elements.assign(DataRegistry.elements.values())
	_elements.sort_custom(func(a: ElementData, b: ElementData) -> bool: return a.ring_index < b.ring_index)
	_build_menu()


func _build_menu() -> void:
	var column := VBoxContainer.new()
	column.position = Vector2(160, 250)
	column.add_theme_constant_override("separation", 16)
	add_child(column)
	column.add_child(UiStyle.label("Tower Defence 2D", 72))
	column.add_child(UiStyle.label("Prototype build", 26, UiStyle.TEXT_DIM))
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 40)
	column.add_child(gap)
	_add_button(column, "Play", 32, _play)
	_add_button(column, "Data check", 24, func() -> void: get_tree().change_scene_to_file(DATA_CHECK_SCENE))
	_add_button(column, "Quit", 24, func() -> void: get_tree().quit())


func _add_button(column: VBoxContainer, text: String, font_size: int, action: Callable) -> void:
	var button := UiStyle.button(text, font_size)
	button.custom_minimum_size = Vector2(360, 64 if font_size > 28 else 54)
	button.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	button.pressed.connect(action)
	column.add_child(button)


func _play() -> void:
	get_tree().change_scene_to_file(GAME_SCENE)


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
