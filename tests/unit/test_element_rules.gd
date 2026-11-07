extends GutTest
## Ring order: 0 Fire, 1 Storm, 2 Nature, 3 Water, 4 Earth, 5 Void.

const FIRE := 0
const STORM := 1
const NATURE := 2
const WATER := 3
const EARTH := 4
const VOID := 5


func _elements(list: Array) -> Array[int]:
	var result: Array[int] = []
	result.assign(list)
	return result


func test_opposites_are_three_steps_apart() -> void:
	assert_eq(ElementRules.opposite_index(FIRE), WATER)
	assert_eq(ElementRules.opposite_index(STORM), EARTH)
	assert_eq(ElementRules.opposite_index(NATURE), VOID)
	assert_eq(ElementRules.opposite_index(VOID), NATURE)


func test_neighbours_wrap_around_the_ring() -> void:
	assert_true(ElementRules.are_neighbours(FIRE, STORM))
	assert_true(ElementRules.are_neighbours(VOID, FIRE), "Void and Fire close the ring")
	assert_false(ElementRules.are_neighbours(FIRE, NATURE))
	assert_false(ElementRules.are_neighbours(FIRE, FIRE))


func test_same_element_wave_halves_damage() -> void:
	assert_eq(ElementRules.damage_multiplier(_elements([FIRE]), FIRE), 0.5)


func test_opposite_element_wave_boosts_damage() -> void:
	assert_eq(ElementRules.damage_multiplier(_elements([FIRE]), WATER), 1.5)


func test_unrelated_and_unaligned_waves_are_neutral() -> void:
	assert_eq(ElementRules.damage_multiplier(_elements([FIRE]), STORM), 1.0)
	assert_eq(ElementRules.damage_multiplier(_elements([FIRE]), -1), 1.0)


func test_hybrids_average_their_elements() -> void:
	# Plasma (Fire + Storm) against a Fire wave: (0.5 + 1.0) / 2
	assert_eq(ElementRules.damage_multiplier(_elements([FIRE, STORM]), FIRE), 0.75)
	# Plasma against a Water wave, Fire's opposite: (1.5 + 1.0) / 2
	assert_eq(ElementRules.damage_multiplier(_elements([FIRE, STORM]), WATER), 1.25)
