#!/usr/bin/env python3
"""Size line-up: every boss's idle sprite standing on a board grid next to a hero, at true sprite scale.

Writes art/story/boss_scale.png. One board cell = 40 sprite px (a hero, about 60 px, stands 1.5 cells tall).
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cast import BOSS_SIZE, CAST, HERO_PX  # noqa: E402

CH = os.path.join("art", "story", "characters")
CELL = 40
ROWS = [
    ["tamsin", "herald_ourra", "herald_gorrath", "herald_vesper", "herald_ashwick", "herald_vholt", "herald_briar",
     "cassivane_ashen"],
    ["tamsin", "cinder_tyrant", "thunderhead", "elder_broodmother", "tidal_leviathan", "mountain_titan", "hollow_king"],
    ["tamsin", "sundered_heart", "gatemaw", "vael_orrun"],
]


def crop(cid):
    im = Image.open(os.path.join(CH, cid, "idle_0.png")).convert("RGBA")
    a = np.asarray(im)[..., 3] > 0
    ys, xs = np.where(a)
    return im.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))


def main():
    f = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf", 12)
    fb = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 20)
    rows = [[(cid, crop(cid)) for cid in r] for r in ROWS]
    W = max(sum(max(im.width, 118) + 24 for _, im in r) for r in rows) + 60
    heights = [max(im.height for _, im in r) + 70 for r in rows]
    H = sum(heights) + 60
    W = (W // CELL + 1) * CELL
    sheet = Image.new("RGB", (W, H), (46, 58, 40))
    d = ImageDraw.Draw(sheet)
    for x in range(0, W, CELL):  # board grid
        d.line((x, 0, x, H), fill=(54, 68, 47))
    for y in range(0, H, CELL):
        d.line((0, y, W, y), fill=(54, 68, 47))
    d.text((16, 12), "Boss sizes on the board (1 square = 1 cell; the hero on the left of each row is Tamsin)",
           font=fb, fill=(240, 232, 210))
    y = 60
    for r, hgt in zip(rows, heights):
        ground = y + hgt - 30
        x = 30
        for cid, im in r:
            sheet.paste(im, (x, ground - im.height), im)
            cells = im.height / CELL
            label = CAST[cid]["title"].split(",")[0].replace("The ", "")
            d.text((x, ground + 4), f"{label}", font=f, fill=(240, 232, 210))
            d.text((x, ground + 17), f"{cells:.1f} cells tall", font=f, fill=(200, 210, 190))
            x += max(im.width, 118) + 24
        y += hgt
    out = os.path.join("art", "story", "boss_scale.png")
    sheet.save(out)
    print(out, sheet.size)


if __name__ == "__main__":
    main()
