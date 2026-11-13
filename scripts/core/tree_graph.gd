class_name TreeGraph
extends RefCounted
## The nodes of one skill tree and the links between them. Links work in both directions.

var start_id: StringName
var _nodes: Dictionary[StringName, TreeNodeData] = {}
var _links: Dictionary[StringName, Array] = {}
var _excludes: Dictionary[StringName, Array] = {}
var _groups: Dictionary[StringName, Array] = {}
var _dependents: Dictionary[StringName, Array] = {}


func _init(nodes: Array[TreeNodeData]) -> void:
	for data in nodes:
		_nodes[data.id] = data
		_links[data.id] = []
		if data.kind == TreeNodeData.Kind.START:
			start_id = data.id
		if not data.choice_group.is_empty():
			_add_unique(_groups, data.choice_group, data.id)
	for data in nodes:
		for other in data.links:
			# Links to unknown ids are skipped here and reported by DataRegistry.validate().
			if _nodes.has(other) and other != data.id:
				_connect(data.id, other)
		for other in data.excludes:
			if _nodes.has(other) and other != data.id:
				_add_unique(_excludes, data.id, other)
				_add_unique(_excludes, other, data.id)
		for other in data.requires:
			if _nodes.has(other) and other != data.id:
				_add_unique(_dependents, other, data.id)


func has_node_id(id: StringName) -> bool:
	return _nodes.has(id)


func node(id: StringName) -> TreeNodeData:
	return _nodes.get(id)


func ids() -> Array[StringName]:
	var result: Array[StringName] = []
	result.assign(_nodes.keys())
	return result


func size() -> int:
	return _nodes.size()


## Nodes that cannot be taken together with this one (pick-one choices), in both directions.
func exclusions(id: StringName) -> Array[StringName]:
	var result: Array[StringName] = []
	result.assign(_excludes.get(id, []))
	return result


## The other nodes of this node's branch (TreeNodeData.choice_group), of which only choice_limit
## can be taken together. Empty for a node outside any branch.
func branch_mates(id: StringName) -> Array[StringName]:
	var result: Array[StringName] = []
	var data := node(id)
	if data == null or data.choice_group.is_empty():
		return result
	for other: StringName in _groups.get(data.choice_group, []):
		if other != id:
			result.append(other)
	return result


## The nodes that must all be taken before this one (TreeNodeData.requires). Empty for most nodes.
func requirements(id: StringName) -> Array[StringName]:
	var result: Array[StringName] = []
	var data := node(id)
	if data != null:
		for other in data.requires:
			if _nodes.has(other):
				result.append(other)
	return result


## The combination nodes that require this one.
func dependents(id: StringName) -> Array[StringName]:
	var result: Array[StringName] = []
	result.assign(_dependents.get(id, []))
	return result


static func _add_unique(map: Dictionary[StringName, Array], key: StringName, value: StringName) -> void:
	if not map.has(key):
		map[key] = []
	if not map[key].has(value):
		map[key].append(value)


func neighbours(id: StringName) -> Array[StringName]:
	var result: Array[StringName] = []
	result.assign(_links.get(id, []))
	return result


## Ids reachable from the start node by following links, and the combination nodes whose
## requirements all are.
func reachable_from_start() -> Array[StringName]:
	var result: Array[StringName] = []
	if start_id.is_empty():
		return result
	var seen: Dictionary[StringName, bool] = {start_id: true}
	var queue: Array[StringName] = [start_id]
	while not queue.is_empty():
		var current: StringName = queue.pop_back()
		result.append(current)
		for next in neighbours(current):
			if not seen.has(next):
				seen[next] = true
				queue.append(next)
	for id: StringName in _nodes:
		var needs := requirements(id)
		if seen.has(id) or needs.is_empty():
			continue
		var met := true
		for other in needs:
			met = met and seen.has(other)
		if met:
			result.append(id)
	return result


func _connect(a: StringName, b: StringName) -> void:
	if not _links[a].has(b):
		_links[a].append(b)
	if not _links[b].has(a):
		_links[b].append(a)
