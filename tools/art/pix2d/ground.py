#!/usr/bin/env python3
"""Hand-drawn ground for the boards, in the same style as the pix2d creatures and towers.

Instead of per-pixel noise, the ground is built the way a pixel artist paints a tileset: flat tone areas with clean
edges, a lit lip on top of every raised patch and a dark one under it, grass drawn as little tufts placed one by one,
pebbles with a highlight and a shadow, flower clusters, a sunken road with an earth bank on its far side and worn
cobbles, and for the fire lands cracked basalt plates with lava in only some of the seams.

usage (from the repository root):
  python3 tools/art/pix2d/ground.py [map ids] [--biomes meadow,nature,fire] [--preview DIR]
Writes assets/art/game/ground/<map>.png, _n.png, _glow.png and <map>.json (props), and the props it uses into
assets/art/game/props/ plus their entries in assets/art/game/art.json. Maps whose biome has no style here are left
as they are (tools/art/gen_game_art.py still paints them).
"""
from __future__ import annotations

import argparse
import glob
import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
from kit import hexc  # noqa: E402
from gen_lighting_demo import encode_normals, fbm, normals_from_height, value_noise  # noqa: E402
import gen_game_art as old  # noqa: E402
import props as P  # noqa: E402

OUT = os.path.join("assets", "art", "game")


def pal(*cols):
    return np.array([hexc(c) for c in cols], np.float64)


# One entry per biome: ground tones (dark to light), grass tuft tones, road tones, the road's far bank, flowers,
# and which props go where.
STYLES = {
    "meadow": {
        "kind": "grass",
        "ground": pal("2f4a22", "3a5a28", "47692d", "557a33", "678c3c"),
        "tuft": pal("2a4220", "4a7030", "6a9440", "8cb452", "b4d070"),
        "road": pal("4a3826", "5e4830", "73583a", "876a46", "9c7e56", "b39468"),
        "bank": pal("2e2218", "3e2e20"),
        "cobble": True, "dirt_patches": 0.10,
        "flowers": [pal("e8e0d0", "fffaf0"), pal("e0b030", "ffe070"), pal("c04a6a", "f07a9a"), pal("6a7ae0", "a0b0ff")],
        "flower_rate": 1.0, "tuft_rate": 0.55, "litter": None,
        "props": {"tree": [("oak_0", 3), ("oak_1", 3), ("pine_0", 2)],
                  "small": [("bush_round", 3), ("bush_berry", 2), ("rock_0", 3), ("rock_1", 2), ("stump", 1), ("log", 1),
                            ("flowers_0", 3), ("flowers_1", 2), ("tuft_0", 4), ("tuft_1", 4), ("mushroom_0", 1)]},
    },
    "nature": {
        "kind": "grass",
        "ground": pal("17301a", "1e3b1f", "264826", "30562c", "3c6532"),
        "tuft": pal("173018", "2a4e24", "3f6c30", "5a8e3c", "80b04c"),
        "road": pal("2e2016", "3c2a1c", "4c3624", "5c442e", "6c5238", "7e6244"),
        "bank": pal("1c140e", "281c14"),
        "cobble": False, "dirt_patches": 0.06, "roots": True,
        "flowers": [pal("c04a8a", "f07ac0"), pal("e0d050", "fff0a0"), pal("e8e8f0", "ffffff")],
        "flower_rate": 1.6, "tuft_rate": 0.8, "litter": pal("5a4a1e", "7a6428", "8a3a1e"),
        "props": {"tree": [("jungle_0", 3), ("jungle_1", 3), ("pine_0", 1)],
                  "small": [("fern_a", 4), ("fern_b", 3), ("bush_round", 3), ("bush_berry", 2), ("rock_mossy", 2),
                            ("stump", 1), ("log", 2), ("mushroom_1", 2), ("mushroom_0", 1), ("flowers_1", 2), ("tuft_0", 3)]},
    },
    "fire": {
        "kind": "basalt",
        "ground": pal("1c1618", "262022", "302829", "3b3132", "473b3a", "564844"),
        "ash": pal("4a4240", "5a504c", "6a5f58"),
        "lava": pal("8a1e10", "d8481a", "ff8a2a", "ffc85a", "fff2c0"),
        "tuft": pal("2a1c16", "4a2c1a", "6a3a1c", "8a4a20", "b06024"),
        "road": pal("2a2422", "352e2b", "413835", "4d433e", "5a4e48", "6a5c54"),
        "bank": pal("120e0e", "1c1616"),
        "cobble": True, "flower_rate": 0.0, "tuft_rate": 0.12,
        "props": {"tree": [("dead_tree_0", 3), ("dead_tree_1", 2), ("basalt_cols", 2)],
                  "small": [("basalt_rock_0", 3), ("basalt_rock_1", 2), ("ember_shard", 1),
                            ("ash_tuft_0", 3), ("ash_tuft_1", 3), ("charred_log", 1), ("skull_rock", 1)]},
    },
    "storm": {  # a windswept plateau of pale grass, slate outcrops
        "kind": "grass",
        "ground": pal("3e4c40", "4a5a4a", "5a6c56", "6c7e64", "809274"),
        "tuft": pal("3a4838", "56684e", "74865e", "92a476", "b4c494"),
        "road": pal("2e333a", "3a4048", "474e58", "555d68", "646d78", "77808a"),
        "bank": pal("1e2228", "2a2f36"),
        "cobble": True, "dirt_patches": 0.0, "slate": True,
        "flowers": [pal("c8d4e4", "eef4ff"), pal("8aa0d0", "b8c8f0")],
        "flower_rate": 0.7, "tuft_rate": 0.9, "litter": None,
        "props": {"tree": [("pine_0", 3), ("standing_stone", 2), ("dead_tree_1", 1)],
                  "small": [("rock_0", 3), ("rock_1", 3), ("slate_shard", 3), ("steppe_tuft_0", 4), ("steppe_tuft_1", 4),
                            ("storm_crystal", 1), ("flowers_0", 1)]},
    },
    "void": {  # the rift: violet grass under no stars
        "kind": "grass",
        "ground": pal("140f1c", "1b1426", "231a30", "2c213c", "372a4a"),
        "tuft": pal("1e1630", "30244a", "463668", "5e4a88", "8068b0"),
        "road": pal("0e0c12", "16121c", "1e1a26", "282230", "322a3c", "3e3448"),
        "bank": pal("08060c", "100c14"),
        "cobble": True, "dirt_patches": 0.0,
        "flowers": [pal("8a5ad0", "c8a0ff"), pal("3aa0b0", "80f0ff")],
        "flower_rate": 0.8, "tuft_rate": 0.6, "litter": None, "glow_flowers": True,
        "props": {"tree": [("void_tree", 3), ("rift_spire", 2)],
                  "small": [("void_shard", 3), ("obsidian_rock", 3), ("void_tuft_0", 4), ("void_tuft_1", 4),
                            ("void_bloom", 2)]},
    },
    "earth": {  # a red sandstone canyon floor of cracked slabs
        "kind": "basalt", "plate": 16,
        "ground": pal("5a2c1c", "6e3622", "82422a", "985232", "ac623c", "c07448"),
        "ash": pal("b07850", "c08a5c", "d09c6c"),
        "tuft": pal("5a4424", "74582e", "8e6e3a", "a88648", "c4a060"),
        "road": pal("7a5e40", "8a6c4a", "9a7a54", "aa8a60", "ba9a6e", "ccac7e"),
        "bank": pal("4a2e1e", "5e3a26"),
        "cobble": False, "flower_rate": 0.0, "tuft_rate": 0.2,
        "props": {"tree": [("mesa_rock", 3), ("cactus_tall", 2)],
                  "small": [("sand_rock_0", 3), ("sand_rock_1", 2), ("cactus_small", 2), ("dry_tuft_0", 4),
                            ("dry_tuft_1", 3), ("bones", 1), ("skull_rock", 1)]},
    },
    "water": {  # a frozen lakeshore under snow
        "kind": "snow",
        "ground": pal("8a98ac", "a2b0c2", "bac6d4", "d0dae4", "e6eef4"),
        "ice": pal("2a4a6a", "4a7aa8", "7ab4e0", "b4e0f8", "eefaff"),
        "tuft": pal("5a4a34", "7a6440", "967e50", "b09a68", "cab680"),
        "road": pal("3e5670", "4a6480", "587490", "6a86a0", "7e98b0", "96aec2"),
        "bank": pal("2a3a4c", "34465a"),
        "cobble": True, "tuft_rate": 0.1,
        "props": {"tree": [("snow_pine", 4), ("ice_spire", 1)],
                  "small": [("snow_rock_0", 3), ("snow_rock_1", 2), ("reed_0", 4), ("reed_1", 3), ("ice_chunk", 2),
                            ("snow_bush", 2)]},
    },
    "heart": {  # the heart of the ring: old flagstones with grass in the joints, gold road, prisms
        "kind": "basalt", "plate": 9,
        "ground": pal("6a645a", "7c766a", "8e887a", "a29a8a", "b6ae9c", "c8c0ae"),
        "ash": pal("94a070", "a4b07c", "b4c08a"),
        "seam_fill": pal("4a6a34", "567a3c"),
        "sparks": pal("ffe07a", "ffffff"),
        "tuft": pal("4a6634", "5e7c40", "78964e", "92b060", "b0c878"),
        "road": pal("6a5430", "806638", "967a44", "ac8e52", "c2a462", "d6ba74"),
        "bank": pal("40321c", "54422a"),
        "cobble": True, "flower_rate": 0.0, "tuft_rate": 0.25,
        "props": {"tree": [("marble_pillar", 3), ("oak_1", 2)],
                  "small": [("prism_shard", 2), ("rock_0", 2), ("flowers_0", 3), ("flowers_1", 3), ("pale_tuft_0", 3),
                            ("pale_tuft_1", 3), ("bush_round", 2)]},
    },
}


# ------------------------------------------------------------------------------------------------ helpers
def voronoi(H, W, cell, rng, jitter=0.8):
    """Jittered-grid Voronoi: (cell id, distance to nearest seed, distance to second nearest)."""
    gh, gw = H // cell + 3, W // cell + 3
    seeds = (np.stack(np.mgrid[0:gh, 0:gw], -1)[..., ::-1] + 0.5 + (rng.random((gh, gw, 2)) - 0.5) * jitter) * cell
    yy, xx = np.mgrid[0:H, 0:W]
    gy, gx = yy // cell + 1, xx // cell + 1
    d1 = np.full((H, W), 1e9)
    d2 = np.full((H, W), 1e9)
    ident = np.zeros((H, W), np.int64)
    for oy in (-1, 0, 1):
        for ox in (-1, 0, 1):
            sy, sx = gy + oy, gx + ox
            sy = np.clip(sy, 0, gh - 1)
            sx = np.clip(sx, 0, gw - 1)
            p = seeds[sy, sx]
            d = np.hypot(xx + 0.5 - p[..., 0] + cell, yy + 0.5 - p[..., 1] + cell)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            d1 = np.where(closer, d, d1)
            ident = np.where(closer, sy * gw + sx, ident)
    return ident, d1, d2


def lips(level, rgb, tones, height):
    """Raised patches: a lit pixel on the top edge of each higher area, a dark one just under it."""
    up = np.zeros_like(level, bool)
    up[1:] = level[1:] > level[:-1]
    down = np.zeros_like(level, bool)
    down[:-1] = level[:-1] > level[1:]
    below = np.zeros_like(level, bool)
    below[1:] = down[:-1]
    n = len(tones)
    rgb[up] = tones[np.clip(level[up] + 1, 0, n - 1)]
    rgb[below] = tones[np.clip(level[below] - 1, 0, n - 1)]
    height[up] += 0.3
    height[below] -= 0.3


def blade(rgb, height, x, y, k, lean, tones, tip):
    H, W = height.shape
    for j in range(k):
        xx = x + (lean if j >= k - 1 else 0)
        yy = y - j
        if 0 <= yy < H and 0 <= xx < W:
            rgb[yy, xx] = tones[min(len(tones) - 1, 1 + j)] if j < k - 1 else tip
            height[yy, xx] = 0.6 + j * 0.2


def tufts(rgb, height, mask, density, tones, rng, spacing=(5, 4)):
    """Grass tufts placed one per grid slot (jittered), more where density is high: three blades with a lit tip."""
    H, W = mask.shape
    sx, sy = spacing
    for y in range(4, H - 1, sy):
        for x in range(1 + (y // sy % 2) * 2, W - 2, sx):
            px = x + int(rng.integers(-1, 2))
            py = y + int(rng.integers(-1, 2))
            if not (0 <= py < H and 0 <= px < W) or not mask[py, px]:
                continue
            if rng.random() > density[py, px]:
                continue
            tall = 2 + int(rng.random() < 0.45)
            rgb[py, px - 1] = tones[0]
            rgb[py, px + 1] = tones[0]
            blade(rgb, height, px - 1, py - 1, tall - 1, -1 if rng.random() < 0.5 else 0, tones, tones[3])
            blade(rgb, height, px, py, tall + 1, int(rng.choice([-1, 0, 1])), tones, tones[4])
            blade(rgb, height, px + 1, py - 1, tall - 1, 1 if rng.random() < 0.5 else 0, tones, tones[3])
            if py + 1 < H:
                rgb[py + 1, px] = tones[0]


def pebble(rgb, height, x, y, tones):
    H, W = height.shape
    if not (1 <= x < W - 2 and 1 <= y < H - 2):
        return
    rgb[y, x] = tones[-1]
    rgb[y, x + 1] = tones[-2]
    rgb[y + 1, x] = tones[-3]
    rgb[y + 1, x + 1] = tones[-4]
    rgb[y + 2, x + 1] = tones[0]
    height[y:y + 2, x:x + 2] += 0.7


# ------------------------------------------------------------------------------------------------ painters
def paint_grass(st, W, H, road_d, half, rng):
    tones = st["ground"]
    base = fbm(H, W, [60, 24, 10], rng)
    level = np.clip((base * 1.25 - 0.12) * len(tones), 0, len(tones) - 1).astype(int)
    # near the road the grass is trodden darker
    level = np.where(road_d < half + 4, np.maximum(level - 1, 0), level)
    rgb = tones[level].copy()
    height = level * 0.25
    lips(level, rgb, tones, height)
    # bare dirt patches with a grass fringe
    if st.get("dirt_patches"):
        d = fbm(H, W, [34, 14, 6], rng)
        bare = (d > 1 - st["dirt_patches"] * 1.8) & (road_d > half + 6)
        road = st["road"]
        lvl = np.clip(((d - 0.6) * 6 + value_noise(H, W, 3, rng) * 0.6) * 3, 0, 3).astype(int) + 1
        rgb[bare] = road[lvl[bare]]
        height[bare] = -0.3
        edge = bare & ~np.roll(bare, 1, 0)
        rgb[edge] = road[0]
    # leaf litter (jungle)
    if st.get("litter") is not None:
        lit = st["litter"]
        for _ in range(int(W * H / 140)):
            x, y = int(rng.integers(1, W - 2)), int(rng.integers(1, H - 2))
            if road_d[y, x] < half + 1:
                continue
            c = lit[int(rng.integers(0, len(lit)))]
            rgb[y, x] = c
            if rng.random() < 0.6:
                rgb[y, x + 1] = c * 0.8
    # roots crawling out of the jungle floor
    if st.get("roots"):
        for _ in range(int(W * H / 9000)):
            x, y = float(rng.uniform(0, W)), float(rng.uniform(0, H))
            ang = rng.uniform(0, math.tau)
            for k in range(int(rng.integers(10, 26))):
                ang += rng.uniform(-0.4, 0.4)
                x += math.cos(ang)
                y += math.sin(ang) * 0.7
                ix, iy = int(x), int(y)
                if not (1 <= ix < W - 1 and 1 <= iy < H - 1):
                    break
                rgb[iy, ix] = hexc("4a3420")
                rgb[iy - 1, ix] = hexc("6a4c2e")
                rgb[iy + 1, ix] = tones[0]
                height[iy, ix] = 0.8
    # slate outcrops breaking through the turf (storm plateau)
    if st.get("slate"):
        ident, d1, d2 = voronoi(H, W, 10, rng)
        out = (fbm(H, W, [44, 18], rng) > 0.66) & (road_d > half + 4)
        sl = pal("2e333c", "3e4550", "525a66", "68717e", "828c98")
        per = rng.random(ident.max() + 1)
        lvl = (per[ident] * 2.99).astype(int) + 1
        rgb[out] = sl[lvl[out]]
        gy, gx = np.gradient(d2 - d1)
        rim = out & ((d2 - d1) < 2.2)
        rgb[rim & ((gx + gy) > 0.1)] = sl[4]
        rgb[out & ((d2 - d1) < 1.0)] = sl[0]
        height[out] = 0.8
    # tufts, denser on the lighter patches
    field = fbm(H, W, [28, 11], rng)
    dens = np.clip(st["tuft_rate"] * np.clip((field - 0.42) * 3.0, 0, 1) * (0.5 + level / (len(tones) - 1)), 0, 1)
    tufts(rgb, height, road_d > half + 2, dens, st["tuft"], rng)
    # flower clusters
    glow_px = []
    for _ in range(int(W * H / 2400 * st.get("flower_rate", 1.0))):
        cx_, cy_ = int(rng.integers(4, W - 4)), int(rng.integers(4, H - 4))
        if road_d[cy_, cx_] < half + 4:
            continue
        col = st["flowers"][int(rng.integers(0, len(st["flowers"])))]
        for _ in range(int(rng.integers(3, 7))):
            x, y = cx_ + int(rng.integers(-3, 4)), cy_ + int(rng.integers(-2, 3))
            rgb[y + 1, x] = st["tuft"][1]
            rgb[y, x] = col[0]
            rgb[y - 1, x] = col[1]
            height[y - 1:y + 1, x] = 0.9
            if st.get("glow_flowers"):
                glow_px.append((x, y - 1, col[1]))
    # pebbles
    stone = pal("3e3a36", "5a5650", "7a746a", "9a9488", "bab4a6")
    for _ in range(int(W * H / 1800)):
        x, y = int(rng.integers(2, W - 3)), int(rng.integers(2, H - 3))
        if road_d[y, x] > half + 2:
            pebble(rgb, height, x, y, stone)
    glow = np.zeros((H, W, 4), np.uint8)
    for (x, y, c) in glow_px:
        glow[y, x, :3] = c.astype(np.uint8)
        glow[y, x, 3] = 200
    return rgb, height, glow


def paint_basalt(st, W, H, road_d, half, rng):
    """Plates: cracked basalt (fire), sandstone slabs (earth) or old flagstones (heart). Lava only where st has it."""
    tones = st["ground"]
    ident, d1, d2 = voronoi(H, W, st.get("plate", 12), rng)
    per = rng.random(ident.max() + 1)
    big = fbm(H, W, [70, 30], rng)
    t = np.clip(per[ident] * 0.55 + big * 0.7 - 0.05, 0, 0.999)
    level = (t * (len(tones) - 1)).astype(int) + 1
    rgb = tones[np.clip(level, 0, len(tones) - 1)].copy()
    height = 0.6 - np.clip(1.6 - (d2 - d1), 0, 1.6) * 0.5
    seam = (d2 - d1) < 1.3
    # bevel: the upper-left rim of each plate is lit, the lower-right rim is dark
    yy, xx = np.mgrid[0:H, 0:W]
    near = (d2 - d1) < 2.6
    gy, gx = np.gradient(d2 - d1)
    lit_rim = near & ~seam & ((gx + gy) > 0.15)
    dark_rim = near & ~seam & ((gx + gy) < -0.15)
    rgb[lit_rim] = tones[np.clip(level[lit_rim] + 1, 0, len(tones) - 1)]
    rgb[dark_rim] = tones[np.clip(level[dark_rim] - 1, 0, len(tones) - 1)]
    rgb[seam] = tones[0]
    height[seam] = -0.5
    # lava runs in some seams only, in long veins
    glow = np.zeros((H, W, 4), np.uint8)
    if st.get("seam_fill") is not None:                      # grass or sand grown into the seams
        rgb[seam] = st["seam_fill"][(yy + xx) % len(st["seam_fill"])][seam]
    lava = st.get("lava")
    vein = fbm(H, W, [90, 40], rng)
    if lava is None:
        lava = np.zeros((5, 3))
        hot = np.zeros((H, W), bool)
    else:
        hot = seam & (np.abs(vein - 0.6) < 0.045) & (road_d > half + 3)
    hot_core = hot & ((d2 - d1) < 0.7)
    rgb[hot] = lava[2]
    rgb[hot_core] = lava[3]
    glow[hot, :3] = lava[2].astype(np.uint8)
    glow[hot, 3] = 210
    glow[hot_core, :3] = lava[3].astype(np.uint8)
    glow[hot_core, 3] = 255
    # the plates next to a hot seam are lit red at their rims
    warm = (~hot) & (np.roll(hot, 1, 0) | np.roll(hot, -1, 0) | np.roll(hot, 1, 1) | np.roll(hot, -1, 1))
    rgb[warm] = lava[0] * 0.75 + rgb[warm] * 0.25
    glow[warm, :3] = lava[0].astype(np.uint8)
    glow[warm, 3] = 120
    # pools of lava where veins are hottest
    pool = (vein > 0.78) & (d1 < 5.5) & (road_d > half + 6) & (per[ident] > 0.8) & (st.get("lava") is not None)
    rgb[pool] = lava[1]
    inner = pool & (d1 < 3.5)
    rgb[inner] = lava[2]
    glow[pool, :3] = lava[2].astype(np.uint8)
    glow[pool, 3] = 230
    height[pool] = -0.6
    # ash drifts settle in flat bands over the plates
    ash = fbm(H, W, [40, 16, 7], rng)
    drift = (ash > 0.62) & ~hot & ~pool
    alv = np.clip(((ash - 0.62) * 8), 0, 2).astype(int)
    rgb[drift] = st["ash"][alv[drift]]
    height[drift] = 0.3
    edge = drift & ~np.roll(drift, -1, 0)
    rgb[np.roll(edge, 1, 0) & ~drift] = tones[0]
    # sparse charred tufts, embers
    tufts(rgb, height, (road_d > half + 2) & ~hot & ~pool, np.full((H, W), st["tuft_rate"]), st["tuft"], rng,
          spacing=(7, 6))
    sparks = st.get("sparks", lava[2:4] if st.get("lava") is not None else None)
    for _ in range(int(W * H / 900) if sparks is not None else 0):
        x, y = int(rng.integers(1, W - 1)), int(rng.integers(1, H - 1))
        if road_d[y, x] < half + 1 or hot[y, x]:
            continue
        c = sparks[1] if rng.random() < 0.4 else sparks[0]
        rgb[y, x] = c
        glow[y, x, :3] = c.astype(np.uint8)
        glow[y, x, 3] = 200
    return rgb, height, glow


def paint_road(st, rgb, height, glow, road_d, dist, half, rng):
    H, W = road_d.shape
    road = st["road"]
    on = road_d < half
    t = fbm(H, W, [20, 8, 3], rng)
    lv = np.clip((t * 1.3 - 0.15) * 4, 0, 3).astype(int) + 1
    rgb[on] = road[lv[on]]
    height[on] = -0.6
    glow[on] = 0
    # ruts
    rut = on & (np.abs(dist - half * 0.45) < 0.9)
    rgb[rut] = road[1]
    height[rut] = -0.8
    # worn cobbles in patches along the middle
    if st.get("cobble"):
        ident, d1, d2 = voronoi(H, W, 5, rng, jitter=0.7)
        keep = fbm(H, W, [30, 12], rng) > 0.48
        cob = on & keep & (road_d < half - 2)
        per = rng.random(ident.max() + 1)
        tone = (per[ident] * 2.99).astype(int) + 2
        seam = cob & ((d2 - d1) < 1.0)
        stone = cob & ~seam
        rgb[stone] = road[np.clip(tone[stone], 0, len(road) - 1)]
        gy, gx = np.gradient(d2 - d1)
        rim = stone & ((d2 - d1) < 2.0)
        top = rim & ((gx + gy) > 0.1)
        bot = rim & ((gx + gy) < -0.1)
        rgb[top] = road[-1]
        rgb[bot] = road[1]
        rgb[seam] = road[0]
        height[stone] = -0.35
        height[seam] = -0.75
    # the far bank (top edge of the road on screen): a strip of earth wall in shadow under a grass lip
    above = np.zeros_like(on)
    for k in (1, 2, 3):
        shifted = np.zeros_like(on)
        shifted[k:] = ~on[:-k]
        above |= shifted
    bank = on & above
    rgb[bank] = st["bank"][1]
    near_top = np.zeros_like(on)
    near_top[1:] = ~on[:-1]
    rgb[on & near_top] = st["bank"][0]
    height[bank] = -0.2
    # the near edge (bottom): a dark line, then the grass lip catching the light
    below = np.zeros_like(on)
    below[:-1] = on[1:] & ~on[:-1]
    rgb[below] = st["bank"][0]
    lip = np.zeros_like(on)
    lip[:-2] = on[2:] & ~on[1:-1] & ~on[:-2]
    rgb[lip & ~on] = st["tuft"][3]
    # stones and pebbles on the road
    for _ in range(int(W * H / 1500)):
        x, y = int(rng.integers(1, W - 3)), int(rng.integers(1, H - 3))
        if road_d[y, x] < half - 3:
            pebble(rgb, height, x, y, road)


def paint_snow(st, W, H, road_d, half, rng):
    """Snow: soft drifts in a few flat tones with lit crests, patches of blue ice, reeds poking through."""
    tones = st["ground"]
    base = fbm(H, W, [50, 20, 8], rng)
    level = np.clip((base * 1.3 - 0.15) * len(tones), 0, len(tones) - 1).astype(int)
    rgb = tones[level].copy()
    height = level * 0.3
    lips(level, rgb, tones, height)
    ice_t = st["ice"]
    ident, d1, d2 = voronoi(H, W, 9, rng)
    icy = (fbm(H, W, [60, 24], rng) > 0.64) & (road_d > half + 4)
    seam = (d2 - d1) < 1.1
    rgb[icy] = ice_t[2]
    gy, gx = np.gradient(d2 - d1)
    rgb[icy & ((d2 - d1) < 2.4) & ((gx + gy) > 0.1)] = ice_t[3]
    rgb[icy & seam] = ice_t[1]
    height[icy] = 0.1
    glow = np.zeros((H, W, 4), np.uint8)
    for _ in range(int(W * H / 700)):
        x, y = int(rng.integers(1, W - 1)), int(rng.integers(1, H - 1))
        if icy[y, x]:
            rgb[y, x] = ice_t[4]
            glow[y, x, :3] = ice_t[4].astype(np.uint8)
            glow[y, x, 3] = 140
    tufts(rgb, height, (road_d > half + 2) & ~icy, np.full((H, W), st["tuft_rate"]), st["tuft"], rng, spacing=(8, 7))
    stone = pal("4a5262", "6a7486", "8e98a8", "b0b8c6", "d6dce6")
    for _ in range(int(W * H / 2600)):
        x, y = int(rng.integers(2, W - 3)), int(rng.integers(2, H - 3))
        if road_d[y, x] > half + 2:
            pebble(rgb, height, x, y, stone)
    return rgb, height, glow


PAINTERS = {"grass": paint_grass, "basalt": paint_basalt, "snow": paint_snow}


# ------------------------------------------------------------------------------------------------ one map
def make_ground(m, props_info, preview=None):
    st = STYLES[m["biome"]]
    cell_art = m["cell"] // old.ART_SCALE
    W, H = m["grid"][0] * cell_art, m["grid"][1] * cell_art
    rng = np.random.default_rng(sum(map(ord, m["id"])) + 7)
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    dist = np.full((H, W), 1e9)
    roads, holes = old.map_roads(m, cell_art)
    for pts in roads:
        dist = np.minimum(dist, old.distance_to_segments(xx, yy, pts, reach=cell_art * 2.5))
    hole_d = np.full((H, W), 1e9)
    for hx, hy in holes:
        hole_d = np.minimum(hole_d, np.hypot(xx - hx, yy - hy))
    half = cell_art * 0.46
    wobble = (fbm(H, W, [9, 4], rng) - 0.5) * 3.0
    road_d = dist + wobble
    rgb, height, glow = PAINTERS[st["kind"]](st, W, H, road_d, half, rng)
    paint_road(st, rgb, height, glow, road_d, dist, half, rng)
    hole_style = {"road": [tuple(c) for c in st["road"]], "tip": tuple(st["tuft"][4])}
    for hx, hy in holes:
        old.paint_hole(rgb, height, glow, hole_style, hx, hy, cell_art, rng)

    folder = os.path.join(OUT, "ground")
    os.makedirs(folder, exist_ok=True)
    rgba = np.zeros((H, W, 4), np.uint8)
    rgba[..., :3] = np.clip(rgb + 0.5, 0, 255).astype(np.uint8)
    rgba[..., 3] = 255
    Image.fromarray(rgba, "RGBA").save(os.path.join(folder, m["id"] + ".png"))
    Image.fromarray(encode_normals(normals_from_height(height, 1.4), np.full((H, W), 255, np.uint8)), "RGBA").save(
        os.path.join(folder, m["id"] + "_n.png"))
    glow_path = os.path.join(folder, m["id"] + "_glow.png")
    if glow[..., 3].any():
        Image.fromarray(glow, "RGBA").save(glow_path)
    elif os.path.exists(glow_path):
        os.remove(glow_path)

    props = place_props(m, st, props_info, road_d, hole_d, half, cell_art, W, H, rng)
    with open(os.path.join(folder, m["id"] + ".json"), "w") as fh:
        json.dump({"size": [W, H], "biome": m["biome"], "props": props}, fh, indent=0)
    if preview:
        pv = Image.fromarray(rgba, "RGBA")
        for p in sorted(props, key=lambda q: q["pos"][1]):
            im = Image.open(os.path.join(OUT, "props", p["kind"] + ".png")).convert("RGBA")
            if p.get("flip"):
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
            pv.alpha_composite(im, (p["pos"][0] - im.width // 2, p["pos"][1] - im.height + 1))
        pv.save(os.path.join(preview, m["id"] + ".png"))


def place_props(m, st, props_info, road_d, hole_d, half, cell_art, W, H, rng):
    """Trees in groves and along the board's edges, small things scattered, nothing on the road or a hole."""
    out = []
    grove = fbm(H, W, [120, 50], rng)
    trees = [k for k, n in st["props"]["tree"] for _ in range(n)]
    small = [k for k, n in st["props"]["small"] for _ in range(n)]
    taken = []
    for _ in range(int(m["grid"][0] * m["grid"][1] * 0.22)):
        x, y = float(rng.uniform(6, W - 6)), float(rng.uniform(30, H - 2))
        edge = min(x, W - x, y, H - y) < cell_art * 1.3
        if not (edge or grove[int(y), int(x)] > 0.66):
            continue
        kind = trees[int(rng.integers(0, len(trees)))]
        w = props_info[kind]["size"][0]
        if road_d[int(y), int(x)] < half + w * 0.45 + 4 or hole_d[int(y), int(x)] < cell_art * 1.3 + w * 0.5:
            continue
        if any(abs(x - tx) < w * 0.6 and abs(y - ty) < 10 for tx, ty in taken):
            continue
        taken.append((x, y))
        out.append({"kind": kind, "pos": [round(x), round(y)], "cell": [int(x // cell_art), int(y // cell_art)],
                    "flip": bool(rng.random() < 0.5)})
    for _ in range(int(m["grid"][0] * m["grid"][1] * 0.6)):
        x, y = float(rng.uniform(4, W - 4)), float(rng.uniform(10, H - 2))
        kind = small[int(rng.integers(0, len(small)))]
        w = props_info[kind]["size"][0]
        if road_d[int(y), int(x)] < half + w * 0.5 + 2 or hole_d[int(y), int(x)] < cell_art * 1.1 + w * 0.5:
            continue
        out.append({"kind": kind, "pos": [round(x), round(y)], "cell": [int(x // cell_art), int(y // cell_art)],
                    "flip": bool(rng.random() < 0.5)})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("maps", nargs="*")
    ap.add_argument("--biomes", default=",".join(STYLES))
    ap.add_argument("--preview")
    a = ap.parse_args()
    biomes = set(a.biomes.split(","))
    art_path = os.path.join(OUT, "art.json")
    art = json.load(open(art_path))
    art["props"].update(P.make_all(os.path.join(OUT, "props")))
    with open(art_path, "w") as fh:
        json.dump(art, fh, indent=1)
    if a.preview:
        os.makedirs(a.preview, exist_ok=True)
    for path in sorted(glob.glob("data/maps/*.tres")):
        m = old.read_map(path)
        if m["biome"] not in biomes or m["biome"] not in STYLES or (a.maps and m["id"] not in a.maps):
            continue
        make_ground(m, art["props"], a.preview)
        print("ground", m["id"], m["biome"])
    print("import files written:", old.write_missing_imports())


if __name__ == "__main__":
    main()
