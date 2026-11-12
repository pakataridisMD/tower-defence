#!/usr/bin/env python3
"""Animate the thirty kinds of the Unbound (tools/art/pix2d/horde.py) and put them in the game.

For each kind it draws, from the same shapes as the rest pose, a walk (8 frames), a death (8 frames) and its
power (see tools/campaign/horde.py for which power each has), and writes them where the game reads the
hand-drawn enemies:

  assets/art/game/drawn/<id>_walk.png, _death.png, _power.png (and _n normal-map strips), and drawn.json.

Then:  python3 tools/art/gen_game_art.py --enemies && godot --headless --import

Usage:  python3 tools/art/gen_horde_art.py [ids] [--gif preview.gif] [--sheet lineup.png] [--no-write]
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "art", "pix2d"))
sys.path.insert(0, os.path.join(ROOT, "tools", "campaign"))

import anim  # noqa: E402
import horde  # noqa: E402  (adds the thirty to creatures.CREATURES)
import horde as roster_art  # noqa: E402,F401
from creatures import CREATURES  # noqa: E402

import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("horde_roster", os.path.join(ROOT, "tools", "campaign", "horde.py"))
roster = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(roster)

DRAWN = os.path.join(ROOT, "assets", "art", "game", "drawn")
PAD = anim.PAD

# How each kind moves (anim.py styles, plus the three added here).
STYLE = {
    "rimeback": "crab", "mire_eel": "slither", "fogwife": "float", "wailing_widow": "float", "smoke_wraith": "float",
    "spark_wisp": "float", "squall_witch": "float", "gale_harpy": "fly",
    "quarry_hound": "lunge", "umbral_stalker": "lunge", "cinderhound": "lunge", "stormrider": "lunge", "briar_stag": "lunge",
    "geode": "heavy", "menhir": "heavy", "brass_juggernaut": "heavy", "barkhulk": "heavy",
}
# How each shows its power: a pose it strikes (raise, roar, hunker), its attack, a dive under the road or a leap.
# (kind, frames per second, frame held while the power lasts or -1)
POWER_ANIM = {
    "brinecaller": ("raise", 10, -1), "netcaster": ("attack", 14, -1), "mire_eel": ("sink", 12, 5), "fogwife": ("attack", 12, -1),
    "rimeback": ("hunker", 10, -1), "oathbroken": ("roar", 12, -1), "quarry_hound": ("attack", 14, -1),
    "runebearer": ("raise", 10, -1), "geode": ("hunker", 12, -1), "menhir": ("attack", 10, -1),
    "lightdrinker": ("raise", 10, -1), "umbral_stalker": ("attack", 14, -1), "gravecaller": ("raise", 10, -1),
    "wailing_widow": ("attack", 12, -1), "voidmaw": ("attack", 12, -1), "cinderhound": ("roar", 12, -1),
    "smoke_wraith": ("thin", 16, -1), "glass_singer": ("raise", 10, -1), "slagwalker": ("hunker", 14, -1),
    "brass_juggernaut": ("roar", 10, -1), "gale_harpy": ("attack", 14, -1), "spark_wisp": ("attack", 14, -1),
    "voiceless": ("raise", 10, -1), "stormrider": ("roar", 14, -1), "squall_witch": ("attack", 12, -1),
    "briarling": ("roar", 14, -1), "seedsower": ("attack", 12, -1), "greenwitch": ("raise", 10, -1),
    "briar_stag": ("leap", 14, -1), "barkhulk": ("roar", 8, -1),
}
CRAB_LEGS = ("n", "f", "n2", "f2", "n3", "f3", "n4", "f4")


# ------------------------------------------------------------------------------------- the added styles
_walk, _attack, _death, _idle = anim.walk, anim.attack, anim.death, anim.idle


def walk(i, n, style, name):
    ph = 2 * math.pi * i / n
    a, c = math.sin(ph), math.cos(ph)
    lag = math.sin(ph - 0.9)
    if style == "crab":        # eight legs in two alternating sets, the shell bobbing
        p = {"body": (0.02 * a, 0, -1.0 * abs(c)), "weapon": (0.08 * a, 0, 0), "hand_w": (0.1 * c, 0, 0),
             "arm_f": (-0.1 * a, 0, 0), "head": (0.04 * lag, 0, 0)}
        for k, side in enumerate(CRAB_LEGS):
            sgn = 1 if (k // 2 + k) % 2 else -1
            p["leg_" + side] = (0.25 * sgn * a, 0, 0)
            p["shin_" + side] = (0.2 * sgn * c, 0, 0)
        return p
    if style == "slither":     # a wave runs down the body from head to tail
        return {"body": (0, 0, 1.0 * math.sin(ph)), "tail": (0.12 * math.sin(ph - 1.2), 0, 0),
                "tail2": (0.22 * math.sin(ph - 2.2), 0, 0), "neck": (0.06 * math.sin(ph + 0.8), 0, 0),
                "head": (0.04 * math.sin(ph + 1.4), 0, 0), "plume": (0.2 * lag, 0, 0)}
    if style == "fly":         # hovers, wings beating, talons dangling
        return {"_all": (0, 0, -2 + 2.0 * a), "wing": (0.5 * c, 0, 0), "wing_f": (0.45 * c, 0, 0),
                "leg_n": (0.1 * a, 0, 0), "shin_n": (0.2 + 0.1 * c, 0, 0), "leg_f": (0.12 * a, 0, 0),
                "shin_f": (0.25 + 0.1 * c, 0, 0), "head": (0.04 * lag, 0, 0), "hair": (0.2 * lag, 0, 0)}
    return _walk(i, n, style, name)


def attack(i, n, style, name):
    k = lambda *v: v[i]  # noqa: E731
    if style == "crab":        # the great claw rears back and snaps
        return {"weapon": (k(0, -0.3, -0.6, -0.7, 0.3, 0.4, 0.2, 0), 0, 0), "hand_w": (k(0, -0.2, -0.4, -0.5, 0.3, 0.3, 0.1, 0), 0, 0),
                "body": (k(0, -0.03, -0.05, -0.06, 0.05, 0.06, 0.03, 0), 0, k(0, -1, -1, -1, 1, 1, 0, 0))}
    if style == "slither":     # rears and strikes, jaw wide
        return {"neck": (k(0, -0.2, -0.35, -0.4, 0.2, 0.25, 0.1, 0), 0, 0), "head": (k(0, -0.1, -0.2, -0.2, 0.1, 0.1, 0.05, 0), 0, 0),
                "jaw": (k(0, 0.1, 0.2, 0.3, 0.6, 0.6, 0.3, 0), 0, 0), "body": (0, k(0, -1, -2, -2, 3, 4, 2, 0), 0),
                "tail": (k(0, 0.1, 0.15, 0.2, -0.1, -0.1, 0, 0), 0, 0)}
    if style == "fly":         # rises on a big beat and stoops at the target
        return {"_all": (k(0, -0.05, -0.1, -0.15, 0.25, 0.3, 0.15, 0), k(0, -1, -2, -2, 4, 5, 3, 0), k(-2, -4, -6, -7, -3, -2, -2, -2)),
                "wing": (k(0, 0.6, 0.9, 1.0, -0.6, -0.7, -0.3, 0), 0, 0), "wing_f": (k(0, 0.5, 0.8, 0.9, -0.5, -0.6, -0.3, 0), 0, 0),
                "leg_n": (k(0, 0, -0.2, -0.3, -0.8, -0.9, -0.5, 0), 0, 0), "leg_f": (k(0, 0, -0.2, -0.3, -0.7, -0.8, -0.4, 0), 0, 0)}
    return _attack(i, n, style, name)


def death(i, n, style, name):
    if style == "crab":        # legs fold under and the shell drops
        q = (0, 0.15, 0.35, 0.6, 0.85, 1.0, 1.05, 1.0)[i]
        p = {"body": (0.05 * q, 0, 6 * q), "head": (0.4 * q, 0, 4 * q), "weapon": (0.6 * q, 0, 4 * q), "arm_f": (0.4 * q, 0, 4 * q)}
        for k, side in enumerate(CRAB_LEGS):
            p["leg_" + side] = ((0.5 if side.startswith("n") else -0.5) * q * (1 if k < 4 else -1), 0, 4 * q)
            p["shin_" + side] = (0.4 * q, 0, 0)
        return p
    if style == "slither":     # thrashes, then lies still belly up
        q = (0, 0.2, 0.45, 0.7, 0.9, 1.0, 1.0, 1.0)[i]
        tw = (0, 1, -1, 1, -0.5, 0.2, 0, 0)[i]
        return {"neck": (0.3 * tw - 0.1 * q, 0, 2 * q), "head": (0.2 * tw + 0.3 * q, 0, 2 * q), "jaw": (0.4 * q, 0, 0),
                "tail": (-0.2 * tw, 0, 0), "tail2": (0.3 * tw, 0, 0), "body": (0, 0, 1 * q)}
    if style == "fly":
        return _death(i, n, "swing", name) | {"wing": (-0.8 * i / n, 0, 0), "wing_f": (-0.6 * i / n, 0, 0)}
    return _death(i, n, style, name)


def idle(i, n, style, name):
    if style in ("crab", "slither", "fly"):
        return walk(i * 8 // n, 8, style, name)
    return _idle(i, n, style, name)


anim.ANIMS.update({"idle": (idle, 6), "walk": (walk, 8), "attack": (attack, 8), "death": (death, 8)})
anim.STYLE.update(STYLE)
for _n in STYLE:
    if STYLE[_n] in ("crab", "slither", "fly"):
        pass


# ------------------------------------------------------------------------------------- powers
def ease(t):
    return 0.5 - 0.5 * math.cos(math.pi * max(0.0, min(1.0, t)))


def blend(a, b, t):
    return {k: tuple(x + (y - x) * t for x, y in zip(a.get(k, (0, 0, 0)), b.get(k, (0, 0, 0)))) for k in set(a) | set(b)}


RAISE = {"weapon": (-1.7, 0, -2), "hand_w": (-0.3, 0, 0), "arm_n": (-1.4, 0, 0), "arm_f": (-1.6, 0, 0), "head": (-0.35, 0, 0),
         "neck": (-0.3, 0, 0), "body": (-0.06, 0, -1), "cloak": (0.15, 0, 0), "hair": (0.2, 0, 0), "aura": (0.3, 0, -3)}
ROAR = {"weapon": (-1.0, 0, 0), "hand_w": (-0.4, 0, 0), "arm_f": (-1.8, 0, 0), "fore_f": (-0.5, 0, 0), "head": (-0.4, 0, 0),
        "neck": (-0.45, 0, 0), "jaw": (0.4, 0, 0), "body": (-0.08, 0, -1), "leg_n": (-0.22, 0, 0), "leg_f": (0.22, 0, 0),
        "leg_n2": (0.15, 0, 0), "leg_f2": (0.15, 0, 0), "plume": (0.3, 0, 0), "wing": (0.6, 0, 0), "wing_f": (0.5, 0, 0)}
HUNKER = {"body": (0, 0, 5), "head": (0.1, 0, 3), "neck": (0.2, 0, 2), "leg_n": (-0.35, 0, 0), "shin_n": (0.7, 0, 0),
          "leg_f": (-0.35, 0, 0), "shin_f": (0.7, 0, 0), "weapon": (0.25, 0, 2), "hand_w": (-0.4, 0, 0), "arm_f": (0.35, 0, 2),
          "fore_f": (-0.6, 0, 0)}


def power_poses(kind, name):
    if kind == "raise":
        t = [0.0, 0.3, 0.65, 0.9, 1.0, 1.0, 1.0, 0.5]
        return [blend({}, RAISE, ease(x)) | {"_all": (0, 0, d)} for x, d in zip(t, [0, 0, 0, -1, -1, -2, -1, 0])]
    if kind == "roar":
        t = [0.0, 0.35, 0.75, 1.0, 1.0, 1.0, 1.0, 0.45]
        return [blend({}, ROAR, ease(x)) | {"_all": (0, s, 0)} for x, s in zip(t, [0, 0, 0, 0, 1, -1, 1, 0])]
    if kind == "hunker":
        t = [0.0, 0.5, 1.0, 1.0, 1.0, 0.7, 0.35, 0.0]
        return [blend({}, HUNKER, ease(x)) for x in t]
    if kind == "leap":         # crouch, spring up in an arc, land
        arc = [0, 2, -8, -14, -16, -12, -5, 1]
        fwd = [0, -1, 3, 6, 9, 11, 13, 13]
        tuck = [0, 0.3, 0.6, 0.7, 0.7, 0.5, 0.2, 0.1]
        p = []
        for a, f, t in zip(arc, fwd, tuck):
            p.append({"_all": (-0.15 * (a < 0) * (1 if f < 8 else -1), f * 0.4, a), "leg_n": (-t, 0, 0), "shin_n": (t * 1.2, 0, 0),
                      "leg_f": (-t, 0, 0), "shin_f": (t * 1.2, 0, 0), "leg_n2": (t, 0, 0), "shin_n2": (t, 0, 0),
                      "leg_f2": (t, 0, 0), "shin_f2": (t, 0, 0), "neck": (-0.2 * t, 0, 0)})
        return p
    raise ValueError(kind)


def draw(name, pose):
    s = CREATURES[name](pose, PAD)
    return Image.fromarray(np.asarray(s.image()).copy()), Image.fromarray(np.asarray(s.normal_image()).copy())


def power_frames(name):
    kind = POWER_ANIM[name][0]
    if kind == "attack":
        return [(f[0], f[1]) for f in anim.frames(name, "attack")]
    if kind == "sink":         # it dives into the road: each frame lower, cut off at the ground line
        out = []
        base = CREATURES[name](None, PAD)
        ground = base.bh - 3 + PAD
        for i, dy in enumerate([0, 3, 7, 12, 18, 26]):
            im, nm = draw(name, {"_all": (0.05 * i, 0, dy), "neck": (0.15 * i, 0, 0)})
            a = np.asarray(im).copy()
            b = np.asarray(nm).copy()
            a[ground:, :, 3] = 0
            b[ground:, :, 3] = 0
            out.append((Image.fromarray(a), Image.fromarray(b)))
        return out
    if kind == "thin":         # it comes apart into smoke for a moment and pulls back together
        base = anim.frames(name, "idle")
        rng = np.random.default_rng(5)
        noise = rng.random(np.asarray(base[0][0]).shape[:2])
        out = []
        for i, gone in enumerate([0.0, 0.3, 0.55, 0.7, 0.55, 0.3, 0.1, 0.0]):
            im = np.asarray(base[i % 6][0]).copy()
            nm = np.asarray(base[i % 6][1]).copy()
            im[noise < gone, 3] = 0
            nm[noise < gone, 3] = 0
            out.append((Image.fromarray(im), Image.fromarray(nm)))
        return out
    return [draw(name, p) for p in power_poses(kind, name)]


def strip(ims):
    w, h = ims[0].size
    o = Image.new("RGBA", (w * len(ims), h), (0, 0, 0, 0))
    for i, im in enumerate(ims):
        o.paste(im, (i * w, 0))
    return o


# ------------------------------------------------------------------------------------- review sheets
FONT = os.path.join(ROOT, "assets", "fonts", "Silkscreen-Regular.ttf")
TITLE_FONT = os.path.join(ROOT, "assets", "fonts", "PirataOne-Regular.ttf")
GRASS = (46, 58, 42, 255)


def lineup(names, path, zoom=3):
    """A labelled sheet: the six hordes in rows, rest poses on one ground line, name and power under each."""
    rows = [roster.ids_of(h) for h in roster.HOSTS]
    rows = [[n for n in r if n in names] for r in rows]
    rows = [r for r in rows if r]
    ims = {n: CREATURES[n]().image() for n in names}
    crops = {n: ims[n].crop(ims[n].getbbox()) for n in names}
    info = {r[0]: r for r in roster.ROSTER}
    small = ImageFont.truetype(FONT, 7)
    title = ImageFont.truetype(TITLE_FONT, 16)
    cellw = max(max(c.width for c in crops.values()) + 10, 92)
    rowh = [max(crops[n].height for n in r) + 44 for r in rows]
    W = cellw * 5 + 110
    H = sum(rowh) + 40
    sheet = Image.new("RGBA", (W, H), GRASS)
    d = ImageDraw.Draw(sheet)
    d.text((10, 6), "The Unbound - thirty new kinds of the horde", font=title, fill=(236, 220, 180))
    y = 34
    for r, h in zip(rows, rowh):
        host = info[r[0]][2]
        hd = roster.HOSTS[host]
        d.text((8, y + h // 2 - 22), hd["name"].replace("the ", "The "), font=title, fill=(236, 220, 180))
        d.text((8, y + h // 2 - 2), hd["art"].upper(), font=small, fill=(170, 170, 150))
        d.text((8, y + h // 2 + 8), "vs " + hd["campaign"].replace("_", " "), font=small, fill=(150, 150, 130))
        ground = y + h - 34
        for k, n in enumerate(r):
            c = crops[n]
            x = 110 + k * cellw + (cellw - c.width) // 2
            sheet.alpha_composite(c, (x, ground - c.height))
            name, power = info[n][1], info[n][9]
            tw = d.textlength(name.upper(), font=small)
            d.text((110 + k * cellw + (cellw - tw) / 2, ground + 6), name.upper(), font=small, fill=(240, 236, 220))
            pw = d.textlength(power.replace("_", " "), font=small)
            d.text((110 + k * cellw + (cellw - pw) / 2, ground + 17), power.replace("_", " "), font=small, fill=(150, 210, 160))
        y += h
    sheet = sheet.convert("RGB")
    sheet.resize((W * zoom, H * zoom), Image.NEAREST).save(path)
    print(path, sheet.size)


def preview(names, frames, path, zoom=2):
    """Every kind in its horde's row: walk twice, its power, walk, die, lie there."""
    rows = [[n for n in roster.ids_of(h) if n in names] for h in roster.HOSTS]
    rows = [r for r in rows if r]
    seq = [("walk", i) for i in range(8)] * 2 + [("power", i) for i in range(12)] + [("walk", i) for i in range(8)] + \
          [("death", i) for i in range(8)] + [("death", 7)] * 6
    crop = {}
    for n in names:
        boxes = [im.getbbox() for key in ("walk", "power", "death") for im in frames[n][key] if im.getbbox()]
        crop[n] = (min(b[0] for b in boxes) - 2, min(b[1] for b in boxes) - 2, max(b[2] for b in boxes) + 2, max(b[3] for b in boxes) + 2)
    cw = {n: crop[n][2] - crop[n][0] for n in names}
    W = max(sum(cw[n] for n in r) for r in rows)
    rh = [max(crop[n][3] - crop[n][1] for n in r) for r in rows]
    out = []
    for anim_name, i in seq:
        im = Image.new("RGBA", (W, sum(rh)), (46, 58, 42, 255))
        y = 0
        for r, h in zip(rows, rh):
            x = (W - sum(cw[n] for n in r)) // 2
            for n in r:
                fr = frames[n][anim_name]
                f = fr[min(i, len(fr) - 1)].crop(crop[n])
                feet = CREATURES[n]().bh - 4 + PAD - crop[n][1]
                im.alpha_composite(f, (x, y + h - (crop[n][3] - crop[n][1]) + 0))
                x += cw[n]
            y += h
        out.append(im.convert("RGB").resize((W * zoom, sum(rh) * zoom), Image.NEAREST))
    out[0].save(path, save_all=True, append_images=out[1:], duration=95, loop=0)
    print(path, out[0].size)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = sys.argv[1:]
    gif = flags[flags.index("--gif") + 1] if "--gif" in flags else None
    sheet = flags[flags.index("--sheet") + 1] if "--sheet" in flags else None
    args = [a for a in args if a not in (gif, sheet)]
    names = args or [r[0] for r in roster.ROSTER]
    if sheet:
        lineup(names, sheet)
    if "--sheet-only" in flags:
        return
    drawn_path = os.path.join(DRAWN, "drawn.json")
    drawn = json.load(open(drawn_path)) if os.path.exists(drawn_path) else {}
    frames = {}
    for n in names:
        walk_f = anim.frames(n, "walk")
        death_f = anim.frames(n, "death")
        pow_f = power_frames(n)
        frames[n] = {"walk": [f[0] for f in walk_f], "death": [f[0] for f in death_f], "power": [f[0] for f in pow_f]}
        s = walk_f[0][2]
        w, h = s.w, s.h
        assert all(f[0].size == (w, h) for f in pow_f + death_f), n
        if "--no-write" not in flags:
            for key, fr in (("walk", walk_f), ("death", death_f), ("power", pow_f)):
                strip([f[0] for f in fr]).save(os.path.join(DRAWN, f"{n}_{key}.png"))
                strip([f[1] for f in fr]).save(os.path.join(DRAWN, f"{n}_{key}_n.png"))
            kind, fps, hold = POWER_ANIM[n]
            drawn[n] = {"source": n, "frame": [w, h], "feet": [w // 2, s.bh - 4 + PAD], "anims": {
                "walk": {"frames": len(walk_f), "fps": anim.FPS["walk"], "loop": True},
                "death": {"frames": len(death_f), "fps": anim.FPS["death"], "loop": False},
                "power": {"frames": len(pow_f), "fps": fps, "loop": False, "hold": hold,
                          "power": next(r[9] for r in roster.ROSTER if r[0] == n)}}}
        print(n, (w, h), len(pow_f), "power frames")
    if "--no-write" not in flags:
        json.dump(drawn, open(drawn_path, "w"), indent=1, sort_keys=True)
    if gif:
        preview(names, frames, gif)


if __name__ == "__main__":
    main()
