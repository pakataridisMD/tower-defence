# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost. Retuned 2026-11-11 after heroes and skills were
# toned down, so the towers the player builds carry each stage.
TUNING["ember_1"] = {"health": 1.74}
TUNING["ember_2"] = {"health": 1.4, "boss": 0.7}
TUNING["ember_3"] = {"health": 1.86, "boss": 0.37}
TUNING["ember_4"] = {"health": 1.43, "boss": 0.28}
TUNING["storm_1"] = {"health": 2.29}
TUNING["storm_2"] = {"health": 2.26, "boss": 0.31}
TUNING["storm_3"] = {"health": 1.24, "boss": 0.95}
TUNING["storm_4"] = {"health": 1.55, "boss": 0.21}
TUNING["nature_1"] = {"health": 1.93}
TUNING["nature_2"] = {"health": 1.37, "boss": 0.71}
TUNING["nature_3"] = {"health": 0.54, "boss": 1.17}
TUNING["nature_4"] = {"health": 1.48, "boss": 0.31}
TUNING["water_1"] = {"health": 0.59}
TUNING["water_2"] = {"health": 0.49, "boss": 0.78}
TUNING["water_3"] = {"health": 0.81, "boss": 1.56}
TUNING["water_4"] = {"health": 1.26, "boss": 0.2}
# The tuning run finds no scale at which the bot keeps 60% of its lives here, so this one sits at
# the bottom of the search range.
TUNING["earth_1"] = {"health": 0.28}
TUNING["earth_2"] = {"health": 1.02, "boss": 0.99}
TUNING["earth_3"] = {"health": 0.72, "boss": 1.76}
TUNING["earth_4"] = {"health": 1.19, "boss": 0.32}
TUNING["void_1"] = {"health": 1.12}
TUNING["void_2"] = {"health": 0.99, "boss": 0.34}
TUNING["void_3"] = {"health": 1.27, "boss": 0.85}
TUNING["void_4"] = {"health": 1.24, "boss": 0.5}
TUNING["converge_1"] = {"health": 1.24, "boss": 0.22}
TUNING["converge_2"] = {"health": 0.97, "boss": 0.24}
TUNING["converge_3"] = {"health": 0.96, "boss": 0.26}
TUNING["assault_1"] = {"health": 0.34, "boss": 0.42, "lives": 30}
