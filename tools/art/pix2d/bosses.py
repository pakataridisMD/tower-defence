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
SKULL = ramp("5c5468", spread=0.6, shift=0.03)        # Vael-Orrun's face: dead ashen glass
SOCKET = (6, 2, 6)
EYE_D = (44, 6, 9)
EYE = [(150, 16, 18), (236, 64, 28), (255, 168, 72), (255, 246, 214)]
MAW = [(22, 4, 8), (74, 10, 12), (176, 40, 20), (250, 128, 44), (255, 226, 150)]
TOOTH = ramp("cfc2a2", spread=0.5)
DROOL = (255, 196, 120)
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


def _vael_head(s, dx=0, dy=0):
    """Vael-Orrun's head (crown, skull face, jaw), drawn as the "head" group; dx, dy move it for other bodies."""
    assert not s._ident, "give the sprite an origin or pad so the head can be moved"
    old = s.pose
    r, hx, hy = old.get("head", (0, 0, 0))
    s.pose = {**old, "head": (r, hx + dx, hy + dy)}
    # head: a gaunt skull of ashen glass with the black crown driven into it, six burning eyes, and a jaw hanging open
    # on the stolen Heartstone fire in his throat. The jaw hinges behind the cheek so it can gape wider when he strikes.
    s.g("head", 88, 68)
    s.part(s.poly([(80, 60), (98, 60), (100, 74), (78, 74)]), GLASS_D)                  # neck
    throat = s.poly([(73, 54), (105, 54), (105, 64), (101, 84), (93, 94), (83, 94), (77, 84), (73, 64)])
    s.fill(throat, MAW[0])
    s.fill(s.ellipse(89, 80, 10, 14) & throat, MAW[1])
    for x0, y0, x1, y1 in ((77, 58, 78, 74), (102, 58, 101, 76), (80, 58, 83, 66)):    # sinew strung across the gape
        s.line(x0, y0, x1, y1, MAW[1])
    skull = s.poly([(71, 18), (105, 18), (110, 25), (114, 36), (113, 44), (105, 50), (103, 58), (75, 58), (72, 50), (63, 44), (62, 36), (66, 25)])
    s.part(skull, SKULL, bulge=0.8)
    s.fill(s.poly([(63, 44), (72, 50), (75, 58), (77, 50)]), SKULL[0])                  # the cheeks fall in under the bone
    s.fill(s.poly([(113, 44), (105, 50), (103, 58), (102, 50)]), SKULL[1])
    s.line(64, 43, 76, 48, SKULL[4])                                                    # cheekbone ridges catch the light
    s.line(102, 48, 112, 43, SKULL[3])
    s.line(66, 26, 63, 36, SKULL[4])
    s.line(63, 36, 64, 42, SKULL[4])
    s.fill(s.rect(62, 23, 114, 25) & skull, SKULL[0])                                    # shadow cast by the crown
    s.line(88, 22, 88, 24, SKULL[0])                                                    # a seam down the brow
    for pts in (((70, 22), (67, 29)), ((106, 22), (109, 28)), ((78, 22), (80, 30)), ((98, 22), (97, 30))):
        (x0, y0), (x1, y1) = pts
        s.line(x0, y0, x1, y1, SKULL[0])                                                # bone grooves under the crown
    # his old signature kept as a wound: a crown-shaped gap burned into the brow, empty grey light (the Unmaking)
    gap = s.poly([(83, 34), (83, 26), (85.5, 29), (88, 25), (90.5, 29), (93, 26), (93, 34)])
    s.fill(gap, GREY_GLOW[2], glow=True)
    s.fill(s.poly([(84, 33), (84, 29), (86, 31), (88, 28), (90, 31), (92, 29), (92, 33)]), GREY_GLOW[3], glow=True)
    # a scowling brow over two deep sockets, each with a slit-pupilled eye of white fire
    s.fill(s.poly([(64, 28), (89, 37), (112, 26), (112, 31), (89, 41), (64, 32)]), SKULL[1])
    s.line(64, 27, 89, 36, SKULL[4])
    s.line(89, 36, 112, 25, SKULL[3])
    for pts in ([(66, 33), (88, 41), (86, 48), (72, 47), (66, 40)], [(91, 41), (111, 31), (112, 39), (106, 47), (93, 48)]):
        s.fill(s.poly(pts), SOCKET)
    for ex, ey in ((77, 42), (101, 41)):
        sock = s.ellipse(ex, ey + 0.5, 5, 3) & s.a & (s.rgb == SOCKET).all(-1)
        s.fill(sock, EYE_D, glow=True)                                                  # the socket smoulders round it
        s.fill(s.rect(ex - 4, ey - 1, ex + 4, ey + 2), EYE[0], glow=True)
        s.fill(s.rect(ex - 3, ey - 1, ex + 3, ey + 1), EYE[1], glow=True)
        s.fill(s.rect(ex - 2, ey - 1, ex + 2, ey), EYE[2], glow=True)
        s.pxs([(ex - 1, ey - 1), (ex + 1, ey - 1)], EYE[3], glow=True)
        s.line(ex, ey - 2, ex, ey + 2, SOCKET)                                          # the slit pupil
    # four smaller eyes crowding the temples and cheeks: six in all, one for each crown that betrayed him
    for ex, ey in ((65, 36), (69, 47), (111, 34), (108, 46)):
        s.fill(s.rect(ex - 1, ey - 1, ex + 2, ey + 1), SOCKET)
        s.fill(s.rect(ex, ey, ex + 1, ey), EYE[1], glow=True)
        s.px(ex, ey, EYE[3], glow=True)
    # fire weeping from the eyes down the cheeks
    for pts in ([(75, 47), (74, 52), (76, 56)], [(103, 47), (105, 51), (104, 56)]):
        _crack(s, pts, EYE[1], EYE[2])
    s.fill(s.poly([(86, 46), (89, 45), (88, 53)]), SOCKET)                              # a nose of two slits
    s.fill(s.poly([(90, 45), (93, 46), (91, 53)]), SOCKET)
    # the crown, black glass hammered down into the skull; its spikes bleed thin cracks into the brow
    s.fill(s.poly([(64, 12), (112, 12), (110, 23), (66, 23)]), GLASS_D[2])
    s.line(64, 12, 112, 12, GLASS[4])
    s.line(66, 23, 110, 23, GLASS_D[0])
    for i, x in enumerate((65, 73, 81, 89, 97, 105)):
        h = (24, 33, 42, 42, 33, 24)[i]
        s.fill(s.poly([(x - 1, 13), (x + 7, 13), (x + 3, 13 - h)]), GLASS_D[3 if i < 3 else 1])
        s.line(x - 1, 13, x + 2, 13 - h, GLASS[4] if i < 3 else GLASS[2])
        s.fill(s.rect(x + 2, 16, x + 4, 20), (6, 5, 10))                               # an empty socket where a gem was
    for pts in ([(72, 23), (74, 27), (72, 30)], [(96, 23), (94, 26), (96, 29)], [(106, 23), (108, 26)]):
        _crack(s, pts, EYE[0])
    # upper fangs, long and uneven, hanging into the fire
    for x, ln in ((76, 4), (79, 11), (82, 4), (85, 6), (88, 3), (91, 6), (94, 4), (97, 5), (100, 13), (103, 4)):
        s.fill(s.poly([(x - 1.2, 57), (x + 1.6, 57), (x + 0.3, 57 + ln)]), TOOTH[2])
        s.line(x - 1, 57, x, 57 + ln - 1, TOOTH[4])
        s.px(x + 1, 57, TOOTH[0])
    for x0, y0, y1 in ((86, 62, 71), (96, 61, 71)):                                     # strings of glowing spit
        s.line(x0, y0, x0 + 1, y1, DROOL, glow=True)
    # the lower jaw: a long bony chin hinged behind the cheek, lower fangs pointing up
    s.g("jaw", 74, 56, "head")
    gullet = s.poly([(73, 72), (105, 72), (101, 84), (93, 94), (83, 94), (77, 84)])
    s.fill(gullet, MAW[0])
    s.fill(s.ellipse(89, 80, 10, 14) & gullet, MAW[1])                                 # the fire sits low and drops with the jaw
    s.fill(s.ellipse(90, 83, 6, 10) & gullet, MAW[2], glow=True)
    s.fill(s.ellipse(90, 86, 3, 6) & gullet, MAW[3], glow=True)
    s.fill(s.ellipse(90, 88, 1.5, 3) & gullet, MAW[4], glow=True)
    jaw = s.poly([(72, 56), (71, 66), (74, 82), (81, 95), (89, 99), (97, 95), (103, 84), (106, 66), (106, 56),
                  (102, 60), (100, 80), (94, 90), (88, 92), (82, 89), (77, 78), (76, 60)])
    s.part(jaw, SKULL, bulge=0.6)
    s.line(72, 57, 74, 82, SKULL[4])
    s.line(74, 82, 81, 95, SKULL[3])
    for x, y, ln in ((78, 76, 4), (80, 84, 10), (84, 89, 4), (88, 91, 5), (92, 90, 4), (96, 87, 5), (99, 80, 11), (101, 70, 4)):
        s.fill(s.poly([(x - 1.2, y), (x + 1.6, y), (x + 0.3, y - ln)]), TOOTH[2])
        s.line(x - 1, y, x, y - ln + 1, TOOTH[4])
    s.pose = old
    s.g("body")


def vael_orrun(pose=None, pad=0):
    """Vael-Orrun, the High King: a towering figure of black glass under a crown of spikes. His face is a gaunt skull
    of ashen glass with six burning eyes and a jaw torn open to the stolen Heartstone fire in his throat."""
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
        s.line(41 + dx * 1.4, 198 + ln, 42 + dx * 1.6, 202 + ln, TOOTH[2])
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
    _vael_head(s)
    # raised arm (front): reaching out, palm open, colour draining to grey around the hand
    s.g("weapon", 112, 82)
    s.part(s.capsule(112, 82, 128, 132, 7.5), GLASS)
    s.g("hand_w", 128, 132, "weapon")
    s.part(s.capsule(128, 132, 150, 108, 6.5, 4.5), GLASS, edge=False)
    for ang, ln in ((-1.3, 16), (-0.9, 20), (-0.5, 21), (-0.1, 18), (0.5, 12)):
        s.part(s.capsule(152, 106, 152 + np.cos(ang) * ln, 106 + np.sin(ang) * ln, 1.5, 0.8), GLASS, edge=False)
        tx, ty = 152 + np.cos(ang) * ln, 106 + np.sin(ang) * ln                         # a hooked bone talon on each finger
        s.line(tx, ty, tx + np.cos(ang + 0.6) * 4, ty + np.sin(ang + 0.6) * 4, TOOTH[3])
    s.line(114, 86, 126, 126, (150, 150, 190))
    for x, y in ((160, 84), (166, 92), (158, 76), (170, 100), (164, 108), (172, 86), (154, 70)):
        s.px(x, y, GREY_GLOW[1], glow=True)
    s.ink()
    _dust(s, 50, 2)
    s.shadow(88, 296, 50, 5)
    return s


SEA = ramp("1c4656", spread=0.5, shift=0.0)
SEA_D = ramp("10303c", spread=0.4, shift=0.0)
TEAL = ramp("3a8a8a", spread=0.5)
PALE = ramp("9a9088", spread=0.42, shift=0.02)      # ashen Herald skin, so the empty eyes read
BEAK = ramp("d8c078", spread=0.5)
VEIL = ramp("8a8894", spread=0.55, shift=0.0)
VEIL_D = ramp("5c5a68", spread=0.5, shift=0.0)
GHOSTV = [(120, 96, 170), (176, 150, 226), (226, 210, 255), (250, 246, 255)]
EMBERW = [(196, 74, 20), (250, 132, 36), (255, 194, 84), (255, 232, 160), (255, 252, 236)]
CLOUD = ramp("34343e", spread=0.5, shift=0.0)
CLOUD_D = ramp("22222a", spread=0.4, shift=0.0)
BOLT = [(150, 140, 230), (214, 208, 255), (250, 250, 255)]
THORN = ramp("3a3040", spread=0.5, shift=0.02)
THORN_D = ramp("261f2c", spread=0.4, shift=0.02)
SATCHEL = ramp("7a5632", spread=0.5)


def _herald_face(s, x, y, dark=False, big=1):
    """Two empty eyes and an open mouth of grey light, looking right from (x, y) = the nearer eye."""
    c0, c1 = ((70, 74, 86), (110, 114, 126)) if dark else (GREY_GLOW[2], GREY_GLOW[3])
    for ex in (x, x + 4 * big):
        s.fill(s.rect(ex, y, ex + 2 * big, y + 2 * big), c0, glow=True)
        s.px(ex, y, c1, glow=True)
    s.fill(s.rect(x + 1, y + 4 * big, x + 1 + 4 * big, y + 4 * big + 2 * big), c0, glow=True)
    s.px(x + 2, y + 4 * big, c1, glow=True)


def ourra(pose=None, pad=0):
    """Saltmother Ourra, the Drowned Herald: an old priestess inside a walking column of black seawater."""
    s = Sprite(96, 150, pose, pad)
    # the column: a wave crest on top, a spreading foot of foam
    s.part(s.ellipse(48, 136, 40, 9), SEA_D)
    s.part(s.capsule(48, 30, 48, 122, 27, 31), SEA, bulge=0.8)
    s.part(s.poly([(22, 34), (30, 10), (44, 22), (56, 4), (66, 20), (78, 12), (74, 36)]), SEA)      # crest
    for x, y in ((30, 12), (56, 6), (78, 14), (40, 20), (66, 20)):
        s.pxs([(x, y), (x + 1, y - 1), (x - 1, y + 1)], (220, 240, 240))
    for x in range(12, 86, 5):
        s.px(x, 138 + (x * 7) % 5, (200, 226, 226))
        s.px(x + 2, 133 + (x * 3) % 4, (150, 200, 204))
    for x, y0, y1 in ((27, 44, 112), (33, 60, 126), (66, 40, 100), (72, 64, 124), (60, 96, 128)):  # currents in the water
        s.line(x, y0, x + 1, y1, SEA[3])
    s.line(24, 40, 23, 110, SEA[4])
    # the priestess inside: tattered teal robes, grey hair, arms lifted
    s.g("cloak", 46, 60)
    s.part(s.poly([(38, 58), (54, 58), (60, 100), (57, 118), (52, 110), (47, 120), (42, 108), (36, 116), (34, 96)]), TEAL)
    s.line(44, 66, 42, 106, TEAL[1])
    s.line(51, 68, 53, 104, TEAL[1])
    s.g("arm_f", 40, 62)
    s.part(s.capsule(40, 62, 30, 52, 2.6, 2.0), TEAL, bias=-0.1)
    s.part(s.ellipse(29, 50, 2.2, 2.4), PALE)
    s.g("head", 47, 56)
    s.part(s.poly([(40, 44), (46, 38), (54, 42), (52, 62), (44, 66), (38, 58)]), VEIL)                # long grey hair
    s.part(s.ellipse(49, 49, 5.2, 6.0), PALE)
    _herald_face(s, 49, 46)
    s.part(s.poly([(42, 42), (48, 37), (55, 41), (50, 44), (44, 47)]), VEIL)
    s.g("weapon", 52, 62)
    s.part(s.capsule(52, 62, 60, 56, 2.8, 2.2), TEAL)
    s.g("hand_w", 60, 56, "weapon")
    s.part(s.capsule(60, 56, 68, 46, 2.2, 1.8), TEAL, edge=False)
    s.part(s.ellipse(69, 44, 2.4, 2.6), PALE)
    # drowned lanterns and fish circling inside
    s.g("aura", 48, 80)
    for x, y in ((28, 72), (68, 84), (36, 104), (62, 36)):
        s.fill(s.rect(x, y, x + 4, y + 5), (90, 70, 40))
        s.fill(s.rect(x + 1, y + 1, x + 3, y + 4), (255, 190, 90), glow=True)
        s.px(x + 1, y - 1, (60, 50, 40))
    for x, y, d in ((62, 70, 1), (30, 88, -1), (56, 112, 1), (34, 56, -1), (70, 104, -1)):
        s.part(s.ellipse(x, y, 3.2, 1.6), VEIL, edge=False)
        s.pxs([(x - 4 * d, y - 1), (x - 4 * d, y + 1), (x - 3 * d, y)], VEIL[2])
        s.px(x + 2 * d, y, DARK)
    s.ink((8, 26, 34))
    _dust(s, 22, 4)
    s.shadow(48, 143, 38, 4)
    return s


def vesper(pose=None, pad=0):
    """The Pale Vesper, the Hollow Herald: a thin, very tall singer in mourning veils, with a choir of ghost-lights."""
    s = Sprite(96, 150, pose, pad)
    # the choir behind her
    s.g("aura", 30, 60)
    for x, y, r in ((14, 40, 5), (24, 66, 4.5), (10, 84, 4), (30, 26, 4), (20, 104, 3.5)):
        s.fill(s.ellipse(x, y, r + 1.5, r + 1.5), GHOSTV[0], glow=True)
        s.fill(s.ellipse(x, y, r, r), GHOSTV[1], glow=True)
        s.fill(s.ellipse(x + 0.5, y - 0.5, r * 0.5, r * 0.5), GHOSTV[3], glow=True)
        s.fill(s.poly([(x - r, y + 2), (x + r, y + 2), (x - 2, y + r * 2.6)]), GHOSTV[0], glow=True)   # a trailing wisp
        s.pxs([(x + 1, y), (x + 3, y)], (60, 40, 90))
        s.px(x + 2, y + 2, (60, 40, 90))                                                         # tiny singing mouths
    # trailing veils
    s.g("cloak", 56, 30)
    s.part(s.poly([(50, 26), (62, 24), (60, 80), (52, 132), (40, 140), (30, 134), (42, 80)]), VEIL_D)
    s.line(48, 40, 38, 130, VEIL_D[0])
    s.line(54, 44, 48, 128, VEIL_D[3])
    # tall narrow gown to the ground
    s.g("body")
    s.part(s.poly([(52, 34), (68, 34), (70, 80), (76, 140), (46, 140), (50, 80)]), VEIL, bulge=0.8)
    for x0, x1 in ((54, 50), (60, 60), (66, 70)):
        s.line(x0, 48, x1, 138, VEIL[1])
    s.part(s.rect(52, 62, 70, 64), VEIL_D, flat=True)
    for x in range(46, 77, 3):
        s.px(x, 140 + x % 2, VEIL_D[1])
    # folded far arm
    s.g("arm_f", 66, 38)
    s.part(s.capsule(66, 38, 72, 56, 2.4, 2.0), VEIL_D, bias=-0.1)
    # head: veiled, mouth always open in song
    s.g("head", 60, 32)
    s.part(s.capsule(60, 34, 61, 26, 2.6), PALE)
    s.part(s.ellipse(62, 17, 6.5, 8.5), PALE)
    s.part(s.poly([(52, 16), (58, 6), (66, 5), (70, 10), (63, 12), (58, 20), (56, 34), (50, 34)]), VEIL)     # hood of the veil
    s.fill(s.rect(63, 13, 65, 15), GREY_GLOW[2], glow=True)
    s.fill(s.rect(67, 13, 69, 15), GREY_GLOW[2], glow=True)
    s.g("jaw", 62, 20, "head")
    s.fill(s.ellipse(66, 21.5, 2.6, 3.4), GREY_GLOW[1], glow=True)
    s.fill(s.ellipse(66, 21.5, 1.6, 2.4), GREY_GLOW[3], glow=True)
    # rings of sung light leaving the mouth
    s.g("plume", 66, 21, "head")
    for r, t in ((7, 2), (12, 1), (17, 0)):
        ring = s.ellipse(70 + r * 0.6, 21, r * 0.5, r) & ~s.ellipse(69 + r * 0.6, 21, r * 0.5, r)
        s.fill(ring & ~s.a, GHOSTV[t], glow=True)
    # near arm lifted, long fingers conducting
    s.g("weapon", 56, 38)
    s.part(s.capsule(56, 38, 62, 54, 2.6, 2.2), VEIL)
    s.g("hand_w", 62, 54, "weapon")
    s.part(s.capsule(62, 54, 76, 44, 2.2, 1.6), VEIL, edge=False)
    for dx, dy in ((5, -5), (6, -2), (6, 1), (4, 3)):
        s.line(77, 43, 77 + dx, 43 + dy, PALE[3])
    s.ink()
    _dust(s, 20, 6)
    s.shadow(60, 144, 20, 3)
    return s


def ashwick(pose=None, pad=0):
    """Ashwick the Kindled, the Flame Herald: a messenger boy made of white-hot embers, flame streaming behind."""
    s = Sprite(84, 80, pose, pad)
    E = EMBERW
    # flame cape streaming back
    s.g("cloak", 40, 30)
    s.fill(s.poly([(40, 26), (26, 20), (10, 24), (20, 30), (2, 36), (18, 40), (6, 50), (24, 48), (18, 60), (36, 48), (42, 38)]), E[0], glow=True)
    s.fill(s.poly([(40, 28), (28, 24), (16, 27), (24, 32), (10, 37), (22, 40), (14, 48), (28, 45), (36, 44)]), E[1], glow=True)
    s.fill(s.poly([(40, 30), (30, 28), (26, 33), (20, 38), (28, 40), (34, 40)]), E[2], glow=True)
    s.pxs([(4, 28), (0, 42), (8, 56), (14, 64), (2, 20)], E[1], glow=True)
    # far leg kicking back, far arm forward (running)
    s.g("leg_f", 44, 50)
    s.part(s.capsule(44, 50, 38, 58, 3.0), E, bias=-0.25, glow=True)
    s.g("shin_f", 38, 58, "leg_f")
    s.part(s.capsule(38, 58, 30, 62, 2.6), E, bias=-0.25, edge=False, glow=True)
    s.part(s.ellipse(28, 63, 3.0, 2.0), E, bias=-0.25, glow=True)
    s.g("arm_f", 50, 34)
    s.part(s.capsule(50, 34, 58, 38, 2.4), E, bias=-0.2, glow=True)
    s.g("fore_f", 58, 38, "arm_f")
    s.part(s.capsule(58, 38, 64, 33, 2.2), E, bias=-0.2, edge=False, glow=True)
    # near leg striding, torso leaning into the run
    s.g("leg_n", 48, 50)
    s.part(s.capsule(48, 50, 55, 59, 3.4), E, glow=True)
    s.g("shin_n", 55, 59, "leg_n")
    s.part(s.capsule(55, 59, 54, 69, 3.0), E, edge=False, glow=True)
    s.part(s.ellipse(57, 71, 4.0, 2.2), E, glow=True)
    s.g("body")
    s.part(s.poly([(40, 30), (52, 28), (54, 40), (52, 52), (42, 52), (40, 40)]), E, glow=True)
    # the messenger's satchel: the one thing that is not fire, and it is burning
    s.line(41, 30, 52, 48, SATCHEL[0])
    s.line(42, 30, 53, 48, SATCHEL[2])
    s.part(s.poly([(42, 44), (53, 44), (54, 54), (43, 55)]), SATCHEL)
    s.part(s.poly([(42, 44), (53, 44), (52, 48), (43, 48)]), SATCHEL, flat=True, bias=0.2)
    s.px(47, 49, (230, 190, 90))
    s.pxs([(44, 43), (50, 42), (53, 43)], E[2], glow=True)
    s.pxs([(45, 41), (51, 40)], E[3], glow=True)
    # head, hair of flame, empty grey face
    s.g("head", 48, 28)
    s.part(s.ellipse(50, 20, 6.4, 6.6), E, glow=True)
    s.g("plume", 46, 16, "head")
    s.fill(s.poly([(44, 20), (40, 12), (45, 14), (44, 6), (50, 12), (52, 5), (55, 13), (56, 16), (48, 15)]), E[1], glow=True)
    s.fill(s.poly([(46, 18), (44, 13), (48, 14), (48, 9), (52, 14), (54, 16)]), E[3], glow=True)
    s.g("head", 48, 28)
    _herald_face(s, 51, 18, dark=True)
    # near arm pumping back
    s.g("weapon", 44, 33)
    s.part(s.capsule(44, 33, 38, 41, 2.8), E, glow=True)
    s.g("hand_w", 38, 41, "weapon")
    s.part(s.capsule(38, 41, 44, 46, 2.5), E, edge=False, glow=True)
    s.ink((120, 40, 14))
    _dust(s, 14, 8)
    s.shadow(46, 74, 16, 2.6)
    return s


def vholt(pose=None, pad=0):
    """Vholt Stormcrown, the Sky Herald: an old warchief crowned with lightning, riding a thunderbird of black cloud."""
    s = Sprite(170, 130, pose, pad)
    # far wing, raised
    s.g("wing_f", 86, 62)
    s.part(s.poly([(86, 62), (104, 22), (132, 6), (124, 24), (138, 26), (124, 40), (132, 46), (112, 56)]), CLOUD_D, flat=True, bias=-0.2)
    # tail of streaming cloud
    s.g("tail", 58, 78)
    s.part(s.poly([(60, 70), (36, 68), (20, 62), (26, 74), (8, 76), (24, 84), (14, 94), (38, 88), (58, 86)]), CLOUD_D)
    s.g("tail2", 24, 78, "tail")
    for x, y in ((6, 70), (2, 82), (10, 98), (0, 92)):
        s.part(s.ellipse(x, y, 3, 2), CLOUD_D, edge=False)
    # body of rolling black cloud
    s.g("body")
    for cx, cy, rx, ry in ((70, 78, 20, 14), (92, 76, 20, 15), (82, 68, 18, 11), (106, 72, 13, 12)):
        s.part(s.ellipse(cx, cy, rx, ry), CLOUD, edge=False)
    for cx, cy, r in ((62, 88, 7), (76, 92, 8), (92, 91, 8), (104, 86, 6)):
        s.part(s.ellipse(cx, cy, r, r * 0.7), CLOUD_D, edge=False)
    # lightning in its belly, and talons of white fire
    for pts in ([(72, 92), (68, 100), (74, 104), (70, 114)], [(94, 92), (98, 100), (93, 106), (97, 116)]):
        for a, b in zip(pts, pts[1:]):
            s.line(*a, *b, BOLT[2], glow=True)
            s.line(a[0] + 1, a[1], b[0] + 1, b[1], BOLT[0], glow=True)
    _crack(s, [(64, 74), (72, 80), (80, 74), (90, 82), (100, 76)], BOLT[1], BOLT[2])
    # neck and head: hooked beak, white-hot eye
    s.g("neck", 108, 70)
    s.part(s.capsule(108, 70, 124, 52, 9, 7), CLOUD, bias=0.2)
    s.g("head", 124, 52, "neck")
    s.part(s.ellipse(130, 46, 10, 8.5), CLOUD, bias=0.3)
    s.part(s.poly([(124, 40), (112, 30), (118, 44)]), CLOUD_D)                                       # crest feathers
    s.part(s.poly([(128, 38), (120, 26), (124, 42)]), CLOUD_D)
    s.part(s.poly([(136, 41), (148, 42), (155, 49), (146, 50), (138, 50)]), BEAK)                    # hooked upper beak
    s.px(154, 50, BEAK[1])
    s.px(153, 51, BEAK[1])
    s.fill(s.poly([(128, 41), (136, 42), (135, 47), (128, 46)]), BOLT[2], glow=True)
    s.fill(s.rect(129, 40, 136, 41), CLOUD_D[0])
    s.px(132, 44, BOLT[0], glow=True)
    s.g("jaw", 137, 50, "head")
    s.part(s.poly([(137, 50), (148, 51), (141, 55)]), BEAK, bias=-0.3)
    # the rider: old warchief, grey braids, crown of lightning, spear
    s.g("rider", 86, 62)
    s.part(s.capsule(82, 62, 76, 70, 3.0), SATCHEL, bias=-0.2)                                        # leg astride
    s.part(s.poly([(78, 40), (92, 40), (94, 62), (78, 63)]), ramp("5a6688"))
    s.part(s.rect(78, 56, 94, 59), SATCHEL, flat=True)
    s.g("hand_w", 90, 46, "rider")
    s.line(86, 70, 112, 14, SATCHEL[1])                                                              # spear
    s.line(87, 70, 113, 14, SATCHEL[3])
    s.fill(s.poly([(111, 16), (115, 16), (117, 4), (112, 10)]), BOLT[2], glow=True)
    s.part(s.capsule(90, 46, 98, 50, 2.6), ramp("5a6688"))
    s.part(s.ellipse(99.5, 50, 2.4, 2.4), PALE)
    s.g("rhead", 86, 40, "rider")
    s.part(s.poly([(78, 30), (84, 26), (86, 44), (80, 46)]), VEIL)                                   # braids
    s.part(s.ellipse(87, 32, 5.6, 6.0), PALE)
    s.part(s.poly([(88, 36), (94, 36), (92, 44), (88, 42)]), VEIL)                                   # beard
    _herald_face(s, 88, 30)
    for pts in ([(80, 27), (79, 20), (82, 23), (83, 15)], [(85, 25), (86, 17), (88, 21), (90, 12)], [(90, 26), (93, 19), (94, 23), (97, 16)]):
        for a, b in zip(pts, pts[1:]):
            s.line(*a, *b, BOLT[2], glow=True)
    # near wing, sweeping down and forward
    s.g("wing", 84, 66)
    wing = [(84, 66), (70, 40), (44, 20), (22, 18), (32, 30), (14, 34), (28, 44), (12, 52), (30, 58), (22, 68), (46, 70), (66, 78)]
    s.part(s.poly(wing), CLOUD, flat=True)
    for x, y in ((22, 18), (14, 34), (12, 52), (22, 68)):
        s.line(70, 44, x, y, CLOUD[0])
    s.part(s.capsule(84, 66, 70, 40, 4.5, 3.4), CLOUD, edge=False)
    s.part(s.capsule(70, 40, 44, 20, 3.4, 2.0), CLOUD, edge=False)
    s.line(70, 40, 46, 22, CLOUD[4])
    s.ink()
    _dust(s, 30, 3)
    s.shadow(84, 124, 40, 4)
    return s


def _flower(s, x, y):
    """A white flower gone grey."""
    s.pxs([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], (214, 214, 222))
    s.pxs([(x - 1, y - 1), (x + 1, y + 1)], (160, 160, 172))
    s.px(x, y, (120, 124, 136), glow=True)


def mother_briar(pose=None, pad=0):
    """Mother Briar, the Thorn Herald: a thicket of black thorns shaped like a hunched old healer."""
    s = Sprite(112, 110, pose, pad)
    rng = np.random.default_rng(12)

    def thorns(cx, cy, rx, ry, n, tone=THORN):
        """Thorn spikes standing out all round a mass."""
        for i in range(n):
            a = 2 * np.pi * i / n + rng.uniform(-0.2, 0.2)
            ln = rng.uniform(4, 9)
            bx, by = cx + np.cos(a) * rx * 0.9, cy + np.sin(a) * ry * 0.9
            s.part(s.poly([(bx - np.sin(a) * 1.6, by + np.cos(a) * 1.6), (bx + np.sin(a) * 1.6, by - np.cos(a) * 1.6),
                           (bx + np.cos(a) * ln, by + np.sin(a) * ln)]), tone, flat=True, edge=False)

    # root legs under the skirt of briars
    for grp, sub, x, tone in (("leg_f", "shin_f", 44, THORN_D), ("leg_n", "shin_n", 60, THORN)):
        s.g(grp, x, 82)
        s.part(s.capsule(x, 82, x + 1, 92, 4.2), tone)
        s.g(sub, x + 1, 92, grp)
        s.part(s.capsule(x + 1, 92, x + 2, 100, 3.6), tone, edge=False)
        s.part(s.poly([(x - 3, 100), (x + 8, 99), (x + 13, 104), (x - 4, 104)]), tone)
    # the hunched back, a great knot of briar
    s.g("body")
    thorns(40, 52, 26, 24, 22, THORN_D)
    s.part(s.ellipse(40, 54, 25, 23), THORN_D)
    thorns(54, 68, 22, 18, 14)
    s.part(s.ellipse(54, 68, 22, 18), THORN)
    for pts in ([(20, 60), (30, 46), (44, 38), (58, 40)], [(24, 70), (38, 58), (52, 54), (66, 60)], [(34, 80), (48, 72), (62, 74), (72, 70)],
                [(30, 40), (40, 50), (38, 62), (46, 74)], [(52, 46), (56, 58), (50, 70), (56, 82)]):
        for a, b in zip(pts, pts[1:]):                                                             # woven canes
            s.line(*a, *b, THORN[4])
            s.line(a[0], a[1] + 1, b[0], b[1] + 1, THORN_D[0])
    for x, y in ((28, 44), (44, 34), (20, 62), (50, 52), (36, 70), (62, 64), (30, 56), (56, 42)):
        _flower(s, x, y)
    # healer's satchel on a strap
    s.line(48, 40, 70, 78, SATCHEL[1])
    s.line(49, 40, 71, 78, SATCHEL[3])
    s.part(s.poly([(62, 72), (78, 72), (80, 88), (64, 90)]), SATCHEL)
    s.part(s.poly([(62, 72), (78, 72), (77, 78), (63, 79)]), SATCHEL, flat=True, bias=0.2)
    s.fill(s.rect(69, 81, 73, 82), (200, 200, 208))
    s.fill(s.rect(70, 80, 72, 85), (200, 200, 208))                                                # a faded healer's cross
    # far arm
    s.g("arm_f", 66, 54)
    s.part(s.capsule(66, 54, 78, 62, 3.0), THORN_D)
    # head thrust forward and low, a hood of thorns, the empty face
    s.g("head", 66, 46)
    thorns(76, 40, 11, 10, 10, THORN_D)
    s.part(s.ellipse(76, 41, 11, 10), THORN)
    s.fill(s.ellipse(80, 43, 6.5, 6.5), (20, 16, 24))
    _herald_face(s, 79, 39)
    _flower(s, 70, 33)
    _flower(s, 80, 31)
    # near arm reaching forward on a gnarled staff
    s.g("weapon", 60, 52)
    s.part(s.capsule(60, 52, 72, 62, 3.6), THORN)
    s.g("hand_w", 72, 62, "weapon")
    for (x0, y0), (x1, y1) in (((96, 20), (93, 44)), ((93, 44), (95, 70)), ((95, 70), (92, 104))):
        s.part(s.capsule(x0, y0, x1, y1, 1.8), THORN_D, edge=False)
    s.part(s.poly([(96, 20), (90, 12), (98, 8), (104, 14), (100, 18)]), THORN_D)                    # the crook of the staff
    _flower(s, 97, 13)
    s.part(s.capsule(72, 62, 92, 58, 3.2, 2.4), THORN, edge=False)
    s.pxs([(93, 55), (95, 57), (93, 60), (96, 60)], THORN[4])
    s.ink()
    _dust(s, 26, 11)
    s.shadow(56, 105, 30, 3.4)
    return s


BOSSES = {"gorrath": gorrath, "cinder_tyrant": cinder_tyrant, "vael_orrun": vael_orrun, "ourra": ourra, "vesper": vesper,
          "ashwick": ashwick, "vholt": vholt, "mother_briar": mother_briar}
CREATURES.update(BOSSES)
