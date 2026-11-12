#!/usr/bin/env python3
"""Shot, hit and blast effects in the hand-drawn 2D style: python3 tools/art/pix2d/effects.py [--preview FILE]

Every effect is a horizontal strip of frames, redrawn frame by frame (never scaled or rotated pixels). Fire, lightning
and magic are drawn in banded tones from a hot core outwards with ragged edges, the way the towers' flames are; rocks,
drops and thorns are lit from the upper left with a dark outline like every other sprite.

Writes assets/art/game/fx/<name>.png (what the game draws, unshaded), <name>_glow.png (the hot pixels, added on top so
they shine at night and bloom) and fx.json (frame size, frame count, frames per second). Shots face right and the game
turns them to face their flight; their centre is the middle of the frame.
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
from kit import hexc  # noqa: E402

OUT = os.path.join("assets", "art", "game", "fx")


def pal(*hexes):
    return [np.array(hexc(h), np.float32) for h in hexes]


FIRE = pal("5a1208", "a8240e", "e0501a", "ff8e2a", "ffc85a", "fff2c0")
SMOKE = pal("1e1a1c", "3a3234", "5a4e4a", "7a6c64")
BOLT = pal("2a2e8a", "4a5ad0", "8aa6ff", "cfe0ff", "ffffff")
AQUA = pal("0e2e58", "17558e", "2a86c4", "62bfe8", "b8ecff", "f2fdff")
SAP = pal("1e4a14", "3a7a22", "62a832", "9ad848", "d8ff8a", "f6ffd8")
LEAF = pal("1e3a18", "2f5e2a", "4f8a34", "7cb444")
THORN = pal("2a2014", "4e3a22", "7a5a30", "b08a52")
ROCK = pal("2a221e", "4e4038", "76665a", "a08e7c", "c8b8a0")
DUST = pal("4e4234", "7a6a54", "a8977a", "cfc0a0")
AMBER = pal("7a3e10", "c06a1a", "f0a030", "ffd070", "fff2c0")
VOID = pal("12061e", "2a1048", "5a2a98", "8e5cd9", "c8a0ff", "f4e8ff")
PUFF = pal("3c3a40", "6a6670", "9a96a0", "cac6cc", "eeeaee")
INK = np.array(hexc("141018"), np.float32)

# How each element's shots and blasts are drawn, and which strip names belong to it. The game picks by element.
ELEMENTS = ("fire", "storm", "nature", "water", "earth", "void")


class Strip:
    """Frames side by side. Each frame has colour, alpha and a glow flag per pixel."""

    def __init__(self, w, h, n, fps):
        self.w, self.h, self.n, self.fps = w, h, n, fps
        self.rgb = np.zeros((h, w * n, 3), np.float32)
        self.a = np.zeros((h, w * n), bool)
        self.glow = np.zeros((h, w * n), bool)

    def frame(self, i):
        return Frame(self, i)

    def images(self):
        a = self.a.astype(np.uint8) * 255
        rgb = np.clip(self.rgb, 0, 255).astype(np.uint8)
        base = Image.fromarray(np.dstack([rgb, a]), "RGBA")
        lum = self.rgb @ np.array([0.3, 0.55, 0.15], np.float32)
        k = np.where(lum > 170, 0.9, 0.45)[..., None]
        g = (self.glow & self.a).astype(np.uint8) * 255
        glow = Image.fromarray(np.dstack([np.clip(self.rgb * k, 0, 255).astype(np.uint8), g]), "RGBA")
        return base, glow


class Frame:
    def __init__(self, strip, i):
        self.s, self.x0 = strip, i * strip.w
        self.w, self.h = strip.w, strip.h
        yy, xx = np.mgrid[0:self.h, 0:self.w]
        self.xx, self.yy = xx.astype(np.float32) + 0.5, yy.astype(np.float32) + 0.5

    def _view(self, arr):
        return arr[:, self.x0:self.x0 + self.w]

    def put(self, mask, col, glow=False):
        rgb, a, g = self._view(self.s.rgb), self._view(self.s.a), self._view(self.s.glow)
        rgb[mask] = col
        a[mask] = True
        g[mask] = glow

    def bands(self, value, mask, tones, glow_from=None):
        """Paints value (0..1) in tones, low to high. Tones from index glow_from up glow."""
        idx = np.clip((value * len(tones)).astype(int), 0, len(tones) - 1)
        for i, t in enumerate(tones):
            m = mask & (idx == i)
            if m.any():
                self.put(m, t, glow=glow_from is not None and i >= glow_from)

    def px(self, x, y, col, glow=False):
        x, y = int(round(x)), int(round(y))
        if 0 <= x < self.w and 0 <= y < self.h:
            m = np.zeros((self.h, self.w), bool)
            m[y, x] = True
            self.put(m, col, glow)

    def line(self, pts, col, glow=False, width=1):
        for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
            steps = int(max(abs(x1 - x0), abs(y1 - y0)) * 2) + 1
            for k in range(steps + 1):
                t = k / steps
                x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
                self.px(x, y, col, glow)
                if width > 1:
                    self.px(x, y + 1, col, glow)

    def disc(self, cx, cy, r, ry=None):
        ry = r if ry is None else ry
        return ((self.xx - cx) / max(r, 0.01)) ** 2 + ((self.yy - cy) / max(ry, 0.01)) ** 2 <= 1.0

    def dist(self, cx, cy, sy=1.0):
        return np.hypot(self.xx - cx, (self.yy - cy) / sy)

    def outline(self, col=INK):
        """A dark line round everything drawn so far that is not glowing."""
        a, g = self._view(self.s.a), self._view(self.s.glow)
        solid = a & ~g
        p = np.pad(solid, 1)
        ring = (p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]) & ~a
        self.put(ring, col)


def noise(w, h, scale, seed, octaves=3):
    """Smooth value noise in 0..1."""
    rng = np.random.default_rng(seed)
    out = np.zeros((h, w), np.float32)
    amp, total = 1.0, 0.0
    for o in range(octaves):
        s = scale / (2 ** o)
        gw, gh = int(w / s) + 3, int(h / s) + 3
        grid = rng.random((gh, gw)).astype(np.float32)
        ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
        gx, gy = xs / s, ys / s
        x0, y0 = gx.astype(int), gy.astype(int)
        fx, fy = gx - x0, gy - y0
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        v = (grid[y0, x0] * (1 - fx) * (1 - fy) + grid[y0, x0 + 1] * fx * (1 - fy)
             + grid[y0 + 1, x0] * (1 - fx) * fy + grid[y0 + 1, x0 + 1] * fx * fy)
        out += v * amp
        total += amp
        amp *= 0.5
    return out / total


def ease_out(t):
    return 1 - (1 - t) ** 2


def lit_poly(f, pts, tones, outline=True):
    """A hard-faced chunk (rock, pod) lit from the upper left: each pixel's tone from where it sits in the shape."""
    from PIL import ImageDraw
    im = Image.new("L", (f.w, f.h), 0)
    ImageDraw.Draw(im).polygon([(x, y) for x, y in pts], fill=255)
    m = np.array(im) > 0
    if not m.any():
        return m
    cx = np.mean([p[0] for p in pts])
    cy = np.mean([p[1] for p in pts])
    r = max(1.0, max(math.hypot(x - cx, y - cy) for x, y in pts))
    shade = 0.55 - ((f.xx - cx) * 0.7 + (f.yy - cy) * 0.75) / (r * 1.6)
    f.bands(np.clip(shade, 0, 0.999), m, tones)
    return m


STRIPS = {}


def effect(fn):
    STRIPS[fn.__name__] = fn
    return fn


# --- Shots ------------------------------------------------------------------------------------------------------


def _fireball(w, h, r, seed):
    s = Strip(w, h, 4, 12)
    hx, cy = w - r - 2, h / 2
    for i in range(4):
        f = s.frame(i)
        n = noise(w, h, 3.0, seed + i, 2)
        # The flame is a teardrop: round at the head, tongues streaming back.
        back = np.clip((hx - f.xx) / (w - r - 3), 0, 1)
        spread = r * (1 - back * 0.75) + (n - 0.5) * 2.2
        d = np.abs(f.yy - cy + back * back * 1.5 * math.sin(i * 1.7)) / np.maximum(spread, 0.3)
        head = f.dist(hx, cy) / r
        body = (f.xx <= hx) & (d < 1.0) & (back < 0.98 - n * 0.35)
        m = (head < 1.0) | body
        heat = np.where(head < 1.0, 1.0 - head * 0.55, 0.0)
        heat = np.maximum(heat, np.where(body, (1 - d) * (1 - back) * 1.1 + (n - 0.5) * 0.3, 0))
        f.bands(np.clip(heat, 0, 0.999), m, FIRE[1:], glow_from=1)
    return s


@effect
def shot_fire():
    return _fireball(16, 9, 3.0, 11)


@effect
def shot_fire_heavy():
    return _fireball(24, 14, 4.6, 12)


def _zigzag(rng, x0, x1, y, amp, steps):
    pts = [(x0, y)]
    for k in range(1, steps):
        pts.append((x0 + (x1 - x0) * k / steps, y + rng.uniform(-amp, amp)))
    pts.append((x1, y))
    return pts


@effect
def shot_storm():
    s = Strip(18, 9, 4, 16)
    rng = np.random.default_rng(21)
    for i in range(4):
        f = s.frame(i)
        pts = _zigzag(rng, 1, 16, 4.5, 2.6, 5)
        f.line(pts, BOLT[1], True, width=2)
        f.line([(x, y - 0.5) for x, y in pts], BOLT[2], True)
        f.line([(x, y) for x, y in pts[2:]], BOLT[4], True)
        f.px(16, 4, BOLT[4], True)
        f.px(16, 5, BOLT[3], True)
    return s


@effect
def shot_storm_heavy():
    s = Strip(17, 17, 4, 14)
    rng = np.random.default_rng(22)
    c = 8.5
    for i in range(4):
        f = s.frame(i)
        for _ in range(4):
            a = rng.uniform(0, math.tau)
            pts = [(c, c)]
            x, y = c, c
            for k in range(3):
                a += rng.uniform(-0.8, 0.8)
                x, y = x + math.cos(a) * 2.6, y + math.sin(a) * 2.6
                pts.append((x, y))
            f.line(pts, BOLT[2], True)
        d = f.dist(c, c)
        n = noise(17, 17, 2.0, 220 + i, 1)
        m = d < 4.2 + (n - 0.5) * 1.5
        f.bands(np.clip(1 - d / 5.0 + 0.1, 0, 0.999), m, BOLT[1:], glow_from=0)
    return s


@effect
def shot_nature():
    s = Strip(14, 7, 2, 8)
    for i in range(2):
        f = s.frame(i)
        # A dark thorn shaft with barbs and a pale glowing tip.
        f.line([(1, 3), (10, 3)], THORN[2])
        f.line([(1, 4), (9, 4)], THORN[1])
        for bx in (3, 6):
            f.px(bx, 2, THORN[2])
            f.px(bx - 1, 1, THORN[1])
            f.px(bx + 1, 5, THORN[1])
        f.outline()
        f.px(11, 3, SAP[3], True)
        f.px(12, 3, SAP[5 - i], True)
        f.px(11, 4, SAP[2], True)
    return s


@effect
def shot_nature_heavy():
    s = Strip(15, 15, 4, 10)
    c = 7.5
    for i in range(4):
        f = s.frame(i)
        # A spiked seed pod that turns as it flies, shedding glowing spores.
        rot = i * math.pi / 8
        spikes = []
        for k in range(14):
            a = rot + k * math.tau / 14
            r = 6.4 if k % 2 == 0 else 3.6
            spikes.append((c + math.cos(a) * r, c + math.sin(a) * r))
        lit_poly(f, spikes, LEAF)
        f.outline()
        f.px(c - 1.5, c - 1.5, SAP[3])
        for k in range(3):
            a = rot * 2 + k * 2.1
            f.px(c - 6 + math.cos(a), c + math.sin(a) * 5, SAP[4], True)
    return s


def _drop(w, h, r, seed, tail):
    s = Strip(w, h, 3, 10)
    hx, cy = w - r - 2, h / 2
    for i in range(3):
        f = s.frame(i)
        back = np.clip((hx - f.xx) / tail, 0, 1)
        wob = math.sin(i * 2.1) * 0.25
        head = f.dist(hx, cy, 1.0 + wob) / r
        body = (f.xx <= hx) & (np.abs(f.yy - cy) < r * (1 - back) * 0.95) & (back < 1)
        m = (head < 1.0) | body
        shade = 0.55 - ((f.xx - hx) * 0.5 + (f.yy - cy) * 0.9) / (r * 2.2) - back * 0.35
        f.bands(np.clip(shade, 0, 0.999), m, AQUA[1:5])
        f.px(hx - r * 0.3, cy - r * 0.45, AQUA[5], True)
        f.outline(np.array(hexc("0a1a34"), np.float32))
        # Spray left behind.
        rng = np.random.default_rng(seed + i)
        for _ in range(3):
            f.px(rng.uniform(0, hx - tail * 0.6), cy + rng.uniform(-r, r), AQUA[3])
    return s


@effect
def shot_water():
    return _drop(15, 9, 2.6, 41, 8)


@effect
def shot_water_heavy():
    return _drop(21, 13, 4.2, 42, 11)


def _rock(size, seed, chips):
    s = Strip(size, size, 4, 10)
    rng = np.random.default_rng(seed)
    c = size / 2
    base = [(rng.uniform(0.7, 1.0), k * math.tau / 7 + rng.uniform(-0.25, 0.25)) for k in range(7)]
    for i in range(4):
        f = s.frame(i)
        rot = i * math.tau / 8
        r = size / 2 - 1.5
        pts = [(c + math.cos(a + rot) * r * k, c + math.sin(a + rot) * r * k) for k, a in base]
        lit_poly(f, pts, ROCK[1:])
        # A chisel line across the face.
        a = rot + 0.6
        f.line([(c - math.cos(a) * r * 0.5, c - math.sin(a) * r * 0.5), (c + math.cos(a) * r * 0.3, c + math.sin(a) * r * 0.3)], ROCK[1])
        f.outline()
        for k in range(chips):
            f.px(rng.uniform(0, 3), c + rng.uniform(-2, 2), DUST[2])
    return s


@effect
def shot_earth():
    return _rock(10, 51, 1)


@effect
def shot_earth_heavy():
    return _rock(15, 52, 2)


def _void(size, seed):
    s = Strip(size, size, 4, 10)
    c = size / 2
    for i in range(4):
        f = s.frame(i)
        n = noise(size, size, 2.5, seed + i, 2)
        d = f.dist(c, c)
        R = size / 2 - 1
        # Violet wisps round a black heart: bright rim, dark middle.
        halo = (d < R * (0.75 + (n - 0.5) * 0.7))
        rim = np.clip(1 - np.abs(d - R * 0.55) / (R * 0.5), 0, 0.999) * 0.85
        f.bands(rim, halo, VOID[1:5], glow_from=1)
        heart = d < R * 0.32
        f.put(heart, VOID[0])
        f.px(c - 0.5, c - 0.5, VOID[2])
    return s


@effect
def shot_void():
    return _void(11, 61)


@effect
def shot_void_heavy():
    return _void(16, 62)


# --- Hits (a shot that struck one enemy) ---------------------------------------------------------------------------

HIT_TONES = {"fire": FIRE[2:], "storm": BOLT[1:], "nature": SAP[1:], "water": AQUA[2:], "earth": AMBER[1:], "void": VOID[2:]}


def _hit(element, seed):
    s = Strip(17, 17, 5, 18)
    tones = HIT_TONES[element]
    rng = np.random.default_rng(seed)
    c = 8.5
    spokes = [rng.uniform(0, math.tau) for _ in range(5)]
    for i in range(5):
        f = s.frame(i)
        t = i / 4
        # A star flash that shrinks, and bits of the element thrown out.
        size = (1 - t) * 6.5 + 1
        d = f.dist(c, c)
        ang = np.arctan2(f.yy - c, f.xx - c)
        star = d < size * (0.35 + 0.65 * np.abs(np.cos(ang * 2 + i * 0.3)) ** 6)
        f.bands(np.clip(1 - d / (size + 0.5) - t * 0.4, 0, 0.999), star, tones, glow_from=0)
        for a in spokes:
            r = 2 + ease_out(t) * 6.5
            x, y = c + math.cos(a) * r, c + math.sin(a) * r + t * t * 2
            col = tones[max(0, len(tones) - 2 - i)]
            if element in ("earth",):
                f.px(x, y, ROCK[3 if i < 3 else 2])
            elif element == "nature":
                f.px(x, y, LEAF[3 - min(i, 2)])
            elif element == "water":
                f.px(x, y, AQUA[4 - min(i, 2)])
                f.px(x, y + 1, AQUA[2])
            else:
                f.px(x, y, col, True)
    return s


for _e in ELEMENTS:
    def _make(e=_e):
        return _hit(e, 70 + ELEMENTS.index(e))
    _make.__name__ = "hit_" + _e
    effect(_make)


# --- Blasts (a shot or skill that bursts over an area) ---------------------------------------------------------------

BLAST = 64  # frame size; the game scales the blast to the shot's splash radius (radius 24 at scale 1)


@effect
def blast_fire():
    s = Strip(BLAST, BLAST, 9, 16)
    c = BLAST / 2
    rng = np.random.default_rng(81)
    embers = [(rng.uniform(0, math.tau), rng.uniform(0.6, 1.1)) for _ in range(14)]
    for i in range(9):
        f = s.frame(i)
        t = i / 8
        n = noise(BLAST, BLAST, 6.0, 800 + i // 2, 3)
        r = 6 + 20 * ease_out(min(1, t * 1.6))
        d = f.dist(c, c + 1, 0.85) / r
        rag = d + (n - 0.5) * 0.45
        shape = rag < 1.0
        # Smoke eats in from the edge as the blast cools, then holes open in it.
        heat = (1 - d) * 1.5 + (n - 0.5) * 0.5 - t * 1.25
        holes = n < (t - 0.45) * 1.3
        fire = shape & (heat > 0) & ~holes
        smoke = shape & (heat <= 0) & (heat > -0.9) & ~holes
        smoke_v = np.clip(0.75 + heat * 0.8 - t * 0.2 + (n - 0.5) * 0.4, 0, 0.999)
        f.bands(smoke_v, smoke, SMOKE)
        f.bands(np.clip(heat, 0, 0.999), fire, FIRE[1:], glow_from=1)
        for a, sp in embers:
            if t < 0.15 or t > 0.95:
                continue
            rr = (8 + 26 * ease_out(t)) * sp
            x, y = c + math.cos(a) * rr, c + math.sin(a) * rr * 0.85 + t * t * 8
            f.px(x, y, FIRE[4 if t < 0.5 else 3], True)
    return s


@effect
def blast_storm():
    s = Strip(BLAST, BLAST, 7, 18)
    c = BLAST / 2
    rng = np.random.default_rng(91)
    for i in range(7):
        f = s.frame(i)
        t = i / 6
        if i < 2:
            # The strike: a white-hot disc and a ring of light.
            d = f.dist(c, c, 0.85)
            r = 6 + i * 5
            f.bands(np.clip(1.1 - d / r, 0, 0.999), d < r, BOLT[1:], glow_from=0)
        # Forked arcs that crawl out and die back.
        arcs = 7 if i < 4 else 4
        for _ in range(arcs):
            a = rng.uniform(0, math.tau)
            x, y = c + math.cos(a) * 3, c + math.sin(a) * 3
            pts = [(x, y)]
            length = (10 + 18 * ease_out(min(1, t * 2))) * rng.uniform(0.6, 1.0)
            for k in range(5):
                a += rng.uniform(-0.7, 0.7)
                step = length / 5
                x, y = x + math.cos(a) * step, y + math.sin(a) * step * 0.85
                pts.append((x, y))
            tone = BOLT[4] if i < 2 else BOLT[3] if i < 4 else BOLT[2]
            f.line(pts, BOLT[1], True, width=2)
            f.line(pts, tone, True)
        for _ in range(6 if i > 1 else 0):
            a, rr = rng.uniform(0, math.tau), rng.uniform(8, 28)
            f.px(c + math.cos(a) * rr, c + math.sin(a) * rr * 0.85, BOLT[3], True)
    return s


@effect
def blast_water():
    s = Strip(BLAST, BLAST, 8, 14)
    c = BLAST / 2
    rng = np.random.default_rng(101)
    drops = [(rng.uniform(0, math.tau), rng.uniform(0.5, 1.0), rng.uniform(0.6, 1.0)) for _ in range(22)]
    for i in range(8):
        f = s.frame(i)
        t = i / 7
        # A ripple ring on the ground with a foam crest.
        rr = 6 + 22 * ease_out(t)
        d = f.dist(c, c + 6, 0.55)
        ring = np.abs(d - rr) < (2.6 - t * 1.5)
        if t < 0.95:
            f.bands(np.clip(1 - np.abs(d - rr) / 2.6 - t * 0.3, 0, 0.999), ring, AQUA[1:5])
        # The splash column rises and falls back.
        col_h = 24 * math.sin(min(1, t * 1.6) * math.pi)
        if col_h > 1:
            n = noise(BLAST, BLAST, 2.0, 1000 + i, 2)
            body = (np.abs(f.xx - c) < 6.5 - (c + 6 - f.yy) / max(col_h, 1) * 4.0 + (n - 0.5) * 2) & (f.yy < c + 7) & (f.yy > c + 6 - col_h)
            shade = 0.6 - (f.xx - c) / 10 - (f.yy - (c + 6 - col_h)) / (col_h * 3)
            f.bands(np.clip(shade, 0, 0.999), body, AQUA[2:6])
        # Drops thrown up in arcs.
        for a, sp, up in drops:
            if t > 0.92:
                continue
            x = c + math.cos(a) * 26 * sp * ease_out(t)
            y = c + 6 + math.sin(a) * 12 * sp * ease_out(t) - up * 28 * t + 40 * t * t
            f.px(x, y, AQUA[4])
            f.px(x + 1, y, AQUA[3])
            f.px(x, y + 1, AQUA[2])
        f.outline(np.array(hexc("0a1a34"), np.float32)) if i < 5 else None
    return s


@effect
def blast_earth():
    s = Strip(BLAST, BLAST, 8, 14)
    c = BLAST / 2
    rng = np.random.default_rng(111)
    rocks = []
    for _ in range(9):
        a = rng.uniform(0, math.tau)
        sz = rng.uniform(1.6, 3.4)
        shape = [(rng.uniform(0.7, 1.0), k * math.tau / 5 + rng.uniform(-0.3, 0.3)) for k in range(5)]
        rocks.append((a, rng.uniform(0.5, 1.0), rng.uniform(0.6, 1.0), sz, shape))
    for i in range(8):
        f = s.frame(i)
        t = i / 7
        # A dust cloud that billows out low and thins.
        n = noise(BLAST, BLAST, 5.0, 1100 + i // 2, 3)
        r = 8 + 20 * ease_out(t)
        d = f.dist(c, c + 4, 0.6) / r
        cloud = (d + (n - 0.5) * 0.5 < 1.0) & (n > t * 0.85 - 0.05)
        if i > 0:
            f.bands(np.clip(0.9 - d * 0.6 - t * 0.5 + (n - 0.5) * 0.3, 0, 0.999), cloud, DUST)
        if i < 2:
            # The crack and flash where it lands.
            f.bands(np.clip(1 - f.dist(c, c + 4, 0.6) / 9, 0, 0.999), f.dist(c, c + 4, 0.6) < 9, AMBER[1:], glow_from=2)
        # Chiselled rubble flung out on arcs.
        for a, sp, up, sz, shape in rocks:
            if t > 0.9:
                continue
            x = c + math.cos(a) * 26 * sp * ease_out(t)
            y = c + 4 + math.sin(a) * 10 * sp * ease_out(t) - up * 26 * t + 36 * t * t
            rot = t * 4
            lit_poly(f, [(x + math.cos(q + rot) * sz * k, y + math.sin(q + rot) * sz * k) for k, q in shape], ROCK[1:])
        f.outline()
    return s


@effect
def blast_nature():
    s = Strip(BLAST, BLAST, 8, 14)
    c = BLAST / 2
    rng = np.random.default_rng(121)
    thorns = [rng.uniform(0, math.tau) for _ in range(9)]
    leaves = [(rng.uniform(0, math.tau), rng.uniform(0.5, 1.0), rng.uniform(0, 6)) for _ in range(16)]
    for i in range(8):
        f = s.frame(i)
        t = i / 7
        # Thorns burst up out of the ground and sink back.
        grow = math.sin(min(1, t * 1.4) * math.pi)
        for a in thorns:
            L = 4 + 20 * grow
            if L < 5:
                continue
            bx, by = c + math.cos(a) * 4, c + 6 + math.sin(a) * 3
            tx, ty = bx + math.cos(a) * L * 0.7, by + math.sin(a) * L * 0.35 - L * 0.8
            nx, ny = -math.sin(a), math.cos(a) * 0.5
            w = 3.2 * min(1, grow + 0.3)
            lit_poly(f, [(bx + nx * w, by + ny * w), (tx, ty), (bx - nx * w, by - ny * w)], LEAF[:2] + THORN[2:])
        f.outline()
        # A puff of glowing spores.
        n = noise(BLAST, BLAST, 4.0, 1200 + i, 2)
        r = 6 + 18 * ease_out(t)
        d = f.dist(c, c, 0.8) / r
        spores = (d < 1) & (n > 0.5 + t * 0.25) & (i > 0)
        f.bands(np.clip(1 - d - t * 0.4 + 0.2, 0, 0.999), spores, SAP[2:], glow_from=1)
        for a, sp, spin in leaves:
            if t > 0.95:
                continue
            x = c + math.cos(a) * 28 * sp * ease_out(t)
            y = c + math.sin(a) * 20 * sp * ease_out(t) + t * t * 10
            f.px(x, y, LEAF[3])
            f.px(x + math.cos(spin + t * 6), y + math.sin(spin + t * 6), LEAF[2])
    return s


@effect
def blast_void():
    s = Strip(BLAST, BLAST, 9, 14)
    c = BLAST / 2
    for i in range(9):
        f = s.frame(i)
        n = noise(BLAST, BLAST, 5.0, 1300 + i, 3)
        if i < 3:
            # It falls inward first: a violet ring closing on a black point.
            rr = 26 * (1 - i / 3) + 3
            d = f.dist(c, c, 0.85)
            ring = np.abs(d - rr + (n - 0.5) * 3) < 2.2
            f.bands(np.clip(1 - np.abs(d - rr) / 3, 0, 0.999) * 0.8, ring, VOID[1:5], glow_from=1)
            f.put(d < 2 + i, VOID[0])
            continue
        # Then it bursts: dark matter with a burning violet rim, torn by holes.
        t = (i - 3) / 5
        r = 6 + 22 * ease_out(t)
        d = f.dist(c, c, 0.85) / r
        rag = d + (n - 0.5) * 0.5
        holes = n < t * 0.75 - 0.05
        shape = (rag < 1) & ~holes
        rim = np.clip((rag - 0.55) / 0.45, 0, 0.999) * (1 - t * 0.5)
        f.bands(rim, shape, VOID[:5], glow_from=2)
    return s


@effect
def death_puff():
    """Dust and a pale breath that rise where an enemy fell; the game tints it towards the enemy's colour."""
    s = Strip(36, 32, 7, 12)
    rng = np.random.default_rng(131)
    blobs = [(rng.uniform(-9, 9), rng.uniform(-2, 3), rng.uniform(3.5, 6.0)) for _ in range(5)]
    for i in range(7):
        f = s.frame(i)
        t = i / 6
        n = noise(36, 32, 3.0, 1400 + i, 2)
        val = np.zeros((32, 36), np.float32)
        m = np.zeros((32, 36), bool)
        for bx, by, br in blobs:
            r = br * (0.6 + ease_out(t) * 0.9)
            x, y = 18 + bx * (0.6 + t * 0.6), 24 + by - t * 12
            d = f.dist(x, y) / r
            inside = d + (n - 0.5) * 0.5 < 1
            m |= inside
            val = np.maximum(val, np.where(inside, 1 - d * 0.6 - (f.yy - y) / (r * 3), 0))
        m &= n > t * 0.8 - 0.1
        f.bands(np.clip(val - t * 0.35, 0, 0.999), m, PUFF)
    return s


def write_all(folder=OUT):
    os.makedirs(folder, exist_ok=True)
    info = {}
    for name, fn in STRIPS.items():
        s = fn()
        base, glow = s.images()
        base.save(os.path.join(folder, name + ".png"))
        if s.glow.any():
            glow.save(os.path.join(folder, name + "_glow.png"))
        elif os.path.exists(os.path.join(folder, name + "_glow.png")):
            os.remove(os.path.join(folder, name + "_glow.png"))
        info[name] = {"size": [s.w, s.h], "frames": s.n, "fps": s.fps, "glow": bool(s.glow.any())}
    with open(os.path.join(folder, "fx.json"), "w") as fh:
        json.dump(info, fh, indent=1)
    return info


def preview(path, zoom=4):
    """Every strip on a dark ground, glow added, scaled up for review."""
    rows = []
    for name, fn in STRIPS.items():
        s = fn()
        base, glow = s.images()
        im = Image.new("RGBA", base.size, (40, 44, 40, 255))
        im.alpha_composite(base)
        g = np.array(glow).astype(np.float32)
        arr = np.array(im).astype(np.float32)
        arr[..., :3] = np.clip(arr[..., :3] + g[..., :3] * (g[..., 3:] / 255) * 0.6, 0, 255)
        rows.append((name, Image.fromarray(arr.astype(np.uint8))))
    W = max(r.width for _, r in rows) * zoom + 160
    H = sum(r.height * zoom + 8 for _, r in rows)
    sheet = Image.new("RGB", (W, H), (22, 24, 30))
    from PIL import ImageDraw
    d = ImageDraw.Draw(sheet)
    y = 0
    for name, r in rows:
        d.text((6, y + 4), name, fill=(230, 220, 190))
        sheet.paste(r.resize((r.width * zoom, r.height * zoom), Image.NEAREST), (160, y))
        y += r.height * zoom + 8
    sheet.save(path)


if __name__ == "__main__":
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])
    else:
        print(json.dumps(write_all(), indent=None)[:400])
