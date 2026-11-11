class_name SimTower
extends RefCounted
## One built tower. Its stats are the tower data with every active modifier applied,
## recomputed whenever the skill tree changes.

const MAX_LEVEL := 3
## Each level above the first: more damage and a little more range.
const DAMAGE_PER_LEVEL := 0.3
const RANGE_PER_LEVEL := 0.08
## Price of reaching level 2 and level 3, as a share of the tower's type price.
const LEVEL_COST_SHARES: Array[float] = [0.5, 0.75]

var id: int
var data: TowerData
var cell: Vector2i
var position: Vector2
## Gold spent on this tower in total: building, levels, hybrid change and ascendancy. Sales refund a share of it.
var price_paid: int
## What the tower's current type cost to build, used to price levels and the change into a hybrid.
var type_price: int
## 1 to MAX_LEVEL.
var level := 1
## The ascendancy taken at the top level, or null.
var ascendancy: AscendancyData
## Set for a hero: then this "tower" is the hero, and never levels, fuses, ascends or sells.
var hero: HeroData
## The hero's level from waves fought, 1 to HeroData.MAX_LEVEL. See hero_level() for the level it fights at.
var hero_level := 1
## Levels added by auras such as Ilyra's.
var hero_level_bonus := 0
## Seconds of wave time until the hero's ability is ready again.
var ability_cooldown := 0.0
## True once the hero has moved during this break.
var moved_this_break := false
## Modifiers from heroes' auras on this tower, set by the run.
var hero_aura: Array[Modifier] = []
var element_indices: Array[int] = []
var tags: Array[StringName] = []
var cooldown := 0.0
## Seconds left in which a boss has silenced this tower: it does not attack.
var silenced := 0.0
## Attacks made so far, for the siege shots of an assault (see RunSim.SIEGE_EVERY).
var shots := 0

var damage := 0.0
var attacks_per_second := 1.0
var attack_range := 0.0
var projectile_speed := 700.0
var splash_radius := 0.0
var chain_count := 0
var chain_range := 0.0
var chain_falloff := 0.0
var bounty_bonus := 0
var burn_spread_radius := 0.0
var poison_spread_count := 0
var knockback := 0.0
var aura_radius := 0.0
var aura_damage := 0.0
## Increased damage this tower gets from the strongest nearby aura (a Void tower).
var aura_bonus := 0.0
## Share of the target's armour this tower's hits ignore.
var armour_ignore := 0.0
var effects: Array[StatusEffectData] = []

var kills := 0
var damage_dealt := 0.0


func _init(p_id: int, p_data: TowerData, p_cell: Vector2i, p_position: Vector2, p_price: int, p_element_indices: Array[int]) -> void:
	id = p_id
	data = p_data
	cell = p_cell
	position = p_position
	price_paid = p_price
	type_price = p_price
	element_indices = p_element_indices
	tags = p_data.all_tags()


## Turns this tower into another type, such as a base tower into a hybrid, keeping its place and record.
## The tower keeps its level; an ascended tower cannot change type.
func change_type(p_data: TowerData, p_element_indices: Array[int], p_type_price: int, extra_paid: int) -> void:
	data = p_data
	element_indices = p_element_indices
	tags = p_data.all_tags()
	type_price = p_type_price
	price_paid += extra_paid


## Gold for the next level, or -1 at the top level.
func level_up_price() -> int:
	if level >= MAX_LEVEL:
		return -1
	return maxi(1, roundi(type_price * LEVEL_COST_SHARES[level - 1]))


func ascend_price(option: AscendancyData) -> int:
	return maxi(1, roundi(type_price * option.cost_share))


func can_ascend() -> bool:
	return level >= MAX_LEVEL and ascendancy == null and not data.ascendancies.is_empty()


## Modifiers that belong to this tower alone: its level, its ascendancy and auras on it.
func is_hero() -> bool:
	return hero != null


## The level a hero fights at: its own plus any aura bonus, never above HeroData.MAX_LEVEL.
func hero_level_now() -> int:
	return mini(hero_level + hero_level_bonus, HeroData.MAX_LEVEL)


## The hero's ability at its current level, or null for a tower.
func hero_ability() -> HeroAbility:
	return hero.ability_at(hero_level_now()) if hero != null else null


func own_modifiers() -> Array[Modifier]:
	var result: Array[Modifier] = []
	if hero != null:
		var levels := hero_level_now() - 1
		if levels > 0:
			result.append(Modifier.create(&"damage", Modifier.Kind.INCREASED, HeroData.DAMAGE_PER_LEVEL * levels))
			result.append(Modifier.create(&"attack_range", Modifier.Kind.INCREASED, HeroData.RANGE_PER_LEVEL * levels))
		if hero_level_now() >= HeroData.ULTIMATE_LEVEL:
			result.append_array(hero.ultimate_modifiers)
	result.append_array(hero_aura)
	if level > 1:
		result.append(Modifier.create(&"damage", Modifier.Kind.MORE, DAMAGE_PER_LEVEL * (level - 1)))
		result.append(Modifier.create(&"attack_range", Modifier.Kind.INCREASED, RANGE_PER_LEVEL * (level - 1)))
	if ascendancy != null:
		result.append_array(ascendancy.modifiers)
	if aura_bonus > 0.0:
		result.append(Modifier.create(&"damage", Modifier.Kind.INCREASED, aura_bonus))
	return result


func recompute(modifiers: Array[Modifier]) -> void:
	var own := own_modifiers()
	if not own.is_empty():
		var combined: Array[Modifier] = []
		combined.append_array(modifiers)
		combined.append_array(own)
		modifiers = combined
	damage = data.stat_with(&"damage", modifiers)
	attacks_per_second = data.stat_with(&"attacks_per_second", modifiers)
	attack_range = data.stat_with(&"attack_range", modifiers)
	projectile_speed = data.stat_with(&"projectile_speed", modifiers)
	splash_radius = data.stat_with(&"splash_radius", modifiers)
	chain_count = roundi(data.stat_with(&"chain_count", modifiers))
	chain_range = data.stat_with(&"chain_range", modifiers)
	chain_falloff = data.stat_with(&"chain_falloff", modifiers)
	bounty_bonus = roundi(data.stat_with(&"bounty_bonus", modifiers))
	burn_spread_radius = data.stat_with(&"burn_spread_radius", modifiers)
	poison_spread_count = roundi(data.stat_with(&"poison_spread_count", modifiers))
	knockback = data.stat_with(&"knockback", modifiers)
	aura_radius = data.stat_with(&"aura_radius", modifiers)
	aura_damage = data.stat_with(&"aura_damage", modifiers)
	armour_ignore = clampf(data.stat_with(&"armour_ignore", modifiers), 0.0, 1.0)
	effects.clear()
	for effect in data.status_effects:
		var spec := effect.duplicate() as StatusEffectData
		spec.damage_per_second = StatCalculator.compute(
				StringName("%s_damage" % effect.kind), effect.damage_per_second, modifiers, tags)
		spec.duration = StatCalculator.compute(
				StringName("%s_duration" % effect.kind), effect.duration, modifiers, tags)
		# "<kind>_strength" scales whatever the effect does besides damage: slow, curse or shatter.
		var strength := StatCalculator.compute(StringName("%s_strength" % effect.kind), 1.0, modifiers, tags)
		spec.slow = clampf(effect.slow * strength, 0.0, 0.9)
		spec.damage_taken = effect.damage_taken * strength
		spec.armour_reduction = effect.armour_reduction * strength
		spec.max_stacks = maxi(1, roundi(StatCalculator.compute(
				StringName("%s_stacks" % effect.kind), effect.max_stacks, modifiers, tags)))
		effects.append(spec)


func chains() -> bool:
	return chain_count > 0 and splash_radius <= 0.0


func effect_spec(kind: StringName) -> StatusEffectData:
	for spec in effects:
		if spec.kind == kind:
			return spec
	return null
