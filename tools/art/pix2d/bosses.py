"""Story bosses in the hand-drawn 2D style. 32 art px = 1 board cell; bosses are drawn huge on purpose.

Heralds share a motif: eyes and mouth are empty grey light and their outlines leak grey dust.
"""
from __future__ import annotations

import numpy as np

from creatures import CREATURES, DARK, IRON, _slab
from kit import Sprite, ramp

GREY_GLOW = [(120, 124, 136), (176, 180, 192), (226, 228, 236), (250, 250, 255)]
OCHRE = ramp("a07c4c", spread=0.5, shift=0.02)
OCHRE_D = ramp("74583c", spread=0.45, shift=0.02)
BASALT = ramp("4c4652", spread=0.62, shift=0.03)
BASALT_D = ramp("38333e", spread=0.5, shift=0.03)
SMOKE = ramp("4a4650", spread=0.4, shift=0.0)
GLASS = ramp("26223a", spread=0.5, shift=0.0)
GLASS_D = ramp("16141f", spread=0.36, shift=0.0)
RING = [(255, 122, 58), (200, 216, 255), (138, 240, 80), (74, 224, 224), (232, 176, 64), (176, 112, 255)]  # the six


def _dust(s, n, seed, cols=GREY_GLOW):
    """Grey dust leaking off the outline (call after ink)."""
    rng = np.random.default_rng(seed)
    ys, xs = np.where(s.a)
    for _ in range(n):
        i = int(rng.integers(len(xs)))
        x, y = int(xs[i]) + int(rng.integers(-5, 6)), int(ys[i]) - int(rng.integers(0, 7))
        if 0 <= x < s.w and 0 <= y < s.h and not s.a[y, x]:
            s.rgb[y, x] = cols[int(rng.integers(1, 3))]
            s.a[y, x] = True
            s.glow[y, x] = True


def _crack(s, pts, col, hot=None):
    """A glowing crack along a zigzag, only where there is body to crack."""
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            x, y = x0 + (x1 - x0) * i / n, y0 + (y1 - y0) * i / n
            tx, ty = (round(v) for v in s.fw(x, y))
            if 0 <= tx < s.w and 0 <= ty < s.h and s.a[ty, tx]:
                s.px(x, y, col, glow=True)
    if hot:
        for x, y in pts[1:-1]:
            s.px(x, y, hot, glow=True)


def gorrath(pose=None, pad=0):
    """Gorrath the Quarried, the Stone Herald: a quarried general, armour fused into him, a carved stone for a heart."""
    s = Sprite(104, 124, pose, pad, origin=(0, 6))
    # far arm
    s.g("arm_f", 68, 38)
    _slab(s, [(62, 34), (75, 34), (76, 56), (64, 56)], OCHRE_D, chips=2, seed=1)
    s.g("fore_f", 70, 56, "arm_f")
    _slab(s, [(64, 57), (76, 57), (78, 76), (66, 76)], OCHRE_D, chips=1, seed=2)
    _slab(s, [(63, 77), (80, 77), (81, 91), (64, 91)], OCHRE_D, chips=2, seed=3)
    # legs: thigh, shin and a broad foot each
    for grp, sub, x, tone, sd in (("leg_f", "shin_f", 36, OCHRE_D, 4), ("leg_n", "shin_n", 54, OCHRE, 7)):
        s.g(grp, x + 6, 74)
        _slab(s, [(x, 72), (x + 13, 72), (x + 13, 90), (x + 1, 90)], tone, chips=2, seed=sd)
        s.g(sub, x + 7, 90, grp)
        _slab(s, [(x + 1, 91), (x + 13, 91), (x + 14, 104), (x + 2, 104)], tone, chips=1, seed=sd + 1)
        _slab(s, [(x - 2, 104), (x + 17, 104), (x + 18, 111), (x - 3, 111)], OCHRE_D, depth=(3, -2), seed=sd + 2)
        s.part(s.rect(x + 1, 88, x + 14, 92), IRON, flat=True)          # iron knee band
    # hips with hanging iron plates
    s.g("body")
    _slab(s, [(35, 62), (70, 62), (68, 73), (37, 73)], OCHRE_D, seed=10)
    for x in (37, 46, 55, 63):
        s.part(s.poly([(x, 66), (x + 7, 66), (x + 6, 78), (x + 3, 81), (x + 1, 78)]), IRON, flat=True)
        s.px(x + 3, 69, IRON[4])
    # the great chest
    _slab(s, [(27, 26), (74, 26), (69, 62), (34, 62)], OCHRE, depth=(4, -4), chips=9, seed=11)
    s.part(s.poly([(29, 30), (72, 30), (71, 35), (30, 35)]), IRON, flat=True)   # fused iron bands
    s.part(s.poly([(33, 55), (69, 55), (69, 60), (34, 60)]), IRON, flat=True)
    for x in (33, 41, 61, 68):
        s.px(x, 32, IRON[4])
        s.px(x, 57, IRON[4])
    # the square hole where his heart was, and the carved stone set in it
    s.fill(s.rect(42, 37, 60, 53), (22, 16, 22))
    s.fill(s.rect(42, 37, 60, 38), OCHRE[0])
    s.fill(s.rect(42, 37, 43, 53), OCHRE[0])
    s.fill(s.rect(46, 40, 57, 51), GREY_GLOW[0], glow=True)
    s.fill(s.rect(47, 41, 56, 50), GREY_GLOW[1], glow=True)
    for (x0, y0, x1, y1) in ((49, 43, 54, 43), (49, 43, 49, 48), (49, 48, 54, 48), (54, 45, 54, 48), (51, 45, 52, 46)):
        s.line(x0, y0, x1, y1, GREY_GLOW[3], glow=True)                 # the oath-rune cut in the stone
    _crack(s, [(42, 45), (38, 47), (35, 44), (31, 46)], GREY_GLOW[1], GREY_GLOW[3])
    _crack(s, [(60, 46), (64, 49), (66, 46), (70, 50)], GREY_GLOW[1], GREY_GLOW[3])
    _crack(s, [(51, 53), (50, 57), (53, 61)], GREY_GLOW[1])
    # head: square helm-skull, iron brow, a crest of stone fins, empty grey eyes and mouth
    s.g("head", 53, 26)
    _slab(s, [(44, 9), (62, 9), (62, 26), (45, 26)], OCHRE_D, chips=2, seed=12)
    _slab(s, [(42, 6), (64, 6), (64, 12), (42, 12)], IRON, depth=(3, -2), seed=13)
    for i, x in enumerate((44, 49, 54, 59)):
        s.fill(s.poly([(x, 6), (x + 4, 6), (x + 3, -1 + (i % 2) * 2), (x + 1, -1 + (i % 2) * 2)]), OCHRE[2 + i % 2])
        s.line(x, 6, x + 1, 0 + (i % 2) * 2, OCHRE[4])
    s.fill(s.rect(52, 14, 56, 17), GREY_GLOW[2], glow=True)
    s.fill(s.rect(58, 14, 62, 17), GREY_GLOW[2], glow=True)
    s.pxs([(53, 15), (59, 15)], GREY_GLOW[3], glow=True)
    s.g("jaw", 47, 20, "head")
    s.fill(s.rect(51, 20, 61, 23), GREY_GLOW[1], glow=True)
    s.fill(s.rect(52, 21, 60, 22), GREY_GLOW[3], glow=True)
    _slab(s, [(47, 23), (62, 23), (61, 27), (48, 27)], OCHRE_D, depth=(2, -1), seed=14)
    # near arm: upper arm, then the general's pauldron (stays with the chest), then forearm and fist
    s.g("weapon", 22, 40)
    _slab(s, [(14, 40), (29, 40), (29, 58), (15, 58)], OCHRE_D, chips=1, seed=15)
    s.g("body")
    _slab(s, [(8, 20), (33, 20), (34, 40), (9, 40)], OCHRE, depth=(5, -5), chips=4, seed=16)
    s.part(s.poly([(8, 34), (34, 34), (34, 40), (9, 40)]), IRON, flat=True)
    for x in (11, 18, 25):
        s.fill(s.poly([(x, 20), (x + 6, 20), (x + 3, 11)]), OCHRE[3])
        s.line(x, 20, x + 3, 12, OCHRE[4])
        s.line(x + 6, 20, x + 3, 12, OCHRE[1])
    s.g("hand_w", 22, 58, "weapon")
    _slab(s, [(12, 59), (30, 59), (31, 78), (13, 78)], OCHRE, chips=4, seed=17)
    s.part(s.rect(12, 62, 32, 66), IRON, flat=True)
    _slab(s, [(9, 78), (33, 78), (33, 93), (10, 93)], OCHRE_D, chips=2, seed=18)
    for x in (15, 21, 27):
        s.line(x, 85, x, 92, OCHRE_D[0])
    s.ink()
    _dust(s, 26, 5)
    s.shadow(52, 113, 30, 4)
    return s


def cinder_tyrant(pose=None, pad=0):
    """The Cinder Tyrant, Ignar corrupted: black basalt split open, grey-white fire inside, a crown of black smoke."""
    s = Sprite(150, 212, pose, pad, origin=(0, 30))
    hot, mid, low = GREY_GLOW[3], GREY_GLOW[2], GREY_GLOW[0]
    # far arm
    s.g("arm_f", 100, 62)
    s.part(s.capsule(100, 62, 108, 92, 11), BASALT_D, bias=-0.1)
    s.g("fore_f", 108, 92, "arm_f")
    s.part(s.capsule(108, 92, 112, 124, 10, 12), BASALT_D, bias=-0.1, edge=False)
    s.part(s.ellipse(113, 133, 13, 11), BASALT_D)
    _crack(s, [(102, 70), (107, 80), (104, 90), (110, 102), (108, 116), (114, 128)], mid, hot)
    # legs
    for grp, sub, hx, kx, fx, tone, r in (("leg_f", "shin_f", 62, 60, 62, BASALT_D, 12), ("leg_n", "shin_n", 88, 92, 96, BASALT, 13)):
        s.g(grp, hx, 112)
        s.part(s.capsule(hx, 112, kx, 138, r), tone)
        s.g(sub, kx, 138, grp)
        s.part(s.capsule(kx, 138, kx + 1, 160, r - 2), tone, edge=False)
        s.part(s.ellipse(kx, 139, r - 3, 6), BASALT_D)                  # knee stone
        s.part(s.ellipse(fx + 2, 168, r + 4, 6.5), tone)
        _crack(s, [(hx - 2, 116), (kx + 3, 126), (kx - 3, 136), (kx + 2, 148), (kx - 1, 158)], mid, hot)
        for dx in (-6, 0, 6):
            s.px(fx + 10 + dx, 171, low)
    # hips and hunched torso
    s.g("body")
    s.part(s.ellipse(75, 108, 27, 14), BASALT_D)
    s.part(s.poly([(38, 46), (70, 38), (108, 42), (116, 72), (102, 104), (52, 106), (36, 78)]), BASALT, bulge=1.1)
    # the open chest: grey-white fire behind black ribs
    s.fill(s.ellipse(80, 72, 19, 21), low, glow=True)
    s.fill(s.ellipse(80, 73, 15, 17), mid, glow=True)
    s.fill(s.ellipse(81, 74, 9, 11), hot, glow=True)
    for i in range(5):
        y = 56 + i * 8
        s.part(s.capsule(60, y + 2, 80, y - 1, 2.3) | s.capsule(80, y - 1, 100, y + 2, 2.3), BASALT)
    s.part(s.capsule(80, 50, 80, 94, 2.6), BASALT_D)                    # breastbone
    for pts in ([(60, 66), (52, 70), (48, 80), (42, 84)], [(100, 68), (106, 76), (104, 86), (110, 92)],
                [(74, 94), (70, 100), (74, 106), (68, 112)], [(90, 94), (94, 102), (90, 110)], [(62, 50), (54, 54), (50, 62)]):
        _crack(s, pts, mid, hot)
    # basalt columns standing on both shoulders
    for x, top in ((106, 30), (113, 24), (120, 34)):
        _slab(s, [(x, top), (x + 7, top), (x + 7, 52), (x, 52)], BASALT_D, depth=(2, -2), seed=x)
    # head: heavy jaw, swept horns, eyes of grey fire
    s.g("head", 84, 44)
    s.part(s.poly([(80, 22), (66, 8), (62, -2), (72, 6), (86, 18)]), BASALT_D)      # far horn
    s.part(s.ellipse(88, 30, 15, 13), BASALT)
    s.part(s.poly([(84, 18), (72, 2), (70, -8), (80, 0), (92, 16)]), BASALT)        # near horn
    s.fill(s.poly([(90, 25), (97, 27), (96, 30), (90, 29)]), mid, glow=True)
    s.fill(s.poly([(99, 27), (103, 28), (103, 31), (99, 30)]), mid, glow=True)
    s.pxs([(93, 27), (94, 28), (101, 29)], hot, glow=True)
    s.line(88, 22, 98, 25, BASALT[0])
    s.g("jaw", 82, 36, "head")
    s.fill(s.poly([(86, 37), (104, 37), (103, 41), (87, 41)]), mid, glow=True)
    s.fill(s.poly([(88, 38), (102, 38), (101, 40), (89, 40)]), hot, glow=True)
    s.part(s.poly([(80, 40), (105, 40), (102, 48), (86, 49)]), BASALT_D)
    for x in (89, 93, 97, 101):
        s.fill(s.poly([(x, 40), (x + 2, 40), (x + 1, 37)]), BASALT[3])              # teeth
    # crown of black smoke, drifting back
    s.g("plume", 84, 16, "head")
    for cx, cy, rx, ry in ((72, 16, 7, 6), (76, 6, 8, 7), (85, 0, 9, 7), (96, 2, 8, 7), (104, 10, 7, 6), (108, 19, 5, 5)):
        s.part(s.ellipse(cx, cy, rx, ry), SMOKE, edge=False)             # a ring of smoke puffs worn like a crown
    for x, top in ((74, -8), (84, -14), (95, -11), (104, -3)):
        s.part(s.poly([(x - 3, top + 12), (x + 3, top + 12), (x + 1, top)]), SMOKE, edge=False)
    s.pxs([(70, -12), (88, -20), (99, -17), (108, -8), (80, -17)], SMOKE[2])
    # near arm: the great hammer arm
    s.g("weapon", 42, 58)
    s.part(s.capsule(42, 58, 32, 92, 13.5), BASALT)
    s.g("body")
    for x, top in ((20, 32), (27, 24), (34, 18), (41, 26), (48, 34)):
        _slab(s, [(x, top), (x + 7, top), (x + 7, 54), (x, 54)], BASALT, depth=(3, -3), chips=1, seed=x)
    s.g("hand_w", 32, 92, "weapon")
    s.part(s.capsule(32, 92, 36, 126, 12, 14.5), BASALT, edge=False)
    s.part(s.ellipse(38, 137, 16, 13.5), BASALT)
    for x in (30, 38, 46):
        s.line(x, 140, x, 149, BASALT[0])
    _crack(s, [(40, 62), (34, 74), (38, 86), (30, 98), (36, 110), (32, 122), (40, 132), (36, 144)], mid, hot)
    _crack(s, [(36, 110), (44, 116), (42, 124)], mid)
    s.ink()
    _dust(s, 40, 9)
    s.shadow(76, 173, 44, 5)
    return s


def vael_orrun(pose=None, pad=0):
    """Vael-Orrun, the High King: a still figure of black glass with a crown-shaped hole for a face."""
    s = Sprite(176, 336, pose, pad, origin=(0, 32))
    # cape of black glass behind
    s.g("cloak", 88, 70)
    cape = [(52, 70), (124, 70), (152, 200), (160, 286), (124, 294), (52, 294), (16, 286), (24, 200)]
    s.fill(s.poly(cape), GLASS_D[1])
    for (x0, y0, x1, y1), t in (((52, 70, 24, 200), 3), ((24, 200, 16, 286), 2), ((124, 70, 152, 200), 0), ((152, 200, 160, 286), 0),
                                ((40, 150, 34, 290), 2), ((138, 150, 144, 290), 0)):
        s.line(x0, y0, x1, y1, GLASS_D[t])
    # hanging arm (rear), long fingers
    s.g("arm_f", 62, 80)
    s.part(s.capsule(62, 80, 46, 140, 7.5), GLASS, bias=-0.1)
    s.g("fore_f", 46, 140, "arm_f")
    s.part(s.capsule(46, 140, 42, 196, 6.5, 4.5), GLASS, bias=-0.1, edge=False)
    for dx, ln in ((-5, 16), (-2, 22), (1, 24), (4, 20)):
        s.part(s.capsule(42 + dx, 198, 41 + dx * 1.4, 198 + ln, 1.4, 0.8), GLASS, edge=False)
    # robe: long faceted planes of glass
    s.g("body")
    facets = [([(64, 72), (78, 72), (72, 292), (44, 292), (54, 180)], 3), ([(78, 72), (90, 72), (92, 292), (72, 292)], 2),
              ([(90, 72), (102, 72), (112, 292), (92, 292)], 1), ([(102, 72), (112, 72), (122, 180), (132, 292), (112, 292)], 0)]
    for pts, t in facets:
        s.fill(s.poly(pts), GLASS[t])
    for (x0, y0, x1, y1), t in (((78, 72, 72, 292), 4), ((90, 72, 92, 292), 3), ((102, 72, 112, 292), 2), ((64, 72, 54, 180), 4), ((54, 180, 44, 292), 4)):
        s.line(x0, y0, x1, y1, GLASS[t])
    s.line(67, 90, 61, 170, (150, 150, 190))                           # a hard glass highlight
    s.line(68, 96, 64, 150, (220, 222, 245))
    # hem crumbling to ash
    rng = np.random.default_rng(3)
    for _ in range(70):
        x, y = int(rng.integers(40, 136)), int(rng.integers(284, 300))
        s.px(x, y, GREY_GLOW[int(rng.integers(0, 2))] if rng.random() < 0.5 else GLASS[int(rng.integers(0, 3))])
    # the stolen Heartstone light in the chest, and cracks bleeding the six colours
    s.fill(s.poly([(88, 96), (100, 114), (88, 138), (76, 114)]), (255, 214, 120), glow=True)
    s.fill(s.poly([(88, 101), (96, 114), (88, 131), (80, 114)]), (255, 240, 190), glow=True)
    s.fill(s.poly([(88, 107), (92, 114), (88, 123), (84, 114)]), (255, 255, 245), glow=True)
    cracks = [[(96, 106), (106, 98), (104, 88), (112, 80)], [(100, 114), (110, 120), (108, 134), (118, 150), (114, 170)],
              [(92, 132), (98, 150), (94, 170), (102, 200), (98, 236)], [(84, 132), (78, 152), (82, 176), (72, 206), (76, 250)],
              [(76, 114), (66, 122), (68, 138), (58, 156), (60, 180)], [(80, 106), (70, 98), (72, 86), (66, 78)]]
    for pts, col in zip(cracks, RING):
        _crack(s, pts, col, (255, 255, 255))
    # shoulders: tall angular pauldrons
    for sx, sgn in ((62, -1), (114, 1)):
        s.fill(s.poly([(sx - 14 * sgn, 66), (sx + 12 * sgn, 84), (sx + 20 * sgn, 76), (sx + 22 * sgn, 50)]), GLASS[1 if sgn > 0 else 3])
        s.fill(s.poly([(sx + 12 * sgn, 84), (sx + 20 * sgn, 76), (sx + 26 * sgn, 96)]), GLASS[0 if sgn > 0 else 2])
        s.line(sx - 14 * sgn, 66, sx + 22 * sgn, 50, GLASS[4 if sgn < 0 else 2])
        s.fill(s.poly([(sx + 14 * sgn, 60), (sx + 22 * sgn, 50), (sx + 28 * sgn, 22)]), GLASS[2 if sgn < 0 else 0])
        s.line(sx + 14 * sgn, 60, sx + 28 * sgn, 22, GLASS[4 if sgn < 0 else 1])
    # head: a tall mask of glass under the black crown with six empty sockets
    s.g("head", 88, 68)
    s.part(s.poly([(80, 60), (96, 60), (98, 72), (78, 72)]), GLASS_D)                  # neck
    head = s.poly([(72, 22), (104, 22), (110, 44), (100, 66), (76, 66), (66, 44)])
    s.part(head, GLASS, bulge=0.7)
    s.line(72, 24, 67, 44, GLASS[4])
    s.line(67, 44, 76, 65, GLASS[3])
    s.fill(s.poly([(66, 14), (110, 14), (108, 24), (68, 24)]), GLASS_D[2])
    s.line(66, 14, 110, 14, GLASS[4])
    for i, x in enumerate((66, 74, 82, 90, 98, 106)):
        h = (26, 34, 42, 42, 34, 26)[i]
        s.fill(s.poly([(x - 1, 15), (x + 6, 15), (x + 2.5, 15 - h)]), GLASS_D[3 if i < 3 else 1])
        s.line(x - 1, 15, x + 2, 15 - h, GLASS[4] if i < 3 else GLASS[2])
        s.fill(s.rect(x + 1, 17, x + 4, 21), (6, 5, 10))                               # an empty socket
        s.px(x + 1, 17, (120, 120, 150))
    # the crown-shaped hole where the face should be: cut clean through the sprite
    hole = s.poly([(77, 60), (77, 36), (82, 46), (88, 32), (94, 46), (99, 36), (99, 60)])
    grow = hole.copy()
    grow[1:] |= hole[:-1]
    grow[:-1] |= hole[1:]
    grow[:, 1:] |= hole[:, :-1]
    grow[:, :-1] |= hole[:, 1:]
    s.fill(grow & ~hole & s.a, (214, 216, 232), glow=True)
    s.a[hole] = False
    # raised arm (front): reaching out, palm open, colour draining to grey around the hand
    s.g("weapon", 112, 82)
    s.part(s.capsule(112, 82, 128, 132, 7.5), GLASS)
    s.g("hand_w", 128, 132, "weapon")
    s.part(s.capsule(128, 132, 150, 108, 6.5, 4.5), GLASS, edge=False)
    for ang, ln in ((-1.3, 16), (-0.9, 20), (-0.5, 21), (-0.1, 18), (0.5, 12)):
        s.part(s.capsule(152, 106, 152 + np.cos(ang) * ln, 106 + np.sin(ang) * ln, 1.5, 0.8), GLASS, edge=False)
    s.line(114, 86, 126, 126, (150, 150, 190))
    for x, y in ((160, 84), (166, 92), (158, 76), (170, 100), (164, 108), (172, 86), (154, 70)):
        s.px(x, y, GREY_GLOW[1], glow=True)
    s.ink()
    s.a[hole] = False
    _dust(s, 50, 2)
    s.shadow(88, 296, 50, 5)
    return s


BOSSES = {"gorrath": gorrath, "cinder_tyrant": cinder_tyrant, "vael_orrun": vael_orrun}
CREATURES.update(BOSSES)
