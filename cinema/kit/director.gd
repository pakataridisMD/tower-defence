extends Node2D
## Plays a cinematic: a list of shots on one timeline, each shot building and animating its own Stage, with one
## overlay on top (flash, subtitles, title cards, letterbox) and one post pass (grade, vignette, grain, impact frames).
##
## Choose the film with the CINE environment variable (a script in res://films/, default "seven_crowns").
## T0 / T1 (seconds) render only part of it. Render with Movie Maker, see README.md.

const FPS := 30.0
const StageScript := preload("res://kit/stage.gd")

var film: Object
var edit: Array = []
var g := 0.0
var t_end := 0.0
var t_start := 0.0
var frame := 0
var frames := 0
var cur := -1
var stage: Node2D

var modulate_node: CanvasModulate
var flash_light: DirectionalLight2D
var flash_rect: ColorRect
var sub_label: Label
var card_small: Label
var card_big: Label
var post_mat: ShaderMaterial


func _ready() -> void:
	RenderingServer.set_default_clear_color(Color.BLACK)
	var name := OS.get_environment("CINE")
	if name == "":
		name = "seven_crowns"
	film = load("res://films/%s.gd" % name).new()
	edit = film.edit()
	t_end = edit[-1][1]
	if OS.get_environment("CUES_OUT") != "":
		_write_cues(OS.get_environment("CUES_OUT"))
		get_tree().quit()
		set_process(false)
		return
	if OS.get_environment("T0") != "":
		t_start = float(OS.get_environment("T0"))
	if OS.get_environment("T1") != "":
		t_end = float(OS.get_environment("T1"))
	# Frame n shows time t_start + n / FPS, for n in [0, frames). Counting whole frames keeps chunks that are
	# rendered separately exactly back to back, so the joined film stays in sync with the music.
	frames = maxi(1, roundi((t_end - t_start) * FPS))
	g = t_start

	modulate_node = CanvasModulate.new()
	add_child(modulate_node)
	flash_light = DirectionalLight2D.new()
	flash_light.color = Color(0.85, 0.8, 1.0)
	flash_light.energy = 0.0
	flash_light.height = 0.6
	flash_light.rotation_degrees = 30
	add_child(flash_light)

	var ov := CanvasLayer.new()
	ov.layer = 10
	add_child(ov)
	flash_rect = ColorRect.new()
	flash_rect.size = Vector2(1920, 1080)
	flash_rect.color = Color(1, 1, 1, 0)
	flash_rect.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ov.add_child(flash_rect)
	var font := load("res://fonts/Cinzel.ttf") as FontFile
	sub_label = _label(font, 38, Color(0.96, 0.93, 0.88), 3, 600, Color(0, 0, 0, 0.85), 10)
	# Long lines wrap onto up to three rows that sit just above the lower letterbox bar.
	sub_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	sub_label.vertical_alignment = VERTICAL_ALIGNMENT_BOTTOM
	sub_label.position = Vector2(160, 810)
	sub_label.size = Vector2(1600, 196)
	ov.add_child(sub_label)
	card_small = _label(font, 30, Color(1, 1, 1), 12, 600, Color(0, 0, 0, 0.7), 14)
	ov.add_child(card_small)
	card_big = _label(font, 104, Color(0.97, 0.95, 1.0), 18, 700, Color(0, 0, 0, 0.7), 18)
	ov.add_child(card_big)

	var post_l := CanvasLayer.new()
	post_l.layer = 20
	add_child(post_l)
	var post := ColorRect.new()
	post.size = Vector2(1920, 1080)
	post_mat = ShaderMaterial.new()
	post_mat.shader = load("res://kit/post.gdshader")
	post.material = post_mat
	post_l.add_child(post)
	for y in [0, 1020]:
		var bar := ColorRect.new()
		bar.position = Vector2(0, y)
		bar.size = Vector2(1920, 60)
		bar.color = Color.BLACK
		post_l.add_child(bar)


func _process(_delta: float) -> void:
	if frame >= frames:
		return
	g = t_start + frame / FPS
	var i := 0
	while i < edit.size() - 1 and g >= edit[i][1]:
		i += 1
	var t0: float = edit[i][0]
	var t1: float = edit[i][1]
	var shot: Callable = edit[i][2]
	if i != cur:
		if stage:
			stage.queue_free()
		stage = StageScript.new()
		add_child(stage)
		move_child(stage, 0)
		stage.T = t1 - t0
		stage.t = g - t0
		shot.call(stage, true)
		cur = i
	var st = stage
	st.t = g - t0
	st.sub_alpha = 0.0
	st.card_alpha = 0.0
	st.impact = false
	shot.call(st, false)
	st.update_rig()

	modulate_node.color = st.ambient
	flash_light.energy = st.light_flash
	flash_rect.color = Color(st.flash_color.r, st.flash_color.g, st.flash_color.b, clampf(st.flash, 0.0, 1.0))
	sub_label.text = st.sub_text
	sub_label.modulate.a = st.sub_alpha
	card_big.text = st.card_name
	card_small.text = st.card_title.to_upper()
	card_big.modulate.a = st.card_alpha
	card_small.modulate.a = st.card_alpha
	card_big.label_settings.shadow_color = Color(st.card_color.r * 0.5, st.card_color.g * 0.3, st.card_color.b * 0.5, 0.85)
	card_small.label_settings.font_color = st.card_color.lerp(Color.WHITE, 0.25)
	var cy: float = 1080.0 * st.card_y
	card_small.position = Vector2(0, cy - 48 - 8 * Stage_ease(st.card_alpha))
	card_big.position = Vector2(0, cy - 12)
	post_mat.set_shader_parameter("t", g)
	post_mat.set_shader_parameter("impact", 1.0 if st.impact else 0.0)
	post_mat.set_shader_parameter("aberr", st.aberr)
	post_mat.set_shader_parameter("fade", clampf(st.fade, 0.0, 1.0))
	frame += 1
	if frame >= frames:
		# Movie Maker still writes the frame drawn this iteration, then the tree quits before the next one.
		get_tree().quit()


## Writes the film's length and audio cues (kind, file, start seconds), one tab-separated line each, for render.sh.
func _write_cues(path: String) -> void:
	var f := FileAccess.open(path, FileAccess.WRITE)
	f.store_line("length\t\t%.4f" % t_end)
	if film.has_method("audio"):
		for c in film.audio():
			f.store_line("%s\t%s\t%.4f" % [c[0], c[1], c[2]])
	f.close()


func Stage_ease(a: float) -> float:
	return 1.0 - pow(1.0 - clampf(a, 0.0, 1.0), 3.0)


func _label(font: Font, size: int, col: Color, spacing: int, weight: int, shadow: Color, shadow_size: int) -> Label:
	var l := Label.new()
	var ls := LabelSettings.new()
	var fv := FontVariation.new()
	fv.base_font = font
	fv.spacing_glyph = spacing
	fv.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): weight}
	ls.font = fv
	ls.font_size = size
	ls.font_color = col
	ls.shadow_color = shadow
	ls.shadow_size = shadow_size
	ls.shadow_offset = Vector2.ZERO
	l.label_settings = ls
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.size = Vector2(1920, size * 1.5)
	l.modulate.a = 0.0
	return l
