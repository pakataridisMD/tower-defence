extends GutTest
## The scripted bot plays every campaign stage, with no meta tree bonuses. It levels towers and casts
## skills but follows one fixed plan, so if it can win, a person can. tools/campaign_balance.gd prints
## the details.

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const MAX_SIM_SECONDS := 4000.0

var registry: Node


func before_all() -> void:
	registry = DataRegistryScript.new()
	registry.reload()


func after_all() -> void:
	registry.free()


func test_the_bot_wins_every_stage() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	for campaign in meta.campaigns_in_order():
		for stage in campaign.stages:
			var sim := RunSim.new(meta.stage_config(stage.id))
			var bot := AutoPlayer.for_sim(sim)
			var elapsed := 0.0
			while not sim.is_over() and elapsed < MAX_SIM_SECONDS:
				bot.act()
				sim.step(RunSim.STEP)
				elapsed += RunSim.STEP
			gut.p("%s: %s after %d waves, %d of %d lives" % [stage.id, RunSim.State.keys()[sim.state],
				sim.wave_index, sim.lives, sim.starting_lives])
			assert_eq(sim.state, RunSim.State.WON, "the bot wins %s" % stage.id)
