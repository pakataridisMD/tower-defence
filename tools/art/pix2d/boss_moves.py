#!/usr/bin/env python3
"""Boss move sets: six more animations for every boss, drawn from the same pose code as idle/walk/attack/death.

Every boss already has idle, walk, attack (its strike) and death in anim.py. This adds:
  roar   rears up, jaws wide, arms thrown out: arrival, rage, a tower destroyed
  cast   both hands raised, holding the spell: heal, bind, silence, the fireball
  slam   winds up and smashes the ground: summons, shockwaves
  guard  folds in behind its arms and holds there while its barrier stands
  hurt   reels from a heavy blow (barrier broken, a quarter of its life gone)
  rise   comes up out of the ground or the dark: its entrance and a new form
  talk   its walk with the jaw working, for while it speaks

usage: python3 tools/art/pix2d/boss_moves.py [names] --out DIR [--sheet sheet.png] [--gif moves.gif] [--jobs 4]
Runs from a checkout of the story-art branch (tools/art/pix2d with bosses.py, wardens.py, final_bosses.py,
vael_ascend.py). Writes <name>_<anim>.png and _n.png strips for all eleven animations, and moves.json.
"""
import argparse
import json
import math
import os
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw  # noqa: E402

import anim  # noqa: E402
import creatures  # noqa: E402

# The game's bosses, by art id.
BOSSES = ["vael_bare", "vael_bare_wrath", "vael_unmade", "cassivane", "sundered_heart", "ourra", "gorrath", "vesper",
          "ashwick", "vholt", "mother_briar", "cinder_tyrant", "thunderhead", "elder_broodmother", "tidal_leviathan",
          "mountain_titan", "hollow_king", "hollow_shade", "dragon"]

# Drawn facing us (arms out to both sides) rather than side on: their jaw drops instead of swinging, and
# a raised arm on the left turns the other way from one on the right.
FRONT = {"vael_bare", "vael_bare_wrath", "vael_unmade"}

FPS = {"idle": 6, "walk": 10, "attack": 14, "death": 10, "roar": 10, "cast": 10, "slam": 12, "guard": 12,
       "hurt": 14, "rise": 10, "talk": 10}
COUNT = {"roar": 10, "cast": 10, "slam": 8, "guard": 6, "hurt": 6, "rise": 10, "talk": 8}
# Frame that a lasting move holds on in the game (guard while the barrier stands), or absent.
HOLD = {"guard": 5}


def _style(name):
    return anim.STYLE.get(name, "swing")


def _jaw(name, v):
    """Opens the mouth by v (0 shut, 1 wide)."""
    if name in FRONT:
        return (0, 0, 5.0 * v)
    if name in anim.GAPE and anim.GAPE[name].get("idle", [(0, 0, 0)])[0][0] == 0 and \
            any(t[2] for t in anim.GAPE[name]["idle"]):
        return (0, 0, 4.0 * v)
    return (0.5 * v, 0, 0)


def _ease(i, n):
    return 0.5 - 0.5 * math.cos(math.pi * min(1.0, i / max(1, n - 1)))


def _env(i, keys):
    """Piecewise-linear value at frame i from (frame, value) keys."""
    for (f0, v0), (f1, v1) in zip(keys, keys[1:]):
        if f0 <= i <= f1:
            t = (i - f0) / max(1, f1 - f0)
            t = 0.5 - 0.5 * math.cos(math.pi * t)
            return v0 + (v1 - v0) * t
    return keys[-1][1]


# ------------------------------------------------------------------ the moves

def roar(i, n, style, name):
    q = _env(i, [(0, 0), (2, 0.55), (4, 1.0), (7, 1.0), (9, 0.15)])
    shake = (1 if i % 2 else -1) * (1.0 if 4 <= i <= 7 else 0)
    if name in FRONT:
        return {"_all": (0, shake, -7 * q), "body": (0, 0, -2 * q), "arm_f": (-0.4 * q, 0, 0), "fore_f": (0.5 * q, 0, 0),
                "weapon": (0.4 * q, 0, 0), "hand_w": (-0.5 * q, 0, 0), "head": (0, 0, -3 * q), "jaw": _jaw(name, 1.2 * q),
                "leg_n": (0.15 * q, 0, 0), "leg_f": (-0.15 * q, 0, 0), "shin_n": (-0.2 * q, 0, 0), "shin_f": (0.2 * q, 0, 0)}
    if style == "lunge":   # rears up, neck high, wings wide
        return {"body": (-0.18 * q, shake, -4 * q), "neck": (-0.45 * q, 0, 0), "head": (-0.25 * q, 0, 0),
                "jaw": (0.55 * q, 0, 0), "wing": (-0.55 * q, 0, 0), "wing_f": (-0.55 * q, 0, 0), "tail": (0.2 * q, 0, 0),
                "tail2": (0.3 * q, 0, 0), "leg_n": (0.15 * q, 0, 0), "leg_n2": (-0.1 * q, 0, 0), "rider": (-0.2 * q, 0, 0),
                "rhead": (-0.2 * q, 0, 0), "hand_w": (-0.8 * q, 0, 0)}
    if style == "float":
        return {"_all": (0, shake, -6 * q), "weapon": (-0.9 * q, 0, 0), "hand_w": (-0.4 * q, 0, 0), "arm_f": (-0.7 * q, 0, 0),
                "fore_f": (-0.4 * q, 0, 0), "head": (-0.2 * q, 0, 0), "jaw": _jaw(name, q), "aura": (0.3 * q, 0, -3 * q),
                "tail": (0.2 * q, 0, 0), "rider": (-0.2 * q, 0, 0), "rhead": (-0.25 * q, 0, 0), **anim._sway(1, -0.4 * q)}
    # on foot: chest out and back, arms thrown wide, head up, roar
    return {"body": (-0.12 * q, shake, -2 * q), "head": (-0.3 * q, 0, 0), "jaw": _jaw(name, q),
            "weapon": ((-2.4 if style in ("titan", "heavy") else -1.1) * q, 0, 0), "hand_w": (-0.3 * q, 0, 0),
            "arm_f": (-2.3 * q, 0, 0), "fore_f": (-0.5 * q, 0, 0),
            "arm_n": (-1.0 * q, 0, 0), "leg_n": (-0.12 * q, 0, 0), "leg_f": (0.12 * q, 0, 0), "shin_n": (0.1 * q, 0, 0),
            **anim._sway(1, -0.35 * q)}


def cast(i, n, style, name):
    q = _env(i, [(0, 0), (3, 1.0), (7, 1.0), (9, 0.0)])
    hum = 0.06 * math.sin(i * 1.7) if 3 <= i <= 7 else 0   # the hands tremble with the power held
    bob = -1.5 * math.sin(i * 1.3) if 3 <= i <= 7 else 0
    if name in FRONT:
        return {"_all": (0, 0, -4 * q + bob), "arm_f": ((0.6 + hum) * q, 0, 0), "fore_f": (-0.15 * q, 0, 0),
                "weapon": (-(0.6 + hum) * q, 0, 0), "hand_w": (0.15 * q, 0, 0), "head": (0, 0, -1 * q), "jaw": _jaw(name, 0.4 * q)}
    if style == "lunge":   # the neck draws back, the jaws glow open
        return {"body": (-0.08 * q, -2 * q, -2 * q), "neck": (-0.3 * q + hum, 0, 0), "head": (0.15 * q, 0, 0),
                "jaw": (0.3 * q, 0, 0), "wing": (-0.35 * q, 0, 0), "wing_f": (-0.35 * q, 0, 0), "hand_w": (-1.2 * q, 0, 0),
                "rider": (-0.1 * q, 0, 0), "_fire": i >= 3 and i <= 7}
    if style == "float":
        return {"_all": (0, 0, -4 * q + bob), "weapon": (-(1.4 + hum) * q, 0, 0), "hand_w": (-0.6 * q, 0, 0),
                "arm_f": (-(1.3 - hum) * q, 0, 0), "fore_f": (-0.6 * q, 0, 0), "head": (-0.15 * q, 0, 0),
                "jaw": _jaw(name, 0.4 * q), "aura": (0.5 * q, 0, -2 * q), "rider": (-0.1 * q, 0, 0), **anim._sway(1, 0.2 * q)}
    # on foot: plants its feet, raises its weapon high and its free hand to the sky
    return {"body": (-0.06 * q, 0, -1 * q), "head": (-0.18 * q, 0, 0), "jaw": _jaw(name, 0.35 * q),
            "weapon": (-(2.2 + hum) * q, 0, 0), "hand_w": (-0.4 * q, 0, 0), "arm_f": (-(2.0 - hum) * q, 0, 0),
            "fore_f": (-0.3 * q, 0, 0), "arm_n": (-1.8 * q, 0, 0), "leg_n": (-0.1 * q, 0, 0), "leg_f": (0.1 * q, 0, 0),
            **anim._sway(1, 0.15 * q)}


def slam(i, n, style, name):
    up = _env(i, [(0, 0), (3, 1.0), (4, 1.0), (5, -0.2), (7, 0)])     # wind-up height
    down = _env(i, [(0, 0), (3, 0), (4, 0.6), (5, 1.0), (6, 0.8), (7, 0)])   # the blow and the crouch
    shake = (2 if i == 5 else -1 if i == 6 else 0)
    if name in FRONT:
        return {"_all": (0, shake, -8 * up + 6 * down), "arm_f": (1.5 * up - 0.9 * down, 0, 0),
                "fore_f": (0.7 * up - 0.4 * down, 0, 0), "weapon": (-1.5 * up + 0.9 * down, 0, 0),
                "hand_w": (-0.7 * up + 0.4 * down, 0, 0), "head": (0, 0, 2 * down), "jaw": _jaw(name, max(up, down)),
                "leg_n": (-0.3 * down, 0, 0), "leg_f": (0.3 * down, 0, 0), "shin_n": (0.5 * down, 0, 0), "shin_f": (-0.5 * down, 0, 0)}
    if style == "lunge":   # rears onto its hind legs and drops its weight on the front
        return {"body": (-0.25 * up + 0.1 * down, shake, -5 * up + 3 * down), "neck": (-0.35 * up + 0.3 * down, 0, 0),
                "head": (0.25 * down, 0, 0), "jaw": (0.5 * down, 0, 0), "wing": (-0.6 * up + 0.3 * down, 0, 0),
                "wing_f": (-0.6 * up + 0.3 * down, 0, 0), "leg_n": (-0.5 * up, 0, 0), "leg_f": (-0.4 * up, 0, 0),
                "shin_n": (0.6 * up, 0, 0), "shin_f": (0.5 * up, 0, 0), "tail": (0.2 * up, 0, 0), "rider": (-0.2 * up + 0.2 * down, 0, 0),
                "hand_w": (-1.0 * up + 0.4 * down, 0, 0)}
    if style == "float":
        return {"_all": (0, shake, -9 * up + 7 * down), "weapon": (-1.6 * up + 0.8 * down, 0, 0), "hand_w": (-0.5 * up, 0, 0),
                "arm_f": (-1.5 * up + 0.7 * down, 0, 0), "fore_f": (-0.4 * up, 0, 0), "head": (-0.15 * up + 0.2 * down, 0, 0),
                "jaw": _jaw(name, down), "aura": (0.4 * down, 0, 3 * down), "rider": (-0.2 * up + 0.2 * down, 0, 0),
                **anim._sway(1, 0.5 * up - 0.5 * down)}
    legs = anim.LEGS.get(name, 32)
    crouch = 0.12 * legs * down
    # on foot: both arms come up over the head and hammer the ground as the knees give
    return {"body": (-0.1 * up + 0.22 * down, 2 * down + shake, crouch - 2 * up),
            "head": (-0.15 * up + 0.2 * down, 0, 0), "jaw": _jaw(name, max(up, down) * 0.8),
            "weapon": (-2.6 * up + (-1.0 if style in ("titan", "heavy") else 0.5) * down, 0, 0), "hand_w": (-0.4 * up, 0, 0),
            "arm_f": (-2.4 * up - 0.8 * down, 0, 0),
            "fore_f": (-0.3 * up, 0, 0), "arm_n": (-2.0 * up + 0.3 * down, 0, 0),
            "leg_n": (-0.35 * down, 0, crouch * 0.4), "shin_n": (0.6 * down, 0, 0),
            "leg_f": (-0.25 * down, 0, crouch * 0.4), "shin_f": (0.5 * down, 0, 0), **anim._sway(1, 0.3 * up - 0.4 * down)}


def guard(i, n, style, name):
    q = _env(i, [(0, 0), (3, 1.0), (5, 1.0)])
    if name in FRONT:
        return {"_all": (0, 0, 3 * q), "arm_f": (-1.1 * q, 0, 0), "fore_f": (-2.0 * q, 0, 0), "weapon": (1.1 * q, 0, 0),
                "hand_w": (2.0 * q, 0, 0), "head": (0, 0, 4 * q), "leg_n": (-0.2 * q, 0, 0), "leg_f": (0.2 * q, 0, 0),
                "shin_n": (0.35 * q, 0, 0), "shin_f": (-0.35 * q, 0, 0)}
    if style == "lunge":   # wings fold round it like a shield, head tucked
        return {"body": (0.06 * q, 0, 3 * q), "neck": (0.35 * q, 0, 0), "head": (0.3 * q, 0, 0), "wing": (0.5 * q, 0, 0),
                "wing_f": (0.6 * q, 0, 0), "tail": (-0.15 * q, 0, 0), "rider": (0.25 * q, 0, 0), "rhead": (0.2 * q, 0, 0),
                "hand_w": (0.5 * q, 0, 0)}
    if style == "float":
        return {"_all": (0, 0, 2 * q), "weapon": (0.7 * q, 0, 0), "hand_w": (0.6 * q, 0, 0), "arm_f": (-0.9 * q, 0, 0),
                "fore_f": (-0.9 * q, 0, 0), "head": (0.2 * q, 0, 0), "aura": (-0.2 * q, 0, 1 * q), "rider": (0.2 * q, 0, 0),
                **anim._sway(1, 0.2 * q)}
    # on foot: crouches behind its weapon held across the body, free arm over its head
    return {"body": (0.12 * q, -1 * q, 2 * q), "head": (0.22 * q, 0, 0), "weapon": (-1.3 * q, 0, 0), "hand_w": (-0.6 * q, 0, 0),
            "arm_f": (-1.2 * q, 0, 0), "fore_f": (-1.4 * q, 0, 0), "arm_n": (-0.9 * q, 0, 0),
            "leg_n": (-0.25 * q, 0, 0), "shin_n": (0.4 * q, 0, 0), "leg_f": (0.15 * q, 0, 0), "shin_f": (0.3 * q, 0, 0),
            **anim._sway(1, 0.15 * q)}


def hurt(i, n, style, name):
    q = [0, 1.0, 0.85, 0.55, 0.25, 0.0][i]
    if name in FRONT:
        return {"_all": (0.05 * q, -4 * q, 3 * q), "arm_f": (-0.6 * q, 0, 0), "weapon": (0.6 * q, 0, 0),
                "fore_f": (-0.7 * q, 0, 0), "hand_w": (0.7 * q, 0, 0), "head": (-0.15 * q, 0, -2 * q), "jaw": _jaw(name, q)}
    if style == "lunge":
        return {"body": (-0.1 * q, -4 * q, 0), "neck": (-0.3 * q, 0, 0), "head": (-0.3 * q, 0, 0), "jaw": (0.4 * q, 0, 0),
                "wing": (-0.4 * q, 0, 0), "wing_f": (-0.3 * q, 0, 0), "rider": (-0.3 * q, 0, 0), "hand_w": (-0.6 * q, 0, 0)}
    if style == "float":
        return {"_all": (-0.08 * q, -4 * q, -1 * q), "weapon": (-0.5 * q, 0, 0), "arm_f": (0.5 * q, 0, 0),
                "head": (-0.3 * q, 0, 0), "jaw": _jaw(name, q), "aura": (-0.3 * q, 0, 0), "rider": (-0.2 * q, 0, 0),
                **anim._sway(1, 0.6 * q)}
    return {"body": (-0.14 * q, -4 * q, 1 * q), "head": (-0.35 * q, 0, 0), "jaw": _jaw(name, q),
            "weapon": (0.5 * q, 0, 0), "hand_w": (0.3 * q, 0, 0), "arm_f": (0.6 * q, 0, 0), "fore_f": (-0.4 * q, 0, 0),
            "arm_n": (0.4 * q, 0, 0), "leg_n": (0.2 * q, 0, 0), "shin_n": (0.25 * q, 0, 0), "leg_f": (-0.15 * q, 0, 0),
            **anim._sway(1, 0.5 * q)}


RISE_FADE = [1.0, 0.82, 0.62, 0.42, 0.24, 0.1, 0.03, 0, 0, 0]


def rise(i, n, style, name):
    """Up from the ground: kneeling or sunk at first, it stands and lifts its head on the last frames."""
    q = 1.0 - _env(i, [(0, 0), (7, 1.0), (9, 1.0)])          # how far down it still is
    lift = _env(i, [(0, 0), (6, 0), (8, 1.0), (9, 0.6)])     # the head comes up, a breath
    if name in FRONT or style == "float":
        p = {"_all": (0, 0, 16 * q), "weapon": (0.6 * q - 0.4 * lift, 0, 0), "arm_f": (-0.6 * q + 0.4 * lift, 0, 0),
             "head": (0.3 * q - 0.1 * lift, 0, 0), "jaw": _jaw(name, lift), "aura": (0, 0, 4 * q), "rider": (0.3 * q, 0, 0)}
        if name in FRONT:
            p.update({"weapon": (1.2 * q - 0.5 * lift, 0, 0), "hand_w": (1.0 * q, 0, 0), "arm_f": (-1.2 * q + 0.5 * lift, 0, 0),
                      "fore_f": (-1.0 * q, 0, 0), "head": (0, 0, 6 * q - 2 * lift)})
        return p
    if style == "lunge":
        return {"body": (0.1 * q, 0, 10 * q), "neck": (0.5 * q - 0.3 * lift, 0, 0), "head": (0.3 * q - 0.2 * lift, 0, 0),
                "jaw": (0.5 * lift, 0, 0), "wing": (0.6 * q - 0.5 * lift, 0, 0), "wing_f": (0.6 * q - 0.5 * lift, 0, 0),
                "leg_n": (-0.7 * q, 0, 4 * q), "shin_n": (0.9 * q, 0, 0), "leg_f": (-0.6 * q, 0, 4 * q), "shin_f": (0.8 * q, 0, 0),
                "leg_n2": (0.5 * q, 0, 4 * q), "shin_n2": (0.4 * q, 0, 0), "leg_f2": (0.4 * q, 0, 4 * q), "shin_f2": (0.4 * q, 0, 0),
                "rider": (0.3 * q - 0.2 * lift, 0, 0), "hand_w": (-0.8 * lift, 0, 0)}
    # on foot: on one knee, head bowed, and it stands
    drop = 0.45 * anim.LEGS.get(name, 32) * q
    return {"leg_n": (-1.0 * q, 0, drop), "shin_n": (2.0 * q, 0, 0), "leg_f": (-0.5 * q, 0, drop), "shin_f": (1.1 * q, 0, 0),
            "body": (0.3 * q, 2 * q, drop), "head": (0.35 * q - 0.3 * lift, 0, 0), "jaw": _jaw(name, lift),
            "weapon": (-0.2 * q - 0.6 * lift, 0, 0), "arm_f": (-0.2 * q - 0.7 * lift, 0, 0), "arm_n": (-0.6 * lift, 0, 0),
            **anim._sway(1, 0.3 * q)}


def talk(i, n, style, name):
    p = anim.walk(i, n, style, name)
    p["jaw"] = _jaw(name, [0.15, 0.7, 0.9, 0.3, 0.1, 0.8, 0.5, 0.2][i % 8])
    p["head"] = (-0.04 * math.sin(i * 1.6), 0, 0) if name not in FRONT else (0, 0, -0.8 * math.sin(i * 1.6))
    if name in FRONT or style in ("float",):
        p["weapon"] = (p.get("weapon", (0, 0, 0))[0] + 0.12 * math.sin(i * 0.8), 0, 0)
    return p


MOVES = {"roar": roar, "cast": cast, "slam": slam, "guard": guard, "hurt": hurt, "rise": rise, "talk": talk}


def frames(name, move):
    if move in anim.ANIMS:
        return anim.frames(name, move)
    fn, n = MOVES[move], COUNT[move]
    style = _style(name)
    pad = anim.PADS.get(name, anim.PAD)
    out = []
    for i in range(n):
        pose = fn(i, n, style, name)
        pose["_t"] = i
        s = creatures.CREATURES[name](pose, pad)
        im, nm = np.asarray(s.image()).copy(), np.asarray(s.normal_image()).copy()
        if move == "rise" and (name in FRONT or style == "float"):   # it gathers out of the dark
            rng = np.random.default_rng(11)
            gone = rng.random(im.shape[:2]) < RISE_FADE[i]
            im[gone, 3] = 0
            nm[gone, 3] = 0
        out.append((Image.fromarray(im), Image.fromarray(nm), s))
    return out


ALL = ["idle", "walk", "talk", "attack", "roar", "cast", "slam", "guard", "hurt", "rise", "death"]


def build(job):
    name, out_dir, moves = job
    meta = {}
    got = {}
    for move in moves:
        fr = frames(name, move)
        anim.strip([f[0] for f in fr]).save(os.path.join(out_dir, f"{name}_{move}.png"))
        anim.strip([f[1] for f in fr]).save(os.path.join(out_dir, f"{name}_{move}_n.png"))
        s = fr[0][2]
        m = meta.setdefault("frame", [s.w, s.h])
        meta["feet"] = [s.w // 2, s.bh - 4 + s.pad]
        spec = {"frames": len(fr), "fps": FPS[move], "loop": move in ("idle", "walk", "talk")}
        if move in HOLD:
            spec["hold"] = HOLD[move]
        meta.setdefault("anims", {})[move] = spec
        got[move] = [f[0] for f in fr]
        del m
    print(name, flush=True)
    return name, meta, got


def sheet(results, path, scale=0.5):
    """One row per boss, one column block per move, every frame shown small."""
    rows = []
    for name, meta, got in results:
        tiles = []
        for move in ALL:
            if move not in got:
                continue
            ims = got[move]
            w, h = ims[0].size
            strip_im = Image.new("RGBA", (w * len(ims), h + 14), (34, 38, 32, 255))
            for k, im in enumerate(ims):
                strip_im.alpha_composite(im, (k * w, 14))
            ImageDraw.Draw(strip_im).text((4, 2), f"{name} {move}", fill=(230, 220, 200, 255))
            tiles.append(strip_im)
        rows.extend(tiles)
    W = max(t.width for t in rows)
    H = sum(t.height for t in rows)
    o = Image.new("RGBA", (W, H), (34, 38, 32, 255))
    y = 0
    for t in rows:
        o.alpha_composite(t, (0, y))
        y += t.height
    o = o.resize((int(W * scale), int(H * scale)), Image.NEAREST)
    o.convert("RGB").save(path)
    print(path, o.size)


def gif(results, path, zoom=1):
    """Every boss side by side, playing each move in turn with its name on top."""
    seq = []
    for move in ALL:
        n = max(len(got[move]) for _, _, got in results)
        reps = 2 if move in ("idle", "walk", "talk") else 1
        hold = 4 if move not in ("idle", "walk", "talk") else 0
        seq += [(move, k) for _ in range(reps) for k in range(n)] + [(move, n - 1)] * hold
    cells = []
    for name, meta, got in results:
        pad = anim.PADS.get(name, anim.PAD)
        w, h = got["walk"][0].size
        cells.append((name, got, (max(0, pad - 30), max(0, pad - 40), w - max(0, pad - 30), h - max(0, pad - 20))))
    cols = min(7, len(cells))
    grid = [cells[i:i + cols] for i in range(0, len(cells), cols)]
    W = max(sum(c[2][2] - c[2][0] for c in r) for r in grid)
    rh = [max(c[2][3] - c[2][1] for c in r) for r in grid]
    frames_out = []
    for move, k in seq:
        im = Image.new("RGBA", (W, sum(rh) + 24), (46, 52, 44, 255))
        ImageDraw.Draw(im).text((8, 6), move.upper(), fill=(240, 200, 120, 255))
        y = 24
        for r, h in zip(grid, rh):
            x = (W - sum(c[2][2] - c[2][0] for c in r)) // 2
            for name, got, crop in r:
                fr = got[move]
                f = fr[min(k, len(fr) - 1) if move not in ("idle", "walk", "talk") else k % len(fr)].crop(crop)
                im.alpha_composite(f, (x, y + h - f.height))
                x += crop[2] - crop[0]
            y += h
        frames_out.append(im.convert("RGB").resize((im.width * zoom, im.height * zoom), Image.NEAREST))
    frames_out[0].save(path, save_all=True, append_images=frames_out[1:], duration=90, loop=0)
    print(path, frames_out[0].size, len(frames_out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--out", default=os.path.join("art", "pix2d", "boss_moves"))
    ap.add_argument("--moves", default=",".join(ALL))
    ap.add_argument("--sheet")
    ap.add_argument("--gif")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    names = a.names or BOSSES
    moves = a.moves.split(",")
    with ProcessPoolExecutor(a.jobs) as ex:
        results = list(ex.map(build, [(n, a.out, moves) for n in names]))
    mp = os.path.join(a.out, "moves.json")
    old = json.load(open(mp)) if os.path.exists(mp) else {}
    for name, meta, _ in results:
        entry = old.setdefault(name, {"anims": {}})
        entry["frame"], entry["feet"] = meta["frame"], meta["feet"]
        entry["anims"].update(meta["anims"])
    json.dump(old, open(mp, "w"), indent=1, sort_keys=True)
    if a.sheet:
        sheet(results, a.sheet)
    if a.gif:
        gif(results, a.gif)


if __name__ == "__main__":
    main()
