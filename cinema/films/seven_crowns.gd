extends RefCounted
## "War of Seven Crowns" story trailer (78 s), rebuilt in the cinematic kit.
## Same edit, voice lines and music as marketing/trailers-v2 (audio: the v2 trailer mix, hits at 18 and 70 s).
## Each shot is func(st: Stage, init: bool): build when init, animate from st.t (0..st.T) otherwise.

const RINGC := [Color8(255, 122, 58), Color8(200, 216, 255), Color8(138, 240, 80), Color8(74, 224, 224),
		Color8(232, 176, 64), Color8(176, 112, 255)]
const ORANGE := Color(1.0, 0.55, 0.2)
const VIOLET := Color(0.7, 0.45, 1.0)


func edit() -> Array:
	return [
		[0.0, 5.0, map_of_crowns],
		[5.0, 8.0, six_monarchs],
		[8.0, 10.0, the_burning],
		[10.0, 12.2, the_armies],
		[12.2, 14.4, called_it_peace],
		[14.4, 18.0, door_opens],
		[18.0, 24.0, king_rises],
		[24.0, 30.0, the_march],
		[30.0, 36.0, the_line],
		[36.0, 42.0, func(st, init): boss(st, init, "cassivane", "CASSIVANE DRAL", "The Ashen Regent", Color(1.0, 0.45, 0.25), Color(0.4, 0.13, 0.12), "embers")],
		[42.0, 44.0, func(st, init): boss(st, init, "vholt", "VHOLT", "Herald of the Storm", Color(0.75, 0.8, 1.0), Color(0.16, 0.2, 0.36), "storm")],
		[44.0, 46.0, func(st, init): boss(st, init, "ourra", "THE SALTMOTHER", "Herald of the Tide", Color(0.35, 0.7, 1.0), Color(0.08, 0.24, 0.36), "rain")],
		[46.0, 48.0, func(st, init): boss(st, init, "gorrath", "GORRATH", "Herald of the Stone", Color(0.95, 0.65, 0.35), Color(0.36, 0.24, 0.16), "embers")],
		[48.0, 51.0, func(st, init): boss(st, init, "sundered_heart", "THE SUNDERED HEART", "What the Regent became", Color(1.0, 0.75, 0.3), Color(0.28, 0.12, 0.28), "void")],
		[51.0, 54.0, the_heroes],
		[54.0, 58.5, refugees],
		[58.5, 62.0, ysolde_on_the_walls],
		[62.0, 66.0, light_falls],
		[66.0, 70.0, light_the_towers],
		[70.0, 78.0, title],
	]


# still-space (320x180 canvas) -> layer coordinates of a split still drawn with overscan 1.1
static func sp(x: float, y: float) -> Vector2:
	return Vector2((x * 2.0 - 320.0) * 1.1, (y * 2.0 - 180.0) * 1.1)


func _cam(st, k0: float, k1: float, c0: Vector2, c1: Vector2) -> void:
	var u: float = st.ease_io(st.t / st.T)
	st.k = lerp(k0, k1, u)
	st.cam = c0.lerp(c1, u)


# ------------------------------------------------------------------ 0-5 "Seven crowns once ruled the world."
func map_of_crowns(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_01", [0.92, 1.0])
		st.ambient = Color(0.9, 0.84, 0.78)
		var m: Node2D = L[0]
		st.v.candle = st.light(m, Vector2(-60, -30), Color(1.0, 0.7, 0.4), 0.5, 3.5, 60)
		st.v.glows = []
		for i in 6:
			var a0 := -PI / 2 + i * PI / 3
			var p := sp(160 + cos(a0) * 66, 90 + sin(a0) * 66 * 0.62)
			st.v.glows.append(st.glow(m, p, RINGC[i], 90, 0.0))
		st.v.mid = st.glow(m, sp(160, 90), Color(0.9, 0.85, 0.75), 70, 0.0)
		st.drift(L[1], Rect2(-340, -200, 680, 400), 70, Color(1.0, 0.85, 0.6, 0.35), 6.0, Vector2(4, -3), 1.0)
		return
	_cam(st, 1.0, 1.22, Vector2(0, 0), Vector2(0, 6))
	st.v.candle.energy = 0.45 + 0.08 * sin(st.t * 9.0) + 0.05 * sin(st.t * 23.0)
	for i in 6:
		var a: float = st.seg(st.t, 0.7 + i * 0.32, 1.2 + i * 0.32)
		st.v.glows[i].modulate.a = 0.55 * a * (0.85 + 0.15 * sin(st.t * 4.0 + i))
	st.v.mid.modulate.a = 0.25 * st.seg(st.t, 3.0, 4.0)
	st.fade = 1.0 - st.seg(st.t, 0.0, 0.9)
	st.subtitle("Seven crowns once ruled the world.", 1.0, 4.4)


# ------------------------------------------------------------------ 5-8 "Six of them..."
func six_monarchs(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_02", [0.15, 0.45, 1.0, 1.12])
		st.ambient = Color(0.9, 0.88, 0.95)
		st.v.g = []
		for i in 6:
			var x := 22 + i * 32
			st.v.g.append(st.glow(L[2], sp(x + 4, 84), RINGC[i], 60, 0.5))
			st.light(L[2], sp(x, 120), RINGC[i], 0.5, 1.2, 25)
		st.fog(L[1], Rect2(-360, 40, 720, 80), 0.35, Color(0.4, 0.35, 0.55), 3.0, 6.0)
		st.drift(L[3], Rect2(-360, -200, 720, 300), 50, Color(0.8, 0.75, 1.0, 0.6), 5.0, Vector2(3, -6), 1.2)
		st.glow(L[3], sp(276, 128), Color(0.5, 0.45, 0.8), 160, 0.25)
		return
	_cam(st, 1.12, 1.04, Vector2(-30, 10), Vector2(18, 4))
	for i in 6:
		st.v.g[i].modulate.a = 0.35 + 0.25 * sin(st.t * 5.0 + i * 1.3)
	st.subtitle("Six of them...", 0.5, 2.9)


# ------------------------------------------------------------------ 8-10 "...burned the seventh."
func the_burning(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_04", [0.08, 0.2, 0.55, 0.85, 1.1])
		st.ambient = Color(0.85, 0.8, 0.85)
		st.v.rift = L[1]
		var c: Node2D = L[3]
		st.v.fire = st.light(c, sp(160, 125), ORANGE, 1.2, 4.0, 25)
		st.v.fg = st.glow(c, sp(160, 128), Color(1.0, 0.5, 0.15), 200, 0.5, 0.6)
		st.drift(c, Rect2(sp(130, 100), Vector2(140, 60)), 120, Color(1.0, 0.6, 0.2, 1), 2.0, Vector2(0, -40), 1.8)
		st.v.ring = []
		for p in [Vector2(50, 120), Vector2(90, 142), Vector2(230, 142), Vector2(270, 120), Vector2(234, 96), Vector2(86, 96)]:
			st.v.ring.append(st.glow(L[4], sp(p.x, p.y), Color(1.0, 0.95, 0.8), 70, 0.4))
		st.v.tear = st.glow(L[1], sp(160, 18), Color(0.8, 0.8, 1.0), 120, 0.5)
		return
	_cam(st, 1.04, 1.16, Vector2(0, 16), Vector2(0, 30))
	st.v.rift.get_child(0).position.y = -26.0 * st.ease_out(st.t / st.T)   # the High King flung out through the stars
	st.v.fire.energy = 1.1 + 0.3 * sin(st.t * 13.0) + 0.15 * sin(st.t * 31.0)
	st.v.fg.modulate.a = 0.45 + 0.1 * sin(st.t * 11.0)
	for i in st.v.ring.size():
		st.v.ring[i].modulate.a = 0.35 + 0.25 * sin(st.t * 9.0 + i)
	st.v.tear.modulate.a = 0.4 + 0.3 * st.seg(st.t, 0.0, 1.5)
	st.shake_amount = 2.0
	st.subtitle("...burned the seventh.", 0.0, 1.8)


# ------------------------------------------------------------------ 10-12.2 "They locked him beyond the stars..."
func the_armies(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_03", [0.08, 0.3, 0.55, 0.8, 0.95, 1.15])
		st.ambient = Color(0.9, 0.82, 0.8)
		st.v.army = L[4]
		st.v.fl = []
		for x in [180, 230, 280]:
			st.v.fl.append(st.light(L[3], sp(x, 128), ORANGE, 0.9, 2.5, 20))
		st.glow(L[3], sp(240, 132), Color(1.0, 0.45, 0.12), 360, 0.35, 0.4)
		st.drift(L[5], Rect2(0, -200, 360, 340), 160, Color(1.0, 0.6, 0.2, 1), 3.0, Vector2(-10, -30), 1.6)
		st.drift(L[5], Rect2(-360, -200, 340, 340), 80, Color(0.75, 0.75, 0.8, 0.6), 4.0, Vector2(4, 10), 1.2, false)
		st.fog(L[2], Rect2(-360, 30, 720, 70), 0.4, Color(0.6, 0.35, 0.25), 3.0, 10.0)
		return
	_cam(st, 1.08, 1.16, Vector2(-36, 10), Vector2(30, 14))
	st.v.army.get_child(0).position.x = 10.0 * st.t / st.T
	for i in st.v.fl.size():
		st.v.fl[i].energy = 0.8 + 0.3 * sin(st.t * (11.0 + i * 3.0) + i)
	st.subtitle("They locked him beyond the stars...", 0.0, 2.2)


# ------------------------------------------------------------------ 12.2-14.4 "...and called it peace."
func called_it_peace(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_05", [0.08, 0.3, 0.6, 0.85, 1.0])
		st.ambient = Color(0.95, 0.9, 0.85)
		var h := sp(160, 94)
		st.v.rays = []
		for i in 7:
			var a := -PI / 2 + (i - 3) * 0.32
			var pl := Polygon2D.new()
			var d := Vector2(cos(a), sin(a))
			var n := d.orthogonal()
			pl.polygon = PackedVector2Array([h + n * 3, h - n * 3, h + d * 420 - n * 40, h + d * 420 + n * 40])
			pl.vertex_colors = PackedColorArray([Color(1, 0.9, 0.7, 0.3), Color(1, 0.9, 0.7, 0.3), Color(1, 0.8, 0.5, 0), Color(1, 0.8, 0.5, 0)])
			pl.material = st.add_mat()
			L[0].add_child(pl)
			st.v.rays.append(pl)
		st.v.heart = st.glow(L[4], h, Color(1.0, 0.95, 0.85), 70, 0.8)
		st.v.motes = []
		for i in 6:
			st.drift(L[4], Rect2(h + Vector2(-30, -30), Vector2(60, 60)), 10, RINGC[i], 1.8, Vector2(0, -15), 1.4, true, 180)
		st.drift(L[3], Rect2(-360, -200, 720, 300), 40, Color(1.0, 0.9, 0.7, 0.5), 6.0, Vector2(6, -2), 1.0)
		return
	_cam(st, 1.2, 1.02, Vector2(0, -24), Vector2(0, 0))
	for i in st.v.rays.size():
		st.v.rays[i].modulate.a = 0.6 + 0.4 * sin(st.t * 1.5 + i * 0.9)
	st.v.heart.modulate.a = 0.6 + 0.2 * sin(st.t * 6.0)
	st.subtitle("...and called it peace.", 0.0, 2.0)


# ------------------------------------------------------------------ 14.4-18 "Now the door is open."
func door_opens(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_07", [0.08, 0.3, 0.6, 0.85, 1.0])
		st.ambient = Color(0.8, 0.76, 0.95)
		var c := sp(166, 150)
		st.v.crack_l = st.light(L[3], c + Vector2(0, -10), VIOLET, 0.6, 4.0, 15)
		st.v.crack_g = st.glow(L[3], c, Color(0.75, 0.5, 1.0), 120, 0.5, 0.45)
		st.v.motes = st.drift(L[3], Rect2(c + Vector2(-60, -10), Vector2(120, 20)), 90, Color(0.8, 0.6, 1.0, 1), 2.4, Vector2(0, -45), 1.4)
		st.v.pil = []
		for p in [Vector2(64, 120), Vector2(102, 110), Vector2(236, 112), Vector2(276, 124), Vector2(134, 100), Vector2(204, 100)]:
			st.v.pil.append(st.glow(L[4], sp(p.x, p.y), RINGC[st.v.pil.size()], 40, 0.4))
		st.v.bolt = st.line(L[3], PackedVector2Array(), Color(0.9, 0.85, 1.0), 2.0)
		st.v.bolt_g = st.line(L[3], PackedVector2Array(), Color(0.6, 0.35, 1.0, 0.4), 8.0)
		st.v.c = c
		return
	_cam(st, 1.0, 1.5, Vector2(0, 0), Vector2(8, 72))
	var u: float = st.seg(st.t, 0.5, st.T)
	st.v.crack_l.energy = 0.6 + 2.2 * u * u
	st.v.crack_g.modulate.a = 0.5 + 0.5 * u
	st.v.crack_g.scale = Vector2.ONE * (120 + 160 * u * u) / 256.0 * Vector2(1, 0.45)
	for i in st.v.pil.size():
		st.v.pil[i].modulate.a = 0.3 + 0.3 * sin(st.t * 7.0 + i * 2.0) + 0.3 * u
	var on: bool = fmod(st.t, 0.7) < 0.12 and st.t > 1.5
	if on:
		var pts: PackedVector2Array = st.bolt_points(st.v.c, st.v.c + Vector2(-40 + 30 * sin(st.t * 3.0), -300), int(st.t * 10), 16, 10)
		st.v.bolt.points = pts
		st.v.bolt_g.points = pts
	st.v.bolt.visible = on
	st.v.bolt_g.visible = on
	st.light_flash = 0.8 if on else 0.0
	st.shake_amount = 4.0 * u
	st.flash = pow(st.seg(st.t, st.T - 0.5, st.T), 2) * 1.2
	st.flash_color = Color(0.8, 0.65, 1.0)
	st.subtitle("Now the door is open.", 0.3, 2.8)


# ------------------------------------------------------------------ 18-24 Vael-Orrun rises out of the Crack
func king_rises(st, init: bool) -> void:
	if init:
		st.ambient = Color(0.17, 0.18, 0.27)
		st.sky(st.layer(0.0), Color(0.008, 0.008, 0.025), Color(0.035, 0.04, 0.09), Color(0.13, 0.12, 0.22))
		var rl: Node2D = st.layer(0.08)
		var pts := PackedVector2Array()
		for i in 41:
			var a := float(i) / 40.0 * TAU
			var jag := 1.0 + 0.45 * sin(i * 2.7) * sin(i * 1.3)
			pts.append(Vector2(-30 + cos(a) * 95, -112 + sin(a) * 13 * jag * (1.0 - 0.6 * absf(cos(a)))))
		var rays := Polygon2D.new()
		rays.polygon = PackedVector2Array([Vector2(-100, -110), Vector2(40, -110), Vector2(260, 70), Vector2(-320, 70)])
		rays.vertex_colors = PackedColorArray([Color(0.6, 0.45, 1, 0.13), Color(0.6, 0.45, 1, 0.13), Color(0.5, 0.3, 0.9, 0), Color(0.5, 0.3, 0.9, 0)])
		rays.material = st.add_mat()
		rl.add_child(rays)
		var eye := Polygon2D.new()
		eye.polygon = pts
		eye.color = Color(0.03, 0.0, 0.06)
		eye.material = st.unshaded()
		rl.add_child(eye)
		st.v.rg = st.line(rl, pts, Color(0.6, 0.3, 1.0, 0.35), 7)
		st.line(rl, pts, Color(0.95, 0.85, 1.0), 1.6)
		st.v.rift_l = st.light(rl, Vector2(-30, -120), Color(0.55, 0.42, 1.0), 0.5, 9.0, 120)
		var far: Node2D = st.layer(0.22)
		st.ridge(far, -560, 560, -22, 26, Color(0.10, 0.105, 0.17), 11)
		st.fog(far, Rect2(-560, -60, 1120, 120), 0.4, Color(0.32, 0.36, 0.55), 4.0, 6.0)
		var mid: Node2D = st.layer(0.45)
		st.ridge(mid, -600, 600, 8, 18, Color(0.04, 0.042, 0.072), 23)
		for x in [-210, -150, 230, 300]:
			st.rect_poly(mid, Rect2(x, -40 - absi(x) % 30, 10 + absi(x) % 7, 60 + absi(x) % 30), Color(0.035, 0.035, 0.06), true)
		st.fog(mid, Rect2(-600, -30, 1200, 90), 0.5, Color(0.3, 0.33, 0.5), 3.0, 8.0)
		var vl: Node2D = st.layer(0.72)
		st.v.crack_l = st.light(vl, Vector2(185, 30), Color(0.7, 0.35, 1.0), 0.0, 5.5, 25)
		st.v.glow = st.glow(vl, Vector2(185, -80), Color(0.65, 0.4, 1.0), 420, 0.0, 1.4)
		st.v.rim = st.light(vl, Vector2(155, -110), Color(0.75, 0.5, 1.0), 0.0, 4.0, 6)
		st.v.king = st.actor(vl, "vael_orrun", "idle", 185, 300, 0.78 * 2.0 / 2.0 * 1.0, true)
		st.v.king.scale = Vector2(0.78, 0.78)
		st.v.motes = st.drift(vl, Rect2(145, -20, 80, 40), 70, Color(0.75, 0.5, 1.0, 0.9), 2.4, Vector2(0, -40), 1.2)
		st.v.motes.emitting = false
		st.rect_poly(vl, Rect2(-700, 44, 1400, 260), Color(0.13, 0.12, 0.16))
		st.v.cracks = []
		for i in 5:
			var p := PackedVector2Array()
			var x := 185.0
			var y := 45.0
			for j in 7:
				p.append(Vector2(x, y))
				x += (-1.0 + 0.5 * i) * 14 + sin(i * 7.3 + j * 2.1) * 8
				y += 2.0 + absf(sin(i * 3.1 + j)) * 3
			st.v.cracks.append(st.line(vl, p, Color(0.85, 0.6, 1.0, 1.0), 1.4))
		st.v.dust = st.burst(vl, Vector2(185, 44), Color(0.55, 0.45, 0.7), 260, 170, 110, 2.6, 2.0, false)
		st.fog(vl, Rect2(-600, 0, 1200, 80), 0.55, Color(0.35, 0.3, 0.55), 2.5, 10.0)
		var near: Node2D = st.layer(1.0)
		st.rect_poly(near, Rect2(-700, 104, 1400, 300), Color(0.11, 0.095, 0.1))
		st.fog(near, Rect2(-700, 70, 1400, 70), 0.5, Color(0.3, 0.3, 0.45), 2.0, 12.0)
		st.v.soldiers = []
		for i in 11:
			var front := i >= 6
			var s = st.actor(near, "soldier", "idle", -358 + (i - 6) * 52 if front else -390 + i * 50, 122 if front else 104, 2.0 if front else 1.7)
			s.modulate = Color(1, 1, 1) if front else Color(0.75, 0.75, 0.85)
			s.set_meta("x0", s.position.x)
			st.v.soldiers.append(s)
		st.v.torches = []
		for x in [-400, -265, -125]:
			st.line(near, PackedVector2Array([Vector2(x, 112), Vector2(x, 58)]), Color(0.12, 0.08, 0.06), 4.0, false)
			st.drift(near, Rect2(x - 3, 54, 6, 3), 60, Color(1.0, 0.7, 0.3, 1), 0.6, Vector2(0, -34), 4.5)
			st.glow(near, Vector2(x, 52), ORANGE, 40, 0.55)
			st.v.torches.append(st.light(near, Vector2(x, 50), Color(1.0, 0.52, 0.2), 1.7, 3.6, 30))
		st.drift(near, Rect2(-500, 20, 1000, 110), 140, Color(1.0, 0.55, 0.2, 0.95), 4.0, Vector2(5, -16), 1.6)
		var fg: Node2D = st.layer(1.45)
		var fpts := PackedVector2Array([Vector2(-640, 220)])
		for i in 64:
			fpts.append(Vector2(-640 + i * 20.0, 128 - absf(sin(i * 1.7)) * 14 - (16 if i % 7 == 0 else 0)))
		fpts.append(Vector2(640, 220))
		var fgp := Polygon2D.new()
		fgp.polygon = fpts
		fgp.color = Color(0.015, 0.01, 0.025)
		fgp.material = st.unshaded()
		fg.add_child(fgp)
		st.v.bolt = st.line(rl, PackedVector2Array(), Color(0.95, 0.9, 1.0), 1.4)
		st.v.bolt_g = st.line(rl, PackedVector2Array(), Color(0.6, 0.35, 1.0, 0.35), 6.0)
		return
	var t: float = st.t
	if t < 3.1:
		var a: float = st.ease_io(t / 3.1)
		st.cam = Vector2(-10, -40).lerp(Vector2(85, -70), a)
		st.k = lerp(1.1, 0.9, a)
	else:
		var a: float = st.ease_io((t - 3.1) / (st.T - 3.1))
		st.cam = Vector2(85, -70).lerp(Vector2(110, -96), a)
		st.k = lerp(0.9, 1.02, a)
	st.shake_amount = 16.0 * exp(-t * 3.0) + 2.0 * st.seg(t, 1.6, 1.7) * (1.0 - st.seg(t, 1.7, 2.1))
	var fl := 0.0
	for s0 in [0.0, 1.7, 4.9]:
		var d: float = t - s0
		if d >= 0.0 and d < 0.35:
			fl = maxf(fl, 1.0 if d < 0.07 else exp(-(d - 0.07) * 14.0))
			if d < 0.2:
				var pts: PackedVector2Array = st.bolt_points(Vector2(-40 + s0 * 10, -108), Vector2(200 if s0 == 0.0 else -150 + s0 * 60, 40), int(s0 * 100) + int(t * 30) % 3, 14, 12)
				st.v.bolt.points = pts
				st.v.bolt_g.points = pts
	st.v.bolt.visible = fl > 0.25
	st.v.bolt_g.visible = fl > 0.25
	st.light_flash = fl * 1.6
	var pulse := 0.75 + 0.25 * sin(t * 5.0) + 0.15 * sin(t * 13.0)
	st.v.rg.width = 6 + 3 * pulse + 6.0 * exp(-t * 0.6)
	st.v.rift_l.energy = 0.45 + 0.25 * pulse + fl
	for i in st.v.torches.size():
		st.v.torches[i].energy = 1.6 + 0.18 * sin(t * 11.0 + i * 37.0) + 0.1 * sin(t * 23.0 + i)
	for i in st.v.soldiers.size():
		var s = st.v.soldiers[i]
		st.pose(s, "idle", t + i * 0.33)
		s.position.x = float(s.get_meta("x0")) - 5.0 * (1.0 - exp(-t * 6.0))
	var rise: float = st.ease_out(t / 3.2)
	var k = st.v.king
	k.position = Vector2(185, 44 + (1.0 - rise) * 270 + sin(t * 1.7) * 1.5 * rise)
	if t >= 4.2:
		st.pose(k, "attack", t - 4.2, false)
	else:
		st.pose(k, "idle", t)
	st.v.glow.position = k.position + Vector2(0, -120)
	st.v.glow.modulate.a = clampf(rise * 1.2, 0.0, 1.0) * (0.8 + 0.2 * sin(t * 3.0))
	st.v.rim.position = k.position + Vector2(-30, -150)
	st.v.rim.energy = rise * 1.4
	var ce := 2.4 * exp(-t * 0.9) + 0.9
	st.v.crack_l.energy = ce * (0.9 + 0.1 * sin(t * 17.0))
	for c in st.v.cracks:
		c.default_color.a = clampf(ce * 0.6, 0.0, 1.0)
	st.fire(st.v.dust)
	st.v.motes.emitting = t >= 0.3
	st.ambient = Color(0.17, 0.18, 0.27).lerp(Color(0.24, 0.2, 0.34), clampf(ce * 0.35, 0.0, 1.0))
	st.flash = maxf(0.9 * exp(-t * 5.0), fl * 0.12)
	st.flash_color = Color(1, 0.95, 1)
	st.impact = t < 2.0 / 30.0
	st.aberr = 0.3 + 4.0 * exp(-t * 4.0)
	st.card("VAEL-ORRUN", "The High King returns", Color(0.75, 0.55, 1.0), 2.4, st.T - 0.1)


# ------------------------------------------------------------------ battlefield backdrop for the battle shots
func battlefield(st, dusk: float) -> Node2D:
	st.sky(st.layer(0.0), Color(0.02, 0.012, 0.04), Color(0.08, 0.05, 0.12), Color(0.26, 0.11, 0.16).lerp(Color(0.4, 0.18, 0.12), dusk), Vector2(0.3, 0.2), Color(0.35, 0.18, 0.6))
	var rl: Node2D = st.layer(0.06)
	st.glow(rl, Vector2(-120, -120), Color(0.6, 0.35, 1.0), 220, 0.5, 0.18)
	st.line(rl, st.bolt_points(Vector2(-190, -122), Vector2(-50, -118), 7, 4, 14), Color(0.9, 0.8, 1.0), 1.4)
	var far: Node2D = st.layer(0.25)
	st.ridge(far, -700, 900, -6, 22, Color(0.12, 0.08, 0.13), 3)
	st.fog(far, Rect2(-700, -40, 1600, 90), 0.4, Color(0.45, 0.25, 0.35), 4.0, 6.0)
	var mid: Node2D = st.layer(0.5)
	st.ridge(mid, -800, 1000, 20, 12, Color(0.06, 0.045, 0.07), 9)
	var gr: Node2D = st.layer(0.8)
	st.rect_poly(gr, Rect2(-900, 30, 2000, 300), Color(0.2, 0.16, 0.18))
	st.fog(gr, Rect2(-900, 10, 2000, 60), 0.45, Color(0.4, 0.3, 0.4), 3.0, 10.0)
	return gr


const HORDE := ["orc", "skeleton", "orc", "ghost", "skeleton", "orc"]
const DEFEND := ["soldier", "soldier", "elf", "soldier", "dwarf", "soldier", "elf"]


# ------------------------------------------------------------------ 24-30 the horde marches under the dragon
func the_march(st, init: bool) -> void:
	if init:
		st.ambient = Color(0.3, 0.27, 0.36)
		battlefield(st, 0.0)
		st.v.rows = []
		var rng := RandomNumberGenerator.new()
		rng.seed = 3
		var rows := [[0.82, 44.0, 1.5], [0.92, 74.0, 1.8], [1.05, 108.0, 2.2]]
		for r in rows.size():
			var lay: Node2D = st.layer(rows[r][0])
			for i in 15:
				var a = st.actor(lay, HORDE[(i + r) % 6], "walk", -470 + i * 72 + rng.randf_range(-10, 10), rows[r][1] + rng.randf_range(-3, 3), rows[r][2])
				a.set_meta("x0", a.position.x)
				a.set_meta("ph", rng.randf())
				if r == 2:
					a.modulate = Color(0.85, 0.82, 0.9)
				st.v.rows.append(a)
				if i % 4 == 1:
					var tl = st.light(lay, Vector2(a.position.x + 8, a.position.y - 50), Color(1.0, 0.5, 0.2), 0.9, 1.6, 25)
					tl.set_meta("x0", tl.position.x)
					st.drift(lay, Rect2(a.position.x + 6, a.position.y - 54, 4, 3), 20, Color(1.0, 0.65, 0.25, 1), 0.5, Vector2(0, -26), 3.0)
					st.v.rows.append(tl)
		var sky_l: Node2D = st.layer(0.65)
		st.v.dragon = st.actor(sky_l, "dragon", "walk", -400, -40, 2.2)
		st.v.dlight = st.light(sky_l, Vector2(-400, -100), ORANGE, 0.0, 4.0, 40)
		st.v.breath = st.drift(sky_l, Rect2(0, 0, 6, 6), 160, Color(1.0, 0.6, 0.2, 1), 0.9, Vector2(110, 170), 4.0, true, 12)
		st.v.breath.emitting = false
		st.drift(st.layer(1.2), Rect2(-500, -220, 1300, 400), 120, Color(0.7, 0.65, 0.7, 0.55), 6.0, Vector2(10, 14), 1.4, false)
		return
	var t: float = st.t
	st.cam = Vector2(lerp(-20.0, 140.0, t / st.T), lerp(-10.0, -24.0, st.ease_io(t / st.T)))
	st.k = lerp(1.0, 1.06, t / st.T)
	for n in st.v.rows:
		var x0: float = n.get_meta("x0")
		n.position.x = x0 + t * 26.0
		if n is Sprite2D:
			st.pose(n, "walk", t + float(n.get_meta("ph")))
	var d = st.v.dragon
	var dx: float = lerp(-420.0, 620.0, st.seg(t, 0.2, st.T))
	d.position = Vector2(dx, -36 + 10 * sin(t * 2.0))
	var breathing := t > 3.0 and t < 4.7
	st.pose(d, "attack" if breathing else "walk", t * 1.2)
	st.v.dlight.position = d.position + Vector2(90, -20)
	st.v.dlight.energy = 0.6 + (2.6 if breathing else 0.0)
	st.v.breath.position = d.position + Vector2(118, -48)
	st.v.breath.emitting = breathing
	st.light_flash = 0.15 if breathing else 0.0
	st.shake_amount = 1.5 if breathing else 0.4


# ------------------------------------------------------------------ 30-36 the defenders hold, orbs fire, the lines meet
func the_line(st, init: bool) -> void:
	if init:
		st.ambient = Color(0.32, 0.29, 0.38)
		var gr: Node2D = battlefield(st, 0.3)
		var towers: Node2D = st.layer(0.8)
		st.v.tops = []
		var els := ["fire", "storm", "water", "nature"]
		for i in 4:
			var x := 150 + i * 70
			st.rect_poly(towers, Rect2(x - 10, 10, 20, 34), Color(0.16, 0.14, 0.16), true)
			var o = st.actor(towers, "orb_" + els[i], "idle", x, 12, 1.4)
			o.set_meta("ph", i * 0.3)
			st.light(towers, Vector2(x, -30), st.EL[els[i]], 1.3, 2.5, 25)
			st.glow(towers, Vector2(x, -30), st.EL[els[i]], 60, 0.5)
			st.v.tops.append([o, Vector2(x, -36), els[i]])
		st.v.fighters = []
		var rng := RandomNumberGenerator.new()
		rng.seed = 5
		st.v.targets = []
		var rows := [[0.85, 52.0, 1.6], [0.95, 80.0, 1.9], [1.08, 112.0, 2.3]]
		for r in rows.size():
			var lay: Node2D = st.layer(rows[r][0])
			var meet := -40.0
			for i in 5:
				var x := meet - 30 - i * 64 - r * 14 + rng.randf_range(-6, 6)
				var a = st.actor(lay, HORDE[(i + r) % 6], "attack" if i == 0 else "walk", x, rows[r][1], rows[r][2])
				a.set_meta("role", "horde")
				a.set_meta("i", i)
				a.set_meta("dead", 1.2 + rng.randf() * 4.0 if i < 2 else 99.0)
				a.set_meta("x0", x)
				st.v.fighters.append(a)
				st.v.targets.append([lay, a])
			for i in 4:
				var x := meet + 26 + i * 54 + r * 10 + rng.randf_range(-6, 6)
				var kname: String = DEFEND[(i + r * 2) % DEFEND.size()]
				var a = st.actor(lay, kname, "attack" if i < 2 or kname == "elf" else "idle", x, rows[r][1], rows[r][2], true)
				a.set_meta("role", "def")
				a.set_meta("i", i)
				st.v.fighters.append(a)
		var fx: Node2D = st.layer(0.95)
		st.v.fx = fx
		st.v.bolts = []
		st.v.bursts = []
		for j in 14:
			var top = st.v.tops[j % 4]
			var tgt = st.v.targets[(j * 5) % st.v.targets.size()]
			var b1 = st.line(fx, PackedVector2Array(), st.EL[top[2]], 6.0)
			b1.modulate.a = 0.35
			var b2 = st.line(fx, PackedVector2Array(), Color(1, 1, 1), 2.0)
			var bl = st.light(fx, Vector2.ZERO, st.EL[top[2]], 0.0, 1.6, 20)
			var bu = st.burst(fx, Vector2.ZERO, st.EL[top[2]], 40, 90, 60, 0.8, 2.0)
			st.v.bolts.append([0.3 + j * 0.42, top, tgt, b1, b2, bl, bu])
		st.v.arrows = []
		for j in 24:
			st.v.arrows.append(st.line(fx, PackedVector2Array(), Color(0.85, 0.8, 0.7), 1.2, false))
		st.drift(st.layer(1.2), Rect2(-500, -200, 1000, 400), 120, Color(1.0, 0.55, 0.2, 0.9), 4.0, Vector2(6, -16), 1.6)
		return
	var t: float = st.t
	st.cam = Vector2(lerp(0.0, 30.0, t / st.T), lerp(-6.0, -14.0, t / st.T))
	st.k = lerp(1.05, 1.14, st.ease_io(t / st.T))
	st.shake_amount = 1.0
	for o in st.v.tops:
		st.pose(o[0], "idle", t + float(o[0].get_meta("ph")))
	for a in st.v.fighters:
		var i: int = a.get_meta("i")
		if a.get_meta("role") == "horde":
			var dead: float = a.get_meta("dead")
			if t > dead:
				st.pose(a, "death", t - dead, false)
			elif i == 0:
				st.pose(a, "attack", t + i * 0.2)
			else:
				st.pose(a, "walk", t + i * 0.2)
				a.position.x = float(a.get_meta("x0")) + minf(20.0, t * 10.0)
		else:
			st.pose(a, a.get_meta("anim"), t + i * 0.27)
	var fl := 0.0
	for b in st.v.bolts:
		var lt: float = t - b[0]
		var top = b[1]
		var tl: Node2D = b[2][0]
		var tgt: Sprite2D = b[2][1]
		var to: Vector2 = st.v.fx.to_local(tl.to_global(tgt.position + Vector2(0, -24)))
		var from: Vector2 = st.v.fx.to_local(top[0].get_parent().to_global(top[1]))
		if lt >= 0.0 and lt < 0.45:
			var p: float = lt / 0.45
			var head := from.lerp(to, p) + Vector2(0, -40 * sin(p * PI))
			var pts: PackedVector2Array
			if top[2] == "storm":
				pts = st.bolt_points(from, head, int(t * 30), 8, 8)
			else:
				pts = PackedVector2Array([from.lerp(head, 0.6), head])
			b[3].points = pts
			b[4].points = pts
			b[3].visible = true
			b[4].visible = true
			b[5].position = head
			b[5].energy = 1.2
		else:
			b[3].visible = false
			b[4].visible = false
			b[5].energy = maxf(0.0, 2.0 - (lt - 0.45) * 6.0) if lt >= 0.45 else 0.0
			if lt >= 0.45:
				b[5].position = to
				b[6].position = to
				st.fire(b[6])
				fl = maxf(fl, maxf(0.0, 0.3 - (lt - 0.45)))
	st.light_flash = fl
	for j in st.v.arrows.size():
		var p := fmod(t * 0.9 + j * 0.041, 1.0)
		var a := Vector2(260 + j * 3, -10)
		var b := Vector2(-160 - j * 7, 70)
		var q := a.lerp(b, p) + Vector2(0, -90 * sin(p * PI))
		var q2 := a.lerp(b, p + 0.02) + Vector2(0, -90 * sin((p + 0.02) * PI))
		st.v.arrows[j].points = PackedVector2Array([q, q + (q2 - q).normalized() * 8])


# ------------------------------------------------------------------ boss reveals
func boss(st, init: bool, name: String, title: String, sub: String, col: Color, sky_low: Color, fx: String) -> void:
	if init:
		st.ambient = Color(0.4, 0.37, 0.44)
		st.sky(st.layer(0.0), Color(0.015, 0.01, 0.025), sky_low * 0.35, sky_low, Vector2(0.5, 0.45), col * 0.35)
		var far: Node2D = st.layer(0.25)
		st.ridge(far, -600, 600, 10, 24, Color(sky_low.r * 0.35, sky_low.g * 0.35, sky_low.b * 0.4), 7)
		st.fog(far, Rect2(-600, -30, 1200, 90), 0.4, sky_low.lerp(Color.WHITE, 0.2), 3.5, 6.0)
		var bl: Node2D = st.layer(0.85)
		st.v.halo = st.glow(bl, Vector2(0, -120), col, 520, 0.35, 1.2)
		var meta: Dictionary = st._anim[name]
		var sc := clampf(300.0 / float(meta["feet"][1]), 1.1, 2.2)
		st.v.boss = st.actor(bl, name, "idle", 0, 128, sc)
		st.v.rim = st.light(bl, Vector2(40, -180), col, 1.4, 5.0, 8)
		st.v.key = st.light(bl, Vector2(-160, -120), Color(0.9, 0.85, 1.0), 0.6, 6.0, 80)
		st.rect_poly(bl, Rect2(-700, 126, 1400, 200), Color(0.16, 0.13, 0.15))
		st.fog(bl, Rect2(-700, 90, 1400, 70), 0.55, sky_low.lerp(Color.WHITE, 0.25), 2.5, 10.0)
		st.v.burst = st.burst(bl, Vector2(60, 40), col, 120, 200, 80, 1.3, 2.5)
		st.v.sc = sc
		var front: Node2D = st.layer(1.3)
		match fx:
			"embers":
				st.drift(front, Rect2(-500, -200, 1000, 400), 140, Color(1.0, 0.55, 0.2, 0.95), 4.0, Vector2(6, -18), 1.6)
			"void":
				st.drift(front, Rect2(-500, -200, 1000, 400), 120, Color(0.75, 0.5, 1.0, 0.9), 4.0, Vector2(0, -14), 1.6)
			"storm":
				st.drift(front, Rect2(-500, -200, 1000, 400), 220, Color(0.7, 0.75, 0.9, 0.5), 0.8, Vector2(-60, 420), 1.0, false, 4)
				st.v.bolt = st.line(far, PackedVector2Array(), Color(0.9, 0.95, 1.0), 1.6)
			"rain":
				st.drift(front, Rect2(-500, -200, 1000, 400), 260, Color(0.6, 0.75, 0.9, 0.45), 0.7, Vector2(-30, 460), 1.0, false, 3)
		return
	var t: float = st.t
	var T: float = st.T
	st.k = lerp(1.0, 1.1, st.ease_io(t / T))
	st.cam = Vector2(0, lerp(-10.0, -40.0, st.ease_io(t / T)))
	var at := T * 0.45
	if t < at:
		st.pose(st.v.boss, "idle", t)
	else:
		st.pose(st.v.boss, "attack", t - at, false)
	st.v.halo.modulate.a = 0.3 + 0.1 * sin(t * 4.0)
	st.v.rim.energy = 1.3 + 0.2 * sin(t * 6.0)
	if t > at + 0.35:
		var ft := t - at - 0.35
		st.fire(st.v.burst)
		st.flash = maxf(0.0, 0.5 - ft * 2.0)
		st.flash_color = col
		st.shake_amount = maxf(0.0, 9.0 - ft * 14.0)
		st.light_flash = maxf(0.0, 0.8 - ft * 3.0)
		st.aberr = 0.3 + maxf(0.0, 2.0 - ft * 6.0)
	if st.v.has("bolt"):
		var on := fmod(t, 0.9) < 0.1
		st.v.bolt.visible = on
		if on:
			st.v.bolt.points = st.bolt_points(Vector2(-200 + 160 * sin(t), -200), Vector2(-120 + 100 * sin(t * 2.0), 20), int(t * 20), 14, 10)
			st.light_flash = maxf(st.light_flash, 0.7)
	st.card(title, sub, col, 0.3, T - 0.05, 0.84)


# ------------------------------------------------------------------ 51-54 the heroes step into the light
const HEROES := ["kaela", "brannoc", "tamsin", "sylvaine", "gorrim", "mirelle"]


func the_heroes(st, init: bool) -> void:
	if init:
		st.ambient = Color(0.4, 0.36, 0.42)
		st.sky(st.layer(0.0), Color(0.04, 0.03, 0.07), Color(0.2, 0.1, 0.14), Color(0.5, 0.26, 0.16), Vector2(0.5, 0.75), Color(0.6, 0.35, 0.15))
		var far: Node2D = st.layer(0.3)
		st.ridge(far, -600, 600, 20, 22, Color(0.14, 0.09, 0.12), 3)
		st.fog(far, Rect2(-600, -10, 1200, 80), 0.4, Color(0.6, 0.4, 0.3), 3.0, 6.0)
		var hl: Node2D = st.layer(0.9)
		st.rect_poly(hl, Rect2(-700, 110, 1400, 200), Color(0.22, 0.18, 0.18))
		st.glow(hl, Vector2(0, -60), Color(1.0, 0.75, 0.45), 600, 0.25, 0.8)
		st.v.h = []
		for i in 6:
			var x := (i - 2.5) * 92.0
			var p = st.person(hl, HEROES[i], x, 116, 2.6, i >= 3)
			p.modulate.a = 0.0
			st.v.h.append(p)
			st.light(hl, Vector2(x - 30, -60), Color(1.0, 0.8, 0.55), 0.9, 1.8, 40)
		st.light(hl, Vector2(0, -260), Color(1.0, 0.75, 0.5), 1.0, 9.0, 140)
		st.fog(hl, Rect2(-700, 80, 1400, 60), 0.5, Color(0.6, 0.45, 0.35), 2.5, 8.0)
		st.drift(st.layer(1.2), Rect2(-500, -200, 1000, 400), 140, Color(1.0, 0.6, 0.25, 0.95), 4.0, Vector2(5, -18), 1.6)
		return
	var t: float = st.t
	st.k = lerp(1.0, 1.08, st.ease_io(t / st.T))
	st.cam = Vector2(0, lerp(-20.0, -30.0, t / st.T))
	for i in 6:
		var a: float = st.ease_io(st.seg(t, i * 0.12, 0.6 + i * 0.12))
		var p = st.v.h[i]
		p.modulate.a = a
		p.position.y = 116 + (1.0 - a) * 12
	st.card("SIXTEEN HEROES", "Rise with the Ring", Color(1.0, 0.75, 0.4), 0.4, st.T - 0.05, 0.84)


# ------------------------------------------------------------------ 54-58.5 "Every city we save... we lose."
func refugees(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_11", [0.08, 0.3, 0.5, 0.75, 1.0, 1.2])
		st.ambient = Color(0.9, 0.85, 0.82)
		st.v.fire = st.glow(L[0], sp(280, 90), Color(1.0, 0.45, 0.15), 260, 0.4, 0.5)
		for x in [260, 290, 310]:
			var smoke: CPUParticles2D = st.drift(L[1], Rect2(sp(x, 84), Vector2(10, 6)), 40, Color(0.2, 0.17, 0.18, 0.7), 6.0, Vector2(8, -22), 9.0, false, 15)
			smoke.scale_amount_curve = null
		st.v.lamp = st.glow(L[4], sp(76, 108), Color(1.0, 0.82, 0.45), 90, 0.6)
		st.v.lamp_l = st.light(L[4], sp(76, 108), Color(1.0, 0.8, 0.45), 0.8, 2.0, 25)
		st.drift(L[5], Rect2(-360, -220, 720, 400), 120, Color(0.75, 0.72, 0.72, 0.7), 6.0, Vector2(10, 16), 1.4, false)
		st.fog(L[2], Rect2(-360, -10, 720, 80), 0.4, Color(0.5, 0.42, 0.4), 3.0, 8.0)
		return
	_cam(st, 1.02, 1.16, Vector2(-34, 16), Vector2(40, 10))
	st.v.fire.modulate.a = 0.35 + 0.1 * sin(st.t * 7.0)
	st.v.lamp.modulate.a = 0.55 + 0.1 * sin(st.t * 9.0)
	st.v.lamp_l.energy = 0.8 + 0.1 * sin(st.t * 13.0)
	st.subtitle("Every city we save... we lose.", 0.8, 4.3)


# ------------------------------------------------------------------ 58.5-62 "We do not fight to win."
func ysolde_on_the_walls(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_12", [0.08, 0.3, 0.5, 0.85, 1.0])
		st.ambient = Color(0.95, 0.9, 0.86)
		var sun := sp(300, 112)
		st.v.rays = []
		for i in 6:
			var a := PI + (i - 2.5) * 0.12
			var d := Vector2(cos(a), sin(a))
			var n := d.orthogonal()
			var pl := Polygon2D.new()
			pl.polygon = PackedVector2Array([sun + n * 4, sun - n * 4, sun + d * 700 - n * 70, sun + d * 700 + n * 70])
			pl.vertex_colors = PackedColorArray([Color(1, 0.8, 0.55, 0.22), Color(1, 0.8, 0.55, 0.22), Color(1, 0.7, 0.4, 0), Color(1, 0.7, 0.4, 0)])
			pl.material = st.add_mat()
			L[0].add_child(pl)
			st.v.rays.append(pl)
		st.glow(L[0], sun, Color(1.0, 0.75, 0.45), 300, 0.45, 0.6)
		for x in [230, 262, 300]:
			st.drift(L[1], Rect2(sp(x, 110), Vector2(10, 6)), 40, Color(0.22, 0.18, 0.2, 0.6), 6.0, Vector2(10, -20), 9.0, false, 15)
		st.light(L[4], sp(130, 110), Color(1.0, 0.8, 0.6), 0.6, 2.5, 30)
		st.drift(L[4], Rect2(-360, -220, 720, 360), 60, Color(1.0, 0.85, 0.65, 0.5), 6.0, Vector2(14, -4), 1.0)
		return
	_cam(st, 1.16, 1.3, Vector2(-30, 26), Vector2(-46, 22))
	for i in st.v.rays.size():
		st.v.rays[i].modulate.a = 0.6 + 0.4 * sin(st.t * 1.2 + i)
	st.subtitle("We do not fight to win.", 0.4, 3.4)


# ------------------------------------------------------------------ 62-66 "We fight so that they may live."
func light_falls(st, init: bool) -> void:
	if init:
		var L: Array = st.still("night_of_falling_stars_09", [0.08, 0.3, 0.6, 0.9, 1.0])
		st.ambient = Color(0.85, 0.85, 0.95)
		st.v.white = L[4]
		st.v.white.modulate.a = 0.0
		st.v.star = st.line(L[0], PackedVector2Array(), Color(1.0, 0.97, 0.9), 3.0)
		st.v.star_g = st.glow(L[0], Vector2.ZERO, Color(1.0, 0.95, 0.85), 120, 0.0)
		st.v.face = st.light(L[3], sp(172, 120), Color(1.0, 0.95, 0.85), 0.0, 3.0, 40)
		st.drift(L[3], Rect2(-360, -220, 720, 300), 90, Color(1.0, 0.9, 0.7, 0.8), 3.0, Vector2(0, 20), 1.4)
		return
	var t: float = st.t
	_cam(st, 1.0, 1.2, Vector2(0, 10), Vector2(6, -10))
	var u: float = st.seg(t, 0.2, 1.8)
	var a := sp(260, -10)
	var b := sp(180, 60)
	var head := a.lerp(b, u)
	st.v.star.points = PackedVector2Array([a.lerp(b, maxf(u - 0.25, 0.0)), head])
	st.v.star_g.position = head
	st.v.star_g.modulate.a = 0.8 * u
	st.v.face.energy = 2.0 * st.seg(t, 1.0, 2.5)
	st.v.white.modulate.a = st.seg(t, 1.6, 3.2)
	st.flash = 0.6 * st.seg(t, 3.0, st.T)
	st.flash_color = Color(1, 0.98, 0.94)
	st.shake_amount = 3.0 * st.seg(t, 1.6, 2.0) * (1.0 - st.seg(t, 2.4, 3.2))
	st.subtitle("We fight so that they may live.", 0.4, 3.9)


# ------------------------------------------------------------------ 66-70 "Light the towers!"
const TOWERS6 := ["fire", "storm", "nature", "water", "earth", "void"]


func light_the_towers(st, init: bool) -> void:
	if init:
		var L: Array = st.still("prologue_05", [0.08, 0.3, 0.6, 0.85, 1.0])
		st.ambient = Color(0.42, 0.4, 0.52)
		st.v.sun = sp(160, 94)
		var fl: Node2D = st.layer(1.05)
		st.v.o = []
		for i in 6:
			var x := -280 + i * 112
			var el: String = TOWERS6[i]
			var o = st.actor(fl, "orb_" + el, "idle", x, 132, 1.8)
			var lt = st.light(fl, Vector2(x, 54), st.EL[el], 0.0, 2.6, 25)
			var g = st.glow(fl, Vector2(x, 54), st.EL[el], 90, 0.0)
			var beams := []
			for w in [[9.0, 0.3], [4.0, 0.7], [1.5, 1.0]]:
				var ln = st.line(fl, PackedVector2Array(), st.EL[el].lerp(Color.WHITE, 0.3 * w[1]), w[0])
				ln.modulate.a = w[1]
				beams.append(ln)
			st.v.o.append([o, lt, g, beams, Vector2(x, 50)])
		st.v.core = st.glow(L[4], st.v.sun, Color(1.0, 0.95, 0.8), 40, 0.8)
		st.v.core_l = st.light(L[4], st.v.sun, Color(1.0, 0.85, 0.6), 0.5, 6.0, 40)
		st.v.fl = fl
		return
	var t: float = st.t
	_cam(st, 1.0, 1.15, Vector2(0, 10), Vector2(0, -10))
	var sun_local: Vector2 = st.v.fl.to_local(st.layers[4][0].to_global(st.v.sun))
	for i in 6:
		var e = st.v.o[i]
		st.pose(e[0], "idle", t + i * 0.2)
		var on: float = st.ease_io(st.seg(t, 0.6 + i * 0.22, 0.9 + i * 0.22))
		e[1].energy = 1.6 * on
		e[2].modulate.a = 0.7 * on
		var p: float = st.ease_io(st.seg(t, 1.0 + i * 0.22, 1.6 + i * 0.22))
		for ln in e[3]:
			ln.visible = p > 0.0
			ln.points = PackedVector2Array([e[4], e[4].lerp(sun_local, p)])
	var u: float = st.seg(t, 2.2, st.T)
	st.v.core.scale = Vector2.ONE * (40 + 600 * u * u) / 256.0
	st.v.core.modulate.a = 0.8 + 0.2 * u
	st.v.core_l.energy = 0.5 + 1.5 * u
	st.flash = pow(u, 3) * 1.6
	st.flash_color = Color(1, 0.97, 0.9)
	st.shake_amount = 6.0 * u
	st.aberr = 0.3 + 2.0 * u
	st.subtitle("Light the towers!", 0.7, 3.0)


# ------------------------------------------------------------------ 70-78 the hit: title and call to action
func title(st, init: bool) -> void:
	if init:
		st.ambient = Color(1, 1, 1)
		st.plate("res://art/land/landing_logo_1920x1080.png", 1.0, 1.0 / 3.0 * 1.04)
		st.drift(st.layer(1.2), Rect2(-500, -220, 1000, 400), 100, Color(1.0, 0.6, 0.25, 0.9), 5.0, Vector2(5, -14), 1.4)
		return
	var t: float = st.t
	st.k = lerp(1.06, 1.0, st.ease_out(t / st.T))
	st.flash = maxf(0.0, 1.6 - t * 1.3)
	st.flash_color = Color(1.0, 0.97, 0.92)
	st.card("", "Wishlist on Steam", Color(1.0, 0.85, 0.55), 2.2, st.T - 0.6, 0.86)
	st.fade = st.seg(t, st.T - 1.0, st.T)
