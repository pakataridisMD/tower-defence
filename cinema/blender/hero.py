"""Our own 3D heroes, built from code in Blender.

A hero reuses the CC0 KayKit rig (bone names, axes and its 76 animations) but with heroic proportions: the bones are
moved, never turned, so every animation's bone rotations still read right. On it we grow a smooth body with the Skin
modifier, weight it to the bones, and hang rigid armour, cloth and props on single bones like game armour.

    import hero
    rig = hero.build("tamsin", location, rot_z)      # then cine3d.play(rig, "Walking_A") like any stand-in
"""
import bpy, bmesh, math, os, random
from mathutils import Vector, Matrix
import cine3d as C

H = 2.3  # hero height in scene units (the stand-ins are about 2.4 including their big heads)


# ------------------------------------------------------------------ skeleton
def proportions(height=H, build=1.0, shoulders=1.0, hips=1.0, legs=1.0):
    """Joint positions (x, y, z) for a heroic figure, `height` tall. build/shoulders/hips scale widths; legs scales
    leg length against the torso."""
    h = height
    leg = 0.47 * legs
    j = {}
    j["ground"] = 0.0
    j["hip_z"] = h * leg
    j["knee_z"] = h * leg * 0.53
    j["ankle_z"] = h * 0.045
    j["pelvis_z"] = h * (leg + 0.02)
    j["waist_z"] = h * (leg + 0.12)
    j["chest_z"] = h * (leg + 0.24)
    j["shoulder_z"] = h * 0.815
    j["neck_z"] = h * 0.845
    j["head_top"] = h
    j["leg_x"] = h * 0.052 * hips
    j["sh_x"] = h * 0.105 * shoulders
    j["elbow_x"] = j["sh_x"] + h * 0.185
    j["wrist_x"] = j["elbow_x"] + h * 0.16
    j["hand_x"] = j["wrist_x"] + h * 0.035
    j["finger_x"] = j["hand_x"] + h * 0.065
    j["build"] = build
    return j


def reshape(rig, j):
    """Move the KayKit rig's bones to the hero's joints, keeping each bone's direction and roll."""
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones

    def put(name, head, tail):
        b = eb.get(name)
        if b is None:
            return
        roll = b.roll
        b.head = Vector(head); b.tail = Vector(tail); b.roll = roll

    z = j
    put("root", (0, 0, 0), (0, 0, z["hip_z"] * 0.6))
    put("hips", (0, 0, z["hip_z"] * 0.98), (0, 0, z["waist_z"]))
    put("spine", (0, 0, z["waist_z"]), (0, 0, z["chest_z"]))
    put("chest", (0, 0, z["chest_z"]), (0, 0, z["neck_z"]))
    put("head", (0, 0, z["neck_z"]), (0, 0, z["head_top"]))
    for s, side in ((".l", 1), (".r", -1)):
        sz = z["shoulder_z"]
        put("upperarm" + s, (side * z["sh_x"], 0, sz), (side * z["elbow_x"], 0.01, sz))
        put("lowerarm" + s, (side * z["elbow_x"], 0.01, sz), (side * z["wrist_x"], 0, sz))
        put("wrist" + s, (side * z["wrist_x"], 0, sz), (side * z["hand_x"], 0, sz))
        put("hand" + s, (side * z["hand_x"], 0, sz), (side * z["finger_x"], 0, sz))
        put("handslot" + s, (side * (z["finger_x"] - 0.02), 0, sz - 0.05), (side * (z["finger_x"] - 0.02), -0.11, sz - 0.05))
        lx = side * z["leg_x"]
        put("upperleg" + s, (lx, 0, z["hip_z"]), (lx, -0.01, z["knee_z"]))
        put("lowerleg" + s, (lx, -0.01, z["knee_z"]), (lx, 0.02, z["ankle_z"] + 0.1))
        put("foot" + s, (lx, 0.02, z["ankle_z"] + 0.1), (lx, -0.12, 0.03))
        put("toes" + s, (lx, -0.12, 0.03), (lx, -0.27, 0.03))
    bpy.ops.object.mode_set(mode="OBJECT")


def base_rig():
    """Import the KayKit Knight for its rig and animations; drop its meshes."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=C.KK + "Knight.glb")
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        if o is rig:
            continue
        if o.name.split(".")[0] in ("1H_Sword", "1H_Sword_Offhand"):
            # Keep the stand-in's swords as invisible grips: anything long held in a hand rides along their Z.
            o.hide_render = o.hide_viewport = True
            rig["grip" + (".l" if "Offhand" in o.name else ".r")] = o.name
            continue
        bpy.data.objects.remove(o, do_unlink=True)
    rig.rotation_mode = "XYZ"
    return rig


def hold(o, rig, side=".r", along=0.0):
    """Put `o` (built centred on the origin, long axis on Z) into a hand's grip, shifted `along` its length."""
    g = bpy.data.objects[rig["grip" + side]]
    o.parent = g; o.matrix_parent_inverse = Matrix.Identity(4)
    o.location = (0, 0, along); o.rotation_euler = (0, 0, 0); o.scale = (1, 1, 1)
    o["hold_side"] = side; o["hold_along"] = along
    return o


def stand_up(parts, rig):
    """Turn held props upright for the rest pose of the current action: a lantern pole or staff reads as carried
    straight up, then swings with the hand from there instead of pointing where the stand-in's sword pointed."""
    bpy.context.view_layer.update()
    for o in parts:
        if "hold_side" not in o:
            continue
        side, along = o["hold_side"], o["hold_along"]
        g = bpy.data.objects[rig["grip" + side]]
        p = g.matrix_world.translation
        dx = o.get("hold_dx", 0.0) * (-1 if side == ".r" else 1)
        off = rig.matrix_world.to_3x3().normalized() @ Vector((dx, 0, 0))
        o.matrix_world = Matrix.Translation(p + off + Vector((0, 0, along))) @ rig.matrix_world.to_3x3().normalized().to_4x4()


# ------------------------------------------------------------------ body
def skin_body(j, name="body", radii=None):
    """A smooth body from a joint graph, using the Skin modifier, then subdivided and applied."""
    b = j["build"]
    r = {"pelvis": 0.115, "waist": 0.10, "chest": 0.125, "neck": 0.045, "shoulder": 0.055, "elbow": 0.038,
         "wrist": 0.028, "hand": 0.032, "hip": 0.07, "knee": 0.048, "ankle": 0.034, "toe": 0.03}
    if radii:
        r.update(radii)
    verts, edges, rad = [], [], []

    def v(p, rr):
        verts.append(Vector(p)); rad.append(rr * b * 1.9)
        return len(verts) - 1
    pel = v((0, 0, j["pelvis_z"]), r["pelvis"])
    wai = v((0, 0.005, j["waist_z"]), r["waist"])
    che = v((0, -0.01, j["chest_z"] + 0.06), r["chest"])
    nec = v((0, 0, j["neck_z"] + 0.03), r["neck"])
    edges += [(pel, wai), (wai, che), (che, nec)]
    for side in (1, -1):
        sh = v((side * j["sh_x"], 0, j["shoulder_z"]), r["shoulder"])
        el = v((side * j["elbow_x"], 0.01, j["shoulder_z"]), r["elbow"])
        wr = v((side * j["wrist_x"], 0, j["shoulder_z"]), r["wrist"])
        ha = v((side * (j["finger_x"] - 0.03), 0, j["shoulder_z"]), r["hand"])
        edges += [(che, sh), (sh, el), (el, wr), (wr, ha)]
        hp = v((side * j["leg_x"], 0, j["hip_z"]), r["hip"])
        kn = v((side * j["leg_x"], -0.01, j["knee_z"]), r["knee"])
        an = v((side * j["leg_x"], 0.02, j["ankle_z"] + 0.06), r["ankle"])
        to = v((side * j["leg_x"], -0.17, 0.035), r["toe"])
        edges += [(pel, hp), (hp, kn), (kn, an), (an, to)]
    me = bpy.data.meshes.new(name); me.from_pydata(verts, edges, [])
    o = bpy.data.objects.new(name, me); C.sc.collection.objects.link(o)
    sk = o.modifiers.new("skin", "SKIN"); sk.use_smooth_shade = True; sk.branch_smoothing = 0.6
    for i, sv in enumerate(o.data.skin_vertices[0].data):
        sv.radius = (rad[i], rad[i])
    o.data.skin_vertices[0].data[pel].use_root = True
    o.modifiers.new("sub", "SUBSURF").levels = 2
    bpy.context.view_layer.objects.active = o
    for m in list(o.modifiers):
        bpy.ops.object.modifier_apply(modifier=m.name)
    return o


def head_mesh(j, name="head", jaw=1.0, nose=1.0, broken_nose=False):
    """A stylised head: a sphere pushed into a skull, jaw, cheekbones, brow and nose."""
    hz = j["neck_z"]; top = j["head_top"]
    hh = (top - hz) * 1.22  # head height
    cz = top - hh * 0.5
    rx, ry, rz = hh * 0.34, hh * 0.39, hh * 0.5
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=32, radius=1, location=(0, 0, cz))
    o = bpy.context.object; o.name = name
    me = o.data
    for vtx in me.vertices:
        x, y, z = vtx.co
        # skull shape: wider at the back-top, narrow chin
        zz = z
        w = 1.0 - max(0.0, -zz) * 0.38 * jaw          # narrower towards the jaw
        x *= rx * w
        y *= ry * (1.0 - max(0.0, -zz) * 0.25)
        if y < 0:  # face side (towards -Y): flatter
            y *= 0.82
        z *= rz
        # brow ridge
        if -0.1 < zz < 0.25 and y < -ry * 0.55:
            y -= hh * 0.02 * (1 - abs(zz - 0.08) / 0.17)
        # nose: a ridge on the centre line
        if abs(x) < rx * 0.16 and -0.35 < zz < 0.08 and y < -ry * 0.6:
            k = (1 - abs(x) / (rx * 0.16)) * (1 - abs(zz + 0.12) / 0.24)
            y -= hh * 0.07 * nose * max(k, 0)
            if broken_nose and zz < -0.05:
                x += hh * 0.012 * max(k, 0)
        # cheekbones
        if 0.4 * rx < abs(x) < rx and -0.25 < zz < 0.0 and y < 0:
            y -= hh * 0.012
        vtx.co = Vector((x, y, z))
    o.location = (0, 0, cz)
    bpy.ops.object.shade_smooth()
    o.modifiers.new("sub", "SUBSURF").levels = 1
    # eyes
    eyes = []
    for side in (-1, 1):
        ex, ey, ez = side * rx * 0.36, -ry * 0.78, cz + rz * 0.05
        bpy.ops.mesh.primitive_uv_sphere_add(radius=hh * 0.06, location=(ex, ey, ez))
        e = bpy.context.object; e.name = "eye"; e.scale = (1, 0.6, 0.75); bpy.ops.object.shade_smooth(); eyes.append(e)
        e.data.materials.append(C.mat("sclera", (0.85, 0.82, 0.78), 0.2))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=hh * 0.034, location=(ex, ey - hh * 0.03, ez))
        iris = bpy.context.object; iris.name = "iris"; iris.scale = (1, 0.5, 1); bpy.ops.object.shade_smooth(); eyes.append(iris)
        iris.data.materials.append(C.mat("iris", (0.08, 0.16, 0.12), 0.1))
        bpy.ops.mesh.primitive_cube_add(location=(ex, ey - hh * 0.035, ez + hh * 0.085))
        br = bpy.context.object; br.name = "brow"; br.scale = (hh * 0.075, hh * 0.02, hh * 0.014)
        br.rotation_euler.y = side * -0.18; eyes.append(br)
        br.data.materials.append(C.mat("brow", (0.35, 0.07, 0.03), 0.8))
    bpy.ops.mesh.primitive_cube_add(location=(0, -ry * 0.86, cz - rz * 0.40))
    mo = bpy.context.object; mo.name = "mouth"; mo.scale = (hh * 0.07, hh * 0.012, hh * 0.008); eyes.append(mo)
    mo.data.materials.append(C.mat("lips", (0.35, 0.12, 0.1), 0.6))
    bpy.ops.mesh.primitive_cylinder_add(radius=hh * 0.17, depth=hh * 0.45, location=(0, ry * 0.05, cz - rz * 0.95))
    nk = bpy.context.object; nk.name = "neck"; bpy.ops.object.shade_smooth(); eyes.append(nk)
    return o, eyes, (rx, ry, rz, cz)


def hair_cap(head_dims, name="hair", crop=0.35, colour=(0.45, 0.08, 0.03)):
    """Cropped hair: the upper part of a slightly larger skull, roughened."""
    rx, ry, rz, cz = head_dims
    bpy.ops.mesh.primitive_uv_sphere_add(segments=40, ring_count=24, radius=1, location=(0, 0, cz))
    o = bpy.context.object; o.name = name
    bm = bmesh.new(); bm.from_mesh(o.data)
    kill = [v for v in bm.verts if v.co.z < -crop + (0.7 if v.co.y < -0.45 else 0.0)]
    bmesh.ops.delete(bm, geom=kill, context="VERTS"); bm.to_mesh(o.data); bm.free()
    o.scale = (rx * 1.08, ry * 1.07, rz * 1.06)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    sol = o.modifiers.new("thick", "SOLIDIFY"); sol.thickness = 0.015
    tex = bpy.data.textures.new("hairnoise", "CLOUDS"); tex.noise_scale = 0.06; tex.noise_depth = 3
    d = o.modifiers.new("tufts", "DISPLACE"); d.texture = tex; d.strength = 0.045
    bpy.ops.object.shade_smooth()
    o.data.materials.append(C.mat("hair", colour, 0.6))
    return o


# ------------------------------------------------------------------ armour, cloth, props
def plate(name, size, loc, m, bevel=0.02, round_=0.0):
    """A plate: a subdivided box pulled `round_` of the way to an ellipsoid, then given a thin bevelled rim."""
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    s = o.modifiers.new("pre", "SUBSURF"); s.levels = 3; s.subdivision_type = "SIMPLE"
    if round_:
        cast = o.modifiers.new("bulge", "CAST"); cast.factor = round_; cast.cast_type = "SPHERE"
    sm = o.modifiers.new("soft", "SUBSURF"); sm.levels = 1
    o.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return o


def on_bone(o, rig, bone):
    """Parent `o` rigidly to `bone`, keeping its current world placement."""
    b = rig.data.bones[bone]
    o.parent = rig; o.parent_type = "BONE"; o.parent_bone = bone
    # A bone child hangs from the bone's tail; cancel the rest-pose bone matrix so it stays where it was built.
    o.matrix_parent_inverse = (rig.matrix_world @ b.matrix_local @ Matrix.Translation((0, b.length, 0))).inverted()
    return o


def steel(name="steel", dent=0.0):
    m = C.mat(name, (0.55, 0.56, 0.6), 0.32, metal=1.0)
    if dent:
        nt = m.node_tree; b = nt.nodes["Principled BSDF"]
        n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 18
        bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = dent
        nt.links.new(n.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
        r = nt.nodes.new("ShaderNodeMapRange"); r.inputs["To Min"].default_value = 0.24; r.inputs["To Max"].default_value = 0.36
        nt.links.new(n.outputs["Fac"], r.inputs["Value"]); nt.links.new(r.outputs["Result"], b.inputs["Roughness"])
    return m


def quilted(name, rgb):
    """Padded gambeson: dark cloth with stitched quilting lines running down the body."""
    m = cloth(name, rgb, 0.9)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Sheen Weight"].default_value = 0.15
    w = nt.nodes.new("ShaderNodeTexWave"); w.wave_type = "BANDS"; w.bands_direction = "X"
    w.inputs["Scale"].default_value = 35; w.inputs["Distortion"].default_value = 0.5
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.45
    nt.links.new(w.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def cloth(name, rgb, rough=0.85):
    m = C.mat(name, rgb, rough)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Sheen Weight"].default_value = 0.4
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 60
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.15
    nt.links.new(n.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def skin_mat(rgb=(0.8, 0.55, 0.42)):
    m = C.mat("skin", rgb, 0.5)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Subsurface Weight"].default_value = 0.15
    b.inputs["Subsurface Radius"].default_value = (0.4, 0.15, 0.08)
    return m


def weight(body, rig):
    """Skin the body to the deform bones with automatic (heat) weights."""
    for o in bpy.context.selected_objects:
        o.select_set(False)
    body.select_set(True); rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.parent_set(type="ARMATURE_AUTO")
    # keep only the bones that should move the body
    keep = {"hips", "spine", "chest", "head"} | {p + s for p in ("upperarm", "lowerarm", "wrist", "hand", "upperleg", "lowerleg", "foot", "toes") for s in (".l", ".r")}
    for vg in list(body.vertex_groups):
        if vg.name not in keep:
            body.vertex_groups.remove(vg)


# ------------------------------------------------------------------ heroes
def tamsin(rig, j):
    """Tamsin Reed, Captain of the Lanternguard: wiry, short, cropped red hair, broken nose, dented steel half-plate
    over a faded blue tabard with a gold lantern sigil, a long war-lantern on a pole."""
    SK = skin_mat((0.82, 0.58, 0.46))
    ST = steel("steel_dented", dent=0.25)
    BLUE = cloth("tabard_blue", (0.04, 0.07, 0.16))
    LEATHER = C.mat("leather", (0.16, 0.09, 0.05), 0.6)
    GOLD = C.mat("gold", (0.9, 0.62, 0.22), 0.3, metal=1.0)
    body = skin_body(j, radii={"chest": 0.112, "pelvis": 0.108, "shoulder": 0.05})
    body.data.materials.append(cloth("gambeson", (0.09, 0.09, 0.1)))  # padded under-clothes; skin shows on face only
    head, eyes, dims = head_mesh(j, broken_nose=True)
    head.data.materials.append(SK)
    for e in eyes:
        if e.name.startswith("neck"):
            e.data.materials.append(SK)
    hair = hair_cap(dims)
    for o in [head, hair] + eyes:
        on_bone(o, rig, "head")
    sz, cz = j["shoulder_z"], j["chest_z"]
    # breastplate and backplate
    bp = plate("breastplate", (0.5, 0.36, 0.46), (0, -0.01, cz + 0.08), ST, 0.03, 0.55)
    tp = bp.modifiers.new("taper", "SIMPLE_DEFORM"); tp.deform_method = "TAPER"; tp.deform_axis = "Z"; tp.factor = 0.55
    on_bone(bp, rig, "chest")
    bpy.ops.mesh.primitive_torus_add(major_radius=0.13, minor_radius=0.045, location=(0, 0.0, j["neck_z"] + 0.0))
    go = bpy.context.object; go.name = "gorget"; go.scale = (1.15, 1.0, 1.0); go.data.materials.append(ST)
    bpy.ops.object.shade_smooth(); on_bone(go, rig, "chest")
    # tassets: a flared steel skirt from the waist, split front and back by the tabard
    bpy.ops.mesh.primitive_cone_add(vertices=32, radius1=0.3, radius2=0.22, depth=0.2, end_fill_type="NOTHING",
                                    location=(0, 0, j["waist_z"] - 0.1))
    ts = bpy.context.object; ts.name = "tassets"; ts.scale = (1.0, 0.8, 1.0); ts.data.materials.append(ST)
    ts.modifiers.new("thick", "SOLIDIFY").thickness = 0.015
    ts.modifiers.new("sub", "SUBSURF").levels = 1
    bpy.ops.object.shade_smooth(); on_bone(ts, rig, "hips")
    # a short dark cape from the shoulders: the hero silhouette
    bpy.ops.mesh.primitive_plane_add(size=1, location=(0, 0.16, (sz + j["hip_z"]) / 2 - 0.05))
    cp = bpy.context.object; cp.name = "cape"; cp.rotation_euler.x = math.radians(84)
    cp.scale = (0.62, sz - j["hip_z"] + 0.35, 1); bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    cps = cp.modifiers.new("sub", "SUBSURF"); cps.levels = 3; cps.subdivision_type = "SIMPLE"
    ct = cp.modifiers.new("flare", "SIMPLE_DEFORM"); ct.deform_method = "TAPER"; ct.deform_axis = "Z"; ct.factor = -0.6
    cb = cp.modifiers.new("curve", "SIMPLE_DEFORM"); cb.deform_method = "BEND"; cb.deform_axis = "Z"; cb.angle = math.radians(-140)
    tx = bpy.data.textures.new("capefolds", "WOOD"); tx.wood_type = "BANDNOISE"; tx.noise_scale = 0.05; tx.turbulence = 2
    dp = cp.modifiers.new("folds", "DISPLACE"); dp.texture = tx; dp.strength = 0.03; dp.direction = "Y"
    cp.modifiers.new("thick", "SOLIDIFY").thickness = 0.012
    cp.data.materials.append(cloth("cape", (0.05, 0.03, 0.03))); bpy.ops.object.shade_smooth(); on_bone(cp, rig, "chest")
    # pauldrons
    for s, side in ((".l", 1), (".r", -1)):
        pa = plate("pauldron", (0.26, 0.3, 0.2), (side * (j["sh_x"] + 0.05), 0, sz + 0.035), ST, 0.03, 0.8)
        on_bone(pa, rig, "upperarm" + s)
        va = plate("vambrace", (0.2, 0.15, 0.15), (side * (j["elbow_x"] + 0.09), 0.005, sz), ST, 0.02, 0.6)
        on_bone(va, rig, "lowerarm" + s)
        gl = plate("gauntlet", (0.14, 0.12, 0.12), (side * (j["hand_x"] + 0.02), 0, sz), LEATHER, 0.02, 0.85)
        on_bone(gl, rig, "hand" + s)
        gr = plate("greave", (0.16, 0.17, 0.34), (side * j["leg_x"], -0.01, (j["knee_z"] + j["ankle_z"]) / 2 + 0.02), ST, 0.02, 0.6)
        on_bone(gr, rig, "lowerleg" + s)
        bo = plate("boot", (0.15, 0.32, 0.15), (side * j["leg_x"], -0.07, 0.06), LEATHER, 0.03, 0.7)
        bt = bo.modifiers.new("toe", "SIMPLE_DEFORM"); bt.deform_method = "TAPER"; bt.deform_axis = "Y"; bt.factor = -0.4
        on_bone(bo, rig, "foot" + s)
        th = plate("cuisse", (0.19, 0.2, 0.3), (side * j["leg_x"], -0.015, (j["hip_z"] + j["knee_z"]) / 2 + 0.03), BLUE, 0.02, 0.5)
        on_bone(th, rig, "upperleg" + s)
    # tabard: front and back panels from the waist down, on the hips
    for y_, nm in ((-0.17, "tabard_front"), (0.16, "tabard_back")):
        tb = plate(nm, (0.3, 0.03, 0.5), (0, y_, j["hip_z"] - 0.04), BLUE, 0.01, 0.0)
        on_bone(tb, rig, "hips")
    belt = plate("belt", (0.42, 0.36, 0.07), (0, 0, j["waist_z"] - 0.02), LEATHER, 0.01, 0.6); on_bone(belt, rig, "hips")
    sig = plate("sigil", (0.08, 0.015, 0.11), (0, -0.19, j["hip_z"] + 0.04), GOLD, 0.005); on_bone(sig, rig, "hips")
    # the war-lantern: a long pole carried like a spear, lantern cage at the top, always lit
    pole_len = 2.6
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=pole_len, vertices=16)
    pole = bpy.context.object; pole.name = "lantern_pole"; pole.data.materials.append(cloth("ash_wood", (0.22, 0.14, 0.08), 0.6))
    hold(pole, rig, ".r", pole_len * 0.3)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.16, vertices=6)
    cage = bpy.context.object; cage.name = "lantern_cage"; cage.data.materials.append(C.M("iron"))
    cage.modifiers.new("wire", "WIREFRAME").thickness = 0.012
    hold(cage, rig, ".r", pole_len * 0.8 + 0.02)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05)
    flame = bpy.context.object; flame.name = "lantern_flame"; flame.data.materials.append(C.M("lantern"))
    hold(flame, rig, ".r", pole_len * 0.8 + 0.02)
    li = bpy.data.lights.new("tamsin_lantern", "POINT"); li.energy = 60; li.color = (1.0, 0.65, 0.32); li.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("tamsin_lantern", li); C.sc.collection.objects.link(lo)
    hold(lo, rig, ".r", pole_len * 0.8 + 0.02)
    weight(body, rig)
    return [body, head, hair, pole, cage, flame, lo] + eyes


HEROES = {"tamsin": (dict(height=2.15, build=0.92, shoulders=0.95, hips=1.0), tamsin)}


POSTURE = {"upperarm": (28.0, (0, 1, 0)), "lowerarm": (7.0, (0, 1, 0))}
HUMAN_POSTURE = {"upperarm": (40.0, (0, 1, 0)), "lowerarm": (-12.0, (0, 1, 0)), "upperleg": (6.0, (0, 1, 0))}


def relax_arms(rig, degrees=28.0, posture=None):
    """The stand-in animations are made for short chibi limbs held out from a wide body; on human proportions that
    reads stiff and apish. A COMBINE layer on top of every action turns bones by a fixed amount about a world axis
    (sign follows the side), e.g. swinging the upper arms down towards the body."""
    posture = posture or {"upperarm": (degrees, (0, 1, 0)), "lowerarm": (degrees * 0.25, (0, 1, 0))}
    act = bpy.data.actions.new(rig.name + "_relax")
    ad = rig.animation_data_create()
    keep = ad.action
    ad.action = act
    for s, side in ((".l", 1), (".r", -1), ("", 1)):
        for bone, (deg, ax) in posture.items():
            if (s == "") != (bone in ("hips", "spine", "chest", "head")):
                continue
            b = rig.data.bones.get(bone + s)
            if b is None or not deg:
                continue
            axis = b.matrix_local.to_3x3().inverted() @ (Vector(ax) * side)
            pb = rig.pose.bones[bone + s]; pb.rotation_mode = "QUATERNION"
            pb.rotation_quaternion = Matrix.Rotation(math.radians(deg), 4, axis.normalized()).to_quaternion()
            pb.keyframe_insert("rotation_quaternion", frame=1)
            pb.rotation_quaternion = (1, 0, 0, 0)
    ad.action = keep
    tr = rig.animation_data.nla_tracks.new()
    st = tr.strips.new("relax", 1, act); st.blend_type = "COMBINE"; st.extrapolation = "HOLD"
    st.action_frame_end = 2; st.repeat = C.sc.frame_end + 10
    return tr


def build(name, loc=(0, 0, 0), rot_z=0.0, action="Idle", phase=0.0):
    props, maker = HEROES[name]
    rig = base_rig()
    j = proportions(**props)
    reshape(rig, j)
    parts = maker(rig, j)
    rig.location = loc; rig.rotation_euler = (0, 0, rot_z)
    sc = SCALE.get(name, 1.0)   # giants are built at human size (so face and hair recipes fit) and scaled up whole
    rig.scale = (sc, sc, sc)
    rig["meshes"] = [p.name for p in parts]
    C.play(rig, action, phase)
    relax_arms(rig)
    C.sc.frame_set(C.sc.frame_start)
    stand_up(parts, rig)
    return rig


# ------------------------------------------------------------------ real human bodies (MakeHuman CC0 data)
MH_TO_KK = {"pelvis": "hips", "spine_01": "spine", "spine_02": "chest", "spine_03": "chest", "neck_01": "head",
            "head": "head", "clavicle": "chest", "upperarm": "upperarm", "lowerarm": "lowerarm", "hand": "hand",
            "thigh": "upperleg", "calf": "lowerleg", "foot": "foot", "ball": "toes"}


def fit_mh(rig, J):
    """Move the KayKit bones onto a MakeHuman body's (T-posed) joints. Bones keep their roll; the arm, spine and
    leg bones keep (very nearly) their stand-in directions, so the animations read the same."""
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones

    def put(name, head, tail):
        b = eb.get(name)
        if b is None:
            return
        roll = b.roll
        b.head = Vector(head); b.tail = Vector(tail); b.roll = roll
    y = J["pelvis"].y
    top = J["head-2"].z + (J["head-2"].z - J["head"].z) * 0.25
    put("root", (0, 0, 0), (0, 0, J["pelvis"].z * 0.6))
    put("hips", (0, y, J["pelvis"].z), (0, y, J["spine-4"].z))
    put("spine", (0, y, J["spine-4"].z), (0, y, J["spine-2"].z))
    put("chest", (0, y, J["spine-2"].z), (0, y, J["neck"].z))
    put("head", (0, y, J["neck"].z), (0, y, top))
    for s, k in ((".l", "l-"), (".r", "r-")):
        sh, el, wr = J[k + "shoulder"], J[k + "elbow"], J[k + "hand"]
        tip = J[k + "finger-3-4"]
        palm = wr.lerp(tip, 0.45)
        put("upperarm" + s, sh, el)
        put("lowerarm" + s, el, wr)
        put("wrist" + s, wr, wr.lerp(palm, 0.3))
        put("hand" + s, wr.lerp(palm, 0.3), Vector((tip.x, wr.y, wr.z)))
        sx = 1 if s == ".l" else -1
        put("handslot" + s, palm + Vector((0, -0.02, -0.03)), palm + Vector((0, -0.13, -0.03)))
        hp, kn, an = J[k + "upper-leg"], J[k + "knee"], J[k + "ankle"]
        ball, toe = J[k + "foot-1"], J[k + "foot-2"]
        put("upperleg" + s, hp, kn)
        put("lowerleg" + s, kn, an)
        put("foot" + s, an, ball)
        put("toes" + s, ball, Vector((toe.x, toe.y - 0.05, ball.z)))
    bpy.ops.object.mode_set(mode="OBJECT")


def mh_weights(body, rig):
    """Turn the MakeHuman weight groups into KayKit bone groups and bind with an Armature modifier."""
    agg = {}
    gi = {g.index: g.name for g in body.vertex_groups}
    for v in body.data.vertices:
        acc = {}
        for g in v.groups:
            n = gi[g.group]
            side = ""
            base = n
            if n.endswith(("_l", "_r")):
                side = "." + n[-1]; base = n[:-2]
            if base.split("_0")[0] in ("thumb", "index", "middle", "ring", "pinky"):
                base = "hand"
            kk = MH_TO_KK.get(base)
            if kk is None:
                continue
            kk = kk + (side if kk not in ("hips", "spine", "chest", "head") else "")
            acc[kk] = acc.get(kk, 0.0) + g.weight
        agg[v.index] = acc
    for g in list(body.vertex_groups):
        body.vertex_groups.remove(g)
    groups = {}
    for i, acc in agg.items():
        for k, w in acc.items():
            if k not in groups:
                groups[k] = body.vertex_groups.new(name=k)
            groups[k].add([i], w, "REPLACE")
    body.parent = rig
    m = body.modifiers.new("rig", "ARMATURE"); m.object = rig
    return body


def hide_under(body, covered):
    """Remove the skin that armour fully covers (so toes never poke through a rigid boot)."""
    g = body.vertex_groups.get("covered") or body.vertex_groups.new(name="covered")
    g.add([v.index for v in body.data.vertices if covered(v.co)], 1.0, "REPLACE")
    m = body.modifiers.get("covered") or body.modifiers.new("covered", "MASK")
    m.vertex_group = "covered"; m.invert_vertex_group = True


def wear(body, name, keep, mat, offset=0.01, thick=0.01, smooth=0, noise=0.0):
    """Clothing or armour cut from the body itself: the faces whose (T-pose) vertices pass `keep(co)` are copied,
    pushed out along their normals and thickened. The copy keeps the body's bone weights, so it moves exactly
    with the body. `smooth` irons out anatomy (for plate armour); `noise` roughens (for hair)."""
    o = body.copy(); o.data = body.data.copy(); o.name = name
    C.sc.collection.objects.link(o)
    bm = bmesh.new(); bm.from_mesh(o.data)
    drop = [v for v in bm.verts if not keep(v.co)]
    bmesh.ops.delete(bm, geom=drop, context="VERTS"); bm.to_mesh(o.data); bm.free()
    o.data.materials.clear(); o.data.materials.append(mat)
    for m in list(o.modifiers):
        if m.type != "ARMATURE":
            o.modifiers.remove(m)
    if smooth:
        sm = o.modifiers.new("iron", "SMOOTH"); sm.factor = 1.0; sm.iterations = smooth
    d = o.modifiers.new("out", "DISPLACE"); d.direction = "NORMAL"; d.mid_level = 0; d.strength = offset
    if noise:
        tx = bpy.data.textures.new(name + "_n", "CLOUDS"); tx.noise_scale = 0.025; tx.noise_depth = 2
        dn = o.modifiers.new("rough", "DISPLACE"); dn.texture = tx; dn.direction = "NORMAL"; dn.strength = noise; dn.mid_level = 0.3
    if thick:
        so = o.modifiers.new("thick", "SOLIDIFY"); so.thickness = thick; so.offset = 1.0
    o.modifiers.new("sub", "SUBSURF").levels = 1
    return o


def hull_plate(body, rig, name, keep, mat, bone, offset=0.03, thick=0.012, scale=(1, 1, 1), voxel=0.012):
    """Rigid plate armour: the convex hull of the body vertices passing `keep` (rest pose), remeshed smooth, pushed
    out by `offset`, thickened, and fixed to one bone. A hull has no hollows, so it reads as beaten steel."""
    pts = [v.co.copy() for v in body.data.vertices if keep(v.co)]
    c = sum(pts, Vector()) / len(pts)
    pts = [c + Vector(((p - c).x * scale[0], (p - c).y * scale[1], (p - c).z * scale[2])) for p in pts]
    bm = bmesh.new()
    for p in pts:
        bm.verts.new(p)
    bmesh.ops.convex_hull(bm, input=bm.verts)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C.sc.collection.objects.link(o)
    rm = o.modifiers.new("remesh", "REMESH"); rm.mode = "VOXEL"; rm.voxel_size = voxel; rm.use_smooth_shade = True
    sm = o.modifiers.new("soft", "SMOOTH"); sm.factor = 1.0; sm.iterations = 18
    d = o.modifiers.new("out", "DISPLACE"); d.direction = "NORMAL"; d.mid_level = 0; d.strength = offset
    so = o.modifiers.new("thick", "SOLIDIFY"); so.thickness = thick; so.offset = -1.0
    o.modifiers.new("sub", "SUBSURF").levels = 1
    o.data.materials.append(mat)
    for p in o.data.polygons:
        p.use_smooth = True
    on_bone(o, rig, bone)
    return o


def hair_mat(rgb):
    """Short hair: strands as a fine bump running front to back, with lighter and darker locks."""
    m = C.mat("hair_" + "%.2f" % rgb[0], rgb, 0.45)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    mp = nt.nodes.new("ShaderNodeMapping"); mp.inputs["Scale"].default_value = (60, 6, 60)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 1.0; nz.inputs["Detail"].default_value = 8
    nt.links.new(mp.outputs["Vector"], nz.inputs["Vector"])
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.6
    nt.links.new(nz.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (rgb[0] * 0.45, rgb[1] * 0.45, rgb[2] * 0.45, 1)
    cr.color_ramp.elements[1].color = (min(1, rgb[0] * 1.6), min(1, rgb[1] * 1.6), min(1, rgb[2] * 1.6), 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Coat Weight"].default_value = 0.2
    return m


def grow_hair(scalp, length=0.06, count=16000, rgb=(0.22, 0.045, 0.015), kink=0.0, clump=0.3, melanin=0.6, redness=0.95):
    """Real strands from a scalp mesh (Cycles renders them as curves). Short and a bit unruly by default."""
    ps = scalp.modifiers.new("hair", "PARTICLE_SYSTEM").particle_system
    st = ps.settings; st.type = "HAIR"; st.count = count; st.hair_length = length
    # strands leave the scalp mostly backwards and a little down: combed-back, cropped
    st.use_advanced_hair = True; st.normal_factor = length * 0.12; st.object_align_factor = (0, length * 0.85, -length * 0.45)
    st.factor_random = length * 0.15
    st.child_type = "INTERPOLATED"; st.rendered_child_count = 16; st.child_percent = 3
    st.clump_factor = clump; st.roughness_1 = 0.004; st.roughness_endpoint = 0.006; st.roughness_2 = 0.003; st.child_length = 1.0
    st.root_radius = 0.0012; st.tip_radius = 0.0002; st.radius_scale = 1.0; st.use_hair_bspline = True
    if kink:
        st.kink = "CURL"; st.kink_amplitude = kink
    m = bpy.data.materials.new("strands"); m.use_nodes = True
    nt = m.node_tree; out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled"); hb.parametrization = "MELANIN"
    hb.inputs["Melanin"].default_value = melanin; hb.inputs["Melanin Redness"].default_value = redness
    hb.inputs["Roughness"].default_value = 0.4; hb.inputs["Random Color"].default_value = 0.15
    nt.links.new(hb.outputs[0], out.inputs["Surface"])
    scalp.data.materials.append(m); st.material = len(scalp.data.materials)
    st.use_modifier_stack = True
    return ps


def cloth_panel(name, width, length, top, mat, front=True):
    """A hanging cloth panel (tabard, loincloth): a plane from `top` down, folded and slightly flared."""
    bpy.ops.mesh.primitive_plane_add(size=1)
    o = bpy.context.object; o.name = name
    o.rotation_euler.x = math.radians(90); o.scale = (width, length, 1)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)
    o.location = (top[0], top[1], top[2] - length / 2)
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = 4; sd.subdivision_type = "SIMPLE"
    fl = o.modifiers.new("flare", "SIMPLE_DEFORM"); fl.deform_method = "TAPER"; fl.deform_axis = "Z"; fl.factor = 0.35
    tx = bpy.data.textures.new(name + "_folds", "WOOD"); tx.wood_type = "BANDNOISE"; tx.noise_scale = 0.06; tx.turbulence = 1.5
    d = o.modifiers.new("folds", "DISPLACE"); d.texture = tx; d.strength = 0.025; d.direction = "Y"
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.008
    o.modifiers.new("smooth", "SUBSURF").levels = 1
    o.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    return o


def comb_hair(rig, scalp_pts, centre, name="hair", length=0.06, comb=(0, 1, -0.5), lift=0.004, segs=6,
              radius=0.0011, melanin=0.6, redness=0.95, jitter=0.3, seed=3, wrap_above=-99.0, push=0.35, bone="head",
              colour=None, wave=0.0):
    """Combed hair as real curves: every strand starts on the scalp and wraps around the head along `comb`
    (back and down by default), a little off the skin. The hair object rides on the head bone."""
    import random as R
    R.seed(seed)
    cv = bpy.data.hair_curves.new(name)
    cv.add_curves([segs] * len(scalp_pts))
    pos = []
    for p0 in scalp_pts:
        p = Vector(p0); r0 = (p - centre).length
        L = length * (0.7 + 0.6 * R.random())
        step = L / (segs - 1)
        d = Vector(comb(p) if callable(comb) else comb) + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * jitter
        for k in range(segs):
            pos.append(p.copy())
            if wave:   # a slow random walk of the direction: floating, wavy strands
                d = (d.normalized() + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * wave)
            if p.z > wrap_above:   # on the head: follow the skull
                n = (p - centre).normalized()
                t = d - n * d.dot(n)
                if t.length < 1e-6:
                    t = Vector((0, 1, 0))
                p = centre + ((p + t.normalized() * step) - centre).normalized() * (r0 + lift * (1 + k * 0.6))
            else:                  # hanging (long hair, beards): fall along d, pushed out from the body's axis
                out = Vector((p.x - centre.x, p.y - centre.y, 0))
                out = out.normalized() if out.length > 1e-6 else Vector((0, -1, 0))
                p = p + (d.normalized() + out * push).normalized() * step
    cv.attributes["position"].data.foreach_set("vector", [c for v in pos for c in v])
    rad = cv.attributes.get("radius") or cv.attributes.new("radius", "FLOAT", "POINT")
    rad.data.foreach_set("value", [radius * (1 - 0.8 * (k / (segs - 1))) for _ in scalp_pts for k in range(segs)])
    o = bpy.data.objects.new(name, cv); C.sc.collection.objects.link(o)
    m = bpy.data.materials.new(name + "_strands"); m.use_nodes = True
    nt = m.node_tree; out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    hb = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    if colour:
        hb.parametrization = "COLOR"; hb.inputs["Color"].default_value = (*colour, 1)
    else:
        hb.parametrization = "MELANIN"
        hb.inputs["Melanin"].default_value = melanin; hb.inputs["Melanin Redness"].default_value = redness
    hb.inputs["Roughness"].default_value = 0.4
    if "Random Color" in hb.inputs:
        hb.inputs["Random Color"].default_value = 0.15
    nt.links.new(hb.outputs[0], out.inputs["Surface"])
    cv.materials.append(m)
    on_bone(o, rig, bone)
    return o


def scalp_points(body, keep, n=20000, seed=5):
    """Random points on the body faces whose vertices all pass `keep` (rest pose)."""
    import random as R
    R.seed(seed)
    me = body.data
    tris = []
    me.calc_loop_triangles()
    for t in me.loop_triangles:
        vs = [me.vertices[i].co for i in t.vertices]
        if all(keep(v) for v in vs):
            tris.append((vs, t.area))
    tot = sum(a for _, a in tris)
    pts = []
    for vs, a in tris:
        k = a / tot * n
        cnt = int(k) + (1 if R.random() < k - int(k) else 0)
        for _ in range(cnt):
            u, v = R.random(), R.random()
            if u + v > 1:
                u, v = 1 - u, 1 - v
            pts.append(vs[0] + (vs[1] - vs[0]) * u + (vs[2] - vs[0]) * v)
    return pts


def eyes_for(rig, helper, iris_rgb=(0.1, 0.2, 0.14)):
    """Replace a MakeHuman eye helper with a sclera ball and an iris, on the head bone."""
    vs = [helper.matrix_world @ v.co for v in helper.data.vertices]
    c = sum(vs, Vector()) / len(vs); r = max((v - c).length for v in vs)
    bpy.data.objects.remove(helper, do_unlink=True)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=c, segments=32, ring_count=16)
    e = bpy.context.object; e.name = "eye"; bpy.ops.object.shade_smooth()
    e.data.materials.append(C.mat("sclera", (0.8, 0.77, 0.72), 0.15))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 0.55, location=c + Vector((0, -r * 0.8, 0)), segments=24, ring_count=12)
    i = bpy.context.object; i.name = "iris"; i.scale = (1, 0.45, 1); bpy.ops.object.shade_smooth()
    m = C.mat("iris", iris_rgb, 0.05)
    i.data.materials.append(m)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 0.25, location=c + Vector((0, -r * 1.0, 0)))
    p = bpy.context.object; p.name = "pupil"; p.scale = (1, 0.3, 1); p.data.materials.append(C.mat("pupil", (0.01, 0.01, 0.01), 0.05))
    for o in (e, i, p):
        on_bone(o, rig, "head")
    return [e, i, p]


def skin_mat_real(rgb=(0.72, 0.48, 0.38), lips=(0.42, 0.16, 0.13), lids=(0.35, 0.2, 0.17)):
    """Skin with tinted lips and eyelids from MakeHuman's UV masks."""
    import mh
    m = C.mat("skin_real", rgb, 0.58)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    col = nt.nodes.new("ShaderNodeRGB"); col.outputs[0].default_value = (*rgb, 1)
    out = col.outputs[0]
    for nm, tint in (("lips", lips), ("eyelids", lids)):
        t = nt.nodes.new("ShaderNodeTexImage"); t.image = mh.mask(nm)
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        mx.inputs[7].default_value = (*tint, 1)
        nt.links.new(t.outputs["Color"], mx.inputs["Factor"]); nt.links.new(out, mx.inputs[6])
        out = mx.outputs[2]
    nt.links.new(out, b.inputs["Base Color"])
    b.inputs["Subsurface Weight"].default_value = 0.25
    b.inputs["Subsurface Radius"].default_value = (0.5, 0.2, 0.1)
    b.inputs["Subsurface Scale"].default_value = 0.02
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 400
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.05
    nt.links.new(n.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def tamsin_mh(rig, body, ex, J):
    SK = skin_mat_real((0.5, 0.29, 0.2))
    ST = steel("steel_dented", dent=0.06)
    BLUE = cloth("tabard_blue", (0.04, 0.07, 0.16))
    GAMB = quilted("gambeson", (0.045, 0.035, 0.03))
    TROU = cloth("trousers", (0.06, 0.05, 0.05))
    LEATHER = C.mat("leather", (0.12, 0.07, 0.04), 0.55)
    GOLD = C.mat("gold", (0.9, 0.62, 0.22), 0.3, metal=1.0)
    HAIR = hair_mat((0.09, 0.018, 0.006))
    body.data.materials.append(SK)
    sh, el, wr = J["l-shoulder"], J["l-elbow"], J["l-hand"]
    neck, pel, kn, an = J["neck"].z, J["pelvis"].z, J["l-knee"].z, J["l-ankle"].z
    s4, s2 = J["spine-4"].z, J["spine-2"].z
    eye = J["l-eye"]; hy = J["head"].y
    parts = []
    ax = lambda c: abs(c.x)
    parts.append(wear(body, "gambeson", lambda c: (ax(c) < sh.x + 0.02 and pel - 0.08 < c.z < neck - 0.04)
                      or (ax(c) >= sh.x + 0.02 and ax(c) < wr.x - 0.05 and c.z > neck - 0.4), GAMB, 0.012, 0.01))
    parts.append(wear(body, "trousers", lambda c: c.z < pel + 0.02 and c.z > an + 0.12, TROU, 0.01, 0.008))
    parts.append(wear(body, "gauntlets", lambda c: ax(c) > el.x + 0.12 and c.z > neck - 0.5, LEATHER, 0.007, 0.006))
    cy = J["spine-2"].y
    parts.append(hull_plate(body, rig, "cuirass", lambda c: ax(c) < sh.x - 0.03 and s2 - 0.06 < c.z < neck - 0.08, ST, "chest", 0.04, scale=(0.95, 1.0, 1.0)))
    parts.append(hull_plate(body, rig, "plackart", lambda c: ax(c) < sh.x - 0.04 and s4 - 0.04 < c.z < s2 - 0.02, ST, "spine", 0.03))
    parts.append(wear(body, "tassets", lambda c: pel - 0.2 < c.z < s4 - 0.03 and ax(c) < 0.32, ST, 0.07, 0.012, smooth=12))
    for side, sd in ((".l", 1), (".r", -1)):
        S = lambda c, sd=sd: c.x * sd > 0
        parts.append(hull_plate(body, rig, "pauldron" + side, lambda c, S=S: S(c) and sh.x - 0.06 < ax(c) < sh.x + 0.15 and c.z > sh.z - 0.04,
                                ST, "upperarm" + side, 0.025, scale=(1.0, 1.0, 1.05)))
        parts.append(hull_plate(body, rig, "vambrace" + side, lambda c, S=S: S(c) and el.x + 0.05 < ax(c) < wr.x - 0.05 and c.z > neck - 0.5,
                                ST, "lowerarm" + side, 0.02))
        kx = J["l-knee"]
        parts.append(hull_plate(body, rig, "boot" + side, lambda c, S=S: S(c) and c.z < an + 0.05 and ax(c) < 0.4,
                                LEATHER, "foot" + side, 0.022, voxel=0.02, scale=(1.08, 1.05, 1.1)))
        parts.append(hull_plate(body, rig, "bootleg" + side, lambda c, S=S: S(c) and an - 0.02 < c.z < kn - 0.1 and ax(c) < 0.4,
                                LEATHER, "lowerleg" + side, 0.018, voxel=0.015))
        parts.append(hull_plate(body, rig, "greave" + side, lambda c, S=S: S(c) and an + 0.17 < c.z < kn - 0.02 and ax(c) < 0.4,
                                ST, "lowerleg" + side, 0.028))
        parts.append(hull_plate(body, rig, "poleyn" + side, lambda c, S=S: S(c) and kn - 0.06 < c.z < kn + 0.08 and c.y < kx.y and ax(c) < 0.4,
                                ST, "lowerleg" + side, 0.035))
    parts.append(wear(body, "hair", lambda c: (c.z > eye.z + 0.075 - 0.45 * ax(c) if c.y < eye.y + 0.05 else
                                              c.z > eye.z + (0.0 if ax(c) < 0.062 else 0.04) - 0.5 * max(0.0, c.y - eye.y - 0.05) and c.z > J["jaw"].z - 0.0),
                      HAIR, 0.002, 0.003))
    hair_keep = lambda c: ax(c) < 0.13 and c.z > neck and (c.z > eye.z + 0.075 - 0.45 * ax(c) if c.y < eye.y + 0.05 else
                           c.z > eye.z + (0.0 if ax(c) < 0.062 else 0.04) - 0.5 * max(0.0, c.y - eye.y - 0.05) and c.z > J["jaw"].z)
    hc = Vector((0, J["head"].y + 0.01, (J["head"].z + J["head-2"].z) / 2))
    parts.append(comb_hair(rig, scalp_points(body, hair_keep, 22000), hc, "tamsin_hair", 0.07,
                           lambda p: (0, 1, 0.02) if p.y < hc.y - 0.025 else (0, 1, -0.45), jitter=0.22))
    parts.append(wear(body, "brows", lambda c: eye.z + 0.022 < c.z < eye.z + 0.036 and 0.012 < ax(c) < 0.062 and c.y < eye.y - 0.0,
                      HAIR, 0.003, 0.002))
    parts.append(wear(body, "gorget", lambda c: neck - 0.09 < c.z < neck + 0.03 and ax(c) < 0.16, ST, 0.03, 0.012, smooth=10))
    hide_under(body, lambda c: c.z < an + 0.07)   # feet live inside the boots
    # tabard panels and belt, rigid on the hips
    for y_, nm in ((J["pelvis"].y - 0.16, "tabard_front"), (J["pelvis"].y + 0.15, "tabard_back")):
        tb = cloth_panel(nm, 0.27, pel - kn + 0.05, (0, y_, s4 - 0.03), BLUE, front=y_ < J["pelvis"].y)
        on_bone(tb, rig, "hips"); parts.append(tb)
    belt = plate("belt", (0.4, 0.3, 0.06), (0, J["pelvis"].y, s4 - 0.01), LEATHER, 0.01, 0.75); on_bone(belt, rig, "hips")
    sig = plate("sigil", (0.08, 0.012, 0.1), (0, J["pelvis"].y - 0.175, pel - 0.02), GOLD, 0.005); on_bone(sig, rig, "hips")
    parts += [belt, sig]
    for h in ex:
        parts += eyes_for(rig, h)
    # the war-lantern
    pole_len = 2.6
    bpy.ops.mesh.primitive_cylinder_add(radius=0.022, depth=pole_len, vertices=16)
    pole = bpy.context.object; pole.name = "lantern_pole"; pole.data.materials.append(cloth("ash_wood", (0.22, 0.14, 0.08), 0.6))
    hold(pole, rig, ".r", pole_len * 0.3)
    bpy.ops.mesh.primitive_cylinder_add(radius=0.07, depth=0.16, vertices=6)
    cage = bpy.context.object; cage.name = "lantern_cage"; cage.data.materials.append(C.M("iron"))
    cage.modifiers.new("wire", "WIREFRAME").thickness = 0.012
    hold(cage, rig, ".r", pole_len * 0.8 + 0.02)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05)
    flame = bpy.context.object; flame.name = "lantern_flame"; flame.data.materials.append(C.M("lantern"))
    hold(flame, rig, ".r", pole_len * 0.8 + 0.02)
    li = bpy.data.lights.new("tamsin_lantern", "POINT"); li.energy = 60; li.color = (1.0, 0.65, 0.32); li.shadow_soft_size = 0.05
    lo = bpy.data.objects.new("tamsin_lantern", li); C.sc.collection.objects.link(lo)
    hold(lo, rig, ".r", pole_len * 0.8 + 0.02)
    return [body] + parts + [pole, cage, flame, lo]


POSTURES = {}
SCALE = {}
HUMANS = {"tamsin": (dict(height=2.1, gender=0.0, muscle=0.8, weight=0.4, tall=0.3,
                          targets={"nose/nose-hump-incr": 0.6}), tamsin_mh)}


def soften(rig, action, phase=0.0, base="Idle", amount=0.65):
    """Play `action` at `amount` strength over `base`: the stand-in walks kick their legs like toys; mixed 65/35
    with the idle they read as a human stride."""
    ad = rig.animation_data_create(); ad.action = None
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    C.play(rig, base, 0.0)
    act = bpy.data.actions.get(action)
    a0, a1 = act.frame_range; L = max(a1 - a0, 1)
    tr = ad.nla_tracks.new(prev=ad.nla_tracks[0])
    st = tr.strips.new(action, int(1 - phase * L), act)
    st.repeat = math.ceil((C.sc.frame_end + L) / L) + 1
    st.use_animated_influence = True; st.influence = amount
    st.keyframe_insert("influence", frame=1)
    return st


def build_human(name, loc=(0, 0, 0), rot_z=0.0, action="Idle", phase=0.0, soft=None):
    """A hero on a real (MakeHuman) body. Faces -Y like the stand-ins after a half turn... see tests."""
    import mh
    props, maker = HUMANS[name]
    rig = base_rig()
    body, ex, J = mh.body(name + "_body", **props)
    fit_mh(rig, J)
    mh_weights(body, rig)
    parts = maker(rig, body, ex, J)
    rig.location = loc; rig.rotation_euler = (0, 0, rot_z)
    sc = SCALE.get(name, 1.0)   # giants are built at human size (so face and hair recipes fit) and scaled up whole
    rig.scale = (sc, sc, sc)
    rig["meshes"] = [p.name for p in parts]
    if soft is None:
        soft = 0.65 if action.startswith(("Walking", "Running")) else 1.0
    if soft < 1.0:
        soften(rig, action, phase, amount=soft)
    else:   # deaths, sitting/lying down and standing up play once and hold their last pose
        once = action.startswith("Death") or action.endswith(("_Down", "_StandUp"))
        st = C.play(rig, action, phase, repeat=1 if once else None)
        if once:
            st.extrapolation = "HOLD"
    relax_arms(rig, posture=POSTURES.get(name, HUMAN_POSTURE))
    C.sc.frame_set(C.sc.frame_start)
    stand_up(parts, rig)
    return rig


# ------------------------------------------------------------------ shared kit for robed and gowned figures
def skirt(name, J, top_z, bottom_z, r_top, r_bottom, mat, rig, y_off=0.0, leg_share=0.55, folds=0.03, rings=28, segs=64,
          flat=0.85):
    """A long robe or gown skirt: a flared tube from the waist to the floor. Its top rides on the hips and its lower
    part follows the thighs about halfway, blended across the middle, so it swings with a stride but never splits."""
    bm = bmesh.new()
    cy = J["pelvis"].y + y_off
    rows = []
    for i in range(rings + 1):
        t = i / rings
        z = top_z + (bottom_z - top_z) * t
        r = r_top + (r_bottom - r_top) * (t ** 0.8)
        rows.append([bm.verts.new((math.cos(a) * r, cy + math.sin(a) * r * flat, z))
                     for a in (2 * math.pi * k / segs for k in range(segs))])
    for i in range(rings):
        for k in range(segs):
            bm.faces.new((rows[i][k], rows[i][(k + 1) % segs], rows[i + 1][(k + 1) % segs], rows[i + 1][k]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C.sc.collection.objects.link(o)
    gh, gl, gr = (o.vertex_groups.new(name=n) for n in ("hips", "upperleg.l", "upperleg.r"))
    for v in me.vertices:
        t = (top_z - v.co.z) / (top_z - bottom_z)
        share = leg_share * min(1.0, max(0.0, t * 1.3 - 0.1))
        fl = min(1.0, max(0.0, 0.5 + v.co.x / 0.18))
        gh.add([v.index], 1 - share, "REPLACE"); gl.add([v.index], share * fl, "REPLACE"); gr.add([v.index], share * (1 - fl), "REPLACE")
    o.parent = rig
    o.modifiers.new("rig", "ARMATURE").object = rig
    tx = bpy.data.textures.new(name + "_folds", "WOOD"); tx.wood_type = "BANDNOISE"; tx.noise_scale = 0.05; tx.turbulence = 0.8
    d = o.modifiers.new("folds", "DISPLACE"); d.texture = tx; d.direction = "NORMAL"; d.strength = folds; d.texture_coords = "OBJECT"
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.008
    o.modifiers.new("sub", "SUBSURF").levels = 1
    o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    return o


def robe_cloth(name, rgb, patches=0.0, rough=0.9, sheen=0.25):
    """Woven wool: fine weave bump, mottled tone, optional darker patches (sewn-on repairs)."""
    m = cloth(name, rgb, rough)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Sheen Weight"].default_value = sheen
    tc = nt.nodes.new("ShaderNodeTexCoord")
    nz = nt.nodes.new("ShaderNodeTexNoise"); nz.inputs["Scale"].default_value = 9; nz.inputs["Detail"].default_value = 4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeValToRGB")
    cr.color_ramp.elements[0].color = (rgb[0] * 0.7, rgb[1] * 0.7, rgb[2] * 0.7, 1)
    cr.color_ramp.elements[1].color = (rgb[0] * 1.2, rgb[1] * 1.2, rgb[2] * 1.2, 1)
    nt.links.new(nz.outputs["Fac"], cr.inputs["Fac"])
    col = cr.outputs["Color"]
    if patches:
        vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 11
        nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
        th = nt.nodes.new("ShaderNodeMath"); th.operation = "GREATER_THAN"; th.inputs[1].default_value = 1 - patches
        nt.links.new(vo.outputs["Color"], th.inputs[0])
        mx = nt.nodes.new("ShaderNodeMix"); mx.data_type = "RGBA"
        mx.inputs[7].default_value = (rgb[0] * 0.75, rgb[1] * 0.76, rgb[2] * 0.78, 1)
        nt.links.new(th.outputs[0], mx.inputs["Factor"]); nt.links.new(col, mx.inputs[6]); col = mx.outputs[2]
    nt.links.new(col, b.inputs["Base Color"])
    return m


def lantern_staff(rig, name, length=2.5, light_rgb=(1.0, 0.72, 0.35), energy=70, flame_mat=None, side=".r", grip=0.35):
    """A tall staff with a brass lantern hung from a crook at the top (Oswin's silhouette)."""
    WOOD = cloth(name + "_wood", (0.13, 0.08, 0.045), 0.7)
    BRASS = C.mat(name + "_brass", (0.75, 0.52, 0.22), 0.3, metal=1.0)
    parts = []
    bpy.ops.mesh.primitive_cylinder_add(radius=0.026, depth=length, vertices=16)
    st = bpy.context.object; st.name = name + "_staff"; st.data.materials.append(WOOD)
    tx = bpy.data.textures.new(name + "_gnarl", "CLOUDS"); tx.noise_scale = 0.15
    d = st.modifiers.new("gnarl", "DISPLACE"); d.texture = tx; d.strength = 0.012
    st.modifiers.new("sub", "SUBSURF").levels = 1
    hold(st, rig, side, length * 0.5 - grip * length); parts.append(st)
    top = length * 0.5 - grip * length + length / 2
    bpy.ops.mesh.primitive_torus_add(major_radius=0.12, minor_radius=0.022, major_segments=24)
    cr = bpy.context.object; cr.name = name + "_crook"; cr.rotation_euler = (math.radians(90), 0, 0)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    cr.data.materials.append(WOOD)
    bm = bmesh.new(); bm.from_mesh(cr.data)   # keep the top half of the ring: a hook bent over to one side
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.01 and v.co.x < 0.0], context="VERTS"); bm.to_mesh(cr.data); bm.free()
    hold(cr, rig, side, top - 0.0); cr["hold_dx"] = 0.12; parts.append(cr)
    for nm, (r, dpt, z) in (("cap", (0.05, 0.03, 0.0)), ("cage", (0.075, 0.18, -0.12)), ("base", (0.06, 0.03, -0.22))):
        bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=dpt, vertices=8)
        o = bpy.context.object; o.name = name + "_lantern_" + nm; o.data.materials.append(BRASS)
        if nm == "cage":
            o.modifiers.new("wire", "WIREFRAME").thickness = 0.01
        hold(o, rig, side, top - 0.06 + z); o["hold_dx"] = 0.24; parts.append(o)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.045)
    fl = bpy.context.object; fl.name = name + "_flame"; fl.data.materials.append(flame_mat or C.M("lantern"))
    hold(fl, rig, side, top - 0.18); fl["hold_dx"] = 0.24; parts.append(fl)
    li = bpy.data.lights.new(name + "_light", "POINT"); li.energy = energy; li.color = light_rgb; li.shadow_soft_size = 0.05
    lo = bpy.data.objects.new(name + "_light", li); C.sc.collection.objects.link(lo)
    hold(lo, rig, side, top - 0.18); lo["hold_dx"] = 0.24; parts.append(lo)
    return parts


def wide_hat(rig, J, mat, brim=0.27, crown_h=0.2, tilt=-8.0):
    """A wide-brimmed traveller's hat with a soft dented crown, the brim drooping a little, on the head bone."""
    top = J["head-2"].z; hy = J["head"].y
    bpy.ops.mesh.primitive_circle_add(radius=brim, vertices=64, fill_type="NGON", location=(0, hy, top - 0.07))
    b = bpy.context.object; b.name = "hat_brim"; b.data.materials.append(mat)
    bpy.ops.object.mode_set(mode="EDIT"); bpy.ops.mesh.inset(thickness=brim * 0.55); bpy.ops.mesh.poke()
    bpy.ops.object.mode_set(mode="OBJECT")
    b.modifiers.new("thick", "SOLIDIFY").thickness = 0.01
    tx = bpy.data.textures.new("brim_wave", "CLOUDS"); tx.noise_scale = 0.25
    dw = b.modifiers.new("wave", "DISPLACE"); dw.texture = tx; dw.strength = 0.04; dw.direction = "Z"
    b.modifiers.new("sub", "SUBSURF").levels = 2
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=48, ring_count=24, location=(0, hy + 0.01, top - 0.07))
    c = bpy.context.object; c.name = "hat_crown"; c.data.materials.append(mat)
    bm = bmesh.new(); bm.from_mesh(c.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -0.05], context="VERTS"); bm.to_mesh(c.data); bm.free()
    c.scale = (0.14, 0.15, crown_h)
    tx2 = bpy.data.textures.new("hat_dent", "CLOUDS"); tx2.noise_scale = 0.4
    dd = c.modifiers.new("dent", "DISPLACE"); dd.texture = tx2; dd.strength = 0.08
    c.modifiers.new("thick", "SOLIDIFY").thickness = 0.01
    c.modifiers.new("sub", "SUBSURF").levels = 1
    for o in (b, c):
        o.rotation_euler.x = math.radians(tilt)
        bpy.context.view_layer.objects.active = o
        bpy.ops.object.shade_smooth()
        on_bone(o, rig, "head")
    return [b, c]


def face_and_hair_points(J):
    eye = J["l-eye"]; hy = J["head"].y
    ax = lambda c: abs(c.x)
    scalp = lambda c: ax(c) < 0.13 and c.z > J["neck"].z and (c.z > eye.z + 0.075 - 0.45 * ax(c) if c.y < eye.y + 0.05 else
                       c.z > eye.z + (0.0 if ax(c) < 0.062 else 0.04) - 0.5 * max(0.0, c.y - eye.y - 0.05) and c.z > J["jaw"].z)
    centre = Vector((0, hy + 0.01, (J["head"].z + J["head-2"].z) / 2))
    return scalp, centre


def oswin_mh(rig, body, ex, J):
    """Oswin the Grey Lantern: 80s, tall, thin, a little stooped, long white beard, patched grey travelling robes,
    wide-brimmed grey hat, a staff with a brass lantern hung from its crook (warm yellow light)."""
    SK = skin_mat_real((0.52, 0.34, 0.27), lips=(0.36, 0.17, 0.15), lids=(0.33, 0.2, 0.18))
    GREY = robe_cloth("oswin_robe", (0.085, 0.088, 0.092), patches=0.05)
    FELT = robe_cloth("oswin_felt", (0.11, 0.11, 0.105), rough=0.95, sheen=0.4)
    LEATHER = C.mat("oswin_leather", (0.09, 0.06, 0.04), 0.6)
    body.data.materials.append(SK)
    sh, el, wr = J["l-shoulder"], J["l-elbow"], J["l-hand"]
    neck, pel, kn, an = J["neck"].z, J["pelvis"].z, J["l-knee"].z, J["l-ankle"].z
    s4 = J["spine-4"].z
    eye = J["l-eye"]
    ax = lambda c: abs(c.x)
    parts = []
    parts.append(wear(body, "robe_top", lambda c: (ax(c) < sh.x + 0.02 and pel - 0.12 < c.z < neck - 0.02)
                      or (ax(c) >= sh.x + 0.02 and ax(c) < wr.x - 0.02 and c.z > neck - 0.4), GREY, 0.025, 0.01, smooth=20))
    parts.append(skirt("robe_skirt", J, s4 + 0.02, 0.03, 0.2, 0.44, GREY, rig, folds=0.035, leg_share=0.7))
    belt = plate("rope_belt", (0.36, 0.28, 0.035), (0, J["pelvis"].y, s4 + 0.03), LEATHER, 0.01, 0.8); on_bone(belt, rig, "hips"); parts.append(belt)
    for side, sd in ((".l", 1), (".r", -1)):
        S = lambda c, sd=sd: c.x * sd > 0
        parts.append(hull_plate(body, rig, "boot" + side, lambda c, S=S: S(c) and c.z < an + 0.05 and ax(c) < 0.4,
                                LEATHER, "foot" + side, 0.02, voxel=0.02, scale=(1.05, 1.05, 1.1)))
    hide_under(body, lambda c: c.z < an + 0.07)
    hide_under(body, lambda c: c.z < an + 0.07 or (c.z < pel - 0.06 and abs(c.x) < 0.4))   # legs live inside the long skirt
    parts += wide_hat(rig, J, FELT)
    scalp, hc = face_and_hair_points(J)
    WHITE = (0.82, 0.8, 0.76)
    # long white hair from under the hat, hanging to the shoulders
    parts.append(comb_hair(rig, scalp_points(body, lambda c: scalp(c) and c.z < eye.z + 0.09 and c.y > eye.y + 0.07, 9000), hc, "oswin_hair", 0.26,
                           (0, 0.6, -1), segs=9, wrap_above=eye.z - 0.02, colour=WHITE, jitter=0.25, radius=0.0012))
    # beard and moustache: from the jaw, cheeks and upper lip, falling to the chest
    mz = J["mouth"].z
    chin = lambda c: (c.y < J["head"].y - 0.03 and J["jaw"].z - 0.075 < c.z < mz - 0.012 and ax(c) < 0.068)
    parts.append(comb_hair(rig, scalp_points(body, chin, 16000, seed=8), hc, "oswin_beard", 0.3, (0, -0.25, -1), segs=10,
                           lift=0.0, colour=WHITE, jitter=0.12, radius=0.0016, push=0.25, wrap_above=99.0))
    lip = lambda c: (c.y < J["head"].y - 0.06 and mz + 0.006 < c.z < mz + 0.022 and ax(c) < 0.03)
    parts.append(comb_hair(rig, scalp_points(body, lip, 2500, seed=10), hc, "oswin_moustache", 0.07,
                           lambda p: (0.7 * p.x / max(abs(p.x), 1e-3), -0.35, -1.4), segs=6, lift=0.0, colour=WHITE, jitter=0.1,
                           radius=0.0014, push=0.2, wrap_above=99.0))
    brow = lambda c: eye.z + 0.02 < c.z < eye.z + 0.036 and 0.01 < ax(c) < 0.064 and c.y < eye.y
    parts.append(comb_hair(rig, scalp_points(body, brow, 1500, seed=9), hc, "oswin_brows", 0.03,
                           lambda p: (1 if p.x > 0 else -1, -0.3, -0.35), segs=4, colour=WHITE, jitter=0.2, radius=0.0012))
    # a heavy wool mantle over the shoulders, darker than the robe
    MANT = robe_cloth("oswin_mantle", (0.06, 0.062, 0.066), patches=0.04)
    parts.append(wear(body, "mantle", lambda c: (ax(c) < sh.x + 0.16 and J["spine-1"].z - 0.12 < c.z < neck + 0.02 and ax(c) < 0.35)
                      , MANT, 0.032, 0.012, smooth=14))
    for h in ex:
        parts += eyes_for(rig, h, iris_rgb=(0.12, 0.14, 0.2))
    parts += lantern_staff(rig, "oswin", 2.45)
    return [body] + parts


POSTURES["oswin"] = dict(HUMAN_POSTURE, chest=(10.0, (1, 0, 0)), head=(-6.0, (1, 0, 0)))
HUMANS["oswin"] = (dict(height=2.3, gender=1.0, muscle=0.25, weight=0.2, tall=0.85, age=0.92,
                        targets={"nose/nose-hump-incr": 0.4, "cheek/l-cheek-bones-incr": 0.5, "cheek/r-cheek-bones-incr": 0.5}),
                   oswin_mh)


def satin(name, rgb, trims=(), trim_rgb=(0.85, 0.6, 0.2)):
    """Satin with gold trim bands: `trims` are (z_lo, z_hi) world heights painted gold (hems, waistbands)."""
    m = C.mat(name, rgb, 0.35)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    b.inputs["Sheen Weight"].default_value = 0.6; b.inputs["Sheen Roughness"].default_value = 0.3
    gold = 0.0
    if trims:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Position"], sep.inputs[0])
        acc = None
        for lo, hi in trims:
            a = nt.nodes.new("ShaderNodeMath"); a.operation = "GREATER_THAN"; a.inputs[1].default_value = lo
            c = nt.nodes.new("ShaderNodeMath"); c.operation = "LESS_THAN"; c.inputs[1].default_value = hi
            nt.links.new(sep.outputs["Z"], a.inputs[0]); nt.links.new(sep.outputs["Z"], c.inputs[0])
            mu = nt.nodes.new("ShaderNodeMath"); mu.operation = "MULTIPLY"
            nt.links.new(a.outputs[0], mu.inputs[0]); nt.links.new(c.outputs[0], mu.inputs[1])
            if acc is None:
                acc = mu.outputs[0]
            else:
                mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
                nt.links.new(acc, mx.inputs[0]); nt.links.new(mu.outputs[0], mx.inputs[1]); acc = mx.outputs[0]
        col = nt.nodes.new("ShaderNodeMix"); col.data_type = "RGBA"
        col.inputs[6].default_value = (*rgb, 1); col.inputs[7].default_value = (*trim_rgb, 1)
        nt.links.new(acc, col.inputs["Factor"]); nt.links.new(col.outputs[2], b.inputs["Base Color"])
        nt.links.new(acc, b.inputs["Metallic"])
    return m


def six_mail(name="six_mail"):
    """Fine mail in six sectors around the body, one per element colour (the Queen's collar)."""
    m = C.mat(name, (0.6, 0.6, 0.6), 0.35, metal=1.0)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Object"], sep.inputs[0])
    at = nt.nodes.new("ShaderNodeMath"); at.operation = "ARCTAN2"
    nt.links.new(sep.outputs["X"], at.inputs[0]); nt.links.new(sep.outputs["Y"], at.inputs[1])
    nm = nt.nodes.new("ShaderNodeMapRange"); nm.inputs["From Min"].default_value = -math.pi; nm.inputs["From Max"].default_value = math.pi
    nt.links.new(at.outputs[0], nm.inputs["Value"])
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "CONSTANT"
    els = cr.color_ramp.elements
    tint = lambda c: (*[0.62 * 0.75 + x * 0.25 for x in c], 1)   # mostly silver, a breath of each element
    els[0].position = 0.0; els[0].color = tint(C.ELEMENTS[0])
    els[1].position = 1 / 6; els[1].color = tint(C.ELEMENTS[1])
    for i in range(2, 6):
        e = els.new(i / 6); e.color = tint(C.ELEMENTS[i])
    nt.links.new(nm.outputs["Result"], cr.inputs["Fac"]); nt.links.new(cr.outputs["Color"], b.inputs["Base Color"])
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 260
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.8; bu.invert = True
    nt.links.new(vo.outputs["Distance"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def braid(rig, J, mat, length=0.75, lobes=36, r0=0.028, r1=0.014):
    """A single long braid from the back of the head down the spine: alternating twisted lobes on a gentle curve."""
    hy = J["head"].y; top = Vector((0, hy + 0.1, J["l-eye"].z - 0.02))
    parts = []
    for i in range(lobes):
        t = i / (lobes - 1)
        z = top.z - length * t
        y = top.y + 0.04 * math.sin(min(1, t * 3) * math.pi / 2) + (0.03 if z < J["neck"].z else 0.0) * min(1, (J["neck"].z - z) * 6)
        r = r0 + (r1 - r0) * t
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, segments=16, ring_count=10,
                                             location=((r * 0.45) * (1 if i % 2 else -1), y, z))
        o = bpy.context.object; o.scale = (r, r * 0.75, r * 2.1); o.rotation_euler.y = 0.55 * (1 if i % 2 else -1)
        parts.append(o)
    for o in parts[1:]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]; parts[0].select_set(True)
    bpy.ops.object.join()
    br = bpy.context.object; br.name = "braid"; br.data.materials.append(mat)
    bpy.ops.object.shade_smooth()
    on_bone(br, rig, "head")
    return br


def circlet(rig, J, mat, points=6):
    """A thin silver circlet with six points around the brow."""
    eye = J["l-eye"]; hy = J["head"].y
    z = eye.z + 0.05
    bpy.ops.mesh.primitive_torus_add(major_radius=0.097, minor_radius=0.0045, major_segments=64, location=(0, hy - 0.005, z))
    t = bpy.context.object; t.name = "circlet"; t.scale = (1.0, 1.12, 1.0); t.rotation_euler.x = math.radians(-12)
    t.data.materials.append(mat); bpy.ops.object.shade_smooth(); on_bone(t, rig, "head")
    out = [t]
    for k in range(points):
        a = -math.pi / 2 + (k - (points - 1) / 2) * 0.42   # fanned across the brow and temples
        x, y = math.cos(a) * 0.097, hy - 0.005 + math.sin(a) * 0.097 * 1.12
        bpy.ops.mesh.primitive_cone_add(radius1=0.006, radius2=0.0, depth=0.03 if k in (2, 3) else 0.022, vertices=8,
                                        location=(x, y, z + 0.013 - 0.004 * math.sin(a) * 1.0))
        p = bpy.context.object; p.name = "circlet_point"; p.data.materials.append(mat); on_bone(p, rig, "head"); out.append(p)
    return out


def ysolde_mh(rig, body, ex, J, blind=False):
    """Queen Ysolde: 24, slight, very straight-backed, sharp face. White and gold gown under a light six-coloured mail
    collar; thin silver circlet of six points; dark hair in a single long braid. (blind: black-gold blindfold, braid cut
    short, grey soldier's cloak.)"""
    SK = skin_mat_real((0.6, 0.4, 0.31), lips=(0.45, 0.17, 0.16), lids=(0.4, 0.24, 0.21))
    sh, el, wr = J["l-shoulder"], J["l-elbow"], J["l-hand"]
    neck, pel, kn, an = J["neck"].z, J["pelvis"].z, J["l-knee"].z, J["l-ankle"].z
    s4, s1 = J["spine-4"].z, J["spine-1"].z
    eye = J["l-eye"]
    ax = lambda c: abs(c.x)
    body.data.materials.append(SK)
    GOWN = satin("gown_white", (0.78, 0.76, 0.7), trims=((0.0, 0.07), (s4 + 0.01, s4 + 0.045)))
    SLEEVE = satin("gown_sleeve", (0.78, 0.76, 0.7), trims=())
    SILVER = C.mat("silver", (0.85, 0.86, 0.9), 0.18, metal=1.0)
    parts = []
    parts.append(wear(body, "bodice", lambda c: (ax(c) < sh.x + 0.02 and pel - 0.08 < c.z < s1 + 0.02)
                      or (ax(c) >= sh.x + 0.02 and ax(c) < wr.x - 0.03 and c.z > neck - 0.4), GOWN, 0.012, 0.008, smooth=10))
    parts.append(skirt("gown_skirt", J, s4 + 0.03, 0.005, 0.16, 0.5, GOWN, rig, folds=0.03, leg_share=0.6, rings=34))
    parts.append(wear(body, "mail_collar", lambda c: ax(c) < sh.x + 0.07 and s1 - 0.04 < c.z < neck - 0.02, six_mail(), 0.022, 0.006, smooth=8))
    for side, sd in ((".l", 1), (".r", -1)):
        S = lambda c, sd=sd: c.x * sd > 0
        parts.append(hull_plate(body, rig, "slipper" + side, lambda c, S=S: S(c) and c.z < an + 0.04 and ax(c) < 0.4,
                                C.mat("slipper", (0.6, 0.45, 0.2), 0.4, metal=0.6), "foot" + side, 0.008, voxel=0.012))
    hide_under(body, lambda c: c.z < an + 0.05)
    hide_under(body, lambda c: c.z < an + 0.07 or (c.z < pel - 0.06 and abs(c.x) < 0.4))   # legs live inside the long skirt
    scalp, hc = face_and_hair_points(J)
    DARK = dict(melanin=0.92, redness=0.25)
    parts.append(comb_hair(rig, scalp_points(body, scalp, 20000), hc, "ysolde_hair", 0.11,
                           lambda p: (0, 1, 0.1) if p.y < hc.y - 0.02 else (-(p.x) * 4, 1, -0.6), jitter=0.12, lift=0.003, **DARK))
    HAIRM = hair_mat((0.03, 0.018, 0.012))
    if not blind:
        parts.append(braid(rig, J, HAIRM))
        parts += circlet(rig, J, SILVER)
    else:
        parts.append(braid(rig, J, HAIRM, length=0.18, lobes=7))
        bf = wear(body, "blindfold", lambda c: eye.z - 0.025 < c.z < eye.z + 0.03 and c.z > J["l-upperlid"].z - 0.05 and ax(c) < 0.11
                  and c.y < J["head"].y + 0.12, satin("blindfold", (0.02, 0.02, 0.025), trims=()), 0.008, 0.004)
        parts.append(bf)
    brow = lambda c: eye.z + 0.02 < c.z < eye.z + 0.034 and 0.012 < ax(c) < 0.06 and c.y < eye.y
    parts.append(comb_hair(rig, scalp_points(body, brow, 300, seed=9), hc, "ysolde_brows", 0.012,
                           lambda p: (1 if p.x > 0 else -1, -0.2, 0.1), segs=4, jitter=0.1, radius=0.0007, **DARK))
    for h in ex:
        parts += eyes_for(rig, h, iris_rgb=(0.16, 0.1, 0.06))
    return [body] + parts


POSTURES["ysolde"] = dict(HUMAN_POSTURE, upperarm=(55.0, (0, 1, 0)), lowerarm=(-35.0, (0, 0, 1)), upperleg=(8.0, (0, 1, 0)))
HUMANS["ysolde"] = (dict(height=2.05, gender=0.0, muscle=0.3, weight=0.25, tall=0.6,
                         targets={"chin/chin-prominent-incr": 0.4, "cheek/l-cheek-bones-incr": 0.6, "cheek/r-cheek-bones-incr": 0.6,
                                  "nose/nose-scale-horiz-decr": 0.4}), ysolde_mh)


# ------------------------------------------------------------------ the Unbound: Heralds
def glow_mat(name, rgb, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    e = nt.nodes.new("ShaderNodeEmission"); e.inputs["Color"].default_value = (*rgb, 1); e.inputs["Strength"].default_value = strength
    nt.links.new(e.outputs[0], out.inputs["Surface"])
    return m


def veil_mat(name, rgb, alpha=0.82):
    m = robe_cloth(name, rgb, rough=0.95, sheen=0.08)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Alpha"].default_value = alpha
    return m


def head_veil(rig, J, mat, drop=0.75, open_front=0.75):
    """A mourning veil over the head and falling past the shoulders, open in front so the face shows."""
    top = J["head-2"].z + 0.03; hy = J["head"].y
    bm = bmesh.new(); rings, segs = 24, 64
    rows = []
    for i in range(rings + 1):
        t = i / rings
        z = top - drop * t
        r = 0.02 + 0.12 * min(1, t * 4) ** 0.6 + 0.2 * t ** 1.5
        row = []
        for k in range(segs):
            a = 2 * math.pi * k / segs - math.pi / 2       # a = -pi/2 is the face (-Y)
            row.append(bm.verts.new((math.cos(a) * r, hy + math.sin(a) * r * 1.05, z)))
        rows.append(row)
    keep_face = lambda k: abs(((2 * math.pi * k / segs) + math.pi) % (2 * math.pi) - math.pi) < open_front / 2
    for i in range(rings):
        t = i / rings
        for k in range(segs):
            if t > 0.12 and keep_face(k) and keep_face((k + 1) % segs):
                continue
            bm.faces.new((rows[i][k], rows[i][(k + 1) % segs], rows[i + 1][(k + 1) % segs], rows[i + 1][k]))
    me = bpy.data.meshes.new("veil"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("veil", me); C.sc.collection.objects.link(o)
    tx = bpy.data.textures.new("veil_folds", "WOOD"); tx.wood_type = "BANDNOISE"; tx.noise_scale = 0.04; tx.turbulence = 1
    d = o.modifiers.new("folds", "DISPLACE"); d.texture = tx; d.strength = 0.02; d.texture_coords = "OBJECT"
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.004
    o.modifiers.new("sub", "SUBSURF").levels = 1
    o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    on_bone(o, rig, "head")
    return o


def wisps(rig, centre_z, rgb=(0.7, 0.55, 1.0), n=5, radius=0.9, energy=15, seed=4):
    """Pale ghost-lights that drift around a figure (the Pale Vesper's choir)."""
    import random as R
    R.seed(seed)
    out = []
    piv = bpy.data.objects.new("wisp_pivot", None); C.sc.collection.objects.link(piv)
    piv.parent = rig; piv.location = (0, 0, centre_z)
    piv.rotation_euler.z = 0; piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler.z = 2 * math.pi; piv.keyframe_insert("rotation_euler", frame=C.sc.frame_end + 240)
    M = glow_mat("wisp", rgb, 14)
    for i in range(n):
        a = 2 * math.pi * i / n + R.uniform(-0.3, 0.3)
        r = radius * R.uniform(0.7, 1.1)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.018, location=(math.cos(a) * r, math.sin(a) * r, R.uniform(-0.6, 0.5)))
        w = bpy.context.object; w.name = "wisp"; w.data.materials.append(M); w.parent = piv
        li = bpy.data.lights.new("wisp_light", "POINT"); li.energy = energy; li.color = rgb; li.shadow_soft_size = 0.05
        lo = bpy.data.objects.new("wisp_light", li); C.sc.collection.objects.link(lo); lo.parent = w
        out += [w, lo]
    out.append(piv)
    return out


def grey_dust(emitter, rate=4000, rgb=(0.55, 0.55, 0.58)):
    """Grey dust leaking off a Herald's outline: tiny glowing motes drifting up and away."""
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.006, subdivisions=1, location=(0, 0, -50))
    mote = bpy.context.object; mote.name = "dust_mote"; mote.data.materials.append(glow_mat("dust", rgb, 1.2))
    ps = emitter.modifiers.new("dust", "PARTICLE_SYSTEM").particle_system
    st = ps.settings; st.count = rate; st.frame_start = -60; st.frame_end = C.sc.frame_end; st.lifetime = 70
    st.lifetime_random = 0.5; st.normal_factor = 0.08; st.factor_random = 0.05
    st.effector_weights.gravity = -0.03; st.brownian_factor = 0.06
    st.render_type = "OBJECT"; st.instance_object = mote; st.particle_size = 0.45; st.size_random = 0.7
    st.use_modifier_stack = True
    return ps


def vesper_mh(rig, body, ex, J):
    """The Pale Vesper, the Hollow Herald: a thin, very tall singer in grey mourning veils, mouth always open in song,
    pale violet ghost-lights following like a choir. Eyes and mouth are empty grey light; grey dust leaks off her."""
    SK = skin_mat_real((0.38, 0.36, 0.37), lips=(0.2, 0.18, 0.2), lids=(0.18, 0.17, 0.2))
    SK.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.05
    body.data.materials.append(SK)
    GREY = veil_mat("vesper_grey", (0.05, 0.05, 0.055), alpha=1.0)
    VEIL = veil_mat("vesper_veil", (0.035, 0.035, 0.04), alpha=0.8)
    LIGHT = glow_mat("hollow_light", (0.8, 0.8, 0.82), 18)
    sh, el, wr = J["l-shoulder"], J["l-elbow"], J["l-hand"]
    neck, pel, an = J["neck"].z, J["pelvis"].z, J["l-ankle"].z
    s4 = J["spine-4"].z
    ax = lambda c: abs(c.x)
    parts = []
    gown = wear(body, "vesper_gown", lambda c: (ax(c) < sh.x + 0.02 and pel - 0.1 < c.z < neck - 0.03)
                or (ax(c) >= sh.x + 0.02 and ax(c) < wr.x - 0.04 and c.z > neck - 0.4), GREY, 0.015, 0.008, smooth=10)
    parts.append(gown)
    sk = skirt("vesper_skirt", J, s4 + 0.02, -0.02, 0.15, 0.55, GREY, rig, folds=0.05, leg_share=0.5, rings=34)
    parts.append(sk)
    parts.append(head_veil(rig, J, VEIL, drop=1.0))
    hide_under(body, lambda c: c.z < an + 0.05)
    hide_under(body, lambda c: c.z < an + 0.07 or (c.z < pel - 0.06 and abs(c.x) < 0.4))   # legs live inside the long skirt
    # empty grey light where the eyes and mouth should be
    for h in ex:
        vs = [h.matrix_world @ v.co for v in h.data.vertices]
        c = sum(vs, Vector()) / len(vs); r = max((v - c).length for v in vs)
        bpy.data.objects.remove(h, do_unlink=True)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=r * 0.98, location=c)
        e = bpy.context.object; e.name = "hollow_eye"; e.data.materials.append(LIGHT); on_bone(e, rig, "head"); parts.append(e)
        li = bpy.data.lights.new("eye_glow", "POINT"); li.energy = 0.6; li.color = (0.85, 0.85, 0.9); li.shadow_soft_size = 0.01
        lo = bpy.data.objects.new("eye_glow", li); C.sc.collection.objects.link(lo); lo.location = c + Vector((0, -0.03, 0))
        on_bone(lo, rig, "head"); parts.append(lo)
    mo = J["mouth"]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=(0, mo.y + 0.03, mo.z - 0.008))
    m = bpy.context.object; m.name = "hollow_mouth"; m.scale = (1.1, 0.8, 1.2); m.data.materials.append(LIGHT)
    on_bone(m, rig, "head"); parts.append(m)
    parts += wisps(rig, J["spine-2"].z, n=6, radius=0.85)
    grey_dust(sk, 900); grey_dust(parts[2], 300)
    return [body] + parts


POSTURES["vesper"] = dict(HUMAN_POSTURE, upperarm=(35.0, (0, 1, 0)), head=(-10.0, (1, 0, 0)))
HUMANS["vesper"] = (dict(height=2.7, gender=0.0, muscle=0.1, weight=0.0, tall=1.0, age=0.6, proportions=0.6,
                         targets={"expression/units/caucasian/mouth-open": 0.9, "cheek/l-cheek-volume-decr": 0.8,
                                  "cheek/r-cheek-volume-decr": 0.8, "neck/measure-neck-height-incr": 0.6}), vesper_mh)


def lamp(rig, energy):
    """Set the brightness of a hero's lantern (or staff light) for a shot."""
    for name in rig["meshes"]:
        o = bpy.data.objects.get(name)
        if o is not None and o.type == "LIGHT":
            o.data.energy = energy
