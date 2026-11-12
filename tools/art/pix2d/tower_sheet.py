#!/usr/bin/env python3
"""Preview towers: python3 tools/art/pix2d/tower_sheet.py [names] --out FILE [--zoom 4] [--old]

--old puts the current in-game sprite (assets/art/game/towers/<id>.png) to the left of each new one.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402

import towers  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("names", nargs="*")
ap.add_argument("--out", default="/tmp/tower_sheet.png")
ap.add_argument("--zoom", type=int, default=4)
ap.add_argument("--old", action="store_true")
ap.add_argument("--bg", default="3a4c34")
a = ap.parse_args()
names = a.names or list(towers.TOWERS)
cells = []
for n in names:
    s, _ = towers.TOWERS[n]()
    pair = []
    if a.old:
        p = os.path.join("assets", "art", "game", "towers", n + ".png")
        if os.path.exists(p):
            pair.append(Image.open(p).convert("RGBA"))
    pair.append(s.image())
    cells.append((n, pair))
cw = max(sum(im.width + 6 for im in pair) for _, pair in cells)
ch = max(im.height for _, pair in cells for im in pair) + 10
cols = min(len(cells), 6)
rows = (len(cells) + cols - 1) // cols
bg = tuple(int(a.bg[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
sheet = Image.new("RGBA", (cols * cw, rows * ch), bg)
for k, (n, pair) in enumerate(cells):
    x, y = (k % cols) * cw, (k // cols) * ch
    for im in pair:
        sheet.alpha_composite(im, (x, y + ch - 10 - im.height))
        x += im.width + 6
sheet = sheet.resize((sheet.width * a.zoom, sheet.height * a.zoom), Image.NEAREST)
d = ImageDraw.Draw(sheet)
for k, (n, _) in enumerate(cells):
    d.text(((k % cols) * cw * a.zoom + 4, ((k // cols) * ch + ch - 9) * a.zoom), n, fill=(230, 220, 200))
sheet.save(a.out)
print(a.out, sheet.size)
