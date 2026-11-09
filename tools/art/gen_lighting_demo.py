#!/usr/bin/env python3
"""Generates the pixel art for the Fire tower lighting test scene.

Every sprite comes with a normal map (OpenGL convention: green points up the screen), so Godot's
2D lights can shade it. Glowing pixels (coals, the window) go in a separate "glow" image that the
scene draws unshaded on top.

Writes to assets/art/lighting_demo/:
  ground.png / ground_n.png      the 640x360 field with the dirt road
  <sprite>.png / <sprite>_n.png  tower, rocks, bushes, grass tufts, slime frames
  tower_glow.png                 the tower's glowing pixels
  layout.json                    road points and where each prop sits (art pixels)

Run from the repository root:  python3 tools/art/gen_lighting_demo.py
Needs numpy and Pillow. The output is deterministic (fixed seed).
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
from PIL import Image

OUT = os.path.join("assets", "art", "lighting_demo")
W, H = 640, 360
RNG = np.random.default_rng(7)


def hexc(s: str) -> np.ndarray:
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32)


# ---------------------------------------------------------------- palette
GRASS = [hexc(c) for c in ("2f4a2c", "3b5a32", "4a6b3a", "5b7d40", "73944a")]
GRASS_TIP = hexc("8fae58")
DIRT = [hexc(c) for c in ("4d3626", "5e4430", "6f5139", "806043", "92714f")]
DIRT_EDGE = hexc("3d2b1f")
STONE = [hexc(c) for c in ("34313a", "47434a", "5a5560", "6f6a72", "88828a", "a39da2")]
MORTAR = hexc("26232b")
MOSS = [hexc(c) for c in ("2e4a2a", "3f6234", "557a3e")]
IRON = [hexc(c) for c in ("2a2629", "443d42", "62585d", "8a7e82")]
COAL = [hexc(c) for c in ("7a1d12", "c2401b", "f07a24", "ffc04a", "fff0a8")]
LEAF = [hexc(c) for c in ("22381f", "2f4c28", "3f6331", "537c3b", "6f9a46")]
BERRY = [hexc(c) for c in ("6e1a2a", "a8303a")]
ROCK = [hexc(c) for c in ("3a3740", "4c4851", "615c63", "7a747a", "958e92")]
LICHEN = hexc("7f8a4a")
SLIME = [hexc(c) for c in ("1d3a5c", "245a86", "2f7fb0", "54a8d4", "a8e0f0")]
FLOWER = [hexc(c) for c in ("e8d878", "d8dce8", "c87ab8")]


# ---------------------------------------------------------------- helpers
def value_noise(h: int, w: int, cell: float, rng: np.random.Generator) -> np.ndarray:
    """Smooth value noise in 0..1."""
    gh, gw = int(h / cell) + 3, int(w / cell) + 3
    grid = rng.random((gh, gw))
    ys = np.arange(h) / cell
    xs = np.arange(w) / cell
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = ys - y0
    fx = xs - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = grid[y0][:, x0]
    b = grid[y0][:, x0 + 1]
    c = grid[y0 + 1][:, x0]
    d = grid[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(h: int, w: int, cells: list[float], rng: np.random.Generator) -> np.ndarray:
    total = np.zeros((h, w))
    amp = 1.0
    norm = 0.0
    for cell in cells:
        total += value_noise(h, w, cell, rng) * amp
        norm += amp
        amp *= 0.5
    return total / norm


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def ramp_pick(ramp: list[np.ndarray], t: np.ndarray, dither: float = 0.0) -> np.ndarray:
    """Quantise t (0..1) onto a colour ramp, with optional ordered dithering between steps."""
    h, w = t.shape
    n = len(ramp)
    if dither > 0:
        b = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
        t = t + (b - 0.5) * dither / n
    idx = np.clip((t * n).astype(int), 0, n - 1)
    pal = np.stack(ramp)
    return pal[idx]


def normals_from_height(hgt: np.ndarray, strength: float) -> np.ndarray:
    """Normal map (x right, y up the screen, z out) from a height field."""
    dx = np.zeros_like(hgt)
    dy = np.zeros_like(hgt)
    dx[:, 1:-1] = (hgt[:, 2:] - hgt[:, :-2]) * 0.5
    dy[1:-1, :] = (hgt[2:, :] - hgt[:-2, :]) * 0.5
    n = np.stack([-dx * strength, dy * strength, np.ones_like(hgt)], axis=-1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


def encode_normals(n: np.ndarray, alpha: np.ndarray) -> np.ndarray:
    out = np.zeros(n.shape[:2] + (4,), dtype=np.uint8)
    out[..., :3] = np.clip((n * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)
    out[..., 3] = alpha
    return out


def save_rgba(name: str, rgb: np.ndarray, alpha: np.ndarray) -> None:
    out = np.zeros(rgb.shape[:2] + (4,), dtype=np.uint8)
    out[..., :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    out[..., 3] = alpha
    Image.fromarray(out, "RGBA").save(os.path.join(OUT, name + ".png"))


def save_sprite(name: str, rgb: np.ndarray, nrm: np.ndarray, alpha: np.ndarray) -> None:
    save_rgba(name, rgb, alpha)
    Image.fromarray(encode_normals(nrm, alpha), "RGBA").save(os.path.join(OUT, name + "_n.png"))


def outline(alpha: np.ndarray) -> np.ndarray:
    """Pixels just outside the shape (4-neighbour)."""
    a = alpha > 0
    grown = a.copy()
    grown[1:, :] |= a[:-1, :]
    grown[:-1, :] |= a[1:, :]
    grown[:, 1:] |= a[:, :-1]
    grown[:, :-1] |= a[:, 1:]
    return grown & ~a


def shade(normal: np.ndarray, light=(-0.45, 0.55, 0.7)) -> np.ndarray:
    l = np.array(light, dtype=np.float32)
    l /= np.linalg.norm(l)
    return np.clip((normal * l).sum(-1), 0, 1)


# ---------------------------------------------------------------- road
def catmull_rom(points: list[tuple[float, float]], samples: int = 24) -> np.ndarray:
    pts = np.array(points, dtype=np.float64)
    pts = np.vstack([pts[0] * 2 - pts[1], pts, pts[-1] * 2 - pts[-2]])
    out = []
    for i in range(1, len(pts) - 2):
        p0, p1, p2, p3 = pts[i - 1], pts[i], pts[i + 1], pts[i + 2]
        for s in range(samples):
            t = s / samples
            t2, t3 = t * t, t * t * t
            out.append(0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t2
                              + (-p0 + 3 * p1 - 3 * p2 + p3) * t3))
    out.append(pts[-2])
    return np.array(out)


ROAD_CONTROL = [(-24, 300), (110, 296), (190, 262), (222, 190), (262, 118), (330, 96), (402, 112),
                (446, 176), (478, 250), (552, 282), (664, 288)]
ROAD_HALF_WIDTH = 15.0
TOWER_POS = (326, 226)


def distance_to_polyline(px: np.ndarray, py: np.ndarray, line: np.ndarray) -> np.ndarray:
    best = np.full(px.shape, 1e9)
    for (ax, ay), (bx, by) in zip(line[:-1], line[1:]):
        vx, vy = bx - ax, by - ay
        ll = vx * vx + vy * vy
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / ll, 0, 1)
        dx = px - (ax + t * vx)
        dy = py - (ay + t * vy)
        best = np.minimum(best, np.sqrt(dx * dx + dy * dy))
    return best


# ---------------------------------------------------------------- ground
def make_ground(road: np.ndarray) -> None:
    rng = np.random.default_rng(11)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    dist = distance_to_polyline(xx, yy, road)
    wobble = (fbm(H, W, [9, 4], rng) - 0.5) * 7.0
    road_d = dist + wobble  # < half width means road
    on_road = road_d < ROAD_HALF_WIDTH
    edge = (road_d >= ROAD_HALF_WIDTH - 1.2) & on_road

    # Grass: patchy clusters of shade, lighter where the noise is high.
    patches = fbm(H, W, [28, 12, 6], rng)
    fine = value_noise(H, W, 2.2, rng)
    g = np.clip(patches * 0.85 + fine * 0.25 - 0.08, 0, 0.999)
    # Grass darkens near the road (worn, shaded by the verge).
    g -= np.clip(1.0 - (road_d - ROAD_HALF_WIDTH) / 6.0, 0, 1) * 0.25
    g = np.clip(g, 0, 0.999)
    rgb = ramp_pick(GRASS[:4], g, dither=0.35)
    height = g * 0.6

    # Little grass strokes: a dark root pixel and a light tip, two or three pixels tall.
    n_strokes = 3400
    sx = rng.integers(0, W, n_strokes)
    sy = rng.integers(3, H, n_strokes)
    for x, y in zip(sx, sy):
        if on_road[y, x] or road_d[y, x] < ROAD_HALF_WIDTH + 1:
            continue
        tall = 2 + (rng.random() < 0.4)
        lean = rng.choice([-1, 0, 0, 1])
        rgb[y, x] = GRASS[0]
        for k in range(1, tall + 1):
            xk = min(max(x + (lean if k == tall else 0), 0), W - 1)
            rgb[y - k, xk] = GRASS[3] if k < tall else GRASS_TIP
            height[y - k, xk] = 0.9
    # A few flowers.
    for _ in range(140):
        x, y = int(rng.integers(2, W - 2)), int(rng.integers(2, H - 2))
        if road_d[y, x] < ROAD_HALF_WIDTH + 3:
            continue
        col = FLOWER[int(rng.integers(0, len(FLOWER)))]
        rgb[y, x] = col
        rgb[y + 1, x] = GRASS[1]
        height[y, x] = 1.0

    # Road: dirt with ruts along its length and a dark lip at the grass edge.
    dirt_t = np.clip(fbm(H, W, [14, 6, 3], rng) * 0.9 + 0.08, 0, 0.999)
    rut = np.abs(np.abs(dist - 0.0) - 7.0) < 1.3
    dirt_t = np.where(rut & on_road, dirt_t - 0.22, dirt_t)
    dirt_t = np.clip(dirt_t, 0, 0.999)
    dirt_rgb = ramp_pick(DIRT, dirt_t, dither=0.5)
    rgb = np.where(on_road[..., None], dirt_rgb, rgb)
    rgb = np.where(edge[..., None], DIRT_EDGE, rgb)
    height = np.where(on_road, -0.6 + dirt_t * 0.3 - rut * 0.25, height)
    # Pebbles on the road.
    for _ in range(260):
        x, y = int(rng.integers(1, W - 2)), int(rng.integers(1, H - 2))
        if road_d[y, x] > ROAD_HALF_WIDTH - 3:
            continue
        rgb[y, x] = ROCK[3]
        rgb[y, x + 1] = ROCK[2]
        rgb[y + 1, x] = ROCK[1]
        rgb[y + 1, x + 1] = DIRT[0]
        height[y, x] += 0.8
        height[y, x + 1] += 0.6

    # Overhanging grass blades along the road edge.
    edge_pts = np.argwhere(edge)
    for y, x in edge_pts[rng.random(len(edge_pts)) < 0.35]:
        if y > 2:
            rgb[y, x] = GRASS[2]
            rgb[y - 1, x] = GRASS[3]
            height[y, x] = 0.4

    nrm = normals_from_height(height, 1.6)
    save_sprite("ground", rgb, nrm, np.full((H, W), 255, np.uint8))
    return dist


# ---------------------------------------------------------------- tower
def make_tower() -> dict:
    w, h = 48, 92
    cx = w / 2 - 0.5
    base_y = h - 6          # bottom of the plinth at the centre front
    rng = np.random.default_rng(3)
    rgb = np.zeros((h, w, 3), np.float32)
    nrm = np.zeros((h, w, 3), np.float32)
    nrm[..., 2] = 1
    alpha = np.zeros((h, w), np.uint8)
    glow = np.zeros((h, w, 4), np.uint8)
    hgt_detail = np.zeros((h, w), np.float32)
    tilt = 0.5  # how much a wall normal leans down the screen (3/4 view)

    def put(x, y, col, n, a=255):
        if 0 <= x < w and 0 <= y < h:
            rgb[y, x] = col
            nrm[y, x] = n / np.linalg.norm(n)
            alpha[y, x] = a

    def cylinder(radius, bottom, height, course_h, stone_w, ramp, moss_rows=0, seed=0):
        """Draws the front of a stone cylinder whose front-bottom point is at y=bottom."""
        r_rng = np.random.default_rng(seed)
        b = radius * 0.42
        stone_tone = r_rng.random((40, 60))
        for x in range(w):
            u = (x - cx) / radius
            if abs(u) > 1:
                continue
            curve = b * math.sqrt(max(0.0, 1 - u * u))
            theta = math.asin(max(-1.0, min(1.0, u)))
            arc = theta * radius
            y_bot = bottom - b + curve
            y_top = y_bot - height
            wall_n = np.array([math.sin(theta), -tilt * math.cos(theta), math.cos(theta)])
            for y in range(int(math.floor(y_top)), int(math.ceil(y_bot)) + 1):
                if y < y_top - 0.5 or y > y_bot + 0.5:
                    continue
                hv = y_bot - y  # height above the base along the wall
                course = int(hv // course_h)
                in_course = hv - course * course_h
                offset = (course % 2) * stone_w * 0.5
                sidx = int(math.floor((arc + offset + 40) / stone_w))
                in_stone = (arc + offset + 40) - sidx * stone_w
                tone = stone_tone[course % 40, sidx % 60]
                # Mortar on course boundaries and between stones; joints thin out near the sides.
                joint = in_course < 1.0 or (in_stone < 1.0 * max(0.35, math.cos(theta)))
                lit = 0.5 + 0.5 * (-0.55 * math.sin(theta) + 0.3)  # light from the upper left
                t = np.clip(0.18 + tone * 0.45 + lit * 0.35 - 0.12 * (in_course < 2), 0, 0.999)
                if joint:
                    col = MORTAR
                    n = wall_n.copy()
                else:
                    col = ramp[int(t * len(ramp))]
                    # Bevel: stone faces bulge a little at their edges.
                    n = wall_n.copy()
                    if in_course < 2.0:
                        n += np.array([0, -0.35 * math.cos(theta) * -1, 0])  # top of stone faces up
                    if in_course > course_h - 1.5:
                        n += np.array([0, -0.35, 0])
                    if in_stone < 2.0:
                        n += np.array([-0.3, 0, 0])
                    elif in_stone > stone_w - 1.5:
                        n += np.array([0.3, 0, 0])
                # Moss creeping up from the bottom.
                if moss_rows and hv < moss_rows and r_rng.random() < (1 - hv / moss_rows) * 0.7:
                    col = MOSS[int(r_rng.integers(0, 3))]
                # Edge darkening at the silhouette.
                if abs(u) > 0.88 and not joint:
                    col = col * 0.82
                put(x, y, col, n)

    def top_disc(radius, y_center, ramp, inner=0.0, seed=0):
        """A flat stone top seen from the 3/4 view (an ellipse), optionally with a hole in it."""
        b = radius * 0.42
        d_rng = np.random.default_rng(seed)
        for y in range(h):
            for x in range(w):
                u = (x - cx) / radius
                v = (y - y_center) / b
                rr = u * u + v * v
                if rr > 1:
                    continue
                if inner and rr < inner * inner:
                    continue
                n = np.array([0.0, 0.6, 0.8])
                t = 0.55 + 0.3 * (-u * 0.4 - v * 0.4) + d_rng.random() * 0.12
                col = ramp[int(np.clip(t, 0, 0.999) * len(ramp))]
                if rr > 0.8:
                    col = ramp[min(len(ramp) - 1, int(np.clip(t + 0.15, 0, 0.999) * len(ramp)))]
                put(x, y, col, n)

    # Battlement: back parapet, shaded walkway, then the outer wall and the front merlons.
    rim_r = 21
    rim_center = 32
    rb = rim_r * 0.42
    parapet = 5
    for x in range(w):
        u = (x - cx) / rim_r
        if abs(u) > 1:
            continue
        y_back = rim_center - rb * math.sqrt(1 - u * u)
        for y in range(int(round(y_back)) - parapet, int(round(y_back)) + 1):
            top = y == int(round(y_back)) - parapet
            col = STONE[4] if top else (STONE[2] if (x + y // 3) % 7 else MORTAR)
            put(x, y, col, np.array([0.0, 0.6, 0.8]) if top else np.array([-u * 0.5, -tilt, 0.85]))
    for y in range(h):
        for x in range(w):
            u = (x - cx) / (rim_r - 1.5)
            v = (y - rim_center) / (rb - 1.0)
            if u * u + v * v <= 1:
                col = STONE[1] if (x * 3 + y * 5) % 11 else STONE[0]
                put(x, y, col, np.array([0.0, 0.6, 0.8]))

    # Plinth, main tower body and the outer wall of the battlement.
    cylinder(radius=20, bottom=base_y, height=9, course_h=4.5, stone_w=9, ramp=STONE[:5], moss_rows=7, seed=1)
    cylinder(radius=17, bottom=base_y - 8, height=46, course_h=6, stone_w=10, ramp=STONE[1:], moss_rows=5, seed=2)
    cylinder(radius=rim_r, bottom=rim_center + rb + 8, height=8, course_h=8, stone_w=7, ramp=STONE[1:], seed=4)
    # Corbel shadow under the battlement.
    for x in range(w):
        u = (x - cx) / 17
        if abs(u) <= 1:
            yb = int(round(rim_center + 8 + 17 * 0.42 * math.sqrt(1 - u * u) - rim_r * 0.42 + (rim_r - 17) * 0.0)) + 1
            for k in range(2):
                if 0 <= yb + k < h and alpha[yb + k, x]:
                    rgb[yb + k, x] *= 0.55

    # Front merlons: the outer wall rises above the walkway in teeth, with gaps (crenels) between.
    for x in range(w):
        u = (x - cx) / rim_r
        if abs(u) > 1:
            continue
        theta = math.asin(u)
        arc = theta * rim_r + 40
        y_front = rim_center + rb * math.sqrt(1 - u * u)
        tooth = int(arc // 6) % 2 == 0
        rise = parapet if tooth else 1
        for k in range(rise + 1):
            y = int(round(y_front)) - k
            if k == rise:
                col = STONE[5] if u < 0.3 else STONE[4]
                n = np.array([0.0, 0.6, 0.8])
            else:
                col = STONE[3] if u < 0.2 else STONE[2]
                n = np.array([math.sin(theta), -tilt * math.cos(theta), math.cos(theta)])
            if tooth and (arc % 6) < 0.9:
                col = MORTAR
            put(x, y, col, n)

    # Iron brazier bowl on a short post, coals glowing inside.
    bowl_cy = 13
    bowl_r = 10
    # Three splayed legs down to the walkway.
    for lx, spread in ((-5, -1), (0, 0), (5, 1)):
        for y in range(bowl_cy + 6, rim_center + 3):
            k = (y - bowl_cy - 6) / 10
            x = int(round(cx + lx + spread * k * 3))
            put(x, y, IRON[2] if spread <= 0 else IRON[1], np.array([0.3 * spread, -0.3, 0.9]))
            put(x + 1, y, IRON[0], np.array([0.5, -0.3, 0.8]))
    # The bowl: a riveted iron half-dome.
    for x in range(w):
        u = (x - cx) / bowl_r
        if abs(u) > 1:
            continue
        depth = 8 * math.sqrt(1 - u * u)
        for y in range(bowl_cy, int(bowl_cy + depth) + 1):
            k = (y - bowl_cy) / max(depth, 1)
            n = np.array([u * 0.8, -0.6 * k, 0.7])
            lit = -u * 0.5 - k * 0.6 + 0.6
            col = IRON[3] if lit > 0.75 else IRON[2] if lit > 0.3 else IRON[1]
            if y == int(bowl_cy + depth):
                col = IRON[0]
            if y == bowl_cy + 4 and int(round(x - cx)) % 4 == 0:
                col = IRON[3]  # rivets
            put(x, y, col, n)
    # Bowl mouth: an ellipse of coals, ringed by a bright iron lip.
    for y in range(h):
        for x in range(w):
            u = (x - cx) / bowl_r
            v = (y - bowl_cy) / (bowl_r * 0.42)
            rr = u * u + v * v
            if rr > 1:
                continue
            if rr > 0.72:
                put(x, y, IRON[3] if v < 0 else IRON[2], np.array([0, 0.6, 0.8]))
            else:
                heat = (1 - rr) * 0.8 + rng.random() * 0.35
                c = COAL[int(np.clip(heat, 0, 0.999) * len(COAL))]
                put(x, y, c * 0.6, np.array([0, 0.6, 0.8]))
                glow[y, x, :3] = np.clip(c, 0, 255).astype(np.uint8)
                glow[y, x, 3] = 255

    # A glowing arrow slit in the front of the tower.
    sx = int(round(cx))
    for y in range(52, 64):
        for x in (sx - 1, sx, sx + 1):
            put(x, y, IRON[0], np.array([0, -tilt, 0.85]))
        if 54 <= y <= 62:
            c = COAL[3] if y > 56 else COAL[2]
            glow[y, sx, :3] = c.astype(np.uint8)
            glow[y, sx, 3] = 255
    for x in (sx - 2, sx + 2):
        for y in range(51, 64):
            put(x, y, STONE[4] if x < sx else STONE[1], np.array([0.5 * np.sign(x - sx), -tilt, 0.8]))

    # Ivy on the left flank.
    for _ in range(70):
        y = int(rng.integers(44, 84))
        spread = (y - 40) / 44
        x = int(cx - 17 + rng.integers(0, int(3 + 6 * spread)))
        if alpha[y, x]:
            put(x, y, LEAF[int(rng.integers(1, 5))], np.array([-0.4, 0.2, 0.9]))

    # Dark outline around the whole sprite (selective outline: darker at the bottom).
    ring = outline(alpha)
    ys, xs = np.nonzero(ring)
    for y, x in zip(ys, xs):
        put(x, y, hexc("17151b"), np.array([0, 0, 1.0]))

    save_sprite("tower", rgb, nrm, alpha)
    Image.fromarray(glow, "RGBA").save(os.path.join(OUT, "tower_glow.png"))
    # Where the fire sits, relative to the sprite's bottom centre.
    return {"size": [w, h], "fire": [0, bowl_cy - h + 1], "slit": [0, 58 - h], "base_offset": 6}


# ---------------------------------------------------------------- rocks, bushes, tufts, slime
def make_rock(name: str, w: int, h: int, seed: int) -> None:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    u = (xx - (w - 1) / 2) / (w / 2 - 0.5)
    v = (yy - (h - 1) * 0.55) / (h * 0.55)
    bump = (fbm(h, w, [4, 2], rng) - 0.5) * 0.5
    rr = u * u + v * v + bump * 0.6
    mask = rr < 1
    hgt = np.sqrt(np.clip(1 - rr, 0, 1)) * (w * 0.35)
    # Facets: quantise the height so the rock reads as chunky planes.
    hgt = np.round(hgt / 2.0) * 2.0 + bump * 2
    nrm = normals_from_height(hgt, 0.9)
    t = shade(nrm) * 0.75 + rng.random((h, w)) * 0.15
    rgb = ramp_pick(ROCK, np.clip(t, 0, 0.999))
    lich = (fbm(h, w, [3], rng) > 0.68) & (nrm[..., 1] > 0.1)
    rgb[lich & mask] = LICHEN
    alpha = (mask * 255).astype(np.uint8)
    ring = outline(alpha)
    rgb[ring] = hexc("1a181e")
    alpha[ring] = 255
    nrm[ring] = (0, 0, 1)
    save_sprite(name, rgb, nrm, alpha)


def make_bush(name: str, w: int, h: int, seed: int, berries: bool) -> None:
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    hgt = np.full((h, w), -1.0)
    nx = np.zeros((h, w))
    ny = np.zeros((h, w))
    blobs = []
    for _ in range(9):
        r = rng.uniform(w * 0.17, w * 0.26)
        bx = rng.uniform(r, w - r)
        by = rng.uniform(r + h * 0.15, h - r)
        blobs.append((bx, by, r))
    blobs.sort(key=lambda b: b[1])
    for bx, by, r in blobs:
        d2 = ((xx - bx) ** 2 + (yy - by) ** 2) / (r * r)
        inside = d2 < 1
        z = np.sqrt(np.clip(1 - d2, 0, 1)) * r + by * 0.4
        take = inside & (z > hgt)
        hgt[take] = z[take]
        nx[take] = ((xx - bx) / r)[take]
        ny[take] = (-(yy - by) / r)[take]
    mask = hgt > -1
    nz = np.sqrt(np.clip(1 - nx * nx - ny * ny, 0.05, 1))
    nrm = np.stack([nx, ny, nz], -1)
    leaf_noise = value_noise(h, w, 1.6, rng)
    nrm[..., 0] += (leaf_noise - 0.5) * 0.5
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    t = shade(nrm) * 0.8 + (leaf_noise - 0.5) * 0.35 + 0.1
    rgb = ramp_pick(LEAF, np.clip(t, 0, 0.999), dither=0.4)
    if berries:
        for _ in range(7):
            ys, xs = np.nonzero(mask)
            i = rng.integers(0, len(ys))
            y, x = ys[i], xs[i]
            rgb[y, x] = BERRY[1]
            if y + 1 < h and mask[y + 1, x]:
                rgb[y + 1, x] = BERRY[0]
    alpha = (mask * 255).astype(np.uint8)
    ring = outline(alpha)
    rgb[ring] = hexc("152012")
    alpha[ring] = 255
    nrm[ring] = (0, 0, 1)
    save_sprite(name, rgb, nrm, alpha)


def make_tuft(name: str, seed: int) -> None:
    rng = np.random.default_rng(seed)
    w, h = 11, 10
    rgb = np.zeros((h, w, 3))
    alpha = np.zeros((h, w), np.uint8)
    nrm = np.zeros((h, w, 3))
    nrm[..., 2] = 1
    for b in range(7):
        x0 = 2 + b + int(rng.integers(-1, 1))
        tall = int(rng.integers(5, 10))
        lean = rng.uniform(-0.45, 0.45) + (b - 3) * 0.12
        for k in range(tall):
            y = h - 1 - k
            x = int(round(x0 + lean * k))
            if 0 <= x < w and 0 <= y < h:
                t = k / tall
                col = GRASS[min(4, 1 + int(t * 4))] if k < tall - 1 else GRASS_TIP
                rgb[y, x] = col
                alpha[y, x] = 255
                nrm[y, x] = (lean * 0.5, 0.35, 0.85)
    nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
    save_sprite(name, rgb, nrm, alpha)


def make_slime_frames() -> None:
    w, h = 18, 16
    for f, (sx, sy) in enumerate([(1.0, 1.0), (1.08, 0.88), (0.94, 1.1), (1.02, 0.96)]):
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        rx, ry = 7.5 * sx, 6.5 * sy
        cy = h - 1 - ry * 0.95
        u = (xx - (w - 1) / 2) / rx
        v = (yy - cy) / ry
        v = np.where(v > 0, v * 1.5, v)  # flatter bottom
        rr = u * u + v * v
        mask = rr < 1
        nz = np.sqrt(np.clip(1 - rr, 0.04, 1))
        nrm = np.stack([u, -v, nz], -1)
        nrm /= np.linalg.norm(nrm, axis=-1, keepdims=True)
        t = shade(nrm) * 0.9 + 0.05
        rgb = ramp_pick(SLIME[:4], np.clip(t, 0, 0.999))
        # Specular highlight and eyes.
        hx, hy = int(round((w - 1) / 2 - rx * 0.4)), int(round(cy - ry * 0.45))
        rgb[hy, hx] = SLIME[4]
        rgb[hy, hx + 1] = SLIME[4]
        rgb[hy + 1, hx] = SLIME[3]
        ey = int(round(cy - ry * 0.05))
        for ex in (int((w - 1) / 2 - 2), int((w - 1) / 2 + 2)):
            rgb[ey, ex] = hexc("0b1220")
            rgb[ey - 1, ex] = hexc("0b1220")
        alpha = (mask * 255).astype(np.uint8)
        ring = outline(alpha)
        rgb[ring] = hexc("0e1b2c")
        alpha[ring] = 255
        nrm[ring] = (0, 0, 1)
        save_sprite(f"slime_{f}", rgb, nrm, alpha)


# ---------------------------------------------------------------- layout
def make_layout(road: np.ndarray) -> dict:
    rng = np.random.default_rng(21)
    props = []
    taken = [(TOWER_POS[0], TOWER_POS[1], 30)]

    def free(x, y, r):
        d = distance_to_polyline(np.array([x], float), np.array([y], float), road)[0]
        if d < ROAD_HALF_WIDTH + r + 2:
            return False
        return all((x - tx) ** 2 + (y - ty) ** 2 > (r + tr) ** 2 for tx, ty, tr in taken)

    def scatter(kinds, count, radius, margin=8):
        placed = 0
        tries = 0
        while placed < count and tries < count * 200:
            tries += 1
            x = float(rng.uniform(margin, W - margin))
            y = float(rng.uniform(margin + 10, H - 2))
            if free(x, y, radius):
                kind = kinds[int(rng.integers(0, len(kinds)))]
                props.append({"kind": kind, "pos": [round(x), round(y)], "flip": bool(rng.random() < 0.5)})
                taken.append((x, y, radius))
                placed += 1

    # A ring of rocks and bushes around the tower's foot, then the rest of the field.
    for ang, kind in [(2.5, "rock_a"), (0.35, "bush_b"), (1.2, "rock_c"), (-2.8, "bush_a")]:
        x = TOWER_POS[0] + math.cos(ang) * 36
        y = TOWER_POS[1] + math.sin(ang) * 18 + 4
        props.append({"kind": kind, "pos": [round(x), round(y)], "flip": False})
        taken.append((x, y, 8))
    scatter(["bush_a", "bush_b"], 9, 12)
    scatter(["rock_a", "rock_b", "rock_c"], 10, 8)
    scatter(["tuft_a", "tuft_b", "tuft_c"], 70, 4, margin=4)
    return {"props": props}


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    road = catmull_rom(ROAD_CONTROL)
    make_ground(road)
    tower = make_tower()
    make_rock("rock_a", 18, 13, 1)
    make_rock("rock_b", 11, 8, 2)
    make_rock("rock_c", 14, 11, 3)
    make_bush("bush_a", 26, 22, 4, berries=False)
    make_bush("bush_b", 20, 17, 5, berries=True)
    for i, name in enumerate(["tuft_a", "tuft_b", "tuft_c"]):
        make_tuft(name, 30 + i)
    make_slime_frames()
    layout = make_layout(road)
    layout["size"] = [W, H]
    layout["road"] = [[round(float(x), 1), round(float(y), 1)] for x, y in road[::3]]
    layout["road_half_width"] = ROAD_HALF_WIDTH
    layout["tower"] = {"pos": list(TOWER_POS), **tower}
    with open(os.path.join(OUT, "layout.json"), "w") as fh:
        json.dump(layout, fh, indent=1)
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
