"""Hero on a real body: front Idle, three-quarter Idle, walking; --close for a portrait. -- OUT --hero tamsin --frames N N"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, cine3d as C, hero
name = C.opt("--hero", "tamsin")
C.setup(2.0)
C.box("floor", (0, 0, -0.05), (30, 30, 0.1), C.M("ground"))
C.world(density=0.0, sky=0.4)
C.light("AREA", (-3, -4, 5), (50, 0, -35), 900, (1.0, 0.92, 0.85), 3, "key")
C.light("AREA", (4, -2, 3), (60, 0, 60), 250, (0.7, 0.8, 1.0), 3, "fill")
C.light("AREA", (0, 4, 4), (-50, 0, 0), 700, (0.8, 0.85, 1.0), 2, "rim")
hero.build_human(name, (-1.6, 0, 0), 0.0, "Idle")
hero.build_human(name, (0, 0, 0), -0.7, "Idle")
hero.build_human(name, (1.6, 0, 0), -1.4, C.opt("--act", "Walking_B"), 0.3)
cam = C.camera(50)
if C.opt("--close", None):
    cam.data.lens = 85
    C.key_cam(cam, [(0, (-1.45, -3.2, 1.9), (88, 0, -3))])
else:
    C.key_cam(cam, [(0, (0, -8.5, 1.2), (88, 0, 0))])
C.render(default_res=50, default_samples=24)
