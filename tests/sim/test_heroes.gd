extends GutTest
## Heroes: who joins when, the party, summoning, moving, levels, auras and every ability.

const TEST_ROAD := preload("res://tests/support/test_road.tres")

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"test_road"
## Buildable cells far from the road, so nothing there ends a wave early.
const FAR_CELL := Vector2i(0, 14)
const FAR_CELL_2 := Vector2i(1, 14)

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	# The small 24 x 15 road these tests were written against (the real maps are bigger and curved).
	registry.maps[&"test_road"] = TEST_ROAD


func _hero(id: StringName) -> HeroData:
	var hero: HeroData = registry.heroes.get(id)
	assert_not_null(hero, "hero %s exists" % id)
	return hero


## A run with these heroes in the party, and Fire taken so fire towers can be built.
func _sim(hero_ids: Array[StringName]) -> RunSim:
	var config := RunConfig.from_registry(registry, MAP)
	for id in hero_ids:
		config.heroes.append(_hero(id))
	var sim := RunSim.new(config)
	sim.tree.points = 5
	sim.allocate_node(&"fire_entry")
	return sim


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


## A free cell next to the road, so a hero there reaches enemies.
func _cell_by_road(sim: RunSim) -> Vector2i:
	for cell in sim.path_cell_list():
		for offset: Vector2i in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
			var next := cell + offset
			if sim.summon_error(sim.party[0].id, next).is_empty():
				return next
	return FAR_CELL


func test_sixteen_heroes_join_in_story_order() -> void:
	assert_eq(registry.heroes.size(), 16)
	assert_eq(registry.validate(), PackedStringArray())
	var order: Array = registry.heroes_in_order().map(func(h: HeroData) -> StringName: return h.id)
	assert_eq(order[0], &"tamsin")
	assert_eq(order[15], &"oswin")
	assert_eq(_hero(&"brannoc").joins_after, &"ember_2")
	assert_eq(_hero(&"ignar").joins_after, &"ember_4")
	assert_eq(_hero(&"ilyra").joins_after, &"converge_1")
	assert_eq(_hero(&"seraphel").joins_after, &"converge_2")
	assert_eq(_hero(&"oswin").arrives_in, &"converge_3")
	assert_eq(_hero(&"oswin").arrives_at_wave, 17)
	for hero: HeroData in registry.heroes.values():
		assert_eq(hero.attack.id, hero.id, "%s attacks as itself" % hero.id)
		assert_true(hero.attack.tags.has(&"hero"))
		assert_false(hero.ability.description.is_empty(), "%s's ability is described" % hero.id)
		assert_false(hero.ultimate_text.is_empty(), "%s's ultimate is described" % hero.id)


func test_heroes_join_as_their_stages_are_won() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var joined := meta.joined_heroes().map(func(h: HeroData) -> StringName: return h.id)
	assert_eq(joined, [&"tamsin"], "only Tamsin is there at the start")
	meta.profile.stage_stars[&"ember_2"] = 1
	assert_true(meta.is_hero_joined(&"brannoc"))
	assert_false(meta.is_hero_joined(&"ignar"))
	meta.profile.stage_stars[&"ember_4"] = 2
	meta.profile.stage_stars[&"converge_3"] = 1
	assert_true(meta.is_hero_joined(&"ignar"))
	assert_true(meta.is_hero_joined(&"oswin"), "Oswin stays once the capital is won")


func test_the_party_defaults_to_the_newest_heroes_and_holds_three() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	for stage in [&"ember_2", &"storm_2", &"nature_2", &"water_2"]:
		meta.profile.stage_stars[stage] = 1
	var party := meta.party().map(func(h: HeroData) -> StringName: return h.id)
	assert_eq(party, [&"kaela", &"sylvaine", &"mirelle"])
	assert_true(meta.toggle_party_hero(&"tamsin"))
	party = meta.party().map(func(h: HeroData) -> StringName: return h.id)
	assert_eq(party.size(), HeroData.MAX_PARTY)
	assert_true(party.has(&"tamsin"))
	assert_false(meta.toggle_party_hero(&"ignar"), "a hero who has not joined cannot be picked")
	var config := meta.add_heroes(meta.stage_config(&"converge_3"))
	assert_eq(config.heroes.size(), 3)
	assert_eq(config.arriving_heroes.map(func(h: HeroData) -> StringName: return h.id), [&"oswin"])


func test_the_party_is_saved() -> void:
	var profile := PlayerProfile.new()
	profile.hero_party = [&"tamsin", &"brannoc"]
	var loaded := PlayerProfile.from_dict(profile.to_dict())
	assert_eq(loaded.hero_party, [&"tamsin", &"brannoc"])


func test_a_hero_is_summoned_once_for_free_and_cannot_be_sold_or_upgraded() -> void:
	var sim := _sim([&"tamsin"])
	var gold := sim.gold
	assert_string_contains(sim.summon_error(&"brannoc", FAR_CELL), "not in your party")
	var path_cell: Vector2i = sim.path_cell_list()[0]
	assert_false(sim.summon_error(&"tamsin", path_cell).is_empty(), "not on the road")
	var tower := sim.summon_hero(&"tamsin", FAR_CELL)
	assert_not_null(tower)
	assert_true(tower.is_hero())
	assert_eq(sim.gold, gold, "summoning is free")
	assert_eq(sim.tower_at(FAR_CELL), tower)
	assert_string_contains(sim.summon_error(&"tamsin", FAR_CELL_2), "already")
	assert_eq(sim.sell_tower(tower), 0)
	assert_true(sim.towers.has(tower), "heroes cannot be sold")
	assert_false(sim.level_up(tower))
	assert_true(sim.hybrid_options(tower).is_empty())
	assert_false(sim.can_place(&"fire_brazier", FAR_CELL), "a tower cannot go on a hero")


func test_a_hero_moves_once_per_break() -> void:
	var sim := _sim([&"tamsin"])
	var tower := sim.summon_hero(&"tamsin", FAR_CELL)
	assert_true(sim.move_hero(tower, FAR_CELL_2))
	assert_eq(tower.cell, FAR_CELL_2)
	assert_null(sim.tower_at(FAR_CELL))
	assert_string_contains(sim.move_error(tower, FAR_CELL), "already moved")
	sim.start_next_wave()
	assert_string_contains(sim.move_error(tower, FAR_CELL), "between waves")


func test_a_hero_gains_a_level_each_wave_and_hits_harder() -> void:
	var sim := _sim([&"tamsin"])
	var tower := sim.summon_hero(&"tamsin", FAR_CELL)
	var damage := tower.damage
	assert_eq(tower.hero_level, 1)
	# A lone hero lets most of a wave through: enough lives that the run outlasts it.
	sim.lives = 999
	assert_true(sim.start_next_wave())
	for step in 40000:
		if sim.state != RunSim.State.WAVE:
			break
		sim.step(RunSim.STEP)
	assert_eq(tower.hero_level, 2)
	assert_almost_eq(tower.damage, damage * (1.0 + HeroData.DAMAGE_PER_LEVEL), 0.01)
	tower.hero_level = HeroData.MAX_LEVEL
	assert_eq(tower.hero_ability(), tower.hero.ultimate, "the ability grows at level %d" % HeroData.ULTIMATE_LEVEL)


## A hero helps, but the towers carry the run: a fresh hero hits about as hard as a base tower, and
## even at the top level it is worth a couple of towers, not a whole defence.
func test_a_hero_is_worth_a_tower_or_two_not_a_whole_defence() -> void:
	var sim := _sim([&"brannoc"])
	var hero := sim.summon_hero(&"brannoc", FAR_CELL)
	sim.gold = 1000
	var tower := sim.place_tower(&"fire_brazier", FAR_CELL_2)
	var tower_dps := tower.damage * tower.attacks_per_second
	assert_lt(hero.damage * hero.attacks_per_second, tower_dps * 1.5, "level 1")
	hero.hero_level = HeroData.MAX_LEVEL
	sim._recompute_towers()
	var top_dps := hero.damage * hero.attacks_per_second
	assert_gt(top_dps, tower_dps, "the top level beats a base tower")
	assert_lt(top_dps, tower_dps * 2.5, "but not by much")


func test_the_aura_lifts_towers_near_the_hero_only() -> void:
	var sim := _sim([&"kaela"])
	sim.gold = 1000
	var near := sim.place_tower(&"fire_brazier", FAR_CELL_2)
	var far := sim.place_tower(&"fire_brazier", Vector2i(23, 0)) if sim.can_place(&"fire_brazier", Vector2i(23, 0)) else null
	var speed := near.attacks_per_second
	sim.summon_hero(&"kaela", FAR_CELL)
	assert_almost_eq(near.attacks_per_second, speed * 1.12, 0.001, "Kaela's aura: +12% attack speed")
	if far != null:
		assert_almost_eq(far.attacks_per_second, speed, 0.001, "towers far away get nothing")


func test_ilyra_lifts_every_hero_a_level() -> void:
	var sim := _sim([&"tamsin", &"ilyra"])
	var tamsin := sim.summon_hero(&"tamsin", FAR_CELL)
	assert_eq(tamsin.hero_level_now(), 1)
	sim.summon_hero(&"ilyra", Vector2i(23, 14) if sim.summon_error(&"ilyra", Vector2i(23, 14)).is_empty() else FAR_CELL_2)
	assert_eq(tamsin.hero_level_now(), 2)


func test_abilities_only_work_during_a_wave_and_cool_down() -> void:
	var sim := _sim([&"aurath"])
	assert_string_contains(sim.hero_ability_error(&"aurath"), "Summon")
	sim.summon_hero(&"aurath", FAR_CELL)
	assert_string_contains(sim.hero_ability_error(&"aurath"), "during a wave")
	_wave_with_enemies(sim, 3)
	var health := sim.enemies.map(func(e: SimEnemy) -> float: return e.health)
	watch_signals(sim)
	assert_true(sim.use_hero_ability(&"aurath"))
	assert_signal_emitted(sim, "hero_ability_used")
	for i in sim.enemies.size():
		assert_lt(sim.enemies[i].health, health[i], "Skyfall hits every enemy")
	assert_string_contains(sim.hero_ability_error(&"aurath"), "ready in")
	assert_false(sim.use_hero_ability(&"aurath"))


func test_frozen_hour_holds_the_whole_board() -> void:
	var sim := _sim([&"mirelle"])
	sim.summon_hero(&"mirelle", FAR_CELL)
	_wave_with_enemies(sim, 3)
	assert_true(sim.use_hero_ability(&"mirelle"))
	for enemy in sim.enemies:
		if not enemy.data.tags.has(&"boss"):
			assert_eq(enemy.speed(), 0.0, "held in place")


func test_great_flood_pushes_enemies_back_and_its_ultimate_sends_them_to_the_start() -> void:
	var sim := _sim([&"thalassa"])
	sim.summon_hero(&"thalassa", FAR_CELL)
	_wave_with_enemies(sim, 3)
	_run(sim, 2.0)
	var before := {}
	for enemy in sim.enemies:
		before[enemy.id] = enemy.progress
	assert_true(sim.use_hero_ability(&"thalassa"))
	for enemy in sim.enemies:
		assert_lt(enemy.progress, before[enemy.id] + 0.001, "pushed back, not forward")
	var tower := sim.hero_tower(&"thalassa")
	tower.hero_level = HeroData.ULTIMATE_LEVEL
	tower.ability_cooldown = 0.0
	_run(sim, 1.0)
	assert_true(sim.use_hero_ability(&"thalassa"))
	for enemy in sim.enemies:
		if not enemy.data.tags.has(&"boss"):
			assert_eq(enemy.progress, 0.0)


func test_last_light_stops_leaks() -> void:
	var sim := _sim([&"ilyra"])
	sim.summon_hero(&"ilyra", FAR_CELL)
	_wave_with_enemies(sim, 1)
	assert_true(sim.use_hero_ability(&"ilyra"))
	var enemy := sim.enemies[0]
	enemy.progress = sim.lane_lengths[enemy.lane] - 1.0
	var lives := sim.lives
	sim.step(RunSim.STEP)
	assert_eq(sim.lives, lives, "no life is lost while the gate is warded")
	assert_lt(enemy.progress, 50.0, "the enemy is thrown back to the start")


func test_eclipse_lifts_gold_and_damage_for_a_while() -> void:
	var sim := _sim([&"nyxara"])
	sim.gold = 1000
	var tower := sim.place_tower(&"fire_brazier", FAR_CELL_2)
	var damage := tower.damage
	sim.summon_hero(&"nyxara", FAR_CELL)
	_wave_with_enemies(sim, 1)
	assert_true(sim.use_hero_ability(&"nyxara"))
	assert_almost_eq(tower.damage, damage * 1.2, 0.01)
	assert_eq(sim.gold_multiplier(), 1.5)
	_run(sim, 6.0)
	assert_eq(sim.gold_multiplier(), 1.0, "it wears off")


func test_cataclysm_lands_on_the_crowds() -> void:
	var sim := _sim([&"ignar"])
	sim.summon_hero(&"ignar", FAR_CELL)
	_wave_with_enemies(sim, 6)
	var points := sim.crowded_points(3, 96.0)
	assert_gt(points.size(), 0)
	var total := 0.0
	for enemy in sim.enemies:
		total += enemy.health
	assert_true(sim.use_hero_ability(&"ignar"))
	var after := 0.0
	for enemy in sim.enemies:
		after += enemy.health if enemy.alive else 0.0
	assert_lt(after, total)


func test_worldbreaker_swallows_weakened_enemies() -> void:
	var sim := _sim([&"orrok"])
	sim.summon_hero(&"orrok", FAR_CELL)
	_wave_with_enemies(sim, 1)
	var enemy := sim.enemies[0]
	enemy.health = enemy.max_health * 0.15
	assert_true(sim.use_hero_ability(&"orrok", enemy.position))
	assert_false(enemy.alive)


func test_every_ability_and_ultimate_can_be_cast() -> void:
	for hero: HeroData in registry.heroes.values():
		for level in [1, HeroData.MAX_LEVEL]:
			var sim := _sim([hero.id])
			var tower := sim.summon_hero(hero.id, FAR_CELL)
			tower.hero_level = level
			_wave_with_enemies(sim, 1)
			var ability := tower.hero_ability()
			assert_true(sim.use_hero_ability(hero.id, sim.enemies[0].position),
					"%s at level %d can cast %s" % [hero.id, level, ability.display_name])
			_run(sim, 0.5)


func test_oswin_arrives_at_wave_seventeen_of_the_capital() -> void:
	var config := RunConfig.from_registry(registry, MAP)
	config.heroes.append(_hero(&"tamsin"))
	config.arriving_heroes.append(_hero(&"oswin"))
	_hero(&"oswin").arrives_at_wave = 2
	var sim := RunSim.new(config)
	assert_eq(sim.party.size(), 1)
	watch_signals(sim)
	sim.start_next_wave()
	assert_eq(sim.party.size(), 1)
	sim.wave_index = 1
	sim.state = RunSim.State.BUILDING
	sim.start_next_wave()
	assert_signal_emitted(sim, "hero_arrived")
	assert_eq(sim.party.size(), 2)
	_hero(&"oswin").arrives_at_wave = 17


func test_a_full_run_with_heroes_is_won() -> void:
	var config := RunConfig.from_registry(registry, MAP)
	config.heroes.append(_hero(&"tamsin"))
	var sim := RunSim.new(config)
	var bot := AutoPlayer.for_sim(sim)
	for step in 400000:
		if sim.is_over():
			break
		if sim.state == RunSim.State.BUILDING:
			bot.play_build_phase()
			sim.start_next_wave()
		else:
			bot.use_skills()
			sim.step(RunSim.STEP)
	gut.p("Run ended %s after %d waves: %d lives" % [RunSim.State.keys()[sim.state], sim.wave_index, sim.lives])
	assert_eq(sim.state, RunSim.State.WON)
	assert_not_null(sim.hero_tower(&"tamsin"), "the bot summoned Tamsin")
