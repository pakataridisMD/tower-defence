class_name KeyButton
extends Button
## A button that shows its keyboard key in the corner. Skill buttons also show their cooldown: a
## shade that drains away as the skill gets ready, with the seconds left on top.

const KEY_FONT_SIZE := 13
const KEY_BOX := Color(0.05, 0.05, 0.09, 0.88)
const SHADE := Color(0.03, 0.03, 0.07, 0.74)

## The key to show, such as "Q" or "1". Empty shows nothing.
var key_text := "":
	set(value):
		if key_text != value:
			key_text = value
			queue_redraw()
## Share of the cooldown still to run, from 0 (ready) to 1 (just used).
var cooldown := 0.0:
	set(value):
		if not is_equal_approx(cooldown, value):
			cooldown = value
			queue_redraw()
## Written over the shade, such as the seconds left.
var cooldown_text := "":
	set(value):
		if cooldown_text != value:
			cooldown_text = value
			queue_redraw()
## A border drawn around the button, for a skill that is running or being aimed. Clear for none.
var outline := Color(0, 0, 0, 0):
	set(value):
		if outline != value:
			outline = value
			queue_redraw()


func _draw() -> void:
	var font := get_theme_default_font()
	if cooldown > 0.0:
		draw_rect(Rect2(Vector2(2, 2), Vector2(size.x - 4.0, (size.y - 4.0) * clampf(cooldown, 0.0, 1.0))), SHADE)
		if not cooldown_text.is_empty():
			var width := font.get_string_size(cooldown_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 22).x
			var at := Vector2((size.x - width) * 0.5, size.y * 0.5 + 8.0)
			draw_string_outline(font, at, cooldown_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, 5, Color(0, 0, 0, 0.8))
			draw_string(font, at, cooldown_text, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color.WHITE)
	if outline.a > 0.0:
		draw_rect(Rect2(Vector2.ONE, size - Vector2(2, 2)), outline, false, 2.0)
	if not key_text.is_empty():
		var width := font.get_string_size(key_text, HORIZONTAL_ALIGNMENT_LEFT, -1, KEY_FONT_SIZE).x
		var box := Rect2(Vector2(3, 3), Vector2(maxf(17.0, width + 8.0), 17.0))
		draw_rect(box, KEY_BOX)
		var color := UiStyle.GOLD if not disabled else UiStyle.TEXT_DIM
		draw_string(font, box.position + Vector2((box.size.x - width) * 0.5, 13.0), key_text,
				HORIZONTAL_ALIGNMENT_LEFT, -1, KEY_FONT_SIZE, color)
