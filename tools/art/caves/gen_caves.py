#!/usr/bin/env python3
"""Draws the enemy caves that break open during a run (see scripts/sim/caves.gd).

usage: python3 tools/art/caves/gen_caves.py [--out DIR] [--sheet FILE]

A cave is a heap of split, chiselled rock thrown up out of the ground around a black maw: fangs of stone
hang over the mouth, bones lie in the churned earth before it and eyes burn in the dark inside. There is
one look per biome (the rock, its moss, snow, lava or rift light). Drawn with the hand-drawn pixel-art kit
(tools/art/pix2d/kit.py): light from the upper left, hue-shifted ramps, ink outlines and a normal map for the
game's 2D lights.

Writes assets/art/game/caves/:
  cave_<biome>.png, _n.png, _glow.png   the cave, its feet on the bottom row, its mouth at "mouth"
  rubble_<biome>.png                    churned earth and thrown rock that goes on the ground under it
  dig_<biome>.png                       a tile of freshly dug road; the game paints the cave's dig with it
  caves.json                            sizes and points (mouth, eyes) per piece, and the dig's edge colour
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pix2d"))
from kit import INK, Sprite, hexc, ramp  # noqa: E402

OUT = os.path.join("assets", "art", "game", "caves")

W, H = 96, 74
# The mouth's centre line and the row its floor meets the ground.
MOUTH_X, MOUTH_FLOOR = 48, 62

BONE = ramp("d8ccae", spread=0.5)
DARK = (10, 7, 10)

# The rock of each biome, its dirt (the biome's road), the accent and the light deep in the maw.
BIOMES = {
    "meadow": dict(rock=ramp("6e6a66", spread=0.55), rock_dark=ramp("4a4648", spread=0.45),
                   dirt=["5a4630", "6a5238", "7a6040", "8c7050", "9c8060"], edge="3e2e20",
                   accent="moss", eyes=(255, 70, 40), deep=(150, 40, 20)),
    "fire": dict(rock=ramp("3e3436", spread=0.5), rock_dark=ramp("262022", spread=0.4),
                 dirt=["3c3332", "4a403c", "5a4d46", "6a5a50", "7a685a"], edge="1c1414",
                 accent="lava", eyes=(255, 150, 40), deep=(255, 90, 20)),
    "storm": dict(rock=ramp("5a626e", spread=0.55), rock_dark=ramp("3a404a", spread=0.45),
                  dirt=["373d46", "454c56", "545c66", "656e78", "79828c"], edge="262b32",
                  accent="lichen", eyes=(170, 220, 255), deep=(80, 140, 255)),
    "nature": dict(rock=ramp("566050", spread=0.55), rock_dark=ramp("343a30", spread=0.45),
                   dirt=["3a2a1c", "4a3624", "5a442c", "6a5234", "7a6040"], edge="2a1e14",
                   accent="roots", eyes=(200, 255, 90), deep=(90, 160, 30)),
    "water": dict(rock=ramp("6a7a8c", spread=0.55), rock_dark=ramp("44505e", spread=0.45),
                  dirt=["4a6a88", "5a7c9a", "6e92ae", "88aac2", "a8c6d8"], edge="33495e",
                  accent="snow", eyes=(140, 230, 255), deep=(60, 160, 230)),
    "earth": dict(rock=ramp("9a5a3a", spread=0.55), rock_dark=ramp("6a3a26", spread=0.45),
                  dirt=["9a7a54", "aa8a60", "ba9a6e", "c8aa7c", "d6ba8c"], edge="6a4a30",
                  accent="strata", eyes=(255, 120, 50), deep=(200, 70, 20)),
    "void": dict(rock=ramp("2e2838", spread=0.5), rock_dark=ramp("1c1824", spread=0.4),
                 dirt=["121016", "1a1620", "221e2a", "2c2636", "383044"], edge="0a080e",
                 accent="rift", eyes=(150, 255, 240), deep=(160, 90, 255)),
    "heart": dict(rock=ramp("a29a8a", spread=0.5), rock_dark=ramp("7a7262", spread=0.45),
                  dirt=["7a6238", "907444", "a88850", "bea060", "d4b874"], edge="4e3e22",
                  accent="gold", eyes=(255, 200, 80), deep=(255, 150, 40)),
}


def facet_rock(s: Sprite, pts, tones, rng, split=True) -> np.ndarray:
    """A chiselled boulder: a polygon cut into flat faces, lit from the upper left."""
    mask = s.poly(pts)
    if not mask.any():
        return mask
    s.part(mask, tones, bulge=0.35, flat=False)
    if split:
        ys, xs = np.nonzero(mask)
        cx, cy = xs.mean(), ys.min() + (ys.max() - ys.min()) * 0.35
        # A ridge from the top down to the lower right splits a lit face from a shadowed one.
        ang = rng.uniform(0.9, 1.4)
        dx, dy = math.cos(ang), math.sin(ang)
        side = (s.xs + 0.5 - cx) * dy - (s.ys + 0.5 - cy) * dx
        shade = mask & (side < 0)
        # One tone darker on the shadowed face.
        for i in range(1, len(tones)):
            m = shade & np.all(s.rgb == tones[i], axis=-1)
            s.rgb[m] = tones[i - 1]
        lit_top = mask & (s.ys < ys.min() + 2.5)
        s.rgb[lit_top] = tones[-1]
        # A crack or two.
        for _ in range(rng.integers(1, 3)):
            x0 = int(rng.uniform(xs.min() + 2, xs.max() - 2))
            y0 = int(rng.uniform(ys.min() + 2, ys.max() - 3))
            x, y = x0, y0
            for _ in range(int(rng.integers(3, 7))):
                if 0 <= y < s.h and 0 <= x < s.w and mask[y, x]:
                    s.rgb[y, x] = tones[0]
                x += int(rng.choice([-1, 0, 1]))
                y += 1
    return mask


def cave(biome: str) -> tuple[Sprite, dict]:
    b = BIOMES[biome]
    rock, rock_d = b["rock"], b["rock_dark"]
    rng = np.random.default_rng(sum(map(ord, biome)) * 7 + 3)
    s = Sprite(W, H)
    mx, fl = MOUTH_X, MOUTH_FLOOR
    # The back of the heap: big slabs heaved up behind the maw, highest in the middle.
    back = [
        [(14, 58), (10, 44), (20, 30), (30, 34), (34, 52)],
        [(28, 46), (30, 22), (40, 10), (50, 14), (52, 30), (44, 44)],
        [(46, 30), (52, 12), (62, 8), (70, 22), (66, 44)],
        [(62, 50), (66, 30), (78, 26), (86, 42), (84, 58)],
    ]
    for pts in back:
        jitter = [(x + rng.uniform(-1.5, 1.5), y + rng.uniform(-1.5, 1.5)) for x, y in pts]
        facet_rock(s, jitter, rock_d if pts is back[0] or pts is back[3] else rock, rng)
    # The maw: a black arch with a lip of lit stone around it.
    arch = [(mx - 15, fl), (mx - 15, fl - 12), (mx - 11, fl - 22), (mx - 4, fl - 27), (mx + 4, fl - 27),
            (mx + 11, fl - 22), (mx + 15, fl - 12), (mx + 15, fl)]
    lip = [(x + (3 if x > mx else -3 if x < mx else 0) + rng.uniform(-1.4, 1.4),
            y - (3 if y < fl - 5 else 0) + rng.uniform(-1.4, 1.4)) for x, y in arch]
    facet_rock(s, lip, rock_d, rng, split=False)
    maw = s.poly(arch)
    yy = s.ys + 0.5
    depth = np.clip((yy - (fl - 27)) / 27.0, 0, 1)
    s.fill(maw, DARK)
    inner = maw & s.poly([(mx - 10, fl), (mx - 9, fl - 16), (mx - 3, fl - 22), (mx + 3, fl - 22), (mx + 9, fl - 16),
                          (mx + 10, fl)])
    deep = np.array(b["deep"], np.float64)
    # A faint light far down the throat, warmest at the floor.
    for y in range(s.h):
        row = inner[y]
        if row.any():
            t = float(depth[y, 0]) ** 2.2 * 0.38
            s.rgb[y][row] = np.clip(np.array(DARK) * (1 - t) + deep * t, 0, 255).astype(np.uint8)
    s.nrm[maw] = (0.0, 0.0, 1.0)
    # Fangs of stone over the mouth and from its floor.
    for fx, flen in ((mx - 9, 7), (mx - 4, 10), (mx + 1, 6), (mx + 6, 9), (mx + 10, 5)):
        top = fl - 24 + abs(fx - mx) * 0.35
        s.part(s.poly([(fx - 2, top), (fx + 2, top), (fx, top + flen)]), rock, bulge=0.4)
    for fx, flen in ((mx - 11, 6), (mx - 6, 4), (mx + 8, 5), (mx + 12, 7)):
        s.part(s.poly([(fx - 2, fl + 1), (fx + 2, fl + 1), (fx + 0.5, fl + 1 - flen)]), rock_d, bulge=0.4)
    # Eyes in the dark.
    eyes = []
    for ex, ey in ((mx - 5, fl - 11), (mx + 4, fl - 15), (mx - 1, fl - 6)):
        ex, ey = int(ex + rng.integers(-1, 2)), int(ey)
        for dx in (0, 3):
            s.px(ex + dx, ey, b["eyes"], glow=True)
        eyes.append([ex + 1.5, ey])
    # Front rocks either side of the maw, lower and nearer.
    front = [
        [(4, 70), (6, 58), (16, 52), (26, 56), (30, 70)],
        [(20, 72), (24, 62), (32, 58), (36, 72)],
        [(66, 72), (64, 60), (72, 56), (78, 62), (80, 72)],
        [(74, 70), (78, 56), (88, 54), (94, 64), (92, 72)],
    ]
    for pts in front:
        jitter = [(x + rng.uniform(-1.2, 1.2), y + rng.uniform(-1.2, 1.2)) for x, y in pts]
        facet_rock(s, jitter, rock, rng)
    # Bones before the mouth: a skull and a few long bones.
    s.part(s.ellipse(mx + 18.5, fl + 7, 3.0, 2.4), BONE, bulge=0.8)
    s.px(mx + 17, fl + 7, INK)
    s.px(mx + 19, fl + 7, INK)
    s.line(mx - 22, fl + 8, mx - 15, fl + 6, BONE[3])
    s.line(mx - 20, fl + 10, mx - 14, fl + 10, BONE[2])
    s.line(mx + 22, fl + 9, mx + 27, fl + 11, BONE[2])
    _accent(s, biome, b, rng)
    s.ink()
    return s, {"mouth": [mx, fl - 4], "eyes": eyes, "foot": [mx, fl + 6], "glow_color": list(b["deep"])}


def _accent(s: Sprite, biome: str, b: dict, rng) -> None:
    """What makes each land's cave its own: moss, snow, lava cracks, rift light, roots, gold."""
    kind = b["accent"]
    top = np.zeros_like(s.a)
    # The top two rows of every rock face.
    a = s.a.copy()
    top[1:] = a[1:] & ~a[:-1]
    top2 = top.copy()
    top2[1:] |= top[:-1] & a[1:]
    maw_free = ~((np.abs(s.xs - MOUTH_X) < 15) & (s.ys > MOUTH_FLOOR - 28))
    if kind == "snow":
        s.fill(top2 & maw_free, (236, 244, 250))
        s.fill(top & maw_free, (255, 255, 255))
    elif kind in ("moss", "lichen", "roots"):
        col = {"moss": [(74, 104, 50), (104, 138, 64)], "lichen": [(150, 160, 120), (190, 196, 150)],
               "roots": [(60, 92, 40), (96, 140, 52)]}[kind]
        pick = top2 & maw_free & (rng.random(s.a.shape) < 0.55)
        s.fill(pick, col[0])
        s.fill(pick & top, col[1])
        if kind == "roots":
            for _ in range(5):
                x = int(rng.integers(12, 84))
                y0 = int(np.argmax(s.a[:, x])) if s.a[:, x].any() else 40
                for k in range(int(rng.integers(4, 9))):
                    s.px(x + (k // 3) * int(rng.choice([-1, 1])), y0 + k, (58, 40, 26))
    elif kind in ("lava", "rift", "gold"):
        col = {"lava": (255, 120, 30), "rift": (170, 110, 255), "gold": (240, 200, 90)}[kind]
        glow = kind != "gold"
        for _ in range(9):
            x, y = int(rng.integers(10, 86)), int(rng.integers(14, 66))
            for k in range(int(rng.integers(3, 8))):
                if 0 <= y < s.h and 0 <= x < s.w and s.a[y, x] and maw_free[y, x]:
                    s.px(x, y, col, glow=glow)
                x += int(rng.choice([-1, 0, 1]))
                y += 1
        if kind == "rift":
            for cx, cy in ((22, 36), (76, 34)):
                s.part(s.poly([(cx - 2, cy + 6), (cx, cy - 4), (cx + 2, cy + 6)]), ramp("8a5ad8", spread=0.6), glow=True)
    elif kind == "strata":
        for y in range(10, 70, 5):
            band = s.a & (s.ys == y) & maw_free & (rng.random(s.a.shape) < 0.8)
            s.rgb[band] = (s.rgb[band] * 0.78).astype(np.uint8)


def rubble(biome: str) -> Image.Image:
    """Ground under the cave: a fan of churned earth and thrown stones, widest before the mouth."""
    b = BIOMES[biome]
    rng = np.random.default_rng(sum(map(ord, biome)) + 91)
    w, h = 112, 64
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float64)
    ang = np.arctan2(ys - h * 0.5, xs - w * 0.5)
    ragged = 1.0 + 0.1 * np.sin(ang * 6 + rng.uniform(0, 6)) + 0.07 * np.sin(ang * 11 + rng.uniform(0, 6))
    d = np.hypot((xs - w * 0.5) / (w * 0.5), (ys - h * 0.5) / (h * 0.5)) / ragged
    dirt = [hexc(c) for c in b["dirt"]]
    noise = rng.random((h, w))
    t = np.clip(1.0 - d + (noise - 0.5) * 0.5, 0, 0.999)
    idx = np.clip((t * len(dirt)).astype(int), 0, len(dirt) - 1)
    rgb = np.array(dirt, np.uint8)[idx]
    alpha = np.where(d < 0.86, 255, np.where(d < 1.0, np.where(noise < (1.0 - d) / 0.14, 255, 0), 0)).astype(np.uint8)
    rgb[(d >= 0.8) & (d < 0.86)] = hexc(b["edge"])
    img = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
    draw = ImageDraw.Draw(img)
    rock = b["rock"]
    for _ in range(26):
        x, y = rng.uniform(6, w - 6), rng.uniform(6, h - 6)
        if math.hypot((x - w * 0.5) / (w * 0.5), (y - h * 0.5) / (h * 0.5)) > 0.85:
            continue
        r = rng.uniform(0.8, 2.2)
        draw.ellipse([x - r, y - r * 0.8, x + r, y + r * 0.8], fill=rock[int(rng.integers(1, 4))] + (255,))
        draw.point([(x - r * 0.4, y - r * 0.4)], fill=rock[4] + (255,))
    return img


def dig_tile(biome: str) -> Image.Image:
    """A 64 x 64 tile of freshly dug road in the biome's dirt, a little darker and rougher than the road."""
    b = BIOMES[biome]
    rng = np.random.default_rng(sum(map(ord, biome)) + 5)
    n = 64
    dirt = [hexc(c) for c in b["dirt"]]
    # Tileable noise: a sum of whole-period sines.
    ys, xs = np.mgrid[0:n, 0:n].astype(np.float64) / n * math.tau
    f = np.zeros((n, n))
    for k in range(6):
        fx, fy = int(rng.integers(1, 5)), int(rng.integers(1, 5))
        f += np.sin(xs * fx + rng.uniform(0, 6)) * np.sin(ys * fy + rng.uniform(0, 6)) / (1 + k * 0.4)
    f = (f - f.min()) / (np.ptp(f) or 1)
    t = np.clip(f * 0.75 + rng.random((n, n)) * 0.3 - 0.1, 0, 0.999)
    idx = np.clip((t * (len(dirt) - 1)).astype(int), 0, len(dirt) - 2)
    rgb = np.array(dirt, np.uint8)[idx]
    rock = b["rock"]
    for _ in range(14):
        x, y = int(rng.integers(0, n - 2)), int(rng.integers(0, n - 2))
        rgb[y, x] = rock[3]
        rgb[y, x + 1] = rock[2]
        rgb[y + 1, x] = rock[1]
    return Image.fromarray(np.dstack([rgb, np.full((n, n), 255, np.uint8)]), "RGBA")


def glow_image(s: Sprite) -> Image.Image | None:
    if not s.glow.any():
        return None
    al = (s.glow & s.a).astype(np.uint8) * 255
    return Image.fromarray(np.dstack([s.rgb, al]), "RGBA")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet", default="", help="also write a labelled review sheet here")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    info: dict = {}
    sheet = []
    for biome in BIOMES:
        s, meta = cave(biome)
        im = s.image()
        im.save(os.path.join(a.out, f"cave_{biome}.png"))
        s.normal_image().save(os.path.join(a.out, f"cave_{biome}_n.png"))
        g = glow_image(s)
        if g is not None:
            g.save(os.path.join(a.out, f"cave_{biome}_glow.png"))
        info[f"cave_{biome}"] = {"size": [im.width, im.height], **meta}
        r = rubble(biome)
        r.save(os.path.join(a.out, f"rubble_{biome}.png"))
        info[f"rubble_{biome}"] = {"size": [r.width, r.height]}
        t = dig_tile(biome)
        t.save(os.path.join(a.out, f"dig_{biome}.png"))
        info[f"dig_{biome}"] = {"size": [t.width, t.height], "edge": list(hexc(BIOMES[biome]["edge"]))}
        sheet.append((biome, im, r, t))
    with open(os.path.join(a.out, "caves.json"), "w") as fh:
        json.dump({"biomes": list(BIOMES), "pieces": info}, fh, indent=1, sort_keys=True)
    print(f"{len(info)} pieces -> {a.out}")
    if a.sheet:
        write_sheet(sheet, a.sheet)


def write_sheet(items, path, zoom=4):
    """Each biome's cave standing on its rubble on a patch of dug road, side by side."""
    cell = (120, 96)
    sheet = Image.new("RGBA", (cell[0] * 4, cell[1] * 2), (34, 38, 30, 255))
    for i, (biome, cave_im, rub, tile) in enumerate(items):
        ox, oy = (i % 4) * cell[0], (i // 4) * cell[1]
        sheet.paste(tile.crop((0, 0, 30, 30)), (ox + 45, oy + 70))
        sheet.alpha_composite(rub, (ox + 4, oy + 40))
        sheet.alpha_composite(cave_im, (ox + 12, oy + 6))
    sheet = sheet.resize((sheet.width * zoom, sheet.height * zoom), Image.NEAREST)
    sheet.save(path)


if __name__ == "__main__":
    main()
