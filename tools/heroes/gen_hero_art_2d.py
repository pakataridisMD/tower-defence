#!/usr/bin/env python3
"""Hero portraits and board sprites in the approved 2D pixel-art style.

Draws with the character art thread's 2D kit (tools/art/pix2d: people.py, portraits.py), so the heroes look the same
in the game as in the story art. Most heroes are people drawn from their cast-sheet spec. Ignar, Aurath and Orrok stay
elemental when freed (bible: Ignar is "a tall figure of cooling black stone"), so their board sprite is their boss
sprite with the corrupted grey light turned back to their element, shrunk 3:1 or 4:1 (each block keeps its most common
colour, bright cracks win) and re-inked.

usage: python3 tools/heroes/gen_hero_art_2d.py [--pix2d tools/art/pix2d] [--out assets/art/heroes]
Writes <out>/portraits/<id>.png (96x96) and <out>/board/<id>.png (feet at the bottom edge).
"""
import argparse
import os
import sys
from collections import Counter

import numpy as np
from PIL import Image

# game id -> people spec id in people.py
PEOPLE = {"tamsin": "tamsin", "brannoc": "brannoc", "kaela": "kaela", "sylvaine": "sylvaine", "mirelle": "mirelle",
          "gorrim": "gorrim", "corvin": "corvin", "ilyra": "ilyra", "seraphel": "seraphel", "oswin": "oswin_grey",
          "elowen": "elowen_warden", "thalassa": "thalassa_warden", "nyxara": "nyxara_queen"}
# freed Wardens who keep their elemental body: game id -> (boss sprite, light ramp in portraits.py, shrink factor)
ELEMENTAL = {"ignar": ("cinder_tyrant", "FIRE", 3), "aurath": ("thunderhead", "STORM", 4),
             "orrok": ("mountain_titan", "AMBER", 3)}
INK = (26, 18, 24, 255)


def shrink(im, f=3):
    a = np.array(im.convert("RGBA"))
    h, w = -(-a.shape[0] // f), -(-a.shape[1] // f)
    pad = np.zeros((h * f, w * f, 4), np.uint8)
    pad[:a.shape[0], :a.shape[1]] = a
    out = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        for x in range(w):
            blk = pad[y * f:(y + 1) * f, x * f:(x + 1) * f].reshape(-1, 4)
            op = blk[blk[:, 3] > 128]
            if len(op) * 2 < f * f * 0.8:
                continue
            lum = op[:, :3].astype(int).sum(1)
            col = Counter(map(tuple, op)).most_common(1)[0][0]
            if (lum > 600).sum() >= 2:
                col = tuple(op[lum.argmax()])
            out[y, x] = col
            out[y, x, 3] = 255
    solid = out[..., 3] > 0
    ink = np.zeros_like(solid)
    for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ink |= np.roll(np.roll(solid, dy, 0), dx, 1)
    out[ink & ~solid] = INK
    return Image.fromarray(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pix2d", default="tools/art/pix2d")
    ap.add_argument("--out", default="assets/art/heroes")
    args = ap.parse_args()
    sys.path.insert(0, os.path.abspath(args.pix2d))
    import creatures  # noqa: F401
    import bosses  # noqa: F401
    import wardens  # noqa: F401
    import final_bosses  # noqa: F401
    import people
    import portraits
    os.makedirs(os.path.join(args.out, "portraits"), exist_ok=True)
    os.makedirs(os.path.join(args.out, "board"), exist_ok=True)
    for gid in list(PEOPLE) + list(ELEMENTAL):
        portraits.portrait(gid).save(os.path.join(args.out, "portraits", gid + ".png"))
        if gid in PEOPLE:
            im = people.PEOPLE[PEOPLE[gid]]().image()
        else:
            name, ramp, factor = ELEMENTAL[gid]
            s = creatures.CREATURES[name]()
            portraits.freed(s, getattr(portraits, ramp))
            big = s.image()
            im = shrink(big.crop(big.getbbox()), factor)
        im.crop(im.getbbox()).save(os.path.join(args.out, "board", gid + ".png"))
        print(gid)


if __name__ == "__main__":
    main()
