class_name SkillWebView
extends Control
## Full-screen view of a skill tree. Left-click takes a node, right-click refunds it. Hovering a node
## that is out of reach highlights the nodes on the way to it and what they cost in all.
## Draws both the in-run web and the meta tree, which share the same TreeState rules, in pixel art
## from TreeArt: a starry backdrop, gems in each region's colour, tower portraits on nodes that unlock towers.

signal close_requested
## Emitted when the player clicks a node. The owner decides whether it is taken.
signal node_clicked(id: StringName)
signal node_refund_requested(id: StringName)

const BACKDROP := Color(0.03, 0.035, 0.055, 0.98)
const LINK_GROOVE := Color("07080d")
const LINK_OPEN := Color("2c3248")
const LINK_NEAR := Color("444c68")
const LINK_PATH := Color(0.95, 0.76, 0.31, 0.95)
const START_COLOR := Color(1.0, 0.9, 0.68)
## Stars that twinkle over the backdrop.
const STAR_COUNT := 46
const BURST_SECONDS := 0.7
## The tree is scaled to fit the screen below the title, up to this much.
const MAX_SCALE := 2.2
const FIT_TOP := 215.0
const FIT_SIDE := 140.0
const FIT_BOTTOM := 100.0
const LABEL_FONT_SIZE := 22
## Room for a region's emblem left of its name.
const EMBLEM_GAP := 32.0


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
## Twinkling stars: x and y as fractions of the view, and a phase.
var _stars: Array[Vector3] = []
## Which nodes were taken last frame, to set off a burst when one is taken.
var _taken_before: Dictionary[StringName, bool] = {}
## Bursts from nodes just taken: where, colour, size and age.
var _bursts: Array[Dictionary] = []
var _panel: StyleBox


## Regions for the in-run web: one per element, in the element's colour.
static func element_regions(elements: Dictionary[StringName, ElementData]) -> Dictionary[StringName, Region]:
	var result: Dictionary[StringName, Region] = {}
	for id in elements:
		result[id] = Region.new(elements[id].display_name, elements[id].color)
	return result


func _ready() -> void:
	_font = ThemeDB.fallback_font
	theme = UiStyle.make_theme()
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	for i in STAR_COUNT:
		_stars.append(Vector3(rng.randf(), rng.randf(), rng.randf() * TAU))
	var panel_texture := TreeArt.texture("panel")
	if panel_texture != null:
		var box := StyleBoxTexture.new()
		box.texture = panel_texture
		box.set_texture_margin_all(12.0)
		_panel = box
	else:
		var flat := StyleBoxFlat.new()
		flat.bg_color = Color(UiStyle.PANEL, 0.98)
		flat.border_color = UiStyle.PANEL_BORDER
		flat.set_border_width_all(2)
		_panel = flat
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
	_bursts.clear()
	_taken_before = _taken_now()
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
	if not visible:
		return
	_time += delta
	if tree != null:
		var taken := _taken_now()
		for id in taken:
			if not _taken_before.has(id):
				var data := tree.graph.node(id)
				_bursts.append({"at": screen_position(id), "color": _node_color(data), "age": 0.0, "radius": _radius(data)})
		_taken_before = taken
	for burst in _bursts:
		burst["age"] += delta
	_bursts = _bursts.filter(func(burst: Dictionary) -> bool: return burst["age"] < BURST_SECONDS)
	queue_redraw()


func _taken_now() -> Dictionary[StringName, bool]:
	var result: Dictionary[StringName, bool] = {}
	if tree != null:
		for id in tree.allocated_ids():
			result[id] = true
	return result


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
		var box_size := Vector2(text_width + EMBLEM_GAP, LABEL_FONT_SIZE + 4.0)
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
	return TreeArt.radius(data)


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
# Pixel art from TreeArt, one art pixel to 2x2 screen pixels. Sprites are placed on even screen
# pixels so the art pixels stay square.

func _draw() -> void:
	_draw_backdrop()
	if tree == null:
		return
	_draw_auras()
	_draw_rings()
	_draw_stars()
	draw_string(_font, Vector2(48, 64), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 40, UiStyle.TEXT)
	var points_text := "%d %s%s to spend" % [tree.points, points_noun, "" if tree.points == 1 else "s"]
	_draw_art(TreeArt.icon(&"star"), Vector2(46, 78))
	draw_string(_font, Vector2(80, 104), points_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, UiStyle.GOLD)
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
	_draw_bursts()
	if not _hovered.is_empty():
		_draw_tooltip(tree.graph.node(_hovered), path)


static func _snap(point: Vector2) -> Vector2:
	return (point * 0.5).round() * 2.0


## Draws a texture at art scale with its top left corner at the given point.
func _draw_art(texture: Texture2D, top_left: Vector2, tint := Color.WHITE) -> void:
	if texture != null:
		draw_texture_rect(texture, Rect2(_snap(top_left), texture.get_size() * TreeArt.SCALE), false, tint)


## Draws a texture at art scale centred on a point.
func _draw_art_centered(texture: Texture2D, center: Vector2, tint := Color.WHITE) -> void:
	if texture != null:
		_draw_art(texture, center - texture.get_size() * TreeArt.SCALE * 0.5, tint)


func _draw_backdrop() -> void:
	var backdrop := TreeArt.texture("backdrop")
	if backdrop == null:
		draw_rect(Rect2(Vector2.ZERO, size), BACKDROP)
		return
	var fit := maxf(size.x / backdrop.get_width(), size.y / backdrop.get_height())
	var art_scale := maxf(TreeArt.SCALE, ceilf(fit))
	var drawn := backdrop.get_size() * art_scale
	draw_texture_rect(backdrop, Rect2(_snap((size - drawn) * 0.5), drawn), false)


## A soft glow in each region's colour behind its nodes.
func _draw_auras() -> void:
	var aura := TreeArt.texture("aura")
	if aura == null:
		return
	var sums: Dictionary[StringName, Vector2] = {}
	var counts: Dictionary[StringName, int] = {}
	for id in tree.graph.ids():
		var data := tree.graph.node(id)
		if regions.has(data.region):
			sums[data.region] = sums.get(data.region, Vector2.ZERO) + _to_screen(data.position)
			counts[data.region] = counts.get(data.region, 0) + 1
	for region_id in sums:
		var center: Vector2 = sums[region_id] / counts[region_id]
		var taken := 0
		for id in tree.graph.ids():
			var data := tree.graph.node(id)
			if data.region == region_id and tree.is_allocated(id):
				taken += 1
		var strength := 0.07 + 0.1 * minf(1.0, taken / 3.0)
		_draw_art_centered(aura, center, Color(regions[region_id].color, strength))


## Faint dotted circles around the start, like an astrolabe.
func _draw_rings() -> void:
	var center := _to_screen(Vector2.ZERO)
	for ring in 3:
		var radius := (130.0 + ring * 125.0) * _scale
		var dots := int(TAU * radius / 14.0)
		for i in dots:
			var at := _snap(center + Vector2.from_angle(TAU * i / dots + ring * 0.3) * radius)
			draw_rect(Rect2(at, Vector2(2, 2)), Color(0.6, 0.66, 0.9, 0.09 if i % 4 else 0.16))


func _draw_stars() -> void:
	var sparkle := TreeArt.texture("sparkle")
	for star in _stars:
		var shine := pow(maxf(0.0, sin(_time * (0.6 + star.z * 0.2) + star.z * 7.0)), 8.0)
		if shine > 0.03:
			_draw_art_centered(sparkle, Vector2(star.x, star.y) * size, Color(0.8, 0.86, 1.0, shine * 0.7))


## The colour a node shows: its region's, warm white for the start, gold for keystones.
func _node_color(data: TreeNodeData) -> Color:
	if data.kind == TreeNodeData.Kind.START:
		return START_COLOR
	return _colors(data)[0]


func _draw_links(path: Array[StringName]) -> void:
	for id in tree.graph.ids():
		for other in tree.graph.neighbours(id):
			if String(other) < String(id):
				continue
			var near := tree.graph.node(id)
			var far := tree.graph.node(other)
			if near.position.length() > far.position.length():
				var swap := near
				near = far
				far = swap
			var a := _snap(_to_screen(near.position))
			var b := _snap(_to_screen(far.position))
			draw_line(a, b, LINK_GROOVE, 8.0)
			var near_taken := tree.is_allocated(near.id)
			var far_taken := tree.is_allocated(far.id)
			if near_taken and far_taken:
				var color := _node_color(near).lerp(_node_color(far), 0.5)
				draw_line(a, b, color.darkened(0.45), 4.0)
				draw_line(a, b, color.lightened(0.1), 2.0)
				_draw_motes(a, b, color)
			else:
				draw_line(a, b, LINK_NEAR if near_taken or far_taken else LINK_OPEN, 2.0)
	for i in range(1, path.size()):
		draw_dashed_line(_snap(screen_position(path[i - 1])), _snap(screen_position(path[i])), LINK_PATH, 4.0, 10.0)


## Specks of light running outward along a taken link.
func _draw_motes(a: Vector2, b: Vector2, color: Color) -> void:
	var length := a.distance_to(b)
	if length < 1.0:
		return
	var count := maxi(1, int(length / 70.0))
	for i in count:
		var t := fposmod(_time * 45.0 / length + float(i) / count, 1.0)
		var at := _snap(a.lerp(b, t))
		draw_rect(Rect2(at - Vector2(2, 2), Vector2(4, 4)), Color(color.lightened(0.55), sin(t * PI) * 0.9))


func _draw_region_labels() -> void:
	for region_id in _label_spots:
		var region := regions[region_id]
		var at := _label_spots[region_id]
		_draw_art(TreeArt.emblem(region_id), Vector2(at.x, at.y - 21.0), Color(region.color.lightened(0.35), 1.0))
		var text_at := Vector2(at.x + EMBLEM_GAP, at.y)
		draw_string_outline(_font, text_at, region.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_FONT_SIZE, 8,
				BACKDROP)
		draw_string(_font, text_at, region.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, LABEL_FONT_SIZE,
				Color(region.color, 0.95))


func _draw_node(data: TreeNodeData) -> void:
	var at := _snap(_to_screen(data.position))
	var style := TreeArt.style(data)
	var half: float = TreeArt.SIZES[style] * TreeArt.SCALE * 0.5
	var top_left := at - Vector2(half, half)
	var taken := tree.is_allocated(data.id)
	var open := tree.can_allocate(data.id)
	var locked := tree.is_locked(data.id)
	var colors := _colors(data)
	if data.kind == TreeNodeData.Kind.START:
		colors = [START_COLOR]
	# How lit the gem is, and how bright the frame and icon are.
	var lit := 0.5
	var frame := 0.68
	var mark := 0.6
	if locked:
		lit = 0.2
		frame = 0.4
		mark = 0.35
	elif taken:
		lit = 1.0
		frame = 1.0
		mark = 1.0
	elif open:
		lit = 0.8
		frame = 1.0
		mark = 1.0
	var seed := float(hash(data.id) % 1000) / 1000.0

	if taken:
		var breathe := 0.5 + 0.12 * sin(_time * 2.0 + seed * TAU)
		_draw_art_centered(TreeArt.texture("glow"), at, Color(colors[0], breathe))
		# A rim in the region's colour marks a taken node; open nodes get a pulsing gold one instead.
		_draw_art_centered(TreeArt.texture("halo_" + style), at, Color(colors[0].lightened(0.25), 0.9))
	if open:
		var pulse := 0.5 + 0.5 * sin(_time * 4.0)
		_draw_art_centered(TreeArt.texture("halo_" + style), at, Color(UiStyle.GOLD, 0.4 + 0.5 * pulse))

	if colors.size() > 1:
		_draw_art(TreeArt.texture("gem_%s_left" % style), top_left, _gem_tint(colors[0], lit))
		_draw_art(TreeArt.texture("gem_%s_right" % style), top_left, _gem_tint(colors[1], lit))
	else:
		_draw_art(TreeArt.texture("gem_" + style), top_left, _gem_tint(colors[0], lit))
	if style == &"portrait":
		var ring: float = TreeArt.RINGS[style] * TreeArt.SCALE
		_draw_art(TreeArt.portrait(data.unlocks_towers[0]), top_left + Vector2(ring, ring), Color(frame, frame, frame))
	elif lit >= 0.7:
		_draw_art(TreeArt.texture("shine_" + style), top_left, Color(1, 1, 1, lit * 0.9))
	_draw_art(TreeArt.texture("frame_" + style), top_left, Color(frame, frame, frame))
	if style != &"portrait":
		_draw_art_centered(TreeArt.icon(TreeArt.node_icon(data)), at, Color(mark, mark, mark))
	if locked:
		_draw_art(TreeArt.icon(&"lock"), at + Vector2(half - 18.0, half - 20.0))
	if taken:
		var glint := pow(maxf(0.0, sin(_time * 1.3 + seed * 40.0)), 14.0)
		if glint > 0.05:
			_draw_art_centered(TreeArt.texture("sparkle"), at + Vector2(half * 0.55, -half * 0.55), Color(1, 1, 1, glint))
	if data.id == _hovered:
		_draw_brackets(at, half + 6.0, UiStyle.GOLD)


## The gem's colour: the region's colour, darker and greyer when out of reach.
static func _gem_tint(color: Color, lit: float) -> Color:
	var grey := Color(color.get_luminance(), color.get_luminance(), color.get_luminance())
	var tint := color.lerp(grey, clampf((0.75 - lit) * 0.8, 0.0, 0.45)) * lit
	tint.a = 1.0
	return tint


## Four corner marks around a hovered node.
func _draw_brackets(center: Vector2, reach: float, color: Color) -> void:
	var length := 10.0
	for corner: Vector2 in [Vector2(-1, -1), Vector2(1, -1), Vector2(1, 1), Vector2(-1, 1)]:
		var tip := _snap(center + corner * reach)
		var across := Rect2(Vector2(tip.x - (length if corner.x > 0 else 0.0), tip.y - (2.0 if corner.y > 0 else 0.0)),
				Vector2(length, 2))
		var down := Rect2(Vector2(tip.x - (2.0 if corner.x > 0 else 0.0), tip.y - (length if corner.y > 0 else 0.0)),
				Vector2(2, length))
		draw_rect(across, color)
		draw_rect(down, color)


func _draw_bursts() -> void:
	for burst in _bursts:
		var t: float = burst["age"] / BURST_SECONDS
		var at: Vector2 = burst["at"]
		var color: Color = burst["color"]
		var radius: float = burst["radius"]
		var fade := 1.0 - t
		draw_arc(at, radius + 6.0 + t * 46.0, 0.0, TAU, 48, Color(color.lightened(0.5), fade * 0.9), 4.0 * fade + 1.0)
		for i in 12:
			var direction := Vector2.from_angle(TAU * i / 12.0 + 0.26)
			var reach := radius + t * (50.0 + (i % 3) * 18.0)
			var spark := _snap(at + direction * reach)
			var side := 6.0 if t < 0.4 else 4.0
			draw_rect(Rect2(spark - Vector2(side, side) * 0.5, Vector2(side, side)), Color(color.lightened(0.6), fade))


func _draw_tooltip(data: TreeNodeData, path: Array[StringName]) -> void:
	var lines: Array[String] = [data.description]
	var status := _status(data, path)
	if not status.is_empty():
		lines.append(status)
	var picture: Texture2D = null
	if not data.unlocks_towers.is_empty():
		picture = BoardArt.tower_picture(data.unlocks_towers[0])
	var text_width := 420.0
	var picture_width := 0.0 if picture == null else picture.get_width() * TreeArt.SCALE + 24.0
	var width := text_width + picture_width
	var node_at := _to_screen(data.position)
	var at := node_at + Vector2(_radius(data) + 18.0, -20.0)
	if at.x + width > size.x - 16.0:
		at.x = node_at.x - _radius(data) - 18.0 - width
	var height := 56.0 + 26.0 * _wrapped_line_count(lines, text_width - 32.0)
	if picture != null:
		height = maxf(height, picture.get_height() * TreeArt.SCALE + 36.0)
	at.y = clampf(at.y, 16.0, size.y - height - 16.0)
	at = _snap(at)
	draw_style_box(_panel, Rect2(at, Vector2(width, height)))
	_draw_art(TreeArt.icon(TreeArt.node_icon(data)), at + Vector2(16, 14), Color(_node_color(data).lightened(0.3), 1.0))
	draw_string(_font, at + Vector2(48, 34), data.display_name, HORIZONTAL_ALIGNMENT_LEFT, text_width - 64.0, 24,
			UiStyle.TEXT)
	var y := at.y + 64.0
	for i in lines.size():
		var color := UiStyle.TEXT if i == 0 else UiStyle.GOLD
		draw_multiline_string(_font, Vector2(at.x + 16, y), lines[i], HORIZONTAL_ALIGNMENT_LEFT, text_width - 32.0, 19,
				-1, color)
		y += 26.0 * _wrapped_line_count([lines[i]], text_width - 32.0)
	if picture != null:
		var picture_size := picture.get_size() * TreeArt.SCALE
		var spot := Vector2(at.x + text_width, at.y + (height - picture_size.y) * 0.5)
		_draw_art_centered(TreeArt.texture("glow"), spot + picture_size * 0.5, Color(_node_color(data), 0.35))
		_draw_art(picture, spot)


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
