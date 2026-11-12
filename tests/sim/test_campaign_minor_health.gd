extends GutTest
## In the campaign, minor enemies have half their health; bosses and skirmish enemies keep all of it.

const TEST_ROAD := preload("res://tests/support/test_road.tres")
const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	registry.maps[&"test_road"] = TEST_ROAD


func _spawn(enemy_id: StringName, campaign: bool) -> SimEnemy:
	var config := RunConfig.from_registry(registry, &"test_road")
	if campaign:
		config.stage = StageData.new()
	var group := SpawnGroup.new()
	group.enemy = enemy_id
	group.count = 1
	var wave := WaveData.new()
	wave.groups = [group] as Array[SpawnGroup]
	var waves := WaveSet.new()
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	config.wave_set = waves
	var sim := RunSim.new(config)
	sim.start_next_wave()
	for i in 30:
		sim._spawn(RunSim.STEP)
	return sim.enemies[0]


func test_a_minor_enemy_has_half_health_in_the_campaign() -> void:
	var full: float = registry.enemies[&"grunt"].max_health
	assert_almost_eq(_spawn(&"grunt", true).max_health, full * 0.5, 0.01)
	assert_almost_eq(_spawn(&"grunt", true).health, full * 0.5, 0.01)


func test_a_minor_enemy_keeps_full_health_in_a_skirmish() -> void:
	var full: float = registry.enemies[&"grunt"].max_health
	assert_almost_eq(_spawn(&"grunt", false).max_health, full, 0.01)


func test_a_boss_keeps_full_health_in_the_campaign() -> void:
	var full: float = registry.enemies[&"saltmother"].max_health
	assert_almost_eq(_spawn(&"saltmother", true).max_health, full, 0.01)
