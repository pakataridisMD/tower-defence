class_name PlayerProfile
extends RefCounted
## Everything that lasts between runs, for one playthrough (one New Game): meta points, the meta tree nodes taken, run records and the
## map and difficulty picked last, and the campaign stages won. SaveFile stores it as versioned JSON.

## Bump this when the saved shape changes, and teach migrate() to upgrade older saves.
const VERSION := 4

## Every meta point ever earned. Unspent points are this minus the cost of the nodes taken, so
## changing a node's cost in an update can never leave a save with negative points.
var meta_points_earned := 0
## Which playthrough this is: each New Game gets the next number, and its own name ("Game 2").
## Saves made before playthroughs existed are Game 1.
var playthrough_id := 1
var playthrough_name := "Game 1"
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
## Story cinematics already played, in the order they were seen. Each plays on its own only once;
## the campaign map's Chronicle replays them.
var seen_cinematics: Array[StringName] = []
## Heroes picked for the next run, in key order. Empty brings the most recent heroes to join.
var hero_party: Array[StringName] = []
## Best meta point score reached on each campaign stage (keyed by stage id) and skirmish map (keyed
## by "skirmish:<map id>"), difficulty multiplier included. A run only pays for beating it.
var run_records: Dictionary[StringName, int] = {}
## How many small replay rewards each stage or skirmish map has paid (see MetaProgress.REPLAY_LIMIT).
var replays_paid: Dictionary[StringName, int] = {}
## Set when loading a save from before records existed (version 3 or older). MetaProgress then
## works out its records from the stages won and caps its meta points at what they are worth.
var needs_records := false


func to_dict() -> Dictionary:
	var nodes: Array[String] = []
	for id in meta_nodes:
		nodes.append(String(id))
	var seen: Array[String] = []
	for id in seen_cinematics:
		seen.append(String(id))
	var party: Array[String] = []
	for id in hero_party:
		party.append(String(id))
	var stars := {}
	for id in stage_stars:
		stars[String(id)] = stage_stars[id]
	return {
		"version": VERSION,
		"playthrough": {"id": playthrough_id, "name": playthrough_name},
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
		"story": {"seen": seen},
		"heroes": {"party": party},
		"records": {"best": _string_keys(run_records), "replays": _string_keys(replays_paid)},
	}


static func _string_keys(source: Dictionary) -> Dictionary:
	var result := {}
	for id in source:
		result[String(id)] = source[id]
	return result


static func _read_counts(source: Variant, into: Dictionary[StringName, int]) -> void:
	if not source is Dictionary:
		return
	for id: Variant in source:
		if id is String and not (id as String).is_empty():
			var count := maxi(0, _read_int(source, id))
			if count > 0:
				into[StringName(id)] = count


## Builds a profile from saved data. Missing or malformed fields fall back to their defaults, so a
## hand-edited or partly damaged save still loads.
static func from_dict(saved: Dictionary) -> PlayerProfile:
	var data := migrate(saved)
	var profile := PlayerProfile.new()
	var playthrough: Variant = data.get("playthrough", {})
	if playthrough is Dictionary:
		profile.playthrough_id = maxi(1, _read_int(playthrough, "id"))
		var name := _read_string(playthrough, "name")
		profile.playthrough_name = name if not name.is_empty() else "Game %d" % profile.playthrough_id
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
	var story: Variant = data.get("story", {})
	if story is Dictionary:
		var seen: Variant = (story as Dictionary).get("seen", [])
		if seen is Array:
			for id: Variant in seen:
				if id is String and not (id as String).is_empty() and not profile.seen_cinematics.has(StringName(id)):
					profile.seen_cinematics.append(StringName(id))
	var heroes: Variant = data.get("heroes", {})
	if heroes is Dictionary:
		var party: Variant = (heroes as Dictionary).get("party", [])
		if party is Array:
			for id: Variant in party:
				if id is String and not (id as String).is_empty() and not profile.hero_party.has(StringName(id)):
					profile.hero_party.append(StringName(id))
	var records: Variant = data.get("records", {})
	if records is Dictionary:
		_read_counts((records as Dictionary).get("best", {}), profile.run_records)
		_read_counts((records as Dictionary).get("replays", {}), profile.replays_paid)
	profile.needs_records = data.get("needs_records", false) == true
	return profile


## Upgrades data saved by an older version of the game to the current shape.
static func migrate(saved: Dictionary) -> Dictionary:
	var data := saved.duplicate(true)
	var version: Variant = data.get("version", 1)
	if not (version is int or version is float) or int(version) < 2:
		# Version 2 added the campaign. Older saves have played none of it.
		data["campaign"] = {"stars": {}}
	if not (version is int or version is float) or int(version) < 3:
		# Version 3 added the story. Older saves have seen none of it.
		data["story"] = {"seen": []}
	if not (version is int or version is float) or int(version) < 4:
		# Version 4 pays meta points only for new records. Older saves could replay a stage for points
		# without end, so their records are rebuilt from the stages won (see MetaProgress).
		data["records"] = {"best": {}, "replays": {}}
		data["needs_records"] = true
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
