extends GutTest
## The expected profiles the campaign is tuned against: the player a new player would be by each stage
## (meta tree, sigils of the lands behind them, heroes), from tools/campaign/meta_profiles.json
## (written by tools/meta_pacing.gd).
##
## Whether the scripted bot wins every stage with them is checked by the "Campaign balance" job in
## .github/workflows/tests.yml: on the big maps with long waves a full pass takes over ten minutes,
## so it runs there four stages at a time (tools/campaign_balance.gd -- --check).

const DataRegistryScript := preload("res://scripts/core/data_registry.gd")
const PROFILES := "res://tools/campaign/meta_profiles.json"

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


func test_the_profiles_grow_through_the_campaign() -> void:
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	var last_nodes := -1
	for campaign in meta.campaigns_in_order():
		for stage in campaign.stages:
			var profile := PlayerProfile.from_dict(profiles.get(String(stage.id), {}))
			assert_true(profile.meta_nodes.size() >= last_nodes, "%s: the player only gains meta nodes" % stage.id)
			last_nodes = profile.meta_nodes.size()
	assert_gt(last_nodes, 50, "by the citadel the player has a good share of the tree")
