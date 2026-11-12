"""Scenery props in the hand-drawn style: trees, bushes, chiselled rocks, stumps, logs, flowers, ferns and the
fire lands' dead trees and basalt. Each function returns a Sprite whose bottom row is where it stands.

make_all(folder) writes <kind>.png, <kind>_n.png (and <kind>_glow.png for glowing ones) and returns their art.json
entries: size, whether the sway shader moves them, whether they glow.
"""
from __future__ import annotations

import math
import os

import numpy as np

from kit import INK, Sprite, hexc, ramp
from towers import BARK, BARK_D, BASALT, FIRE, LEAF, LEAF_D, STONE_W, block, glow_image
from creatures import MOSS, STONE, STONE_D, BONE

LEAF_L = ramp("6a9a3a", spread=0.55)
PINE = ramp("2a5236", spread=0.5)
JUNGLE = ramp("2e6a2a", spread=0.55)
JUNGLE_D = ramp("1e4a22", spread=0.5)
BERRY = hexc("c02a3a")
CHAR = ramp("3e3432", spread=0.45)
FERN = ramp("4a8a30", spread=0.55)

PROPS = {}


def prop(sways=False, glow=False):
    def wrap(fn):
        PROPS[fn.__name__] = (fn, sways, glow)
        return fn
    return wrap


def canopy(s, lumps, tones, tones_d, rng, flecks=20):
    """A leafy crown from overlapping lumps: back ones darker, front ones lit, with leaf flecks on the light side."""
    for (x, y, rx, ry, back) in lumps:
        s.part(s.ellipse(x, y, rx, ry), tones_d if back else tones, bias=-0.1 if back else 0.0)
    ys, xs = np.nonzero(s.a)
    lit = {tuple(tones[3]), tuple(tones[4])}
    mid = {tuple(tones[2]), tuple(tones_d[3]), tuple(tones_d[2])}
    for _ in range(flecks * 3):
        k = int(rng.integers(0, len(xs)))
        x, y = xs[k], ys[k]
        if not (2 <= y < s.h - 2 and 2 <= x < s.w - 2) or not s.a[y - 2, x]:
            continue
        c = tuple(int(v) for v in s.rgb[y, x])
        if c in lit:                       # a leaf catching the light: a small bright chevron
            s.px(x, y, tones[4])
            s.px(x - 1, y + 1, tones[4])
            s.px(x + 1, y + 1, tones[3])
            s.px(x, y + 1, tones[2])
        elif c in mid:                     # a darker leaf shape in the shade
            s.px(x, y, tones[1])
            s.px(x + 1, y, tones[1])
            s.px(x, y - 1, tones[3] if c == tuple(tones[2]) else tones_d[3])


@prop(sways=True)
def oak_0():
    s = Sprite(40, 52)
    rng = np.random.default_rng(1)
    s.part(s.poly([(17, 51), (19, 34), (17, 26), (21, 30), (24, 25), (23, 34), (25, 51)]), BARK)
    s.part(s.poly([(15, 51), (19, 47), (20, 51)]), BARK_D)
    s.part(s.poly([(23, 51), (24, 47), (29, 51)]), BARK_D)
    canopy(s, [(12, 22, 9, 8, True), (28, 21, 10, 8, True), (20, 13, 11, 9, False), (11, 25, 8, 6, False),
               (28, 26, 9, 6, False), (20, 23, 9, 7, False)], LEAF, LEAF_D, rng)
    s.ink()
    return s


@prop(sways=True)
def oak_1():
    s = Sprite(34, 46)
    rng = np.random.default_rng(2)
    s.part(s.poly([(15, 45), (16, 30), (14, 22), (19, 27), (20, 45)]), BARK)
    s.part(s.poly([(13, 45), (16, 41), (17, 45)]), BARK_D)
    canopy(s, [(11, 18, 8, 7, True), (23, 17, 8, 7, True), (17, 11, 9, 8, False), (17, 21, 9, 6, False)],
           LEAF_L, LEAF, rng)
    s.ink()
    return s


@prop(sways=True)
def pine_0():
    s = Sprite(26, 52)
    s.part(s.rect(12, 42, 15, 52), BARK)
    for k, (y, w) in enumerate(((44, 12), (36, 10), (28, 8), (20, 6), (12, 4))):
        s.part(s.poly([(13 - w, y), (13 + w, y), (16 + w * 0.3, y - 3), (13, y - 11), (10 - w * 0.3, y - 3)]), PINE,
               bias=-0.05 * k)
        s.line(13 - w + 1, y, 13 + w - 1, y, PINE[0])
    s.ink()
    return s


@prop(sways=True)
def jungle_0():
    """A broad jungle tree: pale buttress roots, hanging vines, a heavy dark crown."""
    s = Sprite(44, 54)
    rng = np.random.default_rng(3)
    trunk = ramp("8a7a60", spread=0.5)
    s.part(s.poly([(18, 53), (20, 30), (24, 30), (27, 53)]), trunk)
    s.part(s.poly([(12, 53), (20, 42), (21, 53)]), trunk, bias=-0.1)
    s.part(s.poly([(25, 53), (24, 42), (33, 53)]), trunk, bias=-0.1)
    canopy(s, [(12, 20, 11, 8, True), (32, 20, 11, 8, True), (22, 12, 13, 9, False), (10, 26, 9, 6, False),
               (34, 26, 9, 6, False), (22, 25, 11, 7, False)], JUNGLE, JUNGLE_D, rng, flecks=26)
    for x in (9, 16, 30, 36):                                    # vines
        L = int(rng.integers(6, 14))
        s.line(x, 28, x + (1 if x > 22 else -1), 28 + L, JUNGLE[1])
        s.px(x, 28 + L, JUNGLE[3])
    s.ink()
    return s


@prop(sways=True)
def jungle_1():
    """A palm-like tree with drooping fronds."""
    s = Sprite(40, 50)
    trunk = ramp("7a6040", spread=0.5)
    for k in range(9):
        y = 49 - k * 3.5
        x = 19 + math.sin(k * 0.4) * 2
        s.part(s.ellipse(x, y, 2.6, 2.0), trunk)
    top = (21, 18)
    for ang, L in ((-2.7, 16), (-2.1, 15), (-1.4, 12), (-0.6, 15), (-0.1, 17), (0.5, 14), (2.6, 13)):
        x1, y1 = top[0] + math.cos(ang) * L, top[1] + math.sin(ang) * L * 0.55 + 6
        mx, my = (top[0] + x1) / 2, (top[1] + y1) / 2 - 4
        s.part(s.poly([top, (mx, my - 2), (x1, y1), (mx, my + 2)]), FERN)
        s.line(top[0], top[1], x1, y1, FERN[1])
    s.fill(s.ellipse(21, 19, 2, 2), ramp("a8783c")[2])
    s.ink()
    return s


@prop(sways=True)
def bush_round():
    s = Sprite(20, 14)
    rng = np.random.default_rng(4)
    canopy(s, [(6, 9, 6, 4.5, True), (14, 9, 6, 4.5, True), (10, 7, 7, 5, False)], LEAF, LEAF_D, rng, flecks=8)
    s.ink()
    return s


@prop(sways=True)
def bush_berry():
    s = Sprite(18, 13)
    rng = np.random.default_rng(5)
    canopy(s, [(5, 8, 5, 4, True), (12, 8, 5, 4, True), (9, 6, 6, 4.5, False)], LEAF_L, LEAF, rng, flecks=6)
    for (x, y) in ((5, 6), (11, 5), (8, 9), (13, 8), (7, 4)):
        s.px(x, y, BERRY)
        s.px(x, y - 1, (240, 120, 120))
    s.ink()
    return s


def _rock(w, h, tones, seed, moss=0):
    s = Sprite(w, h)
    rng = np.random.default_rng(seed)
    # two or three chiselled faces: lit top, front, dark side
    top = h * 0.45
    s.fill(s.poly([(1, h - 1), (1, top), (w * 0.3, 1), (w * 0.75, 1), (w - 1, top), (w - 1, h - 1)]), tones[2])
    s.fill(s.poly([(1, top), (w * 0.3, 1), (w * 0.75, 1), (w * 0.55, top + 1)]), tones[4])
    s.fill(s.poly([(w * 0.75, 1), (w - 1, top), (w - 1, h - 1), (w * 0.6, h - 1), (w * 0.55, top + 1)]), tones[1])
    s.line(1, top, w * 0.55, top + 1, tones[3])
    for _ in range(max(1, w // 6)):
        x, y = int(rng.integers(2, w - 3)), int(rng.integers(int(top) + 2, h - 1))
        s.px(x, y, tones[0])
    for _ in range(moss):
        x = int(rng.integers(1, w - 1))
        ys = np.nonzero(s.a[:, x])[0]
        if len(ys):
            s.px(x, ys[0], MOSS[3])
            s.px(x, ys[0] + 1, MOSS[2])
    s.ink()
    return s


@prop()
def rock_0():
    return _rock(12, 9, STONE, 6)


@prop()
def rock_1():
    return _rock(17, 12, STONE_D, 7, moss=2)


@prop()
def rock_mossy():
    return _rock(15, 11, STONE_D, 8, moss=8)


@prop()
def stump():
    s = Sprite(14, 11)
    s.part(s.rect(3, 4, 11, 10), BARK)
    s.part(s.poly([(1, 10), (3, 7), (4, 10)]), BARK_D)
    s.part(s.poly([(10, 10), (11, 7), (13, 10)]), BARK_D)
    s.fill(s.ellipse(7, 4, 4, 1.6), hexc("c8a070"))
    s.fill(s.ellipse(7, 4, 2, 0.8), hexc("a07a4a"))
    s.ink()
    return s


@prop()
def log():
    s = Sprite(22, 9)
    s.part(s.capsule(4, 5, 18, 4, 3.0), BARK)
    s.fill(s.ellipse(18, 4, 2.4, 3.0), hexc("c8a070"))
    s.px(18, 4, hexc("8a6a40"))
    s.line(5, 2, 15, 2, BARK[3])
    s.px(9, 1, MOSS[3])
    s.px(10, 1, MOSS[2])
    s.ink()
    return s


def _flowers(cols, seed):
    s = Sprite(11, 8)
    rng = np.random.default_rng(seed)
    for k in range(5):
        x = 1 + k * 2 + int(rng.integers(0, 2))
        top = int(rng.integers(1, 4))
        s.line(x, 7, x, top + 1, LEAF[2])
        s.px(x + (1 if k % 2 else -1), 6, LEAF[3])
        c = cols[k % len(cols)]
        s.px(x, top, c)
        s.px(x - 1, top + 1, c)
        s.px(x + 1, top + 1, c)
        s.px(x, top + 1, hexc("ffe070"))
    return s


@prop(sways=True)
def flowers_0():
    return _flowers([hexc("f0f0f8"), hexc("e8e0ff")], 9)


@prop(sways=True)
def flowers_1():
    return _flowers([hexc("e04a7a"), hexc("8a6ae0"), hexc("f0a030")], 10)


def _fern(seed, w=16, h=11):
    s = Sprite(w, h)
    rng = np.random.default_rng(seed)
    base = (w / 2, h - 1)
    for ang in (-2.6, -2.1, -1.6, -1.1, -0.55):
        L = rng.uniform(h * 0.7, h)
        x1, y1 = base[0] + math.cos(ang) * L * 0.8, base[1] + math.sin(ang) * L
        s.line(base[0], base[1], x1, y1, FERN[2])
        for t in np.linspace(0.3, 0.9, 4):
            px, py = base[0] + (x1 - base[0]) * t, base[1] + (y1 - base[1]) * t
            s.px(px - 1, py + 1, FERN[3])
            s.px(px + 1, py + 1, FERN[1])
        s.px(x1, y1, FERN[4])
    s.ink()
    return s


@prop(sways=True)
def fern_a():
    return _fern(11)


@prop(sways=True)
def fern_b():
    return _fern(12, 13, 9)


@prop(glow=True)
def dead_tree_0():
    """A charred tree: black limbs clawing up, embers still glowing in its cracks."""
    s = Sprite(32, 44)
    s.part(s.poly([(13, 43), (14, 24), (12, 14), (16, 20), (18, 10), (19, 22), (18, 43)]), CHAR)
    s.part(s.poly([(10, 43), (14, 38), (15, 43)]), CHAR, bias=-0.1)
    s.part(s.poly([(17, 43), (18, 38), (22, 43)]), CHAR, bias=-0.1)
    for (x0, y0, x1, y1) in ((14, 26, 5, 16), (5, 16, 3, 9), (17, 22, 26, 13), (26, 13, 29, 6), (12, 14, 9, 5),
                             (18, 10, 21, 2), (8, 21, 4, 20)):
        s.line(x0, y0, x1, y1, CHAR[2])
        s.line(x0 + 1, y0, x1 + 1, y1, CHAR[1])
    for (x, y) in ((15, 30), (16, 31), (15, 36), (16, 22)):
        s.px(x, y, FIRE[2], glow=True)
    s.ink()
    s.pxs([(20, 4), (7, 8)], FIRE[3], glow=True)
    return s


@prop(glow=True)
def dead_tree_1():
    s = Sprite(24, 34)
    s.part(s.poly([(10, 33), (11, 18), (9, 10), (13, 14), (14, 33)]), CHAR)
    for (x0, y0, x1, y1) in ((11, 20, 4, 12), (13, 16, 20, 8), (9, 10, 8, 3)):
        s.line(x0, y0, x1, y1, CHAR[2])
    s.px(12, 25, FIRE[2], glow=True)
    s.px(12, 26, FIRE[3], glow=True)
    s.ink()
    return s


@prop(glow=True)
def basalt_cols():
    """A cluster of hexagonal basalt columns, flat lit tops, a lava glow at their feet."""
    s = Sprite(26, 30)
    for (x, top, w) in ((3, 10, 6), (15, 6, 7), (9, 2, 7), (19, 14, 5)):
        block(s, x, top, x + w, 29, BASALT, depth=2, chips=2, seed=x)
    s.ink()
    s.fill(s.rect(4, 28, 22, 30) & ~s.a, FIRE[1], glow=True)
    s.pxs([(8, 29), (14, 29), (20, 29)], FIRE[2], glow=True)
    return s


def _basalt_rock(w, h, seed):
    s = _rock(w, h, BASALT, seed)
    rng = np.random.default_rng(seed)
    ys, xs = np.nonzero(s.a & (s.rgb[..., 0] > 40))
    for _ in range(2):
        k = int(rng.integers(0, len(xs)))
        s.px(xs[k], ys[k], FIRE[2], glow=True)
    return s


@prop(glow=True)
def basalt_rock_0():
    return _basalt_rock(12, 9, 13)


@prop(glow=True)
def basalt_rock_1():
    return _basalt_rock(17, 12, 14)


@prop(glow=True)
def charred_log():
    s = Sprite(22, 9)
    s.part(s.capsule(4, 5, 18, 4, 3.0), CHAR)
    s.fill(s.ellipse(18, 4, 2.4, 3.0), FIRE[1], glow=True)
    s.px(18, 4, FIRE[3], glow=True)
    s.pxs([(8, 4), (12, 5)], FIRE[2], glow=True)
    s.ink()
    return s


@prop(glow=True)
def ember_shard():
    """Chiselled shards of fire crystal pushing out of the ash, glowing from inside."""
    s = Sprite(14, 16)
    for (pts, tone) in (([(2, 15), (3, 7), (5, 5), (7, 15)], FIRE[1]), ([(9, 15), (10, 9), (12, 8), (13, 15)], FIRE[1]),
                        ([(4, 15), (6, 3), (8, 1), (10, 15)], FIRE[2])):
        s.fill(s.poly(pts), tone, glow=True)
    s.fill(s.poly([(6, 3), (8, 1), (8, 15), (6, 15)]), FIRE[3], glow=True)
    s.line(7, 3, 7, 10, FIRE[4], glow=True)
    s.ink((90, 20, 10))
    s.fill(s.rect(1, 14, 14, 16) & ~s.a, BASALT[1])
    return s


@prop()
def skull_rock():
    s = _rock(14, 10, BASALT, 15)
    s.part(s.ellipse(9, 5, 3.4, 3.0), BONE)
    s.fill(s.rect(8, 5, 9, 6), INK)
    s.fill(s.rect(10, 5, 11, 6), INK)
    s.ink()
    return s


def make_all(folder):
    os.makedirs(folder, exist_ok=True)
    info = {}
    for name, (fn, sways, glow) in PROPS.items():
        s = fn()
        s.image().save(os.path.join(folder, name + ".png"))
        s.normal_image().save(os.path.join(folder, name + "_n.png"))
        if glow:
            glow_image(s).save(os.path.join(folder, name + "_glow.png"))
        info[name] = {"size": [s.w, s.h], "sways": sways, "glow": glow}
    return info
