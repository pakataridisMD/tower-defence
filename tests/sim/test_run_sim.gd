extends GutTest
## Run rules, driven through RunSim with the real data files.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"switchback"
## A buildable cell next to the first stretch of path.
const CELL := Vector2i(2, 3)

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _sim(run_modifiers: Array[Modifier] = []) -> RunSim:
	var config := RunConfig.from_registry(registry, MAP)
	config.run_modifiers = run_modifiers
	return RunSim.new(config)


func _run_until_building(sim: RunSim, max_seconds: float = 300.0) -> void:
	var elapsed := 0.0
	while sim.state == RunSim.State.WAVE and elapsed < max_seconds:
		sim.step(0.05)
		elapsed += 0.05


func test_run_starts_with_the_rules_values() -> void:
	var sim := _sim()
	assert_eq(sim.gold, 150)
	assert_eq(sim.lives, 20)
	assert_eq(sim.tree.points, 1)
	assert_eq(sim.total_waves(), 10)
	assert_eq(sim.wave_number(), 1)


func test_run_modifiers_change_starting_values() -> void:
	var sim := _sim([
		Modifier.create(&"starting_gold", Modifier.Kind.FLAT, 50.0),
		Modifier.create(&"starting_tree_points", Modifier.Kind.FLAT, 1.0),
	])
	assert_eq(sim.gold, 200)
	assert_eq(sim.tree.points, 2)


func test_towers_unlock_through_the_web() -> void:
	var sim := _sim()
	assert_false(sim.is_unlocked(&"fire_brazier"))
	assert_string_contains(sim.placement_error(&"fire_brazier", CELL), "Unlock")
	assert_true(sim.allocate_node(&"fire_entry"))
	assert_true(sim.is_unlocked(&"fire_brazier"))
	assert_true(sim.can_place(&"fire_brazier", CELL))


func test_cannot_build_on_the_path_outside_the_map_or_twice() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	assert_string_contains(sim.placement_error(&"fire_brazier", Vector2i(0, 2)), "path")
	assert_string_contains(sim.placement_error(&"fire_brazier", Vector2i(30, 3)), "Outside")
	assert_not_null(sim.place_tower(&"fire_brazier", CELL))
	assert_string_contains(sim.placement_error(&"fire_brazier", CELL), "already")


func test_building_costs_gold_and_selling_refunds_most_of_it() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_eq(sim.gold, 100)
	assert_eq(sim.sell_tower(tower), 35)
	assert_eq(sim.gold, 135)
	assert_null(sim.tower_at(CELL))


func test_not_enough_gold() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	for x in 3:
		sim.place_tower(&"fire_brazier", Vector2i(x, 0))
	assert_eq(sim.gold, 0)
	assert_string_contains(sim.placement_error(&"fire_brazier", CELL), "gold")


func test_a_cleared_wave_pays_points_and_gold() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var bot := AutoPlayer.new(sim)
	bot.build_towers()
	var gold_before := sim.gold
	assert_true(sim.start_next_wave())
	assert_eq(sim.state, RunSim.State.WAVE)
	_run_until_building(sim)
	assert_eq(sim.state, RunSim.State.BUILDING)
	assert_eq(sim.wave_index, 1)
	assert_eq(sim.kills + sim.leaks, 10, "all 10 grunts were killed or leaked")
	assert_eq(sim.tree.points, 1, "one point per wave")
	assert_true(sim.gold >= gold_before + 20, "wave bonus plus bounties")


func test_leaks_cost_lives_and_can_end_the_run() -> void:
	var sim := _sim([Modifier.create(&"starting_lives", Modifier.Kind.FLAT, -18.0)])
	watch_signals(sim)
	sim.start_next_wave()
	_run_until_building(sim)
	assert_eq(sim.state, RunSim.State.LOST)
	assert_eq(sim.lives, 0)
	assert_signal_emitted_with_parameters(sim, "run_ended", [false])


func test_refunds_only_until_the_next_wave_starts() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	assert_true(sim.can_refund_node(&"fire_entry"))
	sim.start_next_wave()
	assert_false(sim.can_refund_node(&"fire_entry"))


func test_tree_bonuses_apply_to_towers_already_built() -> void:
	var sim := _sim()
	sim.tree.points = 5
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_eq(tower.damage, 8.0)
	sim.allocate_node(&"fire_core")
	assert_almost_eq(tower.damage, 9.2, 0.0001)


func test_keystone_raises_tower_prices() -> void:
	var sim := _sim()
	sim.tree.points = 10
	for id: StringName in [&"storm_entry", &"storm_core", &"storm_notable", &"keystone_overcharge"]:
		assert_true(sim.allocate_node(id), "took %s" % id)
	assert_eq(sim.tower_price(&"fire_brazier"), 63)


func test_locked_nodes_cannot_be_taken() -> void:
	var config := RunConfig.from_registry(registry, MAP)
	config.locked_tree_nodes = [&"fire_entry"]
	var sim := RunSim.new(config)
	assert_false(sim.allocate_node(&"fire_entry"))
	assert_true(sim.allocate_node(&"storm_entry"))


func test_chain_towers_hit_several_enemies() -> void:
	var sim := _sim()
	sim.tree.points = 5
	sim.allocate_node(&"storm_entry")
	var tower := sim.place_tower(&"storm_spire", CELL)
	watch_signals(sim)
	sim.start_next_wave()
	_run_until_building(sim)
	assert_signal_emitted(sim, "chain_fired")
	var points: PackedVector2Array = get_signal_parameters(sim, "chain_fired")[1]
	assert_true(points.size() >= 2, "the tower and at least one enemy")
	assert_true(tower.damage_dealt > 0.0)


func test_towers_turn_to_face_what_they_attack() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_almost_eq(tower.facing, PI / 2.0, 0.001, "new towers face down")
	sim.start_next_wave()
	var elapsed := 0.0
	while tower.damage_dealt == 0.0 and sim.projectiles.is_empty() and elapsed < 60.0:
		sim.step(0.05)
		elapsed += 0.05
	assert_false(sim.projectiles.is_empty() and tower.damage_dealt == 0.0, "the tower attacked")
	var shot: SimProjectile = sim.projectiles[0] if not sim.projectiles.is_empty() else null
	if shot != null:
		var expected := (shot.target_point - tower.position).angle()
		assert_almost_eq(angle_difference(tower.facing, expected), 0.0, 0.05)


func test_meta_bonuses_raise_wave_gold_and_sell_refunds() -> void:
	var rules: RunRules = registry.run_rules
	var sim := _sim([
		Modifier.create(&"gold_per_wave", Modifier.Kind.FLAT, 10.0),
		Modifier.create(&"sell_refund", Modifier.Kind.FLAT, 0.15),
	])
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_eq(sim.sell_value(tower), floori(tower.price_paid * (rules.sell_refund + 0.15)))
	watch_signals(sim)
	AutoPlayer.new(sim).build_towers()
	sim.start_next_wave()
	_run_until_building(sim)
	assert_signal_emitted_with_parameters(sim, "wave_cleared", [1, 1, rules.gold_per_wave + 10])


func test_sell_refunds_never_pay_more_than_the_price() -> void:
	var sim := _sim([Modifier.create(&"sell_refund", Modifier.Kind.FLAT, 5.0)])
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_eq(sim.sell_value(tower), tower.price_paid)


func test_harder_difficulty_levels_give_enemies_more_health() -> void:
	var normal := _first_enemy_health(null)
	var hard := DifficultyData.new()
	hard.enemy_health_multiplier = 1.4
	assert_almost_eq(_first_enemy_health(hard), normal * 1.4, 0.001)


func _first_enemy_health(difficulty: DifficultyData) -> float:
	var config := RunConfig.from_registry(registry, MAP)
	config.difficulty = difficulty
	var sim := RunSim.new(config)
	sim.start_next_wave()
	for i in 600:
		if not sim.enemies.is_empty():
			break
		sim.step(RunSim.STEP)
	assert_false(sim.enemies.is_empty(), "the first enemy spawned")
	return sim.enemies[0].max_health if not sim.enemies.is_empty() else 0.0
