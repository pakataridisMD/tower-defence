"""The six Wardens on real bodies: Ignar (basalt and fire), Aurath (storm cloud), Elowen (bark and blossom),
Thalassa (sea-glass), Orrok (mountain stone) and Nyxara (a starfield face). Built at human size on the KayKit rig,
so every animation works, then scaled up whole by hero.SCALE. Importing registers them with hero.build_human().

Looks follow /mnt/project-files/lore/characters.md (story canon v2).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import cine3d as C
import hero as H
import cast as K
from cast import Fig


# ------------------------------------------------------------------ node helpers
def _blank(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    return m, nt, out


def _n(nt, kind, **inputs):
    n = nt.nodes.new(kind)
    for k, v in inputs.items():
        if k.startswith("_"):
            setattr(n, k[1:], v)
        else:
            n.inputs[k].default_value = v
    return n


def _ramp(nt, fac, a, b, lo=0.0, hi=1.0):
    r = nt.nodes.new("ShaderNodeValToRGB")
    r.color_ramp.elements[0].position = lo; r.color_ramp.elements[0].color = (*a, 1)
    r.color_ramp.elements[1].position = hi; r.color_ramp.elements[1].color = (*b, 1)
    nt.links.new(fac, r.inputs[0])
    return r.outputs[0]


def _animate_w(node, per_frame=1 / 96):
    """Drive a 4D noise's W by the frame, so it drifts slowly (cloud edges, currents)."""
    d = node.inputs["W"].driver_add("default_value").driver
    d.expression = "frame*%f" % per_frame


def _moss(nt, base_col, amount=0.55, rgb=(0.06, 0.11, 0.03)):
    """Moss on the upward faces: mixes `base_col` toward green where the normal points up."""
    geo = _n(nt, "ShaderNodeNewGeometry")
    sep = _n(nt, "ShaderNodeSeparateXYZ"); nt.links.new(geo.outputs["Normal"], sep.inputs[0])
    tc = _n(nt, "ShaderNodeTexCoord")
    no = _n(nt, "ShaderNodeTexNoise", Scale=9.0, Detail=8.0)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"])
    a = _n(nt, "ShaderNodeMath", _operation="MULTIPLY"); nt.links.new(sep.outputs["Z"], a.inputs[0]); nt.links.new(no.outputs["Fac"], a.inputs[1])
    m = _n(nt, "ShaderNodeMapRange"); m.inputs[1].default_value = 0.18; m.inputs[2].default_value = 0.42
    nt.links.new(a.outputs[0], m.inputs[0])
    k = _n(nt, "ShaderNodeMath", _operation="MULTIPLY"); k.inputs[1].default_value = amount; nt.links.new(m.outputs[0], k.inputs[0])
    mx = _n(nt, "ShaderNodeMix", _data_type="RGBA"); mx.inputs[7].default_value = (*rgb, 1)
    nt.links.new(k.outputs[0], mx.inputs["Factor"]); nt.links.new(base_col, mx.inputs[6])
    return mx.outputs[2]


# ------------------------------------------------------------------ materials
def basalt(name, core, crack_rgb=(1.0, 0.33, 0.05), crack_w=0.008, glow=4.0, core_glow=40.0, grey=False):
    """Black basalt cracked with fire. `core`: the point (object space) the cracks widen and brighten toward."""
    m, nt, out = _blank(name)
    tc = _n(nt, "ShaderNodeTexCoord")
    warp = _n(nt, "ShaderNodeTexNoise", Scale=3.0, Detail=4.0)
    nt.links.new(tc.outputs["Object"], warp.inputs["Vector"])
    wv = _n(nt, "ShaderNodeVectorMath", _operation="MULTIPLY_ADD"); wv.inputs[1].default_value = (0.08, 0.08, 0.08)
    nt.links.new(warp.outputs["Color"], wv.inputs[0]); nt.links.new(tc.outputs["Object"], wv.inputs[2])
    vo = _n(nt, "ShaderNodeTexVoronoi", _feature="DISTANCE_TO_EDGE", Scale=5.0)
    nt.links.new(wv.outputs[0], vo.inputs["Vector"])
    dist = _n(nt, "ShaderNodeVectorMath", _operation="DISTANCE"); dist.inputs[1].default_value = core
    nt.links.new(tc.outputs["Object"], dist.inputs[0])
    near = _n(nt, "ShaderNodeMapRange"); near.inputs[1].default_value = 0.04; near.inputs[2].default_value = 0.3
    near.inputs[3].default_value = 1.0; near.inputs[4].default_value = 0.0
    nt.links.new(dist.outputs["Value"], near.inputs[0])
    w = _n(nt, "ShaderNodeMath", _operation="MULTIPLY_ADD"); w.inputs[1].default_value = crack_w * 3; w.inputs[2].default_value = crack_w
    nt.links.new(near.outputs[0], w.inputs[0])
    crack = _n(nt, "ShaderNodeMapRange"); crack.inputs[1].default_value = 0.0; crack.inputs[3].default_value = 1.0; crack.inputs[4].default_value = 0.0
    nt.links.new(vo.outputs["Distance"], crack.inputs[0]); nt.links.new(w.outputs[0], crack.inputs[2])
    strength = _n(nt, "ShaderNodeMath", _operation="MULTIPLY_ADD"); strength.inputs[1].default_value = core_glow; strength.inputs[2].default_value = glow
    nt.links.new(near.outputs[0], strength.inputs[0])
    es = _n(nt, "ShaderNodeMath", _operation="MULTIPLY"); nt.links.new(crack.outputs[0], es.inputs[0]); nt.links.new(strength.outputs[0], es.inputs[1])
    rock = _n(nt, "ShaderNodeTexNoise", Scale=18.0, Detail=12.0, Roughness=0.7)
    nt.links.new(tc.outputs["Object"], rock.inputs["Vector"])
    col = _ramp(nt, rock.outputs["Fac"], (0.012, 0.011, 0.011) if not grey else (0.05, 0.05, 0.05),
                (0.05, 0.045, 0.042) if not grey else (0.14, 0.14, 0.14), 0.35, 0.7)
    b = _n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.72)
    nt.links.new(col, b.inputs["Base Color"])
    b.inputs["Emission Color"].default_value = (*crack_rgb, 1)
    nt.links.new(es.outputs[0], b.inputs["Emission Strength"])
    h = _n(nt, "ShaderNodeMath", _operation="ADD"); nt.links.new(rock.outputs["Fac"], h.inputs[0]); nt.links.new(vo.outputs["Distance"], h.inputs[1])
    bu = _n(nt, "ShaderNodeBump", Strength=0.8); nt.links.new(h.outputs[0], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def storm_cloud(name, rgb=(0.22, 0.24, 0.29), density=40.0, bolt_rgb=(0.75, 0.85, 1.0), bolts=35.0, black=False):
    """A body of cloud: a volume with drifting density, its surface clear except for branching lightning veins."""
    m, nt, out = _blank(name)
    tc = _n(nt, "ShaderNodeTexCoord")
    no = _n(nt, "ShaderNodeTexNoise", _noise_dimensions="4D", Scale=11.0, Detail=12.0, Roughness=0.65)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"]); _animate_w(no)
    dm = _n(nt, "ShaderNodeMapRange"); dm.inputs[1].default_value = 0.42; dm.inputs[2].default_value = 0.68
    dm.inputs[3].default_value = 0.0; dm.inputs[4].default_value = density
    nt.links.new(no.outputs["Fac"], dm.inputs[0])
    vol = _n(nt, "ShaderNodeVolumePrincipled", Anisotropy=0.3)
    vol.inputs["Color"].default_value = (*((0.03, 0.03, 0.035) if black else rgb), 1)
    nt.links.new(dm.outputs[0], vol.inputs["Density"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    # lightning: thin, warped voronoi edges
    warp = _n(nt, "ShaderNodeTexNoise", _noise_dimensions="4D", Scale=6.0, Detail=6.0)
    nt.links.new(tc.outputs["Object"], warp.inputs["Vector"]); _animate_w(warp, 1 / 24)
    wv = _n(nt, "ShaderNodeVectorMath", _operation="MULTIPLY_ADD"); wv.inputs[1].default_value = (0.12, 0.12, 0.12)
    nt.links.new(warp.outputs["Color"], wv.inputs[0]); nt.links.new(tc.outputs["Object"], wv.inputs[2])
    vo = _n(nt, "ShaderNodeTexVoronoi", _feature="DISTANCE_TO_EDGE", Scale=4.0)
    nt.links.new(wv.outputs[0], vo.inputs["Vector"])
    th = _n(nt, "ShaderNodeMath", _operation="LESS_THAN"); th.inputs[1].default_value = 0.0035
    nt.links.new(vo.outputs["Distance"], th.inputs[0])
    tr = _n(nt, "ShaderNodeBsdfTransparent")
    em = _n(nt, "ShaderNodeEmission", Strength=bolts); em.inputs["Color"].default_value = (*bolt_rgb, 1)
    mx = _n(nt, "ShaderNodeMixShader"); nt.links.new(th.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def bark(name, rgb_dark=(0.05, 0.04, 0.03), rgb_light=(0.2, 0.17, 0.13), moss=0.55, grey=False):
    """Old bark, deep vertical furrows, moss in the upward hollows."""
    m, nt, out = _blank(name)
    tc = _n(nt, "ShaderNodeTexCoord")
    wv = _n(nt, "ShaderNodeTexWave", _wave_type="BANDS", _bands_direction="X", Scale=14.0, Distortion=9.0, Detail=6.0)
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    no = _n(nt, "ShaderNodeTexNoise", Scale=30.0, Detail=10.0)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"])
    h = _n(nt, "ShaderNodeMath", _operation="MULTIPLY"); nt.links.new(wv.outputs["Fac"], h.inputs[0]); nt.links.new(no.outputs["Fac"], h.inputs[1])
    if grey:
        rgb_dark, rgb_light = (0.07, 0.07, 0.07), (0.3, 0.29, 0.28)
    col = _ramp(nt, h.outputs[0], rgb_dark, rgb_light, 0.1, 0.5)
    if moss:
        col = _moss(nt, col, moss)
    b = _n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.9)
    nt.links.new(col, b.inputs["Base Color"])
    bu = _n(nt, "ShaderNodeBump", Strength=1.0); nt.links.new(h.outputs[0], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def sea_glass(name, rgb=(0.6, 0.9, 0.86), currents=(0.55, 0.9, 0.85)):
    """Translucent sea-glass with slow currents moving inside."""
    m, nt, out = _blank(name)
    b = _n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.12, IOR=1.33)
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Transmission Weight"].default_value = 1.0
    tc = _n(nt, "ShaderNodeTexCoord")
    fr = _n(nt, "ShaderNodeTexNoise", Scale=60.0, Detail=4.0)
    nt.links.new(tc.outputs["Object"], fr.inputs["Vector"])
    bu = _n(nt, "ShaderNodeBump", Strength=0.08); nt.links.new(fr.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    no = _n(nt, "ShaderNodeTexNoise", _noise_dimensions="4D", Scale=3.0, Detail=3.0)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"]); _animate_w(no, 1 / 120)
    wv = _n(nt, "ShaderNodeTexWave", _wave_type="RINGS", Scale=3.0, Distortion=12.0, Detail=3.0)
    nt.links.new(no.outputs["Color"], wv.inputs["Vector"])
    th = _n(nt, "ShaderNodeMapRange"); th.inputs[1].default_value = 0.8; th.inputs[2].default_value = 1.0
    th.inputs[3].default_value = 0.0; th.inputs[4].default_value = 6.0
    nt.links.new(wv.outputs["Fac"], th.inputs[0])
    vol = _n(nt, "ShaderNodeVolumePrincipled")
    vol.inputs["Color"].default_value = (*currents, 1); vol.inputs["Absorption Color"].default_value = (*rgb, 1)
    vol.inputs["Emission Color"].default_value = (*currents, 1); vol.inputs["Emission Strength"].default_value = 0.0
    nt.links.new(th.outputs[0], vol.inputs["Density"])
    em = _n(nt, "ShaderNodeMath", _operation="MULTIPLY"); em.inputs[1].default_value = 0.08
    nt.links.new(th.outputs[0], em.inputs[0]); nt.links.new(em.outputs[0], vol.inputs["Emission Strength"])
    nt.links.new(vol.outputs[0], out.inputs["Volume"])
    return m


def mountain_stone(name, rgb=(0.3, 0.28, 0.25), moss=0.7, lichen=False):
    m, nt, out = _blank(name)
    tc = _n(nt, "ShaderNodeTexCoord")
    vo = _n(nt, "ShaderNodeTexVoronoi", Scale=5.0)
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    no = _n(nt, "ShaderNodeTexNoise", Scale=12.0, Detail=12.0, Roughness=0.65)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"])
    h = _n(nt, "ShaderNodeMath", _operation="ADD"); nt.links.new(vo.outputs["Distance"], h.inputs[0]); nt.links.new(no.outputs["Fac"], h.inputs[1])
    col = _ramp(nt, no.outputs["Fac"], tuple(c * 0.45 for c in rgb), rgb, 0.3, 0.75)
    if moss:
        col = _moss(nt, col, moss, (0.12, 0.13, 0.11) if lichen else (0.05, 0.1, 0.03))
    b = _n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.88)
    nt.links.new(col, b.inputs["Base Color"])
    bu = _n(nt, "ShaderNodeBump", Strength=0.9); nt.links.new(h.outputs[0], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m


def starfield(name, cloth=False, black=False, sc=(90.0, 35.0), nebula=0.12, big=1.0):
    """Night sky: black with fine stars and a faint violet nebula (Nyxara's face and train)."""
    m, nt, out = _blank(name)
    tc = _n(nt, "ShaderNodeTexCoord")
    em_total = None
    for sc, size, s in ((sc[0], 0.05 * big, 16.0), (sc[1], 0.045 * big, 40.0)):
        vo = _n(nt, "ShaderNodeTexVoronoi", _feature="F1", Scale=sc, Randomness=1.0)
        nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
        th = _n(nt, "ShaderNodeMapRange"); th.inputs[1].default_value = size; th.inputs[2].default_value = 0.0
        th.inputs[3].default_value = 0.0; th.inputs[4].default_value = s
        nt.links.new(vo.outputs["Distance"], th.inputs[0])
        # only some cells hold a star
        keep = _n(nt, "ShaderNodeMath", _operation="GREATER_THAN"); keep.inputs[1].default_value = 0.55
        sep = _n(nt, "ShaderNodeSeparateColor"); nt.links.new(vo.outputs["Color"], sep.inputs[0]); nt.links.new(sep.outputs[0], keep.inputs[0])
        k = _n(nt, "ShaderNodeMath", _operation="MULTIPLY"); nt.links.new(th.outputs[0], k.inputs[0]); nt.links.new(keep.outputs[0], k.inputs[1])
        if em_total is None:
            em_total = k
        else:
            a = _n(nt, "ShaderNodeMath", _operation="ADD"); nt.links.new(em_total.outputs[0], a.inputs[0]); nt.links.new(k.outputs[0], a.inputs[1]); em_total = a
    if black:
        z = _n(nt, "ShaderNodeMath", _operation="MULTIPLY"); z.inputs[1].default_value = 0.0
        nt.links.new(em_total.outputs[0], z.inputs[0]); em_total = z
    neb = _n(nt, "ShaderNodeTexNoise", Scale=2.5, Detail=8.0)
    nt.links.new(tc.outputs["Object"], neb.inputs["Vector"])
    nm = _n(nt, "ShaderNodeMapRange"); nm.inputs[1].default_value = 0.5; nm.inputs[2].default_value = 0.75
    nm.inputs[3].default_value = 0.0; nm.inputs[4].default_value = 0.0 if black else nebula
    nt.links.new(neb.outputs["Fac"], nm.inputs[0])
    b = _n(nt, "ShaderNodeBsdfPrincipled", Roughness=0.85 if cloth else 0.35)
    b.inputs["Base Color"].default_value = (0.004, 0.004, 0.006, 1)
    if cloth:
        b.inputs["Sheen Weight"].default_value = 0.4; b.inputs["Sheen Tint"].default_value = (0.3, 0.25, 0.5, 1)
    e1 = _n(nt, "ShaderNodeEmission"); e1.inputs["Color"].default_value = (0.9, 0.92, 1.0, 1)
    nt.links.new(em_total.outputs[0], e1.inputs["Strength"])
    e2 = _n(nt, "ShaderNodeEmission"); e2.inputs["Color"].default_value = (0.35, 0.18, 0.6, 1)
    nt.links.new(nm.outputs[0], e2.inputs["Strength"])
    a1 = _n(nt, "ShaderNodeAddShader"); nt.links.new(b.outputs[0], a1.inputs[0]); nt.links.new(e1.outputs[0], a1.inputs[1])
    a2 = _n(nt, "ShaderNodeAddShader"); nt.links.new(a1.outputs[0], a2.inputs[0]); nt.links.new(e2.outputs[0], a2.inputs[1])
    nt.links.new(a2.outputs[0], out.inputs["Surface"])
    return m


def flame_mat(name, rgb=(1.0, 0.45, 0.08), strength=12.0):
    """A soft flame: emission fading to clear toward the tip (object Z) with flicker noise."""
    m, nt, out = _blank(name)
    tc = _n(nt, "ShaderNodeTexCoord")
    sep = _n(nt, "ShaderNodeSeparateXYZ"); nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    no = _n(nt, "ShaderNodeTexNoise", _noise_dimensions="4D", Scale=6.0, Detail=3.0)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"]); _animate_w(no, 1 / 12)
    f = _n(nt, "ShaderNodeMath", _operation="SUBTRACT"); nt.links.new(no.outputs["Fac"], f.inputs[0]); nt.links.new(sep.outputs["Z"], f.inputs[1])
    a = _n(nt, "ShaderNodeMapRange"); a.inputs[1].default_value = -0.4; a.inputs[2].default_value = 0.3
    nt.links.new(f.outputs[0], a.inputs[0])
    tr = _n(nt, "ShaderNodeBsdfTransparent")
    em = _n(nt, "ShaderNodeEmission", Strength=strength); em.inputs["Color"].default_value = (*rgb, 1)
    mx = _n(nt, "ShaderNodeMixShader"); nt.links.new(a.outputs[0], mx.inputs[0])
    nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(em.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def bronze_green(name="drowned_bronze"):
    m = C.mat(name, (0.35, 0.3, 0.16), 0.45, metal=1.0)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = _n(nt, "ShaderNodeTexCoord"); no = _n(nt, "ShaderNodeTexNoise", Scale=40.0, Detail=6.0)
    nt.links.new(tc.outputs["Object"], no.inputs["Vector"])
    col = _ramp(nt, no.outputs["Fac"], (0.35, 0.28, 0.13), (0.12, 0.35, 0.28), 0.45, 0.6)
    nt.links.new(col, b.inputs["Base Color"])
    return m


# ------------------------------------------------------------------ shared parts
def skin_as(body, mat):
    body.data.materials.clear(); body.data.materials.append(mat)


def lumpy(o, scale=0.12, strength=0.025, kind="CLOUDS", name="lumps"):
    """Break up a smooth body into rock or bark with a displacement after the rig."""
    tx = bpy.data.textures.new(o.name + "_" + name, kind)
    if kind == "CLOUDS":
        tx.noise_scale = scale; tx.noise_depth = 3
    elif kind == "VORONOI":
        tx.noise_scale = scale
    elif kind == "WOOD":
        tx.wood_type = "BANDNOISE"; tx.noise_scale = scale; tx.turbulence = 6
    d = o.modifiers.new(name, "DISPLACE"); d.texture = tx; d.strength = strength; d.texture_coords = "OBJECT"; d.mid_level = 0.5
    return d


def glow_eyes(f, rgb, strength=20.0, light=1.0, scale=1.0, mat=None):
    """Eyes of light (embers, geodes, lightning): the eye helpers become glowing balls on the head bone."""
    M = mat or H.glow_mat("eye_light", rgb, strength)
    for h in f.ex:
        vs = [h.matrix_world @ v.co for v in h.data.vertices]
        c = sum(vs, Vector()) / len(vs); r = max((v - c).length for v in vs)
        bpy.data.objects.remove(h, do_unlink=True)
        bpy.ops.mesh.primitive_ico_sphere_add(radius=r * scale, location=c, subdivisions=2 if mat else 3)
        e = bpy.context.object; e.name = "warden_eye"; e.data.materials.append(M); H.on_bone(e, f.rig, "head"); f.add(e)
        if light:
            li = bpy.data.lights.new("eye_glow", "POINT"); li.energy = light; li.color = rgb; li.shadow_soft_size = 0.01
            lo = bpy.data.objects.new("eye_glow", li); C.sc.collection.objects.link(lo); lo.location = c + Vector((0, -0.04, 0))
            H.on_bone(lo, f.rig, "head"); f.add(lo)
    f.ex = []


def no_eyes(f):
    for h in f.ex:
        bpy.data.objects.remove(h, do_unlink=True)
    f.ex = []


def point_light(f, name, loc, rgb, energy, bone, size=0.1):
    li = bpy.data.lights.new(name, "POINT"); li.energy = energy; li.color = rgb; li.shadow_soft_size = size
    lo = bpy.data.objects.new(name, li); C.sc.collection.objects.link(lo); lo.location = loc
    H.on_bone(lo, f.rig, bone); f.add(lo)
    return lo


def flame_crown(f, n=13, r=0.1, h=0.2, rgb=(1.0, 0.45, 0.08), smoke=False):
    """A crown of slow flames standing on the head (Ignar). smoke: black smoke instead (the Cinder Tyrant)."""
    top = f.J["head-2"].z - 0.01; cy = f.J["head"].y + 0.005
    M = flame_mat("crown_flame", rgb, 1.6) if not smoke else C.mat("crown_smoke", (0.01, 0.01, 0.01), 1.0)
    for i in range(n):
        a = 2 * math.pi * i / n
        hh = h * (0.7 + 0.6 * ((i * 37) % 7) / 7)
        bpy.ops.mesh.primitive_cone_add(vertices=12, radius1=0.016, radius2=0.001, depth=hh,
                                        location=(math.cos(a) * r, cy + math.sin(a) * r * 0.9, top + hh / 2))
        o = bpy.context.object; o.name = "crown_flame"; o.rotation_euler = (math.sin(a) * -0.25, math.cos(a) * 0.25, 0)
        o.modifiers.new("sub", "SUBSURF").levels = 2
        o.data.materials.append(M); bpy.ops.object.shade_smooth(); H.on_bone(o, f.rig, "head"); f.add(o)
    if not smoke:
        point_light(f, "crown_fire", (0, cy, top + 0.12), rgb, 6, "head", 0.08)


def branch_crown(f, n=44, seed=3, blossom=(0.95, 0.93, 0.9), grey=False):
    """Branches for hair, growing up and back from the scalp, white blossom at the twig ends (Elowen)."""
    R = random.Random(seed)
    pts = H.scalp_points(f.body, f.scalp, n, seed=seed)
    cv = bpy.data.curves.new("branches", "CURVE"); cv.dimensions = "3D"
    cv.bevel_depth = 1.0; cv.bevel_resolution = 2; cv.use_fill_caps = True
    flowers = []

    def grow(p, d, length, r, depth):
        sp = cv.splines.new("POLY"); segs = 6
        sp.points.add(segs - 1)
        step = length / (segs - 1)
        for k in range(segs):
            sp.points[k].co = (*p, 1); sp.points[k].radius = r * (1 - 0.75 * k / (segs - 1))
            if depth == 0 and k in (2, 4) and R.random() < 0.8:
                nd = (d + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-0.2, 1))) * 0.9).normalized()
                grow(p.copy(), nd, length * 0.55, r * 0.55, 1)
            d = (d + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * 0.35).normalized()
            p = p + d * step
        flowers.append(p.copy())
        if depth == 1:
            for _ in range(2):
                flowers.append(p + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * 0.03)

    for p in pts:
        out = (p - f.hc); out.z = max(out.z, 0.0)
        d = (out.normalized() * 0.6 + Vector((0, 0.5, 0.75))).normalized()
        grow(Vector(p), d, R.uniform(0.25, 0.45), 0.014, 0)
    o = bpy.data.objects.new("branches", cv); C.sc.collection.objects.link(o)
    o.data.materials.append(bark("twig_bark", moss=0.0, grey=grey))
    H.on_bone(o, f.rig, "head"); f.add(o)
    bm = bmesh.new()
    for p in flowers:
        for _ in range(3):
            q = p + Vector((R.uniform(-1, 1), R.uniform(-1, 1), R.uniform(-1, 1))) * 0.012
            bmesh.ops.create_icosphere(bm, subdivisions=1, radius=R.uniform(0.007, 0.012), matrix=Matrix.Translation(q))
    me = bpy.data.meshes.new("blossom"); bm.to_mesh(me); bm.free()
    bl = bpy.data.objects.new("blossom", me); C.sc.collection.objects.link(bl)
    BM = C.mat("blossom", blossom if not grey else (0.4, 0.4, 0.42), 0.6)
    BM.node_tree.nodes["Principled BSDF"].inputs["Subsurface Weight"].default_value = 0.4
    bl.data.materials.append(BM); H.on_bone(bl, f.rig, "head"); f.add(bl)


def moss_strands(f, keep, count=5000, length=0.12, seed=21, rgb=(0.08, 0.13, 0.04)):
    """Moss trailing from the arms and shoulders."""
    f.add(H.comb_hair(f.rig, H.scalp_points(f.body, keep, count, seed=seed), f.hc, "moss", length, (0, 0, -1),
                      segs=5, lift=0.0, jitter=0.4, radius=0.0025, push=0.05, wrap_above=99.0, bone="chest", colour=rgb))


def bells_in_hair(f, n=14, seed=5):
    """Drowned bronze bells woven into Thalassa's floating hair."""
    R = random.Random(seed); BR = bronze_green()
    for i in range(n):
        d = Vector((R.uniform(-1, 1), R.uniform(0.2, 1.2), R.uniform(0.1, 1.2))).normalized()
        c = f.hc + d * R.uniform(0.2, 0.42)
        bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=0.016, radius2=0.007, depth=0.026, location=c)
        b = bpy.context.object; b.name = "bell"; b.rotation_euler = (R.uniform(-0.6, 0.6), R.uniform(-0.6, 0.6), 0)
        b.modifiers.new("thick", "SOLIDIFY").thickness = 0.002; b.modifiers.new("sub", "SUBSURF").levels = 1
        b.data.materials.append(BR); bpy.ops.object.shade_smooth(); H.on_bone(b, f.rig, "head"); f.add(b)


def pines(f, sites, seed=8, dead=False):
    """Small pines on a giant's shoulders: stacked cones on a trunk."""
    R = random.Random(seed)
    NEED = C.mat("pine_dead" if dead else "pine", (0.05, 0.035, 0.02) if dead else (0.025, 0.07, 0.03), 0.9)
    TR = C.mat("pine_trunk", (0.06, 0.04, 0.03), 0.9)
    for (x, y, z, bone) in sites:
        h = R.uniform(0.16, 0.34)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.004, depth=h * 0.4, location=(x, y, z + h * 0.2)); t = bpy.context.object
        t.data.materials.append(TR)
        tiers = []
        for k in range(7):
            rr = h * (0.3 - k * 0.038) * R.uniform(0.85, 1.15)
            bpy.ops.mesh.primitive_cone_add(vertices=14, radius1=rr, radius2=rr * 0.15, depth=h * 0.22, location=(x, y, z + h * (0.22 + k * 0.11)))
            c = bpy.context.object; c.rotation_euler = (R.uniform(-0.15, 0.15), R.uniform(-0.15, 0.15), R.uniform(0, 6.3)); tiers.append(c)
        for c in tiers:
            c.data.materials.append(NEED)
        tree = K._join([t] + tiers, "pine")
        d = tree.modifiers.new("ragged", "DISPLACE"); tx = bpy.data.textures.new("pine_rag", "CLOUDS"); tx.noise_scale = 0.006
        d.texture = tx; d.strength = 0.012
        H.on_bone(tree, f.rig, bone); f.add(tree)


def face_poly_material(body, mat, keep):
    """Give the faces whose vertices all pass `keep` a second material (Nyxara's starfield face)."""
    body.data.materials.append(mat); idx = len(body.data.materials) - 1
    vs = body.data.vertices
    for p in body.data.polygons:
        if all(keep(vs[i].co) for i in p.vertices):
            p.material_index = idx


def broken_crown(f, side=".l"):
    """The broken iron crown Nyxara carries in her hand."""
    IRON = C.mat("crown_iron", (0.05, 0.05, 0.055), 0.45, metal=1.0)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=False, segments=24, radius1=0.085, radius2=0.09, depth=0.04)
    for k in range(9):
        a = 2 * math.pi * k / 9
        sp = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.012, radius2=0.0, depth=0.07,
                                   matrix=Matrix.Translation((math.cos(a) * 0.088, math.sin(a) * 0.088, 0.055)))
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if math.atan2(v.co.y, v.co.x) > 2.2], context="VERTS")
    me = bpy.data.meshes.new("broken_crown"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("broken_crown", me); C.sc.collection.objects.link(o)
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.006
    o.data.materials.append(IRON)
    H.hold(o, f.rig, side, -0.09)
    f.add(o)


# ------------------------------------------------------------------ the six Wardens
def ignar(rig, body, ex, J, corrupt=False):
    """Ignar, the Cinder Warden. Black basalt body cracked with orange light, a molten core visible through the chest,
    a crown of slow flames. (corrupt: the Cinder Tyrant, fire burning grey-white, a crown of black smoke.)"""
    f = Fig(rig, body, ex, J)
    core = (0, J["spine-1"].y - 0.06, (J["spine-1"].z + J["spine-2"].z) / 2)
    rgb = (1.0, 0.33, 0.05) if not corrupt else (0.85, 0.85, 0.9)
    skin_as(body, basalt("basalt" if not corrupt else "basalt_grey", core, rgb, grey=corrupt))
    lumpy(body, 0.06, 0.018, "VORONOI")
    glow_eyes(f, (1.0, 0.5, 0.1) if not corrupt else (0.9, 0.9, 1.0), 25, 0.8)
    point_light(f, "molten_core", Vector(core) + Vector((0, -0.2, 0)), rgb, 60, "chest", 0.15)
    flame_crown(f, rgb=(1.0, 0.2, 0.02) if not corrupt else (0.9, 0.9, 1.0), smoke=corrupt)
    return [body] + f.parts


def aurath(rig, body, ex, J, corrupt=False):
    """Aurath of the Storms. A tall rider-shape of cloud, lightning for veins, never quite solid; a white lightning
    spine. (corrupt: the Thunderhead, the cloud gone solid and black.)"""
    f = Fig(rig, body, ex, J)
    skin_as(body, storm_cloud("storm_body", density=10 if not corrupt else 300, black=corrupt))
    lumpy(body, 0.06, 0.05)
    BOLT = H.glow_mat("bolt", (0.8, 0.88, 1.0), 40)
    f.add(H.wear(body, "lightning_spine", lambda c: abs(c.x) < 0.012 and f.pel - 0.15 < c.z < J["head-2"].z, BOLT, 0.004, 0.0))
    glow_eyes(f, (0.8, 0.9, 1.0), 25, 0.3)
    return [body] + f.parts


def elowen(rig, body, ex, J, corrupt=False):
    """Elowen the Evergreen. An old woman of bark, slow and bent, branches for hair that blossom white, moss trailing.
    (corrupt: the Elder Broodmother, the bark grey and swollen.)"""
    f = Fig(rig, body, ex, J)
    skin_as(body, bark("bark_skin", grey=corrupt))
    lumpy(body, 0.05, 0.016, "WOOD", "furrows")
    f.ex = [x for x in f.ex]
    glow_eyes(f, (0.55, 0.85, 0.3) if not corrupt else (0.7, 0.7, 0.72), 6, 0.3, 0.9)
    branch_crown(f, grey=corrupt)
    moss_strands(f, lambda c: abs(c.x) < f.sh.x + 0.02 and f.s2 < c.z < f.neck and c.y > J["spine-1"].y, 6000, 0.2)
    return [body] + f.parts


def thalassa(rig, body, ex, J, corrupt=False):
    """Thalassa of the Deep. A tall translucent sea-glass woman, currents visible inside her, drowned bronze bells
    woven in long floating hair."""
    f = Fig(rig, body, ex, J)
    skin_as(body, sea_glass("sea_glass"))
    glow_eyes(f, (0.6, 0.95, 0.9), 8, 0.5)
    hc = f.hc
    float_up = lambda p: (0.4 * (p.x - hc.x) / max(abs(p.x - hc.x), 0.02), 1.0, 0.45)
    f.add(H.comb_hair(rig, H.scalp_points(body, f.scalp, 7000, seed=31), hc, "floating_hair", 0.6, float_up, segs=16,
                      lift=0.0, jitter=0.35, radius=0.0022, push=0.3, wrap_above=99.0, colour=(0.08, 0.3, 0.3), wave=0.12))
    bells_in_hair(f)
    point_light(f, "deep_glow", (0, J["spine-1"].y, f.s2), (0.4, 0.85, 0.8), 6, "chest", 0.01)
    return [body] + f.parts


def orrok(rig, body, ex, J, corrupt=False):
    """Orrok the Mountain. An enormous slow stone giant, moss and small pines on his shoulders, eyes like two amber
    geodes. (corrupt: the Mountain Titan, grey lichen over his eyes, his trees dead.)"""
    f = Fig(rig, body, ex, J)
    skin_as(body, mountain_stone("mountain", (0.2, 0.19, 0.17), lichen=corrupt))
    lumpy(body, 0.07, 0.04)
    lumpy(body, 0.02, 0.012, name="grain")
    GEO = C.mat("geode", (1.0, 0.55, 0.1), 0.15, emit=(1.0, 0.5, 0.08), strength=8 if not corrupt else 0.5)
    glow_eyes(f, (1.0, 0.55, 0.1), 0, 0.6 if not corrupt else 0.0, 1.05, mat=GEO)
    sh = f.sh; y = J["spine-1"].y
    sites = []
    for sd in (1, -1):
        for (dx, dy, dz) in ((-0.1, 0.0, 0.06), (-0.03, 0.05, 0.05), (0.04, -0.02, 0.04), (-0.06, 0.08, 0.02), (0.0, -0.06, 0.03)):
            sites.append((sd * (sh.x + dx), y + dy, sh.z + dz, "upperarm" + (".l" if sd > 0 else ".r") if dx > 0 else "chest"))
    ROCK = mountain_stone("mountain_plates", (0.22, 0.2, 0.18), moss=0.9, lichen=corrupt)
    n0 = len(f.parts)
    K.plate_set(f, ROCK, pauldron=1.7, chest=0.06)
    for p in f.parts[n0:]:
        lumpy(p, 0.05, 0.045, name="chips")
    pines(f, sites, dead=corrupt)
    return [body] + f.parts


def nyxara(rig, body, ex, J, corrupt=False):
    """Nyxara of the Hollow. Very tall, slender, a starfield where her face should be, a long black train full of slow
    stars, the broken iron crown in her hand."""
    f = Fig(rig, body, ex, J)
    f.skin((0.07, 0.065, 0.09), iris=(0.1, 0.1, 0.1))
    no_eyes(f)
    hy = J["head"].y
    face = lambda c: c.y < hy - 0.035 and f.jaw.z - 0.03 < c.z < f.eye.z + 0.07 and abs(c.x) < 0.075
    face_poly_material(body, starfield("star_face", black=corrupt, sc=(70.0, 28.0), nebula=1.0, big=1.8), face)
    if corrupt:   # the Hollow King: two lights left in the black
        for sx in (-1, 1):
            bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=(sx * f.eye.x, f.eye.y - 0.02, f.eye.z))
            e = bpy.context.object; e.data.materials.append(H.glow_mat("hollow_eye", (0.85, 0.85, 1.0), 40)); H.on_bone(e, rig, "head"); f.add(e)
    SKY = starfield("star_cloth", cloth=True)
    f.add(H.wear(body, "gown", lambda c: f.torso(f.pel - 0.1, f.neck - 0.02, 0.025)(c) or f.sleeves(0.03)(c), SKY, 0.016, 0.008, smooth=12))
    f.add(H.skirt("gown_skirt", J, f.s4 + 0.02, -0.01, 0.15, 0.42, SKY, rig, folds=0.04, rings=32))
    f.hide_legs()
    K.hair(f, 0.7, 16000, comb_front=(0, 1, 0.05), comb_back=(0, 0.3, -1), hang_below=f.eye.z - 0.02, jitter=0.2, colour=(0.015, 0.015, 0.02))
    train(f, SKY)
    if not corrupt:
        broken_crown(f)
    return [body] + f.parts


def train(f, mat, length=2.2, width=0.55):
    """A long train from the shoulders, falling to the ground and trailing far behind."""
    J = f.J
    top = f.sh.z; y0 = J["spine-1"].y + 0.12
    bm = bmesh.new(); rows, segs = 40, 20
    grid = []
    fall = top   # vertical run, then along the ground
    total = fall + length
    for i in range(rows + 1):
        s = total * i / rows
        if s <= fall:
            z = top - s; y = y0 + 0.08 * (s / fall) ** 2
        else:
            z = 0.01; y = y0 + 0.08 + (s - fall)
        w = width * (0.6 + 0.8 * min(1.0, s / fall)) * (1 + 0.4 * max(0.0, (s - fall) / length))
        grid.append([bm.verts.new((((k / segs) - 0.5) * w, y, z)) for k in range(segs + 1)])
    for i in range(rows):
        for k in range(segs):
            bm.faces.new((grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]))
    me = bpy.data.meshes.new("train"); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new("train", me); C.sc.collection.objects.link(o)
    tx = bpy.data.textures.new("train_folds", "WOOD"); tx.wood_type = "BANDNOISE"; tx.noise_scale = 0.08; tx.turbulence = 1
    d = o.modifiers.new("folds", "DISPLACE"); d.texture = tx; d.strength = 0.04; d.texture_coords = "OBJECT"
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.006
    o.modifiers.new("sub", "SUBSURF").levels = 1
    o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    H.on_bone(o, f.rig, "hips")
    f.add(o)
    return o


# ------------------------------------------------------------------ registry (built at human size, scaled up)
_W = {
    "ignar":    (dict(height=2.3, gender=1.0, muscle=1.0, weight=0.75, tall=0.8, age=0.6), ignar, 1.45,
                 dict(H.HUMAN_POSTURE)),
    "aurath":   (dict(height=2.3, gender=1.0, muscle=0.6, weight=0.1, tall=1.0, age=0.6), aurath, 1.4, None),
    "elowen":   (dict(height=2.1, gender=0.0, muscle=0.2, weight=0.15, tall=0.4, age=1.0,
                      targets={"cheek/l-cheek-volume-decr": 1.0, "cheek/r-cheek-volume-decr": 1.0}), elowen, 1.35,
                 dict(H.HUMAN_POSTURE, chest=(22.0, (1, 0, 0)), head=(-16.0, (1, 0, 0)))),
    "thalassa": (dict(height=2.3, gender=0.0, muscle=0.3, weight=0.25, tall=1.0, age=0.55), thalassa, 1.45, None),
    "orrok":    (dict(height=2.3, gender=1.0, muscle=1.0, weight=1.0, tall=0.6, age=0.7, proportions=0.4), orrok, 2.3,
                 dict(H.HUMAN_POSTURE, chest=(12.0, (1, 0, 0)), head=(-10.0, (1, 0, 0)))),
    "nyxara":   (dict(height=2.45, gender=0.0, muscle=0.15, weight=0.0, tall=1.0, age=0.5, proportions=0.7), nyxara, 1.45,
                 dict(H.HUMAN_POSTURE, upperarm=(45.0, (0, 1, 0)))),
}
_CORRUPT = {"ignar": "cinder_tyrant", "aurath": "thunderhead", "elowen": "broodmother", "orrok": "mountain_titan",
            "nyxara": "hollow_king"}
for _k, (_props, _fn, _sc, _post) in _W.items():
    H.HUMANS[_k] = (_props, _fn)
    H.SCALE[_k] = _sc
    if _post:
        H.POSTURES[_k] = _post
    if _k in _CORRUPT:
        _c = _CORRUPT[_k]
        H.HUMANS[_c] = (_props, (lambda fn: lambda r, b, e, j: fn(r, b, e, j, corrupt=True))(_fn))
        H.SCALE[_c] = _sc
        if _post:
            H.POSTURES[_c] = _post
