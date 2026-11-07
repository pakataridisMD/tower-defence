class_name SpawnGroup
extends Resource
## A batch of one enemy type inside a wave.

## Id of an EnemyData.
@export var enemy: StringName
@export var count: int = 10
## Seconds between spawns.
@export var spawn_interval: float = 0.8
## Seconds after the wave starts before this group begins.
@export var start_delay: float = 0.0
