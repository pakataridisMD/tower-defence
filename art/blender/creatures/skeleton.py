CAMERA = dict(center=(0.1, 0, 0.98), ortho=2.3, azim=-74, elev=16)


def build(k):
    bone = k.mat("bone", "ece4cc", 0.95)
    shade = k.mat("bone2", "bcae90", 0.95)
    dark = k.mat("dark", "14121a", 0.6)
    glow = k.mat("glow", "60e0ff", 0.4, emit=5.0)
    rust = k.mat("rust", "9a8a80", 0.7, 0.15)
    rag = k.mat("rag", "5a3a5a", 0.95)
    wood = k.mat("wood", "4a3828", 0.9)
    # thin limbs with knobbly joints
    def limb(name, pts, r=0.045):
        k.skin(name, [(x, y, z, r) for x, y, z in pts], [(i, i + 1) for i in range(len(pts) - 1)], bone, sub=1)
        for x, y, z in pts:
            k.prim("sphere", name + "_j", shade, (x, y, z), (r * 3, r * 3, r * 3))
    limb("leg_f", [(0, 0.12, 0.74), (-0.08, 0.13, 0.42), (-0.14, 0.13, 0.1)])
    limb("leg_n", [(0, -0.12, 0.74), (0.12, -0.13, 0.42), (0.14, -0.13, 0.1)])
    for x, y in ((-0.08, 0.13), (0.2, -0.13)):
        k.prim("cube", "foot", bone, (x, y, 0.05), (0.26, 0.1, 0.07), bevel=0.02)
    k.prim("sphere", "pelvis", bone, (0, 0, 0.76), (0.26, 0.42, 0.2))
    limb("spine", [(0, 0, 0.8), (0.0, 0, 1.0), (0.02, 0, 1.3)], 0.05)
    for i in range(4):  # ribs: flattened rings
        z = 0.98 + i * 0.09
        o = k.prim("cyl", "rib", bone, (0.03, 0, z), (0.34 + 0.03 * (i - 1.5) ** 2 * -1 + 0.06, 0.5, 0.045), seg=14)
    k.prim("sphere", "chest_dark", dark, (0.02, 0, 1.12), (0.26, 0.4, 0.4))
    k.prim("cube", "shoulders", bone, (0.02, 0, 1.33), (0.1, 0.62, 0.08), bevel=0.03)
    limb("arm_f", [(0.02, 0.32, 1.32), (0.0, 0.36, 1.04), (0.1, 0.34, 0.8)])
    limb("arm_n", [(0.02, -0.32, 1.32), (0.14, -0.4, 1.08), (0.38, -0.42, 1.06)])
    # skull: big, with dark sockets and a glowing pinpoint, jaw
    k.prim("sphere", "skull", bone, (0.05, 0, 1.66), (0.52, 0.5, 0.5))
    k.prim("cube", "jaw", bone, (0.16, 0, 1.44), (0.26, 0.3, 0.12), bevel=0.04)
    for y in (0.12, -0.12):
        k.prim("sphere", "socket", dark, (0.26, y, 1.66), (0.14, 0.17, 0.19))
        k.prim("sphere", "eyeglow", glow, (0.315, y, 1.66), (0.05, 0.06, 0.06))
    k.prim("sphere", "nosehole", dark, (0.3, 0, 1.56), (0.06, 0.07, 0.09))
    for i in range(4):
        k.prim("cube", "tooth", dark, (0.29, -0.09 + i * 0.06, 1.47), (0.02, 0.015, 0.09))
    k.prim("cube", "hood_rag", rag, (-0.12, 0, 1.3), (0.1, 0.56, 0.6), rot=(0, -8, 0), bevel=0.04)
    # rusty curved sword and a broken round shield
    k.prim("cube", "blade", rust, (0.72, -0.44, 1.42), (0.13, 0.03, 0.72), rot=(0, 38, 0), bevel=0.012)
    k.prim("cube", "guard", rust, (0.46, -0.44, 1.1), (0.26, 0.06, 0.06), rot=(0, 38, 0), bevel=0.01)
