"""The other five Heralds (the Pale Vesper is in hero.py): Saltmother Ourra, Gorrath the Quarried, Ashwick the
Kindled, Vholt Stormcrown and Mother Briar. All Heralds have grey, empty eyes of light and leak grey dust.
Importing registers them with hero.build_human(). Looks follow lore/characters.md (story canon v2)."""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import cine3d as C
import hero as H
import cast as K
import wardens as W
from cast import Fig

GREY_EYES = (0.82, 0.82, 0.85)


def herald_eyes(f):
    W.glow_eyes(f, GREY_EYES, 18, 0.5)


# ------------------------------------------------------------------ materials
def black_water(name="black_sea"):
    """Black seawater: a thin rippled surface (no refraction, so a face inside stays clear and lights behind don't
    smear into white streaks) over a deep absorbing volume with a little teal scatter."""
    m, nt, out = W._blank(name)
    tc = W._n(nt, "ShaderNodeTexCoord")
    no = W._n(nt, "ShaderNodeTexNoise", _noise_dimensions="4D", Scale=6.0, Detail=6.0)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"]); W._animate_w(no, 1 / 30)
    bu = W._n(nt, "ShaderNodeBump", Strength=0.3); nt.links.new(no.outputs["Fac"], bu.inputs["Height"])
    gl = W._n(nt, "ShaderNodeBsdfGlossy", Roughness=0.25); gl.inputs["Color"].default_value = (0.22, 0.3, 0.3, 1)
    nt.links.new(bu.outputs["Normal"], gl.inputs["Normal"])
    tr = W._n(nt, "ShaderNodeBsdfTransparent"); tr.inputs["Color"].default_value = (0.75, 0.9, 0.9, 1)
    fr = W._n(nt, "ShaderNodeFresnel", IOR=1.33); nt.links.new(bu.outputs["Normal"], fr.inputs["Normal"])
    mx = W._n(nt, "ShaderNodeMixShader"); nt.links.new(fr.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(gl.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    vol = W._n(nt, "ShaderNodeVolumePrincipled", Density=0.5)
    vol.inputs["Color"].default_value = (0.05, 0.25, 0.25, 1); vol.inputs["Absorption Color"].default_value = (0.02, 0.08, 0.08, 1)
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return m


def embers(name="embers"):
    """White-hot embers: glowing white-yellow, cooling to orange with dark ash flakes."""
    m, nt, out = W._blank(name)
    tc = W._n(nt, "ShaderNodeTexCoord")
    no = W._n(nt, "ShaderNodeTexNoise", _noise_dimensions="4D", Scale=22.0, Detail=8.0, Roughness=0.7)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"]); W._animate_w(no, 1 / 20)
    r = nt.nodes.new("ShaderNodeValToRGB"); el = r.color_ramp.elements
    el[0].position = 0.45; el[0].color = (0.02, 0.015, 0.012, 1)
    el[1].position = 0.75; el[1].color = (1.0, 0.95, 0.75, 1)
    e = r.color_ramp.elements.new(0.5); e.color = (1.0, 0.35, 0.04, 1)
    nt.links.new(no.outputs["Fac"], r.inputs[0])
    st = W._n(nt, "ShaderNodeMapRange"); st.inputs[1].default_value = 0.45; st.inputs[2].default_value = 0.85
    st.inputs[3].default_value = 0.0; st.inputs[4].default_value = 4.0
    nt.links.new(no.outputs["Fac"], st.inputs[0])
    b = W._n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.9)
    b.inputs["Base Color"].default_value = (0.02, 0.015, 0.012, 1)
    nt.links.new(r.outputs[0], b.inputs["Emission Color"]); nt.links.new(st.outputs[0], b.inputs["Emission Strength"])
    bu = W._n(nt, "ShaderNodeBump", Strength=0.6); nt.links.new(no.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ parts
def water_column(f, radius=0.62, height=3.6, n_fish=16, n_lanterns=5, seed=6):
    """The 4 m column of black seawater that walks with Ourra, fish and drowned lanterns circling inside."""
    R = random.Random(seed)
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=height, location=(0, f.J["pelvis"].y, height / 2 - 0.02))
    col = bpy.context.object; col.name = "water_column"
    bm = bmesh.new(); bm.from_mesh(col.data)
    bmesh.ops.subdivide_edges(bm, edges=[e for e in bm.edges if abs(e.verts[0].co.z - e.verts[1].co.z) > 0.1], cuts=30)
    bm.to_mesh(col.data); bm.free()
    tx = bpy.data.textures.new("column_waves", "CLOUDS"); tx.noise_scale = 0.25
    d = col.modifiers.new("waves", "DISPLACE"); d.texture = tx; d.strength = 0.05
    col.data.materials.append(black_water()); bpy.ops.object.shade_smooth()
    col.parent = f.rig; f.add(col)
    piv = bpy.data.objects.new("column_pivot", None); C.sc.collection.objects.link(piv); piv.parent = f.rig
    piv.location = (0, f.J["pelvis"].y, 0)
    piv.rotation_euler.z = 0; piv.keyframe_insert("rotation_euler", frame=1)
    piv.rotation_euler.z = -2 * math.pi; piv.keyframe_insert("rotation_euler", frame=C.sc.frame_end + 400)
    for fc in piv.animation_data.action.fcurves if hasattr(piv.animation_data.action, "fcurves") else []:
        for k in fc.keyframe_points:
            k.interpolation = "LINEAR"
    FISH = C.mat("drowned_fish", (0.12, 0.14, 0.14), 0.55, metal=0.1)
    for i in range(n_fish):
        a = R.uniform(0, 2 * math.pi); r = R.uniform(0.3, radius - 0.1)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.04, location=(math.cos(a) * r, math.sin(a) * r, R.uniform(0.2, height - 0.2)))
        fi = bpy.context.object; fi.name = "fish"; fi.scale = (0.35, 1.3, 0.55); fi.rotation_euler.z = a
        fi.data.materials.append(FISH); bpy.ops.object.shade_smooth(); fi.parent = piv; f.add(fi)
    LAN = C.mat("drowned_lantern", (0.15, 0.12, 0.06), 0.5, emit=(0.4, 0.9, 0.7), strength=0.8)
    for i in range(n_lanterns):
        a = 2 * math.pi * i / n_lanterns + 0.4; r = radius * 0.7
        bpy.ops.mesh.primitive_cube_add(size=0.035, location=(math.cos(a) * r, math.sin(a) * r, 0.5 + i * 0.55))
        la = bpy.context.object; la.name = "lantern"; la.data.materials.append(LAN); la.parent = piv; f.add(la)
        li = bpy.data.lights.new("lantern_light", "POINT"); li.energy = 3; li.color = (0.4, 0.9, 0.7); li.shadow_soft_size = 0.03
        lo = bpy.data.objects.new("lantern_light", li); C.sc.collection.objects.link(lo); lo.parent = la; f.add(lo)
    f.add(piv)


def chest_hole(f, targets, size=(0.13, 0.14, 0.15)):
    """A square hole through the chest (Gorrath): a boolean cutter on the chest bone for the body and armour, a dark
    stone lining, and a carved stone heart sitting inside."""
    J = f.J
    cz = (J["spine-1"].z + J["spine-2"].z) / 2 + 0.03
    cy = J["spine-1"].y - 0.1
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, cy, cz)); cut = bpy.context.object; cut.name = "hole_cutter"
    cut.scale = (size[0], size[1] * 1.6, size[2]); bpy.ops.object.transform_apply(scale=True)
    cut.hide_render = True; cut.display_type = "WIRE"; H.on_bone(cut, f.rig, "chest")
    for t in targets:
        b = t.modifiers.new("chest_hole", "BOOLEAN"); b.object = cut; b.operation = "DIFFERENCE"; b.solver = "EXACT"
    bpy.ops.mesh.primitive_cube_add(size=1, location=(0.0, cy + 0.02, cz)); lin = bpy.context.object; lin.name = "hole_lining"
    lin.scale = (size[0] * 0.98, size[1] * 1.1, size[2] * 0.98); bpy.ops.object.transform_apply(scale=True)
    bm = bmesh.new(); bm.from_mesh(lin.data)
    bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if fc.normal.y < -0.5], context="FACES")
    bmesh.ops.reverse_faces(bm, faces=bm.faces[:]); bm.to_mesh(lin.data); bm.free()
    lin.data.materials.append(K.stone("hole_stone", (0.05, 0.045, 0.04))); H.on_bone(lin, f.rig, "chest"); f.add(lin)
    bpy.ops.mesh.primitive_cube_add(size=0.075, location=(0.0, cy + 0.03, cz)); ht = bpy.context.object; ht.name = "stone_heart"
    K._bevel(ht, 0.01, 2)
    ht.data.materials.append(K.stone("heart_stone", (0.3, 0.27, 0.23)))
    ht.data.materials.append(K.rune_overlay("heart_runes", (0.85, 0.85, 0.9), 40, 4, 0.04))
    H.on_bone(ht, f.rig, "chest"); f.add(ht)
    W.point_light(f, "heart_glow", (0.0, cy - 0.05, cz), (0.85, 0.85, 0.9), 2, "chest", 0.03)


def satchel(f, mat, side=1, z=None, name="satchel", size=(0.17, 0.07, 0.14)):
    """A shoulder bag on the hip, with its strap across the chest."""
    J = f.J; z = z or f.pel + 0.02
    bpy.ops.mesh.primitive_cube_add(size=1, location=(side * (f.sh.x - 0.02), J["pelvis"].y - 0.02, z))
    b = bpy.context.object; b.name = name; b.scale = size; bpy.ops.object.transform_apply(scale=True)
    K._bevel(b, 0.015, 3); b.data.materials.append(mat); H.on_bone(b, f.rig, "hips"); f.add(b)
    f.add(H.wear(f.body, name + "_strap", lambda c: abs(c.x * 0.75 - side * (c.z - f.s2) * 0.5) < 0.025 and f.pel < c.z < f.neck + 0.02
                 and abs(c.x) < f.sh.x + 0.02, mat, 0.02, 0.008))
    return b


def lightning_crown(f, n=7):
    """Vholt's crown of lightning: jagged white bolts standing up around the head."""
    R = random.Random(9)
    top = f.J["head-2"].z - 0.03; cy = f.J["head"].y + 0.01
    BOLT = H.glow_mat("crown_bolt", (0.85, 0.9, 1.0), 45)
    cv = bpy.data.curves.new("lightning_crown", "CURVE"); cv.dimensions = "3D"; cv.bevel_depth = 0.0035
    for i in range(n):
        a = 2 * math.pi * i / n
        p = Vector((math.cos(a) * 0.1, cy + math.sin(a) * 0.1, top))
        sp = cv.splines.new("POLY"); sp.points.add(5)
        for k in range(6):
            sp.points[k].co = (*p, 1)
            p = p + Vector((math.cos(a) * 0.012 + R.uniform(-0.02, 0.02), math.sin(a) * 0.012 + R.uniform(-0.02, 0.02), 0.03))
    ring = cv.splines.new("POLY"); ring.points.add(23); ring.use_cyclic_u = True
    for k in range(24):
        a = 2 * math.pi * k / 24
        ring.points[k].co = (math.cos(a) * 0.1, cy + math.sin(a) * 0.1, top + R.uniform(-0.006, 0.006), 1)
    o = bpy.data.objects.new("lightning_crown", cv); C.sc.collection.objects.link(o); o.data.materials.append(BOLT)
    H.on_bone(o, f.rig, "head"); f.add(o)
    W.point_light(f, "crown_light", (0, cy, top + 0.06), (0.75, 0.85, 1.0), 20, "head", 0.05)


def thorn_shell(f, count=7500, flowers=500, grey_flowers=True):
    """Mother Briar's body of black thorns: thorn instances grown out of the skin as hair particles (they follow the
    rig), with white flowers going grey among them."""
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=0.008, radius2=0.0, depth=0.13, location=(0, 0, -60))
    th = bpy.context.object; th.name = "thorn"
    bpy.ops.object.transform_apply(location=False)
    th.data.transform(Matrix.Rotation(math.radians(-90), 4, "Y")); th.data.transform(Matrix.Translation((0.06, 0, 0)))
    b = th.modifiers.new("bend", "SIMPLE_DEFORM"); b.deform_method = "BEND"; b.deform_axis = "Z"; b.angle = math.radians(50)
    th.data.materials.append(W.bark("thorn_bark", (0.006, 0.005, 0.005), (0.035, 0.03, 0.028), moss=0.0))
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.012, subdivisions=2, location=(0, 0, -60)); fl = bpy.context.object
    fl.name = "briar_flower"; fl.scale = (1, 1, 0.45)
    FL = C.mat("briar_flower", (0.55, 0.55, 0.56) if grey_flowers else (0.92, 0.92, 0.88), 0.6)
    fl.data.materials.append(FL)
    for nm, inst, n, size in (("thorns", th, count, 22.0), ("flowers", fl, flowers, 26.0)):   # hair instances come out ~1/23 size
        ps = f.body.modifiers.new(nm, "PARTICLE_SYSTEM").particle_system
        st = ps.settings; st.type = "HAIR"; st.count = n; st.hair_length = 0.05
        st.render_type = "OBJECT"; st.instance_object = inst; st.particle_size = size; st.size_random = 0.6
        st.use_rotations = True; st.rotation_mode = "NOR"; st.phase_factor_random = 2.0; st.rotation_factor_random = 0.25
        ps.seed = 3 if nm == "thorns" else 11
    f.parts += [th, fl]
    th.hide_render = False; th.location.z = -60; fl.location.z = -60


# ------------------------------------------------------------------ the Heralds
def ourra(rig, body, ex, J):
    """Saltmother Ourra, the Drowned Herald. An older woman in tattered teal priestess robes, standing inside a 4 m
    column of black seawater that walks with her; fish and drowned lanterns circle inside it."""
    f = Fig(rig, body, ex, J)
    f.skin((0.4, 0.42, 0.42), lips=(0.25, 0.25, 0.27), lids=(0.22, 0.22, 0.24))
    herald_eyes(f)
    TEAL = H.robe_cloth("ourra_robe", (0.02, 0.12, 0.12), patches=0.15)
    f.add(H.wear(body, "robe_top", lambda c: f.torso(f.pel - 0.1, f.neck - 0.02, 0.025)(c) or f.sleeves(0.05)(c), TEAL, 0.02, 0.01, smooth=12))
    f.add(H.skirt("robe_skirt", J, f.s4 + 0.02, 0.02, 0.17, 0.42, TEAL, rig, folds=0.05))
    f.hide_legs()
    K.hair(f, 0.5, 14000, comb_front=(0, 1, -0.3), comb_back=(0, 0.3, -1), hang_below=f.eye.z - 0.02, jitter=0.25, push=0.06, wave=0.05,
           colour=(0.3, 0.32, 0.31))   # wet hair hangs close, not sprayed out
    water_column(f)
    H.grey_dust(body, 300)
    return [body] + f.parts


def gorrath(rig, body, ex, J):
    """Gorrath the Quarried, the Stone Herald. A massive Stoneborn general, armour fused into his skin, a square hole
    in his chest with a carved stone where his heart was."""
    f = Fig(rig, body, ex, J)
    skin_m = W.mountain_stone("gorrath_skin", (0.13, 0.12, 0.11), moss=0.0)
    W.skin_as(body, skin_m)
    W.lumpy(body, 0.04, 0.01, "VORONOI")
    herald_eyes(f)
    PL = W.basalt("fused_plate", (0, 0, 0), (0.85, 0.85, 0.9), crack_w=0.003, glow=1.5, core_glow=0.0, grey=True)
    n0 = len(f.parts)
    K.plate_set(f, PL, pauldron=1.4, chest=0.05)
    plates = [p for p in f.parts[n0:] if p.name.startswith(("cuirass", "plackart"))]
    for p in f.parts[n0:]:
        W.lumpy(p, 0.05, 0.02, "VORONOI", "chips")
    chest_hole(f, [body] + plates)
    H.grey_dust(body, 400)
    return [body] + f.parts


def ashwick(rig, body, ex, J):
    """Ashwick the Kindled, the Flame Herald. A boy of 14 made of white-hot embers, a messenger's satchel still on his
    shoulder, flame streaming behind him like a cape as he runs."""
    f = Fig(rig, body, ex, J)
    W.skin_as(body, embers())
    herald_eyes(f)
    satchel(f, K.leather("messenger_bag", (0.09, 0.05, 0.025)))
    cape = K.back_cape(f, W.flame_mat("flame_cape", (1.0, 0.22, 0.02), 1.4, tip_down=True), length=f.sh.z - 0.1, width=0.5, name="flame_cape")
    W.point_light(f, "ember_body", (0, J["spine-1"].y - 0.3, f.s2), (1.0, 0.45, 0.12), 40, "chest", 0.2)
    H.grey_dust(body, 500, (0.6, 0.55, 0.5))
    return [body] + f.parts


def vholt(rig, body, ex, J):
    """Vholt Stormcrown, the Sky Herald. An old Galeborn warchief with a crown of lightning. (His black thunderbird
    is a separate mount, see thunderbird().)"""
    f = Fig(rig, body, ex, J)
    f.skin((0.42, 0.36, 0.33), lips=(0.3, 0.22, 0.22))
    herald_eyes(f)
    FUR = H.robe_cloth("vholt_furs", (0.02, 0.02, 0.022), rough=1.0, sheen=0.3)
    LEA = K.leather("vholt_leather", (0.07, 0.05, 0.04))
    K.long_coat(f, H.quilted("vholt_coat", (0.035, 0.035, 0.04)), f.kn - 0.05, flare=0.34)
    f.add(H.wear(body, "fur_mantle", lambda c: abs(c.x) < f.sh.x + 0.1 and f.s1 - 0.02 < c.z < f.neck + 0.02 and c.y > f.J["neck"].y - 0.06, FUR, 0.035, 0.015, smooth=6))
    K.boots(f, LEA)
    K.hair(f, 0.32, 16000, comb_front=(0, 1, 0.2), comb_back=(0, 0.3, -1), hang_below=f.eye.z, jitter=0.35, colour=(0.09, 0.09, 0.095))
    K.beard(f, 0.16, 12000, colour=(0.08, 0.08, 0.085))
    K.brows(f, 400, 0.016, colour=(0.08, 0.08, 0.085))
    lightning_crown(f)
    H.grey_dust(body, 300)
    return [body] + f.parts


def briar(rig, body, ex, J):
    """Mother Briar, the Thorn Herald. A thicket of black thorns in the shape of a hunched old woman, with a healer's
    satchel and white flowers that bloom grey."""
    f = Fig(rig, body, ex, J)
    W.skin_as(body, W.bark("briar_wood", (0.012, 0.01, 0.009), (0.06, 0.05, 0.04), moss=0.0))
    W.lumpy(body, 0.03, 0.02, "WOOD", "tangle")
    herald_eyes(f)
    satchel(f, K.leather("healer_bag", (0.16, 0.12, 0.08)), side=-1, size=(0.15, 0.06, 0.12))
    thorn_shell(f)
    return [body] + f.parts


_HR = {
    "ourra": (dict(height=2.05, gender=0.0, muscle=0.3, weight=0.45, tall=0.5, age=0.85), ourra, 1.0, None),
    "gorrath": (dict(height=2.5, gender=1.0, muscle=1.0, weight=0.8, tall=0.9, age=0.6), gorrath, 1.25,
                dict(H.HUMAN_POSTURE, upperarm=(30.0, (0, 1, 0)))),
    "ashwick": (dict(height=1.7, gender=1.0, muscle=0.3, weight=0.15, tall=0.4, age=0.29), ashwick, 1.0, None),
    "vholt": (dict(height=2.25, gender=1.0, muscle=0.7, weight=0.4, tall=0.7, age=0.85), vholt, 1.0, None),
    "briar": (dict(height=1.9, gender=0.0, muscle=0.2, weight=0.3, tall=0.2, age=0.95), briar, 1.1,
              dict(H.HUMAN_POSTURE, chest=(28.0, (1, 0, 0)), head=(-18.0, (1, 0, 0)))),
}
for _k, (_props, _fn, _sc, _post) in _HR.items():
    H.HUMANS[_k] = (_props, _fn)
    H.SCALE[_k] = _sc
    if _post:
        H.POSTURES[_k] = _post


# ------------------------------------------------------------------ Vholt's mount
def thunderbird(name="thunderbird", loc=(0, 0, 3.0), span=7.0, flap=24):
    """A great bird of black storm cloud with white-hot eyes, flapping slowly. Built facing -Y like the riders.
    Returns (root, saddle): parent a rider's rig to `saddle`."""
    s = span / 7.0
    root = bpy.data.objects.new(name, None); C.sc.collection.objects.link(root); root.location = loc
    CLOUD = W.storm_cloud(name + "_cloud", density=140, black=True, bolts=25)
    SKIN = C.mat(name + "_skin", (0.012, 0.012, 0.015), 0.6)
    parts = []

    def blob(nm, size, at, mat=CLOUD, parent=root):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(0, 0, 0), segments=32, ring_count=16)
        o = bpy.context.object; o.name = name + "_" + nm; o.scale = tuple(v * s for v in size)
        o.location = tuple(v * s for v in at); o.data.materials.append(mat); bpy.ops.object.shade_smooth()
        W.lumpy(o, 0.25, 0.05 * s); o.parent = parent; parts.append(o)
        return o
    blob("body", (0.7, 1.6, 0.62), (0, 0, 0))
    blob("chest", (0.62, 0.8, 0.6), (0, -0.9, 0.12))
    blob("neck", (0.32, 0.55, 0.34), (0, -1.75, 0.45))
    head = blob("head", (0.3, 0.42, 0.3), (0, -2.25, 0.62))
    bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.12 * s, depth=0.55 * s, location=(0, -2.75 * s, 0.55 * s))
    bk = bpy.context.object; bk.name = name + "_beak"; bk.rotation_euler.x = math.radians(-100); bk.data.materials.append(SKIN)
    bk.parent = root; parts.append(bk)
    EYE = H.glow_mat(name + "_eye", (1.0, 0.97, 0.9), 60)
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.055 * s, location=(sx * 0.2 * s, -2.42 * s, 0.7 * s))
        e = bpy.context.object; e.data.materials.append(EYE); e.parent = root; parts.append(e)
        li = bpy.data.lights.new(name + "_eye_light", "POINT"); li.energy = 15; li.color = (1, 0.97, 0.9); li.shadow_soft_size = 0.05
        lo = bpy.data.objects.new(name + "_eye_light", li); C.sc.collection.objects.link(lo)
        lo.location = (sx * 0.22 * s, -2.5 * s, 0.7 * s); lo.parent = root; parts.append(lo)
    # tail: a fan of long feathers
    for k in range(7):
        a = math.radians(-36 + k * 12)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=1, location=(math.sin(a) * 1.1 * s, (1.6 + math.cos(a) * 1.1) * s, -0.05 * s))
        t = bpy.context.object; t.scale = (0.14 * s, 0.9 * s, 0.04 * s); t.rotation_euler.z = -a
        t.data.materials.append(CLOUD); t.parent = root; parts.append(t)
    # wings: tapered, ragged trailing edge, on pivots that flap
    for sx in (-1, 1):
        piv = bpy.data.objects.new(name + "_wing_pivot", None); C.sc.collection.objects.link(piv)
        piv.parent = root; piv.location = (sx * 0.55 * s, -0.5 * s, 0.25 * s); parts.append(piv)
        bm = bmesh.new(); n = 14
        lead, trail = [], []
        for i in range(n + 1):
            t = i / n
            x = sx * t * 3.2 * s
            chord = (1.5 - 0.9 * t) * s
            yl = -0.25 * s + 0.35 * s * t * t
            ragged = (0.25 * s if i % 2 else 0.0) * (0.3 + t)
            lead.append(bm.verts.new((x, yl, 0.15 * s * math.sin(t * math.pi))))
            trail.append(bm.verts.new((x, yl + chord + ragged, 0.1 * s * math.sin(t * math.pi))))
        for i in range(n):
            f = (lead[i], lead[i + 1], trail[i + 1], trail[i])
            bm.faces.new(f if sx > 0 else f[::-1])
        me = bpy.data.meshes.new(name + "_wing"); bm.to_mesh(me); bm.free()
        w = bpy.data.objects.new(name + "_wing", me); C.sc.collection.objects.link(w)
        w.modifiers.new("thick", "SOLIDIFY").thickness = 0.12 * s
        w.modifiers.new("sub", "SUBSURF").levels = 2
        W.lumpy(w, 0.2, 0.06 * s)
        w.data.materials.append(CLOUD); w.parent = piv; parts.append(w)
        piv.rotation_euler = (0, sx * math.radians(6), 0)   # flap=0: wings spread flat (grounded)
        for fr in (range(C.sc.frame_start - flap, C.sc.frame_end + flap * 2, flap // 2) if flap else ()):
            up = ((fr - C.sc.frame_start) // (flap // 2)) % 2 == 0
            piv.rotation_euler = (0, sx * math.radians(-32 if up else 18), 0)
            piv.keyframe_insert("rotation_euler", frame=fr)
    # the body rises and falls with the beat
    for fr in (range(C.sc.frame_start - flap, C.sc.frame_end + flap * 2, flap // 2) if flap else ()):
        up = ((fr - C.sc.frame_start) // (flap // 2)) % 2 == 0
        root.location = (loc[0], loc[1], loc[2] + (0.12 if not up else -0.08) * s)
        root.keyframe_insert("location", frame=fr)
    saddle = bpy.data.objects.new(name + "_saddle", None); C.sc.collection.objects.link(saddle)
    saddle.parent = root; saddle.location = (0, -0.35 * s, 0.6 * s)
    return root, saddle


def mount(rider, saddle):
    """Seat a rider rig (built with action Sit_Chair_Idle) on a saddle: hips on the saddle point."""
    bpy.context.view_layer.update()
    if rider.type != "ARMATURE":   # a sprite card sits with its feet a little below the saddle
        rider.parent = saddle; rider.matrix_parent_inverse = Matrix.Identity(4); rider.location = (0, 0, -0.6)
        return rider
    hips = rider.matrix_world @ rider.pose.bones["hips"].head
    off = rider.matrix_world.translation - hips
    rider.parent = saddle; rider.matrix_parent_inverse = Matrix.Identity(4)
    rider.location = off
    return rider
