"""MakeHuman body on the KayKit rig: front Idle, three-quarter Idle, walking. -- OUT --frames N N"""
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import bpy, cine3d as C, mh, hero
C.setup(2.0)
C.box("floor", (0, 0, -0.05), (30, 30, 0.1), C.M("ground"))
C.world(density=0.0, sky=0.4)
C.light("AREA", (-3, -4, 5), (50, 0, -35), 900, (1.0, 0.92, 0.85), 3, "key")
C.light("AREA", (4, -2, 3), (60, 0, 60), 250, (0.7, 0.8, 1.0), 3, "fill")
C.light("AREA", (0, 4, 4), (-50, 0, 0), 700, (0.8, 0.85, 1.0), 2, "rim")
SK = C.mat("skin", (0.8, 0.55, 0.42), 0.5)
for x, rz, act, ph in ((-1.6, 0.0, "Idle", 0), (0, -0.7, "Idle", 0), (1.6, -1.4, C.opt("--act", "Walking_A"), 0.3)):
    rig = hero.base_rig()
    b, ex, J = mh.body(gender=0.0, muscle=0.85, weight=0.4, tall=0.3)
    b.data.materials.append(SK)
    hero.fit_mh(rig, J)
    hero.mh_weights(b, rig)
    for e in ex:
        e.data.materials.append(C.mat("eye", (0.9, 0.9, 0.9), 0.1)); hero.on_bone(e, rig, "head")
    rig.location = (x, 0, 0); rig.rotation_euler = (0, 0, rz)
    C.play(rig, act, ph)
    hero.relax_arms(rig, posture=hero.HUMAN_POSTURE)
cam = C.camera(50)
C.key_cam(cam, [(0, (0, -8.5, 1.2), (88, 0, 0))])
C.render(default_res=40, default_samples=16)
