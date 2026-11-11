#!/usr/bin/env python3
"""Animate the 2D creatures: idle, walk, attack and death strips drawn from the same code as the rest pose.

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
import bosses  # noqa: E402,F401  (adds the bosses to creatures.CREATURES)

PAD = 28
FPS = {"idle": 6, "walk": 10, "attack": 14, "death": 10}
STYLE = {"elf": "shoot", "dragon": "lunge", "ghost": "float", "golem": "heavy"}
STYLE.update({k: "float" for k in creatures.CREATURES if k.startswith("orb_")})
STYLE.update({"gorrath": "titan", "cinder_tyrant": "titan", "vael_orrun": "float"})
PADS = {"gorrath": 44, "cinder_tyrant": 66}          # room for the long arms of the big ones
LEGS = {"gorrath": 32, "cinder_tyrant": 48}          # thigh + shin length, for kneeling


ORBIT = {"orb_earth": math.pi / 3, "orb_nature": math.pi / 4}   # aura turns by one symmetry step per loop


def _sway(k, v):
    """Loose things (plume, cloak, hair, beard, chain) trail behind the motion: one value scaled per part."""
    return {"plume": (0.9 * k * v, 0, 0), "cloak": (0.5 * k * v, 0, 0), "hair": (0.5 * k * v, 0, 0),
            "beard": (0.4 * k * v, 0, 0), "chain": (1.0 * k * v, 0, 0)}


def idle(i, n, style, name):
    b = math.sin(2 * math.pi * i / n)
    lag = math.sin(2 * math.pi * i / n - 1.0)
    if style == "float":
        return {"_all": (0, 0, 1.2 * b), "tail": (0.08 * lag, 0, 0), "weapon": (0.06 * b, 0, 0), "arm_f": (-0.06 * b, 0, 0),
                "aura": (0.12 * lag, 0, -0.6 * max(0, b)), **_sway(0.12, lag)}
    return {"body": (0, 0, 0.5 + 0.5 * b), "head": (0, 0, 0.3 * lag), "weapon": (0.03 * b, 0, 0), "hand_w": (0.04 * lag, 0, 0),
            "arm_n": (0, 0, 0.3 * lag), "arm_f": (0.04 * b, 0, 0), "fore_f": (-0.05 * b, 0, 0), "neck": (0.03 * b, 0, 0),
            "wing": (0.06 * lag, 0, 0), "wing_f": (0.06 * lag, 0, 0), "tail": (0.04 * b, 0, 0), "tail2": (0.1 * lag, 0, 0),
            "jaw": (0.05 * max(0, b), 0, 0), **_sway(0.08, lag)}


def walk(i, n, style, name):
    ph = 2 * math.pi * i / n
    a, c = math.sin(ph), math.cos(ph)
    lag = math.sin(ph - 0.9)
    if style == "float":
        orbit = ORBIT.get(name)
        aura = (orbit * i / n, 0, 0) if orbit else (0.15 * lag, 0, -0.8 * max(0, c))
        return {"_all": (0, 0, 1.6 * a), "tail": (0.14 * c, 0, 0), "weapon": (0.12 * a, 0, 0), "arm_f": (-0.12 * a, 0, 0),
                "aura": aura, **_sway(0.2, lag)}
    A, K = (0.2, 0.3) if style in ("heavy", "titan") else (0.3, 0.6) if style == "lunge" else (0.4, 0.8)
    return {
        # thighs swing in opposition; each knee folds while its leg is carried forward, and straightens to land
        "leg_n": (-A * a, 0, 0), "shin_n": (0.06 + K * max(0, c), 0, 0),
        "leg_f": (A * a, 0, 0), "shin_f": (0.06 + K * max(0, -c), 0, 0),
        "leg_n2": (A * a, 0, 0), "shin_n2": (0.06 + K * max(0, -c), 0, 0),
        "leg_f2": (-A * a, 0, 0), "shin_f2": (0.06 + K * max(0, c), 0, 0),
        "body": (0.025 * a, 0, -1.3 * abs(c)), "head": (0.03 * lag, 0, 0), "neck": (0.05 * c, 0, 0),
        # free arm swings against its leg with a loose elbow; the weapon arm bobs
        "arm_f": (-0.28 * a, 0, 0), "fore_f": (-0.18 - 0.16 * a, 0, 0),
        "weapon": (0.06 * a, 0, 0), "hand_w": (0.06 * c, 0, 0), "arm_n": (-0.06 * a, 0, 0),
        "wing": (0.2 * c, 0, 0), "wing_f": (0.2 * c, 0, 0), "tail": (0.08 * a, 0, 0), "tail2": (0.16 * lag, 0, 0),
        **_sway(0.2, lag)}


def attack(i, n, style, name):
    k = lambda *v: v[i]  # noqa: E731
    if style == "shoot":       # draw, hold, loose, string snaps straight, nock again
        p = {"arm_f": (0, k(0, -1, -2, -3, -3, 2, 1, 0), 0), "weapon": (k(0, -0.03, -0.05, -0.06, -0.06, 0.04, 0.02, 0), 0, 0),
             "body": (k(0, -0.02, -0.04, -0.05, -0.05, 0.04, 0.02, 0), 0, 0), "head": (k(0, 0, -0.02, -0.03, -0.03, 0.03, 0, 0), 0, 0),
             "leg_n": (k(0, -0.05, -0.1, -0.1, -0.1, -0.05, 0, 0), 0, 0), "shin_n": (k(0, 0.05, 0.1, 0.1, 0.1, 0.05, 0, 0), 0, 0),
             **_sway(1, k(0, 0.05, 0.1, 0.1, 0.1, -0.2, -0.1, 0.05))}
        if i in (5, 6):
            p["_loosed"] = True
        return p
    if style == "lunge":       # coil the neck back, then strike with jaws open and fire
        p = {"neck": (k(0, -0.12, -0.2, -0.24, 0.14, 0.18, 0.1, 0.03), 0, 0), "head": (k(0, -0.08, -0.14, -0.16, 0.1, 0.1, 0.05, 0), 0, 0),
             "jaw": (k(0, 0, 0.1, 0.18, 0.45, 0.45, 0.2, 0), 0, 0), "body": (0, k(0, -1, -2, -2, 2, 3, 2, 0), k(0, 0, 1, 1, 0, 0, 0, 0)),
             "wing": (k(0, -0.15, -0.3, -0.35, 0.25, 0.2, 0.1, 0), 0, 0), "wing_f": (k(0, -0.15, -0.3, -0.35, 0.25, 0.2, 0.1, 0), 0, 0),
             "tail": (k(0, 0.08, 0.12, 0.15, -0.1, -0.08, -0.03, 0), 0, 0), "tail2": (k(0, 0.1, 0.2, 0.25, -0.2, -0.15, -0.05, 0), 0, 0),
             "leg_n": (k(0, 0.05, 0.1, 0.1, -0.12, -0.14, -0.06, 0), 0, 0), "shin_n": (k(0, 0.1, 0.2, 0.2, 0.1, 0.1, 0.05, 0), 0, 0),
             "leg_n2": (k(0, 0.05, 0.1, 0.1, 0.1, 0.1, 0.05, 0), 0, 0), "shin_n2": (k(0, 0.1, 0.25, 0.25, 0, 0, 0, 0), 0, 0)}
        if i in (4, 5, 6):
            p["_fire"] = True
        return p
    if style == "float":
        return {"_all": (0, k(0, -1, -2, -2, 3, 3, 2, 0), 0), "weapon": (k(0, -0.2, -0.4, -0.5, 0.4, 0.5, 0.3, 0), 0, 0),
                "arm_f": (k(0, -0.15, -0.3, -0.4, 0.3, 0.35, 0.2, 0), 0, 0), "tail": (k(0, 0.1, 0.15, 0.2, -0.2, -0.15, -0.05, 0), 0, 0),
                "aura": (k(0, 0.1, 0.2, 0.3, -0.3, -0.2, -0.1, 0), k(0, -1, -1, -2, 2, 2, 1, 0), 0),
                **_sway(1, k(0, 0.1, 0.15, 0.2, -0.3, -0.2, 0.1, 0))}
    if style in ("heavy", "titan"):       # a slow windmill: the arm goes back, up and over, and comes down straight as a hammer
        return {"weapon": (k(0, 0.9, 1.9, 2.8, 3.9, 4.6, 5.4, 6.0), 0, 0), "hand_w": (k(0, -0.5, -0.8, -0.7, -0.2, 0, -0.1, 0), 0, 0),
                "arm_f": (k(0, -0.15, -0.25, -0.3, 0.3, 0.3, 0.15, 0), 0, 0), "fore_f": (k(0, -0.2, -0.3, -0.3, 0, 0, 0, 0), 0, 0),
                "body": (k(0, -0.03, -0.06, -0.08, 0.06, 0.1, 0.06, 0.02), k(0, -1, -1, -1, 1, 2, 1, 0), k(0, 0, 0, 0, 1, 2, 1, 0)),
                "leg_n": (k(0, 0, 0, 0, -0.15, -0.15, -0.08, 0), 0, 0), "shin_n": (k(0, 0, 0, 0, 0.15, 0.15, 0.08, 0), 0, 0),
                "head": (k(0, 0, -0.03, -0.04, 0.05, 0.06, 0.03, 0), 0, 0)}
    # swing: wind up over the shoulder with the elbow bent, cut down as the front knee takes the weight, follow through
    return {"weapon": (k(0, -0.25, -0.5, -0.6, 0.45, 0.8, 0.5, 0.15), 0, 0), "hand_w": (k(0, -0.25, -0.5, -0.6, 0.35, 0.55, 0.3, 0.08), 0, 0),
            "body": (k(0, -0.04, -0.08, -0.1, 0.1, 0.14, 0.08, 0.02), k(0, -1, -1, -2, 2, 3, 2, 0), k(0, 0, 0, 0, 1, 1, 0, 0)),
            "leg_n": (k(0, 0.05, 0.1, 0.1, -0.3, -0.32, -0.15, 0), 0, 0), "shin_n": (k(0, 0.1, 0.2, 0.2, 0.3, 0.25, 0.12, 0), 0, 0),
            "leg_f": (k(0, 0, 0, 0, 0.18, 0.2, 0.1, 0), 0, 0), "shin_f": (k(0, 0.1, 0.15, 0.15, 0.05, 0.05, 0, 0), 0, 0),
            "arm_n": (k(0, 0.08, 0.15, 0.15, -0.15, -0.2, -0.1, 0), 0, 0), "arm_f": (k(0, 0.1, 0.15, 0.15, -0.2, -0.25, -0.1, 0), 0, 0),
            "fore_f": (k(0, -0.1, -0.2, -0.2, -0.3, -0.3, -0.15, 0), 0, 0), "head": (k(0, -0.03, -0.05, -0.06, 0.06, 0.08, 0.04, 0), 0, 0),
            "jaw": (k(0, 0, 0.1, 0.15, 0.3, 0.3, 0.1, 0), 0, 0), **_sway(1, k(0, 0.1, 0.15, 0.1, -0.3, -0.25, 0.1, 0.05))}


def death(i, n, style, name):
    k = lambda *v: v[i]  # noqa: E731
    if style == "float":       # drifts up and comes apart
        return {"_all": (0, 0, -1.0 * i), "weapon": (0.12 * i, 0, 0), "arm_f": (-0.08 * i, 0, 0), "tail": (0.04 * i, 0, 0),
                "aura": (0.15 * i, 0, -0.5 * i), **_sway(0.1, i)}
    if style == "lunge":       # too long to topple: knees fold, the body drops, neck and wings sag, a last twitch
        q = k(0, 0.1, 0.25, 0.5, 0.75, 0.95, 1.05, 1.0)
        return {"body": (0.06 * q, 0, 11 * q), "neck": (0.55 * q, 0, 0), "head": (0.35 * q, 0, 0), "jaw": (0.3 * q, 0, 0),
                "wing": (-0.9 * q, 0, 0), "wing_f": (-0.7 * q, 0, 0), "tail": (-0.15 * q, 0, 0), "tail2": (-0.2 * q, 0, 0),
                "leg_n": (-0.9 * q, 0, 4 * q), "shin_n": (1.1 * q, 0, 0), "leg_f": (-0.7 * q, 0, 4 * q), "shin_f": (0.9 * q, 0, 0),
                "leg_n2": (0.6 * q, 0, 4 * q), "shin_n2": (0.5 * q, 0, 0), "leg_f2": (0.5 * q, 0, 4 * q), "shin_f2": (0.5 * q, 0, 0)}
    if style == "titan":       # too big to topple: drops to its knees, slumps forward and blows away as dust
        q = k(0, 0.15, 0.4, 0.7, 0.9, 1.0, 1.0, 1.0)
        drop = 0.5 * LEGS.get(name, 32) * q
        return {"leg_n": (-1.0 * q, 0, drop), "shin_n": (2.1 * q, 0, 0), "leg_f": (-0.9 * q, 0, drop), "shin_f": (2.0 * q, 0, 0),
                "body": (0.3 * q, 2 * q, drop), "head": (0.35 * q, 0, 0), "jaw": (0.4 * q, 0, 0),
                "weapon": (-0.25 * q, 0, 0), "hand_w": (-0.3 * q, 0, 0), "arm_f": (-0.3 * q, 0, 0), "fore_f": (-0.2 * q, 0, 0),
                **_sway(1, k(0, 0.1, 0.25, 0.4, 0.3, 0.1, 0, 0))}
    # reel from the blow with buckling knees, topple backwards, bounce once and settle with limbs gone slack
    r = k(0, 0.1, 0.3, 0.7, 1.15, 1.5, 1.63, math.pi / 2)
    heavy = style == "heavy"
    return {"_all": (-r, k(0, 0, 1, 3, 5, 8, 9, 9), 0),
            "body": (k(0, -0.08, -0.1, -0.05, 0, 0, 0, 0), 0, k(0, 1, 2, 1, 0, 0, 0, 0)),
            "leg_n": (k(0, -0.3, -0.45, -0.4, -0.3, -0.2, -0.12, -0.15), 0, 0), "shin_n": (k(0, 0.5, 0.8, 0.7, 0.5, 0.3, 0.15, 0.2), 0, 0),
            "leg_f": (k(0, -0.1, -0.2, -0.2, -0.1, 0, 0.05, 0), 0, 0), "shin_f": (k(0, 0.3, 0.5, 0.5, 0.3, 0.15, 0.05, 0.1), 0, 0),
            "weapon": (0 if heavy else k(0, -0.2, -0.5, -0.8, -1.0, -0.9, -0.8, -0.85), 0, 0),
            "hand_w": (k(0, 0.1, 0.3, 0.5, 0.6, 0.5, 0.4, 0.45) * (0.4 if heavy else 1), 0, 0),
            "arm_f": (k(0, -0.2, -0.4, -0.6, -0.7, -0.6, -0.5, -0.55) * (0.3 if heavy else 1), 0, 0), "fore_f": (k(0, -0.2, -0.4, -0.5, -0.4, -0.2, -0.1, -0.15), 0, 0),
            "arm_n": (k(0, 0.1, 0.2, 0.3, 0.3, 0.2, 0.15, 0.2), 0, 0),
            "head": (k(0, -0.15, -0.2, -0.25, -0.15, 0.08, -0.05, 0), 0, 0), "jaw": (k(0, 0.2, 0.3, 0.35, 0.4, 0.5, 0.4, 0.45), 0, 0),
            **_sway(1, k(0, 0.2, 0.4, 0.5, 0.3, -0.3, 0.1, 0))}


ANIMS = {"idle": (idle, 6), "walk": (walk, 8), "attack": (attack, 8), "death": (death, 8)}
DISSOLVE = [0, 0.05, 0.15, 0.3, 0.5, 0.7, 0.85, 0.95]
DISSOLVE_TITAN = [0, 0, 0, 0.03, 0.15, 0.4, 0.68, 0.92]


def frames(name, anim):
    fn, n = ANIMS[anim]
    style = STYLE.get(name, "swing")
    out = []
    for i in range(n):
        pose = fn(i, n, style, name)
        pad = PADS.get(name, PAD)
        s = creatures.CREATURES[name](pose, pad)
        if anim == "death" and style not in ("float", "titan"):   # a falling body must land on the ground, not sink through it
            low = int(np.where(s.a.any(1))[0].max()) - (s.bh - 3 + pad)
            if low > 0:
                r, dx, dy = pose.get("_all", (0, 0, 0))
                pose["_all"] = (r, dx, dy - low)
                s = creatures.CREATURES[name](pose, pad)
        im, nm = np.asarray(s.image()).copy(), np.asarray(s.normal_image()).copy()
        if anim == "death":
            if style in ("float", "titan"):   # dissolve
                rng = np.random.default_rng(7)
                keep = rng.random(im.shape[:2]) >= (DISSOLVE if style == "float" else DISSOLVE_TITAN)[i]
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
            meta.setdefault(nme, {"frame": [s.w, s.h], "feet": [s.w // 2, s.bh - 4 + s.pad], "anims": {}})["anims"][anim] = {
                "frames": len(fr), "fps": FPS[anim], "loop": anim in ("idle", "walk")}
            allf[(nme, anim)] = [f[0] for f in fr]
        print(nme)
    mp = os.path.join(a.out, "anim.json")
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    old.update(meta)
    json.dump(old, open(mp, "w"), indent=1, sort_keys=True)
    if a.gif:
        preview(names, allf, a.gif, a.zoom)


def preview(names, allf, path, zoom):
    """All creatures side by side: idle, walk twice, attack twice, die, hold."""
    seq = [("idle", i) for i in range(6)] + [("walk", i) for i in range(8)] * 2 + [("attack", i) for i in range(8)] * 2 + \
          [("death", i) for i in range(8)] + [("death", 7)] * 6
    cells = {n: allf[(n, "walk")][0].size for n in names}
    cols = 7
    rows = [names[i:i + cols] for i in range(0, len(names), cols)]
    crop = {n: (PADS.get(n, PAD) - 20, PADS.get(n, PAD) - 14, cells[n][0] - PADS.get(n, PAD) + 20, cells[n][1] - PADS.get(n, PAD) + 6) for n in names}
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
