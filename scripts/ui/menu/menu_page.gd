class_name MenuPage
extends Control
## One page of the main menu (Skirmish, Heroes, Codex, Settings, Credits): a Back button with its
## Esc key, the page title in gold, a line under it, and the room below for the page itself.
## Pages fill the screen over the dimmed menu backdrop.

signal back_requested

## Where the page's own content goes, under the title.
var body: Control
var back_button: MenuItemButton
var title_label: Label


func _init(title: String, subtitle: String = "") -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	var shade := ColorRect.new()
	shade.color = Color(0.07, 0.05, 0.1, 0.74)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	shade.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(shade)
	back_button = MenuItemButton.new("Back", "Esc")
	back_button.position = Vector2(48, 36)
	back_button.size = Vector2(184, 56)
	back_button.pressed.connect(func() -> void: back_requested.emit())
	add_child(back_button)
	title_label = UiStyle.menu_title(title, 96)
	title_label.position = Vector2(264, 4)
	add_child(title_label)
	if not subtitle.is_empty():
		var sub := UiStyle.menu_label(subtitle, "body", 32, UiStyle.MENU_DIM)
		sub.position = Vector2(272, 116)
		add_child(sub)
	var line := Divider.new()
	line.position = Vector2(48, 166)
	line.size = Vector2(1824, 12)
	add_child(line)
	body = Control.new()
	body.position = Vector2(48, 192)
	body.size = Vector2(1824, 852)
	body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(body)


## Called every time the page is shown, to pick up changes since it was built.
func refresh() -> void:
	pass


## A framed panel inside the page body, at a place and size in body coordinates.
func add_panel(at: Vector2, panel_size: Vector2, ornate: bool = true) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.menu_panel_box(28, 24, ornate))
	panel.position = at
	panel.size = panel_size
	body.add_child(panel)
	return panel


## A gold line with a diamond in the middle, between parts of a page.
class Divider:
	extends Control

	func _init() -> void:
		mouse_filter = Control.MOUSE_FILTER_IGNORE
		custom_minimum_size = Vector2(0, 12)

	func _draw() -> void:
		var y := size.y * 0.5
		draw_rect(Rect2(0, y - 1, size.x, 2), Color("8a6430"))
		draw_rect(Rect2(0, y + 1, size.x, 2), UiStyle.MENU_INK)
		var mid := size.x * 0.5
		for i in 4:
			draw_rect(Rect2(mid - i * 2, y - 6 + i * 2, i * 4 + 2, 2), UiStyle.MENU_GOLD)
			draw_rect(Rect2(mid - i * 2, y + 6 - i * 2, i * 4 + 2, 2), UiStyle.MENU_GOLD)
