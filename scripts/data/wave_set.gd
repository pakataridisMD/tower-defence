class_name WaveSet
extends Resource
## The full list of waves for a map or mode.

@export var id: StringName
@export var display_name: String
## Enemy health is multiplied by this once for every wave after the first.
@export var health_growth: float = 1.12
## Every enemy's health is multiplied by this in every wave, to tune a whole set at once.
@export var health_scale: float = 1.0
## Bosses' health is multiplied by this on top, so a stage can soften its bosses alone (see
## tools/campaign/tuning.py "boss_life").
@export var boss_health_scale: float = 1.0
@export var waves: Array[WaveData] = []


## Health multiplier for a wave. wave_number starts at 1.
func health_multiplier(wave_number: int) -> float:
	return health_scale * pow(health_growth, maxi(wave_number - 1, 0))
