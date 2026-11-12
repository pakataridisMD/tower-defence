"""0:07 The shut Black Gate from the road, mountain-tall, dust drifting. (VO prologue 03 ends)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C

C.setup(7.0, seed=12)
C.canyon(y0=40, y1=-110, gate_y=-95)
gate = C.Gate(-95); gate.open_to(1, 0.0)
C.world(density=0.009, sky=0.05)
C.moon(4.5, rot=(40, -25, 150))
C.light("AREA", (25, -25, 150), (-45, 0, -10), 600000, (0.55, 0.62, 0.85), 60, "wash")
for k in range(4):
    for side in (-1, 1):
        C.brazier(side * (8 + k * 0.6), -5 - k * 20)
cam = C.camera(24)
# Low on the road, slow crane up: the door fills the frame.
C.key_cam(cam, [(0, (2, 30, 2.0), (96, 0, 179)), (7, (1, 18, 9.0), (100, 0, 180))])
C.render()
