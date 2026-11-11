extends GutTest
## The battle music: its three layers load, loop and line up, each state of a run brings in the
## right layers, and a boss wave swaps them for the boss entrance and boss loop.

const OFF := BattleMusic.SILENT_DB


func test_layers_load_and_line_up() -> void:
	var length := -1.0
	for path: String in BattleMusic.LAYER_FILES:
		var stream := load(path) as AudioStreamOggVorbis
		assert_not_null(stream, "missing music layer " + path)
		if stream == null:
			continue
		if length < 0.0:
			length = stream.get_length()
		assert_almost_eq(stream.get_length(), length, 0.01, "layers must be the same length: " + path)
	assert_gt(length, 60.0, "the loop is about 96 s long")


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
