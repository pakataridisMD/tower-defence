"""Vael-Orrun as a humanoid demon king (design only).

Doctor Paris asked (2026-11-12) for him "more human monster demon like" after the three remake concepts. All three
here share one demonic head: a human face gone wrong, ash-red skin split by cracks of fire, burning slit-pupilled
eyes, a snarling mouth full of fangs, pointed ears, long black hair, great horns, an iron crown sunk into the brow,
and the crown-shaped wound glowing on his forehead (where Oswin's lantern goes in the epilogue).

- vael_demon:          the Demon King. A towering demon in black spiked war plate over a bare, cracked chest
                       with the Heartstone in his sternum, a torn crimson mantle, digitigrade legs and hooves, and a
                       jagged black greatsword.
- vael_demon_winged:   the Fallen. Bare-chested and gaunt, with vast torn bat wings, a spiked tail and four horns.
- vael_demon_sorcerer: the Sorcerer-King. A long crimson-and-black robe open over the chest, grey Unmaking fire
                       in both clawed hands, and long horns swept straight back.
"""
from __future__ import annotations

import math

import numpy as np

from bosses import BOSSES, EYE, GREY_GLOW, MAW, RING, TOOTH, _crack, _dust
from creatures import CREATURES
from kit import Sprite, ramp
from vael_forms import _heart, _six_cracks
from vael_remake import CRIMSON, CRIMSON_D, GOLD, OBSID, _curve, _ribbon

SKIN = ramp("5e4446", spread=0.62, shift=0.04)        # ash-dark demon hide
SKIN_D = ramp("3a2a2e", spread=0.5, shift=0.04)
HORN = ramp("3a302c", spread=0.6, shift=0.02)
HAIR = ramp("1a1418", spread=0.4, shift=0.0)
IRON = ramp("2c2a34", spread=0.6, shift=0.0)
LAVA = [(150, 30, 10), (240, 100, 20), (255, 190, 70), (255, 240, 190)]
FIRE_EYE = [(170, 60, 10), (255, 160, 30), (255, 230, 120), (255, 255, 230)]
INK = (20, 8, 10)


def _lava(s, pts, hot=True):
    _crack(s, pts, LAVA[1], LAVA[2] if hot else None)


def _demon_head(s, dx=0, dy=0, horns="ram"):
    """The shared demon head as the "head" group (pivot at the neck), jaw as "jaw". dx, dy move it."""
    assert not s._ident
    old = s.pose
    r, hx, hy = old.get("head", (0, 0, 0))
    s.pose = {**old, "head": (r, hx + dx, hy + dy)}
    s.g("head", 150, 112)
    # long black hair falling behind
    hair = s.poly([(132, 54), (150, 44), (146, 70), (140, 104), (146, 140), (128, 150), (118, 120), (124, 80)])
    s.part(hair, HAIR, bulge=0.6)
    for x0, y0, x1, y1 in ((134, 60, 124, 130), (140, 64, 134, 144), (128, 70, 120, 124)):
        s.line(x0, y0, x1, y1, HAIR[3])
    # far horn first, then the face, then the near horn
    if horns == "ram":
        far = [_curve((146, 52), (128, 20), (110, 34), 12), _curve((110, 34), (100, 50), (114, 58), 6)]
        near = [_curve((164, 52), (172, 18), (196, 22), 12), _curve((196, 22), (212, 30), (204, 48), 6)]
    elif horns == "four":
        far = [_curve((146, 52), (124, 14), (126, -10), 12), _curve((140, 60), (114, 52), (98, 40), 10)]
        near = [_curve((164, 52), (178, 12), (172, -12), 12), _curve((168, 60), (194, 54), (208, 40), 10)]
    else:  # long, swept straight back
        far = [_curve((146, 52), (120, 34), (78, 26), 14)]
        near = [_curve((162, 50), (140, 26), (96, 10), 14)]
    for k, pts in enumerate(far):
        s.part(_ribbon(s, pts, 5.5 - k * 1.2, 0.8), HORN, bias=-0.25)
    face = s.poly([(134, 54), (160, 46), (174, 54), (182, 62), (181, 70), (184, 86), (178, 92), (174, 100), (164, 110),
                   (150, 106), (138, 96), (132, 78), (132, 62)])
    s.fill(face, SKIN[2])
    s.a |= face
    # ear, long and pointed, swept back
    s.part(s.poly([(138, 70), (120, 54), (126, 66), (136, 84)]), SKIN, bias=-0.1)
    s.line(122, 58, 134, 78, SKIN[0])
    # planes of the face, lit from the upper left
    s.fill(s.poly([(132, 62), (140, 58), (144, 96), (138, 96), (132, 78)]), SKIN[1])          # the far side, in shadow
    s.fill(s.poly([(140, 56), (172, 52), (180, 60), (162, 68), (142, 62)]), SKIN[3])           # forehead
    s.line(141, 56, 169, 52, SKIN[4])
    for x in (152, 156):                                                                   # frown creases
        s.line(x, 58, x + 2, 64, SKIN[1])
    s.fill(s.poly([(142, 63), (162, 69), (180, 60), (181, 66), (163, 74), (142, 68)]), SKIN[3])      # V-shaped brow ridge
    s.line(142, 63, 162, 69, SKIN[4])
    s.line(162, 69, 180, 60, SKIN[3])
    s.line(143, 69, 163, 75, SKIN[0])
    s.line(163, 75, 181, 67, SKIN[0])
    s.fill(s.poly([(144, 70), (162, 75), (160, 81), (146, 79)]), (16, 4, 6))                  # sockets
    s.fill(s.poly([(166, 74), (180, 67), (179, 74), (169, 79)]), (16, 4, 6))
    for pts, core, hot in (([(146, 72), (160, 77), (159, 80), (147, 77)], [(149, 74), (157, 77), (156, 78), (149, 76)], (151, 75)),
                           ([(168, 77), (178, 70), (178, 73), (170, 78)], [(170, 76), (176, 72), (176, 73), (171, 77)], (174, 73))):
        s.fill(s.poly(pts), (110, 34, 8), glow=True)                                        # the socket smoulders
        s.fill(s.poly(pts) & ~s.poly(core), FIRE_EYE[0], glow=True)
        s.fill(s.poly(core), FIRE_EYE[2], glow=True)
        s.px(*hot, FIRE_EYE[3], glow=True)
    s.line(154, 74, 154, 79, (16, 4, 6))                                                   # slit pupils
    s.line(173, 72, 173, 76, (16, 4, 6))
    # nose: a long hooked ridge from between the brows, snarl creases across it
    s.fill(s.poly([(162, 74), (166, 73), (182, 87), (176, 88)]), SKIN[3])
    s.fill(s.poly([(160, 78), (163, 76), (176, 88), (168, 89)]), SKIN[1])
    s.line(165, 74, 181, 86, SKIN[4])
    s.line(176, 87, 179, 87, (16, 4, 6))
    for y in (79, 82):
        s.line(167, y, 171, y - 1, SKIN[0])
    # cheekbone and the hollow beneath it
    s.fill(s.poly([(146, 81), (164, 82), (166, 85), (150, 88)]), SKIN[3])
    s.line(147, 81, 163, 82, SKIN[4])
    s.fill(s.poly([(144, 88), (158, 86), (152, 100), (142, 96)]), SKIN[0])
    # the crown sunk into the brow, and the crown-shaped wound below it
    crown = [(134, 56), (136, 40), (141, 48), (147, 32), (152, 46), (158, 30), (163, 46), (169, 36), (172, 54)]
    s.part(s.poly(crown), IRON, flat=True)
    s.line(134, 56, 172, 52, IRON[4])
    s.line(136, 40, 134, 56, IRON[4])
    for x in (141, 152, 163):
        s.px(x, 52, LAVA[1], glow=True)
    wound = s.poly([(156, 64), (156, 57), (158, 60), (160, 55), (162, 60), (164, 57), (164, 64)])
    s.fill(wound, (236, 236, 244), glow=True)
    s.fill(s.poly([(157, 63), (157, 60), (160, 58), (163, 60), (163, 63)]), (255, 255, 255), glow=True)
    # cracks of fire in the hide
    _lava(s, [(138, 60), (142, 72), (139, 84), (143, 96)])
    _lava(s, [(170, 92), (166, 100), (168, 106)], hot=False)
    # mouth: a wide snarl, the lip pulled back off long fangs, corners dragged up into the cheeks
    s.fill(s.poly([(150, 88), (180, 89), (178, 95), (156, 96)]), MAW[0])
    s.line(150, 88, 180, 88, (120, 30, 34))                                                # gums
    for x, ln in ((154, 4), (157, 3), (160, 6), (163, 3), (166, 4), (169, 3), (172, 8), (175, 4), (178, 3)):
        s.fill(s.poly([(x - 1, 89), (x + 1.5, 89), (x + 0.3, 89 + ln)]), TOOTH[2])
        s.px(x, 89, TOOTH[4])
    s.line(150, 87, 146, 82, SKIN[0])
    s.line(151, 86, 181, 87, SKIN[4])
    # near horn, last so it sits in front of the crown
    for k, pts in enumerate(near):
        s.part(_ribbon(s, pts, 6.5 - k * 1.5, 0.8), HORN, bias=0.05)
        for x, y in pts[2:-2:2]:
            s.px(x, y, HORN[0])                                                          # ridges on the horn
    # the jaw: hinged under the ear, drops open on the fire
    s.g("jaw", 140, 94, "head")
    s.fill(s.poly([(154, 95), (176, 94), (174, 104), (158, 104)]), MAW[1])
    s.fill(s.ellipse(165, 99, 6, 3), MAW[2], glow=True)
    s.fill(s.ellipse(165, 99, 3, 2), MAW[3], glow=True)
    jaw = s.poly([(140, 92), (154, 98), (174, 102), (178, 98), (176, 106), (166, 115), (152, 113), (142, 102)])
    s.fill(jaw, SKIN[2])
    s.a |= jaw
    s.fill(s.poly([(162, 104), (176, 102), (175, 108), (166, 113)]), SKIN[3])               # the chin catches light
    s.line(142, 103, 152, 113, SKIN[0])
    s.line(152, 113, 166, 115, SKIN[0])
    for x, ln in ((158, 3), (162, 5), (166, 3), (170, 7), (174, 3)):
        s.fill(s.poly([(x - 1, 102), (x + 1.5, 102), (x + 0.3, 102 - ln)]), TOOTH[2])
    s.line(144, 96, 152, 108, SKIN[1])
    s.pose = old
    s.g("body")


def _limb(s, x0, y0, x1, y1, r0, r1, bias=0.0, edge=True, upper=True):
    """A muscled limb: a tapering capsule with the belly of the muscle swelling a third of the way down."""
    s.part(s.capsule(x0, y0, x1, y1, r0, r1), SKIN, bias=bias, edge=edge)
    ang = math.atan2(y1 - y0, x1 - x0)
    L = math.hypot(x1 - x0, y1 - y0)
    t = 0.38 if upper else 0.25
    s.part(s.ellipse(x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, L * 0.3, r0 * 1.12, ang), SKIN, bias=bias, edge=False)


def _torso(s, plate=True):
    """A broad, hard-muscled bare chest in flat lit planes, cracked with fire, the Heartstone sunk in the sternum."""
    chest = s.poly([(104, 130), (128, 120), (176, 120), (200, 130), (194, 160), (178, 214), (128, 214), (110, 162)])
    s.fill(chest, SKIN[2])
    s.a |= chest
    s.fill(s.poly([(104, 130), (128, 120), (130, 214), (128, 214), (110, 162)]), SKIN[1])        # the far flank
    s.fill(s.poly([(178, 150), (194, 160), (178, 214), (172, 214)]), SKIN[1])                     # the near flank turning away
    s.part(s.capsule(138, 112, 164, 112, 11), SKIN, bias=-0.05)                                  # thick neck
    s.fill(s.poly([(124, 124), (140, 112), (142, 124)]), SKIN[3])                               # trapezius
    s.fill(s.poly([(178, 124), (162, 112), (160, 124)]), SKIN[2])
    # pectorals: lit tops, a hard dark line beneath
    for pts, top in (([(124, 134), (150, 132), (150, 160), (138, 164), (124, 156)], 3),
                     ([(152, 132), (184, 134), (182, 156), (166, 164), (152, 160)], 2)):
        s.fill(s.poly(pts), SKIN[top])
        (xa, ya), (xb, yb) = pts[0], pts[1]
        s.line(xa, ya, xb, yb, SKIN[4])
        s.line(pts[3][0], pts[3][1], pts[2][0], pts[2][1], SKIN[0])
        s.line(pts[3][0], pts[3][1], pts[4][0], pts[4][1], SKIN[0])
    # the abdomen: three rows of plates, light top-left, dark bottom-right
    for row in range(3):
        y = 170 + row * 13
        for x in (136, 153):
            s.fill(s.rect(x, y, x + 14, y + 10), SKIN[2])
            s.line(x + 1, y, x + 12, y, SKIN[3])
            s.line(x + 1, y + 10, x + 13, y + 10, SKIN[1])
            s.line(x + 14, y + 1, x + 14, y + 9, SKIN[1])
    for y in (160, 168, 176):                                                                 # serratus at the flank
        s.line(126, y, 132, y + 3, SKIN[0])
        s.line(176, y, 180, y + 3, SKIN[0])
    _heart(s, 151, 146, 0.55)
    _six_cracks(s, 151, 146, 0.45)
    _lava(s, [(118, 140), (124, 152), (120, 166), (128, 180)])
    _lava(s, [(188, 142), (184, 154), (186, 168), (178, 184)])
    _lava(s, [(144, 198), (150, 206), (146, 214)], hot=False)


def _leg(s, grp, sub, hx, hy, kx, ky, ax, ay, fx, fy, tones, bias, armour=True):
    """A digitigrade demon leg: thick thigh, knee forward, long shin back, a cloven hoof."""
    s.g(grp, hx, hy)
    s.part(s.capsule(hx, hy, kx, ky, 15, 11), tones, bias=bias)
    s.g(sub, kx, ky, grp)
    s.part(s.ellipse(kx, ky, 10, 9), tones, bias=bias)
    s.part(s.capsule(kx, ky, ax, ay, 9, 6), tones, bias=bias, edge=False)
    s.part(s.capsule(ax, ay, fx, fy - 8, 6, 5), tones, bias=bias)
    s.part(s.poly([(fx - 8, fy - 10), (fx + 8, fy - 10), (fx + 12, fy), (fx - 8, fy)]), HORN, flat=True, bias=bias)
    s.line(fx + 2, fy - 9, fx + 4, fy, HORN[0])                                            # the cleft
    if armour:
        s.part(s.poly([(kx - 10, ky - 10), (kx + 10, ky - 12), (kx + 14, ky + 2), (kx, ky + 12), (kx - 12, ky + 2)]), IRON,
               flat=True, bias=bias)
        s.fill(s.poly([(kx + 8, ky - 8), (kx + 22, ky - 6), (kx + 12, ky + 2)]), IRON[3])          # knee spike
        s.part(s.poly([(kx - 6, ky + 14), (kx + 8, ky + 12), (ax + 8, ay - 4), (ax - 6, ay)]), IRON, flat=True, bias=bias)


def _grey_fire(s, x, y, k=1.0):
    """A tall flickering flame of the Unmaking: grey-white, no warmth in it."""
    for col, sc in ((GREY_GLOW[0], 1.0), (GREY_GLOW[1], 0.72), (GREY_GLOW[2], 0.46), (GREY_GLOW[3], 0.22)):
        for dx, h, w in ((-5, 22, 6), (0, 32, 8), (6, 20, 6), (-9, 12, 4), (10, 13, 4)):
            hh, ww = h * sc * k, w * sc * k + 1
            s.fill(s.poly([(x + dx * sc - ww, y), (x + dx * sc + ww, y), (x + dx * sc * 1.3 + ww * 0.3, y - hh)]), col, glow=True)
        s.fill(s.ellipse(x, y, 10 * sc * k + 1, 5 * sc * k + 1), col, glow=True)


def _claw_hand(s, x, y, ang, n=4, ln=16, tones=SKIN):
    for k in range(n):
        a = ang + (k - (n - 1) / 2) * 0.34
        mx, my = x + math.cos(a) * ln * 0.55, y + math.sin(a) * ln * 0.55
        ex, ey = mx + math.cos(a + 0.4) * ln * 0.5, my + math.sin(a + 0.4) * ln * 0.5
        s.part(s.capsule(x, y, mx, my, 2.4, 2), tones, edge=False)
        s.part(s.capsule(mx, my, ex, ey, 2, 1.5), tones, edge=False)
        s.fill(s.poly([(ex - 1.5, ey - 1), (ex + 1.5, ey + 1), (ex + math.cos(a + 0.9) * 7, ey + math.sin(a + 0.9) * 7)]), HORN[1])
    s.part(s.ellipse(x, y, 6, 5), tones)


def _spiked_pauldron(s, x, y, sgn, bias):
    """A black plate pauldron with three spikes raking back."""
    s.part(s.poly([(x - 18, y + 6), (x - 6, y - 12), (x + 16, y - 10), (x + 22, y + 10), (x + 4, y + 20)]), IRON, bias=bias)
    for k in range(3):
        bx = x - 8 + k * 9
        s.fill(s.poly([(bx - 3, y - 8 + k), (bx + 3, y - 10 + k), (bx - 6 - 4 * k * 0 + (-8 if sgn < 0 else -2), y - 30 + k * 6)]),
               IRON[3 if sgn < 0 else 2])
    s.line(x - 18, y + 6, x - 6, y - 12, IRON[4])
    s.line(x - 14, y + 10, x + 18, y + 12, IRON[0])


# ======================================================================================================================
def vael_demon(pose=None, pad=0):
    """The Demon King: black spiked war plate over a bare cracked chest, a torn crimson mantle, hooves, and a jagged
    black greatsword with fire running down the fuller."""
    s = Sprite(248, 384, pose, pad, origin=(0, 6))
    rng = np.random.default_rng(5)
    s.g("cloak", 150, 126)
    cape = [(118, 124), (186, 124), (176, 220), (170, 330), (150, 344), (132, 336), (110, 362), (92, 340), (70, 366), (60, 330),
            (72, 230), (96, 150)]
    cm = s.poly(cape)
    s.fill(cm, CRIMSON[2])
    s.a |= cm
    s.fill(s.poly([(96, 150), (118, 124), (126, 140), (84, 344), (72, 340), (60, 330), (72, 230)]) & cm, CRIMSON[3])
    for x0, y0, x1, y1 in ((112, 140, 84, 344), (130, 150, 120, 340), (150, 160, 156, 334)):
        s.line(x0, y0, x1, y1, CRIMSON[0])
        s.line(x0 - 2, y0 + 4, x1 - 4, y1 - 6, CRIMSON[3])
    s.line(96, 150, 72, 230, GOLD[3])
    s.line(72, 230, 60, 330, GOLD[2])
    for _ in range(30):
        x, y = int(rng.integers(70, 170)), int(rng.integers(240, 350))
        s.fill(s.ellipse(x, y, 1.5, 1.2) & s.a, CRIMSON_D[0])
    # far arm, hanging, claws flexing
    s.g("arm_f", 124, 136)
    _limb(s, 124, 136, 112, 196, 13, 10, -0.25)
    s.g("fore_f", 112, 196, "arm_f")
    _limb(s, 112, 196, 108, 246, 10, 7, -0.25, False, False)
    s.part(s.poly([(100, 204), (118, 202), (118, 236), (102, 238)]), IRON, flat=True, bias=-0.25)   # vambrace
    _claw_hand(s, 108, 250, 1.65, 4, 18)
    _leg(s, "leg_f", "shin_f", 136, 236, 150, 282, 132, 326, 146, 362, SKIN, -0.3)
    _leg(s, "leg_n", "shin_n", 160, 236, 178, 284, 160, 328, 178, 364, SKIN, 0.0)
    s.g("body")
    # war skirt: black plate tassets over a crimson loincloth
    s.part(s.poly([(140, 214), (166, 214), (170, 268), (152, 278), (136, 266)]), CRIMSON_D, bulge=0.6)
    for x0, x1, bot, b in ((120, 138, 256, -0.15), (134, 152, 262, 0.0), (156, 172, 262, 0.05), (168, 186, 252, 0.1)):
        s.part(s.poly([(x0, 210), (x1, 210), (x1 + 2, bot - 10), ((x0 + x1) / 2, bot), (x0 - 2, bot - 10)]), IRON, flat=True, bias=b)
        s.line(x0 - 1, 212, x0 - 2, bot - 10, IRON[4])
    s.part(s.poly([(120, 206), (184, 206), (182, 218), (122, 218)]), IRON, flat=True)                 # belt
    s.part(s.ellipse(152, 212, 8, 7), IRON)
    s.part(s.ellipse(152, 211, 4, 4), SKIN_D)                                                          # a small skull buckle
    s.pxs([(150, 210), (154, 210)], LAVA[1], glow=True)
    _torso(s)
    _spiked_pauldron(s, 118, 130, -1, -0.15)
    _demon_head(s, horns="ram")
    _spiked_pauldron(s, 184, 130, 1, 0.05)
    # near arm and the greatsword, held low and forward, point toward the ground
    s.g("weapon", 182, 138)
    _limb(s, 184, 136, 202, 196, 14, 11)
    s.g("hand_w", 200, 196, "weapon")
    _limb(s, 202, 196, 214, 240, 11, 8, 0, False, False)
    s.part(s.poly([(204, 206), (222, 210), (222, 236), (206, 238)]), IRON, flat=True)
    blade = s.poly([(212, 250), (226, 250), (234, 300), (230, 330), (238, 352), (224, 376), (216, 352), (220, 320), (212, 296)])
    s.part(blade, OBSID, flat=True)
    s.line(219, 256, 226, 350, LAVA[1], glow=True)
    s.line(220, 256, 227, 348, LAVA[0], glow=True)
    s.line(212, 252, 213, 296, OBSID[4])
    s.part(s.poly([(198, 246), (240, 244), (242, 252), (196, 254)]), IRON, flat=True)                 # crossguard
    s.part(s.capsule(218, 222, 219, 244, 3.5), IRON)                                                   # grip
    s.part(s.ellipse(216, 244, 9, 8), SKIN)                                                            # the fist
    for k in range(3):
        s.line(210, 240 + k * 3, 222, 240 + k * 3, SKIN[0])
    s.ink(INK)
    _dust(s, 50, 5, LAVA)
    s.shadow(150, 372, 70, 6)
    return s


# ======================================================================================================================
def vael_demon_winged(pose=None, pad=0):
    """The Fallen: gaunt and bare-chested, vast torn bat wings, a spiked tail, four horns, claws on both hands."""
    s = Sprite(300, 384, pose, pad, origin=(26, 6))
    # wings: bone fingers and torn membrane, far wing first
    for grp, root, tips, tones, bias in (("wing_f", (130, 136), [(40, 20), (14, 90), (30, 170), (70, 220)], SKIN_D, -0.3),
                                         ("wing", (172, 136), [(250, 0), (282, 70), (270, 150), (236, 210)], SKIN_D, 0.0)):
        s.g(grp, *root)
        rx, ry = root
        elbow = (rx + (tips[0][0] - rx) * 0.45, 60)
        pts = [root, elbow] + tips + [(rx + (tips[-1][0] - rx) * 0.2, 230)]
        mem = s.poly(pts)
        s.fill(mem, (36, 14, 18))
        s.fill(mem & s.poly([root, elbow] + tips[:2]), (48, 18, 22))
        rng = np.random.default_rng(len(tips) + int(rx))
        for k in range(len(tips) - 1):                                                     # scallops torn out between fingers
            (x0, y0), (x1, y1) = tips[k], tips[k + 1]
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            cx, cy = mx + (mx - rx) * 0.12, my + (my - ry) * 0.12
            s.a[s.ellipse(cx, cy, 16 + int(rng.integers(0, 6)), 14)] = False
        for tx, ty in tips:                                                                # veins running out to the tips
            s.line(rx, ry, (tx + elbow[0]) / 2, (ty + elbow[1]) / 2 + 20, (58, 20, 24))
        s.part(s.capsule(rx, ry, *elbow, 5, 4), HORN, bias=bias)
        for tx, ty in tips:
            s.part(s.capsule(*elbow, tx, ty, 3, 1.4), HORN, bias=bias, edge=False)
        s.fill(s.poly([(elbow[0] - 3, elbow[1]), (elbow[0] + 3, elbow[1]), (elbow[0] + (2 if grp == "wing" else -6), elbow[1] - 16)]),
               TOOTH[2])
    # tail, curling behind
    s.g("tail", 140, 218)
    tail = _curve((140, 218), (60, 260), (70, 330), 16) + _curve((70, 330), (76, 356), (100, 350), 6)[1:]
    s.part(_ribbon(s, tail, 7, 2), SKIN, bias=-0.2)
    s.part(s.poly([(98, 342), (116, 344), (104, 360)]), HORN, flat=True)
    # far arm
    s.g("arm_f", 124, 136)
    _limb(s, 124, 136, 106, 194, 12, 9, -0.25)
    s.g("fore_f", 106, 194, "arm_f")
    _limb(s, 106, 194, 92, 238, 9, 6, -0.25, False, False)
    _claw_hand(s, 90, 242, 1.9, 4, 20)
    _leg(s, "leg_f", "shin_f", 136, 236, 150, 282, 132, 326, 146, 362, SKIN, -0.3, armour=False)
    _leg(s, "leg_n", "shin_n", 160, 236, 178, 284, 160, 328, 178, 364, SKIN, 0.0, armour=False)
    s.g("body")
    s.part(s.poly([(124, 206), (182, 206), (176, 268), (160, 252), (150, 282), (138, 254), (126, 262)]), CRIMSON_D, bulge=0.5)
    s.part(s.poly([(122, 204), (184, 204), (182, 214), (124, 214)]), IRON, flat=True)
    for x in (130, 152, 174):                                                              # chains of the six crowns
        s.line(x, 214, x + 2, 236, (110, 104, 118))
    _torso(s)
    _demon_head(s, horns="four")
    s.g("weapon", 182, 138)
    _limb(s, 184, 136, 206, 186, 13, 10)
    s.g("hand_w", 206, 186, "weapon")
    _limb(s, 206, 186, 240, 168, 10, 7, 0, False, False)
    _claw_hand(s, 244, 166, -0.3, 5, 22)
    s.ink(INK)
    _dust(s, 60, 7, LAVA)
    s.shadow(156, 372, 70, 6)
    return s


# ======================================================================================================================
def vael_demon_sorcerer(pose=None, pad=0):
    """The Sorcerer-King: a long crimson-and-black robe open over a cracked chest, horns swept straight back, grey
    Unmaking fire held in both clawed hands."""
    s = Sprite(260, 384, pose, pad, origin=(10, 6))
    s.g("cloak", 150, 126)
    back = s.poly([(112, 124), (190, 124), (214, 360), (86, 360)])
    s.fill(back, CRIMSON_D[1])
    s.a |= back
    # far arm, raised, holding the grey fire high
    s.g("arm_f", 122, 136)
    s.part(s.capsule(122, 136, 92, 168, 11, 9), CRIMSON, bias=-0.2)
    s.g("fore_f", 92, 168, "arm_f")
    _limb(s, 92, 168, 80, 118, 9, 6, -0.25, False, False)
    s.part(s.poly([(82, 174), (104, 168), (98, 190), (76, 190)]), CRIMSON, bias=-0.2)             # hanging sleeve
    _claw_hand(s, 79, 112, -1.6, 4, 16)
    _grey_fire(s, 79, 104, 1.1)
    s.g("body")
    # the robe: open down the front over the chest, gold-trimmed, falling to the ground
    robe_l = s.poly([(112, 124), (140, 128), (136, 220), (120, 362), (84, 362), (100, 230)])
    robe_r = s.poly([(162, 128), (190, 124), (206, 230), (220, 362), (166, 362), (166, 220)])
    _torso(s)
    s.fill(robe_l, CRIMSON[3])
    s.fill(robe_r, CRIMSON[2])
    s.fill(s.poly([(84, 362), (100, 230), (106, 240), (98, 362)]), CRIMSON[1])
    s.fill(s.poly([(206, 230), (220, 362), (204, 362), (196, 240)]), CRIMSON[1])
    for x0, x1 in ((112, 104), (126, 122), (178, 186), (192, 204)):                       # long folds
        s.fill(s.poly([(x0, 236), (x0 + 3, 236), (x1 + 4, 360), (x1, 360)]), CRIMSON[1])
        s.line(x0 - 1, 236, x1 - 1, 360, CRIMSON[4])
    s.a |= robe_l | robe_r
    under = s.poly([(136, 214), (166, 214), (170, 362), (130, 362)])
    s.fill(under, OBSID[1])
    s.fill(s.poly([(136, 214), (146, 214), (142, 362), (130, 362)]), OBSID[2])
    s.a |= under
    for (x0, y0, x1, y1) in ((140, 128, 136, 220), (136, 220, 120, 362), (162, 128, 166, 220), (166, 220, 166, 362)):
        s.line(x0, y0, x1, y1, GOLD[3])
    for x0, x1 in ((104, 96), (120, 116), (186, 198), (200, 212)):
        s.line(x0, 240, x1, 356, CRIMSON[0])
    s.part(s.poly([(124, 206), (178, 206), (176, 216), (126, 216)]), IRON, flat=True)
    rng = np.random.default_rng(8)
    for _ in range(40):                                                                    # the hem burning to ash
        x, y = int(rng.integers(86, 220)), int(rng.integers(352, 368))
        s.px(x, y, LAVA[int(rng.integers(0, 3))] if rng.random() < 0.5 else (60, 50, 50), glow=True)
    # a high collar of black spikes
    for k in range(7):
        a = math.pi + 0.3 + k * 0.42
        x0, y0 = 150 + math.cos(a) * 28, 122 + math.sin(a) * 6
        s.part(s.poly([(x0 - 4, y0), (x0 + 4, y0), (150 + math.cos(a) * 40, 122 + math.sin(a) * 6 - 26 - (k % 2) * 10)]),
               OBSID, flat=True)
    _demon_head(s, horns="long")
    # near arm, forward, the grey fire in an open palm
    s.g("weapon", 182, 136)
    s.part(s.capsule(182, 136, 202, 186, 12, 10), CRIMSON)
    s.g("hand_w", 202, 186, "weapon")
    _limb(s, 202, 186, 234, 172, 9, 6, 0, False, False)
    s.part(s.poly([(196, 180), (214, 176), (218, 200), (196, 204)]), CRIMSON)
    _claw_hand(s, 238, 170, -0.9, 4, 16)
    _grey_fire(s, 242, 162, 0.9)
    s.ink(INK)
    _dust(s, 50, 4, GREY_GLOW)
    s.shadow(152, 368, 70, 6)
    return s


DEMONS = {"vael_demon": vael_demon, "vael_demon_winged": vael_demon_winged, "vael_demon_sorcerer": vael_demon_sorcerer}
CREATURES.update(DEMONS)
BOSSES.update(DEMONS)
