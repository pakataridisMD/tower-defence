#!/usr/bin/env python3
"""Generates the pixel art for the skill trees (the in-run skill web and the meta tree).

Same pixel size as the board: one art pixel is drawn as 2x2 screen pixels.

Writes to assets/art/game/tree/:
  frame_<style>.png      socket frames, untinted: start, minor, notable, keystone, bridge, portrait
  gem_<style>.png        the coloured centre, drawn light grey so the game can tint it with the
                         region's colour; gem_<style>_left/_right for nodes that join two regions
  shine_<style>.png      white highlights drawn over the tinted gem
  halo_<style>.png       a ring that follows the frame's shape, pulsed on nodes you can take
  icon_<name>.png        12x12 icons for what a node does, and the region emblems
  glow.png, aura.png     dithered round glows, tinted at runtime (taken nodes, region auras)
  sparkle.png            a four-pointed twinkle
  backdrop.png           960x540 starry night behind the tree
  panel.png              9-slice tooltip panel, already doubled (12 px margins)

Run from the repository root:  python3 tools/art/gen_tree_art.py
Needs numpy and Pillow. The output is deterministic.
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_lighting_demo import fbm, hexc  # noqa: E402  (shared helpers)

OUT = os.path.join("assets", "art", "game", "tree")
RNG = np.random.default_rng(11)

INK = hexc("0c0b10")
STONE = [hexc(c) for c in ("2a2833", "3d3a47", "55515f", "726d7c", "958f9e", "bdb7c4")]
BRONZE = [hexc(c) for c in ("3b2a1a", "6b4a28", "9a6e38", "c9a35a", "efd58e", "fff4c8")]
GOLD = [hexc(c) for c in ("4a3214", "8a5e1e", "c08a2a", "e8bd4e", "fff0a0", "ffffff")]
SILVER = [hexc(c) for c in ("2e2f3a", "5a5d6e", "8c90a2", "c4c8d6", "eef0f8", "ffffff")]

# Icon palette: cream with a stone shade, so icons read on any gem colour.
ICON_COLORS = {
    "h": hexc("ffffff"),
    "w": hexc("f2e8d0"),
    "s": hexc("c2b394"),
    "d": hexc("8a7a62"),
}
ICON_OUTLINE = hexc("17141c")

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]], dtype=np.float32) / 16.0 + 1.0 / 32.0


def bayer(h: int, w: int) -> np.ndarray:
    return np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]


def save(name: str, rgb: np.ndarray, alpha: np.ndarray, scale: int = 1) -> None:
    img = np.dstack([np.clip(rgb, 0, 255), np.clip(alpha, 0, 255)]).astype(np.uint8)
    im = Image.fromarray(img, "RGBA")
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    im.save(os.path.join(OUT, name + ".png"))


def grid(size: int) -> tuple[np.ndarray, np.ndarray]:
    """Pixel-centre coordinates relative to the middle of a size x size image."""
    ys, xs = np.mgrid[0:size, 0:size].astype(np.float32)
    c = size / 2.0
    return xs + 0.5 - c, ys + 0.5 - c


def dilate(mask: np.ndarray, diagonal: bool = True) -> np.ndarray:
    out = mask.copy()
    shifts = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    if diagonal:
        shifts += [(1, 1), (1, -1), (-1, 1), (-1, -1)]
    for dy, dx in shifts:
        out |= np.roll(np.roll(mask, dy, 0), dx, 1)
    return out


def ramp(colors: list[np.ndarray], t: np.ndarray) -> np.ndarray:
    idx = np.clip((t * (len(colors) - 1) + 0.5).astype(int), 0, len(colors) - 1)
    return np.stack(colors)[idx]


def light(xs: np.ndarray, ys: np.ndarray) -> np.ndarray:
    """0 at the bottom right, 1 at the top left, from the direction of a pixel."""
    d = np.sqrt(xs * xs + ys * ys) + 1e-6
    return np.clip(0.5 + 0.5 * (-(xs * 0.6 + ys * 0.8) / d), 0.0, 1.0)


# --------------------------------------------------------------------------- shapes

def shape_mask(style: str, size: int, inset: float) -> np.ndarray:
    """The node's outline shape shrunk by inset pixels: round, diamond or square."""
    xs, ys = grid(size)
    half = size / 2.0 - inset
    if style == "keystone":
        return np.abs(xs) + np.abs(ys) <= half + 0.01
    if style == "portrait":
        corner = (np.abs(xs) > half - 1.0) & (np.abs(ys) > half - 1.0)
        return (np.abs(xs) <= half) & (np.abs(ys) <= half) & ~corner
    return xs * xs + ys * ys <= half * half


STYLES = {
    # size, frame ramp, ring width (inside the 1 px ink outline)
    "start": (34, GOLD, 4),
    "minor": (20, STONE, 2),
    "notable": (26, BRONZE, 3),
    "keystone": (30, GOLD, 3),
    "bridge": (22, SILVER, 2),
    "portrait": (30, BRONZE, 3),
}


def make_frame(style: str) -> None:
    size, colors, ring = STYLES[style]
    xs, ys = grid(size)
    outer = shape_mask(style, size, 1.0)
    inner = shape_mask(style, size, 1.0 + ring)
    band = outer & ~inner
    lit = light(xs, ys)
    t = 0.35 + 0.55 * lit
    # Bevel: the outer edge catches light, the inner edge sits in shadow (and the other way round).
    outer_edge = band & ~shape_mask(style, size, 2.0)
    inner_edge = band & dilate(inner, diagonal=False)
    t = np.where(outer_edge, t + 0.2 * (lit - 0.4), t)
    t = np.where(inner_edge, 0.95 - lit * 0.75, t)
    rgb = ramp(colors, np.clip(t, 0, 1)).astype(np.float32)
    alpha = np.where(band, 255, 0)
    # Studs or notches, by style.
    if style in ("notable", "portrait"):
        r = size / 2.0 - 1.0 - ring / 2.0
        spots = [(0, -r), (r, 0), (0, r), (-r, 0)] if style == "notable" else [(-r, -r), (r, -r), (r, r), (-r, r)]
        for sx, sy in spots:
            stud = (np.abs(xs - sx) <= 1.0) & (np.abs(ys - sy) <= 1.0)
            rgb[stud] = colors[4]
            rgb[stud & (xs - sx < 0) & (ys - sy < 0)] = colors[5]
            rgb[stud & (xs - sx > 0) & (ys - sy > 0)] = colors[2]
    if style == "start":
        angle = np.arctan2(ys, xs)
        notch = band & (np.cos(angle * 8.0) > 0.7) & ~shape_mask(style, size, 2.5)
        rgb[notch] = colors[1]
    ink = dilate(outer) & ~outer
    ink |= inner & dilate(band, diagonal=False) & ~band  # dark lip where the gem meets the ring
    rgb[ink & ~band] = INK
    alpha = np.where(ink & ~band & ~inner, 255, alpha)
    save("frame_" + style, rgb, alpha)

    # The gem fills the hole; the frame is drawn over its edge.
    gem = shape_mask(style, size, ring)
    g = gem_values(style, xs, ys, gem, size / 2.0 - ring)
    grey = np.dstack([g, g, g]) * 255.0
    save("gem_" + style, grey, np.where(gem, 255, 0))
    save("gem_%s_left" % style, grey, np.where(gem & (xs < 0), 255, 0))
    save("gem_%s_right" % style, grey, np.where(gem & (xs >= 0), 255, 0))
    shine = gem_shine(style, xs, ys, gem, size / 2.0 - ring)
    save("shine_" + style, np.full((size, size, 3), 255.0), shine)

    # Halo: a dithered ring two pixels outside the frame.
    big = size + 8
    hx, hy = grid(big)
    near = shape_mask(style, big, 2.0)
    far = shape_mask(style, big, 4.0)
    halo = near & ~far
    halo &= ((np.floor(hx + 100) + np.floor(hy + 100)) % 2 == 0) | ~shape_mask(style, big, 3.0)
    save("halo_" + style, np.full((big, big, 3), 255.0), np.where(halo, 255, 0))


def gem_values(style: str, xs: np.ndarray, ys: np.ndarray, mask: np.ndarray, radius: float) -> np.ndarray:
    if style == "keystone":
        # Four facets, lit from the top left.
        facet = np.where(xs + ys < 0, np.where(xs - ys < 0, 1.0, 0.82), np.where(xs - ys < 0, 0.7, 0.52))
        table = np.abs(xs) + np.abs(ys) <= radius * 0.42
        return np.where(table, 0.9, facet) * mask
    if style == "portrait":
        # A dark backing that brightens towards the top, dithered in four steps.
        t = 0.32 + 0.18 * (1.0 - (ys + radius) / (2 * radius))
        b = bayer(*xs.shape)
        return (np.floor(t * 12 + b) / 12.0) * mask
    r = np.sqrt(xs * xs + ys * ys) / max(radius, 1.0)
    lit = light(xs, ys)
    v = 0.58 + 0.42 * lit * (1.0 - 0.35 * r) + 0.12 * (1.0 - r)
    v = np.where(r > 0.82, v - 0.16, v)  # darker rim
    return np.clip(np.round(v * 6.0) / 6.0, 0.3, 1.0) * mask


def gem_shine(style: str, xs: np.ndarray, ys: np.ndarray, mask: np.ndarray, radius: float) -> np.ndarray:
    if style == "portrait":
        return np.zeros(xs.shape)
    k = radius * 0.45
    spot = ((xs + k) ** 2 + (ys + k) ** 2 <= max(1.2, radius * 0.16) ** 2)
    glint = (np.abs(xs - k * 0.9) < 0.6) & (np.abs(ys - k * 0.9) < 0.6)
    return np.where(spot & mask, 230, np.where(glint & mask, 120, 0))


# --------------------------------------------------------------------------- icons

ICONS: dict[str, list[str]] = {
    "sword": [
        "............",
        ".........hw.",
        "........hws.",
        ".......hws..",
        "......hws...",
        "..d..hws....",
        "...dhws.....",
        "...dws......",
        "..dsdd......",
        ".dd..d......",
        ".s..........",
        "............",
    ],
    "speed": [
        "............",
        ".ww...ww....",
        ".hws..hws...",
        "..hws..hws..",
        "...hws..hws.",
        "....hws..hws",
        "....wws..wws",
        "...wws..wws.",
        "..wws..wws..",
        ".wws..wws...",
        ".ss...ss....",
        "............",
    ],
    "flame": [
        "............",
        ".....w......",
        ".....ww.....",
        "....wws.....",
        "...wwws..w..",
        "...wwhws.ws.",
        "..swwhhwsws.",
        "..swhhhhws..",
        "..swhhhhws..",
        "...swhhws...",
        "....ssss....",
        "............",
    ],
    "bolt": [
        "............",
        "......hww...",
        ".....hws....",
        "....hws.....",
        "...hws......",
        "..hwwwwww...",
        "......wws...",
        ".....wws....",
        "....wws.....",
        "...ws.......",
        "..s.........",
        "............",
    ],
    "leaf": [
        "............",
        "........www.",
        "......wwwws.",
        ".....wwwhws.",
        "....wwwhwws.",
        "...wwwhwwws.",
        "...wwhwwws..",
        "...whwwwss..",
        "...hwwsss...",
        "..s.sss.....",
        ".s..........",
        "............",
    ],
    "drop": [
        "............",
        ".....w......",
        ".....ww.....",
        "....wwws....",
        "....wwws....",
        "...whwwws...",
        "..whwwwwws..",
        "..whwwwwws..",
        "..wwwwwwss..",
        "...wwwwss...",
        "....ssss....",
        "............",
    ],
    "rock": [
        "............",
        "............",
        ".....www....",
        "....whwws...",
        "...whwwwws..",
        "..whwwwwwss.",
        "..wwwwwswss.",
        ".wwwwwsswss.",
        ".wwwwssssss.",
        ".sssssssss..",
        "............",
        "............",
    ],
    "heart": [
        "............",
        "............",
        "..ww....ww..",
        ".whww..wwws.",
        ".whwwwwwwws.",
        ".wwwwwwwwws.",
        "..wwwwwwws..",
        "...wwwwws...",
        "....wwws....",
        ".....ws.....",
        "............",
        "............",
    ],
    "star": [
        "............",
        ".....ww.....",
        ".....hw.....",
        "....hwws....",
        ".wwwhwwwwws.",
        "..wwhwwwws..",
        "...wwwwws...",
        "...wwwwws...",
        "..wwws.wws..",
        "..ws....ws..",
        ".w........s.",
        "............",
    ],
    "key": [
        "............",
        "...wwww.....",
        "..ws..sw....",
        "..ws..sw....",
        "...wwww.....",
        "....ws......",
        "....wsww....",
        "....ws......",
        "....wsw.....",
        "....ws......",
        "....ss......",
        "............",
    ],
    "flag": [
        "............",
        "..d.........",
        "..dwwwww....",
        "..dwhwwws...",
        "..dwwwwwws..",
        "..dwwwwws...",
        "..dsssss....",
        "..d.........",
        "..d.........",
        "..d.........",
        ".ddd........",
        "............",
    ],
    "skull": [
        "............",
        "...wwwwww...",
        "..whwwwwws..",
        ".whwwwwwwws.",
        ".ww..ww..ws.",
        ".ww..ww..ws.",
        "..wwwwwwws..",
        "...ww.w.ws..",
        "...wwwwwws..",
        "............",
        "............",
        "............",
    ],
    "tower": [
        "............",
        "..w.ww.ww...",
        "..wwwwwww...",
        "...whwws....",
        "...whwws....",
        "...wh.ws....",
        "...whwws....",
        "...whwws....",
        "..wwwwwws...",
        "..sssssss...",
        "............",
        "............",
    ],
    "lock": [
        "............",
        "....www.....",
        "...w...w....",
        "...w...w....",
        "..wwwwwww...",
        "..whwwwws...",
        "..whw.wws...",
        "..whw.wws...",
        "..wwwwwws...",
        "..sssssss...",
        "............",
        "............",
    ],
    "crown": [
        "............",
        "............",
        ".w...w...w..",
        ".ww.www.ww..",
        ".wwwwhwwww..",
        ".wwwwwwwws..",
        ".whwwwwwws..",
        ".ssssssss...",
        "............",
        "............",
        "............",
        "............",
    ],
    "book": [
        "............",
        "............",
        ".wwww.wwww..",
        ".whww.wwws..",
        ".whss.ssws..",
        ".whww.wwws..",
        ".whss.ssws..",
        ".wwwwswwww..",
        "..ssss.sss..",
        "............",
        "............",
        "............",
    ],
    "swords": [
        "............",
        ".hw......wh.",
        "..hw....wh..",
        "...hw..wh...",
        "....hwwh....",
        ".....ww.....",
        "....hwwh....",
        "..d.w..w.d..",
        "...d....d...",
        "..d.d..d.d..",
        ".d........d.",
        "............",
    ],
    "hammer": [
        "............",
        "..wwwwwww...",
        "..whwwwws...",
        "..wwwwwws...",
        "..ssswsss...",
        ".....ws.....",
        ".....ws.....",
        ".....ws.....",
        ".....ws.....",
        ".....ss.....",
        "............",
        "............",
    ],
    "snowflake": [
        "............",
        ".....w......",
        "...w.w.w....",
        "....www.....",
        ".w...w...w..",
        "..w.www.w...",
        ".wwwwhwwww..",
        "..w.www.w...",
        ".w...w...w..",
        "....www.....",
        "...w.w.w....",
        ".....w......",
    ],
    "burst": [
        "............",
        ".....w......",
        ".w...w...w..",
        "..w..w..w...",
        "...wwhww....",
        ".wwwhhhwww..",
        "...wwhww....",
        "..w..w..w...",
        ".w...w...w..",
        ".....w......",
        "............",
        "............",
    ],
    "shield": [
        "............",
        "..wwwwwww...",
        "..whwwwws...",
        "..whwwwws...",
        "..whwwwws...",
        "..whwwwws...",
        "...hwwws....",
        "...wwwws....",
        "....wws.....",
        ".....s......",
        "............",
        "............",
    ],
    "eye": [
        "............",
        "............",
        "............",
        "...wwwwww...",
        "..ww.dd.ww..",
        ".ww.dhdd.ww.",
        ".ww.dddd.ww.",
        "..ww.dd.ww..",
        "...wwwwww...",
        "............",
        "............",
        "............",
    ],
    "bubbles": [
        "............",
        "........ww..",
        ".......whws.",
        "........ss..",
        "...ww.......",
        "..whws..ww..",
        "..wwws.whs..",
        "...ss...s...",
        "....www.....",
        "...whwws....",
        "....sss.....",
        "............",
    ],
    "push": [
        "............",
        "............",
        "....w.......",
        "...hw.......",
        "..hwwwwwwww.",
        ".hwwwwwwwws.",
        "..wwwwwwwws.",
        "...ws.......",
        "....s.......",
        "............",
        "............",
        "............",
    ],
    "shatter": [
        "............",
        "......w.....",
        ".....hws....",
        "....hw.ws...",
        "...hww.wws..",
        "..hwww..ws..",
        "..wwws.wws..",
        "...ww.wws...",
        "....w.ws....",
        ".....ss.....",
        "............",
        "............",
    ],
    "sun": [
        "............",
        ".....hw.....",
        "..h..hw..w..",
        "...h....w...",
        "....hwws....",
        ".hh.hwws.ws.",
        ".hw.wwws.ws.",
        "....wsss....",
        "...w....s...",
        "..w..ws..s..",
        ".....ws.....",
        "............",
    ],
    "diamond": [
        "............",
        ".....ww.....",
        "....whws....",
        "...whwwws...",
        "..whwwwwws..",
        ".whwwwwwwws.",
        ".wwwwwwwwss.",
        "..wwwwwwss..",
        "...wwwwss...",
        "....wwss....",
        ".....ss.....",
        "............",
    ],
}


def icon_from_rows(rows: list[str]) -> tuple[np.ndarray, np.ndarray]:
    assert len(rows) == 12 and all(len(r) == 12 for r in rows), rows
    rgb = np.zeros((12, 12, 3), np.float32)
    mask = np.zeros((12, 12), bool)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in ICON_COLORS:
                rgb[y, x] = ICON_COLORS[ch]
                mask[y, x] = True
    return rgb, mask


def icon_procedural(name: str) -> tuple[np.ndarray, np.ndarray]:
    xs, ys = grid(12)
    r = np.sqrt(xs * xs + ys * ys)
    rgb = np.zeros((12, 12, 3), np.float32)
    lit = light(xs, ys)
    if name == "coin":
        mask = r <= 4.6
        rgb[:] = ICON_COLORS["w"]
        rgb[mask & (lit < 0.35)] = ICON_COLORS["s"]
        rgb[mask & (lit > 0.8) & (r > 3.2)] = ICON_COLORS["h"]
        inner = (r > 1.6) & (r <= 2.6)
        rgb[inner] = ICON_COLORS["d"]
    elif name == "range":
        ring = (r > 3.2) & (r <= 4.6)
        ticks = ((np.abs(xs) < 0.6) | (np.abs(ys) < 0.6)) & (r > 3.5) & (r <= 5.8)
        dot = r <= 1.0
        mask = ring | ticks | dot
        rgb[:] = ICON_COLORS["w"]
        rgb[ring & (lit < 0.4)] = ICON_COLORS["s"]
        rgb[dot] = ICON_COLORS["h"]
    elif name == "spiral":
        angle = np.arctan2(ys, xs)
        mask = np.zeros((12, 12), bool)
        for turn in range(3):
            target = (angle + np.pi + turn * 2 * np.pi) * 0.72
            mask |= (np.abs(r - target) < 0.75) & (r <= 5.4)
        mask |= r <= 0.8
        rgb[:] = ICON_COLORS["w"]
        rgb[mask & (r > 3.6)] = ICON_COLORS["s"]
        rgb[r <= 1.6] = ICON_COLORS["h"]
    elif name == "aura":
        core = r <= 1.6
        ring1 = (r > 2.9) & (r <= 3.9)
        ring2 = (r > 4.9) & (r <= 5.8) & ((np.floor(xs + 6) + np.floor(ys + 6)) % 2 == 0)
        mask = core | ring1 | ring2
        rgb[:] = ICON_COLORS["w"]
        rgb[core] = ICON_COLORS["h"]
        rgb[ring2] = ICON_COLORS["s"]
    else:
        raise KeyError(name)
    return rgb, mask


def make_icon(name: str) -> None:
    if name in ICONS:
        rgb, mask = icon_from_rows(ICONS[name])
    else:
        rgb, mask = icon_procedural(name)
    ink = dilate(mask) & ~mask
    rgb[ink] = ICON_OUTLINE
    save("icon_" + name, rgb, np.where(mask | ink, 255, 0))


# --------------------------------------------------------------------------- glows, sparkle, panel

def make_glow(name: str, size: int, power: float) -> None:
    xs, ys = grid(size)
    r = np.sqrt(xs * xs + ys * ys) / (size / 2.0)
    a = np.clip(1.0 - r, 0.0, 1.0) ** power
    # Three dithered steps, so the glow stays chunky like the rest of the art.
    level = np.floor(a * 3.0 + bayer(size, size)) / 3.0
    save(name, np.full((size, size, 3), 255.0), level * 255.0)


def make_sparkle() -> None:
    rows = [
        "...h...",
        "...w...",
        "..sws..",
        "hwwhwwh",
        "..sws..",
        "...w...",
        "...h...",
    ]
    rgb = np.zeros((7, 7, 3), np.float32)
    alpha = np.zeros((7, 7), np.float32)
    shades = {"h": 255.0, "w": 230.0, "s": 150.0}
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch in shades:
                rgb[y, x] = 255.0
                alpha[y, x] = shades[ch]
    save("sparkle", rgb, alpha)


def make_panel() -> None:
    size = 16
    rgb = np.zeros((size, size, 3), np.float32)
    alpha = np.full((size, size), 255.0)
    rgb[:] = hexc("15161f")
    ys, xs = np.mgrid[0:size, 0:size]
    edge = np.minimum(np.minimum(xs, ys), np.minimum(size - 1 - xs, size - 1 - ys))
    rgb[edge == 0] = INK
    rgb[edge == 1] = BRONZE[3]
    rgb[(edge == 1) & ((xs == size - 2) | (ys == size - 2))] = BRONZE[1]
    rgb[edge == 2] = BRONZE[1]
    rgb[(edge == 2) & ((xs == size - 3) | (ys == size - 3))] = BRONZE[0]
    rgb[(edge == 3)] = hexc("1d1f2b")
    for cx, cy in ((2, 2), (size - 3, 2), (2, size - 3), (size - 3, size - 3)):
        rgb[cy, cx] = BRONZE[5]
    for cx, cy in ((0, 0), (size - 1, 0), (0, size - 1), (size - 1, size - 1)):
        alpha[cy, cx] = 0
    save("panel", rgb, alpha, scale=2)


# --------------------------------------------------------------------------- backdrop

BACKDROP_RAMP = [hexc(c) for c in ("07080e", "0a0c14", "0e111b", "121624", "171c2e", "1d2338")]
NEBULA_A = hexc("2a1f45")
NEBULA_B = hexc("13304a")


def make_backdrop() -> None:
    w, h = 960, 540
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    nx = (xs - w / 2) / (w / 2)
    ny = (ys - h / 2) / (h / 2)
    vignette = 1.0 - np.clip(nx * nx * 0.55 + ny * ny * 0.8, 0.0, 1.0)
    base = 0.18 + 0.5 * vignette
    cloud = fbm(h, w, [220.0, 110.0, 55.0, 27.0], RNG)
    cloud2 = fbm(h, w, [260.0, 130.0, 60.0], RNG)
    t = np.clip(base + (cloud - 0.5) * 0.35, 0, 1)
    b = bayer(h, w)
    idx = np.clip(np.floor(t * (len(BACKDROP_RAMP) - 1) + b).astype(int), 0, len(BACKDROP_RAMP) - 1)
    rgb = np.stack(BACKDROP_RAMP)[idx].astype(np.float32)
    # Two thin nebulae, dithered in over the base.
    for col, field, cut in ((NEBULA_A, cloud, 0.58), (NEBULA_B, cloud2, 0.6)):
        amount = np.clip((field - cut) * 4.0, 0, 0.6) * vignette
        on = amount > b * 0.9
        rgb[on] = rgb[on] * 0.45 + col * 0.55
    # Stars: many faint dots, a few bright crosses.
    star_cols = [hexc(c) for c in ("2a3048", "3d4566", "66708f", "a7b2d4")]
    for _ in range(1100):
        x, y = RNG.integers(0, w), RNG.integers(0, h)
        level = min(3, int(RNG.exponential(0.7)))
        rgb[y, x] = star_cols[level]
    bright = hexc("d6def5")
    for _ in range(28):
        x, y = RNG.integers(2, w - 2), RNG.integers(2, h - 2)
        rgb[y, x] = bright
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rgb[y + dy, x + dx] = star_cols[2]
    save("backdrop", rgb, np.full((h, w), 255.0))


# --------------------------------------------------------------------------- main

PROCEDURAL_ICONS = ("coin", "range", "spiral", "aura")


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    for style in STYLES:
        make_frame(style)
    for name in list(ICONS) + list(PROCEDURAL_ICONS):
        make_icon(name)
    make_glow("glow", 64, 1.5)
    make_glow("aura", 160, 1.8)
    make_sparkle()
    make_panel()
    make_backdrop()
    print("wrote", len(os.listdir(OUT)), "files to", OUT)


if __name__ == "__main__":
    main()
