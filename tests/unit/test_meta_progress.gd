extends GutTest
## The rules that tie the meta tree to runs, on a small made-up tree:
##
##   gold (1) - start - expedition (2) - hard_mode (3)
##
## gold adds 30 starting gold. expedition unlocks the map "far" and the in-run node "secret".
## hard_mode unlocks the difficulty level "hard".

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")


## Stands in for the DataRegistry autoload: MetaProgress only reads these fields.
class FakeRegistry:
	extends Node
	var maps: Dictionary[StringName, MapData] = {}
	var difficulties: Dictionary[StringName, DifficultyData] = {}
	var meta_tree_nodes: Array[TreeNodeData] = []
	var in_run_tree_nodes: Array[TreeNodeData] = []
	var wave_sets: Dictionary[StringName, WaveSet] = {}
	var towers: Dictionary[StringName, TowerData] = {}
	var enemies: Dictionary[StringName, EnemyData] = {}
	var elements: Dictionary[StringName, ElementData] = {}
	var run_rules := RunRules.new()


var registry: FakeRegistry


func _node(id: StringName, kind: TreeNodeData.Kind, links: Array[StringName], cost: int) -> TreeNodeData:
	var data := TreeNodeData.new()
	data.id = id
	data.display_name = String(id).capitalize()
	data.kind = kind
	data.links = links
	data.cost = cost
	return data


func _map(id: StringName, order: int) -> MapData:
	var map := MapData.new()
	map.id = id
	map.display_name = String(id).capitalize()
	map.order = order
	return map


func _difficulty(id: StringName, order: int, health: float, points: float) -> DifficultyData:
	var difficulty := DifficultyData.new()
	difficulty.id = id
	difficulty.display_name = String(id).capitalize()
	difficulty.order = order
	difficulty.enemy_health_multiplier = health
	difficulty.meta_point_multiplier = points
	return difficulty


func before_each() -> void:
	registry = autofree(FakeRegistry.new())
	registry.maps[&"far"] = _map(&"far", 1)
	registry.maps[&"near"] = _map(&"near", 0)
	registry.difficulties[&"hard"] = _difficulty(&"hard", 1, 1.4, 1.5)
	registry.difficulties[&"normal"] = _difficulty(&"normal", 0, 1.0, 1.0)
	var gold := _node(&"gold", TreeNodeData.Kind.ENTRY, [&"start"], 1)
	gold.modifiers = [Modifier.create(&"starting_gold", Modifier.Kind.FLAT, 30.0)]
	var expedition := _node(&"expedition", TreeNodeData.Kind.ENTRY, [&"start"], 2)
	expedition.unlocks_maps = [&"far"]
	expedition.unlocks_nodes = [&"secret"]
	var hard_mode := _node(&"hard_mode", TreeNodeData.Kind.NOTABLE, [&"expedition"], 3)
	hard_mode.unlocks_difficulties = [&"hard"]
	registry.meta_tree_nodes = [_node(&"start", TreeNodeData.Kind.START, [], 0), gold, expedition, hard_mode]


func _meta(points_earned: int = 0, nodes: Array[StringName] = []) -> MetaProgress:
	var profile := PlayerProfile.new()
	profile.meta_points_earned = points_earned
	profile.meta_nodes = nodes
	return MetaProgress.new(registry, profile)


## A finished run on the real data, as MetaProgress sees it at the end.
func _finished_run(state: RunSim.State, waves_cleared: int, kills: int, difficulty: DifficultyData = null) -> RunSim:
	var real: Node = autofree(DataRegistryScript.new())
	real.reload()
	var config := RunConfig.from_registry(real, &"switchback")
	config.rules = config.rules.duplicate() as RunRules
	config.rules.meta_points_per_wave = 1
	config.rules.meta_points_for_win = 2
	config.difficulty = difficulty
	var sim := RunSim.new(config)
	sim.state = state
	sim.wave_index = waves_cleared
	sim.kills = kills
	return sim


# --- Unlocks ---------------------------------------------------------------------

func test_listed_things_stay_locked_until_their_node_is_taken() -> void:
	var meta := _meta(10)
	assert_true(meta.is_map_unlocked(&"near"), "no meta node lists it, so it is open")
	assert_false(meta.is_map_unlocked(&"far"))
	assert_true(meta.is_difficulty_unlocked(&"normal"))
	assert_false(meta.is_difficulty_unlocked(&"hard"))
	var secret: Array[StringName] = [&"secret"]
	assert_eq(meta.locked_in_run_nodes(), secret)

	assert_true(meta.allocate(&"expedition"))
	assert_true(meta.is_map_unlocked(&"far"))
	assert_eq(meta.locked_in_run_nodes().size(), 0)
	assert_false(meta.is_difficulty_unlocked(&"hard"))
	assert_true(meta.allocate(&"hard_mode"))
	assert_true(meta.is_difficulty_unlocked(&"hard"))


func test_unknown_maps_and_levels_are_never_open() -> void:
	var meta := _meta()
	assert_false(meta.is_map_unlocked(&"nowhere"))
	assert_false(meta.is_difficulty_unlocked(&"impossible"))


func test_unlocked_by_names_the_meta_node() -> void:
	var meta := _meta()
	assert_eq(meta.unlocked_by(&"unlocks_maps", &"far").id, &"expedition")
	assert_eq(meta.unlocked_by(&"unlocks_difficulties", &"hard").id, &"hard_mode")
	assert_null(meta.unlocked_by(&"unlocks_maps", &"near"))


func test_lists_are_in_menu_order() -> void:
	var meta := _meta()
	assert_eq(meta.maps_in_order().map(func(map: MapData) -> StringName: return map.id), [&"near", &"far"])
	assert_eq(meta.difficulties_in_order().map(func(level: DifficultyData) -> StringName: return level.id),
		[&"normal", &"hard"])


# --- Choices ---------------------------------------------------------------------

func test_a_new_player_starts_on_the_first_open_choices() -> void:
	var meta := _meta()
	assert_eq(meta.selected_map, &"near")
	assert_eq(meta.selected_difficulty, &"normal")


func test_locked_choices_cannot_be_picked() -> void:
	var meta := _meta()
	assert_false(meta.select_map(&"far"))
	assert_false(meta.select_difficulty(&"hard"))
	assert_eq(meta.selected_map, &"near")
	assert_eq(meta.selected_difficulty, &"normal")


func test_a_refund_moves_choices_it_locks_back_to_open_ones() -> void:
	var meta := _meta(10)
	meta.allocate(&"expedition")
	meta.allocate(&"hard_mode")
	assert_true(meta.select_map(&"far"))
	assert_true(meta.select_difficulty(&"hard"))
	assert_true(meta.refund(&"hard_mode"))
	assert_eq(meta.selected_difficulty, &"normal")
	assert_eq(meta.selected_map, &"far", "still unlocked")
	assert_true(meta.refund(&"expedition"))
	assert_eq(meta.selected_map, &"near")
	assert_eq(meta.profile.last_map, &"near")


func test_saved_choices_that_are_locked_fall_back() -> void:
	var profile := PlayerProfile.new()
	profile.last_map = &"far"
	profile.last_difficulty = &"hard"
	var meta := MetaProgress.new(registry, profile)
	assert_eq(meta.selected_map, &"near")
	assert_eq(meta.selected_difficulty, &"normal")


# --- The tree and the profile ----------------------------------------------------

func test_saved_nodes_are_taken_again_in_any_order() -> void:
	var meta := _meta(6, [&"hard_mode", &"expedition"])
	assert_true(meta.tree.is_allocated(&"expedition"))
	assert_true(meta.tree.is_allocated(&"hard_mode"))
	assert_eq(meta.points(), 1, "6 earned, 5 spent")


func test_the_profile_lists_the_taken_nodes_without_the_start() -> void:
	var meta := _meta(3)
	meta.allocate(&"gold")
	meta.allocate(&"expedition")
	var taken: Array[StringName] = [&"gold", &"expedition"]
	assert_eq(meta.profile.meta_nodes, taken)


func test_reset_refunds_every_node_for_free() -> void:
	var meta := _meta(6)
	meta.allocate(&"gold")
	meta.allocate(&"expedition")
	meta.reset()
	assert_eq(meta.points(), 6)
	assert_eq(meta.profile.meta_nodes.size(), 0)


func test_the_next_run_gets_the_bonuses_choices_and_locks() -> void:
	var meta := _meta(10)
	meta.allocate(&"gold")
	var config := meta.run_config()
	assert_eq(config.map.id, &"near")
	assert_eq(config.difficulty.id, &"normal")
	assert_eq(config.run_modifiers.size(), 1)
	assert_eq(config.run_modifiers[0].stat, &"starting_gold")
	var secret: Array[StringName] = [&"secret"]
	assert_eq(config.locked_tree_nodes, secret)

	meta.allocate(&"expedition")
	meta.allocate(&"hard_mode")
	meta.select_map(&"far")
	meta.select_difficulty(&"hard")
	config = meta.run_config()
	assert_eq(config.map.id, &"far")
	assert_eq(config.enemy_health_multiplier(), 1.4)
	assert_eq(config.locked_tree_nodes.size(), 0)


# --- Finished runs ---------------------------------------------------------------

func test_a_lost_run_pays_a_point_per_wave_cleared() -> void:
	var meta := _meta()
	var earned := meta.record_run(_finished_run(RunSim.State.LOST, 4, 37))
	assert_eq(earned, 4)
	assert_eq(meta.points(), 4)
	assert_eq(meta.profile.meta_points_earned, 4)
	assert_eq(meta.profile.runs_played, 1)
	assert_eq(meta.profile.runs_won, 0)
	assert_eq(meta.profile.best_waves, 4)
	assert_eq(meta.profile.enemies_killed, 37)


func test_a_win_pays_a_bonus_and_harder_levels_pay_more() -> void:
	var meta := _meta()
	assert_eq(meta.record_run(_finished_run(RunSim.State.WON, 10, 100)), 12)
	var hard: DifficultyData = registry.difficulties[&"hard"]
	assert_eq(meta.record_run(_finished_run(RunSim.State.WON, 10, 100, hard)), 18, "12 x 1.5")
	assert_eq(meta.points(), 30)
	assert_eq(meta.profile.runs_won, 2)
	assert_eq(meta.profile.best_waves, 10)
	assert_eq(meta.profile.enemies_killed, 200)


func test_records_keep_the_best_run() -> void:
	var meta := _meta()
	meta.record_run(_finished_run(RunSim.State.LOST, 7, 50))
	meta.record_run(_finished_run(RunSim.State.LOST, 3, 20))
	assert_eq(meta.profile.best_waves, 7)
	assert_eq(meta.profile.runs_played, 2)
