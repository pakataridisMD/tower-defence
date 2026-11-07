class_name MapData
extends Resource
## A map: a grid of build cells and the path enemies walk along.

@export var id: StringName
@export var display_name: String
## Position in the menu, lowest first.
@export var order: int = 0
## Columns and rows of build cells.
@export var grid_size: Vector2i = Vector2i(24, 15)
## Pixels per cell.
@export var cell_size: int = 64
## Cells the path turns at, in order. The path runs in straight lines between them, so
## consecutive waypoints must share a row or a column. The first and last may sit outside
## the grid so enemies walk in from the edge and leave through it.
@export var waypoints: Array[Vector2i] = []
## Id of the WaveSet played on this map.
@export var wave_set: StringName


func cell_center(cell: Vector2i) -> Vector2:
	return (Vector2(cell) + Vector2(0.5, 0.5)) * cell_size


func cell_at(local_position: Vector2) -> Vector2i:
	return Vector2i((local_position / cell_size).floor())


func is_inside(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < grid_size.x and cell.y < grid_size.y


func size_in_pixels() -> Vector2:
	return Vector2(grid_size * cell_size)


## Centres of the waypoints, in pixels.
func path_points() -> PackedVector2Array:
	var points := PackedVector2Array()
	for cell in waypoints:
		points.append(cell_center(cell))
	return points


## Every cell the path passes through, including cells outside the grid.
func path_cells() -> Dictionary[Vector2i, bool]:
	var cells: Dictionary[Vector2i, bool] = {}
	for i in range(1, waypoints.size()):
		var from := waypoints[i - 1]
		var to := waypoints[i]
		var step := Vector2i(signi(to.x - from.x), signi(to.y - from.y))
		var cell := from
		cells[cell] = true
		while cell != to:
			cell += step
			cells[cell] = true
	return cells


## Problems with the waypoints, as readable lines. Empty means the path is valid.
func path_errors() -> PackedStringArray:
	var errors: PackedStringArray = []
	if waypoints.size() < 2:
		errors.append("needs at least 2 waypoints")
	for i in range(1, waypoints.size()):
		var from := waypoints[i - 1]
		var to := waypoints[i]
		if from == to:
			errors.append("waypoints %d and %d are the same cell" % [i - 1, i])
		elif from.x != to.x and from.y != to.y:
			errors.append("waypoints %d and %d do not share a row or column" % [i - 1, i])
	return errors
