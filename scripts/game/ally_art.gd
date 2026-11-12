class_name AllyArt
extends RefCounted
## Draws the army the player musters in the counter-attack, from the strips made by
## tools/art/pix2d/gen_allies_art.py (assets/art/game/allies/). A soldier walks while it marches,
## stands at ease in the line between blows, strikes, flinches from a heavy blow, raises its weapon
## and cries out when it shouts, and falls. A champion is the hero's own board sprite, moved by hand:
## a marching bob, breathing at rest, a wind-up and lunge with a slash of light, a stagger when hit,
## a leap with a flare of light for its war cry, and a fall. Units with no art are drawn by BoardView
## as plain markers.
##
## The sim puts every unit of a road on the road's middle line; here each one gets its own place
## across the road, so a squad stands as a rank and not as one blob.
##
## BoardArt owns one and calls sync() every frame. BoardView reads anchor() and top() to put health
## bars and speech over the units, and ArmyVoice calls cry() when a unit shouts.

const DIR := "res://assets/art/game/allies/"
const HERO_DIR := "res://assets/art/heroes/board/"
## Seconds a fallen unit lies before it fades.
const CORPSE_LINGER := 1.6
const MAX_CORPSES := 40
## Board pixels a unit may stand off the middle of its road, either side.
const SPREAD := 18.0
## Board pixels from the gate within which the army crowds the wall and its ranks open up.
const GATE_CROWD := 90.0
## Share of its health one blow must take for a unit to flinch, and the least time between flinches.
const HURT_SHARE := 0.07
const HURT_REST := 0.9
## A champion's blow: wind-up, strike and recovery, in seconds.
const CHAMPION_SWING := 0.42
## Seconds of a war cry when nothing says how long.
const CRY_TIME := 0.9
## Seconds a champion's slash of light lasts.
const SLASH_TIME := 0.22

static var _meta: Dictionary = {}

var _art: BoardArt
var _visuals: Dictionary[int, Visual] = {}
var _corpses: Array[Corpse] = []
var _slashes: Array[Slash] = []
var _textures: Dictionary[String, CanvasTexture] = {}
## Ally id -> seconds of war cry asked for before its visual existed.
var _pending_cries: Dictionary[int, float] = {}


class Visual:
	var ally: SimAlly
	var root: Node2D
	var body: Sprite2D
	var light: PointLight2D
	var caster: BoardArt.Caster
	## Strips by animation (&"walk", &"idle", &"attack", &"hurt", &"cry", &"death") with frame counts and speeds.
	var strips: Dictionary = {}
	var anim := &"walk"
	var anim_time := 0.0
	var walk_time := 0.0
	var idle_time := 0.0
	var last_health := 0.0
	var flash := 0.0
	var last_cooldown := 0.0
	var champion := false
	var size := Vector2.ZERO
	## Art pixels from the feet to the top of the head.
	var height := 40.0
	## Board pixels off the middle of the road, across it.
	var lateral := 0.0
	var hurt_rest := 0.0
	## Seconds of war cry left.
	var cry_left := 0.0
	var cry_length := 0.0
	## A champion's stagger, fading.
	var stagger := 0.0
	var light_energy := 0.9
	var slashed := false


class Corpse:
	var sprite: Sprite2D
	var frames := 1
	var fps := 10.0
	var time := 0.0
	## A champion has no death strip: its sprite topples this way (+1 or -1).
	var topple := 0.0


class Slash:
	var node: Node2D
	var color: Color
	var time := 0.0
	var facing := 1.0


static func meta() -> Dictionary:
	if _meta.is_empty() and FileAccess.file_exists(DIR + "allies.json"):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DIR + "allies.json"))
		if parsed is Dictionary:
			_meta = parsed
	return _meta


## True when this unit has art of its own (a champion always does, through its hero).
static func has_art(data: AllyData) -> bool:
	if data.is_champion():
		return ResourceLoader.exists(HERO_DIR + "%s.png" % data.hero)
	return meta().has(String(data.id))


## Board pixels off the middle of the road for a unit, the same every frame: champions keep the middle.
static func lateral_for(ally: SimAlly) -> float:
	if ally.is_champion():
		return 0.0
	return (fposmod(float(ally.id) * 0.618034, 1.0) * 2.0 - 1.0) * SPREAD


func _init(art: BoardArt) -> void:
	_art = art


func _strip(id: StringName, anim: String) -> CanvasTexture:
	var key := "%s_%s" % [id, anim]
	if _textures.has(key):
		return _textures[key]
	var tex := CanvasTexture.new()
	tex.diffuse_texture = load(DIR + key + ".png")
	if ResourceLoader.exists(DIR + key + "_n.png"):
		tex.normal_texture = load(DIR + key + "_n.png")
	_textures[key] = tex
	return tex


func sync(delta: float) -> void:
	var seen: Dictionary[int, bool] = {}
	for ally in _art.sim.allies:
		if not ally.alive:
			continue
		seen[ally.id] = true
		var visual: Visual = _visuals.get(ally.id)
		if visual == null:
			if not has_art(ally.data):
				continue
			visual = _make(ally)
			_visuals[ally.id] = visual
			if _pending_cries.has(ally.id):
				_start_cry(visual, _pending_cries[ally.id])
				_pending_cries.erase(ally.id)
		_update(visual, delta)
	for id in _visuals.keys():
		if not seen.has(id):
			var visual: Visual = _visuals[id]
			_leave_corpse(visual)
			_art._remove_caster(visual.caster)
			visual.root.queue_free()
			_visuals.erase(id)
	_advance_corpses(delta)
	_advance_slashes(delta)


## The unit raises its weapon and cries out for a while (its war cry strip, or a champion's leap).
func cry(ally: SimAlly, seconds: float = 0.0) -> void:
	var visual: Visual = _visuals.get(ally.id)
	if visual == null:
		_pending_cries[ally.id] = seconds
		return
	_start_cry(visual, seconds)


func is_crying(ally: SimAlly) -> bool:
	var visual: Visual = _visuals.get(ally.id)
	return visual != null and visual.cry_left > 0.0


## The animation a unit shows now, for tests: &"walk", &"idle", &"attack", &"hurt" or &"cry".
func anim_of(ally: SimAlly) -> StringName:
	var visual: Visual = _visuals.get(ally.id)
	return visual.anim if visual != null else &""


## Where a unit's feet are drawn, in board pixels: its place on the road plus its place in the rank.
func anchor(ally: SimAlly) -> Vector2:
	var visual: Visual = _visuals.get(ally.id)
	if visual == null:
		return ally.position + _across(ally) * lateral_for(ally)
	return visual.root.position * BoardArt.SCALE


## The top of a unit's head as drawn, in board pixels, for its health bar and its words.
func top(ally: SimAlly) -> Vector2:
	var visual: Visual = _visuals.get(ally.id)
	if visual == null:
		return anchor(ally) + Vector2(0, -(44.0 if ally.is_champion() else 34.0) * BoardArt.SCALE)
	var lift := visual.body.position.y if visual.champion else 0.0
	return (visual.root.position + Vector2(0, lift - visual.height)) * BoardArt.SCALE


## The unit's road direction turned a quarter: the way across the road.
func _across(ally: SimAlly) -> Vector2:
	var curves := _art.sim.lane_curves
	if ally.lane < 0 or ally.lane >= curves.size():
		return Vector2.DOWN
	var curve := curves[ally.lane]
	var ahead := curve.sample_baked(maxf(0.0, ally.progress - 8.0))
	var behind := curve.sample_baked(ally.progress + 8.0)
	var along := ahead - behind
	if along.length_squared() < 0.01:
		return Vector2.DOWN
	var across := along.normalized().orthogonal()
	return across if across.y >= 0.0 else -across


func _make(ally: SimAlly) -> Visual:
	var visual := Visual.new()
	visual.ally = ally
	visual.last_health = ally.health
	visual.last_cooldown = ally.cooldown
	visual.walk_time = randf()
	visual.idle_time = randf() * 3.0
	visual.lateral = lateral_for(ally)
	visual.root = Node2D.new()
	visual.root.position = _pos(ally, visual.lateral)
	_art._actors.add_child(visual.root)
	visual.body = Sprite2D.new()
	visual.body.centered = false
	visual.root.add_child(visual.body)
	var silhouette: Texture2D
	if ally.is_champion():
		visual.champion = true
		var texture: Texture2D = load(HERO_DIR + "%s.png" % ally.data.hero)
		visual.size = texture.get_size()
		visual.height = visual.size.y - 2.0
		visual.body.texture = texture
		visual.body.offset = Vector2(-visual.size.x * 0.5, -visual.size.y + 2.0)
		silhouette = texture
		visual.light = _art._point_light(_champion_color(ally).lerp(Color.WHITE, 0.3), visual.light_energy, 80.0, 40.0)
		visual.light.position = Vector2(0, -visual.size.y * 0.6)
		visual.root.add_child(visual.light)
	else:
		var info: Dictionary = meta()[String(ally.data.id)]
		var frame: Array = info["frame"]
		var feet: Array = info["feet"]
		visual.size = Vector2(frame[0], frame[1])
		visual.height = float(info.get("height", feet[1]))
		for anim: String in (info["anims"] as Dictionary).keys():
			var spec: Dictionary = info["anims"][anim]
			visual.strips[StringName(anim)] = {"tex": _strip(ally.data.id, anim), "frames": int(spec["frames"]), "fps": float(spec["fps"])}
		visual.body.offset = -Vector2(feet[0], feet[1])
		_show(visual, &"walk", 0)
		silhouette = (visual.strips[&"walk"]["tex"] as CanvasTexture).diffuse_texture
	visual.caster = _art._add_caster(visual.root, silhouette, visual.body.offset, 0.7, visual.body)
	visual.caster.blob.scale = Vector2(1.0, 0.45) * minf(visual.size.x, 30.0) / 32.0
	# A unit's sun shadow is one frame of its strip: leave it to the blob.
	visual.caster.sun.visible = visual.champion
	return visual


func _champion_color(ally: SimAlly) -> Color:
	return BoardArt.HERO_LIGHT if ally.data.element.is_empty() else _art.sim.config.element_color(ally.data.element)


func _pos(ally: SimAlly, lateral: float) -> Vector2:
	# At the gate the whole army reaches the same spot on the road: there the ranks open wider and
	# stand a few deep, so the crowd at the wall still reads as soldiers.
	var crowd := clampf(1.0 - ally.progress / GATE_CROWD, 0.0, 1.0)
	var at := ally.position + _across(ally) * lateral * (1.0 + 1.3 * crowd)
	if crowd > 0.0 and not ally.is_champion():
		var back := _art.sim.lane_curves[ally.lane].sample_baked(ally.progress + 40.0) - ally.position
		at += back.normalized() * fposmod(float(ally.id) * 0.381966, 1.0) * 46.0 * crowd if back.length_squared() > 0.01 else Vector2.ZERO
	return _art._art_pos(at) + Vector2(0, BoardArt.ENEMY_DROP)


func _show(visual: Visual, anim: StringName, frame: int) -> void:
	var strip: Dictionary = visual.strips.get(anim, visual.strips[&"walk"])
	visual.body.texture = strip["tex"]
	visual.body.hframes = strip["frames"]
	visual.body.frame = clampi(frame, 0, strip["frames"] - 1)


func _strip_time(visual: Visual, anim: StringName) -> float:
	var spec: Dictionary = visual.strips.get(anim, {})
	if spec.is_empty():
		return 0.0
	return float(spec["frames"]) / float(spec["fps"])


func _start_cry(visual: Visual, seconds: float) -> void:
	var length := seconds if seconds > 0.0 else CRY_TIME
	if not visual.champion:
		# The strip lifts the weapon and shakes it twice: play it whole, as often as fits.
		var once := _strip_time(visual, &"cry")
		if once > 0.0:
			length = maxf(once, roundf(length / once) * once)
	visual.cry_left = length
	visual.cry_length = length
	visual.anim = &"cry"
	visual.anim_time = 0.0


func _update(visual: Visual, delta: float) -> void:
	var ally := visual.ally
	var pos := _pos(ally, visual.lateral)
	var step := pos - visual.root.position
	var moved := step.length() > 0.01
	if moved and absf(step.x) > 0.01:
		# Units march up the road toward the citadel; they face the way they go.
		visual.body.flip_h = step.x < 0.0
	elif ally.target != null:
		visual.body.flip_h = ally.target.position.x < ally.position.x
	visual.root.position = pos
	visual.anim_time += delta
	visual.hurt_rest = maxf(0.0, visual.hurt_rest - delta)
	if moved:
		visual.walk_time += delta
	else:
		visual.idle_time += delta
	if visual.cry_left > 0.0:
		visual.cry_left -= delta
		if visual.cry_left <= 0.0 and visual.anim == &"cry":
			visual.anim = &"walk"
	# A blow starts the attack; it plays once, then the unit walks or stands again. A war cry is not cut short.
	if ally.cooldown > visual.last_cooldown + 0.05 and ally.target != null and visual.cry_left <= 0.0:
		visual.anim = &"attack"
		visual.anim_time = 0.0
		visual.slashed = false
	visual.last_cooldown = ally.cooldown
	var lost := visual.last_health - ally.health
	if lost > 0.01:
		visual.flash = 1.0
		if lost >= ally.max_health * HURT_SHARE and visual.hurt_rest <= 0.0 and visual.anim != &"cry":
			visual.hurt_rest = HURT_REST
			visual.stagger = 1.0
			if visual.anim != &"attack" or visual.champion:
				visual.anim = &"hurt"
				visual.anim_time = 0.0
	visual.last_health = ally.health
	visual.flash = maxf(0.0, visual.flash - delta * 8.0)
	if visual.champion:
		_update_champion(visual, delta, moved)
	else:
		_update_soldier(visual, moved)
	var color := Color.WHITE
	if ally.aura_bonus > 0.0:
		color = color.lerp(Color(1.0, 0.85, 0.5), 0.12 + 0.06 * sin(_art._elapsed * 4.0))
	visual.body.modulate = color.lerp(Color(1.9, 1.5, 1.5), visual.flash * 0.7)


func _update_soldier(visual: Visual, moved: bool) -> void:
	var anim := visual.anim
	if anim in [&"attack", &"hurt", &"cry"]:
		var spec: Dictionary = visual.strips.get(anim, {})
		var at := int(visual.anim_time * float(spec.get("fps", 14.0)))
		if anim == &"cry" and not spec.is_empty():
			at = at % int(spec["frames"])
		if spec.is_empty() or (anim != &"cry" and at >= int(spec["frames"])):
			visual.anim = &"walk"
		else:
			_show(visual, anim, at)
			return
	if moved or not visual.strips.has(&"idle"):
		var walk: Dictionary = visual.strips[&"walk"]
		var f := int(visual.walk_time * float(walk["fps"])) % int(walk["frames"]) if moved else 0
		_show(visual, &"walk", f)
	else:
		var idle: Dictionary = visual.strips[&"idle"]
		_show(visual, &"idle", int(visual.idle_time * float(idle["fps"])) % int(idle["frames"]))


## A champion is one picture: it marches with a bob and a sway, breathes at rest, winds up and lunges
## with a slash of light, staggers when struck and leaps with a flare for its war cry.
func _update_champion(visual: Visual, delta: float, moved: bool) -> void:
	var facing := -1.0 if visual.body.flip_h else 1.0
	var offset := Vector2.ZERO
	var turn := 0.0
	var stretch := Vector2.ONE
	if moved:
		var t := visual.walk_time * 7.0
		offset.y = -roundf(absf(sin(t)) * 2.0)
		turn = sin(t) * 0.05
	else:
		var breath := sin(visual.idle_time * 2.4)
		stretch = Vector2(1.0 - 0.015 * breath, 1.0 + 0.025 * breath)
	match visual.anim:
		&"attack":
			var t := visual.anim_time
			if t < 0.14:          # wind up: lean back
				var k := t / 0.14
				turn = -0.16 * k
				offset.x = -2.0 * k
			elif t < 0.26:        # strike: through and forward
				var k := (t - 0.14) / 0.12
				turn = lerpf(-0.16, 0.2, k)
				offset.x = lerpf(-2.0, 6.0, k)
				if not visual.slashed and k > 0.3:
					visual.slashed = true
					_slash(visual, facing)
			elif t < CHAMPION_SWING:
				var k := (t - 0.26) / (CHAMPION_SWING - 0.26)
				turn = lerpf(0.2, 0.0, k)
				offset.x = lerpf(6.0, 0.0, k)
			else:
				visual.anim = &"walk"
		&"hurt":
			if visual.anim_time > 0.3:
				visual.anim = &"walk"
		&"cry":
			var k := clampf(1.0 - visual.cry_left / maxf(0.01, visual.cry_length), 0.0, 1.0)
			var leap := sin(minf(1.0, k * 2.2) * PI)
			offset.y -= leap * 9.0
			stretch = Vector2.ONE * (1.0 + 0.1 * leap)
			turn = -0.08 * leap
	if visual.stagger > 0.0:
		turn -= 0.18 * visual.stagger
		offset.x -= 4.0 * visual.stagger
		visual.stagger = maxf(0.0, visual.stagger - delta * 3.5)
	visual.body.position = Vector2(offset.x * facing, offset.y)
	visual.body.rotation = turn * facing
	visual.body.scale = stretch
	if visual.light != null:
		var glow := visual.light_energy
		if visual.cry_left > 0.0:
			glow += 1.4 * sin(clampf(visual.cry_left / maxf(0.01, visual.cry_length), 0.0, 1.0) * PI)
		visual.light.energy = glow


## A crescent of light swept in front of a champion as its blow lands.
func _slash(visual: Visual, facing: float) -> void:
	var slash := Slash.new()
	slash.color = _champion_color(visual.ally).lerp(Color.WHITE, 0.45)
	slash.facing = facing
	slash.node = Node2D.new()
	slash.node.material = _art._additive
	slash.node.position = visual.root.position + Vector2(facing * visual.size.x * 0.45, -visual.size.y * 0.45)
	slash.node.draw.connect(_draw_slash.bind(slash))
	_art._air.add_child(slash.node)
	_slashes.append(slash)


func _draw_slash(slash: Slash) -> void:
	var k := clampf(slash.time / SLASH_TIME, 0.0, 1.0)
	var fade := 1.0 - k
	var radius := 14.0 + 6.0 * k
	var start := -PI * 0.65
	var sweep := PI * 1.1 * minf(1.0, k * 2.5 + 0.3)
	var outer := PackedVector2Array()
	var inner := PackedVector2Array()
	for i in 13:
		var a := start + sweep * float(i) / 12.0
		var thick := sin(PI * float(i) / 12.0) * 5.0 * fade + 0.5
		outer.append(Vector2(cos(a) * slash.facing, sin(a)) * radius)
		inner.append(Vector2(cos(a) * slash.facing, sin(a)) * (radius - thick))
	inner.reverse()
	var shape := outer + inner
	slash.node.draw_colored_polygon(shape, Color(slash.color, 0.85 * fade))
	slash.node.draw_polyline(outer, Color(1, 1, 1, fade), 1.0)


func _advance_slashes(delta: float) -> void:
	var left: Array[Slash] = []
	for slash in _slashes:
		slash.time += delta
		if slash.time >= SLASH_TIME:
			slash.node.queue_free()
			continue
		slash.node.queue_redraw()
		left.append(slash)
	_slashes = left


func _leave_corpse(visual: Visual) -> void:
	if not visual.champion and not visual.strips.has(&"death"):
		return
	if _corpses.size() >= MAX_CORPSES:
		_corpses.pop_front().sprite.queue_free()
	var corpse := Corpse.new()
	corpse.sprite = Sprite2D.new()
	corpse.sprite.centered = false
	corpse.sprite.offset = visual.body.offset
	corpse.sprite.flip_h = visual.body.flip_h
	corpse.sprite.position = visual.root.position
	if visual.champion:
		# The hero's picture topples backwards where it stood.
		corpse.sprite.texture = visual.body.texture
		corpse.frames = 1
		corpse.fps = 2.0
		corpse.topple = 1.0 if visual.body.flip_h else -1.0
	else:
		var spec: Dictionary = visual.strips[&"death"]
		corpse.frames = spec["frames"]
		corpse.fps = spec["fps"]
		corpse.sprite.texture = spec["tex"]
		corpse.sprite.hframes = corpse.frames
	_art._actors.add_child(corpse.sprite)
	_corpses.append(corpse)


func _advance_corpses(delta: float) -> void:
	var left: Array[Corpse] = []
	for corpse in _corpses:
		corpse.time += delta
		var played := float(corpse.frames) / corpse.fps
		if corpse.time >= played + CORPSE_LINGER:
			corpse.sprite.queue_free()
			continue
		if corpse.topple != 0.0:
			var k := minf(1.0, corpse.time / played)
			corpse.sprite.rotation = corpse.topple * PI * 0.5 * k * k
			corpse.sprite.modulate = Color(1, 1, 1).lerp(Color(0.55, 0.5, 0.55), k)
		else:
			corpse.sprite.frame = mini(int(corpse.time * corpse.fps), corpse.frames - 1)
		if corpse.time > played:
			corpse.sprite.modulate.a = 1.0 - (corpse.time - played) / CORPSE_LINGER
		left.append(corpse)
	_corpses = left


func visual_count() -> int:
	return _visuals.size()
