extends SceneTree
## Plays the final assault with the bot and prints a timeline: when each building fell, the waves,
## lives and how long it took in game time. Usage: godot --headless -s tools/assault_sim.gd

func _initialize() -> void:
	var registry: Node = load("res://scripts/core/data_registry.gd").new()
	registry.reload()
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var stage_id := &"assault_1"
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--stage="):
			stage_id = StringName(arg.trim_prefix("--stage="))
	var sim := RunSim.new(meta.stage_config(stage_id))
	var bot := AutoPlayer.for_sim(sim)
	var elapsed := [0.0]
	sim.structure_destroyed.connect(func(s: SimEnemy) -> void:
		print("%6.0f s  wave %2d  %s falls (lives %d, towers %d)" % [elapsed[0], sim.wave_number(), s.data.display_name, sim.lives, sim.towers.size()]))
	sim.phase_changed.connect(func(p: int) -> void: print("%6.0f s  phase %d" % [elapsed[0], p]))
	sim.boss_arrived.connect(func(e: SimEnemy) -> void: print("%6.0f s  wave %2d  boss %s" % [elapsed[0], sim.wave_number(), e.data.display_name]))
	sim.wave_cleared.connect(func(n: int, _p: int, _g: int) -> void:
		var reach := 0
		var hp := ""
		for structure in sim.structures:
			if sim.is_vulnerable(structure):
				hp += " %s %d%%" % [structure.data.id, 100.0 * structure.health / structure.max_health]
				for tower in sim.towers:
					if tower.position.distance_to(structure.position) <= tower.attack_range:
						reach += 1
		print("%6.0f s  wave %2d cleared, lives %d, gold %d, towers %d (%d at the walls), phase %d%s" % [elapsed[0], n, sim.lives, sim.gold, sim.towers.size(), reach, sim.structure_phase, hp]))
	sim.enemy_leaked.connect(func(e: SimEnemy) -> void:
		if e.data.tags.has(&"boss"): print("        leaked boss %s" % e.data.display_name))
	var breaks := 0.0
	while not sim.is_over() and elapsed[0] < 5000.0:
		if sim.state == RunSim.State.BUILDING:
			bot.spend_points()
			bot.build_towers()
			# A person waits out the break before a wave that starts on its own.
			if sim.break_time_left >= 0.0:
				sim.tick_break(RunSim.STEP)
				breaks += RunSim.STEP
				elapsed[0] += RunSim.STEP
				continue
			sim.start_next_wave()
		bot.act()
		sim.step(RunSim.STEP)
		elapsed[0] += RunSim.STEP
	print("%s after %d waves, %.1f minutes (%.1f in breaks), lives %d of %d, towers %d" % [
		RunSim.State.keys()[sim.state], sim.wave_index, elapsed[0] / 60.0, breaks / 60.0, sim.lives, sim.starting_lives, sim.towers.size()])
	for structure in sim.structures:
		print("  %s: %d of %d health, phase %d" % [structure.data.display_name, structure.health, structure.max_health, structure.phase])
	var near := 0
	for tower in sim.towers:
		for structure in sim.structures:
			if structure.alive and tower.position.distance_to(structure.position) <= tower.attack_range:
				near += 1
	print("  towers in reach of a standing building: %d" % near)
	registry.free()
	quit()
