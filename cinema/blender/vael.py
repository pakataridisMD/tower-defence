"""Vael-Orrun in 3D, from the approved 2D design (art-test/vael-orrun-flesh*, vael-orrun-three-forms.png):
a giant of bare raw muscle, fibre and dark veins, no crown; two long curved horns and a fan of spikes behind the head,
a dark angular mask of a face with white-hot eyes and a glowing mouth, a cage of rib-bones over an open chest where the
lantern burns as a molten core, black claws on hands and feet.

    vael_orrun          the High King (default)
    vael_orrun_wrath    the Wrath: lava breaking through the veins, fire on the shoulders, the core blazing
    vael_orrun_unmade   the Unmade: grey bone and ash, white fire in the hands
"""
import bpy, bmesh, math, random
from mathutils import Vector
import cine3d as C
import hero as H
import wardens as W
from cast import Fig

CORE = (1.0, 0.42, 0.08)


# ------------------------------------------------------------------ materials
def raw_flesh(name="vael_flesh", lava=0.0, ash=False):
    """Bare muscle: dark red-brown fibre bands, purple-black veins, wet sheen. `lava`: veins glow orange (Wrath).
    ash: grey bone-ash instead of flesh (the Unmade)."""
    m, nt, out = W._blank(name)
    tc = W._n(nt, "ShaderNodeTexCoord")
    warp = W._n(nt, "ShaderNodeTexNoise", Scale=4.0, Detail=3.0)
    nt.links.new(tc.outputs["Object"], warp.inputs["Vector"])
    wv = W._n(nt, "ShaderNodeVectorMath", _operation="MULTIPLY_ADD"); wv.inputs[1].default_value = (0.16, 0.16, 0.16)   # warped hard: veins branch, not cells
    nt.links.new(warp.outputs["Color"], wv.inputs[0]); nt.links.new(tc.outputs["Object"], wv.inputs[2])
    fib = W._n(nt, "ShaderNodeTexWave", _wave_type="BANDS", _bands_direction="Z", Scale=140.0, Distortion=10.0, Detail=6.0)
    nt.links.new(wv.outputs[0], fib.inputs["Vector"])
    # veins: thin branching lines where a warped noise crosses its middle value (marble-like), not voronoi cells
    vn = W._n(nt, "ShaderNodeTexNoise", Scale=5.0, Detail=8.0, Roughness=0.6)
    nt.links.new(wv.outputs[0], vn.inputs["Vector"])
    vd = W._n(nt, "ShaderNodeMath", _operation="SUBTRACT"); vd.inputs[1].default_value = 0.5
    nt.links.new(vn.outputs["Fac"], vd.inputs[0])
    va = W._n(nt, "ShaderNodeMath", _operation="ABSOLUTE"); nt.links.new(vd.outputs[0], va.inputs[0])
    vmask = W._n(nt, "ShaderNodeMapRange"); vmask.inputs[1].default_value = 0.0; vmask.inputs[2].default_value = 0.012
    vmask.inputs[3].default_value = 1.0; vmask.inputs[4].default_value = 0.0
    nt.links.new(va.outputs[0], vmask.inputs[0])
    if ash:
        flesh = W._ramp(nt, fib.outputs["Fac"], (0.12, 0.12, 0.13), (0.32, 0.31, 0.3), 0.2, 0.9)
        vein_rgb = (0.05, 0.05, 0.06)
    else:
        flesh = W._ramp(nt, fib.outputs["Fac"], (0.05, 0.009, 0.008), (0.15, 0.032, 0.024), 0.3, 0.8)
        vein_rgb = (0.06, 0.01, 0.07)
    mix = W._n(nt, "ShaderNodeMix", _data_type="RGBA"); mix.inputs[7].default_value = (*vein_rgb, 1)   # 0 factor, 6/7 colours A/B
    nt.links.new(vmask.outputs[0], mix.inputs[0]); nt.links.new(flesh, mix.inputs[6])
    b = W._n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.32 if not ash else 0.85)
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    if not ash:
        b.inputs["Subsurface Weight"].default_value = 0.15
        b.inputs["Subsurface Radius"].default_value = (0.4, 0.08, 0.05)
    if lava:
        b.inputs["Emission Color"].default_value = (*CORE, 1)
        es = W._n(nt, "ShaderNodeMath", _operation="MULTIPLY"); es.inputs[1].default_value = lava
        nt.links.new(vmask.outputs[0], es.inputs[0]); nt.links.new(es.outputs[0], b.inputs["Emission Strength"])
    h = W._n(nt, "ShaderNodeMath", _operation="SUBTRACT")
    nt.links.new(fib.outputs["Fac"], h.inputs[0]); nt.links.new(vmask.outputs[0], h.inputs[1])
    bu = W._n(nt, "ShaderNodeBump", Strength=0.35, Distance=0.002)
    nt.links.new(h.outputs[0], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def horn_mat(name="vael_horn", ash=False):
    m, nt, out = W._blank(name)
    tc = W._n(nt, "ShaderNodeTexCoord")
    sep = W._n(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    rings = W._n(nt, "ShaderNodeTexWave", _wave_type="RINGS", Scale=9.0, Distortion=2.0)
    nt.links.new(tc.outputs["Object"], rings.inputs["Vector"])
    col = W._ramp(nt, rings.outputs["Fac"], (0.03, 0.025, 0.022) if not ash else (0.1, 0.1, 0.1),
                  (0.14, 0.12, 0.1) if not ash else (0.35, 0.35, 0.36), 0.3, 1.0)
    b = W._n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.38); nt.links.new(col, b.inputs["Base Color"])
    bu = W._n(nt, "ShaderNodeBump", Strength=0.4); nt.links.new(rings.outputs["Fac"], bu.inputs["Height"])
    nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ parts
def _cone_along(f, mat, base, d, length, r, bone, name):
    """A tapered cone from `base` along direction `d` (a spike, a claw), riding on `bone`."""
    d = Vector(d).normalized()
    bpy.ops.mesh.primitive_cone_add(vertices=10, radius1=r, radius2=0.0, depth=length, location=Vector(base) + d * length / 2)
    o = bpy.context.object; o.name = name
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(mat); bpy.ops.object.shade_smooth()
    H.on_bone(o, f.rig, bone); f.add(o)
    return o


def horns(f, mat):
    """Two long horns from the temples: out, up and curving in at the tips, ridged, tapering to points."""
    e = f.eye; top = f.J["head-2"].z; hy = f.J["head"].y
    for sd in (1, -1):
        pts = [(0.055, hy - 0.02, top - 0.04), (0.11, hy, top + 0.04), (0.17, hy + 0.02, top + 0.17),
               (0.18, hy + 0.03, top + 0.32), (0.14, hy + 0.01, top + 0.45), (0.09, hy - 0.02, top + 0.52)]
        cu = bpy.data.curves.new("vael_horn", "CURVE"); cu.dimensions = "3D"
        cu.bevel_depth = 0.034; cu.bevel_resolution = 4; cu.resolution_u = 12; cu.use_fill_caps = True
        sp = cu.splines.new("NURBS"); sp.points.add(len(pts) - 1); sp.order_u = 4; sp.use_endpoint_u = True
        for i, (x, y, z) in enumerate(pts):
            sp.points[i].co = (sd * x, y, z, 1.0); sp.points[i].radius = 1.0 - 0.92 * i / (len(pts) - 1)
        o = bpy.data.objects.new("vael_horn", cu); C.sc.collection.objects.link(o)
        cu.materials.append(mat); H.on_bone(o, f.rig, "head"); f.add(o)


def spike_fan(f, mat, n=15, seed=2):
    """A fan of thin spikes standing out behind the head and from the tops of the shoulders."""
    R = random.Random(seed)
    hc = Vector((0, f.J["head"].y + 0.03, (f.J["head"].z + f.J["head-2"].z) / 2 + 0.02))
    for i in range(n):
        a = math.radians(-80 + 160 * i / (n - 1)) + R.uniform(-0.05, 0.05)
        d = Vector((math.sin(a), 0.35, math.cos(a) * 0.9))
        _cone_along(f, mat, hc + d.normalized() * 0.07, d, R.uniform(0.14, 0.26), 0.009, "head", "vael_spike")
    for sd in (1, -1):   # on top of the shoulders, riding the chest so they stay put when the arms move
        for i in range(5):
            base = Vector((sd * (f.sh.x - 0.07 + 0.025 * i), f.J["spine-1"].y + 0.03, f.sh.z + 0.045))
            d = Vector((sd * (0.25 + 0.2 * i), 0.3, 1.0))
            _cone_along(f, mat, base, d, R.uniform(0.12, 0.22), 0.012, "chest", "vael_spike")


def claws(f, mat):
    """Black hooked claws past the fingertips and toes."""
    for k, s in (("l-", ".l"), ("r-", ".r")):
        for i in range(1, 6):
            tip = f.J["%sfinger-%d-4" % (k, i)]
            sd = 1 if s == ".l" else -1
            _cone_along(f, mat, tip, (sd * 1.0, -0.15, -0.55), 0.07 if i > 1 else 0.05, 0.008, "hand" + s, "vael_claw")
        toe = f.J[k + "foot-2"]
        for dx in (-0.03, 0.0, 0.03):
            _cone_along(f, mat, toe + Vector((dx, 0.02, 0.01)), (dx * 4, -1.0, -0.35), 0.07, 0.01, "toes" + s, "vael_claw")


def _torso_section(body, z, half_w):
    """Front y, back y and half width of the torso at height z, from the body mesh (rest pose)."""
    vs = [v.co for v in body.data.vertices if abs(v.co.z - z) < 0.02 and abs(v.co.x) < half_w]
    if not vs:
        return None
    return min(v.y for v in vs), max(v.y for v in vs), max(abs(v.x) for v in vs)


def ribcage(f, mat, n=5):
    """Bone ribs across the front of the chest, standing a little proud of the flesh, over the open core."""
    J = f.J; hi = J["neck"].z - 0.12; lo = J["spine-1"].z - 0.05
    for i in range(n):
        z = hi - (hi - lo) * i / (n - 1)
        sec = _torso_section(f.body, z, f.sh.x * 0.85)
        if not sec:
            continue
        front, back, hw = sec; cy = (front + back) / 2; dp = (back - front) / 2
        w = 0.82 - 0.08 * abs(i - n // 2)   # the middle ribs wrap furthest round
        pts = []
        for k in range(15):
            t = math.radians(-80 * w + 160 * w * k / 14)
            pts.append((hw * 1.02 * math.sin(t), cy - dp * 1.04 * math.cos(t), z - 0.012 * abs(math.sin(t))))
        cu = bpy.data.curves.new("vael_rib", "CURVE"); cu.dimensions = "3D"; cu.bevel_depth = 0.011; cu.bevel_resolution = 3
        sp = cu.splines.new("POLY"); sp.points.add(len(pts) - 1)
        for j, p in enumerate(pts):
            sp.points[j].co = (*p, 1.0); sp.points[j].radius = 1.0 - 0.45 * abs(j - 7) / 7
        o = bpy.data.objects.new("vael_rib", cu); C.sc.collection.objects.link(o)
        cu.materials.append(mat); H.on_bone(o, f.rig, "chest"); f.add(o)


def molten_core(f, rgb=CORE, size=0.075, energy=50, blaze=1.0):
    """Open the chest (a boolean cut on the chest bone) and set the lantern in it as a burning core."""
    J = f.J
    cz = (J["spine-1"].z + J["spine-2"].z) / 2 + 0.04
    sec = _torso_section(f.body, cz, f.sh.x * 0.6)
    front = sec[0] if sec else J["spine-1"].y - 0.12
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, front + 0.02, cz))
    cut = bpy.context.object; cut.name = "core_cutter"; cut.scale = (size * 1.1, size * 0.9, size * 1.6)
    bpy.ops.object.transform_apply(scale=True); cut.hide_render = True; cut.display_type = "WIRE"
    H.on_bone(cut, f.rig, "chest")
    b = f.body.modifiers.new("core_hole", "BOOLEAN"); b.object = cut; b.operation = "DIFFERENCE"; b.solver = "EXACT"
    # after the armature, like Gorrath's chest hole: the cutter rides the chest bone, so posed cuts posed
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, front + 0.045, cz))
    core = bpy.context.object; core.name = "vael_core"; core.scale = (size * 0.85, size * 0.6, size * 1.35)
    M = W.flame_mat("core_fire", rgb, 25.0 * blaze)
    inner = H.glow_mat("core_heat", (1.0, 0.85, 0.55), 12 * blaze)
    core.data.materials.append(inner); bpy.ops.object.shade_smooth(); H.on_bone(core, f.rig, "chest"); f.add(core)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, front + 0.03, cz))
    halo = bpy.context.object; halo.name = "vael_core_fire"; halo.scale = (size * 1.05, size * 0.75, size * 1.55)
    halo.data.materials.append(M); bpy.ops.object.shade_smooth(); H.on_bone(halo, f.rig, "chest"); f.add(halo)
    W.point_light(f, "core_light", (0, front - 0.12, cz), rgb, energy * blaze, "chest", 0.06)


def face_shell(f, mat):
    """An angular mask over the whole face: the face skin copied, lifted off it and decimated into hard facets, with
    holes for the eyes and the mouth. It rides on the head bone, so no human face shows through."""
    e = f.eye; m = f.mouth; body = f.body
    eyes = [Vector((sx * abs(e.x), e.y, e.z)) for sx in (1, -1)]
    keep = lambda c: (c.z > f.jaw.z - 0.04 and c.y < e.y + 0.04 and abs(c.x) < 0.09 and c.z < e.z + 0.11
                      and min((c - q).length for q in eyes) > 0.019 and not (abs(c.z - m.z) < 0.007 and abs(c.x) < 0.026))
    bm = bmesh.new(); bm.from_mesh(body.data); bm.normal_update()
    bmesh.ops.delete(bm, geom=[p for p in bm.faces if not all(keep(v.co) for v in p.verts)], context="FACES")
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
    for v in bm.verts:
        v.co += v.normal * 0.006
    me = bpy.data.meshes.new("vael_face_shell"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("vael_face_shell", me); C.sc.collection.objects.link(o)
    o.data.materials.clear(); o.data.materials.append(mat)
    d = o.modifiers.new("facets", "DECIMATE"); d.ratio = 0.12
    so = o.modifiers.new("thick", "SOLIDIFY"); so.thickness = 0.005; so.offset = 1.0
    H.on_bone(o, f.rig, "head"); f.add(o)


def mask_face(f, mat, mouth_rgb=CORE):
    """An angular dark mask over the face: heavy V brows, cheek blades, a jaw plate split by a glowing mouth of teeth."""
    e = f.eye; m = f.mouth; R = random.Random(5)
    pieces = [((0.03, e.y - 0.014, e.z + 0.021), (0.03, 0.012, 0.007), -0.42),     # V brows angled down to the nose
              ((-0.03, e.y - 0.014, e.z + 0.021), (0.03, 0.012, 0.007), 0.42),
              ((0.058, e.y + 0.008, e.z - 0.038), (0.011, 0.028, 0.022), 0.0),     # cheek blades
              ((-0.058, e.y + 0.008, e.z - 0.038), (0.011, 0.028, 0.022), 0.0),
              ((0.0, e.y - 0.02, e.z - 0.012), (0.008, 0.014, 0.024), 0.0),        # nose ridge
              ((0.0, e.y - 0.004, e.z + 0.062), (0.05, 0.02, 0.028), 0.0)]         # brow-plate up into the horns
    for (x, y, z), sc, rot in pieces:
        bpy.ops.mesh.primitive_cube_add(size=2, location=(x, y, z))
        o = bpy.context.object; o.name = "vael_mask"; o.scale = sc; o.rotation_euler = (0, rot, 0)
        bv = o.modifiers.new("bev", "BEVEL"); bv.width = 0.003; bv.segments = 2
        o.data.materials.append(mat); H.on_bone(o, f.rig, "head"); f.add(o)
    # the mouth: a glowing slot with a row of teeth top and bottom
    glow = H.glow_mat("vael_mouth", mouth_rgb, 14)
    bpy.ops.mesh.primitive_cube_add(size=2, location=(0, m.y - 0.012, m.z - 0.004))
    sl = bpy.context.object; sl.name = "vael_mouth"; sl.scale = (0.03, 0.01, 0.012)
    sl.data.materials.append(glow); H.on_bone(sl, f.rig, "head"); f.add(sl)
    TEETH = C.mat("vael_teeth", (0.75, 0.7, 0.6), 0.4)
    for k in range(7):
        x = -0.026 + 0.0087 * k
        for zz, dz in ((m.z + 0.008, -1), (m.z - 0.016, 1)):
            _cone_along(f, TEETH, (x, m.y - 0.022, zz), (0, -0.1, dz), 0.012 + 0.004 * R.random(), 0.0035, "head", "vael_tooth")
    W.point_light(f, "mouth_glow", (0, m.y - 0.035, m.z + 0.01), mouth_rgb, 0.5, "head", 0.02)


def shoulder_fire(f, rgb=(1.0, 0.4, 0.05), white=False):
    """Fire burning up off the shoulders (the Wrath), or white fire in the hands (the Unmade)."""
    M = W.flame_mat("vael_fire", rgb, 8.0)
    R = random.Random(9)
    sites = ([(sd * (f.sh.x + 0.02 + 0.04 * i), f.J["spine-1"].y + 0.03, f.sh.z + 0.03, "upperarm" + s)
              for sd, s in ((1, ".l"), (-1, ".r")) for i in range(4)] if not white else
             [(sd * (f.wr.x + 0.06 + 0.03 * i), f.wr.y, f.wr.z + 0.03, "hand" + s) for sd, s in ((1, ".l"), (-1, ".r")) for i in range(3)])
    for x, y, z, bone in sites:
        h = R.uniform(0.25, 0.42)
        bpy.ops.mesh.primitive_cone_add(vertices=16, radius1=0.05, radius2=0.002, depth=h, location=(x, y, z + h / 2))
        o = bpy.context.object; o.name = "vael_fire"; o.scale.y = 0.6
        tw = o.modifiers.new("lick", "SIMPLE_DEFORM"); tw.deform_method = "TWIST"; tw.angle = R.uniform(-1.5, 1.5)
        o.modifiers.new("sub", "SUBSURF").levels = 2
        o.data.materials.append(M); bpy.ops.object.shade_smooth(); H.on_bone(o, f.rig, bone); f.add(o)
    W.point_light(f, "fire_light", (0, f.J["spine-1"].y, f.sh.z + 0.25), rgb, 40, "chest", 0.3)


# ------------------------------------------------------------------ the forms
def vael_orrun(rig, body, ex, J, form="king"):
    f = Fig(rig, body, ex, J)
    ash = form == "unmade"
    W.skin_as(body, raw_flesh("vael_flesh_" + form, lava=6.0 if form == "wrath" else 0.0, ash=ash))
    W.lumpy(body, 0.05, 0.008, "VORONOI", "sinew")
    eye_rgb = (1.0, 0.95, 0.8) if not ash else (0.85, 0.9, 1.0)
    W.glow_eyes(f, eye_rgb, 40, 1.2, 0.9)
    HORN = horn_mat("vael_horn_" + form, ash)
    MASK = C.mat("vael_mask_" + form, (0.04, 0.012, 0.01) if not ash else (0.16, 0.16, 0.17), 0.45)
    # the whole face is the dark mask (no human face left), the plates below stand out of it
    e = f.eye
    W.face_poly_material(body, MASK, lambda c: c.z > f.jaw.z - 0.035 and c.y < e.y + 0.035 and abs(c.x) < 0.085
                         and c.z < e.z + 0.1)
    face_shell(f, MASK)
    mask_face(f, MASK, CORE if not ash else (0.75, 0.8, 1.0))
    horns(f, HORN)
    spike_fan(f, HORN)
    claws(f, C.mat("vael_claw", (0.015, 0.012, 0.012), 0.25))
    BONE = C.mat("vael_bone_" + form, (0.32, 0.29, 0.25) if not ash else (0.6, 0.6, 0.62), 0.55)
    molten_core(f, CORE if not ash else (0.8, 0.85, 1.0), blaze={"king": 1.0, "wrath": 2.2, "unmade": 0.7}[form])
    ribcage(f, BONE)
    if form == "wrath":
        shoulder_fire(f)
    elif ash:
        shoulder_fire(f, (0.8, 0.85, 1.0), white=True)
    return [body] + f.parts


_PROPS = dict(height=2.3, gender=1.0, muscle=1.0, weight=0.95, tall=0.85, age=0.5, proportions=0.4)   # broad, heavy with muscle
_POST = dict(H.HUMAN_POSTURE, chest=(8.0, (1, 0, 0)), head=(-6.0, (1, 0, 0)))
for _k, _form in (("vael_orrun", "king"), ("vael_orrun_wrath", "wrath"), ("vael_orrun_unmade", "unmade")):
    H.HUMANS[_k] = (_PROPS, (lambda fm: lambda r, b, e, j: vael_orrun(r, b, e, j, form=fm))(_form))
    H.SCALE[_k] = 2.3
    H.POSTURES[_k] = _POST
