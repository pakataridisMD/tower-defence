class_name SkillWebView
extends Control
## Full-screen view of a skill tree. Left-click takes a node, right-click refunds it.
## Used for the in-run web; the meta tree screen reuses it through the same TreeState rules.

signal close_requested
## Emitted when the player clicks a node. The owner decides whether it is taken.
signal node_clicked(id: StringName)
signal node_refund_requested(id: StringName)

const BACKDROP := Color(0.07, 0.08, 0.11, 0.97)
const LINK_TAKEN := Color(1, 1, 1, 0.85)
const LINK_OPEN := Color(1, 1, 1, 0.18)
const NODE_DIM := 0.3
## The tree is scaled to fit the screen below the title, up to this much.
const MAX_SCALE := 2.2
const FIT_TOP := 215.0
const FIT_SIDE := 140.0
const FIT_BOTTOM := 100.0

var tree: TreeState
var elements: Dictionary[StringName, ElementData] = {}
var title := "Skill web"
## Returns true if a taken node may be refunded right now.
var can_refund: Callable = func(_id: StringName) -> bool: return false
## Short line under the title, such as how refunds work.
var subtitle := ""

var _hovered: StringName = &""
var _font: Font
var _time := 0.0
var _origin := Vector2.ZERO
var _scale := 1.0
var _close: Button


func _ready() -> void:
	_font = ThemeDB.fallback_font
	theme = UiStyle.make_theme()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	resized.connect(_layout)
	_close = UiStyle.button("Close (T)", 20)
	_close.pressed.connect(func() -> void: close_requested.emit())
	add_child(_close)


func show_tree(p_tree: TreeState, p_elements: Dictionary[StringName, ElementData]) -> void:
	tree = p_tree
	elements = p_elements
	_hovered = &""
	show()
	_layout()
	queue_redraw()


func _process(delta: float) -> void:
	if visible:
		_time += delta
		queue_redraw()


func _gui_input(event: InputEvent) -> void:
	if tree == null:
		return
	if event is InputEventMouseMotion:
		_hovered = _node_at(event.position)
	elif event is InputEventMouseButton and event.pressed and not _hovered.is_empty():
		if event.button_index == MOUSE_BUTTON_LEFT:
			node_clicked.emit(_hovered)
		elif event.button_index == MOUSE_BUTTON_RIGHT:
			node_refund_requested.emit(_hovered)
		accept_event()


## Scales and centres the tree so it fills the space below the title.
func _layout() -> void:
	_close.position = Vector2(size.x - _close.size.x - 32.0, 24.0)
	if tree == null or tree.graph.size() == 0:
		return
	var ids := tree.graph.ids()
	var bounds := Rect2(tree.graph.node(ids[0]).position, Vector2.ZERO)
	for id in ids:
		bounds = bounds.expand(tree.graph.node(id).position)
	var area := Rect2(Vector2(FIT_SIDE, FIT_TOP), size - Vector2(FIT_SIDE * 2.0, FIT_TOP + FIT_BOTTOM))
	var span := bounds.size.max(Vector2.ONE)
	_scale = minf(MAX_SCALE, minf(area.size.x / span.x, area.size.y / span.y))
	_origin = area.get_center() - bounds.get_center() * _scale


func _to_screen(tree_position: Vector2) -> Vector2:
	return _origin + tree_position * _scale


## Where a node is drawn, in this view's coordinates.
func screen_position(id: StringName) -> Vector2:
	return _to_screen(tree.graph.node(id).position)


func _node_at(point: Vector2) -> StringName:
	for id in tree.graph.ids():
		var data := tree.graph.node(id)
		if point.distance_to(_to_screen(data.position)) <= _radius(data) + 6.0:
			return id
	return &""


func _radius(data: TreeNodeData) -> float:
	match data.kind:
		TreeNodeData.Kind.START:
			return 26.0
		TreeNodeData.Kind.ENTRY, TreeNodeData.Kind.NOTABLE:
			return 21.0
		TreeNodeData.Kind.BRIDGE:
			return 18.0
		TreeNodeData.Kind.KEYSTONE:
			return 24.0
	return 14.0


func _colors(data: TreeNodeData) -> Array[Color]:
	if data.kind == TreeNodeData.Kind.KEYSTONE:
		return [UiStyle.KEYSTONE]
	if data.kind == TreeNodeData.Kind.START:
		return [Color.WHITE]
	if not data.element.is_empty() and elements.has(data.element):
		return [elements[data.element].color]
	# Bridges take the colours of the regions they join.
	var result: Array[Color] = []
	for other in tree.graph.neighbours(data.id):
		var neighbour := tree.graph.node(other)
		if not neighbour.element.is_empty() and elements.has(neighbour.element):
			var color: Color = elements[neighbour.element].color
			if not result.has(color):
				result.append(color)
	return result if not result.is_empty() else [Color.WHITE]


func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BACKDROP)
	if tree == null:
		return
	draw_string(_font, Vector2(48, 64), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, UiStyle.TEXT)
	var points_text := "%d point%s to spend" % [tree.points, "" if tree.points == 1 else "s"]
	draw_string(_font, Vector2(48, 104), points_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, UiStyle.GOLD)
	if not subtitle.is_empty():
		draw_multiline_string(_font, Vector2(48, 138), subtitle, HORIZONTAL_ALIGNMENT_LEFT, 1300, 18, -1, UiStyle.TEXT_DIM)
	_draw_links()
	_draw_region_labels()
	for id in tree.graph.ids():
		_draw_node(tree.graph.node(id))
	if not _hovered.is_empty():
		_draw_tooltip(tree.graph.node(_hovered))


func _draw_links() -> void:
	for id in tree.graph.ids():
		for other in tree.graph.neighbours(id):
			if String(other) < String(id):
				continue
			var both_taken := tree.is_allocated(id) and tree.is_allocated(other)
			draw_line(_to_screen(tree.graph.node(id).position), _to_screen(tree.graph.node(other).position),
					LINK_TAKEN if both_taken else LINK_OPEN, 4.0 if both_taken else 2.0, true)


## Names each element region just beyond its notable, on the side away from the start.
func _draw_region_labels() -> void:
	for id in tree.graph.ids():
		var data := tree.graph.node(id)
		if data.kind != TreeNodeData.Kind.NOTABLE or not elements.has(data.element):
			continue
		var element: ElementData = elements[data.element]
		var outward := data.position.normalized()
		var at := _to_screen(data.position) + outward * (_radius(data) + 40.0) + Vector2(-60, 8)
		draw_string_outline(_font, at, element.display_name, HORIZONTAL_ALIGNMENT_CENTER, 120, 22, 8, BACKDROP)
		draw_string(_font, at, element.display_name, HORIZONTAL_ALIGNMENT_CENTER, 120, 22, Color(element.color, 0.9))


func _draw_node(data: TreeNodeData) -> void:
	var at := _to_screen(data.position)
	var radius := _radius(data)
	var taken := tree.is_allocated(data.id)
	var open := tree.can_allocate(data.id)
	var colors := _colors(data)
	var strength := 1.0 if taken else (0.75 if open else NODE_DIM)
	if tree.is_locked(data.id):
		strength = 0.15

	if open:
		var pulse := 0.5 + 0.5 * sin(_time * 4.0)
		draw_circle(at, radius + 7.0 + pulse * 3.0, Color(UiStyle.GOLD, 0.25 + 0.2 * pulse))
	if data.kind == TreeNodeData.Kind.KEYSTONE:
		var diamond := PackedVector2Array([at + Vector2(0, -radius), at + Vector2(radius, 0), at + Vector2(0, radius), at + Vector2(-radius, 0)])
		draw_colored_polygon(diamond, Color(colors[0] * strength, 1.0))
	else:
		draw_circle(at, radius, Color(colors[0] * strength, 1.0))
		if colors.size() > 1:
			draw_circle_arc_fill(at, radius, Color(colors[1] * strength, 1.0))
	var ring := Color.WHITE if taken else Color(1, 1, 1, 0.35)
	draw_arc(at, radius + 1.0, 0.0, TAU, 40, ring, 3.0 if taken else 1.5, true)
	if data.id == _hovered:
		draw_arc(at, radius + 5.0, 0.0, TAU, 40, UiStyle.GOLD, 2.0, true)


## Fills the right half of a circle, for nodes that join two elements.
func draw_circle_arc_fill(at: Vector2, radius: float, color: Color) -> void:
	var half := PackedVector2Array([at + Vector2(0, -radius)])
	for i in range(1, 16):
		half.append(at + Vector2.from_angle(-PI / 2.0 + PI * i / 16.0) * radius)
	half.append(at + Vector2(0, radius))
	draw_colored_polygon(half, color)


func _draw_tooltip(data: TreeNodeData) -> void:
	var lines: Array[String] = []
	var status := ""
	if tree.is_allocated(data.id):
		status = "Taken. Right-click to refund." if can_refund.call(data.id) else "Taken."
	elif tree.is_locked(data.id):
		status = "Locked. Unlock it in the meta tree."
	elif tree.can_allocate(data.id):
		status = "Click to take (%d point%s)." % [data.cost, "" if data.cost == 1 else "s"]
	elif tree.points < data.cost:
		status = "Needs %d point%s." % [data.cost, "" if data.cost == 1 else "s"]
	else:
		status = "Take a connected node first."
	lines.append(data.description)
	lines.append(status)

	var width := 420.0
	var node_at := _to_screen(data.position)
	var at := node_at + Vector2(_radius(data) + 16.0, -20.0)
	if at.x + width > size.x - 16.0:
		at.x = node_at.x - _radius(data) - 16.0 - width
	var height := 50.0 + 26.0 * _wrapped_line_count(lines, width - 28.0)
	at.y = clampf(at.y, 16.0, size.y - height - 16.0)
	var box := Rect2(at, Vector2(width, height))
	draw_rect(box, Color(UiStyle.PANEL, 0.98))
	draw_rect(box, UiStyle.PANEL_BORDER, false, 2.0)
	draw_string(_font, at + Vector2(14, 32), data.display_name, HORIZONTAL_ALIGNMENT_LEFT, width - 28.0, 24, UiStyle.TEXT)
	var y := at.y + 62.0
	for i in lines.size():
		var color := UiStyle.TEXT if i == 0 else UiStyle.GOLD
		draw_multiline_string(_font, Vector2(at.x + 14, y), lines[i], HORIZONTAL_ALIGNMENT_LEFT, width - 28.0, 19, -1, color)
		y += 26.0 * _wrapped_line_count([lines[i]], width - 28.0)


func _wrapped_line_count(lines: Array[String], width: float) -> int:
	var total := 0
	for line in lines:
		var text_width := _font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, 19).x
		total += maxi(1, ceili(text_width / width))
	return total
