class_name BoardView
extends Node2D
## Draws the map, towers, enemies, shots and effects from the run simulation with placeholder
## shapes, and handles clicks on the board: placing towers and selecting them.

signal selection_changed(tower: SimTower)
signal placement_failed(reason: String)

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
var selected: SimTower
var hover_cell := Vector2i(-1, -1)

var _effects: Array[Effect] = []
## Seconds since the board was set up, for tower art animations.
var _time := 0.0
var _font: Font
## The ground and path never change during a run, so they are drawn once on their own layer.
var _ground: Node2D


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
	_ground = Node2D.new()
	_ground.show_behind_parent = true
	_ground.draw.connect(_draw_ground_layer)
	add_child(_ground)
	sim.chain_fired.connect(_on_chain_fired)
	sim.projectile_landed.connect(_on_projectile_landed)
	sim.enemy_killed.connect(_on_enemy_killed)
	sim.enemy_leaked.connect(_on_enemy_leaked)


func begin_placing(tower_id: StringName) -> void:
	placing = tower_id
	select(null)


func cancel_placing() -> void:
	placing = &""


func select(tower: SimTower) -> void:
	if selected == tower:
		return
	selected = tower
	selection_changed.emit(tower)


func _process(delta: float) -> void:
	_time += delta
	var active: Array[Effect] = []
	for effect in _effects:
		effect.time += delta
		if effect.time < effect.duration:
			active.append(effect)
	_effects = active
	if selected != null and not sim.towers.has(selected):
		select(null)
	hover_cell = sim.config.map.cell_at(get_local_mouse_position())
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	var click := event as InputEventMouseButton
	if click == null or not click.pressed:
		return
	var map := sim.config.map
	var cell := map.cell_at((make_input_local(click) as InputEventMouseButton).position)
	if not map.is_inside(cell):
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
	# Tower art is taller than a cell, so draw from the top row down and let nearer towers overlap.
	var towers := sim.towers.duplicate()
	towers.sort_custom(func(a: SimTower, b: SimTower) -> bool: return a.position.y < b.position.y)
	for tower: SimTower in towers:
		_draw_tower(tower.data, tower.position, 1.0, tower.facing, tower.id * 3)
	if selected != null:
		_draw_range(selected.position, selected.attack_range, Color(1, 1, 1, 0.55))
	for enemy in sim.enemies:
		_draw_enemy(enemy)
	for shot in sim.projectiles:
		var radius := 7.0 if shot.splash_radius > 0.0 else 4.0
		draw_circle(shot.position, radius, _tower_color(shot.source.data, 0))
	_draw_effects()
	_draw_cursor()


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
	_draw_path_arrows(board)

	var points := map.path_points()
	if points.size() >= 2:
		var entry := Vector2(0, points[0].y)
		var exit := Vector2(board.size.x, points[points.size() - 1].y)
		_ground.draw_string(_font, entry + Vector2(6, -cell_size * 0.5 - 8), "IN", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, UiStyle.TEXT_DIM)
		_ground.draw_string(_font, exit + Vector2(-38, -cell_size * 0.5 - 8), "OUT", HORIZONTAL_ALIGNMENT_LEFT, -1, 18, UiStyle.LIFE)


## Chevrons along the path pointing the way enemies walk.
func _draw_path_arrows(board: Rect2) -> void:
	var offset := PATH_ARROW_SPACING * 0.5
	while offset < sim.path_length - 8.0:
		var at := sim.path_curve.sample_baked(offset)
		var forward := (sim.path_curve.sample_baked(offset + 8.0) - at).normalized()
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


func _draw_tower(data: TowerData, center: Vector2, alpha: float, facing: float = PI / 2.0, phase: int = 0) -> void:
	var art := TowerSpriteSet.for_tower(data.id)
	if art != null:
		art.draw(self, center, facing, _time, phase, Color(1, 1, 1, alpha))
		return
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
	var wave := sim.current_wave()
	var aura := sim.config.element_color(wave.element) if wave != null else Color.WHITE
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
		var top_left := enemy.position + Vector2(-width * 0.5, -radius - 12.0)
		draw_rect(Rect2(top_left, Vector2(width, 5)), Color(0, 0, 0, 0.7))
		draw_rect(Rect2(top_left, Vector2(width * enemy.health / enemy.max_health, 5)), UiStyle.GOOD)


func _draw_effects() -> void:
	for effect in _effects:
		var fade := 1.0 - effect.time / effect.duration
		match effect.kind:
			&"chain":
				draw_polyline(effect.points, Color(effect.color, fade), 4.0, true)
				draw_polyline(effect.points, Color(1, 1, 1, fade), 1.5, true)
			&"blast":
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
	var cell_size := float(map.cell_size)
	var rect := Rect2(Vector2(hover_cell) * cell_size, Vector2(cell_size, cell_size))
	if placing.is_empty():
		draw_rect(rect, Color(1, 1, 1, 0.05))
		return
	var data: TowerData = sim.config.towers.get(placing)
	if data == null:
		return
	var center := map.cell_center(hover_cell)
	draw_rect(rect, VALID if sim.can_place(placing, hover_cell) else INVALID)
	_draw_range(center, data.stat_with(&"attack_range", sim.modifiers()), Color(1, 1, 1, 0.45))
	_draw_tower(data, center, 0.65)


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


func _on_enemy_leaked(enemy: SimEnemy) -> void:
	_add_effect(&"leak", 0.5, enemy.position, UiStyle.BAD)
