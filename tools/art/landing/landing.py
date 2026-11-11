"""Title screen / landing page key art, painted as pixel art (design only).

The scene is built at 640x360 art pixels and scaled up by an integer with nearest filtering, then a bloom from the
emissive layer is added at full size. Characters come from the approved hand-drawn 2D creatures in art/pix2d/anim
(frames are cut from the strips, never rescaled). Everything else (sky, the Rift, Vael-Orrun, Solenne, the ridge) is
painted here with the same rules: light from the upper left, hue-shifted ramps, flat cel clusters, dark ink outline.

    python3 tools/art/landing/landing.py --out DIR [--no-text]

Writes landing_1920x1080.png (title screen, no text), landing_logo_1920x1080.png (with logo), steam / web crops and
the 640x360 native image.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "art", "pix2d"))
from kit import ramp, hexc  # noqa: E402

ANIM = os.path.join(ROOT, "art", "pix2d", "anim")
META = json.load(open(os.path.join(ANIM, "anim.json")))
W, H = 640, 360
INK = np.array([22, 14, 26], np.float32) / 255
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
ELEM = {"fire": "f0602a", "storm": "f6ce50", "nature": "60c852", "water": "4696ec", "earth": "ba804c", "void": "a060ec"}
rng = random.Random(7)


def col(h):
    return np.array(hexc(h), np.float32) / 255


def bayer(h, w, ox=0, oy=0):
    return np.tile(BAYER, (h // 4 + 2, w // 4 + 2))[oy % 4:oy % 4 + h, ox % 4:ox % 4 + w]


class Canvas:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3), np.float32)
        self.emit = np.zeros((H, W, 3), np.float32)
        self.ys, self.xs = np.mgrid[0:H, 0:W]

    # ---- painting helpers -------------------------------------------------------------------------
    def mask_poly(self, pts):
        m = Image.new("L", (W, H), 0)
        ImageDraw.Draw(m).polygon([(round(x), round(y)) for x, y in pts], fill=255)
        return np.asarray(m) > 0

    def fill(self, mask, c, glow=0.0):
        self.rgb[mask] = c
        if glow:
            self.emit[mask] = np.maximum(self.emit[mask], c * glow)

    def outline(self, mask, c=INK):
        d = mask.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            d |= np.roll(np.roll(mask, dy, 0), dx, 1)
        self.rgb[d & ~mask] = c

    def light(self, x, y, c, r, k=1.0, emit=0.0):
        """Additive pool of light, quantised in bands so it stays pixel-art (no smooth gradient)."""
        d = np.sqrt((self.xs - x) ** 2 + ((self.ys - y) * 1.15) ** 2) / r
        f = np.clip(1 - d, 0, 1) ** 1.6
        f = np.floor(f * 6 + bayer(H, W) * 0.9) / 6
        self.rgb += f[..., None] * c * k
        if emit:
            self.emit += f[..., None] * c * emit

    # ---- sprites ----------------------------------------------------------------------------------
    def creature(self, name, anim, frame, fx, fy, flip=False, tint=(1, 1, 1), rim=None, shade=1.0, shadow=True):
        """Paste one animation frame with its feet at (fx, fy). rim = (colour, light_dir_x) adds a coloured edge
        light from the normal map on the side facing that light."""
        m = META[name]
        fw, fh = m["frame"]
        strip = np.asarray(Image.open(os.path.join(ANIM, f"{name}_{anim}.png")).convert("RGBA")).astype(np.float32) / 255
        nstrip = np.asarray(Image.open(os.path.join(ANIM, f"{name}_{anim}_n.png")).convert("RGB")).astype(np.float32) / 255
        s = strip[:, frame * fw:(frame + 1) * fw]
        n = nstrip[:, frame * fw:(frame + 1) * fw] * 2 - 1
        feet_x, feet_y = m["feet"]
        if flip:
            s, n = s[:, ::-1], n[:, ::-1].copy()
            n[..., 0] *= -1
            feet_x = fw - feet_x
        x0, y0 = int(fx - feet_x), int(fy - feet_y)
        if shadow:
            sh = ((self.xs - fx) / (fw * 0.2)) ** 2 + ((self.ys - fy - 1) / 2.6) ** 2 < 1
            self.rgb[sh] *= 0.55
        c = s[..., :3] * np.array(tint, np.float32) * shade
        if rim is not None:
            rc, dx = rim
            dot = np.clip(n[..., 0] * dx + n[..., 1] * -0.35, 0, 1)
            c = c + (dot > 0.45)[..., None] * np.array(rc, np.float32) * 0.55
        a = s[..., 3] > 0.5
        glowpx = (s[..., :3].max(-1) > 0.85) & a & (s[..., :3].min(-1) < 0.75)
        ys, xs = np.nonzero(a)
        ty, tx = ys + y0, xs + x0
        ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
        self.rgb[ty[ok], tx[ok]] = c[ys[ok], xs[ok]]
        gy, gx = np.nonzero(glowpx)
        ty, tx = gy + y0, gx + x0
        ok = (ty >= 0) & (ty < H) & (tx >= 0) & (tx < W)
        self.emit[ty[ok], tx[ok]] += s[gy[ok], gx[ok], :3] * 0.5


# =====================================================================================================
def sky(cv):
    top, mid, low, hor = col("0a0a1f"), col("2b1747"), col("7a2648"), col("e0703a")
    t = cv.ys / 250.0
    bands = [(0.0, top), (0.45, mid), (0.78, low), (1.0, hor)]
    b = bayer(H, W)
    out = np.zeros((H, W, 3), np.float32)
    steps = 14
    tq = np.clip(np.floor(t * steps + b) / steps, 0, 1)
    for (a0, c0), (a1, c1) in zip(bands, bands[1:]):
        m = (tq >= a0) & (tq <= a1)
        u = ((tq - a0) / (a1 - a0))[..., None]
        out = np.where(m[..., None], c0 * (1 - u) + c1 * u, out)
    cv.rgb[:] = out
    # stars
    for _ in range(260):
        x, y = rng.randrange(W), rng.randrange(170)
        v = rng.random()
        c = np.array([0.8, 0.82, 1.0]) * (0.35 + 0.65 * v) * (1 - y / 220)
        cv.rgb[y, x] = np.maximum(cv.rgb[y, x], c)
        if v > 0.93:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                cv.rgb[y + dy, x + dx] = np.maximum(cv.rgb[y + dy, x + dx], c * 0.5)
            cv.emit[y, x] += c * 0.6
    # falling stars: the omen of the Night of Falling Stars
    for x, y, L in ((420, 22, 34), (515, 48, 24), (300, 14, 18), (590, 16, 28), (360, 70, 14)):
        for i in range(L):
            px, py = x - i, y + int(i * 0.55)
            k = 1 - i / L
            c = np.array([1.0, 0.92, 0.75]) * k
            cv.rgb[py, px] = np.maximum(cv.rgb[py, px], c)
            if i < 3:
                cv.emit[py, px] += np.array([1, 0.8, 0.5]) * 1.2


def rift_and_king(cv):
    """The Crack in the Hollow Rift with the High King Vael-Orrun leaning through it."""
    cx, cy = 176, 120
    # a tall jagged tear: zig-zag edges, widest a little below the middle
    pts_l, pts_r = [], []
    n = 34
    for i in range(n + 1):
        t = i / n
        y = 4 + t * 236
        wdt = (math.sin(t * math.pi) ** 0.7) * 96 * (0.85 + 0.15 * math.sin(t * 7))
        z = (8 if i % 2 else -6) * (0.4 + rng.random())
        pts_l.append((cx - wdt + z - (t - 0.5) * 16, y))
        pts_r.append((cx + wdt - z * 0.8 - (t - 0.5) * 16 + rng.uniform(-4, 4), y))
    rift = cv.mask_poly(pts_l + pts_r[::-1])
    ctr = cx - (cv.ys / 236.0 - 0.5) * 16
    d = np.sqrt(((cv.xs - ctr) / 96.0) ** 2 + ((cv.ys - 110) / 150.0) ** 2)
    band = np.clip(np.floor((1 - d) * 6 + bayer(H, W) * 0.8), 0, 5).astype(int)
    vr = np.array(ramp("6a2cc8", n=6, spread=0.95, shift=0.02), np.float32) / 255
    vr[5] = col("f4e2ff")
    cv.rgb[rift] = vr[band[rift]]
    cv.emit[rift] += vr[band[rift]] * (0.2 + band[rift, None] * 0.11)
    # light streaks pouring out of the tear
    for k in range(26):
        y0 = rng.uniform(20, 220)
        x0 = cx + rng.uniform(-60, 60)
        for i in range(rng.randint(6, 20)):
            xx, yy = int(x0), int(y0 - i * 2)
            if 0 <= yy < H and rift[yy, xx]:
                cv.rgb[yy, xx] = np.maximum(cv.rgb[yy, xx], col("e8c8ff"))
    # cracks spidering out across the sky
    for k in range(14):
        a = rng.uniform(0, math.tau)
        x, y = cx + math.cos(a) * 80, 120 + math.sin(a) * 110
        for _ in range(rng.randint(14, 34)):
            a += rng.uniform(-0.7, 0.7)
            x += math.cos(a) * 2; y += math.sin(a) * 2
            if 0 <= int(x) < W and 0 <= int(y) < 200:
                cv.rgb[int(y), int(x)] = col("d9b6ff")
                cv.emit[int(y), int(x)] += col("b070ff") * 0.6
    cv.outline(rift, col("2a0f44"))

    # ---- Vael-Orrun: colossal armoured silhouette, shoulders through the tear, six-socket crown ---------
    S, AX, AY, DY = 1.3, cx, 240, 20

    def T(pts):
        return [(AX + (x - cx) * S, AY + (y + DY - AY) * S) for x, y in pts]

    def P(x, y):
        return T([(x, y)])[0]
    k = col("0c0714"); k2 = col("1e1132"); k3 = col("2c1a46"); rim = col("d2a8ff")
    mantle = [(cx - 72, 240), (cx - 64, 150), (cx - 34, 128), (cx - 14, 124), (cx + 18, 124), (cx + 38, 128),
              (cx + 64, 150), (cx + 70, 240)]
    head = [(cx - 16, 128), (cx - 18, 96), (cx - 12, 82), (cx, 78), (cx + 12, 82), (cx + 18, 96), (cx + 16, 128),
            (cx + 6, 138), (cx - 6, 138)]
    crown = [(cx - 20, 90), (cx - 23, 64), (cx - 15, 78), (cx - 11, 58), (cx - 5, 76), (cx, 50), (cx + 5, 76),
             (cx + 11, 58), (cx + 15, 78), (cx + 23, 64), (cx + 20, 90)]
    pl = [(cx - 66, 158), (cx - 86, 140), (cx - 80, 130), (cx - 56, 132), (cx - 34, 128), (cx - 40, 152)]
    pr = [(cx + 62, 158), (cx + 84, 140), (cx + 78, 130), (cx + 54, 132), (cx + 34, 128), (cx + 38, 152)]
    sp = [[(cx - 78, 134), (cx - 96, 104), (cx - 66, 130)], [(cx + 74, 134), (cx + 94, 104), (cx + 62, 130)],
          [(cx - 60, 132), (cx - 68, 112), (cx - 50, 130)], [(cx + 56, 132), (cx + 64, 112), (cx + 46, 130)]]
    hl = [(cx - 76, 178), (cx - 94, 170), (cx - 102, 158), (cx - 92, 155), (cx - 84, 162), (cx - 70, 166)]
    hr = [(cx + 72, 184), (cx + 92, 176), (cx + 100, 164), (cx + 90, 161), (cx + 80, 168), (cx + 66, 172)]
    parts = [mantle, head, crown, pl, pr, hl, hr] + sp
    sil = np.zeros((H, W), bool)
    for p in parts:
        sil |= cv.mask_poly(T(p))
    cv.fill(sil, k)
    cv.emit[sil] = 0
    # forms: lit upper-left plane on each plate, so the shape reads as armour, not a cut-out
    for p in (pl, pr, head):
        m = cv.mask_poly(T(p))
        inner = m & np.roll(np.roll(m, 3, 0), 3, 1)
        cv.rgb[m & ~inner] = k3
        cv.rgb[inner] = k2
    chest = cv.mask_poly(T([(cx - 30, 150), (cx + 30, 150), (cx + 22, 200), (cx, 214), (cx - 22, 200)]))
    cv.rgb[chest] = k2
    cv.outline(chest, k)
    # veins of the Unmaking glowing through the chest plate
    x, y = P(cx, 170)
    for b in range(5):
        a = -math.pi / 2 + (b - 2) * 0.7
        xx, yy = x, y
        for _ in range(16):
            a += rng.uniform(-0.5, 0.5)
            xx += math.cos(a) * 1.6; yy -= abs(math.sin(a)) * 1.2 - 0.8
            if sil[int(yy), int(xx)]:
                cv.rgb[int(yy), int(xx)] = col("9a5cff")
                cv.emit[int(yy), int(xx)] += col("9a5cff") * 0.9
    cv.rgb[int(y) - 2:int(y) + 3, int(x) - 2:int(x) + 3] = col("f0d8ff")
    cv.emit[int(y) - 3:int(y) + 4, int(x) - 3:int(x) + 4] += col("c080ff") * 1.5
    # violet rim light from the tear behind
    edge = sil & ~(np.roll(sil, 1, 1) & np.roll(sil, -1, 1) & np.roll(sil, 1, 0) & np.roll(sil, -1, 0))
    cv.rgb[edge] = rim
    cv.emit[edge] += rim * 0.4
    # crown: dull gold edges, six empty sockets each holding a faint ember of its kingdom's colour
    cm = cv.mask_poly(T(crown))
    cv.rgb[cm] = col("2a1e2a")
    cv.rgb[cm & ~np.roll(cm, 1, 0)] = col("b08a4a")
    cv.rgb[cm & ~np.roll(cm, 1, 1)] = col("8a6a3a")
    for i, e in enumerate(ELEM):
        x, y = P(cx - 15 + i * 6, 84)
        x, y = int(x), int(y)
        cv.rgb[y - 1:y + 2, x - 1:x + 2] = col("140a14")
        cv.rgb[y, x] = col(ELEM[e]) * 0.8
        cv.emit[y, x] += col(ELEM[e]) * 0.7
    # eyes: burning slits under the brow
    for ex in (cx - 11, cx + 3):
        x, y = P(ex, 104)
        x, y = int(x), int(y)
        cv.rgb[y, x:x + 9] = col("ffffff")
        cv.rgb[y + 1, x + 1:x + 8] = col("e0b0ff")
        cv.emit[y - 1:y + 3, x - 1:x + 10] += col("d090ff") * 1.8
    x, y = P(cx, 112)
    cv.rgb[int(y):int(y) + 20, int(x)] = k3
    cv.outline(sil, col("05030a"))
    return P(cx, 170)


def mountains(cv):
    layers = [(206, 26, col("3a1f48"), 0.10), (222, 18, col("2a1838"), 0.06), (236, 14, col("1d1229"), 0.0)]
    for base, amp, c, haze in layers:
        y = base
        top = np.zeros(W)
        v = 0
        for x in range(W):
            v += rng.uniform(-1.6, 1.6); v *= 0.96
            top[x] = base - amp * (0.5 + 0.5 * math.sin(x / 37.0 + base)) - abs(v) * 2
        m = cv.ys >= top[None, :]
        cv.rgb[m] = c
        # lit ridge line from the sunset
        ridge = m & ~np.roll(m, 1, 0)
        cv.rgb[ridge] = c + np.array([0.18, 0.08, 0.06]) + haze


def building(cv, x, base, w, h, roof="pointed", wall="d8cdb8", roofc="3c5a9c", windows=True, banner=None, spire=0):
    """A hard-faced block: lit left face, darker right face, roof, lit windows."""
    ramp_w = np.array(ramp(wall, n=5, spread=0.55), np.float32) / 255
    ramp_r = np.array(ramp(roofc, n=5, spread=0.6), np.float32) / 255
    split = x + int(w * 0.62)
    front = cv.mask_poly([(x, base), (x, base - h), (split, base - h), (split, base)])
    side = cv.mask_poly([(split, base), (split, base - h), (x + w, base - h + 2), (x + w, base)])
    cv.fill(front, ramp_w[2]); cv.fill(side, ramp_w[1])
    cv.rgb[base - h, x:split] = ramp_w[4]
    cv.rgb[base - h + 1:base, x] = ramp_w[3]
    # stone courses
    for yy in range(base - h + 5, base, 5):
        cv.rgb[yy, x + 1:split] = ramp_w[1]
        cv.rgb[yy, split:x + w] = ramp_w[0]
    if roof == "pointed":
        tip = base - h - int(w * 1.2) - spire
        rf = cv.mask_poly([(x - 2, base - h), ((x + x + w) / 2, tip), (x + w + 2, base - h)])
        rl = rf & (cv.xs < (x + x + w) / 2)
        cv.fill(rf, ramp_r[1]); cv.fill(rl, ramp_r[3])
        cv.rgb[base - h, x - 2:x + w + 3] = ramp_r[0]
        cv.outline(rf)
    elif roof == "crenel":
        for cx_ in range(x, x + w, 4):
            cv.rgb[base - h - 3:base - h, cx_:cx_ + 2] = ramp_w[3] if cx_ < split else ramp_w[1]
    if windows:
        for wy in range(base - h + 6, base - 4, 9):
            for wx in range(x + 3, x + w - 2, 5):
                if rng.random() < 0.55:
                    c = col("ffcf6a") if rng.random() < 0.8 else col("ff9a40")
                    cv.rgb[wy:wy + 3, wx:wx + 2] = c
                    cv.emit[wy:wy + 3, wx:wx + 2] += c * 0.6
    if banner:
        bc = col(banner)
        bx = x + 2
        cv.rgb[base - h + 3:base - h + 14, bx:bx + 3] = bc
        cv.rgb[base - h + 14, bx + 1] = bc
    m = front | side
    cv.outline(m)


def cliff(cv):
    """The rock Solenne stands on: chiselled faces, lit tops, dark right sides (same block style as the golem)."""
    hr = np.array(ramp("5a4650", n=5, spread=0.55), np.float32) / 255
    base = cv.mask_poly([(404, 300), (414, 236), (440, 214), (640, 206), (640, 300)])
    cv.fill(base, hr[1])
    x = 410
    while x < 640:
        w = rng.randint(10, 22)
        top = 214 + rng.randint(0, 6) - (x - 410) * 0.03
        h = rng.randint(16, 40)
        face = cv.mask_poly([(x, top), (x + w * 0.7, top + 2), (x + w * 0.7, top + h), (x, top + h - 3)])
        side = cv.mask_poly([(x + w * 0.7, top + 2), (x + w, top + 5), (x + w, top + h - 2), (x + w * 0.7, top + h)])
        cv.fill(face, hr[2]); cv.fill(side, hr[0])
        cv.rgb[int(top), int(x):int(x + w * 0.7)] = hr[4]
        cv.rgb[int(top) + 1, int(x):int(x + w * 0.7)] = hr[3]
        for _ in range(2):
            cy_ = int(top + rng.randint(5, max(6, h - 4)))
            cv.rgb[cy_, int(x + 2):int(x + w * 0.5)] = hr[1]
        cv.outline(face | side)
        x += w - 2
    # moss on the lit tops
    for _ in range(40):
        x = rng.randrange(412, 640); y = int(214 + rng.randint(-1, 8))
        if cv.rgb[y, x].sum() > hr[3].sum() * 0.9:
            cv.rgb[y, x:x + 2] = col("5c7a3e")


def solenne(cv):
    """Solenne on its hill, right side: white walls, blue roofs, the Sunstone lens burning gold above the keep."""
    # hill
    cliff(cv)
    # back row of houses / towers
    for x, h, w in ((452, 22, 12), (468, 30, 10), (482, 18, 14), (566, 26, 12), (582, 20, 14), (600, 30, 10),
                    (618, 22, 14)):
        building(cv, x, 204, w, h, roof="pointed", wall="b8ad9c", roofc="2f4a86")
    # the keep and its great spire
    building(cv, 512, 204, 34, 64, roof="crenel", wall="e6dcc6", roofc="3c5a9c", banner="c43030")
    building(cv, 520, 140, 18, 40, roof="pointed", wall="ece3cf", roofc="3c5a9c", spire=10)
    # flanking towers
    building(cv, 496, 206, 14, 46, roof="pointed", wall="ddd2bc", banner="c43030")
    building(cv, 548, 206, 14, 50, roof="pointed", wall="ddd2bc", banner="c43030")
    # the wall ring with six element towers
    wallm = cv.mask_poly([(420, 232), (420, 214), (640, 208), (640, 228)])
    wr = np.array(ramp("d6cab2", n=5, spread=0.5), np.float32) / 255
    cv.fill(wallm, wr[2])
    for x in range(420, 640, 4):
        y = int(214 - (x - 420) * 6 / 220)
        cv.rgb[y - 3:y, x:x + 2] = wr[3]
    cv.rgb[226:229, 420:640] = wr[1]
    cv.outline(wallm)
    towers = []
    for i, e in enumerate(ELEM):
        x = 428 + i * 36
        y = int(214 - (x - 420) * 6 / 220) + 14
        building(cv, x, y, 12, 30, roof="crenel", wall="d0c4ac", windows=False)
        c = col(ELEM[e])
        cv.rgb[y - 36:y - 31, x + 4:x + 8] = c
        cv.rgb[y - 35:y - 32, x + 5:x + 7] = np.minimum(c + 0.4, 1)
        cv.emit[y - 37:y - 30, x + 3:x + 9] += c * 1.3
        towers.append((x + 6, y - 34, c))
    # Sunstone lens: a gold ring floating above the spire
    sx, sy = 529, 66
    d = np.sqrt((cv.xs - sx) ** 2 + ((cv.ys - sy) * 1.0) ** 2)
    ring = (d < 13) & (d > 9)
    core = d <= 9
    gr = np.array(ramp("f2c14e", n=5, spread=0.7), np.float32) / 255
    cv.fill(ring, gr[2], 0.6)
    cv.rgb[ring & (cv.xs < sx) & (cv.ys < sy)] = gr[4]
    cv.fill(core, col("fff4d0"), 1.4)
    cv.rgb[core & (d > 6)] = col("ffe08a")
    cv.outline(ring | core, col("5a3610"))
    for a in range(12):
        ang = a * math.tau / 12
        for r in range(16, 22 + (a % 2) * 6):
            x, y = int(sx + math.cos(ang) * r), int(sy + math.sin(ang) * r)
            cv.rgb[y, x] = np.maximum(cv.rgb[y, x], gr[4])
            cv.emit[y, x] += gr[3] * 0.5
    return towers, (sx, sy)


def beams(cv, towers, sun, king):
    """Six element beams rise from the wall towers into the Sunstone, which fires one gold lance at the King."""
    sx, sy = sun
    for x, y, c in towers:
        n = int(math.hypot(sx - x, sy - y))
        for i in range(n):
            t = i / n
            px = x + (sx - x) * t + math.sin(t * 9 + x) * 1.5 * (1 - t)
            py = y + (sy - y) * t
            for o in (-1, 0, 1):
                xx, yy = int(px) + o, int(py)
                if 0 <= xx < W and 0 <= yy < H:
                    cv.rgb[yy, xx] = np.maximum(cv.rgb[yy, xx], c * (0.9 if o else 1.0) + (0 if o else 0.25))
                    cv.emit[yy, xx] += c * (0.5 if o else 0.9)
    # the gold lance (thick, pulsing knots) from the Sunstone to the Rift
    kx, ky = king
    n = int(math.hypot(kx - sx, ky - sy))
    for i in range(n):
        t = i / n
        px, py = sx + (kx - sx) * t, sy + (ky - sy) * t + math.sin(t * math.pi) * -26
        wdt = 2 + (1 if (i // 6) % 2 else 0)
        for o in range(-wdt, wdt + 1):
            xx, yy = int(px), int(py) + o
            if 0 <= yy < H:
                c = col("fff6d8") if abs(o) < 2 else col("f2b84a")
                cv.rgb[yy, xx] = c
                cv.emit[yy, xx] += c * (1.4 if abs(o) < 2 else 0.8)
    # impact burst on the King's shield of night
    for r in range(3, 16):
        for a in range(0, 360, 12):
            if rng.random() < 0.5 - r * 0.02:
                xx, yy = int(kx + math.cos(math.radians(a)) * r), int(ky + math.sin(math.radians(a)) * r * 0.9)
                c = col("ffe7a0") if r < 8 else col("c79bff")
                cv.rgb[yy, xx] = c
                cv.emit[yy, xx] += c
    cv.light(kx, ky, col("ffd27a"), 40, 0.35, 0.3)


def ground(cv):
    """Foreground ridge: a stone road that rises from the left (the horde) to the right (the defenders)."""
    top = np.zeros(W)
    for x in range(W):
        top[x] = 286 - 22 * math.sin((x - 80) / 640 * math.pi) + 3 * math.sin(x / 9.0) * (rng.random() > 0.6)
    m = cv.ys >= top[None, :]
    gr = np.array(ramp("4b3b46", n=5, spread=0.55), np.float32) / 255
    b = bayer(H, W)
    depth = np.clip((cv.ys - top[None, :]) / 70, 0, 1)
    band = np.clip(np.floor((1 - depth) * 3 + b * 0.8), 0, 3).astype(int)
    cv.rgb[m] = gr[band[m]]
    rim = m & ~np.roll(m, 1, 0)
    cv.rgb[rim] = gr[4]
    cv.rgb[np.roll(rim, 1, 0)] = gr[3]
    # chiselled rocks and grass tufts
    for _ in range(60):
        x = rng.randrange(W - 10); y = int(top[x]) + rng.randrange(4, 74)
        if y >= H - 2:
            continue
        w = rng.randrange(3, 9); h = rng.randrange(2, 5)
        cv.rgb[y:y + h, x:x + w] = gr[1]
        cv.rgb[y, x:x + w] = gr[3]
        cv.rgb[y:y + h, x + w - 1] = gr[0]
    for _ in range(140):
        x = rng.randrange(W - 2); y = int(top[x]) + rng.randrange(0, 4)
        g = col("4f6a3a") if rng.random() < 0.7 else col("6f8a46")
        for k in range(rng.randrange(2, 4)):
            cv.rgb[y - k, x + (k if rng.random() < 0.5 else 0) % 2] = g
    return top


def horde(cv, top):
    """Distant horde streaming out of the Rift down the far road: tiny silhouettes with ember eyes and torches."""
    for i in range(170):
        t = rng.random()
        x = int(110 + t * 230 + rng.uniform(-14, 14))
        y = int(246 + t * 6 + rng.uniform(-4, 6))
        h = 4 + int(t * 3)
        c = col("120a18")
        cv.rgb[y - h:y, x:x + 2] = c
        cv.rgb[y - h - 1, x] = c
        if rng.random() < 0.3:
            cv.rgb[y - h + 1, x + 1] = col("ff5a3a"); cv.emit[y - h + 1, x + 1] += col("ff5030") * 0.8
        if rng.random() < 0.07:
            cv.rgb[y - h - 4:y - h, x + 2] = col("3a2a20")
            cv.rgb[y - h - 5, x + 2] = col("ffb040"); cv.emit[y - h - 6:y - h - 3, x + 1:x + 4] += col("ff9030") * 0.9
        if rng.random() < 0.05:  # banner
            cv.rgb[y - h - 7:y - h, x + 2] = col("2a1a20")
            cv.rgb[y - h - 7:y - h - 3, x + 3:x + 6] = col("4a1460")


def battle(cv, top):
    def gy(x):
        return int(top[int(np.clip(x, 0, W - 1))]) + 3

    violet, gold, fire = col("b07cff"), col("ffc860"), col("ff7a3a")
    # ---- horde, left, facing right (light from rift behind them: violet rim on their backs, x = -1) ------
    E = dict(rim=(violet, -1.0), tint=(0.78, 0.74, 0.92))
    cv.creature("ghost", "idle", 2, 40, gy(40) - 26, **E, shadow=False)
    cv.creature("skeleton", "walk", 1, 24, gy(24) + 18, **E)
    cv.creature("orc", "walk", 3, 74, gy(74) + 10, **E)
    cv.creature("skeleton", "walk", 5, 110, gy(110) + 24, **E)
    cv.creature("orc", "attack", 3, 150, gy(150) + 30, **E)
    cv.creature("ghost", "attack", 3, 196, gy(196) - 18, **E, shadow=False)
    cv.creature("skeleton", "attack", 4, 214, gy(214) + 44, **E)
    # ---- defenders, right, facing left (flipped; warm city light from the right edge, x = +1) -------
    D = dict(flip=True, rim=(gold, 1.0), tint=(0.95, 0.88, 0.86))
    cv.creature("golem", "attack", 4, 300, gy(300) + 12, **D)
    cv.creature("soldier", "attack", 3, 262, gy(262) + 40, **D)
    cv.creature("soldier", "idle", 1, 350, gy(350) + 30, **D)
    cv.creature("dwarf", "attack", 3, 316, gy(316) + 56, **D)
    cv.creature("soldier", "attack", 5, 392, gy(392) + 48, **D)
    cv.creature("elf", "attack", 4, 430, gy(430) + 6, **D)
    cv.creature("soldier", "walk", 2, 452, gy(452) + 58, **D)
    cv.creature("elf", "attack", 3, 488, gy(488) + 30, **D)
    cv.creature("soldier", "idle", 3, 520, gy(520) + 50, **D)
    # ---- element orbs hovering over the defenders -----------------------------------------------
    for (e, x, y) in (("storm", 410, 222), ("water", 466, 238), ("nature", 516, 232), ("fire", 566, 236),
                      ("earth", 614, 254), ("void", 262, 232)):
        cv.creature(f"orb_{e}", "idle", 1, x, y, flip=True, shadow=False)
        cv.light(x, y - 14, col(ELEM[e]), 26, 0.22, 0.12)
    # ---- dragon diving over the clash, breathing fire at the line --------------------------------
    cv.creature("dragon", "attack", 4, 352, 214, rim=(violet, -1.0), tint=(0.82, 0.76, 0.9), shadow=False)
    # ---- clash sparks and arrows ------------------------------------------------------------------
    for _ in range(40):
        x, y = rng.uniform(220, 290), rng.uniform(250, 320)
        c = gold if rng.random() < 0.6 else fire
        cv.rgb[int(y), int(x)] = c; cv.emit[int(y), int(x)] += c * 1.2
    for x0, y0 in ((420, 270), (470, 286), (500, 262), (446, 250)):
        for i in range(10):
            cv.rgb[int(y0 - i * 0.3), int(x0 - 40 - i)] = col("e8dcc0")
        cv.emit[int(y0 - 3), int(x0 - 50)] += gold
    cv.light(255, 292, fire, 60, 0.16, 0.1)


def foreground(cv):
    """Dark chiselled rocks in the bottom corners to frame the battle."""
    fr = np.array(ramp("3a2e3c", n=5, spread=0.45), np.float32) / 255
    for x0, flip in ((0, False), (W, True)):
        x = 0
        while x < 120:
            w = rng.randint(14, 30); h = rng.randint(18, 46) - x // 4
            xa = x0 + (-x - w if flip else x)
            top = H - h
            face = cv.mask_poly([(xa, H), (xa, top + 3), (xa + w * 0.6, top), (xa + w * 0.6, H)])
            side = cv.mask_poly([(xa + w * 0.6, H), (xa + w * 0.6, top), (xa + w, top + 4), (xa + w, H)])
            cv.fill(face, fr[1]); cv.fill(side, fr[0])
            cv.rgb[int(top), int(xa):int(xa + w * 0.6)] = fr[3]
            cv.outline(face | side, col("07050a"))
            x += w - 3


def vignette(cv):
    d = np.sqrt(((cv.xs - W / 2) / (W * 0.62)) ** 2 + ((cv.ys - H * 0.45) / (H * 0.7)) ** 2)
    f = np.clip(d - 0.55, 0, 1)
    f = np.floor(f * 8 + bayer(H, W) * 0.9) / 8
    cv.rgb *= (1 - 0.55 * f)[..., None]


def finish(cv, scale=3):
    """Scale up by an integer, then add bloom from the emissive layer."""
    rgb = np.clip(cv.rgb, 0, 1)
    big = np.kron(rgb, np.ones((scale, scale, 1)))
    em = np.kron(np.clip(cv.emit, 0, 3), np.ones((scale, scale, 1)))
    out = big.copy()
    for r, k in ((4 * scale, 0.35), (12 * scale, 0.35), (32 * scale, 0.25)):
        e = np.clip(em / 3, 0, 1)
        im = Image.fromarray((e * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
        out += np.asarray(im).astype(np.float32) / 255 * 3 * k
    out = 1 - np.exp(-out * 1.15)  # soft tonemap so bright cores do not clip flat
    out = out / (1 - math.exp(-1.15))
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8))


def build():
    cv = Canvas()
    sky(cv)
    king = rift_and_king(cv)
    mountains(cv)
    towers, sun = solenne(cv)
    beams(cv, towers, sun, king)
    horde(cv, None)
    top = ground(cv)
    battle(cv, top)
    foreground(cv)
    vignette(cv)
    return cv


def add_logo(img, cx, cy, frac):
    sys.path.insert(0, HERE)
    from logo import paste_logo
    return paste_logo(img, cx, cy, frac)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "art", "landing"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    cv = build()
    Image.fromarray((np.clip(cv.rgb, 0, 1) * 255).astype(np.uint8)).save(os.path.join(args.out, "landing_640x360.png"))
    img = finish(cv, 3)
    out = lambda n: os.path.join(args.out, n)
    img.save(out("landing_1920x1080.png"))
    # 4K for the website hero (6x art pixels, still integer scale)
    finish(cv, 6).save(out("landing_3840x2160.png"))
    sys.path.insert(0, HERE)
    import logo as L
    lg = img.convert("RGBA")
    L.paste_logo(lg, 1090, 118, 0.42)
    lg.convert("RGB").save(out("landing_logo_1920x1080.png"))
    # Steam crops from the full-size art (crop then nearest-resize keeps hard pixels)
    crops = {
        "steam_page_background_1438x810.png": ((0, 0, 1920, 1080), (1438, 810), None),
        "steam_library_hero_3840x1240.png": ((0, 40, 1920, 660), (3840, 1240), None),
        "steam_header_capsule_920x430.png": ((0, 40, 1920, 937), (920, 430), 0.50),
        "steam_main_capsule_1232x706.png": ((0, 0, 1884, 1080), (1232, 706), 0.46),
        "web_banner_1920x600.png": ((0, 40, 1920, 640), (1920, 600), 0.36),
    }
    for name, (box, size, logo_frac) in crops.items():
        im = img.crop(box).resize(size, Image.LANCZOS if size[0] < box[2] - box[0] else Image.NEAREST).convert("RGBA")
        if logo_frac:
            L.paste_logo(im, int(size[0] * 0.57), int(size[1] * 0.11), logo_frac)
        im.convert("RGB").save(out(name))
    print("wrote", args.out)


if __name__ == "__main__":
    main()
