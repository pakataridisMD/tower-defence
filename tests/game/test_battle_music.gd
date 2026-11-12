extends GutTest
## The battle music: every map's tracks load and their layers line up, the track rotates, each state of a run brings in the
## right layers, and a boss wave swaps them for the boss entrance and boss loop.

const OFF := BattleMusic.SILENT_DB


func test_every_track_loads_and_its_layers_line_up() -> void:
	var all := BattleMusic.tracks_for(&"meadow")
	assert_eq(all.size(), 22, "seven realms of three tracks, plus Hold the Line")
	for track: String in all:
		var length := -1.0
		for layer in BattleMusic.LAYER_NAMES.size():
			var path := BattleMusic.layer_file(track, layer)
			var stream := load(path) as AudioStreamOggVorbis
			assert_not_null(stream, "missing music layer " + path)
			if stream == null:
				continue
			if length < 0.0:
				length = stream.get_length()
			assert_almost_eq(stream.get_length(), length, 0.01, "layers must be the same length: " + path)
		assert_gt(length, 50.0, "a battle loop is at least about a minute long: " + track)


func test_every_element_map_has_four_tracks() -> void:
	for biome: StringName in [&"fire", &"water", &"earth", &"storm", &"nature", &"void", &"heart"]:
		var tracks := BattleMusic.tracks_for(biome)
		assert_eq(tracks.size(), 4, "three realm tracks and Hold the Line for " + biome)
		assert_true(tracks.has(BattleMusic.DEFAULT_TRACK))
		for t: String in tracks.slice(0, 3):
			assert_true(t.begins_with("realm_" + String(biome)), t + " belongs to " + biome)


func test_every_map_biome_has_its_own_music() -> void:
	for path: String in DirAccess.get_files_at("res://data/maps"):
		if not path.ends_with(".tres"):
			continue
		var map := load("res://data/maps/" + path) as MapData
		if map.biome == &"meadow":
			continue
		assert_true(BattleMusic.REALM_TRACKS.has(map.biome), "no music for biome %s (%s)" % [map.biome, path])


func test_the_track_changes_after_a_few_waves_or_a_boss() -> void:
	assert_false(BattleMusic.should_change(1, false, 4))
	assert_false(BattleMusic.should_change(BattleMusic.WAVES_PER_TRACK - 1, false, 4))
	assert_true(BattleMusic.should_change(BattleMusic.WAVES_PER_TRACK, false, 4))
	assert_true(BattleMusic.should_change(1, true, 4), "a new track after every boss wave")
	assert_false(BattleMusic.should_change(9, true, 1), "nothing to change to")


func test_build_phase_plays_only_the_calm_layer() -> void:
	assert_eq(BattleMusic.targets(RunSim.State.BUILDING, false, false, 20, 20), PackedFloat32Array([0.0, OFF, OFF]))
	# even before a boss wave, the build phase stays calm
	assert_eq(BattleMusic.targets(RunSim.State.BUILDING, true, true, 2, 20), PackedFloat32Array([0.0, OFF, OFF]))


func test_a_wave_brings_in_the_drums() -> void:
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, false, false, 20, 20), PackedFloat32Array([0.0, 0.0, OFF]))


func test_last_wave_and_low_lives_bring_in_the_choir() -> void:
	var full := PackedFloat32Array([0.0, 0.0, 0.0])
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, false, true, 20, 20), full, "last wave")
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, false, false, 6, 20), full, "30% of lives left")
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, false, false, 7, 20), PackedFloat32Array([0.0, 0.0, OFF]))


func test_the_end_of_a_run_fades_everything_out() -> void:
	assert_eq(BattleMusic.targets(RunSim.State.WON, false, false, 20, 20), PackedFloat32Array([OFF, OFF, OFF]))
	assert_eq(BattleMusic.targets(RunSim.State.LOST, false, false, 0, 20), PackedFloat32Array([OFF, OFF, OFF]))


func test_layers_come_in_faster_than_they_go() -> void:
	assert_gt(BattleMusic.fade_rate(OFF, 0.0), BattleMusic.fade_rate(0.0, OFF))


func test_a_boss_wave_cuts_the_battle_layers_for_the_boss_music() -> void:
	assert_true(BattleMusic.boss_fight(RunSim.State.WAVE, true))
	assert_false(BattleMusic.boss_fight(RunSim.State.BUILDING, true), "not before the boss wave starts")
	assert_false(BattleMusic.boss_fight(RunSim.State.WAVE, false))
	var off := PackedFloat32Array([OFF, OFF, OFF])
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, true, false, 20, 20), off, "boss wave")
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, true, true, 2, 20), off, "boss on the last wave, low lives")
	# the cut is quick, so the entrance hit lands in the clear
	assert_gt(BattleMusic.fade_rate(0.0, OFF, true), BattleMusic.fade_rate(0.0, OFF) * 5.0)


func test_boss_music_loads_and_hands_over_on_the_downbeat() -> void:
	var entrance := load(BattleMusic.ENTRANCE_FILE) as AudioStreamOggVorbis
	var loop := load(BattleMusic.BOSS_LOOP_FILE) as AudioStreamOggVorbis
	assert_not_null(entrance, "missing " + BattleMusic.ENTRANCE_FILE)
	assert_not_null(loop, "missing " + BattleMusic.BOSS_LOOP_FILE)
	if entrance == null or loop == null:
		return
	assert_gt(entrance.get_length(), BattleMusic.ENTRANCE_SECONDS, "the entrance rings on past the handover")
	assert_gt(loop.get_length(), 40.0, "the boss loop is about 55 s long")
	var info: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://assets/game/music/boss_entrance.json"))
	assert_almost_eq(BattleMusic.ENTRANCE_SECONDS, float(info["handover_seconds"]), 0.001,
			"ENTRANCE_SECONDS must match the score")
