class_name RunConfig
extends RefCounted
## Everything a run needs. Built from the loaded data, or by hand in tests.

var map: MapData
var wave_set: WaveSet
var rules: RunRules
var towers: Dictionary[StringName, TowerData] = {}
var enemies: Dictionary[StringName, EnemyData] = {}
var elements: Dictionary[StringName, ElementData] = {}
var tree_nodes: Array[TreeNodeData] = []
## Modifiers that last the whole run, such as meta tree bonuses.
var run_modifiers: Array[Modifier] = []
## In-run tree nodes the player has not unlocked yet in the meta tree.
var locked_tree_nodes: Array[StringName] = []
## The difficulty level picked for the run. Null plays at normal strength.
var difficulty: DifficultyData


## Config for a map using the data loaded by a DataRegistry.
static func from_registry(registry: Node, map_id: StringName) -> RunConfig:
	var config := RunConfig.new()
	config.map = registry.maps.get(map_id)
	if config.map != null:
		config.wave_set = registry.wave_sets.get(config.map.wave_set)
	config.rules = registry.run_rules
	config.towers = registry.towers
	config.enemies = registry.enemies
	config.elements = registry.elements
	config.tree_nodes = registry.in_run_tree_nodes
	return config


## Every enemy's health is multiplied by this.
func enemy_health_multiplier() -> float:
	return difficulty.enemy_health_multiplier if difficulty != null else 1.0


func element_index(id: StringName) -> int:
	var element: ElementData = elements.get(id)
	return element.ring_index if element != null else -1


func element_color(id: StringName) -> Color:
	var element: ElementData = elements.get(id)
	return element.color if element != null else Color.WHITE
