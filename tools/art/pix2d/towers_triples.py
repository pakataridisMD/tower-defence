"""The twenty triple-element towers: the grandest buildings on the board, about half again the size of a base tower.

Each is one landmark that shows all three of its elements: Worldforge is a mountain forge with a tree on its peak,
Starfall an observatory catching a falling star. Registered in TOWERS through towers.py.
"""
from __future__ import annotations

import math

import numpy as np

from kit import INK, hexc, ramp, Sprite
from creatures import STONE, STONE_D, IRON, GOLD, MOSS, BONE
from towers import (AMBER, AQUA, BARK, BARK_D, BASALT, BOLT, COPPER, FIRE, LEAF, LEAF_D, MARBLE, OBSID, SAND, SAP,
                    SLATE, VOIDC, BONE_THORN, block, course_wall, flame, orb, plinth, meta_for, tower)
from towers_duals import (BLIGHT, BOGW, BRASS, CLOUD, EMBER_LEAF, MUD, ROOTS, SOUL, STEAM, TAR, arcs, leaf_crown,
                          pool_top, trunk)

ICE = [hexc(c) for c in ("2a4a6a", "4a7aa8", "7ab4e0", "b4e0f8", "eefaff")]
AURORA = [hexc(c) for c in ("1a6a5a", "2ac0a0", "8af0c0", "d0fff0")]
STAR = [hexc(c) for c in ("8a6a20", "e0b030", "ffe070", "fff6c0", "ffffff")]
DARK_WATER = [hexc(c) for c in ("0c1630", "16285a", "1f4a8a", "3a78b8", "7ab0e0")]


def cloud(s, cx, cy, w, tones=CLOUD):
    for (x, y, r) in ((cx - w * 0.32, cy + 1, w * 0.22), (cx + w * 0.32, cy + 1, w * 0.22), (cx, cy - 3, w * 0.3),
                      (cx - w * 0.1, cy + 3, w * 0.24), (cx + w * 0.16, cy + 3, w * 0.22)):
        s.part(s.ellipse(x, y, r, r * 0.72), tones)


def bolt_down(s, x, y0, y1, seed=0, col=None):
    rng = np.random.default_rng(seed)
    pts = [(x, y0)]
    y = y0
    while y < y1:
        y += rng.integers(3, 6)
        x += rng.integers(-3, 4)
        pts.append((x, min(y, y1)))
    arcs(s, pts, col or BOLT[4])


def rain(s, cx, top, w, h, seed=0, col=None):
    rng = np.random.default_rng(seed)
    for _ in range(int(w * h / 40)):
        x = cx + int(rng.integers(-w // 2, w // 2))
        y = top + int(rng.integers(0, h))
        if 0 <= y < s.h - 2 and 0 <= x < s.w and not s.a[y, x]:
            s.line(x, y, x - 1, y + 2, col or AQUA[3], glow=True)


def drum(s, cx, bottom, w, h, tones, seed=0):
    """A wide round base of stone courses."""
    plinth(s, cx, bottom, w + 8, 6, tones, seed=seed)
    course_wall(s, cx, bottom - 6, w, w - 2, h, tones, row_h=6, seed=seed + 1)


# ------------------------------------------------------------------------------------------------ fire-led
@tower
def triple_worldforge():
    """Worldforge (fire, nature, earth): a mountain-forge of sandstone blocks, lava in its mouth, a great tree on top."""
    s = Sprite(52, 98)
    cx, bottom = 25, 94
    for k, (w, h) in enumerate(((44, 12), (36, 12), (28, 10))):
        y = bottom - sum(hh for _, hh in ((44, 12), (36, 12), (28, 10))[:k])
        n = max(2, w // 9)
        for j in range(n):
            a, b = cx - w / 2 + w * j / n, cx - w / 2 + w * (j + 1) / n
            block(s, round(a), y - h, round(b), y, SAND, depth=3 if j == n - 1 else 0, top=False, side=j == n - 1,
                  chips=2, seed=1200 + k * 10 + j, strata=4)
    s.fill(s.rect(cx - 6, bottom - 16, cx + 6, bottom - 4), INK)
    s.fill(s.poly([(cx - 5, bottom - 4), (cx - 5, bottom - 12), (cx, bottom - 15), (cx + 5, bottom - 12), (cx + 5, bottom - 4)]), FIRE[2], glow=True)
    s.fill(s.rect(cx - 3, bottom - 10, cx + 3, bottom - 4), FIRE[3], glow=True)
    top = bottom - 34
    trunk(s, cx, top, top - 22, 5, BARK, BARK_D)
    leaf_crown(s, cx, top - 34, 44, 22, LEAF, LEAF_D, seed=16)
    for (x, y) in ((cx - 9, top - 34), (cx + 10, top - 38), (cx + 2, top - 44)):
        s.fill(s.ellipse(x, y, 1.6, 1.6), AMBER[3], glow=True)
    s.ink()
    s.pxs([(cx - 3, bottom - 20), (cx + 4, bottom - 24)], FIRE[3], glow=True)
    return s, meta_for(s, "fire", top - 30, light_y=bottom - 10, energy=1.2, rng=130, height=44)


@tower
def triple_hellforge():
    """Hellforge (earth, void, fire): an obsidian anvil-altar on a basalt forge, violet fire roaring behind it."""
    s = Sprite(52, 90)
    cx, bottom = 25, 86
    drum(s, cx, bottom, 36, 14, BASALT, seed=1300)
    top = bottom - 20
    flame(s, cx + 1, top - 2, 30, 40, seed=17, tones=[VOIDC[0], VOIDC[1], VOIDC[2], FIRE[3], FIRE[4]])
    s.part(s.poly([(cx - 13, top - 14), (cx + 15, top - 14), (cx + 10, top - 9), (cx + 6, top - 9), (cx + 6, top - 2),
                   (cx - 4, top - 2), (cx - 4, top - 9), (cx - 9, top - 9)]), OBSID, flat=True)
    s.line(cx - 13, top - 14, cx + 15, top - 14, OBSID[4])
    s.fill(s.rect(cx - 2, top - 13, cx + 4, top - 11), FIRE[3], glow=True)
    for x in (cx - 14, cx + 13):
        s.part(s.poly([(x - 2, top), (x + 3, top), (x + 1, top - 22), (x - 1, top - 20)]), OBSID, flat=True)
        s.px(x, top - 12, VOIDC[3], glow=True)
    s.ink()
    s.pxs([(cx - 8, top - 44), (cx + 9, top - 40), (cx + 2, top - 48)], FIRE[3], glow=True)
    return s, meta_for(s, "fire", top - 24, energy=1.3, rng=130, height=46)


@tower
def triple_witchfire():
    """Witchfire Tree (fire, nature, void): a crooked black tree hung with lanterns of green-violet witch fire."""
    s = Sprite(52, 94)
    cx, bottom = 25, 90
    trunk(s, cx, bottom, bottom - 50, 7, ramp("2e2430", spread=0.4), ramp("221a26", spread=0.4), lean=-2)
    for (x0, y0, x1, y1) in ((cx - 2, bottom - 44, cx - 18, bottom - 60), (cx - 18, bottom - 60, cx - 22, bottom - 72),
                             (cx + 1, bottom - 46, cx + 17, bottom - 64), (cx + 17, bottom - 64, cx + 20, bottom - 78),
                             (cx - 1, bottom - 50, cx + 1, bottom - 84), (cx - 10, bottom - 52, cx - 12, bottom - 66)):
        s.part(s.capsule(x0, y0, x1, y1, 2.2, 1.0), ramp("2e2430", spread=0.4))
    for (x, y) in ((cx - 18, bottom - 56), (cx + 15, bottom - 58), (cx + 1, bottom - 74), (cx - 11, bottom - 64)):
        s.line(x, y - 6, x, y - 3, IRON[2])
        s.part(s.rect(x - 2, y - 3, x + 3, y + 3), IRON, flat=True)
        s.fill(s.rect(x - 1, y - 2, x + 2, y + 2), SOUL[2], glow=True)
        s.px(x, y - 1, SOUL[4], glow=True)
    s.fill(s.ellipse(cx - 1, bottom - 26, 3, 4), (10, 6, 14))
    s.fill(s.ellipse(cx - 1, bottom - 26, 2, 1.2), VOIDC[3], glow=True)
    s.ink()
    flame(s, cx + 1, bottom - 84, 8, 12, seed=18, tones=[VOIDC[0], VOIDC[2], SOUL[2], SOUL[3], SOUL[4]])
    return s, meta_for(s, "void", bottom - 76, energy=1.1, rng=120, height=48)


@tower
def triple_mistwraith():
    """Mistwraith (fire, water, void): a tall hooded stone lantern, a pale fire in it, fog pouring off its base."""
    s = Sprite(48, 96)
    cx, bottom = 23, 92
    drum(s, cx, bottom, 26, 8, STONE_D, seed=1400)
    s.part(s.poly([(cx - 9, bottom - 14), (cx + 10, bottom - 14), (cx + 7, bottom - 52), (cx - 6, bottom - 52)]), STONE, flat=True)
    s.line(cx - 9, bottom - 14, cx - 6, bottom - 52, STONE[4])
    top = bottom - 52
    s.part(s.poly([(cx - 12, top), (cx + 13, top), (cx + 8, top - 18), (cx + 1, top - 30), (cx - 7, top - 18)]), STONE_D, flat=True)
    s.fill(s.poly([(cx - 6, top - 2), (cx + 7, top - 2), (cx + 4, top - 16), (cx + 1, top - 20), (cx - 3, top - 16)]), INK)
    flame(s, cx + 0.5, top - 3, 9, 15, seed=19, tones=[AQUA[0], AQUA[2], AQUA[3], (230, 250, 255), (255, 255, 255)])
    s.ink()
    rng = np.random.default_rng(20)
    for _ in range(9):
        x, y = cx + rng.uniform(-22, 22), bottom - rng.uniform(2, 14)
        r = rng.uniform(3, 6)
        m = s.ellipse(x, y, r, r * 0.55) & ~s.a
        s.fill(m, STEAM[1])
        s.fill(m & (s.ys < y - r * 0.15), STEAM[2])
    s.px(cx - 10, top - 26, VOIDC[3], glow=True)
    s.px(cx + 12, top - 30, VOIDC[3], glow=True)
    return s, meta_for(s, "water", top - 10, energy=1.0, rng=115, height=48)


@tower
def triple_obsidian_geyser():
    """Obsidian Geyser (fire, water, earth): a cone of black glass split by a scalding geyser of steam and water."""
    s = Sprite(50, 96)
    cx, bottom = 24, 92
    s.part(s.poly([(cx - 22, bottom), (cx - 8, bottom - 30), (cx + 9, bottom - 30), (cx + 23, bottom)]), OBSID)
    for (x0, x1) in ((cx - 16, cx - 10), (cx + 7, cx + 14)):
        s.part(s.poly([(x0, bottom), (x0 + 3, bottom - 18), (x1, bottom - 22), (x1 + 2, bottom)]), OBSID, flat=True, bias=0.1)
    s.fill(s.ellipse(cx + 0.5, bottom - 30, 8.5, 2.6), FIRE[1], glow=True)
    s.fill(s.ellipse(cx + 0.5, bottom - 30, 5, 1.4), FIRE[3], glow=True)
    s.line(cx - 6, bottom - 22, cx - 9, bottom - 8, FIRE[2], glow=True)
    s.line(cx + 7, bottom - 24, cx + 10, bottom - 10, FIRE[2], glow=True)
    s.part(s.poly([(cx - 4, bottom - 31), (cx + 5, bottom - 31), (cx + 3, bottom - 70), (cx - 2, bottom - 70)]), AQUA, glow=True)
    s.ink()
    for (x, y, r) in ((cx, bottom - 72, 6), (cx - 6, bottom - 78, 5), (cx + 5, bottom - 80, 5.5), (cx, bottom - 86, 4.5)):
        s.fill(s.ellipse(x, y, r, r * 0.8), STEAM[1])
        s.fill(s.ellipse(x - 1, y - 1, r * 0.7, r * 0.55), STEAM[2])
    rain(s, cx, bottom - 70, 26, 26, seed=21)
    return s, meta_for(s, "water", bottom - 60, light_y=bottom - 32, energy=1.2, rng=120, height=40, emitter="drips")


# ------------------------------------------------------------------------------------------------ storm-led
@tower
def triple_starfall():
    """Starfall (void, fire, storm): an observatory of pale marble with a bronze armillary catching a burning star."""
    s = Sprite(50, 100)
    cx, bottom = 24, 96
    drum(s, cx, bottom, 30, 26, MARBLE, seed=1500)
    top = bottom - 32
    s.part(s.ellipse(cx, top - 3, 14, 7), [hexc(c) for c in ("1e2a5a", "2a3a7a", "3a4e9a", "5a6ab8", "8a9ad8")])
    s.pxs([(cx - 6, top - 6), (cx + 3, top - 7), (cx + 8, top - 3), (cx - 2, top - 2)], STAR[4])
    s.part(s.rect(cx, top - 28, cx + 2, top - 6), BRASS, flat=True)
    oy = top - 34
    ring1 = s.ellipse(cx + 1, oy, 12, 12) & ~s.ellipse(cx + 1, oy, 10.8, 10.8)
    ring2 = s.ellipse(cx + 1, oy, 12, 4) & ~s.ellipse(cx + 1, oy, 10.8, 3)
    s.fill(ring1, BRASS[2])
    s.fill(ring2, BRASS[3])
    orb(s, cx + 1, oy, 5.5, STAR)
    s.ink()
    s.line(cx + 16, oy - 22, cx + 7, oy - 7, STAR[3], glow=True)
    s.line(cx + 17, oy - 22, cx + 8, oy - 7, FIRE[2], glow=True)
    arcs(s, [(cx - 10, oy + 4), (cx - 15, oy + 9), (cx - 12, oy + 13)], VOIDC[3])
    return s, meta_for(s, "storm", oy, energy=1.2, rng=125, height=52)


@tower
def triple_storm_eye():
    """Eye of the Storm (storm, water, void): a slender spire under a turning storm wall, a violet eye in its centre."""
    s = Sprite(54, 100)
    cx, bottom = 26, 96
    drum(s, cx, bottom, 20, 34, SLATE, seed=1600)
    top = bottom - 40
    s.part(s.poly([(cx - 8, top), (cx + 9, top), (cx + 1, top - 12)]), SLATE, flat=True)
    cy = top - 30
    for k, (rx, ry, tone) in enumerate(((24, 11, CLOUD[1]), (20, 9, CLOUD[2]), (15, 7, CLOUD[3]))):
        ring = s.ellipse(cx, cy, rx, ry) & ~s.ellipse(cx, cy + 1, rx - 4, ry - 3)
        s.fill(ring, tone)
    s.fill(s.ellipse(cx, cy + 1, 11, 4), DARK_WATER[1])
    s.fill(s.ellipse(cx, cy + 1, 6, 3), VOIDC[2], glow=True)
    s.fill(s.ellipse(cx, cy + 1, 1.4, 2.6), (14, 6, 24), glow=True)
    s.ink()
    bolt_down(s, cx - 14, cy + 8, top - 2, seed=22)
    bolt_down(s, cx + 15, cy + 8, top + 6, seed=23)
    rain(s, cx, cy + 8, 46, 30, seed=24)
    return s, meta_for(s, "storm", cy, energy=1.1, rng=125, height=56)


@tower
def triple_thunder_geyser():
    """Thunder Geyser (fire, storm, water): a copper pressure tower, a column of boiling water shot through with arcs."""
    s = Sprite(48, 98)
    cx, bottom = 23, 94
    drum(s, cx, bottom, 30, 10, STONE_D, seed=1700)
    s.part(s.capsule(cx, bottom - 22, cx, bottom - 44, 10), COPPER)
    for y in (bottom - 22, bottom - 32, bottom - 42):
        s.line(cx - 10, y, cx + 10, y, COPPER[1])
    s.fill(s.rect(cx - 4, bottom - 20, cx + 4, bottom - 16), FIRE[2], glow=True)
    top = bottom - 54
    s.part(s.rect(cx - 3, top, cx + 4, bottom - 52), IRON, flat=True)
    s.part(s.poly([(cx - 3, top), (cx + 4, top), (cx + 3, top - 32), (cx - 2, top - 32)]), AQUA, glow=True)
    s.ink()
    for (x, y, r) in ((cx, top - 34, 5), (cx - 5, top - 39, 4), (cx + 5, top - 40, 4.5)):
        s.fill(s.ellipse(x, y, r, r * 0.8), STEAM[1])
        s.fill(s.ellipse(x - 1, y - 1, r * 0.7, r * 0.55), STEAM[2])
    arcs(s, [(cx - 3, top - 6), (cx - 9, top - 12), (cx - 6, top - 18), (cx - 11, top - 24)], BOLT[4])
    arcs(s, [(cx + 4, top - 14), (cx + 10, top - 20), (cx + 8, top - 26)], BOLT[3])
    rain(s, cx, top - 30, 28, 30, seed=25)
    return s, meta_for(s, "storm", top - 20, energy=1.1, rng=120, height=48)


@tower
def triple_thunderforge():
    """Thunderforge (fire, storm, earth): a smithy tower of stone, a great anvil on top, a lightning rod striking it."""
    s = Sprite(52, 100)
    cx, bottom = 25, 96
    drum(s, cx, bottom, 32, 28, STONE_D, seed=1800)
    s.fill(s.rect(cx - 5, bottom - 18, cx + 5, bottom - 8), INK)
    s.fill(s.rect(cx - 4, bottom - 16, cx + 4, bottom - 8), FIRE[2], glow=True)
    top = bottom - 34
    s.part(s.poly([(cx - 14, top - 10), (cx + 16, top - 10), (cx + 11, top - 6), (cx + 6, top - 6), (cx + 6, top),
                   (cx - 4, top), (cx - 4, top - 6), (cx - 9, top - 6)]), IRON, flat=True)
    s.line(cx - 14, top - 10, cx + 16, top - 10, IRON[4])
    s.fill(s.rect(cx - 2, top - 9, cx + 4, top - 7), FIRE[3], glow=True)
    s.part(s.rect(cx + 12, top - 44, cx + 14, top - 10), COPPER, flat=True)
    s.part(s.poly([(cx + 11, top - 44), (cx + 15, top - 44), (cx + 13, top - 50)]), COPPER, flat=True)
    s.ink()
    bolt_down(s, cx + 13, top - 64, top - 50, seed=26)
    arcs(s, [(cx + 12, top - 30), (cx + 6, top - 22), (cx + 2, top - 12)], BOLT[4])
    s.pxs([(cx - 6, top - 14), (cx + 3, top - 16), (cx - 1, top - 18)], FIRE[3], glow=True)
    return s, meta_for(s, "storm", top - 20, energy=1.2, rng=125, height=50)


@tower
def triple_tidal_dynamo():
    """Tidal Dynamo (storm, water, earth): a stone mill tower turned by a waterfall, copper coils sparking at the hub."""
    s = Sprite(54, 96)
    cx, bottom = 25, 92
    pool_top(s, cx + 2, bottom - 6, 24, 6, STONE, AQUA, AQUA[4])
    course_wall(s, cx - 4, bottom - 8, 22, 18, 44, STONE, row_h=6, seed=1900)
    top = bottom - 52
    s.part(s.poly([(cx - 16, top), (cx + 8, top), (cx - 4, top - 14)]), SLATE, flat=True)
    hx, hy = cx + 12, bottom - 30
    for k in range(8):                                                         # wheel paddles
        a = k * math.pi / 4
        s.line(hx, hy, hx + math.cos(a) * 13, hy + math.sin(a) * 13, BARK[2])
        s.part(s.rect(hx + math.cos(a) * 12 - 2, hy + math.sin(a) * 12 - 2, hx + math.cos(a) * 12 + 2, hy + math.sin(a) * 12 + 2), BARK)
    ring = s.ellipse(hx, hy, 13, 13) & ~s.ellipse(hx, hy, 11.5, 11.5)
    s.fill(ring, BARK[1])
    s.part(s.ellipse(hx, hy, 3.5, 3.5), COPPER)
    s.fill(s.rect(cx + 8, top + 2, cx + 13, bottom - 44), AQUA[3], glow=True)     # the fall
    s.ink()
    arcs(s, [(hx - 3, hy - 3), (hx - 9, hy - 8), (hx - 14, hy - 6)], BOLT[4])
    arcs(s, [(hx + 3, hy + 2), (hx + 8, hy + 8)], BOLT[3])
    return s, meta_for(s, "storm", hy, energy=1.0, rng=115, height=40, muzzle_x=12)


@tower
def triple_amber_spire():
    """Amber Spire (storm, nature, earth): a tall spike of amber crystal grown from rock, wrapped in vines, crackling."""
    s = Sprite(48, 100)
    cx, bottom = 23, 96
    for (x, w, h) in ((cx - 18, 10, 14), (cx + 8, 12, 12), (cx - 8, 16, 8)):
        block(s, x, bottom - h, x + w, bottom, STONE_D, depth=3, chips=2, seed=x, moss=3)
    s.fill(s.poly([(cx - 8, bottom - 8), (cx + 9, bottom - 8), (cx + 4, bottom - 70), (cx + 1, bottom - 84), (cx - 3, bottom - 70)]),
           AMBER[1], glow=True)
    s.fill(s.poly([(cx - 4, bottom - 10), (cx + 1, bottom - 10), (cx + 1, bottom - 82), (cx - 2, bottom - 68)]), AMBER[2], glow=True)
    s.line(cx - 1, bottom - 70, cx - 1, bottom - 20, AMBER[3], glow=True)
    for (x, top, w) in ((cx - 12, bottom - 30, 5), (cx + 10, bottom - 26, 5)):
        s.fill(s.poly([(x - w / 2, bottom - 8), (x + w / 2, bottom - 8), (x, top)]), AMBER[2], glow=True)
    for k, y in enumerate(range(bottom - 64, bottom - 14, 9)):
        s.line(cx - 7 + k % 2, y + 4, cx + 7, y, LEAF[2])
        s.px(cx + 7, y - 1, LEAF[4])
    s.ink((90, 40, 10))
    arcs(s, [(cx + 1, bottom - 86), (cx + 6, bottom - 92), (cx + 4, bottom - 95)], BOLT[4])
    arcs(s, [(cx - 2, bottom - 84), (cx - 7, bottom - 89)], BOLT[3])
    return s, meta_for(s, "earth", bottom - 76, energy=1.0, rng=120, height=50)


@tower
def triple_polar_rift():
    """Polar Rift (storm, earth, void): pillars of blue ice around a violet tear in the air, an aurora above."""
    s = Sprite(54, 96)
    cx, bottom = 26, 92
    plinth(s, cx, bottom, 44, 6, SLATE, seed=2000)
    for (x, w, h, b) in ((cx - 19, 7, 34, -0.1), (cx + 13, 7, 40, -0.15), (cx - 10, 6, 46, 0.0), (cx + 5, 6, 50, 0.05)):
        s.part(s.poly([(x, bottom - 6), (x + w, bottom - 6), (x + w - 1, bottom - 6 - h), (x + w / 2, bottom - 10 - h),
                       (x + 1, bottom - 6 - h)]), ICE, flat=True, bias=b)
    ry = bottom - 34
    s.fill(s.poly([(cx, ry - 16), (cx + 4, ry - 4), (cx + 1, ry + 14), (cx - 3, ry + 2)]), VOIDC[1], glow=True)
    s.fill(s.poly([(cx, ry - 12), (cx + 2, ry - 2), (cx, ry + 10), (cx - 1, ry + 1)]), VOIDC[3], glow=True)
    s.ink((20, 30, 60))
    for k, tone in enumerate(AURORA[:3]):
        for x in range(cx - 22, cx + 23):
            y = bottom - 74 - k * 2 + math.sin(x * 0.25 + k) * 3
            if not s.a[int(y), x]:
                s.px(x, y, tone, glow=True)
    return s, meta_for(s, "void", ry, energy=1.0, rng=120, height=50)


@tower
def triple_cinderstorm():
    """Cinderstorm (fire, storm, nature): a burning tree under its own black thundercloud, bolts feeding the fire."""
    s = Sprite(54, 100)
    cx, bottom = 26, 96
    trunk(s, cx, bottom, bottom - 44, 7, ramp("3e2a22", spread=0.4), ramp("2e2018", spread=0.4))
    s.line(cx, bottom - 8, cx + 1, bottom - 36, FIRE[2], glow=True)
    leaf_crown(s, cx, bottom - 56, 42, 20, EMBER_LEAF, [FIRE[0], EMBER_LEAF[0], EMBER_LEAF[1], EMBER_LEAF[2], EMBER_LEAF[3]], seed=27)
    for (x, y, w, h) in ((cx - 9, bottom - 62, 9, 11), (cx + 9, bottom - 60, 8, 10), (cx, bottom - 68, 11, 14)):
        flame(s, x, y, w, h, seed=x + 3)
    cloud(s, cx, bottom - 88, 40, [hexc(c) for c in ("1e1e26", "2e2e3a", "44444e", "5e5e6a", "7a7a86")])
    s.ink()
    bolt_down(s, cx - 8, bottom - 82, bottom - 70, seed=28)
    bolt_down(s, cx + 10, bottom - 82, bottom - 68, seed=29)
    return s, meta_for(s, "fire", bottom - 62, energy=1.3, rng=130, height=50)


@tower
def triple_plague_storm():
    """Plague Storm (storm, nature, void): a blighted tree under a sickly green cloud raining poison."""
    s = Sprite(54, 100)
    cx, bottom = 26, 96
    trunk(s, cx, bottom, bottom - 44, 7, BLIGHT, ramp("3a2850"))
    leaf_crown(s, cx, bottom - 56, 40, 18, [hexc(c) for c in ("1e1430", "30204a", "46306a", "60448a", "8060b0")],
               [hexc(c) for c in ("140c20", "221632", "30204a", "46306a", "60448a")], seed=30)
    for (x, y) in ((cx - 10, bottom - 56), (cx + 9, bottom - 60), (cx, bottom - 66)):
        s.fill(s.ellipse(x, y, 1.6, 1.6), SAP[2], glow=True)
    cloud(s, cx, bottom - 86, 42, [hexc(c) for c in ("1e2a1a", "2e3e26", "445a34", "5e7a44", "7a9a5a")])
    s.ink()
    bolt_down(s, cx + 12, bottom - 80, bottom - 66, seed=31, col=SAP[3])
    rain(s, cx, bottom - 80, 44, 34, seed=32, col=SAP[2])
    return s, meta_for(s, "nature", bottom - 62, energy=1.0, rng=120, height=48, emitter="void")


@tower
def triple_rainwild():
    """Rainwild (storm, nature, water): a giant jungle tree with a waterfall pouring from its roots, rain in its crown."""
    s = Sprite(56, 100)
    cx, bottom = 27, 96
    pool_top(s, cx + 2, bottom - 5, 25, 6, MUD, AQUA, AQUA[4])
    trunk(s, cx, bottom - 6, bottom - 48, 9, ramp("8a7a60", spread=0.5), ramp("6a5a44", spread=0.45))
    s.fill(s.rect(cx - 2, bottom - 30, cx + 3, bottom - 8), AQUA[3], glow=True)
    s.fill(s.rect(cx - 1, bottom - 30, cx + 1, bottom - 8), AQUA[4], glow=True)
    leaf_crown(s, cx, bottom - 62, 50, 24, ramp("2e6a2a", spread=0.55), ramp("1e4a22", spread=0.5), seed=33)
    s.ink()
    cloud(s, cx + 2, bottom - 92, 30)
    rain(s, cx + 2, bottom - 88, 34, 12, seed=34)
    return s, meta_for(s, "nature", bottom - 64, energy=0.9, rng=115, height=46)


@tower
def triple_drowned_garden():
    """Drowned Garden (nature, water, void): a sunken shrine arch overgrown with vines, violet lilies in its pool."""
    s = Sprite(54, 90)
    cx, bottom = 26, 86
    pool_top(s, cx + 1, bottom - 8, 24, 8, STONE_D, DARK_WATER, DARK_WATER[4])
    for (x, y) in ((cx - 14, bottom - 8), (cx + 12, bottom - 6), (cx + 2, bottom - 4)):
        s.fill(s.ellipse(x, y, 3.4, 1.6), LEAF[2])
        s.fill(s.ellipse(x + 1, y - 1, 1.5, 1.5), VOIDC[3], glow=True)
    for x in (cx - 17, cx + 11):
        course_wall(s, x + 3, bottom - 10, 7, 6, 36, STONE_D, row_h=6, seed=x, moss_rows=3)
    top = bottom - 50
    s.part(s.poly([(cx - 18, top + 6), (cx - 18, top), (cx - 9, top - 8), (cx + 11, top - 8), (cx + 20, top), (cx + 20, top + 6),
                   (cx + 14, top + 6), (cx + 9, top), (cx - 7, top), (cx - 12, top + 6)]), STONE_D, flat=True)
    for k, x in enumerate(range(cx - 18, cx + 20, 3)):
        L = 4 + (k * 7) % 9
        s.line(x, top - 4, x, top + L, LEAF[2 + k % 2])
    orb(s, cx + 1, bottom - 30, 5, VOIDC)
    s.ink()
    return s, meta_for(s, "void", bottom - 30, energy=0.9, rng=110, height=36)


@tower
def triple_mire_colossus():
    """Mire Colossus (nature, water, earth): the head and shoulders of a mossy stone giant rising from a bog."""
    s = Sprite(56, 86)
    cx, bottom = 27, 82
    pool_top(s, cx + 1, bottom - 6, 26, 7, MUD, BOGW, BOGW[4])
    for (x, y, w, h) in ((cx - 24, bottom - 26, 13, 18), (cx + 12, bottom - 28, 13, 20)):
        block(s, x, y, x + w, y + h, STONE_D, depth=3, chips=3, seed=x * 7, moss=6)
    block(s, cx - 13, bottom - 34, cx + 13, bottom - 8, STONE, depth=4, chips=4, seed=2101, moss=8)
    block(s, cx - 9, bottom - 58, cx + 9, bottom - 34, STONE, depth=4, chips=3, seed=2102, moss=5)
    s.fill(s.rect(cx - 6, bottom - 50, cx - 2, bottom - 47), BOGW[3], glow=True)
    s.fill(s.rect(cx + 2, bottom - 50, cx + 6, bottom - 47), BOGW[3], glow=True)
    s.line(cx - 4, bottom - 40, cx + 4, bottom - 40, STONE[0])
    for x in range(cx - 9, cx + 9, 2):
        s.px(x, bottom - 58, MOSS[3])
        s.px(x + 1, bottom - 59, MOSS[2])
    s.fill(s.rect(cx - 13, bottom - 12, cx + 13, bottom - 8), BOGW[1])
    s.ink()
    return s, meta_for(s, "earth", bottom - 48, energy=0.9, rng=110, height=36)


@tower
def triple_tombroot():
    """Tombroot (nature, earth, void): a mausoleum split open by a tree's roots, violet light in its doorway."""
    s = Sprite(54, 96)
    cx, bottom = 26, 92
    plinth(s, cx, bottom, 44, 6, STONE_D, seed=2200)
    course_wall(s, cx, bottom - 6, 34, 32, 24, STONE_D, row_h=6, seed=2201, moss_rows=2)
    s.fill(s.poly([(cx - 5, bottom - 6), (cx - 5, bottom - 20), (cx, bottom - 25), (cx + 5, bottom - 20), (cx + 5, bottom - 6)]), INK)
    s.fill(s.poly([(cx - 3, bottom - 6), (cx - 3, bottom - 19), (cx, bottom - 22), (cx + 3, bottom - 19), (cx + 3, bottom - 6)]), VOIDC[1], glow=True)
    top = bottom - 30
    s.part(s.poly([(cx - 20, top), (cx + 22, top), (cx + 1, top - 10)]), STONE, flat=True)
    trunk(s, cx + 1, top - 2, top - 26, 5, ramp("6a6a5a", spread=0.45), ramp("4e4e42", spread=0.4))
    for (x0, y0, x1, y1) in ((cx - 2, top, cx - 14, bottom - 10), (cx + 4, top, cx + 16, bottom - 12), (cx, top + 2, cx - 6, bottom - 18)):
        s.part(s.capsule(x0, y0, x1, y1, 2.0, 1.4), ramp("6a6a5a", spread=0.45))
    leaf_crown(s, cx + 1, top - 36, 40, 18, [hexc(c) for c in ("2a3a2a", "3a4e36", "4e6444", "687c56", "8a9a70")],
               [hexc(c) for c in ("1a261c", "2a3a2a", "3a4e36", "4e6444", "687c56")], seed=35)
    s.ink()
    for (x, y) in ((cx - 9, top - 34), (cx + 9, top - 38)):
        s.px(x, y, VOIDC[3], glow=True)
    return s, meta_for(s, "nature", top - 30, light_y=bottom - 14, energy=0.9, rng=110, height=40, emitter="void")


@tower
def triple_boiling_marsh():
    """Boiling Marsh (fire, nature, water): an iron cauldron the size of a hut, bubbling green over a fire, reeds round."""
    s = Sprite(54, 84)
    cx, bottom = 26, 80
    pool_top(s, cx + 1, bottom - 5, 25, 6, MUD, BOGW, BOGW[4])
    for x in (cx - 12, cx + 12):
        s.part(s.rect(x - 1, bottom - 26, x + 2, bottom - 4), IRON, flat=True)
    flame(s, cx + 1, bottom - 8, 24, 12, seed=36)
    s.part(s.ellipse(cx + 1, bottom - 26, 17, 13) & (s.ys > bottom - 33), IRON)
    s.fill(s.ellipse(cx + 1, bottom - 33, 17, 4), IRON[3])
    s.fill(s.ellipse(cx + 1, bottom - 32.5, 14.5, 3), BOGW[2], glow=True)
    s.fill(s.ellipse(cx - 2, bottom - 33, 8, 1.6), BOGW[3], glow=True)
    for x in range(int(cx - 22), int(cx + 24), 5):
        s.line(x, bottom - 2, x + (1 if x % 2 else -1), bottom - 12 - (x * 3) % 6, LEAF[2])
        s.px(x + (1 if x % 2 else -1), bottom - 13 - (x * 3) % 6, ramp("7a5a30")[3])
    s.ink()
    for (x, y, r) in ((cx - 4, bottom - 42, 3), (cx + 5, bottom - 48, 2.5), (cx, bottom - 56, 2)):
        s.fill(s.ellipse(x, y, r, r), BOGW[3], glow=True)
        s.px(x - r * 0.4, y - r * 0.4, BOGW[4], glow=True)
    return s, meta_for(s, "nature", bottom - 40, light_y=bottom - 14, energy=1.1, rng=115, height=36)


@tower
def triple_abyssal_trench():
    """Abyssal Trench (water, earth, void): two cliffs of sandstone with the sea pouring between them into the dark."""
    s = Sprite(56, 90)
    cx, bottom = 27, 86
    for (x0, x1, top, seed) in ((cx - 25, cx - 5, bottom - 56, 2301), (cx + 5, cx + 26, bottom - 48, 2302)):
        rows = 4
        for r in range(rows):
            y1 = bottom - r * (bottom - top) / rows
            y0 = y1 - (bottom - top) / rows
            block(s, x0 + r, round(y0), x1 - r, round(y1), SAND, depth=3, top=(r == rows - 1), chips=2, seed=seed + r, strata=4)
    s.fill(s.rect(cx - 4, bottom - 46, cx + 5, bottom - 6), DARK_WATER[3], glow=True)
    s.fill(s.rect(cx - 2, bottom - 46, cx + 2, bottom - 6), DARK_WATER[4], glow=True)
    s.fill(s.ellipse(cx + 0.5, bottom - 5, 9, 3), (10, 6, 18))
    s.fill(s.ellipse(cx + 0.5, bottom - 5, 5, 1.5), VOIDC[2], glow=True)
    s.ink()
    for (x, y, r) in ((cx - 3, bottom - 48, 3), (cx + 4, bottom - 50, 3), (cx, bottom - 53, 2.5)):
        s.fill(s.ellipse(x, y, r, r * 0.7), STEAM[2])
    return s, meta_for(s, "water", bottom - 30, energy=0.9, rng=110, height=36)
