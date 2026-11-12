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
		if CitadelArt.draws(registry.enemies[enemy_id]):
			continue
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


## The citadel of the final assault is drawn whole, with its fire, its cracks and its ruin.
func test_citadel_has_art() -> void:
	assert_true(CitadelArt.has_art(), "citadel.json")
	var meta := CitadelArt.read_meta()
	assert_eq((meta.get("gates", []) as Array).size(), 3, "three gates")
	for name in ["citadel", "ruin"]:
		_assert_lit(CitadelArt.DIR + name)
	for f in int(meta.get("frames", 0)):
		assert_true(ResourceLoader.exists(CitadelArt.DIR + "citadel_glow_%d.png" % f), "glow frame %d" % f)
	assert_true(ResourceLoader.exists(CitadelArt.DIR + "citadel_cracks.png"), "cracks")


## Every unit of the counter-attack walks, strikes and dies, and every champion has its hero's sprite.
func test_every_ally_has_art() -> void:
	for ally_id: StringName in registry.allies:
		var data: AllyData = registry.allies[ally_id]
		assert_true(AllyArt.has_art(data), "art for %s" % ally_id)
		if data.is_champion():
			continue
		var info: Dictionary = AllyArt.meta()[String(ally_id)]
		for anim in ["walk", "attack", "death"]:
			assert_true(info["anims"].has(anim), "%s %s" % [ally_id, anim])
			_assert_lit(AllyArt.DIR + "%s_%s" % [ally_id, anim])


## Code-drawn enemies walk in six frames and stand on the bottom row. Hand-drawn ones bring their
## own frame count and a padded frame, so their feet only have to be inside it.
func test_enemies_walk_in_six_frames() -> void:
	for enemy_id: StringName in registry.enemies:
		if CitadelArt.draws(registry.enemies[enemy_id]):
			continue
		var meta := BoardArt.enemy_info(enemy_id)
		if meta.get("drawn", false):
			var frame: Array = meta["size"]
			var feet: Array = meta["anchor"]
			assert_gt(int(meta["frames"]), 1, "enemy %s walk cycle" % enemy_id)
			assert_true(int(feet[0]) < int(frame[0]) and int(feet[1]) < int(frame[1]), "enemy %s feet in its frame" % enemy_id)
			continue
		assert_eq(int(meta.get("frames", 0)), 6, "enemy %s walk cycle" % enemy_id)
		var size: Array = meta.get("size", [0, 0])
		var anchor: Array = meta.get("anchor", [0, 0])
		assert_eq(int(anchor[1]), int(size[1]) - 1, "enemy %s stands on the bottom of its picture" % enemy_id)


func test_shots_are_made_of_one_of_the_towers_elements() -> void:
	for tower_id: StringName in registry.towers:
		var data: TowerData = registry.towers[tower_id]
		var style: StringName = BoardArt.shot_style(data)
		assert_true(data.elements.has(style), "%s fires %s shots" % [tower_id, style])
	var brazier: TowerData = registry.towers[&"fire_brazier"]
	assert_eq(BoardArt.shot_style(brazier), &"fire")
	var steam: TowerData = registry.towers[&"hybrid_steam"]
	assert_eq(BoardArt.shot_style(steam), &"water", "the steam tower's crown is water")
	assert_eq(BoardArt.shot_style(null), &"", "no tower, no style")


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


## Plays through the moments the board marks: a tower levelling up and ascending, shots landing, and
## an enemy under every status at once. The drawing must get through all of it without an error.
func test_board_marks_upgrades_hits_and_statuses() -> void:
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
	for i in SimTower.MAX_LEVEL - 1:
		assert_true(sim.level_up(tower), "level up")
	await wait_process_frames(2)
	assert_true(sim.ascend(tower, tower.data.ascendancies[0].id), "ascend")
	await wait_process_frames(2)
	assert_true(art.has_live_effects(), "ascending sets off a ring")
	assert_true(sim.start_next_wave(), "wave started")
	for i in 900:
		if not sim.enemies.is_empty():
			break
		sim.step(RunSim.STEP)
	assert_false(sim.enemies.is_empty(), "an enemy walked in")
	if sim.enemies.is_empty():
		return
	var enemy: SimEnemy = sim.enemies[0]
	for kind: StringName in [&"burn", &"poison", &"slow", &"stun", &"curse", &"shatter"]:
		var spec := StatusEffectData.new()
		spec.kind = kind
		spec.duration = 3.0
		spec.slow = 0.3 if kind == &"slow" else 0.0
		enemy.apply_status(spec, tower, 1.0)
	assert_true(enemy.has_status(&"stun"), "the enemy is marked")
	# Ten seconds of the wave, drawn now and then: shots fly, land and kill.
	for second in 10:
		await wait_process_frames(2)
		for i in 60:
			sim.step(RunSim.STEP)
	await wait_process_frames(2)
	assert_gt(tower.damage_dealt, 0.0, "the tower fought")


## Every enemy with a power has the frames to show it, and every hand-drawn enemy can die on screen.
func test_powers_and_deaths_have_frames() -> void:
	for enemy_id: StringName in registry.enemies:
		var data: EnemyData = registry.enemies[enemy_id]
		var meta := BoardArt.enemy_info(enemy_id)
		if not data.power.is_empty():
			assert_true(meta.has("power"), "%s has power frames" % enemy_id)
		for anim: String in ["power", "death"]:
			var spec: Dictionary = meta.get(anim, {})
			for f in int(spec.get("frames", 0)):
				_assert_lit(ART + "enemies/%s_%s_%d" % [enemy_id, anim, f])
		if meta.get("drawn", false):
			assert_true(meta.has("death"), "%s has death frames" % enemy_id)


## A power plays its animation and holds a lasting one; a grunt lies in its death frames until it rises;
## a killed enemy leaves a body that plays out its death.
func test_the_board_shows_powers_and_deaths() -> void:
	Progress.use_memory_profile()
	var game: Game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	var art: BoardArt = game.board.art
	var sim: RunSim = game.sim
	var wave := WaveData.new()
	wave.element = &"fire"
	var groups: Array[SpawnGroup] = []
	for id: StringName in [&"grunt", &"splitter", &"mender"]:
		var group := SpawnGroup.new()
		group.enemy = id
		group.count = 1
		group.spawn_interval = 0.1
		groups.append(group)
	wave.groups = groups
	var waves := WaveSet.new()
	waves.id = &"test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	sim.config.wave_set = waves
	sim.start_next_wave()
	for i in 30:
		sim._spawn(RunSim.STEP)
	await wait_process_frames(2)
	var by_id := {}
	for enemy in sim.enemies:
		by_id[enemy.data.id] = enemy
	var splitter: SimEnemy = by_id[&"splitter"]
	splitter.power_timer = 0.0
	sim._damage(splitter, 1.0, null)
	await wait_process_frames(2)
	var stone: BoardArt.EnemyVisual = art._enemies[splitter.id]
	assert_eq(stone.anim, &"power", "it plays its power")
	stone.anim_time = 10.0
	await wait_process_frames(1)
	assert_eq(stone.body.texture, stone.power_frames[stone.power_hold], "and holds it while it is stone")
	var grunt: SimEnemy = by_id[&"grunt"]
	grunt.has_power = true
	sim._damage(grunt, 99999.0, null)
	await wait_process_frames(2)
	var bones: BoardArt.EnemyVisual = art._enemies[grunt.id]
	assert_eq(bones.anim, &"fall")
	assert_true(bones.death_frames.has(bones.body.texture), "it lies in its death frames")
	var mender: SimEnemy = by_id[&"mender"]
	sim._damage(mender, 99999.0, null)
	await wait_process_frames(2)
	assert_eq(art._corpses.size(), 1, "the dead mender leaves a body")
