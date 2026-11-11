extends SceneTree
## Plays the campaign in order with the scripted AutoPlayer, the way a new player would, and spends
## the meta points it earns on the meta tree after every stage. Prints how much of the tree is
## filled after each stage, to check that the tree keeps growing across the whole campaign instead
## of filling up in the first land (see tools/meta/gen_meta_tree.py).
##
##   godot --headless -s tools/meta_pacing.gd [-- --tries=<n>] [--quick] [--no-spend]
##
## A lost stage is played again, up to --tries times (default 2), and every attempt pays its meta
## points like a real run. --quick plays only the first stage of each land. The bot spends points on
## the cheapest open node, preferring the land it is about to play, and skips nodes with a
## downside (the player picks those on purpose). --no-spend keeps the points, to compare against a
## player who never opens the tree. The citadel assault is left out: it is its own mode.

const TRIES_DEFAULT := 2


func _initialize() -> void:
	var registry: Node = load("res://scripts/core/data_registry.gd").new()
	registry.reload()
	for line: String in registry.validate():
		print("DATA ERROR: ", line)
	var tries := TRIES_DEFAULT
	var quick := false
	var spend := not OS.get_cmdline_user_args().has("--no-spend")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--tries="):
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
			var focus := campaign.element
			var result := "LOST"
			var lives := ""
			var earned := 0
			var started := Time.get_ticks_msec()
			for attempt in tries:
				if spend:
					_spend(meta, focus)
				var sim := _play(meta, stage)
				earned += meta.record_run(sim)
				earned += int(meta.record_stage(sim).get("first_clear_points", 0))
				if sim.state == RunSim.State.WON:
					result = "WON " if attempt == 0 else "WON%d" % (attempt + 1)
					lives = "%3d/%3d" % [sim.lives, sim.starting_lives]
					break
				lives = "w%2d/%2d" % [sim.wave_index, sim.total_waves()]
			if spend:
				_spend(meta, focus)
			var spent := meta.profile.meta_points_earned - meta.points()
			print("PACING %2d %-11s %s %-8s +%3d  earned %4d  spent %4d  tree %3d%%  nodes %3d  (%d s)" % [
				stage_count, stage.id, result, lives, earned, meta.profile.meta_points_earned, spent,
				roundi(100.0 * spent / full), meta.tree.allocated_ids().size() - 1,
				(Time.get_ticks_msec() - started) / 1000])
	registry.free()
	quit()


func _play(meta: MetaProgress, stage: StageData) -> RunSim:
	var sim := RunSim.new(meta.stage_config(stage.id))
	var bot := AutoPlayer.for_sim(sim)
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 4000.0:
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	return sim


## Buys open nodes, cheapest first, the focus land's own nodes counting as half price, until no
## open node is affordable.
func _spend(meta: MetaProgress, focus: StringName) -> void:
	var graph := meta.tree.graph
	while true:
		var best: StringName = &""
		var best_score := INF
		for id in graph.ids():
			if not meta.tree.can_allocate(id) or _has_downside(graph.node(id)):
				continue
			var data := graph.node(id)
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
