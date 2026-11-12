"""Towers in the hand-drawn 2D style (same kit, light and outline as the creatures).

Each tower function returns (sprite, meta). The sprite's front-bottom point (where it stands on its cell) is at
(w / 2, h - 4). meta gives the game what gen_game_art used to: muzzle, light and emitter, in pixels from that point.
Stone is chiselled blocks (`block`), never round domes; element pieces (flame, bolt, orb, leaves) glow.
"""
from __future__ import annotations

import math

import numpy as np

from kit import INK, Sprite, hexc, ramp
from creatures import STONE, STONE_D, IRON, WOOD, GOLD, MOSS, LEATHER, RED, RED_D

STONE_W = ramp("968e7e", spread=0.5, shift=0.02)       # pale ashlar
SLATE = ramp("5c6474", spread=0.5, shift=0.0)
BASALT = ramp("4a4044", spread=0.45, shift=0.02)
OBSID = ramp("2e2638", spread=0.45, shift=0.0)
SAND = ramp("b08a5c", spread=0.5)
BARK = ramp("6a4a30", spread=0.5)
BARK_D = ramp("4e3626", spread=0.45)
LEAF = ramp("4f8a34", spread=0.55)
LEAF_D = ramp("2f5e2a", spread=0.5)
COPPER = ramp("c07a3a", spread=0.55)
MARBLE = ramp("c8c4ba", spread=0.45, shift=0.02)
CLOTH_R = ramp("a8282e", spread=0.5)
CLOTH_B = ramp("2e4c9a", spread=0.5)
CLOTH_V = ramp("5a2a8a", spread=0.5)

FIRE = [hexc(c) for c in ("8a1e10", "d8481a", "ff8a2a", "ffc85a", "fff2c0")]
BOLT = [hexc(c) for c in ("3a4ab0", "6a86f0", "a8c4ff", "e4f0ff", "ffffff")]
AQUA = [hexc(c) for c in ("12406e", "1f6fa8", "3aa0d8", "7ad0f0", "d4f6ff")]
SAP = [hexc(c) for c in ("2a6a1a", "58b03a", "9ae04a", "d8ff8a", "f6ffd8")]
AMBER = [hexc(c) for c in ("7a3e10", "c06a1a", "f0a030", "ffd070", "fff2c0")]
VOIDC = [hexc(c) for c in ("2a1048", "5a2a98", "8e5cd9", "c8a0ff", "f4e8ff")]

ELEMENT_GLOW = {"fire": FIRE, "storm": BOLT, "water": AQUA, "nature": SAP, "earth": AMBER, "void": VOIDC}
ELEMENT_LIGHT = {"fire": "#ff9a48", "storm": "#ffe27a", "nature": "#9ae04a", "water": "#6ac8ff", "earth": "#ffb04a",
                 "void": "#a070ff"}
ELEMENT_EMITTER = {"fire": "fire", "storm": "sparks", "nature": "leaves", "water": "drips", "earth": "dust", "void": "void"}


# ------------------------------------------------------------------------------------------------ helpers
def block(s, x0, y0, x1, y1, tones, depth=2, top=True, side=True, chips=0, seed=0, moss=0, strata=0):
    """One chiselled block seen from the front and a little above: lit top strip, flat face, dark right side."""
    rng = np.random.default_rng(seed)
    if top and depth:
        s.fill(s.poly([(x0, y0), (x1, y0), (x1 + depth, y0 - depth), (x0 + depth, y0 - depth)]), tones[4])
    if side and depth:
        s.fill(s.poly([(x1, y0), (x1 + depth, y0 - depth), (x1 + depth, y1 - depth), (x1, y1)]), tones[1])
    face = s.rect(x0, y0, x1, y1)
    s.fill(face, tones[2])
    up = face & ~np.roll(face, 1, 0)
    left = face & ~np.roll(face, 1, 1)
    down = face & ~np.roll(face, -1, 0)
    right = face & ~np.roll(face, -1, 1)
    s.rgb[up | left] = tones[3]
    s.rgb[down | right] = tones[1]
    s.nrm[face] = (0.0, 0.25, 0.97)
    if strata:                                                   # sandstone layers: broken dark lines, a lit lip
        for y in range(int(y0) + strata, int(y1) - 1, strata):
            for x in range(int(x0) + 1, int(x1) - 1):
                if rng.random() < 0.82:
                    s.px(x, y, tones[1])
                    if rng.random() < 0.5:
                        s.px(x, y - 1, tones[3])
    for _ in range(chips):
        x = int(rng.integers(int(x0) + 1, max(int(x0) + 2, int(x1) - 1)))
        y = int(rng.integers(int(y0) + 1, max(int(y0) + 2, int(y1) - 1)))
        s.px(x, y, tones[1])
        s.px(x - 1, y, tones[3])
    for _ in range(moss):
        x = int(rng.integers(int(x0), int(x1)))
        y = int(y1) - 1 - int(rng.integers(0, 2))
        s.px(x, y, MOSS[int(rng.integers(1, 4))])
    return face


def course_wall(s, cx, bottom, w_bot, w_top, height, tones, row_h=5, seed=0, moss_rows=1, depth=2):
    """A square tapered wall of staggered chiselled blocks, rows drawn top to bottom so lower rows overlap."""
    rows = max(1, int(round(height / row_h)))
    rng = np.random.default_rng(seed)
    out = []
    for r in reversed(range(rows)):
        y1 = bottom - r * row_h
        y0 = y1 - row_h
        t = (r + 0.5) / rows
        half = (w_bot + (w_top - w_bot) * t) / 2
        x_left, x_right = cx - half, cx + half
        n = max(2, int(round(2 * half / 7)))
        cuts = [x_left + (x_right - x_left) * k / n for k in range(n + 1)]
        if r % 2:
            cuts = [cuts[0]] + [c + (x_right - x_left) / n / 2 for c in cuts[1:-1]] + [cuts[-1]]
        for k in range(len(cuts) - 1):
            a, b = round(cuts[k]), round(cuts[k + 1])
            last = k == len(cuts) - 2
            block(s, a, y0, b, y1, tones, depth=depth if last else 0, top=(r == rows - 1), side=last,
                  chips=1 if rng.random() < 0.5 else 0, seed=seed * 31 + r * 7 + k,
                  moss=(2 if r < moss_rows else 0))
        if r == rows - 1 and depth:
            s.fill(s.poly([(x_left, y0), (x_right, y0), (x_right + depth, y0 - depth), (x_left + depth, y0 - depth)]),
                   tones[4])
        out.append((x_left, x_right, y0, y1))
    return out


def plinth(s, cx, bottom, w, h, tones, seed=0, depth=4):
    """A broad low step of big stones the tower stands on, with its lit top showing."""
    x0, x1 = cx - w / 2, cx + w / 2
    s.fill(s.poly([(x0, bottom - h), (x1, bottom - h), (x1 + depth, bottom - h - depth), (x0 + depth, bottom - h - depth)]),
           tones[3])
    n = max(2, int(round(w / 9)))
    for k in range(n):
        a = round(x0 + w * k / n)
        b = round(x0 + w * (k + 1) / n)
        block(s, a, bottom - h, b, bottom, tones, depth=depth if k == n - 1 else 0, top=False, side=k == n - 1,
              chips=1, seed=seed + k, moss=2)


def flame(s, cx, base, w, h, seed=0, tones=FIRE):
    """A tall fire: dark outer tongues, an orange body, a yellow heart. All glowing, no shading."""
    rng = np.random.default_rng(seed)
    layers = [(1.0, 1.0, tones[1]), (0.72, 0.78, tones[2]), (0.45, 0.55, tones[3]), (0.2, 0.3, tones[4])]
    for sw, sh, col in layers:
        ww, hh = w * sw, h * sh
        pts = [(cx - ww / 2, base)]
        tips = 3 if sw > 0.5 else 2 if sw > 0.3 else 1
        for t in range(tips):
            u = (t + 0.5) / tips
            tx = cx - ww / 2 + ww * u + rng.uniform(-1, 1)
            th = hh * (1.0 if abs(u - 0.5) < 0.2 else 0.7) + rng.uniform(-1.5, 1.5)
            pts.append((tx - ww / tips * 0.35, base - th * 0.5))
            pts.append((tx, base - th))
            pts.append((tx + ww / tips * 0.35, base - th * 0.5))
        pts.append((cx + ww / 2, base))
        pts.append((cx, base + 2))
        s.fill(s.poly(pts), col, glow=True)
    s.fill(s.poly([(cx - w / 2 + 1, base - 1), (cx + w / 2 - 1, base - 1), (cx + w / 2 - 2, base + 1), (cx - w / 2 + 2, base + 1)]),
           tones[2], glow=True)


def orb(s, cx, cy, r, tones, rim=None):
    """A glowing sphere: rim tone, body, a bright crescent at the upper left and a white shine."""
    s.fill(s.ellipse(cx, cy, r, r), tones[1], glow=True)
    s.fill(s.ellipse(cx - r * 0.12, cy - r * 0.12, r * 0.8, r * 0.8), tones[2], glow=True)
    s.fill(s.ellipse(cx - r * 0.25, cy - r * 0.25, r * 0.5, r * 0.5), tones[3], glow=True)
    s.fill(s.ellipse(cx - r * 0.38, cy - r * 0.42, max(0.8, r * 0.2), max(0.8, r * 0.2)), tones[4], glow=True)


def glow_image(s):
    """The pixels the game adds on top, unlit, so they shine at night. Dimmer tones are added at half strength so a
    big glowing area (a crystal, a column of water) does not wash out to white; the hot cores stay full."""
    from PIL import Image
    a = (s.glow & s.a).astype(np.uint8) * 255
    rgb = s.rgb.astype(np.float32)
    lum = rgb @ np.array([0.3, 0.55, 0.15], np.float32)
    k = np.where(lum > 175, 0.95, 0.5)[..., None]
    return Image.fromarray(np.dstack([np.clip(rgb * k, 0, 255).astype(np.uint8), a]), "RGBA")


def meta_for(s, element, muzzle_y, light_y=None, energy=1.0, rng=110, height=40, muzzle_x=0, emitter=None):
    ax, ay = s.w // 2, s.h - 4
    return {
        "size": [s.w, s.h], "anchor": [ax, ay], "muzzle": [muzzle_x, muzzle_y - ay],
        "light": {"color": ELEMENT_LIGHT[element], "offset": [muzzle_x, (light_y if light_y is not None else muzzle_y) - ay],
                  "energy": energy, "range": rng, "height": height},
        "emitter": emitter or ELEMENT_EMITTER[element], "emitter_offset": [muzzle_x, muzzle_y - ay],
    }


TOWERS = {}


def tower(fn):
    TOWERS[fn.__name__] = fn
    return fn


# ------------------------------------------------------------------------------------------------ base towers
@tower
def fire_brazier():
    """Pyre: a squat watchtower of soot-dark ashlar, a red war banner, an iron fire basket roaring on top."""
    s = Sprite(40, 80)
    cx, bottom = 19, 76
    plinth(s, cx, bottom, 32, 6, BASALT, seed=1)
    course_wall(s, cx, bottom - 6, 24, 20, 30, STONE_D, row_h=6, seed=2, moss_rows=1)
    top = bottom - 36
    # corbelled crown: a wider course of blocks with crenels
    for k, (a, b) in enumerate([(cx - 13, cx - 7), (cx - 5, cx + 1), (cx + 3, cx + 9)]):
        block(s, a, top - 7, b, top - 2, STONE, depth=2, side=(k == 2), seed=10 + k)
    block(s, cx - 13, top - 2, cx + 11, top + 1, STONE, depth=0, seed=14)
    for x in range(int(cx - 12), int(cx + 11), 3):
        s.px(x, top + 1, STONE[0])
    # arrow slit with firelight inside
    s.fill(s.rect(cx - 1, bottom - 26, cx + 1, bottom - 17), INK)
    s.fill(s.rect(cx - 1, bottom - 24, cx + 1, bottom - 19), FIRE[2], glow=True)
    # red banner hanging from the crown, an ember sigil
    s.part(s.poly([(cx - 9, top + 1), (cx - 3, top + 1), (cx - 3, top + 16), (cx - 6, top + 13), (cx - 9, top + 16)]),
           CLOTH_R, flat=True)
    s.pxs([(cx - 6, top + 5), (cx - 7, top + 6), (cx - 5, top + 6), (cx - 6, top + 7), (cx - 6, top + 8)], GOLD[3])
    s.line(cx - 9, top + 1, cx - 3, top + 1, IRON[1])
    # iron basket: three legs, a riveted bowl
    bowl = top - 12
    for lx in (-6, 0, 6):
        s.line(cx + lx * 0.6, bowl + 3, cx + lx, top - 7, IRON[1] if lx > 0 else IRON[2])
    s.part(s.poly([(cx - 9, bowl - 1), (cx + 9, bowl - 1), (cx + 6, bowl + 5), (cx - 6, bowl + 5)]), IRON)
    s.line(cx - 9, bowl - 1, cx + 9, bowl - 1, IRON[4])
    s.pxs([(cx - 5, bowl + 2), (cx, bowl + 3), (cx + 5, bowl + 2)], IRON[0])
    s.fill(s.ellipse(cx, bowl - 1, 8, 1.6), FIRE[1], glow=True)
    flame(s, cx, bowl - 1, 16, 22, seed=3)
    s.ink()
    s.pxs([(cx - 3, bowl - 26), (cx + 4, bowl - 22), (cx + 7, bowl - 28)], FIRE[3], glow=True)   # rising embers
    return s, meta_for(s, "fire", bowl - 8, energy=1.25, rng=125, height=44)


@tower
def storm_spire():
    """Tempest: a slate needle bound with copper bands, a copper rod coil and a crackling blue crystal on top."""
    s = Sprite(36, 84)
    cx, bottom = 17, 80
    plinth(s, cx, bottom, 28, 5, SLATE, seed=4)
    course_wall(s, cx, bottom - 5, 18, 12, 36, SLATE, row_h=6, seed=5, moss_rows=1)
    top = bottom - 41
    for y in (bottom - 17, bottom - 33):                      # copper bands
        w = 9.5 - (bottom - 5 - y) / 36 * 3
        s.part(s.rect(cx - w, y - 2, cx + w + 1, y), COPPER, flat=True)
        s.px(cx - w + 1, y - 1, COPPER[4])
    # a pointed slate cap
    s.part(s.poly([(cx - 8, top), (cx + 9, top), (cx + 1, top - 9)]), SLATE, flat=True)
    s.line(cx + 1, top - 9, cx - 7, top - 1, SLATE[4])
    # copper rod with a coil
    s.part(s.rect(cx, top - 24, cx + 2, top - 8), COPPER, flat=True)
    for k in range(4):
        y = top - 11 - k * 3
        s.line(cx - 3, y, cx + 4, y - 1, COPPER[3] if k % 2 else COPPER[2])
    # crystal: three shards of blue, glowing
    s.fill(s.poly([(cx + 1, top - 38), (cx + 5, top - 29), (cx + 1, top - 22), (cx - 3, top - 29)]), BOLT[2], glow=True)
    s.fill(s.poly([(cx + 1, top - 38), (cx + 5, top - 29), (cx + 1, top - 26)]), BOLT[3], glow=True)
    s.fill(s.poly([(cx - 3, top - 29), (cx - 6, top - 33), (cx - 3, top - 25)]), BOLT[1], glow=True)
    s.fill(s.poly([(cx + 5, top - 29), (cx + 8, top - 34), (cx + 4, top - 25)]), BOLT[2], glow=True)
    s.ink()
    # sparks jumping from the crystal to the coil
    s.pxs([(cx - 5, top - 22), (cx - 6, top - 20), (cx - 5, top - 18), (cx + 6, top - 21), (cx + 7, top - 19)], BOLT[4], glow=True)
    return s, meta_for(s, "storm", top - 30, energy=1.0, rng=105, height=48)


@tower
def nature_thornbush():
    """Strangler: a living tower, a gnarled trunk grown out of a ring of standing stones, thorn vines, a glowing seed."""
    s = Sprite(42, 80)
    cx, bottom = 20, 76
    # roots spreading over old stones
    for a, b, c in ((cx - 14, bottom - 7, cx - 7), (cx + 6, bottom - 7, cx + 13)):
        block(s, a, b, c, bottom, STONE_D, depth=2, seed=a, moss=4)
    for pts in ([(cx - 3, bottom - 14), (cx - 15, bottom - 2), (cx - 11, bottom), (cx, bottom - 6)],
                [(cx + 3, bottom - 14), (cx + 16, bottom - 1), (cx + 12, bottom + 1), (cx, bottom - 6)]):
        s.part(s.poly(pts), BARK_D)
    # twisted trunk: two strands winding up
    s.part(s.poly([(cx - 7, bottom - 2), (cx - 4, bottom - 20), (cx - 6, bottom - 34), (cx - 1, bottom - 46),
                   (cx + 3, bottom - 44), (cx, bottom - 32), (cx + 2, bottom - 18), (cx + 1, bottom - 2)]), BARK_D, bias=-0.1)
    s.part(s.poly([(cx - 1, bottom - 2), (cx + 3, bottom - 16), (cx + 1, bottom - 28), (cx + 5, bottom - 42),
                   (cx + 9, bottom - 40), (cx + 6, bottom - 28), (cx + 8, bottom - 14), (cx + 7, bottom - 1)]), BARK)
    for y in range(bottom - 40, bottom - 4, 5):                # bark grain
        s.px(cx + 4 + (y % 3) - 1, y, BARK[1])
    # thorn vines wrapping it
    for k, y in enumerate(range(bottom - 38, bottom - 6, 8)):
        s.line(cx - 6, y + 3, cx + 8, y, LEAF_D[1])
        s.pxs([(cx - 7 + k % 2, y + 2), (cx + 9, y - 1)], BONE_THORN)
    # crown of leaves in lumps, back to front
    for (x, y, rx, ry, t, b) in ((cx - 9, bottom - 50, 9, 7, LEAF_D, -0.1), (cx + 9, bottom - 51, 9, 7, LEAF_D, -0.1),
                                 (cx, bottom - 58, 11, 8, LEAF, 0.0), (cx - 8, bottom - 44, 7, 5, LEAF, 0.0),
                                 (cx + 9, bottom - 44, 7, 5, LEAF, -0.05), (cx + 1, bottom - 47, 8, 6, LEAF, 0.1)):
        s.part(s.ellipse(x, y, rx, ry), t, bias=b)
    rng = np.random.default_rng(6)
    for _ in range(26):                                        # leaf flecks
        x, y = int(rng.integers(cx - 15, cx + 15)), int(rng.integers(bottom - 64, bottom - 40))
        if s.a[y, x]:
            s.px(x, y, LEAF[4] if y < bottom - 54 else LEAF[3])
    # thorns poking out of the crown
    for (x, y, dx, dy) in ((cx - 17, bottom - 50, -2, -1), (cx + 18, bottom - 52, 2, -1), (cx - 4, bottom - 66, -1, -2),
                           (cx + 7, bottom - 64, 1, -2)):
        s.line(x, y, x + dx, y + dy, BONE_THORN)
    # the seed pod hanging under the crown, glowing green
    s.line(cx + 1, bottom - 42, cx + 1, bottom - 38, BARK_D[2])
    orb(s, cx + 1, bottom - 34, 3.6, SAP)
    s.ink()
    return s, meta_for(s, "nature", bottom - 34, light_y=bottom - 36, energy=0.8, rng=95, height=34)


BONE_THORN = hexc("e6dcc0")


@tower
def water_wellspring():
    """Tidecaller: a round-arched well-shrine of pale stone, a basin brimming over, a water orb held in a bronze ring."""
    s = Sprite(42, 76)
    cx, bottom = 20, 72
    # basin: a low wall of blocks, water surface seen from above, spilling over the lip
    s.fill(s.ellipse(cx + 1, bottom - 11, 18, 6), STONE[3])
    s.fill(s.ellipse(cx + 1, bottom - 11, 15.5, 4.5), AQUA[1], glow=False)
    s.fill(s.ellipse(cx, bottom - 12, 12, 3), AQUA[2])
    s.pxs([(cx - 7, bottom - 12), (cx - 6, bottom - 12), (cx + 4, bottom - 10), (cx + 5, bottom - 10), (cx - 1, bottom - 13)],
          AQUA[4], glow=True)
    for k, x in enumerate(range(cx - 17, cx + 19, 6)):
        block(s, x, bottom - 9, min(x + 6, cx + 19), bottom, STONE, depth=0, seed=20 + k, moss=1)
    s.fill(s.rect(cx - 17, bottom - 10, cx + 19, bottom - 8), STONE[4])
    for x in (cx - 10, cx + 9):                                 # water spilling over
        s.fill(s.rect(x, bottom - 9, x + 2, bottom - 2), AQUA[3], glow=True)
        s.px(x, bottom - 2, AQUA[4], glow=True)
    # two pillars and an arch
    for x in (cx - 13, cx + 9):
        course_wall(s, x + 2.5, bottom - 11, 6, 6, 30, STONE, row_h=5, seed=x, moss_rows=1, depth=2)
    arch_top = bottom - 41
    s.part(s.poly([(cx - 14, arch_top + 6), (cx - 14, arch_top), (cx - 8, arch_top - 6), (cx + 10, arch_top - 6),
                   (cx + 16, arch_top), (cx + 16, arch_top + 6), (cx + 12, arch_top + 6), (cx + 8, arch_top + 1),
                   (cx - 6, arch_top + 1), (cx - 10, arch_top + 6)]), STONE, flat=True)
    s.line(cx - 7, arch_top - 6, cx + 9, arch_top - 6, STONE[4])
    s.part(s.poly([(cx - 2, arch_top - 6), (cx + 4, arch_top - 6), (cx + 3, arch_top - 1), (cx - 1, arch_top - 1)]), STONE)  # keystone
    # bronze ring and the floating orb of water inside the arch
    oy = bottom - 26
    s.fill(s.ellipse(cx + 1, oy, 7, 7) & ~s.ellipse(cx + 1, oy, 5.6, 5.6), COPPER[2])
    s.pxs([(cx - 4, oy - 4), (cx - 5, oy - 2)], COPPER[4])
    orb(s, cx + 1, oy, 4.8, AQUA)
    s.line(cx + 1, oy + 7, cx + 1, bottom - 13, AQUA[3], glow=True)            # a thin stream falling into the basin
    s.ink()
    s.pxs([(cx - 4, oy - 9), (cx + 6, oy - 8)], AQUA[4], glow=True)
    return s, meta_for(s, "water", oy, energy=0.9, rng=100, height=36)


@tower
def earth_monolith():
    """Earthshaker: a cairn of huge chiselled sandstone blocks cut with amber runes, a boulder floating over it."""
    s = Sprite(40, 80)
    cx, bottom = 19, 76
    plinth(s, cx, bottom, 34, 6, STONE_D, seed=30)
    block(s, cx - 13, bottom - 20, cx + 11, bottom - 6, SAND, depth=4, chips=4, seed=31, moss=3, strata=4)
    block(s, cx - 10, bottom - 34, cx + 8, bottom - 20, SAND, depth=4, chips=3, seed=32, strata=5)
    block(s, cx - 7, bottom - 44, cx + 5, bottom - 34, SAND, depth=3, chips=2, seed=33, strata=4)
    # amber runes carved into the faces
    for (x, y) in ((cx - 7, bottom - 17), (cx + 2, bottom - 16)):
        s.line(x, y, x, y + 7, AMBER[3], glow=True)
        s.line(x, y + 2, x + 3, y, AMBER[3], glow=True)
        s.line(x, y + 4, x + 3, y + 6, AMBER[2], glow=True)
    s.line(cx - 2, bottom - 31, cx - 2, bottom - 24, AMBER[3], glow=True)
    s.line(cx - 4, bottom - 28, cx, bottom - 28, AMBER[3], glow=True)
    # the floating boulder: an angular chunk, lit top, with an amber seam
    by = bottom - 58
    s.fill(s.poly([(cx - 7, by + 2), (cx - 5, by - 5), (cx + 2, by - 7), (cx + 8, by - 3), (cx + 8, by + 4), (cx + 2, by + 7),
                   (cx - 5, by + 6)]), SAND[2])
    s.fill(s.poly([(cx - 5, by - 5), (cx + 2, by - 7), (cx + 8, by - 3), (cx + 1, by - 1), (cx - 6, by)]), SAND[4])
    s.fill(s.poly([(cx + 8, by - 3), (cx + 8, by + 4), (cx + 2, by + 7), (cx + 2, by + 1)]), SAND[1])
    s.line(cx - 4, by + 3, cx + 1, by + 1, AMBER[3], glow=True)
    s.line(cx + 1, by + 1, cx + 2, by + 5, AMBER[3], glow=True)
    # pebbles drifting up around it
    for (x, y) in ((cx - 11, by + 8), (cx + 12, by + 2), (cx - 9, by - 6)):
        s.fill(s.rect(x, y, x + 2, y + 2), SAND[3])
    s.ink()
    s.pxs([(cx - 2, by + 13), (cx + 1, by + 15), (cx - 1, by + 17)], AMBER[3], glow=True)   # glow dust below
    return s, meta_for(s, "earth", by, light_y=bottom - 28, energy=0.75, rng=85, height=34)


@tower
def void_obelisk():
    """Dark Beacon: a black obsidian obelisk with violet runes, three standing shards, a slitted eye in a ring above."""
    s = Sprite(40, 84)
    cx, bottom = 19, 80
    plinth(s, cx, bottom, 30, 5, OBSID, seed=40)
    for x, h in ((cx - 13, 14), (cx + 10, 12)):                 # side shards
        s.part(s.poly([(x - 3, bottom - 5), (x + 3, bottom - 5), (x + 1, bottom - 5 - h), (x - 1, bottom - 4 - h)]), OBSID, flat=True)
    # the obelisk: front face, lit left bevel, dark right face
    top = bottom - 52
    s.fill(s.poly([(cx + 7, bottom - 5), (cx + 10, bottom - 8), (cx + 7, top + 3), (cx + 5, top + 1)]), OBSID[0])
    s.fill(s.poly([(cx - 7, bottom - 5), (cx + 7, bottom - 5), (cx + 5, top + 1), (cx - 5, top + 1)]), OBSID[2])
    s.fill(s.poly([(cx - 5, top + 1), (cx + 5, top + 1), (cx, top - 6)]), OBSID[3])
    s.line(cx - 7, bottom - 6, cx - 5, top + 1, OBSID[4])
    s.line(cx - 5, top + 1, cx, top - 6, OBSID[4])
    s.nrm[s.a] = (0.0, 0.2, 0.98)
    # runes down the face
    for k, y in enumerate(range(bottom - 46, bottom - 10, 7)):
        x = cx - 1
        if k % 2:
            s.pxs([(x, y), (x + 1, y + 1), (x, y + 2), (x - 1, y + 3), (x, y + 4)], VOIDC[3], glow=True)
        else:
            s.pxs([(x - 1, y), (x, y), (x + 1, y), (x, y + 1), (x, y + 2), (x - 1, y + 3), (x + 1, y + 3)], VOIDC[3], glow=True)
    # floating ring and eye
    ey = top - 16
    ring = s.ellipse(cx, ey, 9, 9) & ~s.ellipse(cx, ey, 7, 7)
    s.fill(ring, OBSID[3])
    s.fill(ring & (s.ys < ey - 3), OBSID[4])
    s.fill(s.ellipse(cx, ey, 6, 6), VOIDC[0], glow=True)
    s.fill(s.ellipse(cx, ey, 5, 3), VOIDC[3], glow=True)
    s.fill(s.ellipse(cx, ey, 1.2, 2.6), (14, 6, 24), glow=True)
    s.px(cx - 2, ey - 1, VOIDC[4], glow=True)
    s.ink()
    s.pxs([(cx - 11, ey + 6), (cx + 12, ey - 5), (cx - 9, ey - 9)], VOIDC[3], glow=True)
    return s, meta_for(s, "void", ey, energy=0.9, rng=100, height=44)


import towers_duals  # noqa: E402,F401  (registers the dual-element towers)
import towers_triples  # noqa: E402,F401  (registers the triple-element towers)
