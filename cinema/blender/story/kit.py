"""Small shared pieces for shot specs: aiming the camera at a point, and set dressing the extras reuse
(standing stones, glow-moss, falling shards, rolling boulders, reeds, fire rings, ice cages, stilt towns)."""
import math, random, json, os
import bpy
from mathutils import Vector
import cine3d as C, hero, wardens as W, sets


def aim(t, pos, target, roll=0.0):
    """A camera key at `t` seconds: at `pos`, looking at `target` (both relative to the mark)."""
    dx, dy, dz = (target[i] - pos[i] for i in range(3))
    rz = math.degrees(math.atan2(-dx, dy))
    rx = 90 + math.degrees(math.atan2(dz, math.hypot(dx, dy)))
    return (t, tuple(pos), (round(rx, 2), roll, round(rz, 2)))


def _at(S, p):
    return S["here"] + Vector(p)


def stones(S, centre=(0, 30, 0), n=11, r=9.0, h=(3.0, 5.5), seed=3):
    """A ring of standing stones (Galeborn camps steer by them)."""
    R = random.Random(seed); c = _at(S, centre); STONE = W.mountain_stone("standing_stone", (0.42, 0.41, 0.38), moss=0.3)
    for k in range(n):
        a = 2 * math.pi * k / n + R.uniform(-0.1, 0.1); hh = R.uniform(*h)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(c.x + math.cos(a) * r, c.y + math.sin(a) * r, c.z + hh / 2 - 0.3))
        s = bpy.context.object; s.scale = (R.uniform(0.9, 1.4), R.uniform(0.5, 0.8), hh)
        s.rotation_euler = (R.uniform(-0.06, 0.06), R.uniform(-0.06, 0.06), a + math.pi / 2)
        s.data.materials.append(STONE); C.rough_up(s, 0.12, 0.8, subdiv=3)


def glow_moss(S, rows=6, per_row=40, depth=(4, 40), width=18, rgb=(0.2, 1.0, 0.4), dark_from=None, light_from=None, step=1.6):
    """Rows of glowing moss along the roots, like lit streets. `dark_from`: seconds when the far row starts
    going out, one row after another every `step` seconds; `light_from` does the reverse (they light again)."""
    R = random.Random(9)
    for k in range(rows):
        m = C.mat("glow_moss_%d" % k, (0.05, 0.12, 0.06), 0.9, emit=rgb, strength=1.2)
        s = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        y = depth[0] + (depth[1] - depth[0]) * k / max(rows - 1, 1)
        if dark_from is not None:
            t0 = dark_from + (rows - 1 - k) * step
            for t, v in ((0, 1.2), (t0, 1.2), (t0 + 0.8, 0.0)):
                s.default_value = v; s.keyframe_insert("default_value", frame=C.sec(t))
        if light_from is not None:
            t0 = light_from + k * step
            for t, v in ((0, 0.0), (t0, 0.0), (t0 + 1.2, 1.2)):
                s.default_value = v; s.keyframe_insert("default_value", frame=C.sec(t))
        for i in range(per_row):
            p = _at(S, (R.uniform(-width, width), y + R.uniform(-1.5, 1.5), 0.02))
            bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=2, location=p)
            o = bpy.context.object; o.scale = (R.uniform(0.15, 0.5), R.uniform(0.1, 0.3), 0.05); o.data.materials.append(m)
            o.rotation_euler.z = R.uniform(0, 3.1)


def shards(S, centre=(0, 12, 0), n=160, top=26, spread=10, start=1.0, over=3.0, rgb=(0.05, 0.06, 0.08), seed=5):
    """Black glass falling out of the sky (the Thunderhead shattering), starting at `start` seconds."""
    R = random.Random(seed); c = _at(S, centre)
    G = C.mat("storm_glass", rgb, 0.05, emit=(0.6, 0.75, 1.0), strength=0.6, metal=0.3)
    for i in range(n):
        p = c + Vector((R.uniform(-spread, spread), R.uniform(-spread, spread), top + R.uniform(-4, 6)))
        bpy.ops.mesh.primitive_cone_add(vertices=3, radius1=R.uniform(0.15, 0.6), depth=R.uniform(0.4, 1.6), location=p)
        o = bpy.context.object; o.data.materials.append(G)
        t0 = start + R.uniform(0, over); fall = math.sqrt(2 * p.z / 9.8)
        o.keyframe_insert("location", frame=C.sec(t0))
        o.location.z = c.z - 0.2; o.rotation_euler = (R.uniform(0, 6), R.uniform(0, 6), R.uniform(0, 6))
        o.keyframe_insert("location", frame=C.sec(t0 + fall)); o.keyframe_insert("rotation_euler", frame=C.sec(t0 + fall))
        o.rotation_euler = (0, 0, 0); o.keyframe_insert("rotation_euler", frame=C.sec(t0))


def boulders(S, from_=(0, 4, 2.0), n=9, run=7.0, start=2.0, seed=6):
    """A body breaking into boulders that roll away downhill (toward -Y) and stop."""
    R = random.Random(seed); c = _at(S, from_)
    for i in range(n):
        o = sets.rock(tuple(c + Vector((R.uniform(-0.8, 0.8), R.uniform(-0.5, 0.5), R.uniform(-1, 1)))), 0, R.uniform(0.15, 0.3))
        o.keyframe_insert("location", frame=C.sec(start)); o.keyframe_insert("rotation_euler", frame=C.sec(start))
        d = Vector((R.uniform(-3, 3), -R.uniform(run * 0.4, run), 0))
        o.location = Vector((o.location.x + d.x, o.location.y + d.y, c.z - from_[2] + 0.3))
        o.rotation_euler.x -= d.length / 0.6
        t1 = start + R.uniform(2.5, 4.5)
        o.keyframe_insert("location", frame=C.sec(t1)); o.keyframe_insert("rotation_euler", frame=C.sec(t1))
        for fc in (o.animation_data.action.fcurves if hasattr(o.animation_data.action, "fcurves") else []):
            for kp in fc.keyframe_points:
                kp.interpolation = "SINE"; kp.easing = "EASE_OUT"


def reeds(S, n=9000, area=(14, 10), centre=(0, 4, 0), dry=True, seed=7):
    """A reed bed: thin bent blades (as one mesh)."""
    import bmesh
    R = random.Random(seed); c = _at(S, centre); bm = bmesh.new()
    for i in range(n):
        x, y = c.x + R.uniform(-area[0], area[0]), c.y + R.uniform(-area[1], area[1])
        if math.hypot(x - c.x, y - c.y + 4) < 1.6:
            continue
        h = R.uniform(0.5, 1.3); lean = Vector((R.uniform(-0.25, 0.25), R.uniform(-0.25, 0.25), 0))
        v = [bm.verts.new((x - 0.008, y, 0)), bm.verts.new((x + 0.008, y, 0)), bm.verts.new(Vector((x, y, h)) + lean)]
        bm.faces.new(v)
    me = bpy.data.meshes.new("reeds"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("reeds", me); C.sc.collection.objects.link(o)
    o.data.materials.append(C.mat("reed", (0.36, 0.3, 0.18) if dry else (0.15, 0.22, 0.08), 0.8))
    return o


def fire_ring(S, centre=(0, 2, 0), r=4.0, n=26, h=(1.2, 2.6), seed=8):
    """A ring of fire burning on the ice."""
    R = random.Random(seed); c = _at(S, centre); F = W.flame_mat("ring_fire", (1.0, 0.35, 0.05), 2.5)
    for k in range(n):
        a = 2 * math.pi * k / n; hh = R.uniform(*h)
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=R.uniform(0.35, 0.7), depth=hh,
                                        location=(c.x + math.cos(a) * r, c.y + math.sin(a) * r, c.z + hh / 2))
        o = bpy.context.object; o.data.materials.append(F); o.visible_shadow = False
    for k in range(4):
        a = 2 * math.pi * k / 4
        C.light("POINT", (c.x + math.cos(a) * r, c.y + math.sin(a) * r, c.z + 1.2), (0, 0, 0), 700, (1.0, 0.45, 0.12), 0.6, "fire")


def ice_cage(S, centre=(0, 2, 0), r=1.6, h=4.5):
    """A short tower of clear ice around a figure, open at the front."""
    c = _at(S, centre); ICE = W.sea_glass("tower_ice_near", (0.78, 0.93, 0.98))
    for k in range(9):
        a = math.radians(315 + k * 33.75)   # leave a gap toward -Y (270 degrees, the camera side)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.42, depth=h + (k % 3) * 0.6,
                                            location=(c.x + math.cos(a) * r, c.y + math.sin(a) * r, c.z + h / 2))
        o = bpy.context.object; o.data.materials.append(ICE); o.rotation_euler = (0.04 * (k % 2), 0.05, 0)


def stilt_town(S, centre=(30, 70, 0), n=14, seed=10):
    """A Tidefolk town on stilts over the ice, lit by torches."""
    R = random.Random(seed); c = _at(S, centre)
    WOOD = C.mat("stilt_wood", (0.12, 0.09, 0.07), 0.85); ROOF = C.mat("tide_roof", (0.55, 0.58, 0.6), 0.6)
    TORCH = C.mat("torch", (1, 0.6, 0.3), 0.5, emit=(1.0, 0.55, 0.2), strength=25)
    for i in range(n):
        x, y = c.x + R.uniform(-22, 22), c.y + R.uniform(-12, 12); z = 3.0
        for dx in (-2, 2):
            for dy in (-1.5, 1.5):
                bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.14, depth=z, location=(x + dx, y + dy, z / 2)); bpy.context.object.data.materials.append(WOOD)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x, y, z + 1.3)); hs = bpy.context.object; hs.scale = (4.6, 3.6, 2.6); hs.data.materials.append(WOOD)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=3.6, depth=1.8, location=(x, y, z + 3.5)); rf = bpy.context.object
        rf.rotation_euler.z = math.pi / 4; rf.scale = (1.0, 0.85, 1.0); rf.data.materials.append(ROOF)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(x + 2.4, y - 1.9, z + 1.0)); bpy.context.object.data.materials.append(TORCH)
        if i % 3 == 0:
            C.light("POINT", (x + 2.4, y - 2.2, z + 1.0), (0, 0, 0), 900, (1.0, 0.55, 0.2), 0.3, "torch")


def hand_glow(rigs, who, rgb=(0.4, 1.0, 0.45), energy=40, side="r", size=0.035):
    """A small glowing thing held in a hand (Elowen's seed)."""
    rig = rigs[who]
    G = hero.glow_mat("seed_glow", rgb, 20)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size); s = bpy.context.object; s.data.materials.append(G)
    bone = "handslot." + side if ("handslot." + side) in rig.pose.bones else "hand." + side
    C.attach(s, rig, bone)
    L = C.light("POINT", (0, 0, 0), (0, 0, 0), energy, rgb, 0.05, "seed_light"); C.attach(L, rig, bone)


def rise(rigs, who, depth=4.0, t0=0.5, t1=6.0):
    """A figure rising out of the water (from `depth` metres under) between t0 and t1 seconds."""
    rig = rigs[who]; z = rig.location.z
    rig.location.z = z - depth; rig.keyframe_insert("location", index=2, frame=C.sec(t0))
    rig.location.z = z; rig.keyframe_insert("location", index=2, frame=C.sec(t1))


def towers(S, spots=((-6, 9), (7, 12)), col=(0.4, 0.8, 1.0)):
    """Two of the player's towers standing behind the scene."""
    for x, y in spots:
        p = _at(S, (x, y, 0)); C.tower(p.x, p.y, col)


def push(target=(0, 0, 1.6), d=(3.0, 2.4), side=0.4, lift=0.0, lens=50, **kw):
    """A slow push-in on a point (a face, usually), from slightly to one side. Times are 0..1 of the shot."""
    tx, ty, tz = target
    a = (tx + side * d[0], ty - d[0], tz + lift); b = (tx + side * d[1], ty - d[1], tz + lift)
    return dict(cam=[aim(0, a, target), aim(1, b, target)], lens=lens, norm=True, **kw)


def drift(a, b, target, target2=None, lens=30, **kw):
    """A camera drifting from a to b while looking at target (then target2). Times are 0..1 of the shot."""
    return dict(cam=[aim(0, a, target), aim(1, b, target2 or target)], lens=lens, norm=True, **kw)


def doors(S, y=9.0, half=4.0, h=9.0, t0=2.0, t1=11.0, opening=False, rgb=(0.36, 0.22, 0.16), braziers=True):
    """A pair of great stone (or wooden) doors across +Y at `y`, swinging shut (or open) between t0 and t1."""
    m = S["here"]; STONE = W.mountain_stone("big_door", rgb, moss=0.0)
    for sx in (-1, 1):
        hinge = bpy.data.objects.new("door_hinge", None); C.sc.collection.objects.link(hinge)
        hinge.location = (m.x + sx * half, m.y + y, m.z)
        d = C.box("door", (0, 0, 0), (half, 0.6, h), STONE, bevel=0.08)
        d.parent = hinge; d.location = (-sx * half / 2, 0, h / 2)
        keys = ((0, 0.0), (t0, 0.0), (t1, 1.35)) if opening else ((0, 1.35), (t0, 1.35), (t1, 0.0))
        for t, ang in keys:
            hinge.rotation_euler.z = sx * ang; hinge.keyframe_insert("rotation_euler", index=2, frame=C.sec(t))
        if braziers:
            for k in range(4):
                C.brazier(m.x + sx * (half - 0.8), m.y + y + 3 + k * 4, m.z, 350)


def darkness(S, rise=(2.0, 20.0), at=(0, 260, 0), width=900):
    """A wall of black rolling up out of the eastern horizon and over the sky."""
    m = S["here"]
    bpy.ops.mesh.primitive_cube_add(size=1, location=(m.x + at[0], m.y - at[1], -60))
    o = bpy.context.object; o.name = "dark_wall"; o.scale = (width, 120, 140)
    mt = bpy.data.materials.new("dark_wall"); mt.use_nodes = True; nt = mt.node_tree
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    v = nt.nodes.new("ShaderNodeVolumePrincipled"); v.inputs["Density"].default_value = 0.08
    v.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1)
    nt.links.new(v.outputs[0], nt.nodes["Material Output"].inputs["Volume"]); o.data.materials.append(mt)
    o.keyframe_insert("location", index=2, frame=C.sec(rise[0])); o.location.z = 160; o.keyframe_insert("location", index=2, frame=C.sec(rise[1]))


def sundered_heart(rigs, who="cassivane_ash", n=60, r=2.2, seed=12):
    """The Sundered Heart: a floating knot of Sunstone shards in six colours around a man, slowly turning."""
    R = random.Random(seed); rig = rigs[who]
    piv = bpy.data.objects.new("heart_knot", None); C.sc.collection.objects.link(piv); piv.parent = rig; piv.location = (0, 0, 1.2)
    piv.keyframe_insert("rotation_euler", index=2, frame=1); piv.rotation_euler.z = 1.5; piv.keyframe_insert("rotation_euler", index=2, frame=C.sc.frame_end)
    cols = [(1, 0.3, 0.08), (0.75, 0.85, 1), (0.35, 1, 0.35), (0.3, 0.85, 1), (1, 0.7, 0.3), (0.7, 0.45, 1)]
    mats = [C.mat("shard_%d" % k, (0.8, 0.8, 0.8), 0.05, emit=c, strength=6) for k, c in enumerate(cols)]
    for i in range(n):
        v = Vector((R.gauss(0, 1), R.gauss(0, 1), R.gauss(0, 0.8))).normalized() * r * R.uniform(0.6, 1.1)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=R.uniform(0.08, 0.25), depth=R.uniform(0.5, 1.4), location=v)
        o = bpy.context.object; o.parent = piv; o.rotation_euler = (R.uniform(0, 6), R.uniform(0, 6), R.uniform(0, 6))
        o.data.materials.append(mats[i % 6])
    C.light("POINT", (0, 0, 0), (0, 0, 0), 400, (1.0, 0.85, 0.7), 1.0, "heart_light").parent = piv


def falling_stars(S, n=30, start=1.0, seed=13):
    """Burning pieces of the Sunstone falling across the city."""
    R = random.Random(seed); m = S["here"]
    G = C.mat("sun_shard", (1, 0.9, 0.6), 0.2, emit=(1.0, 0.8, 0.45), strength=40)
    for i in range(n):
        p = Vector((R.uniform(-60, 60), R.uniform(-60, 60), 80 + R.uniform(-5, 10)))
        bpy.ops.mesh.primitive_ico_sphere_add(radius=R.uniform(0.3, 0.9), subdivisions=1, location=p)
        o = bpy.context.object; o.data.materials.append(G)
        t0 = start + R.uniform(0, 6)
        o.keyframe_insert("location", frame=C.sec(t0))
        o.location = p + Vector((R.uniform(-60, 60), R.uniform(-60, 60), -p.z - 2)); o.keyframe_insert("location", frame=C.sec(t0 + 4))


def silent(seconds=6.0):
    """A shot with no voice line."""
    return dict(seconds=seconds)


# ------------------------------------------------------------------ the land hordes (each land turned on its own people)
def bird_circle(S, rigs, centre=(0, 30, 18), r=14.0, secs=24.0, rider="vholt"):
    """Vholt on his black thunderbird, circling high overhead (the rider is cast with Sit_Chair_Idle)."""
    import heralds
    c = S["here"] + Vector(centre)
    root, saddle = heralds.thunderbird(loc=(0, 0, 0), span=8.0)   # flaps (and bobs) inside a mover that flies the circle
    mover = bpy.data.objects.new("bird_path", None); C.sc.collection.objects.link(mover); root.parent = mover
    if rider in rigs:
        heralds.mount(rigs[rider], saddle)
    for k in range(9):
        a = math.pi * 0.2 + k * (math.pi * 0.9 / 8); t = secs * k / 8
        mover.location = (c.x + math.cos(a) * r, c.y + math.sin(a) * r * 0.6, c.z + math.sin(k) * 1.5)
        mover.rotation_euler = (0, -0.25, a + math.pi)   # banking into the turn, beak along the path
        mover.keyframe_insert("location", frame=C.sec(t)); mover.keyframe_insert("rotation_euler", frame=C.sec(t))


def bird_down(S, rigs, at=(2.5, 3.5, 0)):
    """The thunderbird crashed on the ground, wings spread, still smoking."""
    import heralds
    root, _ = heralds.thunderbird(loc=tuple(S["here"] + Vector(at) + Vector((0, 0, 0.9))), span=8.0, flap=0)
    root.rotation_euler = (0.25, 0.15, 2.4)


def walking_tree(S, start=(6, 26, 0), speed=0.5, sway=0.05, scale=1.6, seed=3):
    """An ancient oak torn out of the ground, walking toward the camera (-Y), rocking side to side."""
    o = sets.tree(tuple(S["here"] + Vector(start)), 0.4, scale, "broad")
    o.keyframe_insert("location", frame=1)
    end = C.sc.frame_end
    o.location.y -= speed * (end - 1) / C.FPS; o.keyframe_insert("location", frame=end)
    for f in range(1, end + 1, 18):
        o.rotation_euler.y = sway * (1 if (f // 18) % 2 else -1); o.keyframe_insert("rotation_euler", index=1, frame=f)
    return o


def fallen_tree(S, at=(2.5, 3.0, 0), scale=1.2):
    """A felled oak lying on its side."""
    o = sets.tree(tuple(S["here"] + Vector(at)), 0.0, scale, "broad")
    o.rotation_euler = (0, math.radians(84), 0.5)
    return o


def walking_rocks(S, n=7, centre=(0, 24, 0), spread=10, speed=0.45, seed=4):
    """Boulders standing up off the canyon floor and lumbering toward the camera."""
    R = random.Random(seed); c = S["here"] + Vector(centre)
    for i in range(n):
        p = c + Vector((R.uniform(-spread, spread), R.uniform(-spread / 2, spread / 2), 0))
        o = sets.rock(tuple(p), R.uniform(0, 6), R.uniform(0.5, 0.9))
        o.keyframe_insert("location", frame=1)
        for f in range(1, C.sc.frame_end + 1, 14):   # a heavy step every 14 frames
            o.location.y = p.y - speed * f / C.FPS; o.location.z = p.z + (0.25 if (f // 14) % 2 else 0)
            o.keyframe_insert("location", frame=f)


def chains(S, at=(0.4, 0.8, 0), n=5, seed=6):
    """Broken iron chains on the floor of a cold forge, and an anvil."""
    import bmesh
    R = random.Random(seed); c = S["here"] + Vector(at); IRON = C.M("iron")
    C.box("anvil", tuple(c + Vector((0.9, 0.6, 0.35))), (0.8, 0.35, 0.7), IRON, bevel=0.03)
    for k in range(n):
        p = c + Vector((R.uniform(-1.2, 1.2), R.uniform(-0.8, 0.8), 0.04)); a = R.uniform(0, 6.3)
        for j in range(R.randint(5, 10)):
            bpy.ops.mesh.primitive_torus_add(major_radius=0.05, minor_radius=0.014,
                                            location=(p.x + math.cos(a) * j * 0.08, p.y + math.sin(a) * j * 0.08, 0.03),
                                            rotation=(math.pi / 2 * (j % 2), 0, a))
            bpy.context.object.data.materials.append(IRON)


def cart(S, at=(1.4, 0.8, 0), plan=True):
    """A handcart with a tower plan pinned on top (Fennick's)."""
    c = S["here"] + Vector(at); WOOD = C.mat("cart_wood", (0.22, 0.14, 0.08), 0.8)
    C.box("cart_bed", tuple(c + Vector((0, 0, 0.75))), (1.4, 0.9, 0.12), WOOD, bevel=0.01)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_cylinder_add(radius=0.38, depth=0.06, location=(c.x + sx * 0.5, c.y - 0.5, c.z + 0.38), rotation=(0, math.pi / 2, math.pi / 2))
        bpy.context.object.data.materials.append(WOOD)
    if plan:
        bpy.ops.mesh.primitive_plane_add(size=0.7, location=tuple(c + Vector((0, 0, 0.82))))
        p = bpy.context.object; p.scale = (1.2, 0.8, 1); p.rotation_euler = (0.05, 0, 0.1)
        p.data.materials.append(C.mat("plan_paper", (0.75, 0.68, 0.5), 0.9))


def ice_holes(S, n=10, area=(14, 26), centre=(0, 14, 0), seed=7, freeze=None):
    """Black holes broken up through the sea ice (the drowned climb out of them). `freeze`: (t0, t1) when they ice over."""
    import heralds
    R = random.Random(seed); c = S["here"] + Vector(centre); BW = heralds.black_water("hole_water")
    for i in range(n):
        p = c + Vector((R.uniform(-area[0], area[0]), R.uniform(-area[1] / 2, area[1] / 2), 0.03))
        bpy.ops.mesh.primitive_circle_add(vertices=9, radius=R.uniform(0.8, 2.2), fill_type="NGON", location=p)
        o = bpy.context.object; o.data.materials.append(BW); o.scale = (1, R.uniform(0.6, 1.0), 1)
        if freeze:
            o.keyframe_insert("scale", frame=C.sec(freeze[0])); o.scale = (0.01, 0.01, 1); o.keyframe_insert("scale", frame=C.sec(freeze[1]))


def floodwater(S, r=7.0, centre=(0, 2, 0)):
    """A pool of black floodwater around a point (the ice tower stands in it)."""
    import heralds
    c = S["here"] + Vector(centre)
    bpy.ops.mesh.primitive_circle_add(vertices=48, radius=r, fill_type="NGON", location=(c.x, c.y, c.z + 0.04))
    bpy.context.object.data.materials.append(heralds.black_water("floodwater"))
