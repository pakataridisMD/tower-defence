#!/usr/bin/env python3
"""Cinematic stills in the hand-drawn 2D style.

Each still is painted at 320x180 and doubled to 640x360 with whole pixels, so backgrounds and characters share one
pixel size. Backgrounds are banded skies, ridges, walls and glows with ordered dithering between bands; characters and
bosses are the same pix2d sprites as the game (never rescaled), lit to sit in the scene's light.

usage: python3 tools/art/pix2d/stills.py [cinematic ids] --out art/pix2d/stills [--sheet sheet.png]
Writes <out>/<cinematic id>/<NN>.png.
"""
from __future__ import annotations

import argparse
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw, ImageFont, ImageOps  # noqa: E402

import creatures  # noqa: E402
import bosses  # noqa: E402,F401
import wardens  # noqa: E402,F401
import final_bosses  # noqa: E402,F401
import people  # noqa: E402

W, H = 320, 180
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
RINGC = [(255, 122, 58), (200, 216, 255), (138, 240, 80), (74, 224, 224), (232, 176, 64), (176, 112, 255)]


def hx(h):
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


class Scene:
    def __init__(self, seed=0):
        self.c = np.zeros((H, W, 3), np.float32)
        self.rng = np.random.default_rng(seed)
        self.ys, self.xs = np.mgrid[0:H, 0:W]
        self.bay = BAYER[self.ys % 4, self.xs % 4]

    # ---- painting helpers -----------------------------------------------------------------------------------------
    def bands(self, top, bottom, y0=0, y1=H, n=7, mask=None):
        """A vertical gradient snapped to n bands, dithered where bands meet."""
        t = np.clip((self.ys - y0) / max(1, y1 - y0), 0, 1)
        q = np.floor(t * (n - 1) + self.bay * 0.999) / (n - 1)
        col = hx(top)[None, None] * (1 - q[..., None]) + hx(bottom)[None, None] * q[..., None]
        m = (self.ys >= y0) & (self.ys < y1)
        if mask is not None:
            m &= mask
        self.c[m] = col[m]

    def blend(self, mask, col, a, steps=4):
        """Mix a colour over a mask in a few flat steps (a in 0..1, may be an array), dithered only where steps meet."""
        a = np.broadcast_to(np.asarray(a, np.float32), (H, W))
        q = np.floor(np.clip(a, 0, 1) * steps + self.bay * 0.999) / steps
        m = mask & (q > 0)
        col = hx(col) if isinstance(col, str) else np.array(col, np.float32)
        self.c[m] = self.c[m] * (1 - q[m, None]) + col * q[m, None]

    def solid_blend(self, mask, col, a):
        """Dithered replacement, for hard things that come and go (dust, mist edges)."""
        a = np.broadcast_to(np.asarray(a, np.float32), (H, W))
        hit = mask & (self.bay < a)
        self.c[hit] = hx(col) if isinstance(col, str) else np.array(col, np.float32)

    def glow(self, cx, cy, r, col, strength=0.8, squash=1.0):
        d = np.hypot(self.xs - cx, (self.ys - cy) / squash) / r
        a = np.clip(1 - d, 0, 1) ** 1.6 * strength
        self.blend(a > 0, col, a)

    def disc(self, cx, cy, r, col, squash=1.0):
        m = np.hypot(self.xs - cx, (self.ys - cy) / squash) <= r
        self.c[m] = hx(col) if isinstance(col, str) else col
        return m

    def stars(self, n, y1=H, cols=((230, 230, 255), (170, 170, 210), (120, 120, 160)), avoid=None):
        for _ in range(n):
            x, y = int(self.rng.integers(0, W)), int(self.rng.integers(0, y1))
            if avoid is not None and avoid[y, x]:
                continue
            self.c[y, x] = cols[int(self.rng.integers(len(cols)))]

    def ridge(self, base, amp, col, seed, freq=1.0, rim=None, jag=0.0):
        """A mountain or hill silhouette; returns its mask. rim lights the top edge."""
        rng = np.random.default_rng(seed)
        x = np.arange(W)
        y = np.full(W, float(base))
        for k in range(1, 5):
            y -= amp / k * np.sin(x / W * math.pi * 2 * freq * k + rng.uniform(0, 6.28))
        if jag:
            y -= np.abs(np.sin(x * 0.37 + rng.uniform(0, 6))) * jag
        top = np.round(y).astype(int)
        m = self.ys >= top[None, :]
        self.c[m] = hx(col)
        if rim:
            edge = m & ~np.roll(m, 1, 0)
            self.c[edge] = hx(rim)
        return m

    def poly(self, pts, col):
        im = Image.new("1", (W, H), 0)
        ImageDraw.Draw(im).polygon([(round(x), round(y)) for x, y in pts], fill=1)
        m = np.asarray(im, bool)
        if col is not None:
            self.c[m] = hx(col) if isinstance(col, str) else col
        return m

    def rect(self, x0, y0, x1, y1, col):
        m = (self.xs >= x0) & (self.xs < x1) & (self.ys >= y0) & (self.ys < y1)
        self.c[m] = hx(col) if isinstance(col, str) else col
        return m

    def line(self, x0, y0, x1, y1, col):
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        for i in range(n + 1):
            x, y = round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n)
            if 0 <= x < W and 0 <= y < H:
                self.c[y, x] = col

    def tower(self, x, base, w, h, col, lit, win=None, crenel=True):
        self.rect(x, base - h, x + w, base, col)
        self.rect(x, base - h, x + 1, base, lit)
        if crenel:
            for k in range(x, x + w, 3):
                self.rect(k, base - h - 2, k + 2, base - h, col)
        if win:
            for wy in range(base - h + 4, base - 4, 7):
                self.rect(x + w // 2 - 1, wy, x + w // 2 + 1, wy + 3, win)

    def wall(self, x0, x1, base, h, col, lit, step=4):
        self.rect(x0, base - h, x1, base, col)
        self.rect(x0, base - h, x1, base - h + 1, lit)
        for k in range(x0, x1, step):
            self.rect(k, base - h - 2, k + step // 2, base - h, col)

    def particles(self, n, cols, y0=0, y1=H, x0=0, x1=W):
        for _ in range(n):
            x, y = int(self.rng.integers(x0, x1)), int(self.rng.integers(y0, y1))
            self.c[y, x] = cols[int(self.rng.integers(len(cols)))]

    def fog(self, y0, y1, col, a=0.5):
        t = np.clip(1 - np.abs(self.ys - (y0 + y1) / 2) / max(1, (y1 - y0) / 2), 0, 1) * a
        self.blend(t > 0, col, t)

    def vignette(self, a=0.55, col=(6, 4, 10)):
        d = np.hypot((self.xs - W / 2) / (W / 2), (self.ys - H / 2) / (H / 2))
        self.blend(d > 0.75, col, np.clip((d - 0.75) * 2.2, 0, 1) * a)

    # ---- characters -----------------------------------------------------------------------------------------------
    def put(self, name, x, feet, flip=False, light=(1, 1, 1), rim=None, sil=None, pose=None, alpha=1.0):
        """Paste a sprite with its feet at (x, feet). light multiplies its colours; sil paints it as a silhouette."""
        s = creatures.CREATURES[name](pose, 30 if pose else 0)
        im = np.asarray(s.image()).astype(np.float32)
        fx, fy = s.w // 2, s.bh - 4 + s.pad
        if flip:
            im = im[:, ::-1]
            fx = s.w - fx
        rgb, a = im[..., :3], im[..., 3] / 255
        rgb = rgb * np.array(light, np.float32)
        if sil is not None:
            rgb[:] = sil
        if rim is not None:                                  # a coloured rim on the side facing the light (left top)
            body = a > 0.6
            edge = body & ~np.roll(body, 1, 1) | body & ~np.roll(body, 1, 0)
            rgb[edge] = rgb[edge] * 0.4 + np.array(rim, np.float32) * 0.6
        x0, y0 = int(x - fx), int(feet - fy)
        self._paste(rgb, a * alpha, x0, y0)
        return s

    def put_image(self, im, x0, y0, alpha=1.0):
        arr = np.asarray(im.convert("RGBA")).astype(np.float32)
        self._paste(arr[..., :3], arr[..., 3] / 255 * alpha, x0, y0)

    def _paste(self, rgb, a, x0, y0):
        h, w = a.shape
        sx0, sy0 = max(0, -x0), max(0, -y0)
        dx0, dy0 = max(0, x0), max(0, y0)
        dx1, dy1 = min(W, x0 + w), min(H, y0 + h)
        if dx1 <= dx0 or dy1 <= dy0:
            return
        rs = rgb[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
        al = a[sy0:sy0 + dy1 - dy0, sx0:sx0 + dx1 - dx0]
        dst = self.c[dy0:dy1, dx0:dx1]
        solid = al > 0.99
        dst[solid] = rs[solid]
        part = (al > 0.05) & ~solid                          # shadows and glass: dither, do not blend
        bay = self.bay[dy0:dy1, dx0:dx1]
        hit = part & (bay < al)
        dst[hit] = rs[hit] * 0.5 + dst[hit] * 0.5

    def image(self):
        im = Image.fromarray(np.clip(self.c, 0, 255).astype(np.uint8), "RGB")
        return im.resize((W * 2, H * 2), Image.NEAREST)


# ---- shared pieces ------------------------------------------------------------------------------------------------
NIGHT = (0.55, 0.6, 0.85)
DUSK = (0.85, 0.72, 0.75)
FIRELIT = (1.05, 0.8, 0.65)


def solenne(sc, cx, base, scale=1.0, lit="e8e0d0", shade="a89c90", glow=True):
    """Solenne: six white ring walls stepping up to the Heartstone at the centre, the Sunstone lens above."""
    for i in range(6):
        w = int((150 - i * 22) * scale)
        h = int((10 + i * 4) * scale)
        y = int(base - i * 6 * scale)
        sc.wall(int(cx - w / 2), int(cx + w / 2), y, h, shade, lit, step=max(3, int(5 * scale)))
        for tx in (int(cx - w / 2), int(cx + w / 2) - 4):
            sc.tower(tx, y, max(3, int(5 * scale)), h + 6, shade, lit)
    if glow:
        sc.glow(cx, base - 48 * scale, 26 * scale, (255, 230, 160), 0.9)
        sc.disc(cx, base - 48 * scale, 3 * scale + 1, (255, 255, 240))
        for i, col in enumerate(RINGC):
            a = -math.pi / 2 + i * math.pi / 3
            sc.c[int(base - 48 * scale + math.sin(a) * 6 * scale), int(cx + math.cos(a) * 6 * scale)] = col
        sc.disc(cx, base - 76 * scale, 5 * scale, (250, 210, 110), squash=0.4)


def flame(sc, x, base, h, cols=((200, 60, 20), (250, 140, 40), (255, 220, 140))):
    for k, col in enumerate(cols):
        hh = h * (1 - k * 0.3)
        w = max(1, 3 - k)
        sc.poly([(x - w, base), (x + w, base), (x + (sc.rng.uniform(-1, 1)), base - hh)], col)


def tiny_army(sc, x0, x1, base, n, col, spear=(150, 150, 160), rows=3):
    for r in range(rows):
        for i in range(n):
            x = x0 + (x1 - x0) * i / n + sc.rng.uniform(-1, 1) + r * 2
            y = base - r * 4
            sc.rect(int(x), int(y - 6), int(x) + 2, int(y), col)
            sc.c[int(y - 7), int(x)] = col
            if i % 2 == 0:
                sc.line(int(x) + 2, int(y - 2), int(x) + 4, int(y - 11), spear)


def crown_gap(sc, cx, cy, s=1.0, edge=(120, 120, 150)):
    pts = [(cx - 14 * s, cy + 8 * s), (cx - 14 * s, cy - 8 * s), (cx - 7 * s, cy), (cx, cy - 12 * s), (cx + 7 * s, cy),
           (cx + 14 * s, cy - 8 * s), (cx + 14 * s, cy + 8 * s)]
    m = sc.poly(pts, (2, 2, 4))
    e = m & ~(np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1))
    sc.c[e] = edge
    return m


def panel(sc, x0, y0, x1, y1, col=(10, 8, 12)):
    sc.rect(x0, y0, x1, y0 + 1, col)
    sc.rect(x0, y1 - 1, x1, y1, col)
    sc.rect(x0, y0, x0 + 1, y1, col)
    sc.rect(x1 - 1, y0, x1, y1, col)


# ---- the prologue -------------------------------------------------------------------------------------------------
def prologue_01():
    """An old painted map coming out of darkness: six kingdoms in a ring, a seventh, colourless, in the middle."""
    sc = Scene(1)
    sc.c[:] = (8, 6, 8)
    sc.bands("c8b088", "a08860", 20, 160, n=5, mask=(sc.xs > 40) & (sc.xs < 280) & (sc.ys > 14) & (sc.ys < 166))
    cx, cy = 160, 90
    names = ["d24a2a", "c8d4f0", "5aa040", "3aa8a8", "c08a40", "8a5ac8"]
    for i, col in enumerate(names):
        a0 = -math.pi / 2 + i * math.pi / 3 - math.pi / 6
        pts = [(cx + math.cos(a0 + k * math.pi / 3 / 6) * r, cy + math.sin(a0 + k * math.pi / 3 / 6) * r * 0.62)
               for r in (34,) for k in range(7)]
        pts += [(cx + math.cos(a0 + k * math.pi / 3 / 6) * (96 + 6 * math.sin(k * 2.1 + i)), cy + math.sin(a0 + k * math.pi / 3 / 6) * (96 + 6 * math.sin(k * 2.1 + i)) * 0.62)
                for k in range(6, -1, -1)]
        m = sc.poly(pts, None)
        sc.blend(m, col, 0.62)
        am = a0 + math.pi / 6
        kx, ky = cx + math.cos(am) * 66, cy + math.sin(am) * 66 * 0.62
        for k, dx in enumerate((-4, -2, 0, 2, 4)):                                  # a crown over each kingdom
            sc.line(kx + dx, ky - 3, kx + dx, ky - 6 - (k % 2) * 2, (90, 60, 30))
        sc.line(kx - 4, ky - 3, kx + 4, ky - 3, (90, 60, 30))
    mid = sc.poly([(cx + math.cos(a) * 30, cy + math.sin(a) * 18) for a in np.linspace(0, 6.28, 20)], None)
    sc.blend(mid, "b8b0a0", 1.0)
    sc.disc(cx, cy, 3, (40, 36, 40))
    # coast, rivers, hatching
    for i in range(14):
        a = i * 0.45
        sc.line(cx + math.cos(a) * 96, cy + math.sin(a) * 60, cx + math.cos(a + 0.45) * 100, cy + math.sin(a + 0.45) * 62, (110, 84, 50))
    sc.particles(260, [(150, 126, 90), (120, 96, 64)], 16, 164, 42, 278)
    # coming out of darkness: heavy vignette, the burnt edge of the parchment
    sc.vignette(1.0)
    d = np.hypot((sc.xs - cx) / 150, (sc.ys - cy) / 90)
    sc.blend(d > 0.7, (8, 6, 8), np.clip((d - 0.7) * 3, 0, 1))
    return sc


def _art_vfx(sc, i, x, top):
    c = RINGC[i]
    if i == 0:      # forge-runes written in the air
        for k in range(3):
            sc.rect(x - 4 + k * 4, top - 6 - k * 3, x - 2 + k * 4, top - 4 - k * 3, c)
        sc.glow(x, top - 6, 10, c, 0.6)
    elif i == 1:    # lightning sung down
        sc.line(x + 2, top - 30, x - 2, top - 18, (240, 240, 255))
        sc.line(x - 2, top - 18, x + 3, top - 10, (240, 240, 255))
        for r in (4, 7):
            sc.line(x + 4, top - r, x + 4 + r, top - r - 2, c)
    elif i == 2:    # a seed sprouting
        sc.line(x, top - 2, x, top - 12, (90, 160, 60))
        sc.line(x, top - 8, x - 4, top - 12, (110, 190, 70))
        sc.line(x, top - 10, x + 4, top - 14, (110, 190, 70))
        sc.glow(x, top - 8, 9, c, 0.5)
    elif i == 3:    # reading ice
        for a in range(6):
            ang = a * math.pi / 3
            sc.line(x, top - 8, x + math.cos(ang) * 6, top - 8 + math.sin(ang) * 6, (220, 250, 255))
    elif i == 4:    # carving a square rune
        for (x0, y0, x1, y1) in ((-4, -12, 4, -12), (4, -12, 4, -4), (-4, -4, 4, -4), (-4, -12, -4, -8)):
            sc.line(x + x0, top + y0, x + x1, top + y1, c)
    else:           # a star-chart traced in the air
        pts = [(x - 6, top - 6), (x - 1, top - 14), (x + 5, top - 9), (x + 3, top - 2)]
        for a, b in zip(pts, pts[1:]):
            sc.line(*a, *b, (150, 120, 220))
        for p in pts:
            sc.c[p[1], p[0]] = (255, 255, 255)


def prologue_02():
    """Six crowned monarchs working their arts; the black-walled capital and a king in black with an empty crown."""
    sc = Scene(2)
    sc.bands("1c1830", "4a3a50", 0, 120, n=6)
    sc.stars(60, 80)
    sc.ridge(122, 6, "2a2434", 3, freq=1.2, rim="4a3e52")
    sc.bands("3a3040", "241e2a", 128, 180, n=4)
    names = ["ignar_king", "aurath_king", "elowen_queen", "thalassa_queen", "orrok_king", "nyxara_queen"]
    for i, n in enumerate(names):
        x = 22 + i * 32
        sc.glow(x, 120, 20, RINGC[i], 0.35, squash=0.6)
        sc.put(n, x, 152, light=(0.9, 0.9, 0.95), rim=RINGC[i])
        _art_vfx(sc, i, x + 4, 86)
    # the middle kingdom's capital on its crossroads, black walls, and the king on his throne
    sc.poly([(232, 150), (250, 104), (300, 100), (318, 150)], (20, 16, 26))
    for x, h in ((240, 40), (254, 58), (270, 70), (286, 54), (302, 38)):
        sc.tower(x, 150, 9, h, (26, 22, 32), (60, 54, 74), win=(120, 110, 140))
    sc.glow(276, 128, 30, (90, 80, 120), 0.4)
    sc.rect(262, 112, 290, 152, (14, 12, 18))
    sc.rect(266, 104, 286, 112, (14, 12, 18))
    sc.put("vael_orrun_king", 276, 152, light=(0.85, 0.85, 0.95), rim=(160, 150, 200))
    panel(sc, 226, 96, 320, 160, (60, 54, 74))
    sc.vignette(0.6)
    return sc


def prologue_03():
    """The High King's armies cross a burning land; behind them the flames freeze into grey glass, a river stops mid-fall."""
    sc = Scene(3)
    sc.bands("2a1418", "8a3a1c", 0, 110, n=7)
    sc.glow(240, 100, 120, (255, 120, 40), 0.5, squash=0.5)
    m = sc.ridge(104, 10, "3a2020", 4, freq=0.8, rim="a04a20")
    # the frozen waterfall at the left: the river hanging still in mid-fall, gone to grey glass
    sc.rect(24, 50, 44, 132, (150, 156, 170))
    for x in range(25, 44, 3):
        sc.line(x, 52, x + 1, 130, (200, 204, 216))
    sc.ridge(126, 4, "2a1c1c", 7, freq=1.5)
    sc.bands("4a2a20", "1e1414", 130, 180, n=5)
    # flames in front burn orange; behind the army (left) they have frozen into grey glass
    for x in range(0, 320, 9):
        h = 10 + (x * 7) % 14
        if x > 150:
            flame(sc, x, 134, h)
        else:
            sc.poly([(x - 3, 134), (x + 3, 134), (x, 134 - h)], (130, 134, 146))
            sc.line(x, 134 - h, x - 1, 132, (200, 204, 216))
    sc.fog(128, 140, (160, 160, 170), 0.3)
    tiny_army(sc, 40, 250, 160, 40, (18, 14, 20), rows=4)
    sc.particles(90, [(255, 170, 60), (255, 220, 140)], 0, 130, 150, 320)
    sc.particles(60, [(180, 180, 190), (120, 120, 130)], 0, 130, 0, 150)
    sc.vignette(0.5)
    return sc


def prologue_04():
    """The six monarchs in a ring around the burning black city, hands joined; the High King flung out through the stars."""
    sc = Scene(4)
    sc.bands("06040c", "1c1028", 0, 100, n=6)
    sc.stars(140, 100)
    # the edge of a starfield tearing, and the king flung out through it
    sc.poly([(130, 0), (190, 0), (176, 30), (150, 34)], (2, 2, 4))
    sc.glow(160, 18, 30, (200, 200, 255), 0.5)
    sc.put("vael_orrun_king", 162, 34, sil=(6, 4, 10), pose={"_all": (2.6, 0, 0)})
    sc.bands("2a1820", "120c12", 100, 180, n=5)
    cx, cy = 160, 132
    sc.glow(cx, cy - 10, 60, (255, 110, 40), 0.7, squash=0.6)
    for x, h in ((140, 30), (150, 44), (162, 52), (174, 40), (184, 26)):
        sc.tower(x, cy + 6, 8, h, (20, 14, 20), (80, 40, 30), win=(255, 140, 50))
    for x in range(132, 192, 6):
        flame(sc, x, cy + 8, 10 + (x * 3) % 9)
    order = [0, 3, 1, 4, 2, 5]      # Fire across from Water, Storm across from Earth, Nature across from Void
    names = ["ignar_king", "aurath_king", "elowen_queen", "thalassa_queen", "orrok_king", "nyxara_queen"]
    spots = [(cx - 110, 150), (cx - 70, 172), (cx + 70, 172), (cx + 110, 150), (cx + 74, 126), (cx - 74, 126)]
    for (x, y), k in sorted(zip(spots, order), key=lambda p: p[0][1]):
        sc.glow(x, y - 30, 22, RINGC[k], 0.4)
        sc.put(names[k], x, y, flip=x > cx, light=FIRELIT, rim=RINGC[k])
    for (x0, y0), (x1, y1) in zip(spots, spots[1:] + spots[:1]):              # a ring of joined light between their hands
        for k in range(0, 11):
            px, py = x0 + (x1 - x0) * k / 10, y0 - 30 + (y1 - y0) * k / 10
            sc.glow(px, py, 4, (255, 240, 200), 0.8)
    sc.vignette(0.6)
    return sc


def prologue_05():
    """The crown shatters into the six-coloured Heartstone; dawn over Solenne, white walls rising on black ruins."""
    sc = Scene(5)
    sc.bands("2a2a5a", "f0b070", 0, 120, n=8)
    sc.glow(160, 120, 140, (255, 200, 120), 0.5, squash=0.5)
    # the six fading into a volcano, a storm, a tree, a sea, a mountain, a starless sky
    for i, x in enumerate((34, 82, 130, 190, 238, 286)):
        sc.glow(x, 40, 16, RINGC[i], 0.45)
    sc.ridge(118, 8, "4a3a48", 11, freq=1.0, rim="d09070")
    sc.rect(0, 140, 320, 180, (20, 16, 22))
    for x in range(0, 320, 7):                                 # black ruins under the new walls
        sc.rect(x, 134 + (x * 13) % 6, x + 4, 142, (26, 20, 28))
    solenne(sc, 160, 142, 1.0)
    # the Heartstone as a six-coloured crystal, the crown's pieces flying from it
    for i, col in enumerate(RINGC):
        a = -math.pi / 2 + i * math.pi / 3
        for r in range(8, 30, 2):
            x, y = 160 + math.cos(a) * r, 94 + math.sin(a) * r * 0.8
            sc.c[int(y), int(x)] = col
    sc.vignette(0.4)
    return sc


def prologue_06():
    """Night. Cassivane Dral alone on a balcony with a gold locket; in the stars over his shoulder, a crown-shaped gap."""
    sc = Scene(6)
    sc.bands("04040c", "1a1a34", 0, 130, n=6)
    gap = crown_gap(sc, 92, 44, 1.6, edge=(50, 50, 70))
    sc.stars(220, 130, avoid=gap)
    solenne(sc, 70, 150, 0.6, lit="5a5870", shade="34324a", glow=False)
    # balcony: stone balustrade
    sc.rect(150, 140, 320, 180, (30, 28, 40))
    sc.rect(150, 136, 320, 140, (60, 58, 76))
    for x in range(156, 320, 10):
        sc.rect(x, 140, x + 4, 162, (44, 42, 58))
    sc.rect(150, 162, 320, 166, (60, 58, 76))
    sc.put("cassivane_marshal", 236, 150, light=(0.45, 0.48, 0.7), rim=(140, 150, 220))
    sc.glow(244, 118, 8, (255, 210, 110), 0.7)
    sc.vignette(0.6)
    return sc


def prologue_07():
    """The Hollow Rift: violet grass, a ring of black pillars singing with stolen light, a black comet, the ground tearing."""
    sc = Scene(7)
    sc.bands("0a0618", "3a2454", 0, 110, n=7)
    sc.stars(120, 110)
    # the black comet with a pale tail
    for k in range(40):
        sc.blend((np.hypot(sc.xs - (250 - k * 3), sc.ys - (24 + k)) < 3 - k * 0.05), (150, 130, 200), 0.6 - k * 0.014)
    sc.disc(250, 24, 4, (4, 2, 8))
    sc.ridge(110, 6, "2a1c3a", 12, freq=1.4, rim="5a4078")
    sc.bands("4a3070", "1e1430", 112, 180, n=5)
    sc.particles(500, [(110, 80, 160), (80, 56, 120), (140, 110, 190)], 112, 180)
    # the crack at the centre: nothing inside, violet at its lips
    crack = sc.poly([(120, 150), (150, 140), (170, 146), (200, 138), (214, 150), (188, 160), (160, 156), (136, 162)], (0, 0, 0))
    e = crack & ~np.roll(crack, 1, 0)
    sc.c[e] = (190, 140, 255)
    sc.glow(166, 150, 50, (160, 100, 240), 0.35, squash=0.4)
    for i, (x, h) in enumerate(((60, 50), (98, 62), (232, 60), (272, 48), (130, 40), (200, 42))):
        base = 150 if i < 4 else 128
        sc.rect(x, base - h, x + 9, base, (12, 8, 18))
        sc.rect(x, base - h, x + 1, base, (60, 44, 90))
        for y in range(base - h + 4, base - 4, 6):
            sc.c[y, x + 4] = RINGC[(i + y) % 6]
    sc.vignette(0.5)
    return sc


def prologue_08():
    """Oswin at the lip of the Crack with his lantern-staff raised; Spirewright towers burning behind; grey shapes crawling out."""
    sc = Scene(8)
    sc.bands("0c0814", "3a2848", 0, 120, n=7)
    sc.stars(80, 70)
    for i, x in enumerate((20, 66, 112, 210, 256, 302)):                       # a line of towers burning in six colours
        sc.tower(x - 5, 118, 10, 34, (34, 30, 42), (80, 74, 96), win=RINGC[i])
        sc.glow(x, 80, 16, RINGC[i], 0.6)
        flame(sc, x, 84, 12, (tuple(int(c * 0.6) for c in RINGC[i]), RINGC[i], (255, 255, 240)))
    sc.ridge(122, 3, "2a1c36", 13, freq=1.2)
    sc.bands("3a2a4a", "18101e", 124, 180, n=5)
    crack = sc.poly([(150, 180), (176, 150), (220, 146), (262, 152), (300, 180)], (0, 0, 0))
    sc.glow(226, 166, 60, (150, 90, 220), 0.4, squash=0.4)
    for x, d in ((196, 1), (234, -1), (262, -1)):                               # grey things crawling out
        sc.put("ghost", x, 168, flip=d < 0, light=(0.5, 0.5, 0.55), alpha=0.85)
    sc.put("skeleton", 214, 172, flip=True, sil=(70, 70, 78))
    sc.glow(108, 110, 50, (255, 220, 140), 0.55)
    sc.put("oswin_grey", 112, 168, light=(1.0, 0.92, 0.8), rim=(255, 230, 160))
    sc.vignette(0.5)
    return sc


def prologue_09():
    """White light; the Crack slams almost shut; Oswin falls into the dark, his lantern out; one spark drifts after him."""
    sc = Scene(9)
    sc.bands("ffffff", "c8c0e0", 0, 50, n=4)
    sc.bands("3a3050", "000000", 50, 180, n=7)
    sc.poly([(0, 46), (320, 46), (320, 56), (176, 52), (160, 60), (144, 52), (0, 56)], (20, 16, 26))
    sc.line(144, 52, 176, 52, (255, 255, 255))
    sc.glow(160, 50, 120, (255, 255, 255), 0.6, squash=0.3)
    sc.put("oswin_grey", 150, 128, light=(0.35, 0.33, 0.42), rim=(240, 240, 255), pose={"_all": (2.4, 0, 0)})
    sc.c[164, 168] = (255, 220, 140)
    sc.c[163, 168] = (255, 255, 220)
    sc.glow(168, 164, 5, (255, 200, 120), 0.5)
    sc.vignette(0.7)
    return sc


def prologue_10():
    """Six quick cuts: the six lands driven mad (grey volcano, black stormcloud, rotting tree, frozen sea, grey-eyed mountain, starless sky)."""
    sc = Scene(10)
    sc.c[:] = (8, 6, 10)
    cells = [(2, 2), (108, 2), (214, 2), (2, 91), (108, 91), (214, 91)]
    for i, (x0, y0) in enumerate(cells):
        x1, y1 = x0 + 104, y0 + 87
        m = (sc.xs >= x0) & (sc.xs < x1) & (sc.ys >= y0) & (sc.ys < y1)
        sky = [("3a3a40", "8a8a8e"), ("101018", "3a3a4a"), ("2a2a24", "6a6a58"), ("1a2a38", "6a8a9a"), ("2a2620", "6a6458"), ("000000", "0a0a12")][i]
        sc.bands(sky[0], sky[1], y0, y1, n=5, mask=m)
        cx = (x0 + x1) // 2
        if i == 0:
            sc.poly([(x0 + 10, y1), (cx - 8, y0 + 34), (cx + 8, y0 + 34), (x1 - 10, y1)], (50, 46, 50))
            for k in range(5):
                sc.glow(cx + sc.rng.uniform(-6, 6), y0 + 26 - k * 5, 8, (220, 220, 226), 0.5)
        elif i == 1:
            for k in range(7):
                sc.disc(x0 + 14 + k * 13, y0 + 34 + (k % 2) * 6, 12, (14, 14, 22))
            sc.disc(cx, y0 + 50, 38, (200, 200, 230), squash=0.2)
            sc.disc(cx, y0 + 50, 35, (14, 14, 22), squash=0.18)
        elif i == 2:
            sc.rect(cx - 5, y0 + 30, cx + 5, y1, (60, 54, 46))
            for k in range(8):
                a = -math.pi / 2 + (k - 3.5) * 0.35
                sc.line(cx, y0 + 34, cx + math.cos(a) * 34, y0 + 34 + math.sin(a) * 26, (70, 64, 56))
            sc.particles(30, [(150, 150, 140)], y0 + 10, y1, x0 + 10, x1 - 10)
        elif i == 3:
            for k in range(6):
                sc.poly([(x0 + k * 18, y1), (x0 + k * 18 + 10, y0 + 40 + (k % 3) * 8), (x0 + k * 18 + 20, y1)], (170, 200, 214))
        elif i == 4:
            sc.poly([(x0, y1), (cx, y0 + 16), (x1, y1)], (90, 84, 76))
            for ex in (cx - 8, cx + 4):
                sc.rect(ex, y0 + 44, ex + 5, y0 + 48, (200, 200, 206))
        else:
            gap = crown_gap(sc, cx, y0 + 44, 1.2, edge=(90, 90, 110))
        panel(sc, x0, y0, x1, y1, (60, 56, 64))
    return sc


def prologue_11():
    """Refugees with carts on an ash road; Tamsin Reed waving them on with her lantern-pole."""
    sc = Scene(11)
    sc.bands("4a3a40", "b08060", 0, 100, n=7)
    sc.glow(280, 90, 80, (255, 140, 60), 0.4, squash=0.5)
    for x in (260, 290, 310):
        for k in range(6):
            sc.glow(x - k * 4, 80 - k * 12, 10 + k * 2, (70, 60, 64), 0.6)
    sc.ridge(100, 6, "5a4a48", 14, freq=1.1, rim="8a6a5a")
    sc.bands("7a6a62", "3a3030", 104, 180, n=5)
    road = sc.poly([(0, 150), (320, 118), (320, 132), (0, 176)], (110, 100, 96))
    sc.particles(300, [(140, 130, 124), (90, 82, 80)], 110, 180)
    for i, x in enumerate(range(150, 320, 26)):                            # carts and people heading away down the road
        y = 150 - (x - 150) * 0.18
        sc.rect(x, int(y) - 7, x + 12, int(y) - 1, (70, 50, 34))
        sc.disc(x + 2, y, 2, (30, 24, 20))
        sc.disc(x + 10, y, 2, (30, 24, 20))
        for k in range(3):
            sc.rect(x - 6 - k * 5, int(y) - 8, x - 4 - k * 5, int(y), (40 + k * 6, 34, 36))
            sc.c[int(y) - 9, x - 5 - k * 5] = (200, 160, 130)
    sc.put("soldier", 52, 166, light=(0.95, 0.9, 0.85))
    sc.glow(76, 108, 22, (255, 210, 120), 0.5)
    sc.put("tamsin", 86, 170, light=(1.0, 0.95, 0.9), rim=(255, 220, 160))
    sc.particles(70, [(160, 150, 150), (200, 190, 186)], 0, 120)
    sc.vignette(0.45)
    return sc


def prologue_12():
    """Queen Ysolde on the white walls of Solenne, looking east toward smoke on the horizon. Room for the title card."""
    sc = Scene(12)
    sc.bands("3a3a6a", "e0a070", 0, 120, n=8)
    for x in (230, 262, 300):
        for k in range(7):
            sc.glow(x + k * 3, 112 - k * 13, 9 + k * 2, (80, 70, 80), 0.55)
    sc.ridge(118, 4, "5a4a60", 15, freq=1.3, rim="c08a70")
    sc.ridge(130, 3, "3a3048", 16, freq=2.0)
    sc.rect(0, 140, 320, 180, (200, 192, 176))                               # the white wall top
    sc.rect(0, 140, 320, 142, (240, 236, 224))
    for x in range(0, 320, 12):
        sc.rect(x, 132, x + 7, 140, (220, 212, 196))
        sc.rect(x, 132, x + 1, 140, (250, 246, 236))
    sc.rect(0, 150, 320, 180, (150, 142, 130))
    sc.put("ysolde", 112, 150, light=(1.0, 0.92, 0.85), rim=(255, 210, 160))
    sc.vignette(0.4)
    return sc


CINEMATICS = {"prologue": [prologue_01, prologue_02, prologue_03, prologue_04, prologue_05, prologue_06, prologue_07,
                           prologue_08, prologue_09, prologue_10, prologue_11, prologue_12]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--out", default=os.path.join("art", "pix2d", "stills"))
    ap.add_argument("--sheet")
    a = ap.parse_args()
    import stills as mod  # the shot modules register into the imported module, not __main__
    import shots_lands  # noqa: F401
    import shots_story  # noqa: F401
    cin = mod.CINEMATICS
    ims = []
    for cid in a.ids or list(cin):
        os.makedirs(os.path.join(a.out, cid), exist_ok=True)
        for i, fn in enumerate(cin[cid]):
            im = fn().image()
            im.save(os.path.join(a.out, cid, f"{i + 1:02d}.png"))
            ims.append((f"{cid} {i + 1:02d}", im))
        print(cid, len(cin[cid]))
    if a.sheet:
        cols = 3
        rows = (len(ims) + cols - 1) // cols
        sheet = Image.new("RGB", (cols * 650, rows * 384), (20, 18, 24))
        d = ImageDraw.Draw(sheet)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        for i, (lab, im) in enumerate(ims):
            x, y = (i % cols) * 650 + 5, (i // cols) * 384 + 4
            sheet.paste(im, (x, y))
            d.text((x + 4, y + 362), lab, font=font, fill=(220, 214, 196))
        sheet.save(a.sheet)
        print(a.sheet, sheet.size)


if __name__ == "__main__":
    main()
