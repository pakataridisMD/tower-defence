class_name SaveSlots
extends RefCounted
## The saved games: ten slots the player saves into by hand from the Esc menu, and one autosave for
## each playthrough (each New Game is a playthrough of its own, see PlayerProfile.playthrough_id),
## which the game keeps up to date by itself. Each is one JSON file (slot_01.json to slot_10.json,
## auto_01.json, auto_02.json and so on) holding:
##   "info"     what the list shows: when, which game, where, which wave, gold, lives, stars.
##   "profile"  the whole PlayerProfile at that moment: campaign stars, talents, heroes, records.
##   "run"      the run being played, as a RunSnapshot, or null outside a run.
## The everyday save (Progress, user://save.json) holds the playthrough being played; the saves are
## copies the player can go back to.
##
## Saves are written like the main save: to a temporary file first, then moved into place. With no
## folder (tests, bot runs) they are kept in memory only.

const COUNT := 10
const VERSION := 1
const MONTHS: Array[String] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

## Where the save files go, or empty to keep them in memory.
var folder := ""
var _memory: Dictionary[String, Dictionary] = {}


func _init(p_folder: String = "") -> void:
	folder = p_folder


static func is_valid_slot(slot: int) -> bool:
	return slot >= 1 and slot <= COUNT


## The name a manual slot is kept under.
static func slot_key(slot: int) -> String:
	return "slot_%02d" % slot


## The name a playthrough's autosave is kept under.
static func auto_key(playthrough: int) -> String:
	return "auto_%02d" % playthrough


func path(key: String) -> String:
	return folder.path_join(key + ".json")


# --- Manual slots ------------------------------------------------------------------

func has(slot: int) -> bool:
	return is_valid_slot(slot) and has_key(slot_key(slot))


## Everything stored in a slot, or an empty dictionary for an empty or unreadable slot.
func read(slot: int) -> Dictionary:
	return read_key(slot_key(slot)) if is_valid_slot(slot) else {}


## The info part of a slot (see the class notes), or empty.
func info(slot: int) -> Dictionary:
	return info_key(slot_key(slot)) if is_valid_slot(slot) else {}


func write(slot: int, data: Dictionary) -> Error:
	if not is_valid_slot(slot):
		return ERR_INVALID_PARAMETER
	return write_key(slot_key(slot), data)


func erase(slot: int) -> void:
	if is_valid_slot(slot):
		erase_key(slot_key(slot))


# --- Autosaves -------------------------------------------------------------------

## The playthroughs that have an autosave, the most recently saved first.
func autosave_ids() -> Array[int]:
	var ids: Array[int] = []
	for key in _keys():
		if key.begins_with("auto_") and key.trim_prefix("auto_").is_valid_int():
			ids.append(key.trim_prefix("auto_").to_int())
	ids.sort_custom(func(a: int, b: int) -> bool:
		return order(info_key(auto_key(a))) > order(info_key(auto_key(b))))
	return ids


## Every playthrough id found in any save, for numbering a new one.
func playthrough_ids() -> Array[int]:
	var ids: Array[int] = []
	for key in _keys():
		var id := int(info_key(key).get("game_id", 0))
		if id > 0 and not ids.has(id):
			ids.append(id)
	return ids


# --- By key ----------------------------------------------------------------------

func has_key(key: String) -> bool:
	return not read_key(key).is_empty()


func read_key(key: String) -> Dictionary:
	if folder.is_empty():
		return _memory.get(key, {}).duplicate(true)
	if not FileAccess.file_exists(path(key)):
		return {}
	var data: Variant = SaveFile._read_json(path(key))
	if data is Dictionary and (data as Dictionary).get("profile") is Dictionary:
		return data
	return {}


func info_key(key: String) -> Dictionary:
	var info_data: Variant = read_key(key).get("info", {})
	return info_data if info_data is Dictionary else {}


func write_key(key: String, data: Dictionary) -> Error:
	if folder.is_empty():
		_memory[key] = data.duplicate(true)
		return OK
	DirAccess.make_dir_recursive_absolute(folder)
	var temp := path(key) + ".tmp"
	var file := FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(data, "\t"))
	file.close()
	if FileAccess.file_exists(path(key)):
		DirAccess.remove_absolute(path(key))
	return DirAccess.rename_absolute(temp, path(key))


func erase_key(key: String) -> void:
	if folder.is_empty():
		_memory.erase(key)
	elif FileAccess.file_exists(path(key)):
		DirAccess.remove_absolute(path(key))


func _keys() -> Array[String]:
	var keys: Array[String] = []
	if folder.is_empty():
		keys.assign(_memory.keys())
		return keys
	for file in DirAccess.get_files_at(folder):
		if file.ends_with(".json"):
			keys.append(file.trim_suffix(".json"))
	return keys


## The save written most recently, by key, or empty when there is none.
func latest_key() -> String:
	var best := ""
	var best_time := -1
	for key in _keys():
		var when := order(info_key(key))
		if when > best_time:
			best = key
			best_time = when
	return best


## Milliseconds since 1970 when a save was made, for putting saves in order.
static func order(info_data: Dictionary) -> int:
	if info_data.has("saved_ms"):
		return int(info_data["saved_ms"])
	return int(info_data.get("saved_at", 0)) * 1000


## A save's contents: the info line, the profile and the run (or null).
static func make(info_data: Dictionary, profile: PlayerProfile, run: Dictionary) -> Dictionary:
	return {
		"version": VERSION,
		"info": info_data,
		"profile": profile.to_dict(),
		"run": run if not run.is_empty() else null,
	}


## When a save was made, in the player's own time: "12 Nov 2026  17:42".
static func date_text(unix_seconds: int) -> String:
	if unix_seconds <= 0:
		return ""
	var zone := Time.get_time_zone_from_system()
	var local := unix_seconds + int(zone.get("bias", 0)) * 60
	var d := Time.get_datetime_dict_from_unix_time(local)
	return "%d %s %d  %02d:%02d" % [d["day"], MONTHS[clampi(d["month"] - 1, 0, 11)], d["year"], d["hour"], d["minute"]]
