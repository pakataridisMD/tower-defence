#!/usr/bin/env python3
"""Draws Nhal Vorath, the Crownless Citadel: the enemy fortress of the final assault.

usage: python3 tools/art/citadel/gen_citadel.py [--out DIR] [--preview FILE] [--zoom N]

A black fortress raised from the ruins of Vael, seen in the game's three-quarter view from the south: a
curtain wall with three gatehouses on its west face (the roads of the level start at their gates), corner
towers with needle roofs, a courtyard cracked with fire, and the keep in the middle, whose great door is
Solenne's stolen Dawn Gate, under a crown of black spikes with one socket empty and a black sun above it.

It covers the right edge of the assault map: board cells 30 to 42 across and -2 to 24 down (32 art px per
cell, like every sprite in the game), and it is drawn as one piece, so the game places it by its anchor.

Writes into assets/art/game/citadel/:
  citadel.png, citadel_n.png       the standing citadel and its normal map (lit by the board's lights)
  citadel_glow_<f>.png (4 frames)  what burns: windows, gates, fire cracks, the crown and the black sun
  citadel_cracks.png               fire cracks that open across it as it is broken (shown by health)
  ruin.png, ruin_n.png, ruin_glow.png  what is left once it has fallen
  citadel.json                     size, anchor (the centre cell the game puts it on), gate and light points
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pix2d"))
from kit import INK, LIGHT, ramp  # noqa: E402

OUT = os.path.join("assets", "art", "game", "citadel")

CELL = 32
# Board cells the picture covers.
X0, Y0, X1, Y1 = 30, -2, 42, 24
W, H = (X1 - X0) * CELL, (Y1 - Y0) * CELL
# The cell the game stands it on (StageData.structures[0].cell): its centre is the anchor.
ANCHOR_CELL = (36, 12)
# The road ends at the gates (board cells), from gen_campaign's finished map.
GATES = [(30, 8), (30, 12), (30, 16)]

# ------------------------------------------------------------------ colours
OBS = ramp("2c2834", spread=0.42, shift=0.02)          # black glass and basalt
OBS_L = ramp("3c3644", spread=0.45, shift=0.02)
BASALT = ramp("34303a", spread=0.4, shift=0.02)
IRON = ramp("4a4a52", spread=0.5, shift=0.0)
BONE = ramp("cfc4a8", spread=0.5)
BLOOD = ramp("5e1418", spread=0.45)
GOLD = ramp("a07a2c", spread=0.5)                      # what is left of the Dawn Gate's gilding
GROUND = ramp("17131c", spread=0.22, shift=0.02)
FIRE = [(120, 24, 16), (200, 60, 24), (250, 120, 40), (255, 190, 90), (255, 240, 200)]
VOID = [(40, 14, 60), (90, 30, 130), (150, 70, 210), (210, 150, 255)]
EMBER = (255, 96, 40)


def C(x, y):
    """Art pixel of a board point (cells)."""
    return (x - X0) * CELL, (y - Y0) * CELL


class Canvas:
    def __init__(self, seed=7):
        self.rgb = np.zeros((H, W, 3), np.uint8)
        self.a = np.zeros((H, W), bool)
        self.n = np.zeros((H, W, 3), np.float32)
        self.n[..., 2] = 1.0
        self.glow = np.zeros((H, W, 4), np.float32)      # straight-alpha emissive layer
        self.cracks = np.zeros((H, W, 4), np.float32)
        self.rng = random.Random(seed)
        self.lights = []

    # -- low level
    def _clip(self, x0, y0, x1, y1):
        return max(0, int(x0)), max(0, int(y0)), min(W, int(x1)), min(H, int(y1))

    def rect(self, x0, y0, x1, y1, col, normal=(0, 0, 1)):
        x0, y0, x1, y1 = self._clip(x0, y0, x1, y1)
        if x1 <= x0 or y1 <= y0:
            return
        self.rgb[y0:y1, x0:x1] = col
        self.a[y0:y1, x0:x1] = True
        self.n[y0:y1, x0:x1] = normal

    def px(self, x, y, col, normal=None):
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H:
            self.rgb[y, x] = col
            self.a[y, x] = True
            if normal is not None:
                self.n[y, x] = normal

    def mask_poly(self, pts):
        from PIL import ImageDraw
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([(round(x), round(y)) for x, y in pts], fill=1)
        return np.asarray(im, bool)

    def fill(self, mask, col, normal=(0, 0, 1)):
        self.rgb[mask] = col
        self.a |= mask
        self.n[mask] = normal

    def glow_px(self, x, y, col, alpha=1.0, layer=None):
        layer = self.glow if layer is None else layer
        x, y = int(x), int(y)
        if 0 <= x < W and 0 <= y < H:
            cur = layer[y, x]
            if alpha >= cur[3]:
                layer[y, x] = (col[0], col[1], col[2], alpha)

    def glow_rect(self, x0, y0, x1, y1, col, alpha=1.0, layer=None):
        for y in range(int(y0), int(y1)):
            for x in range(int(x0), int(x1)):
                self.glow_px(x, y, col, alpha, layer)

    def glow_disc(self, cx, cy, r, cols, layer=None, falloff=1.0):
        """A soft round glow in a few hard bands (pixel-art style)."""
        for y in range(int(cy - r), int(cy + r) + 1):
            for x in range(int(cx - r), int(cx + r) + 1):
                d = math.hypot(x + 0.5 - cx, y + 0.5 - cy) / max(r, 1)
                if d > 1:
                    continue
                band = min(len(cols) - 1, int((1 - d) * len(cols)))
                self.glow_px(x, y, cols[band], (1 - d) ** falloff * 0.9 + 0.1, layer)

    # -- building blocks
    def bricks(self, x0, y0, x1, y1, tones, seed, course=5, length=(7, 13), normal=(0, 0.18, 0.98), mortar=0,
               choices=(1, 2, 2, 2, 3)):
        """A wall face of dressed stone: courses of blocks, each a little different, mortar between."""
        rng = random.Random(seed)
        x0, y0, x1, y1 = int(x0), int(y0), int(x1), int(y1)
        self.rect(x0, y0, x1, y1, tones[1 + mortar], normal)
        y = y0
        row = 0
        while y < y1:
            h = min(course, y1 - y)
            x = x0 - (rng.randint(0, length[0]) if row % 2 else 0)
            while x < x1:
                ln = rng.randint(*length)
                bx0, bx1 = max(x, x0), min(x + ln - 1, x1)
                tone = tones[rng.choice(choices)]
                if bx1 > bx0 and h > 1:
                    self.rect(bx0, y, bx1, y + h - 1, tone, normal)
                    self.rect(bx0, y, bx1, y + 1, tones[min(4, tones.index(tone) + 1)], normal)   # lit top edge
                    if rng.random() < 0.12:                                                      # chip
                        cx = rng.randint(bx0, max(bx0, bx1 - 1))
                        self.px(cx, y + h - 2, tones[0])
                x += ln
            y += h
            row += 1

    def box(self, x0, x1, yb, yf, h, top, face, seed, course=5, crenel=False, cap=None, length=(7, 13),
            choices=(1, 2, 2, 2, 3)):
        """A block in three-quarter view: its ground runs from yb (back) to yf (front) in art px, and it
        stands h px tall. Draws the top, then the south face in courses of stone."""
        # the top face, seen from above at an angle: half its ground depth
        depth = max(2, int((yf - yb) * 0.5))
        ty1 = yf - h
        ty0 = ty1 - depth
        self.rect(x0, ty0, x1, ty1, top[2], (0, -0.62, 0.78))
        self.rect(x0, ty0, x1, ty0 + 1, top[3], (0, -0.62, 0.78))
        self.rect(x1 - 1, ty0, x1, ty1, top[1], (0.6, -0.4, 0.7))
        rng = random.Random(seed)
        for _ in range(int((x1 - x0) * depth / 40)):
            self.px(rng.randint(int(x0), int(x1) - 1), rng.randint(int(ty0), int(ty1) - 1), top[1])
        self.bricks(x0, ty1, x1, yf, face, seed, course, length=length, choices=choices)
        # shade toward the ground and a dark right edge
        self.rect(x1 - 1, ty1, x1, yf, face[0], (0.7, 0, 0.7))
        self.rect(x0, yf - 2, x1, yf, face[0])
        if crenel:
            self.crenels(x0, x1, ty0 + 1, top, face, seed)
        return ty0, ty1

    def crenels(self, x0, x1, y, top, face, seed, w=5, gap=4, h=5):
        x = x0
        rng = random.Random(seed)
        while x + w <= x1:
            self.rect(x, y - h, x + w, y - h + 2, top[3], (0, -0.62, 0.78))
            self.rect(x, y - h + 2, x + w, y + 1, face[2], (0, 0.18, 0.98))
            self.rect(x + w - 1, y - h + 2, x + w, y + 1, face[0])
            if rng.random() < 0.18:                      # a spike with a skull on some merlons
                self.spike(x + w // 2, y - h, 7, IRON)
                if rng.random() < 0.5:
                    self.skull(x + w // 2, y - h - 4)
            x += w + gap

    def spike(self, x, y, ln, tones):
        for i in range(ln):
            self.px(x, y - i, tones[3] if i < ln - 2 else tones[4])
            if i < ln // 3:
                self.px(x + 1, y - i, tones[1])

    def skull(self, x, y):
        for dx, dy in [(-1, 0), (0, 0), (1, 0), (-1, 1), (1, 1), (0, -1), (-1, -1), (1, -1)]:
            self.px(x + dx, y + dy, BONE[3] if dy < 1 else BONE[2])
        self.px(x - 1, y, INK)
        self.px(x + 1, y, INK)
        self.px(x, y + 1, BONE[1])

    def slit(self, x, y, h, seed, col=None, w=2):
        """A narrow window lit from inside."""
        col = col or FIRE
        x, y, h = int(round(x)), int(round(y)), int(round(h))
        self.rect(x - 1, y - 1, x + w + 1, y + h + 1, OBS[0])
        self.rect(x, y, x + w, y + h, (40, 10, 10))
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.glow_px(xx, yy, col[3] if yy < y + 2 else col[2], 1.0)
        self.glow_px(x, y + h, col[1], 0.6)
        self.lights.append(("window", x + w / 2, y + h / 2))

    def needle(self, cx, base_y, half, height, tones, seed, windows=0):
        """A needle roof or spire: a tall triangle, lit on the left, dark on the right."""
        left = self.mask_poly([(cx - half, base_y), (cx, base_y - height), (cx, base_y)])
        right = self.mask_poly([(cx, base_y - height), (cx + half, base_y), (cx, base_y)])
        self.fill(left, tones[3], (-0.7, -0.3, 0.65))
        self.fill(right, tones[1], (0.7, -0.3, 0.65))
        # a ridge line and a few slate courses
        for i in range(0, int(height), 6):
            y = base_y - i
            w = half * (1 - i / height)
            self.rect(cx - w, y, cx - w + 1, y + 1, tones[2])
        for i in range(int(height)):
            self.px(cx, base_y - i, tones[4] if i % 3 else tones[2])
        rng = random.Random(seed)
        for k in range(windows):
            y = base_y - height * (0.25 + 0.2 * k)
            self.slit(int(cx - 1), int(y), 4, seed + k, w=2)
        # a barbed tip
        self.spike(int(cx), int(base_y - height), 5, IRON)

    def tower(self, cx, yf, r, h, roof_h, seed, windows=2, banner=False):
        """A square tower with a needle roof, standing on ground point (cx, yf)."""
        x0, x1 = cx - r, cx + r
        ty0, ty1 = self.box(x0, x1, yf - r, yf, h, OBS_L, OBS, seed, course=4, crenel=True)
        for k in range(windows):
            self.slit(int(cx - 1), int(ty1 + 6 + k * 14), 6, seed + k)
        self.needle(cx, ty0 - 2, r + 2, roof_h, OBS_L, seed, windows=1)
        if banner:
            self.banner(cx - r + 2, ty1 + 2, 6, 18, seed)

    def banner(self, x, y, w, h, seed):
        rng = random.Random(seed)
        self.rect(x - 1, y - 1, x + w + 1, y, IRON[2])
        for xx in range(int(x), int(x + w)):
            ln = h - rng.randint(0, 5)
            for yy in range(int(y), int(y + ln)):
                tone = BLOOD[2] if xx < x + w / 2 else BLOOD[1]
                if (yy - y) % 9 == 0:
                    tone = BLOOD[0]
                self.px(xx, yy, tone)
        # the Crownless sigil: a crown with no stone, in dull gold
        cx, cy = int(x + w / 2), int(y + h * 0.35)
        for dx in (-2, 0, 2):
            self.px(cx + dx, cy - 1, GOLD[2])
        for dx in range(-2, 3):
            self.px(cx + dx, cy, GOLD[1])

    def gatehouse(self, gx, gy, seed):
        """A gatehouse on the west wall: a block that juts out toward the road, with a pointed arch whose
        inside burns, the portcullis teeth raised, braziers either side."""
        x, y = C(gx + 0.5, gy + 0.5)
        x0, x1 = x - 8, x + 46
        yf = y + 22
        ty0, ty1 = self.box(x0, x1, yf - 34, yf, 58, OBS_L, OBS, seed, course=5, crenel=True)
        self.rect(x0, ty1, x0 + 1, yf, RIM)
        # the arch
        ax0, ax1 = x - 2, x + 22
        top = yf - 40
        arch = self.mask_poly([(ax0, yf), (ax0, top + 10), (ax0 + 4, top + 3), ((ax0 + ax1) / 2, top - 4),
                               (ax1 - 4, top + 3), (ax1, top + 10), (ax1, yf)])
        self.fill(arch, (18, 8, 10))
        ring = arch & ~np.roll(arch, 1, 0) | arch & ~np.roll(arch, 1, 1) | arch & ~np.roll(arch, -1, 1)
        self.fill(ring, OBS[0])
        ys, xs = np.nonzero(arch & ~ring)
        for yy, xx in zip(ys, xs):
            d = (yf - yy) / 44.0
            band = 3 if d < 0.35 else 2 if d < 0.65 else 1
            self.glow_px(xx, yy, FIRE[band], 0.85 - 0.3 * d)
        # portcullis teeth hanging at the top of the arch
        for tx in range(int(ax0 + 3), int(ax1 - 2), 4):
            for k in range(6):
                self.px(tx, top + 6 + k, IRON[2] if k < 5 else IRON[3])
        # braziers on either side of the arch
        for bx in (ax1 + 5,):
            self.rect(bx - 2, yf - 14, bx + 3, yf - 10, IRON[1])
            self.rect(bx, yf - 10, bx + 1, yf, IRON[0])
            self.glow_disc(bx + 0.5, yf - 17, 5, FIRE[1:])
            self.lights.append(("brazier", bx + 0.5, yf - 17))
        self.banner(x1 - 12, ty1 + 4, 7, 20, seed + 3)
        self.lights.append(("gate", (ax0 + ax1) / 2, yf - 14))

    # -- finish
    def ink(self):
        a = self.a
        out = np.zeros_like(a)
        out[1:] |= a[:-1]
        out[:-1] |= a[1:]
        out[:, 1:] |= a[:, :-1]
        out[:, :-1] |= a[:, 1:]
        edge = out & ~a
        self.rgb[edge] = INK
        self.a |= edge

    def images(self):
        rgba = np.dstack([self.rgb, self.a.astype(np.uint8) * 255])
        n = self.n / np.linalg.norm(self.n, axis=-1, keepdims=True)
        n = n * 0.5 + 0.5
        n[..., 1] = 1 - n[..., 1]
        nrm = np.dstack([(n * 255).astype(np.uint8), self.a.astype(np.uint8) * 255])
        return Image.fromarray(rgba, "RGBA"), Image.fromarray(nrm, "RGBA")


def glow_image(layer):
    rgb = np.clip(layer[..., :3], 0, 255).astype(np.uint8)
    a = (np.clip(layer[..., 3], 0, 1) * 255).astype(np.uint8)
    return Image.fromarray(np.dstack([rgb, a]), "RGBA")


# ------------------------------------------------------------------ the citadel

def shade_face(c: Canvas, x0, y0, x1, y1, top=1.0, bottom=0.55):
    """Darkens a wall face toward its foot in hard bands (dithered where they meet), so tall faces read as
    tall and the fire below can light them again."""
    x0, y0, x1, y1 = c._clip(x0, y0, x1, y1)
    if y1 - y0 < 2:
        return
    for y in range(y0, y1):
        t = (y - y0) / max(1, y1 - y0 - 1)
        f = top + (bottom - top) * t
        q = round(f / 0.09) * 0.09
        for x in range(x0, x1):
            if not c.a[y, x]:
                continue
            g = q if (x + y) % 2 or abs(f - q) < 0.03 else q + (0.09 if f > q else -0.09)
            c.rgb[y, x] = np.clip(c.rgb[y, x].astype(np.float32) * g, 0, 255).astype(np.uint8)


def shade_across(c: Canvas, x0, y0, x1, y1, left=1.1, right=0.8):
    """Light from the left: a face brightens toward its west end in hard dithered steps."""
    x0, y0, x1, y1 = c._clip(x0, y0, x1, y1)
    for x in range(x0, x1):
        t = (x - x0) / max(1, x1 - x0 - 1)
        f = left + (right - left) * t
        q = round(f / 0.08) * 0.08
        col = c.rgb[y0:y1, x].astype(np.float32)
        alt = q + (0.08 if f > q else -0.08)
        g = np.where((np.arange(y0, y1) + x) % 2 == 0, alt if abs(f - q) > 0.025 else q, q)
        c.rgb[y0:y1, x] = np.clip(col * g[:, None], 0, 255).astype(np.uint8)


def courtyard(c: Canvas, ruined=False):
    """The ground inside the walls: black flagstones split by fire, and the fire-filled ditch at the foot of
    the keep."""
    x0, y0 = C(31, 3)
    x1, y1 = C(42, 23.5)
    c.bricks(x0, y0, x1, y1, GROUND, 3, course=8, length=(12, 26), normal=(0, -0.62, 0.78), choices=(1, 2, 2, 2))
    shade_face(c, x0, y0, x1, y1, 0.7, 0.85)
    rng = random.Random(3)
    for k in range(10 if not ruined else 16):
        x, y = rng.uniform(x0 + 6, x1 - 6), rng.uniform(y0 + 10, y1 - 4)
        for _ in range(rng.randint(14, 34)):
            c.glow_px(x, y, FIRE[2], 0.8)
            c.px(x, y, (40, 12, 10))
            x += rng.choice((-1, 0, 1, 1))
            y += rng.choice((-1, 0, 1))
    # pools and rifts of fire at the foot of the keep, broken and lopsided
    kx, _ = C(37, 0)
    _, ky = C(0, 17.5)
    for k, (dx, dy, rx, ry) in enumerate([(-128, 10, 22, 9), (-70, 30, 12, 5), (96, 22, 16, 6), (20, 44, 9, 4),
                                          (-30, 70, 14, 5), (70, 64, 8, 3)]):
        lava_pool(c, kx + dx, ky + dy, rx, ry, 50 + k, ruined)



def curtain_wall(c: Canvas, ruined=False, seed=11):
    """The north wall at the back, the long west wall walk (its gatehouses are drawn later) and its outer
    face."""
    h = 34 if not ruined else 12
    # north wall
    x0, yb = C(31, 2)
    x1, yf = C(42, 3)
    ty0, ty1 = c.box(x0, x1 + 4, yb, yf, h, OBS_L, OBS, seed, crenel=not ruined)
    shade_face(c, x0, ty1, x1 + 4, yf, 0.9, 0.5)
    # west wall: a band from the north-west corner to the south-west, seen from above
    wx0, wy0 = C(31, 2.5)
    wx1, wy1 = C(32.2, 23)
    c.rect(wx0, wy0 - h, wx1, wy1 - h, OBS_L[2], (0, -0.62, 0.78))
    c.rect(wx0, wy0 - h, wx0 + 2, wy1 - h, OBS_L[3], (-0.6, -0.4, 0.7))
    c.rect(wx1 - 2, wy0 - h, wx1, wy1 - h, OBS[1], (0.6, -0.4, 0.7))
    # the inner (east) face of the west wall, standing over the courtyard
    c.bricks(wx1, wy0 - h + 2, wx1 + 8, wy1, OBS, seed + 2, course=5, length=(4, 7), normal=(0.8, 0.1, 0.6))
    shade_face(c, wx1, wy0 - h, wx1 + 8, wy1, 0.75, 0.45)
    # the wall's outer (west) face shows as a thin dark strip below the walk
    c.bricks(wx0 - 6, wy0 - h + 4, wx0, wy1, BASALT, seed + 1, course=4, length=(4, 6), normal=(-0.8, 0.1, 0.6))
    if not ruined:
        y = wy0 - h
        rng = random.Random(seed)
        while y < wy1 - h - 4:
            c.rect(wx0 - 1, y, wx0 + 4, y + 4, OBS_L[3], (0, -0.62, 0.78))
            c.rect(wx0 - 1, y + 4, wx0 + 4, y + 6, OBS[2])
            if rng.random() < 0.25:
                c.spike(wx0 + 1, y, 8, IRON)
                if rng.random() < 0.6:
                    c.skull(wx0 + 1, y - 5)
            y += 9


def lava_pool(c: Canvas, cx, cy, rx, ry, seed, ruined=False):
    """A ragged rift in the flagstones with fire in it."""
    rng = random.Random(seed)
    pts = []
    for k in range(14):
        a = math.tau * k / 14
        r = rng.uniform(0.55, 1.15)
        pts.append((cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r))
    hole = c.mask_poly(pts)
    rim = hole & ~(np.roll(hole, 1, 0) & np.roll(hole, -1, 0) & np.roll(hole, 1, 1) & np.roll(hole, -1, 1))
    c.fill(hole, (60, 16, 10))
    ys, xs = np.nonzero(hole & ~rim)
    for yy, xx in zip(ys, xs):
        d = math.hypot((xx - cx) / rx, (yy - cy) / ry)
        band = 4 if d < 0.25 else 3 if d < 0.55 else 2
        c.glow_px(xx, yy, FIRE[band if not ruined else band - 1], 0.95 if not ruined else 0.7)
    c.fill(rim, OBS[0])
    # the far lip catches no light, the near lip is lit from below
    ys, xs = np.nonzero(rim)
    for yy, xx in zip(ys, xs):
        if yy > cy:
            c.px(xx, yy, (110, 40, 24))


ROOT = ramp("2a1e2c", spread=0.42, shift=0.03)


def root(c: Canvas, x, y, ang, length, width, seed, depth=0):
    """One black root of the citadel crawling over the ground, thinning as it goes, with a violet vein of
    the Hollow's light down its middle. It branches as it goes."""
    rng = random.Random(seed)
    ln = 0.0
    while ln < length and width > 0.6:
        t = ln / length
        r = width * (1 - 0.75 * t)
        for yy in range(int(y - r - 1), int(y + r + 2)):
            for xx in range(int(x - r - 1), int(x + r + 2)):
                dx, dy = (xx + 0.5 - x) / max(r, 0.5), (yy + 0.5 - y) / max(r, 0.5) * 1.6
                if dx * dx + dy * dy > 1:
                    continue
                lit = -(dx * 0.7 + dy * 0.7)
                tone = ROOT[4] if lit > 0.75 else ROOT[3] if lit > 0.25 else ROOT[2] if lit > -0.3 else ROOT[1]
                c.px(xx, yy, tone, (dx * 0.7, dy * 0.4, 0.6))
        if r > 1.6 and rng.random() < 0.8:
            c.glow_px(x, y, VOID[2] if rng.random() < 0.7 else VOID[3], 0.75)
        ang += rng.uniform(-0.28, 0.28)
        x += math.cos(ang) * 1.6
        y += math.sin(ang) * 1.0
        ln += 1.6
        if depth < 2 and rng.random() < 0.035 and r > 2:
            root(c, x, y, ang + rng.choice((-1, 1)) * rng.uniform(0.6, 1.1), length * (1 - t) * 0.6, r * 0.7,
                 rng.randrange(10 ** 6), depth + 1)


def roots(c: Canvas, ruined=False):
    """The roots the citadel has sent out across the Hollow, out under its walls and toward the roads."""
    kx, _ = C(37, 0)
    _, ky = C(0, 17.5)
    spots = [(-100, -6, math.pi * 1.0, 190, 10), (-84, 8, math.pi * 0.82, 150, 9), (-56, 12, math.pi * 0.64, 140, 8),
             (-14, 14, math.pi * 0.52, 110, 7), (36, 12, math.pi * 0.4, 120, 8), (88, 8, math.pi * 0.28, 100, 8),
             (-102, -50, math.pi * 1.08, 160, 9), (-102, -110, math.pi * 1.16, 150, 8), (104, -90, -math.pi * 0.15, 70, 7),
             (-100, -30, math.pi * 0.92, 200, 7), (104, -20, math.pi * 0.1, 60, 8), (-60, 14, math.pi * 0.75, 170, 6),
             (-80, -160, math.pi * 1.25, 120, 7), (70, -150, -math.pi * 0.3, 70, 6)]
    for i, (dx, dy, ang, ln, w) in enumerate(spots):
        root(c, kx + dx, ky + dy, ang, ln * (0.6 if ruined else 1.0), w, 400 + i)


def box_lit(c: Canvas, x0, x1, yb, yf, h, seed, course=6, crenel=True, bottom=0.55):
    """A block of the keep: c.box, then a cold rim down its lit edge and the face darkened toward its foot."""
    ty0, ty1 = c.box(x0, x1, yb, yf, h, OBS_L, OBS, seed, course=course, crenel=crenel, length=(11, 20),
                     choices=(2, 2, 2, 1, 3))
    shade_face(c, x0, ty1, x1, yf, 1.0, bottom)
    shade_across(c, x0, ty1, x1, yf, 1.12, 0.78)
    c.rect(x0, ty1, x0 + 1, yf, RIM, (-0.8, 0, 0.6))
    c.rect(x0, ty0, x1, ty0 + 1, RIM, (0, -0.8, 0.6))
    return ty0, ty1


RIM = (112, 100, 140)


def barbed_needle(c: Canvas, cx, base_y, half, height, seed, windows=0, lean=0.0, glow_seam=False):
    """A spire: c.needle with hooked barbs up both edges, leaning a little, and maybe a burning seam."""
    tip_x = cx + lean
    left = c.mask_poly([(cx - half, base_y), (tip_x, base_y - height), (cx, base_y)])
    right = c.mask_poly([(tip_x, base_y - height), (cx + half, base_y), (cx, base_y)])
    c.fill(left, OBS_L[3], (-0.7, -0.3, 0.65))
    c.fill(right, OBS[1], (0.7, -0.3, 0.65))
    shade_face(c, cx - half, base_y - height, cx + half + 1, base_y, 1.05, 0.7)
    rng = random.Random(seed)
    for i in range(int(height)):
        t = i / height
        x = cx + lean * t
        c.px(x, base_y - i, OBS_L[4] if i % 4 else OBS_L[2])
        if glow_seam and 0.12 < t < 0.85 and i % 3:
            c.glow_px(x + 1, base_y - i, VOID[2] if i % 7 else VOID[3], 0.9)
    # barbs: little hooks thrown out and up from both edges
    step = max(10, int(height / 7))
    for i in range(step, int(height * 0.85), step):
        t = i / height
        w = half * (1 - t)
        for side in (-1, 1):
            bx = cx + lean * t + side * w
            by = base_y - i
            ln = int(3 + 4 * (1 - t))
            for k in range(ln):
                c.px(bx + side * k, by - k * 0.7 - (k * k) * 0.08, OBS_L[3] if side < 0 else OBS[1])
    for k in range(windows):
        y = base_y - height * (0.2 + 0.18 * k)
        c.slit(int(cx + lean * (0.2 + 0.18 * k) - 1), int(y), 5, seed + k, col=VOID if k % 2 else FIRE)
    c.spike(int(tip_x), int(base_y - height), 7, IRON)


def keep(c: Canvas, ruined=False, seed=21):
    """The keep: three tiers of black stone, buttressed and barbed, the defaced Dawn Gate in its face,
    leaning spires, and the great central spire under the crown of spikes and the black sun."""
    cx, _ = C(37, 0)
    _, gy = C(0, 17.5)
    if ruined:
        box_lit(c, cx - 96, cx + 98, gy - 40, gy, 30, seed, course=5, crenel=False)
        for sx, h in [(-80, 60), (-34, 90), (40, 70), (82, 40)]:
            c.box(cx + sx - 10, cx + sx + 10, gy - 30, gy - 18, h, OBS_L, OBS, seed + sx, course=4)
            for k in range(4):
                c.px(cx + sx - 10 + k * 5, gy - 18 - h - (k % 2) * 4, OBS_L[3])
        rubble(c, cx, gy - 10, 120, 34, seed)
        return
    # tier 1: the great hall
    t1y0, t1y1 = box_lit(c, cx - 104, cx + 106, gy - 34, gy, 150, seed, course=7, bottom=0.5)
    # buttresses: stepped black piers with spikes
    for bx in (-98, -64, 56, 92):
        bx0 = cx + bx
        for step, (inset, top) in enumerate([(0, 40), (2, 90), (4, 130)]):
            c.rect(bx0 + inset, gy - top, bx0 + 12 - inset, gy, OBS_L[2] if step == 0 else OBS_L[1], (-0.3, 0.1, 0.9))
            c.rect(bx0 + 10 - inset, gy - top, bx0 + 12 - inset, gy, OBS[0])
            c.rect(bx0 + inset, gy - top, bx0 + 12 - inset, gy - top + 2, OBS_L[3])
        shade_face(c, bx0, gy - 130, bx0 + 12, gy, 1.0, 0.5)
        barbed_needle(c, bx0 + 6, gy - 130, 7, 36, seed + bx)
    # windows, uneven, lit by fire low and by the Hollow higher up
    for wx, wy, h, col in [(-82, 40, 10, FIRE), (-46, 26, 12, FIRE), (-82, 92, 8, FIRE), (34, 54, 10, FIRE),
                           (74, 28, 12, VOID), (74, 86, 8, FIRE), (-46, 104, 8, VOID)]:
        c.slit(cx + wx, t1y1 + wy, h, seed + wx + wy, col=col)
    dawn_gate(c, cx, gy, seed)
    # tier 2 and tier 3, each set back and taller for it
    t2y0, t2y1 = box_lit(c, cx - 74, cx + 76, t1y0 - 14, t1y0 + 8, 110, seed + 1, course=6)
    for wx, wy, h, col in [(-56, 22, 16, VOID), (-22, 40, 10, FIRE), (20, 18, 14, VOID), (52, 56, 10, FIRE)]:
        c.slit(cx + wx, t2y1 + wy, h, seed + wx + 1, col=col)
    t3y0, t3y1 = box_lit(c, cx - 44, cx + 46, t2y0 - 10, t2y0 + 6, 80, seed + 2, course=6)
    for wx, wy, h in [(-28, 16, 18), (24, 26, 14)]:
        c.slit(cx + wx, t3y1 + wy, h, seed + wx + 3, col=VOID)
    # leaning spires on the tiers, none the same
    for sx, base, ht, half, lean in [(-94, t1y0 + 2, 150, 17, -10), (96, t1y0 + 2, 116, 15, 8),
                                     (-64, t2y0 + 4, 120, 14, -5), (66, t2y0 + 4, 132, 15, 6)]:
        c.rect(cx + sx - 9, base - 24, cx + sx + 9, base, OBS[2])
        c.rect(cx + sx - 9, base - 24, cx + sx - 8, base, RIM)
        c.rect(cx + sx + 7, base - 24, cx + sx + 9, base, OBS[0])
        c.slit(cx + sx - 1, base - 19, 9, seed + sx, col=FIRE if sx < 0 else VOID)
        barbed_needle(c, cx + sx, base - 24, half, ht, seed + sx, windows=2, lean=lean)
    # flying arches from the third tier to the inner spires
    for side in (-1, 1):
        x0, y0 = cx + side * 44, t3y1 + 10
        x1, y1 = cx + side * 64, t2y0 - 20
        for i in range(30):
            t = i / 29
            x = x0 + (x1 - x0) * t
            y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * 14
            c.rect(x - 1, y, x + 2, y + 3, OBS_L[2])
            c.px(x, y, OBS_L[4])
    # the central spire: a black tower, then the great needle with a burning violet seam
    base = t3y0 + 2
    c.box(cx - 18, cx + 20, base - 14, base, 54, OBS_L, OBS, seed + 9, course=5, crenel=True)
    shade_face(c, cx - 18, base - 54, cx + 20, base, 1.0, 0.6)
    c.slit(cx - 1, base - 46, 20, seed + 99, col=VOID)
    needle_base = base - 54 - 8
    tip = needle_base - 168
    barbed_needle(c, cx + 1, needle_base, 24, 168, seed + 98, windows=3, glow_seam=True)
    crown(c, cx + 1, tip + 30)


def dawn_gate(c: Canvas, cx, gy, seed):
    """Solenne's own Dawn Gate, torn from the city and hung in the keep: its gold half stripped, its sun
    scratched out, the fire of the hall showing through its seams."""
    dw, dh = 46, 84
    door = c.mask_poly([(cx - dw / 2, gy), (cx - dw / 2, gy - dh + 18), (cx - dw / 2 + 8, gy - dh + 5), (cx, gy - dh),
                        (cx + dw / 2 - 8, gy - dh + 5), (cx + dw / 2, gy - dh + 18), (cx + dw / 2, gy)])
    frame = c.mask_poly([(cx - dw / 2 - 7, gy), (cx - dw / 2 - 7, gy - dh + 16), (cx - dw / 2 + 4, gy - dh - 2),
                         (cx, gy - dh - 12), (cx + dw / 2 - 4, gy - dh - 2), (cx + dw / 2 + 7, gy - dh + 16),
                         (cx + dw / 2 + 7, gy)])
    c.fill(frame & ~door, GOLD[1], (0, 0.1, 1))
    rng = random.Random(seed + 5)
    ys, xs = np.nonzero(frame & ~door)
    for yy, xx in zip(ys, xs):
        if rng.random() < 0.45:
            c.px(xx, yy, GOLD[2] if rng.random() < 0.4 else OBS[1])
    c.fill(door, (26, 10, 12))
    ys, xs = np.nonzero(door)
    for yy, xx in zip(ys, xs):
        d = (gy - yy) / dh
        if abs(xx - cx) < 1:
            c.glow_px(xx, yy, FIRE[2], 0.9)
        elif (xx * 7 + yy * 3) % 29 == 0:
            c.glow_px(xx, yy, FIRE[3], 0.9)
        else:
            c.px(xx, yy, IRON[0] if (yy // 7) % 2 else (34, 30, 36))
            if (yy % 7) == 0:
                c.px(xx, yy, IRON[1])
        if d < 0.18:
            c.glow_px(xx, yy, FIRE[2], 0.6 * (1 - d / 0.18))
    # the sun of Solenne on the gate, scratched through with three claw marks
    sy = gy - dh + 30
    for a in range(0, 360, 15):
        c.px(cx + 10 * math.cos(math.radians(a)), sy + 10 * math.sin(math.radians(a)), GOLD[3])
    for k in (-5, 0, 5):
        for i in range(-12, 13):
            c.px(cx + k + i * 0.35, sy + i, (10, 4, 6))
    # a spiked lintel above it, off centre, and chains hung from it
    for i in range(-30, 31, 6):
        c.spike(cx + i, gy - dh - 8 - (4 if i == -6 else 0), 9 if i % 12 else 13, IRON)
    c.lights.append(("gate", cx, gy - 26))


def crown(c: Canvas, cx, cy):
    """The Crownless crown high on the central spire: a ring of black spikes around six burning stones and
    an empty seventh socket, and the black sun above it, a disc of nothing with a violet corona."""
    sy = cy - 48
    # rays and corona first (in the glow), then the disc itself
    for k in range(14):
        a = math.tau * k / 14 + 0.2
        ln = 46 if k % 2 else 30
        for i in range(18, ln):
            c.glow_px(cx + math.cos(a) * i, sy + math.sin(a) * i, VOID[2] if i < ln - 8 else VOID[1], 0.85 - (i - 18) / ln * 0.6)
    c.glow_disc(cx, sy, 30, VOID, falloff=1.4)
    for y in range(int(sy - 18), int(sy + 19)):
        for x in range(int(cx - 18), int(cx + 19)):
            d = math.hypot(x + 0.5 - cx, y + 0.5 - sy)
            if d <= 16.5:
                c.px(x, y, (4, 2, 8))
                c.glow_px(x, y, (0, 0, 0), 0.0)
                c.glow[y, x] = (0, 0, 0, 0)
            elif d <= 18:
                c.glow[y, x] = (*VOID[3], 1.0)
    c.lights.append(("sun", cx, sy))
    # the ring of spikes, tall in the middle, in front of the spire
    c.rect(cx - 26, cy - 2, cx + 27, cy + 5, IRON[1])
    c.rect(cx - 26, cy - 2, cx + 27, cy - 1, IRON[3])
    for k in range(11):
        t = (k - 5) / 5.0
        a = -math.pi / 2 + t * 1.05
        ln = 34 - abs(t) * 14
        bx = cx + t * 24
        for i in range(int(ln)):
            w = 2 if i < ln * 0.45 else 1
            x, y = bx + math.cos(a) * i, cy - 1 + math.sin(a) * i
            c.px(x, y, OBS_L[3], (-0.5, -0.5, 0.7))
            if w == 2:
                c.px(x + 1, y, OBS[0])
        c.px(bx + math.cos(a) * ln, cy - 1 + math.sin(a) * ln, IRON[4])
    # six sockets in the six colours of the kingdoms, the seventh empty and black
    colours = [(255, 110, 50), (150, 200, 255), (110, 220, 110), (80, 180, 230), (210, 170, 90), (180, 120, 255)]
    for k in range(7):
        x = cx - 21 + k * 7
        if k == 3:
            c.rect(x, cy, x + 3, cy + 3, (0, 0, 0))
            continue
        col = colours[k if k < 3 else k - 1]
        for dx in range(3):
            for dy in range(3):
                c.glow_px(x + dx, cy + dy, col, 1.0 if (dx, dy) != (2, 2) else 0.6)


def rubble(c: Canvas, cx, cy, rx, ry, seed):
    rng = random.Random(seed)
    for _ in range(int(rx * ry / 12) + 40):
        a = rng.uniform(0, math.tau)
        r = rng.random() ** 0.6
        x, y = cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r
        w, h = rng.randint(3, 9), rng.randint(2, 6)
        tone = rng.choice(OBS_L[1:4])
        c.rect(x, y, x + w, y + h, tone, (0, -0.5, 0.8))
        c.rect(x, y, x + w, y + 1, OBS_L[4])
        if rng.random() < 0.08:
            c.glow_px(x + 1, y + h, FIRE[2], 0.8)


def south_wall(c: Canvas, ruined=False, seed=31):
    x0, yb = C(31, 22.6)
    x1, yf = C(42, 23.6)
    h = 40 if not ruined else 14
    ty0, ty1 = c.box(x0, x1 + 4, yb, yf, h, OBS_L, OBS, seed, crenel=not ruined)
    shade_face(c, x0, ty1, x1 + 4, yf, 1.0, 0.6)
    if not ruined:
        for wx in (40, 128, 196, 290):
            c.slit(x0 + wx, yf - h + 14, 8, seed + wx)
        c.banner(x0 + 70, yf - h + 4, 8, 26, seed + 5)
        c.banner(x0 + 238, yf - h + 4, 8, 26, seed + 6)
    else:
        rubble(c, (x0 + x1) / 2, yf - 6, 150, 10, seed)


def corner_towers(c: Canvas, ruined=False):
    # back corners, then front corners last (they stand in front of the walls)
    spots = [((31.4, 3.0), 40, 92, 101, False), ((41.6, 3.0), 30, 70, 102, False),
             ((31.4, 23.8), 48, 104, 103, True), ((41.6, 23.8), 40, 84, 104, False)]
    for (gx, gy), h, roof, seed, banner in spots:
        x, y = C(gx, gy)
        if ruined:
            c.box(x - 15, x + 15, y - 14, y, 18, OBS_L, OBS, seed, course=4)
            rubble(c, x, y - 4, 22, 8, seed)
            continue
        ty0, ty1 = c.box(x - 15, x + 15, y - 15, y, h + 30, OBS_L, OBS, seed, course=4, crenel=True)
        shade_face(c, x - 15, ty1, x + 15, y, 1.0, 0.55)
        c.rect(x - 15, ty1, x - 14, y, RIM)
        c.slit(int(x - 1), int(ty1 + 8), 7, seed, col=FIRE)
        barbed_needle(c, x, ty0 - 2, 17, roof, seed, windows=1, lean=-4 if gx < 35 else 4)
        if banner:
            c.banner(x - 13, ty1 + 2, 6, 20, seed)


def bounce_light(c: Canvas, strength=1.0, radius=12):
    """The fire lights the stone around it: blur what burns and add it to the stone's colour, in a few
    hard steps so it stays pixel art."""
    g = c.glow[..., :3] * c.glow[..., 3:4]
    for _ in range(3):
        g = box_blur(g, radius)
    add = np.round(g * strength / 12) * 12
    rgb = c.rgb.astype(np.float32) + add * c.a[..., None]
    c.rgb = np.clip(rgb, 0, 255).astype(np.uint8)


def box_blur(img, r):
    out = img
    for axis in (0, 1):
        pad = [(0, 0)] * img.ndim
        pad[axis] = (r + 1, r)
        cs = np.cumsum(np.pad(out, pad, mode="edge"), axis=axis)
        n = out.shape[axis]
        hi = np.take(cs, np.arange(2 * r + 1, 2 * r + 1 + n), axis=axis)
        lo = np.take(cs, np.arange(0, n), axis=axis)
        out = (hi - lo) / (2 * r + 1)
    return out


def citadel(ruined=False) -> Canvas:
    c = Canvas(seed=5 if not ruined else 6)
    courtyard(c, ruined)
    curtain_wall(c, ruined)
    roots(c, ruined)
    keep(c, ruined)
    # the west gatehouses, north first so the southern ones overlap them
    for gx, gy in GATES:
        if ruined:
            x, y = C(gx + 0.5, gy + 0.5)
            c.box(x - 8, x + 46, y - 12, y + 22, 16, OBS_L, OBS, gx * 31 + gy, course=4)
            rubble(c, x + 18, y + 14, 30, 8, gy)
        else:
            c.gatehouse(gx, gy, gx * 31 + gy)
    corner_towers(c, ruined)
    south_wall(c, ruined)
    c.ink()
    bounce_light(c)
    return c


def crack_layer(c: Canvas):
    """Fire cracks that open across the standing citadel as it is broken: the game fades them in by health."""
    rng = random.Random(77)
    ys, xs = np.nonzero(c.a)
    for k in range(70):
        i = rng.randrange(len(xs))
        x, y = float(xs[i]), float(ys[i])
        for _ in range(rng.randint(8, 26)):
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 0 <= yi < H and c.a[yi, xi]:
                c.glow_px(xi, yi, FIRE[3] if rng.random() < 0.3 else FIRE[2], 0.95, layer=c.cracks)
            x += rng.choice((-1, 0, 1))
            y += rng.choice((0, 1, 1))


def flicker(layer: np.ndarray, frame: int) -> np.ndarray:
    """A frame of the fire's flicker: each lit pixel brightens or dims a little, in patches."""
    out = layer.copy()
    yy, xx = np.mgrid[0:H, 0:W]
    phase = np.sin((xx // 5) * 1.7 + (yy // 5) * 2.3 + frame * 1.9) * 0.5 + 0.5
    out[..., 3] = np.clip(layer[..., 3] * (0.72 + 0.4 * phase), 0, 1)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--preview", default="")
    ap.add_argument("--zoom", type=int, default=2)
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    whole = citadel(False)
    crack_layer(whole)
    img, nrm = whole.images()
    img.save(os.path.join(args.out, "citadel.png"))
    nrm.save(os.path.join(args.out, "citadel_n.png"))
    for f in range(4):
        glow_image(flicker(whole.glow, f)).save(os.path.join(args.out, f"citadel_glow_{f}.png"))
    glow_image(whole.cracks).save(os.path.join(args.out, "citadel_cracks.png"))
    ruin = citadel(True)
    rimg, rnrm = ruin.images()
    rimg.save(os.path.join(args.out, "ruin.png"))
    rnrm.save(os.path.join(args.out, "ruin_n.png"))
    glow_image(ruin.glow).save(os.path.join(args.out, "ruin_glow.png"))
    ax, ay = C(ANCHOR_CELL[0] + 0.5, ANCHOR_CELL[1] + 0.5)
    lights = [{"kind": k, "at": [round(x, 1), round(y, 1)]} for k, x, y in whole.lights if k != "window"]
    meta = {"size": [W, H], "anchor": [ax, ay], "cells": [X0, Y0, X1, Y1], "frames": 4,
            "gates": [list(C(gx + 0.5, gy + 0.5)) for gx, gy in GATES], "lights": lights}
    with open(os.path.join(args.out, "citadel.json"), "w") as fh:
        json.dump(meta, fh, indent=1)
    if args.preview:
        preview(args.out, args.preview, args.zoom)
    print("Wrote the citadel to", args.out)


def preview(folder, path, zoom):
    """The citadel standing (with its fire) and fallen, side by side on the void ground, for review."""
    bg = (22, 18, 28, 255)
    sheet = Image.new("RGBA", (W * 2 + 24, H), bg)
    for i, (body, glow) in enumerate([("citadel.png", "citadel_glow_0.png"), ("ruin.png", "ruin_glow.png")]):
        im = Image.open(os.path.join(folder, body)).convert("RGBA")
        lit = Image.new("RGBA", im.size, bg)
        lit.alpha_composite(im)
        g = np.asarray(Image.open(os.path.join(folder, glow)).convert("RGBA")).astype(np.float32)
        base = np.asarray(lit).astype(np.float32)
        # darken the stone like night, then add the glow on top
        base[..., :3] *= 0.8
        a = g[..., 3:4] / 255
        base[..., :3] = np.clip(base[..., :3] * (1 - a * 0.4) + g[..., :3] * a, 0, 255)
        sheet.alpha_composite(Image.fromarray(base.astype(np.uint8), "RGBA"), (i * (W + 24), 0))
    sheet = sheet.resize((sheet.width * zoom, sheet.height * zoom), Image.NEAREST)
    sheet.save(path)


if __name__ == "__main__":
    main()
