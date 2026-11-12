class_name StudioSplash
extends Control
## The studio card that plays when the game opens: a black iron bomb in the dark, its fuse burning
## down, then a blast (white flash, fireball, shock wave, iron shards, sparks and smoke) out of which
## the studio's name is forged, white hot and cooling to bronze. Then the title screen.
##
## Any key or click skips it. It never plays in bot runs (--autoplay), headless runs or with
## --no-splash; those go straight to the title screen. The sound is one file cut to the same
## timeline (tools/sfx/intro.py), so the constants below and the sound's times must match.

## Emitted when the splash ends or is skipped, just before the title screen opens.
signal finished

## Set as the splash hands over, so the title screen fades in from its black.
static var fade_into_menu := false

const MENU_SCENE := "res://scenes/main.tscn"
const SOUND := "res://assets/audio/intro/studio_intro.ogg"
const TITLE_FONT := "res://assets/fonts/Cinzel.ttf"

## The timeline, in seconds.
const FADE_IN := 0.5
const FUSE_LIT := 0.55
const HIT := 2.6
const LOGO_IN := 2.95
const LOGO_COOL := 3.0  # seconds from LOGO_IN until the name has cooled
const FADE_OUT := 6.5
const LENGTH := 7.2
const SKIP_FADE := 0.45
## Clicks and keys in the first moment are ignored, so a double-click on the app icon does not skip.
const SKIP_GUARD := 0.25

const BOMB_SIZE := 540.0
## The fuse, from the bomb's neck, as a cubic curve relative to the bomb's centre.
const FUSE: Array[Vector2] = [Vector2(0, -186), Vector2(-8, -320), Vector2(150, -400), Vector2(240, -318)]

var time := 0.0
var skipping := false
## Tests set these before adding the splash: play even in a headless run, and stay put at the end.
var play_anyway := false
var leave_to_menu := true
## Where the blast is, in this control's coordinates.
var origin := Vector2.ZERO

var _leave_at := LENGTH
var _left := false
var _exploded := false
var _rng := RandomNumberGenerator.new()

var _stage: Control
var _bomb: ColorRect
var _fuse: Line2D
var _fuse_sparks: CPUParticles2D
var _spark_glow: Sprite2D
var _light: Sprite2D
var _flare: Sprite2D
var _fireball: ColorRect
var _smoke: CPUParticles2D
var _sparks: CPUParticles2D
var _debris: CPUParticles2D
var _embers: CPUParticles2D
var _logo: Control
var _name: Label
var _studio: Label
var _halos: Array[Label] = []
var _shock: ColorRect
var _flash: ColorRect
var _fade: ColorRect
var _sound: AudioStreamPlayer


## True when the splash should be skipped entirely: bot runs, headless runs, tests and --no-splash.
static func should_skip() -> bool:
	var args := OS.get_cmdline_user_args()
	return args.has("--autoplay") or args.has("--no-splash") or DisplayServer.get_name() == "headless"


func _ready() -> void:
	if should_skip() and not play_anyway:
		_go_to_menu.call_deferred()
		return
	VideoSettings.load_saved()
	_rng.seed = 7
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var view := get_viewport_rect().size
	origin = Vector2(view.x * 0.5, view.y * 0.5 + 40.0)
	_build(view)
	_sound = AudioStreamPlayer.new()
	_sound.stream = load(SOUND) if ResourceLoader.exists(SOUND) else null
	# Straight to Master: the Effects bus's compressor would flatten the blast. The master volume
	# and mute still apply.
	_sound.bus = &"Master"
	add_child(_sound)
	if _sound.stream != null and DisplayServer.get_name() != "headless":
		_sound.play()


func _input(event: InputEvent) -> void:
	if skipping or time < SKIP_GUARD:
		return
	var pressed := false
	if event is InputEventKey:
		pressed = (event as InputEventKey).pressed and not (event as InputEventKey).echo
	elif event is InputEventMouseButton:
		pressed = (event as InputEventMouseButton).pressed
	elif event is InputEventJoypadButton:
		pressed = (event as InputEventJoypadButton).pressed
	elif event is InputEventScreenTouch:
		pressed = (event as InputEventScreenTouch).pressed
	if pressed:
		get_viewport().set_input_as_handled()
		skip()


## Cuts the splash short: a quick fade to black, then the title screen.
func skip() -> void:
	if skipping or _left:
		return
	skipping = true
	_leave_at = minf(_leave_at, time + SKIP_FADE)
	var from := _fade.color.a if _fade != null else 0.0
	if _fade != null:
		create_tween().tween_property(_fade, "color:a", 1.0, SKIP_FADE * (1.0 - from))
	if _sound != null and _sound.playing:
		create_tween().tween_property(_sound, "volume_db", -40.0, SKIP_FADE)


func _process(delta: float) -> void:
	advance(delta)


## Moves the splash on by `delta` seconds (tests step it by hand).
func advance(delta: float) -> void:
	if _left or _stage == null:
		return
	time += delta
	_animate()
	if time >= _leave_at:
		_go_to_menu()


func _go_to_menu() -> void:
	if _left:
		return
	_left = true
	if _sound != null:
		_sound.stop()
	finished.emit()
	if leave_to_menu:
		fade_into_menu = true
		get_tree().change_scene_to_file(MENU_SCENE)


func _exit_tree() -> void:
	if _sound != null:
		_sound.stop()
		_sound.stream = null


# --- Building the scene ------------------------------------------------------------

func _build(view: Vector2) -> void:
	var black := ColorRect.new()
	black.color = Color(0.0, 0.0, 0.0)
	black.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(black)

	_stage = Control.new()
	_stage.size = view
	_stage.pivot_offset = origin
	_stage.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_stage)

	_light = _glow_sprite(Color(1.0, 0.55, 0.22), 2400.0)
	_light.position = origin
	_light.modulate.a = 0.0
	_stage.add_child(_light)

	_smoke = _make_smoke()
	_stage.add_child(_smoke)

	_bomb = ColorRect.new()
	_bomb.size = Vector2(BOMB_SIZE, BOMB_SIZE)
	_bomb.position = origin - _bomb.size * 0.5
	_bomb.material = _shader_material("bomb")
	_bomb.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stage.add_child(_bomb)

	_fuse = Line2D.new()
	_fuse.width = 9.0
	_fuse.default_color = Color(0.2, 0.15, 0.11)
	_fuse.joint_mode = Line2D.LINE_JOINT_ROUND
	_fuse.begin_cap_mode = Line2D.LINE_CAP_ROUND
	_fuse.end_cap_mode = Line2D.LINE_CAP_ROUND
	_stage.add_child(_fuse)

	_spark_glow = _glow_sprite(Color(1.0, 0.62, 0.25), 260.0)
	_spark_glow.modulate.a = 0.0
	_stage.add_child(_spark_glow)

	_fuse_sparks = _make_fuse_sparks()
	_stage.add_child(_fuse_sparks)

	_fireball = ColorRect.new()
	_fireball.size = Vector2(1500, 1500)
	_fireball.position = origin - _fireball.size * 0.5
	_fireball.material = _shader_material("fireball")
	_fireball.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_fireball.hide()
	_stage.add_child(_fireball)

	_flare = Sprite2D.new()
	_flare.texture = streak(256, 8)
	_flare.position = origin
	_flare.scale = Vector2(14.0, 14.0)
	_flare.modulate = Color(0.75, 0.82, 1.0, 0.0)
	_flare.material = _add_material()
	_stage.add_child(_flare)

	_debris = _make_debris()
	_stage.add_child(_debris)
	_sparks = _make_burst_sparks()
	_stage.add_child(_sparks)

	_build_logo(view)

	_embers = _make_embers(view)
	_stage.add_child(_embers)

	_shock = ColorRect.new()
	_shock.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_shock.material = _shader_material("shockwave")
	_shock.mouse_filter = Control.MOUSE_FILTER_IGNORE
	(_shock.material as ShaderMaterial).set_shader_parameter("center", origin / view)
	(_shock.material as ShaderMaterial).set_shader_parameter("aspect", view.x / view.y)
	_shock.hide()
	add_child(_shock)

	_flash = ColorRect.new()
	_flash.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_flash.color = Color(1.0, 0.93, 0.82, 0.0)
	_flash.material = _add_material()
	_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_flash)

	var vignette := ColorRect.new()
	vignette.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	vignette.material = _shader_material("vignette")
	vignette.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(vignette)

	_fade = ColorRect.new()
	_fade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_fade.color = Color(0, 0, 0, 1)
	_fade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_fade)
	_animate()


func _build_logo(view: Vector2) -> void:
	_logo = Control.new()
	_logo.size = view
	_logo.pivot_offset = origin
	_logo.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_logo.hide()
	_stage.add_child(_logo)
	var font := FontVariation.new()
	font.base_font = load(TITLE_FONT)
	font.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 900}
	font.spacing_glyph = 10
	var spaced := FontVariation.new()
	spaced.base_font = load(TITLE_FONT)
	spaced.variation_opentype = {TextServerManager.get_primary_interface().name_to_tag("wght"): 700}
	spaced.spacing_glyph = 30
	# Halos: the same word with ever wider, fainter outlines, a soft glow while the metal is hot.
	for i in 3:
		var halo := _word("PASIV", font, 230, Vector2(0, -50))
		halo.add_theme_color_override("font_color", Color(0, 0, 0, 0))
		halo.add_theme_constant_override("outline_size", 18 + i * 26)
		halo.add_theme_color_override("font_outline_color", Color(1.0, 0.45, 0.12, [0.5, 0.25, 0.12][i]))
		halo.material = _add_material()
		_halos.append(halo)
		_logo.add_child(halo)
	_name = _word("PASIV", font, 230, Vector2(0, -50))
	_name.add_theme_color_override("font_color", Color(1, 1, 1))
	_name.add_theme_constant_override("outline_size", 10)
	_name.add_theme_color_override("font_outline_color", Color(0.04, 0.03, 0.03))
	_name.material = _text_material(_name)
	_logo.add_child(_name)
	_studio = _word("PRODUCTION", spaced, 58, Vector2(0, 100))
	_studio.add_theme_color_override("font_color", Color(1, 1, 1))
	_studio.add_theme_constant_override("outline_size", 6)
	_studio.add_theme_color_override("font_outline_color", Color(0.04, 0.03, 0.03))
	_studio.material = _text_material(_studio)
	_logo.add_child(_studio)


func _word(text: String, font: Font, font_size: int, offset: Vector2) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_override("font", font)
	label.add_theme_font_size_override("font_size", font_size)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var box := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size) + Vector2(160, 60)
	label.size = box
	label.position = origin + offset - box * 0.5
	return label


func _text_material(label: Label) -> ShaderMaterial:
	var mat := _shader_material("molten_text")
	mat.set_shader_parameter("text_size", label.size)
	return mat


static func _shader_material(shader_name: String) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = load("res://scripts/ui/splash/%s.gdshader" % shader_name)
	return mat


static func _add_material() -> CanvasItemMaterial:
	var mat := CanvasItemMaterial.new()
	mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return mat


# --- Particles ---------------------------------------------------------------------

## A soft round dot, white, for glows, smoke and embers.
static func soft_dot(px: int, hardness: float = 0.0) -> ImageTexture:
	var img := Image.create(px, px, false, Image.FORMAT_RGBA8)
	var c := (px - 1) * 0.5
	for y in px:
		for x in px:
			var d := Vector2(x - c, y - c).length() / c
			var a := clampf(1.0 - d, 0.0, 1.0)
			a = lerpf(a * a * (3.0 - 2.0 * a), 1.0 if d < 0.6 else a, hardness)
			img.set_pixel(x, y, Color(1, 1, 1, a * a))
	return ImageTexture.create_from_image(img)


## A thin streak, bright in the middle, for flying sparks (aligned to their motion).
static func streak(w: int, h: int) -> ImageTexture:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		for x in w:
			var across := 1.0 - absf((x - (w - 1) * 0.5) / ((w - 1) * 0.5 + 0.001))
			var along := 1.0 - absf((y - (h - 1) * 0.5) / ((h - 1) * 0.5))
			img.set_pixel(x, y, Color(1, 1, 1, clampf(across * along * 1.6, 0.0, 1.0)))
	return ImageTexture.create_from_image(img)


## A broken shard of iron.
static func shard(seed_value: int) -> ImageTexture:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_value
	var img := Image.create(18, 12, false, Image.FORMAT_RGBA8)
	var pts := PackedVector2Array()
	for i in 5:
		var ang := TAU * i / 5.0 + rng.randf_range(-0.3, 0.3)
		pts.append(Vector2(9, 6) + Vector2(cos(ang) * rng.randf_range(5, 9), sin(ang) * rng.randf_range(3, 6)))
	for y in 12:
		for x in 18:
			if Geometry2D.is_point_in_polygon(Vector2(x, y), pts):
				var shade := 0.75 + 0.25 * float(y < 6)
				img.set_pixel(x, y, Color(shade, shade, shade, 1))
	return ImageTexture.create_from_image(img)


func _glow_sprite(color: Color, diameter: float) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = soft_dot(128)
	sprite.scale = Vector2.ONE * diameter / 128.0
	sprite.modulate = color
	sprite.material = _add_material()
	return sprite


static func _ramp(stops: Array) -> Gradient:
	var g := Gradient.new()
	g.offsets = PackedFloat32Array(stops.map(func(s: Array) -> float: return s[0]))
	g.colors = PackedColorArray(stops.map(func(s: Array) -> Color: return s[1]))
	return g


func _make_fuse_sparks() -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = 70
	p.lifetime = 0.5
	p.emitting = false
	p.texture = streak(4, 22)
	p.material = _add_material()
	p.direction = Vector2(0, -1)
	p.spread = 180.0
	p.initial_velocity_min = 80.0
	p.initial_velocity_max = 320.0
	p.gravity = Vector2(0, 520)
	p.damping_min = 40.0
	p.damping_max = 140.0
	p.particle_flag_align_y = true
	p.scale_amount_min = 0.4
	p.scale_amount_max = 1.0
	p.color_ramp = _ramp([[0.0, Color(1, 0.97, 0.85, 1)], [0.35, Color(1, 0.7, 0.25, 1)], [1.0, Color(0.9, 0.2, 0.05, 0)]])
	return p


func _make_burst_sparks() -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = 340
	p.lifetime = 2.0
	p.one_shot = true
	p.explosiveness = 0.95
	p.emitting = false
	p.position = origin
	p.texture = streak(5, 40)
	p.material = _add_material()
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 40.0
	p.direction = Vector2(0, -1)
	p.spread = 180.0
	p.initial_velocity_min = 500.0
	p.initial_velocity_max = 2100.0
	p.gravity = Vector2(0, 700)
	p.damping_min = 500.0
	p.damping_max = 1100.0
	p.particle_flag_align_y = true
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.6
	p.color_ramp = _ramp([[0.0, Color(1, 1, 0.92, 1)], [0.2, Color(1, 0.8, 0.4, 1)], [0.6, Color(1, 0.4, 0.1, 0.9)],
			[1.0, Color(0.6, 0.1, 0.02, 0)]])
	return p


func _make_debris() -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = 56
	p.lifetime = 2.6
	p.one_shot = true
	p.explosiveness = 1.0
	p.emitting = false
	p.position = origin
	p.texture = shard(11)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 70.0
	p.direction = Vector2(0, -1)
	p.spread = 180.0
	p.initial_velocity_min = 450.0
	p.initial_velocity_max = 1500.0
	p.gravity = Vector2(0, 1500)
	p.damping_min = 80.0
	p.damping_max = 260.0
	p.angle_min = -180.0
	p.angle_max = 180.0
	p.angular_velocity_min = -900.0
	p.angular_velocity_max = 900.0
	p.scale_amount_min = 0.8
	p.scale_amount_max = 3.2
	p.color_ramp = _ramp([[0.0, Color(1, 0.75, 0.4, 1)], [0.15, Color(0.9, 0.35, 0.1, 1)],
			[0.45, Color(0.16, 0.13, 0.13, 1)], [1.0, Color(0.08, 0.07, 0.07, 0)]])
	return p


func _make_smoke() -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = 70
	p.lifetime = 4.8
	p.one_shot = true
	p.explosiveness = 0.92
	p.emitting = false
	p.position = origin
	p.texture = soft_dot(128)
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	p.emission_sphere_radius = 90.0
	p.direction = Vector2(0, -1)
	p.spread = 180.0
	p.initial_velocity_min = 120.0
	p.initial_velocity_max = 620.0
	p.gravity = Vector2(0, -40)
	p.damping_min = 160.0
	p.damping_max = 340.0
	p.angle_min = -180.0
	p.angle_max = 180.0
	p.angular_velocity_min = -25.0
	p.angular_velocity_max = 25.0
	p.scale_amount_min = 2.4
	p.scale_amount_max = 4.6
	var grow := Curve.new()
	grow.add_point(Vector2(0.0, 0.45))
	grow.add_point(Vector2(0.3, 0.85))
	grow.add_point(Vector2(1.0, 1.0))
	p.scale_amount_curve = grow
	p.color_ramp = _ramp([[0.0, Color(0.55, 0.22, 0.08, 0.0)], [0.06, Color(0.4, 0.16, 0.07, 0.85)],
			[0.25, Color(0.13, 0.1, 0.1, 0.8)], [0.7, Color(0.07, 0.065, 0.07, 0.55)], [1.0, Color(0.05, 0.05, 0.05, 0)]])
	return p


func _make_embers(view: Vector2) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = 90
	p.lifetime = 4.0
	p.emitting = false
	p.position = Vector2(view.x * 0.5, view.y * 0.62)
	p.texture = soft_dot(16, 0.6)
	p.material = _add_material()
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = Vector2(view.x * 0.32, 160)
	p.direction = Vector2(0, -1)
	p.spread = 35.0
	p.initial_velocity_min = 30.0
	p.initial_velocity_max = 140.0
	p.gravity = Vector2(14, -30)
	p.scale_amount_min = 0.25
	p.scale_amount_max = 0.8
	p.color_ramp = _ramp([[0.0, Color(1, 0.6, 0.2, 0)], [0.15, Color(1, 0.55, 0.18, 0.9)], [0.7, Color(0.9, 0.3, 0.08, 0.6)],
			[1.0, Color(0.6, 0.1, 0.02, 0)]])
	return p


# --- The timeline ------------------------------------------------------------------

static func _bezier(points: Array[Vector2], t: float) -> Vector2:
	var u := 1.0 - t
	return points[0] * u * u * u + points[1] * 3.0 * u * u * t + points[2] * 3.0 * u * t * t + points[3] * t * t * t


static func _smooth(edge0: float, edge1: float, x: float) -> float:
	return smoothstep(edge0, edge1, x)


func _animate() -> void:
	var t := time
	if not skipping:
		var fade := 1.0 - _smooth(0.0, FADE_IN, t)
		fade = maxf(fade, _smooth(FADE_OUT, LENGTH, t))
		_fade.color.a = fade
	if t < HIT:
		_animate_fuse(t)
	elif not _exploded:
		_explode()
	if _exploded:
		_animate_blast(t - HIT)


func _animate_fuse(t: float) -> void:
	var burn := clampf((t - FUSE_LIT) / (HIT - 0.08 - FUSE_LIT), 0.0, 1.0)
	var tip_t := 1.0 - burn
	var points := PackedVector2Array()
	var steps := 40
	for i in steps + 1:
		var s := tip_t * i / float(steps)
		points.append(origin + _bezier(FUSE, s))
	_fuse.points = points
	var tip := origin + _bezier(FUSE, tip_t)
	var lit := t >= FUSE_LIT
	_fuse_sparks.position = tip
	_fuse_sparks.emitting = lit
	var flicker := 0.75 + 0.25 * sin(t * 53.0) * sin(t * 31.0 + 1.3) + _rng.randf_range(-0.1, 0.1)
	var flare := _smooth(FUSE_LIT, FUSE_LIT + 0.12, t) * (1.0 + 1.4 * (1.0 - _smooth(FUSE_LIT, FUSE_LIT + 0.35, t)))
	_spark_glow.position = tip
	_spark_glow.modulate.a = (0.85 * flicker * flare) if lit else 0.0
	_light.modulate.a = 0.06 * flicker * flare if lit else 0.0
	var mat := _bomb.material as ShaderMaterial
	mat.set_shader_parameter("light_pos", (tip - _bomb.position) / _bomb.size)
	mat.set_shader_parameter("light_power", (1.3 * flicker * flare) if lit else 0.0)
	mat.set_shader_parameter("heat", _smooth(HIT - 0.55, HIT, t))
	# a slow push in, and the bomb shudders as the fuse reaches it
	_stage.scale = Vector2.ONE * (1.0 + 0.07 * _smooth(0.0, HIT, t))
	var shudder := _smooth(HIT - 0.6, HIT, t) * 3.0
	_stage.position = Vector2(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1)) * shudder


func _explode() -> void:
	_exploded = true
	_bomb.hide()
	_fuse.hide()
	_fuse_sparks.emitting = false
	_spark_glow.hide()
	_fireball.show()
	_shock.show()
	for p: CPUParticles2D in [_sparks, _debris, _smoke]:
		p.restart()
		p.emitting = true
	_embers.emitting = true


func _animate_blast(dt: float) -> void:
	# the flash: two frames of white, then a warm afterglow
	_flash.color.a = 1.0 if dt < 0.05 else exp(-(dt - 0.05) * 9.0) * 0.6
	# a lens streak across the frame, as a camera sees a blast
	_flare.modulate.a = exp(-dt * 3.0) * 0.9
	_flare.scale = Vector2(14.0 + dt * 4.0, 14.0 * (0.6 + 0.4 * exp(-dt * 2.0)))
	_light.modulate.a = clampf(exp(-dt * 1.6) * 0.75, 0.0, 1.0)
	_light.scale = Vector2.ONE * (2400.0 + dt * 600.0) / 128.0
	(_fireball.material as ShaderMaterial).set_shader_parameter("progress", clampf(dt / 2.0, 0.0, 1.0))
	if dt > 2.0:
		_fireball.hide()
	var shock := _shock.material as ShaderMaterial
	shock.set_shader_parameter("radius", dt * 1.5)
	shock.set_shader_parameter("width", 0.06 + dt * 0.1)
	shock.set_shader_parameter("strength", maxf(0.0, 1.0 - dt / 0.85))
	if dt > 0.9:
		_shock.hide()
	# the camera: a hard kick that settles, and a slow drift back
	var amp := 34.0 * exp(-dt * 4.2) + 2.0 * exp(-dt * 0.9)
	_stage.position = Vector2(_rng.randf_range(-1, 1), _rng.randf_range(-1, 1)) * amp
	_stage.scale = Vector2.ONE * (1.0 + 0.02 * _smooth(0.0, 4.0, dt))
	# the studio's name, forged in the blast
	var lt := time - LOGO_IN
	if lt >= 0.0:
		_logo.show()
		var reveal := _smooth(0.0, 0.8, lt)
		var heat := 1.0 - _smooth(0.0, LOGO_COOL, lt)
		heat = heat * heat * (1.0 - 0.0) + 0.06
		for label: Label in [_name, _studio]:
			var mat := label.material as ShaderMaterial
			mat.set_shader_parameter("reveal", reveal)
			mat.set_shader_parameter("heat", heat)
		(_studio.material as ShaderMaterial).set_shader_parameter("reveal", _smooth(0.35, 1.2, lt))
		for halo in _halos:
			halo.modulate.a = reveal * clampf(heat * 1.3, 0.0, 1.0)
		_logo.scale = Vector2.ONE * (1.0 + 0.05 * (1.0 - _smooth(0.0, 1.6, lt)))
