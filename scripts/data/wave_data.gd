class_name WaveData
extends Resource
## One wave. Its enemies take less damage from its element and more from the opposite one.

## Id of an ElementData, or empty for an unaligned wave.
@export var element: StringName
@export var is_boss: bool = false
@export var groups: Array[SpawnGroup] = []


func enemy_count() -> int:
	var total := 0
	for group in groups:
		total += group.count
	return total
