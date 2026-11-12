extends Node2D
## One shot's stage: a parallax camera rig over depth layers, plus builders for plates, actors, lights, fog,
## particles, bolts and glows. A shot function builds its stage once (init) and then animates it every frame.
##
## World units: the 640x360 still space. At zoom k = 1 one unit is 3 screen pixels (1920x1080).
## A layer with parallax p moves p times as far as the focal plane (p = 1) when the camera moves or zooms.

const S := 3.0
const CENTER := Vector2(960, 540)
const RINGC := [Color8(255, 122, 58), Color8(200, 216, 255), Color8(138, 240, 80), Color8(74, 224, 224),
		Color8(232, 176, 64), Color8(176, 112, 255)]
const EL := {"fire": Color(1.0, 0.5, 0.2), "storm": Color(0.7, 0.8, 1.0), "nature": Color(0.5, 1.0, 0.35),
		"water": Color(0.3, 0.75, 1.0), "earth": Color(0.95, 0.7, 0.35), "void": Color(0.7, 0.4, 1.0)}

# Camera, read by the director every frame.
var cam := Vector2.ZERO
var k := 1.0
var shake_amount := 0.0
# Look, read by the director every frame.
var ambient := Color(1, 1, 1)
var flash := 0.0
var flash_color := Color(1, 0.96, 1)
var impact := false
var aberr := 0.3
var fade := 0.0
var sub_text := ""
var sub_alpha := 0.0
var card_name := ""
var card_title := ""
var card_alpha := 0.0
var card_color := Color(1, 0.8, 0.5)
var card_y := 0.72
var light_flash := 0.0

var t := 0.0
var T := 1.0
var v := {}                         # per-shot state
var layers := []                    # [node, parallax]
var fog_mats := []
var sky_mats := []

static var _anim: Dictionary = {}
static var _tex: Dictionary = {}
var _pixel: Shader = preload("res://kit/pixel.gdshader")
var _pixel_flat: Shader = preload("res://kit/pixel_flat.gdshader")
var _shake_seed := 0.0


func _init() -> void:
	if _anim.is_empty():
		_anim = JSON.parse_string(FileAccess.get_file_as_string("res://art/anim/anim.json"))
	_shake_seed = randf() * 100.0


# ---------------------------------------------------------------- rig
func layer(p: float) -> Node2D:
	var n := Node2D.new()
	add_child(n)
	layers.append([n, p])
	return n


func update_rig() -> void:
	var sh := Vector2(sin(t * 63.0 + _shake_seed) + sin(t * 41.0) * 0.6, cos(t * 57.0) + sin(t * 37.0 + _shake_seed) * 0.5) * shake_amount
	for l in layers:
		var n: Node2D = l[0]
		var p: float = l[1]
		var sc := S * (1.0 + (k - 1.0) * maxf(p, 0.0))
		n.scale = Vector2(sc, sc)
		n.position = CENTER + sh * p - cam * p * sc
	for m in fog_mats:
		m.set_shader_parameter("t", t)
	for m in sky_mats:
		m.set_shader_parameter("t", t)


# ---------------------------------------------------------------- painted stills
## Loads the depth layers of a split still (cinema/art/stills/<id>/) onto layers with the given parallax values.
## Returns the layer nodes. A plate is overscanned slightly so camera moves never show an edge.
func still(id: String, ps: Array, over := 1.1) -> Array:
	var out := []
	for i in ps.size():
		var path := "res://art/stills/%s/%d.png" % [id, i]
		if not ResourceLoader.exists(path):
			break
		var n := layer(ps[i])
		var s := Sprite2D.new()
		s.texture = load(path)
		s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
		s.material = _flat_mat()
		s.scale = Vector2(over, over)
		n.add_child(s)
		out.append(n)
	return out


func plate(path: String, p: float, sc := 1.0) -> Sprite2D:
	var n := layer(p)
	var s := Sprite2D.new()
	s.texture = load(path)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	s.material = _flat_mat()
	s.scale = Vector2(sc, sc)
	n.add_child(s)
	return s


func _flat_mat() -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = _pixel_flat
	return m


# ---------------------------------------------------------------- actors
func _canvas_tex(path: String) -> CanvasTexture:
	if not _tex.has(path):
		var ct := CanvasTexture.new()
		ct.diffuse_texture = load(path + ".png")
		if ResourceLoader.exists(path + "_n.png"):
			ct.normal_texture = load(path + "_n.png")
		_tex[path] = ct
	return _tex[path]


## A lit, animated creature from art/anim with its feet at (x, y). Scale 2 matches the stills' pixel size.
func actor(parent: Node, name: String, anim: String, x: float, y: float, sc := 2.0, flip := false) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	var m := ShaderMaterial.new()
	m.shader = _pixel
	s.material = m
	s.set_meta("name", name)
	s.position = Vector2(x, y)
	s.scale = Vector2(sc, sc)
	s.flip_h = flip
	parent.add_child(s)
	pose(s, anim, 0.0)
	return s


## Shows frame `time` of an animation (loops unless loop is false, then holds the last frame).
func pose(s: Sprite2D, anim: String, time: float, loop := true) -> void:
	var name: String = s.get_meta("name")
	var meta: Dictionary = _anim[name]
	var a: Dictionary = meta["anims"][anim]
	var n := int(a["frames"])
	if s.get_meta("anim", "") != anim:
		s.texture = _canvas_tex("res://art/anim/%s_%s" % [name, anim])
		s.hframes = n
		s.set_meta("anim", anim)
		var fw: float = meta["frame"][0]
		var fh: float = meta["frame"][1]
		var fx: float = meta["feet"][0]
		var fy: float = meta["feet"][1]
		s.offset = Vector2((fx - fw / 2.0) if s.flip_h else (fw / 2.0 - fx), fh / 2.0 - fy)
	var f := int(floor(maxf(time, 0.0) * float(a["fps"])))
	s.frame = (f % n) if loop else mini(f, n - 1)


## A still figure from art/people (story characters and heroes), feet at (x, y).
func person(parent: Node, name: String, x: float, y: float, sc := 2.0, flip := false) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = _canvas_tex("res://art/people/" + name)
	s.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	var m := ShaderMaterial.new()
	m.shader = _pixel
	s.material = m
	s.flip_h = flip
	s.position = Vector2(x, y)
	s.scale = Vector2(sc, sc)
	s.offset = Vector2(0, -s.texture.get_height() / 2.0 + 4)
	parent.add_child(s)
	return s


# ---------------------------------------------------------------- light and air
func light(parent: Node, pos: Vector2, col: Color, energy: float, sc: float, height := 30.0) -> PointLight2D:
	var l := PointLight2D.new()
	l.texture = radial(Color(1, 1, 1, 1), Color(1, 1, 1, 0), 0.45)
	l.position = pos
	l.color = col
	l.energy = energy
	l.texture_scale = sc
	l.height = height
	parent.add_child(l)
	return l


var _radial_cache := {}
func radial(c0: Color, c1: Color, mid_a := 0.4) -> GradientTexture2D:
	var key := "%s%s%s" % [c0, c1, mid_a]
	if _radial_cache.has(key):
		return _radial_cache[key]
	var g := GradientTexture2D.new()
	g.width = 256
	g.height = 256
	g.fill = GradientTexture2D.FILL_RADIAL
	g.fill_from = Vector2(0.5, 0.5)
	g.fill_to = Vector2(1.0, 0.5)
	var gr := Gradient.new()
	gr.set_color(0, c0)
	gr.set_color(1, c1)
	gr.add_point(0.35, Color(c0.r, c0.g, c0.b, c0.a * mid_a))
	g.gradient = gr
	_radial_cache[key] = g
	return g


## An additive soft glow (bloom-like halo) of `size` world units across.
func glow(parent: Node, pos: Vector2, col: Color, size: float, alpha := 0.8, squash := 1.0) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = radial(Color(1, 1, 1, 1), Color(1, 1, 1, 0), 0.35)
	s.material = add_mat()
	s.position = pos
	s.modulate = Color(col.r, col.g, col.b, alpha)
	s.scale = Vector2(size / 256.0, size * squash / 256.0)
	parent.add_child(s)
	return s


func fog(parent: Node, r: Rect2, dens: float, tint: Color, sc := 3.0, speed := 8.0) -> ColorRect:
	var c := ColorRect.new()
	c.position = r.position
	c.size = r.size
	var m := ShaderMaterial.new()
	m.shader = preload("res://kit/fog.gdshader")
	m.set_shader_parameter("density", dens)
	m.set_shader_parameter("tint", tint)
	m.set_shader_parameter("scale", sc)
	m.set_shader_parameter("speed", speed)
	c.material = m
	fog_mats.append(m)
	parent.add_child(c)
	return c


func sky(parent: Node, top: Color, mid: Color, low: Color, glow_pos := Vector2(0.47, 0.25), glow_col := Color(0.3, 0.16, 0.55)) -> ColorRect:
	var c := ColorRect.new()
	c.position = Vector2(-460, -280)
	c.size = Vector2(920, 460)
	var m := ShaderMaterial.new()
	m.shader = preload("res://kit/sky.gdshader")
	m.set_shader_parameter("top", top)
	m.set_shader_parameter("mid", mid)
	m.set_shader_parameter("low", low)
	m.set_shader_parameter("glow_pos", glow_pos)
	m.set_shader_parameter("glow_col", glow_col)
	c.material = m
	sky_mats.append(m)
	parent.add_child(c)
	return c


## A ridge line (mountains, hills) filled down to y = 400.
func ridge(parent: Node, x0: float, x1: float, base: float, amp: float, col: Color, seed: float, flat := true) -> Polygon2D:
	var p := PackedVector2Array()
	p.append(Vector2(x0, 400))
	var n := 72
	for i in n + 1:
		var x: float = lerp(x0, x1, float(i) / n)
		var y: float = base - amp * (0.55 * absf(sin(x * 0.011 + seed)) + 0.3 * absf(sin(x * 0.027 + seed * 2.0)) + 0.15 * sin(x * 0.09 + seed))
		p.append(Vector2(x, y))
	p.append(Vector2(x1, 400))
	var poly := Polygon2D.new()
	poly.polygon = p
	poly.color = col
	if flat:
		poly.material = unshaded()
	parent.add_child(poly)
	return poly


func rect_poly(parent: Node, r: Rect2, col: Color, flat := false) -> Polygon2D:
	var poly := Polygon2D.new()
	poly.polygon = PackedVector2Array([r.position, Vector2(r.end.x, r.position.y), r.end, Vector2(r.position.x, r.end.y)])
	poly.color = col
	if flat:
		poly.material = unshaded()
	parent.add_child(poly)
	return poly


# ---------------------------------------------------------------- particles
## Drifting particles (embers, ash, motes, snow) inside rect r, already in flight on the first frame.
func drift(parent: Node, r: Rect2, amount: int, col: Color, life: float, vel: Vector2, size: float, additive := true, spread := 25.0) -> CPUParticles2D:
	var e := CPUParticles2D.new()
	e.position = r.get_center()
	e.amount = amount
	e.lifetime = life
	e.preprocess = life
	e.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	e.emission_rect_extents = r.size / 2
	e.direction = vel.normalized() if vel.length() > 0 else Vector2(0, -1)
	e.spread = spread
	e.gravity = Vector2.ZERO
	e.initial_velocity_min = vel.length() * 0.5
	e.initial_velocity_max = vel.length() * 1.3
	e.scale_amount_min = size * 0.6
	e.scale_amount_max = size * 1.4
	e.color_ramp = ramp(col, Color(col.r, col.g * 0.6, col.b, 0.0))
	e.material = add_mat() if additive else unshaded()
	parent.add_child(e)
	return e


## A one-shot burst (debris, sparks, magic); call .restart() to fire it.
func burst(parent: Node, pos: Vector2, col: Color, n := 60, speed := 120.0, grav := 90.0, life := 1.2, size := 2.0, additive := true) -> CPUParticles2D:
	var b := CPUParticles2D.new()
	b.position = pos
	b.amount = n
	b.one_shot = true
	b.explosiveness = 0.9
	b.lifetime = life
	b.emitting = false
	b.direction = Vector2(0, -1)
	b.spread = 70
	b.initial_velocity_min = speed * 0.3
	b.initial_velocity_max = speed
	b.gravity = Vector2(0, grav)
	b.damping_min = 5
	b.damping_max = 20
	b.scale_amount_min = size * 0.5
	b.scale_amount_max = size * 1.5
	b.color_ramp = ramp(col, Color(col.r, col.g, col.b, 0))
	b.material = add_mat() if additive else unshaded()
	parent.add_child(b)
	return b


func fire(b: CPUParticles2D) -> void:
	if not b.has_meta("fired"):
		b.set_meta("fired", true)
		b.restart()
		b.emitting = true


func ramp(a: Color, b: Color) -> Gradient:
	var g := Gradient.new()
	g.set_color(0, a)
	g.set_color(1, b)
	return g


# ---------------------------------------------------------------- lines
func line(parent: Node, pts: PackedVector2Array, col: Color, width: float, additive := true) -> Line2D:
	var l := Line2D.new()
	l.points = pts
	l.width = width
	l.default_color = col
	l.joint_mode = Line2D.LINE_JOINT_ROUND
	l.material = add_mat() if additive else unshaded()
	parent.add_child(l)
	return l


## A jagged lightning path from a to b, the same for the same seed.
func bolt_points(a: Vector2, b: Vector2, seed: int, jag := 10.0, steps := 9) -> PackedVector2Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed
	var p := PackedVector2Array()
	for i in steps + 1:
		var u := float(i) / steps
		var q := a.lerp(b, u)
		if i > 0 and i < steps:
			var nrm := (b - a).orthogonal().normalized()
			q += nrm * rng.randf_range(-jag, jag)
		p.append(q)
	return p


# ---------------------------------------------------------------- materials and easing
func unshaded() -> CanvasItemMaterial:
	var m := CanvasItemMaterial.new()
	m.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	return m


func add_mat() -> CanvasItemMaterial:
	var m := unshaded()
	m.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD
	return m


static func ease_io(a: float) -> float:
	a = clampf(a, 0.0, 1.0)
	return a * a * (3.0 - 2.0 * a)


static func ease_out(a: float) -> float:
	return 1.0 - pow(1.0 - clampf(a, 0.0, 1.0), 3.0)


## 0 -> 1 between a and b.
static func seg(x: float, a: float, b: float) -> float:
	return clampf((x - a) / maxf(b - a, 1e-4), 0.0, 1.0)


## Fades in over `fi` from a0, out over `fo` before a1.
static func window(x: float, a0: float, a1: float, fi := 0.3, fo := 0.3) -> float:
	return ease_io((x - a0) / fi) * ease_io((a1 - x) / fo)


func subtitle(text: String, a0: float, a1: float) -> void:
	sub_text = text
	sub_alpha = window(t, a0, a1)


func card(name: String, title: String, col: Color, a0: float, a1: float, y := 0.72) -> void:
	card_name = name
	card_title = title
	card_color = col
	card_y = y
	card_alpha = window(t, a0, a1, 0.4, 0.3)
