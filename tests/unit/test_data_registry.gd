extends GutTest
## Loads the real data files. If someone mistypes an id in a .tres file, these tests fail.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func test_real_data_has_no_errors() -> void:
	var errors: PackedStringArray = registry.validate()
	assert_eq(errors.size(), 0, "Data errors:\n" + "\n".join(errors))


func test_all_six_elements_load_in_ring_order() -> void:
	assert_eq(registry.elements.size(), 6)
	assert_eq(registry.element_index(&"fire"), 0)
	assert_eq(registry.element_index(&"void"), 5)
	assert_eq(registry.element_index(&"missing"), -1)


func test_prototype_content_loads() -> void:
	assert_eq(registry.towers.size(), 44, "6 base towers, 3 long-range towers, 15 duals (one per element pair) and 20 triples")
	assert_eq(registry.enemies.size(), 60, "16 base enemies, 30 of the six hordes, 6 Heralds, the Regent, 3 old citadel buildings, Nhal Vorath and Vael-Orrun's three forms")
	assert_true(registry.wave_sets.has(&"prototype"))
	assert_eq(registry.wave_sets[&"prototype"].waves.size(), 10)
	assert_not_null(registry.run_rules)


func test_in_run_tree_unlocks_every_prototype_tower() -> void:
	var graph: TreeGraph = registry.in_run_tree()
	var state := TreeState.new(graph, 100000)
	# Take every node, nearest first, as a player with unlimited points would.
	var taken_any := true
	while taken_any:
		taken_any = false
		for id in graph.ids():
			if state.allocate(id):
				taken_any = true
	# Each keystone pair is a pick-one choice: one of the two stays closed.
	var closed := 0
	for id in graph.ids():
		if state.is_excluded(id):
			closed += 1
	assert_gt(closed, 0, "the keystone pairs close their partners")
	assert_eq(state.allocated_ids().size() + closed, graph.size(), "every node is reachable")
	for tower_id: StringName in registry.towers:
		var data: TowerData = registry.towers[tower_id]
		if data.requires_nodes.is_empty():
			assert_has(state.unlocked_towers(), tower_id)
		else:
			for node_id in data.requires_nodes:
				assert_true(state.is_allocated(node_id), "%s needs %s" % [tower_id, node_id])


func test_hybrid_of_non_neighbours_is_reported() -> void:
	var bad := TowerData.new()
	bad.id = &"bad_hybrid"
	bad.elements = [&"fire", &"nature"]
	registry.towers[bad.id] = bad
	var errors: PackedStringArray = registry.validate()
	assert_true(errors.size() == 1 and "requires_nodes" in errors[0], "Got: %s" % [errors])


func test_unknown_tree_link_is_reported() -> void:
	var node_data := TreeNodeData.new()
	node_data.id = &"orphan"
	node_data.links = [&"does_not_exist"]
	registry.in_run_tree_nodes.append(node_data)
	var errors := "\n".join(registry.validate())
	assert_string_contains(errors, "links to unknown node 'does_not_exist'")
	assert_string_contains(errors, "'orphan': cannot be reached from the start")


func test_unknown_enemy_in_a_wave_is_reported() -> void:
	var group := SpawnGroup.new()
	group.enemy = &"ghost"
	var wave := WaveData.new()
	wave.groups = [group]
	var wave_set := WaveSet.new()
	wave_set.id = &"broken"
	wave_set.waves = [wave]
	registry.wave_sets[wave_set.id] = wave_set
	var errors := "\n".join(registry.validate())
	assert_string_contains(errors, "unknown enemy 'ghost'")


func test_the_meta_tree_can_be_completed() -> void:
	var graph: TreeGraph = registry.meta_tree()
	var state := TreeState.new(graph, 999)
	var taken_any := true
	while taken_any:
		taken_any = false
		for id in graph.ids():
			if state.allocate(id):
				taken_any = true
	# Pick-one choices close their partner, so one node of each pair stays open.
	var pairs := 0
	for id in graph.ids():
		for other in graph.exclusions(id):
			if String(other) > String(id):
				pairs += 1
				assert_false(state.is_allocated(id) and state.is_allocated(other), "%s and %s both taken" % [id, other])
	assert_gt(pairs, 0, "the meta tree has pick-one choices")
	assert_eq(state.allocated_ids().size(), graph.size() - pairs, "every other meta node is reachable")


func test_bad_meta_unlocks_are_reported() -> void:
	var node_data := TreeNodeData.new()
	node_data.id = &"bad_meta"
	node_data.region = &"command"
	node_data.links = [&"meta_start"]
	node_data.unlocks_towers = [&"fire_brazier"]
	node_data.unlocks_maps = [&"atlantis"]
	node_data.unlocks_nodes = [&"nowhere"]
	node_data.unlocks_difficulties = [&"impossible"]
	registry.meta_tree_nodes.append(node_data)
	var errors := "\n".join(registry.validate())
	assert_string_contains(errors, "towers are unlocked in the in-run web")
	assert_string_contains(errors, "unknown map 'atlantis'")
	assert_string_contains(errors, "unknown in-run node 'nowhere'")
	assert_string_contains(errors, "unknown difficulty 'impossible'")


func test_in_run_nodes_cannot_unlock_maps() -> void:
	var node_data := TreeNodeData.new()
	node_data.id = &"greedy"
	node_data.links = [&"start"]
	node_data.unlocks_maps = [&"serpentine"]
	registry.in_run_tree_nodes.append(node_data)
	assert_string_contains("\n".join(registry.validate()), "only meta tree nodes can unlock")


func test_locking_every_map_is_reported() -> void:
	var node_data := TreeNodeData.new()
	node_data.id = &"gatekeeper"
	node_data.region = &"expeditions"
	node_data.links = [&"meta_start"]
	var all_maps: Array[StringName] = []
	all_maps.assign(registry.maps.keys())
	node_data.unlocks_maps = all_maps
	registry.meta_tree_nodes.append(node_data)
	assert_string_contains("\n".join(registry.validate()), "Every map is locked")


func test_an_unknown_meta_branch_is_reported() -> void:
	var node_data := TreeNodeData.new()
	node_data.id = &"lost"
	node_data.region = &"atlantis"
	node_data.links = [&"meta_start"]
	registry.meta_tree_nodes.append(node_data)
	assert_string_contains("\n".join(registry.validate()), "unknown region 'atlantis'")
