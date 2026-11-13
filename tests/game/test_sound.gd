extends GutTest
## The sound effects: every tower, enemy, boss and skill in data/ has its sounds, every file loads,
## and a run played by the bot makes the sounds it should.

const TEST_ROAD := preload("res://tests/support/test_road.tres")

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const STEP := RunSim.STEP
const BOSS_PARTS: Array[String] = ["reveal", "step", "voice", "enrage", "death"]

var registry: Node
var sfx: SoundPlayer


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	# The small 24 x 15 road these tests were written against (the real maps are bigger and curved).
	registry.maps[&"test_road"] = TEST_ROAD
	sfx = SoundPlayer.instance
	assert_not_null(sfx, "the Sfx autoload runs")


func test_every_file_in_the_catalogue_loads() -> void:
	assert_gt(sfx.sounds.size(), 150)
	var files := 0
	for sound: StringName in sfx.sounds:
		var paths := sfx.files_of(sound)
		assert_gt(paths.size(), 0, "%s has files" % sound)
		for path in paths:
			assert_true(ResourceLoader.exists(path), "%s exists" % path)
			assert_true(load(path) is AudioStream, "%s is a sound" % path)
			files += 1
	gut.p("%d sounds in %d files" % [sfx.sounds.size(), files])


func test_the_buses_exist() -> void:
	for bus: StringName in [&"Music", &"Sfx", &"Ui", &"Voice"]:
		assert_gte(AudioServer.get_bus_index(bus), 0, "bus %s" % bus)
	for sound: StringName in sfx.sounds:
		var bus := StringName(sfx.sounds[sound].get("bus", ""))
		assert_gte(AudioServer.get_bus_index(bus), 0, "%s plays on a real bus" % sound)


func test_every_tower_has_an_attack_and_every_element_a_build_sound() -> void:
	for tower_id: StringName in registry.towers:
		assert_true(sfx.has_sound(StringName("tower_" + tower_id)), "tower_%s (run tools/sfx/build.py)" % tower_id)
		var data: TowerData = registry.towers[tower_id]
		for element in data.elements:
			assert_true(sfx.has_sound(StringName("impact_" + element)), "impact_%s" % element)
			assert_true(sfx.has_sound(StringName("tower_place_" + element)), "tower_place_%s" % element)
			for spec: StatusEffectData in data.status_effects:
				assert_true(sfx.has_sound(StringName("status_" + GameAudio._status_word(spec.kind))), "status sound for %s" % spec.kind)


func test_every_enemy_has_a_death_and_every_boss_a_full_set() -> void:
	for enemy_id: StringName in registry.enemies:
		var data: EnemyData = registry.enemies[enemy_id]
		var boss := GameAudio.boss_set_of(data)
		if boss.is_empty():
			assert_false(data.tags.has(&"boss") and not GameAudio.MINOR_BOSSES.has(enemy_id),
				"boss %s has a sound set" % enemy_id)
			assert_true(sfx.has_sound(GameAudio.death_sound_of(data)), "death sound of %s" % enemy_id)
			continue
		for part in BOSS_PARTS:
			assert_true(sfx.has_sound(StringName("boss_%s_%s" % [boss, part])), "boss_%s_%s" % [boss, part])


func test_every_skill_has_a_sound() -> void:
	for skill_id: StringName in registry.skills:
		assert_true(sfx.has_sound(StringName("skill_" + skill_id)), "skill_%s" % skill_id)


func test_a_sound_can_play_and_is_rate_limited() -> void:
	assert_true(sfx.play(&"ui_click"))
	# ui_click waits 30 ms between starts.
	assert_false(sfx.play(&"ui_click"))
	assert_false(sfx.play(&"no_such_sound"))
	assert_true(sfx.play(&"impact_fire", Vector2(400, 300)))
	assert_eq(sfx.history.back(), &"impact_fire")
	sfx.stop()


func test_a_bot_run_makes_the_sounds_of_battle() -> void:
	var heard: Dictionary[StringName, int] = {}
	var count := func(sound: StringName) -> void: heard[sound] = heard.get(sound, 0) + 1
	sfx.played.connect(count)
	var sim := RunSim.new(RunConfig.from_registry(registry, &"test_road"))
	var audio := GameAudio.new()
	add_child_autofree(audio)
	audio.setup(sim, Vector2(24, 96))
	var bot := AutoPlayer.new(sim, AutoPlayer.DEFAULT_NODES, AutoPlayer.DEFAULT_TOWERS)
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 1800.0 and sim.wave_index < 4:
		bot.act()
		sim.step(STEP)
		audio._process(STEP)
		elapsed += STEP
	sfx.played.disconnect(count)
	sfx.stop()
	var names := heard.keys()
	gut.p("Heard: %s" % ", ".join(names.map(func(n: StringName) -> String: return "%s x%d" % [n, heard[n]])))
	assert_true(heard.has(&"wave_start"), "a wave starts with a horn")
	assert_true(heard.has(&"wave_cleared"), "a cleared wave is cheered")
	assert_true(names.any(func(n: StringName) -> bool: return str(n).begins_with("tower_place_")), "building is heard")
	assert_true(names.any(func(n: StringName) -> bool: return str(n).begins_with("tower_") and not str(n).begins_with("tower_place")), "towers are heard attacking")
	assert_true(names.any(func(n: StringName) -> bool: return str(n).begins_with("impact_") or str(n).begins_with("explosion_")), "hits are heard")
	assert_true(names.any(func(n: StringName) -> bool: return str(n).begins_with("death_")), "enemies are heard dying")
	assert_true(heard.has(&"node_take"), "taking skill web nodes is heard")


func test_a_boss_is_revealed_once_and_heard_walking_and_dying() -> void:
	var heard: Array[StringName] = []
	var listen := func(sound: StringName) -> void: heard.append(sound)
	sfx.played.connect(listen)
	var sim := RunSim.new(RunConfig.from_registry(registry, &"test_road"))
	var audio := GameAudio.new()
	add_child_autofree(audio)
	audio.setup(sim, Vector2.ZERO)
	assert_true(sim.start_next_wave())
	var data: EnemyData = registry.enemies[&"mountain_titan"]
	var boss := sim._make_enemy(data, 1.0, 0, -1, 0.0)
	sim.enemies.append(boss)
	for i in 600:
		sim.time_in_wave += STEP
		boss.progress += boss.speed() * STEP
		audio._process(STEP)
	sim._damage(boss, boss.health * 0.7, null)
	audio._process(STEP)
	sim.time_in_wave += STEP
	audio._process(STEP)
	sim._damage(boss, boss.health + 1.0, null)
	sfx.played.disconnect(listen)
	sfx.stop()
	gut.p("Heard: %s" % ", ".join(heard))
	assert_eq(heard.count(&"boss_earth_reveal"), 1, "revealed once")
	assert_true(heard.has(&"boss_earth_step"), "footsteps")
	# Its words are recorded lines played by BossVoice (tests/game/test_boss_moves.gd), not the old chatter.
	assert_true(BossVoice.speaks(&"mountain_titan"), "it has battle lines")
	assert_false(heard.has(&"boss_earth_voice"), "so the synthetic voice stays quiet")
	assert_true(heard.has(&"boss_earth_enrage"), "it roars when badly wounded")
	assert_true(heard.has(&"boss_earth_death"), "its death")


func test_sounds_the_battle_repeats_stay_quiet() -> void:
	for sound: StringName in [&"impact_fire", &"impact_void", &"hit_armour", &"status_burn", &"coin"]:
		var level: float = sfx.sounds[sound].get("volume_db", 0.0) + GameAudio.repeat_db(sound)
		assert_lte(level, -18.0, "%s is a quiet bed even with every slider at full" % sound)
	assert_lt(GameAudio.repeat_db(&"tower_fire_brazier"), 0.0, "tower shots are pulled down")
	assert_lt(GameAudio.repeat_db(&"death_grunt"), 0.0, "ordinary deaths are pulled down")
	for sound: StringName in [&"tower_level_up", &"tower_place_fire", &"boss_fire_death", &"victory", &"explosion_large", &"skill_meteor"]:
		assert_eq(GameAudio.repeat_db(sound), 0.0, "%s keeps its full level" % sound)
	assert_lte(GameAudio.HITS_PER_SECOND, 6.0)


func test_back_buttons_make_the_back_sound() -> void:
	var back := MenuItemButton.new("Back", "Esc")
	add_child_autofree(back)
	await get_tree().process_frame
	back.pressed.emit()
	assert_eq(sfx.history.back(), &"ui_back")
	var other := MenuItemButton.new("Play", "Enter")
	add_child_autofree(other)
	await get_tree().process_frame
	await wait_seconds(0.05)
	other.pressed.emit()
	assert_eq(sfx.history.back(), &"ui_click")


func test_the_credits_play_the_trailer_score() -> void:
	for path: String in CreditsMusic.FILES:
		assert_true(ResourceLoader.exists(path), "%s exists" % path)
	var music := CreditsMusic.new()
	add_child_autofree(music)
	music.set_open(true)
	assert_eq(MenuMusic.held, AudioSettings.menu_music_on(), "the title music steps aside")
	music.set_open(false)
	await wait_process_frames(2)
	assert_false(MenuMusic.held, "and comes back when the page closes")
