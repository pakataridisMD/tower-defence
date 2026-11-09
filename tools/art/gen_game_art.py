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


# ---------------------------------------------------------------- triple towers
# A triple is built from its three elements: one gives the base, one the shaft and one the crown,
# so all 20 are different and each still reads as the mix it is. Three gems in the elements' colours
# circle the crown, which is how a triple is told from a dual at a glance.
RING_ORDER = ["fire", "storm", "nature", "water", "earth", "void"]
ELEMENT_GEM = {"fire": COAL, "storm": SPARK, "nature": SEED, "water": WATER[1:], "earth": AMBER, "void": VOID}
ELEMENT_LIGHT = {"fire": (255, 154, 72), "storm": (255, 226, 122), "nature": (154, 224, 74),
                 "water": (106, 192, 255), "earth": (255, 176, 74), "void": (160, 112, 255)}
ELEMENT_EMITTER = {"fire": "fire", "storm": "sparks", "nature": "leaves", "water": "drips", "earth": "dust", "void": "void"}
TRIPLE_W, TRIPLE_H = 44, 84


def _triple_base(c: Canvas, element: str, cx: float, base: int, seed: int) -> float:
    """A wide two-step plinth in the element's material. Returns the y of the shaft's front foot."""
    r = 18.0
    if element == "fire":
        c.cylinder(cx, base, 8, r, STONE[:5], course_h=3, stone_w=6, moss_rows=3, seed=seed)
        for k in range(-4, 5):  # a glowing grate around the foot
            u = k / 5.0
            y = base - 3 + (r * 0.42) * (math.sqrt(1 - u * u) - 1)
            c.put(cx + u * r, y, COAL[2] * 0.7, (u, -0.5, 0.8), COAL[3])
            c.put(cx + u * r, y - 1, COAL[1] * 0.7, (u, -0.5, 0.8), COAL[2])
    elif element == "storm":
        c.cylinder(cx, base, 8, r, STONE[:5], course_h=2.5, stone_w=5, moss_rows=2, seed=seed)
        c.ring(cx, base - 4 - r * 0.42, r + 0.5, COPPER[3], thickness=2)
    elif element == "nature":
        for ang in (-2.8, -2.2, -1.2, -0.5, 0.2, 0.6):
            c.line(cx, base - 3, cx + math.cos(ang) * 20, base + math.sin(ang) * -3 + 1, WOOD[2], (math.cos(ang) * 0.5, 0.3, 0.8))
        c.cylinder(cx, base, 8, r - 1, WOOD, texture="bark", moss_rows=6, seed=seed)
    elif element == "water":
        c.cylinder(cx, base, 8, r, STONE[:5], course_h=3, stone_w=6, moss_rows=4, seed=seed)
    elif element == "earth":
        c.cylinder(cx, base, 8, r, ROCK, course_h=4, stone_w=9, moss_rows=3, seed=seed)
    else:
        c.cylinder(cx, base, 8, r, OBSIDIAN[:5], course_h=3, stone_w=6, seed=seed)
        c.ring(cx, base - 4 - r * 0.42, r + 0.4, VOID[2], thickness=1, glow=VOID[2])
    top_cy = base - 8 - r * 0.42
    if element == "water":
        battlement(c, cx, top_cy, r)
        pool(c, cx, top_cy, r - 3.5, (r - 3.5) * 0.4, WATER, glow_ramp=WATER, ripples=2, seed=seed + 1)
    else:
        ramp_top = {"fire": STONE[2:], "storm": STONE[2:], "nature": WOOD[1:], "earth": ROCK[1:], "void": OBSIDIAN[1:]}[element]
        c.disc(cx, top_cy, r - 1, ramp_top, seed=seed + 1)
    return top_cy + 3


def _triple_shaft(c: Canvas, element: str, cx: float, foot: float, seed: int) -> tuple[float, float]:
    """The tall middle part. Returns the centre y and the radius of its top."""
    h = 30
    if element == "fire":
        r0, r1 = 10.0, 9.0
        c.cylinder(cx, foot, h, r0, STONE[1:], top_radius=r1, course_h=4, stone_w=6, seed=seed)
        for y0 in (foot - 12, foot - 23):  # arrow slits with fire behind them
            for y in range(int(y0), int(y0) + 6):
                c.put(cx - 4, y, COAL[2] * 0.6, (0, -0.5, 0.85), COAL[3])
                c.put(cx + 4, y, COAL[1] * 0.6, (0, -0.5, 0.85), COAL[2])
    elif element == "storm":
        r0, r1 = 9.0, 5.0
        c.cylinder(cx, foot, h, r0, STONE[1:], top_radius=r1, course_h=4, stone_w=5, seed=seed)
        for hv in (7, 15, 23):
            r = r0 + (r1 - r0) * hv / h
            c.ring(cx, foot - hv - r * 0.42, r + 0.6, COPPER[3], thickness=1)
    elif element == "nature":
        r0, r1 = 8.0, 6.0
        c.cylinder(cx, foot, h, r0, WOOD, top_radius=r1, texture="bark", seed=seed)
        for k in range(10):  # a vine winding up the trunk
            y = foot - 3 - k * 2.8
            x = cx + math.sin(k * 1.1) * 6
            c.put(x, y, LEAF[3], (0, 0.3, 0.9))
            c.put(x + 1, y - 1, LEAF[4], (0, 0.3, 0.9))
    elif element == "water":
        r0, r1 = 8.0, 7.0
        c.cylinder(cx, foot, h, r0, STONE[1:], top_radius=r1, course_h=5, stone_w=5, seed=seed)
        for hv in (9, 20):
            r = r0 + (r1 - r0) * hv / h
            c.ring(cx, foot - hv - r * 0.42, r + 0.5, WATER[3], thickness=1, glow=WATER[2])
        for y in range(int(foot - h + 4), int(foot) - 1):  # a thin waterfall down the front
            if y % 3:
                c.put(cx - 1, y, WATER[4] if y % 2 else WATER[3], (0, -0.4, 0.9), WATER[3] * 0.6)
    elif element == "earth":
        r0, r1 = 8.0, 8.0
        slab(c, cx - 1, foot, 15, h, SANDSTONE, depth=4, seed=seed)
        for y0 in (foot - 24, foot - 15, foot - 7):
            for dx, dy in ((0, 0), (-1, 1), (1, 1), (0, 2), (0, 3)):
                c.put(cx - 2 + dx, y0 + dy, AMBER[2] * 0.7, (0, -0.5, 0.85), AMBER[3])
        return foot - h - 3, 7.0
    else:
        r0, r1 = 8.0, 4.0
        c.cylinder(cx, foot, h, r0, OBSIDIAN[1:], top_radius=r1, texture="metal", seed=seed)
        for hv in (7, 15, 23):
            r = r0 + (r1 - r0) * hv / h
            c.ring(cx, foot - hv - r * 0.42, r + 0.4, VOID[2], thickness=1, glow=VOID[2])
    return foot - h - r1 * 0.42, r1


def _triple_crown(c: Canvas, element: str, cx: float, top_cy: float, top_r: float, seed: int) -> float:
    """What sits on top and does the shooting. Returns the y its shots leave from."""
    if element == "fire":
        c.disc(cx, top_cy, top_r + 2, IRON[1:])
        bowl = top_cy - 9
        for lx in (-4, 0, 4):
            c.line(cx + lx, bowl + 4, cx + lx * 1.4, top_cy, IRON[2] if lx <= 0 else IRON[1], (0.3 * lx, -0.3, 0.9))
        for x in range(c.w):
            u = (x - cx) / 8.0
            if abs(u) > 1:
                continue
            depth = 5.5 * math.sqrt(1 - u * u)
            for y in range(int(bowl), int(bowl + depth) + 1):
                c.put(x, y, IRON[3] if u < -0.2 else IRON[2] if u < 0.5 else IRON[1], (u * 0.8, -0.5, 0.7))
        for y in range(int(bowl) - 4, int(bowl) + 4):
            for x in range(c.w):
                u, v = (x - cx) / 8.0, (y - bowl) / 3.0
                rr = u * u + v * v
                if rr <= 0.75:
                    heat = (1 - rr) * 0.8 + c.rng.random() * 0.35
                    col = COAL[int(np.clip(heat, 0, 0.999) * len(COAL))]
                    c.put(x, y, col * 0.6, (0, 0.6, 0.8), col)
        return bowl - 3
    if element == "storm":
        c.disc(cx, top_cy, top_r + 1.5, COPPER[1:])
        for side in (-1, 1):
            c.line(cx + side * (top_r + 1), top_cy, cx + side * (top_r + 5), top_cy - 12, COPPER[2] if side < 0 else COPPER[1], (side * 0.5, 0, 0.8))
            c.put(cx + side * (top_r + 5), top_cy - 13, SPARK[3], glow=SPARK[3])
        c.crystal(cx, top_cy - 24, 11, 19, SPARK)
        return top_cy - 15
    if element == "nature":
        c.leaves(cx, top_cy - 9, 19, 11, LEAF, count=13, seed=seed)
        for _ in range(8):
            ys, xs = np.nonzero(c.alpha[: int(top_cy)])
            i = int(c.rng.integers(0, len(ys)))
            c.put(xs[i], ys[i], SEED[2] * 0.7, (0, 0.3, 0.9), SEED[2])
        return top_cy - 10
    if element == "water":
        c.disc(cx, top_cy, top_r + 2.5, STONE[3:])
        pool(c, cx, top_cy, top_r + 1, (top_r + 1) * 0.4, WATER, glow_ramp=WATER, ripples=1, seed=seed)
        orb = top_cy - 12
        c.sphere(cx, orb, 7.5, [w * 0.8 for w in WATER[1:]], WATER[2:])
        for k, dx in enumerate((-9, 9, -11, 11)):
            c.put(cx + dx, top_cy - 4 + k * 2, WATER[4], (0, 0.3, 0.9), WATER[4] * 0.8)
        return orb
    if element == "earth":
        rock = top_cy - 11
        c.disc(cx, top_cy, top_r + 1.5, ROCK[1:])
        c.sphere(cx, rock, 8, ROCK)
        for dx, dy in ((-3, -2), (2, 1), (-1, 3), (4, -3)):
            c.put(cx + dx, rock + dy, AMBER[2] * 0.7, (0, 0.2, 0.9), AMBER[3])
        for dx in (-4, 0, 4):
            c.put(cx + dx, rock + 9, AMBER[3], glow=AMBER[3])
        return rock
    orb = top_cy - 13
    c.disc(cx, top_cy, top_r + 1.5, OBSIDIAN[2:])
    for y in range(c.h):
        for x in range(c.w):
            d = math.hypot(x - cx, (y - orb) * 1.1)
            if d <= 7.0:
                rim = d > 5.4
                c.put(x, y, VOID[2] * 0.6 if rim else OBSIDIAN[0], (0, 0, 1), VOID[3] if rim else None)
    for ang in np.linspace(0, math.tau, 10, endpoint=False):
        c.put(cx + math.cos(ang) * 11, orb + math.sin(ang) * 3.5, VOID[2] * 0.6, glow=VOID[2])
    return orb


def triple_tower(tower_id: str, elements: list[str]) -> dict:
    """Draws one triple from its elements. The roles turn with the mix, so no element is always the base."""
    order = sorted(elements, key=RING_ORDER.index)
    turn = sum(RING_ORDER.index(e) for e in order) % 3
    base_el, shaft_el, crown_el = order[turn:] + order[:turn]
    seed = 300 + sum((i + 1) * 7 * (RING_ORDER.index(e) + 1) for i, e in enumerate(order))
    c = Canvas(TRIPLE_W, TRIPLE_H, seed=seed)
    cx = c.w / 2 - 0.5
    base = c.h - 4
    foot = _triple_base(c, base_el, cx, base, seed + 1)
    top_cy, top_r = _triple_shaft(c, shaft_el, cx, foot, seed + 2)
    muzzle_y = _triple_crown(c, crown_el, cx, top_cy, top_r, seed + 3)
    # Three gems, one per element, set into the plinth where they always show.
    for k, element in enumerate(order):
        gx = cx + (k - 1) * 9
        gy = base - 4 + (0 if k == 1 else -2)
        gem = ELEMENT_GEM[element]
        for dx, dy, idx in ((0, -1, 3), (-1, 0, 2), (1, 0, 1), (0, 0, 3), (0, 1, 1)):
            col = gem[min(idx, len(gem) - 1)]
            c.put(gx + dx, gy + dy, col * 0.8, (dx * 0.5, -0.4, 0.8), col)
    c.ink()
    c.save(os.path.join(OUT, "towers"), tower_id, glow=True)
    light = np.mean([ELEMENT_LIGHT[e] for e in order], axis=0)
    light = light * 0.6 + np.array(ELEMENT_LIGHT[crown_el]) * 0.4
    return {"size": [c.w, c.h], "anchor": [c.w // 2, base], "muzzle": [0, int(muzzle_y - base)],
            "light": {"color": "#%02x%02x%02x" % tuple(int(v) for v in light), "offset": [0, int(muzzle_y - base) + 2],
                      "energy": 1.25, "range": 135, "height": 52},
            "emitter": ELEMENT_EMITTER[crown_el], "emitter_offset": [0, int(muzzle_y - base) - 1]}


def tower_elements(tower_id: str) -> list[str]:
    with open(os.path.join("data", "towers", tower_id + ".tres")) as fh:
        line = re.search(r"^elements = .*$", fh.read(), re.M).group(0)
    return re.findall(r'&"(\w+)"', line)


# ---------------------------------------------------------------- enemies
# One step of the walk: (stretch across, stretch up, lift off the ground in pixels).
# A squash, the push off, the air, and the landing.
HOP = [(1.10, 0.86, 0), (1.0, 1.0, 0), (0.92, 1.12, 1), (0.95, 1.07, 2), (1.0, 1.0, 1), (1.07, 0.92, 0)]
SPEC_LIGHT = np.array([-0.45, 0.55, 0.7]) / np.linalg.norm([-0.45, 0.55, 0.7])


def lumps(c: Canvas, parts: list[tuple], ramp=SLIME_BODY) -> None:
    """A body made of rounded lumps, each (cx, cy, rx, ry, flat). `flat` squashes the lower half, so
    the lump sits on the ground instead of floating as a ball. Where lumps overlap the nearer one wins.
    Shaded as wet jelly: a soft top light, light bouncing back up into the lower right, a hot glint."""
    for y in range(c.h):
        for x in range(c.w):
            best = None
            for pcx, pcy, prx, pry, flat in parts:
                u = (x - pcx) / prx
                v = (y - pcy) / pry
                if v > 0:
                    v *= flat
                rr = u * u + v * v
                if rr > 1:
                    continue
                z = math.sqrt(1 - rr) * min(prx, pry)
                if best is None or z > best[0]:
                    best = (z, u, v, rr)
            if best is None:
                continue
            _, u, v, rr = best
            n = np.array([u, -v, math.sqrt(max(0.04, 1 - rr))])
            n /= np.linalg.norm(n)
            lit = float(n @ SPEC_LIGHT)
            t = max(0.0, lit) * 0.8 + 0.12
            if rr > 0.62 and u > 0.1 and v > -0.35:
                t += 0.2 * (rr - 0.62) / 0.38  # light through the jelly, low on the far side
            idx = int(np.clip(t, 0, 0.999) * 4)
            if lit > 0.975:
                idx = 4
            c.put(x, y, ramp[idx], n)


def creature(name: str, w: int, h: int, rx: float, ry: float, gear=None, seed: int = 0, kind: str = "blob") -> dict:
    """Draws an enemy's walk cycle. The body is drawn in greys, since the game tints it with the
    enemy's element; `gear` draws the untinted parts (eyes, armour, crowns) around (cx, cy, rx, ry).
    Enemies face right; the game flips them when they walk left.

    kind: "blob" hops; "twin" is two blobs joined (it splits); "dart" and "serpent" trail a tail behind
    a head; "beetle" is a shell on little feet; "wisp" floats over the ground with a ragged hem."""
    ground = h - 2
    mid = (w - 1) / 2
    heavy = ry >= 9
    for f, (sx, sy, lift) in enumerate(HOP):
        phase = f / len(HOP) * math.tau
        body = Canvas(w, h, seed)
        gear_c = Canvas(w, h, seed + 100)
        if heavy:
            sx, sy, lift = 1 + (sx - 1) * 0.6, 1 + (sy - 1) * 0.6, lift // 2
        gcx, grx, gry = mid, rx * sx, ry * sy
        if kind == "blob":
            gcy = ground - lift - gry * 0.625
            parts = [(gcx, gcy, grx, gry, 1.6)]
            if heavy and lift == 0:  # big ones pool at the base
                parts.append((gcx, ground - gry * 0.16, grx * 1.1, gry * 0.3, 1.9))
            lumps(body, parts)
        elif kind == "twin":
            lean = math.sin(phase) * 0.07
            parts = []
            for side, grow in ((-1, 1 + lean), (1, 1 - lean)):
                part_ry = ry * grow * (1.0 if side < 0 else 0.92)
                parts.append((mid + side * rx * 0.37, ground - part_ry * 0.625, rx * 0.66 * (2 - grow), part_ry, 1.6))
            gcy, grx, gry = ground - ry * 0.625, rx, ry
            lumps(body, parts)
        elif kind in ("dart", "serpent"):
            count, shrink, gap = (3, 0.7, 0.62) if kind == "dart" else (4, 0.8, 0.5)
            grx, gry = rx * 0.78, ry * (1 + (sy - 1) * 0.5)
            # Head to the right, tail to the left, and the whole length centred on the canvas.
            tail = rx * gap * count + grx * shrink ** count
            gcx = mid + (tail - grx) / 2
            gcy = ground - (lift if kind == "dart" else 0) - gry * 0.625
            parts = [(gcx, gcy, grx, gry, 1.6)]
            for k in range(1, count + 1):
                seg_rx, seg_ry = grx * shrink ** k, ry * shrink ** k
                sway = math.sin(phase - k * 1.1) * (0.8 if kind == "dart" else 1.4)
                parts.append((gcx - rx * gap * k, ground - seg_ry * 0.625 - max(0.0, sway), seg_rx, seg_ry, 1.6))
            lumps(body, parts)
        elif kind == "beetle":
            up = (0, 1, 0, 0, 1, 0)[f]
            grx, gry = rx, ry
            gcy = ground - 2 - up - ry * 0.5
            lumps(body, [(gcx, gcy, rx, ry, 2.0)])
            # The rim of the shell, and the belly in its shadow.
            for x in range(w):
                u = (x - gcx) / rx
                if abs(u) >= 1:
                    continue
                rim = gcy + ry * 0.5 * math.sqrt(1 - u * u) - max(1.0, ry * 0.14)
                for y in range(int(round(rim)), h):
                    if body.alpha[y, x]:
                        body.put(x, y, SLIME_BODY[0 if y == int(round(rim)) else 1], (u * 0.5, -0.6, 0.6))
            for i, fx in enumerate((-0.7, -0.26, 0.26, 0.7)):
                stepping = (f + (i % 2) * 3) % 6 < 3
                foot_y = ground - (1 if stepping else 0)
                foot_x = gcx + fx * rx + (1 if stepping else 0)
                for dx in (0, 1):
                    body.put(foot_x + dx, foot_y, SLIME_BODY[0], (0, 0.4, 0.9))
                    body.put(foot_x + dx, foot_y - 1, SLIME_BODY[1], (0, 0.4, 0.9))
        elif kind == "wisp":
            hover = 2 + (0, 1, 2, 2, 1, 0)[f]
            grx, gry = rx, ry * 0.8
            hem = ground - hover
            gcy = hem - ry * 0.75 - gry * 0.2
            for x in range(w):
                u = (x - gcx) / rx
                if abs(u) > 1:
                    continue
                tatter = 1.6 * math.sin(x * 1.5 + phase) + (2.0 if int(x + f) % 4 == 0 else 0.0)
                bottom = hem - abs(u) * 2.0 - max(0.0, tatter)
                for y in range(int(gcy), int(round(bottom)) + 1):
                    fade = (y - gcy) / max(1.0, bottom - gcy)
                    n = np.array([u, 0.15, math.sqrt(max(0.04, 1 - u * u))])
                    t = float(shade(n[None, None, :])[0, 0]) * 0.8 + 0.12 - fade * 0.3
                    body.put(x, y, SLIME_BODY[int(np.clip(t, 0, 0.999) * 4)], n)
            lumps(body, [(gcx, gcy, grx, gry, 1.0)])
        else:
            raise ValueError(kind)
        body.ink()
        body.save(os.path.join(OUT, "enemies"), f"{name}_{f}")
        if gear:
            gear(gear_c, gcx, gcy, grx, gry)
            gear_c.save(os.path.join(OUT, "enemies"), f"{name}_gear_{f}", glow=True)
    return {"size": [w, h], "anchor": [w // 2, h - 1], "gear": gear is not None, "frames": len(HOP)}


def eyes(c: Canvas, cx, cy, rx, ry, glow=None, gap=2) -> None:
    """Two eyes looking the way it walks. Big enough bodies get a pupil with a glint."""
    dark = hexc("0b1220")
    ey = cy - ry * 0.05
    look = 1 if rx >= 6 else 0
    for ex in (cx - gap + look, cx + gap + look):
        if rx < 7:
            c.put(ex, ey, dark, glow=glow)
            c.put(ex, ey - 1, dark if glow is None else glow * 0.8, glow=glow)
            continue
        tall = (0, -1, -2) if rx >= 12 else (0, -1)
        for dx in (0, 1):
            for dy in tall:
                c.put(ex + dx, ey + dy, dark if glow is None else glow, glow=glow)
        if glow is None:
            c.put(ex, ey + tall[-1], hexc("f4f6f8"))
        else:
            c.put(ex + 1, ey + tall[-1], hexc("ffffff"), glow=hexc("ffffff"))


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


def mender_gear(c, cx, cy, rx, ry):
    # A green sprout on its head and a soft glowing heart: it heals.
    eyes(c, cx, cy, rx, ry)
    top = cy - ry * 0.95
    for k in range(3):
        c.put(cx, top - k, LEAF[2 + (k > 1)], (0, 0.3, 0.9))
    for side in (-1, 1):
        c.put(cx + side, top - 3, LEAF[4], (side * 0.5, 0.5, 0.7))
        c.put(cx + side * 2, top - 3, LEAF[3], (side * 0.5, 0.5, 0.7))
    heart = hexc("7af08a")
    for dx, dy in ((0, 0), (-1, -1), (1, -1)):
        c.put(cx + dx, cy + ry * 0.45 + dy, heart * 0.8, glow=heart)
    c.ink()


def splitter_gear(c, cx, cy, rx, ry):
    # A dark crack down the middle where it will split.
    eyes(c, cx, cy - 1, rx, ry, gap=3)
    x = cx
    for k, y in enumerate(range(int(cy - ry * 0.85), int(cy + ry * 0.6))):
        x += (1 if k % 3 == 0 else -1 if k % 3 == 1 else 0) * 0.7
        c.put(x, y, hexc("2a2030"), (0, 0, 1))
        if k % 2 == 0:
            c.put(x + 1, y, hexc("f4e0ff") * 0.6, glow=hexc("f0c0ff"))


def shardling_gear(c, cx, cy, rx, ry):
    c.put(cx - 1, cy, hexc("0b1220"))
    c.put(cx + 1, cy, hexc("0b1220"))


def warded_gear(c, cx, cy, rx, ry):
    # Runes orbit it: immune to effects.
    eyes(c, cx, cy, rx, ry)
    rune = hexc("8af0ff")
    for k in range(10):
        a = k / 10 * math.tau
        x, y = cx + math.cos(a) * (rx + 1.2), cy - ry * 0.2 + math.sin(a) * (ry * 0.75)
        if k % 2 == 0:
            c.put(x, y, rune * 0.75, glow=rune)
    for x in range(int(cx - 2), int(cx + 3)):
        c.put(x, cy - ry * 0.75, hexc("c8f8ff"), (0, 0.5, 0.8), rune)


def flame_crown(c, cx, top, width, cols, glow_col):
    for i, x in enumerate(range(int(cx - width), int(cx + width) + 1)):
        tall = 2 + (3 if i % 3 == 1 else 1 if i % 3 == 0 else 0)
        for k in range(tall):
            col = cols[min(len(cols) - 1, k + 1)]
            c.put(x, top - k, col, (0, 0.5, 0.8), col if k else glow_col)


def cinder_tyrant_gear(c, cx, cy, rx, ry):
    flame_crown(c, cx, cy - ry * 0.85, 7, COAL, hexc("ffb040"))
    for k in range(9):  # glowing cracks across the shell
        x = cx - rx * 0.6 + k * 1.6
        y = cy - ry * 0.3 + (k % 3) - 1
        c.put(x, y, COAL[3], glow=COAL[2])
    eyes(c, cx, cy, rx, ry, glow=hexc("ffe060"), gap=4)
    c.ink()


def thunderhead_gear(c, cx, cy, rx, ry):
    # A storm cloud riding its head, with a bolt dropping through it.
    for k, (ox, r) in enumerate(((-6, 4.5), (0, 6.0), (6, 4.5), (-2, 3.5), (3, 4))):
        ccx, ccy = cx + ox, cy - ry * 0.9 - (2 if k < 3 else 4)
        for y in range(int(ccy - r), int(ccy + r) + 1):
            for x in range(int(ccx - r), int(ccx + r) + 1):
                d = ((x - ccx) / r) ** 2 + ((y - ccy) / (r * 0.7)) ** 2
                if d <= 1:
                    lit = 0.7 - 0.35 * (x - ccx) / r - 0.35 * (y - ccy) / r
                    c.put(x, y, CLOUD[int(np.clip(lit, 0, 0.999) * 5)], (0, 0.5, 0.8))
    bolt = SPARK[3]
    pts = [(cx + 1, cy - ry * 0.9), (cx - 2, cy - ry * 0.55), (cx + 1, cy - ry * 0.5), (cx - 1, cy - ry * 0.2)]
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        c.line(x0, y0, x1, y1, bolt, glow=SPARK[4])
    eyes(c, cx, cy + 2, rx, ry, glow=hexc("e0f4ff"), gap=4)
    c.ink()


def broodmother_gear(c, cx, cy, rx, ry):
    # Branching antlers with leaves, and a cluster of small eyes.
    for side in (-1, 1):
        x, y = cx + side * rx * 0.45, cy - ry * 0.8
        for k in range(8):
            x += side * 0.7
            y -= 1
            c.put(x, y, WOOD[3], (side * 0.4, 0.5, 0.8))
            if k in (3, 6):
                c.put(x + side, y - 1, WOOD[4])
                c.put(x + side * 2, y - 1, LEAF[3])
                c.put(x + side * 2, y - 2, LEAF[4])
        c.put(x, y - 1, LEAF[4])
    for dx, dy in ((-4, 0), (4, 0), (-2, -2), (2, -2), (0, 1), (-6, -2), (6, -2)):
        c.put(cx + dx, cy - ry * 0.1 + dy, hexc("e0ff70") * 0.8, glow=hexc("e0ff70"))
    c.ink()


def leviathan_gear(c, cx, cy, rx, ry):
    # Fins on each side and a coral crest.
    for side in (-1, 1):
        for k in range(7):
            for j in range(4 - k // 2):
                c.put(cx + side * (rx - 1 + j), cy - ry * 0.2 - k + j, WATER[3 - (j > 1)], (side * 0.6, 0.4, 0.7))
    for i, x in enumerate(range(int(cx - 6), int(cx + 7), 2)):
        h = 3 + (i % 3)
        for k in range(h):
            c.put(x, cy - ry * 0.9 - k, hexc("ff8a7a") if k < h - 1 else hexc("ffd0c0"), (0, 0.5, 0.8))
    eyes(c, cx, cy, rx, ry, glow=hexc("60fff0"), gap=5)
    c.ink()


def mountain_titan_gear(c, cx, cy, rx, ry):
    # Rock plates over its back.
    rng = np.random.default_rng(9)
    for px, py, r in ((-8, -0.6, 4.5), (0, -0.85, 5.5), (8, -0.6, 4.5), (-4, -0.3, 3.5), (5, -0.3, 3.5)):
        ccx, ccy = cx + px, cy + ry * py
        for y in range(int(ccy - r), int(ccy + r * 0.6) + 1):
            for x in range(int(ccx - r), int(ccx + r) + 1):
                if abs(x - ccx) + abs(y - ccy) * 1.3 <= r:
                    lit = 0.6 - 0.3 * (x - ccx) / r - 0.3 * (y - ccy) / r + rng.random() * 0.1
                    c.put(x, y, SANDSTONE[int(np.clip(lit, 0, 0.999) * 6)], ((x - ccx) / r * 0.6, 0.5, 0.7))
    eyes(c, cx, cy + 3, rx, ry, glow=hexc("ffb030"), gap=5)
    c.ink()


def hollow_king_gear(c, cx, cy, rx, ry):
    # A crown of black spikes and one great void eye.
    top = cy - ry * 0.85
    for i, x in enumerate(range(int(cx - 7), int(cx + 8))):
        h = 5 if i % 4 == 0 else 2
        for k in range(h):
            c.put(x, top - k, OBSIDIAN[2 + (k == h - 1) * 2], (0, 0.5, 0.8))
        c.put(x, top + 1, OBSIDIAN[1])
    for i in range(0, 15, 4):
        c.put(cx - 7 + i, top - 5, VOID[3], glow=VOID[4])
    for dy in (-1, 0, 1):
        for dx in (-2, -1, 0, 1, 2):
            if abs(dx) + abs(dy) <= 2:
                col = VOID[4] if (dx, dy) == (0, 0) else VOID[2]
                c.put(cx + dx, cy + dy, col, glow=col)
    c.ink()


def hollow_shade_gear(c, cx, cy, rx, ry):
    for k in range(4):
        c.put(cx - rx * 0.5 + k * 2, cy - ry - k % 2, VOID[2], glow=VOID[3])
    eyes(c, cx, cy, rx, ry, glow=VOID[4], gap=3)
    c.ink()


def sundered_heart_gear(c, cx, cy, rx, ry):
    # A cracked crystal shell, one shard per element, around a white-hot core.
    shards = [COAL, SPARK, SEED + [hexc("f0ffc0")], WATER, AMBER, VOID]
    for k, ramp in enumerate(shards):
        a = -math.pi / 2 + (k - 2.5) * 0.42
        x = cx + math.cos(a) * rx * 0.75
        top = cy + math.sin(a) * ry * 0.9 - 7
        c.crystal(x, top, 5, 10, ramp[-5:] if len(ramp) >= 5 else ramp, glow=True)
    for y in range(int(cy - 4), int(cy + 5)):
        for x in range(int(cx - 4), int(cx + 5)):
            d = math.hypot(x - cx, (y - cy) * 1.2)
            if d <= 4:
                col = hexc("ffffff") if d < 2 else hexc("fff0c0")
                c.put(x, y, col, glow=col)
    c.ink()


ENEMIES = {
    "grunt": lambda: creature("grunt", 20, 17, 7.5, 6.5, grunt_gear, 1),
    "runner": lambda: creature("runner", 22, 13, 6.0, 4.5, runner_gear, 2, "dart"),
    "brute": lambda: creature("brute", 26, 22, 11.0, 9.5, brute_gear, 3, "beetle"),
    "warden": lambda: creature("warden", 42, 34, 16.0, 13.5, warden_gear, 4),
    "mender": lambda: creature("mender", 20, 21, 7.5, 6.5, mender_gear, 5),
    "splitter": lambda: creature("splitter", 26, 17, 10.5, 7.0, splitter_gear, 6, "twin"),
    "shardling": lambda: creature("shardling", 16, 11, 4.2, 3.2, shardling_gear, 7, "dart"),
    "warded": lambda: creature("warded", 24, 20, 8.5, 7.0, warded_gear, 8, "beetle"),
    "cinder_tyrant": lambda: creature("cinder_tyrant", 42, 36, 16.0, 13.5, cinder_tyrant_gear, 9),
    "thunderhead": lambda: creature("thunderhead", 40, 40, 15.0, 12.5, thunderhead_gear, 10, "wisp"),
    "broodmother": lambda: creature("broodmother", 44, 38, 17.5, 13.5, broodmother_gear, 11, "beetle"),
    "leviathan": lambda: creature("leviathan", 68, 38, 19.0, 15.0, leviathan_gear, 12, "serpent"),
    "mountain_titan": lambda: creature("mountain_titan", 46, 40, 18.5, 16.0, mountain_titan_gear, 13, "beetle"),
    "hollow_king": lambda: creature("hollow_king", 40, 44, 15.0, 15.0, hollow_king_gear, 14, "wisp"),
    "hollow_shade": lambda: creature("hollow_shade", 26, 28, 10.0, 10.0, hollow_shade_gear, 15, "wisp"),
    "sundered_heart": lambda: creature("sundered_heart", 52, 46, 20.0, 16.5, sundered_heart_gear, 16),
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
    info.update(make_biome_props(folder))
    return info


# ---------------------------------------------------------------- biomes
def ramp(*cols):
    return [hexc(c) for c in cols]


# The look of each biome: ground and road ramps, the grass tufts painted into the ground, specks
# and flowers, glowing specks or cracks, and which props are scattered (kind, weight).
BIOMES = {
    "meadow": {
        "ground": GRASS[:4], "tuft": GRASS, "tip": GRASS_TIP, "road": DIRT, "edge": DIRT_EDGE,
        "flowers": FLOWER, "flower_rate": 1.0, "pebbles": ROCK,
        "props": [("tuft_0", 6), ("tuft_1", 6), ("tuft_2", 6), ("stone_0", 2), ("stone_1", 1),
                  ("mushroom_0", 1), ("mushroom_1", 1), ("bush_0", 1), ("bush_1", 1)],
    },
    "fire": {  # ash fields over cooling lava
        "ground": ramp("1e1819", "2a2223", "382d2c", "463833"), "tuft": ramp("2a1c16", "3e2618", "5a321a", "7a4420", "a85a24"),
        "tip": hexc("ff9a3a"), "road": ramp("3c3332", "4a403c", "5a4d46", "6a5a50", "7a685a"), "edge": hexc("1c1414"),
        "flowers": [hexc("ff7a2a"), hexc("ffb040")], "flower_rate": 0.8, "pebbles": OBSIDIAN[1:5],
        "cracks": (COAL, 0.026), "glow_flowers": True,
        "props": [("ash_tuft_0", 5), ("ash_tuft_1", 5), ("basalt_0", 3), ("basalt_1", 2), ("lava_vent", 2),
                  ("charred_stump", 2), ("ember_crystal", 1)],
    },
    "storm": {  # a windswept plateau of pale grass and slate
        "ground": ramp("47574a", "566a56", "687d63", "7e9372"), "tuft": ramp("44543f", "5c6e52", "778a66", "93a67c", "b0c294"),
        "tip": hexc("d0dcb0"), "road": ramp("373d46", "454c56", "545c66", "656e78", "79828c"), "edge": hexc("262b32"),
        "flowers": [hexc("d8e4f0"), hexc("a8c0e8")], "flower_rate": 1.2, "pebbles": ROCK,
        "props": [("steppe_tuft_0", 6), ("steppe_tuft_1", 6), ("slate_0", 3), ("slate_1", 2), ("storm_crystal", 2),
                  ("standing_stone", 1)],
    },
    "nature": {  # deep, overgrown jungle floor
        "ground": ramp("1a3219", "223f20", "2c4e28", "375e30"), "tuft": ramp("1c331a", "284a22", "36622c", "4a7e36", "64a042"),
        "tip": hexc("8cc850"), "road": ramp("3a2a1c", "4a3624", "5a442c", "6a5234", "7a6040"), "edge": hexc("2a1e14"),
        "flowers": [hexc("f070a0"), hexc("f0e070"), hexc("ffffff")], "flower_rate": 3.0, "pebbles": MOSS,
        "props": [("tuft_0", 4), ("tuft_1", 4), ("fern_0", 4), ("fern_1", 3), ("bush_0", 3), ("bush_1", 3),
                  ("mushroom_0", 2), ("mushroom_1", 3), ("stone_1", 1)],
    },
    "water": {  # a frozen lakeshore under snow
        "ground": ramp("8a9aae", "a4b4c6", "bccad8", "d4e0ea"), "tuft": ramp("6a5a40", "806c48", "9a8456", "b49e68", "ccb880"),
        "tip": hexc("e8dca8"), "road": ramp("4a6a88", "5a7c9a", "6e92ae", "88aac2", "a8c6d8"), "edge": hexc("33495e"),
        "flowers": [hexc("ffffff"), hexc("e0f0ff")], "flower_rate": 1.5, "pebbles": ramp("6a7a8a", "8090a0", "98a8b8"),
        "glints": ([hexc("e8f8ff"), hexc("bfe8ff")], 0.004),
        "props": [("reed_0", 5), ("reed_1", 4), ("ice_0", 3), ("ice_1", 2), ("snow_rock", 2), ("frozen_shrub", 2)],
    },
    "earth": {  # a red sandstone canyon
        "ground": ramp("6e3622", "82422a", "985232", "ac623c"), "tuft": ramp("5a4424", "74582e", "8e6e3a", "a88648", "c4a060"),
        "tip": hexc("dcc080"), "road": ramp("9a7a54", "aa8a60", "ba9a6e", "c8aa7c", "d6ba8c"), "edge": hexc("6a4a30"),
        "flowers": [hexc("f0d070"), hexc("e07040")], "flower_rate": 0.5, "pebbles": SANDSTONE,
        "props": [("dry_tuft_0", 5), ("dry_tuft_1", 4), ("boulder_0", 3), ("boulder_1", 2), ("cactus_0", 2),
                  ("cactus_1", 1), ("bones", 1)],
    },
    "void": {  # the rift: violet grass under no stars
        "ground": ramp("17121f", "1f182a", "282036", "322842"), "tuft": ramp("221a34", "34284e", "4a3a6c", "62508c", "8068b0"),
        "tip": hexc("b49ae8"), "road": ramp("121016", "1a1620", "221e2a", "2c2636", "383044"), "edge": hexc("0a080e"),
        "flowers": [hexc("c8a0ff"), hexc("80f0ff")], "flower_rate": 1.0, "pebbles": OBSIDIAN[1:5],
        "glints": ([VOID[3], VOID[4], hexc("80f0ff")], 0.006), "glow_flowers": True,
        "props": [("void_tuft_0", 5), ("void_tuft_1", 5), ("void_crystal", 3), ("obsidian_shard", 3),
                  ("rift_stone", 2), ("mushroom_1", 1)],
    },
    "heart": {  # the heart of the ring: pale stone, gold roads, prisms
        "ground": ramp("7c766c", "8e887c", "a29a8c", "b6ae9c"), "tuft": ramp("6a6650", "84805e", "9e986c", "b8b07c", "d0c890"),
        "tip": hexc("f0e8b0"), "road": ramp("7a6238", "907444", "a88850", "bea060", "d4b874"), "edge": hexc("4e3e22"),
        "flowers": [hexc("ff8a60"), hexc("f0e060"), hexc("80e070"), hexc("60c0ff"), hexc("d0a0ff")], "flower_rate": 1.0,
        "pebbles": ramp("8a8478", "a09a8c", "c0b8a8"),
        "glints": ([hexc("ff9a6a"), hexc("ffe07a"), hexc("9af07a"), hexc("7ad0ff"), hexc("caa0ff"), hexc("ffffff")], 0.004),
        "glow_flowers": True,
        "props": [("pale_tuft_0", 5), ("pale_tuft_1", 5), ("prism_0", 2), ("prism_1", 2), ("marble_0", 3),
                  ("ruin_pillar", 2)],
    },
}


def tuft(folder, name, cols, tip, seed, w=9, h=8, blades=5, tall=(4, 8)):
    c = Canvas(w, h, seed=seed)
    for b in range(blades):
        x0 = 1 + b * (w - 2) / max(1, blades - 1) + int(c.rng.integers(-1, 1))
        height = int(c.rng.integers(tall[0], tall[1]))
        lean = c.rng.uniform(-0.4, 0.4) + (b - blades / 2) * 0.1
        for k in range(height):
            col = cols[min(len(cols) - 1, 1 + int(k / height * (len(cols) - 1)))] if k < height - 1 else tip
            c.put(x0 + lean * k, c.h - 1 - k, col, (lean * 0.5, 0.35, 0.85))
    c.save(folder, name)
    return {name: {"size": [c.w, c.h], "sways": True}}


def rock(folder, name, w, h, cols, seed, accent=None, glow=None):
    c = Canvas(w, h, seed=seed)
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float64)
    u = (xx - (w - 1) / 2) / (w / 2 - 0.5)
    v = (yy - (h - 1) * 0.55) / (h * 0.55)
    rr = u * u + v * v
    hgt = np.round(np.sqrt(np.clip(1 - rr, 0, 1)) * w * 0.35)
    nrm = normals_from_height(hgt, 0.9)
    t = shade(nrm) * 0.75 + c.rng.random((h, w)) * 0.15
    rgb = ramp_pick(cols, np.clip(t, 0, 0.999))
    for y in range(h):
        for x in range(w):
            if rr[y, x] < 1:
                col = rgb[y, x]
                g = None
                if accent is not None and c.rng.random() < 0.12 and nrm[y, x, 1] > 0.05:
                    col = accent
                    g = accent if glow else None
                c.put(x, y, col, nrm[y, x], g)
    c.ink()
    c.save(folder, name, glow=bool(glow))
    return {name: {"size": [w, h], "sways": False, "glow": bool(glow)}}


def crystal_prop(folder, name, ramp_cols, seed, w=11, h=14, count=3):
    c = Canvas(w, h, seed=seed)
    spots = [(w / 2, 1, 4, h - 2), (w / 2 - 3, 5, 3, h - 6), (w / 2 + 3, 6, 3, h - 7)][:count]
    for cx, top, cw, ch in sorted(spots, key=lambda sp: sp[1]):
        c.crystal(cx, top, cw, ch, ramp_cols, glow=True)
    c.ink()
    c.save(folder, name, glow=True)
    return {name: {"size": [w, h], "sways": False, "glow": True}}


def make_biome_props(folder) -> dict:
    info = {}
    for i in range(2):
        info.update(tuft(folder, f"ash_tuft_{i}", BIOMES["fire"]["tuft"], BIOMES["fire"]["tip"], 200 + i, blades=4, tall=(3, 6)))
        info.update(tuft(folder, f"steppe_tuft_{i}", BIOMES["storm"]["tuft"], BIOMES["storm"]["tip"], 210 + i, w=11, blades=7, tall=(4, 8)))
        info.update(tuft(folder, f"reed_{i}", BIOMES["water"]["tuft"], BIOMES["water"]["tip"], 220 + i, w=7, h=12, blades=4, tall=(7, 12)))
        info.update(tuft(folder, f"dry_tuft_{i}", BIOMES["earth"]["tuft"], BIOMES["earth"]["tip"], 230 + i, blades=5, tall=(3, 7)))
        info.update(tuft(folder, f"void_tuft_{i}", BIOMES["void"]["tuft"], BIOMES["void"]["tip"], 240 + i, blades=6, tall=(4, 8)))
        info.update(tuft(folder, f"pale_tuft_{i}", BIOMES["heart"]["tuft"], BIOMES["heart"]["tip"], 250 + i, blades=5, tall=(3, 7)))
    # Fire
    info.update(rock(folder, "basalt_0", 9, 7, OBSIDIAN[1:6], 300, accent=COAL[3], glow=True))
    info.update(rock(folder, "basalt_1", 13, 9, OBSIDIAN[1:6], 301, accent=COAL[2], glow=True))
    c = Canvas(13, 7, seed=302)  # a small pool of lava with a dark rim
    for y in range(c.h):
        for x in range(c.w):
            d = ((x - 6) / 6.2) ** 2 + ((y - 3.5) / 3.2) ** 2
            if d <= 1:
                if d > 0.6:
                    c.put(x, y, OBSIDIAN[2 + (y < 3)], (0, 0.5, 0.8))
                else:
                    col = COAL[4] if d < 0.15 else COAL[3] if d < 0.35 else COAL[2]
                    c.put(x, y, col, (0, 0, 1), col)
    c.ink()
    c.save(folder, "lava_vent", glow=True)
    info["lava_vent"] = {"size": [c.w, c.h], "sways": False, "glow": True}
    c = Canvas(9, 12, seed=303)  # a charred stump with embers
    for y in range(4, 12):
        for x in range(2, 7):
            u = (x - 4) / 2.5
            c.put(x, y, WOOD[0] if abs(u) > 0.7 else WOOD[1] if u > 0 else WOOD[2], c.wall_normal(u))
    for x, y in ((3, 4), (5, 3), (4, 5)):
        c.put(x, y, COAL[2], glow=COAL[3])
    c.put(1, 11, WOOD[1])
    c.put(7, 11, WOOD[1])
    c.ink()
    c.save(folder, "charred_stump", glow=True)
    info["charred_stump"] = {"size": [c.w, c.h], "sways": False, "glow": True}
    info.update(crystal_prop(folder, "ember_crystal", COAL, 304, count=2))
    # Storm
    info.update(rock(folder, "slate_0", 10, 6, ramp("3a4048", "4a525c", "5c6670", "707a86", "8a94a0"), 310))
    info.update(rock(folder, "slate_1", 14, 8, ramp("3a4048", "4a525c", "5c6670", "707a86", "8a94a0"), 311, accent=hexc("8aa060")))
    info.update(crystal_prop(folder, "storm_crystal", SPARK[:2] + [hexc("6ab8ff"), hexc("a8dcff"), hexc("e8f8ff")], 312))
    c = Canvas(9, 18, seed=313)  # a standing stone with a carved bolt
    for y in range(2, 18):
        for x in range(1, 8):
            u = (x - 4) / 3.5
            if y < 4 and abs(u) > 0.6:
                continue
            t = 0.55 - 0.35 * u + c.rng.random() * 0.12
            c.put(x, y, ROCK[int(np.clip(t, 0, 0.999) * 5)], c.wall_normal(u))
    for x, y in ((4, 6), (3, 8), (5, 9), (4, 11)):
        c.put(x, y, hexc("8ad0ff"), glow=hexc("bfe8ff"))
    c.ink()
    c.save(folder, "standing_stone", glow=True)
    info["standing_stone"] = {"size": [c.w, c.h], "sways": False, "glow": True}
    # Nature
    for i in range(2):
        c = Canvas(14, 10, seed=320 + i)
        for f in range(5):
            a = math.pi * (0.15 + 0.7 * f / 4)
            for k in range(7):
                x = 7 - math.cos(a) * k
                y = 9 - math.sin(a) * k * 0.9
                c.put(x, y, LEAF[2 + (k > 3)] if k % 2 else LEAF[1 + (k > 3)], (-math.cos(a) * 0.5, 0.5, 0.7))
        c.ink()
        c.save(folder, f"fern_{i}")
        info[f"fern_{i}"] = {"size": [c.w, c.h], "sways": True}
    # Water
    ice = ramp("6a8eb0", "8ab0cc", "a8cce0", "c8e4f0", "eaf8ff")
    info.update(crystal_prop(folder, "ice_0", ice, 330, w=9, h=11, count=2))
    info.update(crystal_prop(folder, "ice_1", ice, 331, w=11, h=14, count=3))
    c = Canvas(12, 9, seed=332)  # a rock with snow on top
    c.disc(6, 5, 5.5, ROCK, seed=332)
    for x in range(1, 11):
        for k in range(2):
            c.put(x, 3 + k + (x % 3 == 0), hexc("f0f6ff") if k == 0 else hexc("d0dcea"), (0, 0.7, 0.7))
    c.ink()
    c.save(folder, "snow_rock")
    info["snow_rock"] = {"size": [c.w, c.h], "sways": False}
    c = Canvas(14, 11, seed=333)
    c.leaves(7, 6, 6.5, 4.5, ramp("3a4a5a", "56687a", "7a8ea0", "a8bccc"), count=6, seed=333)
    for x in range(2, 12, 2):
        c.put(x, 2 + (x % 4 == 0), hexc("f4f8ff"))
    c.ink()
    c.save(folder, "frozen_shrub")
    info["frozen_shrub"] = {"size": [c.w, c.h], "sways": True}
    # Earth
    info.update(rock(folder, "boulder_0", 11, 8, SANDSTONE, 340))
    info.update(rock(folder, "boulder_1", 16, 11, SANDSTONE, 341, accent=hexc("c48a5a")))
    for i, tall in enumerate((12, 16)):
        c = Canvas(11, tall, seed=342 + i)
        cactus = ramp("2a4a2a", "3a6236", "4e7c44", "6a9a56")
        for y in range(2, tall):
            for x in range(4, 7):
                u = (x - 5) / 1.5
                c.put(x, y, cactus[int(np.clip(0.6 - 0.4 * u, 0, 0.999) * 4)], c.wall_normal(u))
        for side, arm_y in ((-1, tall // 2), (1, tall // 2 - 2 - i)):
            for k in range(3):
                c.put(5 + side * (2 + k * 0.4), arm_y, cactus[1 + (side < 0)])
            for k in range(4):
                c.put(5 + side * 3, arm_y - k, cactus[2 if side < 0 else 1], (side * 0.5, 0.3, 0.8))
        c.put(5, 1, hexc("f0a0c0"))
        c.ink()
        c.save(folder, f"cactus_{i}")
        info[f"cactus_{i}"] = {"size": [c.w, c.h], "sways": False}
    c = Canvas(12, 6, seed=344)
    bone = ramp("b8ac90", "d8ccb0", "f0e8d0")
    c.line(1, 4, 10, 3, bone[1], (0, 0.5, 0.8))
    c.line(2, 2, 9, 5, bone[0], (0, 0.5, 0.8))
    for x, y in ((1, 3), (10, 2), (2, 1), (9, 5)):
        c.put(x, y, bone[2])
    c.ink()
    c.save(folder, "bones")
    info["bones"] = {"size": [c.w, c.h], "sways": False}
    # Void
    info.update(crystal_prop(folder, "void_crystal", VOID, 350))
    info.update(rock(folder, "obsidian_shard", 9, 9, OBSIDIAN[1:6], 351, accent=VOID[2], glow=True))
    info.update(rock(folder, "rift_stone", 14, 8, OBSIDIAN[:5], 352, accent=hexc("80f0ff"), glow=True))
    # Heart
    prism = [hexc("6a5a88"), hexc("8a7ab8"), hexc("d0a0ff"), hexc("a0e0ff"), hexc("fff8e0")]
    info.update(crystal_prop(folder, "prism_0", prism, 360))
    info.update(crystal_prop(folder, "prism_1", [hexc("885a3a"), hexc("c88a4a"), hexc("ffd070"), hexc("fff0a0"), hexc("ffffff")], 361, w=9, h=12, count=2))
    info.update(rock(folder, "marble_0", 11, 7, ramp("8a8478", "a8a090", "c4bca8", "dcd6c4", "f0ecdc"), 362))
    c = Canvas(10, 20, seed=363)  # a broken pillar
    marble = ramp("7a7468", "989080", "b4ac9a", "ccc4b0", "e4dcc8")
    for y in range(4, 20):
        for x in range(1, 9):
            u = (x - 4.5) / 4
            if y < 6 and x > 4 + (y - 4):
                continue
            t = 0.55 - 0.35 * u + (0.08 if x % 3 == 0 else 0)
            c.put(x, y, marble[int(np.clip(t, 0, 0.999) * 5)], c.wall_normal(u))
    for x in range(0, 10):
        c.put(x, 18, marble[2], (0, 0.5, 0.8))
    c.ink()
    c.save(folder, "ruin_pillar")
    info["ruin_pillar"] = {"size": [c.w, c.h], "sways": False}
    return info


# ---------------------------------------------------------------- ground per map
def read_map(path: str) -> dict:
    text = open(path).read()
    head, _, main = text.partition("[resource]")
    mid = re.search(r'^id = &"(\w+)"', main, re.M).group(1)
    grid = re.search(r"grid_size = Vector2i\((\d+), (\d+)\)", main)
    cell = re.search(r"cell_size = (\d+)", main)
    biome = re.search(r'^biome = &"(\w+)"', main, re.M)

    def points(line):
        return [(int(a), int(b)) for a, b in re.findall(r"Vector2i\((-?\d+), (-?\d+)\)", line)]

    # Lane 0 is the map's own waypoints; extra lanes are sub-resources above it.
    lanes = [points(re.search(r"^waypoints = (.*)", main, re.M).group(1))]
    lanes += [points(line) for line in re.findall(r"^waypoints = (.*)", head, re.M)]
    return {"id": mid, "grid": (int(grid.group(1)), int(grid.group(2))) if grid else (24, 15),
            "cell": int(cell.group(1)) if cell else 64, "waypoints": lanes[0], "lanes": lanes,
            "biome": biome.group(1) if biome else "meadow"}


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
    rng = np.random.default_rng(sum(map(ord, m["id"])))
    b = BIOMES.get(m.get("biome", "meadow"), BIOMES["meadow"])
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    dist = np.full((H, W), 1e9)
    for lane in m.get("lanes", [m["waypoints"]]):
        pts = [((x + 0.5) * cell_art, (y + 0.5) * cell_art) for x, y in lane]
        # Stretch the ends so the road runs off the edge of the board.
        if len(pts) >= 2:
            for i, j in ((0, 1), (-1, -2)):
                ax, ay = pts[i]
                bx, by = pts[j]
                d = math.hypot(ax - bx, ay - by) or 1
                pts[i] = (ax + (ax - bx) / d * cell_art * 2, ay + (ay - by) / d * cell_art * 2)
        dist = np.minimum(dist, distance_to_segments(xx, yy, pts))
    half = cell_art * 0.46
    wobble = (fbm(H, W, [7, 3], rng) - 0.5) * 4.0
    road_d = dist + wobble
    on_road = road_d < half
    edge = (road_d >= half - 1.2) & on_road

    patches = fbm(H, W, [26, 11, 5], rng)
    fine = value_noise(H, W, 2.2, rng)
    g = np.clip(patches * 0.85 + fine * 0.25 - 0.08, 0, 0.999)
    g -= np.clip(1.0 - (road_d - half) / 5.0, 0, 1) * 0.25
    g = np.clip(g, 0, 0.999)
    rgb = ramp_pick(b["ground"], g, dither=0.35)
    height = g * 0.6
    glow = np.zeros((H, W, 4), np.uint8)
    for _ in range(int(W * H / 75)):
        x, y = int(rng.integers(0, W)), int(rng.integers(3, H))
        if road_d[y, x] < half + 1:
            continue
        tall = 2 + (rng.random() < 0.4)
        lean = int(rng.choice([-1, 0, 0, 1]))
        rgb[y, x] = b["tuft"][0]
        for k in range(1, tall + 1):
            xk = min(max(x + (lean if k == tall else 0), 0), W - 1)
            rgb[y - k, xk] = b["tuft"][3] if k < tall else b["tip"]
            height[y - k, xk] = 0.9
    for _ in range(int(W * H / 2600 * b.get("flower_rate", 1.0))):
        x, y = int(rng.integers(2, W - 2)), int(rng.integers(2, H - 2))
        if road_d[y, x] < half + 3:
            continue
        col = b["flowers"][int(rng.integers(0, len(b["flowers"])))]
        rgb[y, x] = col
        rgb[y + 1, x] = b["tuft"][1]
        height[y, x] = 1.0
        if b.get("glow_flowers"):
            glow[y, x, :3] = np.clip(col, 0, 255).astype(np.uint8)
            glow[y, x, 3] = 200
    # Glowing cracks (lava under the ash) and glints (ice, rift light, prisms) off the road.
    if "cracks" in b:
        cols, width = b["cracks"]
        ridge = np.abs(fbm(H, W, [22, 9, 4], rng) - 0.5)
        crack = (ridge < width) & (road_d > half + 2) & (fbm(H, W, [30, 12], rng) > 0.45)
        rgb = np.where(crack[..., None], ramp_pick(cols[1:4], np.clip(1 - ridge / width, 0, 0.999)), rgb)
        height = np.where(crack, -0.4, height)
        glow[crack, :3] = np.clip(cols[3], 0, 255).astype(np.uint8)
        glow[crack, 3] = np.clip((1 - ridge[crack] / width) * 255, 90, 255).astype(np.uint8)
    if "glints" in b:
        cols, rate = b["glints"]
        for _ in range(int(W * H * rate)):
            x, y = int(rng.integers(1, W - 1)), int(rng.integers(1, H - 1))
            if road_d[y, x] < half + 1:
                continue
            col = cols[int(rng.integers(0, len(cols)))]
            rgb[y, x] = col
            glow[y, x, :3] = np.clip(col, 0, 255).astype(np.uint8)
            glow[y, x, 3] = 160

    dirt_t = np.clip(fbm(H, W, [12, 5, 3], rng) * 0.9 + 0.08, 0, 0.999)
    rut = np.abs(dist - 6.0) < 1.2
    dirt_t = np.clip(np.where(rut & on_road, dirt_t - 0.22, dirt_t), 0, 0.999)
    rgb = np.where(on_road[..., None], ramp_pick(b["road"], dirt_t, dither=0.5), rgb)
    rgb = np.where(edge[..., None], b["edge"], rgb)
    glow[on_road] = 0
    height = np.where(on_road, -0.6 + dirt_t * 0.3 - rut * 0.25, height)
    for _ in range(int(W * H / 1300)):
        x, y = int(rng.integers(1, W - 2)), int(rng.integers(1, H - 2))
        if road_d[y, x] > half - 3:
            continue
        pebble = b["pebbles"]
        rgb[y, x] = pebble[min(3, len(pebble) - 1)]
        rgb[y, x + 1] = pebble[min(2, len(pebble) - 1)]
        rgb[y + 1, x] = pebble[1]
        height[y, x] += 0.8
    edge_pts = np.argwhere(edge)
    for y, x in edge_pts[rng.random(len(edge_pts)) < 0.35]:
        if y > 2:
            rgb[y, x] = b["tuft"][2]
            rgb[y - 1, x] = b["tuft"][3]
            height[y, x] = 0.4

    folder = os.path.join(OUT, "ground")
    os.makedirs(folder, exist_ok=True)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(folder, m["id"] + ".png"))
    Image.fromarray(encode_normals(normals_from_height(height, 1.6), np.full((H, W), 255, np.uint8)), "RGBA").save(
        os.path.join(folder, m["id"] + "_n.png"))
    glow_path = os.path.join(folder, m["id"] + "_glow.png")
    if glow[..., 3].any():
        Image.fromarray(glow, "RGBA").save(glow_path)
    elif os.path.exists(glow_path):
        os.remove(glow_path)

    # Props: small things in the grass, never on the road. The game hides a cell's props when a
    # tower is built there.
    props = []
    kinds = [k for k, n in b["props"] for _ in range(n)]
    for _ in range(int(m["grid"][0] * m["grid"][1] * 0.75)):
        x, y = float(rng.uniform(4, W - 4)), float(rng.uniform(8, H - 2))
        kind = kinds[int(rng.integers(0, len(kinds)))]
        size = props_info[kind]["size"]
        if road_d[int(y), int(x)] < half + size[0] * 0.5 + 2:
            continue
        cell = [int(x // cell_art), int(y // cell_art)]
        props.append({"kind": kind, "pos": [round(x), round(y)], "cell": cell, "flip": bool(rng.random() < 0.5)})
    with open(os.path.join(folder, m["id"] + ".json"), "w") as fh:
        json.dump({"size": [W, H], "biome": m.get("biome", "meadow"), "props": props}, fh, indent=0)


def write_missing_imports() -> int:
    """Gives every new picture the Godot import file the others have (no mipmaps, lossless), so the art
    loads the same way whether or not the editor has opened the project since it was drawn."""
    import hashlib
    template_path = os.path.join(OUT, "towers", "fire_brazier.png.import")
    with open(template_path) as fh:
        template = fh.read()
    old_res = "res://assets/art/game/towers/fire_brazier.png"
    old_hash = hashlib.md5(old_res.encode()).hexdigest()
    old_uid = re.search(r'uid="(uid://\w+)"', template).group(1)
    alphabet = "abcdefghijklmnopqrstuvwxy012345678"
    written = 0
    for path in sorted(glob.glob(os.path.join(OUT, "**", "*.png"), recursive=True)):
        if os.path.exists(path + ".import"):
            continue
        res = "res://" + path.replace(os.sep, "/")
        digest = hashlib.md5(res.encode()).hexdigest()
        number = int(hashlib.sha1(res.encode()).hexdigest(), 16)
        uid = "uid://" + alphabet[number % 25] + "".join(alphabet[(number >> (5 * k)) % 34] for k in range(1, 13))
        text = template.replace(old_res, res).replace("fire_brazier.png-" + old_hash, os.path.basename(path) + "-" + digest)
        with open(path + ".import", "w") as fh:
            fh.write(text.replace(old_uid, uid))
        written += 1
    return written


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    art = {"art_scale": ART_SCALE, "towers": {}, "enemies": {}, "props": {}}
    # "--towers" or "--enemies" redraws only those and keeps everything else in art.json as it is.
    towers_only = "--towers" in sys.argv
    enemies_only = "--enemies" in sys.argv
    if towers_only or enemies_only:
        with open(os.path.join(OUT, "art.json")) as fh:
            art = json.load(fh)
    if enemies_only:
        art["enemies"] = {}
        for eid in sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob("data/enemies/*.tres")):
            if eid in ENEMIES:
                art["enemies"][eid] = ENEMIES[eid]()
        with open(os.path.join(OUT, "art.json"), "w") as fh:
            json.dump(art, fh, indent=1)
        print("Wrote the enemies in", OUT, "and", write_missing_imports(), "import files")
        return
    if towers_only:
        art["towers"] = {}
    tower_ids = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob("data/towers/*.tres"))
    for tid in tower_ids:
        if tid in TOWERS:
            art["towers"][tid] = TOWERS[tid]()
        elif tid.startswith("triple_"):
            art["towers"][tid] = triple_tower(tid, tower_elements(tid))
        else:
            print("No art recipe for tower", tid, "- the game draws a placeholder")
    if towers_only:
        with open(os.path.join(OUT, "art.json"), "w") as fh:
            json.dump(art, fh, indent=1)
        print("Wrote the towers in", OUT, "and", write_missing_imports(), "import files")
        return
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
    print("Wrote", OUT, "and", write_missing_imports(), "import files")


if __name__ == "__main__":
    main()
