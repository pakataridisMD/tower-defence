#!/usr/bin/env python3
"""Split pix2d cinematic stills into depth layers for the Godot cinematic kit.

The stills painter (tools/art/pix2d/stills.py) paints back to front on one canvas. Here every top-level painting call
is recorded as a snapshot; a shot's CUTS say after which calls a new depth layer starts. Layer k holds the pixels that
changed between cut k-1 and cut k (layer 0 is the whole canvas so far), so far layers keep their full picture behind
near ones and parallax never opens holes. The vignette is skipped: the kit grades in post.

usage: python3 cinema/tools/layer_stills.py --list prologue 7       # print the call list of one still
       python3 cinema/tools/layer_stills.py --out cinema/art/stills    # write every still in CUTS
Writes <out>/<cinematic>_<NN>/<k>.png (RGBA, 640x360) and layers.json with the cut names.
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "art", "pix2d"))
import stills  # noqa: E402
import shots_lands  # noqa: E402,F401
import shots_story  # noqa: E402,F401

# (cinematic, shot) -> [(end, name), ...] back to front. `end` is the last call of that layer: an index, or
# "after:<call>#n" / "before:<call>#n" (n-th call of that name, 1-based; -1 = the last one). Whatever is painted after
# the last cut becomes the "front" layer.
CUTS = {
    ("prologue", 1): [("after:particles#1", "map")],
    ("prologue", 2): [("after:stars#1", "sky"), ("after:bands#2", "ground"), ("before:poly#1", "monarchs")],
    ("prologue", 3): [("after:glow#1", "sky"), ("before:ridge#2", "far"), ("after:bands#2", "ground"), ("after:fog#1", "flames"),
                      ("before:particles#1", "army")],
    ("prologue", 4): [("after:stars#1", "sky"), ("after:put#1", "rift"), ("after:bands#2", "ground"), ("before:put#2", "city")],
    ("prologue", 5): [("before:ridge#1", "sky"), ("after:ridge#1", "ridge"), ("before:wall#1", "ruins"), (73, "city")],
    ("prologue", 7): [(42, "sky"), ("after:ridge#1", "ridge"), ("after:particles#1", "ground"), ("after:glow#-1", "crack")],
    ("prologue", 11): [("before:ridge#1", "sky"), ("after:ridge#1", "ridge"), ("after:bands#2", "ground"), ("before:put#1", "road"),
                       ("after:put#2", "people")],
    ("prologue", 12): [("before:ridge#1", "sky"), ("after:ridge#1", "far"), ("after:ridge#2", "near"), ("before:put#1", "wall")],
    ("night_of_falling_stars", 9): [("after:stars#1", "sky"), ("before:bands#2", "houses"), ("before:put#1", "street"),
                                    ("after:put#2", "people")],
}


def resolve(log, end):
    if isinstance(end, int):
        return end
    mode, rest = end.split(":")
    name, n = rest.split("#")
    idx = [i for i, (nm, _, _) in enumerate(log) if nm == name]
    i = idx[int(n) - 1] if int(n) > 0 else idx[int(n)]
    return i if mode == "after" else i - 1

LOG = []
_depth = [0]
_scene = [None]


def _wrap(name, fn):
    def w(self, *a, **k):
        _depth[0] += 1
        try:
            if name == "vignette" and _depth[0] == 1:
                return None
            return fn(self, *a, **k)
        finally:
            _depth[0] -= 1
            if _depth[0] == 0 and self is _scene[0]:
                LOG.append((name, _brief(a), self.c.copy()))
    return w


def _brief(a):
    out = []
    for v in a[:3]:
        if isinstance(v, (int, float, str)):
            out.append(str(v))
        elif isinstance(v, (tuple, list)) and len(v) <= 4:
            out.append(str(tuple(v)))
        else:
            out.append(type(v).__name__)
    return ", ".join(out)


for _n in ("bands", "blend", "solid_blend", "glow", "disc", "stars", "ridge", "poly", "rect", "line", "tower", "wall",
           "particles", "fog", "vignette", "put", "put_image"):
    setattr(stills.Scene, _n, _wrap(_n, getattr(stills.Scene, _n)))
_init = stills.Scene.__init__


def _init_wrap(self, *a, **k):
    _init(self, *a, **k)
    _scene[0] = self
    LOG.clear()


stills.Scene.__init__ = _init_wrap


def run(cid, n):
    fn = stills.CINEMATICS[cid][n - 1]
    sc = fn()
    return sc, list(LOG)


def to_img(arr, alpha=None):
    rgb = np.clip(arr, 0, 255).astype(np.uint8)
    if alpha is None:
        alpha = np.full(rgb.shape[:2], 255, np.uint8)
    im = Image.fromarray(np.dstack([rgb, alpha]), "RGBA")
    return im.resize((im.width * 2, im.height * 2), Image.NEAREST)


def split(cid, n, cuts, out):
    sc, log = run(cid, n)
    final = sc.c.copy()
    snaps = [s for (_, _, s) in log]
    bounds = [resolve(log, c) for c, _ in cuts]          # call index after which layer k ENDS (inclusive)
    names = [nm for _, nm in cuts] + ["front"]
    d = os.path.join(out, f"{cid}_{n:02d}")
    os.makedirs(d, exist_ok=True)
    prev = None
    ends = [snaps[b] for b in bounds] + [final]
    for k, cur in enumerate(ends):
        if prev is None:
            to_img(cur).save(os.path.join(d, f"{k}.png"))
        else:
            ch = np.any(np.abs(cur - prev) > 0.5, axis=2)
            to_img(cur, (ch * 255).astype(np.uint8)).save(os.path.join(d, f"{k}.png"))
        prev = cur
    json.dump({"layers": names}, open(os.path.join(d, "layers.json"), "w"))
    to_img(final).save(os.path.join(d, "flat.png"))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", nargs=2)
    ap.add_argument("--out", default=os.path.join(ROOT, "cinema", "art", "stills"))
    a = ap.parse_args()
    if a.list:
        _, log = run(a.list[0], int(a.list[1]))
        for i, (nm, args, _) in enumerate(log):
            print(i, nm, args)
        return
    for (cid, n), cuts in CUTS.items():
        print(split(cid, n, cuts, a.out))


if __name__ == "__main__":
    main()
