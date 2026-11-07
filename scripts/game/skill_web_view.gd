class_name SkillWebView
extends Control
## Full-screen view of a skill tree. Left-click takes a node, right-click refunds it. Hovering a node
## that is out of reach highlights the nodes on the way to it and what they cost in all.
## Draws both the in-run web and the meta tree, which share the same TreeState rules.

signal close_requested
## Emitted when the player clicks a node. The owner decides whether it is taken.
signal node_clicked(id: StringName)
signal node_refund_requested(id: StringName)

const BACKDROP := Color(0.07, 0.08, 0.11, 0.97)
const LINK_TAKEN := Color(1, 1, 1, 0.85)
const LINK_OPEN := Color(1, 1, 1, 0.18)
const LINK_PATH := Color(0.95, 0.76, 0.31, 0.75)
const NODE_DIM := 0.3
## The tree is scaled to fit the screen below the title, up to this much.
const MAX_SCALE := 2.2
const FIT_TOP := 215.0
const FIT_SIDE := 140.0
const FIT_BOTTOM := 100.0
const LABEL_FONT_SIZE := 22


## A named, coloured part of a tree: an element in the in-run web, a branch in the meta tree.
class Region:
	var display_name: String
	var color: Color

	func _init(p_display_name: String, p_color: Color) -> void:
		display_name = p_display_name
		color = p_color


var tree: TreeState
## Keyed by the region id that nodes carry.
var regions: Dictionary[StringName, Region] = {}
var title := "Skill web"
## Short text under the title, such as how refunds work.
var subtitle := ""
## Word for the points this tree spends, as in "3 points to spend".
var points_noun := "point"
var close_text := "Close (T)"
## Returns true if a taken node may be refunded right now.
var can_refund: Callable = func(_id: StringName) -> bool: return false
## Tooltip status of a taken node that cannot be refunded right now.
var taken_text := "Taken."

var _hovered: StringName = &""
var _font: Font
var _time := 0.0
var _origin := Vector2.ZERO
var _scale := 1.0
var _close: Button
## Where each region's name is drawn (the start of the text's baseline), worked out in _layout().
var _label_spots: Dictionary[StringName, Vector2] = {}
## Extra buttons in the top right corner, left of the close button.
var _header_buttons: Array[Button] = []


## Regions for the in-run web: one per element, in the element's colour.
static func element_regions(elements: Dictionary[StringName, ElementData]) -> Dictionary[StringName, Region]:
	var result: Dictionary[StringName, Region] = {}
	for id in elements:
		result[id] = Region.new(elements[id].display_name, elements[id].color)
	return result


func _ready() -> void:
	_font = ThemeDB.fallback_font
	theme = UiStyle.make_theme()
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	resized.connect(_layout)
	_close = UiStyle.button(close_text, 20)
	_close.pressed.connect(func() -> void: close_requested.emit())
	add_child(_close)
	_layout()


func show_tree(p_tree: TreeState, p_regions: Dictionary[StringName, Region]) -> void:
	tree = p_tree
	regions = p_regions
	_hovered = &""
	show()
	_layout()
	queue_redraw()


## Adds a button to the top right corner, left of the close button.
func add_header_button(button: Button) -> void:
	_header_buttons.append(button)
	add_child(button)
	button.minimum_size_changed.connect(_layout)
	_layout()


## Where a node is drawn, in this view's coordinates.
func screen_position(id: StringName) -> Vector2:
	return _to_screen(tree.graph.node(id).position)


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


# --- Layout ----------------------------------------------------------------------

## Scales and centres the tree so it fills the space below the title.
func _layout() -> void:
	if _close == null:
		return
	var right := size.x - 32.0
	var buttons: Array[Button] = [_close]
	buttons.append_array(_header_buttons)
	for button in buttons:
		var width := button.get_combined_minimum_size().x
		button.position = Vector2(right - width, 24.0)
		right -= width + 16.0
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
	_place_region_labels()


## Puts each region's name beside its node farthest from the start, on the side that covers the
## fewest nodes and links, preferring the side facing away from the start.
func _place_region_labels() -> void:
	_label_spots.clear()
	var farthest: Dictionary[StringName, TreeNodeData] = {}
	for id in tree.graph.ids():
		var data := tree.graph.node(id)
		if not regions.has(data.region):
			continue
		var best: TreeNodeData = farthest.get(data.region)
		if best == null or data.position.length() > best.position.length():
			farthest[data.region] = data
	for region_id in farthest:
		var data := farthest[region_id]
		var text_width := _font.get_string_size(regions[region_id].display_name, HORIZONTAL_ALIGNMENT_LEFT, -1,
				LABEL_FONT_SIZE).x
		var box_size := Vector2(text_width, LABEL_FONT_SIZE)
		var at := _to_screen(data.position)
		var outward := data.position.normalized()
		var best_box := Rect2()
		var best_score := INF
		for step in 16:
			var direction := Vector2.from_angle(TAU * step / 16.0)
			var reach := _radius(data) + 10.0 + absf(direction.x) * box_size.x * 0.5 + absf(direction.y) * box_size.y * 0.5
			var box := Rect2(at + direction * reach - box_size * 0.5, box_size)
			var score := _label_clutter(box) * 10.0 + 1.0 - direction.dot(outward)
			if score < best_score:
				best_score = score
				best_box = box
		_label_spots[region_id] = Vector2(best_box.position.x, best_box.end.y - 5.0)


## How badly a label box would cover nodes and links, or stick out of the space below the title.
func _label_clutter(box: Rect2) -> float:
	var grown := box.grow(6.0)
	var clutter := 0.0
	for id in tree.graph.ids():
		var data := tree.graph.node(id)
		var center := _to_screen(data.position)
		if center.clamp(grown.position, grown.end).distance_to(center) < _radius(data) + 4.0:
			clutter += 3.0
		for other in tree.graph.neighbours(id):
			if String(other) > String(id) and _segment_hits_rect(center, _to_screen(tree.graph.node(other).position), grown):
				clutter += 1.0
	var free_area := Rect2(Vector2(0.0, FIT_TOP - 60.0), size - Vector2(0.0, FIT_TOP - 60.0))
	if not free_area.encloses(box):
		clutter += 5.0
	return clutter


static func _segment_hits_rect(a: Vector2, b: Vector2, rect: Rect2) -> bool:
	if rect.has_point(a) or rect.has_point(b):
		return true
	var corners: Array[Vector2] = [rect.position, Vector2(rect.end.x, rect.position.y), rect.end, Vector2(rect.position.x, rect.end.y)]
	for i in 4:
		if Geometry2D.segment_intersects_segment(a, b, corners[i], corners[(i + 1) % 4]) != null:
			return true
	return false


func _to_screen(tree_position: Vector2) -> Vector2:
	return _origin + tree_position * _scale


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
	var result: Array[Color] = []
	if data.kind == TreeNodeData.Kind.KEYSTONE:
		result.append(UiStyle.KEYSTONE)
	elif data.kind == TreeNodeData.Kind.START:
		result.append(Color.WHITE)
	elif regions.has(data.region):
		result.append(regions[data.region].color)
	else:
		# Bridges take the colours of the regions they join.
		for other in tree.graph.neighbours(data.id):
			var neighbour := tree.graph.node(other)
			if regions.has(neighbour.region) and not result.has(regions[neighbour.region].color):
				result.append(regions[neighbour.region].color)
	if result.is_empty():
		result.append(Color.WHITE)
	return result


# --- Drawing ---------------------------------------------------------------------

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), BACKDROP)
	if tree == null:
		return
	draw_string(_font, Vector2(48, 64), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, UiStyle.TEXT)
	var points_text := "%d %s%s to spend" % [tree.points, points_noun, "" if tree.points == 1 else "s"]
	draw_string(_font, Vector2(48, 104), points_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, UiStyle.GOLD)
	if not subtitle.is_empty():
		draw_multiline_string(_font, Vector2(48, 138), subtitle, HORIZONTAL_ALIGNMENT_LEFT, size.x - 96.0, 18, -1,
				UiStyle.TEXT_DIM)
	var path: Array[StringName] = []
	if not _hovered.is_empty():
		path = tree.path_to(_hovered)
	_draw_links(path)
	_draw_region_labels()
	for id in tree.graph.ids():
		_draw_node(tree.graph.node(id))
	if not _hovered.is_empty():
		_draw_tooltip(tree.graph.node(_hovered), path)


func _draw_links(path: Array[StringName]) -> void:
	for id in tree.graph.ids():
		for other in tree.graph.neighbours(id):
			if String(other) < String(id):
				continue
			var both_taken := tree.is_allocated(id) and tree.is_allocated(other)
			draw_line(_to_screen(tree.graph.node(id).position), _to_screen(tree.graph.node(other).position),
					LINK_TAKEN if both_taken else LINK_OPEN, 4.0 if both_taken else 2.0, true)
	for i in range(1, path.size()):
		draw_line(screen_position(path[i - 1]), screen_position(path[i]), LINK_PATH, 5.0, true)


func _draw_region_labels() -> void:
	for region_id in _label_spots:
		var region := regions[region_id]
		var at := _label_spots[region_id]
		draw_string_outline(_font, at, region.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_FONT_SIZE, 8, BACKDROP)
		draw_string(_font, at, region.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_FONT_SIZE, Color(region.color, 0.9))


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


## Fills the right half of a circle, for nodes that join two regions.
func draw_circle_arc_fill(at: Vector2, radius: float, color: Color) -> void:
	var half := PackedVector2Array([at + Vector2(0, -radius)])
	for i in range(1, 16):
		half.append(at + Vector2.from_angle(-PI / 2.0 + PI * i / 16.0) * radius)
	half.append(at + Vector2(0, radius))
	draw_colored_polygon(half, color)


func _draw_tooltip(data: TreeNodeData, path: Array[StringName]) -> void:
	var lines: Array[String] = [data.description]
	var status := _status(data, path)
	if not status.is_empty():
		lines.append(status)
	var width := 440.0
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


## What clicking the node would do, or what stands in the way.
func _status(data: TreeNodeData, path: Array[StringName]) -> String:
	if data.kind == TreeNodeData.Kind.START:
		return ""
	if tree.is_allocated(data.id):
		return "Taken. Right-click to refund." if can_refund.call(data.id) else taken_text
	if tree.is_locked(data.id):
		return "Locked. Unlock it in the meta tree."
	if tree.can_allocate(data.id):
		return "Click to take (%s)." % _points(data.cost)
	if path.size() > 2:
		var total := 0
		for i in range(1, path.size()):
			total += tree.graph.node(path[i]).cost
		var steps := path.size() - 2
		return "Take %d node%s on the way first: %s in all." % [steps, "" if steps == 1 else "s", _points(total)]
	if path.size() == 2:
		return "Needs %s." % _points(data.cost)
	return "Out of reach."


func _points(amount: int) -> String:
	return "%d %s%s" % [amount, points_noun, "" if amount == 1 else "s"]


func _wrapped_line_count(lines: Array[String], width: float) -> int:
	var total := 0
	for line in lines:
		var text_width := _font.get_string_size(line, HORIZONTAL_ALIGNMENT_LEFT, -1, 19).x
		total += maxi(1, ceili(text_width / width))
	return total
