class_name WaveData
extends Resource
## One wave. Its enemies take less damage from its element and more from the opposite one.

## Id of an ElementData, or empty for an unaligned wave.
@export var element: StringName
@export var is_boss: bool = false
## Every enemy's health in this wave is multiplied by this, on top of the wave set's growth.
@export var health_multiplier: float = 1.0
## How the wave comes at you, in a few words for the HUD ("Runner packs, a flank attack and a
## closing surge."). Empty says nothing.
@export var description: String
@export var groups: Array[SpawnGroup] = []


func enemy_count() -> int:
	var total := 0
	for group in groups:
		total += group.count
	return total


## Seconds from the wave's start to its last spawn.
func spawn_window() -> float:
	var last := 0.0
	for group in groups:
		last = maxf(last, group.start_delay + group.duration())
	return last
