"""Vholt riding his thunderbird. -- OUT --frames N N"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, cine3d as C, hero, cast, wardens, heralds
C.setup(2.0)
g = C.box("ground", (0, 0, -0.05), (80, 80, 0.1), C.M("mud"))
C.world(density=0.015, sky=0.1, colour=(0.02, 0.025, 0.05))
C.light("AREA", (4, 8, 9), (-45, 0, 160), 2500, (0.55, 0.68, 1.0), 5, "rim")
C.light("AREA", (-7, -6, 6), (65, 0, -50), 600, (0.4, 0.5, 0.8), 5, "fill")
root, saddle = heralds.thunderbird(loc=(0, 0, 3.4))
rig = hero.build_human("vholt", (0, 0, 0), 0.0, "Sit_Chair_Idle")
heralds.mount(rig, saddle)
root.rotation_euler.z = math.radians(-30)
cam = C.camera(35, 4.0, 11)
C.key_cam(cam, [(0, (6.5, -10.5, 7.5), (68, 0, 32))])
C.render(default_res=40, default_samples=16)
