extends RefCounted
## Any game cutscene, built from its story data: data/story/cinematics/<SCENE>.json for the lines, speakers and
## lengths, assets/story/images/<SCENE>/<NN>.png (or a split still in art/stills/<SCENE>_<NN>/) for the picture,
## assets/story/voice/<SCENE>/<NN>.ogg for each line and the scene's music cue.
##
## Every shot gets a slow camera move, depth (parallax when the still is split into layers), drifting dust or embers
## in the scene's element, low fog, and the line as a subtitle. A scene can stage any shot by hand in
## films/scenes/<SCENE>.gd with `func shot_<NN>(st, init, info)`; it then replaces the default for that shot.
##
## SCENE picks the cutscene. STORY_ROOT points at the checkout that holds data/ and assets/ (default: the repo this
## cinema folder lives in), so a scene can be rendered from another branch's story and voices.

const PAD := 0.6          # seconds after a line before the cut
const TAIL := 1.6         # extra hold on the last shot while the picture fades
const ELEMENT := {
	"ember": "fire", "storm": "storm", "nature": "nature", "water": "water", "earth": "earth", "void": "void",
}
const MOTE := {
	"fire": Color(1.0, 0.55, 0.22), "storm": Color(0.75, 0.82, 1.0), "nature": Color(0.6, 1.0, 0.45),
	"water": Color(0.45, 0.85, 1.0), "earth": Color(0.95, 0.8, 0.55), "void": Color(0.75, 0.45, 1.0),
	"": Color(0.95, 0.88, 0.75),
}

var id := ""
var root := ""
var title := ""
var element := ""
var shots: Array = []     # {t0, t1, text, speaker, image, still, voice, voice_len}
var music := ""
var custom: Object = null
var _textures := {}


func _init() -> void:
	id = OS.get_environment("SCENE")
	assert(id != "", "Set SCENE to a cinematic id, e.g. SCENE=earth_herald")
	root = OS.get_environment("STORY_ROOT")
	if root == "":
		root = ProjectSettings.globalize_path("res://").path_join("..").simplify_path()
	var data: Dictionary = _json("data/story/cinematics/%s.json" % id)
	title = str(data.get("title", ""))
	element = ELEMENT.get(id.get_slice("_", 0), "")
	music = _music_path(data)
	var markers := _markers(data.get("shots", []).size())
	var t := 0.0
	var list: Array = data.get("shots", [])
	for i in list.size():
		var s: Dictionary = list[i]
		var nn := "%02d" % (i + 1)
		var voice := root.path_join("assets/story/voice/%s/%s.ogg" % [id, nn])
		var voice_len := 0.0
		if FileAccess.file_exists(voice):
			var ogg := AudioStreamOggVorbis.load_from_file(voice)
			voice_len = ogg.get_length() if ogg else 0.0
		else:
			voice = ""
		var len := maxf(float(s.get("duration", 4.0)), voice_len + PAD)
		if not markers.is_empty():
			# The music was written shot by shot: cut on its markers, but never before the line has finished.
			var next: float = markers[i + 1] if i + 1 < markers.size() else t + len
			len = maxf(next - t, voice_len + PAD)
		if i == list.size() - 1:
			len += TAIL
		shots.append({
			"t0": t, "t1": t + len, "text": str(s.get("text", "")), "speaker": str(s.get("speaker", "")),
			"image": root.path_join("assets/story/images/%s/%s.png" % [id, nn]),
			"still": "%s_%s" % [id, nn], "voice": voice, "voice_len": voice_len, "index": i,
		})
		t += len
	var custom_path := "res://films/scenes/%s.gd" % id
	if ResourceLoader.exists(custom_path):
		custom = load(custom_path).new()


func edit() -> Array:
	var out := []
	for s in shots:
		out.append([s["t0"], s["t1"], _shot.bind(s)])
	return out


## Audio cues for render.sh: the music from 0 and each line at its shot's start (+ a small lead-in).
func audio() -> Array:
	var out := []
	if music != "":
		out.append(["music", music, 0.0])
	for s in shots:
		if s["voice"] != "":
			out.append(["voice", s["voice"], s["t0"] + _lead(s)])
	return out


func _lead(s: Dictionary) -> float:
	return 0.5 if s["index"] == 0 else 0.25


# ---------------------------------------------------------------- the default shot
func _shot(st, init: bool, s: Dictionary) -> void:
	var fn := "shot_%02d" % (s["index"] + 1)
	if custom and custom.has_method(fn):
		custom.call(fn, st, init, s)
	else:
		_default(st, init, s)
	# Subtitle, fades and title are shared by every shot.
	var a0 := _lead(s)
	var a1: float = minf(a0 + maxf(s["voice_len"] - 0.4, 2.5), st.T - 0.15)
	if s["text"] != "":
		st.subtitle(s["text"], a0, a1)
	if s["index"] == 0:
		st.fade = maxf(st.fade, 1.0 - st.ease_out(st.t / 1.0))
		if title != "":
			st.card(title, "", MOTE[element], 0.6, minf(3.6, st.T - 0.5), 0.42)
	if s["t1"] == shots[-1]["t1"]:
		st.fade = maxf(st.fade, st.seg(st.t, st.T - TAIL, st.T - 0.1))


func _default(st, init: bool, s: Dictionary) -> void:
	var i: int = s["index"]
	if init:
		var base := DirAccess.dir_exists_absolute(ProjectSettings.globalize_path("res://art/stills/%s" % s["still"]))
		if base:
			var n := 0
			while ResourceLoader.exists("res://art/stills/%s/%d.png" % [s["still"], n]):
				n += 1
			var ps := []
			for j in n:
				ps.append(lerpf(0.55, 1.2, float(j) / maxf(n - 1, 1)))
			st.still(s["still"], ps)
		else:
			var tex := _texture(s["image"])
			if tex:
				var n: Node2D = st.layer(1.0)
				var sp := Sprite2D.new()
				sp.texture = tex
				sp.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
				sp.material = st._flat_mat()
				sp.scale = Vector2(1.12, 1.12)
				n.add_child(sp)
		# Atmosphere in front of the picture: low fog and motes in the scene's element.
		var front: Node2D = st.layer(1.25)
		st.fog(front, Rect2(-420, 40, 840, 200), 0.32, Color(0.55, 0.5, 0.6) if element != "fire" else Color(0.6, 0.4, 0.3), 3.0, 6.0)
		var col: Color = MOTE[element]
		var up := element in ["fire", "void"]
		st.drift(front, Rect2(-400, -200, 800, 400), 70, Color(col.r, col.g, col.b, 0.7),
				6.0, Vector2(8, -14) if up else Vector2(10, 4), 1.1, true, 40.0)
		# One of four slow moves, so consecutive shots never repeat.
		st.v["move"] = i % 4
		st.v["seed"] = float(i) * 1.7
	var u: float = st.ease_io(st.t / st.T)
	match int(st.v["move"]):
		0:  # push in
			st.k = lerpf(1.0, 1.09, u)
			st.cam = Vector2(0, lerpf(0, -6, u))
		1:  # pan right
			st.k = 1.05
			st.cam = Vector2(lerpf(-18, 18, u), 0)
		2:  # pull out
			st.k = lerpf(1.1, 1.02, u)
			st.cam = Vector2(lerpf(6, 0, u), lerpf(4, 0, u))
		3:  # drift left and down
			st.k = lerpf(1.04, 1.07, u)
			st.cam = Vector2(lerpf(16, -14, u), lerpf(-5, 3, u))
	st.cam += Vector2(sin(st.t * 0.7 + st.v["seed"]), cos(st.t * 0.5 + st.v["seed"])) * 1.2
	var breathe := 0.94 + 0.04 * sin(st.t * 0.8 + st.v["seed"])
	st.ambient = Color(breathe, breathe, breathe * 1.02)


# ---------------------------------------------------------------- files
func _texture(path: String) -> Texture2D:
	if not _textures.has(path):
		var img := Image.load_from_file(path) if FileAccess.file_exists(path) else null
		_textures[path] = ImageTexture.create_from_image(img) if img else null
	return _textures[path]


func _json(rel: String) -> Variant:
	return JSON.parse_string(FileAccess.get_file_as_string(root.path_join(rel)))


func _music_path(data: Dictionary) -> String:
	var cue := str(data.get("music", ""))
	if cue == "":
		var cues: Variant = _json("assets/story/music/cinematic_music.json")
		if cues is Dictionary:
			cue = str(cues.get("cinematics", {}).get(id, ""))
	if cue == "":
		return ""
	if cue.begins_with("res://"):
		cue = cue.get_file().get_basename()
	var path := root.path_join("assets/story/music/%s.ogg" % cue)
	return path if FileAccess.file_exists(path) else ""


func _markers(n_shots: int) -> Array:
	if music == "":
		return []
	var info: Variant = _json("assets/story/music/%s.json" % music.get_file().get_basename())
	if not info is Dictionary or not info.get("markers") is Array:
		return []
	var out := []
	for m in info["markers"]:
		if m is Dictionary and m.has("time"):
			out.append(float(m["time"]))
	return out if out.size() == n_shots else []
