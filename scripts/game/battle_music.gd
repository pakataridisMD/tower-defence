class_name BattleMusic
extends Node
## The music under a run. Each track is a loop in three layers that play in sync: the calm layer
## plays all the time, the wave layer fades in while a wave is running, and the boss layer fades in
## on the last wave and when the lives run low.
## Every map has a pool of tracks for its element (tools/music/loops/realms.py, three per element,
## plus Hold the Line from tools/music/loops/battle.py), so a long mission does not loop one tune:
## the run starts on a random track of the pool and moves on to the next one in the build phase
## after every few waves and after every boss wave, crossfading between them.
## A boss wave gets its own music instead (tools/music/loops/boss_entrance.py and boss.py): the
## battle layers cut out, a 5 s entrance stinger hits, and a faster 140 bpm boss loop takes over
## until the wave ends, when it fades out and the calm layer comes back.
## Plays on the "Music" bus when the project has one.

enum Layer { CALM, WAVE, BOSS }

const MUSIC_DIR := "res://assets/game/music/"
const LAYER_NAMES: Array[String] = ["calm", "wave", "boss"]
## Hold the Line, the first battle track. It is in every pool.
const DEFAULT_TRACK := "battle"
## The tracks of each map biome. A biome not listed here (the meadow skirmish maps) gets them all.
const REALM_TRACKS := {
	&"fire": ["realm_fire_1", "realm_fire_2", "realm_fire_3"],
	&"water": ["realm_water_1", "realm_water_2", "realm_water_3"],
	&"earth": ["realm_earth_1", "realm_earth_2", "realm_earth_3"],
	&"storm": ["realm_storm_1", "realm_storm_2", "realm_storm_3"],
	&"nature": ["realm_nature_1", "realm_nature_2", "realm_nature_3"],
	&"void": ["realm_void_1", "realm_void_2", "realm_void_3"],
	&"heart": ["realm_heart_1", "realm_heart_2", "realm_heart_3"],
}
## Waves played on one track before the build phase moves on to the next one.
const WAVES_PER_TRACK := 3
## Seconds the crossfade between two tracks takes.
const CROSSFADE := 4.0
const ENTRANCE_FILE := "res://assets/game/music/boss_entrance_hit.ogg"
const BOSS_LOOP_FILE := "res://assets/game/music/boss_fight.ogg"
## Seconds from the entrance's first hit (at 0.0 s, no pickup) to the downbeat where the boss
## loop takes over: 3 bars of 4/4 at 140 bpm. Sound effects can time a boss reveal to it.
const ENTRANCE_SECONDS := 3 * 4 * 60.0 / 140.0
## Seconds the battle layers take to cut out when a boss wave starts, and the boss loop to fade
## out when it ends.
const BOSS_CUT := 0.4
const BOSS_FADE_OUT := 3.0
const BUS := &"Music"
const SILENT_DB := -60.0
## Seconds a layer takes to come all the way in, and to go all the way out.
const FADE_IN := 1.5
const FADE_OUT := 4.0
## At or below this share of the starting lives, the boss layer comes in.
const DANGER_SHARE := 0.3

var player: AudioStreamPlayer
## The track pool of this run's map and which one is playing.
var pool: Array[String] = []
var track_index := 0
## Waves finished since the current track started.
var waves_on_track := 0
var volumes := PackedFloat32Array([0.0, SILENT_DB, SILENT_DB])
var entrance_player: AudioStreamPlayer
var boss_player: AudioStreamPlayer

var _sim: RunSim
var _sync: AudioStreamSynchronized
## Seconds since the boss entrance hit, or -1 when no boss wave is running.
var _boss_time := -1.0
## The track that is fading out after a change, with its stream.
var _old_player: AudioStreamPlayer
var _last_state := RunSim.State.BUILDING
var _last_wave_boss := false


## The tracks for a map biome: its realm's three, then Hold the Line. Unknown biomes (the meadow
## skirmish maps) get every track.
static func tracks_for(biome: StringName) -> Array[String]:
	var out: Array[String] = []
	if REALM_TRACKS.has(biome):
		out.assign(REALM_TRACKS[biome])
	else:
		for k: StringName in REALM_TRACKS:
			out.append_array(REALM_TRACKS[k])
	out.append(DEFAULT_TRACK)
	return out


static func layer_file(track: String, layer: int) -> String:
	return MUSIC_DIR + "%s_%s.ogg" % [track, LAYER_NAMES[layer]]


## The build phase after a finished wave moves to the next track when the last wave was a boss
## wave, or when the track has played WAVES_PER_TRACK waves.
static func should_change(waves_done: int, boss_wave_done: bool, pool_size: int) -> bool:
	return pool_size > 1 and (boss_wave_done or waves_done >= WAVES_PER_TRACK)


## Target volume (dB) of each layer for the state of a run.
static func targets(state: RunSim.State, boss_wave: bool, last_wave: bool, lives: int,
		starting_lives: int) -> PackedFloat32Array:
	var t := PackedFloat32Array([0.0, SILENT_DB, SILENT_DB])
	if boss_fight(state, boss_wave):
		t[Layer.CALM] = SILENT_DB
		return t
	match state:
		RunSim.State.WAVE:
			t[Layer.WAVE] = 0.0
			if last_wave or in_danger(lives, starting_lives):
				t[Layer.BOSS] = 0.0
		RunSim.State.WON, RunSim.State.LOST:
			t[Layer.CALM] = SILENT_DB
	return t


## A boss wave is running: the boss entrance and loop play instead of the battle layers.
static func boss_fight(state: RunSim.State, boss_wave: bool) -> bool:
	return state == RunSim.State.WAVE and boss_wave


static func in_danger(lives: int, starting_lives: int) -> bool:
	return starting_lives > 0 and lives <= floori(starting_lives * DANGER_SHARE)


## dB per second for a layer moving from `from` towards `to`. A boss wave cuts the layers out fast.
static func fade_rate(from: float, to: float, boss: bool = false) -> float:
	if boss and to < from:
		return -SILENT_DB / BOSS_CUT
	return -SILENT_DB / (FADE_IN if to > from else FADE_OUT)


func setup(sim: RunSim) -> void:
	_sim = sim
	var biome: StringName = &"meadow"
	if sim.config != null and sim.config.map != null:
		biome = sim.config.map.biome
	pool = tracks_for(biome)
	var rng := RandomNumberGenerator.new()
	rng.randomize()
	track_index = rng.randi_range(0, pool.size() - 1)
	_start_track(pool[track_index], 0.0)
	var entrance := load(ENTRANCE_FILE) as AudioStreamOggVorbis
	var loop := load(BOSS_LOOP_FILE) as AudioStreamOggVorbis
	if entrance == null or loop == null:
		push_warning("boss music missing: " + ENTRANCE_FILE + ", " + BOSS_LOOP_FILE)
	if loop != null:
		loop.loop = true
	entrance_player = _new_player(_wrap(entrance))
	boss_player = _new_player(_wrap(loop))


## Start a track's layers in sync, at the current layer volumes, with the player at `start_db`.
func _start_track(track: String, start_db: float) -> void:
	_sync = AudioStreamSynchronized.new()
	_sync.stream_count = LAYER_NAMES.size()
	for i in LAYER_NAMES.size():
		var path := layer_file(track, i)
		var stream := load(path) as AudioStreamOggVorbis
		if stream == null:
			push_warning("battle music layer missing: " + path)
			continue
		stream.loop = true
		_sync.set_sync_stream(i, stream)
		_sync.set_sync_stream_volume(i, volumes[i])
	player = _new_player(_sync)
	player.volume_db = start_db
	player.play()


## Crossfade to the next track of the pool.
func next_track() -> void:
	if pool.size() < 2:
		return
	if _old_player != null:
		_release(_old_player)
	_old_player = player
	track_index = (track_index + 1) % pool.size()
	waves_on_track = 0
	_start_track(pool[track_index], SILENT_DB)


func current_track() -> String:
	return pool[track_index] if not pool.is_empty() else ""


## The boss streams play inside a one-stream AudioStreamSynchronized, like the battle layers, so
## _exit_tree can take the file streams out of a playback the audio server still holds at quit.
func _wrap(stream: AudioStream) -> AudioStreamSynchronized:
	if stream == null:
		return null
	var w := AudioStreamSynchronized.new()
	w.stream_count = 1
	w.set_sync_stream(0, stream)
	return w


func _new_player(stream: AudioStream) -> AudioStreamPlayer:
	var p := AudioStreamPlayer.new()
	p.stream = stream
	p.bus = BUS if AudioServer.get_bus_index(BUS) >= 0 else &"Master"
	add_child(p)
	return p


func _process(delta: float) -> void:
	if _sim == null or _sync == null:
		return
	var wave := _sim.current_wave()
	var boss_wave := wave != null and wave.is_boss
	var last_wave := _sim.wave_index >= _sim.total_waves() - 1
	var boss := boss_fight(_sim.state, boss_wave)
	_track_rotation(boss_wave)
	_crossfade(delta)
	var t := targets(_sim.state, boss_wave, last_wave, _sim.lives, _sim.starting_lives)
	for i in volumes.size():
		if volumes[i] == t[i]:
			continue
		volumes[i] = move_toward(volumes[i], t[i], fade_rate(volumes[i], t[i], boss) * delta)
		_sync.set_sync_stream_volume(i, volumes[i])
	_update_boss(boss, delta)


## Count finished waves and move to the next track when a build phase starts.
func _track_rotation(boss_wave: bool) -> void:
	var state := _sim.state
	if _last_state == RunSim.State.WAVE and state != RunSim.State.WAVE:
		waves_on_track += 1
		if state == RunSim.State.BUILDING and should_change(waves_on_track, _last_wave_boss, pool.size()):
			next_track()
	if state == RunSim.State.WAVE:
		_last_wave_boss = boss_wave
	_last_state = state


func _crossfade(delta: float) -> void:
	var rate := -SILENT_DB / CROSSFADE
	if player != null and player.volume_db < 0.0:
		player.volume_db = move_toward(player.volume_db, 0.0, rate * delta)
	if _old_player != null:
		_old_player.volume_db = move_toward(_old_player.volume_db, SILENT_DB, rate * delta)
		if _old_player.volume_db <= SILENT_DB:
			_release(_old_player)
			_old_player = null


func _update_boss(boss: bool, delta: float) -> void:
	if boss:
		if _boss_time < 0.0:
			_boss_time = 0.0
			boss_player.stop()  # a loop still fading out from the last boss wave
			if entrance_player.stream != null:
				entrance_player.play()
		else:
			_boss_time += delta
		if _boss_time >= ENTRANCE_SECONDS and boss_player.stream != null and not boss_player.playing:
			boss_player.volume_db = 0.0
			# start where the loop would be had it started exactly on the downbeat
			boss_player.play(_boss_time - ENTRANCE_SECONDS)
		return
	_boss_time = -1.0
	if boss_player.playing:
		boss_player.volume_db = move_toward(boss_player.volume_db, SILENT_DB, -SILENT_DB / BOSS_FADE_OUT * delta)
		if boss_player.volume_db <= SILENT_DB:
			boss_player.stop()


## Stop and let go of the streams when the run's scene closes, or the audio server still holds
## their playbacks when the game quits.
func _exit_tree() -> void:
	for p: AudioStreamPlayer in [player, _old_player, entrance_player, boss_player]:
		if p != null:
			_release(p)
	_old_player = null
	_sync = null
	_sim = null


func _release(p: AudioStreamPlayer) -> void:
	p.stop()
	var sync := p.stream as AudioStreamSynchronized
	p.stream = null
	if sync != null:
		for i in sync.stream_count:
			sync.set_sync_stream(i, null)
	if p.get_parent() == self and p != player and p != entrance_player and p != boss_player:
		p.queue_free()
