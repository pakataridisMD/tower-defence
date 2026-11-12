class_name SettingsPage
extends MenuPage
## Settings: Sound (a volume slider and mute switch for every bus, as in the in-run audio panel,
## and the title screen's music on or off) and Video (window mode and v-sync). Every change applies and saves at once. The studio's
## name sits at the right of the tab row.

const TABS: Array[String] = ["Sound", "Video"]

var tab := 0
var sliders: Dictionary[StringName, HSlider] = {}
var mutes: Dictionary[StringName, CheckBox] = {}
var _percent: Dictionary[StringName, Label] = {}
var _sections: Array[Control] = []
var _tab_buttons: Array[Button] = []
var developer_label: Label
## Turns the title screen's music on and off (on when pressed).
var menu_music: CheckBox


func _init() -> void:
	super("Settings")
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 8)
	body.add_child(tabs)
	var group := ButtonGroup.new()
	for i in TABS.size():
		var b := UiStyle.menu_choice(TABS[i], group, 40)
		b.custom_minimum_size = Vector2(240, 56)
		b.button_pressed = i == 0
		var index := i
		b.toggled.connect(func(on: bool) -> void:
			if on:
				show_tab(index))
		tabs.add_child(b)
		_tab_buttons.append(b)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tabs.add_child(spacer)
	developer_label = UiStyle.menu_label(
			"Developed by %s  (%s)" % [CreditsPage.DEVELOPER, CreditsPage.MAKERS], "small", 16, UiStyle.MENU_GOLD)
	developer_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	tabs.add_child(developer_label)
	var panel := add_panel(Vector2(0, 68), Vector2(1824, 784))
	var stack := Control.new()
	panel.add_child(stack)
	_sections.append(_sound())
	_sections.append(_video())
	for section in _sections:
		stack.add_child(section)
	show_tab(0)


func show_tab(index: int) -> void:
	tab = index
	for i in _tab_buttons.size():
		_tab_buttons[i].set_pressed_no_signal(i == index)
	for i in _sections.size():
		_sections[i].visible = i == index


func refresh() -> void:
	for bus: StringName in sliders.keys():
		sliders[bus].set_value_no_signal(roundf(AudioSettings.volume(bus) * 100.0))
		mutes[bus].set_pressed_no_signal(AudioSettings.is_muted(bus))
		_show(bus)
	menu_music.set_pressed_no_signal(AudioSettings.menu_music_on())


func _sound() -> Control:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 14)
	column.add_child(UiStyle.menu_label("VOLUME", "small", 16, UiStyle.MENU_GOLD))
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 32)
	grid.add_theme_constant_override("v_separation", 18)
	column.add_child(grid)
	for entry in AudioSettings.BUSES:
		var bus: StringName = entry[0]
		grid.add_child(UiStyle.menu_label(entry[1], "button", 40))
		var slider := HSlider.new()
		slider.min_value = 0
		slider.max_value = 100
		slider.step = 5
		slider.focus_mode = Control.FOCUS_NONE
		slider.custom_minimum_size = Vector2(620, 40)
		slider.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		_style_slider(slider)
		slider.value = roundf(AudioSettings.volume(bus) * 100.0)
		slider.value_changed.connect(func(value: float) -> void:
			AudioSettings.set_volume(bus, value / 100.0)
			_show(bus))
		grid.add_child(slider)
		sliders[bus] = slider
		var percent := UiStyle.menu_label("", "button", 40, UiStyle.MENU_GOLD_LIGHT)
		percent.custom_minimum_size = Vector2(110, 0)
		grid.add_child(percent)
		_percent[bus] = percent
		var mute := UiStyle.menu_switch()
		mute.custom_minimum_size = Vector2(160, 56)
		mute.text = "Mute"
		mute.focus_mode = Control.FOCUS_NONE
		mute.button_pressed = AudioSettings.is_muted(bus)
		mute.toggled.connect(func(on: bool) -> void:
			AudioSettings.set_muted(bus, on)
			_show(bus))
		grid.add_child(mute)
		mutes[bus] = mute
		_show(bus)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 10)
	column.add_child(gap)
	column.add_child(UiStyle.menu_label("MUSIC", "small", 16, UiStyle.MENU_GOLD))
	menu_music = UiStyle.menu_switch()
	menu_music.text = "Menu music (plays on the title screen)"
	menu_music.focus_mode = Control.FOCUS_NONE
	menu_music.button_pressed = AudioSettings.menu_music_on()
	menu_music.toggled.connect(AudioSettings.set_menu_music)
	column.add_child(menu_music)
	return column


func _video() -> Control:
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 20)
	column.add_child(UiStyle.menu_label("DISPLAY", "small", 16, UiStyle.MENU_GOLD))
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	var label := UiStyle.menu_label("Window", "button", 40)
	label.custom_minimum_size = Vector2(240, 0)
	row.add_child(label)
	var group := ButtonGroup.new()
	for i in VideoSettings.MODES.size():
		var b := UiStyle.menu_choice(VideoSettings.MODES[i], group, 40)
		b.custom_minimum_size = Vector2(260, 56)
		b.button_pressed = (i == 0) == VideoSettings.fullscreen
		var full := i == 0
		b.toggled.connect(func(on: bool) -> void:
			if on:
				VideoSettings.set_fullscreen(full))
		row.add_child(b)
	column.add_child(row)
	var vsync := UiStyle.menu_switch()
	vsync.text = "V-Sync (no tearing; caps the frame rate to the screen)"
	vsync.focus_mode = Control.FOCUS_NONE
	vsync.button_pressed = VideoSettings.vsync
	vsync.toggled.connect(VideoSettings.set_vsync)
	column.add_child(vsync)
	return column


func _show(bus: StringName) -> void:
	var muted := AudioSettings.is_muted(bus)
	_percent[bus].text = "Off" if muted else "%d%%" % roundi(AudioSettings.volume(bus) * 100.0)
	sliders[bus].modulate.a = 0.45 if muted else 1.0


## A gold groove with a stone-and-gold knob, to match the frames.
static func _style_slider(slider: HSlider) -> void:
	var groove := StyleBoxFlat.new()
	groove.bg_color = Color("0f0c15")
	groove.border_color = UiStyle.MENU_INK
	groove.set_border_width_all(2)
	groove.content_margin_top = 6
	groove.content_margin_bottom = 6
	slider.add_theme_stylebox_override("slider", groove)
	var fill := StyleBoxFlat.new()
	fill.bg_color = UiStyle.MENU_GOLD
	fill.border_color = UiStyle.MENU_INK
	fill.set_border_width_all(2)
	fill.border_width_top = 2
	fill.content_margin_top = 6
	fill.content_margin_bottom = 6
	slider.add_theme_stylebox_override("grabber_area", fill)
	slider.add_theme_stylebox_override("grabber_area_highlight", fill)
	var knob := Image.create(20, 32, false, Image.FORMAT_RGBA8)
	knob.fill(UiStyle.MENU_INK)
	knob.fill_rect(Rect2i(2, 2, 16, 28), Color("776a8a"))
	knob.fill_rect(Rect2i(6, 6, 8, 20), UiStyle.MENU_GOLD)
	knob.fill_rect(Rect2i(6, 6, 6, 6), UiStyle.MENU_GOLD_LIGHT)
	var tex := ImageTexture.create_from_image(knob)
	slider.add_theme_icon_override("grabber", tex)
	slider.add_theme_icon_override("grabber_highlight", tex)
