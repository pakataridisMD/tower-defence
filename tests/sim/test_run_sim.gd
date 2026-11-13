extends GutTest
## Run rules, driven through RunSim with the real data files.

const TEST_ROAD := preload("res://tests/support/test_road.tres")

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"test_road"
## A buildable cell next to the first stretch of path.
const CELL := Vector2i(3, 3)

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	# The small 24 x 15 road these tests were written against (the real maps are bigger and curved).
	registry.maps[&"test_road"] = TEST_ROAD


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
	assert_eq(sim.tree.points, registry.run_rules.starting_tree_points)
	assert_eq(sim.total_waves(), 10)
	assert_eq(sim.wave_number(), 1)


func test_run_modifiers_change_starting_values() -> void:
	var sim := _sim([
		Modifier.create(&"starting_gold", Modifier.Kind.FLAT, 50.0),
		Modifier.create(&"starting_tree_points", Modifier.Kind.FLAT, 1.0),
	])
	assert_eq(sim.gold, 200)
	assert_eq(sim.tree.points, registry.run_rules.starting_tree_points + 1)


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
		sim.place_tower(&"fire_brazier", Vector2i(x + 5, 0))
	assert_eq(sim.gold, 0)
	assert_string_contains(sim.placement_error(&"fire_brazier", CELL), "gold")


func test_a_cleared_wave_pays_points_and_gold() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var bot := AutoPlayer.new(sim)
	bot.build_towers()
	var gold_before := sim.gold
	var points_before := sim.tree.points
	var enemies := sim.current_wave().enemy_count()
	sim.lives = 999
	assert_true(sim.start_next_wave())
	assert_eq(sim.state, RunSim.State.WAVE)
	_run_until_building(sim)
	assert_eq(sim.state, RunSim.State.BUILDING)
	assert_eq(sim.wave_index, 1)
	assert_eq(sim.kills + sim.leaks, enemies, "every enemy of the wave was killed or leaked")
	assert_eq(sim.tree.points - points_before, registry.run_rules.tree_points_per_wave, "the points for one wave")
	assert_true(sim.gold >= gold_before + 20, "wave bonus plus bounties")


func test_next_wave_starts_on_its_own_after_the_break() -> void:
	var sim := _sim()
	sim.lives = 999
	assert_lt(sim.break_time_left, 0.0, "the first wave waits for the player")
	assert_false(sim.tick_break(60.0), "nothing counts down before the first wave")
	assert_eq(sim.state, RunSim.State.BUILDING)
	sim.start_next_wave()
	_run_until_building(sim)
	assert_eq(sim.state, RunSim.State.BUILDING)
	assert_eq(sim.break_time_left, RunSim.AUTO_WAVE_DELAY, "a 15 second break after a cleared wave")
	assert_false(sim.tick_break(RunSim.AUTO_WAVE_DELAY - 0.5))
	assert_eq(sim.state, RunSim.State.BUILDING, "still building with half a second left")
	assert_true(sim.tick_break(1.0), "the wave starts when the break runs out")
	assert_eq(sim.state, RunSim.State.WAVE)
	assert_eq(sim.wave_number(), 2)
	assert_lt(sim.break_time_left, 0.0)


func test_starting_the_wave_early_ends_the_countdown() -> void:
	var sim := _sim()
	sim.lives = 999
	sim.start_next_wave()
	_run_until_building(sim)
	sim.tick_break(3.0)
	assert_true(sim.start_next_wave())
	assert_lt(sim.break_time_left, 0.0)
	assert_false(sim.tick_break(60.0))


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
	sim.tree.points = 6
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_eq(tower.damage, 8.0)
	# Taking level III takes the way to it: a 4% pick, level II's 5%, an attack speed pick and its own 8%.
	sim.allocate_node(&"fire_core")
	assert_true(sim.tree.is_allocated(&"fire_core"))
	assert_almost_eq(tower.damage, 8.0 * 1.17, 0.0001)


func test_keystone_raises_tower_prices() -> void:
	var sim := _sim()
	sim.tree.points = 100
	for id: StringName in [&"storm_entry", &"storm_core", &"storm_notable", &"keystone_overcharge"]:
		assert_true(sim.allocate_node(id), "took %s" % id)
	assert_eq(sim.tower_price(&"fire_brazier"), 60, "20% more")


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
	assert_signal_emitted_with_parameters(sim, "wave_cleared", [1, rules.tree_points_per_wave, rules.gold_per_wave + 10 + sim.last_savings_bonus])


func test_kept_gold_earns_a_savings_bonus_at_the_end_of_a_wave() -> void:
	var rules: RunRules = registry.run_rules
	assert_eq(rules.savings_bonus, 0.2)
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	AutoPlayer.new(sim).build_towers()
	sim.gold = 300
	watch_signals(sim)
	sim.start_next_wave()
	# Whatever the wave pays in bounties, the bonus is 20% of what is held when it ends.
	var elapsed := 0.0
	while sim.state == RunSim.State.WAVE and elapsed < 300.0:
		elapsed += 0.05
		var expected := mini(floori(sim.gold * 0.2), rules.savings_cap_at(1))
		sim.step(0.05)
		if sim.state != RunSim.State.WAVE:
			assert_eq(sim.last_savings_bonus, expected)
	assert_true(sim.last_savings_bonus >= 60, "300 gold kept earns at least 60")
	assert_signal_emitted_with_parameters(sim, "savings_paid", [sim.last_savings_bonus])
	var cleared: Array = get_signal_parameters(sim, "wave_cleared")
	assert_eq(cleared[2], rules.gold_per_wave + sim.last_savings_bonus, "the wave's gold includes the bonus")


func test_the_savings_bonus_is_capped_and_never_negative() -> void:
	var rules: RunRules = registry.run_rules
	assert_eq(rules.savings_bonus_for(0, 0.2), 0)
	assert_eq(rules.savings_bonus_for(-50, 0.2), 0)
	assert_eq(rules.savings_bonus_for(99, 0.2), 19)
	assert_eq(rules.savings_bonus_for(500, 0.2), 100)
	assert_eq(rules.savings_bonus_for(100000, 0.2), rules.savings_bonus_cap)


func test_the_savings_cap_grows_geometrically_from_the_first_wave() -> void:
	var rules: RunRules = registry.run_rules
	assert_eq(rules.savings_cap_at(1), 150, "the first wave keeps the base cap")
	assert_eq(rules.savings_cap_at(2), 162)
	assert_eq(rules.savings_cap_at(11), roundi(150 * pow(1.08, 10)))
	assert_eq(rules.savings_bonus_for(100000, 0.2, 11), rules.savings_cap_at(11))
	for wave in range(1, 60):
		assert_true(rules.savings_cap_at(wave + 1) > rules.savings_cap_at(wave), "it always rises")


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
