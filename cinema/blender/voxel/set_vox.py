"""Ember Reach sets as 3D pixel art: the game's own Ember map as the ground, voxel houses in the game's colours
(after assets/art/game/landmarks/house_fire_*.png), lamps, a cart, a volcano behind, embers in the air."""
import math, random
import bpy
from voxkit import Part, rgb, image_plane, V, _fcurves
import cine3d as C

REPO = __import__("os").path.abspath(__import__("os").path.join(__import__("os").path.dirname(__file__), "..", "..", ".."))
SV = 0.06   # metres per cell for buildings (chunkier, as the game draws its buildings)

STONE = [rgb("#4a403c"), rgb("#54483f"), rgb("#3e3532"), rgb("#5c5048")]
ROOF = [rgb("#a83c30"), rgb("#8e3026"), rgb("#b84a34")]
WOOD = rgb("#6a4a30"); WOOD_D = rgb("#4a3020"); WIN = rgb("#ffa040")


def house(name, loc, w=56, d=44, h=38, rot=0, seed=1, chimney=True):
    p = Part(seed); rnd = random.Random(seed)
    def wall(x, y, z):
        if z % 6 == 0:
            return rgb("#2e2624")                                  # mortar courses
        return STONE[(x // 5 + y // 5 + (z // 6) * 3 + rnd.randint(0, 1)) % len(STONE)]
    p.box(0, 0, 0, w, d, h, wall)
    # windows (glowing) and a door on the front (y = 0)
    for wx in (8, w - 16):
        p.box(wx, -1, 14, wx + 8, 1, 26, lambda x, y, z: rgb("#2a1c14") if x in (wx, wx + 7) or z in (14, 25) or x == wx + 4 else WIN)
    p.box(w // 2 - 5, -1, 0, w // 2 + 5, 1, 20, lambda x, y, z: WOOD_D if (x - w // 2) % 3 == 0 else WOOD)
    # a stepped red gable roof along x, overhanging
    for i in range(0, d // 2 + 4):
        z = h + i // 1
        p.box(-3, -4 + i, z, w + 3, -3 + i, z + 2, lambda x, y, z: ROOF[(x // 4 + z) % len(ROOF)] if z % 3 else ROOF[1])
        p.box(-3, d + 3 - i, z, w + 3, d + 4 - i, z + 2, lambda x, y, z: ROOF[(x // 4 + z) % len(ROOF)] if z % 3 else ROOF[1])
    p.box(-3, d // 2 - 1, h + d // 2 + 2, w + 3, d // 2 + 1, h + d // 2 + 4, rgb("#6e241c"))
    for i in range(0, d // 2 + 3):   # gable ends filled with stone
        z = h + i
        p.box(0, i, z, 1, d - i, z + 1, wall); p.box(w - 1, i, z, w, d - i, z + 1, wall)
    if chimney:
        p.box(w - 14, d // 2 + 2, h, w - 6, d // 2 + 10, h + d // 2 + 16, lambda x, y, z: STONE[(z // 3) % 4])
        p.box(w - 13, d // 2 + 3, h + d // 2 + 16, w - 7, d // 2 + 9, h + d // 2 + 17, rgb("#ff7a2a"), glow=1.0)
    o = p.mesh(name, size=SV, origin=(w / 2, 0, 0), glow_strength=5.0)
    o.location = loc; o.rotation_euler.z = math.radians(rot)
    for wx in (8, w - 16):   # warm light out of each window
        L = C.light("POINT", (0, 0, 0), (0, 0, 0), 40, (1.0, 0.62, 0.3), 0.3, name + "_win")
        L.parent = o; L.location = ((wx + 4 - w / 2) * SV, -0.4, 20 * SV)
    return o


def lamp(name, loc, seed=5):
    p = Part(seed)
    p.box(-1, -1, 0, 2, 2, 70, rgb("#2e2a2a"))
    p.box(-4, -4, 70, 5, 5, 72, rgb("#2e2a2a"))
    p.box(-3, -3, 72, 4, 4, 80, WIN, glow=1.0)
    p.box(-4, -4, 80, 5, 5, 82, rgb("#2e2a2a"))
    o = p.mesh(name, size=V, glow_strength=2.5); o.location = loc
    L = C.light("POINT", (0, 0, 0), (0, 0, 0), 60, (1.0, 0.6, 0.28), 0.1, name + "_light"); L.parent = o; L.location = (0, 0, 76 * V)
    return o


def cart(name, loc, rot=0, seed=9):
    """Fennick's cart, a tower plan pinned on its bed (parchment with a tower drawn in ink)."""
    p = Part(seed)
    p.box(-20, -12, 14, 20, 12, 17, lambda x, y, z: WOOD_D if x % 5 == 0 else WOOD)          # bed
    p.box(-20, -12, 17, 20, -11, 22, WOOD); p.box(-20, 11, 17, 20, 12, 22, WOOD)              # sides
    p.box(19, -12, 17, 20, 12, 22, WOOD)
    for sx in (-1, 1):                                                                         # wheels
        for a in range(0, 360, 8):
            r = math.radians(a)
            for rr in (10, 11):
                p.put(-6 + rr * math.cos(r), sx * 13, 11 + rr * math.sin(r), WOOD_D)
        for a in range(0, 180, 45):
            r = math.radians(a)
            p.line((-6 - 10 * math.cos(r), sx * 13, 11 - 10 * math.sin(r)), (-6 + 10 * math.cos(r), sx * 13, 11 + 10 * math.sin(r)), 0.4, WOOD)
    p.line((-20, 0, 15), (-40, 0, 6), 0.8, WOOD)                                               # shaft
    PAPER = rgb("#e8dcb8"); INK = rgb("#3a2a22")
    def plan(x, y, z):   # a little tower drawn on the parchment: base, shaft, crystal on top
        u, v = x + 14, y + 8
        if (6 <= u <= 10 and 2 <= v <= 3) or (7 <= u <= 9 and 3 <= v <= 11) or (u in (6, 10) and 11 <= v <= 12) or (8 == u and 13 <= v <= 14):
            return INK
        return PAPER
    p.box(-14, -8, 17, 2, 8, 18, plan)
    p.box(3, -9, 17, 14, 2, 21, lambda x, y, z: rgb("#7a5a3a") if (x + z) % 3 else rgb("#5a3e28"))   # a crate
    o = p.mesh(name, size=V); o.location = loc; o.rotation_euler.z = math.radians(rot)
    return o


def volcano(loc=(6, 70, 0)):
    """A big coarse voxel volcano behind the town, glowing lava runs down its face."""
    p = Part(31); rnd = random.Random(31)
    R, H = 34, 26
    for z in range(H):
        r = R * (1 - z / (H + 4))
        for x in range(-R, R + 1):
            for y in range(-R, R + 1):
                if x * x + y * y <= r * r and (z < H - 3 or x * x + y * y > (r * 0.45) ** 2):
                    lava = (abs(x - (z * 0.2) - 3) < 1.2 and y < 0) or (abs(x + 9 - z * 0.15) < 0.9 and y < 0 and z > 6)
                    col = rgb("#ff6a1a") if lava else [rgb("#2a2224"), rgb("#342a2a"), rgb("#3e3230")][rnd.randint(0, 2)]
                    p.put(x, y, z, col, 1.0 if lava else 0.0)
    p.box(-6, -6, H - 3, 7, 7, H - 2, rgb("#ff8a2a"), glow=1.0)
    o = p.mesh("volcano", size=1.4, glow_strength=3.0); o.location = loc
    return o


def embers(count=600, area=(-8, 8, -4, 12), seed=4, frames=360):
    """Glowing cubes drifting up and sideways through the street (each its own little pixel), looping."""
    p = Part(); p.put(0, 0, 0, rgb("#ffb050"), 1.0)
    proto = p.mesh("ember_cube", size=0.02, glow_strength=4.0); proto.location = (0, 0, -50)
    rnd = random.Random(seed)
    col = bpy.data.collections.new("embers"); bpy.context.scene.collection.children.link(col)
    for i in range(count):
        e = proto.copy(); col.objects.link(e)
        x = rnd.uniform(area[0], area[1]); y = rnd.uniform(area[2], area[3]); z0 = rnd.uniform(-0.5, 4.0)
        sp = rnd.uniform(0.25, 0.6); drift = rnd.uniform(-0.2, 0.2); ph = rnd.uniform(0, 6.28)
        for f in (1, frames):
            t = (f - 1) / 24.0
            e.location = (x + drift * t + 0.1 * math.sin(ph + t), y, z0 + sp * t)
            e.keyframe_insert("location", frame=f)
        e.rotation_euler = (rnd.uniform(0, 3), rnd.uniform(0, 3), 0)
        for fc in _fcurves(e.animation_data.action):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    return col


def ember_street():
    """The street the test scene plays in. Returns marks."""
    import os
    gdir = os.path.join(REPO, "assets", "art", "game", "ground")
    image_plane("ground", os.path.join(gdir, "c_ember_1.png"), 40.0, loc=(4, 6, 0), glow_path=os.path.join(gdir, "c_ember_1_glow.png"), glow=1.5)
    house("house_a", (-4.2, 4.2, 0), seed=1)
    house("house_b", (0.6, 5.4, 0), w=48, h=34, seed=2, chimney=False)
    house("house_c", (5.6, 4.6, 0), w=60, h=42, seed=3)
    house("house_d", (-9.5, 2.0, 0), rot=60, seed=4)
    house("house_e", (10.0, 2.4, 0), rot=-55, seed=5)
    lamp("lamp_a", (-1.6, 2.2, 0)); lamp("lamp_b", (3.4, 2.6, 0))
    cart("cart", (1.35, 0.9, 0), rot=-15)
    volcano()
    embers()
    # sky: a deep ember dusk, bright enough that the figures always read
    w = bpy.data.worlds.new("ember_sky"); bpy.context.scene.world = w; w.use_nodes = True; nt = w.node_tree
    bg = nt.nodes["Background"]; tc = nt.nodes.new("ShaderNodeTexCoord"); sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0]); nt.links.new(sep.outputs["Z"], ramp.inputs[0])
    ramp.color_ramp.elements[0].position = 0.48; ramp.color_ramp.elements[0].color = (0.55, 0.16, 0.06, 1)
    ramp.color_ramp.elements[1].position = 0.75; ramp.color_ramp.elements[1].color = (0.06, 0.03, 0.08, 1)
    nt.links.new(ramp.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 1.0
    return dict(fennick=(0.2, 0.0, 0.0), tamsin=(-1.9, 2.0, 0.0), cart=(1.35, 0.9, 0.0))
