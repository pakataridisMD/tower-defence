class_name AscendancyData
extends Resource
## A specialisation a tower can take once it reaches its top level. Each tower offers two, and
## taking one is final, in the spirit of Path of Exile's ascendancy classes.

@export var id: StringName
@export var display_name: String
@export var description: String
## Gold to ascend, as a share of the tower's price: 1.0 means the same again.
@export var cost_share: float = 1.0
## Applied to this tower only, on top of the skill web.
@export var modifiers: Array[Modifier] = []
