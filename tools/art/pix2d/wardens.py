"""The corrupted Wardens (stage-4 bosses) in the hand-drawn 2D style: each is the freed Warden, made wrong.

32 art px = 1 board cell. Wardens stand about 5 to 6 cells tall. Corruption reads the same on all of them:
their own colour drained to grey, grey light where their element's light should be, grey dust off the outline.
"""
from __future__ import annotations

import math

import numpy as np

from bosses import GREY_GLOW, _crack, _dust
from creatures import CREATURES, _slab
from kit import Sprite, ramp

# ---- Mountain Titan ---------------------------------------------------------------------------------------------
TITAN = ramp("6e6860", spread=0.5, shift=0.02)
TITAN_D = ramp("524e4a", spread=0.42, shift=0.02)
LICHEN = [(112, 114, 116), (150, 152, 154), (186, 188, 188), (214, 214, 210)]
GEODE = [(120, 60, 16), (206, 120, 30), (255, 184, 70), (255, 230, 160)]
DEADWOOD = ramp("3a3028", spread=0.4, shift=0.02)
FLAME = [(176, 52, 18), (238, 104, 30), (255, 170, 54), (255, 226, 140)]
DEADMOSS = ramp("6a6a48", spread=0.4)


def _lichen(s, cx, cy, rx, ry, seed, n=40):
    """Grey lichen crusting over stone: a scatter of pale pixels that thickens toward the middle."""
    rng = np.random.default_rng(seed)
    for _ in range(n):
        a, r = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform(0, 1))
        x, y = cx + math.cos(a) * rx * r, cy + math.sin(a) * ry * r
        tx, ty = (round(v) for v in s.fw(x, y))
        if 0 <= tx < s.w and 0 <= ty < s.h and s.a[ty, tx]:
            s.px(round(x), round(y), LICHEN[int(rng.integers(0, 3)) if r > 0.5 else int(rng.integers(1, 4))])


def _dead_pine(s, x, base, h, seed, burn=True):
    """A dead pine: a black trunk, bare drooping branch tiers, a few flames and embers licking up it."""
    rng = np.random.default_rng(seed)
    s.part(s.poly([(x - 2.5, base), (x + 2.5, base), (x + 0.5, base - h), (x - 0.5, base - h)]), DEADWOOD, flat=True)
    for i in range(5, int(h) - 1, 3):
        y = base - i
        ln = max(2.0, (h - i) * 0.42)
        s.line(x, y, x - ln, y + ln * 0.55, DEADWOOD[2])
        s.line(x, y, x + ln, y + ln * 0.55, DEADWOOD[0])
        s.px(round(x - ln), round(y + ln * 0.55) + 1, DEADWOOD[1])
    if burn:
        for _ in range(2):
            fy = base - rng.uniform(h * 0.35, h * 0.8)
            fx = x + rng.uniform(-2, 2)
            fh = rng.uniform(5, 8)
            s.fill(s.poly([(fx - 2.5, fy + 2), (fx + 2.5, fy + 2), (fx + 1, fy - fh), (fx - 1, fy - fh * 0.5)]), FLAME[1], glow=True)
            s.fill(s.poly([(fx - 1, fy + 1), (fx + 1.5, fy + 1), (fx + 0.5, fy - fh * 0.55)]), FLAME[2], glow=True)
            s.px(round(fx), round(fy), FLAME[3], glow=True)
        for _ in range(3):
            s.px(round(x + rng.uniform(-6, 6)), round(base - h - rng.uniform(0, 10)), FLAME[int(rng.integers(1, 3))], glow=True)


def mountain_titan(pose=None, pad=0):
    """The Mountain Titan, Orrok corrupted: a vast hunched stone giant with crags for shoulders, grey lichen over his
    amber eyes, the pines on his shoulders dead and burning."""
    s = Sprite(184, 214, pose, pad, origin=(0, 18))
    # far arm, long enough that the knuckles reach the ground
    s.g("arm_f", 126, 66)
    _slab(s, [(114, 60), (140, 60), (142, 108), (118, 108)], TITAN_D, chips=3, seed=1)
    s.g("fore_f", 130, 108, "arm_f")
    _slab(s, [(116, 109), (142, 109), (146, 148), (120, 148)], TITAN_D, chips=2, seed=2)
    _slab(s, [(112, 148), (150, 148), (152, 182), (114, 182)], TITAN_D, chips=3, seed=3)
    for x in (122, 131, 140):
        s.line(x, 170, x, 181, TITAN_D[0])
    # legs: short thick thighs and shins, broad feet
    for grp, sub, x, tone, sd in (("leg_f", "shin_f", 64, TITAN_D, 4), ("leg_n", "shin_n", 92, TITAN, 7)):
        s.g(grp, x + 13, 128)
        _slab(s, [(x, 124), (x + 26, 124), (x + 26, 154), (x + 2, 154)], tone, chips=2, seed=sd)
        s.g(sub, x + 13, 154, grp)
        _slab(s, [(x + 1, 155), (x + 25, 155), (x + 27, 180), (x + 3, 180)], tone, chips=2, seed=sd + 1)
        _slab(s, [(x - 5, 180), (x + 32, 180), (x + 34, 191), (x - 6, 191)], TITAN_D, depth=(3, -2), seed=sd + 2)
        _lichen(s, x + 13, 164, 9, 10, sd, 12)
    # hips
    s.g("body")
    _slab(s, [(58, 112), (124, 112), (120, 130), (62, 130)], TITAN_D, chips=2, seed=10)
    # the hunched chest, leaning forward, runes cut into it gone grey
    _slab(s, [(40, 44), (98, 40), (136, 50), (128, 116), (54, 118)], TITAN, depth=(5, -5), chips=12, seed=11)
    _slab(s, [(62, 76), (118, 74), (114, 102), (68, 102)], TITAN_D, depth=(2, -2), chips=3, seed=12)    # belly plate
    for (x0, y0, x1, y1) in ((74, 82, 84, 82), (84, 82, 84, 94), (74, 94, 84, 94), (74, 82, 74, 88), (92, 84, 106, 84),
                             (99, 84, 99, 98), (92, 98, 106, 98)):
        s.line(x0, y0, x1, y1, GREY_GLOW[1], glow=True)                                                  # square runes, dead grey
    s.pxs([(79, 88), (99, 91)], GREY_GLOW[3], glow=True)
    _crack(s, [(66, 52), (72, 60), (68, 68), (76, 74)], GREY_GLOW[1], GREY_GLOW[3])
    _crack(s, [(114, 102), (120, 108), (116, 114)], GREY_GLOW[1])
    _lichen(s, 122, 58, 8, 6, 14, 18)
    for x, y, ln in ((58, 116, 10), (66, 118, 6), (122, 114, 7), (114, 118, 5)):
        s.line(x, y, x, y + ln, DEADMOSS[1])
        s.line(x + 1, y, x + 1, y + ln - 2, DEADMOSS[2])
    # far shoulder crag with its pines, behind the head
    _slab(s, [(94, 42), (102, 22), (108, 30), (116, 16), (126, 34), (134, 50), (96, 52)], TITAN_D, depth=(3, -3), chips=3, seed=13)
    for x, b, h, sd in ((104, 30, 30, 20), (116, 22, 24, 21)):
        _dead_pine(s, x, b, h, sd)
    # head: low and thrust forward, a heavy brow, amber geode eyes crusted over with lichen, a beard of hanging rock
    s.g("head", 126, 56)
    _slab(s, [(114, 40), (146, 40), (148, 68), (116, 68)], TITAN_D, chips=3, seed=15)
    _slab(s, [(110, 34), (148, 30), (154, 38), (152, 46), (110, 46)], TITAN, depth=(4, -3), chips=2, seed=16)   # brow ridge
    for ex in (128, 141):
        s.fill(s.poly([(ex - 4, 50), (ex, 47), (ex + 5, 50), (ex + 5, 55), (ex, 58), (ex - 4, 55)]), GEODE[0], glow=True)
        s.fill(s.poly([(ex - 2, 50), (ex, 49), (ex + 3, 51), (ex + 2, 55), (ex - 2, 54)]), GEODE[2], glow=True)
        s.px(ex + 1, 51, GEODE[3], glow=True)
        s.fill(s.poly([(ex - 5, 49), (ex, 46), (ex + 6, 49), (ex + 5, 52), (ex + 1, 50), (ex - 3, 53)]), LICHEN[1])   # lichen grown over
        s.pxs([(ex - 3, 49), (ex - 1, 48), (ex + 2, 48), (ex + 4, 50), (ex - 4, 52)], LICHEN[3])
        s.pxs([(ex + 3, 56), (ex - 3, 56)], LICHEN[2])
    s.g("jaw", 118, 62, "head")
    _slab(s, [(116, 60), (148, 60), (146, 72), (118, 72)], TITAN_D, depth=(3, -2), chips=1, seed=17)
    s.fill(s.rect(122, 62, 145, 64), (24, 20, 22))
    for x, ln in ((118, 14), (124, 22), (130, 26), (136, 20), (142, 12)):
        _slab(s, [(x, 70), (x + 7, 70), (x + 5, 70 + ln), (x + 2, 70 + ln - 3)], TITAN, depth=(2, -2), seed=x)  # beard of hanging rock
    # near arm: upper arm, the great crag of a shoulder with burning pines, forearm and fist on the ground
    s.g("weapon", 42, 72)
    _slab(s, [(28, 70), (58, 70), (56, 116), (30, 116)], TITAN_D, chips=3, seed=18)
    s.g("body")
    crag = [(14, 78), (12, 46), (20, 22), (28, 30), (36, 6), (46, 20), (54, 12), (64, 30), (74, 40), (76, 78)]
    _slab(s, crag, TITAN, depth=(6, -6), chips=7, seed=19)
    s.line(36, 8, 30, 40, TITAN[1])
    s.line(54, 14, 58, 44, TITAN[1])
    _lichen(s, 30, 58, 12, 12, 23, 36)
    for x, b, h, sd in ((24, 28, 32, 24), (44, 20, 40, 25), (62, 30, 30, 26), (72, 42, 18, 27)):
        _dead_pine(s, x, b, h, sd)
    s.g("hand_w", 42, 116, "weapon")
    _slab(s, [(24, 117), (60, 117), (62, 154), (26, 154)], TITAN, chips=4, seed=28)
    _crack(s, [(30, 124), (38, 132), (34, 140), (42, 148)], GREY_GLOW[1], GREY_GLOW[3])
    _slab(s, [(14, 154), (64, 154), (66, 188), (16, 188)], TITAN_D, chips=3, seed=29)
    for x in (26, 36, 46, 56):
        s.line(x, 172, x, 187, TITAN_D[0])
    s.ink()
    _dust(s, 40, 11)
    s.shadow(90, 192, 68, 5)
    return s


# ---- Thunderhead ------------------------------------------------------------------------------------------------
STORMC = ramp("383b58", spread=0.5, shift=0.0)
STORMC_D = ramp("262840", spread=0.4, shift=0.0)
FROZEN = [(110, 108, 160), (170, 172, 214), (226, 228, 250), (252, 252, 255)]


def _bolt_arc(s, cx, cy, rx, ry, a0, a1, seed, step=0.16, amp=3.0, gaps=0.18):
    """A zigzag of frozen lightning along part of an ellipse, broken in places."""
    rng = np.random.default_rng(seed)
    a = a0
    prev = None
    k = 0
    while a <= a1:
        r = amp * (1 if k % 2 else -1)
        x = cx + math.cos(a) * (rx + r * 0.5)
        y = cy + math.sin(a) * (ry + r)
        if prev and rng.random() > gaps:
            s.line(prev[0], prev[1], x, y, FROZEN[2], glow=True)
            s.line(prev[0], prev[1] + 1, x, y + 1, FROZEN[0], glow=True)
            if rng.random() < 0.25:
                s.px(round(x), round(y), FROZEN[3], glow=True)
        prev = (x, y)
        a += step
        k += 1


def thunderhead(pose=None, pad=0):
    """Thunderhead, Aurath corrupted: horse and rider of storm cloud gone solid and black, ringed by frozen lightning that never strikes."""
    s = Sprite(214, 186, pose, pad, origin=(0, 10))
    C, CD = STORMC, STORMC_D
    # back half of the ring
    s.g("aura", 104, 110)
    _bolt_arc(s, 104, 110, 98, 22, math.pi, 2 * math.pi, 1)
    # tail of hard black cloud
    s.g("tail", 52, 112)
    for cx, cy, rx, ry in ((40, 112, 14, 9), (24, 120, 11, 8), (12, 132, 8, 6), (6, 144, 5, 4)):
        s.part(s.ellipse(cx, cy, rx, ry), CD, edge=False)
    # far front leg
    s.g("arm_f", 110, 124)
    s.part(s.capsule(110, 124, 116, 146, 6.5, 5), CD, bias=-0.15)
    s.g("fore_f", 116, 146, "arm_f")
    s.part(s.capsule(116, 146, 112, 162, 5, 4), CD, bias=-0.15, edge=False)
    s.part(s.poly([(106, 162), (117, 161), (118, 168), (106, 168)]), CD, flat=True)
    # the horse: a rolling body that breaks into cloud behind, no hind legs
    s.g("body")
    for cx, cy, rx, ry in ((52, 140, 20, 12), (36, 150, 14, 9), (22, 158, 9, 6)):
        s.part(s.ellipse(cx, cy, rx, ry), CD, edge=False)
    for cx, cy, rx, ry in ((68, 122, 30, 20), (98, 114, 30, 22), (118, 110, 18, 18)):
        s.part(s.ellipse(cx, cy, rx, ry), C, edge=False)
    rng = np.random.default_rng(4)
    for _ in range(40):
        x, y = rng.uniform(4, 60), rng.uniform(150, 172)
        if rng.random() < 0.6:
            s.px(round(x), round(y), CD[int(rng.integers(0, 3))])
    # the white lightning spine, frozen and grey
    _crack(s, [(130, 80), (118, 96), (104, 100), (86, 106), (66, 110), (46, 118), (30, 126)], FROZEN[1], FROZEN[3])
    # neck, mane and head
    s.g("neck", 124, 104)
    s.part(s.capsule(124, 106, 144, 70, 15, 10), C)
    s.g("head", 144, 70, "neck")
    s.part(s.poly([(136, 62), (148, 52), (162, 58), (176, 72), (178, 80), (170, 84), (158, 80), (144, 76)]), C, bulge=0.8)
    s.part(s.poly([(146, 54), (148, 40), (154, 52)]), CD)                                              # ears
    s.part(s.poly([(140, 58), (140, 44), (146, 54)]), CD)
    s.fill(s.poly([(154, 60), (161, 61), (160, 64), (154, 63)]), GREY_GLOW[2], glow=True)
    s.px(158, 61, GREY_GLOW[3], glow=True)
    s.pxs([(174, 76), (175, 77)], (10, 10, 18))
    s.g("jaw", 160, 78, "head")
    s.part(s.poly([(158, 78), (172, 82), (164, 88), (154, 84)]), CD)
    s.g("hair", 128, 66, "neck")
    for cx, cy, r in ((136, 56, 7), (128, 64, 7), (120, 74, 7), (114, 86, 6), (110, 96, 5)):
        s.part(s.ellipse(cx - 2, cy, r, r * 0.8), CD, edge=False)
    # near front leg, raised in a prance
    s.g("leg_n", 122, 124)
    s.part(s.capsule(122, 124, 138, 136, 7, 5.5), C)
    s.g("shin_n", 138, 136, "leg_n")
    s.part(s.capsule(138, 136, 132, 152, 5.5, 4.2), C, edge=False)
    s.part(s.poly([(126, 152), (137, 150), (139, 157), (127, 158)]), CD, flat=True)
    # the rider: a cloak of cloud, a crown of frozen lightning, a lance of it
    s.g("cloak", 86, 70)
    for cx, cy, rx, ry in ((76, 74, 12, 9), (64, 80, 11, 8), (52, 86, 9, 7), (42, 92, 7, 5)):
        s.part(s.ellipse(cx, cy, rx, ry), CD, edge=False)
    s.g("rider", 90, 96)
    s.part(s.poly([(80, 66), (98, 64), (104, 96), (82, 100)]), C)
    s.part(s.capsule(92, 98, 104, 112, 6, 5), C)                                                         # leg astride
    _crack(s, [(91, 66), (93, 76), (90, 86), (93, 96)], FROZEN[1], FROZEN[3])
    s.g("rhead", 92, 64, "rider")
    s.part(s.ellipse(92, 56, 8, 9), C)
    s.fill(s.rect(94, 54, 97, 56), GREY_GLOW[2], glow=True)
    s.fill(s.rect(99, 54, 101, 56), GREY_GLOW[2], glow=True)
    for pts in ([(84, 50), (82, 40), (86, 44), (85, 32)], [(90, 47), (91, 36), (94, 41), (95, 28)], [(97, 48), (100, 40), (102, 44), (106, 34)]):
        for a, b in zip(pts, pts[1:]):
            s.line(*a, *b, FROZEN[2], glow=True)
    s.g("weapon", 96, 72, "rider")
    s.part(s.capsule(96, 72, 106, 86, 4.5, 4), C)
    s.g("hand_w", 106, 86, "weapon")
    for (x0, y0), (x1, y1) in (((70, 104), (100, 84)), ((100, 84), (98, 78)), ((98, 78), (150, 44)), ((150, 44), (148, 38)), ((148, 38), (184, 14))):
        s.line(x0, y0, x1, y1, FROZEN[2], glow=True)
        s.line(x0 + 1, y0 + 1, x1 + 1, y1 + 1, FROZEN[0], glow=True)
    s.fill(s.poly([(180, 14), (190, 6), (186, 18)]), FROZEN[3], glow=True)
    s.part(s.capsule(106, 86, 116, 80, 4, 3.5), C, edge=False)
    s.part(s.ellipse(117, 79, 4, 4), C)
    s.g("aura", 104, 110)
    s.ink((12, 12, 22))
    # front half of the ring, over everything
    _bolt_arc(s, 104, 110, 98, 22, 0, math.pi, 2)
    for x, y in ((8, 100), (200, 104), (30, 128), (178, 130)):
        s.fill(s.poly([(x, y - 4), (x + 2, y), (x, y + 4), (x - 2, y)]), FROZEN[2], glow=True)   # sparks hanging still in the air
    s.g("body")
    _dust(s, 30, 12)
    s.shadow(100, 176, 56, 4)
    return s


# ---- Elder Broodmother ------------------------------------------------------------------------------------------
GBARK = ramp("6e675e", spread=0.5, shift=0.02)
GBARK_D = ramp("504a44", spread=0.42, shift=0.02)
SWELL = ramp("948682", spread=0.5, shift=0.02)
FACEB = ramp("a39a8c", spread=0.5, shift=0.02)
YOUNG = [(150, 156, 170), (196, 202, 212), (230, 234, 240), (252, 252, 255)]
BLOSSOM = [(150, 150, 160), (196, 196, 204), (226, 226, 230)]


def _shardling(s, x, y, d=1, k=1.0):
    """One of the Broodmother's pale young: a little glassy shard of a grub with two dark eyes."""
    s.fill(s.poly([(x - 4 * k * d, y), (x, y - 3 * k), (x + 4 * k * d, y - 1), (x + 1 * d, y + 3 * k)]), YOUNG[1])
    s.fill(s.poly([(x - 3 * k * d, y), (x, y - 2 * k), (x + 1 * d, y)]), YOUNG[3])
    s.px(x + 2 * d, y - 1, (30, 26, 34))
    s.px(x + 3 * d, y, (30, 26, 34))
    s.pxs([(x - 2 * d, y + 2), (x, y + 3), (x + 2 * d, y + 2)], YOUNG[0])


def _branch(s, x, y, ang, ln, w, depth, rng, tips):
    """A forking dead branch; tips are collected for blossoms and hanging young."""
    x1, y1 = x + math.cos(ang) * ln, y + math.sin(ang) * ln
    s.part(s.capsule(x, y, x1, y1, w, max(0.8, w * 0.65)), GBARK_D, edge=False)
    if depth == 0:
        tips.append((x1, y1))
        return
    for da in (-0.45, 0.4):
        _branch(s, x1, y1, ang + da + rng.uniform(-0.15, 0.15), ln * rng.uniform(0.62, 0.78), w * 0.65, depth - 1, rng, tips)


def elder_broodmother(pose=None, pad=0):
    """The Elder Broodmother, Elowen corrupted: a bent old bark woman gone grey, a swollen hump of brood on her back,
    shedding pale young from her branches."""
    s = Sprite(192, 200, pose, pad, origin=(0, 16))
    rng = np.random.default_rng(5)
    # the crown of branches, sweeping up and back, blossoms gone grey and young hanging from the tips
    s.g("hair", 120, 50)
    tips = []
    for ang, ln in ((-2.3, 28), (-1.85, 32), (-2.75, 26), (-1.45, 22)):
        _branch(s, 120, 46, ang, ln, 3.4, 3, rng, tips)
    for i, (x, y) in enumerate(tips):
        if i % 3 == 0:
            s.line(x, y, x, y + 6 + i % 4, (120, 120, 128))
            _shardling(s, round(x), round(y + 10 + i % 4), 1 if i % 2 else -1, 1.0)
        else:
            s.pxs([(round(x) - 1, round(y)), (round(x) + 1, round(y)), (round(x), round(y) - 1), (round(x), round(y) + 1)], BLOSSOM[1])
            s.px(round(x), round(y), BLOSSOM[2])
    # far arm, long and knotted
    s.g("arm_f", 124, 80)
    s.part(s.capsule(124, 80, 142, 112, 5, 4), GBARK_D, bias=-0.15)
    s.g("fore_f", 142, 112, "arm_f")
    s.part(s.capsule(142, 112, 160, 128, 4, 3), GBARK_D, bias=-0.15, edge=False)
    for ang, ln in ((-0.3, 13), (0.2, 15), (0.7, 12)):
        s.part(s.capsule(160, 128, 160 + math.cos(ang) * ln, 128 + math.sin(ang) * ln, 1.4, 0.8), GBARK_D, edge=False)
    # root feet peeping out under the hem
    for grp, sub, hx, tone in (("leg_f", "shin_f", 82, GBARK_D), ("leg_n", "shin_n", 110, GBARK)):
        s.g(grp, hx, 160)
        s.part(s.capsule(hx, 160, hx, 176, 7), tone)
        s.g(sub, hx, 176, grp)
        for dx, dy in ((-14, 6), (-6, 8), (4, 8), (14, 5)):
            s.part(s.capsule(hx, 178, hx + dx, 180 + dy, 3.4, 1.4), tone, edge=False)
    # the long bark gown, flaring to a hem of roots and dead moss
    s.g("body")
    s.part(s.poly([(86, 64), (122, 66), (136, 120), (150, 176), (52, 178), (60, 120)]), GBARK_D, bulge=0.3)
    for x0, x1 in ((92, 70), (102, 88), (112, 108), (120, 130)):
        s.line(x0, 72, x1, 176, GBARK_D[0])
    for x0, x1 in ((96, 78), (116, 122)):
        s.line(x0, 74, x1, 170, GBARK_D[3])
    for i, x in enumerate(range(50, 152, 5)):
        ln = 4 + (i * 7) % 8
        s.part(s.poly([(x, 174), (x + 5, 174), (x + 3, 174 + ln), (x + 1, 174 + ln - 2)]), GBARK_D if i % 3 else DEADMOSS, flat=True)
    # the swollen hump of brood on her back, splitting where the young push out
    for cx, cy, rx, ry in ((72, 90, 30, 30), (54, 76, 18, 18), (80, 60, 18, 16), (56, 114, 16, 18), (94, 76, 12, 12)):
        s.part(s.ellipse(cx, cy, rx, ry), SWELL, bulge=1.2)
    for x0, y0, x1, y1 in ((50, 70, 48, 124), (68, 58, 62, 118), (86, 56, 88, 100), (42, 90, 58, 72)):
        s.line(x0, y0, x1, y1, SWELL[1])
    for x, y in ((56, 78), (78, 60), (92, 80), (58, 112), (74, 96)):
        s.fill(s.ellipse(x, y, 6.5, 4.5), (26, 22, 28))
        _shardling(s, x + 1, y + 1, 1, 1.0)
    _crack(s, [(64, 84), (72, 90), (68, 98), (78, 104)], GREY_GLOW[1], GREY_GLOW[3])
    # a shawl of dead moss over the bent shoulders
    s.part(s.poly([(94, 60), (124, 66), (132, 90), (118, 100), (98, 96)]), DEADMOSS, bulge=0.7)
    for x in range(100, 132, 4):
        s.line(x, 94 + (x % 3), x - 1, 100 + (x % 5), DEADMOSS[1])
    s.g("hair", 120, 50)
    for x0, y0, x1, y1 in ((124, 50, 110, 84), (118, 54, 102, 92), (112, 56, 96, 96)):
        s.part(s.capsule(x0, y0, x1, y1, 2.0, 1.0), GBARK_D, edge=False)
    s.px(110, 85, BLOSSOM[1])
    s.px(104, 93, BLOSSOM[1])
    # head: bowed low and forward, a long old face with a hooked nose and jutting chin, grey light for eyes
    s.g("head", 124, 74)
    s.part(s.capsule(118, 76, 128, 70, 6), FACEB, bias=-0.2)                                                     # neck
    s.part(s.poly([(122, 50), (136, 50), (144, 58), (156, 70), (150, 72), (150, 76), (146, 78), (150, 88),
                   (140, 94), (128, 92), (118, 76)]), FACEB)
    s.line(144, 59, 155, 69, FACEB[4])
    s.line(134, 76, 136, 86, FACEB[1])                                                                         # cheek line
    s.line(136, 56, 146, 60, FACEB[0])                                                                          # heavy brow
    s.fill(s.poly([(138, 61), (144, 62), (143, 65), (138, 64)]), GREY_GLOW[2], glow=True)
    s.px(141, 62, GREY_GLOW[3], glow=True)
    s.pxs([(132, 66), (134, 68), (130, 72)], FACEB[1])                                                          # wrinkles
    s.g("jaw", 140, 82, "head")
    s.fill(s.poly([(140, 80), (149, 79), (148, 82), (141, 83)]), (24, 20, 24))
    # near arm reaching forward, a young one clinging to the fingers
    s.g("weapon", 104, 82)
    s.part(s.capsule(104, 82, 116, 116, 6, 5), GBARK)
    s.g("hand_w", 116, 116, "weapon")
    s.part(s.capsule(116, 116, 144, 132, 5, 3.6), GBARK, edge=False)
    for ang, ln in ((-0.5, 14), (-0.1, 17), (0.3, 15), (0.8, 11)):
        s.part(s.capsule(145, 132, 145 + math.cos(ang) * ln, 132 + math.sin(ang) * ln, 1.6, 0.9), GBARK, edge=False)
    s.line(160, 138, 162, 144, (120, 120, 128))
    _shardling(s, 163, 147, 1, 1.2)
    s.ink()
    _dust(s, 34, 13)
    # young already shed, crawling off along the ground
    s.g("body")
    for x, y, d in ((30, 192, -1), (44, 195, 1), (166, 194, 1), (180, 190, 1)):
        _shardling(s, x, y, d, 1.4)
    s.ink()
    s.shadow(100, 196, 62, 5)
    return s


# ---- Tidal Leviathan --------------------------------------------------------------------------------------------
BICE = ramp("22344a", spread=0.5, shift=0.0)
BICE_D = ramp("16222f", spread=0.4, shift=0.0)
ICEHI = [(120, 170, 196), (186, 226, 240), (236, 250, 255)]
HULL = ramp("5a4632", spread=0.45, shift=0.02)
BRONZE = ramp("a07a34", spread=0.55)
SAIL = ramp("8a8a88", spread=0.45, shift=0.0)
SEAW = ramp("1a3c4a", spread=0.45, shift=0.0)


def _chain(s, pts, r0, r1, tones, edge=True, bias=0.0):
    """A thick body along a polyline, tapering from r0 to r1."""
    n = len(pts) - 1
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        ra, rb = r0 + (r1 - r0) * i / n, r0 + (r1 - r0) * (i + 1) / n
        s.part(s.capsule(x0, y0, x1, y1, ra, rb), tones, edge=edge and i == 0, bias=bias)


def _bell(s, x, y, hang=6):
    s.line(x, y - hang, x, y - 2, (60, 50, 40))
    s.part(s.poly([(x - 1.5, y - 2), (x + 1.5, y - 2), (x + 3.5, y + 4), (x - 3.5, y + 4)]), BRONZE, edge=False)
    s.line(x - 3, y + 4, x + 3, y + 4, BRONZE[4])
    s.px(x, y + 5, BRONZE[0])


def tidal_leviathan(pose=None, pad=0):
    """The Tidal Leviathan, Thalassa corrupted: a vast eel of black ice and drowned ships, rising out of the sea, its
    bells ringing out of tune."""
    s = Sprite(232, 200, pose, pad, origin=(0, 8))
    # the sea it rises from (stays put)
    s.g("leg_sea", 116, 186)
    s.part(s.ellipse(116, 188, 112, 9), SEAW)
    # a far coil arching out of the water behind, ship ribs frozen into it
    s.g("tail", 80, 170)
    _chain(s, [(12, 190), (20, 158), (40, 138), (62, 144), (76, 176)], 11, 13, BICE_D, bias=-0.1)
    for x, y in ((22, 160), (32, 146), (46, 140), (58, 144), (68, 156)):
        s.line(x - 6, y - 6, x + 6, y + 8, HULL[2])
        s.line(x - 5, y - 6, x + 7, y + 8, HULL[0])
    s.g("tail2", 20, 158, "tail")
    for x, y in ((18, 142), (30, 128), (44, 124)):
        s.fill(s.poly([(x - 4, y + 8), (x + 4, y + 8), (x - 2, y - 6)]), ICEHI[0])
    # the main body rising, a dorsal ridge of ice shards, a broken mast frozen into the back
    s.g("body")
    body = [(112, 194), (110, 160), (118, 124), (134, 96)]
    _chain(s, body, 22, 17, BICE)
    for (x, y), (x1, y1) in zip(body, body[1:]):
        s.line(x - 12, y - 4, x1 - 10, y1 - 2, ICEHI[0])
    s.line(98, 168, 102, 140, ICEHI[1])
    for x, y, h in ((96, 150, 14), (100, 132, 16), (108, 114, 16), (120, 98, 14)):
        s.fill(s.poly([(x - 4, y + 4), (x + 4, y + 2), (x - 6, y - h)]), ICEHI[0])
        s.line(x - 4, y + 3, x - 6, y - h, ICEHI[2])
    for x, y in ((112, 172), (120, 148), (122, 128)):
        s.line(x - 8, y, x + 8, y - 6, HULL[2])                                                                   # planks frozen in the ice
        s.line(x - 8, y + 1, x + 8, y - 5, HULL[0])
    s.part(s.poly([(116, 124), (120, 126), (82, 34), (79, 35)]), HULL, flat=True)                                 # the mast
    s.part(s.poly([(66, 58), (110, 46), (111, 49), (67, 61)]), HULL, flat=True)                                  # yard
    s.fill(s.poly([(70, 61), (104, 52), (100, 80), (90, 72), (84, 86), (76, 70)]), SAIL[2])                        # torn sail
    s.line(70, 61, 76, 70, SAIL[0])
    s.line(88, 58, 90, 72, SAIL[1])
    for x, y in ((70, 70), (84, 66), (106, 56)):
        _bell(s, x, y)
    for cx, cy, r in ((60, 66, 5), (112, 62, 5)):
        for k in range(3):
            ang = -0.8 + k * 0.8
            s.px(round(cx + math.cos(ang) * r * (1 if cx > 90 else -1)), round(cy + math.sin(ang) * r), GREY_GLOW[1], glow=True)
    # neck, head with frills of ice, and the hinged jaw full of ice teeth
    s.g("neck", 134, 96)
    _chain(s, [(134, 96), (148, 72), (168, 58)], 17, 14, BICE, edge=False)
    s.line(134, 84, 152, 62, ICEHI[0])
    for x, y in ((140, 76), (152, 62)):
        s.fill(s.poly([(x - 4, y + 2), (x + 3, y - 2), (x - 10, y - 14)]), ICEHI[0])
    s.g("head", 168, 58, "neck")
    s.part(s.poly([(158, 46), (182, 38), (206, 42), (222, 52), (218, 58), (196, 60), (170, 66), (160, 62)]), BICE, bulge=0.8)
    s.line(170, 42, 214, 46, ICEHI[1])
    for x, y, h in ((160, 44, 18), (168, 40, 22), (176, 38, 16)):
        s.fill(s.poly([(x, y + 4), (x + 6, y + 2), (x - 6, y - h)]), ICEHI[0])
        s.line(x + 2, y + 2, x - 5, y - h + 2, ICEHI[2])
    s.fill(s.poly([(192, 46), (200, 46), (199, 50), (192, 50)]), GREY_GLOW[2], glow=True)
    s.px(197, 47, GREY_GLOW[3], glow=True)
    for x in range(176, 220, 5):
        s.fill(s.poly([(x, 58), (x + 3, 58), (x + 1.5, 64)]), ICEHI[2])                                          # upper teeth
    s.g("jaw", 172, 62, "head")
    s.part(s.poly([(170, 64), (214, 62), (208, 70), (184, 76), (170, 72)]), BICE_D)
    for x in range(180, 210, 5):
        s.fill(s.poly([(x, 63), (x + 3, 63), (x + 1.5, 58)]), ICEHI[1])
    # a fin of torn sail-cloth and ice on the near side
    s.g("wing", 112, 140)
    s.part(s.poly([(112, 140), (88, 124), (74, 132), (84, 140), (72, 150), (92, 152)]), BICE_D, flat=True)
    for x, y in ((74, 132), (72, 150)):
        s.line(108, 140, x, y, ICEHI[0])
    s.g("body")
    s.ink((8, 16, 26))
    # foam where the body meets the sea
    s.g("leg_sea", 116, 186)
    rng = np.random.default_rng(8)
    for _ in range(60):
        x, y = rng.uniform(8, 224), rng.uniform(180, 196)
        if abs(x - 112) < 30 or abs(x - 18) < 16 or abs(x - 76) < 14 or rng.random() < 0.3:
            s.px(round(x), round(y), (200, 226, 230) if rng.random() < 0.5 else (140, 190, 200))
    s.g("body")
    _dust(s, 30, 14)
    return s


# ---- Hollow King -------------------------------------------------------------------------------------------------
VOIDB = ramp("2c2240", spread=0.45, shift=0.0)
VOIDB_D = ramp("1a1428", spread=0.36, shift=0.0)
VIOLET = [(96, 60, 150), (150, 104, 220), (204, 170, 255), (244, 234, 255)]
IRONC = ramp("4a4650", spread=0.5, shift=0.0)
NIGHT = (8, 6, 14)


def _stars(s, mask_pts, n, seed, cols):
    rng = np.random.default_rng(seed)
    m = s.poly(mask_pts)
    ys, xs = np.where(m)
    if not len(xs):
        return
    for _ in range(n):
        i = int(rng.integers(len(xs)))
        s.rgb[ys[i], xs[i]] = cols[int(rng.integers(len(cols)))]


def hollow_king(pose=None, pad=0):
    """The Hollow King, Nyxara corrupted: a very tall, slender queen wearing Vael-Orrun's iron crown, her starfield face
    gone black but for two lights, a long black train whose stars have gone out."""
    s = Sprite(160, 226, pose, pad, origin=(0, 16))
    # the long train sweeping out behind, a few stars left in it, dim
    s.g("cloak", 80, 62)
    train = [(72, 60), (60, 110), (34, 160), (6, 204), (40, 208), (96, 206), (86, 110)]
    s.part(s.poly(train), VOIDB_D, bulge=0.5)
    _stars(s, [(66, 90), (48, 150), (14, 202), (90, 204), (82, 100)], 26, 3, [(96, 92, 120), (140, 136, 160), VIOLET[0]])
    for (x0, y0), (x1, y1) in (((44, 168), (30, 186)), ((30, 186), (52, 194)), ((60, 140), (44, 168))):
        s.line(x0, y0, x1, y1, (60, 52, 84))                                                                   # a dead star-chart
    # far arm hanging, long fingers
    s.g("arm_f", 90, 70)
    s.part(s.capsule(90, 70, 98, 110, 4, 3.4), VOIDB_D, bias=-0.1)
    s.g("fore_f", 98, 110, "arm_f")
    s.part(s.capsule(98, 110, 100, 146, 3.4, 2.6), VOIDB_D, bias=-0.1, edge=False)
    for dx, ln in ((-2, 12), (0, 15), (2, 13)):
        s.part(s.capsule(100 + dx, 147, 100 + dx * 1.6, 147 + ln, 1.0, 0.7), VOIDB_D, edge=False)
    # the narrow gown to the ground, violet trim, a dead constellation down the front
    s.g("body")
    s.part(s.poly([(70, 60), (92, 60), (96, 110), (108, 206), (56, 206), (66, 110)]), VOIDB, bulge=0.6)
    for x0, x1 in ((76, 68), (84, 84), (90, 100)):
        s.line(x0, 70, x1, 204, VOIDB[1])
    s.line(56, 206, 108, 206, VIOLET[0])
    s.part(s.rect(68, 90, 96, 93), IRONC, flat=True)                                                             # iron girdle
    pts = [(80, 112), (74, 132), (86, 150), (78, 176), (90, 192)]
    for a, b2 in zip(pts, pts[1:]):
        s.line(*a, *b2, (70, 60, 100))
    for x, y in pts:
        s.px(x, y, (150, 146, 170))
    # shoulders: tall iron collar standing up behind the head
    s.part(s.poly([(72, 64), (58, 30), (66, 36), (76, 56)]), IRONC, flat=True, bias=-0.15)
    s.part(s.poly([(90, 64), (104, 28), (98, 36), (86, 56)]), IRONC, flat=True)
    s.line(58, 30, 72, 63, IRONC[4])
    s.part(s.poly([(68, 60), (94, 60), (90, 68), (72, 68)]), VOIDB)
    # head: the face is a hole of night with two lights in it, under the iron crown
    s.g("head", 82, 58)
    s.part(s.capsule(82, 60, 82, 52, 3.4), VOIDB_D)
    s.part(s.ellipse(84, 40, 10, 13), VOIDB, bulge=0.8)                                                           # hood
    s.fill(s.ellipse(87, 41, 6.5, 9.5), NIGHT)
    s.fill(s.rect(86, 38, 88, 40), (236, 234, 250), glow=True)
    s.fill(s.rect(91, 38, 93, 40), (236, 234, 250), glow=True)
    s.pxs([(87, 38), (92, 38)], (255, 255, 255), glow=True)
    # Vael-Orrun's crown of black iron, too big and jagged, cracks of violet light
    s.part(s.poly([(72, 30), (98, 30), (96, 24), (72, 24)]), IRONC, flat=True)
    for i, x in enumerate((72, 77, 82, 87, 92)):
        h = (10, 16, 22, 16, 12)[i]
        s.part(s.poly([(x, 25), (x + 5, 25), (x + 2.5, 25 - h)]), IRONC, flat=True, edge=False)
    _crack(s, [(80, 24), (82, 28), (80, 30)], VIOLET[1], VIOLET[3])
    _crack(s, [(90, 24), (89, 28)], VIOLET[1])
    # near arm lifted, a dead gravity well turning in the palm
    s.g("weapon", 74, 68)
    s.part(s.capsule(74, 68, 96, 90, 4, 3.4), VOIDB)
    s.g("hand_w", 96, 90, "weapon")
    s.part(s.capsule(96, 90, 116, 74, 3.4, 2.6), VOIDB, edge=False)
    for ang, ln in ((-1.4, 10), (-1.0, 13), (-0.6, 13), (-0.2, 10)):
        s.part(s.capsule(117, 73, 117 + math.cos(ang) * ln, 73 + math.sin(ang) * ln, 1.0, 0.7), VOIDB, edge=False)
    s.g("aura", 126, 54, "hand_w")
    ring = s.ellipse(126, 54, 13, 6) & ~s.ellipse(126, 54, 10.5, 4)
    s.fill(ring, VIOLET[0], glow=True)
    s.fill(s.ellipse(126, 54, 7, 7), NIGHT)
    s.fill(s.ellipse(126, 54, 7, 7) & ~s.ellipse(126, 54, 6, 6), VIOLET[1], glow=True)
    s.fill(ring & (s.ys > 54 + s.pad + s.oy), VIOLET[1], glow=True)
    s.px(123, 51, VIOLET[3], glow=True)
    s.g("body")
    s.ink((14, 8, 24))
    _dust(s, 36, 15)
    s.shadow(80, 210, 36, 4)
    return s


def hollow_shade(pose=None, pad=0):
    """A Hollow Shade: one of the two halves the Hollow King splits into, a hooded shred of night with two lights."""
    s = Sprite(70, 92, pose, pad)
    s.g("cloak", 36, 30)
    s.part(s.poly([(30, 26), (12, 60), (4, 84), (20, 80), (28, 88), (38, 80), (46, 86), (50, 60), (44, 28)]), VOIDB_D)
    s.g("arm_f", 44, 36)
    s.part(s.capsule(44, 36, 56, 52, 2.6, 1.8), VOIDB_D, bias=-0.1)
    s.g("body")
    s.part(s.poly([(30, 26), (46, 26), (52, 56), (44, 74), (36, 66), (26, 72), (24, 50)]), VOIDB)
    s.g("head", 38, 26)
    s.part(s.ellipse(39, 18, 9, 10), VOIDB)
    s.fill(s.ellipse(42, 19, 5, 7), NIGHT)
    s.fill(s.rect(41, 17, 42, 18), (236, 234, 250), glow=True)
    s.fill(s.rect(45, 17, 46, 18), (236, 234, 250), glow=True)
    for i, x in enumerate((32, 36, 40, 44)):
        s.part(s.poly([(x, 10), (x + 4, 10), (x + 2, 10 - (5, 8, 9, 6)[i])]), IRONC, flat=True, edge=False)      # half a crown
    s.g("weapon", 34, 34)
    s.part(s.capsule(34, 34, 50, 46, 3, 2.2), VOIDB)
    s.g("hand_w", 50, 46, "weapon")
    for ang in (-0.6, -0.2, 0.2):
        s.part(s.capsule(51, 46, 51 + math.cos(ang) * 9, 46 + math.sin(ang) * 9, 1.0, 0.6), VOIDB, edge=False)
    s.g("body")
    s.ink((14, 8, 24))
    rng = np.random.default_rng(2)
    for _ in range(18):
        x, y = rng.uniform(6, 50), rng.uniform(70, 90)
        s.px(round(x), round(y), VOIDB[int(rng.integers(0, 3))])
    s.shadow(32, 88, 16, 2.4)
    return s


WARDENS = {"mountain_titan": mountain_titan, "thunderhead": thunderhead, "elder_broodmother": elder_broodmother, "tidal_leviathan": tidal_leviathan,
           "hollow_king": hollow_king, "hollow_shade": hollow_shade}
CREATURES.update(WARDENS)
