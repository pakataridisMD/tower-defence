import math
CAMERA = dict(center=(0.2, 0, 1.3), ortho=5.2, azim=-70, elev=16, size=384)


def build(k):
    scale_m = k.mat("scale", "a02a22", 0.6, noise=0.5, noise_scale=26)
    belly = k.mat("belly", "e0b060", 0.7)
    wing_m = k.mat("wing", "7a1e22", 0.8)
    horn = k.mat("horn", "e8dcc0", 0.5)
    dark = k.mat("dark", "2a1418", 0.7)
    eye = k.mat("eye", "ffd040", 0.3, emit=5.0)
    fire = k.mat("fire", "ffa030", 0.3, emit=9.0)
    # body: one long skinned spine from tail tip to snout, S-curved neck
    spine = [(-2.0, 0, 0.5, 0.05), (-1.6, 0, 0.42, 0.11), (-1.15, 0, 0.5, 0.2), (-0.7, 0, 0.72, 0.34), (-0.2, 0, 0.95, 0.46, 0.5),
             (0.3, 0, 1.05, 0.44, 0.48), (0.65, 0, 1.4, 0.28), (0.7, 0, 1.85, 0.21), (0.95, 0, 2.2, 0.2), (1.3, 0, 2.3, 0.25, 0.24),
             (1.72, 0, 2.2, 0.15, 0.17)]
    k.skin("body", spine, [(i, i + 1) for i in range(len(spine) - 1)], scale_m)
    # belly plates along the underside
    for i, (x, z, s) in enumerate(((-0.5, 0.52, 0.5), (-0.15, 0.56, 0.6), (0.2, 0.66, 0.6), (0.5, 0.98, 0.42), (0.52, 1.5, 0.32),
                                   (0.6, 1.85, 0.26))):
        k.prim("sphere", "belly", belly, (x + 0.12, 0, z), (s, s * 0.9, s * 0.75))
    # legs
    for y, dx in ((0.4, -0.08), (-0.4, 0.08)):
        k.skin("hind", [(-0.5 + dx, y * 0.8, 0.85, 0.24), (-0.72 + dx, y * 1.15, 0.42, 0.15), (-0.5 + dx, y * 1.2, 0.1, 0.12),
                        (-0.22 + dx, y * 1.2, 0.07, 0.1)], [(0, 1), (1, 2), (2, 3)], scale_m)
        k.skin("fore", [(0.35 + dx, y * 0.8, 1.0, 0.2), (0.52 + dx, y * 1.15, 0.5, 0.12), (0.5 + dx, y * 1.2, 0.1, 0.11),
                        (0.76 + dx, y * 1.2, 0.07, 0.1)], [(0, 1), (1, 2), (2, 3)], scale_m)
        for cx in (-0.14 + dx, 0.84 + dx):
            for j in (-1, 0, 1):
                k.prim("cone", "claw", horn, (cx + 0.06, y * 1.2 + j * 0.07, 0.05), (0.07, 0.07, 0.2), rot=(0, 80, j * 15))
    # head details: jaw, horns, eye, nostril flame
    k.prim("sphere", "jaw", scale_m, (1.56, 0, 2.08), (0.6, 0.3, 0.16), rot=(0, 14, 0))
    for y in (0.13, -0.13):
        k.prim("cone", "horn", horn, (1.0, y * 1.2, 2.56), (0.13, 0.13, 0.62), rot=(y * 110, -55, 0))
        k.prim("sphere", "eye", eye, (1.44, y * 1.25, 2.38), (0.1, 0.08, 0.09))
        k.prim("sphere", "brow", dark, (1.42, y * 1.25, 2.45), (0.2, 0.12, 0.07), rot=(0, 15, 0))
    for i in range(5):
        k.prim("cone", "tooth", horn, (1.5 + i * 0.07, -0.13, 2.14), (0.04, 0.04, 0.11), rot=(180, 0, 0))
    for i in range(9):  # back spikes from head to tail
        t = i / 8
        x = 1.0 - 2.6 * t
        z = [2.5, 2.1, 1.75, 1.52, 1.45, 1.3, 1.0, 0.72, 0.6][i]
        k.prim("cone", "spike", horn, (x, 0, z), (0.12, 0.08, 0.26 + 0.1 * math.sin(t * 3.1)), rot=(0, -25, 0))
    k.prim("cone", "tail_tip", horn, (-2.12, 0, 0.55), (0.3, 0.06, 0.42), rot=(0, -100, 0))
    # wings: an arm bone with three fingers and a membrane fan, both raised
    for y, tilt in ((1, 1.0), (-1, 1.0)):
        root = (0.1, 0.3 * y, 1.4)
        elbow = (-0.3, 0.9 * y, 2.5)
        wrist = (0.2, 1.6 * y, 3.1)
        tips = [(-1.6, 2.3 * y, 2.3), (-1.2, 2.5 * y, 3.0), (-0.3, 2.7 * y, 3.6)]
        pts = [root + (0.12,), elbow + (0.09,), wrist + (0.07,)] + [t + (0.035,) for t in tips]
        k.skin("wingbone", pts, [(0, 1), (1, 2), (2, 3), (2, 4), (2, 5)], scale_m, sub=1)
        import bpy
        me = bpy.data.meshes.new("membrane")
        verts = [root, elbow, wrist] + tips + [(-0.9, 0.4 * y, 1.5)]
        faces = [(0, 1, 6), (1, 3, 6), (1, 2, 3), (2, 4, 3), (2, 5, 4)]
        me.from_pydata(verts, [], faces)
        ob = bpy.data.objects.new("membrane", me)
        bpy.context.scene.collection.objects.link(ob)
        ob.data.materials.append(wing_m)
        sol = ob.modifiers.new("s", "SOLIDIFY")
        sol.thickness = 0.03
    # a lick of flame from the mouth
    k.prim("cone", "flame", fire, (2.1, 0, 2.08), (0.3, 0.26, 0.7), rot=(0, 100, 0))
    k.prim("sphere", "flame2", fire, (1.9, 0, 2.1), (0.22, 0.2, 0.2))
