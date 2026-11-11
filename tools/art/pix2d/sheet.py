#!/usr/bin/env python3
"""A labelled review sheet: rest poses side by side on grass, feet on one line, the footman first for scale.

usage: python3 tools/art/pix2d/sheet.py name[=Label] ... --out sheet.png [--zoom 3] [--no-scale]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import creatures  # noqa: E402
import bosses  # noqa: E402,F401
import wardens  # noqa: E402,F401
import final_bosses  # noqa: E402,F401
import people  # noqa: E402,F401

FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
GRASS = (58, 76, 52, 255)


def crop(im):
    box = im.getbbox() or (0, 0, 1, 1)
    return im.crop(box), box


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="+")
    ap.add_argument("--out", required=True)
    ap.add_argument("--zoom", type=int, default=3)
    ap.add_argument("--no-scale", action="store_true")
    a = ap.parse_args()
    items = [] if a.no_scale else [("soldier", "footman")]
    for n in a.names:
        name, _, label = n.partition("=")
        items.append((name, label or name.replace("_", " ")))
    cells = []
    for name, label in items:
        s = creatures.CREATURES[name]()
        im = s.image()
        feet = s.bh - 4 + s.pad                # canvas row of the feet line
        c, box = crop(im)
        cells.append((c, feet - box[1], label))
    gap, top, base = 14, 10, 22
    above = max(f for _, f, _ in cells)
    below = max(c.height - f for c, f, _ in cells)
    W = sum(c.width for c, _, _ in cells) + gap * (len(cells) + 1)
    H = top + above + below + base
    sheet = Image.new("RGBA", (W, H), GRASS)
    x = gap
    feet_y = top + above
    for c, f, _ in cells:
        sheet.alpha_composite(c, (x, feet_y - f))
        x += c.width + gap
    big = sheet.resize((W * a.zoom, H * a.zoom), Image.NEAREST)
    d = ImageDraw.Draw(big)
    font = ImageFont.truetype(FONT, 6 * a.zoom)
    x = gap
    for c, _, label in cells:
        cx = (x + c.width / 2) * a.zoom
        tw = d.textlength(label, font=font)
        d.text((cx - tw / 2, (H - base + 8) * a.zoom), label, font=font, fill=(236, 226, 196))
        x += c.width + gap
    big.convert("RGB").save(a.out)
    print(a.out, big.size)


if __name__ == "__main__":
    main()
