#!/usr/bin/env python3
"""Renders the story characters: portraits, animated battle sprites and sprite sheets.

These are design renders for review. Nothing here is loaded by the game until it is approved.

Writes to art/story/ (and copies previews to --preview DIR if given):
  characters/<id>/portrait.png         96x96 bust on a painted background
  characters/<id>/portrait_clear.png   same bust, transparent background
  characters/<id>/<anim>_<n>.png       battle sprite frames (+ _n.png normal maps, _glow.png)
  characters/<id>/sheet.png            every animation, one row each
  characters/<id>/preview.gif          the animations played back, enlarged
  characters/<id>/card.png             portrait + sheet, enlarged, for review

Run from the repository root:  python3 tools/art/story/gen_story_art.py [ids...] [--preview DIR]
Needs numpy and Pillow.
"""
from __future__ import annotations

import argparse
import os
import shutil
import sys

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cast import CAST, body_of  # noqa: E402
from rig import ANIMS, Pose, build  # noqa: E402
from sdf import INK, Camera, Light, hexc, normals_rgba, render, to_rgba  # noqa: E402

OUT = os.path.join("art", "story", "characters")
SPRITE_W, SPRITE_H = 64, 76
BAYER4 = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0


def light_for(c: dict) -> Light:
    return Light(rim_col=c.get("rim", (255, 200, 140)))


def portrait_bg(w, h, cols, seed=0) -> np.ndarray:
    """Dark vignette with a glow behind the head, dithered into a few steps, plus drifting motes."""
    dark, mid, hot = (hexc(c) for c in cols)
    ys, xs = np.mgrid[0:h, 0:w]
    cx, cy = w * 0.58, h * 0.38
    d = np.sqrt(((xs - cx) / w) ** 2 + ((ys - cy) / h) ** 2)
    t = np.clip(1 - d * 1.7, 0, 1) ** 1.6
    b = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    steps = 6
    q = np.floor(t * steps + (b - 0.5) * 0.9) / steps
    q = np.clip(q, 0, 1)[..., None]
    col = np.where(q < 0.5, dark + (mid - dark) * (q * 2), mid + (hot - mid) * ((q - 0.5) * 2) * 0.55)
    rng = np.random.default_rng(seed)
    for _ in range(18):
        x, y = rng.integers(0, w), rng.integers(0, h)
        r = rng.choice([0, 0, 1])
        col[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = hot * 0.7 + mid * 0.3
    return col.astype(np.float32)


def composite(bg: np.ndarray, fg: np.ndarray) -> np.ndarray:
    a = fg[..., 3:4] / 255.0
    out = bg * (1 - a) + fg[..., :3] * a
    return np.clip(out + 0.5, 0, 255).astype(np.uint8)


def frame_border(img: np.ndarray, col) -> np.ndarray:
    img = img.copy()
    img[0, :] = img[-1, :] = img[:, 0] = img[:, -1] = INK
    img[1, 1:-1] = img[-2, 1:-1] = col
    img[1:-1, 1] = img[1:-1, -2] = col
    return img


def render_char(prims, mats, cam, light):
    """Render solid parts, then translucent ones (layer >= 100) on top with a 50% ordered dither."""
    solid = [p for p in prims if p.layer < 100]
    ghost = [p for p in prims if p.layer >= 100]
    r = render(solid, mats, cam, light)
    if not ghost:
        return r
    g = render(ghost, mats, cam, light, outline=False)
    h, w = r.alpha.shape
    b = np.tile(BAYER4, (h // 4 + 1, w // 4 + 1))[:h, :w]
    over = (g.alpha > 0) & ((b < 0.25) | (r.alpha == 0) & (b < 0.6))
    edge = (g.alpha > 0) & ~np.roll(g.alpha > 0, 1, 0)
    over |= edge
    r.rgb[over] = g.rgb[over]
    r.alpha[over] = 255
    r.nrm[over] = g.nrm[over]
    r.glow[g.glow[..., 3] > 0] = g.glow[g.glow[..., 3] > 0]
    return r


def make_portrait(cid: str, folder: str) -> np.ndarray:
    c = CAST[cid]
    pf = c["portrait"]
    pose = Pose(**c.get("portrait_pose", dict(arm_n=(0.05, 0.18, 0.25), arm_f=(-0.05, 0.18, 0.25))))
    spec = dict(c["spec"], **c.get("portrait_spec", {}))
    if not c.get("portrait_weapon"):
        spec.pop("weapon", None)
    prims = build(spec, body_of(cid), pose)
    cam = Camera(96, 96, pf["center"], pf["scale"], yaw=pf["yaw"], pitch=pf["pitch"])
    r = render_char(prims, c["mats"], cam, light_for(c))
    fg = to_rgba(r)
    Image.fromarray(fg).save(os.path.join(folder, "portrait_clear.png"))
    bg = portrait_bg(96, 96, pf["bg"], seed=len(cid))
    img = composite(bg, fg)
    img = frame_border(img, hexc(pf["bg"][1]) * 0.6 + hexc("c8a070") * 0.4)
    Image.fromarray(img).save(os.path.join(folder, "portrait.png"))
    return img


def make_sprites(cid: str, folder: str) -> dict[str, list[np.ndarray]]:
    c = CAST[cid]
    body = body_of(cid, head_scale=c.get("sprite_head", 1.5))
    body.bulk *= c.get("sprite_bulk", 1.3)
    body.shoulder *= 1.12
    body.hip_w *= 1.15
    scale = c.get("sprite_scale", 34.0) * 1.85 / body.height if c.get("sprite_fit") else c.get("sprite_scale", 34.0)
    fw, fh = c.get("frame", (SPRITE_W, SPRITE_H))
    cam = Camera(fw, fh, (0.0, c.get("frame_cy", 0.98 * body.height / 1.85), 0.0), scale, yaw=-0.75, pitch=0.35)
    out = {}
    for name, (fn, n) in ANIMS.items():
        frames = []
        for i in range(n):
            pose = fn(i, n)
            for k, val in c.get("pose_override", {}).items():
                if name == "death" and k in ("leg_n", "leg_f"):
                    continue
                setattr(pose, k, val + getattr(pose, k) if k in ("bob", "lean") else val)
            r = render_char(build(c["spec"], body, pose), c["mats"], cam, light_for(c))
            rgba = to_rgba(r)
            Image.fromarray(rgba).save(os.path.join(folder, f"{name}_{i}.png"))
            Image.fromarray(normals_rgba(r)).save(os.path.join(folder, f"{name}_{i}_n.png"))
            if r.glow[..., 3].any():
                Image.fromarray(r.glow).save(os.path.join(folder, f"{name}_{i}_glow.png"))
            frames.append(rgba)
        out[name] = frames
    return out


def make_sheet(frames: dict[str, list[np.ndarray]], folder: str, bg=(58, 76, 52)) -> np.ndarray:
    cols = max(len(v) for v in frames.values())
    fh, fw = next(iter(frames.values()))[0].shape[:2]
    sheet = np.zeros((fh * len(frames), fw * cols, 4), np.uint8)
    for j, (_, row) in enumerate(frames.items()):
        for i, f in enumerate(row):
            sheet[j * fh:(j + 1) * fh, i * fw:(i + 1) * fw] = f
    Image.fromarray(sheet).save(os.path.join(folder, "sheet.png"))
    flat = np.zeros(sheet.shape[:2] + (3,), np.float32) + np.array(bg, np.float32)
    return composite(flat, sheet)


def make_gif(frames: dict[str, list[np.ndarray]], folder: str, zoom=4, bg=(58, 76, 52)) -> None:
    seq = []
    for name in ("idle", "walk", "attack", "cast", "hurt", "death"):
        reps = {"idle": 2, "walk": 2, "attack": 1, "cast": 1, "hurt": 2, "death": 1}[name]
        for _ in range(reps):
            seq += frames[name]
        if name == "death":
            seq += [frames[name][-1]] * 4
    imgs = []
    for f in seq:
        flat = np.zeros(f.shape[:2] + (3,), np.float32) + np.array(bg, np.float32)
        imgs.append(Image.fromarray(composite(flat, f)).resize((f.shape[1] * zoom, f.shape[0] * zoom), Image.NEAREST))
    imgs[0].save(os.path.join(folder, "preview.gif"), save_all=True, append_images=imgs[1:], duration=130, loop=0)


def make_card(cid: str, portrait: np.ndarray, sheet: np.ndarray, folder: str) -> None:
    zoom = 3
    p = np.kron(portrait, np.ones((zoom, zoom, 1), np.uint8))
    s = np.kron(sheet, np.ones((2, 2, 1), np.uint8))
    h = max(p.shape[0], s.shape[0]) + 16
    w = p.shape[1] + s.shape[1] + 24
    card = np.zeros((h, w, 3), np.uint8) + np.array([24, 22, 30], np.uint8)
    card[8:8 + p.shape[0], 8:8 + p.shape[1]] = p
    card[8:8 + s.shape[0], 16 + p.shape[1]:16 + p.shape[1] + s.shape[1]] = s
    Image.fromarray(card).save(os.path.join(folder, "card.png"))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("ids", nargs="*")
    ap.add_argument("--preview", default="")
    ap.add_argument("--portrait-only", action="store_true")
    args = ap.parse_args()
    ids = args.ids or list(CAST)
    for cid in ids:
        folder = os.path.join(OUT, cid)
        os.makedirs(folder, exist_ok=True)
        portrait = make_portrait(cid, folder)
        if not args.portrait_only:
            frames = make_sprites(cid, folder)
            sheet = make_sheet(frames, folder)
            make_gif(frames, folder)
            make_card(cid, portrait, sheet, folder)
        if args.preview:
            dst = os.path.join(args.preview, cid)
            os.makedirs(dst, exist_ok=True)
            for fn in ("portrait.png", "card.png", "preview.gif", "sheet.png"):
                if os.path.exists(os.path.join(folder, fn)):
                    shutil.copy(os.path.join(folder, fn), dst)
        print("rendered", cid)


if __name__ == "__main__":
    main()
