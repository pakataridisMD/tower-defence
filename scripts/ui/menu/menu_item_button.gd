class_name MenuItemButton
extends Button
## A wide menu button: an icon, its name, a dim note on the right (such as "8 points") and its key
## in a small keycap. When hovered it gets the gold frame and a gold gem on its left edge.

const KEY_SIZE := 16
const NOTE_SIZE := 16

## The key shown in a keycap on the right, such as "C". Empty shows none.
var key_text := "":
	set(value):
		key_text = value
		queue_redraw()
## Small text before the keycap, such as "Ember Reach - stage 3". Empty shows none.
var note := "":
	set(value):
		note = value
		queue_redraw()


func _init(text_value: String = "", key: String = "", icon_name: String = "", note_text: String = "") -> void:
	text = text_value
	key_text = key
	note = note_text
	focus_mode = Control.FOCUS_NONE
	alignment = HORIZONTAL_ALIGNMENT_LEFT
	icon = UiStyle.menu_art("icon_" + icon_name) if not icon_name.is_empty() else null
	add_theme_constant_override("h_separation", 16)
	var f := UiStyle.font("button")
	if f != null:
		add_theme_font_override("font", f)
	add_theme_font_size_override("font_size", 40)
	mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	mouse_entered.connect(queue_redraw)
	mouse_exited.connect(queue_redraw)


func _draw() -> void:
	var hot := is_hovered() and not disabled
	var small := UiStyle.font("small")
	var right := size.x - 18.0
	if not key_text.is_empty() and small != null:
		var width := maxf(28.0, small.get_string_size(key_text, HORIZONTAL_ALIGNMENT_LEFT, -1, KEY_SIZE).x + 14.0)
		var box := Rect2(Vector2(right - width, size.y * 0.5 - 14.0), Vector2(width, 28.0))
		draw_rect(box, UiStyle.MENU_INK)
		draw_rect(box.grow(-2), Color("554a66"))
		draw_rect(Rect2(box.position + Vector2(2, box.size.y - 6), Vector2(box.size.x - 4, 4)), Color("231d2e"))
		draw_string(small, Vector2(box.position.x + 7.0, box.position.y + 18.0), key_text, HORIZONTAL_ALIGNMENT_LEFT,
				-1, KEY_SIZE, UiStyle.MENU_TEXT if not disabled else UiStyle.MENU_DIM)
		right = box.position.x - 14.0
	if not note.is_empty() and small != null:
		var width := small.get_string_size(note, HORIZONTAL_ALIGNMENT_LEFT, -1, NOTE_SIZE).x
		draw_string(small, Vector2(right - width, size.y * 0.5 + 6.0), note, HORIZONTAL_ALIGNMENT_LEFT, -1, NOTE_SIZE,
				UiStyle.MENU_GOLD if hot else UiStyle.MENU_DIM)
	if hot:
		# A gold gem hanging off the left edge.
		var mid := size.y * 0.5
		for i in 5:
			draw_rect(Rect2(Vector2(-8 + i * 2, mid - (5 - i) * 2), Vector2(2, (5 - i) * 4)), UiStyle.MENU_INK)
		for i in 4:
			draw_rect(Rect2(Vector2(-6 + i * 2, mid - (4 - i) * 2 + 2), Vector2(2, (4 - i) * 4 - 4)),
					UiStyle.MENU_GOLD_LIGHT if i < 2 else UiStyle.MENU_GOLD)
