extends GutTest
## The in-run skill tree (tools/web/gen_skill_web.py): six element columns that climb from level I
## to VI, a branch of options between two levels with one pick (two where it has four), a node for
## every dual and triple tower that needs a level of each of its elements, and clicks that take the
## way to a far node.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const LEVELS: Array[String] = ["entry", "level2", "core", "notable", "level5", "level6"]
const KEYSTONES: Array[StringName] = [&"keystone_focus", &"keystone_overcharge", &"keystone_hoard"]

var registry: Node
var graph: TreeGraph


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	graph = registry.in_run_tree()


func _sim(points: int = 0) -> RunSim:
	var sim := RunSim.new(RunConfig.from_registry(registry, registry.maps.keys()[0]))
	sim.tree.points = points
	return sim


func test_every_element_climbs_six_levels_in_its_own_column() -> void:
	assert_eq(registry.elements.size(), 6)
	for element: StringName in registry.elements:
		var column := graph.node(StringName("%s_entry" % element)).position.x
		var last_y := INF
		for part in LEVELS:
			var id := StringName("%s_%s" % [element, part])
			assert_true(graph.has_node_id(id), String(id))
			var data := graph.node(id)
			assert_eq(data.region, element)
			assert_almost_eq(data.position.x, column, 1.0, "%s stands in its element's column" % id)
			assert_true(data.position.y < last_y, "%s is above the level before it" % id)
			assert_almost_eq(data.position.y, graph.node(StringName("fire_%s" % part)).position.y, 1.0,
					"%s is level with Fire's" % id)
			last_y = data.position.y


func test_level_one_opens_the_elements_own_tower() -> void:
	for element: StringName in registry.elements:
		var entry := graph.node(StringName("%s_entry" % element))
		assert_eq(entry.kind, TreeNodeData.Kind.ENTRY)
		assert_eq(entry.unlocks_towers.size(), 1, "%s opens one tower" % entry.id)
		var tower: TowerData = registry.towers[entry.unlocks_towers[0]]
		assert_true(tower.elements.has(element) and not tower.is_hybrid())


func test_a_branch_of_options_stands_between_two_levels() -> void:
	for element: StringName in registry.elements:
		for row in range(1, LEVELS.size()):
			var below := StringName("%s_%s" % [element, LEVELS[row - 1]])
			var above := StringName("%s_%s" % [element, LEVELS[row]])
			assert_false(graph.neighbours(below).has(above), "%s is not joined straight to %s" % [below, above])
			var first := StringName("%s_b%d_a" % [element, row])
			assert_true(graph.has_node_id(first), String(first))
			var options := graph.branch_mates(first)
			options.append(first)
			assert_true(options.size() == 3 or options.size() == 4, "%s has %d options" % [first, options.size()])
			for id in options:
				var data := graph.node(id)
				assert_eq(data.kind, TreeNodeData.Kind.MINOR)
				assert_eq(data.choice_limit, 2 if options.size() == 4 else 1, "%s pick limit" % id)
				assert_true(graph.neighbours(id).has(below) and graph.neighbours(id).has(above),
						"%s joins %s to %s" % [id, below, above])


func test_a_branch_of_three_takes_one_pick() -> void:
	var sim := _sim(20)
	assert_true(sim.allocate_node(&"fire_entry"))
	assert_true(sim.allocate_node(&"fire_b1_b"))
	assert_eq(sim.tree.excluded_by(&"fire_b1_a"), &"fire_b1_b", "the pick closes the other options")
	assert_false(sim.allocate_node(&"fire_b1_a"))
	assert_false(sim.allocate_node(&"fire_b1_c"))
	assert_true(sim.refund_node(&"fire_b1_b"), "taken in this break, so it can be swapped")
	assert_true(sim.allocate_node(&"fire_b1_c"))


func test_a_branch_of_four_takes_two_picks() -> void:
	var sim := _sim(40)
	assert_true(sim.allocate_node(&"fire_level2"))
	assert_true(sim.allocate_node(&"fire_b2_a"))
	assert_eq(sim.tree.excluded_by(&"fire_b2_c"), &"", "a second pick is still open")
	assert_true(sim.allocate_node(&"fire_b2_c"))
	assert_false(sim.tree.excluded_by(&"fire_b2_b").is_empty(), "two picks close the rest")
	assert_false(sim.allocate_node(&"fire_b2_d"))
	assert_true(sim.allocate_node(&"fire_core"), "the next level opens above a pick")


func test_a_level_needs_a_pick_from_the_branch_below() -> void:
	var sim := _sim(40)
	assert_true(sim.allocate_node(&"fire_entry"))
	assert_false(sim.tree.can_allocate(&"fire_level2"), "no pick yet")
	assert_true(sim.allocate_node(&"fire_b1_a"))
	assert_true(sim.tree.can_allocate(&"fire_level2"))


func test_levels_cost_more_the_higher_they_stand() -> void:
	var last := 0
	for part in LEVELS:
		var cost := graph.node(StringName("fire_%s" % part)).cost
		assert_true(cost >= last, "fire_%s costs %d" % [part, cost])
		last = cost
	var sim := _sim()
	assert_eq(sim.tree.path_cost(&"fire_level2"), 3, "level I, a pick and level II")
	assert_true(sim.tree.path_cost(&"fire_level6") > 20, "the top of a column is a whole run's work")


func test_every_dual_and_triple_tower_has_a_node_of_its_own() -> void:
	var combos := 0
	for tower: TowerData in registry.towers.values():
		if not tower.is_hybrid():
			continue
		combos += 1
		var id := StringName("tower_%s" % tower.id)
		assert_true(graph.has_node_id(id), String(id))
		var data := graph.node(id)
		assert_eq(data.unlocks_towers, [tower.id] as Array[StringName])
		assert_true(graph.neighbours(id).is_empty(), "%s hangs on its requirements, not on links" % id)
		assert_eq(data.requires.size(), tower.elements.size(), "%s needs a level of each element" % id)
		var level_y := graph.node(data.requires[0]).position.y
		for other in data.requires:
			assert_true(tower.elements.has(graph.node(other).region), "%s needs %s" % [id, other])
			assert_almost_eq(graph.node(other).position.y, level_y, 1.0, "%s needs the same level of each" % id)
		assert_almost_eq(data.position.y, level_y, 60.0, "%s stands on the line of the level it needs" % id)
	assert_eq(combos, 35, "15 duals and 20 triples")


func test_a_dual_is_taken_at_level_two_of_both_elements() -> void:
	var sim := _sim(40)
	assert_true(sim.allocate_node(&"fire_level2"))
	assert_false(sim.tree.can_allocate(&"tower_hybrid_plasma"), "Storm II is missing")
	assert_true(sim.allocate_node(&"storm_level2"))
	assert_false(sim.is_unlocked(&"hybrid_plasma"), "the levels alone do not open the tower")
	assert_true(sim.tree.can_allocate(&"tower_hybrid_plasma"))
	assert_true(sim.allocate_node(&"tower_hybrid_plasma"))
	assert_true(sim.is_unlocked(&"hybrid_plasma"))
	assert_false(sim.is_unlocked(&"hybrid_soulflame"), "Void was not taken")


func test_a_triple_is_taken_at_level_three_of_three_elements() -> void:
	var sim := _sim(60)
	for id: StringName in [&"fire_core", &"storm_core"]:
		assert_true(sim.allocate_node(id))
	assert_true(sim.is_unlocked(&"storm_skyneedle"), "the long-range tower opens at its element's level III")
	assert_false(sim.tree.can_allocate(&"tower_triple_cinderstorm"), "Nature III is missing")
	assert_true(sim.allocate_node(&"nature_core"))
	assert_true(sim.allocate_node(&"tower_triple_cinderstorm"))
	assert_true(sim.is_unlocked(&"triple_cinderstorm"))


func test_a_click_on_a_tower_node_takes_the_levels_it_needs() -> void:
	var sim := _sim(40)
	var cost := sim.tree.path_cost(&"tower_hybrid_plasma")
	assert_eq(cost, 3 + 3 + 1, "Fire II, Storm II and the node")
	sim.tree.points = cost - 1
	assert_false(sim.allocate_node(&"tower_hybrid_plasma"), "one point short")
	assert_false(sim.tree.is_allocated(&"fire_entry"), "nothing taken on the way")
	sim.tree.points = cost
	assert_true(sim.allocate_node(&"tower_hybrid_plasma"))
	assert_true(sim.tree.is_allocated(&"fire_level2") and sim.tree.is_allocated(&"storm_level2"))
	assert_eq(sim.tree.points, 0)


func test_a_taken_tower_node_holds_its_levels() -> void:
	var sim := _sim(40)
	assert_true(sim.allocate_node(&"tower_hybrid_plasma"))
	assert_false(sim.can_refund_node(&"fire_level2"), "Plasma Coil needs it")
	assert_true(sim.can_refund_node(&"tower_hybrid_plasma"))
	assert_true(sim.refund_node(&"tower_hybrid_plasma"))
	assert_false(sim.is_unlocked(&"hybrid_plasma"))
	assert_true(sim.can_refund_node(&"fire_level2"), "free again once the tower node is refunded")


func test_the_old_level_and_keystone_ids_are_kept() -> void:
	# Stages (starting_nodes), saves and the Talents tree's unlocks_nodes name these.
	for element: StringName in registry.elements:
		for part: String in ["entry", "core", "notable"]:
			assert_true(graph.has_node_id(StringName("%s_%s" % [element, part])), "%s_%s" % [element, part])
	for id in KEYSTONES:
		assert_true(graph.has_node_id(id), String(id))


func test_an_option_gives_less_than_a_keystone_would() -> void:
	# A pick is a real choice (up to a fifth of a stat); the keystones carry the rule changes.
	for id in graph.ids():
		var data := graph.node(id)
		if data.kind != TreeNodeData.Kind.MINOR:
			continue
		assert_false(data.modifiers.is_empty(), "%s gives something" % id)
		for modifier in data.modifiers:
			if modifier.kind == Modifier.Kind.INCREASED:
				assert_true(absf(modifier.value) <= 0.25, "%s gives %s" % [id, modifier.value])


func test_every_keystone_is_a_pick_one_pair() -> void:
	var keystones := 0
	for id in graph.ids():
		if graph.node(id).kind == TreeNodeData.Kind.KEYSTONE:
			keystones += 1
			assert_eq(graph.exclusions(id).size(), 1, "%s has one partner" % id)
	assert_eq(keystones, 12, "two at the top of each element")


func test_a_click_on_a_far_node_takes_the_way_to_it() -> void:
	var sim := _sim(5)
	var cost := sim.tree.path_cost(&"fire_core")
	assert_eq(cost, 6, "levels I to III and a pick from each branch between")
	assert_false(sim.allocate_node(&"fire_core"), "not enough points")
	assert_false(sim.tree.is_allocated(&"fire_entry"), "nothing taken on the way")
	sim.tree.points = cost
	assert_true(sim.allocate_node(&"fire_core"))
	assert_true(sim.tree.is_allocated(&"fire_entry"))
	assert_eq(sim.tree.points, 0)
	assert_true(sim.can_refund_node(&"fire_core"), "taken in this break, so the tip can be refunded")
	assert_false(sim.can_refund_node(&"fire_entry"), "the rest of the way hangs on it")


func test_a_stage_closes_the_columns_of_elements_it_does_not_allow() -> void:
	# The lands open every element now, so a stage that limits them is made up here.
	var stage := StageData.new()
	stage.allowed_elements = [&"fire", &"storm", &"void"] as Array[StringName]
	var closed := MetaProgress.new(registry, PlayerProfile.new()).closed_nodes(stage)
	for id in graph.ids():
		var data := graph.node(id)
		if data.kind == TreeNodeData.Kind.START:
			continue
		var shut := false
		if not data.region.is_empty():
			shut = not stage.allowed_elements.has(data.region)
		else:
			# A keystone closes with the element under it, a tower node with any element it needs.
			for other in graph.neighbours(id) + graph.requirements(id):
				shut = shut or not stage.allowed_elements.has(graph.node(other).region)
		assert_eq(closed.has(id), shut, "%s closed" % id)
	assert_true(closed.has(&"tower_hybrid_thornstorm"), "Nature is closed, so the Storm and Nature dual is")
	assert_false(closed.has(&"tower_hybrid_plasma"))
