extends SceneTree
## Measures one simulation step on a crowded board: 40 towers and up to 500 enemies on the path
## at once. At 60 fps and 3x speed the game runs three steps per frame, so a step should stay
## well under 2 ms to leave most of each frame for drawing.
##
## Run it with: godot --headless --path . -s tools/benchmark_sim.gd

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const TOWER_COUNT := 40
const ENEMY_COUNT := 500
const SPAWN_INTERVAL := 0.03
const SIM_SECONDS := 25.0
const CROWDED := 400
const TOWERS: Array[StringName] = [
	&"hybrid_plasma", &"fire_brazier", &"storm_spire", &"hybrid_thornstorm", &"nature_thornbush",
]


func _init() -> void:
	var registry: Node = DataRegistryScript.new()
	registry.reload()
	var sim := RunSim.new(_crowded_config(registry))
	registry.free()
	sim.gold = 1_000_000
	sim.tree.points = 100
	for id in AutoPlayer.DEFAULT_NODES:
		sim.allocate_node(id)
	sim.allocate_node(&"keystone_overcharge")
	var bot := AutoPlayer.new(sim)
	for i in TOWER_COUNT:
		var tower_id := TOWERS[i % TOWERS.size()]
		var cell := bot.best_cell(tower_id)
		if cell.x >= 0:
			sim.place_tower(tower_id, cell)
	sim.start_next_wave()

	var crowded_steps := 0
	var crowded_usec := 0
	var slowest_usec := 0
	var peak_enemies := 0
	var peak_projectiles := 0
	var steps := roundi(SIM_SECONDS / RunSim.STEP)
	var started := Time.get_ticks_usec()
	for i in steps:
		var before := Time.get_ticks_usec()
		sim.step(RunSim.STEP)
		var took := Time.get_ticks_usec() - before
		peak_enemies = maxi(peak_enemies, sim.enemies.size())
		peak_projectiles = maxi(peak_projectiles, sim.projectiles.size())
		if sim.enemies.size() >= CROWDED:
			crowded_steps += 1
			crowded_usec += took
			slowest_usec = maxi(slowest_usec, took)
	var total_ms := (Time.get_ticks_usec() - started) / 1000.0

	print("Benchmark: %d towers, peak %d enemies, peak %d projectiles, %d kills" % [
		sim.towers.size(), peak_enemies, peak_projectiles, sim.kills])
	print("%d steps (%.0f s of game time) took %.0f ms, %.3f ms per step on average" % [
		steps, SIM_SECONDS, total_ms, total_ms / steps])
	if crowded_steps > 0:
		var average := crowded_usec / 1000.0 / crowded_steps
		print("With %d+ enemies alive: %d steps, %.3f ms average, %.3f ms slowest" % [
			CROWDED, crowded_steps, average, slowest_usec / 1000.0])
		print("At 3x speed that is %.2f ms of a 16.7 ms frame" % (average * 3.0))
	else:
		print("The board never held %d enemies at once" % CROWDED)
	quit()


## One long wave of slow, tough enemies, so the path fills up and stays full.
func _crowded_config(registry: Node) -> RunConfig:
	var config := RunConfig.from_registry(registry, &"switchback")
	var enemy: EnemyData = (config.enemies[&"grunt"] as EnemyData).duplicate()
	enemy.id = &"benchmark_grunt"
	enemy.max_health = 5000.0
	enemy.speed = 60.0
	config.enemies = config.enemies.duplicate()
	config.enemies[enemy.id] = enemy
	var group := SpawnGroup.new()
	group.enemy = enemy.id
	group.count = ENEMY_COUNT
	group.spawn_interval = SPAWN_INTERVAL
	var wave := WaveData.new()
	wave.element = &"water"
	wave.groups.append(group)
	var wave_set := WaveSet.new()
	wave_set.id = &"benchmark"
	wave_set.waves.append(wave)
	config.wave_set = wave_set
	return config
