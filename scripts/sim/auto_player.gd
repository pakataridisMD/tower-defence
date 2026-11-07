class_name AutoPlayer
extends RefCounted
## A simple scripted player. Tests use it to check that a full run can be won, and the game
## runs it with the --autoplay flag to record footage without a human.

const DEFAULT_NODES: Array[StringName] = [
	&"fire_entry", &"storm_entry", &"fire_cw", &"storm_ccw", &"bridge_plasma",
	&"fire_core", &"storm_core", &"fire_notable", &"storm_cw", &"storm_notable",
	&"nature_entry", &"nature_ccw", &"bridge_thornstorm", &"fire_ccw",
	&"nature_core", &"nature_notable", &"nature_cw",
]
const DEFAULT_TOWERS: Array[StringName] = [
	&"hybrid_plasma", &"fire_brazier", &"storm_spire", &"hybrid_thornstorm", &"nature_thornbush",
]
## Spacing of the points used to measure how much path a cell covers.
const PATH_SAMPLE_SPACING := 32.0

var sim: RunSim
## Tree nodes to take, in order. A node that cannot be taken yet is retried next time.
var node_priority: Array[StringName] = []
## Towers to build, best first. The bot builds the first unlocked one it can afford.
var tower_priority: Array[StringName] = []
var max_towers := 40

var _path_samples := PackedVector2Array()
var _coverage_cache: Dictionary[Vector3i, int] = {}


func _init(
		p_sim: RunSim,
		p_nodes: Array[StringName] = DEFAULT_NODES,
		p_towers: Array[StringName] = DEFAULT_TOWERS
) -> void:
	sim = p_sim
	node_priority = p_nodes
	tower_priority = p_towers
	var offset := 0.0
	while offset <= sim.path_length:
		_path_samples.append(sim.path_curve.sample_baked(offset))
		offset += PATH_SAMPLE_SPACING


## Spend points and gold, then start the next wave. Does nothing unless the sim is building.
func play_build_phase() -> void:
	if sim.state != RunSim.State.BUILDING:
		return
	spend_points()
	build_towers()
	sim.start_next_wave()


func spend_points() -> void:
	var took_one := true
	while took_one and sim.tree.points > 0:
		took_one = false
		for id in node_priority:
			if sim.allocate_node(id):
				took_one = true
				break


func build_towers() -> void:
	while sim.towers.size() < max_towers:
		var tower_id := _affordable_tower()
		if tower_id.is_empty():
			return
		var cell := best_cell(tower_id)
		if cell.x < 0 or sim.place_tower(tower_id, cell) == null:
			return


## The free cell where this tower covers the most path, or (-1, -1) if none is free.
func best_cell(tower_id: StringName) -> Vector2i:
	var data: TowerData = sim.config.towers[tower_id]
	var reach := data.stat_with(&"attack_range", sim.modifiers())
	var best := Vector2i(-1, -1)
	var best_score := 0
	var grid := sim.config.map.grid_size
	for x in grid.x:
		for y in grid.y:
			var cell := Vector2i(x, y)
			if not sim.can_place(tower_id, cell):
				continue
			var score := coverage(cell, reach)
			if score > best_score:
				best_score = score
				best = cell
	return best


## How many path sample points lie within reach of a cell's centre.
func coverage(cell: Vector2i, reach: float) -> int:
	var key := Vector3i(cell.x, cell.y, roundi(reach))
	if _coverage_cache.has(key):
		return _coverage_cache[key]
	var center := sim.config.map.cell_center(cell)
	var reach_squared := reach * reach
	var count := 0
	for point in _path_samples:
		if point.distance_squared_to(center) <= reach_squared:
			count += 1
	_coverage_cache[key] = count
	return count


func _affordable_tower() -> StringName:
	for id in tower_priority:
		if sim.is_unlocked(id) and sim.gold >= sim.tower_price(id):
			return id
	return &""
