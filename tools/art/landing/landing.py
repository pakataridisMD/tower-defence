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
        wdt = (math.sin(t * math.pi) ** 0.7) * 128 * (0.85 + 0.15 * math.sin(t * 7))
        z = (8 if i % 2 else -6) * (0.4 + rng.random())
        pts_l.append((cx - wdt + z - (t - 0.5) * 16, y))
        pts_r.append((cx + wdt - z * 0.8 - (t - 0.5) * 16 + rng.uniform(-4, 4), y))
    rift = cv.mask_poly(pts_l + pts_r[::-1])
    ctr = cx - (cv.ys / 236.0 - 0.5) * 16
    d = np.sqrt(((cv.xs - ctr) / 120.0) ** 2 + ((cv.ys - 100) / 130.0) ** 2)
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

    return king(cv, rift)


PARTS = []


def plate(cv, pts, tones, clip=None, violet=None, gold=None, split=0.45, lines=()):
    """One armour plate: flat cel tones lit from the upper left, violet rim from the Rift behind on the top and
    left edges, a gold rim from the Sunstone on the right edges, ink outline."""
    m = cv.mask_poly(pts)
    if clip is not None:
        m &= clip
    if not m.any():
        return m
    ys, xs = np.nonzero(m)
    x0, x1, y0, y1 = xs.min(), xs.max(), ys.min(), ys.max()
    u = (cv.xs - x0) / max(1, x1 - x0) + (cv.ys - y0) / max(1, y1 - y0)
    tone = np.where(u < split * 2 * 0.55, 2, np.where(u < split * 2 * 1.25, 1, 0))
    cv.rgb[m] = np.array(tones)[tone[m]]
    inner = m & np.roll(m, 1, 0) & np.roll(m, -1, 0) & np.roll(m, 1, 1) & np.roll(m, -1, 1)
    top = m & ~np.roll(m, 1, 0)
    left = m & ~np.roll(m, 1, 1)
    right = m & ~np.roll(m, -1, 1)
    cv.rgb[m & ~inner] = tones[0] * 0.55
    cv.rgb[(top | left) & m] = tones[3]
    PARTS.append(m)
    for (ax, ay), (bx, by) in lines:
        n = int(max(abs(bx - ax), abs(by - ay))) + 1
        for i in range(n):
            xx, yy = int(ax + (bx - ax) * i / n), int(ay + (by - ay) * i / n)
            if m[yy, xx]:
                cv.rgb[yy, xx] = tones[0] * 0.7
    return m


def king(cv, rift):
    """The High King Vael-Orrun: a colossus in black plate leaning out of the Rift, one gauntlet reaching for
    Solenne. The Sunstone's lance strikes his palm and holds it back."""
    A = [col("0e0918"), col("1c1230"), col("2c1d48"), col("3e2a5e")]      # armour tones (shadow..light), edge
    C = [col("12070e"), col("220c1a"), col("34142a"), col("4a1c3a")]      # cloak
    V, G = col("d6aaff"), col("ffcf70")
    cx = 168
    # ---- cloak: torn mantle billowing to the left out of the Rift -----------------------------------
    cl = [(cx - 40, 96), (cx - 90, 108), (cx - 132, 132), (cx - 150, 170), (cx - 160, 214), (cx - 138, 200),
          (cx - 132, 228), (cx - 112, 206), (cx - 100, 236), (cx - 80, 210), (cx - 60, 240), (cx + 70, 240),
          (cx + 60, 110)]
    plate(cv, cl, C, violet=V * 0.8, split=0.6)
    for i in range(7):  # tears in the hem
        x = cx - 150 + i * 13
        cv.rgb[200 + i % 3 * 6:214 + i % 2 * 8, x:x + 2] = C[0]
    # ---- torso and chest plate -----------------------------------------------------------------------
    plate(cv, [(cx - 44, 104), (cx + 46, 104), (cx + 54, 240), (cx - 52, 240)], A, violet=V)
    chest = plate(cv, [(cx - 34, 112), (cx + 36, 112), (cx + 30, 160), (cx + 2, 184), (cx - 28, 160)], A,
                  violet=V, gold=G, lines=[((cx + 1, 114), (cx + 1, 182)), ((cx - 30, 140), (cx + 32, 140))])
    # the Unmaking burns through a wound in the chest
    hx, hy = cx + 1, 150
    for b in range(9):
        a = b * math.tau / 9 + rng.uniform(-0.2, 0.2)
        xx, yy = float(hx), float(hy)
        for _ in range(rng.randint(8, 18)):
            a += rng.uniform(-0.45, 0.45)
            xx += math.cos(a) * 1.4; yy += math.sin(a) * 1.4
            if 0 <= int(yy) < H and chest[int(yy), int(xx)]:
                cv.rgb[int(yy), int(xx)] = col("b070ff")
                cv.emit[int(yy), int(xx)] += col("a060ff") * 1.0
    d = np.hypot(cv.xs - hx, (cv.ys - hy) * 1.2)
    cv.rgb[d < 4] = col("c890ff"); cv.rgb[d < 2.5] = col("ffffff")
    cv.emit[d < 6] += col("c080ff") * 1.6
    # belt of skulls of the old kings would be too much: a plain heavy belt with a gold buckle
    plate(cv, [(cx - 50, 196), (cx + 52, 196), (cx + 53, 206), (cx - 51, 206)], A, violet=V, gold=G)
    cv.rgb[197:206, cx - 4:cx + 6] = col("8a6a3a"); cv.rgb[199:204, cx - 2:cx + 4] = col("2a1e2a")
    # ---- far (viewer-left) pauldron: three stacked plates and a swept horn ---------------------------
    for i, dy in enumerate((0, 12, 22)):
        plate(cv, [(cx - 30, 98 + dy), (cx - 74 - i * 6, 92 + dy + i * 4), (cx - 96 - i * 4, 108 + dy + i * 3),
                   (cx - 84 - i * 4, 126 + dy), (cx - 40, 120 + dy)], A, violet=V)
    plate(cv, [(cx - 76, 94), (cx - 112, 52), (cx - 100, 50), (cx - 62, 92)], A, violet=V, gold=None)
    # far arm gripping the Rift edge
    plate(cv, [(cx - 92, 140), (cx - 112, 168), (cx - 122, 190), (cx - 106, 196), (cx - 94, 172), (cx - 78, 150)],
          A, violet=V)
    for f in range(4):
        plate(cv, [(cx - 124 + f * 5, 188), (cx - 130 + f * 5, 200), (cx - 126 + f * 5, 204), (cx - 118 + f * 5, 194)],
              A, violet=V)
    # ---- reaching arm (viewer right): upper arm, vambrace, open gauntlet toward the city --------------
    plate(cv, [(cx + 40, 110), (cx + 96, 120), (cx + 106, 142), (cx + 50, 148)], A, violet=V, gold=G,
          lines=[((cx + 70, 114), (cx + 76, 146))])
    plate(cv, [(cx + 92, 118), (cx + 140, 116), (cx + 150, 134), (cx + 100, 144)], A, violet=V, gold=G,
          lines=[((cx + 118, 117), (cx + 122, 140))])
    # gauntlet: palm toward Solenne, fingers splayed like claws
    palm = (cx + 160, 124)
    plate(cv, [(cx + 140, 112), (cx + 160, 108), (cx + 166, 136), (cx + 146, 142)], A, violet=V, gold=G)
    for (fx, fy), (tx, ty) in (((cx + 156, 110), (cx + 176, 92)), ((cx + 162, 116), (cx + 186, 104)),
                               ((cx + 164, 124), (cx + 188, 120)), ((cx + 162, 132), (cx + 182, 138)),
                               ((cx + 146, 140), (cx + 160, 154))):
        mx, my = (fx + tx) / 2, (fy + ty) / 2
        plate(cv, [(fx - 3, fy - 2), (mx, my - 3), (tx, ty), (mx + 1, my + 3), (fx + 2, fy + 3)], A, violet=V, gold=G)
        cv.rgb[int(ty), int(tx)] = col("e8d8ff")
    # ---- near pauldron (viewer right), over the arm -----------------------------------------------------
    for i, dy in enumerate((0, 11, 20)):
        plate(cv, [(cx + 30, 98 + dy), (cx + 76 + i * 5, 90 + dy + i * 4), (cx + 98 + i * 3, 104 + dy + i * 3),
                   (cx + 88 + i * 3, 122 + dy), (cx + 40, 118 + dy)], A, violet=V, gold=G)
    plate(cv, [(cx + 70, 92), (cx + 104, 46), (cx + 114, 50), (cx + 86, 96)], A, violet=V, gold=G)
    # ---- helm: tall great-helm with brow ridge, cheek guards, swept horns, glowing T visor --------------
    plate(cv, [(cx - 22, 52), (cx - 34, 38), (cx - 56, 30), (cx - 40, 46), (cx - 26, 64)], A, violet=V)
    plate(cv, [(cx + 22, 52), (cx + 34, 38), (cx + 58, 28), (cx + 42, 46), (cx + 26, 64)], A, violet=V, gold=G)
    plate(cv, [(cx - 22, 96), (cx - 26, 60), (cx - 18, 42), (cx, 36), (cx + 18, 42), (cx + 26, 60), (cx + 22, 96),
               (cx + 8, 108), (cx - 8, 108)], A, violet=V, gold=G,
          lines=[((cx, 38), (cx, 66)), ((cx - 22, 84), (cx - 8, 96)), ((cx + 22, 84), (cx + 8, 96))])
    plate(cv, [(cx - 24, 62), (cx + 24, 62), (cx + 22, 68), (cx - 22, 68)], A, violet=V, gold=G)  # brow
    # visor: T-slit with burning eyes
    cv.rgb[70:73, cx - 17:cx + 18] = col("0a040e")
    cv.rgb[70:100, cx - 1:cx + 2] = col("0a040e")
    for ex in (cx - 15, cx + 4):
        cv.rgb[71, ex:ex + 11] = col("ffffff")
        cv.rgb[70, ex + 2:ex + 9] = col("e8c4ff")
        cv.emit[69:74, ex - 2:ex + 13] += col("d090ff") * 2.2
    for y in range(74, 98, 2):
        cv.rgb[y, cx] = col("c880ff"); cv.emit[y, cx] += col("a060ff") * 0.8
    # ---- crown: six tall spikes, each socket empty but for an ember of its kingdom ---------------------
    crown = [(cx - 24, 48), (cx - 28, 16), (cx - 19, 34), (cx - 15, 6), (cx - 7, 30), (cx, 0), (cx + 7, 30),
             (cx + 15, 6), (cx + 19, 34), (cx + 28, 16), (cx + 24, 48)]
    cm = plate(cv, crown, [col("3a2616"), col("624422"), col("8e6634"), col("d8ac60")], violet=None, gold=G, split=0.35)
    cv.rgb[47:50, cx - 24:cx + 25] = col("8e6634"); cv.rgb[47, cx - 24:cx + 25] = col("f0c878")
    for tx, ty in ((cx - 28, 16), (cx - 15, 6), (cx, 0), (cx + 15, 6), (cx + 28, 16)):
        for k in range(1, 12):  # lit left flank of each spike
            yy = ty + k * 2; xx = int(tx + (k * 0.55 if tx <= cx else k * 0.45)) - (1 if tx > cx else 0)
            if cm[yy, xx]:
                cv.rgb[yy, xx] = col("f0c878")
    for i, e in enumerate(ELEM):
        x, y = cx - 16 + i * 6 + (1 if i > 2 else 0), 41
        cv.rgb[y - 2:y + 2, x - 1:x + 2] = col("140a14")
        cv.rgb[y - 1:y + 1, x] = col(ELEM[e]) * 0.9
        cv.emit[y - 1:y + 1, x] += col(ELEM[e]) * 0.9
    sil = np.zeros((H, W), bool)
    for m in PARTS:
        sil |= m
    PARTS.clear()
    glow_keep = cv.emit.copy()
    cv.emit[sil] = 0
    hot = sil & (cv.rgb.max(-1) > 0.6)            # eyes, wound, sockets keep their glow
    cv.emit[hot] = glow_keep[hot]
    out_t = sil & ~np.roll(sil, 1, 0)
    out_l = sil & ~np.roll(sil, 1, 1)
    out_r = sil & ~np.roll(sil, -1, 1)
    vio = (out_t | out_l) & (cv.xs < cx + 120)
    cv.rgb[vio] = V; cv.emit[vio] += V * 0.5
    cv.rgb[np.roll(vio, 1, 1) & sil & ~out_r] = V * 0.55
    gld = (out_r | out_t) & (cv.xs > cx + 20)
    cv.rgb[gld] = G; cv.emit[gld] += G * 0.5
    cv.rgb[np.roll(gld, -1, 1) & sil] = G * 0.6
    cv.outline(sil, col("05030a"))
    return palm


def clouds(cv):
    """Storm clouds wheeling round the Rift: puffs built from overlapping circles, lit from the Rift side."""
    tones = [col("1c1232"), col("2a1a44"), col("3e2660"), col("6a3e94"), col("a070d0")]
    for i in range(34):
        a = rng.uniform(0, math.tau)
        r = rng.uniform(130, 240)
        x = 168 + math.cos(a) * r * 1.3
        y = 96 + math.sin(a) * r * 0.36
        if y > 190 or y < 0 or x > 470 or x < -40:
            continue
        m = np.zeros((H, W), bool)
        n = rng.randint(3, 6)
        span = rng.uniform(30, 70)
        for k in range(n):
            px = x - span / 2 + span * k / max(1, n - 1)
            rr = rng.uniform(5, 11) * (1.3 if 0 < k < n - 1 else 0.9)
            m |= np.hypot(cv.xs - px, (cv.ys - y) * 1.25) < rr
        m &= cv.ys < y + 4
        near = max(0.0, 1 - math.hypot(x - 168, (y - 100) * 2) / 320)
        cv.rgb[m] = tones[1] if near < 0.35 else tones[2]
        lit = m & ~np.roll(m, 2, 0)
        cv.rgb[lit] = tones[3] if near > 0.3 else tones[2]
        cv.rgb[m & ~np.roll(m, 1, 0)] = tones[4] if near > 0.45 else tones[3]
        side = m & ~np.roll(m, 2, 1) if x > 168 else m & ~np.roll(m, -2, 1)
        cv.rgb[side & ~lit] = tones[2]
        cv.rgb[m & ~np.roll(m, -1, 0)] = tones[0]


def road(cv):
    """The far plain and the road winding down from the Rift to the battle, packed with the horde."""
    plain = cv.ys >= 232
    b = bayer(H, W)
    pt = [col("1a1228"), col("221630"), col("2c1c38")]
    band = np.clip(np.floor((cv.ys - 232) / 14 + b * 0.7), 0, 2).astype(int)
    cv.rgb[plain] = np.array(pt)[band[plain]]
    def path(t):  # rift foot, swings left across the plain, then back right to the battle
        return 160 - math.sin(t * math.pi) * 120 + t * 90, 233 + t * 44
    pts_a, pts_b = [], []
    for i in range(61):
        t = i / 60
        x, y = path(t)
        w = 2 + t * 6
        pts_a.append((x - w, y - 1 - t * 2)); pts_b.append((x + w, y + 1 + t * 2))
    rd = cv.mask_poly(pts_a + pts_b[::-1])
    cv.rgb[rd] = col("4a3448")
    cv.rgb[rd & ~np.roll(rd, 1, 0)] = col("624a5c")
    for i in range(520):
        t = rng.random()
        x, y = path(t)
        x += rng.uniform(-1, 1) * (3 + t * 7); y += rng.uniform(-1, 1) * (1 + t * 2)
        x, y = int(x), int(y)
        h = 3 + int(t * 4)
        if y >= H - 1 or x < 1 or x >= W - 3:
            continue
        cv.rgb[y - h:y, x:x + 1 + (t > 0.5)] = col("0c0610")
        cv.rgb[y - h - 1, x] = col("0c0610")
        if rng.random() < 0.25:
            cv.rgb[y - h + 1, x] = col("ff6a3a"); cv.emit[y - h + 1, x] += col("ff5030") * 0.7
        if rng.random() < 0.07:
            cv.rgb[y - h - 4:y - h, x + 1] = col("2a1a14")
            cv.rgb[y - h - 5, x + 1] = col("ffb040"); cv.emit[y - h - 5, x + 1] += col("ff9030") * 1.6
        if rng.random() < 0.035:
            cv.rgb[y - h - 8:y - h, x + 1] = col("1a1018")
            cv.rgb[y - h - 8:y - h - 4, x + 2:x + 5] = col("6a2c9a")
    cv.light(190, 250, col("ff7a3a"), 70, 0.06, 0.05)


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
    B = dict(rim=(violet, -1.0), tint=(0.52, 0.48, 0.66))
    for nm, an, fr, x in (("orc", "walk", 1, 96), ("skeleton", "walk", 3, 168), ("orc", "walk", 6, 196)):
        cv.creature(nm, an, fr, x, gy(x) - 4, **B)
    cv.creature("ghost", "idle", 2, 40, gy(40) - 26, **E, shadow=False)
    cv.creature("skeleton", "walk", 1, 24, gy(24) + 18, **E)
    cv.creature("orc", "walk", 3, 74, gy(74) + 10, **E)
    cv.creature("skeleton", "walk", 5, 110, gy(110) + 24, **E)
    cv.creature("orc", "attack", 3, 150, gy(150) + 30, **E)
    cv.creature("ghost", "attack", 3, 196, gy(196) - 18, **E, shadow=False)
    cv.creature("skeleton", "attack", 4, 214, gy(214) + 44, **E)
    # ---- defenders, right, facing left (flipped; warm city light from the right edge, x = +1) -------
    D = dict(flip=True, rim=(gold, 1.0), tint=(0.95, 0.88, 0.86))
    DB = dict(flip=True, rim=(gold, 1.0), tint=(0.62, 0.56, 0.62))
    for nm, an, fr, x in (("soldier", "idle", 0, 356), ("soldier", "idle", 4, 392), ("dwarf", "idle", 2, 540),
                          ("soldier", "idle", 2, 572)):
        cv.creature(nm, an, fr, x, gy(x) + 2, **DB)
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
    cv.creature("dragon", "attack", 4, 262, 226, rim=(violet, -1.0), tint=(0.82, 0.76, 0.9), shadow=False)
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
    # dragon fire: a widening cone of flame tongues from the mouth down onto the golem
    mx, my = 316, 184
    for i in range(260):
        t = rng.random() ** 0.7
        x = mx + t * 22 + rng.gauss(0, 1) * t * 7
        y = my + t * 58 + rng.gauss(0, 1) * t * 5
        r = 0.8 + t * 2.6 * rng.random()
        m = np.hypot(cv.xs - x, cv.ys - y) < r
        c = col("fff4c8") if t < 0.25 else (col("ffc040") if t < 0.55 else (col("f06a24") if t < 0.85 else col("a8301a")))
        cv.rgb[m] = c; cv.emit[m] += c * (1.0 - 0.5 * t)
    cv.light(338, 256, fire, 40, 0.25, 0.2)
    # arrow volley arcing from the elves into the horde
    for k in range(14):
        x0, y0 = rng.uniform(410, 500), rng.uniform(236, 270)
        x1, y1 = rng.uniform(40, 200), rng.uniform(250, 300)
        for i in range(0, 28):
            t = 0.55 + i / 100
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * 60
            if i < 6:
                cv.rgb[int(y), int(x)] = col("e8dcc0")
        cv.rgb[int(y), int(x)] = col("ffffff")
    # orb bolts: each element orb fires a small bolt at the horde
    for e, (x0, y0), (x1, y1) in (("storm", (404, 214), (150, 262)), ("water", (460, 230), (210, 280)),
                                  ("void", (256, 224), (120, 250)), ("fire", (560, 228), (230, 300))):
        c = col(ELEM[e])
        n = 40
        for i in range(n):
            t = 0.25 + i / n * 0.35
            x = x0 + (x1 - x0) * t; y = y0 + (y1 - y0) * t - math.sin(t * math.pi) * 18
            cv.rgb[int(y), int(x)] = np.minimum(c + 0.3 * (i > n - 6), 1)
            cv.emit[int(y), int(x)] += c * (0.4 + 0.08 * i / 4)
        m = np.hypot(cv.xs - x, cv.ys - y) < 2.5
        cv.rgb[m] = np.minimum(c + 0.5, 1); cv.emit[m] += c * 1.4
    # embers drifting up from the clash
    for _ in range(90):
        x, y = rng.uniform(180, 560), rng.uniform(120, 300)
        c = fire if rng.random() < 0.6 else gold
        cv.rgb[int(y), int(x)] = c; cv.emit[int(y), int(x)] += c * 0.9


def foreground(cv):
    """Dark chiselled rocks in the bottom corners to frame the battle."""
    fr = np.array(ramp("3a2e3c", n=5, spread=0.45), np.float32) / 255
    for x0, flip in ((0, False), (W, True)):
        x = 0
        while x < 120:
            w = rng.randint(14, 30); h = max(6, rng.randint(18, 46) - x // 4)
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
    clouds(cv)
    king = rift_and_king(cv)
    mountains(cv)
    towers, sun = solenne(cv)
    beams(cv, towers, sun, king)
    cv.light(sun[0], 150, col("ffc860"), 170, 0.10, 0.0)
    road(cv)
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
