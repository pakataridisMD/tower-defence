#!/usr/bin/env python3
"""Generates the in-game pixel art: tower, enemy and prop sprites, and each map's ground.

Same look as the lighting test (tools/art/gen_lighting_demo.py): detailed top-down pixel art in the
spirit of Graveyard Keeper, where every sprite has a normal map (OpenGL convention, green points up
the screen) so Godot's 2D lights shade it, and glowing pixels go in a separate "_glow" image that the
game draws unshaded.

One art pixel is drawn as 2x2 screen pixels, so a 64 px map cell is 32 art pixels.

Writes to assets/art/game/:
  towers/<tower_id>.png, _n.png, _glow.png    one per tower in data/towers
  enemies/<enemy_id>_<frame>.png, _n.png       body frames, drawn light so the game can tint them
  enemies/<enemy_id>_gear_<frame>.png, _n.png  untinted parts (eyes, armour, crowns)
  props/<prop>.png, _n.png                     grass tufts, stones, mushrooms, bushes
  ground/<map_id>.png, _n.png                  the whole board, road included
  ground/<map_id>.json                         where the props sit, by cell
  art.json                                     anchors, light colours and muzzle points

Run from the repository root:  python3 tools/art/gen_game_art.py
Needs numpy and Pillow. The output is deterministic.
"""
from __future__ import annotations

import glob
import json
import math
import os
import re
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_lighting_demo import (  # noqa: E402  (shared palette and helpers)
    BERRY, COAL, DIRT, DIRT_EDGE, FLOWER, GRASS, GRASS_TIP, IRON, LEAF, LICHEN, MORTAR, MOSS, ROCK,
    STONE, encode_normals, fbm, hexc, normals_from_height, outline, ramp_pick, shade, value_noise,
)

OUT = os.path.join("assets", "art", "game")
ART_SCALE = 2  # screen pixels per art pixel
INK = hexc("17151b")

WOOD = [hexc(c) for c in ("2b1d18", "3d2a20", "54392a", "6e4c35", "8a6444")]
COPPER = [hexc(c) for c in ("3a2218", "6a3a22", "9a5a2e", "c8803e", "e8b070")]
SPARK = [hexc(c) for c in ("6a5a20", "c8a83a", "f2d060", "fff0a0", "ffffff")]
PLASMA = [hexc(c) for c in ("7a1d40", "d0406a", "ff8a5a", "ffd08a", "fff6e0")]
SEED = [hexc(c) for c in ("2a5a1a", "5aa02a", "9ae04a", "d8ff8a")]
SLIME_BODY = [hexc(c) for c in ("3a4250", "6a7484", "a0a8b4", "d2d8de", "f4f6f8")]
MUSHROOM = [hexc(c) for c in ("6a2a3a", "a8404a", "d86a5a")]
GLOWCAP = [hexc(c) for c in ("2a6a6a", "4ac0b0", "9af0e0")]
WATER = [hexc(c) for c in ("12304e", "1d4f7a", "2f7fb0", "54a8d4", "a8e0f0", "eafaff")]
SANDSTONE = [hexc(c) for c in ("3e2f26", "56423a", "6e5848", "8a725a", "a68e70", "c4ae8c")]
AMBER = [hexc(c) for c in ("6a3a10", "b06a1a", "e8a030", "ffd070", "fff2c0")]
OBSIDIAN = [hexc(c) for c in ("120f1a", "1d1828", "2a2338", "3a3050", "4e4268", "6a5a88")]
VOID = [hexc(c) for c in ("2a1048", "5a2a98", "8e5cd9", "c8a0ff", "f4e8ff")]
SOUL = [hexc(c) for c in ("3a0f5a", "7a2ab0", "b25af0", "e0a8ff", "fff0ff")]
CLOUD = [hexc(c) for c in ("3a4250", "56607a", "7a86a0", "a8b4c8", "d8e0ec")]
EMBER_LEAF = [hexc(c) for c in ("3a1a10", "6a2a14", "a8401a", "e07a2a", "ffc04a")]
BLIGHT = [hexc(c) for c in ("1e1228", "34204a", "4e2e6a", "6e4890", "9a70b8")]
ABYSS = [hexc(c) for c in ("0a0f22", "121c3e", "1e2e5e", "34508a", "6a84c0", "b0c4f0")]
MUD = [hexc(c) for c in ("231a14", "33261c", "463426", "5a4632", "6e5a40")]
BOG = [hexc(c) for c in ("1a3a2a", "2a5a3a", "3f7a48", "6aa85a", "b0e08a")]


# ---------------------------------------------------------------- a sprite canvas
class Canvas:
    """RGB, normals, alpha and glow for one sprite, with drawing helpers for the 3/4 view."""

    TILT = 0.5  # how far a wall's normal leans down the screen

    def __init__(self, w: int, h: int, seed: int = 0):
        self.w, self.h = w, h
        self.rgb = np.zeros((h, w, 3), np.float32)
        self.nrm = np.zeros((h, w, 3), np.float32)
        self.nrm[..., 2] = 1
        self.alpha = np.zeros((h, w), np.uint8)
        self.glow = np.zeros((h, w, 4), np.uint8)
        self.rng = np.random.default_rng(seed)

    def put(self, x, y, col, n=(0.0, 0.0, 1.0), glow=None) -> None:
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            n = np.asarray(n, np.float32)
            self.rgb[y, x] = col
            self.nrm[y, x] = n / max(1e-6, float(np.linalg.norm(n)))
            self.alpha[y, x] = 255
            if glow is not None:
                self.glow[y, x, :3] = np.clip(glow, 0, 255).astype(np.uint8)
                self.glow[y, x, 3] = 255

    def wall_normal(self, u: float) -> np.ndarray:
        theta = math.asin(max(-1.0, min(1.0, u)))
        return np.array([math.sin(theta), -self.TILT * math.cos(theta), math.cos(theta)])

    def cylinder(self, cx, bottom, height, radius, ramp, *, top_radius=None, course_h=4.0, stone_w=6.0,
                 texture="stone", moss_rows=0, seed=0) -> None:
        """The front of an upright cylinder (or a taper, with top_radius) whose front-bottom point is at y=bottom."""
        rng = np.random.default_rng(seed)
        tone = rng.random((64, 64))
        top_radius = radius if top_radius is None else top_radius
        max_r = max(radius, top_radius)
        for x in range(self.w):
            for y in range(self.h):
                # Height above the base along the wall, for this column: solve per pixel since the radius varies.
                dx = x - cx
                found = None
                for hv in np.arange(0, height + 0.01, 0.5):
                    r = radius + (top_radius - radius) * (hv / max(height, 1e-6))
                    if abs(dx) > r + 0.25:
                        continue
                    u = max(-1.0, min(1.0, dx / max(r, 0.5)))
                    yy = bottom - r * 0.42 + r * 0.42 * math.sqrt(max(0.0, 1 - u * u)) - hv
                    if abs(yy - y) <= 0.5:
                        found = (hv, r, u)
                        break
                if found is None:
                    continue
                hv, r, u = found
                theta = math.asin(u)
                arc = theta * r
                n = self.wall_normal(u)
                lit = 0.5 + 0.5 * (-0.55 * math.sin(theta) + 0.3)
                if texture == "stone":
                    course = int(hv // course_h)
                    in_course = hv - course * course_h
                    offset = (course % 2) * stone_w * 0.5
                    s = arc + offset + 40
                    sidx = int(s // stone_w)
                    in_stone = s - sidx * stone_w
                    t = tone[course % 64, sidx % 64]
                    joint = in_course < 1.0 or in_stone < max(0.35, math.cos(theta))
                    if joint:
                        col = MORTAR
                    else:
                        v = np.clip(0.15 + t * 0.45 + lit * 0.35 - 0.1 * (in_course < 1.8), 0, 0.999)
                        col = ramp[int(v * len(ramp))]
                        if in_course < 1.8:
                            n = n + np.array([0, 0.35, 0])
                        if in_stone < 1.6:
                            n = n + np.array([-0.3, 0, 0])
                elif texture == "bark":
                    stripe = int((arc + 40) // 2.0)
                    t = tone[int(hv // 3) % 64, stripe % 64]
                    v = np.clip(0.1 + lit * 0.45 + t * 0.35 + 0.15 * math.sin(stripe * 1.7 + hv * 0.15), 0, 0.999)
                    col = ramp[int(v * len(ramp))]
                    if stripe % 3 == 0:
                        col = ramp[0]
                        n = n + np.array([0.25, 0, 0])
                elif texture == "metal":
                    v = np.clip(0.2 + lit * 0.7 + (0.25 if abs(u + 0.35) < 0.18 else 0), 0, 0.999)
                    col = ramp[int(v * len(ramp))]
                else:  # plain
                    v = np.clip(0.15 + lit * 0.75, 0, 0.999)
                    col = ramp[int(v * len(ramp))]
                if moss_rows and hv < moss_rows and rng.random() < (1 - hv / moss_rows) * 0.65:
                    col = MOSS[int(rng.integers(0, 3))]
                if abs(u) > 0.86:
                    col = col * 0.8
                self.put(x, y, col, n)
        del max_r

    def disc(self, cx, cy, radius, ramp, *, flat=False, seed=0) -> None:
        """A flat top seen from the 3/4 view: an ellipse."""
        rng = np.random.default_rng(seed)
        b = radius * 0.42
        for y in range(self.h):
            for x in range(self.w):
                u = (x - cx) / radius
                v = (y - cy) / max(b, 0.5)
                rr = u * u + v * v
                if rr > 1:
                    continue
                t = 0.55 - 0.25 * u - 0.2 * v + rng.random() * (0.0 if flat else 0.12)
                col = ramp[int(np.clip(t, 0, 0.999) * len(ramp))]
                self.put(x, y, col, (0.0, 0.6, 0.8))

    def ring(self, cx, cy, radius, col, thickness=1, glow=None) -> None:
        """The front half of a horizontal band around a cylinder."""
        b = radius * 0.42
        for x in range(self.w):
            u = (x - cx) / radius
            if abs(u) > 1:
                continue
            y = cy + b * math.sqrt(1 - u * u)
            lit = 1.0 - 0.35 * (u + 1)
            for k in range(thickness):
                self.put(x, y - k, col * (0.7 + 0.45 * lit), self.wall_normal(u), glow)

    def sphere(self, cx, cy, r, ramp, glow_ramp=None, light=(-0.45, 0.55, 0.7)) -> None:
        for y in range(self.h):
            for x in range(self.w):
                dx, dy = (x - cx) / r, (y - cy) / r
                rr = dx * dx + dy * dy
                if rr > 1:
                    continue
                n = np.array([dx, -dy, math.sqrt(max(0.0, 1 - rr))])
                t = float(shade(n[None, None, :], light)[0, 0]) * 0.85 + 0.12
                col = ramp[int(np.clip(t, 0, 0.999) * len(ramp))]
                g = glow_ramp[int(np.clip(t, 0, 0.999) * len(glow_ramp))] if glow_ramp is not None else None
                self.put(x, y, col, n, g)

    def crystal(self, cx, top, w, h, ramp, glow=True) -> None:
        """An upright diamond with a lit left facet and a darker right one."""
        mid = top + h * 0.38
        for y in range(int(top), int(top + h) + 1):
            if y <= mid:
                half = w / 2 * (y - top) / max(mid - top, 1)
            else:
                half = w / 2 * (1 - (y - mid) / max(top + h - mid, 1))
            for x in range(int(cx - half - 0.5), int(cx + half + 0.5) + 1):
                if abs(x - cx) > half + 0.25:
                    continue
                left = x < cx
                upper = y <= mid
                idx = 3 if (left and upper) else 2 if left else 1 if upper else 0
                if abs(x - cx) < 0.6:
                    idx = 4
                col = ramp[min(idx, len(ramp) - 1)]
                n = ((-0.6 if left else 0.6), (0.4 if upper else -0.4), 0.7)
                self.put(x, y, col, n, col if glow else None)

    def line(self, x0, y0, x1, y1, col, n=(0.0, 0.0, 1.0), glow=None) -> None:
        steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            self.put(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, col, n, glow)

    def leaves(self, cx, cy, rx, ry, ramp, count=8, seed=0, berries=None) -> None:
        rng = np.random.default_rng(seed)
        blobs = []
        for _ in range(count):
            r = rng.uniform(min(rx, ry) * 0.45, min(rx, ry) * 0.7)
            bx = cx + rng.uniform(-rx + r, rx - r)
            by = cy + rng.uniform(-ry + r, ry - r)
            blobs.append((bx, by, r))
        blobs.sort(key=lambda b: b[1])
        noise = value_noise(self.h, self.w, 1.6, rng)
        for bx, by, r in blobs:
            for y in range(max(0, int(by - r - 1)), min(self.h, int(by + r + 2))):
                for x in range(max(0, int(bx - r - 1)), min(self.w, int(bx + r + 2))):
                    dx, dy = (x - bx) / r, (y - by) / r
                    rr = dx * dx + dy * dy
                    if rr > 1:
                        continue
                    n = np.array([dx + (noise[y, x] - 0.5) * 0.5, -dy, math.sqrt(max(0.05, 1 - rr))])
                    n /= np.linalg.norm(n)
                    t = float(shade(n[None, None, :])[0, 0]) * 0.8 + (noise[y, x] - 0.5) * 0.35 + 0.1
                    self.put(x, y, ramp[int(np.clip(t, 0, 0.999) * len(ramp))], n)
        if berries is not None:
            ys, xs = np.nonzero(self.alpha)
            for _ in range(berries[0]):
                i = int(rng.integers(0, len(ys)))
                self.put(xs[i], ys[i], berries[1][1], glow=berries[2][1] if len(berries) > 2 else None)

    def ink(self) -> None:
        ring = outline(self.alpha)
        ys, xs = np.nonzero(ring)
        for y, x in zip(ys, xs):
            self.put(x, y, INK)

    def save(self, folder: str, name: str, glow: bool = False) -> None:
        os.makedirs(folder, exist_ok=True)
        rgba = np.zeros((self.h, self.w, 4), np.uint8)
        rgba[..., :3] = np.clip(self.rgb + 0.5, 0, 255).astype(np.uint8)
        rgba[..., 3] = self.alpha
        Image.fromarray(rgba, "RGBA").save(os.path.join(folder, name + ".png"))
        Image.fromarray(encode_normals(self.nrm, self.alpha), "RGBA").save(os.path.join(folder, name + "_n.png"))
        if glow:
            Image.fromarray(self.glow, "RGBA").save(os.path.join(folder, name + "_glow.png"))


def battlement(c: Canvas, cx, cy, r, ramp=STONE) -> None:
    """Back parapet, shaded walkway, then front merlons, for a round tower top centred at (cx, cy)."""
    b = r * 0.42
    parapet = 3
    for x in range(c.w):
        u = (x - cx) / r
        if abs(u) > 1:
            continue
        y_back = cy - b * math.sqrt(1 - u * u)
        for k in range(parapet + 1):
            top = k == parapet
            c.put(x, y_back - k, ramp[4] if top else ramp[2], (0, 0.6, 0.8) if top else (-u * 0.5, -c.TILT, 0.85))
    c.disc(cx, cy, r - 1.2, [ramp[0], ramp[1], ramp[1]], flat=True)
    for x in range(c.w):
        u = (x - cx) / r
        if abs(u) > 1:
            continue
        theta = math.asin(u)
        y_front = cy + b * math.sqrt(1 - u * u)
        tooth = int((theta * r + 40) // 4) % 2 == 0
        rise = parapet if tooth else 1
        for k in range(rise + 1):
            if k == rise:
                c.put(x, y_front - k, ramp[5] if u < 0.3 else ramp[4], (0, 0.6, 0.8))
            else:
                c.put(x, y_front - k, ramp[3] if u < 0.2 else ramp[2], c.wall_normal(u))


# ---------------------------------------------------------------- towers
TOWERS: dict[str, dict] = {}


def tower(fn):
    TOWERS[fn.__name__] = fn
    return fn


@tower
def fire_brazier() -> dict:
    c = Canvas(34, 66, seed=1)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 14, STONE[:5], course_h=3, stone_w=6, moss_rows=4, seed=1)
    c.cylinder(cx, base - 4, 25, 11.5, STONE[1:], course_h=4, stone_w=6, moss_rows=3, seed=2)
    top_cy = base - 4 - 25 - 4.5
    c.cylinder(cx, top_cy + 5.5 + 6, 6, 14, STONE[1:], course_h=6, stone_w=5, seed=3)
    battlement(c, cx, top_cy, 14)
    # Arrow slit with a warm glow inside.
    for y in range(base - 22, base - 14):
        c.put(cx, y, IRON[0], (0, -0.5, 0.85), COAL[3] if y > base - 21 else None)
        c.put(cx - 1, y, STONE[4], (-0.5, -0.5, 0.8))
        c.put(cx + 1, y, STONE[1], (0.5, -0.5, 0.8))
    # Brazier: three legs, a riveted bowl and glowing coals.
    bowl_cy = top_cy - 13
    for lx in (-3, 0, 3):
        c.line(cx + lx, bowl_cy + 4, cx + lx * 1.6, top_cy + 2, IRON[2] if lx <= 0 else IRON[1], (0.3 * lx, -0.3, 0.9))
    for x in range(c.w):
        u = (x - cx) / 6.5
        if abs(u) > 1:
            continue
        depth = 5 * math.sqrt(1 - u * u)
        for y in range(int(bowl_cy), int(bowl_cy + depth) + 1):
            k = (y - bowl_cy) / max(depth, 1)
            lit = -u * 0.5 - k * 0.6 + 0.6
            col = IRON[3] if lit > 0.75 else IRON[2] if lit > 0.3 else IRON[1]
            c.put(x, y, col, (u * 0.8, -0.6 * k, 0.7))
    for y in range(c.h):
        for x in range(c.w):
            u, v = (x - cx) / 6.5, (y - bowl_cy) / 2.7
            rr = u * u + v * v
            if rr > 1:
                continue
            if rr > 0.6:
                c.put(x, y, IRON[3] if v < 0 else IRON[2], (0, 0.6, 0.8))
            else:
                heat = (1 - rr) * 0.8 + c.rng.random() * 0.35
                col = COAL[int(np.clip(heat, 0, 0.999) * len(COAL))]
                c.put(x, y, col * 0.6, (0, 0.6, 0.8), col)
    # Ivy on the left flank.
    for _ in range(26):
        y = int(c.rng.integers(base - 26, base - 4))
        x = int(cx - 11 + c.rng.integers(0, 3))
        if c.alpha[y, x]:
            c.put(x, y, LEAF[int(c.rng.integers(1, 5))], (-0.4, 0.2, 0.9))
    c.ink()
    c.save(os.path.join(OUT, "towers"), "fire_brazier", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, bowl_cy - base - 2],
            "light": {"color": "#ff9a48", "offset": [0, bowl_cy - base + 2], "energy": 1.2, "range": 120, "height": 40},
            "emitter": "fire", "emitter_offset": [0, bowl_cy - base - 1]}


@tower
def storm_spire() -> dict:
    c = Canvas(30, 66, seed=2)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 12.5, STONE[:5], course_h=2.5, stone_w=5, moss_rows=3, seed=4)
    c.cylinder(cx, base - 4, 30, 8.5, STONE[1:], top_radius=4.5, course_h=4, stone_w=5, seed=5)
    # Copper bands and lightning rods.
    for k, hv in enumerate((6, 14, 22)):
        r = 8.5 + (4.5 - 8.5) * hv / 30
        c.ring(cx, base - 4 - hv - r * 0.42 + 0.0, r + 0.6, COPPER[3], thickness=2 if k == 0 else 1)
    top = base - 4 - 30 - 2
    c.disc(cx, top + 1, 4.8, COPPER[1:])
    for side in (-1, 1):
        c.line(cx + side * 4, top + 1, cx + side * 6, top - 9, COPPER[2] if side < 0 else COPPER[1], (side * 0.5, 0, 0.8))
        c.put(cx + side * 6, top - 10, SPARK[3], glow=SPARK[3])
    # A floating storm crystal, crackling.
    c.crystal(cx, top - 21, 9, 15, SPARK)
    for _ in range(5):
        x = cx + c.rng.integers(-6, 7)
        y = top - 14 + c.rng.integers(-8, 8)
        if not c.alpha[int(y), int(x)]:
            c.put(x, y, SPARK[4], glow=SPARK[4])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "storm_spire", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, top - 14 - base],
            "light": {"color": "#ffe27a", "offset": [0, top - 12 - base], "energy": 0.9, "range": 100, "height": 46},
            "emitter": "sparks", "emitter_offset": [0, top - 14 - base]}


@tower
def nature_thornbush() -> dict:
    c = Canvas(36, 52, seed=3)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    # Roots spreading over the ground, then a gnarled trunk.
    for ang in (-2.6, -2.0, -1.0, -0.4, 0.3):
        c.line(cx, base - 2, cx + math.cos(ang) * 13, base + math.sin(ang) * -3 + 1, WOOD[2], (math.cos(ang) * 0.5, 0.3, 0.8))
    c.cylinder(cx, base, 16, 6.5, WOOD, top_radius=4.5, texture="bark", seed=6)
    # Branches with thorns.
    for x0, y0, x1, y1 in ((cx - 2, base - 12, cx - 11, base - 25), (cx + 2, base - 14, cx + 12, base - 27), (cx, base - 16, cx + 1, base - 30)):
        c.line(x0, y0, x1, y1, WOOD[3], (0, 0.3, 0.9))
        c.line(x0 + 1, y0, x1 + 1, y1, WOOD[1], (0.4, 0, 0.8))
        for t in (0.3, 0.6, 0.85):
            tx, ty = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            c.put(tx - 1, ty - 1, hexc("d8d0b0"), (0, 0.5, 0.8))
    # Canopy of dark leaves with glowing seed pods.
    c.leaves(cx, base - 32, 15, 11, LEAF, count=11, seed=7)
    for _ in range(6):
        ys, xs = np.nonzero(c.alpha[: base - 22])
        i = int(c.rng.integers(0, len(ys)))
        x, y = xs[i], ys[i]
        c.put(x, y, SEED[2] * 0.7, (0, 0.3, 0.9), SEED[2])
        c.put(x, y + 1, SEED[1] * 0.7, (0, -0.3, 0.9), SEED[1])
    # Thorny brambles around the foot.
    for _ in range(18):
        ang = c.rng.uniform(0, math.tau)
        x = cx + math.cos(ang) * c.rng.uniform(5, 12)
        y = base - 2 + math.sin(ang) * c.rng.uniform(1, 4)
        c.put(x, y, LEAF[int(c.rng.integers(1, 4))], (0, 0.4, 0.9))
        c.put(x + 1, y - 1, hexc("d8d0b0"))
    c.ink()
    c.save(os.path.join(OUT, "towers"), "nature_thornbush", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, -32],
            "light": {"color": "#9ae04a", "offset": [0, -30], "energy": 0.6, "range": 70, "height": 30},
            "emitter": "leaves", "emitter_offset": [0, -32]}


@tower
def hybrid_plasma() -> dict:
    c = Canvas(34, 68, seed=4)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 6, 14, STONE[:5], course_h=3, stone_w=6, moss_rows=3, seed=8)
    c.cylinder(cx, base - 5, 16, 11, STONE[1:], top_radius=9, course_h=4, stone_w=6, seed=9)
    # Copper coil: stacked rings narrowing upwards.
    coil_base = base - 5 - 16 - 4
    c.disc(cx, coil_base + 1, 9, STONE[2:])
    c.cylinder(cx, coil_base + 1, 18, 3, COPPER, texture="metal", seed=10)
    for k in range(7):
        r = 7 - k * 0.6
        c.ring(cx, coil_base - 2 - k * 2.5, r, COPPER[3] if k % 2 == 0 else COPPER[2], thickness=1)
    # Plasma orb with a hot glow.
    orb_y = coil_base - 24
    c.sphere(cx, orb_y, 6, [p * 0.75 for p in PLASMA], PLASMA)
    for _ in range(6):
        ang = c.rng.uniform(0, math.tau)
        c.put(cx + math.cos(ang) * 8, orb_y + math.sin(ang) * 7, SPARK[3], glow=SPARK[3])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_plasma", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, orb_y - base],
            "light": {"color": "#ff8a6a", "offset": [0, orb_y - base + 2], "energy": 1.1, "range": 110, "height": 50},
            "emitter": "plasma", "emitter_offset": [0, orb_y - base]}


@tower
def hybrid_thornstorm() -> dict:
    c = Canvas(34, 64, seed=5)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 12.5, STONE[:5], course_h=2.5, stone_w=5, moss_rows=5, seed=11)
    # A carved wooden totem wrapped in vines.
    c.cylinder(cx, base - 4, 26, 7, WOOD, top_radius=6, texture="bark", seed=12)
    for k in range(9):
        y = base - 6 - k * 3
        x = cx - 6 + (k % 3) * 5
        c.put(x, y, LEAF[3], (0, 0.3, 0.9))
        c.put(x + 1, y - 1, LEAF[2], (0, 0.3, 0.9))
    for y in (base - 14, base - 22):
        c.put(cx - 2, y, SPARK[2] * 0.6, glow=SPARK[2])
        c.put(cx + 2, y, SPARK[2] * 0.6, glow=SPARK[2])
    # Roots grip a storm crystal on top; leaves crown it.
    top = base - 4 - 26 - 2
    c.disc(cx, top + 1, 6, WOOD[1:])
    c.leaves(cx, top - 2, 12, 5, LEAF, count=7, seed=13, berries=(4, BERRY, SEED))
    c.crystal(cx, top - 19, 8, 14, SPARK)
    for side in (-1, 1):
        c.line(cx + side * 5, top - 2, cx + side * 3, top - 10, WOOD[3], (side * 0.5, 0, 0.8))
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_thornstorm", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, top - 12 - base],
            "light": {"color": "#d8f070", "offset": [0, top - 10 - base], "energy": 0.85, "range": 95, "height": 44},
            "emitter": "sparks", "emitter_offset": [0, top - 12 - base]}


def pool(c: Canvas, cx, cy, rx, ry, ramp, *, glow_ramp=None, ripples=3, seed=0) -> None:
    """A flat liquid surface seen from the 3/4 view, with a few bright ripples."""
    rng = np.random.default_rng(seed)
    for y in range(c.h):
        for x in range(c.w):
            u, v = (x - cx) / rx, (y - cy) / ry
            rr = u * u + v * v
            if rr > 1:
                continue
            t = 0.35 + 0.3 * (1 - rr) - 0.15 * u + rng.random() * 0.1
            idx = int(np.clip(t, 0, 0.999) * (len(ramp) - 1))
            g = glow_ramp[min(idx, len(glow_ramp) - 1)] * 0.5 if glow_ramp is not None and rr < 0.5 else None
            c.put(x, y, ramp[idx], (0.0, 0.3, 0.95), g)
    for k in range(ripples):
        r = (k + 1) / (ripples + 1)
        for a in np.linspace(math.pi * 0.15, math.pi * 0.85, 9):
            c.put(cx + math.cos(a) * rx * r, cy - math.sin(a) * ry * r, ramp[-1], (0, 0.5, 0.85),
                  glow_ramp[-1] * 0.6 if glow_ramp is not None else None)


def slab(c: Canvas, cx, bottom, w, h, ramp, *, depth=3, seed=0) -> None:
    """An upright stone block: a lit front face, a shaded right side and a top."""
    rng = np.random.default_rng(seed)
    left, right = int(round(cx - w / 2)), int(round(cx + w / 2))
    top = int(round(bottom - h))
    for x in range(left, right + 1):
        for y in range(top, int(bottom) + 1):
            t = 0.55 - 0.25 * (x - left) / max(w, 1) + rng.random() * 0.12 - 0.15 * (y - top) / max(h, 1)
            c.put(x, y, ramp[int(np.clip(t, 0, 0.999) * len(ramp))], (0.0, -c.TILT, 0.9))
        for k in range(depth):  # the top face
            c.put(x + k * 0.5, top - 1 - k, ramp[-2], (0, 0.6, 0.8))
    for k in range(depth):  # the right side
        for y in range(top - k, int(bottom) - k + 1):
            c.put(right + 1 + k * 0.5, y, ramp[1], (0.8, -0.2, 0.6))


@tower
def water_wellspring() -> dict:
    c = Canvas(34, 60, seed=21)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 6, 14, STONE[:5], course_h=3, stone_w=6, moss_rows=4, seed=31)
    basin_cy = base - 6 - 14 * 0.42
    battlement(c, cx, basin_cy, 14)
    pool(c, cx, basin_cy, 11.5, 4.3, WATER, ripples=2, seed=32)
    # A slim pillar rising from the basin, holding a smaller bowl.
    c.cylinder(cx, basin_cy + 1, 14, 3, STONE[1:], texture="plain", seed=33)
    bowl_cy = basin_cy - 15
    c.cylinder(cx, bowl_cy + 4, 3, 7, STONE[2:], texture="plain", seed=34)
    c.disc(cx, bowl_cy, 7, STONE[3:])
    pool(c, cx, bowl_cy, 5.5, 2.1, WATER, glow_ramp=WATER, ripples=1, seed=35)
    # A glowing water orb above, with falling droplets.
    orb_y = bowl_cy - 9
    c.sphere(cx, orb_y, 5, [w * 0.8 for w in WATER[1:]], WATER[2:])
    for k, dx in enumerate((-6, 6, -9, 9)):
        y = bowl_cy + 2 + k * 2
        c.put(cx + dx, y, WATER[4], (0, 0.3, 0.9), WATER[4] * 0.8)
        c.put(cx + dx, y + 1, WATER[3], (0, 0.3, 0.9))
    c.ink()
    c.save(os.path.join(OUT, "towers"), "water_wellspring", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, orb_y - base],
            "light": {"color": "#6ac0ff", "offset": [0, orb_y - base + 2], "energy": 0.9, "range": 100, "height": 40},
            "emitter": "drips", "emitter_offset": [0, orb_y - base]}


@tower
def earth_monolith() -> dict:
    c = Canvas(36, 66, seed=22)
    cx = c.w / 2 - 1.5
    base = c.h - 4
    # Rubble ring and a low plinth.
    c.cylinder(cx + 1, base, 4, 15, ROCK, course_h=4, stone_w=8, moss_rows=3, seed=41)
    c.disc(cx + 1, base - 4 - 15 * 0.42, 14, ROCK[1:], seed=42)
    # The standing stone, with amber runes.
    slab(c, cx, base - 7, 13, 36, SANDSTONE, depth=4, seed=43)
    rune_x = cx - 1
    for y0, shape in ((base - 38, ((0, 0), (0, 1), (0, 2), (-1, 1), (1, 1))),
                      (base - 29, ((0, 0), (-1, 1), (1, 1), (0, 2), (0, 3))),
                      (base - 19, ((-1, 0), (0, 0), (1, 0), (0, 1), (0, 2)))):
        for dx, dy in shape:
            c.put(rune_x + dx, y0 + dy, AMBER[2] * 0.7, (0, -0.5, 0.85), AMBER[3])
    # Cracks.
    for y in range(base - 33, base - 25):
        c.put(cx + 3 + (y % 3 == 0), y, SANDSTONE[0], (0.4, -0.4, 0.8))
    # A floating boulder above, held by amber light.
    rock_y = base - 7 - 36 - 9
    c.sphere(cx + 1, rock_y, 6, ROCK)
    for dx in (-3, 0, 3):
        c.put(cx + 1 + dx, rock_y + 7, AMBER[3], glow=AMBER[3])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "earth_monolith", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [1, rock_y - base],
            "light": {"color": "#ffb04a", "offset": [0, -26], "energy": 0.7, "range": 80, "height": 34},
            "emitter": "dust", "emitter_offset": [1, rock_y - base + 6]}


@tower
def void_obelisk() -> dict:
    c = Canvas(30, 70, seed=23)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 12, OBSIDIAN[:5], course_h=3, stone_w=5, seed=51)
    c.disc(cx, base - 5 - 12 * 0.42, 11, OBSIDIAN[1:], seed=52)
    # A tapering obsidian needle with violet seams.
    c.cylinder(cx, base - 7, 38, 6.5, OBSIDIAN[1:], top_radius=2.5, texture="metal", seed=53)
    for hv in (8, 18, 28):
        r = 6.5 + (2.5 - 6.5) * hv / 38
        c.ring(cx, base - 7 - hv - r * 0.42, r + 0.4, VOID[2], thickness=1, glow=VOID[2])
    # Orbiting shards and a void eye on top.
    top = base - 7 - 38 - 3
    c.crystal(cx, top - 16, 8, 13, VOID)
    for ang in (0.4, 2.2, 4.0):
        x = cx + math.cos(ang) * 9
        y = top - 9 + math.sin(ang) * 3
        c.put(x, y, VOID[3] * 0.7, glow=VOID[3])
        c.put(x, y - 1, VOID[2] * 0.7, glow=VOID[2])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "void_obelisk", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, top - 10 - base],
            "light": {"color": "#a070ff", "offset": [0, top - 8 - base], "energy": 0.9, "range": 110, "height": 46},
            "emitter": "void", "emitter_offset": [0, top - 10 - base]}


@tower
def hybrid_bog() -> dict:
    c = Canvas(38, 56, seed=24)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 16, WOOD, texture="bark", moss_rows=5, seed=61)
    pool_cy = base - 5 - 16 * 0.42
    c.disc(cx, pool_cy, 16, WOOD[1:])
    pool(c, cx, pool_cy, 14, 5.2, BOG, glow_ramp=SEED, ripples=2, seed=62)
    # Rotting posts and a hanging lantern pod.
    for px, h in ((-10, 16), (9, 20), (-3, 26)):
        c.cylinder(cx + px, pool_cy + 2, h, 1.8, WOOD, texture="bark", seed=63 + h)
    c.line(cx - 3, pool_cy - 26, cx + 6, pool_cy - 22, WOOD[3], (0, 0.4, 0.8))
    pod_y = pool_cy - 17
    c.sphere(cx + 6, pod_y, 3.5, [b * 0.8 for b in BOG[1:]], SEED)
    # Mushrooms and bubbles.
    for mx in (-12, 12):
        c.disc(cx + mx, pool_cy + 1, 3, MUSHROOM)
    for bx, by in ((-5, 1), (3, -1), (7, 2)):
        c.put(cx + bx, pool_cy + by, BOG[4], (0, 0.5, 0.8), SEED[2] * 0.6)
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_bog", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [6, pod_y - base],
            "light": {"color": "#8ae07a", "offset": [0, pool_cy - base - 4], "energy": 0.7, "range": 90, "height": 30},
            "emitter": "bubbles", "emitter_offset": [0, pool_cy - base]}


@tower
def hybrid_quagmire() -> dict:
    c = Canvas(40, 58, seed=25)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 6, 17, ROCK, course_h=3, stone_w=7, moss_rows=4, seed=71)
    pool_cy = base - 6 - 17 * 0.42
    battlement(c, cx, pool_cy, 17, ROCK + [ROCK[-1]])
    pool(c, cx, pool_cy, 14.5, 5.5, MUD, ripples=3, seed=72)
    # Standing stones and a water crystal hovering over the mud.
    for px in (-9, 9):
        slab(c, cx + px - 1, pool_cy + 1, 4, 11 if px < 0 else 14, SANDSTONE, depth=2, seed=73 + px)
    c.crystal(cx, pool_cy - 26, 9, 16, WATER[1:])
    for dx in (-2, 2):
        c.put(cx + dx, pool_cy - 2, WATER[4], (0, 0.5, 0.8), WATER[3] * 0.7)
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_quagmire", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, pool_cy - 20 - base],
            "light": {"color": "#7ab8e0", "offset": [0, pool_cy - 18 - base], "energy": 0.8, "range": 95, "height": 40},
            "emitter": "drips", "emitter_offset": [0, pool_cy - 20 - base]}


@tower
def hybrid_gravity_well() -> dict:
    c = Canvas(40, 64, seed=26)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 17, OBSIDIAN[:5], course_h=3, stone_w=7, seed=81)
    ring_cy = base - 5 - 17 * 0.42
    c.disc(cx, ring_cy, 16, ROCK[:4], seed=82)
    c.ring(cx, ring_cy - 1, 12, VOID[1], thickness=1, glow=VOID[1])
    # Four leaning stones around the well.
    for px, h in ((-13, 18), (13, 18), (-6, 24), (6, 24)):
        slab(c, cx + px, ring_cy + (1 if abs(px) > 10 else -2), 4, h, ROCK, depth=2, seed=83 + h + px)
    # The singularity: a black orb with a bright violet rim.
    orb_y = ring_cy - 33
    for y in range(c.h):
        for x in range(c.w):
            d = math.hypot(x - cx, (y - orb_y) * 1.1)
            if d <= 5.5:
                rim = d > 4.2
                c.put(x, y, VOID[2] * 0.6 if rim else OBSIDIAN[0], (0, 0, 1), VOID[3] if rim else None)
    for ang in np.linspace(0, math.tau, 10, endpoint=False):
        c.put(cx + math.cos(ang) * 9, orb_y + math.sin(ang) * 3, VOID[2] * 0.6, glow=VOID[2])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_gravity_well", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, orb_y - base],
            "light": {"color": "#9a6aff", "offset": [0, orb_y - base + 2], "energy": 1.0, "range": 110, "height": 44},
            "emitter": "void", "emitter_offset": [0, orb_y - base]}


@tower
def hybrid_soulflame() -> dict:
    c = Canvas(34, 68, seed=27)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 13, OBSIDIAN[:5], course_h=3, stone_w=6, seed=91)
    c.cylinder(cx, base - 4, 22, 10, OBSIDIAN[1:], top_radius=8, course_h=4, stone_w=5, seed=92)
    for hv in (6, 15):
        r = 10 + (8 - 10) * hv / 22
        c.ring(cx, base - 4 - hv - r * 0.42, r + 0.5, SOUL[2], thickness=1, glow=SOUL[2])
    top_cy = base - 4 - 22 - 3.5
    battlement(c, cx, top_cy, 11, OBSIDIAN)
    # A skull-faced bowl of ghostly violet fire.
    bowl_cy = top_cy - 12
    for lx in (-3, 0, 3):
        c.line(cx + lx, bowl_cy + 3, cx + lx * 1.5, top_cy + 1, IRON[2] if lx <= 0 else IRON[1], (0.3 * lx, -0.3, 0.9))
    for x in range(c.w):
        u = (x - cx) / 6
        if abs(u) > 1:
            continue
        depth = 4 * math.sqrt(1 - u * u)
        for y in range(int(bowl_cy), int(bowl_cy + depth) + 1):
            c.put(x, y, IRON[2] if u < 0 else IRON[1], (u * 0.8, -0.5, 0.7))
    for y in range(c.h):
        for x in range(c.w):
            u, v = (x - cx) / 6, (y - bowl_cy) / 2.5
            if u * u + v * v <= 1:
                heat = (1 - (u * u + v * v)) * 0.8 + c.rng.random() * 0.3
                col = SOUL[int(np.clip(heat, 0, 0.999) * len(SOUL))]
                c.put(x, y, col * 0.6, (0, 0.6, 0.8), col)
    for dx in (-2, 2):
        c.put(cx + dx, bowl_cy + 2, SOUL[4], glow=SOUL[4])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_soulflame", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, bowl_cy - base - 2],
            "light": {"color": "#c07aff", "offset": [0, bowl_cy - base + 2], "energy": 1.1, "range": 115, "height": 40},
            "emitter": "soulfire", "emitter_offset": [0, bowl_cy - base - 1]}


@tower
def hybrid_wildfire() -> dict:
    c = Canvas(38, 60, seed=101)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    for ang in (-2.7, -2.1, -1.0, -0.4, 0.4):
        c.line(cx, base - 2, cx + math.cos(ang) * 13, base + math.sin(ang) * -3 + 1, WOOD[1], (math.cos(ang) * 0.5, 0.3, 0.8))
    c.cylinder(cx, base, 18, 6, WOOD, top_radius=4, texture="bark", seed=102)
    c.leaves(cx, base - 32, 16, 12, EMBER_LEAF, count=12, seed=103)
    for _ in range(9):
        ys, xs = np.nonzero(c.alpha[: base - 24])
        i = int(c.rng.integers(0, len(ys)))
        c.put(xs[i], ys[i], COAL[3] * 0.7, (0, 0.3, 0.9), COAL[3])
    for _ in range(4):
        ys, xs = np.nonzero(c.alpha[: base - 24])
        i = int(c.rng.integers(0, len(ys)))
        c.put(xs[i], ys[i], SEED[2] * 0.7, (0, 0.3, 0.9), SEED[2])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_wildfire", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, -34],
            "light": {"color": "#ff9a48", "offset": [0, -32], "energy": 0.9, "range": 100, "height": 34},
            "emitter": "fire", "emitter_offset": [0, -42]}


@tower
def hybrid_squall() -> dict:
    c = Canvas(36, 70, seed=104)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 12.5, STONE[:5], course_h=2.5, stone_w=5, moss_rows=3, seed=105)
    c.cylinder(cx, base - 4, 26, 8, STONE[1:], top_radius=5, course_h=4, stone_w=5, seed=106)
    for hv in (7, 17):
        r = 8 + (5 - 8) * hv / 26
        c.ring(cx, base - 4 - hv - r * 0.42, r + 0.5, WATER[3], thickness=1, glow=WATER[2])
    top = base - 4 - 26 - 2
    c.disc(cx, top + 1, 5.5, STONE[2:])
    # A storm cloud with a crystal of lightning inside it.
    c.leaves(cx, top - 12, 16, 7, CLOUD, count=10, seed=107)
    c.crystal(cx, top - 18, 7, 12, SPARK)
    for k in range(5):
        x = cx - 10 + k * 5
        c.put(x, top - 3, WATER[4], (0, 0.3, 0.9), WATER[3] * 0.8)
        c.put(x + 1, top - 1, WATER[3], (0, 0.3, 0.9))
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_squall", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, top - 12 - base],
            "light": {"color": "#a8d8ff", "offset": [0, top - 10 - base], "energy": 0.9, "range": 110, "height": 46},
            "emitter": "drips", "emitter_offset": [0, top - 5 - base]}


@tower
def hybrid_ironbark() -> dict:
    c = Canvas(40, 62, seed=108)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 15, ROCK, course_h=4, stone_w=8, moss_rows=4, seed=109)
    c.cylinder(cx, base - 4, 22, 8, WOOD, top_radius=6, texture="bark", seed=110)
    for hv in (4, 12, 19):
        r = 8 + (6 - 8) * hv / 22
        c.ring(cx, base - 4 - hv - r * 0.42, r + 0.4, IRON[3], thickness=1)
    top = base - 4 - 22
    c.leaves(cx, top - 8, 18, 10, LEAF, count=12, seed=111)
    for _ in range(14):
        ys, xs = np.nonzero(c.alpha[: top + 2])
        i = int(c.rng.integers(0, len(ys)))
        c.put(xs[i], ys[i], IRON[3], (0, 0.5, 0.8))
    for _ in range(5):
        ys, xs = np.nonzero(c.alpha[: top + 2])
        i = int(c.rng.integers(0, len(ys)))
        c.put(xs[i], ys[i], AMBER[3] * 0.7, (0, 0.3, 0.9), AMBER[3])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_ironbark", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, top - 8 - base],
            "light": {"color": "#d8c070", "offset": [0, top - 6 - base], "energy": 0.6, "range": 80, "height": 36},
            "emitter": "leaves", "emitter_offset": [0, top - 8 - base]}


@tower
def hybrid_abyss() -> dict:
    c = Canvas(40, 58, seed=112)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 6, 17, OBSIDIAN[:5], course_h=3, stone_w=7, seed=113)
    pool_cy = base - 6 - 17 * 0.42
    battlement(c, cx, pool_cy, 17, OBSIDIAN)
    pool(c, cx, pool_cy, 14.5, 5.5, ABYSS, glow_ramp=VOID, ripples=3, seed=114)
    for px in (-10, 10):
        c.cylinder(cx + px, pool_cy + 2, 12, 1.6, OBSIDIAN[2:], texture="plain", seed=115 + px)
        c.put(cx + px, pool_cy - 12, VOID[3], glow=VOID[3])
    orb_y = pool_cy - 22
    c.sphere(cx, orb_y, 6, [a * 0.9 for a in ABYSS[1:]], VOID[1:])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_abyss", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, orb_y - base],
            "light": {"color": "#6a7aff", "offset": [0, orb_y - base + 2], "energy": 0.9, "range": 105, "height": 40},
            "emitter": "void", "emitter_offset": [0, orb_y - base]}


@tower
def hybrid_magma() -> dict:
    c = Canvas(42, 56, seed=116)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    # A small volcano: a tapering rock cone with a lava lake in its crater.
    c.cylinder(cx, base, 24, 18, ROCK, top_radius=9, course_h=5, stone_w=9, moss_rows=3, seed=117)
    crater = base - 24 - 9 * 0.42
    c.disc(cx, crater, 9, ROCK[:3])
    pool(c, cx, crater, 7.5, 2.8, COAL[:4], glow_ramp=COAL, ripples=1, seed=118)
    for k, (x0, y0) in enumerate(((-6, crater + 3), (4, crater + 4), (-1, crater + 3))):
        for d in range(5 + k * 3):
            c.put(cx + x0 + (d % 2) * (1 if k % 2 else -1), y0 + d, COAL[2] * 0.7, (0, -0.4, 0.8), COAL[2])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_magma", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, crater - base - 2],
            "light": {"color": "#ff7a30", "offset": [0, crater - base], "energy": 1.2, "range": 120, "height": 30},
            "emitter": "fire", "emitter_offset": [0, crater - base - 1]}


@tower
def hybrid_riftstorm() -> dict:
    c = Canvas(32, 70, seed=119)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 5, 12, OBSIDIAN[:5], course_h=3, stone_w=5, seed=120)
    c.cylinder(cx, base - 4, 32, 7.5, OBSIDIAN[1:], top_radius=4, texture="metal", seed=121)
    for hv in (6, 15, 24):
        r = 7.5 + (4 - 7.5) * hv / 32
        c.ring(cx, base - 4 - hv - r * 0.42, r + 0.6, COPPER[3], thickness=1)
    top = base - 4 - 32 - 2
    c.disc(cx, top + 1, 4.5, COPPER[1:])
    for side in (-1, 1):
        c.line(cx + side * 4, top + 1, cx + side * 7, top - 10, COPPER[2] if side < 0 else COPPER[1], (side * 0.5, 0, 0.8))
        c.put(cx + side * 7, top - 11, VOID[3], glow=VOID[3])
    c.crystal(cx, top - 20, 8, 14, VOID)
    for _ in range(5):
        x = cx + c.rng.integers(-7, 8)
        y = top - 14 + c.rng.integers(-8, 8)
        if not c.alpha[int(y), int(x)]:
            c.put(x, y, SPARK[4], glow=SPARK[3])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_riftstorm", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, top - 13 - base],
            "light": {"color": "#c08aff", "offset": [0, top - 11 - base], "energy": 1.0, "range": 110, "height": 48},
            "emitter": "sparks", "emitter_offset": [0, top - 13 - base]}


@tower
def hybrid_steam() -> dict:
    c = Canvas(38, 52, seed=122)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    c.cylinder(cx, base, 10, 15, STONE[:5], course_h=3, stone_w=6, moss_rows=3, seed=123)
    rim = base - 10 - 15 * 0.42
    battlement(c, cx, rim, 15)
    pool(c, cx, rim, 12, 4.6, WATER[1:], glow_ramp=WATER, ripples=2, seed=124)
    # Copper pipes and a glowing fire grate under the water.
    for side in (-1, 1):
        c.line(cx + side * 15, base - 3, cx + side * 17, rim - 6, COPPER[2] if side < 0 else COPPER[1], (side * 0.6, 0, 0.8))
        c.put(cx + side * 17, rim - 7, COPPER[4], (0, 0.6, 0.8))
    for k in range(-2, 3):
        c.put(cx + k * 3, base - 4, COAL[3] * 0.7, (0, -0.5, 0.85), COAL[3])
        c.put(cx + k * 3, base - 5, COAL[2] * 0.7, (0, -0.5, 0.85), COAL[2])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_steam", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, rim - base - 3],
            "light": {"color": "#ffc090", "offset": [0, -6], "energy": 0.8, "range": 90, "height": 20},
            "emitter": "steam", "emitter_offset": [0, rim - base - 2]}


@tower
def hybrid_lodestone() -> dict:
    c = Canvas(36, 70, seed=125)
    cx = c.w / 2 - 1.5
    base = c.h - 4
    c.cylinder(cx + 1, base, 4, 15, ROCK, course_h=4, stone_w=8, moss_rows=3, seed=126)
    c.disc(cx + 1, base - 4 - 15 * 0.42, 14, ROCK[1:], seed=127)
    slab(c, cx, base - 7, 11, 32, SANDSTONE, depth=4, seed=128)
    for y in range(base - 36, base - 10, 4):
        for x in range(int(cx - 6), int(cx + 8)):
            c.put(x, y, COPPER[3] if x < cx else COPPER[2], (0, -0.5, 0.85))
    top = base - 7 - 32 - 6
    c.crystal(cx + 1, top - 14, 9, 15, SPARK)
    for ang in (0.3, 1.9, 3.5, 5.0):
        c.put(cx + 1 + math.cos(ang) * 9, top - 7 + math.sin(ang) * 3, SPARK[3], glow=SPARK[3])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_lodestone", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [1, top - 8 - base],
            "light": {"color": "#ffe27a", "offset": [0, top - 6 - base], "energy": 0.9, "range": 105, "height": 46},
            "emitter": "sparks", "emitter_offset": [1, top - 8 - base]}


@tower
def hybrid_blightroot() -> dict:
    c = Canvas(38, 58, seed=129)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    for ang in (-2.8, -2.2, -1.2, -0.3, 0.5):
        c.line(cx, base - 2, cx + math.cos(ang) * 14, base + math.sin(ang) * -3 + 1, OBSIDIAN[3], (math.cos(ang) * 0.5, 0.3, 0.8))
    c.cylinder(cx, base, 17, 6, [OBSIDIAN[1], OBSIDIAN[2], WOOD[1], WOOD[2], OBSIDIAN[4]], top_radius=4, texture="bark", seed=130)
    for x0, y0, x1, y1 in ((cx - 2, base - 12, cx - 12, base - 24), (cx + 2, base - 14, cx + 12, base - 27)):
        c.line(x0, y0, x1, y1, OBSIDIAN[3], (0, 0.3, 0.9))
    c.leaves(cx, base - 31, 15, 11, BLIGHT, count=11, seed=131)
    for _ in range(7):
        ys, xs = np.nonzero(c.alpha[: base - 22])
        i = int(c.rng.integers(0, len(ys)))
        c.put(xs[i], ys[i], SEED[2] * 0.7, (0, 0.3, 0.9), SEED[2])
    for _ in range(3):
        ys, xs = np.nonzero(c.alpha[: base - 22])
        i = int(c.rng.integers(0, len(ys)))
        c.put(xs[i], ys[i], VOID[3] * 0.7, (0, 0.3, 0.9), VOID[3])
    c.ink()
    c.save(os.path.join(OUT, "towers"), "hybrid_blightroot", glow=True)
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, -32],
            "light": {"color": "#a0e070", "offset": [0, -30], "energy": 0.7, "range": 85, "height": 30},
            "emitter": "void", "emitter_offset": [0, -32]}


# ---------------------------------------------------------------- enemies
def slime(name: str, w: int, h: int, rx: float, ry: float, gear=None, seed: int = 0) -> dict:
    frames = [(1.0, 1.0), (1.07, 0.9), (0.95, 1.08), (1.02, 0.97)]
    for f, (sx, sy) in enumerate(frames):
        body = Canvas(w, h, seed)
        gear_c = Canvas(w, h, seed + 100)
        erx, ery = rx * sx, ry * sy
        cy = h - 1 - ery * 0.95
        cx = (w - 1) / 2
        for y in range(h):
            for x in range(w):
                u = (x - cx) / erx
                v = (y - cy) / ery
                v = v * 1.5 if v > 0 else v
                rr = u * u + v * v
                if rr > 1:
                    continue
                n = np.array([u, -v, math.sqrt(max(0.04, 1 - rr))])
                t = float(shade(n[None, None, :])[0, 0]) * 0.85 + 0.1
                body.put(x, y, SLIME_BODY[int(np.clip(t, 0, 0.999) * 4)], n)
        hx, hy = cx - erx * 0.42, cy - ery * 0.48
        body.put(hx, hy, SLIME_BODY[4], (0, 0.5, 0.9))
        body.put(hx + 1, hy, SLIME_BODY[4], (0, 0.5, 0.9))
        body.ink()
        body.save(os.path.join(OUT, "enemies"), f"{name}_{f}")
        if gear:
            gear(gear_c, cx, cy, erx, ery)
            gear_c.save(os.path.join(OUT, "enemies"), f"{name}_gear_{f}", glow=True)
    return {"size": [w, h], "anchor": [w // 2, h - 1], "gear": gear is not None, "frames": len(frames)}


def eyes(c: Canvas, cx, cy, rx, ry, glow=None, gap=2) -> None:
    ey = cy - ry * 0.05
    for ex in (cx - gap, cx + gap):
        c.put(ex, ey, hexc("0b1220"), glow=glow)
        c.put(ex, ey - 1, hexc("0b1220") if glow is None else glow * 0.8, glow=glow)


def grunt_gear(c, cx, cy, rx, ry):
    eyes(c, cx, cy, rx, ry)


def runner_gear(c, cx, cy, rx, ry):
    eyes(c, cx + 1, cy, rx, ry, gap=1.5)
    # Swept-back ears make it read as fast.
    c.put(cx - rx + 1, cy - ry * 0.7, SLIME_BODY[1])
    c.put(cx - rx, cy - ry * 0.9, SLIME_BODY[1])


def brute_gear(c, cx, cy, rx, ry):
    # An iron helmet with rivets and a nose guard.
    for x in range(c.w):
        u = (x - cx) / (rx * 0.9)
        if abs(u) > 1:
            continue
        top = cy - ry * 0.95 * math.sqrt(1 - u * u)
        for y in range(int(top), int(cy - ry * 0.25)):
            lit = 0.5 - 0.4 * u - 0.2 * (y - top) / ry
            col = IRON[3] if lit > 0.55 else IRON[2] if lit > 0.2 else IRON[1]
            c.put(x, y, col, (u * 0.8, 0.5, 0.6))
        c.put(x, cy - ry * 0.25, IRON[0], (0, -0.5, 0.8))
    for k in (-3, 0, 3):
        c.put(cx + k, cy - ry * 0.4, IRON[3], (0, 0.5, 0.8))
    for y in range(int(cy - ry * 0.3), int(cy + 1)):
        c.put(cx, y, IRON[2], (0, -0.3, 0.9))
    eyes(c, cx, cy + 1, rx, ry, glow=hexc("ff6a3a"), gap=3)
    c.ink()


def warden_gear(c, cx, cy, rx, ry):
    # A bone crown with glowing eyes and a pair of horns.
    crown_y = cy - ry * 0.9
    for x in range(int(cx - 7), int(cx + 8)):
        tooth = 3 if (x - int(cx)) % 3 == 0 else 1
        for k in range(tooth + 1):
            c.put(x, crown_y - k, hexc("e8dcc0") if x < cx else hexc("b8a888"), (0, 0.5, 0.8))
        c.put(x, crown_y + 1, hexc("8a7a5a"))
    for side in (-1, 1):
        for k in range(7):
            c.put(cx + side * (rx * 0.75 + k * 0.6), cy - ry * 0.5 - k * 1.1, hexc("d8ccb0") if k < 5 else hexc("f4ecd8"))
    eyes(c, cx, cy, rx, ry, glow=hexc("ff4a6a"), gap=4)
    c.ink()


ENEMIES = {
    "grunt": lambda: slime("grunt", 18, 15, 7.5, 6.5, grunt_gear, 1),
    "runner": lambda: slime("runner", 14, 11, 5.5, 4.5, runner_gear, 2),
    "brute": lambda: slime("brute", 24, 20, 10.5, 9.0, brute_gear, 3),
    "warden": lambda: slime("warden", 36, 30, 16.0, 13.5, warden_gear, 4),
}


# ---------------------------------------------------------------- props
def make_props() -> dict:
    folder = os.path.join(OUT, "props")
    info = {}
    for i in range(3):
        c = Canvas(9, 8, seed=40 + i)
        for b in range(5):
            x0 = 2 + b + int(c.rng.integers(-1, 1))
            tall = int(c.rng.integers(4, 8))
            lean = c.rng.uniform(-0.4, 0.4) + (b - 2) * 0.12
            for k in range(tall):
                col = GRASS[min(4, 1 + int(k / tall * 4))] if k < tall - 1 else GRASS_TIP
                c.put(x0 + lean * k, c.h - 1 - k, col, (lean * 0.5, 0.35, 0.85))
        c.save(folder, f"tuft_{i}")
        info[f"tuft_{i}"] = {"size": [c.w, c.h], "sways": True}
    for i, (w, h) in enumerate(((8, 6), (11, 8))):
        c = Canvas(w, h, seed=50 + i)
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
        u = (xx - (w - 1) / 2) / (w / 2 - 0.5)
        v = (yy - (h - 1) * 0.55) / (h * 0.55)
        rr = u * u + v * v
        hgt = np.round(np.sqrt(np.clip(1 - rr, 0, 1)) * w * 0.35)
        nrm = normals_from_height(hgt, 0.9)
        t = shade(nrm) * 0.75 + c.rng.random((h, w)) * 0.15
        rgb = ramp_pick(ROCK, np.clip(t, 0, 0.999))
        for y in range(h):
            for x in range(w):
                if rr[y, x] < 1:
                    col = LICHEN if (c.rng.random() < 0.12 and nrm[y, x, 1] > 0.1) else rgb[y, x]
                    c.put(x, y, col, nrm[y, x])
        c.ink()
        c.save(folder, f"stone_{i}")
        info[f"stone_{i}"] = {"size": [w, h], "sways": False}
    for i, (cap, glowing) in enumerate(((MUSHROOM, False), (GLOWCAP, True))):
        c = Canvas(9, 9, seed=60 + i)
        for k, (mx, my, r) in enumerate(((3, 6, 2.5), (6, 7, 1.8))):
            for y in range(int(my - 1), c.h):
                c.put(mx, y, hexc("e0d8c0") if k == 0 else hexc("c8c0a8"), (0, -0.3, 0.9))
            for x in range(int(mx - r), int(mx + r) + 1):
                for y in range(int(my - r - 1), int(my) + 1):
                    if ((x - mx) / r) ** 2 + ((y - my + 0.5) / (r * 0.8)) ** 2 <= 1:
                        lit = 0.6 - 0.3 * (x - mx) / r - 0.3 * (y - my) / r
                        col = cap[2] if lit > 0.7 else cap[1] if lit > 0.35 else cap[0]
                        c.put(x, y, col * (0.7 if glowing else 1.0), (0, 0.5, 0.8), col if glowing else None)
        c.ink()
        c.save(folder, f"mushroom_{i}", glow=glowing)
        info[f"mushroom_{i}"] = {"size": [c.w, c.h], "sways": False, "glow": glowing}
    for i in range(2):
        c = Canvas(16, 13, seed=70 + i)
        c.leaves(7.5, 7, 7.5, 5.5, LEAF, count=6, seed=70 + i, berries=(4, BERRY) if i else None)
        c.ink()
        c.save(folder, f"bush_{i}")
        info[f"bush_{i}"] = {"size": [c.w, c.h], "sways": True}
    return info


# ---------------------------------------------------------------- ground per map
def read_map(path: str) -> dict:
    text = open(path).read()
    mid = re.search(r'^id = &"(\w+)"', text, re.M).group(1)
    grid = re.search(r"grid_size = Vector2i\((\d+), (\d+)\)", text)
    cell = re.search(r"cell_size = (\d+)", text)
    wps = re.findall(r"Vector2i\((-?\d+), (-?\d+)\)", re.search(r"waypoints = (.*)", text).group(1))
    return {"id": mid, "grid": (int(grid.group(1)), int(grid.group(2))) if grid else (24, 15),
            "cell": int(cell.group(1)) if cell else 64, "waypoints": [(int(a), int(b)) for a, b in wps]}


def distance_to_segments(px, py, pts) -> np.ndarray:
    best = np.full(px.shape, 1e9)
    for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
        vx, vy = bx - ax, by - ay
        ll = max(vx * vx + vy * vy, 1e-9)
        t = np.clip(((px - ax) * vx + (py - ay) * vy) / ll, 0, 1)
        best = np.minimum(best, np.hypot(px - (ax + t * vx), py - (ay + t * vy)))
    return best


def make_ground(m: dict, props_info: dict) -> None:
    cell_art = m["cell"] // ART_SCALE
    W, H = m["grid"][0] * cell_art, m["grid"][1] * cell_art
    rng = np.random.default_rng(abs(hash(m["id"])) % (2 ** 31) if False else sum(map(ord, m["id"])))
    pts = [((x + 0.5) * cell_art, (y + 0.5) * cell_art) for x, y in m["waypoints"]]
    # Stretch the ends so the road runs off the edge of the board.
    if len(pts) >= 2:
        for i, j in ((0, 1), (-1, -2)):
            ax, ay = pts[i]
            bx, by = pts[j]
            d = math.hypot(ax - bx, ay - by) or 1
            pts[i] = (ax + (ax - bx) / d * cell_art * 2, ay + (ay - by) / d * cell_art * 2)
    half = cell_art * 0.46
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    dist = distance_to_segments(xx, yy, pts)
    wobble = (fbm(H, W, [7, 3], rng) - 0.5) * 4.0
    road_d = dist + wobble
    on_road = road_d < half
    edge = (road_d >= half - 1.2) & on_road

    patches = fbm(H, W, [26, 11, 5], rng)
    fine = value_noise(H, W, 2.2, rng)
    g = np.clip(patches * 0.85 + fine * 0.25 - 0.08, 0, 0.999)
    g -= np.clip(1.0 - (road_d - half) / 5.0, 0, 1) * 0.25
    g = np.clip(g, 0, 0.999)
    rgb = ramp_pick(GRASS[:4], g, dither=0.35)
    height = g * 0.6
    for _ in range(int(W * H / 75)):
        x, y = int(rng.integers(0, W)), int(rng.integers(3, H))
        if road_d[y, x] < half + 1:
            continue
        tall = 2 + (rng.random() < 0.4)
        lean = int(rng.choice([-1, 0, 0, 1]))
        rgb[y, x] = GRASS[0]
        for k in range(1, tall + 1):
            xk = min(max(x + (lean if k == tall else 0), 0), W - 1)
            rgb[y - k, xk] = GRASS[3] if k < tall else GRASS_TIP
            height[y - k, xk] = 0.9
    for _ in range(int(W * H / 2600)):
        x, y = int(rng.integers(2, W - 2)), int(rng.integers(2, H - 2))
        if road_d[y, x] < half + 3:
            continue
        rgb[y, x] = FLOWER[int(rng.integers(0, len(FLOWER)))]
        rgb[y + 1, x] = GRASS[1]
        height[y, x] = 1.0

    dirt_t = np.clip(fbm(H, W, [12, 5, 3], rng) * 0.9 + 0.08, 0, 0.999)
    rut = np.abs(dist - 6.0) < 1.2
    dirt_t = np.clip(np.where(rut & on_road, dirt_t - 0.22, dirt_t), 0, 0.999)
    rgb = np.where(on_road[..., None], ramp_pick(DIRT, dirt_t, dither=0.5), rgb)
    rgb = np.where(edge[..., None], DIRT_EDGE, rgb)
    height = np.where(on_road, -0.6 + dirt_t * 0.3 - rut * 0.25, height)
    for _ in range(int(W * H / 1300)):
        x, y = int(rng.integers(1, W - 2)), int(rng.integers(1, H - 2))
        if road_d[y, x] > half - 3:
            continue
        rgb[y, x] = ROCK[3]
        rgb[y, x + 1] = ROCK[2]
        rgb[y + 1, x] = ROCK[1]
        height[y, x] += 0.8
    edge_pts = np.argwhere(edge)
    for y, x in edge_pts[rng.random(len(edge_pts)) < 0.35]:
        if y > 2:
            rgb[y, x] = GRASS[2]
            rgb[y - 1, x] = GRASS[3]
            height[y, x] = 0.4

    folder = os.path.join(OUT, "ground")
    os.makedirs(folder, exist_ok=True)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(folder, m["id"] + ".png"))
    Image.fromarray(encode_normals(normals_from_height(height, 1.6), np.full((H, W), 255, np.uint8)), "RGBA").save(
        os.path.join(folder, m["id"] + "_n.png"))

    # Props: small things in the grass, never on the road. The game hides a cell's props when a
    # tower is built there.
    props = []
    weights = [("tuft_0", 6), ("tuft_1", 6), ("tuft_2", 6), ("stone_0", 2), ("stone_1", 1),
               ("mushroom_0", 1), ("mushroom_1", 1), ("bush_0", 1), ("bush_1", 1)]
    kinds = [k for k, n in weights for _ in range(n)]
    for _ in range(int(m["grid"][0] * m["grid"][1] * 0.75)):
        x, y = float(rng.uniform(4, W - 4)), float(rng.uniform(8, H - 2))
        kind = kinds[int(rng.integers(0, len(kinds)))]
        size = props_info[kind]["size"]
        if road_d[int(y), int(x)] < half + size[0] * 0.5 + 2:
            continue
        cell = [int(x // cell_art), int(y // cell_art)]
        props.append({"kind": kind, "pos": [round(x), round(y)], "cell": cell, "flip": bool(rng.random() < 0.5)})
    with open(os.path.join(folder, m["id"] + ".json"), "w") as fh:
        json.dump({"size": [W, H], "props": props}, fh, indent=0)


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    art = {"art_scale": ART_SCALE, "towers": {}, "enemies": {}, "props": {}}
    tower_ids = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob("data/towers/*.tres"))
    for tid in tower_ids:
        if tid in TOWERS:
            art["towers"][tid] = TOWERS[tid]()
        else:
            print("No art recipe for tower", tid, "- the game draws a placeholder")
    for eid in sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob("data/enemies/*.tres")):
        if eid in ENEMIES:
            art["enemies"][eid] = ENEMIES[eid]()
        else:
            print("No art recipe for enemy", eid, "- the game draws a placeholder")
    art["props"] = make_props()
    for path in sorted(glob.glob("data/maps/*.tres")):
        make_ground(read_map(path), art["props"])
    with open(os.path.join(OUT, "art.json"), "w") as fh:
        json.dump(art, fh, indent=1)
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
