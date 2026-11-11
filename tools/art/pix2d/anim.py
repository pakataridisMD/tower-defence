#!/usr/bin/env python3
"""Animate the 2D creatures: walk, attack and death strips drawn from the same code as the rest pose.

Each creature's drawing code names its groups (legs, weapon arm, head, wings...) and their joints. A pose turns and
shifts those groups, and every frame is drawn fresh, so there is no smeared rotation of finished pixels.

usage: python3 tools/art/pix2d/anim.py [names] --out art/pix2d/anim [--gif preview.gif]
Writes <name>_<anim>.png (frames left to right), <name>_<anim>_n.png (normal maps) and anim.json.
"""
import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image  # noqa: E402

import creatures  # noqa: E402

PAD = 28
FPS = {"walk": 10, "attack": 12, "death": 8}
STYLE = {"elf": "shoot", "dragon": "lunge", "ghost": "float", "golem": "heavy"}
STYLE.update({k: "float" for k in creatures.CREATURES if k.startswith("orb_")})


def _key(vals, i):
    return vals[i]


def walk(i, n, style):
    a = math.sin(2 * math.pi * i / n)
    c = math.cos(2 * math.pi * i / n)
    if style == "float":
        return {"_all": (0, 0, 1.6 * a), "tail": (0.14 * c, 0, 0), "weapon": (0.12 * a, 0, 0), "arm_f": (-0.12 * a, 0, 0)}
    k = 0.26 if style == "heavy" else 0.42
    bob = -(1 - abs(a)) * (1.4 if style != "lunge" else 1.0)
    return {"leg_n": (k * a, 0, 0), "leg_f": (-k * a, 0, 0), "leg_n2": (-0.3 * a, 0, 0), "leg_f2": (0.3 * a, 0, 0),
            "body": (0.02 * a, 0, bob), "weapon": (0.07 * a, 0, 0), "arm_n": (-0.08 * a, 0, 0),
            "arm_f": (0.22 * a, 0, 0), "wing": (0.2 * c, 0, 0), "wing_f": (0.2 * c, 0, 0), "tail": (0.09 * a, 0, 0),
            "head": (0, 0, 0.3 * c)}


def attack(i, n, style):
    if style == "shoot":       # draw the string back, loose, recover
        pull = [0, -1, -2, -2, 1, 0][i]
        return {"arm_f": (0, pull, 0), "body": ([0, -0.03, -0.05, -0.05, 0.04, 0][i], 0, 0),
                "weapon": (0, [0, 0, 0, 0, 1, 0][i], 0), "head": (0, 0, 0)}
    if style == "lunge":       # rear the head back, then strike forward breathing fire
        p = {"head": ([0, -0.14, -0.2, 0.1, 0.1, 0.03][i], [0, -2, -3, 4, 4, 1][i], 0),
             "body": (0, [0, -1, -2, 2, 2, 0][i], 0), "wing": ([0, -0.2, -0.3, 0.25, 0.15, 0][i], 0, 0),
             "wing_f": ([0, -0.2, -0.3, 0.25, 0.15, 0][i], 0, 0), "tail": ([0, 0.1, 0.15, -0.1, -0.05, 0][i], 0, 0)}
        if i in (3, 4):
            p["_fire"] = True
        return p
    if style == "float":
        return {"_all": (0, [0, -1, -2, 3, 2, 0][i], 0), "weapon": ([0, -0.3, -0.5, 0.45, 0.3, 0][i], 0, 0),
                "arm_f": ([0, -0.2, -0.4, 0.35, 0.2, 0][i], 0, 0), "tail": ([0, 0.1, 0.15, -0.2, -0.1, 0][i], 0, 0)}
    if style == "heavy":       # the arm hangs down, so it swings up and forward (anticlockwise) to punch
        return {"weapon": ([0, 0.3, 0.45, -1.25, -1.0, -0.3][i], 0, 0), "arm_f": ([0, -0.2, -0.3, 0.3, 0.2, 0][i], 0, 0),
                "body": ([0, -0.04, -0.07, 0.1, 0.07, 0.02][i], [0, -1, -1, 2, 1, 0][i], 0),
                "leg_n": ([0, 0, 0, -0.15, -0.1, 0][i], 0, 0), "head": ([0, 0, -0.04, 0.05, 0.03, 0][i], 0, 0)}
    return {"weapon": ([0, -0.45, -0.7, 0.95, 0.7, 0.2][i], 0, 0),
            "body": ([0, -0.06, -0.1, 0.14, 0.1, 0.03][i], [0, -1, -1, 2, 1, 0][i], 0),
            "leg_n": ([0, 0, 0, -0.22, -0.15, 0][i], 0, 0), "leg_f": ([0, 0, 0, 0.15, 0.1, 0][i], 0, 0),
            "arm_n": ([0, 0.1, 0.15, -0.15, -0.1, 0][i], 0, 0), "arm_f": ([0, 0.1, 0.15, -0.2, -0.1, 0][i], 0, 0),
            "head": ([0, -0.03, -0.05, 0.06, 0.04, 0][i], 0, 0)}


def death(i, n, style):
    if style == "float":       # drifts up and comes apart
        return {"_all": (0, 0, -1.2 * i), "weapon": (0.15 * i, 0, 0), "arm_f": (-0.1 * i, 0, 0), "tail": (0.05 * i, 0, 0)}
    if style == "lunge":       # too long to topple: the legs give way, the body drops, head and wings sag
        k = [0, 0.15, 0.4, 0.7, 0.9, 1.0][i]
        return {"body": (0.06 * k, 0, 11 * k), "head": (0.75 * k, -3 * k, 6 * k), "wing": (-0.9 * k, 0, 0),
                "wing_f": (-0.7 * k, 0, 0), "tail": (-0.2 * k, 0, 0), "leg_n": (-1.0 * k, 0, 4 * k),
                "leg_f": (-0.8 * k, 0, 4 * k), "leg_n2": (1.0 * k, 0, 4 * k), "leg_f2": (0.8 * k, 0, 4 * k)}
    r = [0, 0.2, 0.6, 1.1, 1.5, math.pi / 2][i]
    wr = 0 if style == "heavy" else [0, -0.3, -0.6, -0.8, -0.9, -0.9][i]
    return {"_all": (-r, [0, 0, 2, 5, 8, 9][i], [0, -1, 0, 1, 3, 3][i]), "weapon": (wr, 0, 0),
            "head": ([0, -0.1, -0.15, -0.2, -0.1, 0][i], 0, 0), "leg_n": ([0, 0.2, 0.35, 0.3, 0.15, 0.1][i], 0, 0),
            "wing": ([0, 0.2, 0.5, 0.8, 1.0, 1.0][i], 0, 0), "wing_f": ([0, 0.2, 0.5, 0.8, 1.0, 1.0][i], 0, 0)}


ANIMS = {"walk": (walk, 8), "attack": (attack, 6), "death": (death, 6)}


def frames(name, anim):
    fn, n = ANIMS[anim]
    style = STYLE.get(name, "swing")
    out = []
    for i in range(n):
        pose = fn(i, n, style)
        s = creatures.CREATURES[name](pose, PAD)
        if anim == "death" and style != "float":   # a falling body must land on the ground, not sink through it
            low = int(np.where(s.a.any(1))[0].max()) - (s.bh - 3 + PAD)
            if low > 0:
                r, dx, dy = pose.get("_all", (0, 0, 0))
                pose["_all"] = (r, dx, dy - low)
                s = creatures.CREATURES[name](pose, PAD)
        im, nm = np.asarray(s.image()).copy(), np.asarray(s.normal_image()).copy()
        if anim == "death":
            if style == "float":   # dissolve
                rng = np.random.default_rng(7)
                keep = rng.random(im.shape[:2]) >= [0, 0.1, 0.3, 0.55, 0.75, 0.92][i]
                im[~keep, 3] = 0
                nm[~keep, 3] = 0
            if hasattr(s, "_shadow"):  # the ground shadow fades with the body
                sh = s._shadow & ~s.a
                im[sh, 3] = (im[sh, 3] * (1 - i / n)).astype(np.uint8)
        out.append((Image.fromarray(im), Image.fromarray(nm), s))
    return out


def strip(ims):
    w, h = ims[0].size
    o = Image.new("RGBA", (w * len(ims), h), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        o.paste(im, (i * w, 0))
    return o


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--out", default=os.path.join("art", "pix2d", "anim"))
    ap.add_argument("--gif")
    ap.add_argument("--zoom", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    names = a.names or list(creatures.CREATURES)
    meta, allf = {}, {}
    for nme in names:
        for anim in ANIMS:
            fr = frames(nme, anim)
            strip([f[0] for f in fr]).save(os.path.join(a.out, f"{nme}_{anim}.png"))
            strip([f[1] for f in fr]).save(os.path.join(a.out, f"{nme}_{anim}_n.png"))
            s = fr[0][2]
            meta.setdefault(nme, {"frame": [s.w, s.h], "feet": [s.w // 2, s.bh - 4 + PAD], "anims": {}})["anims"][anim] = {
                "frames": len(fr), "fps": FPS[anim], "loop": anim == "walk"}
            allf[(nme, anim)] = [f[0] for f in fr]
        print(nme)
    mp = os.path.join(a.out, "anim.json")
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    old.update(meta)
    json.dump(old, open(mp, "w"), indent=1, sort_keys=True)
    if a.gif:
        preview(names, allf, a.gif, a.zoom)


def preview(names, allf, path, zoom):
    """All creatures side by side: walk twice, attack twice, die, hold."""
    seq = [("walk", i) for i in range(8)] * 2 + [("attack", i) for i in range(6)] * 2 + \
          [("death", i) for i in range(6)] + [("death", 5)] * 5
    cells = {n: allf[(n, "walk")][0].size for n in names}
    cols = 7
    rows = [names[i:i + cols] for i in range(0, len(names), cols)]
    crop = {n: (8, 14, cells[n][0] - 8, cells[n][1] - PAD + 6) for n in names}
    cw = {n: crop[n][2] - crop[n][0] for n in names}
    ch = {n: crop[n][3] - crop[n][1] for n in names}
    W = max(sum(cw[n] for n in r) for r in rows)
    rh = [max(ch[n] for n in r) for r in rows]
    out = []
    for anim, i in seq:
        im = Image.new("RGBA", (W, sum(rh)), (58, 76, 52, 255))
        y = 0
        for r, h in zip(rows, rh):
            x = (W - sum(cw[n] for n in r)) // 2
            for n in r:
                f = allf[(n, anim)][i].crop(crop[n])
                im.alpha_composite(f, (x, y + h - f.height))
                x += cw[n]
            y += h
        out.append(im.convert("RGB").resize((W * zoom, sum(rh) * zoom), Image.NEAREST))
    out[0].save(path, save_all=True, append_images=out[1:], duration=100, loop=0)
    print(path, out[0].size)


if __name__ == "__main__":
    main()
