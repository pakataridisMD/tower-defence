class_name TowerData
extends Resource
## A tower type. Base towers have one element; hybrids have two neighbouring elements.

@export var id: StringName
@export var display_name: String
@export_multiline var description: String
@export var elements: Array[StringName] = []
## Gold to build.
@export var cost: int = 50
## Extra tags that tree modifiers can target. Element ids and "hybrid" are added automatically.
@export var tags: Array[StringName] = []

@export_group("Attack")
@export var damage: float = 10.0
@export var attacks_per_second: float = 1.0
## Pixels.
@export var attack_range: float = 160.0
## Pixels per second. Towers that chain hit instantly and ignore this.
@export var projectile_speed: float = 700.0
## Pixels. 0 means single target.
@export var splash_radius: float = 0.0
## Extra enemies a hit jumps to. 0 means no chaining.
@export var chain_count: int = 0
## Pixels a chain can jump.
@export var chain_range: float = 0.0
## Fraction of damage lost on each chain jump.
@export_range(0.0, 1.0) var chain_falloff: float = 0.0
@export var status_effects: Array[StatusEffectData] = []


func is_hybrid() -> bool:
	return elements.size() == 2


## Tags used to decide which modifiers apply to this tower.
func all_tags() -> Array[StringName]:
	var result: Array[StringName] = []
	result.append_array(elements)
	for tag in tags:
		if not result.has(tag):
			result.append(tag)
	if is_hybrid():
		result.append(&"hybrid")
	return result


## Base value of a numeric property by name, so modifiers can target any attack stat.
## Unknown stats return 0, which lets tree nodes add brand new stats with FLAT modifiers.
func base_stat(stat: StringName) -> float:
	var value: Variant = get(stat)
	if value is float or value is int:
		return float(value)
	return 0.0


## Final value of a stat after applying modifiers that match this tower's tags.
func stat_with(stat: StringName, modifiers: Array[Modifier]) -> float:
	return StatCalculator.compute(stat, base_stat(stat), modifiers, all_tags())
