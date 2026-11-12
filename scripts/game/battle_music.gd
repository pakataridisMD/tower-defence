class_name BattleMusic
extends Node
## The music under a run. One 96 s loop in three layers that play in sync (written by
## tools/music/loops/battle.py): the calm layer plays all the time, the wave layer fades in while a
## wave is running, and the boss layer fades in on the last wave and when the lives run low.
## A boss wave gets its own music instead (tools/music/loops/boss_entrance.py and boss.py): the
## battle layers cut out, a 5 s entrance stinger hits, and a faster 140 bpm boss loop takes over
## until the wave ends, when it fades out and the calm layer comes back.
## Plays on the "Music" bus when the project has one.

enum Layer { CALM, WAVE, BOSS }

const LAYER_FILES: Array[String] = [
	"res://assets/game/music/battle_calm.ogg",
	"res://assets/game/music/battle_wave.ogg",
	"res://assets/game/music/battle_boss.ogg",
]
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
var volumes := PackedFloat32Array([0.0, SILENT_DB, SILENT_DB])
var entrance_player: AudioStreamPlayer
var boss_player: AudioStreamPlayer

var _sim: RunSim
var _sync: AudioStreamSynchronized
## Seconds since the boss entrance hit, or -1 when no boss wave is running.
var _boss_time := -1.0


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
	_sync = AudioStreamSynchronized.new()
	_sync.stream_count = LAYER_FILES.size()
	for i in LAYER_FILES.size():
		var stream := load(LAYER_FILES[i]) as AudioStreamOggVorbis
		if stream == null:
			push_warning("battle music layer missing: " + LAYER_FILES[i])
			continue
		stream.loop = true
		_sync.set_sync_stream(i, stream)
		_sync.set_sync_stream_volume(i, volumes[i])
	player = _new_player(_sync)
	player.play()
	var entrance := load(ENTRANCE_FILE) as AudioStreamOggVorbis
	var loop := load(BOSS_LOOP_FILE) as AudioStreamOggVorbis
	if entrance == null or loop == null:
		push_warning("boss music missing: " + ENTRANCE_FILE + ", " + BOSS_LOOP_FILE)
	if loop != null:
		loop.loop = true
	entrance_player = _new_player(_wrap(entrance))
	boss_player = _new_player(_wrap(loop))


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
	var last_wave := _sim.wave_index >= _sim.total_waves() - 1 and not _sim.is_endless()
	var boss := boss_fight(_sim.state, boss_wave)
	var t := targets(_sim.state, boss_wave, last_wave, _sim.lives, _sim.starting_lives)
	for i in volumes.size():
		if volumes[i] == t[i]:
			continue
		volumes[i] = move_toward(volumes[i], t[i], fade_rate(volumes[i], t[i], boss) * delta)
		_sync.set_sync_stream_volume(i, volumes[i])
	_update_boss(boss, delta)


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
	for p: AudioStreamPlayer in [player, entrance_player, boss_player]:
		if p == null:
			continue
		p.stop()
		var sync := p.stream as AudioStreamSynchronized
		p.stream = null
		if sync != null:
			for i in sync.stream_count:
				sync.set_sync_stream(i, null)
	_sync = null
	_sim = null
