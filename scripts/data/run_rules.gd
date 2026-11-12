class_name RunRules
extends Resource
## Economy and pacing numbers for a run.

@export var starting_gold: int = 150
@export var starting_lives: int = 20
## Tree points available before the first wave, so the player can pick a first element.
@export var starting_tree_points: int = 1
## Tree points paid every `waves_per_tree_point` waves. The skill web's costs are set against this:
## its nearest nodes cost 1 point and its rim up to 6.
@export var tree_points_per_wave: int = 1
## Tree points are paid every this many waves.
@export var waves_per_tree_point: int = 2
## Extra tree points for beating a boss wave.
@export var tree_points_per_boss: int = 1
## Gold paid for clearing a wave, on top of bounties.
@export var gold_per_wave: int = 20
## Share of a tower's price returned when it is sold.
@export_range(0.0, 1.0) var sell_refund: float = 0.7

@export_group("Meta points")
## Meta points for each wave cleared, won or lost.
@export var meta_points_per_wave: int = 1
## Extra meta points for winning the run.
@export var meta_points_for_win: int = 2


## Tree points earned for clearing a wave. wave_number starts at 1.
func tree_points_after_wave(wave_number: int, wave_was_boss: bool) -> int:
	var points := 0
	if waves_per_tree_point > 0 and wave_number % waves_per_tree_point == 0:
		points += tree_points_per_wave
	if wave_was_boss:
		points += tree_points_per_boss
	return points


## Meta points paid at the end of a run, before the difficulty multiplier.
func meta_points_after_run(waves_cleared: int, won: bool) -> int:
	return maxi(0, waves_cleared) * meta_points_per_wave + (meta_points_for_win if won else 0)
