class_name Caves
extends RefCounted
## Enemy caves that break open during a run.
##
## Every 4 or 5 waves the ground cracks open somewhere new and the horde starts coming out of it as
## well as down the roads. A cave opens in the break before the wave it first sends enemies in, at a
## random spot in the open ground: far from the defended city, far from every other place the horde
## comes from, and a short dig away from a road it joins. The dig is a new stretch of road from the
## cave's mouth to that road, so nothing can be built on it; it bends around the towers already
## standing. It always joins a road early enough that the horde still walks most of it.
##
## RunSim keeps the caves and their lanes; this only finds where the next one goes.

## Waves between two caves: a random number from this range.
const EVERY_MIN := 4
const EVERY_MAX := 5
## No run has more caves than this.
const MAX_CAVES := 4
## Cells from a cave to the city at the end of the road, at the least.
const BASE_DISTANCE := 12.0
## Cells from a cave to any other place the horde comes from (a road's start, another cave), at the least.
const SPAWN_DISTANCE := 8.0
## Cells of new road from the cave's mouth to the road it joins: at least and at most.
const DIG_MIN := 2
const DIG_MAX := 7
## The road a cave joins must still have this share of its length ahead of the join.
const ROAD_LEFT := 0.5


## One cave: where it stands, the new road it dug and the lane its horde walks.
class Cave:
	## The cell the cave's mouth is in.
	var cell: Vector2i
	## The cells of new road, from beside the cave to the road it joins (not including either).
	var dig: Array[Vector2i] = []
	## The cells around the cave mouth nothing can be built on (the mound), the mouth included.
	var cells: Array[Vector2i] = []
	## The lane the cave's horde walks in RunSim.lane_curves, and the lane it joins.
	var lane := -1
	var joins_lane := 0
	## Pixels along the joined lane where the dig meets it.
	var join_offset := 0.0
	## The wave it first sent enemies in (1-based).
	var wave := 0
	## The walk from the mouth to the joined road, in board pixels (smoothed), for the art.
	var dig_points := PackedVector2Array()


## The cell where a cave can open, with its dig, or null when there is no room. `blocked` says which
## cells cannot be dug or covered (towers, camps, the city, the enemy's buildings, earlier caves);
## `is_road` which cells are the map's own roads; `spawns` are where the horde already comes from, in
## board pixels; `bases` where it is going (the city).
static func find(map: MapData, curves: Array[Curve2D], lengths: PackedFloat32Array, is_road: Callable,
		blocked: Callable, spawns: PackedVector2Array, bases: PackedVector2Array, rng: RandomNumberGenerator) -> Cave:
	var cell_size := float(map.cell_size)
	var road_lanes := mini(map.lane_count(), curves.size())
	# Road cells a dig may join: far enough from the end of their road. Each to [lane, offset].
	var joins: Dictionary[Vector2i, Array] = {}
	var parent: Dictionary[Vector2i, Vector2i] = {}
	var depth: Dictionary[Vector2i, int] = {}
	var queue: Array[Vector2i] = []
	for x in map.grid_size.x:
		for y in map.grid_size.y:
			var cell := Vector2i(x, y)
			if not is_road.call(cell) or blocked.call(cell):
				continue
			var join := _join(map, curves, lengths, road_lanes, cell)
			if join.is_empty():
				continue
			joins[cell] = join
			depth[cell] = 0
			parent[cell] = cell
			queue.append(cell)
	# Out from the roads over open ground, so each cell knows its shortest dig.
	var head := 0
	while head < queue.size():
		var at := queue[head]
		head += 1
		if depth[at] > DIG_MAX:
			continue
		for step: Vector2i in [Vector2i.LEFT, Vector2i.RIGHT, Vector2i.UP, Vector2i.DOWN]:
			var next := at + step
			if depth.has(next) or not map.is_inside(next) or is_road.call(next) or blocked.call(next):
				continue
			depth[next] = depth[at] + 1
			parent[next] = at
			queue.append(next)
	var candidates: Array[Vector2i] = []
	for cell: Vector2i in depth:
		var d: int = depth[cell]
		# depth counts the mouth's own cell: a dig of n cells puts the mouth n + 1 from the road.
		if d < DIG_MIN + 1 or d > DIG_MAX + 1:
			continue
		if not _room_for_mound(map, cell, is_road, blocked):
			continue
		var centre := map.cell_center(cell)
		if _near(centre, bases, BASE_DISTANCE * cell_size) or _near(centre, spawns, SPAWN_DISTANCE * cell_size):
			continue
		candidates.append(cell)
	if candidates.is_empty():
		return null
	candidates.sort()
	var cave := Cave.new()
	cave.cell = candidates[rng.randi_range(0, candidates.size() - 1)]
	cave.cells = mound(cave.cell)
	var walk := parent[cave.cell]
	while not joins.has(walk):
		cave.dig.append(walk)
		walk = parent[walk]
	cave.joins_lane = joins[walk][0]
	cave.join_offset = joins[walk][1]
	return cave


## The cells a cave's mound covers: its mouth and the eight around it.
static func mound(cell: Vector2i) -> Array[Vector2i]:
	var cells: Array[Vector2i] = []
	for dy in range(-1, 2):
		for dx in range(-1, 2):
			cells.append(cell + Vector2i(dx, dy))
	return cells


## The road a cave's horde walks, in board pixels: out of the mouth, along the dig, onto the road it
## joins and down it to the end. Also fills in cave.dig_points.
static func lane_points(map: MapData, cave: Cave, curve: Curve2D, length: float) -> PackedVector2Array:
	var rough := PackedVector2Array([map.cell_center(cave.cell)])
	for cell in cave.dig:
		rough.append(map.cell_center(cell))
	rough.append(curve.sample_baked(cave.join_offset))
	cave.dig_points = _smooth(rough, 3)
	var points := cave.dig_points.duplicate()
	var offset := cave.join_offset + 12.0
	while offset < length:
		points.append(curve.sample_baked(offset))
		offset += 12.0
	points.append(curve.sample_baked(length))
	return points


## The waves the next cave opens before: the first after 4 or 5 waves, then every 4 or 5.
static func next_wave(after: int, rng: RandomNumberGenerator) -> int:
	return after + rng.randi_range(EVERY_MIN, EVERY_MAX)


## Lane and offset of the road through a cell, if it has enough road left ahead: [lane, offset],
## otherwise empty. Where two roads share a cell, the one with more road ahead.
static func _join(map: MapData, curves: Array[Curve2D], lengths: PackedFloat32Array, lanes: int, cell: Vector2i) -> Array:
	var centre := map.cell_center(cell)
	var best: Array = []
	var best_left := -1.0
	for lane in lanes:
		var offset := curves[lane].get_closest_offset(centre)
		if curves[lane].sample_baked(offset).distance_to(centre) > map.cell_size * 0.9:
			continue
		var left := lengths[lane] - offset
		if left < lengths[lane] * ROAD_LEFT or left <= best_left:
			continue
		best = [lane, offset]
		best_left = left
	return best


static func _room_for_mound(map: MapData, cell: Vector2i, is_road: Callable, blocked: Callable) -> bool:
	for c in mound(cell):
		# Keep a cell of open ground between the mound and the edge.
		if c.x < 1 or c.y < 1 or c.x >= map.grid_size.x - 1 or c.y >= map.grid_size.y - 1:
			return false
		if is_road.call(c) or blocked.call(c):
			return false
	return true


static func _near(point: Vector2, others: PackedVector2Array, distance: float) -> bool:
	for other in others:
		if point.distance_to(other) < distance:
			return true
	return false


## Rounds the corners of a line of points (Chaikin), keeping its ends.
static func _smooth(points: PackedVector2Array, rounds: int) -> PackedVector2Array:
	var line := points
	for r in rounds:
		if line.size() < 3:
			return line
		var next := PackedVector2Array([line[0]])
		for i in line.size() - 1:
			var a := line[i]
			var b := line[i + 1]
			next.append(a.lerp(b, 0.25))
			next.append(a.lerp(b, 0.75))
		next.append(line[line.size() - 1])
		line = next
	return line
