"""Shared building blocks for the Blender cinematic shots (cinema/blender/shots/*.py).

A shot script does `import cine3d as C`, builds its set with these helpers, keys its camera, then calls C.render().
Run any shot with:  blender -b -P cinema/blender/shots/<shot>.py -- OUT_DIR [--frames a b] [--res 67] [--samples 32] [--gpu]
Stand-in characters are CC0 KayKit packs (Kay Lousberg) in $KAYKIT; scenery textures are CC0 Poly Haven in ph/.
"""
import bpy, math, random, sys, os

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(HERE, "ph")
ASSETS = os.environ.get("KAYKIT", "/home/user/assets3d")
KK = ASSETS + "/kaykit/addons/kaykit_character_pack_adventures/Characters/gltf/"
SK = ASSETS + "/skeletons/addons/kaykit_character_pack_skeletons/Characters/gltf/"
FPS = 24

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def opt(name, default, n=1):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default


OUT = argv[0] if argv and not argv[0].startswith("--") else "/tmp/shot"
sc = None


def setup(seconds, seed=7):
    """Empty scene, `seconds` long at 24 fps. Returns the scene."""
    global sc
    random.seed(seed)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, int(round(seconds * FPS))
    return sc


def sec(t):
    return 1 + t * FPS


# ------------------------------------------------------------------ materials
def mat(name, base, rough=0.8, emit=None, strength=0.0, metal=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    return m


def pbr(name, folder, scale, tint=(1, 1, 1), bump=0.6):
    """A Poly Haven texture set (diff, nor_gl, rough, disp), box-projected in object space."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])

    def img(kind, colour):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(PH, folder, "%s_%s_1k.jpg" % (folder, kind)), check_existing=True)
        t.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        t.projection = "BOX"; t.projection_blend = 0.3
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    tint_n = nt.nodes.new("ShaderNodeMix"); tint_n.data_type = "RGBA"; tint_n.blend_type = "MULTIPLY"
    tint_n.inputs["Factor"].default_value = 1.0; tint_n.inputs["B"].default_value = (*tint, 1)
    nt.links.new(img("diff", True).outputs["Color"], tint_n.inputs["A"])
    nt.links.new(tint_n.outputs["Result"], b.inputs["Base Color"])
    nt.links.new(img("rough", False).outputs["Color"], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(img("nor_gl", False).outputs["Color"], nm.inputs["Color"])
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = bump
    nt.links.new(img("disp", False).outputs["Color"], bu.inputs["Height"]); nt.links.new(nm.outputs["Normal"], bu.inputs["Normal"])
    nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


_mats = {}


def M(name):
    """The shared palette, built on first use."""
    if name not in _mats:
        _mats[name] = {
            "rock": lambda: pbr("rock", "dark_rock_02", 0.08, (0.8, 0.8, 0.85)),
            "gate": lambda: pbr("gate", "castle_wall_slates", 0.12, (0.55, 0.55, 0.6), 0.8),
            "ground": lambda: pbr("ground", "gray_rocks", 0.25, (0.7, 0.7, 0.72)),
            "mud": lambda: pbr("mud", "brown_mud_02", 0.2, (0.6, 0.58, 0.6)),
            "iron": lambda: mat("iron", (0.05, 0.045, 0.04), 0.45, metal=0.6),
            "white_stone": lambda: pbr("white_stone", "castle_wall_slates", 0.15, (1.25, 1.2, 1.25), 0.5),
            "lantern": lambda: mat("lantern", (1.0, 0.7, 0.35), 0.4, emit=(1.0, 0.62, 0.25), strength=12),
            "white_lantern": lambda: mat("white_lantern", (1, 1, 1), 0.3, emit=(0.92, 0.95, 1.0), strength=30),
            "fire": lambda: mat("fire", (1.0, 0.45, 0.12), 0.5, emit=(1.0, 0.42, 0.1), strength=18),
            "gap": lambda: mat("gap", (0, 0, 0), 1.0, emit=(0.55, 0.58, 0.66), strength=3.0),
            "grey_eye": lambda: mat("grey_eye", (0.8, 0.82, 0.85), 0.3, emit=(0.85, 0.88, 0.95), strength=12),
            "black": lambda: mat("black", (0.0, 0.0, 0.0), 1.0),
            "pale": lambda: mat("pale", (0.55, 0.53, 0.5), 0.75),
        }[name]()
    return _mats[name]


# ------------------------------------------------------------------ geometry
def box(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3
    return o


def rough_up(obj, strength, scale, subdiv=5):
    m = obj.modifiers.new("sub", "SUBSURF"); m.levels = m.render_levels = subdiv; m.subdivision_type = "SIMPLE"
    tex = bpy.data.textures.new(obj.name + "_n", "CLOUDS"); tex.noise_scale = scale; tex.noise_depth = 5
    d = obj.modifiers.new("disp", "DISPLACE"); d.texture = tex; d.strength = strength; d.texture_coords = "GLOBAL"
    t2 = bpy.data.textures.new(obj.name + "_v", "VORONOI"); t2.noise_scale = scale * 0.35
    d2 = obj.modifiers.new("cracks", "DISPLACE"); d2.texture = t2; d2.strength = strength * 0.35; d2.texture_coords = "GLOBAL"


_scans = {}


def scan(folder, loc, rot_z, scale, material=None):
    """A linked copy of a Poly Haven scanned rock."""
    if folder not in _scans:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(PH, folder, folder + "_1k.gltf"))
        src = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
        src.hide_render = src.hide_viewport = True
        _scans[folder] = src
    o = _scans[folder].copy(); sc.collection.objects.link(o)
    o.hide_render = o.hide_viewport = False
    o.rotation_mode = "XYZ"; o.location = loc; o.rotation_euler = (0, 0, rot_z); o.scale = (scale,) * 3
    if material:
        o.data = o.data.copy(); o.data.materials[0] = material
    return o


def canyon(y0=20, y1=-100, gate_y=-95, floor=True, walls_h=170, depth=0):
    """The Rift: a gravel road between textured rock walls that widen into a hall before the gate."""
    if floor:
        g = box("road", (0, (y0 + y1) / 2 - 20, -0.5 + depth), (240, abs(y1 - y0) + 80, 1), M("ground"))
        rough_up(g, 0.6, 3.0, 5)
    k = 0
    y = y0
    while y > y1 - 10:
        for side in (-1, 1):
            w = 14 + random.uniform(0, 6)
            t = (y0 - y) / max(y0 - gate_y, 1)
            inner = 15 + (t * 4) ** 2 * 6 * 0.6 + random.uniform(0, 2)
            c = box("cliff", (side * (inner + w / 2), y, walls_h / 2 - 5 + depth), (w, 34, walls_h + random.uniform(-10, 30)), M("rock"))
            c.rotation_euler.z = random.uniform(-0.15, 0.15)
            rough_up(c, 6.0, 9.0, 6)
        y -= 24
        k += 1
    for _ in range(14):
        x = random.choice((-1, 1)) * random.uniform(4.5, 11)
        scan("rock_face_02", (x, random.uniform(y1 + 15, y0), -0.6 + depth), random.uniform(0, 6.3), random.uniform(0.5, 1.3), M("rock"))


class Gate:
    """The Black Gate: two mountain-tall doors in a carved frame. `open_to(frame, gap)` keys the gap in metres."""
    G = 1.9

    def __init__(self, y=-95):
        G = self.G
        self.y = y
        for side in (-1, 1):
            box("frame_post", (side * 22 * G, y, 40 * G), (10 * G, 10 * G, 80 * G), M("gate"), 0.4)
        box("lintel", (0, y, 84 * G), (56 * G, 12 * G, 10 * G), M("gate"), 0.5)
        self.doors = []
        for side in (-1, 1):
            # Each door hinges on its outer post: an empty at the hinge carries the slab and its iron bands.
            hinge = bpy.data.objects.new("hinge", None); sc.collection.objects.link(hinge)
            hinge.location = (side * 18.8 * G, y + 1, 0)
            door = box("door", (-side * 8.9 * G, 0, 33 * G), (17.8 * G, 3 * G, 66 * G), M("gate"), 0.3)
            door.parent = hinge
            rough_up(door, 0.6, 2.0, 4)
            for r in range(6):
                b = box("band", (-side * 8.9 * G, 1.7 * G, (6 + r * 10.5) * G), (16.5 * G, 0.6 * G, 1.2 * G), M("iron"), 0.1)
                b.parent = hinge
            self.doors.append((side, hinge))
        self.slit = box("gap_light", (0, y - 45, 30 * G), (0.01, 0.5, 60 * G), M("gap"))
        self.light = bpy.data.objects.new("gaplight", bpy.data.lights.new("gaplight", "AREA")); sc.collection.objects.link(self.light)
        L = self.light.data; L.energy = 0; L.color = (0.7, 0.74, 0.85); L.shape = "RECTANGLE"; L.size = 2; L.size_y = 50 * G
        self.light.location = (0, y - 3, 30 * G); self.light.rotation_euler = (math.radians(-90), 0, 0)

    def open_to(self, frame, gap, interp="BEZIER"):
        """Key the gap between the doors (metres) at `frame`; 0 = shut."""
        G = self.G
        ang = math.asin(min(gap / 2 / (17.8 * G), 0.9))
        for side, hinge in self.doors:
            hinge.rotation_euler.z = side * ang  # doors swing away from the camera (towards -Y)
            hinge.keyframe_insert("rotation_euler", index=2, frame=frame)
        self.slit.scale.x = max(gap * 260, 0.001)
        self.slit.keyframe_insert("scale", index=0, frame=frame)
        self.light.data.energy = 60000 * min(gap / 2.6, 1.5)
        self.light.data.keyframe_insert("energy", frame=frame)


# ------------------------------------------------------------------ characters
HELD = ("Sword", "Shield", "Axe", "Staff", "Crossbow", "Dagger", "Wand", "Mug", "Spellbook", "Throwable", "Knife", "Blade")


def char(path, loc, rot_z, action, phase=0.0, keep=(), scale=1.0):
    """A rigged CC0 stand-in with `action` looping on an NLA strip (offset by `phase` of a cycle)."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        held = any(w in o.name for w in HELD)
        if o.type == "MESH" and ((held and not any(k in o.name for k in keep)) or o.parent is None):
            o.hide_render = o.hide_viewport = True
    rig.rotation_mode = "XYZ"; rig.location = loc; rig.rotation_euler = (0, 0, rot_z); rig.scale = (scale,) * 3
    play(rig, action, phase)
    rig["meshes"] = [o.name for o in new if o.type == "MESH" and not o.hide_render]
    return rig


def play(rig, action, phase=0.0, start=1, repeat=None):
    act = bpy.data.actions.get(action)
    ad = rig.animation_data_create(); ad.action = None
    for tr in list(ad.nla_tracks):
        ad.nla_tracks.remove(tr)
    a0, a1 = act.frame_range
    length = max(a1 - a0, 1)
    strip = ad.nla_tracks.new().strips.new(action, int(start - phase * length), act)
    strip.repeat = repeat or (math.ceil((sc.frame_end + length) / length) + 1)
    return strip


def recolour(rig, rgb, strength=0.65):
    """Tint a stand-in's materials towards `rgb` (cloth colours for factions)."""
    for name in rig["meshes"]:
        o = bpy.data.objects[name]
        for i, m in enumerate(o.data.materials):
            if m is None:
                continue
            m2 = m.copy(); o.data.materials[i] = m2
            nt = m2.node_tree; b = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
            if b is None:
                continue
            mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"
            mix.inputs["Factor"].default_value = 1.0; mix.inputs["B"].default_value = (*rgb, 1)
            hs = nt.nodes.new("ShaderNodeHueSaturation"); hs.inputs["Saturation"].default_value = 1.0 - strength
            src = b.inputs["Base Color"].links[0].from_socket if b.inputs["Base Color"].links else None
            if src:
                nt.links.new(src, hs.inputs["Color"])
            else:
                hs.inputs["Color"].default_value = b.inputs["Base Color"].default_value
            nt.links.new(hs.outputs["Color"], mix.inputs["A"])
            nt.links.new(mix.outputs["Result"], b.inputs["Base Color"])


def attach(obj, rig, bone, loc=(0, 0, 0), rot=(0, 0, 0)):
    obj.parent = rig; obj.parent_type = "BONE"; obj.parent_bone = bone
    obj.location = loc; obj.rotation_euler = rot


def lantern(rig, bone="handslot.r", pole=1.6, white=False, energy=160):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=pole)
    p = bpy.context.object; p.data.materials.append(M("iron"))
    attach(p, rig, bone, (0, pole / 2 - 0.3, 0), (math.pi / 2, 0, 0))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22)
    g = bpy.context.object; g.data.materials.append(M("white_lantern" if white else "lantern"))
    attach(g, rig, bone, (0, pole - 0.2, 0))
    li = bpy.data.lights.new("lantern", "POINT"); li.energy = energy; li.shadow_soft_size = 0.25
    li.color = (0.9, 0.94, 1.0) if white else (1.0, 0.62, 0.3)
    lo = bpy.data.objects.new("lantern_light", li); sc.collection.objects.link(lo)
    attach(lo, rig, bone, (0, pole - 0.2, 0))
    return g, lo


def grey_eyes(rig, size=0.045):
    """Two small grey glowing eyes on the head bone: the mark of the Hush's servants."""
    for side in (-1, 1):
        bpy.ops.mesh.primitive_uv_sphere_add(radius=size)
        e = bpy.context.object; e.data.materials.append(M("grey_eye"))
        attach(e, rig, "head", (side * 0.17, 0.42, 0.42))


def march(rig, speed, axis=1, sign=-1):
    """Move a character steadily along an axis with a driver (metres per second)."""
    v0 = rig.location[axis]
    d = rig.driver_add("location", axis).driver
    d.expression = "%f + %f * frame" % (v0, sign * speed / FPS)


# ------------------------------------------------------------------ light and air
def world(density=0.008, sky=0.05, colour=(0.03, 0.035, 0.06)):
    w = bpy.data.worlds.new("w"); sc.world = w; w.use_nodes = True
    nt = w.node_tree; bg = nt.nodes["Background"]
    bg.inputs["Color"].default_value = (*colour, 1); bg.inputs["Strength"].default_value = 1
    hdr = os.path.join(PH, "fouriesburg_mountain_cloudy", "fouriesburg_mountain_cloudy_1k.hdr")
    if sky and os.path.exists(hdr):
        env = nt.nodes.new("ShaderNodeTexEnvironment"); env.image = bpy.data.images.load(hdr)
        nt.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = sky
    if density:
        vol = nt.nodes.new("ShaderNodeVolumePrincipled")
        vol.inputs["Density"].default_value = density; vol.inputs["Color"].default_value = (0.6, 0.62, 0.75, 1)
        vol.inputs["Anisotropy"].default_value = 0.4
        nt.links.new(vol.outputs[0], nt.nodes["World Output"].inputs["Volume"])
    return w


def light(kind, loc, rot, energy, colour, size=1.0, name="light"):
    L = bpy.data.lights.new(name, kind); L.energy = energy; L.color = colour
    if kind == "AREA":
        L.size = size
    elif kind == "SUN":
        L.angle = 0.02
    elif kind in ("POINT", "SPOT"):
        L.shadow_soft_size = size
    o = bpy.data.objects.new(name, L); sc.collection.objects.link(o)
    o.location = loc; o.rotation_euler = tuple(math.radians(a) for a in rot)
    return o


def moon(energy=4.0, rot=(35, -30, 150)):
    return light("SUN", (0, 0, 100), rot, energy, (0.45, 0.58, 1.0), name="moon")


def brazier(x, y, z=0.0, energy=500):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.5, depth=1.6, location=(x, y, z + 0.8)); bpy.context.object.data.materials.append(M("iron"))
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.45, subdivisions=2, location=(x, y, z + 1.75))
    f = bpy.context.object; f.data.materials.append(M("fire")); f.scale = (1, 1, 1.5)
    return light("POINT", (x, y, z + 2.4), (0, 0, 0), energy, (1.0, 0.5, 0.18), 0.6, "brazier")


# ------------------------------------------------------------------ camera
def camera(lens=35, fstop=None, focus=None):
    cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
    cam.data.lens = lens; cam.data.sensor_width = 36; cam.data.clip_end = 3000
    if fstop:
        cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = fstop
        if isinstance(focus, (int, float)):
            cam.data.dof.focus_distance = focus
        elif focus is not None:
            cam.data.dof.focus_object = focus
    return cam


def key_cam(cam, keys):
    """keys: [(seconds, (x, y, z), (pitch, roll, yaw) in degrees), ...]; eased in and out between keys.
    (90, 0, 180) looks along -Y, level."""
    for t, loc, rot in keys:
        cam.location = loc; cam.rotation_euler = tuple(math.radians(a) for a in rot)
        cam.keyframe_insert("location", frame=sec(t)); cam.keyframe_insert("rotation_euler", frame=sec(t))


def shake(cam, amount=0.05, freq=8.0):
    """Hand-held wobble on the camera's rotation (noise modifiers on its rotation curves)."""
    ad = cam.animation_data
    if not ad or not ad.action:
        cam.keyframe_insert("rotation_euler", frame=1)
        ad = cam.animation_data
    curves = getattr(ad.action, "fcurves", None)
    if curves is None:
        curves = [fc for layer in ad.action.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]
    for fc in curves:
        if fc.data_path == "rotation_euler":
            n = fc.modifiers.new("NOISE"); n.strength = amount; n.scale = FPS / freq; n.phase = random.uniform(0, 100)


# ------------------------------------------------------------------ render
def render(default_res=67, default_samples=32):
    f0, f1 = (int(x) for x in opt("--frames", [str(sc.frame_start), str(sc.frame_end)], 2))
    r = sc.render
    r.engine = "CYCLES"; sc.cycles.device = "CPU"
    if "--gpu" in argv:
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("METAL", "OPTIX", "CUDA", "HIP", "ONEAPI"):
            try:
                prefs.compute_device_type = kind
            except TypeError:
                continue
            prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == kind
                sc.cycles.device = "GPU"
                break
    sc.cycles.samples = int(opt("--samples", str(default_samples))); sc.cycles.use_denoising = True
    sc.cycles.volume_step_rate = 4; sc.cycles.max_bounces = 4
    r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, int(opt("--res", str(default_res)))
    r.use_motion_blur = True; r.motion_blur_shutter = 0.5
    sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"
    r.image_settings.file_format = "PNG"
    os.makedirs(OUT, exist_ok=True)
    for f in range(f0, f1 + 1, int(opt("--step", "1"))):   # --step N: every Nth frame (animatic previews)
        path = os.path.join(OUT, "f%04d.png" % f)
        if os.path.exists(path) and "--force" not in argv:
            continue  # resumable: rerun the same command to finish a cut-short render
        sc.frame_set(f)
        r.filepath = path
        bpy.ops.render.render(write_still=True)


ELEMENTS = [(1.0, 0.25, 0.08), (0.75, 0.85, 1.0), (0.35, 1.0, 0.3), (0.15, 0.85, 0.85), (0.95, 0.7, 0.25), (0.65, 0.3, 1.0)]


def tower(x, y, col, h=9.0):
    """A Spirewright tower: a stone spire with a glowing crystal in its element's colour. Returns the crystal."""
    bpy.ops.mesh.primitive_cone_add(vertices=6, radius1=1.6, radius2=0.7, depth=h, location=(x, y, h / 2))
    s = bpy.context.object; s.data.materials.append(M("pale"))
    bpy.ops.mesh.primitive_ico_sphere_add(radius=0.8, subdivisions=1, location=(x, y, h + 0.9))
    c = bpy.context.object; c.scale = (0.8, 0.8, 1.4)
    c.data.materials.append(mat("crystal", col, 0.2, emit=col, strength=10))
    light("POINT", (x, y, h + 1.0), (0, 0, 0), 1500, col, 0.5, "crystal")
    return c


def beam(a, b, col, radius=0.18, strength=8):
    """A straight bolt of tower light from a to b."""
    import mathutils
    a, b = mathutils.Vector(a), mathutils.Vector(b)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(radius=radius, depth=d.length, location=(a + b) / 2, vertices=12)
    o = bpy.context.object
    o.rotation_mode = "QUATERNION"; o.rotation_quaternion = d.to_track_quat("Z", "Y")
    o.data.materials.append(mat("beam", col, 0.5, emit=col, strength=strength))
    o.visible_shadow = False
    return o
