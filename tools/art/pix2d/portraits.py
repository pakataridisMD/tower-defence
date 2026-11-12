#!/usr/bin/env python3
"""Story portraits, 96x96, under the game's character ids.

People get a bust drawn from their spec (people.portrait). Heralds, Wardens and Vael-Orrun are not people: their
portrait is the head of their battle sprite, cropped and doubled (whole pixels, never smoothed) onto the same disc.
Freed Wardens use their boss sprite with the grey light turned back to their own element's colour.

usage: python3 tools/art/pix2d/portraits.py [ids] --out art/pix2d/portraits [--sheet sheet.png]
"""
import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

import creatures  # noqa: E402
import bosses  # noqa: E402,F401
import wardens  # noqa: E402,F401
import final_bosses  # noqa: E402,F401
import people  # noqa: E402
import vael_ascend  # noqa: E402,F401
from kit import Sprite  # noqa: E402

FIRE = [(150, 40, 16), (230, 96, 30), (255, 160, 60), (255, 220, 140)]
STORM = [(110, 100, 200), (170, 170, 240), (226, 228, 255), (255, 255, 255)]
AMBER = [(130, 80, 20), (210, 140, 40), (250, 196, 90), (255, 236, 170)]

# game id -> people spec id
PEOPLE = {"tamsin": "tamsin", "brannoc": "brannoc", "kaela": "kaela", "sylvaine": "sylvaine", "mirelle": "mirelle",
          "gorrim": "gorrim", "corvin": "corvin", "ilyra": "ilyra", "seraphel": "seraphel", "oswin": "oswin_grey",
          "oswin_white": "oswin_white", "ysolde": "ysolde", "ysolde_blind": "ysolde_blind", "fennick": "fennick",
          "cassivane": "cassivane_marshal", "thalassa": "thalassa_warden", "elowen": "elowen_warden", "nyxara": "nyxara_queen",
          "ignar_king": "ignar_king", "aurath_king": "aurath_king", "elowen_queen": "elowen_queen",
          "thalassa_queen": "thalassa_queen", "orrok_king": "orrok_king", "nyxara_queen": "nyxara_queen",
          "vael_orrun_king": "vael_orrun_king"}
# game id -> (sprite, centre x, centre y on the canvas, crop size, disc colour, freed element ramp or None)
HEADS = {"saltmother": ("ourra", 50, 52, 48, "3a8a8a", None), "gorrath": ("gorrath", 54, 24, 48, "a07c4c", None),
         "pale_vesper": ("vesper", 63, 20, 48, "8a70c0", None), "ashwick": ("ashwick", 49, 24, 48, "e06020", None),
         "vholt": ("vholt", 90, 36, 48, "6a78b0", None), "mother_briar": ("mother_briar", 76, 42, 48, "5a8a3a", None),
         "cassivane_ashen": ("cassivane", 52, 34, 48, "6a5a5a", None), "vael_orrun": ("vael_bare", 150, 124, 48, "6a2a2e", None),
         "ignar": ("cinder_tyrant", 90, 58, 48, "e0602a", FIRE), "aurath": ("thunderhead", 94, 62, 48, "8aa0e0", STORM),
         "orrok": ("mountain_titan", 132, 74, 48, "b07030", AMBER),
         "sundered_heart": ("sundered_heart", 104, 100, 96, "e0a040", None), "hollow_king": ("hollow_king", 86, 54, 48, "5a40a0", None)}


def freed(s, tones):
    """Turn a corrupted Warden's grey light back into its element's light."""
    rgb = s.rgb.astype(np.int32)
    sat = rgb.max(-1) - rgb.min(-1)
    m = s.a & s.glow & (sat < 40)
    lum = rgb[..., 0] * 0.3 + rgb[..., 1] * 0.55 + rgb[..., 2] * 0.15
    idx = np.clip(((lum - 100) / 160 * len(tones)).astype(int), 0, len(tones) - 1)
    s.rgb[m] = np.array(tones, np.uint8)[idx][m]
    return s


def disc(acc):
    from people import R
    a = R(acc, spread=0.4)
    bg = Sprite(96, 96)
    m = bg.ellipse(48, 48, 46, 46)
    bg.fill(m, tuple(int(c * 0.28) for c in a[1]))
    bg.fill(bg.ellipse(40, 36, 30, 30) & m, tuple(int(c * 0.4) for c in a[2]))
    bg.fill(m & ~bg.ellipse(48, 48, 44.5, 44.5), a[2])
    return bg, m


def head_portrait(gid):
    name, cx, cy, size, acc, el = HEADS[gid]
    s = creatures.CREATURES[name]()
    if el:
        freed(s, el)
    im = s.image()
    box = (cx - size // 2, cy - size // 2, cx + size // 2, cy + size // 2)
    crop = Image.new("RGBA", (size, size))
    crop.alpha_composite(im.crop((max(0, box[0]), max(0, box[1]), min(im.width, box[2]), min(im.height, box[3]))),
                         (max(0, -box[0]), max(0, -box[1])))
    crop = crop.resize((96, 96), Image.NEAREST)
    bg, m = disc(acc)
    out = bg.image()
    out.alpha_composite(crop)
    arr = np.asarray(out).copy()
    arr[~m, 3] = 0
    ring = m & ~bg.ellipse(48, 48, 44.5, 44.5)
    arr[ring, :3] = bg.rgb[ring]
    arr[ring, 3] = 255
    return Image.fromarray(arr)


def portrait(gid):
    if gid in PEOPLE:
        return people.portrait(PEOPLE[gid]).image()
    return head_portrait(gid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--out", default=os.path.join("art", "pix2d", "portraits"))
    ap.add_argument("--sheet")
    a = ap.parse_args()
    ids = a.ids or list(PEOPLE) + list(HEADS)
    os.makedirs(a.out, exist_ok=True)
    ims = []
    for gid in ids:
        im = portrait(gid)
        im.save(os.path.join(a.out, gid + ".png"))
        ims.append((gid, im))
    if a.sheet:
        z, cols = 2, 10
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGBA", (cols * 104 * z, rows * 116 * z), (30, 28, 34, 255))
        d = ImageDraw.Draw(sheet)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 9 * z)
        for i, (gid, im) in enumerate(ims):
            x, y = (i % cols) * 104 * z + 4 * z, (i // cols) * 116 * z + 4 * z
            sheet.alpha_composite(im.resize((96 * z, 96 * z), Image.NEAREST), (x, y))
            tw = d.textlength(gid, font=font)
            d.text((x + 48 * z - tw / 2, y + 98 * z), gid, font=font, fill=(220, 214, 196))
        sheet.convert("RGB").save(a.sheet)
        print(a.sheet, sheet.size)


if __name__ == "__main__":
    main()
