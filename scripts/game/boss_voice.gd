class_name BossVoice
extends Node
## What the bosses say in battle: ElevenLabs lines recorded by tools/voice/boss_lines.py from
## data/story/boss_lines.json into assets/audio/voice/bosses/<boss>/<kind>_<n>.ogg, listed with their
## lengths in assets/audio/voice/bosses/lines.json.
##
## One boss speaks at a time, on the Voice bus, with the music ducked under it. A line that matters
## (arrival, rage, a new form, death) cuts in over chatter; chatter waits its turn or is dropped.

const LINES_FILE := "res://assets/audio/voice/bosses/lines.json"
const VOICE_DIR := "res://assets/audio/voice/bosses/"
## Kinds that cut in over whatever is being said.
const URGENT: Array[StringName] = [&"arrive", &"enrage", &"transform", &"flee", &"death", &"destroy"]
## The music sinks this far under a boss's words.
const DUCK_DB := -7.0
## Each kind of line, from the same boss, at most this often (seconds of real time).
const KIND_GAP := 7.0

## Boss id -> {kind -> [{file, text, secs}]}, with shared lines folded in.
static var _lines: Dictionary = {}
static var _loaded := false

## Every line started, newest last (as "<boss>/<kind>"), for tests: kept even when silent.
var history: Array[String] = []
var _player: AudioStreamPlayer
var _silent := false
var _speaking_until := 0.0
var _speaking_urgent := false
var _last_kind: Dictionary[String, float] = {}
var _last_index: Dictionary[String, int] = {}

signal spoke(boss_id: StringName, kind: StringName, text: String, seconds: float)


func _ready() -> void:
	_silent = AudioServer.get_driver_name() == "Dummy" or DisplayServer.get_name() == "headless"
	_player = AudioStreamPlayer.new()
	_player.bus = &"Voice" if AudioServer.get_bus_index(&"Voice") >= 0 else &"Master"
	add_child(_player)


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	if not FileAccess.file_exists(LINES_FILE):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(LINES_FILE))
	if parsed is Dictionary:
		_lines = parsed


## The lines a boss has of one kind, its own first, then those of the boss it shares with.
static func lines_of(boss_id: StringName, kind: StringName) -> Array:
	_load()
	var seen := {}
	var id := String(boss_id)
	while not id.is_empty() and not seen.has(id):
		seen[id] = true
		var entry: Dictionary = _lines.get(id, {})
		var only: Array = entry.get("only", [])
		if only.is_empty() or only.has(String(kind)):
			var own: Array = (entry.get("lines", {}) as Dictionary).get(String(kind), [])
			if not own.is_empty():
				return own
		id = entry.get("share", "")
	return []


## True when this boss has recorded lines (its old synthetic chatter should stay quiet).
static func speaks(boss_id: StringName) -> bool:
	return not lines_of(boss_id, &"taunt").is_empty() or not lines_of(boss_id, &"arrive").is_empty()


func is_speaking() -> bool:
	return _now() < _speaking_until


## Says a line of this kind (falling back to a taunt). Returns its length in seconds, or 0 when the
## boss has nothing to say, said the same kind too recently, or someone else is talking.
func say(boss_id: StringName, kind: StringName) -> float:
	var lines := lines_of(boss_id, kind)
	if lines.is_empty() and kind not in URGENT:
		lines = lines_of(boss_id, &"taunt")
	if lines.is_empty():
		return 0.0
	var urgent := kind in URGENT
	var now := _now()
	var key := "%s/%s" % [boss_id, kind]
	if not urgent and now - float(_last_kind.get(key, -100.0)) < KIND_GAP:
		return 0.0
	if now < _speaking_until and (not urgent or _speaking_urgent):
		return 0.0
	var index := (int(_last_index.get(key, -1)) + 1) % lines.size()
	_last_index[key] = index
	var line: Dictionary = lines[index]
	var seconds := float(line.get("secs", 2.0))
	_last_kind[key] = now
	_speaking_until = now + seconds + 0.4
	_speaking_urgent = urgent
	history.append(key)
	if history.size() > 64:
		history.remove_at(0)
	if not _silent:
		var stream: AudioStream = load(VOICE_DIR + String(line["file"]))
		if stream != null:
			_player.stream = stream
			_player.play()
			SoundPlayer.duck(DUCK_DB, seconds)
	spoke.emit(boss_id, kind, String(line.get("text", "")), seconds)
	return seconds


func stop() -> void:
	_speaking_until = 0.0
	if _player != null:
		_player.stop()


func _now() -> float:
	return Time.get_ticks_msec() / 1000.0
