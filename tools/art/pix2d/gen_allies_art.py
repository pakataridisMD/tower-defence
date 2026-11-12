#!/usr/bin/env python3
"""Draws and animates the army of the counter-attack (tools/art/pix2d/allies.py) for the game.

usage: python3 tools/art/pix2d/gen_allies_art.py [names] [--out DIR] [--sheet FILE] [--gif FILE] [--zoom N]

Writes <id>_<anim>.png and its _n.png normal strip (frames left to right) for every animation, into
assets/art/game/allies/, and allies.json with each one's frame size, feet point, height above the feet and
frame counts, which scripts/game/ally_art.gd reads. The animations: walk, idle (standing in the line between
blows), attack, hurt (a flinch from a heavy blow), cry (the war cry it gives when it shouts) and death. --sheet writes a labelled sheet of the rest poses for review and
--gif an animated preview.
"""
import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402

import allies  # noqa: E402
import anim  # noqa: E402
import creatures  # noqa: E402

OUT = os.path.join("assets", "art", "game", "allies")
ANIMS = ("walk", "idle", "attack", "hurt", "cry", "death")

creatures.CREATURES.update(allies.UNITS)
anim.STYLE.update(allies.STYLES)
_walk, _attack, _death, _idle = anim.walk, anim.attack, anim.death, anim.idle
anim.FPS.update({"hurt": 14, "cry": 9})


def walk(i, n, style, name):
    if style == "fly":
        ph = 2 * math.pi * i / n
        a, c = math.sin(ph), math.cos(ph)
        return {"_all": (0, 0, -6 + 2.0 * a), "wing": (0.55 * c, 0, 0), "wing_f": (0.5 * c, 0, 0),
                "leg_n": (0.5, 0, 0), "leg_f": (0.45, 0, 0), "tail": (0.08 * a, 0, 0), "head": (0.04 * c, 0, 0),
                **anim._sway(0.2, math.sin(ph - 0.9))}
    base = {"charge": "lunge"}.get(style, style)
    return _walk(i, n, base, name)


def attack(i, n, style, name):
    k = lambda *v: v[i]  # noqa: E731
    if style == "thrust":
        return {"weapon": (k(0, -0.04, -0.08, -0.1, 0.05, 0.08, 0.04, 0), k(0, -2, -4, -5, 4, 7, 4, 1), k(0, 1, 2, 2, -2, -3, -1, 0)),
                "body": (k(0, -0.03, -0.05, -0.06, 0.06, 0.08, 0.04, 0), k(0, -1, -1, -2, 2, 3, 2, 0), 0),
                "leg_n": (k(0, 0.05, 0.1, 0.1, -0.3, -0.32, -0.15, 0), 0, 0), "shin_n": (k(0, 0.1, 0.2, 0.2, 0.3, 0.25, 0.12, 0), 0, 0),
                "head": (k(0, -0.03, -0.04, -0.05, 0.04, 0.05, 0.02, 0), 0, 0), **anim._sway(1, k(0, 0.1, 0.15, 0.1, -0.3, -0.25, 0.1, 0.05))}
    if style == "recoil":
        p = {"weapon": (k(0, -0.02, -0.03, -0.03, 0.08, 0.05, 0.02, 0), k(0, 0, 0, 0, -2, -1, 0, 0), 0),
             "body": (k(0, -0.01, -0.02, -0.02, 0.04, 0.03, 0.01, 0), k(0, 0, 0, 0, -1, -1, 0, 0), 0),
             "head": (k(0, 0, -0.02, -0.02, 0.03, 0.02, 0, 0), 0, 0)}
        if i in (4, 5, 6):
            p["_loosed"] = True
        return p
    if style == "raise":
        return {"weapon": (k(0, -0.25, -0.5, -0.7, -0.75, -0.6, -0.3, -0.1), 0, k(0, -1, -2, -3, -3, -2, -1, 0)),
                "hand_w": (k(0, -0.1, -0.2, -0.3, -0.3, -0.2, -0.1, 0), 0, 0),
                "arm_n": (k(0, -0.1, -0.2, -0.3, -0.3, -0.2, -0.1, 0), 0, 0),
                "body": (k(0, -0.02, -0.04, -0.05, -0.05, -0.03, -0.01, 0), 0, k(0, 0, -1, -1, -1, 0, 0, 0)),
                "head": (k(0, -0.04, -0.08, -0.1, -0.1, -0.06, -0.02, 0), 0, 0), **anim._sway(1, k(0, 0.05, 0.1, 0.15, 0.15, 0.1, 0.05, 0))}
    if style == "charge":
        p = _attack(i, n, "lunge", name)
        p["weapon"] = (k(0, -0.03, -0.05, -0.06, 0.03, 0.04, 0.02, 0), k(0, -2, -4, -5, 5, 8, 4, 1), 0)
        p.pop("_fire", None)
        return p
    if style == "fly":
        return {"_all": (k(0, -0.05, -0.1, -0.12, 0.15, 0.18, 0.08, 0), k(0, -1, -2, -3, 3, 5, 2, 0), -6 + k(0, -2, -4, -5, 1, 2, 0, 0)),
                "wing": (k(0, -0.3, -0.6, -0.7, 0.5, 0.6, 0.3, 0), 0, 0), "wing_f": (k(0, -0.3, -0.5, -0.6, 0.4, 0.5, 0.2, 0), 0, 0),
                "weapon": (k(0, -0.05, -0.1, -0.12, 0.1, 0.12, 0.05, 0), k(0, -2, -3, -4, 4, 6, 3, 0), 0),
                "leg_n": (k(0.5, 0.3, 0, -0.2, -0.5, -0.5, -0.2, 0.3), 0, 0), "leg_f": (k(0.45, 0.3, 0, -0.2, -0.45, -0.45, -0.2, 0.3), 0, 0),
                "neck": (k(0, -0.05, -0.1, -0.12, 0.1, 0.12, 0.05, 0), 0, 0), "jaw": (k(0, 0, 0.1, 0.2, 0.3, 0.2, 0.1, 0), 0, 0)}
    if style == "ram":
        return {"weapon": (k(0, 0.02, 0.04, 0.05, -0.02, -0.03, -0.01, 0), k(0, -3, -6, -8, 4, 8, 4, 0), 0),
                "body": (0, 0, k(0, 0, 0, 0, 0, -1, 0, 0))}
    if style == "catapult":
        p = {"weapon": (k(0, -0.08, -0.15, -0.18, 1.0, 1.9, 1.7, 0.8), 0, 0), "body": (0, 0, k(0, 0, 0, 0, -1, -2, -1, 0))}
        if i in (5, 6, 7):
            p["_loosed"] = True
        return p
    return _attack(i, n, style, name)


def death(i, n, style, name):
    if style in ("ram", "catapult"):
        q = (0, 0.1, 0.3, 0.55, 0.8, 0.95, 1.0, 1.0)[i]
        return {"body": (0.12 * q, 0, 4 * q), "weapon": (0.5 * q, 3 * q, 8 * q), "_loosed": True}
    if style == "fly":
        p = _death(i, n, "lunge", name)
        p["_all"] = (0, 0, -6 * (1 - i / (n - 1)))
        return p
    base = {"charge": "lunge", "thrust": "swing", "recoil": "swing", "raise": "swing"}.get(style, style)
    return _death(i, n, base, name)


def idle(i, n, style, name):
    """Standing in the line: breathing, weapon ready, a small shift of weight. Fliers hover."""
    b = math.sin(2 * math.pi * i / n)
    lag = math.sin(2 * math.pi * i / n - 1.0)
    if style == "fly":
        return {"_all": (0, 0, -6 + 1.5 * b), "wing": (0.35 * b, 0, 0), "wing_f": (0.3 * b, 0, 0),
                "leg_n": (0.5, 0, 0), "leg_f": (0.45, 0, 0), "head": (0.03 * lag, 0, 0), **anim._sway(0.15, lag)}
    if style in ("ram", "catapult"):
        return {"body": (0, 0, 0.4 * max(0, b)), "weapon": (0.01 * b, 0, 0)}
    p = _idle(i, n, {"charge": "lunge"}.get(style, style), name)
    p["weapon"] = (0.05 * b, 0, 0)
    return p


def hurt(i, n, style, name):
    """A heavy blow lands: the body snaps back, the head jerks, the weapon dips, then it squares up again."""
    q = (0, 1.0, 0.7, 0.25)[i]
    if style in ("ram", "catapult"):
        return {"_all": (0, -2 * q, 0), "body": (-0.04 * q, 0, -1 * q), "weapon": (0.06 * q, 0, 0)}
    if style == "fly":
        return {"_all": (-0.18 * q, -3 * q, -6 - 2 * q), "wing": (-0.5 * q, 0, 0), "wing_f": (-0.4 * q, 0, 0),
                "leg_n": (0.5, 0, 0), "leg_f": (0.45, 0, 0), "head": (-0.15 * q, 0, 0)}
    if style in ("lunge", "charge"):
        return {"_all": (-0.08 * q, -3 * q, 0), "neck": (-0.25 * q, 0, 0), "head": (-0.2 * q, 0, 0), "jaw": (0.3 * q, 0, 0),
                "leg_n": (0.15 * q, 0, 0), "leg_f": (0.1 * q, 0, 0), "tail": (0.2 * q, 0, 0)}
    return {"_all": (-0.09 * q, -2 * q, 0), "body": (-0.06 * q, 0, 1 * q), "head": (-0.18 * q, 0, 0), "jaw": (0.3 * q, 0, 0),
            "weapon": (0.25 * q, 0, 0), "hand_w": (0.2 * q, 0, 0), "arm_f": (-0.25 * q, 0, 0), "fore_f": (-0.2 * q, 0, 0),
            "arm_n": (0.15 * q, 0, 0), "leg_n": (-0.2 * q, 0, 0), "shin_n": (0.25 * q, 0, 0),
            "leg_f": (0.1 * q, 0, 0), "shin_f": (0.15 * q, 0, 0), **anim._sway(1, -0.3 * q)}


def cry(i, n, style, name):
    """The war cry: the weapon goes up and is shaken at the sky twice, head back, mouth open. Beasts rear and howl."""
    up = (0.2, 0.6, 1.0, 0.85, 1.0, 0.85, 1.0, 0.6)[i]   # lift, then two pumps
    pump = (0, 0, 0, 1, 0, 1, 0, 0)[i]
    if style in ("ram", "catapult"):
        return {"body": (0, 0, -1.0 * pump), "weapon": (-0.02 * up, 0, 0)}
    if style == "fly":
        return {"_all": (-0.12 * up, 0, -8 - 3 * up), "wing": (-0.6 * up + 0.3 * pump, 0, 0), "wing_f": (-0.5 * up + 0.3 * pump, 0, 0),
                "leg_n": (0.5, 0, 0), "leg_f": (0.45, 0, 0), "neck": (-0.2 * up, 0, 0), "head": (-0.2 * up, 0, 0),
                "jaw": (0.4 * up, 0, 0), "weapon": (-0.4 * up, -2 * up, 0)}
    if style in ("lunge", "charge"):    # rear up and howl
        return {"_all": (-0.16 * up, 0, -2 * up), "neck": (-0.4 * up, 0, 0), "head": (-0.3 * up, 0, 0), "jaw": (0.5 * up, 0, 0),
                "leg_n": (-0.3 * up, 0, 0), "leg_f": (-0.25 * up, 0, 0), "leg_n2": (0.15 * up, 0, 0), "leg_f2": (0.15 * up, 0, 0),
                "tail": (-0.2 * up, 0, 0), "weapon": (-0.3 * up, -2 * up, 0)}
    body = {"body": (-0.05 * up, 0, -1.0 * pump), "head": (-0.16 * up, 0, 0), "jaw": (0.5 * up, 0, 0),
            "leg_n": (-0.12 * up, 0, 0), "shin_n": (0.12 * up, 0, 0), "arm_n": (-0.2 * up, 0, 0),
            **anim._sway(1, 0.2 * up - 0.15 * pump)}
    turn = CRY_TURN.get(name, CRY_TURN_STYLE.get(style, 0.5)) * up
    lift = -3 * up - 1.5 * pump
    if style == "shoot":        # the bow goes up in the off hand
        return {**body, "arm_f": (-0.9 * up, 0, -2 * up), "weapon": (-0.6 * up, 0, -3 * up)}
    if style in ("recoil", "raise"):   # held up high
        return {**body, "weapon": (-turn, 0, lift - 2 * up), "hand_w": (-0.15 * turn, 0, 0), "arm_f": (-0.5 * up, 0, -2 * up)}
    # a blade, spear, axe or stone fist turned up at the sky and shaken
    return {**body, "weapon": (-turn, 0, lift), "hand_w": (-0.15 * turn, 0, 0), "arm_f": (-0.4 * up, 0, 0),
            "fore_f": (-0.3 * up, 0, 0)}


# How far (radians) the weapon turns up for the war cry: each is held at its own angle at rest.
CRY_TURN_STYLE = {"swing": 0.45, "thrust": 0.35, "raise": 0.1, "recoil": 0.7, "heavy": 0.7}
CRY_TURN = {"veil_blade": 0.8, "firebrand": 0.6, "banner_bearer": 0.05, "spire_golem": 2.2}


anim.ANIMS.update({"walk": (walk, 8), "idle": (idle, 6), "attack": (attack, 8), "hurt": (hurt, 4), "cry": (cry, 8),
                   "death": (death, 8)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--out", default=OUT)
    ap.add_argument("--sheet")
    ap.add_argument("--gif")
    ap.add_argument("--zoom", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    names = a.names or sorted(allies.UNITS)
    meta_path = os.path.join(a.out, "allies.json")
    meta = json.load(open(meta_path)) if os.path.exists(meta_path) else {}
    allf = {}
    for name in names:
        entry = None
        for an in ANIMS:
            fr = anim.frames(name, an)
            anim.strip([f[0] for f in fr]).save(os.path.join(a.out, f"{name}_{an}.png"))
            anim.strip([f[1] for f in fr]).save(os.path.join(a.out, f"{name}_{an}_n.png"))
            s = fr[0][2]
            if entry is None:
                entry = {"frame": [s.w, s.h], "feet": [s.w // 2, s.bh - 4 + anim.PAD], "anims": {}}
            if an == "walk":   # art pixels from the feet to the top of the head, for its health bar
                top = min((f[0].getbbox() or (0, s.h, 0, 0))[1] for f in fr)
                entry["height"] = entry["feet"][1] - top
            entry["anims"][an] = {"frames": len(fr), "fps": anim.FPS[an], "loop": an in ("walk", "idle")}
            allf[(name, an)] = [f[0] for f in fr]
        meta[name] = entry
        print(name)
    with open(meta_path, "w") as fh:
        json.dump(meta, fh, indent=1, sort_keys=True)
    if a.sheet:
        sheet(names, allf, a.sheet, a.zoom)
    if a.gif:
        preview(names, allf, a.gif, a.zoom)


def _crop(im):
    box = im.getbbox() or (0, 0, im.width, im.height)
    return im.crop(box)


def sheet(names, allf, path, zoom):
    """The rest pose (walk frame 0) of each unit with its name, five to a row, on dark ground."""
    cols = 5
    cell_w, cell_h = 96, 92
    rows = math.ceil(len(names) / cols)
    im = Image.new("RGBA", (cols * cell_w, rows * cell_h), (34, 30, 38, 255))
    d = ImageDraw.Draw(im)
    for k, name in enumerate(names):
        x, y = (k % cols) * cell_w, (k // cols) * cell_h
        f = _crop(allf[(name, "walk")][0])
        im.alpha_composite(f, (x + (cell_w - f.width) // 2, y + cell_h - 14 - f.height))
        d.text((x + 3, y + cell_h - 12), name, fill=(230, 220, 200, 255))
    im.resize((im.width * zoom, im.height * zoom), Image.NEAREST).save(path)
    print(path)


def preview(names, allf, path, zoom):
    """Every unit walking twice, attacking twice and dying, side by side."""
    seq = [("walk", i) for i in range(8)] * 2 + [("idle", i) for i in range(6)] * 2 + [("attack", i) for i in range(8)] * 2 + \
        [("hurt", i) for i in range(4)] + [("idle", 0)] * 3 + [("cry", i) for i in range(8)] * 2 + \
        [("death", i) for i in range(8)] + [("death", 7)] * 6
    cols = 5
    cw, ch = 100, 86
    rows = math.ceil(len(names) / cols)
    frames = []
    for an, i in seq:
        im = Image.new("RGBA", (cols * cw, rows * ch), (40, 44, 40, 255))
        for k, name in enumerate(names):
            f = allf[(name, an)][i]
            x, y = (k % cols) * cw, (k // cols) * ch
            ox = x + (cw - f.width) // 2
            oy = y + ch - f.height + anim.PAD - 6
            im.alpha_composite(f, (max(0, ox), max(0, oy))) if ox >= 0 and oy >= 0 else im.alpha_composite(f.crop((max(0, -ox), max(0, -oy), f.width, f.height)), (max(0, ox), max(0, oy)))
        frames.append(im.convert("RGB").resize((im.width * zoom, im.height * zoom), Image.NEAREST))
    frames[0].save(path, save_all=True, append_images=frames[1:], duration=90, loop=0)
    print(path)


if __name__ == "__main__":
    main()
