class_name MetaProgress
extends RefCounted
## The rules that tie the meta tree to runs: what the taken nodes unlock and add, how the next run
## is set up, and what a finished run pays. Pure logic over a profile; the Progress autoload adds
## loading and saving.
##
## Unlocking works by listing: a map, difficulty level or in-run web node named in any meta node's
## unlocks_* list stays locked until one of those meta nodes is taken. Anything no meta node lists
## is open from the start.

## Display names and colours of the meta tree branches, keyed by the nodes' region: four inner
## wings, the Starpath ring road between them and one constellation per element on the outer ring
## (in the element's own colour). The tree itself is written by tools/meta/gen_meta_tree.py.
const BRANCH_NAMES: Dictionary[StringName, String] = {
	&"arsenal": "Arsenal",
	&"command": "Command",
	&"expeditions": "Expeditions",
	&"mastery": "Mastery",
	&"starpath": "Starpath",
	&"fire": "Fire",
	&"storm": "Storm",
	&"nature": "Nature",
	&"water": "Water",
	&"earth": "Earth",
	&"void": "Void",
}
const BRANCH_COLORS: Dictionary[StringName, Color] = {
	&"arsenal": Color("ef6f6c"),
	&"command": Color("f4c95d"),
	&"expeditions": Color("4cc9f0"),
	&"mastery": Color("b388eb"),
	&"starpath": Color("c9d3ee"),
	&"fire": Color("e4572e"),
	&"storm": Color("f2c14e"),
	&"nature": Color("5bb450"),
	&"water": Color("2e86de"),
	&"earth": Color("a0785a"),
	&"void": Color("8e5cd9"),
}

## Meta points are paid for records, not for playing: each campaign stage and each skirmish map
## keeps the best score reached on it (waves cleared plus the win bonus, times the difficulty's
## multiplier), and a run pays only the part of its score above that record. So a stage is worth
## a fixed amount on each difficulty however often it is played. A won replay that sets no record
## pays REPLAY_WIN_POINTS, at most REPLAY_LIMIT times per stage or map.
const REPLAY_WIN_POINTS := 1
const REPLAY_LIMIT := 3

## TESTING SWITCH: while true, every campaign stage (all six lands, the Convergence and the final
## assault on the citadel) can be played from the world map in any order. Set it to false before
## release to bring back the normal order (each land opens after the one before, each stage after
## the stage before it).
const UNLOCK_ALL_STAGES := true

## Starts as UNLOCK_ALL_STAGES. Tests that check the normal opening order set it to false.
var unlock_all_stages := UNLOCK_ALL_STAGES

## A DataRegistry, or a node with the same fields in tests.
var registry: Node
var profile: PlayerProfile
var tree: TreeState
var selected_map: StringName = &""
var selected_difficulty: StringName = &""
## True when the next skirmish is endless.
var endless := false
## What the last recorded run paid for, for the end screen: a new record, a replay reward, or
## nothing new.
var last_run_note := ""


func _init(p_registry: Node, p_profile: PlayerProfile) -> void:
	registry = p_registry
	profile = p_profile
	if profile.needs_records:
		_rebuild_records()
	tree = TreeState.new(TreeGraph.new(registry.meta_tree_nodes), profile.meta_points_earned)
	tree.restore(profile.meta_nodes)
	selected_map = profile.last_map
	selected_difficulty = profile.last_difficulty
	endless = profile.last_endless
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


## Makes the next skirmish endless, or a normal run of the map's waves.
func set_endless(on: bool) -> void:
	endless = on
	_sync_profile()


## Most waves cleared in an endless skirmish on a map, or 0.
func endless_best(map_id: StringName) -> int:
	return profile.endless_best.get(map_id, 0)


# --- Runs ------------------------------------------------------------------------

## Everything the next run needs: the chosen map and difficulty, the meta tree's bonuses, and the
## in-run nodes that are still locked.
func run_config() -> RunConfig:
	var config := RunConfig.from_registry(registry, selected_map)
	config.run_modifiers = tree.modifiers()
	config.run_modifiers.append_array(campaign_rewards())
	config.locked_tree_nodes = locked_in_run_nodes()
	config.difficulty = registry.difficulties.get(selected_difficulty)
	config.endless = endless
	return config


## A finished run's score: a point per wave cleared, plus a bonus for winning, times the
## difficulty's multiplier. A run pays meta points only for beating the record on its stage or map.
static func run_score(sim: RunSim) -> int:
	var won := sim.state == RunSim.State.WON
	var multiplier := sim.config.difficulty.meta_point_multiplier if sim.config.difficulty != null else 1.0
	return roundi(sim.config.rules.meta_points_after_run(sim.wave_index, won) * multiplier)


## The key a run's record is kept under: the campaign stage, or the skirmish map (endless runs keep
## their own records, "endless:<map id>").
static func record_key(sim: RunSim) -> StringName:
	if sim.config.stage != null:
		return sim.config.stage.id
	var mode := "endless" if sim.is_endless() else "skirmish"
	return StringName("%s:%s" % [mode, sim.config.map.id if sim.config.map != null else &""])


## Meta points a finished run would pay, without recording it.
func meta_points_for(sim: RunSim) -> int:
	var key := record_key(sim)
	var best: int = profile.run_records.get(key, 0)
	var score := run_score(sim)
	if score > best:
		return score - best
	if sim.state == RunSim.State.WON and profile.replays_paid.get(key, 0) < REPLAY_LIMIT:
		return REPLAY_WIN_POINTS
	return 0


## Pays a finished run's meta points and updates the records. Returns the points earned.
func record_run(sim: RunSim) -> int:
	var key := record_key(sim)
	var best: int = profile.run_records.get(key, 0)
	var score := run_score(sim)
	var earned := meta_points_for(sim)
	if score > best:
		profile.run_records[key] = score
		last_run_note = "New record here: %d, up from %d." % [score, best] if best > 0 else ""
	elif earned > 0:
		profile.replays_paid[key] = profile.replays_paid.get(key, 0) + 1
		var left: int = REPLAY_LIMIT - profile.replays_paid[key]
		if left > 0:
			last_run_note = "No new record, so a small replay reward (%d more here)." % left
		else:
			last_run_note = "No new record, so a small replay reward, the last one here. Only a new record or a harder level pays from now on."
	else:
		last_run_note = "No new record (best %d). Clear more waves, win, or play a harder level to earn more here." % best
	profile.meta_points_earned += earned
	tree.points += earned
	profile.runs_played += 1
	if sim.state == RunSim.State.WON:
		profile.runs_won += 1
	profile.best_waves = maxi(profile.best_waves, sim.wave_index)
	if sim.is_endless() and sim.config.map != null:
		profile.endless_best[sim.config.map.id] = maxi(endless_best(sim.config.map.id), sim.wave_index)
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
	if unlock_all_stages:
		return true
	return campaign.requires_campaigns.all(func(id: StringName) -> bool: return is_campaign_complete(id))


## A stage opens once its campaign is open and the stage before it has been won.
func is_stage_unlocked(stage_id: StringName) -> bool:
	var campaign: CampaignData = registry.campaign_of(stage_id)
	if campaign == null or not is_campaign_unlocked(campaign.id):
		return false
	if unlock_all_stages:
		return true
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
	result["first_win"] = earned > 0 and before == 0
	result["best"] = stars(stage.id)
	var joined: Array[HeroData] = []
	if earned > 0 and before == 0:
		for hero in heroes_in_order():
			if hero.joins_after == stage.id or hero.arrives_in == stage.id:
				joined.append(hero)
	result["heroes_joined"] = joined
	if sim.config.campaign != null and not campaign_was_done:
		result["campaign_complete"] = is_campaign_complete(sim.config.campaign.id)
	return result


# --- Story ---------------------------------------------------------------------------

## Campaign stages won so far, in any order. The story moves on with this count.
func stages_won() -> int:
	var count := 0
	for id in profile.stage_stars:
		if profile.stage_stars[id] > 0:
			count += 1
	return count


func has_seen(cinematic_id: StringName) -> bool:
	return profile.seen_cinematics.has(cinematic_id)


## Remembers that a cinematic was played, so it does not play on its own again. Returns true if it
## was new.
func mark_seen(cinematic_id: StringName) -> bool:
	if cinematic_id.is_empty() or profile.seen_cinematics.has(cinematic_id):
		return false
	profile.seen_cinematics.append(cinematic_id)
	return true


## Cinematics that should play now that this stage was won, oldest first.
func story_after_stage(story: Story, stage_id: StringName) -> Array[StringName]:
	return story.due_after_win(stage_id, stages_won(), profile.seen_cinematics)


## Cinematics that should play before a stage starts: the prologue before the very first stage,
## and any written for that stage.
func story_before_stage(story: Story, stage_id: StringName) -> Array[StringName]:
	var result: Array[StringName] = []
	if not story.prologue.is_empty() and story.has_cinematic(story.prologue) and not has_seen(story.prologue):
		result.append(story.prologue)
	for id in story.due_before_stage(stage_id, profile.seen_cinematics):
		if not result.has(id):
			result.append(id)
	return result


# --- Heroes ----------------------------------------------------------------------

func heroes_in_order() -> Array[HeroData]:
	var result: Array[HeroData] = []
	result.assign(registry.heroes.values())
	result.sort_custom(func(a: HeroData, b: HeroData) -> bool: return a.order < b.order)
	return result


## True once a hero has joined: from the start, or by winning the stage that brings them.
func is_hero_joined(hero_id: StringName) -> bool:
	var hero: HeroData = registry.heroes.get(hero_id)
	if hero == null:
		return false
	if hero.joins_after.is_empty() and hero.arrives_in.is_empty():
		return true
	for stage_id in [hero.joins_after, hero.arrives_in]:
		if not stage_id.is_empty() and stars(stage_id) > 0:
			return true
	return false


func joined_heroes() -> Array[HeroData]:
	var result: Array[HeroData] = []
	for hero in heroes_in_order():
		if is_hero_joined(hero.id):
			result.append(hero)
	return result


## The heroes the next run brings: the ones picked, or if none are, the most recent to join.
func party() -> Array[HeroData]:
	var result: Array[HeroData] = []
	for id in profile.hero_party:
		var hero: HeroData = registry.heroes.get(id)
		if hero != null and is_hero_joined(id) and result.size() < HeroData.MAX_PARTY:
			result.append(hero)
	if result.is_empty():
		var joined := joined_heroes()
		joined.reverse()
		for hero in joined:
			if result.size() >= HeroData.MAX_PARTY:
				break
			result.append(hero)
		result.sort_custom(func(a: HeroData, b: HeroData) -> bool: return a.order < b.order)
	return result


## Adds a joined hero to the party, or takes them out. A full party drops its first hero to make
## room. Returns false for a hero who has not joined.
func toggle_party_hero(hero_id: StringName) -> bool:
	if not is_hero_joined(hero_id):
		return false
	var ids: Array[StringName] = []
	for hero in party():
		ids.append(hero.id)
	if ids.has(hero_id):
		ids.erase(hero_id)
	else:
		if ids.size() >= HeroData.MAX_PARTY:
			ids.remove_at(0)
		ids.append(hero_id)
	profile.hero_party = ids
	return true


## Adds the party, and any hero who arrives during the stage, to a run's config.
func add_heroes(config: RunConfig) -> RunConfig:
	if config == null:
		return null
	config.heroes = party()
	if config.stage != null:
		for hero in heroes_in_order():
			if hero.arrives_in == config.stage.id and not config.heroes.has(hero):
				config.arriving_heroes.append(hero)
	return config


# --- Internals -------------------------------------------------------------------

## For saves from before records: every stage won counts as won on Normal, every skirmish map as
## played to the best wave count, and the meta points are capped at what that progress is worth
## now. Points farmed by replaying under the old rules go; the nodes they bought are refunded.
func _rebuild_records() -> void:
	profile.needs_records = false
	var rules: RunRules = registry.run_rules
	var worth := 0
	for stage: StageData in registry.stages.values():
		if profile.stage_stars.get(stage.id, 0) <= 0:
			continue
		var wave_set := stage.wave_set
		if wave_set.is_empty() and registry.maps.has(stage.map):
			wave_set = registry.maps[stage.map].wave_set
		var waves := _wave_count(wave_set)
		var score := rules.meta_points_after_run(waves, true) if rules != null else 0
		profile.run_records[stage.id] = maxi(profile.run_records.get(stage.id, 0), score)
		worth += profile.run_records[stage.id] + stage.first_clear_points
	if profile.best_waves > 0:
		for map in maps_in_order():
			var waves := mini(profile.best_waves, _wave_count(map.wave_set))
			var won := profile.runs_won > 0 and waves >= _wave_count(map.wave_set)
			var key := StringName("skirmish:%s" % map.id)
			var score := rules.meta_points_after_run(waves, won) if rules != null else 0
			profile.run_records[key] = maxi(profile.run_records.get(key, 0), score)
			worth += profile.run_records[key]
	profile.meta_points_earned = mini(profile.meta_points_earned, worth)


func _wave_count(wave_set_id: StringName) -> int:
	var wave_set: WaveSet = registry.wave_sets.get(wave_set_id)
	return wave_set.waves.size() if wave_set != null else 0

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
	profile.last_endless = endless


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
