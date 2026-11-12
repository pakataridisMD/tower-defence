"""The army of the counter-attack: twenty units the player musters against the citadel, drawn with kit.py
in the same hand-drawn style as the creatures. All face right, feet on the bottom rows.

Most are people of the Concord built from one figure (`trooper`) dressed per unit: armour, head, weapon,
shield, skirt and cloak. The rest are drawn on their own: the warhound, the storm-lancer on his horse,
the hawk-rider, the ram and the catapult. The Deepwood archer, the Stoneborn shieldbreaker and the
Spirewright golem reuse the elf, dwarf and golem of creatures.py.
"""
from __future__ import annotations

import math

import numpy as np

import creatures as C
from kit import Sprite, ramp

SKIN = C.SKIN
STEEL = C.STEEL
GOLD = C.GOLD
WOOD = C.WOOD
LEATHER = C.LEATHER
DARK = C.DARK
WHITE = C.WHITE

IRON_B = ramp("3a3436", spread=0.45)          # blackened plate
COPPER = ramp("b8632e", spread=0.5)
NAVY = ramp("2c3c66", spread=0.5)
GAMBESON = ramp("9a3a2c", spread=0.5)
VEIL = ramp("3a2a4a", spread=0.45, shift=0.0)
VEIL_D = ramp("2a1e36", spread=0.4, shift=0.0)
HIDE = ramp("8a4a2a", spread=0.5)
FLAME_HAIR = ramp("e0702a", spread=0.55)
SKY = ramp("8fb4d8", spread=0.5, shift=0.0)
SKY_D = ramp("5a7ea8", spread=0.45, shift=0.0)
SNOW = ramp("e8ecf0", spread=0.4, shift=0.0)
TEAL = ramp("2f7f86", spread=0.5, shift=0.0)
PEARL = ramp("d8d2c0", spread=0.45)
CHAR = ramp("3a3a40", spread=0.45, shift=0.0)
ICE = ramp("cfe2ee", spread=0.45, shift=0.0)
CREAM = ramp("e6dcc0", spread=0.45)
CREAM_D = ramp("b8aa8a", spread=0.45)
WHITE_HAIR = ramp("e8e4dc", spread=0.4)
HORSE = ramp("cfd0d4", spread=0.55, shift=0.0)
MANE = ramp("4a4c58", spread=0.45)
HAWK = ramp("7a5a3a", spread=0.55)
HAWK_L = ramp("e8dcc0", spread=0.45)
HOUND = ramp("5a4a44", spread=0.5)

FIRE = [(200, 70, 20), (255, 130, 30), (255, 190, 60), (255, 236, 150)]
VOIDL = [(120, 60, 200), (170, 110, 255), (220, 180, 255)]
ICEL = [(90, 180, 230), (150, 225, 255), (230, 250, 255)]
STORM = [(120, 150, 255), (190, 215, 255), (245, 250, 255)]
SUN = [(230, 160, 40), (255, 210, 90), (255, 245, 200)]


# ------------------------------------------------------------------ the people of the Concord

def _head(s, cfg):
    kind = cfg.get("helm", "great")
    H = cfg.get("helm_tone", STEEL)
    plume = cfg.get("plume")
    eyes = cfg.get("eyes")
    if kind in ("great", "horned"):
        if plume is not None:
            s.g("plume", 21, 7, "head")
            s.part(s.poly([(22, 6), (17, 2), (11, 4), (9, 10), (12, 16), (15, 11), (19, 10)]), plume)
            s.g("head", 24, 20)
        s.part(s.ellipse(24.5, 14, 6.8, 7.0) | s.rect(18, 8, 31, 12), H)
        s.part(s.rect(18, 7, 31, 9), H, flat=True, bias=0.3)
        s.fill(s.rect(24, 13, 32, 15), DARK)
        glint = eyes or (255, 240, 200)
        s.px(28, 13, glint, glow=eyes is not None)
        s.px(30, 13, glint, glow=eyes is not None)
        s.line(28, 9, 28, 20, H[1])
        s.pxs([(26, 17), (26, 19), (30, 17), (30, 19)], DARK)
        s.line(19, 20, 30, 20, H[0])
        if kind == "horned":
            s.part(s.poly([(19, 8), (14, 1), (12, -4), (17, 0), (22, 7)]), C.BONE)
            s.part(s.poly([(29, 7), (33, 0), (37, -3), (35, 3), (31, 9)]), C.BONE)
    elif kind == "kettle":
        s.part(s.ellipse(26, 15, 4.6, 5.0), SKIN)
        s.pxs([(29, 14), (29, 15)], DARK)
        s.px(31, 16, SKIN[1])
        s.line(27, 18, 29, 18, SKIN[1])
        s.part(s.ellipse(25, 9.5, 6.0, 4.4), H)
        s.part(s.poly([(15, 11), (35, 11), (33, 13.5), (17, 13.5)]), H, flat=True, bias=0.2)
        s.line(22, 13, 22, 19, LEATHER[1])
        if plume is not None:
            s.part(s.ellipse(24, 5, 2.0, 2.0), plume)
    elif kind in ("hood", "cowl", "mask"):
        hood = cfg.get("hood", VEIL)
        s.g("cloak", 20, 12, "head")
        s.part(s.poly([(18, 9), (14, 14), (12, 22), (18, 22)]), hood, bias=-0.15)
        s.g("head", 24, 20)
        s.part(s.ellipse(25, 14, 6.6, 7.2), hood)
        if kind == "cowl":
            s.part(s.ellipse(27.5, 15, 3.6, 4.2), SKIN)
            s.pxs([(29, 14), (29, 15)], cfg.get("eye_colour", DARK))
            s.px(31, 16, SKIN[1])
        else:
            s.fill(s.ellipse(27.5, 15, 3.4, 4.2), (14, 10, 18))
            col = eyes or (200, 200, 220)
            s.px(28, 14, col, glow=True)
            s.px(30, 14, col, glow=True)
            if kind == "mask":
                s.part(s.poly([(25, 16), (31, 16), (30, 20), (26, 20)]), STEEL, flat=True)
        s.line(19, 9, 26, 7, hood[4])
    elif kind == "crest":
        s.part(s.ellipse(26, 15, 4.6, 5.0), SKIN)
        s.pxs([(29, 14), (29, 15)], DARK)
        s.px(31, 16, SKIN[1])
        s.part(s.ellipse(25, 10.5, 6.0, 4.8) | s.rect(19, 10, 23, 18), H)
        s.part(s.poly([(17, 7), (22, 2), (32, 4), (28, 7)]), plume or C.RED)
    else:   # bare head with hair, maybe a circlet
        hair = cfg.get("hair", WHITE_HAIR)
        s.g("hair", 22, 10, "head")
        s.part(s.poly([(19, 9), (24, 6), (27, 11), (23, 24), (17, 25), (17, 16)]), hair)
        s.g("head", 24, 20)
        s.part(s.ellipse(26.5, 14, 4.6, 5.0), SKIN)
        s.part(s.poly([(20, 11), (24, 7), (30, 8), (31, 10), (26, 10), (23, 15)]), hair)
        s.pxs([(29, 13), (29, 14)], DARK)
        s.px(31, 15, SKIN[1])
        s.line(28, 17, 30, 17, SKIN[1])
        if cfg.get("circlet"):
            s.line(21, 9, 30, 9, GOLD[3])
            s.px(29, 9, cfg["circlet"], glow=True)


def _weapon(s, cfg):
    """Drawn in the hand_w group: the forearm from the elbow (33, 24.7), the hand near (37.5, 26.5), and what it holds."""
    kind = cfg["weapon"]
    PD = cfg["plate_d"]
    hand = cfg.get("hand", STEEL)
    glow = cfg.get("glow")
    if kind == "sword":
        s.part(s.poly([(36, 24), (39, 24), (43, 5), (41, 3), (39, 5)]), STEEL, flat=True, bias=0.2)
        s.line(41, 5, 38, 23, STEEL[4])
        s.part(s.rect(33, 23, 43, 25), GOLD, flat=True)
    elif kind == "greatsword":
        blade = s.poly([(36, 24), (40, 24), (47, -4), (45, -7), (42, -3)])
        s.part(blade, IRON_B, flat=True, bias=0.1)
        s.line(44, -4, 38, 22, glow[2], glow=True)
        s.line(43, -3, 37, 22, glow[1], glow=True)
        s.part(s.poly([(31, 22), (45, 24), (45, 26), (31, 25)]), COPPER, flat=True)
    elif kind in ("pike", "harpoon", "lance"):
        ln = {"pike": 34, "harpoon": 22, "lance": 30}[kind]
        dx, dy = 0.42, -0.9
        x0, y0 = 37.5 - dx * 12, 26.5 - dy * 12
        x1, y1 = 37.5 + dx * ln, 26.5 + dy * ln
        s.part(s.capsule(x0, y0, x1, y1, 1.0), WOOD, flat=True, edge=False)
        tip = [(x1 - 2, y1 + 1), (x1 + 2, y1 + 1), (x1 + dx * 9, y1 + dy * 9)]
        s.part(s.poly(tip), STEEL, flat=True, bias=0.2)
        if kind == "harpoon":
            s.line(x1 - 2, y1 + 1, x1 - 4, y1 + 5, STEEL[3])
            s.line(x1 + 2, y1 + 1, x1 + 4, y1 + 4, STEEL[3])
            s.line(x0, y0, x0 - 4, y0 + 4, PEARL[3])
        if kind == "pike" and glow:
            s.part(s.rect(x1 - 1.5, y1 + 3, x1 + 1.5, y1 + 7), GOLD, flat=True)
            s.px(x1, y1 + 5, glow[2], glow=True)
    elif kind in ("crossbow", "arbalest"):
        big = kind == "arbalest"
        wood = CHAR if big else WOOD
        s.part(s.rect(29, 25, 45 + (3 if big else 0), 28), wood, flat=True)
        bx = 44 + (3 if big else 0)
        span = 9 if big else 7
        s.part(s.poly([(bx - 1, 26 - span), (bx + 2, 26 - span + 1), (bx + 1, 27), (bx + 2, 27 + span), (bx - 1, 27 + span)]),
               IRON_B if big else STEEL, flat=True)
        if s.pose.get("_loosed"):
            s.line(bx - 1, 26 - span, bx - 1, 27 + span, (220, 214, 200))
        else:
            s.line(bx - 1, 26 - span, 34, 26, (220, 214, 200))
            s.line(34, 26, bx - 1, 27 + span, (220, 214, 200))
            s.line(34, 25, bx + 5, 25, STEEL[3])
            tipc = glow[2] if glow else STEEL[4]
            s.pxs([(bx + 5, 25), (bx + 6, 25)], tipc, glow=glow is not None)
    elif kind == "staff":
        s.part(s.capsule(37.5, 44, 37.5, 4, 1.1), WOOD, flat=True, edge=False)
        top = cfg.get("staff_top", "ice")
        if top == "ice":
            s.fill(s.poly([(37.5, -6), (41, 1), (37.5, 6), (34, 1)]), glow[0], glow=True)
            s.fill(s.poly([(37.5, -4), (39.5, 1), (37.5, 4)]), glow[1], glow=True)
            s.px(37, -2, glow[2], glow=True)
        else:   # storm: a forked iron head with a spark between the prongs
            s.line(37.5, 4, 34, -2, IRON_B[3])
            s.line(37.5, 4, 41, -2, IRON_B[3])
            s.line(37.5, 4, 37.5, -4, IRON_B[3])
            for (x, y) in ((35, -4), (37, -6), (39, -5), (40, -3), (36, 0)):
                s.px(x, y, glow[2], glow=True)
            s.line(35, -3, 40, -1, glow[1], glow=True)
    elif kind == "lantern":
        s.part(s.capsule(37.5, 26.5, 39, 10, 1.0), WOOD, flat=True, edge=False)
        s.line(39, 10, 42, 9, IRON_B[3])
        s.part(s.rect(40, 9, 46, 17), GOLD, flat=True)
        s.fill(s.rect(41, 11, 45, 16), glow[1], glow=True)
        s.fill(s.rect(42, 12, 44, 15), glow[2], glow=True)
        s.line(40, 9, 46, 9, GOLD[4])
    elif kind == "banner":
        s.part(s.capsule(37.5, 46, 37.5, -10, 1.0), WOOD, flat=True, edge=False)
        s.part(s.ellipse(37.5, -11, 1.8, 1.8), GOLD)
        s.g("chain", 38, -6, "hand_w")
        cloth = s.poly([(38, -6), (54, -6), (54, 16), (46, 11), (38, 16)])
        s.part(cloth, C.RED, bulge=0.5)
        s.line(38, -6, 54, -6, GOLD[3])
        for a in range(0, 360, 30):
            s.px(46 + 4 * math.cos(math.radians(a)), 3 + 4 * math.sin(math.radians(a)), GOLD[3])
        s.part(s.ellipse(46, 3, 2.4, 2.4), GOLD)
        s.g("hand_w", 33, 24.7, "weapon")
    elif kind == "blades":
        s.part(s.poly([(36, 25), (39, 24), (48, 16), (49, 13), (45, 17)]), STEEL, flat=True, bias=0.25)
        s.line(39, 24, 48, 14, glow[1], glow=True)
    elif kind == "firepot":
        s.part(s.ellipse(39, 22, 3.6, 3.4), HIDE)
        s.line(36, 20, 42, 20, COPPER[3])
        s.fill(s.poly([(36.5, 19), (38, 12), (39.5, 16), (41, 11), (42, 19)]), FIRE[1], glow=True)
        s.fill(s.poly([(38, 19), (39.5, 14), (41, 19)]), FIRE[3], glow=True)
    s.part(s.capsule(33, 24.7, 36, 26, 2.6), PD, edge=False)
    s.part(s.ellipse(37.5, 26.5, 2.6, 2.4), hand)


def trooper(cfg, pose=None, pad=0):
    s = Sprite(50, 56, pose, pad)
    P, PD = cfg["plate"], cfg["plate_d"]
    T = cfg.get("trim", STEEL)
    LEG = cfg.get("legs", STEEL)
    BOOT = cfg.get("boots", LEG)
    cape = cfg.get("cape")
    armoured = cfg.get("armoured", True)
    if cape is not None:
        s.g("cloak", 20, 22)
        s.part(s.poly([(17, 21), (24, 21), (22, 44), (15, 48), (9, 46), (11, 32)]), cape, bias=-0.1)
        s.line(12, 33, 11, 45, cape[0])
    s.g("leg_f", 21, 38)
    s.part(s.capsule(21, 39, 20.8, 43, 2.4), LEG, bias=-0.3)
    s.g("shin_f", 20.8, 43, "leg_f")
    s.part(s.capsule(20.8, 43, 20.5, 47, 2.4), LEG, bias=-0.3, edge=False)
    s.part(s.ellipse(20.5, 49.5, 3.6, 2.2), BOOT, bias=-0.3)
    s.g("weapon", 29, 23)
    s.part(s.capsule(29, 23, 33, 24.7, 2.6), PD)
    s.g("hand_w", 33, 24.7, "weapon")
    _weapon(s, cfg)
    s.g("weapon", 29, 23)
    s.part(s.ellipse(30.5, 21.5, 4.2 if armoured else 3.2, 3.4 if armoured else 2.8), PD)
    s.g("body")
    if cfg.get("skirt") == "robe":
        s.part(s.poly([(18, 22), (30, 22), (32, 35), (17, 35)]), P)
    else:
        s.part(s.ellipse(24, 29, 7.4, 7.4), P)
        s.line(27, 23, 28, 34, P[4])
    if armoured:
        s.part(s.rect(19, 21, 30, 23), T, flat=True)
    else:
        s.line(20, 22, 29, 22, T[3])
    if cfg.get("strap"):
        s.line(20, 23, 29, 33, LEATHER[1])
    s.g("head", 24, 20)
    _head(s, cfg)
    s.g("body")
    skirt = cfg.get("skirt", "plate")
    s.g("leg_n", 27, 40)
    s.part(s.capsule(27, 39, 27.5, 43, 2.8), LEG)
    s.g("body")
    if skirt == "plate":
        s.part(s.poly([(16, 35), (32, 35), (33, 42), (15, 42)]), P)
        s.line(15, 42, 33, 42, T[3])
        s.line(24, 36, 24, 41, P[0])
    elif skirt == "short":
        s.part(s.poly([(16, 35), (32, 35), (33, 41), (15, 41)]), cfg.get("skirt_tone", PD))
    s.part(s.rect(16, 34, 32, 36), LEATHER, flat=True)
    s.pxs([(24, 34), (25, 34), (24, 35), (25, 35)], GOLD[3])
    if cfg.get("belt_light"):
        s.fill(s.rect(28, 36, 31, 40), GOLD[1])
        s.fill(s.rect(29, 37, 30, 39), cfg["belt_light"], glow=True)
    s.g("leg_n", 27, 40)
    s.g("shin_n", 27.5, 43, "leg_n")
    s.part(s.capsule(27.3, 42, 28, 47.5, 2.8), LEG)
    if armoured:
        s.part(s.ellipse(27.5, 43, 2.6, 2.0), P)
    s.part(s.ellipse(29.5, 50, 4.2, 2.4) | s.rect(26, 46, 31, 50), BOOT)
    s.g("body")
    if skirt == "robe":
        robe = cfg.get("robe", P)
        s.part(s.poly([(16, 34), (32, 34), (35, 49), (29, 50), (24, 48), (19, 50), (13, 49)]), robe)
        s.line(24, 36, 24, 47, robe[1])
        s.line(13, 49, 35, 49, cfg.get("trim", GOLD)[3])
    s.g("arm_n", 18.5, 24)
    shield = cfg.get("shield")
    if shield == "heater":
        s.part(s.capsule(18.5, 25, 22, 31, 2.6), P)
        s.part(s.poly([(24, 24), (37, 24), (37, 35), (30.5, 44), (24, 35)]), STEEL, flat=True)
        s.part(s.poly([(25.5, 25.5), (35.5, 25.5), (35.5, 34.5), (30.5, 41.5), (25.5, 34.5)]), cfg.get("shield_tone", C.RED), bulge=0.6)
        em = cfg.get("emblem", GOLD)
        s.line(30, 27, 30, 39, em[3])
        s.line(31, 27, 31, 38, em[2])
        s.line(27, 30, 34, 30, em[3])
        s.line(27, 31, 34, 31, em[2])
    elif shield == "round":
        s.part(s.capsule(18.5, 25, 22, 31, 2.6), P)
        st = cfg.get("shield_tone", WOOD)
        s.part(s.ellipse(29.5, 32, 6.6, 7.4), st)
        s.part(s.ellipse(29.5, 32, 2.2, 2.4), PEARL if st is TEAL else STEEL)
        s.line(23, 32, 36, 32, st[1])
    elif cfg.get("off_blade"):
        s.part(s.capsule(18.5, 25, 22, 32, 2.4), PD)
        s.part(s.poly([(22, 33), (24, 32), (31, 37), (32, 39), (28, 37)]), STEEL, flat=True, bias=0.2)
        s.part(s.ellipse(22.5, 33, 2.2, 2.2), cfg.get("hand", SKIN))
    else:
        s.part(s.capsule(18.5, 25, 20.5, 32, 2.4), P)
        s.part(s.ellipse(21, 33.5, 2.2, 2.2), cfg.get("hand", SKIN))
    if armoured:
        s.part(s.ellipse(18.5, 23.5, 5.6, 4.6), P)
        s.line(14, 26, 22, 27, T[3])
        s.line(15, 24, 21, 21, P[4])
    else:
        s.part(s.ellipse(18.5, 24, 3.8, 3.4), P)
    s.ink()
    s.shadow(25, 52, 12, 2.6)
    return s


TROOPERS = {
    "pikeman": dict(plate=NAVY, plate_d=ramp("22305a", spread=0.45), helm="kettle", weapon="pike", glow=SUN,
                    belt_light=SUN[1], shield=None, hand=STEEL, cape=None),
    "crossbowman": dict(plate=GAMBESON, plate_d=C.RED_D, helm="kettle", weapon="crossbow", skirt="short",
                        armoured=False, legs=LEATHER, boots=LEATHER, hand=SKIN, strap=True),
    "ember_knight": dict(plate=IRON_B, plate_d=ramp("2a2426", spread=0.4), trim=COPPER, helm="horned", helm_tone=IRON_B,
                         eyes=FIRE[2], weapon="greatsword", glow=FIRE, cape=ramp("6a1a16", spread=0.4), legs=IRON_B),
    "veil_blade": dict(plate=VEIL, plate_d=VEIL_D, trim=VOIDL and ramp("6a4a8a"), helm="mask", hood=VEIL_D, eyes=VOIDL[2],
                       weapon="blades", glow=VOIDL, off_blade=True, skirt="short", armoured=False, legs=CHAR, boots=CHAR,
                       cape=VEIL_D, hand=CHAR),
    "firebrand": dict(plate=HIDE, plate_d=ramp("6a3820", spread=0.45), trim=COPPER, helm="bare", hair=FLAME_HAIR,
                      weapon="firepot", skirt="short", armoured=False, legs=LEATHER, boots=LEATHER, hand=SKIN, strap=True),
    "stormcaller": dict(plate=SKY, plate_d=SKY_D, trim=GOLD, helm="bare", hair=WHITE_HAIR, circlet=STORM[1],
                        weapon="staff", staff_top="storm", glow=STORM, skirt="robe", robe=SKY_D, armoured=False,
                        legs=SKY_D, boots=LEATHER, hand=SKIN, cape=SNOW),
    "pearl_marine": dict(plate=TEAL, plate_d=ramp("1f5a60", spread=0.45), trim=PEARL, helm="kettle", helm_tone=PEARL,
                         weapon="harpoon", shield="round", shield_tone=TEAL, skirt="short", legs=LEATHER, boots=LEATHER,
                         hand=SKIN),
    "hollow_hunter": dict(plate=CHAR, plate_d=ramp("2a2a30", spread=0.4), trim=ramp("6a6a74"), helm="hood", hood=CHAR,
                          eyes=VOIDL[2], weapon="arbalest", glow=VOIDL, skirt="short", armoured=False, legs=CHAR,
                          boots=LEATHER, cape=ramp("4a4a52", spread=0.4), hand=CHAR),
    "tide_priestess": dict(plate=ICE, plate_d=ramp("9ab8cc", spread=0.45), trim=ramp("9ad0e8"), helm="cowl", hood=ICE,
                           eye_colour=(60, 120, 160), weapon="staff", staff_top="ice", glow=ICEL, skirt="robe", robe=ICE,
                           armoured=False, legs=ICE, boots=ICE, hand=SKIN),
    "lantern_cleric": dict(plate=CREAM, plate_d=CREAM_D, trim=GOLD, helm="cowl", hood=CREAM, weapon="lantern", glow=SUN,
                           skirt="robe", robe=CREAM, armoured=False, legs=CREAM_D, boots=LEATHER, hand=SKIN),
    "banner_bearer": dict(plate=C.RED, plate_d=C.RED_D, helm="great", plume=GOLD, weapon="banner", shield=None),
}


def _trooper(name):
    def draw(pose=None, pad=0):
        return trooper(TROOPERS[name], pose, pad)
    draw.__name__ = name
    return draw


# ------------------------------------------------------------------ beasts, riders and machines

def warhound(pose=None, pad=0):
    """Emberfolk warhound: a lean forge-bred hound, iron collar and spiked harness, embers smouldering in its ruff."""
    s = Sprite(52, 40, pose, pad)
    s.g("tail", 12, 20)
    s.part(s.capsule(12, 20, 5, 13, 1.6, 1.0), HOUND, bias=-0.1)
    s.g("leg_f2", 14, 25)
    s.part(s.capsule(14, 25, 13, 30, 2.2), HOUND, bias=-0.35)
    s.g("shin_f2", 13, 30, "leg_f2")
    s.part(s.capsule(13, 30, 14, 35, 1.6), HOUND, bias=-0.35, edge=False)
    s.g("leg_f", 34, 25)
    s.part(s.capsule(34, 25, 35, 30, 2.0), HOUND, bias=-0.35)
    s.g("shin_f", 35, 30, "leg_f")
    s.part(s.capsule(35, 30, 36, 35, 1.6), HOUND, bias=-0.35, edge=False)
    s.g("body")
    s.part(s.ellipse(24, 22, 13, 6.5), HOUND)
    s.part(s.ellipse(32, 21, 7, 7), HOUND)
    s.line(14, 18, 34, 16, HOUND[4])
    s.part(s.poly([(18, 18), (30, 17), (31, 20), (18, 21)]), LEATHER, flat=True)
    for x in (20, 24, 28):
        s.px(x, 16, STEEL[4])
        s.px(x, 17, STEEL[3])
    for (x, y) in ((27, 13), (30, 12), (33, 12), (29, 14), (32, 14)):
        s.px(x, y, FIRE[2], glow=True)
    s.px(31, 13, FIRE[3], glow=True)
    s.g("neck", 36, 18)
    s.part(s.capsule(34, 19, 40, 13, 3.6), HOUND)
    s.part(s.rect(34, 15, 39, 18), IRON_B, flat=True)
    s.pxs([(35, 15), (37, 15)], STEEL[4])
    s.g("head", 41, 13, "neck")
    s.part(s.ellipse(42, 12, 4.8, 4.0), HOUND)
    s.part(s.poly([(38, 8), (40, 3), (42, 8)]), HOUND, bias=0.1)
    s.g("jaw", 44, 14, "head")
    s.part(s.poly([(44, 13), (51, 14), (50, 17), (44, 16)]), HOUND, bias=-0.1)
    s.pxs([(46, 16), (48, 16)], WHITE)
    s.g("head", 41, 13, "neck")
    s.part(s.poly([(44, 10), (51, 12), (51, 14), (44, 14)]), HOUND)
    s.px(51, 12, DARK)
    s.px(44, 11, FIRE[2], glow=True)
    s.g("leg_n2", 15, 25)
    s.part(s.capsule(15, 25, 16, 30, 2.4), HOUND)
    s.g("shin_n2", 16, 30, "leg_n2")
    s.part(s.capsule(16, 30, 15, 35, 1.8), HOUND, edge=False)
    s.part(s.ellipse(16, 36, 2.6, 1.4), HOUND)
    s.g("leg_n", 31, 25)
    s.part(s.capsule(31, 25, 32, 30, 2.3), HOUND)
    s.g("shin_n", 32, 30, "leg_n")
    s.part(s.capsule(32, 30, 33, 35, 1.8), HOUND, edge=False)
    s.part(s.ellipse(34, 36, 2.6, 1.4), HOUND)
    s.ink()
    s.shadow(25, 36.5, 16, 2.4)
    return s


def gale_lancer(pose=None, pad=0):
    """Galeborn sky-lancer: a pale steppe horse in barding, its rider in blue steel with a long couched lance."""
    s = Sprite(66, 60, pose, pad)
    s.g("tail", 13, 30)
    s.part(s.poly([(14, 28), (8, 30), (5, 40), (8, 46), (11, 38), (15, 32)]), MANE, bias=-0.1)
    s.g("leg_f2", 17, 40)
    s.part(s.capsule(17, 40, 16, 47, 2.6), HORSE, bias=-0.35)
    s.g("shin_f2", 16, 47, "leg_f2")
    s.part(s.capsule(16, 47, 17, 53, 1.8), HORSE, bias=-0.35, edge=False)
    s.part(s.ellipse(17.5, 54.5, 2.4, 1.4), MANE, bias=-0.3)
    s.g("leg_f", 41, 40)
    s.part(s.capsule(41, 40, 42, 47, 2.4), HORSE, bias=-0.35)
    s.g("shin_f", 42, 47, "leg_f")
    s.part(s.capsule(42, 47, 43, 53, 1.8), HORSE, bias=-0.35, edge=False)
    s.part(s.ellipse(43.5, 54.5, 2.4, 1.4), MANE, bias=-0.3)
    s.g("body")
    s.part(s.ellipse(29, 36, 15, 8.5), HORSE)
    s.part(s.poly([(17, 30), (40, 30), (42, 40), (16, 40)]), SKY_D, bulge=0.5)
    s.line(16, 40, 42, 40, GOLD[3])
    for x in (20, 27, 34):
        s.fill(s.poly([(x, 40), (x + 3, 40), (x + 1.5, 43)]), SKY_D[1])
    s.g("neck", 42, 32)
    s.part(s.poly([(38, 34), (44, 22), (50, 18), (52, 24), (46, 36)]), HORSE)
    s.part(s.poly([(43, 22), (48, 16), (47, 22), (42, 30)]), MANE)
    s.g("head", 51, 21, "neck")
    s.part(s.poly([(48, 17), (55, 19), (60, 25), (58, 28), (52, 26), (48, 23)]), HORSE)
    s.part(s.poly([(49, 18), (51, 13), (52, 18)]), HORSE)
    s.part(s.rect(49, 17, 55, 19), SKY_D, flat=True)
    s.px(53, 21, DARK)
    s.px(59, 26, DARK)
    s.line(52, 24, 44, 26, LEATHER[2])
    s.g("body")
    # the rider: blue steel, crest helm, a wing-shaped plume
    s.part(s.capsule(27, 28, 28, 34, 2.6), SKY_D, bias=-0.2)
    s.part(s.ellipse(28, 22, 5.4, 6.4), SKY)
    s.part(s.rect(24, 16, 33, 18), STEEL, flat=True)
    s.g("head", 29, 16)
    s.part(s.ellipse(29.5, 11, 4.6, 5.0) | s.rect(25, 7, 34, 10), STEEL)
    s.fill(s.rect(30, 10, 35, 12), DARK)
    s.px(32, 10, STORM[2], glow=True)
    s.g("plume", 26, 6, "head")
    s.part(s.poly([(27, 6), (21, 1), (16, 3), (19, 6), (15, 8), (22, 9)]), GOLD)
    s.g("body")
    s.g("weapon", 30, 22)
    s.part(s.capsule(14, 26, 64, 18, 1.1), WOOD, flat=True, edge=False)
    s.part(s.poly([(62, 16.5), (70, 17), (62, 20)]), STEEL, flat=True)
    s.g("chain", 56, 19, "weapon")
    s.part(s.poly([(56, 19), (52, 25), (48, 23), (51, 20)]), SKY, bulge=0.4)
    s.g("weapon", 30, 22)
    s.part(s.capsule(30, 22, 34, 24, 2.4), SKY)
    s.part(s.ellipse(34.5, 23.5, 2.2, 2.2), STEEL)
    s.g("leg_n2", 19, 40)
    s.part(s.capsule(19, 40, 20, 47, 2.8), HORSE)
    s.g("shin_n2", 20, 47, "leg_n2")
    s.part(s.capsule(20, 47, 19, 53, 2.0), HORSE, edge=False)
    s.part(s.ellipse(19.5, 54.5, 2.6, 1.5), MANE)
    s.g("leg_n", 38, 40)
    s.part(s.capsule(38, 40, 39, 47, 2.6), HORSE)
    s.g("shin_n", 39, 47, "leg_n")
    s.part(s.capsule(39, 47, 40, 53, 2.0), HORSE, edge=False)
    s.part(s.ellipse(40.5, 54.5, 2.6, 1.5), MANE)
    s.g("body")
    s.part(s.capsule(30, 30, 34, 38, 2.2), SKY)          # the rider's near leg in the stirrup
    s.part(s.ellipse(35, 39, 2.4, 1.6), STEEL)
    s.ink()
    s.shadow(30, 56, 20, 2.8)
    return s


def griffin_rider(pose=None, pad=0):
    """Highwind hawk-rider: a great storm-hawk with barred wings, gold beak and talons, and a rider with a spear."""
    s = Sprite(70, 64, pose, pad)
    s.g("wing_f", 30, 26)
    s.part(s.poly([(30, 26), (24, 8), (34, 2), (48, 4), (44, 14), (38, 26)]), HAWK, flat=True, bias=-0.3)
    for k in range(4):
        s.line(31 + k * 4, 22, 30 + k * 5, 6, HAWK[0])
    s.g("tail", 16, 34)
    s.part(s.poly([(18, 31), (4, 32), (2, 38), (6, 41), (18, 38)]), HAWK, flat=True)
    for y in (34, 37):
        s.line(4, y, 16, y, HAWK_L[2])
    s.g("leg_f", 30, 42)
    s.part(s.capsule(30, 42, 29, 50, 1.6), GOLD, bias=-0.3)
    s.pxs([(27, 51), (29, 52), (31, 51)], GOLD[1])
    s.g("body")
    s.part(s.ellipse(30, 35, 14, 9), HAWK)
    s.part(s.ellipse(35, 38, 8, 6), HAWK_L, bias=0.1)
    for (x, y) in ((32, 36), (36, 36), (34, 39), (38, 39), (36, 41)):
        s.line(x, y, x + 2, y, HAWK[1])
    s.g("neck", 42, 30)
    s.part(s.ellipse(45, 26, 6.0, 6.6), HAWK_L)
    s.g("head", 47, 22, "neck")
    s.part(s.ellipse(48, 20, 5.0, 4.6), HAWK_L)
    s.part(s.poly([(43, 16), (40, 13), (46, 16)]), HAWK)
    s.g("jaw", 52, 21, "head")
    s.part(s.poly([(52, 21), (57, 22), (55, 24), (52, 23)]), GOLD, bias=-0.1)
    s.g("head", 47, 22, "neck")
    s.part(s.poly([(51, 18), (57, 19), (58, 22), (53, 21)]), GOLD)
    s.px(50, 19, DARK)
    s.px(51, 18, STORM[2], glow=True)
    s.g("wing", 30, 28)
    s.part(s.poly([(28, 28), (14, 12), (12, 2), (22, 6), (34, 14), (40, 26)]), HAWK, flat=True)
    for k in range(4):
        s.line(30 - k * 3, 26 - k, 16 + k * 3, 6 + k * 2, HAWK[1])
    s.line(14, 4, 38, 24, HAWK_L[3])
    s.g("body")
    # rider astride, leaning forward
    s.part(s.ellipse(29, 23, 5.0, 6.0), SKY)
    s.part(s.rect(25, 17, 33, 19), STEEL, flat=True)
    s.g("head", 30, 17)
    s.part(s.ellipse(30.5, 12, 4.4, 4.8) | s.rect(26, 8, 35, 11), STEEL)
    s.fill(s.rect(31, 11, 36, 13), DARK)
    s.g("plume", 27, 8, "head")
    s.part(s.poly([(28, 7), (22, 4), (19, 8), (24, 10)]), HAWK_L)
    s.g("body")
    s.g("weapon", 31, 22)
    s.part(s.capsule(18, 30, 54, 6, 1.0), WOOD, flat=True, edge=False)
    s.part(s.poly([(53, 5), (59, 1), (55, 8)]), STEEL, flat=True)
    s.part(s.capsule(31, 22, 36, 21, 2.2), SKY)
    s.part(s.ellipse(37, 21, 2.0, 2.0), STEEL)
    s.g("leg_n", 36, 42)
    s.part(s.capsule(36, 42, 37, 50, 1.8), GOLD)
    s.pxs([(35, 51), (37, 52), (39, 52)], GOLD[2])
    s.ink()
    s.shadow(32, 60, 18, 2.4)
    return s


def battering_ram(pose=None, pad=0):
    """Spirewright ram: a timber shed roofed with hides, on four wheels, swinging an iron-headed log on chains."""
    s = Sprite(74, 46, pose, pad)
    s.g("body")
    # far wheels
    for x in (18, 52):
        s.part(s.ellipse(x, 38, 6, 6), WOOD, bias=-0.35)
    # frame and hide roof
    s.part(s.poly([(10, 34), (62, 34), (62, 37), (10, 37)]), WOOD, flat=True)
    for x in (12, 36, 58):
        s.part(s.rect(x, 14, x + 3, 35), WOOD, flat=True)
    s.part(s.poly([(6, 18), (36, 4), (66, 18), (62, 20), (36, 8), (10, 20)]), HIDE)
    s.part(s.poly([(10, 18), (36, 7), (62, 18), (60, 26), (12, 26)]), ramp("6a4a32", spread=0.45))
    for x in range(16, 60, 8):
        s.line(x, 26, x + (36 - x) * 0.6, 10, HIDE[1])
    s.line(6, 18, 36, 4, HIDE[4])
    s.pxs([(14, 22), (24, 16), (48, 16), (58, 22)], STEEL[3])
    s.g("weapon", 36, 14)
    for x in (24, 46):
        s.line(x, 14, x, 25, STEEL[2])
    s.part(s.capsule(8, 27, 62, 27, 3.2), WOOD, flat=True)
    s.part(s.poly([(60, 21), (70, 23), (73, 27), (70, 31), (60, 33)]), IRON_B)
    s.pxs([(70, 26), (71, 27)], SUN[1], glow=True)
    s.line(60, 21, 60, 33, GOLD[3])
    s.g("body")
    for x in (22, 56):
        s.part(s.ellipse(x, 39, 6.4, 6.4), WOOD)
        s.part(s.ellipse(x, 39, 2.0, 2.0), IRON_B)
        s.line(x - 5, 39, x + 5, 39, WOOD[1])
        s.line(x, 34, x, 44, WOOD[1])
    s.ink()
    s.shadow(38, 44, 30, 2.4)
    return s


def sunstone_catapult(pose=None, pad=0):
    """Spirewright catapult: a timber frame on wheels whose arm throws shards of the broken Sunstone."""
    s = Sprite(64, 54, pose, pad)
    s.g("body")
    for x in (16, 46):
        s.part(s.ellipse(x, 46, 6, 6), WOOD, bias=-0.35)
    s.part(s.poly([(8, 42), (56, 42), (56, 46), (8, 46)]), WOOD, flat=True)
    s.part(s.poly([(24, 42), (30, 24), (34, 24), (30, 42)]), WOOD, flat=True)
    s.part(s.poly([(38, 42), (34, 24), (38, 24), (44, 42)]), WOOD, flat=True, bias=-0.15)
    s.part(s.rect(28, 22, 40, 26), IRON_B, flat=True)
    s.part(s.ellipse(14, 38, 5, 4), IRON_B)                    # counterweight box at the back
    s.g("weapon", 34, 25)
    s.part(s.capsule(34, 25, 10, 34, 1.6), WOOD, flat=True)
    s.part(s.ellipse(9, 35, 3.6, 2.4), LEATHER)
    if not s.pose.get("_loosed"):
        s.fill(s.poly([(7, 33), (9, 29), (11, 33), (9, 35)]), SUN[1], glow=True)
        s.px(9, 31, SUN[2], glow=True)
    s.g("body")
    s.line(30, 26, 18, 38, STEEL[2])
    for x in (20, 50):
        s.part(s.ellipse(x, 47, 6.4, 6.4), WOOD)
        s.part(s.ellipse(x, 47, 2.0, 2.0), IRON_B)
        s.line(x - 5, 47, x + 5, 47, WOOD[1])
        s.line(x, 42, x, 52, WOOD[1])
    s.pxs([(30, 30), (36, 30)], SUN[1], glow=True)
    s.ink()
    s.shadow(32, 52, 26, 2.4)
    return s


def spire_golem(pose=None, pad=0):
    """The golem of creatures.py, its runes burning Sunstone gold instead of blue."""
    s = C.golem(pose, pad)
    gold = {C.RUNE[0]: SUN[0], C.RUNE[1]: SUN[1], C.RUNE[2]: SUN[2]}
    for old, new in gold.items():
        m = s.glow & np.all(s.rgb == np.array(old, np.uint8), axis=-1)
        s.rgb[m] = new
    return s


UNITS = {
    "footman": C.soldier,
    "root_archer": C.elf,
    "ironbreaker": C.dwarf,
    "spire_golem": spire_golem,
    "warhound": warhound,
    "gale_lancer": gale_lancer,
    "griffin_rider": griffin_rider,
    "battering_ram": battering_ram,
    "sunstone_catapult": sunstone_catapult,
}
UNITS.update({name: _trooper(name) for name in TROOPERS})

# How each one moves (anim.py styles, plus the ones gen_allies_art.py adds).
STYLES = {
    "root_archer": "shoot", "spire_golem": "heavy", "ironbreaker": "heavy",
    "pikeman": "thrust", "pearl_marine": "thrust", "crossbowman": "recoil", "hollow_hunter": "recoil",
    "stormcaller": "raise", "tide_priestess": "raise", "lantern_cleric": "raise", "banner_bearer": "raise",
    "warhound": "lunge", "gale_lancer": "charge", "griffin_rider": "fly",
    "battering_ram": "ram", "sunstone_catapult": "catapult",
}
