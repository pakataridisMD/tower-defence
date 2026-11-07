extends GutTest
## Pacing numbers from the design doc: about 18 tree points by wave 30.


func test_one_point_every_other_wave_plus_one_per_boss() -> void:
	var rules := RunRules.new()
	var total := 0
	for wave in range(1, 31):
		total += rules.tree_points_after_wave(wave, wave % 10 == 0)
	assert_eq(total, 18)


func test_wave_health_grows_from_wave_two() -> void:
	var waves := WaveSet.new()
	waves.health_growth = 1.1
	assert_eq(waves.health_multiplier(1), 1.0)
	assert_almost_eq(waves.health_multiplier(3), 1.21, 0.0001)


func test_tower_stats_use_its_tags() -> void:
	var tower := TowerData.new()
	tower.elements = [&"fire", &"storm"]
	tower.damage = 10.0
	var mods: Array[Modifier] = [
		Modifier.create(&"damage", Modifier.Kind.INCREASED, 0.5, [&"fire"]),
		Modifier.create(&"damage", Modifier.Kind.MORE, 1.0, [&"hybrid"]),
		Modifier.create(&"damage", Modifier.Kind.FLAT, 100.0, [&"nature"]),
	]
	# (10) * (1 + 0.5) * (1 + 1.0); the nature bonus does not apply.
	assert_eq(tower.stat_with(&"damage", mods), 30.0)


func test_unknown_stats_start_at_zero() -> void:
	var tower := TowerData.new()
	assert_eq(tower.base_stat(&"burn_spread_radius"), 0.0)
	assert_eq(tower.base_stat(&"damage"), tower.damage)
