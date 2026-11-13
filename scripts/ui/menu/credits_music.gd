class_name CreditsMusic
extends Node
## The Credits page's music: the trailer score (tools/music/cues/trailer*.py), played one cue after
## another on the Music bus while the page is open. The title music (MenuMusic) steps aside for it
## and comes back when the page closes. Settings > Sound > Menu music turns this off too.

const FILES: Array[String] = [
	"res://assets/story/music/trailer2.ogg",
	"res://assets/story/music/trailer.ogg",
	"res://assets/story/music/trailer2_short.ogg",
	"res://assets/story/music/trailer_short.ogg",
]
const BUS := &"Music"
const SILENT_DB := -60.0
const FADE_IN := 1.5
const FADE_OUT := 1.0

var player: AudioStreamPlayer
## Which cue plays now, an index into FILES.
var index := 0
## True while the page is open.
var on := false
## The music's own fade, 0 (silent) to 1.
var level := 0.0


func _ready() -> void:
	player = AudioStreamPlayer.new()
	player.bus = BUS if AudioServer.get_bus_index(BUS) >= 0 else &"Master"
	player.volume_db = SILENT_DB
	player.finished.connect(_next)
	add_child(player)


## The page opened (true) or closed (false).
func set_open(open: bool) -> void:
	on = open
	MenuMusic.held = open and AudioSettings.menu_music_on()
	if open and AudioSettings.menu_music_on() and not player.playing:
		_start(index)


func _start(i: int) -> void:
	index = posmod(i, FILES.size())
	var stream := load(FILES[index]) as AudioStream
	if stream == null:
		push_warning("credits music missing: " + FILES[index])
		return
	player.stream = stream
	player.play()


func _next() -> void:
	if on and AudioSettings.menu_music_on():
		_start(index + 1)


func _process(delta: float) -> void:
	if player == null:
		return
	var want := on and AudioSettings.menu_music_on()
	MenuMusic.held = want
	if want and not player.playing:
		_start(index)
	level = move_toward(level, 1.0 if want else 0.0, delta / (FADE_IN if want else FADE_OUT))
	player.volume_db = linear_to_db(maxf(level, 0.001)) if level > 0.001 else SILENT_DB
	if not want and level <= 0.0 and player.playing:
		player.stop()


func _exit_tree() -> void:
	MenuMusic.held = false
	if player != null:
		player.stop()
		player.stream = null
