extends Node
## Loads every game data file at start-up and indexes it by id. Registered as the DataRegistry autoload.
##
## To add a tower, enemy, wave set or tree node, create a .tres file in the matching data folder.
## validate() checks that every reference between files points at something real; a unit test
## runs it, so a typo in the data fails the tests instead of breaking a run.

const ELEMENTS_DIR := "res://data/elements"
const TOWERS_DIR := "res://data/towers"
const ENEMIES_DIR := "res://data/enemies"
const WAVES_DIR := "res://data/waves"
const IN_RUN_TREE_DIR := "res://data/trees/in_run"
const MAPS_DIR := "res://data/maps"
const RUN_RULES_PATH := "res://data/rules/run_rules.tres"

var elements: Dictionary[StringName, ElementData] = {}
var towers: Dictionary[StringName, TowerData] = {}
var enemies: Dictionary[StringName, EnemyData] = {}
var wave_sets: Dictionary[StringName, WaveSet] = {}
var maps: Dictionary[StringName, MapData] = {}
var in_run_tree_nodes: Array[TreeNodeData] = []
var run_rules: RunRules

var _load_errors: PackedStringArray = []


func _ready() -> void:
	reload()


func reload() -> void:
	_load_errors.clear()
	elements.clear()
	towers.clear()
	enemies.clear()
	wave_sets.clear()
	maps.clear()
	in_run_tree_nodes.clear()

	for resource in load_folder(ELEMENTS_DIR):
		_index(elements, resource as ElementData, ELEMENTS_DIR)
	for resource in load_folder(TOWERS_DIR):
		_index(towers, resource as TowerData, TOWERS_DIR)
	for resource in load_folder(ENEMIES_DIR):
		_index(enemies, resource as EnemyData, ENEMIES_DIR)
	for resource in load_folder(WAVES_DIR):
		_index(wave_sets, resource as WaveSet, WAVES_DIR)
	for resource in load_folder(MAPS_DIR):
		_index(maps, resource as MapData, MAPS_DIR)
	for resource in load_folder(IN_RUN_TREE_DIR):
		var node_data := resource as TreeNodeData
		if node_data == null:
			_load_errors.append("%s: %s is not a TreeNodeData" % [IN_RUN_TREE_DIR, resource.resource_path])
		else:
			in_run_tree_nodes.append(node_data)

	run_rules = load(RUN_RULES_PATH) as RunRules
	if run_rules == null:
		_load_errors.append("Missing run rules at %s" % RUN_RULES_PATH)


## Every resource file in a folder. Works in exported builds too, where files are remapped.
static func load_folder(dir: String) -> Array[Resource]:
	var result: Array[Resource] = []
	for file in ResourceLoader.list_directory(dir):
		if file.ends_with("/"):
			continue
		var resource := load(dir.path_join(file))
		if resource != null:
			result.append(resource)
	return result


## Ring position of an element id, or -1 if the id is unknown or empty.
func element_index(id: StringName) -> int:
	var element: ElementData = elements.get(id)
	return element.ring_index if element != null else -1


func tower_element_indices(tower: TowerData) -> Array[int]:
	var result: Array[int] = []
	for id in tower.elements:
		result.append(element_index(id))
	return result


func in_run_tree() -> TreeGraph:
	return TreeGraph.new(in_run_tree_nodes)


## Every problem found in the loaded data, as readable lines. Empty means the data is consistent.
func validate() -> PackedStringArray:
	var errors := _load_errors.duplicate()
	_validate_elements(errors)
	_validate_towers(errors)
	_validate_enemies(errors)
	_validate_waves(errors)
	_validate_maps(errors)
	_validate_tree(errors, "in-run tree", in_run_tree_nodes)
	if run_rules != null and run_rules.starting_lives <= 0:
		errors.append("Run rules: starting lives must be above 0")
	return errors


func _index(target: Dictionary, resource: Resource, dir: String) -> void:
	if resource == null:
		_load_errors.append("%s: a file has the wrong resource type" % dir)
		return
	var id: StringName = resource.get(&"id")
	if id.is_empty():
		_load_errors.append("%s: %s has no id" % [dir, resource.resource_path])
	elif target.has(id):
		_load_errors.append("%s: duplicate id '%s' in %s" % [dir, id, resource.resource_path])
	else:
		target[id] = resource


func _validate_elements(errors: PackedStringArray) -> void:
	var used: Dictionary[int, StringName] = {}
	for element: ElementData in elements.values():
		if element.ring_index < 0 or element.ring_index >= ElementData.RING_SIZE:
			errors.append("Element '%s': ring_index %d is outside 0-5" % [element.id, element.ring_index])
		elif used.has(element.ring_index):
			errors.append("Element '%s': ring_index %d is already used by '%s'" % [
				element.id, element.ring_index, used[element.ring_index]])
		else:
			used[element.ring_index] = element.id


func _validate_towers(errors: PackedStringArray) -> void:
	for tower: TowerData in towers.values():
		var label := "Tower '%s'" % tower.id
		if tower.elements.is_empty() or tower.elements.size() > 2:
			errors.append("%s: needs one element, or two for a hybrid" % label)
		for element_id in tower.elements:
			if not elements.has(element_id):
				errors.append("%s: unknown element '%s'" % [label, element_id])
		if tower.is_hybrid():
			var indices := tower_element_indices(tower)
			if indices[0] >= 0 and indices[1] >= 0 and not ElementRules.are_neighbours(indices[0], indices[1]):
				errors.append("%s: hybrid elements must be neighbours on the ring" % label)
		if tower.cost <= 0:
			errors.append("%s: cost must be above 0" % label)
		if tower.attacks_per_second <= 0.0 or tower.attack_range <= 0.0:
			errors.append("%s: attacks_per_second and attack_range must be above 0" % label)
		for effect in tower.status_effects:
			if effect == null or effect.kind.is_empty():
				errors.append("%s: a status effect has no kind" % label)


func _validate_enemies(errors: PackedStringArray) -> void:
	for enemy: EnemyData in enemies.values():
		if enemy.max_health <= 0.0 or enemy.speed <= 0.0:
			errors.append("Enemy '%s': max_health and speed must be above 0" % enemy.id)


func _validate_waves(errors: PackedStringArray) -> void:
	for wave_set: WaveSet in wave_sets.values():
		if wave_set.waves.is_empty():
			errors.append("Wave set '%s': has no waves" % wave_set.id)
		for i in wave_set.waves.size():
			var wave: WaveData = wave_set.waves[i]
			var label := "Wave set '%s' wave %d" % [wave_set.id, i + 1]
			if wave == null:
				errors.append("%s: is empty" % label)
				continue
			if not wave.element.is_empty() and not elements.has(wave.element):
				errors.append("%s: unknown element '%s'" % [label, wave.element])
			if wave.groups.is_empty():
				errors.append("%s: has no spawn groups" % label)
			for group in wave.groups:
				if group == null or not enemies.has(group.enemy):
					errors.append("%s: unknown enemy '%s'" % [label, group.enemy if group else &""])
				elif group.count <= 0:
					errors.append("%s: group of '%s' has count %d" % [label, group.enemy, group.count])


func _validate_maps(errors: PackedStringArray) -> void:
	for map: MapData in maps.values():
		for problem in map.path_errors():
			errors.append("Map '%s': %s" % [map.id, problem])
		if not wave_sets.has(map.wave_set):
			errors.append("Map '%s': unknown wave set '%s'" % [map.id, map.wave_set])


func _validate_tree(errors: PackedStringArray, tree_name: String, nodes: Array[TreeNodeData]) -> void:
	var ids: Dictionary[StringName, bool] = {}
	var starts := 0
	for node_data in nodes:
		var label := "%s node '%s'" % [tree_name, node_data.id]
		if node_data.id.is_empty():
			errors.append("%s: a node has no id (%s)" % [tree_name, node_data.resource_path])
		elif ids.has(node_data.id):
			errors.append("%s: duplicate id" % label)
		ids[node_data.id] = true
		if node_data.kind == TreeNodeData.Kind.START:
			starts += 1
		if not node_data.element.is_empty() and not elements.has(node_data.element):
			errors.append("%s: unknown element '%s'" % [label, node_data.element])
		for tower_id in node_data.unlocks_towers:
			if not towers.has(tower_id):
				errors.append("%s: unlocks unknown tower '%s'" % [label, tower_id])
		for modifier in node_data.modifiers:
			if modifier == null or modifier.stat.is_empty():
				errors.append("%s: a modifier has no stat" % label)
		if node_data.cost < 0:
			errors.append("%s: cost cannot be negative" % label)
	if starts != 1:
		errors.append("%s: needs exactly one START node, found %d" % [tree_name, starts])
	for node_data in nodes:
		for link in node_data.links:
			if not ids.has(link):
				errors.append("%s node '%s': links to unknown node '%s'" % [tree_name, node_data.id, link])
	if starts == 1:
		var graph := TreeGraph.new(nodes)
		var reachable := graph.reachable_from_start()
		for node_data in nodes:
			if not reachable.has(node_data.id):
				errors.append("%s node '%s': cannot be reached from the start" % [tree_name, node_data.id])
