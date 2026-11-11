"""The five test creatures, drawn directly as pixel art with kit.py. All face right; feet sit on the bottom rows."""
from __future__ import annotations

import math

from kit import INK, Sprite, hexc, ramp

SKIN = ramp("e2b08a", shift=0.02)
STEEL = ramp("8e98aa", spread=0.6)
BLUE = ramp("3558a8")
LEATHER = ramp("6b4526")
GOLD = ramp("e0aa36")
RED = ramp("b4282a", spread=0.55)
RED_D = ramp("8a1f26", spread=0.45)
WOOD = ramp("7a5230")
BONE = ramp("e6dcc0", spread=0.55)
DARK = (30, 22, 30)
WHITE = (250, 246, 236)


def soldier():
    """Footman: heavy red plate with steel trim, closed helm with a plume, heater shield forward, broadsword raised."""
    s = Sprite(50, 56)
    # far leg (steel greave, sabaton)
    s.part(s.capsule(21, 39, 20.5, 47, 2.4), STEEL, bias=-0.3)
    s.part(s.ellipse(20.5, 49.5, 3.6, 2.2), STEEL, bias=-0.3)
    # sword arm on the far side, raised: blade, crossguard, gauntlet
    s.part(s.poly([(36, 24), (39, 24), (43, 5), (41, 3), (39, 5)]), STEEL, flat=True, bias=0.2)
    s.line(41, 5, 38, 23, STEEL[4])
    s.line(40, 6, 37, 23, STEEL[1])
    s.part(s.capsule(29, 23, 36, 26, 2.6), RED_D)
    s.part(s.rect(33, 23, 43, 25), GOLD, flat=True)
    s.part(s.ellipse(37.5, 26.5, 2.6, 2.4), STEEL)
    s.part(s.ellipse(30.5, 21.5, 4.2, 3.4), RED_D)             # far pauldron
    # torso: red breastplate with a steel collar and a centre ridge
    s.part(s.ellipse(24, 29, 7.4, 7.4), RED)
    s.line(27, 23, 28, 34, RED[4])
    s.part(s.rect(19, 21, 30, 23), STEEL, flat=True)
    # helm: steel, flat-topped, eye slit and breath holes, red plume swept back
    s.part(s.poly([(22, 6), (17, 2), (11, 4), (9, 10), (12, 16), (15, 11), (19, 10)]), RED)
    s.part(s.ellipse(24.5, 14, 6.8, 7.0) | s.rect(18, 8, 31, 12), STEEL)
    s.part(s.rect(18, 7, 31, 9), STEEL, flat=True, bias=0.3)
    s.fill(s.rect(24, 13, 32, 15), DARK)                        # eye slit
    s.px(28, 13, (255, 240, 200))
    s.px(30, 13, (255, 240, 200))
    s.line(28, 9, 28, 20, STEEL[1])                             # nose ridge
    s.pxs([(26, 17), (26, 19), (30, 17), (30, 19)], DARK)      # breath holes
    s.line(19, 20, 30, 20, STEEL[0])
    # tassets (plate skirt) and belt
    s.part(s.poly([(16, 35), (32, 35), (33, 42), (15, 42)]), RED)
    s.line(15, 42, 33, 42, STEEL[3])
    s.line(24, 36, 24, 41, RED[0])
    s.part(s.rect(16, 34, 32, 36), LEATHER, flat=True)
    s.pxs([(24, 34), (25, 34), (24, 35), (25, 35)], GOLD[3])
    # near leg: greave with a red knee cop, sabaton
    s.part(s.capsule(27, 42, 28, 47.5, 2.8), STEEL)
    s.part(s.ellipse(27.5, 43, 2.6, 2.0), RED)
    s.part(s.ellipse(29.5, 50, 4.2, 2.4) | s.rect(26, 46, 31, 50), STEEL)
    # shield arm and heater shield held forward, covering the body
    s.part(s.capsule(18.5, 25, 22, 31, 2.6), RED)
    shield = s.poly([(24, 24), (37, 24), (37, 35), (30.5, 44), (24, 35)])
    s.part(shield, STEEL, flat=True)
    inner = s.poly([(25.5, 25.5), (35.5, 25.5), (35.5, 34.5), (30.5, 41.5), (25.5, 34.5)])
    s.part(inner, RED, bulge=0.6)
    s.line(30, 27, 30, 39, GOLD[3])                             # gold cross on the shield
    s.line(31, 27, 31, 38, GOLD[2])
    s.line(27, 30, 34, 30, GOLD[3])
    s.line(27, 31, 34, 31, GOLD[2])
    # near pauldron, big and layered, with a steel rim
    s.part(s.ellipse(18.5, 23.5, 5.6, 4.6), RED)
    s.line(14, 26, 22, 27, STEEL[3])
    s.line(15, 24, 21, 21, RED[4])
    s.ink()
    s.shadow(25, 52, 12, 2.6)
    return s


GREEN = ramp("5d8a3a")
GREEN_D = ramp("47702e")
IRON = ramp("6e7078", spread=0.5)
PURPLE = ramp("5a3a66")
RUST = ramp("8a7468", spread=0.45)
ROCK = ramp("8a8072", spread=0.5)
ROCK_D = ramp("665e56", spread=0.45)
MOSS = ramp("5c8a34")
PINE = ramp("2f6034")
EMBER = [(200, 70, 20), (255, 130, 30), (255, 190, 60), (255, 236, 150)]
DRAGON = ramp("b0302a", spread=0.55)
DRAGON_D = ramp("7a2026", spread=0.45)
WING = ramp("8a2630", spread=0.4)
BELLY = ramp("e0b25a")
EYE_RED = (255, 70, 40)
CYAN = (110, 235, 255)


def orc():
    s = Sprite(58, 56)
    # axe haft and head behind the body, raised over the shoulder
    s.part(s.capsule(37, 38, 44, 9, 1.1), WOOD, flat=True)
    s.part(s.poly([(40, 8), (49, 4), (53, 13), (45, 16)]), IRON)
    s.line(50, 5, 53, 12, IRON[4])
    s.line(51, 5, 53, 11, WHITE)
    # far arm and leg
    s.part(s.capsule(20, 25, 16, 36, 3.0), GREEN_D, bias=-0.15)
    s.part(s.ellipse(15.5, 38, 3.2, 3.0), GREEN_D, bias=-0.1)
    s.part(s.capsule(22, 39, 21, 47, 3.0), GREEN_D, bias=-0.2)
    s.part(s.ellipse(20.5, 49.5, 4.0, 2.4), GREEN_D, bias=-0.15)
    # near leg, loincloth, torso
    s.part(s.capsule(29.5, 39, 30.5, 47, 3.5), GREEN)
    s.part(s.ellipse(31.5, 49.6, 4.8, 2.6), GREEN)
    s.part(s.ellipse(26, 28.5, 9.6, 9.0), GREEN)
    s.part(s.poly([(18, 35), (35, 35), (34, 43), (27, 41), (20, 43)]), LEATHER)
    s.part(s.rect(17, 34, 36, 36), IRON, flat=True)
    s.part(s.ellipse(28, 35, 2.0, 2.0), BONE)                      # skull buckle
    s.pxs([(27, 35), (29, 35)], DARK)
    s.line(19, 22, 33, 33, LEATHER[1])                             # chest strap
    s.line(19, 23, 33, 34, LEATHER[2])
    # head, thrust forward: brow, jaw, tusks, ear, mohawk
    s.part(s.poly([(25, 13), (21, 7), (28, 14)]), GREEN_D)         # ear
    s.part(s.ellipse(32, 16.5, 6.6, 6.0), GREEN)
    s.part(s.ellipse(34.5, 21, 5.2, 3.3), GREEN_D)                 # jaw
    s.part(s.poly([(27, 9), (33, 7), (35, 11), (28, 12)]), [(40, 26, 30), (60, 38, 40), (84, 52, 50)], flat=True)
    s.part(s.rect(33, 13, 39, 15), GREEN_D, flat=True, bias=-0.4)  # heavy brow
    s.pxs([(35, 15), (36, 15)], EYE_RED, glow=True)
    s.px(37, 15, (255, 190, 120), glow=True)
    s.pxs([(38, 17), (38, 18)], GREEN_D[0])                        # nostril
    s.pxs([(36, 20), (36, 19), (36, 18)], WHITE)                   # tusks
    s.pxs([(33, 20), (33, 19)], BONE[3])
    s.line(34, 22, 38, 22, GREEN_D[0])                             # mouth
    # near arm: spiked pauldron, big forearm and fist gripping the haft
    s.part(s.capsule(25.5, 24, 34, 33, 3.9), GREEN)
    s.part(s.ellipse(24.5, 21, 5.4, 4.6), IRON)
    for x in (21, 24.5, 28):
        s.part(s.poly([(x - 1.5, 18), (x + 1.5, 18), (x, 13)]), BONE)
    s.part(s.ellipse(36, 35, 3.8, 3.6), GREEN)
    s.pxs([(35, 37), (37, 37)], GREEN_D[0])                        # knuckles
    s.ink()
    s.shadow(26, 51.5, 13, 2.8)
    return s


def skeleton():
    s = Sprite(48, 52)
    cloak = s.poly([(17, 19), (23, 18), (22, 40), (19, 37), (17, 42), (14, 36), (15, 26)])
    s.part(cloak, PURPLE)
    # rusty sword behind the near hand
    s.part(s.poly([(36, 26), (38, 27), (44, 10), (42, 9)]), RUST, flat=True, bias=0.15)
    s.line(43, 10, 37, 26, RUST[4])
    s.pxs([(40, 18), (41, 14)], RUST[0])                           # notches
    # legs: thin bones with knobs at the joints
    def bone(pts, r=1.15, bias=0.0):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            s.part(s.capsule(x0, y0, x1, y1, r), BONE, bias=bias)
        for x, y in pts:
            s.part(s.ellipse(x, y, r + 0.9, r + 0.9), BONE, bias=bias)
    bone([(22, 33), (20.5, 39), (21, 45)], bias=-0.3)
    s.part(s.ellipse(22.5, 46.5, 3.0, 1.5), BONE, bias=-0.3)
    bone([(26.5, 33), (28.5, 39), (27.5, 45)])
    s.part(s.ellipse(29.5, 46.5, 3.4, 1.6), BONE)
    s.part(s.ellipse(24.5, 32.5, 4.6, 2.5), BONE)                  # pelvis
    s.pxs([(24, 33), (25, 33)], DARK)
    # ribcage: a dark hollow with ribs across it, spine behind
    s.part(s.capsule(24, 31, 24, 21, 1.2), BONE, bias=-0.2)
    s.fill(s.ellipse(25, 25.5, 5.0, 4.6), (44, 32, 46))
    for i, y in enumerate((22, 24, 26, 28)):
        w = (4, 5, 5, 4)[i]
        s.line(25 - w, y, 25 + w, y, BONE[3])
        s.px(25 + w, y, BONE[4])
        s.px(25 - w, y, BONE[1])
    s.line(26, 21, 26, 29, BONE[2])                                # breastbone
    # arms
    bone([(20, 21.5), (17.5, 27), (20, 32)], bias=-0.3)
    bone([(30, 21.5), (33, 26.5), (37, 27)])
    s.part(s.capsule(34.5, 25, 39.5, 28.5, 0.9), RUST, flat=True)  # crossguard
    # skull
    s.part(s.rect(24, 17, 31, 21), BONE)                           # jaw
    s.part(s.ellipse(25.5, 13.5, 6.2, 5.8), BONE)
    s.fill(s.rect(26, 12, 28, 15), DARK)
    s.fill(s.rect(30, 12, 32, 15), DARK)
    s.px(27, 13, CYAN, glow=True)
    s.px(31, 13, CYAN, glow=True)
    s.pxs([(29, 16), (29, 17)], DARK)                              # nose
    s.line(25, 19, 31, 19, BONE[0])
    s.pxs([(26, 18), (28, 18), (30, 18), (27, 20), (29, 20)], BONE[0])  # teeth gaps
    s.pxs([(22, 9), (23, 10)], BONE[0])                            # crack in the skull
    s.ink()
    s.shadow(25, 47.5, 9, 2.2)
    return s


def _cracks(s, mask, n, seed, col):
    import numpy as np
    rng = np.random.default_rng(seed)
    ys, xs = np.where(mask)
    for _ in range(n):
        i = rng.integers(len(xs))
        x, y = int(xs[i]), int(ys[i])
        for _ in range(int(rng.integers(3, 7))):
            if 0 <= y < s.h and 0 <= x < s.w and mask[y, x]:
                s.rgb[y, x] = col
            x += int(rng.integers(-1, 2))
            y += 1


STONE = ramp("8d8676", spread=0.5, shift=0.02)
STONE_D = ramp("6a645c", spread=0.45, shift=0.02)
RUNE = [(40, 150, 200), (90, 220, 255), (200, 250, 255)]


def _slab(s, pts, tones=STONE, depth=(3, -3), chips=0, seed=0):
    """A chiselled stone block: a flat front face, a lit top and a dark right side, with hard edges."""
    import numpy as np
    dx, dy = depth
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    n = len(pts)
    for i in range(n):
        (x0, y0), (x1, y1) = pts[i], pts[(i + 1) % n]
        mx, my = (x0 + x1) / 2 - cx, (y0 + y1) / 2 - cy
        ex, ey = x1 - x0, y1 - y0
        nx, ny = ey, -ex
        if nx * mx + ny * my < 0:
            nx, ny = -nx, -ny
        L = math.hypot(nx, ny) or 1
        nx, ny = nx / L, ny / L
        quad = s.poly([(x0, y0), (x1, y1), (x1 + dx, y1 + dy), (x0 + dx, y0 + dy)])
        if ny < -0.35:
            s.fill(quad, tones[4])                               # top face catches the light
        elif nx > 0.35:
            s.fill(quad, tones[1])                               # right side in shadow
    front = s.poly(pts)
    s.fill(front, tones[2])
    # bevel: a light line inside the top and left edges, a dark one inside the bottom and right
    up = front & ~np.roll(front, 1, 0)
    left = front & ~np.roll(front, 1, 1)
    down = front & ~np.roll(front, -1, 0)
    right = front & ~np.roll(front, -1, 1)
    s.rgb[up | left] = tones[3]
    s.rgb[down | right] = tones[1]
    rng = np.random.default_rng(seed)
    ys, xs = np.where(front)
    for _ in range(chips):                                       # chisel marks and cracks
        i = rng.integers(len(xs))
        x, y = int(xs[i]), int(ys[i])
        for _ in range(int(rng.integers(2, 6))):
            if 0 <= y < s.h and 0 <= x < s.w and front[y, x]:
                s.rgb[y, x] = tones[0]
                if x > 0 and front[y, x - 1]:
                    s.rgb[y, x - 1] = tones[3]
            x += int(rng.integers(0, 2))
            y += 1
    return front


def golem():
    """Stone golem: hard-edged quarried blocks, a slit of rune light for eyes, glowing runes cut into the chest."""
    s = Sprite(72, 72)
    # far arm
    _slab(s, [(47, 22), (57, 22), (58, 32), (48, 32)], STONE_D, chips=1, seed=1)        # far shoulder
    _slab(s, [(50, 33), (57, 33), (58, 46), (51, 46)], STONE_D, seed=2)
    _slab(s, [(49, 47), (59, 47), (60, 57), (50, 57)], STONE_D, chips=1, seed=3)        # far fist
    # legs and feet
    _slab(s, [(25, 47), (33, 47), (33, 60), (26, 60)], STONE_D, chips=1, seed=4)
    _slab(s, [(37, 47), (46, 47), (46, 60), (38, 60)], STONE_D, chips=1, seed=5)
    _slab(s, [(23, 61), (35, 61), (36, 67), (22, 67)], STONE, depth=(3, -2), seed=6)
    _slab(s, [(36, 61), (49, 61), (50, 67), (35, 67)], STONE, depth=(3, -2), seed=7)
    # hips and the great chest block, wider at the shoulders
    _slab(s, [(26, 40), (46, 40), (45, 47), (27, 47)], STONE_D, seed=8)
    chest = _slab(s, [(21, 19), (49, 19), (46, 40), (25, 40)], STONE, chips=5, seed=9)
    # runes cut into the chest, glowing
    for (x0, y0, x1, y1) in ((33, 23, 33, 35), (33, 23, 38, 27), (38, 27, 33, 30), (29, 26, 29, 33), (29, 33, 26, 36),
                             (41, 30, 41, 36), (41, 33, 44, 31)):
        s.line(x0, y0, x1, y1, RUNE[1], glow=True)
    s.pxs([(33, 26), (33, 31), (29, 29), (41, 33)], RUNE[2], glow=True)
    # head: a squat block set forward, one glowing eye slit under a heavy brow
    _slab(s, [(33, 8), (46, 8), (46, 19), (34, 19)], STONE_D, chips=1, seed=10)
    _slab(s, [(32, 6), (47, 6), (47, 10), (32, 10)], STONE, depth=(3, -2), seed=11)     # brow slab
    s.fill(s.rect(37, 12, 46, 14), (20, 30, 40))
    s.fill(s.rect(38, 12, 41, 14), RUNE[1], glow=True)
    s.fill(s.rect(43, 12, 46, 14), RUNE[1], glow=True)
    s.px(39, 12, RUNE[2], glow=True)
    s.px(44, 12, RUNE[2], glow=True)
    s.line(37, 17, 44, 17, STONE_D[0])                                                   # mouth crack
    # near arm: huge shoulder block, upper arm, forearm slab, fist on the ground side
    _slab(s, [(13, 31), (22, 31), (22, 43), (14, 43)], STONE_D, seed=12)
    _slab(s, [(8, 16), (24, 16), (25, 31), (9, 31)], STONE, depth=(4, -4), chips=3, seed=13)
    _slab(s, [(10, 42), (25, 42), (26, 56), (11, 56)], STONE, chips=3, seed=14)
    _slab(s, [(9, 56), (27, 56), (27, 65), (10, 65)], STONE_D, chips=1, seed=15)
    for x in (14, 19, 23):
        s.line(x, 60, x, 64, STONE_D[0])                                                 # finger gaps
    s.line(12, 48, 24, 48, RUNE[0], glow=True)                                           # rune band on the forearm
    s.pxs([(14, 48), (18, 48), (22, 48)], RUNE[2], glow=True)
    # crystals grown out of the near shoulder, and a little moss in the joints
    for (x, top, w) in ((12, 5, 3), (17, 2, 4), (22, 7, 3)):
        s.fill(s.poly([(x - w, 13), (x, top), (x + w, 13)]), RUNE[0], glow=True)
        s.fill(s.poly([(x - w + 1, 13), (x, top + 1), (x, 13)]), RUNE[1], glow=True)
        s.line(x, top + 1, x - w + 1, 12, RUNE[2], glow=True)
    s.pxs([(26, 40), (27, 41), (45, 40), (24, 31), (25, 32), (13, 43), (33, 60), (38, 61)], MOSS[2])
    s.pxs([(27, 40), (46, 41), (25, 31), (14, 44)], MOSS[1])
    s.ink()
    s.shadow(37, 68.5, 20, 3.0)
    return s


def dragon():
    s = Sprite(110, 88)
    # far wing, behind everything
    s.part(s.poly([(50, 46), (52, 14), (66, 3), (62, 14), (66, 26), (60, 38)]), WING, flat=True, bias=-0.3)
    # tail, thin to thick, with a spade tip
    pts = [(6, 66), (12, 70), (20, 70), (28, 66), (36, 61)]
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        s.part(s.capsule(x0, y0, x1, y1, 1.5 + i * 1.6, 3.0 + i * 1.7), DRAGON, edge=False)
    s.part(s.poly([(7, 66), (1, 60), (3, 68), (0, 73)]), BONE)
    # far legs
    s.part(s.capsule(60, 60, 64, 74, 3.0), DRAGON_D, bias=-0.2)
    s.part(s.ellipse(66, 76.5, 4.4, 2.2), DRAGON_D, bias=-0.2)
    s.part(s.capsule(40, 62, 44, 75, 3.2), DRAGON_D, bias=-0.2)
    s.part(s.ellipse(46, 76.8, 4.6, 2.2), DRAGON_D, bias=-0.2)
    # body and neck
    s.part(s.capsule(56, 50, 70, 28, 6.4, 4.6), DRAGON)
    s.part(s.ellipse(46, 56, 17, 11.5), DRAGON)
    # pale belly plates under the body and up the front of the neck
    s.part(s.ellipse(48, 62.5, 12.5, 5.0) & s.ellipse(46, 56, 17, 11.5), BELLY)
    s.part(s.capsule(62, 53, 73, 34, 2.6, 1.6) & ~s.capsule(55, 49, 69, 27, 5.0, 3.4), BELLY, edge=False)
    for x, y in ((40, 62), (45, 63), (50, 63), (55, 62)):
        s.px(x, y, BELLY[0])
        s.px(x, y + 1, BELLY[0])
    # head: skull, snout, jaw, horns
    s.part(s.poly([(72, 19), (64, 9), (68, 21)]), BONE, bias=-0.2)  # far horn
    s.part(s.capsule(78, 26, 91, 28, 4.6, 3.2), DRAGON)
    s.part(s.capsule(77, 31.5, 89, 33, 2.4, 1.6), DRAGON_D)        # lower jaw
    s.part(s.ellipse(76, 24.5, 8.4, 6.8), DRAGON)
    s.part(s.poly([(73, 19), (63, 13), (70, 23)]), BONE)           # near horn
    s.fill(s.rect(80, 22, 83, 24), (255, 220, 60), glow=True)      # eye
    s.px(82, 22, DARK)
    s.px(82, 23, DARK)
    s.line(78, 20, 84, 21, DRAGON_D[0])                            # brow
    s.pxs([(90, 26)], DARK)                                        # nostril
    for x in (83, 85, 87, 89):
        s.px(x, 31, WHITE)                                         # teeth
    # fire
    s.fill(s.poly([(91, 29), (104, 25), (109, 30), (103, 35), (92, 33)]), EMBER[1], glow=True)
    s.fill(s.poly([(92, 30), (102, 28), (105, 30), (101, 33), (93, 32)]), EMBER[2], glow=True)
    s.fill(s.poly([(93, 30), (99, 30), (99, 32), (94, 32)]), EMBER[3], glow=True)
    # spikes along the neck and back
    for x, y in ((66, 27), (62, 34), (58, 41), (30, 53), (23, 61), (15, 66)):
        s.part(s.poly([(x - 2, y + 2), (x + 2, y + 1), (x - 2, y - 4)]), BONE, edge=False)
    # near legs: thigh, shin, clawed feet
    s.part(s.ellipse(36, 61, 7.6, 9.0), DRAGON)
    s.part(s.capsule(34, 66, 38, 76, 3.4, 2.8), DRAGON)
    s.part(s.ellipse(40, 78.2, 5.6, 2.6), DRAGON)
    s.part(s.capsule(55, 60, 58, 76, 3.8, 2.8), DRAGON)
    s.part(s.ellipse(60, 78.2, 5.4, 2.6), DRAGON)
    for x in (42, 44, 46, 62, 64, 66):
        s.px(x, 79, WHITE)
        s.px(x - 1, 80, WHITE)
    # near wing: arm, fingers and membrane, raised
    wing = s.poly([(50, 47), (44, 18), (26, 4), (8, 10), (14, 20), (4, 28), (14, 34), (10, 44), (26, 42), (34, 48)])
    s.part(wing, WING, flat=True)
    for (x0, y0), (x1, y1) in (((44, 18), (8, 10)), ((44, 18), (4, 28)), ((44, 18), (10, 44)), ((44, 18), (26, 4))):
        s.line(x0, y0, x1, y1, WING[0])
    s.part(s.capsule(50, 47, 44, 18, 2.8, 2.0), DRAGON)
    s.part(s.capsule(44, 18, 26, 4, 2.0, 1.2), DRAGON, edge=False)
    s.part(s.poly([(44, 18), (47, 10), (41, 14)]), BONE)           # wing claw
    s.ink()
    s.shadow(48, 81.5, 30, 3.4)
    return s


HAIR = ramp("e6c466", spread=0.5)
CLOAK = ramp("3f7a44")
CLOAK_D = ramp("2c5a38", spread=0.45)
TUNIC = ramp("8a6a3c")
BEARD = ramp("d0682a", spread=0.55)
MAIL = ramp("7c8490", spread=0.5)
GHOST = ramp("a8e0d8", spread=0.6, shift=0.0)
GHOST_D = ramp("5aa0a8", spread=0.5, shift=0.0)


def elf():
    """Elf archer: slim, hooded green cloak, long fair hair, pointed ear, longbow drawn with an arrow on the string."""
    s = Sprite(52, 58)
    # cloak hanging behind
    s.part(s.poly([(20, 20), (27, 20), (25, 46), (19, 49), (13, 47), (11, 44), (15, 30)]), CLOAK_D)
    s.line(16, 31, 14, 46, CLOAK_D[0])
    # far leg and boot
    s.part(s.capsule(22.5, 38, 21, 48, 1.9), TUNIC, bias=-0.3)
    s.part(s.capsule(20.5, 46, 20.5, 51, 2.1), LEATHER, bias=-0.3)
    s.part(s.ellipse(21.5, 52.5, 3.0, 1.6), LEATHER, bias=-0.3)
    # near leg and tall boot
    s.part(s.capsule(26.5, 38, 28.5, 47, 2.2), TUNIC)
    s.part(s.capsule(28.5, 45, 28.5, 51, 2.4), LEATHER)
    s.part(s.ellipse(29.5, 52.5, 3.6, 1.8), LEATHER)
    s.line(26, 45, 31, 45, LEATHER[4])
    # slim torso: green jerkin, belt, quiver strap
    s.part(s.poly([(20, 21), (29, 21), (30, 35), (31, 41), (20, 41), (21, 35)]), CLOAK)
    s.part(s.rect(20, 34, 31, 36), LEATHER, flat=True)
    s.px(26, 34, GOLD[3])
    s.px(26, 35, GOLD[2])
    s.line(21, 22, 29, 33, LEATHER[1])
    # quiver on the back with fletchings
    s.part(s.capsule(18, 30, 15, 17, 2.0), LEATHER)
    s.pxs([(14, 14), (15, 13), (16, 14), (13, 15), (16, 12)], WHITE)
    s.pxs([(14, 15), (15, 15), (16, 15)], RED[3])
    # far arm pulling the string back
    s.part(s.capsule(23, 23, 18, 25.5, 1.8), CLOAK_D, bias=-0.1)
    s.part(s.ellipse(17.5, 25.5, 1.7, 1.6), SKIN)
    # head: hair falling behind, face, long pointed ear, hood pushed back
    s.part(s.poly([(19, 9), (24, 6), (27, 12), (23, 27), (18, 28), (17, 18)]), HAIR)
    s.line(20, 12, 19, 26, HAIR[1])
    s.part(s.ellipse(26.5, 14, 4.6, 5.0), SKIN)
    s.part(s.poly([(20, 11), (24, 7), (30, 8), (31, 10), (26, 10), (23, 15)]), HAIR)
    s.part(s.poly([(23, 14), (17, 9), (22, 16)]), SKIN)          # ear
    s.pxs([(29, 13), (29, 14)], (60, 130, 80))                  # eye
    s.px(29, 12, HAIR[1])
    s.px(31, 15, SKIN[1])                                       # nose
    s.line(28, 17, 30, 17, SKIN[1])
    s.part(s.poly([(19, 19), (30, 19), (31, 22), (18, 23)]), CLOAK)   # hood collar
    # longbow in the near hand, arrow nocked
    for (x0, y0), (x1, y1) in (((40, 9), (43, 17)), ((43, 17), (43.5, 25)), ((43.5, 25), (43, 33)), ((43, 33), (40, 41))):
        s.part(s.capsule(x0, y0, x1, y1, 1.0), WOOD, edge=False)
    s.pxs([(39, 8), (39, 42)], GOLD[3])
    s.line(39, 9, 18, 25, (220, 214, 200))                      # string, drawn back to the hand
    s.line(18, 25, 39, 41, (220, 214, 200))
    s.line(18, 25, 46, 25, WOOD[3])                             # arrow
    s.pxs([(47, 25), (48, 25), (46, 24), (46, 26)], STEEL[4])
    s.pxs([(19, 24), (20, 24), (19, 26), (20, 26)], WHITE)
    s.part(s.capsule(29, 23.5, 41, 25, 1.9), CLOAK)             # near arm, straight out
    s.part(s.capsule(36, 24.5, 41, 25, 2.0), LEATHER)           # bracer
    s.part(s.ellipse(42.5, 25, 1.8, 2.0), SKIN)
    s.ink()
    s.shadow(25, 54.5, 11, 2.4)
    return s


def dwarf():
    """Dwarf: short and very broad, horned steel helm, huge braided beard, mail, two-handed warhammer."""
    s = Sprite(54, 48)
    # hammer haft behind, head up over the far shoulder
    s.part(s.capsule(34, 33, 41, 9, 1.2), WOOD, flat=True)
    s.part(s.poly([(34, 3), (48, 6), (46, 15), (32, 12)]), IRON)
    s.line(35, 4, 47, 7, IRON[4])
    s.line(34, 11, 45, 14, IRON[0])
    s.part(s.poly([(35, 5), (37, 5.5), (35.5, 11.5), (33.5, 11)]), GOLD, flat=True)
    s.part(s.poly([(45, 7.5), (47, 8), (45.5, 14), (43.5, 13.5)]), GOLD, flat=True)
    # far leg and boot
    s.part(s.capsule(21, 35, 20, 40, 3.0), LEATHER, bias=-0.3)
    s.part(s.ellipse(20, 42.5, 4.4, 2.4), IRON, bias=-0.3)
    # near leg and big iron-shod boot
    s.part(s.capsule(29, 35, 30, 40, 3.4), LEATHER)
    s.part(s.ellipse(31, 42.5, 5.2, 2.6), IRON)
    s.line(27, 41, 35, 41, IRON[4])
    # barrel torso in mail, red tabard edge, wide belt
    s.part(s.ellipse(25, 26.5, 10.5, 9.0), MAIL)
    for y in range(20, 34, 2):                                    # mail rings
        for x in range(16 + (y // 2) % 2, 36, 2):
            if s.a[y, x] and s.part_id[y, x] == s._n:
                s.px(x, y, MAIL[1])
    s.part(s.poly([(15, 31), (36, 31), (35, 38), (16, 38)]), RED_D)
    s.line(16, 38, 35, 38, GOLD[2])
    s.part(s.rect(15, 30, 37, 33), LEATHER, flat=True)
    s.part(s.rect(24, 29, 29, 34), GOLD, flat=True)
    s.px(26, 31, GOLD[0])
    # head: big nose, helm with horns, beard over the chest
    s.part(s.ellipse(28, 14.5, 6.6, 6.0), SKIN)
    s.part(s.ellipse(34.5, 16, 2.6, 2.2), SKIN, bias=0.1)         # nose
    s.part(s.ellipse(28, 9.5, 7.4, 5.4) & s.rect(0, 0, 54, 13), STEEL)   # helm dome
    s.part(s.rect(20, 11, 36, 14), STEEL, flat=True, bias=0.25)   # brow band
    s.pxs([(23, 12), (27, 12), (31, 12), (35, 12)], GOLD[3])
    s.part(s.rect(32, 13, 34, 17), STEEL, flat=True)              # nasal bar
    s.pxs([(30, 15), (31, 15)], DARK)                             # eye under the brow
    s.part(s.poly([(22, 9), (19, 3), (16, 1), (18, 6), (20, 11)]), BONE)       # horns
    s.part(s.poly([(34, 8), (38, 3), (41, 1), (39, 6), (36, 10)]), BONE)
    # near arm: steel pauldron, thick mailed arm, gauntlet on the haft
    s.part(s.capsule(19, 22, 30, 31, 3.6), MAIL)
    s.part(s.ellipse(18, 20, 5.6, 4.6), STEEL)
    s.line(13, 22, 22, 23, GOLD[2])
    s.part(s.ellipse(35, 33.5, 3.6, 3.4), IRON)
    s.pxs([(34, 35), (36, 35)], IRON[0])
    # beard over the chest and arm: full, forked, with gold braid rings, and a moustache
    s.part(s.poly([(22, 16), (36, 17), (38, 23), (36, 30), (33, 36), (30, 31), (27, 37), (24, 30), (22, 23)]), BEARD)
    s.line(27, 23, 27, 34, BEARD[1])
    s.line(32, 23, 33, 33, BEARD[1])
    s.line(30, 22, 30, 30, BEARD[4])
    s.part(s.rect(26, 33, 29, 35), GOLD, flat=True)
    s.part(s.rect(32, 32, 35, 34), GOLD, flat=True)
    s.part(s.poly([(29, 18), (37, 18), (40, 22), (32, 21)]), BEARD, bias=0.2)
    s.ink()
    s.shadow(26, 44.5, 14, 2.6)
    return s


def ghost():
    """Ghost: hooded pale wraith, hollow glowing eyes, clawed hands reaching forward, body trailing into wisps."""
    s = Sprite(48, 58)
    # trailing tail, curling back and breaking into wisps
    tail = s.poly([(16, 26), (32, 26), (31, 38), (26, 46), (19, 50), (12, 49), (16, 45), (13, 42), (17, 38), (14, 34)])
    s.part(tail, GHOST_D)
    for x, y in ((10, 51), (8, 49), (14, 52), (7, 53), (11, 55), (18, 53), (5, 51), (22, 51), (9, 46)):
        s.px(x, y, GHOST_D[2 + (x + y) % 2], glow=True)
    for y in range(36, 51):                                        # ragged, dithered lower edge
        for x in range(10, 32):
            if s.a[y, x] and (x + y) % 2 == 0 and y > 40 + (x % 5):
                s.a[y, x] = False
    # far arm reaching
    s.part(s.capsule(27, 28, 37, 30, 1.8, 1.3), GHOST_D)
    s.pxs([(39, 29), (40, 28), (39, 31), (40, 32), (40, 30)], GHOST[3], glow=True)
    # robe body and hood
    s.part(s.poly([(15, 20), (33, 20), (34, 30), (31, 38), (17, 38), (14, 30)]), GHOST)
    s.line(20, 24, 19, 37, GHOST[1])
    s.line(27, 25, 28, 37, GHOST[1])
    s.part(s.ellipse(25, 14, 9.0, 9.6) | s.poly([(16, 14), (34, 14), (35, 23), (15, 23)]), GHOST)
    s.part(s.poly([(18, 8), (12, 3), (17, 12)]), GHOST)            # hood tip swept back
    # the dark inside of the hood with two burning eyes and a gaping mouth
    s.fill(s.ellipse(28, 15.5, 5.6, 6.4), (22, 40, 52))
    s.pxs([(26, 13), (27, 13), (30, 13), (31, 13), (27, 14), (31, 14)], CYAN, glow=True)
    s.pxs([(27, 13), (31, 13)], WHITE, glow=True)
    s.fill(s.ellipse(29.5, 19, 1.8, 2.2), (8, 16, 24))
    # near arm and claws
    s.part(s.capsule(21, 27, 33, 34, 2.4, 1.6), GHOST)
    for dx, dy in ((2, -2), (3, 0), (2, 2), (4, -1), (4, 1)):
        s.px(33 + dx, 34 + dy, WHITE, glow=True)
    # chain hanging from the wrist
    s.pxs([(31, 37), (31, 39), (30, 41), (30, 43)], IRON[3])
    s.pxs([(31, 38), (30, 40), (30, 42)], IRON[1])
    s.ink((30, 70, 84))
    s.shadow(23, 56, 9, 1.8)
    return s


ELEMENTS = {
    "fire": (ramp("f0701c", spread=0.6, shift=0.05), (255, 240, 170), (255, 190, 60)),
    "storm": (ramp("7a8cf0", spread=0.6, shift=0.0), (240, 248, 255), (190, 220, 255)),
    "water": (ramp("2a8ad0", spread=0.6, shift=0.0), (220, 250, 255), (120, 220, 255)),
    "nature": (ramp("58b03a", spread=0.55), (236, 255, 190), (170, 240, 90)),
    "earth": (ramp("a8783c", spread=0.5), (255, 226, 150), (230, 180, 80)),
    "void": (ramp("7a3ac0", spread=0.6, shift=0.0), (240, 210, 255), (200, 130, 255)),
}


def elemental(kind="fire"):
    """Elemental ball: a floating core with two eyes, wrapped in its element (flame tongues, arcs, waves, leaves...)."""
    tones, hot, mid = ELEMENTS[kind]
    s = Sprite(40, 46)
    cx, cy = 20, 20
    if kind == "fire":
        for pts in ([(10, 20), (8, 8), (14, 13), (17, 2), (22, 11), (27, 4), (27, 13), (33, 9), (30, 21)],):
            s.part(s.poly(pts), tones, flat=True, bias=-0.2, glow=True)
        s.part(s.poly([(13, 18), (13, 11), (17, 14), (19, 7), (23, 13), (27, 10), (27, 18)]), [mid, hot], flat=True, glow=True)
    elif kind == "storm":
        s.part(s.ellipse(12, 16, 6, 5) | s.ellipse(28, 15, 7, 5.5) | s.ellipse(20, 11, 8, 6), ramp("5a6488", spread=0.5), glow=True)
        for pts in ([(6, 24), (10, 28), (8, 30), (12, 36)], [(33, 22), (30, 27), (33, 29), (29, 36)], [(20, 31), (22, 35), (19, 37), (21, 41)]):
            for a, b in zip(pts, pts[1:]):
                s.line(*a, *b, hot, glow=True)
    elif kind == "water":
        s.part(s.poly([(20, 2), (26, 12), (14, 12)]), tones, glow=True)
        for x, y in ((6, 14), (34, 16), (9, 30), (32, 29), (20, 37)):
            s.part(s.ellipse(x, y, 1.8, 2.2), tones, glow=True)
            s.px(x - 1, y - 1, hot, glow=True)
    elif kind == "nature":
        for ang in range(0, 360, 45):
            a = math.radians(ang + 10)
            x, y = cx + math.cos(a) * 12, cy + math.sin(a) * 12
            s.part(s.ellipse(x, y, 4.2, 2.2, a + 0.5), MOSS if ang % 90 else PINE)
        s.pxs([(20, 4), (21, 3), (22, 4), (21, 5)], (255, 150, 190))
    elif kind == "earth":
        for i, ang in enumerate(range(0, 360, 60)):
            a = math.radians(ang + 20)
            x, y = cx + math.cos(a) * 14, cy + math.sin(a) * 12
            _slab(s, [(x - 3, y - 2.5), (x + 2.5, y - 3), (x + 3, y + 2.5), (x - 2, y + 3)], ROCK if i % 2 else ROCK_D,
                  depth=(1.5, -1.5))
    elif kind == "void":
        for i, ang in enumerate(range(0, 360, 30)):
            a = math.radians(ang)
            r = 14 + (i % 3) * 1.5
            s.px(round(cx + math.cos(a) * r), round(cy + math.sin(a) * r * 0.9), mid if i % 2 else hot, glow=True)
        s.part(s.ellipse(cx, cy, 13.5, 4.0, -0.35) & ~s.ellipse(cx, cy, 11.5, 2.6, -0.35), tones, flat=True, glow=True)
    # the core
    s.part(s.ellipse(cx, cy + 1, 9.5, 9.5), tones, bulge=1.2, glow=True)
    s.part(s.ellipse(cx - 3, cy - 3, 3.4, 2.6, -0.6), [mid, hot], flat=True, edge=False, glow=True)   # shine
    if kind == "void":
        s.fill(s.ellipse(cx + 1, cy + 2, 5.5, 5.5), (16, 8, 30))
        s.part(s.ellipse(cx, cy, 13.5, 4.0, -0.35) & ~s.ellipse(cx, cy, 11.5, 2.6, -0.35) & s.rect(0, cy + 1, 40, 46),
               tones, flat=True, glow=True)
    if kind == "earth":
        s.line(14, 22, 18, 26, tones[0])
        s.line(18, 26, 17, 29, tones[0])
        s.line(26, 14, 24, 17, tones[0])
    # eyes, looking right
    eye = hot if kind != "void" else (255, 255, 255)
    for ex in (21, 26):
        s.pxs([(ex, cy + 1), (ex, cy + 2), (ex + 1, cy + 1), (ex + 1, cy + 2)], DARK if kind != "void" else eye, glow=True)
        s.px(ex + 1, cy + 1, eye, glow=True)
    s.ink(tones[0])
    s.shadow(20, 43, 8, 2.0)
    return s


CREATURES = {"soldier": soldier, "orc": orc, "skeleton": skeleton, "golem": golem, "dragon": dragon,
             "elf": elf, "dwarf": dwarf, "ghost": ghost}
for _k in ELEMENTS:
    CREATURES["orb_" + _k] = (lambda k=_k: elemental(k))
