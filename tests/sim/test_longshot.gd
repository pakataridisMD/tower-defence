extends GutTest
## The long-range towers (tag "longshot"): Skyneedle, Eyrie and Flare Battery. They reach most of a
## real map, fire fast for little damage, unlock from their element's core node, never fuse, and the
## Eyrie shoots the weakest enemy in sight.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const LONGSHOTS: Array[StringName] = [&"storm_skyneedle", &"nature_eyrie", &"fire_flare_battery"]
## A campaign map at the full 42 x 26 size.
const MAP := &"c_storm_2"

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _sim() -> RunSim:
	var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
	sim.tree.points = 20
	sim.gold = 5000
	return sim


func _unlock(sim: RunSim, tower_id: StringName) -> void:
	var element: StringName = sim.config.towers[tower_id].elements[0]
	sim.allocate_node(StringName("%s_entry" % element))
	sim.allocate_node(StringName("%s_core" % element))


## The free cell nearest the middle of the map.
func _middle_cell(sim: RunSim, tower_id: StringName) -> Vector2i:
	var grid := sim.config.map.grid_size
	var middle := Vector2(grid) / 2.0
	var best := Vector2i(-1, -1)
	for x in grid.x:
		for y in grid.y:
			var cell := Vector2i(x, y)
			if sim.placement_error(tower_id, cell) == "" and \
					(best.x < 0 or Vector2(cell).distance_to(middle) < Vector2(best).distance_to(middle)):
				best = cell
	return best


func test_three_longshots_are_fast_light_and_far_reaching() -> void:
	var base_ranges: Array[float] = []
	for tower_id: StringName in registry.towers:
		var data: TowerData = registry.towers[tower_id]
		if data.elements.size() == 1 and not data.is_longshot():
			base_ranges.append(data.attack_range)
	for tower_id in LONGSHOTS:
		var data: TowerData = registry.towers.get(tower_id)
		assert_not_null(data, "%s exists" % tower_id)
		if data == null:
			continue
		assert_true(data.is_longshot(), "%s is tagged longshot" % tower_id)
		assert_eq(data.elements.size(), 1, "%s has one element" % tower_id)
		assert_false(data.requires_nodes.is_empty(), "%s unlocks from the web" % tower_id)
		assert_true(data.attack_range >= 6.0 * base_ranges.max(), "%s reaches far past any base tower" % tower_id)
		assert_true(data.attacks_per_second >= 2.0, "%s fires fast" % tower_id)
		assert_true(data.damage <= 5.0, "%s hits lightly" % tower_id)
		assert_true(data.projectile_speed >= 1500.0, "%s shots cross the map quickly" % tower_id)


func test_from_the_middle_a_longshot_covers_most_of_the_road() -> void:
	var sim := _sim()
	for tower_id in LONGSHOTS:
		_unlock(sim, tower_id)
		var cell := _middle_cell(sim, tower_id)
		var tower := sim.place_tower(tower_id, cell)
		assert_not_null(tower, "built %s" % tower_id)
		if tower == null:
			continue
		var inside := 0
		var total := 0
		for lane in sim.lane_curves.size():
			var curve: Curve2D = sim.lane_curves[lane]
			var length := curve.get_baked_length()
			var along := 0.0
			while along <= length:
				total += 1
				if curve.sample_baked(along).distance_to(tower.position) <= tower.attack_range:
					inside += 1
				along += 32.0
		assert_true(float(inside) / total >= 0.8, "%s covers %d of %d road points" % [tower_id, inside, total])
		sim.sell_tower(tower)


func test_locked_until_the_element_core_node() -> void:
	var sim := _sim()
	var cell := Vector2i(-1, -1)
	sim.allocate_node(&"storm_entry")
	cell = _middle_cell(sim, &"storm_spire")
	assert_string_contains(sim.placement_error(&"storm_skyneedle", cell), "Unlock")
	assert_true(sim.allocate_node(&"storm_core"))
	assert_eq(sim.placement_error(&"storm_skyneedle", cell), "")


func test_longshots_never_fuse() -> void:
	var sim := _sim()
	for element in ["storm", "nature", "fire", "water", "earth", "void"]:
		for part in ["entry", "core", "notable", "cw", "ccw"]:
			sim.allocate_node(StringName("%s_%s" % [element, part]))
	for tower_id in LONGSHOTS:
		var tower := sim.place_tower(tower_id, _middle_cell(sim, tower_id))
		assert_eq(sim.hybrid_options(tower), [] as Array[StringName], "%s has no hybrid" % tower_id)
	var spire := sim.place_tower(&"storm_spire", _middle_cell(sim, &"storm_spire"))
	for option in sim.hybrid_options(spire):
		assert_false(sim.config.towers[option].is_longshot(), "a spire does not turn into %s" % option)


func test_eyrie_shoots_the_weakest_enemy_in_sight() -> void:
	var sim := _sim()
	_unlock(sim, &"nature_eyrie")
	var tower := sim.place_tower(&"nature_eyrie", _middle_cell(sim, &"nature_eyrie"))
	var strong := sim._make_enemy(sim.config.enemies[&"grunt"], 3.0, 0, -1, 600.0)
	var weak := sim._make_enemy(sim.config.enemies[&"grunt"], 1.0, 0, -1, 300.0)
	weak.health *= 0.25
	sim.enemies.append_array([strong, weak])
	sim._rebuild_hash()
	assert_eq(sim._find_target(tower), weak, "the weakest, though the other is nearer the exit")
	# Once enough arrows are in flight to finish it, the next goes to someone else.
	weak.incoming = weak.health
	assert_eq(sim._find_target(tower), strong)


func test_light_hits_barely_dent_armour() -> void:
	var needle: TowerData = registry.towers[&"storm_skyneedle"]
	var brazier: TowerData = registry.towers[&"fire_brazier"]
	var armour := 4.0
	var share_needle := CombatMath.hit_damage(needle.damage, 1.0, armour) / needle.damage
	var share_brazier := CombatMath.hit_damage(brazier.damage, 1.0, armour) / brazier.damage
	assert_true(share_needle < share_brazier, "armour takes a bigger bite out of light hits")


func test_each_longshot_clears_a_wave_of_weak_enemies_alone() -> void:
	for tower_id in LONGSHOTS:
		var sim := _sim()
		sim.lives = 1000
		_unlock(sim, tower_id)
		var tower := sim.place_tower(tower_id, _middle_cell(sim, tower_id))
		sim.start_next_wave()
		var elapsed := 0.0
		while sim.state == RunSim.State.WAVE and elapsed < 300.0:
			sim.step(0.05)
			elapsed += 0.05
		assert_true(tower.kills > 0, "%s killed %d enemies" % [tower_id, tower.kills])
