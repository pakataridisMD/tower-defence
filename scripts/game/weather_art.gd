class_name WeatherArt
extends Node2D
## Draws the weather over a battle (see Weather): the wind that bends the trees and grass and blows
## leaves, dust or ash across the map in gusts, and the spells of rain, thunderstorm, snow, blizzard,
## ashfall or dust storm that roll in for a few waves. Rain darkens and wets the ground, a storm throws
## lightning, and snow settles on the ground while it falls and melts away after.
##
## BoardArt owns it: it lives in the air layer (art pixels), drives the shared sway shader of the
## props, and tints the light through ambient_tint() and sun_scale().

## How fast a spell comes in and goes out, in intensity per second (about 8 and 6 seconds).
const FADE_IN := 0.12
const FADE_OUT := 0.17
## Art pixels added around the map so the weather also covers its edges when zoomed out.
const MARGIN := 48.0
## How each kind of weather tints the light at full strength, and how much sun gets through.
const TINTS := {
	Weather.Kind.CLEAR: Color(1, 1, 1), Weather.Kind.RAIN: Color(0.74, 0.78, 0.88),
	Weather.Kind.STORM: Color(0.6, 0.64, 0.78), Weather.Kind.SNOW: Color(0.94, 0.97, 1.06),
	Weather.Kind.BLIZZARD: Color(0.84, 0.9, 1.02), Weather.Kind.ASH: Color(0.82, 0.74, 0.72),
	Weather.Kind.DUST: Color(1.0, 0.84, 0.66),
}
const SUN := {
	Weather.Kind.CLEAR: 1.0, Weather.Kind.RAIN: 0.45, Weather.Kind.STORM: 0.25, Weather.Kind.SNOW: 0.7,
	Weather.Kind.BLIZZARD: 0.45, Weather.Kind.ASH: 0.55, Weather.Kind.DUST: 0.5,
}
## What the wind carries on a clear day in each land: [colours, how many at once].
const DEBRIS := {
	&"meadow": [[Color(0.52, 0.66, 0.25), Color(0.78, 0.62, 0.24), Color(0.62, 0.42, 0.2)], 26],
	&"nature": [[Color(0.36, 0.6, 0.22), Color(0.5, 0.72, 0.26), Color(0.72, 0.58, 0.22)], 34],
	&"storm": [[Color(0.66, 0.7, 0.52), Color(0.58, 0.58, 0.5), Color(0.8, 0.78, 0.6)], 30],
	&"water": [[Color(0.92, 0.96, 1.0), Color(0.82, 0.9, 0.98)], 40],
	&"fire": [[Color(0.32, 0.3, 0.3), Color(0.5, 0.46, 0.44)], 30],
	&"earth": [[Color(0.82, 0.66, 0.44), Color(0.7, 0.54, 0.34)], 34],
	&"void": [[Color(0.42, 0.3, 0.55), Color(0.28, 0.22, 0.36)], 22],
	&"heart": [[Color(0.95, 0.85, 0.9), Color(0.7, 0.8, 0.45), Color(0.95, 0.92, 0.7)], 26],
}

var weather: Weather
var board: BoardArt
## The weather on show now, and how strongly (0 to 1). A new kind only comes in once the old one has
## faded out.
var kind := Weather.Kind.CLEAR
var intensity := 0.0
## How hard the wind blows right now (the map's wind, raised by the weather).
var wind_now := 1.0
## Snow lying on the ground (0 to 1) and how wet the ground is after rain (0 to 1).
var snow_cover := 0.0
var wetness := 0.0

## Set by the capture tool to hold one kind of weather at full strength.
var _forced := -1
var _size := Vector2.ZERO
var _phase := 0.0
var _gust_at := -INF
var _gust_power := 0.0
var _gust_speed := 260.0
var _gust_wait := 2.0
var _along_min := 0.0
var _along_max := 0.0
var _flash := 0.0
var _next_strike := 4.0
var _rng := RandomNumberGenerator.new()

var _streak: ImageTexture
var _drop: ImageTexture
var _flake: ImageTexture
var _flake_big: ImageTexture
var _leaf: ImageTexture
var _haze: GradientTexture2D

var _debris: CPUParticles2D
## Every kind of weather's emitters.
var _emitters: Dictionary = {}
var _cover: Sprite2D


func build(p_board: BoardArt, p_weather: Weather) -> void:
	board = p_board
	weather = p_weather
	_rng.seed = hash(String(weather.map_id)) + 17
	_size = board.sim.config.map.size_in_pixels() / BoardArt.SCALE
	for corner in [Vector2.ZERO, Vector2(_size.x, 0), Vector2(0, _size.y), _size]:
		var along: float = (corner as Vector2).dot(weather.wind_dir)
		_along_min = minf(_along_min, along)
		_along_max = maxf(_along_max, along)
	_make_textures()
	_build_debris()
	_build_rain()
	_build_snow()
	_build_ash()
	_build_dust()
	_build_cover()
	wind_now = weather.wind
	_show(_target_kind())
	update(0.0)


## Holds one kind of weather at full strength (or lets the waves decide again with -1).
func force(forced_kind: int) -> void:
	_forced = forced_kind
	if forced_kind >= 0:
		_show(forced_kind as Weather.Kind)
		intensity = 1.0
		snow_cover = _cover_cap() if Weather.is_snow(kind) else 0.0
		wetness = 1.0 if Weather.is_wet(kind) else 0.0


func _target_kind() -> Weather.Kind:
	if _forced >= 0:
		return _forced as Weather.Kind
	var sim := board.sim
	if sim.state == RunSim.State.WON:
		return Weather.Kind.CLEAR
	return weather.kind_at(sim.wave_number())


func update(delta: float) -> void:
	var target := _target_kind()
	if target == kind:
		intensity = minf(1.0, intensity + FADE_IN * delta) if kind != Weather.Kind.CLEAR else 0.0
	else:
		intensity = maxf(0.0, intensity - FADE_OUT * delta)
		if intensity <= 0.0:
			_show(target)
	var boost: float = Weather.WIND_BOOST[kind]
	wind_now = weather.wind * lerpf(1.0, boost, intensity)
	var falling := intensity if Weather.is_snow(kind) else 0.0
	if falling > 0.2:
		snow_cover = minf(_cover_cap(), snow_cover + 0.02 * falling * delta)
	else:
		snow_cover = maxf(0.0, snow_cover - 0.008 * delta)
	var raining := intensity if Weather.is_wet(kind) else 0.0
	wetness = clampf(wetness + (raining - wetness) * minf(1.0, delta * (0.25 if raining > wetness else 0.05)), 0.0, 1.0)
	_cover.modulate = Color(1, 1, 1, snow_cover)
	_cover.visible = snow_cover > 0.005
	board._ground.modulate = Color(1, 1, 1).lerp(Color(0.78, 0.82, 0.9), wetness * 0.8)
	for each: Weather.Kind in _emitters:
		for emitter: CPUParticles2D in _emitters[each]:
			emitter.modulate = Color(1, 1, 1, intensity if each == kind else 0.0)
	_debris.modulate = Color(1, 1, 1, clampf(0.55 + 0.25 * wind_now, 0.0, 1.0))
	_update_wind(delta)
	_update_lightning(delta)


## How thick the snow can lie: thicker in a blizzard.
func _cover_cap() -> float:
	return 0.6 if kind == Weather.Kind.BLIZZARD else 0.45


## Turns on the emitters of a new kind of weather (the old ones stop and their last flakes fall).
func _show(next: Weather.Kind) -> void:
	kind = next
	for each: Weather.Kind in _emitters:
		for emitter: CPUParticles2D in _emitters[each]:
			emitter.emitting = each == kind
	if kind == Weather.Kind.STORM:
		_next_strike = _rng.randf_range(2.0, 5.0)


## The light under the weather: grey under rain, cold under snow, brown in a dust storm, and white for
## an instant when lightning strikes.
func ambient_tint() -> Color:
	var tint: Color = Color(1, 1, 1).lerp(TINTS[kind], intensity)
	return tint + Color(_flash, _flash, _flash * 1.1, 0.0) * 0.9


func sun_scale() -> float:
	return lerpf(1.0, SUN[kind], intensity) + _flash * 0.8


# ------------------------------------------------------------------ wind

func _update_wind(delta: float) -> void:
	_phase += delta * (1.4 + 0.7 * wind_now)
	_gust_wait -= delta
	if _gust_wait <= 0.0:
		# A gust front sweeps across the map from upwind: the trees bow as it passes.
		_gust_at = _along_min - 160.0
		_gust_speed = _rng.randf_range(220.0, 340.0) * (0.8 + 0.2 * wind_now)
		_gust_power = _rng.randf_range(1.6, 3.2) * wind_now
		_gust_wait = _rng.randf_range(3.5, 8.0) / maxf(0.6, wind_now * 0.7)
	_gust_at += _gust_speed * delta
	var world := board._world.get_global_transform()
	var material := board._sway_material
	material.set_shader_parameter("strength", 0.7 + 0.35 * wind_now)
	material.set_shader_parameter("phase", _phase)
	material.set_shader_parameter("lean", 0.55 * wind_now)
	material.set_shader_parameter("gust", _gust_power if _gust_at < _along_max + 200.0 else 0.0)
	material.set_shader_parameter("gust_at", _gust_at)
	material.set_shader_parameter("wind_dir", weather.wind_dir)
	material.set_shader_parameter("map_origin", world.origin)
	material.set_shader_parameter("map_scale", maxf(0.001, world.get_scale().x))


## Where a gust front is now (along the wind, in map art pixels) and how hard it pushes, for tests.
func gust() -> Vector2:
	return Vector2(_gust_at, _gust_power)


# ------------------------------------------------------------------ lightning

func _update_lightning(delta: float) -> void:
	_flash = maxf(0.0, _flash - delta * 5.0)
	if kind != Weather.Kind.STORM or intensity < 0.5:
		return
	_next_strike -= delta
	if _next_strike > 0.0:
		return
	_next_strike = _rng.randf_range(3.5, 9.0)
	strike(Vector2(_rng.randf_range(0.1, 0.9) * _size.x, _rng.randf_range(0.15, 0.95) * _size.y))


## A bolt of lightning comes down on this point (art pixels): the sky flashes twice, the bolt forks
## down from above and the ground where it lands lights up.
func strike(at: Vector2) -> void:
	_flash = 1.0
	var tween := create_tween()
	tween.tween_interval(0.13)
	tween.tween_callback(func() -> void: _flash = maxf(_flash, 0.65))
	var top := at + Vector2(_rng.randf_range(-30.0, 30.0), -_rng.randf_range(150.0, 230.0))
	var points := _jagged(top, at, 11, 9.0)
	_bolt(points, 1.0)
	# One fork splits off part of the way down.
	var fork_from: Vector2 = points[_rng.randi_range(3, 6)]
	_bolt(_jagged(fork_from, fork_from + Vector2(_rng.randf_range(-40.0, 40.0), _rng.randf_range(25.0, 50.0)), 5, 5.0), 0.6)
	board._pulse_light(at, Color(0.75, 0.85, 1.0), 4.0, 150.0, 0.45)
	board._ring(at, Color(0.8, 0.9, 1.0), 2.0, 14.0, 0.35, 1.0)
	board._sparks(at, Color(0.85, 0.95, 1.0), 8, 12.0)


func _jagged(from: Vector2, to: Vector2, steps: int, wander: float) -> PackedVector2Array:
	var points := PackedVector2Array([from])
	var side := (to - from).orthogonal().normalized()
	for i in range(1, steps):
		var t := float(i) / steps
		points.append(from.lerp(to, t) + side * _rng.randf_range(-wander, wander))
	points.append(to)
	return points


func _bolt(points: PackedVector2Array, power: float) -> void:
	for layer in [[5.0, Color(0.55, 0.7, 1.0, 0.35)], [1.6, Color(0.92, 0.96, 1.0, 1.0)]]:
		var line := Line2D.new()
		line.points = points
		line.width = float(layer[0]) * power
		line.default_color = layer[1]
		line.material = board._additive
		line.joint_mode = Line2D.LINE_JOINT_SHARP
		add_child(line)
		var tween := line.create_tween()
		tween.tween_property(line, "modulate:a", 0.0, 0.4).set_delay(0.06)
		tween.tween_callback(line.queue_free)


# ------------------------------------------------------------------ the emitters

func _make_textures() -> void:
	_streak = _image(1, 11, func(_x: int, y: int) -> Color: return Color(1, 1, 1, 0.2 + 0.8 * float(y) / 10.0))
	_drop = _image(3, 1, func(x: int, _y: int) -> Color: return Color(1, 1, 1, 1.0 if x == 1 else 0.55))
	_flake = _image(1, 1, func(_x: int, _y: int) -> Color: return Color.WHITE)
	_flake_big = _image(2, 2, func(x: int, y: int) -> Color: return Color(1, 1, 1, 1.0 if x == y else 0.6))
	_leaf = _image(2, 1, func(_x: int, _y: int) -> Color: return Color.WHITE)
	_haze = board._radial(64, [Color(1, 1, 1, 1), Color(1, 1, 1, 0.4), Color(1, 1, 1, 0)], [0.0, 0.45, 1.0])


func _image(w: int, h: int, paint: Callable) -> ImageTexture:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		for x in w:
			img.set_pixel(x, y, paint.call(x, y))
	return ImageTexture.create_from_image(img)


## An emitter over the whole map, with local coordinates so it stays on the map as the camera moves.
func _emitter(amount: int, lifetime: float, texture: Texture2D, parent: Node2D = self) -> CPUParticles2D:
	var p := CPUParticles2D.new()
	p.amount = maxi(1, amount)
	p.lifetime = lifetime
	p.texture = texture
	p.emission_shape = CPUParticles2D.EMISSION_SHAPE_RECTANGLE
	p.emission_rect_extents = _size / 2.0 + Vector2(MARGIN, MARGIN)
	p.position = _size / 2.0
	p.local_coords = true
	p.preprocess = lifetime
	p.emitting = false
	parent.add_child(p)
	return p


func _fade(colors: Array, offsets: Array = []) -> Gradient:
	var at := offsets.duplicate()
	if at.is_empty():
		for i in colors.size():
			at.append(float(i) / maxf(1.0, colors.size() - 1))
	return board._gradient(colors, at)


## How many of something fit the map at this density (one per `area` square art pixels).
func _count(area: float, low: int, high: int) -> int:
	return clampi(int(_size.x * _size.y / area), low, high)


func _slant(fall: float, push: float) -> Vector2:
	return Vector2(weather.wind_dir.x * push, fall).normalized()


func _build_debris() -> void:
	var spec: Array = DEBRIS.get(weather.biome, DEBRIS[&"meadow"])
	var colors: Array = spec[0]
	_debris = _emitter(int(float(spec[1]) * clampf(weather.wind, 0.6, 2.0)), 8.0, _leaf)
	_debris.direction = weather.wind_dir
	_debris.spread = 14.0
	_debris.initial_velocity_min = 22.0 + 14.0 * weather.wind
	_debris.initial_velocity_max = 40.0 + 26.0 * weather.wind
	_debris.gravity = Vector2(0, 3.0)
	_debris.angle_min = 0.0
	_debris.angle_max = 360.0
	_debris.angular_velocity_min = -220.0
	_debris.angular_velocity_max = 220.0
	var ramp: Array = []
	for c: Color in colors:
		ramp.append(c)
	_debris.color_initial_ramp = _fade(ramp)
	_debris.color_ramp = _fade([Color(1, 1, 1, 0), Color(1, 1, 1, 1), Color(1, 1, 1, 1), Color(1, 1, 1, 0)], [0.0, 0.1, 0.85, 1.0])
	_debris.emitting = true


func _build_rain() -> void:
	for spec in [[Weather.Kind.RAIN, 900.0, 300.0, 360.0, 0.3, Color(0.8, 0.86, 0.98, 0.8)],
			[Weather.Kind.STORM, 600.0, 380.0, 450.0, 0.55, Color(0.82, 0.88, 1.0, 0.9)]]:
		var rain := _emitter(_count(spec[1], 300, 2400), 0.36, _streak)
		rain.position.y -= 40.0
		rain.direction = _slant(1.0, float(spec[4]) * weather.wind)
		rain.spread = 2.0
		rain.initial_velocity_min = spec[2]
		rain.initial_velocity_max = spec[3]
		rain.particle_flag_align_y = true
		var drop: Color = spec[5]
		rain.color_ramp = _fade([Color(drop, 0.0), drop, drop, Color(drop, 0.0)], [0.0, 0.15, 0.8, 1.0])
		# Drops landing: small splashes all over the ground.
		var splash := _emitter(_count(float(spec[1]) * 2.5, 80, 600), 0.28, _drop, board._shadows)
		splash.scale_amount_min = 0.7
		splash.scale_amount_max = 1.3
		var curve := Curve.new()
		curve.add_point(Vector2(0, 0.5))
		curve.add_point(Vector2(1, 1.6))
		splash.scale_amount_curve = curve
		splash.color_ramp = _fade([Color(0.85, 0.92, 1.0, 0.75), Color(0.85, 0.92, 1.0, 0.0)])
		_emitters[spec[0]] = [rain, splash]


func _build_snow() -> void:
	for spec in [[Weather.Kind.SNOW, 1.0, 14.0, 28.0, 0.6], [Weather.Kind.BLIZZARD, 2.0, 40.0, 75.0, 2.4]]:
		var many := float(spec[1])
		var small := _emitter(_count(1100.0 / many, 300, 2400), 6.0, _flake_big)
		var big := _emitter(_count(3000.0 / many, 120, 900), 5.0, _flake_big)
		big.scale_amount_min = 1.5
		big.scale_amount_max = 2.0
		for flakes: CPUParticles2D in [small, big]:
			flakes.direction = _slant(1.0, float(spec[4]) * weather.wind)
			flakes.spread = 18.0
			flakes.initial_velocity_min = spec[2]
			flakes.initial_velocity_max = spec[3]
			flakes.gravity = Vector2(weather.wind_dir.x * 4.0 * many, 3.0)
			flakes.damping_min = 1.0
			flakes.damping_max = 3.0
			flakes.color_ramp = _fade([Color(1, 1, 1, 0), Color(0.96, 0.98, 1.0, 0.95), Color(0.96, 0.98, 1.0, 0.9), Color(1, 1, 1, 0)], [0.0, 0.12, 0.85, 1.0])
		_emitters[spec[0]] = [small, big]


func _build_ash() -> void:
	var void_land := weather.biome == &"void"
	var flake_color := Color(0.4, 0.3, 0.5) if void_land else Color(0.5, 0.47, 0.45)
	var glow_color := Color(0.75, 0.45, 1.0) if void_land else Color(1.0, 0.5, 0.18)
	var ash := _emitter(_count(1800.0, 150, 1100), 7.0, _flake_big)
	ash.direction = _slant(1.0, 0.7 * weather.wind)
	ash.spread = 25.0
	ash.initial_velocity_min = 8.0
	ash.initial_velocity_max = 20.0
	ash.gravity = Vector2(weather.wind_dir.x * 3.0, 2.0)
	ash.scale_amount_min = 0.5
	ash.scale_amount_max = 1.0
	ash.color_ramp = _fade([Color(flake_color, 0), Color(flake_color, 0.9), Color(flake_color, 0.8), Color(flake_color, 0)], [0.0, 0.15, 0.8, 1.0])
	# Live sparks drifting up through the ash.
	var embers := _emitter(_count(9000.0, 30, 200), 4.0, _flake)
	embers.material = board._additive
	embers.direction = Vector2(weather.wind_dir.x * 0.6, -1.0).normalized()
	embers.spread = 30.0
	embers.initial_velocity_min = 6.0
	embers.initial_velocity_max = 18.0
	embers.color_ramp = _fade([Color(glow_color, 0), glow_color, Color(glow_color, 0)])
	_emitters[Weather.Kind.ASH] = [ash, embers]


func _build_dust() -> void:
	var grains := _emitter(_count(1500.0, 200, 1200), 2.6, _flake)
	grains.direction = Vector2(weather.wind_dir.x, weather.wind_dir.y * 0.4 + 0.08).normalized()
	grains.spread = 6.0
	grains.initial_velocity_min = 90.0
	grains.initial_velocity_max = 160.0
	var sand := Color(0.86, 0.7, 0.48)
	grains.color_ramp = _fade([Color(sand, 0), Color(sand, 0.8), Color(sand, 0.7), Color(sand, 0)], [0.0, 0.1, 0.85, 1.0])
	# Big soft clouds of dust rolling across the map.
	var clouds := _emitter(_count(24000.0, 14, 70), 7.0, _haze)
	clouds.direction = weather.wind_dir
	clouds.spread = 8.0
	clouds.initial_velocity_min = 35.0
	clouds.initial_velocity_max = 60.0
	clouds.scale_amount_min = 2.5
	clouds.scale_amount_max = 5.0
	var haze := Color(0.8, 0.64, 0.44)
	clouds.color_ramp = _fade([Color(haze, 0), Color(haze, 0.16), Color(haze, 0.14), Color(haze, 0)], [0.0, 0.25, 0.75, 1.0])
	_emitters[Weather.Kind.DUST] = [grains, clouds]


## Snow that settles in drifts on the ground (patchy, thicker in the hollows of the noise).
func _build_cover() -> void:
	var noise := FastNoiseLite.new()
	noise.seed = _rng.randi()
	noise.frequency = 0.045
	noise.fractal_octaves = 3
	var tex := NoiseTexture2D.new()
	tex.width = maxi(8, int(_size.x / 4.0))
	tex.height = maxi(8, int(_size.y / 4.0))
	tex.noise = noise
	tex.color_ramp = _fade([Color(1, 1, 1, 0.0), Color(1, 1, 1, 0.0), Color(1, 1, 1, 0.7), Color(1, 1, 1, 0.95)], [0.0, 0.42, 0.68, 1.0])
	_cover = Sprite2D.new()
	_cover.texture = tex
	_cover.centered = false
	_cover.scale = Vector2(4, 4)
	# Smooth drifts, not 4-pixel blocks.
	_cover.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR
	_cover.visible = false
	board._ground.add_child(_cover)
