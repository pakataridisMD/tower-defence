extends GutTest
## Plays whole runs with the scripted AutoPlayer. These guard the prototype's balance:
## a sensible strategy should win, and doing nothing should lose.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const STEP := RunSim.STEP
## Generous cap so a stuck run fails instead of hanging the test suite.
const MAX_SIM_SECONDS := 3600.0

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _play(bot_nodes: Array[StringName], bot_towers: Array[StringName]) -> RunSim:
	var sim := RunSim.new(RunConfig.from_registry(registry, &"switchback"))
	var bot := AutoPlayer.new(sim, bot_nodes, bot_towers)
	var elapsed := 0.0
	while not sim.is_over() and elapsed < MAX_SIM_SECONDS:
		bot.act()
		sim.step(STEP)
		elapsed += STEP
	gut.p("Run ended %s after %d waves: %d lives, %d kills, %d leaks, %d towers, %d gold left" % [
		RunSim.State.keys()[sim.state], sim.wave_index, sim.lives, sim.kills, sim.leaks,
		sim.towers.size(), sim.gold])
	return sim


func test_a_sensible_strategy_wins() -> void:
	var sim := _play(AutoPlayer.DEFAULT_NODES, AutoPlayer.DEFAULT_TOWERS)
	assert_eq(sim.state, RunSim.State.WON)


func test_doing_nothing_loses() -> void:
	var sim := _play([], [])
	assert_eq(sim.state, RunSim.State.LOST)
	assert_true(sim.wave_index < sim.total_waves())


## The new elements must be able to carry a run on their own, without Fire, Storm or Nature.
func test_a_water_earth_void_strategy_wins() -> void:
	var nodes: Array[StringName] = [
		&"earth_entry", &"water_entry", &"earth_ccw", &"water_cw", &"bridge_quagmire",
		&"earth_core", &"earth_notable", &"void_entry", &"earth_cw", &"void_ccw", &"bridge_gravity_well",
		&"water_core", &"water_notable", &"void_core", &"void_notable", &"void_cw", &"water_ccw",
	]
	var towers: Array[StringName] = [
		&"hybrid_gravity_well", &"hybrid_quagmire", &"earth_monolith", &"void_obelisk", &"water_wellspring",
	]
	var sim := _play(nodes, towers)
	assert_eq(sim.state, RunSim.State.WON)
