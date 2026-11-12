#!/usr/bin/env python3
"""Tower upgrade looks and animation sheets: python3 tools/art/pix2d/tower_anim.py [tower ids] [--preview DIR]

Every tower gets one sheet with five rows, one per look, and fourteen frames per row:

    rows:    l1, l2, l3 (the three levels), a0, a1 (its first and second ascendancy)
    columns: 8 idle frames, then 6 attack frames

A level is a minor upgrade and adds pieces to the same building: level 2 a bronze collar and two ward lanterns, level 3
a gold collar, a second one, war banners, iron-poled lanterns and motes circling the crown. An ascendancy is a major
upgrade and changes the whole building: it is raised on a dais and remade in one of two ways.

    a0 "Exalted": the stone turns pale and warm, gold trims it, two crystal pylons flank it and a sun halo turns
        behind its crown.
    a1 "Dread":   the stone turns black and splits with veins of its element, iron spikes and chains hang off it,
        spiked braziers burn either side and a crown of black thorns stands behind its head.

The idle frames redraw each tower with its fire, orbs, arcs, rain and leaves moving (the helpers in towers*.py are
swapped for moving ones while a frame is drawn), bob the pieces that float, and run a shimmer up every glowing pixel.
The attack frames gather (dim, pieces drop), release (white-hot, the element pieces swell and flare one pixel out,
floating pieces kick up) and settle.

Writes assets/art/game/towers/anim/<id>.png, <id>_n.png, <id>_glow.png and the tower's entry in
assets/art/game/towers/anim/anim.json (kept apart from art.json so other art work never collides with it). Then run `godot --headless --import`. New towers added to towers*.py are picked up with no extra work.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
from collections import deque

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))

from kit import INK, Sprite, hexc, ramp  # noqa: E402
from creatures import IRON, GOLD, BONE  # noqa: E402
import towers  # noqa: E402
import towers_duals  # noqa: E402
import towers_triples  # noqa: E402
from towers import (ELEMENT_GLOW, ELEMENT_LIGHT, MARBLE, OBSID, COPPER, CLOTH_R, CLOTH_B, CLOTH_V, block,  # noqa: E402
                    glow_image)

STAGES = ["l1", "l2", "l3", "a0", "a1"]
IDLE = 8
ATTACK = 6
IDLE_FPS = 8
ATTACK_FPS = 18
PAD_X = 16
PAD_TOP = 14
PAD_BOT = 3
DAIS = 3
OUT = os.path.join("assets", "art", "game")

# The attack, frame by frame: how big the element pieces are drawn, how hot the glow is, how floating pieces move.
ATTACK_SIZE = [0.88, 1.0, 1.4, 1.22, 1.08, 1.0]
ATTACK_HEAT = [0.78, 1.05, 1.7, 1.35, 1.12, 1.0]
ATTACK_LIFT = [1, 1, -2, -1, 0, 0]

BRONZE = COPPER
CLOTH = {"fire": CLOTH_R, "storm": CLOTH_B, "void": CLOTH_V, "water": ramp("1f6a7a", spread=0.5),
         "nature": ramp("3a6a26", spread=0.5), "earth": ramp("9a6a22", spread=0.5)}
CLOTH_BLACK = ramp("2a2024", spread=0.45)
IVORY = np.array([236, 222, 190], np.float32)
SOOT = np.array([34, 26, 32], np.float32)
DREAD_IRON = ramp("3e3a40", spread=0.5)
PALE = ramp("a8a294", spread=0.45, shift=0.02)
CLOTH_BLOOD = ramp("6a161c", spread=0.5)


# ------------------------------------------------------------------------------------------------ moving helpers
class Anim:
    """What frame is being drawn. phase runs 0..1 over the idle loop; attack is -1 or the attack frame."""
    phase = 0.0
    attack = -1

    @classmethod
    def frame_seed(cls):
        return (100 + cls.attack) * 17 if cls.attack >= 0 else int(round(cls.phase * IDLE)) * 13

    @classmethod
    def size(cls):
        return ATTACK_SIZE[cls.attack] if cls.attack >= 0 else 1.0

    @classmethod
    def wave(cls, cycles=1.0, offset=0.0):
        return math.sin((cls.phase * cycles + offset) * math.tau)


_orig = {
    "flame": towers.flame, "orb": towers.orb, "arcs": towers_duals.arcs, "leaf_crown": towers_duals.leaf_crown,
    "bolt_down": towers_triples.bolt_down, "rain": towers_triples.rain,
}


def _flame(s, cx, base, w, h, seed=0, tones=towers.FIRE):
    k = Anim.size()
    breathe = 1.0 + 0.1 * Anim.wave(2)
    return _orig["flame"](s, cx, base, w * (0.85 + 0.15 * k), h * k * breathe, seed=seed + Anim.frame_seed(), tones=tones)


def _orb(s, cx, cy, r, tones, rim=None):
    k = Anim.size()
    return _orig["orb"](s, cx, cy, r * k * (1.0 + 0.07 * Anim.wave()), tones, rim)


def _arcs(s, pts, col, glow=True):
    rng = np.random.default_rng(Anim.frame_seed() + 5)
    moved = [pts[0]] + [(x + int(rng.integers(-1, 2)), y + int(rng.integers(-1, 2))) for x, y in pts[1:-1]] + [pts[-1]]
    return _orig["arcs"](s, moved, col, glow)


def _leaf_crown(s, cx, cy, w, h, tones, tones_d, seed=0, glow=False):
    return _orig["leaf_crown"](s, cx + round(Anim.wave() * 0.8), cy, w, h, tones, tones_d, seed=seed, glow=glow)


def _bolt_down(s, x, y0, y1, seed=0, col=None):
    return _orig["bolt_down"](s, x, y0, y1, seed=seed + Anim.frame_seed(), col=col)


def _rain(s, cx, top, w, h, seed=0, col=None):
    return _orig["rain"](s, cx, top, w, h, seed=seed + Anim.frame_seed(), col=col)


_moving = {"flame": _flame, "orb": _orb, "arcs": _arcs, "leaf_crown": _leaf_crown, "bolt_down": _bolt_down,
           "rain": _rain}


def draw_tower(name):
    """The tower drawn at the current Anim frame, with the moving helpers swapped in."""
    mods = (towers, towers_duals, towers_triples)
    saved = []
    for m in mods:
        for key, fn in _moving.items():
            if hasattr(m, key):
                saved.append((m, key, getattr(m, key)))
                setattr(m, key, fn)
    try:
        return towers.TOWERS[name]()
    finally:
        for m, key, fn in saved:
            setattr(m, key, fn)


# ------------------------------------------------------------------------------------------------ pixels
def components(a):
    """Label the 8-connected islands of a mask. Returns (labels, sizes)."""
    lab = np.zeros(a.shape, np.int32)
    sizes = [0]
    h, w = a.shape
    n = 0
    for y0, x0 in zip(*np.nonzero(a)):
        if lab[y0, x0]:
            continue
        n += 1
        q = deque([(y0, x0)])
        lab[y0, x0] = n
        count = 0
        while q:
            y, x = q.popleft()
            count += 1
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    yy, xx = y + dy, x + dx
                    if 0 <= yy < h and 0 <= xx < w and a[yy, xx] and not lab[yy, xx]:
                        lab[yy, xx] = n
                        q.append((yy, xx))
        sizes.append(count)
    return lab, sizes


def floaters(s):
    """Pieces that hang in the air: islands that do not reach the ground rows and are not the main building."""
    lab, sizes = components(s.a)
    total = sum(sizes)
    out = np.zeros_like(s.a)
    ground = s.h - 12
    for k in range(1, len(sizes)):
        m = lab == k
        if not m[ground:].any() and sizes[k] < total * 0.4:
            out |= m
    return out


def shift_mask(s, mask, dy):
    """Move the pixels under mask dy rows (all their layers), leaving the rest."""
    if dy == 0 or not mask.any():
        return
    rgb, nrm, glow = s.rgb[mask].copy(), s.nrm[mask].copy(), s.glow[mask].copy()
    ys, xs = np.nonzero(mask)
    s.a[mask] = False
    s.glow[mask] = False
    ny = np.clip(ys + dy, 0, s.h - 1)
    s.a[ny, xs] = True
    s.rgb[ny, xs] = rgb
    s.nrm[ny, xs] = nrm
    s.glow[ny, xs] = glow


def paste(dst, src, ox, oy):
    m = src.a
    ys, xs = np.nonzero(m)
    ty, tx = ys + oy, xs + ox
    ok = (ty >= 0) & (ty < dst.h) & (tx >= 0) & (tx < dst.w)
    ys, xs, ty, tx = ys[ok], xs[ok], ty[ok], tx[ok]
    dst.rgb[ty, tx] = src.rgb[ys, xs]
    dst.nrm[ty, tx] = src.nrm[ys, xs]
    dst.glow[ty, tx] = src.glow[ys, xs]
    dst.a[ty, tx] = True


def blend(rgb, col, t):
    return np.clip(rgb.astype(np.float32) * (1 - t) + np.asarray(col, np.float32) * t, 0, 255).astype(np.uint8)


# ------------------------------------------------------------------------------------------------ the tower's shape
class Shape:
    """Where things are on a tower, measured once from its level-1 rest frame (in that sprite's own pixels)."""

    def __init__(self, s, meta):
        self.w, self.h = s.w, s.h
        self.ax, self.ay = meta["anchor"]
        self.mx, self.my = self.ax + meta["muzzle"][0], self.ay + meta["muzzle"][1]
        float_mask = floaters(s)
        body = s.a & ~float_mask
        rows = np.nonzero(body.any(1))[0]
        self.top = int(rows.min())
        self.spans = {}
        for y in rows:
            xs = np.nonzero(body[y])[0]
            self.spans[int(y)] = (int(xs.min()), int(xs.max()))
        foot = [self.spans[y] for y in range(self.ay - 3, self.ay + 1) if y in self.spans]
        self.foot_l = min(a for a, _ in foot) if foot else self.ax - 12
        self.foot_r = max(b for _, b in foot) if foot else self.ax + 12
        self.body_h = self.ay - self.top
        self.glow = s.glow & s.a
        self.solid = body & ~self.glow
        self.collars = self._collars()
        # the side edges a banner or spike can hang from, a third and two thirds of the way up
        self.left_edge = min(a for a, _ in self.spans.values())
        self.right_edge = max(b for _, b in self.spans.values())

    def _collars(self):
        """Rows for a metal collar: narrow, mostly solid stone or bark, between a quarter and two thirds up."""
        best = []
        for lo, hi in ((0.28, 0.48), (0.5, 0.7)):
            pick, score = None, None
            for y in range(int(self.ay - self.body_h * hi), int(self.ay - self.body_h * lo)):
                if y not in self.spans or y + 1 not in self.spans:
                    continue
                a, b = self.spans[y]
                width = b - a + 1
                if width < 4:
                    continue
                solid = self.solid[y, a:b + 1].mean() * self.solid[y + 1, a:b + 1].mean()
                if solid < 0.75:
                    continue
                sc = width - solid * 6
                if score is None or sc < score:
                    pick, score = y, sc
            if pick is not None:
                best.append(pick)
        return best


# ------------------------------------------------------------------------------------------------ decorations
def collar(front, shape, y, tones, ox, oy, rune=None):
    """A metal collar round the building at row y: lit top row, dark bottom row, rivets, one pixel proud each side."""
    a, b = shape.spans[y]
    a, b = a + ox - 1, b + ox + 1
    yy = y + oy
    front.fill(front.rect(a, yy, b + 1, yy + 1), tones[3])
    front.fill(front.rect(a, yy + 1, b + 1, yy + 2), tones[1])
    for i, x in enumerate(range(a + 1, b + 1, 3)):
        if rune is not None and i % 2:
            front.px(x, yy, ELEMENT_GLOW[rune][3], glow=True)
            front.px(x, yy + 1, ELEMENT_GLOW[rune][2], glow=True)
        else:
            front.px(x, yy, tones[4])
    front.px(b, yy, tones[2])
    front.px(b, yy + 1, tones[0])
    front.nrm[yy:yy + 2, a:b + 1] = (0.0, -0.3, 0.95)


def lantern(layer, x, ground, element, tall=False, flare=1.0):
    """A ward lantern by the tower's foot: a stone post (level 2) or an iron pole with a pennant (level 3)."""
    tones = ELEMENT_GLOW[element]
    if tall:
        layer.part(layer.rect(x, ground - 13, x + 2, ground), IRON, flat=True)
        layer.fill(layer.rect(x - 1, ground - 1, x + 3, ground + 1), IRON[1])
        head = ground - 16
        layer.fill(layer.rect(x - 1, head, x + 3, head + 3), IRON[2])
        layer.fill(layer.rect(x, head - 1, x + 2, head + 2), tones[3] if flare < 1.3 else tones[4], glow=True)
        sway = round(Anim.wave(1, 0.25 if x % 2 else 0.0))
        cloth = CLOTH.get(element, CLOTH_R)
        pts = [(x + 2, ground - 12), (x + 7 + sway, ground - 11), (x + 6 + sway, ground - 9), (x + 2, ground - 8)]
        if x > layer.w / 2:
            pts = [(x, ground - 12), (x - 5 + sway, ground - 11), (x - 4 + sway, ground - 9), (x, ground - 8)]
        layer.part(layer.poly(pts), cloth, flat=True)
    else:
        block(layer, x - 1, ground - 6, x + 3, ground, towers.STONE_D, depth=1, seed=x)
        layer.fill(layer.rect(x, ground - 9, x + 2, ground - 6), tones[3] if flare < 1.3 else tones[4], glow=True)
        layer.px(x, ground - 10, tones[2], glow=True)


def banner(front, shape, y, side, element, ox, oy, dread=False):
    """A war banner hung from the collar at row y, on one side of the building, swaying a little."""
    a, b = shape.spans[y]
    x = (a + ox + 1) if side < 0 else (b + ox - 3)
    yy = y + oy + 2
    sway = round(Anim.wave(1, 0.3 if side > 0 else 0.0) * 1.0)
    cloth = CLOTH_BLOOD if dread else CLOTH.get(element, CLOTH_R)
    length = 11
    pts = [(x, yy), (x + 4, yy), (x + 4 + sway, yy + length), (x + 2 + sway, yy + length - 2), (x + sway, yy + length)]
    front.part(front.poly(pts), cloth, flat=True)
    tones = ELEMENT_GLOW[element]
    front.px(x + 2, yy + 3, tones[3], glow=True)
    front.px(x + 2, yy + 4, tones[2], glow=True)
    trim = GOLD if not dread else IRON
    front.line(x, yy, x + 4, yy, trim[3])
    if dread:  # torn: a couple of holes
        front.px(x + 1 + sway, yy + 7, (0, 0, 0))
        front.a[yy + 7, x + 1 + sway] = False


def motes(back, front, cx, cy, n, element, radius=10, glow_big=False):
    """Little lights circling the crown; the ones behind it go on the back layer."""
    tones = ELEMENT_GLOW[element]
    for i in range(n):
        ang = (Anim.phase + i / n) * math.tau
        x = cx + math.cos(ang) * radius
        y = cy + math.sin(ang) * radius * 0.42 - 2
        layer = front if math.sin(ang) > 0 else back
        layer.px(round(x), round(y), tones[4], glow=True)
        layer.px(round(x) + 1, round(y), tones[3], glow=True)
        if glow_big:
            layer.px(round(x), round(y) + 1, tones[2], glow=True)


def dais(back, shape, ox, oy, tones, edge, runes, element, spikes=False):
    """The raised step an ascended tower stands on."""
    cx = (shape.foot_l + shape.foot_r) / 2 + ox
    w = (shape.foot_r - shape.foot_l) + 14
    ground = shape.ay + oy + DAIS
    x0, x1 = round(cx - w / 2), round(cx + w / 2)
    block(back, x0, ground - DAIS - 3, x1, ground, tones, depth=3, chips=3, seed=w)
    back.line(x0, ground - DAIS - 3, x1, ground - DAIS - 3, edge[3])
    gl = ELEMENT_GLOW[element]
    if runes:
        for x in range(x0 + 3, x1 - 1, 5):
            back.px(x, ground - 2, gl[3], glow=True)
            back.px(x + 1, ground - 2, gl[2], glow=True)
    if spikes:
        for x in range(x0 + 1, x1 + 1, 4):
            back.fill(back.poly([(x, ground - DAIS - 3), (x + 2, ground - DAIS - 3), (x + 1, ground - DAIS - 7)]), IRON[2])
            back.px(x + 1, ground - DAIS - 6, IRON[4])
        for x in (x0 + 4, x1 - 6):  # skulls set in the front of the step
            skull(back, x, ground - 3)
    return x0, x1, ground


def skull(layer, x, y):
    layer.fill(layer.rect(x, y - 2, x + 4, y + 1), BONE[3])
    layer.fill(layer.rect(x + 1, y + 1, x + 3, y + 2), BONE[2])
    layer.px(x + 1, y - 1, (20, 10, 12))
    layer.px(x + 3, y - 1, (20, 10, 12))
    layer.px(x, y - 2, BONE[4])


def pylon(back, x, ground, height, element, flare):
    """A squat pale obelisk on a stepped foot, banded in gold, a crystal of the element floating over it."""
    block(back, x - 3, ground - 3, x + 4, ground, MARBLE, depth=1, seed=x + 1)
    block(back, x - 2, ground - height, x + 3, ground - 3, PALE, depth=1, chips=2, seed=x)
    for y in (ground - height + 3, ground - 7):
        back.fill(back.rect(x - 2, y, x + 3, y + 1), GOLD[3])
        back.px(x + 2, y, GOLD[1])
    back.fill(back.poly([(x - 2, ground - height), (x + 3, ground - height), (x + 0.5, ground - height - 4)]), GOLD[3])
    back.px(x, ground - height - 2, GOLD[4])
    tones = ELEMENT_GLOW[element]
    bob = round(Anim.wave(1, 0.5 if x % 2 else 0.0))
    cy = ground - height - 9 + bob
    k = 1 if flare > 1.3 else 0
    back.fill(back.poly([(x + 0.5, cy - 4 - k), (x + 3 + k, cy), (x + 0.5, cy + 4 + k), (x - 2 - k, cy)]), tones[2], glow=True)
    back.fill(back.poly([(x + 0.5, cy - 4 - k), (x + 3 + k, cy), (x + 0.5, cy)]), tones[3], glow=True)
    back.px(x, cy - 2, tones[4], glow=True)


def brazier(back, x, ground, height, element):
    """A black iron brazier on a spiked pole, burning the element."""
    back.part(back.rect(x, ground - height, x + 2, ground), DREAD_IRON, flat=True)
    for dx in (-2, 3):
        back.line(x + (0 if dx < 0 else 1), ground - height + 4, x + dx, ground - height + 1, IRON[2])
    bowl = ground - height
    back.part(back.poly([(x - 3, bowl - 1), (x + 5, bowl - 1), (x + 3, bowl + 3), (x - 1, bowl + 3)]), DREAD_IRON)
    for sx in (x - 3, x + 1, x + 5):
        back.px(sx, bowl - 2, IRON[3])
    _flame(back, x + 1, bowl - 1, 7, 11, seed=x, tones=ELEMENT_GLOW[element])


def halo(back, cx, cy, r, element):
    """A gold sun ring behind the crown, rays round it, the element's lights running round the ring."""
    ring = back.ellipse(cx, cy, r, r) & ~back.ellipse(cx, cy, r - 1.6, r - 1.6)
    back.fill(ring, GOLD[3])
    back.fill(ring & (back.ys > cy + r * 0.3), GOLD[1])
    back.fill(ring & (back.ys < cy - r * 0.5), GOLD[4])
    tones = ELEMENT_GLOW[element]
    for i in range(8):
        ang = (i / 8 + Anim.phase / 8) * math.tau
        x0, y0 = cx + math.cos(ang) * (r + 1), cy + math.sin(ang) * (r + 1)
        x1, y1 = cx + math.cos(ang) * (r + 3 + (i % 2) * 2), cy + math.sin(ang) * (r + 3 + (i % 2) * 2)
        back.line(round(x0), round(y0), round(x1), round(y1), GOLD[2] if i % 2 else GOLD[3])
    for i in range(3):
        ang = (Anim.phase + i / 3) * math.tau
        back.px(round(cx + math.cos(ang) * (r - 0.8)), round(cy + math.sin(ang) * (r - 0.8)), tones[4], glow=True)


def thorn_crown(back, cx, cy, r, element, flare):
    """Black thorns fanned out behind the crown, their tips lit by the element."""
    tones = ELEMENT_GLOW[element]
    for i, deg in enumerate((-150, -120, -90, -60, -30, -165, -15)):
        ang = math.radians(deg)
        length = r + (5 if i % 2 == 0 else 2) + (1 if flare > 1.3 else 0)
        x0, y0 = cx + math.cos(ang) * (r * 0.4), cy + math.sin(ang) * (r * 0.4)
        x1, y1 = cx + math.cos(ang) * length, cy + math.sin(ang) * length
        nx, ny = -math.sin(ang) * 1.3, math.cos(ang) * 1.3
        back.fill(back.poly([(x0 + nx, y0 + ny), (x0 - nx, y0 - ny), (x1, y1)]), DREAD_IRON[1])
        back.px(round(x1), round(y1), tones[3], glow=True)


def spikes(front, shape, ox, oy, count=3):
    """Iron spikes driven through the building's sides, pointing out and up, with a chain hung between."""
    ys = sorted(shape.spans)
    lo, hi = shape.ay - shape.body_h * 0.75, shape.ay - shape.body_h * 0.2
    picks = [round(lo + (hi - lo) * (k + 0.5) / count) for k in range(count)]
    ends = {-1: [], 1: []}
    for y in picks:
        if y not in shape.spans:
            continue
        a, b = shape.spans[y]
        for side, x in ((-1, a + ox), (1, b + ox)):
            yy = y + oy
            tip = (x + side * 5, yy - 3)
            front.fill(front.poly([(x, yy - 1), (x, yy + 1), tip]), IRON[2])
            front.line(x, yy - 1, tip[0], tip[1], IRON[4])
            front.px(tip[0], tip[1], BONE[4])
            ends[side].append((x + side * 2, yy))
    for side, pts in ends.items():
        for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):   # a chain sagging between two spikes
            n = max(2, int(abs(y1 - y0)))
            for i in range(n + 1):
                t = i / n
                sag = math.sin(t * math.pi) * 2 * side
                front.px(round(x0 + (x1 - x0) * t + sag), round(y0 + (y1 - y0) * t), IRON[3] if i % 2 else IRON[1])
    del ys


def veins(s, mask, element, seed):
    """Cracks of the element's light splitting the blackened stone (glowing, so they shine at night)."""
    tones = ELEMENT_GLOW[element]
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(mask)
    if len(ys) == 0:
        return
    n = max(4, len(ys) // 140)
    for _ in range(n):
        i = int(rng.integers(len(ys)))
        y, x = int(ys[i]), int(xs[i])
        for step in range(int(rng.integers(4, 9))):
            if not (0 <= y < s.h and 0 <= x < s.w) or not mask[y, x]:
                break
            s.rgb[y, x] = tones[3] if step % 3 else tones[4]
            s.glow[y, x] = True
            y += int(rng.choice([-1, -1, 0, 1]))
            x += int(rng.choice([-1, 0, 1]))


# ------------------------------------------------------------------------------------------------ one frame
def elements_of(name):
    path = os.path.join("data", "towers", name + ".tres")
    try:
        text = open(path).read()
    except OSError:
        return ["fire"]
    import re
    m = re.search(r'^elements = Array\[StringName\]\(\[(.*?)\]\)', text, re.M)
    found = re.findall(r'&"(\w+)"', m.group(1)) if m else []
    return [e for e in found if e in ELEMENT_GLOW] or ["fire"]


def main_element(meta, elems):
    color = meta.get("light", {}).get("color", "")
    for e in elems:
        if ELEMENT_LIGHT.get(e) == color:
            return e
    return elems[0]


def frame(name, stage, shape, elems, main, cell_w, cell_h, idle_k=None, attack_k=None):
    Anim.phase = (idle_k or 0) / IDLE
    Anim.attack = -1 if attack_k is None else attack_k
    heat = ATTACK_HEAT[attack_k] if attack_k is not None else 1.0
    s, _ = draw_tower(name)
    ascended = stage in ("a0", "a1")
    ox, oy = PAD_X, PAD_TOP - (DAIS if ascended else 0)

    # floating pieces bob on the idle, drop and kick on the attack
    fl = floaters(s)
    dy = round(Anim.wave()) if attack_k is None else ATTACK_LIFT[attack_k]
    shift_mask(s, fl, dy)

    # an ascended tower's stone is remade
    solid = s.a & ~s.glow & ~(s.rgb == np.array(INK, np.uint8)).all(-1)
    if stage == "a0":
        # pale stone goes ivory; coloured parts (leaves, cloth, bark) keep most of their colour
        rgb = s.rgb.astype(np.float32)
        sat = (rgb.max(-1) - rgb.min(-1)) / np.maximum(rgb.max(-1), 1)
        k = np.clip(0.22 - sat * 0.5, 0.03, 0.22)[..., None]
        s.rgb[solid] = np.clip(rgb * (1 - k) + IVORY * k, 0, 255).astype(np.uint8)[solid]
        lum = s.rgb.astype(np.float32).mean(-1)
        hi = solid & (lum > np.percentile(lum[solid], 88) if solid.any() else solid)
        s.rgb[hi] = blend(s.rgb[hi], GOLD[3], 0.45)
    elif stage == "a1":
        s.rgb[solid] = blend(s.rgb[solid], SOOT, 0.55)
        veins(s, solid, main, seed=len(name) * 7 + 3)

    back = Sprite(cell_w, cell_h)
    front = Sprite(cell_w, cell_h)
    ground = shape.ay + oy
    mx, my = shape.mx + ox, shape.my + oy
    left_x, right_x = shape.foot_l + ox - 4, shape.foot_r + ox + 3
    side_l, side_r = elems[0], elems[-1]

    if stage == "l2":
        for y in shape.collars[:1]:
            collar(front, shape, y, BRONZE, ox, oy, rune=main)
        lantern(front, left_x, ground, side_l, flare=heat)
        lantern(front, right_x, ground, side_r, flare=heat)
    elif stage == "l3":
        for y in shape.collars:
            collar(front, shape, y, GOLD, ox, oy, rune=main)
        if shape.collars:
            banner(front, shape, shape.collars[0], -1, side_l, ox, oy)
            banner(front, shape, shape.collars[0], 1, side_r, ox, oy)
        lantern(front, left_x - 1, ground, side_l, tall=True, flare=heat)
        lantern(front, right_x + 1, ground, side_r, tall=True, flare=heat)
    elif stage == "a0":
        dais(back, shape, ox, oy, MARBLE, GOLD, True, main)
        h = max(14, min(26, int(shape.body_h * 0.32)))
        pylon(back, shape.left_edge + ox - 3, ground + DAIS, h, side_l, heat)
        pylon(back, shape.right_edge + ox + 3, ground + DAIS, h, side_r, heat)
        halo(back, mx, my, 9 if shape.body_h < 70 else 11, main)
        for y in shape.collars:
            collar(front, shape, y, GOLD, ox, oy)
        if shape.collars:
            banner(front, shape, shape.collars[0], -1, side_l, ox, oy)
            banner(front, shape, shape.collars[0], 1, side_r, ox, oy)
    elif stage == "a1":
        dais(back, shape, ox, oy, OBSID, IRON, False, main, spikes=True)
        h = max(14, int(shape.body_h * 0.35))
        brazier(back, shape.left_edge + ox - 3, ground + DAIS, h, side_l)
        brazier(back, shape.right_edge + ox + 2, ground + DAIS, h, side_r)
        thorn_crown(back, mx, my, 8 if shape.body_h < 70 else 10, main, heat)
        for y in shape.collars[:1]:
            collar(front, shape, y, DREAD_IRON, ox, oy)
            banner(front, shape, y, -1, side_l, ox, oy, dread=True)
            banner(front, shape, y, 1, side_r, ox, oy, dread=True)
        spikes(front, shape, ox, oy)

    back.ink()
    front.ink()
    if stage == "l3":
        motes(back, front, mx, my, 3, main)
    elif stage == "a0":
        motes(back, front, mx, my, 4, main, radius=12, glow_big=True)
    out = Sprite(cell_w, cell_h)
    paste(out, back, 0, 0)
    paste(out, s, ox, oy)
    paste(out, front, 0, 0)

    # glow: a shimmer running up every glowing pixel, and the attack's heat
    g = out.glow & out.a
    if g.any():
        period = 10
        band = ((out.ys + int(Anim.phase * period * 2)) % period) < 2
        if attack_k is None:
            out.rgb[g & band] = blend(out.rgb[g & band], (255, 255, 255), 0.3)
        elif heat > 1.0:
            out.rgb[g] = blend(out.rgb[g], (255, 255, 255), min(0.75, (heat - 1.0) * 0.8))
        else:
            out.rgb[g] = blend(out.rgb[g], (0, 0, 0), (1.0 - heat) * 0.8)
        if attack_k is not None and heat >= 1.6:
            # the flare: one pixel of light round everything that glows, out into the air
            ring = np.zeros_like(g)
            ring[1:] |= g[:-1]
            ring[:-1] |= g[1:]
            ring[:, 1:] |= g[:, :-1]
            ring[:, :-1] |= g[:, 1:]
            ring &= ~out.a
            out.rgb[ring] = ELEMENT_GLOW[main][3]
            out.a |= ring
            out.glow |= ring
    return out


def build(name, preview=None):
    Anim.phase, Anim.attack = 0.0, -1
    s, meta = draw_tower(name)
    shape = Shape(s, meta)
    elems = elements_of(name)
    main = main_element(meta, elems)
    cell_w, cell_h = s.w + PAD_X * 2, s.h + PAD_TOP + PAD_BOT
    cols = IDLE + ATTACK
    diffuse = Image.new("RGBA", (cell_w * cols, cell_h * len(STAGES)))
    normal = Image.new("RGBA", diffuse.size)
    glow = Image.new("RGBA", diffuse.size)
    for r, stage in enumerate(STAGES):
        for c in range(cols):
            f = frame(name, stage, shape, elems, main, cell_w, cell_h,
                      idle_k=c if c < IDLE else None, attack_k=c - IDLE if c >= IDLE else None)
            at = (c * cell_w, r * cell_h)
            diffuse.paste(f.image(), at)
            normal.paste(f.normal_image(), at)
            glow.paste(glow_image(f), at)
    anim = {
        "sheet": "towers/anim/" + name, "cell": [cell_w, cell_h],
        "anchor": [meta["anchor"][0] + PAD_X, meta["anchor"][1] + PAD_TOP],
        "stages": STAGES, "lift": [0, 0, 0, DAIS, DAIS],
        "idle": IDLE, "idle_fps": IDLE_FPS, "attack": ATTACK, "attack_fps": ATTACK_FPS, "attack_peak": 2,
    }
    return diffuse, normal, glow, anim


def preview_sheet(name, diffuse, cell, path, zoom=3, bg=(58, 76, 52)):
    """A labelled review picture: every look in a row, every frame across."""
    im = Image.new("RGBA", diffuse.size, bg + (255,))
    im.alpha_composite(diffuse)
    im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for r, st in enumerate(STAGES):
        d.text((4, r * cell[1] * zoom + 4), st, fill=(240, 230, 200))
    d.text((IDLE * cell[0] * zoom + 4, 4), "attack", fill=(255, 200, 160))
    im.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--preview", help="also write a labelled review sheet per tower into this folder")
    ap.add_argument("--dry", action="store_true", help="previews only, leave the game's files alone")
    args = ap.parse_args()
    names = args.names or list(towers.TOWERS)
    folder = os.path.join(OUT, "towers", "anim")
    os.makedirs(folder, exist_ok=True)
    index_path = os.path.join(folder, "anim.json")
    index = json.load(open(index_path)) if os.path.exists(index_path) else {}
    for n in names:
        diffuse, normal, glow, anim = build(n)
        if args.preview:
            os.makedirs(args.preview, exist_ok=True)
            preview_sheet(n, diffuse, anim["cell"], os.path.join(args.preview, n + ".png"))
        if args.dry:
            print("previewed", n)
            continue
        diffuse.save(os.path.join(folder, n + ".png"))
        normal.save(os.path.join(folder, n + "_n.png"))
        glow.save(os.path.join(folder, n + "_glow.png"))
        index[n] = anim
        print("tower", n, anim["cell"])
    if not args.dry:
        with open(index_path, "w") as fh:
            json.dump(dict(sorted(index.items())), fh, indent=1)


if __name__ == "__main__":
    main()
