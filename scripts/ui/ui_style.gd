class_name UiStyle
extends RefCounted
## Shared colours, theme and small widget helpers so every screen looks the same.

const BACKGROUND := Color("1f2433")
const PANEL := Color("272e3f")
const PANEL_BORDER := Color("3b4459")
const TEXT := Color("e9ecf2")
const TEXT_DIM := Color("9aa3b5")
const GOLD := Color("f2c14e")
const LIFE := Color("ff7b7b")
const GOOD := Color("6bdc8a")
const BAD := Color("ff6b6b")
const KEYSTONE := Color("e8c547")


## Pixel art for panels and buttons, drawn by tools/art/gen_ui_art.py. Every picture is already
## doubled, so it is shown at one screen pixel per picture pixel and stays sharp.
const ART := "res://assets/art/ui/"
## Edge of a panel or button picture that is never stretched, in screen pixels.
const SLICE := 8
## Flat colours used when a picture is missing.
const BUTTON_FLAT := {
	"normal": Color("39425a"), "hover": Color("48536f"), "pressed": Color("2f3749"), "disabled": Color("2b3142"),
	"picked": Color("48536f"),
}

static var _art: Dictionary = {}


## A picture from the interface art, or null if it has not been drawn.
static func art(name: String) -> Texture2D:
	if _art.has(name):
		return _art[name]
	var path := ART + name + ".png"
	var texture: Texture2D = load(path) if ResourceLoader.exists(path) else null
	_art[name] = texture
	return texture


static func make_theme() -> Theme:
	var theme := Theme.new()
	theme.default_font_size = 20

	theme.set_stylebox("panel", "PanelContainer", panel_box(14, 14))
	# Slim panels and compact buttons, for the HUD where room is tight.
	theme.set_type_variation("SlimPanel", "PanelContainer")
	theme.set_stylebox("panel", "SlimPanel", panel_box(10, 8))
	theme.set_type_variation("CompactButton", "Button")
	for state: String in ["normal", "hover", "pressed", "disabled"]:
		theme.set_stylebox(state, "Button", button_box(state, 14, 8))
		theme.set_stylebox(state, "CompactButton", button_box(state, 5, 4))
	theme.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	theme.set_stylebox("focus", "CompactButton", StyleBoxEmpty.new())
	theme.set_color("font_color", "Button", TEXT)
	theme.set_color("font_hover_color", "Button", Color.WHITE)
	theme.set_color("font_pressed_color", "Button", TEXT)
	theme.set_color("font_disabled_color", "Button", Color(TEXT_DIM, 0.7))
	theme.set_color("font_color", "Label", TEXT)
	theme.set_color("default_color", "RichTextLabel", TEXT)
	theme.set_stylebox("panel", "TooltipPanel", panel_box(10, 8))
	theme.set_color("font_color", "TooltipLabel", TEXT)
	theme.set_font_size("font_size", "TooltipLabel", 17)
	return theme


## The frame behind a panel, with this much room between the frame and what is inside.
static func panel_box(margin_x: float, margin_y: float) -> StyleBox:
	var texture := art("panel")
	if texture == null:
		var flat := StyleBoxFlat.new()
		flat.bg_color = PANEL
		flat.border_color = PANEL_BORDER
		flat.set_border_width_all(2)
		flat.set_corner_radius_all(10)
		flat.content_margin_left = margin_x
		flat.content_margin_right = margin_x
		flat.content_margin_top = margin_y
		flat.content_margin_bottom = margin_y
		return flat
	var box := StyleBoxTexture.new()
	box.texture = texture
	box.set_texture_margin_all(SLICE)
	box.content_margin_left = margin_x
	box.content_margin_right = margin_x
	box.content_margin_top = margin_y
	box.content_margin_bottom = margin_y
	return box


## A button's look in one state: normal, hover, pressed, disabled or picked.
static func button_box(state: String, margin_x: float, margin_y: float) -> StyleBox:
	var texture := art("button_" + state)
	# A pressed button sinks a little.
	var sink := 2.0 if state == "pressed" else 0.0
	if texture == null:
		var flat := StyleBoxFlat.new()
		flat.bg_color = BUTTON_FLAT[state]
		flat.set_corner_radius_all(8)
		if state == "picked":
			flat.border_color = GOLD
			flat.set_border_width_all(2)
		flat.content_margin_left = margin_x
		flat.content_margin_right = margin_x
		flat.content_margin_top = margin_y + sink
		flat.content_margin_bottom = margin_y - sink
		return flat
	var box := StyleBoxTexture.new()
	box.texture = texture
	box.set_texture_margin_all(SLICE)
	box.content_margin_left = margin_x
	box.content_margin_right = margin_x
	box.content_margin_top = margin_y + sink
	box.content_margin_bottom = margin_y - sink
	return box


## A button that never takes keyboard focus, so Space and Enter stay free for game shortcuts.
static func button(text: String, font_size: int = 20) -> Button:
	var result := Button.new()
	result.text = text
	result.focus_mode = Control.FOCUS_NONE
	result.add_theme_font_size_override("font_size", font_size)
	return result


## A small button that shows its keyboard key in the corner (see KeyButton). Like button(), it
## never takes keyboard focus.
static func key_button(text: String, font_size: int = 16) -> KeyButton:
	var result := KeyButton.new()
	result.text = text
	result.focus_mode = Control.FOCUS_NONE
	result.theme_type_variation = &"CompactButton"
	result.add_theme_font_size_override("font_size", font_size)
	return result


## A toggle button for picking one option from a group, such as a map. The picked one gets a
## gold border.
static func choice_button(text: String, group: ButtonGroup, font_size: int = 20) -> Button:
	var result := button(text, font_size)
	result.toggle_mode = true
	result.button_group = group
	var picked := button_box("picked", 14, 8)
	result.add_theme_stylebox_override("pressed", picked)
	result.add_theme_stylebox_override("hover_pressed", picked)
	result.add_theme_color_override("font_pressed_color", Color.WHITE)
	result.add_theme_color_override("font_hover_pressed_color", Color.WHITE)
	return result


static func label(text: String, font_size: int = 20, color: Color = TEXT) -> Label:
	var result := Label.new()
	result.text = text
	result.add_theme_font_size_override("font_size", font_size)
	result.add_theme_color_override("font_color", color)
	return result


## A small round icon in one or two element colours, used on tower buttons.
static func element_icon(colors: Array[Color], icon_size: int = 28) -> ImageTexture:
	var image := Image.create(icon_size, icon_size, false, Image.FORMAT_RGBA8)
	var radius := icon_size * 0.5 - 1.0
	var center := Vector2(icon_size, icon_size) * 0.5
	for x in icon_size:
		for y in icon_size:
			var point := Vector2(x + 0.5, y + 0.5)
			if point.distance_to(center) > radius:
				continue
			var index := 0 if colors.size() < 2 or point.x < center.x else 1
			image.set_pixel(x, y, colors[index])
	return ImageTexture.create_from_image(image)


# --- The menu look -----------------------------------------------------------------
# The main menu and its pages use pixel fonts and stone-and-gold frames painted by
# tools/art/menu/gen_menu_assets.py. Other screens keep make_theme() until they opt in with
# menu_theme().

const MENU_ART := "res://assets/art/menu/"
const FONT_DIR := "res://assets/fonts/"
## Font files for each kind of text. Sizes that keep the pixel fonts on their grid: titles any size,
## buttons 40 (or 30, 50), body 32, small 16.
const FONTS := {
	"title": "PirataOne-Regular.ttf", "button": "Jersey10-Regular.ttf", "body": "PixelifySans.ttf",
	"small": "Silkscreen-Regular.ttf",
}
const MENU_TEXT := Color("efe3c8")
const MENU_DIM := Color("9d92a8")
const MENU_GOLD := Color("d8ac60")
const MENU_GOLD_LIGHT := Color("f6d690")
const MENU_INK := Color("0c0910")
## Corner size of the menu frames in screen pixels (8 picture pixels shown at 2x).
const MENU_SLICE := 16

static var _fonts: Dictionary = {}


## A pixel font for "title", "button", "body" or "small" text, drawn without smoothing so it stays
## crisp. Null if the font file is missing.
static func font(kind: String) -> Font:
	if _fonts.has(kind):
		return _fonts[kind]
	var path: String = FONT_DIR + str(FONTS.get(kind, ""))
	var result: FontFile = null
	if ResourceLoader.exists(path):
		result = (load(path) as FontFile).duplicate()
		result.antialiasing = TextServer.FONT_ANTIALIASING_NONE
		result.hinting = TextServer.HINTING_NONE
		result.subpixel_positioning = TextServer.SUBPIXEL_POSITIONING_DISABLED
		result.generate_mipmaps = false
	_fonts[kind] = result
	return result


## A picture from the menu art, or null.
static func menu_art(name: String) -> Texture2D:
	var key := "menu/" + name
	if _art.has(key):
		return _art[key]
	var path := MENU_ART + name + ".png"
	var texture: Texture2D = load(path) if ResourceLoader.exists(path) else null
	_art[key] = texture
	return texture


## A stone frame with a gold line (ornate: gold rivets in the corners). Its middle is tiled.
static func menu_panel_box(margin_x: float = 28, margin_y: float = 24, ornate: bool = true) -> StyleBox:
	var texture := menu_art("panel" if ornate else "panel_plain")
	if texture == null:
		return panel_box(margin_x, margin_y)
	return _tiled(texture, MENU_SLICE, margin_x, margin_y)


## A menu button in one state: normal, hover, pressed, picked or disabled.
static func menu_button_box(state: String, margin_x: float = 18, margin_y: float = 6) -> StyleBox:
	var texture := menu_art("button_" + state)
	if texture == null:
		return button_box(state, margin_x, margin_y)
	var sink := 2.0 if state == "pressed" else 0.0
	return _tiled(texture, 8, margin_x, margin_y + sink, margin_y - sink)


static func _tiled(texture: Texture2D, slice: int, margin_x: float, margin_top: float, margin_bottom: float = -1.0) -> StyleBoxTexture:
	var box := StyleBoxTexture.new()
	box.texture = texture
	box.set_texture_margin_all(slice)
	box.axis_stretch_horizontal = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	box.axis_stretch_vertical = StyleBoxTexture.AXIS_STRETCH_MODE_TILE_FIT
	box.content_margin_left = margin_x
	box.content_margin_right = margin_x
	box.content_margin_top = margin_top
	box.content_margin_bottom = margin_top if margin_bottom < 0.0 else margin_bottom
	return box


## The theme for the menu and its pages: pixel fonts, stone and gold frames, gold for picked.
static func menu_theme() -> Theme:
	var theme := make_theme()
	var body := font("body")
	if body != null:
		theme.default_font = body
	theme.default_font_size = 32
	theme.set_stylebox("panel", "PanelContainer", menu_panel_box())
	for state: String in ["normal", "hover", "pressed", "disabled"]:
		theme.set_stylebox(state, "Button", menu_button_box(state))
	theme.set_stylebox("hover_pressed", "Button", menu_button_box("picked"))
	var button_font := font("button")
	if button_font != null:
		theme.set_font("font", "Button", button_font)
		theme.set_font("font", "CheckBox", button_font)
		theme.set_font("font", "CheckButton", button_font)
		theme.set_font("font", "OptionButton", button_font)
	theme.set_font_size("font_size", "Button", 40)
	theme.set_font_size("font_size", "CheckBox", 40)
	theme.set_font_size("font_size", "CheckButton", 40)
	theme.set_color("font_color", "Button", MENU_TEXT)
	theme.set_color("font_hover_color", "Button", Color("fff6d8"))
	theme.set_color("font_pressed_color", "Button", Color("fff6d8"))
	theme.set_color("font_hover_pressed_color", "Button", Color("fff6d8"))
	theme.set_color("font_disabled_color", "Button", Color("5e566a"))
	theme.set_color("font_color", "Label", MENU_TEXT)
	theme.set_color("default_color", "RichTextLabel", MENU_TEXT)
	theme.set_stylebox("panel", "TooltipPanel", menu_panel_box(14, 10, false))
	theme.set_color("font_color", "TooltipLabel", MENU_TEXT)
	theme.set_font_size("font_size", "TooltipLabel", 32)
	if body != null:
		theme.set_font("font", "TooltipLabel", body)
	return theme


## A label in one of the menu fonts.
static func menu_label(text: String, kind: String = "body", font_size: int = 32, color: Color = MENU_TEXT) -> Label:
	var result := label(text, font_size, color)
	var f := font(kind)
	if f != null:
		result.add_theme_font_override("font", f)
	result.add_theme_color_override("font_shadow_color", MENU_INK)
	result.add_theme_constant_override("shadow_offset_x", 2)
	result.add_theme_constant_override("shadow_offset_y", 2)
	return result


## A page or panel title: gold blackletter with a dark outline.
static func menu_title(text: String, font_size: int = 96) -> Label:
	var result := menu_label(text, "title", font_size, MENU_GOLD_LIGHT)
	result.add_theme_color_override("font_outline_color", MENU_INK)
	result.add_theme_constant_override("outline_size", 6)
	result.add_theme_constant_override("shadow_offset_y", 4)
	return result


## A menu button with the button font. It never takes keyboard focus.
static func menu_button(text: String, font_size: int = 40) -> Button:
	var result := button(text, font_size)
	var f := font("button")
	if f != null:
		result.add_theme_font_override("font", f)
	return result


## Like menu_button, but toggles inside a group; the picked one gets the gold frame.
static func menu_choice(text: String, group: ButtonGroup, font_size: int = 40) -> Button:
	var result := menu_button(text, font_size)
	result.toggle_mode = true
	result.button_group = group
	var picked := menu_button_box("picked")
	result.add_theme_stylebox_override("pressed", picked)
	result.add_theme_stylebox_override("hover_pressed", picked)
	return result


## An on/off switch (Mute, V-Sync): a CheckBox drawn as a menu button that turns gold when on.
static func menu_switch() -> CheckBox:
	var result := CheckBox.new()
	result.focus_mode = Control.FOCUS_NONE
	result.alignment = HORIZONTAL_ALIGNMENT_CENTER
	result.add_theme_constant_override("h_separation", 0)
	result.add_theme_icon_override("checked", PlaceholderTexture2D.new())
	result.add_theme_icon_override("unchecked", PlaceholderTexture2D.new())
	result.add_theme_icon_override("checked_disabled", PlaceholderTexture2D.new())
	result.add_theme_icon_override("unchecked_disabled", PlaceholderTexture2D.new())
	for state: String in ["normal", "hover", "disabled"]:
		result.add_theme_stylebox_override(state, menu_button_box(state))
	var picked := menu_button_box("picked")
	result.add_theme_stylebox_override("pressed", picked)
	result.add_theme_stylebox_override("hover_pressed", picked)
	result.add_theme_color_override("font_pressed_color", MENU_GOLD_LIGHT)
	result.add_theme_color_override("font_hover_pressed_color", MENU_GOLD_LIGHT)
	return result
