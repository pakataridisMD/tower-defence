extends SceneTree
func _initialize() -> void:
	var registry: Node = load("res://scripts/core/data_registry.gd").new()
	registry.reload()
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	for arg in OS.get_cmdline_user_args():
		var parts := arg.split(":")
		var config := meta.stage_config(StringName(parts[0]))
		config.wave_set.health_scale = float(parts[1])
		var sim := RunSim.new(config)
		var bot := AutoPlayer.for_sim(sim)
		var leaks := {}
		sim.enemy_leaked.connect(func(e: SimEnemy) -> void:
			var k := "w%d %s" % [sim.wave_number(), e.data.id]
			leaks[k] = leaks.get(k, 0) + 1)
		var t := 0.0
		while not sim.is_over() and t < 8000.0:
			bot.act()
			sim.step(RunSim.STEP)
			t += RunSim.STEP
		print(parts[0], " ", RunSim.State.keys()[sim.state], " wave ", sim.wave_index, " lives ", sim.lives, " towers ", sim.towers.size(), " ", leaks)
	registry.free()
	quit()
