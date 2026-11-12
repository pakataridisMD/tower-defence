extends Node
## Saves screenshots of the main menu, the meta tree, the skill web, a battle and the end screen
## while the AutoPlayer plays a run. It needs a real window, so run it on a desktop or under xvfb-run:
##   godot --path . --resolution 1920x1080 --fixed-fps 30 res://tools/capture.tscn -- --out=<folder>
## It plays with a made-up profile kept in memory, so it never touches a real save.
## Add --quick after `--` to skip the run and only take the menu, the meta tree and the skill web.
## Add --ui to take the menu and the HUD at its busiest instead: a tower selected, skills cast, one
## being aimed, and the Esc menu.
## Add --heroes to take the campaign party picker and a battle with three heroes on the board.
## Add --campaign to take the campaign map and a battle in each biome instead (each battle jumps
## straight to a late wave with plenty of gold, so the board is busy).
## Add --menu to take the title screen and every menu page (Skirmish, Heroes, Codex, Settings, Credits)
## and the quit question.
## Add --map to take the campaign world map: the next stage up close, the whole world, a land, a city at
## the closest zoom, and the Heartland and the citadel once every other stage is won.
## Add --bigmaps to take the big winding maps: a few battles with the whole map in view, then the same
## battle zoomed in on a spawn hole.
## Add --powers to film the horde's powers: a wave of every kind of the rank and file and the Warden
## against the bot's towers, saved as numbered frames in <out>/powers/ (make a GIF from them).
## Add --horde=<tide|stone|hollow|flame|sky|grove> with --powers to film that horde's five kinds instead,
## with the camera close and following them.
## Add --landmarks to take the enemy war camps and the defended cities at the road ends in every land,
## by day, at night and burning, plus frames for short clips (<out>/clips/<name>/NNN.png).
## Add --look[=stage,stage] for the graphics look test: in each stage (the fire and jungle lands by default)
## one of each base tower is built in a row by the road, then the whole map, the row up close at x1
## and x2, and the same row at night are taken.
## Add --edge to film the edge pan: zoomed in on a battle, the mouse is pushed against each edge of the
## screen in turn, saved as numbered frames in <out>/edge/ (make a clip from them).
## Add --story to take the cinematic player, a Herald's boss banner, the final level's defence and counter-attack and
## the campaign map with the citadel on it.

const MENU_SCENE := preload("res://scenes/main.tscn")
const META_TREE_SCENE := preload("res://scenes/meta/meta_tree.tscn")
const GAME_SCENE := preload("res://scenes/game/game.tscn")
const CAMPAIGN_SCENE := preload("res://scenes/campaign/campaign_map.tscn")
## Campaign battles to shoot: stage, wave to jump to (counted from 0), seconds into it.
const CAMPAIGN_SHOTS := [
	[&"ember_4", 14, 14.0], [&"storm_3", 9, 10.0], [&"nature_2", 8, 10.0], [&"water_3", 10, 10.0],
	[&"earth_4", 14, 12.0], [&"void_4", 14, 16.0], [&"converge_2", 12, 12.0], [&"converge_3", 19, 14.0],
]
## Big maps to shoot: stage (empty for the Switchback skirmish), wave to jump to, seconds into it.
const BIG_MAP_SHOTS := [
	[&"", 3, 12.0], [&"ember_2", 6, 14.0], [&"water_3", 8, 14.0], [&"void_4", 10, 14.0], [&"converge_3", 12, 16.0],
]
## Gives up on a moment after this many frames, so a broken run cannot hang the tool.
const MAX_WAIT_FRAMES := 40000

var _out := ""
var _quick := false
var _campaign := false
var _ui := false
var _story := false
var _heroes := false
var _menu := false
var _map := false
var _bigmaps := false
var _edge := false
var _powers := false
## With --bosses[=id,...]: film each boss on the road doing every move, with the voice cues.
var _bosses: PackedStringArray = []
var _landmarks := false
var _horde := &""
var _look: PackedStringArray = []
## With --look: shoot the towers' effects in a fight (shots, hits, a Meteor and a Doom) instead of the look shots.
var _fx_shots := false


func _ready() -> void:
	_out = OS.get_user_data_dir().path_join("shots")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			_out = arg.trim_prefix("--out=")
		elif arg == "--quick":
			_quick = true
		elif arg == "--campaign":
			_campaign = true
		elif arg == "--ui":
			_ui = true
		elif arg == "--edge":
			_edge = true
		elif arg == "--story":
			_story = true
		elif arg == "--heroes":
			_heroes = true
		elif arg == "--menu":
			_menu = true
		elif arg == "--map":
			_map = true
		elif arg == "--bigmaps":
			_bigmaps = true
		elif arg == "--powers":
			_powers = true
		elif arg.begins_with("--bosses"):
			_bosses = arg.trim_prefix("--bosses").trim_prefix("=").split(",", false)
			if _bosses.is_empty():
				_bosses = PackedStringArray(["vael_orrun", "gorrath", "cinder_tyrant", "pale_vesper", "vholt", "mountain_titan"])
		elif arg == "--landmarks":
			_landmarks = true
		elif arg.begins_with("--horde="):
			_horde = StringName(arg.trim_prefix("--horde="))
		elif arg == "--fx":
			_fx_shots = true
		elif arg.begins_with("--look"):
			_look = arg.trim_prefix("--look").trim_prefix("=").split(",", false)
			if _look.is_empty():
				_look = PackedStringArray(["ember_4", "nature_2"])
	DirAccess.make_dir_recursive_absolute(_out)
	Progress.use_memory_profile(_demo_profile())
	# The map's glide down from the whole world would still be moving in the first shots.
	CampaignScreen.intro_played = true
	if not _look.is_empty():
		_run_look()
	elif _powers:
		_run_powers()
	elif not _bosses.is_empty():
		_run_bosses()
	elif _landmarks:
		_run_landmarks()
	elif _menu:
		_run_menu()
	elif _map:
		_run_map()
	elif _bigmaps:
		_run_big_maps()
	elif _edge:
		_run_edge()
	elif _story:
		_run_story()
	elif _heroes:
		_run_heroes()
	elif _ui:
		_run_ui()
	elif _campaign:
		_run_campaign()
	else:
		_run()


## The menu, then a run set up by hand so the HUD has everything to show.
func _run_ui() -> void:
	var menu := MENU_SCENE.instantiate()
	add_child(menu)
	await _wait(0.6)
	await _shot("menu")
	menu.free()

	var game := GAME_SCENE.instantiate() as Game
	add_child(game)
	await _wait(0.3)
	var sim := game.sim
	sim.tree.points = 30
	for id: StringName in AutoPlayer.DEFAULT_NODES:
		sim.allocate_node(id)
	for id: StringName in [&"water_entry", &"earth_entry", &"void_entry"]:
		sim.allocate_node(id)
	sim.gold = 2500
	var bot := AutoPlayer.for_sim(sim)
	bot.build_towers()
	sim.gold = 900
	await _wait(0.3)
	await _shot("hud_help")
	# A tower selected: its numbers and its upgrade buttons.
	game.board.select(sim.towers[0])
	game.hud.show_shop_tier(2)
	await _wait(0.3)
	await _shot("hud_tower")
	# The Esc menu, and its question before leaving a run.
	game.open_pause_menu()
	await _wait(0.2)
	await _shot("pause_menu")
	game.pause_menu.ask_to_leave(&"menu")
	await _wait(0.2)
	await _shot("pause_menu_leave")
	game.close_pause_menu()
	sim.wave_index = 6
	game._start_wave()
	# The wave's announcement: its number and how it comes.
	await _until(func() -> bool: return sim.time_in_wave > 1.5 or sim.is_over())
	await _shot("wave_announce")
	await _until(func() -> bool: return sim.time_in_wave > 9.0 or sim.is_over())
	game._begin_skill(&"surge")
	game._begin_skill(&"tidal_wave")
	var target := _crowd(sim)
	game._begin_skill(&"meteor")
	Input.warp_mouse(game.board.to_global(target))
	_hover(game.board.to_global(target))
	await _wait(0.2)
	await _shot("hud_aiming")
	game._cast_skill(&"meteor", target)
	await _wait(0.12)
	await _shot("skill_meteor")
	game._begin_skill(&"earthquake")
	game._cast_skill(&"entangle", _crowd(sim))
	await _wait(0.15)
	await _shot("skill_cast")
	print("Screenshots saved to ", _out)
	get_tree().quit()


## The party picker, then a battle with the party summoned: one hero selected, one ability aimed.
func _run_heroes() -> void:
	Progress.use_memory_profile(_campaign_profile())
	var screen := CAMPAIGN_SCENE.instantiate() as CampaignScreen
	add_child(screen)
	await _wait(0.4)
	screen.select(&"storm_3")
	await _wait(0.6)
	await _shot("heroes_party")
	screen.free()
	Progress.active_stage = &"storm_3"
	var game := GAME_SCENE.instantiate() as Game
	add_child(game)
	await _wait(0.3)
	var sim := game.sim
	sim.gold = 3000
	sim.tree.points = 14
	var bot := AutoPlayer.for_sim(sim)
	bot.build_towers()
	await _wait(0.3)
	var heroes := sim.hero_towers()
	if not heroes.is_empty():
		game.board.select(heroes[0])
	await _wait(0.3)
	await _shot("heroes_building")
	sim.wave_index = 8
	game._start_wave()
	await _until(func() -> bool: return sim.time_in_wave > 10.0 or sim.is_over())
	if heroes.size() > 1:
		var target := _crowd(sim)
		game._begin_hero(heroes[1].hero.id)
		Input.warp_mouse(game.board.to_global(target))
		_hover(game.board.to_global(target))
		await _wait(0.2)
		await _shot("heroes_aiming")
		if game.board.aiming_hero == heroes[1].hero.id:
			game._cast_hero(heroes[1].hero.id, target)
		await _wait(0.15)
		await _shot("heroes_ability")
	print("Screenshots saved to ", _out)
	get_tree().quit()


## Where the most enemies stand close together, or the middle of the board if there are none.
static func _crowd(sim: RunSim) -> Vector2:
	var best := sim.config.map.size_in_pixels() * 0.5
	var most := 0
	for center in sim.enemies:
		var count := 0
		for other in sim.enemies:
			if other.alive and other.position.distance_to(center.position) < 110.0:
				count += 1
		if center.alive and count > most:
			most = count
			best = center.position
	return best


## Ember Reach and the Thunder Steppe done, two more under way.
static func _campaign_profile() -> PlayerProfile:
	var profile := _demo_profile()
	for pair: Array in [[&"ember_1", 3], [&"ember_2", 3], [&"ember_3", 2], [&"ember_4", 1], [&"storm_1", 3],
			[&"storm_2", 2], [&"storm_3", 2], [&"storm_4", 2], [&"nature_1", 3], [&"nature_2", 1], [&"void_1", 2],
			[&"water_1", 3], [&"earth_1", 1]]:
		profile.stage_stars[pair[0]] = pair[1]
	return profile


func _run_map() -> void:
	Progress.use_memory_profile(_campaign_profile())
	var screen := CAMPAIGN_SCENE.instantiate() as CampaignScreen
	add_child(screen)
	await _wait(0.6)
	await _shot("map_stage")
	screen.show_whole_world()
	await _wait(0.9)
	_hover(screen.stage_position(&"water_2"))
	await _wait(0.2)
	await _shot("map_world")
	screen.select(&"ember_3")
	await _wait(0.8)
	await _shot("map_land")
	screen.zoom_step(1)
	await _wait(0.6)
	screen.zoom_step(1)
	await _wait(0.6)
	screen.select(&"ember_4")
	await _wait(0.6)
	await _shot("map_close")
	screen.free()
	var profile := _campaign_profile()
	for stage: StageData in DataRegistry.stages.values():
		if not stage.id in [&"assault_1", &"converge_3"]:
			profile.stage_stars[stage.id] = 3
	Progress.use_memory_profile(profile)
	screen = CAMPAIGN_SCENE.instantiate() as CampaignScreen
	add_child(screen)
	await _wait(0.6)
	screen.select(&"converge_3")
	await _wait(0.8)
	await _shot("map_heartland")
	profile.stage_stars[&"converge_3"] = 3
	screen.select(&"assault_1")
	await _wait(0.9)
	await _shot("map_citadel")
	screen.free()
	print("Screenshots saved to ", _out)
	get_tree().quit()


func _run_campaign() -> void:
	Progress.use_memory_profile(_campaign_profile())
	var screen := CAMPAIGN_SCENE.instantiate() as CampaignScreen
	add_child(screen)
	await _wait(0.4)
	screen.select(&"nature_3")
	await _wait(0.6)
	_hover(screen.stage_position(&"storm_4"))
	await _wait(0.2)
	await _shot("campaign_map")
	screen.select(&"converge_3")
	await _wait(0.6)
	await _shot("campaign_convergence")
	screen.free()
	for entry: Array in CAMPAIGN_SHOTS:
		Progress.active_stage = entry[0]
		var game := GAME_SCENE.instantiate() as Game
		game.autoplay = true
		add_child(game)
		await _wait(0.2)
		game.sim.wave_index = entry[1]
		game.sim.gold = 6000
		game.sim.tree.points = 14
		await _until(func() -> bool: return game.sim.state == RunSim.State.WAVE and game.sim.time_in_wave > entry[2] \
				or game.sim.is_over())
		await _shot("stage_" + String(entry[0]))
		game.free()
		await _wait(0.1)
	print("Screenshots saved to ", _out)
	get_tree().quit()


const LOOK_TOWERS: Array[StringName] = [&"fire_brazier", &"storm_spire", &"nature_thornbush",
		&"water_wellspring", &"earth_monolith", &"void_obelisk"]


func _run_look() -> void:
	Progress.use_memory_profile(_campaign_profile())
	for stage in _look:
		if stage == "skirmish":
			Progress.play_skirmish()
		else:
			Progress.active_stage = StringName(stage)
		var game := GAME_SCENE.instantiate() as Game
		game.autoplay = true
		add_child(game)
		await _wait(0.2)
		var sim := game.sim
		sim.tree.points = 30
		for id: StringName in [&"fire_entry", &"storm_entry", &"nature_entry", &"water_entry", &"earth_entry", &"void_entry"]:
			sim.allocate_node(id)
		sim.gold = 9000
		var row := _look_row(game)
		sim.wave_index = 6
		_light(game.board.art, DayNight.DAY)
		if _fx_shots:
			await _fx_fight(game, stage, row)
			game.free()
			await _wait(0.1)
			continue
		await _until(func() -> bool: return sim.state == RunSim.State.WAVE and sim.time_in_wave > 9.0 or sim.is_over())
		await _shot("look_%s_whole" % stage)
		game.camera.set_view(1.0, row)
		await _wait(0.4)
		await _shot("look_%s_x1" % stage)
		game.camera.set_view(2.0, row)
		await _wait(0.4)
		await _shot("look_%s_x2" % stage)
		_light(game.board.art, DayNight.NIGHT)
		game.camera.set_view(1.0, row)
		await _wait(2.5)
		await _shot("look_%s_night" % stage)
		game.free()
		await _wait(0.1)
	print("Screenshots saved to ", _out)
	get_tree().quit()


## Close shots of a fight: the enemy with the most towers around it, the shots flying at it, then a
## Meteor and a Doom cast on it.
func _fx_fight(game: Game, stage: String, _row: Vector2) -> void:
	var sim := game.sim
	var hottest := func() -> SimEnemy:
		var best: SimEnemy = null
		var best_count := 0
		for enemy in sim.enemies:
			if not enemy.alive:
				continue
			var count := 0
			for tower in sim.towers:
				if tower.position.distance_to(enemy.position) < 260.0:
					count += 1
			if count > best_count:
				best = enemy
				best_count = count
		return best
	await _until(func() -> bool: return sim.state == RunSim.State.WAVE and sim.time_in_wave > 14.0 or sim.is_over())
	var target: SimEnemy = hottest.call()
	if target == null:
		push_warning("Capture: no fight to shoot")
		return
	game.camera.set_view(2.0, target.position)
	await _wait(0.5)
	await _shot("fx_%s_1" % stage)
	await _wait(0.3)
	await _shot("fx_%s_2" % stage)
	for skill_id: StringName in [&"meteor", &"doom"]:
		target = hottest.call()
		if target != null:
			game.camera.set_view(2.0, target.position)
			sim.use_skill(skill_id, target.position)
		await _wait(0.15)
		await _shot("fx_%s_%s" % [stage, skill_id])
		await _wait(0.8)


## Builds one of each base tower in free cells next to the road, a third of the way along, and returns
## the board point in the middle of them.
func _look_row(game: Game) -> Vector2:
	var sim := game.sim
	var map := sim.config.map
	var path := map.path_points(0)
	var target := path[int(path.size() * 0.35)]
	var cells: Array[Vector2i] = []
	for y in map.grid_size.y:
		for x in map.grid_size.x:
			cells.append(Vector2i(x, y))
	cells.sort_custom(func(a: Vector2i, b: Vector2i) -> bool:
		return map.cell_center(a).distance_to(target) < map.cell_center(b).distance_to(target))
	var built: Array[Vector2] = []
	for tower_id in LOOK_TOWERS:
		for cell in cells:
			if sim.can_place(tower_id, cell):
				sim.gold = maxi(sim.gold, 2000)
				if sim.place_tower(tower_id, cell) != null:
					built.append(map.cell_center(cell))
				break
	var middle := Vector2.ZERO
	for p in built:
		middle += p
	return middle / maxf(built.size(), 1.0) if not built.is_empty() else target


func _run_big_maps() -> void:
	Progress.use_memory_profile(_campaign_profile())
	for entry: Array in BIG_MAP_SHOTS:
		if String(entry[0]).is_empty():
			Progress.play_skirmish()
		else:
			Progress.active_stage = entry[0]
		var game := GAME_SCENE.instantiate() as Game
		game.autoplay = true
		add_child(game)
		await _wait(0.2)
		game.sim.wave_index = entry[1]
		game.sim.gold = 6000
		game.sim.tree.points = 14
		await _until(func() -> bool: return game.sim.state == RunSim.State.WAVE and game.sim.time_in_wave > entry[2] \
				or game.sim.is_over())
		var shot_name := "bigmap_" + (String(entry[0]) if not String(entry[0]).is_empty() else "switchback")
		await _shot(shot_name)
		# Up close: the first spawn hole, or where the road comes in.
		var map := game.sim.config.map
		var lane := map.hole_lanes[0] if not map.hole_lanes.is_empty() else 0
		game.camera.set_view(1.0, map.path_points(lane)[0])
		await _wait(0.3)
		await _shot(shot_name + "_close")
		game.free()
		await _wait(0.1)
	print("Screenshots saved to ", _out)
	get_tree().quit()


func _run_story() -> void:
	# The cinematic player: the prologue's title card, then two of its shots.
	var player := CinematicPlayer.new()
	player.queue = [&"prologue", &"ember_herald"] as Array[StringName]
	player.change_scene_when_done = false
	player.mark_seen = false
	add_child(player)
	await _wait(1.6)
	await _shot("story_title")
	for shot in [0, 4, 9]:
		while player.current_id() == &"prologue" and player.current_shot() < shot:
			player.next_shot()
			await _wait(CinematicPlayer.FADE * 2.0 + 0.2)
		await _wait(2.5)
		await _shot("story_prologue_%02d" % (shot + 1))
	player.skip_cinematic()
	await _wait(CinematicPlayer.FADE * 2.0 + 1.2)
	player.next_shot()
	await _wait(CinematicPlayer.FADE * 2.0 + 2.5)
	await _shot("story_herald_scene")
	player.free()

	# A Herald leads the last wave of its element's second stage.
	for entry: Array in [[&"ember_2", "story_herald_boss"], [&"water_2", "story_saltmother"]]:
		Progress.active_stage = entry[0]
		var game := GAME_SCENE.instantiate() as Game
		game.autoplay = true
		add_child(game)
		await _wait(0.2)
		game.sim.wave_index = game.sim.total_waves() - 1
		game.sim.gold = 6000
		game.sim.tree.points = 14
		await _until(func() -> bool: return game.sim.strongest_boss() != null and game.sim.time_in_wave > 9.0 \
				or game.sim.is_over())
		await _shot(entry[1])
		game.free()
		await _wait(0.1)

	# The final level: the defence before the citadel, then the counter-attack with the army at its gates.
	Progress.active_stage = &"assault_1"
	var assault := GAME_SCENE.instantiate() as Game
	assault.autoplay = true
	add_child(assault)
	await _until(func() -> bool: return assault.sim.wave_number() >= 4 and assault.sim.time_in_wave > 8.0 \
			or assault.sim.is_over())
	await _shot("story_assault_gate")
	# The turning's own scene would hold the battle still: this picture is of the fight after it.
	Progress.mark_seen(&"the_turning")
	assault.sim.enemies.clear()
	assault.sim.wave_index = assault.sim.config.stage.counter_wave - 1
	assault.sim.start_next_wave()
	assault.sim.gold = 2400
	# No towers were built in the waves skipped: keep the run alive for the picture.
	assault.sim.lives = 9999
	Engine.time_scale = 4.0
	var citadel: SimEnemy = assault.sim.structures[0]
	await _until(func() -> bool: return citadel.health < 0.8 * citadel.max_health or assault.sim.is_over())
	Engine.time_scale = 1.0
	await _wait(1.0)
	await _shot("story_counter_attack")
	assault.free()

	# The campaign map once the Convergence is won: the road to the citadel opens.
	var profile := _campaign_profile()
	for stage: StageData in DataRegistry.stages.values():
		if stage.id != &"assault_1":
			profile.stage_stars[stage.id] = 3
	Progress.use_memory_profile(profile)
	var screen := CAMPAIGN_SCENE.instantiate() as CampaignScreen
	add_child(screen)
	await _wait(0.4)
	screen.select(&"assault_1")
	await _wait(0.8)
	await _shot("story_campaign_citadel")
	screen.free()
	print("Screenshots saved to ", _out)
	get_tree().quit()


## A player some way into the campaign: the storm land done, part of the economy wing and one
## map unlocked, a few points left to spend.
static func _demo_profile() -> PlayerProfile:
	var profile := PlayerProfile.new()
	profile.meta_points_earned = 75
	profile.meta_nodes = [&"command_gold", &"command_purse", &"command_levy", &"command_salvage", &"command_tithe",
		&"starpath_30", &"starpath_15", &"starpath_0", &"mastery_storm", &"storm_focus", &"storm_power", &"storm_heart",
		&"storm_haste", &"mastery_range", &"mastery_will", &"expedition_serpentine", &"arsenal_edge", &"arsenal_drill",
		&"arsenal_cadence", &"arsenal_cadence_2"]
	profile.runs_played = 3
	profile.runs_won = 1
	profile.best_waves = 10
	profile.enemies_killed = 412
	return profile


func _run_menu() -> void:
	# Two stages won in the first land, so Continue and the story card show.
	var first: CampaignData = Progress.meta.campaigns_in_order()[0]
	Progress.meta.profile.stage_stars[first.stages[0].id] = 3
	Progress.meta.profile.stage_stars[first.stages[1].id] = 2
	var menu := MENU_SCENE.instantiate()
	add_child(menu)
	await _wait(0.5)
	_hover(menu.buttons[&"continue"].get_global_rect().get_center())
	await _wait(0.2)
	await _shot("menu_title")
	for id: StringName in [&"skirmish", &"heroes", &"codex", &"settings", &"credits"]:
		menu.open_page(id)
		await _wait(0.3)
		await _shot("menu_" + id)
	menu.pages[&"codex"].show_tab(1)
	menu.open_page(&"codex")
	await _wait(0.3)
	await _shot("menu_codex_enemies")
	menu.pages[&"settings"].show_tab(1)
	menu.open_page(&"settings")
	await _wait(0.3)
	await _shot("menu_settings_video")
	menu.close_page()
	menu.ask_to_quit()
	await _wait(0.3)
	await _shot("menu_quit")
	get_tree().quit()


func _run() -> void:
	var menu := MENU_SCENE.instantiate()
	add_child(menu)
	await _wait(0.5)
	await _shot("menu")
	menu.free()

	var meta_tree := META_TREE_SCENE.instantiate()
	add_child(meta_tree)
	await _wait(0.5)
	_hover(meta_tree.web.screen_position(&"arsenal_hoard"))
	await _wait(0.2)
	await _shot("meta_tree")
	meta_tree.web.show_whole_tree()
	_hover(Vector2(4, 4))
	await _wait(0.3)
	await _shot("meta_tree_whole")
	meta_tree.web.zoom_by(3.0, meta_tree.web.screen_position(&"storm_heart"))
	_hover(meta_tree.web.screen_position(&"storm_overload"))
	await _wait(0.3)
	await _shot("meta_tree_close")
	meta_tree.free()

	var game := GAME_SCENE.instantiate() as Game
	if _quick:
		add_child(game)
		await _wait(0.3)
		game._toggle_web()
		await _wait(0.3)
		_hover(game.web.screen_position(&"bridge_plasma"))
		await _wait(0.2)
		await _shot("skill_web_start")
		print("Screenshots saved to ", _out)
		get_tree().quit()
		return
	game.autoplay = true
	add_child(game)
	await _until(func() -> bool: return game.sim.wave_index >= 1 and game.sim.state == RunSim.State.WAVE \
			and game.sim.time_in_wave > 8.0)
	await _shot("early_wave")
	# The web as the bot opens it, before it spends its point, with the mouse over an open node.
	await _until(func() -> bool: return game.sim.wave_index >= 5 and game.web.visible)
	await _wait(0.3)
	_hover(game.web.screen_position(&"storm_core"))
	await get_tree().process_frame
	await _shot("skill_web")
	await _until(func() -> bool: return game.sim.wave_index >= 6 and game.sim.state == RunSim.State.WAVE \
			and game.sim.time_in_wave > 14.0)
	await _shot("battle")
	# The last wave is fought at night, by the light of the towers.
	await _until(func() -> bool: return game.sim.wave_index >= game.sim.total_waves() - 1 \
			and game.sim.state == RunSim.State.WAVE and game.sim.time_in_wave > 12.0)
	await _shot("night_battle")
	await _until(func() -> bool: return game.sim.is_over())
	await _wait(1.0)
	await _shot("end")
	print("Screenshots saved to ", _out)
	get_tree().quit()


func _run_powers() -> void:
	var game := GAME_SCENE.instantiate() as Game
	game.autoplay = true
	add_child(game)
	await _wait(0.2)
	# Real time, not the bot's top speed, so the film plays as a person sees it.
	game._speed_index = 0
	game.hud.speed = Game.SPEEDS[0]
	game.sim.gold = 900
	game.sim.tree.points = 6
	var wave := WaveData.new()
	wave.element = &"void"
	var groups: Array[SpawnGroup] = []
	for entry: Array in [[&"grunt", 6, 0.7, 0.0], [&"brute", 2, 1.6, 2.0], [&"mender", 2, 2.0, 3.0],
			[&"runner", 4, 0.9, 5.0], [&"splitter", 2, 2.5, 7.0], [&"warded", 3, 1.6, 8.0], [&"warden", 1, 1.0, 11.0]]:
		var group := SpawnGroup.new()
		group.enemy = entry[0]
		group.count = entry[1]
		group.spawn_interval = entry[2]
		group.start_delay = entry[3]
		groups.append(group)
	if not _horde.is_empty():
		groups = _horde_groups(_horde)
	wave.groups = groups
	var waves := WaveSet.new()
	waves.id = &"powers"
	waves.health_growth = 1.0
	waves.waves = [wave, wave] as Array[WaveData]
	game.sim.config.wave_set = waves
	await _until(func() -> bool: return game.sim.state == RunSim.State.WAVE)
	var folder := _out.path_join("powers")
	DirAccess.make_dir_recursive_absolute(folder)
	var count := [0]
	game.sim.enemy_power.connect(func(enemy: SimEnemy, power: StringName, _t: Array) -> void:
		print("frame %d: %s %s" % [count[0], enemy.data.id, power]))
	var follow := Vector2.INF
	while game.sim.state == RunSim.State.WAVE and count[0] < 900:
		if not _horde.is_empty():
			follow = _follow_horde(game, follow)
		await RenderingServer.frame_post_draw
		if Engine.get_process_frames() % 2 == 0:
			var image := get_viewport().get_texture().get_image()
			image.save_png(folder.path_join("f_%04d.png" % count[0]))
			count[0] += 1
		await get_tree().process_frame
	print("Saved %d frames to %s" % [count[0], folder])
	get_tree().quit()


## Each boss in turn walks on, and is made to go through its moves while the camera follows it:
## frames in <out>/bosses/f_NNNN.png and the voice lines it says, by frame, in <out>/bosses/cues.json
## (tools/art/boss_film.py turns them into a film with sound). --fixed-fps 30 keeps frames and time in step.
func _run_bosses() -> void:
	var game := GAME_SCENE.instantiate() as Game
	add_child(game)
	await _wait(0.2)
	game._speed_index = 0
	game.hud.speed = Game.SPEEDS[0]
	var waves := WaveSet.new()
	waves.id = &"bosses"
	waves.health_growth = 1.0
	var list: Array[WaveData] = []
	for boss_id in _bosses:
		var wave := WaveData.new()
		wave.element = &"void"
		var group := SpawnGroup.new()
		group.enemy = StringName(boss_id)
		group.count = 1
		wave.groups = [group] as Array[SpawnGroup]
		list.append(wave)
	waves.waves = list
	game.sim.config.wave_set = waves
	var folder := _out.path_join("bosses")
	DirAccess.make_dir_recursive_absolute(folder)
	var cues: Array = []
	var count := [0]
	game.bosses.voice.spoke.connect(func(_b: StringName, _k: StringName, text: String, _s: float) -> void:
		cues.append({"frame": count[0], "file": game.bosses.voice.last_file, "text": text}))
	var script := [[&"attack", &"taunt"], [&"cast", &"bind"], [&"slam", &""], [&"guard", &"shield"],
		[&"hurt", &"hurt"], [&"roar", &"enrage"], [&"attack", &"taunt"]]
	for boss_id in _bosses:
		game.sim.start_next_wave()
		await _until(func() -> bool: return not game.sim.enemies.is_empty())
		var boss: SimEnemy = game.sim.enemies[0]
		# Far enough along the road to be in the open.
		boss.progress = game.sim.lane_lengths[boss.lane] * 0.45
		boss.position = game.sim.lane_curves[boss.lane].sample_baked(boss.progress)
		var tall := BoardArt.enemy_height(boss.data.id)
		var zoom := 0.75 if tall > 300.0 else 1.0 if tall > 200.0 else 1.5
		var step := 0
		var next := 4.0
		var t := 0.0
		while t < 4.0 + script.size() * 2.6 + 1.0:
			game.camera.set_view(zoom, boss.position + Vector2(0, -BoardArt.enemy_height(boss.data.id) * 0.25))
			if t >= next and step < script.size():
				var item: Array = script[step]
				game.bosses.act(boss, item[0], item[1], item[0] == &"guard")
				if item[0] == &"guard":
					get_tree().create_timer(1.6).timeout.connect(func() -> void: game.board.art.release_boss_move(boss, &"guard"))
				step += 1
				next += 2.6
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(folder.path_join("f_%04d.png" % count[0]))
			count[0] += 1
			t += 1.0 / 30.0
			await get_tree().process_frame
		boss.alive = false
		await _until(func() -> bool: return game.sim.state != RunSim.State.WAVE)
	var file := FileAccess.open(folder.path_join("cues.json"), FileAccess.WRITE)
	file.store_string(JSON.stringify(cues, " "))
	file.close()
	print("Saved %d frames and %d voice cues to %s" % [count[0], cues.size(), folder])
	get_tree().quit()


## One group for each kind of a horde, in the order its land meets them, a few seconds apart.
func _horde_groups(horde: StringName) -> Array[SpawnGroup]:
	var kinds: Array[EnemyData] = []
	for data: EnemyData in DataRegistry.enemies.values():
		if data.horde == horde:
			kinds.append(data)
	var groups: Array[SpawnGroup] = []
	for i in kinds.size():
		var group := SpawnGroup.new()
		group.enemy = kinds[i].id
		group.count = 6 if kinds[i].power == &"swarm" else 3
		group.spawn_interval = 0.8
		group.start_delay = 1.5 * float(i)
		groups.append(group)
	return groups


## Keeps the camera close on the middle of the horde, easing after it. Every kind carries its power.
func _follow_horde(game: Game, follow: Vector2) -> Vector2:
	var sum := Vector2.ZERO
	var n := 0
	for enemy in game.sim.enemies:
		if enemy.alive and not enemy.structure:
			if not enemy.raised:
				enemy.has_power = true
			sum += enemy.position
			n += 1
	if n == 0:
		return follow
	var middle := sum / float(n)
	follow = middle if follow == Vector2.INF else follow.lerp(middle, 0.04)
	game.camera.set_view(1.5, follow)
	return follow


func _hover(at: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = at
	motion.global_position = at
	Input.parse_input_event(motion)


## Stages whose camps and cities are shot, one per land, and the clip stages.
const LANDMARK_STAGES: Array[StringName] = [&"ember_1", &"storm_2", &"nature_1", &"water_1", &"earth_3", &"void_1", &"converge_1"]
const LANDMARK_CLIPS: Array[StringName] = [&"ember_1", &"water_1"]


func _run_landmarks() -> void:
	Progress.use_memory_profile(_campaign_profile())
	for stage: StringName in LANDMARK_STAGES:
		Progress.active_stage = stage
		var game := GAME_SCENE.instantiate() as Game
		game.autoplay = true
		add_child(game)
		await _wait(0.2)
		var sim := game.sim
		var art := game.board.art
		_light(art, DayNight.DAY)
		sim.wave_index = 3
		sim.gold = 3000
		sim.tree.points = 10
		await _until(func() -> bool: return sim.state == RunSim.State.WAVE and sim.time_in_wave > 4.0 or sim.is_over())
		await _shot("landmarks_%s" % stage)
		for site in sim.landmarks:
			await _crop("landmark_%s_%s_%d" % [stage, site.kind, site.anchor.x + site.anchor.y * 100], game, site)
		if stage in LANDMARK_CLIPS:
			for site in sim.landmarks:
				await _clip("%s_%s_day" % [stage, site.kind], game, site, 40)
		_light(art, DayNight.NIGHT)
		await _wait(1.0)
		for site in sim.landmarks:
			if site.kind == &"city":
				await _crop("landmark_%s_city_night" % stage, game, site)
		if stage in LANDMARK_CLIPS:
			for site in sim.landmarks:
				await _clip("%s_%s_night" % [stage, site.kind], game, site, 40)
		sim.lives = maxi(1, roundi(sim.starting_lives * 0.55))
		await _wait(1.0)
		for site in sim.landmarks:
			if site.kind == &"city":
				await _crop("landmark_%s_city_burning" % stage, game, site)
				if stage == LANDMARK_CLIPS[0]:
					await _clip("%s_city_burning" % stage, game, site, 40)
		game.free()
		await _wait(0.1)
	print("Screenshots saved to ", _out)
	get_tree().quit()


## Holds the light at a time of day (the campaign profile has reached the Long Night).
func _light(art: BoardArt, time: float) -> void:
	art.light_override = time
	art.day_night.clock = floorf(art.day_night.clock) + time
	art.day_night.set_target(art.day_night.clock)


## The screen around a camp or city, three cells on each side.
func _site_region(game: Game, site: Landmarks.Site) -> Rect2i:
	var map := game.sim.config.map
	var rect := Rect2(map.cell_center(site.anchor), Vector2.ZERO)
	for cell in site.cells:
		rect = rect.expand(map.cell_center(cell))
	rect = game.board.get_global_transform_with_canvas() * rect.grow(map.cell_size * 2.2)
	var screen := Rect2(Vector2.ZERO, get_viewport().get_visible_rect().size)
	return Rect2i(rect.intersection(screen))


func _crop(shot_name: String, game: Game, site: Landmarks.Site) -> void:
	await RenderingServer.frame_post_draw
	var image := get_viewport().get_texture().get_image().get_region(_site_region(game, site))
	var path := _out.path_join(shot_name + ".png")
	print("Saved %s (%s)" % [path, error_string(image.save_png(path))])


func _clip(clip_name: String, game: Game, site: Landmarks.Site, frames: int) -> void:
	var folder := _out.path_join("clips").path_join(clip_name)
	DirAccess.make_dir_recursive_absolute(folder)
	var region := _site_region(game, site)
	for i in frames:
		await _wait(0.08)
		await RenderingServer.frame_post_draw
		get_viewport().get_texture().get_image().get_region(region).save_png(folder.path_join("%03d.png" % i))
	print("Saved clip ", folder)


## A battle zoomed in, with a drawn mouse pointer pushed against the left, bottom, right and top edges.
func _run_edge() -> void:
	Progress.active_stage = &"ember_2"
	var game := GAME_SCENE.instantiate() as Game
	game.autoplay = true
	add_child(game)
	await _wait(0.2)
	game.sim.wave_index = 6
	game.sim.gold = 6000
	game.sim.tree.points = 14
	await _until(func() -> bool: return game.sim.state == RunSim.State.WAVE and game.sim.time_in_wave > 8.0 \
			or game.sim.is_over())
	game.camera.set_view(1.5, game.sim.config.map.size_in_pixels() * 0.5)
	var pointer_layer := CanvasLayer.new()
	pointer_layer.layer = 100
	add_child(pointer_layer)
	var pointer := Polygon2D.new()
	pointer.polygon = PackedVector2Array([Vector2(0, 0), Vector2(0, 34), Vector2(9, 26), Vector2(15, 40),
		Vector2(21, 37), Vector2(15, 24), Vector2(26, 24)])
	pointer.color = Color.WHITE
	var outline := Line2D.new()
	outline.points = pointer.polygon
	outline.closed = true
	outline.width = 2.5
	outline.default_color = Color.BLACK
	pointer.add_child(outline)
	pointer_layer.add_child(pointer)
	var screen := get_viewport().get_visible_rect()
	var middle := BoardCamera.VIEW_CENTER
	var stops: Array[Vector2] = [middle, Vector2(screen.position.x + 1, middle.y), middle,
		Vector2(middle.x, screen.end.y - 2), Vector2(screen.end.x - 2, middle.y), Vector2(middle.x + 300, middle.y),
		Vector2(middle.x - 200, screen.position.y + 1), middle]
	var folder := _out.path_join("edge")
	DirAccess.make_dir_recursive_absolute(folder)
	var frame := 0
	var at := middle
	for index in range(1, stops.size()):
		var target: Vector2 = stops[index]
		# Glide to the next stop, then hold there so the board has time to slide.
		for step in 50:
			at = at.lerp(target, 0.18) if step < 20 else target
			pointer.position = at
			var motion := InputEventMouseMotion.new()
			motion.position = at
			motion.global_position = at
			get_tree().root.push_input(motion, true)
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(folder.path_join("%04d.png" % frame))
			frame += 1
	print("Saved clip ", folder)
	game.free()
	get_tree().quit()


func _wait(seconds: float) -> void:
	await get_tree().create_timer(seconds).timeout


func _until(condition: Callable) -> void:
	var frames := 0
	while not condition.call() and frames < MAX_WAIT_FRAMES:
		await get_tree().process_frame
		frames += 1
	if frames >= MAX_WAIT_FRAMES:
		push_warning("Capture: gave up waiting for a moment")


func _shot(shot_name: String) -> void:
	await RenderingServer.frame_post_draw
	var path := _out.path_join(shot_name + ".png")
	var error := get_viewport().get_texture().get_image().save_png(path)
	print("Saved %s (%s)" % [path, error_string(error)])
