class_name SoundPlayer
extends Node
## Plays the game's sound effects. Registered as the Sfx autoload.
##
## Every sound is listed in assets/audio/sfx/catalogue.json, which tools/sfx/build.py writes next to
## the rendered files: its variations, its bus, its volume, how many copies may sound at once and
## the shortest gap between two starts. Board sounds are panned by where they happen on screen.
##
## Call it through the static helpers, which do nothing when the autoload is missing (scripts run
## with -s): SoundPlayer.sfx(&"ui_click") or SoundPlayer.sfx(&"impact_fire", position).
## Every button in the game clicks on its own: buttons are wired up as they enter the tree. Give a
## button the meta "no_sfx" to keep it quiet.

const CATALOGUE_PATH := "res://assets/audio/sfx/catalogue.json"
const SOUND_ROOT := "res://assets/audio/sfx/"
const FLAT_PLAYERS := 16
const PLACED_PLAYERS := 40
const MUSIC_BUS := &"Music"
## How long a duck takes to reach its depth and to come back.
const DUCK_IN := 0.08
const DUCK_OUT := 0.9
## How far 2D sounds carry; the board is under 2000 pixels wide, so everything stays audible.
const MAX_DISTANCE := 3200.0
const HISTORY_SIZE := 256

## A sound started (tests listen to it).
signal played(sound: StringName)

static var instance: SoundPlayer

## False silences everything (the bot's footage runs can turn it off).
var enabled := true
## Sound name -> settings from the catalogue.
var sounds: Dictionary[StringName, Dictionary] = {}
## Boss enemy id -> boss sound set, and enemy id -> death sound.
var boss_sets: Dictionary[StringName, StringName] = {}
var enemy_deaths: Dictionary[StringName, StringName] = {}
## Names of the last sounds started, newest last. Tests read it.
var history: Array[StringName] = []

var _streams: Dictionary[String, AudioStream] = {}
var _flat: Array[AudioStreamPlayer] = []
var _placed: Array[AudioStreamPlayer2D] = []
var _last_start: Dictionary[StringName, float] = {}
var _last_variant: Dictionary[StringName, int] = {}
var _warned: Dictionary[StringName, bool] = {}
var _duck_db := 0.0
var _duck_now := 0.0
var _duck_hold := 0.0
var _duck_tween: Tween
## With no sound card (headless runs, CI) nothing is really played: the dummy audio driver never
## releases what it played, which shows as leaked resources at exit. Sounds are still chosen,
## counted and reported, so tests see the same decisions.
var _silent := false


func _enter_tree() -> void:
	instance = self
	process_mode = Node.PROCESS_MODE_ALWAYS


func _exit_tree() -> void:
	if instance == self:
		instance = null
	# Let go of every stream, or sounds still playing at quit keep their resources alive.
	for player: Node in _all_players():
		player.call(&"stop")
		player.set(&"stream", null)
	_streams.clear()


func _ready() -> void:
	_silent = AudioServer.get_driver_name() == "Dummy" or DisplayServer.get_name() == "headless"
	AudioSettings.load_saved()
	load_catalogue()
	for i in FLAT_PLAYERS:
		var player := AudioStreamPlayer.new()
		add_child(player)
		_flat.append(player)
	for i in PLACED_PLAYERS:
		var placed := AudioStreamPlayer2D.new()
		placed.max_distance = MAX_DISTANCE
		placed.attenuation = 0.6
		placed.panning_strength = 0.8
		add_child(placed)
		_placed.append(placed)
	get_tree().node_added.connect(_on_node_added)


func load_catalogue() -> void:
	sounds.clear()
	boss_sets.clear()
	enemy_deaths.clear()
	var text := FileAccess.get_file_as_string(CATALOGUE_PATH)
	var data: Variant = JSON.parse_string(text)
	if not data is Dictionary:
		push_error("Sound catalogue %s is missing or broken" % CATALOGUE_PATH)
		return
	var sound_table: Dictionary = data.get("sounds", {})
	for key: String in sound_table:
		sounds[StringName(key)] = sound_table[key]
	var bosses: Dictionary = data.get("boss_sets", {})
	for key: String in bosses:
		boss_sets[StringName(key)] = StringName(bosses[key])
	var deaths: Dictionary = data.get("enemy_deaths", {})
	for key: String in deaths:
		enemy_deaths[StringName(key)] = StringName(deaths[key])


# --- Static helpers ------------------------------------------------------------------

## Plays a sound if the Sfx autoload is running. `at` is a canvas position for board sounds.
static func sfx(sound: StringName, at: Variant = null, volume_db: float = 0.0, pitch: float = 1.0) -> bool:
	return instance != null and instance.play(sound, at, volume_db, pitch)


static func duck(db: float, seconds: float) -> void:
	if instance != null:
		instance.duck_music(db, seconds)


# --- Playing -----------------------------------------------------------------------

func has_sound(sound: StringName) -> bool:
	return sounds.has(sound)


## The files of a sound, as res:// paths.
func files_of(sound: StringName) -> PackedStringArray:
	var out := PackedStringArray()
	if sounds.has(sound):
		for file: String in sounds[sound].get("files", []):
			out.append(SOUND_ROOT + file)
	return out


## Starts a sound. Returns false when it is unknown, too soon after the last one, already playing
## as often as allowed, or every player is busy with something more important.
func play(sound: StringName, at: Variant = null, volume_db: float = 0.0, pitch: float = 1.0) -> bool:
	if not enabled:
		return false
	var spec: Dictionary = sounds.get(sound, {})
	if spec.is_empty():
		if not _warned.has(sound):
			_warned[sound] = true
			push_warning("Unknown sound effect: %s" % sound)
		return false
	var now := Time.get_ticks_msec() / 1000.0
	var gap: float = spec.get("min_gap", 0.0)
	if _last_start.has(sound) and now - _last_start[sound] < gap:
		return false
	var priority: int = spec.get("priority", 1)
	var positional: bool = spec.get("positional", true) and at is Vector2
	var player: Node = _free_player(sound, positional, priority, spec.get("max_voices", 4))
	if player == null:
		return false
	var stream := _pick_stream(sound, spec)
	if stream == null:
		return false
	_last_start[sound] = now
	if _silent:
		_record(sound)
		return true
	var jitter: float = spec.get("pitch_jitter", 0.0)
	var bus := StringName(spec.get("bus", "Sfx"))
	if AudioServer.get_bus_index(bus) < 0:
		bus = &"Master"
	var volume: float = spec.get("volume_db", 0.0) + volume_db
	var scale := pitch * (1.0 + randf_range(-jitter, jitter))
	if positional:
		var placed := player as AudioStreamPlayer2D
		placed.stream = stream
		placed.bus = bus
		placed.volume_db = volume
		placed.pitch_scale = scale
		placed.global_position = at
		placed.play()
	else:
		var flat := player as AudioStreamPlayer
		flat.stream = stream
		flat.bus = bus
		flat.volume_db = volume
		flat.pitch_scale = scale
		flat.play()
	player.set_meta(&"sound", sound)
	player.set_meta(&"priority", priority)
	player.set_meta(&"started", now)
	var duck_db: float = spec.get("duck_db", 0.0)
	if duck_db < 0.0:
		duck_music(duck_db, spec.get("duck_time", 1.0))
	_record(sound)
	return true


func _record(sound: StringName) -> void:
	history.append(sound)
	if history.size() > HISTORY_SIZE:
		history.remove_at(0)
	played.emit(sound)


## Stops every copy of a sound (or every sound when the name is empty).
func stop(sound: StringName = &"") -> void:
	for player: Node in _all_players():
		if sound.is_empty() or player.get_meta(&"sound", &"") == sound:
			player.call(&"stop")


func is_playing(sound: StringName) -> bool:
	for player: Node in _all_players():
		if player.get_meta(&"sound", &"") == sound and player.get(&"playing"):
			return true
	return false


## Lowers the music bus by db (a negative number) for a few seconds, then brings it back. A deeper
## duck takes over a lighter one.
func duck_music(db: float, seconds: float) -> void:
	var bus := AudioServer.get_bus_index(MUSIC_BUS)
	if bus < 0:
		return
	var now := Time.get_ticks_msec() / 1000.0
	if db > _duck_db and now < _duck_hold:
		_duck_hold = maxf(_duck_hold, now + seconds)
		return
	_duck_db = db
	_duck_hold = now + seconds
	if _duck_tween != null:
		_duck_tween.kill()
	_duck_tween = create_tween()
	_duck_tween.tween_method(_set_duck, _duck_now, db, DUCK_IN)
	_duck_tween.tween_interval(seconds)
	_duck_tween.tween_method(_set_duck, db, 0.0, DUCK_OUT)
	_duck_tween.tween_callback(func() -> void: _duck_db = 0.0)


## How far the music is ducked right now, in dB (0 when it is not). AudioSettings adds it on top of
## the player's music volume.
func music_duck_db() -> float:
	return _duck_now


func _set_duck(db: float) -> void:
	_duck_now = db
	AudioSettings.apply_bus(MUSIC_BUS, db)


func _all_players() -> Array[Node]:
	var out: Array[Node] = []
	out.append_array(_flat)
	out.append_array(_placed)
	return out


## A free player, or the least important one to cut short. Null when the sound already plays as
## often as allowed or nothing less important can be stolen.
func _free_player(sound: StringName, positional: bool, priority: int, max_voices: int) -> Node:
	var pool: Array[Node] = []
	if positional:
		pool.append_array(_placed)
	else:
		pool.append_array(_flat)
	var same: Array[Node] = []
	var free: Node = null
	var victim: Node = null
	for player: Node in pool:
		var playing: bool = player.get(&"playing")
		if not playing:
			if free == null:
				free = player
			continue
		if player.get_meta(&"sound", &"") == sound:
			same.append(player)
		# The victim: the least important sound, the oldest of those, never a more important one.
		var p: int = player.get_meta(&"priority", 0)
		if p > priority:
			continue
		if victim == null:
			victim = player
			continue
		var vp: int = victim.get_meta(&"priority", 0)
		var older: bool = player.get_meta(&"started", 0.0) < victim.get_meta(&"started", 0.0)
		if p < vp or (p == vp and older):
			victim = player
	if same.size() >= max_voices:
		# Cut the oldest copy short so the newest is heard, but only for quick, repeated sounds.
		if max_voices >= 2:
			var oldest := same[0]
			for player in same:
				if player.get_meta(&"started", 0.0) < oldest.get_meta(&"started", 0.0):
					oldest = player
			oldest.call(&"stop")
			return oldest
		return null
	if free != null:
		return free
	if victim != null:
		victim.call(&"stop")
	return victim


func _pick_stream(sound: StringName, spec: Dictionary) -> AudioStream:
	var files: Array = spec.get("files", [])
	if files.is_empty():
		return null
	var index := 0
	if files.size() > 1:
		# Never the same variation twice in a row.
		index = randi() % files.size()
		if _last_variant.get(sound, -1) == index:
			index = (index + 1 + randi() % (files.size() - 1)) % files.size()
	_last_variant[sound] = index
	var path: String = SOUND_ROOT + str(files[index])
	if not _streams.has(path):
		var stream := load(path) as AudioStream
		if stream == null:
			push_error("Missing sound file %s" % path)
			return null
		_streams[path] = stream
	return _streams[path]


func _on_node_added(node: Node) -> void:
	var button := node as BaseButton
	if button == null or button.has_meta(&"no_sfx"):
		return
	# A "Back" button steps back a page, and sounds like it.
	var back := button is Button and (button as Button).text == "Back"
	button.pressed.connect(func() -> void: play(&"ui_back" if back else &"ui_click"))
	button.mouse_entered.connect(func() -> void:
		if not button.disabled:
			play(&"ui_hover"))
