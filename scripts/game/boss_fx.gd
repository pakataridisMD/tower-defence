class_name BossFx
extends Node2D
## Draws the bosses' own abilities over the board art (see BossAbilities): a green rush of light when
## a boss heals, a shimmering barrier round it while the barrier holds, dark chains on the towers it
## binds, and the overlord's fireball: a red mark on the doomed tower, the ball arcing in, the tower
## bursting apart and its ruin burning on the cell until the wave ends.
##
## It lives in BoardArt's world, so it draws in art pixels (half a screen pixel), and borrows its
## bursts, rings, beams and lights so the effects match the rest of the board.

const HEAL := Color(0.45, 1.0, 0.55)
const BARRIER := Color(0.55, 0.8, 1.0)
const BARRIER_RIM := Color(1.0, 0.86, 0.45)
const CHAIN := Color(0.62, 0.3, 1.0)
const CHAIN_DARK := Color(0.16, 0.08, 0.26)
const FIRE := Color(1.0, 0.45, 0.1)
const FIRE_CORE := Color(1.0, 0.92, 0.6)
const EMBER := Color(0.95, 0.3, 0.06)
## How high the fireball arcs over the board, in art pixels.
const ARC := 70.0

var sim: RunSim
var art: BoardArt
## Towers bound by a boss and how long the chains hold, by tower id: [tower, seconds left, duration].
var _bound: Dictionary[int, Array] = {}
## Bits of a destroyed tower flying apart: [position, velocity, seconds left, size, colour].
var _debris: Array[Array] = []
## Ruins as they were struck, by cell, for their stones: [art position, seed].
var _ruins: Dictionary[Vector2i, Array] = {}
var _time := 0.0
var _trail_wait := 0.0


func setup(p_sim: RunSim, p_art: BoardArt) -> void:
	sim = p_sim
	art = p_art
	z_index = 5
	material = art._unshaded
	art._world.add_child(self)
	sim.boss_ability.connect(_on_boss_ability)


func _process(delta: float) -> void:
	if sim == null:
		return
	_time += delta
	for id: int in _bound.keys():
		var entry: Array = _bound[id]
		entry[1] -= delta
		var tower: SimTower = entry[0]
		if entry[1] <= 0.0 or not sim.towers.has(tower):
			_bound.erase(id)
	var flying: Array[Array] = []
	for bit in _debris:
		bit[2] -= delta
		if bit[2] > 0.0:
			bit[1] += Vector2(0, 160.0) * delta
			bit[0] += bit[1] * delta
			flying.append(bit)
	_debris = flying
	for cell: Vector2i in _ruins.keys():
		if not sim.boss_powers.is_ruin(cell):
			_ruins.erase(cell)
	_trail_wait -= delta
	if _trail_wait <= 0.0:
		_trail_wait = 0.05
		for ball in sim.boss_powers.fireballs():
			art._burst(_fireball_at(ball), FIRE, 4, 10.0)
	queue_redraw()


func _feet(enemy: SimEnemy) -> Vector2:
	return art._art_pos(enemy.position) + Vector2(0, BoardArt.ENEMY_DROP)


## The boss's sprite size in art pixels, or a guess before it has one.
func _size(enemy: SimEnemy) -> Vector2:
	var visual: BoardArt.EnemyVisual = art._enemies.get(enemy.id)
	return visual.size if visual != null and visual.size != Vector2.ZERO else Vector2(48, 60)


func _chest(enemy: SimEnemy) -> Vector2:
	return _feet(enemy) + Vector2(0, -_size(enemy).y * 0.45)


func _tower_base(tower: SimTower) -> Vector2:
	return art._art_pos(tower.position) + Vector2(0, BoardArt.TOWER_BASE_DROP)


## Where a fireball is now: on an arc from the boss's raised hand to the tower.
func _fireball_at(ball: Array) -> Vector2:
	var boss: SimEnemy = ball[0]
	var tower: SimTower = ball[1]
	var t := clampf(1.0 - float(ball[2]) / BossAbilities.FIREBALL_FLIGHT, 0.0, 1.0)
	var from := _feet(boss) + Vector2(0, -_size(boss).y * 0.95)
	var to := _tower_base(tower) + Vector2(0, -12)
	# It eases in, then drops onto the tower.
	var eased := t * t * (3.0 - 2.0 * t)
	return from.lerp(to, eased) + Vector2(0, -sin(t * PI) * ARC)


func _on_boss_ability(boss: SimEnemy, ability: StringName, targets: Array) -> void:
	var chest := _chest(boss)
	var feet := _feet(boss)
	var size := _size(boss)
	match ability:
		&"heal":
			art._ring(feet, HEAL, 4.0, size.x * 0.9, 0.9, 2.0)
			art._ring(chest, HEAL.lerp(Color.WHITE, 0.4), 2.0, size.x * 0.5, 0.6)
			art._burst(chest, HEAL, 26, 22.0)
			art._sparks(chest, HEAL.lerp(Color.WHITE, 0.5), 10, size.x * 0.4)
			art._pulse_light(chest, HEAL, 2.2, size.x * 1.4, 0.9)
		&"shield":
			art._ring(chest, BARRIER_RIM, size.x * 0.9, size.x * 0.6, 0.4, 2.0)
			art._burst(chest, BARRIER, 22, 18.0)
			art._pulse_light(chest, BARRIER, 1.8, size.x * 1.2, 0.6)
		&"shield_break":
			art._burst(chest, BARRIER.lerp(Color.WHITE, 0.4), 40, 46.0)
			art._ring(chest, BARRIER_RIM, size.x * 0.55, size.x * 1.1, 0.45, 2.0)
			art._sparks(chest, Color.WHITE, 12, size.x * 0.6)
			art._pulse_light(chest, BARRIER, 2.4, size.x * 1.4, 0.4)
		&"bind":
			for tower: SimTower in targets:
				var base := _tower_base(tower)
				_bound[tower.id] = [tower, tower.silenced, tower.silenced]
				art._beam(chest, base + Vector2(0, -10), CHAIN, 0.5, 2.0)
				art._ring(base, CHAIN, 22.0, 6.0, 0.5, 2.0)
				art._burst(base + Vector2(0, -8), CHAIN, 16, 14.0)
			art._pulse_light(chest, CHAIN, 1.6, size.x, 0.5)
		&"fireball":
			var hand := feet + Vector2(0, -size.y * 0.95)
			art._burst(hand, FIRE, 30, 24.0)
			art._ring(hand, FIRE_CORE, 2.0, 18.0, 0.4, 2.0)
			art._pulse_light(hand, FIRE, 2.6, 90.0, 0.8)
		&"destroy_tower":
			var tower: SimTower = targets[0]
			_explode(tower)


## The fireball lands: the tower bursts apart in fire and stone and its ruin starts to burn.
func _explode(tower: SimTower) -> void:
	var base := _tower_base(tower)
	var body := base + Vector2(0, -14)
	art._burst(body, FIRE, 60, 60.0)
	art._burst(body, Color(0.35, 0.3, 0.28), 30, 40.0, false)
	art._ring(base, FIRE_CORE, 4.0, 46.0, 0.6, 3.0)
	art._ring(base, FIRE, 2.0, 30.0, 0.8, 2.0)
	art._sparks(body, FIRE_CORE, 14, 30.0)
	art._pulse_light(body, FIRE, 3.2, 140.0, 1.2)
	var colors := tower.data.elements.map(func(id: StringName) -> Color: return _element_color(id))
	for i in 22:
		var angle := -PI * 0.5 + randf_range(-1.2, 1.2)
		var speed := randf_range(50.0, 130.0)
		var color: Color = Color(0.42, 0.38, 0.35) if i % 3 != 0 or colors.is_empty() else colors[i % colors.size()]
		_debris.append([body + Vector2(randf_range(-6, 6), randf_range(-8, 4)), Vector2.from_angle(angle) * speed,
				randf_range(0.6, 1.1), randf_range(1.0, 3.0), color])
	_ruins[tower.cell] = [base, randi() % 1000]


func _element_color(element_id: StringName) -> Color:
	var element: ElementData = sim.config.elements.get(element_id)
	return element.color if element != null else Color(0.8, 0.7, 0.5)


func _draw() -> void:
	if sim == null:
		return
	for enemy in sim.enemies:
		if enemy.alive and enemy.barrier > 0.0:
			_draw_barrier(enemy)
	for entry: Array in _bound.values():
		_draw_chains(entry[0], float(entry[1]) / maxf(0.1, float(entry[2])))
	for ball in sim.boss_powers.fireballs():
		_draw_target(ball[1], float(ball[2]))
		_draw_fireball(_fireball_at(ball))
	for cell: Vector2i in _ruins:
		_draw_ruin(_ruins[cell][0], int(_ruins[cell][1]))
	for bit in _debris:
		var fade := clampf(float(bit[2]) * 2.0, 0.0, 1.0)
		var bit_size := float(bit[3])
		draw_rect(Rect2((bit[0] as Vector2).floor(), Vector2(bit_size, bit_size)), Color(bit[4] as Color, fade))


## A shimmering shell round the boss, thinner as it takes damage, with runes running round its rim.
func _draw_barrier(enemy: SimEnemy) -> void:
	var size := _size(enemy)
	var center := _chest(enemy)
	var full := enemy.max_health * maxf(enemy.data.shield_amount, 0.01)
	var left := clampf(enemy.barrier / full, 0.0, 1.0)
	var fading := clampf(enemy.barrier_left / 0.6, 0.0, 1.0)
	var radius := Vector2(size.x * 0.62, size.y * 0.62)
	var wobble := 1.0 + 0.03 * sin(_time * 5.0)
	var points := PackedVector2Array()
	for i in 49:
		var angle := TAU * float(i) / 48.0
		points.append(center + Vector2(cos(angle) * radius.x, sin(angle) * radius.y) * wobble)
	var alpha := (0.25 + 0.55 * left) * fading
	draw_polygon(points, PackedColorArray([Color(BARRIER, 0.08 * fading)]))
	draw_polyline(points, Color(BARRIER, alpha), 1.5 + left * 1.5)
	draw_polyline(points, Color(BARRIER_RIM, alpha * 0.6), 1.0)
	# Hexagons of light drift over the shell.
	for i in 10:
		var angle := TAU * float(i) / 10.0 + _time * 0.9
		var at := center + Vector2(cos(angle) * radius.x, sin(angle) * radius.y * 0.9) * 0.82 * wobble
		var flicker := 0.5 + 0.5 * sin(_time * 7.0 + float(i) * 1.7)
		_hexagon(at, 2.5 + left * 1.5, Color(BARRIER.lerp(Color.WHITE, 0.4), alpha * flicker))


func _hexagon(at: Vector2, radius: float, color: Color) -> void:
	var points := PackedVector2Array()
	for i in 7:
		points.append(at + Vector2.from_angle(TAU * float(i) / 6.0) * radius)
	draw_polyline(points, color, 1.0)


## Dark chains from the ground round a bound tower, pulled tight, with a violet seal under it.
func _draw_chains(tower: SimTower, left: float) -> void:
	var base := _tower_base(tower)
	var fade := clampf(left * 4.0, 0.0, 1.0)
	# The seal turns under the tower.
	for i in 6:
		var angle := TAU * float(i) / 6.0 + _time * 1.4
		var at := base + Vector2(cos(angle) * 15.0, sin(angle) * 6.0)
		draw_rect(Rect2(at.floor() - Vector2.ONE, Vector2(2, 2)), Color(CHAIN.lerp(Color.WHITE, 0.3), 0.9 * fade))
	_draw_ellipse(base, Vector2(15, 6), Color(CHAIN, 0.7 * fade))
	for k in 4:
		var angle := TAU * float(k) / 4.0 + PI * 0.25
		var anchor := base + Vector2(cos(angle) * 18.0, sin(angle) * 7.0)
		var grip := base + Vector2(cos(angle) * 5.0, -16.0 + sin(angle) * 2.0)
		var shake := Vector2(sin(_time * 30.0 + k) * 0.5, 0)
		var links := 7
		for j in links:
			var t := float(j) / float(links - 1)
			var at := anchor.lerp(grip, t) + shake
			var link := Vector2(2, 3) if j % 2 == 0 else Vector2(3, 2)
			draw_rect(Rect2(at.floor() - Vector2(1, 1), link), Color(CHAIN_DARK, 0.95 * fade))
			draw_rect(Rect2(at.floor() - Vector2(1, 1), Vector2(1, 1)), Color(CHAIN, 0.9 * fade))


func _draw_ellipse(center: Vector2, radius: Vector2, color: Color) -> void:
	var points := PackedVector2Array()
	for i in 33:
		var angle := TAU * float(i) / 32.0
		points.append(center + Vector2(cos(angle) * radius.x, sin(angle) * radius.y))
	draw_polyline(points, color, 1.0)


## A red mark that tightens on the doomed tower while the fireball flies: sell it now or lose it.
func _draw_target(tower: SimTower, left: float) -> void:
	if not sim.towers.has(tower):
		return
	var base := _tower_base(tower)
	var t := clampf(left / BossAbilities.FIREBALL_FLIGHT, 0.0, 1.0)
	var radius := Vector2(10.0 + 14.0 * t, 4.0 + 6.0 * t)
	var pulse := 0.6 + 0.4 * sin(_time * 18.0)
	_draw_ellipse(base, radius, Color(1.0, 0.15, 0.08, pulse))
	_draw_ellipse(base, radius * 0.6, Color(1.0, 0.5, 0.2, pulse * 0.7))
	for i in 4:
		var angle := TAU * float(i) / 4.0 + _time * 2.0
		var tick := base + Vector2(cos(angle) * radius.x, sin(angle) * radius.y)
		draw_line(tick, tick + (tick - base).normalized() * 4.0, Color(1.0, 0.2, 0.1, pulse), 1.0)


func _draw_fireball(at: Vector2) -> void:
	var flicker := 1.0 + 0.12 * sin(_time * 40.0)
	draw_circle(at, 9.0 * flicker, Color(EMBER, 0.35))
	draw_circle(at, 6.5 * flicker, Color(FIRE, 0.85))
	draw_circle(at, 4.0, Color(1.0, 0.75, 0.3))
	draw_circle(at + Vector2(-1, -1), 2.2, FIRE_CORE)


## A heap of broken stone where the tower stood, burning, with smoke rising from it.
func _draw_ruin(base: Vector2, salt: int) -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = salt
	draw_rect(Rect2(base + Vector2(-13, -3), Vector2(26, 6)), Color(0.08, 0.06, 0.06, 0.8))
	for i in 9:
		var at := base + Vector2(rng.randf_range(-11, 9), rng.randf_range(-8, 1))
		var size := Vector2(rng.randi_range(3, 6), rng.randi_range(2, 4))
		var shade := rng.randf_range(0.18, 0.34)
		draw_rect(Rect2(at.floor(), size), Color(shade, shade * 0.92, shade * 0.88))
		draw_rect(Rect2(at.floor(), Vector2(size.x, 1)), Color(shade + 0.12, shade + 0.1, shade + 0.08))
	# A broken stump of the tower.
	draw_rect(Rect2(base + Vector2(-4, -14), Vector2(7, 12)), Color(0.24, 0.21, 0.2))
	draw_rect(Rect2(base + Vector2(-4, -14), Vector2(2, 12)), Color(0.32, 0.29, 0.27))
	for i in 7:
		var rise := fposmod(_time * 1.3 + float(i) * 0.143 + float(salt) * 0.01, 1.0)
		var at := base + Vector2(sin(float(salt + i) * 2.1) * 9.0, -2.0 - rise * 22.0)
		var flame := FIRE_CORE.lerp(EMBER, rise)
		draw_rect(Rect2(at.floor(), Vector2(2.0 if rise < 0.3 else 1.0, 3.0 if rise < 0.5 else 2.0)), Color(flame, 1.0 - rise * 0.8))
	for i in 5:
		var rise := fposmod(_time * 0.35 + float(i) * 0.2 + float(salt) * 0.013, 1.0)
		var at := base + Vector2(sin(rise * 5.0 + float(i)) * 4.0 + rise * 8.0, -16.0 - rise * 40.0)
		var radius := 2.0 + rise * 5.0
		draw_circle(at, radius, Color(0.12, 0.1, 0.1, 0.45 * (1.0 - rise)))
