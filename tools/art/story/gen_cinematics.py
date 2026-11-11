#!/usr/bin/env python3
"""Paints the cinematic stills (640x360 pixel art), one per shot, for review.

Writes art/story/cinematics/<cinematic_id>/<NN>.png plus contact.png (all shots on one sheet).
The in-game cinematic player reads assets/story/images/<cinematic_id>/<NN>.png; copy there once approved.

Run from the repository root:  python3 tools/art/story/gen_cinematics.py [cinematic_id] [--shots 1,5]
"""
from __future__ import annotations

import argparse
import importlib
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

OUT = os.path.join("art", "story", "cinematics")
MODULES = {"prologue": "shots_prologue", "night_of_falling_stars": "shots_midpoint",
           "dawn": "shots_dawn", "heart_falls": "shots_heart_falls"}


def contact(folder, n):
    ims = [Image.open(os.path.join(folder, f"{i:02d}.png")) for i in range(1, n + 1)
           if os.path.exists(os.path.join(folder, f"{i:02d}.png"))]
    cols = 3
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * 324, rows * 184), (16, 14, 20))
    for k, im in enumerate(ims):
        sheet.paste(im.resize((320, 180), Image.NEAREST), ((k % cols) * 324 + 2, (k // cols) * 184 + 2))
    sheet.save(os.path.join(folder, "contact.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--shots", default="")
    args = ap.parse_args()
    for cid in args.ids or list(MODULES):
        mod = importlib.import_module(MODULES[cid])
        folder = os.path.join(OUT, cid)
        os.makedirs(folder, exist_ok=True)
        want = {int(s) for s in args.shots.split(",") if s}
        for i, fn in enumerate(mod.SHOTS, 1):
            if want and i not in want:
                continue
            img = fn()
            Image.fromarray(np.asarray(img)).save(os.path.join(folder, f"{i:02d}.png"))
            print(cid, i)
        contact(folder, len(mod.SHOTS))


if __name__ == "__main__":
    main()
