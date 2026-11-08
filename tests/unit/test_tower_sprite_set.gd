extends GutTest
## Tower art from the Blender pipeline: every sheet in the repository must match its JSON, and
## the lookups that turn an aim angle and a time into a frame must pick the right cell.


func _art_ids() -> Array[String]:
	var ids: Array[String] = []
	for folder in DirAccess.get_directories_at(TowerSpriteSet.ROOT):
		ids.append(folder)
	return ids


func test_every_tower_art_folder_loads_and_matches_a_tower() -> void:
	var registry: Node = autofree(preload("res://scripts/core/data_registry.gd").new())
	registry.reload()
	var ids := _art_ids()
	assert_true(ids.size() > 0, "at least one tower has art")
	for id in ids:
		var art := TowerSpriteSet.load_from(TowerSpriteSet.ROOT.path_join(id).path_join("%s.json" % id))
		assert_not_null(art, "art for %s loads" % id)
		if art == null:
			continue
		assert_eq(String(art.id), id, "the JSON id matches its folder")
		assert_true(registry.towers.has(StringName(id)), "%s is a tower in data/towers" % id)
		assert_eq(Vector2(art.sheet.get_size()),
			Vector2(art.frame_size.x * art.frames, art.frame_size.y * art.directions))
		if art.texture.normal_texture != null:
			assert_eq(art.texture.normal_texture.get_size(), art.sheet.get_size(), "normal map matches the sheet")
		if art.pixel_art:
			assert_eq(art.anchor, art.anchor.round(), "pixel art anchors sit on whole pixels")
			assert_eq(art.display_scale, roundf(art.display_scale), "pixel art scales by whole numbers")
		var footprint := art.draw_rect_at(Vector2.ZERO)
		assert_true(footprint.has_point(Vector2.ZERO), "the cell centre is inside the frame")


func test_towers_without_art_return_null() -> void:
	assert_null(TowerSpriteSet.for_tower(&"no_such_tower"))


func _sample_set(directions: int, frames: int) -> TowerSpriteSet:
	var art := TowerSpriteSet.new()
	art.directions = directions
	art.frames = frames
	art.fps = 10.0
	art.frame_size = Vector2(256, 256)
	art.anchor = Vector2(128, 166)
	art.display_scale = 0.5
	return art


func test_aim_angles_pick_the_nearest_direction() -> void:
	var art := _sample_set(16, 8)
	assert_eq(art.direction_index(0.0), 0, "right")
	assert_eq(art.direction_index(PI / 2.0), 4, "down")
	assert_eq(art.direction_index(PI), 8, "left")
	assert_eq(art.direction_index(-PI / 2.0), 12, "up")
	assert_eq(art.direction_index(TAU - 0.01), 0, "just short of a full turn wraps to right")
	assert_eq(art.direction_index(TAU / 16.0 * 0.4), 0)
	assert_eq(art.direction_index(TAU / 16.0 * 0.6), 1)


func test_animation_loops_and_offsets() -> void:
	var art := _sample_set(16, 8)
	assert_eq(art.frame_index(0.0), 0)
	assert_eq(art.frame_index(0.25), 2)
	assert_eq(art.frame_index(0.8), 0, "eight frames at 10 fps loop every 0.8 s")
	assert_eq(art.frame_index(0.0, 3), 3)
	assert_eq(art.frame_index(0.0, -1), 7)


func test_regions_and_placement() -> void:
	var art := _sample_set(16, 8)
	assert_eq(art.region(4, 2), Rect2(512, 1024, 256, 256))
	assert_eq(art.draw_rect_at(Vector2(100, 100)), Rect2(36, 17, 128, 128))
