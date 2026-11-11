extends GutTest
## The story side of the campaign: boss tricks (ward, silence, blink, enrage, escape), the assault on
## the citadel (buildings, phases, build limit, the overlord), the story files and when their
## cinematics are due, saving what was seen, and the cinematic player.

const TEST_ROAD := preload("res://tests/support/test_road.tres")

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	# The small 24 x 15 road these tests were written against (the real maps are bigger and curved).
	registry.maps[&"test_road"] = TEST_ROAD


func _sim(groups: Array[SpawnGroup], map_id: StringName = &"test_road") -> RunSim:
	var config := RunConfig.from_registry(registry, map_id)
	var wave := WaveData.new()
	wave.element = &"fire"
	wave.groups = groups
	var waves := WaveSet.new()
	waves.id = &"test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	config.wave_set = waves
	var sim := RunSim.new(config)
	sim.tree.points = 20
	sim.gold = 5000
	return sim


func _group(enemy: StringName, count: int = 1) -> SpawnGroup:
	var group := SpawnGroup.new()
	group.enemy = enemy
	group.count = count
	group.spawn_interval = 0.1
	return group


func _spawn_all(sim: RunSim) -> void:
	sim.start_next_wave()
	for i in 120:
		sim._spawn(RunSim.STEP)


# --- Boss tricks -----------------------------------------------------------------

func test_a_ward_shields_nearby_allies_but_not_the_caster() -> void:
	var sim := _sim([_group(&"saltmother"), _group(&"grunt")])
	_spawn_all(sim)
	var boss := sim.enemies[0]
	var grunt := sim.enemies[1]
	grunt.position = boss.position + Vector2(20, 0)
	sim._tick_boss_tricks(RunSim.STEP)
	assert_gt(grunt.ward, 0.0, "the grunt is shielded")
	assert_eq(boss.ward, 0.0, "the caster is not")
	var before := grunt.health
	sim._damage(grunt, 10.0, null)
	assert_almost_eq(before - grunt.health, 10.0 * (1.0 - grunt.ward), 0.01)


func test_silence_stops_towers_in_reach_from_shooting() -> void:
	var sim := _sim([_group(&"vholt")])
	_spawn_all(sim)
	var boss := sim.enemies[0]
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", Vector2i(2, 3))
	assert_not_null(tower)
	tower.position = boss.position + Vector2(30, 0)
	watch_signals(sim)
	boss.silence_timer = 0.0
	sim._tick_boss_tricks(RunSim.STEP)
	assert_gt(tower.silenced, 0.0)
	assert_signal_emitted(sim, "towers_silenced")


func test_a_blink_jumps_forward_but_never_out_of_the_map() -> void:
	var sim := _sim([_group(&"pale_vesper")])
	_spawn_all(sim)
	var boss := sim.enemies[0]
	var start := boss.progress
	boss.blink_timer = 0.0
	sim._tick_boss_tricks(RunSim.STEP)
	assert_almost_eq(boss.progress, start + boss.data.blink_distance, 0.01)
	boss.progress = sim.lane_lengths[boss.lane] - 70.0
	boss.blink_timer = 0.0
	sim._tick_boss_tricks(RunSim.STEP)
	assert_lt(boss.progress, sim.lane_lengths[boss.lane], "the blink stops short of the exit")


func test_enrage_makes_a_beaten_boss_faster() -> void:
	var sim := _sim([_group(&"gorrath")])
	_spawn_all(sim)
	var boss := sim.enemies[0]
	var calm := boss.speed()
	boss.health = boss.max_health * (boss.data.enrage_below - 0.05)
	sim._tick_boss_tricks(RunSim.STEP)
	assert_true(boss.enraged)
	assert_gt(boss.speed(), calm)


func test_the_regent_escapes_instead_of_dying() -> void:
	var sim := _sim([_group(&"ashen_regent")])
	_spawn_all(sim)
	var boss := sim.enemies[0]
	watch_signals(sim)
	boss.health = boss.max_health * (boss.data.escape_below - 0.05)
	sim._tick_boss_tricks(RunSim.STEP)
	assert_false(boss.alive)
	assert_true(boss.escaped)
	assert_signal_emitted(sim, "enemy_escaped")


func test_every_herald_and_the_regent_lead_a_stage() -> void:
	var leaders := {}
	for waves: WaveSet in registry.wave_sets.values():
		for wave in waves.waves:
			for group in wave.groups:
				leaders[group.enemy] = true
	for id in [&"saltmother", &"gorrath", &"pale_vesper", &"ashwick", &"vholt", &"mother_briar", &"ashen_regent"]:
		assert_true(leaders.has(id), "%s leads a wave somewhere" % id)


# --- The assault -----------------------------------------------------------------

func _assault() -> RunSim:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	return RunSim.new(meta.stage_config(&"assault_1"))


func test_the_assault_has_three_phases_of_buildings() -> void:
	var sim := _assault()
	assert_true(sim.is_assault())
	assert_eq(sim.total_phases(), 3)
	assert_eq(sim.structure_phase, 1)
	assert_eq(sim.structures_left(1).size(), 1)
	for structure in sim.structures:
		assert_eq(structure.speed(), 0.0, "buildings do not walk")
		assert_eq(sim.is_vulnerable(structure), structure.phase == 1)


func test_towers_cannot_be_built_past_the_front() -> void:
	var sim := _assault()
	var limit := sim.build_limit()
	assert_gt(limit, 0)
	var tower_id: StringName = sim.config.towers.keys()[0]
	var past := Vector2i(limit + 1, 0)
	assert_ne(sim.placement_error(tower_id, past), "", "a cell past the front is refused")


func test_a_fallen_gate_closes_roads_releases_heralds_and_moves_the_front() -> void:
	var sim := _assault()
	var limit := sim.build_limit()
	var gate := sim.structures_left(1)[0]
	watch_signals(sim)
	sim._damage(gate, gate.health + 1.0, null)
	assert_false(gate.alive)
	assert_eq(sim.structure_phase, 2)
	for lane in gate.closes_lanes:
		assert_true(sim.is_lane_closed(lane))
	assert_eq(sim._arrivals.size(), gate.releases.size(), "the heralds come out")
	assert_gt(sim.build_limit(), limit, "the front moves forward")
	assert_signal_emitted(sim, "structure_destroyed")
	assert_signal_emitted(sim, "phase_changed")
	assert_false(sim.is_over())


func test_the_run_is_won_only_when_the_overlord_falls_too() -> void:
	var sim := _assault()
	sim.start_next_wave()
	for phase in range(1, sim.total_phases() + 1):
		for structure in sim.structures_left(phase):
			sim._damage(structure, structure.health + 1.0, null)
	assert_true(sim.citadel_fallen)
	var overlord: SimEnemy = null
	for enemy in sim._arrivals:
		if enemy.data.tags.has(&"overlord"):
			overlord = enemy
	assert_not_null(overlord, "Vael-Orrun comes out of the throne")
	assert_false(sim.is_over(), "not won while he walks")
	overlord.alive = false
	sim._arrivals.clear()
	sim.step(RunSim.STEP)
	assert_eq(sim.state, RunSim.State.WON)


# --- Story files -----------------------------------------------------------------

func test_the_story_files_load_and_every_scene_they_name_exists() -> void:
	var story := Story.load_from("res://data/story")
	assert_eq(story.errors.size(), 0, "\n".join(story.errors))
	assert_false(story.prologue.is_empty())
	for id in story.all_triggered_cinematics():
		assert_true(story.has_cinematic(id), "cinematic %s exists" % id)


func test_every_boss_character_names_a_real_enemy() -> void:
	var story := Story.load_from("res://data/story")
	for person: Dictionary in story.characters.values():
		var enemy := StringName(str(person.get("boss_enemy", "")))
		if not enemy.is_empty():
			assert_true(registry.enemies.has(enemy), "%s is an enemy" % enemy)


func test_the_prologue_plays_once_before_the_first_stage() -> void:
	var story := Story.load_from("res://data/story")
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var first := meta.story_before_stage(story, &"ember_1")
	assert_eq(first[0], story.prologue)
	for id in first:
		meta.mark_seen(id)
	assert_false(meta.story_before_stage(story, &"ember_1").has(story.prologue))


func test_beats_are_due_after_enough_wins_and_only_once() -> void:
	var story := Story.load_from("res://data/story")
	var seen: Array[StringName] = []
	assert_false(story.due_after_win(&"", 5, seen).has(&"regents_counsel"))
	assert_true(story.due_after_win(&"", 6, seen).has(&"regents_counsel"))
	seen.append(&"regents_counsel")
	assert_false(story.due_after_win(&"", 7, seen).has(&"regents_counsel"))


func test_a_stage_scene_comes_before_the_beats() -> void:
	var story := Story.load_from("res://data/story")
	var due := story.due_after_win(&"ember_2", 6, [] as Array[StringName])
	assert_eq(due[0], &"ember_herald")
	assert_true(due.has(&"regents_counsel"))


func test_the_assault_opens_with_its_intro_and_ends_with_the_epilogue() -> void:
	var story := Story.load_from("res://data/story")
	assert_true(story.due_before_stage(&"assault_1", [] as Array[StringName]).has(&"assault_intro"))
	assert_eq(story.due_after_win(&"assault_1", 0, [] as Array[StringName])[0], &"epilogue")


# --- Saving ----------------------------------------------------------------------

func test_seen_cinematics_survive_a_save() -> void:
	var profile := PlayerProfile.new()
	profile.seen_cinematics.append(&"prologue")
	var loaded := PlayerProfile.from_dict(profile.to_dict())
	assert_eq(loaded.seen_cinematics, [&"prologue"] as Array[StringName])


func test_an_old_save_has_seen_no_story() -> void:
	var old := PlayerProfile.new().to_dict()
	old.erase("story")
	old["version"] = 2
	var migrated := PlayerProfile.migrate(old)
	assert_eq(int(migrated["version"]), PlayerProfile.VERSION)
	assert_true(PlayerProfile.from_dict(migrated).seen_cinematics.is_empty())


# --- Cinematic player ------------------------------------------------------------

func test_the_player_walks_through_shots_and_finishes() -> void:
	var player := CinematicPlayer.new()
	player.story = Story.load_from("res://data/story")
	player.queue = [&"prologue"] as Array[StringName]
	player.change_scene_when_done = false
	player.mark_seen = false
	add_child_autofree(player)
	assert_eq(player.current_id(), &"prologue")
	var shots: int = (player.story.cinematic(&"prologue")["shots"] as Array).size()
	assert_gt(shots, 0)
	watch_signals(player)
	player.skip_cinematic()
	player._process(1.0)
	assert_true(player.is_done())
	assert_signal_emitted(player, "finished")


func test_shots_keep_their_own_timing_without_music_markers() -> void:
	var story := Story.load_from("res://data/story")
	if story.music_for(&"ember_herald").is_empty():
		assert_eq(story.shot_markers(&"ember_herald").size(), 0)
	else:
		# Herald music is not written shot by shot, so its markers are not used for timing.
		assert_ne(story.shot_markers(&"ember_herald").size(), 3)
