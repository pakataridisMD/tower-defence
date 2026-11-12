# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost. Retuned 2026-11-11 for the long waves (several
# beats each: packs, surges, flanks) on top of the toned-down heroes and skills, and again when the
# horde got its powers (EnemyData.power). Retuned 2026-11-12 for the 42x26 maps with spawn holes;
# ember_4, storm_4 and assault_1 were lowered by hand there (their tune ran past the job's time).
TUNING["ember_1"] = {"health": 2.2}
TUNING["ember_2"] = {"health": 2.75, "boss": 0.97}
TUNING["ember_3"] = {"health": 1.47, "boss": 3.78}
TUNING["ember_4"] = {"health": 2.0, "boss": 0.42}
TUNING["storm_1"] = {"health": 2.55}
TUNING["storm_2"] = {"health": 2.98, "boss": 0.28}
TUNING["storm_3"] = {"health": 2.06, "boss": 0.96}
TUNING["storm_4"] = {"health": 1.9, "boss": 0.2}
TUNING["nature_1"] = {"health": 2.13}
TUNING["nature_2"] = {"health": 2.92, "boss": 0.76}
TUNING["nature_3"] = {"health": 1.49, "boss": 1.5}
TUNING["nature_4"] = {"health": 1.57, "boss": 0.59}
# The horde's powers cost lives here at any health scale (the tune bottoms out), so this one is
# set by hand where the bot wins keeping a little under half.
TUNING["water_1"] = {"health": 0.5}
TUNING["water_2"] = {"health": 2.6, "boss": 0.47}
TUNING["water_3"] = {"health": 1.82, "boss": 1.61}
TUNING["water_4"] = {"health": 1.11, "boss": 0.29}
TUNING["earth_1"] = {"health": 2.6}
TUNING["earth_2"] = {"health": 1.29, "boss": 0.73}
TUNING["earth_3"] = {"health": 0.59, "boss": 2.63}
TUNING["earth_4"] = {"health": 1.29, "boss": 0.35}
TUNING["void_1"] = {"health": 1.99}
TUNING["void_2"] = {"health": 2.0, "boss": 0.48}
TUNING["void_3"] = {"health": 1.84, "boss": 1.92}
TUNING["void_4"] = {"health": 2.2, "boss": 0.57}
TUNING["converge_1"] = {"health": 2.11, "boss": 0.32}
TUNING["converge_2"] = {"health": 2.15, "boss": 0.24}
TUNING["converge_3"] = {"health": 1.49, "boss": 0.35}
TUNING["assault_1"] = {"health": 0.22, "boss": 0.17, "lives": 30}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish`: it found
# 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a little lower.
TUNING["prototype"] = {"health": 0.85}
