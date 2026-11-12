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
TUNING["ember_1"] = {"health": 3.05}
TUNING["ember_2"] = {"health": 3.93, "boss": 0.45}
TUNING["ember_3"] = {"health": 4.67, "boss": 1.33}
TUNING["ember_4"] = {"health": 5.71, "boss": 0.53}
TUNING["storm_1"] = {"health": 4.89}
TUNING["storm_2"] = {"health": 5.71, "boss": 0.77}
TUNING["storm_3"] = {"health": 4.79, "boss": 3.24}
TUNING["storm_4"] = {"health": 15.42, "boss": 0.21}
TUNING["nature_1"] = {"health": 7.7}
TUNING["nature_2"] = {"health": 11.91, "boss": 0.47}
TUNING["nature_3"] = {"health": 6.82, "boss": 1.23}
TUNING["nature_4"] = {"health": 7.04, "boss": 0.53}
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
TUNING["void_4"] = {"health": 15.6, "boss": 0.59}
TUNING["converge_1"] = {"health": 11.47, "boss": 0.71}
TUNING["converge_2"] = {"health": 8.15, "boss": 0.68}
TUNING["converge_3"] = {"health": 9.47, "boss": 0.28}
TUNING["assault_1"] = {"health": 2.09, "boss": 0.8, "lives": 30}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish` with no
# meta tree: it found 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a
# little lower.
TUNING["prototype"] = {"health": 0.85}
