class_name BoardCamera
extends Node
## Pans and zooms the board inside its part of the screen, for maps bigger than the screen.
##
## The board node itself is moved and scaled (there is no Camera2D), so the HUD layers never move and
## board.to_global() still gives screen positions. Zoom steps are whole multiples of the art's pixels,
## so the pixel art stays crisp at every step. A map starts zoomed out so all of it shows.
##
## Mouse wheel or pinch zooms toward the cursor, middle-drag or a two-finger swipe pans, the arrow
## keys pan, + and - zoom, and Home shows the whole map again.

## Screen area the board is shown in: left of the side panel, under the top bar.
const VIEW_RECT := Rect2(12, 88, 1560, 984)
const VIEW_CENTER := Vector2(12 + 780, 88 + 492)
## Board scales the player can step through. 0.5 shows one art pixel per screen pixel.
const ZOOMS: Array[float] = [0.5, 1.0, 1.5, 2.0]
## Screen pixels per second the arrow keys pan.
const KEY_PAN_SPEED := 900.0
## Seconds a zoom step takes to ease in.
const ZOOM_TIME := 0.14

var board: Node2D
## Returns true while a full-screen panel (the skill web, the pause menu) is up, so the board stays put.
var blocked_when := Callable()
## Size of the map in board pixels.
var map_size := Vector2.ZERO
## Smallest scale: the largest step that still shows the whole map (or the smallest step).
var min_zoom := 1.0
var zoom := 1.0

var _target_zoom := 1.0
## Board point kept under this screen point while zooming.
var _anchor_board := Vector2.ZERO
var _anchor_screen := Vector2.ZERO
var _dragging := false


func setup(p_board: Node2D, p_map_size: Vector2) -> void:
	board = p_board
	map_size = p_map_size
	min_zoom = ZOOMS[0]
	for step in ZOOMS:
		if map_size.x * step <= VIEW_RECT.size.x and map_size.y * step <= VIEW_RECT.size.y:
			min_zoom = step
	# A big map is shown as large as the view allows rather than at the next crisp step below, so the
	# whole-map view fills the screen. That scale is between whole art pixels, so the board is drawn
	# with smooth filtering there (see _apply).
	var fit := minf(VIEW_RECT.size.x / maxf(map_size.x, 1.0), VIEW_RECT.size.y / maxf(map_size.y, 1.0))
	if fit > min_zoom + 0.02 and fit < 1.0:
		min_zoom = floorf(fit * 100.0) / 100.0
	show_all()


## Zooms out so the whole map shows, centred.
func show_all() -> void:
	zoom = min_zoom
	_target_zoom = min_zoom
	_apply(map_size * 0.5, VIEW_CENTER)


## True when the whole map fits on screen at the current zoom.
func shows_all() -> bool:
	return map_size.x * zoom <= VIEW_RECT.size.x + 0.5 and map_size.y * zoom <= VIEW_RECT.size.y + 0.5


## Steps the zoom in (+1) or out (-1), keeping the board point under `screen_point` where it is.
func step_zoom(direction: int, screen_point: Vector2 = VIEW_CENTER) -> void:
	var steps := _steps()
	var index := steps.find(_target_zoom)
	if index < 0:
		index = 0
	var next := clampi(index + direction, 0, steps.size() - 1)
	if steps[next] == _target_zoom:
		return
	_target_zoom = steps[next]
	if not VIEW_RECT.has_point(screen_point):
		screen_point = VIEW_CENTER
	_anchor_screen = screen_point
	_anchor_board = board.to_local(screen_point)


## Zooms straight to a scale, with a board point at a screen point. For tests and screenshots.
func set_view(p_zoom: float, board_point: Vector2, screen_point: Vector2 = VIEW_CENTER) -> void:
	zoom = clampf(p_zoom, min_zoom, ZOOMS[ZOOMS.size() - 1])
	_target_zoom = zoom
	_apply(board_point, screen_point)


## Moves the view by a screen offset.
func pan(screen_delta: Vector2) -> void:
	board.position = _clamped(board.position + screen_delta, zoom)
	_anchor_screen += screen_delta


## Nearest filtering keeps the pixel art crisp when every art pixel covers a whole number of screen
## pixels (the art is drawn at 2x, so steps of 0.5); in between, smooth filtering stops pixels from
## doubling up unevenly.
static func filter_for(scale: float) -> CanvasItem.TextureFilter:
	var screen_px := scale * 2.0
	if absf(screen_px - roundf(screen_px)) < 0.01:
		return CanvasItem.TEXTURE_FILTER_NEAREST
	return CanvasItem.TEXTURE_FILTER_LINEAR


func _steps() -> Array[float]:
	var steps: Array[float] = []
	for step in ZOOMS:
		if step >= min_zoom:
			steps.append(step)
	return steps


func _process(delta: float) -> void:
	if board == null:
		return
	if not is_equal_approx(zoom, _target_zoom):
		zoom = lerpf(zoom, _target_zoom, clampf(delta / ZOOM_TIME * 2.5, 0.0, 1.0))
		if absf(zoom - _target_zoom) < 0.01:
			zoom = _target_zoom
		_apply(_anchor_board, _anchor_screen)
	var keys := Vector2.ZERO
	if Input.is_key_pressed(KEY_LEFT):
		keys.x += 1.0
	if Input.is_key_pressed(KEY_RIGHT):
		keys.x -= 1.0
	if Input.is_key_pressed(KEY_UP):
		keys.y += 1.0
	if Input.is_key_pressed(KEY_DOWN):
		keys.y -= 1.0
	if keys != Vector2.ZERO and not _blocked():
		pan(keys * KEY_PAN_SPEED * delta)


func _unhandled_input(event: InputEvent) -> void:
	if board == null or _blocked():
		return
	var button := event as InputEventMouseButton
	if button != null:
		match button.button_index:
			MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN:
				if button.pressed and VIEW_RECT.has_point(button.position):
					step_zoom(1 if button.button_index == MOUSE_BUTTON_WHEEL_UP else -1, button.position)
					get_viewport().set_input_as_handled()
			MOUSE_BUTTON_MIDDLE:
				_dragging = button.pressed
				get_viewport().set_input_as_handled()
		return
	var motion := event as InputEventMouseMotion
	if motion != null and _dragging:
		pan(motion.relative)
		get_viewport().set_input_as_handled()
		return
	var swipe := event as InputEventPanGesture
	if swipe != null:
		pan(-swipe.delta * 24.0)
		get_viewport().set_input_as_handled()
		return
	var pinch := event as InputEventMagnifyGesture
	if pinch != null and absf(pinch.factor - 1.0) > 0.04:
		step_zoom(1 if pinch.factor > 1.0 else -1, pinch.position)
		get_viewport().set_input_as_handled()
		return
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo:
		match key.keycode:
			KEY_EQUAL, KEY_PLUS, KEY_KP_ADD:
				step_zoom(1)
			KEY_MINUS, KEY_KP_SUBTRACT:
				step_zoom(-1)
			KEY_HOME:
				show_all()
			_:
				return
		get_viewport().set_input_as_handled()


func _blocked() -> bool:
	return blocked_when.is_valid() and blocked_when.call()


## Scales the board and places it so `board_point` sits at `screen_point`, kept inside the view.
func _apply(board_point: Vector2, screen_point: Vector2) -> void:
	board.scale = Vector2(zoom, zoom)
	board.texture_filter = filter_for(zoom)
	board.position = _clamped(screen_point - board_point * zoom, zoom)


## A board position that keeps the map filling the view (or centred in it when it is smaller), on
## whole screen pixels.
func _clamped(at: Vector2, factor: float) -> Vector2:
	var size := map_size * factor
	var result := at
	for axis in 2:
		var lo := VIEW_RECT.position[axis]
		var span := VIEW_RECT.size[axis]
		if size[axis] <= span:
			result[axis] = lo + (span - size[axis]) * 0.5
		else:
			result[axis] = clampf(at[axis], lo + span - size[axis], lo)
	return result.round()
