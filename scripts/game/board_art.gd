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

## The colour of lantern light and of the Sunstone, for heroes with no element of their own.
const HERO_LIGHT := Color(1.0, 0.9, 0.62)

static var _info: Dictionary = {}
static var _fx_info: Dictionary = {}
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
## The wind, rain, snow, ash and dust over the map (see Weather).
var weather: WeatherArt
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
var _flipbooks: Array[Flipbook] = []
## Blasts are drawn for this splash radius (art pixels) and scaled to the real one.
const BLAST_RADIUS := 24.0
var _corpses: Array[Corpse] = []
## Bodies left playing their deaths at once, oldest cleared first.
const MAX_CORPSES := 40
## Seconds a body stays on the ground after its death has played, fading out.
const CORPSE_LINGER := 1.2
## The war camps and the city at the road ends, or null when there is no art for them.
var landmarks: LandmarkArt
## The enemy caves that open during the run, or null without their art.
var caves: CaveArt
## The enemy citadel of the final assault, or null when the run has none.
var citadel: CitadelArt
## The army mustered in the counter-attack.
var army: AllyArt


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
## A hand-drawn effect played frame by frame (tools/art/pix2d/effects.py): the picture, and its hot pixels
## added on top so they shine at night.
class Flipbook:
	var node: Node2D
	var sprites: Array[Sprite2D] = []
	var frames := 1
	var fps := 12.0
	var age := 0.0
	var loop := false


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
	## Set for a beam: a line from `at` to here that fades (a mender's healing reaching an ally).
	var beam_to := Vector2.INF


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
	## The building's sprite. With an animation sheet (towers/anim/anim.json, tools/art/pix2d/tower_anim.py) it
	## has one row per look (levels 1-3, then each ascendancy) and idle frames then attack frames across.
	var body: Sprite2D
	var anim: Dictionary = {}
	## The row of the sheet it shows: TowerLook.stage_index().
	var stage := 0
	## Seconds of idle loop, started at a random point so towers side by side do not move in step.
	var idle_time := 0.0
	## Seconds into the attack it is playing, or below 0 while it idles.
	var attack_time := -1.0
	## Seconds until it may throw another flourish of its element when it fires.
	var flourish_wait := 0.0
	## Its shadow's picture: the rest frame of its current look.
	var silhouette: AtlasTexture
	## Muzzle and light where the level-1 art put them; an ascended tower stands on a dais and lifts them.
	var base_muzzle := Vector2.ZERO
	var base_light := Vector2.ZERO
	## The crown's own particles (fire, sparks, drips...), which rise with the crown onto the dais.
	var emitter: CPUParticles2D
	var base_emitter := Vector2.ZERO


class EnemyVisual:
	var enemy: SimEnemy
	## The kind of enemy it was drawn as (a boss changes kind when it takes a new form).
	var kind: StringName
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
	## Its power's frames (see tools/art/gen_enemy_powers.py) and its death's, empty without art.
	var power_frames: Array[CanvasTexture] = []
	var power_fps := 10.0
	## The power frame held while the power lasts (phased out, turned to stone), or -1.
	var power_hold := -1
	var death_frames: Array[CanvasTexture] = []
	var death_fps := 10.0
	## What it is showing: &"walk", &"power" (its power, once), &"unpower" (the power played back to
	## the start as it wears off) or &"fall" (lying in a heap before it rises).
	var anim := &"walk"
	var anim_time := 0.0
	## Above 0, it faces its power's target for this many more seconds instead of where it walks.
	var face_time := 0.0
	var face_left := false
	## Seconds until a power that never fires (an aura, a trait) is shown off again.
	var idle_power := 0.0
	## A boss's own moves (tools/art/pix2d/boss_moves.py), by name: {frames, fps, hold}. See BOSS_MOVES.
	var moves: Dictionary[StringName, Dictionary] = {}
	## The move playing while anim is &"move", and whether it stays on its hold frame (a guard while
	## the barrier stands) until released.
	var move := &""
	var move_hold := false
	## Seconds left of speech: its walk works its jaw meanwhile.
	var talk_left := 0.0


## The moves a boss can be drawn with besides its walk and death, in art.json under these names.
## BossDirector chooses when each plays; talk replaces the walk while it speaks, idle while it stands.
const BOSS_MOVES: Array[StringName] = [&"idle", &"talk", &"attack", &"roar", &"cast", &"slam", &"guard",
	&"hurt", &"rise"]


## A killed enemy playing out its death where it fell.
class Corpse:
	var sprite: Sprite2D
	var frames: Array[CanvasTexture] = []
	var fps := 10.0
	var time := 0.0


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


## A hand-drawn effect strip's size, frame count and speed, or {} if it has not been drawn.
static func fx_info(fx_name: String) -> Dictionary:
	if _fx_info.is_empty() and FileAccess.file_exists(ART + "fx/fx.json"):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART + "fx/fx.json"))
		if parsed is Dictionary:
			_fx_info = parsed
	return _fx_info.get(fx_name, {})


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
	# The board's filter is set by BoardCamera (crisp at whole-pixel zooms, smooth in between).
	texture_filter = CanvasItem.TEXTURE_FILTER_PARENT_NODE
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
	if LandmarkArt.has_art():
		landmarks = LandmarkArt.new()
		add_child(landmarks)
		landmarks.build(self)
	if CaveArt.has_art():
		caves = CaveArt.new()
		add_child(caves)
		caves.build(self)
	_build_citadel()
	army = AllyArt.new(self)
	_build_fireflies()
	weather = WeatherArt.new()
	_air.add_child(weather)
	weather.build(self, Weather.for_map(sim.config.map))
	sim.chain_fired.connect(_on_chain_fired)
	sim.projectile_landed.connect(_on_projectile_landed)
	sim.enemy_killed.connect(_on_enemy_killed)
	sim.skill_used.connect(_on_skill_used)
	sim.enemy_power.connect(_on_enemy_power)
	sim.enemy_transformed.connect(_on_enemy_transformed)
	sim.boss_fled.connect(_on_boss_fled)
	sim.citadel_struck.connect(_on_citadel_struck)
	sim.structure_destroyed.connect(_on_structure_destroyed)
	sim.ally_attacked.connect(_on_ally_attacked)
	sim.tower_attacked.connect(_on_tower_attacked)
	sim.ally_healed.connect(_on_ally_healed)
	sim.allies_mustered.connect(_on_allies_mustered)
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
// Sways the top of a sprite in the wind while its base stays planted. WeatherArt drives it: a steady
// lean downwind, a flutter that quickens as the wind rises, and gust fronts that sweep across the map
// and bow everything they pass.
uniform float strength = 0.9;
uniform float phase = 0.0;
uniform float lean = 0.0;
uniform float gust = 0.0;
uniform float gust_at = -100000.0;
uniform float gust_width = 150.0;
uniform vec2 wind_dir = vec2(1.0, 0.0);
uniform vec2 map_origin = vec2(0.0);
uniform float map_scale = 1.0;
void vertex() {
	float top = pow(1.0 - UV.y, 1.4);
	vec2 world = (MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy;
	vec2 m = (world - map_origin) / map_scale;
	float t = phase + m.x * 0.02 + m.y * 0.015;
	float d = (dot(m, wind_dir) - gust_at) / gust_width;
	float front = exp(-d * d);
	float flutter = (sin(t) + 0.35 * sin(t * 2.7)) * strength * (1.0 + 0.8 * front);
	float push = (lean + gust * front * (0.85 + 0.15 * sin(t * 3.3))) * sign(wind_dir.x);
	VERTEX.x += (flutter + push) * top;
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
		if sim.landmark_at(Vector2i(c[0], c[1])) != null:
			continue
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


## The citadel stands between the ground and everything that walks: the roads start at its gates.
func _build_citadel() -> void:
	for structure in sim.structures:
		if CitadelArt.draws(structure.data):
			citadel = CitadelArt.new()
			citadel.z_index = 1
			_world.add_child(citadel)
			citadel.build(self, structure)
			return


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
	weather.update(delta)
	_update_light(delta)
	_sync_towers(delta)
	_sync_enemies(delta)
	_sync_shots()
	_advance_corpses(delta)
	if landmarks != null:
		landmarks.update(delta)
	if caves != null:
		caves.update(delta)
	if citadel != null:
		citadel.update(delta, sim.is_vulnerable(citadel.structure))
	army.sync(delta)
	_update_shadows()
	_advance_fx(delta)
	_advance_flipbooks(delta)
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
	if weather != null:
		_ambient.color *= weather.ambient_tint()
		_sun.energy *= weather.sun_scale()
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
			if tower.is_hero():
				# A hero can march to another tile.
				current.root.position = _art_pos(tower.position) + Vector2(0, TOWER_BASE_DROP)
		elif tower.is_hero():
			_towers[tower.id] = _make_hero(tower)
			seen[tower.id] = true
			_celebrate(_towers[tower.id], true)
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
		var level_now := visual.tower.hero_level if visual.tower.is_hero() else visual.tower.level
		if level_now != visual.level or ascended != visual.ascended:
			var ascending := ascended and not visual.ascended
			visual.level = level_now
			visual.ascended = ascended
			_set_stage(visual)
			_celebrate(visual, ascending)
		_animate_tower(visual, delta)


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
	visual.body = body
	visual.glow = Sprite2D.new()
	visual.glow.texture = load(ART + "towers/%s_glow.png" % tower.data.id)
	visual.glow.centered = false
	visual.glow.offset = offset
	visual.glow.material = _additive
	visual.root.add_child(visual.glow)
	var sheet := TowerLook.sheet_info(tower.data.id)
	if TowerLook.has_sheet(sheet):
		# The animated sheet replaces the still: every look of the tower, idling and attacking.
		visual.anim = sheet
		var cell_anchor: Array = sheet["anchor"]
		offset = -Vector2(cell_anchor[0], cell_anchor[1])
		var path := ART + String(sheet["sheet"])
		body.texture = lit_texture(path)
		visual.glow.texture = load(path + "_glow.png")
		for sprite: Sprite2D in [body, visual.glow]:
			sprite.offset = offset
			sprite.hframes = TowerLook.columns(sheet)
			sprite.vframes = (sheet["stages"] as Array).size()
		visual.idle_time = randf() * 10.0
		visual.silhouette = AtlasTexture.new()
		visual.silhouette.atlas = (body.texture as CanvasTexture).diffuse_texture
	var light_meta: Dictionary = meta.get("light", {})
	var light_offset: Array = light_meta.get("offset", [0, -30])
	visual.light_energy = light_meta.get("energy", 1.0)
	visual.light = _point_light(Color(light_meta.get("color", "#ffffff")), visual.light_energy,
			light_meta.get("range", 100.0), light_meta.get("height", 40.0))
	visual.light.position = Vector2(light_offset[0], light_offset[1])
	visual.root.add_child(visual.light)
	var muzzle: Array = meta.get("muzzle", [0, -30])
	visual.muzzle = Vector2(muzzle[0], muzzle[1])
	visual.base_muzzle = visual.muzzle
	visual.base_light = visual.light.position
	var emitter_offset: Array = meta.get("emitter_offset", muzzle)
	var emitter := _tower_emitter(String(meta.get("emitter", "")))
	if emitter != null:
		emitter.position = visual.root.position + Vector2(emitter_offset[0], emitter_offset[1])
		_air.add_child(emitter)
		visual.root.tree_exiting.connect(emitter.queue_free)
		visual.emitter = emitter
		visual.base_emitter = emitter.position
	var silhouette: Texture2D = (body.texture as CanvasTexture).diffuse_texture
	if visual.silhouette != null:
		silhouette = visual.silhouette
		_set_stage(visual)
	visual.caster = _add_caster(visual.root, silhouette, offset, 1.0)
	visual.caster.blob.scale = Vector2(1.0, 0.45) * 28.0 / 32.0
	return visual


## Shows the look for the tower's level or ascendancy: its row of the sheet, its shadow, and its muzzle
## and light lifted onto the dais once it has ascended.
func _set_stage(visual: TowerVisual) -> void:
	if visual.anim.is_empty():
		return
	visual.stage = TowerLook.stage_index(visual.tower, (visual.anim["stages"] as Array).size())
	var cell: Array = visual.anim["cell"]
	visual.silhouette.region = Rect2(0, visual.stage * float(cell[1]), cell[0], cell[1])
	var lift := Vector2(0, -TowerLook.lift(visual.anim, visual.stage))
	visual.muzzle = visual.base_muzzle + lift
	visual.light.position = visual.base_light + lift
	if visual.emitter != null:
		visual.emitter.position = visual.base_emitter + lift
	_animate_tower(visual, 0.0)


## Plays the tower's idle loop, or its attack once it has fired, with a small recoil on the strike.
func _animate_tower(visual: TowerVisual, delta: float) -> void:
	if visual.anim.is_empty():
		return
	visual.idle_time += delta
	visual.flourish_wait = maxf(0.0, visual.flourish_wait - delta)
	if visual.attack_time >= 0.0:
		visual.attack_time += delta
		if visual.attack_time >= TowerLook.attack_length(visual.anim):
			visual.attack_time = -1.0
	var frame := TowerLook.frame(visual.anim, visual.stage, visual.idle_time, visual.attack_time)
	visual.body.frame = frame
	visual.glow.frame = frame
	var kick := TowerLook.recoil(visual.anim, visual.attack_time)
	var squash := Vector2(1.0 + 0.025 * kick, 1.0 - 0.035 * kick)
	visual.body.scale = squash
	visual.glow.scale = squash


## A hero standing on its tile: its sprite, a light in its colour and a shadow.
func _make_hero(tower: SimTower) -> TowerVisual:
	var visual := TowerVisual.new()
	visual.tower = tower
	visual.data_id = tower.data.id
	var element := tower.hero.element
	var color := HERO_LIGHT if element.is_empty() else sim.config.element_color(element)
	visual.colors.append(color)
	visual.shot_style = shot_style(tower.data)
	visual.root = Node2D.new()
	visual.root.position = _art_pos(tower.position) + Vector2(0, TOWER_BASE_DROP)
	_actors.add_child(visual.root)
	var path := "res://assets/art/heroes/board/%s.png" % tower.hero.id
	var texture: Texture2D = load(path) if ResourceLoader.exists(path) else _pixel
	var size := texture.get_size()
	var offset := Vector2(-size.x * 0.5, -size.y + 2.0)
	var body := Sprite2D.new()
	body.texture = texture
	body.centered = false
	body.offset = offset
	visual.root.add_child(body)
	visual.glow = Sprite2D.new()
	visual.root.add_child(visual.glow)
	visual.light_energy = 0.8
	visual.light = _point_light(color.lerp(Color.WHITE, 0.3), visual.light_energy, 90.0, 40.0)
	visual.light.position = Vector2(0, -size.y * 0.6)
	visual.root.add_child(visual.light)
	visual.muzzle = Vector2(0, -size.y * 0.6)
	visual.caster = _add_caster(visual.root, texture, offset, 1.0)
	visual.caster.blob.scale = Vector2(1.0, 0.45) * 24.0 / 32.0
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
		# A major upgrade: a pillar of light comes down on the tower as it is remade, and the ground shakes off dust.
		var top := visual.root.position + Vector2(0, -150)
		for dx in [-2.0, 0.0, 2.0]:
			_beam(top + Vector2(dx, 0), visual.root.position + Vector2(dx, -2), color.lerp(Color.WHITE, 0.5), 0.6, 2.0 if dx == 0.0 else 1.0)
		_ring(visual.root.position, color, 6.0, 60.0, 0.9, 2.0)
		_burst(visual.root.position + Vector2(0, -2), Color(0.7, 0.62, 0.5), 18, 30.0, false)
		_pulse_light(visual.root.position + visual.muzzle, color, 2.5, 160.0, 0.9)
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
		if visual != null and visual.kind != enemy.data.id:
			# A boss in a new form is drawn as that form.
			_remove_caster(visual.caster)
			visual.root.queue_free()
			_enemies.erase(enemy.id)
			visual = null
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
	visual.kind = enemy.data.id
	visual.tint = tint
	visual.last_health = enemy.health
	visual.time = randf() * 2.0
	var count: int = meta.get("frames", 4)
	for f in count:
		visual.frames.append(lit_texture(ART + "enemies/%s_%d" % [enemy.data.id, f]))
		if meta.get("gear", false):
			visual.gear_frames.append(lit_texture(ART + "enemies/%s_gear_%d" % [enemy.data.id, f]))
			visual.glow_frames.append(load(ART + "enemies/%s_gear_%d_glow.png" % [enemy.data.id, f]))
	for anim: String in ["power", "death"]:
		var spec: Dictionary = meta.get(anim, {})
		var list: Array[CanvasTexture] = visual.power_frames if anim == "power" else visual.death_frames
		for f in int(spec.get("frames", 0)):
			list.append(lit_texture(ART + "enemies/%s_%s_%d" % [enemy.data.id, anim, f]))
		if anim == "power":
			visual.power_fps = float(spec.get("fps", 10))
			visual.power_hold = int(spec.get("hold", -1))
		else:
			visual.death_fps = float(spec.get("fps", 10))
	for move in BOSS_MOVES:
		var spec: Dictionary = meta.get(String(move), {})
		if spec.is_empty():
			continue
		var list: Array[CanvasTexture] = []
		for f in int(spec.get("frames", 0)):
			list.append(lit_texture(ART + "enemies/%s_%s_%d" % [enemy.data.id, move, f]))
		visual.moves[move] = {"frames": list, "fps": float(spec.get("fps", 10)), "hold": int(spec.get("hold", -1))}
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
	if enemy.has_power and PASSIVE_POWERS.has(enemy.data.power) and visual.anim == &"walk" and enemy.downed <= 0.0:
		visual.idle_power -= delta
		if visual.idle_power <= 0.0:
			visual.idle_power = 5.0 + fposmod(float(enemy.id) * 1.618, 1.0) * 4.0
			_play_power(enemy)
	visual.body.texture = _enemy_frame(visual, delta, frame)
	if visual.gear != null:
		visual.gear.texture = visual.gear_frames[frame]
		visual.gear_glow.texture = visual.glow_frames[frame]
	visual.face_time = maxf(0.0, visual.face_time - delta)
	if visual.face_time > 0.0 or absf(pos.x - visual.last_x) > 0.01:
		var left := visual.face_left if visual.face_time > 0.0 else pos.x < visual.last_x
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
	if enemy.is_hardened():
		# Turned to stone: grey, cold and still, with the crystals bright.
		color = color.lerp(Color(0.42, 0.46, 0.55), 0.6)
	if enemy.is_phased():
		# Thinned into the air: pale and flickering.
		color = Color(color.lerp(Color(0.75, 0.95, 1.0), 0.5), 0.42 + 0.12 * sin(_elapsed * 23.0 + float(enemy.id)))
	if enemy.haste_left > 0.0:
		color = color.lerp(Color(1.0, 0.55, 0.45), 0.18 + 0.08 * pulse)
	color = _horde_tint(enemy, color, pulse)
	visual.body.modulate = color.lerp(Color(1.8, 1.8, 1.8), visual.flash * 0.7)
	if visual.gear != null:
		visual.gear.modulate = Color(1, 1, 1).lerp(Color(1.8, 1.8, 1.8), visual.flash * 0.7)


## Enemies take the colour of their element.
func _enemy_tint(enemy: SimEnemy) -> Color:
	# The six hordes are drawn in their own element's colours already.
	if enemy.element < 0 or not enemy.data.horde.is_empty():
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
	if style != &"" and _flipbook("shot_%s%s" % [style, "_heavy" if heavy else ""], node, true) != null:
		_drawn_shot_trail(node, style, hot, second, heavy)
	else:
		_procedural_shot(node, style, color, second, hot, heavy)
	if heavy:
		# A shot that will burst carries its own light, if there is room for one.
		var light := _flash_light(color.lerp(Color.WHITE, 0.2), 0.9, 34.0, 16.0)
		if light != null:
			node.add_child(light)
	return node


## What a hand-drawn shot leaves behind it: embers, spray, dust or spores.
func _drawn_shot_trail(node: Node2D, style: StringName, hot: Color, second: Color, heavy: bool) -> void:
	match style:
		&"fire":
			_shot_trail(node, 10 if heavy else 4, 0.25, Color(1, 0.85, 0.45), second, Vector2(0, -12), true)
		&"storm":
			if heavy:
				var sparks := _shot_trail(node, 8, 0.2, Color.WHITE, second, Vector2.ZERO, true)
				sparks.spread = 180.0
				sparks.initial_velocity_max = 16.0
		&"nature":
			_shot_trail(node, 6 if heavy else 2, 0.4, hot, second, Vector2(0, 14), true)
		&"water":
			_shot_trail(node, 8 if heavy else 3, 0.35, hot, second, Vector2(0, 34), false)
		&"earth":
			_shot_trail(node, 8 if heavy else 3, 0.45, Color(0.9, 0.8, 0.62, 0.8), second.lerp(Color(0.6, 0.5, 0.4), 0.5), Vector2(0, 6), false)
		&"void":
			_shot_trail(node, 8 if heavy else 4, 0.4, hot, second, Vector2.ZERO, true)


## The plain shots drawn in code, for an element with no hand-drawn picture.
func _procedural_shot(node: Node2D, style: StringName, color: Color, second: Color, hot: Color, heavy: bool) -> void:
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


## The frame an enemy shows now: its walk, its power playing out or held, or its death while it lies
## in a heap. `walk_frame` is the walk's frame for this moment.
func _enemy_frame(visual: EnemyVisual, delta: float, walk_frame: int) -> CanvasTexture:
	var enemy := visual.enemy
	visual.anim_time += delta
	if enemy.downed > 0.0:
		if visual.anim != &"fall":
			visual.anim = &"fall"
			visual.anim_time = 0.0
		if visual.death_frames.is_empty():
			return visual.frames[0]
		return visual.death_frames[mini(int(visual.anim_time * visual.death_fps), visual.death_frames.size() - 1)]
	if visual.anim == &"fall":
		# It stands up: a grunt's power is its rise.
		visual.anim = &"walk"
	visual.talk_left = maxf(0.0, visual.talk_left - delta)
	if visual.anim == &"move":
		var shown := _move_frame(visual)
		if shown != null:
			return shown
		visual.anim = &"walk"
	if visual.anim == &"walk" and not visual.moves.is_empty():
		return _boss_walk_frame(visual, walk_frame)
	var count := visual.power_frames.size()
	if count == 0 or visual.anim == &"walk":
		return visual.frames[walk_frame]
	var step := int(visual.anim_time * visual.power_fps)
	var lasting := enemy.is_phased() or enemy.is_hardened() or enemy.is_submerged() or _is_charging(enemy)
	if visual.anim == &"power":
		if visual.power_hold >= 0 and step >= visual.power_hold:
			if lasting:
				return visual.power_frames[visual.power_hold]
			# It wears off: play back to the start.
			visual.anim = &"unpower"
			visual.anim_time = 0.0
			return visual.power_frames[visual.power_hold]
		if step >= count:
			visual.anim = &"walk"
			return visual.frames[walk_frame]
		return visual.power_frames[step]
	# &"unpower"
	var back := (visual.power_hold if visual.power_hold >= 0 else count - 1) - step
	if back < 0:
		visual.anim = &"walk"
		return visual.frames[walk_frame]
	return visual.power_frames[back]


## The frame of the boss move playing now, or null once it has played out.
func _move_frame(visual: EnemyVisual) -> CanvasTexture:
	var spec: Dictionary = visual.moves.get(visual.move, {})
	if spec.is_empty():
		return null
	var frames: Array[CanvasTexture] = spec["frames"]
	var step := int(visual.anim_time * float(spec["fps"]))
	var hold: int = spec["hold"]
	if visual.move_hold:
		return frames[mini(step, hold if hold >= 0 else frames.size() - 1)]
	if step >= frames.size():
		return null
	return frames[step]


## A boss between moves: it works its jaw while it speaks, and stands breathing when it is not moving.
func _boss_walk_frame(visual: EnemyVisual, walk_frame: int) -> CanvasTexture:
	var enemy := visual.enemy
	if visual.talk_left > 0.0 and visual.moves.has(&"talk"):
		var talk: Array[CanvasTexture] = visual.moves[&"talk"]["frames"]
		# Standing still it still talks, at the pace of speech rather than of its feet.
		var at := walk_frame if enemy.speed() > 0.0 else int(visual.anim_time * 10.0)
		return talk[at % talk.size()]
	if (enemy.speed() <= 0.0 or enemy.has_status(&"stun")) and visual.moves.has(&"idle"):
		var idle: Array[CanvasTexture] = visual.moves[&"idle"]["frames"]
		return idle[int(visual.anim_time * float(visual.moves[&"idle"]["fps"])) % idle.size()]
	return visual.frames[walk_frame]


## Plays one of a boss's moves (BOSS_MOVES) from its first frame. With `hold`, a move that has a hold
## frame stays on it until release_boss_move(). Returns how long the move takes, 0 if the boss cannot
## (no art for that move, or it is lying in a heap).
func play_boss_move(enemy: SimEnemy, move: StringName, hold := false) -> float:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	if visual == null or visual.kind != enemy.data.id or not visual.moves.has(move) or enemy.downed > 0.0:
		return 0.0
	visual.anim = &"move"
	visual.move = move
	visual.move_hold = hold and int(visual.moves[move]["hold"]) >= 0
	visual.anim_time = 0.0
	var spec: Dictionary = visual.moves[move]
	return float((spec["frames"] as Array).size()) / float(spec["fps"])


## Lets a held move (a guard) play out and go back to walking.
func release_boss_move(enemy: SimEnemy, move: StringName = &"") -> void:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	if visual != null and visual.anim == &"move" and (move.is_empty() or visual.move == move):
		visual.anim = &"walk"
		visual.move_hold = false


## The boss works its jaw for this many seconds (it is speaking).
func set_boss_talking(enemy: SimEnemy, seconds: float) -> void:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	if visual != null:
		visual.talk_left = maxf(visual.talk_left, seconds)


## The move a boss is showing now (&"" while it walks), for tests and the director.
func boss_move_of(enemy: SimEnemy) -> StringName:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	return visual.move if visual != null and visual.anim == &"move" else &""


## True when this kind of enemy has art for that boss move.
static func has_boss_move(enemy_id: StringName, move: StringName) -> bool:
	return enemy_info(enemy_id).has(String(move))


## Starts an enemy's power animation from its first frame.
func _play_power(enemy: SimEnemy) -> void:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	if visual != null and not visual.power_frames.is_empty():
		visual.anim = &"power"
		visual.anim_time = 0.0


## A killed enemy plays out its death where it fell, then fades.
func _leave_corpse(enemy: SimEnemy) -> void:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	if visual == null or visual.death_frames.is_empty():
		return
	if _corpses.size() >= MAX_CORPSES:
		_corpses.pop_front().sprite.queue_free()
	var corpse := Corpse.new()
	corpse.frames = visual.death_frames
	corpse.fps = visual.death_fps
	corpse.sprite = Sprite2D.new()
	corpse.sprite.texture = visual.death_frames[0]
	corpse.sprite.centered = false
	corpse.sprite.offset = visual.body.offset
	corpse.sprite.flip_h = visual.body.flip_h
	corpse.sprite.modulate = visual.tint
	corpse.sprite.position = visual.root.position
	corpse.sprite.scale = Vector2.ONE * visual.size_scale
	_actors.add_child(corpse.sprite)
	_corpses.append(corpse)


func _advance_corpses(delta: float) -> void:
	var left: Array[Corpse] = []
	for corpse in _corpses:
		corpse.time += delta
		var played := float(corpse.frames.size()) / corpse.fps
		if corpse.time >= played + CORPSE_LINGER:
			corpse.sprite.queue_free()
			continue
		corpse.sprite.texture = corpse.frames[mini(int(corpse.time * corpse.fps), corpse.frames.size() - 1)]
		if corpse.time > played:
			corpse.sprite.modulate.a = 1.0 - (corpse.time - played) / CORPSE_LINGER
		left.append(corpse)
	_corpses = left


## What a power looks like on the board, on top of the enemy's own animation.
func _on_enemy_power(enemy: SimEnemy, power: StringName, targets: Array) -> void:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	var feet := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP)
	var tall := visual.size.y * 0.55 if visual != null else 20.0
	var chest := feet + Vector2(0, -tall * 0.6)
	var radius := enemy.data.power_radius / SCALE
	match power:
		&"fall":
			# The bones come apart in a puff of grave dust.
			_burst(feet + Vector2(0, -4), Color(0.75, 0.72, 0.66), 16, 18.0, false)
			_ring(feet, Color(0.55, 0.45, 0.75), 2.0, 10.0, 0.35)
		&"rise":
			_play_power(enemy)
			_ring(feet, NECRO, 12.0, 2.0, 0.6, 1.0)
			_burst(feet + Vector2(0, -6), NECRO, 18, 20.0)
			_sparks(chest, NECRO.lerp(Color.WHITE, 0.4), 8, 12.0)
			_pulse_light(feet + Vector2(0, -8), NECRO, 1.6, 40.0, 0.6)
		&"phase":
			_play_power(enemy)
			_burst(chest, Color(0.7, 0.95, 1.0), 14, 16.0)
			_sparks(chest, Color(0.85, 1.0, 1.0), 7, 10.0)
		&"war_cry":
			_play_power(enemy)
			# A blood-red shock wave out to the edge of the cry, and every ally it reached flares.
			_ring(chest, Color(0.95, 0.25, 0.15), 4.0, radius, 0.55, 2.0)
			_ring(chest, Color(1.0, 0.6, 0.35), 2.0, radius * 0.7, 0.4)
			for ally: SimEnemy in targets:
				if ally != enemy:
					_sparks(_art_pos(ally.position) + Vector2(0, ENEMY_DROP - 8), Color(1.0, 0.45, 0.3), 5, 7.0)
			_pulse_light(chest, Color(1.0, 0.3, 0.15), 1.4, radius * 1.2, 0.5)
		&"mend":
			_play_power(enemy)
			var hand := feet + Vector2(0, -tall * 1.05)
			_ring(feet, HEAL, 3.0, radius, 0.8, 1.0)
			_burst(hand, HEAL.lerp(Color.WHITE, 0.4), 16, 14.0)
			for ally: SimEnemy in targets:
				var at := _art_pos(ally.position) + Vector2(0, ENEMY_DROP - 10)
				if ally != enemy:
					_beam(hand, at, HEAL, 0.45)
				_sparks(at, HEAL.lerp(Color.WHITE, 0.3), 6, 8.0)
			_pulse_light(hand, HEAL, 1.6, radius, 0.7)
		&"harden":
			_play_power(enemy)
			_burst(feet + Vector2(0, -6), Color(0.6, 0.6, 0.62), 18, 20.0, false)
			_ring(feet, Color(0.55, 0.85, 1.0), 14.0, 4.0, 0.4, 2.0)
			_sparks(chest, Color(0.6, 0.9, 1.0), 8, 14.0)
		&"shield":
			_ring(chest, WARD, 3.0, 13.0, 0.35)
		&"block":
			_play_power(enemy)
			# The ward takes the blow and shatters in gold and blue.
			var side := -1.0 if visual != null and visual.body.flip_h else 1.0
			var at := chest + Vector2(side * 7.0, 0)
			_ring(at, WARD.lerp(Color.WHITE, 0.5), 2.0, 14.0, 0.3, 2.0)
			_burst(at, WARD, 20, 26.0)
			_sparks(at, Color(1.0, 0.85, 0.4), 9, 12.0)
			_pulse_light(at, WARD, 1.5, 36.0, 0.25)
		&"breath":
			_play_power(enemy)
			if not targets.is_empty():
				_breathe_fire(enemy, visual, targets[0] as SimTower)
		_:
			_on_horde_power(enemy, power, targets, feet, chest, radius, tall)


const NECRO := Color(0.62, 0.35, 1.0)
# The six hordes' colours: brine, ochre stone, the hollow's violet dark, ember, lightning and briar.
const TIDE := Color(0.32, 0.78, 0.82)
const STONE := Color(0.9, 0.66, 0.34)
const HOLLOW := Color(0.5, 0.25, 0.85)
const FLAME := Color(1.0, 0.45, 0.12)
const SKY := Color(0.62, 0.82, 1.0)
const GROVE := Color(0.5, 0.85, 0.3)
const RIME := Color(0.78, 0.94, 1.0)
## Powers that never fire as an event: their animation is played now and then to show them.
const PASSIVE_POWERS: Array[StringName] = [&"bulwark", &"steadfast", &"hush", &"remedy", &"swarm", &"fireborn",
		&"stalk", &"momentum", &"facets"]
const HEAL := Color(0.45, 1.0, 0.55)
const WARD := Color(0.55, 0.8, 1.0)


func _is_charging(enemy: SimEnemy) -> bool:
	return enemy.has_power and enemy.data.power == &"charge" and enemy.power_left > 0.0


## How the six hordes' powers colour the body: dim and sunk under the water, a pale stalker, the
## faded green of the raised dead, an iced shell, a charge's heat and a juggernaut's glowing brass.
func _horde_tint(enemy: SimEnemy, color: Color, pulse: float) -> Color:
	if enemy.is_submerged():
		color = Color(color.lerp(Color(0.12, 0.3, 0.38), 0.6), 0.45)
	if enemy.has_power and enemy.data.power == &"stalk":
		color = Color(color.darkened(0.25), 0.6 + 0.15 * pulse)
	if enemy.raised:
		color = color.lerp(Color(0.55, 0.75, 0.55), 0.45).darkened(0.1)
	if enemy.shell > 0.0:
		color = color.lerp(RIME, 0.3)
	if _is_charging(enemy):
		color = color.lerp(Color(1.0, 0.75, 0.45), 0.25 + 0.15 * pulse)
	if enemy.momentum > 0.0 and enemy.data.power_limit > 0.0:
		color = color.lerp(Color(1.0, 0.55, 0.2), 0.35 * enemy.momentum / enemy.data.power_limit)
	if enemy.spur > 0.0:
		color = color.lerp(SKY, 0.25 * pulse)
	return color


## The six hordes' powers on the board, on top of the creature's own power animation.
func _on_horde_power(enemy: SimEnemy, power: StringName, targets: Array, feet: Vector2, chest: Vector2,
		radius: float, tall: float) -> void:
	match power:
		&"douse":
			_play_power(enemy)
			_ring(feet, TIDE, 3.0, radius, 0.6, 1.0)
			_burst(chest, TIDE.lerp(Color.WHITE, 0.35), 18, 16.0, false)
			for ally: SimEnemy in targets:
				var at := _art_pos(ally.position) + Vector2(0, ENEMY_DROP - 8)
				_burst(at, Color(0.7, 0.9, 1.0), 8, 8.0, false)
		&"net":
			_play_power(enemy)
			for tower: SimTower in targets:
				var at := _art_pos(tower.position) + Vector2(0, -8)
				_beam(chest, at, Color(0.75, 0.7, 0.55), 0.5)
				_ring(at, Color(0.8, 0.75, 0.6), 12.0, 5.0, 0.45, 1.0)
		&"submerge":
			_play_power(enemy)
			_ring(feet, TIDE, 2.0, 12.0, 0.5)
			_burst(feet + Vector2(0, -3), TIDE.lerp(Color.WHITE, 0.4), 16, 12.0, false)
		&"fog":
			_play_power(enemy)
			_ring(chest, Color(0.75, 0.82, 0.85), 4.0, radius, 0.9, 2.0)
			for tower: SimTower in targets:
				_burst(_art_pos(tower.position) + Vector2(0, -10), Color(0.8, 0.85, 0.88), 14, 12.0, false)
		&"rime_shell":
			_play_power(enemy)
			_ring(chest, RIME, 14.0, 4.0, 0.45, 2.0)
			_sparks(chest, RIME, 9, 13.0)
			_pulse_light(chest, RIME, 1.2, 30.0, 0.5)
		&"shell_break":
			_burst(chest, RIME, 26, 22.0)
			_sparks(chest, Color.WHITE, 8, 12.0)
		&"accrete":
			_play_power(enemy)
			_burst(feet + Vector2(0, -4), STONE.darkened(0.3), 14, 12.0, false)
			_sparks(chest, STONE, 6, 9.0)
		&"charge":
			_play_power(enemy)
			_burst(feet, STONE.darkened(0.35), 20, 18.0, false)
			_ring(feet, STONE, 3.0, 14.0, 0.35, 2.0)
		&"eclipse":
			_play_power(enemy)
			_ring(chest, HOLLOW, radius, 4.0, 0.8, 2.0)
			for tower: SimTower in targets:
				var at := _art_pos(tower.position) + Vector2(0, -10)
				_beam(at, chest, HOLLOW.lerp(Color.BLACK, 0.3), 0.6, 2.0)
		&"raise":
			_play_power(enemy)
			_ring(feet, NECRO, radius * 0.6, 3.0, 0.7, 1.0)
			_pulse_light(chest, NECRO, 1.6, radius, 0.7)
			for child: SimEnemy in targets:
				var at := _art_pos(child.position) + Vector2(0, ENEMY_DROP)
				_beam(chest, at + Vector2(0, -6), NECRO, 0.5)
				_burst(at + Vector2(0, -4), Color(0.5, 0.45, 0.4), 14, 14.0, false)
				_ring(at, NECRO, 10.0, 2.0, 0.5)
		&"wail":
			_ring(chest, HOLLOW.lerp(Color.WHITE, 0.4), 4.0, radius, 0.7, 2.0)
			_ring(chest, HOLLOW, 2.0, radius * 0.75, 0.55)
			_pulse_light(chest, HOLLOW, 1.8, radius, 0.6)
			for tower: SimTower in targets:
				_sparks(_art_pos(tower.position) + Vector2(0, -12), HOLLOW.lerp(Color.WHITE, 0.4), 6, 9.0)
		&"devour":
			_play_power(enemy)
			for dead: SimEnemy in targets:
				var at := _art_pos(dead.position) + Vector2(0, ENEMY_DROP - 6)
				_beam(at, chest, HOLLOW, 0.5, 2.0)
				_burst(at, HOLLOW.darkened(0.3), 12, 10.0)
			_pulse_light(chest, HOLLOW, 1.4, 36.0, 0.5)
		&"smoke":
			_burst(chest, Color(0.45, 0.42, 0.4), 12, 12.0, false)
		&"glass_ward":
			_play_power(enemy)
			_pulse_light(chest, Color(1.0, 0.7, 0.35), 1.3, radius, 0.5)
			for ally: SimEnemy in targets:
				var at := _art_pos(ally.position) + Vector2(0, ENEMY_DROP - 10)
				_beam(chest, at, Color(1.0, 0.75, 0.4), 0.45)
				_ring(at, Color(1.0, 0.82, 0.55), 2.0, 11.0, 0.35)
		&"meltdown":
			_play_power(enemy)
			_burst(feet + Vector2(0, -6), FLAME, 22, 16.0)
			_sparks(chest, Color(1.0, 0.85, 0.4), 8, 12.0)
			_pulse_light(chest, FLAME, 1.5, 40.0, 0.6)
		&"tailwind":
			_play_power(enemy)
			_ring(chest, SKY, 3.0, radius, 0.5, 1.0)
			for ally: SimEnemy in targets:
				var at := _art_pos(ally.position) + Vector2(0, ENEMY_DROP - 6)
				_burst(at, SKY.lerp(Color.WHITE, 0.4), 6, 10.0, false)
		&"static":
			for tower: SimTower in targets:
				var at := _art_pos(tower.position) + Vector2(0, -10)
				_beam(chest, at, Color(0.8, 0.92, 1.0), 0.35, 2.0)
				_sparks(at, SKY.lerp(Color.WHITE, 0.5), 10, 10.0)
				_pulse_light(at, SKY, 1.6, 30.0, 0.3)
		&"spur":
			_play_power(enemy)
			_sparks(feet + Vector2(0, -4), SKY, 8, 10.0)
		&"gust":
			_play_power(enemy)
			_ring(chest, SKY.lerp(Color.WHITE, 0.3), 4.0, radius, 0.5, 2.0)
			_burst(chest, Color(0.85, 0.92, 1.0), 20, radius * 0.6, false)
		&"sow":
			_play_power(enemy)
			_burst(feet + Vector2(0, -2), GROVE.darkened(0.3), 10, 10.0, false)
		&"sprout":
			for child: SimEnemy in targets:
				var at := _art_pos(child.position) + Vector2(0, ENEMY_DROP)
				_burst(at + Vector2(0, -3), GROVE, 14, 12.0, false)
				_ring(at, GROVE, 2.0, 10.0, 0.45)
		&"bound":
			_play_power(enemy)
			if not targets.is_empty():
				var from := _art_pos(targets[0] as Vector2) + Vector2(0, ENEMY_DROP)
				_burst(from, GROVE.darkened(0.4), 12, 10.0, false)
				_beam(from + Vector2(0, -tall * 0.5), chest, GROVE.lerp(Color.WHITE, 0.3), 0.35)
			_burst(feet, GROVE.darkened(0.3), 12, 12.0, false)
		&"grow":
			_play_power(enemy)
			_burst(chest, GROVE, 16, 16.0, false)
			_pulse_light(chest, GROVE, 1.2, 34.0, 0.5)


## A stream of dragon fire from the Warden's jaws to the tower, which burns while it is silenced.
func _breathe_fire(enemy: SimEnemy, visual: EnemyVisual, tower: SimTower) -> void:
	var feet := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP)
	var target := _art_pos(tower.position) + Vector2(0, -10)
	var side := 1.0 if target.x >= feet.x else -1.0
	var size := visual.size if visual != null else Vector2(60, 60)
	if visual != null:
		# It turns on the tower to breathe.
		visual.face_left = side < 0.0
		visual.face_time = float(visual.power_frames.size()) / visual.power_fps + 0.3
	# Where the jaws are in the hand-drawn dragon's strike (feet at 83,112 in a 166x144 frame).
	var mouth := feet + Vector2(side * size.x * 0.3, -size.y * 0.32)
	# The jaws open on the fifth frame of the strike.
	var delay := 4.0 / (visual.power_fps if visual != null else 12.0)
	get_tree().create_timer(delay).timeout.connect(func() -> void:
		_beam(mouth, target, Color(1.0, 0.45, 0.1), 0.5, 4.0)
		_beam(mouth, target, Color(1.0, 0.85, 0.4), 0.35, 1.0)
		_pulse_light(mouth, Color(1.0, 0.5, 0.15), 2.0, 70.0, 0.5))
	for i in 9:
		var t := float(i) / 8.0
		var at := mouth.lerp(target, t)
		get_tree().create_timer(delay + t * 0.2).timeout.connect(func() -> void:
			_burst(at, Color(1.0, 0.75 - t * 0.4, 0.2), 18 + i * 3, 12.0 + t * 18.0)
			if i == 8:
				_burst(target, Color(1.0, 0.4, 0.1), 40, 30.0)
				_ring(target, Color(1.0, 0.45, 0.1), 3.0, 22.0, 0.45, 2.0)
				_pulse_light(target, Color(1.0, 0.45, 0.15), 2.4, 70.0, 0.8))


## A short glow that fades: a rise, a cry, a healing, a blocked blow.
func _pulse_light(at: Vector2, color: Color, energy: float, radius: float, life: float) -> void:
	var light := _flash_light(color, energy, maxf(16.0, radius), 14.0)
	if light == null:
		return
	light.position = at
	_air.add_child(light)
	var tween := create_tween()
	tween.tween_property(light, "energy", 0.0, life)
	tween.tween_callback(func() -> void: _release_light(light))


func _beam(from: Vector2, to: Vector2, color: Color, life: float, width := 1.0) -> void:
	if _fx.size() >= MAX_FX:
		return
	var fx := Fx.new()
	fx.ring = false
	fx.at = from
	fx.beam_to = to
	fx.color = color
	fx.life = life
	fx.width = width
	_fx.append(fx)


# ------------------------------------------------------------------ effects

## A tower strikes: its attack plays (gather, flare, settle) and its crown throws off a flourish of its element.
func _on_tower_attacked(tower: SimTower, _target: SimEnemy) -> void:
	var visual: TowerVisual = _towers.get(tower.id)
	if visual == null or visual.anim.is_empty():
		return
	# A tower that fires faster than its attack plays starts again from the gather, not mid-flare.
	if visual.attack_time < 0.0 or visual.attack_time > TowerLook.attack_length(visual.anim) * 0.5:
		visual.attack_time = 0.0
	visual.pulse = maxf(visual.pulse, 1.0)
	if visual.flourish_wait > 0.0:
		return
	visual.flourish_wait = 0.4
	_attack_flourish(visual)


## The element's own flourish where the tower's crown releases its shot.
func _attack_flourish(visual: TowerVisual) -> void:
	var at := visual.root.position + visual.muzzle
	var base := visual.root.position
	var color: Color = visual.colors[0]
	var big := visual.stage >= 3
	match visual.shot_style:
		&"fire":
			_burst(at + Vector2(0, -2), Color(1.0, 0.62, 0.2), 12 if big else 7, 30.0)
			_pulse_light(at, Color(1.0, 0.6, 0.25), 1.6, 70.0, 0.25)
		&"storm":
			for k in 2 + int(big):
				var a := randf() * TAU
				var mid := at + Vector2(cos(a), sin(a)) * 5.0 + Vector2(randf_range(-2, 2), randf_range(-2, 2))
				var end := at + Vector2(cos(a), sin(a)) * randf_range(9.0, 14.0)
				_beam(at, mid, Color(0.8, 0.9, 1.0), 0.12)
				_beam(mid, end, Color(0.6, 0.75, 1.0), 0.12)
			_pulse_light(at, Color(0.75, 0.85, 1.0), 1.8, 70.0, 0.15)
		&"water":
			_ring(at, Color(0.5, 0.85, 1.0), 2.0, 11.0 if big else 8.0, 0.3)
			_burst(at, Color(0.55, 0.85, 1.0), 6, 22.0, false)
		&"nature":
			_burst(at, Color(0.55, 0.85, 0.3), 7 if big else 5, 20.0, false)
			_sparks(at, Color(0.8, 1.0, 0.5), 4, 8.0)
		&"earth":
			_ring(base, Color(0.75, 0.6, 0.4), 4.0, 16.0 if big else 12.0, 0.35)
			_burst(base + Vector2(0, -1), Color(0.6, 0.5, 0.38), 6, 18.0, false)
		&"void":
			# The void pulls in before it lets go: a ring closing on the crown.
			_ring(at, Color(0.65, 0.4, 1.0), 14.0 if big else 11.0, 2.0, 0.28)
			_sparks(at, Color(0.8, 0.6, 1.0), 5, 9.0)
		_:
			_sparks(at, color.lerp(Color.WHITE, 0.3), 5, 8.0)


func _on_chain_fired(tower: SimTower, points: PackedVector2Array) -> void:
	var visual: TowerVisual = _towers.get(tower.id)
	var color := HERO_LIGHT if tower.data.elements.is_empty() else sim.config.element_color(tower.data.elements[tower.data.elements.size() - 1])
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
			var hit_at := at + Vector2(0, ENEMY_DROP - 5)
			if style == &"" or _play_fx("hit_" + String(style), hit_at) == null:
				_sparks(hit_at, color, 5, 7.0)
		return
	var radius := shot.splash_radius / SCALE
	if style != &"" and _play_fx("blast_" + String(style), at, radius / BLAST_RADIUS) != null:
		# The drawn blast carries its own debris; a faint ring still shows how far it reached.
		_ring(at, Color(color, 0.55), radius * 0.6, radius, 0.35)
	else:
		_procedural_blast(at, style, color, radius)
	var light := _flash_light(color, 1.8, radius * 1.6, 12.0)
	if light != null:
		light.position = at
		_air.add_child(light)
		var tween := create_tween()
		tween.tween_property(light, "energy", 0.0, 0.3)
		tween.tween_callback(func() -> void: _release_light(light))


func _procedural_blast(at: Vector2, style: StringName, color: Color, radius: float) -> void:
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


func _on_enemy_killed(enemy: SimEnemy, _killer: SimTower, _bounty: int) -> void:
	_leave_corpse(enemy)
	var visual: EnemyVisual = _enemies.get(enemy.id)
	var color := visual.tint if visual != null else Color(0.8, 0.85, 0.9)
	var at := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP - 4)
	if not enemy.data.tags.has(&"boss"):
		var puff := _play_fx("death_puff", at + Vector2(0, -8))
		if puff != null:
			puff.node.modulate = color.lerp(Color.WHITE, 0.55)
			_burst(at, color, 6, 18.0, false)
		else:
			_burst(at, color, 14, 22.0, false)
			_ring(at, color.lerp(Color.WHITE, 0.4), 2.0, 9.0, 0.25)
		return
	var boss_puff := _play_fx("death_puff", at + Vector2(0, -20), 2.5)
	if boss_puff != null:
		boss_puff.node.modulate = color.lerp(Color.WHITE, 0.45)
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


## The boss throws off its form: a wall of its colour, a flash, and the new form where it stood.
func _on_enemy_transformed(enemy: SimEnemy, _from: EnemyData) -> void:
	var at := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP - 40)
	var color := Color(0.7, 0.3, 1.0)
	_burst(at, color, 60, 70.0)
	_burst(at, Color(1.0, 0.3, 0.25), 30, 40.0, false)
	_ring(at, color.lerp(Color.WHITE, 0.4), 6.0, 70.0, 0.9, 2.0)
	_ring(at, Color.WHITE, 4.0, 40.0, 0.5)
	_pulse_light(at, color, 3.0, 220.0, 1.6)


## The beaten king runs for his citadel: a trail of void where he went.
func _on_boss_fled(enemy: SimEnemy) -> void:
	var at := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP - 30)
	_burst(at, Color(0.55, 0.25, 0.9), 30, 30.0)
	_ring(at, Color(0.8, 0.6, 1.0), 4.0, 30.0, 0.6)


## The citadel's spires strike at the army: violet lightning from the black sun to each unit hit.
func _on_citadel_struck(_structure: SimEnemy, targets: Array[SimAlly]) -> void:
	var from := _art_pos(citadel.bolt_origin()) if citadel != null else _art_pos(_structure.position)
	for ally in targets:
		var to := _art_pos(ally.position) + Vector2(0, ENEMY_DROP - 10)
		_beam(from, to, Color(0.75, 0.45, 1.0), 0.28, 2.0)
		_ring(to, Color(0.85, 0.6, 1.0), 2.0, 12.0, 0.3)
		_sparks(to, Color(0.8, 0.55, 1.0), 6, 10.0)
	_pulse_light(from, Color(0.6, 0.3, 1.0), 1.8, 160.0, 0.3)


func _on_structure_destroyed(structure: SimEnemy) -> void:
	if citadel == null or citadel.structure != structure:
		return
	# Every gate and the keep go up in fire as it falls.
	var top := citadel.position
	for k in 14:
		var at := top + Vector2(60.0 + randf() * 300.0, 120.0 + randf() * 560.0)
		_burst(at, Color(1.0, 0.45 + randf() * 0.3, 0.2), 20, 60.0, false)
		_ring(at, Color(1.0, 0.8, 0.5), 4.0, 30.0 + randf() * 30.0, 0.8)
	_pulse_light(_art_pos(citadel.bolt_origin()), Color(1.0, 0.5, 0.25), 4.0, 600.0, 2.5)


func _on_ally_attacked(ally: SimAlly, target: SimEnemy) -> void:
	if target == null:
		return
	var at := _art_pos(target.position) + Vector2(0, ENEMY_DROP - 8)
	if target.data.structure and citadel != null:
		# A blow on the citadel lands on the gate in front of the unit.
		at = _art_pos(ally.position) + Vector2(14, -8)
	var color := Color(1.0, 0.85, 0.6)
	if not ally.data.element.is_empty():
		color = sim.config.element_color(ally.data.element).lerp(Color.WHITE, 0.3)
	if ally.data.is_ranged():
		_beam(_art_pos(ally.position) + Vector2(0, -14), at, color, 0.12, 1.0)
	_sparks(at, color, 3 if ally.data.splash_radius <= 0.0 else 8, 6.0 + ally.data.splash_radius * 0.1)


func _on_ally_healed(ally: SimAlly, healed: Array[SimAlly]) -> void:
	var from := _art_pos(ally.position) + Vector2(0, -16)
	for other in healed:
		if other != ally:
			_beam(from, _art_pos(other.position) + Vector2(0, -12), Color(1.0, 0.92, 0.6), 0.35)
	_ring(from + Vector2(0, 12), Color(1.0, 0.9, 0.55), 3.0, 18.0, 0.5)


func _on_allies_mustered(squad: Array[SimAlly]) -> void:
	if squad.is_empty():
		return
	var at := _art_pos(squad[0].position) + Vector2(0, ENEMY_DROP)
	_ring(at, Color(1.0, 0.85, 0.45), 4.0, 26.0, 0.6, 2.0)
	_burst(at, Color(1.0, 0.8, 0.4), 16, 26.0)


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
			_play_fx("blast_" + String(skill.element), at, radius / BLAST_RADIUS)
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


## Starts a hand-drawn effect strip on `parent`. Null when that strip has not been drawn.
func _flipbook(fx_name: String, parent: Node2D, loop: bool) -> Flipbook:
	var meta := fx_info(fx_name)
	if meta.is_empty():
		return null
	var book := Flipbook.new()
	book.frames = int(meta.get("frames", 1))
	book.fps = float(meta.get("fps", 12))
	book.loop = loop
	if loop:
		# Shots in flight do not all flicker in step.
		book.age = randf() * book.frames / book.fps
	book.node = Node2D.new()
	parent.add_child(book.node)
	var layers := [[fx_name, _unshaded]]
	if meta.get("glow", false):
		layers.append([fx_name + "_glow", _additive])
	for layer: Array in layers:
		var sprite := Sprite2D.new()
		sprite.texture = load(ART + "fx/%s.png" % layer[0])
		sprite.hframes = book.frames
		sprite.material = layer[1]
		book.node.add_child(sprite)
		book.sprites.append(sprite)
	_flipbooks.append(book)
	return book


## Plays a hand-drawn effect once at a point in the air, scaled (blasts are drawn for BLAST_RADIUS).
func _play_fx(fx_name: String, at: Vector2, scale_by := 1.0) -> Flipbook:
	if _flipbooks.size() >= MAX_FX:
		return null
	var book := _flipbook(fx_name, _air, false)
	if book != null:
		book.node.position = at
		book.node.scale = Vector2.ONE * clampf(scale_by, 0.5, 4.0)
	return book


func _advance_flipbooks(delta: float) -> void:
	var live: Array[Flipbook] = []
	for book in _flipbooks:
		if not is_instance_valid(book.node) or book.node.is_queued_for_deletion():
			continue
		book.age += delta
		var frame := int(book.age * book.fps)
		if not book.loop and frame >= book.frames:
			book.node.queue_free()
			continue
		for sprite in book.sprites:
			sprite.frame = frame % book.frames
		live.append(book)
	_flipbooks = live


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
	for visual: TowerVisual in _towers.values():
		_draw_tower_hexes(visual)
		if visual.tower.silenced > 0.0:
			# A silenced tower smoulders until it can fire again.
			var salt := float(visual.tower.id) * 2.3
			for i in 6:
				var rise := fposmod(_elapsed * 1.5 + salt + float(i) * 0.17, 1.0)
				var at := visual.root.position + Vector2(sin(salt + float(i) * 2.2) * 7.0, -4.0 - rise * 26.0)
				var flame := Color(1.0, 0.92, 0.55).lerp(Color(0.85, 0.2, 0.05), rise)
				_marks.draw_rect(Rect2(at.floor(), Vector2(1.0, 2.0 if rise < 0.4 else 1.0)), Color(flame, 1.0 - rise * 0.7))
	for fx in _fx:
		var fade := 1.0 - fx.age / fx.life
		var spread := 1.0 - fade * fade
		if fx.beam_to != Vector2.INF:
			# A thread of light that runs out from the start and fades.
			var reach := fx.at.lerp(fx.beam_to, minf(1.0, spread * 2.0))
			_marks.draw_line(fx.at, reach, Color(fx.color, fade * 0.9), fx.width)
			_dot(_marks, reach, Color(fx.color.lerp(Color.WHITE, 0.6), fade))
		elif fx.ring:
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
	var feet := visual.root.position
	var half := visual.size.x * 0.32
	var tall := visual.size.y * 0.7
	var head := feet + Vector2(0, -tall - 3.0)
	var salt := float(enemy.id) * 1.37
	_draw_power_marks(visual, feet, half, tall, salt)
	if enemy.statuses.is_empty() and not healing:
		return
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


## What an enemy's power looks like while it lasts: a grunt that will rise has a cold violet fire in
## its skull and smoulders while it lies in a heap, a warded dwarf's rune shield hangs in front of
## it, a war cry leaves red streaks at the heels and stone glints with crystal.
func _draw_power_marks(visual: EnemyVisual, feet: Vector2, half: float, tall: float, salt: float) -> void:
	var enemy := visual.enemy
	var side := -1.0 if visual.body.flip_h else 1.0
	if enemy.downed > 0.0:
		for i in 4:
			var rise := fposmod(_elapsed * 1.1 + salt + float(i) * 0.25, 1.0)
			var at := feet + Vector2(sin(salt * 2.0 + float(i) * 1.9) * half * 0.8, -1.0 - rise * tall * 0.5)
			_dot(_marks, at, Color(NECRO.lerp(Color.WHITE, 0.3 * (1.0 - rise)), 1.0 - rise))
		return
	if enemy.has_power and enemy.data.power == &"rise" and not enemy.risen:
		# Eyes that burn: this one will get up again.
		var flicker := 0.7 + 0.3 * sin(_elapsed * 11.0 + salt)
		var eye := (feet + Vector2(side * visual.size.x * 0.035, -visual.size.y * 0.42)).floor()
		_dot(_marks, eye, Color(NECRO.lerp(Color.WHITE, 0.35), flicker))
		_dot(_marks, eye + Vector2(0, -1 - int(fposmod(_elapsed * 4.0 + salt, 2.0))), Color(NECRO, flicker * 0.5))
	if enemy.shield_up:
		# A curved rune ward held up in front of it, in gold and ice blue.
		var center := feet + Vector2(side * (half + 2.0), -tall * 0.45)
		var throb := 0.55 + 0.25 * sin(_elapsed * 4.0 + salt)
		for i in 7:
			var y := (float(i) - 3.0) * 2.0
			var at := center + Vector2(side * (1.5 - absf(float(i) - 3.0) * 0.5), y)
			_dot(_marks, at, Color(WARD.lerp(Color.WHITE, 0.3), throb))
			if i % 3 == 1:
				_dot(_marks, at + Vector2(-side, 0), Color(1.0, 0.82, 0.4, throb * 0.8))
	if enemy.haste_left > 0.0:
		for i in 3:
			var trail := fposmod(_elapsed * 3.0 + salt + float(i) * 0.33, 1.0)
			var at := feet + Vector2(-side * (half * 0.6 + trail * 6.0), -1.0 - float(i) * 3.0)
			_dot(_marks, at, Color(1.0, 0.3, 0.2, 0.9 * (1.0 - trail)))
	if enemy.is_hardened():
		for i in 3:
			var glint := 0.5 + 0.5 * sin(_elapsed * 7.0 + salt + float(i) * 2.0)
			var at := feet + Vector2((float(i) - 1.0) * half * 0.8, -tall * (0.3 + 0.2 * float(i % 2)))
			_dot(_marks, at, Color(0.7, 0.95, 1.0, glint))
	_draw_horde_marks(visual, feet, half, tall, salt, side)


## The hordes' lasting powers: an ice shell, a lent rune of armour, the Menhir's stillness, a
## Greenwitch's blessing, a pack's thorns, a charge's dust and the raised dead's grave light. Aura
## bearers show the edge of their reach.
func _draw_horde_marks(visual: EnemyVisual, feet: Vector2, half: float, tall: float, salt: float, side: float) -> void:
	var enemy := visual.enemy
	if enemy.shell > 0.0:
		for i in 6:
			var angle := TAU * float(i) / 6.0 + salt
			var at := feet + Vector2(cos(angle) * (half + 2.0), -tall * 0.45 + sin(angle) * tall * 0.4)
			_dot(_marks, at, Color(RIME, 0.6 + 0.3 * sin(_elapsed * 5.0 + float(i))))
	if enemy.bonus_armour > 0.0:
		var at := (feet + Vector2(0, -tall - 6.0)).floor()
		var glow := Color(STONE.lerp(Color.WHITE, 0.3), 0.6 + 0.3 * sin(_elapsed * 4.0 + salt))
		_marks.draw_rect(Rect2(at + Vector2(-1, -1), Vector2(3, 1)), glow)
		_marks.draw_rect(Rect2(at + Vector2(0, -1), Vector2(1, 3)), glow)
	if enemy.steady and not (enemy.has_power and enemy.data.power == &"steadfast"):
		for i in 2:
			_dot(_marks, feet + Vector2((float(i) * 2.0 - 1.0) * half * 0.7, 1.0), Color(STONE.darkened(0.2), 0.8))
	if enemy.remedied and enemy.has_status(&"poison"):
		var rise := fposmod(_elapsed * 0.8 + salt, 1.0)
		_dot(_marks, feet + Vector2(sin(salt) * half, -tall * 0.4 - rise * 6.0), Color(GROVE.lerp(Color.WHITE, 0.4), 1.0 - rise))
	if enemy.swarm > 0.0 or _is_charging(enemy) or enemy.momentum > 0.0 or enemy.spur > 0.0:
		var color := GROVE if enemy.swarm > 0.0 else (SKY if enemy.spur > 0.0 else (FLAME if enemy.momentum > 0.0 else STONE))
		for i in 3:
			var trail := fposmod(_elapsed * 3.0 + salt + float(i) * 0.33, 1.0)
			var at := feet + Vector2(-side * (half * 0.6 + trail * 7.0), -1.0 - float(i) * 2.0)
			_dot(_marks, at, Color(color, 0.85 * (1.0 - trail)))
	if enemy.raised:
		var flicker := 0.6 + 0.3 * sin(_elapsed * 9.0 + salt)
		_dot(_marks, (feet + Vector2(side * visual.size.x * 0.04, -visual.size.y * 0.42)).floor(), Color(GROVE.lerp(NECRO, 0.5), flicker))
	if enemy.has_power and enemy.downed <= 0.0 and AURA_COLORS.has(enemy.data.power):
		var reach := enemy.data.power_radius / SCALE
		var throb := 0.12 + 0.06 * sin(_elapsed * 2.5 + salt)
		_draw_ring(feet, reach, clampi(int(reach * 0.8), 24, 96), Color(AURA_COLORS[enemy.data.power], throb), 1.0)


const AURA_COLORS := {
	&"bulwark": Color(0.9, 0.66, 0.34),
	&"steadfast": Color(0.75, 0.62, 0.45),
	&"hush": Color(0.55, 0.6, 0.75),
	&"remedy": Color(0.5, 0.85, 0.3),
}


## What the hordes do to a tower: fog round it, a net over it, an eclipse on it, a hush on its effects.
func _draw_tower_hexes(visual: TowerVisual) -> void:
	var tower := visual.tower
	var base := visual.root.position
	var salt := float(tower.id) * 1.9
	if tower.fog_left > 0.0:
		for i in 8:
			var drift := fposmod(_elapsed * 0.4 + salt + float(i) * 0.125, 1.0)
			var at := base + Vector2(cos(TAU * float(i) / 8.0 + drift) * 10.0, -6.0 + sin(TAU * float(i) / 8.0 + drift) * 4.0)
			_marks.draw_rect(Rect2(at.floor(), Vector2(2, 1)), Color(0.82, 0.86, 0.88, 0.5))
	if tower.net_left > 0.0:
		var c := Color(0.78, 0.72, 0.55, 0.85)
		for i in 3:
			var x := float(i) * 4.0 - 4.0
			_marks.draw_line(base + Vector2(x - 4, -18), base + Vector2(x + 4, -2), c, 1.0)
			_marks.draw_line(base + Vector2(x + 4, -18), base + Vector2(x - 4, -2), c, 1.0)
	if tower.eclipse_left > 0.0:
		var throb := 0.5 + 0.3 * sin(_elapsed * 3.0 + salt)
		_draw_ring(base + Vector2(0, -22), 3.0, 12, Color(HOLLOW, throb), 1.0)
		_dot(_marks, base + Vector2(0, -22), Color(0.05, 0.02, 0.1, throb))
	if tower.hushed:
		for i in 3:
			_dot(_marks, base + Vector2(float(i) * 3.0 - 3.0, -24.0), Color(0.55, 0.6, 0.75, 0.6))


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
	# Hand-drawn sprites are already drawn at their full size.
	if cells <= 0.0 or meta.is_empty() or meta.get("drawn", false):
		return 1.0
	var size: Array = meta["size"]
	return maxf(1.0, roundf(cells * CELL_ART / float(size[1])))
