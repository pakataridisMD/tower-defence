"""The campaign world map of Orrhen, version 3: the whole world, each kingdom its own continent.

The game's campaign screen (scripts/ui/campaign_screen.gd) shows it. Needs numpy, Pillow, scipy and
scikit-image. Takes a few minutes.

The world ocean floats in the Outer Hollow (the starfield beyond the edge of the world). Six continents,
one per kingdom, lie around the Heartland of Orrun, where Solenne stands on the ruins of Vael; each is
joined to the middle by a land bridge or a great stone bridge. The map is 6000x3400 art pixels, shown
at 2x with nearest filtering. It is grown in this order:

1. Continents: warped, rotated outlines with bays, peninsulas and archipelagos; bent mountain spines
   across each; land shapes per kingdom (a caldera volcano, a high steppe, wet lowland forest, a frozen
   inland sea, terraced canyons, chasms into the void, a broad plateau in the middle).
2. Water: depressions flooded into lakes (priority flood), rivers from flow accumulation.
3. Biomes per kingdom by height (beach, lowland, rock, snow), hill-shaded from the upper left,
   blended where land bridges meet, posterised to one palette with ordered dithering.
4. Detail: roads by least-cost paths through passes and over bridges, villages with farmland and
   lanes, watchtowers, ships, lighthouses, forests, peaks, ground tufts and flowers, towns and capitals.

Usage:
    python3 tools/art/worldmap/gen_world_map.py [--game assets/art/worldmap] [--out PREVIEW_DIR] [--seed 7]

--game writes what the game uses: world_map.png (the painted map without labels or stage markers),
one medallion per stage, the land names as pixel lettering and world_map.json (where every stage, city,
road and label sits, in map pixels). --out also writes the design previews: the labelled map, an
overview and a close-up of each land.
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
from skimage.graph import MCP_Geometric, route_through_array

sys.path.insert(0, str(Path(__file__).resolve().parent))
import map_v1 as v1  # noqa: E402  (sprite kit and lettering from the first pass)
from map_v1 import (ACCENT, INK, LAND_NAME, LANDS, STAGES, Spr, hexc, house, landmark,  # noqa: E402
                    pixel_text, ramp, shaded_block, _darken, _lighten)

F = 2.0                 # detail scale relative to v2 (pixel-sized textures are multiplied by this)
W, H = 6000, 3400
SCALE = 2
CX, CY = 3000.0, 1730.0          # the middle of the world: Solenne, on the ruins of Vael
WRX, WRY = 2880.0, 1620.0        # the world ocean; beyond it is the Outer Hollow
ROOT = Path(__file__).resolve().parents[3]
# Each kingdom is a continent: (angle from the middle, distance as a fraction of the world ocean,
# radii in px, rotation in degrees, mountain ranges). Ring order is kept so opposites face each other.
CONT = {
    "fire":   (-95, 0.68, (600, 400), 10, 2),
    "storm":  (-22, 0.70, (680, 470), -20, 1),
    "nature": (40, 0.67, (600, 420), 25, 1),
    "water":  (98, 0.67, (620, 380), -8, 2),
    "earth":  (155, 0.70, (660, 450), 18, 3),
    "void":   (215, 0.66, (520, 380), -30, 2),
}
HEART_R = (560.0, 380.0)
# How each continent reaches the Heartland: a land bridge or a great stone bridge over a strait.
LINK = {"fire": "isthmus", "storm": "bridge", "nature": "isthmus", "water": "bridge", "earth": "isthmus",
        "void": "bridge"}
RING_R = (360.0, 250.0)          # the Heartland ring road around Solenne
CITADEL = (470.0, 770.0)         # bottom-centre of Nhal Vorath in the Outer Hollow
DS = 4  # the water simulation and road search run on a grid 4x coarser than the map

BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
BAYER = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W].astype(np.float32)
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
RN = np.sqrt(((XX - CX) / WRX) ** 2 + ((YY - CY) / WRY) ** 2)     # 1.0 at the edge of the world ocean


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


def gauss_at(x, y, sx, sy):
    return np.exp(-(((XX - x) / sx) ** 2 + ((YY - y) / sy) ** 2))


# --------------------------------------------------------------------------- layout

def cont_centre(land: str) -> tuple[float, float]:
    ang, dist = CONT[land][0], CONT[land][1]
    a = math.radians(ang)
    return CX + dist * WRX * math.cos(a), CY + dist * WRY * math.sin(a)


def radius_towards(radii, rot, dx, dy) -> float:
    """Radius of a rotated ellipse in the direction (dx, dy)."""
    a = math.atan2(dy, dx) - math.radians(rot)
    return 1.0 / math.sqrt((math.cos(a) / radii[0]) ** 2 + (math.sin(a) / radii[1]) ** 2)


def link_ends(land: str):
    """The continent's end and the Heartland's end of its link to the middle."""
    cx, cy = cont_centre(land)
    dx, dy = CX - cx, CY - cy
    ln = math.hypot(dx, dy)
    ux, uy = dx / ln, dy / ln
    r = radius_towards(CONT[land][2], CONT[land][3], ux, uy)
    rh = radius_towards(HEART_R, 0, -ux, -uy)
    return (cx + ux * r * 0.78, cy + uy * r * 0.78), (CX - ux * rh * 0.8, CY - uy * rh * 0.8)


def ring_point(angle: float) -> tuple[float, float]:
    a = math.radians(angle)
    return CX + RING_R[0] * math.cos(a), CY + RING_R[1] * math.sin(a)


def stage_layout() -> dict[int, tuple[float, float]]:
    """Each land's road runs from its far coast (stage 1) to its capital (stage 4) beside the link."""
    out: dict[int, tuple[float, float]] = {}
    ts = [0.0, 0.36, 0.7, 1.0]
    zig = [0.32, -0.3, 0.28, 0.0]
    for li, land in enumerate(LANDS):
        cx, cy = cont_centre(land)
        dx, dy = CX - cx, CY - cy
        ln = math.hypot(dx, dy)
        ux, uy = dx / ln, dy / ln
        px, py = -uy, ux
        radii, rot = CONT[land][2], CONT[land][3]
        r_al = radius_towards(radii, rot, ux, uy)
        r_pp = radius_towards(radii, rot, px, py)
        far = (cx - ux * r_al * 0.6, cy - uy * r_al * 0.6)
        near = (cx + ux * r_al * 0.5, cy + uy * r_al * 0.5)
        for k in range(4):
            t = ts[k]
            out[li * 4 + k + 1] = (far[0] + (near[0] - far[0]) * t + px * r_pp * zig[k],
                                   far[1] + (near[1] - far[1]) * t + py * r_pp * zig[k])
    out[25] = ring_point(156)        # Crossmere, where the roads from the six lands meet the ring road
    out[26] = (CX - 150, CY + 120)
    out[27] = (CX, CY + 10)
    return out


# --------------------------------------------------------------------------- geology

def line_distance(polylines, width_px=3) -> np.ndarray:
    """Distance in map pixels to the nearest of some polylines (computed on the coarse grid)."""
    h, w = H // DS, W // DS
    img = Image.new("L", (w, h), 0)
    d = ImageDraw.Draw(img)
    for pts in polylines:
        d.line([(x / DS, y / DS) for x, y in pts], fill=1, width=1)
    m = np.asarray(img) > 0
    dist = ndimage.distance_transform_edt(~m) * DS
    return np.asarray(Image.fromarray(dist.astype(np.float32), mode="F").resize((W, H), Image.BILINEAR))


def continent_fields(seed: int):
    """Normalised distance to each continent's warped outline (1.0 on the coast), and soft weights."""
    log("continents")
    shapes = {}
    mh, mw = H + 800, W + 1200            # larger noise canvases, sliced at an offset per continent
    warp_big = fbm(seed + 1, 8.5, 5, h=mh, w=mw)
    warp_mid = fbm(seed + 12, 22, 5, h=mh, w=mw)
    warp_fine = fbm(seed + 42, 72, 4, h=mh, w=mw)
    for i, land in enumerate(LANDS + ["heart"]):
        if land == "heart":
            (cx, cy), radii, rot = (CX, CY), HEART_R, 0.0
        else:
            cx, cy = cont_centre(land)
            radii, rot = CONT[land][2], CONT[land][3]
        a = math.radians(rot)
        u = (XX - cx) * math.cos(a) + (YY - cy) * math.sin(a)
        v = -(XX - cx) * math.sin(a) + (YY - cy) * math.cos(a)
        cn = np.sqrt((u / radii[0]) ** 2 + (v / radii[1]) ** 2)
        # each continent gets its own warp by sampling the shared noise at an offset
        ox, oy = (i * 977) % 1200, (i * 613) % 800
        wb = warp_big[oy:oy + H, ox:ox + W]
        wm = warp_mid[(oy * 3) % 800:(oy * 3) % 800 + H, (ox * 3) % 1200:(ox * 3) % 1200 + W]
        wf = warp_fine[oy:oy + H, ox:ox + W]
        cn = cn + (wb - 0.5) * (0.95 if land != "heart" else 0.45) + (wm - 0.5) * 0.4 + (wf - 0.5) * 0.1
        shapes[land] = cn.astype(np.float32)
    raw = {k: np.exp(-2.6 * np.clip(v, 0, None) ** 2) for k, v in shapes.items()}
    total = sum(raw.values()) + 1e-6
    heart = (raw["heart"] / total).astype(np.float32)
    lsum = sum(raw[k] for k in LANDS) + 1e-6
    weights = [(raw[k] / lsum).astype(np.float32) for k in LANDS]
    return shapes, weights, heart


def elevation(seed: int, shapes, weights, heart_w, nodes, rng):
    log("elevation")
    cont = fbm(seed + 3, 9, 7)
    elev = np.full((H, W), -1.0, np.float32)
    inland = {}
    for land, cn in shapes.items():
        e = np.minimum((1.0 - cn) * 0.7, 0.16 + (1.0 - cn) * 0.14)   # steep coasts, low interiors
        elev = np.maximum(elev, e)
        inland[land] = smoothstep(0.02, 0.14, e)
    elev += (cont - 0.5) * 0.1 + (fbm(seed + 4, 30, 5) - 0.5) * 0.05 + (fbm(seed + 41, 120, 3) - 0.5) * 0.015
    # archipelagos in the open sea
    isl = fbm(seed + 43, 40, 5)
    elev = np.maximum(elev, (isl - 0.8) * 1.4 - 0.03 * (RN > 0.97))

    # land bridges from four continents to the Heartland; the others get a great stone bridge
    log("land bridges")
    bridges = []
    isth_lines = []
    for land in LANDS:
        p, q = link_ends(land)
        if LINK[land] == "isthmus":
            mid = ((p[0] + q[0]) / 2 + rng.uniform(-60, 60), (p[1] + q[1]) / 2 + rng.uniform(-60, 60))
            isth_lines.append([p, mid, q])
        else:
            bridges.append((land, p, q))
    d_isth = line_distance(isth_lines)
    wn = fbm(seed + 44, 20, 4)
    width = 70 + (wn - 0.5) * 90
    bridge_land = smoothstep(1.0, 0.45, d_isth / width)
    elev = np.where(bridge_land > 0, np.maximum(elev, (0.1 + (cont - 0.5) * 0.08) * bridge_land - 0.02 * (1 - bridge_land)), elev)

    # mountain ranges: bent spines across each continent
    log("mountain ranges")
    rid = ridged(seed + 20, 14, 7)
    rid_fine = ridged(seed + 21, 52, 4)
    spines = []
    for land in LANDS:
        cx, cy = cont_centre(land)
        radii, rot, n = CONT[land][2], CONT[land][3], CONT[land][4]
        for _ in range(n):
            phi = math.radians(rng.uniform(0, 180))
            off = rng.uniform(-0.35, 0.35)
            pts = []
            bend = rng.uniform(-0.35, 0.35)
            for t in np.linspace(-0.85, 0.85, 9):
                o = off + bend * (1 - t * t) + rng.uniform(-0.08, 0.08)
                ax = math.cos(phi) * t * radii[0] - math.sin(phi) * o * radii[1]
                ay = math.sin(phi) * t * radii[1] * 0.9 + math.cos(phi) * o * radii[1]
                pts.append((cx + ax, cy + ay))
            spines.append(pts)
    d_sp = line_distance(spines)
    rw = 80 + (fbm(seed + 22, 16, 4) - 0.5) * 130
    landmask = sum(inland[k] for k in LANDS)
    massif = smoothstep(0.25, 0.6, fbm(seed + 25, 30, 4))      # break the band into massifs and passes
    range_mask = np.exp(-(d_sp / np.maximum(rw, 20)) ** 2) * np.clip(landmask, 0, 1) * (0.35 + 0.65 * massif)
    elev += range_mask * (0.12 + 0.55 * rid + 0.12 * rid_fine)
    # foothill country away from the spines
    hills = ridged(seed + 23, 24, 6) * smoothstep(0.62, 0.8, fbm(seed + 24, 8, 3))
    elev += hills * 0.2 * np.clip(landmask, 0, 1)

    w = dict(zip(LANDS, weights))
    hw = heart_w
    # Ember Reach: the Pyrrhenhall caldera volcano under stage 4, open ash plains elsewhere
    vx, vy = nodes[4]
    vol_r = np.sqrt((XX - vx) ** 2 + ((YY - vy) * 1.25) ** 2)
    cone = np.clip(1 - vol_r / 340, 0, 1) ** 1.6 * 0.55
    crater = np.clip(1 - vol_r / 104, 0, 1) ** 0.6 * 0.42
    elev += (cone - crater) * smoothstep(0.2, 0.6, w["fire"]) * (1 - hw)
    elev -= 0.06 * w["fire"] * inland["fire"] * (range_mask < 0.4)
    # Thunder Steppe: a high flat plain
    flat = w["storm"] * inland["storm"] * (range_mask < 0.3)
    elev = elev + (0.2 + (elev - 0.2) * 0.45 - elev) * flat
    # Verdant Deep: low and wet
    elev -= 0.05 * w["nature"] * inland["nature"]
    # Frostmere: the frozen inland sea, on the far side from the Heartland
    cx, cy = cont_centre("water")
    elev -= np.exp(-(((XX - (cx + 40)) / 260) ** 2 + ((YY - (cy + 40)) / 130) ** 2)) * 0.55 * inland["water"]
    # Sunscar: table-land cut into terraces
    terr = np.floor((elev + 0.06) * 14) / 14
    elev = elev + (0.06 + (terr - elev) * 0.85) * w["earth"] * inland["earth"]
    # The Heartland: a broad, gentle plateau
    h_in = smoothstep(0.3, 0.6, hw) * inland["heart"]
    elev = elev * (1 - h_in) + (0.28 + (1 - shapes["heart"]) * 0.1 + (cont - 0.5) * 0.04) * h_in
    heart = smoothstep(0.35, 0.6, hw).astype(np.float32)
    return elev.astype(np.float32), heart, bridges, range_mask


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
    thresh = 260.0 * F * 1.25
    img = Image.new("L", (W, H), 0)
    d = ImageDraw.Draw(img)
    ys, xs = np.nonzero((acc > thresh) & ~sea & ~lake)
    for y, x in zip(ys, xs):
        ty, tx = tgt[y, x]
        if ty == y and tx == x:
            continue
        a = acc[y, x]
        width = int(np.clip(1 + math.log2(a / thresh) * 1.0, 1, 8))
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
    tex = fbm(seed + 9, 70 * F, 3)
    patch = fbm(seed + 14, 9 * F, 5)
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
    depth = np.clip(-elev / 0.9, 0, 0.75)
    waves = fbm(seed + 5, 90 * F, 2)
    ocean = tone(np.clip(0.72 - depth * 0.7 + (waves - 0.5) * 0.14, 0, 1), ramp("1a4868", 6, 0.42))
    glint = (waves > 0.74) & (np.roll(waves, 1, 1) <= 0.74) & (BAYER > 0.55)
    glint = glint | np.roll(glint, 1, 1)
    ocean[glint] = hexc("5a94b8")
    wf = weights[LANDS.index("water")]
    near_land = ndimage.gaussian_filter((~water).astype(np.float32), 25 * F)
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
    """Beyond the world ocean: the Outer Hollow, a starfield behind a rim where the sea pours away."""
    log("outer hollow")
    edge = RN + (fbm(seed + 6, 14, 6) - 0.5) * 0.05 + (fbm(seed + 7, 4, 3) - 0.5) * 0.04
    hol = edge > 1.0
    neb = fbm(seed + 8, 8, 6)
    neb2 = fbm(seed + 45, 5, 5)
    sky = tone(np.clip(neb * 0.75 - 0.1 + np.clip(1.25 - edge, 0, 0.3), 0, 1), ramp("1b1030", 6, 0.3, 0.01), 0.9)
    teal = tone(np.clip(neb2 * 0.8 - 0.2, 0, 1), ramp("10303a", 5, 0.25, 0.01), 0.9)
    sky = np.where((neb2 > 0.62)[..., None], teal, sky)
    rgb[hol] = sky[hol]
    # the rim: falling water, white foam streaks over teal, then a violet glow into the dark
    fall = (edge > 1.0) & (edge < 1.008)
    streak = (np.sin(np.arctan2(YY - CY, XX - CX) * 900) > 0.2)
    rgb[fall] = np.where(streak[fall, None], np.array(hexc("dff2f6")), np.array(hexc("4a9ab0")))
    rim = (edge >= 1.008) & (edge < 1.02)
    rgb[rim] = rgb[rim] * 0.5 + np.array(hexc("6a3aa8")) * 0.5
    lip = (edge > 0.994) & (edge <= 1.0)
    rgb[lip] = hexc("9fd8e6")
    rng = np.random.default_rng(seed + 9)
    r = rng.random((H, W))
    rgb[hol & (r > 0.9955)] = hexc("e8d8ff")
    big = hol & (r > 0.99975)
    rgb[ndimage.binary_dilation(big) & hol] = hexc("b8a0e8")
    rgb[big] = (255, 255, 255)
    return hol | fall


def sky_bodies(img: Image.Image) -> None:
    """A pale moon and a ringed far world in the corners of the Outer Hollow."""
    s = Spr(140, 140)
    s.ell(0, 0, 139, 139, "8a8aa8")
    s.ell(4, 2, 125, 123, "c8c8dc")
    s.ell(10, 6, 80, 70, "e8e8f4")
    for x, y, r in ((40, 60, 12), (85, 40, 8), (70, 95, 16), (100, 80, 6), (30, 30, 6)):
        s.ell(x - r, y - r, x + r, y + r, "a8a8c0")
        s.ell(x - r + 2, y - r + 2, x + r, y + r, "9898b4")
    moon = s.done((40, 36, 60))
    img.alpha_composite(moon, (W - 260, 60))
    p = Spr(220, 120)
    p.ell(50, 10, 169, 109, "4a7a8a")
    p.ell(56, 14, 140, 90, "6aa0b0")
    p.ell(64, 20, 110, 60, "9ac8d0")
    p.d.ellipse([0, 48, 219, 74], outline=hexc("d8c8a0") + (255,), width=4)
    p.d.ellipse([6, 52, 213, 70], outline=hexc("8a7a60") + (255,), width=2)
    img.alpha_composite(p.done((20, 30, 40)), (40, H - 220))


def void_chasms(rgb, seed, weights, heart, water, elev):
    """Holes in the Hollow Rift that drop into the starry dark, with a lit far rim and a dark near wall."""
    n = fbm(seed + 30, 18 * F, 5)
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
        k = 3
        lw, lh = 46 * k, 40 * k
        w, h = lw + 90, lh + 60
        s = Spr(w, h)
        ls = KSpr(46, 40, k)
        landmark(ls, land, 46, 40)
        lim = ls.done()
        n_house, rad = 55, (w / 2 - 6, h / 2 - 6)
    else:
        w, h = 88, 62
        s = Spr(w, h)
        lim = None
        n_house, rad = 24 + int(rng.integers(0, 7)), (w / 2 - 6, h / 2 - 8)
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


def crossmere_sprite(rng, k: int = 1) -> Image.Image:
    """The crossroads market town: tents, carts and a square where every road met."""
    w, h = 80, 56
    s = KSpr(w, h, k) if k > 1 else Spr(w, h)
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


# --------------------------------------------------------------------------- settlements and details

def village_sprite(land: str, rng) -> Image.Image:
    w, h = 46, 32
    s = Spr(w, h)
    n = int(rng.integers(3, 8)) if land not in ("fire", "void") else int(rng.integers(2, 5))
    spots = []
    for _ in range(200):
        x, y = rng.uniform(1, w - 10), rng.uniform(5, h - 11)
        if all(abs(x - a) > 9 or abs(y - b) > 9 for a, b in spots):
            spots.append((x, y))
        if len(spots) >= n:
            break
    for x, y in sorted(spots, key=lambda p: p[1]):
        house(s, int(x), int(y), land, w=8 if land == "storm" else 7)
    if land in ("storm", "nature", "earth") and rng.random() < 0.4:      # a windmill or a well
        x = int(rng.uniform(4, w - 8))
        s.rect(x, 2, x + 3, 10, "d8d0c0")
        s.rect(x + 3, 2, x + 3, 10, "a89c88")
        s.line([(x - 3, 0), (x + 6, 7)], "6a4a2a")
        s.line([(x + 6, 0), (x - 3, 7)], "6a4a2a")
    return s.done()


FIELD_COLOURS = {
    "storm": [("d8b850", "b8983a"), ("8ab048", "6a9038"), ("a07a48", "7a5a32"), ("c8c060", "a8a048")],
    "nature": [("7aa848", "5a8838"), ("b8a850", "988a3a"), ("6a8a3a", "4e6e2c")],
    "earth": [("d89a58", "b87a40"), ("c8b060", "a89048"), ("a86a3a", "88502a")],
    "water": [("c8d8c0", "a8bca0")],
}


def draw_fields(d: ImageDraw.ImageDraw, x0, y0, land, rng, ok) -> list[tuple[int, int, int, int]]:
    """A patchwork of striped fields with hedges around a village."""
    rects = []
    cols = FIELD_COLOURS.get(land)
    if not cols:
        return rects
    for _ in range(int(rng.integers(20, 40))):
        fx = x0 + rng.uniform(-110, 110)
        fy = y0 + rng.uniform(-70, 80)
        fw, fh = int(rng.integers(12, 30)), int(rng.integers(8, 18))
        box = (int(fx), int(fy), int(fx) + fw, int(fy) + fh)
        if not ok(box) or any(not (b[2] < box[0] - 1 or b[0] > box[2] + 1 or b[3] < box[1] - 1 or b[1] > box[3] + 1)
                              for b in rects):
            continue
        c1, c2 = cols[int(rng.integers(0, len(cols)))]
        d.rectangle(box, fill=hexc(c1) + (255,))
        vertical = rng.random() < 0.4
        if vertical:
            for x in range(box[0] + 1, box[2], 3):
                d.line([(x, box[1]), (x, box[3])], fill=hexc(c2) + (255,))
        else:
            for y in range(box[1] + 1, box[3], 3):
                d.line([(box[0], y), (box[2], y)], fill=hexc(c2) + (255,))
        d.rectangle(box, outline=hexc("3a5a22" if land != "earth" else "6a3a20") + (255,))
        d.line([(box[0], box[3] + 1), (box[2], box[3] + 1)], fill=(20, 24, 12, 255))
        rects.append(box)
    return rects


def tower_sprite(land: str) -> Image.Image:
    s = Spr(11, 22)
    s.rect(2, 6, 8, 21, "8a8494")
    s.rect(2, 6, 3, 21, "b8b2c4")
    s.rect(7, 6, 8, 21, "5a5466")
    for x in (2, 5, 8):
        s.rect(x, 4, x, 5, "8a8494")
    s.rect(5, 10, 5, 12, "201828")
    s.px(5, 11, "ffd070")
    s.line([(5, 4), (5, 0)], "4a3a2a")
    s.rect(6, 0, 9, 2, ACCENT[land])
    return s.done()


def ship_sprite(rng, sail: str) -> Image.Image:
    s = Spr(18, 14)
    s.poly([(0, 9), (17, 9), (14, 13), (3, 13)], "6a4a2a")
    s.rect(0, 9, 17, 9, "8a6a3a")
    s.line([(8, 1), (8, 9)], "4a3420")
    s.poly([(9, 1), (15, 4), (9, 8)], sail)
    s.poly([(7, 2), (2, 7), (7, 7)], _darken(sail, 0.85))
    im = s.done()
    if rng.random() < 0.5:
        im = im.transpose(Image.FLIP_LEFT_RIGHT)
    return im


def lighthouse_sprite() -> Image.Image:
    s = Spr(12, 30)
    s.poly([(2, 29), (4, 6), (8, 6), (10, 29)], "f4f0e8")
    s.poly([(7, 6), (8, 6), (10, 29), (8, 29)], "b8b0a8")
    for y in (10, 18, 25):
        s.poly([(2 + (29 - y) * 0.08, y), (10 - (29 - y) * 0.08, y), (10 - (29 - y - 2) * 0.08, y + 2),
                (2 + (29 - y - 2) * 0.08, y + 2)], "c0402a")
    s.rect(3, 2, 8, 5, "3a3448")
    s.rect(4, 3, 7, 4, "fff0a0")
    s.poly([(3, 2), (5, 0), (8, 2)], "c0402a")
    return s.done()


def draw_bridge(d: ImageDraw.ImageDraw, p, q):
    """A great stone bridge on arches over a strait."""
    x0, y0 = p
    x1, y1 = q
    ln = math.hypot(x1 - x0, y1 - y0)
    ux, uy = (x1 - x0) / ln, (y1 - y0) / ln
    nx, ny = -uy, ux
    if ny < 0:
        nx, ny = -nx, -ny                     # the side facing the viewer (down the screen)
    d.line([(x0 + nx * 9, y0 + ny * 9), (x1 + nx * 9, y1 + ny * 9)], fill=(10, 20, 30, 140), width=12)
    for t in np.arange(0, ln, 26):
        cx, cy = x0 + ux * t, y0 + uy * t
        d.polygon([(cx + nx * 6 - ux * 4, cy + ny * 6 - uy * 4), (cx + nx * 6 + ux * 4, cy + ny * 6 + uy * 4),
                   (cx + nx * 14 + ux * 4, cy + ny * 14 + uy * 4), (cx + nx * 14 - ux * 4, cy + ny * 14 - uy * 4)],
                  fill=hexc("5a5466") + (255,))
    d.line([(x0, y0), (x1, y1)], fill=hexc("2a2632") + (255,), width=16)
    d.line([(x0, y0), (x1, y1)], fill=hexc("9a94a8") + (255,), width=12)
    d.line([(x0 - nx * 5, y0 - ny * 5), (x1 - nx * 5, y1 - ny * 5)], fill=hexc("c8c2d4") + (255,), width=2)
    d.line([(x0 + nx * 5, y0 + ny * 5), (x1 + nx * 5, y1 + ny * 5)], fill=hexc("6a6478") + (255,), width=2)
    d.line([(x0, y0), (x1, y1)], fill=hexc("d8c49a") + (255,), width=4)
    for t in np.arange(13, ln, 26):           # lamp posts
        cx, cy = x0 + ux * t - nx * 6, y0 + uy * t - ny * 6
        d.rectangle([cx - 1, cy - 4, cx, cy], fill=hexc("3a3448") + (255,))
        d.point((cx, cy - 5), fill=hexc("fff0a0") + (255,))


def ground_details(rgb, land_idx, heart, ok, rng):
    """Grass tufts, flowers, pebbles, cinders and ice glints, one or two pixels each."""
    r = rng.random((H, W))
    spots = ok & (r < 0.012)
    ys, xs = np.nonzero(spots)
    li = land_idx[ys, xs]
    hrt = heart[ys, xs] > 0.5
    tuft = {0: "6a5048", 1: "b8c860", 2: "5aa040", 3: "f4fbff", 4: "e8b878", 5: "8a6ac8"}
    flower = {0: "ff8a2a", 1: "f8e070", 2: "f088b0", 3: "bfe0ff", 4: "f8f0c8", 5: "e2c8ff"}
    pick = rng.random(len(xs))
    for k in range(6):
        sel = (li == k) & ~hrt
        a = sel & (pick < 0.7)
        rgb[ys[a], xs[a]] = hexc(tuft[k])
        up = np.clip(ys[a] - 1, 0, H - 1)
        rgb[up, xs[a]] = hexc(tuft[k])
        b = sel & (pick >= 0.7)
        rgb[ys[b], xs[b]] = hexc(flower[k])
    hs = hrt & (pick < 0.5)
    rgb[ys[hs], xs[hs]] = hexc("ffffff")


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


# --------------------------------------------------------------------------- labels

CITY_SIDE = {27: "right", 25: "left", 23: "left", 24: "right"}
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"


def label_view(img: Image.Image, scale: float, ox: float, oy: float, nodes, av, size: int) -> Image.Image:
    """Draw land, city and place names onto a view of the map (scale = view px per art px, origin ox, oy)."""
    out = img.copy()
    unit = max(3, int(round(6 * scale)))
    for land in LANDS:
        cx, cy = cont_centre(land)
        b = CONT[land][2][1]
        ly = cy + b + 120 if land == "water" else cy - b - 90
        ac = ACCENT[land]
        txt = pixel_text(LAND_NAME[land], ["ffffff", _lighten(ac), ac, _darken(ac, 0.8), _darken(ac, 0.6)], unit=unit)
        x, y = (cx - ox) * scale - txt.width / 2, (ly - oy) * scale - txt.height / 2
        out.alpha_composite(txt, (int(x), int(y)))
    t = pixel_text("THE HEARTLAND OF ORRUN", ["ffffff", "f4f0ff", "d8d0f0", "b8b0d8", "9890c0"], unit=max(2, unit - 1))
    out.alpha_composite(t, (int((CX - ox) * scale - t.width / 2), int((CY - HEART_R[1] - 70 - oy) * scale)))
    t3 = pixel_text("NHAL VORATH", ["f0d8ff", "d0a8ff", "b27cff", "8a4ad8", "6a2ab0"], unit=unit)
    out.alpha_composite(t3, (int((CITADEL[0] - ox) * scale - t3.width / 2), int((CITADEL[1] + 20 - oy) * scale)))
    if ox == 0 and oy == 0:
        title = pixel_text("ORRHEN", ["fff6d0", "ffe08a", "f2c14e", "d89a32", "a86a22"], unit=unit * 2)
        tx = int(W * scale - title.width - 420 * scale)
        out.alpha_composite(title, (tx, int(60 * scale)))
        sub = pixel_text("THE WAR OF SEVEN CROWNS", ["fff6d0", "efd58e", "c9a35a", "9a6e38", "6b4a28"],
                         unit=max(2, unit // 2 + 1))
        out.alpha_composite(sub, (tx + title.width // 2 - sub.width // 2, int(60 * scale) + title.height + 6))
    d = ImageDraw.Draw(out)
    font = ImageFont.truetype(SERIF, size)
    sw = max(2, size // 7)
    for n, (x, y) in nodes.items():
        my = y + (12 if n != 27 else 118)
        side = CITY_SIDE.get(n)
        name = STAGES[n][1] if n != 27 else "Solenne, the Crowned Heart"
        if side == "left":
            pos_, anchor = ((x - 34 - ox) * scale, (my - oy) * scale), "rm"
        elif side == "right":
            pos_, anchor = ((x + 34 - ox) * scale, (my - oy) * scale), "lm"
        else:
            pos_, anchor = ((x - ox) * scale, (my + 26 - oy) * scale), "mt"
        d.text(pos_, name, font=font, anchor=anchor, fill=(255, 242, 184) if n > 24 else (255, 246, 224),
               stroke_width=sw, stroke_fill=INK)
    d.text(((av[0] - ox) * scale, (CITADEL[1] + 80 - oy) * scale), "The final assault", font=font, anchor="mt",
           fill=(240, 216, 255), stroke_width=sw, stroke_fill=INK)
    return out


# --------------------------------------------------------------------------- game export

# Stage numbers on the map and the game's stage ids: four per land in ring order, then the Convergence.
STAGE_PREFIX = {"fire": "ember", "storm": "storm", "nature": "nature", "water": "water", "earth": "earth",
                "void": "void"}


def stage_id(n: int) -> str:
    if n > 24:
        return f"converge_{n - 24}"
    return f"{STAGE_PREFIX[LANDS[(n - 1) // 4]]}_{(n - 1) % 4 + 1}"


def resample(pts, step: float = 14.0) -> list[list[float]]:
    """A road from the coarse search grid, smoothed and evened out to a point every `step` px."""
    pts = smooth_path(pts, 4)
    if len(pts) < 2:
        return [[round(float(x), 1), round(float(y), 1)] for x, y in pts]
    seg = np.sqrt(((pts[1:] - pts[:-1]) ** 2).sum(1))
    dist = np.concatenate([[0.0], np.cumsum(seg)])
    marks = np.linspace(0, dist[-1], max(2, int(dist[-1] / step) + 1))
    xs = np.interp(marks, dist, pts[:, 0])
    ys = np.interp(marks, dist, pts[:, 1])
    return [[round(float(x), 1), round(float(y), 1)] for x, y in zip(xs, ys)]


def medal_spot(n: int, nodes) -> tuple[float, float]:
    x, y = nodes[n]
    return x, y + (118 if n == 27 else 12)


def export_game(game: Path, clean: Image.Image, nodes, av, trails, links, assault, city_tops) -> None:
    """What the campaign screen draws: the map, the stage medallions, the land names and where it all is."""
    log("game export")
    game.mkdir(parents=True, exist_ok=True)
    clean.convert("RGB").save(game / "world_map.png", optimize=True)
    stages = {}
    for n in sorted(nodes):
        land = LANDS[(n - 1) // 4] if n <= 24 else "heart"
        v1.medallion(str(n), ACCENT[land], big=n % 4 == 0 or n > 24).save(game / f"medal_{n:02d}.png")
        mx, my = medal_spot(n, nodes)
        entry = {"number": n, "city": STAGES[n][1], "land": land,
                 "medal": [round(mx, 1), round(my, 1)],
                 "city_top": [round(city_tops[n][0], 1), round(city_tops[n][1], 1)],
                 "label": CITY_SIDE.get(n, "below")}
        if n in trails:
            entry["trail"] = resample(trails[n])
        stages[stage_id(n)] = entry
    v1.letter_medallion([".#.", "#.#", "###", "#.#", "#.#"], "d07cff").save(game / "medal_assault.png")
    stages["assault_1"] = {"number": 28, "city": "Nhal Vorath", "land": "hollow",
                           "medal": [round(av[0], 1), round(av[1], 1)],
                           "city_top": [round(av[0], 1), round(av[1] - 40, 1)], "label": "below",
                           "trail": resample(assault, 18.0)}
    labels = {}
    for land in LANDS:
        cx, cy = cont_centre(land)
        b = CONT[land][2][1]
        ly = cy + b + 120 if land == "water" else cy - b - 90
        ac = ACCENT[land]
        txt = pixel_text(LAND_NAME[land], ["ffffff", _lighten(ac), ac, _darken(ac, 0.8), _darken(ac, 0.6)], unit=1)
        txt.save(game / f"label_{land}.png")
        labels[land] = {"file": f"label_{land}.png", "at": [round(cx, 1), round(ly, 1)]}
    txt = pixel_text("THE HEARTLAND OF ORRUN", ["ffffff", "f4f0ff", "d8d0f0", "b8b0d8", "9890c0"], unit=1)
    txt.save(game / "label_heart.png")
    labels["heart"] = {"file": "label_heart.png", "at": [CX, round(CY - HEART_R[1] - 50, 1)]}
    txt = pixel_text("NHAL VORATH", ["f0d8ff", "d0a8ff", "b27cff", "8a4ad8", "6a2ab0"], unit=1)
    txt.save(game / "label_hollow.png")
    labels["hollow"] = {"file": "label_hollow.png", "at": [CITADEL[0], CITADEL[1] + 50]}
    data = {
        "size": [W, H],
        "image": "world_map.png",
        "centre": [CX, CY],
        "stages": stages,
        "links": {STAGE_PREFIX[land] + "_4": resample(pts) for land, pts in links.items()},
        "lands": {land: {"centre": [round(v, 1) for v in cont_centre(land)], "accent": ACCENT[land]}
                  for land in LANDS},
        "labels": labels,
    }
    (game / "world_map.json").write_text(json.dumps(data, indent=1) + "\n")


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--game", default=str(ROOT / "assets" / "art" / "worldmap"),
                    help="where the game's map art goes; empty to skip")
    ap.add_argument("--out", default="", help="where the design previews go; empty to skip them")
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    out = Path(args.out) if args.out else None
    if out is not None:
        out.mkdir(parents=True, exist_ok=True)
    seed = args.seed
    rng = np.random.default_rng(seed)
    nodes = stage_layout()

    shapes, weights, heart_w = continent_fields(seed)
    elev, heart, bridges, range_mask = elevation(seed, shapes, weights, heart_w, nodes, rng)
    land_idx = np.argmax(np.stack(weights), 0).astype(np.int8)

    # keep every stage on dry land, away from the shore: move it to the nearest good spot
    dry = ndimage.binary_erosion(elev > 0.05, iterations=24) & (elev < 0.4)
    for n, (x, y) in list(nodes.items()):
        if dry[int(y), int(x)]:
            continue
        best = None
        for r in range(8, 600, 8):
            for a in range(0, 360, 8):
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
    hyd["lake"] &= np.hypot(hx * DS - vx, hy * DS - vy) > 180
    river = draw_rivers(hyd, elev, seed)
    shade = hillshade(elev)
    rgb, water, lava = paint(seed, elev, weights, heart, river, hyd, shade)
    hol = outer_hollow(rgb, seed, water)
    chasm = void_chasms(rgb, seed, weights, heart, water, elev)

    # the Crack: a glowing fissure from the heart of the Hollow Rift to the edge of the world
    log("the Crack")
    cvx, cvy = cont_centre("void")
    end = (CITADEL[0] + 110, CITADEL[1] + 20)
    crack_pts = [(cvx + (end[0] - cvx) * t, cvy + (end[1] - cvy) * t) for t in np.linspace(0, 1, 7)]
    jag = []
    for (x0, y0), (x1, y1) in zip(crack_pts, crack_pts[1:]):
        for k in range(14):
            t = k / 14
            jag.append((x0 + (x1 - x0) * t + rng.uniform(-14, 14), y0 + (y1 - y0) * t + rng.uniform(-14, 14)))
    jag.append(crack_pts[-1])
    cimg = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(cimg)
    cd.line(jag, fill=1, width=17)
    cd.line(jag, fill=2, width=8)
    cd.line(jag, fill=3, width=3)
    cm = np.asarray(cimg)
    halo = ndimage.binary_dilation(cm > 0, iterations=5)
    rgb[halo] = rgb[halo] * 0.4 + np.array(hexc("4a1a80")) * 0.6
    rgb[cm == 1] = hexc("7a3ad0")
    rgb[cm == 2] = hexc("c79bff")
    rgb[cm == 3] = hexc("f8f0ff")

    land_ok = ~water & ~hol & (river == 0) & ~chasm & ~lava & ~halo
    ground_details(rgb, land_idx, heart, land_ok & (elev < 0.5), rng)

    log("posterize")
    noisy = np.clip(rgb + (BAYER[..., None] - 0.5) * 18, 0, 255).astype(np.uint8)
    q = Image.fromarray(noisy).quantize(colors=220, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    base = q.convert("RGBA")
    del noisy, q

    # --- roads over the coarse grid: slopes, peaks and water cost more; bridges and land bridges are cheap
    log("roads")
    z = hyd["z"]
    gy, gx = np.gradient(z)
    slope = np.sqrt(gx ** 2 + gy ** 2)
    sub = (slice(DS // 2, None, DS), slice(DS // 2, None, DS))
    water_c, river_c, chasm_c = water[sub], river[sub] > 0, chasm[sub]
    cost = 1 + slope * 600 + np.clip(z - 0.42, 0, 1) * 60 + water_c * 3000 + river_c * 14 + chasm_c * 3000
    bimg = Image.new("L", (cost.shape[1], cost.shape[0]), 0)
    bd = ImageDraw.Draw(bimg)
    for _, p, q2 in bridges:
        bd.line([(p[0] / DS, p[1] / DS), (q2[0] / DS, q2[1] / DS)], fill=1, width=3)
    cost = np.where(np.asarray(bimg) > 0, 1.0, cost)

    def route(a, b):
        ia = (min(cost.shape[0] - 1, int(a[1] / DS)), min(cost.shape[1] - 1, int(a[0] / DS)))
        ib = (min(cost.shape[0] - 1, int(b[1] / DS)), min(cost.shape[1] - 1, int(b[0] / DS)))
        idx, _ = route_through_array(cost, ia, ib, fully_connected=True, geometric=True)
        return [((x + 0.5) * DS, (y + 0.5) * DS) for y, x in idx]

    paths = []
    trails: dict[int, list] = {}     # the road into each stage from the one before it
    links: dict[str, list] = {}      # each land's road from its capital to the Heartland ring road
    for li, land in enumerate(LANDS):
        for k in range(3):
            trails[li * 4 + k + 2] = route(nodes[li * 4 + k + 1], nodes[li * 4 + k + 2])
            paths.append(("road", trails[li * 4 + k + 2]))
        _, qh = link_ends(land)
        ang = math.degrees(math.atan2((qh[1] - CY) / RING_R[1], (qh[0] - CX) / RING_R[0]))
        links[land] = route(nodes[li * 4 + 4], ring_point(ang))
        paths.append(("road", links[land]))
    ring = [ring_point(a) for a in range(0, 361, 3)]
    paths.append(("ring", ring))
    trails[26] = route(nodes[25], nodes[26])
    trails[27] = route(nodes[26], nodes[27])
    paths.append(("royal", trails[26] + trails[27]))

    # --- villages, farmland and the lanes that join them to the roads
    log("villages")
    road_c = np.zeros(cost.shape, bool)
    for _, pts in paths:
        for x, y in pts:
            road_c[min(cost.shape[0] - 1, int(y / DS)), min(cost.shape[1] - 1, int(x / DS))] = True
    occupied = np.zeros((H, W), bool)
    for n, (x, y) in nodes.items():
        r = 220 if n % 4 == 0 or n > 24 else 130
        if n == 27:
            r = 520
        occupied[max(0, int(y) - r):int(y) + r // 2, max(0, int(x) - r):int(x) + r] = True
    occupied |= halo | (cm > 0)
    villages = []
    for _ in range(40000):
        x, y = int(rng.integers(40, W - 40)), int(rng.integers(40, H - 40))
        if not land_ok[y, x] or occupied[y, x] or not (0.05 < elev[y, x] < 0.4):
            continue
        in_heart = heart[y, x] > 0.5
        if any((x - a) ** 2 + (y - b) ** 2 < (160 if in_heart else 230) ** 2 for a, b, _ in villages):
            continue
        # the Heartland is where every people now lives: its villages are of every style
        villages.append((x, y, LANDS[int(rng.integers(0, 6))] if in_heart else LANDS[land_idx[y, x]]))
        if len(villages) >= 190:
            break
    draw = ImageDraw.Draw(base)
    fields = np.zeros((H, W), bool)

    def field_ok(box):
        x0, y0, x1, y1 = box
        if x0 < 2 or y0 < 2 or x1 >= W - 2 or y1 >= H - 2:
            return False
        win = (slice(y0, y1 + 2), slice(x0, x1 + 1))
        return bool(land_ok[win].all() and not occupied[win].any() and (elev[win] < 0.38).all()
                    and not road_c[y0 // DS:y1 // DS + 1, x0 // DS:x1 // DS + 1].any())

    for x, y, land in villages:
        for bx in draw_fields(draw, x, y, land, rng, field_ok):
            fields[bx[1]:bx[3] + 2, bx[0]:bx[2] + 1] = True
    mcp = MCP_Geometric(cost)
    starts = list(zip(*np.nonzero(road_c)))
    mcp.find_costs(starts)
    lanes = []
    for x, y, land in villages:
        try:
            tb = mcp.traceback((y // DS, x // DS))
        except ValueError:
            continue
        if 2 < len(tb) < 160:
            lanes.append([((c + 0.5) * DS, (r + 0.5) * DS) for r, c in tb])

    # lanes, roads and great bridges, drawn into the ground
    for pts in lanes:
        p = [tuple(q2) for q2 in smooth_path(pts)]
        draw.line(p, fill=hexc("5a4632") + (255,), width=4, joint="curve")
        draw.line(p, fill=hexc("c8b088") + (255,), width=2, joint="curve")
    base = draw_roads(base, paths, river, water)
    draw = ImageDraw.Draw(base)
    for _, p, q2 in bridges:
        draw_bridge(draw, p, q2)

    # --- scenery
    log("scenery")
    board = Board()
    avoid = fields.copy()
    for n, (x, y) in nodes.items():
        r = 110 if n % 4 == 0 or n > 24 else 60
        if n == 27:
            r = 330
        avoid[max(0, int(y) - r):int(y) + r // 3, max(0, int(x) - r):int(x) + r] = True
    avoid |= halo | (cm > 0)
    for kind, pts in paths + [("lane", l) for l in lanes]:
        r = 7 if kind != "lane" else 4
        for x, y in pts[::2]:
            xi, yi = int(x), int(y)
            avoid[max(0, yi - r):yi + r, max(0, xi - r):xi + r] = True
    for _, p, q2 in bridges:
        for t in np.linspace(0, 1, 200):
            xi, yi = int(p[0] + (q2[0] - p[0]) * t), int(p[1] + (q2[1] - p[1]) * t)
            avoid[max(0, yi - 14):yi + 14, max(0, xi - 14):xi + 14] = True
    for x, y, _ in villages:
        avoid[y - 30:y + 6, x - 26:x + 26] = True
    blocked = water | avoid | (river > 0) | chasm | hol | lava

    hi = ndimage.maximum_filter(elev, size=19)
    peaks = (elev >= hi) & (elev > 0.45) & ~blocked
    ys, xs = np.nonzero(peaks)
    rock_by_land = {land: BIOME[land][2] for land in LANDS}
    peak_cache = {}

    def peak(land, size, snow):
        key = (land, size // 2, snow, int(rng.integers(0, 8)))
        if key not in peak_cache:
            peak_cache[key] = peak_sprite(np.random.default_rng(abs(hash(key)) % 2 ** 32), size,
                                          rock_by_land[land], snow, land)
        return peak_cache[key]

    for y, x in zip(ys, xs):
        if heart[y, x] > 0.5:
            continue
        land = LANDS[land_idx[y, x]]
        size = int(np.clip(14 + (elev[y, x] - 0.45) * 130, 14, 46))
        snow = elev[y, x] > (0.6 if land != "water" else 0.45) and land not in ("fire", "void")
        board.put(peak(land, size, snow), x, y + 4, 3)
    for gy0 in range(0, H - 12, 12):
        for gx0 in range(0, W - 14, 14):
            x, y = gx0 + int(rng.integers(0, 14)), gy0 + int(rng.integers(0, 12))
            if blocked[y, x] or elev[y, x] < 0.47 or heart[y, x] > 0.5 or rng.random() < 0.2:
                continue
            land = LANDS[land_idx[y, x]]
            size = int(np.clip(14 + (elev[y, x] - 0.47) * 110, 14, 30))
            snow = elev[y, x] > 0.66 and land in ("water", "storm", "earth", "nature")
            board.put(peak(land, size, snow), x, y + 3, 2)
    log(f"peaks placed ({len(board.items)})")

    tree_cache = {land: [tree_sprite(np.random.default_rng(i * 7 + j), land) for j in range(14)]
                  for i, land in enumerate(LANDS)}
    stones = [stones_sprite(np.random.default_rng(i)) for i in range(6)]
    steps = [step_sprite(np.random.default_rng(i)) for i in range(8)]
    crystals = [crystal_sprite(np.random.default_rng(i)) for i in range(12)]
    ruins = [ruin_sprite(np.random.default_rng(i)) for i in range(10)]
    forest_n = fbm(seed + 60, 20, 5)
    acc_full = np.asarray(Image.fromarray(np.log1p(hyd["acc"]).astype(np.float32), mode="F").resize((W, H)))
    hdist = np.sqrt(((XX - CX) / HEART_R[0]) ** 2 + ((YY - CY) / HEART_R[1]) ** 2)
    cell = 7
    for gy0 in range(0, H - cell, cell):
        for gx0 in range(0, W - cell, cell):
            x = gx0 + int(rng.integers(0, cell))
            y = gy0 + int(rng.integers(0, cell))
            if blocked[y, x] or elev[y, x] > 0.5:
                continue
            if heart[y, x] > 0.5:
                if hdist[y, x] < 0.75 and rng.random() < 0.05:
                    board.put(ruins[int(rng.integers(0, 10))], x, y, 1)
                elif rng.random() < 0.04:
                    board.put(crystals[int(rng.integers(0, 12))], x, y, 1)
                continue
            land = LANDS[land_idx[y, x]]
            wet = acc_full[y, x]
            f = forest_n[y, x]
            p = {"nature": 0.25 + f * 0.9, "storm": (wet > 4.6) * 0.35 + (f > 0.72) * 0.25,
                 "water": (f > 0.48) * 0.55, "earth": (f > 0.75) * 0.08 + (wet > 5) * 0.2, "fire": (f > 0.6) * 0.18,
                 "void": (f > 0.62) * 0.3}[land]
            if rng.random() < p:
                board.put(tree_cache[land][int(rng.integers(0, 14))], x, y, 2)
            elif land == "storm" and rng.random() < 0.0015:
                board.put(stones[int(rng.integers(0, 6))], x, y, 1)
            elif land == "void" and rng.random() < 0.01:
                board.put(steps[int(rng.integers(0, 8))], x, y - 8, 6)
    ys, xs = np.nonzero(chasm & (BAYER > 0.97))
    for i in rng.permutation(len(xs))[:700]:
        board.put(steps[int(rng.integers(0, 8))], xs[i], ys[i], 8)
    log(f"scenery placed ({len(board.items)})")

    # --- watchtowers on high road passes, ships at sea, lighthouses on headlands
    towers = []
    for kind, pts in paths:
        if kind != "road":
            continue
        for x, y in pts[::6]:
            xi, yi = int(x), int(y)
            if elev[yi, xi] > 0.4 and all((xi - a) ** 2 + (yi - b) ** 2 > 360 ** 2 for a, b in towers):
                towers.append((xi, yi))
                board.put(tower_sprite(LANDS[land_idx[yi, xi]]), xi + 12, yi + 2, 2)
    sea_open = water & ~hol & (elev < -0.03)
    land_c = ~water[sub]
    dist_land = ndimage.distance_transform_edt(~land_c) * DS
    ships = []
    ys, xs = np.nonzero(sea_open[sub] & (dist_land > 30) & (dist_land < 320))
    for i in rng.permutation(len(xs)):
        x, y = int(xs[i] * DS), int(ys[i] * DS)
        fw = weights[LANDS.index("water")][y, x]
        if fw > 0.6 or any((x - a) ** 2 + (y - b) ** 2 < 260 ** 2 for a, b in ships):
            continue
        ships.append((x, y))
        sail = ACCENT[LANDS[land_idx[y, x]]] if rng.random() < 0.5 else "f0ece0"
        board.put(ship_sprite(rng, sail), x, y, 0)
        if len(ships) >= 90:
            break
    coast = ~water & ndimage.binary_dilation(sea_open, iterations=3) & ~blocked
    ys, xs = np.nonzero(coast[::4, ::4])
    lights = []
    for i in rng.permutation(len(xs)):
        x, y = int(xs[i] * 4), int(ys[i] * 4)
        if any((x - a) ** 2 + (y - b) ** 2 < 520 ** 2 for a, b in lights):
            continue
        lights.append((x, y))
        board.put(lighthouse_sprite(), x, y, 2)
        if len(lights) >= 22:
            break
    for x, y, land in villages:
        board.put(village_sprite(land, rng), x, y + 4, 2)
    # refugee camps between Solenne's walls and the ring road
    for a in range(0, 360, 24):
        ax = CX + (RING_R[0] - 70) * math.cos(math.radians(a + 7))
        ay = CY + (RING_R[1] - 50) * math.sin(math.radians(a + 7)) + 20
        if not blocked[int(ay), int(ax)]:
            board.put(village_sprite("storm", rng), ax, ay, 2)
    log(f"towers {len(towers)}, ships {len(ships)}, lighthouses {len(lights)}, villages {len(villages)}")

    # --- towns, capitals, Solenne, Nhal Vorath
    log("cities")
    city_tops: dict[int, tuple[float, float]] = {}   # where smoke rises when a city falls
    for n, (x, y) in nodes.items():
        if n == 27:
            with scaled(3):
                im = v1.solenne_sprite()
            im = stonework(im, seed + 71, brick=(5, 3), skip_bright=250)
            board.put(im, x, y + 100, 4)
            city_tops[n] = (x, y + 100 - im.height * 0.7)
            continue
        if n == 26:
            with scaled(2):
                im = lumen_gate_sprite()
            board.put(im, x, y - 10, 3)
        elif n == 25:
            im = crossmere_sprite(rng, 2)
            board.put(im, x, y - 10, 2)
        else:
            land = LANDS[(n - 1) // 4]
            im = town_sprite(n, land, rng, n % 4 == 0)
            board.put(im, x, y - 10, 2)
        city_tops[n] = (x, y - 10 - im.height * 0.6)
    with scaled(4):
        nv = v1.nhal_vorath_sprite()
    nv = stonework(nv, seed + 70, brick=(10, 4), skip_bright=150)
    board.put(nv, *CITADEL, 0)
    av = (CITADEL[0], CITADEL[1] - nv.height + 4 * 58)

    img = board.bake(base)
    del board
    log("glow")
    img = glow_pass(img, lava | (cm > 1), "ff6a1a", 8, 0.35)
    img = glow_pass(img, cm > 0, "9a5aff", 14, 0.3)
    hs = np.zeros((H, W), bool)
    hs[int(CY) - 120:int(CY) - 100, int(CX) - 6:int(CX) + 6] = True
    img = glow_pass(img, hs, "fff2b8", 20, 0.25)
    lh = np.zeros((H, W), bool)
    for x, y in lights:
        lh[max(0, y - 28):y - 24, x - 2:x + 2] = True
    img = glow_pass(img, lh, "fff0a0", 10, 0.4)
    sky_bodies(img)
    pv, ph = link_ends("void")
    assault = [nodes[27], ph, pv, (cvx, cvy)] + [(x + 30, y + 20) for x, y in crack_pts[1:-1]] + [av]
    draw_assault(img, assault)

    def frame(im: Image.Image) -> Image.Image:
        a = np.asarray(im).copy()
        a[:8, :, :3] = a[-8:, :, :3] = a[:, :8, :3] = a[:, -8:, :3] = hexc("3b2a1a")
        a[3:5, 3:-3, :3] = a[-5:-3, 3:-3, :3] = hexc("c9a35a")
        a[3:-3, 3:5, :3] = a[3:-3, -5:-3, :3] = hexc("c9a35a")
        return Image.fromarray(a)

    clean = frame(img)
    if args.game:
        export_game(Path(args.game), clean, nodes, av, trails, links, assault, city_tops)
    if out is None:
        log("done")
        return
    clean.convert("RGB").save(out / "world_map_v3_clean.png")

    log("medallions")
    marked = img.copy()
    for n, (x, y) in nodes.items():
        land = LANDS[(n - 1) // 4] if n <= 24 else "heart"
        with scaled(3):
            m = v1.medallion(str(n), ACCENT[land], big=n % 4 == 0 or n > 24)
        my = y + 12 if n != 27 else y + 118
        marked.alpha_composite(m, (int(x - m.width / 2), int(my - m.height / 2)))
    with scaled(3):
        am = v1.letter_medallion([".#.", "#.#", "###", "#.#", "#.#"], "d07cff")
    marked.alpha_composite(am, (int(av[0] - am.width / 2), int(av[1] - am.height / 2)))
    marked = frame(marked)
    marked.convert("RGB").save(out / "world_map_v3.png")
    del img, clean

    log("labels")
    label_view(marked, 1.0, 0, 0, nodes, av, 30).convert("RGB").save(out / "world_map_v3_labelled.png")
    ov = marked.resize((W // 2, H // 2), Image.LANCZOS)
    label_view(ov, 0.5, 0, 0, nodes, av, 20).convert("RGB").save(out / "world_map_v3_overview.png")
    views = {"ember-reach": cont_centre("fire"), "thunder-steppe": cont_centre("storm"),
             "verdant-deep": cont_centre("nature"), "frostmere": cont_centre("water"),
             "sunscar-canyon": cont_centre("earth"), "hollow-rift-and-citadel": (720, 640),
             "heartland": (CX, CY)}
    for name, (vx_, vy_) in views.items():
        x0 = int(np.clip(vx_ - 480, 0, W - 960))
        y0 = int(np.clip(vy_ - 270, 0, H - 540))
        crop = marked.crop((x0, y0, x0 + 960, y0 + 540)).resize((1920, 1080), Image.NEAREST)
        label_view(crop, 2.0, x0, y0, nodes, av, 30).convert("RGB").save(out / f"closeup_v3_{name}.png")

    data = {
        "size": [W, H], "scale": SCALE,
        "stages": [{"stage": n, "name": STAGES[n][0], "city": STAGES[n][1],
                    "land": LANDS[(n - 1) // 4] if n <= 24 else "heart",
                    "x": round(nodes[n][0], 1), "y": round(nodes[n][1], 1)} for n in sorted(nodes)],
        "assault": {"name": "Nhal Vorath, the Crownless Citadel", "x": av[0], "y": av[1],
                    "route": [[round(x, 1), round(y, 1)] for x, y in assault]},
        "continents": {land: {"centre": [round(v, 1) for v in cont_centre(land)], "link": LINK[land]}
                       for land in LANDS},
    }
    (out / "world_map_v3_nodes.json").write_text(json.dumps(data, indent=1))
    log(f"wrote {out}")


if __name__ == "__main__":
    main()
