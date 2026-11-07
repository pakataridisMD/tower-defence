class_name MetaProgress
extends RefCounted
## The rules that tie the meta tree to runs: what the taken nodes unlock and add, how the next run
## is set up, and what a finished run pays. Pure logic over a profile; the Progress autoload adds
## loading and saving.
##
## Unlocking works by listing: a map, difficulty level or in-run web node named in any meta node's
## unlocks_* list stays locked until one of those meta nodes is taken. Anything no meta node lists
## is open from the start.

## Display names and colours of the meta tree branches, keyed by the nodes' region.
const BRANCH_NAMES: Dictionary[StringName, String] = {
	&"arsenal": "Arsenal",
	&"command": "Command",
	&"expeditions": "Expeditions",
	&"mastery": "Mastery",
}
const BRANCH_COLORS: Dictionary[StringName, Color] = {
	&"arsenal": Color("ef6f6c"),
	&"command": Color("f4c95d"),
	&"expeditions": Color("4cc9f0"),
	&"mastery": Color("b388eb"),
}

## A DataRegistry, or a node with the same fields in tests.
var registry: Node
var profile: PlayerProfile
var tree: TreeState
var selected_map: StringName = &""
var selected_difficulty: StringName = &""


func _init(p_registry: Node, p_profile: PlayerProfile) -> void:
	registry = p_registry
	profile = p_profile
	tree = TreeState.new(TreeGraph.new(registry.meta_tree_nodes), profile.meta_points_earned)
	tree.restore(profile.meta_nodes)
	selected_map = profile.last_map
	selected_difficulty = profile.last_difficulty
	_sync_profile()


## Unspent meta points.
func points() -> int:
	return tree.points


# --- The meta tree ---------------------------------------------------------------

func allocate(id: StringName) -> bool:
	if not tree.allocate(id):
		return false
	_sync_profile()
	return true


func refund(id: StringName) -> bool:
	if not tree.refund(id):
		return false
	_sync_profile()
	return true


## Refunds the whole tree. Respeccing the meta tree is always free.
func reset() -> void:
	tree.reset()
	_sync_profile()


# --- Unlocks ---------------------------------------------------------------------

func is_map_unlocked(id: StringName) -> bool:
	return registry.maps.has(id) and _is_open(&"unlocks_maps", id)


func is_difficulty_unlocked(id: StringName) -> bool:
	return registry.difficulties.has(id) and _is_open(&"unlocks_difficulties", id)


## In-run web nodes that no taken meta node has unlocked yet.
func locked_in_run_nodes() -> Array[StringName]:
	var unlocked := _listed(&"unlocks_nodes", true)
	var result: Array[StringName] = []
	for id in _listed(&"unlocks_nodes", false):
		if not unlocked.has(id):
			result.append(id)
	return result


## The meta node that unlocks a map, difficulty level or in-run node, for "Unlock in ..." hints.
func unlocked_by(field: StringName, id: StringName) -> TreeNodeData:
	for node_data: TreeNodeData in registry.meta_tree_nodes:
		var listed: Array[StringName] = node_data.get(field)
		if listed.has(id):
			return node_data
	return null


func maps_in_order() -> Array[MapData]:
	var result: Array[MapData] = []
	result.assign(registry.maps.values())
	result.sort_custom(func(a: MapData, b: MapData) -> bool: return a.order < b.order)
	return result


func difficulties_in_order() -> Array[DifficultyData]:
	var result: Array[DifficultyData] = []
	result.assign(registry.difficulties.values())
	result.sort_custom(func(a: DifficultyData, b: DifficultyData) -> bool: return a.order < b.order)
	return result


func select_map(id: StringName) -> bool:
	if not is_map_unlocked(id):
		return false
	selected_map = id
	_sync_profile()
	return true


func select_difficulty(id: StringName) -> bool:
	if not is_difficulty_unlocked(id):
		return false
	selected_difficulty = id
	_sync_profile()
	return true


# --- Runs ------------------------------------------------------------------------

## Everything the next run needs: the chosen map and difficulty, the meta tree's bonuses, and the
## in-run nodes that are still locked.
func run_config() -> RunConfig:
	var config := RunConfig.from_registry(registry, selected_map)
	config.run_modifiers = tree.modifiers()
	config.locked_tree_nodes = locked_in_run_nodes()
	config.difficulty = registry.difficulties.get(selected_difficulty)
	return config


## Meta points a finished run pays: per wave cleared, plus a bonus for winning, times the
## difficulty's multiplier.
static func meta_points_for(sim: RunSim) -> int:
	var won := sim.state == RunSim.State.WON
	var multiplier := sim.config.difficulty.meta_point_multiplier if sim.config.difficulty != null else 1.0
	return roundi(sim.config.rules.meta_points_after_run(sim.wave_index, won) * multiplier)


## Pays a finished run's meta points and updates the records. Returns the points earned.
func record_run(sim: RunSim) -> int:
	var earned := meta_points_for(sim)
	profile.meta_points_earned += earned
	tree.points += earned
	profile.runs_played += 1
	if sim.state == RunSim.State.WON:
		profile.runs_won += 1
	profile.best_waves = maxi(profile.best_waves, sim.wave_index)
	profile.enemies_killed += sim.kills
	return earned


# --- Internals -------------------------------------------------------------------

## Copies the tree and the choices back into the profile, and moves a choice that is no longer
## unlocked (after a refund, or a save from an older version) back to the first open option.
func _sync_profile() -> void:
	profile.meta_nodes.clear()
	for id in tree.allocated_ids():
		if id != tree.graph.start_id:
			profile.meta_nodes.append(id)
	if not is_map_unlocked(selected_map):
		selected_map = _first_open_map()
	if not is_difficulty_unlocked(selected_difficulty):
		selected_difficulty = _first_open_difficulty()
	profile.last_map = selected_map
	profile.last_difficulty = selected_difficulty


func _first_open_map() -> StringName:
	for map in maps_in_order():
		if is_map_unlocked(map.id):
			return map.id
	return &""


func _first_open_difficulty() -> StringName:
	for difficulty in difficulties_in_order():
		if is_difficulty_unlocked(difficulty.id):
			return difficulty.id
	return &""


func _is_open(field: StringName, id: StringName) -> bool:
	return not _listed(field, false).has(id) or _listed(field, true).has(id)


## Ids listed in one of the unlocks_* fields, by every meta node or only by the taken ones.
func _listed(field: StringName, taken_only: bool) -> Dictionary[StringName, bool]:
	var result: Dictionary[StringName, bool] = {}
	for node_data: TreeNodeData in registry.meta_tree_nodes:
		if taken_only and not tree.is_allocated(node_data.id):
			continue
		var listed: Array[StringName] = node_data.get(field)
		for id in listed:
			result[id] = true
	return result
