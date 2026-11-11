"""Story characters in the hand-drawn 2D style: a standing figure (about 1.6 cells tall) and a 96x96 portrait bust,
both drawn from one spec per character, so the sprite and the portrait always agree.

A spec names the build, materials and signature pieces; the drawing code turns them into parts. Signature items
(Tamsin's lantern-pole, Gorrim's door-shield, Mirelle's ice staff...) are small functions in ITEMS.
"""
from __future__ import annotations

import math

import numpy as np

from bosses import GREY_GLOW, RING
from creatures import CREATURES, DARK, GOLD, LEATHER, STEEL, WOOD
from kit import Sprite, ramp

INKP = (26, 18, 24)


def R(h, spread=0.5, shift=0.035):
    return ramp(h, spread=spread, shift=shift)


# ---- held items for the standing figure (drawn in the near hand at (hx, hy)) ----------------------------------------
def _lantern(s, x, y, light=((255, 200, 90), (255, 236, 160)), sparks=False):
    s.part(s.rect(x - 2, y, x + 3, y + 6), R("a07a34"), flat=True)
    s.fill(s.rect(x - 1, y + 1, x + 2, y + 5), light[0], glow=True)
    s.px(x, y + 2, light[1], glow=True)
    s.px(x, y - 1, R("a07a34")[1])
    if sparks:
        for i, (dx, dy) in enumerate(((-4, 1), (4, 2), (-3, 6), (4, 6), (0, -3), (-5, 4))):
            s.px(x + dx, y + dy, RING[i], glow=True)


def item_lantern_pole(s, hx, hy, sp):
    s.part(s.capsule(hx, hy + 14, hx + 4, hy - 30, 0.9), WOOD, edge=False)
    s.line(hx + 4, hy - 30, hx + 8, hy - 30, STEEL[2])
    _lantern(s, hx + 8, hy - 29)


def item_hammer(s, hx, hy, sp):
    s.part(s.capsule(hx - 2, hy + 6, hx + 6, hy - 18, 1.0), WOOD, edge=False)
    head = s.rect(hx + 1, hy - 26, hx + 13, hy - 17)
    s.part(head, R("4a4650"), flat=True)
    s.line(hx + 1, hy - 22, hx + 13, hy - 22, (255, 140, 40), glow=True)
    s.px(hx + 12, hy - 25, (255, 190, 90), glow=True)


def item_lance(s, hx, hy, sp):
    s.line(hx - 8, hy + 8, hx + 14, hy - 34, R("6e7a90")[3])
    s.line(hx - 7, hy + 8, hx + 15, hy - 34, R("6e7a90")[1])
    s.fill(s.poly([(hx + 13, hy - 33), (hx + 18, hy - 40), (hx + 16, hy - 31)]), (240, 240, 255), glow=True)
    s.pxs([(hx + 19, hy - 42), (hx + 20, hy - 38), (hx + 15, hy - 43)], (200, 200, 255), glow=True)


def item_bow(s, hx, hy, sp):
    for (x0, y0), (x1, y1) in (((hx - 1, hy - 17), (hx + 3, hy - 8)), ((hx + 3, hy - 8), (hx + 3.5, hy)), ((hx + 3.5, hy), (hx + 3, hy + 8)),
                               ((hx + 3, hy + 8), (hx - 1, hy + 16))):
        s.part(s.capsule(x0, y0, x1, y1, 1.0), R("e8e0c8"), edge=False)
    s.line(hx - 1, hy - 17, hx - 1, hy + 16, (220, 214, 200))
    for x, y in ((hx + 3, hy - 9), (hx + 4, hy + 6), (hx, hy - 16)):
        s.pxs([(x, y), (x + 1, y - 1)], (110, 190, 70))


def item_ice_staff(s, hx, hy, sp):
    s.part(s.capsule(hx, hy + 16, hx + 1, hy - 26, 1.4), R("bfe6ee", 0.4), edge=False)
    s.fill(s.ellipse(hx + 1, hy - 27, 3.6, 4.4), (200, 240, 250))
    s.line(hx - 1, hy - 27, hx + 3, hy - 27, (120, 140, 150))                                         # the frozen fish
    s.pxs([(hx + 3, hy - 28), (hx + 3, hy - 26), (hx - 1, hy - 28), (hx, hy - 26)], (120, 140, 150))


def item_pick_shield(s, hx, hy, sp):
    s.part(s.capsule(hx - 4, hy + 4, hx + 2, hy - 12, 1.0), WOOD, edge=False)
    s.part(s.poly([(hx - 4, hy - 14), (hx + 8, hy - 11), (hx - 1, hy - 9)]), STEEL, flat=True)


def item_star_blade(s, hx, hy, sp):
    s.part(s.poly([(hx, hy - 1), (hx + 3, hy - 2), (hx + 20, hy - 26), (hx + 16, hy - 24)]), R("1c1830"), flat=True)
    for k in range(4):
        s.px(hx + 4 + k * 4, hy - 5 - k * 5, (230, 226, 255), glow=True)
    s.part(s.rect(hx - 2, hy - 2, hx + 4, hy), STEEL, flat=True)


def item_astrolabe(s, hx, hy, sp):
    s.line(hx, hy, hx + 1, hy + 6, GOLD[2])
    ring = s.ellipse(hx + 1, hy + 10, 4, 4) & ~s.ellipse(hx + 1, hy + 10, 2.6, 2.6)
    s.fill(ring, GOLD[3])
    s.line(hx - 2, hy + 8, hx + 4, hy + 12, GOLD[1])
    s.pxs([(hx + 6, hy + 6), (hx + 7, hy + 9), (hx - 4, hy + 12)], (200, 190, 255), glow=True)


def item_greatsword(s, hx, hy, sp):
    s.part(s.poly([(hx + 1, hy - 3), (hx + 5, hy - 3), (hx + 6, hy - 40), (hx + 3, hy - 44), (hx, hy - 40)]), R("f0d890", 0.4), flat=True)
    s.fill(s.poly([(hx + 2, hy - 6), (hx + 4, hy - 6), (hx + 4, hy - 38), (hx + 3, hy - 41), (hx + 2, hy - 38)]), (255, 244, 200), glow=True)
    s.part(s.rect(hx - 3, hy - 3, hx + 9, hy - 1), GOLD, flat=True)
    s.part(s.rect(hx + 2, hy - 1, hx + 4, hy + 5), LEATHER, flat=True)


def item_lantern_staff(s, hx, hy, sp):
    white = sp.get("white", False)
    s.part(s.capsule(hx, hy + 16, hx + 1, hy - 30, 1.1), WOOD if not white else R("e8e0d0"), edge=False)
    s.part(s.capsule(hx + 1, hy - 30, hx + 7, hy - 33, 1.0), WOOD if not white else R("e8e0d0"), edge=False)
    s.line(hx + 7, hy - 33, hx + 7, hy - 29, STEEL[2])
    _lantern(s, hx + 7, hy - 28, ((250, 250, 255), (255, 255, 255)) if white else ((255, 200, 90), (255, 236, 160)), sparks=white)


def item_rod(s, hx, hy, sp):
    s.part(s.capsule(hx, hy + 16, hx + 1, hy - 22, 1.0), R("c09040"), edge=False)
    for k in range(-20, 16, 5):
        s.px(hx + 1, hy + k, R("c09040")[0])


def item_locket(s, hx, hy, sp):
    s.fill(s.ellipse(hx + 1, hy + 1, 1.8, 2.0), GOLD[3])
    s.px(hx + 1, hy + 1, GOLD[1])
    s.line(hx + 1, hy + 3, hx, hy + 7, GOLD[2])


def item_sword(s, hx, hy, sp):
    s.part(s.poly([(hx + 1, hy - 2), (hx + 4, hy - 2), (hx + 13, hy - 24), (hx + 10, hy - 24)]), STEEL, flat=True, bias=0.2)
    s.part(s.rect(hx - 2, hy - 2, hx + 7, hy), GOLD, flat=True)


def item_flame(s, hx, hy, sp):
    for k, col in enumerate(((230, 100, 30), (255, 170, 60), (255, 230, 150))):
        s.fill(s.poly([(hx - 3 + k, hy), (hx + 4 - k, hy), (hx + 1, hy - 9 + k * 2)]), col, glow=True)


ITEMS = {k[5:]: v for k, v in dict(globals()).items() if k.startswith("item_")}


# ---- the standing figure --------------------------------------------------------------------------------------------
BUILDS = {"normal": (1.0, 1.0), "tall": (0.95, 1.1), "lean": (0.9, 1.06), "wide": (1.25, 0.92), "short": (1.2, 0.82),
          "huge": (1.35, 1.12), "slight": (0.88, 0.98)}


def figure(sp, pose=None, pad=0):
    """Draw one story character standing, facing right. Coordinates are written for a 52x60 canvas and scaled by build."""
    bx, by = BUILDS[sp.get("build", "normal")]
    W, H = 60, 76
    s = Sprite(W, H, pose, pad)
    cx, foot = 30, 71

    def X(x):
        return cx + (x - 26) * bx

    def Y(y):
        return foot - (61 - y) * by

    def rr(r):
        return r * (bx + by) / 2

    skin = R(sp.get("skin", "e2b08a"), shift=0.02)
    top, top_d = R(sp["top"]), R(sp.get("top_d", sp["top"]), spread=0.42)
    legs = R(sp.get("legs", "5a4a3a"))
    boots = R(sp.get("boots", "4a3426"))
    trim = R(sp.get("trim", "e0aa36"))
    robe = sp.get("body") in ("robe", "gown")
    # cloak behind
    if sp.get("cloak"):
        c = R(sp["cloak"], spread=0.42)
        s.g("cloak", X(24), Y(22))
        s.part(s.poly([(X(21), Y(21)), (X(29), Y(21)), (X(28), Y(50)), (X(22), Y(57)), (X(16), Y(54)), (X(13), Y(48)), (X(16), Y(32))]), c, bias=-0.1)
        s.line(X(17), Y(33), X(15), Y(50), c[0])
    # far leg
    if not robe:
        s.g("leg_f", X(23), Y(40))
        s.part(s.capsule(X(23), Y(40), X(22.4), Y(46), rr(2.2)), legs, bias=-0.3)
        s.g("shin_f", X(22.4), Y(46), "leg_f")
        s.part(s.capsule(X(22.4), Y(46), X(22), Y(53), rr(2.2)), boots, bias=-0.3, edge=False)
        s.part(s.ellipse(X(23), Y(56), rr(3.2), rr(1.8)), boots, bias=-0.3)
    # far arm
    s.g("arm_f", X(30), Y(25))
    s.part(s.capsule(X(30), Y(25), X(33), Y(33), rr(2.0)), top_d, bias=-0.15)
    s.g("fore_f", X(33), Y(33), "arm_f")
    s.part(s.capsule(X(33), Y(33), X(35), Y(39), rr(1.8)), top_d, bias=-0.15, edge=False)
    s.part(s.ellipse(X(35.5), Y(40), rr(1.7), rr(1.7)), skin, bias=-0.15)
    if sp.get("far_item"):
        ITEMS[sp["far_item"]](s, X(35.5), Y(40), sp)
    # near leg
    if not robe:
        s.g("leg_n", X(28), Y(40))
        s.part(s.capsule(X(28), Y(40), X(29), Y(46), rr(2.4)), legs)
        s.g("shin_n", X(29), Y(46), "leg_n")
        s.part(s.capsule(X(29), Y(46), X(29.5), Y(53), rr(2.4)), boots, edge=False)
        s.part(s.ellipse(X(31), Y(56), rr(3.6), rr(1.9)), boots)
    # torso, skirt of the robe or coat
    s.g("body")
    if robe:
        s.part(s.poly([(X(20), Y(36)), (X(32), Y(36)), (X(35), Y(57)), (X(17), Y(57))]), top, bulge=0.6)
        s.line(X(17), Y(57), X(35), Y(57), trim[2])
        for x in (X(23), X(29)):
            s.line(x, Y(40), x + (x - X(26)) * 0.3, Y(56), top[1])
        s.part(s.ellipse(X(23.5), Y(58), rr(2.6), rr(1.4)) | s.ellipse(X(30), Y(58), rr(2.8), rr(1.5)), boots)
    elif sp.get("body") == "coat":
        s.part(s.poly([(X(20), Y(34)), (X(32), Y(34)), (X(34), Y(49)), (X(29), Y(47)), (X(26), Y(50)), (X(18), Y(48))]), top)
    torso = s.poly([(X(20), Y(21)), (X(31), Y(21)), (X(32), Y(30)), (X(31), Y(39)), (X(20), Y(39)), (X(19), Y(30))])
    s.part(torso, top)
    if sp.get("body") == "armour":
        s.line(X(27), Y(22), X(28), Y(37), top[4])
        s.part(s.ellipse(X(21), Y(23), rr(4.2), rr(3.4)), top)                                          # pauldron
    if sp.get("tabard"):
        tb = R(sp["tabard"])
        s.part(s.poly([(X(22), Y(26)), (X(30), Y(26)), (X(31), Y(46)), (X(26), Y(44)), (X(21), Y(46))]), tb, bulge=0.5)
        s.px(X(26), Y(32), trim[3])
        s.px(X(26), Y(33), trim[2])
    s.part(s.rect(X(19.5), Y(36), X(32), Y(38)), LEATHER, flat=True)
    s.px(X(26), Y(36), trim[3])
    if sp.get("chest"):
        sp["chest"](s, X, Y, rr)
    # head
    s.g("head", X(26), Y(21))
    hair = R(sp["hair"]) if sp.get("hair") else None
    hs = sp.get("hair_style", "short")
    if hair is not None and hs in ("long", "braid", "wild"):
        s.g("hair", X(23), Y(10), "head")
        if hs == "braid":
            s.part(s.capsule(X(22), Y(10), X(19), Y(30), rr(1.6), rr(1.1)), hair)
        else:
            s.part(s.poly([(X(20), Y(8)), (X(26), Y(5)), (X(28), Y(12)), (X(25), Y(26 if hs == "long" else 20)), (X(19), Y(27 if hs == "long" else 21)), (X(17), Y(16))]), hair)
        s.g("head", X(26), Y(21))
    s.part(s.capsule(X(26), Y(21), X(26), Y(18), rr(1.6)), skin, bias=-0.15)
    s.part(s.ellipse(X(27), Y(13.5), rr(4.6), rr(5.2)), skin)
    if hair is not None and hs != "bald":
        s.part(s.poly([(X(21), Y(11)), (X(25), Y(7)), (X(30), Y(7.5)), (X(32), Y(10)), (X(27), Y(10)), (X(24), Y(14)), (X(22), Y(16))]), hair)
    eye = sp.get("eye", (40, 34, 40))
    s.pxs([(X(29.6), Y(13)), (X(29.6), Y(14))], eye, glow=bool(sp.get("eye_glow")))
    s.px(X(31.6), Y(15), skin[1])
    s.line(X(28.6), Y(17), X(30.6), Y(17), skin[1])
    if sp.get("beard"):
        bd = R(sp.get("beard_col", sp.get("hair", "888888")))
        s.g("beard", X(28), Y(17), "head")
        ln = {"short": 3, "long": 12, "belt": 18}[sp["beard"]]
        s.part(s.poly([(X(24.5), Y(16)), (X(28), Y(16.5)), (X(31.5), Y(16.5)), (X(31), Y(19)), (X(29), Y(17 + ln)), (X(26), Y(17 + ln - 2)), (X(24), Y(19))]), bd)
        if sp.get("beard_rings"):
            for k in range(2, ln, 4):
                s.px(X(28), Y(18 + k), R(sp["beard_rings"])[3])
        s.g("head", X(26), Y(21))
    if sp.get("face"):
        sp["face"](s, X, Y, rr)
    hd = sp.get("headgear")
    if hd:
        HEADGEAR[hd](s, X, Y, rr, sp)
    # near arm and the held item
    s.g("weapon", X(22), Y(24))
    s.part(s.capsule(X(22), Y(24), X(24), Y(32), rr(2.1)), top)
    s.g("hand_w", X(24), Y(32), "weapon")
    s.part(s.capsule(X(24), Y(32), X(31), Y(33), rr(1.9)), top, edge=False)
    s.part(s.ellipse(X(32.5), Y(33), rr(1.8), rr(1.8)), skin)
    if sp.get("item"):
        ITEMS[sp["item"]](s, X(32.5), Y(33), sp)
    s.ink(sp.get("ink", INKP))
    if sp.get("after"):
        sp["after"](s, X, Y, rr)
    s.shadow(cx, foot - 4 + 4, 11 * bx, 2.4)
    return s


# ---- headgear (figure) ----------------------------------------------------------------------------------------------
def _hat(s, X, Y, rr, sp):
    c = R(sp.get("hat", "7a7a80"))
    s.part(s.poly([(X(18), Y(9)), (X(36), Y(9.5)), (X(33), Y(11)), (X(20), Y(11))]), c, flat=True)
    s.part(s.poly([(X(22), Y(9)), (X(31), Y(9)), (X(28), Y(2)), (X(24), Y(1))]), c)


def _crown(s, X, Y, rr, sp):
    c = R(sp.get("crown", "e0aa36"))
    s.part(s.rect(X(21.5), Y(6), X(32.5), Y(9.5)), c, flat=True)
    for i, x in enumerate((21.5, 24.5, 27.5, 30.5)):
        s.part(s.poly([(X(x), Y(6.5)), (X(x + 2), Y(6.5)), (X(x + 1), Y(0 if i in (1, 2) else 2))]), c, flat=True, edge=False)
    if sp.get("crown_gem"):
        s.px(X(27), Y(8), sp["crown_gem"], glow=True)
    if sp.get("sockets"):
        for x in (23, 25, 27, 29, 31):
            s.px(X(x), Y(8), (8, 6, 12))


def _circlet(s, X, Y, rr, sp):
    s.line(X(22), Y(8), X(32), Y(8.5), (220, 220, 230))
    for i, x in enumerate((23, 25, 27, 29, 31)):
        s.px(X(x), Y(7), RING[i])


def _hood(s, X, Y, rr, sp):
    c = R(sp.get("hood", sp.get("cloak", sp["top"])), spread=0.42)
    s.part(s.poly([(X(20), Y(18)), (X(20), Y(9)), (X(25), Y(5)), (X(31), Y(6)), (X(33), Y(11)), (X(30), Y(10)), (X(26), Y(12)), (X(24), Y(20))]), c)


def _horns(s, X, Y, rr, sp):
    c = R(sp.get("horn", "e6dcc0"))
    s.part(s.poly([(X(23), Y(9)), (X(25), Y(8)), (X(21), Y(1)), (X(19), Y(2))]), c, flat=True)
    s.part(s.poly([(X(28), Y(8)), (X(30), Y(9)), (X(33), Y(2)), (X(31), Y(1))]), c, flat=True)


def _blindfold(s, X, Y, rr, sp):
    s.part(s.rect(X(22), Y(12), X(32), Y(15)), R("1e1a20"), flat=True)
    s.px(X(30), Y(13), GOLD[3])
    _circlet(s, X, Y, rr, sp)


HEADGEAR = {"hat": _hat, "crown": _crown, "circlet": _circlet, "hood": _hood, "horns": _horns, "blindfold": _blindfold}


# ---- signature extras -----------------------------------------------------------------------------------------------
def _war_paint(s, X, Y, rr):
    s.line(X(27), Y(15), X(29), Y(15.5), (250, 250, 255))
    s.px(X(31), Y(13), (250, 250, 255))


def _door_shield(s, X, Y, rr):
    s.g("arm_n", X(30), Y(26))
    door = s.poly([(X(29), Y(22)), (X(39), Y(22)), (X(39), Y(48)), (X(29), Y(48))])
    s.part(door, R("8a7c66"), flat=True)
    s.part(s.poly([(X(30), Y(23)), (X(38), Y(23)), (X(38), Y(47)), (X(30), Y(47))]), R("8a7c66"), bulge=0.4)
    for y in (28, 36, 44):
        s.line(X(31), Y(y), X(37), Y(y), (200, 130, 50))
    s.g("body")


def _ember_arm(s, X, Y, rr):
    for y in (26, 29, 31):
        s.px(X(23), Y(y), (255, 150, 50), glow=True)


def _black_veins(s, X, Y, rr):
    s.line(X(25), Y(28), X(27), Y(33), (40, 30, 60))


def _apron(s, X, Y, rr):
    s.part(s.poly([(X(22), Y(26)), (X(31), Y(26)), (X(32), Y(48)), (X(21), Y(48))]), LEATHER, bulge=0.4)


def _spectacles(s, X, Y, rr):
    s.pxs([(X(26), Y(8)), (X(27), Y(8)), (X(29), Y(8)), (X(30), Y(8))], (200, 200, 220))
    s.pxs([(X(22), Y(13)), (X(22), Y(14)), (X(23), Y(15)), (X(32), Y(12))], (240, 240, 240))   # side-whiskers


def _halo_glow(s, X, Y, rr):
    s.line(X(17), Y(57), X(35), Y(57), (255, 255, 255), glow=True)


SPECS = {
    "tamsin": dict(name="Tamsin Reed", build="lean", top="8e98aa", top_d="6e7888", body="armour", tabard="34508a",
                   legs="4a4a5a", hair="c8502a", item="lantern_pole", skin="dca684"),
    "brannoc": dict(name="Brannoc Emberhand", build="huge", top="6e7078", body="armour", hair=None, hair_style="bald",
                    beard="long", beard_col="2a2228", beard_rings="c09040", item="hammer", chest=_apron, skin="c88a64"),
    "kaela": dict(name="Kaela Stormrider", build="tall", top="5a6a88", body="coat", hair="1e1a20", hair_style="long",
                  item="lance", face=_war_paint, skin="a8744e", boots="2e2a30"),
    "sylvaine": dict(name="Sylvaine Thornwhisper", build="tall", top="4a6a34", top_d="3a4a2a", legs="5a4630", cloak="3f6a34",
                     hair="8a5a2a", hair_style="long", item="bow", skin="e4bc94"),
    "mirelle": dict(name="Mirelle the Tide-Seer", build="slight", top="d8e4e4", body="robe", trim="3a9a9a", hair="e8e4d8",
                    hair_style="long", item="ice_staff", eye=(140, 230, 230), eye_glow=True, skin="ecd4c4"),
    "gorrim": dict(name="Gorrim Stonebeard", build="short", top="9a4a30", body="armour", hair="b0a080", beard="belt",
                   beard_rings="8a8a90", item="pick_shield", after=None, chest=None, skin="d49a70"),
    "corvin": dict(name="Corvin the Uncrowned", build="tall", top="2e2838", legs="2a2430", cloak="3a2a4a", headgear="hood",
                   hood="3a2a4a", hair="d0d0d8", item="star_blade", skin="c8a088"),
    "ilyra": dict(name="Ilyra the Unbroken", build="slight", top="2a3458", body="robe", hair="f0f0f4", hair_style="long",
                  item="astrolabe", chest=_black_veins, eye=(150, 140, 230), eye_glow=True, skin="dcc4b8"),
    "seraphel": dict(name="Seraphel the Dawnblade", build="tall", top="e8dcb0", top_d="b8a880", body="armour", hair="9a9a9a",
                     legs="c8b888", boots="a89060",
                     item="greatsword", eye=(255, 210, 90), eye_glow=True, skin="d8a884"),
    "oswin_grey": dict(name="Oswin, the Grey Lantern", build="tall", top="7a7a80", body="robe", trim="5a5a60", hair="e0e0e0",
                       hair_style="long", beard="long", beard_col="e8e8e8", headgear="hat", item="lantern_staff", skin="dcb494"),
    "oswin_white": dict(name="Oswin, the White Lantern", build="tall", top="f0f0f4", body="robe", trim="ffffff", hair="ffffff",
                        hair_style="long", beard="long", beard_col="ffffff", item="lantern_staff", white=True, after=_halo_glow,
                        skin="e8c8a8"),
    "ysolde": dict(name="Queen Ysolde", build="slight", top="f0ead8", body="gown", trim="e0aa36", hair="2a2024",
                   hair_style="braid", headgear="circlet", skin="e8c4a4"),
    "ysolde_blind": dict(name="Queen Ysolde, blinded", build="slight", top="f0ead8", body="gown", trim="e0aa36", cloak="6a6a70",
                         hair="2a2024", headgear="blindfold", item="rod", skin="e8c4a4"),
    "fennick": dict(name="Master Tobias Fennick", build="short", top="7a4a2a", legs="4a4038", hair=None, hair_style="bald",
                    item="rod", face=_spectacles, skin="e09a7a", trim="c09040"),
    "cassivane_marshal": dict(name="Cassivane Dral, Lord Marshal", build="huge", top="a8a8b0", body="armour", tabard="9a2424",
                              cloak="8a1f26", hair="5a5050", beard="short", beard_col="c0c0c4", item="locket", skin="d8a888"),
    "vael_orrun_king": dict(name="Vael-Orrun, the High King", build="tall", top="1c1a24", body="robe", trim="3a3648", hair="1c1a24",
                            hair_style="long", headgear="crown", crown="4a4656", sockets=True, skin="d8d0c8",
                            eye=(20, 20, 24)),
    # the Wardens as mortal monarchs, for the prologue's history shots
    "ignar_king": dict(name="Ignar the Forge-King", build="huge", top="6a3a28", body="armour", hair="2a1a14", beard="long",
                       beard_col="2a1a14", headgear="crown", crown="3a3638", crown_gem=(255, 120, 40), item="hammer", skin="c88a64"),
    "aurath_king": dict(name="Aurath the Horse-King", build="lean", top="5a6688", body="coat", hair="c8c8d0", hair_style="long",
                        headgear="crown", crown="c8ccd8", item="lance", skin="d0a07c"),
    "elowen_queen": dict(name="Elowen the Green Queen", build="slight", top="4a7a3a", body="gown", trim="e0c050", hair="c89040",
                         hair_style="long", headgear="crown", crown="5a8a3a", skin="ecc8a4"),
    "thalassa_queen": dict(name="Thalassa the Sea-Queen", build="tall", top="2a7a7a", body="gown", trim="e8e0d0", hair="1a3a4a",
                           hair_style="long", headgear="crown", crown="e8d8d0", crown_gem=(240, 140, 140), skin="e0c0a8"),
    "orrok_king": dict(name="Orrok the Mountain-King", build="huge", top="8a6a48", body="armour", hair="6a6058", beard="belt",
                       beard_col="7a7068", headgear="crown", crown="8a8070", item="pick_shield", skin="c89a78"),
    "nyxara_queen": dict(name="Nyxara the Star-Queen", build="tall", top="2a2240", body="gown", trim="8a6ad0", hair="1a1424",
                         hair_style="long", headgear="hood", hood="1a1424", crown_gem=(230, 230, 255), skin="1a1424",
                         eye=(230, 230, 255), eye_glow=True),
    # Wardens that read as people in a portrait
    "elowen_warden": dict(name="Elowen the Evergreen", build="slight", top="5a4632", body="gown", trim="80a050", hair="f4f0ec",
                          hair_style="long", skin="8a6a48", eye=(150, 230, 120), eye_glow=True),
    "thalassa_warden": dict(name="Thalassa of the Deep", build="tall", top="2a8a8a", body="gown", trim="c09040", hair="1a4a5a",
                            hair_style="long", skin="8ad0d0", eye=(220, 255, 255), eye_glow=True),
}
SPECS["gorrim"]["chest"] = _door_shield
SPECS["orrok_king"]["chest"] = _door_shield
SPECS["brannoc"]["after"] = _ember_arm


# ---- portraits ------------------------------------------------------------------------------------------------------
ACCENT = {"tamsin": "d8a040", "brannoc": "e0602a", "kaela": "8aa0e0", "sylvaine": "60a040", "mirelle": "40b0b0",
          "gorrim": "b07030", "corvin": "8a60d0", "ilyra": "7a70e0", "seraphel": "f0d070", "oswin_grey": "d8a040",
          "oswin_white": "f0f0ff", "ysolde": "e0c060", "ysolde_blind": "a0a0a8", "fennick": "c09040",
          "cassivane_marshal": "b03030", "elowen_warden": "60a040", "thalassa_warden": "40b0b0", "vael_orrun_king": "605a70", "ignar_king": "e0602a", "aurath_king": "8aa0e0",
          "elowen_queen": "60a040", "thalassa_queen": "40b0b0", "orrok_king": "b07030", "nyxara_queen": "8a60d0"}


def _p_hair_back(s, sp, hair):
    hs = sp.get("hair_style", "short")
    if hs == "long":
        s.part(s.poly([(34, 30), (44, 20), (58, 20), (60, 34), (54, 60), (46, 80), (32, 82), (30, 56)]), hair)
        s.line(38, 40, 36, 78, hair[1])
        s.line(44, 44, 42, 78, hair[3])
    elif hs == "braid":
        for k in range(5):
            s.part(s.ellipse(37 - k * 1.2, 56 + k * 7, 4.2, 4.6), hair)
        s.part(s.ellipse(32, 92, 2, 3), GOLD)


def _p_hair_front(s, sp, hair):
    hs = sp.get("hair_style", "short")
    if hs == "bald":
        s.pxs([(44, 26), (45, 25), (46, 25)], (255, 240, 220))
        return
    s.part(s.poly([(30, 44), (30, 30), (38, 20), (50, 16), (62, 19), (67, 28), (60, 26), (52, 26), (44, 30), (38, 38), (37, 50)]), hair)
    s.line(42, 22, 36, 36, hair[3])
    s.line(52, 19, 46, 27, hair[3])


def _p_beard(s, sp):
    bd = R(sp.get("beard_col", sp.get("hair", "888888")))
    ln = {"short": 6, "long": 26, "belt": 30}[sp["beard"]]
    s.part(s.poly([(38, 48), (44, 52), (54, 54), (62, 52), (65, 52), (64, 58), (60, 63 + ln * 0.3), (52, 63 + ln), (42, 60 + ln * 0.6), (37, 54)]), bd)
    s.fill(s.rect(55, 55, 61, 57), (60, 40, 40))                                                     # mouth in the beard
    s.line(46, 56, 48, 56 + ln * 0.6, bd[1])
    s.line(56, 56, 54, 56 + ln * 0.8, bd[3])
    if sp.get("beard_rings"):
        rc = R(sp["beard_rings"])
        for k in range(10, int(ln) + 6, 8):
            s.fill(s.rect(50, 52 + k, 56, 54 + k), rc[3])
            s.line(50, 54 + k, 56, 54 + k, rc[1])


def _p_headgear(s, sp):
    hd = sp.get("headgear")
    if hd == "hat":
        c = R(sp.get("hat", "7a7a80"))
        s.part(s.ellipse(50, 24, 30, 5), c, flat=True)
        s.part(s.poly([(36, 24), (64, 24), (60, 6), (52, 0), (42, 4)]), c)
        s.line(37, 21, 63, 21, c[0])
    elif hd == "crown":
        c = R(sp.get("crown", "e0aa36"))
        s.part(s.poly([(34, 22), (66, 20), (66, 26), (34, 28)]), c, flat=True)
        for x in (34, 41, 48, 55, 62):
            s.part(s.poly([(x, 23), (x + 4, 23), (x + 2, 12)]), c, flat=True, edge=False)
        if sp.get("crown_gem"):
            s.fill(s.ellipse(50, 24, 2, 2), sp["crown_gem"], glow=True)
    elif hd in ("circlet", "blindfold"):
        s.line(36, 24, 66, 22, (220, 220, 232))
        for i, x in enumerate((40, 45, 50, 55, 60, 64)):
            s.px(x, 22 - (1 if i % 2 else 0), RING[i], glow=True)
        if hd == "blindfold":
            s.part(s.poly([(34, 33), (68, 32), (68, 40), (34, 41)]), R("1e1a20"), flat=True)
            s.line(40, 36, 64, 35, GOLD[2])
            s.pxs([(44, 36), (52, 35), (60, 35)], GOLD[3])
    elif hd == "hood":
        c = R(sp.get("hood", sp.get("cloak", sp["top"])), spread=0.42)
        s.part(s.poly([(28, 64), (28, 30), (38, 14), (54, 10), (68, 18), (72, 34), (66, 26), (54, 22), (42, 28), (38, 44), (40, 64)]), c)
        s.line(66, 26, 70, 40, c[0])


FEMALE = {"elowen_warden", "thalassa_warden", "tamsin", "kaela", "sylvaine", "mirelle", "ilyra", "seraphel", "ysolde", "ysolde_blind", "elowen_queen",
          "thalassa_queen", "nyxara_queen"}
OLD = {"elowen_warden", "oswin_grey", "oswin_white", "fennick", "gorrim", "brannoc", "cassivane_marshal", "orrok_king"}


def portrait(cid, pose=None, pad=0):
    """A 96x96 bust, facing three-quarters right, on a dark vignette of the character's colour."""
    sp = SPECS[cid]
    s = Sprite(96, 96, pose, pad)
    acc = R(ACCENT.get(cid, "8a8a8a"), spread=0.4)
    # backdrop: a dark disc in the character's colour, ringed
    bg = s.ellipse(48, 48, 46, 46)
    s.fill(bg, tuple(int(c * 0.28) for c in acc[1]))
    s.fill(s.ellipse(40, 36, 30, 30) & bg, tuple(int(c * 0.4) for c in acc[2]))
    s.fill(bg & ~s.ellipse(48, 48, 44.5, 44.5), acc[2])
    base_a = s.a.copy()
    s.a[:] = False
    skin = R(sp.get("skin", "e2b08a"), shift=0.02)
    top, trim = R(sp["top"]), R(sp.get("trim", "e0aa36"))
    hair = R(sp["hair"]) if sp.get("hair") else None
    if sp.get("cloak"):
        c = R(sp["cloak"], spread=0.42)
        s.part(s.poly([(4, 96), (10, 74), (26, 66), (70, 66), (88, 74), (94, 96)]), c, bias=-0.1)
    if hair is not None:
        _p_hair_back(s, sp, hair)
    s.part(s.capsule(45, 78, 46, 60, 9.5, 8.5), skin, bias=-0.4)                                     # neck
    # shoulders and chest
    s.part(s.poly([(8, 96), (14, 82), (30, 72), (62, 72), (82, 80), (90, 96)]), top)
    body = sp.get("body")
    if body == "armour":
        s.part(s.ellipse(22, 80, 16, 11), top)
        s.part(s.ellipse(78, 82, 12, 9), top, bias=-0.1)
        s.line(10, 86, 34, 88, trim[3])
        s.line(48, 76, 50, 96, top[4])
    else:
        s.part(s.poly([(36, 70), (60, 70), (50, 90)]), top, bulge=0.4, bias=-0.1)
        s.line(36, 70, 50, 90, trim[3])
        s.line(60, 70, 50, 90, trim[2])
    s.part(s.poly([(30, 72), (40, 70), (46, 76), (54, 70), (64, 72), (60, 78), (46, 82), (34, 78)]), top, bias=0.05)
    s.line(40, 71, 46, 77, trim[3])
    s.line(46, 77, 54, 71, trim[2])
    if sp.get("tabard"):
        tb = R(sp["tabard"])
        s.part(s.poly([(38, 80), (62, 80), (64, 96), (36, 96)]), tb, bulge=0.4)
        s.fill(s.rect(47, 84, 53, 92), trim[3])
        s.fill(s.rect(48, 85, 52, 91), trim[1])
    if sp.get("portrait_chest"):
        sp["portrait_chest"](s, sp)
    # neck, ear, head: one rounded profile shape, three-quarters right, with brow, nose and chin
    fem = cid in FEMALE
    if fem:       # a softer, narrower jaw and a smaller nose
        head = [(31, 34), (36, 24), (46, 19), (58, 20), (63, 27), (65, 36), (68, 45), (65, 48), (64, 52), (62, 56), (57, 61),
                (49, 64), (39, 59), (32, 50)]
    else:
        head = [(31, 34), (36, 24), (46, 19), (58, 20), (64, 27), (66, 36), (70, 46), (66, 49), (65, 53), (64, 58), (60, 64),
                (48, 66), (37, 61), (32, 50)]
    s.part(s.poly(head), skin, bulge=0.75, bias=0.1)
    s.part(s.ellipse(35, 44, 3.6, 5.4), skin, bias=-0.05)
    s.line(35, 42, 35, 47, skin[1])
    s.line(66, 37, 69, 45, skin[4])                                                                   # light on the nose
    s.pxs([(65, 48), (66, 48), (64, 47)], skin[0])
    # face: brows, eyes, mouth
    eye = sp.get("eye", (52, 40, 40))
    glow = bool(sp.get("eye_glow"))
    for ex, w in ((49, 5), (60, 3)):
        s.line(ex - 1, 32, ex + w, 31, hair[1] if hair is not None else skin[1])
        s.fill(s.rect(ex, 35, ex + w, 38), (240, 236, 228))
        s.fill(s.rect(ex + w - 2, 35, ex + w, 38), eye, glow=glow)
        s.px(ex + w - 2, 35, (255, 255, 255), glow=True)
        s.line(ex, 34, ex + w, 34, (40, 28, 30))
    if fem:
        s.line(56, 55, 61, 54, (170, 70, 70))
        s.line(57, 56, 60, 56, (200, 110, 100))
        for ex, w in ((49, 5), (60, 3)):
            s.px(ex + w + 1, 34, (40, 28, 30))                                                       # lashes
    else:
        s.line(56, 56, 62, 55, (150, 80, 70))
        s.px(58, 57, skin[1])
    if cid in OLD:
        s.line(66, 40, 63, 42, skin[1])
        s.line(52, 41, 56, 42, skin[1])
        s.line(60, 50, 58, 54, skin[1])
        s.line(40, 28, 46, 27, skin[1])
    s.line(50, 63, 56, 62, skin[1])                                                                   # under the chin
    if sp.get("portrait_face"):
        sp["portrait_face"](s, sp)
    if sp.get("beard"):
        _p_beard(s, sp)
    if hair is not None and sp.get("headgear") != "hood":
        _p_hair_front(s, sp, hair)
    elif sp.get("hair_style") == "bald":
        _p_hair_front(s, sp, skin)
    _p_headgear(s, sp)
    s.ink(INKP)
    # put the backdrop back under the figure
    fig = s.a.copy()
    keep = base_a & ~fig
    s.a |= base_a
    s.rgb[keep] = s.rgb[keep]
    return _composite_bg(s, base_a, fig, acc)


def _composite_bg(s, base_a, fig, acc):
    # redraw the backdrop where the figure is not, and clip the figure to the disc
    rgb = s.rgb.copy()
    bg = Sprite(96, 96)
    m = bg.ellipse(48, 48, 46, 46)
    bg.fill(m, tuple(int(c * 0.28) for c in acc[1]))
    bg.fill(bg.ellipse(40, 36, 30, 30) & m, tuple(int(c * 0.4) for c in acc[2]))
    out = bg.rgb.copy()
    out[fig & m] = rgb[fig & m]
    ring = m & ~bg.ellipse(48, 48, 44.5, 44.5)
    out[ring] = acc[2]
    s.rgb = out
    s.a = m.copy()
    s.glow &= m
    return s


def _pf_paint(s, sp):
    s.line(56, 44, 62, 45, (250, 250, 255))
    s.line(64, 42, 66, 45, (250, 250, 255))
    s.line(46, 42, 50, 47, (250, 250, 255))


def _pf_freckles(s, sp):
    for x, y in ((56, 44), (59, 45), (62, 43), (46, 44), (49, 45)):
        s.px(x, y, (255, 210, 110), glow=True)


def _pf_broken_nose(s, sp):
    s.pxs([(65, 41), (66, 43), (64, 44)], R(sp["skin"])[0])
    s.line(46, 30, 52, 40, (200, 120, 110))                                                        # scar


def _pf_scar_brow(s, sp):
    s.line(60, 29, 63, 36, (220, 200, 200))


def _pf_spectacles(s, sp):
    for x in (44, 56):
        ring = s.ellipse(x, 22, 4, 3) & ~s.ellipse(x, 22, 2.6, 1.8)
        s.fill(ring, (200, 170, 90))
        s.fill(s.ellipse(x, 22, 2.4, 1.6), (200, 230, 240))
    for side in ((30, 40, 36, 58), (64, 40, 66, 52)):
        s.part(s.poly([(side[0], side[1]), (side[2], side[1] - 2), (side[2] + 2, side[3]), (side[0] + 2, side[3])]), R("f0f0f0"))


def _pf_ember_runes(s, sp):
    for x, y in ((18, 86), (24, 90), (14, 92)):
        s.px(x, y, (255, 150, 50), glow=True)


def _pf_veins(s, sp):
    for x0, y0, x1, y1 in ((40, 62, 44, 74), (56, 64, 54, 72)):
        s.line(x0, y0, x1, y1, (50, 40, 80))
    s.px(42, 68, (200, 200, 255), glow=True)


def _pf_starface(s, sp):
    s.fill(s.ellipse(52, 42, 14, 17), (16, 12, 26))
    rng = np.random.default_rng(1)
    for _ in range(18):
        s.px(int(rng.integers(42, 64)), int(rng.integers(28, 56)), (230, 228, 255), glow=True)


def _pf_grey(s, sp):
    pass


def _pf_blossoms(s, sp):
    for x, y in ((34, 24), (42, 18), (52, 16), (60, 20), (30, 34), (32, 50), (28, 62)):
        s.pxs([(x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)], (255, 255, 255))
        s.px(x, y, (240, 220, 120))


def _pf_bells(s, sp):
    for x, y in ((32, 50), (36, 64), (30, 72), (40, 76)):
        s.fill(s.poly([(x - 1, y), (x + 1, y), (x + 3, y + 4), (x - 3, y + 4)]), (196, 150, 70))
        s.px(x, y + 5, (110, 80, 40))


PORTRAIT_EXTRAS = {"elowen_warden": _pf_blossoms, "thalassa_warden": _pf_bells, "kaela": _pf_paint, "sylvaine": _pf_freckles, "tamsin": _pf_broken_nose, "corvin": _pf_scar_brow,
                   "fennick": _pf_spectacles, "brannoc": _pf_ember_runes, "ilyra": _pf_veins, "nyxara_queen": _pf_starface}
for _k, _f in PORTRAIT_EXTRAS.items():
    SPECS[_k]["portrait_face"] = _f


def _make(cid):
    def draw(pose=None, pad=0):
        return figure(SPECS[cid], pose, pad)
    draw.__doc__ = SPECS[cid]["name"]
    return draw


PEOPLE = {cid: _make(cid) for cid in SPECS}
CREATURES.update(PEOPLE)
