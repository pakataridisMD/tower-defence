"""MakeHuman body test: a morphed, T-posed body in studio light. blender -b -P tests/mh_body.py -- OUT --frames 1 1"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, cine3d as C, mh
C.setup(1.0)
C.box("floor", (0, 0, -0.05), (30, 30, 0.1), C.M("ground"))
C.world(density=0.0, sky=0.4)
C.light("AREA", (-3, -4, 5), (50, 0, -35), 900, (1.0, 0.92, 0.85), 3, "key")
C.light("AREA", (4, -2, 3), (60, 0, 60), 250, (0.7, 0.8, 1.0), 3, "fill")
C.light("AREA", (0, 4, 4), (-50, 0, 0), 700, (0.8, 0.85, 1.0), 2, "rim")
b, ex, J = mh.body(gender=0.0, muscle=0.85, weight=0.4, tall=0.3)
b.data.materials.append(C.mat("skin", (0.8, 0.55, 0.42), 0.5))
for e in ex: e.data.materials.append(C.mat("eye", (0.9, 0.9, 0.9), 0.1))
print("JOINTS", {k: tuple(round(x, 3) for x in J[k]) for k in ("l-shoulder", "l-elbow", "l-hand", "neck", "head", "pelvis", "l-knee", "l-ankle")})
cam = C.camera(50)
C.key_cam(cam, [(0, (0, -6.5, 1.15), (88, 0, 0))])
C.render(default_res=40, default_samples=16)
