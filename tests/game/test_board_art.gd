extends GutTest
## The in-game pixel art: every tower, enemy and map in the data has its pictures, the light follows the
## waves, and the real game scene draws a tower with the art.
##
## If a new tower or enemy fails here, add a recipe for it to tools/art/gen_game_art.py and run that script.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const GAME_SCENE := preload("res://scenes/game/game.tscn")
const ART := BoardArt.ART

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _assert_lit(path: String) -> void:
	assert_true(ResourceLoader.exists(path + ".png"), "missing picture " + path + ".png")
	assert_true(ResourceLoader.exists(path + "_n.png"), "missing normal map " + path + "_n.png")


func test_every_tower_has_art() -> void:
	for tower_id: StringName in registry.towers:
		var meta := BoardArt.tower_info(tower_id)
		assert_false(meta.is_empty(), "art.json has no entry for tower %s" % tower_id)
		if meta.is_empty():
			continue
		assert_true(meta.has("anchor") and meta.has("muzzle") and meta.has("light"), "tower %s metadata" % tower_id)
		_assert_lit(ART + "towers/%s" % tower_id)
		assert_true(ResourceLoader.exists(ART + "towers/%s_glow.png" % tower_id), "tower %s glow" % tower_id)
		assert_not_null(BoardArt.tower_picture(tower_id), "shop picture for %s" % tower_id)


func test_every_enemy_has_art() -> void:
	for enemy_id: StringName in registry.enemies:
		var meta := BoardArt.enemy_info(enemy_id)
		assert_false(meta.is_empty(), "art.json has no entry for enemy %s" % enemy_id)
		if meta.is_empty():
			continue
		assert_gt(int(meta.get("frames", 0)), 0, "enemy %s has frames" % enemy_id)
		for f in int(meta["frames"]):
			_assert_lit(ART + "enemies/%s_%d" % [enemy_id, f])
			if meta.get("gear", false):
				_assert_lit(ART + "enemies/%s_gear_%d" % [enemy_id, f])
		assert_gt(BoardArt.enemy_height(enemy_id), 0.0)


func test_every_map_has_ground_art() -> void:
	for map_id: StringName in registry.maps:
		assert_true(BoardArt.has_ground(map_id), "map %s has ground art" % map_id)
		assert_true(ResourceLoader.exists(ART + "ground/%s_n.png" % map_id), "map %s normal map" % map_id)
		assert_true(FileAccess.file_exists(ART + "ground/%s.json" % map_id), "map %s props" % map_id)


func test_every_prop_has_art() -> void:
	for kind: String in BoardArt.info().get("props", {}):
		_assert_lit(ART + "props/" + kind)


func test_sun_sets_as_the_waves_go_on() -> void:
	assert_almost_eq(DayNight.target_for(0, false, 0.0, false), DayNight.DAY, 0.001, "the first wave is at midday")
	var last_wave_end := DayNight.target_for(9, true, DayNight.WAVE_SECONDS, false)
	assert_almost_eq(last_wave_end, DayNight.NIGHT, 0.001, "the tenth wave ends at night")
	assert_almost_eq(DayNight.target_for(10, false, 0.0, false), 1.0 + DayNight.DAY, 0.001, "a new day after ten waves")
	assert_almost_eq(DayNight.target_for(10, false, 0.0, true), DayNight.DAWN, 0.001, "a win ends in a dawn")
	var light := DayNight.new()
	light.set_target(DayNight.DAY)
	light.snap()
	assert_lt(light.night(), 0.05, "daylight")
	light.set_target(DayNight.NIGHT)
	light.snap()
	assert_gt(light.night(), 0.95, "night")
	assert_lt(light.sun_energy(), 0.05, "no sun at night")


func test_light_never_runs_backwards() -> void:
	var light := DayNight.new()
	light.set_target(0.4)
	light.advance(1.0)
	var after_one := light.clock
	assert_gt(after_one, DayNight.DAY)
	assert_lte(after_one, 0.4)
	light.set_target(0.2)
	light.advance(1.0)
	assert_eq(light.clock, after_one, "an earlier target does not turn the clock back")


func test_game_draws_towers_with_the_art() -> void:
	Progress.use_memory_profile()
	var game: Game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	var art: BoardArt = game.board.art
	assert_not_null(art, "the board uses the pixel art")
	var before := _count_sprites(art)
	var tower: SimTower = null
	game.sim.gold = 9999
	game.sim.allocate_node(&"fire_entry")
	for y in game.sim.config.map.grid_size.y:
		for x in game.sim.config.map.grid_size.x:
			if tower == null and game.sim.placement_error(&"fire_brazier", Vector2i(x, y)).is_empty():
				tower = game.sim.place_tower(&"fire_brazier", Vector2i(x, y))
	assert_not_null(tower, "found a free cell")
	await wait_process_frames(2)
	assert_gt(_count_sprites(art), before, "placing a tower adds its sprites")


func _count_sprites(node: Node) -> int:
	var count := 1 if node is Sprite2D else 0
	for child in node.get_children():
		count += _count_sprites(child)
	return count
