"""A set with people in it: -- OUT --set ember --frames N N --cam wide|close"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, cine3d as C, hero, cast, wardens, heralds, sets
name = C.opt("--set", "ember"); camk = C.opt("--cam", "wide")
C.setup(2.0)
S = getattr(sets, name)()
m = S["marks"].get("hero", S["marks"].get("east_wall"))
cast_list = {"ember": [("ignar", (0.8, 2.2, 0), math.radians(200), "Idle"), ("brannoc", (-1.2, -0.6, 0), math.radians(-20), "Cheer"),
                       ("tamsin", (-2.6, 0.4, 0), math.radians(-35), "Idle")],
             "solenne": [("ysolde", (0, 0.3, 0), math.radians(-10), "Idle"), ("tamsin", (-1.2, 0.6, 0), math.radians(-20), "Idle")]}.get(name)
if cast_list is None:
    local = {"earth": "gorrim", "storm": "kaela", "nature": "sylvaine", "water": "mirelle", "void": "corvin"}.get(name, "brannoc")
    cast_list = [("tamsin", (-0.9, 0.3, 0), math.radians(-25), "Idle"), (local, (0.9, 0.6, 0), math.radians(-5), "Idle")]
if name == "solenne":
    m = S["marks"]["east_wall"]
for who, loc, rz, act in cast_list:
    hero.build_human(who, m + __import__("mathutils").Vector(loc), rz, act)
cam = C.camera(35 if camk in ("wide", "aerial") else 50, 4.0, 12 if camk == "wide" else 6)
C.key_cam(cam, S["cams"][camk])
C.render(default_res=40, default_samples=16)
