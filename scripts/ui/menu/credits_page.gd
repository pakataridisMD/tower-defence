class_name CreditsPage
extends MenuPage
## Credits: who made the game and the free fonts and tools it uses.

## The studio that made the game (a working name for now) and its two makers, equal partners.
## Shown here and on the Settings page.
const DEVELOPER := "Pasiv Production"
const MAKERS := "Doctor Paris and Thanos"

const LINES: Array[Array] = [
	["DEVELOPED BY", [DEVELOPER]],
	["A GAME BY", [MAKERS]],
	["STORY", ["The War of Seven Crowns"]],
	["NARRATOR", ["Elariel (ElevenLabs)"]],
	["MUSIC AND SOUND", ["Original score and effects"]],
	["FONTS (SIL OPEN FONT LICENSE)", ["Pirata One, Jersey 10, Pixelify Sans, Silkscreen"]],
	["ENGINE", ["Godot Engine (MIT licence)"]],
]


func _init() -> void:
	super("Credits")
	var panel := add_panel(Vector2(412, 0), Vector2(1000, 852))
	var column := VBoxContainer.new()
	column.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_theme_constant_override("separation", 6)
	panel.add_child(column)
	for block: Array in LINES:
		var heading := UiStyle.menu_label(block[0], "small", 16, UiStyle.MENU_GOLD)
		heading.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		column.add_child(heading)
		for line: String in block[1]:
			var text := UiStyle.menu_label(line, "button", 40)
			text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			column.add_child(text)
		var gap := Control.new()
		gap.custom_minimum_size = Vector2(0, 22)
		column.add_child(gap)
	var thanks := UiStyle.menu_title("Thank you for holding the road.", 56)
	thanks.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(thanks)
