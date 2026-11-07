class_name PlayerProfile
extends RefCounted
## Everything that lasts between runs: meta points, the meta tree nodes taken, run records and the
## map and difficulty picked last. SaveFile stores it as versioned JSON.

## Bump this when the saved shape changes, and teach migrate() to upgrade older saves.
const VERSION := 1

## Every meta point ever earned. Unspent points are this minus the cost of the nodes taken, so
## changing a node's cost in an update can never leave a save with negative points.
var meta_points_earned := 0
## Meta tree nodes taken, not counting the start, in the order they were taken.
var meta_nodes: Array[StringName] = []
var runs_played := 0
var runs_won := 0
## Most waves cleared in a single run.
var best_waves := 0
var enemies_killed := 0
var last_map: StringName = &""
var last_difficulty: StringName = &""


func to_dict() -> Dictionary:
	var nodes: Array[String] = []
	for id in meta_nodes:
		nodes.append(String(id))
	return {
		"version": VERSION,
		"meta_points_earned": meta_points_earned,
		"meta_nodes": nodes,
		"stats": {
			"runs_played": runs_played,
			"runs_won": runs_won,
			"best_waves": best_waves,
			"enemies_killed": enemies_killed,
		},
		"last_map": String(last_map),
		"last_difficulty": String(last_difficulty),
	}


## Builds a profile from saved data. Missing or malformed fields fall back to their defaults, so a
## hand-edited or partly damaged save still loads.
static func from_dict(saved: Dictionary) -> PlayerProfile:
	var data := migrate(saved)
	var profile := PlayerProfile.new()
	profile.meta_points_earned = maxi(0, _read_int(data, "meta_points_earned"))
	var nodes: Variant = data.get("meta_nodes", [])
	if nodes is Array:
		for id: Variant in nodes:
			if id is String and not (id as String).is_empty():
				profile.meta_nodes.append(StringName(id))
	var stats: Variant = data.get("stats", {})
	if stats is Dictionary:
		profile.runs_played = maxi(0, _read_int(stats, "runs_played"))
		profile.runs_won = maxi(0, _read_int(stats, "runs_won"))
		profile.best_waves = maxi(0, _read_int(stats, "best_waves"))
		profile.enemies_killed = maxi(0, _read_int(stats, "enemies_killed"))
	profile.last_map = StringName(_read_string(data, "last_map"))
	profile.last_difficulty = StringName(_read_string(data, "last_difficulty"))
	return profile


## Upgrades data saved by an older version of the game to the current shape.
static func migrate(saved: Dictionary) -> Dictionary:
	# Version 1 is the first saved shape, so there is nothing to upgrade yet. A future version 2
	# would check saved.get("version", 1) here and rename or convert the fields that changed.
	return saved


static func _read_int(data: Dictionary, key: String) -> int:
	var value: Variant = data.get(key, 0)
	if value is int or value is float:
		return int(value)
	return 0


static func _read_string(data: Dictionary, key: String) -> String:
	var value: Variant = data.get(key, "")
	return value if value is String else ""
