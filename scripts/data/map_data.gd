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
## Cells the path turns at, in order. Without a curve the path runs in straight lines between them,
## so consecutive waypoints must share a row or a column. The first and last may sit outside the
## grid so enemies walk in from the edge and leave through it. A first waypoint inside the grid is
## where the road starts on the board: a spawn hole (see hole_lanes) or a building of the enemy base.
@export var waypoints: Array[Vector2i] = []
## The road's centre line, densely sampled, in cells (cell (x, y) has its centre at (x, y)). When set,
## enemies walk along it instead of the straight lines between waypoints, and every cell it passes
## close to is road. It starts and ends at the first and last waypoint. Written by
## tools/campaign/maps.py; tools/art/gen_game_art.py paints the road from it.
@export var curve: PackedVector2Array = []
## Id of the WaveSet played on this map.
@export var wave_set: StringName
## Extra roads for maps with more than one entrance. Lane 0 is `waypoints`; lane n is extra_lanes[n - 1].
## Lanes may join, so enemies from several entrances converge on one exit.
@export var extra_lanes: Array[MapLane] = []
## Look of the ground: meadow, fire, storm, nature, water, earth, void or heart. See tools/art/gen_game_art.py.
@export var biome: StringName = &"meadow"
## False keeps the map out of the skirmish map list, for maps only played in the campaign.
@export var skirmish: bool = true
## Lanes that start at a spawn hole: a pit in the open ground the horde climbs out of, partway
## along the road. Their road joins another lane's.
@export var hole_lanes: PackedInt32Array = []

## A cell is road when the centre line passes this close to its centre, in cells. Half the road is
## about 0.46 cells wide, so this keeps towers off the road's edges where it runs at a slant.
const ROAD_REACH := 0.78


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


## A lane's curve in cells, or an empty array for a lane that runs straight between its waypoints.
func lane_curve(lane: int) -> PackedVector2Array:
	if lane <= 0:
		return curve
	var extra := extra_lanes[lane - 1]
	return extra.curve if extra != null else PackedVector2Array()


## True when the lane starts at a spawn hole in the open ground rather than at the edge.
func is_spawn_hole(lane: int) -> bool:
	return hole_lanes.has(lane)


## The road enemies walk on a lane, in pixels: its curve, or the centres of its waypoints.
func path_points(lane: int = 0) -> PackedVector2Array:
	var points := PackedVector2Array()
	var line := lane_curve(lane)
	if not line.is_empty():
		for point in line:
			points.append((point + Vector2(0.5, 0.5)) * cell_size)
		return points
	for cell in lane_waypoints(lane):
		points.append(cell_center(cell))
	return points


## Every cell any lane passes through, including cells outside the grid.
func path_cells() -> Dictionary[Vector2i, bool]:
	var cells: Dictionary[Vector2i, bool] = {}
	for lane in lane_count():
		var line := lane_curve(lane)
		if not line.is_empty():
			_add_curve_cells(line, cells)
			continue
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


## Marks the cells whose centre is within ROAD_REACH of a curve.
static func _add_curve_cells(line: PackedVector2Array, cells: Dictionary[Vector2i, bool]) -> void:
	for i in range(1, line.size()):
		var a := line[i - 1]
		var b := line[i]
		var low := Vector2i((a.min(b) - Vector2.ONE).floor())
		var high := Vector2i((a.max(b) + Vector2.ONE).ceil())
		for x in range(low.x, high.x + 1):
			for y in range(low.y, high.y + 1):
				var cell := Vector2i(x, y)
				if cells.has(cell):
					continue
				var centre := Vector2(cell)
				if Geometry2D.get_closest_point_to_segment(centre, a, b).distance_to(centre) < ROAD_REACH:
					cells[cell] = true


## Problems with the waypoints, as readable lines. Empty means every lane is valid.
func path_errors() -> PackedStringArray:
	var errors: PackedStringArray = []
	for lane in lane_count():
		var points := lane_waypoints(lane)
		var prefix := "" if lane == 0 else "lane %d: " % lane
		if points.size() < 2:
			errors.append(prefix + "needs at least 2 waypoints")
		var line := lane_curve(lane)
		if not line.is_empty():
			if line.size() < 2:
				errors.append(prefix + "the curve needs at least 2 points")
			elif points.size() >= 2 and (not line[0].is_equal_approx(Vector2(points[0])) \
					or not line[line.size() - 1].is_equal_approx(Vector2(points[points.size() - 1]))):
				errors.append(prefix + "the curve does not start and end at the first and last waypoint")
			for point in line:
				if point.x < -1.5 or point.y < -1.5 or point.x > grid_size.x + 0.5 or point.y > grid_size.y + 0.5:
					errors.append(prefix + "the curve leaves the board at %s" % point)
					break
			continue
		for i in range(1, points.size()):
			var from := points[i - 1]
			var to := points[i]
			if from == to:
				errors.append(prefix + "waypoints %d and %d are the same cell" % [i - 1, i])
			elif from.x != to.x and from.y != to.y:
				errors.append(prefix + "waypoints %d and %d do not share a row or column" % [i - 1, i])
	for lane in hole_lanes:
		if lane <= 0 or lane >= lane_count():
			errors.append("hole lane %d does not exist" % lane)
		elif not is_inside(lane_waypoints(lane)[0]):
			errors.append("hole lane %d starts outside the board" % lane)
	return errors
