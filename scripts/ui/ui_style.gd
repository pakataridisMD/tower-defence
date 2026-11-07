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


static func make_theme() -> Theme:
	var theme := Theme.new()
	theme.default_font_size = 20

	var panel := StyleBoxFlat.new()
	panel.bg_color = PANEL
	panel.border_color = PANEL_BORDER
	panel.set_border_width_all(2)
	panel.set_corner_radius_all(10)
	panel.set_content_margin_all(14)
	theme.set_stylebox("panel", "PanelContainer", panel)

	theme.set_stylebox("normal", "Button", _button_box(Color("39425a")))
	theme.set_stylebox("hover", "Button", _button_box(Color("48536f")))
	theme.set_stylebox("pressed", "Button", _button_box(Color("2f3749")))
	theme.set_stylebox("disabled", "Button", _button_box(Color("2b3142")))
	theme.set_stylebox("focus", "Button", StyleBoxEmpty.new())
	theme.set_color("font_color", "Button", TEXT)
	theme.set_color("font_hover_color", "Button", Color.WHITE)
	theme.set_color("font_pressed_color", "Button", TEXT)
	theme.set_color("font_disabled_color", "Button", Color(TEXT_DIM, 0.7))
	theme.set_color("font_color", "Label", TEXT)
	theme.set_color("default_color", "RichTextLabel", TEXT)
	return theme


static func _button_box(color: Color) -> StyleBoxFlat:
	var box := StyleBoxFlat.new()
	box.bg_color = color
	box.set_corner_radius_all(8)
	box.content_margin_left = 14
	box.content_margin_right = 14
	box.content_margin_top = 8
	box.content_margin_bottom = 8
	return box


## A button that never takes keyboard focus, so Space and Enter stay free for game shortcuts.
static func button(text: String, font_size: int = 20) -> Button:
	var result := Button.new()
	result.text = text
	result.focus_mode = Control.FOCUS_NONE
	result.add_theme_font_size_override("font_size", font_size)
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
