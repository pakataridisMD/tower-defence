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


def _flame(s, x, y, h, w, seed, pal=None):
    """A tall pillar of fire rising from (x, y): wavering tongues of five heats, hottest at the root."""
    rng = np.random.default_rng(seed)
    pal = pal or HOT
    for layer, col in enumerate(pal[1:]):
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
        s.px(x + rng.uniform(-w, w), y - h * rng.uniform(0.6, 1.25), pal[int(rng.integers(2, len(pal) - 1))], glow=True)


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
FLESH = [(18, 5, 9), (46, 12, 18), (74, 21, 27), (106, 35, 37), (148, 62, 54)]   # raw dark muscle
VEIN = (30, 8, 30)
VEIN_L = (128, 44, 72)
SINEW = [(96, 70, 64), (150, 122, 108), (196, 172, 152)]
CLAW = [(14, 9, 11), (46, 34, 36), (98, 84, 80), (150, 136, 124)]
BLOOD = [(70, 4, 10), (142, 12, 20), (214, 40, 40), (255, 140, 120)]
BONE = [(30, 24, 24), (64, 52, 48), (108, 94, 84), (154, 140, 124), (204, 192, 172)]


def _nrm(x0, y0, x1, y1):
    """Unit normal of a segment, turned to face the light (up, then left)."""
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / L, dx / L
    if ny > 0.15 or (abs(ny) <= 0.15 and nx > 0):
        nx, ny = -nx, -ny
    return nx, ny, dx / L, dy / L


def _axis(x0, y0, x1, y1, r0, r1, tt, o):
    nx, ny, _, _ = _nrm(x0, y0, x1, y1)
    r = r0 + (r1 - r0) * tt
    return x0 + (x1 - x0) * tt + nx * o * r, y0 + (y1 - y0) * tt + ny * o * r


def _darken(s, m, k=0.74):
    s.rgb[m] = (s.rgb[m] * k).astype(np.uint8)


def _fibres(s, m, x0, y0, x1, y1, r0, r1, step=2.6, k=0.74):
    """Muscle fibre: thin darker striations running the length of the muscle."""
    rr = (r0 + r1) / 2
    for o in np.arange(-0.9, 0.95, step / rr):
        pa = _axis(x0, y0, x1, y1, r0, r1, 0.06, o)
        pb = _axis(x0, y0, x1, y1, r0, r1, 0.94, o * 0.95)
        _darken(s, s.capsule(*pa, *pb, 0.45) & m & ~s.glow, k)


def _vein(s, m, pts, w=1.0):
    """A raised vein: dark purple cord with a wet lit edge on its upper-left."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s.fill(s.capsule(x0 - 1, y0 - 1, x1 - 1, y1 - 1, w * 0.6) & m, VEIN_L)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s.fill(s.capsule(x0, y0, x1, y1, w * 0.7) & m, VEIN)


def _veins(s, m, x0, y0, x1, y1, r0, r1, n, seed):
    """Veins snaking along a limb, each with a branch."""
    rng = np.random.default_rng(seed)
    for _ in range(n):
        t0, span = rng.uniform(0.05, 0.35), rng.uniform(0.45, 0.65)
        o, ph, fq = rng.uniform(-0.5, 0.6), rng.uniform(0, 6.28), rng.uniform(3, 5)
        pts = [_axis(x0, y0, x1, y1, r0, r1, min(0.97, t0 + span * j / 9), o + 0.16 * math.sin(ph + j * fq / 9)) for j in range(10)]
        _vein(s, m, pts, 1.1)
        j0 = int(rng.integers(3, 6))
        d = rng.choice([-1, 1]) * rng.uniform(0.12, 0.2)
        br = [pts[j0]] + [_axis(x0, y0, x1, y1, r0, r1, min(0.97, t0 + span * (j0 + j) / 9), o + d * j) for j in range(1, 4)]
        _vein(s, m, br, 0.7)


_FORM = [1]


def _fissure(s, m, x, y, a, ln, seed, w=1.3):
    """A jagged crack of Heartstone fire splitting the muscle open."""
    rng = np.random.default_rng(seed)
    pts = [(x, y)]
    for _ in range(int(ln / 5)):
        a += rng.uniform(-0.6, 0.6)
        x, y = x + math.cos(a) * 5, y + math.sin(a) * 5
        pts.append((x, y))
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s.fill(s.capsule(x0, y0, x1, y1, w + 0.8) & m & ~s.glow, FLESH[0])
    for k, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        ww = w * (1 - k / len(pts) * 0.6)
        s.fill(s.capsule(x0, y0, x1, y1, ww) & m, HOT[1], glow=True)
        s.fill(s.capsule(x0, y0, x1, y1, ww * 0.45) & m, HOT[3], glow=True)


def _mlimb(s, x0, y0, x1, y1, r0, r1, belly=0.38, bk=1.0, veins=2, seed=0):
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
    _fibres(s, m, x0, y0, x1, y1, r0, r1)
    _veins(s, m, x0, y0, x1, y1, r0, r1, veins, seed)
    s.px(bx + nx * r * 0.6, by + ny * r * 0.6, (236, 160, 140))                                   # a wet glint
    if _FORM[0] >= 2:                                                                            # the Wrath: split by fire
        rng = np.random.default_rng(seed + 7)
        for _ in range(2):
            tt = rng.uniform(0.15, 0.6)
            px_, py_ = _axis(x0, y0, x1, y1, r0, r1, tt, rng.uniform(-0.4, 0.4))
            _fissure(s, m, px_, py_, math.atan2(y1 - y0, x1 - x0) + rng.uniform(-0.5, 0.5), L * 0.45, int(rng.integers(1e6)))
    return m


def _hand(s, hx, hy, ang, seed=0):
    """A big clawed hand, palm out: thumb, four jointed fingers curling slightly, black hooked talons, tendons."""
    ux, uy = math.cos(ang), math.sin(ang)
    px_, py_ = hx + ux * 7, hy + uy * 7
    palm = s.ellipse(px_, py_, 9, 7.5, ang)
    s.fill(palm, FLESH[2])
    s.a |= palm
    s.fill(s.ellipse(px_ - 1.5, py_ - 2, 5, 3.5, ang) & palm, FLESH[3])
    for side in (-1, 1):                                                                       # the thumb, toward the body
        tx = math.cos(ang + side * 1.25)
        if (hx < 150) == (tx > 0):
            break
    ta = ang + side * 1.05
    tb = (px_ + math.cos(ang + side * 1.5) * 6, py_ + math.sin(ang + side * 1.5) * 6)
    tm = (tb[0] + math.cos(ta) * 7, tb[1] + math.sin(ta) * 7)
    s.fill(s.capsule(*tb, *tm, 3.2, 2.4), FLESH[2])
    s.a |= s.capsule(*tb, *tm, 3.2, 2.4)
    tt = (tm[0] + math.cos(ta - side * 0.5) * 6, tm[1] + math.sin(ta - side * 0.5) * 6)
    s.fill(s.capsule(*tm, *tt, 1.8, 0.5), CLAW[1])
    s.line(tm[0], tm[1], tt[0], tt[1], CLAW[2])
    for k, sp in enumerate((-0.5, -0.17, 0.16, 0.48)):                                         # four fingers
        fa = ang + sp
        kx, ky = px_ + math.cos(fa) * 8, py_ + math.sin(fa) * 8                                  # knuckle
        L1, L2 = (9, 7) if k in (1, 2) else (8, 6)
        mx, my = kx + math.cos(fa) * L1, ky + math.sin(fa) * L1
        ca = fa + side * 0.38                                                                    # curling in
        ex, ey = mx + math.cos(ca) * L2, my + math.sin(ca) * L2
        for (a0, b0, a1, b1, r0, r1, tone) in ((kx, ky, mx, my, 3.3, 2.8, FLESH[2]), (mx, my, ex, ey, 2.8, 2.2, FLESH[2])):
            mm = s.capsule(a0, b0, a1, b1, r0, r1)
            s.fill(mm, tone)
            s.a |= mm
        s.fill(s.capsule(kx - 0.6, ky - 0.8, mx - 0.6, my - 0.8, 1.0), FLESH[3])
        s.px(kx, ky, FLESH[4])                                                                   # knuckle
        s.px(mx, my, FLESH[3])
        s.line(hx, hy, kx, ky, SINEW[0])                                                         # tendon on the back of the hand
        ta2 = ca + side * 0.45                                                                   # the talon, hooked
        c1 = (ex + math.cos(ca) * 5, ey + math.sin(ca) * 5)
        c2 = (c1[0] + math.cos(ta2) * 5, c1[1] + math.sin(ta2) * 5)
        s.fill(s.capsule(ex, ey, *c1, 1.9, 1.3), CLAW[1])
        s.fill(s.capsule(*c1, *c2, 1.3, 0.4), CLAW[0])
        s.line(ex, ey, c1[0], c1[1], CLAW[2])
        s.px(ex - 0.5, ey - 0.5, CLAW[3])
    _vein(s, s.a, [(hx - ux * 6, hy - uy * 6 + 1), (hx + ux * 2, hy + uy * 2 + 2), (px_ + ux * 3, py_ + uy * 3 + 1)], 0.8)


def _foot(s, ax, ay, fs):
    """A clawed demon foot hanging toes-down: ankle knob, heel spur, tendons down the instep, four taloned toes."""
    s.fill(s.poly([(ax + fs * 4, ay + 2), (ax + fs * 14, ay - 4), (ax + fs * 8, ay + 8)]), BONE[2])     # heel spur
    s.line(ax + fs * 5, ay + 2, ax + fs * 13, ay - 3, BONE[3])
    heel = s.ellipse(ax + fs * 3, ay + 6, 6, 7)
    s.fill(heel, FLESH[1])
    inst = s.poly([(ax - 7, ay - 2), (ax + 7, ay - 2), (ax + 8, ay + 10), (ax + 6, ay + 20), (ax - 6, ay + 20), (ax - 8, ay + 10)])
    s.fill(inst, FLESH[1])
    s.fill(s.poly([(ax - 7, ay - 2), (ax, ay - 2), (ax - 1, ay + 20), (ax - 6, ay + 20), (ax - 8, ay + 10)]), FLESH[2])
    s.a |= heel | inst
    s.fill(s.ellipse(ax - fs * 5, ay + 1, 3, 3), FLESH[3])                                      # ankle knob
    for k in (-3, 0, 3):                                                                       # tendons down the instep
        s.line(ax + k, ay + 4, ax + k * 1.3, ay + 17, FLESH[3 if k < 0 else 0])
    for k, (dx, ln) in enumerate(((-6, 7), (-2, 9), (2, 9), (6, 7))):                          # toes, splayed a little
        bx, by = ax + dx, ay + 19
        tx, ty = bx + dx * 0.35, by + ln
        mm = s.capsule(bx, by, tx, ty, 2.6, 2.0)
        s.fill(mm, FLESH[2] if dx < 0 else FLESH[1])
        s.a |= mm
        s.px(bx - 1, by + 1, FLESH[3])
        cx_, cy_ = tx + dx * 0.15, ty + 6                                                      # talon, curling under
        s.fill(s.capsule(tx, ty, cx_, cy_, 1.8, 1.0), CLAW[1])
        s.fill(s.capsule(cx_, cy_, cx_ - fs * 2.5, cy_ + 3, 1.0, 0.4), CLAW[0])
        s.line(tx - 0.6, ty, cx_ - 0.6, cy_, CLAW[2])
    _vein(s, s.a, [(ax - 4, ay - 6), (ax - 3, ay + 4), (ax - 5, ay + 12)], 0.8)


def _drip(s, x, y, ln, seed=0):
    """A run of blood with a bead at the end."""
    s.line(x, y, x, y + ln, BLOOD[1])
    s.px(x - 1, y + 1, BLOOD[2])
    s.fill(s.ellipse(x, y + ln + 1, 1.3, 1.8), BLOOD[1])
    s.px(x - 0.4, y + ln, BLOOD[3])


def vael_bare(pose=None, pad=0, form=1):
    """Vael-Orrun, bare: the same floating pose, stripped to a naked hide of dark, hard muscle.

    form 2 (the Wrath): the hide splits on Heartstone fire, the chest bursts open, a second pair of horns, six eyes,
    fire pouring off the shoulders."""
    _FORM[0] = form
    s = Sprite(300, 440, pose, pad, origin=(0, 40))
    cx = 150
    # ---- hips, under the thighs
    s.g("body")
    hips = s.poly([(128, 194), (172, 194), (178, 214), (150, 234), (122, 214)])
    s.fill(hips, FLESH[1])
    s.a |= hips
    # ---- legs: heavy thighs, long hanging shins, clawed feet pointed down
    for grp, sub, (hx, hy), (kx, ky), (ax, ay), fs in (("leg_f", "shin_f", (137, 214), (129, 284), (125, 338), -1),
                                                       ("leg_n", "shin_n", (163, 214), (170, 282), (168, 336), 1)):
        s.g(grp, hx, hy)
        _mlimb(s, hx, hy, kx, ky, 18, 11, belly=0.38, veins=2, seed=hx + 3)
        s.fill(s.ellipse(kx - fs * 3, ky - 13, 6, 8) & s.capsule(hx, hy, kx, ky, 18, 11), FLESH[3 if fs < 0 else 2])  # teardrop above the knee
        s.line(hx + fs * 2, hy + 14, kx + fs * 4, ky - 6, FLESH[0])                            # the split between the thigh muscles
        s.g(sub, kx, ky, grp)
        s.fill(s.ellipse(kx, ky, 10, 8), FLESH[2])
        s.fill(s.ellipse(kx - 2, ky - 1, 5, 4), FLESH[3])                                        # kneecap
        _mlimb(s, kx, ky + 4, ax, ay, 11, 5.5, belly=0.26, bk=0.85, veins=2, seed=kx)          # calf
        s.line(ax + fs * 4, ay - 14, ax + fs * 3, ay, FLESH[3])                                  # the heel tendon
        _foot(s, ax, ay, fs)
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
    for sgn in (-1, 1):                                                                          # fibre fanning across the pecs
        pec = s.poly([(150 + sgn * 2, 110), (150 + sgn * 46, 112), (150 + sgn * 40, 140), (150 + sgn * 18, 152), (150 + sgn * 2, 146)])
        for j in range(12):
            _darken(s, s.capsule(150 + sgn * 3, 112 + j * 3.2, 150 + sgn * 46, 111 + j * 1.6, 0.45) & pec)
        obl = s.poly([(150 + sgn * 34, 150), (150 + sgn * 20, 158), (150 + sgn * 18, 198), (150 + sgn * 22, 202), (150 + sgn * 30, 182)])
        for j in range(6):
            _darken(s, s.capsule(150 + sgn * (36 - j * 2), 150 + j * 3, 150 + sgn * (20 - j * 0.4), 176 + j * 5, 0.45) & obl)
    for pts in (((141, 150), (133, 158), (128, 172), (121, 184)), ((159, 150), (167, 160), (171, 174), (178, 182)),
                ((140, 118), (128, 114), (116, 118), (108, 114)), ((160, 120), (172, 118), (184, 122)),
                ((146, 156), (142, 170), (144, 186), (139, 200), (142, 214)), ((156, 158), (160, 176), (157, 194))):
        _vein(s, torso | hips, list(pts), 1.1)                                                   # veins swollen black around the core
    for x, y0, ln in ((147, 154, 22), (153, 156, 30), (141, 150, 12)):                          # blood running from the open chest
        s.fill(s.capsule(x, y0, x - 1, y0 + ln, 0.8), BLOOD[1])
        s.px(x - 1, y0 + 2, BLOOD[2])
        s.fill(s.ellipse(x - 1, y0 + ln + 1, 1.3, 1.8), BLOOD[1])
        s.px(x - 1.4, y0 + ln, BLOOD[3])
    if form >= 2:
        for k in range(9):
            a = -math.pi / 2 + k * 0.7 + 0.3
            _fissure(s, torso | hips, 150 + math.cos(a) * 10, 136 + math.sin(a) * 20, a, 34 + (k % 3) * 10, 300 + k, 1.6)
    core = s.ellipse(150, 132, 9, 22) if form == 1 else s.ellipse(150, 134, 15, 30)
    for r, col in ((1.0, HOT[0]), (0.8, HOT[1]), (0.6, HOT[2]), (0.4, HOT[3]), (0.22, HOT[4]), (0.1, HOT[5])):
        s.fill(s.ellipse(150, 132 + (form > 1) * 2, (9 + 6 * (form > 1)) * r + 0.5, (22 + 8 * (form > 1)) * r + 0.5) & core, col, glow=True)
    for k in range(5):                                                                           # rib bars across the light
        y = 116 + k * 7
        w = 10 - abs(k - 2) * 1.5
        if form >= 2:                                                                            # ribs snapped and splayed open
            for sg in (-1, 1):
                s.fill(s.poly([(150 + sg * 9, y + 1), (150 + sg * (w + 12), y - 4), (150 + sg * (w + 13), y - 1), (150 + sg * 9, y + 5)]), BONE[1])
                s.line(150 + sg * 9, y + 1, 150 + sg * (w + 12), y - 4, BONE[3])
            continue
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
    if form >= 2:                                                                                # fire pouring off the shoulders
        _flame(s, 116, 108, 66, 18, 41)
        _flame(s, 184, 108, 72, 18, 43)
    # ---- neck and traps
    s.fill(s.poly([(136, 92), (164, 92), (176, 110), (124, 110)]), FLESH[1])
    s.fill(s.poly([(136, 92), (150, 92), (150, 110), (124, 110)]), FLESH[2])
    s.line(140, 96, 148, 112, FLESH[3])
    neck = s.poly([(136, 92), (164, 92), (176, 110), (124, 110)])
    for j in range(7):                                                                           # neck cords and fibre
        _darken(s, s.capsule(138 + j * 4, 92, 128 + j * 7, 110, 0.45) & neck)
    _vein(s, neck, [(140, 93), (138, 100), (133, 106), (130, 110)], 1.1)
    _vein(s, neck, [(160, 94), (163, 102), (168, 109)], 1.0)
    # ---- head: a long demon skull of dark hide, heavy brow, horns, a wild mane behind
    s.g("head", cx, 104)
    mrng = np.random.default_rng(17)
    for k in range(19):
        a = -math.pi / 2 + (k - 9) * 0.17 + mrng.uniform(-0.08, 0.08)
        L = mrng.uniform(8, 34) * (1.0 - abs(k - 9) * 0.03)
        tip = (cx + math.cos(a) * (L + 16), 74 + math.sin(a) * (L + 16))
        s.fill(s.poly([(cx + math.cos(a - 0.12) * 12, 74 + math.sin(a - 0.12) * 12),
                       (cx + math.cos(a + 0.12) * 12, 74 + math.sin(a + 0.12) * 12), tip]), SIL_D[2])
    if form >= 2:
        for sgn in (-1, 1):                                                                      # a second pair, sweeping out
            pts = _curve((cx + sgn * 13, 70), (cx + sgn * 44, 66), (cx + sgn * 56, 34), 12)
            s.fill(_ribbon(s, pts, 4.5, 0.6), BONE[1])
            s.fill(_ribbon(s, pts[:8], 1.8, 0.5), BONE[2])
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
    if form >= 2:                                                                                # four more eyes torn open above
        for sgn in (-1, 1):
            s.fill(s.poly([(cx + sgn * 10, 66), (cx + sgn * 3, 70), (cx + sgn * 3, 72), (cx + sgn * 10, 69)]), EYES, glow=True)
            s.fill(s.poly([(cx + sgn * 7, 59), (cx + sgn * 2, 62), (cx + sgn * 2, 64), (cx + sgn * 7, 62)]), HOT[4], glow=True)
    s.line(cx - 11, 86, cx - 6, 92, FLESH[3])                                                   # cheekbones
    s.line(cx + 11, 86, cx + 6, 92, FLESH[0])
    _vein(s, head, [(cx - 14, 72), (cx - 12, 66), (cx - 13, 61)], 0.8)                          # temples throbbing
    _vein(s, head, [(cx + 14, 72), (cx + 12, 66), (cx + 13, 61)], 0.8)
    _vein(s, head, [(cx - 2, 60), (cx - 1, 66), (cx - 3, 70)], 0.7)
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
        _fibres(s, s.ellipse(sx, sy - 2, 17, 13), sx - 14, sy - 8, sx + 8, sy + 10, 8, 8)
        _mlimb(s, sx, sy, ex, ey, 14, 10, belly=0.45, veins=2, seed=sx)
        s.g(sub, ex, ey, grp)
        fm = _mlimb(s, ex, ey, hx, hy, 11, 7, belly=0.3, bk=0.9, veins=3, seed=ex)
        _hand(s, hx, hy, math.atan2(hy - ey, hx - ex))
        p0 = _axis(ex, ey, hx, hy, 11, 7, 0.9, -0.75)                                            # blood running back down the forearm
        p1 = _axis(ex, ey, hx, hy, 11, 7, 0.45, -0.8)
        p2 = _axis(ex, ey, hx, hy, 11, 7, 0.05, -0.85)
        for (a0, b0), (a1, b1) in ((p0, p1), (p1, p2)):
            s.fill(s.capsule(a0, b0, a1, b1, 0.8) & fm, BLOOD[1])
        _drip(s, p2[0], p2[1] + 1, 7)
    # ---- backlight: every edge still burns against the red sky behind him
    s.g("body")
    claw = np.zeros_like(s.a)
    for c in CLAW:
        claw |= np.all(s.rgb == np.array(c, np.uint8), axis=-1)
    claw &= s.a
    keep = s.rgb[claw].copy()
    a = s.a & ~s.glow
    up = a & ~np.roll(s.a, 1, 0)
    dn = a & ~np.roll(s.a, -1, 0)
    lf = a & ~np.roll(s.a, 1, 1)
    rt = a & ~np.roll(s.a, -1, 1)
    s.rgb[dn] = RIM_B
    s.rgb[(lf | rt) & ~up] = RIM_S
    s.rgb[up] = RIM_T
    s.rgb[claw] = keep                                                                           # talons stay black
    s.ink(INK)
    _dust(s, 40, 3, [HOT[1], HOT[2], HOT[3]])
    s.shadow(150, 404, 40, 3)
    return s


def vael_bare_wrath(pose=None, pad=0):
    return vael_bare(pose, pad, form=2)


# ---- form 3, the Unmade: the flesh burnt off, a charred skeleton wreathed in the grey fire of the Unmaking
CHAR = [(10, 8, 12), (30, 27, 34), (62, 58, 68), (112, 108, 120), (186, 184, 198)]
GREYF = [(50, 46, 70), (98, 94, 126), (152, 150, 180), (208, 208, 228), (242, 242, 252), (255, 255, 255)]
VOID = [(6, 4, 10), (16, 12, 22), (30, 24, 40)]


def _bone(s, x0, y0, x1, y1, r0, r1=None, knob=1.4):
    """A long bone: a lit shaft and knobbed ends."""
    r1 = r0 if r1 is None else r1
    m = s.capsule(x0, y0, x1, y1, r0, r1)
    s.fill(m, CHAR[1])
    s.a |= m
    nx, ny, _, _ = _nrm(x0, y0, x1, y1)
    s.fill(s.capsule(x0 + nx * r0 * 0.4, y0 + ny * r0 * 0.4, x1 + nx * r1 * 0.4, y1 + ny * r1 * 0.4, r0 * 0.5, r1 * 0.5) & m, CHAR[2])
    s.line(x0 + nx * r0 * 0.5, y0 + ny * r0 * 0.5, x1 + nx * r1 * 0.5, y1 + ny * r1 * 0.5, CHAR[3])
    for (x, y, r) in ((x0, y0, r0), (x1, y1, r1)):
        k = s.ellipse(x, y, r * knob + 0.5, r * knob + 0.5)
        s.fill(k, CHAR[1])
        s.fill(s.ellipse(x - 0.6, y - 0.8, r * 0.8, r * 0.6), CHAR[3])
        s.a |= k
    return m


def _gfire(s, x, y, h, w, seed, pal=None):
    """Separate licking tongues of fire, each swaying, hottest at the root (reads as fire, not a cone)."""
    pal = pal or GREYF
    rng = np.random.default_rng(seed)
    n = 6
    for k in range(n):
        dx = (k / (n - 1) - 0.5) * 2 * w + rng.uniform(-2, 2)
        hh = h * rng.uniform(0.35, 1.0) * (1.0 - abs(dx) / (w * 2.2))
        ph, amp = rng.uniform(0, 6.28), rng.uniform(2, 4.5)
        pts = [(x + dx * (1 - 0.4 * j / 10) + math.sin(ph + j * 0.7) * amp * j / 10, y - hh * j / 10) for j in range(11)]
        for frac, ww, col in ((1.0, 3.6, pal[1]), (0.75, 2.4, pal[2]), (0.5, 1.5, pal[3]), (0.28, 0.9, pal[4])):
            m = int(round(10 * frac)) + 1
            s.fill(_ribbon(s, pts[:m], ww, 0.3), col, glow=True)
    s.fill(s.ellipse(x, y, w * 0.9 + 2, 3), pal[3], glow=True)
    for _ in range(10):
        s.px(x + rng.uniform(-w, w), y - h * rng.uniform(0.7, 1.3), pal[int(rng.integers(2, 5))], glow=True)


def _wisps(s, x, y, ln, seed, sway=1):
    """Tatters of void smoke trailing down."""
    rng = np.random.default_rng(seed)
    for k in range(5):
        pts = [(x + rng.uniform(-6, 6), y)]
        for j in range(6):
            px_, py_ = pts[-1]
            pts.append((px_ + sway * rng.uniform(-2, 4), py_ + ln / 6))
        s.fill(_ribbon(s, pts, rng.uniform(3, 5), 0.5), VOID[int(rng.integers(0, 3))])


def vael_unmade(pose=None, pad=0):
    """Vael-Orrun, the Unmade: what is left when the Wrath burns through. Charred bone, void smoke where flesh was,
    a white-hot Heartstone in an open cage of ribs, and the colourless fire of the Unmaking pouring off him."""
    s = Sprite(300, 440, pose, pad, origin=(0, 40))
    cx = 150
    # ---- void smoke hanging where the body was
    s.g("body")
    yy, xx = np.mgrid[0:s.h, 0:s.w]
    dith = ((xx + yy) % 2 == 0)
    smoke = s.ellipse(150, 168, 30, 42) & dith                                                   # a dithered smoke where the gut was
    s.fill(smoke, VOID[1])
    s.a |= smoke
    _wisps(s, 140, 196, 70, 5)
    _wisps(s, 160, 196, 60, 6)
    # ---- legs of bone
    for grp, sub, (hx, hy), (kx, ky), (ax, ay), fs in (("leg_f", "shin_f", (138, 216), (129, 284), (125, 338), -1),
                                                       ("leg_n", "shin_n", (162, 216), (170, 282), (168, 336), 1)):
        s.g(grp, hx, hy)
        _bone(s, hx, hy, kx, ky, 5.5, 4.4)
        s.g(sub, kx, ky, grp)
        _bone(s, kx, ky + 2, ax, ay, 4.2, 3.2)
        _bone(s, kx + fs * 4, ky + 4, ax + fs * 4, ay - 2, 1.6, 1.4, knob=1.0)                    # the fibula
        for k, dx in enumerate((-5, -2, 2, 5)):                                                  # foot bones and talons
            _bone(s, ax, ay + 2, ax + dx, ay + 16, 1.4, 1.2, knob=1.1)
            s.fill(s.capsule(ax + dx, ay + 16, ax + dx * 1.2, ay + 24, 1.6, 0.8), CLAW[1])
            s.fill(s.capsule(ax + dx * 1.2, ay + 24, ax + dx * 1.2 - fs * 2.5, ay + 27, 0.9, 0.4), CLAW[0])
    # ---- pelvis and spine
    s.g("body")
    for sg in (-1, 1):                                                                           # the hip bone: two flared wings
        wing = s.poly([(150 + sg * 6, 204), (150 + sg * 18, 192), (150 + sg * 32, 184), (150 + sg * 34, 192), (150 + sg * 26, 212),
                       (150 + sg * 12, 226), (150 + sg * 6, 226)])
        s.fill(wing, CHAR[2] if sg < 0 else CHAR[1])
        s.a |= wing
        s.line(150 + sg * 18, 193, 150 + sg * 32, 185, CHAR[3])
        s.fill(s.ellipse(150 + sg * 14, 213, 3.5, 4.5), VOID[0])
    sac = s.poly([(144, 196), (156, 196), (154, 222), (150, 230), (146, 222)])
    s.fill(sac, CHAR[2])
    s.a |= sac
    for k in range(13):                                                                          # vertebrae
        y = 196 - k * 7.5
        s.fill(s.ellipse(150, y, 4.5, 3), CHAR[2])
        s.px(149, y - 1, CHAR[3])
        s.a |= s.ellipse(150, y, 4.5, 3)
    # ---- the open cage of ribs and the white-hot Heartstone inside
    core = s.ellipse(150, 140, 13, 28)
    for r, col in ((1.4, GREYF[0]), (1.0, GREYF[1]), (0.75, GREYF[2]), (0.5, GREYF[3]), (0.3, GREYF[4]), (0.14, GREYF[5])):
        s.fill(s.ellipse(150, 140, 13 * r + 0.5, 28 * r + 0.5), col, glow=True)
    for k, col in enumerate(RING):                                                               # the six stolen colours
        a = k / 6 * 6.28
        s.px(150 + math.cos(a) * 6, 140 + math.sin(a) * 14, col, glow=True)
    for k in range(7):                                                                           # ribs curving out and back, broken in front
        y = 110 + k * 10
        w = 40 - abs(k - 2.5) * 4
        for sg in (-1, 1):
            pts = _curve((150 + sg * 4, y), (150 + sg * (w + 6), y - 2), (150 + sg * (w * 0.7), y + 18), 8)
            m = _ribbon(s, pts, 2.6, 1.2)
            s.fill(m, CHAR[2] if sg < 0 else CHAR[1])
            s.a |= m
            s.line(pts[0][0], pts[0][1] - 1, pts[3][0], pts[3][1] - 1.5, CHAR[3])
    for sg in (-1, 1):                                                                           # collarbones and the spines of the back
        _bone(s, 150 + sg * 6, 106, 150 + sg * 40, 112, 2.6, 2.2)
        for k in range(5):
            a = -math.pi / 2 + sg * (0.3 + k * 0.24)
            bx, by = cx + sg * (18 + k * 6), 106 + k * 2
            L = 34 + (k % 2) * 14 - k * 2
            tip = (bx + math.cos(a) * L, by + math.sin(a) * L)
            s.fill(s.poly([(bx - 3, by + 2), (bx + 3, by + 2), tip]), CHAR[1])
            s.line(bx, by, tip[0], tip[1], CHAR[3])
    # ---- the skull
    s.g("head", cx, 104)
    for sgn in (-1, 1):                                                                          # four horns, longer than ever
        for (p0, p1, p2, w0) in (((cx + sgn * 10, 62), (cx + sgn * 36, 40), (cx + sgn * 22, 2), 5.5),
                                 ((cx + sgn * 13, 70), (cx + sgn * 48, 64), (cx + sgn * 62, 26), 4.5)):
            pts = _curve(p0, p1, p2, 12)
            s.fill(_ribbon(s, pts, w0, 0.7), CHAR[1])
            s.fill(_ribbon(s, pts[:8], w0 * 0.4, 0.5), CHAR[3])
    head = s.poly([(cx - 14, 58), (cx + 14, 58), (cx + 17, 72), (cx + 12, 88), (cx - 12, 88), (cx - 17, 72)])
    s.fill(head, CHAR[2])
    s.a |= head
    s.fill(s.poly([(cx, 58), (cx + 14, 58), (cx + 17, 72), (cx + 12, 88), (cx, 88)]), CHAR[1])
    s.line(cx - 12, 60, cx - 2, 59, CHAR[4])
    for sgn in (-1, 1):                                                                          # deep sockets, a pin of white in each
        s.fill(s.poly([(cx + sgn * 14, 72), (cx + sgn * 3, 76), (cx + sgn * 4, 84), (cx + sgn * 13, 80)]), VOID[0])
        s.fill(s.ellipse(cx + sgn * 8, 79, 1.6, 1.4), GREYF[5], glow=True)
    s.fill(s.poly([(cx - 2, 84), (cx + 2, 84), (cx, 89)]), VOID[0])                              # the nose hole
    s.g("jaw", cx, 90, "head")
    jaw = s.poly([(cx - 12, 88), (cx + 12, 88), (cx + 8, 102), (cx - 8, 102)])
    s.fill(jaw, CHAR[1])
    s.a |= jaw
    s.fill(s.poly([(cx - 9, 91), (cx + 9, 91), (cx + 6, 99), (cx - 6, 99)]), GREYF[2], glow=True)  # grey fire in the throat
    for x in (cx - 8, cx - 4, cx, cx + 4, cx + 8):                                              # teeth
        s.fill(s.poly([(x - 1.3, 88), (x + 1.3, 88), (x, 94)]), CHAR[4])
    # ---- arms of bone, raised
    for grp, sub, (sx, sy), (ex, ey), (hx, hy) in (("arm_f", "fore_f", (110, 114), (74, 100), (50, 72)),
                                                   ("weapon", "hand_w", (190, 116), (230, 124), (260, 102))):
        s.g(grp, sx, sy)
        _bone(s, sx, sy, ex, ey, 5.2, 4.2)
        s.g(sub, ex, ey, grp)
        nx, ny, ux, uy = _nrm(ex, ey, hx, hy)
        _bone(s, ex + nx * 2.5, ey + ny * 2.5, hx + nx * 2, hy + ny * 2, 2.2, 1.8, knob=1.1)          # radius and ulna
        _bone(s, ex - nx * 2.5, ey - ny * 2.5, hx - nx * 1.5, hy - ny * 1.5, 2.0, 1.6, knob=1.1)
        ang = math.atan2(hy - ey, hx - ex)
        for k, sp in enumerate((-0.6, -0.2, 0.2, 0.6)):                                         # finger bones and talons
            fa = ang + sp
            k1 = (hx + math.cos(fa) * 9, hy + math.sin(fa) * 9)
            k2 = (k1[0] + math.cos(fa + 0.3) * 8, k1[1] + math.sin(fa + 0.3) * 8)
            _bone(s, hx, hy, *k1, 1.5, 1.3, knob=1.1)
            _bone(s, *k1, *k2, 1.3, 1.1, knob=1.0)
            c2 = (k2[0] + math.cos(fa + 0.7) * 7, k2[1] + math.sin(fa + 0.7) * 7)
            s.fill(s.capsule(*k2, *c2, 1.6, 0.4), CLAW[0])
        _gfire(s, hx, hy - 2, 62, 9, sx)                                            # the Unmaking in both hands
    # ---- the grey fire pouring off the bones
    s.g("body")
    _gfire(s, 120, 112, 84, 12, 61)
    _gfire(s, 180, 112, 92, 12, 63)
    _gfire(s, 150, 124, 40, 6, 67)                                                    # up through the ribs
    s.g("head")
    _gfire(s, cx, 58, 70, 12, 65)
    # ---- rim: the edges catch the cold light
    s.g("body")
    claw = np.zeros_like(s.a)
    for c in CLAW + VOID:
        claw |= np.all(s.rgb == np.array(c, np.uint8), axis=-1)
    claw &= s.a
    keep = s.rgb[claw].copy()
    a = s.a & ~s.glow
    up = a & ~np.roll(s.a, 1, 0)
    lf = a & ~np.roll(s.a, 1, 1)
    rt = a & ~np.roll(s.a, -1, 1)
    s.rgb[(lf | rt) & ~up] = GREYF[1]
    s.rgb[up] = GREYF[2]
    s.rgb[claw] = keep
    s.ink((6, 4, 10))
    _dust(s, 60, 3, [GREYF[1], GREYF[2], GREYF[3]])
    s.shadow(150, 404, 40, 3)
    return s


ASCEND = {"vael_ascend": vael_ascend, "vael_bare": vael_bare, "vael_bare_wrath": vael_bare_wrath, "vael_unmade": vael_unmade}
CREATURES.update(ASCEND)
BOSSES.update(ASCEND)
