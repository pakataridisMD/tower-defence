extends GutTest
## The campaign: its data, the order stages open in, stars, rewards, stage rules and saves.

const TEST_ROAD := preload("res://tests/support/test_road.tres")

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const ELEMENT_CAMPAIGNS: Array[StringName] = [
	&"ember_reach", &"thunder_steppe", &"verdant_deep", &"frostmere", &"sunscar_canyon", &"hollow_rift",
]

var registry: Node


func before_each() -> void:
	registry = autofree(DataRegistryScript.new())
	registry.reload()
	# The small 24 x 15 road these tests were written against (the real maps are bigger and curved).
	registry.maps[&"test_road"] = TEST_ROAD


func _meta(profile: PlayerProfile = null) -> MetaProgress:
	return MetaProgress.new(registry, profile if profile != null else PlayerProfile.new())


## A finished stage run, without playing it.
func _finished(meta: MetaProgress, stage_id: StringName, won: bool, lives_left: int) -> RunSim:
	var sim := RunSim.new(meta.stage_config(stage_id))
	sim.state = RunSim.State.WON if won else RunSim.State.LOST
	sim.lives = lives_left
	sim.wave_index = sim.total_waves() if won else 2
	return sim


func _win_campaign(meta: MetaProgress, campaign_id: StringName) -> void:
	for stage in (registry.campaigns[campaign_id] as CampaignData).stages:
		meta.profile.stage_stars[stage.id] = 1


func test_there_is_a_campaign_per_element_and_the_convergence() -> void:
	assert_eq(registry.campaigns.size(), 8)
	var elements: Array[StringName] = []
	for campaign: CampaignData in registry.campaigns.values():
		if not campaign.element.is_empty():
			elements.append(campaign.element)
			assert_eq(campaign.stages.size(), 4, campaign.id)
			assert_true(campaign.stages[-1].is_guardian, "%s ends with a Warden" % campaign.id)
	elements.sort()
	var all: Array[StringName] = []
	all.assign(registry.elements.keys())
	all.sort()
	assert_eq(elements, all)
	var convergence: CampaignData = registry.campaigns[&"convergence"]
	assert_eq(convergence.requires_campaigns.size(), 6)
	assert_eq(registry.stages.size(), 28)


func test_campaign_maps_stay_out_of_skirmish() -> void:
	var meta := _meta()
	for map in meta.maps_in_order():
		assert_true(map.skirmish, "%s is a skirmish map" % map.id)
	assert_false(meta.is_map_unlocked(&"c_ember_1"))
	assert_false(meta.select_map(&"c_ember_1"))


func test_each_element_campaign_favours_its_element() -> void:
	for campaign_id in ELEMENT_CAMPAIGNS:
		var campaign: CampaignData = registry.campaigns[campaign_id]
		var home := campaign.element
		var ring: int = registry.element_index(home)
		for stage in campaign.stages:
			assert_eq(stage.allowed_elements[0], home)
			assert_eq(stage.allowed_elements.size(), 3)
			for other in stage.allowed_elements.slice(1):
				assert_true(ElementRules.are_neighbours(ring, registry.element_index(other)), "%s: %s is a neighbour" % [stage.id, other])
			assert_eq(stage.starting_nodes, [StringName("%s_entry" % home)] as Array[StringName])
			var wave_set: WaveSet = registry.wave_sets[registry.maps[stage.map].wave_set]
			for wave in wave_set.waves:
				if wave.is_boss and stage.is_guardian and wave == wave_set.waves[-1]:
					continue
				var aligned: int = registry.element_index(wave.element)
				var weak_to := ElementRules.opposite_index(aligned)
				assert_true(stage.allowed_elements.any(func(e: StringName) -> bool: return registry.element_index(e) == weak_to),
						"%s: every wave is weak to an element you can draft" % stage.id)


func test_wardens_resist_their_home_element() -> void:
	for campaign_id in ELEMENT_CAMPAIGNS:
		var campaign: CampaignData = registry.campaigns[campaign_id]
		var guardian := campaign.stages[-1]
		var last: WaveData = registry.wave_sets[registry.maps[guardian.map].wave_set].waves[-1]
		assert_true(last.is_boss)
		var boss: EnemyData = registry.enemies[last.groups[0].enemy]
		assert_true(boss.tags.has(&"boss"))
		assert_eq(boss.element, campaign.element, "%s's Warden is %s" % [campaign_id, campaign.element])


func test_the_lands_open_one_after_another_and_the_convergence_last() -> void:
	var meta := _meta()
	assert_true(meta.is_stage_unlocked(&"ember_1"), "a new player starts in the Ember Reach")
	for i in ELEMENT_CAMPAIGNS.size():
		var campaign: CampaignData = registry.campaigns[ELEMENT_CAMPAIGNS[i]]
		assert_true(meta.is_stage_unlocked(campaign.stages[0].id), "%s opens after the land before it" % campaign.id)
		assert_false(meta.is_stage_unlocked(campaign.stages[1].id), campaign.stages[1].id)
		if i + 1 < ELEMENT_CAMPAIGNS.size():
			var next: CampaignData = registry.campaigns[ELEMENT_CAMPAIGNS[i + 1]]
			assert_false(meta.is_stage_unlocked(next.stages[0].id), "%s waits for %s" % [next.id, campaign.id])
		assert_false(meta.is_campaign_unlocked(&"convergence"))
		_win_campaign(meta, ELEMENT_CAMPAIGNS[i])
	assert_true(meta.is_stage_unlocked(&"converge_1"))


func test_winning_a_stage_opens_the_next() -> void:
	var meta := _meta()
	meta.record_stage(_finished(meta, &"ember_1", true, 20))
	assert_true(meta.is_stage_unlocked(&"ember_2"))
	assert_false(meta.is_stage_unlocked(&"ember_3"))
	assert_eq(meta.next_stage(registry.campaigns[&"ember_reach"]).id, &"ember_2")
	assert_eq(meta.stage_after(&"ember_1").id, &"ember_2")
	assert_null(meta.stage_after(&"ember_4"))


func test_a_loss_opens_nothing() -> void:
	var meta := _meta()
	var result := meta.record_stage(_finished(meta, &"ember_1", false, 0))
	assert_eq(result["stars"], 0)
	assert_eq(result["first_clear_points"], 0)
	assert_false(meta.is_stage_unlocked(&"ember_2"))


func test_stars_count_the_lives_kept() -> void:
	var meta := _meta()
	assert_eq(MetaProgress.stars_for(_finished(meta, &"ember_1", true, 20)), 3)
	assert_eq(MetaProgress.stars_for(_finished(meta, &"ember_1", true, 19)), 2)
	assert_eq(MetaProgress.stars_for(_finished(meta, &"ember_1", true, 10)), 2)
	assert_eq(MetaProgress.stars_for(_finished(meta, &"ember_1", true, 9)), 1)
	assert_eq(MetaProgress.stars_for(_finished(meta, &"ember_1", false, 9)), 0)


func test_the_first_win_pays_once_and_the_best_stars_are_kept() -> void:
	var meta := _meta()
	var points := meta.points()
	var first := meta.record_stage(_finished(meta, &"ember_1", true, 5))
	assert_eq(first["stars"], 1)
	assert_eq(first["first_clear_points"], 3)
	assert_eq(meta.points(), points + 3)
	var better := meta.record_stage(_finished(meta, &"ember_1", true, 20))
	assert_eq(better["first_clear_points"], 0, "paid only once")
	assert_eq(meta.stars(&"ember_1"), 3)
	meta.record_stage(_finished(meta, &"ember_1", true, 5))
	assert_eq(meta.stars(&"ember_1"), 3, "a worse win keeps the best")


func test_the_convergence_opens_after_all_six() -> void:
	var meta := _meta()
	for i in ELEMENT_CAMPAIGNS.size():
		assert_false(meta.is_campaign_unlocked(&"convergence"))
		_win_campaign(meta, ELEMENT_CAMPAIGNS[i])
		assert_true(meta.is_campaign_complete(ELEMENT_CAMPAIGNS[i]))
	assert_true(meta.is_stage_unlocked(&"converge_1"))
	assert_false(meta.is_stage_unlocked(&"converge_2"))


func test_finishing_a_campaign_says_so_once() -> void:
	var meta := _meta()
	for id: StringName in [&"ember_1", &"ember_2", &"ember_3"]:
		assert_false(meta.record_stage(_finished(meta, id, true, 20))["campaign_complete"])
	assert_true(meta.record_stage(_finished(meta, &"ember_4", true, 20))["campaign_complete"])
	assert_false(meta.record_stage(_finished(meta, &"ember_4", true, 20))["campaign_complete"], "not again")


func test_campaign_rewards_reach_every_run() -> void:
	var meta := _meta()
	var reward: Modifier = (registry.campaigns[&"ember_reach"] as CampaignData).reward_modifiers[0]
	assert_false(meta.run_config().run_modifiers.has(reward))
	_win_campaign(meta, &"ember_reach")
	assert_true(meta.run_config().run_modifiers.has(reward), "skirmish")
	assert_true(meta.stage_config(&"storm_1").run_modifiers.has(reward), "other campaigns")


func test_a_stage_closes_the_elements_it_does_not_allow() -> void:
	var meta := _meta()
	var sim := RunSim.new(meta.stage_config(&"ember_1"))
	assert_true(sim.tree.is_allocated(&"fire_entry"), "starts with Fire")
	assert_true(sim.is_unlocked(&"fire_brazier"))
	assert_false(sim.tree.can_refund(&"fire_entry"), "the free node stays")
	for id: StringName in [&"water_entry", &"nature_entry", &"earth_entry", &"bridge_bog", &"bridge_thornstorm"]:
		assert_true(sim.tree.is_locked(id), "%s is closed" % id)
	for id: StringName in [&"storm_entry", &"void_entry", &"bridge_plasma", &"bridge_soulflame"]:
		assert_false(sim.tree.is_locked(id), "%s is open" % id)
	assert_eq(sim.tree.points, registry.run_rules.starting_tree_points, "the free node costs nothing")


func test_stage_rules_change_the_run() -> void:
	var meta := _meta()
	var sim := RunSim.new(meta.stage_config(&"ember_1"))
	sim.tree.points = 10
	var free := Vector2i(-1, -1)
	for x in sim.config.map.grid_size.x:
		for y in sim.config.map.grid_size.y:
			if free.x < 0 and sim.can_place(&"fire_brazier", Vector2i(x, y)):
				free = Vector2i(x, y)
	var brazier := sim.place_tower(&"fire_brazier", free)
	var plain := RunSim.new(RunConfig.from_registry(registry, &"test_road"))
	plain.allocate_node(&"fire_entry")
	plain.gold = 1000
	var other := plain.place_tower(&"fire_brazier", Vector2i(5, 4))
	assert_almost_eq(brazier.damage, other.damage * 1.2, 0.001, "home ground")
	var lives_stage := RunSim.new(meta.stage_config(&"nature_2"))
	assert_eq(lives_stage.lives, registry.run_rules.starting_lives + 5)
	assert_eq(lives_stage.starting_lives, lives_stage.lives)


func test_save_keeps_the_stars_and_old_saves_still_load() -> void:
	var profile := PlayerProfile.new()
	profile.stage_stars[&"ember_1"] = 3
	profile.stage_stars[&"storm_2"] = 1
	var loaded := PlayerProfile.from_dict(JSON.parse_string(JSON.stringify(profile.to_dict())))
	assert_eq(loaded.stage_stars, profile.stage_stars)
	var old := PlayerProfile.from_dict({"version": 1, "meta_points_earned": 7})
	assert_eq(old.meta_points_earned, 7)
	assert_true(old.stage_stars.is_empty())
	var odd := PlayerProfile.from_dict({"version": 2, "campaign": {"stars": {"ember_1": 9, "x": "y", "": 2}}})
	assert_eq(odd.stage_stars, {&"ember_1": 3} as Dictionary[StringName, int], "bad entries are dropped, stars capped at 3")


func test_progress_plays_the_chosen_stage() -> void:
	Progress.use_memory_profile()
	assert_false(Progress.play_stage(&"ember_2"), "locked")
	assert_true(Progress.play_stage(&"ember_1"))
	assert_eq(Progress.run_config().stage.id, &"ember_1")
	Progress.play_skirmish()
	assert_null(Progress.run_config().stage)


func test_replaying_a_won_stage_pays_almost_nothing() -> void:
	var meta := _meta()
	var waves := RunSim.new(meta.stage_config(&"ember_1")).total_waves()
	var worth: int = registry.run_rules.meta_points_after_run(waves, true)
	assert_eq(meta.record_run(_finished(meta, &"ember_1", false, 0)), 2, "two waves cleared")
	assert_eq(meta.record_run(_finished(meta, &"ember_1", true, 5)), worth - 2, "the rest of the stage")
	var replays := 0
	for i in 20:
		replays += meta.record_run(_finished(meta, &"ember_1", true, 5))
	assert_eq(replays, MetaProgress.REPLAY_WIN_POINTS * MetaProgress.REPLAY_LIMIT, "twenty replays, capped")
	assert_eq(meta.record_run(_finished(meta, &"ember_2", false, 0)), 2, "other stages keep their own record")


func test_old_saves_lose_points_farmed_by_replays() -> void:
	var farmed := {"version": 3, "meta_points_earned": 5000, "meta_nodes": ["command_gold"],
		"campaign": {"stars": {"ember_1": 3}}}
	var profile := PlayerProfile.from_dict(farmed)
	assert_true(profile.needs_records)
	var meta := _meta(profile)
	var waves := RunSim.new(meta.stage_config(&"ember_1")).total_waves()
	var worth: int = registry.run_rules.meta_points_after_run(waves, true) + 3
	assert_eq(meta.profile.meta_points_earned, worth, "capped at what winning ember_1 is worth")
	assert_eq(meta.profile.run_records[&"ember_1"], worth - 3)
	assert_true(meta.tree.is_allocated(&"command_gold"), "nodes it can still afford stay taken")
	assert_eq(meta.record_run(_finished(meta, &"ember_1", true, 5)), MetaProgress.REPLAY_WIN_POINTS, "a replay now")
	var honest := _meta(PlayerProfile.from_dict({"version": 3, "meta_points_earned": 4}))
	assert_eq(honest.profile.meta_points_earned, 0, "nothing won, nothing kept")
