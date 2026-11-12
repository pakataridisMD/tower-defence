"""0:24 Oswin turns the light of all his towers on the Gate and drives it back to a cart's width. (VO 08)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C

C.setup(7.5, seed=14)
C.canyon(y0=40, y1=-110, gate_y=-95)
gate = C.Gate(-95)
gate.open_to(C.sec(0), 7.0); gate.open_to(C.sec(7.0), 2.6)
C.world(density=0.008, sky=0.04)
C.moon(3.0)
# Six towers in an arc on the road, each pouring its colour onto the door.
for i, col in enumerate(C.ELEMENTS):
    x = (i - 2.5) * 6.0
    y = -48 - abs(i - 2.5) * 3.0
    c = C.tower(x, y, col)
    C.beam(c.location, (x * 0.25, -92.5, 30 + (i % 3) * 8), col)
oswin = C.char(C.KK + "Mage.glb", (0, -78, 0), 0.0, "Spellcasting", 0.0)
C.recolour(oswin, (0.8, 0.8, 0.82), 0.92)
C.lantern(oswin, pole=2.4, white=True, energy=600)
cam = C.camera(30)
# From behind the towers, rising slowly over them towards the door.
C.key_cam(cam, [(0, (6, -10, 6), (92, 0, 174)), (7.5, (4, -22, 12), (95, 0, 176))])
C.render()
