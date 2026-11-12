"""The fifteen dual-element towers in the hand-drawn style. Imported by towers.py, which registers them in TOWERS.

Each one is its own building, not a stack of parts: it should read as both elements at a glance (a burning tree for
Wildfire, a copper coil with a plasma orb for Plasma Coil) and stand a little taller and broader than a base tower.
"""
from __future__ import annotations

import math

import numpy as np

from kit import INK, hexc, ramp, Sprite
from creatures import STONE, STONE_D, IRON, GOLD, MOSS, BONE
from towers import (AMBER, AQUA, BARK, BARK_D, BASALT, BOLT, COPPER, FIRE, LEAF, LEAF_D, OBSID, SAND, SAP, SLATE,
                    VOIDC, BONE_THORN, block, course_wall, flame, orb, plinth, meta_for, tower)

MUD = ramp("4a3826", spread=0.45)
TAR = [hexc(c) for c in ("120e0c", "1e1814", "2c241c", "3c3226", "524636")]
BOGW = [hexc(c) for c in ("16301e", "1f4a2a", "2e6a38", "4a9a4a", "8ad06a")]
BLIGHT = ramp("5a3a7a", spread=0.5)
BLIGHT_L = ramp("7a4aa0", spread=0.55)
EMBER_LEAF = [hexc(c) for c in ("6a1e10", "a8401a", "e07a2a", "ffb040", "ffe08a")]
SOUL = [hexc(c) for c in ("1a3a2a", "2aa070", "6af0b0", "c0ffe0", "f4fff8")]
BRASS = ramp("b08a3a", spread=0.55)
CLOUD = [hexc(c) for c in ("3a4250", "56607a", "7a86a0", "a8b4c8", "d8e0ec")]
STEAM = [hexc(c) for c in ("8a96a4", "b4c0cc", "dce4ec", "f4f8fc")]
ROOTS = ramp("5a4632", spread=0.45)


def arcs(s, pts, col, glow=True):
    for (x0, y0), (x1, y1) in zip(pts[:-1], pts[1:]):
        s.line(x0, y0, x1, y1, col, glow=glow)


def pool_top(s, cx, cy, rx, ry, rim, water, shine=None):
    """A pool seen from above: a stone rim, the water inside, two glints."""
    s.fill(s.ellipse(cx, cy, rx, ry), rim[3])
    s.fill(s.ellipse(cx, cy + 0.5, rx - 2, ry - 1.4), water[1])
    s.fill(s.ellipse(cx - 1, cy, rx - 4, ry - 2.2), water[2])
    if shine is not None:
        s.pxs([(cx - rx * 0.4, cy - 1), (cx - rx * 0.4 + 1, cy - 1), (cx + rx * 0.3, cy + 1)], shine, glow=True)


def leaf_crown(s, cx, cy, w, h, tones, tones_d, seed=0, glow=False):
    """A domed crown of leaf lumps around (cx, cy): a darker back row, a lit front row, one lump on top."""
    rng = np.random.default_rng(seed)
    r = w * 0.24
    back = [(cx - w * 0.3, cy - h * 0.25), (cx + w * 0.3, cy - h * 0.3), (cx, cy - h * 0.55)]
    front = [(cx - w * 0.33, cy + h * 0.2), (cx + w * 0.32, cy + h * 0.15), (cx - w * 0.05, cy + h * 0.3),
             (cx - w * 0.12, cy - h * 0.15), (cx + w * 0.14, cy - h * 0.35)]
    for (x, y) in back:
        s.part(s.ellipse(x + rng.uniform(-1, 1), y, r * 1.05, r * 0.85), tones_d, bias=-0.1, glow=glow)
    for (x, y) in front:
        s.part(s.ellipse(x + rng.uniform(-1, 1), y, r, r * 0.8), tones, glow=glow)
    ys, xs = np.nonzero(s.a)
    lit = {tuple(tones[3]), tuple(tones[4])}
    for _ in range(60):
        k = int(rng.integers(0, len(xs)))
        x, y = xs[k], ys[k]
        if abs(y - cy) < h and s.a[max(0, y - 2), x] and tuple(int(v) for v in s.rgb[y, x]) in lit:
            s.px(x, y, tones[4], glow=glow)
            s.px(x - 1, y + 1, tones[4], glow=glow)
            s.px(x, y + 1, tones[2], glow=glow)


def trunk(s, cx, bottom, top, w, tones, tones_d, lean=0.0):
    s.part(s.poly([(cx - w, bottom), (cx - w * 0.5 + lean, top), (cx + w * 0.5 + lean, top), (cx + w, bottom)]), tones)
    s.part(s.poly([(cx - w - 5, bottom), (cx - w * 0.4, bottom - 7), (cx - w * 0.2, bottom)]), tones_d)
    s.part(s.poly([(cx + w + 5, bottom), (cx + w * 0.4, bottom - 7), (cx + w * 0.2, bottom)]), tones_d)
    for y in range(int(top) + 3, int(bottom) - 2, 4):
        s.px(cx + (y % 3) - 1 + lean * (bottom - y) / (bottom - top), y, tones[1])


# ------------------------------------------------------------------------------------------------ fire + x
@tower
def hybrid_plasma():
    """Plasma Coil: a stone drum, a brass coil spiralling up a copper mast, a white-hot orb caged in iron."""
    s = Sprite(40, 86)
    cx, bottom = 19, 82
    plinth(s, cx, bottom, 32, 5, BASALT, seed=101)
    course_wall(s, cx, bottom - 5, 22, 20, 14, STONE_D, row_h=7, seed=102)
    top = bottom - 19
    s.part(s.rect(cx - 2, top - 32, cx + 3, top), COPPER, flat=True)
    for k in range(8):
        y = top - 3 - k * 3.6
        w = 7 - k * 0.45
        s.line(cx - w, y + 1, cx + w + 1, y - 1, BRASS[3] if k % 2 else BRASS[2])
        s.px(cx - w, y + 1, BRASS[4])
    oy = top - 40
    for a in (-1, 1):
        s.line(cx + a * 6, oy + 5, cx + a * 2, top - 31, IRON[1])
        s.line(cx + a * 6, oy - 4, cx + a * 6, oy + 5, IRON[2])
    orb(s, cx + 0.5, oy, 5.5, [FIRE[2], FIRE[3], FIRE[4], (255, 255, 240), (255, 255, 255)])
    s.line(cx - 6, oy - 4, cx + 7, oy - 4, IRON[3])
    s.ink()
    arcs(s, [(cx - 6, oy + 2), (cx - 10, oy + 6), (cx - 8, oy + 10), (cx - 12, oy + 15)], BOLT[3])
    arcs(s, [(cx + 6, oy - 2), (cx + 11, oy + 1), (cx + 9, oy + 6), (cx + 13, oy + 9)], FIRE[3])
    return s, meta_for(s, "fire", oy, energy=1.2, rng=120, height=48)


@tower
def hybrid_wildfire():
    """Wildfire: a tree that burns and does not die, ember leaves and glowing cracks in the bark."""
    s = Sprite(44, 84)
    cx, bottom = 21, 80
    trunk(s, cx, bottom, bottom - 40, 6, ramp("3e2a22", spread=0.4), ramp("2e2018", spread=0.4), lean=1)
    for (x0, y0, x1, y1) in ((cx, bottom - 6, cx + 1, bottom - 20), (cx - 2, bottom - 22, cx, bottom - 34), (cx + 2, bottom - 14, cx + 3, bottom - 26)):
        s.line(x0, y0, x1, y1, FIRE[2], glow=True)
    leaf_crown(s, cx + 1, bottom - 50, 36, 18, EMBER_LEAF, [FIRE[0], EMBER_LEAF[0], EMBER_LEAF[1], EMBER_LEAF[2], EMBER_LEAF[3]],
               seed=7)
    for (x, y, w, h) in ((cx - 6, bottom - 58, 8, 10), (cx + 8, bottom - 56, 7, 9), (cx + 1, bottom - 64, 10, 14)):
        flame(s, x, y, w, h, seed=x)
    s.ink((60, 14, 8))
    s.pxs([(cx - 12, bottom - 70), (cx + 14, bottom - 74), (cx + 4, bottom - 84 + 3)], FIRE[3], glow=True)
    return s, meta_for(s, "fire", bottom - 60, energy=1.3, rng=125, height=46)


@tower
def hybrid_magma():
    """Magma Forge: a squat cone of basalt blocks, lava welling over its lip and running down the sides."""
    s = Sprite(44, 74)
    cx, bottom = 21, 70
    rows = [(36, 8), (30, 8), (24, 8), (19, 7)]
    y = bottom
    for k, (w, h) in enumerate(rows):
        n = max(2, w // 8)
        for j in range(n):
            a = cx - w / 2 + w * j / n
            b = cx - w / 2 + w * (j + 1) / n
            block(s, round(a), y - h, round(b), y, BASALT, depth=3 if j == n - 1 else 0, top=False, side=j == n - 1,
                  chips=1, seed=200 + k * 10 + j)
        y -= h
    mouth = y
    s.fill(s.ellipse(cx + 1, mouth, 10, 3), BASALT[4])
    s.fill(s.ellipse(cx + 1, mouth + 0.5, 8, 2), FIRE[2], glow=True)
    s.fill(s.ellipse(cx, mouth, 5, 1.2), FIRE[3], glow=True)
    for (x, L) in ((cx - 5, 14), (cx + 4, 22), (cx + 8, 9)):            # lava runs
        s.fill(s.rect(x, mouth + 1, x + 2, mouth + L), FIRE[2], glow=True)
        s.fill(s.rect(x, mouth + 1, x + 1, mouth + L - 2), FIRE[3], glow=True)
        s.fill(s.ellipse(x + 1, mouth + L, 2, 1.2), FIRE[1], glow=True)
    flame(s, cx + 1, mouth - 1, 10, 10, seed=9)
    s.ink()
    s.pxs([(cx - 2, mouth - 16), (cx + 5, mouth - 20), (cx + 1, mouth - 24)], FIRE[3], glow=True)
    return s, meta_for(s, "fire", mouth - 4, energy=1.25, rng=120, height=40)


@tower
def hybrid_soulflame():
    """Soulflame: an obsidian brazier on a stack of skulls, burning with a cold green-violet ghost fire."""
    s = Sprite(40, 84)
    cx, bottom = 19, 80
    plinth(s, cx, bottom, 30, 5, OBSID, seed=301)
    for k, (x, y) in enumerate(((cx - 7, bottom - 9), (cx + 1, bottom - 9), (cx - 3, bottom - 16), (cx + 5, bottom - 15),
                                 (cx - 9, bottom - 15))):
        s.part(s.ellipse(x + 3, y, 4, 3.6), BONE, bias=-0.1 * (k % 2))
        s.fill(s.rect(x + 1, y, x + 3, y + 2), INK)
        s.fill(s.rect(x + 4, y, x + 6, y + 2), INK)
        s.px(x + 2, y + 1, SOUL[2], glow=True)
        s.px(x + 5, y + 1, SOUL[2], glow=True)
    s.part(s.poly([(cx - 4, bottom - 20), (cx + 5, bottom - 20), (cx + 3, bottom - 44), (cx - 2, bottom - 44)]), OBSID, flat=True)
    bowl = bottom - 50
    s.part(s.poly([(cx - 10, bowl - 1), (cx + 11, bowl - 1), (cx + 6, bowl + 6), (cx - 5, bowl + 6)]), OBSID)
    s.line(cx - 10, bowl - 1, cx + 11, bowl - 1, OBSID[4])
    for x in (cx - 6, cx, cx + 6):
        s.px(x, bowl + 2, VOIDC[3], glow=True)
    flame(s, cx + 0.5, bowl - 1, 17, 24, seed=11, tones=[VOIDC[0], VOIDC[2], SOUL[2], SOUL[3], SOUL[4]])
    s.ink()
    s.pxs([(cx - 6, bowl - 28), (cx + 7, bowl - 24)], SOUL[3], glow=True)
    return s, meta_for(s, "void", bowl - 8, energy=1.1, rng=110, height=44)


@tower
def hybrid_steam():
    """Steam Vent: a riveted copper boiler on a stone hearth, a furnace mouth glowing, steam jetting from a valve."""
    s = Sprite(42, 82)
    cx, bottom = 20, 78
    plinth(s, cx, bottom, 34, 5, STONE_D, seed=401)
    course_wall(s, cx, bottom - 5, 26, 26, 10, STONE_D, row_h=5, seed=402)
    s.fill(s.rect(cx - 5, bottom - 13, cx + 5, bottom - 7), INK)
    s.fill(s.rect(cx - 4, bottom - 12, cx + 4, bottom - 7), FIRE[2], glow=True)
    s.fill(s.rect(cx - 2, bottom - 11, cx + 2, bottom - 8), FIRE[3], glow=True)
    tank_b, tank_t = bottom - 15, bottom - 44
    s.part(s.capsule(cx, tank_b - 6, cx, tank_t + 6, 10.5), COPPER)
    for y in (tank_b - 7, tank_b - 16, tank_t + 9):
        s.line(cx - 10, y, cx + 10, y, COPPER[1])
        for x in range(int(cx - 8), int(cx + 9), 4):
            s.px(x, y - 1, COPPER[4])
    s.part(s.rect(cx + 8, tank_t + 10, cx + 16, tank_t + 13), IRON, flat=True)     # pipe
    s.part(s.rect(cx + 13, tank_t + 13, cx + 16, bottom - 6), IRON, flat=True)
    s.part(s.rect(cx - 2, tank_t - 8, cx + 3, tank_t + 2), IRON, flat=True)          # valve stack
    s.part(s.rect(cx - 4, tank_t - 10, cx + 5, tank_t - 7), IRON, flat=True)
    s.fill(s.ellipse(cx + 0.5, tank_t - 4, 2, 1.5), (255, 240, 220))
    s.ink()
    for (x, y, r) in ((cx, tank_t - 15, 4), (cx - 3, tank_t - 22, 5), (cx + 3, tank_t - 29, 5.5), (cx - 1, tank_t - 36, 4)):
        s.fill(s.ellipse(x, y, r, r * 0.8), STEAM[1])
        s.fill(s.ellipse(x - 1, y - 1, r * 0.7, r * 0.55), STEAM[2])
        s.px(x - r * 0.4, y - r * 0.4, STEAM[3])
    return s, meta_for(s, "water", tank_t - 14, light_y=bottom - 10, energy=0.9, rng=100, height=30, emitter="drips")


# ------------------------------------------------------------------------------------------------ storm + x
@tower
def hybrid_squall():
    """Squall: a slate lighthouse with a lantern room of blue glass, a storm cloud raining around its crown."""
    s = Sprite(40, 92)
    cx, bottom = 19, 88
    plinth(s, cx, bottom, 30, 5, SLATE, seed=501)
    course_wall(s, cx, bottom - 5, 18, 13, 40, SLATE, row_h=6, seed=502, moss_rows=1)
    top = bottom - 45
    s.part(s.rect(cx - 9, top - 2, cx + 10, top + 1), IRON, flat=True)
    s.fill(s.rect(cx - 6, top - 12, cx + 7, top - 2), AQUA[2], glow=True)
    s.fill(s.rect(cx - 4, top - 11, cx + 2, top - 3), AQUA[3], glow=True)
    for x in (cx - 6, cx, cx + 6):
        s.line(x, top - 12, x, top - 2, IRON[1])
    s.part(s.poly([(cx - 8, top - 12), (cx + 9, top - 12), (cx + 1, top - 19)]), SLATE, flat=True)
    cy = top - 26
    for (x, y, r) in ((cx - 9, cy + 1, 6), (cx + 9, cy + 1, 6), (cx, cy - 3, 8), (cx - 3, cy + 3, 6), (cx + 5, cy + 3, 6)):
        s.part(s.ellipse(x, y, r, r * 0.75), CLOUD)
    s.ink()
    arcs(s, [(cx + 2, cy + 6), (cx - 1, cy + 11), (cx + 2, cy + 13), (cx - 2, cy + 19)], BOLT[4])
    rng = np.random.default_rng(12)
    for _ in range(14):
        x = cx + int(rng.integers(-15, 16))
        y = cy + int(rng.integers(8, 30))
        if not s.a[y, x]:
            s.line(x, y, x - 1, y + 2, AQUA[3], glow=True)
    return s, meta_for(s, "storm", cy, energy=1.0, rng=110, height=50)


@tower
def hybrid_thornstorm():
    """Thornstorm: a thorned tree split by lightning, a copper spike driven through its crown, sparks in the leaves."""
    s = Sprite(42, 86)
    cx, bottom = 20, 82
    trunk(s, cx, bottom, bottom - 38, 6, BARK, BARK_D)
    s.line(cx, bottom - 6, cx + 1, bottom - 30, ramp("2a2018")[1])             # the split
    s.line(cx + 1, bottom - 8, cx + 2, bottom - 30, BOLT[3], glow=True)
    leaf_crown(s, cx + 1, bottom - 50, 34, 18, LEAF, LEAF_D, seed=13)
    for (x, y, dx, dy) in ((cx - 16, bottom - 52, -3, -1), (cx + 18, bottom - 54, 3, -1), (cx - 8, bottom - 64, -2, -2),
                           (cx + 10, bottom - 66, 2, -2), (cx - 14, bottom - 46, -3, 1)):
        s.line(x, y, x + dx, y + dy, BONE_THORN)
    s.part(s.rect(cx, bottom - 80, cx + 3, bottom - 56), COPPER, flat=True)
    s.part(s.poly([(cx - 1, bottom - 80), (cx + 4, bottom - 80), (cx + 1.5, bottom - 85)]), COPPER, flat=True)
    s.ink()
    arcs(s, [(cx - 4, bottom - 78), (cx - 8, bottom - 72), (cx - 6, bottom - 68)], BOLT[4])
    arcs(s, [(cx + 6, bottom - 76), (cx + 10, bottom - 71), (cx + 8, bottom - 66)], BOLT[3])
    s.pxs([(cx - 9, bottom - 58), (cx + 7, bottom - 61), (cx - 2, bottom - 55)], BOLT[4], glow=True)
    return s, meta_for(s, "storm", bottom - 74, energy=1.0, rng=105, height=46)


@tower
def hybrid_lodestone():
    """Lodestone: a dark iron-veined monolith between two horns of iron, rock shards hanging in its field."""
    s = Sprite(44, 84)
    cx, bottom = 21, 80
    plinth(s, cx, bottom, 34, 6, STONE_D, seed=601)
    for a in (-1, 1):                                                         # iron horns
        pts = [(cx + a * 9, bottom - 6), (cx + a * 15, bottom - 22), (cx + a * 16, bottom - 44), (cx + a * 12, bottom - 56),
               (cx + a * 10, bottom - 54), (cx + a * 12, bottom - 42), (cx + a * 11, bottom - 24), (cx + a * 5, bottom - 6)]
        s.part(s.poly(pts), IRON, bias=-0.15 if a > 0 else 0)
        s.fill(s.rect(cx + a * 12 - 1, bottom - 58, cx + a * 12 + 2, bottom - 54), (210, 60, 50) if a < 0 else (60, 100, 210))
    block(s, cx - 6, bottom - 40, cx + 6, bottom - 6, SLATE, depth=3, chips=3, seed=602)
    s.line(cx - 3, bottom - 36, cx + 2, bottom - 26, BOLT[3], glow=True)
    s.line(cx + 2, bottom - 26, cx - 1, bottom - 14, BOLT[3], glow=True)
    for (x, y, w) in ((cx - 4, bottom - 52, 6), (cx + 1, bottom - 62, 5), (cx - 5, bottom - 70, 4)):
        block(s, x, y, x + w, y + w - 1, STONE, depth=2, seed=x + y)
    s.ink()
    arcs(s, [(cx - 11, bottom - 56), (cx - 5, bottom - 59), (cx + 1, bottom - 55), (cx + 6, bottom - 58), (cx + 11, bottom - 56)], BOLT[4])
    return s, meta_for(s, "storm", bottom - 60, energy=1.0, rng=105, height=46)


@tower
def hybrid_riftstorm():
    """Riftstorm: a shattered slate spire whose top floats apart around a violet tear crackling with lightning."""
    s = Sprite(40, 90)
    cx, bottom = 19, 86
    plinth(s, cx, bottom, 30, 5, OBSID, seed=701)
    course_wall(s, cx, bottom - 5, 18, 14, 24, SLATE, row_h=6, seed=702)
    top = bottom - 29
    s.part(s.poly([(cx - 7, top), (cx - 2, top - 6), (cx + 1, top - 2), (cx + 4, top - 7), (cx + 8, top)]), SLATE, flat=True)
    ry = top - 22
    for (pts, b) in (([(cx - 12, ry - 4), (cx - 6, ry - 9), (cx - 4, ry + 1), (cx - 9, ry + 5)], 0.0),
                     ([(cx + 6, ry - 10), (cx + 13, ry - 5), (cx + 10, ry + 4), (cx + 5, ry)], -0.1),
                     ([(cx - 3, ry - 18), (cx + 4, ry - 19), (cx + 2, ry - 12), (cx - 2, ry - 12)], 0.05)):
        s.part(s.poly(pts), SLATE, flat=True, bias=b)
    s.fill(s.poly([(cx, ry - 10), (cx + 3, ry - 2), (cx + 1, ry + 9), (cx - 2, ry + 1)]), VOIDC[1], glow=True)
    s.fill(s.poly([(cx, ry - 7), (cx + 1.5, ry - 1), (cx, ry + 6), (cx - 1, ry + 1)]), VOIDC[3], glow=True)
    s.ink()
    arcs(s, [(cx + 2, ry - 3), (cx + 7, ry - 6), (cx + 9, ry - 1)], BOLT[4])
    arcs(s, [(cx - 1, ry + 3), (cx - 6, ry + 1), (cx - 9, ry + 6)], VOIDC[4])
    return s, meta_for(s, "void", ry, energy=1.0, rng=110, height=50)


# ------------------------------------------------------------------------------------------------ nature/water/earth/void
@tower
def hybrid_bog():
    """Bog: a rotten mossy stump standing in a black-green pool, lily pads, bubbles of glowing swamp gas."""
    s = Sprite(44, 74)
    cx, bottom = 21, 70
    pool_top(s, cx + 1, bottom - 7, 20, 7, MUD, BOGW, BOGW[4])
    for (x, y) in ((cx - 13, bottom - 6), (cx + 12, bottom - 9), (cx + 6, bottom - 3)):
        s.fill(s.ellipse(x, y, 3, 1.4), LEAF[3])
        s.px(x + 1, y, LEAF[1])
    trunk(s, cx, bottom - 8, bottom - 36, 8, ROOTS, ramp("3a2c20"))
    s.part(s.poly([(cx - 8, bottom - 36), (cx - 5, bottom - 44), (cx - 1, bottom - 38), (cx + 3, bottom - 46), (cx + 6, bottom - 37),
                   (cx + 8, bottom - 36)]), ROOTS, flat=True)
    for y in range(bottom - 34, bottom - 10, 3):                                 # moss beard
        s.line(cx - 7, y, cx - 4, y + 1, MOSS[2 + (y % 2)])
    for (x, y) in ((cx + 2, bottom - 30), (cx - 2, bottom - 22)):
        s.fill(s.ellipse(x, y, 1.6, 1.6), BOGW[3], glow=True)
    s.ink()
    for (x, y, r) in ((cx - 4, bottom - 52, 3), (cx + 4, bottom - 58, 2.4), (cx - 1, bottom - 64, 2)):
        s.fill(s.ellipse(x, y, r, r), BOGW[3], glow=True)
        s.px(x - r * 0.4, y - r * 0.4, BOGW[4], glow=True)
    return s, meta_for(s, "nature", bottom - 54, light_y=bottom - 10, energy=0.8, rng=95, height=30)


@tower
def hybrid_quagmire():
    """Quagmire: a ring of sunken standing stones around a pool of tar, a boulder slowly going under."""
    s = Sprite(46, 66)
    cx, bottom = 22, 62
    pool_top(s, cx + 1, bottom - 10, 21, 8, MUD, TAR, TAR[4])
    for (x, h, w) in ((cx - 19, 26, 7), (cx + 12, 30, 7), (cx - 9, 38, 7)):
        block(s, x, bottom - 10 - h, x + w, bottom - 6, STONE_D, depth=2, chips=2, seed=x + h, moss=2)
    s.part(s.ellipse(cx + 3, bottom - 12, 7, 5), SAND)
    s.fill(s.rect(cx - 5, bottom - 10, cx + 12, bottom - 6), TAR[1])
    s.ink()
    for (x, y) in ((cx - 6, bottom - 12), (cx + 10, bottom - 8)):
        s.fill(s.ellipse(x, y, 1.6, 1.0), TAR[4])
    s.line(cx - 9, bottom - 40, cx - 9, bottom - 34, AQUA[3], glow=True)
    s.line(cx + 15, bottom - 32, cx + 15, bottom - 26, AMBER[3], glow=True)
    return s, meta_for(s, "earth", bottom - 30, light_y=bottom - 14, energy=0.7, rng=90, height=28)


@tower
def hybrid_ironbark():
    """Ironbark: an ancient oak grown around chiselled stone, iron bands rusted into the bark, amber sap."""
    s = Sprite(46, 86)
    cx, bottom = 22, 82
    block(s, cx - 15, bottom - 14, cx - 3, bottom, STONE_D, depth=3, chips=2, seed=901, moss=3)
    block(s, cx + 3, bottom - 10, cx + 16, bottom, STONE_D, depth=3, chips=2, seed=902, moss=3)
    trunk(s, cx, bottom, bottom - 44, 8, BARK, BARK_D)
    for y in (bottom - 14, bottom - 30):
        s.part(s.rect(cx - 6 + (bottom - y) * 0.06, y - 2, cx + 7 - (bottom - y) * 0.06, y), IRON, flat=True)
        s.px(cx - 4, y - 1, ramp("8a4a2a")[3])
    s.fill(s.ellipse(cx + 3, bottom - 22, 1.6, 2.4), AMBER[3], glow=True)
    leaf_crown(s, cx, bottom - 54, 42, 20, LEAF, LEAF_D, seed=14)
    s.ink()
    return s, meta_for(s, "nature", bottom - 56, light_y=bottom - 22, energy=0.7, rng=90, height=32)


@tower
def hybrid_abyss():
    """Abyss: a sunken well of black stone, a whirlpool turning in it, dark tentacles of water rising round."""
    s = Sprite(44, 74)
    cx, bottom = 21, 70
    for k, x in enumerate(range(cx - 18, cx + 18, 6)):
        block(s, x, bottom - 12, x + 6, bottom, OBSID, depth=0, seed=1000 + k)
    s.fill(s.ellipse(cx + 1, bottom - 13, 19, 6), OBSID[3])
    s.fill(s.ellipse(cx + 1, bottom - 12.5, 16, 4.6), [12, 20, 50])
    for k, r in enumerate((14, 10, 6)):
        ring = s.ellipse(cx + 1, bottom - 12.5, r, r * 0.3) & ~s.ellipse(cx + 1, bottom - 12.5, r - 1.3, r * 0.3 - 0.6)
        s.fill(ring, AQUA[1 + k], glow=True)
    s.fill(s.ellipse(cx + 1, bottom - 12.5, 2.5, 1), VOIDC[2], glow=True)
    for (x, ph, h) in ((cx - 11, 0.0, 30), (cx + 12, 1.5, 26), (cx + 1, 3.0, 38)):
        pts_l, pts_r = [], []
        for k in range(12):
            t = k / 11
            y = bottom - 14 - t * h
            xx = x + math.sin(t * 4 + ph) * 3 * (1 - t * 0.3)
            w = 2.6 * (1 - t) + 0.6
            pts_l.append((xx - w, y))
            pts_r.append((xx + w, y))
        s.part(s.poly(pts_l + pts_r[::-1]), [hexc(c) for c in ("0c1630", "16285a", "1f4a8a", "3a78b8", "7ab0e0")])
    s.ink((8, 10, 30))
    s.pxs([(cx - 11, bottom - 44), (cx + 1, bottom - 52), (cx + 12, bottom - 40)], AQUA[4], glow=True)
    return s, meta_for(s, "water", bottom - 30, light_y=bottom - 14, energy=0.9, rng=100, height=34)


@tower
def hybrid_gravity_well():
    """Gravity Well: a broken pedestal, a black sphere over it with a violet rim, cut blocks orbiting it."""
    s = Sprite(44, 84)
    cx, bottom = 21, 80
    plinth(s, cx, bottom, 32, 6, SAND, seed=1101)
    block(s, cx - 6, bottom - 26, cx + 6, bottom - 6, SAND, depth=3, chips=2, seed=1102)
    s.fill(s.poly([(cx - 6, bottom - 26), (cx - 2, bottom - 29), (cx + 2, bottom - 26), (cx + 6, bottom - 30), (cx + 6, bottom - 26)]), SAND[4])
    oy = bottom - 48
    s.fill(s.ellipse(cx, oy, 9.5, 9.5), VOIDC[2], glow=True)
    s.fill(s.ellipse(cx, oy, 8, 8), (10, 6, 18))
    s.fill(s.ellipse(cx - 3, oy - 3, 1.6, 1.2), VOIDC[3], glow=True)
    for (x, y, w) in ((cx - 18, oy - 2, 6), (cx + 12, oy + 4, 5), (cx + 7, oy - 16, 5), (cx - 10, oy + 12, 4)):
        block(s, x, y, x + w, y + w - 1, SAND, depth=2, seed=x * 3 + y)
    s.ink()
    ring = s.ellipse(cx, oy + 1, 18, 4.5) & ~s.ellipse(cx, oy + 1, 16.8, 3.6) & ~s.a
    s.fill(ring, VOIDC[3], glow=True)
    return s, meta_for(s, "void", oy, energy=0.9, rng=105, height=44)


@tower
def hybrid_blightroot():
    """Blightroot: a twisted tree gone to rot, violet bark, black leaves, a glowing eye in its hollow."""
    s = Sprite(44, 84)
    cx, bottom = 21, 80
    trunk(s, cx, bottom, bottom - 42, 7, BLIGHT, ramp("3a2850"), lean=-1)
    s.fill(s.ellipse(cx, bottom - 24, 3.4, 4.4), (14, 6, 20))
    s.fill(s.ellipse(cx, bottom - 24, 2.4, 1.4), SAP[3], glow=True)
    s.px(cx, bottom - 24, (20, 30, 10), glow=True)
    leaf_crown(s, cx - 1, bottom - 52, 38, 18, [hexc(c) for c in ("1e1430", "30204a", "46306a", "60448a", "8060b0")],
               [hexc(c) for c in ("140c20", "221632", "30204a", "46306a", "60448a")], seed=15)
    for (x, y, dx, dy) in ((cx - 18, bottom - 54, -3, 0), (cx + 17, bottom - 56, 3, -1), (cx - 6, bottom - 72, -1, -3)):
        s.line(x, y, x + dx, y + dy, BONE_THORN)
    for (x, y) in ((cx - 10, bottom - 56), (cx + 8, bottom - 60), (cx, bottom - 68), (cx + 12, bottom - 52)):
        s.fill(s.ellipse(x, y, 1.8, 1.8), SAP[2], glow=True)
    s.ink()
    return s, meta_for(s, "nature", bottom - 58, light_y=bottom - 26, energy=0.8, rng=95, height=34, emitter="void")
