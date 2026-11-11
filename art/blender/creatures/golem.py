CAMERA = dict(center=(0.15, 0, 1.3), ortho=3.0, azim=-74, elev=16)


def build(k):
    rock = k.mat("rock", "a09684", 0.95, noise=0.7, noise_scale=6)
    rock2 = k.mat("rock2", "7a7062", 0.95, noise=0.7, noise_scale=9)
    moss = k.mat("moss", "5a7a34", 0.95, noise=0.5, noise_scale=20)
    core = k.mat("core", "ffb030", 0.4, emit=8.0)
    crack = k.mat("crack", "ff7a20", 0.4, emit=5.0)

    def boulder(name, loc, scale, m=rock, rot=(0, 0, 0)):
        o = k.prim("ico", name, m, loc, scale, rot=rot, subdiv=2, smooth=False)
        k.displace(o, 0.12, 0.35)
        return o
    # boulders stacked into a body: tiny head sunk between massive shoulders, forearms like pillars
    boulder("hips", (0, 0, 0.75), (0.75, 0.9, 0.55), rock2)
    boulder("chest", (0.08, 0, 1.4), (1.05, 1.3, 1.0))
    boulder("leg_f", (-0.1, 0.32, 0.32), (0.45, 0.42, 0.66), rock2)
    boulder("leg_n", (0.12, -0.32, 0.32), (0.45, 0.42, 0.66), rock2)
    boulder("foot_f", (0.0, 0.33, 0.1), (0.6, 0.46, 0.24))
    boulder("foot_n", (0.24, -0.33, 0.1), (0.6, 0.46, 0.24))
    boulder("sh_f", (0.08, 0.78, 1.72), (0.7, 0.62, 0.6))
    boulder("sh_n", (0.08, -0.78, 1.72), (0.72, 0.64, 0.62))
    boulder("up_f", (0.14, 0.88, 1.25), (0.42, 0.4, 0.6), rock2)
    boulder("up_n", (0.16, -0.9, 1.25), (0.42, 0.4, 0.6), rock2)
    boulder("fore_f", (0.3, 0.86, 0.72), (0.56, 0.5, 0.8))
    boulder("fore_n", (0.36, -0.9, 0.72), (0.58, 0.52, 0.82))
    boulder("fist_n", (0.42, -0.9, 0.3), (0.6, 0.56, 0.5), rock2)
    boulder("fist_f", (0.36, 0.86, 0.3), (0.6, 0.56, 0.5), rock2)
    boulder("head", (0.34, 0, 2.0), (0.5, 0.52, 0.44), rock2)
    # glowing eyes and a core burning through the chest cracks
    for y in (0.13, -0.13):
        k.prim("cube", "eye", core, (0.57, y, 2.02), (0.06, 0.12, 0.07))
    k.prim("sphere", "core", core, (0.56, 0, 1.42), (0.3, 0.5, 0.5))
    k.prim("cube", "crack1", crack, (0.6, -0.3, 1.2), (0.03, 0.05, 0.5), rot=(25, 0, 0))
    k.prim("cube", "crack2", crack, (0.6, 0.26, 1.62), (0.03, 0.05, 0.4), rot=(-35, 0, 0))
    k.prim("cube", "crack3", crack, (0.44, -0.9, 0.78), (0.26, 0.04, 0.4), rot=(0, 20, 0))
    # moss and a small tree on the shoulders
    o = k.prim("sphere", "moss1", moss, (0.02, -0.78, 2.02), (0.66, 0.6, 0.22))
    k.displace(o, 0.05, 0.2)
    o = k.prim("sphere", "moss2", moss, (0.0, 0.74, 2.0), (0.6, 0.56, 0.2))
    k.displace(o, 0.05, 0.2)
    k.prim("cyl", "trunk", k.mat("bark", "4a3424", 0.9), (-0.08, -0.7, 2.25), (0.07, 0.07, 0.34))
    k.prim("cone", "pine1", k.mat("pine", "2e5a2e", 0.9), (-0.08, -0.7, 2.5), (0.36, 0.36, 0.42))
    k.prim("cone", "pine2", k.mat("pine", "2e5a2e", 0.9), (-0.08, -0.7, 2.72), (0.26, 0.26, 0.36))
