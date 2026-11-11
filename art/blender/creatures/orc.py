CAMERA = dict(center=(0.1, 0, 1.0), ortho=2.6, azim=-74, elev=16)


def build(k):
    skin_m = k.mat("oskin", "6a9a3e", 0.7)
    dark_skin = k.mat("oskin2", "4a6e2c", 0.7)
    hide = k.mat("hide", "6a4a2c", 0.9)
    iron = k.mat("iron", "7a7a84", 0.65, 0.15)
    bone = k.mat("bone", "e8e0c8", 0.6)
    dark = k.mat("dark", "1a1410", 0.5)
    red = k.mat("eye", "ff4020", 0.4, emit=3.0)
    wood = k.mat("wood", "4a3220", 0.9)
    # hunched, huge shoulders and arms, small legs, jutting jaw
    k.skin("legs", [(0, 0, 0.7, 0.2, 0.26), (-0.1, 0.2, 0.4, 0.13), (-0.16, 0.21, 0.12, 0.12), (0.02, 0.21, 0.06, 0.11),
                    (0.12, -0.2, 0.4, 0.13), (0.16, -0.21, 0.12, 0.12), (0.34, -0.21, 0.06, 0.11)],
           [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6)], dark_skin)
    k.skin("torso", [(0, 0, 0.72, 0.22, 0.27), (0.1, 0, 1.05, 0.28, 0.36), (0.2, 0, 1.3, 0.26, 0.4)], [(0, 1), (1, 2)], skin_m)
    k.prim("cyl", "loin", hide, (0.02, 0, 0.66), (0.56, 0.68, 0.3), taper=1.15)
    k.prim("cyl", "belt", iron, (0.02, 0, 0.8), (0.56, 0.68, 0.07))
    k.prim("sphere", "skull_buckle", bone, (0.3, 0, 0.8), (0.14, 0.14, 0.16))
    # arms: long, thick, knuckles near the knees
    k.skin("arm_f", [(0.2, 0.42, 1.34, 0.17), (0.3, 0.52, 1.0, 0.14), (0.5, 0.46, 0.72, 0.15)], [(0, 1), (1, 2)], skin_m)
    k.skin("arm_n", [(0.2, -0.42, 1.34, 0.17), (0.34, -0.54, 1.02, 0.14), (0.58, -0.5, 0.9, 0.15)], [(0, 1), (1, 2)], skin_m)
    k.prim("sphere", "fist_n", dark_skin, (0.62, -0.5, 0.9), (0.26, 0.26, 0.26))
    k.prim("sphere", "pauldron", iron, (0.18, -0.44, 1.42), (0.42, 0.42, 0.32))
    for i in range(3):
        k.prim("cone", "spike", bone, (0.1 + i * 0.1, -0.5, 1.6 - abs(i - 1) * 0.04), (0.09, 0.09, 0.24), rot=(-20, (i - 1) * 20, 0))
    k.prim("cube", "strap", hide, (0.22, 0, 1.12), (0.5, 0.82, 0.1), rot=(35, 0, 0), bevel=0.02)
    # head: low, forward, heavy jaw with tusks
    k.prim("sphere", "head", skin_m, (0.42, 0, 1.52), (0.5, 0.5, 0.46))
    k.prim("sphere", "jaw", dark_skin, (0.52, 0, 1.4), (0.42, 0.46, 0.28))
    k.prim("sphere", "brow", dark_skin, (0.58, 0, 1.62), (0.26, 0.44, 0.12))
    for y in (0.13, -0.13):
        k.prim("sphere", "eye", red, (0.67, y, 1.56), (0.07, 0.09, 0.07))
        k.prim("cone", "tusk", bone, (0.68, y * 1.25, 1.46), (0.07, 0.07, 0.2), rot=(0, 10, 0))
        k.prim("cone", "ear", skin_m, (0.34, y * 2.1, 1.6), (0.12, 0.08, 0.3), rot=(y * 500, -20, 0))
    k.prim("sphere", "nose", dark_skin, (0.69, 0, 1.52), (0.1, 0.14, 0.08))
    k.prim("cube", "mohawk", dark, (0.3, 0, 1.78), (0.4, 0.07, 0.14), rot=(0, 10, 0), bevel=0.03)
    # big cleaver-axe held forward in the near fist
    k.prim("cyl", "haft", wood, (0.5, -0.52, 1.25), (0.07, 0.07, 1.3), rot=(0, -22, 0))
    k.prim("cube", "axe", iron, (0.08, -0.52, 1.86), (0.5, 0.05, 0.44), rot=(0, -22, 0), bevel=0.03)
    k.prim("cube", "axe_edge", bone, (-0.16, -0.52, 1.76), (0.1, 0.03, 0.5), rot=(0, -22, 0), bevel=0.01)
