# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost (Void 4).
TUNING["ember_1"] = {"health": 2.53}
TUNING["ember_2"] = {"health": 1.46, "boss": 1.22}
TUNING["ember_3"] = {"health": 2.7, "boss": 0.81}
TUNING["ember_4"] = {"health": 3.79, "boss": 0.29}
TUNING["storm_1"] = {"health": 2.36}
TUNING["storm_2"] = {"health": 2.82, "boss": 0.72}
TUNING["storm_3"] = {"health": 1.14, "boss": 3.78}
TUNING["storm_4"] = {"health": 3.79, "boss": 0.2}
TUNING["nature_1"] = {"health": 2.11}
TUNING["nature_2"] = {"health": 2.35, "boss": 0.96}
TUNING["nature_3"] = {"health": 0.62, "boss": 1.81}
TUNING["nature_4"] = {"health": 1.76, "boss": 0.5}
TUNING["water_1"] = {"health": 0.82}
TUNING["water_2"] = {"health": 0.75, "boss": 0.68}
TUNING["water_3"] = {"health": 2.69, "boss": 0.67}
TUNING["water_4"] = {"health": 1.3, "boss": 0.2}
# The tuning run found no scale at which the bot keeps 60% of its lives here, so this one stays
# where the bot wins with a little over half.
TUNING["earth_1"] = {"health": 0.48}
TUNING["earth_2"] = {"health": 1.48, "boss": 0.75}
TUNING["earth_3"] = {"health": 1.02, "boss": 1.42}
TUNING["earth_4"] = {"health": 1.61, "boss": 0.24}
TUNING["void_1"] = {"health": 1.22}
TUNING["void_2"] = {"health": 0.94, "boss": 0.38}
TUNING["void_3"] = {"health": 2.54, "boss": 1.25}
TUNING["void_4"] = {"health": 1.85, "boss": 0.72}
TUNING["converge_1"] = {"health": 1.64, "boss": 0.36}
TUNING["converge_2"] = {"health": 1.04, "boss": 0.31}
TUNING["converge_3"] = {"health": 1.23, "boss": 0.31}
TUNING["assault_1"] = {"health": 0.8, "boss": 0.15, "lives": 30}
