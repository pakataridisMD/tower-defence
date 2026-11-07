class_name CombatMath
extends RefCounted
## Damage formulas, kept separate so they are easy to test and to tune.

## Share of a hit that always gets through armour, so weak towers still hurt armoured enemies a little.
const MIN_DAMAGE_SHARE := 0.2


## Damage of one direct hit after the wave's element multiplier, curses and armour.
static func hit_damage(damage: float, element_multiplier: float, armour: float, damage_taken: float = 0.0) -> float:
	var scaled := damage * element_multiplier * (1.0 + damage_taken)
	return maxf(scaled - armour, scaled * MIN_DAMAGE_SHARE)


## Damage on a chain jump. Jump 0 is the first target.
static func chain_damage(damage: float, falloff: float, jump: int) -> float:
	return damage * pow(1.0 - clampf(falloff, 0.0, 1.0), jump)


## Seconds between attacks.
static func attack_interval(attacks_per_second: float) -> float:
	return 1.0 / maxf(attacks_per_second, 0.01)
