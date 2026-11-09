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
	var map: MapData = registry.maps.get(id)
	return map != null and map.skirmish and _is_open(&"unlocks_maps", id)


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


## Maps for skirmish runs, in menu order. Campaign-only maps are left out.
func maps_in_order() -> Array[MapData]:
	var result: Array[MapData] = []
	for map: MapData in registry.maps.values():
		if map.skirmish:
			result.append(map)
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
	config.run_modifiers.append_array(campaign_rewards())
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


# --- Campaign --------------------------------------------------------------------

## Share of lives left needed for two stars. Three stars means losing no lives at all.
const TWO_STAR_LIVES := 0.5


func campaigns_in_order() -> Array[CampaignData]:
	var result: Array[CampaignData] = []
	result.assign(registry.campaigns.values())
	result.sort_custom(func(a: CampaignData, b: CampaignData) -> bool: return a.order < b.order)
	return result


## Best stars for a stage: 0 until it is won, then 1 to 3.
func stars(stage_id: StringName) -> int:
	return profile.stage_stars.get(stage_id, 0)


func campaign_stars(campaign: CampaignData) -> int:
	var total := 0
	for stage in campaign.stages:
		total += stars(stage.id)
	return total


func is_campaign_complete(campaign_id: StringName) -> bool:
	var campaign: CampaignData = registry.campaigns.get(campaign_id)
	if campaign == null or campaign.stages.is_empty():
		return false
	return campaign.stages.all(func(stage: StageData) -> bool: return stars(stage.id) > 0)


func is_campaign_unlocked(campaign_id: StringName) -> bool:
	var campaign: CampaignData = registry.campaigns.get(campaign_id)
	if campaign == null:
		return false
	return campaign.requires_campaigns.all(func(id: StringName) -> bool: return is_campaign_complete(id))


## A stage opens once its campaign is open and the stage before it has been won.
func is_stage_unlocked(stage_id: StringName) -> bool:
	var campaign: CampaignData = registry.campaign_of(stage_id)
	if campaign == null or not is_campaign_unlocked(campaign.id):
		return false
	var index := campaign.stage_index(stage_id)
	return index == 0 or stars(campaign.stages[index - 1].id) > 0


## The first stage of a campaign that is open and not yet won, or null.
func next_stage(campaign: CampaignData) -> StageData:
	for stage in campaign.stages:
		if is_stage_unlocked(stage.id) and stars(stage.id) == 0:
			return stage
	return null


## The stage after this one in its campaign, or null after the last.
func stage_after(stage_id: StringName) -> StageData:
	var campaign: CampaignData = registry.campaign_of(stage_id)
	if campaign == null:
		return null
	var index := campaign.stage_index(stage_id)
	return campaign.stages[index + 1] if index + 1 < campaign.stages.size() else null


## Lasting bonuses from every finished campaign. They apply to every run.
func campaign_rewards() -> Array[Modifier]:
	var result: Array[Modifier] = []
	for campaign: CampaignData in registry.campaigns.values():
		if is_campaign_complete(campaign.id):
			result.append_array(campaign.reward_modifiers)
	return result


## Everything a campaign stage needs: its map and waves, the meta tree's bonuses, the rewards of
## finished campaigns, the stage's own rules, and the skill web cut down to its elements.
func stage_config(stage_id: StringName) -> RunConfig:
	var stage: StageData = registry.stages.get(stage_id)
	if stage == null:
		return null
	var config := RunConfig.from_registry(registry, stage.map)
	if not stage.wave_set.is_empty():
		config.wave_set = registry.wave_sets.get(stage.wave_set)
	config.stage = stage
	config.campaign = registry.campaign_of(stage_id)
	config.run_modifiers = tree.modifiers()
	config.run_modifiers.append_array(campaign_rewards())
	config.run_modifiers.append_array(stage.modifiers)
	config.locked_tree_nodes = locked_in_run_nodes()
	for id in closed_nodes(stage):
		if not config.locked_tree_nodes.has(id):
			config.locked_tree_nodes.append(id)
	config.granted_tree_nodes = stage.starting_nodes
	config.difficulty = registry.difficulties.get(selected_difficulty)
	return config


## Skill web nodes a stage closes: every node of an element it does not allow, and the bridges and
## keystones next to one.
func closed_nodes(stage: StageData) -> Array[StringName]:
	var result: Array[StringName] = []
	if stage.allowed_elements.is_empty():
		return result
	var graph := TreeGraph.new(registry.in_run_tree_nodes)
	var closed := func(node_data: TreeNodeData) -> bool:
		return not node_data.region.is_empty() and not stage.allowed_elements.has(node_data.region)
	for node_data: TreeNodeData in registry.in_run_tree_nodes:
		if node_data.kind == TreeNodeData.Kind.START:
			continue
		var shut: bool = closed.call(node_data)
		if not shut and node_data.region.is_empty():
			for other in graph.neighbours(node_data.id):
				if closed.call(graph.node(other)):
					shut = true
					break
		if shut:
			result.append(node_data.id)
	return result


## Stars a finished stage earns: none for a loss, three for losing no lives, two for keeping at
## least half of them, otherwise one.
static func stars_for(sim: RunSim) -> int:
	if sim.state != RunSim.State.WON:
		return 0
	if sim.lives >= sim.starting_lives:
		return 3
	if sim.lives >= ceili(sim.starting_lives * TWO_STAR_LIVES):
		return 2
	return 1


## Records a finished campaign stage: keeps the best stars and pays the first-win bonus. Returns
## {stars, first_clear_points, campaign_complete} for the end screen. Call it after record_run.
func record_stage(sim: RunSim) -> Dictionary:
	var stage := sim.config.stage
	var result := {"stars": 0, "first_clear_points": 0, "campaign_complete": false, "best": 0}
	if stage == null:
		return result
	var earned := stars_for(sim)
	var before := stars(stage.id)
	var campaign_was_done := sim.config.campaign != null and is_campaign_complete(sim.config.campaign.id)
	result["stars"] = earned
	if earned > before:
		profile.stage_stars[stage.id] = earned
	if earned > 0 and before == 0 and stage.first_clear_points > 0:
		profile.meta_points_earned += stage.first_clear_points
		tree.points += stage.first_clear_points
		result["first_clear_points"] = stage.first_clear_points
	result["best"] = stars(stage.id)
	if sim.config.campaign != null and not campaign_was_done:
		result["campaign_complete"] = is_campaign_complete(sim.config.campaign.id)
	return result


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
