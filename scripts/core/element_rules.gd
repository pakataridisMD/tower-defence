class_name ElementRules
extends RefCounted
## Ring maths for elements: neighbours, opposites and wave damage multipliers.
## Works on ring indices so it has no dependency on loaded data.

## Each wave is aligned to one element: its enemies take less damage from that element...
const SAME_ELEMENT_MULTIPLIER := 0.5
## ...and more damage from the opposite element.
const OPPOSITE_ELEMENT_MULTIPLIER := 1.5
const OPPOSITE_STEP := 3

## How each kind of enemy takes tower damage, by steps round the ring from its own element: its own
## element, a neighbour, two steps away and the opposite. Most are PLAIN; the rest are tougher against
## some elements and softer against the opposite one, so the player has to bring the right towers.
const PLAIN := &""
## Born of its element: immune to it, and the opposite element tears it apart.
const ATTUNED := &"attuned"
## Rune-warded: immune to its own element and both its neighbours, weak to the opposite.
const WARDED := &"warded"
## Heavy plate and hide: shrugs off most of every element; only the opposite cuts deep.
const TANK := &"tank"
const PROFILES := {
	PLAIN: [0.5, 1.0, 1.0, 1.5],
	ATTUNED: [0.0, 1.0, 1.0, 2.0],
	WARDED: [0.0, 0.0, 1.0, 2.0],
	TANK: [0.25, 0.6, 0.6, 2.0],
}
const PROFILE_NAMES := {PLAIN: "", ATTUNED: "Attuned", WARDED: "Warded", TANK: "Tank"}
const PROFILE_TEXT := {
	PLAIN: "Takes half damage from its own element and 1.5x from the opposite.",
	ATTUNED: "Attuned: immune to its own element, takes double damage from the opposite.",
	WARDED: "Warded: immune to its own element and both its neighbours, takes double from the opposite.",
	TANK: "Tank: takes a quarter from its own element and 0.6x from all others, double from the opposite.",
}


static func opposite_index(ring_index: int) -> int:
	return (ring_index + OPPOSITE_STEP) % ElementData.RING_SIZE


static func are_opposites(a: int, b: int) -> bool:
	return opposite_index(a) == b


static func are_neighbours(a: int, b: int) -> bool:
	var difference := absi(a - b)
	return difference == 1 or difference == ElementData.RING_SIZE - 1


## Steps round the ring from a to b: 0 (same) to 3 (opposite).
static func steps(a: int, b: int) -> int:
	var difference := absi(a - b) % ElementData.RING_SIZE
	return mini(difference, ElementData.RING_SIZE - difference)


## Damage factor of one element against an enemy of `enemy_element` with an affinity profile.
static func element_factor(element: int, enemy_element: int, profile: StringName = PLAIN) -> float:
	if element < 0 or enemy_element < 0:
		return 1.0
	var table: Array = PROFILES.get(profile, PROFILES[PLAIN])
	return table[steps(element, enemy_element)]


## Damage multiplier for a tower with the given elements against an enemy aligned to enemy_element.
## A hybrid averages the factor of each of its elements, so a dual or triple is never fully stopped
## by one immunity. Pass -1 for an unaligned enemy.
static func damage_multiplier(tower_elements: Array[int], enemy_element: int, profile: StringName = PLAIN) -> float:
	if tower_elements.is_empty() or enemy_element < 0:
		return 1.0
	var total := 0.0
	for element in tower_elements:
		total += element_factor(element, enemy_element, profile)
	return total / tower_elements.size()


## The best factor anything can get against the profile: its opposite element's.
static func weakness_multiplier(enemy_element: int, profile: StringName = PLAIN) -> float:
	if enemy_element < 0:
		return 1.0
	return (PROFILES.get(profile, PROFILES[PLAIN]) as Array)[OPPOSITE_STEP]


## Ring indices of the elements the profile is immune to, around `enemy_element`.
static func immunities(enemy_element: int, profile: StringName = PLAIN) -> Array[int]:
	var result: Array[int] = []
	if enemy_element < 0:
		return result
	for element in ElementData.RING_SIZE:
		if element_factor(element, enemy_element, profile) <= 0.0:
			result.append(element)
	return result
