#!/usr/bin/env python3
"""Stand-in art for Vael-Orrun's second and third forms, until the boss art is drawn.

usage: python3 tools/art/citadel/gen_vael_forms.py

Makes recoloured copies of the High King's hand-drawn strips in assets/art/game/drawn/ and adds them
to drawn.json: the Sunderer burns a deep blood red with a violet edge, the Unmade is drained to ash
and void. The real forms come from the boss redraw; this only keeps the boss visible as it changes.
Run tools/art/gen_game_art.py --enemies afterwards to cut the frames.
"""
import json
import os

import numpy as np
from PIL import Image

DRAWN = os.path.join("assets", "art", "game", "drawn")
SOURCE = "vael_orrun"
FORMS = {
    # (multiply rgb, add rgb, desaturate 0..1)
    "vael_orrun_wrath": ((1.25, 0.55, 0.7), (18, 0, 10), 0.35),
    "vael_orrun_unmade": ((0.7, 0.6, 1.05), (8, 0, 26), 0.8),
}


def recolour(im: Image.Image, mul, add, grey) -> Image.Image:
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    rgb = a[..., :3]
    lum = rgb @ np.array([0.3, 0.59, 0.11], np.float32)
    rgb = rgb * (1 - grey) + lum[..., None] * grey
    rgb = rgb * np.array(mul, np.float32) + np.array(add, np.float32)
    a[..., :3] = np.clip(rgb, 0, 255)
    return Image.fromarray(a.astype(np.uint8), "RGBA")


def main():
    path = os.path.join(DRAWN, "drawn.json")
    with open(path) as fh:
        info = json.load(fh)
    for form, (mul, add, grey) in FORMS.items():
        for anim in info[SOURCE]["anims"]:
            src = os.path.join(DRAWN, f"{SOURCE}_{anim}.png")
            if not os.path.exists(src):
                continue
            recolour(Image.open(src), mul, add, grey).save(os.path.join(DRAWN, f"{form}_{anim}.png"))
            Image.open(os.path.join(DRAWN, f"{SOURCE}_{anim}_n.png")).save(os.path.join(DRAWN, f"{form}_{anim}_n.png"))
        entry = dict(info[SOURCE])
        entry["source"] = SOURCE
        entry["stand_in"] = True
        info[form] = entry
    with open(path, "w") as fh:
        json.dump(info, fh, indent=1, sort_keys=True)
    print("Wrote stand-in strips for", ", ".join(FORMS))


if __name__ == "__main__":
    main()
