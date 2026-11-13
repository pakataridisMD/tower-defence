class_name WeatherBadge
extends Control
## Tells the player what the sky is doing: when a spell of weather rolls in, a banner across the
## battle ("A THUNDERSTORM BREAKS"), and while it lasts, a badge in the top left corner of the view with
## a pixel icon, the weather's name and the waves it covers. It hides again when the sky clears.
##
## Part of the HUD (see Hud.show_weather); it reads the board's WeatherArt every frame.

const BADGE_POSITION := Vector2(24, 100)
const BANNER_TOP := 248.0
## How long the arrival banner stays, in seconds (it fades out over the last second).
const BANNER_TIME := 4.5
## Pixel size of the icon (14x14 picture pixels).
const ICON_SCALE := 4.0

## The colour each kind is named in.
const COLORS := {
	Weather.Kind.RAIN: Color(0.58, 0.75, 1.0), Weather.Kind.STORM: Color(1.0, 0.86, 0.38),
	Weather.Kind.SNOW: Color(0.9, 0.95, 1.0), Weather.Kind.BLIZZARD: Color(0.78, 0.92, 1.0),
	Weather.Kind.ASH: Color(1.0, 0.56, 0.26), Weather.Kind.DUST: Color(0.94, 0.74, 0.46),
}
## The icons, 14x14, one letter per pixel (see PALETTE; "." is empty).
const ICONS := {
	Weather.Kind.RAIN: [
		"..............", "....cccc......", "...cccccc.ccc.", ".cccccccccccc.", "cccccccccccccc",
		"cccccccccccccc", ".CCCCCCCCCCCC.", "..............", "..b...b...b...", ".b...b...b....",
		"..............", "...b...b...b..", "..b...b...b...", "..............",
	],
	Weather.Kind.STORM: [
		"..............", "....CCCC......", "...CCCCCC.CCC.", ".CCCCCCCCCCCCC", "CCCCCCCCCCCCCC",
		"CCCCCCCCCCCCCC", ".GGGGyyGGGGGG.", "......yy...b..", ".b...yy....b..", "b...yyyyy.....",
		"......yy..b...", ".b...yy...b...", "b....y........", "..............",
	],
	Weather.Kind.SNOW: [
		"......w.......", "....w.w.w.....", ".....www......", ".w....w....w..", "..w...w...w...",
		"...w..w..w....", "wwwwwwwwwwwww.", "...w..w..w....", "..w...w...w...", ".w....w....w..",
		".....www......", "....w.w.w.....", "......w.......", "..............",
	],
	Weather.Kind.BLIZZARD: [
		"..............", ".wwwwwwww..w..", "..........w.w.", "..wwwwwwwwww..", "..............",
		"w..wwwwwwwwwww", "..............", ".wwwwwww...w..", "..........w.w.", "...w.....w....",
		"..w.w.........", "...w...wwwwww.", "..............", "..............",
	],
	Weather.Kind.ASH: [
		"....g..g......", "..g...gg..g...", "...gggggg.....", "..gggGGggg....", "...ggGGgg.o...",
		".....GG.......", "....oGGo......", ".o...oo...o...", "....SrrS......", "...SSrrSS.....",
		"..SSSrrSSS....", ".SSSSSSSSSS...", "SSSSSSSSSSSSS.", "..............",
	],
	Weather.Kind.DUST: [
		"..............", "..sssssssss...", ".s.........s..", "..........s...", ".ssssssss.....",
		"..............", "...ssssssssss.", "..s...........", "...s......s...", "....ssssss....",
		"..............", ".ssss..sssss..", "..............", "..............",
	],
}
const PALETTE := {
	"c": Color(0.8, 0.83, 0.9), "C": Color(0.46, 0.5, 0.6), "G": Color(0.32, 0.35, 0.44),
	"b": Color(0.48, 0.68, 1.0), "y": Color(1.0, 0.9, 0.35), "w": Color(0.95, 0.97, 1.0),
	"g": Color(0.6, 0.57, 0.55), "o": Color(1.0, 0.55, 0.18), "r": Color(1.0, 0.36, 0.1),
	"S": Color(0.3, 0.22, 0.2), "s": Color(0.9, 0.72, 0.46),
}

var sky: WeatherArt
var sim: RunSim
## The kind on the badge and the banner (what the sky shows now).
var shown := Weather.Kind.CLEAR

var _badge: PanelContainer
var _icon: Control
var _title: Label
var _detail: Label
var _banner: VBoxContainer
var _banner_title: Label
var _banner_detail: Label
var _banner_time := 0.0


func setup(p_sky: WeatherArt, p_sim: RunSim) -> void:
	sky = p_sky
	sim = p_sim
	name = "WeatherBadge"
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_build_badge()
	_build_banner()
	_refresh(0.0)


func _build_badge() -> void:
	_badge = PanelContainer.new()
	_badge.theme_type_variation = &"SlimPanel"
	_badge.position = BADGE_POSITION
	_badge.mouse_filter = Control.MOUSE_FILTER_PASS
	_badge.tooltip_text = "The weather is only for the eyes: it does not change the battle."
	add_child(_badge)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	_badge.add_child(row)
	_icon = Control.new()
	_icon.custom_minimum_size = Vector2(14, 14) * ICON_SCALE
	_icon.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_icon.draw.connect(_draw_icon)
	row.add_child(_icon)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 0)
	column.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(column)
	_title = UiStyle.label("", 30)
	_title.add_theme_color_override("font_outline_color", UiStyle.MENU_INK)
	_title.add_theme_constant_override("outline_size", 6)
	_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(_title)
	_detail = UiStyle.label("", 16, UiStyle.MENU_DIM)
	_detail.custom_minimum_size = Vector2(190, 0)
	_detail.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(_detail)
	_badge.hide()


func _build_banner() -> void:
	_banner = VBoxContainer.new()
	_banner.position = Vector2(24, BANNER_TOP)
	_banner.size = Vector2(1536, 110)
	_banner.add_theme_constant_override("separation", 2)
	_banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_banner)
	_banner_title = UiStyle.label("", 52)
	_banner_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_title.add_theme_color_override("font_outline_color", UiStyle.MENU_INK)
	_banner_title.add_theme_constant_override("outline_size", 10)
	_banner_title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.add_child(_banner_title)
	_banner_detail = UiStyle.label("", 16, UiStyle.MENU_TEXT)
	_banner_detail.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner_detail.add_theme_color_override("font_outline_color", UiStyle.MENU_INK)
	_banner_detail.add_theme_constant_override("outline_size", 6)
	_banner_detail.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.add_child(_banner_detail)
	_banner.hide()


func _process(delta: float) -> void:
	_refresh(delta)


func _refresh(delta: float) -> void:
	if sky == null or not is_instance_valid(sky):
		_badge.hide()
		_banner.hide()
		return
	var now := sky.kind if sky.intensity > 0.001 else Weather.Kind.CLEAR
	if now != shown:
		shown = now
		if shown != Weather.Kind.CLEAR:
			_announce()
		_icon.queue_redraw()
	_badge.visible = shown != Weather.Kind.CLEAR
	if _badge.visible:
		_title.text = Weather.describe(shown)
		_title.add_theme_color_override("font_color", COLORS[shown])
		_detail.text = detail()
		_badge.modulate.a = clampf(sky.intensity * 3.0, 0.0, 1.0)
		_badge.reset_size()
	_banner_time = maxf(0.0, _banner_time - delta)
	_banner.visible = _banner_time > 0.0
	_banner.modulate.a = clampf(_banner_time, 0.0, 1.0)


## The banner as a spell of weather rolls in.
func _announce() -> void:
	_banner_title.text = String(Weather.ARRIVALS.get(shown, Weather.describe(shown))).to_upper()
	_banner_title.add_theme_color_override("font_color", COLORS[shown])
	_banner_detail.text = "%s  -  %s" % [Weather.describe(shown), _waves_text()]
	_banner_time = BANNER_TIME


## The line under the badge's name: which waves it covers, or that it is clearing.
func detail() -> String:
	if sky.target_kind() != shown:
		return "Clearing"
	return _waves_text()


func _waves_text() -> String:
	var spell := sky.weather.spell_at(sim.wave_number())
	if spell.is_empty():
		return "Passing over"
	var first := int(spell[1])
	var last := int(spell[2])
	if first == last:
		return "For wave %d" % first
	return "For waves %d and %d" % [first, last]


## The text on the banner now (empty when it is not showing), for tests.
func banner_text() -> String:
	return _banner_title.text if _banner.visible else ""


func badge_visible() -> bool:
	return _badge.visible


func _draw_icon() -> void:
	var rows: Array = ICONS.get(shown, [])
	for y in rows.size():
		var line: String = rows[y]
		for x in line.length():
			var key := line[x]
			if PALETTE.has(key):
				_icon.draw_rect(Rect2(Vector2(x, y) * ICON_SCALE, Vector2.ONE * ICON_SCALE), PALETTE[key])
