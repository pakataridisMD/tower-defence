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


def bounded_fog(size=900.0, height=220.0, z0=-20.0):
    """Move the world's fog into a big box around the set. A world volume is infinite, and in Cycles it swallows
    sunlight and moonlight completely, so sets with a sun need the fog bounded."""
    w = C.sc.world; nt = w.node_tree; out = nt.nodes["World Output"]
    vol = nt.nodes.get("Principled Volume")
    if not vol:
        return None
    for l in list(out.inputs["Volume"].links):
        nt.links.remove(l)
    d = vol.inputs["Density"].default_value; col = vol.inputs["Color"].default_value[:3]; an = vol.inputs["Anisotropy"].default_value
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0, 0, z0 + height / 2)); box = bpy.context.object; box.name = "fog"
    box.scale = (size, size, height)
    m, mt, mo = W._blank("fog")
    v = W._n(mt, "ShaderNodeVolumePrincipled", Density=d, Anisotropy=an); v.inputs["Color"].default_value = (*col, 1)
    mt.links.new(v.outputs[0], mo.inputs["Volume"])
    box.data.materials.append(m)
    box.visible_shadow = True
    return box


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
    bounded_fog(400, 120)
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
    LIT = C.mat("window", (1.0, 0.7, 0.35), 0.4, emit=(1.0, 0.62, 0.25), strength=14)
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
        if math.hypot(x, y + 30) < 11:
            continue   # and the palace square (mark 'square') clear
        z = 10.0 if r < 50 else 0.0
        house(x, y, z, R.uniform(4, 8), R.uniform(4, 7), R.uniform(5, 10), a + R.uniform(-0.2, 0.2), WALL, ROOF,
              LIT if night and R.random() < 0.5 else None, R)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=50, depth=10, location=(0, 0, 5))
    hill = bpy.context.object; hill.data.materials.append(WALL)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32, radius=7, depth=60, location=(0, 0, 40))
    tw = bpy.context.object; tw.data.materials.append(WALL)
    sunstone_frame(0, 0, 80, 10, sun_lit)
    if night:
        C.world(density=0.0012, sky=0.06, colour=(0.012, 0.015, 0.03))
        C.moon(4.0, rot=(35, 0, 200))
    else:
        C.world(density=0.003, sky=0.6)
        C.light("SUN", (0, 0, 100), (50, 0, 30), 4.0, (1.0, 0.9, 0.75), name="dawn_sun")
    bounded_fog(1200, 200)
    ew = east + 0.12
    marks = {"east_wall": Vector((math.cos(ew) * 120, math.sin(ew) * 120, 14.0)), "inner_wall": Vector((0, -55, 22.0)),
             "gate": Vector((0, -128, 0.0)), "square": Vector((0, -30, 10.0)),
             "spire": Vector((0, -3.0, 70.0))}
    cams = {"aerial": [(0, (60, -330, 90), (78, 0, 10))], "wall": [(0, (math.cos(ew) * 129, math.sin(ew) * 129, 15.7), (88, 0, math.degrees(ew + math.pi / 2)))]}
    return {"marks": marks, "cams": cams}


# ------------------------------------------------------------------ Poly Haven assets (fetched on the Mac by get_ph.py)
import os
_groups = {}


def have(asset):
    return os.path.isdir(os.path.join(C.PH, asset))


def ph_model(asset, loc, rot_z=0.0, scale=1.0, fallback=None):
    """Place a Poly Haven model (all its meshes) as a linked collection instance. If the asset is not on this machine
    (the cloud can't download them), call `fallback(loc, rot_z, scale)` instead, or place nothing."""
    path = os.path.join(C.PH, asset, asset + "_1k.gltf")
    if not os.path.exists(path):
        return fallback(loc, rot_z, scale) if fallback else None
    if asset not in _groups:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=path)
        new = [o for o in bpy.data.objects if o not in before]
        col = bpy.data.collections.new("ph_" + asset)
        for o in new:
            for c in list(o.users_collection):
                c.objects.unlink(o)
            col.objects.link(o)
        _groups[asset] = col
    e = bpy.data.objects.new(asset, None); C.sc.collection.objects.link(e)
    e.instance_type = "COLLECTION"; e.instance_collection = _groups[asset]
    e.location = loc; e.rotation_euler = (0, 0, rot_z); e.scale = (scale,) * 3
    return e


def tex(name, asset, scale, tint=(1, 1, 1), bump=0.6, fallback="ground"):
    """A Poly Haven texture set if present, else one of the shared palette materials."""
    if have(asset):
        return C.pbr(name, asset, scale, tint, bump)
    return C.M(fallback)


def sky(hdri, strength=1.0, density=0.002, fog=(0.6, 0.62, 0.75), colour=(0.03, 0.035, 0.06)):
    """World light from a Poly Haven HDRI (falls back to the cloudy one in ph/) plus a thin fog."""
    C.world(density=density, sky=0.0, colour=colour)
    w = C.sc.world; nt = w.node_tree; bg = nt.nodes["Background"]
    path = os.path.join(C.PH, hdri, hdri + "_1k.hdr")
    if not os.path.exists(path):   # the daylight fallback is far brighter than the night skies it stands in for
        path = os.path.join(C.PH, "fouriesburg_mountain_cloudy", "fouriesburg_mountain_cloudy_1k.hdr")
        strength *= 0.12 if any(k in hdri for k in ("night", "moon", "golf")) else 0.6
    env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(path, check_existing=True)
    nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = strength
    vol = nt.nodes.get("Principled Volume")
    if vol:
        vol.inputs["Color"].default_value = (*fog, 1)
    bounded_fog()
    return w


def rock(loc, rot_z=0.0, scale=1.0, mat=None):
    """A rock: a Poly Haven boulder when present, else a displaced ico-sphere."""
    def fb(l, r, s):
        bpy.ops.mesh.primitive_ico_sphere_add(radius=1.0, subdivisions=4, location=l)
        o = bpy.context.object; o.name = "rock"; o.scale = (s * 1.3, s, s * 0.8); o.rotation_euler.z = r
        tx = bpy.data.textures.new("rock_n", "CLOUDS"); tx.noise_scale = 0.6
        d = o.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = 0.5
        o.data.materials.append(mat or C.M("rock")); bpy.ops.object.shade_smooth()
        return o
    return ph_model(random.choice(["namaqualand_boulder_02", "namaqualand_boulder_03", "boulder_01"]), loc, rot_z, scale, fb)


def tree(loc, rot_z=0.0, scale=1.0, kind="pine", dead=False, mat=None):
    """A tree: a Poly Haven one when present, else a procedural trunk with cone or blob crowns."""
    asset = {"pine": "fir_tree_01", "broad": "island_tree_02", "small": "tree_small_02"}[kind] if not dead else "dead_tree_trunk_02"
    def fb(l, r, s):
        TR = C.mat("trunk", (0.06, 0.045, 0.03), 0.9)
        bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=0.35 * s, radius2=0.12 * s, depth=8 * s, location=(l[0], l[1], l[2] + 4 * s))
        t = bpy.context.object; t.data.materials.append(TR)
        if dead:
            return t
        LEAF = C.mat("needles" if kind == "pine" else "leaves", (0.02, 0.06, 0.025) if kind == "pine" else (0.05, 0.09, 0.03), 0.85)
        for k in range(5 if kind == "pine" else 3):
            if kind == "pine":
                bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=(2.4 - k * 0.4) * s, depth=2.6 * s, location=(l[0], l[1], l[2] + (3 + k * 1.3) * s))
            else:
                bpy.ops.mesh.primitive_ico_sphere_add(radius=2.2 * s, subdivisions=3, location=(l[0] + random.uniform(-1, 1) * s, l[1] + random.uniform(-1, 1) * s, l[2] + (7 + k) * s))
            c = bpy.context.object; c.data.materials.append(LEAF)
            c.parent = t; c.location = c.location - t.location   # crowns ride on the trunk (walking trees)
            tx = bpy.data.textures.new("crown", "CLOUDS"); tx.noise_scale = 0.4
            d = c.modifiers.new("d", "DISPLACE"); d.texture = tx; d.strength = 0.6 * s
        return t
    return ph_model(asset, loc, rot_z, scale, fb)


# ------------------------------------------------------------------ the other lands
def flat_stage(h, r0=9.0, r1=19.0):
    """Wrap a height function so a stage of radius r0 around the origin is flat (z = 0)."""
    def g(x, y):
        k = min(1.0, max(0.0, (math.hypot(x, y) - r0) / (r1 - r0)))
        return h(x, y) * k * k * (3 - 2 * k)
    return g


def earth(seed=5):
    """Grundhallow and the Canyon Switchbacks: a red-rock canyon by torchlight, cliff cities cut in terraces, giant
    stone faces of old kings carved in the far wall."""
    R = random.Random(seed)
    RED = tex("red_rock", "aerial_rocks_02", 0.08, (0.9, 0.5, 0.35), 0.8, "rock")
    def h(x, y):
        wall = max(0.0, abs(x) - 14) ** 1.25 * 1.6 + max(0.0, y - 70) ** 1.3 * 2.0   # walls either side of a 28 m floor and at the far end
        return terraces(wall + fbm(x, y, 0.03, 4, seed) * 3, 4.5, 0.6) + fbm(x, y, 0.08, 3, seed + 1) * 0.6
    heightfield("canyon", 200, 220, flat_stage(h, 8, 14), RED)
    for i in range(3):   # the faces of the old kings in the far wall
        bpy.ops.mesh.primitive_uv_sphere_add(radius=9, location=(-24 + i * 24, 78, 24))
        f = bpy.context.object; f.name = "king_face"; f.scale = (0.75, 0.35, 1.1); f.data.materials.append(RED)
        C.rough_up(f, 0.6, 1.5, subdiv=3)
    TORCH = C.M("fire")
    for i in range(18):   # cliff-city windows and torches on the terraces
        side = 1 if i % 2 else -1; y = R.uniform(-20, 80); x = side * R.uniform(17, 30); z = h(x, y)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(x - side * 0.5, y, z + 1.2)); w = bpy.context.object
        w.scale = (0.2, 0.8, 1.2); w.data.materials.append(C.mat("cliff_window", (1, 0.6, 0.3), 0.5, emit=(1.0, 0.55, 0.2), strength=8))
        C.light("POINT", (x - side * 1.5, y, z + 2), (0, 0, 0), 300, (1.0, 0.55, 0.2), 0.3, "torch")
    for i in range(10):
        rock((R.uniform(-12, 12), R.uniform(10, 60), 0), R.uniform(0, 6.3), R.uniform(0.6, 1.6), RED)
    sky("satara_night", 0.4, 0.004, (0.7, 0.5, 0.45), (0.02, 0.012, 0.01))
    C.moon(4.0, rot=(40, 0, 160))
    C.light("AREA", (2, -4, 9), (20, 0, 10), 1500, (1.0, 0.6, 0.3), 8, "stage_torchlight")   # torchlight pooled on the stage
    return {"marks": {"hero": Vector((0, 0, 0))},
            "cams": {"wide": [(0, (5, -16, 4), (82, 0, 16))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}}


def storm(seed=8, lightning=True):
    """Aurvanis and Galeback Ridge: the open steppe under a storm sky, wind-bent grass, round Galeborn tents."""
    R = random.Random(seed)
    GR = tex("steppe", "aerial_grass_rock", 0.06, (0.7, 0.75, 0.6), 0.5, "ground")
    h = lambda x, y: fbm(x, y, 0.012, 4, seed) * 8 + max(0.0, y - 40) * 0.15
    heightfield("steppe", 400, 200, flat_stage(h), GR)
    FELT = W.H.robe_cloth("tent_felt", (0.45, 0.42, 0.36), patches=0.2)
    for i in range(9):
        x, y = R.uniform(-40, 40), R.uniform(15, 70)
        z = flat_stage(h)(x, y)
        bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=3.2, depth=2.4, location=(x, y, z + 1.2)); bpy.context.object.data.materials.append(FELT)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=3.4, depth=2.0, location=(x, y, z + 3.4)); bpy.context.object.data.materials.append(FELT)
    for i in range(40):
        p = (R.uniform(-60, 60), R.uniform(8, 120)); rock((p[0], p[1], flat_stage(h)(*p)), R.uniform(0, 6.3), R.uniform(0.3, 1.0))
    sky("kloofendal_48d_partly_cloudy_puresky", 0.25, 0.003, (0.55, 0.6, 0.7), (0.05, 0.06, 0.08))
    C.light("SUN", (0, 0, 60), (60, 0, 30), 1.2, (0.7, 0.78, 0.95), name="storm_light")
    if lightning:   # a far strike that flashes on a few frames
        L = C.light("POINT", (-30, 160, 60), (0, 0, 0), 0, (0.8, 0.85, 1.0), 2, "lightning")
        for f, e in ((1, 0), (30, 0), (31, 4e6), (33, 0), (35, 2e6), (37, 0)):
            L.data.energy = e; L.data.keyframe_insert("energy", frame=f)
    return {"marks": {"hero": Vector((0, 0, 0))},
            "cams": {"wide": [(0, (6, -18, 3.5), (84, 0, 18))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}}


def nature(seed=12):
    """Elderhollow and the Rootway: a forest of vast old trees, roots like walls, moss and ferns, shafts of light."""
    R = random.Random(seed)
    FL = tex("forest_floor", "brown_mud_leaves_01", 0.15, (0.6, 0.6, 0.5), 0.6, "mud")
    h = lambda x, y: fbm(x, y, 0.03, 4, seed) * 2.5
    heightfield("forest_floor", 200, 160, flat_stage(h, 6, 12), FL)
    BARK = W.bark("giant_bark", moss=0.8)
    for i in range(16):
        a = R.uniform(0, 2 * math.pi); r = R.uniform(10, 70)
        x, y = math.cos(a) * r, abs(math.sin(a)) * r + 4
        rr = R.uniform(1.6, 3.5)
        bpy.ops.mesh.primitive_cone_add(vertices=24, radius1=rr * 1.6, radius2=rr * 0.8, depth=60, location=(x, y, 28))
        t = bpy.context.object; t.data.materials.append(BARK); C.rough_up(t, 0.4, 2.0, subdiv=3)
    for i in range(30):
        tree((R.uniform(-60, 60), R.uniform(15, 100), 0), R.uniform(0, 6.3), R.uniform(0.8, 1.3), "pine")
    sky("lilienstein", 0.4, 0.008, (0.6, 0.75, 0.6), (0.02, 0.03, 0.02))
    C.light("SUN", (0, 0, 60), (35, 10, 200), 6.0, (1.0, 0.92, 0.75), name="shafts")
    return {"marks": {"hero": Vector((0, 0, 0))},
            "cams": {"wide": [(0, (5, -15, 3), (84, 0, 16))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}}


def water(seed=14, frozen=True):
    """Pearlhaven and the Saltmarsh: a frozen sea under the moon, the ice tower, harbour lights far off."""
    R = random.Random(seed)
    ICE = C.mat("sea_ice", (0.75, 0.85, 0.9), 0.15) if frozen else W.sea_glass("open_sea", (0.05, 0.15, 0.18))
    if have("snow_02"):
        ICE = C.pbr("sea_ice", "snow_02", 0.1, (0.8, 0.9, 1.0), 0.3)
    h = lambda x, y: fbm(x, y, 0.05, 3, seed) * 0.25
    heightfield("sea", 500, 160, h, ICE)
    for i in range(25):   # pressure ridges and broken floes
        bpy.ops.mesh.primitive_cube_add(size=1, location=(R.uniform(-80, 80), R.uniform(10, 150), 0.2))
        f = bpy.context.object; f.scale = (R.uniform(2, 8), R.uniform(0.4, 1.5), R.uniform(0.3, 1.2)); f.rotation_euler = (R.uniform(-0.3, 0.3), R.uniform(-0.3, 0.3), R.uniform(0, 3.1))
        f.data.materials.append(W.sea_glass("floe_glass", (0.7, 0.9, 0.95)))
    bpy.ops.mesh.primitive_cylinder_add(vertices=8, radius=6, depth=50, location=(-30, 90, 25))
    tw = bpy.context.object; tw.name = "ice_tower"; tw.data.materials.append(W.sea_glass("tower_ice", (0.75, 0.92, 0.97)))
    C.light("POINT", (-30, 90, 40), (0, 0, 0), 2e4, (0.5, 0.85, 1.0), 4, "tower_glow")
    LIT = C.mat("harbour_light", (1, 0.7, 0.35), 0.4, emit=(1.0, 0.65, 0.3), strength=10)
    for i in range(60):
        bpy.ops.mesh.primitive_cube_add(size=0.6, location=(R.uniform(20, 120), R.uniform(180, 220), R.uniform(1, 12))); bpy.context.object.data.materials.append(LIT)
    sky("moonless_golf", 0.5, 0.002, (0.6, 0.7, 0.85), (0.01, 0.015, 0.03))
    C.moon(3.0, rot=(30, 0, 160))
    return {"marks": {"hero": Vector((0, 0, 0))},
            "cams": {"wide": [(0, (5, -16, 3.0), (84, 0, 16))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}}


def void(seed=21):
    """Lamplight and the Fractured Steps: broken stone stairs hanging in a violet dark, Veilwalker lanterns."""
    R = random.Random(seed)
    ST = tex("void_stone", "medieval_blocks_03", 0.2, (0.45, 0.42, 0.5), 0.7, "rock")
    C.box("landing", (0, 0, -0.5), (16, 16, 1), ST, bevel=0.2)
    VIO = C.mat("void_lantern", (0.8, 0.6, 1.0), 0.3, emit=(0.7, 0.45, 1.0), strength=4)
    for i in range(40):   # the fractured steps: blocks drifting in the dark
        x, y, z = R.uniform(-50, 50), R.uniform(10, 120), R.uniform(-15, 35)
        b = C.box("step", (x, y, z), (R.uniform(2, 7), R.uniform(2, 6), R.uniform(0.8, 3)), ST, bevel=0.1)
        b.rotation_euler = (R.uniform(-0.2, 0.2), R.uniform(-0.2, 0.2), R.uniform(0, 3.1))
        if R.random() < 0.35:
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(x, y, z + 2)); bpy.context.object.data.materials.append(VIO)
            C.light("POINT", (x, y, z + 2.3), (0, 0, 0), 600, (0.7, 0.45, 1.0), 0.3, "void_lantern")
    VIO_NEAR = C.mat("void_lantern_near", (0.8, 0.6, 1.0), 0.3, emit=(0.7, 0.45, 1.0), strength=1.2)
    for sx in (-1, 1):   # two lanterns on posts at the back of the landing
        bpy.ops.mesh.primitive_cylinder_add(radius=0.05, depth=2.4, location=(sx * 5, 7, 1.2)); bpy.context.object.data.materials.append(C.M("iron"))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.18, location=(sx * 5, 7, 2.5)); bpy.context.object.data.materials.append(VIO_NEAR)
        C.light("POINT", (sx * 5, 6.7, 2.5), (0, 0, 0), 300, (0.7, 0.45, 1.0), 0.3, "void_lantern")
    C.world(density=0.006, sky=0.0, colour=(0.012, 0.006, 0.025))
    vol = C.sc.world.node_tree.nodes.get("Principled Volume")
    if vol:
        vol.inputs["Color"].default_value = (0.65, 0.5, 0.85, 1)
    bounded_fog(300, 120, -60)
    return {"marks": {"hero": Vector((0, 0, 0))},
            "cams": {"wide": [(0, (5, -15, 3.5), (82, 0, 16))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}}


def hollow(seed=31):
    """The Hollow under the Rift: a stone sky, grey fires, and on a broken plain the black fortress of Nhal Vorath,
    built of old ruined walls, towers and gates."""
    R = random.Random(seed)
    G = tex("hollow_ground", "aerial_rocks_02", 0.08, (0.35, 0.35, 0.36), 0.8, "ground")
    h = lambda x, y: fbm(x, y, 0.02, 5, seed) * 5 + max(0.0, y - 60) * 0.1
    heightfield("hollow_plain", 500, 200, flat_stage(h), G)
    bpy.ops.mesh.primitive_plane_add(size=1200, location=(0, 0, 160)); roof = bpy.context.object; roof.name = "stone_sky"
    roof.data.materials.append(C.M("rock")); C.rough_up(roof, 18, 40, subdiv=6); roof.rotation_euler.x = math.pi
    BLACK = C.mat("fortress_black", (0.015, 0.015, 0.017), 0.6)
    fx, fy = 0, 220
    for i in range(14):   # towers of mismatched ruins piled into one fortress
        x = fx + R.uniform(-70, 70); y = fy + R.uniform(-20, 40); hh = R.uniform(30, 90)
        t = C.box("fortress", (x, y, hh / 2), (R.uniform(8, 20), R.uniform(8, 20), hh), BLACK, bevel=0.3)
        C.rough_up(t, 0.8, 3.0, subdiv=3)
    C.box("fortress_wall", (fx, fy - 25, 18), (160, 8, 36), BLACK)
    C.box("fortress_gate", (fx, fy - 29.2, 12), (16, 0.5, 24), C.mat("gate_void", (0, 0, 0), 1.0))
    GF = C.mat("grey_fire", (0.8, 0.8, 0.85), 0.5, emit=(0.75, 0.77, 0.82), strength=12)
    for i in range(14):   # grey fires on the plain
        x, y = R.uniform(-80, 80), R.uniform(20, 180)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=0.8, location=(x, y, flat_stage(h)(x, y) + 0.6)); bpy.context.object.data.materials.append(GF)
        C.light("POINT", (x, y, flat_stage(h)(x, y) + 2), (0, 0, 0), 2500, (0.75, 0.77, 0.82), 1, "grey_fire")
    C.world(density=0.006, sky=0.0, colour=(0.05, 0.05, 0.055))
    C.light("AREA", (0, 60, 150), (0, 0, 0), 2e5, (0.7, 0.72, 0.78), 200, "stone_sky_glow")   # dull light off the stone sky
    bounded_fog(800, 150)
    return {"marks": {"hero": Vector((0, 0, 0)), "gate": Vector((fx, fy - 32, 0))},
            "cams": {"wide": [(0, (8, -20, 5), (82, 0, 12))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}}


def rift():
    """The Rift and the Black Gate: the canyon from the trailer (cine3d.canyon)."""
    C.canyon()
    C.world(density=0.0015, sky=0.25)
    C.moon(9.0, rot=(28, -35, 120))
    C.light("AREA", (25, -25, 200), (-45, 0, -10), 400000, (0.55, 0.62, 0.85), 80, "wash")   # as the trailer's s01
    return {"marks": {"hero": Vector((0, 0, 0))}, "cams": {"wide": [(0, (5, -16, 3), (84, 0, 16))]}}


# ------------------------------------------------------------------ halls (interiors)
def heartstone(loc, size=0.35, energy=300, name="heartstone"):
    """The Heartstone: a six-coloured crystal (Vael-Orrun's crown, broken into a key), slowly turning."""
    bpy.ops.mesh.primitive_ico_sphere_add(radius=size, subdivisions=1, location=loc)
    o = bpy.context.object; o.name = name; o.scale = (0.7, 0.7, 1.3)
    m, nt, out = W._blank(name + "_glass")
    gc = W._n(nt, "ShaderNodeTexCoord"); sep = W._n(nt, "ShaderNodeSeparateXYZ")
    nt.links.new(gc.outputs["Object"], sep.inputs[0])
    ang = W._n(nt, "ShaderNodeMath", _operation="ARCTAN2"); nt.links.new(sep.outputs[1], ang.inputs[0]); nt.links.new(sep.outputs[0], ang.inputs[1])
    rn = nt.nodes.new("ShaderNodeValToRGB"); els = rn.color_ramp.elements
    cols = [(1, 0.3, 0.08), (0.75, 0.85, 1), (0.35, 1, 0.35), (0.3, 0.85, 1), (1, 0.7, 0.3), (0.7, 0.45, 1), (1, 0.3, 0.08)]
    els[0].position, els[0].color = 0.0, (*cols[0], 1); els[1].position, els[1].color = 1.0, (*cols[-1], 1)
    for k in range(1, 6):
        e = els.new(k / 6); e.color = (*cols[k], 1)
    norm = nt.nodes.new("ShaderNodeMapRange"); norm.inputs[1].default_value = -math.pi; norm.inputs[2].default_value = math.pi
    nt.links.new(ang.outputs[0], norm.inputs[0]); nt.links.new(norm.outputs[0], rn.inputs[0])
    ramp = rn
    em = W._n(nt, "ShaderNodeEmission"); em.inputs["Strength"].default_value = 12
    nt.links.new(ramp.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], out.inputs[0])
    o.data.materials.append(m)
    o.rotation_euler.z = 0; o.keyframe_insert("rotation_euler", index=2, frame=1)
    o.rotation_euler.z = 2 * math.pi; o.keyframe_insert("rotation_euler", index=2, frame=C.sc.frame_end + 480)
    C.light("POINT", tuple(Vector(loc) + Vector((0, 0, 0.2))), (0, 0, 0), energy, (1.0, 0.85, 0.75), 0.3, name + "_light")
    return o


def hall(ruined=False, heart=True, dawn=False, seed=17):
    """An interior: the Hall of the Ring in Solenne (white stone, a round dais with the Heartstone, braziers), or with
    `ruined` the black throne hall of Nhal Vorath (broken columns, grey fires, a stone sky through the roof).
    Marks: 'hero' (the floor in front of the dais), 'dais' (its top), 'door' (the far side, toward the camera)."""
    R = random.Random(seed)
    FLOOR = tex("hall_floor", "castle_brick_07" if not ruined else "aerial_rocks_02", 0.25,
                (0.75, 0.72, 0.68) if not ruined else (0.2, 0.2, 0.21), 0.5, "rock")
    STONE = C.M("white_stone") if not ruined else W.basalt("throne_stone", (0.02, 0.02, 0.022), (0.3, 0.3, 0.32), glow=0.0, core_glow=0.0, grey=True)
    bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=18, depth=0.4, location=(0, 0, -0.2)); bpy.context.object.data.materials.append(FLOOR)
    for k in range(16):   # the ring of columns
        a = 2 * math.pi * k / 16; h = 11 if not ruined else R.uniform(3, 11)
        if ruined and R.random() < 0.25:
            continue
        bpy.ops.mesh.primitive_cylinder_add(vertices=20, radius=0.7, depth=h, location=(math.cos(a) * 14, math.sin(a) * 14 + 4, h / 2))
        c = bpy.context.object; c.data.materials.append(STONE)
        if ruined:
            C.rough_up(c, 0.15, 1.0, subdiv=3)
    if not ruined:   # dome and wall
        bpy.ops.mesh.primitive_uv_sphere_add(radius=16, segments=48, ring_count=24, location=(0, 4, 11))
        d = bpy.context.object; d.scale = (1, 1, 0.55); d.data.materials.append(STONE)
        bm = d.data
        for p in bm.polygons:
            p.use_smooth = True
        bpy.ops.mesh.primitive_cylinder_add(vertices=96, radius=17, depth=11, location=(0, 4, 5.5), end_fill_type="NOTHING"); w = bpy.context.object
        w.data.materials.append(STONE); w.modifiers.new("s", "SOLIDIFY").thickness = 0.6
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=3.0, depth=0.9, location=(0, 6, 0.45)); bpy.context.object.data.materials.append(STONE)
    if heart and not ruined:
        heartstone((0, 6, 1.6))
    fire = (1.0, 0.6, 0.25) if not ruined else (0.75, 0.77, 0.82)
    for k in range(6):
        a = math.pi / 2 + 2 * math.pi * (k + 0.5) / 6
        x, y = math.cos(a) * 9, math.sin(a) * 9 + 4
        bpy.ops.mesh.primitive_cylinder_add(radius=0.35, depth=1.2, location=(x, y, 0.6)); bpy.context.object.data.materials.append(C.M("iron"))
        C.light("POINT", (x, y, 1.6), (0, 0, 0), 500, fire, 0.4, "brazier")
    if dawn:   # a beam of white light down through the roof
        C.light("SPOT", (0, 6, 30), (0, 0, 0), 2e5, (1.0, 0.97, 0.9), 0.5, "dawn_beam").data.spot_size = 0.25
    C.world(density=0.02, sky=0.0, colour=(0.03, 0.03, 0.035))
    bounded_fog(60, 30, -2)
    if ruined:
        C.light("AREA", (0, 4, 40), (0, 0, 0), 2e4, (0.7, 0.72, 0.78), 30, "stone_sky_glow")
    return {"marks": {"hero": Vector((0, 0, 0)), "dais": Vector((0, 6, 0.9)), "door": Vector((0, -12, 0))},
            "cams": {"wide": [(0, (0, -15, 3.5), (84, 0, 0))], "close": [(0, (2.5, -6.5, 1.8), (88, 0, 20))]}}
