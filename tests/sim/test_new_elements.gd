extends GutTest
## Water, Earth and Void towers, their effects (slow, knockback, stun, shatter, curse, auras), and
## turning a base tower into a hybrid in place.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"switchback"
## Buildable cells next to the first stretch of path.
const CELL := Vector2i(2, 3)
const NEXT_CELL := Vector2i(3, 3)

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _sim() -> RunSim:
	var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
	sim.tree.points = 20
	sim.gold = 5000
	return sim


func _enemy(sim: RunSim, enemy_id: StringName = &"grunt", progress := 200.0) -> SimEnemy:
	var enemy := SimEnemy.new(999, sim.config.enemies[enemy_id], 1.0)
	enemy.progress = progress
	return enemy


func _effect(kind: StringName) -> StatusEffectData:
	var spec := StatusEffectData.new()
	spec.kind = kind
	spec.duration = 1.0
	return spec


func test_each_new_element_unlocks_its_tower() -> void:
	var sim := _sim()
	for pair: Array in [[&"water_entry", &"water_wellspring"], [&"earth_entry", &"earth_monolith"], [&"void_entry", &"void_obelisk"]]:
		assert_false(sim.is_unlocked(pair[1]))
		assert_true(sim.allocate_node(pair[0]), "took %s" % pair[0])
		assert_true(sim.is_unlocked(pair[1]), "%s unlocked" % pair[1])


func test_every_hybrid_has_a_bridge_between_its_elements() -> void:
	var sim := _sim()
	for pair: Array in [
		[&"bridge_bog", &"hybrid_bog", [&"nature_entry", &"nature_cw", &"water_entry", &"water_ccw"]],
		[&"bridge_quagmire", &"hybrid_quagmire", [&"water_entry", &"water_cw", &"earth_entry", &"earth_ccw"]],
		[&"bridge_gravity_well", &"hybrid_gravity_well", [&"earth_entry", &"earth_cw", &"void_entry", &"void_ccw"]],
		[&"bridge_soulflame", &"hybrid_soulflame", [&"void_entry", &"void_cw", &"fire_entry", &"fire_ccw"]],
	]:
		for id: StringName in pair[2]:
			sim.allocate_node(id)
		assert_true(sim.allocate_node(pair[0]), "took %s" % pair[0])
		assert_true(sim.is_unlocked(pair[1]))


func test_stuns_stop_enemies_but_never_chain_forever() -> void:
	var sim := _sim()
	var enemy := _enemy(sim)
	enemy.apply_status(_effect(&"stun"), null, 1.0)
	assert_eq(enemy.speed(), 0.0, "stunned")
	enemy.statuses[&"stun"].time_left = 0.01
	sim.enemies.append(enemy)
	sim.state = RunSim.State.WAVE
	sim._tick_statuses(0.05)
	assert_false(enemy.has_status(&"stun"), "the stun wore off")
	enemy.apply_status(_effect(&"stun"), null, 1.0)
	assert_false(enemy.has_status(&"stun"), "immune for a moment after a stun")
	sim._tick_statuses(SimEnemy.STUN_IMMUNITY + 0.1)
	enemy.apply_status(_effect(&"stun"), null, 1.0)
	assert_true(enemy.has_status(&"stun"), "can be stunned again later")


func test_bosses_cannot_be_stunned_and_take_half_knockback() -> void:
	var sim := _sim()
	var boss := _enemy(sim, &"warden")
	boss.apply_status(_effect(&"stun"), null, 1.0)
	assert_false(boss.has_status(&"stun"))
	assert_eq(boss.knock_back(20.0), 10.0)


func test_knockback_is_capped_per_enemy() -> void:
	var sim := _sim()
	var enemy := _enemy(sim, &"grunt", 1000.0)
	var total := 0.0
	for i in 100:
		total += enemy.knock_back(30.0)
	assert_eq(total, SimEnemy.MAX_KNOCKBACK)
	assert_eq(enemy.progress, 1000.0 - SimEnemy.MAX_KNOCKBACK)


func test_shatter_lowers_armour_per_stack() -> void:
	var sim := _sim()
	var brute := _enemy(sim, &"brute")
	var spec := _effect(&"shatter")
	spec.armour_reduction = 1.5
	spec.max_stacks = 5
	brute.apply_status(spec, null, 1.0)
	brute.apply_status(spec, null, 1.0)
	assert_eq(brute.effective_armour(), brute.armour - 3.0)
	for i in 10:
		brute.apply_status(spec, null, 1.0)
	assert_eq(brute.effective_armour(), 0.0, "never below zero")


func test_strength_nodes_scale_slows() -> void:
	var sim := _sim()
	sim.allocate_node(&"water_entry")
	var tower := sim.place_tower(&"water_wellspring", CELL)
	var before := tower.effect_spec(&"slow").slow
	sim.allocate_node(&"water_core")
	sim.allocate_node(&"water_notable")
	assert_almost_eq(tower.effect_spec(&"slow").slow, before * 1.3, 0.0001, "Deep Freeze")


func test_void_auras_boost_neighbours_but_not_themselves() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	sim.allocate_node(&"void_entry")
	var brazier := sim.place_tower(&"fire_brazier", CELL)
	var base_damage := brazier.damage
	var obelisk := sim.place_tower(&"void_obelisk", NEXT_CELL)
	assert_almost_eq(brazier.damage, base_damage * 1.15, 0.0001)
	assert_eq(obelisk.aura_bonus, 0.0)
	sim.sell_tower(obelisk)
	assert_almost_eq(brazier.damage, base_damage, 0.0001, "the aura leaves with the tower")


func test_a_base_tower_can_become_a_hybrid_in_place() -> void:
	var sim := _sim()
	sim.allocate_node(&"water_entry")
	var tower := sim.place_tower(&"water_wellspring", CELL)
	assert_eq(sim.hybrid_options(tower), [] as Array[StringName], "no bridge taken yet")
	for id: StringName in [&"water_ccw", &"nature_entry", &"nature_cw", &"bridge_bog"]:
		assert_true(sim.allocate_node(id))
	assert_eq(sim.hybrid_options(tower), [&"hybrid_bog"] as Array[StringName])
	var price := sim.hybrid_upgrade_price(tower, &"hybrid_bog")
	assert_eq(price, sim.tower_price(&"hybrid_bog") - sim.tower_price(&"water_wellspring"))
	var gold := sim.gold
	assert_true(sim.upgrade_to_hybrid(tower, &"hybrid_bog"))
	assert_eq(sim.gold, gold - price)
	assert_eq(tower.data.id, &"hybrid_bog")
	assert_eq(sim.tower_at(CELL), tower, "same tower, same place")
	assert_eq(tower.price_paid, sim.tower_price(&"hybrid_bog"), "sells as a hybrid")
	assert_true(tower.splash_radius > 0.0, "stats follow the new type")
	assert_eq(sim.hybrid_options(tower), [] as Array[StringName], "no triple is unlocked, so the dual stays as it is")


func test_hybrid_upgrade_needs_gold() -> void:
	var sim := _sim()
	for id: StringName in [&"void_entry", &"void_cw", &"fire_entry", &"fire_ccw", &"bridge_soulflame"]:
		sim.allocate_node(id)
	var tower := sim.place_tower(&"fire_brazier", CELL)
	sim.gold = 0
	assert_string_contains(sim.hybrid_upgrade_error(tower, &"hybrid_soulflame"), "gold")
	assert_false(sim.upgrade_to_hybrid(tower, &"hybrid_soulflame"))
	assert_eq(tower.data.id, &"fire_brazier")


func test_new_towers_fight_a_wave() -> void:
	for tower_id: StringName in [&"water_wellspring", &"earth_monolith", &"void_obelisk"]:
		var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
		sim.tree.points = 5
		sim.allocate_node(StringName(String(tower_id).get_slice("_", 0) + "_entry"))
		var tower := sim.place_tower(tower_id, CELL)
		assert_not_null(tower, "built %s" % tower_id)
		sim.start_next_wave()
		var elapsed := 0.0
		while sim.state == RunSim.State.WAVE and elapsed < 300.0:
			sim.step(0.05)
			elapsed += 0.05
		assert_gt(tower.damage_dealt, 0.0, "%s dealt damage" % tower_id)


func test_levels_cost_gold_and_raise_damage_and_range() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	var damage := tower.damage
	var reach := tower.attack_range
	var price := tower.level_up_price()
	assert_eq(price, roundi(tower.type_price * 0.5))
	var gold := sim.gold
	assert_true(sim.level_up(tower))
	assert_eq(tower.level, 2)
	assert_eq(sim.gold, gold - price)
	assert_almost_eq(tower.damage, damage * 1.3, 0.0001)
	assert_almost_eq(tower.attack_range, reach * 1.08, 0.0001)
	assert_true(sim.level_up(tower))
	assert_false(sim.level_up(tower), "level 3 is the top")
	assert_string_contains(sim.level_up_error(tower), "top level")
	assert_eq(tower.price_paid, tower.type_price + roundi(tower.type_price * 0.5) + roundi(tower.type_price * 0.75))


func test_every_tower_offers_two_ascendancies() -> void:
	for tower_id: StringName in registry.towers:
		var data: TowerData = registry.towers[tower_id]
		assert_eq(data.ascendancies.size(), 2, "%s ascendancies" % tower_id)
		for option in data.ascendancies:
			assert_false(option.id.is_empty() or option.modifiers.is_empty(), "%s/%s is filled in" % [tower_id, option.id])


func test_ascending_needs_the_top_level_and_is_final() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_string_contains(sim.ascend_error(tower, &"pyre"), "level")
	sim.level_up(tower)
	sim.level_up(tower)
	var splash := tower.splash_radius
	assert_true(sim.ascend(tower, &"pyre"))
	assert_almost_eq(tower.splash_radius, splash * 1.6, 0.0001)
	assert_false(sim.ascend(tower, &"hearth"), "only one ascendancy")
	assert_eq(tower.ascendancy.id, &"pyre")


func test_ascendancies_can_add_status_stacks() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	sim.level_up(tower)
	sim.level_up(tower)
	var stacks := tower.effect_spec(&"burn").max_stacks
	sim.ascend(tower, &"hearth")
	assert_eq(tower.effect_spec(&"burn").max_stacks, stacks + 3)


func test_a_levelled_base_tower_keeps_its_level_as_a_hybrid_but_ascended_ones_cannot_change() -> void:
	var sim := _sim()
	for id: StringName in [&"water_entry", &"water_ccw", &"nature_entry", &"nature_cw", &"bridge_bog"]:
		sim.allocate_node(id)
	var tower := sim.place_tower(&"water_wellspring", CELL)
	sim.level_up(tower)
	assert_true(sim.upgrade_to_hybrid(tower, &"hybrid_bog"))
	assert_eq(tower.level, 2)
	var other := sim.place_tower(&"water_wellspring", NEXT_CELL)
	sim.level_up(other)
	sim.level_up(other)
	sim.ascend(other, &"frostspring")
	assert_eq(sim.hybrid_options(other), [] as Array[StringName])
	assert_false(sim.upgrade_to_hybrid(other, &"hybrid_bog"))


func test_selling_refunds_levels_too() -> void:
	var sim := _sim()
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", CELL)
	sim.level_up(tower)
	assert_eq(sim.sell_value(tower), floori(tower.price_paid * registry.run_rules.sell_refund))
	assert_true(tower.price_paid > tower.type_price)


func test_every_element_pair_has_exactly_one_hybrid() -> void:
	var pairs: Dictionary[String, StringName] = {}
	for tower_id: StringName in registry.towers:
		var data: TowerData = registry.towers[tower_id]
		if not data.is_dual():
			continue
		var names: Array[String] = [String(data.elements[0]), String(data.elements[1])]
		names.sort()
		var key := "+".join(names)
		assert_false(pairs.has(key), "%s and %s share %s" % [tower_id, pairs.get(key, &""), key])
		pairs[key] = tower_id
	assert_eq(pairs.size(), 15)


func test_far_hybrids_unlock_from_both_elements_nodes() -> void:
	var sim := _sim()
	for id: StringName in [&"fire_entry", &"fire_core", &"nature_entry"]:
		sim.allocate_node(id)
	assert_false(sim.is_unlocked(&"hybrid_wildfire"))
	assert_string_contains(sim.placement_error(&"hybrid_wildfire", CELL), "Unlock")
	sim.allocate_node(&"nature_core")
	assert_true(sim.is_unlocked(&"hybrid_wildfire"))
	assert_not_null(sim.place_tower(&"hybrid_wildfire", CELL))


func test_opposite_hybrids_need_both_notables_and_are_never_resisted() -> void:
	var sim := _sim()
	for id: StringName in [&"fire_entry", &"fire_core", &"fire_notable", &"water_entry", &"water_core"]:
		sim.allocate_node(id)
	assert_false(sim.is_unlocked(&"hybrid_steam"))
	sim.allocate_node(&"water_notable")
	assert_true(sim.is_unlocked(&"hybrid_steam"))
	var steam: TowerData = registry.towers[&"hybrid_steam"]
	var indices: Array[int] = registry.tower_element_indices(steam)
	for wave_element in 6:
		assert_eq(ElementRules.damage_multiplier(indices, wave_element), 1.0, "never resisted, never weak-point")


func test_a_base_tower_can_become_a_far_hybrid() -> void:
	var sim := _sim()
	for id: StringName in [&"storm_entry", &"storm_core", &"void_entry", &"void_core"]:
		sim.allocate_node(id)
	var tower := sim.place_tower(&"storm_spire", CELL)
	assert_has(sim.hybrid_options(tower), &"hybrid_riftstorm")
	assert_true(sim.upgrade_to_hybrid(tower, &"hybrid_riftstorm"))


func test_far_hybrids_fight_a_wave() -> void:
	for tower_id: StringName in [&"hybrid_wildfire", &"hybrid_squall", &"hybrid_ironbark", &"hybrid_abyss", &"hybrid_magma",
			&"hybrid_riftstorm", &"hybrid_steam", &"hybrid_lodestone", &"hybrid_blightroot"]:
		var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
		sim.tree.points = 20
		sim.gold = 1000
		var data: TowerData = registry.towers[tower_id]
		for element_id in data.elements:
			for part in ["entry", "core", "notable"]:
				sim.allocate_node(StringName("%s_%s" % [element_id, part]))
		var tower := sim.place_tower(tower_id, CELL)
		assert_not_null(tower, "built %s" % tower_id)
		if tower == null:
			continue
		sim.start_next_wave()
		var elapsed := 0.0
		while sim.state == RunSim.State.WAVE and elapsed < 300.0:
			sim.step(0.05)
			elapsed += 0.05
		assert_gt(tower.damage_dealt, 0.0, "%s dealt damage" % tower_id)
