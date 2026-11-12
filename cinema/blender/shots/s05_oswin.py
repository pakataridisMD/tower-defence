"""0:32 Oswin at the foot of the Gate, lantern-staff raised, six colours of tower light washing over him. (VO 08 ends)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C

C.setup(8.0, seed=15)
C.canyon(y0=-20, y1=-110, gate_y=-95)
gate = C.Gate(-95); gate.open_to(C.sec(0), 3.4); gate.open_to(C.sec(8), 2.4)
C.world(density=0.010, sky=0.03)
C.moon(2.0)
oswin = C.char(C.KK + "Mage.glb", (0, -80, 0), 0.25, "Spellcast_Long", 0.0)
C.recolour(oswin, (0.8, 0.8, 0.82), 0.92)
C.lantern(oswin, pole=2.4, white=True, energy=800)
# The towers are off screen behind the camera: their colours fall on him from six directions.
for i, col in enumerate(C.ELEMENTS):
    a = math.radians(-60 + i * 24)
    C.light("SPOT", (math.sin(a) * 14, -80 + math.cos(a) * 18, 9), (60, 0, math.degrees(math.pi - a)), 7000, col, 0.4, "towerlight")
cam = C.camera(50, fstop=2.8, focus=oswin)
# Low angle, slowly circling him; the door and its slit loom behind.
C.key_cam(cam, [(0, (-4.5, -73, 0.8), (95, 0, 208)), (8, (3.5, -73.5, 0.7), (96, 0, 158))])
C.shake(cam, 0.003, 5)
C.render()
