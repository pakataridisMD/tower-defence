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
TUNING["ember_1"] = {"health": 3.05}
TUNING["ember_2"] = {"health": 3.86, "boss": 0.39}
TUNING["ember_3"] = {"health": 4.01, "boss": 1.30}
TUNING["ember_4"] = {"health": 6.00, "boss": 0.33}
TUNING["storm_1"] = {"health": 6.59}
TUNING["storm_2"] = {"health": 6.81, "boss": 1.39}
TUNING["storm_3"] = {"health": 5.26, "boss": 1.97}
TUNING["storm_4"] = {"health": 13.49, "boss": 0.28}
TUNING["nature_1"] = {"health": 6.75}
TUNING["nature_2"] = {"health": 10.95, "boss": 0.45}
TUNING["nature_3"] = {"health": 6.30, "boss": 1.74}
TUNING["nature_4"] = {"health": 6.55, "boss": 0.45}
TUNING["water_1"] = {"health": 8.59}
TUNING["water_2"] = {"health": 11.32, "boss": 0.36}
TUNING["water_3"] = {"health": 13.46, "boss": 0.85}
TUNING["water_4"] = {"health": 11.71, "boss": 3.03}
TUNING["earth_1"] = {"health": 6.22}
TUNING["earth_2"] = {"health": 9.77, "boss": 0.28}
TUNING["earth_3"] = {"health": 4.93, "boss": 3.96}
TUNING["earth_4"] = {"health": 8.59, "boss": 2.85}
TUNING["void_1"] = {"health": 6.22}
TUNING["void_2"] = {"health": 13.56, "boss": 1.40}
TUNING["void_3"] = {"health": 7.70, "boss": 1.50}
TUNING["void_4"] = {"health": 13.49, "boss": 3.55}
TUNING["converge_1"] = {"health": 11.54, "boss": 0.59}
# converge_2 lowered from 11.17 to 10.0 on 2026-11-12: the bot lost it on wave 17 once the stronger bosses landed.
TUNING["converge_2"] = {"health": 10.0, "boss": 0.24, "boss_life": 0.6}
TUNING["converge_3"] = {"health": 13.83, "boss": 0.24, "boss_life": 0.17}
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
# `campaign_balance.gd -- --skirmish --map=<map>` with no meta tree, x0.95. gen_campaign.py triples them
# (SKIRMISH_HARDNESS), as it does the prototype waves above.
TUNING["skirmish_cinderfall"] = {"health": 0.3}
TUNING["skirmish_stormcrown"] = {"health": 0.41}
TUNING["skirmish_thornwild"] = {"health": 0.49}
TUNING["skirmish_frozen_ford"] = {"health": 0.35}
TUNING["skirmish_red_gorge"] = {"health": 0.35}
TUNING["skirmish_riftwalk"] = {"health": 0.5}
