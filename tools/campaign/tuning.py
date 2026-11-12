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
# Nov 12: every boss got 4x its life (Vael-Orrun 10x) and new abilities (heal, barrier, binding towers,
# his fireball). "boss_life" softens a stage's bosses alone (WaveSet.boss_health_scale) where the bot could
# no longer beat them keeping a tenth of its lives; from `campaign_balance.gd -- --tune-bosses`. Stages
# without it keep the bosses' full life.
TUNING["ember_1"] = {"health": 3.05}
TUNING["ember_2"] = {"health": 3.93, "boss": 0.45, "boss_life": 0.16}
TUNING["ember_3"] = {"health": 4.67, "boss": 1.33, "boss_life": 0.25}
TUNING["ember_4"] = {"health": 5.71, "boss": 0.53, "boss_life": 0.19}
TUNING["storm_1"] = {"health": 4.89}
TUNING["storm_2"] = {"health": 5.71, "boss": 0.77}
TUNING["storm_3"] = {"health": 4.79, "boss": 3.24}
TUNING["storm_4"] = {"health": 15.42, "boss": 0.21, "boss_life": 0.26}
TUNING["nature_1"] = {"health": 7.7}
TUNING["nature_2"] = {"health": 11.91, "boss": 0.47}
TUNING["nature_3"] = {"health": 6.82, "boss": 1.23, "boss_life": 0.41}
TUNING["nature_4"] = {"health": 7.04, "boss": 0.53, "boss_life": 0.29}
TUNING["water_1"] = {"health": 8.96}
TUNING["water_2"] = {"health": 11.91, "boss": 0.3}
TUNING["water_3"] = {"health": 13.62, "boss": 1.09}
TUNING["water_4"] = {"health": 12.06, "boss": 4.11}
TUNING["earth_1"] = {"health": 6.15}
TUNING["earth_2"] = {"health": 7.11, "boss": 7.57}
TUNING["earth_3"] = {"health": 5.34, "boss": 0.77}
TUNING["earth_4"] = {"health": 8.51, "boss": 0.24}
TUNING["void_1"] = {"health": 6.67}
TUNING["void_2"] = {"health": 11.32, "boss": 1.59}
TUNING["void_3"] = {"health": 8.51, "boss": 1.53}
TUNING["void_4"] = {"health": 15.6, "boss": 0.59, "boss_life": 0.30}
TUNING["converge_1"] = {"health": 11.47, "boss": 0.71, "boss_life": 0.16}
TUNING["converge_2"] = {"health": 8.15, "boss": 0.68, "boss_life": 0.19}
TUNING["converge_3"] = {"health": 9.47, "boss": 0.28, "boss_life": 0.15}
# The final level was rebuilt as 38 rolling waves, Vael-Orrun's three forms on wave 39 and the
# counter-attack on 40; set by hand with `campaign_balance.gd -- --stage=assault_1 --health=X --boss=X`.
# The boss is the cliff (his last form must fall before the end of the road): the bot won up to
# about 0.11 of a wave's health for him and lost at 0.17, so he sits at 0.09.
TUNING["assault_1"] = {"health": 2.3, "boss": 0.04, "lives": 30, "boss_life": 0.33}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish` with no
# meta tree: it found 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a
# little lower.
TUNING["prototype"] = {"health": 0.85}
