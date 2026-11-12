class_name RunConfig
extends RefCounted
## Everything a run needs. Built from the loaded data, or by hand in tests.

## Endless skirmish: the horde starts at half strength and grows 3% a wave, in numbers and in health
## each. Played by the bot on Switchback: a new player falls around wave 15 whatever the rate (the
## first Warden after the map's own waves); a player who has freed the six lands reaches about wave
## 95 at 3%, 80 at 4% and 60 at 5%.
const ENDLESS_START := 0.5
const ENDLESS_GROWTH := 1.03

var map: MapData
var wave_set: WaveSet
var rules: RunRules
var towers: Dictionary[StringName, TowerData] = {}
var enemies: Dictionary[StringName, EnemyData] = {}
var elements: Dictionary[StringName, ElementData] = {}
var tree_nodes: Array[TreeNodeData] = []
## Skills the player can cast during a wave, by id.
var skills: Dictionary[StringName, SkillData] = {}
## Modifiers that last the whole run, such as meta tree bonuses.
var run_modifiers: Array[Modifier] = []
## In-run tree nodes the player has not unlocked yet in the meta tree.
var locked_tree_nodes: Array[StringName] = []
## The difficulty level picked for the run. Null plays at normal strength.
var difficulty: DifficultyData
## Endless skirmish: after the last wave the waves keep coming. The horde starts at endless_start of
## the map's numbers and health and grows by endless_growth every wave, in numbers and in health
## each (see RunSim.endless_multiplier).
var endless := false
var endless_start := ENDLESS_START
var endless_growth := ENDLESS_GROWTH
## Skill web nodes taken for free at the start, such as a campaign stage's starting nodes.
var granted_tree_nodes: Array[StringName] = []
## The campaign stage being played and its campaign, or null in a skirmish.
var stage: StageData
var campaign: CampaignData
## The heroes the player brings, up to HeroData.MAX_PARTY. Each can be summoned once.
var heroes: Array[HeroData] = []
## Units the player can muster in the counter-attack of the final assault, by id.
var allies: Dictionary[StringName, AllyData] = {}
## Heroes who arrive during this run at a wave (HeroData.arrives_at_wave) and join the party then.
var arriving_heroes: Array[HeroData] = []
## Enemy caves break open every few waves (see Caves). Tests that count lanes turn them off.
var caves := true
## Where the caves open is random, from this seed. 0 picks a seed from the map and stage, so the same
## stage always gets the same caves (the balance check and tests rely on that); the game sets a new
## one for each run.
var cave_seed := 0


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
	config.skills = registry.skills
	config.allies = registry.allies
	return config


## Every enemy's health is multiplied by this.
func enemy_health_multiplier() -> float:
	return difficulty.enemy_health_multiplier if difficulty != null else 1.0


## Every wave brings this many times as many enemies (bosses excepted).
func enemy_count_multiplier() -> float:
	return difficulty.enemy_count_multiplier if difficulty != null else 1.0


## Starting gold is multiplied by this (the difficulty's).
func starting_gold_multiplier() -> float:
	return difficulty.starting_gold_multiplier if difficulty != null else 1.0


func element_index(id: StringName) -> int:
	var element: ElementData = elements.get(id)
	return element.ring_index if element != null else -1


## Colour of the element at a ring index, or white for -1.
func element_color_at(ring_index: int) -> Color:
	for element: ElementData in elements.values():
		if element.ring_index == ring_index:
			return element.color
	return Color.WHITE


func element_color(id: StringName) -> Color:
	var element: ElementData = elements.get(id)
	return element.color if element != null else Color.WHITE
