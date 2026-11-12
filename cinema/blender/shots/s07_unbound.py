"""0:50 Out through the gap and up the Rift road: the Unbound, grey-eyed, with their Herald at the head. (VO 10)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C, hero

C.setup(8.0, seed=17)
C.canyon(y0=30, y1=-110, gate_y=-95)
gate = C.Gate(-95); gate.open_to(C.sec(0), 2.6)
C.world(density=0.006, sky=0.05)
C.moon(4.0)
C.light("AREA", (6, -30, 30), (-55, 0, 170), 60000, (0.55, 0.62, 0.85), 20, "wash")
C.light("AREA", (0, -52, 18), (-75, 0, 180), 15000, (0.7, 0.72, 0.8), 10, "rim")
herald = hero.build_human("vesper", (0, -62, 0), math.pi, "Walking_B", 0.0)
C.march(herald, 1.0, sign=1)
for i in range(46):
    row, col = divmod(i, 2)
    kind = random.choice(["Skeleton_Minion", "Skeleton_Minion", "Skeleton_Warrior", "Skeleton_Rogue", "Skeleton_Mage"])
    rig = C.char(C.SK + kind + ".glb", ((col - 0.5) * 1.6 + random.uniform(-0.3, 0.3), -66 - row * 2.2, 0), math.pi,
                 "Walking_D_Skeletons", random.random(), scale=1.1)
    C.grey_eyes(rig); C.march(rig, 1.0, sign=1)
cam = C.camera(50, fstop=4.0, focus=herald)
# Low on the road ahead of them, backing away as they come on.
C.key_cam(cam, [(0, (1.6, -50, 1.0), (93, 0, 173)), (8, (1.2, -46.5, 0.9), (94, 0, 175))])   # low and close: she fills the frame as she comes on
C.shake(cam, 0.003, 4)
C.render()
