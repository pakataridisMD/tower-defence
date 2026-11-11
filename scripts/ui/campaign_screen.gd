class_name CampaignScreen
extends Control
## The campaign map: the painted world of Orrhen. Each kingdom is a continent around the Heartland of
## Orrun. A kingdom's four stages run from its far coast to its capital, the Convergence holds the
## Heartland and Solenne, and the assault on Nhal Vorath waits in the Outer Hollow past the edge of the
## world. When a stage is won its city falls (its people get away), and smoke rises over it.
##
## The map and where everything sits on it come from tools/art/worldmap/gen_world_map.py. The header
## and the side panel use the menu's look (UiStyle.menu_theme).
## Wheel or +/- zooms, dragging (or a trackpad) moves the map, Left/Right step through the stages and
## Home shows the whole world. Click a stage to read about it, then Begin. Esc goes back to the menu.

const MENU_SCENE := "res://scenes/main.tscn"
const GAME_SCENE := "res://scenes/game/game.tscn"
const MAP_DIR := "res://assets/art/worldmap/"
const GROUND_ART := "res://assets/art/game/ground/%s.png"
const PANEL_WIDTH := 600.0
const PANEL_MARGIN := 40.0
## How far the map can zoom, in screen pixels per map pixel. Zero stands for "the whole world".
const ZOOMS: Array[float] = [0.0, 0.5, 1.0, 2.0]
## The zoom the map opens at, centred on the stage.
const STAGE_ZOOM := 1.0
const GLIDE_TIME := 0.35
const INTRO_TIME := 1.8
const DRAG_THRESHOLD := 6.0
## How far down the screen the title and its line reach.
const HEADER_HEIGHT := 180.0
const SPACE := Color("07060d")
const SMOKE := Color("2a2530")
## The city that does not fall.
const SAVED_CITY := &"converge_3"

## The intro glide, from the whole world down to the next stage, plays once per session.
static var intro_played := false
## The painted map is large, so it is loaded once and kept for the next visit.
static var _map_cache: Texture2D

## The stage shown in the side panel.
var selected: StringName = &""
## Screen pixels per map pixel.
var zoom := STAGE_ZOOM
## The map pixel in the middle of the part of the screen the panel leaves free.
var center := Vector2.ZERO

var _map: Texture2D
var _map_size := Vector2(6000, 3400)
var _spots: Dictionary = {}
var _links: Dictionary = {}
var _labels: Array[Dictionary] = []
var _medals: Dictionary[StringName, Texture2D] = {}
var _order: Array[StringName] = []
var _elements: Dictionary[StringName, ElementData] = {}
var _hovered: StringName = &""
var _time := 0.0
var _city_font: Font
var _small_font: Font

var _glide := {}
var _pressed := false
var _press_at := Vector2.ZERO
var _dragging := false
var _magnify := 1.0

var _map_layer: Control
var _marks: Control
var _header: Control
var _stars_label: Label
var _panel: PanelContainer
var _caption: Label
var _stage_title: Label
var _city: Label
var _story: Label
var _preview: TextureRect
var _summary: RichTextLabel
var _details: RichTextLabel
var _begin: MenuItemButton
var _party_title: Label
var _party_grid: GridContainer
var _party_buttons: Dictionary[StringName, KeyButton] = {}
var _zoom_bar: HBoxContainer


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UiStyle.menu_theme()
	clip_contents = true
	_city_font = _font_or_fallback("button")
	_small_font = _font_or_fallback("small")
	for element: ElementData in DataRegistry.elements.values():
		_elements[element.id] = element
	_load_layout()
	_map_layer = _layer()
	_map_layer.draw.connect(_draw_map)
	_marks = _layer()
	_marks.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_marks.clip_contents = true
	_marks.draw.connect(_draw_marks)
	_build_header()
	_build_panel()
	_build_zoom_bar()
	_place_panel()
	var start := Progress.active_stage
	if start.is_empty() or not DataRegistry.stages.has(start):
		start = _first_open_stage()
	select(start, false)
	if not intro_played:
		intro_played = true
		zoom = _fit_zoom()
		center = _map_size * 0.5
		_glide_to(_spot(start), STAGE_ZOOM, INTRO_TIME, 0.35)
	else:
		zoom = STAGE_ZOOM
		center = _spot(start)
	_clamp_view()


static func _font_or_fallback(kind: String) -> Font:
	var result := UiStyle.font(kind)
	return result if result != null else ThemeDB.fallback_font


func _layer() -> Control:
	var layer := Control.new()
	layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	layer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(layer)
	return layer


func _notification(what: int) -> void:
	if what == NOTIFICATION_RESIZED and _panel != null:
		_place_panel()
		_clamp_view()


func _process(delta: float) -> void:
	_time += delta
	if not _glide.is_empty():
		_step_glide(delta)
	_map_layer.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST if zoom >= 0.99 and _glide.is_empty() \
			else CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
	_map_layer.queue_redraw()
	_marks.queue_redraw()


# --- The map and where things are on it ---------------------------------------------

func _load_layout() -> void:
	if _map_cache == null:
		_map_cache = load(MAP_DIR + "world_map.png") as Texture2D
	_map = _map_cache
	var text := FileAccess.get_file_as_string(MAP_DIR + "world_map.json")
	var data: Variant = JSON.parse_string(text)
	if not data is Dictionary:
		push_error("Campaign map: cannot read %sworld_map.json" % MAP_DIR)
		return
	var size_list: Array = data.get("size", [6000, 3400])
	_map_size = Vector2(size_list[0], size_list[1])
	_spots = data.get("stages", {})
	_links = data.get("links", {})
	var labels: Dictionary = data.get("labels", {})
	for land: String in labels:
		var entry: Dictionary = labels[land]
		var texture := load(MAP_DIR + str(entry["file"])) as Texture2D
		if texture != null:
			_labels.append({"land": land, "texture": texture, "at": _vec(entry["at"])})
	for campaign in Progress.meta.campaigns_in_order():
		for stage in campaign.stages:
			_order.append(stage.id)
			var spot: Dictionary = _spots.get(String(stage.id), {})
			if spot.is_empty():
				push_error("Campaign map: stage %s has no spot in world_map.json" % stage.id)
				continue
			var number := int(spot.get("number", 0))
			var file := "medal_assault.png" if stage.id == &"assault_1" else "medal_%02d.png" % number
			_medals[stage.id] = load(MAP_DIR + file) as Texture2D


static func _vec(pair: Variant) -> Vector2:
	var list: Array = pair
	return Vector2(float(list[0]), float(list[1]))


## A stage's medallion, in map pixels.
func _spot(stage_id: StringName) -> Vector2:
	var spot: Dictionary = _spots.get(String(stage_id), {})
	return _vec(spot["medal"]) if spot.has("medal") else _map_size * 0.5


## The part of the screen the side panel leaves for the map.
func view_rect() -> Rect2:
	var right := size.x - PANEL_WIDTH - PANEL_MARGIN - 16.0
	return Rect2(Vector2.ZERO, Vector2(maxf(right, size.x * 0.4), size.y))


func map_to_screen(point: Vector2) -> Vector2:
	return (point - center) * zoom + view_rect().get_center()


func screen_to_map(point: Vector2) -> Vector2:
	return (point - view_rect().get_center()) / zoom + center


func _fit_zoom() -> float:
	var view := view_rect().size
	return minf(view.x / _map_size.x, view.y / _map_size.y) * 0.96


func _zoom_steps() -> Array[float]:
	var steps: Array[float] = []
	var fit := _fit_zoom()
	for step in ZOOMS:
		if step == 0.0:
			steps.append(fit)
		elif step > fit * 1.05:
			steps.append(step)
	return steps


## Keeps the map over the free part of the screen, or in its middle when it is smaller than that.
func _clamp_view() -> void:
	zoom = clampf(zoom, _fit_zoom(), ZOOMS[-1])
	var half := view_rect().size * 0.5 / zoom
	for axis in 2:
		if half[axis] * 2.0 >= _map_size[axis]:
			center[axis] = _map_size[axis] * 0.5
		else:
			center[axis] = clampf(center[axis], half[axis], _map_size[axis] - half[axis])


## Moves the view to a map point at a zoom over a short time. With an anchor, that screen point
## keeps showing the same map point while the zoom changes (zooming toward the mouse).
func _glide_to(target: Vector2, target_zoom: float, duration := GLIDE_TIME, delay := 0.0,
		anchor := Vector2.INF) -> void:
	_glide = {"from": center, "to": target, "from_zoom": zoom, "to_zoom": target_zoom, "t": -delay,
		"duration": duration, "anchor": anchor, "anchor_map": screen_to_map(anchor) if anchor != Vector2.INF else Vector2.ZERO}


func _step_glide(delta: float) -> void:
	_glide["t"] = float(_glide["t"]) + delta
	var t := clampf(float(_glide["t"]) / float(_glide["duration"]), 0.0, 1.0)
	var eased := t * t * (3.0 - 2.0 * t)
	zoom = exp(lerpf(log(float(_glide["from_zoom"])), log(float(_glide["to_zoom"])), eased))
	var anchor: Vector2 = _glide["anchor"]
	if anchor != Vector2.INF:
		center = Vector2(_glide["anchor_map"]) - (anchor - view_rect().get_center()) / zoom
	else:
		center = Vector2(_glide["from"]).lerp(_glide["to"], eased)
	_clamp_view()
	if t >= 1.0:
		_glide = {}


## One zoom step in (+1) or out (-1), toward a screen point.
func zoom_step(direction: int, anchor := Vector2.INF) -> void:
	var steps := _zoom_steps()
	var now := float(_glide["to_zoom"]) if not _glide.is_empty() else zoom
	var index := 0
	for i in steps.size():
		if absf(steps[i] - now) < absf(steps[index] - now):
			index = i
	var target := steps[clampi(index + direction, 0, steps.size() - 1)]
	if is_equal_approx(target, now):
		return
	if anchor == Vector2.INF or target <= _fit_zoom() * 1.01:
		_glide_to(_map_size * 0.5 if target <= _fit_zoom() * 1.01 else center, target)
	else:
		_glide_to(center, target, GLIDE_TIME, 0.0, anchor)


func show_whole_world() -> void:
	_glide_to(_map_size * 0.5, _fit_zoom(), GLIDE_TIME * 1.5)


## Brings a stage into view: closer if the whole world is showing, recentred if it is near an edge.
func focus(stage_id: StringName) -> void:
	var target := _spot(stage_id)
	var target_zoom := maxf(zoom, ZOOMS[1])
	var view := Rect2(Vector2(0, HEADER_HEIGHT), view_rect().size - Vector2(0, HEADER_HEIGHT)).grow(-120.0)
	var at := map_to_screen(target)
	if target_zoom > zoom * 1.01 or not view.has_point(at):
		_glide_to(target, target_zoom)


func _first_open_stage() -> StringName:
	for campaign in Progress.meta.campaigns_in_order():
		var stage := Progress.meta.next_stage(campaign)
		if stage != null:
			return stage.id
	var campaigns := Progress.meta.campaigns_in_order()
	return campaigns[0].stages[0].id if not campaigns.is_empty() else &""


# --- Header and side panel -------------------------------------------------------

## Back, the page title and the star count, like the menu's pages, over a dark band at the top.
func _build_header() -> void:
	_header = Control.new()
	_header.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_header)
	var back := MenuItemButton.new("Back", "Esc")
	back.position = Vector2(48, 36)
	back.size = Vector2(184, 56)
	back.pressed.connect(back_to_menu)
	_header.add_child(back)
	var title := UiStyle.menu_title("Campaign", 96)
	title.position = Vector2(264, 4)
	_header.add_child(title)
	var sub := UiStyle.menu_label("Free the six lands, and every road leads to Solenne.", "body", 32, UiStyle.MENU_DIM)
	sub.position = Vector2(272, 116)
	_header.add_child(sub)
	_stars_label = UiStyle.menu_label("", "small", 16, UiStyle.MENU_GOLD)
	_stars_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_header.add_child(_stars_label)
	var line := MenuPage.Divider.new()
	line.name = "Line"
	_header.add_child(line)


func _build_panel() -> void:
	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", UiStyle.menu_panel_box(26, 22))
	add_child(_panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 8)
	_panel.add_child(column)
	_caption = UiStyle.menu_label("", "small", 16, UiStyle.MENU_GOLD)
	column.add_child(_caption)
	_stage_title = UiStyle.menu_title("", 60)
	_stage_title.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_stage_title.custom_minimum_size = Vector2(540, 0)
	column.add_child(_stage_title)
	_city = UiStyle.menu_label("", "small", 16, UiStyle.MENU_GOLD)
	_city.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_city.custom_minimum_size = Vector2(540, 0)
	column.add_child(_city)
	_story = UiStyle.menu_label("", "body", 32, UiStyle.MENU_DIM)
	_story.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_story.custom_minimum_size = Vector2(540, 0)
	column.add_child(_story)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 16)
	column.add_child(row)
	var frame := PanelContainer.new()
	var dark := StyleBoxFlat.new()
	dark.bg_color = Color("120e18")
	dark.set_content_margin_all(4)
	frame.add_theme_stylebox_override("panel", dark)
	row.add_child(frame)
	_preview = TextureRect.new()
	_preview.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_preview.custom_minimum_size = Vector2(240, 135)
	frame.add_child(_preview)
	_summary = _rich(32)
	_summary.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_summary.fit_content = true
	row.add_child(_summary)
	# Long rule lists scroll, so the party and Begin below always stay on the screen.
	_details = _rich(16)
	_details.scroll_active = true
	_details.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_details.custom_minimum_size = Vector2(540, 100)
	column.add_child(_details)
	_build_party(column)
	_begin = MenuItemButton.new("Begin stage", "Enter")
	_begin.custom_minimum_size = Vector2(0, 72)
	_begin.pressed.connect(begin)
	column.add_child(_begin)


func _rich(font_size: int) -> RichTextLabel:
	var result := RichTextLabel.new()
	result.bbcode_enabled = true
	result.scroll_active = false
	var body := UiStyle.font("body")
	if body != null:
		result.add_theme_font_override("normal_font", body)
		result.add_theme_font_override("bold_font", _small_font)
	result.add_theme_font_size_override("normal_font_size", font_size)
	result.add_theme_font_size_override("bold_font_size", 16)
	result.add_theme_color_override("default_color", UiStyle.MENU_TEXT)
	return result


func _place_panel() -> void:
	_panel.position = Vector2(size.x - PANEL_WIDTH - PANEL_MARGIN, 40)
	_panel.size = Vector2(PANEL_WIDTH, size.y - 80.0)
	var view := view_rect()
	# Stage marks stop at the panel's edge; the painted map carries on behind it.
	_marks.set_anchors_preset(Control.PRESET_TOP_LEFT)
	_marks.position = Vector2.ZERO
	_marks.size = view.size
	_header.size = Vector2(view.size.x, HEADER_HEIGHT)
	_stars_label.position = Vector2(view.size.x - 440, 64)
	_stars_label.size = Vector2(400, 24)
	var line := _header.get_node("Line") as Control
	line.position = Vector2(48, 166)
	line.size = Vector2(view.size.x - 88, 12)
	if _zoom_bar != null:
		_zoom_bar.position = Vector2(48, size.y - 124)


## Zoom buttons for playing with the mouse alone.
func _build_zoom_bar() -> void:
	_zoom_bar = HBoxContainer.new()
	_zoom_bar.add_theme_constant_override("separation", 8)
	add_child(_zoom_bar)
	for entry: Array in [["+", 1], ["-", -1], ["Whole world", 0]]:
		var button := UiStyle.menu_button(entry[0], 40)
		button.custom_minimum_size = Vector2(56 if entry[1] != 0 else 210, 56)
		var direction: int = entry[1]
		button.pressed.connect(func() -> void:
			if direction == 0:
				show_whole_world()
			else:
				zoom_step(direction))
		_zoom_bar.add_child(button)


## The heroes who have joined, to pick the party from. Gold frames mark the ones going.
func _build_party(column: VBoxContainer) -> void:
	_party_title = UiStyle.menu_label("", "small", 16, UiStyle.MENU_GOLD)
	column.add_child(_party_title)
	_party_grid = GridContainer.new()
	_party_grid.columns = 8
	_party_grid.add_theme_constant_override("h_separation", 6)
	_party_grid.add_theme_constant_override("v_separation", 6)
	column.add_child(_party_grid)
	for hero in Progress.meta.heroes_in_order():
		var hero_id := hero.id
		var button := UiStyle.key_button("", 14)
		button.icon = Hud.hero_portrait(hero_id)
		button.expand_icon = true
		button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		button.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		button.custom_minimum_size = Vector2(60, 60)
		button.pressed.connect(func() -> void:
			Progress.toggle_party_hero(hero_id)
			SoundPlayer.sfx(&"ui_toggle")
			_refresh_party())
		_party_grid.add_child(button)
		_party_buttons[hero_id] = button
	_refresh_party()


func _refresh_party() -> void:
	var meta := Progress.meta
	var party := meta.party()
	var joined := meta.joined_heroes()
	_party_title.text = "HEROES  -  TAKE UP TO %d  -  F1-F3 IN BATTLE" % HeroData.MAX_PARTY
	for hero in meta.heroes_in_order():
		var button := _party_buttons[hero.id]
		var has_joined := joined.has(hero)
		button.visible = has_joined
		var slot := party.find(hero)
		button.outline = UiStyle.GOLD if slot >= 0 else Color(0, 0, 0, 0)
		button.key_text = "F%d" % (slot + 1) if slot >= 0 else ""
		button.modulate = Color.WHITE if slot >= 0 else Color(1, 1, 1, 0.6)
		button.tooltip_text = "%s, %s\n%s\n%s" % [hero.display_name, hero.title, hero.blurb,
				"In the party. Click to leave behind." if slot >= 0 else "Click to bring."]


## Shows a stage in the side panel and brings it into view on the map.
func select(stage_id: StringName, move_view := true) -> void:
	var stage: StageData = DataRegistry.stages.get(stage_id)
	if stage == null:
		return
	selected = stage_id
	var meta := Progress.meta
	var campaign := DataRegistry.campaign_of(stage_id)
	var index := campaign.stage_index(stage_id)
	_caption.text = ("%s  -  stage %d of %d" % [campaign.display_name, index + 1, campaign.stages.size()]).to_upper()
	_caption.add_theme_color_override("font_color", _campaign_color(campaign).lerp(UiStyle.MENU_GOLD_LIGHT, 0.35))
	_stage_title.text = stage.display_name
	var city := _city_line(stage)
	_city.text = city[0]
	_city.add_theme_color_override("font_color", city[1])
	_story.text = stage.description
	var map: MapData = DataRegistry.maps.get(stage.map)
	_preview.texture = load(GROUND_ART % stage.map) if map != null and ResourceLoader.exists(GROUND_ART % stage.map) else null
	_summary.text = _summary_text(stage)
	_details.text = _details_text(stage, campaign)
	_details.scroll_to_line(0)
	var unlocked := meta.is_stage_unlocked(stage_id)
	_begin.disabled = not unlocked
	_begin.text = "Begin stage" if meta.stars(stage_id) == 0 else "Play again"
	if not unlocked:
		_begin.text = "Locked"
	if move_view and is_inside_tree():
		focus(stage_id)


## The city the stage defends and what became of it, with the colour to show it in.
func _city_line(stage: StageData) -> Array:
	var won := Progress.meta.stars(stage.id) > 0
	if stage.is_assault():
		return ["NHAL VORATH HAS FALLEN", UiStyle.GOOD] if won else ["BRING DOWN NHAL VORATH", UiStyle.MENU_GOLD]
	var city := Story.shared().city(stage.id)
	var name := str(city.get("name", ""))
	if name.is_empty():
		var spot: Dictionary = _spots.get(String(stage.id), {})
		name = str(spot.get("city", ""))
	if name.is_empty():
		return ["", UiStyle.MENU_GOLD]
	if not won:
		return [("Defend %s" % name).to_upper(), UiStyle.MENU_GOLD]
	if bool(city.get("saved", false)):
		return [("%s is saved" % name).to_upper(), UiStyle.GOOD]
	return [("%s has fallen. Its people got away." % name).to_upper(), UiStyle.MENU_DIM]


## Stars, waves and roads beside the battlefield picture.
func _summary_text(stage: StageData) -> String:
	var meta := Progress.meta
	var stars := meta.stars(stage.id)
	var wave_set := _wave_set(stage)
	var lines: PackedStringArray = []
	var star := TreeArt.ART + "icon_star.png"
	var star_row := ""
	for i in 3:
		star_row += "[img=24x24 color=#%s]%s[/img] " % [
			(UiStyle.MENU_GOLD_LIGHT if i < stars else Color("4a4256")).to_html(false), star]
	lines.append(star_row)
	lines.append("%d waves" % (wave_set.waves.size() if wave_set != null else 0))
	var map: MapData = DataRegistry.maps.get(stage.map)
	if map != null and map.lane_count() > 1:
		lines.append("%d roads" % map.lane_count())
	if stage.is_guardian:
		lines.append("[color=#%s]Warden[/color]" % UiStyle.KEYSTONE.to_html(false))
	return "\n".join(lines)


func _details_text(stage: StageData, campaign: CampaignData) -> String:
	var meta := Progress.meta
	var gold := UiStyle.MENU_GOLD.to_html(false)
	var lines: PackedStringArray = []
	var stars := meta.stars(stage.id)
	if not meta.is_stage_unlocked(stage.id):
		if not meta.is_campaign_unlocked(campaign.id):
			lines.append("[color=#%s]Opens when every element campaign is finished.[/color]" % UiStyle.BAD.to_html(false))
		else:
			lines.append("[color=#%s]Win the stage before it to open this one.[/color]" % UiStyle.BAD.to_html(false))
	lines.append("[color=#%s][b]RULES[/b][/color]" % gold)
	for rule in stage.rule_text:
		lines.append("-  " + rule)
	var enemies := _enemy_names(_wave_set(stage))
	if not enemies.is_empty():
		lines.append("[color=#%s][b]ENEMIES[/b][/color]" % gold)
		lines.append(", ".join(enemies))
	lines.append("[color=#%s][b]REWARD[/b][/color]" % gold)
	lines.append("%d meta points for the first win%s. Stars: win, keep half your lives, lose none." % [
		stage.first_clear_points, "" if stars == 0 else " (claimed)"])
	if not campaign.reward_name.is_empty():
		var done := meta.is_campaign_complete(campaign.id)
		lines.append("%s%s  %s" % [campaign.reward_name,
			" [color=#%s](earned)[/color]" % UiStyle.GOOD.to_html(false) if done else " for finishing the campaign:",
			campaign.reward_description])
	return "\n".join(lines)


func _wave_set(stage: StageData) -> WaveSet:
	if not stage.wave_set.is_empty():
		return DataRegistry.wave_sets.get(stage.wave_set)
	var map: MapData = DataRegistry.maps.get(stage.map)
	return DataRegistry.wave_sets.get(map.wave_set) if map != null else null


## Every enemy the stage's waves send, bosses first, with their traits.
func _enemy_names(wave_set: WaveSet) -> PackedStringArray:
	var seen: Array[EnemyData] = []
	if wave_set == null:
		return PackedStringArray()
	for wave in wave_set.waves:
		for group in wave.groups:
			var data: EnemyData = DataRegistry.enemies.get(group.enemy)
			if data != null and not seen.has(data):
				seen.append(data)
	seen.sort_custom(func(a: EnemyData, b: EnemyData) -> bool: return a.tags.has(&"boss") and not b.tags.has(&"boss"))
	var result: PackedStringArray = []
	for data in seen:
		var words := data.trait_words()
		var name := data.display_name
		if data.tags.has(&"boss"):
			name = "[color=#%s]%s[/color]" % [UiStyle.KEYSTONE.to_html(false), name]
		result.append(name + (" (%s)" % ", ".join(words) if not words.is_empty() else ""))
	return result


func begin() -> void:
	if Progress.play_stage(selected):
		Progress.play_story(get_tree(), Progress.meta.story_before_stage(Story.shared(), selected), GAME_SCENE)


func back_to_menu() -> void:
	get_tree().change_scene_to_file(MENU_SCENE)


## The stage before or after the selected one, in campaign order.
func step_stage(direction: int) -> void:
	if _order.is_empty():
		return
	var index := _order.find(selected)
	select(_order[posmod(index + direction, _order.size())])


# --- Input -----------------------------------------------------------------------

func _gui_input(event: InputEvent) -> void:
	var motion := event as InputEventMouseMotion
	if motion != null:
		var held := motion.button_mask & (MOUSE_BUTTON_MASK_LEFT | MOUSE_BUTTON_MASK_RIGHT | MOUSE_BUTTON_MASK_MIDDLE)
		if _pressed and not _dragging and motion.position.distance_to(_press_at) > DRAG_THRESHOLD:
			_dragging = true
		if held != 0 and (_dragging or motion.button_mask & MOUSE_BUTTON_MASK_LEFT == 0):
			_glide = {}
			center -= motion.relative / zoom
			_clamp_view()
		_hovered = stage_at(motion.position) if not _dragging else &""
		mouse_default_cursor_shape = Control.CURSOR_DRAG if _dragging \
				else (Control.CURSOR_POINTING_HAND if not _hovered.is_empty() else Control.CURSOR_ARROW)
		return
	var button := event as InputEventMouseButton
	if button != null:
		if button.pressed and button.button_index in [MOUSE_BUTTON_WHEEL_UP, MOUSE_BUTTON_WHEEL_DOWN]:
			zoom_step(1 if button.button_index == MOUSE_BUTTON_WHEEL_UP else -1, button.position)
			accept_event()
		elif button.button_index == MOUSE_BUTTON_LEFT:
			if button.pressed:
				_pressed = true
				_dragging = false
				_press_at = button.position
				var hit := stage_at(button.position)
				if not hit.is_empty() and hit == selected and button.double_click:
					begin()
			else:
				if _pressed and not _dragging:
					var hit := stage_at(button.position)
					if not hit.is_empty():
						select(hit)
						SoundPlayer.sfx(&"ui_toggle")
				_pressed = false
				_dragging = false
			accept_event()
		return
	var pan := event as InputEventPanGesture
	if pan != null:
		_glide = {}
		center += pan.delta * 24.0 / zoom
		_clamp_view()
		accept_event()
		return
	var magnify := event as InputEventMagnifyGesture
	if magnify != null:
		_magnify *= magnify.factor
		if _magnify > 1.25 or _magnify < 0.8:
			zoom_step(1 if _magnify > 1.0 else -1, magnify.position)
			_magnify = 1.0
		accept_event()


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	var handled := true
	match key.keycode:
		KEY_ESCAPE:
			back_to_menu()
		KEY_ENTER, KEY_KP_ENTER:
			begin()
		KEY_LEFT, KEY_UP:
			step_stage(-1)
		KEY_RIGHT, KEY_DOWN, KEY_TAB:
			step_stage(-1 if key.shift_pressed else 1)
		KEY_EQUAL, KEY_PLUS, KEY_KP_ADD:
			zoom_step(1)
		KEY_MINUS, KEY_KP_SUBTRACT:
			zoom_step(-1)
		KEY_HOME:
			show_whole_world()
		_:
			handled = false
	if handled:
		get_viewport().set_input_as_handled()


## The stage whose medallion is under a screen point, or empty.
func stage_at(point: Vector2) -> StringName:
	var best: StringName = &""
	var best_distance := INF
	for id: StringName in _medals:
		var distance := point.distance_to(map_to_screen(_spot(id)))
		if distance <= _medal_radius(id) + 6.0 and distance < best_distance:
			best = id
			best_distance = distance
	return best


## Where a stage's medallion is on the screen right now.
func stage_position(stage_id: StringName) -> Vector2:
	return map_to_screen(_spot(stage_id)) if _medals.has(stage_id) else Vector2.ZERO


# --- Drawing ---------------------------------------------------------------------

## The march on the enemy citadel, unlocked by the Convergence.
func _is_assault(campaign: CampaignData) -> bool:
	return campaign != null and campaign.element.is_empty() and campaign.requires_campaigns.has(&"convergence")


func _campaign_color(campaign: CampaignData) -> Color:
	if _is_assault(campaign):
		return Color("e0524a")
	if campaign == null or campaign.element.is_empty():
		return Color("f4e7c0")
	var element: ElementData = _elements.get(campaign.element)
	return element.color if element != null else Color.WHITE


## Medallions are drawn at a whole multiple of their pixels: larger when the map is closer.
func _medal_scale() -> float:
	return 3.0 if zoom >= 0.45 else 2.0


func _medal_radius(stage_id: StringName) -> float:
	var texture: Texture2D = _medals.get(stage_id)
	return (texture.get_width() if texture != null else 13) * _medal_scale() * 0.5


func _draw_map() -> void:
	_map_layer.draw_rect(Rect2(Vector2.ZERO, size), SPACE)
	if _map == null:
		return
	var origin := map_to_screen(Vector2.ZERO)
	if zoom >= 0.99:
		origin = origin.round()
	_map_layer.draw_texture_rect(_map, Rect2(origin, _map_size * zoom), false)


func _draw_marks() -> void:
	var meta := Progress.meta
	for id: StringName in _links:
		if meta.stars(id) > 0:
			_draw_trail(_points(_links[id]), _campaign_color(DataRegistry.campaign_of(id)), 0.7)
	for id: StringName in _order:
		var spot: Dictionary = _spots.get(String(id), {})
		if spot.has("trail") and meta.is_stage_unlocked(id):
			var walked := meta.stars(id) > 0
			_draw_trail(_points(spot["trail"]), _campaign_color(DataRegistry.campaign_of(id)), 1.0 if walked else 0.6)
	for id: StringName in _order:
		if meta.stars(id) > 0 and id != SAVED_CITY:
			_draw_smoke(id)
	_draw_land_labels()
	for id: StringName in _order:
		if _medals.has(id) and id != selected and id != _hovered:
			_draw_stage(id)
	for id: StringName in [_hovered, selected]:
		if _medals.has(id):
			_draw_stage(id)
	_draw_shades()


func _points(list: Variant) -> PackedVector2Array:
	var points := PackedVector2Array()
	for pair: Variant in list:
		points.append(_vec(pair))
	return points


## The road into an open stage, picked out in its land's colour, with light flowing along it.
func _draw_trail(points: PackedVector2Array, color: Color, strength: float) -> void:
	if points.size() < 2:
		return
	var width := clampf(4.0 * zoom, 2.0, 6.0)
	var screen := PackedVector2Array()
	for point in points:
		screen.append(map_to_screen(point))
	for i in range(0, screen.size() - 1, 2):
		_marks.draw_line(screen[i], screen[i + 1], Color(UiStyle.MENU_INK, 0.55 * strength), width + 3.0)
		_marks.draw_line(screen[i], screen[i + 1], Color(color.lightened(0.35), 0.85 * strength), width)
	var count := screen.size()
	for k in 3:
		var t := fposmod(_time * 0.12 + k / 3.0, 1.0) * (count - 1)
		var i := mini(int(t), count - 2)
		var at := screen[i].lerp(screen[i + 1], t - i)
		_marks.draw_rect(Rect2(at - Vector2.ONE * width, Vector2.ONE * width * 2.0), Color(1, 0.97, 0.85, 0.9 * strength))


## Smoke over a city that has fallen, with embers glowing under it.
func _draw_smoke(stage_id: StringName) -> void:
	var spot: Dictionary = _spots.get(String(stage_id), {})
	if not spot.has("city_top"):
		return
	var base := _vec(spot["city_top"])
	if not view_rect().grow(240.0 * maxf(zoom, 0.5)).has_point(map_to_screen(base)):
		return
	var seed := float(spot.get("number", 1)) * 1.7
	var glow := 0.22 + 0.1 * sin(_time * 3.0 + seed)
	_pixel_disc(map_to_screen(base + Vector2(0, 12)), maxf(22.0 * zoom, 3.0), Color(1.0, 0.42, 0.12, glow))
	_pixel_disc(map_to_screen(base + Vector2(0, 12)), maxf(10.0 * zoom, 2.0), Color(1.0, 0.62, 0.2, glow * 1.4))
	for i in 9:
		var t := fposmod(_time * 0.08 + i / 9.0 + seed * 0.13, 1.0)
		var drift := Vector2(sin(t * 4.0 + i * 1.3 + seed) * 10.0 + t * 60.0, -t * 170.0)
		var radius := (9.0 + t * 30.0) * zoom
		var shade := SMOKE.lerp(Color("6a6470"), t)
		_pixel_disc(map_to_screen(base + drift), maxf(radius, 2.0), Color(shade, 0.8 * (1.0 - t) * minf(1.0, t * 6.0)))


## A filled circle made of square cells that sit on the map's pixel grid, so smoke reads as pixel art.
func _pixel_disc(at: Vector2, radius: float, color: Color) -> void:
	var cell := maxf(2.0, roundf(zoom * 2.0))
	var origin := map_to_screen(Vector2.ZERO)
	var middle := ((at - origin) / cell).round() * cell + origin
	var rows := ceili(radius / cell)
	for row in range(-rows, rows + 1):
		var dy := row * cell
		var half := roundf(sqrt(maxf(radius * radius - dy * dy, 0.0)) / cell) * cell
		if half > 0.0:
			_marks.draw_rect(Rect2(middle.x - half, middle.y + dy, half * 2.0, cell), color)


func _draw_land_labels() -> void:
	var meta := Progress.meta
	var letter := float(clampi(roundi(zoom * 4.0), 2, 4))
	for entry in _labels:
		var texture: Texture2D = entry["texture"]
		var drawn := texture.get_size() * letter
		var middle := map_to_screen(entry["at"])
		# A name just under the title band slides down out of it.
		var lowest := HEADER_HEIGHT + drawn.y * 0.5 + 8.0
		if middle.y < lowest and middle.y > lowest - 240.0:
			middle.y = lowest
		_marks.draw_texture_rect(texture, Rect2((middle - drawn * 0.5).round(), drawn), false)
		var campaign := _campaign_of_land(entry["land"])
		if campaign == null:
			continue
		var line := "%d / %d STARS" % [meta.campaign_stars(campaign), campaign.stages.size() * 3]
		if meta.is_campaign_complete(campaign.id) and not campaign.reward_name.is_empty():
			line += "  -  " + campaign.reward_name.to_upper()
		_text_centered(line, middle + Vector2(0, drawn.y * 0.5 + 22.0), _small_font, 16,
				UiStyle.MENU_GOLD_LIGHT)


func _campaign_of_land(land: String) -> CampaignData:
	for campaign in Progress.meta.campaigns_in_order():
		if land == "heart" and campaign.id == &"convergence":
			return campaign
		if land == "hollow" and _is_assault(campaign):
			return campaign
		if not campaign.element.is_empty() and campaign.element == StringName(land):
			return campaign
	return null


func _draw_stage(stage_id: StringName) -> void:
	var meta := Progress.meta
	var texture := _medals[stage_id]
	var art := _medal_scale()
	var at := map_to_screen(_spot(stage_id)).round()
	var drawn := texture.get_size() * art
	var half := drawn.x * 0.5
	var unlocked := meta.is_stage_unlocked(stage_id)
	var stars := meta.stars(stage_id)
	if stage_id == selected:
		var breathe := 1.5 * sin(_time * 3.0)
		_marks.draw_circle(at, half + 14.0 + breathe, Color(UiStyle.MENU_GOLD_LIGHT, 0.16))
		_marks.draw_arc(at, half + 7.0 + breathe, 0.0, TAU, 48, UiStyle.MENU_INK, 7.0)
		_marks.draw_arc(at, half + 7.0 + breathe, 0.0, TAU, 48, UiStyle.MENU_GOLD_LIGHT, 3.5)
	elif unlocked and stars == 0:
		var pulse := 0.5 + 0.5 * sin(_time * 4.0)
		_marks.draw_arc(at, half + 5.0 + 3.0 * pulse, 0.0, TAU, 40, Color(UiStyle.MENU_GOLD, 0.35 + 0.5 * pulse), 3.0)
	elif stage_id == _hovered:
		_marks.draw_arc(at, half + 6.0, 0.0, TAU, 40, Color(1, 1, 1, 0.8), 3.0)
	var tint := Color.WHITE if unlocked else Color(0.42, 0.42, 0.5)
	_marks.draw_texture_rect(texture, Rect2(at - drawn * 0.5, drawn), false, tint)
	if not unlocked:
		var lock := TreeArt.icon(&"lock")
		if lock != null:
			var lock_size := lock.get_size() * (2.0 if art >= 3.0 else 1.0)
			_marks.draw_texture_rect(lock, Rect2(at + Vector2(half * 0.35, half * 0.2), lock_size), false)
	elif stars > 0 or stage_id == selected:
		var star := TreeArt.icon(&"star")
		if star != null:
			var star_size := star.get_size() * (1.5 if art >= 3.0 else 1.0)
			for i in 3:
				var spot := at + Vector2((i - 1) * (star_size.x + 2.0), half + star_size.y * 0.5 + 4.0)
				_marks.draw_texture_rect(star, Rect2(spot - star_size * 0.5, star_size), false,
						UiStyle.MENU_GOLD_LIGHT if i < stars else Color(0.3, 0.28, 0.36, 0.9))
	_draw_city_name(stage_id, at, half)


## The city's name beside its medallion: always for the picked and hovered stage, for every stage
## once the map is close enough to read them.
func _draw_city_name(stage_id: StringName, at: Vector2, half: float) -> void:
	var focused := stage_id == selected or stage_id == _hovered
	if zoom < 0.45 and not focused:
		return
	var spot: Dictionary = _spots.get(String(stage_id), {})
	var city := str(Story.shared().city(stage_id).get("name", spot.get("city", "")))
	if stage_id == &"assault_1":
		city = "The final assault"
	if city.is_empty():
		return
	var fallen := Progress.meta.stars(stage_id) > 0 and stage_id != SAVED_CITY
	var color := UiStyle.MENU_TEXT if not fallen else Color("aaa092")
	if stage_id == SAVED_CITY:
		color = UiStyle.MENU_GOLD_LIGHT
	var font_size := 30
	var side := str(spot.get("label", "below"))
	var width := _city_font.get_string_size(city, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	var position := at + Vector2(-width * 0.5, half + 50.0)
	if side == "left":
		position = at + Vector2(-half - 12.0 - width, 10.0)
	elif side == "right":
		position = at + Vector2(half + 12.0, 10.0)
	_text(city, position, _city_font, font_size, color)
	var stage: StageData = DataRegistry.stages.get(stage_id)
	if focused and stage != null and stage.display_name != city:
		var sub := stage.display_name.to_upper()
		var sub_width := _small_font.get_string_size(sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x
		var sub_x := position.x + (width - sub_width) * 0.5 if side == "below" else \
				(position.x + width - sub_width if side == "left" else position.x)
		_text(sub, Vector2(sub_x, position.y + 24.0), _small_font, 16, UiStyle.MENU_GOLD)


## Dark bands under the header and the controls line, so they read over any part of the map.
func _draw_shades() -> void:
	var width := view_rect().size.x
	_marks.draw_rect(Rect2(0, 0, width, 130), Color(SPACE, 0.78))
	var fade := PackedColorArray([Color(SPACE, 0.78), Color(SPACE, 0.78), Color(SPACE, 0.0), Color(SPACE, 0.0)])
	_marks.draw_polygon(PackedVector2Array([Vector2(0, 130), Vector2(width, 130), Vector2(width, 210), Vector2(0, 210)]), fade)
	var foot := PackedColorArray([Color(SPACE, 0.0), Color(SPACE, 0.0), Color(SPACE, 0.8), Color(SPACE, 0.8)])
	_marks.draw_polygon(PackedVector2Array([Vector2(0, size.y - 70), Vector2(width, size.y - 70), Vector2(width, size.y),
		Vector2(0, size.y)]), foot)
	_text("WHEEL OR +/- ZOOM  -  DRAG TO MOVE  -  ARROWS PICK A STAGE  -  HOME WHOLE WORLD  -  ENTER BEGINS",
		Vector2(48, size.y - 30), _small_font, 16, UiStyle.MENU_DIM)
	var meta := Progress.meta
	var total := 0
	var earned := 0
	for campaign in meta.campaigns_in_order():
		total += campaign.stages.size() * 3
		earned += meta.campaign_stars(campaign)
	_stars_label.text = "%d / %d STARS" % [earned, total]


func _text(text: String, at: Vector2, font: Font, font_size: int, color: Color) -> void:
	_marks.draw_string_outline(font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, 6, Color(UiStyle.MENU_INK, 0.9))
	_marks.draw_string(font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size, color)


func _text_centered(text: String, at: Vector2, font: Font, font_size: int, color: Color) -> void:
	var width := font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, font_size).x
	_text(text, at - Vector2(width * 0.5, 0), font, font_size, color)
