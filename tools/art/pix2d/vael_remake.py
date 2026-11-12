"""A complete remake of Vael-Orrun, the High King: three new concepts (design only).

Doctor Paris turned down the glass-robe king and its variants (2026-11-12: "make complete remake of him, go crazy"),
so these start from nothing: new heads, bodies, palettes and a bigger scale (about 11 to 12 board cells tall).

- vael_hollow:  the Hollow Sovereign. A hunched four-armed giant of ivory bone in a rotten crimson royal mantle,
                walking on bent beast legs; a long split-jawed skull under a halo of floating black blades; his rib
                cage opened like two doors on the Heartstone.
- vael_eclipse: the Black Sun. The shape the story already gives him in the sky: a head that is a black sun with a
                burning corona and a crown-shaped tear in it, and one vast eye looking out of the tear; a body of
                night sky full of stars, wings of void, long needle-fingered arms.
- vael_throne:  the Throne-Walker. The dead High King still seated on his throne, which has grown eight black glass
                spider legs and carries him to war; a gaunt corpse face under a crown too big for it, a beard of
                chains, the Heartstone burning on his sceptre.
"""
from __future__ import annotations

import math

import numpy as np

from bosses import BOSSES, EYE, GLASS, GLASS_D, GREY_GLOW, MAW, RING, TOOTH, _crack, _dust
from creatures import CREATURES
from kit import Sprite, ramp
from vael_forms import _heart, _six_cracks

IVORY = ramp("c4b8a0", spread=0.6, shift=0.04)
IVORY_D = ramp("8a806e", spread=0.5, shift=0.04)
CRIMSON = ramp("6e1622", spread=0.55, shift=0.03)
CRIMSON_D = ramp("4a0e18", spread=0.45, shift=0.03)
GOLD = ramp("b8903c", spread=0.6, shift=0.03)
OBSID = ramp("2a2434", spread=0.6, shift=0.0)
VOIDR = ramp("1c1430", spread=0.5, shift=0.0)
DEAD = ramp("7c7a6a", spread=0.6, shift=0.03)            # corpse skin
HOT = [(120, 20, 10), (220, 70, 20), (255, 150, 40), (255, 214, 120), (255, 248, 220)]
GOLDEYE = [(150, 70, 10), (240, 160, 40), (255, 230, 140), (255, 255, 235)]
STARS = [(255, 255, 255), (190, 210, 255), (255, 230, 170), (200, 170, 255)]


def _claws(s, x, y, ang, n=4, ln=18, spread=0.35, r=2.0, tones=IVORY, tip=GLASS):
    """Long jointed fingers fanned around angle ang, each with a black glass claw tip."""
    for k in range(n):
        a = ang + (k - (n - 1) / 2) * spread
        mx, my = x + math.cos(a) * ln * 0.55, y + math.sin(a) * ln * 0.55
        a2 = a + 0.35
        ex, ey = mx + math.cos(a2) * ln * 0.5, my + math.sin(a2) * ln * 0.5
        s.part(s.capsule(x, y, mx, my, r, r * 0.8), tones, edge=False)
        s.part(s.capsule(mx, my, ex, ey, r * 0.8, r * 0.5), tones, edge=False)
        s.part(s.poly([(ex - 1.5, ey - 1.5), (ex + 1.5, ey + 1.5), (ex + math.cos(a2 + 0.5) * 7, ey + math.sin(a2 + 0.5) * 7)]),
               tip, flat=True, edge=False)


def _curve(p0, p1, p2, n=16):
    """Points along a quadratic curve."""
    return [((1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t * t * p2[0],
             (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t * t * p2[1]) for t in (i / n for i in range(n + 1))]


def _ribbon(s, pts, w0, w1):
    """A tapering band along a polyline, as a polygon mask."""
    left, right = [], []
    n = len(pts)
    for i, (x, y) in enumerate(pts):
        x0, y0 = pts[max(i - 1, 0)]
        x1, y1 = pts[min(i + 1, n - 1)]
        dx, dy = x1 - x0, y1 - y0
        L = math.hypot(dx, dy) or 1
        nx, ny = -dy / L, dx / L
        w = w0 + (w1 - w0) * i / (n - 1)
        left.append((x + nx * w, y + ny * w))
        right.append((x - nx * w, y - ny * w))
    return s.poly(left + right[::-1])


# ======================================================================================================================
def vael_hollow(pose=None, pad=0):
    """The Hollow Sovereign: a hunched, four-armed giant of ivory bone on bent beast legs, in a rotten crimson mantle
    with gold trim. His long skull juts forward with split jaws full of needles, one gold eye and a third eye opening
    in his brow, under a halo of floating black blades (the crown, broken and orbiting him). His rib cage stands open
    like two doors, and a smaller pair of arms holds them apart around the burning Heartstone."""
    s = Sprite(248, 384, pose, pad, origin=(0, 6))
    rng = np.random.default_rng(21)
    # ---- the mantle, hanging behind the hunched back
    s.g("cloak", 120, 108)
    cape = [(100, 100), (146, 100), (150, 200), (148, 300), (140, 360), (128, 342), (118, 372), (100, 350), (86, 368), (70, 334),
            (52, 370), (40, 336), (24, 352), (30, 270), (56, 170)]
    s.part(s.poly(cape), CRIMSON, bulge=0.7)
    for x0, y0, x1, y1 in ((96, 120, 70, 350), (112, 130, 104, 352), (128, 130, 132, 350), (80, 130, 42, 330)):
        s.line(x0, y0, x1, y1, CRIMSON[0])                                                  # deep folds
        s.line(x0 - 2, y0 + 4, x1 - 4, y1 - 6, CRIMSON[3])
        s.line(x0 - 3, y0 + 8, x1 - 5, y1 - 10, CRIMSON[2])
    s.line(96, 100, 54, 170, GOLD[3])
    s.line(54, 170, 30, 260, GOLD[3])
    s.line(30, 260, 26, 340, GOLD[2])
    s.line(97, 102, 55, 172, GOLD[1])
    for _ in range(40):                                                                      # moth holes and rot
        x, y = int(rng.integers(36, 140)), int(rng.integers(200, 360))
        s.fill(s.ellipse(x, y, 1.5, 1.2) & s.a, CRIMSON_D[0])
    for x0, top, x1 in ((126, 300, 134), (92, 310, 100), (58, 296, 66), (40, 318, 46)):        # rents torn up from the hem
        s.a[s.poly([(x0, top), (x1 - 2, 374), (x0 - 6, 374)])] = False
    # ---- far arm, hanging to the knee with dangling blade fingers
    s.g("arm_f", 122, 122)
    s.part(s.capsule(122, 122, 102, 190, 6.5, 5.5), IVORY_D, bias=-0.15)
    s.part(s.ellipse(102, 190, 6, 6), IVORY_D, bias=-0.15)
    s.g("fore_f", 102, 190, "arm_f")
    s.part(s.capsule(102, 190, 96, 250, 5, 4), IVORY_D, bias=-0.15, edge=False)
    _claws(s, 96, 252, 1.62, 4, 30, 0.22, 1.8, IVORY_D)
    # ---- legs: bent backwards like a beast's, ivory bone with black glass greaves
    for grp, sub, ft, hx, kx, ax, tx, bias, tones in (("leg_f", "shin_f", "foot_f", 108, 128, 104, 124, -0.25, IVORY_D),
                                                     ("leg_n", "shin_n", "foot_n", 128, 152, 128, 150, 0.0, IVORY)):
        s.g(grp, hx, 232)
        s.part(s.capsule(hx, 232, kx, 280, 11, 8), tones, bias=bias)
        s.g(sub, kx, 280, grp)
        s.part(s.ellipse(kx, 280, 8, 8), tones, bias=bias)
        s.part(s.capsule(kx, 280, ax, 332, 6.5, 4.5), tones, bias=bias, edge=False)
        s.part(s.poly([(kx - 6, 290), (kx + 6, 288), (ax + 6, 322), (ax - 2, 326)]), OBSID, flat=True, bias=bias)
        s.part(s.capsule(ax, 332, tx, 366, 4.5, 3.5), tones, bias=bias)                    # the long hind foot
        for d in (-6, 2, 10):
            s.part(s.poly([(tx + d - 2, 364), (tx + d + 4, 364), (tx + d + 10, 374), (tx + d + 6, 376)]), OBSID, flat=True)
    # ---- pelvis and spine, the spine ridged with back-pointing spikes
    s.g("body")
    s.part(s.poly([(92, 206), (110, 200), (122, 214), (112, 236), (98, 232)]), IVORY_D, bias=-0.1)     # far hip blade
    s.part(s.poly([(116, 216), (130, 204), (142, 210), (140, 226), (126, 238), (116, 232)]), IVORY_D)    # near hip blade
    spine = _curve((116, 220), (104, 160), (128, 112), 12)
    for i, (x, y) in enumerate(spine):
        s.part(s.ellipse(x, y, 6, 4.5), IVORY, bias=-0.05)
        if i % 2 == 0 and 2 < i < 12:
            s.part(s.poly([(x - 2, y - 3), (x - 2, y + 3), (x - 16, y - 6)]), OBSID, flat=True)
    # ---- the open chest: a cavity of ember around the Heartstone
    cav = s.ellipse(140, 166, 22, 40)
    s.fill(cav, MAW[0])
    s.fill(s.ellipse(141, 170, 16, 30) & cav, MAW[1])
    s.fill(s.ellipse(142, 170, 10, 20) & cav, (140, 60, 20), glow=True)
    for pts in ([(124, 140), (134, 156), (130, 176), (138, 196)], [(156, 138), (150, 160), (158, 182), (150, 202)]):
        s.line(*pts[0], *pts[1], (180, 40, 30))                                             # veins in the hollow
        s.line(*pts[1], *pts[2], (180, 40, 30))
        s.line(*pts[2], *pts[3], (120, 20, 20))
    _heart(s, 142, 168, 1.1)
    _six_cracks(s, 142, 168, 0.5)
    # ribs: from the spine round the front, and the near side swung open like a door, hooked at the tips
    for i in range(7):
        y = 130 + i * 12
        w = 1 - abs(i - 3) * 0.08
        if i in (0, 6):
            back = _curve((118, y), (132, y - 10), (156, y - 4), 8)
            door = _curve((156, y - 4), (162, y), (160, y + 6), 4)
        else:                                                                                # broken open and splayed forward
            back = _curve((118, y), (124, y - 6), (128, y - 4), 4)
            door = _curve((152, y - 2), (176 * w + 6, y - 14), (190 * w, y - 2), 8)
        for pts, tones, b in ((back, IVORY_D, -0.1), (door, IVORY, 0.05)):
            m = np.zeros((s.h, s.w), bool)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                m |= s.capsule(x0, y0, x1, y1, 2.6 if i not in (0, 6) else 2.0)
            s.part(m, tones, bias=b)
    # the small inner arms, reaching out of the hollow to hold the doors open
    for (sx, sy), (hx, hy) in (((136, 204), (166, 150)), ((146, 204), (172, 186))):
        s.part(s.capsule(sx, sy, (sx + hx) / 2 + 6, (sy + hy) / 2 + 6, 2.4), IVORY_D)
        s.part(s.capsule((sx + hx) / 2 + 6, (sy + hy) / 2 + 6, hx, hy, 2.0), IVORY_D, edge=False)
        for a in (-1.6, -1.1, -0.6):
            s.line(hx, hy, hx + math.cos(a) * 6, hy + math.sin(a) * 6, IVORY[3])
    # ---- collar of black spikes round the neck, and the long neck curving forward
    for k in range(9):
        a = math.pi + 0.25 + k * 0.17
        x0, y0 = 132 + math.cos(a) * 14, 112 + math.sin(a) * 10
        x1, y1 = 132 + math.cos(a) * (40 + (k % 2) * 12), 112 + math.sin(a) * (34 + (k % 2) * 10)
        s.part(s.poly([(x0 - 3, y0), (x0 + 3, y0 + 2), (x1, y1)]), OBSID, flat=True)
    neck = _curve((132, 114), (140, 90), (164, 82), 8)
    for x, y in neck:
        s.part(s.ellipse(x, y, 7, 5.5), IVORY, bias=-0.05)
    # ---- head: halo of blades behind, long skull in profile, split jaws
    s.g("head", 166, 80)
    for k in range(11):                                                                      # the broken crown, orbiting
        a = -math.pi * 0.95 + k * (math.pi * 1.25 / 10)
        cx, cy = 168 + math.cos(a) * 48, 66 + math.sin(a) * 46
        tx, ty = 168 + math.cos(a) * 70, 66 + math.sin(a) * 68
        px_, py_ = -math.sin(a) * 4, math.cos(a) * 4
        blade = s.poly([(cx + px_, cy + py_), (cx - px_, cy - py_), (tx, ty)])
        s.part(blade, GLASS, flat=True)
        s.line(cx + px_, cy + py_, tx, ty, GLASS[4])
        s.px(cx, cy, GOLDEYE[1], glow=True)
    ring = np.zeros((s.h, s.w), bool)
    for k in range(48):
        a = -math.pi * 0.95 + k * (math.pi * 1.25 / 47)
        ring |= s.ellipse(168 + math.cos(a) * 46, 66 + math.sin(a) * 44, 0.8, 0.8)
    s.fill(ring & ~s.a, GOLD[2], glow=True)
    # horns sweeping back from the brow
    for p0, p1, p2, tones in (((160, 58), (134, 24), (104, 30), OBSID), ((168, 56), (150, 18), (122, 10), OBSID)):
        pts = _curve(p0, p1, p2, 10)
        s.part(_ribbon(s, pts, 4.5, 0.6), tones, bias=-0.1 if p0[0] == 160 else 0.05)
    skull = s.poly([(150, 70), (156, 54), (172, 48), (186, 52), (204, 62), (222, 72), (224, 78), (206, 84), (170, 86), (154, 82)])
    s.part(skull, IVORY, bulge=0.8)
    s.line(172, 49, 204, 62, IVORY[4])
    s.line(204, 62, 222, 72, IVORY[4])
    s.fill(s.poly([(174, 60), (186, 58), (190, 68), (178, 70)]), (8, 4, 6))                  # the eye socket
    s.fill(s.rect(181, 62, 186, 66), GOLDEYE[0], glow=True)
    s.fill(s.rect(182, 63, 185, 65), GOLDEYE[1], glow=True)
    s.px(183, 63, GOLDEYE[3], glow=True)
    wound = s.poly([(156, 60), (156, 50), (159, 54), (162, 46), (165, 54), (168, 50), (168, 60)])  # the crown-shaped wound
    s.fill(wound, GOLDEYE[2], glow=True)
    s.fill(s.ellipse(162, 56, 1.4, 3.5) & wound, (20, 6, 4))                                          # a third eye opening in it
    s.px(162, 55, GOLDEYE[3], glow=True)
    for x, y in ((210, 70), (214, 72)):
        s.px(x, y, (8, 4, 6))                                                                # nostril slits
    s.line(176, 74, 200, 72, IVORY[1])                                                       # cheek ridge
    s.line(150, 70, 158, 82, IVORY[0])
    _crack(s, [(186, 66), (190, 74), (188, 80)], EYE[1], EYE[2])                             # fire weeping from the eye
    for x in range(168, 222, 4):                                                             # upper needle teeth
        ln = 6 + (x % 8 == 0) * 6
        s.fill(s.poly([(x - 1, 83), (x + 1.5, 83), (x + 0.3, 83 + ln)]), TOOTH[2])
        s.px(x, 83, TOOTH[4])
    # the jaw: two long mandibles that open apart
    s.g("jaw", 162, 82, "head")
    s.fill(s.poly([(162, 84), (222, 104), (206, 122), (166, 98)]), MAW[1])
    s.fill(s.ellipse(178, 92, 10, 5), MAW[2], glow=True)
    s.fill(s.ellipse(176, 92, 5, 3), MAW[3], glow=True)
    for (x0, y0), (x1, y1), tones, b in (((162, 84), (206, 122), IVORY_D, -0.2), ((162, 86), (224, 104), IVORY, 0.0)):
        s.part(s.capsule(x0, y0, x1, y1, 4.5, 2.2), tones, bias=b)
        for k in range(1, 7):
            t = k / 7
            x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            s.fill(s.poly([(x - 1, y - 2), (x + 1.5, y - 2), (x + 0.3, y - 8 + t * 3)]), TOOTH[2])
    s.line(186, 90, 188, 108, DROOL_GLOW, glow=True)
    s.line(200, 92, 199, 110, DROOL_GLOW, glow=True)
    # ---- near arm: reaching forward, long blade fingers spread
    s.g("weapon", 140, 120)
    s.part(s.capsule(140, 120, 176, 172, 7.5, 6), IVORY)
    s.part(s.ellipse(176, 172, 7, 7), IVORY)
    s.part(s.poly([(140, 112), (160, 116), (166, 138), (146, 136)]), OBSID, flat=True)      # a glass pauldron shard
    s.fill(s.poly([(152, 116), (164, 98), (160, 120)]), OBSID[3])
    s.g("hand_w", 176, 172, "weapon")
    s.part(s.capsule(176, 172, 214, 150, 6, 4.5), IVORY, edge=False)
    _claws(s, 216, 148, -0.35, 4, 34, 0.32, 2.0)
    s.ink((20, 10, 14))
    _dust(s, 40, 21, [(90, 20, 20), (180, 60, 30), (230, 120, 50), (255, 190, 90)])
    s.shadow(126, 376, 74, 6)
    return s


DROOL_GLOW = (255, 196, 120)


# ======================================================================================================================
def vael_eclipse(pose=None, pad=0):
    """The Black Sun: the shape he wears in the sky, come down. His head is a black sun with a burning corona and a
    crown-shaped tear in it, and one vast eye looking out of the tear. His body is night sky, full of stars, fraying
    into tendrils that never touch the ground; void wings with burning edges spread behind; his arms are long and
    thin with needle fingers."""
    s = Sprite(288, 384, pose, pad, origin=(0, 0))
    rng = np.random.default_rng(33)
    VOID = (10, 6, 20)

    def starfill(m, n, seed):
        r = np.random.default_rng(seed)
        ys, xs = np.where(m)
        if not len(xs):
            return
        for _ in range(n):
            i = int(r.integers(len(xs)))
            x, y = xs[i], ys[i]
            s.rgb[y, x] = STARS[int(r.integers(len(STARS)))]
            s.glow[y, x] = True
        for _ in range(n // 12):                                                             # a few bright crossed stars
            i = int(r.integers(len(xs)))
            x, y = xs[i], ys[i]
            for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                if 0 <= x + dx < s.w and 0 <= y + dy < s.h and m[y + dy, x + dx]:
                    s.rgb[y + dy, x + dx] = (255, 255, 255) if (dx, dy) == (0, 0) else (170, 190, 255)
                    s.glow[y + dy, x + dx] = True

    def nebula(m, cx, cy, rx, ry, col, seed):
        r = np.random.default_rng(seed)
        e = s.ellipse(cx, cy, rx, ry) & m
        dither = r.random(e.shape) < 0.45
        s.rgb[e & dither] = col

    def void_part(m, rim=(110, 80, 190), seed=0, stars=40):
        s.fill(m, VOID)
        nebula(m, *(np.array(np.where(m)).mean(1)[::-1]), 18, 30, (34, 16, 54), seed) if m.any() else None
        starfill(m, stars, seed)
        # rim light on the upper-left edges, a burning rim low-right
        up = m & ~np.roll(m, 1, 0)
        left = m & ~np.roll(m, 1, 1)
        right = m & ~np.roll(m, -1, 1)
        s.rgb[up | left] = rim
        s.rgb[right & ~up] = (120, 40, 30)
        s.a |= m
        return m

    # ---- wings of void with burning edges, three to a side
    s.g("cloak", 144, 132)
    for sgn in (-1, 1):
        for k in range(3):
            tip = (144 + sgn * (136 - k * 18), 20 + k * 54)
            mid = (144 + sgn * (78 - k * 8), 128 + k * 12)
            pts = _curve((144 + sgn * 10, 136), mid, tip, 14)
            m = _ribbon(s, pts, 17 - k * 4, 1).copy()
            void_part(m, (90, 60, 160) if sgn < 0 else (70, 50, 130), 40 + k + (sgn > 0) * 5, 20)
            for x, y in pts[4::2]:                                                           # embers along the wing
                s.px(x + sgn * 2, y - 4, HOT[2], glow=True)
    # ---- far arm, raised high and clawing at the sky
    s.g("arm_f", 118, 142)
    void_part(s.capsule(118, 142, 76, 106, 6, 5), seed=51, stars=8)
    s.g("fore_f", 76, 106, "arm_f")
    void_part(s.capsule(76, 106, 62, 54, 5, 3.5), seed=52, stars=6)
    for a in (-2.2, -1.85, -1.5, -1.15):
        x1, y1 = 62 + math.cos(a) * 30, 54 + math.sin(a) * 30
        s.line(62, 54, x1, y1, (90, 70, 150))
        s.line(x1, y1, x1 + math.cos(a + 0.4) * 5, y1 + math.sin(a + 0.4) * 5, (240, 240, 255), glow=True)
    # ---- body: a robe of night sky, fraying into tendrils
    s.g("body")
    robe = s.poly([(118, 128), (170, 128), (184, 200), (204, 290), (84, 290), (104, 200)]).copy()
    for k in range(9):
        x0 = 86 + k * 13
        sway = math.sin(k * 1.7) * 14
        pts = _curve((x0 + 6, 284), (x0 + 6 + sway, 316), (x0 + 6 - sway * 0.5, 352 - (k % 3) * 10), 10)
        robe |= _ribbon(s, pts, 6.5, 0.8)
    void_part(robe, seed=61, stars=170)
    nebula(robe, 150, 230, 26, 40, (44, 18, 60), 62)
    nebula(robe, 128, 180, 14, 22, (30, 20, 70), 63)
    starfill(robe, 60, 64)
    for _ in range(50):                                                                      # the tendril ends go to embers
        x, y = int(rng.integers(84, 206)), int(rng.integers(330, 370))
        if not s.a[min(y, s.h - 1), x]:
            s.px(x, y, HOT[int(rng.integers(0, 3))], glow=True)
    _heart(s, 144, 170, 1.0)
    _six_cracks(s, 144, 170, 0.8)
    # shoulders: two black plates like the edge of an eclipse
    for x0, sgn in ((118, -1), (170, 1)):
        m = s.poly([(x0, 124), (x0 + sgn * 26, 118), (x0 + sgn * 34, 134), (x0 + sgn * 8, 144)])
        s.part(m, OBSID, flat=True, bias=-0.1 if sgn < 0 else 0.05)
        s.line(x0, 124, x0 + sgn * 26, 118, HOT[2], glow=True)
    # ---- head: the black sun
    s.g("head", 144, 118)
    cx, cy, R = 144, 76, 30
    for layer, (col, scale) in enumerate(((HOT[0], 1.0), (HOT[1], 0.72), (HOT[2], 0.48), (HOT[3], 0.26))):
        for k in range(28):
            a = k / 28 * 2 * math.pi + layer * 0.11
            ln = (10 + 14 * abs(math.sin(k * 2.3)) + 6 * (k % 3 == 0)) * scale + 2
            wob = math.sin(k * 3.1) * 0.12
            p0 = (cx + math.cos(a - 0.09) * R, cy + math.sin(a - 0.09) * R)
            p1 = (cx + math.cos(a + 0.09) * R, cy + math.sin(a + 0.09) * R)
            tip = (cx + math.cos(a + wob) * (R + ln), cy + math.sin(a + wob) * (R + ln))
            s.fill(s.poly([p0, p1, tip]), col, glow=True)
    s.fill(s.ellipse(cx, cy, R + 2, R + 2), HOT[4], glow=True)                              # the bright ring
    s.fill(s.ellipse(cx, cy, R, R), (4, 2, 6))
    s.fill(s.ellipse(cx - 6, cy - 6, R - 8, R - 8), (12, 8, 18))
    # the crown-shaped tear, white-hot, and the eye looking out of it
    tear = s.poly([(cx - 21, cy + 14), (cx - 18, cy + 4), (cx - 22, cy - 12), (cx - 13, cy - 2), (cx - 8, cy - 19), (cx - 2, cy - 6),
                   (cx + 6, cy - 20), (cx + 10, cy - 3), (cx + 21, cy - 13), (cx + 18, cy + 4), (cx + 22, cy + 13), (cx + 8, cy + 19),
                   (cx - 4, cy + 17)])
    grow = tear.copy()
    for ax, sh in ((0, 1), (0, -1), (1, 1), (1, -1)):
        grow |= np.roll(tear, sh, ax)
    s.fill(grow, HOT[3], glow=True)
    s.fill(tear, (255, 250, 236), glow=True)
    s.fill(s.ellipse(cx + 2, cy + 3, 15, 13) & tear, (150, 20, 16), glow=True)             # the iris
    s.fill(s.ellipse(cx + 2, cy + 3, 12, 10) & tear, (220, 60, 24), glow=True)
    s.fill(s.ellipse(cx + 2, cy + 3, 8, 7) & tear, (250, 140, 40), glow=True)
    s.fill(s.ellipse(cx + 2, cy + 3, 4, 4) & tear, (255, 214, 120), glow=True)
    s.fill(s.ellipse(cx + 2, cy + 3, 2, 10) & tear, (10, 4, 8))                             # the slit pupil
    s.px(cx - 2, cy, (255, 255, 255), glow=True)
    for pts in ([(cx - 20, cy + 16), (cx - 26, cy + 22), (cx - 24, cy + 28)], [(cx + 20, cy + 16), (cx + 25, cy + 24)],
                [(cx - 6, cy - 16), (cx - 8, cy - 24)], [(cx + 6, cy - 16), (cx + 9, cy - 25)]):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            s.line(x0, y0, x1, y1, HOT[3], glow=True)
    # ---- near arm: reaching forward, needle fingers
    s.g("weapon", 170, 142)
    void_part(s.capsule(170, 142, 204, 204, 6, 5), seed=71, stars=10)
    s.g("hand_w", 204, 204, "weapon")
    void_part(s.capsule(204, 204, 244, 176, 5, 3.5), seed=72, stars=8)
    for a in (-0.9, -0.5, -0.1, 0.3):
        x1, y1 = 244 + math.cos(a) * 32, 176 + math.sin(a) * 32
        s.line(244, 176, x1, y1, (90, 70, 150))
        s.line(x1, y1, x1 + math.cos(a + 0.4) * 5, y1 + math.sin(a + 0.4) * 5, (240, 240, 255), glow=True)
    s.ink((16, 8, 24))
    _dust(s, 60, 33, [HOT[0], HOT[1], HOT[2], HOT[3]])
    s.shadow(144, 378, 40, 4)
    return s


# ======================================================================================================================
def vael_throne(pose=None, pad=0):
    """The Throne-Walker: the dead High King still seated on his throne, which has grown eight legs of black glass and
    carries him to war like a spider. A gaunt corpse face under a crown too big for it, eyes of red fire, a beard of
    chains; the robe crimson and gold gone to rot; the Heartstone burning on the head of his sceptre."""
    s = Sprite(312, 372, pose, pad, origin=(0, 6))
    # ---- far legs (darker)
    def leg(grp, sub, hx, hy, kx, ky, fx, fy, bias, r=7):
        s.g(grp, hx, hy)
        s.part(s.capsule(hx, hy, kx, ky, r, r - 2), OBSID, bias=bias)
        s.part(s.ellipse(kx, ky, r - 1, r - 1), OBSID, bias=bias)
        s.part(s.poly([(kx - 3, ky - 4), (kx + 3, ky - 4), (kx, ky - 16)]), OBSID, flat=True, bias=bias)   # knee spike
        s.g(sub, kx, ky, grp)
        s.part(s.capsule(kx, ky, fx, fy - 10, r - 2, r - 4), OBSID, bias=bias, edge=False)
        s.part(s.poly([(fx - 3, fy - 12), (fx + 3, fy - 12), (fx, fy)]), OBSID, flat=True, bias=bias)
        s.line(kx, ky, fx, fy - 10, EYE[0])                                                  # a red seam of fire
    leg("leg_f", "shin_f", 136, 236, 70, 170, 28, 360, -0.35)
    leg("leg_f2", "shin_f2", 140, 240, 100, 188, 76, 362, -0.3)
    leg("leg_f3", "shin_f3", 168, 240, 226, 186, 250, 362, -0.3)
    leg("leg_f4", "shin_f4", 172, 236, 252, 168, 296, 358, -0.35)
    # ---- the throne back: a fan of spikes shaped like a crown, gems gone dark
    s.g("body")
    back = s.poly([(100, 226), (98, 92), (104, 40), (116, 70), (126, 14), (138, 58), (156, 4), (174, 58), (186, 14), (196, 70),
                   (208, 40), (214, 92), (212, 226)])
    s.part(back, OBSID, bulge=0.6)
    for x, top in ((104, 40), (126, 14), (156, 4), (186, 14), (208, 40)):
        s.line(x, top, x - 2 if x < 156 else x + 2, 100, OBSID[4] if x <= 156 else OBSID[1])
    for x, y in ((116, 96), (156, 70), (196, 96), (126, 150), (186, 150)):
        s.fill(s.poly([(x, y - 5), (x + 4, y), (x, y + 5), (x - 4, y)]), EYE[0], glow=True)
        s.px(x, y - 1, EYE[2], glow=True)
    s.line(98, 92, 104, 40, GOLD[3])
    s.line(212, 226, 214, 92, GOLD[1])
    # ---- the seat and its base, gold-trimmed, a skull on the front
    s.part(s.poly([(92, 214), (222, 214), (226, 258), (88, 258)]), OBSID, flat=True)
    s.line(92, 214, 222, 214, GOLD[3])
    s.line(88, 258, 226, 258, GOLD[1])
    s.part(s.ellipse(157, 240, 10, 9), IVORY)
    s.fill(s.ellipse(153, 239, 2.5, 3), (8, 4, 6))
    s.fill(s.ellipse(161, 239, 2.5, 3), (8, 4, 6))
    for x in range(151, 164, 3):
        s.line(x, 246, x, 249, IVORY[1])
    # ---- the king: robe, lap and knees
    s.part(s.poly([(116, 200), (198, 196), (214, 214), (204, 226), (112, 226)]), CRIMSON)          # lap
    s.part(s.capsule(176, 206, 214, 212, 13, 11), CRIMSON)                                        # near thigh
    s.part(s.capsule(214, 212, 216, 250, 10, 8), CRIMSON, edge=False)                            # shin
    s.part(s.poly([(204, 248), (230, 248), (234, 258), (204, 258)]), OBSID, flat=True)          # iron boot
    s.part(s.poly([(124, 118), (188, 118), (196, 200), (116, 204)]), CRIMSON, bulge=0.8)        # torso
    s.line(156, 122, 156, 200, GOLD[2])
    s.line(124, 118, 116, 204, GOLD[3])
    s.line(188, 118, 196, 200, GOLD[1])
    # withered chest showing through the torn robe
    s.part(s.poly([(140, 124), (172, 124), (166, 160), (146, 160)]), DEAD, bulge=0.6)
    for y in (132, 140, 148):
        s.line(146, y, 166, y, DEAD[0])
    # ---- arms: far one on the armrest gripping it with claws
    s.part(s.capsule(124, 128, 108, 176, 9, 7), CRIMSON_D)
    s.part(s.capsule(108, 176, 106, 206, 6, 5), DEAD, bias=-0.2)
    for a in (1.2, 1.5, 1.8, 2.1):
        s.line(106, 206, 106 + math.cos(a) * 12, 206 + math.sin(a) * 12, DEAD[1])
        s.px(106 + math.cos(a) * 13, 206 + math.sin(a) * 13, TOOTH[3])
    # ---- head: a gaunt corpse king, crown far too big, beard of chains
    s.g("head", 156, 118)
    s.part(s.poly([(142, 100), (172, 100), (174, 118), (140, 118)]), DEAD, bias=-0.2)          # neck
    for x in range(132, 182, 6):                                                               # lank white hair
        s.line(x, 60, x - 4 + (x > 156) * 8, 120 + (x % 12), (186, 182, 170))
    face = s.poly([(136, 54), (178, 54), (182, 76), (176, 98), (164, 112), (150, 112), (138, 98), (132, 76)])
    s.part(face, DEAD, bulge=0.9)
    s.fill(s.poly([(132, 76), (140, 84), (142, 100), (138, 98)]), DEAD[0])                    # sunken cheeks
    s.fill(s.poly([(182, 76), (174, 84), (172, 100), (176, 98)]), DEAD[1])
    for ex in (147, 168):                                                                      # sockets, red fire inside
        s.fill(s.ellipse(ex, 72, 7, 6), (8, 4, 6))
        s.fill(s.ellipse(ex + 1, 73, 2.5, 2), EYE[1], glow=True)
        s.px(ex + 1, 72, EYE[3], glow=True)
        _crack(s, [(ex, 78), (ex - 1, 86), (ex + 1, 94)], EYE[0])
    s.fill(s.poly([(155, 80), (160, 80), (158, 88)]), (8, 4, 6))                              # no nose left
    s.line(140, 64, 154, 68, DEAD[0])                                                          # brow, furrowed
    s.line(174, 64, 162, 68, DEAD[0])
    # the crown: huge, slipping over one eye
    crown = [(126, 62), (128, 34), (136, 46), (142, 18), (150, 40), (158, 8), (166, 40), (174, 18), (180, 46), (188, 30),
             (190, 58)]
    s.part(s.poly(crown), GOLD, flat=True)
    s.fill(s.poly([(126, 56), (190, 52), (190, 60), (126, 64)]), GOLD[1])
    for x in (136, 158, 180):
        s.fill(s.poly([(x, 54), (x + 3, 57), (x, 60), (x - 3, 57)]), (40, 0, 10))              # empty settings
    s.line(128, 34, 126, 62, GOLD[4])
    # the jaw: slack and open, long teeth, chains for a beard
    s.g("jaw", 144, 96, "head")
    s.fill(s.poly([(144, 96), (170, 96), (166, 112), (150, 112)]), MAW[0])
    s.fill(s.ellipse(157, 104, 6, 5), MAW[2], glow=True)
    for x in range(146, 170, 3):
        s.fill(s.poly([(x - 1, 96), (x + 1.4, 96), (x + 0.2, 102)]), TOOTH[2])
    s.part(s.poly([(144, 108), (170, 108), (166, 122), (148, 122)]), DEAD)
    for x in range(148, 168, 3):
        s.fill(s.poly([(x - 1, 109), (x + 1.4, 109), (x + 0.2, 104)]), TOOTH[2])
    for k, x in enumerate(range(146, 170, 4)):                                                # the chain beard
        ln = 22 + (k % 3) * 10
        for y in range(122, 122 + ln, 3):
            s.px(x + (y // 3 % 2), y, (130, 126, 140))
            s.px(x + 1 - (y // 3 % 2), y + 1, (80, 76, 90))
        s.px(x, 122 + ln, GOLD[3])
    # ---- near arm: raising the sceptre with the Heartstone
    s.g("weapon", 186, 126)
    s.part(s.capsule(186, 126, 214, 160, 10, 8), CRIMSON)
    s.g("hand_w", 214, 160, "weapon")
    s.part(s.capsule(214, 160, 228, 126, 6, 5), DEAD, edge=False)
    s.part(s.capsule(232, 196, 234, 54, 3), GOLD)                                               # sceptre shaft
    s.part(s.ellipse(229, 124, 7, 6), DEAD)                                                     # the fist
    for k in range(3):
        s.line(224, 120 + k * 3, 236, 120 + k * 3, DEAD[0])
    s.fill(s.poly([(222, 54), (234, 30), (246, 54), (234, 62)]), GOLD[2])                      # the cage of the head
    _heart(s, 234, 38, 0.9)
    _six_cracks(s, 234, 38, 0.6)
    # ---- near legs, drawn last so they stand in front of the throne
    s.g("body")
    leg("leg_n", "shin_n", 132, 248, 46, 214, 10, 364, 0.0, 8)
    leg("leg_n2", "shin_n2", 146, 254, 112, 228, 104, 366, 0.05, 8)
    leg("leg_n3", "shin_n3", 170, 254, 210, 230, 218, 366, 0.05, 8)
    leg("leg_n4", "shin_n4", 182, 248, 274, 206, 306, 362, 0.0, 8)
    s.ink((18, 10, 14))
    _dust(s, 40, 44, [(90, 20, 20), (180, 60, 30), (230, 120, 50), (255, 190, 90)])
    s.shadow(158, 364, 130, 7)
    return s


REMAKE = {"vael_hollow": vael_hollow, "vael_eclipse": vael_eclipse, "vael_throne": vael_throne}
CREATURES.update(REMAKE)
BOSSES.update(REMAKE)
