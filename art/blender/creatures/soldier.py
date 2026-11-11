CAMERA = dict(center=(0.1, 0, 1.0), ortho=2.3, azim=-74, elev=16)


def build(k):
    skin_m = k.mat("skin", "d8a880", 0.6)
    cloth = k.mat("cloth", "2f4a9a", 0.9)
    steel = k.mat("steel", "c4c8d0", 0.65, 0.15)
    leather = k.mat("leather", "5a3a22", 0.8)
    gold = k.mat("gold", "e0b040", 0.3, 1.0)
    red = k.mat("red", "b02a22", 0.8)
    dark = k.mat("dark", "20202a", 0.5)
    # chunky proportions: big head, short legs. Faces +X; the camera sees the -Y side.
    k.skin("legs", [(0, 0, 0.78, 0.17, 0.2), (-0.08, 0.16, 0.42, 0.115), (-0.16, 0.17, 0.2, 0.105),
                    (0.1, -0.16, 0.42, 0.115), (0.16, -0.17, 0.2, 0.105)], [(0, 1), (1, 2), (0, 3), (3, 4)], cloth)
    k.skin("boot_f", [(-0.16, 0.17, 0.22, 0.12), (-0.17, 0.17, 0.07, 0.12), (0.0, 0.17, 0.055, 0.1)], [(0, 1), (1, 2)], leather)
    k.skin("boot_n", [(0.16, -0.17, 0.22, 0.12), (0.17, -0.17, 0.07, 0.12), (0.34, -0.17, 0.055, 0.1)], [(0, 1), (1, 2)], leather)
    k.skin("torso", [(0, 0, 0.8, 0.2, 0.24), (0.02, 0, 1.05, 0.22, 0.27), (0.02, 0, 1.25, 0.2, 0.3)], [(0, 1), (1, 2)], steel)
    k.prim("cube", "tabard", cloth, (0.2, 0, 0.8), (0.06, 0.26, 0.46), bevel=0.02)
    k.prim("cube", "tab_trim", gold, (0.21, 0, 0.6), (0.06, 0.27, 0.05), bevel=0.01)
    k.prim("cyl", "belt", leather, (0.01, 0, 0.86), (0.48, 0.58, 0.08))
    k.prim("cube", "buckle", gold, (0.24, 0, 0.86), (0.04, 0.1, 0.09), bevel=0.01)
    k.skin("arm_f", [(0.02, 0.33, 1.25, 0.11), (0.12, 0.38, 1.02, 0.09), (0.3, 0.3, 0.98, 0.08)], [(0, 1), (1, 2)], cloth)
    k.skin("arm_n", [(0.02, -0.33, 1.25, 0.11), (0.1, -0.44, 1.02, 0.09), (0.34, -0.46, 1.0, 0.08)], [(0, 1), (1, 2)], cloth)
    for y in (0.34, -0.34):
        k.prim("sphere", "pauldron", steel, (0.02, y, 1.3), (0.3, 0.3, 0.24))
    k.prim("sphere", "hand_n", skin_m, (0.36, -0.46, 1.0), (0.15, 0.15, 0.15))
    k.prim("sphere", "head", skin_m, (0.04, 0, 1.62), (0.5, 0.48, 0.5))
    k.prim("sphere", "nose", skin_m, (0.3, 0, 1.57), (0.1, 0.1, 0.1))
    for y in (0.1, -0.1):
        k.prim("sphere", "eye", dark, (0.265, y, 1.63), (0.07, 0.08, 0.11))
    k.prim("sphere", "helm", steel, (-0.03, 0, 1.78), (0.56, 0.56, 0.4))
    k.prim("cyl", "brim", steel, (-0.01, 0, 1.76), (0.64, 0.62, 0.05))
    k.prim("cube", "chin", k.mat("hair", "6a4424", 0.9), (0.2, 0, 1.46), (0.2, 0.3, 0.12), bevel=0.04)
    k.prim("cube", "crest", red, (-0.06, 0, 2.0), (0.46, 0.08, 0.18), bevel=0.04)
    # sword in the near hand, raised; round shield on the far arm, edge-on behind the body
    k.prim("cube", "blade", steel, (0.68, -0.46, 1.42), (0.12, 0.03, 0.8), rot=(0, 35, 0), bevel=0.01)
    k.prim("cube", "guard", gold, (0.42, -0.46, 1.06), (0.3, 0.07, 0.07), rot=(0, 35, 0), bevel=0.01)
    k.prim("cyl", "grip", leather, (0.37, -0.46, 0.98), (0.06, 0.06, 0.16), rot=(0, 35, 0))
    k.prim("cyl", "shield", cloth, (0.3, 0.36, 1.02), (0.66, 0.66, 0.06), rot=(90, 0, -35))
    k.prim("cyl", "shield_rim", steel, (0.295, 0.37, 1.02), (0.72, 0.72, 0.04), rot=(90, 0, -35))
    k.prim("sphere", "boss", gold, (0.33, 0.33, 1.02), (0.2, 0.2, 0.12), rot=(0, 0, -35))
