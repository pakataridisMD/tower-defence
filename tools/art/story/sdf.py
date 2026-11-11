"""A tiny signed-distance-field renderer that turns posed 3D characters into lit pixel art.

Characters are built from rounded primitives (spheres, ellipsoids, round cones, boxes) blended with
smooth unions, like clay. Each pixel is sphere-traced straight through an orthographic camera, then
lit with a warm key light from the upper left (the same direction the in-game sprites use), a
coloured rim light from behind and a little ambient occlusion. The light level is snapped onto a
hue-shifted colour ramp per material, and a 1 px ink outline goes round the silhouette, so the result
matches the hand-drawn look of tools/art/gen_game_art.py.

Everything is numpy and deterministic. Coordinates: x right, y up, z towards the viewer; a character
stands on y=0 facing +x.
"""
from __future__ import annotations

import colorsys
import math
from dataclasses import dataclass, field

import numpy as np

INK = np.array([0x17, 0x15, 0x1B], np.float32)


# ---------------------------------------------------------------- colour ramps
def hexc(s: str) -> np.ndarray:
    s = s.lstrip("#")
    return np.array([int(s[i:i + 2], 16) for i in (0, 2, 4)], np.float32)


def make_ramp(base: str, n: int = 6, spread: float = 0.62, hue_shift: float = 0.06, sat_bias: float = 0.0) -> np.ndarray:
    """A pixel-art ramp around `base`: shadows drift toward blue-violet and lose value, lights toward
    warm yellow and lose saturation, which is what makes pixel shading look painted rather than grey."""
    r, g, b = hexc(base) / 255.0
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    out = []
    for i in range(n):
        t = i / (n - 1) * 2 - 1  # -1 darkest .. +1 lightest
        # hue moves toward 0.70 (violet) in shadow and 0.13 (yellow) in light
        target = 0.70 if t < 0 else 0.13
        dh = ((target - h + 0.5) % 1.0) - 0.5
        hh = (h + dh * hue_shift * abs(t) * 2.2) % 1.0
        ss = np.clip(s * (1 + 0.25 * -t) + sat_bias - (0.18 * t if t > 0 else 0) , 0, 1)
        vv = np.clip(v * (1 + spread * t) if t < 0 else v + (1 - v) * spread * 0.8 * t, 0.03, 1)
        out.append(np.array(colorsys.hsv_to_rgb(hh, ss, vv)) * 255)
    return np.array(out, np.float32)


@dataclass
class Material:
    ramp: np.ndarray                 # (n, 3) dark .. light
    emissive: bool = False           # drawn at full brightness and written to the glow map
    spec: float = 0.0                # strength of a hard specular highlight (metal, eyes, gems)
    rim: float = 1.0                 # how much rim light it catches
    bands: float = 1.0               # contrast of the light ramp
    flat: float = 0.0                # 1 = ignore lighting entirely (eyes, runes)
    tex: float = 0.0                 # strength of surface texture noise (cloth weave, hair strands, stone)
    tex_freq: float = 60.0
    tex_axis: str = ""


def mat(base: str, **kw) -> Material:
    n = kw.pop("n", 6)
    spread = kw.pop("spread", 0.62)
    hue_shift = kw.pop("hue_shift", 0.06)
    return Material(make_ramp(base, n, spread, hue_shift), **kw)


def glow_mat(base: str, **kw) -> Material:
    r = make_ramp(base, 5, 0.5, 0.03)
    return Material(r, emissive=True, **kw)


# ---------------------------------------------------------------- primitives
@dataclass
class Prim:
    kind: str
    a: tuple                         # parameters, meaning depends on kind
    mat: str
    k: float = 0.0                   # smooth-union radius with what came before
    sub: bool = False                # carve instead of add
    disp: tuple | None = None        # (amplitude, frequency, axis, seed) surface folds
    layer: int = 0                   # smooth unions only blend within a layer


def sphere(c, r, m, k=0.0, **kw):
    return Prim("sphere", (np.array(c, np.float32), r), m, k, **kw)


def ellipsoid(c, radii, m, k=0.0, rot=None, **kw):
    return Prim("ellip", (np.array(c, np.float32), np.array(radii, np.float32), rot), m, k, **kw)


def cone(a, b, ra, rb, m, k=0.0, **kw):
    """Round cone (capsule with two radii) from point a to point b."""
    return Prim("rcone", (np.array(a, np.float32), np.array(b, np.float32), ra, rb), m, k, **kw)


def box(c, half, m, k=0.0, round_=0.0, rot=None, **kw):
    return Prim("box", (np.array(c, np.float32), np.array(half, np.float32), round_, rot), m, k, **kw)


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float32)


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float32)


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]], np.float32)


def _dist(p: Prim, q: np.ndarray) -> np.ndarray:
    if p.kind == "sphere":
        c, r = p.a
        d = np.linalg.norm(q - c, axis=-1) - r
    elif p.kind == "ellip":
        c, radii, rot = p.a
        v = q - c
        if rot is not None:
            v = v @ rot  # rot maps local->world, so world->local is v @ rot
        k0 = np.linalg.norm(v / radii, axis=-1)
        k1 = np.linalg.norm(v / (radii * radii), axis=-1)
        d = k0 * (k0 - 1.0) / np.maximum(k1, 1e-6)
    elif p.kind == "rcone":
        a, b, r1, r2 = p.a
        ba = b - a
        l2 = float(ba @ ba)
        if l2 < 1e-9:
            d = np.linalg.norm(q - a, axis=-1) - max(r1, r2)
        else:
            # exact round cone (Inigo Quilez)
            rr = r1 - r2
            a2 = l2 - rr * rr
            il2 = 1.0 / l2
            pa = q - a
            y = pa @ ba
            z = y - l2
            xv = pa * l2 - y[..., None] * ba
            x2 = (xv * xv).sum(-1)
            y2 = y * y * l2
            z2 = z * z * l2
            kk = np.sign(rr) * rr * rr * x2
            d = np.where(np.sign(z) * a2 * z2 > kk, np.sqrt(x2 + z2) * il2 - r2,
                         np.where(np.sign(y) * a2 * y2 < kk, np.sqrt(x2 + y2) * il2 - r1,
                                  (np.sqrt(np.maximum(x2 * a2 * il2, 0)) + y * rr) * il2 - r1))
    elif p.kind == "box":
        c, half, rnd, rot = p.a
        v = q - c
        if rot is not None:
            v = v @ rot
        qq = np.abs(v) - half + rnd
        d = np.linalg.norm(np.maximum(qq, 0), axis=-1) + np.minimum(qq.max(-1), 0) - rnd
    else:
        raise ValueError(p.kind)
    if p.disp is not None:
        amp, freq, axis, seed = p.disp
        d = d + amp * _folds(q, freq, axis, seed)
    return d


_FOLD_CACHE: dict = {}


def _folds(q, freq, axis, seed):
    """Smooth pseudo-noise made from a few sines; `axis` stretches it so folds run along a direction."""
    key = (freq, axis, seed)
    if key not in _FOLD_CACHE:
        rng = np.random.default_rng(seed)
        dirs = rng.normal(size=(5, 3)).astype(np.float32)
        if axis == "y":      # folds that hang down: vary mostly around, little along y
            dirs[:, 1] *= 0.15
        elif axis == "x":
            dirs[:, 0] *= 0.15
        dirs /= np.linalg.norm(dirs, axis=1, keepdims=True)
        _FOLD_CACHE[key] = (dirs * freq, rng.uniform(0, 6.28, 5).astype(np.float32))
    dirs, ph = _FOLD_CACHE[key]
    return np.sin(q @ dirs.T + ph).mean(-1)


def _smin(a, b, k):
    if k <= 0:
        return np.minimum(a, b)
    h = np.clip(0.5 + 0.5 * (b - a) / k, 0, 1)
    return b * (1 - h) + a * h - k * h * (1 - h)


def scene_dist(prims: list[Prim], q: np.ndarray, want_mat: bool = False):
    """Distance to the model; with want_mat also the index of the material at each point."""
    layers: dict[int, np.ndarray] = {}
    best = np.full(q.shape[:-1], 1e9, np.float32)
    mid = np.full(q.shape[:-1], -1, np.int32)
    for i, p in enumerate(prims):
        d = _dist(p, q)
        cur = layers.get(p.layer)
        if p.sub:
            if cur is not None:
                cur = np.maximum(cur, -d) if p.k <= 0 else -_smin(-cur, d, p.k)
                layers[p.layer] = cur
            continue
        if want_mat:
            closer = d < best
            best = np.where(closer, d, best)
            mid = np.where(closer, i, mid)
        layers[p.layer] = d if cur is None else _smin(cur, d, p.k)
    total = None
    for d in layers.values():
        total = d if total is None else np.minimum(total, d)
    if want_mat:
        return total, mid
    return total


# ---------------------------------------------------------------- camera and render
@dataclass
class Camera:
    width: int
    height: int
    center: tuple          # world point at the image centre
    scale: float           # pixels per world unit
    yaw: float = 0.0       # radians, turns the model (positive shows more of its front when it faces +x)
    pitch: float = 0.0     # radians, looks down on the model


@dataclass
class Light:
    key: tuple = (-0.55, 0.65, 0.55)
    rim: tuple = (0.7, 0.3, -0.65)
    rim_col: tuple = (255, 200, 140)
    rim_amt: float = 0.7
    ambient: float = 0.18
    fill: tuple = (0.6, -0.2, 0.5)
    fill_amt: float = 0.12


@dataclass
class Render:
    rgb: np.ndarray
    alpha: np.ndarray
    nrm: np.ndarray
    glow: np.ndarray
    depth: np.ndarray
    matid: np.ndarray = field(default=None)


def render(prims: list[Prim], mats: dict[str, Material], cam: Camera, light: Light = Light(),
           outline: bool = True, inner_lines: bool = True, steps: int = 72) -> Render:
    w, h = cam.width, cam.height
    R = rot_x(cam.pitch) @ rot_y(cam.yaw)        # world -> camera
    Rt = R.T
    xs = (np.arange(w) + 0.5 - w / 2) / cam.scale
    ys = -(np.arange(h) + 0.5 - h / 2) / cam.scale
    X, Y = np.meshgrid(xs, ys)
    zfar = 6.0
    # pixel rays in camera space, from z=+zfar towards -z
    o_cam = np.stack([X, Y, np.full_like(X, zfar)], -1).reshape(-1, 3).astype(np.float32)
    dir_cam = np.array([0, 0, -1], np.float32)
    center = np.array(cam.center, np.float32)
    o = o_cam @ R + center        # camera -> world: v_world = Rt @ v_cam  ==  v_cam @ R
    dvec = dir_cam @ R
    t = np.zeros(len(o), np.float32)
    hit = np.zeros(len(o), bool)
    alive = np.ones(len(o), bool)
    eps = 0.35 / cam.scale
    for _ in range(steps):
        idx = np.nonzero(alive)[0]
        if len(idx) == 0:
            break
        q = o[idx] + t[idx, None] * dvec
        d = scene_dist(prims, q)
        t[idx] += d * 0.9
        done = d < eps
        hit[idx[done]] = True
        gone = t[idx] > zfar * 2
        alive[idx[done | gone]] = False
    n_px = w * h
    rgb = np.zeros((n_px, 3), np.float32)
    nrm = np.zeros((n_px, 3), np.float32)
    nrm[:, 2] = 1
    glow = np.zeros((n_px, 4), np.uint8)
    depth = np.full(n_px, -1e9, np.float32)
    matid = np.full(n_px, -1, np.int32)
    hi = np.nonzero(hit)[0]
    if len(hi):
        p = o[hi] + t[hi, None] * dvec
        _, mid = scene_dist(prims, p, want_mat=True)
        e = 0.5 / cam.scale
        grads = []
        for ax in range(3):
            dv = np.zeros(3, np.float32)
            dv[ax] = e
            grads.append(scene_dist(prims, p + dv) - scene_dist(prims, p - dv))
        n = np.stack(grads, -1)
        n /= np.maximum(np.linalg.norm(n, axis=-1, keepdims=True), 1e-6)
        # ambient occlusion: how much the field shrinks along the normal
        ao = np.zeros(len(hi), np.float32)
        for i, step in enumerate((0.03, 0.07, 0.12)):
            ao += (step - scene_dist(prims, p + n * step)) / (2 ** i)
        ao = np.clip(1 - ao * 3.0, 0.35, 1)
        n_cam = n @ Rt        # world -> camera: v_cam = R @ v_world == v_world @ Rt
        L = np.array(light.key, np.float32) @ np.eye(3)
        L /= np.linalg.norm(L)
        Lr = np.array(light.rim, np.float32)
        Lr /= np.linalg.norm(Lr)
        Lf = np.array(light.fill, np.float32)
        Lf /= np.linalg.norm(Lf)
        # lights are given in camera space so every view is lit from the same screen direction
        diff = np.clip(n_cam @ L, 0, 1)
        fill = np.clip(n_cam @ Lf, 0, 1) * light.fill_amt
        rimv = np.clip(n_cam @ Lr, 0, 1) * np.clip(1 - n_cam[:, 2], 0, 1) ** 0.6
        names = [pr.mat for pr in prims]
        mat_names = sorted(set(names))
        for mn in mat_names:
            m = mats[mn]
            sel = np.array([names[j] == mn for j in mid], bool) if len(mid) else np.zeros(0, bool)
            if not sel.any():
                continue
            lvl = light.ambient + diff[sel] * 0.95 + fill[sel]
            lvl = lvl * (0.55 + 0.45 * ao[sel])
            lvl = 0.5 + (lvl - 0.5) * m.bands
            if m.tex > 0:
                lvl = lvl + _folds(p[sel], m.tex_freq, m.tex_axis, 99) * m.tex
            if m.flat:
                lvl = lvl * (1 - m.flat) + 0.75 * m.flat
            if m.emissive:
                lvl = 0.55 + 0.45 * lvl
            ramp = m.ramp
            k = len(ramp)
            ix = np.clip((lvl * k).astype(int), 0, k - 1)
            col = ramp[ix].copy()
            if m.spec > 0:
                hv = L + np.array([0, 0, 1], np.float32)
                hv /= np.linalg.norm(hv)
                sp = np.clip(n_cam[sel] @ hv, 0, 1) ** 40 * m.spec
                col = np.where((sp > 0.45)[:, None], ramp[-1] * 0.5 + 255 * 0.5, col)
            if m.rim > 0 and not m.emissive:
                rc = np.array(light.rim_col, np.float32)
                ra = rimv[sel] * light.rim_amt * m.rim
                band = (ra > 0.5).astype(np.float32)[:, None]
                col = col * (1 - band * 0.45) + rc * band * 0.45 * (0.5 + 0.5 * col / 255)
            rgb[hi[sel]] = col
            if m.emissive:
                glow[hi[sel], :3] = np.clip(col, 0, 255).astype(np.uint8)
                glow[hi[sel], 3] = 255
        matid[hi] = np.array([mat_names.index(names[j]) for j in mid])
        nrm[hi] = n_cam
        depth[hi] = -t[hi]
    rgb = rgb.reshape(h, w, 3)
    alpha = hit.reshape(h, w).astype(np.uint8) * 255
    nrm = nrm.reshape(h, w, 3)
    glow = glow.reshape(h, w, 4)
    depth = depth.reshape(h, w)
    matid = matid.reshape(h, w)
    if inner_lines:
        _inner_lines(rgb, alpha, depth, matid, 3.0 / cam.scale)
    r = Render(rgb, alpha, nrm, glow, depth, matid)
    if outline:
        add_outline(r)
    return r


def _inner_lines(rgb, alpha, depth, matid, gap):
    """Darken the far side of depth steps inside the silhouette (selective outlines)."""
    a = alpha > 0
    edge = np.zeros_like(a)
    for dy, dx in ((0, 1), (1, 0), (0, -1), (-1, 0)):
        nd = np.roll(np.roll(depth, dy, 0), dx, 1)
        na = np.roll(np.roll(a, dy, 0), dx, 1)
        edge |= a & na & (nd - depth > gap)
    rgb[edge] = rgb[edge] * 0.45 + INK * 0.55


def add_outline(r: Render, col=INK) -> None:
    a = r.alpha > 0
    grown = a.copy()
    grown[1:, :] |= a[:-1, :]
    grown[:-1, :] |= a[1:, :]
    grown[:, 1:] |= a[:, :-1]
    grown[:, :-1] |= a[:, 1:]
    ring = grown & ~a
    r.rgb[ring] = col
    r.alpha[ring] = 255
    r.nrm[ring] = (0, 0, 1)


def to_rgba(r: Render) -> np.ndarray:
    out = np.zeros(r.rgb.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip(r.rgb + 0.5, 0, 255).astype(np.uint8)
    out[..., 3] = r.alpha
    return out


def normals_rgba(r: Render) -> np.ndarray:
    out = np.zeros(r.rgb.shape[:2] + (4,), np.uint8)
    out[..., :3] = np.clip((r.nrm * 0.5 + 0.5) * 255 + 0.5, 0, 255).astype(np.uint8)
    out[..., 3] = r.alpha
    return out
