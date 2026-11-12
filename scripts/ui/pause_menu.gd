class_name PauseMenu
extends Control
## The menu Esc opens during a run: resume, save or load a game (Game opens Saved games over it),
## exit to the main menu, exit to the campaign map (in a campaign stage), the audio settings, or quit
## to the desktop. The run waits while it is open
## (Game pauses it). Leaving a run that is still going asks once first, because the run is lost;
## Enter confirms and Esc steps back.

signal resume_requested
signal audio_requested
## Save game or Load game: `mode` is &"save" or &"load".
signal saves_requested(mode: StringName)
## `scene` is &"menu", &"campaign" or &"quit".
signal leave_requested(scene: StringName)

const BUTTON_SIZE := Vector2(420, 62)
const LEAVE_TEXT: Dictionary[StringName, String] = {
	&"menu": "Exit to the main menu?",
	&"campaign": "Exit to the campaign map?",
	&"quit": "Quit to the desktop?",
}
## The confirm button for each way out.
const LEAVE_BUTTON: Dictionary[StringName, String] = {
	&"menu": "Exit to main menu  (Enter)",
	&"campaign": "Exit to campaign map  (Enter)",
	&"quit": "Quit to desktop  (Enter)",
}

var resume_button: Button
var save_button: Button
var load_button: Button
var audio_button: Button
var fullscreen_button: Button
var campaign_button: Button
var menu_button: Button
var quit_button: Button
var leave_button: Button
var stay_button: Button
## The leaving choice waiting for "Leave" or "Stay", or empty.
var pending: StringName = &""
## Set by Game when the menu opens: leaving needs no second press once the run is over.
var run_is_over := false

var _subtitle: Label
var _choices: VBoxContainer
var _confirm: VBoxContainer
var _confirm_title: Label


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = UiStyle.make_theme()
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.6)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.panel_box(44, 32))
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 14)
	panel.add_child(column)
	var title := UiStyle.label("Paused", 52)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(title)
	_subtitle = UiStyle.label("", 19, UiStyle.TEXT_DIM)
	_subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(_subtitle)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 6)
	column.add_child(gap)

	_choices = VBoxContainer.new()
	_choices.add_theme_constant_override("separation", 12)
	column.add_child(_choices)
	resume_button = _add_button(_choices, "Resume  (Esc)", func() -> void: resume_requested.emit())
	save_button = _add_button(_choices, "Save game  (S)", func() -> void: saves_requested.emit(&"save"))
	load_button = _add_button(_choices, "Load game  (L)", func() -> void: saves_requested.emit(&"load"))
	menu_button = _add_button(_choices, "Exit to main menu", func() -> void: ask_to_leave(&"menu"))
	campaign_button = _add_button(_choices, "Exit to campaign map", func() -> void: ask_to_leave(&"campaign"))
	audio_button = _add_button(_choices, "Audio settings  (O)", func() -> void: audio_requested.emit())
	fullscreen_button = _add_button(_choices, VideoSettings.toggle_text(), VideoSettings.toggle_fullscreen)
	FullscreenKey.watch(_show_fullscreen)
	quit_button = _add_button(_choices, "Quit to desktop", func() -> void: ask_to_leave(&"quit"))

	_confirm = VBoxContainer.new()
	_confirm.add_theme_constant_override("separation", 12)
	_confirm.hide()
	column.add_child(_confirm)
	_confirm_title = UiStyle.label("", 28)
	_confirm_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_confirm.add_child(_confirm_title)
	var warning := UiStyle.label("This run will be lost. Your campaign progress and talents are kept.", 19,
			UiStyle.TEXT_DIM)
	warning.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	warning.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	warning.custom_minimum_size = Vector2(BUTTON_SIZE.x, 0)
	_confirm.add_child(warning)
	leave_button = _add_button(_confirm, "", confirm)
	leave_button.add_theme_color_override("font_color", UiStyle.BAD)
	leave_button.add_theme_color_override("font_hover_color", UiStyle.LIFE)
	stay_button = _add_button(_confirm, "Stay  (Esc)", back)


func _add_button(column: VBoxContainer, text: String, action: Callable) -> Button:
	var button := UiStyle.button(text, 26)
	button.custom_minimum_size = BUTTON_SIZE
	button.pressed.connect(action)
	column.add_child(button)
	return button


## Shows the menu. `where` names the map or stage under the title; `in_campaign` adds the
## campaign map button.
func open(where: String, in_campaign: bool, over: bool) -> void:
	_subtitle.text = where
	_subtitle.visible = not where.is_empty()
	campaign_button.visible = in_campaign
	run_is_over = over
	_show_fullscreen()
	back()
	show()


func _show_fullscreen(_on: bool = false) -> void:
	fullscreen_button.text = VideoSettings.toggle_text()


func ask_to_leave(scene: StringName) -> void:
	if run_is_over:
		_leave(scene)
		return
	pending = scene
	_confirm_title.text = LEAVE_TEXT[scene]
	leave_button.text = LEAVE_BUTTON[scene]
	_choices.hide()
	_confirm.show()


## Steps back from the "are you sure" question to the menu.
func back() -> void:
	pending = &""
	_confirm.hide()
	_choices.show()


func is_confirming() -> bool:
	return not pending.is_empty()


## "Yes, leave": goes the way that was asked about.
func confirm() -> void:
	if is_confirming():
		_leave(pending)


func _leave(scene: StringName) -> void:
	pending = &""
	leave_requested.emit(scene)
