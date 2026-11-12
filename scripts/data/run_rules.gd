class_name RunRules
extends Resource
## Economy and pacing numbers for a run.

@export var starting_gold: int = 150
@export var starting_lives: int = 20
## Tree points available before the first wave, so the player can pick a first element.
@export var starting_tree_points: int = 1
## One in-run tree point every this many waves.
@export var waves_per_tree_point: int = 2
## Extra tree points for beating a boss wave.
@export var tree_points_per_boss: int = 1
## Gold paid for clearing a wave, on top of bounties.
@export var gold_per_wave: int = 20
## Clearing a wave also pays this share of the gold the player kept unspent, as a reward for saving.
@export_range(0.0, 1.0) var savings_bonus: float = 0.2
## The savings bonus never pays more than this for the first wave, so hoarding cannot snowball.
@export var savings_bonus_cap: int = 150
## The cap grows by this share every wave after the first (geometric: 150, 162, 175, ...).
@export var savings_cap_growth: float = 0.08
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
		points += 1
	if wave_was_boss:
		points += tree_points_per_boss
	return points


## The most the savings bonus can pay for clearing wave `wave_number` (starts at 1).
func savings_cap_at(wave_number: int) -> int:
	return roundi(savings_bonus_cap * pow(1.0 + savings_cap_growth, maxi(0, wave_number - 1)))


## The savings bonus for keeping `kept` gold through wave `wave_number`, at `share` (normally savings_bonus).
func savings_bonus_for(kept: int, share: float, wave_number: int = 1) -> int:
	if kept <= 0 or share <= 0.0:
		return 0
	return mini(floori(kept * share), savings_cap_at(wave_number))


## Meta points paid at the end of a run, before the difficulty multiplier.
func meta_points_after_run(waves_cleared: int, won: bool) -> int:
	return maxi(0, waves_cleared) * meta_points_per_wave + (meta_points_for_win if won else 0)
