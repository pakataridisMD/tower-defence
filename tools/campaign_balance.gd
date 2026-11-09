extends SceneTree
## Plays every campaign stage with the scripted AutoPlayer and prints how each went, for tuning the
## campaign (see tools/campaign/gen_campaign.py). No meta tree bonuses, Normal difficulty.
##
##   godot --headless -s tools/campaign_balance.gd [-- --stage=<id>] [--tune]
##
## --tune searches each stage's health scale so the bot (which never levels its towers, so it plays
## worse than a person) wins keeping a target share of its lives, and prints lines for
## tools/campaign/tuning.py.

## Share of lives the bot should keep, by stage position in an element campaign and in the Convergence.
const TARGETS: Array[float] = [0.7, 0.55, 0.4, 0.25]
const CONVERGE_TARGETS: Array[float] = [0.45, 0.35, 0.25]


func _initialize() -> void:
	var registry: Node = load("res://scripts/core/data_registry.gd").new()
	registry.reload()
	for line: String in registry.validate():
		print("DATA ERROR: ", line)
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--stage="):
			only = arg.trim_prefix("--stage=")
	var tune := OS.get_cmdline_user_args().has("--tune")
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	for campaign in meta.campaigns_in_order():
		for i in campaign.stages.size():
			var stage := campaign.stages[i]
			if not only.is_empty() and stage.id != only:
				continue
			if tune:
				var targets := TARGETS if not campaign.element.is_empty() else CONVERGE_TARGETS
				_tune(meta, stage, targets[mini(i, targets.size() - 1)])
				continue
			var started := Time.get_ticks_msec()
			var sim := _play(meta, stage)
			print("%-11s %-26s %s wave %2d/%2d  lives %3d/%3d  stars %d  towers %2d  gold %5d  (%d ms)" % [
				stage.id, stage.display_name, "WON " if sim.state == RunSim.State.WON else "LOST",
				sim.wave_index, sim.total_waves(), sim.lives, sim.starting_lives, MetaProgress.stars_for(sim),
				sim.towers.size(), sim.gold, Time.get_ticks_msec() - started])
	registry.free()
	quit()


func _play(meta: MetaProgress, stage: StageData) -> RunSim:
	var sim := RunSim.new(meta.stage_config(stage.id))
	var bot := AutoPlayer.for_sim(sim)
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 4000.0:
		bot.play_build_phase()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	return sim


## Bisects the stage's health scale: the highest scale at which the bot still wins with `target` of
## its lives left.
##
## Two passes: first the ordinary waves (with the boss waves made harmless) for the target plus a
## tenth, then the boss waves' own health multiplier, where the bot only needs to keep half the target.
func _tune(meta: MetaProgress, stage: StageData, target: float) -> void:
	var waves := meta.stage_config(stage.id).wave_set
	var bosses: Array[WaveData] = []
	for wave in waves.waves:
		if wave.is_boss:
			bosses.append(wave)
	var set_boss := func(value: float) -> void:
		for wave in bosses:
			wave.health_multiplier = value
	set_boss.call(0.02)
	var health := _bisect(meta, stage, target + (0.1 if not bosses.is_empty() else 0.0), 0.3, 2.5,
			func(value: float) -> void: waves.health_scale = value)
	waves.health_scale = health
	var boss := 0.0
	# If even a weak boss beats the bot, the waves before it are too strong for it to build up:
	# soften them and try again.
	for attempt in 6:
		if bosses.is_empty():
			break
		boss = _bisect(meta, stage, target * 0.5, 0.1, 4.0, set_boss)
		if boss > 0.2:
			break
		health = snappedf(health * 0.8, 0.01)
		waves.health_scale = health
	var line := 'TUNING["%s"] = {"health": %.2f' % [stage.id, health]
	if not bosses.is_empty():
		line += ', "boss": %.2f' % boss
	print(line + "}")


## The highest value in [low, high] at which the bot still wins keeping `target` of its lives.
func _bisect(meta: MetaProgress, stage: StageData, target: float, low: float, high: float, apply: Callable) -> float:
	for step in 8:
		var mid := (low + high) * 0.5
		apply.call(mid)
		var sim := _play(meta, stage)
		if sim.state == RunSim.State.WON and sim.lives >= ceili(sim.starting_lives * target):
			low = mid
		else:
			high = mid
	apply.call(low)
	return snappedf(low, 0.01)
