"""The campaign world map of Orrhen, version 2: a large map grown from real geology.

Design only (not wired into the game). Needs numpy, Pillow, scipy and scikit-image.

The map is 3000x1700 art pixels (about ten times the area of the first pass, see map_v1.py) and is
shown at 2x with nearest filtering. It is grown in this order:

1. Elevation: a continental dome with a noisy coast and islands, mountain ranges along four of the
   six kingdom borders, river valleys along the other two, and land shapes per kingdom (a caldera
   volcano in the Ember Reach, a high flat steppe, wet lowland forest, a frozen inland sea in
   Frostmere, terraced canyons in Sunscar, chasms into the void in the Hollow Rift).
2. Water: depressions are flooded (priority flood) so lakes form where water would pool, then
   every cell drains to its lowest neighbour and flow is accumulated; rivers are where enough
   water gathers, wider downstream.
3. Biomes: each kingdom's ground, rock and shore palettes, blended smoothly across a wide ragged
   transition band, chosen by height (beach, lowland, foothills, rock, snow), hill-shaded from
   the upper left and dithered to the ramp tones.
4. Scenery: peaks at the local highs, forests where it is wet, kingdom-specific props, towns and
   capitals, roads that find the cheapest way through passes and across bridges.

Usage:
    python3 tools/art/worldmap/gen_world_map.py [--out art/worldmap] [--seed 7] [--fast]
"""
from __future__ import annotations

import argparse
import colorsys
import contextlib
import heapq
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
from skimage.graph import route_through_array

sys.path.insert(0, str(Path(__file__).resolve().parent))
import map_v1 as v1  # noqa: E402  (sprite kit and lettering from the first pass)
from map_v1 import (ACCENT, INK, LAND_NAME, LANDS, STAGES, Spr, hexc, house, landmark,  # noqa: E402
                    pixel_text, ramp, shaded_block, _darken, _lighten)

W, H = 3000, 1700
SCALE = 2
CX, CY = 1560.0, 905.0
RX, RY = 1060.0, 730.0
ROOT = Path(__file__).resolve().parents[3]
ANGLE = {"fire": -90, "storm": -30, "nature": 30, "water": 90, "earth": 150, "void": 210}
# Kingdom borders, clockwise from Fire|Storm. Mountains or a river valley.
BORDER = ["mountains", "river", "river", "mountains", "mountains", "mountains"]
DS = 4  # the water simulation and road search run on a grid 4x coarser than the map

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
BAYER = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W].astype(np.float32)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
NX, NY = (XX - CX) / RX, (YY - CY) / RY
RN = np.sqrt(NX ** 2 + NY ** 2)
ANG = np.degrees(np.arctan2(NY, NX))


def log(msg: str, t0=[time.time()]) -> None:
    print(f"[{time.time() - t0[0]:6.1f}s] {msg}", flush=True)


# --------------------------------------------------------------------------- noise

def fbm(seed: int, scale: float, octaves: int = 4, h: int = H, w: int = W) -> np.ndarray:
    """Value-noise fBm, 0..1. `scale` is the number of cells across the width at the first octave."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = max(2, int(scale * 2 ** o))
        gw, gh = cells + 3, int(cells * h / w) + 4
        grid = rng.random((gh, gw)).astype(np.float32)
        img = Image.fromarray(grid, mode="F").resize((int(w * gw / cells), int(w * gw / cells * gh / gw)),
                                                     Image.BICUBIC)
        out += np.asarray(img, np.float32)[:h, :w] * amp
        total += amp
        amp *= 0.5
    out /= total
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def ridged(seed: int, scale: float, octaves: int = 5) -> np.ndarray:
    n = fbm(seed, scale, octaves)
    return (1.0 - np.abs(n * 2 - 1)) ** 2


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def pos(angle: float, rn: float) -> tuple[float, float]:
    a = math.radians(angle)
    return CX + rn * RX * math.cos(a), CY + rn * RY * math.sin(a)


def gauss_at(x, y, sx, sy):
    return np.exp(-(((XX - x) / sx) ** 2 + ((YY - y) / sy) ** 2))


# --------------------------------------------------------------------------- layout

def stage_layout() -> dict[int, tuple[float, float]]:
    out: dict[int, tuple[float, float]] = {}
    radii = [0.84, 0.70, 0.565, 0.445]
    wiggle = [8.0, -7.0, 6.0, -2.0]
    for li, land in enumerate(LANDS):
        for k in range(4):
            out[li * 4 + k + 1] = pos(ANGLE[land] + wiggle[k], radii[k])
    out[25] = pos(116, 0.285)
    out[26] = pos(128, 0.135)
    out[27] = (CX, CY + 6)
    return out


# --------------------------------------------------------------------------- geology

def kingdom_fields(seed: int):
    """Warped angle, soft weights per kingdom (they overlap in a wide ragged band) and border distance."""
    warp = (fbm(seed + 13, 4, 3) - 0.5) * 30 + (fbm(seed + 2, 12, 3) - 0.5) * 12
    a_w = (ANG + 90 + warp) % 360
    jitter = (fbm(seed + 40, 60, 2) - 0.5) * 9          # ragged edges inside the transition band
    weights = []
    for k in range(6):
        d = np.abs(((a_w + jitter - 60 * k + 180) % 360) - 180)
        weights.append(smoothstep(42, 18, d))
    wsum = np.maximum(sum(weights), 1e-4)
    weights = [w / wsum for w in weights]
    u = (a_w - 30) % 60
    dist_deg = np.minimum(u, 60 - u)
    b_near = ((np.floor((a_w - 30) / 60) + (u >= 30)) % 6).astype(int)
    dist_px = np.radians(dist_deg) * RN * (RX + RY) / 2
    return a_w, weights, dist_px, b_near


def elevation(seed: int, weights, dist_px, b_near, nodes):
    log("elevation")
    coast = (fbm(seed + 1, 9, 6) - 0.5) * 0.13 + (fbm(seed + 12, 2.5, 3) - 0.5) * 0.16
    land_rn = RN + coast
    cont = fbm(seed + 3, 5, 6)
    elev = (1.0 - land_rn) * 0.75 + (cont - 0.5) * 0.22
    # gentle domes and basins everywhere so lowlands are not flat
    elev += (fbm(seed + 4, 14, 4) - 0.5) * 0.06
    inland = smoothstep(0.3, 0.5, RN) * smoothstep(1.05, 0.9, RN)

    # mountain ranges along the mountain borders, river valleys along the others
    rid = ridged(seed + 20, 7, 6)
    rid_fine = ridged(seed + 21, 26, 4)
    is_mtn = np.isin(b_near, [i for i, b in enumerate(BORDER) if b == "mountains"])
    width = 95 + (fbm(seed + 22, 6, 3) - 0.5) * 80
    range_mask = np.exp(-(dist_px / width) ** 2) * inland
    elev += np.where(is_mtn, range_mask * (0.12 + 0.55 * rid + 0.12 * rid_fine), 0)
    valley = np.exp(-(dist_px / 55) ** 2) * inland
    elev -= np.where(~is_mtn, valley * 0.10, 0)

    # interior uplands: scattered hill country with its own small ranges
    hills = ridged(seed + 23, 12, 5) * smoothstep(0.62, 0.8, fbm(seed + 24, 4, 3))
    elev += hills * 0.22 * inland

    w = dict(zip(LANDS, weights))
    # Ember Reach: the Pyrrhenhall caldera volcano under stage 4, black hills
    vx, vy = nodes[4]
    vol_r = np.sqrt((XX - vx) ** 2 + ((YY - vy) * 1.25) ** 2)
    cone = np.clip(1 - vol_r / 170, 0, 1) ** 1.6 * 0.55
    crater = np.clip(1 - vol_r / 52, 0, 1) ** 0.6 * 0.42
    elev += (cone - crater) * smoothstep(0.2, 0.6, w["fire"])
    # Thunder Steppe: a high flat plain
    elev = elev + (0.20 + (elev - 0.20) * 0.45 - elev) * w["storm"] * (~is_mtn | (range_mask < 0.3))
    # Ember Reach: open ash plains between the ridges
    elev -= 0.07 * w["fire"] * inland * (range_mask < 0.4)
    # Verdant Deep: low and wet
    elev -= 0.05 * w["nature"] * inland
    # Frostmere: the frozen inland sea
    sx, sy = pos(84, 0.6)
    elev -= gauss_at(sx, sy, 200, 100) * 0.5 * smoothstep(0.3, 0.8, w["water"])
    # Sunscar: a raised table-land cut into terraces
    terr = np.floor((elev + 0.06) * 14) / 14
    elev = elev + (0.06 + (terr - elev) * 0.85) * w["earth"] * inland
    # The Heartland: a broad, gentle plateau
    heart = smoothstep(0.37, 0.27, RN + (fbm(seed + 16, 10, 3) - 0.5) * 0.12)
    elev = elev * (1 - heart) + (0.33 + (0.32 - RN) * 0.35 + (cont - 0.5) * 0.04) * heart
    return elev.astype(np.float32), heart


def priority_flood(z: np.ndarray, ocean: np.ndarray) -> np.ndarray:
    """Fill depressions so every cell can drain to the sea (Barnes et al.), with a tiny slope."""
    h, w = z.shape
    filled = z.copy()
    done = ocean.copy()
    done[0, :] = done[-1, :] = done[:, 0] = done[:, -1] = True
    heap = []
    edge = done & ndimage.binary_dilation(~done)
    for y, x in zip(*np.nonzero(edge)):
        heapq.heappush(heap, (float(filled[y, x]), int(y), int(x)))
    eps = 1e-5
    nb = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))
    while heap:
        zc, y, x = heapq.heappop(heap)
        for dy, dx in nb:
            ny, nx = y + dy, x + dx
            if 0 <= ny < h and 0 <= nx < w and not done[ny, nx]:
                done[ny, nx] = True
                if filled[ny, nx] <= zc:
                    filled[ny, nx] = zc + eps
                heapq.heappush(heap, (float(filled[ny, nx]), ny, nx))
    return filled


def hydrology(elev: np.ndarray, rain: np.ndarray):
    log("hydrology: flood")
    z = elev[DS // 2::DS, DS // 2::DS].copy()
    r = rain[DS // 2::DS, DS // 2::DS]
    ocean = z < 0
    # only the open ocean counts as sea for draining; inland basins below 0 become lakes/inland seas
    lab, _ = ndimage.label(ocean)
    border_labels = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}
    sea = np.isin(lab, list(border_labels))
    filled = priority_flood(z, sea)
    log("hydrology: flow")
    h, w = z.shape
    pad = np.pad(filled, 1, constant_values=-10)
    best = np.full(z.shape, np.inf, np.float32)
    tgt = np.zeros(z.shape + (2,), np.int32)
    yy, xx = np.mgrid[0:h, 0:w]
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
        nbv = pad[1 + dy:1 + dy + h, 1 + dx:1 + dx + w]
        drop = (filled - nbv) / (1.41421 if dy and dx else 1.0)
        better = (drop > 0) & (-drop < best)
        best = np.where(better, -drop, best)
        tgt[..., 0] = np.where(better, np.clip(yy + dy, 0, h - 1), tgt[..., 0])
        tgt[..., 1] = np.where(better, np.clip(xx + dx, 0, w - 1), tgt[..., 1])
    acc = np.where(sea, 0, r).astype(np.float64)
    order = np.argsort(-filled, axis=None)
    ty, tx = tgt[..., 0].ravel(), tgt[..., 1].ravel()
    flat = acc.ravel()
    seaf = sea.ravel()
    has = np.isfinite(best).ravel()
    for i in order:
        if seaf[i] or not has[i]:
            continue
        j = ty[i] * w + tx[i]
        if j != i:
            flat[j] += flat[i]
    acc = flat.reshape(h, w)
    depth = filled - z
    lake = (depth > 0.012) & ~sea
    lab, n = ndimage.label(lake)
    sizes = ndimage.sum(lake, lab, range(n + 1))
    lake = sizes[lab] >= 25
    lake &= lab > 0
    return {"z": z, "filled": filled, "sea": sea, "acc": acc, "tgt": tgt, "lake": lake}


def draw_rivers(hyd, elev, seed):
    """River segments from each cell to its downhill neighbour, meandering and wider downstream."""
    log("rivers")
    acc, tgt, sea, lake = hyd["acc"], hyd["tgt"], hyd["sea"], hyd["lake"]
    h, w = acc.shape
    rng = np.random.default_rng(seed + 50)
    jx = (rng.random((h, w)) - 0.5) * DS * 1.4
    jy = (rng.random((h, w)) - 0.5) * DS * 1.4
    thresh = 260.0
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    ys, xs = np.nonzero((acc > thresh) & ~sea & ~lake)
    for y, x in zip(ys, xs):
        ty, tx = tgt[y, x]
        if ty == y and tx == x:
            continue
        a = acc[y, x]
        width = int(np.clip(1 + math.log2(a / thresh) * 0.9, 1, 6))
        p0 = (x * DS + DS / 2 + jx[y, x], y * DS + DS / 2 + jy[y, x])
        p1 = (tx * DS + DS / 2 + jx[ty, tx], ty * DS + DS / 2 + jy[ty, tx])
        d.line([p0, p1], fill=width, width=width)
        if width >= 3:
            d.ellipse([p1[0] - width / 2, p1[1] - width / 2, p1[0] + width / 2, p1[1] + width / 2], fill=width)
    river = np.asarray(img)
    return river


# --------------------------------------------------------------------------- painting

BIOME = {
    #           lowland        upland        rock          shore         texture tint
    "fire":   ("4a3430", "5a4642", "2e2428", "3a3030"),
    "storm":  ("7f9a3c", "9aa046", "5e6270", "c8b880"),
    "nature": ("2f6a2e", "3f7a36", "5a6a5a", "8a8a5a"),
    "water":  ("c4dcec", "e2eef6", "8aa0b8", "d8e8f2"),
    "earth":  ("b4602e", "c88a50", "8a4428", "d8a868"),
    "void":   ("3e2a6a", "2e2050", "2a2238", "4a3a6a"),
}
HEART = ("c4bed4", "d8d2e4", "8a849c", "e8e2f0")


def tone(value: np.ndarray, pal: np.ndarray, dither: float = 0.6) -> np.ndarray:
    n = len(pal)
    b = BAYER[:value.shape[0], :value.shape[1]]
    idx = np.clip(np.floor(value * n + (b - 0.5) * dither), 0, n - 1).astype(np.int8)
    return pal[idx]


def hillshade(elev: np.ndarray, k: float = 60.0) -> np.ndarray:
    gy, gx = np.gradient(ndimage.gaussian_filter(elev, 1.2))
    nx, ny, nz = -gx * k, -gy * k, np.ones_like(elev)
    ln = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    light = np.array([-0.55, -0.62, 0.56])
    light /= np.linalg.norm(light)
    return (nx * light[0] + ny * light[1] + nz * light[2]) / ln


def paint(seed, elev, weights, heart, river, hyd, shade):
    log("paint ground")
    tex = fbm(seed + 9, 70, 3)
    patch = fbm(seed + 14, 9, 4)
    rgb = np.zeros((H, W, 3), np.float32)
    lum = np.clip((shade - 0.35) * 1.6, 0, 1)
    snow_line = 0.72
    for k, land in enumerate(LANDS):
        wk = weights[k] * (1 - heart)
        if wk.max() <= 0:
            continue
        low, up, rock, shore = BIOME[land]
        v = np.clip(lum * 0.75 + (tex - 0.5) * 0.35 + 0.1, 0, 1)
        col = np.where((patch > 0.55)[..., None], tone(v, ramp(up, 5, 0.4)), tone(v, ramp(low, 5, 0.4)))
        rock_c = tone(np.clip(lum * 0.9 - 0.1, 0, 1), ramp(rock, 6, 0.5))
        r = smoothstep(0.46, 0.6, elev + (tex - 0.5) * 0.06)[..., None] * 0.85
        col = col * (1 - r) + rock_c * r
        sn = smoothstep(snow_line - (0.18 if land == "water" else 0.0),
                        snow_line + 0.04 - (0.18 if land == "water" else 0.0), elev + (tex - 0.5) * 0.05)
        if land in ("fire", "void"):
            sn = sn * 0.0
        snow_c = tone(np.clip(lum * 1.2, 0, 1), ramp("dfe8f4", 5, 0.35))
        col = col * (1 - sn[..., None]) + snow_c * sn[..., None]
        beach = smoothstep(0.022, 0.0, elev)[..., None]
        col = col * (1 - beach) + tone(np.clip(lum + 0.1, 0, 1), ramp(shore, 5, 0.3)) * beach
        if land == "fire":      # ash fields and cinder glints
            ember = (tex > 0.93) & (BAYER > 0.7)
            col[ember] = hexc("c2401c")
        if land == "void":      # starlight specks on violet grass
            spark = (tex > 0.94) & (BAYER > 0.85)
            col[spark] = hexc("e2c8ff")
        if land == "nature":    # glow-moss
            moss = (tex > 0.95) & (BAYER > 0.85)
            col[moss] = hexc("7ff0c8")
        rgb += col * wk[..., None]

    # Heartland: prism glass plains with rainbow streaks
    hue = (fbm(seed + 11, 10, 3) * 1.5) % 1.0
    prism = np.stack([np.asarray(colorsys.hsv_to_rgb(h, 0.18, 1.0)) for h in np.linspace(0, 1, 13)[:-1]]) * 255
    pr = prism[(np.floor(hue * 12) % 12).astype(int)]
    v = np.clip(lum * 0.7 + 0.15 + (tex - 0.5) * 0.25, 0, 1)
    hc = tone(v, ramp("a8a2bc", 5, 0.36)) * 0.78 + pr * 0.22
    streak = (np.abs(((XX + YY * 0.6 + tex * 30) % 41) - 20) < 0.6) & (BAYER > 0.4)
    hc[streak] = np.minimum(hc[streak] + 30, 255)
    rgb = rgb * (1 - heart[..., None]) + hc * heart[..., None]

    log("paint water")
    sea = elev < 0
    # inland basins below sea level are inland seas or lakes too
    lake_full = np.kron(hyd["lake"], np.ones((DS, DS), bool))[:H, :W]
    lake_full = ndimage.binary_opening(ndimage.binary_closing(lake_full, iterations=2), iterations=1)
    water = sea | lake_full
    depth = np.clip(-elev / 0.35, 0, 1)
    waves = fbm(seed + 5, 90, 2)
    ocean = tone(np.clip(0.72 - depth * 0.7 + (waves - 0.5) * 0.25, 0, 1), ramp("1a4868", 6, 0.42))
    glint = (waves > 0.74) & (np.roll(waves, 1, 1) <= 0.74) & (BAYER > 0.55)
    glint = glint | np.roll(glint, 1, 1)
    ocean[glint] = hexc("5a94b8")
    wf = weights[LANDS.index("water")]
    near_land = ndimage.gaussian_filter((~water).astype(np.float32), 25)
    lab_w, _ = ndimage.label(water)
    edge_ids = set(np.unique(np.concatenate([lab_w[0], lab_w[-1], lab_w[:, 0], lab_w[:, -1]]))) - {0}
    inland_w = water & ~np.isin(lab_w, list(edge_ids))
    frozen = smoothstep(0.35, 0.6, wf) * np.maximum(smoothstep(0.05, 0.25, near_land), inland_w)
    ice = tone(np.clip(0.55 + (waves - 0.5) * 0.5 + lum * 0.2, 0, 1), ramp("b0d4ec", 5, 0.3))
    crack = np.abs(fbm(seed + 10, 12, 4) - 0.5) < 0.006
    ice[crack] = hexc("5a86b0")
    wcol = ocean * (1 - frozen[..., None]) + ice * frozen[..., None]
    rgb[water] = wcol[water]
    shallow = water & ndimage.binary_dilation(~water, iterations=4)
    rgb[shallow] = rgb[shallow] * 0.65 + np.array(hexc("4a98b4")) * 0.35 * (1 - frozen[shallow, None]) \
        + rgb[shallow] * 0.35 * frozen[shallow, None]
    foam = water & ndimage.binary_dilation(~water, iterations=1)
    rgb[foam] = np.where(frozen[foam, None] > 0.5, np.array(hexc("f4faff")), np.array(hexc("cfe6ee")))
    # cliff lip: dark edge where land drops to water below it
    lip = ~water & np.roll(water, -1, 0)
    rgb[lip] *= 0.55
    lip2 = ~water & np.roll(water, -2, 0) & ~lip
    rgb[lip2] *= 0.78

    log("paint rivers")
    rv = river > 0
    fire_w = weights[LANDS.index("fire")] * (1 - heart)
    lava = rv & (fire_w > 0.55)
    bank = ndimage.binary_dilation(rv, iterations=1) & ~rv & ~water
    rgb[bank] = rgb[bank] * 0.6
    rcol = np.where(frozen[..., None] > 0.5, np.array(hexc("9cc8e8"), np.float32),
                    np.array(hexc("3f7fae"), np.float32))
    rgb[rv] = rcol[rv]
    core = rv & (river >= 3) & (BAYER > 0.5) & (frozen < 0.5)
    rgb[core] = hexc("5a9ac4")
    rgb[lava] = hexc("ff8a2a")
    rgb[lava & (river >= 2) & (BAYER > 0.4)] = hexc("ffd060")
    glow = ndimage.binary_dilation(lava, iterations=3) & ~lava & ~water
    rgb[glow] = rgb[glow] * 0.6 + np.array(hexc("c2401c")) * 0.4
    return np.clip(rgb, 0, 255), water, lava


def outer_hollow(rgb, seed, water):
    """The top-left corner beyond the edge of the world: a starfield behind a glowing rim."""
    log("outer hollow")
    n_edge = fbm(seed + 6, 6, 5)
    d = np.sqrt((XX / 880.0) ** 2 + (YY / 640.0) ** 2) + (n_edge - 0.5) * 0.3 + (fbm(seed + 7, 2, 3) - .5) * .25
    hol = (d < 1.0) & water
    neb = fbm(seed + 8, 5, 5)
    sky = tone(np.clip(neb * 0.7 - 0.05 + (1 - d) * 0.2, 0, 1), ramp("1b1030", 6, 0.3, 0.01), 0.9)
    rgb[hol] = sky[hol]
    rim = ndimage.binary_dilation(hol, iterations=3) & ~hol & water
    rgb[rim] = hexc("6a3aa8")
    rgb[ndimage.binary_dilation(hol, iterations=1) & ~hol & water] = hexc("c79bff")
    rng = np.random.default_rng(seed + 9)
    stars = hol & (rng.random((H, W)) > 0.994)
    rgb[stars] = hexc("e8d8ff")
    big = hol & (rng.random((H, W)) > 0.9993)
    rgb[ndimage.binary_dilation(big) & hol] = hexc("b8a0e8")
    rgb[big] = (255, 255, 255)
    return hol


def void_chasms(rgb, seed, weights, heart, water, elev):
    """Holes in the Hollow Rift that drop into the starry dark, with a lit far rim and a dark near wall."""
    n = fbm(seed + 30, 18, 4)
    wv = weights[LANDS.index("void")] * (1 - heart)
    hole = (n > 0.74) & (wv > 0.7) & ~water & (elev < 0.45)
    hole = ndimage.binary_opening(hole, iterations=2)
    rng = np.random.default_rng(seed + 31)
    rgb[hole] = hexc("0a0614")
    rgb[hole & (rng.random((H, W)) > 0.985)] = hexc("d8c8ff")
    wall = hole & ~np.roll(hole, 3, 0)          # the near (upper) wall seen from above
    rgb[wall] = hexc("2a1e40")
    rim_far = ~hole & np.roll(hole, 1, 0)       # lit lip below the hole
    rgb[rim_far] = hexc("8a6ac8")
    rim_near = ~hole & np.roll(hole, -1, 0)
    rgb[rim_near] = hexc("140c22")
    return hole


# --------------------------------------------------------------------------- sprites

class KSpr(Spr):
    """A Spr whose shape coordinates are multiplied by k: the same designs drawn larger and finer."""

    def __init__(self, w, h, k=2):
        self.k = k
        super().__init__(int(w * k), int(h * k))

    def _p(self, pts):
        return [(x * self.k, y * self.k) for x, y in pts]

    def rect(self, x0, y0, x1, y1, c):
        k = self.k
        self.d.rectangle([x0 * k, y0 * k, (x1 + 1) * k - 1, (y1 + 1) * k - 1], fill=hexc(c) + (255,))

    def poly(self, pts, c):
        self.d.polygon(self._p(pts), fill=hexc(c) + (255,))

    def ell(self, x0, y0, x1, y1, c):
        k = self.k
        self.d.ellipse([x0 * k, y0 * k, (x1 + 1) * k - 1, (y1 + 1) * k - 1], fill=hexc(c) + (255,))

    def px(self, x, y, c, glow=False):
        k = self.k
        self.d.rectangle([x * k, y * k, x * k + k - 1, y * k + k - 1], fill=hexc(c) + (255,))

    def line(self, pts, c, w=1):
        self.d.line(self._p(pts), fill=hexc(c) + (255,), width=max(1, int(w * self.k * 0.75)))


@contextlib.contextmanager
def scaled(k):
    orig = v1.Spr
    v1.Spr = lambda w, h: KSpr(w, h, k)
    try:
        yield
    finally:
        v1.Spr = orig


def peak_sprite(rng, size: int, rock: str, snow: bool, land: str) -> Image.Image:
    """A chiselled mountain of one to three summits: lit west faces, dark east faces, ridge lines,
    an optional snow cap. Widths, heights and summit positions vary so ranges never look stamped."""
    w = int(size * rng.uniform(0.85, 1.5))
    h = int(size * rng.uniform(0.55, 0.95))
    s = Spr(w + 4, h + 2)
    pal = ramp(rock, 5, 0.55)
    c = ["%02x%02x%02x" % tuple(int(v) for v in p) for p in pal]
    base = h
    summits = [(rng.uniform(0.3, 0.7), 1.0)]
    if w > 14 and rng.random() < 0.6:
        summits.append((rng.choice([rng.uniform(0.1, 0.3), rng.uniform(0.7, 0.9)]), rng.uniform(0.5, 0.75)))
    if w > 22 and rng.random() < 0.4:
        summits.append((rng.uniform(0.15, 0.85), rng.uniform(0.4, 0.6)))
    for fx, fh in sorted(summits, key=lambda t: t[1]):
        px_ = 2 + int(fx * w)
        top = int(base - h * fh)
        half = int(h * fh * rng.uniform(0.8, 1.15))
        l, r = max(0, px_ - half), min(w + 3, px_ + half)
        s.poly([(l, base), (px_, top), (r, base)], c[2])
        s.poly([(l, base), (px_, top), (px_ - 1, base)], c[3])
        s.poly([(px_, top), (px_ - 1, base), (px_ - max(2, half // 3), base)], c[4])
        s.poly([(px_, top), (r, base), (px_ + max(2, half // 3), base)], c[1])
        s.line([(px_, top), (px_ + half // 4, top + (base - top) * 0.6)], c[0])
        if snow and fh > 0.55:
            sh = max(3, (base - top) // 3)
            s.poly([(px_ - sh * 0.8, top + sh), (px_, top), (px_ + sh * 0.8, top + sh), (px_ + 1, top + sh - 2),
                    (px_ - 2, top + sh - 1)], "eef4ff")
            s.poly([(px_, top), (px_ + sh * 0.8, top + sh), (px_ + 1, top + sh - 2)], "b8c8e0")
        if land == "fire" and fh == 1.0 and rng.random() < 0.3:
            s.px(px_, top + 1, "ffb040")
            s.line([(px_, top + 2), (px_ + 2, top + (base - top) * 0.5)], "c2401c")
    return s.done()


def tree_sprite(rng, land: str) -> Image.Image:
    if land == "water":                     # snowy pine
        h = int(rng.integers(8, 13))
        s = Spr(7, h + 1)
        s.poly([(0, h - 2), (3, 0), (6, h - 2)], "2c5a50")
        s.poly([(3, 0), (6, h - 2), (4, h - 2)], "1c3a3a")
        s.poly([(1, h // 2), (3, 1), (4, h // 2 - 1)], "e8f2fa")
        s.rect(3, h - 2, 3, h, "4a3a2a")
        return s.done((14, 26, 30))
    if land == "fire":                      # charred dead tree
        s = Spr(7, 9)
        s.line([(3, 8), (3, 1)], "1a1214")
        s.line([(3, 4), (0, 2)], "1a1214")
        s.line([(3, 3), (6, 1)], "2a1e20")
        s.px(6, 1, "ff8a2a")
        return s.done((10, 6, 8))
    if land == "void":                      # glowing star-mushroom
        r = int(rng.integers(3, 5))
        s = Spr(2 * r + 1, 2 * r + 3)
        s.rect(r, r, r, 2 * r + 2, "6a5a8a")
        s.ell(0, 0, 2 * r, r + 1, "7a4ab8")
        s.ell(1, 0, r, r - 1, "b58ae8")
        s.px(r, 1, "f0e0ff")
        return s.done((22, 10, 40))
    if land == "earth":                     # dry thorn tree
        s = Spr(9, 8)
        s.line([(4, 7), (4, 3)], "4a2a1a")
        s.ell(0, 0, 8, 4, "7a6a2e")
        s.ell(1, 0, 5, 2, "a8984a")
        return s.done((30, 16, 10))
    # broadleaf, darker in the deep forest
    r = int(rng.integers(3, 7)) if land == "nature" else int(rng.integers(2, 5))
    s = Spr(2 * r + 2, 2 * r + 3)
    base = ("1f4a26", "2e6b30", "4a8f3a", "8ccf5a") if land == "nature" else ("3a5a22", "557a2a", "7a9a3a", "b4c860")
    s.ell(0, 1, 2 * r, 2 * r + 1, base[0])
    s.ell(1, 0, 2 * r - 2, 2 * r - 1, base[1])
    s.ell(2, 1, r + 1, r, base[2])
    s.px(3, 2, base[3])
    return s.done((16, 30, 18))


def stones_sprite(rng) -> Image.Image:
    n = int(rng.integers(3, 7))
    s = Spr(4 * n + 2, 9)
    for i in range(n):
        x, hh = i * 4, int(rng.integers(4, 8))
        s.rect(x, 8 - hh, x + 2, 8, "8a8a94")
        s.rect(x, 8 - hh, x, 8, "c0c0cc")
        s.rect(x + 2, 8 - hh, x + 2, 8, "5a5a66")
    return s.done()


def step_sprite(rng) -> Image.Image:
    w = int(rng.integers(6, 12))
    s = Spr(w, 5)
    s.rect(0, 0, w - 1, 1, "9a8ac0")
    s.rect(0, 2, w - 1, 4, "4a3a70")
    s.px(1, 0, "e0d0ff")
    return s.done((20, 10, 40))


def crystal_sprite(rng) -> Image.Image:
    hgt = int(rng.integers(5, 11))
    s = Spr(5, hgt)
    hue = rng.random()
    c = "%02x%02x%02x" % tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.28, 1.0))
    d = "%02x%02x%02x" % tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.35, 0.72))
    s.poly([(0, hgt - 1), (2, 0), (4, hgt - 1)], c)
    s.poly([(2, 0), (4, hgt - 1), (2, hgt - 1)], d)
    s.px(1, 2, "ffffff")
    return s.done((70, 64, 96))


def ruin_sprite(rng) -> Image.Image:
    with scaled(1):
        return v1.ruin(rng)


def town_sprite(num: int, land: str, rng, capital: bool) -> Image.Image:
    """A town: houses packed around a square, a wall or palisade for forts; capitals add a landmark."""
    if capital:
        k = 2
        lw, lh = 46 * k, 40 * k
        w, h = lw + 60, lh + 40
        s = Spr(w, h)
        ls = KSpr(46, 40, k)
        landmark(ls, land, 46, 40)
        lim = ls.done()
        n_house, rad = 30, (w / 2 - 6, h / 2 - 6)
    else:
        w, h = 64, 46
        s = Spr(w, h)
        lim = None
        n_house, rad = 14 + int(rng.integers(0, 5)), (w / 2 - 6, h / 2 - 8)
    cx, cy = w / 2, h / 2 + 2
    spots = []
    tries = 0
    hw = 8 if land == "storm" else 7
    while len(spots) < n_house and tries < 2000:
        tries += 1
        a, t = rng.uniform(0, 2 * math.pi), math.sqrt(rng.uniform(0.05, 1.0))
        x, y = cx + rad[0] * t * math.cos(a) - hw / 2, cy + rad[1] * t * math.sin(a) - 4
        if lim is not None and abs(x + hw / 2 - cx) < lw / 2 - 4 and y + 8 > cy - lh / 2 - 8 and y < cy + lh / 2 - 22:
            continue
        if x < 1 or y < 5 or x + hw > w - 2 or y + 10 > h - 1:
            continue
        if all(abs(x - px) > hw + 1 or abs(y - py) > 9 for px, py in spots):
            spots.append((x, y))
    if num in (2, 11, 6):          # forts: a ring wall or palisade
        wallc = {"fire": ("6a5a50", "8a7a70"), "nature": ("4a6a2a", "6a8a3a"), "storm": ("7a6a50", "a89a78")}[land]
        s.d.ellipse([2, 4, w - 3, h - 2], outline=hexc(wallc[0]) + (255,), width=2)
        for k2 in range(0, 360, 20):
            a = math.radians(k2)
            s.px(int(cx + (w / 2 - 3) * math.cos(a)), int(h / 2 + 1 + (h / 2 - 4) * math.sin(a)), wallc[1])
    for x, y in sorted(spots, key=lambda p: p[1]):
        if lim is not None and y > cy - 6:
            continue
        house(s, int(x), int(y), land, w=hw)
    if lim is not None:
        s.im.alpha_composite(lim.crop((1, 1, lim.width - 1, lim.height - 1)),
                             (int(cx - lw / 2), int(cy - lh / 2 - 6)))
        for x, y in sorted(spots, key=lambda p: p[1]):
            if y > cy - 6:
                house(s, int(x), int(y), land, w=hw)
    return s.done()


def crossmere_sprite(rng) -> Image.Image:
    """The crossroads market town: tents, carts and a square where every road met."""
    w, h = 80, 56
    s = Spr(w, h)
    s.rect(0, h // 2 - 1, w - 1, h // 2 + 1, "d8c49a")
    s.rect(w // 2 - 1, 0, w // 2 + 1, h - 1, "d8c49a")
    s.ell(w // 2 - 9, h // 2 - 6, w // 2 + 9, h // 2 + 6, "e8dcb8")
    s.rect(w // 2 - 1, h // 2 - 4, w // 2 + 1, h // 2 + 1, "8a8a94")
    lands = ["fire", "storm", "nature", "water", "earth", "void"]
    spots = []
    for _ in range(400):
        x, y = rng.uniform(3, w - 11), rng.uniform(6, h - 11)
        if abs(x + 4 - w / 2) < 12 and abs(y + 4 - h / 2) < 10:
            continue
        if abs(y + 4 - h / 2) < 4 or abs(x + 4 - w / 2) < 6:
            continue
        if all(abs(x - px) > 9 or abs(y - py) > 9 for px, py in spots):
            spots.append((x, y))
    for x, y in sorted(spots, key=lambda p: p[1])[:22]:
        house(s, int(x), int(y), lands[int(rng.integers(0, 6))], w=7)
    return s.done()


def lumen_gate_sprite() -> Image.Image:
    s = Spr(40, 34)
    s.poly([(0, 30), (6, 4), (34, 4), (40, 30)], "f4f0fa")
    s.rect(12, 10, 27, 33, "3a3448")
    s.ell(12, 4, 27, 18, "3a3448")
    s.rect(14, 14, 25, 33, "201828")
    s.rect(0, 2, 8, 33, "e8e2f0")
    s.rect(31, 2, 39, 33, "c8c0d8")
    s.rect(0, 0, 8, 2, "ffffff")
    s.rect(31, 0, 39, 2, "e8e2f0")
    s.px(19, 7, "fff2b8")
    s.px(20, 7, "fff2b8")
    return s.done()


def stonework(im: Image.Image, seed: int, brick=(7, 3), skip_bright: int = 200) -> Image.Image:
    """Give a large flat-shaded sprite masonry: staggered brick lines, chips and a dithered grain."""
    a = np.asarray(im).astype(np.float32).copy()
    h, w = a.shape[:2]
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:h, 0:w]
    solid = a[..., 3] > 0
    dark = a[..., :3].max(-1) < 30
    bright = a[..., :3].max(-1) > skip_bright
    body = solid & ~dark & ~bright
    bw, bh = brick
    row = yy // bh
    mortar = (yy % bh == 0) | (((xx + (row % 2) * (bw // 2)) % bw) == 0)
    a[body & mortar, :3] *= 0.72
    grain = rng.random((h, w))
    a[body & (grain > 0.93), :3] *= 0.8
    a[body & (grain < 0.04), :3] = np.minimum(a[body & (grain < 0.04), :3] * 1.25, 255)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8))


# --------------------------------------------------------------------------- compositing

class Board:
    def __init__(self):
        self.items: list[tuple[float, Image.Image, int, int, int]] = []

    def put(self, im: Image.Image, x: float, y: float, shadow: int = 2):
        self.items.append((y, im, int(round(x - im.width / 2)), int(round(y - im.height)), shadow))

    def bake(self, base: Image.Image) -> Image.Image:
        out = base.copy()
        sh = Image.new("RGBA", out.size, (0, 0, 0, 0))
        cache: dict[int, Image.Image] = {}
        for _, im, x0, y0, s in self.items:
            if not s:
                continue
            key = id(im)
            if key not in cache:
                a = np.asarray(im)[..., 3]
                sil = np.zeros(a.shape + (4,), np.uint8)
                sil[..., 3] = np.where(a > 0, 100, 0)
                sil[..., :3] = (12, 8, 24)
                cache[key] = Image.fromarray(sil)
            sh.alpha_composite(cache[key], (max(0, x0 + s), max(0, y0 + s // 2 + 1)))
        out.alpha_composite(sh)
        for _, im, x0, y0, _ in sorted(self.items, key=lambda t: t[0]):
            if x0 < 0 or y0 < 0:
                cut = im.crop((max(0, -x0), max(0, -y0), im.width, im.height))
                out.alpha_composite(cut, (max(0, x0), max(0, y0)))
            else:
                out.alpha_composite(im, (x0, y0))
        return out


def glow_pass(img: Image.Image, mask: np.ndarray, colour: str, radius: int, strength: float) -> Image.Image:
    """Stepped light pools around glowing things (lava, the Crack, the Heartstone)."""
    blur = ndimage.gaussian_filter(mask.astype(np.float32), radius)
    blur = blur / (blur.max() + 1e-6)
    f = np.floor(np.clip(blur * 2.0, 0, 1) * 4 + BAYER * 0.9) / 4 * strength
    a = np.asarray(img).astype(np.float32)
    a[..., :3] = np.clip(a[..., :3] + f[..., None] * np.array(hexc(colour), np.float32), 0, 255)
    return Image.fromarray(a.astype(np.uint8))


# --------------------------------------------------------------------------- roads

def road_paths(nodes, cost_full, assault_pts):
    log("roads")
    cost = cost_full
    paths = []

    def route(a, b):
        ia = (int(a[1] / DS), int(a[0] / DS))
        ib = (int(b[1] / DS), int(b[0] / DS))
        idx, _ = route_through_array(cost, ia, ib, fully_connected=True, geometric=True)
        return [((x + 0.5) * DS, (y + 0.5) * DS) for y, x in idx]

    for li in range(6):
        for k in range(3):
            paths.append(("road", route(nodes[li * 4 + k + 1], nodes[li * 4 + k + 2])))
        paths.append(("road", route(nodes[li * 4 + 4], pos(ANGLE[LANDS[li]] - 2, 0.285))))
    ring = [pos(a, 0.285 + 0.01 * math.sin(math.radians(a * 5))) for a in range(0, 361, 4)]
    paths.append(("ring", ring))
    paths.append(("royal", route(nodes[25], nodes[26]) + route(nodes[26], nodes[27])))
    paths.append(("assault", assault_pts))
    return paths


def smooth_path(pts, n=3):
    pts = np.array(pts, np.float32)
    if len(pts) < 5:
        return pts
    for _ in range(n):
        pts[1:-1] = (pts[:-2] + pts[1:-1] * 2 + pts[2:]) / 4
    return pts


def draw_roads(base: Image.Image, paths, river, water):
    d = ImageDraw.Draw(base)
    bridges = []
    for kind, pts in paths:
        p = [tuple(q) for q in smooth_path(pts)] if kind not in ("ring", "assault") else pts
        if kind == "assault":
            continue
        fill, edge = {"road": ("d8c49a", "4a3a2e"), "ring": ("efe4c8", "6a5a48"),
                      "royal": ("fff6d8", "6a5a48")}[kind]
        wd = 4 if kind == "road" else 5
        d.line(p, fill=hexc(edge) + (255,), width=wd + 2, joint="curve")
        d.line(p, fill=hexc(fill) + (255,), width=wd - 1, joint="curve")
        for x, y in p[::2]:
            xi, yi = int(x), int(y)
            if 0 <= xi < W and 0 <= yi < H and river[yi, xi] > 0:
                bridges.append((xi, yi))
    for x, y in bridges:
        d.rectangle([x - 4, y - 3, x + 4, y + 3], fill=hexc("6a4a2a") + (255,))
        d.rectangle([x - 4, y - 3, x + 4, y - 2], fill=hexc("a8804a") + (255,))
        d.line([(x - 4, y + 3), (x + 4, y + 3)], fill=INK + (255,))
    return base


def draw_assault(img: Image.Image, pts):
    d = ImageDraw.Draw(img)
    pts = [(float(x), float(y)) for x, y in pts]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(1, int(math.hypot(x1 - x0, y1 - y0) / 7))
        for k in range(0, n, 2):
            a, b = k / n, min(1, (k + 1) / n)
            seg = [(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)]
            d.line(seg, fill=(42, 10, 58, 255), width=7)
            d.line(seg, fill=hexc("d07cff") + (255,), width=3)


# --------------------------------------------------------------------------- main

CITY_LABEL = {8: (-1, 0, "rm"), 12: (-1, 0, "rm"), 25: (-1, 0, "rm"), 26: (-1, 0, "rm"), 27: (1, 0, "lm"),
              2: (-1, 0, "rm"), 3: (1, 0, "lm"), 6: (1, 0, "lm"), 19: (-1, 0, "rm"), 21: (1, 0, "lm"),
              23: (1, 0, "lm"), 7: (1, 0, "lm"), 11: (-1, 0, "rm")}
LAND_LABEL = {"fire": (-82, 0.97), "storm": (-36, 1.0), "nature": (40, 0.97), "water": (100, 0.95),
              "earth": (150, 1.02), "void": (196, 0.86)}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "art" / "worldmap"))
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    seed = args.seed
    rng = np.random.default_rng(seed)
    nodes = stage_layout()

    a_w, weights, dist_px, b_near = kingdom_fields(seed)
    elev, heart = elevation(seed, weights, dist_px, b_near, nodes)
    # keep every stage on dry land, away from the shore: move it to the nearest good spot
    dry = ndimage.binary_erosion(elev > 0.04, iterations=14)
    for n, (x, y) in list(nodes.items()):
        if dry[int(y), int(x)]:
            continue
        best = None
        for r in range(6, 260, 6):
            for a in range(0, 360, 10):
                qx, qy = x + r * math.cos(math.radians(a)), y + r * math.sin(math.radians(a))
                if 0 <= qx < W and 0 <= qy < H and dry[int(qy), int(qx)]:
                    best = (qx, qy)
                    break
            if best:
                break
        nodes[n] = best or (x, y)
    rain = 0.6 + weights[LANDS.index("nature")] * 1.2 + weights[LANDS.index("water")] * 0.6 \
        - weights[LANDS.index("earth")] * 0.3 - weights[LANDS.index("fire")] * 0.2
    hyd = hydrology(elev, rain.astype(np.float32))
    vx, vy = nodes[4]
    hy, hx = np.mgrid[0:hyd["lake"].shape[0], 0:hyd["lake"].shape[1]]
    hyd["lake"] &= np.hypot(hx * DS - vx, hy * DS - vy) > 90
    river = draw_rivers(hyd, elev, seed)
    shade = hillshade(elev)
    rgb, water, lava = paint(seed, elev, weights, heart, river, hyd, shade)
    hol = outer_hollow(rgb, seed, water)
    chasm = void_chasms(rgb, seed, weights, heart, water, elev)

    # the Crack: a glowing fissure from deep in the Hollow Rift out over the edge of the world
    log("the Crack")
    crack_pts = [pos(208, 0.62), pos(214, 0.74), pos(207, 0.86), pos(214, 0.98), pos(210, 1.12), (560, 330),
                 (380, 250)]
    jag = []
    for (x0, y0), (x1, y1) in zip(crack_pts, crack_pts[1:]):
        for k in range(10):
            t = k / 10
            jag.append((x0 + (x1 - x0) * t + rng.uniform(-6, 6), y0 + (y1 - y0) * t + rng.uniform(-6, 6)))
    jag.append(crack_pts[-1])
    cimg = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(cimg)
    cd.line(jag, fill=1, width=11)
    cd.line(jag, fill=2, width=5)
    cd.line(jag, fill=3, width=2)
    cm = np.asarray(cimg)
    halo = ndimage.binary_dilation(cm > 0, iterations=4)
    rgb[halo] = rgb[halo] * 0.4 + np.array(hexc("4a1a80")) * 0.6
    rgb[cm == 1] = hexc("7a3ad0")
    rgb[cm == 2] = hexc("c79bff")
    rgb[cm == 3] = hexc("f8f0ff")

    # posterize the painted ground to a shared palette with ordered dithering, so blends stay pixel art
    log("posterize")
    noisy = np.clip(rgb + (BAYER[..., None] - 0.5) * 18, 0, 255).astype(np.uint8)
    q = Image.fromarray(noisy).quantize(colors=200, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    rgb = np.asarray(q.convert("RGB")).astype(np.float32)
    base = Image.fromarray(rgb.astype(np.uint8)).convert("RGBA")

    # --- roads: cheapest paths over the coarse grid (slopes, mountains and water cost more)
    z = hyd["z"]
    gy, gx = np.gradient(z)
    slope = np.sqrt(gx ** 2 + gy ** 2)
    water_c = water[DS // 2::DS, DS // 2::DS]
    river_c = river[DS // 2::DS, DS // 2::DS] > 0
    chasm_c = chasm[DS // 2::DS, DS // 2::DS]
    cost = 1 + slope * 600 + np.clip(z - 0.42, 0, 1) * 60 + water_c * 400 + river_c * 12 + chasm_c * 400
    assault = [nodes[27], pos(200, 0.38), pos(208, 0.6), pos(212, 0.8), pos(211, 1.0), (560, 330), (430, 270),
               (300, 210)]
    paths = road_paths(nodes, cost, assault)
    base = draw_roads(base, paths, river, water)

    # --- scenery
    log("scenery")
    board = Board()
    avoid = np.zeros((H, W), bool)
    for kind, pts in paths:
        for x, y in pts:
            xi, yi = int(x), int(y)
            avoid[max(0, yi - 7):yi + 7, max(0, xi - 7):xi + 7] = True
    for n, (x, y) in nodes.items():
        r = 70 if n in (4, 8, 12, 16, 20, 24) else 46
        if n == 27:
            r = 190
        avoid[max(0, int(y) - r):int(y) + r // 2, max(0, int(x) - r):int(x) + r] = True
    avoid |= halo | (cm > 0)

    land_idx = np.argmax(np.stack(weights), 0)
    blocked = water | avoid | (river > 0) | chasm | hol | lava

    # mountain peaks at local highs
    hi = ndimage.maximum_filter(elev, size=19)
    peaks = (elev >= hi) & (elev > 0.45) & ~blocked
    ys, xs = np.nonzero(peaks)
    rock_by_land = {land: BIOME[land][2] for land in LANDS}
    peak_cache = {}
    for y, x in zip(ys, xs):
        land = "heart" if heart[y, x] > 0.5 else LANDS[land_idx[y, x]]
        if land == "heart":
            continue
        size = int(np.clip(14 + (elev[y, x] - 0.45) * 130, 14, 46))
        snow = elev[y, x] > (0.6 if land != "water" else 0.45) and land not in ("fire", "void")
        key = (land, size // 3, snow, int(rng.integers(0, 8)))
        if key not in peak_cache:
            peak_cache[key] = peak_sprite(np.random.default_rng(hash(key) % 2 ** 32), size, rock_by_land[land],
                                          snow, land)
        board.put(peak_cache[key], x, y + 4, 3)
    # foothill bumps between peaks
    for gy0 in range(0, H - 12, 12):
        for gx0 in range(0, W - 14, 14):
            x, y = gx0 + int(rng.integers(0, 14)), gy0 + int(rng.integers(0, 12))
            if blocked[y, x] or elev[y, x] < 0.47 or heart[y, x] > 0.5 or rng.random() < 0.2:
                continue
            land = LANDS[land_idx[y, x]]
            size = int(np.clip(14 + (elev[y, x] - 0.47) * 110, 14, 30))
            snow = elev[y, x] > 0.66 and land in ("water", "storm", "earth", "nature")
            key = (land, size // 2, snow, int(rng.integers(0, 8)))
            if key not in peak_cache:
                peak_cache[key] = peak_sprite(np.random.default_rng(hash(key) % 2 ** 32), size,
                                              rock_by_land[land], snow, land)
            board.put(peak_cache[key], x, y + 3, 2)
    log(f"peaks placed ({len(board.items)})")

    # forests and props by biome, on a jittered grid so they never clump into one pixel
    tree_cache = {land: [tree_sprite(np.random.default_rng(i * 7 + j), land) for j in range(10)]
                  for i, land in enumerate(LANDS)}
    stones = [stones_sprite(np.random.default_rng(i)) for i in range(6)]
    steps = [step_sprite(np.random.default_rng(i)) for i in range(8)]
    crystals = [crystal_sprite(np.random.default_rng(i)) for i in range(12)]
    ruins = [ruin_sprite(np.random.default_rng(i)) for i in range(10)]
    forest_n = fbm(seed + 60, 10, 4)
    acc_full = np.kron(np.log1p(hyd["acc"]), np.ones((DS, DS)))[:H, :W]
    cell = 7
    for gy0 in range(0, H - cell, cell):
        for gx0 in range(0, W - cell, cell):
            x = gx0 + int(rng.integers(0, cell))
            y = gy0 + int(rng.integers(0, cell))
            if blocked[y, x] or elev[y, x] > 0.5:
                continue
            if heart[y, x] > 0.5:
                rr = RN[y, x]
                if rr < 0.24 and rng.random() < 0.06:
                    board.put(ruins[int(rng.integers(0, 10))], x, y, 1)
                elif rng.random() < 0.05:
                    board.put(crystals[int(rng.integers(0, 12))], x, y, 1)
                continue
            land = LANDS[land_idx[y, x]]
            wet = acc_full[y, x]
            f = forest_n[y, x]
            p = {"nature": 0.25 + f * 0.9, "storm": (wet > 4.2) * 0.35 + (f > 0.72) * 0.25,
                 "water": (f > 0.48) * 0.55, "earth": (f > 0.75) * 0.08, "fire": (f > 0.6) * 0.18,
                 "void": (f > 0.62) * 0.3}[land]
            if rng.random() < p:
                board.put(tree_cache[land][int(rng.integers(0, 10))], x, y, 2)
            elif land == "storm" and rng.random() < 0.004:
                board.put(stones[int(rng.integers(0, 6))], x, y, 1)
            elif land == "void" and rng.random() < 0.01:
                board.put(steps[int(rng.integers(0, 8))], x, y - 8, 6)
    # floating steps across chasms
    ys, xs = np.nonzero(chasm & (BAYER > 0.97))
    for i in rng.permutation(len(xs))[:260]:
        board.put(steps[int(rng.integers(0, 8))], xs[i], ys[i], 8)
    log(f"scenery placed ({len(board.items)})")

    # --- towns, capitals, Solenne, Nhal Vorath
    log("cities")
    for n, (x, y) in nodes.items():
        if n == 27:
            with scaled(2):
                im = v1.solenne_sprite()
            im = stonework(im, seed + 71, brick=(5, 3), skip_bright=250)
            board.put(im, x, y + 66, 4)
            continue
        if n == 26:
            board.put(lumen_gate_sprite(), x, y - 6, 3)
            continue
        if n == 25:
            board.put(crossmere_sprite(rng), x, y - 8, 2)
            continue
        land = LANDS[(n - 1) // 4]
        capital = n % 4 == 0
        im = town_sprite(n, land, rng, capital)
        board.put(im, x, y - 8, 2)
    with scaled(3):
        nv = v1.nhal_vorath_sprite()
    nv = stonework(nv, seed + 70, brick=(9, 4), skip_bright=150)
    citadel = (300, 560)
    board.put(nv, *citadel, 0)

    img = board.bake(base)
    log("glow")
    img = glow_pass(img, lava | (cm > 1), "ff6a1a", 6, 0.35)
    img = glow_pass(img, cm > 0, "9a5aff", 10, 0.3)
    hs = np.zeros((H, W), bool)
    hs[int(CY) - 34:int(CY) - 26, int(CX) - 4:int(CX) + 4] = True
    img = glow_pass(img, hs, "fff2b8", 14, 0.22)
    draw_assault(img, assault)

    def frame(im: Image.Image) -> Image.Image:
        a = np.asarray(im).astype(np.float32)
        v = np.clip(1 - (np.maximum(np.abs(XX - W / 2) / (W / 2), np.abs(YY - H / 2) / (H / 2)) - 0.88) * 3, 0.65, 1)
        a[..., :3] *= (np.floor(v * 8) / 8)[..., None]
        a[:5, :, :3] = a[-5:, :, :3] = a[:, :5, :3] = a[:, -5:, :3] = hexc("3b2a1a")
        a[2, 2:-2, :3] = a[-3, 2:-2, :3] = a[2:-2, 2, :3] = a[2:-2, -3, :3] = hexc("c9a35a")
        return Image.fromarray(a.astype(np.uint8))

    clean = frame(img)
    clean.convert("RGB").save(out / "world_map_v2_clean.png")

    # --- stage medallions
    log("medallions")
    marked = img.copy()
    for n, (x, y) in nodes.items():
        land = LANDS[(n - 1) // 4] if n <= 24 else "heart"
        with scaled(2):
            m = v1.medallion(str(n), ACCENT[land], big=n % 4 == 0 or n > 24)
        my = y + 6 if n != 27 else y + 74
        marked.alpha_composite(m, (int(x - m.width / 2), int(my - m.height / 2)))
    with scaled(2):
        am = v1.letter_medallion([".#.", "#.#", "###", "#.#", "#.#"], "d07cff")
    av = (citadel[0], citadel[1] - 3 * 170 + 3 * 58)
    marked.alpha_composite(am, (int(av[0] - am.width / 2), int(av[1] - am.height / 2)))
    marked = frame(marked)
    marked.convert("RGB").save(out / "world_map_v2.png")

    # --- labelled preview at 2x
    log("labels")
    lab = marked.copy()
    for land, (ang, rr) in LAND_LABEL.items():
        ac = ACCENT[land]
        txt = pixel_text(LAND_NAME[land], ["ffffff", _lighten(ac), ac, _darken(ac, 0.8), _darken(ac, 0.6)], unit=4)
        x, y = pos(ang, rr)
        lab.alpha_composite(txt, (int(np.clip(x - txt.width / 2, 20, W - txt.width - 20)), int(y - txt.height / 2)))
    title = pixel_text("ORRHEN", ["fff6d0", "ffe08a", "f2c14e", "d89a32", "a86a22"], unit=9)
    lab.alpha_composite(title, (W - title.width - 60, 50))
    sub = pixel_text("THE WAR OF SEVEN CROWNS", ["fff6d0", "efd58e", "c9a35a", "9a6e38", "6b4a28"], unit=3)
    lab.alpha_composite(sub, (W - 60 - title.width // 2 - sub.width // 2, 50 + title.height + 8))
    t3 = pixel_text("NHAL VORATH", ["f0d8ff", "d0a8ff", "b27cff", "8a4ad8", "6a2ab0"], unit=4)
    lab.alpha_composite(t3, (citadel[0] - t3.width // 2, citadel[1] + 10))
    big = lab.resize((W * SCALE, H * SCALE), Image.NEAREST)
    d = ImageDraw.Draw(big)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 30)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 26)
    for n, (x, y) in nodes.items():
        side, _, anchor = CITY_LABEL.get(n, (0, 0, "mt"))
        my = (y + 6 if n != 27 else y + 74)
        if anchor == "mt":
            tx, ty = x, my + 20
        else:
            tx, ty = x + side * 22, my
        name = STAGES[n][1] if n != 27 else "Solenne, the Crowned Heart"
        d.text((tx * SCALE, ty * SCALE), name, font=font, anchor=anchor,
               fill=(255, 242, 184) if n > 24 else (255, 246, 224), stroke_width=5, stroke_fill=INK)
    d.text((citadel[0] * SCALE, (citadel[1] + 48) * SCALE), "The final assault", font=small, anchor="mt",
           fill=(240, 216, 255), stroke_width=5, stroke_fill=INK)
    cx_, cy_ = pos(212, 1.06)
    d.text((cx_ * SCALE + 50, cy_ * SCALE + 30), "the Crack", font=small, anchor="lm",
           fill=(220, 190, 255), stroke_width=5, stroke_fill=INK)
    big.convert("RGB").save(out / "world_map_v2_labelled_2x.png", optimize=True)
    big.resize((1920, int(1920 * H / W)), Image.LANCZOS).convert("RGB").save(out / "world_map_v2_overview.png")

    data = {
        "size": [W, H], "scale": SCALE,
        "stages": [{"stage": n, "name": STAGES[n][0], "city": STAGES[n][1],
                    "land": LANDS[(n - 1) // 4] if n <= 24 else "heart",
                    "x": round(nodes[n][0], 1), "y": round(nodes[n][1], 1)} for n in sorted(nodes)],
        "assault": {"name": "Nhal Vorath, the Crownless Citadel", "x": av[0], "y": av[1],
                    "route": [[round(x, 1), round(y, 1)] for x, y in assault]},
    }
    (out / "world_map_v2_nodes.json").write_text(json.dumps(data, indent=1))
    log(f"wrote {out}")


if __name__ == "__main__":
    main()
