class_name RunRules
extends Resource
## Economy and pacing numbers for a run.

@export var starting_gold: int = 150
@export var starting_lives: int = 20
## One in-run tree point every this many waves.
@export var waves_per_tree_point: int = 2
## Extra tree points for beating a boss wave.
@export var tree_points_per_boss: int = 1


## Tree points earned for clearing a wave. wave_number starts at 1.
func tree_points_after_wave(wave_number: int, wave_was_boss: bool) -> int:
	var points := 0
	if waves_per_tree_point > 0 and wave_number % waves_per_tree_point == 0:
		points += 1
	if wave_was_boss:
		points += tree_points_per_boss
	return points
