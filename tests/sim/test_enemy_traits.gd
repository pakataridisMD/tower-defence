extends GutTest
## The campaign's enemy traits (healing, splitting, summoning, warding, changing element), spawn
## groups with their own element, and maps with several roads.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


## A run on a real map with one wave of the given groups.
func _sim(groups: Array[SpawnGroup], map_id: StringName = &"switchback", element: StringName = &"fire") -> RunSim:
	var config := RunConfig.from_registry(registry, map_id)
	var wave := WaveData.new()
	wave.element = element
	wave.groups = groups
	var waves := WaveSet.new()
	waves.id = &"test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	config.wave_set = waves
	var sim := RunSim.new(config)
	sim.tree.points = 20
	sim.gold = 5000
	return sim


func _group(enemy: StringName, count: int = 1, element: StringName = &"", lane: int = -1) -> SpawnGroup:
	var group := SpawnGroup.new()
	group.enemy = enemy
	group.count = count
	group.spawn_interval = 0.1
	group.element = element
	group.lane = lane
	return group


func _spawn_all(sim: RunSim) -> void:
	sim.start_next_wave()
	for i in 120:
		sim._spawn(RunSim.STEP)


func _effect(kind: StringName, dps: float = 0.0) -> StatusEffectData:
	var spec := StatusEffectData.new()
	spec.kind = kind
	spec.duration = 5.0
	spec.damage_per_second = dps
	return spec


func test_warded_enemies_ignore_every_effect() -> void:
	var sim := _sim([_group(&"warded")])
	_spawn_all(sim)
	var warded := sim.enemies[0]
	for kind: StringName in [&"burn", &"poison", &"slow", &"stun", &"curse", &"shatter"]:
		warded.apply_status(_effect(kind), null, 1.0)
	assert_true(warded.statuses.is_empty())


func test_splitters_burst_into_shardlings_with_their_element() -> void:
	var sim := _sim([_group(&"splitter")], &"switchback", &"water")
	_spawn_all(sim)
	var splitter := sim.enemies[0]
	splitter.progress = 300.0
	sim._damage(splitter, 99999.0, null)
	sim._remove_dead()
	sim.enemies.append_array(sim._arrivals)
	sim._arrivals.clear()
	assert_eq(sim.enemies.size(), 3)
	for shard in sim.enemies:
		assert_eq(shard.data.id, &"shardling")
		assert_eq(shard.element, splitter.element, "same element as the splitter")
		assert_true(shard.progress <= 300.0 and shard.progress > 250.0, "just behind where it died")
	assert_eq(sim.kills, 1)


func test_a_wave_is_not_over_until_the_pieces_are_dead() -> void:
	var sim := _sim([_group(&"splitter")])
	sim.allocate_node(&"fire_entry")
	sim.start_next_wave()
	var saw_shardlings := false
	var elapsed := 0.0
	while sim.state == RunSim.State.WAVE and elapsed < 300.0:
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
		if sim.enemies.any(func(e: SimEnemy) -> bool: return e.data.id == &"shardling"):
			saw_shardlings = true
		if sim.enemies.size() == 1 and sim.enemies[0].data.id == &"splitter" and sim.towers.is_empty():
			sim._damage(sim.enemies[0], 99999.0, null)
	assert_true(saw_shardlings)
	assert_ne(sim.state, RunSim.State.WAVE, "the wave ended")


func test_bosses_summon_on_a_timer() -> void:
	var sim := _sim([_group(&"broodmother")])
	_spawn_all(sim)
	var mother := sim.enemies[0]
	mother.progress = 400.0
	sim._tick_traits(2.4)
	assert_true(sim._arrivals.is_empty())
	sim._tick_traits(0.2)
	assert_eq(sim._arrivals.size(), 2, "two shardlings every 2.5 seconds")
	assert_eq(sim._arrivals[0].data.id, &"shardling")


func test_guardians_keep_their_own_element_in_any_wave() -> void:
	var sim := _sim([_group(&"cinder_tyrant")], &"switchback", &"water")
	_spawn_all(sim)
	assert_eq(sim.enemies[0].element, sim.config.element_index(&"fire"))


func test_groups_can_carry_their_own_element() -> void:
	var sim := _sim([_group(&"grunt", 1, &"void"), _group(&"grunt", 1)], &"switchback", &"storm")
	_spawn_all(sim)
	var elements: Array[int] = []
	for enemy in sim.enemies:
		elements.append(enemy.element)
	elements.sort()
	assert_eq(elements, [sim.config.element_index(&"storm"), sim.config.element_index(&"void")] as Array[int])


func test_damage_uses_each_enemys_element() -> void:
	var sim := _sim([_group(&"grunt", 1, &"water"), _group(&"grunt", 1, &"fire")], &"switchback", &"storm")
	sim.allocate_node(&"fire_entry")
	var tower := sim.place_tower(&"fire_brazier", Vector2i(2, 3))
	_spawn_all(sim)
	sim.enemies.sort_custom(func(a: SimEnemy, b: SimEnemy) -> bool: return a.element < b.element)
	var fire_enemy := sim.enemies[0]
	var water_enemy := sim.enemies[1]
	sim._hit(tower, fire_enemy, 10.0)
	sim._hit(tower, water_enemy, 10.0)
	var fire_loss := fire_enemy.max_health - fire_enemy.health
	var water_loss := water_enemy.max_health - water_enemy.health
	assert_almost_eq(water_loss, fire_loss * 3.0, 0.01, "Fire hits Water for 1.5x and Fire for 0.5x")


func test_prismatic_enemies_turn_round_the_ring() -> void:
	var sim := _sim([_group(&"sundered_heart")], &"switchback", &"fire")
	_spawn_all(sim)
	var heart := sim.enemies[0]
	var start := heart.element
	sim._tick_traits(5.01)
	assert_eq(heart.element, (start + 1) % ElementData.RING_SIZE)
	for i in 5:
		sim._tick_traits(5.0)
	assert_eq(heart.element, start, "all the way round")


func test_shared_groups_take_turns_over_the_roads() -> void:
	var sim := _sim([_group(&"grunt", 6)], &"c_converge_2")
	assert_eq(sim.lane_curves.size(), 3)
	_spawn_all(sim)
	var lanes: Array[int] = []
	for enemy in sim.enemies:
		lanes.append(enemy.lane)
	assert_eq(lanes, [0, 1, 2, 0, 1, 2] as Array[int])


func test_a_group_can_keep_to_one_road() -> void:
	var sim := _sim([_group(&"grunt", 3, &"", 2)], &"c_converge_2")
	_spawn_all(sim)
	for enemy in sim.enemies:
		assert_eq(enemy.lane, 2)
		assert_eq(enemy.position, sim.lane_curves[2].sample_baked(0.0))


func test_towers_aim_at_whoever_is_closest_to_the_exit_on_any_road() -> void:
	var sim := _sim([_group(&"grunt", 2)], &"c_converge_2")
	_spawn_all(sim)
	var far_along := sim.enemies[0]
	var behind := sim.enemies[1]
	far_along.lane = 0
	behind.lane = 1
	far_along.progress = sim.lane_lengths[0] - 300.0
	behind.progress = sim.lane_lengths[1] - 400.0
	assert_true(sim.distance_to_exit(far_along) < sim.distance_to_exit(behind))
	far_along.position = Vector2(100, 100)
	behind.position = Vector2(110, 100)
	var tower := SimTower.new(1, sim.config.towers[&"fire_brazier"], Vector2i(1, 1), Vector2(105, 100), 10, [0] as Array[int])
	tower.attack_range = 200.0
	sim._rebuild_hash()
	assert_eq(sim._find_target(tower), far_along)


func test_every_road_of_a_map_is_path() -> void:
	var map: MapData = registry.maps[&"c_converge_3"]
	var cells := map.path_cells()
	for lane in map.lane_count():
		for point in map.lane_waypoints(lane):
			assert_true(cells.has(point), "lane %d passes %s" % [lane, point])
	assert_eq(map.path_errors(), PackedStringArray())


func test_bad_lanes_are_reported() -> void:
	var map := MapData.new()
	map.waypoints = [Vector2i(0, 0), Vector2i(5, 0)] as Array[Vector2i]
	var lane := MapLane.new()
	lane.waypoints = [Vector2i(0, 3), Vector2i(4, 4)] as Array[Vector2i]
	map.extra_lanes = [lane] as Array[MapLane]
	assert_eq(map.path_errors().size(), 1)
	assert_string_contains(map.path_errors()[0], "lane 1")
