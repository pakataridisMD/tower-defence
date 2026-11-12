"""Render one shot of a story cinematic from its spec in story/<land>.py.

    blender -b -P film.py -- OUT --film ember_warden --shot 2 [--frames A B] [--step N] [--res R] [--samples S] [--gpu]

A spec is a dict (see story/ember.py):
    set:   name of a builder in sets.py (+ "set_args")
    cast:  [(hero name, (x, y, z) from the set's mark, facing in degrees, action, {phase, soft, walk: (speed, axis)})]
    cam:   [(seconds, (x, y, z), (rx, ry, rz))] camera keys, positions relative to the mark; or a set camera name
    lens, fstop, focus (a cast name)
    extra: optional function(S, rigs) for anything special (a bursting column, a flare, falling ash...)
The shot lasts as long as its voice line (story/voice.json) plus `pad` seconds; "seconds" overrides that.
--step N renders every Nth frame only (animatic previews); the cut repeats frames to keep timing."""
import sys, os, json, math, importlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector
import cine3d as C, hero, cast, wardens, heralds, sets

HERE = os.path.dirname(os.path.abspath(__file__))
VOICE = json.load(open(os.path.join(HERE, "story", "voice.json")))
LAND = {"ember": "ember", "storm": "storm", "nature": "nature", "water": "water", "earth": "earth", "void": "void"}


def spec_for(film, n):
    mod = importlib.import_module("story." + film.split("_")[0])
    return mod.SHOTS[film][n - 1]


def length(film, n, sp):
    if "seconds" in sp:
        return sp["seconds"]
    line = VOICE.get(film, {}).get("%02d" % n)
    return (line["duration"] if line else 6.0) + sp.get("pad", 0.4)


def build(film, n):
    sp = spec_for(film, n)
    secs = length(film, n, sp)
    C.setup(secs, seed=sp.get("seed", 7))
    S = getattr(sets, sp["set"])(**sp.get("set_args", {}))
    mark = S["marks"][sp.get("mark", "hero")]
    rigs = {}
    for entry in sp.get("cast", []):
        who, pos, face, action = entry[:4]
        opt = entry[4] if len(entry) > 4 else {}
        rig = hero.build_human(who, mark + Vector(pos), math.radians(face), action, opt.get("phase", 0.0), opt.get("soft"))
        if "walk" in opt:
            speed, axis = opt["walk"]
            C.march(rig, speed, axis=axis[0], sign=axis[1])
        rigs[opt.get("as", who)] = rig
    if "extra" in sp:
        sp["extra"](S, rigs)
    cam = C.camera(sp.get("lens", 35), sp.get("fstop"), rigs.get(sp.get("focus")))
    if isinstance(sp["cam"], str):   # a set's own camera: already in set coordinates
        C.key_cam(cam, S["cams"][sp["cam"]])
    else:                           # shot keys are relative to the mark
        C.key_cam(cam, [(t, tuple(mark + Vector(p)), r) for t, p, r in sp["cam"]])
    return sp


if __name__ == "__main__":
    film = C.opt("--film", "ember_warden"); n = int(C.opt("--shot", "1"))
    build(film, n)
    C.render(default_res=67, default_samples=32)
