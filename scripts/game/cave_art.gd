class_name CaveArt
extends Node
## Draws the enemy caves that break open during a run (see Caves), and their opening.
##
## A cave is a heap of split rock around a black maw with eyes burning inside, on a fan of churned
## earth, with a fresh-dug road from its mouth to the road it joins. When one opens the ground shakes,
## rock and dust burst out, the heap heaves up out of the earth and the dig tears open behind it.
##
## Pieces come from tools/art/caves/gen_caves.py. BoardArt owns the layers and lights; this only adds
## to them. It is a child node of BoardArt, so its signal connections go with the board.

const ART := "res://assets/art/game/caves/"
const CELL := 32.0
## Seconds the heap takes to heave up out of the ground.
const RISE_TIME := 1.6
## Half the width of the dug road, in art pixels (the map's roads are about 0.46 cells).
const DIG_HALF := 13.0

static var _info: Dictionary = {}

var board: BoardArt
var sim: RunSim
var biome := "meadow"
var _caves: Array[Shown] = []
var _elapsed := 0.0


## One cave on the board.
class Shown:
	var cave: Caves.Cave
	var sprite: Sprite2D
	var glow: Sprite2D
	var light: PointLight2D
	var dig: Sprite2D
	var rubble: Sprite2D
	## Seconds since it began to open; RISE_TIME and more once it stands.
	var age := 0.0
	var base: Vector2
	var light_energy := 0.0


static func info() -> Dictionary:
	if _info.is_empty() and FileAccess.file_exists(ART + "caves.json"):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART + "caves.json"))
		if parsed is Dictionary:
			_info = parsed
	return _info


static func piece(name: String) -> Dictionary:
	return (info().get("pieces", {}) as Dictionary).get(name, {})


static func has_art() -> bool:
	return not info().is_empty()


func build(p_board: BoardArt) -> void:
	board = p_board
	sim = board.sim
	var kinds: Array = info().get("biomes", [])
	biome = String(sim.config.map.biome) if kinds.has(String(sim.config.map.biome)) else "meadow"
	# Caves already open (a loaded run) stand there from the start.
	for cave in sim.caves:
		_show(cave, false)
	sim.cave_opened.connect(func(cave: Caves.Cave) -> void: _show(cave, true))


## The caves on the board, for tests and captures.
func shown() -> int:
	return _caves.size()


## True while a cave is still heaving up.
func is_opening() -> bool:
	for shown_cave in _caves:
		if shown_cave.age < RISE_TIME:
			return true
	return false


func _show(cave: Caves.Cave, opening: bool) -> void:
	var meta := piece("cave_" + biome)
	if meta.is_empty():
		return
	var shown_cave := Shown.new()
	shown_cave.cave = cave
	var centre := (Vector2(cave.cell) + Vector2(0.5, 0.5)) * CELL
	# The mouth sits on the cave's cell; the heap rises behind it.
	var foot: Array = meta.get("foot", [48, 68])
	var size: Array = meta["size"]
	var mouth: Array = meta.get("mouth", [48, 58])
	shown_cave.base = (centre + Vector2(0, float(foot[1]) - float(mouth[1]))).floor()

	shown_cave.dig = _dig_sprite(cave)
	if shown_cave.dig != null:
		board._ground.add_child(shown_cave.dig)
	var rubble_meta := piece("rubble_" + biome)
	if not rubble_meta.is_empty():
		shown_cave.rubble = Sprite2D.new()
		shown_cave.rubble.texture = load(ART + "rubble_%s.png" % biome)
		shown_cave.rubble.position = centre + Vector2(0, 2)
		board._ground.add_child(shown_cave.rubble)

	var sprite := Sprite2D.new()
	sprite.texture = BoardArt.lit_texture(ART + "cave_" + biome)
	sprite.centered = false
	# Drawn from its feet, so it can heave up out of the ground by scaling.
	sprite.offset = Vector2(-float(size[0]) * 0.5, -float(foot[1]))
	sprite.position = shown_cave.base
	board._actors.add_child(sprite)
	shown_cave.sprite = sprite
	if ResourceLoader.exists(ART + "cave_%s_glow.png" % biome):
		var glow := Sprite2D.new()
		glow.texture = load(ART + "cave_%s_glow.png" % biome)
		glow.centered = false
		glow.offset = sprite.offset
		glow.material = board._additive
		sprite.add_child(glow)
		shown_cave.glow = glow
	board._add_caster(sprite, (sprite.texture as CanvasTexture).diffuse_texture, sprite.offset, 0.7, sprite)
	var tint: Array = meta.get("glow_color", [255, 90, 30])
	shown_cave.light = board._point_light(Color8(int(tint[0]), int(tint[1]), int(tint[2])), 0.0, 70.0, 10.0)
	shown_cave.light.position = centre + Vector2(0, -2)
	shown_cave.light_energy = 0.9
	board._air.add_child(shown_cave.light)
	_hide_props(cave)
	_caves.append(shown_cave)
	if opening:
		_open(shown_cave, centre)
	else:
		shown_cave.age = RISE_TIME
		_pose(shown_cave)


## The ground shakes and splits, rock and dust burst out and the heap heaves up.
func _open(shown_cave: Shown, centre: Vector2) -> void:
	shown_cave.age = 0.0
	_pose(shown_cave)
	var dust := Color(0.55, 0.47, 0.38)
	var rock := Color(0.42, 0.4, 0.38)
	board._ring(centre, dust, 6.0, 70.0, 0.9, 2.0)
	board._ring(centre, Color(0.25, 0.2, 0.18), 2.0, 46.0, 0.6, 3.0)
	board._burst(centre, dust, 40, 60.0, false)
	board._pulse_light(centre, shown_cave.light.color, 3.0, 150.0, 1.4)
	for i in 4:
		var timer := get_tree().create_timer(0.25 + i * 0.3)
		timer.timeout.connect(func() -> void:
			if not is_instance_valid(board):
				return
			var at := centre + Vector2(randf_range(-26.0, 26.0), randf_range(-8.0, 10.0))
			board._burst(at, rock if i % 2 == 0 else dust, 22, 70.0, false)
			board._ring(at, dust, 4.0, 30.0, 0.5))
	# Dust drifts off the dig as it tears open.
	if shown_cave.cave.dig_points.size() >= 2:
		var points := shown_cave.cave.dig_points
		for k in range(0, points.size(), maxi(1, points.size() / 5)):
			var at: Vector2 = points[k] / BoardArt.SCALE
			var timer := get_tree().create_timer(0.1 + 0.12 * k / maxf(1.0, points.size() / 5.0))
			timer.timeout.connect(func() -> void:
				if is_instance_valid(board):
					board._burst(at, dust, 10, 30.0, false))
	SoundPlayer.sfx(&"skill_earthquake", null, 2.0, 0.75)
	SoundPlayer.sfx(&"structure_collapse", null, -2.0, 0.8)


## Hides the grass tufts and stones under the mound and on the dig.
func _hide_props(cave: Caves.Cave) -> void:
	var cells: Array[Vector2i] = []
	cells.append_array(cave.cells)
	cells.append_array(cave.dig)
	for cell in cells:
		for caster: BoardArt.Caster in board._props_by_cell.get(cell, []):
			caster.node.visible = false
			caster.blob.visible = false
			caster.sun.visible = false
		board._props_by_cell.erase(cell)


## The fresh-dug road from the cave's mouth to the road it joins, painted with the land's dirt.
func _dig_sprite(cave: Caves.Cave) -> Sprite2D:
	var meta := piece("dig_" + biome)
	if meta.is_empty() or cave.dig_points.size() < 2:
		return null
	var tile: Image = (load(ART + "dig_%s.png" % biome) as Texture2D).get_image()
	tile.decompress()
	var edge_rgb: Array = meta.get("edge", [40, 30, 20])
	var edge := Color8(int(edge_rgb[0]), int(edge_rgb[1]), int(edge_rgb[2]))
	var points := PackedVector2Array()
	for point in cave.dig_points:
		points.append(point / BoardArt.SCALE)
	var low := points[0]
	var high := points[0]
	for point in points:
		low = low.min(point)
		high = high.max(point)
	var margin := DIG_HALF + 3.0
	var origin := (low - Vector2(margin, margin)).floor()
	var size := Vector2i((high - origin + Vector2(margin, margin)).ceil())
	var mask := PackedByteArray()
	mask.resize(size.x * size.y)
	# Stamp a ragged disc every pixel along the line; thinner at the very end where it meets the road.
	var noise := FastNoiseLite.new()
	noise.seed = cave.cell.x * 131 + cave.cell.y
	noise.frequency = 0.15
	var walked := 0.0
	for i in range(1, points.size()):
		var a := points[i - 1] - origin
		var b := points[i] - origin
		var steps := maxi(1, ceili(a.distance_to(b)))
		for s in steps:
			var at := a.lerp(b, float(s) / steps)
			walked += a.distance_to(b) / steps
			var radius := DIG_HALF + noise.get_noise_1d(walked) * 2.5
			var r := ceili(radius)
			for dy in range(-r, r + 1):
				for dx in range(-r, r + 1):
					if dx * dx + dy * dy > radius * radius:
						continue
					var x := int(at.x) + dx
					var y := int(at.y) + dy
					if x >= 0 and y >= 0 and x < size.x and y < size.y:
						mask[y * size.x + x] = 1
	var image := Image.create(size.x, size.y, false, Image.FORMAT_RGBA8)
	var tw := tile.get_width()
	var th := tile.get_height()
	for y in size.y:
		for x in size.x:
			if mask[y * size.x + x] == 0:
				continue
			var border := false
			for o: Vector2i in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var nx := x + o.x
				var ny := y + o.y
				if nx < 0 or ny < 0 or nx >= size.x or ny >= size.y or mask[ny * size.x + nx] == 0:
					border = true
					break
			var colour := edge if border else tile.get_pixel(posmod(int(origin.x) + x, tw), posmod(int(origin.y) + y, th))
			image.set_pixel(x, y, colour)
	var sprite := Sprite2D.new()
	sprite.texture = ImageTexture.create_from_image(image)
	sprite.centered = false
	sprite.position = origin
	return sprite


func _pose(shown_cave: Shown) -> void:
	var t := clampf(shown_cave.age / RISE_TIME, 0.0, 1.0)
	# Heaves up fast, overshoots a little and settles, shaking all the while.
	var rise := 1.0 - pow(1.0 - t, 3.0) + sin(t * PI) * 0.08
	var shake := (1.0 - t) * 1.6
	shown_cave.sprite.scale = Vector2(1.0 + (1.0 - t) * 0.15, maxf(0.02, rise))
	shown_cave.sprite.position = shown_cave.base + Vector2(sin(_elapsed * 70.0) * shake, 0).round()
	var reveal := clampf(t * 1.6, 0.0, 1.0)
	if shown_cave.dig != null:
		shown_cave.dig.modulate.a = reveal
	if shown_cave.rubble != null:
		shown_cave.rubble.modulate.a = clampf(t * 3.0, 0.0, 1.0)
		shown_cave.rubble.scale = Vector2.ONE * (0.6 + 0.4 * clampf(t * 2.0, 0.0, 1.0))


func update(delta: float) -> void:
	_elapsed += delta
	var night := board.day_night.night()
	for shown_cave in _caves:
		if shown_cave.age < RISE_TIME:
			shown_cave.age += delta
			_pose(shown_cave)
		var flicker := 0.85 + 0.15 * sin(_elapsed * 5.3 + shown_cave.cave.cell.x) * sin(_elapsed * 3.1)
		# Brighter while the horde pours out of it.
		var busy := 1.4 if sim.state == RunSim.State.WAVE else 1.0
		shown_cave.light.energy = shown_cave.light_energy * (0.45 + 0.75 * night) * flicker * busy
		if shown_cave.glow != null:
			shown_cave.glow.modulate.a = (0.6 + 0.4 * night) * flicker
