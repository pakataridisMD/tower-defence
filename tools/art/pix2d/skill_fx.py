#!/usr/bin/env python3
"""The player skills' big effects, hand-drawn frame by frame: python3 tools/art/pix2d/skill_fx.py [--preview FILE]

Comets and their impacts, burning ground, the tsunami's wall of water, rock spikes and boulders, thorn vines,
lightning from the sky and the void rift. Drawn the same way as the tower shots in effects.py (banded tones from a hot
core out, ragged edges, rocks lit from the upper left with a dark outline), only much bigger.

Writes assets/art/game/skill_fx/<name>.png, <name>_glow.png (hot pixels the game adds on top so they shine at night)
and skill_fx.json (frame size, frame count, frames per second). The game (SkillFx) places and times them.
"""
from __future__ import annotations

import json
import math
import os
import sys

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from effects import (AMBER, AQUA, BOLT, DUST, FIRE, INK, LEAF, ROCK, SAP, SMOKE, THORN, VOID, Strip,  # noqa: E402
                     _fireball, ease_out, lit_poly, noise, pal)

OUT = os.path.join("assets", "art", "game", "skill_fx")

FOAM = pal("8fb8d0", "c8e4f0", "eef8ff", "ffffff")
DEEP = pal("061a36", "0b2a52", "12406e", "1a5a8c", "2a7ab0", "4a9ccc")
EMBER = pal("3a0c06", "6a1a0a", "a8300e")
SCORCH = pal("140e0c", "241a16", "3a2c24", "54423a")

STRIPS = {}


def effect(fn):
    STRIPS[fn.__name__] = fn
    return fn


# --- Fire: Meteor, Comet Shower, Firestorm, Cataclysm --------------------------------------------------------------


@effect
def comet():
    """A burning rock with a long tail, flying right (the game turns it to its fall)."""
    w, h, r = 56, 26, 8
    s = _fireball(w, h, r, 5100)
    hx, cy = w - r - 2, h / 2
    for i in range(s.n):
        f = s.frame(i)
        # A dark rock in the heart of the flame, its face lit by its own fire.
        rot = i * 0.6
        pts = [(hx + 1 + math.cos(rot + k * 1.26) * 4.6 * (0.8 + 0.2 * ((k * 7) % 3) / 2),
                cy + math.sin(rot + k * 1.26) * 4.2) for k in range(5)]
        lit_poly(f, pts, [EMBER[0], EMBER[1], ROCK[2], AMBER[2]])
    return s


@effect
def comet_impact():
    """The comet lands: a white flash, a fireball that climbs into a mushroom of smoke, a ground ring and debris."""
    W, H, n = 128, 112, 13
    s = Strip(W, H, n, 15)
    cx, gy = W / 2, H - 26  # where it hits the ground
    rng = np.random.default_rng(5200)
    debris = [(rng.uniform(math.pi * 1.05, math.pi * 1.95), rng.uniform(0.5, 1.0), rng.uniform(2.0, 3.6),
               [(rng.uniform(0.7, 1.0), k * math.tau / 5 + rng.uniform(-0.3, 0.3)) for k in range(5)]) for _ in range(12)]
    embers = [(rng.uniform(0, math.tau), rng.uniform(0.5, 1.1)) for _ in range(30)]
    for i in range(n):
        f = s.frame(i)
        t = i / (n - 1)
        nz = noise(W, H, 9.0, 5300 + i // 2, 3)
        # The ring of dust and fire racing out along the ground.
        rr = 10 + 52 * ease_out(min(1, t * 1.5))
        d = f.dist(cx, gy, 0.32)
        ring = np.abs(d - rr + (nz - 0.5) * 6) < (5 - t * 3.5)
        ring &= nz > t * 0.9 - 0.1
        # The column of fire and smoke that climbs and spreads into a cap.
        rise = 50 * ease_out(min(1, t * 1.3))
        cap_y = gy - 8 - rise
        cap_r = 10 + 20 * ease_out(min(1, t * 1.2))
        stem_w = 7 + 5 * t
        stem = (np.abs(f.xx - cx) < stem_w + (nz - 0.5) * 5) & (f.yy < gy) & (f.yy > cap_y)
        cap = f.dist(cx, cap_y, 0.65) / cap_r + (nz - 0.5) * 0.5 < 1.0
        base = f.dist(cx, gy - 6, 0.6) / (14 + 18 * ease_out(min(1, t * 2))) + (nz - 0.5) * 0.5 < 1.0
        shape = stem | cap | base
        heat = 1.15 - t * 1.25 + (nz - 0.5) * 0.6 - np.clip((gy - f.yy) / 120, 0, 1) * 0.3
        heat = heat + np.where(cap, -f.dist(cx, cap_y, 0.65) / cap_r * 0.4, 0) + np.where(base, 0.25 - t * 0.2, 0)
        holes = nz < (t - 0.55) * 1.4
        fire = shape & (heat > 0.2) & ~holes
        smoke = shape & (heat <= 0.2) & ~holes
        f.bands(np.clip(0.75 + heat - t * 0.3 + (nz - 0.5) * 0.3, 0, 0.999), smoke, SMOKE)
        f.bands(np.clip(heat - 0.2, 0, 0.999), fire, FIRE[1:], glow_from=1)
        if i < 2:
            # The white flash where it struck.
            fl = f.dist(cx, gy - 6, 0.7)
            r0 = 14 + i * 12
            f.bands(np.clip(1.2 - fl / r0, 0, 0.999), fl < r0, FIRE[3:], glow_from=0)
        # Burning rock thrown out on arcs.
        for a, sp, sz, shape_k in debris:
            if t > 0.92 or i == 0:
                continue
            x = cx + math.cos(a) * 58 * sp * ease_out(t)
            y = gy + math.sin(a) * 40 * sp * ease_out(t) + 70 * t * t
            rot = t * 5 + a
            lit_poly(f, [(x + math.cos(q + rot) * sz * k, y + math.sin(q + rot) * sz * k) for k, q in shape_k],
                     [EMBER[1], ROCK[1], ROCK[2], AMBER[2]])
        for a, sp in embers:
            if t < 0.08 or t > 0.95:
                continue
            er = (14 + 50 * ease_out(t)) * sp
            x, y = cx + math.cos(a) * er, gy - 10 + math.sin(a) * er * 0.6 + t * t * 20 - 10 * sp
            f.px(x, y, FIRE[4 if t < 0.5 else 3], True)
        f.outline() if i < 9 else None
        # The ring is drawn last so it is not outlined: a soft rush of dust, fire at first.
        if t < 0.7:
            f.bands(np.clip(0.9 - t - np.abs(d - rr) / 12, 0, 0.999), ring & ~f.s.a[:, f.x0:f.x0 + W],
                    DUST if t > 0.3 else FIRE[2:], glow_from=None if t > 0.3 else 1)
    return s


@effect
def crater():
    """The scorched pit a comet leaves: burnt ground, a rocky lip and cracks that still glow."""
    W, H = 72, 36
    s = Strip(W, H, 1, 1)
    f = s.frame(0)
    cx, cy = W / 2, H / 2
    nz = noise(W, H, 5.0, 5400, 3)
    d = f.dist(cx, cy, 0.5)
    burnt = d + (nz - 0.5) * 9 < 33
    f.bands(np.clip(0.2 + (d / 34) * 0.7 + (nz - 0.5) * 0.4, 0, 0.999), burnt, SCORCH)
    lip = np.abs(d - 18 + (nz - 0.5) * 4) < 2.4
    f.bands(np.clip(0.5 - (f.yy - cy) / 18 + (nz - 0.5) * 0.4, 0, 0.999), lip, ROCK[1:4])
    pit = d < 15 + (nz - 0.5) * 3
    f.bands(np.clip(0.3 + (f.yy - cy) / 30, 0, 0.999), pit, SCORCH[:2] + [EMBER[0]])
    rng = np.random.default_rng(5401)
    for k in range(7):
        a = k * math.tau / 7 + rng.uniform(-0.3, 0.3)
        x, y = cx, cy
        pts = [(x, y)]
        for step in range(5):
            a += rng.uniform(-0.6, 0.6)
            x, y = x + math.cos(a) * 5.5, y + math.sin(a) * 2.8
            pts.append((x, y))
        f.line(pts, EMBER[2], True)
        f.line(pts[:3], FIRE[3], True)
    f.bands(np.clip(1 - d / 7, 0, 0.999), d < 7, FIRE[1:5], glow_from=1)
    return s


@effect
def ground_fire():
    """One tongue of flame for a burning field; the game scatters many."""
    W, H, n = 22, 30, 6
    s = Strip(W, H, n, 12)
    for i in range(n):
        f = s.frame(i)
        nz = noise(W, H, 3.0, 5500 + i, 2)
        sway = math.sin(i / n * math.tau) * 2.2
        up = np.clip((H - 2 - f.yy) / (H - 4), 0, 1)
        width = (6.5 - up * 5.2) * (0.9 + 0.2 * math.sin(i * 1.3))
        dx = np.abs(f.xx - W / 2 - sway * up * up)
        shape = (dx < width + (nz - 0.5) * 3) & (up > 0) & (up < 0.98 - (nz - 0.5) * 0.3)
        heat = (1 - dx / np.maximum(width, 0.5)) * (1 - up * 0.7) + (nz - 0.5) * 0.3
        f.bands(np.clip(heat, 0, 0.999), shape, FIRE[1:], glow_from=1)
        # Embers lifting off the tip.
        for k in range(3):
            ey = (H - 8 - ((i * 5 + k * 9) % 22))
            f.px(W / 2 + math.sin(i + k * 2) * 4, ey, FIRE[4], True)
    return s


# --- Water: Tidal Wave, Tsunami, Riptide, Great Deluge ---------------------------------------------------------------


@effect
def tsunami():
    """A stretch of the wall of water, moving right. Tiles top to bottom; the game stacks it down the board."""
    W, H, n = 84, 96, 8
    s = Strip(W, H, n, 12)
    for i in range(n):
        f = s.frame(i)
        ph = i / n * math.tau
        y = f.yy
        # The crest's x along the wall: waves of foam that repeat every tile, rolling along it.
        crest = 58 + 4 * np.sin(y / H * math.tau * 2 + ph) + 2.5 * np.sin(y / H * math.tau * 3 - ph * 2)
        lip = crest + 6 + 2 * np.sin(y / H * math.tau * 4 + ph * 3)
        x = f.xx
        # The water behind the crest: it rises from a thin sheet (left) to the wall at the crest.
        behind = np.clip((x - 4) / (crest - 4), 0, 1)
        nz = noise(W, H + 16, 6.0, 5600 + i, 3)[:H]
        body = (x < crest) & (behind + (nz - 0.5) * 0.35 > 0.12)
        stripes = 0.5 * np.sin(y / 5 + x / 9 - ph * 2)
        f.bands(np.clip(behind * 0.85 + stripes * 0.12 + (nz - 0.5) * 0.25, 0, 0.999), body, DEEP)
        # The curling face: the wall's front, dark at its foot where it throws its shadow ahead.
        face = (x >= crest) & (x < lip)
        f.bands(np.clip(0.75 - (x - crest) / 8 + (nz - 0.5) * 0.3, 0, 0.999), face, AQUA[1:5])
        # Foam on the crest and spray thrown ahead of it.
        foam = (np.abs(x - crest + 1) < 2.4 + (nz - 0.5) * 3) | ((x >= lip - 2) & (x < lip + 1.5) & (nz > 0.45))
        f.bands(np.clip(0.4 + (nz - 0.4) * 1.6, 0, 0.999), foam, FOAM, glow_from=3)
        rng = np.random.default_rng(5650 + i)
        for _ in range(26):
            yy = rng.uniform(0, H)
            cxs = 58 + 4 * math.sin(yy / H * math.tau * 2 + ph) + 8
            f.px(cxs + rng.uniform(0, 14) ** 1.2, yy, FOAM[rng.integers(1, 4)], bool(rng.random() < 0.3))
        # White streaks running back over the body.
        for k in range(5):
            yy = ((k * 23 + i * 3) % H)
            f.line([(crest[int(yy), 0] - 30 + (i * 4) % 10, yy), (crest[int(yy), 0] - 6, yy + 1)], FOAM[1])
    return s


@effect
def wave_spray():
    """A burst of spray where the wave meets an enemy."""
    W, H, n = 40, 40, 7
    s = Strip(W, H, n, 16)
    rng = np.random.default_rng(5700)
    drops = [(rng.uniform(-math.pi * 0.95, -math.pi * 0.05), rng.uniform(0.4, 1.0)) for _ in range(26)]
    for i in range(n):
        f = s.frame(i)
        t = i / (n - 1)
        for a, sp in drops:
            x = W / 2 + math.cos(a) * 18 * sp * ease_out(t)
            y = H - 8 + math.sin(a) * 24 * sp * ease_out(t) + 26 * t * t
            col = FOAM[3] if t < 0.4 else FOAM[2] if t < 0.7 else AQUA[3]
            f.px(x, y, col, t < 0.4)
            f.px(x, y + 1, AQUA[3])
        if t < 0.5:
            d = f.dist(W / 2, H - 8, 0.4)
            f.bands(np.clip(1 - d / (6 + 12 * t), 0, 0.999), d < 6 + 12 * t, FOAM[:3])
    return s


# --- Earth: Earthquake, Rockfall, Worldbreaker -----------------------------------------------------------------------


@effect
def rock_spike():
    """Stone shards punch up out of the ground, hold, and crumble back."""
    W, H, n = 36, 48, 10
    s = Strip(W, H, n, 14)
    rng = np.random.default_rng(5800)
    shards = [(rng.uniform(-9, 9), rng.uniform(16, 34), rng.uniform(3.5, 6.0), rng.uniform(-0.35, 0.35)) for _ in range(4)]
    shards.sort(key=lambda s_: -s_[1])
    gy = H - 6
    for i in range(n):
        f = s.frame(i)
        t = i / (n - 1)
        grow = ease_out(min(1, t * 3.5)) if t < 0.65 else max(0, 1 - (t - 0.65) / 0.35)
        nz = noise(W, H, 4.0, 5810, 2)
        # The ground cracks and heaves around the shards.
        d = f.dist(W / 2, gy, 0.35)
        mound = d + (nz - 0.5) * 4 < 9 + 6 * min(1, t * 3)
        f.bands(np.clip(0.6 - (f.yy - gy) / 6, 0, 0.999), mound & (f.yy > gy - 4), DUST)
        for ox, hgt, wid, lean in shards:
            L = hgt * grow
            if L < 2:
                continue
            bx = W / 2 + ox
            tip = (bx + lean * L, gy - L)
            lit_poly(f, [(bx - wid, gy + 1), (bx - wid * 0.3, gy - L * 0.6), tip, (bx + wid * 0.5, gy - L * 0.5), (bx + wid, gy + 1)], ROCK)
        if t > 0.7:
            # Crumbling: chips fall off.
            for k in range(8):
                x = W / 2 + rng.uniform(-12, 12)
                y = gy - rng.uniform(0, 20) * (1 - (t - 0.7) / 0.3) + (t - 0.7) * 30
                f.px(x, y, ROCK[2])
        f.outline()
        if t < 0.3:
            # The hot glint where the ground splits.
            m = (np.abs(f.yy - gy) < 1.2) & (np.abs(f.xx - W / 2) < 10 * (1 - t * 2))
            f.put(m, AMBER[3], glow=True)
    return s


@effect
def boulder():
    """A falling boulder, tumbling."""
    W, n = 26, 4
    s = Strip(W, W, n, 12)
    rng = np.random.default_rng(5900)
    shape = [(rng.uniform(0.75, 1.0), k * math.tau / 7 + rng.uniform(-0.2, 0.2)) for k in range(7)]
    for i in range(n):
        f = s.frame(i)
        rot = i * math.tau / n / 2
        pts = [(W / 2 + math.cos(q + rot) * 10 * k, W / 2 + math.sin(q + rot) * 9.5 * k) for k, q in shape]
        lit_poly(f, pts, ROCK)
        # A chip of moss and a crack, so the turning shows.
        cx = W / 2 + math.cos(rot + 1) * 4
        cy = W / 2 + math.sin(rot + 1) * 4
        f.px(cx, cy, LEAF[1])
        f.px(cx + 1, cy, LEAF[2])
        f.line([(W / 2 + math.cos(rot + 3) * 6, W / 2 + math.sin(rot + 3) * 6), (W / 2, W / 2)], ROCK[0])
        f.outline()
    return s


@effect
def dust_cloud():
    """A low cloud of dust rolling out where the ground heaves or a boulder lands."""
    W, H, n = 64, 40, 9
    s = Strip(W, H, n, 12)
    for i in range(n):
        f = s.frame(i)
        t = i / (n - 1)
        nz = noise(W, H, 6.0, 6000 + i // 2, 3)
        r = 8 + 24 * ease_out(t)
        d = f.dist(W / 2, H - 12, 0.5) / r
        shape = (d + (nz - 0.5) * 0.6 < 1) & (nz > t * 0.9 - 0.15)
        f.bands(np.clip(0.95 - d * 0.5 - t * 0.6 + (nz - 0.5) * 0.4, 0, 0.999), shape, DUST)
    return s


# --- Nature: Entangle, Thorned Roots, Bramble Field, Wrath of the Wild -------------------------------------------------


@effect
def vines():
    """Thorned vines burst from the ground, lash up and curl, then sink back."""
    W, H, n = 56, 64, 12
    s = Strip(W, H, n, 14)
    rng = np.random.default_rng(6100)
    stems = [(rng.uniform(-16, 16), rng.uniform(28, 46), rng.uniform(-1, 1), rng.uniform(0, math.tau)) for _ in range(6)]
    gy = H - 6
    for i in range(n):
        f = s.frame(i)
        t = i / (n - 1)
        grow = ease_out(min(1, t * 2.8)) if t < 0.7 else max(0.0, 1 - (t - 0.7) / 0.3)
        d = f.dist(W / 2, gy, 0.35)
        f.bands(np.clip(0.6 - d / 30, 0, 0.999), d < 14 * min(1, t * 4), DUST[:3])
        for ox, hgt, bend, ph in stems:
            L = hgt * grow
            if L < 3:
                continue
            pts = []
            steps = 12
            for k in range(steps + 1):
                u = k / steps
                lash = math.sin(u * 2.6 + ph + t * 7) * 5 * u + bend * u * u * 14
                pts.append((W / 2 + ox + lash, gy - u * L))
            for k, (x, y) in enumerate(pts):
                u = k / steps
                wdt = 2.8 * (1 - u * 0.75)
                m = f.disc(x, y, wdt)
                f.bands(np.clip(0.4 + (f.xx - x) * -0.15, 0, 0.999), m, LEAF)
                if k % 3 == 1:
                    side = 1 if k % 2 else -1
                    f.line([(x + side * wdt, y), (x + side * (wdt + 3), y - 2)], THORN[3])
            # A curled tip.
            x, y = pts[-1]
            f.px(x + 1, y - 1, SAP[3])
        f.outline()
        if 0.1 < t < 0.6:
            for k in range(8):
                a = k / 8 * math.tau + t * 3
                f.px(W / 2 + math.cos(a) * 18 * t, gy - 10 - math.sin(a) * 14 * t, SAP[4], True)
    return s


@effect
def bramble():
    """A clump of brambles in a thorn field; the game scatters many and they sway."""
    W, H, n = 28, 22, 4
    s = Strip(W, H, n, 6)
    rng = np.random.default_rng(6200)
    canes = [(rng.uniform(-10, 10), rng.uniform(9, 17), rng.uniform(-0.7, 0.7)) for _ in range(5)]
    gy = H - 3
    for i in range(n):
        f = s.frame(i)
        sway = math.sin(i / n * math.tau) * 1.4
        for ox, hgt, lean in canes:
            pts = [(W / 2 + ox + (lean * u * hgt) + sway * u * u, gy - u * hgt) for u in np.linspace(0, 1, 8)]
            f.line(pts, THORN[1], width=2)
            f.line(pts, LEAF[2])
            for k in (2, 4, 6):
                x, y = pts[k]
                f.px(x + (1 if k % 4 else -1) * 2, y - 1, THORN[3])
        for k in range(3):
            x, y = W / 2 + (k - 1) * 7, gy - 10 - (k % 2) * 3
            f.px(x, y, SAP[3], True)
        f.outline()
    return s


# --- Storm: Thunderstorm, Tempest, Wrath of the Sky ---------------------------------------------------------------


@effect
def lightning():
    """A bolt from the sky to the ground with forks, the brightest frames first."""
    W, H, n = 48, 208, 6
    s = Strip(W, H, n, 20)
    rng = np.random.default_rng(6300)
    path = [(W / 2 + rng.uniform(-8, 8), 0.0)]
    while path[-1][1] < H - 10:
        x, y = path[-1]
        path.append((float(np.clip(x + rng.uniform(-9, 9), 6, W - 6)), y + rng.uniform(10, 18)))
    path[-1] = (W / 2, H - 10)
    forks = []
    for k in range(3, len(path) - 2, 3):
        x, y = path[k]
        a = rng.choice([-1, 1])
        fork = [(x, y)]
        for _ in range(3):
            x, y = x + a * rng.uniform(4, 8), y + rng.uniform(6, 12)
            fork.append((x, y))
        forks.append(fork)
    for i in range(n):
        f = s.frame(i)
        if i in (0, 2):
            # The ground lights up where it lands.
            d = f.dist(W / 2, H - 10, 0.4)
            f.bands(np.clip(1.1 - d / 20, 0, 0.999), d < 20, BOLT[1:], glow_from=0)
        bright = BOLT[4] if i in (0, 2) else BOLT[3] if i in (1, 3) else BOLT[2]
        if i < 5:
            # A wide blue halo, then the white-hot core two pixels thick.
            for dx in (-2, -1, 1, 2):
                f.line([(x + dx, y) for x, y in path], BOLT[0] if abs(dx) == 2 else BOLT[1], True)
            for fork in forks[: (len(forks) if i < 3 else 1)]:
                f.line([(x + 1, y) for x, y in fork], BOLT[1], True)
                f.line(fork, BOLT[2] if i > 1 else BOLT[3], True)
            f.line(path, bright, True)
            f.line([(x + 1, y) for x, y in path], bright if i < 3 else BOLT[2], True)
    return s


# --- Void: Doom, Singularity, Event Horizon, Collapse --------------------------------------------------------------


@effect
def void_rift():
    """The rift on the ground, its arms wheeling in towards the black heart."""
    W, H, n = 96, 52, 8
    s = Strip(W, H, n, 10)
    cx, cy = W / 2, H / 2
    for i in range(n):
        f = s.frame(i)
        dx, dy = f.xx - cx, (f.yy - cy) / 0.5
        r = np.hypot(dx, dy)
        a = np.arctan2(dy, dx)
        spin = i / n * math.tau / 3
        arms = np.sin(a * 3 + r / 6.5 - spin * 3)
        nz = noise(W, H, 5.0, 6400 + i, 2)
        disc = r < 44 + (nz - 0.5) * 6
        v = np.clip(0.55 + arms * 0.35 - r / 90 + (nz - 0.5) * 0.3, 0, 0.999)
        f.bands(v, disc & (arms > -0.2 + r / 120), VOID[:5], glow_from=3)
        f.put(r < 7 + math.sin(i) * 0.8, VOID[0])
        rim = np.abs(r - 8.5) < 1.2
        f.put(rim, VOID[4], glow=True)
    return s


@effect
def void_collapse():
    """The rift closes: a ring falls inward onto a point, then bursts in black and violet."""
    W, n = 120, 11
    s = Strip(W, W, n, 14)
    c = W / 2
    for i in range(n):
        f = s.frame(i)
        nz = noise(W, W, 8.0, 6500 + i, 3)
        d = f.dist(c, c, 0.7)
        if i < 4:
            rr = 50 * (1 - i / 4) + 4
            ring = np.abs(d - rr + (nz - 0.5) * 5) < 3.5
            f.bands(np.clip(1 - np.abs(d - rr) / 4, 0, 0.999) * 0.9, ring, VOID[1:], glow_from=2)
            f.put(d < 3 + i * 1.5, VOID[0])
            continue
        t = (i - 4) / (n - 5)
        r = 10 + 46 * ease_out(t)
        rag = d / r + (nz - 0.5) * 0.5
        holes = nz < t * 0.8 - 0.05
        shape = (rag < 1) & ~holes
        rim = np.clip((rag - 0.45) / 0.55, 0, 0.999) * (1 - t * 0.45)
        f.bands(rim, shape, VOID[:6], glow_from=2)
        if i == 4:
            f.bands(np.clip(1 - d / 14, 0, 0.999), d < 14, VOID[3:], glow_from=0)
    return s


def write_all(folder=OUT):
    os.makedirs(folder, exist_ok=True)
    info = {}
    for name, fn in STRIPS.items():
        s = fn()
        base, glow = s.images()
        base.save(os.path.join(folder, name + ".png"))
        glow_path = os.path.join(folder, name + "_glow.png")
        if s.glow.any():
            glow.save(glow_path)
        elif os.path.exists(glow_path):
            os.remove(glow_path)
        info[name] = {"size": [s.w, s.h], "frames": s.n, "fps": s.fps, "glow": bool(s.glow.any())}
    with open(os.path.join(folder, "skill_fx.json"), "w") as fh:
        json.dump(info, fh, indent=1)
    return info


def preview(path, zoom=3):
    """Every strip on a dark ground, glow added, scaled up for review."""
    from PIL import ImageDraw
    rows = []
    for name, fn in STRIPS.items():
        s = fn()
        base, glow = s.images()
        im = Image.new("RGBA", base.size, (52, 60, 44, 255))
        im.alpha_composite(base)
        g = np.array(glow).astype(np.float32)
        arr = np.array(im).astype(np.float32)
        arr[..., :3] = np.clip(arr[..., :3] + g[..., :3] * (g[..., 3:] / 255) * 0.6, 0, 255)
        rows.append((name, Image.fromarray(arr.astype(np.uint8))))
    width = min(max(r.width for _, r in rows) * zoom + 140, 4000)
    height = sum(r.height * zoom + 8 for _, r in rows)
    sheet = Image.new("RGB", (width, height), (22, 24, 30))
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, r in rows:
        d.text((6, y + 4), name, fill=(230, 220, 190))
        sheet.paste(r.resize((r.width * zoom, r.height * zoom), Image.NEAREST), (140, y))
        y += r.height * zoom + 8
    sheet.save(path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
    else:
        print(json.dumps(write_all())[:300])
