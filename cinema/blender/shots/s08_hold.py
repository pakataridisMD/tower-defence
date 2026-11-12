"""0:58 Our answer: the lanterns of the army winding down the Rift road to the Gate. (VO 12: "Hold the road.")"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C, hero

C.setup(8.0, seed=7)
C.canyon(y0=40, y1=-110, gate_y=-95)
gate = C.Gate(-95); gate.open_to(C.sec(0), 2.6)
C.world(density=0.008, sky=0.05)
C.moon(4.0)
C.light("AREA", (25, -25, 150), (-45, 0, -10), 250000, (0.55, 0.62, 0.85), 60, "wash")
C.light("SPOT", (0, -115, 25), (-95, 0, 0), 1.2e7, (0.75, 0.78, 0.88), 1, "beam")
for k in range(6):
    for side in (-1, 1):
        C.brazier(side * (7.5 + k * 0.6), 8 - k * 17 + (4 if side > 0 else 0))
for i in range(34):
    kind = random.choice(["Knight", "Barbarian", "Knight", "Rogue_Hooded"])
    x = random.uniform(-0.6, 0.6) + (1.1 if i % 2 else -1.1)
    rig = C.char(C.KK + kind + ".glb", (x, 6 - i * 3.4 + random.uniform(-1, 1), 0), 0.0, "Walking_A", random.random())
    C.lantern(rig); C.march(rig, 2.2)
tamsin = hero.build_human("tamsin", (-2.6, 15.0, 0), math.pi - 0.5, "Idle")
cam = C.camera(24)
C.key_cam(cam, [(0, (3.0, 30.0, 16.0), (88, 0, 176)), (8, (2.5, 23.0, 12.5), (90, 0, 177))])
C.render()
