extends GutTest
## A run frozen into a save slot (RunSnapshot) and thawed again into a fresh RunSim. The data goes
## through JSON both ways, as it does on disk.

const TEST_ROAD := preload("res://tests/support/test_road.tres")
const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAP := &"test_road"
const CELL := Vector2i(3, 3)

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	registry.maps[&"test_road"] = TEST_ROAD


func _sim(hero_ids: Array[StringName] = []) -> RunSim:
	var config := RunConfig.from_registry(registry, MAP)
	for id in hero_ids:
		config.heroes.append(registry.heroes[id])
	return RunSim.new(config)


func _clear_wave(sim: RunSim) -> void:
	assert_true(sim.start_next_wave())
	var elapsed := 0.0
	while sim.state == RunSim.State.WAVE and elapsed < 300.0:
		sim.step(0.05)
		elapsed += 0.05
	assert_eq(sim.state, RunSim.State.BUILDING, "the wave ends")


## Through JSON and back, as a slot file would.
func _through_json(data: Dictionary) -> Dictionary:
	var parsed: Variant = JSON.parse_string(JSON.stringify(data))
	assert_true(parsed is Dictionary)
	return parsed


func _free_cell(sim: RunSim, hero: StringName) -> Vector2i:
	for cell in sim.path_cell_list():
		for offset: Vector2i in [Vector2i(0, 1), Vector2i(0, -1), Vector2i(1, 0), Vector2i(-1, 0)]:
			if sim.summon_error(hero, cell + offset).is_empty():
				return cell + offset
	return Vector2i(-1, -1)


## A run two waves in: a levelled fire tower, the skill web, a summoned hero, gold and lives spent.
func _played() -> RunSim:
	var sim := _sim([&"tamsin"])
	# The skirmish waves are three times as tough as they were (gen_campaign.SKIRMISH_HARDNESS), and
	# one tower and a hero do not hold them: plenty of lives, as this test is about saving, not balance.
	sim.lives = 500
	sim.tree.points = 4
	assert_true(sim.allocate_node(&"fire_entry"))
	sim.gold = 2000
	var tower := sim.place_tower(&"fire_brazier", CELL)
	assert_not_null(tower)
	assert_true(sim.level_up(tower))
	assert_not_null(sim.summon_hero(&"tamsin", _free_cell(sim, &"tamsin")))
	_clear_wave(sim)
	_clear_wave(sim)
	sim.lives -= 3
	return sim


func test_a_run_comes_back_as_it_was() -> void:
	var sim := _played()
	var data := _through_json(RunSnapshot.capture(sim))
	var thawed := _sim([&"tamsin"])
	assert_eq(RunSnapshot.restore(thawed, data), 0, "every tower fits back")
	assert_eq(thawed.state, RunSim.State.BUILDING)
	assert_eq(thawed.wave_index, sim.wave_index)
	assert_eq(thawed.wave_number(), 3)
	assert_eq(thawed.gold, sim.gold)
	assert_eq(thawed.lives, sim.lives)
	assert_eq(thawed.kills, sim.kills)
	assert_eq(thawed.tree.points, sim.tree.points)
	assert_true(thawed.tree.is_allocated(&"fire_entry"))
	assert_eq(thawed.towers.size(), sim.towers.size())
	var tower := thawed.tower_at(CELL)
	assert_not_null(tower)
	assert_eq(tower.data.id, &"fire_brazier")
	assert_eq(tower.level, 2)
	assert_eq(tower.price_paid, sim.tower_at(CELL).price_paid)
	assert_almost_eq(tower.damage, sim.tower_at(CELL).damage, 0.001, "stats are worked out again")
	var hero := thawed.hero_tower(&"tamsin")
	assert_not_null(hero, "the hero is back on the field")
	assert_eq(hero.hero_level, sim.hero_tower(&"tamsin").hero_level)
	assert_eq(hero.cell, sim.hero_tower(&"tamsin").cell)
	assert_eq(thawed.sell_value(tower), sim.sell_value(sim.tower_at(CELL)))


func test_a_thawed_run_plays_on() -> void:
	var sim := _played()
	var thawed := _sim([&"tamsin"])
	RunSnapshot.restore(thawed, _through_json(RunSnapshot.capture(sim)))
	_clear_wave(thawed)
	assert_eq(thawed.wave_index, 3)
	assert_true(thawed.level_up(thawed.tower_at(CELL)), "towers still upgrade")
	assert_null(thawed.place_tower(&"fire_brazier", CELL), "the cell is taken")


func test_a_snapshot_from_the_break_goes_back_to_the_break() -> void:
	var sim := _played()
	var at_start := RunSnapshot.capture(sim)
	assert_true(sim.start_next_wave())
	for i in 200:
		sim.step(RunSim.STEP)
	assert_false(at_start.is_empty())
	var thawed := _sim([&"tamsin"])
	RunSnapshot.restore(thawed, _through_json(at_start))
	assert_eq(thawed.state, RunSim.State.BUILDING)
	assert_eq(thawed.wave_number(), 3, "back to the start of wave 3")
	assert_true(thawed.enemies.is_empty())
	assert_true(thawed.start_next_wave())


func test_a_tower_that_no_longer_exists_is_paid_back() -> void:
	var sim := _played()
	var data := _through_json(RunSnapshot.capture(sim))
	var paid := 0
	for entry: Dictionary in data["towers"]:
		if entry.has("type"):
			entry["type"] = "tower_from_an_old_version"
			paid += int(entry["price_paid"])
	var thawed := _sim([&"tamsin"])
	assert_eq(RunSnapshot.restore(thawed, data), paid)
	assert_eq(thawed.gold, sim.gold + paid)
	assert_null(thawed.tower_at(CELL))


func test_junk_is_not_a_run() -> void:
	var thawed := _sim()
	assert_eq(RunSnapshot.restore(thawed, {"hello": 1}), -1)
	assert_eq(thawed.wave_index, 0)


## The strongest check: a campaign run the bot played for a few waves is frozen in a break, and the
## original and the thawed copy then fight the same next wave untouched. Anything the snapshot
## forgot would make them come out differently.
func test_a_thawed_campaign_run_fights_the_next_wave_exactly_like_the_original() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var config := meta.add_heroes(meta.stage_config(&"ember_2"))
	var sim := RunSim.new(config)
	var bot := AutoPlayer.for_sim(sim)
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 3000.0 and not (sim.wave_index >= 3 and sim.state == RunSim.State.BUILDING):
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	assert_eq(sim.state, RunSim.State.BUILDING, "the bot reaches the break before wave 4")
	assert_gt(sim.towers.size(), 2)
	var thawed := RunSim.new(meta.add_heroes(meta.stage_config(&"ember_2")))
	assert_eq(RunSnapshot.restore(thawed, _through_json(RunSnapshot.capture(sim))), 0)
	for run: RunSim in [sim, thawed]:
		assert_true(run.start_next_wave())
		var t := 0.0
		while run.state == RunSim.State.WAVE and t < 600.0:
			run.step(RunSim.STEP)
			t += RunSim.STEP
	assert_eq(thawed.wave_index, sim.wave_index)
	assert_eq(thawed.gold, sim.gold)
	assert_eq(thawed.lives, sim.lives)
	assert_eq(thawed.kills, sim.kills)
	assert_eq(thawed.tree.points, sim.tree.points)
	for i in sim.towers.size():
		assert_almost_eq(thawed.towers[i].damage_dealt, sim.towers[i].damage_dealt, 0.01,
				"tower %d did the same damage" % i)


func test_an_assault_keeps_the_fallen_buildings() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var sim := RunSim.new(meta.stage_config(&"assault_1"))
	assert_true(sim.is_assault())
	var data := _through_json(RunSnapshot.capture(sim))
	data["structures"][0]["alive"] = false
	data["structures"][0]["health"] = 0.0
	data["structure_phase"] = 2
	data["wave_index"] = 12
	var thawed := RunSim.new(meta.stage_config(&"assault_1"))
	RunSnapshot.restore(thawed, data)
	assert_false(thawed.structures[0].alive)
	assert_eq(thawed.structure_phase, 2)
	assert_eq(thawed.wave_number(), 13)
	assert_true(thawed.start_next_wave())
