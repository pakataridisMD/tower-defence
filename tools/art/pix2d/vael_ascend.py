"""Vael-Orrun, the Ascendant: the High King hanging in the air over his citadel (design only).

Doctor Paris's mood reference (2026-11-12): a demon lord floating, seen almost as a silhouette against a burning
sky; a ragged, spiky outline; horns and a wild mane; eyes of white fire; a chest split open on molten light behind
bars of rib; fire rising from both open hands; a long tattered coat streaming in the wind; long legs hanging.
This is our own figure in that spirit: the body is near-black and lit from behind, so every edge burns with a rim of
orange light, and the crown-shaped wound on his brow (where Oswin's lantern goes) glows white.

id: vael_ascend. About 12 board cells tall with the fire.
"""
from __future__ import annotations

import math

import numpy as np

from bosses import BOSSES, GREY_GLOW, RING, _dust
from creatures import CREATURES
from kit import Sprite, ramp
from vael_remake import _curve, _ribbon

SIL = ramp("2c1c20", spread=0.36, shift=0.02)          # the backlit body: almost black, warm
SIL_D = ramp("1c1216", spread=0.3, shift=0.02)
HOT = [(110, 16, 8), (200, 50, 14), (250, 110, 24), (255, 176, 60), (255, 230, 150), (255, 252, 228)]
RIM_T = (255, 150, 64)                                   # edge facing up into the light
RIM_S = (226, 84, 36)                                    # side edges
RIM_B = (120, 32, 22)                                    # under edges
EYES = (255, 244, 214)
INK = (14, 6, 8)


def _flame(s, x, y, h, w, seed):
    """A tall pillar of fire rising from (x, y): wavering tongues of five heats, hottest at the root."""
    rng = np.random.default_rng(seed)
    for layer, col in enumerate(HOT[1:]):
        sc = 1.0 - layer * 0.18
        for k in range(7):
            dx = (k - 3) * w * 0.24 * sc
            hh = h * sc * (0.6 + 0.4 * rng.random()) * (1.0 if k in (2, 3, 4) else 0.55)
            ww = w * 0.3 * sc + 1
            ph = rng.uniform(0, 6.28)
            pts = []
            for j in range(9):                                                            # a wavering tongue
                t = j / 8
                off = math.sin(ph + t * 5) * w * 0.25 * t
                half = ww * (1 - t) ** 0.8
                pts.append((x + dx * (1 - 0.5 * t) + off - half, y - hh * t))
            right = [(px_ + 2 * ww * (1 - j / 8) ** 0.8, py_) for j, (px_, py_) in enumerate(pts)]
            s.fill(s.poly(pts + right[::-1]), col, glow=True)
        s.fill(s.ellipse(x, y - 2, w * 0.6 * sc + 1, w * 0.3 * sc + 1), col, glow=True)
    for _ in range(14):                                                                   # sparks flying off the top
        s.px(x + rng.uniform(-w, w), y - h * rng.uniform(0.6, 1.25), HOT[int(rng.integers(2, 5))], glow=True)


def _shards(s, pts, tones, seed, n=7, ln=(10, 26), down=True):
    """Ragged triangular shreds hanging off a line of points (a sleeve, a hem)."""
    rng = np.random.default_rng(seed)
    for i in range(len(pts) - 1):
        (x0, y0), (x1, y1) = pts[i], pts[i + 1]
        for k in range(n):
            t = (k + rng.random()) / n
            bx, by = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            L = rng.uniform(*ln)
            a = (math.pi / 2 if down else -math.pi / 2) + rng.uniform(-0.45, 0.45)
            s.fill(s.poly([(bx - 2.5, by), (bx + 2.5, by), (bx + math.cos(a) * L, by + math.sin(a) * L)]), tones[int(rng.integers(1, 3))])
    return s


def vael_ascend(pose=None, pad=0):
    """Vael-Orrun, the Ascendant: floating, arms spread, fire in both hands, the chest split on molten light."""
    s = Sprite(300, 440, pose, pad, origin=(0, 40))
    cx = 150
    # ---- coat tails streaming out to the right in the wind, behind everything
    s.g("cloak", cx, 200)
    tail = s.poly([(132, 196), (172, 196), (196, 240), (236, 280), (282, 318), (250, 316), (262, 336), (226, 322), (232, 350),
                   (196, 318), (190, 352), (170, 304), (150, 300)])
    s.fill(tail, SIL_D[1])
    s.a |= tail
    _shards(s, [(196, 318), (226, 322), (262, 336)], SIL_D, 4, 4, (8, 22))
    for x0, y0, x1, y1 in ((176, 220, 270, 318), (170, 236, 228, 330), (160, 240, 196, 340)):
        s.line(x0, y0, x1, y1, SIL_D[0])
    # a thin tail, curling up behind the left leg, a barb at the tip
    s.g("tail", 138, 230)
    tl = _curve((138, 230), (88, 270), (98, 330), 14) + _curve((98, 330), (104, 352), (90, 358), 6)[1:]
    s.fill(_ribbon(s, tl, 3.5, 1.2), SIL[1])
    s.fill(s.poly([(84, 352), (96, 356), (86, 368)]), SIL[2])
    # ---- legs, long and hanging, toes pointed down
    for grp, sub, hx, kx, ky, fx, fy, tone in (("leg_f", "shin_f", 140, 132, 300, 128, 376, SIL[1]),
                                               ("leg_n", "shin_n", 160, 168, 296, 164, 382, SIL[2])):
        s.g(grp, hx, 240)
        s.fill(s.capsule(hx, 240, kx, ky, 9, 6.5), tone)
        s.g(sub, kx, ky, grp)
        s.fill(s.capsule(kx, ky, fx, fy - 8, 6.5, 4), tone)
        s.fill(s.poly([(fx - 4, fy - 12), (fx + 4, fy - 12), (fx + 1, fy + 4)]), tone)    # a pointed, clawed foot
        s.a |= s.capsule(hx, 240, kx, ky, 9, 6.5) | s.capsule(kx, ky, fx, fy - 8, 6.5, 4)
        _shards(s, [(kx - 6, ky + 4), (kx + 6, ky + 4)], SIL, 11 + hx, 3, (6, 16))           # torn wraps at the knee
    # ---- the coat's front: split down the middle, ragged hem of shards
    s.g("body")
    coat = s.poly([(126, 186), (174, 186), (186, 230), (178, 268), (164, 254), (156, 290), (146, 252), (134, 280), (124, 246), (116, 228)])
    s.fill(coat, SIL[1])
    s.a |= coat
    s.fill(s.poly([(150, 190), (174, 186), (186, 230), (178, 268), (164, 254), (154, 230)]), SIL[2])
    _shards(s, [(116, 228), (134, 280)], SIL, 5, 4, (10, 24))
    _shards(s, [(164, 254), (178, 268), (186, 236)], SIL, 6, 4, (10, 26))
    s.line(150, 190, 152, 280, SIL_D[0])
    # ---- torso: a tall V, the chest split on a column of molten light behind bars of rib
    torso = s.poly([(112, 108), (188, 108), (182, 140), (170, 192), (130, 192), (118, 140)])
    s.fill(torso, SIL[2])
    s.a |= torso
    s.fill(s.poly([(112, 108), (150, 106), (150, 192), (130, 192), (118, 140)]), SIL[1])
    core = s.ellipse(150, 152, 14, 38)
    for r, col in ((1.0, HOT[0]), (0.8, HOT[1]), (0.6, HOT[2]), (0.4, HOT[3]), (0.22, HOT[4]), (0.1, HOT[5])):
        s.fill(s.ellipse(150, 152, 14 * r + 0.5, 38 * r + 0.5) & core, col, glow=True)
    for k in range(7):                                                                    # rib bars across the light
        y = 122 + k * 9
        w = 15 - abs(k - 3) * 1.6
        s.fill(s.poly([(150 - w - 4, y), (150 - 3, y + 3), (150 + 3, y + 3), (150 + w + 4, y), (150 + w + 4, y + 3),
                       (150 + 3, y + 6), (150 - 3, y + 6), (150 - w - 4, y + 3)]), SIL[2])
    s.fill(s.rect(146, 112, 154, 116), SIL[1])
    for k, col in enumerate(RING):                                                       # the six stolen colours, faint, in the core
        s.px(144 + k * 2.4, 150 + (k % 2) * 6, col, glow=True)
    # ---- the spiked collar: long blades sweeping up and out from both shoulders
    for sgn in (-1, 1):
        for k in range(7):
            a = -math.pi / 2 + sgn * (0.25 + k * 0.2)
            bx, by = cx + sgn * (18 + k * 4), 104 + k * 1.5
            L = 30 + (k % 3) * 12 - k * 1.5
            tip = (bx + math.cos(a) * L, by + math.sin(a) * L)
            s.fill(s.poly([(bx - 3, by + 2), (bx + 3, by + 2), tip]), SIL[1 + (k % 2)])
    # ---- head: a long demon skull, horns, a wild mane of spikes behind it
    s.g("head", cx, 104)
    mrng = np.random.default_rng(17)
    for k in range(19):                                                                   # the mane, wild and uneven
        a = -math.pi / 2 + (k - 9) * 0.17 + mrng.uniform(-0.08, 0.08)
        L = mrng.uniform(8, 34) * (1.0 - abs(k - 9) * 0.03)
        tip = (cx + math.cos(a) * (L + 16), 74 + math.sin(a) * (L + 16))
        s.fill(s.poly([(cx + math.cos(a - 0.12) * 12, 74 + math.sin(a - 0.12) * 12),
                       (cx + math.cos(a + 0.12) * 12, 74 + math.sin(a + 0.12) * 12), tip]), SIL_D[2])
    for sgn in (-1, 1):                                                                   # horns curving up and in
        pts = _curve((cx + sgn * 10, 62), (cx + sgn * 34, 44), (cx + sgn * 20, 10), 12)
        s.fill(_ribbon(s, pts, 5, 0.7), SIL[2])
    head = s.poly([(cx - 13, 58), (cx + 13, 58), (cx + 16, 72), (cx + 11, 90), (cx + 4, 100), (cx - 4, 100), (cx - 11, 90), (cx - 16, 72)])
    s.fill(head, SIL[2])
    s.a |= head
    s.fill(s.poly([(cx - 13, 58), (cx, 58), (cx, 100), (cx - 4, 100), (cx - 11, 90), (cx - 16, 72)]), SIL[1])
    s.fill(s.poly([(cx - 13, 74), (cx - 3, 79), (cx - 4, 82), (cx - 12, 79)]), EYES, glow=True)      # eyes of white fire,
    s.fill(s.poly([(cx + 13, 74), (cx + 3, 79), (cx + 4, 82), (cx + 12, 79)]), EYES, glow=True)      # slanted hard
    s.pxs([(cx - 12, 75), (cx + 12, 75), (cx - 10, 80), (cx + 10, 80)], HOT[3], glow=True)
    wound = s.poly([(cx - 4, 70), (cx - 4, 64), (cx - 2, 66), (cx, 62), (cx + 2, 66), (cx + 4, 64), (cx + 4, 70)])
    s.fill(wound, GREY_GLOW[3], glow=True)                                                # the crown-shaped wound
    s.g("jaw", cx, 90, "head")
    s.fill(s.poly([(cx - 6, 90), (cx + 6, 90), (cx + 3, 96), (cx - 3, 96)]), HOT[2], glow=True)      # a mouth of embers
    for x in (cx - 4, cx - 1, cx + 2):
        s.line(x, 90, x + 1, 94, SIL_D[0])
    # ---- arms spread wide: the left raised high, the right held out, fire rising from both palms
    for grp, sub, (sx, sy), (ex, ey), (hx, hy), fire in (("arm_f", "fore_f", (116, 114), (78, 102), (52, 76), (48, 66, 96, 22)),
                                                         ("weapon", "hand_w", (184, 116), (226, 126), (258, 108), (262, 100, 84, 20))):
        s.g(grp, sx, sy)
        upper = s.capsule(sx, sy, ex, ey, 11, 8)
        s.fill(upper, SIL[2])
        s.a |= upper
        _shards(s, [(sx, sy + 6), (ex, ey + 6)], SIL, sx, 3, (8, 18))
        s.g(sub, ex, ey, grp)
        fore = s.capsule(ex, ey, hx, hy, 8, 5.5)
        s.fill(fore, SIL[2])
        s.a |= fore
        _shards(s, [(ex, ey + 4), ((ex + hx) / 2, (ey + hy) / 2 + 4)], SIL, ex, 3, (8, 20))
        ang = math.atan2(hy - ey, hx - ex)
        for k in range(5):                                                                # a spread hand of long claws
            a = ang - 1.2 + k * 0.6
            fx, fy = hx + math.cos(a) * 16, hy + math.sin(a) * 16
            s.fill(s.capsule(hx, hy, fx, fy, 2, 1), SIL[2])
            s.line(fx, fy, fx + math.cos(a - 0.5) * 6, fy + math.sin(a - 0.5) * 6, SIL[3])
        s.fill(s.ellipse(hx, hy, 6, 6), SIL[2])
        _flame(s, *fire, seed=sx)
    s.g("body")
    EDGE = (150, 46, 24)
    for (x0, y0), (x1, y1) in (((112, 108), (118, 140)), ((118, 140), (130, 192)), ((188, 108), (182, 140)), ((182, 140), (170, 192)),
                               ((150, 190), (152, 280)), ((174, 186), (186, 230)), ((126, 186), (116, 228))):
        s.line(x0, y0, x1, y1, EDGE)                                                     # inner edges catch the backlight too
    vrng = np.random.default_rng(29)
    for _ in range(9):                                                                    # dim ember veins in the hide
        x, y = vrng.uniform(120, 180), vrng.uniform(110, 260)
        pts = [(x, y)]
        for j in range(4):
            x, y = x + vrng.uniform(-5, 5), y + vrng.uniform(4, 9)
            pts.append((x, y))
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            if s.a[int(y1), int(x1)] and not s.glow[int(y1), int(x1)]:
                s.line(x0, y0, x1, y1, (96, 22, 14))
    # ---- backlight: every edge burns, brightest where it faces up into the light, warmer near the fires
    a = s.a & ~s.glow
    up = a & ~np.roll(s.a, 1, 0)
    dn = a & ~np.roll(s.a, -1, 0)
    lf = a & ~np.roll(s.a, 1, 1)
    rt = a & ~np.roll(s.a, -1, 1)
    s.rgb[dn] = RIM_B
    s.rgb[(lf | rt) & ~up] = RIM_S
    s.rgb[up] = RIM_T
    inner = a & ~(up | dn | lf | rt) & ~np.roll(s.a, 2, 0)
    s.rgb[inner] = (170, 60, 30)
    ys, xs = np.mgrid[0:s.h, 0:s.w]
    for fx, fy in (s.fw(48, 66), s.fw(262, 100)):
        d = np.hypot(xs - fx, ys - fy)
        k = np.clip(1 - d / 70, 0, 1)[..., None] * 0.55
        m = a & (d < 70)
        s.rgb[m] = (s.rgb[m] * (1 - k[m]) + np.array([230, 110, 40]) * k[m]).astype(np.uint8)
    s.ink(INK)
    _dust(s, 70, 3, [HOT[1], HOT[2], HOT[3], HOT[4]])
    s.shadow(150, 396, 40, 3)  # floats well above it
    return s


# ---- the bare version (Doctor Paris, 2026-11-12): no coat, no crown wound, no fire; naked dark muscled hide
FLESH = [(20, 10, 14), (44, 24, 28), (66, 37, 39), (90, 53, 50), (122, 76, 66)]
BONE = [(30, 24, 24), (64, 52, 48), (108, 94, 84), (154, 140, 124), (204, 192, 172)]


def _nrm(x0, y0, x1, y1):
    """Unit normal of a segment, turned to face the light (up, then left)."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    if ny > 0.15 or (abs(ny) <= 0.15 and nx > 0):
        nx, ny = -nx, -ny
    return nx, ny, dx / L, dy / L


def _mlimb(s, x0, y0, x1, y1, r0, r1, belly=0.38, bk=1.0):
    """A hard-muscled limb in flat planes: dark base, lit side, a bulging belly with a hot spot, a seam on the shadow side."""
    m = s.capsule(x0, y0, x1, y1, r0, r1)
    s.fill(m, FLESH[1])
    s.a |= m
    nx, ny, ux, uy = _nrm(x0, y0, x1, y1)
    lit = s.capsule(x0 + nx * r0 * 0.4, y0 + ny * r0 * 0.4, x1 + nx * r1 * 0.4, y1 + ny * r1 * 0.4, r0 * 0.62, r1 * 0.62) & m
    s.fill(lit, FLESH[2])
    L = math.hypot(x1 - x0, y1 - y0)
    bx, by = x0 + (x1 - x0) * belly, y0 + (y1 - y0) * belly
    r = r0 + (r1 - r0) * belly
    rot = math.atan2(uy, ux)
    s.fill(s.ellipse(bx + nx * r * 0.3, by + ny * r * 0.3, L * 0.26 * bk, r * 0.62, rot) & m, FLESH[3])
    s.fill(s.ellipse(bx + nx * r * 0.55, by + ny * r * 0.55, L * 0.12 * bk, r * 0.22, rot) & m, FLESH[4])
    for o in (0.45, 0.55):
        s.line(bx - ux * L * 0.22 - nx * r * o, by - uy * L * 0.22 - ny * r * o,
               bx + ux * L * 0.34 - nx * r * o, by + uy * L * 0.34 - ny * r * o, FLESH[0])     # the seam under the belly
    return m


def _bclaw(s, hx, hy, ang, n=5, ln=17):
    """A spread hand: a knuckled palm and long hooked bone claws."""
    s.fill(s.ellipse(hx, hy, 7, 6, ang), FLESH[2])
    s.fill(s.ellipse(hx - 1, hy - 2, 4, 3, ang), FLESH[3])
    for k in range(n):
        a = ang - 1.1 + k * 0.55
        mx, my = hx + math.cos(a) * 8, hy + math.sin(a) * 8
        fx, fy = hx + math.cos(a) * ln, hy + math.sin(a) * ln
        s.fill(s.capsule(hx, hy, mx, my, 2.6, 2), FLESH[2])                                    # finger
        s.fill(s.capsule(mx, my, fx, fy, 2, 0.6), BONE[2])                                      # claw
        s.line(fx, fy, fx + math.cos(a - 0.7) * 5, fy + math.sin(a - 0.7) * 5, BONE[3])          # the hook


def vael_bare(pose=None, pad=0):
    """Vael-Orrun, bare: the same floating pose, stripped to a naked hide of dark, hard muscle."""
    s = Sprite(300, 440, pose, pad, origin=(0, 40))
    cx = 150
    # ---- a thin tail, curling down behind the far leg, a barb at the tip
    s.g("tail", 146, 232)
    tl = _curve((146, 232), (92, 268), (96, 330), 14) + _curve((96, 330), (102, 354), (88, 360), 6)[1:]
    s.fill(_ribbon(s, tl, 4.5, 1.4), FLESH[1])
    s.fill(_ribbon(s, tl[:10], 2.0, 0.8), FLESH[2])
    s.fill(s.poly([(80, 352), (96, 358), (84, 372)]), BONE[2])
    # ---- hips, under the thighs
    s.g("body")
    hips = s.poly([(128, 194), (172, 194), (178, 214), (150, 234), (122, 214)])
    s.fill(hips, FLESH[1])
    s.a |= hips
    # ---- legs: heavy thighs, long hanging shins, clawed feet pointed down
    for grp, sub, (hx, hy), (kx, ky), (ax, ay), fs in (("leg_f", "shin_f", (137, 214), (129, 286), (125, 346), -1),
                                                       ("leg_n", "shin_n", (163, 214), (170, 284), (168, 344), 1)):
        s.g(grp, hx, hy)
        _mlimb(s, hx, hy, kx, ky, 18, 11, belly=0.38)
        s.fill(s.ellipse(kx - fs * 3, ky - 13, 6, 8) & s.capsule(hx, hy, kx, ky, 18, 11), FLESH[3 if fs < 0 else 2])  # teardrop above the knee
        s.line(hx + fs * 2, hy + 14, kx + fs * 4, ky - 6, FLESH[0])                            # the split between the thigh muscles
        s.g(sub, kx, ky, grp)
        s.fill(s.ellipse(kx, ky, 10, 8), FLESH[2])
        s.fill(s.ellipse(kx - 2, ky - 1, 5, 4), FLESH[3])                                        # kneecap
        _mlimb(s, kx, ky + 4, ax, ay, 11, 5, belly=0.26, bk=0.85)                                # calf
        s.fill(s.poly([(ax - 5, ay - 2), (ax + 5, ay - 2), (ax + 3, ay + 16), (ax - 1, ay + 20)]), FLESH[1])
        s.fill(s.poly([(ax - 4, ay - 2), (ax, ay - 2), (ax - 1, ay + 16)]), FLESH[2])
        for k in (-3, 0, 3):                                                                     # toe claws hanging
            s.fill(s.poly([(ax + k - 1.5, ay + 16), (ax + k + 1.5, ay + 16), (ax + k, ay + 28 - abs(k))]), BONE[2])
    s.g("body")
    s.line(150, 222, 150, 240, FLESH[0])                                                         # the crease between the thighs
    # ---- torso: a broad V of muscle, the sternum split on molten light behind bars of rib
    torso = s.poly([(102, 108), (198, 108), (190, 140), (170, 198), (130, 198), (110, 140)])
    s.fill(torso, FLESH[1])
    s.a |= torso
    s.fill(s.poly([(102, 108), (150, 106), (150, 198), (130, 198), (110, 140)]), FLESH[2])
    s.line(129, 200, 147, 228, FLESH[0])                                                         # the hip lines, a hard V
    s.line(171, 200, 153, 228, FLESH[0])
    s.line(128, 198, 146, 224, FLESH[3])
    for sgn, base, top in ((-1, 2, 3), (1, 1, 2)):                                               # obliques over the flanks
        s.fill(s.poly([(150 + sgn * 34, 150), (150 + sgn * 20, 158), (150 + sgn * 18, 198), (150 + sgn * 22, 202), (150 + sgn * 30, 182)]),
               FLESH[base])
        for y in (148, 157, 166):                                                                # serratus fingers
            s.line(150 + sgn * 36, y, 150 + sgn * 26, y + 5, FLESH[0])
            s.line(150 + sgn * 35, y + 2, 150 + sgn * 28, y + 6, FLESH[top])
    s.fill(s.ellipse(150, 177, 18, 26) & s.rect(130, 152, 171, 202), FLESH[0])                 # the abdomen: three pairs of rounded slabs
    for row in range(3):
        y = 164 + row * 12
        for sgn in (-1, 1):
            x = 150 + sgn * 8
            s.fill(s.ellipse(x, y, 7, 5.5), FLESH[2 if sgn < 0 else 1])
            s.fill(s.ellipse(x - 1.5, y - 1.5, 4.5, 3), FLESH[3 if sgn < 0 else 2])
            if sgn < 0:
                s.px(x - 3, y - 3, FLESH[4])
    for sgn, base, top, hi in ((-1, 2, 3, 4), (1, 1, 2, 3)):                                     # pectorals: lit tops, deep shadow under
        pts = [(150 + sgn * 2, 110), (150 + sgn * 46, 112), (150 + sgn * 40, 140), (150 + sgn * 18, 152), (150 + sgn * 2, 146)]
        pec = s.poly(pts)
        s.fill(pec, FLESH[base - 1])
        s.fill(s.ellipse(150 + sgn * 22, 128, 21, 15) & pec, FLESH[base])                      # a rounded slab of muscle
        s.fill(s.ellipse(150 + sgn * 25, 124, 14, 8, -sgn * 0.15) & pec, FLESH[top])
        s.fill(s.ellipse(150 + sgn * 28, 121, 6, 3, -sgn * 0.15) & pec, FLESH[hi])
        s.line(150 + sgn * 4, 110, 150 + sgn * 40, 111, FLESH[0])                                # the collarbone shadow
        for o in (0, 1, 2):
            s.line(150 + sgn * 2, 146 + o, 150 + sgn * 18, 152 + o, FLESH[0])
            s.line(150 + sgn * 18, 152 + o, 150 + sgn * 40, 140 + o, FLESH[0])
    core = s.ellipse(150, 132, 9, 22)
    for r, col in ((1.0, HOT[0]), (0.8, HOT[1]), (0.6, HOT[2]), (0.4, HOT[3]), (0.22, HOT[4]), (0.1, HOT[5])):
        s.fill(s.ellipse(150, 132, 9 * r + 0.5, 22 * r + 0.5) & core, col, glow=True)
    for k in range(5):                                                                           # rib bars across the light
        y = 116 + k * 7
        w = 10 - abs(k - 2) * 1.5
        s.fill(s.poly([(150 - w - 3, y), (150, y + 3), (150 + w + 3, y), (150 + w + 3, y + 3), (150, y + 6), (150 - w - 3, y + 3)]),
               BONE[1])
        s.line(150 - w - 3, y, 150, y + 3, BONE[2])
    for k, col in enumerate(RING):                                                              # the six stolen colours, faint
        s.px(145 + k * 2, 128 + (k % 2) * 8, col, glow=True)
    vrng = np.random.default_rng(29)
    for _ in range(7):                                                                           # ember cracks spreading from the core
        a = vrng.uniform(0, 6.28)
        x, y = 150 + math.cos(a) * 10, 132 + math.sin(a) * 22
        for j in range(3):
            nx_, ny_ = x + math.cos(a) * 5 + vrng.uniform(-2, 2), y + math.sin(a) * 5 + vrng.uniform(-2, 2)
            s.line(x, y, nx_, ny_, HOT[1] if j else HOT[2], glow=True)
            x, y = nx_, ny_
    # ---- bone spines breaking out of the shoulders and back
    for sgn in (-1, 1):
        for k in range(5):
            a = -math.pi / 2 + sgn * (0.3 + k * 0.24)
            bx, by = cx + sgn * (20 + k * 6), 104 + k * 2
            L = 26 + (k % 2) * 12 - k * 2
            tip = (bx + math.cos(a) * L, by + math.sin(a) * L)
            s.fill(s.poly([(bx - 3, by + 2), (bx + 3, by + 2), tip]), BONE[1])
            s.line(bx + sgn * -2, by, tip[0], tip[1], BONE[2])
    # ---- neck and traps
    s.fill(s.poly([(136, 92), (164, 92), (176, 110), (124, 110)]), FLESH[1])
    s.fill(s.poly([(136, 92), (150, 92), (150, 110), (124, 110)]), FLESH[2])
    s.line(140, 96, 148, 112, FLESH[3])
    # ---- head: a long demon skull of dark hide, heavy brow, horns, a wild mane behind
    s.g("head", cx, 104)
    mrng = np.random.default_rng(17)
    for k in range(19):
        a = -math.pi / 2 + (k - 9) * 0.17 + mrng.uniform(-0.08, 0.08)
        L = mrng.uniform(8, 34) * (1.0 - abs(k - 9) * 0.03)
        tip = (cx + math.cos(a) * (L + 16), 74 + math.sin(a) * (L + 16))
        s.fill(s.poly([(cx + math.cos(a - 0.12) * 12, 74 + math.sin(a - 0.12) * 12),
                       (cx + math.cos(a + 0.12) * 12, 74 + math.sin(a + 0.12) * 12), tip]), SIL_D[2])
    for sgn in (-1, 1):
        pts = _curve((cx + sgn * 10, 62), (cx + sgn * 34, 44), (cx + sgn * 20, 10), 12)
        s.fill(_ribbon(s, pts, 5, 0.7), BONE[1])
        s.fill(_ribbon(s, pts[:9], 2, 0.6), BONE[2])
    head = s.poly([(cx - 13, 58), (cx + 13, 58), (cx + 16, 72), (cx + 11, 90), (cx + 4, 100), (cx - 4, 100), (cx - 11, 90), (cx - 16, 72)])
    s.fill(head, FLESH[1])
    s.a |= head
    s.fill(s.poly([(cx - 13, 58), (cx, 58), (cx, 100), (cx - 4, 100), (cx - 11, 90), (cx - 16, 72)]), FLESH[2])
    s.fill(s.poly([(cx - 15, 70), (cx, 76), (cx + 15, 70), (cx + 14, 74), (cx, 80), (cx - 14, 74)]), FLESH[3])  # heavy V brow
    s.fill(s.poly([(cx - 12, 64), (cx - 2, 70), (cx - 2, 72), (cx - 13, 68)]), FLESH[3])     # ridges up the forehead
    s.fill(s.poly([(cx + 12, 64), (cx + 2, 70), (cx + 2, 72), (cx + 13, 68)]), FLESH[2])
    s.fill(s.poly([(cx - 13, 76), (cx - 3, 81), (cx - 4, 84), (cx - 12, 81)]), EYES, glow=True)     # eyes of white fire
    s.fill(s.poly([(cx + 13, 76), (cx + 3, 81), (cx + 4, 84), (cx + 12, 81)]), EYES, glow=True)
    s.pxs([(cx - 12, 77), (cx + 12, 77), (cx - 10, 82), (cx + 10, 82)], HOT[3], glow=True)
    s.line(cx - 11, 86, cx - 6, 92, FLESH[3])                                                   # cheekbones
    s.line(cx + 11, 86, cx + 6, 92, FLESH[0])
    s.g("jaw", cx, 90, "head")
    s.fill(s.poly([(cx - 8, 90), (cx + 8, 90), (cx + 5, 99), (cx, 101), (cx - 5, 99)]), HOT[1], glow=True)   # a maw of embers
    s.fill(s.poly([(cx - 4, 93), (cx + 4, 93), (cx + 2, 98), (cx - 2, 98)]), HOT[3], glow=True)
    for x, ln in ((cx - 6, 6), (cx - 2, 4), (cx + 2, 4), (cx + 6, 6)):                         # upper fangs
        s.fill(s.poly([(x - 1.2, 90), (x + 1.2, 90), (x, 90 + ln)]), BONE[3])
    for x in (cx - 4, cx + 4):                                                                     # lower fangs
        s.fill(s.poly([(x - 1, 100), (x + 1, 100), (x, 95)]), BONE[3])
    # ---- arms spread wide and raised, claws open
    for grp, sub, (sx, sy), (ex, ey), (hx, hy) in (("arm_f", "fore_f", (110, 116), (74, 100), (50, 72)),
                                                   ("weapon", "hand_w", (190, 118), (230, 124), (260, 102))):
        s.g(grp, sx, sy)
        s.fill(s.ellipse(sx, sy - 2, 17, 13), FLESH[1])                                            # deltoid
        s.a |= s.ellipse(sx, sy - 2, 17, 13)
        s.fill(s.ellipse(sx - 2, sy - 5, 12, 8), FLESH[2])
        s.fill(s.ellipse(sx - 4, sy - 8, 7, 3.5), FLESH[3 if sx < cx else 2])
        _mlimb(s, sx, sy, ex, ey, 14, 10, belly=0.45)
        s.g(sub, ex, ey, grp)
        _mlimb(s, ex, ey, hx, hy, 11, 7, belly=0.3, bk=0.9)
        _bclaw(s, hx, hy, math.atan2(hy - ey, hx - ex))
    # ---- backlight: every edge still burns against the red sky behind him
    s.g("body")
    a = s.a & ~s.glow
    up = a & ~np.roll(s.a, 1, 0)
    dn = a & ~np.roll(s.a, -1, 0)
    lf = a & ~np.roll(s.a, 1, 1)
    rt = a & ~np.roll(s.a, -1, 1)
    s.rgb[dn] = RIM_B
    s.rgb[(lf | rt) & ~up] = RIM_S
    s.rgb[up] = RIM_T
    s.ink(INK)
    _dust(s, 40, 3, [HOT[1], HOT[2], HOT[3]])
    s.shadow(150, 404, 40, 3)
    return s


ASCEND = {"vael_ascend": vael_ascend, "vael_bare": vael_bare}
CREATURES.update(ASCEND)
BOSSES.update(ASCEND)
