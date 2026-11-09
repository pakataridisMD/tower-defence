extends Node
## Saves screenshots of the main menu, the meta tree, the skill web, a battle and the end screen
## while the AutoPlayer plays a run. It needs a real window, so run it on a desktop or under xvfb-run:
##   godot --path . --resolution 1920x1080 --fixed-fps 30 res://tools/capture.tscn -- --out=<folder>
## It plays with a made-up profile kept in memory, so it never touches a real save.
## Add --quick after `--` to skip the run and only take the menu, the meta tree and the skill web.
## Add --campaign to take the campaign map and a battle in each biome instead (each battle jumps
## straight to a late wave with plenty of gold, so the board is busy).

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


func _ready() -> void:
	_out = OS.get_user_data_dir().path_join("shots")
	for arg in OS.get_cmdline_user_args():
		if arg.begins_with("--out="):
			_out = arg.trim_prefix("--out=")
		elif arg == "--quick":
			_quick = true
		elif arg == "--campaign":
			_campaign = true
	DirAccess.make_dir_recursive_absolute(_out)
	Progress.use_memory_profile(_demo_profile())
	if _campaign:
		_run_campaign()
	else:
		_run()


## Ember Reach and the Thunder Steppe done, two more under way.
static func _campaign_profile() -> PlayerProfile:
	var profile := _demo_profile()
	for pair: Array in [[&"ember_1", 3], [&"ember_2", 3], [&"ember_3", 2], [&"ember_4", 1], [&"storm_1", 3],
			[&"storm_2", 2], [&"storm_3", 2], [&"storm_4", 2], [&"nature_1", 3], [&"nature_2", 1], [&"void_1", 2],
			[&"water_1", 3], [&"earth_1", 1]]:
		profile.stage_stars[pair[0]] = pair[1]
	return profile


func _run_campaign() -> void:
	Progress.use_memory_profile(_campaign_profile())
	var screen := CAMPAIGN_SCENE.instantiate() as CampaignScreen
	add_child(screen)
	await _wait(0.4)
	screen.select(&"nature_3")
	_hover(screen.stage_position(&"storm_4"))
	await _wait(0.4)
	await _shot("campaign_map")
	screen.select(&"converge_3")
	await _wait(0.3)
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
