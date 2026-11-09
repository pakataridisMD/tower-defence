extends GutTest
## The skill trees' pixel art: every node, region and stat has a picture, and the tree screen draws
## with it. If a new node or stat fails here, add an icon to tools/art/gen_tree_art.py or a mapping
## to scripts/game/tree_art.gd.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _icon_exists(icon_name: StringName) -> bool:
	return ResourceLoader.exists(TreeArt.ART + "icon_%s.png" % icon_name)


func test_every_style_has_its_pictures() -> void:
	for style: StringName in TreeArt.SIZES:
		for part in ["frame_", "gem_", "shine_", "halo_"]:
			assert_not_null(TreeArt.texture(part + style), "%s%s" % [part, style])
		assert_not_null(TreeArt.texture("gem_%s_left" % style), "split gem for %s" % style)
		assert_not_null(TreeArt.texture("gem_%s_right" % style), "split gem for %s" % style)
		assert_eq(int(TreeArt.texture("frame_" + style).get_width()), int(TreeArt.SIZES[style]), "%s size" % style)
	for name in ["glow", "aura", "sparkle", "panel", "backdrop"]:
		assert_not_null(TreeArt.texture(name), name)


func test_every_node_in_both_trees_has_an_icon() -> void:
	for graph: TreeGraph in [registry.in_run_tree(), registry.meta_tree()]:
		for id in graph.ids():
			var data := graph.node(id)
			var icon_name := TreeArt.node_icon(data)
			assert_true(_icon_exists(icon_name), "node %s wants icon '%s'" % [id, icon_name])


func test_tower_nodes_show_the_tower() -> void:
	for tower_id: StringName in registry.towers:
		var picture := TreeArt.portrait(tower_id)
		assert_not_null(picture, "portrait for %s" % tower_id)
		if picture != null:
			var window: int = TreeArt.SIZES[&"portrait"] - 2 * TreeArt.RINGS[&"portrait"]
			assert_eq(picture.get_size(), Vector2(window, window))
	var entry := (registry.in_run_tree() as TreeGraph).node(&"fire_entry")
	assert_eq(TreeArt.style(entry), &"portrait")


func test_every_region_has_an_emblem() -> void:
	var regions: Array[StringName] = []
	regions.append_array(registry.elements.keys())
	regions.append_array(MetaProgress.BRANCH_NAMES.keys())
	for region in regions:
		assert_true(TreeArt.EMBLEMS.has(region), "emblem listed for %s" % region)
		assert_true(_icon_exists(TreeArt.EMBLEMS.get(region, &"")), "emblem picture for %s" % region)


func test_stat_icons_exist_and_match_by_name() -> void:
	for icon_name: StringName in TreeArt.STAT_ICONS.values() + TreeArt.STAT_WORDS.values():
		assert_true(_icon_exists(icon_name), "icon %s" % icon_name)
	assert_eq(TreeArt.stat_icon(&"damage"), &"sword")
	assert_eq(TreeArt.stat_icon(&"burn_duration"), &"flame")
	assert_eq(TreeArt.stat_icon(&"slow_strength"), &"snowflake")
	assert_eq(TreeArt.stat_icon(&"aura_damage"), &"aura", "a word inside the name beats 'damage'")
	assert_eq(TreeArt.stat_icon(&"something_new"), &"")


func test_tree_screen_draws_and_bursts_when_a_node_is_taken() -> void:
	var view: SkillWebView = SkillWebView.new()
	add_child_autofree(view)
	var state := TreeState.new(registry.in_run_tree(), 5)
	view.show_tree(state, SkillWebView.element_regions(registry.elements))
	await wait_process_frames(2)
	assert_true(state.allocate(&"fire_entry"))
	await wait_process_frames(2)
	assert_eq(view._bursts.size(), 1, "taking a node sets off a burst")
	await wait_seconds(SkillWebView.BURST_SECONDS + 0.1)
	assert_eq(view._bursts.size(), 0, "the burst fades")
