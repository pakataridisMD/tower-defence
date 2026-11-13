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
# Retuned again on 2026-11-12 when the Talents tree became tower unlocks only (no stat bonuses): the
# Balance workflow's [tune] values x0.95, taken only where they are lower than before, so no stage
# got harder. earth_3, earth_4, water_3 and converge_1 then sat on a knife edge against the new
# meta profiles, so they were tuned again locally and sit 10% under what that found (earth_3 lower
# still, at 3.0: the bot lost its third wave at 4.2 but won at 3.0).
# These were found with full minor enemy health; the campaign's halving of it (RunSim) comes on top.
TUNING["ember_1"] = {"health": 3.05}
TUNING["ember_2"] = {"health": 3.86, "boss": 0.23}
TUNING["ember_3"] = {"health": 4.01, "boss": 1.30}
TUNING["ember_4"] = {"health": 6.00, "boss": 0.33, "boss_life": 0.50}
TUNING["storm_1"] = {"health": 6.59}
TUNING["storm_2"] = {"health": 6.81, "boss": 0.43}
TUNING["storm_3"] = {"health": 5.26, "boss": 0.93}
TUNING["storm_4"] = {"health": 4.71, "boss": 0.14, "boss_life": 0.24}
TUNING["nature_1"] = {"health": 6.75}
TUNING["nature_2"] = {"health": 10.95, "boss": 0.37}
TUNING["nature_3"] = {"health": 6.30, "boss": 1.74, "boss_life": 0.84}
TUNING["nature_4"] = {"health": 6.55, "boss": 0.45}
TUNING["water_1"] = {"health": 7.04}
TUNING["water_2"] = {"health": 11.32, "boss": 0.28}
TUNING["water_3"] = {"health": 10.76, "boss": 0.66}
TUNING["water_4"] = {"health": 8.93, "boss": 3.03}
TUNING["earth_1"] = {"health": 6.22}
TUNING["earth_2"] = {"health": 6.47, "boss": 0.28, "boss_life": 0.17}
TUNING["earth_3"] = {"health": 3.0, "boss": 1.99}
TUNING["earth_4"] = {"health": 5.77, "boss": 2.79}
TUNING["void_1"] = {"health": 6.22}
TUNING["void_2"] = {"health": 7.38, "boss": 1.23}
TUNING["void_3"] = {"health": 7.70, "boss": 1.20}
TUNING["void_4"] = {"health": 13.49, "boss": 0.34}
TUNING["converge_1"] = {"health": 7.78, "boss": 0.28, "boss_life": 0.49}
TUNING["converge_2"] = {"health": 7.60, "boss": 0.24, "boss_life": 0.15}
TUNING["converge_3"] = {"health": 3.94, "boss": 0.20, "boss_life": 0.24}
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
# 2026-11-12: lowered from 2.3 to 1.9 when talents became tower unlocks only (the bot lost wave 37 at 2.3).
TUNING["assault_1"] = {"health": 1.90, "boss": 0.04, "lives": 30, "boss_life": 0.55}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish` with no
# meta tree: it found 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a
# little lower.
# 2026-11-12: lowered from 0.85 to 0.45 when talents became tower unlocks only: a veteran lost the old
# talents' gold, lives and damage, and the Water/Earth/Void plan lost at 0.6.
TUNING["prototype"] = {"health": 0.45}
# The land skirmish maps' own waves (data/waves/skirmish_<map>.tres), from
# `campaign_balance.gd -- --skirmish --map=<map>` with no meta tree, x0.95. gen_campaign.py triples them
# (SKIRMISH_HARDNESS), as it does the prototype waves above. Their Warden waves carry 35% of their health
# ("boss_life" 40%: the Wardens themselves, since main gave every boss 4x life) since 2026-11-12: with talents now unlocking only towers, a veteran's towers lost the old talents'
# damage and lives, and the Warden walked off every land map with a third of its health left.
TUNING["skirmish_cinderfall"] = {"health": 0.3, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_stormcrown"] = {"health": 0.41, "boss": 0.35, "boss_life": 0.15}
TUNING["skirmish_thornwild"] = {"health": 0.49, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_frozen_ford"] = {"health": 0.35, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_red_gorge"] = {"health": 0.35, "boss": 0.35, "boss_life": 0.4}
TUNING["skirmish_riftwalk"] = {"health": 0.5, "boss": 0.35, "boss_life": 0.4}
