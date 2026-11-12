extends GutTest
## The in-run skill web (tools/web/gen_skill_web.py): ten times the first web's 40 nodes, costs that
## climb with distance from the Origin, the old ids still in place, and clicks that take the way to
## a far node.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const OLD_PARTS: Array[String] = ["entry", "cw", "ccw", "core", "notable"]
const OLD_IDS: Array[StringName] = [
	&"bridge_plasma", &"bridge_thornstorm", &"bridge_bog", &"bridge_quagmire", &"bridge_gravity_well",
	&"bridge_soulflame", &"keystone_focus", &"keystone_overcharge", &"keystone_hoard",
]

var registry: Node
var graph: TreeGraph


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	graph = registry.in_run_tree()


func test_the_web_is_ten_times_the_old_one() -> void:
	assert_true(graph.size() >= 390, "about 400 nodes, was 40 (has %d)" % graph.size())


func test_old_ids_are_kept() -> void:
	for element: StringName in registry.elements:
		for part in OLD_PARTS:
			assert_true(graph.has_node_id(StringName("%s_%s" % [element, part])), "%s_%s" % [element, part])
	for id in OLD_IDS:
		assert_true(graph.has_node_id(id), String(id))


func test_costs_climb_with_distance() -> void:
	# Minor nodes further out never cost less than nearer ones.
	var minors: Array[TreeNodeData] = []
	for id in graph.ids():
		var data := graph.node(id)
		if data.kind == TreeNodeData.Kind.MINOR:
			minors.append(data)
	minors.sort_custom(func(a: TreeNodeData, b: TreeNodeData) -> bool:
		return a.position.length() < b.position.length())
	assert_eq(minors.front().cost, 1, "the nearest cost 1")
	assert_true(minors.back().cost >= 5, "the rim costs 5 or more")
	for i in range(1, minors.size()):
		assert_true(minors[i].cost >= minors[i - 1].cost or
				minors[i].position.length() - minors[i - 1].position.length() < 5.0,
				"%s costs less than %s" % [minors[i].id, minors[i - 1].id])


func test_minor_nodes_are_small() -> void:
	# Each travel node gives a few percent, well under the old web's 10 to 25%.
	for id in graph.ids():
		var data := graph.node(id)
		if data.kind != TreeNodeData.Kind.MINOR:
			continue
		for modifier in data.modifiers:
			if modifier.kind == Modifier.Kind.INCREASED:
				assert_true(absf(modifier.value) <= 0.08, "%s gives %s" % [id, modifier.value])


func test_every_keystone_is_a_pick_one_pair() -> void:
	var keystones := 0
	for id in graph.ids():
		if graph.node(id).kind == TreeNodeData.Kind.KEYSTONE:
			keystones += 1
			assert_eq(graph.exclusions(id).size(), 1, "%s has one partner" % id)
	assert_eq(keystones, 12, "two at the tip of each element")


func test_a_click_on_a_far_node_takes_the_way_to_it() -> void:
	var sim := RunSim.new(RunConfig.from_registry(registry, registry.maps.keys()[0]))
	sim.tree.points = 4
	var cost := sim.tree.path_cost(&"fire_core")
	assert_eq(cost, 5, "entry, two travel nodes and the core")
	assert_false(sim.allocate_node(&"fire_core"), "not enough points")
	assert_false(sim.tree.is_allocated(&"fire_entry"), "nothing taken on the way")
	sim.tree.points = cost
	assert_true(sim.allocate_node(&"fire_core"))
	assert_true(sim.tree.is_allocated(&"fire_entry"))
	assert_eq(sim.tree.points, 0)
	assert_true(sim.can_refund_node(&"fire_core"), "taken in this break, so the tip can be refunded")
	assert_false(sim.can_refund_node(&"fire_entry"), "the rest of the way hangs on it")


func test_a_stage_closes_the_bridges_of_elements_it_does_not_allow() -> void:
	# The lands open every element now, so a stage that limits them is made up here.
	var stage := StageData.new()
	stage.allowed_elements = [&"fire", &"storm", &"void"] as Array[StringName]
	var closed := MetaProgress.new(registry, PlayerProfile.new()).closed_nodes(stage)
	for id in graph.ids():
		var data := graph.node(id)
		if data.region.is_empty() and data.kind != TreeNodeData.Kind.START:
			var touches_closed := false
			for other in graph.neighbours(id):
				var region := graph.node(other).region
				if not region.is_empty() and not stage.allowed_elements.has(region):
					touches_closed = true
			assert_eq(closed.has(id), touches_closed, "%s closed" % id)

