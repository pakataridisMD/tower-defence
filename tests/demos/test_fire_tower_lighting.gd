extends GutTest
## The lighting art test builds its world from the generated art and layout, and keeps running.

const SCENE := preload("res://scenes/demos/fire_tower_lighting.tscn")

var demo: FireTowerLighting


func before_each() -> void:
	demo = SCENE.instantiate()
	add_child_autofree(demo)
	await wait_process_frames(3)


func test_layout_has_a_road_and_props() -> void:
	var layout: Variant = JSON.parse_string(FileAccess.get_file_as_string(FireTowerLighting.ART + "layout.json"))
	assert_true(layout is Dictionary, "layout.json parses")
	assert_gt((layout["road"] as Array).size(), 20, "the road has enough points to follow")
	assert_gt((layout["props"] as Array).size(), 50, "the field is dressed with props")


func test_slimes_walk_the_road() -> void:
	var before: Array[Vector2] = []
	for slime in demo._slimes:
		before.append(slime.sprite.position)
	await wait_seconds(0.5)
	var moved := 0
	for i in demo._slimes.size():
		if demo._slimes[i].sprite.position != before[i]:
			moved += 1
	assert_eq(demo._slimes.size(), 4)
	assert_gt(moved, 0, "slimes move along the road")


func test_time_of_day_keys_set_the_mood() -> void:
	demo._jump(FireTowerLighting.DAY)
	demo._apply_time()
	var day_ambient := demo._ambient.color
	assert_almost_eq(demo._night(), 0.0, 0.01)
	demo._jump(FireTowerLighting.NIGHT)
	demo._apply_time()
	assert_almost_eq(demo._night(), 1.0, 0.01)
	assert_lt(demo._ambient.color.v, day_ambient.v, "night is darker than day")
	assert_gt(demo._sun.energy, -0.01)
	assert_almost_eq(demo._sun.energy, 0.0, 0.01, "the sun is off at night")


func test_the_tower_fires_at_slimes_in_range() -> void:
	# Put a slime right next to the tower and let the tower shoot it.
	var slime: FireTowerLighting.Slime = demo._slimes[0]
	slime.sprite.position = demo._tower_base + Vector2(40, 10)
	demo._shot_timer = 0.0
	demo._update_tower(0.016)
	assert_gt(demo._shot_timer, 0.5, "the tower reloads after firing")
