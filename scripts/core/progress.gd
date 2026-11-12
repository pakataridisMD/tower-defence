extends Node
## The player's lasting progress: loaded at start-up and saved after every change. Registered as
## the Progress autoload. The rules live in MetaProgress; this node adds the save file.
##
## Command line options, given after `--`:
##   --save-path=<path>  read and write the save there instead of user://save.json.
## With --autoplay and no --save-path, progress stays in memory, so a bot never touches a real save.
## The same goes for test runs, from the command line or from the editor's GUT panel.

signal changed

const DEFAULT_SAVE_PATH := "user://save.json"

var save_path := DEFAULT_SAVE_PATH
## False keeps progress in memory only.
var persist := true
var meta: MetaProgress
## The campaign stage the next run plays, or empty for a skirmish on the selected map. Not saved.
var active_stage: StringName = &""
## Cinematics waiting to play, and the scene to open once they are done. Set by play_story().
var cinematic_queue: Array[StringName] = []
var cinematic_next_scene := ""

const CINEMATIC_SCENE := "res://scenes/story/cinematic.tscn"


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	var chosen_path := false
	for arg in args:
		if arg.begins_with("--save-path="):
			save_path = arg.trim_prefix("--save-path=")
			chosen_path = true
	if (args.has("--autoplay") or _running_tests()) and not chosen_path:
		persist = false
	load_profile()


func load_profile() -> void:
	var profile := SaveFile.load_profile(save_path) if persist else PlayerProfile.new()
	meta = MetaProgress.new(DataRegistry, profile)
	changed.emit()


## Starts over with a profile kept in memory only. Tests call this so they never read or write
## a real save.
func use_memory_profile(profile: PlayerProfile = null) -> void:
	persist = false
	active_stage = &""
	meta = MetaProgress.new(DataRegistry, profile if profile != null else PlayerProfile.new())
	changed.emit()


func save() -> void:
	if not persist:
		return
	var error := SaveFile.save_profile(meta.profile, save_path)
	if error != OK:
		push_error("Could not save progress to %s: %s" % [save_path, error_string(error)])


func allocate_meta(id: StringName) -> bool:
	return _saved(meta.allocate(id))


func refund_meta(id: StringName) -> bool:
	return _saved(meta.refund(id))


func reset_meta() -> void:
	meta.reset()
	_saved(true)


func select_map(id: StringName) -> bool:
	return _saved(meta.select_map(id))


func select_difficulty(id: StringName) -> bool:
	return _saved(meta.select_difficulty(id))


## Makes the next skirmish endless or not, and saves.
func set_endless(on: bool) -> void:
	meta.set_endless(on)
	_saved(true)


## Makes the next run a campaign stage. Returns false if the stage is still locked.
func play_stage(id: StringName) -> bool:
	if not meta.is_stage_unlocked(id):
		return false
	active_stage = id
	return true


## Makes the next run a skirmish on the selected map.
func play_skirmish() -> void:
	active_stage = &""


## The next run's config, with the hero party.
func run_config() -> RunConfig:
	if not active_stage.is_empty():
		var config := meta.stage_config(active_stage)
		if config != null:
			return meta.add_heroes(config)
	return meta.add_heroes(meta.run_config())


## Adds a hero to the party or takes them out, and saves.
func toggle_party_hero(hero_id: StringName) -> bool:
	return _saved(meta.toggle_party_hero(hero_id))


## Pays a finished run's meta points, updates the records and saves. Returns the points earned.
func record_run(sim: RunSim) -> int:
	var earned := meta.record_run(sim)
	_saved(true)
	return earned


## Records a finished campaign stage (after record_run) and saves. See MetaProgress.record_stage.
func record_stage(sim: RunSim) -> Dictionary:
	var result := meta.record_stage(sim)
	_saved(true)
	return result


## Marks a cinematic as seen and saves.
func mark_seen(cinematic_id: StringName) -> bool:
	return _saved(meta.mark_seen(cinematic_id))


## Opens a scene, first playing these cinematics if there are any. Use it for every scene change
## the story can sit in front of.
func play_story(tree: SceneTree, cinematics: Array[StringName], next_scene: String) -> void:
	if cinematics.is_empty():
		tree.change_scene_to_file(next_scene)
		return
	cinematic_queue = cinematics.duplicate()
	cinematic_next_scene = next_scene
	tree.change_scene_to_file(CINEMATIC_SCENE)


## True when GUT runs the tests: its runner scene or script is on the command line.
static func _running_tests() -> bool:
	for arg in OS.get_cmdline_args():
		if arg.contains("addons/gut/"):
			return true
	return false


func _saved(did_change: bool) -> bool:
	if did_change:
		save()
		changed.emit()
	return did_change
