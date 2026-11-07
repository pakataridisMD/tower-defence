extends GutTest
## Saving and loading the player profile. Every test works in its own folder under user://, never
## on the real save.

const DIR := "user://test_saves"

var path := DIR.path_join("save.json")


func before_each() -> void:
	_remove_files()
	DirAccess.make_dir_recursive_absolute(DIR)


func after_all() -> void:
	_remove_files()
	DirAccess.remove_absolute(DIR)


func _remove_files() -> void:
	if not DirAccess.dir_exists_absolute(DIR):
		return
	for file in DirAccess.get_files_at(DIR):
		DirAccess.remove_absolute(DIR.path_join(file))


func _profile(points: int = 12) -> PlayerProfile:
	var profile := PlayerProfile.new()
	profile.meta_points_earned = points
	profile.meta_nodes = [&"command_gold", &"command_lives"]
	profile.runs_played = 3
	profile.runs_won = 1
	profile.best_waves = 10
	profile.enemies_killed = 250
	profile.last_map = &"serpentine"
	profile.last_difficulty = &"hard"
	return profile


func _write(file_path: String, text: String) -> void:
	var file := FileAccess.open(file_path, FileAccess.WRITE)
	file.store_string(text)
	file.close()


func test_a_saved_profile_loads_back_the_same() -> void:
	assert_eq(SaveFile.save_profile(_profile(), path), OK)
	assert_eq(SaveFile.load_profile(path).to_dict(), _profile().to_dict())
	assert_file_does_not_exist(path + ".tmp")


func test_the_save_is_versioned_json() -> void:
	SaveFile.save_profile(_profile(), path)
	var saved: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	assert_true(saved is Dictionary)
	assert_eq(int(saved["version"]), PlayerProfile.VERSION)
	assert_eq(int(saved["meta_points_earned"]), 12)


func test_the_previous_save_is_kept_as_a_backup() -> void:
	SaveFile.save_profile(_profile(5), path)
	SaveFile.save_profile(_profile(9), path)
	assert_eq(SaveFile.load_profile(path).meta_points_earned, 9)
	assert_eq(SaveFile.load_profile(path + ".bak").meta_points_earned, 5)


func test_a_damaged_save_falls_back_to_the_backup_and_is_kept_aside() -> void:
	SaveFile.save_profile(_profile(5), path)
	SaveFile.save_profile(_profile(9), path)
	_write(path, "{\"meta_points_earned\": 9, \"meta_no")
	assert_eq(SaveFile.load_profile(path).meta_points_earned, 5, "loads the backup")
	assert_file_exists(path + ".corrupt")
	assert_eq(FileAccess.get_file_as_string(path + ".corrupt"), "{\"meta_points_earned\": 9, \"meta_no")


func test_a_missing_or_empty_save_starts_fresh() -> void:
	assert_eq(SaveFile.load_profile(path).to_dict(), PlayerProfile.new().to_dict())
	_write(path, "")
	assert_eq(SaveFile.load_profile(path).to_dict(), PlayerProfile.new().to_dict())


func test_malformed_fields_fall_back_to_defaults() -> void:
	_write(path, JSON.stringify({
		"version": 1,
		"meta_points_earned": -4,
		"meta_nodes": [3, "command_gold", "", null],
		"stats": ["not", "a", "dictionary"],
		"last_map": 7,
		"last_difficulty": "hard",
	}))
	var profile := SaveFile.load_profile(path)
	assert_eq(profile.meta_points_earned, 0, "negative points are not allowed")
	var nodes: Array[StringName] = [&"command_gold"]
	assert_eq(profile.meta_nodes, nodes)
	assert_eq(profile.runs_played, 0)
	assert_eq(profile.last_map, &"")
	assert_eq(profile.last_difficulty, &"hard")
