extends GutTest
## The thirty kinds of the six hordes (tools/campaign/horde.py) each have their own power. One test or
## more for each: what it does in the sim, with the numbers read from its data.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")

const HORDE: Array[StringName] = [
	&"brinecaller", &"netcaster", &"mire_eel", &"fogwife", &"rimeback",
	&"oathbroken", &"quarry_hound", &"runebearer", &"geode", &"menhir",
	&"lightdrinker", &"umbral_stalker", &"gravecaller", &"wailing_widow", &"voidmaw",
	&"cinderhound", &"smoke_wraith", &"glass_singer", &"slagwalker", &"brass_juggernaut",
	&"gale_harpy", &"spark_wisp", &"voiceless", &"stormrider", &"squall_witch",
	&"briarling", &"seedsower", &"greenwitch", &"briar_stag", &"barkhulk",
]

var registry: Node
var seen: Array = []


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	seen = []


func _sim(groups: Array[SpawnGroup]) -> RunSim:
	var config := RunConfig.from_registry(registry, &"switchback")
	var wave := WaveData.new()
	wave.element = &"fire"
	wave.groups = groups
	var waves := WaveSet.new()
	waves.id = &"test"
	waves.health_growth = 1.0
	waves.waves = [wave] as Array[WaveData]
	config.wave_set = waves
	var sim := RunSim.new(config)
	sim.tree.points = 20
	sim.gold = 5000
	sim.enemy_power.connect(func(e: SimEnemy, power: StringName, targets: Array) -> void: seen.append([e, power, targets]))
	return sim


func _group(enemy: StringName, count: int = 1) -> SpawnGroup:
	var group := SpawnGroup.new()
	group.enemy = enemy
	group.count = count
	group.spawn_interval = 0.1
	return group


## Spawns the wave, with every enemy carrying its power and standing at the same spot.
func _spawn_all(sim: RunSim) -> void:
	sim.start_next_wave()
	for i in 200:
		sim._spawn(RunSim.STEP)
	for enemy in sim.enemies:
		enemy.has_power = true
		enemy.position = sim.enemies[0].position
		enemy.progress = sim.enemies[0].progress
		enemy.lane = sim.enemies[0].lane


func _of(sim: RunSim, id: StringName) -> Array[SimEnemy]:
	var found: Array[SimEnemy] = []
	for enemy in sim.enemies:
		if enemy.data.id == id:
			found.append(enemy)
	return found


func _effect(kind: StringName, dps := 0.0, slow := 0.0) -> StatusEffectData:
	var spec := StatusEffectData.new()
	spec.kind = kind
	spec.duration = 5.0
	spec.damage_per_second = dps
	spec.slow = slow
	return spec


func _tower(sim: RunSim, at: Vector2, damage := 10.0) -> SimTower:
	var data: TowerData = registry.towers.values()[0]
	var tower := SimTower.new(sim._new_id(), data, Vector2i.ZERO, at, 0, [] as Array[int])
	tower.damage = damage
	tower.attacks_per_second = 2.0
	tower.attack_range = 200.0
	tower.splash_radius = 0.0
	tower.armour_ignore = 0.0
	sim.towers.append(tower)
	return tower


func _powers(name: StringName) -> Array:
	return seen.filter(func(entry: Array) -> bool: return entry[1] == name)


## Ticks the powers for `seconds` in small steps.
func _tick(sim: RunSim, seconds: float) -> void:
	var left := seconds
	while left > 0.0:
		sim._tick_powers(minf(0.05, left))
		left -= 0.05


func _use(sim: RunSim, enemy: SimEnemy) -> void:
	enemy.power_timer = 0.0
	sim._tick_powers(0.01)


# ------------------------------------------------------------------ every kind

func test_every_horde_kind_has_a_power_lore_and_art() -> void:
	for id in HORDE:
		var data: EnemyData = registry.enemies.get(id)
		assert_not_null(data, "%s is in the registry" % id)
		if data == null:
			continue
		assert_false(data.power.is_empty(), "%s has a power" % id)
		assert_false(data.power_text().is_empty(), "%s explains its power" % id)
		assert_false(data.lore.is_empty(), "%s has lore" % id)
		assert_false(data.horde.is_empty(), "%s belongs to a horde" % id)
		var art := BoardArt.enemy_info(id)
		assert_false(art.is_empty(), "%s has art" % id)
		assert_true(art.has("power") and art.has("death"), "%s has power and death frames" % id)


# ------------------------------------------------------------------ the Tide

func test_a_brinecaller_washes_off_burns_poisons_and_slows() -> void:
	var sim := _sim([_group(&"brinecaller", 2)])
	_spawn_all(sim)
	var other := sim.enemies[1]
	other.apply_status(_effect(&"poison", 5.0), null, 1.0)
	other.apply_status(_effect(&"slow", 0.0, 0.5), null, 1.0)
	_use(sim, sim.enemies[0])
	assert_false(other.has_status(&"poison"))
	assert_false(other.is_slowed())
	assert_eq(_powers(&"douse").size(), 1)


func test_a_brinecaller_waits_while_nobody_needs_washing() -> void:
	var sim := _sim([_group(&"brinecaller")])
	_spawn_all(sim)
	_use(sim, sim.enemies[0])
	assert_eq(_powers(&"douse").size(), 0)


func test_a_netcaster_slows_the_strongest_tower_near() -> void:
	var sim := _sim([_group(&"netcaster")])
	_spawn_all(sim)
	var caster := sim.enemies[0]
	var weak := _tower(sim, caster.position + Vector2(40, 0), 5.0)
	var strong := _tower(sim, caster.position + Vector2(-40, 0), 50.0)
	_use(sim, caster)
	assert_gt(strong.net_left, 0.0)
	assert_eq(weak.net_left, 0.0)
	assert_almost_eq(strong.rate_now(), 2.0 * (1.0 - caster.data.power_amount), 0.001)
	strong.tick_hexes(caster.data.power_duration + 0.1)
	assert_eq(strong.rate_now(), 2.0, "the net wears off")


func test_a_mire_eel_dives_out_of_reach_and_swims_faster() -> void:
	var sim := _sim([_group(&"mire_eel")])
	_spawn_all(sim)
	var eel := sim.enemies[0]
	eel.apply_status(_effect(&"burn", 5.0), null, 1.0)
	_use(sim, eel)
	assert_true(eel.untouchable())
	assert_true(eel.statuses.is_empty(), "the water puts out what clung to it")
	assert_almost_eq(eel.speed(), eel.base_speed * (1.0 + eel.data.power_amount), 0.01)
	var tower := _tower(sim, eel.position)
	var before := eel.health
	sim._hit(tower, eel, 50.0)
	assert_eq(eel.health, before)
	_tick(sim, eel.data.power_duration + 0.1)
	assert_false(eel.untouchable(), "it surfaces")


func test_a_fogwife_shortens_the_towers_reach() -> void:
	var sim := _sim([_group(&"fogwife")])
	_spawn_all(sim)
	var wife := sim.enemies[0]
	var near := _tower(sim, wife.position + Vector2(60, 0))
	var far := _tower(sim, wife.position + Vector2(wife.data.power_radius + 50.0, 0))
	_use(sim, wife)
	assert_almost_eq(near.range_now(), 200.0 * (1.0 - wife.data.power_amount), 0.01)
	assert_eq(far.range_now(), 200.0)


func test_a_rimeback_shell_soaks_hits_then_breaks() -> void:
	var sim := _sim([_group(&"rimeback")])
	_spawn_all(sim)
	var beast := sim.enemies[0]
	var shell := beast.max_health * beast.data.power_amount
	assert_almost_eq(beast.shell, shell, 0.01, "it walks in with its shell on")
	sim._damage(beast, shell * 0.5, null)
	assert_eq(beast.health, beast.max_health, "the shell takes it")
	sim._damage(beast, shell, null)
	assert_eq(beast.shell, 0.0)
	assert_lt(beast.health, beast.max_health, "what is left over gets through")
	assert_eq(_powers(&"shell_break").size(), 1)
	_use(sim, beast)
	assert_almost_eq(beast.shell, shell, 0.01, "it grows a new one")


# ------------------------------------------------------------------ the Stone Host

func test_an_oathbroken_grows_armour_with_every_hit_up_to_its_limit() -> void:
	var sim := _sim([_group(&"oathbroken")])
	_spawn_all(sim)
	var knight := sim.enemies[0]
	var tower := _tower(sim, knight.position, 1.0)
	var start := knight.armour
	for i in 3:
		sim._hit(tower, knight, 1.0)
	assert_almost_eq(knight.armour, start + 3.0 * knight.data.power_amount, 0.01)
	for i in 30:
		sim._hit(tower, knight, 1.0)
	assert_almost_eq(knight.armour, start + knight.data.power_limit * knight.data.power_amount, 0.01)


func test_a_quarry_hound_charges_through_slows() -> void:
	var sim := _sim([_group(&"quarry_hound")])
	_spawn_all(sim)
	var hound := sim.enemies[0]
	hound.apply_status(_effect(&"slow", 0.0, 0.6), null, 1.0)
	_use(sim, hound)
	assert_false(hound.is_slowed())
	assert_almost_eq(hound.speed(), hound.base_speed * (1.0 + hound.data.power_amount), 0.01)
	hound.apply_status(_effect(&"slow", 0.0, 0.6), null, 1.0)
	assert_almost_eq(hound.speed(), hound.base_speed * (1.0 + hound.data.power_amount), 0.01, "no slow holds it")
	assert_eq(hound.knock_back(30.0), 0.0)


func test_a_runebearer_lends_armour_to_the_ranks_near_it() -> void:
	var sim := _sim([_group(&"runebearer"), _group(&"oathbroken")])
	_spawn_all(sim)
	var knight: SimEnemy = _of(sim, &"oathbroken")[0]
	var bearer: SimEnemy = _of(sim, &"runebearer")[0]
	sim._tick_horde_auras(0.05)
	assert_eq(knight.bonus_armour, bearer.data.power_amount)
	assert_eq(bearer.bonus_armour, 0.0, "not to itself")
	knight.position += Vector2(bearer.data.power_radius + 50.0, 0)
	sim._tick_horde_auras(0.05)
	assert_eq(knight.bonus_armour, 0.0)


func test_a_geode_takes_less_from_splash_and_chains() -> void:
	var sim := _sim([_group(&"geode", 2)])
	_spawn_all(sim)
	var plain := _tower(sim, sim.enemies[0].position, 100.0)
	var blast := _tower(sim, sim.enemies[0].position, 100.0)
	blast.splash_radius = 40.0
	var a := sim.enemies[0]
	var b := sim.enemies[1]
	sim._hit(plain, a, 100.0)
	sim._hit(blast, b, 100.0)
	var lost_a := a.max_health - a.health
	var lost_b := b.max_health - b.health
	assert_almost_eq(lost_b, lost_a * (1.0 - b.data.power_amount), 0.01)


func test_a_menhir_steadies_the_ranks_against_slows_and_pushes() -> void:
	var sim := _sim([_group(&"menhir"), _group(&"oathbroken")])
	_spawn_all(sim)
	var knight: SimEnemy = _of(sim, &"oathbroken")[0]
	knight.apply_status(_effect(&"slow", 0.0, 0.5), null, 1.0)
	sim._tick_horde_auras(0.05)
	assert_true(knight.steady)
	assert_eq(knight.speed(), knight.base_speed)
	assert_eq(knight.knock_back(40.0), 0.0)


# ------------------------------------------------------------------ the Hollow

func test_a_lightdrinker_dims_the_towers_damage() -> void:
	var sim := _sim([_group(&"lightdrinker")])
	_spawn_all(sim)
	var drinker := sim.enemies[0]
	var tower := _tower(sim, drinker.position + Vector2(50, 0), 40.0)
	_use(sim, drinker)
	assert_almost_eq(tower.damage_now(), 40.0 * (1.0 - drinker.data.power_amount), 0.01)


func test_an_umbral_stalker_is_only_seen_up_close() -> void:
	var sim := _sim([_group(&"umbral_stalker")])
	_spawn_all(sim)
	var stalker := sim.enemies[0]
	var far := _tower(sim, stalker.position + Vector2(160, 0))
	var near := _tower(sim, stalker.position + Vector2(60, 0))
	sim._rebuild_hash()
	assert_null(sim._find_target(far), "within range, but too far to see it")
	assert_eq(sim._find_target(near), stalker)


func test_a_gravecaller_raises_the_fallen_who_pay_nothing() -> void:
	var sim := _sim([_group(&"gravecaller"), _group(&"oathbroken", 3)])
	_spawn_all(sim)
	var caller: SimEnemy = _of(sim, &"gravecaller")[0]
	for knight in _of(sim, &"oathbroken"):
		sim._damage(knight, 99999.0, null)
	_use(sim, caller)
	var raised: Array = _powers(&"raise")[0][2]
	assert_eq(raised.size(), int(caller.data.power_limit), "only so many at a time")
	for child: SimEnemy in raised:
		assert_true(child.raised)
		assert_false(child.has_power)
		assert_almost_eq(child.health, child.max_health * caller.data.power_amount, 0.01)
	sim._tick_powers(0.01)
	sim._spawn(RunSim.STEP)
	var gold := sim.gold
	sim._kill(raised[0], null)
	assert_eq(sim.gold, gold, "the raised dead pay no bounty")


func test_a_wailing_widow_silences_towers_as_she_dies() -> void:
	var sim := _sim([_group(&"wailing_widow")])
	_spawn_all(sim)
	var widow := sim.enemies[0]
	var tower := _tower(sim, widow.position + Vector2(50, 0))
	sim._damage(widow, 99999.0, tower)
	assert_almost_eq(tower.silenced, widow.data.power_duration, 0.01)


func test_a_voidmaw_feeds_on_the_dying_near_it() -> void:
	var sim := _sim([_group(&"voidmaw"), _group(&"briarling")])
	_spawn_all(sim)
	var maw: SimEnemy = _of(sim, &"voidmaw")[0]
	sim._damage(maw, maw.max_health * 0.5, null)
	var before := maw.health
	sim._damage(_of(sim, &"briarling")[0], 99999.0, null)
	assert_almost_eq(maw.health, before + maw.max_health * maw.data.power_amount, 0.01)


# ------------------------------------------------------------------ the Flame

func test_a_cinderhound_drinks_fire_and_shakes_off_chills() -> void:
	var sim := _sim([_group(&"cinderhound")])
	_spawn_all(sim)
	var hound := sim.enemies[0]
	sim._damage(hound, hound.max_health * 0.5, null)
	var before := hound.health
	hound.apply_status(_effect(&"burn", 10.0), null, 1.0)
	hound.apply_status(_effect(&"slow", 0.0, 0.5), null, 1.0)
	var slow_left: float = hound.statuses[&"slow"].time_left
	sim._tick_statuses(1.0)
	assert_gt(hound.health, before, "the burn heals it")
	assert_almost_eq(hound.statuses[&"slow"].time_left, slow_left - hound.data.power_amount, 0.01)


func test_a_smoke_wraith_lets_some_blows_pass_through() -> void:
	var sim := _sim([_group(&"smoke_wraith")])
	_spawn_all(sim)
	var wraith := sim.enemies[0]
	var tower := _tower(sim, wraith.position, 0.1)
	for i in 30:
		sim._hit(tower, wraith, 0.1)
	assert_eq(_powers(&"smoke").size(), int(30 * wraith.data.power_amount))


func test_a_glass_singer_wards_the_ones_ahead() -> void:
	var sim := _sim([_group(&"glass_singer"), _group(&"oathbroken", 4)])
	_spawn_all(sim)
	var singer: SimEnemy = _of(sim, &"glass_singer")[0]
	_use(sim, singer)
	var warded := _of(sim, &"oathbroken").filter(func(e: SimEnemy) -> bool: return e.shield_up)
	assert_eq(warded.size(), int(singer.data.power_limit))
	var knight: SimEnemy = warded[0]
	var tower := _tower(sim, knight.position)
	sim._hit(tower, knight, 50.0)
	assert_eq(knight.health, knight.max_health, "the ward takes the blow")
	assert_false(knight.shield_up, "and breaks")


func test_a_slagwalker_melts_its_armour_away_as_it_is_hit() -> void:
	var sim := _sim([_group(&"slagwalker")])
	_spawn_all(sim)
	var slag := sim.enemies[0]
	var tower := _tower(sim, slag.position, 1.0)
	var start := slag.armour
	sim._hit(tower, slag, 50.0)
	assert_almost_eq(slag.armour, start - slag.data.power_amount, 0.01)
	for i in 20:
		sim._hit(tower, slag, 1.0)
	assert_eq(slag.armour, 0.0)
	assert_eq(_powers(&"meltdown").size(), 1)


func test_a_brass_juggernaut_gathers_speed_until_checked() -> void:
	var sim := _sim([_group(&"brass_juggernaut")])
	_spawn_all(sim)
	var jug := sim.enemies[0]
	for i in 100:
		sim._tick_horde_auras(0.1)
	assert_almost_eq(jug.momentum, jug.data.power_limit, 0.01)
	assert_almost_eq(jug.speed(), jug.base_speed * (1.0 + jug.data.power_limit), 0.01)
	jug.apply_status(_effect(&"slow", 0.0, 0.3), null, 1.0)
	sim._tick_horde_auras(0.1)
	assert_eq(jug.momentum, 0.0)


# ------------------------------------------------------------------ the Sky

func test_a_gale_harpy_carries_the_horde_forward() -> void:
	var sim := _sim([_group(&"gale_harpy"), _group(&"oathbroken")])
	_spawn_all(sim)
	var knight: SimEnemy = _of(sim, &"oathbroken")[0]
	var harpy: SimEnemy = _of(sim, &"gale_harpy")[0]
	var before := knight.progress
	_use(sim, harpy)
	assert_almost_eq(knight.progress, before + harpy.data.power_amount, 0.5)


func test_a_spark_wisp_shocks_the_tower_that_kills_it() -> void:
	var sim := _sim([_group(&"spark_wisp")])
	_spawn_all(sim)
	var wisp := sim.enemies[0]
	var tower := _tower(sim, wisp.position)
	sim._damage(wisp, 99999.0, tower)
	assert_almost_eq(tower.silenced, wisp.data.power_duration, 0.01)


func test_the_voiceless_hush_towers_effects() -> void:
	var sim := _sim([_group(&"voiceless"), _group(&"oathbroken")])
	_spawn_all(sim)
	var hushed := _tower(sim, sim.enemies[0].position + Vector2(40, 0))
	hushed.effects = [_effect(&"poison", 5.0)] as Array[StatusEffectData]
	sim._tick_horde_auras(0.05)
	assert_true(hushed.hushed)
	var knight: SimEnemy = _of(sim, &"oathbroken")[0]
	sim._hit(hushed, knight, 1.0)
	assert_false(knight.has_status(&"poison"))


func test_a_stormrider_is_spurred_on_by_hits() -> void:
	var sim := _sim([_group(&"stormrider")])
	_spawn_all(sim)
	var rider := sim.enemies[0]
	var tower := _tower(sim, rider.position, 0.1)
	for i in 10:
		sim._hit(tower, rider, 0.1)
	assert_almost_eq(rider.spur, rider.data.power_limit, 0.001)
	assert_almost_eq(rider.speed(), rider.base_speed * (1.0 + rider.data.power_limit), 0.01)
	sim._tick_horde_auras(rider.data.power_duration + 0.1)
	assert_eq(rider.spur, 0.0, "it calms down")


func test_a_squall_witch_blows_shots_out_of_the_air() -> void:
	var sim := _sim([_group(&"squall_witch")])
	_spawn_all(sim)
	var witch := sim.enemies[0]
	var shot := SimProjectile.new()
	shot.position = witch.position + Vector2(30, 0)
	shot.target = witch
	sim.projectiles.append(shot)
	_use(sim, witch)
	assert_true(shot.done)


# ------------------------------------------------------------------ the Grove

func test_briarlings_run_faster_in_a_pack() -> void:
	var sim := _sim([_group(&"briarling", 5)])
	_spawn_all(sim)
	sim._tick_horde_auras(0.05)
	var one := sim.enemies[0]
	assert_almost_eq(one.swarm, minf(one.data.power_limit, one.data.power_amount * 4.0), 0.001)


func test_a_seedsower_plants_briarlings_that_sprout_later() -> void:
	var sim := _sim([_group(&"seedsower")])
	_spawn_all(sim)
	var sower := sim.enemies[0]
	_use(sim, sower)
	assert_eq(sim._seeds.size(), 1)
	sim._tick_seeds(sower.data.power_duration + 0.1)
	assert_eq(sim._seeds.size(), 0)
	var sprouts: Array = _powers(&"sprout")[0][2]
	assert_eq(sprouts.size(), int(sower.data.power_amount))
	assert_eq((sprouts[0] as SimEnemy).data.id, &"briarling")


func test_a_greenwitch_turns_poison_into_medicine() -> void:
	var sim := _sim([_group(&"greenwitch"), _group(&"oathbroken")])
	_spawn_all(sim)
	var knight: SimEnemy = _of(sim, &"oathbroken")[0]
	sim._damage(knight, knight.max_health * 0.5, null)
	var before := knight.health
	knight.apply_status(_effect(&"poison", 10.0), null, 1.0)
	sim._tick_horde_auras(0.05)
	sim._tick_statuses(1.0)
	assert_gt(knight.health, before)


func test_a_briar_stag_bounds_out_of_a_slow() -> void:
	var sim := _sim([_group(&"briar_stag")])
	_spawn_all(sim)
	var stag := sim.enemies[0]
	_use(sim, stag)
	assert_eq(_powers(&"bound").size(), 0, "it waits until something slows it")
	stag.apply_status(_effect(&"slow", 0.0, 0.5), null, 1.0)
	var before := stag.progress
	_use(sim, stag)
	assert_false(stag.is_slowed())
	assert_almost_eq(stag.progress, before + stag.data.power_amount, 0.5)


func test_a_barkhulk_grows_bigger_over_time() -> void:
	var sim := _sim([_group(&"barkhulk")])
	_spawn_all(sim)
	var hulk := sim.enemies[0]
	var start := hulk.max_health
	for i in 20:
		_use(sim, hulk)
	assert_almost_eq(hulk.max_health, start * (1.0 + hulk.data.power_amount * hulk.data.power_limit), 0.5)
