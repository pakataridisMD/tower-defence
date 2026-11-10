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
