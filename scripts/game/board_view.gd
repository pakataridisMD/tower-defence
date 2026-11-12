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
## The player clicked the board while aiming a hero's ability.
signal hero_aimed(hero_id: StringName, at: Vector2)

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
## Hero being summoned, hero whose ability is being aimed, and hero marching, or empty / null.
var summoning: StringName = &""
var aiming_hero: StringName = &""
var moving: SimTower
var selected: SimTower
var hover_cell := Vector2i(-1, -1)
## Where the mouse last was, in board pixels and on screen.
var _mouse := Vector2(-1, -1)
var _screen_mouse := Vector2(-1, -1)
## The part of the screen the board is shown in (see BoardCamera). Empty means anywhere.
var view_rect := Rect2()

var _effects: Array[Effect] = []
var _font: Font
## The ground and path never change during a run, so they are drawn once on their own layer.
## Only used when the map has no art.
var _ground: Node2D
## The lit pixel art, or null when the map has no art.
var art: BoardArt
## Draws the defended city's name over the art, or null.
var _names: Node2D
## Draws the army's health bars, the champions' names and what the units shout, over the art.
var _army_layer: Node2D
## Words over units' heads: [ally, text, seconds shown, seconds to show].
var _speech: Array[Array] = []
## Last time (in seconds of _clock) each enemy showed "IMMUNE", so a splash storm does not spam it.
var _immune_shown: Dictionary[int, float] = {}
var _clock := 0.0
## The enemy under the mouse, whose card is drawn, or null.
var hovered_enemy: SimEnemy
var _card_layer: Node2D


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
		if art.landmarks != null:
			# The city's name sits over its gate, above the art (which draws over this node).
			_names = Node2D.new()
			var names := _names
			names.z_index = 8
			names.material = overlay
			names.draw.connect(_draw_city_names.bind(names))
			add_child(names)
	else:
		_ground = Node2D.new()
		_ground.show_behind_parent = true
		_ground.draw.connect(_draw_ground_layer)
		add_child(_ground)
	_army_layer = Node2D.new()
	_army_layer.z_index = 8
	_army_layer.material = overlay
	_army_layer.draw.connect(_draw_army_layer)
	add_child(_army_layer)
	# The hovered enemy's card goes over everything on the board, art and actors included.
	_card_layer = Node2D.new()
	_card_layer.z_index = 20
	_card_layer.material = overlay
	_card_layer.draw.connect(func() -> void:
		for enemy in sim.enemies:
			_draw_affinity_badge(_card_layer, enemy)
		if hovered_enemy != null and hovered_enemy.alive:
			_draw_enemy_card(_card_layer, hovered_enemy))
	add_child(_card_layer)
	sim.chain_fired.connect(_on_chain_fired)
	sim.projectile_landed.connect(_on_projectile_landed)
	sim.enemy_killed.connect(_on_enemy_killed)
	sim.enemy_leaked.connect(_on_enemy_leaked)
	sim.enemy_immune.connect(_on_enemy_immune)
	sim.skill_used.connect(_on_skill_used)
	sim.hero_ability_used.connect(_on_hero_ability_used)


func begin_placing(tower_id: StringName) -> void:
	cancel_hero_actions()
	aiming = &""
	placing = tower_id
	select(null)


func cancel_placing() -> void:
	placing = &""


## Starts placing a hero: the next click on a free tile summons it.
func begin_summoning(hero_id: StringName) -> void:
	cancel_hero_actions()
	placing = &""
	aiming = &""
	summoning = hero_id
	select(null)


## Starts aiming a hero's ability: the next click on the board casts it.
func begin_hero_aiming(hero_id: StringName) -> void:
	cancel_hero_actions()
	placing = &""
	aiming = &""
	aiming_hero = hero_id


## Starts marching a hero: the next click on a free tile moves it there.
func begin_moving(tower: SimTower) -> void:
	cancel_hero_actions()
	placing = &""
	aiming = &""
	moving = tower


func cancel_hero_actions() -> void:
	summoning = &""
	aiming_hero = &""
	moving = null


## True while the board is waiting for a click for a hero.
func has_hero_action() -> bool:
	return not summoning.is_empty() or not aiming_hero.is_empty() or moving != null


func select(tower: SimTower) -> void:
	if selected == tower:
		return
	selected = tower
	selection_changed.emit(tower)


## Starts aiming a skill: the cursor shows its reach and the next click on the board casts it.
func begin_aiming(skill_id: StringName) -> void:
	cancel_hero_actions()
	placing = &""
	aiming = skill_id


func cancel_aiming() -> void:
	aiming = &""


## Where the mouse is on the board, kept inside it.
func mouse_point() -> Vector2:
	return _mouse.clamp(Vector2.ZERO, sim.config.map.size_in_pixels())


## True while the mouse is over the board.
func mouse_inside() -> bool:
	if view_rect.has_area() and not view_rect.has_point(_screen_mouse):
		return false
	return Rect2(Vector2.ZERO, sim.config.map.size_in_pixels()).has_point(_mouse)


## How much bigger to draw text and bars so they stay readable when the board is zoomed out.
func label_scale() -> float:
	return clampf(1.0 / maxf(global_scale.x, 0.01), 1.0, 2.0)


## Follows the mouse from its events, so the cursor is right however the events arrive.
func _input(event: InputEvent) -> void:
	if event is InputEventMouse:
		_screen_mouse = (event as InputEventMouse).position
		_mouse = (make_input_local(event) as InputEventMouse).position


func _process(delta: float) -> void:
	var active: Array[Effect] = []
	for effect in _effects:
		effect.time += delta
		if effect.time < effect.duration:
			active.append(effect)
	_effects = active
	var speaking: Array[Array] = []
	for words in _speech:
		words[2] += delta
		if words[2] < words[3] and (words[0] as SimAlly).alive:
			speaking.append(words)
	_speech = speaking
	if not sim.allies.is_empty() or not _speech.is_empty():
		_army_layer.queue_redraw()
	if selected != null and not sim.towers.has(selected):
		select(null)
	hover_cell = sim.config.map.cell_at(_mouse)
	_clock += delta
	hovered_enemy = _enemy_under_mouse()
	queue_redraw()


func _unhandled_input(event: InputEvent) -> void:
	var click := event as InputEventMouseButton
	if click == null or not click.pressed:
		return
	if click.button_index != MOUSE_BUTTON_LEFT and click.button_index != MOUSE_BUTTON_RIGHT:
		return
	if view_rect.has_area() and not view_rect.has_point(click.position):
		return
	var map := sim.config.map
	var at := (make_input_local(click) as InputEventMouseButton).position
	var cell := map.cell_at(at)
	if not map.is_inside(cell):
		return
	if has_hero_action():
		if click.button_index == MOUSE_BUTTON_LEFT:
			_hero_click(cell, at)
		elif click.button_index == MOUSE_BUTTON_RIGHT:
			cancel_hero_actions()
		get_viewport().set_input_as_handled()
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


func _hero_click(cell: Vector2i, at: Vector2) -> void:
	if not aiming_hero.is_empty():
		hero_aimed.emit(aiming_hero, at)
		return
	if not summoning.is_empty():
		var error := sim.summon_error(summoning, cell)
		if error.is_empty():
			var tower := sim.summon_hero(summoning, cell)
			cancel_hero_actions()
			select(tower)
		else:
			placement_failed.emit(error)
		return
	if moving != null:
		var error := sim.move_error(moving, cell)
		if error.is_empty():
			sim.move_hero(moving, cell)
			cancel_hero_actions()
		else:
			placement_failed.emit(error)


# --- Drawing -----------------------------------------------------------------

func _draw() -> void:
	if sim == null:
		return
	for tower in sim.towers:
		if tower.is_hero():
			if art == null:
				_draw_hero(tower.hero.id, tower.position, 1.0)
		elif not _has_tower_art(tower.data.id):
			_draw_tower(tower.data, tower.position, 1.0)
	for tower in sim.towers:
		_draw_level(tower)
	if selected != null:
		_draw_range(selected.position, selected.attack_range, Color(1, 1, 1, 0.55))
		if selected.aura_radius > 0.0 and selected.aura_damage > 0.0:
			_draw_range(selected.position, selected.aura_radius, Color(0.75, 0.5, 1.0, 0.5))
		if selected.is_hero():
			_draw_range(selected.position, sim.hero_aura_radius(), Color(UiStyle.GOLD, 0.6))
	_draw_enemy_ground()
	for structure in sim.structures:
		_draw_structure(structure)
	for enemy in sim.enemies:
		_draw_enemy(enemy)
	for ally in sim.allies:
		_draw_ally(ally)
	for tower in sim.towers:
		if tower.silenced > 0.0:
			_draw_silenced(tower)
	if art == null:
		for shot in sim.projectiles:
			var radius := 7.0 if shot.splash_radius > 0.0 else 4.0
			draw_circle(shot.position, radius, _tower_color(shot.source.data, 0))
	else:
		_draw_road_labels()
	_draw_effects()
	_draw_cursor()
	_card_layer.queue_redraw()


## Small gems under a tower: one per level above the first, gold once it has ascended.
func _draw_level(tower: SimTower) -> void:
	if tower.is_hero():
		_draw_hero_level(tower)
		return
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
	if art.landmarks != null and not sim.landmarks.is_empty():
		_names.queue_redraw()
		return
	for lane in sim.config.map.lane_count():
		var ends := _road_ends(lane)
		if ends.is_empty():
			continue
		var exit_label := lane == 0 or ends[1].distance_to(_road_ends(0)[1]) > 1.0
		_draw_outlined(ends[0], "IN", UiStyle.TEXT)
		if exit_label:
			_draw_outlined(ends[1], "OUT", UiStyle.LIFE)


## The defended city's name over its gate. The camps and the city show where the roads start and end.
func _draw_city_names(on: Node2D) -> void:
	var size := sim.config.map.size_in_pixels()
	var cell_size := float(sim.config.map.cell_size)
	for site in sim.landmarks:
		if site.kind != &"city":
			continue
		var top := sim.config.map.cell_center(site.anchor)
		for cell in site.cells:
			top.y = minf(top.y, sim.config.map.cell_center(cell).y)
		var text := art.landmarks.city_name
		var width := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x
		var at := Vector2(top.x - width * 0.5, top.y - cell_size * 0.95)
		at.x = clampf(at.x, 6.0, size.x - width - 6.0)
		at.y = clampf(at.y, 20.0, size.y - 8.0)
		on.draw_string_outline(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, 6, Color(0, 0, 0, 0.7))
		on.draw_string(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, Color(1.0, 0.9, 0.7))


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
	var size := roundi(18 * label_scale())
	draw_string_outline(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, 6, Color(0, 0, 0, 0.6))
	draw_string(_font, at, text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, color)


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
	var radius := 11.0
	if enemy.data.tags.has(&"boss"):
		radius = 22.0
	elif enemy.data.tags.has(&"armoured"):
		radius = 15.0
	elif enemy.data.tags.has(&"fast"):
		radius = 9.0
	return radius * (1.6 if enemy.elite else 1.0)


## Height of the enemy's sprite on the board, 0 without art.
func _art_height(enemy: SimEnemy) -> float:
	if art == null:
		return 0.0
	return BoardArt.enemy_height(enemy.data.id) * (BoardArt.ELITE_SCALE if enemy.elite else 1.0)


func _draw_enemy(enemy: SimEnemy) -> void:
	var radius := _enemy_radius(enemy)
	var art_height := _art_height(enemy)
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
		# Zoomed out, the bar keeps its size on screen.
		var k := label_scale()
		width *= k
		var top_left := enemy.position + Vector2(-width * 0.5, top - 4.0 * (k - 1.0))
		draw_rect(Rect2(top_left - Vector2(1, 1) * k, Vector2(width + 2.0 * k, 6.0 * k)), Color(0, 0, 0, 0.75))
		draw_rect(Rect2(top_left, Vector2(width * enemy.health / enemy.max_health, 4.0 * k)), UiStyle.GOOD)


## In an assault, the ground the enemy still holds is shaded red, with its edge marked.
func _draw_enemy_ground() -> void:
	var limit := sim.build_limit()
	if limit < 0:
		return
	var map := sim.config.map
	var left := float(limit + 1) * map.cell_size
	var pulse := 0.5 + 0.5 * sin(Time.get_ticks_msec() * 0.002)
	draw_rect(Rect2(left, 0, map.size_in_pixels().x - left, map.size_in_pixels().y), Color(0.35, 0.02, 0.12, 0.22))
	draw_dashed_line(Vector2(left, 0), Vector2(left, map.size_in_pixels().y), Color(1.0, 0.35, 0.45, 0.4 + 0.3 * pulse), 3.0, 14.0)


## A unit of the counter-attack with no art of its own: a marker. Its bar is drawn over the art by
## _draw_army_layer.
func _draw_ally(ally: SimAlly) -> void:
	if not ally.alive or (art != null and AllyArt.has_art(ally.data)):
		return
	var radius := 14.0 if ally.is_champion() else 10.0
	var color := UiStyle.GOLD if ally.is_champion() else Color(0.75, 0.2, 0.2)
	if not ally.data.element.is_empty():
		color = sim.config.element_color(ally.data.element)
	draw_circle(ally.position, radius + 3.0, Color(0.95, 0.85, 0.55))
	draw_circle(ally.position, radius, Color(0.12, 0.1, 0.14))
	draw_circle(ally.position, radius - 3.0, color)


## Shows words over a unit's head for a while (ArmyVoice calls it when a unit shouts).
func say(ally: SimAlly, text: String, seconds: float = 2.4) -> void:
	for words in _speech:
		if words[0] == ally:
			words[1] = text
			words[2] = 0.0
			words[3] = seconds
			return
	_speech.append([ally, text, 0.0, seconds])


## Words being shown over units' heads now: [ally, text, seconds shown, seconds to show].
func speech() -> Array[Array]:
	return _speech


## Where a unit's head is drawn, in board pixels.
func ally_top(ally: SimAlly) -> Vector2:
	if art != null and AllyArt.has_art(ally.data):
		return art.army.top(ally)
	return ally.position + Vector2(0, -(14.0 if ally.is_champion() else 10.0) - 6.0)


## Over the art: a health bar on every unit of the army (a champion's in gold, with its name), and
## the words a unit shouts in a small dark box over its head.
func _draw_army_layer() -> void:
	var k := label_scale()
	var on := _army_layer
	for ally in sim.allies:
		if not ally.alive:
			continue
		var head := ally_top(ally)
		var champion := ally.is_champion()
		var width := (46.0 if champion else 26.0) * k
		var tall := (6.0 if champion else 4.0) * k
		var at := head + Vector2(-width * 0.5, -tall - 6.0 * k)
		var share := clampf(ally.health / ally.max_health, 0.0, 1.0)
		on.draw_rect(Rect2(at - Vector2(1.5, 1.5) * k, Vector2(width + 3.0 * k, tall + 3.0 * k)), Color(0, 0, 0, 0.8))
		on.draw_rect(Rect2(at, Vector2(width, tall)), Color(0.22, 0.06, 0.06, 0.9))
		on.draw_rect(Rect2(at, Vector2(width * share, tall)), _ally_bar_color(ally, share))
		if champion:
			# A notch every quarter, and the hero's name.
			for q in [0.25, 0.5, 0.75]:
				on.draw_rect(Rect2(at + Vector2(width * q - 0.5 * k, 0), Vector2(1.0 * k, tall)), Color(0, 0, 0, 0.55))
			var size := roundi(13 * k)
			# The first name only: heroes march together, and full names would run into each other.
			var label := ally.data.display_name.get_slice(" ", 0)
			var label_width := _font.get_string_size(label, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
			var spot := Vector2(head.x - label_width * 0.5, at.y - 4.0 * k)
			on.draw_string_outline(_font, spot, label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, roundi(4 * k), Color(0, 0, 0, 0.85))
			on.draw_string(_font, spot, label, HORIZONTAL_ALIGNMENT_LEFT, -1, size, UiStyle.GOLD)
	for words in _speech:
		_draw_words(on, words[0], words[1], words[2], words[3], k)


func _ally_bar_color(ally: SimAlly, share: float) -> Color:
	if ally.is_champion():
		return UiStyle.GOLD.lerp(UiStyle.BAD, clampf((0.4 - share) / 0.4, 0.0, 1.0))
	if share > 0.6:
		return Color(0.42, 0.85, 0.42)
	if share > 0.3:
		return Color(0.95, 0.78, 0.25)
	return Color(0.95, 0.3, 0.22)


func _draw_words(on: Node2D, ally: SimAlly, text: String, shown: float, length: float, k: float) -> void:
	var alpha := clampf(shown / 0.15, 0.0, 1.0) * clampf((length - shown) / 0.35, 0.0, 1.0)
	var size := roundi(15 * k)
	var text_size := _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size)
	var pad := Vector2(7, 4) * k
	var head := ally_top(ally)
	var rise := 4.0 * k * minf(1.0, shown / 0.2)
	var bottom := head.y - (30.0 if ally.is_champion() else 16.0) * k - rise
	var box := Rect2(Vector2(head.x - text_size.x * 0.5 - pad.x, bottom - text_size.y - pad.y * 2.0), text_size + pad * 2.0)
	var fill := Color(0.06, 0.05, 0.07, 0.86 * alpha)
	var edge := Color(UiStyle.GOLD if ally.is_champion() else Color(0.85, 0.8, 0.7), 0.9 * alpha)
	on.draw_rect(box, fill)
	on.draw_rect(box, edge, false, 1.5 * k)
	var tip := PackedVector2Array([Vector2(head.x - 5.0 * k, box.end.y), Vector2(head.x + 5.0 * k, box.end.y),
		Vector2(head.x, box.end.y + 6.0 * k)])
	on.draw_colored_polygon(tip, fill)
	var ink := Color(1.0, 0.92, 0.7) if ally.is_champion() else UiStyle.TEXT
	on.draw_string(_font, Vector2(box.position.x + pad.x, box.end.y - pad.y - text_size.y * 0.22), text, HORIZONTAL_ALIGNMENT_LEFT,
		-1, size, Color(ink, alpha))


## A building of the enemy base: its health bar, and a shield while it cannot be hurt yet.
func _draw_structure(structure: SimEnemy) -> void:
	if not structure.alive:
		return
	if art != null and art.citadel != null and art.citadel.structure == structure:
		_draw_citadel(structure)
		return
	var height := BoardArt.enemy_height(structure.data.id) if art != null else 0.0
	if height <= 0.0:
		var half := 40.0
		draw_rect(Rect2(structure.position - Vector2(half, half), Vector2(half, half) * 2.0), Color("2a2338"))
		draw_rect(Rect2(structure.position - Vector2(half, half), Vector2(half, half) * 2.0), sim.config.element_color_at(structure.element), false, 3.0)
		height = half * 2.0
	var center := structure.position + Vector2(0, -height * 0.4)
	if not sim.is_vulnerable(structure):
		var shimmer := 0.25 + 0.1 * sin(Time.get_ticks_msec() * 0.003 + structure.id)
		draw_circle(center, height * 0.62, Color(0.75, 0.55, 1.0, shimmer * 0.4))
		draw_arc(center, height * 0.62, 0.0, TAU, 48, Color(0.85, 0.7, 1.0, shimmer + 0.3), 2.0, true)
	var width := 96.0
	var top_left := structure.position + Vector2(-width * 0.5, BoardArt.ENEMY_DROP * BoardArt.SCALE - height - 14.0)
	draw_rect(Rect2(top_left - Vector2(2, 2), Vector2(width + 4, 10)), Color(0, 0, 0, 0.8))
	var color := UiStyle.BAD if sim.is_vulnerable(structure) else Color(0.6, 0.55, 0.7)
	draw_rect(Rect2(top_left, Vector2(width * maxf(0.0, structure.health) / structure.max_health, 6)), color)


## The citadel: a ward of violet light over it until the counter-attack, then a long health bar over
## its gates, where the army fights.
func _draw_citadel(structure: SimEnemy) -> void:
	var gates := art.citadel.gate_points()
	if gates.is_empty():
		return
	var top := gates[0].y - 150.0
	var bottom := gates[gates.size() - 1].y + 150.0
	var x := gates[0].x
	if not sim.is_vulnerable(structure):
		var shimmer := 0.3 + 0.12 * sin(Time.get_ticks_msec() * 0.003)
		for gate in gates:
			draw_arc(gate + Vector2(26, 0), 64.0, PI * 0.5, PI * 1.5, 24, Color(0.8, 0.6, 1.0, shimmer), 3.0, true)
		draw_line(Vector2(x - 6, top), Vector2(x - 6, bottom), Color(0.75, 0.5, 1.0, shimmer * 0.8), 2.0)
		return
	var k := label_scale()
	var width := 240.0 * k
	var at := Vector2(x + 200.0 - width * 0.5, top - 30.0)
	draw_rect(Rect2(at - Vector2(3, 3) * k, Vector2(width + 6.0 * k, 16.0 * k)), Color(0, 0, 0, 0.85))
	draw_rect(Rect2(at, Vector2(width * maxf(0.0, structure.health) / structure.max_health, 10.0 * k)), UiStyle.BAD)
	var font := ThemeDB.fallback_font
	draw_string(font, at + Vector2(0, -6.0 * k), structure.data.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, int(14 * k), Color(1, 0.85, 0.85))


## A silenced tower shows a crossed-out ring until it can fire again.
func _draw_silenced(tower: SimTower) -> void:
	var at := tower.position + Vector2(0, -44)
	draw_circle(at, 11.0, Color(0, 0, 0, 0.6))
	draw_arc(at, 11.0, 0.0, TAU, 24, Color(0.85, 0.6, 1.0), 2.0, true)
	draw_line(at + Vector2(-7, -7), at + Vector2(7, 7), Color(0.85, 0.6, 1.0), 2.0)


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
				var k := label_scale()
				draw_string(_font, effect.position + rise * k - Vector2(30.0 * (k - 1.0), 0), effect.text, HORIZONTAL_ALIGNMENT_CENTER,
					60.0 * k, roundi(18 * k), Color(effect.color, fade))
			&"hero_blast":
				var spread := effect.radius * (0.5 + 0.5 * (1.0 - fade))
				draw_circle(effect.position, spread, Color(effect.color, 0.22 * fade))
				draw_arc(effect.position, spread, 0.0, TAU, 72, Color(effect.color.lightened(0.4), fade), 4.0, true)
			&"leak":
				draw_circle(effect.position, 30.0, Color(UiStyle.BAD, 0.5 * fade))


func _draw_cursor() -> void:
	var map := sim.config.map
	if not map.is_inside(hover_cell):
		return
	if not aiming.is_empty():
		_draw_aim()
		return
	if not aiming_hero.is_empty():
		_draw_hero_aim()
		return
	var cell_size := float(map.cell_size)
	if not summoning.is_empty() or moving != null:
		_draw_hero_cursor()
		return
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


# --- Heroes ------------------------------------------------------------------

## A hero's board sprite standing on its cell, for maps drawn without art.
func _draw_hero(hero_id: StringName, center: Vector2, alpha: float) -> void:
	var sprite := hero_sprite(hero_id)
	if sprite == null:
		draw_circle(center, 20.0, Color(UiStyle.GOLD, alpha))
		return
	var size := sprite.get_size() * BoardArt.SCALE
	var feet := center + Vector2(0, BoardArt.TOWER_BASE_DROP * BoardArt.SCALE + 4.0)
	draw_texture_rect(sprite, Rect2(feet - Vector2(size.x * 0.5, size.y), size), false, Color(1, 1, 1, alpha))


static func hero_sprite(hero_id: StringName) -> Texture2D:
	var path := "res://assets/art/heroes/board/%s.png" % hero_id
	return load(path) if ResourceLoader.exists(path) else null


## A hero's level under its feet, as a small gold number.
func _draw_hero_level(tower: SimTower) -> void:
	var at := tower.position + Vector2(-20, 40)
	var text := "Lv %d" % tower.hero_level_now()
	draw_string_outline(_font, at, text, HORIZONTAL_ALIGNMENT_CENTER, 40, 14, 4, Color(0, 0, 0, 0.8))
	draw_string(_font, at, text, HORIZONTAL_ALIGNMENT_CENTER, 40, 14, UiStyle.GOLD)


## The tile a hero would be summoned or marched to, with its reach and its aura.
func _draw_hero_cursor() -> void:
	var map := sim.config.map
	var cell_size := float(map.cell_size)
	var rect := Rect2(Vector2(hover_cell) * cell_size, Vector2(cell_size, cell_size))
	var hero_id := summoning if moving == null else moving.hero.id
	var error := sim.summon_error(hero_id, hover_cell) if moving == null else sim.move_error(moving, hover_cell)
	var valid := error.is_empty()
	if art != null:
		_draw_build_grid()
	draw_rect(rect, VALID if valid else INVALID)
	draw_rect(rect, Color(VALID if valid else INVALID, 0.9), false, 2.0)
	var center := map.cell_center(hover_cell)
	var hero := sim.hero_data(hero_id)
	if hero != null:
		_draw_range(center, hero.attack.attack_range, Color(1, 1, 1, 0.45))
		_draw_range(center, sim.hero_aura_radius(), Color(UiStyle.GOLD, 0.45))
	_draw_hero(hero_id, center, 0.7)


## The reach of the hero ability being aimed, around the mouse.
func _draw_hero_aim() -> void:
	var tower := sim.hero_tower(aiming_hero)
	if tower == null:
		return
	var ability := tower.hero_ability()
	var radius := ability.radius_cells * sim.config.map.cell_size
	var color := UiStyle.GOLD if tower.hero.element.is_empty() else sim.config.element_color(tower.hero.element).lightened(0.25)
	draw_circle(_mouse, radius, Color(color, 0.12))
	draw_arc(_mouse, radius, 0.0, TAU, 72, Color(color, 0.95), 3.0, true)
	for enemy in sim.enemies:
		if enemy.alive and enemy.position.distance_to(_mouse) <= radius:
			draw_arc(enemy.position, _enemy_radius(enemy) + 5.0, 0.0, TAU, 20, Color(1, 1, 1, 0.8), 2.0, true)


func _on_hero_ability_used(tower: SimTower, ability: HeroAbility, points: PackedVector2Array) -> void:
	var color := UiStyle.GOLD if tower.hero.element.is_empty() else sim.config.element_color(tower.hero.element)
	var radius := ability.radius_cells * sim.config.map.cell_size
	if ability.target == HeroAbility.Target.BOARD:
		radius = sim.config.map.size_in_pixels().x * 0.5
	for point in points:
		var effect := _add_effect(&"hero_blast", 0.6, point, color)
		effect.radius = radius


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


func _on_enemy_immune(enemy: SimEnemy, _tower: SimTower) -> void:
	if _clock - float(_immune_shown.get(enemy.id, -10.0)) < 1.2:
		return
	_immune_shown[enemy.id] = _clock
	if _immune_shown.size() > 400:
		_immune_shown.clear()
	var effect := _add_effect(&"text", 0.9, enemy.position + Vector2(0, -24), Color("c9d1e0"))
	effect.text = "IMMUNE"


# --- Enemy weaknesses ------------------------------------------------------------

## The living enemy nearest the mouse, if the mouse is on it. Not while placing or aiming.
func _enemy_under_mouse() -> SimEnemy:
	if not mouse_inside() or not placing.is_empty() or not aiming.is_empty() or has_hero_action():
		return null
	var best: SimEnemy = null
	var best_distance := INF
	for enemy in sim.enemies:
		if not enemy.alive or enemy.leaked:
			continue
		var reach := _enemy_radius(enemy) + 6.0
		# Sprites stand on their position, so the body is above it.
		var body := enemy.position + Vector2(0, -minf(_art_height(enemy) * 0.45, 40.0))
		var distance := minf(body.distance_to(_mouse), enemy.position.distance_to(_mouse))
		if distance <= reach and distance < best_distance:
			best_distance = distance
			best = enemy
	return best


## A small mark over enemies that are not plain: a diamond (attuned), a shield (warded) or a plate
## (tank), in the colour of their element, so the player sees at a glance what to bring.
func _draw_affinity_badge(on: CanvasItem, enemy: SimEnemy) -> void:
	var radius := _enemy_radius(enemy)
	var art_height := _art_height(enemy)
	if enemy.affinity.is_empty() or enemy.element < 0 or not enemy.alive:
		return
	var k := label_scale()
	# Drawn sprites stand in tall frames, so the mark sits over the body by the enemy's size instead.
	var top := -radius * (3.2 if art_height > 0.0 else 1.0) - 10.0
	var at := enemy.position + Vector2(0, top - 4.0 * (k - 1.0))
	var color := sim.config.element_color_at(enemy.element)
	var s := 5.0 * k
	var shape := PackedVector2Array()
	match enemy.affinity:
		ElementRules.ATTUNED:
			shape = PackedVector2Array([at + Vector2(0, -s), at + Vector2(s, 0), at + Vector2(0, s), at + Vector2(-s, 0)])
		ElementRules.WARDED:
			shape = PackedVector2Array([at + Vector2(-s, -s), at + Vector2(s, -s), at + Vector2(s, s * 0.2),
				at + Vector2(0, s * 1.2), at + Vector2(-s, s * 0.2)])
		_:
			shape = PackedVector2Array([at + Vector2(-s, -s), at + Vector2(s, -s), at + Vector2(s, s), at + Vector2(-s, s)])
	var outline := shape.duplicate()
	outline.append(shape[0])
	on.draw_colored_polygon(shape, Color(0, 0, 0, 0.7))
	var inner := PackedVector2Array()
	for point in shape:
		inner.append(at + (point - at) * 0.6)
	on.draw_colored_polygon(inner, color)
	on.draw_polyline(outline, UiStyle.GOLD if enemy.elite else Color(1, 1, 1, 0.85), 1.5 * k, true)


## The hovered enemy's card: its name, element and what hurts it.
func _draw_enemy_card(on: CanvasItem, enemy: SimEnemy) -> void:
	var lines := enemy_card_lines(enemy)
	# The same size on screen at any zoom.
	var k := 1.0 / maxf(global_scale.x, 0.01)
	var size := roundi(15 * k)
	var line_height := 19.0 * k
	var width := 0.0
	for line in lines:
		var w := 0.0
		for part in line:
			w += _font.get_string_size(String(part[0]), HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		width = maxf(width, w)
	var pad := 8.0 * k
	var box := Vector2(width + pad * 2.0, line_height * lines.size() + pad * 1.4)
	var at := enemy.position + Vector2(24.0 * k, -box.y - 20.0 * k)
	var board := sim.config.map.size_in_pixels()
	at.x = clampf(at.x, 0.0, maxf(0.0, board.x - box.x))
	at.y = clampf(at.y, 0.0, maxf(0.0, board.y - box.y))
	on.draw_rect(Rect2(at, box), Color(0.05, 0.06, 0.09, 0.9))
	on.draw_rect(Rect2(at, box), UiStyle.GOLD if enemy.elite else Color(1, 1, 1, 0.35), false, 1.5 * k)
	var y := at.y + pad + line_height * 0.75
	for line in lines:
		var x := at.x + pad
		for part in line:
			var text := String(part[0])
			on.draw_string(_font, Vector2(x, y), text, HORIZONTAL_ALIGNMENT_LEFT, -1, size, part[1])
			x += _font.get_string_size(text, HORIZONTAL_ALIGNMENT_LEFT, -1, size).x
		y += line_height


## The card as lines of [text, colour] parts. Public so tests can read it.
func enemy_card_lines(enemy: SimEnemy) -> Array:
	var dim := UiStyle.TEXT_DIM
	var lines: Array = []
	lines.append([[enemy.display_name(), UiStyle.GOLD if enemy.elite else Color.WHITE]])
	var own := sim.config.element_at(enemy.element)
	var kind := String(ElementRules.PROFILE_NAMES.get(enemy.affinity, ""))
	if enemy.elite:
		kind = "Elite tank"
	if own != null:
		var head: Array = [[own.display_name, own.color]]
		if not kind.is_empty():
			head.append(["  ·  " + kind, dim])
		lines.append(head)
		var opposite := sim.config.element_at(ElementRules.opposite_index(enemy.element))
		var weak := ElementRules.weakness_multiplier(enemy.element, enemy.affinity)
		lines.append([["Weak to ", dim], [opposite.display_name if opposite else "?", opposite.color if opposite else Color.WHITE],
			["  x%s" % _factor(weak), UiStyle.GOOD]])
		var immune := ElementRules.immunities(enemy.element, enemy.affinity)
		if not immune.is_empty():
			var parts: Array = [["Immune to ", dim]]
			for i in immune.size():
				var el := sim.config.element_at(immune[i])
				if i > 0:
					parts.append([", ", dim])
				parts.append([el.display_name if el else "?", el.color if el else Color.WHITE])
			lines.append(parts)
		var resist: Array = [["Resists ", dim]]
		var any := false
		for step in [0, 1, 2]:
			var factor: float = ElementRules.element_factor((enemy.element + step) % ElementData.RING_SIZE, enemy.element, enemy.affinity)
			if factor <= 0.0 or factor >= 1.0:
				continue
			var names: PackedStringArray = []
			for side in ([1, -1] if step in [1, 2] else [0]):
				var el := sim.config.element_at(posmod(enemy.element + step * side, ElementData.RING_SIZE))
				if el != null:
					names.append(el.display_name)
			if any:
				resist.append([", ", dim])
			resist.append(["%s x%s" % ["/".join(names), _factor(factor)], UiStyle.BAD])
			any = true
		if any:
			lines.append(resist)
	elif not kind.is_empty():
		lines.append([[kind, dim]])
	lines.append([["Health %d / %d" % [ceili(enemy.health), ceili(enemy.max_health)], dim],
		["  ·  Armour %d" % roundi(enemy.effective_armour()), dim]])
	return lines


static func _factor(value: float) -> String:
	return ("%.2f" % value).rstrip("0").rstrip(".")
