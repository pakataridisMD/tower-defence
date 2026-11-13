extends SceneTree
## Plays the campaign in order with the scripted AutoPlayer, the way a new player would, and spends
## the meta points it earns on the meta tree after every stage. Prints how much of the tree is
## filled after each stage, to check that the tree keeps growing across the whole campaign instead
## of filling up in the first land (see tools/meta/gen_meta_tree.py).
##
##   godot --headless -s tools/meta_pacing.gd [-- --tries=<n>] [--quick] [--no-spend] [--profiles=<path>]
##
## A lost stage is played again, up to --tries times (default 2), and every attempt pays its meta
## points like a real run. --quick plays only the first stage of each land. Before a stage the bot
## first buys its way to the Forge talents of the towers its plan for that stage builds (the trees
## are linked: no talent, no tower), then spends on the cheapest open node, preferring the element
## it is about to play, and skips nodes with a downside (the player picks those on purpose). --no-spend keeps the points, to compare against a
## player who never opens the tree. The citadel assault is left out: it is its own mode.
## --profiles writes the player's profile as it stands before each stage (meta tree, finished
## campaigns' sigils, heroes) to a JSON file, keyed by stage id, with the assault getting the profile
## after the last stage. tools/campaign_balance.gd tunes every stage against those profiles, and
## tools/campaign/meta_profiles.json is the copy it reads by default.

const TRIES_DEFAULT := 2


func _initialize() -> void:
	var registry: Node = load("res://scripts/core/data_registry.gd").new()
	registry.reload()
	for line: String in registry.validate():
		print("DATA ERROR: ", line)
	var tries := TRIES_DEFAULT
	var quick := false
	var spend := not OS.get_cmdline_user_args().has("--no-spend")
	var profiles_path := ""
	var profiles := {}
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--profiles="):
			profiles_path = arg.trim_prefix("--profiles=")
			if profiles_path.is_relative_path():
				profiles_path = "res://" + profiles_path
		elif arg.begins_with("--tries="):
			tries = maxi(1, int(arg.trim_prefix("--tries=")))
		elif arg == "--quick":
			quick = true
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var graph := meta.tree.graph
	var full := _most_a_player_can_take(graph)
	print("PACING tree: %d nodes, %d points to take everything a player can" % [graph.size() - 1, full])
	var stage_count := 0
	for campaign in meta.campaigns_in_order():
		if campaign.id == &"assault":
			continue
		for i in campaign.stages.size():
			if quick and i > 0:
				continue
			var stage := campaign.stages[i]
			stage_count += 1
			var wanted := _plan_towers(meta, stage)
			var focus := _focus(registry, wanted)
			var result := "LOST"
			var lives := ""
			var earned := 0
			var started := Time.get_ticks_msec()
			for attempt in tries:
				if spend:
					_spend(meta, focus, wanted)
				if attempt == 0:
					profiles[String(stage.id)] = meta.profile.to_dict()
				var sim := _play(meta, stage)
				earned += meta.record_run(sim)
				earned += int(meta.record_stage(sim).get("first_clear_points", 0))
				if sim.state == RunSim.State.WON:
					result = "WON " if attempt == 0 else "WON%d" % (attempt + 1)
					lives = "%3d/%3d" % [sim.lives, sim.starting_lives]
					break
				lives = "w%2d/%2d" % [sim.wave_index, sim.total_waves()]
			if spend:
				_spend(meta, focus, wanted)
			var spent := meta.profile.meta_points_earned - meta.points()
			print("PACING %2d %-11s %s %-8s +%3d  earned %4d  spent %4d  tree %3d%%  nodes %3d  (%d s)" % [
				stage_count, stage.id, result, lives, earned, meta.profile.meta_points_earned, spent,
				roundi(100.0 * spent / full), meta.tree.allocated_ids().size() - 1,
				(Time.get_ticks_msec() - started) / 1000])
	if not profiles_path.is_empty():
		profiles["assault_1"] = meta.profile.to_dict()
		var file := FileAccess.open(profiles_path, FileAccess.WRITE)
		file.store_string(JSON.stringify(profiles, "\t", true))
		file.close()
		print("PACING profiles for %d stages written to %s" % [profiles.size(), profiles_path])
	registry.free()
	quit()


func _play(meta: MetaProgress, stage: StageData) -> RunSim:
	# With the heroes who have joined, as in the game.
	var sim := RunSim.new(meta.add_heroes(meta.stage_config(stage.id)))
	var bot := AutoPlayer.for_sim(sim)
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 4000.0:
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	return sim


## The towers the bot's plan for this stage builds, best first.
func _plan_towers(meta: MetaProgress, stage: StageData) -> Array[StringName]:
	return AutoPlayer.for_sim(RunSim.new(meta.stage_config(stage.id))).tower_priority


## The element most of the plan's towers share: its talents count as half price.
func _focus(registry: Node, towers: Array[StringName]) -> StringName:
	var counts: Dictionary[StringName, int] = {}
	var best: StringName = &""
	for tower_id in towers:
		for element: StringName in registry.towers[tower_id].elements:
			counts[element] = counts.get(element, 0) + 1
			if best.is_empty() or counts[element] > counts[best]:
				best = element
	return best


## First walks toward the Forge talent of each wanted tower that is still locked, nearest first,
## saving up when the next step is too dear. Then buys open nodes, cheapest first, the focus
## element's own nodes counting as half price, until no open node is affordable.
func _spend(meta: MetaProgress, focus: StringName, wanted: Array[StringName]) -> void:
	var graph := meta.tree.graph
	while true:
		var target: StringName = &""
		var target_cost := 0
		for tower_id in wanted:
			if meta.is_tower_unlocked(tower_id):
				continue
			var talent := meta.unlocked_by(&"unlocks_towers", tower_id)
			var cost := meta.tree.path_cost(talent.id) if talent != null else -1
			if cost > 0 and (target.is_empty() or cost < target_cost):
				target = talent.id
				target_cost = cost
		if target.is_empty():
			break
		if not meta.allocate(meta.tree.path_to(target)[1]):
			return
	while true:
		var best: StringName = &""
		var best_score := INF
		for id in graph.ids():
			if not meta.tree.can_allocate(id) or _has_downside(graph.node(id)):
				continue
			var data := graph.node(id)
			if not data.unlocks_towers.is_empty():
				continue
			var score := float(data.cost) * (0.5 if data.region == focus and not focus.is_empty() else 1.0)
			if score < best_score or (score == best_score and String(id) < String(best)):
				best_score = score
				best = id
		if best.is_empty() or not meta.allocate(best):
			return


static func _has_downside(data: TreeNodeData) -> bool:
	for modifier in data.modifiers:
		var good_when_low := modifier.stat == &"cost" or modifier.stat == &"skill_cooldown" or modifier.stat == &"chain_falloff"
		if (modifier.value < 0.0) != good_when_low:
			return true
	return false


## Every node's cost, less the cheaper side of each pick-one choice.
static func _most_a_player_can_take(graph: TreeGraph) -> int:
	var total := 0
	for id in graph.ids():
		total += graph.node(id).cost
		for other in graph.exclusions(id):
			if String(other) > String(id):
				total -= mini(graph.node(id).cost, graph.node(other).cost)
	return total
