class_name StageData
extends Resource
## One stage of a campaign: a map with its waves, and the rules that make it different from a
## skirmish run, such as which elements the skill web offers.

@export var id: StringName
@export var display_name: String
## A line or two of story, shown on the campaign map.
@export_multiline var description: String
## Id of a MapData. Its wave set is played unless wave_set is given.
@export var map: StringName
## Id of a WaveSet to play instead of the map's own.
@export var wave_set: StringName
## The last stage of an element campaign, where its corrupted Warden waits.
@export var is_guardian: bool = false

@export_group("Rules")
## Elements whose regions of the skill web can be taken. Empty allows every element. Bridges and
## keystones next to a closed region close too.
@export var allowed_elements: Array[StringName] = []
## Skill web nodes taken for free at the start of the stage. They cannot be refunded.
@export var starting_nodes: Array[StringName] = []
## Modifiers for the whole stage, such as a bonus for the home element's towers.
@export var modifiers: Array[Modifier] = []
## The rules in words, one line each, for the campaign map and the run screen.
@export var rule_text: PackedStringArray = []
## Above 0, replaces the starting gold and lives of the run rules (before meta tree bonuses).
@export var starting_gold: int = 0
@export var starting_lives: int = 0

@export_group("Reward")
## Meta points paid the first time the stage is won, on top of the usual points.
@export var first_clear_points: int = 3

@export_group("Assault")
## Buildings of the enemy base. A stage with any is an assault: it is won by bringing every one of
## them down (and whatever the last one releases), not by surviving the waves. When the waves run
## out, the last one repeats, stronger each time.
@export var structures: Array[StructureSpec] = []
## The rightmost column towers may be built in, for each phase of the assault (first phase first).
## Phases past the end of the list, or a value below 0, allow the whole map.
@export var build_columns: PackedInt32Array = []
## Above 0, the next wave starts on its own this many seconds after a wave is cleared.
@export var auto_wave_delay: float = 0.0


func is_assault() -> bool:
	return not structures.is_empty()


## The number of phases: the highest phase of any structure.
func phase_count() -> int:
	var count := 0
	for spec in structures:
		if spec != null:
			count = maxi(count, spec.phase)
	return count
