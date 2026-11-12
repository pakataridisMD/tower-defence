extends GutTest
## The Talents tree only unlocks towers: the six base towers are always open, every other tower
## stays out of runs until its talent is taken, and the skill web still opens it inside the run.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _meta(points: int = 0) -> MetaProgress:
	var profile := PlayerProfile.new()
	profile.meta_points_earned = points
	var meta := MetaProgress.new(registry, profile)
	meta.select_map(&"switchback")
	return meta


func test_every_tower_but_the_base_towers_has_exactly_one_talent() -> void:
	var talents: Dictionary[StringName, int] = {}
	for node_data: TreeNodeData in registry.meta_tree_nodes:
		if node_data.kind == TreeNodeData.Kind.START:
			continue
		assert_eq(node_data.unlocks_towers.size(), 1, "%s unlocks one tower" % node_data.id)
		assert_true(node_data.modifiers.is_empty(), "%s gives no stat bonus" % node_data.id)
		assert_true(node_data.unlocks_maps.is_empty() and node_data.unlocks_difficulties.is_empty()
				and node_data.unlocks_nodes.is_empty(), "%s unlocks nothing but its tower" % node_data.id)
		for tower_id in node_data.unlocks_towers:
			talents[tower_id] = talents.get(tower_id, 0) + 1
	for tower: TowerData in registry.towers.values():
		var base := not tower.is_hybrid() and tower.requires_nodes.is_empty()
		assert_eq(talents.get(tower.id, 0), 0 if base else 1, "talents for %s" % tower.id)


func test_a_new_player_has_only_the_base_towers() -> void:
	var meta := _meta()
	var config := meta.run_config()
	assert_true(config.locked_towers.has(&"hybrid_plasma"))
	assert_true(config.locked_towers.has(&"triple_cinderstorm"))
	assert_true(config.locked_towers.has(&"storm_skyneedle"))
	assert_false(config.locked_towers.has(&"fire_brazier"))
	assert_has(config.locked_tree_nodes, &"bridge_plasma", "the web shows the Plasma bridge as locked")
	assert_true(meta.is_map_unlocked(&"serpentine"), "maps are no longer talents")
	assert_true(meta.is_difficulty_unlocked(&"nightmare"), "nor are difficulty levels")


func test_taking_a_talent_opens_its_tower_through_the_skill_web() -> void:
	var meta := _meta(100)
	assert_true(meta.allocate(&"talent_hybrid_plasma"))
	var sim := RunSim.new(meta.run_config())
	assert_false(sim.tree.is_locked(&"bridge_plasma"))
	assert_false(sim.is_unlocked(&"hybrid_plasma"), "still needs its bridge in the run")
	sim.tree.points = 100
	assert_true(sim.allocate_node(&"bridge_plasma") or sim.tree.allocate_path(&"bridge_plasma").size() > 0)
	assert_true(sim.is_unlocked(&"hybrid_plasma"))


func test_a_locked_tower_stays_shut_whatever_the_web_says() -> void:
	var sim := RunSim.new(_meta().run_config())
	sim.tree.points = 500
	for id in [&"fire_core", &"storm_core", &"nature_core"]:
		sim.tree.allocate_path(id)
	assert_true(sim.tree.is_allocated(&"storm_core"))
	assert_false(sim.is_unlocked(&"triple_cinderstorm"), "the triple is not a talent yet")
	assert_false(sim.is_unlocked(&"storm_skyneedle"))


func test_campaign_stages_lock_the_same_towers() -> void:
	var meta := _meta(100)
	assert_true(meta.allocate(&"talent_storm_skyneedle"))
	var config := meta.stage_config(&"ember_1")
	assert_false(config.locked_towers.has(&"storm_skyneedle"))
	assert_true(config.locked_towers.has(&"hybrid_plasma"))


func test_any_talent_can_be_bought_from_the_start() -> void:
	var meta := _meta(40)
	assert_true(meta.allocate(&"talent_triple_worldforge"), "a triple at the edge, with nothing else taken")
	assert_false(meta.run_config().locked_towers.has(&"triple_worldforge"))
	assert_true(meta.allocate(&"talent_storm_skyneedle"))
	assert_true(meta.refund(&"talent_triple_worldforge"), "and any talent refunds on its own")
	assert_eq(meta.points(), 40 - 10)
