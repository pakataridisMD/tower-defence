"""The five test creatures, drawn directly as pixel art with kit.py. All face right; feet sit on the bottom rows."""
from __future__ import annotations

import math

from kit import INK, Sprite, hexc, ramp

SKIN = ramp("e2b08a", shift=0.02)
STEEL = ramp("8e98aa", spread=0.6)
BLUE = ramp("3558a8")
LEATHER = ramp("6b4526")
GOLD = ramp("e0aa36")
RED = ramp("b8302a")
WOOD = ramp("7a5230")
BONE = ramp("e6dcc0", spread=0.55)
DARK = (30, 22, 30)
WHITE = (250, 246, 236)


def soldier():
    s = Sprite(48, 52)
    # far side first: shield arm, far leg
    s.part(s.capsule(21, 35, 20, 43, 2.3), BLUE, bias=-0.25)
    s.part(s.ellipse(20.5, 45, 3.4, 2.2), LEATHER, bias=-0.2)
    # round shield on the far arm, seen behind the body
    s.part(s.ellipse(15.5, 30, 5.2, 7.2), BLUE)
    s.part(s.ellipse(15.5, 30, 5.2, 7.2) & ~s.ellipse(15.5, 30, 4.0, 6.0), STEEL, flat=True)
    s.part(s.ellipse(15, 30, 1.6, 2.0), GOLD)
    # near leg and boot
    s.part(s.capsule(26, 35, 27.5, 43, 2.7), BLUE)
    s.part(s.ellipse(28.5, 45.2, 4.0, 2.4) | s.rect(25, 41, 30, 45), LEATHER)
    # torso: breastplate, tabard skirt, belt
    s.part(s.poly([(18, 33), (31, 33), (32, 39), (17, 39)]), BLUE)
    s.part(s.ellipse(24.5, 28.5, 6.6, 6.8), STEEL)
    s.part(s.rect(18, 32, 31, 34), LEATHER, flat=True)
    s.pxs([(27, 32), (28, 32), (27, 33), (28, 33)], GOLD[3])
    s.pxs([(22, 36), (23, 37), (24, 36), (25, 37)], GOLD[2])  # trim on the tabard
    # head: face, then helmet over the top and back
    s.part(s.ellipse(25.5, 16.5, 5.6, 5.6), SKIN)
    helm = s.ellipse(24.8, 14.2, 6.6, 6.0) & ((s.ys < 15) | (s.xs < 22))
    s.part(helm, STEEL)
    s.part(s.rect(19, 14, 33, 16), STEEL, flat=True, bias=0.25)
    s.part(s.poly([(20, 5), (28, 4), (31, 8), (19, 9)]), RED)
    s.pxs([(28, 17), (28, 18)], DARK)                 # eye
    s.px(29, 17, WHITE)
    s.pxs([(31, 19)], SKIN[1])                        # nose shadow
    s.pxs([(27, 21), (28, 21), (29, 21), (30, 21), (28, 22), (29, 22)], LEATHER[1])  # moustache and chin
    # near arm: pauldron, sleeve, gauntlet, sword raised forward
    blade = s.poly([(35, 27), (37, 28), (44, 10), (42, 9)])
    s.part(blade, STEEL, flat=True, bias=0.3)
    s.line(43, 10, 36, 27, STEEL[4])
    s.part(s.capsule(27.5, 26, 33.5, 29.5, 2.3), BLUE)
    s.part(s.ellipse(27, 24.5, 3.6, 3.2), STEEL)
    s.part(s.ellipse(34.5, 29.5, 2.4, 2.3), STEEL, bias=0.1)
    s.part(s.capsule(32.5, 26.5, 38.5, 29.5, 1.0), GOLD)   # crossguard
    s.ink()
    s.shadow(24, 47.5, 11, 2.6)
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


def golem():
    s = Sprite(66, 66)
    # far arm and shoulder
    s.part(s.capsule(45, 27, 47, 43, 5.2), ROCK_D, bias=-0.15)
    s.part(s.ellipse(47.5, 48, 6.0, 5.4), ROCK_D, bias=-0.1)
    s.part(s.ellipse(43, 21.5, 7.5, 6.5), ROCK_D)
    # legs: short pillars with wide feet
    s.part(s.poly([(24, 44), (31, 44), (32, 57), (23, 57)]), ROCK_D, bias=-0.1)
    s.part(s.poly([(34, 44), (42, 44), (43, 57), (33, 57)]), ROCK_D)
    s.part(s.ellipse(27, 59.5, 6.5, 3.2), ROCK, bias=-0.1)
    s.part(s.ellipse(39, 59.8, 7.0, 3.4), ROCK)
    # body: a great boulder, hips below it
    s.part(s.ellipse(32.5, 43, 10.5, 5.5), ROCK_D)
    body = s.ellipse(32, 30.5, 14.5, 13.0)
    s.part(body, ROCK)
    # the core burning through a crack in the chest
    core = s.poly([(35, 22), (39, 26), (37, 30), (41, 35), (37, 40), (35, 34), (32, 30), (34, 26)])
    s.fill(core, EMBER[1], glow=True)
    s.fill(s.poly([(35, 25), (37, 27), (36, 31), (38, 35), (36, 37), (35, 33), (34, 29)]), EMBER[2], glow=True)
    s.pxs([(36, 28), (36, 32), (37, 35)], EMBER[3], glow=True)
    s.line(41, 35, 44, 38, EMBER[0], glow=True)
    s.line(32, 30, 28, 33, EMBER[0], glow=True)
    s.line(35, 22, 33, 19, EMBER[0], glow=True)
    # head: small, sunk between the shoulders
    s.part(s.ellipse(37, 17, 7.4, 6.4), ROCK_D)
    s.part(s.rect(35, 13, 45, 15), ROCK_D, flat=True, bias=-0.35)  # brow ridge
    s.fill(s.rect(37, 15, 39, 17), EMBER[2], glow=True)
    s.fill(s.rect(41, 15, 43, 17), EMBER[2], glow=True)
    s.line(37, 20, 43, 20, ROCK_D[0])
    s.pxs([(38, 21), (40, 21), (42, 21)], ROCK_D[0])
    # near shoulder, arm and fist, hanging to the knee
    s.part(s.capsule(19, 30, 20, 45, 6.2), ROCK)
    s.part(s.ellipse(20.5, 21.5, 9.2, 8.2), ROCK)
    s.part(s.ellipse(20.5, 51, 7.4, 6.4), ROCK)
    s.line(16, 53, 25, 53, ROCK[0])
    s.pxs([(19, 54), (22, 54), (19, 55), (22, 55)], ROCK[0])       # fingers
    for m, seed in ((body, 1), (s.ellipse(20.5, 21.5, 9.2, 8.2), 2), (s.ellipse(20.5, 51, 7.4, 6.4), 3),
                    (s.capsule(19, 30, 20, 45, 6.2), 4)):
        _cracks(s, m & (s.part_id > 0) & ~s.glow, 3, seed, ROCK[0])
    # moss and a small pine growing on the near shoulder
    s.part(s.ellipse(19.5, 14.5, 8.2, 3.0), MOSS)
    s.pxs([(13, 17), (17, 18), (24, 17), (26, 18)], MOSS[1])
    s.part(s.rect(13, 8, 15, 13), WOOD, flat=True)
    s.part(s.poly([(14, 1), (18, 6), (10, 6)]), PINE)
    s.part(s.poly([(14, 4), (19, 10), (9, 10)]), PINE)
    s.pxs([(22, 12), (25, 13)], (240, 220, 120))                   # small flowers in the moss
    s.ink()
    s.shadow(33, 62.5, 17, 3.0)
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


CREATURES = {"soldier": soldier, "orc": orc, "skeleton": skeleton, "golem": golem, "dragon": dragon}
