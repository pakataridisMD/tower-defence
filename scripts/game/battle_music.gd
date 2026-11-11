class_name BattleMusic
extends Node
## The music under a run. One 96 s loop in three layers that play in sync (written by
## tools/music/loops/battle.py): the calm layer plays all the time, the wave layer fades in while a
## wave is running, and the boss layer fades in on boss waves, on the last wave, and when the lives
## run low. Plays on the "Music" bus when the project has one.

enum Layer { CALM, WAVE, BOSS }

const LAYER_FILES: Array[String] = [
	"res://assets/game/music/battle_calm.ogg",
	"res://assets/game/music/battle_wave.ogg",
	"res://assets/game/music/battle_boss.ogg",
]
const BUS := &"Music"
const SILENT_DB := -60.0
## Seconds a layer takes to come all the way in, and to go all the way out.
const FADE_IN := 1.5
const FADE_OUT := 4.0
## At or below this share of the starting lives, the boss layer comes in.
const DANGER_SHARE := 0.3

var player: AudioStreamPlayer
var volumes := PackedFloat32Array([0.0, SILENT_DB, SILENT_DB])

var _sim: RunSim
var _sync: AudioStreamSynchronized


## Target volume (dB) of each layer for the state of a run.
static func targets(state: RunSim.State, boss_wave: bool, last_wave: bool, lives: int,
		starting_lives: int) -> PackedFloat32Array:
	var t := PackedFloat32Array([0.0, SILENT_DB, SILENT_DB])
	match state:
		RunSim.State.WAVE:
			t[Layer.WAVE] = 0.0
			if boss_wave or last_wave or in_danger(lives, starting_lives):
				t[Layer.BOSS] = 0.0
		RunSim.State.WON, RunSim.State.LOST:
			t[Layer.CALM] = SILENT_DB
	return t


static func in_danger(lives: int, starting_lives: int) -> bool:
	return starting_lives > 0 and lives <= floori(starting_lives * DANGER_SHARE)


## dB per second for a layer moving from `from` towards `to`.
static func fade_rate(from: float, to: float) -> float:
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
	player = AudioStreamPlayer.new()
	player.stream = _sync
	player.bus = BUS if AudioServer.get_bus_index(BUS) >= 0 else &"Master"
	add_child(player)
	player.play()


func _process(delta: float) -> void:
	if _sim == null or _sync == null:
		return
	var wave := _sim.current_wave()
	var boss_wave := wave != null and wave.is_boss
	var last_wave := _sim.wave_index >= _sim.total_waves() - 1
	var t := targets(_sim.state, boss_wave, last_wave, _sim.lives, _sim.starting_lives)
	for i in volumes.size():
		if volumes[i] == t[i]:
			continue
		volumes[i] = move_toward(volumes[i], t[i], fade_rate(volumes[i], t[i]) * delta)
		_sync.set_sync_stream_volume(i, volumes[i])


## Stop and let go of the streams when the run's scene closes, or the audio server still holds
## their playbacks when the game quits.
func _exit_tree() -> void:
	if player != null:
		player.stop()
		player.stream = null
	if _sync != null:
		for i in _sync.stream_count:
			_sync.set_sync_stream(i, null)
	_sync = null
	_sim = null
