class_name TowerSpriteSet
extends RefCounted
## Pre-rendered tower art made by the Blender pipeline in art/blender (see docs/art-pipeline.md).
##
## Each tower with art has `res://assets/sprites/towers/<id>/<id>.png`, a sheet with one row per
## aim direction and one column per animation frame, and `<id>.json` describing it. Towers
## without art keep the placeholder shapes.

const ROOT := "res://assets/sprites/towers"

## Loaded sets by tower id. A missing set is cached as null so the disk is checked only once.
static var _cache: Dictionary = {}

var id: StringName
## The sheet wrapped with the filter it needs: nearest for pixel art, smooth for HD renders.
var texture: CanvasTexture
var sheet: Texture2D
## True for pixel-art sheets, which must be drawn with sharp, unfiltered pixels.
var pixel_art := false
## Size of one frame in the sheet, in pixels.
var frame_size := Vector2.ZERO
var directions := 1
var frames := 1
var fps := 10.0
## Pixel in a frame where the centre of the tower's cell is.
var anchor := Vector2.ZERO
## Scale the sheet is drawn at: 2 for pixel art (each art pixel is 2x2 screen pixels at 1080p),
## 0.5 for HD sheets, which are rendered at 2x so they stay sharp on 4K screens.
var display_scale := 0.5


## The art for a tower, or null if it has none yet.
static func for_tower(tower_id: StringName) -> TowerSpriteSet:
	if not _cache.has(tower_id):
		_cache[tower_id] = load_from(ROOT.path_join(tower_id).path_join("%s.json" % tower_id))
	return _cache[tower_id]


## Reads a sprite set from its JSON file. Returns null if the file is missing; reports broken files.
static func load_from(json_path: String) -> TowerSpriteSet:
	if not FileAccess.file_exists(json_path):
		return null
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(json_path))
	if not parsed is Dictionary:
		push_error("Tower art %s is not a JSON object" % json_path)
		return null
	var data: Dictionary = parsed
	var sheet_path := json_path.get_base_dir().path_join(str(data.get("sheet", "")))
	var sheet := load(sheet_path) as Texture2D if ResourceLoader.exists(sheet_path) else null
	if sheet == null:
		push_error("Tower art %s: sheet %s is missing" % [json_path, sheet_path])
		return null
	var result := TowerSpriteSet.new()
	result.id = StringName(str(data.get("id", "")))
	result.sheet = sheet
	result.pixel_art = str(data.get("filter", "linear")) == "nearest"
	result.texture = CanvasTexture.new()
	result.texture.diffuse_texture = sheet
	var normal_name := str(data.get("normal_sheet", ""))
	if not normal_name.is_empty():
		var normal_path := json_path.get_base_dir().path_join(normal_name)
		if ResourceLoader.exists(normal_path):
			# Lets Light2D nodes (torches, glowing towers, a day-night cycle) shade the sprite.
			result.texture.normal_texture = load(normal_path)
		else:
			push_error("Tower art %s: normal map %s is missing" % [json_path, normal_path])
	result.texture.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST if result.pixel_art \
		else CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	result.frame_size = _vector(data.get("frame_size"), Vector2(sheet.get_size()))
	result.directions = maxi(1, int(data.get("directions", 1)))
	result.frames = maxi(1, int(data.get("frames", 1)))
	result.fps = maxf(0.0, float(data.get("fps", 10.0)))
	result.anchor = _vector(data.get("anchor"), result.frame_size * 0.5)
	result.display_scale = float(data.get("display_scale", 0.5))
	var expected := Vector2(result.frame_size.x * result.frames, result.frame_size.y * result.directions)
	if Vector2(sheet.get_size()) != expected:
		push_error("Tower art %s: sheet is %s but the JSON describes %s" % [json_path, sheet.get_size(), expected])
		return null
	return result


static func _vector(value: Variant, fallback: Vector2) -> Vector2:
	if value is Array and value.size() == 2:
		return Vector2(float(value[0]), float(value[1]))
	return fallback


## Row of the sheet closest to a screen angle (radians, 0 = right, clockwise like Godot).
func direction_index(angle: float) -> int:
	return posmod(roundi(angle / TAU * directions), directions)


## Animation column at a time in seconds. `offset` desynchronises towers built side by side.
func frame_index(time: float, offset: int = 0) -> int:
	return posmod(int(floor(time * fps)) + offset, frames)


func region(direction: int, frame: int) -> Rect2:
	return Rect2(Vector2(frame * frame_size.x, direction * frame_size.y), frame_size)


## Where the frame lands on the board when the tower stands on `center`.
func draw_rect_at(center: Vector2) -> Rect2:
	return Rect2(center - anchor * display_scale, frame_size * display_scale)


func draw(canvas: CanvasItem, center: Vector2, facing: float, time: float, offset: int = 0,
		modulate: Color = Color.WHITE) -> void:
	canvas.draw_texture_rect_region(texture, draw_rect_at(center),
		region(direction_index(facing), frame_index(time, offset)), modulate)


## A square close-up of the tower for menus, cut from one frame of the sheet. Shown at
## `display_scale` it is 56 pixels wide; controls showing pixel art should use nearest filtering.
func portrait(direction: int = 2, frame: int = 0) -> AtlasTexture:
	var side := roundf(frame_size.x * 0.44)
	# The tower stands on the anchor and rises above it, so centre the crop a little higher.
	var centre := (anchor - Vector2(0, frame_size.y * 0.24)).round()
	var crop := Rect2(centre - Vector2(side, side) * 0.5, Vector2(side, side))
	crop = crop.intersection(Rect2(Vector2.ZERO, frame_size))
	var atlas := AtlasTexture.new()
	atlas.atlas = sheet
	atlas.region = Rect2(region(direction, frame).position + crop.position, crop.size)
	return atlas
