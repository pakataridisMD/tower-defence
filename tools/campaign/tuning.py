# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost.
#
# Retuned 2026-11-12 against the player a new player would be by each stage: the meta tree they
# have bought, the sigils of the lands behind them and the heroes who have joined
# (tools/campaign/meta_profiles.json, from tools/meta_pacing.gd), on the 42x26 maps with the long
# waves and the horde's powers. The lands open in order, so those profiles hold. Retuned again the
# same day once each land's own horde (tools/campaign/horde.py, five kinds per land) joined its waves.
# converge_2, nature_3 and water_3 sit 5% under what the tune found: the bot only scraped through there.
# Retuned again on 2026-11-12 when the skill web grew tenfold (397 nodes, climbing costs, smaller
# bonuses, three skill points a wave): every element and Convergence stage, from a local --tune per stage.
# nature_4 and earth_3 sit 5% under what that tune found: the bot lost or only scraped through there.
# These were found with full minor enemy health; the campaign's halving of it (RunSim) comes on top.
# Retuned 2026-11-12 night for elemental affinities (attuned, warded, tank, Hulking elites) and each
# land fought by its own element's horde with every element open (the bot brings what the horde fears).
# Stages at 18.92 hit the bisect's ceiling: the counter-element bot wins them easily.
TUNING["ember_1"] = {"health": 2.17}
TUNING["ember_2"] = {"health": 1.83, "boss": 3.69}
TUNING["ember_3"] = {"health": 3.09, "boss": 1.91}
TUNING["ember_4"] = {"health": 2.09, "boss": 3.82}
TUNING["storm_1"] = {"health": 8.81}
TUNING["storm_2"] = {"health": 5.79, "boss": 3.44}
TUNING["storm_3"] = {"health": 6.17, "boss": 2.47}
TUNING["storm_4"] = {"health": 2.96, "boss": 7.57}
TUNING["nature_1"] = {"health": 10.51}
TUNING["nature_2"] = {"health": 4.96, "boss": 0.10}
TUNING["nature_3"] = {"health": 8.00, "boss": 0.28}
TUNING["nature_4"] = {"health": 8.00, "boss": 0.21}
TUNING["water_1"] = {"health": 18.92}
TUNING["water_2"] = {"health": 18.92, "boss": 2.29}
TUNING["water_3"] = {"health": 10.14, "boss": 2.15}
TUNING["water_4"] = {"health": 4.88, "boss": 7.57}
TUNING["earth_1"] = {"health": 18.92}
TUNING["earth_2"] = {"health": 18.92, "boss": 3.41}
TUNING["earth_3"] = {"health": 9.53, "boss": 2.26}
TUNING["earth_4"] = {"health": 15.14, "boss": 1.94}
TUNING["void_1"] = {"health": 13.46}
TUNING["void_2"] = {"health": 8.46, "boss": 1.26}
TUNING["void_3"] = {"health": 9.18, "boss": 0.66}
TUNING["void_4"] = {"health": 12.37, "boss": 2.20}
TUNING["converge_1"] = {"health": 13.55, "boss": 0.98}
TUNING["converge_2"] = {"health": 7.50, "boss": 0.42, "boss_life": 0.60}
TUNING["converge_3"] = {"health": 13.09, "boss": 0.24, "boss_life": 0.17}
# Nov 12: every boss got 4x its life (Vael-Orrun 10x) and new abilities (heal, barrier, binding towers,
# his fireball). "boss_life" softens a stage's bosses alone (WaveSet.boss_health_scale) where the bot could
# no longer beat them keeping a tenth of its lives; from `campaign_balance.gd -- --tune-bosses`. Stages
# without it keep the bosses' full life.
# The final level was rebuilt as 38 rolling waves, Vael-Orrun's three forms on wave 39 and the
# counter-attack on 40; set by hand with `campaign_balance.gd -- --stage=assault_1 --health=X --boss=X`.
# The boss is the cliff (his last form must fall before the end of the road): the bot won up to
# about 0.11 of a wave's health for him and lost at 0.17, so he sits at 0.09.
TUNING["assault_1"] = {"health": 2.3, "boss": 0.04, "lives": 30, "boss_life": 0.45}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish` with no
# meta tree: it found 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a
# little lower.
TUNING["prototype"] = {"health": 0.85}
# The land skirmish maps' own waves (data/waves/skirmish_<map>.tres), from
# `campaign_balance.gd -- --skirmish --map=<map>` with no meta tree, x0.95, played by a bot that brings the
# element the land's horde fears (AutoPlayer.counter_plan). gen_campaign.py triples them
# (SKIRMISH_HARDNESS), as it does the prototype waves above.
TUNING["skirmish_cinderfall"] = {"health": 0.39}
TUNING["skirmish_stormcrown"] = {"health": 0.84}
TUNING["skirmish_thornwild"] = {"health": 0.64}
TUNING["skirmish_frozen_ford"] = {"health": 0.47}
TUNING["skirmish_red_gorge"] = {"health": 0.63}
TUNING["skirmish_riftwalk"] = {"health": 0.4}
