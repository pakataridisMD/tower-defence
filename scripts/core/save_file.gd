class_name SaveFile
extends RefCounted
## Reads and writes the player profile as JSON.
##
## A save is written to a temporary file first and then moved into place, and the previous save is
## kept as a .bak copy, so a crash halfway through writing never loses progress. A save that cannot
## be read is copied to .corrupt, so it is not overwritten, and the backup is loaded instead.


## Loads the profile at `path`, falling back to the backup, then to a fresh profile.
static func load_profile(path: String) -> PlayerProfile:
	if FileAccess.file_exists(path):
		var data: Variant = _read_json(path)
		if data is Dictionary:
			return PlayerProfile.from_dict(data)
		push_warning("The save at %s could not be read. A copy is kept at %s.corrupt." % [path, path])
		DirAccess.copy_absolute(path, path + ".corrupt")
	var backup := path + ".bak"
	if FileAccess.file_exists(backup):
		var data: Variant = _read_json(backup)
		if data is Dictionary:
			return PlayerProfile.from_dict(data)
	return PlayerProfile.new()


static func save_profile(profile: PlayerProfile, path: String) -> Error:
	DirAccess.make_dir_recursive_absolute(path.get_base_dir())
	var temp := path + ".tmp"
	var file := FileAccess.open(temp, FileAccess.WRITE)
	if file == null:
		return FileAccess.get_open_error()
	file.store_string(JSON.stringify(profile.to_dict(), "\t"))
	file.close()
	var backup := path + ".bak"
	if FileAccess.file_exists(path):
		if FileAccess.file_exists(backup):
			DirAccess.remove_absolute(backup)
		var moved := DirAccess.rename_absolute(path, backup)
		if moved != OK:
			return moved
	return DirAccess.rename_absolute(temp, path)


## The parsed JSON in a file, or null if the file is empty or not valid JSON.
static func _read_json(path: String) -> Variant:
	var text := FileAccess.get_file_as_string(path)
	if text.strip_edges().is_empty():
		return null
	var json := JSON.new()
	if json.parse(text) != OK:
		return null
	return json.data
