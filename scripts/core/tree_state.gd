class_name TreeState
extends RefCounted
## Which nodes of one tree the player has taken, and how many points are left.
##
## Rules: the start node is always taken; a node can be taken when it links to a taken node
## and the player has enough points; a node can be refunded only if every other taken node
## still connects back to the start without it. With free_pick on (the Talents tree), links do not
## matter: any node can be taken or refunded on its own, as long as the points cover it.

signal changed

var graph: TreeGraph
var points: int = 0
var _allocated: Dictionary[StringName, bool] = {}
var _locked: Dictionary[StringName, bool] = {}
var _granted: Dictionary[StringName, bool] = {}
## When true, nodes need no taken neighbour and refunds need not keep the tree connected.
var free_pick := false


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


## Takes nodes for free, such as a campaign stage's starting nodes. They cost no points, ignore
## locks and cannot be refunded. Each must link to a taken node, so list them from the start outward.
func grant(ids: Array[StringName]) -> void:
	for id in ids:
		if not graph.has_node_id(id) or is_allocated(id):
			continue
		_allocated[id] = true
		_granted[id] = true
	if not ids.is_empty():
		changed.emit()


func is_granted(id: StringName) -> bool:
	return _granted.has(id)


func is_locked(id: StringName) -> bool:
	return _locked.has(id)


## The taken node that closes this one, when they are a pick-one choice. Empty if none does.
func excluded_by(id: StringName) -> StringName:
	for other in graph.exclusions(id):
		if is_allocated(other):
			return other
	return &""


func is_excluded(id: StringName) -> bool:
	return not excluded_by(id).is_empty()


func can_allocate(id: StringName) -> bool:
	if not graph.has_node_id(id) or is_allocated(id) or is_locked(id) or is_excluded(id):
		return false
	if graph.node(id).cost > points:
		return false
	if free_pick:
		return true
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
	if id == graph.start_id or not is_allocated(id) or is_granted(id):
		return false
	if free_pick:
		return true
	return _count_connected_without(id) == _allocated.size() - 1


func refund(id: StringName) -> bool:
	if not can_refund(id):
		return false
	_allocated.erase(id)
	points += graph.node(id).cost
	changed.emit()
	return true


## The shortest chain of nodes that would connect `id` to the taken part of the tree: it starts
## with the taken node it grows from and ends with `id`. Empty when `id` is taken, locked or cannot
## be reached. The tree screen uses it to show what a far node costs.
func path_to(id: StringName) -> Array[StringName]:
	var path: Array[StringName] = []
	if not graph.has_node_id(id) or is_allocated(id) or is_locked(id) or is_excluded(id):
		return path
	if free_pick:
		return [graph.start_id, id] as Array[StringName]
	# Breadth-first from the target outwards; toward[n] is the next step from n back to the target.
	var toward: Dictionary[StringName, StringName] = {id: &""}
	var queue: Array[StringName] = [id]
	var head := 0
	while head < queue.size():
		var current := queue[head]
		head += 1
		for next in graph.neighbours(current):
			if toward.has(next):
				continue
			if is_allocated(next):
				path.append(next)
				var step := current
				while not step.is_empty():
					path.append(step)
					step = toward[step]
				return path
			if is_locked(next) or is_excluded(next):
				continue
			toward[next] = current
			queue.append(next)
	return path


## Points needed to take `id` together with every node on the way to it (see path_to), or -1 when
## it is taken, locked or cannot be reached.
func path_cost(id: StringName) -> int:
	var path := path_to(id)
	if path.is_empty():
		return -1
	var total := 0
	for i in range(1, path.size()):
		total += graph.node(path[i]).cost
	return total


## Takes `id` and every node on the way to it, nearest first, when the points cover all of them.
## Returns the ids taken; empty when nothing was.
func allocate_path(id: StringName) -> Array[StringName]:
	var taken: Array[StringName] = []
	var cost := path_cost(id)
	if cost < 0 or cost > points:
		return taken
	var path := path_to(id)
	for i in range(1, path.size()):
		if not allocate(path[i]):
			break
		taken.append(path[i])
	return taken


## Takes the given nodes in any order, as far as links and points allow, for example when
## loading a save. Ids that cannot be taken (unknown, unlinked, or too expensive) are skipped.
func restore(ids: Array[StringName]) -> void:
	var pending := ids.duplicate()
	var progress := true
	while progress and not pending.is_empty():
		progress = false
		for id in pending.duplicate():
			if allocate(id):
				pending.erase(id)
				progress = true


## Refunds every taken node except the start.
func reset() -> void:
	for id in _allocated:
		if id != graph.start_id and not is_granted(id):
			points += graph.node(id).cost
	_allocated.clear()
	if not graph.start_id.is_empty():
		_allocated[graph.start_id] = true
	for id in _granted:
		_allocated[id] = true
	changed.emit()


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
