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
	var config := meta.stage_config(stage_id)
	# --health=X and --boss=X try other numbers than tuning.py's without regenerating the data.
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--health="):
			config.wave_set = config.wave_set.duplicate()
			config.wave_set.health_scale = float(arg.trim_prefix("--health="))
		if arg.begins_with("--boss="):
			for wave in config.wave_set.waves:
				if wave.is_boss:
					wave.health_multiplier = float(arg.trim_prefix("--boss="))
		if arg.begins_with("--citadel="):
			config.enemies = config.enemies.duplicate()
			var citadel: EnemyData = config.enemies[&"nhal_vorath"].duplicate()
			citadel.max_health = float(arg.trim_prefix("--citadel="))
			config.enemies[&"nhal_vorath"] = citadel
		if arg.begins_with("--bolt="):
			config.enemies = config.enemies.duplicate()
			var spires: EnemyData = config.enemies[&"nhal_vorath"].duplicate()
			spires.bolt_damage = float(arg.trim_prefix("--bolt="))
			config.enemies[&"nhal_vorath"] = spires
	var sim := RunSim.new(config)
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
	sim.enemy_transformed.connect(func(e: SimEnemy, _from: EnemyData) -> void:
		print("%6.0f s  wave %2d  %s rises as %s" % [elapsed[0], sim.wave_number(), _from.display_name, e.data.display_name]))
	sim.boss_fled.connect(func(e: SimEnemy) -> void:
		print("%6.0f s  wave %2d  %s flees to the citadel (lives %d)" % [elapsed[0], sim.wave_number(), e.data.display_name, sim.lives]))
	sim.counter_attack_started.connect(func() -> void:
		print("%6.0f s  COUNTER-ATTACK, gold %d, lives %d" % [elapsed[0], sim.gold, sim.lives]))
	var mustered := {}
	sim.allies_mustered.connect(func(squad: Array[SimAlly]) -> void:
		var id: StringName = squad[0].data.id
		mustered[id] = mustered.get(id, 0) + 1)
	var lost := [0]
	sim.ally_died.connect(func(_a: SimAlly) -> void: lost[0] += 1)
	var next_report := [0.0]
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
		if sim.wave_number() == sim.config.stage.boss_wave and sim.state == RunSim.State.WAVE and elapsed[0] >= next_report[0]:
			next_report[0] = elapsed[0] + 10.0
			for e in sim.enemies:
				if e.data.tags.has(&"overlord"):
					var silenced := 0
					for t in sim.towers:
						if t.silenced > 0.0:
							silenced += 1
					print("%6.0f s  %s %d/%d hp, %d%% of the road, ward %.2f, %d towers silenced, %d enemies" % [elapsed[0], e.data.display_name, e.health, e.max_health, 100.0 * e.progress / sim.lane_lengths[e.lane], e.ward, silenced, sim.enemies.size()])
		if sim.counter_started and elapsed[0] >= next_report[0]:
			next_report[0] = elapsed[0] + 20.0
			var citadel := sim.structures[0]
			var front := 1.0e9
			for ally in sim.allies:
				front = minf(front, ally.progress)
			print("%6.0f s  army %d on the field (front %d px from the gate), %d fallen, enemies %d, gold %d, lives %d, citadel %d%%" % [
				elapsed[0], sim.allies.size(), front, lost[0], sim.enemies.size(), sim.gold, sim.lives, 100.0 * citadel.health / citadel.max_health])
	print("mustered: %s" % [mustered])
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
