class_name PlayerProfile
extends RefCounted
## Everything that lasts between runs: meta points, the meta tree nodes taken, run records and the
## map and difficulty picked last, and the campaign stages won. SaveFile stores it as versioned JSON.

## Bump this when the saved shape changes, and teach migrate() to upgrade older saves.
const VERSION := 2

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
## Best stars (1 to 3) for each campaign stage won. A stage that is missing has not been won.
var stage_stars: Dictionary[StringName, int] = {}


func to_dict() -> Dictionary:
	var nodes: Array[String] = []
	for id in meta_nodes:
		nodes.append(String(id))
	var stars := {}
	for id in stage_stars:
		stars[String(id)] = stage_stars[id]
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
		"campaign": {"stars": stars},
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
	var campaign: Variant = data.get("campaign", {})
	if campaign is Dictionary:
		var stars: Variant = (campaign as Dictionary).get("stars", {})
		if stars is Dictionary:
			for id: Variant in stars:
				var count := clampi(_read_int(stars, id), 0, 3) if id is String else 0
				if count > 0 and not (id as String).is_empty():
					profile.stage_stars[StringName(id)] = count
	return profile


## Upgrades data saved by an older version of the game to the current shape.
static func migrate(saved: Dictionary) -> Dictionary:
	var data := saved.duplicate(true)
	var version: Variant = data.get("version", 1)
	if not (version is int or version is float) or int(version) < 2:
		# Version 2 added the campaign. Older saves have played none of it.
		data["campaign"] = {"stars": {}}
	data["version"] = VERSION
	return data


static func _read_int(data: Dictionary, key: String) -> int:
	var value: Variant = data.get(key, 0)
	if value is int or value is float:
		return int(value)
	return 0


static func _read_string(data: Dictionary, key: String) -> String:
	var value: Variant = data.get(key, "")
	return value if value is String else ""
