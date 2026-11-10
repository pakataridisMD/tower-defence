#!/usr/bin/env python3
"""Generates the pixel art for the interface: panels, buttons, skill icons, and the main menu's
backdrop and title.

Writes to assets/art/ui/:
  panel.png                  9-slice panel frame, already doubled (8 px margins)
  button_<state>.png         9-slice buttons, already doubled: normal, hover, pressed, disabled, picked
  skill_<skill_id>.png       one icon per skill in data/skills, already doubled (36x36)
  menu_backdrop.png          640x360 night scene for the main menu, shown at 3x: the six base towers
                             on their ring, lit by their own lights, and a wave marching past
  logo.png                   the title in pixel letters, shown at 3x

The backdrop is built from the game's own art (assets/art/game), so run tools/art/gen_game_art.py
first if the towers or enemies changed.

Run from the repository root:  python3 tools/art/gen_ui_art.py
Needs numpy and Pillow. The output is deterministic.
"""
from __future__ import annotations

import glob
import hashlib
import json
import math
import os
import re
import sys
import tempfile

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_game_art as game  # noqa: E402  (the ground painter)
from gen_lighting_demo import hexc  # noqa: E402
from gen_tree_art import BRONZE, INK, bayer, dilate  # noqa: E402

OUT = os.path.join("assets", "art", "ui")
GAME_ART = os.path.join("assets", "art", "game")
CLEAR = None


def save(name: str, rgb: np.ndarray, alpha: np.ndarray, scale: int = 1) -> None:
    img = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 255)]).astype(np.uint8)
    im = Image.fromarray(img, "RGBA")
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(os.path.join(OUT, name + ".png"))


def edge_distance(size: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ys, xs = np.mgrid[0:size, 0:size]
    return np.minimum(np.minimum(xs, ys), np.minimum(size - 1 - xs, size - 1 - ys)), xs, ys


# --------------------------------------------------------------------------- panel and buttons

def make_panel() -> None:
    """Dark slate with a bronze rim, like the tooltip panel of the skill trees."""
    size = 16
    edge, xs, ys = edge_distance(size)
    rgb = np.zeros((size, size, 3), np.float32)
    alpha = np.full((size, size), 255.0)
    rgb[:] = hexc("191b27")
    rgb[edge == 0] = INK
    rgb[edge == 1] = BRONZE[3]
    rgb[(edge == 1) & ((xs == size - 2) | (ys == size - 2))] = BRONZE[1]
    rgb[edge == 2] = BRONZE[1]
    rgb[(edge == 2) & ((xs == size - 3) | (ys == size - 3))] = BRONZE[0]
    rgb[edge == 3] = hexc("11121a")
    for cx, cy in ((1, 1), (size - 2, 1), (1, size - 2), (size - 2, size - 2)):
        rgb[cy, cx] = BRONZE[5]
    for cx, cy in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        alpha[cy, cx] = 0
    save("panel", rgb, alpha, scale=2)


# Each state: outline, top light, body, bottom shade, lip under the body.
BUTTONS = {
    "normal": ("0e0f16", "666e90", "3a4058", "2f3449", "20232f"),
    "hover": ("0e0f16", "8e98c2", "4a5273", "3b425e", "272b3b"),
    "pressed": ("0e0f16", "171a24", "2a2e41", "2f3449", "343a50"),
    "disabled": ("14151c", "30344a", "262938", "22242f", "1b1c25"),
    "picked": ("f2c14e", "8e98c2", "4a5273", "3b425e", "8a5e1e"),
}


def make_button(state: str) -> None:
    outline_c, light_c, body_c, shade_c, lip_c = (hexc(c) for c in BUTTONS[state])
    size = 12
    edge, xs, ys = edge_distance(size)
    rgb = np.zeros((size, size, 3), np.float32)
    alpha = np.full((size, size), 255.0)
    rgb[:] = body_c
    rgb[edge == 0] = outline_c
    inside = edge >= 1
    rgb[inside & (ys == 1)] = light_c
    rgb[inside & (ys == size - 3)] = shade_c
    rgb[inside & (ys == size - 2)] = lip_c
    # A lighter left edge and a darker right one, so the button looks cut from one block.
    rgb[inside & (xs == 1) & (ys > 1) & (ys < size - 2)] = body_c * 1.12
    rgb[inside & (xs == size - 2) & (ys > 1) & (ys < size - 2)] = shade_c
    for cx, cy in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        alpha[cy, cx] = 0
    for cx, cy in ((1, 1), (size - 2, 1), (1, size - 2), (size - 2, size - 2)):
        rgb[cy, cx] = outline_c
    save("button_" + state, rgb, alpha, scale=2)


# --------------------------------------------------------------------------- skill icons

SKILL_ICONS = {
    "meteor": ({"d": "c0401a", "o": "ff8a3a", "y": "ffd060", "w": "fff2c0", "R": "9a6a58", "r": "5a3a30"}, [
        "............dd..",
        "..........ddod..",
        ".........dooyd..",
        "........dooyod..",
        ".......dooyyo...",
        "......dooyyod...",
        ".....doyywyo....",
        "....doyywwyd....",
        "...doyRRRwyd....",
        "..doyRRRRRo.....",
        "..dyRRRrRRRd....",
        "..doRRrrrRRd....",
        "..dorRRrrRr.....",
        "...drrRRrr......",
        "....drrrr.......",
        "................",
    ]),
    "surge": ({"y": "ffe27a", "w": "fff8d0", "b": "9ac8ff"}, [
        "................",
        ".......yyyyy....",
        "......ywwwy.....",
        ".....ywwwy......",
        "....ywwwy...b...",
        "...ywwwyyyy.....",
        "..ywwwwwwwy.....",
        "..yyyywwwy...b..",
        ".....ywwy.......",
        ".b..ywwy........",
        "....ywy.........",
        "...ywy....b.....",
        "...yy...........",
        "..yy............",
        "..y.............",
        "................",
    ]),
    "entangle": ({"g": "5aa02a", "G": "9ae04a", "d": "2a5a1a", "t": "d8ff8a"}, [
        "................",
        "....g......G....",
        "...gGg....gGg...",
        "...dg......gd...",
        "....g..t...g....",
        "....gg....gg....",
        "..t..gg..gg..t..",
        "......gggg......",
        "....t.gGGg.t....",
        "......gggg......",
        ".....gg..gg.....",
        "..t.gg....gg.t..",
        "...gg..t...gg...",
        "..gGg......gGg..",
        "..dg........gd..",
        "................",
    ]),
    "tidal_wave": ({"w": "eafaff", "l": "a8e0f0", "m": "54a8d4", "d": "2f7fb0", "k": "1d4f7a"}, [
        "................",
        "................",
        ".....wwwww......",
        "...wwlllllww....",
        "..wllmmmmmllw...",
        ".wlmmmddmmmmlw..",
        ".wlmd....dmmlw..",
        ".wlw......dmmlw.",
        "..w.......dmmlw.",
        ".........ddmmlw.",
        "........ddmmmlw.",
        "w.....dddmmmmlw.",
        "lw.wdddmmmmmmllw",
        "mlwlmmmmmmmmmmll",
        "dmmmmmmmmmmmmmmm",
        "kddddddddddddddk",
    ]),
    "earthquake": ({"a": "c4ae8c", "s": "8a725a", "d": "56423a", "k": "3e2f26", "c": "1a1410"}, [
        "................",
        ".......a........",
        "......asa.......",
        "..a...asd...a...",
        ".asa.aassd.asa..",
        ".assaasssdaassd.",
        ".asssassssasssd.",
        "aassssscsssssssd",
        "asssscscssscsssd",
        "assscsssccsssssd",
        "adsscssssscssddk",
        "adddcsdddsscdddk",
        "kddddcddddcdddkk",
        "kkdddddddddddkk.",
        ".kkkkkkkkkkkkk..",
        "................",
    ]),
    "doom": ({"w": "f4e8ff", "l": "c8a0ff", "m": "8e5cd9", "d": "5a2a98", "k": "2a1048"}, [
        "................",
        ".....llllll.....",
        "...llwwwwwwll...",
        "..lwwwwwwwwwwl..",
        "..lwwwwwwwwwwl..",
        ".lwwwwwwwwwwwwm.",
        ".lwkkkwwwwkkkwm.",
        ".lwkkkkwwkkkkwm.",
        ".lwwkkkwwkkkwwm.",
        "..lwwwwkkwwwwm..",
        "..mlwwwkkwwwmm..",
        "...mlwwwwwwmm...",
        "...mlwkwkwkmd...",
        "...mlwkwkwkmd...",
        "....mmmmmmmd....",
        "................",
    ]),
}


def make_skill_icon(name: str) -> None:
    palette, rows = SKILL_ICONS[name]
    assert len(rows) == 16 and all(len(r) == 16 for r in rows), name
    size = 18
    rgb = np.zeros((size, size, 3), np.float32)
    mask = np.zeros((size, size), bool)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                rgb[y + 1, x + 1] = hexc(palette[ch])
                mask[y + 1, x + 1] = True
    ink = dilate(mask, diagonal=False) & ~mask
    rgb[ink] = INK
    save("skill_" + name, rgb, np.where(mask | ink, 255, 0), scale=2)


# --------------------------------------------------------------------------- logo

FONT = {
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
}
LOGO_GOLD = [hexc(c) for c in ("fff6d0", "ffe08a", "f2c14e", "d89a32", "a86a22")]
LOGO_BLUE = [hexc(c) for c in ("f0f8ff", "bfe0ff", "7ab8f0", "4a86d0", "2f5aa0")]


def make_logo(text: str = "TOWER DEFENCE 2D", accent_from: int = 14) -> None:
    """Chunky letters, three art pixels to a letter pixel, gold with the last word in blue."""
    unit = 3
    columns: list[tuple[np.ndarray, bool]] = []
    for index, ch in enumerate(text):
        if ch == " ":
            columns.append((np.zeros((7, 3), bool), False))
            continue
        glyph = np.array([[c == "#" for c in row] for row in FONT[ch]])
        columns.append((glyph, index >= accent_from))
        columns.append((np.zeros((7, 1), bool), False))
    width = sum(c.shape[1] for c, _ in columns) * unit
    pad = 3
    H, W = 7 * unit + pad * 2 + 3, width + pad * 2
    mask = np.zeros((H, W), bool)
    accent = np.zeros((H, W), bool)
    x = pad
    for glyph, is_accent in columns:
        big = np.kron(glyph, np.ones((unit, unit), bool))
        mask[pad:pad + 7 * unit, x:x + big.shape[1]] = big
        accent[pad:pad + 7 * unit, x:x + big.shape[1]] = is_accent
        x += big.shape[1]
    ys = np.mgrid[0:H, 0:W][0]
    t = np.clip((ys - pad) / (7 * unit - 1), 0, 1)
    band = np.clip((t * 4.0 + (bayer(H, W) - 0.5) * 0.9 + 0.5).astype(int), 0, 4)
    rgb = np.where(accent[..., None], np.stack(LOGO_BLUE)[band], np.stack(LOGO_GOLD)[band]).astype(np.float32)
    # A bright top edge on every stroke.
    top = mask & ~np.roll(mask, 1, 0)
    rgb[top] = 255.0
    alpha = np.where(mask, 255.0, 0.0)
    ink = dilate(mask) & ~mask
    rgb[ink] = INK
    alpha[ink] = 255.0
    solid = mask | ink
    shadow = np.roll(solid, 2, 0) & ~solid
    rgb[shadow] = hexc("05050a")
    alpha[shadow] = 150.0
    save("logo", rgb, alpha)


# --------------------------------------------------------------------------- menu backdrop

BACKDROP_SIZE = (640, 360)
# The ring the six base towers stand on, in backdrop pixels. scripts/ui/main_menu.gd uses the same
# numbers to write the element names under them.
RING_CENTER = (452.0, 168.0)
RING_RADII = (104.0, 70.0)
RING_TOWERS = ["fire_brazier", "storm_spire", "nature_thornbush", "water_wellspring", "earth_monolith", "void_obelisk"]
ROAD_ROW = 9
ROAD_COLUMN = 18
NIGHT = np.array([0.40, 0.47, 0.76])
# The wave on the road: (enemy, x, y offset, on the upward stretch).
MARCH = [
    ("runner", 224, 2, False), ("grunt", 252, -3, False), ("grunt", 276, 4, False), ("warden", 304, 0, False),
    ("grunt", 334, -4, False), ("grunt", 356, 3, False), ("brute", 386, 0, False), ("grunt", 416, 4, False),
    ("mender", 440, -3, False), ("grunt", 466, 2, False), ("leviathan", 512, 2, False), ("grunt", 556, -2, False),
    ("runner", 0, 262, True), ("grunt", 0, 226, True), ("grunt", 0, 196, True), ("brute", 0, 150, True),
    ("grunt", 0, 108, True), ("runner", 0, 66, True),
]


def load_rgba(path: str) -> np.ndarray:
    return np.asarray(Image.open(path).convert("RGBA")).astype(np.float32)


def blend(canvas: np.ndarray, sprite: np.ndarray, left: int, top: int, additive: bool = False) -> None:
    """Draws an RGBA sprite on an RGB canvas, clipped to it."""
    h, w = sprite.shape[:2]
    x0, y0 = max(left, 0), max(top, 0)
    x1, y1 = min(left + w, canvas.shape[1]), min(top + h, canvas.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    part = sprite[y0 - top:y1 - top, x0 - left:x1 - left]
    a = part[..., 3:4] / 255.0
    target = canvas[y0:y1, x0:x1]
    if additive:
        target += part[..., :3] * a
    else:
        target[:] = target * (1 - a) + part[..., :3] * a


def stamp(mask: np.ndarray, alpha: np.ndarray, left: int, top: int, value: float) -> None:
    """Raises a mask to `value` wherever a sprite with this alpha would be drawn."""
    h, w = alpha.shape
    x0, y0 = max(left, 0), max(top, 0)
    x1, y1 = min(left + w, mask.shape[1]), min(top + h, mask.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    solid = alpha[y0 - top:y1 - top, x0 - left:x1 - left] > 128
    target = mask[y0:y1, x0:x1]
    target[solid] = np.maximum(target[solid], value)


def element_colors() -> dict[str, np.ndarray]:
    colors = {}
    for path in glob.glob("data/elements/*.tres"):
        text = open(path).read()
        eid = re.search(r'^id = &"(\w+)"', text, re.M).group(1)
        r, g, b = (float(v) for v in re.search(r"^color = Color\(([\d.]+), ([\d.]+), ([\d.]+)", text, re.M).groups())
        colors[eid] = np.array([r, g, b]) * 255.0
    return colors


def ring_point(index: int) -> tuple[float, float]:
    angle = -math.pi / 2 + 2 * math.pi * index / 6
    return RING_CENTER[0] + math.cos(angle) * RING_RADII[0], RING_CENTER[1] + math.sin(angle) * RING_RADII[1]


def make_backdrop() -> None:
    W, H = BACKDROP_SIZE
    with open(os.path.join(GAME_ART, "art.json")) as fh:
        art = json.load(fh)
    # The ground comes from the game's own painter: a road along the bottom that turns up the right side.
    menu_map = {"id": "menu", "grid": (20, 12), "cell": 64, "biome": "meadow",
                "waypoints": [(-1, ROAD_ROW), (ROAD_COLUMN, ROAD_ROW), (ROAD_COLUMN, -1)]}
    menu_map["lanes"] = [menu_map["waypoints"]]
    real_out = game.OUT
    with tempfile.TemporaryDirectory() as scratch:
        game.OUT = scratch
        try:
            game.make_ground(menu_map, art["props"])
        finally:
            game.OUT = real_out
        ground = load_rgba(os.path.join(scratch, "ground", "menu.png"))[:H, :W, :3].copy()
        with open(os.path.join(scratch, "ground", "menu.json")) as fh:
            props = json.load(fh)["props"]

    feet = [ring_point(i) for i in range(6)]
    road_y = (ROAD_ROW + 0.5) * 32
    road_x = (ROAD_COLUMN + 0.5) * 32
    tint = element_colors()["water"] / 255.0 * 0.7 + 0.3

    # Everything that stands on the ground, drawn from the back to the front.
    things: list[tuple[float, str, tuple]] = []
    for prop in props:
        px, py = prop["pos"]
        if py >= H + 4 or any(math.hypot(px - fx, (py - fy) * 1.6) < 26 for fx, fy in feet):
            continue
        things.append((py, "prop", (prop["kind"], px, py, prop["flip"])))
    for index, tower_id in enumerate(RING_TOWERS):
        things.append((feet[index][1], "tower", (tower_id, feet[index])))
    for enemy_id, x, y, upward in MARCH:
        foot = (road_x + (x - 2 if y % 2 else x + 3), float(y)) if upward else (float(x), road_y + y + 4)
        things.append((foot[1], "enemy", (enemy_id, foot)))
    things.sort(key=lambda entry: entry[0])

    canvas = ground
    glow = np.zeros((H, W, 3), np.float32)
    # Towers and enemies never go as dark as the grass, so they read against the night.
    floor = np.zeros((H, W), np.float32)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)

    def shadow(cx: float, cy: float, rx: float, ry: float) -> None:
        inside = ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0
        canvas[inside] *= 0.62

    for _, kind, data in things:
        if kind == "tower":
            shadow(data[1][0], data[1][1] - 1, 15, 5)
        elif kind == "enemy":
            size = art["enemies"][data[0]]["size"]
            shadow(data[1][0], data[1][1] - 1, size[0] * 0.42, max(2.0, size[0] * 0.12))
    for _, kind, data in things:
        if kind == "prop":
            name, px, py, flip = data
            sprite = load_rgba(os.path.join(GAME_ART, "props", name + ".png"))
            if flip:
                sprite = sprite[:, ::-1]
            blend(canvas, sprite, int(px) - sprite.shape[1] // 2, int(py) - sprite.shape[0] + 1)
        elif kind == "tower":
            tower_id, (fx, fy) = data
            anchor = art["towers"][tower_id]["anchor"]
            left, top = int(round(fx)) - anchor[0], int(round(fy)) - anchor[1]
            sprite = load_rgba(os.path.join(GAME_ART, "towers", tower_id + ".png"))
            blend(canvas, sprite, left, top)
            stamp(floor, sprite[..., 3], left, top, 0.9)
            glow_path = os.path.join(GAME_ART, "towers", tower_id + "_glow.png")
            if os.path.exists(glow_path):
                blend(glow, load_rgba(glow_path), left, top, additive=True)
        else:
            enemy_id, (fx, fy) = data
            meta = art["enemies"][enemy_id]
            frame = (int(fx) // 7) % meta.get("frames", 4)
            left, top = int(round(fx)) - meta["anchor"][0], int(round(fy)) - meta["anchor"][1]
            body = load_rgba(os.path.join(GAME_ART, "enemies", "%s_%d.png" % (enemy_id, frame)))
            body[..., :3] *= tint
            blend(canvas, body, left, top)
            stamp(floor, body[..., 3], left, top, 0.95)
            gear_path = os.path.join(GAME_ART, "enemies", "%s_gear_%d.png" % (enemy_id, frame))
            if os.path.exists(gear_path):
                blend(canvas, load_rgba(gear_path), left, top)
            gear_glow = os.path.join(GAME_ART, "enemies", "%s_gear_%d_glow.png" % (enemy_id, frame))
            if os.path.exists(gear_glow):
                blend(glow, load_rgba(gear_glow), left, top, additive=True)

    # Night, and the pool of light around every tower. The light is stepped and dithered so it keeps
    # the look of the pixels under it.
    light = np.ones((H, W, 3), np.float32) * NIGHT
    dither = bayer(H, W) - 0.5
    for index, tower_id in enumerate(RING_TOWERS):
        meta = art["towers"][tower_id].get("light", {})
        color = hexc(meta.get("color", "#ffffff")) / 255.0
        reach = float(meta.get("range", 100)) * 0.95
        fx, fy = feet[index]
        d = np.hypot(xx - fx, (yy - (fy - 8)) * 1.45) / reach
        fall = np.clip(1.0 - d, 0.0, 1.0) ** 1.4
        fall = np.floor(fall * 8.0 + dither * 0.7 + 0.5) / 8.0
        light += fall[..., None] * color * (0.95 + 0.6 * float(meta.get("energy", 1.0)))
    # A faint ring of lights on the grass through the six towers, and lines between opposites.
    marks = np.zeros((H, W), np.float32)
    for k in range(90):
        angle = 2 * math.pi * k / 90
        px = int(round(RING_CENTER[0] + math.cos(angle) * RING_RADII[0]))
        py = int(round(RING_CENTER[1] + math.sin(angle) * RING_RADII[1]))
        marks[py, px] = 0.8
        marks[py, px + 1] = 0.45
    for a in range(3):
        (ax, ay), (bx, by) = feet[a], feet[a + 3]
        for k in range(8, 93):
            if k % 6 < 2:
                marks[int(round(ay + (by - ay) * k / 100)), int(round(ax + (bx - ax) * k / 100))] = 0.4
    lit = canvas * np.clip(np.maximum(light, floor[..., None]), 0.0, 1.3)
    lit += marks[..., None] * np.array([190.0, 215.0, 255.0])
    lit += glow

    # Fireflies over the grass.
    rng = np.random.default_rng(7)
    for _ in range(46):
        x, y = int(rng.integers(4, W - 4)), int(rng.integers(6, H - 6))
        if abs(y - road_y) < 20 or abs(x - road_x) < 20:
            continue
        lit[y, x] = hexc("eaff9a")
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            lit[y + dy, x + dx] = lit[y + dy, x + dx] * 0.55 + hexc("9ac84a") * 0.45

    # Darker toward the edges, and under the menu on the left.
    edge = np.minimum(np.minimum(xx, W - 1 - xx) / 90.0, np.minimum(yy, H - 1 - yy) / 60.0)
    shade = 0.66 + 0.34 * np.clip(edge, 0.0, 1.0)
    shade *= 0.55 + 0.45 * np.clip((xx - 150.0) / 130.0, 0.0, 1.0)
    lit *= shade[..., None]
    save("menu_backdrop", lit, np.full((H, W), 255.0))


# --------------------------------------------------------------------------- import files

def write_missing_imports() -> int:
    """Gives every new picture the Godot import file the game art has (no mipmaps, lossless)."""
    template_path = os.path.join(GAME_ART, "towers", "fire_brazier.png.import")
    with open(template_path) as fh:
        template = fh.read()
    old_res = "res://assets/art/game/towers/fire_brazier.png"
    old_hash = hashlib.md5(old_res.encode()).hexdigest()
    old_uid = re.search(r'uid="(uid://\w+)"', template).group(1)
    alphabet = "abcdefghijklmnopqrstuvwxy012345678"
    written = 0
    for path in sorted(glob.glob(os.path.join(OUT, "*.png"))):
        if os.path.exists(path + ".import"):
            continue
        res = "res://" + path.replace(os.sep, "/")
        digest = hashlib.md5(res.encode()).hexdigest()
        number = int(hashlib.sha1(res.encode()).hexdigest(), 16)
        uid = "uid://" + alphabet[number % 25] + "".join(alphabet[(number >> (5 * k)) % 34] for k in range(1, 13))
        text = template.replace(old_res, res).replace("fire_brazier.png-" + old_hash, os.path.basename(path) + "-" + digest)
        with open(path + ".import", "w") as fh:
            fh.write(text.replace(old_uid, uid))
        written += 1
    return written


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    make_panel()
    for state in BUTTONS:
        make_button(state)
    skill_ids = sorted(os.path.splitext(os.path.basename(p))[0] for p in glob.glob("data/skills/*.tres"))
    for skill_id in skill_ids:
        if skill_id not in SKILL_ICONS:
            raise SystemExit("No icon drawn for the skill '%s': add it to SKILL_ICONS" % skill_id)
        make_skill_icon(skill_id)
    make_logo()
    make_backdrop()
    print("Wrote the interface art in", OUT, "and", write_missing_imports(), "import files")


if __name__ == "__main__":
    main()
