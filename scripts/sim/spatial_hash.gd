class_name SpatialHash
extends RefCounted
## Buckets enemies by area so towers only check enemies near them, not every enemy on the map.

var cell_size: float
var _cells: Dictionary[Vector2i, Array] = {}


func _init(p_cell_size: float = 128.0) -> void:
	cell_size = p_cell_size


func clear() -> void:
	_cells.clear()


func insert(enemy: SimEnemy) -> void:
	var key := Vector2i((enemy.position / cell_size).floor())
	if not _cells.has(key):
		_cells[key] = []
	_cells[key].append(enemy)


## Living enemies within radius of center.
func query(center: Vector2, radius: float) -> Array[SimEnemy]:
	var result: Array[SimEnemy] = []
	var radius_squared := radius * radius
	var low := Vector2i(((center - Vector2(radius, radius)) / cell_size).floor())
	var high := Vector2i(((center + Vector2(radius, radius)) / cell_size).floor())
	for x in range(low.x, high.x + 1):
		for y in range(low.y, high.y + 1):
			var key := Vector2i(x, y)
			if not _cells.has(key):
				continue
			for enemy: SimEnemy in _cells[key]:
				if enemy.alive and enemy.position.distance_squared_to(center) <= radius_squared:
					result.append(enemy)
	return result
