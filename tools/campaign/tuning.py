# Each stage's health scale, and its boss waves' health, found by
#   godot --headless -s tools/campaign_balance.gd -- --tune
# (the Balance workflow runs it for a commit message with [tune]). Each has a margin taken off: 5%,
# and 5% more for as long as the bot still lost. Retuned 2026-11-11 for the long waves (several
# beats each: packs, surges, flanks) on top of the toned-down heroes and skills.
TUNING["ember_1"] = {"health": 1.89}
TUNING["ember_2"] = {"health": 1.68, "boss": 1.34}
TUNING["ember_3"] = {"health": 2.13, "boss": 1.11}
TUNING["ember_4"] = {"health": 2.91, "boss": 0.42}
TUNING["storm_1"] = {"health": 2.19}
TUNING["storm_2"] = {"health": 2.28, "boss": 0.75}
TUNING["storm_3"] = {"health": 1.31, "boss": 1.51}
TUNING["storm_4"] = {"health": 2.91, "boss": 0.20}
TUNING["nature_1"] = {"health": 1.53}
TUNING["nature_2"] = {"health": 1.93, "boss": 0.82}
TUNING["nature_3"] = {"health": 1.15, "boss": 1.23}
TUNING["nature_4"] = {"health": 1.91, "boss": 0.51}
TUNING["water_1"] = {"health": 0.73}
TUNING["water_2"] = {"health": 1.21, "boss": 0.87}
TUNING["water_3"] = {"health": 1.05, "boss": 2.51}
TUNING["water_4"] = {"health": 1.05, "boss": 0.31}
TUNING["earth_1"] = {"health": 0.59}
TUNING["earth_2"] = {"health": 1.29, "boss": 0.96}
TUNING["earth_3"] = {"health": 0.91, "boss": 2.33}
TUNING["earth_4"] = {"health": 1.27, "boss": 0.56}
TUNING["void_1"] = {"health": 2.24}
TUNING["void_2"] = {"health": 1.59, "boss": 0.54}
TUNING["void_3"] = {"health": 2.28, "boss": 0.89}
TUNING["void_4"] = {"health": 2.76, "boss": 0.45}
TUNING["converge_1"] = {"health": 1.73, "boss": 0.32}
TUNING["converge_2"] = {"health": 1.82, "boss": 0.26}
TUNING["converge_3"] = {"health": 1.62, "boss": 0.26}
TUNING["assault_1"] = {"health": 0.47, "boss": 0.65, "lives": 30}
# The skirmish waves (data/waves/prototype.tres), from `campaign_balance.gd -- --skirmish`: it found
# 0.95, but the Water/Earth/Void plan only scrapes through there, so this sits a little lower.
TUNING["prototype"] = {"health": 0.85}
