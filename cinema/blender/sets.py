"""Sets for the story videos: one builder per place, all procedural plus the CC0 Poly Haven scans in ph/.

    import sets
    S = sets.ember()          # builds the Ember Reach around the origin
    S["marks"]["hero"]        # where to stand characters; S["cams"] holds suggested camera keys

Each builder returns {"marks": {...}, "cams": {...}} so shot scripts can place people and cameras by name."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix, noise
import cine3d as C
import wardens as W


# ------------------------------------------------------------------ terrain
def heightfield(name, size, res, h, mat, loc=(0, 0, 0)):
    """A grid mesh `size` metres across with `res` cells a side, raised by h(x, y)."""
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=size / 2)
    for v in bm.verts:
        v.co.z = h(v.co.x + loc[0], v.co.y + loc[1])
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C.sc.collection.objects.link(o); o.location = loc
    for p in me.polygons:
        p.use_smooth = True
    o.data.materials.append(mat)
    return o


def fbm(x, y, scale, octaves=5, seed=0):
    return noise.fractal(Vector((x * scale + seed * 17.3, y * scale - seed * 9.1, seed * 0.37)), 0.6, 2.0, octaves)


def terraces(v, step, sharp=0.75):
    """Quantise a height into terraces with steep risers."""
    k = math.floor(v / step); t = v / step - k
    t = min(1.0, max(0.0, (t - sharp) / (1 - sharp)))
    return (k + t * t * (3 - 2 * t)) * step


# ------------------------------------------------------------------ materials
def lava(name="lava", strength=3.5):
    m, nt, out = W._blank(name)
    tc = W._n(nt, "ShaderNodeTexCoord")
    no = W._n(nt, "ShaderNodeTexNoise", _noise_dimensions="4D", Scale=0.35, Detail=8.0, Roughness=0.65)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"]); W._animate_w(no, 1 / 240)
    vo = W._n(nt, "ShaderNodeTexVoronoi", _feature="DISTANCE_TO_EDGE", Scale=0.6)
    nt.links.new(no.outputs["Color"], vo.inputs["Vector"])
    crust = W._n(nt, "ShaderNodeMapRange"); crust.inputs[1].default_value = 0.02; crust.inputs[2].default_value = 0.12
    nt.links.new(vo.outputs["Distance"], crust.inputs[0])   # 0 = hot seam, 1 = cooled crust
    col = W._ramp(nt, crust.outputs[0], (1.0, 0.32, 0.05), (0.05, 0.01, 0.003), 0.0, 1.0)
    b = W._n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.8)
    b.inputs["Base Color"].default_value = (0.02, 0.012, 0.01, 1)
    nt.links.new(col, b.inputs["Emission Color"])
    inv = W._n(nt, "ShaderNodeMath", _operation="SUBTRACT"); inv.inputs[0].default_value = 1.0; nt.links.new(crust.outputs[0], inv.inputs[1])
    st = W._n(nt, "ShaderNodeMath", _operation="MULTIPLY_ADD"); st.inputs[1].default_value = strength; st.inputs[2].default_value = 0.4
    nt.links.new(inv.outputs[0], st.inputs[0]); nt.links.new(st.outputs[0], b.inputs["Emission Strength"])
    bu = W._n(nt, "ShaderNodeBump", Strength=0.6); nt.links.new(crust.outputs[0], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def basalt_ground(name="basalt_ground"):
    """Dark basalt with ash in the flats (rock texture from ph/ when present)."""
    m = C.pbr(name, "dark_rock_02", 0.12, (0.32, 0.29, 0.28), 0.9)
    return m


def banner_cloth(name, rgb):
    return W.H.robe_cloth(name, rgb, rough=0.85, sheen=0.3)


# ------------------------------------------------------------------ props
def banner(x, y, z, rgb, h=4.5, w=1.1, rot=0.0):
    """A pole with a long hanging banner (cloth panel with folds), brass finial."""
    BR = C.mat("banner_brass", (0.7, 0.5, 0.2), 0.3, metal=1.0)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=h + 0.6, location=(x, y, z + (h + 0.6) / 2))
    pole = bpy.context.object; pole.data.materials.append(C.M("iron"))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.1, location=(x, y, z + h + 0.65)); bpy.context.object.data.materials.append(BR)
    bm = bmesh.new(); rows, cols = 16, 6
    grid = [[bm.verts.new((((c / cols) - 0.5) * w, 0.0, -r / rows * h * 0.85)) for c in range(cols + 1)] for r in range(rows + 1)]
    for r in range(rows):
        for c in range(cols):
            bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
    # swallowtail
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -h * 0.85 + 0.6 and abs(v.co.x) < (h * 0.85 + v.co.z) * 0.6], context="VERTS")
    me = bpy.data.meshes.new("banner"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("banner", me); C.sc.collection.objects.link(o)
    o.location = (x + math.cos(rot) * (w / 2 + 0.06), y + math.sin(rot) * (w / 2 + 0.06), z + h + 0.4); o.rotation_euler.z = rot
    tx = bpy.data.textures.new("banner_folds", "WOOD"); tx.wood_type = "BANDNOISE"; tx.noise_scale = 0.4; tx.turbulence = 3
    d = o.modifiers.new("folds", "DISPLACE"); d.texture = tx; d.strength = 0.12; d.direction = "Y"
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.01; o.modifiers.new("sub", "SUBSURF").levels = 1
    o.data.materials.append(banner_cloth("banner_%d" % len(bpy.data.materials), rgb))
    for p in me.polygons:
        p.use_smooth = True
    return o


def forge_house(x, y, z, rot=0.0, w=5.0, d=4.0, h=3.2, glow=(1.0, 0.45, 0.12)):
    """A squat stone forge-house with a glowing door and a smoking chimney."""
    o = C.box("forge_house", (x, y, z + h / 2), (w, d, h), C.M("rock"), bevel=0.15)
    for v in o.data.vertices:   # battered walls: narrower at the top, like a kiln
        if v.co.z > 0:
            v.co.x *= 0.82; v.co.y *= 0.82
    o.rotation_euler.z = rot
    C.rough_up(o, 0.12, 0.6, subdiv=3)
    roof = C.box("forge_roof", (x, y, z + h + 0.2), (w * 0.82 + 0.4, d * 0.82 + 0.4, 0.4), C.M("iron"), bevel=0.1); roof.rotation_euler.z = rot
    dx, dy = math.sin(rot), -math.cos(rot)
    door = C.box("forge_door", (x + dx * (d / 2 + 0.01), y + dy * (d / 2 + 0.01), z + 1.1), (1.4, 0.05, 2.0),
                 C.mat("forge_glow", glow, 0.5, emit=glow, strength=5))
    door.rotation_euler.z = rot
    C.light("POINT", (x + dx * (d / 2 + 1.0), y + dy * (d / 2 + 1.0), z + 1.4), (0, 0, 0), 400, glow, 0.8, "forge_light")
    bpy.ops.mesh.primitive_cylinder_add(radius=0.45, depth=2.5, location=(x + 1.3, y + 0.8, z + h + 1.2))
    ch = bpy.context.object; ch.data.materials.append(C.M("rock"))
    return o


def ash_fall(count=6000, area=60, top=25, rgb=(0.5, 0.48, 0.46), glowing=0.15):
    """Ash and embers drifting down through the scene (particles from a plane overhead)."""
    bpy.ops.mesh.primitive_plane_add(size=area, location=(0, 0, top)); em = bpy.context.object; em.name = "ash_sky"
    em.hide_render = True
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.025, subdivisions=1, location=(0, 0, -80)); fl = bpy.context.object; fl.name = "ash_flake"
    fl.scale = (1, 1, 0.3); fl.data.materials.append(C.mat("ash", rgb, 0.9))
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.012, subdivisions=1, location=(0, 0, -80)); eb = bpy.context.object; eb.name = "ember_mote"
    eb.data.materials.append(W.H.glow_mat("ember_mote", (1.0, 0.45, 0.1), 25))
    for nm, inst, n in (("ash", fl, count), ("embers", eb, int(count * glowing))):
        ps = em.modifiers.new(nm, "PARTICLE_SYSTEM").particle_system; st = ps.settings
        st.count = n; st.frame_start = C.sc.frame_start - 300; st.frame_end = C.sc.frame_end; st.lifetime = 400
        st.normal_factor = 0.0; st.effector_weights.gravity = 0.02; st.brownian_factor = 0.4
        st.render_type = "OBJECT"; st.instance_object = inst; st.particle_size = 1.0; st.size_random = 0.7
        st.use_rotations = True; st.rotation_factor_random = 1.0; st.angular_velocity_factor = 2.0
        ps.seed = 5 if nm == "ash" else 9
    return em


# ------------------------------------------------------------------ the lands
def ember(seed=3, caldera=True):
    """The Ember Reach: black basalt terraces, lava rivers in the valleys, forge-houses with glowing doors, red and
    brass banners, the caldera of Pyrrhenhall smoking behind, ash falling. The hero mark is a terrace at the origin."""
    R = random.Random(seed)

    def h(x, y):
        r = math.hypot(x, y)
        base = fbm(x, y, 0.025, 5, seed) * 6.0
        base = base + max(0.0, y - 15) * 0.25
        river = abs(fbm(x * 0.6, y, 0.02, 3, seed + 4))   # valleys where the ridged noise is low
        v = base - max(0.0, 0.12 - river) * 40.0
        v = terraces(v, 1.6, 0.7)
        k = min(1.0, max(0.0, (r - 9.0) / 10.0))   # a flat stage of about 9 m around the mark, easing into the land
        return v * k * k * (3 - 2 * k)
    ground = heightfield("ember_ground", 160, 220, h, basalt_ground())
    W.lumpy(ground, 3.0, 0.25, name="crags")
    lv = heightfield("lava_rivers", 160, 40, lambda x, y: -1.8 + 0.0 * x, lava())
    if caldera:
        bpy.ops.mesh.primitive_cone_add(vertices=64, radius1=70, radius2=18, depth=45, location=(15, 160, 10))
        cal = bpy.context.object; cal.name = "caldera"; cal.data.materials.append(basalt_ground("caldera_rock"))
        C.rough_up(cal, 6.0, 12.0, subdiv=4)
        bpy.ops.mesh.primitive_cylinder_add(radius=17, depth=1, location=(15, 160, 32.8))
        rim = bpy.context.object; rim.data.materials.append(C.mat("caldera_glow", (1, 0.4, 0.1), 0.5, emit=(1.0, 0.35, 0.08), strength=20))
        C.light("POINT", (15, 160, 40), (0, 0, 0), 3e5, (1.0, 0.35, 0.1), 15, "caldera_light")
    marks = {"hero": Vector((0, 0, 0))}
    houses = []
    for i in range(7):
        a = R.uniform(-1.2, 1.2); r = R.uniform(14, 34)
        x, y = math.sin(a) * r, math.cos(a) * r
        z = h(x, y)
        houses.append(forge_house(x, y, z, rot=math.atan2(-x, -y) + math.pi, w=R.uniform(4, 7), d=R.uniform(3.5, 5)))
        if i < 4:
            banner(x + 3, y - 2, z, (0.45, 0.03, 0.02) if i % 2 == 0 else (0.5, 0.32, 0.08))
    marks["forge"] = houses[0].location.copy()
    banner(-4.5, 3.0, 0.0, (0.45, 0.03, 0.02)); banner(4.8, 3.5, 0.0, (0.5, 0.32, 0.08))
    ash_fall()
    C.world(density=0.004, sky=0.0, colour=(0.035, 0.016, 0.012))
    w = C.sc.world; vol = w.node_tree.nodes.get("Principled Volume")
    if vol:
        vol.inputs["Color"].default_value = (0.6, 0.5, 0.48, 1)
    C.light("SUN", (0, 0, 50), (55, 0, 160), 0.35, (0.6, 0.65, 1.0), name="sky_cold")
    C.light("AREA", (6, -6, 5), (60, 0, 45), 500, (1.0, 0.55, 0.3), 3, "key_forge")   # warm key on the people
    cams = {"wide": [(0, (4.5, -13, 3.2), (84, 0, 17))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}
    return {"marks": marks, "cams": cams}


# ------------------------------------------------------------------ Solenne
def house(x, y, z, w, d, h, rot, wall, roof, lit=None, R=random):
    """A town house: walls with a gabled roof; a few warm windows if `lit`."""
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= w; v.co.y *= d; v.co.z = (v.co.z + 0.5) * h
    me = bpy.data.meshes.new("house"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("house", me); C.sc.collection.objects.link(o); o.data.materials.append(wall)
    o.location = (x, y, z); o.rotation_euler.z = rot
    bm = bmesh.new()
    rh = w * 0.45
    vs = [bm.verts.new(c) for c in ((-w / 2 - 0.2, -d / 2 - 0.2, h), (w / 2 + 0.2, -d / 2 - 0.2, h), (0, -d / 2 - 0.2, h + rh),
                                    (-w / 2 - 0.2, d / 2 + 0.2, h), (w / 2 + 0.2, d / 2 + 0.2, h), (0, d / 2 + 0.2, h + rh))]
    for f in ((0, 1, 2), (5, 4, 3), (0, 3, 4, 1), (1, 4, 5, 2), (2, 5, 3, 0)):
        bm.faces.new([vs[i] for i in f])
    me = bpy.data.meshes.new("roof"); bm.to_mesh(me); bm.free()
    r = bpy.data.objects.new("roof", me); C.sc.collection.objects.link(r); r.data.materials.append(roof)
    r.parent = o
    if lit:
        for k in range(R.randint(0, 3)):
            wx = R.uniform(-w / 2 + 0.5, w / 2 - 0.5); wz = R.uniform(1.0, h - 0.8)
            bpy.ops.mesh.primitive_cube_add(size=1, location=(wx, -d / 2 - 0.02, wz))
            win = bpy.context.object; win.scale = (0.45, 0.05, 0.7); win.data.materials.append(lit); win.parent = o
    return o


def wall_ring(radius, height, thick, mat, z=0.0, towers=12, gate_angles=(), seg=96, merlons=True):
    """A round city wall with crenellations and round towers; gaps where `gate_angles` (radians) are."""
    out = []
    bm = bmesh.new()
    def gate(a):
        return any(abs((a - g + math.pi) % (2 * math.pi) - math.pi) < 0.035 for g in gate_angles)
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        if gate((a0 + a1) / 2):
            continue
        pts = []
        for (a, r) in ((a0, radius - thick / 2), (a1, radius - thick / 2), (a1, radius + thick / 2), (a0, radius + thick / 2)):
            pts.append((math.cos(a) * r, math.sin(a) * r))
        lo = [bm.verts.new((px, py, z)) for px, py in pts]; hi = [bm.verts.new((px, py, z + height)) for px, py in pts]
        bm.faces.new(hi); bm.faces.new(lo[::-1])
        for k in range(4):
            bm.faces.new((lo[k], lo[(k + 1) % 4], hi[(k + 1) % 4], hi[k]))
    me = bpy.data.meshes.new("city_wall"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("city_wall", me); C.sc.collection.objects.link(o); o.data.materials.append(mat); out.append(o)
    if merlons:
        n = int(2 * math.pi * radius / 2.0)
        for i in range(n):
            a = 2 * math.pi * i / n
            if gate(a):
                continue
            m = C.box("merlon", (math.cos(a) * (radius + thick / 2 - 0.3), math.sin(a) * (radius + thick / 2 - 0.3), z + height + 0.75),
                      (0.6, 1.1, 1.5), mat)
            m.rotation_euler.z = a; out.append(m)
    for i in range(towers):
        a = 2 * math.pi * (i + 0.5) / towers
        if gate(a):
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=thick * 1.1, depth=height + 6, location=(math.cos(a) * radius, math.sin(a) * radius, z + (height + 6) / 2))
        t = bpy.context.object; t.data.materials.append(mat); out.append(t)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=thick * 1.3, depth=5, location=(math.cos(a) * radius, math.sin(a) * radius, z + height + 8.5))
        c = bpy.context.object; c.data.materials.append(C.mat("slate_roof", (0.06, 0.07, 0.09), 0.6)); out.append(c)
    return out


def sunstone_frame(x, y, z, r=9.0, lit=0.0):
    """The Sunstone's frame on the high tower: a ring of white-gold with six spokes. lit 0 = cold, 1 = blazing dawn."""
    GOLD = C.mat("sun_frame", (0.85, 0.75, 0.5), 0.3, metal=1.0, emit=(1.0, 0.85, 0.55), strength=lit * 30)
    bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.45, location=(x, y, z), rotation=(math.radians(90), 0, 0))
    ring = bpy.context.object; ring.data.materials.append(GOLD)
    for k in range(6):
        a = k * math.pi / 3
        bpy.ops.mesh.primitive_cylinder_add(radius=0.18, depth=r * 2, location=(x, y, z), rotation=(0, a, 0))
        bpy.context.object.rotation_euler = (math.radians(90), 0, 0); bpy.context.object.rotation_euler.rotate_axis("Y", a)
        bpy.context.object.data.materials.append(GOLD)
    if lit:
        C.light("POINT", (x, y - 1, z), (0, 0, 0), 5e5 * lit, (1.0, 0.85, 0.6), 4, "sunstone_light")
    return ring


def solenne(seed=11, night=True, sun_lit=0.0, refugees_lights=True):
    """Solenne, the white city at the centre of the Ring: an outer wall (east gate toward the camera side, -Y), packed
    houses of white stone with slate roofs, an inner wall round the palace hill, and the Sunstone frame on the high
    tower. Marks: 'east_wall' (on the outer wall walk, looking out east = -Y), 'inner_wall', 'gate', 'square'."""
    R = random.Random(seed)
    WALL = C.M("white_stone")
    ROOF = C.mat("roofs", (0.05, 0.055, 0.07), 0.55)
    LIT = C.mat("window", (1.0, 0.7, 0.35), 0.4, emit=(1.0, 0.62, 0.25), strength=6)
    ground = heightfield("solenne_ground", 900, 120, lambda x, y: fbm(x, y, 0.01, 3, seed) * 1.5 * min(1.0, max(0.0, (math.hypot(x, y) - 125) / 30)) - 0.05,
                         C.M("ground"))
    east = -math.pi / 2   # the east gate faces the camera side (-Y)
    walls = wall_ring(120, 14, 4.0, WALL, z=0.0, towers=20, gate_angles=(east,))
    inner = wall_ring(55, 12, 3.5, WALL, z=10.0, towers=10, gate_angles=(east,))
    for _ in range(900):
        a = R.uniform(0, 2 * math.pi); r = R.uniform(12, 114)
        if 50 < r < 60:
            continue
        x, y = math.cos(a) * r, math.sin(a) * r
        if abs(a - (east % (2 * math.pi))) < 0.06 and r > 60:
            continue   # keep the main road open
        z = 10.0 if r < 50 else 0.0
        house(x, y, z, R.uniform(4, 8), R.uniform(4, 7), R.uniform(5, 10), a + R.uniform(-0.2, 0.2), WALL, ROOF,
              LIT if night and R.random() < 0.5 else None, R)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=50, depth=10, location=(0, 0, 5))
    hill = bpy.context.object; hill.data.materials.append(WALL)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=7, depth=60, location=(0, 0, 40))
    tw = bpy.context.object; tw.data.materials.append(WALL)
    sunstone_frame(0, 0, 80, 10, sun_lit)
    if night:
        C.world(density=0.006, sky=0.02, colour=(0.012, 0.015, 0.03))
        C.moon(1.2, rot=(30, 0, 200))
    else:
        C.world(density=0.003, sky=0.6)
        C.light("SUN", (0, 0, 100), (50, 0, 30), 4.0, (1.0, 0.9, 0.75), name="dawn_sun")
    ew = east + 0.12
    marks = {"east_wall": Vector((math.cos(ew) * 120, math.sin(ew) * 120, 14.0)), "inner_wall": Vector((0, -55, 22.0)),
             "gate": Vector((0, -128, 0.0)), "square": Vector((0, -30, 10.0))}
    cams = {"aerial": [(0, (60, -330, 90), (78, 0, 10))], "wall": [(0, (math.cos(ew) * 120 + 2.5, math.sin(ew) * 120 - 5.5, 15.8), (86, 0, 20))]}
    return {"marks": marks, "cams": cams}
