extends GutTest
## The bosses' own abilities (BossAbilities): healing, the barrier, binding towers, and Vael-Orrun's
## fireball that destroys a tower and leaves a burning ruin. Also that the bosses got their extra life.

const TEST_ROAD := preload("res://tests/support/test_road.tres")
const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	registry.maps[&"test_road"] = TEST_ROAD


func _sim(boss: StringName) -> RunSim:
	var config := RunConfig.from_registry(registry, &"test_road")
	var group := SpawnGroup.new()
	group.enemy = boss
	group.count = 1
	var wave := WaveData.new()
	wave.is_boss = true
	wave.groups = [group] as Array[SpawnGroup]
	var waves := WaveSet.new()
	waves.id = &"test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	config.wave_set = waves
	var sim := RunSim.new(config)
	sim.tree.points = 20
	sim.gold = 50000
	sim.allocate_node(&"fire_entry")
	sim.start_next_wave()
	for i in 30:
		sim._spawn(RunSim.STEP)
	return sim


func _tower(sim: RunSim, cell: Vector2i, near: SimEnemy) -> SimTower:
	var why := sim.placement_error(&"fire_brazier", cell)
	var tower := sim.place_tower(&"fire_brazier", cell)
	assert_not_null(tower, "placed at %s: %s" % [cell, why])
	tower.position = near.position + Vector2(40 + cell.x, 0)
	return tower


func _abilities(sim: RunSim) -> Array:
	var used: Array = []
	sim.boss_ability.connect(func(_boss: SimEnemy, ability: StringName, targets: Array) -> void:
		used.append([ability, targets]))
	return used


func _named(used: Array, ability: StringName) -> Array:
	return used.filter(func(entry: Array) -> bool: return entry[0] == ability)


func test_every_boss_got_more_life_and_vael_orrun_ten_times() -> void:
	assert_eq(registry.enemies[&"leviathan"].max_health, 13600.0, "the Leviathan: 3400 x4")
	assert_eq(registry.enemies[&"warden"].max_health, 4800.0, "the Ashdrake: 1200 x4")
	assert_eq(registry.enemies[&"vael_orrun"].max_health, 45000.0, "Vael-Orrun: 4500 x10")
	assert_eq(registry.enemies[&"vael_orrun_wrath"].max_health, 48000.0)
	assert_eq(registry.enemies[&"vael_orrun_unmade"].max_health, 48000.0)


func test_every_boss_but_the_shade_has_a_new_ability() -> void:
	for data: EnemyData in registry.enemies.values():
		if not data.tags.has(&"boss") or data.id == &"hollow_shade":
			continue
		var has_one := data.heal_interval > 0.0 or data.shield_interval > 0.0 or data.bind_interval > 0.0
		assert_true(has_one, "%s heals, shields or binds" % data.id)
		assert_false(data.boss_text().is_empty(), "%s explains its abilities in the codex" % data.id)


func test_vael_orrun_has_every_ability_in_every_form() -> void:
	for form: StringName in [&"vael_orrun", &"vael_orrun_wrath", &"vael_orrun_unmade"]:
		var data: EnemyData = registry.enemies[form]
		assert_gt(data.heal_interval, 0.0, "%s heals" % form)
		assert_gt(data.shield_interval, 0.0, "%s shields" % form)
		assert_gt(data.bind_interval, 0.0, "%s binds" % form)
		assert_gt(data.silence_interval, 0.0, "%s silences" % form)
		assert_eq(data.doom_interval, 200.0, "%s hurls a fireball every 200 s" % form)


func test_a_boss_heals_itself_but_not_while_burning() -> void:
	var sim := _sim(&"broodmother")
	var boss := sim.enemies[0]
	var used := _abilities(sim)
	boss.health = boss.max_health * 0.5
	boss.heal_timer = 0.0
	sim.boss_powers.tick(RunSim.STEP)
	assert_almost_eq(boss.health, boss.max_health * (0.5 + boss.data.heal_amount), 1.0)
	assert_eq(_named(used, &"heal").size(), 1)
	var burn := StatusEffectData.new()
	burn.kind = &"burn"
	burn.duration = 5.0
	boss.apply_status(burn, null, 1.0)
	var before := boss.health
	boss.heal_timer = 0.0
	sim.boss_powers.tick(RunSim.STEP)
	assert_eq(boss.health, before, "no heal while burning")
	assert_eq(_named(used, &"heal").size(), 1)
	assert_almost_eq(boss.heal_timer, BossAbilities.HEAL_RETRY, 0.05, "it tries again soon")


func test_boss_healing_stays_gentle() -> void:
	# Doctor Paris found the bosses' healing too strong: no boss heals more than 0.04%
	# of its life a second, from its heal and its regeneration together.
	for data: EnemyData in registry.enemies.values():
		if not data.tags.has(&"boss"):
			continue
		var per_second := data.regen_per_second
		if data.heal_interval > 0.0:
			per_second += data.heal_amount / data.heal_interval
		assert_lte(per_second, 0.0004, "%s heals %.3f%% a second" % [data.id, per_second * 100.0])


func test_boss_abilities_cut_to_a_tenth() -> void:
	# Doctor Paris found the bosses too powerful (2026-11-12): every heal, barrier, bind, silence
	# and ward was cut to a tenth of its strength, and fireballs and summons come ten times slower.
	for data: EnemyData in registry.enemies.values():
		if not data.tags.has(&"boss"):
			continue
		assert_lte(data.shield_amount, 0.015, "%s barrier" % data.id)
		assert_lte(data.heal_amount, 0.0025, "%s heal" % data.id)
		assert_lte(data.bind_duration, 0.3, "%s bind" % data.id)
		assert_lte(data.silence_duration, 0.3, "%s silence" % data.id)
		assert_lte(data.ward_reduction, 0.035, "%s ward" % data.id)
		assert_lte(data.enrage_speed, 1.1, "%s enrage" % data.id)
		if data.doom_interval > 0.0:
			assert_gte(data.doom_interval, 200.0, "%s fireball" % data.id)
		if not data.summon.is_empty():
			assert_gte(data.summon_interval, 25.0, "%s summons" % data.id)


func test_a_full_boss_waits_to_heal() -> void:
	var sim := _sim(&"leviathan")
	var boss := sim.enemies[0]
	var used := _abilities(sim)
	boss.heal_timer = 0.0
	sim.boss_powers.tick(RunSim.STEP)
	assert_eq(_named(used, &"heal").size(), 0, "no heal at full health")


func test_the_barrier_soaks_damage_then_breaks() -> void:
	var sim := _sim(&"mountain_titan")
	var boss := sim.enemies[0]
	var used := _abilities(sim)
	boss.shield_timer = 0.0
	sim.boss_powers.tick(RunSim.STEP)
	assert_eq(_named(used, &"shield").size(), 1)
	var barrier := boss.max_health * boss.data.shield_amount
	assert_almost_eq(boss.barrier, barrier, 0.1)
	sim._damage(boss, barrier * 0.5, null)
	assert_eq(boss.health, boss.max_health, "the barrier took it all")
	sim._damage(boss, barrier, null)
	assert_almost_eq(boss.health, boss.max_health - barrier * 0.5, 0.5, "the rest gets through")
	assert_eq(boss.barrier, 0.0)
	assert_eq(_named(used, &"shield_break").size(), 1)


func test_the_barrier_fades() -> void:
	var sim := _sim(&"mountain_titan")
	var boss := sim.enemies[0]
	boss.shield_timer = 0.0
	sim.boss_powers.tick(RunSim.STEP)
	for i in roundi((boss.data.shield_duration + 0.5) / RunSim.STEP):
		sim.boss_powers.tick(RunSim.STEP)
	assert_eq(boss.barrier, 0.0)


func test_bind_stops_the_strongest_towers_in_reach() -> void:
	var sim := _sim(&"thunderhead")
	var boss := sim.enemies[0]
	var used := _abilities(sim)
	var towers: Array[SimTower] = []
	for x in 4:
		towers.append(_tower(sim, Vector2i(8 + x * 2, 4), boss))
	var far := sim.place_tower(&"fire_brazier", Vector2i(20, 12))
	far.position = boss.position + Vector2(5000, 0)
	# Placing a tower recomputes every tower's stats, so the strengths are set after.
	towers[2].damage *= 3.0
	towers[3].damage *= 2.0
	far.damage *= 10.0
	boss.bind_timer = 0.0
	sim.boss_powers.tick(RunSim.STEP)
	var bound: Array = _named(used, &"bind")[0][1]
	assert_eq(bound.size(), boss.data.bind_count, "binds %d towers" % boss.data.bind_count)
	assert_true(bound.has(towers[2]) and bound.has(towers[3]), "the two strongest in reach")
	assert_eq(far.silenced, 0.0, "a tower out of reach is safe")
	assert_almost_eq(towers[2].silenced, boss.data.bind_duration, 0.01)
	assert_eq(towers[0].silenced, 0.0)


func test_vael_orrun_fireball_destroys_a_tower_and_leaves_a_ruin() -> void:
	var sim := _sim(&"vael_orrun")
	var boss := sim.enemies[0]
	var used := _abilities(sim)
	var weak := _tower(sim, Vector2i(8, 4), boss)
	var strong := _tower(sim, Vector2i(10, 4), boss)
	var hero_like := _tower(sim, Vector2i(12, 4), boss)
	strong.damage *= 4.0
	hero_like.damage *= 100.0
	hero_like.hero = registry.heroes.values()[0]
	boss.doom_timer = 0.0
	# Nothing else interferes: only the fireball.
	boss.bind_timer = 999.0
	sim.boss_powers.tick(RunSim.STEP)
	var cast := _named(used, &"fireball")
	assert_eq(cast.size(), 1, "it hurls a fireball")
	assert_eq(cast[0][1][0], strong, "at the strongest tower, never a hero")
	assert_true(sim.towers.has(strong), "the ball is still in the air")
	for i in roundi((BossAbilities.FIREBALL_FLIGHT + 0.1) / RunSim.STEP):
		sim.boss_powers.tick(RunSim.STEP)
	assert_false(sim.towers.has(strong), "the tower is destroyed")
	assert_true(sim.towers.has(weak))
	assert_eq(_named(used, &"destroy_tower").size(), 1)
	assert_true(sim.boss_powers.is_ruin(Vector2i(10, 4)))
	assert_eq(sim.placement_error(&"fire_brazier", Vector2i(10, 4)), "The ruin still burns: build here once the wave is over")
	assert_almost_eq(boss.doom_timer, boss.data.doom_interval - BossAbilities.FIREBALL_FLIGHT - 0.1, 0.1, "the next comes a full interval after")
	sim.boss_powers.clear()
	assert_true(sim.placement_error(&"fire_brazier", Vector2i(10, 4)).is_empty(), "the ruin is cleared after the wave")


func test_a_tower_sold_under_the_fireball_is_not_lost_twice() -> void:
	var sim := _sim(&"vael_orrun")
	var boss := sim.enemies[0]
	var used := _abilities(sim)
	var tower := _tower(sim, Vector2i(8, 4), boss)
	boss.doom_timer = 0.0
	boss.bind_timer = 999.0
	sim.boss_powers.tick(RunSim.STEP)
	var gold := sim.gold
	assert_gt(sim.sell_tower(tower), 0)
	for i in roundi((BossAbilities.FIREBALL_FLIGHT + 0.1) / RunSim.STEP):
		sim.boss_powers.tick(RunSim.STEP)
	assert_gt(sim.gold, gold)
	assert_eq(_named(used, &"destroy_tower").size(), 0)
	assert_false(sim.boss_powers.is_ruin(Vector2i(8, 4)))


func test_a_new_form_starts_without_the_old_barrier() -> void:
	var sim := _sim(&"vael_orrun")
	var boss := sim.enemies[0]
	boss.shield_timer = 0.0
	sim.boss_powers.tick(RunSim.STEP)
	assert_gt(boss.barrier, 0.0)
	boss.barrier = 0.0
	sim._damage(boss, boss.health + 1.0, null)
	assert_eq(boss.data.id, &"vael_orrun_wrath", "he changes form")
	assert_eq(boss.barrier, 0.0)
	assert_gt(boss.doom_timer, 0.0, "the fireball timer starts afresh")


func test_old_tricks_are_announced_too() -> void:
	var sim := _sim(&"vholt")
	var boss := sim.enemies[0]
	var used := _abilities(sim)
	var tower := _tower(sim, Vector2i(8, 4), boss)
	tower.position = boss.position + Vector2(30, 0)
	boss.silence_timer = 0.0
	boss.blink_timer = 0.0
	sim._tick_boss_tricks(RunSim.STEP)
	assert_eq(_named(used, &"silence").size(), 1)
	assert_eq(_named(used, &"blink").size(), 1)
