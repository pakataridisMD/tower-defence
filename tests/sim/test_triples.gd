extends GutTest
## Triple-element towers: one for every set of three elements, unlocked by the three core nodes,
## and reachable by fusing a dual in place.

const TEST_ROAD := preload("res://tests/support/test_road.tres")

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"test_road"
## A buildable cell next to the first stretch of path.
const CELL := Vector2i(2, 3)

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	# The small 24 x 15 road these tests were written against (the real maps are bigger and curved).
	registry.maps[&"test_road"] = TEST_ROAD


func _sim() -> RunSim:
	var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
	sim.tree.points = 40
	sim.gold = 5000
	return sim


func _triples() -> Array[TowerData]:
	var result: Array[TowerData] = []
	for data: TowerData in registry.towers.values():
		if data.is_triple():
			result.append(data)
	return result


func _take_cores(sim: RunSim, elements: Array[StringName]) -> void:
	for element_id in elements:
		sim.allocate_node(StringName("%s_entry" % element_id))
		sim.allocate_node(StringName("%s_core" % element_id))


func test_every_set_of_three_elements_has_exactly_one_triple() -> void:
	var sets: Dictionary[String, StringName] = {}
	for data in _triples():
		var names: Array[String] = []
		for element_id in data.elements:
			names.append(String(element_id))
		names.sort()
		var key := "+".join(names)
		assert_false(sets.has(key), "%s and %s share %s" % [data.id, sets.get(key, &""), key])
		sets[key] = data.id
	assert_eq(sets.size(), 20)


func test_triples_carry_all_three_element_tags() -> void:
	var data: TowerData = registry.towers[&"triple_cinderstorm"]
	var tags := data.all_tags()
	for tag: StringName in [&"fire", &"storm", &"nature", &"hybrid", &"triple"]:
		assert_has(tags, tag)
	assert_true(data.is_hybrid() and data.is_triple() and not data.is_dual())
	var dual: TowerData = registry.towers[&"hybrid_plasma"]
	assert_does_not_have(dual.all_tags(), &"triple")


func test_wave_resistance_averages_the_three_elements() -> void:
	var indices: Array[int] = registry.tower_element_indices(registry.towers[&"triple_thunder_geyser"])
	# Fire and Water cancel out on each other's waves, and Storm is unaffected by both.
	assert_almost_eq(ElementRules.damage_multiplier(indices, registry.element_index(&"fire")), 1.0, 0.0001)
	# Against its third element it is resisted by a sixth; against that element's opposite it gains a sixth.
	assert_almost_eq(ElementRules.damage_multiplier(indices, registry.element_index(&"storm")), 2.5 / 3.0, 0.0001)
	assert_almost_eq(ElementRules.damage_multiplier(indices, registry.element_index(&"earth")), 3.5 / 3.0, 0.0001)


func test_a_triple_unlocks_from_its_three_core_nodes() -> void:
	var sim := _sim()
	_take_cores(sim, [&"fire", &"storm"])
	assert_false(sim.is_unlocked(&"triple_cinderstorm"))
	assert_string_contains(sim.placement_error(&"triple_cinderstorm", CELL), "Unlock")
	_take_cores(sim, [&"nature"])
	assert_true(sim.is_unlocked(&"triple_cinderstorm"))
	assert_not_null(sim.place_tower(&"triple_cinderstorm", CELL))
	assert_false(sim.is_unlocked(&"triple_starfall"), "no Void core yet")


func test_a_dual_can_fuse_into_a_triple_and_a_base_tower_cannot_skip_a_step() -> void:
	var sim := _sim()
	_take_cores(sim, [&"fire", &"nature", &"earth"])
	var base := sim.place_tower(&"fire_brazier", CELL)
	assert_does_not_have(sim.hybrid_options(base), &"triple_worldforge", "a base tower becomes a dual first")
	assert_has(sim.hybrid_options(base), &"hybrid_wildfire")
	assert_true(sim.upgrade_to_hybrid(base, &"hybrid_wildfire"))
	sim.level_up(base)
	assert_eq(sim.hybrid_options(base), [&"triple_worldforge"] as Array[StringName])
	var price := sim.hybrid_upgrade_price(base, &"triple_worldforge")
	assert_eq(price, sim.tower_price(&"triple_worldforge") - sim.tower_price(&"hybrid_wildfire"))
	var gold := sim.gold
	assert_true(sim.upgrade_to_hybrid(base, &"triple_worldforge"))
	assert_eq(sim.gold, gold - price)
	assert_eq(base.data.id, &"triple_worldforge")
	assert_eq(base.level, 2, "it keeps its level")
	assert_eq(sim.hybrid_options(base), [] as Array[StringName], "a triple is the last step")


func test_an_ascended_dual_cannot_fuse() -> void:
	var sim := _sim()
	_take_cores(sim, [&"fire", &"nature", &"earth"])
	var tower := sim.place_tower(&"hybrid_wildfire", CELL)
	sim.level_up(tower)
	sim.level_up(tower)
	assert_true(sim.ascend(tower, &"rot_blossom"))
	assert_eq(sim.hybrid_options(tower), [] as Array[StringName])
	assert_false(sim.upgrade_to_hybrid(tower, &"triple_worldforge"))


func test_triples_can_level_up_and_ascend() -> void:
	var sim := _sim()
	_take_cores(sim, [&"void", &"fire", &"storm"])
	var tower := sim.place_tower(&"triple_starfall", CELL)
	sim.level_up(tower)
	sim.level_up(tower)
	var chains := tower.chain_count
	assert_true(sim.ascend(tower, &"supernova"))
	assert_eq(tower.chain_count, chains + 3)


func test_every_triple_fights_a_wave() -> void:
	for data in _triples():
		var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
		sim.tree.points = 20
		sim.gold = 1000
		_take_cores(sim, data.elements)
		var tower := sim.place_tower(data.id, CELL)
		assert_not_null(tower, "built %s" % data.id)
		if tower == null:
			continue
		sim.start_next_wave()
		var elapsed := 0.0
		while sim.state == RunSim.State.WAVE and elapsed < 300.0:
			sim.step(0.05)
			elapsed += 0.05
		assert_gt(tower.damage_dealt, 0.0, "%s dealt damage" % data.id)


func test_triples_cost_more_than_any_dual() -> void:
	var dearest_dual := 0
	for data: TowerData in registry.towers.values():
		if data.is_dual():
			dearest_dual = maxi(dearest_dual, data.cost)
	for data in _triples():
		assert_gt(data.cost, dearest_dual, "%s is a top-tier tower" % data.id)
