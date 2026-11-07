class_name EnemyData
extends Resource
## An enemy type. Health is scaled per wave by the wave set.

@export var id: StringName
@export var display_name: String
@export var max_health: float = 40.0
## Pixels per second along the path.
@export var speed: float = 80.0
## Flat damage removed from each hit.
@export var armour: float = 0.0
## Gold paid when killed.
@export var bounty: int = 3
## Lives lost if this enemy reaches the exit.
@export var leak_damage: int = 1
@export var tags: Array[StringName] = []
