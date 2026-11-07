class_name TreeState
extends RefCounted
## Which nodes of one tree the player has taken, and how many points are left.
##
## Rules: the start node is always taken; a node can be taken when it links to a taken node
## and the player has enough points; a node can be refunded only if every other taken node
## still connects back to the start without it.

signal changed

var graph: TreeGraph
var points: int = 0
var _allocated: Dictionary[StringName, bool] = {}
var _locked: Dictionary[StringName, bool] = {}


func _init(p_graph: TreeGraph, p_points: int = 0) -> void:
	graph = p_graph
	points = p_points
	if not graph.start_id.is_empty():
		_allocated[graph.start_id] = true


func is_allocated(id: StringName) -> bool:
	return _allocated.has(id)


func allocated_ids() -> Array[StringName]:
	var result: Array[StringName] = []
	result.assign(_allocated.keys())
	return result


## Locked nodes cannot be taken until something (such as the meta tree) unlocks them.
func lock(ids: Array[StringName]) -> void:
	for id in ids:
		_locked[id] = true


func is_locked(id: StringName) -> bool:
	return _locked.has(id)


func can_allocate(id: StringName) -> bool:
	if not graph.has_node_id(id) or is_allocated(id) or is_locked(id):
		return false
	if graph.node(id).cost > points:
		return false
	for other in graph.neighbours(id):
		if is_allocated(other):
			return true
	return false


func allocate(id: StringName) -> bool:
	if not can_allocate(id):
		return false
	points -= graph.node(id).cost
	_allocated[id] = true
	changed.emit()
	return true


func can_refund(id: StringName) -> bool:
	if id == graph.start_id or not is_allocated(id):
		return false
	return _count_connected_without(id) == _allocated.size() - 1


func refund(id: StringName) -> bool:
	if not can_refund(id):
		return false
	_allocated.erase(id)
	points += graph.node(id).cost
	changed.emit()
	return true


## Every modifier granted by the taken nodes.
func modifiers() -> Array[Modifier]:
	var result: Array[Modifier] = []
	for id in _allocated:
		result.append_array(graph.node(id).modifiers)
	return result


## Ids of every tower the taken nodes unlock, without duplicates.
func unlocked_towers() -> Array[StringName]:
	var result: Array[StringName] = []
	for id in _allocated:
		for tower in graph.node(id).unlocks_towers:
			if not result.has(tower):
				result.append(tower)
	return result


## How many taken nodes still connect to the start if `excluded` is removed.
func _count_connected_without(excluded: StringName) -> int:
	var seen: Dictionary[StringName, bool] = {graph.start_id: true}
	var queue: Array[StringName] = [graph.start_id]
	while not queue.is_empty():
		var current: StringName = queue.pop_back()
		for next in graph.neighbours(current):
			if next == excluded or seen.has(next) or not is_allocated(next):
				continue
			seen[next] = true
			queue.append(next)
	return seen.size()
