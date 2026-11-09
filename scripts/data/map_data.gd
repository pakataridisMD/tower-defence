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
## Extra roads for maps with more than one entrance. Lane 0 is `waypoints`; lane n is extra_lanes[n - 1].
## Lanes may join, so enemies from several entrances converge on one exit.
@export var extra_lanes: Array[MapLane] = []
## Look of the ground: meadow, fire, storm, nature, water, earth, void or heart. See tools/art/gen_game_art.py.
@export var biome: StringName = &"meadow"
## False keeps the map out of the skirmish map list, for maps only played in the campaign.
@export var skirmish: bool = true


func cell_center(cell: Vector2i) -> Vector2:
	return (Vector2(cell) + Vector2(0.5, 0.5)) * cell_size


func cell_at(local_position: Vector2) -> Vector2i:
	return Vector2i((local_position / cell_size).floor())


func is_inside(cell: Vector2i) -> bool:
	return cell.x >= 0 and cell.y >= 0 and cell.x < grid_size.x and cell.y < grid_size.y


func size_in_pixels() -> Vector2:
	return Vector2(grid_size * cell_size)


func lane_count() -> int:
	return 1 + extra_lanes.size()


## The turning points of one lane. Lane 0 is the main path.
func lane_waypoints(lane: int) -> Array[Vector2i]:
	if lane <= 0:
		return waypoints
	var extra := extra_lanes[lane - 1]
	return extra.waypoints if extra != null else ([] as Array[Vector2i])


## Centres of a lane's waypoints, in pixels.
func path_points(lane: int = 0) -> PackedVector2Array:
	var points := PackedVector2Array()
	for cell in lane_waypoints(lane):
		points.append(cell_center(cell))
	return points


## Every cell any lane passes through, including cells outside the grid.
func path_cells() -> Dictionary[Vector2i, bool]:
	var cells: Dictionary[Vector2i, bool] = {}
	for lane in lane_count():
		var points := lane_waypoints(lane)
		for i in range(1, points.size()):
			var from := points[i - 1]
			var to := points[i]
			var step := Vector2i(signi(to.x - from.x), signi(to.y - from.y))
			var cell := from
			cells[cell] = true
			while cell != to:
				cell += step
				cells[cell] = true
	return cells


## Problems with the waypoints, as readable lines. Empty means every lane is valid.
func path_errors() -> PackedStringArray:
	var errors: PackedStringArray = []
	for lane in lane_count():
		var points := lane_waypoints(lane)
		var prefix := "" if lane == 0 else "lane %d: " % lane
		if points.size() < 2:
			errors.append(prefix + "needs at least 2 waypoints")
		for i in range(1, points.size()):
			var from := points[i - 1]
			var to := points[i]
			if from == to:
				errors.append(prefix + "waypoints %d and %d are the same cell" % [i - 1, i])
			elif from.x != to.x and from.y != to.y:
				errors.append(prefix + "waypoints %d and %d do not share a row or column" % [i - 1, i])
	return errors
