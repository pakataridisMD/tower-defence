"""The campaign world map of Orrhen, painted as hand-drawn pixel art.

Design only (not wired into the game). The map is painted at 960x540 art pixels and shown at 2x
(1920x1080), with nearest filtering, light from the upper left like every sprite in the game.

Layout follows the lore (lore/bible.md, sections 2 and 5) and the in-game element ring
(Fire at the top, then clockwise Storm, Nature, Water, Earth, Void):

- six lands ring the Heartland, four stages each, retreating from the coast toward the middle;
- the Heartland holds Crossmere, the Lumen Gate and Solenne, built on the black ruins of Vael;
- the Crack splits the Hollow Rift and opens onto the Outer Hollow, where Nhal Vorath hangs
  upside down beneath a black sun (the final assault).

Usage:
    python3 tools/art/worldmap/gen_world_map.py [--out art/worldmap] [--seed 7]

Writes:
    world_map_base.png      terrain, scenery and cities, no nodes or labels (960x540)
    world_map_clean_2x.png  the same at 1920x1080
    world_map_nodes_2x.png  with stage medallions and roads (what the game would show)
    world_map_labelled.png  with names of lands and cities (preview for review)
    world_map_nodes.json    every stage's position in art pixels and its city
"""
from __future__ import annotations

import argparse
import colorsys
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 960, 540
SCALE = 2
CX, CY = 500.0, 292.0          # centre of the world disc
RX, RY = 318.0, 222.0          # radii of the disc
INK = (26, 18, 24)
ROOT = Path(__file__).resolve().parents[3]

# Ring order and screen angle (degrees, 0 = east, clockwise because y points down).
LANDS = ["fire", "storm", "nature", "water", "earth", "void"]
ANGLE = {"fire": -90, "storm": -30, "nature": 30, "water": 90, "earth": 150, "void": 210}
LAND_NAME = {
    "fire": "EMBER REACH", "storm": "THUNDER STEPPE", "nature": "VERDANT DEEP",
    "water": "FROSTMERE", "earth": "SUNSCAR CANYON", "void": "HOLLOW RIFT",
}
ACCENT = {
    "fire": "ff7a2a", "storm": "8fb8ff", "nature": "7fd05a", "water": "7fd8f0",
    "earth": "e0a050", "void": "b27cff", "heart": "fff2b8",
}

# Stage number -> (stage name, city) from the Ledger of Fallen Cities.
STAGES = {
    1: ("Ashfall Road", "Kethra"), 2: ("Cinder Steps", "Brazier Hold"),
    3: ("Obsidian Crossing", "Vitrea"), 4: ("Throne of Cinders", "Pyrrhenhall"),
    5: ("Windswept Pass", "Stonering Camp"), 6: ("Galeback Ridge", "Highwind"),
    7: ("The Long Squall", "Tarrow's Rest"), 8: ("Eye of the Storm", "Aurvanis"),
    9: ("Mossy Trail", "Fernholt"), 10: ("Rootway", "Elderhollow"),
    11: ("Bramble Maze", "Thornwall"), 12: ("Heart of the Grove", "Sylvanmere"),
    13: ("Tidepool Shore", "Netmend"), 14: ("Saltmarsh Bends", "Reedhaven"),
    15: ("Frozen Causeway", "Glasswater"), 16: ("The Drowned Throne", "Pearlhaven"),
    17: ("Red Gulch", "Dustmark"), 18: ("Canyon Switchbacks", "Kharum Terraces"),
    19: ("Mesa Loop", "Mesa Kharn"), 20: ("Titan's Cradle", "Grundhallow"),
    21: ("Starless Path", "Lamplight"), 22: ("Fractured Steps", "Vesperhold"),
    23: ("Mirror Rift", "Twinmoor"), 24: ("Throne of the Hollow King", "Umbrael"),
    25: ("Shattered Crossroads", "Crossmere"), 26: ("Prism Wastes", "The Lumen Gate"),
    27: ("Heart of the Ring", "Solenne"),
}


# --------------------------------------------------------------------------- colour

def hexc(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(base: str, n: int = 5, spread: float = 0.5, shift: float = 0.035) -> np.ndarray:
    """Same ramp as tools/art/pix2d/kit.py: shadows lean cool, lights lean warm."""
    r, g, b = [c / 255 for c in hexc(base)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    for i in range(n):
        t = i / (n - 1) - 0.5
        ll = min(0.93, max(0.04, l + t * spread * (0.8 if t > 0 else 1.1)))
        target = 0.13 if t > 0 else 0.72
        dh = ((target - h + 0.5) % 1.0) - 0.5
        hh = (h + dh * abs(t) * 2 * shift * 4) % 1.0
        ss = min(1.0, max(0.0, s * (1.0 - 0.5 * t if t > 0 else 1.0 - 0.25 * t)))
        out.append([int(c * 255) for c in colorsys.hls_to_rgb(hh, ll, ss)])
    return np.array(out, np.float32)


BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
BAYER = np.tile(BAYER4, (H // 4 + 1, W // 4 + 1))[:H, :W]


def tone(value: np.ndarray, pal: np.ndarray, dither: float = 0.55) -> np.ndarray:
    """Map 0..1 to ramp tones with ordered dithering between neighbours."""
    n = len(pal)
    idx = np.clip(np.floor(value * n + (BAYER[:value.shape[0], :value.shape[1]] - 0.5) * dither), 0, n - 1)
    return pal[idx.astype(int)]


# --------------------------------------------------------------------------- noise

def fbm(seed: int, scale: float, octaves: int = 4, h: int = H, w: int = W) -> np.ndarray:
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        cells = max(2, int(scale * 2 ** o))
        gw, gh = cells + 2, int(cells * h / w) + 3
        grid = Image.fromarray((rng.random((gh, gw)) * 255).astype(np.uint8))
        layer = np.asarray(grid.resize((int(w * gw / cells), int(h * gw / cells)), Image.BICUBIC),
                           np.float32)[:h, :w] / 255.0
        out += layer * amp
        total += amp
        amp *= 0.5
    out /= total
    return (out - out.min()) / (out.max() - out.min() + 1e-6)


def lit(height: np.ndarray, strength: float = 6.0) -> np.ndarray:
    """Brighten slopes facing the upper-left light, darken the others."""
    slope = height - np.roll(np.roll(height, 1, 0), 1, 1)
    return np.clip(height * 0.55 + 0.25 + slope * strength, 0, 1)


def dilate(mask: np.ndarray, n: int = 1) -> np.ndarray:
    out = mask.copy()
    for _ in range(n):
        m = out.copy()
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            m |= np.roll(np.roll(out, dy, 0), dx, 1)
        out = m
    return out


# --------------------------------------------------------------------------- geometry

YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)
NX, NY = (XX - CX) / RX, (YY - CY) / RY
RN = np.sqrt(NX ** 2 + NY ** 2)
ANG = np.degrees(np.arctan2(NY, NX))


def pos(angle: float, rn: float) -> tuple[float, float]:
    a = math.radians(angle)
    return CX + rn * RX * math.cos(a), CY + rn * RY * math.sin(a)


def stage_layout() -> dict[int, tuple[float, float]]:
    """Stage 1 near the coast, stage 4 (the land's capital) nearest the Heartland."""
    out: dict[int, tuple[float, float]] = {}
    radii = [0.86, 0.72, 0.585, 0.455]
    wiggle = [9.0, -8.0, 7.0, -2.0]
    for li, land in enumerate(LANDS):
        for k in range(4):
            out[li * 4 + k + 1] = pos(ANGLE[land] + wiggle[k], radii[k])
    out[25] = pos(118, 0.30)                  # Crossmere, on the ring road
    out[26] = pos(128, 0.135)                 # the Lumen Gate, Solenne's outer wall
    out[27] = (CX, CY + 2)                    # Solenne
    return out


# --------------------------------------------------------------------------- terrain

def paint_terrain(seed: int):
    rgb = np.zeros((H, W, 3), np.float32)
    n_coast = fbm(seed + 1, 6, 5)
    n_big = fbm(seed + 12, 2.5, 3)
    n_ang = fbm(seed + 2, 4, 3)
    land_rn = RN + (n_coast - 0.5) * 0.14 + (n_big - 0.5) * 0.12
    is_land = land_rn < 1.0
    # a few islands off the coast
    isl = fbm(seed + 3, 14, 3)
    is_land |= (land_rn < 1.18) & (isl > 0.8)

    # which land each pixel belongs to
    warp = fbm(seed + 13, 7, 3)
    a = (ANG + 90 + (warp - 0.5) * 34 + (n_ang - 0.5) * 18) % 360
    land_idx = np.floor((a + 30) / 60).astype(int) % 6
    n_hrt = fbm(seed + 16, 10, 3)
    heart = RN + (n_ang - 0.5) * 0.14 + (n_hrt - 0.5) * 0.22 < 0.34

    # ---------- sea
    dist = np.clip((land_rn - 1.0) / 0.5, 0, 1)
    waves = fbm(seed + 4, 30, 2)
    sea_v = 0.62 - dist * 0.6 + (waves - 0.5) * 0.3
    sea = tone(sea_v, ramp("17405e", 5, 0.38))
    rgb[:] = sea
    # wave glints: short horizontal dashes
    glint = (waves > 0.72) & (np.roll(waves, 1, 1) <= 0.72) & (BAYER > 0.6)
    glint = glint | np.roll(glint, 1, 1)
    rgb[glint & ~is_land] = hexc("4f88b0")

    # ---------- the Outer Hollow: the top-left corner beyond the edge of the world
    n_edge = fbm(seed + 5, 5, 4)
    hollow_d = np.sqrt((XX / 300.0) ** 2 + (YY / 215.0) ** 2) + (n_edge - 0.5) * 0.4 + (n_big - 0.5) * 0.3
    hollow = (hollow_d < 1.0) & ~is_land
    neb = fbm(seed + 6, 3, 4)
    sky = tone(np.clip(neb * 0.6 - 0.05 + (1 - hollow_d) * 0.15, 0, 1), ramp("1b1030", 5, 0.25, 0.01), 0.8)
    rgb[hollow] = sky[hollow]
    rim = dilate(hollow, 2) & ~hollow & ~is_land
    rgb[rim] = hexc("6a3aa8")
    rgb[dilate(hollow, 1) & ~hollow & ~is_land] = hexc("c79bff")
    rng = np.random.default_rng(seed + 7)
    stars = hollow & (rng.random((H, W)) > 0.993)
    rgb[stars] = hexc("e8d8ff")

    # ---------- coast: shallow water and foam
    shallow = ~is_land & dilate(is_land, 3) & ~hollow
    rgb[shallow] = rgb[shallow] * 0.6 + np.array(hexc("3f86a0")) * 0.4
    foam = ~is_land & dilate(is_land, 1)
    rgb[foam] = hexc("cfe8ef")

    # ---------- lands
    height = fbm(seed + 8, 8, 5)
    detail = fbm(seed + 9, 40, 2)
    river = fbm(seed + 10, 5, 4)
    shade = lit(height * 0.7 + detail * 0.3, 7.0)
    patch = fbm(seed + 14, 5, 4)                      # big patches of a second ground type
    pmask = (patch + (BAYER - 0.5) * 0.06) > 0.56
    stream = np.abs(fbm(seed + 15, 3.5, 4) - 0.5) < 0.012  # rivers and gorges
    for li, land in enumerate(LANDS):
        m = is_land & (land_idx == li) & ~heart
        if land == "fire":
            v = tone(shade * 0.9, ramp("3a2624", 5, 0.32))
            ash = tone(shade * 0.85, ramp("5a504c", 5, 0.3))
            v[pmask] = ash[pmask]
            lava = np.abs(river - 0.5) < 0.011
            glow = dilate(lava, 2) & ~lava
            v[glow] = v[glow] * 0.55 + np.array(hexc("c2401c")) * 0.45
            v[lava] = hexc("ff9c2e")
            core = lava & (np.abs(river - 0.5) < 0.004)
            v[core] = hexc("ffe680")
        elif land == "storm":
            wind = (np.sin(XX * 0.35 - YY * 0.9 + detail * 6) * 0.5 + 0.5) * 0.25
            v = tone(np.clip(shade * 0.8 + wind, 0, 1), ramp("7d9a3a", 5, 0.45))
            gold = tone(np.clip(shade * 0.8 + wind, 0, 1), ramp("b8a04a", 5, 0.45))
            v[pmask] = gold[pmask]
            v[stream] = hexc("4a86b0")
            v[dilate(stream) & ~stream] = hexc("2e4a3a")
        elif land == "nature":
            v = tone(shade * 0.8, ramp("2b5a2a", 5, 0.4))
            moss = (detail > 0.86) & (BAYER > 0.8)
            v[moss] = hexc("7ff0c8")
            v[stream] = hexc("3a7aa0")
            v[dilate(stream) & ~stream] = hexc("1a3a24")
        elif land == "water":
            ice = tone(np.clip(shade * 0.6 + 0.3, 0, 1), ramp("9cc4e2", 5, 0.35))
            snow = tone(np.clip(shade * 0.5 + 0.5, 0, 1), ramp("dfeaf4", 5, 0.2))
            ice[pmask] = snow[pmask]
            crack = np.abs(river - 0.5) < 0.006
            ice[crack] = hexc("3d6f9e")
            open_w = height < 0.33
            ice[open_w] = tone(height * 2.2, ramp("24527e", 5, 0.3))[open_w]
            ice[dilate(open_w) & ~open_w] = hexc("f4fbff")
            v = ice
        elif land == "earth":
            steps = np.floor((height * 0.8 + detail * 0.08) * 7) / 7
            v = tone(lit(steps, 9.0) * 0.9 + 0.05, ramp("b25a30", 5, 0.45))
            sand = tone(lit(steps, 9.0) * 0.9 + 0.05, ramp("c88a50", 5, 0.4))
            v[pmask] = sand[pmask]
            edge = steps != np.roll(steps, -1, 0)
            v[edge] = hexc("4a2016")
            gorge = dilate(stream)
            v[gorge] = hexc("2a120c")
            v[stream & (BAYER > 0.5)] = hexc("4a86b0")
        else:  # void
            v = tone(shade * 0.85, ramp("3e2766", 5, 0.35))
            dark = tone(shade * 0.7, ramp("22163c", 5, 0.3))
            v[pmask] = dark[pmask]
            spark = (detail > 0.9) & (BAYER > 0.9)
            v[spark] = hexc("e2c8ff")
        rgb[m] = v[m]

    # ---------- Heartland: prism glass plains
    hm = is_land & heart
    hue = (fbm(seed + 11, 6, 3) * 1.4) % 1.0
    pr = np.zeros((H, W, 3), np.float32)
    for i, c in enumerate(colorsys.hsv_to_rgb(h, 0.16, 1.0) for h in np.linspace(0, 1, 7)[:-1]):
        pr[(np.floor(hue * 6) % 6) == i] = np.array(c) * 255
    base = tone(np.clip(shade * 0.6 + 0.3, 0, 1), ramp("b4aec4", 5, 0.35))
    v = base * 0.75 + pr * 0.25
    streak = (np.abs(((XX + YY * 0.6 + detail * 20) % 23) - 11) < 0.6) & (BAYER > 0.4)
    v[streak] = np.minimum(v[streak] + 28, 255)
    rgb[hm] = v[hm]

    # dark seams where lands meet (a soft cliff line)
    lab = np.where(is_land, np.where(heart, 6, land_idx), -1)
    seam = is_land & ((lab != np.roll(lab, 1, 0)) | (lab != np.roll(lab, 1, 1)))
    rgb[seam] = rgb[seam] * 0.55

    # coast cliffs: land pixels with sea just below them get a dark lip
    lip = is_land & ~np.roll(is_land, -1, 0)
    rgb[lip] = rgb[lip] * 0.5
    lip2 = is_land & ~np.roll(is_land, -2, 0) & ~lip
    rgb[lip2] = rgb[lip2] * 0.75

    info = {"is_land": is_land, "land_idx": land_idx, "heart": heart, "hollow": hollow,
            "lab": lab, "river": river, "height": height}
    return rgb, info


# --------------------------------------------------------------------------- sprites

class Spr:
    """A small RGBA sprite drawn with hard-edged PIL shapes, inked and shadowed afterwards."""

    def __init__(self, w: int, h: int):
        self.im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.glow: list[tuple[int, int, str]] = []

    def rect(self, x0, y0, x1, y1, c):
        self.d.rectangle([x0, y0, x1, y1], fill=hexc(c) + (255,))

    def poly(self, pts, c):
        self.d.polygon([tuple(p) for p in pts], fill=hexc(c) + (255,))

    def ell(self, x0, y0, x1, y1, c):
        self.d.ellipse([x0, y0, x1, y1], fill=hexc(c) + (255,))

    def px(self, x, y, c, glow=False):
        self.d.point((x, y), fill=hexc(c) + (255,))
        if glow:
            self.glow.append((x, y, c))

    def line(self, pts, c, w=1):
        self.d.line([tuple(p) for p in pts], fill=hexc(c) + (255,), width=w)

    def done(self, ink=INK) -> Image.Image:
        a = np.asarray(self.im).copy()
        mask = a[..., 3] > 0
        pad = np.pad(mask, 1)
        ring = np.zeros_like(pad)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            ring |= np.roll(np.roll(pad, dy, 0), dx, 1)
        ring &= ~pad
        out = np.zeros((a.shape[0] + 2, a.shape[1] + 2, 4), np.uint8)
        out[1:-1, 1:-1] = a
        out[ring] = ink + (255,)
        return Image.fromarray(out)


def shaded_block(s: Spr, x, y, w, h, top, front, side, depth=2):
    """A hard-edged block seen from above: lit top, front face, dark right side."""
    s.rect(x, y + depth, x + w - 1, y + h - 1, front)
    s.rect(x, y, x + w - 1, y + depth - 1, top)
    s.rect(x + w - 2, y + depth, x + w - 1, y + h - 1, side)


def house(s: Spr, x, y, land, w=7, big=False):
    """One building in the style of its land. (x, y) is the top-left of the roof."""
    if land == "fire":                 # dark stone, flat red roof, glowing forge chimney
        shaded_block(s, x, y, w, 7, "a8402a", "4a3632", "2e2220", 3)
        s.rect(x + w - 3, y - 3, x + w - 2, y, "3a2a28")
        s.px(x + w - 3, y - 4, "ffcf5a", glow=True)
        s.px(x + 2, y + 5, "ffb040", glow=True)
    elif land == "storm":              # cone tents with a pole and pennant
        s.poly([(x, y + 7), (x + w // 2, y), (x + w - 1, y + 7)], "d8c79a")
        s.poly([(x + w // 2, y), (x + w - 1, y + 7), (x + w // 2 + 1, y + 7)], "9c8a62")
        s.line([(x + w // 2, y - 3), (x + w // 2, y)], "5a4630")
        s.px(x + w // 2 + 1, y - 3, "6fa0ff")
        s.px(x + w // 2 - 1, y + 6, "3a2e22")
    elif land == "nature":             # round thatch hut under a canopy
        s.ell(x - 1, y - 3, x + w, y + 3, "3f8a36")
        s.ell(x, y - 3, x + w - 3, y + 1, "6cb848")
        shaded_block(s, x + 1, y + 2, w - 2, 5, "8a6a3a", "6a4a2a", "4a321e", 1)
        s.px(x + w // 2, y + 5, "ffe08a", glow=True)
    elif land == "water":              # white walls on stilts, blue dome roof
        s.rect(x + 1, y + 6, x + 1, y + 8, "5a4a3a")
        s.rect(x + w - 2, y + 6, x + w - 2, y + 8, "5a4a3a")
        shaded_block(s, x, y + 2, w, 5, "f4f8ff", "dbe6f0", "9ab0c8", 1)
        s.ell(x + 1, y - 1, x + w - 2, y + 3, "5a8ed0")
        s.px(x + 2, y, "bfe0ff")
        s.px(x + w // 2, y + 5, "ffe08a", glow=True)
    elif land == "earth":              # sandstone block cut into the rock, dark doorways
        shaded_block(s, x, y, w, 8, "e8b070", "c07a44", "7a4428", 3)
        s.rect(x + 2, y + 5, x + 3, y + 7, "2a1410")
        s.px(x + w - 4, y + 4, "ffd070", glow=True)
    else:                              # void: dark domed observatory huts with violet light
        shaded_block(s, x, y + 2, w, 6, "4a3a6a", "2e2448", "1c1630", 1)
        s.ell(x, y - 1, x + w - 1, y + 4, "5e4a8a")
        s.px(x + 2, y + 0, "9a84c8")
        s.px(x + w // 2, y + 5, "c8a0ff", glow=True)


def city_sprite(num: int, land: str, rng) -> Image.Image:
    """A cluster of buildings; the land's capital (stage 4) gets a landmark."""
    capital = num % 4 == 0 and num <= 24
    w, h = (46, 40) if capital else (30, 24)
    s = Spr(w, h)
    if capital:
        landmark(s, land, w, h)
    spots = [(3, 10), (12, 6), (20, 11), (8, 15), (17, 15)] if not capital else \
        [(2, 26), (10, 29), (30, 28), (37, 25), (19, 31)]
    count = 4 if not capital else 5
    order = sorted(spots[:count], key=lambda p: p[1])
    for x, y in order:
        house(s, x + int(rng.integers(-1, 2)), y, land, w=7 if land != "storm" else 8)
    # a little wall or palisade for forts
    if num in (2, 11):
        s.rect(1, h - 4, w - 2, h - 3, "6a5a50" if num == 2 else "4a6a2a")
        for x in range(1, w - 1, 3):
            s.px(x, h - 5, "8a7a70" if num == 2 else "6a8a3a")
    return s.done()


def landmark(s: Spr, land, w, h):
    if land == "fire":   # Pyrrhenhall: the caldera with a lava lake
        s.ell(4, 2, w - 5, 24, "4a302a")
        s.ell(8, 6, w - 9, 21, "2a1a18")
        s.ell(11, 9, w - 12, 19, "ff8a2a")
        s.ell(15, 11, w - 17, 16, "ffe07a")
        s.poly([(4, 13), (8, 6), (12, 9)], "7a4a38")
    elif land == "storm":  # Aurvanis: the great tent of the Sky-Moot
        s.poly([(6, 24), (23, 2), (40, 24)], "e8dcb0")
        s.poly([(23, 2), (40, 24), (25, 24)], "a8946a")
        s.line([(23, 0), (23, 3)], "5a4630")
        s.rect(24, 0, 27, 1, "6fa0ff")
        for x in (12, 18, 28, 34):
            s.line([(x, 24 - abs(x - 23) // 2), (x, 24)], "8a7650")
    elif land == "nature":  # Sylvanmere: the great tree
        s.rect(20, 14, 26, 30, "6a4a2a")
        s.rect(20, 14, 21, 30, "8a6a3a")
        s.ell(2, 0, w - 3, 22, "2e6b30")
        s.ell(6, 1, w - 12, 15, "4a8f3a")
        s.ell(9, 2, 22, 10, "86c450")
        for gx, gy in ((10, 12), (30, 9), (22, 17), (35, 15)):
            s.px(gx, gy, "c8ffb0", glow=True)
    elif land == "water":  # Pearlhaven: pearl domes and a harbour mole
        s.rect(2, 22, w - 3, 24, "dbe6f0")
        s.ell(12, 4, 33, 22, "f2f6ff")
        s.ell(14, 5, 24, 13, "ffffff")
        s.ell(27, 13, 32, 20, "c8d8ec")
        s.rect(22, 0, 23, 5, "c8d8ec")
        s.px(22, 0, "ffe08a", glow=True)
    elif land == "earth":  # Grundhallow: a giant carved face over the Deep Halls
        s.poly([(6, 24), (8, 2), (38, 2), (40, 24)], "c07a44")
        s.poly([(8, 2), (38, 2), (36, 5), (10, 5)], "e8b070")
        s.poly([(34, 5), (38, 2), (40, 24), (36, 24)], "7a4428")
        s.rect(13, 9, 18, 11, "4a2016")
        s.rect(27, 9, 32, 11, "4a2016")
        s.px(15, 10, "ffd070", glow=True)
        s.px(29, 10, "ffd070", glow=True)
        s.poly([(21, 10), (24, 10), (25, 17), (20, 17)], "a8622e")
        s.rect(17, 19, 28, 24, "2a1410")
        s.rect(19, 21, 26, 24, "1a0c08")
    else:  # Umbrael: the observatory and its great telescope
        s.ell(9, 6, 36, 26, "3e2f60")
        s.ell(11, 7, 26, 18, "5e4a8a")
        s.poly([(22, 14), (40, 0), (43, 3), (25, 17)], "8a7ab0")
        s.poly([(25, 17), (43, 3), (43, 5), (26, 18)], "4a3a70")
        s.px(41, 1, "e8d8ff", glow=True)
        s.px(18, 20, "c8a0ff", glow=True)


def solenne_sprite() -> Image.Image:
    """Six stepped walls faced with the stone of each land, the Heartstone and the Spire of Aurel."""
    w, h = 96, 80
    s = Spr(w, h)
    walls = ["b8442c", "7e8a9c", "3f7f38", "6cb8dc", "c88446", "2a1e3e"]  # outer to inner
    cx, cy0 = w // 2, h - 30
    rng = np.random.default_rng(3)
    for i, c in enumerate(walls):
        rx, ry = 46 - i * 7, 26 - i * 4
        cy = cy0 - i * 3                                             # each ring stands higher
        s.ell(cx - rx, cy - ry + 3, cx + rx, cy + ry + 3, "4a4458")    # wall face
        s.ell(cx - rx, cy - ry + 3, cx + rx, cy + ry + 2, _darken(c, 0.7))
        s.ell(cx - rx, cy - ry, cx + rx, cy + ry, c)                   # wall top
        s.ell(cx - rx + 2, cy - ry + 1, cx + rx - 2, cy + ry - 1, "d8d2e2")
        if i < 5:   # white roofs packed between this wall and the next
            for _ in range(110 - i * 16):
                a = rng.uniform(0, 2 * math.pi)
                t = rng.uniform(0.62, 0.92)
                x = int(cx + rx * t * math.cos(a))
                y = int(cy + ry * t * math.sin(a))
                s.rect(x - 1, y - 1, x + 1, y, "fbf8ff")
                s.px(x + 1, y, "9a90b4")
                s.px(x - 1, y + 1, "6a6080")
                if rng.random() < 0.15:
                    s.px(x, y + 1, "ffe08a")
    cy = cy0 - 5 * 3
    # Hall of the Ring and the Heartstone
    s.ell(cx - 8, cy - 5, cx + 8, cy + 5, "f8f4ff")
    s.ell(cx - 5, cy - 3, cx + 5, cy + 3, "fff2b8")
    for k, c in enumerate(["ff7a2a", "8fb8ff", "7fd05a", "7fd8f0", "e0a050", "b27cff"]):
        a = math.radians(k * 60 - 90)
        s.px(cx + round(4 * math.cos(a)), cy + round(2 * math.sin(a)), c, glow=True)
    s.px(cx, cy, "ffffff", glow=True)
    # the Spire of Aurel, tall and white, with the Sunstone lens at the top
    sx, base = cx + 13, cy + 4
    s.poly([(sx - 3, base), (sx - 1, base - 34), (sx + 1, base - 34), (sx + 3, base)], "f4f0fa")
    s.poly([(sx + 1, base - 34), (sx + 3, base), (sx + 1, base)], "b8b0cc")
    s.ell(sx - 4, base - 42, sx + 4, base - 34, "fff0a0")
    s.ell(sx - 2, base - 40, sx + 1, base - 37, "ffffff")
    # the Dawn Gate on the east side of the outer wall
    gx, gy = cx + 44, cy0 + 1
    s.rect(gx - 2, gy - 4, gx + 2, gy + 4, "fff2b8")
    s.rect(gx - 1, gy - 1, gx + 1, gy + 4, "3a3448")
    return s.done()


def nhal_vorath_sprite() -> Image.Image:
    """The Crownless Citadel, built from what the Unbound tore out of the world, hanging upside down
    beneath a black sun. Its gate is a mouth; its long middle spire is Solenne's, made wrong."""
    w, h = 176, 170
    s = Spr(w, h)
    cx = w // 2
    rng = np.random.default_rng(11)
    # black sun: corona rays, rim, black core
    for k in range(0, 360, 15):
        a = math.radians(k)
        ln = 34 if k % 30 else 40
        s.line([(cx + 26 * math.cos(a), 28 + 24 * math.sin(a)), (cx + ln * math.cos(a), 28 + ln * 0.85 * math.sin(a))],
               "5a2a9a")
    s.ell(cx - 28, 2, cx + 28, 54, "8a4ae0")
    s.ell(cx - 25, 4, cx + 25, 52, "3a1a60")
    s.ell(cx - 22, 6, cx + 22, 50, "05030a")
    # the upturned foundation: a slab of stolen ground
    top = 50
    s.poly([(cx - 62, top), (cx + 62, top), (cx + 50, top + 16), (cx - 50, top + 16)], "2e2838")
    s.poly([(cx - 62, top), (cx + 62, top), (cx + 60, top + 4), (cx - 60, top + 4)], "54496a")
    s.poly([(cx + 40, top + 4), (cx + 60, top + 4), (cx + 50, top + 16), (cx + 36, top + 16)], "1a1622")
    # stolen things jutting out: a burned red wall, a frozen ship, an uprooted tree, a broken Order tower
    s.poly([(cx - 60, top + 2), (cx - 78, top - 8), (cx - 74, top + 10), (cx - 58, top + 12)], "6a2a20")
    s.rect(cx - 76, top - 6, cx - 72, top - 4, "a84030")
    s.poly([(cx + 58, top + 2), (cx + 82, top - 12), (cx + 76, top + 2), (cx + 54, top + 14)], "8ab0c8")
    s.line([(cx + 70, top - 6), (cx + 70, top - 20)], "5a4a3a")
    s.poly([(cx - 30, top + 16), (cx - 40, top + 34), (cx - 34, top + 34), (cx - 26, top + 16)], "4a3a2a")
    for k in range(4):
        s.line([(cx - 36, top + 30), (cx - 46 + k * 4, top + 42 + (k % 2) * 3)], "3a2a1e")
    # hanging spires pointing down
    spires = [(-46, 34, 6), (-30, 52, 8), (-14, 70, 9), (0, 108, 11), (14, 72, 9), (30, 54, 8), (46, 36, 6)]
    for dx, ln, half in spires:
        x, y0 = cx + dx, top + 14
        s.poly([(x - half, y0), (x + half, y0), (x, y0 + ln)], "2a2436")
        s.poly([(x - half, y0), (x - half + 3, y0), (x, y0 + ln)], "4e4664")
        s.poly([(x + half - 3, y0), (x + half, y0), (x, y0 + ln)], "15111e")
        for k in range(y0 + 6, y0 + ln - 6, 8):
            s.px(x - 1, k, "ff3a5a", glow=True)
        # bands of stolen wall stone on the spires, one per land
        band = ["a84030", "7e8a9c", "3f7f38", "6cb8dc", "c88446", "2a1e3e"][int(rng.integers(0, 6))]
        s.line([(x - half + 2, y0 + 4), (x + half - 2, y0 + 4)], band)
    # the middle spire is Solenne's, made wrong: six rings, upside down
    x = cx
    for k, c in enumerate(["b8442c", "7e8a9c", "3f7f38", "6cb8dc", "c88446", "4a3a6e"]):
        y = top + 22 + k * 11
        half = max(2, 9 - k)
        s.line([(x - half, y), (x + half, y)], c)
    # the gate is a mouth, with teeth, in the underside of the slab
    gy = top + 6
    s.ell(cx - 16, gy - 4, cx + 16, gy + 10, "0a0610")
    for k in range(-13, 14, 4):
        s.poly([(cx + k - 2, gy - 2), (cx + k + 2, gy - 2), (cx + k, gy + 3)], "e0d6c4")
        s.poly([(cx + k - 2, gy + 9), (cx + k + 2, gy + 9), (cx + k, gy + 4)], "e0d6c4")
    s.px(cx - 6, gy + 3, "ff3a5a", glow=True)
    s.px(cx + 6, gy + 3, "ff3a5a", glow=True)
    return s.done(ink=(40, 10, 50))


def mountain(rng, snow: bool) -> Image.Image:
    w = int(rng.integers(12, 20))
    hgt = int(w * rng.uniform(0.7, 1.0))
    s = Spr(w, hgt)
    peak = int(w * rng.uniform(0.35, 0.55))
    s.poly([(0, hgt - 1), (peak, 0), (w - 1, hgt - 1)], "6a6478")
    s.poly([(0, hgt - 1), (peak, 0), (peak - 1, hgt - 1)], "9a94a8")
    s.poly([(peak, 0), (w - 1, hgt - 1), (peak + w // 4, hgt - 1)], "4a4458")
    if snow:
        s.poly([(peak - 3, 4), (peak, 0), (peak + 3, 4), (peak + 1, 3)], "f4f6ff")
    return s.done()


def tree(rng, r: int) -> Image.Image:
    s = Spr(2 * r + 2, 2 * r + 3)
    s.ell(0, 1, 2 * r, 2 * r + 1, "1f4a26")
    s.ell(1, 0, 2 * r - 2, 2 * r - 1, "2e6b30")
    s.ell(2, 1, r + 1, r, "4a8f3a")
    s.px(3, 2, "8ccf5a")
    return s.done(ink=(16, 30, 18))


def stone(rng) -> Image.Image:
    s = Spr(3, 6)
    s.rect(0, 0, 2, 5, "8a8a94")
    s.rect(0, 0, 0, 5, "b8b8c4")
    s.rect(2, 0, 2, 5, "5a5a66")
    return s.done()


def float_step(rng) -> Image.Image:
    w = int(rng.integers(5, 9))
    s = Spr(w, 4)
    s.rect(0, 0, w - 1, 1, "8a7ab0")
    s.rect(0, 2, w - 1, 3, "4a3a70")
    return s.done((20, 10, 40))


def ruin(rng) -> Image.Image:
    """Black stone of old Vael: a broken pillar, a broken arch or a fallen block."""
    kind = rng.integers(0, 3)
    if kind == 0:
        hgt = int(rng.integers(6, 11))
        s = Spr(4, hgt)
        s.rect(0, 1, 3, hgt - 1, "2a2632")
        s.rect(0, 1, 0, hgt - 1, "4e4660")
        s.poly([(0, 1), (3, 0), (3, 2)], "3a3444")
    elif kind == 1:
        s = Spr(11, 9)
        s.rect(0, 2, 2, 8, "2a2632")
        s.rect(0, 2, 0, 8, "4e4660")
        s.rect(8, 4, 10, 8, "2a2632")
        s.rect(8, 4, 8, 8, "4e4660")
        s.rect(0, 0, 6, 2, "3a3444")
        s.rect(0, 0, 6, 0, "5a5270")
    else:
        s = Spr(8, 5)
        s.rect(0, 1, 7, 4, "2a2632")
        s.rect(0, 1, 7, 1, "4e4660")
        s.px(3, 3, "b27cff")
    return s.done()


def crystal(rng) -> Image.Image:
    """A shard of prism glass with a rainbow glint."""
    hgt = int(rng.integers(4, 8))
    s = Spr(4, hgt)
    hue = rng.random()
    c = "%02x%02x%02x" % tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.28, 1.0))
    d = "%02x%02x%02x" % tuple(int(v * 255) for v in colorsys.hsv_to_rgb(hue, 0.35, 0.75))
    s.poly([(0, hgt - 1), (1, 0), (3, hgt - 1)], c)
    s.poly([(1, 0), (3, hgt - 1), (2, hgt - 1)], d)
    s.px(1, 1, "ffffff")
    return s.done((70, 64, 96))


def ice_spire(rng) -> Image.Image:
    s = Spr(5, 8)
    s.poly([(0, 7), (2, 0), (4, 7)], "bfe6ff")
    s.poly([(2, 0), (4, 7), (3, 7)], "6aa0d0")
    return s.done((30, 50, 80))


def mesa(rng) -> Image.Image:
    w = int(rng.integers(12, 22))
    s = Spr(w, 11)
    s.rect(1, 3, w - 2, 10, "a8552e")
    s.rect(1, 3, w - 2, 5, "e8a868")
    s.rect(w - 4, 4, w - 2, 10, "6a3020")
    s.line([(1, 8), (w - 3, 8)], "7a3a22")
    return s.done()


def basalt(rng) -> Image.Image:
    s = Spr(6, 7)
    s.poly([(0, 6), (2, 0), (5, 2), (5, 6)], "3a2a2c")
    s.poly([(0, 6), (2, 0), (2, 6)], "5a4444")
    s.px(3, 6, "ff8a2a", glow=True)
    return s.done()


# --------------------------------------------------------------------------- compositing

class Board:
    def __init__(self, rgb: np.ndarray):
        self.base = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
        self.items: list[tuple[float, Image.Image, int, int, float]] = []
        self.glows: list[tuple[int, int, str, int]] = []

    def put(self, im: Image.Image, x: float, y: float, shadow: float = 2.0, glows=None):
        """Place a sprite with its bottom-centre at (x, y)."""
        x0, y0 = int(round(x - im.width / 2)), int(round(y - im.height))
        self.items.append((y, im, x0, y0, shadow))

    def bake(self) -> Image.Image:
        out = self.base.copy()
        shadow_layer = Image.new("RGBA", out.size, (0, 0, 0, 0))
        for _, im, x0, y0, sh in self.items:
            if sh:
                a = np.asarray(im)[..., 3]
                sil = np.zeros(a.shape + (4,), np.uint8)
                sil[..., 3] = np.where(a > 0, 110, 0)
                sil[..., :3] = (12, 8, 24)
                shadow_layer.alpha_composite(Image.fromarray(sil), (x0 + int(sh), y0 + int(sh) // 2 + 1))
        out.alpha_composite(shadow_layer)
        for _, im, x0, y0, _ in sorted(self.items, key=lambda t: t[0]):
            out.alpha_composite(im, (x0, y0))
        return out


def add_glow(img: Image.Image, points: list[tuple[int, int, str, int]]) -> Image.Image:
    """Soft additive light pools around glowing pixels (lava, windows, the Heartstone)."""
    a = np.asarray(img).astype(np.float32)
    light = np.zeros((H, W, 3), np.float32)
    for x, y, c, r in points:
        if not (0 <= x < W and 0 <= y < H):
            continue
        x0, x1, y0, y1 = max(0, x - r), min(W, x + r + 1), max(0, y - r), min(H, y + r + 1)
        yy, xx = np.mgrid[y0:y1, x0:x1]
        d = np.sqrt((xx - x) ** 2 + (yy - y) ** 2) / r
        f = np.clip(1 - d, 0, 1) ** 2
        # stepped falloff so the light reads as pixel art, not an airbrush
        f = np.floor(f * 4 + BAYER[y0:y1, x0:x1] * 0.9) / 4 * 0.33
        light[y0:y1, x0:x1] += f[..., None] * np.array(hexc(c), np.float32)
    a[..., :3] = np.clip(a[..., :3] + light, 0, 255)
    return Image.fromarray(a.astype(np.uint8))


def scatter(board, info, rng, cities, avoid):
    is_land, land_idx, heart, lab = info["is_land"], info["land_idx"], info["heart"], info["lab"]

    def free(x, y, r):
        return all((x - ax) ** 2 + ((y - ay) * 1.3) ** 2 > (r + ar) ** 2 for ax, ay, ar in avoid)

    def land_at(x, y):
        xi, yi = int(x), int(y)
        if not (2 <= xi < W - 2 and 2 <= yi < H - 2) or not is_land[yi, xi]:
            return None
        return "heart" if heart[yi, xi] else LANDS[land_idx[yi, xi]]

    # mountains along the borders between lands
    seam = is_land & (lab >= 0) & (lab < 6) & ((lab != np.roll(lab, 3, 1)) | (lab != np.roll(lab, 3, 0)))
    seam &= (lab != 6) & (np.roll(lab, 3, 1) != 6) & (np.roll(lab, 3, 0) != 6)
    ys, xs = np.nonzero(seam)
    order = rng.permutation(len(xs))
    placed = []
    for i in order[:2600]:
        x, y = xs[i], ys[i]
        if RN[y, x] > 0.98 or not free(x, y, 8):
            continue
        if any((x - px) ** 2 + (y - py) ** 2 < 120 for px, py in placed):
            continue
        placed.append((x, y))
        board.put(mountain(rng, snow=RN[y, x] < 0.75 or LANDS[land_idx[y, x]] == "water"), x, y + 3)

    # land scenery
    for _ in range(9000):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        land = land_at(x, y)
        if land is None or not free(x, y, 5):
            continue
        if land == "nature" and rng.random() < 0.9:
            board.put(tree(rng, int(rng.integers(3, 6))), x, y, 2)
            avoid.append((x, y, 3))
        elif land == "fire" and rng.random() < 0.05:
            board.put(basalt(rng), x, y, 1)
            avoid.append((x, y, 4))
        elif land == "storm" and rng.random() < 0.03:
            for k in range(int(rng.integers(1, 4))):
                board.put(stone(rng), x + k * 4, y + (k % 2), 1)
            avoid.append((x, y, 8))
        elif land == "water" and rng.random() < 0.035:
            board.put(ice_spire(rng), x, y, 1)
            avoid.append((x, y, 4))
        elif land == "earth" and rng.random() < 0.012:
            board.put(mesa(rng), x, y, 2)
            avoid.append((x, y, 10))
        elif land == "void" and rng.random() < 0.05:
            board.put(float_step(rng), x, y - 5, 5)
            avoid.append((x, y, 5))
        elif land == "heart" and RN[int(y), int(x)] < 0.27 and rng.random() < 0.2:
            board.put(ruin(rng), x, y, 1)
            avoid.append((x, y, 5))
        elif land == "heart" and rng.random() < 0.25:
            board.put(crystal(rng), x, y, 1)
            avoid.append((x, y, 3))


def stage_land(num: int) -> str:
    return LANDS[(num - 1) // 4] if num <= 24 else "heart"


def roads_layer(nodes: dict[int, tuple[float, float]], assault: list[tuple[float, float]]) -> Image.Image:
    """Dirt roads between stages, the Heartland ring road, and the assault route through the Crack."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)

    def road(pts, fill, edge, dash=0):
        pts = [(round(x), round(y)) for x, y in pts]
        d.line(pts, fill=edge + (255,), width=4, joint="curve")
        if not dash:
            d.line(pts, fill=fill + (255,), width=2, joint="curve")
            return
        # dashes along the polyline
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            n = max(1, int(math.hypot(x1 - x0, y1 - y0) / dash))
            for k in range(0, n, 2):
                a, b = k / n, min(1, (k + 1) / n)
                d.line([(x0 + (x1 - x0) * a, y0 + (y1 - y0) * a), (x0 + (x1 - x0) * b, y0 + (y1 - y0) * b)],
                       fill=fill + (255,), width=2)

    ring = [pos(a, 0.31 + 0.012 * math.sin(math.radians(a * 5))) for a in range(0, 361, 6)]
    road(ring, hexc("efe4c8"), hexc("6a5a48"))
    for li in range(6):
        pts = [nodes[li * 4 + k + 1] for k in range(4)]
        a = ANGLE[LANDS[li]] - 2
        pts.append(pos(a, 0.31))
        road(_bend(pts), hexc("d8c49a"), hexc("4a3a2e"))
    road([nodes[25], nodes[26], nodes[27]], hexc("fff6d8"), hexc("6a5a48"))
    road(assault, hexc("d07cff"), hexc("2a0a3a"), dash=3)
    return layer


def _bend(pts):
    """Wobble a polyline a little so roads look walked rather than ruled."""
    out = [pts[0]]
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        mx, my = (x0 + x1) / 2, (y0 + y1) / 2
        nx, ny = -(y1 - y0), (x1 - x0)
        ln = math.hypot(nx, ny) or 1
        k = 0.12 * (1 if len(out) % 2 else -1)
        out += [(mx + nx / ln * ln * k * 0.5, my + ny / ln * ln * k * 0.5), (x1, y1)]
    return out


# --------------------------------------------------------------------------- medallions and text

DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"], "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"], "3": ["###", "..#", ".##", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"], "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"], "7": ["###", "..#", ".#.", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"], "9": ["###", "#.#", "###", "..#", "###"],
}


def medallion(label: str, accent: str, big: bool = False) -> Image.Image:
    r = 8 if big else 6
    s = Spr(2 * r + 1, 2 * r + 2)
    s.ell(0, 1, 2 * r, 2 * r + 1, "1a1420")
    s.ell(0, 0, 2 * r, 2 * r, accent)
    s.ell(1, 1, 2 * r - 1, 2 * r - 1, _darken(accent, 0.45))
    s.ell(2, 2, 2 * r - 2, 2 * r - 2, "201828")
    s.px(3, 3, _lighten(accent))
    width = len(label) * 4 - 1
    x0, y0 = r - width // 2, r - 2
    for i, ch in enumerate(label):
        for yy, row in enumerate(DIGITS.get(ch, ["...", ] * 5)):
            for xx, c in enumerate(row):
                if c == "#":
                    s.px(x0 + i * 4 + xx, y0 + yy, "fff6e0")
    return s.done()


def letter_medallion(ch_rows: list[str], accent: str) -> Image.Image:
    r = 8
    s = Spr(2 * r + 1, 2 * r + 2)
    s.ell(0, 1, 2 * r, 2 * r + 1, "1a1420")
    s.ell(0, 0, 2 * r, 2 * r, accent)
    s.ell(2, 2, 2 * r - 2, 2 * r - 2, "1a0a24")
    for yy, row in enumerate(ch_rows):
        for xx, c in enumerate(row):
            if c == "#":
                s.px(r - len(row) // 2 + xx, r - 3 + yy, "ffd0ff")
    return s.done()


def _darken(c, f):
    return "%02x%02x%02x" % tuple(int(v * f) for v in hexc(c))


def _lighten(c):
    return "%02x%02x%02x" % tuple(min(255, int(v + (255 - v) * 0.6)) for v in hexc(c))


PIXFONT = {
    "A": [".###.", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "B": ["####.", "#...#", "#...#", "####.", "#...#", "#...#", "####."],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "G": [".####", "#....", "#....", "#.###", "#...#", "#...#", ".###."],
    "H": ["#...#", "#...#", "#...#", "#####", "#...#", "#...#", "#...#"],
    "I": ["###", ".#.", ".#.", ".#.", ".#.", ".#.", "###"],
    "K": ["#...#", "#..#.", "#.#..", "##...", "#.#..", "#..#.", "#...#"],
    "L": ["#....", "#....", "#....", "#....", "#....", "#....", "#####"],
    "M": ["#...#", "##.##", "#.#.#", "#.#.#", "#...#", "#...#", "#...#"],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "P": ["####.", "#...#", "#...#", "####.", "#....", "#....", "#...."],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "S": [".####", "#....", "#....", ".###.", "....#", "....#", "####."],
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "U": ["#...#", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "V": ["#...#", "#...#", "#...#", "#...#", ".#.#.", ".#.#.", "..#.."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "Y": ["#...#", "#...#", ".#.#.", "..#..", "..#..", "..#..", "..#.."],
    " ": ["..", "..", "..", "..", "..", "..", ".."],
}


def pixel_text(text: str, colours: list[str], unit: int = 1) -> Image.Image:
    """Chunky lettering like the game logo: banded fill, bright top edge, ink outline, drop shadow."""
    cols = []
    for ch in text:
        g = np.array([[c == "#" for c in row] for row in PIXFONT[ch]])
        cols += [g, np.zeros((7, 1), bool)]
    glyphs = np.concatenate(cols, 1)
    glyphs = np.kron(glyphs, np.ones((unit, unit), bool))
    h, w = glyphs.shape
    mask = np.zeros((h + 5, w + 4), bool)
    mask[2:2 + h, 2:2 + w] = glyphs
    pal = np.array([hexc(c) for c in colours], np.float32)
    band = np.clip(((np.arange(mask.shape[0]) - 2) / max(1, h - 1) * len(pal)).astype(int), 0, len(pal) - 1)
    rgb = pal[band][:, None, :].repeat(mask.shape[1], 1)
    top = mask & ~np.roll(mask, 1, 0)
    rgb[top] = np.minimum(rgb[top] + 60, 255)
    ink = dilate(mask) & ~mask
    shadow = np.roll(mask | ink, 1, 0) & ~(mask | ink)
    out = np.zeros(mask.shape + (4,), np.uint8)
    out[mask, :3] = rgb[mask]
    out[mask, 3] = 255
    out[ink] = INK + (255,)
    out[shadow] = (5, 5, 10, 160)
    return Image.fromarray(out)


# where the land names go (art pixels), and city labels that must dodge a neighbour: (dx, dy, anchor)
LAND_LABEL = {"fire": (560, 58), "storm": (800, 130), "nature": (715, 478), "water": (585, 506),
              "earth": (262, 470), "void": (318, 112)}
CITY_LABEL = {8: (-10, 0, "rm"), 12: (-10, 0, "rm"), 19: (-10, 0, "rm"), 25: (-10, 0, "rm"),
              26: (-10, 0, "rm"), 27: (10, 0, "lm"), 6: (10, 0, "lm"), 3: (10, 0, "lm"), 2: (-10, 0, "rm"),
              21: (10, 0, "lm"), 23: (10, 0, "lm")}

GOLD = ["fff6d0", "ffe08a", "f2c14e", "d89a32", "a86a22"]


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "art" / "worldmap"))
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    rgb, info = paint_terrain(args.seed)
    nodes = stage_layout()

    # the Crack: a glowing fissure from deep in the Hollow Rift out to the Outer Hollow
    crack_pts = [pos(210, 0.66), pos(214, 0.78), pos(208, 0.9), pos(215, 1.02), (210, 150), (150, 110)]
    crack = Image.new("L", (W, H), 0)
    cd = ImageDraw.Draw(crack)
    jag = []
    for (x0, y0), (x1, y1) in zip(crack_pts, crack_pts[1:]):
        for k in range(6):
            t = k / 6
            jag.append((x0 + (x1 - x0) * t + rng.uniform(-3, 3), y0 + (y1 - y0) * t + rng.uniform(-3, 3)))
    jag.append(crack_pts[-1])
    cd.line(jag, fill=255, width=5)
    cm = np.asarray(crack) > 0
    rgb[dilate(cm, 2)] = rgb[dilate(cm, 2)] * 0.4 + np.array(hexc("7a3ad0")) * 0.6
    rgb[cm] = hexc("c79bff")
    core = Image.new("L", (W, H), 0)
    ImageDraw.Draw(core).line(jag, fill=255, width=2)
    rgb[np.asarray(core) > 0] = hexc("f4e8ff")

    board = Board(rgb)
    avoid: list[tuple[float, float, float]] = []
    glows: list[tuple[int, int, str, int]] = []

    # cities
    for num, (x, y) in nodes.items():
        if num == 27:
            im = solenne_sprite()
            board.put(im, x, y + 30, 3)
            avoid.append((x, y, 50))
            continue
        if num == 26:
            continue                     # the Lumen Gate is Solenne's outer wall
        land = stage_land(num)
        if num == 25:
            im = city_sprite(25, "storm", rng)   # a crossroads market town of tents and carts
        else:
            im = city_sprite(num, land, rng)
        if num % 4 == 0 and num <= 24 and num != 20:   # Grundhallow stays above its road
            # a capital stands beside its medallion, on the side away from the stage before it
            side = 1 if nodes[num - 1][0] < x else -1
            x, y = x + side * 30, y + 14
        board.put(im, x, y - 4, 2)
        avoid.append((x, y - 12, 18 if im.width < 40 else 26))

    # Nhal Vorath in the Outer Hollow
    nv = nhal_vorath_sprite()
    citadel_xy = (110, 178)
    board.put(nv, *citadel_xy, 0)

    # roads avoid scenery
    assault = [nodes[27], pos(200, 0.4), pos(210, 0.62), pos(212, 0.8), (215, 160), (170, 118), (124, 70)]
    for (x0, y0), (x1, y1) in zip(assault, assault[1:]):
        for t in np.linspace(0, 1, 8):
            avoid.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 4))
    for li in range(6):
        for k in range(4):
            x0, y0 = nodes[li * 4 + k + 1]
            x1, y1 = nodes[li * 4 + k + 2] if k < 3 else pos(ANGLE[LANDS[li]], 0.31)
            for t in np.linspace(0, 1, 7):
                avoid.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, 5))
    for a in range(0, 360, 5):
        avoid.append((*pos(a, 0.31), 5))

    scatter(board, info, rng, nodes, avoid)
    roads = roads_layer(nodes, assault)
    base_noroads = board.bake()

    # glows: lava, windows, the Heartstone, the black sun's corona
    river = info["river"]
    lava = info["is_land"] & (info["land_idx"] == 0) & ~info["heart"] & (np.abs(river - 0.5) < 0.006)
    ly, lx = np.nonzero(lava)
    for i in rng.permutation(len(lx))[:140]:
        glows.append((int(lx[i]), int(ly[i]), "ff6a1a", 9))
    for _, im, x0, y0, _ in board.items:
        a = np.asarray(im)
        bright = (a[..., 3] > 0) & (a[..., :3].max(-1) > 235) & (a[..., :3].min(-1) < 200)
        for yy, xx in zip(*np.nonzero(bright)):
            if rng.random() < 0.5:
                glows.append((x0 + int(xx), y0 + int(yy), "%02x%02x%02x" % tuple(a[yy, xx, :3]), 6))
    glows += [(int(CX), int(CY - 8), "fff2b8", 26), (int(CX + 13), int(CY - 40), "fff0a0", 14)]
    cy_ = np.nonzero(cm)
    for i in rng.permutation(len(cy_[0]))[:60]:
        glows.append((int(cy_[1][i]), int(cy_[0][i]), "9a5aff", 10))

    def finish(img: Image.Image) -> Image.Image:
        img = add_glow(img, glows)
        a = np.asarray(img).astype(np.float32)
        # vignette in four hard steps
        v = np.clip(1 - (np.maximum(np.abs(XX - W / 2) / (W / 2), np.abs(YY - H / 2) / (H / 2)) - 0.82) * 2.5, 0.6, 1)
        v = np.floor(v * 8) / 8
        a[..., :3] *= v[..., None]
        # bronze frame like the menu panel
        a[:3, :, :3] = a[-3:, :, :3] = a[:, :3, :3] = a[:, -3:, :3] = hexc("3b2a1a")
        a[1, 1:-1, :3] = a[-2, 1:-1, :3] = a[1:-1, 1, :3] = a[1:-1, -2, :3] = hexc("c9a35a")
        return Image.fromarray(a.astype(np.uint8))

    clean = finish(base_noroads)
    clean.convert("RGB").save(out / "world_map_base.png")
    clean.resize((W * SCALE, H * SCALE), Image.NEAREST).convert("RGB").save(out / "world_map_clean_2x.png")

    # roads under the sprites: re-bake with roads painted into the ground
    with_roads = Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8)).convert("RGBA")
    with_roads.alpha_composite(roads)
    board.base = with_roads
    nodes_img = board.bake()
    for num, (x, y) in nodes.items():
        acc = ACCENT[stage_land(num)]
        m = medallion(str(num), acc, big=num in (4, 8, 12, 16, 20, 24, 25, 26, 27))
        yy = y + (8 if num != 27 else 34)
        if num == 26:
            yy = y + 4
        nodes_img.alpha_composite(m, (int(x - m.width / 2), int(yy - m.height / 2)))
    a_rows = [".#.", "#.#", "###", "#.#", "#.#"]
    am = letter_medallion(a_rows, "d07cff")
    nodes_img.alpha_composite(am, (int(citadel_xy[0] - am.width / 2), 56))
    nodes_img = finish(nodes_img)
    nodes_2x = nodes_img.resize((W * SCALE, H * SCALE), Image.NEAREST)
    nodes_2x.convert("RGB").save(out / "world_map_nodes_2x.png")

    # labelled preview: pixel lettering for lands, a clean serif for cities (as the game UI would draw)
    lab = nodes_img.copy()
    for land, (x, y) in LAND_LABEL.items():
        ac = ACCENT[land]
        txt = pixel_text(LAND_NAME[land], ["ffffff", _lighten(ac), ac, _darken(ac, 0.8), _darken(ac, 0.6)], unit=2)
        lab.alpha_composite(txt, (int(x - txt.width / 2), int(y - txt.height / 2)))
    title = pixel_text("ORRHEN", GOLD, unit=3)
    lab.alpha_composite(title, (W - title.width - 24, 18))
    sub = pixel_text("THE CAMPAIGN", ["fff6d0", "efd58e", "c9a35a", "9a6e38", "6b4a28"])
    lab.alpha_composite(sub, (W - title.width // 2 - 24 - sub.width // 2, 18 + title.height + 2))
    t3 = pixel_text("NHAL VORATH", ["f0d8ff", "d0a8ff", "b27cff", "8a4ad8", "6a2ab0"])
    lab.alpha_composite(t3, (citadel_xy[0] - t3.width // 2, citadel_xy[0] + 76))
    big = lab.resize((W * SCALE, H * SCALE), Image.NEAREST)
    d = ImageDraw.Draw(big)
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 15)
    small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 13)
    for num, (x, y) in nodes.items():
        name = STAGES[num][1]
        dx, dy, anchor = CITY_LABEL.get(num, (0, 17, "mt"))
        my = y + (8 if num != 27 else 34) + (-4 if num == 26 else 0)
        colour = (255, 242, 184) if num >= 25 else (255, 246, 224)
        d.text(((x + dx) * SCALE, (my + dy) * SCALE), name, font=font, anchor=anchor,
               fill=colour, stroke_width=3, stroke_fill=INK)
    d.text(((citadel_xy[0]) * SCALE, (citadel_xy[0] + 92) * SCALE), "The final assault", font=small,
           anchor="mt", fill=(240, 216, 255), stroke_width=3, stroke_fill=INK)
    cx_, cy_ = pos(214, 1.03)
    d.text((cx_ * SCALE + 30, cy_ * SCALE + 10), "the Crack", font=small, anchor="lm",
           fill=(220, 190, 255), stroke_width=3, stroke_fill=INK)
    big.convert("RGB").save(out / "world_map_labelled.png")

    data = {
        "size": [W, H], "scale": SCALE,
        "stages": [{"stage": n, "name": STAGES[n][0], "city": STAGES[n][1], "land": stage_land(n),
                    "x": round(nodes[n][0], 1), "y": round(nodes[n][1], 1)} for n in sorted(nodes)],
        "assault": {"name": "Nhal Vorath, the Crownless Citadel", "x": citadel_xy[0], "y": 65,
                    "route": [[round(x, 1), round(y, 1)] for x, y in assault]},
    }
    (out / "world_map_nodes.json").write_text(json.dumps(data, indent=1))
    print("wrote", out)


if __name__ == "__main__":
    main()
