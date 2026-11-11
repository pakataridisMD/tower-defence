"""Act IV and V bosses in the hand-drawn 2D style: Cassivane the Ashen Regent, the Sundered Heart, the Gatemaw and
the Echo-Heralds. 32 art px = 1 board cell."""
from __future__ import annotations

import math

import numpy as np

from bosses import BOSSES, GREY_GLOW, RING, _crack, _dust
from creatures import CREATURES, DARK, GOLD, RED_D, SKIN, _slab
from kit import Sprite, ramp

CHAR = ramp("3a3638", spread=0.5, shift=0.02)          # blackened plate
CHAR_D = ramp("2a2628", spread=0.42, shift=0.02)
ENAMEL = ramp("7a2424", spread=0.45)                   # what is left of the red enamel
CLOAKR = ramp("6e1c20", spread=0.45)
ASHSKIN = ramp("a89c94", spread=0.45, shift=0.02)
SILVER = ramp("b8b8bc", spread=0.5, shift=0.0)
GREYH = ramp("7c7a80", spread=0.5, shift=0.0)
HEART = [(200, 130, 50), (255, 196, 96), (255, 236, 180), (255, 255, 240)]
EMBERE = [(150, 50, 20), (230, 110, 40), (255, 180, 90)]


def _shard(s, x, y, ang, ln, w, cols, glow=True):
    """A crystal shard: a long diamond split into a lit and a shaded half."""
    ca, sa = math.cos(ang), math.sin(ang)
    tip = (x + ca * ln, y + sa * ln)
    mid = (x + ca * ln * 0.35, y + sa * ln * 0.35)
    l = (mid[0] - sa * w, mid[1] + ca * w)
    r = (mid[0] + sa * w, mid[1] - ca * w)
    lit, dark = (l, r) if (-sa * -0.5 + ca * -0.62) > 0 else (r, l)
    s.fill(s.poly([(x, y), lit, tip]), cols[2], glow=glow)
    s.fill(s.poly([(x, y), dark, tip]), cols[1], glow=glow)
    s.line(x, y, tip[0], tip[1], cols[3], glow=glow)


def _flakes(s, n, seed, cols):
    """Armour flaking like burned paper: pale curls along the shapes, inside the body."""
    rng = np.random.default_rng(seed)
    ys, xs = np.where(s.a)
    for _ in range(n):
        i = int(rng.integers(len(xs)))
        y, x = ys[i], xs[i]
        s.rgb[y, x] = cols[int(rng.integers(len(cols)))]


def cassivane(pose=None, pad=0):
    """Cassivane Dral, the Ashen Regent: the Lord Marshal's plate blackened and flaking like burned paper, ash drifting
    off him, Heartstone shards growing out of his shoulders, eyes gone grey, the gold locket still in his hand."""
    s = Sprite(104, 116, pose, pad, origin=(2, 4))
    # the red cloak behind, burned to tatters at the hem
    s.g("cloak", 42, 44)
    s.part(s.poly([(36, 42), (52, 42), (50, 70), (40, 100), (34, 92), (28, 102), (22, 92), (16, 98), (20, 70)]), CLOAKR, bias=-0.1)
    for x, y in ((24, 94), (30, 98), (36, 94), (20, 90)):
        s.px(x, y, EMBERE[1], glow=True)
    # far leg
    s.g("leg_f", 42, 76)
    s.part(s.capsule(42, 78, 41.6, 86, 4.8), CHAR_D, bias=-0.25)
    s.g("shin_f", 41.6, 86, "leg_f")
    s.part(s.capsule(41.6, 86, 41, 94, 4.6), CHAR_D, bias=-0.25, edge=False)
    s.part(s.ellipse(42, 99, 7, 4.2), CHAR_D, bias=-0.25)
    # sword arm on the far side, raised: a blackened longsword with a grey edge
    s.g("weapon", 58, 46)
    s.part(s.capsule(58, 46, 66, 50, 5), CHAR_D)
    s.g("hand_w", 66, 50, "weapon")
    s.part(s.poly([(72, 48), (78, 48), (90, 4), (86, 0), (82, 6)]), CHAR, flat=True, bias=0.15)
    s.line(86, 2, 76, 46, GREY_GLOW[2], glow=True)
    s.line(84, 6, 74, 46, CHAR[1])
    s.part(s.capsule(66, 50, 72, 52, 5), CHAR_D, edge=False)
    s.part(s.rect(66, 46, 86, 50), GOLD, flat=True, bias=-0.2)
    s.part(s.ellipse(75, 53, 5, 4.6), CHAR)
    s.g("weapon", 58, 46)
    s.part(s.ellipse(61, 43, 8, 6.6), CHAR_D)
    # torso: blackened breastplate, a few red enamel scraps left, a crack of grey fire
    s.g("body")
    s.part(s.ellipse(48, 58, 15, 15), CHAR)
    s.fill(s.poly([(40, 50), (50, 48), (52, 58), (42, 62)]), ENAMEL[2])
    s.fill(s.poly([(52, 64), (58, 60), (60, 68), (54, 70)]), ENAMEL[1])
    s.line(55, 46, 57, 68, CHAR[4])
    _crack(s, [(46, 50), (50, 56), (47, 62), (52, 68)], GREY_GLOW[1], GREY_GLOW[3])
    s.part(s.rect(38, 42, 60, 46), CHAR_D, flat=True)
    # head: bare, ash-pale, grey at the temples gone all grey, short silver beard, grey light for eyes
    s.g("head", 48, 40)
    s.part(s.ellipse(50, 28, 10, 11.5), ASHSKIN)
    s.part(s.poly([(40, 22), (46, 15), (56, 15), (61, 20), (60, 23), (52, 20), (46, 24), (42, 30)]), GREYH)      # swept-back hair
    s.part(s.poly([(48, 34), (60, 32), (61, 38), (56, 42), (50, 41)]), SILVER, bias=-0.05)                       # short beard
    s.fill(s.rect(53, 26, 56, 28), GREY_GLOW[2], glow=True)
    s.px(54, 26, GREY_GLOW[3], glow=True)
    s.line(52, 24, 58, 24, ASHSKIN[0])
    s.pxs([(60, 29), (61, 30), (60, 31)], ASHSKIN[1])
    s.line(51, 23, 51, 31, GREYH[1])                                                                         # grey temple
    s.line(56, 35, 59, 35, ASHSKIN[0])
    # tassets and belt
    s.g("leg_n", 54, 80)
    s.part(s.capsule(54, 78, 55, 86, 5.6), CHAR)
    s.g("body")
    s.part(s.poly([(32, 70), (64, 70), (66, 84), (30, 84)]), CHAR)
    s.fill(s.poly([(34, 74), (44, 74), (44, 82), (33, 82)]), ENAMEL[1])
    s.line(30, 84, 66, 84, CHAR[3])
    s.line(48, 72, 48, 82, CHAR[0])
    s.part(s.rect(32, 68, 64, 72), ramp("4a3020"), flat=True)
    s.fill(s.rect(47, 68, 51, 72), GOLD[2])
    # near leg
    s.g("leg_n", 54, 80)
    s.g("shin_n", 55, 86, "leg_n")
    s.part(s.capsule(54.6, 84, 56, 95, 5.6), CHAR)
    s.part(s.ellipse(55, 86, 5.2, 4), ENAMEL)
    s.part(s.ellipse(59, 100, 8.4, 4.8) | s.rect(52, 92, 62, 100), CHAR)
    # near arm: the locket held against the chest, chain hanging
    s.g("arm_n", 37, 48)
    s.part(s.capsule(37, 50, 42, 62, 5), CHAR)
    s.part(s.capsule(42, 62, 52, 60, 4.6), CHAR, edge=False)
    s.part(s.ellipse(54, 59, 4.4, 4.2), CHAR_D)
    s.fill(s.ellipse(57, 61, 3, 3.4), GOLD[3])
    s.fill(s.ellipse(57.5, 61.5, 1.6, 2), GOLD[1])
    s.px(56, 60, (255, 250, 210))
    s.line(57, 64, 56, 72, GOLD[2])
    s.px(56, 73, GOLD[3])
    # near pauldron, and the Heartstone shards growing out of both shoulders
    s.part(s.ellipse(37, 47, 11, 9), CHAR)
    s.fill(s.poly([(30, 46), (40, 42), (42, 48), (32, 50)]), ENAMEL[2])
    s.line(28, 52, 44, 54, CHAR[3])
    s.g("body")
    for x, y, ang, ln, w in ((32, 42, -2.0, 18, 3.4), (37, 41, -1.65, 14, 3.0), (27, 44, -2.5, 14, 2.8), (24, 50, -2.9, 9, 2.2),
                             (64, 40, -1.0, 13, 2.8), (68, 43, -0.55, 9, 2.2)):
        _shard(s, x, y, ang, ln, w, HEART)
    s.ink()
    _flakes(s, 60, 3, [(120, 116, 112), (90, 86, 84), (156, 150, 144)])
    _dust(s, 34, 17)
    s.shadow(50, 104, 22, 3.4)
    return s


SUN = [(150, 80, 30), (222, 140, 50), (255, 200, 100), (255, 240, 200)]
PALEH = [(200, 196, 210), (230, 228, 236), (250, 248, 255), (255, 255, 255)]


def _shard_ring(s, cx, cy, n, r0, ln, w, seed, sets, jitter=0.25, turn=0.0):
    rng = np.random.default_rng(seed)
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n + rng.uniform(-jitter, jitter)
        rr = r0 * rng.uniform(0.85, 1.1)
        x, y = cx + math.cos(ang) * rr, cy + math.sin(ang) * rr * 0.9
        cols = sets[i % len(sets)]
        _shard(s, x, y, ang + turn * (1 if i % 2 else -1) + rng.uniform(-0.2, 0.2), ln * rng.uniform(0.7, 1.15), w * rng.uniform(0.8, 1.2), cols)
        tip = (x + math.cos(ang) * ln * 0.5, y + math.sin(ang) * ln * 0.5)
        s.px(round(tip[0]), round(tip[1]), RING[i % 6], glow=True)


def sundered_heart(pose=None, pad=0):
    """The Sundered Heart: a huge floating knot of Sunstone shards and stolen Heartstone light, around a small grey
    figure curled about the locket in the middle."""
    s = Sprite(210, 214, pose, pad, origin=(0, 4))
    cx, cy = 104, 96
    # outer shards, turning slowly as one
    s.g("aura", cx, cy)
    _shard_ring(s, cx, cy, 13, 44, 52, 7, 1, [SUN, PALEH, SUN])
    # bits of the Regent's black armour caught in the knot
    for x, y, ang in ((40, 70, 0.4), (164, 120, -0.6), (150, 46, 1.0), (58, 150, -1.2)):
        c, sn = math.cos(ang), math.sin(ang)
        pts = [(x + c * dx - sn * dy, y + sn * dx + c * dy) for dx, dy in ((-7, -4), (7, -5), (8, 3), (-6, 5))]
        s.part(s.poly(pts), CHAR, flat=True)
        s.px(x, y, ENAMEL[2])
    # the light of the Heartstone
    s.g("body")
    for r, col in ((34, HEART[0]), (28, HEART[1]), (21, HEART[2]), (13, HEART[3])):
        s.fill(s.ellipse(cx, cy, r, r * 0.92), col, glow=True)
    # inner shards packed tight around it
    _shard_ring(s, cx, cy, 11, 24, 32, 5.5, 2, [PALEH, SUN, HEART])
    for i in range(6):
        ang = -math.pi / 2 + i * math.pi / 3
        pts = [(cx + math.cos(ang) * r, cy + math.sin(ang) * r + (2 if r % 2 else -2)) for r in range(14, 44, 6)]
        _crack(s, pts, RING[i], (255, 255, 255))
    # shards grown across the others, so it reads as a knot and not a star
    rng = np.random.default_rng(9)
    DSUN = [(110, 60, 30), (170, 100, 40), (214, 150, 70), (250, 210, 150)]
    for i in range(18):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(14, 34)
        x, y = cx + math.cos(a) * r, cy + math.sin(a) * r
        _shard(s, x, y, a + rng.uniform(-1.4, 1.4), rng.uniform(26, 44), rng.uniform(4, 7), [DSUN, SUN, PALEH][i % 3])
    for r, col in ((15, HEART[2]), (11, HEART[3])):
        s.fill(s.ellipse(cx, cy, r, r), col, glow=True)
    # the small grey figure curled in the middle, knees to his chest, holding the locket
    G = [(70, 66, 74), (104, 100, 108), (136, 132, 140), (170, 166, 172)]
    s.fill(s.ellipse(cx - 3, cy + 2, 7, 9.5), G[1])                                                          # curved back
    s.fill(s.ellipse(cx - 5, cy, 3, 7), G[2])
    s.fill(s.ellipse(cx + 2, cy - 9, 4.6, 4.6), G[2])                                                        # bowed head
    s.pxs([(cx, cy - 12), (cx + 1, cy - 12), (cx - 1, cy - 11)], G[3])
    s.fill(s.ellipse(cx + 5, cy + 3, 4.5, 6.5), G[0])                                                        # knees drawn up
    s.fill(s.ellipse(cx + 2, cy + 11, 5, 2.5), G[1])                                                         # feet
    s.line(cx + 2, cy - 3, cx + 7, cy - 2, G[3])                                                              # arm wrapped round
    s.fill(s.ellipse(cx + 6, cy - 3, 2, 2.2), GOLD[3])
    s.px(cx + 6, cy - 4, (255, 255, 220))
    s.ink((90, 50, 20))
    s.g("aura", cx, cy)
    rng = np.random.default_rng(4)
    for _ in range(40):                                                                                      # loose sparks
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(60, 98)
        s.px(round(cx + math.cos(a) * r), round(cy + math.sin(a) * r * 0.92), [SUN[2], PALEH[2], RING[int(rng.integers(6))]][int(rng.integers(3))], glow=True)
    s.g("body")
    s.shadow(104, 206, 40, 4)
    return s


OBS = ramp("38343e", spread=0.5, shift=0.02)
OBS_D = ramp("26232c", spread=0.4, shift=0.02)
TIMBER = ramp("6a4a2c", spread=0.5, shift=0.02)
IRONG = ramp("5a5c64", spread=0.5, shift=0.0)
BRASS = ramp("b07a30", spread=0.55)
DAWN = ramp("d8c890", spread=0.5)


def _gate(s, x, y, w, h, down, kind, seed):
    """A stolen city gate set as a tooth: planks, iron bands, an arch at the root, a broken point at the tip."""
    rng = np.random.default_rng(seed)
    sg = 1 if down else -1
    tip = y + sg * h
    jag = [(x + w, tip - sg * 6), (x + w * 0.7, tip - sg * 1), (x + w * 0.5, tip + sg * 2), (x + w * 0.3, tip - sg * 2), (x, tip - sg * 7)]
    face = TIMBER if kind in ("plain", "brazier") else DAWN if kind == "dawn" else IRONG
    s.part(s.poly([(x, y), (x + w, y)] + jag), face, flat=True)
    if kind == "portcullis":
        for gx in range(int(x) + 3, int(x + w), 5):
            s.line(gx, y, gx, tip - sg * 4, IRONG[3])
            s.line(gx + 1, y, gx + 1, tip - sg * 4, IRONG[0])
        for gy in range(int(min(y, tip)) + 4, int(max(y, tip)) - 3, 6):
            s.line(x + 1, gy, x + w - 1, gy, IRONG[3])
    else:
        for gx in range(int(x) + 4, int(x + w) - 1, 4):
            s.line(gx, y + sg, gx, tip - sg * 5, face[1])
        for k in (0.25, 0.65):
            by = y + sg * h * k
            s.part(s.rect(x, min(by, by + sg * 3), x + w, max(by, by + sg * 3) + 1), BRASS if kind == "brazier" else IRONG, flat=True, edge=False)
            for gx in range(int(x) + 3, int(x + w), 6):
                s.px(gx, round(by + sg), (220, 214, 200))
        sy = y + sg * h * 0.45
        if kind == "brazier":                                                                               # Brazier Hold's flame sigil
            s.fill(s.poly([(x + w / 2 - 4, sy + 4), (x + w / 2 + 4, sy + 4), (x + w / 2 + 1, sy - 6), (x + w / 2 - 1, sy - 2)]), (230, 110, 40))
            s.px(round(x + w / 2), round(sy + 1), (255, 200, 90))
        if kind == "dawn":                                                                                  # the Dawn Gate's sun
            s.fill(s.ellipse(x + w / 2, sy, 4, 4), (240, 196, 80))
            for a in range(8):
                ang = a * math.pi / 4
                s.px(round(x + w / 2 + math.cos(ang) * 6), round(sy + math.sin(ang) * 6), (240, 196, 80))
    # the arch where it was torn from its wall
    s.line(x, y, x + w, y, (20, 16, 20))
    if rng.random() < 0.6:
        s.line(x + 2, y + sg * 2, x + w - 2, y + sg * 2, face[4])


def gatemaw(pose=None, pad=0):
    """The Gatemaw: Nhal Vorath's living gate, a cliff of black stone with a mouth the width of the road and stolen
    city gates set in it for teeth. Faces the player; the lower jaw drops to spit out the Unbound."""
    s = Sprite(288, 176, pose, pad, origin=(0, 8))
    # the gullet: dark, with grey light far inside
    s.g("body")
    s.fill(s.poly([(36, 84), (252, 84), (244, 172), (44, 172)]), (14, 10, 16))
    for r, col in ((34, (40, 38, 46)), (20, GREY_GLOW[0])):
        s.fill(s.ellipse(144, 132, r * 2, r * 0.6), col, glow=col == GREY_GLOW[0])
    s.fill(s.ellipse(144, 132, 18, 5), GREY_GLOW[1], glow=True)
    if s.pose.get("_spit"):                     # the gullet blazes as it spits out the Unbound
        s.fill(s.ellipse(144, 134, 60, 18), GREY_GLOW[1], glow=True)
        s.fill(s.ellipse(144, 136, 36, 10), GREY_GLOW[2], glow=True)
        s.fill(s.ellipse(144, 138, 16, 5), GREY_GLOW[3], glow=True)
    # the face of black stone: courses of blocks, merlons along the brow, towers for cheeks
    for row, y in enumerate(range(20, 84, 16)):
        off = 0 if row % 2 else 14
        for x in range(-14 + off, 290, 28):
            x0, x1 = max(6, x), min(282, x + 28)
            if x1 - x0 > 6:
                _slab(s, [(x0, y), (x1, y), (x1, y + 16), (x0, y + 16)], OBS if row % 2 else OBS_D, depth=(2, -2), chips=1, seed=abs(x) * 7 + y)
    for x in range(10, 280, 20):
        _slab(s, [(x, 8), (x + 12, 8), (x + 12, 20), (x, 20)], OBS, depth=(2, -2), seed=x)
    for x0, x1 in ((0, 40), (248, 288)):
        _slab(s, [(x0, 40), (x1, 40), (x1, 168), (x0, 168)], OBS_D, depth=(3, -3), chips=4, seed=x0 + 3)
        _slab(s, [(x0 - 2, 30), (x1 + 2, 30), (x1 + 2, 42), (x0 - 2, 42)], OBS, depth=(3, -3), seed=x0 + 5)
    # eyes: two arched windows of grey light, the brow over them carved into a frown
    for ex in (92, 196):
        s.fill(s.poly([(ex - 14, 66), (ex - 14, 50), (ex - 8, 42), (ex + 8, 42), (ex + 14, 50), (ex + 14, 66)]), (16, 12, 18))
        s.fill(s.poly([(ex - 10, 64), (ex - 10, 52), (ex - 6, 46), (ex + 6, 46), (ex + 10, 52), (ex + 10, 64)]), GREY_GLOW[1], glow=True)
        s.fill(s.rect(ex - 4, 50, ex + 5, 62), GREY_GLOW[3], glow=True)
        s.line(ex, 46, ex, 64, (16, 12, 18))
        d = 1 if ex < 144 else -1
        _slab(s, [(ex - 20, 34 - 6 * d), (ex + 20, 34 + 6 * d), (ex + 20, 40 + 6 * d), (ex - 20, 40 - 6 * d)], OBS, depth=(2, -2), seed=ex)
    # the upper jaw: a heavy lintel and gates hanging from it as teeth
    _slab(s, [(30, 76), (258, 76), (252, 90), (36, 90)], OBS, depth=(3, -3), chips=4, seed=91)
    kinds = ["portcullis", "brazier", "plain", "dawn", "plain", "portcullis"]
    for i, x in enumerate(range(42, 236, 33)):
        _gate(s, x, 90, 26, 30 + (i % 2) * 8, True, kinds[i], i)
    for x in (40, 248):
        for y in range(92, 150, 5):
            s.pxs([(x, y), (x + 1, y + 2)], IRONG[2 + (y // 5) % 2])                                         # chains
    # the lower jaw: gates rising from the ground as teeth, on a lip of broken stone
    s.g("jaw", 144, 166)
    for i, x in enumerate(range(56, 220, 34)):
        _gate(s, x, 162, 24, 24 + ((i + 1) % 2) * 8, False, ["plain", "portcullis", "dawn", "plain", "brazier"][i], i + 10)
    _slab(s, [(40, 160), (248, 160), (244, 172), (44, 172)], OBS_D, depth=(3, -3), chips=4, seed=92)
    s.g("body")
    s.ink()
    _dust(s, 40, 19)
    s.shadow(144, 171, 140, 4)
    return s


# ---- Final assault structures -----------------------------------------------------------------------------------
from bosses import GLASS, GLASS_D  # noqa: E402

MIRROR = ramp("5a5e6e", spread=0.5, shift=0.0)
MIRROR_D = ramp("3c3f4c", spread=0.42, shift=0.0)


def mirror_spire(pose=None, pad=0):
    """The Mirror Spire: Solenne's six rings of walls made wrong, stacked upside down on a point of black glass, every
    ring a stolen city wall gone grey, a drained keystone glyph in each."""
    s = Sprite(176, 262, pose, pad, origin=(0, 6))
    cx = 88
    # the black-glass pool the point stands in, with the spire's reflection
    s.g("leg_pool", cx, 246)
    s.part(s.ellipse(cx, 248, 62, 8), GLASS_D, flat=True)
    for k in range(5):
        s.line(cx - 40 + k * 4, 248 - (k % 2), cx + 40 - k * 4, 248 - (k % 2), GLASS_D[3 if k % 2 else 2])
    s.g("body")
    # rings from the widest at the top down to the narrowest just above the point
    tiers = [(10, 166, 30), (42, 148, 32), (76, 132, 32), (110, 116, 30), (142, 100, 28), (172, 86, 26)]
    for i, (y, w, h) in reversed(list(enumerate(tiers))):     # lowest first, so each ring's hanging merlons overlap the one below
        x0, x1 = cx - w / 2, cx + w / 2
        _slab(s, [(x0, y), (x1, y), (x1 - 6, y + h), (x0 + 6, y + h)], MIRROR if i % 2 else MIRROR_D, depth=(3, -3), chips=4, seed=40 + i)
        for x in range(int(x0) + 8, int(x1) - 8, 14):                       # merlons hanging the wrong way, under each ring
            s.part(s.rect(x, y + h, x + 8, y + h + 6), MIRROR_D, flat=True)
        for x in range(int(x0) + 14, int(x1) - 14, 18):                     # windows of grey glass
            s.fill(s.rect(x, y + 9, x + 5, y + 19), (20, 18, 26))
            s.fill(s.rect(x + 1, y + 10, x + 4, y + 18), GREY_GLOW[0], glow=True)
            s.px(x + 1, y + 10, GREY_GLOW[2], glow=True)
        gy = y + h / 2
        s.fill(s.poly([(cx, gy - 7), (cx + 6, gy), (cx, gy + 7), (cx - 6, gy)]), (24, 22, 30))
        s.fill(s.poly([(cx, gy - 5), (cx + 4, gy), (cx, gy + 5), (cx - 4, gy)]), RING[i], glow=True)
        s.px(cx, gy - 3, (255, 255, 255), glow=True)
        if s.pose.get("_spit"):                                             # the rings flare in turn
            s.fill(s.poly([(cx, gy - 9), (cx + 8, gy), (cx, gy + 9), (cx - 8, gy)]) & ~s.poly([(cx, gy - 5), (cx + 4, gy), (cx, gy + 5), (cx - 4, gy)]),
                   GREY_GLOW[2], glow=True)
    # the point of black glass it stands on
    s.part(s.poly([(cx - 30, 204), (cx + 30, 204), (cx + 2, 246), (cx - 2, 246)]), GLASS, bulge=0.6)
    s.line(cx - 22, 206, cx - 1, 244, GLASS[4])
    _crack(s, [(cx - 8, 208), (cx - 3, 220), (cx - 6, 232)], GREY_GLOW[1], GREY_GLOW[3])
    # the gate at the top that Seraphel holds open
    s.fill(s.poly([(cx - 10, 10), (cx - 10, 2), (cx - 5, -4), (cx + 5, -4), (cx + 10, 2), (cx + 10, 10)]), (20, 18, 26))
    s.fill(s.poly([(cx - 7, 10), (cx - 7, 3), (cx - 3, -1), (cx + 3, -1), (cx + 7, 3), (cx + 7, 10)]), GREY_GLOW[1], glow=True)
    s.ink()
    _dust(s, 40, 21)
    s.shadow(cx, 250, 30, 2)
    return s


def crownless_throne(pose=None, pad=0):
    """The Crownless Throne: no throne at all, only a dais of black glass standing on nothing, with a high back cut
    through by a crown-shaped gap and six empty sockets where the Wardens' colours belong."""
    s = Sprite(200, 220, pose, pad, origin=(0, 6))
    cx = 100
    # the high back of black glass, a crown-shaped gap cut clean through it
    s.g("body")
    back = s.poly([(cx - 34, 150), (cx - 40, 60), (cx - 26, 20), (cx - 10, 34), (cx, 4), (cx + 10, 34), (cx + 26, 20), (cx + 40, 60), (cx + 34, 150)])
    s.part(back, GLASS, bulge=0.5)
    for (x0, y0, x1, y1), k in (((cx - 40, 60, cx - 34, 150), 4), ((cx - 26, 20, cx - 40, 60), 4), ((cx + 40, 60, cx + 34, 150), 1),
                                ((cx, 4, cx - 10, 34), 3), ((cx - 18, 40, cx - 20, 140), 2), ((cx + 18, 40, cx + 20, 140), 1)):
        s.line(x0, y0, x1, y1, GLASS[k])
    for i, (x, y) in enumerate(((cx - 30, 70), (cx - 32, 96), (cx - 30, 122), (cx + 30, 70), (cx + 32, 96), (cx + 30, 122))):
        s.fill(s.rect(x - 3, y - 3, x + 3, y + 3), (6, 5, 10))                                              # six empty sockets
        s.px(x - 2, y - 2, RING[i])
        if s.pose.get("_spit"):
            s.fill(s.rect(x - 2, y - 2, x + 2, y + 2), RING[i], glow=True)
    hole = s.poly([(cx - 16, 120), (cx - 16, 70), (cx - 8, 86), (cx, 62), (cx + 8, 86), (cx + 16, 70), (cx + 16, 120)])
    # the stepped dais, floating
    for i, (w, y, h) in enumerate(((150, 150, 12), (120, 162, 10), (94, 172, 10))):
        _slab(s, [(cx - w / 2, y), (cx + w / 2, y), (cx + w / 2 - 8, y + h), (cx - w / 2 + 8, y + h)], GLASS if i % 2 else GLASS_D, depth=(3, -3), seed=60 + i)
    s.part(s.poly([(cx - 40, 182), (cx + 40, 182), (cx + 6, 206), (cx - 6, 206)]), GLASS_D, bulge=0.6)        # the shard underneath
    _crack(s, [(cx - 20, 184), (cx - 8, 192), (cx - 4, 202)], GREY_GLOW[1], GREY_GLOW[3])
    s.ink()
    grow = hole.copy()
    grow[1:] |= hole[:-1]
    grow[:-1] |= hole[1:]
    grow[:, 1:] |= hole[:, :-1]
    grow[:, :-1] |= hole[:, 1:]
    s.fill(grow & ~hole & s.a, (214, 216, 232), glow=True)
    s.a[hole] = False
    _dust(s, 30, 22)
    rng = np.random.default_rng(6)
    for _ in range(30):                                                                                     # ash falling into nothing below
        s.px(round(cx + rng.uniform(-50, 50)), round(rng.uniform(190, 216)), GREY_GLOW[int(rng.integers(0, 2))], glow=True)
    s.shadow(cx, 214, 30, 2)
    return s


# ---- Echo-Heralds ------------------------------------------------------------------------------------------------
HERALD_ELEMENT = {"ourra": 3, "gorrath": 4, "vesper": 5, "ashwick": 0, "vholt": 1, "mother_briar": 2}   # index into RING
GLASSG = [(46, 50, 62), (78, 84, 98), (118, 124, 140), (166, 172, 188), (214, 218, 230)]
FLICKER = {1: 2, 4: 1, 6: 4}       # on these frames an echo shows another element than its own (offset round the ring)


def _echo(herald):
    """An Echo-Herald: the Herald redrawn as a glassy grey reflection, its light flickering between the elements."""
    base = BOSSES[herald]
    own = HERALD_ELEMENT[herald]

    def draw(pose=None, pad=0):
        t = (pose or {}).get("_t", 0)
        s = base({k: v for k, v in (pose or {}).items() if k != "_t"}, pad)
        el = RING[(own + FLICKER.get(t % 8, 0)) % 6]
        lum = (s.rgb[..., 0] * 0.3 + s.rgb[..., 1] * 0.55 + s.rgb[..., 2] * 0.15) / 255
        idx = np.clip((lum * 1.25 * len(GLASSG)).astype(int), 0, len(GLASSG) - 1)
        out = np.array(GLASSG, np.uint8)[idx]
        g = s.glow & s.a
        e = np.array(el, np.float32)
        out[g] = np.clip(e * 0.55 + 255 * 0.45 * lum[g, None], 0, 255).astype(np.uint8)
        # a mirror sheen: thin diagonal streaks across the body
        diag = ((s.xs + s.ys) % 23 == 0) | ((s.xs + s.ys) % 23 == 1)
        sheen = diag & s.a & ~g
        out[sheen] = np.minimum(out[sheen].astype(int) + 46, 255).astype(np.uint8)
        # the outline takes the element's colour
        edge = s.a & ~np.roll(s.a, 1, 0) | s.a & ~np.roll(s.a, -1, 0) | s.a & ~np.roll(s.a, 1, 1) | s.a & ~np.roll(s.a, -1, 1)
        out[edge & (lum < 0.2)] = (e * 0.6).astype(np.uint8)
        s.rgb[s.a] = out[s.a]
        s.opacity = 220
        return s

    draw.__doc__ = f"Echo of {herald}: a glassy grey reflection flickering between its element and the others."
    return draw


ECHOES = {"echo_" + h: _echo(h) for h in HERALD_ELEMENT}


FINAL = {"cassivane": cassivane, "sundered_heart": sundered_heart, "gatemaw": gatemaw, "mirror_spire": mirror_spire,
         "crownless_throne": crownless_throne, **ECHOES}
CREATURES.update(FINAL)
