class_name CitadelArt
extends Node2D
## Draws Nhal Vorath, the enemy citadel of the final assault, from the art made by
## tools/art/citadel/gen_citadel.py: the lit fortress, the fire in its windows and cracks (flickering),
## fire cracks that open as the army breaks it, its lights, and the ruin it leaves when it falls.
##
## BoardArt makes one when the run has a citadel and calls update() every frame. It sits in art
## pixels, like everything under BoardArt's world node.

const DIR := "res://assets/art/game/citadel/"
const FLICKER_FPS := 7.0
## Seconds the citadel shakes and burns before the ruin shows.
const COLLAPSE_TIME := 2.4

var structure: SimEnemy
var meta: Dictionary = {}
var fallen := false

var _art: BoardArt
var _body: Sprite2D
var _glow: Sprite2D
var _cracks: Sprite2D
var _ruin: Sprite2D
var _ruin_glow: Sprite2D
var _frames: Array[Texture2D] = []
var _lights: Array[PointLight2D] = []
var _light_energy: Array[float] = []
var _time := 0.0
var _last_health := -1.0
var _shake := 0.0
var _collapse := -1.0
var _noise := FastNoiseLite.new()


static func has_art() -> bool:
	return FileAccess.file_exists(DIR + "citadel.json")


static func read_meta() -> Dictionary:
	if not has_art():
		return {}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DIR + "citadel.json"))
	return parsed if parsed is Dictionary else {}


## True for a building drawn by this art rather than as an enemy sprite.
static func draws(data: EnemyData) -> bool:
	return data.structure and data.tags.has(&"citadel") and has_art()


func build(art: BoardArt, p_structure: SimEnemy) -> void:
	_art = art
	structure = p_structure
	meta = read_meta()
	_noise.frequency = 1.3
	var cells: Array = meta.get("cells", [30, -2, 42, 24])
	position = Vector2(float(cells[0]), float(cells[1])) * BoardArt.CELL_ART
	_body = _sprite(BoardArt.lit_texture(DIR + "citadel"))
	add_child(_body)
	for f in int(meta.get("frames", 1)):
		_frames.append(load(DIR + "citadel_glow_%d.png" % f))
	_glow = _sprite(_frames[0])
	_glow.material = art._additive
	add_child(_glow)
	_cracks = _sprite(load(DIR + "citadel_cracks.png"))
	_cracks.material = art._additive
	_cracks.modulate = Color(1, 1, 1, 0)
	add_child(_cracks)
	for entry: Dictionary in meta.get("lights", []):
		var at: Array = entry["at"]
		var kind: String = entry["kind"]
		var color := Color(1.0, 0.5, 0.2)
		var energy := 1.1
		var radius := 70.0
		match kind:
			"sun":
				color = Color(0.62, 0.35, 1.0)
				energy = 1.6
				radius = 150.0
			"gate":
				radius = 90.0
				energy = 1.3
			"brazier":
				radius = 50.0
		var light := art._point_light(color, energy, radius, 30.0)
		light.position = Vector2(at[0], at[1])
		add_child(light)
		_lights.append(light)
		_light_energy.append(energy)


func _sprite(texture: Texture2D) -> Sprite2D:
	var sprite := Sprite2D.new()
	sprite.texture = texture
	sprite.centered = false
	return sprite


## Where the citadel's bolts come from: the black sun on its spire, in board (screen) pixels.
func bolt_origin() -> Vector2:
	for entry: Dictionary in meta.get("lights", []):
		if entry["kind"] == "sun":
			var at: Array = entry["at"]
			return (position + Vector2(at[0], at[1])) * BoardArt.SCALE
	return structure.position


## The gates the roads start at, in board pixels.
func gate_points() -> Array[Vector2]:
	var out: Array[Vector2] = []
	for at: Array in meta.get("gates", []):
		out.append((position + Vector2(at[0], at[1])) * BoardArt.SCALE)
	return out


func update(delta: float, vulnerable: bool) -> void:
	_time += delta
	if fallen:
		return
	if not structure.alive and _collapse < 0.0:
		_collapse = 0.0
	if _collapse >= 0.0:
		_advance_collapse(delta)
		return
	_glow.texture = _frames[int(_time * FLICKER_FPS) % _frames.size()]
	var flicker := 0.88 + 0.12 * _noise.get_noise_1d(_time * 2.0)
	for i in _lights.size():
		_lights[i].energy = _light_energy[i] * (flicker + 0.08 * sin(_time * 3.1 + i))
	# The cracks open as it is broken; each blow shakes it a little.
	var hurt := 1.0 - clampf(structure.health / maxf(1.0, structure.max_health), 0.0, 1.0)
	_cracks.modulate.a = clampf(hurt * 1.4, 0.0, 1.0) * (0.8 + 0.2 * sin(_time * 5.0)) if vulnerable else 0.0
	if _last_health >= 0.0 and structure.health < _last_health - 0.002 * structure.max_health:
		_shake = minf(_shake + 0.25, 1.0)
	_last_health = structure.health
	_shake = maxf(0.0, _shake - delta * 2.5)
	var jolt := Vector2(_noise.get_noise_2d(_time * 40.0, 0.0), _noise.get_noise_2d(0.0, _time * 40.0)) * _shake * 2.0
	_body.position = jolt.round()
	_glow.position = _body.position
	_cracks.position = _body.position


## It shakes, every crack burns white, and it sinks into its ruin.
func _advance_collapse(delta: float) -> void:
	_collapse += delta
	var t := clampf(_collapse / COLLAPSE_TIME, 0.0, 1.0)
	_cracks.modulate.a = 1.0
	_cracks.modulate = Color(1.0 + t, 1.0 + t * 0.6, 1.0, 1.0)
	var jolt := Vector2(_noise.get_noise_2d(_time * 60.0, 0.0), _noise.get_noise_2d(0.0, _time * 60.0)) * (2.0 + 4.0 * t)
	_body.position = jolt.round() + Vector2(0, roundf(t * t * 18.0))
	_glow.position = _body.position
	_cracks.position = _body.position
	for i in _lights.size():
		_lights[i].energy = _light_energy[i] * (1.0 + 2.0 * t)
	if t < 1.0:
		return
	fallen = true
	for child in [_body, _glow, _cracks]:
		child.queue_free()
	for light in _lights:
		light.energy *= 0.25
	_ruin = _sprite(BoardArt.lit_texture(DIR + "ruin"))
	add_child(_ruin)
	_ruin_glow = _sprite(load(DIR + "ruin_glow.png"))
	_ruin_glow.material = _art._additive
	add_child(_ruin_glow)
