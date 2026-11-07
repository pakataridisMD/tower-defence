extends GutTest
## The order flat -> increased -> more is the core of every tree node, so it is pinned down here.


func _mods(list: Array) -> Array[Modifier]:
	var result: Array[Modifier] = []
	result.assign(list)
	return result


func test_no_modifiers_returns_base() -> void:
	assert_eq(StatCalculator.compute(&"damage", 10.0, _mods([])), 10.0)


func test_flat_is_added_before_percentages() -> void:
	var mods := _mods([
		Modifier.create(&"damage", Modifier.Kind.FLAT, 5.0),
		Modifier.create(&"damage", Modifier.Kind.INCREASED, 1.0),
	])
	assert_eq(StatCalculator.compute(&"damage", 10.0, mods), 30.0)


func test_increased_modifiers_add_together() -> void:
	var mods := _mods([
		Modifier.create(&"damage", Modifier.Kind.INCREASED, 0.2),
		Modifier.create(&"damage", Modifier.Kind.INCREASED, 0.3),
	])
	assert_almost_eq(StatCalculator.compute(&"damage", 10.0, mods), 15.0, 0.0001)


func test_more_modifiers_multiply_each_other() -> void:
	var mods := _mods([
		Modifier.create(&"damage", Modifier.Kind.MORE, 0.5),
		Modifier.create(&"damage", Modifier.Kind.MORE, 0.5),
	])
	assert_almost_eq(StatCalculator.compute(&"damage", 10.0, mods), 22.5, 0.0001)


func test_full_example_from_docs() -> void:
	var mods := _mods([
		Modifier.create(&"damage", Modifier.Kind.FLAT, 5.0),
		Modifier.create(&"damage", Modifier.Kind.INCREASED, 0.2),
		Modifier.create(&"damage", Modifier.Kind.INCREASED, 0.3),
		Modifier.create(&"damage", Modifier.Kind.MORE, 0.5),
	])
	assert_almost_eq(StatCalculator.compute(&"damage", 10.0, mods), 33.75, 0.0001)


func test_other_stats_are_ignored() -> void:
	var mods := _mods([Modifier.create(&"attack_range", Modifier.Kind.FLAT, 50.0)])
	assert_eq(StatCalculator.compute(&"damage", 10.0, mods), 10.0)


func test_tagged_modifier_only_applies_to_matching_tags() -> void:
	var fire_only := Modifier.create(&"damage", Modifier.Kind.INCREASED, 1.0, [&"fire"])
	var mods := _mods([fire_only])
	assert_eq(StatCalculator.compute(&"damage", 10.0, mods, [&"fire"]), 20.0, "fire tower gets the bonus")
	assert_eq(StatCalculator.compute(&"damage", 10.0, mods, [&"storm"]), 10.0, "storm tower does not")


func test_minus_one_more_zeroes_a_stat() -> void:
	var mods := _mods([Modifier.create(&"chain_falloff", Modifier.Kind.MORE, -1.0)])
	assert_eq(StatCalculator.compute(&"chain_falloff", 0.2, mods), 0.0)


func test_large_reductions_never_go_negative() -> void:
	var mods := _mods([Modifier.create(&"damage", Modifier.Kind.INCREASED, -3.0)])
	assert_eq(StatCalculator.compute(&"damage", 10.0, mods), 0.0)
