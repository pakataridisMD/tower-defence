class_name AudioSettings
extends RefCounted
## The player's volume and mute for each audio bus, kept in user://settings.cfg and applied at start-up
## (the Sfx autoload calls load_saved). Volumes are shares from 0 to 1; 0 is silent.
##
## Bot runs (--autoplay) and test runs keep the settings in memory only, so they never touch the
## player's file. The Music bus also carries the sound effects' ducking: SoundPlayer adds its duck
## on top of the player's volume through apply_bus.

const PATH := "user://settings.cfg"
const SECTION := "audio"
## Every bus the player can set: [bus name, name shown in the settings, starting volume].
const BUSES: Array[Array] = [
	[&"Master", "Master (all sound)", 0.9],
	[&"Music", "Music", 0.8],
	[&"Sfx", "Effects", 0.9],
	[&"Ui", "Interface", 0.8],
	[&"Voice", "Voices and narration", 1.0],
]
const MASTER := &"Master"
const MUSIC := &"Music"

static var path := PATH
static var persist := true
static var _volume: Dictionary[StringName, float] = {}
static var _muted: Dictionary[StringName, bool] = {}
static var _loaded := false


## Reads the saved settings (or the starting ones) and applies them to the buses.
static func load_saved() -> void:
	_defaults()
	persist = not (OS.get_cmdline_user_args().has("--autoplay") or _running_tests())
	if persist:
		var file := ConfigFile.new()
		if file.load(path) == OK:
			for bus: StringName in _volume.keys():
				_volume[bus] = clampf(float(file.get_value(SECTION, "%s_volume" % bus, _volume[bus])), 0.0, 1.0)
				_muted[bus] = bool(file.get_value(SECTION, "%s_muted" % bus, false))
	_loaded = true
	apply()


## Back to the starting volumes, in memory only until the next change. Tests call this.
static func reset_to_defaults() -> void:
	_defaults()
	_loaded = true
	apply()
	save()


static func volume(bus: StringName) -> float:
	_ensure()
	return _volume.get(bus, 1.0)


static func is_muted(bus: StringName) -> bool:
	_ensure()
	return _muted.get(bus, false)


static func set_volume(bus: StringName, share: float) -> void:
	_ensure()
	if not _volume.has(bus):
		return
	_volume[bus] = clampf(share, 0.0, 1.0)
	apply()
	save()


static func set_muted(bus: StringName, muted: bool) -> void:
	_ensure()
	if not _muted.has(bus):
		return
	_muted[bus] = muted
	apply()
	save()


## Mutes or unmutes everything (the M key in a run). Returns true when the game is now muted.
static func toggle_mute_all() -> bool:
	set_muted(MASTER, not is_muted(MASTER))
	return is_muted(MASTER)


## Sets every bus from the settings.
static func apply() -> void:
	for entry in BUSES:
		var bus: StringName = entry[0]
		var extra := 0.0
		if bus == MUSIC and SoundPlayer.instance != null:
			extra = SoundPlayer.instance.music_duck_db()
		apply_bus(bus, extra)


## Sets one bus from the settings, plus `extra_db` (the music duck).
static func apply_bus(bus: StringName, extra_db: float = 0.0) -> void:
	_ensure()
	var index := AudioServer.get_bus_index(bus)
	if index < 0:
		return
	var share: float = _volume.get(bus, 1.0)
	AudioServer.set_bus_volume_db(index, linear_to_db(maxf(share, 0.0001)) + extra_db)
	AudioServer.set_bus_mute(index, _muted.get(bus, false) or share <= 0.0)


static func save() -> void:
	if not persist:
		return
	var file := ConfigFile.new()
	file.load(path)  # Keep any other sections.
	for bus: StringName in _volume.keys():
		file.set_value(SECTION, "%s_volume" % bus, snappedf(_volume[bus], 0.01))
		file.set_value(SECTION, "%s_muted" % bus, _muted[bus])
	file.save(path)


static func _defaults() -> void:
	_volume.clear()
	_muted.clear()
	for entry in BUSES:
		_volume[entry[0]] = entry[2]
		_muted[entry[0]] = false


static func _ensure() -> void:
	if not _loaded:
		_defaults()
		_loaded = true


static func _running_tests() -> bool:
	for arg in OS.get_cmdline_args():
		if arg.contains("addons/gut/"):
			return true
	return false
