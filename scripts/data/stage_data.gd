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
