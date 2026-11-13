extends GutTest
## The skills the player casts during a wave: how they open, what each one does and how they cool down.

const TEST_ROAD := preload("res://tests/support/test_road.tres")

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"test_road"
## A buildable cell far from every stretch of road, so a tower there never ends the wave early.
const FAR_CELL := Vector2i(0, 14)

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	# The small 24 x 15 road these tests were written against (the real maps are bigger and curved).
	registry.maps[&"test_road"] = TEST_ROAD


## A run with plenty of points and these skill web nodes taken.
func _sim(nodes: Array[StringName] = []) -> RunSim:
	var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
	sim.tree.points = 20
	for id in nodes:
		assert_true(sim.allocate_node(id), "takes %s" % id)
	return sim


## Starts the first wave and runs it until this many enemies are on the road.
func _wave_with_enemies(sim: RunSim, count: int = 5) -> void:
	assert_true(sim.start_next_wave())
	for step in 4000:
		if sim.enemies.size() >= count:
			return
		sim.step(RunSim.STEP)
	fail_test("the wave never put %d enemies on the road" % count)


func _run(sim: RunSim, seconds: float) -> void:
	for step in int(seconds / RunSim.STEP):
		sim.step(RunSim.STEP)


func test_every_element_has_a_skill_in_ring_order() -> void:
	var sim := _sim()
	var skills := sim.skill_list()
	assert_eq(skills.size(), 6)
	for i in skills.size():
		assert_eq(sim.config.element_index(skills[i].element), i, "%s is skill %d" % [skills[i].id, i])
		assert_false(sim.is_skill_unlocked(skills[i].id), "%s starts locked" % skills[i].id)
		assert_gt(skills[i].cooldown, 0.0)


func test_a_skill_opens_with_its_element_and_only_works_during_a_wave() -> void:
	var sim := _sim()
	assert_string_contains(sim.skill_error(&"meteor"), "skill tree")
	assert_false(sim.use_skill(&"meteor", Vector2(100, 100)))
	sim.allocate_node(&"fire_entry")
	assert_true(sim.is_skill_unlocked(&"meteor"))
	assert_false(sim.is_skill_unlocked(&"surge"), "taking Fire does not open the Storm skill")
	assert_string_contains(sim.skill_error(&"meteor"), "during a wave")
	assert_false(sim.use_skill(&"meteor", Vector2(100, 100)))
	sim.start_next_wave()
	assert_eq(sim.skill_error(&"meteor"), "")


func test_meteor_hits_what_is_near_and_then_cools_down() -> void:
	var sim := _sim([&"fire_entry"])
	_wave_with_enemies(sim, 6)
	var skill: SkillData = sim.config.skills[&"meteor"]
	var at := sim.enemies[0].position
	# Who is in reach is decided where they stand when the meteor lands, after its fall.
	var near: Array[SimEnemy] = []
	var far: Array[SimEnemy] = []
	sim.skill_struck.connect(func(_cast: SimSkillCast, blow: SimSkillCast.Blow, _hit: Array[SimEnemy]) -> void:
		for enemy in sim.enemies:
			if enemy.position.distance_to(blow.at) <= blow.radius:
				near.append(enemy)
			else:
				far.append(enemy))
	watch_signals(sim)
	assert_true(sim.use_skill(&"meteor", at))
	assert_signal_emitted(sim, "skill_used")
	assert_signal_not_emitted(sim, "skill_struck", "the meteor is still falling")
	assert_eq(sim.skill_casts().size(), 1)
	_run(sim, skill.impact_delay + 0.05)
	assert_signal_emitted(sim, "skill_struck")
	assert_false(near.is_empty(), "it lands among them")
	assert_false(far.is_empty(), "some enemies are out of its reach")
	for enemy in near:
		assert_true(not enemy.alive or (enemy.health < enemy.max_health and enemy.has_status(&"burn")),
				"an enemy in reach is hurt and burning")
	for enemy in far:
		assert_eq(enemy.health, enemy.max_health, "an enemy out of reach is untouched")

	var spent := skill.impact_delay + 0.05
	assert_almost_eq(sim.skill_cooldown_left(&"meteor"), skill.cooldown - spent, 0.05)
	assert_string_contains(sim.skill_error(&"meteor"), "ready in")
	assert_false(sim.use_skill(&"meteor", at), "it cannot be cast again straight away")
	_run(sim, 10.0)
	assert_almost_eq(sim.skill_cooldown_left(&"meteor"), skill.cooldown - 10.0 - spent, 0.1)


func test_a_cooldown_runs_down_and_the_skill_can_be_cast_again() -> void:
	var sim := _sim([&"water_entry"])
	_wave_with_enemies(sim, 1)
	assert_true(sim.use_skill(&"tidal_wave"))
	sim._skill_cooldowns[&"tidal_wave"] = 0.5
	_run(sim, 1.0)
	assert_eq(sim.skill_cooldown_left(&"tidal_wave"), 0.0)
	assert_true(sim.use_skill(&"tidal_wave"))


func test_surge_speeds_up_every_tower_for_a_while() -> void:
	var sim := _sim([&"fire_entry", &"storm_entry"])
	var tower := sim.place_tower(&"fire_brazier", FAR_CELL)
	assert_not_null(tower)
	var before := tower.attacks_per_second
	_wave_with_enemies(sim, 1)
	assert_true(sim.use_skill(&"surge"))
	assert_gt(tower.attacks_per_second, before * 1.15)
	assert_gt(sim.skill_time_left(&"surge"), 0.0)
	_run(sim, sim.config.skills[&"surge"].duration + 0.5)
	assert_eq(sim.state, RunSim.State.WAVE, "the wave is still running")
	assert_almost_eq(tower.attacks_per_second, before, 0.0001)
	assert_eq(sim.skill_time_left(&"surge"), 0.0)


func test_tidal_wave_pushes_every_enemy_back() -> void:
	var sim := _sim([&"water_entry"])
	_wave_with_enemies(sim, 4)
	_run(sim, 3.0)
	var before: Dictionary[int, float] = {}
	for enemy in sim.enemies:
		before[enemy.id] = enemy.progress
	var pushed: Dictionary[int, bool] = {}
	sim.skill_struck.connect(func(_cast: SimSkillCast, _blow: SimSkillCast.Blow, hit: Array[SimEnemy]) -> void:
		for enemy in hit:
			pushed[enemy.id] = true)
	assert_true(sim.use_skill(&"tidal_wave"))
	# The wave crosses the board, hitting each enemy as it passes.
	_run(sim, sim.config.skills[&"tidal_wave"].sweep_time + 0.1)
	for id in before:
		assert_true(pushed.has(id), "the wave reached enemy %d" % id)
	assert_true(sim.skill_casts().is_empty(), "the wave has crossed")


func test_entangle_holds_and_poisons_what_it_reaches() -> void:
	var sim := _sim([&"nature_entry"])
	_wave_with_enemies(sim, 3)
	var target := sim.enemies[0]
	assert_true(sim.use_skill(&"entangle", target.position))
	assert_true(target.has_status(&"stun"))
	assert_true(target.has_status(&"poison"))
	var held_at := target.progress
	_run(sim, 1.0)
	assert_almost_eq(target.progress, held_at, 0.001, "a stunned enemy does not move")


func test_earthquake_and_doom_weaken_enemies() -> void:
	var sim := _sim([&"earth_entry", &"void_entry"])
	_wave_with_enemies(sim, 3)
	var target := sim.enemies[0]
	var armour := target.effective_armour()
	assert_true(sim.use_skill(&"earthquake"))
	for enemy in sim.enemies:
		assert_true(not enemy.alive or enemy.has_status(&"shatter"))
	assert_true(not target.alive or target.effective_armour() <= armour)
	assert_true(sim.use_skill(&"doom", target.position))
	assert_true(not target.alive or target.damage_taken_bonus() > 0.0, "a cursed enemy takes more damage")


func test_a_broken_skill_is_reported() -> void:
	var skill := SkillData.new()
	skill.id = &"broken"
	skill.element = &"plasma"
	skill.requires_node = &"nowhere"
	skill.cooldown = 0.0
	registry.skills[skill.id] = skill
	var errors := "\n".join(registry.validate())
	assert_string_contains(errors, "Skill 'broken': unknown element 'plasma'")
	assert_string_contains(errors, "requires unknown skill tree node 'nowhere'")
	assert_string_contains(errors, "cooldown must be above 0")
	assert_string_contains(errors, "does nothing")


func test_the_bot_casts_skills_and_levels_its_towers() -> void:
	var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
	var bot := AutoPlayer.new(sim)
	var casts: Array[int] = [0]
	sim.skill_used.connect(func(_skill: SkillData, _at: Vector2) -> void: casts[0] += 1)
	var best_level := 1
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 3600.0:
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
		if sim.state == RunSim.State.BUILDING:
			for tower in sim.towers:
				best_level = maxi(best_level, tower.level)
	gut.p("The bot cast %d skills; its best tower reached level %d" % [casts[0], best_level])
	assert_gt(casts[0], 5, "it uses its skills")
	assert_gt(best_level, 1, "it levels towers")


func test_a_bot_with_skills_and_levels_off_plays_like_before() -> void:
	var sim := RunSim.new(RunConfig.from_registry(registry, MAP))
	var bot := AutoPlayer.new(sim)
	bot.skills = false
	bot.upgrades = false
	var casts: Array[int] = [0]
	sim.skill_used.connect(func(_skill: SkillData, _at: Vector2) -> void: casts[0] += 1)
	var elapsed := 0.0
	while sim.wave_index < 3 and not sim.is_over() and elapsed < 600.0:
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	assert_eq(casts[0], 0)
	for tower in sim.towers:
		assert_eq(tower.level, 1)
