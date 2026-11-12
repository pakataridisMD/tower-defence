"""0:52 On the walls of Solenne at night: "I am Ysolde, Queen of Solenne. You are a Spirewright..." (VO 12 opens)"""
import sys, os, math, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import cine3d as C, hero

C.setup(7.0, seed=19)
WALL = C.M("white_stone")
C.box("walkway", (0, 0, -0.25), (60, 5, 0.5), WALL)
C.box("wall_face", (0, 2.2, -12), (60, 1.2, 24), WALL)
for i in range(-14, 15):                       # crenellations on the outer (east) side, towards the Rift
    C.box("merlon", (i * 2.0, -2.2, 0.75), (1.1, 0.6, 1.5), WALL)
C.box("parapet", (0, -2.2, 0.2), (60, 0.6, 0.4), WALL)
for x in (-9.0, -4.5, 5.5, 11.0):            # braziers along the parapet, clear of the camera
    C.brazier(x, -1.4, 0.0, energy=350)
# the city below and behind her: scattered warm windows
glow = C.M("lantern")
random.seed(3)
for _ in range(260):
    x, y = random.uniform(-80, 80), random.uniform(12, 140)
    bpy = __import__("bpy")
    bpy.ops.mesh.primitive_cube_add(size=0.35, location=(x, y, -18 + random.uniform(0, 14)))
    bpy.context.object.data.materials.append(glow)
C.world(density=0.012, sky=0.03)
C.moon(2.5, rot=(30, 0, 200))
C.light("AREA", (-2.2, 2.6, 2.6), (-60, 0, -140), 160, (1.0, 0.72, 0.45), 1.5, "brazier_key")
C.light("AREA", (2.2, -3.8, 3.5), (55, 0, 30), 600, (0.55, 0.65, 1.0), 2.5, "moon_rim")
queen = hero.build_human("ysolde", (0, -0.6, 0), math.pi + 0.15, "Idle")
cam = C.camera(60, fstop=2.2, focus=queen)
# From the walkway, slowly closing on her as she looks out over the city towards the camera.
C.key_cam(cam, [(0, (0.7, 3.6, 1.9), (88, 0, 172)), (7, (0.45, 2.7, 1.92), (87, 0, 174))])
C.render()
