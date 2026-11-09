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
const META_TREE_DIR := "res://data/trees/meta"
const MAPS_DIR := "res://data/maps"
const DIFFICULTIES_DIR := "res://data/difficulties"
const CAMPAIGNS_DIR := "res://data/campaigns"
const RUN_RULES_PATH := "res://data/rules/run_rules.tres"

var elements: Dictionary[StringName, ElementData] = {}
var towers: Dictionary[StringName, TowerData] = {}
var enemies: Dictionary[StringName, EnemyData] = {}
var wave_sets: Dictionary[StringName, WaveSet] = {}
var maps: Dictionary[StringName, MapData] = {}
var difficulties: Dictionary[StringName, DifficultyData] = {}
var campaigns: Dictionary[StringName, CampaignData] = {}
## Every campaign stage by id.
var stages: Dictionary[StringName, StageData] = {}
var in_run_tree_nodes: Array[TreeNodeData] = []
var meta_tree_nodes: Array[TreeNodeData] = []
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
	difficulties.clear()
	campaigns.clear()
	stages.clear()
	in_run_tree_nodes.clear()
	meta_tree_nodes.clear()

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
	for resource in load_folder(DIFFICULTIES_DIR):
		_index(difficulties, resource as DifficultyData, DIFFICULTIES_DIR)
	for resource in load_folder(CAMPAIGNS_DIR):
		_index(campaigns, resource as CampaignData, CAMPAIGNS_DIR)
	for campaign: CampaignData in campaigns.values():
		for stage in campaign.stages:
			if stage != null and not stage.id.is_empty() and not stages.has(stage.id):
				stages[stage.id] = stage
	_load_tree(IN_RUN_TREE_DIR, in_run_tree_nodes)
	_load_tree(META_TREE_DIR, meta_tree_nodes)

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


func meta_tree() -> TreeGraph:
	return TreeGraph.new(meta_tree_nodes)


## Every problem found in the loaded data, as readable lines. Empty means the data is consistent.
func validate() -> PackedStringArray:
	var errors := _load_errors.duplicate()
	_validate_elements(errors)
	_validate_towers(errors)
	_validate_enemies(errors)
	_validate_waves(errors)
	_validate_maps(errors)
	_validate_difficulties(errors)
	var element_ids: Array[StringName] = []
	element_ids.assign(elements.keys())
	_validate_tree(errors, "in-run tree", in_run_tree_nodes, element_ids)
	_validate_tree(errors, "meta tree", meta_tree_nodes, MetaProgress.BRANCH_NAMES.keys())
	_validate_unlocks(errors)
	_validate_campaigns(errors)
	if run_rules != null and run_rules.starting_lives <= 0:
		errors.append("Run rules: starting lives must be above 0")
	return errors


func _load_tree(dir: String, target: Array[TreeNodeData]) -> void:
	for resource in load_folder(dir):
		var node_data := resource as TreeNodeData
		if node_data == null:
			_load_errors.append("%s: %s is not a TreeNodeData" % [dir, resource.resource_path])
		else:
			target.append(node_data)


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
		if tower.elements.is_empty() or tower.elements.size() > 3:
			errors.append("%s: needs one element, two for a dual or three for a triple" % label)
		for element_id in tower.elements:
			if not elements.has(element_id):
				errors.append("%s: unknown element '%s'" % [label, element_id])
			elif tower.elements.count(element_id) > 1:
				errors.append("%s: element '%s' is listed twice" % [label, element_id])
		if tower.is_dual():
			var indices := tower_element_indices(tower)
			if indices[0] >= 0 and indices[1] >= 0 and indices[0] != indices[1] \
					and not ElementRules.are_neighbours(indices[0], indices[1]) and tower.requires_nodes.is_empty():
				errors.append("%s: hybrids of elements that are not neighbours need requires_nodes" % label)
		if tower.is_triple() and tower.requires_nodes.is_empty():
			errors.append("%s: triples have no bridge node, so they need requires_nodes" % label)
		for node_id in tower.requires_nodes:
			if not in_run_tree_nodes.any(func(n: TreeNodeData) -> bool: return n.id == node_id):
				errors.append("%s: requires unknown skill web node '%s'" % [label, node_id])
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
				elif not group.element.is_empty() and not elements.has(group.element):
					errors.append("%s: group of '%s' has unknown element '%s'" % [label, group.enemy, group.element])


func _validate_maps(errors: PackedStringArray) -> void:
	for map: MapData in maps.values():
		for problem in map.path_errors():
			errors.append("Map '%s': %s" % [map.id, problem])
		if not wave_sets.has(map.wave_set):
			errors.append("Map '%s': unknown wave set '%s'" % [map.id, map.wave_set])


func _validate_difficulties(errors: PackedStringArray) -> void:
	if difficulties.is_empty():
		errors.append("No difficulty levels in %s" % DIFFICULTIES_DIR)
	for difficulty: DifficultyData in difficulties.values():
		if difficulty.enemy_health_multiplier <= 0.0 or difficulty.meta_point_multiplier < 0.0:
			errors.append("Difficulty '%s': multipliers must be above 0" % difficulty.id)


## Meta nodes unlock things by listing their ids; in-run nodes only unlock towers.
func _validate_unlocks(errors: PackedStringArray) -> void:
	var in_run_ids: Dictionary[StringName, bool] = {}
	for node_data in in_run_tree_nodes:
		in_run_ids[node_data.id] = true
		if not (node_data.unlocks_nodes.is_empty() and node_data.unlocks_maps.is_empty() \
				and node_data.unlocks_difficulties.is_empty()):
			errors.append("in-run tree node '%s': only meta tree nodes can unlock nodes, maps or difficulty levels" % node_data.id)
	var gated_maps: Dictionary[StringName, bool] = {}
	var gated_difficulties: Dictionary[StringName, bool] = {}
	for node_data in meta_tree_nodes:
		var label := "meta tree node '%s'" % node_data.id
		if not node_data.unlocks_towers.is_empty():
			errors.append("%s: towers are unlocked in the in-run web, not the meta tree" % label)
		for id in node_data.unlocks_nodes:
			if not in_run_ids.has(id):
				errors.append("%s: unlocks unknown in-run node '%s'" % [label, id])
		for id in node_data.unlocks_maps:
			gated_maps[id] = true
			if not maps.has(id):
				errors.append("%s: unlocks unknown map '%s'" % [label, id])
		for id in node_data.unlocks_difficulties:
			gated_difficulties[id] = true
			if not difficulties.has(id):
				errors.append("%s: unlocks unknown difficulty '%s'" % [label, id])
	if not maps.values().any(func(map: MapData) -> bool: return map.skirmish and not gated_maps.has(map.id)):
		errors.append("Every map is locked behind the meta tree, so a new player has nowhere to play")
	if not difficulties.keys().any(func(id: StringName) -> bool: return not gated_difficulties.has(id)):
		errors.append("Every difficulty level is locked behind the meta tree")


func _validate_tree(errors: PackedStringArray, tree_name: String, nodes: Array[TreeNodeData],
		regions: Array) -> void:
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
		if not node_data.region.is_empty() and not regions.has(node_data.region):
			errors.append("%s: unknown region '%s'" % [label, node_data.region])
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


## The campaign a stage belongs to, or null.
func campaign_of(stage_id: StringName) -> CampaignData:
	for campaign: CampaignData in campaigns.values():
		if campaign.stage_index(stage_id) >= 0:
			return campaign
	return null


func _validate_campaigns(errors: PackedStringArray) -> void:
	var seen_stages: Dictionary[StringName, StringName] = {}
	var node_ids: Dictionary[StringName, bool] = {}
	for node_data in in_run_tree_nodes:
		node_ids[node_data.id] = true
	for campaign: CampaignData in campaigns.values():
		var label := "Campaign '%s'" % campaign.id
		if not campaign.element.is_empty() and not elements.has(campaign.element):
			errors.append("%s: unknown element '%s'" % [label, campaign.element])
		if campaign.stages.is_empty():
			errors.append("%s: has no stages" % label)
		for required in campaign.requires_campaigns:
			if not campaigns.has(required) or required == campaign.id:
				errors.append("%s: requires unknown campaign '%s'" % [label, required])
		for modifier in campaign.reward_modifiers:
			if modifier == null or modifier.stat.is_empty():
				errors.append("%s: a reward modifier has no stat" % label)
		for stage in campaign.stages:
			if stage == null or stage.id.is_empty():
				errors.append("%s: a stage has no id" % label)
				continue
			var stage_label := "Stage '%s'" % stage.id
			if seen_stages.has(stage.id):
				errors.append("%s: id is used twice (in '%s' and '%s')" % [stage_label, seen_stages[stage.id], campaign.id])
			seen_stages[stage.id] = campaign.id
			var map: MapData = maps.get(stage.map)
			if map == null:
				errors.append("%s: unknown map '%s'" % [stage_label, stage.map])
			var wave_set_id := stage.wave_set if not stage.wave_set.is_empty() else (map.wave_set if map != null else &"")
			if not wave_sets.has(wave_set_id):
				errors.append("%s: unknown wave set '%s'" % [stage_label, wave_set_id])
			for element_id in stage.allowed_elements:
				if not elements.has(element_id):
					errors.append("%s: allows unknown element '%s'" % [stage_label, element_id])
			for node_id in stage.starting_nodes:
				if not node_ids.has(node_id):
					errors.append("%s: starts with unknown skill web node '%s'" % [stage_label, node_id])
			for modifier in stage.modifiers:
				if modifier == null or modifier.stat.is_empty():
					errors.append("%s: a modifier has no stat" % stage_label)
	for enemy: EnemyData in enemies.values():
		var label := "Enemy '%s'" % enemy.id
		if not enemy.element.is_empty() and not elements.has(enemy.element):
			errors.append("%s: unknown element '%s'" % [label, enemy.element])
		if enemy.split_count > 0 and not enemies.has(enemy.split_into):
			errors.append("%s: splits into unknown enemy '%s'" % [label, enemy.split_into])
		if enemy.split_into == enemy.id or enemy.summon == enemy.id:
			errors.append("%s: cannot split into or summon itself" % label)
		if enemy.summon_interval > 0.0 and not enemies.has(enemy.summon):
			errors.append("%s: summons unknown enemy '%s'" % [label, enemy.summon])
