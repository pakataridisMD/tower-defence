extends SceneTree
## Plays every campaign stage with the scripted AutoPlayer and prints how each went, for tuning the
## campaign (see tools/campaign/gen_campaign.py). No meta tree bonuses, Normal difficulty.
##
##   godot --headless -s tools/campaign_balance.gd [-- --stage=<id>] [--health=X --boss=X --boss-life=X] [--tune] [--tune-bosses] [--skirmish] [--compare]
##       [--heroes] [--skill-levels] [--list] [--no-meta] [--check]
##
## --tune searches each stage's health scale so the bot wins keeping a target share of its lives,
## and prints lines for tools/campaign/tuning.py. The bot levels its towers and casts its skills,
## but it never sells, never fuses a tower and follows one fixed plan, so a person still has room
## to do better. --skirmish does the same for the skirmish waves (data/waves/prototype.tres),
## against two different plans; add --map=<id> for another skirmish map's own waves. The number it
## prints goes into tuning.py as it is: gen_campaign.py multiplies every skirmish wave set by
## SKIRMISH_HARDNESS on top (skirmish is three times harder than this tuning). --compare plays everything with several kinds of bot (with and
## without skills and upgrades), to see what each habit is worth. --heroes plays every stage with a
## party of the three heroes who would have joined by then, with and without heroes and skills, to
## see how much of a run they carry next to the towers. --skill-levels plays every stage with the bot
## as it is and with the bot buying skill levels from spare gold. --list prints the stage ids, so CI can tune
## them one stage per process, side by side.
##
## Every stage is played (and tuned) by the player a new player would be by then: the profile in
## tools/campaign/meta_profiles.json for that stage, with its meta tree, the sigils of the lands
## already finished and the heroes who have joined. tools/meta_pacing.gd -- --profiles=<path> writes
## that file. --no-meta plays with an empty profile instead, as before.

const PROFILES := "res://tools/campaign/meta_profiles.json"

## Share of lives the bot should keep, by stage position in an element campaign and in the Convergence.
const TARGETS: Array[float] = [0.6, 0.45, 0.3, 0.2]
const CONVERGE_TARGETS: Array[float] = [0.35, 0.25, 0.15]
## Share of lives the weaker of the two skirmish plans should keep on Normal.
const SKIRMISH_TARGET := 0.4
const SKIRMISH_MAP := &"switchback"
## A second skirmish plan, built on Water, Earth and Void. The first is the bot's default plan.
const OTHER_NODES: Array[StringName] = [
	&"earth_entry", &"void_entry", &"earth_level2", &"void_level2", &"tower_hybrid_gravity_well", &"earth_core",
	&"void_core", &"earth_b2_b", &"void_b2_b", &"earth_notable", &"water_entry", &"water_level2",
	&"tower_hybrid_quagmire", &"void_notable", &"water_core", &"earth_level5", &"void_level5", &"earth_b4_b",
	&"void_b4_b", &"water_notable", &"earth_level6", &"void_level6", &"water_level5", &"water_level6",
]
const OTHER_TOWERS: Array[StringName] = [
	&"hybrid_gravity_well", &"hybrid_quagmire", &"earth_monolith", &"void_obelisk", &"water_wellspring",
]


func _initialize() -> void:
	var registry: Node = load("res://scripts/core/data_registry.gd").new()
	registry.reload()
	for line: String in registry.validate():
		print("DATA ERROR: ", line)
	var only := ""
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--stage="):
			only = arg.trim_prefix("--stage=")
	# --no-power=<power> plays without that power, to see what it is worth.
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--no-power="):
			for data: EnemyData in registry.enemies.values():
				if data.power == StringName(arg.trim_prefix("--no-power=")):
					data.power = &""
	var tune := OS.get_cmdline_user_args().has("--tune")
	var meta := MetaProgress.new(registry, PlayerProfile.new())
	_registry = registry
	if not OS.get_cmdline_user_args().has("--no-meta"):
		_load_profiles()
	if OS.get_cmdline_user_args().has("--list"):
		for campaign in meta.campaigns_in_order():
			for stage in campaign.stages:
				print("STAGE ", stage.id)
		registry.free()
		quit()
		return
	if OS.get_cmdline_user_args().has("--compare"):
		_compare(registry, meta)
		registry.free()
		quit()
		return
	if OS.get_cmdline_user_args().has("--skill-levels"):
		_compare_skill_levels(meta, only)
		registry.free()
		quit()
		return
	if OS.get_cmdline_user_args().has("--heroes"):
		_compare_heroes(meta, only)
		registry.free()
		quit()
		return
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--map="):
			_skirmish_map = StringName(arg.trim_prefix("--map="))
	if OS.get_cmdline_user_args().has("--skirmish"):
		_tune_skirmish(registry)
		registry.free()
		quit()
		return
	var lost := 0
	for campaign in meta.campaigns_in_order():
		for i in campaign.stages.size():
			var stage := campaign.stages[i]
			if not only.is_empty() and stage.id != only:
				continue
			if tune:
				var targets := TARGETS if not campaign.element.is_empty() else CONVERGE_TARGETS
				_tune(meta, stage, targets[mini(i, targets.size() - 1)])
				continue
			if OS.get_cmdline_user_args().has("--tune-bosses"):
				_tune_boss_life(meta, stage)
				continue
			var started := Time.get_ticks_msec()
			var sim := _play(meta, stage)
			if sim.state != RunSim.State.WON:
				lost += 1
			print("%-11s %-26s %s wave %2d/%2d  lives %3d/%3d  stars %d  towers %2d  gold %5d  %s  (%d ms)" % [
				stage.id, stage.display_name, "WON " if sim.state == RunSim.State.WON else "LOST",
				sim.wave_index, sim.total_waves(), sim.lives, sim.starting_lives, MetaProgress.stars_for(sim),
				sim.towers.size(), sim.gold, _wave_summary(), Time.get_ticks_msec() - started])
	registry.free()
	# Plain play exits with 1 if the bot lost a stage, so CI can check the balance (--check is the
	# same as no option; it only says so in the workflow).
	quit(1 if lost > 0 else 0)


var _registry: Node
## The map --skirmish tunes.
var _skirmish_map := SKIRMISH_MAP
## The expected profile before each stage, by stage id, from PROFILES. Empty plays with no meta.
var _profiles: Dictionary = {}
var _metas: Dictionary = {}


func _load_profiles() -> void:
	if not FileAccess.file_exists(PROFILES):
		print("No %s: playing with an empty profile" % PROFILES)
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(PROFILES))
	if parsed is Dictionary:
		_profiles = parsed


## The stage's run, as the expected player of that point in the campaign would start it.
func _config(meta: MetaProgress, stage: StageData) -> RunConfig:
	if not _profiles.has(String(stage.id)):
		return meta.stage_config(stage.id)
	if not _metas.has(stage.id):
		_metas[stage.id] = MetaProgress.new(_registry, PlayerProfile.from_dict(_profiles[String(stage.id)]))
	var stage_meta: MetaProgress = _metas[stage.id]
	return stage_meta.add_heroes(stage_meta.stage_config(stage.id))


## How long each wave of the last _play took, in seconds from its start until its last enemy fell.
var _wave_seconds: PackedFloat32Array = []


func _play(meta: MetaProgress, stage: StageData) -> RunSim:
	var config := _config(meta, stage)
	# --health=X and --boss=X try other numbers than tuning.py's without regenerating the data.
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--health="):
			config.wave_set.health_scale = float(arg.trim_prefix("--health="))
		if arg.begins_with("--boss="):
			for wave in config.wave_set.waves:
				if wave.is_boss:
					wave.health_multiplier = float(arg.trim_prefix("--boss="))
		if arg.begins_with("--boss-life="):
			config.wave_set.boss_health_scale = float(arg.trim_prefix("--boss-life="))
	var sim := RunSim.new(config)
	var bot := AutoPlayer.for_sim(sim)
	_wave_seconds.clear()
	sim.wave_cleared.connect(func(_n: int, _p: int, _g: int) -> void: _wave_seconds.append(sim.time_in_wave))
	var elapsed := 0.0
	if OS.get_cmdline_user_args().has("--trace"):
		_trace(sim, func() -> float: return elapsed)
	while not sim.is_over() and elapsed < 8000.0:
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	return sim


## --trace prints the bosses, their forms and every leak as the run goes.
func _trace(sim: RunSim, clock: Callable) -> void:
	var at := func() -> String: return "%6.0f s  wave %2d  lives %3d  " % [clock.call(), sim.wave_number(), sim.lives]
	sim.boss_arrived.connect(func(e: SimEnemy) -> void: print(at.call(), "boss ", e.data.id))
	sim.enemy_transformed.connect(func(e: SimEnemy, _from: EnemyData) -> void: print(at.call(), "changes into ", e.data.id))
	sim.boss_fled.connect(func(e: SimEnemy) -> void: print(at.call(), "flees ", e.data.id))
	sim.enemy_leaked.connect(func(e: SimEnemy) -> void: print(at.call(), "leaked ", e.data.id))


## Average and longest wave of the last _play, and the whole time spent in waves.
func _wave_summary() -> String:
	if _wave_seconds.is_empty():
		return "waves -"
	var total := 0.0
	var longest := 0.0
	for seconds in _wave_seconds:
		total += seconds
		longest = maxf(longest, seconds)
	return "wave avg %3ds max %3ds  fighting %4.1f min" % [roundi(total / _wave_seconds.size()), roundi(longest), total / 60.0]


## Kinds of bot to compare: name, upgrades, skills, ascends, upgrade bias.
const BOTS := [
	["plain", false, false, false, 1.0], ["skills", false, true, false, 1.0], ["up 1.0", true, true, true, 1.0],
	["up 0.6", true, true, true, 0.6], ["up 0.35", true, true, true, 0.35], ["lvl 0.6", true, true, false, 0.6],
	["up 0.6 quiet", true, false, true, 0.6],
]


func _set_up(bot: AutoPlayer, kind: Array) -> void:
	bot.upgrades = kind[1]
	bot.skills = kind[2]
	bot.ascends = kind[3]
	bot.upgrade_bias = kind[4]


func _run_bot(sim: RunSim, bot: AutoPlayer) -> String:
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 4000.0:
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	if sim.state == RunSim.State.WON:
		return "%3d%%" % roundi(100.0 * sim.lives / sim.starting_lives)
	return " w%-2d" % sim.wave_index


## A table: one row per stage (and per skirmish plan), one column per kind of bot. A cell is the
## share of lives kept, or the wave the bot fell on.
func _compare(registry: Node, meta: MetaProgress) -> void:
	var header := "%-12s" % "COMPARE"
	for kind: Array in BOTS:
		header += " %12s" % kind[0]
	print(header)
	var wins: Array[int] = []
	var kept: Array[int] = []
	wins.resize(BOTS.size())
	kept.resize(BOTS.size())
	var rows: Array[Array] = [["skirmish A", &"", AutoPlayer.DEFAULT_NODES, AutoPlayer.DEFAULT_TOWERS],
			["skirmish B", &"", OTHER_NODES, OTHER_TOWERS]]
	for campaign in meta.campaigns_in_order():
		for stage in campaign.stages:
			rows.append([String(stage.id), stage.id])
	for row: Array in rows:
		var line := "%-12s" % row[0]
		for i in BOTS.size():
			var sim: RunSim
			var bot: AutoPlayer
			if row.size() > 2:
				sim = RunSim.new(RunConfig.from_registry(registry, SKIRMISH_MAP))
				bot = AutoPlayer.new(sim, row[2], row[3])
			else:
				sim = RunSim.new(meta.stage_config(row[1]))
				bot = AutoPlayer.for_sim(sim)
			_set_up(bot, BOTS[i])
			var cell := _run_bot(sim, bot)
			line += " %12s" % cell
			if sim.state == RunSim.State.WON:
				wins[i] += 1
				kept[i] += roundi(100.0 * sim.lives / sim.starting_lives)
		print("COMPARE " + line)
	var total := "%-12s" % "wins/lives"
	for i in BOTS.size():
		total += " %12s" % ("%d/%d" % [wins[i], kept[i]])
	print("COMPARE " + total)


## A table for --skill-levels: one row per stage, the bot as it is against the same bot buying skill
## levels with spare gold (half its gold goes on them at most), with the gold it put into them.
func _compare_skill_levels(meta: MetaProgress, only: String) -> void:
	print("%-12s %12s %12s %8s" % ["LEVELS", "skills", "+levels", "gold"])
	var kept: Array[int] = [0, 0]
	var wins: Array[int] = [0, 0]
	for campaign in meta.campaigns_in_order():
		for stage in campaign.stages:
			if not only.is_empty() and stage.id != only:
				continue
			var line := "%-12s" % stage.id
			var spent := 0
			for i in 2:
				var sim := RunSim.new(_config(meta, stage))
				var bot := AutoPlayer.for_sim(sim)
				bot.skill_upgrades = i == 1
				var elapsed := 0.0
				while not sim.is_over() and elapsed < 8000.0:
					bot.act()
					sim.step(RunSim.STEP)
					elapsed += RunSim.STEP
				line += " %12s" % ("%3d%%" % roundi(100.0 * sim.lives / sim.starting_lives) if sim.state == RunSim.State.WON else " w%-2d" % sim.wave_index)
				spent = bot.skill_gold
				if sim.state == RunSim.State.WON:
					wins[i] += 1
					kept[i] += roundi(100.0 * sim.lives / sim.starting_lives)
			print("LEVELS " + line + " %8d" % spent)
	print("LEVELS %-12s %12s %12s" % ["wins/lives", "%d/%d" % [wins[0], kept[0]], "%d/%d" % [wins[1], kept[1]]])


## Kinds of play for --heroes: name, skills, heroes. All of them level and ascend towers.
const HERO_BOTS := [["build", false, false], ["skills", true, false], ["heroes", false, true], ["all", true, true]]


## A table: one row per stage, one column per kind of play. A cell is the share of lives kept (or
## the wave the bot fell on); "heroes" and "all" also show the share of tower damage the heroes
## dealt. The party is the three heroes who joined last before the stage, as a player going through
## the campaigns in order would bring.
func _compare_heroes(meta: MetaProgress, only: String) -> void:
	var header := "%-12s %-28s" % ["HEROES", "party"]
	for kind: Array in HERO_BOTS:
		header += " %12s" % kind[0]
	print(header)
	var joined: Array[HeroData] = []
	for hero in meta.heroes_in_order():
		if hero.joins_after.is_empty() and hero.arrives_in.is_empty():
			joined.append(hero)
	var wins: Array[int] = []
	var kept: Array[int] = []
	wins.resize(HERO_BOTS.size())
	kept.resize(HERO_BOTS.size())
	for campaign in meta.campaigns_in_order():
		for stage in campaign.stages:
			var party: Array[HeroData] = joined.slice(maxi(0, joined.size() - HeroData.MAX_PARTY))
			if only.is_empty() or stage.id == only:
				var names: PackedStringArray = []
				for hero in party:
					names.append(String(hero.id))
				var line := "%-12s %-28s" % [stage.id, ",".join(names)]
				for i in HERO_BOTS.size():
					var config := meta.stage_config(stage.id)
					config.heroes = party.duplicate()
					var sim := RunSim.new(config)
					var bot := AutoPlayer.for_sim(sim)
					bot.skills = HERO_BOTS[i][1]
					bot.heroes = HERO_BOTS[i][2]
					var cell := _run_bot(sim, bot)
					if HERO_BOTS[i][2]:
						var hero_damage := 0.0
						var all_damage := 0.0
						for tower in sim.towers:
							all_damage += tower.damage_dealt
							if tower.is_hero():
								hero_damage += tower.damage_dealt
						cell += " h%2d%%" % roundi(100.0 * hero_damage / maxf(1.0, all_damage))
					line += " %12s" % cell
					if sim.state == RunSim.State.WON:
						wins[i] += 1
						kept[i] += roundi(100.0 * sim.lives / sim.starting_lives)
				print("HEROES " + line)
			for hero in meta.heroes_in_order():
				if hero.joins_after == stage.id:
					joined.append(hero)
	var total := "%-12s %-28s" % ["wins/lives", ""]
	for i in HERO_BOTS.size():
		total += " %12s" % ("%d/%d" % [wins[i], kept[i]])
	print("HEROES " + total)


## Plays a skirmish run with one plan and returns the share of lives it kept, or -1 if it lost.
func _play_skirmish(registry: Node, nodes: Array[StringName], towers: Array[StringName]) -> float:
	var sim := RunSim.new(RunConfig.from_registry(registry, _skirmish_map))
	var bot := AutoPlayer.new(sim, nodes, towers)
	var elapsed := 0.0
	while not sim.is_over() and elapsed < 4000.0:
		bot.act()
		sim.step(RunSim.STEP)
		elapsed += RunSim.STEP
	return float(sim.lives) / float(sim.starting_lives) if sim.state == RunSim.State.WON else -1.0


## Bisects the skirmish waves' health scale: the highest at which both plans still win and keep
## SKIRMISH_TARGET of their lives between them.
func _tune_skirmish(registry: Node) -> void:
	var config := RunConfig.from_registry(registry, _skirmish_map)
	var waves := config.wave_set
	var low := 0.1
	var high := 5.0
	for step in 9:
		waves.health_scale = (low + high) * 0.5
		var first := -1.0
		var second := -1.0
		var main := AutoPlayer.main_element(config)
		if main.is_empty():
			first = _play_skirmish(registry, AutoPlayer.DEFAULT_NODES, AutoPlayer.DEFAULT_TOWERS)
			second = _play_skirmish(registry, OTHER_NODES, OTHER_TOWERS)
		else:
			# A land's map: mostly one element, so it is tuned for the player who brings what it fears.
			var plan := AutoPlayer.counter_plan(config, main)
			first = _play_skirmish(registry, plan[0], plan[1])
			second = first
		print("skirmish scale %.2f: default plan %.2f, other plan %.2f" % [waves.health_scale, first, second])
		if minf(first, second) > 0.0 and (first + second) * 0.5 >= SKIRMISH_TARGET:
			low = waves.health_scale
		else:
			high = waves.health_scale
	print("SKIRMISH %s health_scale = %.2f (growth %.2f)" % [waves.id, snappedf(low, 0.01), waves.health_growth])


## Bisects the stage's health scale: the highest scale at which the bot still wins with `target` of
## its lives left.
##
## Two passes: first the ordinary waves (with the boss waves made harmless) for the target plus a
## tenth, then the boss waves' own health multiplier, where the bot only needs to keep half the target.
## The numbers it prints already have a margin taken off.
func _tune(meta: MetaProgress, stage: StageData, target: float) -> void:
	var waves := meta.stage_config(stage.id).wave_set
	var bosses: Array[WaveData] = []
	for wave in waves.waves:
		if wave.is_boss:
			bosses.append(wave)
	var set_boss := func(value: float) -> void:
		for wave in bosses:
			wave.health_multiplier = value
	set_boss.call(0.02)
	var health := _bisect(meta, stage, target + (0.1 if not bosses.is_empty() else 0.0), 0.1, 20.0,
			func(value: float) -> void: waves.health_scale = value)
	waves.health_scale = health
	var boss := 0.0
	# If even a weak boss beats the bot, the waves before it are too strong for it to build up:
	# soften them and try again.
	for attempt in 6:
		if bosses.is_empty():
			break
		boss = _bisect(meta, stage, target * 0.5, 0.1, 8.0, set_boss)
		if boss > 0.2:
			break
		health = snappedf(health * 0.8, 0.01)
		waves.health_scale = health
	# The bot's result does not fall evenly as health rises, so take a margin and check that it
	# still wins there: 5% off, and another 5% for as long as it loses.
	var margin := 0.95
	for attempt in 6:
		waves.health_scale = health * margin
		set_boss.call(boss * margin)
		if _play(meta, stage).state == RunSim.State.WON:
			break
		margin *= 0.95
	var line := 'TUNING["%s"] = {"health": %.2f' % [stage.id, health * margin]
	if not bosses.is_empty():
		line += ', "boss": %.2f' % (boss * margin)
	print(line + "}")


## Share of lives the bot must keep for a stage's bosses to stay at full strength (see --tune-bosses).
const BOSS_LIFE_TARGET := 0.1


## --tune-bosses: the bosses keep their full life (EnemyData.max_health) wherever the bot still wins
## keeping BOSS_LIFE_TARGET of its lives. Elsewhere it finds the highest share of their life the bot can
## beat, with a 5% margin, and prints it as the stage's "boss_life" for tools/campaign/tuning.py.
func _tune_boss_life(meta: MetaProgress, stage: StageData) -> void:
	var waves := meta.stage_config(stage.id).wave_set
	var apply := func(value: float) -> void: waves.boss_health_scale = value
	apply.call(1.0)
	var sim := _play(meta, stage)
	if sim.state == RunSim.State.WON and sim.lives >= ceili(sim.starting_lives * BOSS_LIFE_TARGET):
		print('TUNING["%s"] boss_life 1.0 (full: lives %d/%d)' % [stage.id, sim.lives, sim.starting_lives])
		return
	var life := _bisect(meta, stage, BOSS_LIFE_TARGET, 0.05, 1.0, apply)
	var margin := 0.95
	for attempt in 6:
		apply.call(life * margin)
		if _play(meta, stage).state == RunSim.State.WON:
			break
		margin *= 0.95
	print('TUNING["%s"] boss_life %.2f' % [stage.id, life * margin])


## The highest value in [low, high] at which the bot still wins keeping `target` of its lives.
func _bisect(meta: MetaProgress, stage: StageData, target: float, low: float, high: float, apply: Callable) -> float:
	for step in 8:
		var mid := (low + high) * 0.5
		apply.call(mid)
		var sim := _play(meta, stage)
		if sim.state == RunSim.State.WON and sim.lives >= ceili(sim.starting_lives * target):
			low = mid
		else:
			high = mid
	apply.call(low)
	return snappedf(low, 0.01)
