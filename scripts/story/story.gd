class_name Story
extends RefCounted
## The campaign's story, read from plain JSON in data/story/ so writers can fill it in without Godot:
##
##   story.json             which cinematic plays when, and the city lost after each stage
##   characters.json        the heroes and villains, and which boss enemy each villain is
##   cinematics/<id>.json   one cinematic: a title and its shots, each with narration and an art note
##
## Pictures and narration are found by name: assets/story/images/<cinematic>/<NN>.png and
## assets/story/voice/<cinematic>/<NN>.ogg, where NN counts the shots from 01. Anything missing is
## replaced by a placeholder, so the story can be written before its art and voice exist.
## See data/story/README.md.

const STORY_DIR := "res://data/story"
const IMAGE_PATH := "res://assets/story/images/%s/%02d.png"
const VOICE_PATH := "res://assets/story/voice/%s/%02d.ogg"
const PORTRAIT_PATH := "res://assets/story/portraits/%s.png"
const MUSIC_PATH := "res://assets/story/music/%s.ogg"
## A finished, pre-rendered film of a whole cinematic (picture, voice and music mixed in). When one
## exists it plays instead of the stills. Its <id>.json may list when each shot starts, in seconds,
## as {"shots": [0.0, 6.2, ...]}, so the player can show the subtitles over it.
const VIDEO_PATH := "res://assets/story/video/%s.ogv"
## The music thread's map of which cue plays under each cinematic: {"cinematics": {id: cue}}.
const MUSIC_MAP := "res://assets/story/music/cinematic_music.json"
## Words a narrator reads per second, to time a shot that has no voice line yet.
const WORDS_PER_SECOND := 2.4

## Music cue for each cinematic id, from MUSIC_MAP. A cinematic's own "music" field wins.
var music_cues: Dictionary = {}

## Cinematic id that opens the campaign.
var prologue: StringName = &""
## Plot beats that play once enough stages are won, in any order: {cinematic, after_stages_won}.
## "after_stage" and "before_stage" (a stage id) also work here.
var beats: Array[Dictionary] = []
## Scenes tied to one stage, by stage id: {before, after, lost, during: [{wave, cinematic}]}.
var stage_scenes: Dictionary = {}
## From this many stages won, the element lands are fought at night (the Long Night). 0 never.
var night_from_stages_won := 0
## The named boss of a stage, by stage id (a character id).
var stage_bosses: Dictionary = {}
## The final assault: {intro, outro, post_credits, movements: [{name, minutes, boss, cinematic}]}.
var assault: Dictionary = {}
## The city each stage defends, by stage id: {name, fall_text, capital}.
var cities: Dictionary = {}
## Characters by id.
var characters: Dictionary = {}
## Where the cinematics' films are looked for (tests point it elsewhere).
var video_path := VIDEO_PATH
## Cinematics by id, each {id, title, music, shots: [{text, speaker, art_note, image, voice, duration}]}.
var cinematics: Dictionary = {}
## Problems found while reading the files, as readable lines.
var errors: PackedStringArray = []

static var _shared: Story


## The story read from data/story, loaded once.
static func shared() -> Story:
	if _shared == null:
		_shared = Story.load_from(STORY_DIR)
	return _shared


static func load_from(dir: String) -> Story:
	var story := Story.new()
	var main: Variant = story._read_json(dir.path_join("story.json"))
	if main is Dictionary:
		story.prologue = StringName(str(main.get("prologue", "")))
		for beat: Variant in main.get("beats", []):
			if beat is Dictionary and beat.has("cinematic"):
				story.beats.append(beat)
		var cities: Variant = main.get("cities", {})
		if cities is Dictionary:
			story.cities = cities
		var scenes: Variant = main.get("stage_scenes", {})
		if scenes is Dictionary:
			story.stage_scenes = scenes
		var bosses: Variant = main.get("stage_bosses", {})
		if bosses is Dictionary:
			story.stage_bosses = bosses
		var assault: Variant = main.get("assault", {})
		if assault is Dictionary:
			story.assault = assault
		story.night_from_stages_won = int(main.get("night_from_stages_won", 0))
	var people: Variant = story._read_json(dir.path_join("characters.json"))
	if people is Array:
		for person: Variant in people:
			if person is Dictionary and person.has("id"):
				story.characters[StringName(str(person["id"]))] = person
	if FileAccess.file_exists(MUSIC_MAP):
		var cue_map: Variant = story._read_json(MUSIC_MAP)
		if cue_map is Dictionary and cue_map.get("cinematics") is Dictionary:
			story.music_cues = cue_map["cinematics"]
	var folder := dir.path_join("cinematics")
	for file in ResourceLoader.list_directory(folder):
		if file.ends_with(".json"):
			story._add_cinematic(file.get_basename(), story._read_json(folder.path_join(file)))
	for id in story.all_triggered_cinematics():
		if not story.cinematics.has(id):
			story.errors.append("story.json: plays unknown cinematic '%s'" % id)
	if not story.prologue.is_empty() and not story.cinematics.has(story.prologue):
		story.errors.append("story.json: unknown prologue '%s'" % story.prologue)
	return story


func _read_json(path: String) -> Variant:
	if not FileAccess.file_exists(path):
		return null
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if parsed == null:
		errors.append("%s is not valid JSON" % path)
	return parsed


## Reads one cinematic. Shots may be under "shots", "lines" or "beats", or be the whole file.
func _add_cinematic(file_id: String, data: Variant) -> void:
	var shots: Variant = data
	var info: Dictionary = {}
	if data is Dictionary:
		info = data
		shots = data.get("shots", data.get("lines", data.get("beats", [])))
	if not shots is Array:
		errors.append("cinematics/%s.json has no shots" % file_id)
		return
	var id := StringName(str(info.get("id", file_id)))
	var list: Array[Dictionary] = []
	for i in (shots as Array).size():
		var shot: Variant = shots[i]
		if not shot is Dictionary:
			continue
		var text := str(shot.get("text", ""))
		var image := str(shot.get("image", ""))
		if image.is_empty():
			image = IMAGE_PATH % [id, i + 1]
		var voice: Variant = shot.get("voice", "")
		voice = VOICE_PATH % [id, i + 1] if voice is not String or (voice as String).is_empty() else voice
		if shot.get("voice", true) is bool and shot.get("voice", true) == false:
			voice = ""
		var words := text.split(" ", false).size()
		list.append({
			"text": text,
			"speaker": str(shot.get("speaker", "")),
			"art_note": str(shot.get("art_note", "")),
			"image": image,
			"voice": voice,
			"duration": float(shot.get("duration", maxf(4.0, words / WORDS_PER_SECOND + 1.5))),
			"tint": str(shot.get("tint", "")),
			"motion": str(shot.get("motion", "")),
		})
	cinematics[id] = {
		"id": id,
		"title": str(info.get("title", "")),
		"subtitle": str(info.get("subtitle", "")),
		"music": str(info.get("music", "")),
		"shots": list,
	}


func cinematic(id: StringName) -> Dictionary:
	return cinematics.get(id, {})


func has_cinematic(id: StringName) -> bool:
	return cinematics.has(id)


## The music file for a cinematic, or "" when it has none or the file is not there yet.
func video_for(id: StringName) -> String:
	var path := video_path % id
	return path if ResourceLoader.exists(path) else ""


## When each shot starts in the cinematic's film, from the film's sidecar <id>.json; empty without one
## (the film then carries its own subtitles, if any).
func video_shot_times(id: StringName) -> PackedFloat32Array:
	var times := PackedFloat32Array()
	var path := (video_path % id).get_basename() + ".json"
	if not FileAccess.file_exists(path):
		return times
	var data: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	if data is Dictionary and (data as Dictionary).get("shots") is Array:
		for t: Variant in (data as Dictionary)["shots"]:
			if t is float or t is int:
				times.append(float(t))
	return times


func music_for(id: StringName) -> String:
	var cue := str(cinematic(id).get("music", ""))
	if cue.is_empty():
		cue = str(music_cues.get(String(id), ""))
	if cue.is_empty():
		return ""
	var path := cue if cue.begins_with("res://") else MUSIC_PATH % cue
	return path if ResourceLoader.exists(path) else ""


## The start times of each shot in seconds from the start of the music, when the cinematic's cue
## has one marker per shot (its <cue>.json, from the music thread); otherwise empty.
func shot_markers(id: StringName) -> PackedFloat32Array:
	var result := PackedFloat32Array()
	var path := music_for(id)
	if path.is_empty():
		return result
	var info: Variant = _read_json(path.get_basename() + ".json") if FileAccess.file_exists(path.get_basename() + ".json") else null
	if not info is Dictionary or not (info as Dictionary).get("markers") is Array:
		return result
	for marker: Variant in info["markers"]:
		if marker is Dictionary and marker.has("time"):
			result.append(float(marker["time"]))
	var shots: Array = cinematic(id).get("shots", [])
	return result if result.size() == shots.size() else PackedFloat32Array()


## Every cinematic id the story files ask to play, for checking that each exists.
func all_triggered_cinematics() -> Array[StringName]:
	var result: Array[StringName] = []
	var add := func(value: Variant) -> void:
		var id := StringName(str(value)) if value != null else &""
		if not id.is_empty() and not result.has(id):
			result.append(id)
	add.call(prologue)
	for beat in beats:
		add.call(beat.get("cinematic"))
	for scenes: Variant in stage_scenes.values():
		if scenes is Dictionary:
			for key in ["before", "after", "lost"]:
				add.call(scenes.get(key))
			for moment: Variant in scenes.get("during", []):
				if moment is Dictionary:
					add.call(moment.get("cinematic"))
	add.call(assault.get("intro"))
	add.call(assault.get("outro"))
	add.call(assault.get("post_credits"))
	for movement: Variant in assault.get("movements", []):
		if movement is Dictionary:
			add.call(movement.get("cinematic"))
	return result


func _scene(stage_id: StringName, key: String) -> StringName:
	var scenes: Variant = stage_scenes.get(String(stage_id), {})
	if scenes is Dictionary and scenes.has(key):
		return StringName(str(scenes[key]))
	return &""


## The scene that plays when a stage is lost, if it has one (Solenne falls).
func lost_scene(stage_id: StringName) -> StringName:
	var id := _scene(stage_id, "lost")
	return id if cinematics.has(id) else &""


## The scene that plays when this wave of a stage starts, if any ({wave, cinematic}).
func scene_at_wave(stage_id: StringName, wave_number: int) -> StringName:
	var scenes: Variant = stage_scenes.get(String(stage_id), {})
	if not scenes is Dictionary:
		return &""
	for moment: Variant in scenes.get("during", []):
		if moment is Dictionary and int(moment.get("wave", -1)) == wave_number:
			var id := StringName(str(moment.get("cinematic", "")))
			if cinematics.has(id):
				return id
	return &""


## The scene for an assault phase starting (1 is the first movement), if any.
func assault_movement(phase: int) -> Dictionary:
	var movements: Variant = assault.get("movements", [])
	if movements is Array and phase >= 1 and phase <= (movements as Array).size():
		var movement: Variant = movements[phase - 1]
		return movement if movement is Dictionary else {}
	return {}


## Cinematics not yet seen that are due once `stages_won` stages are won and `stage_id` was just won.
## Pass an empty stage id to only check counts.
func due_after_win(stage_id: StringName, stages_won: int, seen: Array[StringName]) -> Array[StringName]:
	var result: Array[StringName] = []
	for beat in beats:
		var id := StringName(str(beat["cinematic"]))
		if seen.has(id) or result.has(id) or not cinematics.has(id):
			continue
		if beat.has("after_stage") and StringName(str(beat["after_stage"])) == stage_id:
			result.append(id)
		elif beat.has("after_stages_won") and stages_won >= int(beat["after_stages_won"]):
			result.append(id)
	# A stage's own scene comes before the plot beats its win unlocks. The ending plays after the assault.
	var own := _scene(stage_id, "after")
	if stage_id == StringName(str(assault.get("stage", "assault_1"))) and assault.has("outro"):
		own = StringName(str(assault["outro"]))
	if not own.is_empty() and cinematics.has(own) and not seen.has(own):
		result.push_front(own)
		# The reveal after the credits follows the ending straight away.
		var after_credits := StringName(str(assault.get("post_credits", "")))
		if own == StringName(str(assault.get("outro", ""))) and cinematics.has(after_credits) \
				and not seen.has(after_credits):
			result.insert(1, after_credits)
	return result


## Cinematics not yet seen that play before a stage starts.
func due_before_stage(stage_id: StringName, seen: Array[StringName]) -> Array[StringName]:
	var result: Array[StringName] = []
	var own := _scene(stage_id, "before")
	if stage_id == StringName(str(assault.get("stage", "assault_1"))) and assault.has("intro"):
		own = StringName(str(assault["intro"]))
	if not own.is_empty() and cinematics.has(own) and not seen.has(own):
		result.append(own)
	for beat in beats:
		var id := StringName(str(beat["cinematic"]))
		if beat.has("before_stage") and StringName(str(beat["before_stage"])) == stage_id \
				and not seen.has(id) and cinematics.has(id):
			result.append(id)
	return result


## The city a stage defends: {name, fall_text, capital}, or an empty dictionary.
func city(stage_id: StringName) -> Dictionary:
	var entry: Variant = cities.get(String(stage_id), {})
	return entry if entry is Dictionary else {}


## The character who is this boss enemy, or an empty dictionary.
## The name to show above a line: the character's name from characters.json (hidden characters keep
## theirs, "???"), or the id itself for a speaker who is not a character, such as the narrator.
func speaker_name(speaker: StringName) -> String:
	if speaker.is_empty():
		return ""
	var person: Dictionary = characters.get(speaker, {})
	return str(person.get("name", speaker))


func character_for_enemy(enemy_id: StringName) -> Dictionary:
	for person: Dictionary in characters.values():
		if StringName(str(person.get("boss_enemy", ""))) == enemy_id:
			return person
	return {}


static func portrait(character_id: StringName) -> Texture2D:
	var path := PORTRAIT_PATH % character_id
	return load(path) if ResourceLoader.exists(path) else null
