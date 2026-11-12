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
## The ten save slots (see SaveSlots). Kept in memory when progress is.
var slots := SaveSlots.new()
## A run loaded from a slot, waiting for the game scene to put it back (see RunSnapshot). Not saved.
var pending_run: Dictionary = {}

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
	slots = SaveSlots.new(save_path.get_base_dir().path_join("slots") if persist else "")
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
	pending_run = {}
	slots = SaveSlots.new()
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


# --- Save slots ------------------------------------------------------------------

## Saves everything into a slot: the profile as it is now and, during a run, the run (a RunSnapshot,
## see Game.run_snapshot). Overwrites what was there.
func save_to_slot(slot: int, run: Dictionary = {}) -> Error:
	var error := slots.write(slot, SaveSlots.make(slot_info(run), meta.profile, run))
	if error != OK:
		push_error("Could not save slot %d: %s" % [slot, error_string(error)])
	return error


## Loads a slot: its profile replaces the current one (and is saved as the everyday save), and its
## run, if it has one, waits in pending_run for the game scene. Returns true if the slot held a run,
## so the caller opens the game; false means open a menu. Returns false and changes nothing for an
## empty slot (check has_slot first).
func load_from_slot(slot: int) -> bool:
	var data := slots.read(slot)
	if data.is_empty():
		return false
	meta = MetaProgress.new(DataRegistry, PlayerProfile.from_dict(data["profile"]))
	active_stage = &""
	pending_run = {}
	var run: Variant = data.get("run")
	if run is Dictionary and (run as Dictionary).has("wave_index"):
		var stage := StringName(str(run.get("stage", "")))
		if not stage.is_empty() and DataRegistry.stages.has(stage):
			active_stage = stage
		var map := StringName(str(run.get("map", "")))
		if stage.is_empty() and DataRegistry.maps.has(map):
			meta.selected_map = map
		var difficulty := StringName(str(run.get("difficulty", "")))
		if DataRegistry.difficulties.has(difficulty) or difficulty.is_empty():
			meta.selected_difficulty = difficulty
		meta.endless = run.get("endless", false) == true
		if not stage.is_empty() and active_stage.is_empty():
			push_warning("Slot %d's stage %s no longer exists; loading its progress only." % [slot, stage])
		else:
			pending_run = run
	save()
	changed.emit()
	return not pending_run.is_empty()


func has_slot(slot: int) -> bool:
	return slots.has(slot)


func delete_slot(slot: int) -> void:
	slots.erase(slot)


## What the slot list shows for a save made now: when, where, the wave and the campaign's stars.
func slot_info(run: Dictionary = {}) -> Dictionary:
	var earned := 0
	var total := 0
	for campaign in meta.campaigns_in_order():
		earned += meta.campaign_stars(campaign)
		total += campaign.stages.size() * 3
	var info := {
		"saved_at": int(Time.get_unix_time_from_system()),
		"kind": "progress",
		"stars": earned,
		"stars_total": total,
		"stages_won": meta.stages_won(),
		"heroes": meta.joined_heroes().size(),
	}
	if run.is_empty():
		info["title"] = "Campaign progress"
		info["where"] = "Saved from the menu"
		return info
	info["kind"] = "run"
	info["wave"] = RunSnapshot.wave_number(run)
	info["gold"] = int(run.get("gold", 0))
	info["lives"] = int(run.get("lives", 0))
	var difficulty: DifficultyData = DataRegistry.difficulties.get(StringName(str(run.get("difficulty", ""))))
	info["difficulty"] = difficulty.display_name if difficulty != null else ""
	var stage: StageData = DataRegistry.stages.get(StringName(str(run.get("stage", ""))))
	var wave_set_id: StringName = &""
	if stage != null:
		info["title"] = stage.display_name
		var campaign: CampaignData = DataRegistry.campaign_of(stage.id)
		info["where"] = "%s, stage %d" % [campaign.display_name, campaign.stage_index(stage.id) + 1] if campaign != null \
				else "Campaign"
		wave_set_id = stage.wave_set
		if wave_set_id.is_empty() and DataRegistry.maps.has(stage.map):
			wave_set_id = DataRegistry.maps[stage.map].wave_set
		info["assault"] = not stage.structures.is_empty()
	else:
		var map: MapData = DataRegistry.maps.get(StringName(str(run.get("map", ""))))
		info["title"] = map.display_name if map != null else "Skirmish"
		info["where"] = "Skirmish"
		if run.get("endless", false) == true:
			info["where"] = "Endless skirmish"
			info["endless"] = true
		if map != null:
			wave_set_id = map.wave_set
	var wave_set: WaveSet = DataRegistry.wave_sets.get(wave_set_id)
	info["waves"] = wave_set.waves.size() if wave_set != null else 0
	return info


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
