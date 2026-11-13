extends GutTest
## The two trees are linked. Talents (the meta tree) keeps its lasting stat bonuses and carries the
## Forge talents, one for every tower past the six base towers. A dual or triple can be built in a
## run only when its Forge talent is taken (which opens its node in the run's skill tree) and that
## node is taken in the run.

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


func test_every_tower_but_the_base_towers_has_exactly_one_forge_talent() -> void:
	var talents: Dictionary[StringName, int] = {}
	for node_data: TreeNodeData in registry.meta_tree_nodes:
		if node_data.unlocks_towers.is_empty():
			continue
		assert_eq(node_data.region, &"forge", "%s is a Forge talent" % node_data.id)
		assert_eq(node_data.unlocks_towers.size(), 1, "%s unlocks one tower" % node_data.id)
		assert_true(node_data.modifiers.is_empty(), "%s gives no stat bonus" % node_data.id)
		for tower_id in node_data.unlocks_towers:
			talents[tower_id] = talents.get(tower_id, 0) + 1
	for tower: TowerData in registry.towers.values():
		var base := not tower.is_hybrid() and tower.requires_nodes.is_empty()
		assert_eq(talents.get(tower.id, 0), 0 if base else 1, "talents for %s" % tower.id)


func test_talents_still_give_lasting_bonuses() -> void:
	var with_bonus := 0
	for node_data: TreeNodeData in registry.meta_tree_nodes:
		if not node_data.modifiers.is_empty():
			with_bonus += 1
	assert_true(with_bonus >= 120, "the wheel of stat talents is back (%d give a bonus)" % with_bonus)


func test_a_new_player_has_only_the_base_towers() -> void:
	var config := _meta().run_config()
	assert_true(config.locked_towers.has(&"hybrid_plasma"))
	assert_true(config.locked_towers.has(&"triple_cinderstorm"))
	assert_true(config.locked_towers.has(&"storm_skyneedle"))
	assert_false(config.locked_towers.has(&"fire_brazier"))


func test_a_forge_talent_hangs_on_a_path_through_talents() -> void:
	var meta := _meta(200)
	assert_false(meta.allocate(&"talent_hybrid_plasma"), "not next to the start")
	var cost := meta.tree.path_cost(&"talent_hybrid_plasma")
	assert_true(cost > registry.meta_tree().node(&"talent_hybrid_plasma").cost, "the way to it costs points too")
	assert_true(meta.allocate_path(&"talent_hybrid_plasma"))
	assert_eq(meta.points(), 200 - cost)
	assert_false(meta.run_config().locked_towers.has(&"hybrid_plasma"))
	# Triples sit further out than the duals they grow from.
	assert_true(meta.tree.path_cost(&"talent_triple_cinderstorm") > 0)
	var fresh := _meta(200)
	assert_true(fresh.tree.path_cost(&"talent_triple_cinderstorm") > cost, "a triple is a longer way than a dual")


func test_a_forge_talent_opens_the_towers_node_in_the_skill_tree() -> void:
	var meta := _meta(200)
	assert_has(meta.run_config().locked_tree_nodes, &"tower_hybrid_plasma", "locked without the talent")
	assert_true(meta.allocate_path(&"talent_hybrid_plasma"))
	var config := meta.run_config()
	assert_does_not_have(config.locked_tree_nodes, &"tower_hybrid_plasma")
	assert_has(config.locked_tree_nodes, &"tower_hybrid_soulflame", "the other duals stay locked")
	var sim := RunSim.new(config)
	assert_false(sim.is_unlocked(&"hybrid_plasma"), "its node still has to be taken in the run")
	sim.tree.points = 100
	assert_true(sim.allocate_node(&"tower_hybrid_plasma"))
	assert_true(sim.is_unlocked(&"hybrid_plasma"))


func test_a_locked_tower_stays_shut_whatever_the_skill_tree_says() -> void:
	var sim := RunSim.new(_meta().run_config())
	sim.tree.points = 500
	for id: StringName in [&"fire_core", &"storm_core", &"nature_core"]:
		assert_true(sim.allocate_node(id))
	assert_true(sim.tree.is_locked(&"tower_triple_cinderstorm"))
	assert_false(sim.allocate_node(&"tower_triple_cinderstorm"), "no Forge talent")
	assert_false(sim.allocate_node(&"tower_hybrid_plasma"))
	assert_false(sim.is_unlocked(&"triple_cinderstorm"))
	assert_false(sim.is_unlocked(&"storm_skyneedle"), "a long-range tower needs its talent too")
	assert_true(sim.is_unlocked(&"fire_brazier"), "base towers need no talent")


func test_campaign_stages_lock_the_same_towers() -> void:
	var meta := _meta(200)
	assert_true(meta.allocate_path(&"talent_storm_skyneedle"))
	var config := meta.stage_config(&"ember_1")
	assert_false(config.locked_towers.has(&"storm_skyneedle"))
	assert_true(config.locked_towers.has(&"hybrid_plasma"))
