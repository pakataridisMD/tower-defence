"""0:00 The Rift from above: a chasm miles deep, the Black Gate shut at the bottom. (VO prologue 03 starts)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C

C.setup(7.0, seed=11)
C.canyon(y0=120, y1=-110, gate_y=-95, walls_h=260, depth=0)
gate = C.Gate(-95); gate.open_to(1, 0.0)
C.world(density=0.0025, sky=0.25)   # a little more air between the camera and the gate
C.moon(9.0, rot=(28, -35, 120))
C.light("AREA", (25, -25, 200), (-45, 0, -10), 400000, (0.55, 0.62, 0.85), 80, "wash")
for k in range(5):
    for side in (-1, 1):
        C.brazier(side * (7.5 + k * 0.6), 40 - k * 28)
cam = C.camera(24)
# Very high above the canyon, pitched steeply down so the floor, the braziers and the far-off gate all show;
# sinks into the chasm and tilts up towards the gate.
C.key_cam(cam, [(0, (0, 110, 240), (42, 0, 180)), (7, (0, 45, 40), (90, 0, 180))])
C.render()
