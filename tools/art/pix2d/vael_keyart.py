#!/usr/bin/env python3
"""Key-art still of Vael-Orrun, the Ascendant, hanging over the Crownless Citadel against a burning sky (design only).

usage: python3 tools/art/pix2d/vael_keyart.py OUT.png [--zoom 2]
Painted at 400x560 in whole pixels: a dithered red sky, a vast pale sun low behind him, black gothic spires and a
balustrade in silhouette, embers, and the vael_ascend sprite pasted at 1x.
"""
import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402

import vael_ascend  # noqa: E402

W, H = 400, 560
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def lerp(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("out")
    ap.add_argument("--zoom", type=int, default=2)
    a = ap.parse_args()
    ys, xs = np.mgrid[0:H, 0:W]
    sx, sy, R = 200, 230, 108
    d = np.hypot(xs - sx, ys - sy)
    # sky: dithered bands of red, hotter toward the sun
    bands = [(22, 4, 6), (52, 8, 8), (92, 16, 10), (140, 34, 14), (190, 62, 22), (230, 110, 40)]
    t = np.clip(1 - (d - R) / 300, 0, 1) * (len(bands) - 1)
    t = t + (BAYER[ys % 4, xs % 4] - 0.5)
    idx = np.clip(t.round().astype(int), 0, len(bands) - 1)
    img = np.array(bands, np.uint8)[idx]
    # the sun: pale and huge, mottled, with a burning rim
    disc = d <= R
    tone = np.clip(0.55 + 0.45 * (1 - d / R) + 0.12 * np.sin(xs * 0.11 + ys * 0.07) * np.cos(ys * 0.13), 0, 1)
    tone = tone + (BAYER[ys % 4, xs % 4] - 0.5) * 0.18
    pal = [(232, 150, 96), (246, 190, 132), (252, 220, 170), (255, 238, 204)]
    sidx = np.clip((tone * len(pal)).astype(int), 0, len(pal) - 1)
    img[disc] = np.array(pal, np.uint8)[sidx][disc]
    rng = np.random.default_rng(4)
    for _ in range(26):                                                        # craters
        cx, cy, r = rng.uniform(sx - R, sx + R), rng.uniform(sy - R, sy + R), rng.uniform(3, 12)
        m = (np.hypot(xs - cx, ys - cy) <= r) & disc
        img[m] = (img[m] * 0.93).astype(np.uint8)
    img[(d > R) & (d <= R + 2)] = (255, 200, 120)
    im = Image.fromarray(img).convert("RGBA")
    dr = ImageDraw.Draw(im)
    # gothic spires and buttresses in silhouette
    dark, dark2 = (20, 6, 8), (44, 12, 12)

    def spire(x, base, w, h, col):
        dr.polygon([(x - w, base), (x - w, base - h * 0.6), (x - w * 0.6, base - h * 0.75), (x, base - h), (x + w * 0.6, base - h * 0.75),
                    (x + w, base - h * 0.6), (x + w, base)], fill=col)
        for k in range(int(h * 0.6 // 18)):                                    # crockets up the edges
            yy = base - h * 0.6 + k * 18
            dr.polygon([(x - w - 3, yy), (x - w, yy - 6), (x - w, yy)], fill=col)
            dr.polygon([(x + w + 3, yy), (x + w, yy - 6), (x + w, yy)], fill=col)
        for k in range(3):                                                      # lit lancet windows
            wy = base - h * 0.5 + k * 30
            dr.rectangle([x - 2, wy, x + 2, wy + 12], fill=(120, 30, 14) if col == dark2 else (70, 16, 10))
    for x, w, h in ((60, 14, 330), (110, 9, 250), (300, 10, 270), (352, 16, 360)):
        spire(x, H, w, h, dark2)
    for x, w, h in ((18, 22, 470), (384, 24, 500)):
        spire(x, H, w, h, dark)
    dr.rectangle([0, 470, W, H], fill=dark)                                    # the balustrade: a row of pointed arches
    for x in range(6, W, 24):
        dr.polygon([(x, 504), (x, 486), (x + 3, 480), (x + 7, 476), (x + 11, 480), (x + 14, 486), (x + 14, 504)], fill=(96, 24, 12))
        dr.polygon([(x + 2, 504), (x + 2, 487), (x + 7, 480), (x + 12, 487), (x + 12, 504)], fill=(130, 36, 14))
        dr.line([(x + 7, 482), (x + 7, 504)], fill=dark)
    dr.rectangle([0, 466, W, 472], fill=(60, 16, 12))
    dr.rectangle([0, 504, W, 510], fill=(46, 12, 10))
    # embers drifting up
    for _ in range(160):
        x, y = rng.uniform(0, W), rng.uniform(0, H)
        im.putpixel((int(x), int(y)), [(255, 180, 70, 255), (255, 120, 40, 255), (255, 230, 150, 255)][int(rng.integers(3))])
    # him
    spr = vael_ascend.vael_ascend().image()
    im.alpha_composite(spr, ((W - spr.width) // 2, 34))
    im = im.convert("RGB").resize((W * a.zoom, H * a.zoom), Image.NEAREST)
    im.save(a.out)
    print(a.out, im.size)


if __name__ == "__main__":
    main()
