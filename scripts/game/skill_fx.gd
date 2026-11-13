class_name SkillFx
extends Node
## Draws the player's skills on the board as big hand-drawn effects: comets that fall from the sky and
## blow craters in the road, a wall of water that sweeps the board, rock spikes and boulders, thorn vines,
## lightning, and a void rift that swallows the road. Enemies they hit are thrown into the air and slide
## back where they are pushed, and the board shakes under the heavy ones.
##
## It only reads the simulation (RunSim.skill_cast and skill_struck) and draws into BoardArt's layers,
## in BoardArt's art pixels. The strips come from tools/art/pix2d/skill_fx.py.

const ART := "res://assets/art/game/skill_fx/"
## Seconds a comet is seen falling before it lands.
const FALL := 0.6
## Where a comet comes from, in art pixels from where it lands (high up and to the right).
const FALL_FROM := Vector2(170.0, -360.0)
## Seconds a boulder takes to drop once its target is picked.
const DROP := 0.22
## Strips drawn with the board's light (rock, water, plants); the rest burn by their own light.
const LIT := [&"crater", &"rock_spike", &"boulder", &"dust_cloud", &"vines", &"bramble", &"tsunami", &"wave_spray"]
## Effects allowed at once, to keep big casts cheap.
const MAX_ANIMS := 160
## How long a crater stays on the ground, fading over the last part.
const CRATER_TIME := 7.0
## The tsunami tile's crest, in art pixels from its left edge.
const WAVE_CREST := 62.0

static var _info: Dictionary = {}

var art: BoardArt
var sim: RunSim

var _anims: Array[Anim] = []
var _comets: Array[Comet] = []
var _walls: Array[Wall] = []
var _fields: Array[Field] = []
var _rocks: Array[Rock] = []
var _cracks: Array[Crack] = []
var _crack_layer: Node2D
## The board shakes this many art pixels, dying away.
var _shake := 0.0
var _flash: Sprite2D
var _flash_alpha := 0.0


## A strip played on the board: once, or looping for `life` seconds.
class Anim:
	var node: Node2D
	var sprites: Array[Sprite2D] = []
	var frames := 1
	var fps := 12.0
	var age := 0.0
	var loop := false
	## Seconds a loop plays before it fades; below 0 it plays until told to stop.
	var life := -1.0
	var fade := 0.0
	var alpha := 1.0


## A comet on its way down to one strike.
class Comet:
	var cast: SimSkillCast
	var blow: SimSkillCast.Blow
	var anim: Anim
	var trail: CPUParticles2D
	var shadow: Sprite2D
	var marker := 0.0
	var size := 1.0


## One sweep's wall of water crossing the board.
class Wall:
	var cast: SimSkillCast
	var blow: SimSkillCast.Blow
	var node: Node2D
	var tiles: Array[Sprite2D] = []
	var spray: CPUParticles2D
	var fade := 1.0
	var gone := false


## A field left on the ground (burning, brambles, a rift) for as long as the sim's zone lasts.
class Field:
	var cast: SimSkillCast
	var zone: SimSkillCast.Zone
	var anims: Array[Anim] = []
	var particles: CPUParticles2D
	var light: PointLight2D


## A boulder dropping onto an enemy picked by a bolt.
class Rock:
	var anim: Anim
	var from := Vector2.ZERO
	var to := Vector2.ZERO
	var age := 0.0


## Cracks torn across the ground by an earthquake, glowing as they fade.
class Crack:
	var lines: Array[PackedVector2Array] = []
	var age := 0.0
	var life := 2.6


static func info(strip: String) -> Dictionary:
	if _info.is_empty() and FileAccess.file_exists(ART + "skill_fx.json"):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART + "skill_fx.json"))
		if parsed is Dictionary:
			_info = parsed
	return _info.get(strip, {})


## True when the skills' strips have been drawn.
static func has_art() -> bool:
	return not info("comet").is_empty()


func setup(p_art: BoardArt) -> void:
	art = p_art
	sim = art.sim
	_crack_layer = Node2D.new()
	_crack_layer.z_index = 1
	_crack_layer.material = art._additive
	_crack_layer.draw.connect(_draw_cracks)
	art._world.add_child(_crack_layer)
	_flash = Sprite2D.new()
	_flash.texture = art._pixel
	_flash.centered = false
	_flash.material = art._additive
	_flash.z_index = 5
	_flash.modulate = Color(1, 1, 1, 0)
	_flash.scale = sim.config.map.size_in_pixels() / BoardArt.SCALE + Vector2(400, 400)
	_flash.position = Vector2(-200, -200)
	art._world.add_child(_flash)
	sim.skill_cast.connect(_on_cast)
	sim.skill_struck.connect(_on_struck)


# ------------------------------------------------------------------ per frame

func _process(delta: float) -> void:
	if sim == null:
		return
	var live := sim.skill_casts()
	_advance_comets(live)
	_advance_walls(delta, live)
	_advance_fields(delta, live)
	_advance_rocks(delta)
	_advance_anims(delta)
	_advance_cracks(delta)
	# The shake dies away; the board settles back on whole pixels.
	_shake = maxf(0.0, _shake - delta * (10.0 + _shake * 3.0))
	if _shake > 0.05:
		art._world.position = Vector2(randf_range(-1.0, 1.0), randf_range(-1.0, 1.0)) * _shake * BoardArt.SCALE
	else:
		art._world.position = Vector2.ZERO
	_flash_alpha = maxf(0.0, _flash_alpha - delta * 3.5)
	_flash.modulate = Color(_flash.modulate, _flash_alpha)


## True while anything of a skill is still being drawn.
func is_busy() -> bool:
	return not (_anims.is_empty() and _comets.is_empty() and _walls.is_empty() and _fields.is_empty() and _rocks.is_empty())


func shake(amount: float) -> void:
	_shake = maxf(_shake, amount)


func flash(color: Color, alpha: float) -> void:
	_flash.modulate = Color(color, maxf(_flash_alpha, alpha))
	_flash_alpha = maxf(_flash_alpha, alpha)


# ------------------------------------------------------------------ casts and blows

func _on_cast(cast: SimSkillCast) -> void:
	match cast.skill.element:
		&"fire":
			for blow in cast.blows_of(&"strike"):
				_add_comet(cast, blow)
		&"water":
			for blow in cast.blows_of(&"sweep"):
				_add_wall(cast, blow)
		&"storm":
			# The sky darkens and cracks open: a flash over the whole board.
			flash(Color(0.75, 0.82, 1.0), 0.22 if cast.rank.bolts > 0 else 0.1)


func _on_struck(cast: SimSkillCast, blow: SimSkillCast.Blow, hit: Array[SimEnemy]) -> void:
	var element := cast.skill.element
	var at := art._art_pos(blow.at)
	var radius := blow.radius / BoardArt.SCALE
	match blow.kind:
		&"strike":
			match element:
				&"fire":
					_land_comet(cast, blow, at, radius)
				&"earth":
					_quake(cast, blow)
				&"nature":
					_vines(cast, blow, at, radius, hit)
				&"void":
					_rift(cast, blow, at, radius)
				_:
					_generic(cast, at, radius)
		&"sweep":
			for enemy in hit:
				_play(&"wave_spray", _enemy_foot(enemy), 1.2, art._air, Vector2(0, 12))
		&"bolt":
			if element == &"storm":
				_lightning(at)
			else:
				_drop_boulder(at)
		&"finale":
			_collapse(cast, at, radius)
	if blow.main and cast.rank.zone_time > 0.0 and not cast.zones.is_empty():
		_add_field(cast, cast.zones[cast.zones.size() - 1])
	if cast.launch > 0.0:
		var height := {&"fire": 30.0, &"water": 22.0, &"earth": 24.0, &"void": 14.0, &"storm": 10.0, &"nature": 12.0}.get(element, 16.0) as float
		var seconds := cast.launch * (0.5 if blow.kind == &"bolt" else 1.0)
		for enemy in hit:
			art.toss_enemy(enemy, seconds, height * (0.6 if blow.kind == &"bolt" else 1.0))


func _enemy_foot(enemy: SimEnemy) -> Vector2:
	return art._art_pos(enemy.position) + Vector2(0, BoardArt.ENEMY_DROP)


# ------------------------------------------------------------------ fire

func _add_comet(cast: SimSkillCast, blow: SimSkillCast.Blow) -> void:
	var comet := Comet.new()
	comet.cast = cast
	comet.blow = blow
	# The rock grows with its level and (gently) with how wide the blast it brings is.
	var wide := sqrt(clampf(cast.radius / 110.0, 0.6, 2.0))
	comet.size = clampf(blow.radius / maxf(1.0, cast.radius), 0.5, 1.0) * (1.2 + 0.15 * float(cast.level)) * wide
	comet.anim = _anim(&"comet", art._air, true)
	if comet.anim == null:
		return
	comet.anim.node.visible = false
	comet.anim.node.scale = Vector2.ONE * comet.size
	comet.trail = art._particles(40, 0.55, Vector2(3, 3) * comet.size)
	comet.trail.material = art._additive
	comet.trail.gravity = Vector2(0, -20)
	comet.trail.initial_velocity_min = 4.0
	comet.trail.initial_velocity_max = 16.0
	comet.trail.spread = 180.0
	comet.trail.scale_amount_min = 1.0
	comet.trail.scale_amount_max = 3.0
	comet.trail.color_ramp = art._gradient([Color(1, 0.95, 0.6), Color(1.0, 0.5, 0.15), Color(0.3, 0.1, 0.05, 0)], [0.0, 0.35, 1.0])
	comet.trail.emitting = false
	art._air.add_child(comet.trail)
	comet.shadow = Sprite2D.new()
	comet.shadow.texture = art._blob_texture
	comet.shadow.position = art._art_pos(blow.at)
	comet.shadow.modulate = Color(1, 1, 1, 0)
	art._shadows.add_child(comet.shadow)
	_comets.append(comet)


func _advance_comets(live: Array[SimSkillCast]) -> void:
	var keep: Array[Comet] = []
	for comet in _comets:
		if comet.blow.done or not live.has(comet.cast):
			_drop_comet(comet)
			continue
		var start := comet.blow.time - minf(FALL, comet.blow.time)
		var u := clampf((comet.cast.age - start) / maxf(0.05, comet.blow.time - start), 0.0, 1.0)
		var to := art._art_pos(comet.blow.at)
		var from := to + FALL_FROM * (0.8 + 0.2 * comet.size)
		if comet.cast.age >= start:
			# It speeds up as it falls.
			var pos := from.lerp(to, clampf(u * u * 0.35 + u * 0.65, 0.0, 1.0))
			comet.anim.node.visible = true
			comet.anim.node.position = pos
			comet.anim.node.rotation = (to - from).angle()
			comet.trail.position = pos
			comet.trail.emitting = true
			# Its shadow gathers on the ground where it will land.
			var r := comet.blow.radius / BoardArt.SCALE
			comet.shadow.scale = Vector2(r / 14.0, r / 28.0) * (0.4 + 0.6 * u)
			comet.shadow.modulate = Color(1, 1, 1, 0.25 + 0.6 * u)
			comet.marker += 1.0
			if int(comet.marker) % 12 == 1:
				art._ring(to, Color(1.0, 0.55, 0.2), r, r * 0.85, 0.3)
		keep.append(comet)
	_comets = keep


func _drop_comet(comet: Comet) -> void:
	_free_anim(comet.anim)
	comet.trail.emitting = false
	art.get_tree().create_timer(0.7).timeout.connect(comet.trail.queue_free)
	comet.shadow.queue_free()


func _land_comet(cast: SimSkillCast, blow: SimSkillCast.Blow, at: Vector2, radius: float) -> void:
	for comet in _comets:
		if comet.blow == blow:
			_drop_comet(comet)
			_comets.erase(comet)
			break
	var big := 1.0 if blow.main else 0.7
	# The impact strip is drawn for a blast about 48 art pixels across its ground ring.
	_play(&"comet_impact", at, clampf(radius / 46.0, 0.6, 3.2), art._air, Vector2(0, 30))
	var crater := _anim(&"crater", art._shadows, false)
	if crater != null:
		crater.node.position = at
		crater.node.scale = Vector2.ONE * clampf(radius / 30.0, 0.6, 3.0)
		crater.loop = true
		crater.life = CRATER_TIME
		crater.fade = 2.5
	art._ring(at, Color(1.0, 0.85, 0.55), radius * 0.2, radius * 1.15, 0.45, 2.0)
	art._burst(at, Color(1.0, 0.6, 0.2), 50, 110.0 * big)
	art._burst(at, Color(0.35, 0.3, 0.28), 30, 60.0, false)
	art._pulse_light(at, Color(1.0, 0.55, 0.2), 3.2 * big, radius * 3.0, 0.9)
	shake((5.0 + float(cast.level)) * big)
	flash(Color(1.0, 0.7, 0.4), 0.12 * big)


# ------------------------------------------------------------------ water

func _add_wall(cast: SimSkillCast, blow: SimSkillCast.Blow) -> void:
	var meta := info("tsunami")
	if meta.is_empty():
		return
	var wall := Wall.new()
	wall.cast = cast
	wall.blow = blow
	wall.node = Node2D.new()
	wall.node.visible = false
	art._air.add_child(wall.node)
	var tile_h: float = (meta["size"] as Array)[1]
	var board_h := sim.config.map.size_in_pixels().y / BoardArt.SCALE
	var count := ceili((board_h + tile_h * 2.0) / tile_h)
	var moving_right := blow.to_x > blow.at.x
	# A higher level raises a taller, wider wall.
	var width := 1.0 + 0.18 * float(cast.level - 1)
	wall.node.scale = Vector2(width if moving_right else -width, 1.0)
	for k in count:
		for layer in _layers(&"tsunami", meta):
			var sprite := Sprite2D.new()
			sprite.texture = layer[0]
			sprite.material = layer[1]
			sprite.hframes = int(meta["frames"])
			sprite.centered = false
			sprite.position = Vector2(-WAVE_CREST, -tile_h + tile_h * float(k))
			wall.node.add_child(sprite)
			wall.tiles.append(sprite)
	wall.spray = art._particles(90, 0.9, Vector2(4, board_h * 0.5))
	wall.spray.position = Vector2(4, board_h * 0.5)
	wall.spray.gravity = Vector2(0, 60)
	wall.spray.direction = Vector2(1, -0.6)
	wall.spray.spread = 40.0
	wall.spray.initial_velocity_min = 20.0
	wall.spray.initial_velocity_max = 70.0
	wall.spray.scale_amount_max = 2.5
	wall.spray.color_ramp = art._gradient([Color(1, 1, 1), Color(0.75, 0.9, 1.0), Color(0.5, 0.75, 0.95, 0)], [0.0, 0.5, 1.0])
	wall.spray.emitting = false
	wall.node.add_child(wall.spray)
	_walls.append(wall)


func _advance_walls(delta: float, live: Array[SimSkillCast]) -> void:
	var keep: Array[Wall] = []
	for wall in _walls:
		var started := wall.cast.age >= wall.blow.time
		if wall.blow.done or not live.has(wall.cast):
			wall.gone = true
		if wall.gone:
			wall.fade -= delta * 2.5
			wall.node.position.x += delta * 260.0 * signf(wall.blow.to_x - wall.blow.at.x)
			wall.spray.emitting = false
			if wall.fade <= 0.0:
				wall.node.queue_free()
				continue
		elif started:
			wall.node.visible = true
			wall.spray.emitting = true
			wall.node.position = Vector2(wall.blow.front_at(wall.cast.age) / BoardArt.SCALE, 0)
			# The ground rumbles under it.
			shake(1.6 + 0.3 * float(wall.cast.level))
		wall.node.modulate = Color(1, 1, 1, clampf(wall.fade, 0.0, 1.0) * 0.94)
		var frame := int(art._elapsed * 12.0) % maxi(1, wall.tiles[0].hframes) if not wall.tiles.is_empty() else 0
		for sprite in wall.tiles:
			sprite.frame = frame
		keep.append(wall)
	_walls = keep


# ------------------------------------------------------------------ earth

## The ground heaves: the board shakes, cracks tear along the roads and spikes of rock punch up under
## the enemies and along the way.
func _quake(cast: SimSkillCast, blow: SimSkillCast.Blow) -> void:
	shake(7.0 + float(cast.level) * 1.5)
	flash(Color(1.0, 0.75, 0.45), 0.08)
	var crack := Crack.new()
	var spots: Array[Vector2] = []
	for lane in sim.lane_curves.size():
		var curve := sim.lane_curves[lane]
		var length := curve.get_baked_length()
		var step := 150.0 if cast.level < 3 else 110.0
		var d := fmod(float(cast.skill.id.hash() % 97) + blow.time * 37.0, step)
		while d < length:
			spots.append(art._art_pos(curve.sample_baked(d)) + Vector2(0, BoardArt.ENEMY_DROP))
			d += step
	var seed_ := 0
	for spot in spots:
		seed_ += 1
		crack.lines.append(_crack_line(spot, seed_))
		if _anims.size() < MAX_ANIMS * 0.6:
			_play(&"rock_spike", spot + Vector2(randf_range(-10, 10), randf_range(-4, 4)), 1.0 + 0.1 * cast.level, art._actors, Vector2(0, 18))
		if seed_ % 4 == 0:
			_play(&"dust_cloud", spot, 1.2, art._air, Vector2(0, 8))
	for enemy in sim.enemies:
		if enemy.alive and _anims.size() < MAX_ANIMS * 0.8:
			_play(&"rock_spike", _enemy_foot(enemy) + Vector2(4, 2), 0.9, art._actors, Vector2(0, 18))
	_cracks.append(crack)


func _crack_line(from: Vector2, seed_: int) -> PackedVector2Array:
	var rng := RandomNumberGenerator.new()
	rng.seed = seed_ * 7919 + int(art._elapsed * 10.0)
	var points := PackedVector2Array([from])
	var angle := rng.randf() * TAU
	var at := from
	for k in 6:
		angle += rng.randf_range(-0.7, 0.7)
		at += Vector2(cos(angle), sin(angle) * 0.6) * rng.randf_range(6.0, 12.0)
		points.append(at)
	return points


func _advance_cracks(delta: float) -> void:
	if _cracks.is_empty():
		return
	var keep: Array[Crack] = []
	for crack in _cracks:
		crack.age += delta
		if crack.age < crack.life:
			keep.append(crack)
	_cracks = keep
	_crack_layer.queue_redraw()


func _draw_cracks() -> void:
	for crack in _cracks:
		var t := crack.age / crack.life
		var glow := Color(1.0, 0.55 - 0.2 * t, 0.2, (1.0 - t) * 0.9)
		var core := Color(1.0, 0.9, 0.6, (1.0 - t) * (1.0 - t))
		for line in crack.lines:
			var shown := int(ceil(line.size() * minf(1.0, crack.age * 6.0)))
			if shown < 2:
				continue
			var part := line.slice(0, shown)
			_crack_layer.draw_polyline(part, glow, 2.0)
			_crack_layer.draw_polyline(part, core, 1.0)


func _drop_boulder(at: Vector2) -> void:
	var anim := _anim(&"boulder", art._air, true)
	if anim == null:
		return
	var rock := Rock.new()
	rock.anim = anim
	rock.to = at + Vector2(0, BoardArt.ENEMY_DROP)
	rock.from = rock.to + Vector2(randf_range(-30, 30), -220)
	anim.node.position = rock.from
	anim.node.scale = Vector2.ONE * 1.3
	_rocks.append(rock)


func _advance_rocks(delta: float) -> void:
	var keep: Array[Rock] = []
	for rock in _rocks:
		rock.age += delta
		var u := clampf(rock.age / DROP, 0.0, 1.0)
		rock.anim.node.position = rock.from.lerp(rock.to, u * u)
		if u >= 1.0:
			_free_anim(rock.anim)
			_play(&"dust_cloud", rock.to, 1.0, art._air, Vector2(0, 8))
			_play(&"rock_spike", rock.to, 0.8, art._actors, Vector2(0, 18))
			art._burst(rock.to, Color(0.6, 0.52, 0.42), 18, 50.0, false)
			shake(2.5)
			continue
		keep.append(rock)
	_rocks = keep


# ------------------------------------------------------------------ storm

func _lightning(at: Vector2) -> void:
	var foot := at + Vector2(0, BoardArt.ENEMY_DROP)
	var meta := info("lightning")
	var height: float = (meta.get("size", [0, 200]) as Array)[1]
	_play(&"lightning", foot, 1.4, art._air, Vector2(0, height * 0.5 - 10.0))
	art._ring(foot, Color(0.8, 0.88, 1.0), 3.0, 26.0, 0.4, 2.0)
	art._sparks(foot + Vector2(0, -6), Color(0.85, 0.92, 1.0), 10, 16.0)
	art._pulse_light(foot, Color(0.6, 0.7, 1.0), 3.0, 140.0, 0.35)
	flash(Color(0.8, 0.85, 1.0), 0.1)
	shake(1.8)


# ------------------------------------------------------------------ nature

func _vines(cast: SimSkillCast, blow: SimSkillCast.Blow, at: Vector2, radius: float, hit: Array[SimEnemy]) -> void:
	var size := clampf(radius / 40.0, 0.8, 1.8)
	_play(&"vines", at, size, art._actors, Vector2(0, 26))
	var clumps := 5 + cast.level * 2
	for k in clumps:
		var angle := float(k) * 2.39996 + blow.time
		var spot := at + Vector2(cos(angle), sin(angle) * 0.6) * radius * (0.35 + 0.6 * fmod(float(k) * 0.618, 1.0))
		_play(&"vines", spot, size * 0.6, art._actors, Vector2(0, 26), float(k) * 0.03)
	for enemy in hit.slice(0, 14):
		_play(&"vines", _enemy_foot(enemy) + Vector2(0, 2), 0.7, art._actors, Vector2(0, 26))
	art._ring(at, Color(0.6, 1.0, 0.4), radius, 4.0, 0.5, 2.0)
	art._burst(at, Color(0.7, 1.0, 0.45), 30, 40.0)
	shake(2.0 + float(cast.level) * 0.5)


# ------------------------------------------------------------------ void

func _rift(cast: SimSkillCast, blow: SimSkillCast.Blow, at: Vector2, radius: float) -> void:
	if not blow.main:
		return
	var rift := _anim(&"void_rift", art._shadows, true)
	if rift != null:
		rift.node.position = at
		rift.node.scale = Vector2.ONE * clampf(radius / 44.0, 0.6, 2.4)
		rift.life = maxf(1.2, cast.rank.zone_time)
		rift.fade = 0.6
	var pull := art._particles(70, 0.8, Vector2(radius, radius * 0.5))
	pull.position = at
	pull.material = art._additive
	pull.local_coords = false
	pull.emission_shape = CPUParticles2D.EMISSION_SHAPE_SPHERE
	pull.emission_sphere_radius = radius
	pull.radial_accel_min = -radius * 3.0
	pull.radial_accel_max = -radius * 2.0
	pull.tangential_accel_min = 40.0
	pull.tangential_accel_max = 80.0
	pull.scale_amount_max = 2.0
	pull.color_ramp = art._gradient([Color(0.95, 0.85, 1.0), Color(0.6, 0.3, 1.0), Color(0.2, 0.05, 0.4, 0)], [0.0, 0.5, 1.0])
	art._air.add_child(pull)
	pull.emitting = true
	art.get_tree().create_timer(maxf(1.0, cast.rank.zone_time)).timeout.connect(func() -> void:
		if is_instance_valid(pull):
			pull.emitting = false
			art.get_tree().create_timer(1.0).timeout.connect(pull.queue_free))
	art._ring(at, Color(0.8, 0.55, 1.0), radius * 1.2, 3.0, 0.6, 2.0)
	art._pulse_light(at, Color(0.6, 0.3, 1.0), 2.4, radius * 2.5, 0.8)
	shake(2.0 + float(cast.level) * 0.6)


func _collapse(cast: SimSkillCast, at: Vector2, radius: float) -> void:
	_play(&"void_collapse", at, clampf(radius / 40.0, 0.7, 2.6), art._air)
	art._burst(at, Color(0.7, 0.4, 1.0), 60, 120.0)
	art._pulse_light(at, Color(0.7, 0.35, 1.0), 3.5, radius * 3.0, 1.0)
	flash(Color(0.6, 0.35, 1.0), 0.18)
	shake(8.0 + float(cast.level))


func _generic(_cast: SimSkillCast, at: Vector2, radius: float) -> void:
	if radius > 0.0:
		art._ring(at, Color(1, 1, 1), radius, radius * 0.95, 0.6, 2.0)


# ------------------------------------------------------------------ fields

func _add_field(cast: SimSkillCast, zone: SimSkillCast.Zone) -> void:
	for field in _fields:
		if field.zone == zone:
			return
	var field := Field.new()
	field.cast = cast
	field.zone = zone
	var at := art._art_pos(zone.at)
	var radius := zone.radius / BoardArt.SCALE
	match cast.skill.element:
		&"fire":
			var count := clampi(int(radius * radius / 70.0), 10, 56)
			for k in count:
				var spot := at + _scatter(k, radius * 0.9)
				var flame := _anim(&"ground_fire", art._actors, true)
				if flame == null:
					break
				flame.node.position = spot
				flame.age = float(k) * 0.07
				flame.node.scale = Vector2.ONE * (0.8 + 0.5 * fmod(float(k) * 0.37, 1.0))
				for sprite in flame.sprites:
					sprite.offset.y = -12.0
				field.anims.append(flame)
			field.light = art._flash_light(Color(1.0, 0.5, 0.2), 1.6, radius * 2.2, 20.0)
		&"nature":
			var count := clampi(int(radius * radius / 80.0), 8, 36)
			for k in count:
				var bramble := _anim(&"bramble", art._actors, true)
				if bramble == null:
					break
				bramble.node.position = at + _scatter(k, radius * 0.95)
				bramble.age = float(k) * 0.11
				for sprite in bramble.sprites:
					sprite.offset.y = -8.0
				field.anims.append(bramble)
		&"void":
			field.particles = art._particles(40, 1.0, Vector2(radius, radius * 0.5))
			field.particles.material = art._additive
			field.particles.gravity = Vector2(0, -14)
			field.particles.color_ramp = art._gradient([Color(0.85, 0.7, 1.0), Color(0.5, 0.2, 0.9, 0)], [0.0, 1.0])
			field.particles.position = at
			art._air.add_child(field.particles)
			field.particles.emitting = true
	if field.light != null:
		field.light.position = at
		art._air.add_child(field.light)
	_fields.append(field)


func _scatter(k: int, radius: float) -> Vector2:
	var angle := float(k) * 2.39996
	var dist := sqrt(fmod(float(k) * 0.618034 + 0.13, 1.0)) * radius
	return Vector2(cos(angle), sin(angle) * 0.55) * dist


func _advance_fields(_delta: float, live: Array[SimSkillCast]) -> void:
	var keep: Array[Field] = []
	for field in _fields:
		var open := live.has(field.cast) and field.cast.zones.has(field.zone)
		if open:
			var left := field.zone.time_left / maxf(0.01, field.zone.duration)
			# The field dies down over its last second.
			var alpha := clampf(field.zone.time_left, 0.0, 1.0)
			for anim in field.anims:
				anim.alpha = alpha
			if field.light != null:
				field.light.energy = 1.6 * alpha * (0.85 + 0.15 * sin(art._elapsed * 11.0)) * (0.6 + 0.4 * left)
			keep.append(field)
			continue
		for anim in field.anims:
			anim.life = 0.0
			anim.fade = 0.3
		if field.particles != null:
			field.particles.emitting = false
			art.get_tree().create_timer(1.2).timeout.connect(field.particles.queue_free)
		if field.light != null:
			art._release_light(field.light)
	_fields = keep


# ------------------------------------------------------------------ strips

func _layers(strip: StringName, meta: Dictionary) -> Array:
	var lit := LIT.has(strip)
	var result := [[load(ART + "%s.png" % strip), null if lit else art._unshaded]]
	if meta.get("glow", false):
		result.append([load(ART + "%s_glow.png" % strip), art._additive])
	return result


## A strip ready to play on `parent`, or null when it has not been drawn or too many are playing.
func _anim(strip: StringName, parent: Node2D, loop: bool) -> Anim:
	var meta := info(String(strip))
	if meta.is_empty() or _anims.size() >= MAX_ANIMS:
		return null
	var anim := Anim.new()
	anim.frames = int(meta.get("frames", 1))
	anim.fps = float(meta.get("fps", 12))
	anim.loop = loop
	anim.node = Node2D.new()
	parent.add_child(anim.node)
	for layer: Array in _layers(strip, meta):
		var sprite := Sprite2D.new()
		sprite.texture = layer[0]
		if layer[1] != null:
			sprite.material = layer[1]
		sprite.hframes = anim.frames
		anim.node.add_child(sprite)
		anim.sprites.append(sprite)
	_anims.append(anim)
	return anim


## Plays a strip once at a point. `lift` moves the picture against its point, such as up so its foot
## stands there. A delay holds it back that many seconds.
func _play(strip: StringName, at: Vector2, scale_by: float, parent: Node2D, lift := Vector2.ZERO, delay := 0.0) -> Anim:
	var anim := _anim(strip, parent, false)
	if anim == null:
		return null
	anim.node.position = at
	anim.node.scale = Vector2.ONE * scale_by
	anim.age = -delay
	for sprite in anim.sprites:
		sprite.offset = -lift
	if delay > 0.0:
		anim.node.visible = false
	return anim


func _free_anim(anim: Anim) -> void:
	if anim == null:
		return
	anim.node.queue_free()
	_anims.erase(anim)


func _advance_anims(delta: float) -> void:
	var keep: Array[Anim] = []
	for anim in _anims:
		if not is_instance_valid(anim.node) or anim.node.is_queued_for_deletion():
			continue
		anim.age += delta
		if anim.age < 0.0:
			continue
		anim.node.visible = true
		var frame := int(anim.age * anim.fps)
		var alpha := anim.alpha
		if anim.loop:
			if anim.life >= 0.0:
				var left := anim.life - anim.age
				if left <= 0.0:
					anim.node.queue_free()
					continue
				if anim.fade > 0.0:
					alpha *= clampf(left / anim.fade, 0.0, 1.0)
			frame %= anim.frames
		elif frame >= anim.frames:
			anim.node.queue_free()
			continue
		for sprite in anim.sprites:
			sprite.frame = frame
		anim.node.modulate = Color(1, 1, 1, alpha)
		keep.append(anim)
	_anims = keep
