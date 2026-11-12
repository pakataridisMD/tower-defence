"""Render one shot of a story cinematic from its spec in story/<land>.py.

    blender -b -P film.py -- OUT --film ember_warden --shot 2 [--frames A B] [--step N] [--res R] [--samples S] [--gpu] [--eevee] [--mid]

A spec is a dict (see story/ember.py):
    set:   name of a builder in sets.py (+ "set_args")
    cast:  [(hero name, (x, y, z) from the set's mark, facing in degrees, action, {phase, soft, at, walk: (speed, axis), as})]
    cam:   [(seconds, (x, y, z), (rx, ry, rz))] camera keys, positions relative to the mark; or a set camera name
    lens, fstop, focus (a cast name)
    extra: optional function(S, rigs) for anything special (a bursting column, a flare, falling ash...)
    key:   a soft fill light riding with the camera (energy, or (energy, rgb)), for night close-ups
    norm:  camera key times are fractions of the shot (0..1) instead of seconds
    reuse / montage: the shot is cut from other renders (a trailer shot, or a list of other films' shots)
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
    """A land's films live in story/<land>.py; the main story (prologue, Solenne, the assault...) in story/main.py."""
    land = film.split("_")[0]
    mod = importlib.import_module("story." + (land if land in LAND else "main"))
    return mod.SHOTS[film][n - 1]


def length(film, n, sp):
    if "seconds" in sp:
        return sp["seconds"]
    line = VOICE.get(film, {}).get("%02d" % n)
    return (line["duration"] if line else 6.0) + sp.get("pad", 0.4)


def build(film, n):
    sp = spec_for(film, n)
    if "reuse" in sp or "montage" in sp:   # made from other renders (trailer shots, other films): nothing to build
        raise SystemExit("%s %d reuses %s" % (film, n, sp.get("reuse") or sp.get("montage")))
    secs = length(film, n, sp)
    C.setup(secs, seed=sp.get("seed", 7))
    S = getattr(sets, sp["set"])(**sp.get("set_args", {}))
    mark = S["marks"][sp.get("mark", "hero")]
    rigs = {}
    for entry in sp.get("cast", []):
        who, pos, face, action = entry[:4]
        opt = entry[4] if len(entry) > 4 else {}
        rig = hero.build_human(who, mark + Vector(pos), math.radians(face), action, opt.get("phase", 0.0), opt.get("soft"))
        if "scale" in opt:   # a figure bigger than life (the Thunderhead as a storm-giant)
            rig.scale = [v * opt["scale"] for v in rig.scale]
        if "at" in opt:   # start the action `at` seconds in (it holds its first pose until then)
            for tr in rig.animation_data.nla_tracks:
                for st in tr.strips:
                    if st.action and st.action.name == action:
                        st.frame_start_ui = st.frame_start_ui + C.sec(opt["at"]) - 1
        if "walk" in opt:
            speed, axis = opt["walk"]
            C.march(rig, speed, axis=axis[0], sign=axis[1])
        rigs[opt.get("as", who)] = rig
    if "extra" in sp:
        sp["extra"](S, rigs)
    cam = C.camera(sp.get("lens", 35), sp.get("fstop"), rigs.get(sp.get("focus")))
    if isinstance(sp["cam"], str):   # a set's own camera: already in set coordinates
        C.key_cam(cam, S["cams"][sp["cam"]])
    else:                           # shot keys are relative to the mark; with "norm" their times run 0..1 over the shot
        k = secs if sp.get("norm") else 1.0
        C.key_cam(cam, [(t * k, tuple(mark + Vector(p)), r) for t, p, r in sp["cam"]])
    if sp.get("key"):   # a soft fill riding with the camera (night close-ups): energy, optional colour
        k = sp["key"] if isinstance(sp["key"], (tuple, list)) else (sp["key"], (1.0, 0.8, 0.6))
        L = C.light("AREA", (0, 0, 0), (0, 0, 0), k[0], k[1], 1.5, "camera_fill")
        L.parent = cam; L.location = (0.8, 0.9, 0.3)
    return sp


if __name__ == "__main__":
    film = C.opt("--film", "ember_warden"); n = int(C.opt("--shot", "1"))
    build(film, n)
    if "--mid" in C.argv:   # one frame from the middle of the shot (quick spec checks)
        m = (C.sc.frame_start + C.sc.frame_end) // 2
        C.argv += ["--frames", str(m), str(m)]
    C.render(default_res=67, default_samples=32)
