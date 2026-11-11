# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Retuned 2026-11-11 when the horde got
# its powers (EnemyData.power). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost (Void 4).
TUNING["ember_1"] = {"health": 2.3}
TUNING["ember_2"] = {"health": 1.68, "boss": 1.26}
TUNING["ember_3"] = {"health": 2.45, "boss": 0.67}
TUNING["ember_4"] = {"health": 3.52, "boss": 0.32}
TUNING["storm_1"] = {"health": 2.29}
TUNING["storm_2"] = {"health": 2.78, "boss": 0.5}
TUNING["storm_3"] = {"health": 1.26, "boss": 1.62}
TUNING["storm_4"] = {"health": 3.79, "boss": 0.21}
TUNING["nature_1"] = {"health": 1.98}
TUNING["nature_2"] = {"health": 1.59, "boss": 1.21}
TUNING["nature_3"] = {"health": 0.51, "boss": 1.78}
TUNING["nature_4"] = {"health": 1.38, "boss": 0.36}
TUNING["water_1"] = {"health": 0.78}
TUNING["water_2"] = {"health": 0.6, "boss": 0.87}
TUNING["water_3"] = {"health": 2.13, "boss": 1.44}
TUNING["water_4"] = {"health": 1.39, "boss": 0.2}
# The tuning run found no scale at which the bot keeps 60% of its lives here, so this one stays
# where the bot wins with a little over half.
TUNING["earth_1"] = {"health": 0.28}
TUNING["earth_2"] = {"health": 1.3, "boss": 0.81}
TUNING["earth_3"] = {"health": 0.86, "boss": 1.37}
TUNING["earth_4"] = {"health": 1.4, "boss": 0.32}
TUNING["void_1"] = {"health": 1.42}
TUNING["void_2"] = {"health": 0.93, "boss": 0.4}
TUNING["void_3"] = {"health": 2.0, "boss": 1.51}
TUNING["void_4"] = {"health": 2.14, "boss": 0.9}
TUNING["converge_1"] = {"health": 1.51, "boss": 0.53}
TUNING["converge_2"] = {"health": 0.94, "boss": 0.34}
TUNING["converge_3"] = {"health": 1.39, "boss": 0.27}
TUNING["assault_1"] = {"health": 0.54, "boss": 0.31, "lives": 30}
