extends GutTest
## The army of the counter-attack comes alive: its shouts are written for every voice and hero and
## spoken one at a time, and on the board its units stand in ranks, cry out when they speak and wear
## health bars over their heads.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const KINDS := ["muster", "charge", "fight", "siege", "hurt", "death", "bolt", "crack", "victory"]
const HERO_KINDS := ["muster", "fight", "siege", "hurt", "death", "crack"]

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()


func _counter_sim() -> RunSim:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var sim := RunSim.new(meta.stage_config(&"assault_1"))
	sim.wave_index = sim.config.stage.counter_wave - 1
	sim.start_next_wave()
	sim.gold = 99999
	sim.lives = 9999
	return sim


func _voice(sim: RunSim, board: BoardView = null) -> ArmyVoice:
	var voice := ArmyVoice.new()
	add_child_autofree(voice)
	voice.setup(sim, board, 7)
	return voice


func test_every_unit_but_the_hounds_has_a_voice_and_every_hero_speaks() -> void:
	var voice := _voice(_counter_sim())
	for data: AllyData in registry.allies.values():
		if data.is_champion():
			var lines: Dictionary = voice.champions.get(String(data.hero), {})
			for kind in HERO_KINDS:
				assert_false((lines.get(kind, []) as Array).is_empty(), "%s has a %s line" % [data.hero, kind])
		elif data.id != &"warhound":
			assert_true(voice.unit_voice.has(data.id), "%s has a voice" % data.id)
	for troop_voice: String in voice.lines:
		for kind in KINDS:
			assert_false((voice.lines[troop_voice].get(kind, []) as Array).is_empty(), "%s has %s lines" % [troop_voice, kind])


func test_line_ids_are_unique_and_tags_are_hidden_from_the_words() -> void:
	var voice := _voice(_counter_sim())
	var seen := {}
	for table: Dictionary in voice.lines.values() + voice.champions.values():
		for kind: String in table:
			for entry: Dictionary in table[kind]:
				assert_false(seen.has(entry["id"]), "line id %s is used once" % entry["id"])
				seen[entry["id"]] = true
				assert_false(ArmyVoice.shown_text(entry["text"]).contains("["), "no tag shows in %s" % entry["id"])
	assert_eq(ArmyVoice.shown_text("[pained scream] Aaargh!"), "Aaargh!")


func test_a_squad_shouts_as_it_marches_out_and_a_hero_always_does() -> void:
	var sim := _counter_sim()
	var voice := _voice(sim)
	sim.muster(&"champion_tamsin", 0)
	assert_eq(voice.said.size(), 1)
	assert_eq(voice.said[0]["id"], "tamsin_muster")
	assert_gt(voice.busy(), 0.0, "the line takes time")
	# While Tamsin speaks, the footmen march out quietly.
	sim.muster(&"footman", 0)
	assert_eq(voice.said.size(), 1, "one line at a time")


func test_lines_stay_occasional_in_a_long_fight() -> void:
	var sim := _counter_sim()
	var voice := _voice(sim)
	for id in [&"footman", &"pikeman", &"crossbowman", &"ironbreaker", &"root_archer", &"lantern_cleric", &"gale_lancer"]:
		sim.muster(id, 0)
	var seconds := 120.0
	var steps := int(seconds / RunSim.STEP)
	for i in steps:
		sim.step(RunSim.STEP)
		voice.step(RunSim.STEP)
	var words := voice.said.filter(func(line: Dictionary) -> bool: return line["kind"] != &"death")
	assert_gt(words.size(), 3, "the army speaks during two minutes of battle")
	assert_lt(words.size(), int(seconds / ArmyVoice.GAP.x), "but never more than one line per quiet gap")


func test_the_army_roars_when_the_citadel_loses_a_quarter() -> void:
	var sim := _counter_sim()
	var voice := _voice(sim)
	sim.muster(&"footman", 0)
	voice.step(10.0)
	var citadel := sim.structures[0]
	citadel.health = citadel.max_health * 0.7
	voice.step(0.1)
	assert_eq(voice.said[-1]["kind"], &"crack")
	var count := voice.said.size()
	voice.step(10.0)
	assert_eq(voice.said.size(), count, "each quarter is roared once")


## On the board: units stand across the road in ranks, a speaker raises its weapon and its words show
## over its head, and every unit's health bar sits above its head.
func test_the_board_shows_the_army_alive() -> void:
	Progress.use_memory_profile()
	var stage_before := Progress.active_stage
	Progress.active_stage = &"assault_1"
	Progress.mark_seen(&"the_turning")
	var game: Game = add_child_autofree(preload("res://scenes/game/game.tscn").instantiate())
	Progress.active_stage = stage_before
	await wait_process_frames(2)
	var sim := game.sim
	assert_true(sim.is_counter_assault(), "the final level")
	sim.wave_index = sim.config.stage.counter_wave - 1
	sim.start_next_wave()
	sim.gold = 99999
	sim.lives = 9999
	var hero := sim.muster(&"champion_tamsin", 0)[0]
	var squad := sim.muster(&"footman", 0)
	await wait_process_frames(3)
	var army: AllyArt = game.board.art.army
	assert_eq(army.visual_count(), 1 + squad.size())
	# Tamsin calls the Lanternguard: she leaps with her war cry and her words show over her.
	assert_true(army.is_crying(hero), "the speaker cries out")
	assert_eq(army.anim_of(hero), &"cry")
	var words := game.board.speech()
	assert_eq(words.size(), 1)
	assert_eq(words[0][0], hero)
	assert_eq(words[0][1], ArmyVoice.shown_text(game.army_voice.champions["tamsin"]["muster"][0]["text"]))
	# The footmen stand in a rank across the road, and every bar is above its unit's head.
	var spots := {}
	for ally in squad:
		spots[army.anchor(ally).round()] = true
		assert_lt(army.top(ally).y, army.anchor(ally).y - 40.0, "%d: the head is well above the feet" % ally.id)
	assert_eq(spots.size(), squad.size(), "no two footmen on one spot")
	# A heavy blow makes a footman flinch.
	var footman := squad[1]
	footman.health -= footman.max_health * 0.3
	await wait_process_frames(2)
	assert_eq(army.anim_of(footman), &"hurt")


func test_ranks_spread_units_across_the_road() -> void:
	var sim := _counter_sim()
	var offsets := {}
	for i in 12:
		var ally := SimAlly.new(i, registry.allies[&"footman"], 1.0)
		offsets[snappedf(AllyArt.lateral_for(ally), 0.1)] = true
		assert_lte(absf(AllyArt.lateral_for(ally)), AllyArt.SPREAD)
	assert_gt(offsets.size(), 8, "a squad does not stand on one spot")
	var champion := SimAlly.new(99, registry.allies[&"champion_tamsin"], 1.0)
	assert_eq(AllyArt.lateral_for(champion), 0.0, "a hero keeps the middle of the road")
	assert_not_null(sim)


func test_every_line_is_recorded() -> void:
	var voice := _voice(_counter_sim())
	for table: Dictionary in [voice.lines, voice.champions]:
		for who: String in table:
			for kind: String in table[who]:
				for entry: Dictionary in table[who][kind]:
					var path := ArmyVoice.AUDIO_DIR + "%s/%s.ogg" % [who, entry["id"]]
					assert_true(ResourceLoader.exists(path), "recording " + path)
