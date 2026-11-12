"""The rest of the story cast, built the same way as the heroes in hero.py (real MakeHuman bodies on the KayKit rig).

Each character is a short recipe of shared parts: hair, beard, clothes cut from the body, hull armour, long coats
and capes, and props held in the hands. Importing this module registers them with hero.build_human():

    import hero, cast
    rig = hero.build_human("brannoc", (0, 0, 0), 0.0, "Idle")

Looks follow /mnt/project-files/lore/characters.md (story canon v2).
"""
import bpy, bmesh, math, random
from mathutils import Vector, Matrix
import cine3d as C
import hero as H


# ------------------------------------------------------------------ context
class Fig:
    """Joint heights and helpers for one body, so recipes read like a costume list."""

    def __init__(self, rig, body, ex, J):
        self.rig, self.body, self.ex, self.J = rig, body, ex, J
        self.sh, self.el, self.wr = J["l-shoulder"], J["l-elbow"], J["l-hand"]
        self.neck, self.pel, self.kn, self.an = J["neck"].z, J["pelvis"].z, J["l-knee"].z, J["l-ankle"].z
        self.s1, self.s2, self.s4 = J["spine-1"].z, J["spine-2"].z, J["spine-4"].z
        self.eye, self.mouth, self.jaw = J["l-eye"], J["mouth"], J["jaw"]
        self.scalp, self.hc = H.face_and_hair_points(J)
        self.parts = []

    ax = staticmethod(lambda c: abs(c.x))

    def add(self, *objs):
        for o in objs:
            if isinstance(o, (list, tuple)):
                self.parts.extend(o)
            elif o is not None:
                self.parts.append(o)

    # body regions (rest T-pose)
    def torso(self, lo, hi, widen=0.02):
        return lambda c: abs(c.x) < self.sh.x + widen and lo < c.z < hi

    def sleeves(self, to_wrist=0.03):
        return lambda c: abs(c.x) >= self.sh.x + 0.02 and abs(c.x) < self.wr.x - to_wrist and c.z > self.neck - 0.4

    def skin(self, rgb, lips=None, lids=None, iris=(0.12, 0.1, 0.07)):
        sk = H.skin_mat_real(rgb, lips or (rgb[0] * 0.75, rgb[1] * 0.42, rgb[2] * 0.45),
                             lids or (rgb[0] * 0.7, rgb[1] * 0.6, rgb[2] * 0.6))
        self.body.data.materials.append(sk)
        for h in self.ex:
            self.add(H.eyes_for(self.rig, h, iris_rgb=iris))
        self.ex = []
        return sk

    def hide_feet(self):
        H.hide_under(self.body, lambda c: c.z < self.an + 0.07)

    def hide_legs(self):
        H.hide_under(self.body, lambda c: c.z < self.an + 0.07 or (c.z < self.pel - 0.06 and abs(c.x) < 0.4))


# ------------------------------------------------------------------ materials
def leather(name, rgb, rough=0.55):
    m = C.mat(name, rgb, rough)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 90; n.inputs["Detail"].default_value = 6
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.25
    nt.links.new(n.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def mail(name="mail", rgb=(0.4, 0.4, 0.42)):
    m = C.mat(name, rgb, 0.4, metal=1.0)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = 220
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.9; bu.invert = True
    nt.links.new(vo.outputs["Distance"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def enamel_plate(name, rgb, dent=0.05):
    """Painted or enamelled steel (Gorrim's rust-red, Cassivane's red)."""
    m = H.steel(name, dent)
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1); b.inputs["Metallic"].default_value = 0.55
    return m


def stone(name, rgb=(0.32, 0.29, 0.26)):
    m = C.mat(name, rgb, 0.85)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n = nt.nodes.new("ShaderNodeTexNoise"); n.inputs["Scale"].default_value = 14; n.inputs["Detail"].default_value = 10
    nt.links.new(tc.outputs["Object"], n.inputs["Vector"])
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = 0.7
    nt.links.new(n.outputs["Fac"], bu.inputs["Height"]); nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


def rune_overlay(name, rgb, scale=30, strength=6, cover=0.08):
    """Glowing marks on skin (ember runes, war paint as emission=0): a transparent layer with lit strokes."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.feature = "DISTANCE_TO_EDGE"; vo.inputs["Scale"].default_value = scale
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    th = nt.nodes.new("ShaderNodeMath"); th.operation = "LESS_THAN"; th.inputs[1].default_value = cover
    nt.links.new(vo.outputs["Distance"], th.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    if strength:
        sh = nt.nodes.new("ShaderNodeEmission"); sh.inputs["Color"].default_value = (*rgb, 1); sh.inputs["Strength"].default_value = strength
    else:
        sh = nt.nodes.new("ShaderNodeBsdfDiffuse"); sh.inputs["Color"].default_value = (*rgb, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(th.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(sh.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


def stripes_overlay(name, rgb, scale=9.0, width=0.12, axis="Z"):
    """Painted bands on skin (Kaela's lightning paint): a transparent layer with jagged white stripes."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; out = nt.nodes["Material Output"]
    for n in list(nt.nodes):
        if n.type != "OUTPUT_MATERIAL":
            nt.nodes.remove(n)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = axis
    wv.wave_profile = "SAW"; wv.inputs["Scale"].default_value = scale; wv.inputs["Distortion"].default_value = 6
    wv.inputs["Detail"].default_value = 1.5
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    th = nt.nodes.new("ShaderNodeMath"); th.operation = "LESS_THAN"; th.inputs[1].default_value = width
    nt.links.new(wv.outputs["Fac"], th.inputs[0])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    di = nt.nodes.new("ShaderNodeBsdfDiffuse"); di.inputs["Color"].default_value = (*rgb, 1)
    mx = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(th.outputs[0], mx.inputs[0]); nt.links.new(tr.outputs[0], mx.inputs[1]); nt.links.new(di.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    return m


# ------------------------------------------------------------------ hair and beards
def hair(f, length=0.07, count=20000, comb_front=(0, 1, 0.05), comb_back=(0, 1, -0.45), jitter=0.22, hang_below=None,
         keep=None, name="hair", **colour):
    """Head hair as combed strands. `hang_below`: z under which long hair stops following the skull and falls."""
    sc = keep or f.scalp
    hc = f.hc
    kw = dict(colour)
    if hang_below is not None:
        kw.update(wrap_above=hang_below, segs=10)
    f.add(H.comb_hair(f.rig, H.scalp_points(f.body, sc, count), hc, name, length,
                      lambda p: comb_front if p.y < hc.y - 0.025 else comb_back, jitter=jitter, **kw))


def beard(f, length=0.12, count=14000, name="beard", moustache=True, push=0.12, **colour):
    mz = f.mouth.z; ax = Fig.ax
    chin = lambda c: (c.y < f.J["head"].y - 0.03 and f.jaw.z - 0.075 < c.z < mz - 0.012 and ax(c) < 0.068)
    f.add(H.comb_hair(f.rig, H.scalp_points(f.body, chin, count, seed=8), f.hc, name, length, (0, -0.08, -1),
                      segs=8 if length > 0.1 else 5, lift=0.0, jitter=0.1, radius=0.0016, push=push, wrap_above=99.0, **colour))
    if moustache:
        lip = lambda c: (c.y < f.J["head"].y - 0.06 and mz + 0.006 < c.z < mz + 0.022 and ax(c) < 0.03)
        f.add(H.comb_hair(f.rig, H.scalp_points(f.body, lip, 2500, seed=10), f.hc, name + "_moustache", min(0.06, length),
                          lambda p: (0.7 * p.x / max(abs(p.x), 1e-3), -0.35, -1.4), segs=5, lift=0.0, jitter=0.1,
                          radius=0.0014, push=0.2, wrap_above=99.0, **colour))


def stubble(f, **colour):
    mz = f.mouth.z; ax = Fig.ax
    jaw = lambda c: (c.y < f.J["head"].y - 0.0 and f.jaw.z - 0.06 < c.z < mz + 0.02 and ax(c) < 0.075
                     and not (abs(c.z - mz) < 0.008 and ax(c) < 0.025))
    f.add(H.comb_hair(f.rig, H.scalp_points(f.body, jaw, 9000, seed=11), f.hc, "stubble", 0.004, (0, 0, -1), segs=3,
                      lift=0.0, jitter=0.3, radius=0.0007, wrap_above=99.0, **colour))


def brows(f, count=350, length=0.013, **colour):
    eye = f.eye; ax = Fig.ax
    b = lambda c: eye.z + 0.02 < c.z < eye.z + 0.035 and 0.012 < ax(c) < 0.062 and c.y < eye.y
    f.add(H.comb_hair(f.rig, H.scalp_points(f.body, b, count, seed=9), f.hc, "brows", length,
                      lambda p: (1 if p.x > 0 else -1, -0.2, 0.1), segs=4, jitter=0.1, radius=0.0008, **colour))


def beard_rings(f, mat, n=5, length=0.3):
    """Rings braided into a beard (brass for Brannoc, iron for Gorrim), down its front."""
    out = []
    for i in range(n):
        z = f.jaw.z - 0.06 - (i + 0.5) * length / (n + 1)
        x = (-1) ** i * 0.02 * (1 + i % 3)
        bpy.ops.mesh.primitive_torus_add(major_radius=0.014, minor_radius=0.004, location=(x, f.J["head"].y - 0.11 - 0.02 * i / n, z))
        r = bpy.context.object; r.name = "beard_ring"; r.rotation_euler.x = math.radians(90); r.data.materials.append(mat)
        H.on_bone(r, f.rig, "head"); out.append(r)
    f.add(out)


# ------------------------------------------------------------------ clothes
def long_coat(f, mat, hem_z, flare=0.36, top_widen=0.03, sleeves=True, collar=True):
    """A coat: body and sleeves cut from the body, a skirt from the waist to `hem_z`."""
    keep = f.torso(f.pel - 0.1, f.neck - (0.0 if collar else 0.03), top_widen)
    if sleeves:
        sl = f.sleeves(0.02); keep0 = keep
        keep = lambda c: keep0(c) or sl(c)
    f.add(H.wear(f.body, "coat", keep, mat, 0.022, 0.01, smooth=14))
    f.add(H.skirt("coat_skirt", f.J, f.s4 + 0.02, hem_z, 0.19, flare, mat, f.rig, folds=0.03, leg_share=0.75, rings=22))


def back_cape(f, mat, length=1.2, width=0.62, name="cape"):
    """A cloak hanging from the shoulders down the back, on the chest bone."""
    J = f.J
    top = f.sh.z + 0.02; y0 = J["spine-1"].y + 0.14
    bm = bmesh.new(); rows, segs = 18, 24
    grid = []
    for i in range(rows + 1):
        t = i / rows
        z = top - length * t
        w = width * (0.75 + 0.45 * t)
        row = []
        for k in range(segs + 1):
            u = k / segs - 0.5
            a = u * math.pi * 0.9
            row.append(bm.verts.new((math.sin(a) * w * 0.55, y0 + (1 - math.cos(a)) * -0.05 + 0.12 * t * t + 0.02, z)))
        grid.append(row)
    for i in range(rows):
        for k in range(segs):
            bm.faces.new((grid[i][k], grid[i][k + 1], grid[i + 1][k + 1], grid[i + 1][k]))
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); C.sc.collection.objects.link(o)
    tx = bpy.data.textures.new(name + "_folds", "WOOD"); tx.wood_type = "BANDNOISE"; tx.noise_scale = 0.05; tx.turbulence = 1
    d = o.modifiers.new("folds", "DISPLACE"); d.texture = tx; d.strength = 0.035; d.direction = "Y"; d.texture_coords = "OBJECT"
    o.modifiers.new("thick", "SOLIDIFY").thickness = 0.008
    o.modifiers.new("sub", "SUBSURF").levels = 1
    o.data.materials.append(mat)
    for p in me.polygons:
        p.use_smooth = True
    H.on_bone(o, f.rig, "chest")
    f.add(o)
    return o


def hood(f, mat, up=True):
    """A ranger's hood: up over the head (open in front), or down as a roll at the back of the neck."""
    if up:
        o = H.head_veil(f.rig, f.J, mat, drop=0.32, open_front=1.5)
        o.name = "hood"; o.scale = (1.12, 1.12, 1.0)
    else:
        bpy.ops.mesh.primitive_torus_add(major_radius=0.11, minor_radius=0.04, location=(0, f.J["neck"].y + 0.07, f.neck + 0.0))
        o = bpy.context.object; o.name = "hood_down"; o.scale = (1.2, 0.8, 0.7); o.data.materials.append(mat)
        bpy.ops.object.shade_smooth(); H.on_bone(o, f.rig, "chest")
    f.add(o)
    return o


def boots(f, mat, high=True):
    ax = Fig.ax
    for side, sd in ((".l", 1), (".r", -1)):
        S = lambda c, sd=sd: c.x * sd > 0
        f.add(H.hull_plate(f.body, f.rig, "boot" + side, lambda c, S=S: S(c) and c.z < f.an + 0.05 and ax(c) < 0.4,
                           mat, "foot" + side, 0.02, voxel=0.02, scale=(1.06, 1.05, 1.1)))
        if high:
            f.add(H.hull_plate(f.body, f.rig, "bootleg" + side, lambda c, S=S: S(c) and f.an - 0.02 < c.z < f.kn - 0.08 and ax(c) < 0.4,
                               mat, "lowerleg" + side, 0.018, voxel=0.015))
    f.hide_feet()


def plate_set(f, mat, legs=True, arms=True, pauldron=1.0, chest=0.035):
    """Full plate pieces as hulls on their bones (cuirass, faulds, pauldrons, vambraces, greaves, knees)."""
    ax = Fig.ax; J = f.J
    f.add(H.hull_plate(f.body, f.rig, "cuirass", lambda c: ax(c) < f.sh.x - 0.03 and f.s2 - 0.06 < c.z < f.neck - 0.08,
                       mat, "chest", chest, scale=(0.97, 1.0, 1.0)))
    f.add(H.hull_plate(f.body, f.rig, "plackart", lambda c: ax(c) < f.sh.x - 0.04 and f.s4 - 0.04 < c.z < f.s2 - 0.02, mat, "spine", 0.03))
    f.add(H.wear(f.body, "faulds", lambda c: f.pel - 0.2 < c.z < f.s4 - 0.03 and ax(c) < 0.33, mat, 0.07, 0.012, smooth=12))
    f.add(H.wear(f.body, "gorget", lambda c: f.neck - 0.09 < c.z < f.neck + 0.03 and ax(c) < 0.16, mat, 0.03, 0.012, smooth=10))
    for side, sd in ((".l", 1), (".r", -1)):
        S = lambda c, sd=sd: c.x * sd > 0
        if arms:
            f.add(H.hull_plate(f.body, f.rig, "pauldron" + side, lambda c, S=S: S(c) and f.sh.x - 0.06 < ax(c) < f.sh.x + 0.15 and c.z > f.sh.z - 0.04,
                               mat, "upperarm" + side, 0.03 * pauldron, scale=(1.0 * pauldron, 1.0 * pauldron, 1.05 * pauldron)))
            f.add(H.hull_plate(f.body, f.rig, "vambrace" + side, lambda c, S=S: S(c) and f.el.x + 0.05 < ax(c) < f.wr.x - 0.05 and c.z > f.neck - 0.5,
                               mat, "lowerarm" + side, 0.02))
        if legs:
            kx = J["l-knee"]
            f.add(H.hull_plate(f.body, f.rig, "greave" + side, lambda c, S=S: S(c) and f.an + 0.17 < c.z < f.kn - 0.02 and ax(c) < 0.4,
                               mat, "lowerleg" + side, 0.028))
            f.add(H.hull_plate(f.body, f.rig, "poleyn" + side, lambda c, S=S: S(c) and f.kn - 0.06 < c.z < f.kn + 0.08 and c.y < kx.y and ax(c) < 0.4,
                               mat, "lowerleg" + side, 0.035))
            f.add(H.hull_plate(f.body, f.rig, "cuisse" + side, lambda c, S=S: S(c) and f.kn + 0.06 < c.z < f.pel - 0.12 and c.y < kx.y + 0.03 and ax(c) < 0.4,
                               mat, "upperleg" + side, 0.025))


# ------------------------------------------------------------------ props (built along +Z, grip at the origin)
def _join(objs, name, mat=None):
    for o in objs[1:]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]; objs[0].select_set(True)
    bpy.ops.object.join()
    o = bpy.context.object; o.name = name
    if mat:
        o.data.materials.clear(); o.data.materials.append(mat)
    return o


def _cyl(r, d, z, verts=16, x=0.0, y=0.0):
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=d, vertices=verts, location=(x, y, z))
    return bpy.context.object


def _box(sx, sy, sz, z, x=0.0, y=0.0):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z)); o = bpy.context.object; o.scale = (sx / 2, sy / 2, sz / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    return o


def _bevel(o, w=0.008, seg=2):
    b = o.modifiers.new("bevel", "BEVEL"); b.width = w; b.segments = seg
    return o


def forge_hammer(f, side=".r"):
    """Brannoc's forge-hammer: a heavy iron head glowing orange at the seams, on an ash haft."""
    IRON = C.mat("hammer_iron", (0.08, 0.075, 0.07), 0.45, metal=1.0)
    WOOD = H.cloth("haft", (0.13, 0.08, 0.045), 0.7)
    GLOW = H.glow_mat("ember_seam", (1.0, 0.38, 0.08), 10)
    haft = _cyl(0.024, 1.05, 0.25); haft.data.materials.append(WOOD)
    head = _bevel(_box(0.34, 0.17, 0.17, 0.78), 0.015); head.data.materials.append(IRON)
    seams = [_box(0.342, 0.172, 0.006, 0.78), _box(0.006, 0.172, 0.172, 0.78, x=0.09), _box(0.006, 0.172, 0.172, 0.78, x=-0.09)]
    for p in seams:
        p.data.materials.append(GLOW)
    for p in [haft, head] + seams:   # bake each part's place into its mesh so the joined hammer's origin is the grip
        p.data.transform(Matrix.Translation(p.location)); p.location = (0, 0, 0)
        for m in p.modifiers:
            bpy.context.view_layer.objects.active = p
            bpy.ops.object.modifier_apply(modifier=m.name)
    hm = _join([haft, head] + seams, "forge_hammer")
    H.hold(hm, f.rig, side, 0.0)
    li = bpy.data.lights.new("hammer_glow", "POINT"); li.energy = 25; li.color = (1.0, 0.45, 0.15); li.shadow_soft_size = 0.1
    lo = bpy.data.objects.new("hammer_glow", li); C.sc.collection.objects.link(lo); H.hold(lo, f.rig, side, 0.78)
    f.add(hm, lo)


def lance(f, side=".r", length=2.8):
    """Kaela's lightning lance: a long ash shaft, steel head with a crackling white tip."""
    WOOD = H.cloth("lance_wood", (0.18, 0.13, 0.08), 0.6)
    STEEL = H.steel("lance_steel", 0.03)
    sh = _cyl(0.025, length, 0); sh.data.materials.append(WOOD); H.hold(sh, f.rig, side, length * 0.25)
    bpy.ops.mesh.primitive_cone_add(radius1=0.045, radius2=0.0, depth=0.42, vertices=4)
    tip = bpy.context.object; tip.data.materials.append(STEEL); H.hold(tip, f.rig, side, length * 0.75 + 0.2)
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.03, subdivisions=2)
    sp = bpy.context.object; sp.data.materials.append(H.glow_mat("spark", (0.85, 0.9, 1.0), 40)); H.hold(sp, f.rig, side, length * 0.75 + 0.42)
    li = bpy.data.lights.new("lance_spark", "POINT"); li.energy = 30; li.color = (0.75, 0.85, 1.0); li.shadow_soft_size = 0.02
    lo = bpy.data.objects.new("lance_spark", li); C.sc.collection.objects.link(lo); H.hold(lo, f.rig, side, length * 0.75 + 0.42)
    f.add(sh, tip, sp, lo)


def miner_pick(f, side=".r"):
    IRON = C.mat("pick_iron", (0.12, 0.1, 0.09), 0.5, metal=1.0)
    WOOD = H.cloth("pick_haft", (0.12, 0.08, 0.05), 0.7)
    h = _cyl(0.026, 0.75, 0); h.data.materials.append(WOOD); H.hold(h, f.rig, side, 0.18)
    bpy.ops.mesh.primitive_cone_add(radius1=0.022, radius2=0.003, depth=0.36, vertices=8)
    hd = bpy.context.object; hd.rotation_euler.y = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    sd = hd.modifiers.new("bend", "SIMPLE_DEFORM"); sd.deform_method = "BEND"; sd.deform_axis = "Y"; sd.angle = math.radians(35)
    hd.data.materials.append(IRON); H.hold(hd, f.rig, side, 0.52); hd["hold_dx"] = 0.12
    f.add(h, hd)


def door_shield(f, mat, on_back=False):
    """Gorrim's shield: a carved stone door from the Kharum Terraces, on the left forearm (or slung on the back)."""
    o = _bevel(_box(0.5, 0.08, 0.85, 0), 0.02, 3)
    tx = bpy.data.textures.new("door_carving", "STUCCI"); tx.noise_scale = 0.08
    d = o.modifiers.new("carve", "DISPLACE"); d.texture = tx; d.strength = 0.012
    sd = o.modifiers.new("sub", "SUBSURF"); sd.levels = 3; sd.subdivision_type = "SIMPLE"; o.modifiers.move(2, 1)
    # carved frame and a band of runes
    fr = _bevel(_box(0.54, 0.09, 0.05, 0.41)); fr2 = _bevel(_box(0.54, 0.09, 0.05, -0.41))
    for p in (fr, fr2):
        p.data.materials.append(mat)
    o.data.materials.append(mat)
    door = _join([o, fr, fr2], "door_shield")
    if on_back:
        door.location = (0, f.J["spine-1"].y + 0.2, f.s2 - 0.05); door.rotation_euler.z = 0
        H.on_bone(door, f.rig, "chest")
    else:
        # strapped on the left forearm; in the T-pose the forearm runs along +X, the door's face looks forward (-Y)
        mid = f.el.lerp(f.wr, 0.45)
        door.rotation_euler.y = math.radians(90)
        door.location = (mid.x, mid.y - 0.13, mid.z)
        H.on_bone(door, f.rig, "lowerarm.l")
    f.add(door)
    return door


def star_blade(f, side=".r", length=1.0):
    """Corvin's long curved blade of black glass that shows stars."""
    m = C.mat("star_glass", (0.01, 0.01, 0.02), 0.05)
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vo = nt.nodes.new("ShaderNodeTexVoronoi"); vo.inputs["Scale"].default_value = 140
    nt.links.new(tc.outputs["Object"], vo.inputs["Vector"])
    th = nt.nodes.new("ShaderNodeMath"); th.operation = "LESS_THAN"; th.inputs[1].default_value = 0.06
    nt.links.new(vo.outputs["Distance"], th.inputs[0])
    nt.links.new(th.outputs[0], b.inputs["Emission Strength"]); b.inputs["Emission Color"].default_value = (0.75, 0.7, 1.0, 1)
    b.inputs["Coat Weight"].default_value = 1.0
    bl = _box(0.05, 0.008, length, length / 2 + 0.12)
    sd = bl.modifiers.new("sub", "SUBSURF"); sd.levels = 4; sd.subdivision_type = "SIMPLE"
    tp = bl.modifiers.new("taper", "SIMPLE_DEFORM"); tp.deform_method = "TAPER"; tp.deform_axis = "Z"; tp.factor = -0.6
    cu = bl.modifiers.new("curve", "SIMPLE_DEFORM"); cu.deform_method = "BEND"; cu.deform_axis = "Y"; cu.angle = math.radians(18)
    bl.data.materials.append(m)
    hilt = _cyl(0.018, 0.22, 0.0); hilt.data.materials.append(leather("hilt_wrap", (0.05, 0.03, 0.06)))
    guard = _bevel(_box(0.14, 0.03, 0.025, 0.11)); guard.data.materials.append(C.mat("guard_silver", (0.7, 0.7, 0.75), 0.3, metal=1.0))
    for p, z in ((bl, 0.0), (hilt, 0.0), (guard, 0.0)):
        H.hold(p, f.rig, side, z)
    f.add(bl, hilt, guard)


# ------------------------------------------------------------------ the cast
def brannoc(rig, body, ex, J):
    """Brannoc Emberhand, Smith-Lord of the Reach. 50, huge, barrel-chested, bald, black beard with brass rings.
    Leather forge apron over chain mail, bare scarred arms, one arm tattooed with glowing ember runes;
    forge-hammer glowing orange at the seams."""
    f = Fig(rig, body, ex, J)
    f.skin((0.5, 0.3, 0.2), iris=(0.1, 0.06, 0.03))
    MAIL = mail("brannoc_mail", (0.22, 0.21, 0.2))
    APRON = leather("forge_apron", (0.16, 0.08, 0.035))
    BRASS = C.mat("brass", (0.75, 0.52, 0.2), 0.3, metal=1.0)
    ax = Fig.ax
    f.add(H.wear(body, "mail_shirt", lambda c: f.torso(f.pel - 0.16, f.neck - 0.05, 0.04)(c) or
                 (f.sh.x + 0.04 <= abs(c.x) < f.el.x - 0.02 and c.z > f.neck - 0.4), MAIL, 0.02, 0.008, smooth=6))
    f.add(H.wear(body, "apron", lambda c: c.y < J["spine-2"].y + 0.0 and ax(c) < 0.2 and f.kn - 0.05 < c.z < f.s1, APRON, 0.04, 0.012, smooth=20))
    f.add(H.wear(body, "breeches", lambda c: f.an + 0.12 < c.z < f.pel + 0.02 and ax(c) < 0.4, H.cloth("brannoc_breeches", (0.06, 0.05, 0.045)), 0.012, 0.008))
    f.add(H.wear(body, "runes", lambda c: c.x < -(f.sh.x + 0.04) and ax(c) < f.wr.x - 0.03 and c.z > f.neck - 0.4,
                 rune_overlay("ember_runes", (1.0, 0.4, 0.08), 26, 8, 0.05), 0.002, 0.0))
    boots(f, leather("brannoc_boots", (0.06, 0.04, 0.03)))
    beard(f, 0.24, 18000, melanin=0.95, redness=0.1)
    beard_rings(f, BRASS, 6, 0.22)
    brows(f, 500, 0.016, melanin=0.95, redness=0.1)
    forge_hammer(f)
    return [body] + f.parts


def kaela(rig, body, ex, J):
    """Kaela Stormrider, Marshal of the Steppe. 28, lean, tall, sun-dark. Long blue-grey riding coat slit for the
    saddle, white war-paint lightning stripes across the face, long black hair; lightning lance."""
    f = Fig(rig, body, ex, J)
    f.skin((0.42, 0.25, 0.16), iris=(0.08, 0.05, 0.03))
    COAT = H.robe_cloth("riding_coat", (0.06, 0.08, 0.11), rough=0.8, sheen=0.1)
    ax = Fig.ax
    f.add(H.wear(body, "trousers", lambda c: f.an + 0.1 < c.z < f.pel + 0.02 and ax(c) < 0.4, H.cloth("kaela_trousers", (0.08, 0.07, 0.06)), 0.01, 0.006))
    long_coat(f, COAT, f.kn - 0.25, flare=0.42)
    f.add(H.wear(body, "belt", lambda c: f.s4 - 0.035 < c.z < f.s4 + 0.02 and ax(c) < 0.3, leather("kaela_belt", (0.1, 0.06, 0.035)), 0.045, 0.01))
    f.add(H.wear(body, "war_paint", lambda c: c.z > f.jaw.z - 0.02 and c.y < f.eye.y + 0.05 and ax(c) < 0.09 and c.z < f.eye.z + 0.06,
                 stripes_overlay("lightning_paint", (0.9, 0.9, 0.88), 14, 0.16, "Z"), 0.0015, 0.0))
    boots(f, leather("kaela_boots", (0.05, 0.04, 0.035)))
    hair(f, 0.6, 22000, comb_front=(0, 1, 0.1), comb_back=(0, 0.5, -1), hang_below=f.eye.z - 0.03, melanin=0.97, redness=0.15, jitter=0.18)
    brows(f, 300, 0.012, melanin=0.97, redness=0.15)
    lance(f)
    return [body] + f.parts


def gorrim(rig, body, ex, J):
    """Gorrim Stonebeard, Shield of the Canyon. 60, short, wide as a door. Rust-red plate, a beard to his belt braided
    with iron rings; a carved stone door for a shield; short heavy pick."""
    f = Fig(rig, body, ex, J)
    f.skin((0.52, 0.32, 0.23), iris=(0.1, 0.08, 0.05))
    RUST = enamel_plate("rust_plate", (0.32, 0.1, 0.05), dent=0.1)
    IRON = C.mat("ring_iron", (0.15, 0.14, 0.13), 0.4, metal=1.0)
    plate_set(f, RUST, pauldron=1.15, chest=0.045)
    f.add(H.wear(body, "padding", f.sleeves(0.05), H.quilted("gorrim_padding", (0.08, 0.05, 0.035)), 0.014, 0.01))
    f.add(H.wear(body, "hose", lambda c: f.an + 0.1 < c.z < f.pel and abs(c.x) < 0.4, H.cloth("gorrim_hose", (0.07, 0.05, 0.04)), 0.01, 0.006))
    boots(f, leather("gorrim_boots", (0.08, 0.05, 0.03)), high=False)
    GREY = dict(colour=(0.5, 0.48, 0.45))
    beard(f, 0.48, 24000, push=0.18, **GREY)
    beard_rings(f, IRON, 9, 0.42)
    hair(f, 0.09, 12000, **GREY)
    brows(f, 500, 0.016, **GREY)
    door_shield(f, stone("door_stone", (0.1, 0.08, 0.07)))
    miner_pick(f)
    return [body] + f.parts


def corvin(rig, body, ex, J):
    """Corvin the Uncrowned, Ranger of the Rift. 34, tall, lean, rangy. Weathered black and violet hooded ranger cloak,
    silver hair tied back though young, a long curved blade of black glass that shows stars; stubble, scarred brow."""
    f = Fig(rig, body, ex, J)
    f.skin((0.55, 0.36, 0.27), iris=(0.18, 0.18, 0.22))
    CLOAK = H.robe_cloth("ranger_cloak", (0.05, 0.035, 0.07), patches=0.04, rough=0.9, sheen=0.2)
    JERKIN = leather("ranger_jerkin", (0.05, 0.045, 0.045))
    ax = Fig.ax
    f.add(H.wear(body, "jerkin", lambda c: f.torso(f.pel - 0.12, f.neck - 0.03, 0.02)(c) or f.sleeves(0.03)(c), JERKIN, 0.016, 0.01, smooth=8))
    f.add(H.wear(body, "trousers", lambda c: f.an + 0.1 < c.z < f.pel + 0.02 and ax(c) < 0.4, H.cloth("corvin_trousers", (0.04, 0.035, 0.035)), 0.01, 0.006))
    back_cape(f, CLOAK, length=(f.sh.z - f.kn) + 0.15, width=0.7, name="ranger_cloak")
    hood(f, CLOAK, up=False)
    boots(f, leather("corvin_boots", (0.04, 0.03, 0.03)))
    SILVER = dict(colour=(0.62, 0.62, 0.64))
    hair(f, 0.22, 16000, comb_front=(0, 1, 0.0), comb_back=(0, 1, -0.6), **SILVER)
    stubble(f, colour=(0.3, 0.28, 0.27))
    brows(f, 300, 0.012, colour=(0.35, 0.33, 0.33))
    star_blade(f)
    return [body] + f.parts


H.HUMANS["brannoc"] = (dict(height=2.35, gender=1.0, muscle=1.0, weight=0.95, tall=0.75, age=0.66,
                            targets={"head/head-fat-incr": 0.4, "neck/measure-neck-circ-incr": 0.8}), brannoc)
H.POSTURES["brannoc"] = dict(H.HUMAN_POSTURE, upperarm=(45.0, (0, 1, 0)))
H.HUMANS["kaela"] = (dict(height=2.2, gender=0.0, muscle=0.65, weight=0.2, tall=0.85, age=0.52,
                          targets={"cheek/l-cheek-bones-incr": 0.6, "cheek/r-cheek-bones-incr": 0.6}), kaela)
H.HUMANS["gorrim"] = (dict(height=1.75, gender=1.0, muscle=0.9, weight=0.85, tall=0.0, age=0.75, proportions=0.2,
                           targets={"nose/nose-volume-incr": 0.6}), gorrim)
H.POSTURES["gorrim"] = dict(H.HUMAN_POSTURE, upperarm=(48.0, (0, 1, 0)))
H.HUMANS["corvin"] = (dict(height=2.25, gender=1.0, muscle=0.6, weight=0.25, tall=0.85, age=0.55,
                           targets={"cheek/l-cheek-bones-incr": 0.5, "cheek/r-cheek-bones-incr": 0.5}), corvin)
