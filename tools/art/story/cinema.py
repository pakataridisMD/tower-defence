"""Building blocks for the 640x360 pixel-art cinematic stills.

A still is painted in float RGB with numpy: dithered skies, fbm ridgelines, cities, glows, particles,
and characters rendered by the SDF rig (rim-lit to match the shot). `finish()` snaps the picture to a
limited number of tones per channel with ordered dithering, so it reads as pixel art and sits next to
the in-game sprites.
"""
from __future__ import annotations

import math
import os
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cast import CAST, body_of  # noqa: E402
from rig import Pose, build  # noqa: E402
from sdf import Camera, Light, hexc, render, to_rgba  # noqa: E402

W, H = 640, 360
PIX = 2  # screen pixels per art pixel: stills are painted at 640x360 but finished at 320x180
BAYER8 = np.array([
    [0, 32, 8, 40, 2, 34, 10, 42], [48, 16, 56, 24, 50, 18, 58, 26], [12, 44, 4, 36, 14, 46, 6, 38],
    [60, 28, 52, 20, 62, 30, 54, 22], [3, 35, 11, 43, 1, 33, 9, 41], [51, 19, 59, 27, 49, 17, 57, 25],
    [15, 47, 7, 39, 13, 45, 5, 37], [63, 31, 55, 23, 61, 29, 53, 21]]) / 64.0


def C(h):
    return hexc(h)


def bayer(h=H, w=W):
    return np.tile(BAYER8, (h // 8 + 1, w // 8 + 1))[:h, :w]


# ---------------------------------------------------------------- noise
def value_noise(h, w, cell, seed):
    rng = np.random.default_rng(seed)
    gh, gw = int(h / cell) + 3, int(w / cell) + 3
    grid = rng.random((gh, gw))
    ys = np.arange(h) / cell
    xs = np.arange(w) / cell
    y0 = np.floor(ys).astype(int)
    x0 = np.floor(xs).astype(int)
    fy = ys - y0
    fx = xs - x0
    fy = fy * fy * (3 - 2 * fy)
    fx = fx * fx * (3 - 2 * fx)
    a = grid[y0][:, x0]
    b = grid[y0][:, x0 + 1]
    c = grid[y0 + 1][:, x0]
    d = grid[y0 + 1][:, x0 + 1]
    top = a + (b - a) * fx[None, :]
    bot = c + (d - c) * fx[None, :]
    return top + (bot - top) * fy[:, None]


def fbm(h, w, cell, seed, octaves=4):
    out = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    for o in range(octaves):
        out += value_noise(h, w, max(cell / 2 ** o, 1.0), seed + o * 17) * amp
        norm += amp
        amp *= 0.5
    return out / norm


def noise1(n, cell, seed, octaves=4):
    return fbm(1, n, cell, seed, octaves)[0]


# ---------------------------------------------------------------- painting
SPRITE_MASK = np.zeros((H, W), bool)  # pixels covered by pasted characters (kept free of dithering)


def canvas(col="000000"):
    SPRITE_MASK[:] = False
    return np.zeros((H, W, 3), np.float32) + C(col)


def vgrad(img, stops, y0=0, y1=H):
    """Vertical gradient through (t, hex) stops between rows y0 and y1."""
    ts = np.array([s[0] for s in stops])
    cols = np.stack([C(s[1]) for s in stops])
    for y in range(max(0, y0), min(H, y1)):
        t = (y - y0) / max(1, y1 - y0)
        for ch in range(3):
            img[y, :, ch] = np.interp(t, ts, cols[:, ch])
    return img


def glow(img, x, y, r, col, amt=1.0, power=2.0, ry=None):
    ys, xs = np.mgrid[0:H, 0:W]
    ry = ry or r
    d = np.sqrt(((xs - x) / r) ** 2 + ((ys - y) / ry) ** 2)
    f = np.clip(1 - d, 0, 1) ** power * amt
    img += f[..., None] * C(col) if isinstance(col, str) else f[..., None] * np.asarray(col, np.float32)
    return img


def darken_edges(img, amt=0.55, power=2.2):
    ys, xs = np.mgrid[0:H, 0:W]
    d = np.sqrt(((xs - W / 2) / (W * 0.62)) ** 2 + ((ys - H / 2) / (H * 0.62)) ** 2)
    img *= (1 - np.clip(d, 0, 1) ** power * amt)[..., None]
    return img


def stars(img, n, seed, ymax=H, bright=1.0, col="e8e8ff"):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, ymax))
        b = rng.random() ** 3 * bright
        img[y, x] = img[y, x] * (1 - b) + C(col) * b
        if b > 0.7 and 1 <= x < W - 1 and 1 <= y < H - 1:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                img[y + dy, x + dx] = img[y + dy, x + dx] * 0.6 + C(col) * 0.4 * b
    return img


def ridge(img, base, amp, cell, col, seed, top_col=None, rim=None, jag=0.0):
    """Fill a mountain/hill silhouette below an fbm ridgeline. Returns the height profile."""
    prof = base - (noise1(W, cell, seed) - 0.5) * 2 * amp
    if jag:
        prof -= np.abs(np.sin(np.arange(W) * 0.13 + seed)) * jag * noise1(W, cell / 3, seed + 5)
    prof = prof.astype(int)
    c = C(col)
    tc = C(top_col) if top_col else c
    for x in range(W):
        y0 = max(0, prof[x])
        if y0 >= H:
            continue
        n = H - y0
        t = np.linspace(0, 1, n)[:, None]
        img[y0:, x] = tc * (1 - np.clip(t * 4, 0, 1)) + c * np.clip(t * 4, 0, 1)
        if rim is not None:
            img[y0, x] = C(rim)
    return prof


def poly(img, pts, col, alpha=1.0):
    """Fill a polygon (list of (x, y))."""
    from PIL import ImageDraw
    m = Image.new("L", (W, H), 0)
    ImageDraw.Draw(m).polygon([tuple(map(float, p)) for p in pts], fill=255)
    a = np.asarray(m, np.float32)[..., None] / 255 * alpha
    c = C(col) if isinstance(col, str) else np.asarray(col, np.float32)
    img[:] = img * (1 - a) + c * a
    return a[..., 0]


def ellipse_mask(cx, cy, rx, ry):
    ys, xs = np.mgrid[0:H, 0:W]
    return ((xs - cx) / rx) ** 2 + ((ys - cy) / ry) ** 2 <= 1


def particles(img, n, seed, box, col, size=(0, 1), bright=(0.5, 1.0), add=True):
    rng = np.random.default_rng(seed)
    x0, y0, x1, y1 = box
    c = C(col)
    for _ in range(n):
        x, y = int(rng.uniform(x0, x1)), int(rng.uniform(y0, y1))
        s = int(rng.integers(size[0], size[1] + 1))
        b = rng.uniform(*bright)
        ys, ye, xs, xe = max(0, y - s), min(H, y + s + 1), max(0, x - s), min(W, x + s + 1)
        if ye <= ys or xe <= xs:  # off-canvas (a negative end would wrap round and paint a whole column)
            continue
        if add:
            img[ys:ye, xs:xe] += c * b
        else:
            img[ys:ye, xs:xe] = img[ys:ye, xs:xe] * (1 - b) + c * b
    return img


# ---------------------------------------------------------------- characters in a shot
def figure(cid, pose=None, height_px=80, yaw=-0.75, pitch=0.15, rim=None, rim_amt=0.9, key=None, spec_over=None,
           mats_over=None, ambient=0.18):
    """Render a cast member to RGBA at roughly height_px tall. Returns (rgba, foot_x, foot_y) in the image."""
    c = CAST[cid]
    body = body_of(cid)
    spec = dict(c["spec"], **(spec_over or {}))
    mats = dict(c["mats"], **(mats_over or {}))
    pose = pose or Pose()
    height_px = height_px / PIX  # render at art-pixel resolution, then blow up by PIX
    scale = height_px / (body.height * 1.08)
    w = int(height_px * 1.6) + 8
    h = int(height_px * 1.45) + 8
    cy = body.height * 0.55
    cam = Camera(w, h, (0.0, cy, 0.0), scale, yaw=yaw, pitch=pitch)
    light = Light(rim_col=rim or c.get("rim", (255, 200, 140)), rim_amt=rim_amt, ambient=ambient)
    if key is not None:
        light.key = key
    r = render(build(spec, body, pose), mats, cam, light)
    rgba = to_rgba(r)
    foot_y = int(h / 2 + cy * scale * math.cos(pitch))
    rgba = np.kron(rgba, np.ones((PIX, PIX, 1), np.uint8))
    return rgba, w // 2 * PIX, foot_y * PIX, r


def paste(img, rgba, x, y, ax=0.5, ay=1.0, alpha=1.0, glow_map=None):
    """Paste rgba with its anchor (ax, ay of its size, or a pixel offset if given as ints) at (x, y)."""
    h, w = rgba.shape[:2]
    ox = int(x - (ax * w if isinstance(ax, float) else ax)) // PIX * PIX
    oy = int(y - (ay * h if isinstance(ay, float) else ay)) // PIX * PIX
    xs0, ys0 = max(0, ox), max(0, oy)
    xs1, ys1 = min(W, ox + w), min(H, oy + h)
    if xs1 <= xs0 or ys1 <= ys0:
        return
    sub = rgba[ys0 - oy:ys1 - oy, xs0 - ox:xs1 - ox].astype(np.float32)
    a = sub[..., 3:4] / 255.0 * alpha
    if alpha >= 0.99:
        SPRITE_MASK[ys0:ys1, xs0:xs1] |= sub[..., 3] > 127
    img[ys0:ys1, xs0:xs1] = img[ys0:ys1, xs0:xs1] * (1 - a) + sub[..., :3] * a


def tint(rgba, col, amt):
    out = rgba.copy().astype(np.float32)
    out[..., :3] = out[..., :3] * (1 - amt) + C(col) * amt
    return np.clip(out, 0, 255).astype(np.uint8)


def silhouette(rgba, col, rim_col=None, rim_side=1):
    """Flat silhouette with an optional 1 px rim on one side (light behind the figure)."""
    out = rgba.copy()
    a = out[..., 3] > 0
    out[a, :3] = C(col)
    if rim_col is not None:
        edge = a & ~np.roll(a, rim_side, axis=1)
        edge |= a & ~np.roll(a, 1, axis=0)
        out[edge, :3] = C(rim_col)
    return out


def scale_nearest(rgba, f):
    h, w = rgba.shape[:2]
    return np.asarray(Image.fromarray(rgba).resize((max(1, int(w * f)), max(1, int(h * f))), Image.NEAREST))


# ---------------------------------------------------------------- set pieces
def black_sun(img, cx, cy, r, seed=3, corona_col="d8c8ff", gap_dir=-math.pi / 2):
    """A black sun whose corona has a crown-shaped gap (three teeth) cut out of it, showing nothing."""
    ys, xs = np.mgrid[0:H, 0:W]
    dx, dy = xs - cx, ys - cy
    d = np.sqrt(dx * dx + dy * dy)
    ang = np.arctan2(dy, dx)
    rng = np.random.default_rng(seed)
    rays = np.zeros_like(d)
    for k in range(9):
        f = rng.integers(5, 23)
        ph = rng.uniform(0, 6.28)
        rays += np.maximum(0, np.sin(ang * f + ph)) ** 3 * rng.uniform(0.3, 1.0)
    rays /= 9
    reach = r * (1.35 + 1.4 * rays)
    corona = np.clip(1 - (d - r) / (reach - r + 1e-6), 0, 1) * (d > r)
    # crown-shaped gap: an angular window around gap_dir with three teeth biting outward
    rel = (ang - gap_dir + math.pi) % (2 * math.pi) - math.pi
    width = 0.55
    inside = np.abs(rel) < width
    teeth = (np.cos(rel / width * math.pi * 1.5) > 0.0)
    gap_reach = np.where(teeth, r * 3.2, r * 1.6)
    hole = inside & (d < gap_reach) & (d > r * 0.98)
    corona = np.where(hole, 0, corona)
    img += (corona ** 1.6)[..., None] * C(corona_col) * 0.9
    img[hole] = img[hole] * 0.15  # nothing shows through the gap, not even stars
    disc = d <= r
    img[disc] = C("050308")
    ring = (d > r - 1.2) & (d <= r + 0.8) & ~hole
    img[ring] = C(corona_col) * 0.9 + 20
    return img


def element_sea(img, y0, y1, seed=1, sat=1.0):
    """The churning sea of every colour at once (prologue shot 1)."""
    cols = np.stack([C(c) for c in ("e8502a", "e8e8ff", "6ad04a", "2ac0c0", "d89a3a", "8a4ad8")])
    hh = y1 - y0
    warp = fbm(hh, W, 90, seed + 1) * 6
    n = fbm(hh, W, 70, seed) * 6 + warp
    idx0 = np.floor(n).astype(int) % 6
    t = n - np.floor(n)
    t = t * t * (3 - 2 * t)
    c = cols[idx0] * (1 - t[..., None]) + cols[(idx0 + 1) % 6] * t[..., None]
    shade = fbm(hh, W, 25, seed + 3)
    c = c * (0.35 + 0.8 * shade[..., None]) * sat
    img[y0:y1] = c
    return img


def smoke(img, x, y_base, height, col="3a3036", seed=0, lean=0.4, width=14, amt=0.85):
    """A rising smoke column: fbm puffs inside a cone that widens and leans with height."""
    ys, xs = np.mgrid[0:H, 0:W]
    t = np.clip((y_base - ys) / height, 0, 1)
    centre = x + lean * (y_base - ys) + np.sin(t * 5 + seed) * 8
    half = width * (0.4 + 2.2 * t)
    n = fbm(H, W, 14, seed + 300)
    inside = (np.abs(xs - centre) < half * (0.6 + 0.8 * n)) & (ys < y_base) & (ys > y_base - height)
    dens = np.clip(1 - np.abs(xs - centre) / (half + 1e-6), 0, 1) * (1 - t ** 2) * (0.5 + n)
    a = (inside * np.clip(dens, 0, 1) * amt)[..., None]
    shade = (0.75 + 0.5 * (n - 0.5))[..., None]
    img[:] = img * (1 - a) + C(col) * shade * a
    return img


def rotate_rgba(rgba, deg):
    return np.asarray(Image.fromarray(rgba).rotate(deg, resample=Image.NEAREST, expand=True))


def finish(img, levels=14, dither=0.9, grade=None):
    """Snap to pixel-art tones: ordered dithering to `levels` steps per channel."""
    out = np.clip(img, 0, 255) / 255.0
    if grade is not None:
        out = out * (1 - grade[1]) + out * C(grade[0]) / 255.0 * grade[1]
    # down to art pixels (2x2 average: characters pasted as 2x2 blocks come through exactly)
    out = out.reshape(H // PIX, PIX, W // PIX, PIX, 3).mean((1, 3))
    b = bayer(H // PIX, W // PIX)[..., None]
    q = np.floor(out * (levels - 1) + (b - 0.5) * dither + 0.5) / (levels - 1)
    m = SPRITE_MASK.reshape(H // PIX, PIX, W // PIX, PIX).all((1, 3))
    q[m] = out[m]
    q = (np.clip(q, 0, 1) * 255).astype(np.uint8)
    return np.kron(q, np.ones((PIX, PIX, 1), np.uint8))


def save(img8, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    Image.fromarray(img8).save(path)
