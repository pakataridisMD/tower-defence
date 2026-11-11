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
## Add --story to take the cinematic player, a Herald's boss banner, the assault on the citadel and
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
		elif arg == "--story":
			_story = true
		elif arg == "--heroes":
			_heroes = true
		elif arg == "--menu":
			_menu = true
		elif arg == "--map":
			_map = true
	DirAccess.make_dir_recursive_absolute(_out)
	Progress.use_memory_profile(_demo_profile())
	# The map's glide down from the whole world would still be moving in the first shots.
	CampaignScreen.intro_played = true
	if _menu:
		_run_menu()
	elif _map:
		_run_map()
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

	# The assault: the opening, then the second movement once the gate has fallen.
	Progress.active_stage = &"assault_1"
	var assault := GAME_SCENE.instantiate() as Game
	assault.autoplay = true
	add_child(assault)
	await _until(func() -> bool: return assault.sim.wave_number() >= 4 and assault.sim.time_in_wave > 8.0 \
			or assault.sim.is_over())
	await _shot("story_assault_gate")
	Engine.time_scale = 8.0
	await _until(func() -> bool: return assault.sim.structure_phase >= 2 or assault.sim.is_over())
	Engine.time_scale = 1.0
	await _wait(3.0)
	await _shot("story_assault_heralds")
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


## A player a few runs in: some meta points spent, one map unlocked, a few left to spend.
static func _demo_profile() -> PlayerProfile:
	var profile := PlayerProfile.new()
	profile.meta_points_earned = 17
	profile.meta_nodes = [&"command_gold", &"command_lives", &"mastery_range", &"expedition_serpentine"]
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


func _hover(at: Vector2) -> void:
	var motion := InputEventMouseMotion.new()
	motion.position = at
	motion.global_position = at
	Input.parse_input_event(motion)


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
