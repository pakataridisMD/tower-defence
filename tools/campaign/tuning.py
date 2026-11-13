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
# Retuned 2026-11-13 when the Talents tree became tower unlocks only: the old talents' stat bonuses
# (about +100% damage, +35% attack speed, gold and lives) are gone, so every stage came down. From the
# Balance workflow's [tune] against meta profiles where the pacing bot buys the towers of the element it
# plays (the one the land's horde fears). ember_2, storm_1, nature_4, water_3, earth_2 and void_1 were set
# by hand from the --check runs (earth_2's boss wave lowered to 0.15: the bot lost at the boss at 0.30).
TUNING["ember_1"] = {"health": 2.23}
TUNING["ember_2"] = {"health": 1.40, "boss": 2.00}
TUNING["ember_3"] = {"health": 2.56, "boss": 2.47}
TUNING["ember_4"] = {"health": 2.03, "boss": 0.21}
TUNING["storm_1"] = {"health": 4.00}
TUNING["storm_2"] = {"health": 4.33, "boss": 2.96}
TUNING["storm_3"] = {"health": 3.21, "boss": 3.38}
TUNING["storm_4"] = {"health": 0.84, "boss": 0.18}
TUNING["nature_1"] = {"health": 4.83}
TUNING["nature_2"] = {"health": 2.66, "boss": 7.57}
TUNING["nature_3"] = {"health": 3.42, "boss": 0.45}
TUNING["nature_4"] = {"health": 2.00, "boss": 0.21}
TUNING["water_1"] = {"health": 9.03}
TUNING["water_2"] = {"health": 4.67, "boss": 0.24}
TUNING["water_3"] = {"health": 2.50, "boss": 0.30}
TUNING["water_4"] = {"health": 0.88, "boss": 0.18}
TUNING["earth_1"] = {"health": 6.81}
TUNING["earth_2"] = {"health": 4.00, "boss": 0.15}
TUNING["earth_3"] = {"health": 2.68, "boss": 0.30}
TUNING["earth_4"] = {"health": 1.28, "boss": 0.12}
TUNING["void_1"] = {"health": 4.50}
TUNING["void_2"] = {"health": 2.38, "boss": 0.30}
TUNING["void_3"] = {"health": 2.74, "boss": 0.83}
TUNING["void_4"] = {"health": 2.15, "boss": 0.28}
TUNING["converge_1"] = {"health": 1.16, "boss": 0.21}
TUNING["converge_2"] = {"health": 1.19, "boss": 0.21, "boss_life": 0.67}
TUNING["converge_3"] = {"health": 3.27, "boss": 0.21, "boss_life": 0.27}
# Nov 12: every boss got 4x its life (Vael-Orrun 10x) and new abilities (heal, barrier, binding towers,
# his fireball). "boss_life" softens a stage's bosses alone (WaveSet.boss_health_scale) where the bot could
# no longer beat them keeping a tenth of its lives; from `campaign_balance.gd -- --tune-bosses`. Stages
# without it keep the bosses' full life.
# After the 90% ability cut and the boss ramp (Nov 12, abilities grow from 30% on the first stage to
# 100% on the last) the three last stages were retuned, so their bosses are the toughest again.
# assault_1: the bot wins up to 0.72 and loses at 0.77 (Vael-Orrun reaches the end), so 0.65.
# Nov 13, after talents became tower unlocks only (no stat bonuses), --tune-bosses was run again on the
# stages the bot lost at the boss: ember_4, storm_4, nature_3, earth_2, the Convergence and the assault.
# The final level was rebuilt as 38 rolling waves, Vael-Orrun's three forms on wave 39 and the
# counter-attack on 40; set by hand with `campaign_balance.gd -- --stage=assault_1 --health=X --boss=X`.
# The boss is the cliff (his last form must fall before the end of the road): the bot won up to
# about 0.11 of a wave's health for him and lost at 0.17, so he sits at 0.09.
# 2026-11-13: lowered from 2.3 to 0.55 when talents became tower unlocks only: the bot lost wave 29 to the
# Brass Juggernauts at anything from 1.0 up and won at 0.6.
TUNING["assault_1"] = {"health": 0.55, "boss": 0.04, "lives": 30, "boss_life": 0.55}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish` with no
# meta tree: it found 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a
# little lower.
# 2026-11-12: lowered from 0.85 to 0.45 when talents became tower unlocks only: a veteran lost the old
# talents' gold, lives and damage, and the Water/Earth/Void plan lost at 0.6.
TUNING["prototype"] = {"health": 0.45}
# The land skirmish maps' own waves (data/waves/skirmish_<map>.tres), from
# `campaign_balance.gd -- --skirmish --map=<map>` with no meta tree, x0.95, played by a bot that brings the
# element the land's horde fears (AutoPlayer.counter_plan). gen_campaign.py triples them
# (SKIRMISH_HARDNESS), as it does the prototype waves above.
# 2026-11-13: retuned with talents as tower unlocks only (no stat bonuses). The Warden on the last wave
# beat the veteran at full strength, so its wave and its own life are softened too (Stormcrown's
# thunderhead most of all).
TUNING["skirmish_cinderfall"] = {"health": 0.23, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_stormcrown"] = {"health": 0.15, "boss": 0.35, "boss_life": 0.15}
TUNING["skirmish_thornwild"] = {"health": 0.20, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_frozen_ford"] = {"health": 0.11, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_red_gorge"] = {"health": 0.14, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_riftwalk"] = {"health": 0.15, "boss": 0.35, "boss_life": 0.4}
