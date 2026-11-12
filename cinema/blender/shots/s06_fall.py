"""0:40 The ground gives way and Oswin falls through. His lantern is still lit. (VO 09)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C, hero

C.setup(10.0, seed=16)
gate = C.Gate(-95); gate.open_to(C.sec(0), 2.6)
gate.slit.hide_render = True; gate.light.hide_render = True
# A shaft of rock under the gap, falling away into black.
for k in range(8):
    for side in (-1, 1):
        c = C.box("shaft", (side * 9, -96, -20 - k * 40), (8, 26, 42), C.M("rock"))
        c.rotation_euler.z = random.uniform(-0.2, 0.2); C.rough_up(c, 3.0, 6.0, 5)
    for side in (-1, 1):
        c = C.box("shaft", (0, -96 + side * 12, -20 - k * 40), (26, 6, 42), C.M("rock"))
        C.rough_up(c, 3.0, 6.0, 5)
C.world(density=0.012, sky=0.0, colour=(0.0, 0.0, 0.0))
oswin = hero.build_human("oswin", (0, -96, 0), 0.0, "Jump_Idle")
hero.lamp(oswin, 900)
# He drops away from the camera, slowly tumbling, until only the white point of the lantern is left.
oswin.keyframe_insert("location", index=2, frame=C.sec(0))
oswin.location.z = -3; oswin.keyframe_insert("location", index=2, frame=C.sec(2.0))
oswin.location.z = -260; oswin.keyframe_insert("location", index=2, frame=C.sec(10))
oswin.rotation_euler.x = 0; oswin.keyframe_insert("rotation_euler", index=0, frame=C.sec(1.5))
oswin.rotation_euler.x = math.radians(-160); oswin.keyframe_insert("rotation_euler", index=0, frame=C.sec(10))
cam = C.camera(35)
C.key_cam(cam, [(0, (0, -96, 14), (0, 0, 0)), (10, (0, -96, 9), (0, 0, 8))])
C.render()
