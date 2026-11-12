extends GutTest
## The scripted bot plays every campaign stage as the player a new player would be by then: the meta
## tree, the sigils of the lands already finished and the heroes who have joined, from
## tools/campaign/meta_profiles.json (written by tools/meta_pacing.gd). It levels towers and casts
## skills but follows one fixed plan, so if it can win, a person can. tools/campaign_balance.gd
## prints the details.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const PROFILES := "res://tools/campaign/meta_profiles.json"
const MAX_SIM_SECONDS := 8000.0

var registry: Node
var profiles: Dictionary = {}


func before_all() -> void:
	registry = DataRegistryScript.new()
	registry.reload()
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PROFILES))
	if parsed is Dictionary:
		profiles = parsed


func after_all() -> void:
	registry.free()


func test_there_is_an_expected_profile_for_every_stage() -> void:
	for stage_id: StringName in registry.stages:
		assert_true(profiles.has(String(stage_id)), "%s has a profile in %s" % [stage_id, PROFILES])


func test_the_bot_wins_every_stage() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	for campaign in meta.campaigns_in_order():
		for stage in campaign.stages:
			var config := meta.stage_config(stage.id)
			if profiles.has(String(stage.id)):
				var expected := MetaProgress.new(registry, PlayerProfile.from_dict(profiles[String(stage.id)]))
				config = expected.add_heroes(expected.stage_config(stage.id))
			var sim := RunSim.new(config)
			var bot := AutoPlayer.for_sim(sim)
			var elapsed := 0.0
			while not sim.is_over() and elapsed < MAX_SIM_SECONDS:
				bot.act()
				sim.step(RunSim.STEP)
				elapsed += RunSim.STEP
			gut.p("%s: %s after %d waves, %d of %d lives" % [stage.id, RunSim.State.keys()[sim.state],
				sim.wave_index, sim.lives, sim.starting_lives])
			assert_eq(sim.state, RunSim.State.WON, "the bot wins %s" % stage.id)
