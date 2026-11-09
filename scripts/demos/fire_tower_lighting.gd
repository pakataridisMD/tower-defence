class_name FireTowerLighting
extends Control
## Art test: one Fire tower on a patch of field, lit the way Graveyard Keeper-style games are lit.
##
## Everything is pixel art drawn at 640x360 and scaled up 3x. Each sprite has a normal map, so the
## sun, the brazier, the arrow slit and every fireball shade it as they move. On top of that:
## an ambient tint that runs through day, dusk, night and dawn, fake projected shadows that turn away
## from the strongest light, grass that sways and bends when slimes walk through it, fire and smoke
## particles, mist and fireflies at night.
##
## Keys: 1 day, 2 dusk, 3 night, 4 dawn (each stops the clock), Space runs or stops the clock,
## Esc goes back to the menu.
## Command line (after `--`): --shots=<folder> saves day, dusk and night screenshots and quits.
## --clip starts at dusk with a fast clock, for recording with Godot's --write-movie.

const ART := "res://assets/art/lighting_demo/"
const MENU_SCENE := "res://scenes/main.tscn"
const ART_SIZE := Vector2i(640, 360)
const PIXEL_SCALE := 3

## Seconds for a whole day when the clock runs.
const DAY_LENGTH := 48.0
const DAY := 0.08
const DUSK := 0.3
const NIGHT := 0.55
const DAWN := 0.9

## Where shadows fall in sunlight (away from a low sun in the lower left).
const SUN_SHADOW_DIR := Vector2(0.8, -0.6)
const FIRE_COLOR := Color(1.0, 0.6, 0.28)
const TOWER_RANGE := 150.0
const SHOT_INTERVAL := 1.1
const FIREBALL_SPEED := 190.0
const SLIME_SPEED := 20.0
const SLIME_HP := 3

var time_of_day := DUSK
var clock_running := false
var clock_speed := 1.0

var _viewport: SubViewport
var _world: Node2D
var _props: Node2D
var _shadow_layer: Node2D
var _air: Node2D
var _ambient: CanvasModulate
var _sun: DirectionalLight2D
var _fire_light: PointLight2D
var _slit_light: PointLight2D
var _mist: ColorRect
var _fireflies: CPUParticles2D
var _hud: Label

var _ambient_gradient: Gradient
var _night_gradient: Gradient
var _noise := FastNoiseLite.new()
var _pixel: ImageTexture
var _light_texture: GradientTexture2D
var _blob_texture: GradientTexture2D
var _sway_shader: Shader

var _road := Curve2D.new()
var _tower_base := Vector2.ZERO
var _fire_pos := Vector2.ZERO
var _casters: Array[Caster] = []
var _tufts: Array[Sprite2D] = []
var _slimes: Array[Slime] = []
var _slime_frames: Array[CanvasTexture] = []
var _slime_albedo: Texture2D
var _shot_timer := 0.5
var _spawn_timer := 0.0
var _elapsed := 0.0


## Something that casts the two fake shadows: one from the sun and one from the brazier.
class Caster:
	var node: Node2D
	var sun_shadow: Sprite2D
	var fire_shadow: Sprite2D
	var height := 1.0


class Slime:
	var sprite: Sprite2D
	var caster: Caster
	var distance := 0.0
	var hp := SLIME_HP
	var flash := 0.0
	var frame_time := 0.0


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_noise.frequency = 2.2
	_build_resources()
	_build_viewport()
	var layout := _load_layout()
	_build_ground()
	_build_lights()
	_build_road(layout)
	_build_tower(layout)
	_build_props(layout)
	_build_atmosphere()
	_build_hud()
	for i in 4:
		_spawn_slime(i * 34.0)
	_apply_time()
	var args := OS.get_cmdline_user_args()
	for arg in args:
		if arg.begins_with("--shots="):
			_take_shots(arg.trim_prefix("--shots="))
		elif arg == "--clip":
			time_of_day = DUSK - 0.04
			clock_running = true
			clock_speed = 1.0


# ------------------------------------------------------------------ setup

func _build_resources() -> void:
	var img := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	img.fill(Color.WHITE)
	_pixel = ImageTexture.create_from_image(img)

	_light_texture = _radial_texture(256, [Color(1, 1, 1, 1), Color(1, 1, 1, 0.55), Color(1, 1, 1, 0)], [0.0, 0.35, 1.0])
	_blob_texture = _radial_texture(32, [Color(0, 0, 0, 0.55), Color(0, 0, 0, 0)], [0.45, 1.0])

	_ambient_gradient = _ramp(
			[Color(0.86, 0.86, 0.84), Color(0.88, 0.84, 0.78), Color(0.9, 0.64, 0.55), Color(0.42, 0.38, 0.6),
			Color(0.2, 0.23, 0.4), Color(0.2, 0.23, 0.4), Color(0.62, 0.6, 0.78), Color(0.86, 0.86, 0.84)],
			[0.0, 0.2, 0.3, 0.4, 0.5, 0.8, 0.9, 1.0])
	# How much of the night look applies (0 day, 1 night), stored in the red channel.
	_night_gradient = _ramp(
			[Color(0, 0, 0), Color(0, 0, 0), Color(0.85, 0, 0), Color(1, 0, 0), Color(1, 0, 0), Color(0, 0, 0), Color(0, 0, 0)],
			[0.0, 0.24, 0.42, 0.5, 0.82, 0.95, 1.0])

	_sway_shader = Shader.new()
	_sway_shader.code = """
shader_type canvas_item;
// Sways the top of a sprite while its base stays planted. push bends it away from a passer-by.
uniform float strength = 1.2;
uniform float speed = 1.7;
uniform float push = 0.0;
void vertex() {
	float top = 1.0 - UV.y;
	vec2 world = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	float t = TIME * speed + world.x * 0.045 + world.y * 0.03;
	VERTEX.x += (sin(t) + 0.35 * sin(t * 2.7)) * strength * top + push * top;
}
"""


func _radial_texture(size: int, colors: Array, offsets: Array) -> GradientTexture2D:
	var gradient := Gradient.new()
	gradient.colors = PackedColorArray(colors)
	gradient.offsets = PackedFloat32Array(offsets)
	var tex := GradientTexture2D.new()
	tex.gradient = gradient
	tex.fill = GradientTexture2D.FILL_RADIAL
	tex.fill_from = Vector2(0.5, 0.5)
	tex.fill_to = Vector2(1.0, 0.5)
	tex.width = size
	tex.height = size
	return tex


func _build_viewport() -> void:
	var container := SubViewportContainer.new()
	container.stretch = true
	container.stretch_shrink = PIXEL_SCALE
	container.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	add_child(container)
	container.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_viewport = SubViewport.new()
	_viewport.size = ART_SIZE
	_viewport.canvas_item_default_texture_filter = Viewport.DEFAULT_CANVAS_ITEM_TEXTURE_FILTER_NEAREST
	_viewport.snap_2d_transforms_to_pixel = true
	container.add_child(_viewport)
	_world = Node2D.new()
	_viewport.add_child(_world)
	_ambient = CanvasModulate.new()
	_world.add_child(_ambient)


func _load_layout() -> Dictionary:
	var text := FileAccess.get_file_as_string(ART + "layout.json")
	var parsed: Variant = JSON.parse_string(text)
	if parsed is Dictionary:
		return parsed
	push_error("Lighting demo: could not read layout.json")
	return {}


func _canvas_texture(name: String) -> CanvasTexture:
	var tex := CanvasTexture.new()
	tex.diffuse_texture = load(ART + name + ".png")
	tex.normal_texture = load(ART + name + "_n.png")
	return tex


func _build_ground() -> void:
	var ground := Sprite2D.new()
	ground.texture = _canvas_texture("ground")
	ground.centered = false
	_world.add_child(ground)
	_shadow_layer = Node2D.new()
	_shadow_layer.z_index = 1
	_world.add_child(_shadow_layer)
	_props = Node2D.new()
	_props.y_sort_enabled = true
	_props.z_index = 2
	_world.add_child(_props)
	_air = Node2D.new()
	_air.z_index = 4
	_world.add_child(_air)


func _build_lights() -> void:
	_sun = DirectionalLight2D.new()
	_sun.color = Color(1.0, 0.93, 0.8)
	_sun.height = 0.55
	# A directional light shines along its local +Y; turn that to travel the way shadows fall.
	_sun.rotation = atan2(-SUN_SHADOW_DIR.x, SUN_SHADOW_DIR.y)
	_sun.blend_mode = Light2D.BLEND_MODE_ADD
	_world.add_child(_sun)


func _build_road(layout: Dictionary) -> void:
	for p: Array in layout.get("road", []):
		_road.add_point(Vector2(p[0], p[1]))


func _build_tower(layout: Dictionary) -> void:
	var info: Dictionary = layout.get("tower", {})
	var pos: Array = info.get("pos", [320, 220])
	var size: Array = info.get("size", [48, 92])
	var fire: Array = info.get("fire", [0, -78])
	var slit: Array = info.get("slit", [0, -34])
	var base_offset: float = info.get("base_offset", 6)
	_tower_base = Vector2(pos[0], pos[1])

	var tower := Node2D.new()
	tower.position = _tower_base
	_props.add_child(tower)
	var body := Sprite2D.new()
	body.texture = _canvas_texture("tower")
	body.centered = false
	body.offset = Vector2(-float(size[0]) / 2.0, -float(size[1]) + base_offset)
	tower.add_child(body)
	var glow := Sprite2D.new()
	glow.texture = load(ART + "tower_glow.png")
	glow.centered = false
	glow.offset = body.offset
	glow.material = _unshaded_material(false)
	tower.add_child(glow)
	_add_caster(tower, load(ART + "tower.png"), body.offset, 1.0, false)

	_fire_pos = _tower_base + Vector2(fire[0], fire[1] + base_offset)
	_fire_light = _point_light(FIRE_COLOR, 1.5, 1.15, 46.0)
	_fire_light.position = _fire_pos + Vector2(0, 6)
	_world.add_child(_fire_light)
	_slit_light = _point_light(Color(1.0, 0.55, 0.25), 0.7, 0.2, 8.0)
	_slit_light.position = _tower_base + Vector2(slit[0], slit[1] + base_offset + 8)
	_world.add_child(_slit_light)

	# Flames (additive, unshaded), then smoke (lit, so it glows orange near the fire).
	var flames := _particles(46, 0.55, Vector2(5, 1.5))
	flames.direction = Vector2(0, -1)
	flames.spread = 14.0
	flames.gravity = Vector2(0, -38)
	flames.initial_velocity_min = 6.0
	flames.initial_velocity_max = 18.0
	flames.scale_amount_min = 1.0
	flames.scale_amount_max = 3.0
	flames.color_ramp = _ramp([Color(1, 0.98, 0.75), Color(1, 0.75, 0.25), Color(0.95, 0.3, 0.08), Color(0.5, 0.08, 0.05, 0)], [0.0, 0.25, 0.65, 1.0])
	flames.material = _unshaded_material(true)
	flames.position = _fire_pos
	_air.add_child(flames)
	var embers := _particles(8, 1.8, Vector2(5, 1))
	embers.direction = Vector2(0, -1)
	embers.spread = 35.0
	embers.gravity = Vector2(6, -14)
	embers.initial_velocity_min = 10.0
	embers.initial_velocity_max = 24.0
	embers.color_ramp = _ramp([Color(1, 0.85, 0.4), Color(1, 0.4, 0.1, 0)], [0.0, 1.0])
	embers.material = _unshaded_material(true)
	embers.position = _fire_pos
	_air.add_child(embers)
	var smoke := _particles(18, 2.6, Vector2(3, 1))
	smoke.direction = Vector2(0.2, -1)
	smoke.spread = 10.0
	smoke.gravity = Vector2(5, -6)
	smoke.initial_velocity_min = 10.0
	smoke.initial_velocity_max = 16.0
	smoke.scale_amount_min = 2.0
	smoke.scale_amount_max = 4.0
	smoke.color_ramp = _ramp([Color(0.35, 0.33, 0.33, 0.0), Color(0.4, 0.38, 0.38, 0.45), Color(0.5, 0.5, 0.52, 0)], [0.0, 0.2, 1.0])
	smoke.position = _fire_pos + Vector2(0, -6)
	_air.add_child(smoke)


func _build_props(layout: Dictionary) -> void:
	for prop: Dictionary in layout.get("props", []):
		var kind: String = prop["kind"]
		var p: Array = prop["pos"]
		var albedo: Texture2D = load(ART + kind + ".png")
		var sprite := Sprite2D.new()
		sprite.texture = _canvas_texture(kind)
		sprite.centered = false
		sprite.flip_h = prop.get("flip", false)
		sprite.offset = Vector2(-albedo.get_width() / 2.0, -albedo.get_height() + 1)
		sprite.position = Vector2(p[0], p[1])
		var sways := kind.begins_with("tuft") or kind.begins_with("bush")
		if sways:
			var mat := ShaderMaterial.new()
			mat.shader = _sway_shader
			mat.set_shader_parameter("strength", 1.3 if kind.begins_with("tuft") else 0.45)
			sprite.material = mat
			if kind.begins_with("tuft"):
				_tufts.append(sprite)
		_props.add_child(sprite)
		var height := 0.5 if kind.begins_with("tuft") else 1.0
		_add_caster(sprite, albedo, sprite.offset, height, sprite.flip_h)


func _build_atmosphere() -> void:
	var noise := FastNoiseLite.new()
	noise.frequency = 0.012
	noise.fractal_octaves = 3
	var noise_tex := NoiseTexture2D.new()
	noise_tex.width = 256
	noise_tex.height = 256
	noise_tex.seamless = true
	noise_tex.noise = noise
	var shader := Shader.new()
	shader.code = """
shader_type canvas_item;
// Two layers of drifting noise make a low mist. amount fades it in at night.
uniform sampler2D noise : repeat_enable, filter_nearest;
uniform float amount = 0.0;
uniform vec4 tint : source_color = vec4(0.75, 0.82, 1.0, 1.0);
void fragment() {
	vec2 uv = UV * vec2(2.5, 1.4);
	float a = texture(noise, uv + vec2(TIME * 0.008, 0.0)).r;
	float b = texture(noise, uv * 1.7 + vec2(-TIME * 0.013, TIME * 0.004)).r;
	float m = smoothstep(0.55, 0.9, a * 0.6 + b * 0.5);
	COLOR = vec4(tint.rgb, m * amount);
}
"""
	var mat := ShaderMaterial.new()
	mat.shader = shader
	mat.set_shader_parameter("noise", noise_tex)
	_mist = ColorRect.new()
	_mist.size = Vector2(ART_SIZE)
	_mist.material = mat
	_mist.z_index = 3
	_mist.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_world.add_child(_mist)

	_fireflies = _particles(26, 5.0, Vector2(ART_SIZE) / 2.0)
	_fireflies.position = Vector2(ART_SIZE) / 2.0
	_fireflies.direction = Vector2(1, 0)
	_fireflies.spread = 180.0
	_fireflies.gravity = Vector2.ZERO
	_fireflies.initial_velocity_min = 2.0
	_fireflies.initial_velocity_max = 7.0
	_fireflies.color_ramp = _ramp([Color(0.8, 1, 0.4, 0), Color(0.85, 1, 0.45, 1), Color(0.8, 1, 0.4, 0)], [0.0, 0.5, 1.0])
	_fireflies.material = _unshaded_material(true)
	_air.add_child(_fireflies)

	for f in 4:
		_slime_frames.append(_canvas_texture("slime_%d" % f))
	_slime_albedo = load(ART + "slime_0.png")


func _build_hud() -> void:
	_hud = Label.new()
	_hud.add_theme_font_size_override("font_size", 22)
	_hud.add_theme_color_override("font_color", Color(0.93, 0.9, 0.84))
	_hud.add_theme_color_override("font_outline_color", Color(0.05, 0.05, 0.08))
	_hud.add_theme_constant_override("outline_size", 6)
	_hud.position = Vector2(28, 1080 - 64)
	add_child(_hud)


# ------------------------------------------------------------------ helpers

func _point_light(color: Color, energy: float, scale: float, height: float) -> PointLight2D:
	var light := PointLight2D.new()
	light.texture = _light_texture
	light.color = color
	light.energy = energy
	light.texture_scale = scale
	light.height = height
	light.blend_mode = Light2D.BLEND_MODE_ADD
	return light


func _particles(amount: int, lifetime: float, extents: Vector2) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = amount
	p.lifetime = lifetime
	p.texture = _pixel
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = extents
	p.local_coords = false
	return p


func _ramp(colors: Array, offsets: Array) -> Gradient:
	var g := Gradient.new()
	g.colors = PackedColorArray(colors)
	g.offsets = PackedFloat32Array(offsets)
	return g


func _unshaded_material(additive: bool) -> CanvasItemMaterial:
	var mat := CanvasItemMaterial.new()
	mat.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	if additive:
		mat.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return mat


func _add_caster(node: Node2D, albedo: Texture2D, offset: Vector2, height: float, flip: bool) -> Caster:
	var caster := Caster.new()
	caster.node = node
	caster.height = height
	var blob := Sprite2D.new()
	blob.texture = _blob_texture
	var width := absf(offset.x) * 2.0
	blob.scale = Vector2(width * 1.1, width * 0.45) / 32.0
	blob.position = node.position
	_shadow_layer.add_child(blob)
	for i in 2:
		var shadow := Sprite2D.new()
		shadow.texture = albedo
		shadow.centered = false
		shadow.offset = offset
		shadow.flip_h = flip
		shadow.modulate = Color(0, 0, 0, 0)
		shadow.position = node.position
		_shadow_layer.add_child(shadow)
		if i == 0:
			caster.sun_shadow = shadow
		else:
			caster.fire_shadow = shadow
	node.set_meta("blob", blob)
	_casters.append(caster)
	return caster


func _spawn_slime(start_distance: float) -> void:
	var slime := Slime.new()
	slime.distance = start_distance
	slime.frame_time = randf() * 2.0
	slime.sprite = Sprite2D.new()
	slime.sprite.texture = _slime_frames[0]
	slime.sprite.centered = false
	slime.sprite.offset = Vector2(-_slime_albedo.get_width() / 2.0, -_slime_albedo.get_height() + 1)
	_props.add_child(slime.sprite)
	slime.caster = _add_caster(slime.sprite, _slime_albedo, slime.sprite.offset, 0.8, false)
	_slimes.append(slime)
	_place_slime(slime)


func _place_slime(slime: Slime) -> void:
	var length := _road.get_baked_length()
	if length <= 0.0:
		return
	slime.sprite.position = _road.sample_baked(fmod(slime.distance, length)).round()


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	_elapsed += delta
	if clock_running:
		time_of_day = fmod(time_of_day + delta * clock_speed / DAY_LENGTH, 1.0)
	_apply_time()
	_flicker()
	_update_slimes(delta)
	_update_tower(delta)
	_update_shadows()
	_update_grass()


func _night() -> float:
	return _night_gradient.sample(time_of_day).r


func _apply_time() -> void:
	var night := _night()
	_ambient.color = _ambient_gradient.sample(time_of_day)
	_sun.energy = (1.0 - night) * 0.45
	_sun.color = Color(1.0, 0.93, 0.8).lerp(Color(1.0, 0.62, 0.42), clampf((time_of_day - 0.18) / 0.14, 0.0, 1.0) * (1.0 - night))
	(_mist.material as ShaderMaterial).set_shader_parameter("amount", night * 0.16)
	_fireflies.modulate = Color(1, 1, 1, night)
	var phase := "Day"
	if time_of_day >= 0.22 and time_of_day < 0.42:
		phase = "Dusk"
	elif time_of_day >= 0.42 and time_of_day < 0.85:
		phase = "Night"
	elif time_of_day >= 0.85:
		phase = "Dawn"
	_hud.text = "Fire tower lighting test  ·  %s%s  ·  1 Day  2 Dusk  3 Night  4 Dawn  ·  Space: %s the clock  ·  Esc: menu" % [
		phase, "" if clock_running else " (clock stopped)", "stop" if clock_running else "run"]


func _flicker() -> void:
	var n := _noise.get_noise_1d(_elapsed * 9.0)
	var n2 := _noise.get_noise_1d(_elapsed * 23.0 + 100.0)
	var boost := 0.55 + _night() * 0.45
	_fire_light.energy = (1.45 + n * 0.35 + n2 * 0.15) * boost
	_fire_light.texture_scale = 1.15 + n * 0.05
	_fire_light.position = _fire_pos + Vector2(n2 * 1.2, 6.0 + n * 0.8)
	_slit_light.energy = (0.7 + n2 * 0.2) * boost


func _update_slimes(delta: float) -> void:
	var length := _road.get_baked_length()
	for slime in _slimes:
		slime.distance += SLIME_SPEED * delta
		if slime.distance > length:
			slime.distance -= length
			slime.hp = SLIME_HP
		slime.frame_time += delta
		slime.sprite.texture = _slime_frames[int(slime.frame_time * 7.0) % 4]
		slime.flash = maxf(0.0, slime.flash - delta * 5.0)
		slime.sprite.modulate = Color(1, 1, 1).lerp(Color(3.0, 2.2, 1.6), slime.flash)
		_place_slime(slime)


func _update_tower(delta: float) -> void:
	_shot_timer -= delta
	if _shot_timer > 0.0:
		return
	var target: Slime = null
	var best := TOWER_RANGE
	for slime in _slimes:
		var d := slime.sprite.position.distance_to(_tower_base)
		if d < best and slime.hp > 0:
			best = d
			target = slime
	if target == null:
		_shot_timer = 0.2
		return
	_shot_timer = SHOT_INTERVAL
	_fire_at(target)


func _fire_at(target: Slime) -> void:
	var ball := Node2D.new()
	ball.position = _fire_pos + Vector2(0, -3)
	_air.add_child(ball)
	var core := Sprite2D.new()
	core.texture = _pixel
	core.scale = Vector2(3, 3)
	core.modulate = Color(1, 0.95, 0.7)
	core.material = _unshaded_material(true)
	ball.add_child(core)
	var trail := _particles(24, 0.35, Vector2(1, 1))
	trail.gravity = Vector2(0, -12)
	trail.initial_velocity_max = 4.0
	trail.scale_amount_min = 1.0
	trail.scale_amount_max = 2.0
	trail.color_ramp = _ramp([Color(1, 0.9, 0.5), Color(1, 0.4, 0.1), Color(0.6, 0.1, 0.05, 0)], [0.0, 0.4, 1.0])
	trail.material = _unshaded_material(true)
	ball.add_child(trail)
	var light := _point_light(FIRE_COLOR, 1.1, 0.32, 18.0)
	ball.add_child(light)

	var flight := func(step: float) -> void:
		if not is_instance_valid(ball):
			return
		var goal := target.sprite.position + Vector2(0, -5)
		ball.position = ball.position.move_toward(goal, FIREBALL_SPEED * step)
	var tween := create_tween()
	var duration := ball.position.distance_to(target.sprite.position) / FIREBALL_SPEED + 0.05
	tween.tween_method(func(_v: float) -> void: flight.call(get_process_delta_time()), 0.0, 1.0, duration)
	tween.tween_callback(func() -> void: _explode(ball, target))


func _explode(ball: Node2D, target: Slime) -> void:
	var at := ball.position
	ball.queue_free()
	target.hp -= 1
	target.flash = 1.0
	var burst := _particles(30, 0.45, Vector2(1, 1))
	burst.one_shot = true
	burst.explosiveness = 1.0
	burst.spread = 180.0
	burst.gravity = Vector2(0, 30)
	burst.initial_velocity_min = 18.0
	burst.initial_velocity_max = 46.0
	burst.scale_amount_max = 2.0
	burst.color_ramp = _ramp([Color(1, 0.95, 0.6), Color(1, 0.45, 0.1), Color(0.4, 0.1, 0.05, 0)], [0.0, 0.4, 1.0])
	burst.material = _unshaded_material(true)
	burst.position = at
	_air.add_child(burst)
	burst.emitting = true
	var flash := _point_light(FIRE_COLOR, 2.2, 0.55, 14.0)
	flash.position = at
	_world.add_child(flash)
	var tween := create_tween()
	tween.tween_property(flash, "energy", 0.0, 0.35)
	tween.tween_callback(flash.queue_free)
	get_tree().create_timer(1.0).timeout.connect(burst.queue_free)
	if target.hp <= 0:
		# Back to the start of the road, so the field never empties.
		target.hp = SLIME_HP
		target.distance = 0.0


func _update_shadows() -> void:
	var night := _night()
	var fire_strength := clampf(_fire_light.energy / 1.5, 0.0, 1.3)
	for caster in _casters:
		var pos := caster.node.position
		var blob: Sprite2D = caster.node.get_meta("blob")
		blob.position = pos
		# Sun: a long, flattened silhouette pointing to the upper right.
		var sun := caster.sun_shadow
		sun.position = pos
		sun.rotation = atan2(SUN_SHADOW_DIR.x, -SUN_SHADOW_DIR.y)
		sun.scale = Vector2(1.0, 0.62)
		sun.modulate = Color(0, 0, 0, 0.32 * (1.0 - night))
		# Fire: points away from the tower, stretches with distance and fades out of reach.
		var fire := caster.fire_shadow
		var away := pos - _tower_base
		var dist := away.length()
		if dist < 6.0:
			fire.modulate = Color(0, 0, 0, 0)
			continue
		var dir := away / dist
		fire.position = pos
		fire.rotation = atan2(dir.x, -dir.y)
		fire.scale = Vector2(1.0, clampf(dist / 70.0, 0.35, 1.5) * caster.height)
		var reach := clampf(1.0 - dist / 190.0, 0.0, 1.0)
		fire.modulate = Color(0, 0, 0, 0.6 * reach * fire_strength * (0.35 + night * 0.65))


func _update_grass() -> void:
	for tuft in _tufts:
		var push := 0.0
		for slime in _slimes:
			var d := tuft.position - slime.sprite.position
			if absf(d.y) < 8.0 and absf(d.x) < 12.0:
				push += signf(d.x) * (1.0 - absf(d.x) / 12.0) * 3.0
		(tuft.material as ShaderMaterial).set_shader_parameter("push", push)


# ------------------------------------------------------------------ input and capture

func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	match key.keycode:
		KEY_1:
			_jump(DAY)
		KEY_2:
			_jump(DUSK)
		KEY_3:
			_jump(NIGHT)
		KEY_4:
			_jump(DAWN)
		KEY_SPACE:
			clock_running = not clock_running
			clock_speed = 1.0
		KEY_ESCAPE:
			get_tree().change_scene_to_file(MENU_SCENE)
		_:
			return
	get_viewport().set_input_as_handled()


func _jump(t: float) -> void:
	time_of_day = t
	clock_running = false


func _take_shots(folder: String) -> void:
	DirAccess.make_dir_recursive_absolute(folder)
	await get_tree().create_timer(2.5).timeout
	for entry: Array in [["day", DAY], ["dusk", DUSK], ["night", NIGHT]]:
		_jump(entry[1])
		await get_tree().create_timer(1.6).timeout
		await RenderingServer.frame_post_draw
		var path := folder.path_join("lighting_%s.png" % entry[0])
		get_viewport().get_texture().get_image().save_png(path)
		print("Saved ", path)
	get_tree().quit()
