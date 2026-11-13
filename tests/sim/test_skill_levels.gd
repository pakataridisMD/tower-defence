extends GutTest
## Skill levels: the player buys them with gold during a run, and each one makes the skill land harder,
## wider or more often (comet showers, a second wave, boulders, lightning, fields that linger).

const TEST_ROAD := preload("res://tests/support/test_road.tres")
const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"test_road"
const ENTRIES: Array[StringName] = [&"fire_entry", &"storm_entry", &"nature_entry", &"water_entry", &"earth_entry", &"void_entry"]

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	registry.maps[&"test_road"] = TEST_ROAD


func _sim(nodes: Array[StringName] = ENTRIES) -> RunSim:
	var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
	sim.tree.points = 40
	for id in nodes:
		assert_true(sim.allocate_node(id), "takes %s" % id)
	return sim


func _wave_with_enemies(sim: RunSim, count: int) -> void:
	assert_true(sim.start_next_wave())
	for step in 6000:
		if sim.enemies.size() >= count:
			return
		sim.step(RunSim.STEP)
	fail_test("the wave never put %d enemies on the road" % count)


func _run(sim: RunSim, seconds: float) -> void:
	for step in int(seconds / RunSim.STEP):
		sim.step(RunSim.STEP)


## Every blow that lands while the sim runs, with what it hit.
func _record(sim: RunSim) -> Array:
	var blows: Array = []
	sim.skill_struck.connect(func(_cast: SimSkillCast, blow: SimSkillCast.Blow, hit: Array[SimEnemy]) -> void:
		blows.append([blow, hit.duplicate()]))
	return blows


func test_every_skill_has_five_levels_that_cost_more_and_more() -> void:
	assert_eq(registry.validate(), PackedStringArray(), "the data is sound")
	for skill: SkillData in registry.skills.values():
		assert_eq(skill.max_level(), 5, "%s has five levels" % skill.id)
		assert_eq(skill.rank(1).cost, 0, "the first level comes free")
		for level in range(2, 6):
			var rank := skill.rank(level)
			assert_gt(rank.cost, skill.rank(level - 1).cost, "%s level %d costs more" % [skill.id, level])
			assert_false(rank.title.is_empty(), "%s level %d has a name" % [skill.id, level])
			assert_false(rank.description.is_empty(), "%s level %d says what it adds" % [skill.id, level])


func test_a_skill_is_raised_with_gold_once_it_is_open() -> void:
	var sim := _sim([])
	sim.gold = 5000
	assert_eq(sim.skill_level(&"meteor"), 1)
	assert_string_contains(sim.skill_upgrade_error(&"meteor"), "skill tree")
	assert_false(sim.upgrade_skill(&"meteor"))
	sim.allocate_node(&"fire_entry")
	watch_signals(sim)
	var cost := sim.skill_upgrade_cost(&"meteor")
	assert_eq(cost, sim.config.skills[&"meteor"].rank(2).cost)
	assert_true(sim.upgrade_skill(&"meteor"))
	assert_signal_emitted_with_parameters(sim, "skill_upgraded", [sim.config.skills[&"meteor"], 2])
	assert_eq(sim.gold, 5000 - cost)
	assert_eq(sim.skill_level(&"meteor"), 2)
	for level in range(3, 6):
		assert_true(sim.upgrade_skill(&"meteor"))
	assert_eq(sim.skill_level(&"meteor"), 5)
	assert_eq(sim.skill_upgrade_cost(&"meteor"), -1)
	assert_string_contains(sim.skill_upgrade_error(&"meteor"), "last level")
	assert_false(sim.upgrade_skill(&"meteor"))
	sim.allocate_node(&"water_entry")
	sim.gold = 10
	assert_eq(sim.skill_upgrade_error(&"tidal_wave"), "Not enough gold")


func test_a_higher_level_hits_harder_and_wider() -> void:
	var low := _sim()
	_wave_with_enemies(low, 3)
	assert_true(low.use_skill(&"meteor", low.enemies[0].position))
	var high := _sim()
	high.skill_levels[&"meteor"] = 5
	_wave_with_enemies(high, 3)
	assert_true(high.use_skill(&"meteor", high.enemies[0].position))
	var weak: SimSkillCast = low.skill_casts()[0]
	var strong: SimSkillCast = high.skill_casts()[0]
	assert_gt(strong.damage, weak.damage * 1.5)
	assert_gt(strong.radius, weak.radius)
	assert_eq(weak.blows_of(&"strike").size(), 1, "level 1 drops one meteor")
	assert_eq(strong.blows_of(&"strike").size(), 6, "Cataclysm drops six comets")


func test_meteor_burns_last_longer_and_reach_further_each_level() -> void:
	var skill: SkillData = registry.skills[&"meteor"]
	var burn_time := 0.0
	var reach := 0.0
	for level in range(1, 6):
		var sim := _sim()
		sim.skill_levels[&"meteor"] = level
		_wave_with_enemies(sim, 1)
		assert_true(sim.use_skill(&"meteor", sim.enemies[0].position))
		var cast: SimSkillCast = sim.skill_casts()[0]
		var burn: StatusEffectData = null
		for effect in cast.effects:
			if effect.kind == &"burn":
				burn = effect
		assert_not_null(burn, "level %d sets what it hits alight" % level)
		assert_gt(burn.duration, burn_time, "level %d burns longer" % level)
		assert_gt(cast.radius, reach, "level %d lands wider" % level)
		burn_time = burn.duration
		reach = cast.radius
	assert_gte(burn_time, 10.0, "Cataclysm's burns last ten seconds")

	# The burn keeps hurting after the blast, on an enemy that lived through it.
	var sim := _sim()
	_wave_with_enemies(sim, 1)
	var enemy := sim.enemies[0]
	enemy.max_health = 1.0e9
	enemy.health = enemy.max_health
	assert_true(sim.use_skill(&"meteor", enemy.position))
	_run(sim, skill.impact_delay + 0.1)
	assert_true(enemy.has_status(&"burn"), "it is burning after the blast")
	var after_blast := enemy.health
	_run(sim, 5.0)
	assert_true(enemy.has_status(&"burn"), "still burning five seconds on")
	assert_lt(enemy.health, after_blast, "the burn kept hurting")


func test_a_blazing_meteor_throws_enemies_off_their_feet() -> void:
	var sim := _sim()
	sim.skill_levels[&"meteor"] = 2
	_wave_with_enemies(sim, 3)
	var blows := _record(sim)
	assert_true(sim.use_skill(&"meteor", sim.enemies[0].position))
	_run(sim, 0.7)
	assert_eq(blows.size(), 1)
	var hit: Array = blows[0][1]
	assert_false(hit.is_empty())
	for enemy: SimEnemy in hit:
		assert_true(not enemy.alive or enemy.has_status(&"stun") or enemy.data.tags.has(&"boss"), "thrown down")


func test_firestorm_burns_what_walks_in_after_it_landed() -> void:
	var sim := _sim()
	sim.skill_levels[&"meteor"] = 4
	_wave_with_enemies(sim, 1)
	# Land it on the road ahead of the first enemy, so it walks into the fire.
	var first := sim.enemies[0]
	var ahead := sim.lane_curves[first.lane].sample_baked(first.progress + 200.0)
	assert_true(sim.use_skill(&"meteor", ahead))
	_run(sim, 0.7)
	var cast: SimSkillCast = sim.skill_casts()[0]
	assert_eq(cast.zones.size(), 1, "the ground is burning")
	var burned := false
	for step in int(4.0 / RunSim.STEP):
		sim.step(RunSim.STEP)
		if first.alive and first.position.distance_to(ahead) <= cast.zones[0].radius if not cast.zones.is_empty() else false:
			burned = burned or first.has_status(&"burn") or first.health < first.max_health
	assert_true(burned or not first.alive, "the enemy that walked in caught fire")


func test_riptide_sends_two_waves_and_a_tsunami_knocks_down() -> void:
	var sim := _sim()
	sim.skill_levels[&"tidal_wave"] = 4
	_wave_with_enemies(sim, 3)
	_run(sim, 2.0)
	var blows := _record(sim)
	assert_true(sim.use_skill(&"tidal_wave"))
	var cast: SimSkillCast = sim.skill_casts()[0]
	assert_eq(cast.blows_of(&"sweep").size(), 2)
	assert_gt(cast.damage, 0.0, "the wave hits for damage")
	var knocked := false
	var skill: SkillData = sim.config.skills[&"tidal_wave"]
	for step in int((skill.strike_gap + skill.sweep_time + 0.2) / RunSim.STEP):
		sim.step(RunSim.STEP)
		for enemy in sim.enemies:
			knocked = knocked or enemy.has_status(&"stun")
	assert_true(knocked, "the wall of water knocks enemies down")
	var swept := {}
	for entry: Array in blows:
		var blow: SimSkillCast.Blow = entry[0]
		swept[blow] = true
	assert_eq(swept.size(), 2, "both waves crossed")
	assert_true(sim.skill_casts().is_empty())


func test_rockfall_drops_boulders_on_different_enemies() -> void:
	var sim := _sim()
	sim.skill_levels[&"earthquake"] = 3
	_wave_with_enemies(sim, 8)
	var blows := _record(sim)
	assert_true(sim.use_skill(&"earthquake"))
	_run(sim, sim.config.skills[&"earthquake"].bolt_time + 0.5)
	var targets := {}
	for entry: Array in blows:
		var blow: SimSkillCast.Blow = entry[0]
		if blow.kind == &"bolt" and blow.target != null:
			targets[blow.target.id] = true
	assert_eq(targets.size(), 6, "six boulders, each on its own enemy")


func test_thunderstorm_strikes_enemies_and_speeds_towers_more() -> void:
	var sim := _sim()
	var tower := sim.place_tower(&"fire_brazier", Vector2i(0, 14))
	var before := tower.attacks_per_second
	sim.skill_levels[&"surge"] = 3
	_wave_with_enemies(sim, 6)
	var hurt_before := 0
	for enemy in sim.enemies:
		hurt_before += 1 if enemy.health < enemy.max_health else 0
	var blows := _record(sim)
	assert_true(sim.use_skill(&"surge"))
	assert_gt(tower.attacks_per_second, before * 1.25, "28% faster at Static Surge's power")
	assert_almost_eq(sim.skill_time_left(&"surge"), sim.config.skills[&"surge"].duration * 1.4, 0.01)
	_run(sim, sim.config.skills[&"surge"].bolt_time + 0.3)
	var bolts := 0
	for entry: Array in blows:
		bolts += 1 if (entry[0] as SimSkillCast.Blow).kind == &"bolt" else 0
	assert_eq(bolts, 6)


func test_a_collapsing_rift_crushes_what_is_inside() -> void:
	var sim := _sim()
	sim.skill_levels[&"doom"] = 5
	_wave_with_enemies(sim, 3)
	var blows := _record(sim)
	var target := sim.enemies[0]
	assert_true(sim.use_skill(&"doom", target.position))
	var cast: SimSkillCast = sim.skill_casts()[0]
	_run(sim, sim.config.skills[&"doom"].impact_delay + cast.rank.zone_time + 0.2)
	var finales := blows.filter(func(entry: Array) -> bool: return (entry[0] as SimSkillCast.Blow).kind == &"finale")
	assert_eq(finales.size(), 1, "the rift collapsed once")
	assert_true(sim.skill_casts().is_empty())


func test_a_wave_that_ends_drops_what_is_still_falling() -> void:
	var sim := _sim()
	_wave_with_enemies(sim, 1)
	assert_true(sim.use_skill(&"meteor", sim.enemies[0].position))
	assert_false(sim.skill_casts().is_empty())
	sim._finish_wave()
	assert_true(sim.skill_casts().is_empty())


func test_a_running_boon_takes_a_new_level_at_once() -> void:
	var sim := _sim()
	var tower := sim.place_tower(&"fire_brazier", Vector2i(0, 14))
	var before := tower.attacks_per_second
	_wave_with_enemies(sim, 1)
	assert_true(sim.use_skill(&"surge"))
	var level_one := tower.attacks_per_second
	sim.gold = 1000
	assert_true(sim.upgrade_skill(&"surge"))
	assert_gt(tower.attacks_per_second, level_one)
	assert_gt(level_one, before)
