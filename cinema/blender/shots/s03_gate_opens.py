"""0:14 Somebody unlocked the Black Gate: the doors grind apart, grey light and grey eyes in the gap. (VO 07)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C

C.setup(10.5, seed=13)
C.canyon(y0=30, y1=-110, gate_y=-95)
gate = C.Gate(-95)
gate.open_to(C.sec(0), 0.0); gate.open_to(C.sec(1.5), 0.0); gate.open_to(C.sec(9.0), 7.0)
C.world(density=0.010, sky=0.04)
C.moon(3.5, rot=(40, -25, 150))
C.light("AREA", (25, -25, 150), (-45, 0, -10), 500000, (0.55, 0.62, 0.85), 60, "wash")
# Grey shapes pressing out of the dark behind the door.
for i in range(16):
    kind = random.choice(["Skeleton_Minion", "Skeleton_Warrior", "Skeleton_Minion", "Skeleton_Rogue"])
    # Stand-ins face -Y by default; turned by pi they face the camera and walk out towards it.
    rig = C.char(C.SK + kind + ".glb", (random.uniform(-2.6, 2.6), -100 - i * 1.6, 0), math.pi, "Walking_D_Skeletons", random.random(), scale=1.15)
    C.grey_eyes(rig)
    C.march(rig, 0.6, sign=1)
dust = C.light("POINT", (0, -92, 2), (0, 0, 0), 0, (0.8, 0.82, 0.9), 3, "dust")
cam = C.camera(32, fstop=5.6, focus=60)
C.key_cam(cam, [(0, (3, 2, 3.0), (95, 0, 179)), (10.5, (1.5, -14, 2.5), (96, 0, 180))])
C.shake(cam, 0.004, 6)
C.render()
