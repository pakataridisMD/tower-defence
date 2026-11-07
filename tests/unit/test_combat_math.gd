extends GutTest


func test_armour_is_subtracted_from_each_hit() -> void:
	assert_eq(CombatMath.hit_damage(10.0, 1.0, 4.0), 6.0)


func test_a_fifth_of_a_hit_always_gets_through_armour() -> void:
	assert_almost_eq(CombatMath.hit_damage(10.0, 1.0, 50.0), 2.0, 0.0001)


func test_element_multiplier_applies_before_armour() -> void:
	# Opposite element: 10 * 1.5 = 15, minus 5 armour.
	assert_eq(CombatMath.hit_damage(10.0, 1.5, 5.0), 10.0)


func test_curses_raise_damage_taken() -> void:
	assert_almost_eq(CombatMath.hit_damage(10.0, 1.0, 0.0, 0.2), 12.0, 0.0001)


func test_chain_damage_falls_off_per_jump() -> void:
	assert_eq(CombatMath.chain_damage(10.0, 0.2, 0), 10.0)
	assert_almost_eq(CombatMath.chain_damage(10.0, 0.2, 2), 6.4, 0.0001)
	assert_eq(CombatMath.chain_damage(10.0, 0.0, 3), 10.0, "Thunderhead removes falloff")


func test_attack_interval() -> void:
	assert_almost_eq(CombatMath.attack_interval(2.0), 0.5, 0.0001)
	assert_true(CombatMath.attack_interval(0.0) > 0.0, "never divides by zero")
