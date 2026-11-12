"""Body variants for Vael-Orrun, the High King, for Doctor Paris to choose from (design only).

All share the monster head from bosses._vael_head (black crown, ashen skull, six burning eyes, a jaw open on the
Heartstone fire) and the Heartstone light in the chest. Ids: vael_orrun (the glass robe, in bosses.py) and the five
below. 32 art px = 1 board cell; all are about 9 to 10 cells tall.
"""
from __future__ import annotations

import math

import numpy as np

from bosses import (BOSSES, EYE, GLASS, GLASS_D, GREY_GLOW, MAW, RING, SKULL, TOOTH, _crack, _dust, _vael_head)
from creatures import CREATURES
from kit import Sprite, ramp

BONE = ramp("6e6676", spread=0.62, shift=0.03)        # black-glass bone, a shade lighter than the robe
PLATE = ramp("3a3552", spread=0.62, shift=0.0)
PLATE_D = ramp("26233a", spread=0.5, shift=0.0)
CHAIN = [(70, 66, 80), (110, 106, 122)]
EMBER = [EYE[0], EYE[1], EYE[2]]


def _heart(s, cx, cy, k=1.0):
    """The stolen Heartstone light: a three-step diamond of gold-white glow."""
    for (w, h), col in zip(((12, 21), (8, 15), (4, 8)), ((255, 214, 120), (255, 240, 190), (255, 255, 245))):
        w, h = w * k, h * k
        s.fill(s.poly([(cx, cy - h), (cx + w, cy), (cx, cy + h), (cx - w, cy)]), col, glow=True)


def _six_cracks(s, cx, cy, reach=1.0):
    """Cracks bleeding the six stolen colours out from the heart."""
    for k, col in enumerate(RING):
        a = -math.pi / 2 + k * math.pi / 3 + 0.3
        pts, x, y = [(cx, cy)], cx, cy
        for j in range(4):
            a += (0.35 if j % 2 else -0.35)
            x, y = x + math.cos(a) * 11 * reach, y + math.sin(a) * 13 * reach
            pts.append((x, y))
        _crack(s, pts, col, (255, 255, 255))


def _talons(s, x, y, angles, ln=14, r=1.5, tones=GLASS, claw=TOOTH[3]):
    """A spread hand of long fingers, each ending in a hooked bone talon."""
    for ang in angles:
        tx, ty = x + math.cos(ang) * ln, y + math.sin(ang) * ln
        s.part(s.capsule(x, y, tx, ty, r, 0.8), tones, edge=False)
        s.line(tx, ty, tx + math.cos(ang + 0.6) * 4, ty + math.sin(ang + 0.6) * 4, claw)


def _pauldrons(s, l=62, r=114, y=0, big=1.0):
    """Tall angular shoulder plates of black glass with a back-swept spike, like the robe form's."""
    for sx, sgn in ((l, -1), (r, 1)):
        P = lambda dx, dy: (sx + dx * sgn * big, y + dy)   # noqa: E731
        s.fill(s.poly([P(-14, 66), P(12, 84), P(20, 76), P(22, 50 - 6 * (big - 1))]), GLASS[1 if sgn > 0 else 3])
        s.fill(s.poly([P(12, 84), P(20, 76), P(26, 96)]), GLASS[0 if sgn > 0 else 2])
        s.line(*P(-14, 66), *P(22, 50), GLASS[4 if sgn < 0 else 2])
        s.fill(s.poly([P(14, 60), P(22, 50), P(28, 22 - 14 * (big - 1))]), GLASS[2 if sgn < 0 else 0])
        s.line(*P(14, 60), *P(28, 22 - 14 * (big - 1)), GLASS[4 if sgn < 0 else 1])


def _torn_cape(s, top, bot, xl, xr, flare, seed, tone=GLASS_D):
    """A cape from the shoulders with a ragged, torn hem."""
    rng = np.random.default_rng(seed)
    hem = []
    n = 9
    for i in range(n + 1):
        x = xr + flare - (xr - xl + 2 * flare) * i / n
        hem.append((x, bot - (rng.integers(0, 26) if i % 2 else 0)))
    s.fill(s.poly([(xl, top), (xr, top)] + hem), tone[1])
    for i in range(1, n, 2):
        x, y = hem[i]
        s.line((xl + xr) / 2 + (x - (xl + xr) / 2) * 0.3, top + 30, x, y, tone[0])
    s.line(xl, top, hem[-1][0], hem[-1][1], tone[3])


# ---- B: the Bone Sovereign ---------------------------------------------------------------------------------------------
def vael_orrun_bone(pose=None, pad=0):
    """The Bone Sovereign: a towering skeleton of black glass in the rags of a king's mantle. The Heartstone burns
    inside a cage of ribs; shards of glass armour cling to the shoulders and hips; long legs stride."""
    s = Sprite(176, 336, pose, pad, origin=(0, 32))
    s.g("cloak", 88, 70)
    _torn_cape(s, 70, 268, 54, 122, 26, 4)
    # far arm, hanging: bone with knobbed joints
    s.g("arm_f", 64, 84)
    s.part(s.capsule(64, 84, 52, 142, 4.5), BONE, bias=-0.25)
    s.part(s.ellipse(52, 142, 5, 5), BONE, bias=-0.25)
    s.g("fore_f", 52, 142, "arm_f")
    s.part(s.capsule(52, 142, 48, 196, 3.5, 3), BONE, bias=-0.25, edge=False)
    _talons(s, 48, 198, (1.2, 1.45, 1.7, 1.95), 16, tones=BONE)
    # legs: long bones, knee knobs, clawed glass feet
    for grp, sub, hx, kx, fx, bias in (("leg_f", "shin_f", 80, 74, 72, -0.25), ("leg_n", "shin_n", 98, 106, 108, 0.0)):
        s.g(grp, hx, 196)
        s.part(s.capsule(hx, 196, kx, 242, 5.5, 4.5), BONE, bias=bias)
        s.g(sub, kx, 242, grp)
        s.part(s.ellipse(kx, 242, 6, 6), BONE, bias=bias)
        s.part(s.capsule(kx, 242, fx, 286, 4.5, 3.5), BONE, bias=bias, edge=False)
        s.part(s.poly([(fx - 8, 284), (fx + 4, 282), (fx + 16, 292), (fx + 12, 296), (fx - 8, 296)]), GLASS, bias=bias)
        for d in (0, 6, 12):
            s.line(fx + 4 + d, 294, fx + 8 + d, 297, TOOTH[2])
        s.part(s.poly([(kx - 7, 250), (kx + 7, 248), (kx + 5, 272), (kx - 3, 276)]), GLASS, bias=bias, flat=True)  # greave shard
    s.g("body")
    # pelvis and the shard-plate skirt
    for x0, x1, bot, lean in ((64, 74, 222, -4), (72, 84, 236, -2), (92, 104, 238, 3), (102, 114, 226, 6)):
        s.part(s.poly([(x0, 188), (x1, 188), ((x0 + x1) / 2 + lean, bot)]), GLASS, flat=True, bias=-0.1)   # hanging glass shards
    s.part(s.poly([(64, 176), (78, 182), (88, 192), (98, 182), (112, 176), (110, 192), (96, 204), (80, 204), (66, 192)]), BONE)
    s.line(70, 180, 80, 196, BONE[4])
    # spine, and the cage of ribs with the Heartstone burning inside
    s.fill(s.ellipse(88, 128, 22, 32), GLASS_D[0])
    s.fill(s.ellipse(88, 128, 14, 20), (40, 26, 22))
    s.fill(s.ellipse(88, 128, 10, 14), (120, 70, 30), glow=True)
    for y in range(90, 182, 7):
        s.part(s.ellipse(88, y, 4.5, 3.5), BONE)
    for i in range(6):
        y = 98 + i * 11
        w = 24 - abs(i - 2) * 2.5
        for sgn in (-1, 1):
            arc = s.capsule(88, y, 88 + sgn * w, y + 6, 2.4) | s.capsule(88 + sgn * w, y + 6, 88 + sgn * (w - 6), y + 16, 2.0)
            s.part(arc, BONE, bias=-0.15 if sgn < 0 else 0.05)
    _heart(s, 88, 128, 1.0)
    _six_cracks(s, 88, 128, 0.6)
    # collarbones and the shoulder plates
    s.part(s.capsule(66, 82, 110, 82, 3.5), BONE)
    _pauldrons(s, 60, 116, 4, 1.1)
    _vael_head(s)
    # near arm reaching out, palm open, talons spread
    s.g("weapon", 112, 86)
    s.part(s.capsule(112, 86, 128, 134, 4.5), BONE)
    s.part(s.ellipse(128, 134, 5, 5), BONE)
    s.g("hand_w", 128, 134, "weapon")
    s.part(s.capsule(128, 134, 150, 110, 3.5, 3), BONE, edge=False)
    _talons(s, 151, 108, (-1.3, -0.9, -0.5, -0.1, 0.5), 18, tones=BONE)
    s.part(s.poly([(112, 92), (122, 96), (126, 112), (116, 110)]), GLASS, flat=True)    # a glass vambrace shard
    s.ink()
    _dust(s, 40, 5)
    s.shadow(90, 298, 46, 5)
    return s


# ---- C: the Dread King --------------------------------------------------------------------------------------------------
def vael_orrun_knight(pose=None, pad=0):
    """The Dread King: the High King in full black-glass war plate, a torn mantle behind him and a greatsword of
    black glass with a burning fuller. The Heartstone is set in his breastplate like a stolen jewel."""
    s = Sprite(184, 336, pose, pad, origin=(0, 32))
    s.g("cloak", 88, 70)
    _torn_cape(s, 70, 286, 50, 126, 30, 7)
    # far arm, a gauntlet resting low
    s.g("arm_f", 62, 86)
    s.part(s.capsule(62, 86, 52, 140, 9), PLATE, bias=-0.25)
    s.g("fore_f", 52, 140, "arm_f")
    s.part(s.capsule(52, 140, 50, 186, 8, 7), PLATE, bias=-0.25, edge=False)
    s.part(s.ellipse(50, 192, 8, 8), PLATE, bias=-0.25)
    _talons(s, 50, 196, (1.3, 1.6, 1.9), 9, 1.8, PLATE)
    # armoured legs
    for grp, sub, hx, kx, fx, tone in (("leg_f", "shin_f", 76, 72, 70, PLATE_D), ("leg_n", "shin_n", 100, 106, 108, PLATE)):
        s.g(grp, hx, 200)
        s.part(s.capsule(hx, 200, kx, 244, 11, 10), tone)
        s.g(sub, kx, 244, grp)
        s.part(s.capsule(kx, 244, fx, 284, 10, 8), tone, edge=False)
        s.part(s.poly([(kx - 9, 236), (kx + 9, 236), (kx + 12, 246), (kx, 256), (kx - 12, 246)]), tone, flat=True)  # knee cop
        s.line(kx, 236, kx, 254, tone[4])
        s.part(s.poly([(fx - 12, 282), (fx + 8, 280), (fx + 22, 292), (fx + 20, 297), (fx - 12, 297)]), tone, flat=True)
    s.g("body")
    # tassets: hanging plates of the war skirt
    for x0, x1, bot, t in ((62, 78, 238, -0.15), (76, 92, 244, 0.0), (90, 106, 242, 0.05), (104, 118, 234, 0.1)):
        s.part(s.poly([(x0, 176), (x1, 176), (x1 + 2, bot - 8), ((x0 + x1) / 2 + 1, bot), (x0 - 2, bot - 8)]), PLATE, flat=True, bias=t)
        s.line(x0 - 1, 178, x0 - 2, bot - 8, PLATE[4])
        s.line(x0, 196, x1 + 1, 196, PLATE[0])
        s.line(x0, 197, x1 + 1, 197, PLATE[3])
    # breastplate and the Heartstone set in it
    s.part(s.poly([(62, 78), (114, 78), (118, 120), (108, 176), (68, 176), (58, 120)]), PLATE, bulge=0.9)
    s.line(88, 80, 88, 172, PLATE[0])
    s.line(87, 80, 87, 108, PLATE[4])
    s.line(62, 80, 58, 120, PLATE[4])
    s.line(58, 120, 68, 174, PLATE[3])
    for y0 in (84, 90):                                                                      # a gorget of overlapping lames
        s.line(68, y0, 108, y0, PLATE[0])
        s.line(68, y0 + 1, 108, y0 + 1, PLATE[3])
    for y in (150, 160, 170):
        s.line(70, y, 106, y, PLATE[0])
    s.part(s.poly([(64, 170), (112, 170), (110, 180), (66, 180)]), PLATE_D, flat=True)    # sword belt
    s.part(s.poly([(84, 168), (92, 168), (93, 182), (88, 186), (83, 182)]), PLATE, flat=True)
    s.px(88, 175, EYE[1], glow=True)
    s.fill(s.poly([(88, 100), (102, 120), (88, 142), (74, 120)]), PLATE_D[0])                 # setting
    _heart(s, 88, 121, 0.85)
    _six_cracks(s, 88, 121, 0.7)
    _pauldrons(s, 58, 118, 2, 1.25)
    for sx in (44, 132):                                                                     # rows of spikes on the pauldrons
        for k in range(3):
            x = sx + (k * 6 if sx > 88 else -k * 6) + (0 if sx > 88 else 0)
            s.fill(s.poly([(x - 3, 74 + k * 4), (x + 3, 74 + k * 4), (x, 58 + k * 4)]), GLASS[3 if sx < 88 else 1])
    _vael_head(s)
    # near arm and the greatsword, raised point-up beside the head
    s.g("weapon", 114, 88)
    s.part(s.capsule(114, 88, 126, 134, 9.5), PLATE)
    s.g("hand_w", 126, 134, "weapon")
    s.part(s.capsule(126, 134, 146, 122, 8, 7), PLATE, edge=False)
    blade = s.poly([(144, 116), (154, 116), (160, -4), (156, -18), (150, -6)])
    s.part(blade, GLASS, flat=True)
    s.line(150, 112, 155, -6, EYE[1], glow=True)                                             # the burning fuller
    s.line(151, 112, 156, -4, EYE[0], glow=True)
    s.line(145, 114, 151, -6, GLASS[4])
    s.part(s.poly([(132, 116), (166, 114), (168, 120), (130, 122)]), PLATE, flat=True)      # crossguard
    s.fill(s.poly([(140, 116), (144, 104), (148, 116)]), PLATE[2])
    s.fill(s.poly([(150, 116), (154, 104), (158, 116)]), PLATE[1])
    s.part(s.capsule(148, 122, 150, 140, 3), PLATE_D)                                        # grip
    s.part(s.ellipse(150, 143, 4.5, 4), PLATE)                                               # pommel
    s.part(s.ellipse(148, 128, 8, 7), PLATE)                                                 # the fist on the grip
    s.ink()
    _dust(s, 30, 6)
    s.shadow(92, 298, 50, 5)
    return s


# ---- D: the Six-Armed Sovereign ----------------------------------------------------------------------------------------
def vael_orrun_sixarm(pose=None, pad=0):
    """The Six-Armed Sovereign: the glass robe, but six long arms, each clutching the burning art he tore from one of
    the six monarchs (fire, storm, nature, water, earth, void)."""
    s = Sprite(180, 336, pose, pad, origin=(2, 32))
    s.g("cloak", 88, 70)
    cape = [(52, 70), (124, 70), (150, 200), (156, 288), (124, 296), (52, 296), (20, 288), (26, 200)]
    s.fill(s.poly(cape), GLASS_D[1])
    s.line(52, 70, 26, 200, GLASS_D[3])
    s.line(26, 200, 20, 288, GLASS_D[2])

    def arm(grp, sx, sy, ex, ey, hx, hy, col, bias, parent=None):
        s.g(grp, sx, sy, parent) if grp else None
        s.part(s.capsule(sx, sy, ex, ey, 4.5, 4), GLASS, bias=bias)
        s.part(s.capsule(ex, ey, hx, hy, 3.8, 3), GLASS, bias=bias, edge=False)
        # the stolen art burning in the hand
        s.fill(s.ellipse(hx, hy, 7, 7), tuple(int(c * 0.55) for c in col), glow=True)
        s.fill(s.ellipse(hx, hy, 5, 5), col, glow=True)
        s.fill(s.ellipse(hx - 1, hy - 1, 2, 2), (255, 255, 240), glow=True)
        ang = math.atan2(hy - ey, hx - ex)
        _talons(s, hx, hy, (ang - 1.0, ang - 0.4, ang + 0.4, ang + 1.0), 8, 1.2)

    # far side arms (darker): void, earth, water
    arm(None, 66, 120, 42, 156, 24, 184, RING[5], -0.25)
    arm(None, 64, 100, 34, 112, 14, 96, RING[3], -0.25)
    arm("arm_f", 64, 80, 40, 52, 24, 20, RING[4], -0.25)
    s.g("body")
    facets = [([(64, 72), (78, 72), (72, 292), (44, 292), (54, 180)], 3), ([(78, 72), (90, 72), (92, 292), (72, 292)], 2),
              ([(90, 72), (102, 72), (112, 292), (92, 292)], 1), ([(102, 72), (112, 72), (122, 180), (132, 292), (112, 292)], 0)]
    for pts, t in facets:
        s.fill(s.poly(pts), GLASS[t])
    for (x0, y0, x1, y1), t in (((78, 72, 72, 292), 4), ((90, 72, 92, 292), 3), ((102, 72, 112, 292), 2)):
        s.line(x0, y0, x1, y1, GLASS[t])
    rng = np.random.default_rng(3)
    for _ in range(70):
        x, y = int(rng.integers(40, 136)), int(rng.integers(284, 300))
        s.px(x, y, GREY_GLOW[int(rng.integers(0, 2))] if rng.random() < 0.5 else GLASS[int(rng.integers(0, 3))])
    _heart(s, 88, 118)
    _six_cracks(s, 88, 118, 0.9)
    for y in (84, 104, 124):                                                                 # where the extra arms join
        s.part(s.ellipse(66, y, 6, 5), GLASS, bias=-0.1)
        s.part(s.ellipse(110, y, 6, 5), GLASS)
    _pauldrons(s, 62, 114)
    _vael_head(s)
    # near side arms: fire high, storm out, nature low
    arm(None, 110, 124, 134, 156, 152, 182, RING[2], 0.0)
    arm(None, 112, 104, 142, 112, 162, 96, RING[1], 0.0)
    arm("weapon", 112, 82, 136, 52, 152, 20, RING[0], 0.0)
    s.ink()
    _dust(s, 50, 2)
    s.shadow(88, 298, 50, 5)
    return s


# ---- E: the Abomination -------------------------------------------------------------------------------------------------
def vael_orrun_beast(pose=None, pad=0):
    """The Abomination: the king gone beast. A hunched mountain of black glass on knuckles and claws, a ridge of glass
    spines down the back, the crown and skull thrust forward, and the Heartstone glaring out of a split in the chest
    ringed with rib-teeth."""
    s = Sprite(232, 300, pose, pad, origin=(0, 34))
    # far arm, a pillar to the ground
    s.g("arm_f", 128, 118)
    s.part(s.capsule(128, 118, 150, 186, 13, 11), GLASS, bias=-0.3)
    s.g("fore_f", 150, 186, "arm_f")
    s.part(s.capsule(150, 186, 156, 244, 11, 9), GLASS, bias=-0.3, edge=False)
    s.part(s.poly([(140, 242), (170, 240), (178, 256), (138, 258)]), GLASS, bias=-0.3)
    _talons(s, 170, 250, (0.1, 0.5), 10, 2, GLASS, TOOTH[2])
    # hind legs, folded and heavy
    for grp, sub, hx, kx, fx, bias in (("leg_f", "shin_f", 58, 32, 50, -0.3), ("leg_n", "shin_n", 76, 54, 74, 0.0)):
        s.g(grp, hx, 186)
        s.part(s.capsule(hx, 186, kx, 220, 17, 13), GLASS, bias=bias)
        s.g(sub, kx, 220, grp)
        s.part(s.capsule(kx, 220, fx, 252, 11, 8), GLASS, bias=bias, edge=False)
        s.part(s.poly([(fx - 14, 250), (fx + 10, 248), (fx + 22, 258), (fx - 14, 259)]), GLASS, bias=bias)
        for d in (6, 13, 20):
            s.line(fx + d - 2, 256, fx + d + 2, 260, TOOTH[2])
    s.g("body")
    # the hunched mass and the robe rags hanging from it
    body = s.poly([(18, 196), (24, 140), (48, 96), (86, 70), (124, 74), (150, 98), (162, 130), (156, 176), (128, 206),
                   (70, 214), (30, 212)])
    s.part(body, GLASS, bulge=1.1)
    for x0, top, ln in ((30, 200, 40), (52, 208, 34), (96, 206, 30), (120, 200, 24)):
        s.fill(s.poly([(x0, top), (x0 + 16, top), (x0 + 12, top + ln), (x0 + 6, top + ln - 10), (x0 + 2, top + ln + 4)]), GLASS_D[1])
    s.line(26, 142, 48, 98, GLASS[4])
    s.line(48, 98, 86, 72, GLASS[4])
    # spines of black glass along the back, tallest at the hump
    for k, (x, y) in enumerate(((30, 140), (40, 118), (52, 100), (66, 86), (82, 76), (98, 72), (114, 74))):
        h = (16, 22, 30, 36, 34, 26, 18)[k]
        lean = -0.5
        tip = (x + lean * h * 0.6, y - h)
        s.fill(s.poly([(x - 5, y + 4), (x + 5, y + 4), tip]), GLASS[3 if k < 4 else 2])
        s.line(x - 5, y + 4, *tip, GLASS[4])
        s.line(x + 5, y + 4, *tip, GLASS_D[1])
    # the split chest: rib-teeth round the Heartstone
    s.fill(s.ellipse(104, 156, 16, 26), MAW[0])
    s.fill(s.ellipse(104, 156, 11, 20), MAW[1])
    s.fill(s.ellipse(104, 156, 7, 13), (120, 70, 30), glow=True)
    _heart(s, 104, 156, 0.8)
    for k in range(5):
        y = 138 + k * 9
        for sgn in (-1, 1):
            x = 104 + sgn * (15 - abs(k - 2) * 2)
            s.fill(s.poly([(x, y - 2), (x, y + 2), (x - sgn * 8, y + 1)]), TOOTH[2])
            s.px(x - sgn * 2, y - 1, TOOTH[4])
    _six_cracks(s, 104, 156, 0.8)
    # shoulder plates and the head thrust forward and low
    s.part(s.poly([(116, 82), (156, 92), (166, 116), (140, 120), (118, 104)]), GLASS, flat=True)
    s.fill(s.poly([(150, 94), (166, 82), (172, 60)]), GLASS[2])
    s.part(s.capsule(124, 92, 166, 118, 16, 13), GLASS)                                      # a thick neck thrust forward
    s.line(124, 78, 160, 104, GLASS[4])
    _vael_head(s, dx=82, dy=56)
    # near arm: the great clawed forelimb
    s.g("weapon", 150, 120)
    s.part(s.capsule(150, 120, 182, 182, 14, 12), GLASS)
    s.g("hand_w", 182, 182, "weapon")
    s.part(s.capsule(182, 182, 190, 238, 12, 10), GLASS, edge=False)
    s.part(s.poly([(172, 236), (206, 236), (216, 254), (170, 258)]), GLASS)
    for d in (0, 12, 22):
        s.part(s.poly([(186 + d, 250), (192 + d, 248), (198 + d, 262), (192 + d, 260)]), TOOTH, flat=True)
    s.ink()
    _dust(s, 50, 8)
    s.shadow(116, 262, 92, 6)
    return s


# ---- F: the Ash Wraith -------------------------------------------------------------------------------------------------
def vael_orrun_wraith(pose=None, pad=0):
    """The Ash Wraith: no body left under the robe, only shadow. A vast mantle of torn black banners spreads behind
    him like wings, the robe frays into long ribbons of ash, and from his belt hang the six broken crowns of the
    monarchs who betrayed him."""
    s = Sprite(200, 336, pose, pad, origin=(0, 32))
    rng = np.random.default_rng(11)
    # the mantle of torn banners, spread like wings
    s.g("cloak", 100, 76)
    for sgn, tone in ((-1, GLASS_D), (1, GLASS_D)):
        pts = [(100 + sgn * 10, 70), (100 + sgn * 70, 26), (100 + sgn * 94, 14)]
        for k in range(6):
            pts.append((100 + sgn * (92 - k * 9), 60 + k * 30 + int(rng.integers(0, 18))))
            pts.append((100 + sgn * (86 - k * 9), 52 + k * 30))
        pts.append((100 + sgn * 22, 230))
        s.fill(s.poly(pts), tone[2 if sgn < 0 else 1])
        for k in range(4):
            s.line(100 + sgn * 14, 74, 100 + sgn * (90 - k * 14), 30 + k * 40, tone[0])
        s.line(100 + sgn * 10, 70, 100 + sgn * 94, 14, tone[4 if sgn < 0 else 3])
    # the robe, fraying into ribbons of ash that never touch the ground
    s.g("body")
    robe = s.poly([(76, 76), (124, 76), (134, 160), (140, 230), (60, 230), (66, 160)])
    s.part(robe, GLASS, bulge=0.7)
    s.line(100, 80, 100, 228, GLASS[0])
    s.line(84, 80, 72, 226, GLASS[4])
    for k in range(9):
        x0 = 62 + k * 9
        ln = int(rng.integers(30, 70))
        sway = int(rng.integers(-8, 9))
        rib = s.poly([(x0, 226), (x0 + 8, 226), (x0 + 6 + sway, 226 + ln), (x0 + 3 + sway, 226 + ln + 6)])
        s.fill(rib, GLASS[2 if k < 4 else 1])
        for j in range(12):                                                               # the ends crumble to ash
            y = 226 + ln - 8 + int(rng.integers(0, 22))
            s.px(x0 + 4 + sway + int(rng.integers(-4, 5)), y, GREY_GLOW[int(rng.integers(0, 2))] if rng.random() < 0.6 else GLASS[1])
    # belt and the six broken crowns on chains
    s.fill(s.rect(68, 150, 132, 156), GLASS_D[0])
    for k, col in enumerate(RING):
        x = 70 + k * 12
        ln = 18 + (k % 3) * 8
        for y in range(156, 156 + ln, 3):
            s.px(x, y, CHAIN[1])
            s.px(x + 1, y + 1, CHAIN[0])
        y = 156 + ln
        crown = s.poly([(x - 5, y + 6), (x - 5, y), (x - 3, y + 3), (x, y - 1), (x + 3, y + 3), (x + 5, y), (x + 5, y + 6)])
        s.fill(crown, (150, 130, 70) if k != 3 else (120, 120, 130))
        s.line(x - 5, y + 6, x + 5, y + 6, (90, 74, 40))
        s.px(x, y + 4, col, glow=True)                                                     # the dead gem still glints
        s.px(x + 3, y + 2, (40, 32, 20))                                                   # a crack in the gold
    _heart(s, 100, 112)
    _six_cracks(s, 100, 112, 0.7)
    _pauldrons(s, 74, 126, 2)
    _vael_head(s, dx=12)
    # both arms reaching forward, long and thin, talons out
    s.g("arm_f", 78, 90)
    s.part(s.capsule(78, 90, 50, 128, 4.5, 4), GLASS, bias=-0.15)
    s.g("fore_f", 50, 128, "arm_f")
    s.part(s.capsule(50, 128, 30, 98, 3.8, 3), GLASS, bias=-0.15, edge=False)
    _talons(s, 29, 96, (-2.6, -2.2, -1.8, -1.4), 16, 1.4)
    for x, y in ((14, 70), (20, 62), (8, 82), (26, 56)):
        s.px(x, y, GREY_GLOW[1], glow=True)
    s.g("weapon", 124, 88)
    s.part(s.capsule(124, 88, 146, 120, 4.5, 4), GLASS)
    s.g("hand_w", 146, 120, "weapon")
    s.part(s.capsule(146, 120, 174, 98, 3.8, 3), GLASS, edge=False)
    _talons(s, 176, 96, (-1.2, -0.8, -0.4, 0.0, 0.4), 16, 1.4)
    for x, y in ((186, 80), (192, 92), (182, 70), (194, 104)):
        s.px(x, y, GREY_GLOW[1], glow=True)
    s.ink()
    _dust(s, 70, 12)
    s.shadow(100, 312, 34, 4)
    return s


VARIANTS = {"vael_orrun_bone": vael_orrun_bone, "vael_orrun_knight": vael_orrun_knight,
            "vael_orrun_sixarm": vael_orrun_sixarm, "vael_orrun_beast": vael_orrun_beast,
            "vael_orrun_wraith": vael_orrun_wraith}
CREATURES.update(VARIANTS)
BOSSES.update(VARIANTS)
