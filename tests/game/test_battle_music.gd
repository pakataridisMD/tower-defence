extends GutTest
## The battle music: its three layers load, loop and line up, and each state of a run brings in the
## right layers.

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


func test_boss_last_wave_and_low_lives_bring_in_the_choir() -> void:
	var full := PackedFloat32Array([0.0, 0.0, 0.0])
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, true, false, 20, 20), full, "boss wave")
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, false, true, 20, 20), full, "last wave")
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, false, false, 6, 20), full, "30% of lives left")
	assert_eq(BattleMusic.targets(RunSim.State.WAVE, false, false, 7, 20), PackedFloat32Array([0.0, 0.0, OFF]))


func test_the_end_of_a_run_fades_everything_out() -> void:
	assert_eq(BattleMusic.targets(RunSim.State.WON, false, false, 20, 20), PackedFloat32Array([OFF, OFF, OFF]))
	assert_eq(BattleMusic.targets(RunSim.State.LOST, false, false, 0, 20), PackedFloat32Array([OFF, OFF, OFF]))


func test_layers_come_in_faster_than_they_go() -> void:
	assert_gt(BattleMusic.fade_rate(OFF, 0.0), BattleMusic.fade_rate(0.0, OFF))
