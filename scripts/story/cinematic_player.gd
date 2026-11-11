class_name CinematicPlayer
extends Control
## Plays story cinematics full screen: each shot is a picture that drifts slowly (a pan or a zoom)
## between letterbox bars, with the narrator's line as a subtitle and her voice if it has been
## recorded. Shots fade through black. A shot with no picture yet shows a placeholder card with the
## art note, so the story can be reviewed before its art exists.
##
## Space, Enter or a click moves to the next shot; Esc skips the whole cinematic.
##
## As a scene (scenes/story/cinematic.tscn) it plays Progress.cinematic_queue and then opens
## Progress.cinematic_next_scene. Tests and tools can also add it by hand: set `queue`, then listen
## for `finished`.

signal shot_started(cinematic_id: StringName, index: int)
signal finished

const FADE := 0.6
## Pause after a voice line ends before the next shot.
const VOICE_TAIL := 0.8
const TITLE_TIME := 3.2
const MUSIC_DB := -10.0
## How far the music drops under a voice line, and how long it takes to fade out at the end.
const MUSIC_DUCK_DB := 7.0
const MUSIC_FADE := 1.5
const BAR_HEIGHT := 110.0
## How far a picture drifts over a shot: it is drawn this much larger than the screen.
const DRIFT := 0.08
const MOTIONS: Array[String] = ["in", "right", "out", "left", "up"]

## Cinematics still to play, first one next.
var queue: Array[StringName] = []
## Open Progress.cinematic_next_scene when done. Off when added by hand.
var change_scene_when_done := true
## Marks each cinematic as seen in the player's progress.
var mark_seen := true
var story: Story

var _cinematic: Dictionary = {}
var _shot := -1
## -1 while the title card shows.
var _time := 0.0
var _length := 0.0
var _fade_out := -1.0
var _texture: Texture2D
var _voice: AudioStreamPlayer
var _music: AudioStreamPlayer
var _font: Font
var _bold: Font
var _done := false
var _skipping := false
## Shot start times in the music, when the music was written shot by shot.
var _markers := PackedFloat32Array()


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_font = ThemeDB.fallback_font
	var bold := SystemFont.new()
	bold.font_weight = 700
	bold.fallbacks = [_font]
	_bold = bold
	_voice = AudioStreamPlayer.new()
	add_child(_voice)
	_music = AudioStreamPlayer.new()
	_music.volume_db = MUSIC_DB
	add_child(_music)
	if story == null:
		story = Story.shared()
	if queue.is_empty() and change_scene_when_done:
		queue = Progress.cinematic_queue.duplicate()
		Progress.cinematic_queue.clear()
	_next_cinematic()


func _process(delta: float) -> void:
	if _done:
		return
	_time += delta
	var music_target := MUSIC_DB - (MUSIC_DUCK_DB if _voice.playing else 0.0)
	_music.volume_db = move_toward(_music.volume_db, music_target, delta * MUSIC_DUCK_DB * 3.0)
	if _fade_out >= 0.0:
		_fade_out += delta
		if _fade_out >= FADE:
			_fade_out = -1.0
			_advance()
	elif _shot_over():
		_fade_out = 0.0
	queue_redraw()


## The cinematic playing now, its shot (-1 on the title card) and the shot's data.
func current_id() -> StringName:
	return _cinematic.get("id", &"")


func current_shot() -> int:
	return _shot


func is_done() -> bool:
	return _done


## Moves on: to the next shot, or the next cinematic after the last one.
func next_shot() -> void:
	if _done:
		return
	if _fade_out < 0.0:
		_fade_out = 0.0


## Skips what is left of this cinematic.
func skip_cinematic() -> void:
	if _done:
		return
	_voice.stop()
	# Stay on the shot showing now while it fades out; the next step moves past the last shot.
	_shot = maxi(_shot, _shots().size() - 1) if _shot >= 0 else _shot
	_skipping = true
	_fade_out = 0.0


func _gui_input(event: InputEvent) -> void:
	var click := event as InputEventMouseButton
	if click != null and click.pressed and click.button_index == MOUSE_BUTTON_LEFT:
		next_shot()
		accept_event()


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_SPACE, KEY_ENTER, KEY_KP_ENTER, KEY_RIGHT:
			next_shot()
		KEY_ESCAPE:
			skip_cinematic()
		_:
			return
	get_viewport().set_input_as_handled()


## A shot ends after its length, or, when the music was written shot by shot, so that the next
## shot fades in right on its marker.
func _shot_over() -> bool:
	var next := _shot + 1
	if not _markers.is_empty() and _shot >= 0 and next < _markers.size() and _music.playing:
		return _music.get_playback_position() >= _markers[next] - FADE
	return _time >= _length


func _shots() -> Array:
	return _cinematic.get("shots", [])


func _next_cinematic() -> void:
	_cinematic = {}
	while not queue.is_empty() and _cinematic.is_empty():
		var id: StringName = queue.pop_front()
		_cinematic = story.cinematic(id)
	if _cinematic.is_empty():
		_finish()
		return
	if mark_seen and is_inside_tree() and get_node_or_null("/root/Progress") != null:
		Progress.mark_seen(_cinematic["id"])
	var path := story.music_for(_cinematic["id"])
	_markers = story.shot_markers(_cinematic["id"])
	var stream: AudioStream = load(path) if not path.is_empty() else null
	# Cinematics that share a cue (several in a row) keep it playing instead of starting it over.
	if stream == null or stream != _music.stream or not _music.playing:
		_music.stop()
		_music.volume_db = MUSIC_DB
		_music.stream = stream
		if stream != null:
			_music.play()
	_shot = -1
	_time = 0.0
	_length = TITLE_TIME if not str(_cinematic.get("title", "")).is_empty() else 0.01
	shot_started.emit(_cinematic["id"], -1)


func _advance() -> void:
	_voice.stop()
	_shot = _shots().size() if _skipping else _shot + 1
	_skipping = false
	var shots := _shots()
	if _shot >= shots.size():
		_next_cinematic()
		return
	var shot: Dictionary = shots[_shot]
	_time = 0.0
	_texture = load(shot["image"]) if ResourceLoader.exists(shot["image"]) else null
	_length = float(shot["duration"])
	if not str(shot["voice"]).is_empty() and ResourceLoader.exists(shot["voice"]):
		var stream: AudioStream = load(shot["voice"])
		_voice.stream = stream
		_voice.play()
		_length = stream.get_length() + VOICE_TAIL + FADE
	shot_started.emit(_cinematic["id"], _shot)


func _finish() -> void:
	_done = true
	finished.emit()
	if _music.playing and is_inside_tree():
		# The music fades out over a moment rather than cutting off.
		var tween := create_tween()
		tween.tween_property(_music, "volume_db", -60.0, MUSIC_FADE)
		tween.tween_callback(_music.stop)
		if change_scene_when_done:
			await tween.finished
	else:
		_music.stop()
	if change_scene_when_done and is_inside_tree():
		var next := Progress.cinematic_next_scene
		Progress.cinematic_next_scene = ""
		get_tree().change_scene_to_file(next if not next.is_empty() else "res://scenes/main.tscn")


# --- Drawing ---------------------------------------------------------------------

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, size), Color.BLACK)
	if _done or _cinematic.is_empty():
		return
	var fade_in := clampf(_time / FADE, 0.0, 1.0)
	var fade_out := 1.0 - clampf(_fade_out / FADE, 0.0, 1.0) if _fade_out >= 0.0 else 1.0
	var alpha := minf(fade_in, fade_out)
	if _shot < 0 or _shot >= _shots().size():
		if _shot < 0:
			_draw_title(alpha)
		return
	var shot: Dictionary = _shots()[_shot]
	var frame := Rect2(0, BAR_HEIGHT, size.x, size.y - BAR_HEIGHT * 2.0)
	if _texture != null:
		_draw_picture(frame, shot, alpha)
	else:
		_draw_placeholder(frame, shot, alpha)
	# Letterbox bars, then the subtitle on the lower one.
	draw_rect(Rect2(0, 0, size.x, BAR_HEIGHT), Color.BLACK)
	draw_rect(Rect2(0, size.y - BAR_HEIGHT, size.x, BAR_HEIGHT), Color.BLACK)
	_draw_subtitle(shot, alpha)
	var hint := "Space: next    Esc: skip"
	draw_string(_font, Vector2(size.x - 260, 40), hint, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(1, 1, 1, 0.35))
	var count := "%d / %d" % [_shot + 1, _shots().size()]
	draw_string(_font, Vector2(40, 40), count, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(1, 1, 1, 0.35))


func _draw_title(alpha: float) -> void:
	var title := str(_cinematic.get("title", ""))
	var subtitle := str(_cinematic.get("subtitle", ""))
	var gold := Color(UiStyle.GOLD, alpha)
	var width := _bold.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, 64).x
	draw_string(_bold, Vector2((size.x - width) * 0.5, size.y * 0.5), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 64, gold)
	var line := minf(width, 600.0) * clampf(_time / 1.2, 0.0, 1.0)
	draw_line(Vector2((size.x - line) * 0.5, size.y * 0.5 + 24), Vector2((size.x + line) * 0.5, size.y * 0.5 + 24), Color(gold, alpha * 0.6), 2.0)
	if not subtitle.is_empty():
		var sub_width := _font.get_string_size(subtitle, HORIZONTAL_ALIGNMENT_LEFT, -1, 26).x
		draw_string(_font, Vector2((size.x - sub_width) * 0.5, size.y * 0.5 + 72), subtitle, HORIZONTAL_ALIGNMENT_LEFT, -1, 26, Color(UiStyle.TEXT_DIM, alpha))


## The picture fills the frame and drifts: a slow zoom in or out, or a pan, picked per shot.
func _draw_picture(frame: Rect2, shot: Dictionary, alpha: float) -> void:
	var t := clampf(_time / maxf(_length, 0.1), 0.0, 1.0)
	t = t * t * (3.0 - 2.0 * t)
	var cover := maxf(frame.size.x / _texture.get_width(), frame.size.y / _texture.get_height())
	var motion := str(shot.get("motion", ""))
	if motion.is_empty():
		motion = MOTIONS[_shot % MOTIONS.size()]
	var zoom := 1.0 + DRIFT
	var shift := Vector2.ZERO
	match motion:
		"in":
			zoom = 1.0 + DRIFT * t
		"out":
			zoom = 1.0 + DRIFT * (1.0 - t)
		"right":
			shift.x = lerpf(-1.0, 1.0, t)
		"left":
			shift.x = lerpf(1.0, -1.0, t)
		"up":
			shift.y = lerpf(1.0, -1.0, t)
		_:
			zoom = 1.0
	var drawn := _texture.get_size() * cover * zoom
	var spare := drawn - frame.size
	var top_left := frame.position - spare * 0.5 + spare * 0.5 * shift
	draw_texture_rect(_texture, Rect2(top_left, drawn), false, Color(1, 1, 1, alpha))


## A stand-in for a picture that has not been drawn: a tinted card with the art note.
func _draw_placeholder(frame: Rect2, shot: Dictionary, alpha: float) -> void:
	var tint := Color(str(shot.get("tint", ""))) if Color.html_is_valid(str(shot.get("tint", ""))) else Color("3a2a5a")
	var steps := 24
	for i in steps:
		var band := Rect2(frame.position.x, frame.position.y + frame.size.y * i / steps, frame.size.x, frame.size.y / steps + 1.0)
		var shade := tint.darkened(0.55 + 0.35 * float(i) / steps)
		draw_rect(band, Color(shade, alpha))
	# Slow embers rising, so the card is not dead still.
	for k in 40:
		var seed := float(k) * 37.7
		var x := fposmod(seed * 13.1 + sin(_time * 0.3 + seed) * 20.0, frame.size.x)
		var y := frame.end.y - fposmod(_time * (12.0 + fmod(seed, 17.0)) + seed * 7.0, frame.size.y)
		draw_rect(Rect2(x, y, 3, 3), Color(tint.lightened(0.6), 0.35 * alpha))
	var note := str(shot.get("art_note", ""))
	var box := Rect2(frame.position + Vector2(frame.size.x * 0.18, frame.size.y * 0.22), Vector2(frame.size.x * 0.64, frame.size.y * 0.5))
	draw_rect(box, Color(0, 0, 0, 0.35 * alpha))
	_draw_dashed_rect(box, Color(1, 1, 1, 0.3 * alpha))
	draw_string(_font, box.position + Vector2(24, 40), "PICTURE TO COME", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(UiStyle.GOLD, 0.7 * alpha))
	if not note.is_empty():
		draw_multiline_string(_font, box.position + Vector2(24, 84), note, HORIZONTAL_ALIGNMENT_LEFT, box.size.x - 48, 24, -1, Color(1, 1, 1, 0.75 * alpha))


func _draw_dashed_rect(box: Rect2, color: Color) -> void:
	var corners := [box.position, Vector2(box.end.x, box.position.y), box.end, Vector2(box.position.x, box.end.y)]
	for i in 4:
		draw_dashed_line(corners[i], corners[(i + 1) % 4], color, 2.0, 12.0)


## The narration, typed out over the first part of the shot, with the speaker's name above it.
func _draw_subtitle(shot: Dictionary, alpha: float) -> void:
	var text := str(shot.get("text", "")).replace("\n\n", " ")
	if text.is_empty():
		return
	var reveal := clampf((_time - 0.3) / maxf(1.0, _length * 0.55), 0.0, 1.0)
	var shown := text.substr(0, ceili(text.length() * reveal))
	var speaker := str(shot.get("speaker", ""))
	var width := minf(size.x - 240.0, 1400.0)
	var left := (size.x - width) * 0.5
	var top := size.y - BAR_HEIGHT - 150.0
	# A soft shade behind the text so it reads over any picture.
	draw_rect(Rect2(0, top - 30.0, size.x, 180.0), Color(0, 0, 0, 0.45 * alpha))
	if not speaker.is_empty():
		draw_string(_bold, Vector2(left, top), speaker.to_upper(), HORIZONTAL_ALIGNMENT_LEFT, -1, 18, Color(UiStyle.GOLD, alpha))
	draw_multiline_string(_font, Vector2(left, top + 38.0), shown, HORIZONTAL_ALIGNMENT_LEFT, width, 30, 3, Color(1, 1, 1, alpha))
