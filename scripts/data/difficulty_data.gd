class_name DifficultyData
extends Resource
## A difficulty level the player picks before a run. Harder levels pay more meta points.

@export var id: StringName
@export var display_name: String
## One line, shown on the main menu.
@export var description: String
## Position in the menu, lowest first.
@export var order: int = 0
## Every enemy's health is multiplied by this.
@export var enemy_health_multiplier: float = 1.0
## Every wave brings this many times as many enemies (bosses excepted), spaced closer so the wave
## lasts about as long. See RunSim.MAX_WAVE_ENEMIES for the cap.
@export var enemy_count_multiplier: float = 1.0
## Meta points earned at the end of a run are multiplied by this.
@export var meta_point_multiplier: float = 1.0
