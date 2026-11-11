extends GutTest
## The big meta tree on the Talents screen: it opens at normal zoom on the Origin, pans by dragging
## without taking nodes, zooms around the cursor in crisp pixel-art steps, and shows pick-one choices.

const META_TREE_SCENE := preload("res://scenes/meta/meta_tree.tscn")


func _use_profile(points_earned: int, nodes: Array[StringName] = []) -> void:
	var profile := PlayerProfile.new()
	profile.meta_points_earned = points_earned
	profile.meta_nodes = nodes
	Progress.use_memory_profile(profile)


func _open() -> Control:
	var screen: Control = META_TREE_SCENE.instantiate()
	add_child_autofree(screen)
	await wait_process_frames(2)
	return screen


func _mouse(at: Vector2, button: MouseButton, pressed: bool) -> void:
	var event := InputEventMouseButton.new()
	event.button_index = button
	event.pressed = pressed
	event.position = at
	get_tree().root.push_input(event, true)


func _move(to: Vector2, relative: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = to
	motion.relative = relative
	get_tree().root.push_input(motion, true)


func test_the_tree_is_ten_times_the_old_one() -> void:
	var graph: TreeGraph = DataRegistry.meta_tree()
	assert_gt(graph.size(), 160, "about ten times the first meta tree's 16 nodes")
	var total := 0
	for id in graph.ids():
		total += graph.node(id).cost
	assert_gt(total, 700, "costs far more than a first campaign pass pays in its opening lands")


func test_it_opens_on_the_origin_at_normal_zoom() -> void:
	_use_profile(0)
	var screen = await _open()
	var web: SkillWebView = screen.web
	assert_true(web.navigable)
	assert_almost_eq(web.zoom(), 1.0, 0.001)
	var origin := web.screen_position(&"meta_start")
	assert_true(web.get_rect().has_point(origin))
	assert_gt(origin.y, SkillWebView.HEADER_BAND, "the Origin is below the title band")


func test_dragging_pans_without_taking_a_node() -> void:
	_use_profile(10)
	var screen = await _open()
	var web: SkillWebView = screen.web
	var at := web.screen_position(&"command_gold")
	_move(at, Vector2.ZERO)
	_mouse(at, MOUSE_BUTTON_LEFT, true)
	_move(at + Vector2(-120, 40), Vector2(-120, 40))
	_mouse(at + Vector2(-120, 40), MOUSE_BUTTON_LEFT, false)
	assert_false(Progress.meta.tree.is_allocated(&"command_gold"), "a drag is not a click")
	assert_almost_eq(web.screen_position(&"command_gold").x, at.x - 120.0, 0.5)
	assert_almost_eq(web.screen_position(&"command_gold").y, at.y + 40.0, 0.5)


func test_the_wheel_zooms_around_the_cursor_in_whole_pixel_steps() -> void:
	_use_profile(0)
	var screen = await _open()
	var web: SkillWebView = screen.web
	var pivot := web.screen_position(&"command_gold")
	for i in 6:
		_mouse(pivot, MOUSE_BUTTON_WHEEL_DOWN, true)
	assert_lt(web.zoom(), 0.8)
	assert_eq(web._art, 1.0, "zoomed out, one art pixel per screen pixel")
	assert_almost_eq(web.screen_position(&"command_gold").distance_to(pivot), 0.0, 1.0, "the node under the cursor stays put")
	web.show_whole_tree()
	var view := web.get_rect()
	for id: StringName in [&"fire_pyre", &"water_glacial_heart", &"earth_fault_line", &"storm_ball_lightning"]:
		assert_true(view.has_point(web.screen_position(id)), "%s on screen when the whole tree shows" % id)
	for i in 20:
		_mouse(pivot, MOUSE_BUTTON_WHEEL_UP, true)
	assert_almost_eq(web.zoom(), SkillWebView.ZOOM_MAX, 0.001)
	assert_eq(web._art, 3.0)


func test_a_pick_one_choice_closes_its_partner() -> void:
	var path: Array[StringName] = [&"arsenal_edge", &"arsenal_drill", &"arsenal_thornstorm", &"arsenal_piercer"]
	_use_profile(60, path)
	var screen = await _open()
	assert_true(Progress.allocate_meta(&"arsenal_glass_cannon"))
	assert_true(Progress.meta.tree.is_excluded(&"arsenal_siegecraft"))
	assert_false(Progress.allocate_meta(&"arsenal_siegecraft"))
	var status: String = screen.web._status(Progress.meta.tree.graph.node(&"arsenal_siegecraft"), [] as Array[StringName])
	assert_string_contains(status, "Glass Cannon")
	assert_true(Progress.refund_meta(&"arsenal_glass_cannon"))
	assert_true(Progress.allocate_meta(&"arsenal_siegecraft"))
