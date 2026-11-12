extends GutTest
## Bosses in battle: every boss has its move set drawn (tools/art/pix2d/boss_moves.py), BossDirector
## plays the moves on what the boss does, and every recorded battle line is there to be played.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const GAME_SCENE := preload("res://scenes/game/game.tscn")
const ART := BoardArt.ART

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _bosses() -> Array[StringName]:
	var out: Array[StringName] = []
	for enemy_id: StringName in registry.enemies:
		var data: EnemyData = registry.enemies[enemy_id]
		if data.tags.has(&"boss") and BoardArt.enemy_info(enemy_id).get("drawn", false):
			out.append(enemy_id)
	return out


func test_every_boss_has_its_moves() -> void:
	var bosses := _bosses()
	assert_gt(bosses.size(), 10, "the hand-drawn bosses")
	for boss_id in bosses:
		var meta := BoardArt.enemy_info(boss_id)
		var moves := 2   # walk and death
		for move in BoardArt.BOSS_MOVES:
			assert_true(meta.has(String(move)), "%s has no %s" % [boss_id, move])
			if not meta.has(String(move)):
				continue
			moves += 1
			var spec: Dictionary = meta[String(move)]
			for f in int(spec.get("frames", 0)):
				var path := ART + "enemies/%s_%s_%d" % [boss_id, move, f]
				assert_true(ResourceLoader.exists(path + ".png") and ResourceLoader.exists(path + "_n.png"), path)
		assert_true(moves >= 10, "%s has %d moves" % [boss_id, moves])
	assert_true(int(BoardArt.enemy_info(&"gorrath")["guard"].get("hold", -1)) >= 0, "a guard holds")


func test_every_battle_line_is_recorded() -> void:
	var text := FileAccess.get_file_as_string("res://data/story/boss_lines.json")
	var written: Dictionary = (JSON.parse_string(text) as Dictionary)["bosses"]
	for boss_id: String in written:
		assert_true(registry.enemies.has(StringName(boss_id)), "boss_lines.json: %s is not an enemy" % boss_id)
		for kind: String in (written[boss_id] as Dictionary).get("lines", {}):
			var lines := BossVoice.lines_of(StringName(boss_id), StringName(kind))
			assert_eq(lines.size(), (written[boss_id]["lines"][kind] as Array).size(), "%s %s recorded" % [boss_id, kind])
			for line: Dictionary in lines:
				assert_true(ResourceLoader.exists(BossVoice.VOICE_DIR + String(line["file"])), String(line["file"]))
				assert_gt(float(line["secs"]), 0.2, String(line["file"]))
	assert_true(BossVoice.speaks(&"vael_orrun_unmade"), "a later form speaks")
	assert_false(BossVoice.lines_of(&"hollow_shade", &"taunt").is_empty(), "a shade shares its king's taunts")
	assert_true(BossVoice.lines_of(&"hollow_shade", &"arrive").is_empty(), "but not his arrival")


func test_a_boss_takes_turns_to_speak() -> void:
	var voice: BossVoice = autofree(BossVoice.new())
	add_child(voice)
	assert_gt(voice.say(&"gorrath", &"arrive"), 0.0, "it announces itself")
	assert_eq(voice.say(&"gorrath", &"taunt"), 0.0, "chatter waits while it speaks")
	assert_gt(voice.say(&"gorrath", &"death"), 0.0, "its death cuts in")
	assert_eq(voice.history, ["gorrath/arrive", "gorrath/death"] as Array[String])


## A boss in the real game: it rises when it appears, then reels, guards, casts and strikes when told.
func test_director_plays_boss_moves_on_the_board() -> void:
	Progress.use_memory_profile()
	var game: Game = GAME_SCENE.instantiate()
	add_child_autofree(game)
	await wait_process_frames(2)
	var sim: RunSim = game.sim
	var art: BoardArt = game.board.art
	assert_not_null(art)
	assert_not_null(game.bosses, "the game has a boss director")
	var wave := WaveData.new()
	wave.element = &"earth"
	var group := SpawnGroup.new()
	group.enemy = &"gorrath"
	group.count = 1
	wave.groups = [group] as Array[SpawnGroup]
	var waves := WaveSet.new()
	waves.id = &"boss_test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	sim.config.wave_set = waves
	sim.start_next_wave()
	var boss: SimEnemy = null
	for i in 600:
		sim.step(RunSim.STEP)
		if not sim.enemies.is_empty():
			boss = sim.enemies[0]
			break
	assert_not_null(boss, "the boss came on")
	if boss == null:
		return
	for i in 3:
		sim.step(RunSim.STEP)
		await wait_process_frames(1)
	assert_eq(art.boss_move_of(boss), &"rise", "it rises out of the ground")
	assert_gt(art.play_boss_move(boss, &"guard", true), 0.0)
	for i in 40:
		await wait_process_frames(1)
	assert_eq(art.boss_move_of(boss), &"guard", "a held guard stays up")
	art.release_boss_move(boss, &"guard")
	assert_eq(art.boss_move_of(boss), &"", "and comes down when released")
	game.bosses.act(boss, &"cast", &"bind")
	assert_eq(art.boss_move_of(boss), &"cast")
	boss.health = boss.max_health * 0.45
	sim.step(RunSim.STEP)
	await wait_process_frames(2)
	assert_eq(art.boss_move_of(boss), &"hurt", "it reels as its health falls")
