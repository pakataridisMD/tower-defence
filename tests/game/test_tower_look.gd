extends GutTest
## Towers change with every upgrade and never stand still: each has a sheet with a look per level and
## per ascendancy, an idle loop and an attack, and the board plays them.
##
## If a new tower fails here, run `python3 tools/art/pix2d/tower_anim.py <tower id>` after drawing it in
## tools/art/pix2d/towers*.py, then `godot --headless --import`.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const GAME_SCENE := preload("res://scenes/game/game.tscn")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func test_every_tower_has_a_look_per_upgrade_and_an_animation() -> void:
	for tower_id: StringName in registry.towers:
		var data: TowerData = registry.towers[tower_id]
		var anim: Dictionary = TowerLook.sheet_info(tower_id)
		assert_true(TowerLook.has_sheet(anim), "tower %s has an animation sheet" % tower_id)
		if not TowerLook.has_sheet(anim):
			continue
		var stages: Array = anim["stages"]
		assert_eq(stages.size(), SimTower.MAX_LEVEL + data.ascendancies.size(), "%s: a look per level and ascendancy" % tower_id)
		assert_gte(int(anim["idle"]), 4, "%s idles" % tower_id)
		assert_gte(int(anim["attack"]), 4, "%s attacks" % tower_id)
		var path := BoardArt.ART + String(anim["sheet"])
		var texture: Texture2D = load(path + ".png")
		var cell: Array = anim["cell"]
		assert_eq(texture.get_size(), Vector2(float(cell[0]) * TowerLook.columns(anim), float(cell[1]) * stages.size()),
				"%s sheet size" % tower_id)
		assert_true(ResourceLoader.exists(path + "_n.png"), "%s normal map" % tower_id)
		assert_true(ResourceLoader.exists(path + "_glow.png"), "%s glow" % tower_id)


## Each level and each ascendancy looks different from the one before it.
func test_every_look_is_different() -> void:
	var anim: Dictionary = TowerLook.sheet_info(&"fire_brazier")
	var image: Image = (load(BoardArt.ART + String(anim["sheet"]) + ".png") as Texture2D).get_image()
	var cell: Array = anim["cell"]
	var rows: Array[Image] = []
	for stage in (anim["stages"] as Array).size():
		rows.append(image.get_region(Rect2i(0, stage * int(cell[1]), int(cell[0]), int(cell[1]))))
	for a in rows.size():
		for b in range(a + 1, rows.size()):
			assert_ne(rows[a].get_data(), rows[b].get_data(), "looks %d and %d differ" % [a, b])


func test_the_look_follows_level_and_ascendancy() -> void:
	var no_elements: Array[int] = []
	var tower := SimTower.new(1, registry.towers[&"fire_brazier"], Vector2i.ZERO, Vector2.ZERO, 0, no_elements)
	assert_eq(TowerLook.stage_index(tower), 0)
	tower.level = 2
	assert_eq(TowerLook.stage_index(tower), 1)
	tower.level = 3
	assert_eq(TowerLook.stage_index(tower), 2)
	tower.ascendancy = tower.data.ascendancies[0]
	assert_eq(TowerLook.stage_index(tower), 3, "first ascendancy")
	tower.ascendancy = tower.data.ascendancies[1]
	assert_eq(TowerLook.stage_index(tower), 4, "second ascendancy")


func test_frames_loop_the_idle_and_play_the_attack_once() -> void:
	var anim := {"idle": 8, "idle_fps": 8, "attack": 6, "attack_fps": 18, "attack_peak": 2}
	assert_eq(TowerLook.frame(anim, 0, 0.0, -1.0), 0)
	assert_eq(TowerLook.frame(anim, 0, 1.0 / 8.0 * 3.5, -1.0), 3)
	assert_eq(TowerLook.frame(anim, 0, 1.01, -1.0), 0, "the idle loops")
	assert_eq(TowerLook.frame(anim, 2, 0.0, -1.0), 28, "the row of the third look")
	assert_eq(TowerLook.frame(anim, 0, 0.0, 0.0), 8, "the attack starts after the idle frames")
	assert_eq(TowerLook.frame(anim, 1, 0.0, 10.0), 14 + 13, "and holds its last frame")
	assert_lt(TowerLook.recoil(anim, 0.05), 0.0, "it gathers first")
	assert_gt(TowerLook.recoil(anim, 0.15), 0.5, "then kicks on the release")
	assert_eq(TowerLook.recoil(anim, -1.0), 0.0)


## In the game: the tower idles, plays its attack when it fires, and changes its look as it is upgraded.
func test_the_board_animates_and_upgrades_a_tower() -> void:
	Progress.use_memory_profile()
	var game: Game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	var art: BoardArt = game.board.art
	var sim: RunSim = game.sim
	sim.gold = 99999
	sim.allocate_node(&"fire_entry")
	var tower: SimTower = null
	for cell in sim.path_cell_list():
		for step: Vector2i in [Vector2i.UP, Vector2i.DOWN, Vector2i.LEFT, Vector2i.RIGHT]:
			if tower == null and sim.placement_error(&"fire_brazier", cell + step).is_empty():
				tower = sim.place_tower(&"fire_brazier", cell + step)
	assert_not_null(tower, "found a cell beside the road")
	if tower == null:
		return
	await wait_process_frames(2)
	var visual: BoardArt.TowerVisual = art._towers[tower.id]
	assert_false(visual.anim.is_empty(), "the tower plays its sheet")
	var columns := TowerLook.columns(visual.anim)
	var seen := {}
	for i in 30:
		seen[visual.body.frame] = true
		await wait_physics_frames(1)
	assert_gt(seen.size(), 1, "it idles")
	sim.tower_attacked.emit(tower, null)
	await wait_process_frames(1)
	assert_gte(visual.body.frame % columns, int(visual.anim["idle"]), "it plays its attack when it fires")
	assert_eq(visual.glow.frame, visual.body.frame, "its glow keeps step")
	sim.level_up(tower)
	await wait_process_frames(1)
	assert_eq(visual.body.frame / columns, 1, "level 2 look")
	sim.level_up(tower)
	await wait_process_frames(1)
	assert_eq(visual.body.frame / columns, 2, "level 3 look")
	var muzzle_before := visual.muzzle
	assert_true(sim.ascend(tower, tower.data.ascendancies[1].id), "ascend")
	await wait_process_frames(1)
	assert_eq(visual.body.frame / columns, 4, "the second ascendancy's look")
	assert_lt(visual.muzzle.y, muzzle_before.y, "the dais lifts its crown")
	assert_eq(visual.silhouette.region.position.y, 4.0 * float(visual.anim["cell"][1]), "its shadow follows")
