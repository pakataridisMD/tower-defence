class_name VideoSettings
extends RefCounted
## The player's window mode and v-sync, kept in user://settings.cfg next to the audio settings and
## applied when the menu first opens. Bot and test runs keep them in memory and never touch the
## window.

const SECTION := "video"
const MODES: Array[String] = ["Fullscreen", "Windowed"]

static var fullscreen := true
static var vsync := true
static var _loaded := false


static func load_saved() -> void:
	if _loaded:
		return
	_loaded = true
	if not AudioSettings.persist:
		return
	var file := ConfigFile.new()
	if file.load(AudioSettings.path) == OK:
		fullscreen = bool(file.get_value(SECTION, "fullscreen", fullscreen))
		vsync = bool(file.get_value(SECTION, "vsync", vsync))
	apply()


static func set_fullscreen(on: bool) -> void:
	fullscreen = on
	apply()
	save()


static func set_vsync(on: bool) -> void:
	vsync = on
	apply()
	save()


static func apply() -> void:
	if not AudioSettings.persist or DisplayServer.get_name() == "headless":
		return
	DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
	DisplayServer.window_set_vsync_mode(DisplayServer.VSYNC_ENABLED if vsync else DisplayServer.VSYNC_DISABLED)


static func save() -> void:
	if not AudioSettings.persist:
		return
	var file := ConfigFile.new()
	file.load(AudioSettings.path)  # Keep the audio section.
	file.set_value(SECTION, "fullscreen", fullscreen)
	file.set_value(SECTION, "vsync", vsync)
	file.save(AudioSettings.path)
