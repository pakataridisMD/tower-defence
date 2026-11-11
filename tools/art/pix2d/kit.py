"""2D pixel-art kit: creatures are drawn part by part, straight onto a small canvas.

Each part is a flat shape (ellipse, polygon, capsule) with a colour ramp. The kit rounds the shape into a soft dome,
lights it from the upper left (like every other sprite in the game), and snaps the light to the ramp's few tones,
so parts come out as clean cel-shaded clusters rather than gradients. Parts drawn later sit on top and get a dark
line on their shadow side. `ink()` adds the outline. A normal map is written alongside for the game's 2D lights.
"""
from __future__ import annotations

import colorsys
import math

import numpy as np
from PIL import Image, ImageDraw

LIGHT = np.array([-0.5, -0.62, 0.6])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
INK = (26, 18, 24)


def hexc(h):
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(base, n=5, spread=0.5, shift=0.035):
    """n tones from shadow to highlight around a base colour; shadows lean cool, lights lean warm."""
    r, g, b = [c / 255 for c in hexc(base)]
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    out = []
    for i in range(n):
        t = i / (n - 1) - 0.5                      # -0.5 shadow .. +0.5 light
        ll = min(0.93, max(0.05, l + t * spread * (0.8 if t > 0 else 1.1)))
        target = 0.13 if t > 0 else 0.72           # warm yellow for lights, blue-violet for shadows
        dh = ((target - h + 0.5) % 1.0) - 0.5
        hh = (h + dh * abs(t) * 2 * shift * 4) % 1.0
        ss = min(1.0, max(0.0, s * (1.0 - 0.5 * t if t > 0 else 1.0 - 0.25 * t)))
        out.append(tuple(int(c * 255) for c in colorsys.hls_to_rgb(hh, ll, ss)))
    return out


IDENT = np.array([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]])


def _tf(rot, px, py, dx, dy):
    """2x3 matrix: rotate by rot (clockwise on screen) about (px, py), then move by (dx, dy)."""
    c, s = math.cos(rot), math.sin(rot)
    return np.array([[c, -s, px - c * px + s * py + dx], [s, c, py - s * px - c * py + dy]])


def _mul(a, b):
    """a after b."""
    A = np.vstack([a, [0, 0, 1]])
    B = np.vstack([b, [0, 0, 1]])
    return (A @ B)[:2]


class Sprite:
    """Canvas for one creature frame.

    pose: None for the rest pose, or {group: (rot, dx, dy)} plus optional "_all" for the whole creature. The drawing
    code names the group it is about to draw with g(name, pivot_x, pivot_y, parent); every shape after that is moved
    by the pose. Groups chain through their parents (thigh > shin, upper arm > forearm > weapon, neck > head > jaw). pad adds empty space on all sides so swings
    and falls are not clipped; drawing coordinates stay those of the rest pose.
    """

    def __init__(self, w, h, pose=None, pad=0):
        self.bw, self.bh, self.pad = w, h, pad
        w, h = w + 2 * pad, h + 2 * pad
        self.w, self.h = w, h
        self.pose = pose or {}
        r, dx, dy = self.pose.get("_all", (0, 0, 0))
        self._base = _mul(_tf(r, self.bw / 2 + pad, self.bh - 5 + pad, dx, dy), _tf(0, 0, 0, pad, pad))
        r, dx, dy = self.pose.get("body", (0, 0, 0))
        self._body = _tf(r, self.bw / 2, self.bh * 0.65, dx, dy)
        self.M = self._base if not self.pose and not pad else _mul(self._base, self._body)
        self._ident = not self.pose and not pad
        self._world = {"body": self._body}
        self.rgb = np.zeros((h, w, 3), np.uint8)
        self.a = np.zeros((h, w), bool)
        self.nrm = np.zeros((h, w, 3), np.float32)
        self.nrm[..., 2] = 1
        self.glow = np.zeros((h, w), bool)
        self.part_id = np.zeros((h, w), np.int32)
        self._n = 0
        self.ys, self.xs = np.mgrid[0:h, 0:w]

    # ---- pose groups ----------------------------------------------------------------------------
    def g(self, name="body", px=0.0, py=0.0, parent=None):
        """Everything drawn after this belongs to group `name`, which turns about the joint (px, py).

        parent: a group named earlier that this one hangs from (a shin from its thigh, a forearm from the upper arm).
        Without a parent, legs hang from the ground frame and every other group from "body".
        """
        if self._ident:
            return
        if name == "body":
            self.M = _mul(self._base, self._body)
            return
        r, dx, dy = self.pose.get(name, (0, 0, 0))
        m = _tf(r, px, py, dx, dy)
        if parent:
            up = self._world[parent]
        else:
            up = IDENT if name.startswith("leg") else self._body
        self._world[name] = _mul(up, m)
        self.M = _mul(self._base, self._world[name])

    def fw(self, x, y):
        """Where a rest-pose point lands on the canvas."""
        if self._ident:
            return x, y
        return (self.M[0, 0] * x + self.M[0, 1] * y + self.M[0, 2], self.M[1, 0] * x + self.M[1, 1] * y + self.M[1, 2])

    def _inv(self):
        """Canvas pixel centres mapped back into rest-pose coordinates."""
        ys, xs = np.mgrid[0:self.h, 0:self.w]
        px, py = xs + 0.5, ys + 0.5
        if self._ident:
            return px, py
        A = np.linalg.inv(np.vstack([self.M, [0, 0, 1]]))
        return A[0, 0] * px + A[0, 1] * py + A[0, 2], A[1, 0] * px + A[1, 1] * py + A[1, 2]

    # ---- shapes (boolean masks) -----------------------------------------------------------------
    def _mask(self, draw_fn):
        im = Image.new("1", (self.w, self.h), 0)
        draw_fn(ImageDraw.Draw(im))
        return np.asarray(im, bool)

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        px, py = self._inv()
        dx, dy = px - cx, py - cy
        c, s = math.cos(rot), math.sin(rot)
        u, v = dx * c + dy * s, -dx * s + dy * c
        return (u / rx) ** 2 + (v / ry) ** 2 <= 1.0

    def poly(self, pts):
        pts = [self.fw(x, y) for x, y in pts]
        return self._mask(lambda d: d.polygon([(round(x), round(y)) for x, y in pts], fill=1))

    def capsule(self, x0, y0, x1, y1, r0, r1=None):
        r1 = r0 if r1 is None else r1
        px, py = self._inv()
        dx, dy = x1 - x0, y1 - y0
        L2 = dx * dx + dy * dy or 1e-6
        t = np.clip(((px - x0) * dx + (py - y0) * dy) / L2, 0, 1)
        d = np.hypot(px - (x0 + t * dx), py - (y0 + t * dy))
        return d <= r0 + (r1 - r0) * t

    def rect(self, x0, y0, x1, y1):
        if not self._ident:
            return self.poly([(x0, y0), (x1 - 1, y0), (x1 - 1, y1 - 1), (x0, y1 - 1)])
        m = np.zeros((self.h, self.w), bool)
        m[int(y0):int(y1), int(x0):int(x1)] = True
        return m

    # ---- painting -------------------------------------------------------------------------------
    def part(self, mask, tones, bulge=1.0, flat=False, edge=True, light=None, bias=0.0, glow=False):
        """Paint a shape as a rounded, lit form. tones: ramp (dark to light). bias shifts it lighter or darker."""
        if not mask.any():
            return mask
        self._n += 1
        # dome height from distance to the shape's edge
        d = np.zeros(mask.shape, np.float32)
        cur = mask.copy()
        k = 0
        while cur.any() and k < 40:
            d[cur] += 1
            er = cur.copy()
            er[1:] &= cur[:-1]
            er[:-1] &= cur[1:]
            er[:, 1:] &= cur[:, :-1]
            er[:, :-1] &= cur[:, 1:]
            er[0] = er[-1] = False
            er[:, 0] = er[:, -1] = False
            cur = er
            k += 1
        R = max(d.max(), 1.0)
        hgt = np.sqrt(np.clip(1 - (1 - np.clip(d / R, 0, 1)) ** 2, 0, 1)) * R * bulge
        # smooth the height a little so the tone bands are clean clusters
        pad = np.pad(hgt, 1, mode="edge")
        hgt = (pad[1:-1, 1:-1] * 4 + pad[:-2, 1:-1] + pad[2:, 1:-1] + pad[1:-1, :-2] + pad[1:-1, 2:]) / 8
        gy, gx = np.gradient(hgt)
        n = np.stack([-gx, -gy, np.ones_like(gx) * (1.0 if not flat else 6.0)], -1)
        n /= np.linalg.norm(n, axis=-1, keepdims=True)
        L = LIGHT if light is None else np.asarray(light) / np.linalg.norm(light)
        sh = n @ L + bias
        nt = len(tones)
        idx = np.clip(((sh - 0.12) / 0.98 * nt).astype(int), 0, nt - 1)
        cols = np.array(tones, np.uint8)[idx]
        self.rgb[mask] = cols[mask]
        self.nrm[mask] = n[mask]
        self.glow[mask] = glow
        if edge and self.a.any():  # a dark line where this part overlaps what is under it, on the shadow side
            under = self.a & ~mask
            sx = np.zeros_like(mask)
            sx[:, :-1] |= mask[:, :-1] & under[:, 1:]
            sx[:-1] |= mask[:-1] & under[1:]
            self.rgb[sx] = tones[0]
        self.a |= mask
        self.part_id[mask] = self._n
        return mask

    def px(self, x, y, col, glow=False):
        if not self._ident:
            x, y = self.fw(x, y)
            x, y = round(x), round(y)
        if 0 <= x < self.w and 0 <= y < self.h:
            self.rgb[int(y), int(x)] = col
            self.a[int(y), int(x)] = True
            self.glow[int(y), int(x)] = glow

    def pxs(self, pts, col, glow=False):
        for x, y in pts:
            self.px(x, y, col, glow)

    def line(self, x0, y0, x1, y1, col, glow=False):
        if not self._ident:
            (x0, y0), (x1, y1) = self.fw(x0, y0), self.fw(x1, y1)
        n = int(max(abs(x1 - x0), abs(y1 - y0))) + 1
        ident, self._ident = self._ident, True
        for i in range(n + 1):
            t = i / max(n, 1)
            self.px(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), col, glow)
        self._ident = ident

    def fill(self, mask, col, glow=False):
        self.rgb[mask] = col
        self.a |= mask
        self.glow[mask] = glow

    def ink(self, col=INK):
        a = self.a
        out = np.zeros_like(a)
        out[1:] |= a[:-1]
        out[:-1] |= a[1:]
        out[:, 1:] |= a[:, :-1]
        out[:, :-1] |= a[:, 1:]
        edge = out & ~a
        # glowing parts get a softer, coloured edge instead of black
        g = self.glow
        gn = np.zeros_like(a)
        gn[1:] |= g[:-1]
        gn[:-1] |= g[1:]
        gn[:, 1:] |= g[:, :-1]
        gn[:, :-1] |= g[:, 1:]
        self.rgb[edge] = col
        self.a |= edge

    def shadow(self, cx, cy, rx, ry):
        """Soft ground shadow drawn under everything (call last)."""
        ident, self._ident = self._ident, True
        m = self.ellipse(cx + self.pad, cy + self.pad, rx, ry) & ~self.a
        self._ident = ident
        self.rgb[m] = (18, 16, 26)
        self._shadow = m

    def image(self):
        al = self.a.astype(np.uint8) * 255
        if hasattr(self, "_shadow"):
            al[self._shadow & ~self.a] = 90
        return Image.fromarray(np.dstack([self.rgb, al]), "RGBA")

    def normal_image(self):
        n = self.nrm * 0.5 + 0.5
        n[..., 1] = 1 - n[..., 1]
        return Image.fromarray(np.dstack([(n * 255).astype(np.uint8), self.a.astype(np.uint8) * 255]), "RGBA")
