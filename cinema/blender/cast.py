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


def beard(f, length=0.12, count=14000, name="beard", moustache=True, push=0.12, radius=0.0016, jitter=0.1, wave=0.0,
          comb=(0, -0.08, -1), full=False, **colour):
    """A full beard from the chin and jaw. Thinner strands, more jitter and a little `wave` keep a dark beard from
    reading as one solid block (Brannoc)."""
    mz = f.mouth.z; ax = Fig.ax
    # chin and jaw, plus the cheeks up to the mouth's corners at the sides: a full beard, not a goatee
    chin = lambda c: (c.y < f.J["head"].y - 0.03 and f.jaw.z - 0.075 < c.z < (mz - 0.012 if ax(c) < 0.035 else mz + 0.025)
                      and ax(c) < (0.068 if not full else 0.085))
    f.add(H.comb_hair(f.rig, H.scalp_points(f.body, chin, count, seed=8), f.hc, name, length, comb,
                      segs=10 if length > 0.1 else 5, lift=0.0, jitter=jitter, radius=radius, push=push, wrap_above=99.0,
                      wave=wave, **colour))
    if moustache:
        lip = lambda c: (c.y < f.J["head"].y - 0.06 and mz + 0.006 < c.z < mz + 0.022 and ax(c) < 0.03)
        f.add(H.comb_hair(f.rig, H.scalp_points(f.body, lip, 2500, seed=10), f.hc, name + "_moustache", min(0.06 if not full else 0.045, length),
                          lambda p: (0.7 * p.x / max(abs(p.x), 1e-3), -0.35 if not full else -0.15, -1.4), segs=5, lift=0.0,
                          jitter=0.1, radius=0.0014 if not full else radius, push=0.2 if not full else 0.08, wrap_above=99.0, **colour))


def stubble(f, length=0.004, count=9000, radius=0.0007, **colour):
    mz = f.mouth.z; ax = Fig.ax
    jaw = lambda c: (c.y < f.J["head"].y - 0.0 and f.jaw.z - 0.06 < c.z < mz + 0.02 and ax(c) < 0.075
                     and not (abs(c.z - mz) < 0.008 and ax(c) < 0.025))
    f.add(H.comb_hair(f.rig, H.scalp_points(f.body, jaw, count, seed=11), f.hc, "stubble", length, (0, 0, -1), segs=3,
                      lift=0.0, jitter=0.3, radius=radius, wrap_above=99.0, **colour))


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
    # black-brown, thinner strands with some wave, lying on the chest: highlights read in low light, not a black block
    beard(f, 0.24, 11000, push=0.04, radius=0.0011, jitter=0.2, wave=0.06, comb=(0, 0.12, -1), full=True, melanin=0.88, redness=0.3)
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


# ------------------------------------------------------------------ batch 2 props
def longbow(f, side=".l", leaves=True):
    """Sylvaine's longbow of pale white wood that has sprouted leaves."""
    WOOD = C.mat("pale_wood", (0.75, 0.72, 0.62), 0.5)
    LEAF = H.cloth("bow_leaf", (0.12, 0.3, 0.06), 0.5)
    bpy.ops.mesh.primitive_torus_add(major_radius=0.9, minor_radius=0.016, major_segments=64, minor_segments=8)
    b = bpy.context.object
    bm = bmesh.new(); bm.from_mesh(b.data)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x < 0.62], context="VERTS"); bm.to_mesh(b.data); bm.free()
    b.data.transform(Matrix.Translation((-0.62, 0, 0))); b.rotation_euler.x = math.radians(90)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    b.data.materials.append(WOOD)
    parts = [b]
    if leaves:
        random.seed(12)
        for i in range(14):
            t = random.uniform(-0.6, 0.6); z = t * 1.2
            bpy.ops.mesh.primitive_plane_add(size=0.06, location=(0.28 * (1 - (t / 0.65) ** 2) + 0.01, 0, z))
            l = bpy.context.object; l.scale = (1, 0.5, 1); l.rotation_euler = (random.uniform(0, 3), random.uniform(0, 3), random.uniform(0, 3))
            l.data.materials.append(LEAF); parts.append(l)
    bw = _join(parts, "leaf_bow")
    st = _cyl(0.002, 1.4, 0); st.data.materials.append(C.mat("bowstring", (0.7, 0.7, 0.65), 0.6)); st.name = "bowstring"
    bw = _join([bw, st], "leaf_bow")
    H.hold(bw, f.rig, side, 0.0)
    f.add(bw)


def ice_staff(f, side=".r", length=1.9):
    """Mirelle's staff of clear ice with a fish skeleton frozen inside."""
    ICE = C.mat("ice", (0.75, 0.9, 0.95), 0.05)
    b = ICE.node_tree.nodes["Principled BSDF"]; b.inputs["Transmission Weight"].default_value = 0.9; b.inputs["IOR"].default_value = 1.31
    st = _cyl(0.035, length, 0, 8); st.data.materials.append(ICE)
    tx = bpy.data.textures.new("ice_facets", "VORONOI"); tx.noise_scale = 0.08
    d = st.modifiers.new("facets", "DISPLACE"); d.texture = tx; d.strength = 0.01
    bones = []
    spine = _cyl(0.003, 0.32, 0, 6); bones.append(spine)
    for k in range(9):
        r = _cyl(0.0018, 0.06 - abs(k - 4) * 0.008, -0.13 + k * 0.032, 4); r.rotation_euler.y = math.radians(90)
        bpy.ops.object.transform_apply(location=False, rotation=True, scale=False); bones.append(r)
    fish = _join(bones, "frozen_fish", C.mat("fishbone", (0.85, 0.82, 0.75), 0.5))
    H.hold(st, f.rig, side, length * 0.25); H.hold(fish, f.rig, side, length * 0.62)
    li = bpy.data.lights.new("ice_glow", "POINT"); li.energy = 6; li.color = (0.5, 0.9, 1.0)
    lo = bpy.data.objects.new("ice_glow", li); C.sc.collection.objects.link(lo); H.hold(lo, f.rig, side, length * 0.7)
    f.add(st, fish, lo)


def astrolabe(f, side=".l"):
    """Ilyra's broken astrolabe on a chain, hanging from her hand."""
    BR = C.mat("astro_brass", (0.6, 0.45, 0.2), 0.35, metal=1.0)
    rings = []
    for k, (r, rot) in enumerate(((0.06, (90, 0, 0)), (0.05, (90, 0, 50)), (0.042, (20, 70, 0)))):
        bpy.ops.mesh.primitive_torus_add(major_radius=r, minor_radius=0.004, location=(0, 0, -0.16))
        o = bpy.context.object; o.rotation_euler = tuple(math.radians(a) for a in rot)
        if k == 2:   # broken: a third of the inner ring missing
            bm = bmesh.new(); bm.from_mesh(o.data)
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.x > 0.02 and v.co.y > 0], context="VERTS"); bm.to_mesh(o.data); bm.free()
        rings.append(o)
    ch = _cyl(0.0015, 0.14, -0.07, 4); rings.append(ch)
    a = _join(rings, "astrolabe", BR)
    for p in a.data.polygons:
        p.use_smooth = True
    H.hold(a, f.rig, side, 0.0)
    f.add(a)


def glass_greatsword(f, side=".r", length=1.5):
    """Seraphel's greatsword whose blade is a sliver of Sunstone glass, glowing like a dawn."""
    GL = C.mat("sunglass", (1.0, 0.9, 0.7), 0.05)
    b = GL.node_tree.nodes["Principled BSDF"]
    b.inputs["Transmission Weight"].default_value = 0.6; b.inputs["Emission Color"].default_value = (1.0, 0.78, 0.45, 1)
    b.inputs["Emission Strength"].default_value = 4
    bl = _box(0.08, 0.014, length, length / 2 + 0.16)
    sd = bl.modifiers.new("sub", "SUBSURF"); sd.levels = 3; sd.subdivision_type = "SIMPLE"
    tp = bl.modifiers.new("taper", "SIMPLE_DEFORM"); tp.deform_method = "TAPER"; tp.deform_axis = "Z"; tp.factor = -0.5
    bl.data.materials.append(GL)
    GOLD = C.mat("white_gold", (0.9, 0.82, 0.62), 0.25, metal=1.0)
    gd = _bevel(_box(0.34, 0.04, 0.04, 0.14)); gd.data.materials.append(GOLD)
    hi = _cyl(0.02, 0.3, 0.0); hi.data.materials.append(leather("sword_grip", (0.08, 0.05, 0.03)))
    for p in (bl, gd, hi):
        p.data.transform(Matrix.Translation(p.location)); p.location = (0, 0, 0)
    sw = _join([hi, gd], "greatsword_hilt")
    H.hold(sw, f.rig, side, 0.0); H.hold(bl, f.rig, side, 0.0)
    li = bpy.data.lights.new("dawn_blade", "POINT"); li.energy = 40; li.color = (1.0, 0.8, 0.5); li.shadow_soft_size = 0.3
    lo = bpy.data.objects.new("dawn_blade", li); C.sc.collection.objects.link(lo); H.hold(lo, f.rig, side, length * 0.6)
    f.add(sw, bl, lo)


def measuring_rod(f, side=".r", length=1.2):
    BR = C.mat("rod_brass", (0.7, 0.5, 0.2), 0.3, metal=1.0)
    r = _cyl(0.012, length, 0, 8); r.data.materials.append(BR)
    for k in range(8):
        t = _cyl(0.0135, 0.004, -length / 2 + (k + 1) * length / 9, 8); t.data.materials.append(C.mat("rod_mark", (0.05, 0.04, 0.03), 0.5))
        t.data.transform(Matrix.Translation(t.location)); t.location = (0, 0, 0)
        r = _join([r, t], "measuring_rod")
    H.hold(r, f.rig, side, length * 0.35)
    f.add(r)


def locket(f, side=".l"):
    GOLD = C.mat("locket_gold", (0.85, 0.62, 0.25), 0.25, metal=1.0)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.025, location=(0, 0, 0)); l = bpy.context.object; l.scale = (1, 0.4, 1.2)
    l.data.materials.append(GOLD); bpy.ops.object.shade_smooth()
    H.hold(l, f.rig, side, -0.02)
    f.add(l)


# ------------------------------------------------------------------ batch 2
def sylvaine(rig, body, ex, J):
    """Sylvaine Thornwhisper, Bow of the Deep. 300 (looks 30), tall, slender. Green and bark-brown layered leathers, a
    cloak of living moss, longbow of pale white wood that has sprouted leaves, gold freckles that glow faintly."""
    f = Fig(rig, body, ex, J)
    f.skin((0.58, 0.4, 0.3), iris=(0.2, 0.32, 0.08))
    GREEN = leather("sylvaine_green", (0.06, 0.12, 0.04))
    BARK = leather("sylvaine_bark", (0.1, 0.065, 0.035))
    MOSS = H.robe_cloth("moss", (0.05, 0.11, 0.03), rough=1.0, sheen=0.6)
    ax = Fig.ax
    f.add(H.wear(body, "leathers", lambda c: f.torso(f.pel - 0.15, f.neck - 0.05, 0.02)(c) or f.sleeves(0.04)(c), GREEN, 0.014, 0.008, smooth=8))
    f.add(H.wear(body, "bark_layers", lambda c: f.s4 - 0.05 < c.z < f.s2 and ax(c) < f.sh.x, BARK, 0.03, 0.01, smooth=12))
    f.add(H.wear(body, "leggings", lambda c: f.an + 0.1 < c.z < f.pel + 0.02 and ax(c) < 0.4, BARK, 0.01, 0.006))
    cp = back_cape(f, MOSS, length=(f.sh.z - f.an) - 0.05, width=0.68, name="moss_cloak")
    tx = bpy.data.textures.new("moss_tufts", "CLOUDS"); tx.noise_scale = 0.02
    dm = cp.modifiers.new("tufts", "DISPLACE"); dm.texture = tx; dm.strength = 0.02
    f.add(H.wear(body, "freckles", lambda c: c.y < f.eye.y + 0.02 and f.mouth.z < c.z < f.eye.z and ax(c) < 0.07,
                 rune_overlay("gold_freckles", (1.0, 0.75, 0.3), 160, 1.5, 0.03), 0.001, 0.0))
    boots(f, BARK)
    hair(f, 0.55, 20000, comb_front=(0, 1, 0.05), comb_back=(0, 0.45, -1), hang_below=f.eye.z - 0.03, melanin=0.35, redness=0.55)
    brows(f, 250, 0.011, melanin=0.35, redness=0.55)
    longbow(f)
    return [body] + f.parts


def mirelle(rig, body, ex, J):
    """Mirelle the Tide-Seer. 19, small, pale. Layers of white and teal sea-wool, pearls sewn on everything, milky blind
    eyes, a staff of clear ice with a fish skeleton frozen inside; barefoot."""
    f = Fig(rig, body, ex, J)
    f.skin((0.68, 0.52, 0.45), iris=(0.55, 0.62, 0.62))
    WOOL = H.robe_cloth("sea_wool", (0.62, 0.66, 0.64), rough=0.95, sheen=0.4)
    TEAL = H.robe_cloth("teal_wool", (0.04, 0.2, 0.2), rough=0.95, sheen=0.4)
    PEARL = C.mat("pearl", (0.85, 0.83, 0.8), 0.15)
    PEARL.node_tree.nodes["Principled BSDF"].inputs["Coat Weight"].default_value = 1.0
    f.add(H.wear(body, "wool_top", lambda c: f.torso(f.pel - 0.1, f.neck - 0.03, 0.03)(c) or f.sleeves(0.02)(c), WOOL, 0.025, 0.01, smooth=14))
    f.add(H.wear(body, "teal_wrap", lambda c: f.s2 - 0.02 < c.z < f.neck + 0.0 and abs(c.x) < f.sh.x + 0.1, TEAL, 0.045, 0.012, smooth=14))
    f.add(H.skirt("wool_skirt", J, f.s4 + 0.02, f.an + 0.05, 0.17, 0.36, TEAL, rig, folds=0.03))
    f.add(H.skirt("wool_underskirt", J, f.s4 - 0.1, f.an - 0.02, 0.16, 0.3, WOOL, rig, folds=0.02))
    random.seed(21)
    for i in range(40):   # pearls on the wrap and skirt
        a = random.uniform(0, 2 * math.pi); z = random.uniform(f.kn, f.neck - 0.04)
        r = 0.2 if z < f.s4 else 0.17
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.008, location=(math.cos(a) * r, J["pelvis"].y + math.sin(a) * r * 0.85, z))
        p = bpy.context.object; p.data.materials.append(PEARL)
        H.on_bone(p, rig, "hips" if z < f.s4 else "chest"); f.add(p)
    H.hide_under(body, lambda c: (c.z < f.pel - 0.06 and abs(c.x) < 0.4 and c.z > f.an + 0.03))   # barefoot: feet show
    hair(f, 0.35, 18000, comb_front=(0, 1, 0.0), comb_back=(0, 0.4, -1), hang_below=f.eye.z - 0.04, colour=(0.75, 0.73, 0.68))
    brows(f, 200, 0.01, colour=(0.7, 0.68, 0.62))
    ice_staff(f)
    return [body] + f.parts


def ilyra(rig, body, ex, J):
    """Ilyra the Unbroken. 22, thin, hollow-cheeked, intense. Torn dark-blue Veilwalker student robes, bare arms with
    black veins, white hair, a broken astrolabe on a chain."""
    f = Fig(rig, body, ex, J)
    f.skin((0.6, 0.45, 0.4), iris=(0.22, 0.24, 0.3))
    ROBE = H.robe_cloth("veil_robe", (0.025, 0.035, 0.08), patches=0.06)
    ax = Fig.ax
    f.add(H.wear(body, "robe_top", f.torso(f.pel - 0.1, f.neck - 0.03, 0.025), ROBE, 0.018, 0.008, smooth=12))
    sk = H.skirt("robe_skirt", J, f.s4 + 0.02, 0.02, 0.17, 0.38, ROBE, rig, folds=0.035)
    tx = bpy.data.textures.new("torn_hem", "CLOUDS"); tx.noise_scale = 0.06
    f.add(sk)
    f.add(H.wear(body, "veins", lambda c: abs(c.x) > f.sh.x + 0.03 and abs(c.x) < f.wr.x and c.z > f.neck - 0.4,
                 rune_overlay("black_veins", (0.02, 0.0, 0.03), 40, 0, 0.025), 0.0015, 0.0))
    f.hide_legs()
    hair(f, 0.3, 18000, comb_front=(0, 1, -0.2), comb_back=(0, 0.5, -1), hang_below=f.eye.z - 0.03, jitter=0.3, colour=(0.85, 0.85, 0.84))
    brows(f, 220, 0.011, colour=(0.75, 0.75, 0.74))
    astrolabe(f)
    return [body] + f.parts


def seraphel(rig, body, ex, J, dim=0.0):
    """Seraphel the Dawnblade, Knight of the Sunstone. Looks 40, tall, broad-shouldered, grave. White-gold plate etched
    with six colours (dim 0 = bright, 1 = nearly grey), a greatsword of Sunstone glass, gold eyes, cropped grey hair."""
    f = Fig(rig, body, ex, J)
    f.skin((0.55, 0.36, 0.27), iris=(0.75, 0.55, 0.15))
    PL = H.steel("white_gold_plate", 0.03)
    b = PL.node_tree.nodes["Principled BSDF"]; b.inputs["Base Color"].default_value = (0.9, 0.84, 0.68, 1)
    plate_set(f, PL, pauldron=1.2, chest=0.04)
    f.add(H.wear(body, "underlayer", f.sleeves(0.05), H.quilted("seraphel_under", (0.25, 0.22, 0.18)), 0.014, 0.01))
    f.add(H.wear(body, "etch", lambda c: abs(c.x) < f.sh.x - 0.05 and f.s2 < c.z < f.neck - 0.1 and c.y < J["spine-1"].y,
                 rune_overlay("six_etch", (0.9, 0.7, 0.4), 22, 3 * (1 - dim), 0.02), 0.05, 0.0))
    boots(f, H.steel("sabatons", 0.03), high=False)
    hair(f, 0.03, 14000, colour=(0.45, 0.44, 0.42))
    stubble(f, colour=(0.4, 0.38, 0.36))
    brows(f, 300, 0.012, colour=(0.4, 0.38, 0.36))
    back_cape(f, H.robe_cloth("seraphel_cape", (0.55, 0.5, 0.4), rough=0.8), length=(f.sh.z - f.kn) + 0.1, width=0.75)
    glass_greatsword(f)
    return [body] + f.parts


def fennick(rig, body, ex, J):
    """Master Tobias Fennick, Chief Tower-Wright. 70, short, stout, red-faced, bald with huge white side-whiskers.
    Brass-buttoned waistcoat over a stained shirt, magnifying spectacles pushed up on his head, a tool belt, a brass
    measuring rod."""
    f = Fig(rig, body, ex, J)
    f.skin((0.62, 0.33, 0.25), iris=(0.2, 0.25, 0.3))
    SHIRT = H.robe_cloth("fennick_shirt", (0.36, 0.32, 0.25), patches=0.12)
    VEST = H.robe_cloth("fennick_waistcoat", (0.12, 0.06, 0.04), rough=0.6, sheen=0.3)
    BRASS = C.mat("fennick_brass", (0.75, 0.52, 0.2), 0.3, metal=1.0)
    ax = Fig.ax
    f.add(H.wear(body, "shirt", lambda c: f.torso(f.pel - 0.05, f.neck - 0.02, 0.02)(c) or f.sleeves(0.04)(c), SHIRT, 0.012, 0.006, smooth=8))
    f.add(H.wear(body, "waistcoat", f.torso(f.pel - 0.03, f.neck - 0.07, -0.02), VEST, 0.03, 0.01, smooth=14))
    f.add(H.wear(body, "breeches", lambda c: f.kn - 0.05 < c.z < f.pel + 0.02 and ax(c) < 0.4, H.cloth("fennick_breeches", (0.1, 0.08, 0.06)), 0.014, 0.008))
    f.add(H.wear(body, "toolbelt", lambda c: f.pel - 0.02 < c.z < f.pel + 0.05 and ax(c) < 0.3, leather("toolbelt", (0.12, 0.07, 0.035)), 0.05, 0.012))
    for k in range(5):   # brass buttons down the waistcoat
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.009, location=(0, J["spine-2"].y - 0.2, f.s4 + 0.04 + k * 0.06))
        bt = bpy.context.object; bt.data.materials.append(BRASS); H.on_bone(bt, rig, "chest" if k > 2 else "spine"); f.add(bt)
    boots(f, leather("fennick_boots", (0.06, 0.04, 0.03)), high=False)
    f.add(H.wear(body, "stockings", lambda c: f.an + 0.03 < c.z < f.kn - 0.03 and ax(c) < 0.4, H.cloth("stockings", (0.22, 0.2, 0.17)), 0.006, 0.004))
    # side-whiskers: big white mutton-chops from the cheeks and jaw
    mz = f.mouth.z
    chops = lambda c: (0.04 < ax(c) < 0.085 and f.jaw.z - 0.02 < c.z < f.eye.z - 0.02 and c.y < J["head"].y + 0.02)
    f.add(H.comb_hair(rig, H.scalp_points(body, chops, 12000, seed=14), f.hc, "whiskers", 0.04,
                      lambda p: (0.5 * p.x / max(abs(p.x), 1e-3), -0.2, -1.0), segs=6, lift=0.0, jitter=0.25, radius=0.0012,
                      push=0.15, wrap_above=99.0, colour=(0.85, 0.84, 0.8)))
    side = lambda c: abs(c.x) > 0.06 and c.z < f.eye.z + 0.05 and c.y > f.eye.y + 0.05 and f.scalp(c)
    hair(f, 0.025, 6000, keep=side, colour=(0.85, 0.84, 0.8))
    brows(f, 500, 0.018, colour=(0.85, 0.84, 0.8))
    # magnifying spectacles pushed up on the bald head
    for sx in (-1, 1):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.022, minor_radius=0.003, location=(sx * 0.03, J["head"].y - 0.06, f.eye.z + 0.1))
        g = bpy.context.object; g.rotation_euler.x = math.radians(60); g.data.materials.append(BRASS); H.on_bone(g, rig, "head"); f.add(g)
        bpy.ops.mesh.primitive_cylinder_add(radius=0.02, depth=0.004, location=(sx * 0.03, J["head"].y - 0.06, f.eye.z + 0.1))
        l = bpy.context.object; l.rotation_euler.x = math.radians(60)
        gl = C.mat("lens", (0.9, 0.9, 0.9), 0.02); gl.node_tree.nodes["Principled BSDF"].inputs["Transmission Weight"].default_value = 1.0
        l.data.materials.append(gl); H.on_bone(l, rig, "head"); f.add(l)
    measuring_rod(f)
    return [body] + f.parts


def cassivane(rig, body, ex, J, ashen=False):
    """Cassivane Dral, the Lord Marshal. 55, tall, handsome, broad, grey at the temples. Polished steel and red-enamel
    plate, a red cloak, a short silver beard, a gold locket always in his hand. (ashen: the armour blackened and flaking,
    ash drifting off him, Heartstone shards growing from his shoulders, eyes grey.)"""
    f = Fig(rig, body, ex, J)
    f.skin((0.5, 0.33, 0.25) if not ashen else (0.36, 0.33, 0.32), iris=(0.25, 0.18, 0.1) if not ashen else (0.6, 0.6, 0.62))
    if ashen:
        PL = enamel_plate("burned_plate", (0.03, 0.025, 0.025), dent=0.4)
        PL.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.85
    else:
        PL = enamel_plate("marshal_plate", (0.38, 0.05, 0.04), dent=0.03)
    plate_set(f, PL, pauldron=1.1)
    f.add(H.wear(body, "arming_coat", f.sleeves(0.05), H.quilted("marshal_under", (0.1, 0.03, 0.03)), 0.014, 0.01))
    boots(f, H.steel("marshal_sabatons", 0.04), high=False)
    cape = back_cape(f, H.robe_cloth("marshal_cloak", (0.28, 0.02, 0.02) if not ashen else (0.04, 0.03, 0.03), rough=0.8),
                     length=(f.sh.z - f.an) - 0.05, width=0.8, name="marshal_cloak")
    TEMPLE = dict(colour=(0.18, 0.15, 0.13))
    hair(f, 0.06, 16000, **TEMPLE)
    stubble(f, 0.012, 16000, 0.0009, colour=(0.62, 0.62, 0.6))   # a short, trimmed silver beard
    brows(f, 300, 0.013, **TEMPLE)
    locket(f)
    if ashen:
        H.grey_dust(cape, 700, (0.3, 0.29, 0.28))
        SH = H.glow_mat("heartstone_shard", (0.85, 0.55, 1.0), 6)
        random.seed(31)
        for side in (1, -1):
            for k in range(5):
                bpy.ops.mesh.primitive_cone_add(radius1=0.03, radius2=0.0, depth=random.uniform(0.15, 0.32), vertices=5,
                                                location=(side * (f.sh.x + random.uniform(-0.05, 0.08)), J["spine-1"].y + random.uniform(-0.05, 0.08), f.sh.z + 0.06))
                s = bpy.context.object; s.rotation_euler = (random.uniform(-0.6, 0.6), side * random.uniform(0.2, 0.8), 0)
                s.data.materials.append(SH); H.on_bone(s, rig, "upperarm" + (".l" if side > 0 else ".r")); f.add(s)
    return [body] + f.parts


def keeper(rig, body, ex, J):
    """Vael-Orrun as the Keeper of the Crossroads (the painted memory in the_truth): about 40, kind-faced, plain grey
    robes, no crown, ink on his fingers, a Tidefolk wedding ring, warm brown eyes."""
    f = Fig(rig, body, ex, J)
    f.skin((0.55, 0.38, 0.28), iris=(0.22, 0.12, 0.05))
    ROBE = H.robe_cloth("keeper_robe", (0.16, 0.16, 0.15))
    f.add(H.wear(body, "robe_top", lambda c: f.torso(f.pel - 0.1, f.neck - 0.02, 0.025)(c) or f.sleeves(0.02)(c), ROBE, 0.02, 0.01, smooth=14))
    f.add(H.skirt("robe_skirt", J, f.s4 + 0.02, 0.03, 0.19, 0.4, ROBE, rig, folds=0.03))
    f.hide_legs()
    f.add(H.wear(body, "ink", lambda c: abs(c.x) > J["l-finger-3-1"].x - 0.02, rune_overlay("ink", (0.02, 0.02, 0.04), 60, 0, 0.12), 0.001, 0.0))
    hair(f, 0.07, 18000, melanin=0.85, redness=0.3)
    stubble(f, 0.01, 15000, 0.0009, melanin=0.85, redness=0.3)
    brows(f, 300, 0.012, melanin=0.85, redness=0.3)
    return [body] + f.parts


H.HUMANS["sylvaine"] = (dict(height=2.3, gender=0.0, muscle=0.45, weight=0.15, tall=0.95, age=0.55,
                             targets={"ears/l-ear-shape-pointed": 1.0, "ears/r-ear-shape-pointed": 1.0}), sylvaine)
H.HUMANS["mirelle"] = (dict(height=1.85, gender=0.0, muscle=0.2, weight=0.2, tall=0.15, age=0.45), mirelle)
H.POSTURES["mirelle"] = H.POSTURES["ysolde"]
H.HUMANS["ilyra"] = (dict(height=2.0, gender=0.0, muscle=0.2, weight=0.0, tall=0.5, age=0.49,
                          targets={"cheek/l-cheek-volume-decr": 1.0, "cheek/r-cheek-volume-decr": 1.0}), ilyra)
H.HUMANS["seraphel"] = (dict(height=2.4, gender=1.0, muscle=0.85, weight=0.5, tall=0.9, age=0.6), seraphel)
H.HUMANS["fennick"] = (dict(height=1.8, gender=1.0, muscle=0.3, weight=0.95, tall=0.0, age=0.85), fennick)
H.HUMANS["cassivane"] = (dict(height=2.35, gender=1.0, muscle=0.7, weight=0.55, tall=0.85, age=0.68), cassivane)
H.HUMANS["cassivane_ash"] = (H.HUMANS["cassivane"][0], lambda r, b, e, j: cassivane(r, b, e, j, ashen=True))
H.HUMANS["keeper"] = (dict(height=2.2, gender=1.0, muscle=0.45, weight=0.45, tall=0.7, age=0.62), keeper)
H.HUMANS["ysolde_blind"] = (H.HUMANS["ysolde"][0], lambda r, b, e, j: H.ysolde_mh(r, b, e, j, blind=True))
H.POSTURES["ysolde_blind"] = H.POSTURES["ysolde"]
H.HUMANS["seraphel_grey"] = (H.HUMANS["seraphel"][0], lambda r, b, e, j: seraphel(r, b, e, j, dim=1.0))
