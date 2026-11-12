class_name SaveSlots
extends RefCounted
## The ten save slots the player saves into and loads from, by hand, from the main menu or the Esc
## menu. Each slot is one JSON file (slot_01.json to slot_10.json) holding:
##   "info"     what the slot list shows: when, where, which wave, gold, lives, stars.
##   "profile"  the whole PlayerProfile at that moment: campaign stars, talents, heroes, records.
##   "run"      the run being played, as a RunSnapshot, or null for a save made outside a run.
## The everyday save (Progress, user://save.json) is separate and keeps saving itself; a slot is a
## copy the player can go back to.
##
## Slots are written like the main save: to a temporary file first, then moved into place. With no
## folder (tests, bot runs) they are kept in memory only.

const COUNT := 10
const VERSION := 1
const MONTHS: Array[String] = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

## Where the slot files go, or empty to keep slots in memory.
var folder := ""
var _memory: Dictionary[int, Dictionary] = {}


func _init(p_folder: String = "") -> void:
	folder = p_folder


func path(slot: int) -> String:
	return folder.path_join("slot_%02d.json" % slot)


static func is_valid_slot(slot: int) -> bool:
	return slot >= 1 and slot <= COUNT


func has(slot: int) -> bool:
	return not read(slot).is_empty()


## Everything stored in a slot, or an empty dictionary for an empty or unreadable slot.
func read(slot: int) -> Dictionary:
	if not is_valid_slot(slot):
		return {}
	if folder.is_empty():
		return _memory.get(slot, {}).duplicate(true)
	if not FileAccess.file_exists(path(slot)):
		return {}
	var data: Variant = SaveFile._read_json(path(slot))
	if data is Dictionary and (data as Dictionary).get("profile") is Dictionary:
		return data
	return {}


## The info part of a slot (see the class notes), or empty.
func info(slot: int) -> Dictionary:
	var info_data: Variant = read(slot).get("info", {})
	return info_data if info_data is Dictionary else {}


func write(slot: int, data: Dictionary) -> Error:
	if not is_valid_slot(slot):
		return ERR_INVALID_PARAMETER
	if folder.is_empty():
		_memory[slot] = data.duplicate(true)
		return OK
	DirAccess.make_dir_recursive_absolute(folder)
	var temp := path(slot) + ".tmp"
	var file := FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(data, "\t"))
	file.close()
	if FileAccess.file_exists(path(slot)):
		DirAccess.remove_absolute(path(slot))
	return DirAccess.rename_absolute(temp, path(slot))


func erase(slot: int) -> void:
	if not is_valid_slot(slot):
		return
	if folder.is_empty():
		_memory.erase(slot)
	elif FileAccess.file_exists(path(slot)):
		DirAccess.remove_absolute(path(slot))


## The slot saved most recently, or 0 when every slot is empty.
func latest() -> int:
	var best := 0
	var best_time := -1
	for slot in range(1, COUNT + 1):
		var when := int(info(slot).get("saved_at", -1))
		if has(slot) and when > best_time:
			best = slot
			best_time = when
	return best


## A slot's contents: the info line, the profile and the run (or null).
static func make(info_data: Dictionary, profile: PlayerProfile, run: Dictionary) -> Dictionary:
	return {
		"version": VERSION,
		"info": info_data,
		"profile": profile.to_dict(),
		"run": run if not run.is_empty() else null,
	}


## When a slot was saved, in the player's own time: "12 Nov 2026  17:42".
static func date_text(unix_seconds: int) -> String:
	if unix_seconds <= 0:
		return ""
	var zone := Time.get_time_zone_from_system()
	var local := unix_seconds + int(zone.get("bias", 0)) * 60
	var d := Time.get_datetime_dict_from_unix_time(local)
	return "%d %s %d  %02d:%02d" % [d["day"], MONTHS[clampi(d["month"] - 1, 0, 11)], d["year"], d["hour"], d["minute"]]
