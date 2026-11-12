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


ASCEND = {"vael_ascend": vael_ascend}
CREATURES.update(ASCEND)
BOSSES.update(ASCEND)
