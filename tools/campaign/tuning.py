# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost.
#
# Retuned 2026-11-12 against the player a new player would be by each stage: the meta tree they
# have bought, the sigils of the lands behind them and the heroes who have joined
# (tools/campaign/meta_profiles.json, from tools/meta_pacing.gd), on the 42x26 maps with the long
# waves and the horde's powers. The lands open in order, so those profiles hold. ember_3, storm_3
# and storm_4 sit 5% under what the tune found: the bot only scraped through (or lost) there.
TUNING["ember_1"] = {"health": 3.14}
TUNING["ember_2"] = {"health": 4.76, "boss": 0.47}
TUNING["ember_3"] = {"health": 4.6, "boss": 1.57}
TUNING["ember_4"] = {"health": 7.41, "boss": 0.33}
TUNING["storm_1"] = {"health": 6.67}
TUNING["storm_2"] = {"health": 8.58, "boss": 0.66}
TUNING["storm_3"] = {"health": 5.81, "boss": 2.94}
TUNING["storm_4"] = {"health": 8.54, "boss": 2.71}
TUNING["nature_1"] = {"health": 8.58}
TUNING["nature_2"] = {"health": 12.72, "boss": 0.74}
TUNING["nature_3"] = {"health": 6.82, "boss": 1.06}
TUNING["nature_4"] = {"health": 6.93, "boss": 0.56}
TUNING["water_1"] = {"health": 9.70}
TUNING["water_2"] = {"health": 11.81, "boss": 1.94}
TUNING["water_3"] = {"health": 15.09, "boss": 0.98}
TUNING["water_4"] = {"health": 13.96, "boss": 4.17}
TUNING["earth_1"] = {"health": 9.47}
TUNING["earth_2"] = {"health": 7.44, "boss": 0.39}
TUNING["earth_3"] = {"health": 5.09, "boss": 5.02}
TUNING["earth_4"] = {"health": 8.14, "boss": 0.24}
TUNING["void_1"] = {"health": 11.25}
TUNING["void_2"] = {"health": 16.71, "boss": 0.39}
TUNING["void_3"] = {"health": 14.13, "boss": 1.15}
TUNING["void_4"] = {"health": 18.78, "boss": 0.53}
TUNING["converge_1"] = {"health": 12.06, "boss": 0.63}
TUNING["converge_2"] = {"health": 9.64, "boss": 0.66}
TUNING["converge_3"] = {"health": 15.95, "boss": 0.20}
# The final level was rebuilt as 38 rolling waves, Vael-Orrun's three forms on wave 39 and the
# counter-attack on 40; set by hand with `campaign_balance.gd -- --stage=assault_1 --health=X --boss=X`.
# The boss is the cliff (his last form must fall before the end of the road): the bot won up to
# about 0.11 of a wave's health for him and lost at 0.17, so he sits at 0.09.
TUNING["assault_1"] = {"health": 2.3, "boss": 0.04, "lives": 30}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish` with no
# meta tree: it found 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a
# little lower.
TUNING["prototype"] = {"health": 0.85}
