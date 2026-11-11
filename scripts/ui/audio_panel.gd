class_name AudioPanel
extends Control
## The audio settings: a volume slider and a mute switch for each bus (master, music, effects,
## interface, voices). Changes apply at once and are saved (see AudioSettings). Opened from the main
## menu and from a run (O); Esc or Close shuts it.

signal closed

const SLIDER_WIDTH := 360.0
## A sound to hear while setting a bus, so the player can judge the level.
const PREVIEW: Dictionary[StringName, StringName] = {
	&"Master": &"ui_confirm", &"Sfx": &"impact_earth", &"Ui": &"ui_click",
}

## Bus name -> its slider, its percent label and its mute switch.
var sliders: Dictionary[StringName, HSlider] = {}
var mutes: Dictionary[StringName, CheckButton] = {}
var _percent: Dictionary[StringName, Label] = {}


func _init() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	process_mode = Node.PROCESS_MODE_ALWAYS
	theme = UiStyle.make_theme()
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.55)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.panel_box(30, 24))
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 14)
	panel.add_child(column)
	column.add_child(UiStyle.label("Audio", 34))
	column.add_child(UiStyle.label("Saved as you change it. M mutes everything during a run.", 17, UiStyle.TEXT_DIM))
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 18)
	grid.add_theme_constant_override("v_separation", 12)
	column.add_child(grid)
	for entry in AudioSettings.BUSES:
		_add_row(grid, entry[0], entry[1])
	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", 12)
	buttons.alignment = BoxContainer.ALIGNMENT_END
	column.add_child(buttons)
	var reset := UiStyle.button("Reset", 20)
	reset.custom_minimum_size = Vector2(150, 48)
	reset.pressed.connect(_reset)
	buttons.add_child(reset)
	var close := UiStyle.button("Close (Esc)", 20)
	close.custom_minimum_size = Vector2(190, 48)
	close.pressed.connect(close_panel)
	buttons.add_child(close)


func _add_row(grid: GridContainer, bus: StringName, title: String) -> void:
	var name_label := UiStyle.label(title, 21)
	name_label.custom_minimum_size = Vector2(250, 0)
	name_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	grid.add_child(name_label)
	var slider := HSlider.new()
	slider.min_value = 0
	slider.max_value = 100
	slider.step = 5
	slider.focus_mode = Control.FOCUS_NONE
	slider.custom_minimum_size = Vector2(SLIDER_WIDTH, 36)
	slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	slider.value = roundf(AudioSettings.volume(bus) * 100.0)
	slider.value_changed.connect(func(value: float) -> void: _on_volume(bus, value))
	slider.drag_ended.connect(func(_changed: bool) -> void: _preview(bus))
	grid.add_child(slider)
	sliders[bus] = slider
	var percent := UiStyle.label("", 20, UiStyle.TEXT_DIM)
	percent.custom_minimum_size = Vector2(64, 0)
	percent.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	percent.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	grid.add_child(percent)
	_percent[bus] = percent
	var mute := CheckButton.new()
	mute.text = "Mute"
	mute.focus_mode = Control.FOCUS_NONE
	mute.add_theme_font_size_override("font_size", 19)
	mute.button_pressed = AudioSettings.is_muted(bus)
	mute.toggled.connect(func(on: bool) -> void: _on_mute(bus, on))
	grid.add_child(mute)
	mutes[bus] = mute
	_show(bus)


func _on_volume(bus: StringName, value: float) -> void:
	AudioSettings.set_volume(bus, value / 100.0)
	_show(bus)


func _on_mute(bus: StringName, on: bool) -> void:
	AudioSettings.set_muted(bus, on)
	_show(bus)
	if not on:
		_preview(bus)


func _preview(bus: StringName) -> void:
	if PREVIEW.has(bus):
		SoundPlayer.sfx(PREVIEW[bus])


func _show(bus: StringName) -> void:
	var muted := AudioSettings.is_muted(bus)
	_percent[bus].text = "off" if muted else "%d%%" % roundi(AudioSettings.volume(bus) * 100.0)
	sliders[bus].modulate.a = 0.45 if muted else 1.0


## Shows the saved settings again (after M was pressed while the panel was shut, say).
func refresh() -> void:
	for bus: StringName in sliders.keys():
		sliders[bus].set_value_no_signal(roundf(AudioSettings.volume(bus) * 100.0))
		mutes[bus].set_pressed_no_signal(AudioSettings.is_muted(bus))
		_show(bus)


func _reset() -> void:
	AudioSettings.reset_to_defaults()
	refresh()


func close_panel() -> void:
	hide()
	closed.emit()


func _input(event: InputEvent) -> void:
	if not visible:
		return
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode in [KEY_ESCAPE, KEY_O]:
		get_viewport().set_input_as_handled()
		close_panel()
