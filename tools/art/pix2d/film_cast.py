"""Battle-style sprites for the film cast who had none: the Keeper, Seraphel (bright and greyed) and the six mortal
monarchs. They are the people.py figures, animated with anim.py, plus a cast animation, written in the format of
art/story/characters/<id>/ that the Blender story films read (cinema/blender/sprites.py):

    <anim>_<k>.png, <anim>_<k>_n.png (normal map), <anim>_<k>_glow.png (glowing pixels only, where there are any)

idle 6, walk 8, attack 8, cast 8, death 8 frames, drawn for 8 fps, facing right, 96x88 canvas, feet at (48, 84),
no ground shadow (the 3D set casts its own).

    python3 tools/art/pix2d/film_cast.py [ids] --out art/story/characters --sheet sheet.png
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import anim  # noqa: E402
import creatures  # noqa: E402
import people  # noqa: E402
from people import ACCENT, R, SPECS  # noqa: E402

W, H, FX, FY = 96, 88, 48, 84     # canvas and feet point


def item_hammer_down(s, hx, hy, sp):
    """Ignar's forge hammer carried head-down at his side, so it does not hide his face."""
    s.part(s.capsule(hx + 1, hy - 5, hx + 3, hy + 13, 1.0), people.WOOD, edge=False)
    s.part(s.rect(hx - 3, hy + 12, hx + 9, hy + 19), R("4a4650"), flat=True)
    s.line(hx - 3, hy + 15, hx + 9, hy + 15, (255, 140, 40), glow=True)
    s.px(hx + 8, hy + 13, (255, 190, 90), glow=True)


def item_greatsword_grey(s, hx, hy, sp):
    """The Sunstone blade with its light gone: grey glass, nothing glowing."""
    s.part(s.poly([(hx + 1, hy - 3), (hx + 5, hy - 3), (hx + 6, hy - 40), (hx + 3, hy - 44), (hx, hy - 40)]), R("b8b4a8", 0.4), flat=True)
    s.fill(s.poly([(hx + 2, hy - 6), (hx + 4, hy - 6), (hx + 4, hy - 38), (hx + 3, hy - 41), (hx + 2, hy - 38)]), (208, 204, 196))
    s.part(s.rect(hx - 3, hy - 3, hx + 9, hy - 1), R("8a8478"), flat=True)
    s.part(s.rect(hx + 2, hy - 1, hx + 4, hy + 5), people.LEATHER, flat=True)


people.ITEMS["hammer_down"] = item_hammer_down
people.ITEMS["greatsword_grey"] = item_greatsword_grey


def _seraphel_grey():
    sp = dict(SPECS["seraphel"])
    sp.update(name="Seraphel, the light gone grey", top="b4b0a4", top_d="8e8a80", legs="a09c90", boots="7e7a70",
              eye=(150, 140, 120), eye_glow=False, skin="c8a08a", item="greatsword_grey")
    return sp


def _keeper():
    """Vael-Orrun as the Keeper of the Crossroads: about 40, kind, plain grey robes, no crown, ink on his fingers."""
    sp = dict(SPECS["vael_orrun_young"])
    sp.update(name="The Keeper of the Crossroads", top="7a7a7e", top_d="5e5e64", trim="9a9aa0", headgear=None, item=None)
    return sp


FILM = {
    "keeper": (_keeper(), "e8c890"),
    "seraphel": (dict(SPECS["seraphel"]), ACCENT["seraphel"]),
    "seraphel_grey": (_seraphel_grey(), "c8c4b8"),
    "ignar_king": (dict(SPECS["ignar_king"], top="5e5a5e", tabard="8a2a18", hair="3a1810", beard="short", beard_col="4a1c12", skin="d8a07c", item="hammer_down"),
                   ACCENT["ignar_king"]),
    "aurath_king": (dict(SPECS["aurath_king"]), ACCENT["aurath_king"]),
    "elowen_queen": (dict(SPECS["elowen_queen"]), ACCENT["elowen_queen"]),
    "thalassa_queen": (dict(SPECS["thalassa_queen"], hair="241c26"), ACCENT["thalassa_queen"]),
    "orrok_king": (dict(SPECS["orrok_king"]), ACCENT["orrok_king"]),
    "nyxara_queen": (dict(SPECS["nyxara_queen"]), ACCENT["nyxara_queen"]),
}


def _with_cast_light(sp, accent):
    """Wrap the spec's after-hook: during a cast a small light gathers in the near hand."""
    before = sp.get("after")
    tones = R(accent)

    def after(s, X, Y, rr):
        if before:
            before(s, X, Y, rr)
        q = s.pose.get("_cast", 0.0)
        if q <= 0:
            return
        s.g("weapon", X(22), Y(24))
        s.g("hand_w", X(24), Y(32), "weapon")
        hx, hy = X(34.5), Y(32)
        r = 0.8 + 2.2 * q
        s.fill(s.ellipse(hx, hy, r + 1, r + 1), tones[2], glow=True)
        s.fill(s.ellipse(hx, hy, r, r), tones[3], glow=True)
        s.fill(s.ellipse(hx, hy, max(0.6, r - 1.4), max(0.6, r - 1.4)), (255, 250, 235), glow=True)
        t = s.pose.get("_t", 0)
        for k in range(int(3 + 4 * q)):
            a = k * 2.4 + t * 0.9
            d = r + 2 + (k % 3)
            s.px(hx + d * math.cos(a), hy + d * math.sin(a), tones[3 + (k % 2)], glow=True)

    sp["after"] = after
    return sp


def cast(i, n, style, name):
    """Raise the near hand, gather light, hold it out, let it go and come back down."""
    k = lambda *v: v[i]  # noqa: E731
    return {"weapon": (k(0, -0.25, -0.5, -0.7, -0.75, -0.75, -0.5, -0.2), 0, 0),
            "hand_w": (k(0, 0.1, 0.25, 0.35, 0.4, 0.4, 0.25, 0.05), 0, 0),
            "arm_f": (k(0, -0.1, -0.25, -0.35, -0.4, -0.4, -0.25, -0.1), 0, 0),
            "fore_f": (k(0, -0.1, -0.3, -0.4, -0.45, -0.45, -0.3, -0.1), 0, 0),
            "body": (k(0, -0.02, -0.04, -0.05, -0.05, 0.02, 0.01, 0), 0, k(0, 0, -1, -1, -1, 0, 0, 0)),
            "head": (k(0, -0.03, -0.06, -0.08, -0.08, 0, 0, 0), 0, 0),
            "_cast": k(0, 0.1, 0.35, 0.7, 1.0, 1.0, 0.5, 0.1),
            **anim._sway(1, k(0, 0.1, 0.2, 0.25, 0.25, -0.15, -0.1, 0))}


anim.ANIMS["cast"] = (cast, 8)
ORDER = ["idle", "walk", "attack", "cast", "death"]


def register():
    for fid, (sp, acc) in FILM.items():
        sp = _with_cast_light(sp, acc)
        creatures.CREATURES[fid] = (lambda spec: (lambda pose=None, pad=0: people.figure(spec, pose, pad)))(sp)


def crop(s, im, nm):
    """Cut a W x H window with the rest-pose feet at (FX, FY); drop the ground shadow."""
    a = np.asarray(im).copy()
    n = np.asarray(nm).copy()
    if hasattr(s, "_shadow"):
        sh = s._shadow & ~s.a
        a[sh] = 0
        n[sh] = 0
    fx, fy = s.pad + 30, s.pad + 71            # figure(): cx 30, foot 71 on its 60x76 canvas
    x0, y0 = fx - FX, fy - FY
    out = []
    for arr in (a, n):
        c = np.zeros((H, W, 4), np.uint8)
        sx0, sy0 = max(0, x0), max(0, y0)
        sx1, sy1 = min(arr.shape[1], x0 + W), min(arr.shape[0], y0 + H)
        c[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = arr[sy0:sy1, sx0:sx1]
        out.append(c)
    a, n = out
    clipped = int(s.a.sum()) - int((a[..., 3] > 0).sum())
    g = np.zeros_like(a)
    gm = np.zeros(s.a.shape, bool)
    gm[:] = s.glow & s.a
    gc = np.zeros((H, W), bool)
    sx0, sy0 = max(0, x0), max(0, y0)
    sx1, sy1 = min(gm.shape[1], x0 + W), min(gm.shape[0], y0 + H)
    gc[sy0 - y0:sy1 - y0, sx0 - x0:sx1 - x0] = gm[sy0:sy1, sx0:sx1]
    g[gc] = a[gc]
    return a, n, g, clipped


def render(fid, out):
    d = os.path.join(out, fid)
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        if f.endswith(".png"):
            os.remove(os.path.join(d, f))
    rows = []
    for an in ORDER:
        row = []
        for k, (im, nm, s) in enumerate(anim.frames(fid, an)):
            a, n, g, clipped = crop(s, im, nm)
            if clipped > 0 and an != "death":
                print("  clipped", fid, an, k, clipped)
            Image.fromarray(a).save(os.path.join(d, "%s_%d.png" % (an, k)))
            Image.fromarray(n).save(os.path.join(d, "%s_%d_n.png" % (an, k)))
            if g[..., 3].any():
                Image.fromarray(g).save(os.path.join(d, "%s_%d_glow.png" % (an, k)))
            row.append(Image.fromarray(a))
        rows.append(row)
    sheet = Image.new("RGBA", (W * 8, H * len(rows)))
    for r, row in enumerate(rows):
        for c, im in enumerate(row):
            sheet.alpha_composite(im, (c * W, r * H))
    sheet.save(os.path.join(d, "sheet.png"))
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--out", default="art/story/characters")
    ap.add_argument("--sheet")
    ap.add_argument("--zoom", type=int, default=2)
    a = ap.parse_args()
    register()
    ids = a.ids or list(FILM)
    sheets = []
    for fid in ids:
        print(fid)
        sheets.append((fid, render(fid, a.out)))
    if a.sheet:
        from PIL import ImageDraw
        z = a.zoom
        sw, sh = sheets[0][1].size
        big = Image.new("RGBA", (sw * z, (sh + 14) * z * len(sheets)), (44, 42, 52, 255))
        dr = ImageDraw.Draw(big)
        for i, (fid, s) in enumerate(sheets):
            y = i * (sh + 14) * z
            dr.text((6, y + 4), fid + "   idle / walk / attack / cast / death", fill=(230, 230, 230))
            big.alpha_composite(s.resize((sw * z, sh * z), Image.NEAREST), (0, y + 14 * z))
        big.save(a.sheet)


if __name__ == "__main__":
    main()
