"""Hero beauty shots in story light: dusk, cold rim from behind, the lantern's warm key.
-- OUT --hero tamsin --shot close|full --frames N N"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, cine3d as C, hero
name = C.opt("--hero", "tamsin"); shot = C.opt("--shot", "close")
C.setup(2.0)
g = C.box("ground", (0, 0, -0.05), (60, 60, 0.1), C.M("mud"))
for i, (x, y, s) in enumerate(((-2.5, 3, 1.4), (2.8, 5, 2.2), (-5, 9, 3.0), (6, 12, 3.5))):
    C.box("rock%d" % i, (x, y, s / 2), (s, s * 0.8, s), C.M("rock"))
C.world(density=0.02, sky=0.08, colour=(0.02, 0.025, 0.05))
C.light("AREA", (1.5, 3.5, 3.2), (-45, 0, 160), 900, (0.55, 0.68, 1.0), 2.5, "rim")
C.light("AREA", (-3.5, -2.5, 2.2), (70, 0, -55), 120, (0.4, 0.5, 0.8), 3, "fill")
C.light("AREA", (2.5, -2.0, 2.0), (70, 0, 50), 260, (1.0, 0.62, 0.35), 1.0, "warm_key")
rig = hero.build_human(name, (0, 0, 0), -0.35, "Idle")
if shot == "close":
    cam = C.camera(70, 2.8, 2.6)
    C.key_cam(cam, [(0, (0.9, -2.5, 1.85), (90, 0, 20))])
else:
    cam = C.camera(32, 4.0, 3.6)
    C.key_cam(cam, [(0, (1.2, -3.4, 0.55), (96, 0, 19))])
C.render(default_res=60, default_samples=48)
