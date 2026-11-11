# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost. Retuned 2026-11-11 after heroes and skills were
# toned down, so the towers the player builds carry each stage, and again when
# the horde got its powers (EnemyData.power).
TUNING["ember_1"] = {"health": 1.95}
TUNING["ember_2"] = {"health": 1.27, "boss": 0.79}
TUNING["ember_3"] = {"health": 1.56, "boss": 0.63}
TUNING["ember_4"] = {"health": 2.22, "boss": 0.21}
TUNING["storm_1"] = {"health": 2.22}
TUNING["storm_2"] = {"health": 2.35, "boss": 0.37}
TUNING["storm_3"] = {"health": 0.94, "boss": 1.14}
TUNING["storm_4"] = {"health": 1.55, "boss": 0.21}
TUNING["nature_1"] = {"health": 1.77}
TUNING["nature_2"] = {"health": 1.11, "boss": 0.84}
TUNING["nature_3"] = {"health": 0.54, "boss": 1.28}
TUNING["nature_4"] = {"health": 1.24, "boss": 0.38}
TUNING["water_1"] = {"health": 0.52}
TUNING["water_2"] = {"health": 0.32, "boss": 1.48}
TUNING["water_3"] = {"health": 0.28, "boss": 3.77}
TUNING["water_4"] = {"health": 1.19, "boss": 0.2}
# The tuning run finds no scale at which the bot keeps 60% of its lives here, so this one sits at
# the bottom of the search range.
TUNING["earth_1"] = {"health": 0.28}
TUNING["earth_2"] = {"health": 0.96, "boss": 0.84}
TUNING["earth_3"] = {"health": 0.47, "boss": 2.3}
TUNING["earth_4"] = {"health": 0.97, "boss": 0.4}
TUNING["void_1"] = {"health": 1.21}
TUNING["void_2"] = {"health": 0.94, "boss": 0.35}
TUNING["void_3"] = {"health": 1.23, "boss": 1.03}
TUNING["void_4"] = {"health": 1.36, "boss": 0.48}
TUNING["converge_1"] = {"health": 1.15, "boss": 0.2}
TUNING["converge_2"] = {"health": 0.93, "boss": 0.24}
TUNING["converge_3"] = {"health": 1.23, "boss": 0.26}
TUNING["assault_1"] = {"health": 0.34, "boss": 0.38, "lives": 30}
