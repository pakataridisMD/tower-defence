"""Hero look test: three views of one hero (front, three-quarter, walking) in a simple studio light.
blender -b -P cinema/blender/tests/hero_turnaround.py -- OUT_DIR --hero tamsin [--frames 1 1]"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C, hero

name = C.opt("--hero", "tamsin")
C.setup(2.0)
C.box("floor", (0, 0, -0.05), (30, 30, 0.1), C.M("ground"))
C.world(density=0.0, sky=0.4)
C.light("AREA", (-3, -4, 5), (50, 0, -35), 900, (1.0, 0.92, 0.85), 3, "key")
C.light("AREA", (4, -2, 3), (60, 0, 60), 250, (0.7, 0.8, 1.0), 3, "fill")
C.light("AREA", (0, 4, 4), (-50, 0, 0), 700, (0.8, 0.85, 1.0), 2, "rim")
a = hero.build(name, (-1.6, 0, 0), math.pi, "Idle")      # facing the camera (+Y? camera at -Y)
b = hero.build(name, (0, 0, 0), math.pi - 0.7, "Idle")
c = hero.build(name, (1.6, 0, 0), math.pi - 1.4, "Walking_A", 0.3)
for r in (a, b, c):
    r.rotation_euler.z += math.pi  # stand-ins face -Y; turn them to face the camera at -Y
cam = C.camera(50)
if C.opt("--close", None):
    cam.data.lens = 85
    C.key_cam(cam, [(0, (0.9, -6.5, 1.75), (86, 0, 8))])
else:
    C.key_cam(cam, [(0, (0, -8.5, 1.3), (88, 0, 0))])
C.render(default_res=50, default_samples=32)
