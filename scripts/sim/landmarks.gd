class_name Landmarks
extends RefCounted
## Where the enemy's war camps and the defended city stand on a map.
##
## Every road that enters from the edge of the map starts in an enemy war camp, and the road out
## ends in the city the player defends. Each one takes a small block of build cells beside its road
## end, just inside the edge, so no tower can stand on it. Roads that start inside the map (spawn
## holes) have no camp. Lanes that share an end share one site.

## Rows of cells a site reaches into the map from the edge.
const DEPTH := 3
## Cells a site reaches to each side of its road.
const HALF_WIDTH := 2


## One camp or city.
class Site:
	## &"camp" or &"city".
	var kind: StringName
	## Lanes whose road starts (camp) or ends (city) here.
	var lanes: Array[int] = []
	## The road's first (camp) or last (city) cell inside the map.
	var anchor: Vector2i
	## From the map edge into the map, one of the four axis directions.
	var inward: Vector2i
	## The build cells the site covers (never road cells).
	var cells: Array[Vector2i] = []
	## Where the road crosses the edge of the map, in board pixels.
	var gate: Vector2

	## Across the road, one of the two axis directions square to `inward`.
	func across() -> Vector2i:
		return Vector2i(-inward.y, inward.x)

	## How far a cell is from the edge (0 is the row on the edge) and to which side of the road it lies.
	func depth_of(cell: Vector2i) -> int:
		var d := cell - anchor
		return d.x * inward.x + d.y * inward.y

	func side_of(cell: Vector2i) -> int:
		var d := cell - anchor
		var a := across()
		return d.x * a.x + d.y * a.y


## The sites on a map. `is_path` and `blocked` say which cells cannot be taken (road, enemy buildings).
static func find(map: MapData, is_path: Callable, blocked: Callable = Callable()) -> Array[Site]:
	var sites: Array[Site] = []
	var taken: Dictionary[Vector2i, bool] = {}
	for kind: StringName in [&"camp", &"city"]:
		for lane in map.lane_count():
			var points := map.path_points(lane)
			if points.size() < 2:
				continue
			var end := points[0] if kind == &"camp" else points[points.size() - 1]
			var inward := _inward(map, end)
			if inward == Vector2i.ZERO:
				continue
			var anchor := _anchor(map, end, inward)
			var shared := _site_at(sites, kind, anchor)
			if shared != null:
				shared.lanes.append(lane)
				continue
			var site := Site.new()
			site.kind = kind
			site.lanes.append(lane)
			site.anchor = anchor
			site.inward = inward
			site.gate = _gate(map, anchor, inward)
			for depth in DEPTH:
				for side in range(-HALF_WIDTH, HALF_WIDTH + 1):
					var cell := anchor + inward * depth + site.across() * side
					if not map.is_inside(cell) or taken.has(cell) or is_path.call(cell):
						continue
					if blocked.is_valid() and blocked.call(cell):
						continue
					taken[cell] = true
					site.cells.append(cell)
			sites.append(site)
	return sites


## Which way is into the map from a road end outside it, or zero when the end is inside the map.
static func _inward(map: MapData, end: Vector2) -> Vector2i:
	var size := map.size_in_pixels()
	if end.x < 0.0:
		return Vector2i.RIGHT
	if end.x > size.x:
		return Vector2i.LEFT
	if end.y < 0.0:
		return Vector2i.DOWN
	if end.y > size.y:
		return Vector2i.UP
	return Vector2i.ZERO


## The first cell inside the map where the road comes in from the edge.
static func _anchor(map: MapData, end: Vector2, _inward: Vector2i) -> Vector2i:
	var cell := map.cell_at(end)
	cell.x = clampi(cell.x, 0, map.grid_size.x - 1)
	cell.y = clampi(cell.y, 0, map.grid_size.y - 1)
	return cell


static func _gate(map: MapData, anchor: Vector2i, inward: Vector2i) -> Vector2:
	return map.cell_center(anchor) - Vector2(inward) * map.cell_size * 0.5


static func _site_at(sites: Array[Site], kind: StringName, anchor: Vector2i) -> Site:
	for site in sites:
		if site.kind == kind and site.anchor == anchor:
			return site
	return null
