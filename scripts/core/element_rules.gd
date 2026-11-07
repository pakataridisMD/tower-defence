class_name ElementRules
extends RefCounted
## Ring maths for elements: neighbours, opposites and wave damage multipliers.
## Works on ring indices so it has no dependency on loaded data.

## Each wave is aligned to one element: its enemies take less damage from that element...
const SAME_ELEMENT_MULTIPLIER := 0.5
## ...and more damage from the opposite element.
const OPPOSITE_ELEMENT_MULTIPLIER := 1.5
const OPPOSITE_STEP := 3


static func opposite_index(ring_index: int) -> int:
	return (ring_index + OPPOSITE_STEP) % ElementData.RING_SIZE


static func are_opposites(a: int, b: int) -> bool:
	return opposite_index(a) == b


static func are_neighbours(a: int, b: int) -> bool:
	var difference := absi(a - b)
	return difference == 1 or difference == ElementData.RING_SIZE - 1


## Damage multiplier for a tower with the given elements against a wave aligned to wave_element.
## A hybrid averages the factor of each of its elements. Pass -1 for an unaligned wave.
static func damage_multiplier(tower_elements: Array[int], wave_element: int) -> float:
	if tower_elements.is_empty() or wave_element < 0:
		return 1.0
	var total := 0.0
	for element in tower_elements:
		if element == wave_element:
			total += SAME_ELEMENT_MULTIPLIER
		elif are_opposites(element, wave_element):
			total += OPPOSITE_ELEMENT_MULTIPLIER
		else:
			total += 1.0
	return total / tower_elements.size()
