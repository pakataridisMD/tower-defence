class_name BoardArt
extends Node2D
## Draws a run as lit pixel art: the map's ground, props in the grass, towers, enemies, shots and
## impacts. Every sprite has a normal map, so the sun and the towers' own lights shade it. The light
## over the board follows the run (see DayNight), so the last waves are fought at night by the light
## of the towers.
##
## It only reads the simulation; BoardView keeps the input, the overlays and the placeholder shapes
## used for anything that has no art. Art comes from tools/art/gen_game_art.py.

const ART := "res://assets/art/game/"
## Screen pixels per art pixel.
const SCALE := 2.0
## Where a tower's base sits in its cell, in art pixels below the cell centre.
const TOWER_BASE_DROP := 8.0
## Shadows fall this way in sunlight (away from a low sun in the lower left).
const SUN_SHADOW_DIR := Vector2(0.8, -0.6)
## Enemies stand this far below the road's centre line (in art pixels), so they look centred on it.
const ENEMY_DROP := 4.0
## Art pixels across one board cell (64 screen pixels at SCALE 2).
const CELL_ART := 32.0
## How tall the major bosses stand, in board cells, as the story art draws them (a hero is about
## 1.5 cells). They are centred on their road and drawn over the cells around it.
const BOSS_CELLS := {
	&"saltmother": 3.25, &"gorrath": 3.25, &"pale_vesper": 3.25, &"ashwick": 3.25, &"vholt": 3.5,
	&"mother_briar": 3.25, &"ashen_regent": 3.4,
	&"cinder_tyrant": 5.0, &"thunderhead": 5.0, &"broodmother": 5.0, &"mountain_titan": 5.0,
	&"hollow_king": 5.0, &"leviathan": 6.3, &"sundered_heart": 5.0,
	&"gatemaw": 8.0, &"vael_orrun": 9.0,
}
## Short-lived lights (shots, blasts, lightning) allowed at once, to keep lighting cheap.
const MAX_FLASH_LIGHTS := 10
## Rings and sprays of sparks allowed at once.
const MAX_FX := 90
## The element a tower's shots are made of, from what its crown gives off (its emitter in art.json).
const SHOT_STYLES := {
	"fire": &"fire", "sparks": &"storm", "plasma": &"storm", "leaves": &"nature", "bubbles": &"nature",
	"drips": &"water", "steam": &"water", "dust": &"earth", "void": &"void", "soulfire": &"void",
}

static var _info: Dictionary = {}
static var _texture_cache: Dictionary = {}

var sim: RunSim
var day_night := DayNight.new()
## Above 0, holds the light at this time of day whatever the waves, such as DayNight.NIGHT for the
## Long Night or DayNight.DAWN once the dawn comes in the siege of Solenne.
var light_override := -1.0

var _world: Node2D
var _ground: Node2D
var _shadows: Node2D
var _actors: Node2D
var _air: Node2D
var _ambient: CanvasModulate
var _sun: DirectionalLight2D
var _fireflies: CPUParticles2D
## Glowing cracks and glints in the ground, brighter at night.
var _ground_glow: Node2D
## The map's biome tints the light and the motes in the air.
var _biome: StringName = &"meadow"

var _pixel: ImageTexture
var _light_texture: GradientTexture2D
var _blob_texture: GradientTexture2D
var _sway_material: ShaderMaterial
var _unshaded: CanvasItemMaterial
var _additive: CanvasItemMaterial

var _towers: Dictionary[int, TowerVisual] = {}
var _enemies: Dictionary[int, EnemyVisual] = {}
var _shots: Dictionary[SimProjectile, Node2D] = {}
var _props_by_cell: Dictionary[Vector2i, Array] = {}
var _casters: Array[Caster] = []
var _flash_lights := 0
var _elapsed := 0.0
var _noise := FastNoiseLite.new()
var _tower_count := -1
## Drawn on the ground under the towers: aura rings and the runes that circle an ascended tower.
var _ground_fx: Node2D
## Drawn over everything: what is hurting each enemy, and the rings and sparks of hits.
var _marks: Node2D
var _fx: Array[Fx] = []


## Something with a contact shadow and a sun shadow that follows it.
class Caster:
	var node: Node2D
	var flip_from: Sprite2D
	var blob: Sprite2D
	var sun: Sprite2D
	var height := 1.0
	## How much larger than its art the thing is drawn (big bosses).
	var size_scale := 1.0


## A short effect drawn straight onto the board: a ring that spreads (or closes in), or a spray of sparks.
class Fx:
	var ring := true
	var at := Vector2.ZERO
	var color := Color.WHITE
	var age := 0.0
	var life := 0.3
	var from := 2.0
	var to := 12.0
	var count := 5
	var salt := 0
	var width := 1.0


class TowerVisual:
	var tower: SimTower
	## The tower type this visual was drawn for; a tower that changes into a hybrid is redrawn.
	var data_id: StringName
	var root: Node2D
	var glow: Sprite2D
	var light: PointLight2D
	var light_energy := 1.0
	var pulse := 0.0
	var caster: Caster
	var muzzle := Vector2.ZERO
	## One colour per element of the tower.
	var colors: Array[Color] = []
	var shot_style: StringName
	## The level and ascension this visual last showed, to mark the moment they change.
	var level := 1
	var ascended := false


class EnemyVisual:
	var enemy: SimEnemy
	var root: Node2D
	var body: Sprite2D
	var gear: Sprite2D
	var gear_glow: Sprite2D
	var frames: Array[CanvasTexture] = []
	var gear_frames: Array[CanvasTexture] = []
	var glow_frames: Array[Texture2D] = []
	var caster: Caster
	var last_health := 0.0
	var flash := 0.0
	var time := 0.0
	var last_x := 0.0
	var tint := Color.WHITE
	## The sprite's size in art pixels, as drawn.
	var size := Vector2.ZERO
	var size_scale := 1.0


# ------------------------------------------------------------------ setup

## True when the art for this map exists, so the board can be drawn with it.
static func has_ground(map_id: StringName) -> bool:
	return ResourceLoader.exists(ART + "ground/%s.png" % map_id)


static func info() -> Dictionary:
	if _info.is_empty() and FileAccess.file_exists(ART + "art.json"):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART + "art.json"))
		if parsed is Dictionary:
			_info = parsed
	return _info


static func tower_info(tower_id: StringName) -> Dictionary:
	return (info().get("towers", {}) as Dictionary).get(String(tower_id), {})


static func enemy_info(enemy_id: StringName) -> Dictionary:
	return (info().get("enemies", {}) as Dictionary).get(String(enemy_id), {})


## The tower's plain picture (no normal map), for menus and the placement preview. Null if it has no art.
static func tower_picture(tower_id: StringName) -> Texture2D:
	if tower_info(tower_id).is_empty():
		return null
	return load(ART + "towers/%s.png" % tower_id)


static func lit_texture(path: String) -> CanvasTexture:
	if _texture_cache.has(path):
		return _texture_cache[path]
	var tex := CanvasTexture.new()
	tex.diffuse_texture = load(path + ".png")
	if ResourceLoader.exists(path + "_n.png"):
		tex.normal_texture = load(path + "_n.png")
	_texture_cache[path] = tex
	return tex


func setup(p_sim: RunSim) -> void:
	sim = p_sim
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_noise.frequency = 2.0
	_build_resources()
	_world = Node2D.new()
	_world.scale = Vector2(SCALE, SCALE)
	add_child(_world)
	_ambient = CanvasModulate.new()
	add_child(_ambient)
	_sun = DirectionalLight2D.new()
	_sun.height = 0.55
	_sun.rotation = atan2(-SUN_SHADOW_DIR.x, SUN_SHADOW_DIR.y)
	add_child(_sun)
	for layer_z in [0, 1, 2, 4]:
		var layer := Node2D.new()
		layer.z_index = layer_z
		_world.add_child(layer)
		match layer_z:
			0: _ground = layer
			1: _shadows = layer
			2:
				_actors = layer
				_actors.y_sort_enabled = true
			4: _air = layer
	_ground_fx = Node2D.new()
	_ground_fx.z_index = 1
	_ground_fx.material = _additive
	_ground_fx.draw.connect(_draw_ground_fx)
	_world.add_child(_ground_fx)
	_marks = Node2D.new()
	_marks.z_index = 4
	_marks.material = _unshaded
	_marks.draw.connect(_draw_marks)
	_world.add_child(_marks)
	_build_ground()
	_build_fireflies()
	sim.chain_fired.connect(_on_chain_fired)
	sim.projectile_landed.connect(_on_projectile_landed)
	sim.enemy_killed.connect(_on_enemy_killed)
	sim.skill_used.connect(_on_skill_used)
	_update_light(0.0)
	day_night.snap()
	_update_light(0.0)


func _build_resources() -> void:
	var img := Image.create(1, 1, false, Image.FORMAT_RGBA8)
	img.fill(Color.WHITE)
	_pixel = ImageTexture.create_from_image(img)
	_light_texture = _radial(128, [Color(1, 1, 1, 1), Color(1, 1, 1, 0.5), Color(1, 1, 1, 0)], [0.0, 0.4, 1.0])
	_blob_texture = _radial(32, [Color(0, 0, 0, 0.5), Color(0, 0, 0, 0)], [0.45, 1.0])
	var sway := Shader.new()
	sway.code = """
shader_type canvas_item;
// Sways the top of a sprite while its base stays planted.
uniform float strength = 0.9;
void vertex() {
	float top = 1.0 - UV.y;
	vec2 world = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	float t = TIME * 1.7 + world.x * 0.02 + world.y * 0.015;
	VERTEX.x += (sin(t) + 0.35 * sin(t * 2.7)) * strength * top;
}
"""
	_sway_material = ShaderMaterial.new()
	_sway_material.shader = sway
	_unshaded = CanvasItemMaterial.new()
	_unshaded.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_additive = CanvasItemMaterial.new()
	_additive.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	_additive.blend_mode = CanvasItemMaterial.BLEND_MODE_ADD


func _radial(size: int, colors: Array, offsets: Array) -> GradientTexture2D:
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


## Each biome's light: a tint over the day and night colours, and the motes that drift in the air
## (colour, drift up or down).
const BIOME_TINTS := {
	&"meadow": Color(1, 1, 1), &"fire": Color(1.08, 0.9, 0.82), &"storm": Color(0.92, 0.96, 1.04),
	&"nature": Color(0.94, 1.04, 0.92), &"water": Color(0.95, 1.0, 1.1), &"earth": Color(1.08, 0.96, 0.86),
	&"void": Color(0.9, 0.84, 1.08), &"heart": Color(1.04, 1.02, 0.96),
}
const BIOME_MOTES := {
	&"meadow": [Color(0.85, 1, 0.45), 0.0], &"fire": [Color(1.0, 0.55, 0.2), -8.0],
	&"storm": [Color(0.75, 0.9, 1.0), 0.0], &"nature": [Color(0.75, 1, 0.4), 0.0],
	&"water": [Color(0.95, 0.98, 1.0), 6.0], &"earth": [Color(1.0, 0.85, 0.55), 0.0],
	&"void": [Color(0.75, 0.55, 1.0), -4.0], &"heart": [Color(1.0, 0.95, 0.7), -3.0],
}


## The ground is cut into 2x2-cell pieces so each piece only takes the lights near it
## (the Compatibility renderer caps the lights per drawn item).
func _build_ground() -> void:
	var map := sim.config.map
	_biome = map.biome if BIOME_TINTS.has(map.biome) else &"meadow"
	var path := ART + "ground/%s" % map.id
	var tex := lit_texture(path)
	var cell := float(map.cell_size) / SCALE
	var chunk := cell * 2.0
	var size := Vector2(map.grid_size) * cell
	var y := 0.0
	while y < size.y:
		var x := 0.0
		while x < size.x:
			var piece := Sprite2D.new()
			piece.texture = tex
			piece.centered = false
			piece.region_enabled = true
			piece.region_rect = Rect2(x, y, minf(chunk, size.x - x), minf(chunk, size.y - y))
			piece.position = Vector2(x, y)
			_ground.add_child(piece)
			x += chunk
		y += chunk
	if ResourceLoader.exists(path + "_glow.png"):
		_ground_glow = Sprite2D.new()
		_ground_glow.texture = load(path + "_glow.png")
		_ground_glow.centered = false
		_ground_glow.material = _additive
		_ground.add_child(_ground_glow)
	var layout_path := path + ".json"
	if not FileAccess.file_exists(layout_path):
		return
	var layout: Variant = JSON.parse_string(FileAccess.get_file_as_string(layout_path))
	if not layout is Dictionary:
		return
	var prop_info: Dictionary = info().get("props", {})
	for prop: Dictionary in layout.get("props", []):
		var kind: String = prop["kind"]
		var p: Array = prop["pos"]
		var c: Array = prop["cell"]
		var meta: Dictionary = prop_info.get(kind, {})
		var sprite := Sprite2D.new()
		sprite.texture = lit_texture(ART + "props/" + kind)
		var tex_size := sprite.texture.get_size()
		sprite.centered = false
		sprite.offset = Vector2(-floorf(tex_size.x / 2.0), -tex_size.y + 1)
		sprite.position = Vector2(p[0], p[1])
		sprite.flip_h = prop.get("flip", false)
		if meta.get("sways", false):
			sprite.material = _sway_material
		if meta.get("glow", false):
			var glow := Sprite2D.new()
			glow.texture = load(ART + "props/%s_glow.png" % kind)
			glow.centered = false
			glow.offset = sprite.offset
			glow.flip_h = sprite.flip_h
			glow.material = _additive
			glow.set_meta("night_glow", true)
			sprite.add_child(glow)
		_actors.add_child(sprite)
		var caster := _add_caster(sprite, (sprite.texture as CanvasTexture).diffuse_texture, sprite.offset, 0.5, sprite)
		var key := Vector2i(c[0], c[1])
		if not _props_by_cell.has(key):
			_props_by_cell[key] = []
		_props_by_cell[key].append(caster)


func _build_fireflies() -> void:
	var size := sim.config.map.size_in_pixels() / SCALE
	_fireflies = _particles(30, 5.0, size / 2.0)
	_fireflies.position = size / 2.0
	_fireflies.spread = 180.0
	_fireflies.initial_velocity_min = 2.0
	_fireflies.initial_velocity_max = 6.0
	var mote: Array = BIOME_MOTES[_biome]
	var mote_color: Color = mote[0]
	_fireflies.gravity = Vector2(0, mote[1])
	_fireflies.color_ramp = _gradient([Color(mote_color, 0), mote_color, Color(mote_color, 0)], [0.0, 0.5, 1.0])
	_fireflies.material = _additive
	_air.add_child(_fireflies)


func _add_caster(node: Node2D, silhouette: Texture2D, offset: Vector2, height: float, flip_from: Sprite2D = null) -> Caster:
	var caster := Caster.new()
	caster.node = node
	caster.flip_from = flip_from
	caster.height = height
	var size := silhouette.get_size()
	caster.blob = Sprite2D.new()
	caster.blob.texture = _blob_texture
	caster.blob.scale = Vector2(size.x * 1.1, maxf(3.0, size.x * 0.4)) / 32.0
	_shadows.add_child(caster.blob)
	caster.sun = Sprite2D.new()
	caster.sun.texture = silhouette
	caster.sun.centered = false
	caster.sun.offset = offset
	caster.sun.modulate = Color(0, 0, 0, 0)
	_shadows.add_child(caster.sun)
	_casters.append(caster)
	return caster


func _remove_caster(caster: Caster) -> void:
	_casters.erase(caster)
	caster.blob.queue_free()
	caster.sun.queue_free()


func _particles(amount: int, lifetime: float, extents: Vector2) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = amount
	p.lifetime = lifetime
	p.texture = _pixel
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = extents
	p.local_coords = false
	return p


func _gradient(colors: Array, offsets: Array) -> Gradient:
	var g := Gradient.new()
	g.colors = PackedColorArray(colors)
	g.offsets = PackedFloat32Array(offsets)
	return g


func _point_light(color: Color, energy: float, radius: float, height: float) -> PointLight2D:
	var light := PointLight2D.new()
	light.texture = _light_texture
	light.color = color
	light.energy = energy
	light.texture_scale = radius / 64.0
	light.height = height
	return light


func _art_pos(board_position: Vector2) -> Vector2:
	return board_position / SCALE


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	if sim == null:
		return
	_elapsed += delta
	_update_light(delta)
	_sync_towers(delta)
	_sync_enemies(delta)
	_sync_shots()
	_update_shadows()
	_advance_fx(delta)
	_ground_fx.queue_redraw()
	_marks.queue_redraw()


func _update_light(delta: float) -> void:
	var in_wave := sim.state == RunSim.State.WAVE
	var target := DayNight.target_for(sim.wave_index, in_wave, sim.time_in_wave, sim.state == RunSim.State.WON)
	if light_override >= 0.0:
		# The clock only runs forward, so the held time is today's, or tomorrow's if today's has passed.
		target = floorf(day_night.clock) + light_override
		if target < day_night.clock - 0.001:
			target += 1.0
	day_night.set_target(target)
	day_night.advance(delta)
	_ambient.color = day_night.ambient() * BIOME_TINTS[_biome]
	_sun.energy = day_night.sun_energy()
	_sun.color = day_night.sun_color()
	var motes := day_night.night()
	if _biome in [&"fire", &"water", &"void", &"heart"]:
		motes = maxf(motes, 0.45)
	_fireflies.modulate = Color(1, 1, 1, motes)
	if _ground_glow != null:
		var flicker := 0.85 + 0.15 * _noise.get_noise_1d(_elapsed * 3.0)
		_ground_glow.modulate = Color(1, 1, 1, (0.45 + 0.55 * day_night.night()) * flicker)


func _sync_towers(delta: float) -> void:
	var seen: Dictionary[int, bool] = {}
	for tower in sim.towers:
		var current: TowerVisual = _towers.get(tower.id)
		if current != null and current.data_id == tower.data.id:
			seen[tower.id] = true
		elif not tower_info(tower.data.id).is_empty():
			if current != null:
				_remove_caster(current.caster)
				current.root.queue_free()
			var made := _make_tower(tower)
			_towers[tower.id] = made
			seen[tower.id] = true
			if current != null:
				_celebrate(made, false)
			else:
				_burst(made.root.position, Color(0.75, 0.68, 0.55), 10, 16.0, false)
	for id in _towers.keys():
		if not seen.has(id):
			var visual: TowerVisual = _towers[id]
			_remove_caster(visual.caster)
			visual.root.queue_free()
			_towers.erase(id)
	if sim.towers.size() != _tower_count:
		_tower_count = sim.towers.size()
		for cell in _props_by_cell:
			var free := sim.tower_at(cell) == null
			for caster: Caster in _props_by_cell[cell]:
				caster.node.visible = free
				caster.blob.visible = free
				caster.sun.visible = free
	var night := day_night.night()
	var flicker := _noise.get_noise_1d(_elapsed * 9.0)
	for visual: TowerVisual in _towers.values():
		visual.pulse = maxf(0.0, visual.pulse - delta * 4.0)
		var boost := (0.4 + night * 0.6) * (1.0 + 0.12 * (visual.tower.level - 1)) * (1.35 if visual.tower.ascendancy != null else 1.0)
		visual.light.energy = visual.light_energy * boost * (1.0 + flicker * 0.12 + visual.pulse * 0.6)
		visual.glow.modulate = Color(1, 1, 1, 0.85 + 0.15 * flicker + visual.pulse * 0.3)
		var ascended := visual.tower.ascendancy != null
		if visual.tower.level != visual.level or ascended != visual.ascended:
			var ascending := ascended and not visual.ascended
			visual.level = visual.tower.level
			visual.ascended = ascended
			_celebrate(visual, ascending)


func _make_tower(tower: SimTower) -> TowerVisual:
	var meta := tower_info(tower.data.id)
	var visual := TowerVisual.new()
	visual.tower = tower
	visual.data_id = tower.data.id
	visual.level = tower.level
	visual.ascended = tower.ascendancy != null
	visual.shot_style = shot_style(tower.data)
	for element in tower.data.elements:
		visual.colors.append(sim.config.element_color(element))
	if visual.colors.is_empty():
		visual.colors.append(Color.WHITE)
	var anchor: Array = meta["anchor"]
	var offset := -Vector2(anchor[0], anchor[1])
	visual.root = Node2D.new()
	visual.root.position = _art_pos(tower.position) + Vector2(0, TOWER_BASE_DROP)
	_actors.add_child(visual.root)
	var body := Sprite2D.new()
	body.texture = lit_texture(ART + "towers/%s" % tower.data.id)
	body.centered = false
	body.offset = offset
	visual.root.add_child(body)
	visual.glow = Sprite2D.new()
	visual.glow.texture = load(ART + "towers/%s_glow.png" % tower.data.id)
	visual.glow.centered = false
	visual.glow.offset = offset
	visual.glow.material = _additive
	visual.root.add_child(visual.glow)
	var light_meta: Dictionary = meta.get("light", {})
	var light_offset: Array = light_meta.get("offset", [0, -30])
	visual.light_energy = light_meta.get("energy", 1.0)
	visual.light = _point_light(Color(light_meta.get("color", "#ffffff")), visual.light_energy,
			light_meta.get("range", 100.0), light_meta.get("height", 40.0))
	visual.light.position = Vector2(light_offset[0], light_offset[1])
	visual.root.add_child(visual.light)
	var muzzle: Array = meta.get("muzzle", [0, -30])
	visual.muzzle = Vector2(muzzle[0], muzzle[1])
	var emitter_offset: Array = meta.get("emitter_offset", muzzle)
	var emitter := _tower_emitter(String(meta.get("emitter", "")))
	if emitter != null:
		emitter.position = visual.root.position + Vector2(emitter_offset[0], emitter_offset[1])
		_air.add_child(emitter)
		visual.root.tree_exiting.connect(emitter.queue_free)
	visual.caster = _add_caster(visual.root, (body.texture as CanvasTexture).diffuse_texture, offset, 1.0)
	visual.caster.blob.scale = Vector2(1.0, 0.45) * 28.0 / 32.0
	return visual


## The element a tower's shots are made of: the one its crown is built from, else its first.
static func shot_style(data: TowerData) -> StringName:
	if data == null or data.elements.is_empty():
		return &""
	var kind := String(tower_info(data.id).get("emitter", ""))
	if SHOT_STYLES.has(kind):
		var style: StringName = SHOT_STYLES[kind]
		if data.elements.has(style):
			return style
	return data.elements[0]


## A tower that gains a level, fuses or ascends: sparks climb it and a ring spreads from its base.
func _celebrate(visual: TowerVisual, ascending: bool) -> void:
	var color := visual.colors[0].lerp(Color.WHITE, 0.35)
	var sparks := _particles(34 if ascending else 16, 0.8, Vector2(9, 3))
	sparks.one_shot = true
	sparks.explosiveness = 0.7
	sparks.direction = Vector2(0, -1)
	sparks.spread = 12.0
	sparks.gravity = Vector2(0, -25)
	sparks.initial_velocity_min = 18.0
	sparks.initial_velocity_max = 46.0 if ascending else 34.0
	sparks.color_ramp = _gradient([Color.WHITE, color, Color(color, 0)], [0.0, 0.4, 1.0])
	sparks.material = _additive
	sparks.position = visual.root.position + Vector2(0, -4)
	_air.add_child(sparks)
	sparks.emitting = true
	get_tree().create_timer(1.4).timeout.connect(sparks.queue_free)
	_ring(visual.root.position, color, 4.0, 30.0 if ascending else 20.0, 0.45)
	if ascending:
		_ring(visual.root.position, Color.WHITE, 2.0, 44.0, 0.7)
	visual.pulse = 2.0


func _tower_emitter(kind: String) -> CPUParticles2D:
	match kind:
		"fire":
			var flames := _particles(26, 0.5, Vector2(3.5, 1))
			flames.direction = Vector2(0, -1)
			flames.spread = 14.0
			flames.gravity = Vector2(0, -30)
			flames.initial_velocity_min = 5.0
			flames.initial_velocity_max = 14.0
			flames.scale_amount_min = 1.0
			flames.scale_amount_max = 2.0
			flames.color_ramp = _gradient([Color(1, 0.98, 0.75), Color(1, 0.75, 0.25), Color(0.95, 0.3, 0.08), Color(0.5, 0.08, 0.05, 0)], [0.0, 0.25, 0.65, 1.0])
			flames.material = _additive
			return flames
		"sparks", "plasma":
			var sparks := _particles(6, 0.35, Vector2(4, 5))
			sparks.direction = Vector2(0, -1)
			sparks.spread = 180.0
			sparks.gravity = Vector2.ZERO
			sparks.initial_velocity_min = 6.0
			sparks.initial_velocity_max = 16.0
			var hot := Color(1, 0.85, 0.5) if kind == "plasma" else Color(1, 0.95, 0.6)
			sparks.color_ramp = _gradient([Color.WHITE, hot, Color(hot, 0)], [0.0, 0.3, 1.0])
			sparks.material = _additive
			return sparks
		"drips":
			var drips := _particles(6, 0.9, Vector2(5, 2))
			drips.direction = Vector2(0, 1)
			drips.spread = 25.0
			drips.gravity = Vector2(0, 40)
			drips.initial_velocity_min = 2.0
			drips.initial_velocity_max = 8.0
			drips.color_ramp = _gradient([Color(0.85, 0.97, 1.0), Color(0.4, 0.75, 1.0, 0.9), Color(0.2, 0.5, 0.9, 0)], [0.0, 0.4, 1.0])
			drips.material = _additive
			return drips
		"dust":
			var dust := _particles(4, 1.6, Vector2(5, 1))
			dust.direction = Vector2(0, 1)
			dust.spread = 30.0
			dust.gravity = Vector2(0, 8)
			dust.initial_velocity_min = 1.0
			dust.initial_velocity_max = 4.0
			dust.color_ramp = _gradient([Color(1, 0.8, 0.4, 0), Color(1, 0.75, 0.35, 0.8), Color(0.8, 0.5, 0.2, 0)], [0.0, 0.3, 1.0])
			dust.material = _additive
			return dust
		"void", "soulfire":
			var soul := kind == "soulfire"
			var wisps := _particles(14 if soul else 8, 0.8 if soul else 1.4, Vector2(3.5, 1) if soul else Vector2(8, 4))
			wisps.direction = Vector2(0, -1)
			wisps.spread = 20.0 if soul else 180.0
			wisps.gravity = Vector2(0, -20) if soul else Vector2.ZERO
			wisps.initial_velocity_min = 4.0 if soul else 2.0
			wisps.initial_velocity_max = 11.0 if soul else 6.0
			wisps.scale_amount_min = 1.0
			wisps.scale_amount_max = 2.0 if soul else 1.0
			wisps.color_ramp = _gradient([Color(0.95, 0.85, 1.0), Color(0.7, 0.4, 1.0, 0.9), Color(0.3, 0.1, 0.6, 0)], [0.0, 0.35, 1.0])
			wisps.material = _additive
			return wisps
		"steam":
			var steam := _particles(10, 1.6, Vector2(8, 2))
			steam.direction = Vector2(0, -1)
			steam.spread = 18.0
			steam.gravity = Vector2(2, -6)
			steam.initial_velocity_min = 4.0
			steam.initial_velocity_max = 10.0
			steam.scale_amount_min = 1.0
			steam.scale_amount_max = 3.0
			steam.color_ramp = _gradient([Color(1, 1, 1, 0), Color(0.95, 0.97, 1.0, 0.6), Color(0.85, 0.9, 0.95, 0)], [0.0, 0.25, 1.0])
			return steam
		"bubbles":
			var bubbles := _particles(5, 1.2, Vector2(9, 2))
			bubbles.direction = Vector2(0, -1)
			bubbles.spread = 10.0
			bubbles.gravity = Vector2(0, -4)
			bubbles.initial_velocity_min = 2.0
			bubbles.initial_velocity_max = 5.0
			bubbles.color_ramp = _gradient([Color(0.7, 1, 0.5, 0), Color(0.65, 1, 0.45, 0.85), Color(0.5, 0.9, 0.3, 0)], [0.0, 0.3, 1.0])
			bubbles.material = _additive
			return bubbles
		"leaves":
			var pollen := _particles(5, 2.5, Vector2(10, 5))
			pollen.direction = Vector2(0.3, 1)
			pollen.spread = 40.0
			pollen.gravity = Vector2(2, 6)
			pollen.initial_velocity_min = 1.0
			pollen.initial_velocity_max = 4.0
			pollen.color_ramp = _gradient([Color(0.7, 1, 0.4, 0), Color(0.75, 1, 0.45, 0.9), Color(0.6, 0.9, 0.3, 0)], [0.0, 0.3, 1.0])
			pollen.material = _additive
			return pollen
	return null


func _sync_enemies(delta: float) -> void:
	var seen: Dictionary[int, bool] = {}
	var shown: Array[SimEnemy] = sim.enemies.duplicate()
	shown.append_array(sim.structures)
	for enemy in shown:
		if not enemy.alive:
			continue
		seen[enemy.id] = true
		var visual: EnemyVisual = _enemies.get(enemy.id)
		if visual == null:
			if enemy_info(enemy.data.id).is_empty():
				continue
			visual = _make_enemy(enemy, _enemy_tint(enemy))
			_enemies[enemy.id] = visual
		_update_enemy(visual, delta)
	for id in _enemies.keys():
		if not seen.has(id):
			var visual: EnemyVisual = _enemies[id]
			_remove_caster(visual.caster)
			visual.root.queue_free()
			_enemies.erase(id)


func _make_enemy(enemy: SimEnemy, tint: Color) -> EnemyVisual:
	var meta := enemy_info(enemy.data.id)
	var visual := EnemyVisual.new()
	visual.enemy = enemy
	visual.tint = tint
	visual.last_health = enemy.health
	visual.time = randf() * 2.0
	var count: int = meta.get("frames", 4)
	for f in count:
		visual.frames.append(lit_texture(ART + "enemies/%s_%d" % [enemy.data.id, f]))
		if meta.get("gear", false):
			visual.gear_frames.append(lit_texture(ART + "enemies/%s_gear_%d" % [enemy.data.id, f]))
			visual.glow_frames.append(load(ART + "enemies/%s_gear_%d_glow.png" % [enemy.data.id, f]))
	var anchor: Array = meta["anchor"]
	var offset := -Vector2(anchor[0], anchor[1])
	var size: Array = meta["size"]
	visual.size_scale = enemy_scale(enemy.data.id)
	visual.size = Vector2(size[0], size[1]) * visual.size_scale
	visual.root = Node2D.new()
	visual.root.position = _art_pos(enemy.position) + Vector2(0, ENEMY_DROP)
	visual.last_x = visual.root.position.x
	_actors.add_child(visual.root)
	visual.body = Sprite2D.new()
	visual.body.texture = visual.frames[0]
	visual.body.centered = false
	visual.body.offset = offset
	visual.root.add_child(visual.body)
	if not visual.gear_frames.is_empty():
		visual.gear = Sprite2D.new()
		visual.gear.texture = visual.gear_frames[0]
		visual.gear.centered = false
		visual.gear.offset = offset
		visual.root.add_child(visual.gear)
		visual.gear_glow = Sprite2D.new()
		visual.gear_glow.texture = visual.glow_frames[0]
		visual.gear_glow.centered = false
		visual.gear_glow.offset = offset
		visual.gear_glow.material = _additive
		visual.root.add_child(visual.gear_glow)
	visual.caster = _add_caster(visual.root, visual.frames[0].diffuse_texture, offset, 0.7, visual.body)
	visual.caster.size_scale = visual.size_scale
	visual.caster.blob.scale *= visual.size_scale
	visual.root.scale = Vector2.ONE * visual.size_scale
	return visual


func _update_enemy(visual: EnemyVisual, delta: float) -> void:
	var enemy := visual.enemy
	var pos := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP)
	var speed_factor := enemy.speed() / maxf(1.0, enemy.base_speed)
	# A stunned enemy stops mid-step.
	if not enemy.has_status(&"stun"):
		visual.time += delta * (0.6 + speed_factor * 0.4) * (1.6 if enemy.data.tags.has(&"fast") else 1.0)
	var frame := int(visual.time * 9.0) % visual.frames.size()
	visual.body.texture = visual.frames[frame]
	if visual.gear != null:
		visual.gear.texture = visual.gear_frames[frame]
		visual.gear_glow.texture = visual.glow_frames[frame]
	if absf(pos.x - visual.last_x) > 0.01:
		var left := pos.x < visual.last_x
		visual.body.flip_h = left
		if visual.gear != null:
			visual.gear.flip_h = left
			visual.gear_glow.flip_h = left
	visual.last_x = pos.x
	visual.root.position = pos
	if enemy.health < visual.last_health - 0.01:
		visual.flash = 1.0
	visual.last_health = enemy.health
	visual.flash = maxf(0.0, visual.flash - delta * 9.0)
	# A hit squashes it for a moment.
	visual.root.scale = Vector2(1.0 + visual.flash * 0.14, 1.0 - visual.flash * 0.14) * visual.size_scale
	if enemy.data.prismatic_interval > 0.0:
		visual.tint = visual.tint.lerp(_enemy_tint(enemy), minf(1.0, delta * 4.0))
	var color := visual.tint
	if enemy.is_regenerating() and enemy.health < enemy.max_health:
		color = color.lerp(Color(0.6, 1.0, 0.6), 0.15 + 0.1 * sin(_elapsed * 6.0))
	var pulse := 0.5 + 0.5 * sin(_elapsed * 9.0 + float(enemy.id))
	if enemy.has_status(&"burn"):
		color = color.lerp(Color(1.0, 0.5, 0.2), 0.35 * pulse)
	if enemy.has_status(&"poison"):
		color = color.lerp(Color(0.5, 1.0, 0.35), 0.35 * (1.0 - pulse))
	if enemy.has_status(&"slow"):
		color = color.lerp(Color(0.55, 0.8, 1.0), 0.45)
	if enemy.has_status(&"curse"):
		color = color.lerp(Color(0.7, 0.45, 1.0), 0.3 + 0.2 * pulse)
	if enemy.has_status(&"shatter"):
		color = color.darkened(0.15)
	if enemy.has_status(&"stun"):
		color = color.lerp(Color(1.0, 0.9, 0.5), 0.5)
	visual.body.modulate = color.lerp(Color(1.8, 1.8, 1.8), visual.flash * 0.7)
	if visual.gear != null:
		visual.gear.modulate = Color(1, 1, 1).lerp(Color(1.8, 1.8, 1.8), visual.flash * 0.7)


## Enemies take the colour of their element.
func _enemy_tint(enemy: SimEnemy) -> Color:
	if enemy.element < 0:
		return Color.WHITE
	return sim.config.element_color_at(enemy.element).lerp(Color.WHITE, 0.3)


func _sync_shots() -> void:
	var live: Dictionary[SimProjectile, bool] = {}
	for shot in sim.projectiles:
		live[shot] = true
		var node: Node2D = _shots.get(shot)
		if node == null:
			node = _make_shot(shot)
			_shots[shot] = node
		var pos := _art_pos(shot.position)
		var travel := pos - node.position
		node.position = pos
		if travel.length_squared() > 0.0001:
			node.rotation = travel.angle()
	for shot in _shots.keys():
		if not live.has(shot):
			var node: Node2D = _shots[shot]
			_shots.erase(shot)
			_retire(node)


func _make_shot(shot: SimProjectile) -> Node2D:
	var node := Node2D.new()
	node.position = _art_pos(shot.position)
	_air.add_child(node)
	var source: TowerVisual = _towers.get(shot.source.id) if shot.source != null else null
	var style := shot_style(shot.source.data) if shot.source != null else &""
	if source != null:
		source.pulse = 1.0
		node.position = source.root.position + source.muzzle
		style = source.shot_style
	var color := sim.config.element_color(style) if style != &"" else Color.WHITE
	# A mixed tower's shot trails its other element.
	var second := color
	if shot.source != null:
		for element in shot.source.data.elements:
			if element != style:
				second = sim.config.element_color(element)
	var hot := color.lerp(Color.WHITE, 0.6)
	var heavy := shot.splash_radius > 0.0
	match style:
		&"fire":
			# A fireball: hot core and a trail of flame.
			_shot_core(node, Color(1, 0.95, 0.7), 3.0 if heavy else 2.0, true)
			_shot_trail(node, 18 if heavy else 7, 0.3 if heavy else 0.2, Color(1, 0.9, 0.5), second, Vector2(0, -10), true)
		&"storm":
			# A crooked bolt; the heavy ones are ball lightning.
			_shot_streak(node, [Vector2(-5, 0), Vector2(-3, -1.5), Vector2(-1, 1), Vector2(1, 0)], Color(color, 0.7), 2.0, true)
			_shot_streak(node, [Vector2(-5, 0), Vector2(-3, -1.5), Vector2(-1, 1), Vector2(1, 0)], Color(1, 1, 0.92), 1.0, true)
			if heavy:
				_shot_core(node, Color(1, 1, 0.9), 3.0, true)
				var sparks := _shot_trail(node, 12, 0.25, Color.WHITE, second, Vector2.ZERO, true)
				sparks.spread = 180.0
				sparks.initial_velocity_max = 16.0
		&"nature":
			# A thorn with a pale tip, or a seed pod that sheds spores.
			_shot_streak(node, [Vector2(-4, 0), Vector2(0, 0)], color.darkened(0.3), 1.0, false)
			_shot_streak(node, [Vector2(0, 0), Vector2(2, 0)], hot, 1.0, false)
			if heavy:
				_shot_core(node, color, 3.0, false)
			_shot_trail(node, 10 if heavy else 4, 0.4, hot, second, Vector2(0, 14), false)
		&"water":
			# A drop with a tail of spray that falls away behind it.
			var tail := _shot_streak(node, [Vector2(-5, 0), Vector2(0, 0)], Color.WHITE, 1.0, false)
			tail.gradient = _gradient([Color(color, 0.0), hot], [0.0, 1.0])
			_shot_core(node, hot, 3.0 if heavy else 2.0, false)
			_shot_trail(node, 12 if heavy else 5, 0.35, hot, second, Vector2(0, 34), false)
		&"earth":
			# A tumbling rock and its dust.
			_shot_core(node, color.darkened(0.25), 4.0 if heavy else 3.0, false)
			var chip := _shot_core(node, color.lerp(Color.WHITE, 0.35), 2.0 if heavy else 1.0, false)
			chip.position = Vector2(-1, -1)
			_shot_trail(node, 10 if heavy else 4, 0.45, Color(0.9, 0.8, 0.62, 0.8), second.lerp(Color(0.6, 0.5, 0.4), 0.5), Vector2(0, 6), false)
		&"void":
			# A dark heart in a violet halo.
			var halo := _shot_core(node, Color(color, 0.85), 1.0, true)
			halo.texture = _light_texture
			halo.scale = Vector2.ONE * (14.0 if heavy else 9.0) / 128.0
			_shot_core(node, Color(0.1, 0.04, 0.2), 3.0 if heavy else 2.0, false)
			_shot_trail(node, 14 if heavy else 6, 0.4, hot, second, Vector2.ZERO, true)
		_:
			_shot_streak(node, [Vector2(-3, 0), Vector2(1, 0)], color.lerp(Color.WHITE, 0.25), 1.0, false)
	if heavy:
		# A shot that will burst carries its own light, if there is room for one.
		var light := _flash_light(color.lerp(Color.WHITE, 0.2), 0.9, 34.0, 16.0)
		if light != null:
			node.add_child(light)
	return node


func _shot_core(node: Node2D, color: Color, size: float, glowing: bool) -> Sprite2D:
	var core := Sprite2D.new()
	core.texture = _pixel
	core.scale = Vector2(size, size)
	core.modulate = color
	core.material = _additive if glowing else _unshaded
	node.add_child(core)
	return core


func _shot_trail(node: Node2D, amount: int, lifetime: float, from: Color, to: Color, gravity: Vector2, glowing: bool) -> CPUParticles2D:
	var trail := _particles(amount, lifetime, Vector2(1, 1))
	trail.gravity = gravity
	trail.initial_velocity_max = 3.0
	trail.scale_amount_max = 2.0
	trail.color_ramp = _gradient([from, to, Color(to.darkened(0.4), 0)], [0.0, 0.4, 1.0])
	trail.material = _additive if glowing else _unshaded
	node.add_child(trail)
	return trail


## A short line along the way the shot flies (the shot's node turns to face its travel).
func _shot_streak(node: Node2D, points: Array, color: Color, width: float, glowing: bool) -> Line2D:
	var streak := Line2D.new()
	streak.points = PackedVector2Array(points)
	streak.width = width
	streak.default_color = color
	streak.material = _additive if glowing else _unshaded
	node.add_child(streak)
	return streak


## Lets a shot's particles fade out instead of vanishing with it.
func _retire(node: Node2D) -> void:
	for child in node.get_children():
		if child is CPUParticles2D:
			(child as CPUParticles2D).emitting = false
		elif child is PointLight2D:
			_release_light(child as PointLight2D)
		else:
			child.queue_free()
	get_tree().create_timer(0.4).timeout.connect(node.queue_free)


func _flash_light(color: Color, energy: float, radius: float, height: float) -> PointLight2D:
	if _flash_lights >= MAX_FLASH_LIGHTS:
		return null
	_flash_lights += 1
	return _point_light(color, energy, radius, height)


func _release_light(light: PointLight2D) -> void:
	_flash_lights = maxi(0, _flash_lights - 1)
	light.queue_free()


func _update_shadows() -> void:
	var day := 1.0 - day_night.night()
	var angle := atan2(SUN_SHADOW_DIR.x, -SUN_SHADOW_DIR.y)
	for caster in _casters:
		var pos := caster.node.position
		caster.blob.position = pos
		caster.sun.position = pos
		caster.sun.rotation = angle
		caster.sun.scale = Vector2(1.0, 0.6 * caster.height) * caster.size_scale
		caster.sun.modulate = Color(0, 0, 0, 0.3 * day)
		if caster.flip_from != null:
			caster.sun.flip_h = caster.flip_from.flip_h


# ------------------------------------------------------------------ effects

func _on_chain_fired(tower: SimTower, points: PackedVector2Array) -> void:
	var visual: TowerVisual = _towers.get(tower.id)
	var color := sim.config.element_color(tower.data.elements[tower.data.elements.size() - 1])
	var bolt_points := PackedVector2Array()
	var start := _art_pos(points[0])
	if visual != null:
		visual.pulse = 1.0
		start = visual.root.position + visual.muzzle
	bolt_points.append(start)
	var previous := start
	for i in range(1, points.size()):
		var target := _art_pos(points[i]) + Vector2(0, ENEMY_DROP - 5)
		# A jagged bolt: a few kinked steps between each pair of points.
		var steps := 4
		for s in range(1, steps + 1):
			var p := previous.lerp(target, float(s) / steps)
			if s < steps:
				p += Vector2(randf_range(-2.5, 2.5), randf_range(-2.5, 2.5))
			bolt_points.append(p)
		previous = target
		_sparks(target, color.lerp(Color.WHITE, 0.5), 4, 6.0)
	var glow := Line2D.new()
	glow.points = bolt_points
	glow.width = 2.0
	glow.default_color = Color(color, 0.8)
	glow.material = _additive
	_air.add_child(glow)
	var core := Line2D.new()
	core.points = bolt_points
	core.width = 1.0
	core.default_color = Color(1, 1, 0.95)
	core.material = _additive
	_air.add_child(core)
	var light := _flash_light(color, 1.2, 40.0, 20.0)
	if light != null:
		light.position = previous
		_air.add_child(light)
	var tween := create_tween()
	tween.set_parallel()
	tween.tween_property(glow, "modulate:a", 0.0, 0.2)
	tween.tween_property(core, "modulate:a", 0.0, 0.2)
	if light != null:
		tween.tween_property(light, "energy", 0.0, 0.2)
	tween.chain().tween_callback(func() -> void:
		glow.queue_free()
		core.queue_free()
		if light != null:
			_release_light(light))


func _on_projectile_landed(shot: SimProjectile) -> void:
	var at := _art_pos(shot.position)
	var style := shot_style(shot.source.data) if shot.source != null else &""
	var color := sim.config.element_color(style).lerp(Color.WHITE, 0.25) if style != &"" else Color(1, 0.8, 0.5)
	if shot.splash_radius <= 0.0:
		# A shot that found its target throws a few sparks off it.
		if shot.target != null and shot.target.alive:
			_sparks(at + Vector2(0, ENEMY_DROP - 5), color, 5, 7.0)
		return
	var radius := shot.splash_radius / SCALE
	match style:
		&"water":
			# A splash: drops thrown up that fall back, and a ripple.
			_burst(at, color, 26, 34.0, false)
			_ring(at, color.lerp(Color.WHITE, 0.4), radius * 0.25, radius, 0.45)
			_ring(at, color, radius * 0.1, radius * 0.7, 0.6)
		&"earth":
			# Rubble and a ring of dust.
			_burst(at, color.darkened(0.2), 20, 28.0, false)
			_ring(at, Color(0.95, 0.85, 0.65), radius * 0.3, radius, 0.4)
		&"void":
			# It falls inward before it bursts.
			_ring(at, color, radius, 2.0, 0.3)
			_burst(at, color, 16, 20.0)
		&"storm":
			_burst(at, Color(1, 1, 0.85), 22, 46.0)
			_ring(at, color, radius * 0.4, radius, 0.22)
		&"nature":
			_burst(at, color, 22, 26.0, false)
			_ring(at, color.lerp(Color.WHITE, 0.3), radius * 0.3, radius, 0.4)
		_:
			_burst(at, color.lerp(Color(1, 0.8, 0.4), 0.3), 22, 30.0)
			_ring(at, color.lerp(Color(1, 0.9, 0.6), 0.5), radius * 0.3, radius, 0.3)
	var light := _flash_light(color, 1.8, radius * 1.6, 12.0)
	if light != null:
		light.position = at
		_air.add_child(light)
		var tween := create_tween()
		tween.tween_property(light, "energy", 0.0, 0.3)
		tween.tween_callback(func() -> void: _release_light(light))


func _on_enemy_killed(enemy: SimEnemy, _killer: SimTower, _bounty: int) -> void:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	var color := visual.tint if visual != null else Color(0.8, 0.85, 0.9)
	var at := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP - 4)
	if not enemy.data.tags.has(&"boss"):
		_burst(at, color, 14, 22.0, false)
		_ring(at, color.lerp(Color.WHITE, 0.4), 2.0, 9.0, 0.25)
		return
	# A boss goes out with a blast and a flash of its own colour.
	_burst(at, color, 48, 50.0, false)
	_burst(at, color.lerp(Color.WHITE, 0.5), 20, 30.0)
	_ring(at, color.lerp(Color.WHITE, 0.4), 4.0, 34.0, 0.6)
	_ring(at, Color.WHITE, 2.0, 22.0, 0.4)
	var light := _flash_light(color, 2.2, 90.0, 20.0)
	if light != null:
		light.position = at
		_air.add_child(light)
		var tween := create_tween()
		tween.tween_property(light, "energy", 0.0, 0.5)
		tween.tween_callback(func() -> void: _release_light(light))


## A cast skill: a blast where it lands, or a wave of light across the whole board, and sparks on
## every enemy it reached.
func _on_skill_used(skill: SkillData, board_at: Vector2) -> void:
	var at := _art_pos(board_at)
	var color := sim.config.element_color(skill.element).lerp(Color.WHITE, 0.25)
	var bright := color.lerp(Color.WHITE, 0.5)
	var light_radius := 0.0
	if skill.is_targeted():
		var radius := skill.radius / SCALE
		light_radius = radius * 2.2
		_ring(at, color, radius, radius * 0.97, 0.9, 2.0)
		if skill.damage > 0.0:
			# It lands: a flash, flying sparks and a shock wave out to its edge.
			_ring(at, bright, radius * 0.1, radius, 0.4, 2.0)
			_ring(at, color, radius * 0.05, radius * 0.8, 0.7)
			_burst(at, bright, 60, 80.0)
			_burst(at, color.darkened(0.25), 36, 46.0, false)
		else:
			# It takes hold instead of hitting: the ring closes in.
			_ring(at, bright, radius, 4.0, 0.5, 2.0)
			_ring(at, color, radius * 0.8, 2.0, 0.75)
			_burst(at, color, 34, 30.0, false)
	else:
		var reach := sim.config.map.size_in_pixels().length() * 0.5 / SCALE
		light_radius = reach
		_ring(at, bright, 8.0, reach, 0.9, 2.0)
		_ring(at, color, 4.0, reach * 0.85, 1.2, 2.0)
		if not skill.modifiers.is_empty():
			# A boon for the towers: every one of them flares.
			for visual: TowerVisual in _towers.values():
				_ring(visual.root.position + Vector2(0, -8), bright, 3.0, 18.0, 0.6)
				_sparks(visual.root.position + Vector2(0, -26), bright, 6, 11.0)
	for enemy in sim.enemies:
		if enemy.alive and (not skill.is_targeted() or enemy.position.distance_to(board_at) <= skill.radius):
			_sparks(_art_pos(enemy.position) + Vector2(0, ENEMY_DROP - 5), bright, 6, 9.0)
	var light := _flash_light(color, 2.4, light_radius, 30.0)
	if light != null:
		light.position = at
		_air.add_child(light)
		var tween := create_tween()
		tween.tween_property(light, "energy", 0.0, 0.6)
		tween.tween_callback(func() -> void: _release_light(light))


func _burst(at: Vector2, color: Color, amount: int, speed: float, glowing := true) -> void:
	var burst := _particles(amount, 0.45, Vector2(1, 1))
	burst.one_shot = true
	burst.explosiveness = 1.0
	burst.spread = 180.0
	burst.gravity = Vector2(0, 40)
	burst.initial_velocity_min = speed * 0.4
	burst.initial_velocity_max = speed
	burst.scale_amount_max = 2.0
	burst.color_ramp = _gradient([color.lerp(Color.WHITE, 0.5), color, Color(color.darkened(0.4), 0)], [0.0, 0.4, 1.0])
	if glowing:
		burst.material = _additive
	burst.position = at
	_air.add_child(burst)
	burst.emitting = true
	get_tree().create_timer(0.8).timeout.connect(burst.queue_free)


func _ring(at: Vector2, color: Color, from: float, to: float, life: float, width := 1.0) -> void:
	if _fx.size() >= MAX_FX:
		return
	var fx := Fx.new()
	fx.at = at
	fx.color = color
	fx.from = from
	fx.to = to
	fx.life = life
	fx.width = width
	_fx.append(fx)


func _sparks(at: Vector2, color: Color, count: int, reach: float) -> void:
	if _fx.size() >= MAX_FX:
		return
	var fx := Fx.new()
	fx.ring = false
	fx.at = at
	fx.color = color
	fx.count = count
	fx.to = reach
	fx.life = 0.22
	fx.salt = randi() % 1000
	_fx.append(fx)


## True while a ring or a spray of sparks is still playing.
func has_live_effects() -> bool:
	return not _fx.is_empty()


func _advance_fx(delta: float) -> void:
	var live: Array[Fx] = []
	for fx in _fx:
		fx.age += delta
		if fx.age < fx.life:
			live.append(fx)
	_fx = live


## One art pixel.
func _dot(on: Node2D, at: Vector2, color: Color) -> void:
	on.draw_rect(Rect2(at.floor(), Vector2.ONE), color)


func _draw_ground_fx() -> void:
	for visual: TowerVisual in _towers.values():
		var tower := visual.tower
		if tower.aura_radius > 0.0 and tower.aura_damage > 0.0:
			# The reach of an aura: a slow ring of lights on the ground.
			var center := _art_pos(tower.position)
			var radius := tower.aura_radius / SCALE
			var aura := visual.colors[visual.colors.size() - 1].lerp(Color.WHITE, 0.2)
			for i in 40:
				var angle := TAU * float(i) / 40.0 + _elapsed * 0.12
				var wave := 0.5 + 0.5 * sin(_elapsed * 2.0 + float(i) * 0.7)
				_dot(_ground_fx, center + Vector2.from_angle(angle) * radius, Color(aura, 0.15 + 0.3 * wave))
		if tower.ascendancy != null:
			# Runes circle the foot of an ascended tower, one colour per element.
			for i in 8:
				var angle := TAU * float(i) / 8.0 - _elapsed * 0.9
				var rune := visual.colors[i % visual.colors.size()].lerp(Color.WHITE, 0.4)
				var at := visual.root.position + Vector2(cos(angle) * 16.0, sin(angle) * 7.0 - 1.0)
				_dot(_ground_fx, at, Color(rune, 0.95))
				_dot(_ground_fx, at + Vector2(-sin(angle), cos(angle) * 0.5) * 1.6, Color(rune, 0.4))


func _draw_marks() -> void:
	for visual: EnemyVisual in _enemies.values():
		_draw_enemy_marks(visual)
	for fx in _fx:
		var fade := 1.0 - fx.age / fx.life
		var spread := 1.0 - fade * fade
		if fx.ring:
			var radius := lerpf(fx.from, fx.to, spread)
			# Big rings get more corners, so a skill's shock wave stays round.
			var corners := clampi(int(radius * 0.8), 28, 120)
			_draw_ring(fx.at, radius, corners, Color(fx.color, fade), fx.width)
			if radius > 5.0:
				_draw_ring(fx.at, radius - 1.0 - fx.width, corners, Color(fx.color, fade * 0.35), fx.width)
		else:
			for i in fx.count:
				var angle := float(fx.salt) + TAU * float(i) / float(fx.count) + sin(float(fx.salt + i * 7))
				var at := fx.at + Vector2.from_angle(angle) * fx.to * spread
				_dot(_marks, at, Color(fx.color.lerp(Color.WHITE, fade * 0.6), minf(1.0, fade * 2.0)))


## A ring that stops at the edge of the board, so a wide skill never draws over the HUD.
func _draw_ring(at: Vector2, radius: float, corners: int, color: Color, width: float) -> void:
	var board := Rect2(Vector2.ZERO, sim.config.map.size_in_pixels() / SCALE)
	if board.encloses(Rect2(at - Vector2(radius, radius), Vector2(radius, radius) * 2.0)):
		_marks.draw_arc(at, radius, 0.0, TAU, corners, color, width)
		return
	var run := PackedVector2Array()
	for i in corners + 1:
		var point := at + Vector2.from_angle(TAU * float(i) / float(corners)) * radius
		if board.has_point(point):
			run.append(point)
			continue
		if run.size() > 1:
			_marks.draw_polyline(run, color, width)
		run.clear()
	if run.size() > 1:
		_marks.draw_polyline(run, color, width)


## What is hurting an enemy, drawn on it: flames for a burn, bubbles for poison, frost at its feet for
## a slow, stars round its head for a stun, a violet mark for a curse and falling chips for shattered
## armour. A healing enemy gives off green crosses.
func _draw_enemy_marks(visual: EnemyVisual) -> void:
	var enemy := visual.enemy
	var healing := enemy.is_regenerating() and enemy.health < enemy.max_health
	if enemy.statuses.is_empty() and not healing:
		return
	var feet := visual.root.position
	var half := visual.size.x * 0.32
	var tall := visual.size.y * 0.7
	var head := feet + Vector2(0, -tall - 3.0)
	var salt := float(enemy.id) * 1.37
	if enemy.has_status(&"slow"):
		for i in 5:
			var glint := 0.5 + 0.5 * sin(_elapsed * 5.0 + salt + float(i) * 2.1)
			var at := feet + Vector2((float(i) - 2.0) * half * 0.55, 0.0)
			_dot(_marks, at, Color(0.7, 0.9, 1.0).lerp(Color.WHITE, glint))
			if i % 2 == 0:
				_dot(_marks, at + Vector2(0, -1), Color(0.5, 0.78, 1.0))
				_dot(_marks, at + Vector2(0, -2), Color(0.85, 0.96, 1.0, glint))
	if enemy.has_status(&"burn"):
		for i in 3:
			var rise := fposmod(_elapsed * 1.7 + salt + float(i) * 0.37, 1.0)
			var at := feet + Vector2(sin(salt * 3.0 + float(i) * 2.4) * half, -2.0 - rise * tall)
			var flame := Color(1.0, 0.95, 0.6).lerp(Color(0.95, 0.3, 0.1), rise)
			_marks.draw_rect(Rect2(at.floor(), Vector2(1.0, 2.0 if rise < 0.5 else 1.0)), Color(flame, 1.0 - rise * 0.6))
	if enemy.has_status(&"poison"):
		for i in 2:
			var rise := fposmod(_elapsed * 0.9 + salt * 0.7 + float(i) * 0.5, 1.0)
			var sway := sin(salt * 2.0 + float(i) * 3.1) * half + sin(_elapsed * 4.0 + float(i)) * 0.8
			var at := feet + Vector2(sway, -tall * 0.5 - rise * tall * 0.7)
			_dot(_marks, at, Color(0.5, 0.92, 0.3, 1.0 - rise * 0.5))
			_dot(_marks, at + Vector2(0, -1), Color(0.85, 1.0, 0.6, 1.0 - rise))
	if enemy.has_status(&"shatter"):
		for i in 2:
			var fall := fposmod(_elapsed * 1.4 + salt + float(i) * 0.5, 1.0)
			var side := -1.0 if i == 0 else 1.0
			var at := feet + Vector2(side * (half + 1.0 + fall * 2.0), -tall * 0.6 + fall * tall * 0.6)
			_dot(_marks, at, Color(0.86, 0.88, 0.93, 1.0 - fall * 0.7))
	if enemy.has_status(&"stun"):
		for i in 3:
			var angle := _elapsed * 6.0 + TAU * float(i) / 3.0
			var at := head + Vector2(cos(angle) * (half + 1.0), sin(angle) * 1.5)
			_dot(_marks, at, Color(1.0, 0.92, 0.45))
			if sin(angle) > 0.0:
				_dot(_marks, at + Vector2(0, -1), Color(1.0, 1.0, 0.85))
	if enemy.has_status(&"curse"):
		var throb := 0.5 + 0.5 * sin(_elapsed * 5.0 + salt)
		var mark := Color(0.72, 0.45, 1.0).lerp(Color.WHITE, throb * 0.45)
		var at := head + Vector2(0, -3)
		for offset: Vector2 in [Vector2(0, -1), Vector2(-1, 0), Vector2(1, 0), Vector2(0, 1)]:
			_dot(_marks, at + offset, mark)
		_dot(_marks, at, Color(0.2, 0.08, 0.35))
	if healing:
		var rise := fposmod(_elapsed * 0.8 + salt, 1.0)
		var at := (head + Vector2(sin(salt) * half, 4.0 - rise * 6.0)).floor()
		var green := Color(0.5, 1.0, 0.55, 1.0 - rise)
		_marks.draw_rect(Rect2(at + Vector2(-1, 0), Vector2(3, 1)), green)
		_marks.draw_rect(Rect2(at + Vector2(0, -1), Vector2(1, 3)), green)


## Height of an enemy's sprite in board pixels, for placing its health bar. 0 if it has no art.
static func enemy_height(enemy_id: StringName) -> float:
	var meta := enemy_info(enemy_id)
	if meta.is_empty():
		return 0.0
	var size: Array = meta["size"]
	return float(size[1]) * SCALE * enemy_scale(enemy_id)


## How many times larger than its art a boss is drawn, so it stands BOSS_CELLS[id] cells tall. Whole
## numbers keep the pixel art crisp. 1 for everything else.
static func enemy_scale(enemy_id: StringName) -> float:
	var cells: float = BOSS_CELLS.get(enemy_id, 0.0)
	var meta := enemy_info(enemy_id)
	if cells <= 0.0 or meta.is_empty():
		return 1.0
	var size: Array = meta["size"]
	return maxf(1.0, roundf(cells * CELL_ART / float(size[1])))
