class_name MenuMusic
extends Node
## The title screen's music, "The Last Watch" (tools/music/loops/menu.py): a seamless loop on the
## Music bus that fades in when the menu opens. Settings > Sound > Menu music turns it off and on
## (AudioSettings.menu_music_on, saved); it fades out or back in at once. The Music volume and mute
## apply to it as to all music.
##
## Coming back to the title screen in the same session picks the loop up where it was left.

const FILE := "res://assets/game/music/menu_main.ogg"
const BUS := &"Music"
const SILENT_DB := -60.0
const FADE_IN := 2.5
const FADE_OUT := 1.0

## Where the music starts the first time: the second section ("the watch", 8 bars of 4/4 at
## 84 bpm in), so the menu opens on the music gathering rather than on its quietest part.
const FIRST_START := 8 * 4 * 60.0 / 84.0

## Where the loop was when the menu last closed, so it carries on rather than starting again.
static var resume_at := FIRST_START

var player: AudioStreamPlayer
## The music's own fade, 0 (silent) to 1, on top of the bus volume.
var level := 0.0
var _sync: AudioStreamSynchronized


func _ready() -> void:
	var stream := load(FILE) as AudioStreamOggVorbis
	if stream == null:
		push_warning("menu music missing: " + FILE)
		return
	stream.loop = true
	# Played inside a one-stream AudioStreamSynchronized, like the battle music, so _exit_tree can
	# take the file out of a playback the audio server still holds when the game quits.
	_sync = AudioStreamSynchronized.new()
	_sync.stream_count = 1
	_sync.set_sync_stream(0, stream)
	player = AudioStreamPlayer.new()
	player.stream = _sync
	player.bus = BUS if AudioServer.get_bus_index(BUS) >= 0 else &"Master"
	player.volume_db = SILENT_DB
	add_child(player)
	if wanted():
		player.play(fposmod(resume_at, stream.get_length()) if stream.get_length() > 0.0 else 0.0)


## Set while another piece of menu music plays instead (the Credits page plays the trailer score).
static var held := false


## True while the player wants menu music.
static func wanted() -> bool:
	return AudioSettings.menu_music_on() and not held


func _process(delta: float) -> void:
	if player == null:
		return
	var on := wanted()
	if on and not player.playing:
		player.play(_position())
	var target := 1.0 if on else 0.0
	level = move_toward(level, target, delta / (FADE_IN if on else FADE_OUT))
	player.volume_db = linear_to_db(maxf(level, 0.001)) if level > 0.001 else SILENT_DB
	if not on and level <= 0.0 and player.playing:
		resume_at = _position()
		player.stop()


func _position() -> float:
	return player.get_playback_position() if player != null and player.playing else resume_at


func _exit_tree() -> void:
	if player == null:
		return
	resume_at = _position()
	player.stop()
	player.stream = null
	if _sync != null:
		_sync.set_sync_stream(0, null)
	_sync = null
