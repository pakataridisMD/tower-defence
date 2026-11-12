class_name FullscreenKey
extends Node
## Autoload: switches between full screen and a window from anywhere in the game (title screen,
## a run, the campaign map, a cutscene, paused or not). Keys: F11, Alt+Enter, and on a Mac the
## usual Cmd+Ctrl+F. It also watches the window, so a change made with the Mac's green button is
## kept in the settings, and tells toggle buttons to update their text through `changed`.

signal changed(fullscreen: bool)

static var _instance: FullscreenKey


func _enter_tree() -> void:
	_instance = self
	process_mode = Node.PROCESS_MODE_ALWAYS


func _ready() -> void:
	get_window().size_changed.connect(_on_window_resized)


func _exit_tree() -> void:
	if _instance == self:
		_instance = null


## Tells listeners the mode changed (VideoSettings calls this after every switch).
static func changed_now() -> void:
	if _instance != null:
		_instance.changed.emit(VideoSettings.fullscreen)


## Connects a listener to `changed`, if the autoload is running.
static func watch(listener: Callable) -> void:
	if _instance != null and not _instance.changed.is_connected(listener):
		_instance.changed.connect(listener)


static func is_toggle_key(event: InputEvent) -> bool:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return false
	match key.keycode:
		KEY_F11:
			return true
		KEY_ENTER, KEY_KP_ENTER:
			return key.alt_pressed and not key.ctrl_pressed and not key.meta_pressed
		KEY_F:
			return key.meta_pressed and key.ctrl_pressed
	return false


func _input(event: InputEvent) -> void:
	if is_toggle_key(event):
		get_viewport().set_input_as_handled()
		VideoSettings.toggle_fullscreen()


func _on_window_resized() -> void:
	if VideoSettings.sync_from_window():
		changed.emit(VideoSettings.fullscreen)
