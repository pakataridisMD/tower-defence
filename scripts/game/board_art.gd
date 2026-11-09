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
const ENEMY_DROP := 5.0
## Short-lived lights (shots, blasts, lightning) allowed at once, to keep lighting cheap.
const MAX_FLASH_LIGHTS := 10

static var _info: Dictionary = {}
static var _texture_cache: Dictionary = {}

var sim: RunSim
var day_night := DayNight.new()

var _world: Node2D
var _ground: Node2D
var _shadows: Node2D
var _actors: Node2D
var _air: Node2D
var _ambient: CanvasModulate
var _sun: DirectionalLight2D
var _fireflies: CPUParticles2D

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


## Something with a contact shadow and a sun shadow that follows it.
class Caster:
	var node: Node2D
	var flip_from: Sprite2D
	var blob: Sprite2D
	var sun: Sprite2D
	var height := 1.0


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
	_build_ground()
	_build_fireflies()
	sim.chain_fired.connect(_on_chain_fired)
	sim.projectile_landed.connect(_on_projectile_landed)
	sim.enemy_killed.connect(_on_enemy_killed)
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


## The ground is cut into 2x2-cell pieces so each piece only takes the lights near it
## (the Compatibility renderer caps the lights per drawn item).
func _build_ground() -> void:
	var map := sim.config.map
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
	_fireflies.gravity = Vector2.ZERO
	_fireflies.initial_velocity_min = 2.0
	_fireflies.initial_velocity_max = 6.0
	_fireflies.color_ramp = _gradient([Color(0.8, 1, 0.4, 0), Color(0.85, 1, 0.45, 1), Color(0.8, 1, 0.4, 0)], [0.0, 0.5, 1.0])
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


func _update_light(delta: float) -> void:
	var in_wave := sim.state == RunSim.State.WAVE
	day_night.set_target(DayNight.target_for(sim.wave_index, in_wave, sim.time_in_wave, sim.state == RunSim.State.WON))
	day_night.advance(delta)
	_ambient.color = day_night.ambient()
	_sun.energy = day_night.sun_energy()
	_sun.color = day_night.sun_color()
	_fireflies.modulate = Color(1, 1, 1, day_night.night())


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
			_towers[tower.id] = _make_tower(tower)
			seen[tower.id] = true
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


func _make_tower(tower: SimTower) -> TowerVisual:
	var meta := tower_info(tower.data.id)
	var visual := TowerVisual.new()
	visual.tower = tower
	visual.data_id = tower.data.id
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
	var wave := sim.current_wave()
	var tint := Color.WHITE
	if wave != null:
		tint = sim.config.element_color(wave.element).lerp(Color.WHITE, 0.3)
	for enemy in sim.enemies:
		if not enemy.alive:
			continue
		seen[enemy.id] = true
		var visual: EnemyVisual = _enemies.get(enemy.id)
		if visual == null:
			if enemy_info(enemy.data.id).is_empty():
				continue
			visual = _make_enemy(enemy, tint)
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
	return visual


func _update_enemy(visual: EnemyVisual, delta: float) -> void:
	var enemy := visual.enemy
	var pos := _art_pos(enemy.position) + Vector2(0, ENEMY_DROP)
	var speed_factor := enemy.speed() / maxf(1.0, enemy.base_speed)
	visual.time += delta * (0.6 + speed_factor * 0.4) * (1.6 if enemy.data.tags.has(&"fast") else 1.0)
	var frame := int(visual.time * 7.0) % visual.frames.size()
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
	var color := visual.tint
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
	if source != null:
		source.pulse = 1.0
		node.position = source.root.position + source.muzzle
	var elements := shot.source.data.elements if shot.source != null else ([] as Array[StringName])
	var color := sim.config.element_color(elements[0]) if not elements.is_empty() else Color.WHITE
	if shot.splash_radius > 0.0:
		# A fireball: hot core, trail, and its own light if there is room for one.
		var core := Sprite2D.new()
		core.texture = _pixel
		core.scale = Vector2(3, 3)
		core.modulate = Color(1, 0.95, 0.7)
		core.material = _additive
		node.add_child(core)
		var trail := _particles(18, 0.3, Vector2(1, 1))
		trail.gravity = Vector2(0, -10)
		trail.initial_velocity_max = 3.0
		trail.scale_amount_max = 2.0
		trail.color_ramp = _gradient([Color(1, 0.9, 0.5), color, Color(color.darkened(0.5), 0)], [0.0, 0.4, 1.0])
		trail.material = _additive
		node.add_child(trail)
		var light := _flash_light(color.lerp(Color.WHITE, 0.2), 0.9, 34.0, 16.0)
		if light != null:
			node.add_child(light)
	else:
		# A thorn or bolt: a short streak pointing the way it flies.
		var streak := Line2D.new()
		streak.points = PackedVector2Array([Vector2(-3, 0), Vector2(1, 0)])
		streak.width = 1.0
		streak.default_color = color.lerp(Color.WHITE, 0.25)
		streak.material = _unshaded
		node.add_child(streak)
	return node


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
		caster.sun.scale = Vector2(1.0, 0.6 * caster.height)
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
	if shot.splash_radius <= 0.0:
		return
	var at := _art_pos(shot.position)
	var color := Color(1, 0.55, 0.2)
	if shot.source != null and not shot.source.data.elements.is_empty():
		color = sim.config.element_color(shot.source.data.elements[0]).lerp(Color(1, 0.8, 0.4), 0.3)
	_burst(at, color, 22, 30.0)
	var light := _flash_light(color, 1.8, shot.splash_radius / SCALE * 1.6, 12.0)
	if light != null:
		light.position = at
		_air.add_child(light)
		var tween := create_tween()
		tween.tween_property(light, "energy", 0.0, 0.3)
		tween.tween_callback(func() -> void: _release_light(light))


func _on_enemy_killed(enemy: SimEnemy, _killer: SimTower, _bounty: int) -> void:
	var visual: EnemyVisual = _enemies.get(enemy.id)
	var color := visual.tint if visual != null else Color(0.8, 0.85, 0.9)
	_burst(_art_pos(enemy.position) + Vector2(0, ENEMY_DROP - 4), color, 14, 22.0, false)


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


## Height of an enemy's sprite in board pixels, for placing its health bar. 0 if it has no art.
static func enemy_height(enemy_id: StringName) -> float:
	var meta := enemy_info(enemy_id)
	if meta.is_empty():
		return 0.0
	var size: Array = meta["size"]
	return float(size[1]) * SCALE
