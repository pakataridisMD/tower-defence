"""The thirty kinds of the Unbound hordes, hand-drawn in the pix2d style (see creatures.py and kit.py).

Five for each land's invaders, each shaped by the art of the kingdom whose Warden sent it:

  the Tide   (Tidelore: drowned things, rime, sea-fog)          brinecaller rimeback fogwife netcaster mire_eel
  the Stone  (Runecarving: oaths, weight, standing stones)      oathbroken runebearer quarry_hound geode menhir
  the Hollow (Starcraft: shadow, the road of the dead)          lightdrinker gravecaller umbral_stalker voidmaw wailing_widow
  the Flame  (Kindling: cinders, slag, glass, brass)            cinderhound slagwalker smoke_wraith glass_singer brass_juggernaut
  the Sky    (Stormsong: wind, lost voices, lightning)          gale_harpy voiceless stormrider squall_witch spark_wisp
  the Grove  (Rootcraft: seed, thorn, venom, old growth)        seedsower briarling greenwitch barkhulk briar_stag

Every function draws the rest pose facing right and names its pose groups (legs, arms, head, tail...) so
anim.py and tools/art/gen_horde_art.py can animate it. Docstrings are the art notes.
"""
from __future__ import annotations

import math

import numpy as np

from creatures import (BONE, CREATURES, CYAN, DARK, GOLD, IRON, LEATHER, MOSS, RUNE, RUST, STEEL, WHITE, WOOD,
                       _slab)
from kit import Sprite, ramp

# ---------------------------------------------------------------------------------------------- palettes
DROWN = ramp("8fa3a6", spread=0.55, shift=0.0)        # drowned skin, blue-grey
DROWN_D = ramp("62777e", spread=0.5, shift=0.0)
KELP = ramp("3d5a3a", spread=0.45)
SEAROBE = ramp("2f4a52", spread=0.45, shift=0.0)
BARNACLE = ramp("cfc6ae", spread=0.5)
ICE = ramp("a8d8ec", spread=0.55, shift=0.0)
ICE_D = ramp("6aa0c0", spread=0.5, shift=0.0)
SHELL = ramp("7a4a46", spread=0.5)
SHELL_D = ramp("5a3438", spread=0.45)
FOG = ramp("b8c4c6", spread=0.5, shift=0.0)
FOG_D = ramp("7d8b90", spread=0.45, shift=0.0)
OILSKIN = ramp("4a5236", spread=0.45)
NET = (150, 140, 110)
EEL = ramp("3f5a58", spread=0.5, shift=0.0)
EEL_BELLY = ramp("9aa88a", spread=0.5)
LURE = [(60, 160, 150), (120, 240, 210), (220, 255, 240)]
TEAL_EYE = (150, 255, 230)

GRANITE = ramp("8a8c94", spread=0.5, shift=0.0)
GRANITE_D = ramp("62646e", spread=0.45, shift=0.0)
FLESH_STONE = ramp("a08c78", spread=0.5)
RUNE_GOLD = [(170, 110, 30), (250, 190, 70), (255, 240, 170)]
HOUND = ramp("6e6660", spread=0.5)
GEODE = [(70, 30, 110), (120, 60, 170), (170, 110, 220), (220, 180, 250)]
LICHEN = ramp("8a9a4a", spread=0.5)

VOIDSKIN = ramp("4a3e5e", spread=0.55, shift=0.0)
VOIDSKIN_D = ramp("2e2640", spread=0.45, shift=0.0)
VIOLET = [(110, 50, 190), (170, 100, 255), (230, 200, 255)]
SHROUD = ramp("2a2434", spread=0.4, shift=0.0)
GRAVE = ramp("6a6a5e", spread=0.5)
WIDOW = ramp("bdb8c8", spread=0.55, shift=0.0)
WIDOW_D = ramp("6e6680", spread=0.45, shift=0.0)
STALK = ramp("2a2238", spread=0.45, shift=0.0)

CINDER = ramp("3a2a26", spread=0.45)
MAGMA = [(150, 30, 10), (230, 80, 20), (255, 160, 40), (255, 230, 140)]
SLAG = ramp("5a4a44", spread=0.5)
SMOKE = ramp("6a6460", spread=0.5, shift=0.0)
GLASS = ramp("9ad8d0", spread=0.6, shift=0.0)
ROBE_RED = ramp("6a1e22", spread=0.45)
BRASS = ramp("b08a3a", spread=0.6)
BRASS_D = ramp("7a5a2a", spread=0.5)

HARPY = ramp("6a7488", spread=0.55, shift=0.0)
FEATHER = ramp("3e4658", spread=0.45, shift=0.0)
STORMSKIN = ramp("9aa0b0", spread=0.5, shift=0.0)
BOLT = [(90, 120, 230), (170, 210, 255), (240, 250, 255)]
HORSE = ramp("3a3e4c", spread=0.5, shift=0.0)
CLOTH_BLUE = ramp("2e3a5e", spread=0.45, shift=0.0)

BARK = ramp("5a4630", spread=0.5)
BARK_D = ramp("3e3022", spread=0.45)
LEAF = ramp("4a7a2e", spread=0.5)
THORN = ramp("8a6a48", spread=0.5)
VENOM = [(80, 150, 30), (150, 220, 60), (220, 255, 150)]
GREENSKIN = ramp("7a8a5a", spread=0.5)
ANTLER = ramp("c8b890", spread=0.5)
STAG = ramp("4a3628", spread=0.5)
PETAL = ramp("8a2a4a", spread=0.5)


# ---------------------------------------------------------------------------------------------- helpers
def leg(s, side, hip, knee, ankle, r, tones, foot=None, foot_r=(3.4, 2.0), foot_tones=None, bias=0.0, r2=None):
    """A leg bent at the knee: thigh in group leg_<side>, shin and foot in shin_<side>."""
    s.g("leg_" + side, *hip)
    s.part(s.capsule(*hip, *knee, r), tones, bias=bias)
    s.g("shin_" + side, *knee, "leg_" + side)
    s.part(s.capsule(*knee, *ankle, r2 if r2 is not None else r * 0.9), tones, bias=bias, edge=False)
    if foot:
        s.part(s.ellipse(*foot, *foot_r), foot_tones or tones, bias=bias)


def arm(s, group, child, shoulder, elbow, hand, r, tones, bias=0.0, hand_r=None, hand_tones=None, r2=None, parent=None):
    """An arm bent at the elbow: upper arm in `group`, forearm and hand in `child`."""
    s.g(group, *shoulder, parent)
    s.part(s.capsule(*shoulder, *elbow, r), tones, bias=bias)
    s.g(child, *elbow, group)
    s.part(s.capsule(*elbow, *hand, r2 if r2 is not None else r * 0.9), tones, bias=bias, edge=False)
    if hand_r:
        s.part(s.ellipse(*hand, hand_r, hand_r * 0.95), hand_tones or tones, bias=bias)


def eyes(s, pts, col, glow=True):
    s.pxs(pts, col, glow=glow)


def dither_out(s, x0, x1, y0, y1, keep=lambda x, y: (x + y) % 2):
    """Knock out every other pixel in a box (drawn in rest coordinates) for wisps and ragged hems."""
    for y in range(y0, y1):
        for x in range(x0, x1):
            tx, ty = (round(v) for v in s.fw(x, y))
            if 0 <= tx < s.w and 0 <= ty < s.h and s.a[ty, tx] and not keep(x, y):
                s.a[ty, tx] = False


# ================================================================================================ THE TIDE
def brinecaller(pose=None, pad=0):
    """Brinecaller: a drowned tide-priest, stooped, in a rotted sea-green cope hung with kelp and barnacles. Pale
    drowned face with no lips and teal glints for eyes. A long crook with a dripping brine censer swinging from it."""
    s = Sprite(52, 60, pose, pad)
    s.g("cloak", 20, 22)
    s.part(s.poly([(18, 22), (26, 22), (24, 50), (18, 53), (12, 52), (10, 46), (14, 34)]), SEAROBE, bias=-0.2)
    for x, y in ((12, 52), (15, 53), (11, 49)):
        s.px(x, y + 1, KELP[1])
    leg(s, "f", (23, 41), (22, 46), (21.5, 51), 2.2, DROWN_D, foot=(22, 53), foot_r=(2.8, 1.5), bias=-0.3)
    s.g("weapon", 30, 26)
    # crook behind the near hand: long haft, hook at the top, censer hanging from the hook
    s.g("hand_w", 34, 31, "weapon")
    s.part(s.capsule(36, 52, 39, 6, 1.1), WOOD, flat=True)
    s.part(s.capsule(39, 6, 43, 3, 1.0) | s.capsule(43, 3, 46, 6, 1.0) | s.capsule(46, 6, 45, 10, 1.0), WOOD, flat=True)
    s.g("chain", 45, 10, "hand_w")
    s.line(45, 10, 45, 15, IRON[2])
    s.part(s.ellipse(45, 18, 2.6, 3.0), IRON)
    s.pxs([(44, 17), (46, 19)], TEAL_EYE, glow=True)
    s.pxs([(45, 22), (44, 24), (46, 26)], ICE[3], glow=True)                 # brine dripping
    s.g("body")
    # stooped body in the cope, rope belt, kelp hanging
    s.part(s.poly([(17, 22), (31, 20), (33, 32), (34, 46), (16, 46), (15, 32)]), SEAROBE)
    s.line(22, 24, 20, 45, SEAROBE[1])
    s.line(28, 24, 29, 45, SEAROBE[1])
    s.part(s.rect(16, 34, 33, 36), LEATHER, flat=True)
    for x0, y0, x1, y1 in ((19, 36, 18, 44), (25, 36, 26, 45), (30, 36, 31, 42)):
        s.line(x0, y0, x1, y1, KELP[2])
    s.pxs([(19, 27), (20, 28), (29, 30), (24, 40), (18, 31)], BARNACLE[3])
    s.pxs([(20, 27), (30, 30), (25, 40)], BARNACLE[1])
    dither_out(s, 15, 35, 44, 47, keep=lambda x, y: (x * 3) % 5)
    leg(s, "n", (28, 43), (29, 47), (28.5, 51), 2.3, DROWN, foot=(30, 53), foot_r=(3.0, 1.5))
    s.g("head", 29, 21)
    # head hung forward under a hood, drowned face
    s.part(s.ellipse(29, 15, 7.6, 7.8) | s.poly([(21, 16), (36, 12), (36, 22), (22, 23)]), SEAROBE)
    s.part(s.ellipse(32, 17, 4.4, 5.0), DROWN)
    s.fill(s.rect(31, 15, 36, 17), (20, 30, 34))
    eyes(s, [(32, 15), (35, 15)], TEAL_EYE)
    s.line(32, 20, 35, 20, DROWN_D[0])
    s.pxs([(33, 21), (35, 21)], DROWN[3])                                   # teeth, no lips
    s.pxs([(26, 9), (24, 11), (34, 9)], BARNACLE[3])
    s.g("hair", 25, 12, "head")
    s.part(s.poly([(25, 11), (21, 13), (18, 24), (22, 21)]), KELP)             # kelp hanging from the hood
    s.g("weapon", 30, 26)
    arm(s, "weapon", "hand_w", (30, 26), (34, 31), (37, 30), 2.2, SEAROBE, hand_r=1.9, hand_tones=DROWN)
    arm(s, "arm_n", "fore_n", (22, 26), (21, 33), (25, 37), 2.2, SEAROBE, hand_r=1.8, hand_tones=DROWN)
    s.ink()
    s.shadow(25, 54.5, 11, 2.2)
    return s


def rimeback(pose=None, pad=0):
    """Rimeback: a crab as big as a cart, dragged up from under the ice. A high domed shell crusted with jagged rime
    crystals, one huge claw held forward and open, eyes on stalks, legs splayed wide and bent twice like a spider's."""
    s = Sprite(78, 54, pose, pad)
    # far legs first (darker): out and up to the knee, then down to a point
    for i, (hx, kx, ky, fx) in enumerate(((50, 60, 22, 64), (44, 50, 20, 53), (34, 28, 20, 25), (28, 18, 23, 13))):
        side = ("f", "f2", "f3", "f4")[i]
        s.g("leg_" + side, hx, 32)
        s.part(s.capsule(hx, 32, kx, ky, 2.3, 2.0), SHELL_D, bias=-0.3)
        s.g("shin_" + side, kx, ky, "leg_" + side)
        s.part(s.capsule(kx, ky, fx, 46, 2.0, 0.8), SHELL_D, bias=-0.3, edge=False)
    # small claw behind
    s.g("arm_f", 54, 33)
    s.part(s.capsule(54, 33, 61, 30, 2.4), SHELL_D, bias=-0.2)
    s.g("fore_f", 61, 30, "arm_f")
    s.part(s.poly([(60, 27), (68, 26), (66, 30), (61, 33)]), SHELL_D, bias=-0.2)
    s.g("body")
    # the shell: a high dome, pale underside, rime crusted thick on top
    shell = s.ellipse(39, 33, 19, 11.5) & s.rect(0, 0, 80, 41)
    s.part(shell, SHELL)
    s.part(s.ellipse(39, 39, 17, 4) & s.rect(0, 0, 80, 42), SHELL_D, edge=False)
    s.line(22, 40, 56, 40, SHELL[0])
    for x, y in ((26, 34), (33, 36), (44, 36), (51, 33), (30, 30), (48, 29)):
        s.px(x, y, BARNACLE[3])
        s.px(x + 1, y, BARNACLE[1])
    crust = s.ellipse(39, 30, 17, 8) & s.rect(0, 0, 80, 30)
    s.part(crust, ICE_D, bias=0.1)
    for (x, top, w) in ((26, 18, 2.5), (30, 12, 3.5), (35, 15, 3), (40, 8, 4), (45, 13, 3), (50, 17, 3), (34, 20, 2), (47, 21, 2)):
        s.part(s.poly([(x - w, 27), (x, top), (x + w * 0.7, 26)]), ICE, flat=True, bias=0.1)
        s.line(x, top + 1, x - w + 1, 26, ICE[4])
    # eyes on stalks
    s.g("head", 55, 30)
    for x in (54, 58):
        s.part(s.capsule(x, 30, x + 1, 22, 1.0), SHELL)
        s.part(s.ellipse(x + 1, 21, 1.8, 1.8), [(10, 10, 14), (30, 30, 40)])
        s.px(x + 1, 20, TEAL_EYE, glow=True)
    s.pxs([(58, 35), (59, 36), (58, 37)], SHELL_D[0])
    # near legs
    for i, (hx, kx, ky, fx) in enumerate(((52, 64, 28, 70), (46, 54, 26, 58), (34, 26, 26, 21), (28, 16, 30, 10))):
        side = ("n", "n2", "n3", "n4")[i]
        s.g("leg_" + side, hx, 38)
        s.part(s.capsule(hx, 38, kx, ky, 2.6, 2.2), SHELL)
        s.g("shin_" + side, kx, ky, "leg_" + side)
        s.part(s.capsule(kx, ky, fx, 49, 2.2, 0.8), SHELL, edge=False)
        s.px(kx, ky - 2, SHELL[4])
    # the great claw, held forward and open
    s.g("weapon", 56, 37)
    s.part(s.capsule(56, 37, 63, 40, 3.2), SHELL)
    s.g("hand_w", 63, 40, "weapon")
    s.part(s.ellipse(67, 38, 5, 4), SHELL, edge=False)
    s.part(s.poly([(66, 34), (77, 28), (76, 33), (70, 37)]), SHELL, bias=0.1)            # upper pincer
    s.part(s.poly([(69, 40), (77, 40), (74, 44), (66, 43)]), SHELL_D)                    # lower pincer
    s.pxs([(73, 31), (75, 30), (72, 40), (74, 41)], BARNACLE[4])
    s.part(s.poly([(63, 36), (66, 30), (69, 35)]), ICE, flat=True)
    s.ink()
    s.shadow(40, 49.5, 28, 2.8)
    return s


def fogwife(pose=None, pad=0):
    """Fogwife: a drowned seer who gave the water every memory she had, even her face. A tall, hunched shape in wet
    grey veils that fray into fog, long lank hair, bony arms reaching ahead with long fingers, a blank grey face with
    two cold pinprick eyes and a mouth hanging open on nothing."""
    s = Sprite(52, 64, pose, pad)
    s.g("tail", 22, 34)
    s.part(s.poly([(15, 30), (29, 30), (31, 44), (27, 52), (20, 57), (13, 56), (9, 50), (12, 41)]), FOG_D, bias=-0.1)
    for x, y in ((10, 57), (7, 54), (15, 59), (20, 60), (5, 58), (25, 58), (12, 61), (3, 55)):
        s.px(x, y, FOG[1 + (x + y) % 2])
    dither_out(s, 6, 34, 44, 60, keep=lambda x, y: ((x + y) % 2 == 0 and y < 47 + (x % 6)) or (x * 7 + y) % 5 == 0)
    arm(s, "arm_f", "fore_f", (26, 24), (31, 32), (40, 33), 1.3, FOG_D, bias=-0.25)
    s.g("fore_f", 31, 32, "arm_f")
    for dx, dy in ((4, -1), (5, 1), (4, 3)):
        s.line(40, 33, 40 + dx, 33 + dy, BONE[1])
    s.g("body")
    # hunched body: the back rounds up high, the chest sinks
    s.part(s.poly([(14, 22), (22, 15), (31, 18), (32, 30), (29, 40), (15, 40), (12, 30)]), FOG)
    s.line(19, 21, 17, 39, FOG[1])
    s.line(25, 22, 25, 39, FOG[1])
    s.line(29, 26, 29, 38, FOG[1])
    s.g("head", 30, 20)
    s.g("hair", 27, 13, "head")
    s.part(s.poly([(26, 12), (20, 15), (17, 30), (21, 27), (23, 33), (26, 24), (28, 30), (29, 19)]), [(40, 44, 50), (58, 64, 70), (76, 84, 90)])
    s.g("head", 30, 20)
    # veil over the head, hanging forward
    s.part(s.ellipse(31, 15, 6.2, 6.8) | s.poly([(25, 15), (37, 13), (39, 24), (26, 22)]), FOG)
    s.fill(s.ellipse(34, 17.5, 3.5, 4.6), (150, 160, 164))                         # the blank face
    s.fill(s.ellipse(34.5, 18.5, 2.5, 3.2), (128, 138, 144))
    eyes(s, [(33, 16), (36, 16)], (220, 255, 255))
    s.pxs([(34, 20), (35, 20), (34, 21), (35, 21), (34, 22)], (24, 28, 34))         # mouth hanging open
    arm(s, "weapon", "hand_w", (26, 25), (34, 32), (44, 31), 1.5, FOG)
    s.g("hand_w", 34, 32, "weapon")
    for dx, dy in ((4, -3), (5, -1), (5, 1), (3, 3)):
        s.line(44, 31, 44 + dx, 31 + dy, BONE[2])
    s.ink((50, 60, 70))
    s.opacity = 235
    s.shadow(22, 61, 9, 1.8)
    return s


def netcaster(pose=None, pad=0):
    """Drowned Netcaster: a big drowned fisherman in a rotted oilskin coat, sou'wester hat, one hand a rusted hook,
    a weighted net bundled over the other shoulder. Bloated grey face, one eye gone, one burning teal."""
    s = Sprite(56, 58, pose, pad)
    s.g("arm_f", 21, 24)
    # net bundle on the far shoulder, weights hanging
    s.part(s.ellipse(17, 27, 7, 8), [(70, 64, 50), (110, 100, 78), (140, 130, 100), (160, 150, 118)])
    for i in range(6):
        s.line(11 + i * 2, 20, 13 + i * 2, 34, (80, 72, 56))
    for i in range(5):
        s.line(10, 21 + i * 3, 24, 22 + i * 3, (80, 72, 56))
    s.pxs([(11, 35), (15, 36), (20, 35)], IRON[2])
    leg(s, "f", (23, 40), (22.5, 45), (22, 50), 2.8, OILSKIN, foot=(22, 52), foot_r=(3.6, 1.8), foot_tones=LEATHER, bias=-0.3)
    s.g("body")
    s.part(s.ellipse(27, 30, 10, 11), OILSKIN)
    s.part(s.poly([(17, 34), (37, 34), (38, 44), (16, 44)]), OILSKIN)
    s.line(27, 21, 27, 43, OILSKIN[1])
    s.pxs([(28, 26), (28, 31), (28, 36)], BARNACLE[3])
    s.part(s.rect(17, 36, 37, 38), LEATHER, flat=True)
    dither_out(s, 15, 39, 43, 45, keep=lambda x, y: x % 3)
    leg(s, "n", (31, 41), (32, 46), (31.5, 50), 3.0, OILSKIN, foot=(33, 52), foot_r=(4.0, 1.9), foot_tones=LEATHER)
    s.g("head", 30, 20)
    # bloated drowned face under a sou'wester
    s.part(s.ellipse(32, 15, 6.6, 6.4), DROWN)
    s.part(s.ellipse(35, 18.5, 4, 2.5), DROWN_D)                      # jowl
    s.fill(s.rect(30, 13, 33, 15), (24, 30, 36))
    s.px(31, 13, TEAL_EYE, glow=True)
    s.px(32, 14, LURE[1], glow=True)
    s.pxs([(35, 13), (36, 13), (35, 14)], DROWN_D[0])                   # the empty socket
    s.line(33, 19, 37, 19, DROWN_D[0])
    s.part(s.ellipse(30.5, 10, 8.5, 3.6) | s.poly([(22, 10), (40, 9), (42, 12), (21, 13)]), OILSKIN, bias=0.15)
    s.line(21, 12, 42, 12, OILSKIN[4])
    s.pxs([(25, 8), (35, 8)], BARNACLE[3])
    # near arm ends in a hook
    arm(s, "weapon", "hand_w", (24, 24), (28, 31), (34, 33), 3.0, OILSKIN, r2=2.6)
    s.g("hand_w", 28, 31, "weapon")
    s.part(s.capsule(34, 33, 37, 32, 1.6), RUST, flat=True)
    s.part(s.capsule(37, 32, 41, 28, 1.3) | s.capsule(41, 28, 40, 24, 1.2) | s.capsule(40, 24, 37, 25, 1.0), RUST, flat=True)
    s.px(37, 26, RUST[4])
    s.ink()
    s.shadow(28, 53, 13, 2.4)
    return s


def mire_eel(pose=None, pad=0):
    """Mire Eel: a drowned eel as long as a boat, slithering in an S along the road. Slick dark back, pale belly,
    a ragged fin down its spine, a lantern lure dangling over a mouth full of needles."""
    s = Sprite(78, 40, pose, pad)
    pts = [(4, 26), (12, 30), (22, 31), (32, 27), (42, 24), (50, 26)]
    groups = [("tail2", 22, 31, "tail"), ("tail2", 22, 31, "tail"), ("tail", 42, 24, None), ("tail", 42, 24, None),
              ("body", 0, 0, None)]
    for i, ((x0, y0), (x1, y1)) in enumerate(zip(pts, pts[1:])):
        g = groups[i]
        if g[0] == "body":
            s.g("body")
        else:
            if g[0] == "tail2":
                s.g("tail", 42, 24)
            s.g(*g[:3], g[3])
        r0, r1 = 1.2 + i * 1.3, 2.4 + i * 1.3
        s.part(s.capsule(x0, y0, x1, y1, r0, r1), EEL, edge=False)
        s.part(s.capsule(x0, y0 + r0 * 0.6, x1, y1 + r1 * 0.6, r0 * 0.5, r1 * 0.5), EEL_BELLY, edge=False, bias=0.1)
        # spine fin
        s.part(s.poly([(x0, y0 - r0 + 1), (x1, y1 - r1 + 1), ((x0 + x1) / 2, min(y0, y1) - r1 - 2.5)]), KELP, flat=True, edge=False)
    s.g("body")
    s.part(s.ellipse(54, 25, 8, 6.2), EEL)
    s.part(s.ellipse(55, 28.5, 6, 2.5), EEL_BELLY, edge=False)
    s.g("neck", 56, 25)
    s.g("head", 58, 24, "neck")
    s.g("jaw", 60, 28, "head")
    s.part(s.poly([(58, 27), (73, 28), (71, 31), (58, 31)]), EEL_BELLY)
    for x in range(61, 72, 2):
        s.px(x, 27, WHITE)
    s.g("head", 58, 24, "neck")
    s.part(s.poly([(56, 18), (66, 19), (75, 24), (73, 27), (57, 28)]), EEL)
    for x in range(62, 73, 2):
        s.px(x, 27, WHITE)
        s.px(x + 1, 28, BONE[2])
    s.fill(s.rect(64, 21, 66, 23), (230, 240, 210), glow=True)
    s.px(65, 22, DARK)
    s.line(62, 20, 67, 20, EEL[0])
    # the lure on its stalk
    s.g("plume", 60, 18, "head")
    s.part(s.capsule(60, 18, 66, 10, 0.8) | s.capsule(66, 10, 71, 11, 0.7), EEL, edge=False)
    s.part(s.ellipse(71.5, 13, 2.0, 2.2), LURE, glow=True)
    s.px(71, 12, LURE[2], glow=True)
    s.ink()
    s.shadow(40, 35.5, 30, 2.2)
    return s


# ================================================================================================ THE STONE
def _crystal(s, x, base, top, w, tones=GEODE, glow=True):
    s.fill(s.poly([(x - w, base), (x, top), (x + w, base)]), tones[1], glow=glow)
    s.fill(s.poly([(x - w + 1, base), (x, top + 1), (x, base)]), tones[2], glow=glow)
    s.line(x, top + 1, x - w + 1, base - 1, tones[3], glow=glow)


def oathbroken(pose=None, pad=0):
    """Oathbroken: a Stoneborn mason who broke a carved oath and is slowly turning to stone. Broad and stooped,
    half his body still flesh in torn leather, the other half grown over with grey granite slabs that split his
    clothes, a cracked rune glowing in the stone of his chest. Drags a broken mason's maul; a snapped chain on one wrist."""
    s = Sprite(56, 56, pose, pad)
    s.g("weapon", 32, 25)
    s.g("hand_w", 36, 31, "weapon")
    s.part(s.capsule(38, 35, 46, 14, 1.3), WOOD, flat=True)
    _slab(s, [(41, 8), (52, 11), (50, 18), (39, 15)], GRANITE_D, depth=(2, -2), chips=1, seed=21)
    s.g("arm_f", 20, 25)
    s.part(s.capsule(20, 25, 17, 32, 3.0), FLESH_STONE, bias=-0.25)
    s.g("fore_f", 17, 32, "arm_f")
    s.part(s.capsule(17, 32, 16, 38, 2.8), FLESH_STONE, bias=-0.25, edge=False)
    s.part(s.ellipse(16, 40, 3.0, 2.8), FLESH_STONE, bias=-0.2)
    s.line(16, 42, 14, 46, IRON[2])
    s.pxs([(14, 47), (13, 48)], IRON[1])
    leg(s, "f", (23, 40), (22, 45), (21.5, 50), 3.0, LEATHER, foot=(21.5, 52), foot_r=(3.8, 1.8), bias=-0.3)
    s.g("body")
    s.part(s.ellipse(26, 31, 10.5, 10), LEATHER)
    s.part(s.poly([(17, 36), (35, 36), (36, 44), (16, 44)]), LEATHER)
    # granite grown over the back and the near shoulder, splitting the leather
    _slab(s, [(14, 22), (24, 18), (27, 30), (17, 38)], GRANITE, chips=2, seed=22)
    _slab(s, [(25, 24), (33, 23), (34, 33), (26, 35)], GRANITE_D, depth=(2, -2), chips=1, seed=23)
    s.line(27, 26, 30, 30, RUNE_GOLD[1], glow=True)
    s.line(30, 30, 28, 33, RUNE_GOLD[1], glow=True)
    s.px(29, 28, RUNE_GOLD[2], glow=True)
    s.part(s.rect(16, 38, 36, 40), LEATHER, flat=True, bias=-0.2)
    leg(s, "n", (30, 41), (31, 46), (30.5, 50), 3.2, GRANITE_D, foot=(32, 52), foot_r=(4.2, 2.0), foot_tones=GRANITE)
    s.g("head", 30, 21)
    s.part(s.ellipse(32, 15.5, 6.2, 6.2), FLESH_STONE)
    _slab(s, [(26, 9), (33, 8), (32, 17), (26, 19)], GRANITE, depth=(2, -2), chips=1, seed=24)   # stone over half the face
    s.part(s.poly([(33, 10), (39, 13), (38, 21), (33, 21)]), FLESH_STONE, edge=False)
    s.px(36, 14, (40, 24, 20))
    s.px(30, 13, RUNE_GOLD[2], glow=True)                       # the stone eye still burns
    s.px(39, 16, FLESH_STONE[1])
    s.line(34, 19, 37, 19, FLESH_STONE[0])
    s.part(s.poly([(33, 19), (39, 19), (37, 24), (34, 23)]), [(70, 62, 56), (100, 90, 80), (130, 118, 104)])   # grey beard
    s.g("weapon", 32, 25)
    arm(s, "weapon", "hand_w", (32, 25), (36, 31), (38, 35), 3.3, GRANITE, hand_r=3.0, hand_tones=GRANITE_D)
    s.ink()
    s.shadow(27, 53, 13, 2.4)
    return s


def runebearer(pose=None, pad=0):
    """Runebearer: a bowed Stoneborn oath-keeper carrying a carved standing stone twice its height strapped to its
    back, the oath-runes on it burning gold. It walks bent nearly double under the weight, leaning on a staff."""
    s = Sprite(56, 74, pose, pad)
    s.g("body")
    # the standing stone, strapped on the back
    _slab(s, [(8, 6), (24, 3), (27, 52), (11, 55)], GRANITE, depth=(3, -3), chips=4, seed=31)
    for (x0, y0, x1, y1) in ((14, 12, 14, 22), (14, 12, 19, 15), (19, 15, 14, 18), (19, 26, 19, 36), (16, 30, 22, 30),
                             (14, 40, 18, 46), (18, 46, 22, 40)):
        s.line(x0, y0, x1, y1, RUNE_GOLD[1], glow=True)
    s.pxs([(14, 12), (19, 26), (18, 46)], RUNE_GOLD[2], glow=True)
    s.pxs([(10, 50), (11, 51), (24, 8), (25, 9)], LICHEN[2])
    s.g("arm_f", 27, 37)
    s.part(s.capsule(27, 37, 23, 43, 2.6), LEATHER, bias=-0.25)
    leg(s, "f", (24, 54), (24, 59), (23, 65), 3.0, LEATHER, foot=(23, 67), foot_r=(3.8, 1.8), foot_tones=IRON, bias=-0.3)
    s.g("body")
    # bent torso under the stone, straps across it
    s.part(s.ellipse(30, 44, 9.5, 9), FLESH_STONE)
    s.part(s.poly([(22, 47), (38, 47), (38, 57), (21, 57)]), LEATHER)
    s.line(23, 36, 37, 50, LEATHER[0])
    s.line(23, 37, 37, 51, LEATHER[2])
    s.line(21, 47, 36, 40, LEATHER[0])
    s.part(s.rect(21, 53, 39, 55), IRON, flat=True)
    leg(s, "n", (32, 55), (33, 60), (32, 65), 3.2, LEATHER, foot=(34, 67), foot_r=(4.2, 2.0), foot_tones=IRON)
    s.g("head", 37, 40)
    s.part(s.ellipse(39, 40, 6, 5.8), FLESH_STONE)
    s.part(s.ellipse(39, 36.5, 6.6, 3.4) & s.rect(0, 0, 60, 38), IRON)             # iron skullcap
    s.fill(s.rect(40, 39, 45, 41), (30, 22, 20))
    s.px(43, 39, RUNE_GOLD[2], glow=True)
    s.part(s.poly([(39, 43), (46, 42), (44, 51), (40, 47), (38, 50)]), [(80, 70, 62), (120, 110, 96), (156, 146, 128)])
    s.px(46, 40, FLESH_STONE[1])
    arm(s, "weapon", "hand_w", (33, 43), (39, 48), (44, 47), 3.0, FLESH_STONE, hand_r=2.4)
    s.g("hand_w", 39, 48, "weapon")
    s.part(s.capsule(45, 38, 47, 67, 1.1), WOOD, flat=True)                          # walking staff
    s.part(s.ellipse(45, 37, 2.2, 2.2), RUNE_GOLD, glow=True)
    s.ink()
    s.shadow(30, 68.5, 16, 2.6)
    return s


def quarry_hound(pose=None, pad=0):
    """Quarry Hound: a hunting hound carved from quarry stone and given a body by an oath of pursuit. Long low
    chiselled blocks for chest, ribs and jaw, legs of stacked stone, a rune slit for an eye, a broken chain collar."""
    s = Sprite(66, 48, pose, pad)
    # far legs
    s.g("leg_f", 46, 27)
    _slab(s, [(43, 26), (49, 26), (50, 34), (44, 35)], GRANITE_D, depth=(2, -2), seed=41)
    s.g("shin_f", 47, 35, "leg_f")
    _slab(s, [(45, 35), (49, 35), (51, 42), (46, 42)], GRANITE_D, depth=(2, -2), seed=42)
    s.g("leg_f2", 20, 27)
    _slab(s, [(17, 25), (24, 25), (24, 34), (18, 34)], GRANITE_D, depth=(2, -2), seed=43)
    s.g("shin_f2", 21, 34, "leg_f2")
    _slab(s, [(17, 34), (22, 34), (20, 42), (15, 42)], GRANITE_D, depth=(2, -2), seed=44)
    # tail
    s.g("tail", 13, 22)
    _slab(s, [(4, 13), (8, 12), (14, 20), (11, 23)], HOUND, depth=(2, -2), seed=45)
    s.g("body")
    # chest block, rib slabs, haunch
    _slab(s, [(12, 18), (26, 16), (27, 31), (13, 30)], HOUND, chips=2, seed=46)
    _slab(s, [(25, 19), (37, 18), (37, 29), (26, 30)], GRANITE_D, chips=1, seed=47)
    for x in (28, 31, 34):
        s.line(x, 20, x, 28, GRANITE_D[0])
    _slab(s, [(36, 14), (50, 13), (51, 30), (38, 31)], HOUND, chips=3, seed=48)
    s.line(42, 18, 46, 24, RUNE[1], glow=True)
    s.line(46, 24, 42, 28, RUNE[1], glow=True)
    s.g("neck", 48, 18)
    s.g("head", 52, 16, "neck")
    s.g("jaw", 54, 22, "head")
    _slab(s, [(51, 21), (63, 22), (62, 26), (52, 26)], GRANITE_D, depth=(2, -2), seed=49)
    s.pxs([(55, 21), (57, 21), (59, 21), (61, 22)], BONE[3])
    s.g("head", 52, 16, "neck")
    _slab(s, [(48, 8), (58, 9), (65, 17), (64, 21), (50, 21)], HOUND, chips=1, seed=50)
    _slab(s, [(49, 3), (53, 4), (54, 10), (50, 10)], GRANITE_D, depth=(2, -2), seed=51)       # ear
    s.fill(s.rect(56, 12, 60, 14), RUNE[1], glow=True)
    s.px(58, 12, RUNE[2], glow=True)
    s.pxs([(62, 18), (63, 18), (57, 20), (59, 20), (61, 20)], BONE[3])
    s.g("neck", 48, 18)
    s.part(s.capsule(47, 13, 49, 23, 1.4), IRON, flat=True)
    s.pxs([(46, 25), (45, 27), (46, 29)], IRON[2])
    # near legs
    s.g("leg_n2", 17, 28)
    _slab(s, [(13, 26), (21, 26), (22, 35), (14, 35)], HOUND, depth=(2, -2), seed=52)
    s.g("shin_n2", 17, 35, "leg_n2")
    _slab(s, [(13, 35), (19, 35), (17, 43), (11, 43)], HOUND, depth=(2, -2), seed=53)
    s.g("leg_n", 43, 28)
    _slab(s, [(40, 27), (47, 27), (47, 36), (41, 36)], HOUND, depth=(2, -2), seed=54)
    s.g("shin_n", 44, 36, "leg_n")
    _slab(s, [(42, 36), (47, 36), (49, 43), (43, 43)], HOUND, depth=(2, -2), seed=55)
    s.ink()
    s.shadow(33, 44.5, 22, 2.2)
    return s


def geode(pose=None, pad=0):
    """Geode Brute: a boulder of the deep halls that split open and stood up. A hulking shell of grey rock blocks,
    the front cracked wide on a heart of violet crystal that glows; crystal fists, a small head sunk between the
    shoulders. Its facets scatter any blow that is spread thin."""
    s = Sprite(70, 66, pose, pad)
    s.g("arm_f", 50, 22)
    _slab(s, [(46, 19), (56, 20), (57, 32), (47, 32)], GRANITE_D, chips=1, seed=61)
    s.g("fore_f", 52, 32, "arm_f")
    _slab(s, [(48, 32), (56, 32), (57, 44), (49, 44)], GRANITE_D, seed=62)
    _crystal(s, 52, 52, 41, 4, glow=False)
    leg(s, "f", (30, 46), (29, 52), (29, 58), 4.0, GRANITE_D, bias=-0.3)
    s.g("shin_f", 29, 52, "leg_f")
    _slab(s, [(24, 56), (35, 56), (36, 61), (23, 61)], GRANITE_D, depth=(2, -2), seed=63)
    s.g("leg_n", 41, 46)
    _slab(s, [(37, 45), (46, 45), (46, 54), (38, 54)], GRANITE_D, seed=64)
    s.g("shin_n", 42, 54, "leg_n")
    _slab(s, [(36, 55), (49, 55), (50, 61), (35, 61)], GRANITE, depth=(2, -2), seed=65)
    s.g("body")
    shell = _slab(s, [(20, 14), (50, 12), (52, 40), (44, 48), (26, 48), (18, 38)], GRANITE, chips=6, seed=66)
    # the open heart: a jagged split full of crystal
    split = s.poly([(30, 18), (38, 16), (44, 24), (42, 40), (34, 45), (28, 36), (31, 27)])
    s.fill(split, GEODE[0], glow=True)
    for x, b, t, w in ((33, 44, 31, 3), (38, 42, 26, 3.5), (34, 33, 21, 2.5), (40, 30, 19, 2.5), (31, 38, 30, 2)):
        _crystal(s, x, b, t, w)
    s.line(29, 18, 30, 30, GRANITE[0])
    s.g("head", 38, 12)
    _slab(s, [(32, 4), (44, 4), (45, 13), (33, 13)], GRANITE_D, depth=(2, -2), chips=1, seed=67)
    s.fill(s.rect(38, 7, 44, 9), GEODE[2], glow=True)
    s.px(42, 7, GEODE[3], glow=True)
    s.g("weapon", 18, 22)
    _slab(s, [(9, 14), (24, 13), (25, 27), (10, 28)], GRANITE, depth=(3, -3), chips=2, seed=68)
    s.g("hand_w", 16, 38, "weapon")
    _slab(s, [(9, 28), (22, 28), (23, 40), (10, 40)], GRANITE, chips=1, seed=69)
    _slab(s, [(8, 40), (24, 40), (25, 50), (9, 50)], GRANITE_D, chips=1, seed=70)
    for x, t in ((11, 43), (15, 41), (20, 44)):
        _crystal(s, x, 50, t - 4, 2)
    s.g("body")
    for x, t in ((12, 6), (17, 3), (22, 8)):
        _crystal(s, x, 14, t, 3)
    s.ink()
    s.shadow(36, 62.5, 22, 3.0)
    return s


def menhir(pose=None, pad=0):
    """Menhir Walker: one of the old standing stones of the Steppe, woken by a mad oath and walking on stubby stone
    legs. A tall lichened slab with a king's face carved into it, eyes of rune light, the oath-band round its middle
    burning. Where it stands, the ground will not move."""
    s = Sprite(52, 82, pose, pad)
    s.g("arm_f", 36, 36)
    _slab(s, [(34, 34), (41, 35), (42, 50), (35, 50)], GRANITE_D, depth=(2, -2), seed=71)
    leg(s, "f", (22, 64), (22, 69), (21, 74), 3.6, GRANITE_D, bias=-0.3)
    s.g("shin_f", 22, 69, "leg_f")
    _slab(s, [(16, 72), (27, 72), (27, 77), (15, 77)], GRANITE_D, depth=(2, -2), seed=72)
    s.g("leg_n", 30, 64)
    _slab(s, [(26, 63), (34, 63), (34, 70), (27, 70)], GRANITE_D, depth=(2, -2), seed=73)
    s.g("shin_n", 30, 70, "leg_n")
    _slab(s, [(24, 72), (37, 72), (38, 77), (23, 77)], GRANITE, depth=(2, -2), seed=74)
    s.g("body")
    _slab(s, [(14, 10), (22, 3), (34, 5), (38, 20), (37, 66), (13, 66)], GRANITE, depth=(4, -4), chips=8, seed=75)
    s.g("head", 26, 20)
    # the carved face of a forgotten king
    s.line(19, 16, 25, 15, GRANITE[0])
    s.line(28, 15, 34, 16, GRANITE[0])
    s.fill(s.rect(20, 18, 24, 20), (20, 26, 34))
    s.fill(s.rect(29, 18, 33, 20), (20, 26, 34))
    s.pxs([(22, 18), (31, 18), (21, 18), (30, 18)], RUNE[1], glow=True)
    s.line(26, 17, 27, 27, GRANITE[3])
    s.line(27, 17, 28, 27, GRANITE[1])
    s.line(22, 30, 32, 30, GRANITE[0])
    s.line(23, 31, 31, 31, GRANITE[3])
    for x in range(18, 36, 3):
        s.line(x, 6, x + 1, 10, GRANITE[3])                     # a carved crown
    s.g("body")
    s.part(s.rect(13, 40, 38, 44), IRON, flat=True)
    for x in range(15, 37, 4):
        s.line(x, 41, x + 2, 43, RUNE_GOLD[1], glow=True)
    s.pxs([(14, 12), (15, 13), (16, 12), (36, 24), (35, 25), (14, 55), (15, 56), (16, 57), (34, 60), (35, 61), (20, 50)], LICHEN[2])
    s.pxs([(15, 12), (36, 25), (15, 55), (35, 60)], LICHEN[1])
    s.g("weapon", 15, 38)
    _slab(s, [(8, 36), (16, 36), (16, 52), (9, 52)], GRANITE, depth=(2, -2), chips=1, seed=76)
    s.ink()
    s.shadow(26, 78.5, 15, 2.6)
    return s


STONE_HOST = {"oathbroken": oathbroken, "runebearer": runebearer, "quarry_hound": quarry_hound, "geode": geode,
              "menhir": menhir}


# ================================================================================================ THE HOLLOW
def _stars(s, box, n, seed, cols=VIOLET):
    """A few star pixels scattered over whatever is already drawn in box (rest coordinates)."""
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    k = 0
    for _ in range(n * 6):
        x, y = int(rng.integers(x0, x1)), int(rng.integers(y0, y1))
        tx, ty = (round(v) for v in s.fw(x, y))
        if 0 <= tx < s.w and 0 <= ty < s.h and s.a[ty, tx]:
            s.px(x, y, cols[1 + k % 2], glow=True)
            k += 1
            if k >= n:
                break


def lightdrinker(pose=None, pad=0):
    """Lightdrinker: a Veilwalker who spent all her light on starcraft and kept going. Tall, gaunt and grey, her hair
    and eyes bleached white, wrapped in a black shroud. She holds up a lantern that burns black, drinking the light
    out of everything near it."""
    s = Sprite(50, 64, pose, pad)
    s.g("cloak", 20, 22)
    s.part(s.poly([(18, 20), (25, 20), (24, 54), (17, 58), (11, 55), (13, 40)]), SHROUD, bias=-0.2)
    leg(s, "f", (22, 43), (21.5, 49), (21, 55), 1.8, VOIDSKIN_D, foot=(21.5, 57), foot_r=(2.6, 1.3), bias=-0.3)
    arm(s, "arm_f", "fore_f", (21, 24), (18, 31), (21, 36), 1.6, SHROUD, bias=-0.25, hand_r=1.5, hand_tones=STORMSKIN)
    s.g("body")
    s.part(s.poly([(18, 20), (28, 19), (30, 34), (31, 46), (17, 46), (18, 34)]), SHROUD)
    s.line(23, 22, 22, 45, SHROUD[2])
    s.line(27, 24, 28, 45, SHROUD[0])
    s.part(s.rect(18, 33, 30, 35), VOIDSKIN, flat=True)
    dither_out(s, 15, 33, 44, 47, keep=lambda x, y: x % 4)
    leg(s, "n", (26, 44), (27, 50), (26.5, 55), 1.9, VOIDSKIN, foot=(27.5, 57), foot_r=(2.8, 1.3))
    s.g("head", 26, 18)
    s.g("hair", 22, 9, "head")
    s.part(s.poly([(22, 7), (17, 10), (14, 26), (18, 23), (19, 30), (23, 20), (25, 12)]), [(150, 150, 160), (190, 190, 200), (225, 225, 232), (245, 245, 250)])
    s.g("head", 26, 18)
    s.part(s.ellipse(27, 12, 4.6, 5.6), STORMSKIN)
    s.part(s.poly([(21, 8), (26, 5), (31, 7), (31, 9), (24, 10), (22, 15)]), [(190, 190, 200), (225, 225, 232), (245, 245, 250)])
    s.pxs([(29, 11), (30, 11)], (255, 255, 255), glow=True)                     # white blind eyes
    s.px(31, 14, STORMSKIN[1])
    s.line(28, 16, 30, 16, VOIDSKIN_D[1])
    s.line(26, 14, 26, 17, STORMSKIN[1])                                         # hollow cheek
    # the black lantern held high
    arm(s, "weapon", "hand_w", (26, 23), (32, 20), (35, 13), 1.7, SHROUD, hand_r=1.6, hand_tones=STORMSKIN)
    s.g("hand_w", 32, 20, "weapon")
    s.line(35, 12, 36, 8, IRON[2])
    s.part(s.poly([(33, 8), (40, 8), (39, 2), (34, 2)]), IRON, flat=True)
    s.part(s.rect(33, 0, 41, 2), IRON, flat=True)
    s.fill(s.poly([(34, 7), (39, 7), (38, 3), (35, 3)]), (10, 4, 18))
    s.fill(s.poly([(35, 6), (38, 6), (36.5, 2)]), VIOLET[0], glow=True)
    s.px(36, 5, (4, 0, 8))
    s.ink()
    s.shadow(24, 58.5, 9, 2.0)
    return s


def gravecaller(pose=None, pad=0):
    """Gravecaller: a deathwalker of the Rift whose road of the dead now runs the wrong way. Hooded in black and grave-
    grey, face behind a bone mask, finger bones strung on his robe, raising a staff topped with a violet star caged in
    ribs. Where the horde falls, he calls it back up."""
    s = Sprite(54, 62, pose, pad)
    s.g("cloak", 20, 22)
    s.part(s.poly([(18, 20), (26, 20), (25, 52), (19, 55), (12, 54), (9, 48), (14, 34)]), SHROUD, bias=-0.15)
    s.g("weapon", 31, 25)
    s.g("hand_w", 35, 31, "weapon")
    s.part(s.capsule(36, 55, 41, 8, 1.1), BONE, flat=True)
    for dx in (-3, 0, 3):
        s.line(41, 7, 41 + dx, 2, BONE[2])
    s.line(38, 2, 44, 2, BONE[1])
    s.part(s.ellipse(41, 5, 2.6, 2.6), VIOLET, glow=True)
    s.px(41, 4, VIOLET[2], glow=True)
    s.line(38, 3, 38, 7, BONE[3])
    s.line(44, 3, 44, 7, BONE[3])
    leg(s, "f", (23, 42), (22.5, 47), (22, 52), 2.2, GRAVE, foot=(22, 54), foot_r=(3, 1.5), bias=-0.3)
    s.g("body")
    s.part(s.poly([(16, 21), (31, 20), (33, 34), (35, 47), (15, 47), (16, 34)]), GRAVE)
    s.part(s.poly([(22, 21), (31, 20), (33, 34), (35, 47), (26, 47)]), SHROUD, edge=False)
    s.line(22, 22, 25, 46, SHROUD[3])
    for x, y in ((19, 30), (21, 33), (23, 36), (19, 38)):
        s.line(x, y, x, y + 2, BONE[3])                     # finger bones strung on the robe
    s.part(s.rect(16, 35, 34, 37), LEATHER, flat=True)
    dither_out(s, 14, 36, 45, 48, keep=lambda x, y: (x * 5 + y) % 4)
    leg(s, "n", (29, 43), (30, 48), (29.5, 52), 2.3, GRAVE, foot=(31, 54), foot_r=(3.2, 1.5))
    s.g("head", 28, 20)
    s.part(s.ellipse(28, 13, 7.8, 8.2) | s.poly([(20, 14), (36, 12), (37, 22), (20, 23)]), SHROUD)
    s.fill(s.ellipse(31, 15, 5.5, 6.5), (10, 6, 14))                              # the dark of the hood
    s.part(s.poly([(29, 11), (35, 10), (37, 14), (36, 19), (33, 22), (30, 20), (29, 15)]), BONE, bias=-0.05)   # skull mask
    s.fill(s.rect(30, 13, 33, 16), (16, 6, 24))
    s.fill(s.rect(34, 13, 36, 16), (16, 6, 24))
    s.pxs([(31, 14), (35, 14)], VIOLET[2], glow=True)
    s.pxs([(31, 15), (35, 15)], VIOLET[1], glow=True)
    s.px(34, 17, (16, 6, 24))
    for x in (31, 32, 33, 34):
        s.px(x, 19 + (x % 2), BONE[0])
    s.line(30, 12, 33, 11, BONE[0])
    s.part(s.poly([(22, 6), (27, 2), (24, 9)]), SHROUD)                            # hood point
    arm(s, "weapon", "hand_w", (31, 25), (35, 31), (38, 30), 2.3, SHROUD, hand_r=1.9, hand_tones=BONE)
    arm(s, "arm_n", "fore_n", (21, 25), (19, 32), (24, 34), 2.2, SHROUD, hand_r=1.6, hand_tones=BONE)
    s.ink()
    s.shadow(26, 55.5, 12, 2.2)
    return s


def umbral_stalker(pose=None, pad=0):
    """Umbral Stalker: a great cat made of the dark between stars, long and low, its pelt black-violet and scattered
    with tiny stars. Violet eyes, a long whip of a tail, claws out. It is not there until it is close."""
    s = Sprite(70, 44, pose, pad)
    s.g("tail", 16, 20)
    s.g("tail2", 8, 14, "tail")
    s.part(s.capsule(8, 14, 2, 5, 1.6, 1.0), STALK, edge=False)
    s.part(s.ellipse(2, 4, 2, 2), VIOLET, glow=True)
    s.g("tail", 16, 20)
    s.part(s.capsule(16, 20, 8, 14, 2.2, 1.6), STALK, edge=False)
    leg(s, "f", (48, 25), (52, 31), (50, 37), 2.6, STALK, foot=(52, 38.5), foot_r=(3.2, 1.4), bias=-0.35)
    leg(s, "f2", (20, 24), (16, 30), (19, 36), 3.0, STALK, foot=(21, 38), foot_r=(3.2, 1.4), bias=-0.35)
    s.g("body")
    s.part(s.capsule(18, 22, 50, 21, 8, 7), STALK)
    s.part(s.capsule(22, 27, 46, 26, 3, 3) & s.capsule(18, 22, 50, 21, 8, 7), VOIDSKIN_D, edge=False)
    s.line(22, 16, 46, 15, STALK[4])
    _stars(s, (14, 12, 52, 30), 10, 81)
    s.g("neck", 50, 20)
    s.g("head", 56, 18, "neck")
    s.g("jaw", 58, 22, "head")
    s.part(s.poly([(56, 21), (65, 22), (63, 24), (57, 24)]), STALK)
    s.pxs([(59, 22), (61, 22), (63, 22)], WHITE)
    s.g("head", 56, 18, "neck")
    s.part(s.ellipse(57, 17, 6.4, 5.8), STALK)
    s.part(s.ellipse(63, 19.5, 3.4, 2.8), STALK)
    s.part(s.poly([(52, 14), (53, 8), (57, 12)]), STALK)
    s.part(s.poly([(56, 12), (59, 7), (60, 13)]), STALK)
    s.px(54, 11, VIOLET[0])
    s.px(58, 10, VIOLET[0])
    s.fill(s.poly([(58, 15), (62, 15), (61, 17), (58, 16)]), VIOLET[1], glow=True)
    s.px(61, 15, VIOLET[2], glow=True)
    s.px(60, 16, (10, 0, 20))
    s.pxs([(64, 22), (65, 22)], WHITE)
    s.px(66, 18, VIOLET[0])
    s.line(62, 19, 66, 18, STALK[0])
    leg(s, "n2", (24, 25), (19, 31), (23, 37), 3.4, STALK, foot=(25, 39), foot_r=(3.6, 1.5))
    leg(s, "n", (46, 26), (50, 32), (48, 37), 3.0, STALK, foot=(51, 39), foot_r=(3.6, 1.5))
    s.g("shin_n", 50, 32, "leg_n")
    s.pxs([(54, 39), (55, 38)], WHITE)
    s.ink((40, 18, 60))
    s.shadow(35, 40.5, 22, 2.0)
    return s


def voidmaw(pose=None, pad=0):
    """Voidmaw: a thing grown in the dark at the bottom of the Rift: a bloated, hunched body that is nearly all
    mouth, a ring of needle teeth round a hole full of stars. Short thick legs, little clawed arms, a crown of
    eyes. It feeds on what dies near it."""
    s = Sprite(64, 58, pose, pad)
    arm(s, "arm_f", "fore_f", (40, 32), (45, 36), (48, 33), 2.2, VOIDSKIN_D, bias=-0.25, hand_r=1.8)
    leg(s, "f", (26, 42), (24, 47), (25, 52), 4.0, VOIDSKIN_D, foot=(25, 54), foot_r=(5, 2), bias=-0.3)
    s.g("body")
    body = s.ellipse(32, 30, 18, 17)
    s.part(body, VOIDSKIN)
    s.part(s.ellipse(32, 40, 13, 6) & body, VOIDSKIN_D, edge=False)
    # the maw: a ring of teeth around a hole of stars, facing right and up
    s.g("jaw", 40, 28)
    hole = s.ellipse(41, 28, 9, 11)
    s.fill(hole, (8, 4, 16))
    s.fill(s.ellipse(43, 28, 5.5, 7.5), (20, 6, 40), glow=True)
    for i in range(14):
        a = i / 14 * 2 * math.pi
        x0, y0 = 41 + math.cos(a) * 9.5, 28 + math.sin(a) * 11.5
        x1, y1 = 41 + math.cos(a) * 6.5, 28 + math.sin(a) * 8
        s.line(x0, y0, x1, y1, BONE[3 if i % 2 else 2])
    s.pxs([(44, 25), (42, 31), (45, 30), (43, 27)], VIOLET[1 + 0], glow=True)
    s.pxs([(41, 24), (46, 28)], VIOLET[2], glow=True)
    s.g("body")
    _stars(s, (14, 14, 32, 42), 9, 91)
    # a crown of eyes along the top
    for x, y in ((22, 16), (27, 13), (33, 12), (39, 14)):
        s.part(s.ellipse(x, y, 2, 1.8), [(30, 10, 40), (60, 30, 80)])
        s.px(x, y, (255, 230, 120), glow=True)
    s.pxs([(18, 20), (20, 18), (24, 14)], BONE[2])
    leg(s, "n", (35, 43), (37, 48), (36, 52), 4.2, VOIDSKIN, foot=(38, 54), foot_r=(5.4, 2.1))
    arm(s, "weapon", "hand_w", (30, 34), (36, 40), (41, 41), 2.4, VOIDSKIN, hand_r=2.0)
    s.g("hand_w", 36, 40, "weapon")
    s.pxs([(43, 40), (43, 42), (42, 43)], WHITE)
    s.ink((30, 14, 40))
    s.shadow(31, 55, 18, 2.6)
    return s


def wailing_widow(pose=None, pad=0):
    """Wailing Widow: a widow of the Rift who would not let her husband walk the road of the dead, and followed him
    down it. She drifts in a torn grey wedding veil, long black hair streaming, hands clawed at her chest, mouth torn
    open in a scream that never ends. When she is struck down the scream breaks loose."""
    s = Sprite(50, 62, pose, pad)
    s.g("hair", 22, 12)
    s.part(s.poly([(22, 9), (15, 11), (7, 22), (3, 34), (9, 31), (8, 40), (14, 30), (19, 22)]), [(14, 10, 18), (30, 24, 38), (48, 40, 58)])
    s.g("tail", 24, 34)
    s.part(s.poly([(14, 30), (32, 30), (33, 42), (29, 50), (22, 56), (14, 54), (10, 47), (13, 40)]), WIDOW_D)
    for x, y in ((11, 55), (8, 52), (16, 58), (21, 59), (6, 56), (26, 57)):
        s.px(x, y, WIDOW[2])
    dither_out(s, 6, 36, 44, 60, keep=lambda x, y: ((x + y) % 2 == 0 and y < 47 + (x % 5)) or (x * 3 + y) % 7 == 0)
    s.g("body")
    s.part(s.poly([(16, 19), (30, 18), (33, 30), (31, 40), (16, 40), (14, 30)]), WIDOW)
    s.line(21, 22, 20, 39, WIDOW[1])
    s.line(27, 22, 28, 39, WIDOW[1])
    s.part(s.rect(17, 25, 31, 27), WIDOW_D, flat=True)
    s.g("head", 26, 18)
    s.part(s.ellipse(27, 12, 5.4, 6.2), [(150, 146, 160), (190, 186, 198), (220, 216, 226), (240, 238, 244)])
    s.part(s.poly([(20, 6), (28, 3), (33, 7), (30, 9), (24, 9), (21, 18)]), [(14, 10, 18), (30, 24, 38), (48, 40, 58)])
    s.fill(s.rect(28, 9, 30, 11), (20, 10, 30))
    s.fill(s.rect(31, 9, 33, 11), (20, 10, 30))
    s.pxs([(29, 10), (32, 10)], VIOLET[2], glow=True)
    s.fill(s.ellipse(30.5, 15.5, 1.8, 2.8), (12, 4, 18))                      # the scream
    s.line(28, 9, 28, 13, (110, 104, 122))
    s.g("plume", 22, 6, "head")
    s.part(s.poly([(22, 5), (14, 3), (8, 12), (12, 22), (16, 14), (21, 10)]), WIDOW, bias=-0.1)     # veil streaming back
    dither_out(s, 6, 20, 14, 24, keep=lambda x, y: (x + y) % 3)
    s.g("body")
    arm(s, "weapon", "hand_w", (26, 22), (31, 28), (27, 31), 1.5, WIDOW, hand_r=1.4, hand_tones=WIDOW_D)
    s.g("hand_w", 31, 28, "weapon")
    for dx, dy in ((-2, -1), (-2, 1), (-1, 2)):
        s.line(27, 31, 27 + dx, 31 + dy, WIDOW_D[1])
    arm(s, "arm_n", "fore_n", (19, 22), (20, 29), (24, 30), 1.4, WIDOW, hand_r=1.3, hand_tones=WIDOW_D)
    s.ink((50, 40, 70))
    s.opacity = 240
    s.shadow(23, 59, 9, 1.8)
    return s


HOLLOW = {"lightdrinker": lightdrinker, "gravecaller": gravecaller, "umbral_stalker": umbral_stalker, "voidmaw": voidmaw,
          "wailing_widow": wailing_widow}


# ================================================================================================ THE FLAME
def _cracks(s, pts, col=MAGMA[2], glow=True):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s.line(x0, y0, x1, y1, col, glow=glow)


def cinderhound(pose=None, pad=0):
    """Cinderhound: a hunting dog of the Ember Throne that lay down in a forge and got up again. Lean black cinder
    cracked all over with magma, a mane of flame down its neck, coal eyes, a burning tongue. Fire feeds it."""
    s = Sprite(66, 46, pose, pad)
    s.g("tail", 14, 20)
    s.part(s.capsule(14, 20, 5, 12, 2.2, 1.2), CINDER, edge=False)
    s.fill(s.poly([(6, 12), (1, 5), (4, 4), (8, 9)]), MAGMA[2], glow=True)
    leg(s, "f", (46, 26), (50, 32), (48, 38), 2.4, CINDER, foot=(50, 39.5), foot_r=(3, 1.3), bias=-0.35)
    leg(s, "f2", (18, 25), (14, 31), (17, 38), 2.6, CINDER, foot=(19, 39.5), foot_r=(3, 1.3), bias=-0.35)
    s.g("body")
    s.part(s.capsule(17, 22, 47, 20, 7, 7.5), CINDER)
    s.part(s.capsule(20, 27, 44, 26, 2.5, 3) & s.capsule(17, 22, 47, 20, 7, 7.5), CINDER, bias=-0.3, edge=False)
    for i, x in enumerate(range(24, 44, 5)):                              # ribs glowing through
        s.line(x, 17 + i % 2, x + 1, 26, MAGMA[1], glow=True)
    _cracks(s, [(18, 18), (21, 21), (20, 25)])
    s.g("neck", 47, 19)
    s.g("head", 54, 16, "neck")
    s.g("jaw", 56, 21, "head")
    s.part(s.poly([(54, 20), (65, 21), (63, 24), (55, 24)]), CINDER)
    s.fill(s.poly([(57, 21), (63, 22), (60, 25), (57, 26)]), MAGMA[2], glow=True)    # burning tongue
    s.g("head", 54, 16, "neck")
    s.part(s.ellipse(55, 15, 6.4, 5.4), CINDER)
    s.part(s.poly([(57, 13), (66, 16), (65, 20), (56, 20)]), CINDER)
    s.part(s.poly([(51, 11), (54, 3), (56, 11)]), CINDER)
    s.fill(s.rect(57, 13, 60, 15), MAGMA[3], glow=True)
    s.px(59, 13, (255, 255, 230), glow=True)
    s.pxs([(58, 20), (60, 20), (62, 20), (64, 20)], WHITE)
    _cracks(s, [(52, 15), (55, 18)])
    # the flame mane down the neck and back
    s.g("plume", 46, 12, "neck")
    for i, (x, h) in enumerate(((52, 9), (48, 10), (44, 8), (40, 7), (36, 6), (31, 5))):
        s.fill(s.poly([(x - 3, 14 + i * 0.3), (x - 2, 14 - h), (x + 2, 14 + i * 0.3)]), MAGMA[1], glow=True)
        s.fill(s.poly([(x - 2, 14), (x - 1.5, 15 - h * 0.6), (x + 1, 14)]), MAGMA[2], glow=True)
    leg(s, "n2", (22, 26), (17, 32), (21, 38), 3.0, CINDER, foot=(23, 40), foot_r=(3.4, 1.4))
    leg(s, "n", (44, 27), (48, 33), (46, 38), 2.8, CINDER, foot=(49, 40), foot_r=(3.4, 1.4))
    s.g("shin_n", 48, 33, "leg_n")
    _cracks(s, [(47, 34), (47, 37)])
    s.ink()
    s.shadow(34, 41.5, 22, 2.0)
    return s


def slagwalker(pose=None, pad=0):
    """Slagwalker: a smith-lord who walked into his own furnace to become a weapon. Now a hulk in plates of black
    slag that drip as he moves, molten metal glowing in every seam, his face a mask fused shut over two white-hot
    slits. Each blow knocks a plate loose."""
    s = Sprite(62, 62, pose, pad)
    arm(s, "arm_f", "fore_f", (42, 24), (46, 31), (45, 38), 3.6, SLAG, bias=-0.3, hand_r=3.4)
    leg(s, "f", (26, 44), (25, 49), (25, 54), 4.0, SLAG, foot=(25, 56), foot_r=(4.6, 2.0), bias=-0.3)
    s.g("body")
    s.part(s.ellipse(32, 31, 13, 13), SLAG)
    s.part(s.poly([(21, 38), (43, 38), (44, 48), (20, 48)]), SLAG)
    # molten seams between the plates
    _cracks(s, [(22, 26), (28, 29), (36, 27), (42, 30)])
    _cracks(s, [(26, 34), (32, 37), (40, 35)])
    _cracks(s, [(32, 37), (31, 46)])
    _cracks(s, [(24, 43), (30, 44)], MAGMA[1])
    s.pxs([(28, 30), (36, 28), (32, 38)], MAGMA[3], glow=True)
    for x, y in ((24, 48), (30, 49), (38, 48)):                             # drips
        s.line(x, y, x, y + 2, MAGMA[2], glow=True)
    leg(s, "n", (36, 45), (37, 50), (36, 54), 4.2, SLAG, foot=(38, 56), foot_r=(5, 2.1))
    s.g("shin_n", 37, 50, "leg_n")
    _cracks(s, [(36, 49), (38, 53)])
    s.g("head", 34, 19)
    s.part(s.ellipse(36, 14, 7, 7), SLAG)
    s.part(s.rect(30, 6, 43, 10), SLAG, flat=True, bias=0.2)
    s.fill(s.rect(36, 13, 43, 14), MAGMA[3], glow=True)
    s.pxs([(38, 13), (41, 13)], (255, 255, 240), glow=True)
    _cracks(s, [(34, 17), (37, 19), (41, 18)], MAGMA[1])
    s.fill(s.poly([(33, 5), (35, 0), (37, 5)]), SLAG[1])
    s.fill(s.poly([(38, 5), (40, 1), (42, 6)]), SLAG[1])
    # near arm: a huge slag fist dripping
    arm(s, "weapon", "hand_w", (24, 25), (26, 34), (31, 39), 4.2, SLAG, hand_r=4.6)
    s.g("weapon", 24, 25)
    s.part(s.ellipse(23, 22, 6.5, 5.5), SLAG, bias=0.1)
    _cracks(s, [(19, 22), (23, 24), (27, 22)])
    s.g("hand_w", 26, 34, "weapon")
    _cracks(s, [(28, 37), (32, 40), (34, 38)])
    s.line(31, 44, 31, 46, MAGMA[2], glow=True)
    s.ink()
    s.shadow(31, 58, 17, 2.6)
    return s


def smoke_wraith(pose=None, pad=0):
    """Smoke Wraith: the smoke of a burned town that would not blow away. A tall rolling column of soot with an
    ember heart showing through, two coal eyes in a hood of smoke, long arms that come apart at the fingers. Most
    blows go straight through it."""
    s = Sprite(52, 64, pose, pad)
    s.g("tail", 24, 36)
    s.part(s.poly([(15, 30), (32, 30), (35, 42), (31, 52), (24, 58), (15, 57), (11, 50), (13, 42)]), SMOKE, bias=-0.2)
    for x, y in ((12, 58), (8, 55), (18, 60), (24, 61), (6, 59), (28, 59), (14, 62)):
        s.px(x, y, SMOKE[2 + (x + y) % 2])
    dither_out(s, 6, 37, 44, 62, keep=lambda x, y: ((x + y) % 2 == 0 and y < 48 + (x % 5)) or (x * 7 + y) % 4 == 0)
    arm(s, "arm_f", "fore_f", (27, 24), (33, 30), (40, 28), 2.0, SMOKE, bias=-0.3)
    dither_out(s, 36, 44, 24, 33, keep=lambda x, y: (x + y) % 2)
    s.g("body")
    # rolling billows of smoke for a body
    for cx, cy, r in ((22, 34, 8), (28, 29, 7), (20, 24, 7), (27, 20, 6), (24, 40, 7)):
        s.part(s.ellipse(cx, cy, r, r * 0.85), SMOKE)
    s.fill(s.ellipse(25, 30, 3.2, 3.6), MAGMA[1], glow=True)                       # the ember heart
    s.fill(s.ellipse(25, 30, 1.8, 2.0), MAGMA[3], glow=True)
    s.pxs([(23, 26), (28, 33), (21, 33)], MAGMA[0], glow=True)
    s.g("head", 28, 18)
    s.g("plume", 24, 6, "head")
    for cx, cy, r in ((22, 6, 4), (17, 3, 3), (13, 5, 2.4)):
        s.part(s.ellipse(cx, cy, r, r * 0.8), SMOKE, bias=0.1)
    s.g("head", 28, 18)
    s.part(s.ellipse(29, 12, 7, 7.2), SMOKE)
    s.fill(s.ellipse(32, 13, 4, 4.8), (24, 18, 18))
    s.pxs([(31, 12), (34, 12)], MAGMA[3], glow=True)
    s.pxs([(31, 13), (34, 13)], MAGMA[1], glow=True)
    arm(s, "weapon", "hand_w", (24, 24), (32, 31), (41, 33), 2.4, SMOKE)
    s.g("hand_w", 32, 31, "weapon")
    for dx, dy in ((4, -2), (5, 0), (4, 2)):
        s.line(41, 33, 41 + dx, 33 + dy, SMOKE[1])
    dither_out(s, 38, 47, 29, 37, keep=lambda x, y: (x * 3 + y) % 3)
    s.ink((40, 32, 30))
    s.opacity = 230
    s.shadow(24, 61, 9, 1.8)
    return s


def glass_singer(pose=None, pad=0):
    """Glass-Singer: an old Kindler who sang sand into glass until she had no warmth left. Gaunt in a scorched red
    robe, her bare arms cold blue and covered in glowing ember-rune tattoos, her face behind a cracked glass mask.
    Shards of glass hang in the air round her raised hand, ringing."""
    s = Sprite(52, 60, pose, pad)
    s.g("cloak", 20, 22)
    s.part(s.poly([(18, 21), (25, 21), (24, 50), (18, 54), (12, 52), (11, 44), (15, 32)]), ROBE_RED, bias=-0.2)
    leg(s, "f", (23, 42), (22.5, 47), (22, 52), 2.0, ROBE_RED, foot=(22, 54), foot_r=(2.8, 1.4), foot_tones=LEATHER, bias=-0.3)
    arm(s, "arm_f", "fore_f", (21, 24), (18, 31), (21, 36), 1.6, STORMSKIN, bias=-0.2, hand_r=1.5)
    s.g("body")
    s.part(s.poly([(17, 21), (29, 20), (31, 34), (33, 47), (16, 47), (17, 34)]), ROBE_RED)
    s.line(23, 23, 21, 46, ROBE_RED[1])
    s.line(28, 24, 29, 46, ROBE_RED[4])
    s.part(s.rect(17, 33, 31, 35), BRASS, flat=True)
    for x, y in ((19, 40), (24, 42), (29, 39), (26, 45)):
        s.px(x, y, CINDER[1])                                                 # scorch marks
    leg(s, "n", (28, 43), (29, 48), (28.5, 52), 2.1, ROBE_RED, foot=(30, 54), foot_r=(3, 1.4), foot_tones=LEATHER)
    s.g("head", 27, 19)
    s.g("hair", 23, 12, "head")
    s.part(s.poly([(23, 10), (17, 13), (16, 25), (20, 22), (22, 27), (25, 16)]), [(60, 56, 62), (100, 96, 104), (140, 136, 144)])
    s.g("head", 27, 19)
    s.part(s.ellipse(28, 13, 4.8, 5.6), STORMSKIN)
    s.part(s.poly([(27, 9), (33, 9), (34, 17), (31, 19), (27, 17)]), GLASS, flat=True, bias=0.1)   # glass mask
    s.line(29, 10, 32, 15, (240, 255, 255))
    s.line(30, 12, 28, 16, GLASS[0])
    s.pxs([(30, 12), (32, 12)], MAGMA[2], glow=True)
    s.part(s.poly([(22, 9), (27, 6), (32, 8), (29, 10), (24, 12)]), [(60, 56, 62), (100, 96, 104), (140, 136, 144)])
    # raised near arm, tattooed, shards hanging round the hand
    arm(s, "weapon", "hand_w", (26, 24), (33, 22), (37, 15), 1.7, STORMSKIN, hand_r=1.6)
    s.g("weapon", 26, 24)
    s.pxs([(28, 23), (30, 23), (31, 22)], MAGMA[2], glow=True)
    s.g("hand_w", 33, 22, "weapon")
    s.pxs([(34, 20), (35, 18), (36, 17)], MAGMA[2], glow=True)
    s.g("aura", 37, 13)
    for x, y, h in ((42, 9, 4), (33, 7, 3), (44, 16, 3), (39, 4, 3), (31, 12, 2)):
        s.fill(s.poly([(x - 1, y + h), (x, y - h), (x + 1.5, y + h - 1)]), GLASS[3], glow=True)
        s.px(x, y - h + 1, (250, 255, 255), glow=True)
    s.g("body")
    s.part(s.capsule(16, 25, 15, 30, 1.6), STORMSKIN)
    s.pxs([(16, 26), (15, 28)], MAGMA[2], glow=True)
    s.ink()
    s.shadow(25, 55, 10, 2.0)
    return s


def brass_juggernaut(pose=None, pad=0):
    """Brass Juggernaut: a siege engine of the smith-lords that woke up hungry. A walking furnace of riveted brass on
    iron legs, a fire-mouth roaring in its belly, a chimney belching smoke, pistons at the knees and a battering ram
    for an arm. Slow to start, terrible once it gets going."""
    s = Sprite(72, 74, pose, pad)
    s.g("arm_f", 50, 28)
    s.part(s.capsule(50, 28, 55, 36, 3.2), IRON, bias=-0.25)
    s.g("fore_f", 55, 36, "arm_f")
    s.part(s.capsule(55, 36, 55, 45, 3.0), IRON, bias=-0.25, edge=False)
    s.part(s.ellipse(55, 47, 4, 3.5), BRASS_D, bias=-0.2)
    leg(s, "f", (30, 52), (28, 59), (29, 65), 3.6, IRON, foot=(29, 67), foot_r=(6, 2.2), foot_tones=BRASS_D, bias=-0.3)
    s.g("body")
    # chimney and smoke
    s.part(s.rect(20, 4, 27, 18), IRON, flat=True)
    s.part(s.rect(19, 3, 28, 6), BRASS, flat=True)
    for cx, cy, r in ((22, 1, 2.6), (18, -1, 2.0)):
        s.fill(s.ellipse(cx, cy + 2, r, r * 0.8), SMOKE[2])
    # the boiler body
    boiler = s.ellipse(37, 34, 19, 18)
    s.part(boiler, BRASS)
    for y in (22, 34, 46):
        s.line(19, y, 55, y, BRASS_D[1])
        for x in range(21, 55, 4):
            tx, ty = (round(v) for v in s.fw(x, y + 1))
            if 0 <= tx < s.w and 0 <= ty < s.h and boiler[ty, tx]:
                s.px(x, y + 1, BRASS[4])
    # the fire-mouth with a grate
    s.fill(s.ellipse(44, 37, 7, 6), (30, 12, 6))
    s.fill(s.ellipse(44, 38, 5.5, 4.4), MAGMA[1], glow=True)
    s.fill(s.ellipse(44, 39, 3.5, 2.6), MAGMA[3], glow=True)
    for x in (41, 44, 47):
        s.line(x, 32, x, 43, IRON[1])
    s.part(s.rect(36, 30, 52, 32), IRON, flat=True)
    # a riveted helm-head with a glowing visor slit
    s.g("head", 46, 18)
    s.part(s.ellipse(47, 15, 7, 6), IRON)
    s.part(s.rect(40, 8, 55, 12), BRASS, flat=True, bias=0.2)
    s.fill(s.rect(46, 14, 54, 16), MAGMA[2], glow=True)
    s.px(51, 14, MAGMA[3], glow=True)
    s.pxs([(42, 10), (46, 10), (50, 10), (54, 10)], BRASS[0])
    leg(s, "n", (42, 53), (44, 60), (43, 65), 4.0, IRON, foot=(45, 67), foot_r=(6.4, 2.3), foot_tones=BRASS_D)
    s.g("leg_n", 42, 53)
    s.part(s.rect(40, 55, 47, 58), BRASS, flat=True)
    s.g("shin_n", 44, 60, "leg_n")
    s.part(s.ellipse(44, 60, 3.2, 3.2), BRASS)                              # knee piston
    # near arm: a brass battering ram
    s.g("weapon", 22, 30)
    s.part(s.capsule(22, 30, 20, 40, 3.8), IRON)
    s.g("hand_w", 20, 40, "weapon")
    s.part(s.capsule(20, 40, 26, 47, 3.6), IRON, edge=False)
    s.part(s.poly([(22, 44), (34, 44), (36, 53), (24, 53)]), BRASS, flat=True)
    s.part(s.rect(33, 43, 38, 54), BRASS_D, flat=True)
    s.pxs([(25, 46), (25, 51), (31, 46), (31, 51)], BRASS[4])
    s.g("weapon", 22, 30)
    s.part(s.ellipse(21, 27, 6.5, 5.5), BRASS)
    s.pxs([(17, 26), (21, 24), (25, 26)], BRASS[4])
    s.ink()
    s.shadow(37, 69.5, 22, 3.0)
    return s


FLAME = {"cinderhound": cinderhound, "slagwalker": slagwalker, "smoke_wraith": smoke_wraith, "glass_singer": glass_singer,
         "brass_juggernaut": brass_juggernaut}


# ================================================================================================ THE SKY
def _bolt(s, pts, glow=True):
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        s.line(x0, y0, x1, y1, BOLT[1], glow=glow)
    for x, y in pts[1:-1]:
        s.px(x, y, BOLT[2], glow=glow)


def gale_harpy(pose=None, pad=0):
    """Gale Harpy: a sky-rider's hunting bird crossed with the rider, the way the mad storm likes things. A grey
    woman's body, wild white hair, a screaming face, and huge storm-grey wings; bird legs ending in black talons."""
    s = Sprite(66, 62, pose, pad)
    s.g("wing_f", 30, 24)
    s.part(s.poly([(30, 24), (38, 8), (52, 2), (48, 10), (56, 12), (46, 18), (52, 24), (40, 26)]), FEATHER, flat=True, bias=-0.45)
    leg(s, "f", (27, 38), (31, 43), (27, 48), 1.8, FEATHER, bias=-0.3)
    s.g("shin_f", 31, 43, "leg_f")
    for dx in (-2, 1, 3):
        s.line(27, 48, 27 + dx, 51, DARK)
    s.g("wing", 27, 24)
    wing = s.poly([(27, 24), (22, 10), (14, 0), (14, 6), (6, 3), (11, 10), (3, 11), (11, 16), (6, 20), (16, 21), (21, 27)])
    s.part(wing, FEATHER, flat=True, bias=0.15)
    for (x0, y0), (x1, y1) in (((22, 10), (14, 0)), ((21, 13), (6, 3)), ((20, 16), (3, 11)), ((20, 20), (6, 20))):
        s.line(x0, y0, x1, y1, FEATHER[0])
    s.part(s.capsule(27, 24, 22, 10, 2.0, 1.3), STORMSKIN)
    s.g("body")
    s.part(s.ellipse(29, 30, 6.5, 9), STORMSKIN)
    s.part(s.poly([(23, 34), (35, 34), (34, 41), (24, 41)]), FEATHER)               # feathered hips
    for x in (25, 28, 31):
        s.line(x, 36, x + 1, 41, FEATHER[1])
    leg(s, "n", (31, 39), (35, 44), (31, 49), 2.0, FEATHER)
    s.g("shin_n", 35, 44, "leg_n")
    for dx in (-2, 1, 4):
        s.line(31, 49, 31 + dx, 52, DARK)
    s.g("head", 31, 21)
    s.g("hair", 30, 12, "head")
    s.part(s.poly([(31, 10), (25, 7), (19, 9), (24, 12), (19, 16), (26, 16), (24, 21), (30, 18)]), [(16, 14, 22), (34, 30, 44), (56, 50, 70)])
    s.g("head", 31, 21)
    s.part(s.ellipse(35, 15, 4.4, 5.0), STORMSKIN)
    s.part(s.poly([(30, 10), (35, 8), (40, 11), (34, 12), (31, 16)]), [(16, 14, 22), (34, 30, 44), (56, 50, 70)])
    s.fill(s.rect(36, 13, 39, 15), (24, 22, 34))
    s.pxs([(37, 13), (38, 13)], BOLT[2], glow=True)
    s.fill(s.ellipse(38, 18, 1.4, 1.8), (20, 16, 28))                              # screaming mouth
    s.px(40, 16, STORMSKIN[1])
    s.ink()
    s.shadow(30, 54.5, 12, 2.0)
    return s


def voiceless(pose=None, pad=0):
    """Voiceless: a Galeborn stormsinger who sang until her voice ran out, and kept singing anyway. Thin in a
    storm-blue robe, her throat bound in grey cloth, her mouth stitched shut. Static crawls over her hands as she
    conducts a song no one can hear, and where she walks the towers' arts fall silent too."""
    s = Sprite(52, 60, pose, pad)
    s.g("cloak", 20, 22)
    s.part(s.poly([(18, 21), (25, 21), (24, 50), (18, 53), (12, 52), (11, 44), (15, 32)]), CLOTH_BLUE, bias=-0.2)
    leg(s, "f", (23, 42), (22.5, 47), (22, 52), 2.0, CLOTH_BLUE, foot=(22, 54), foot_r=(2.8, 1.4), foot_tones=LEATHER, bias=-0.3)
    arm(s, "arm_f", "fore_f", (21, 24), (16, 27), (13, 22), 1.5, STORMSKIN, bias=-0.2, hand_r=1.5)
    s.g("fore_f", 16, 27, "arm_f")
    _bolt(s, [(13, 21), (11, 18), (13, 16), (11, 13)])
    s.g("body")
    s.part(s.poly([(17, 21), (29, 20), (31, 34), (33, 47), (16, 47), (17, 34)]), CLOTH_BLUE)
    s.line(23, 23, 21, 46, CLOTH_BLUE[1])
    s.line(28, 24, 29, 46, CLOTH_BLUE[4])
    s.part(s.rect(17, 33, 31, 35), STEEL, flat=True)
    for x, y in ((20, 38), (26, 42)):
        s.px(x, y, BOLT[1], glow=True)
    leg(s, "n", (28, 43), (29, 48), (28.5, 52), 2.1, CLOTH_BLUE, foot=(30, 54), foot_r=(3, 1.4), foot_tones=LEATHER)
    s.g("head", 27, 19)
    s.g("hair", 23, 11, "head")
    s.part(s.poly([(23, 9), (15, 11), (10, 18), (16, 18), (13, 25), (21, 20), (24, 22)]), [(30, 34, 50), (50, 56, 76), (74, 80, 104)])
    s.g("head", 27, 19)
    s.part(s.ellipse(28, 13, 4.6, 5.4), STORMSKIN)
    s.part(s.poly([(22, 9), (27, 6), (32, 8), (29, 10), (24, 13)]), [(30, 34, 50), (50, 56, 76), (74, 80, 104)])
    s.pxs([(30, 12), (31, 12)], BOLT[2], glow=True)
    s.px(30, 13, BOLT[0])
    s.line(29, 16, 32, 16, (60, 40, 50))                                           # stitched mouth
    s.pxs([(29, 15), (31, 15), (30, 17), (32, 17)], (120, 100, 100))
    s.part(s.rect(24, 18, 32, 21), [(90, 92, 96), (130, 132, 136), (160, 162, 166)], flat=True)   # bound throat
    s.line(25, 19, 31, 19, (70, 72, 76))
    # the near hand raised, conducting, static crawling over it
    arm(s, "weapon", "hand_w", (26, 24), (33, 26), (38, 21), 1.6, STORMSKIN, hand_r=1.5)
    s.g("hand_w", 33, 26, "weapon")
    _bolt(s, [(38, 20), (40, 16), (38, 14), (41, 10)])
    _bolt(s, [(39, 22), (43, 21), (42, 24), (46, 24)])
    s.ink()
    s.shadow(25, 55, 10, 2.0)
    return s


def stormrider(pose=None, pad=0):
    """Stormrider: one of Aurath's sky-riders, dead in the saddle, still riding. A gaunt black storm-horse with a mane
    of lightning and white eyes, and on its back a rider in rotted blue riding leathers, face hidden by a hood, lance
    couched. Every blow drives it faster."""
    s = Sprite(74, 66, pose, pad)
    s.g("tail", 16, 34)
    s.part(s.poly([(17, 32), (10, 34), (4, 44), (6, 48), (11, 42), (15, 38)]), BOLT, flat=True, glow=True)
    leg(s, "f", (52, 42), (56, 49), (53, 56), 2.4, HORSE, foot=(54, 58), foot_r=(2.8, 1.5), bias=-0.35)
    leg(s, "f2", (22, 42), (18, 49), (21, 56), 2.6, HORSE, foot=(22, 58), foot_r=(2.8, 1.5), bias=-0.35)
    s.g("body")
    s.part(s.capsule(20, 38, 52, 37, 8, 8.5), HORSE)
    s.part(s.capsule(24, 44, 48, 43, 3, 3) & s.capsule(20, 38, 52, 37, 8, 8.5), HORSE, bias=-0.3, edge=False)
    for x in (30, 34, 38):
        s.line(x, 35, x + 1, 43, HORSE[1])                                        # ribs showing
    # saddle cloth
    s.part(s.poly([(28, 30), (42, 30), (43, 41), (27, 41)]), CLOTH_BLUE)
    s.line(27, 41, 43, 41, GOLD[2])
    s.g("neck", 50, 34)
    s.part(s.capsule(50, 36, 58, 22, 5.5, 4.2), HORSE)
    s.g("plume", 52, 24, "neck")
    for i, (x, y) in enumerate(((56, 18), (53, 22), (50, 26), (48, 30), (46, 33))):
        _bolt(s, [(x, y), (x - 4, y - 2 + i % 2), (x - 6, y + 2), (x - 9, y)])
    s.g("head", 58, 22, "neck")
    s.part(s.capsule(58, 20, 67, 26, 4.2, 2.8), HORSE)
    s.part(s.poly([(56, 16), (57, 11), (60, 16)]), HORSE)
    s.fill(s.rect(61, 19, 63, 21), (240, 250, 255), glow=True)
    s.pxs([(68, 26), (66, 27)], DARK)
    s.line(62, 25, 66, 27, IRON[2])                                               # bit and reins
    s.g("body")
    s.line(40, 29, 62, 25, LEATHER[1])
    # the rider
    s.g("arm_f", 38, 18)
    s.part(s.capsule(38, 18, 41, 25, 1.8), CLOTH_BLUE, bias=-0.25)
    s.g("body")
    s.part(s.poly([(31, 13), (40, 12), (42, 28), (32, 30)]), CLOTH_BLUE)
    s.part(s.rect(31, 24, 42, 26), LEATHER, flat=True)
    s.part(s.capsule(36, 28, 40, 37, 2.2), CLOTH_BLUE)                            # thigh over the saddle
    s.part(s.capsule(40, 37, 39, 44, 1.8), LEATHER, edge=False)
    s.g("head", 36, 12)
    s.part(s.ellipse(37, 7, 5, 5.6) | s.poly([(31, 7), (42, 6), (43, 12), (31, 13)]), CLOTH_BLUE)
    s.fill(s.ellipse(39.5, 8, 2.6, 3.4), (10, 12, 20))
    s.pxs([(39, 7), (41, 7)], BOLT[2], glow=True)
    s.part(s.poly([(32, 3), (27, 1), (29, 6)]), CLOTH_BLUE)
    s.g("weapon", 33, 16)
    s.part(s.capsule(33, 16, 38, 22, 2.0), CLOTH_BLUE)
    s.g("hand_w", 38, 22, "weapon")
    s.part(s.capsule(34, 23, 70, 8, 1.0), WOOD, flat=True)                        # lance, couched and raised
    s.part(s.poly([(68, 6), (76, 2), (71, 10)]), STEEL, flat=True)
    s.part(s.poly([(60, 12), (66, 10), (58, 7)]), CLOTH_BLUE, flat=True)          # pennant
    s.part(s.ellipse(39, 22, 1.8, 1.8), LEATHER)
    leg(s, "n2", (25, 43), (20, 50), (24, 56), 3.0, HORSE, foot=(25, 58), foot_r=(3, 1.6))
    leg(s, "n", (49, 43), (53, 50), (50, 56), 2.8, HORSE, foot=(51, 58), foot_r=(3, 1.6))
    s.ink()
    s.shadow(37, 60, 24, 2.4)
    return s


def squall_witch(pose=None, pad=0):
    """Squall Witch: a hag of the high passes who sold her voice to the wind for a broom and a bad temper. She rides
    a gust, rags and long grey hair whipping, one arm thrown out to fling the wind, a crooked staff hung with bird
    skulls and bells that do not ring."""
    s = Sprite(58, 62, pose, pad)
    s.g("tail", 22, 38)
    s.part(s.poly([(12, 34), (30, 34), (36, 44), (28, 46), (20, 52), (8, 50), (2, 44)]), CLOTH_BLUE, bias=-0.2)
    for i in range(4):                                                            # the gust she rides
        s.line(4 + i * 3, 52 + i, 30 + i * 4, 49 + i, (190, 210, 230))
        s.line(10 + i * 2, 54 + i, 22 + i * 3, 54 + i, (150, 170, 196))
    dither_out(s, 0, 40, 40, 58, keep=lambda x, y: ((x + y) % 2 == 0) or y < 46)
    arm(s, "arm_f", "fore_f", (24, 24), (19, 29), (14, 26), 1.5, STORMSKIN, bias=-0.25, hand_r=1.4)
    s.g("body")
    s.part(s.poly([(18, 20), (30, 19), (33, 36), (16, 37)]), CLOTH_BLUE)
    s.line(23, 22, 22, 36, CLOTH_BLUE[1])
    s.part(s.rect(18, 29, 32, 31), LEATHER, flat=True)
    s.g("head", 28, 18)
    s.g("hair", 24, 10, "head")
    s.part(s.poly([(25, 8), (14, 6), (4, 10), (12, 13), (2, 18), (14, 18), (8, 24), (22, 18), (26, 16)]),
           [(120, 124, 132), (160, 164, 172), (200, 202, 208)])
    s.g("head", 28, 18)
    s.part(s.ellipse(29, 13, 4.6, 5.2), STORMSKIN)
    s.part(s.poly([(33, 13), (38, 17), (33, 17)]), STORMSKIN)                      # hooked nose
    s.pxs([(31, 11), (32, 11)], BOLT[2], glow=True)
    s.line(30, 18, 33, 18, (40, 30, 40))
    s.part(s.poly([(22, 9), (28, 2), (31, 1), (32, 6), (36, 9), (22, 11)]), CLOTH_BLUE)   # ragged hood
    s.g("weapon", 27, 23)
    arm(s, "weapon", "hand_w", (27, 23), (34, 27), (41, 24), 1.6, STORMSKIN, hand_r=1.5)
    s.g("hand_w", 34, 27, "weapon")
    s.part(s.capsule(36, 44, 46, 6, 1.0), WOOD, flat=True)
    s.part(s.ellipse(46, 5, 2.4, 2.0), BONE)
    s.pxs([(47, 5)], DARK)
    s.line(46, 7, 49, 8, BONE[1])
    for x, y in ((44, 12), (43, 17)):
        s.line(x, y, x + 2, y + 3, IRON[2])
        s.px(x + 2, y + 4, GOLD[3])
    for i in range(3):                                                            # wind flung from her
        s.line(48 + i, 18 + i * 4, 56, 15 + i * 5, (210, 228, 240))
    s.ink()
    s.shadow(22, 58.5, 11, 1.8)
    return s


def spark_wisp(pose=None, pad=0):
    """Spark Wisp: a scrap of a dead stormsinger's last note, still crackling. A small jagged ball of lightning
    with a skull of light inside it and arcs spitting off in every direction. Whatever kills it gets the shock."""
    s = Sprite(36, 40, pose, pad)
    cx, cy = 18, 18
    s.g("aura", cx, cy)
    for i in range(11):
        a = i / 11 * 2 * math.pi + 0.3
        r = 13 + (i * 5) % 4
        x0, y0 = cx + math.cos(a) * 8, cy + math.sin(a) * 8
        x1, y1 = cx + math.cos(a + 0.35) * (r - 3), cy + math.sin(a + 0.35) * (r - 3)
        x2, y2 = cx + math.cos(a - 0.05) * r, cy + math.sin(a - 0.05) * r
        _bolt(s, [(x0, y0), (x1, y1), (x2, y2)] if i % 3 else [(x0, y0), (x1, y1)])
    s.g("body")
    s.part(s.ellipse(cx, cy, 9.5, 9.5), [(40, 50, 150), (80, 110, 230), (150, 185, 255), (215, 232, 255)], bulge=1.2, glow=True)
    s.fill(s.ellipse(cx - 3, cy - 4, 2.6, 1.8), (250, 252, 255), glow=True)
    # a skull of white light inside, with dark slanted sockets and a grin
    s.fill(s.ellipse(cx + 2, cy + 1, 5.2, 4.6), (225, 238, 255), glow=True)
    s.fill(s.poly([(cx - 1, cy - 1), (cx + 2, cy), (cx + 1, cy + 2), (cx - 1, cy + 1)]), (20, 24, 70), glow=True)
    s.fill(s.poly([(cx + 6, cy - 1), (cx + 3, cy), (cx + 4, cy + 2), (cx + 6, cy + 1)]), (20, 24, 70), glow=True)
    s.px(cx, cy + 1, (140, 220, 255), glow=True)
    s.px(cx + 5, cy + 1, (140, 220, 255), glow=True)
    for x in range(cx, cx + 6):
        s.px(x, cy + 4 + (x % 2), (20, 24, 70), glow=True)
    s.ink((40, 50, 140))
    s.shadow(18, 36, 6, 1.4)
    return s


SKY = {"gale_harpy": gale_harpy, "voiceless": voiceless, "stormrider": stormrider, "squall_witch": squall_witch,
       "spark_wisp": spark_wisp}


# ================================================================================================ THE GROVE
def _thorns(s, pts, col=THORN[3]):
    for x, y, dx, dy in pts:
        s.line(x, y, x + dx, y + dy, col)


def seedsower(pose=None, pad=0):
    """Seedsower: a Deepwood grove-planter who has been sowing for three hundred years and has forgotten why. Bent in
    sackcloth, a mask of bark over its face with a crown of dead twigs, one long hand always flinging glowing seeds.
    Wherever the seeds land, something thorned comes up a little later."""
    s = Sprite(52, 60, pose, pad)
    s.g("cloak", 19, 22)
    s.part(s.poly([(17, 21), (24, 21), (23, 50), (17, 53), (11, 51), (10, 44), (14, 32)]), BARK_D, bias=-0.2)
    s.part(s.ellipse(15, 37, 5.5, 6.5), [(90, 74, 50), (126, 104, 70), (156, 132, 92), (176, 152, 110)])   # seed sack
    s.line(15, 31, 22, 23, LEATHER[1])
    s.pxs([(13, 33), (16, 35), (14, 38)], VENOM[1], glow=True)
    leg(s, "f", (23, 42), (22.5, 47), (22, 52), 2.0, BARK_D, foot=(22, 54), foot_r=(2.8, 1.4), bias=-0.3)
    s.g("body")
    s.part(s.poly([(17, 21), (29, 20), (31, 34), (33, 47), (16, 47), (17, 34)]), [(62, 50, 36), (88, 72, 50), (112, 94, 66), (130, 112, 80), (150, 130, 96)])
    s.line(22, 23, 21, 46, (90, 74, 50))
    s.line(28, 24, 29, 46, (90, 74, 50))
    s.part(s.rect(17, 33, 31, 35), LEAF, flat=True)
    dither_out(s, 15, 35, 45, 48, keep=lambda x, y: (x * 3 + y) % 4)
    leg(s, "n", (28, 43), (29, 48), (28.5, 52), 2.1, BARK, foot=(30, 54), foot_r=(3, 1.4))
    s.g("head", 27, 19)
    s.part(s.ellipse(28, 13, 6, 6.4) | s.poly([(22, 13), (34, 11), (35, 20), (22, 21)]), [(90, 74, 50), (126, 104, 70), (156, 132, 92)])
    s.part(s.poly([(28, 9), (35, 9), (36, 16), (33, 20), (28, 18)]), BARK, bias=0.1)       # bark mask
    s.fill(s.rect(30, 12, 32, 14), (14, 12, 8))
    s.fill(s.rect(33, 12, 35, 14), (14, 12, 8))
    s.pxs([(31, 13), (34, 13)], VENOM[2], glow=True)
    s.line(29, 17, 33, 18, BARK[0])
    for x, h, lean in ((23, 7, -2), (26, 9, -1), (29, 8, 1), (32, 6, 2), (25, 6, -3)):     # twig crown
        s.line(x, 8, x + lean, 8 - h, BARK_D[2])
        s.px(x + lean - 1, 8 - h + 2, BARK_D[2])
    arm(s, "weapon", "hand_w", (26, 24), (32, 29), (38, 26), 1.7, BARK, hand_r=1.6)
    s.g("hand_w", 32, 29, "weapon")
    for dx, dy in ((2, -2), (3, 0), (2, 2)):
        s.line(38, 26, 38 + dx * 1.5, 26 + dy, BARK_D[2])
    s.g("aura", 40, 26)
    for x, y in ((43, 22), (46, 27), (42, 30), (48, 21), (45, 33)):
        s.px(x, y, VENOM[2], glow=True)
        s.px(x + 1, y, VENOM[1], glow=True)
    s.ink()
    s.shadow(25, 55, 10, 2.0)
    return s


def briarling(pose=None, pad=0):
    """Briarling: what comes up where a Seedsower's seed falls. Knee-high, a running knot of bramble and thorn on
    twig legs, a seed-husk skull, two red berries for eyes. They come in handfuls and run faster together."""
    s = Sprite(36, 36, pose, pad)
    leg(s, "f", (16, 22), (14, 26), (15, 30), 1.0, BARK_D, bias=-0.3)
    s.g("shin_f", 14, 26, "leg_f")
    s.line(15, 30, 13, 31, BARK_D[1])
    s.g("arm_f", 20, 15)
    s.part(s.capsule(20, 15, 26, 14, 0.9), BARK_D, bias=-0.3)
    s.g("body")
    # a tangle of bramble loops
    for cx, cy, rx, ry, rot in ((17, 17, 7, 5, 0.3), (14, 15, 5, 4, -0.5), (20, 19, 5, 4, 0.8)):
        s.part(s.ellipse(cx, cy, rx, ry, rot) & ~s.ellipse(cx, cy, rx - 1.6, ry - 1.6, rot), BARK)
    s.part(s.ellipse(17, 17, 4.5, 3.5), BARK_D, edge=False)
    _thorns(s, [(10, 14, -2, -1), (12, 11, -1, -2), (16, 11, 0, -2), (21, 13, 1, -2), (24, 18, 2, 0), (11, 19, -2, 1), (19, 22, 1, 2)])
    s.pxs([(13, 18), (22, 15), (18, 21)], LEAF[2])
    s.g("head", 22, 12)
    s.part(s.ellipse(25, 11, 4.6, 4.2), [(110, 90, 60), (150, 126, 86), (186, 164, 118), (210, 192, 150)])
    s.line(23, 7, 28, 14, (110, 90, 60))
    s.pxs([(26, 10), (28, 10)], (230, 30, 40), glow=True)
    s.pxs([(26, 11), (28, 11)], (140, 10, 24))
    s.line(25, 13, 29, 13, (60, 40, 30))
    _thorns(s, [(22, 7, -1, -3), (25, 6, 0, -3), (28, 7, 2, -2)])
    leg(s, "n", (19, 22), (21, 26), (19, 30), 1.1, BARK)
    s.g("shin_n", 21, 26, "leg_n")
    s.line(19, 30, 22, 31, BARK[2])
    s.g("weapon", 15, 16)
    s.part(s.capsule(15, 16, 9, 20, 1.0), BARK)
    s.ink()
    s.shadow(17, 32, 7, 1.4)
    return s


def greenwitch(pose=None, pad=0):
    """Greenwitch: a Deepwood apothecary of the old school, where healing and poison are one craft. Green-grey skin,
    a hood of layered leaves, vials and dried roots at her belt, a mortar steaming with green venom held before her.
    Poison that touches the horde near her turns to medicine."""
    s = Sprite(52, 60, pose, pad)
    s.g("cloak", 20, 22)
    s.part(s.poly([(18, 21), (25, 21), (24, 50), (18, 53), (12, 52), (11, 44), (15, 32)]), LEAF, bias=-0.25)
    for y in range(26, 50, 5):
        s.line(13, y, 22, y + 2, LEAF[0])
    leg(s, "f", (23, 42), (22.5, 47), (22, 52), 2.0, BARK_D, foot=(22, 54), foot_r=(2.8, 1.4), bias=-0.3)
    s.g("body")
    s.part(s.poly([(17, 21), (29, 20), (31, 34), (33, 47), (16, 47), (17, 34)]), BARK)
    s.line(23, 23, 21, 46, BARK[1])
    s.part(s.rect(17, 33, 31, 35), LEATHER, flat=True)
    for x, col in ((19, VENOM), (23, PETAL), (27, VENOM)):                       # vials at the belt
        s.part(s.rect(x, 35, x + 2, 39), [col[0], col[1], col[2]], flat=True, glow=True)
    s.line(29, 35, 30, 40, (120, 100, 60))
    leg(s, "n", (28, 43), (29, 48), (28.5, 52), 2.1, BARK_D, foot=(30, 54), foot_r=(3, 1.4))
    s.g("head", 27, 19)
    s.part(s.ellipse(28.5, 13.5, 4.6, 5.4), GREENSKIN)
    s.pxs([(30, 12), (31, 12)], VENOM[2], glow=True)
    s.part(s.poly([(32, 14), (35, 17), (31, 17)]), GREENSKIN)                       # long nose
    s.line(29, 18, 31, 18, GREENSKIN[0])
    s.px(27, 15, GREENSKIN[1])
    # a hood of overlapping leaves
    for x, y, rx, ry, rot in ((24, 9, 4.5, 2.6, -0.6), (28, 7, 4.5, 2.4, 0.1), (32, 9, 3.6, 2.0, 0.6), (22, 14, 3.5, 2.4, -1.2),
                              (21, 19, 3.4, 2.2, -1.4)):
        s.part(s.ellipse(x, y, rx, ry, rot), LEAF)
    s.line(21, 9, 32, 7, LEAF[0])
    # the mortar held out, venom steaming
    arm(s, "weapon", "hand_w", (26, 24), (31, 30), (36, 30), 1.7, GREENSKIN)
    s.g("hand_w", 31, 30, "weapon")
    s.part(s.poly([(33, 27), (42, 27), (40, 33), (35, 33)]), GRANITE)
    s.part(s.ellipse(37.5, 27, 4.5, 1.4), VENOM, glow=True, edge=False)
    s.line(39, 26, 43, 21, WOOD[2])                                                # pestle
    s.g("aura", 37, 24)
    for x, y in ((36, 22), (38, 19), (35, 16), (37, 13), (40, 23), (39, 17)):
        s.px(x, y, VENOM[1 + (x + y) % 2], glow=True)
    s.ink()
    s.shadow(25, 55, 10, 2.0)
    return s


def barkhulk(pose=None, pad=0):
    """Barkhulk: an oak of the Verdant Deep older than the Concord, torn up by the roots and walking. A split trunk
    with a face sunk in the bark and amber sap for eyes, root legs, branch arms with a few black leaves, fungus and
    moss in its seams. It keeps growing as it walks."""
    s = Sprite(72, 86, pose, pad)
    s.g("arm_f", 46, 30)
    s.part(s.capsule(46, 30, 54, 38, 3.6, 3.0), BARK_D, bias=-0.25)
    s.g("fore_f", 54, 38, "arm_f")
    s.part(s.capsule(54, 38, 58, 50, 3.0, 2.0), BARK_D, bias=-0.25, edge=False)
    for dx, dy in ((-3, 4), (0, 5), (3, 4)):
        s.line(58, 50, 58 + dx, 50 + dy, BARK_D[2])
    leg(s, "f", (30, 64), (27, 71), (28, 77), 4.2, BARK_D, bias=-0.3, r2=3.4)
    s.g("shin_f", 27, 71, "leg_f")
    for dx in (-5, -1, 3):
        s.line(28, 77, 28 + dx, 80, BARK_D[1])
    s.g("body")
    # the crown of branches
    for (x0, y0, x1, y1, r) in ((30, 18, 18, 4, 2.0), (36, 16, 38, 1, 2.0), (42, 18, 54, 6, 1.8), (24, 22, 12, 14, 1.6)):
        s.part(s.capsule(x0, y0, x1, y1, r, r * 0.5), BARK_D)
    for cx, cy in ((16, 4), (38, 1), (55, 5), (11, 13), (24, 7), (47, 8)):
        s.part(s.ellipse(cx, cy, 5, 3.2), [(20, 30, 18), (32, 46, 26), (44, 60, 32)])
    # the trunk
    trunk = s.poly([(24, 18), (46, 17), (49, 40), (47, 66), (25, 66), (21, 42)])
    s.part(trunk, BARK)
    for x0, x1 in ((27, 26), (32, 31), (38, 39), (44, 45)):
        s.line(x0, 20, x1, 64, BARK[1])
    s.line(29, 40, 30, 54, BARK[4])
    # the face: a sunken hollow with sap eyes and a knot of a mouth
    s.fill(s.ellipse(39, 30, 6.5, 4), BARK_D[0])
    s.fill(s.rect(35, 29, 38, 31), (255, 180, 40), glow=True)
    s.fill(s.rect(41, 29, 44, 31), (255, 180, 40), glow=True)
    s.pxs([(36, 32), (42, 32), (36, 33)], (200, 120, 20), glow=True)
    s.fill(s.ellipse(40, 40, 3, 4.5), BARK_D[0])
    s.line(37, 25, 44, 26, BARK_D[0])
    # fungus and moss
    for x, y in ((24, 46), (23, 49), (46, 52)):
        s.part(s.ellipse(x, y, 3, 1.4), [(150, 120, 90), (200, 170, 130), (230, 210, 170)])
    s.pxs([(26, 58), (27, 59), (28, 58), (45, 36), (46, 37), (24, 28), (25, 29)], MOSS[2])
    leg(s, "n", (40, 64), (43, 71), (42, 77), 4.6, BARK, r2=3.8)
    s.g("shin_n", 43, 71, "leg_n")
    for dx in (-3, 1, 5):
        s.line(42, 77, 42 + dx, 80, BARK[2])
    arm(s, "weapon", "hand_w", (24, 28), (18, 42), (20, 54), 4.0, BARK, r2=3.0)
    s.g("hand_w", 18, 42, "weapon")
    for dx, dy in ((-3, 5), (0, 6), (3, 5), (5, 2)):
        s.line(20, 54, 20 + dx, 54 + dy, BARK[2])
    s.part(s.ellipse(16, 46, 2.6, 1.6), [(20, 30, 18), (32, 46, 26), (44, 60, 32)])
    s.ink()
    s.shadow(36, 81.5, 20, 3.0)
    return s


def briar_stag(pose=None, pad=0):
    """Briar Stag: the white stag of the Green Queen's hunts, gone dark and grown through with bramble. A tall stag
    of black-brown hide wound round with thorns, a huge crown of thorned antlers hung with blood-red flowers, eyes
    of green fire. Catch it in frost or mud and it bounds clear."""
    s = Sprite(68, 64, pose, pad, origin=(0, 4))
    s.g("tail", 14, 30)
    s.part(s.ellipse(12, 30, 2.6, 3.4), STAG)
    leg(s, "f", (48, 37), (51, 45), (49, 53), 2.0, STAG, foot=(50, 56), foot_r=(2.0, 1.4), foot_tones=[(30, 24, 20)], bias=-0.35)
    leg(s, "f2", (20, 37), (16, 45), (19, 53), 2.2, STAG, foot=(20, 56), foot_r=(2.0, 1.4), foot_tones=[(30, 24, 20)], bias=-0.35)
    s.g("body")
    s.part(s.capsule(18, 33, 49, 30, 8.5, 8.5), STAG)
    s.part(s.capsule(22, 39, 46, 38, 2.5, 2.5) & s.capsule(18, 33, 49, 30, 8.5, 8.5), STAG, bias=-0.3, edge=False)
    s.part(s.ellipse(47, 34, 6, 5), [(150, 140, 120), (180, 170, 150), (200, 192, 172)], edge=False)   # pale ruff
    # bramble wound round the body
    for i in range(5):
        x = 20 + i * 6
        s.line(x, 24, x + 4, 40, (20, 40, 16))
        s.line(x + 1, 24, x + 5, 40, LEAF[1])
        s.px(x + 3, 29, THORN[4])
        s.px(x + 4, 34, THORN[4])
    s.pxs([(26, 28), (38, 30)], PETAL[3])
    s.g("neck", 48, 30)
    s.part(s.capsule(48, 32, 55, 18, 5, 3.6), STAG)
    s.g("head", 55, 18, "neck")
    s.g("plume", 54, 12, "head")
    # thorned antlers with red flowers
    for pts in (((54, 12), (48, 2), (40, -3)), ((48, 2), (50, -6)), ((44, 0), (40, 4)), ((54, 12), (59, 1), (64, -6)),
                ((59, 1), (66, 1)), ((62, -3), (60, -8)), ((51, 6), (46, 8))):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            s.part(s.capsule(x0, y0 + 6, x1, y1 + 6, 1.3, 0.9), ANTLER, edge=False)
    _thorns(s, [(48, 7, -1, -1), (56, 8, 1, -1), (60, 5, 1, -2), (46, 4, -1, 1)])
    for x, y in ((41, 4), (64, 1), (51, 1), (47, 13)):
        s.part(s.ellipse(x, y, 1.8, 1.6), PETAL, glow=True)
    s.g("head", 55, 18, "neck")
    s.part(s.capsule(54, 16, 65, 22, 4.6, 2.6), STAG)
    s.part(s.poly([(51, 14), (46, 11), (52, 17)]), STAG)                             # ear
    s.fill(s.rect(57, 15, 59, 17), VENOM[2], glow=True)
    s.px(58, 15, (240, 255, 220), glow=True)
    s.px(65, 21, (20, 14, 12))
    leg(s, "n2", (23, 38), (18, 46), (22, 53), 2.6, STAG, foot=(23, 56), foot_r=(2.2, 1.5), foot_tones=[(30, 24, 20)])
    leg(s, "n", (45, 38), (49, 46), (46, 53), 2.4, STAG, foot=(47, 56), foot_r=(2.2, 1.5), foot_tones=[(30, 24, 20)])
    s.ink()
    s.shadow(34, 57.5, 20, 2.2)
    return s


GROVE = {"seedsower": seedsower, "briarling": briarling, "greenwitch": greenwitch, "barkhulk": barkhulk, "briar_stag": briar_stag}


TIDE = {"brinecaller": brinecaller, "rimeback": rimeback, "fogwife": fogwife, "netcaster": netcaster, "mire_eel": mire_eel}
HORDE = dict(TIDE)
HORDE.update(STONE_HOST)
HORDE.update(HOLLOW)
HORDE.update(FLAME)
HORDE.update(SKY)
HORDE.update(GROVE)
CREATURES.update(HORDE)
