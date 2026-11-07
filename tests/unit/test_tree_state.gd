extends GutTest
## A small test tree:
##
##   start - a - b - c
##           |
##           d (costs 2, unlocks a tower, carries a modifier)

var graph: TreeGraph


func _node(id: StringName, kind: TreeNodeData.Kind, links: Array[StringName], cost: int = 1) -> TreeNodeData:
	var data := TreeNodeData.new()
	data.id = id
	data.kind = kind
	data.links = links
	data.cost = cost
	return data


func before_each() -> void:
	var d := _node(&"d", TreeNodeData.Kind.NOTABLE, [&"a"], 2)
	d.unlocks_towers = [&"test_tower"]
	d.modifiers = [Modifier.create(&"damage", Modifier.Kind.INCREASED, 0.5)]
	var nodes: Array[TreeNodeData] = [
		_node(&"start", TreeNodeData.Kind.START, [], 0),
		_node(&"a", TreeNodeData.Kind.ENTRY, [&"start"]),
		_node(&"b", TreeNodeData.Kind.MINOR, [&"a"]),
		_node(&"c", TreeNodeData.Kind.MINOR, [&"b"]),
		d,
	]
	graph = TreeGraph.new(nodes)


func test_links_work_both_ways() -> void:
	assert_has(graph.neighbours(&"start"), &"a")
	assert_has(graph.neighbours(&"a"), &"start")
	assert_has(graph.neighbours(&"a"), &"d")


func test_start_is_taken_for_free() -> void:
	var state := TreeState.new(graph, 3)
	assert_true(state.is_allocated(&"start"))
	assert_eq(state.points, 3)


func test_can_only_take_nodes_next_to_taken_ones() -> void:
	var state := TreeState.new(graph, 5)
	assert_true(state.can_allocate(&"a"))
	assert_false(state.can_allocate(&"b"), "b is not connected to anything taken yet")
	assert_true(state.allocate(&"a"))
	assert_true(state.can_allocate(&"b"))


func test_taking_a_node_spends_its_cost() -> void:
	var state := TreeState.new(graph, 3)
	state.allocate(&"a")
	state.allocate(&"d")
	assert_eq(state.points, 0)


func test_cannot_overspend() -> void:
	var state := TreeState.new(graph, 2)
	state.allocate(&"a")
	assert_false(state.can_allocate(&"d"), "d costs 2 and only 1 point is left")
	assert_false(state.allocate(&"d"))


func test_cannot_take_a_node_twice_or_an_unknown_node() -> void:
	var state := TreeState.new(graph, 5)
	state.allocate(&"a")
	assert_false(state.allocate(&"a"))
	assert_false(state.allocate(&"missing"))


func test_refunding_a_leaf_returns_points() -> void:
	var state := TreeState.new(graph, 2)
	state.allocate(&"a")
	state.allocate(&"b")
	assert_true(state.refund(&"b"))
	assert_eq(state.points, 1)
	assert_false(state.is_allocated(&"b"))


func test_cannot_refund_a_node_that_others_depend_on() -> void:
	var state := TreeState.new(graph, 3)
	state.allocate(&"a")
	state.allocate(&"b")
	state.allocate(&"c")
	assert_false(state.can_refund(&"b"), "c would be cut off from the start")
	assert_false(state.can_refund(&"start"))


func test_modifiers_and_unlocks_come_from_taken_nodes() -> void:
	var state := TreeState.new(graph, 3)
	assert_eq(state.modifiers().size(), 0)
	state.allocate(&"a")
	state.allocate(&"d")
	assert_eq(state.modifiers().size(), 1)
	assert_eq(state.unlocked_towers().size(), 1)
	assert_has(state.unlocked_towers(), &"test_tower")


func test_changed_signal_fires() -> void:
	var state := TreeState.new(graph, 1)
	watch_signals(state)
	state.allocate(&"a")
	assert_signal_emitted(state, "changed")


func test_restore_takes_nodes_in_any_order() -> void:
	var state := TreeState.new(graph, 10)
	state.restore([&"c", &"d", &"b", &"a"])
	for id: StringName in [&"a", &"b", &"c", &"d"]:
		assert_true(state.is_allocated(id), "%s is taken" % id)
	assert_eq(state.points, 5)


func test_restore_skips_nodes_it_cannot_take() -> void:
	var state := TreeState.new(graph, 2)
	state.restore([&"missing", &"c", &"a", &"d"])
	assert_eq(state.allocated_ids().size(), 2, "only the start and a")
	assert_true(state.is_allocated(&"a"))
	assert_false(state.is_allocated(&"c"), "c is cut off without b")
	assert_false(state.is_allocated(&"d"), "d costs 2 and only 1 point is left")
	assert_eq(state.points, 1)


func test_reset_refunds_everything_but_the_start() -> void:
	var state := TreeState.new(graph, 5)
	state.restore([&"a", &"b", &"d"])
	watch_signals(state)
	state.reset()
	assert_eq(state.allocated_ids().size(), 1)
	assert_true(state.is_allocated(&"start"))
	assert_eq(state.points, 5)
	assert_signal_emitted(state, "changed")


func test_path_to_a_far_node_starts_at_the_taken_part() -> void:
	var state := TreeState.new(graph, 5)
	var from_start: Array[StringName] = [&"start", &"a", &"b", &"c"]
	assert_eq(state.path_to(&"c"), from_start)
	state.allocate(&"a")
	var from_a: Array[StringName] = [&"a", &"b", &"c"]
	assert_eq(state.path_to(&"c"), from_a)


func test_path_to_is_empty_for_taken_unknown_or_blocked_nodes() -> void:
	var state := TreeState.new(graph, 5)
	state.allocate(&"a")
	assert_eq(state.path_to(&"a").size(), 0, "already taken")
	assert_eq(state.path_to(&"missing").size(), 0)
	state.lock([&"b"])
	assert_eq(state.path_to(&"c").size(), 0, "the only way there runs through a locked node")
