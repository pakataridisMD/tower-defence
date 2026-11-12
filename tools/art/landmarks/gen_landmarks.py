#!/usr/bin/env python3
"""Draws the enemy war camp and the living cities that stand at the ends of every road.

usage: python3 tools/art/landmarks/gen_landmarks.py [--out DIR] [--sheet FILE]

The pieces are drawn with the hand-drawn pixel-art kit (tools/art/pix2d/kit.py): light from the upper left,
hue-shifted ramps, ink outlines and a normal map for the game's 2D lights. BoardArt (LandmarkArt) places the
pieces on the cells each camp or city covers, so everything here is a single prop that stands on one spot:
tents, stakes and watchtowers for the camp; houses, wall blocks and gate towers for the cities, with one look
per biome; townsfolk and camp sentries as walk strips; and ground patches that go under both.

Writes assets/art/game/landmarks/<piece>.png, <piece>_n.png, <piece>_glow.png (lit windows and fires, for
night) and landmarks.json, which lists every piece with its size, frames and the points the game needs
(chimneys for smoke, fires for light and sparks).
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pix2d"))
from kit import INK, Sprite, hexc, ramp  # noqa: E402

OUT = os.path.join("assets", "art", "game", "landmarks")

# ------------------------------------------------------------------ colours

WOOD = ramp("6a4628", spread=0.5)
WOOD_D = ramp("4a3020", spread=0.45)
HIDE = ramp("5e4a3e", spread=0.45)
HIDE_D = ramp("3e3030", spread=0.4)
BLOOD = ramp("7a1a1e", spread=0.45)
BONE = ramp("ddd2b4", spread=0.5)
IRON = ramp("5e6068", spread=0.5)
STEEL = ramp("8e98aa", spread=0.6)
RED = ramp("b4282a", spread=0.55)
CLOTH = [ramp(c, spread=0.45) for c in ("5a4a3a", "3e4a5a", "5a3a3a", "4a5038", "6a5a48")]
SKIN = [ramp(c, spread=0.4, shift=0.02) for c in ("d9a982", "b07a56", "8a5a3e", "e6c09a")]
HAIR = [(40, 28, 22), (90, 60, 34), (150, 140, 128), (30, 24, 26), (120, 50, 30)]
FIRE = [(150, 40, 20), (230, 90, 30), (255, 160, 50), (255, 220, 120), (255, 250, 220)]
WINDOW = [(255, 170, 70), (255, 214, 130)]
DARK = (24, 18, 22)

# Each biome's city: wall and roof ramps, timber, roof shape, window light.
BIOMES = {
    "meadow": dict(wall=ramp("cbbf9e", spread=0.45), timber=WOOD_D, roof=ramp("4e5a72", spread=0.5),
                   stone=ramp("8a8478", spread=0.5), roof_kind="pitched", walls="timber", window=WINDOW),
    "heart": dict(wall=ramp("e2dccb", spread=0.4), timber=ramp("8a7a5a"), roof=ramp("34477a", spread=0.5),
                  stone=ramp("c8c0ac", spread=0.45), roof_kind="pitched", walls="stone", window=[(255, 200, 110), (255, 240, 190)],
                  trim=ramp("d4a83a")),
    "fire": dict(wall=ramp("4e4040", spread=0.45), timber=ramp("2e2224"), roof=ramp("8e2e1e", spread=0.5),
                 stone=ramp("4a4044", spread=0.45), roof_kind="pitched", walls="stone", window=[(255, 120, 40), (255, 190, 90)]),
    "storm": dict(wall=ramp("7e6e52", spread=0.45), timber=WOOD_D, roof=ramp("8e7e5a", spread=0.45),
                  stone=ramp("7a7e84", spread=0.5), roof_kind="hide", walls="plank", window=WINDOW),
    "nature": dict(wall=ramp("6e4e2e", spread=0.45), timber=ramp("3a2a1c"), roof=ramp("4e6e2a", spread=0.5),
                   stone=ramp("6a7060", spread=0.5), roof_kind="thatch", walls="plank", window=[(220, 255, 140), (250, 255, 200)]),
    "water": dict(wall=ramp("9aa4ae", spread=0.45), timber=ramp("4a5462"), roof=ramp("e4eef6", spread=0.35),
                  stone=ramp("7a8a98", spread=0.5), roof_kind="snow", walls="plank", window=WINDOW),
    "earth": dict(wall=ramp("b48c5c", spread=0.45), timber=WOOD, roof=ramp("9a7448", spread=0.45),
                  stone=ramp("a08460", spread=0.5), roof_kind="flat", walls="adobe", window=WINDOW),
    "void": dict(wall=ramp("3e3a52", spread=0.45), timber=ramp("24202e"), roof=ramp("4e2e72", spread=0.5),
                 stone=ramp("4a4660", spread=0.45), roof_kind="spire", walls="stone", window=[(110, 235, 220), (200, 255, 250)]),
}


# ------------------------------------------------------------------ helpers

def shade_fill(s: Sprite, mask, tones, i=2):
    s.fill(mask, tones[i])


def box(s: Sprite, x0, y0, x1, y1, tones, side=3, kind="plank", seed=0):
    """A wall seen from the front, with its right side in shadow going back and up."""
    side_m = s.poly([(x1, y0), (x1 + side, y0 - side), (x1 + side, y1 - side), (x1, y1)])
    s.fill(side_m, tones[0])
    front = s.rect(x0, y0, x1, y1)
    s.fill(front, tones[2])
    s.line(x0, y0, x1 - 1, y0, tones[3])
    s.line(x0, y1 - 1, x1 - 1, y1 - 1, tones[1])
    rng = np.random.default_rng(seed)
    if kind == "plank":
        for x in range(x0 + 3, x1 - 1, 4):
            s.line(x, y0 + 1, x, y1 - 2, tones[1])
        for _ in range((x1 - x0) // 3):
            s.px(int(rng.integers(x0 + 1, x1 - 1)), int(rng.integers(y0 + 1, y1 - 1)), tones[3])
    elif kind == "stone":
        row = 0
        for y in range(y0 + 3, y1 - 1, 3):
            s.line(x0, y, x1 - 1, y, tones[1])
            off = 2 if row % 2 else 0
            for x in range(x0 + 2 + off, x1 - 1, 5):
                s.px(x, y + 1, tones[1])
                s.px(x, y + 2, tones[1])
            row += 1
        for _ in range((x1 - x0) // 2):
            s.px(int(rng.integers(x0 + 1, x1 - 1)), int(rng.integers(y0 + 1, y1 - 1)), tones[3])
    elif kind == "timber":
        s.line(x0, y0 + 1, x0, y1 - 1, DARK)
        s.line(x1 - 1, y0 + 1, x1 - 1, y1 - 1, DARK)
        s.line(x0, (y0 + y1) // 2, x1 - 1, (y0 + y1) // 2, WOOD_D[1])
        mid = (x0 + x1) // 2
        s.line(mid, y0, mid, y1 - 1, WOOD_D[1])
        s.line(x0 + 1, y0 + 1, mid - 1, (y0 + y1) // 2 - 1, WOOD_D[2])
    elif kind == "adobe":
        for _ in range((x1 - x0)):
            x, y = int(rng.integers(x0 + 1, x1 - 1)), int(rng.integers(y0 + 1, y1 - 1))
            s.px(x, y, tones[1] if rng.random() < 0.5 else tones[3])
    return front


def window(s: Sprite, x, y, w, h, col, shutters=None):
    s.fill(s.rect(x - 1, y - 1, x + w + 1, y + h + 1), DARK)
    s.fill(s.rect(x, y, x + w, y + h), col[0], glow=True)
    s.fill(s.rect(x, y, x + max(1, w // 2), y + max(1, h // 2)), col[1], glow=True)
    if w >= 3:
        s.line(x + w // 2, y, x + w // 2, y + h - 1, DARK)
    if shutters:
        s.fill(s.rect(x - 2, y, x - 1, y + h), shutters[1])
        s.fill(s.rect(x + w + 1, y, x + w + 2, y + h), shutters[1])


def door(s: Sprite, x, y, w, h, tones):
    s.fill(s.rect(x - 1, y - 1, x + w + 1, y + h), DARK)
    s.fill(s.rect(x, y, x + w, y + h), tones[1])
    s.line(x + w // 2, y, x + w // 2, y + h - 1, tones[0])
    s.px(x + w - 2, y + h // 2, (200, 170, 90))


def roof(s: Sprite, x0, x1, eave, ridge, tones, kind, seed=0):
    """The roof over a front wall from x0 to x1: the front slope from the eave up to the ridge."""
    rng = np.random.default_rng(seed)
    if kind == "flat":
        top = s.poly([(x0 - 1, eave), (x1 + 3, eave - 3), (x1 + 3, eave - 6), (x0 - 1, eave - 3)])
        s.fill(top, tones[3])
        s.fill(s.rect(x0 - 1, eave - 3, x1 + 1, eave + 1), tones[2])
        s.line(x0 - 1, eave - 3, x1, eave - 3, tones[4])
        for x in range(x0, x1, 4):                                   # parapet teeth
            s.fill(s.rect(x, eave - 5, x + 2, eave - 3), tones[3])
        s.fill(s.rect(x0 + 2, eave + 1, x0 + 4, eave + 3), WOOD[1])  # roof beams sticking out
        s.fill(s.rect(x1 - 4, eave + 1, x1 - 2, eave + 3), WOOD[1])
        return
    if kind == "spire":
        mid = (x0 + x1) / 2
        slope = s.poly([(x0 - 3, eave), (x1 + 3, eave), (mid + 1, ridge), (mid - 1, ridge)])
        s.part(slope, tones, flat=True)
        for y in range(int(ridge) + 4, eave, 3):
            t = (y - ridge) / max(1, eave - ridge)
            half = (x1 - x0 + 6) / 2 * t
            s.line(round(mid - half) + 1, y, round(mid + half) - 1, y, tones[1])
        s.line(mid, ridge, x1 + 3, eave, tones[0])
        s.line(round(mid), ridge - 4, round(mid), ridge, tones[3])
        s.px(round(mid), ridge - 5, (140, 255, 240), glow=True)
        return
    oh = 3
    pts = [(x0 - oh, eave), (x1 + oh, eave), (x1 + oh - 1 + 3, ridge), (x0 - oh + 2 + 3, ridge)]
    if kind == "hide":
        pts = [(x0 - oh, eave), (x1 + oh, eave), (x1 - 2 + 3, ridge), (x0 + 3 + 3, ridge)]
    slope = s.poly(pts)
    s.part(slope, tones, flat=True, bias=0.05)
    # gable end on the right, in shadow
    s.fill(s.poly([(x1 + oh, eave), (x1 + oh + 3, eave - 3), (pts[2][0], ridge)]), tones[0])
    if kind in ("pitched", "snow"):
        for y in range(int(ridge) + 2, eave, 3):                   # tile courses
            s.line(x0 - oh + 1, y, x1 + oh - 1, y, tones[1])
            off = 1 if (y // 3) % 2 else 3
            for x in range(x0 - oh + off, x1 + oh, 4):
                s.px(x, y - 1, tones[1])
    elif kind == "thatch":
        for _ in range((x1 - x0) * 3):
            x = int(rng.integers(x0 - oh + 1, x1 + oh))
            y = int(rng.integers(int(ridge) + 1, eave))
            if slope[y, x]:
                s.line(x, y, x, min(eave - 1, y + 2), tones[1] if rng.random() < 0.6 else tones[3])
        s.line(x0 - oh, eave, x1 + oh, eave, tones[0])
    elif kind == "hide":
        for x in range(x0, x1 + 2, 5):
            s.line(x, eave - 1, x + 3, ridge + 1, tones[1])
        s.line(x0 - oh, eave, x1 + oh, eave, BLOOD[1])
    if kind == "snow":
        for x in range(x0 - oh, x1 + oh):
            if rng.random() < 0.55:
                s.px(x, eave, (240, 248, 255))
    s.line(pts[3][0], ridge, pts[2][0], ridge, tones[4])


def chimney(s: Sprite, x, top, h, tones):
    s.fill(s.rect(x, top, x + 4, top + h), tones[2])
    s.fill(s.rect(x + 4, top + 1, x + 5, top + h), tones[0])
    s.line(x, top, x + 3, top, tones[4])
    s.fill(s.rect(x + 1, top, x + 3, top + 1), DARK)


# ------------------------------------------------------------------ city pieces

def house(biome: str, variant: int) -> tuple[Sprite, dict]:
    """A town house. variant 0: cottage, 1: tall house, 2: long house with a shop front."""
    b = BIOMES[biome]
    widths = [(28, 13, 15), (24, 20, 18), (34, 12, 13)]
    w, wall_h, roof_h = widths[variant]
    if b["roof_kind"] == "flat":
        roof_h = 7
    if b["roof_kind"] == "spire":
        roof_h += 10
    W, H = w + 12, wall_h + roof_h + 14
    s = Sprite(W, H)
    x0, x1 = 4, 4 + w
    floor_y = H - 4
    top = floor_y - wall_h
    box(s, x0, top, x1, floor_y, b["wall"], kind=b["walls"], seed=variant + len(biome))
    if b["walls"] in ("plank", "timber"):
        s.line(x0, top, x0, floor_y - 1, b["timber"][1])
        s.line(x1 - 1, top, x1 - 1, floor_y - 1, b["timber"][1])
    if b["walls"] == "stone":
        s.fill(s.rect(x0, floor_y - 2, x1, floor_y), b["stone"][1])
    info = {"chimney": None, "windows": []}
    # doors and windows
    door_x = x0 + (w // 2 - 2 if variant != 2 else 4)
    door(s, door_x, floor_y - 7, 5, 7, b["timber"])
    wins = []
    if variant == 0:
        wins = [(x0 + 3, top + 4), (x1 - 7, top + 4)]
    elif variant == 1:
        wins = [(x0 + 3, top + 4), (x1 - 7, top + 4), (x0 + 3, top + 11), (x1 - 7, top + 11)]
    else:
        wins = [(x0 + 12, top + 3), (x0 + 18, top + 3), (x0 + 24, top + 3)]
    for wx, wy in wins:
        if abs(wx - door_x) < 6 and wy + 4 > floor_y - 8:
            continue
        window(s, wx, wy, 4, 4, b["window"], shutters=b["timber"] if variant != 2 else None)
    if variant == 2:                                                 # shop front with an awning and crates
        aw = s.poly([(x0 + 10, top + 9), (x1 - 1, top + 9), (x1 + 1, top + 12), (x0 + 8, top + 12)])
        s.fill(aw, BLOOD[2] if biome != "nature" else ramp("6e7a3a")[2])
        for x in range(x0 + 9, x1, 4):
            s.line(x, top + 10, x + 1, top + 12, BLOOD[3] if biome != "nature" else ramp("6e7a3a")[3])
        s.fill(s.rect(x0 + 12, floor_y - 4, x0 + 17, floor_y), WOOD[2])
        s.line(x0 + 12, floor_y - 4, x0 + 16, floor_y - 4, WOOD[3])
        s.fill(s.rect(x0 + 19, floor_y - 3, x0 + 23, floor_y), WOOD[1])
        s.pxs([(x0 + 13, floor_y - 5), (x0 + 15, floor_y - 5)], (170, 60, 40))
        s.px(x0 + 20, floor_y - 4, (200, 170, 60))
    if biome == "heart":
        s.line(x0, top, x1 - 1, top, b["trim"][3])
    roof(s, x0, x1, top, top - roof_h, b["roof"], b["roof_kind"], seed=variant * 7 + len(biome))
    if b["roof_kind"] not in ("spire",):
        cx = x1 - 8 if variant != 1 else x0 + 4
        ctop = top - roof_h - 3
        if b["roof_kind"] == "flat":
            ctop = top - 9
        chimney(s, cx, ctop, roof_h - 2 if b["roof_kind"] != "flat" else 5, b["stone"])
        info["chimney"] = [cx + 2, ctop]
    s.ink()
    s.shadow(W / 2 + 1, floor_y + 1, w / 2 + 4, 2.5)
    return s, info


def gate_tower(biome: str) -> tuple[Sprite, dict]:
    """A square watchtower beside the city gate, with a lit window, battlements and a flag."""
    b = BIOMES[biome]
    W, H = 30, 66
    s = Sprite(W, H)
    x0, x1 = 6, 22
    floor_y = H - 4
    top = 26
    box(s, x0, top, x1, floor_y, b["stone"], side=3, kind="stone", seed=len(biome))
    # battlements
    s.fill(s.rect(x0 - 2, top - 4, x1 + 2, top + 1), b["stone"][3])
    s.fill(s.poly([(x1 + 2, top - 4), (x1 + 5, top - 7), (x1 + 5, top - 2), (x1 + 2, top + 1)]), b["stone"][0])
    for x in range(x0 - 2, x1 + 2, 4):
        s.fill(s.rect(x, top - 7, x + 2, top - 4), b["stone"][3])
        s.px(x, top - 7, b["stone"][4])
    s.line(x0 - 2, top + 1, x1 + 1, top + 1, b["stone"][0])
    window(s, 12, top + 8, 4, 6, b["window"])
    window(s, 12, top + 22, 4, 4, b["window"])
    # flag
    s.line(9, top - 22, 9, top - 7, WOOD_D[2])
    flag = s.poly([(10, top - 22), (19, top - 20), (17, top - 17), (19, top - 14), (10, top - 15)])
    banner = BLOOD if biome != "heart" else ramp("2e4a9a")
    s.part(flag, banner, flat=True)
    s.px(14, top - 18, (220, 190, 90))
    s.ink()
    s.shadow(W / 2 + 1, floor_y + 1, 11, 2.5)
    return s, {"light": [14, top + 10]}


def wall_block(biome: str) -> tuple[Sprite, dict]:
    """A short stretch of town wall with a crenel; a row of them makes a wall in either direction."""
    b = BIOMES[biome]
    W, H = 14, 24
    s = Sprite(W, H)
    floor_y = H - 4
    box(s, 2, 8, 11, floor_y, b["stone"], side=2, kind="stone", seed=3)
    s.fill(s.rect(1, 4, 12, 8), b["stone"][3])
    s.fill(s.rect(4, 2, 8, 4), b["stone"][3])
    s.line(1, 4, 11, 4, b["stone"][4])
    s.ink()
    return s, {}


def lamp_post() -> tuple[Sprite, dict]:
    s = Sprite(10, 30)
    s.fill(s.rect(4, 8, 6, 26), IRON[1])
    s.line(4, 8, 4, 25, IRON[3])
    s.fill(s.rect(3, 24, 7, 26), IRON[2])
    s.fill(s.rect(2, 3, 8, 9), IRON[0])
    s.fill(s.rect(3, 4, 7, 8), (255, 190, 90), glow=True)
    s.fill(s.rect(3, 4, 5, 6), (255, 240, 180), glow=True)
    s.fill(s.rect(2, 1, 8, 3), IRON[2])
    s.ink()
    s.shadow(5, 26, 3, 1.2)
    return s, {"light": [5, 6]}


def well(biome: str) -> tuple[Sprite, dict]:
    b = BIOMES[biome]
    s = Sprite(22, 28)
    s.part(s.ellipse(11, 20, 8, 4), b["stone"])
    s.fill(s.ellipse(11, 19, 5.5, 2.4), (20, 26, 36))
    s.fill(s.rect(3, 6, 5, 21), WOOD[1])
    s.fill(s.rect(17, 6, 19, 21), WOOD[1])
    s.part(s.poly([(1, 7), (11, 1), (21, 7), (19, 8), (11, 3), (3, 8)]), b["roof"], flat=True)
    s.line(5, 9, 17, 9, WOOD[2])
    s.line(11, 9, 11, 14, (90, 80, 60))
    s.fill(s.rect(10, 14, 13, 17), WOOD[2])
    s.ink()
    s.shadow(11, 24, 9, 2)
    return s, {}


def market_stall() -> tuple[Sprite, dict]:
    s = Sprite(28, 28)
    s.fill(s.rect(4, 10, 6, 24), WOOD_D[2])
    s.fill(s.rect(22, 10, 24, 24), WOOD_D[1])
    s.fill(s.rect(3, 17, 25, 21), WOOD[2])
    s.line(3, 17, 24, 17, WOOD[3])
    canopy = s.poly([(1, 11), (27, 11), (24, 4), (4, 4)])
    s.fill(canopy, (130, 40, 36))
    for x in range(3, 26, 4):
        s.fill(s.poly([(x, 11), (x + 2, 11), (x + 1, 4), (x, 4)]) & canopy, (200, 180, 140))
    s.line(1, 11, 26, 11, (90, 26, 24))
    for i, c in enumerate([(160, 50, 40), (200, 160, 60), (100, 140, 60), (150, 90, 160)]):
        s.fill(s.rect(6 + i * 4, 15, 9 + i * 4, 17), c)
    s.ink()
    s.shadow(14, 24, 12, 2)
    return s, {}


def cart() -> tuple[Sprite, dict]:
    s = Sprite(26, 20)
    s.fill(s.rect(3, 6, 20, 12), WOOD[2])
    s.line(3, 6, 19, 6, WOOD[3])
    for x in range(6, 20, 4):
        s.line(x, 7, x, 11, WOOD[1])
    s.line(20, 10, 25, 12, WOOD[1])
    s.part(s.ellipse(8, 13, 3.5, 3.5), WOOD_D)
    s.px(8, 13, IRON[3])
    s.fill(s.ellipse(11, 5, 6, 2.5), (180, 150, 80))                # sacks
    s.fill(s.ellipse(15, 4, 4, 2), (160, 130, 70))
    s.ink()
    s.shadow(12, 16, 11, 1.6)
    return s, {}


def crates() -> tuple[Sprite, dict]:
    s = Sprite(18, 18)
    box(s, 2, 7, 10, 15, WOOD, side=2, kind="plank")
    box(s, 9, 9, 15, 15, WOOD_D, side=2, kind="plank")
    box(s, 4, 2, 10, 7, WOOD, side=2, kind="plank")
    s.ink()
    s.shadow(9, 15, 8, 1.4)
    return s, {}


def paving(biome: str, seed: int) -> Sprite:
    """Ground under a city cell: worn paving stones that fray into the ground at the edges."""
    b = BIOMES[biome]
    tones = b["stone"]
    s = Sprite(38, 38)
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:38, 0:38]
    d = np.maximum(abs(xs - 18.5), abs(ys - 18.5))
    edge = 16.5 + rng.normal(0, 1.4, (38, 38))
    m = d < edge
    s.fill(m, tones[1])
    for y in range(1, 38, 5):
        off = int(rng.integers(0, 5))
        for x in range(-off, 38, 6):
            st = s.rect(x + 1, y + 1, x + 5, y + 4) & m
            s.fill(st, tones[2 + int(rng.integers(0, 2))])
            s.fill(s.rect(x + 1, y + 1, x + 4, y + 2) & m, tones[3])
    return s


def mud(seed: int) -> Sprite:
    """Ground under a camp cell: trampled mud with puddles, ruts and straw."""
    s = Sprite(38, 38)
    rng = np.random.default_rng(seed)
    ys, xs = np.mgrid[0:38, 0:38]
    r = np.hypot(xs - 18.5, ys - 18.5)
    edge = 19.5 + rng.normal(0, 1.8, (38, 38))
    m = (r < edge) & (np.maximum(abs(xs - 18.5), abs(ys - 18.5)) < 17.5 + rng.normal(0, 1.0, (38, 38)))
    tones = ramp("3e3024", spread=0.35)
    s.fill(m, tones[2])
    noise = rng.random((38, 38))
    s.fill(m & (noise < 0.18), tones[1])
    s.fill(m & (noise > 0.9), tones[3])
    for _ in range(2):
        cx, cy = rng.uniform(8, 30, 2)
        p = s.ellipse(cx, cy, rng.uniform(2, 4), rng.uniform(1, 2)) & m
        s.fill(p, (34, 30, 34))
        s.fill(p & s.rect(0, 0, 38, int(cy)), (60, 56, 64))
    for _ in range(6):
        x, y = int(rng.integers(4, 34)), int(rng.integers(4, 34))
        if m[y, x]:
            s.line(x, y, x + int(rng.integers(1, 3)), y - 1, (150, 128, 70))
    return s


# ------------------------------------------------------------------ camp pieces

def tent_a(seed=0) -> tuple[Sprite, dict]:
    """A low ridge tent of stitched dark hides, with a red war stripe and crossed poles."""
    s = Sprite(38, 32)
    hide = HIDE if seed % 2 == 0 else HIDE_D
    floor_y = 28
    # far side of the roof, in shadow, going back up-right
    s.fill(s.poly([(19, 6), (31, 2), (36, floor_y - 6), (30, floor_y)]), hide[0])
    front = s.poly([(4, floor_y), (19, 6), (30, floor_y)])
    s.part(front, hide, flat=True, bias=0.05)
    for i, x in enumerate(range(8, 28, 5)):                          # stitched seams
        s.line(x, floor_y - 1, 19 + (x - 19) // 3, 9, hide[1])
    s.line(7, floor_y - 6, 27, floor_y - 6, BLOOD[2])                # war stripe
    s.line(8, floor_y - 7, 26, floor_y - 7, BLOOD[1])
    s.fill(s.poly([(15, floor_y), (19, 14), (23, floor_y)]), DARK)   # dark opening
    s.line(19, 15, 17, floor_y - 1, hide[1])
    s.line(15, 2, 23, 10, WOOD_D[3])                                 # poles crossing over the ridge
    s.line(23, 2, 15, 10, WOOD_D[2])
    s.line(31, 0, 33, 4, WOOD_D[2])
    s.ink()
    s.shadow(19, floor_y + 1, 16, 2.4)
    return s, {}


def tent_b(seed=0) -> tuple[Sprite, dict]:
    """A tall hide war tent on a ring of poles, a pale skull daubed on the front."""
    s = Sprite(30, 42)
    floor_y = 38
    hide = HIDE_D if seed % 2 == 0 else HIDE
    body = s.poly([(3, floor_y), (14, 6), (16, 6), (27, floor_y)])
    s.part(body, hide, bias=0.0)
    s.fill(s.poly([(16, 6), (27, floor_y), (22, floor_y)]), hide[0])
    for x0 in (8, 14, 20):
        s.line(x0, floor_y - 1, 15, 8, hide[1])
    for dx in (-4, -1, 2, 5):                                        # pole tips through the smoke hole
        s.line(15, 7, 15 + dx, 0, WOOD_D[3])
    s.fill(s.poly([(12, floor_y), (15, floor_y - 12), (18, floor_y)]), DARK)
    # daubed skull
    s.fill(s.ellipse(15, 19, 3.5, 3), BONE[3])
    s.fill(s.rect(13, 21, 18, 24), BONE[3])
    s.pxs([(14, 19), (16, 19)], DARK)
    s.line(13, 23, 17, 23, DARK)
    s.line(4, floor_y - 4, 26, floor_y - 4, BLOOD[2])
    s.ink()
    s.shadow(15, floor_y + 1, 13, 2.4)
    return s, {}


def tent_c() -> tuple[Sprite, dict]:
    """The warlord's great tent: two peaks, a black banner and trophies hung over the door."""
    s = Sprite(48, 46)
    floor_y = 42
    s.fill(s.poly([(24, 10), (40, 6), (46, floor_y - 6), (40, floor_y)]), HIDE_D[0])
    body = s.poly([(3, floor_y), (12, 12), (24, 18), (34, 10), (42, floor_y)])
    s.part(body, HIDE_D, flat=True, bias=0.05)
    for x in range(6, 42, 5):
        s.line(x, floor_y - 1, x + (24 - x) // 4, 16, HIDE_D[1])
    s.line(5, floor_y - 9, 40, floor_y - 9, BLOOD[2])
    s.line(5, floor_y - 10, 40, floor_y - 10, BLOOD[1])
    s.fill(s.poly([(18, floor_y), (22, floor_y - 16), (27, floor_y - 16), (31, floor_y)]), DARK)
    s.line(18, floor_y - 17, 31, floor_y - 17, WOOD_D[3])
    for x in (20, 24, 28):                                           # skulls over the door
        s.fill(s.ellipse(x, floor_y - 19, 1.8, 1.6), BONE[3])
        s.px(x, floor_y - 19, DARK)
    # peaks and banner poles
    s.line(12, 12, 12, 0, WOOD_D[3])
    s.line(34, 10, 34, 0, WOOD_D[3])
    flag = s.poly([(35, 0), (45, 2), (42, 5), (45, 8), (35, 7)])
    s.part(flag, ramp("2a2228", spread=0.3), flat=True)
    s.px(39, 4, BLOOD[3])
    s.px(40, 4, BLOOD[3])
    s.ink()
    s.shadow(23, floor_y + 1, 21, 2.6)
    return s, {}


def stake(seed=0) -> tuple[Sprite, dict]:
    """One sharpened log of the camp's palisade. Rows of them make the wall in either direction."""
    rng = np.random.default_rng(seed)
    h = 20 + int(rng.integers(0, 4))
    s = Sprite(8, h + 6)
    floor_y = h + 2
    s.part(s.rect(2, 5, 6, floor_y), WOOD)
    s.fill(s.poly([(2, 5), (4, 1), (6, 5)]), WOOD[3])
    s.line(4, 1, 5, 5, WOOD[1])
    s.line(2, floor_y - 6, 5, floor_y - 7, (60, 56, 60))             # lashing
    if seed % 3 == 0:
        s.fill(s.ellipse(4, 3, 2.2, 1.9), BONE[3])                   # a skull jammed on the point
        s.pxs([(3, 3), (5, 3)], DARK)
    s.ink()
    return s, {}


def watchtower() -> tuple[Sprite, dict]:
    """A rough log watchtower with a burning brazier on top, beside the camp gate."""
    W, H = 30, 70
    s = Sprite(W, H)
    floor_y = H - 4
    for x0, x1 in ((7, 9), (21, 19)):                                  # legs
        s.part(s.capsule(x0, floor_y, x1, 24, 1.6), WOOD, flat=True)
    s.line(7, floor_y - 6, 21, floor_y - 18, WOOD_D[2])               # cross braces
    s.line(21, floor_y - 6, 7, floor_y - 18, WOOD_D[1])
    s.line(8, floor_y - 24, 20, floor_y - 34, WOOD_D[2])
    s.fill(s.rect(4, 20, 26, 25), WOOD[2])                            # platform
    s.line(4, 20, 25, 20, WOOD[3])
    s.fill(s.rect(5, 12, 25, 20), WOOD_D[2])                          # parapet of hides
    for x in range(6, 25, 3):
        s.line(x, 12, x, 19, WOOD_D[1])
    s.line(5, 15, 24, 15, BLOOD[2])
    s.fill(s.poly([(6, 12), (9, 4), (12, 12)]), WOOD[3])              # spikes
    s.fill(s.poly([(18, 12), (21, 4), (24, 12)]), WOOD[3])
    s.fill(s.rect(11, 7, 19, 12), IRON[1])                            # brazier bowl
    s.line(11, 7, 18, 7, IRON[3])
    s.fill(s.rect(12, 5, 18, 7), FIRE[2], glow=True)
    s.ink()
    s.shadow(W / 2, floor_y + 1, 12, 2.4)
    return s, {"fire": [15, 5]}


def bonfire() -> tuple[Sprite, dict]:
    s = Sprite(22, 14)
    s.part(s.ellipse(11, 9, 9, 3.4), ramp("5a5658", spread=0.45))
    s.fill(s.ellipse(11, 8.5, 6.5, 2.4), (30, 22, 20))
    s.line(5, 9, 16, 6, WOOD_D[2])
    s.line(6, 6, 17, 9, WOOD_D[3])
    s.fill(s.ellipse(11, 8, 3.5, 1.4), FIRE[1], glow=True)
    s.ink()
    return s, {"fire": [11, 6]}


def flame(frame: int) -> Sprite:
    """One of four flame frames for camp fires and burning houses (drawn glowing)."""
    s = Sprite(14, 20)
    rng = np.random.default_rng(frame * 13 + 1)
    sway = [0, 1, 0, -1][frame]
    tips = [(7 + sway, 1 + frame % 2), (4 + sway // 2, 6), (10 + sway, 5 - frame % 2)]
    for i, (tx, ty) in enumerate(tips):
        m = s.poly([(tx, ty), (tx + 3, 12), (tx + 2, 18), (tx - 3, 18), (tx - 3, 12)])
        s.fill(m, FIRE[1], glow=True)
    s.fill(s.poly([(7 + sway, 5), (10, 13), (9, 18), (5, 18), (4, 13)]), FIRE[2], glow=True)
    s.fill(s.poly([(7, 10), (9, 15), (8, 18), (6, 18), (5, 15)]), FIRE[3], glow=True)
    s.px(7, 17, FIRE[4], glow=True)
    for _ in range(2):
        s.px(int(rng.integers(3, 11)), int(rng.integers(0, 6)), FIRE[2], glow=True)
    return s


def war_banner(seed=0) -> tuple[Sprite, dict]:
    """A tall pole with a tattered black war banner and a horned skull on top."""
    s = Sprite(18, 46)
    floor_y = 42
    s.fill(s.rect(4, 6, 6, floor_y), WOOD_D[2])
    s.line(4, 6, 4, floor_y - 1, WOOD_D[3])
    cloth = ramp("2c2026", spread=0.3) if seed % 2 == 0 else BLOOD
    flag = s.poly([(6, 9), (16, 9), (16, 28), (14, 25), (12, 30), (10, 26), (8, 31), (6, 27)])
    s.part(flag, cloth, flat=True)
    s.line(6, 9, 16, 9, WOOD_D[3])
    mark = BLOOD[3] if seed % 2 == 0 else BONE[2]
    s.line(8, 13, 14, 19, mark)                                       # a crossed sigil
    s.line(14, 13, 8, 19, mark)
    s.line(11, 12, 11, 22, mark)
    s.fill(s.ellipse(5, 4, 2.5, 2.2), BONE[3])
    s.pxs([(4, 4), (6, 4)], DARK)
    s.line(2, 3, 1, 0, BONE[2])
    s.line(8, 3, 9, 0, BONE[2])
    s.ink()
    s.shadow(5, floor_y + 1, 4, 1.3)
    return s, {"sways": True}


def war_drum() -> tuple[Sprite, dict]:
    s = Sprite(22, 20)
    s.part(s.rect(3, 6, 19, 16) | s.ellipse(11, 16, 8, 2.5), BLOOD)
    s.part(s.ellipse(11, 6, 8, 2.6), BONE)
    for x in range(4, 19, 3):
        s.line(x, 8, x + 1, 15, BONE[1])
    s.line(15, 2, 18, 6, WOOD[3])
    s.fill(s.ellipse(15, 2, 1.4, 1.4), BONE[3])
    s.ink()
    s.shadow(11, 17, 9, 1.6)
    return s, {}


def weapon_rack() -> tuple[Sprite, dict]:
    s = Sprite(24, 26)
    s.fill(s.rect(3, 10, 5, 22), WOOD_D[2])
    s.fill(s.rect(19, 10, 21, 22), WOOD_D[1])
    s.line(3, 13, 20, 13, WOOD[3])
    s.line(3, 19, 20, 19, WOOD[2])
    for i, x in enumerate(range(6, 19, 3)):
        s.line(x, 21, x + 1, 3 + i % 2 * 2, WOOD[2])
        s.fill(s.poly([(x, 4 + i % 2 * 2), (x + 1, 0 + i % 2 * 2), (x + 2, 4 + i % 2 * 2)]), IRON[3])
    s.ink()
    s.shadow(12, 22, 10, 1.6)
    return s, {}


def cage() -> tuple[Sprite, dict]:
    s = Sprite(22, 28)
    floor_y = 24
    s.fill(s.rect(3, floor_y - 2, 19, floor_y), WOOD_D[1])
    s.fill(s.ellipse(11, floor_y - 4, 4, 2), BONE[2])                # bones inside
    s.line(8, floor_y - 3, 14, floor_y - 5, BONE[3])
    for x in range(4, 19, 3):
        s.line(x, 6, x, floor_y - 2, IRON[2])
    s.line(3, 6, 18, 6, IRON[3])
    s.fill(s.poly([(3, 6), (11, 1), (19, 6)]), IRON[1])
    s.line(11, 0, 11, 1, IRON[3])
    s.ink()
    s.shadow(11, floor_y + 1, 9, 1.6)
    return s, {}


# ------------------------------------------------------------------ people

def person(frame: int, clothes, skin, hair, kind="folk") -> Sprite:
    """A small figure walking right. frame 0..3 walks; kind folk, hooded (camp sentry) or guard."""
    s = Sprite(16, 28)
    step = [0, 1, 0, -1][frame]
    bob = 1 if frame % 2 else 0
    hip = 18 - bob
    # legs
    legs = STEEL if kind == "guard" else (clothes if kind == "hooded" else ramp("3a3030", spread=0.35))
    s.part(s.capsule(7, hip, 7 - step * 2, 24, 1.3), legs, bias=-0.25)
    s.part(s.capsule(9, hip, 9 + step * 2, 24, 1.4), legs)
    # body
    body_tones = clothes if kind != "guard" else RED
    s.part(s.poly([(5, 10 - bob), (11, 10 - bob), (12, hip + 2), (4, hip + 2)]), body_tones)
    if kind == "folk":
        s.line(4, hip, 11, hip, (60, 44, 30))
    if kind == "guard":
        s.fill(s.rect(5, 10 - bob, 11, 12 - bob), STEEL[2])
    # arm
    s.part(s.capsule(8, 12 - bob, 8 + step * 2, 17 - bob, 1.2), body_tones, bias=-0.05)
    # head
    hy = 7 - bob
    if kind == "hooded":
        s.part(s.ellipse(8, hy, 3.6, 3.8) | s.poly([(4, hy), (12, hy), (10, hy + 4), (6, hy + 4)]), clothes)
        s.fill(s.ellipse(9.5, hy + 0.5, 1.8, 2.0), DARK)
        s.px(10, hy, (255, 70, 40), glow=True)
    elif kind == "guard":
        s.part(s.ellipse(8, hy, 3.4, 3.6), STEEL)
        s.fill(s.rect(8, hy - 1, 12, hy), DARK)
        s.fill(s.poly([(5, hy - 4), (2, hy - 6), (4, hy - 2)]), RED[3])
    else:
        s.part(s.ellipse(8, hy, 3.0, 3.2), skin)
        s.fill(s.ellipse(7.2, hy - 1.5, 3.0, 2.0) & ~s.rect(9, hy - 1, 12, hy + 3), hair)
        s.px(10, hy, DARK)
    if kind == "hooded":                                              # spear
        s.line(12, 2 - bob, 12, 22, WOOD_D[3])
        s.fill(s.poly([(11, 3 - bob), (12, -1 - bob + 1), (13, 3 - bob)]), IRON[3])
    if kind == "guard":
        s.line(12, 1 - bob, 12, 22, WOOD[3])
        s.px(12, 0 - bob + 1, STEEL[4])
    s.ink()
    s.shadow(8, 25, 4.5, 1.3)
    return s


def people_strips() -> dict[str, list[Sprite]]:
    strips = {}
    for i in range(5):
        strips[f"folk_{i}"] = [person(f, CLOTH[i], SKIN[i % len(SKIN)], HAIR[i]) for f in range(4)]
    strips["guard"] = [person(f, CLOTH[0], SKIN[0], HAIR[0], "guard") for f in range(4)]
    strips["sentry_0"] = [person(f, ramp("2e2a30", spread=0.35), SKIN[0], HAIR[0], "hooded") for f in range(4)]
    strips["sentry_1"] = [person(f, ramp("4a1e22", spread=0.35), SKIN[0], HAIR[0], "hooded") for f in range(4)]
    return strips


# ------------------------------------------------------------------ output

def glow_image(s: Sprite) -> Image.Image | None:
    if not s.glow.any():
        return None
    al = (s.glow & s.a).astype(np.uint8) * 255
    return Image.fromarray(np.dstack([s.rgb, al]), "RGBA")


def save_piece(out: str, name: str, s: Sprite, meta: dict, info: dict) -> Image.Image:
    im = s.image()
    im.save(os.path.join(out, name + ".png"))
    s.normal_image().save(os.path.join(out, name + "_n.png"))
    g = glow_image(s)
    entry = {"size": [im.width, im.height]}
    if g is not None:
        g.save(os.path.join(out, name + "_glow.png"))
        entry["glow"] = True
    entry.update({k: v for k, v in meta.items() if v is not None and v != []})
    info[name] = entry
    return im


def save_strip(out: str, name: str, frames: list[Sprite], info: dict) -> Image.Image:
    w, h = frames[0].w, frames[0].h
    im = Image.new("RGBA", (w * len(frames), h))
    nm = Image.new("RGBA", (w * len(frames), h))
    gl = Image.new("RGBA", (w * len(frames), h))
    has_glow = False
    for i, f in enumerate(frames):
        im.paste(f.image(), (i * w, 0))
        nm.paste(f.normal_image(), (i * w, 0))
        g = glow_image(f)
        if g is not None:
            gl.paste(g, (i * w, 0))
            has_glow = True
    im.save(os.path.join(out, name + ".png"))
    nm.save(os.path.join(out, name + "_n.png"))
    entry = {"size": [w, h], "frames": len(frames)}
    if has_glow:
        gl.save(os.path.join(out, name + "_glow.png"))
        entry["glow"] = True
    info[name] = entry
    return im


def ground_image(s: Sprite) -> Image.Image:
    im = s.image()
    return im


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet", default="", help="also write a labelled review sheet here")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    info: dict = {}
    sheet: list[tuple[str, Image.Image]] = []

    def piece(name, made):
        s, meta = made
        sheet.append((name, save_piece(a.out, name, s, meta, info)))

    # camp
    piece("tent_a0", tent_a(0))
    piece("tent_a1", tent_a(1))
    piece("tent_b0", tent_b(0))
    piece("tent_b1", tent_b(1))
    piece("tent_c", tent_c())
    for i in range(4):
        piece(f"stake_{i}", stake(i))
    piece("watchtower", watchtower())
    piece("bonfire", bonfire())
    piece("banner_0", war_banner(0))
    piece("banner_1", war_banner(1))
    piece("drum", war_drum())
    piece("rack", weapon_rack())
    piece("cage", cage())
    sheet.append(("flame", save_strip(a.out, "flame", [flame(i) for i in range(4)], info)))
    for i in range(3):
        m = mud(40 + i)
        m.image().save(os.path.join(a.out, f"mud_{i}.png"))
        info[f"mud_{i}"] = {"size": [m.w, m.h]}
        sheet.append((f"mud_{i}", m.image()))
    # city
    for biome in BIOMES:
        for v in range(3):
            piece(f"house_{biome}_{v}", house(biome, v))
        piece(f"gatetower_{biome}", gate_tower(biome))
        piece(f"wall_{biome}", wall_block(biome))
        piece(f"well_{biome}", well(biome))
        for i in range(2):
            p = paving(biome, 70 + i)
            p.image().save(os.path.join(a.out, f"paving_{biome}_{i}.png"))
            info[f"paving_{biome}_{i}"] = {"size": [p.w, p.h]}
            if i == 0:
                sheet.append((f"paving_{biome}_{i}", p.image()))
    piece("lamp", lamp_post())
    piece("stall", market_stall())
    piece("cart", cart())
    piece("crates", crates())
    for name, frames in people_strips().items():
        sheet.append((name, save_strip(a.out, name, frames, info)))

    with open(os.path.join(a.out, "landmarks.json"), "w") as fh:
        json.dump({"biomes": list(BIOMES), "pieces": info}, fh, indent=1, sort_keys=True)
    print(f"{len(info)} pieces -> {a.out}")
    if a.sheet:
        write_sheet(sheet, a.sheet)


def write_sheet(items, path, zoom=4, cols=8):
    from PIL import ImageDraw
    cell_w = max(im.width for _, im in items) * zoom + 16
    cell_h = max(im.height for _, im in items) * zoom + 28
    rows = math.ceil(len(items) / cols)
    sheet = Image.new("RGBA", (cell_w * cols, cell_h * rows), (52, 62, 46, 255))
    d = ImageDraw.Draw(sheet)
    for i, (name, im) in enumerate(items):
        x, y = (i % cols) * cell_w, (i // cols) * cell_h
        big = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
        sheet.alpha_composite(big, (x + 8, y + 4))
        d.text((x + 8, y + cell_h - 20), name, fill=(240, 236, 220))
    sheet.save(path)


if __name__ == "__main__":
    main()
