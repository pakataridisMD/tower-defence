class_name AllyArt
extends RefCounted
## Draws the army the player musters in the counter-attack: each unit walks, strikes and dies from
## the strips made by tools/art/pix2d/allies.py (assets/art/game/allies/), and a champion is the
## hero's own board sprite marching with a bob and a light. Units with no art are drawn by BoardView
## as plain markers.
##
## BoardArt owns one and calls sync() every frame.

const DIR := "res://assets/art/game/allies/"
const HERO_DIR := "res://assets/art/heroes/board/"
## Seconds a fallen unit lies before it fades.
const CORPSE_LINGER := 1.6
const MAX_CORPSES := 40

static var _meta: Dictionary = {}

var _art: BoardArt
var _visuals: Dictionary[int, Visual] = {}
var _corpses: Array[Corpse] = []
var _textures: Dictionary[String, CanvasTexture] = {}


class Visual:
	var ally: SimAlly
	var root: Node2D
	var body: Sprite2D
	var light: PointLight2D
	var caster: BoardArt.Caster
	## Strips by animation (&"walk", &"attack", &"death") and their frame counts and speeds.
	var strips: Dictionary = {}
	var anim := &"walk"
	var anim_time := 0.0
	var walk_time := 0.0
	var last_health := 0.0
	var flash := 0.0
	var last_cooldown := 0.0
	var champion := false
	var size := Vector2.ZERO


class Corpse:
	var sprite: Sprite2D
	var frames := 1
	var fps := 10.0
	var time := 0.0


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
		_update(visual, delta)
	for id in _visuals.keys():
		if not seen.has(id):
			var visual: Visual = _visuals[id]
			_leave_corpse(visual)
			_art._remove_caster(visual.caster)
			visual.root.queue_free()
			_visuals.erase(id)
	_advance_corpses(delta)


func _make(ally: SimAlly) -> Visual:
	var visual := Visual.new()
	visual.ally = ally
	visual.last_health = ally.health
	visual.last_cooldown = ally.cooldown
	visual.walk_time = randf()
	visual.root = Node2D.new()
	visual.root.position = _pos(ally)
	_art._actors.add_child(visual.root)
	visual.body = Sprite2D.new()
	visual.body.centered = false
	visual.root.add_child(visual.body)
	var silhouette: Texture2D
	if ally.is_champion():
		visual.champion = true
		var texture: Texture2D = load(HERO_DIR + "%s.png" % ally.data.hero)
		visual.size = texture.get_size()
		visual.body.texture = texture
		visual.body.offset = Vector2(-visual.size.x * 0.5, -visual.size.y + 2.0)
		silhouette = texture
		var color := BoardArt.HERO_LIGHT if ally.data.element.is_empty() else _art.sim.config.element_color(ally.data.element)
		visual.light = _art._point_light(color.lerp(Color.WHITE, 0.3), 0.9, 80.0, 40.0)
		visual.light.position = Vector2(0, -visual.size.y * 0.6)
		visual.root.add_child(visual.light)
	else:
		var info: Dictionary = meta()[String(ally.data.id)]
		var frame: Array = info["frame"]
		var feet: Array = info["feet"]
		visual.size = Vector2(frame[0], frame[1])
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


func _pos(ally: SimAlly) -> Vector2:
	return _art._art_pos(ally.position) + Vector2(0, BoardArt.ENEMY_DROP)


func _show(visual: Visual, anim: StringName, frame: int) -> void:
	var strip: Dictionary = visual.strips.get(anim, visual.strips[&"walk"])
	visual.body.texture = strip["tex"]
	visual.body.hframes = strip["frames"]
	visual.body.frame = clampi(frame, 0, strip["frames"] - 1)


func _update(visual: Visual, delta: float) -> void:
	var ally := visual.ally
	var pos := _pos(ally)
	var moved := pos.distance_to(visual.root.position) > 0.01
	if moved:
		# Units march up the road toward the citadel; they face the way they go.
		visual.body.flip_h = pos.x < visual.root.position.x - 0.01
	elif ally.target != null:
		visual.body.flip_h = ally.target.position.x < ally.position.x
	visual.root.position = pos
	# A blow starts the attack strip; it plays once, then the unit walks or stands again.
	if ally.cooldown > visual.last_cooldown + 0.05 and ally.target != null:
		visual.anim = &"attack"
		visual.anim_time = 0.0
	visual.last_cooldown = ally.cooldown
	visual.anim_time += delta
	if moved:
		visual.walk_time += delta
	if visual.champion:
		var bob := absf(sin(visual.walk_time * 7.0)) * 2.0 if moved else 0.0
		var lunge := 0.0
		if visual.anim == &"attack":
			lunge = sin(minf(1.0, visual.anim_time / 0.35) * PI) * 4.0
			if visual.anim_time > 0.35:
				visual.anim = &"walk"
		visual.body.position = Vector2(lunge * (-1.0 if visual.body.flip_h else 1.0), -roundf(bob))
	else:
		var anim := visual.anim
		if anim == &"attack":
			var spec: Dictionary = visual.strips.get(&"attack", {})
			var step := int(visual.anim_time * float(spec.get("fps", 14.0)))
			if spec.is_empty() or step >= int(spec["frames"]):
				visual.anim = &"walk"
			else:
				_show(visual, &"attack", step)
		if visual.anim == &"walk":
			var walk: Dictionary = visual.strips[&"walk"]
			var f := int(visual.walk_time * float(walk["fps"])) % int(walk["frames"]) if moved or ally.fighting == false else 0
			_show(visual, &"walk", f)
	if ally.health < visual.last_health - 0.01:
		visual.flash = 1.0
	visual.last_health = ally.health
	visual.flash = maxf(0.0, visual.flash - delta * 8.0)
	var color := Color.WHITE
	if ally.aura_bonus > 0.0:
		color = color.lerp(Color(1.0, 0.85, 0.5), 0.12 + 0.06 * sin(_art._elapsed * 4.0))
	visual.body.modulate = color.lerp(Color(1.9, 1.5, 1.5), visual.flash * 0.7)


func _leave_corpse(visual: Visual) -> void:
	if visual.champion or not visual.strips.has(&"death"):
		return
	if _corpses.size() >= MAX_CORPSES:
		_corpses.pop_front().sprite.queue_free()
	var spec: Dictionary = visual.strips[&"death"]
	var corpse := Corpse.new()
	corpse.frames = spec["frames"]
	corpse.fps = spec["fps"]
	corpse.sprite = Sprite2D.new()
	corpse.sprite.texture = spec["tex"]
	corpse.sprite.hframes = corpse.frames
	corpse.sprite.centered = false
	corpse.sprite.offset = visual.body.offset
	corpse.sprite.flip_h = visual.body.flip_h
	corpse.sprite.position = visual.root.position
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
		corpse.sprite.frame = mini(int(corpse.time * corpse.fps), corpse.frames - 1)
		if corpse.time > played:
			corpse.sprite.modulate.a = 1.0 - (corpse.time - played) / CORPSE_LINGER
		left.append(corpse)
	_corpses = left


func visual_count() -> int:
	return _visuals.size()
