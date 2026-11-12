# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost. Retuned 2026-11-11 for the long waves (several
# beats each: packs, surges, flanks) on top of the toned-down heroes and skills, and again when the
# horde got its powers (EnemyData.power).
TUNING["ember_1"] = {"health": 1.79}
TUNING["ember_2"] = {"health": 1.91, "boss": 1.14}
TUNING["ember_3"] = {"health": 2.35, "boss": 1.09}
TUNING["ember_4"] = {"health": 2.9, "boss": 0.42}
TUNING["storm_1"] = {"health": 2.04}
TUNING["storm_2"] = {"health": 2.42, "boss": 0.53}
TUNING["storm_3"] = {"health": 1.55, "boss": 1.26}
TUNING["storm_4"] = {"health": 3.02, "boss": 0.2}
TUNING["nature_1"] = {"health": 1.09}
TUNING["nature_2"] = {"health": 1.61, "boss": 0.73}
TUNING["nature_3"] = {"health": 0.89, "boss": 1.42}
TUNING["nature_4"] = {"health": 1.57, "boss": 0.59}
# The horde's powers cost lives here at any health scale (the tune bottoms out), so this one is
# set by hand where the bot wins keeping a little under half.
TUNING["water_1"] = {"health": 0.5}
TUNING["water_2"] = {"health": 0.87, "boss": 1.29}
TUNING["water_3"] = {"health": 1.23, "boss": 2.19}
TUNING["water_4"] = {"health": 1.11, "boss": 0.29}
# The horde's powers cost lives here at any health scale (the tune bottoms out), so this one is
# set by hand where the bot wins keeping a little under half.
TUNING["earth_1"] = {"health": 0.4}
TUNING["earth_2"] = {"health": 1.15, "boss": 1.12}
TUNING["earth_3"] = {"health": 0.66, "boss": 2.94}
TUNING["earth_4"] = {"health": 1.29, "boss": 0.35}
TUNING["void_1"] = {"health": 2.24}
TUNING["void_2"] = {"health": 1.42, "boss": 0.63}
TUNING["void_3"] = {"health": 2.19, "boss": 0.89}
TUNING["void_4"] = {"health": 2.2, "boss": 0.57}
TUNING["converge_1"] = {"health": 1.59, "boss": 0.51}
TUNING["converge_2"] = {"health": 1.79, "boss": 0.27}
TUNING["converge_3"] = {"health": 1.26, "boss": 0.32}
TUNING["assault_1"] = {"health": 0.51, "boss": 0.56, "lives": 30}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish`: it found
# 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a little lower.
TUNING["prototype"] = {"health": 0.85}
