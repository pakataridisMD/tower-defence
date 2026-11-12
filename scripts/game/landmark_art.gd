class_name LandmarkArt
extends Node
## Builds and animates the enemy war camps and the defended city at the ends of the roads (see
## Landmarks for where they stand).
##
## The camp is hide tents behind a palisade of stakes, with log watchtowers on either side of the
## road, fires burning, war banners in the wind and hooded sentries pacing. The city is a walled
## town in the look of its land: houses with smoking chimneys and windows that light up at night,
## gate towers over the road and townsfolk going about their day. Every life lost sets another house
## burning, and the townsfolk run when an enemy gets through.
##
## Pieces come from tools/art/landmarks/gen_landmarks.py. BoardArt owns the layers and lights;
## this only adds to them. It is a child node of BoardArt, so its signal connections go with the board.

const ART := "res://assets/art/game/landmarks/"
const CELL := 32.0
## Art pixels a walker covers per second, and how much faster when the city panics.
const WALK_SPEED := 9.0
const PANIC_SPEED := 2.6
const PANIC_TIME := 4.0
## Seconds the camp's fires flare when a wave marches.
const ALARM_TIME := 3.5

static var _info: Dictionary = {}

var board: BoardArt
var sim: RunSim
var biome := "meadow"
var city_name := ""

var _walkers: Array[Walker] = []
var _flames: Array[Sprite2D] = []
var _fire_lights: Array[PointLight2D] = []
var _windows: Array[Sprite2D] = []
var _city_lights: Array[PointLight2D] = []
var _houses: Array[House] = []
var _burning := 0
var _panic := 0.0
var _alarm := 0.0
var _elapsed := 0.0
var _seen_enemies: Dictionary[int, bool] = {}
var _rng := RandomNumberGenerator.new()


## Someone walking about a camp or the city: they pick a spot inside their area, walk to it, wait, repeat.
class Walker:
	var sprite: Sprite2D
	var area: Rect2
	var target := Vector2.ZERO
	var wait := 0.0
	var frame_time := 0.0
	var speed := 1.0
	var city := true
	## Guards stand at the gate and only turn their heads.
	var still := false


class House:
	var sprite: Sprite2D
	var roof: Vector2
	var fire: Array[Node2D] = []


static func info() -> Dictionary:
	if _info.is_empty() and FileAccess.file_exists(ART + "landmarks.json"):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART + "landmarks.json"))
		if parsed is Dictionary:
			_info = parsed
	return _info


static func piece(name: String) -> Dictionary:
	return (info().get("pieces", {}) as Dictionary).get(name, {})


static func has_art() -> bool:
	return not info().is_empty()


## The name of the city a map's road leads to: the stage's city from the story, or a plain name.
static func city_name_for(map: MapData) -> String:
	var stage_id := String(map.id).trim_prefix("c_")
	var entry := Story.shared().city(StringName(stage_id))
	return str(entry.get("name", "Haven"))


func build(p_board: BoardArt) -> void:
	board = p_board
	sim = board.sim
	_rng.seed = hash(sim.config.map.id)
	var kinds: Array = info().get("biomes", [])
	biome = String(sim.config.map.biome) if kinds.has(String(sim.config.map.biome)) else "meadow"
	city_name = city_name_for(sim.config.map)
	for site in sim.landmarks:
		if site.kind == &"camp":
			_build_camp(site)
		else:
			_build_city(site)
	sim.enemy_leaked.connect(_on_enemy_leaked)
	sim.wave_started.connect(_on_wave_started)


# ------------------------------------------------------------------ layout helpers

func _center(cell: Vector2i) -> Vector2:
	return (Vector2(cell) + Vector2(0.5, 0.5)) * CELL


## A piece standing with its feet on `at` (art pixels), lit, with a shadow, sorted with the actors.
func _place(name: String, at: Vector2, flip := false, cast := true) -> Sprite2D:
	var meta := piece(name)
	if meta.is_empty():
		return null
	var sprite := Sprite2D.new()
	sprite.texture = BoardArt.lit_texture(ART + name)
	var size: Array = meta["size"]
	var frames: int = meta.get("frames", 1)
	sprite.hframes = frames
	sprite.centered = false
	sprite.offset = Vector2(-floorf(float(size[0]) / 2.0), -float(size[1]) + 4.0)
	sprite.position = at.floor()
	sprite.flip_h = flip
	if meta.get("sways", false):
		sprite.material = board._sway_material
	if meta.get("glow", false) and frames == 1:
		var glow := Sprite2D.new()
		glow.texture = load(ART + name + "_glow.png")
		glow.centered = false
		glow.offset = sprite.offset
		glow.flip_h = flip
		glow.material = board._additive
		sprite.add_child(glow)
		_windows.append(glow)
	board._actors.add_child(sprite)
	if cast:
		var silhouette := (sprite.texture as CanvasTexture).diffuse_texture
		if frames == 1:
			board._add_caster(sprite, silhouette, sprite.offset, 0.6, sprite)
	return sprite


## A patch of ground (mud or paving) under a cell, drawn over the map's ground.
func _patch(name: String, cell: Vector2i) -> void:
	var tex: Texture2D = load(ART + name + ".png")
	if tex == null:
		return
	var sprite := Sprite2D.new()
	sprite.texture = tex
	sprite.position = _center(cell)
	sprite.flip_h = _rng.randf() < 0.5
	sprite.flip_v = _rng.randf() < 0.5
	board._ground.add_child(sprite)


## Feet points along a row of `count` pieces across the road, inside one cell.
func _row(site: Landmarks.Site, cell: Vector2i, count: int) -> Array[Vector2]:
	var across := Vector2(site.across()).abs()
	var result: Array[Vector2] = []
	for i in count:
		var t := (float(i) + 0.5) / count - 0.5
		result.append(_center(cell) + across * t * CELL + Vector2(0, 8 if across.y > 0.5 else 10))
	return result


func _cells_by_place(site: Landmarks.Site) -> Dictionary:
	var by: Dictionary = {}
	for cell in site.cells:
		by[Vector2i(site.depth_of(cell), site.side_of(cell))] = cell
	return by


func _fire(at: Vector2, scale := 1.0, light := true) -> Sprite2D:
	var flame := Sprite2D.new()
	flame.texture = load(ART + "flame.png")
	flame.hframes = 4
	flame.frame = _rng.randi_range(0, 3)
	flame.centered = false
	flame.offset = Vector2(-7, -18)
	flame.position = at.floor()
	flame.scale = Vector2(scale, scale)
	flame.material = board._unshaded
	flame.z_index = 1
	flame.set_meta("phase", _rng.randf() * 10.0)
	board._actors.add_child(flame)
	_flames.append(flame)
	if light:
		var lamp := board._point_light(Color(1.0, 0.55, 0.22), 1.1, 60.0 * scale, 30.0)
		lamp.position = at + Vector2(0, -6)
		board._air.add_child(lamp)
		lamp.set_meta("energy", lamp.energy)
		_fire_lights.append(lamp)
	var sparks := board._particles(6, 1.4, Vector2(2, 1))
	sparks.position = at + Vector2(0, -8)
	sparks.gravity = Vector2(1, -16)
	sparks.initial_velocity_min = 2.0
	sparks.initial_velocity_max = 6.0
	sparks.color_ramp = board._gradient([Color(1, 0.8, 0.4, 1), Color(1, 0.4, 0.1, 0)], [0.0, 1.0])
	sparks.material = board._additive
	board._air.add_child(sparks)
	return flame


func _smoke(at: Vector2, dark := false, amount := 10) -> CPUParticles2D:
	var smoke := board._particles(amount, 3.6, Vector2(1, 0.5))
	smoke.position = at
	smoke.direction = Vector2(0.3, -1)
	smoke.spread = 12.0
	smoke.gravity = Vector2(3.0, -5.0)
	smoke.initial_velocity_min = 3.0
	smoke.initial_velocity_max = 6.0
	smoke.scale_amount_min = 2.0
	smoke.scale_amount_max = 4.0
	var base := Color(0.12, 0.1, 0.1) if dark else Color(0.62, 0.6, 0.6)
	smoke.color_ramp = board._gradient([Color(base, 0.0), Color(base, 0.55 if dark else 0.38), Color(base, 0.0)], [0.0, 0.2, 1.0])
	smoke.z_index = 3
	board._air.add_child(smoke)
	return smoke


func _walker(strip: String, area: Rect2, city: bool, start: Vector2 = Vector2.INF) -> Walker:
	var w := Walker.new()
	w.area = area
	w.city = city
	w.sprite = _place(strip, start if start != Vector2.INF else _random_in(area), false, false)
	if w.sprite == null:
		return null
	w.sprite.frame = _rng.randi_range(0, 3)
	w.target = _random_in(area)
	w.wait = _rng.randf_range(0.0, 2.0)
	w.speed = _rng.randf_range(0.8, 1.2)
	_walkers.append(w)
	return w


func _random_in(area: Rect2) -> Vector2:
	return Vector2(_rng.randf_range(area.position.x, area.end.x), _rng.randf_range(area.position.y, area.end.y))


## The cells of a site as one rectangle in art pixels (road included), shrunk a little.
func _site_rect(site: Landmarks.Site) -> Rect2:
	var rect := Rect2(_center(site.anchor), Vector2.ZERO)
	for cell in site.cells:
		rect = rect.expand(_center(cell))
	return rect.grow(10.0)


# ------------------------------------------------------------------ the camp

func _build_camp(site: Landmarks.Site) -> void:
	var by := _cells_by_place(site)
	var inner := Landmarks.DEPTH - 1
	for cell in site.cells:
		_patch("mud_%d" % _rng.randi_range(0, 2), cell)
	var yard := _yard_key(by, inner)
	var tents := ["tent_c", "tent_b0", "tent_a0", "tent_b1", "tent_a1", "tent_b0"]
	var tent_i := _rng.randi_range(0, 2)
	for key: Vector2i in by:
		var cell: Vector2i = by[key]
		var flip := key.y < 0
		if key == yard:
			# the yard: a fire with the war drum and the spoils around it
			var at := _center(cell)
			_place("bonfire", at + Vector2(0, 6), false, false)
			_fire(at + Vector2(0, 4), 0.75)
			_smoke(at + Vector2(0, -10), true, 8)
			_place("drum", at + Vector2(-9, 15))
			_place(["rack", "cage"][_rng.randi_range(0, 1)], at + Vector2(10, -2), flip)
		elif key.x == inner and absi(key.y) == 1:
			var tower := _place("watchtower", _center(cell) + Vector2(0, 10), flip)
			if tower != null:
				_fire(tower.position + Vector2(0, -61), 0.6)
				_smoke(tower.position + Vector2(0, -68), true, 6)
		elif key.x == inner:
			var i := 0
			for at in _row(site, cell, 4):
				_place("stake_%d" % ((i + absi(key.y)) % 4), at + Vector2(_rng.randf_range(-1, 1), 0))
				i += 1
		else:
			var tent: String = tents[tent_i % tents.size()]
			tent_i += 1
			_place(tent, _center(cell) + Vector2(_rng.randf_range(-3, 3), 11), flip)
	# war banners either side of the road where it leaves the camp
	var gate := _gate_point(site)
	for sign_: float in [-1.0, 1.0]:
		var banner_at := gate + Vector2(site.across()) * sign_ * CELL * 0.55 + Vector2(0, 14)
		_place("banner_%d" % (0 if sign_ < 0 else 1), banner_at, sign_ < 0, false)
	var area := _site_rect(site)
	for i in 4:
		_walker("sentry_%d" % (i % 2), area, false)
	for sign_: float in [-1.0, 1.0]:
		var guard := _walker("sentry_1", area, false, gate + Vector2(site.across()) * sign_ * CELL * 0.4 + Vector2(0, 8))
		if guard != null:
			guard.still = true
			guard.sprite.flip_h = sign_ > 0 if site.inward.y != 0 else site.inward.x < 0


## The open cell beside the road just inside the wall, kept for the camp fire or the town well.
func _yard_key(by: Dictionary, inner: int) -> Vector2i:
	for side: int in [1, -1, 2, -2]:
		if by.has(Vector2i(inner - 1, side)):
			return Vector2i(inner - 1, side)
	return Vector2i(-99, -99)


## Where the road passes through the wall.
func _gate_point(site: Landmarks.Site) -> Vector2:
	return _center(site.anchor) + Vector2(site.inward) * CELL * float(Landmarks.DEPTH - 1)


# ------------------------------------------------------------------ the city

func _build_city(site: Landmarks.Site) -> void:
	var by := _cells_by_place(site)
	var inner := Landmarks.DEPTH - 1
	for cell in site.cells:
		_patch("paving_%s_%d" % [biome, _rng.randi_range(0, 1)], cell)
	var yard := _yard_key(by, inner)
	var variant := _rng.randi_range(0, 2)
	for key: Vector2i in by:
		var cell: Vector2i = by[key]
		if key == yard:
			# the square: the well, a stall and a lamp
			var at := _center(cell)
			_place("well_" + biome, at + Vector2(-6, 6))
			_place(["stall", "cart", "crates"][_rng.randi_range(0, 2)], at + Vector2(8, 16))
			_city_lamp(at + Vector2(10, -4))
		elif key.x == inner and absi(key.y) == 1:
			var tower := _place("gatetower_" + biome, _center(cell) + Vector2(0, 10), key.y < 0)
			if tower != null:
				var lamp := board._point_light(Color(1.0, 0.75, 0.45), 0.0, 48.0, 40.0)
				lamp.position = tower.position + Vector2(0, -26)
				board._air.add_child(lamp)
				_city_lights.append(lamp)
		elif key.x == inner:
			for at in _row(site, cell, 3):
				_place("wall_" + biome, at)
		else:
			_house("house_%s_%d" % [biome, variant % 3], _center(cell) + Vector2(_rng.randf_range(-2, 2), 12))
			variant += 1
	# lamps by the road just inside the gate
	var street := _gate_point(site) - Vector2(site.inward) * CELL
	for sign_: float in [-1.0, 1.0]:
		_city_lamp(street + Vector2(site.across()) * sign_ * CELL * 0.42 + Vector2(0, 8))
	var area := _site_rect(site)
	var folk := 5 + mini(4, site.cells.size() / 3)
	for i in folk:
		_walker("folk_%d" % (i % 5), area, true)
	var gate := _gate_point(site)
	for sign_: float in [-1.0, 1.0]:
		var guard := _walker("guard", area, true, gate + Vector2(site.across()) * sign_ * CELL * 0.4 + Vector2(0, 8))
		if guard != null:
			guard.still = true
			guard.sprite.flip_h = site.inward.x > 0 or (site.inward.y != 0 and sign_ > 0)


func _house(name: String, at: Vector2) -> void:
	var sprite := _place(name, at, _rng.randf() < 0.3)
	if sprite == null:
		return
	var house := House.new()
	house.sprite = sprite
	var meta := piece(name)
	var size: Array = meta["size"]
	house.roof = sprite.position + Vector2(0, -float(size[1]) * 0.55)
	if meta.has("chimney"):
		var chimney: Array = meta["chimney"]
		var local := Vector2(chimney[0], chimney[1]) + sprite.offset
		if sprite.flip_h:
			local.x = -local.x - 1.0
		_smoke(sprite.position + local, false, 7)
	_houses.append(house)


func _city_lamp(at: Vector2) -> void:
	var lamp_post := _place("lamp", at, false, false)
	if lamp_post == null:
		return
	var lamp := board._point_light(Color(1.0, 0.72, 0.4), 0.0, 40.0, 30.0)
	lamp.position = lamp_post.position + Vector2(0, -22)
	board._air.add_child(lamp)
	_city_lights.append(lamp)


# ------------------------------------------------------------------ per frame

func update(delta: float) -> void:
	_elapsed += delta
	_panic = maxf(0.0, _panic - delta)
	_alarm = maxf(0.0, _alarm - delta)
	var night := board.day_night.night()
	for flame in _flames:
		var phase: float = flame.get_meta("phase")
		flame.frame = int((_elapsed + phase) * 9.0) % 4
	var flare := 1.0 + 0.8 * (_alarm / ALARM_TIME)
	for lamp in _fire_lights:
		var base: float = lamp.get_meta("energy")
		lamp.energy = base * flare * (0.8 + 0.2 * sin(_elapsed * 11.0 + lamp.position.x))
	for glow in _windows:
		glow.modulate = Color(1, 1, 1, clampf(0.15 + night, 0.0, 1.0))
	for lamp in _city_lights:
		lamp.energy = 0.9 * night
	_update_burning()
	_spawned_at_camps()
	for w in _walkers:
		_walk(w, delta)


func _walk(w: Walker, delta: float) -> void:
	if w.still:
		w.sprite.frame = 0
		return
	var speed := WALK_SPEED * w.speed
	if w.city and _panic > 0.0:
		speed *= PANIC_SPEED
	elif not w.city and _alarm > 0.0:
		speed *= 1.6
	if w.wait > 0.0 and not (w.city and _panic > 0.0):
		w.wait -= delta
		w.sprite.frame = 0
		return
	var to := w.target - w.sprite.position
	if to.length() < 1.5:
		w.target = _random_in(w.area)
		w.wait = _rng.randf_range(0.5, 3.5)
		return
	var step := to.normalized() * minf(speed * delta, to.length())
	w.sprite.position += step
	if absf(step.x) > 0.01:
		w.sprite.flip_h = step.x < 0.0
	w.frame_time += delta * speed / WALK_SPEED
	w.sprite.frame = int(w.frame_time * 8.0) % 4


## One more house burns for each share of lives lost.
func _update_burning() -> void:
	if _houses.is_empty() or sim.starting_lives <= 0:
		return
	var lost := 1.0 - clampf(float(sim.lives) / float(sim.starting_lives), 0.0, 1.0)
	var should := mini(_houses.size(), ceili(lost * _houses.size()))
	while _burning < should:
		var house := _houses[_burning]
		house.fire.append(_fire(house.roof + Vector2(-4, 2), 0.7))
		house.fire.append(_fire(house.roof + Vector2(5, 4), 0.55, false))
		house.fire.append(_smoke(house.roof + Vector2(0, -8), true, 12))
		_burning += 1


## Dust where the road leaves a camp as each enemy marches out.
func _spawned_at_camps() -> void:
	for enemy in sim.enemies:
		if _seen_enemies.has(enemy.id):
			continue
		_seen_enemies[enemy.id] = true
		for site in sim.landmarks:
			if site.kind == &"camp" and site.lanes.has(enemy.lane):
				var gate := _gate_point(site)
				board._burst(gate + Vector2(0, 8), Color(0.45, 0.38, 0.3, 0.6), 4, 10.0, false)
				break


func _on_wave_started(_wave_number: int) -> void:
	_alarm = ALARM_TIME


func _on_enemy_leaked(_enemy: SimEnemy) -> void:
	_panic = PANIC_TIME
	for site in sim.landmarks:
		if site.kind == &"city":
			board._burst(_center(site.anchor), Color(1.0, 0.45, 0.2), 10, 30.0)


func walker_count() -> int:
	return _walkers.size()


func house_count() -> int:
	return _houses.size()


func burning_count() -> int:
	return _burning
