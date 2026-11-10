class_name BoardView
extends Node2D
## Shows the run simulation on the board and handles clicks on it: placing towers and selecting them.
##
## The map, towers, enemies, shots and impacts are drawn as lit pixel art by a BoardArt child when the
## map has art. This node draws the overlays on top (ranges, health bars, the build cursor, gold
## text), unshaded so night never darkens them, and falls back to placeholder shapes for anything
## without art.

signal selection_changed(tower: SimTower)
signal placement_failed(reason: String)
## The player clicked the board while aiming a skill.
signal skill_aimed(skill_id: StringName, at: Vector2)

const GROUND := Color("243042")
const GROUND_ALT := Color("273447")
const GRID_LINE := Color(1, 1, 1, 0.035)
const PATH_FILL := Color("7d6a4b")
const PATH_EDGE := Color("5c4d36")
const PATH_ARROW := Color(0, 0, 0, 0.2)
## Gap between the arrows that show which way enemies walk.
const PATH_ARROW_SPACING := 96.0
const VALID := Color(0.42, 0.86, 0.54, 0.35)
const INVALID := Color(1.0, 0.42, 0.42, 0.35)
const ENEMY_BODY := Color("dfe3ea")
const ENEMY_OUTLINE := Color("141821")
const TOWER_BASE := Color("161b26")
const TOWER_HALF_SIZE := 24.0

var sim: RunSim
## Tower id being placed, or empty.
var placing: StringName = &""
## Skill id being aimed, or empty.
var aiming: StringName = &""
var selected: SimTower
var hover_cell := Vector2i(-1, -1)
## Where the mouse last was, in board pixels.
var _mouse := Vector2(-1, -1)

var _effects: Array[Effect] = []
var _font: Font
## The ground and path never change during a run, so they are drawn once on their own layer.
## Only used when the map has no art.
var _ground: Node2D
## The lit pixel art, or null when the map has no art.
var art: BoardArt


## A short-lived visual: a lightning arc, an explosion, floating gold text or a leak flash.
class Effect:
	var kind: StringName
	var time := 0.0
	var duration := 0.3
	var position := Vector2.ZERO
	var points := PackedVector2Array()
	var radius := 0.0
	var color := Color.WHITE
	var text := ""


func setup(p_sim: RunSim) -> void:
	sim = p_sim
	_font = ThemeDB.fallback_font
	var overlay := CanvasItemMaterial.new()
	overlay.light_mode = CanvasItemMaterial.LIGHT_MODE_UNSHADED
	material = overlay
	texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	if BoardArt.has_ground(sim.config.map.id):
		art = BoardArt.new()
		art.show_behind_parent = true
		add_child(art)
		art.setup(sim)
	else:
		_ground = Node2D.new()
		_ground.show_behind_parent = true
		_ground.draw.connect(_draw_ground_layer)
		add_child(_ground)
	sim.chain_fired.connect(_on_chain_fired)
	sim.projectile_landed.connect(_on_projectile_landed)
	sim.enemy_killed.connect(_on_enemy_killed)
	sim.enemy_leaked.connect(_on_enemy_leaked)
	sim.skill_used.connect(_on_skill_used)


func begin_placing(tower_id: StringName) -> void:
	aiming = &""
	placing = tower_id
	select(null)


func cancel_placing() -> void:
	placing = &""


func select(tower: SimTower) -> void:
	if selected == tower:
		return
	selected = tower
	selection_changed.emit(tower)


## Starts aiming a skill: the cursor shows its reach and the next click on the board casts it.
func begin_aiming(skill_id: StringName) -> void:
	placing = &""
	aiming = skill_id


func cancel_aiming() -> void:
	aiming = &""


## Where the mouse is on the board, kept inside it.
func mouse_point() -> Vector2:
	return _mouse.clamp(Vector2.ZERO, sim.config.map.size_in_pixels())


## True while the mouse is over the board.
func mouse_inside() -> bool:
	return Rect2(Vector2.ZERO, sim.config.map.size_in_pixels()).has_point(_mouse)


## Follows the mouse from its events, so the cursor is right however the events arrive.
func _input(event: InputEvent) -> void:
	if event is InputEventMouse:
		_mouse = (make_input_local(event) as InputEventMouse).position


func _process(delta: float) -> void:
	var active: Array[Effect] = []
	for effect in _effects:
		effect.time += delta
		if effect.time < effect.duration:
			active.append(effect)
	_effects = active
	if selected != null and not sim.towers.has(selected):
		select(null)
	hover_cell = sim.config.map.cell_at(_mouse)
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	var click := event as InputEventMouseButton
	if click == null or not click.pressed:
		return
	var map := sim.config.map
	var at := (make_input_local(click) as InputEventMouseButton).position
	var cell := map.cell_at(at)
	if not map.is_inside(cell):
		return
	if not aiming.is_empty():
		if click.button_index == MOUSE_BUTTON_LEFT:
			skill_aimed.emit(aiming, at)
		elif click.button_index == MOUSE_BUTTON_RIGHT:
			cancel_aiming()
		get_viewport().set_input_as_handled()
		return
	if click.button_index == MOUSE_BUTTON_LEFT:
		if placing.is_empty():
			select(sim.tower_at(cell))
		else:
			var error := sim.placement_error(placing, cell)
			if error.is_empty():
				sim.place_tower(placing, cell)
				if not click.shift_pressed:
					cancel_placing()
			else:
				placement_failed.emit(error)
		get_viewport().set_input_as_handled()
	elif click.button_index == MOUSE_BUTTON_RIGHT:
		cancel_placing()
		select(null)
		get_viewport().set_input_as_handled()


# --- Drawing -----------------------------------------------------------------

func _draw() -> void:
	if sim == null:
		return
	for tower in sim.towers:
		if not _has_tower_art(tower.data.id):
			_draw_tower(tower.data, tower.position, 1.0)
	for tower in sim.towers:
		_draw_level(tower)
	if selected != null:
		_draw_range(selected.position, selected.attack_range, Color(1, 1, 1, 0.55))
		if selected.aura_radius > 0.0 and selected.aura_damage > 0.0:
			_draw_range(selected.position, selected.aura_radius, Color(0.75, 0.5, 1.0, 0.5))
	for enemy in sim.enemies:
		_draw_enemy(enemy)
	if art == null:
		for shot in sim.projectiles:
			var radius := 7.0 if shot.splash_radius > 0.0 else 4.0
			draw_circle(shot.position, radius, _tower_color(shot.source.data, 0))
	else:
		_draw_road_labels()
	_draw_effects()
	_draw_cursor()


## Small gems under a tower: one per level above the first, gold once it has ascended.
func _draw_level(tower: SimTower) -> void:
	var gems := tower.level - 1 + (1 if tower.ascendancy != null else 0)
	if gems <= 0:
		return
	var y := tower.position.y + 26.0
	var start := tower.position.x - (gems - 1) * 6.0
	for i in gems:
		var gold := tower.ascendancy != null and i == gems - 1
		var c := Vector2(start + i * 12.0, y)
		var gem := PackedVector2Array([c + Vector2(0, -5), c + Vector2(4, 0), c + Vector2(0, 5), c + Vector2(-4, 0)])
		draw_colored_polygon(gem, Color(0.1, 0.08, 0.12, 0.9))
		var inner := PackedVector2Array([c + Vector2(0, -3.5), c + Vector2(2.6, 0), c + Vector2(0, 3.5), c + Vector2(-2.6, 0)])
		draw_colored_polygon(inner, Color(1.0, 0.82, 0.3) if gold else Color(0.75, 0.92, 1.0))


func _has_tower_art(tower_id: StringName) -> bool:
	return art != null and not BoardArt.tower_info(tower_id).is_empty()


func _draw_road_labels() -> void:
	for lane in sim.config.map.lane_count():
		var ends := _road_ends(lane)
		if ends.is_empty():
			continue
		var exit_label := lane == 0 or ends[1].distance_to(_road_ends(0)[1]) > 1.0
		_draw_outlined(ends[0], "IN", UiStyle.TEXT)
		if exit_label:
			_draw_outlined(ends[1], "OUT", UiStyle.LIFE)


## Where to write IN and OUT for a lane: just inside the board where the road enters and leaves.
## Empty when the lane has fewer than two points.
func _road_ends(lane: int) -> PackedVector2Array:
	var points := sim.config.map.path_points(lane)
	if points.size() < 2:
		return PackedVector2Array()
	var size := sim.config.map.size_in_pixels()
	var cell_size := float(sim.config.map.cell_size)
	var result := PackedVector2Array()
	for point in [points[0], points[points.size() - 1]]:
		var at := Vector2(clampf(point.x, 6.0, size.x - 44.0), clampf(point.y, cell_size, size.y - 8.0))
		result.append(at + Vector2(0, -cell_size * 0.5 - 6) if point.y > 0 and point.y < size.y else at + Vector2(cell_size * 0.5 + 4, 0))
	return result


func _draw_outlined(at: Vector2, text: String, color: Color) -> void:
	draw_string_outline(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, 6, Color(0, 0, 0, 0.6))
	draw_string(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, color)


func _draw_ground_layer() -> void:
	var map := sim.config.map
	var cell_size := float(map.cell_size)
	var board := Rect2(Vector2.ZERO, map.size_in_pixels())
	_ground.draw_rect(board, GROUND)
	for x in map.grid_size.x:
		for y in map.grid_size.y:
			if (x + y) % 2 == 0:
				_ground.draw_rect(Rect2(Vector2(x, y) * cell_size, Vector2(cell_size, cell_size)), GROUND_ALT)
	for x in range(1, map.grid_size.x):
		_ground.draw_line(Vector2(x * cell_size, 0), Vector2(x * cell_size, board.size.y), GRID_LINE)
	for y in range(1, map.grid_size.y):
		_ground.draw_line(Vector2(0, y * cell_size), Vector2(board.size.x, y * cell_size), GRID_LINE)

	# Path: an edge drawn slightly larger than each cell, then the fill on top, so neighbouring
	# cells join into one road with a border only on the outside.
	var cells := sim.path_cell_list()
	for cell in cells:
		var rect := Rect2(Vector2(cell) * cell_size, Vector2(cell_size, cell_size))
		_ground.draw_rect(rect.grow(4.0).intersection(board), PATH_EDGE)
	for cell in cells:
		var rect := Rect2(Vector2(cell) * cell_size, Vector2(cell_size, cell_size))
		_ground.draw_rect(rect.intersection(board), PATH_FILL)
	for lane in sim.lane_curves.size():
		_draw_path_arrows(board, lane)
	for lane in map.lane_count():
		var ends := _road_ends(lane)
		if not ends.is_empty():
			_ground.draw_string(_font, ends[0], "IN", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, UiStyle.TEXT_DIM)
			_ground.draw_string(_font, ends[1], "OUT", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, UiStyle.LIFE)


## Chevrons along the path pointing the way enemies walk.
func _draw_path_arrows(board: Rect2, lane: int) -> void:
	var curve := sim.lane_curves[lane]
	var offset := PATH_ARROW_SPACING * 0.5
	while offset < sim.lane_lengths[lane] - 8.0:
		var at := curve.sample_baked(offset)
		var forward := (curve.sample_baked(offset + 8.0) - at).normalized()
		offset += PATH_ARROW_SPACING
		if not board.has_point(at) or forward.is_zero_approx():
			continue
		var side := forward.orthogonal()
		var tip := at + forward * 6.0
		var back := tip - forward * 11.0
		_ground.draw_polyline(PackedVector2Array([back + side * 9.0, tip, back - side * 9.0]), PATH_ARROW, 3.0, true)


func _draw_range(center: Vector2, radius: float, color: Color) -> void:
	draw_circle(center, radius, Color(color, 0.06))
	draw_arc(center, radius, 0.0, TAU, 72, color, 2.0, true)


func _draw_tower(data: TowerData, center: Vector2, alpha: float) -> void:
	var base := Rect2(center - Vector2(TOWER_HALF_SIZE, TOWER_HALF_SIZE), Vector2(TOWER_HALF_SIZE, TOWER_HALF_SIZE) * 2.0)
	draw_rect(base, Color(TOWER_BASE, alpha))
	draw_rect(base, Color(1, 1, 1, 0.12 * alpha), false, 2.0)
	var shape := _tower_shape(data, center)
	draw_colored_polygon(shape, Color(_tower_color(data, 0), alpha))
	if data.is_hybrid():
		var right_half := PackedVector2Array([
			center + Vector2(0, -40), center + Vector2(40, -40), center + Vector2(40, 40), center + Vector2(0, 40)])
		for piece in Geometry2D.intersect_polygons(shape, right_half):
			draw_colored_polygon(piece, Color(_tower_color(data, 1), alpha))
	var outline := shape.duplicate()
	outline.append(shape[0])
	draw_polyline(outline, Color(0, 0, 0, 0.55 * alpha), 2.0, true)


## Chain towers are diamonds, splash towers are circles, single-target towers are triangles.
func _tower_shape(data: TowerData, center: Vector2) -> PackedVector2Array:
	var points := PackedVector2Array()
	if data.chain_count > 0 and data.splash_radius <= 0.0:
		for offset: Vector2 in [Vector2(0, -19), Vector2(19, 0), Vector2(0, 19), Vector2(-19, 0)]:
			points.append(center + offset)
	elif data.splash_radius > 0.0:
		for i in 20:
			points.append(center + Vector2.from_angle(TAU * i / 20.0) * 17.0)
	else:
		for i in 3:
			points.append(center + Vector2.from_angle(-PI / 2.0 + TAU * i / 3.0) * 20.0)
	return points


func _tower_color(data: TowerData, index: int) -> Color:
	if data.elements.is_empty():
		return Color.WHITE
	return sim.config.element_color(data.elements[mini(index, data.elements.size() - 1)])


func _enemy_radius(enemy: SimEnemy) -> float:
	if enemy.data.tags.has(&"boss"):
		return 22.0
	if enemy.data.tags.has(&"armoured"):
		return 15.0
	if enemy.data.tags.has(&"fast"):
		return 9.0
	return 11.0


func _draw_enemy(enemy: SimEnemy) -> void:
	var radius := _enemy_radius(enemy)
	var art_height := BoardArt.enemy_height(enemy.data.id) if art != null else 0.0
	if art_height <= 0.0:
		var aura := sim.config.element_color_at(enemy.element)
		draw_circle(enemy.position, radius + 3.0, aura)
		draw_circle(enemy.position, radius, ENEMY_OUTLINE)
		draw_circle(enemy.position, radius - 2.0, ENEMY_BODY)
		if enemy.data.tags.has(&"armoured") or enemy.data.tags.has(&"boss"):
			draw_arc(enemy.position, radius - 5.0, 0.0, TAU, 24, Color("8a93a6"), 3.0, true)
		if enemy.has_status(&"burn"):
			draw_arc(enemy.position, radius + 6.0, 0.0, TAU, 24, Color("ff8a3d"), 2.5, true)
		if enemy.has_status(&"poison"):
			draw_circle(enemy.position + Vector2(radius * 0.7, -radius * 0.7), 4.0, Color("7be35b"))
	if enemy.health < enemy.max_health:
		var width := radius * 2.0 + 8.0
		var top := -radius - 12.0
		if art_height > 0.0:
			# Enemy art stands on its position, so the bar goes above the sprite.
			top = BoardArt.ENEMY_DROP * BoardArt.SCALE - art_height - 6.0
		var top_left := enemy.position + Vector2(-width * 0.5, top)
		draw_rect(Rect2(top_left - Vector2(1, 1), Vector2(width + 2, 6)), Color(0, 0, 0, 0.75))
		draw_rect(Rect2(top_left, Vector2(width * enemy.health / enemy.max_health, 4)), UiStyle.GOOD)


func _draw_effects() -> void:
	for effect in _effects:
		var fade := 1.0 - effect.time / effect.duration
		match effect.kind:
			&"chain":
				if art != null:
					continue
				draw_polyline(effect.points, Color(effect.color, fade), 4.0, true)
				draw_polyline(effect.points, Color(1, 1, 1, fade), 1.5, true)
			&"blast":
				if art != null:
					continue
				var radius := effect.radius * (0.6 + 0.4 * (1.0 - fade))
				draw_circle(effect.position, radius, Color(effect.color, 0.35 * fade))
			&"text":
				var rise := Vector2(0, -30.0 * (1.0 - fade))
				draw_string(_font, effect.position + rise, effect.text, HORIZONTAL_ALIGNMENT_CENTER, 60, 18, Color(effect.color, fade))
			&"leak":
				draw_circle(effect.position, 30.0, Color(UiStyle.BAD, 0.5 * fade))


func _draw_cursor() -> void:
	var map := sim.config.map
	if not map.is_inside(hover_cell):
		return
	if not aiming.is_empty():
		_draw_aim()
		return
	var cell_size := float(map.cell_size)
	var rect := Rect2(Vector2(hover_cell) * cell_size, Vector2(cell_size, cell_size))
	if placing.is_empty():
		draw_rect(rect, Color(1, 1, 1, 0.06))
		draw_rect(rect, Color(1, 1, 1, 0.18), false, 2.0)
		return
	var data: TowerData = sim.config.towers.get(placing)
	if data == null:
		return
	if art != null:
		_draw_build_grid()
	var center := map.cell_center(hover_cell)
	var valid := sim.can_place(placing, hover_cell)
	draw_rect(rect, VALID if valid else INVALID)
	draw_rect(rect, Color(VALID if valid else INVALID, 0.9), false, 2.0)
	_draw_range(center, data.stat_with(&"attack_range", sim.modifiers()), Color(1, 1, 1, 0.45))
	var picture := BoardArt.tower_picture(data.id) if art != null else null
	if picture == null:
		_draw_tower(data, center, 0.65)
		return
	var anchor: Array = BoardArt.tower_info(data.id)["anchor"]
	var base := center + Vector2(0, BoardArt.TOWER_BASE_DROP * BoardArt.SCALE)
	var top_left := base - Vector2(anchor[0], anchor[1]) * BoardArt.SCALE
	draw_texture_rect(picture, Rect2(top_left, picture.get_size() * BoardArt.SCALE), false, Color(1, 1, 1, 0.7))


## The reach of the skill being aimed, around the mouse, with a mark on every enemy it would hit.
func _draw_aim() -> void:
	var skill: SkillData = sim.config.skills.get(aiming)
	if skill == null:
		return
	var at := _mouse
	var color := sim.config.element_color(skill.element).lightened(0.25)
	draw_circle(at, skill.radius, Color(color, 0.12))
	draw_arc(at, skill.radius, 0.0, TAU, 72, Color(color, 0.95), 3.0, true)
	draw_arc(at, skill.radius - 5.0, 0.0, TAU, 72, Color(0, 0, 0, 0.35), 2.0, true)
	for offset: Vector2 in [Vector2(1, 0), Vector2(0, 1), Vector2(-1, 0), Vector2(0, -1)]:
		draw_line(at + offset * 6.0, at + offset * 16.0, Color(1, 1, 1, 0.9), 2.0)
	for enemy in sim.enemies:
		if enemy.alive and enemy.position.distance_to(at) <= skill.radius:
			draw_arc(enemy.position, _enemy_radius(enemy) + 5.0, 0.0, TAU, 20, Color(1, 1, 1, 0.8), 2.0, true)


## Faint cell lines over the grass while building, so the grid is clear without cluttering the art.
func _draw_build_grid() -> void:
	var map := sim.config.map
	var cell_size := float(map.cell_size)
	var board := map.size_in_pixels()
	for x in range(1, map.grid_size.x):
		draw_line(Vector2(x * cell_size, 0), Vector2(x * cell_size, board.y), Color(1, 1, 1, 0.07))
	for y in range(1, map.grid_size.y):
		draw_line(Vector2(0, y * cell_size), Vector2(board.x, y * cell_size), Color(1, 1, 1, 0.07))


# --- Effects -----------------------------------------------------------------

func _add_effect(kind: StringName, duration: float, position_: Vector2, color: Color) -> Effect:
	var effect := Effect.new()
	effect.kind = kind
	effect.duration = duration
	effect.position = position_
	effect.color = color
	_effects.append(effect)
	return effect


func _on_chain_fired(tower: SimTower, points: PackedVector2Array) -> void:
	var effect := _add_effect(&"chain", 0.18, tower.position, _tower_color(tower.data, tower.data.elements.size() - 1))
	effect.points = points


func _on_projectile_landed(shot: SimProjectile) -> void:
	if shot.splash_radius > 0.0:
		var effect := _add_effect(&"blast", 0.3, shot.position, _tower_color(shot.source.data, 0))
		effect.radius = shot.splash_radius


func _on_enemy_killed(enemy: SimEnemy, _killer: SimTower, bounty: int) -> void:
	var effect := _add_effect(&"text", 0.8, enemy.position, UiStyle.GOLD)
	effect.text = "+%d" % bounty


## Without art, a cast skill shows as a plain flash over what it reached.
func _on_skill_used(skill: SkillData, at: Vector2) -> void:
	var effect := _add_effect(&"blast", 0.45, at, sim.config.element_color(skill.element))
	effect.radius = skill.radius if skill.is_targeted() else sim.config.map.size_in_pixels().x * 0.5


func _on_enemy_leaked(enemy: SimEnemy) -> void:
	_add_effect(&"leak", 0.5, enemy.position, UiStyle.BAD)
