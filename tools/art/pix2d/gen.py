#!/usr/bin/env python3
"""Draw the 2D pixel-art test creatures. usage: python3 tools/art/pix2d/gen.py [names] --out DIR"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image
import creatures
import bosses  # noqa: F401  (adds the bosses to creatures.CREATURES)
import wardens  # noqa: F401
import final_bosses  # noqa: F401

ap = argparse.ArgumentParser()
ap.add_argument("names", nargs="*")
ap.add_argument("--out", default=os.path.join("art", "pix2d"))
ap.add_argument("--zoom", type=int, default=8)
a = ap.parse_args()
os.makedirs(a.out, exist_ok=True)
for n in a.names or list(creatures.CREATURES):
    s = creatures.CREATURES[n]()
    im = s.image()
    im.save(os.path.join(a.out, n + ".png"))
    s.normal_image().save(os.path.join(a.out, n + "_n.png"))
    big = Image.new("RGBA", (im.width * a.zoom, im.height * a.zoom), (58, 76, 52, 255))
    big.alpha_composite(im.resize(big.size, Image.NEAREST))
    big.save(os.path.join(a.out, n + "_big.png"))
    print(n, im.size)
