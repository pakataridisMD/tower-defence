class_name TowerData
extends Resource
## A tower type. Base towers have one element; hybrids have two neighbouring elements.

@export var id: StringName
@export var display_name: String
@export_multiline var description: String
@export var elements: Array[StringName] = []
## Gold to build.
@export var cost: int = 50
## Skill web nodes that unlock this tower once every one of them is taken. Used by hybrids of
## elements that are not neighbours, which have no bridge node between them.
@export var requires_nodes: Array[StringName] = []
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
## Pixels a hit pushes an enemy back along the path. Each enemy can only be pushed back
## SimEnemy.MAX_KNOCKBACK in total, so knockback towers cannot hold a wave forever.
@export var knockback: float = 0.0
@export var status_effects: Array[StatusEffectData] = []
## Extra gold for each kill. Tree nodes can add more.
@export var bounty_bonus: int = 0
## When an enemy poisoned by this tower dies, its poison jumps to this many nearby enemies.
@export var poison_spread_count: int = 0

@export_group("Upgrades")
## The two specialisations offered at the top level. Empty means the tower cannot ascend.
@export var ascendancies: Array[AscendancyData] = []

@export_group("Aura")
## Pixels. Other towers this close get aura_damage as increased damage. The strongest aura wins.
@export var aura_radius: float = 0.0
## Fraction: 0.15 means 15% increased damage for towers in the aura.
@export var aura_damage: float = 0.0


func ascendancy(ascendancy_id: StringName) -> AscendancyData:
	for option in ascendancies:
		if option.id == ascendancy_id:
			return option
	return null


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
