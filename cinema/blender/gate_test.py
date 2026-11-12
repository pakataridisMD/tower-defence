"""Look test: the army filing through the Black Gate at the bottom of the Rift.

Run: python gate_test.py -- OUT_DIR [--frames a b] [--res 50] [--samples 64] [--gpu] [--no-ph]
CC0 characters from KayKit (Kay Lousberg); canyon, gate, lanterns and light are built here.
"""
import bpy, math, random, sys, os
from mathutils import Vector

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
OUT = argv[0] if argv else "/tmp/gate"
def opt(name, default, n=1):
    if name in argv:
        i = argv.index(name)
        v = argv[i + 1:i + 1 + n]
        return v if n > 1 else v[0]
    return default
F0, F1 = (int(x) for x in opt("--frames", ["1", "1"], 2))
RES = int(opt("--res", "50"))
SAMPLES = int(opt("--samples", "48"))
GPU = "--gpu" in argv
PH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ph")
USE_PH = os.path.isdir(PH) and "--no-ph" not in argv
ASSETS = os.environ.get("KAYKIT", "/home/user/assets3d")
KK = ASSETS + "/kaykit/addons/kaykit_character_pack_adventures/Characters/gltf/"
SK = ASSETS + "/skeletons/addons/kaykit_character_pack_skeletons/Characters/gltf/"
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, 150
sc.render.fps = 30


# ------------------------------------------------------------------ materials
def mat(name, base, rough=0.8, emit=None, strength=0.0, noise=None):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*base, 1)
    b.inputs["Roughness"].default_value = rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = strength
    if noise:  # (scale, dark colour): rock-like colour variation and bump
        tc = nt.nodes.new("ShaderNodeTexCoord")
        n1 = nt.nodes.new("ShaderNodeTexNoise"); n1.inputs["Scale"].default_value = noise[0]
        n1.inputs["Detail"].default_value = 8
        vor = nt.nodes.new("ShaderNodeTexVoronoi"); vor.inputs["Scale"].default_value = noise[0] * 0.6
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].color = (*noise[1], 1)
        ramp.color_ramp.elements[1].color = (*base, 1)
        nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
        nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
        mix = nt.nodes.new("ShaderNodeMath"); mix.operation = "MULTIPLY"
        nt.links.new(n1.outputs["Fac"], mix.inputs[0]); nt.links.new(vor.outputs["Distance"], mix.inputs[1])
        nt.links.new(n1.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump"); bump.inputs["Strength"].default_value = 1.0
        nt.links.new(mix.outputs[0], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def pbr(name, folder, scale, tint=(1, 1, 1), bump=0.6):
    """A Poly Haven texture set (diff, nor_gl, rough, disp) box-projected in object space, so any shape takes it."""
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord"); mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (scale, scale, scale)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    def img(kind, colour):
        t = nt.nodes.new("ShaderNodeTexImage")
        t.image = bpy.data.images.load(os.path.join(PH, folder, "%s_%s_1k.jpg" % (folder, kind)))
        t.image.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        t.projection = "BOX"; t.projection_blend = 0.3
        nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
        return t
    d = img("diff", True)
    tint_n = nt.nodes.new("ShaderNodeMix"); tint_n.data_type = "RGBA"; tint_n.blend_type = "MULTIPLY"
    tint_n.inputs["Factor"].default_value = 1.0; tint_n.inputs["B"].default_value = (*tint, 1)
    nt.links.new(d.outputs["Color"], tint_n.inputs["A"]); nt.links.new(tint_n.outputs["Result"], b.inputs["Base Color"])
    nt.links.new(img("rough", False).outputs["Color"], b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap"); nt.links.new(img("nor_gl", False).outputs["Color"], nm.inputs["Color"])
    bu = nt.nodes.new("ShaderNodeBump"); bu.inputs["Strength"].default_value = bump
    nt.links.new(img("disp", False).outputs["Color"], bu.inputs["Height"]); nt.links.new(nm.outputs["Normal"], bu.inputs["Normal"])
    nt.links.new(bu.outputs["Normal"], b.inputs["Normal"])
    return m


ROCK = mat("rock", (0.16, 0.14, 0.15), 0.9, noise=(0.35, (0.04, 0.035, 0.04)))
GATE = mat("gate", (0.2, 0.19, 0.21), 0.6, noise=(0.5, (0.05, 0.045, 0.055)))
GROUND = mat("ground", (0.11, 0.1, 0.1), 0.95, noise=(0.6, (0.03, 0.028, 0.03)))
GLASS = mat("lantern_glow", (1.0, 0.7, 0.35), 0.4, emit=(1.0, 0.62, 0.25), strength=12)
IRON = mat("iron", (0.05, 0.045, 0.04), 0.5)
if USE_PH:
    ROCK = pbr("rock", "dark_rock_02", 0.08, (0.8, 0.8, 0.85))
    GATE = pbr("gate", "castle_wall_slates", 0.12, (0.55, 0.55, 0.6), 0.8)
    GROUND = pbr("ground", "gray_rocks", 0.25, (0.7, 0.7, 0.72))
VOIDGLOW = mat("gap", (0.0, 0.0, 0.0), 1.0, emit=(0.55, 0.58, 0.66), strength=3.0)


def displaced(obj, strength, scale, subdiv=6):
    m = obj.modifiers.new("sub", "SUBSURF"); m.levels = m.render_levels = subdiv; m.subdivision_type = "SIMPLE"
    tex = bpy.data.textures.new(obj.name + "_n", "CLOUDS"); tex.noise_scale = scale; tex.noise_depth = 5
    d = obj.modifiers.new("disp", "DISPLACE"); d.texture = tex; d.strength = strength; d.texture_coords = "GLOBAL"
    t2 = bpy.data.textures.new(obj.name + "_v", "VORONOI"); t2.noise_scale = scale * 0.35; t2.distance_metric = "DISTANCE"
    d2 = obj.modifiers.new("cracks", "DISPLACE"); d2.texture = t2; d2.strength = strength * 0.35; d2.texture_coords = "GLOBAL"


def box(name, loc, size, m, bevel=0.0):
    bpy.ops.mesh.primitive_cube_add(location=loc)
    o = bpy.context.object; o.name = name; o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    o.data.materials.append(m)
    if bevel:
        b = o.modifiers.new("bev", "BEVEL"); b.width = bevel; b.segments = 3
    return o


# ------------------------------------------------------------------ the Rift and the Gate
# The road runs along -Y towards the gate at y = -120. Camera behind the column, looking down the road.
ground = box("road", (0, -60, -0.5), (240, 200, 1), GROUND)
displaced(ground, 0.6, 3.0, 5)
def scan(folder, loc, rot_z, scale):
    """A linked copy of a Poly Haven scanned rock (one mesh in memory however many copies)."""
    if folder not in _scans:
        before = set(bpy.data.objects)
        bpy.ops.import_scene.gltf(filepath=os.path.join(PH, folder, folder + "_1k.gltf"))
        src = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
        src.hide_render = src.hide_viewport = True
        _scans[folder] = src
    o = _scans[folder].copy(); sc.collection.objects.link(o)
    o.hide_render = o.hide_viewport = False
    o.rotation_mode = "XYZ"; o.location = loc; o.rotation_euler = (0, 0, rot_z); o.scale = (scale,) * 3
    return o
_scans = {}

for side in (-1, 1):
    for k in range(5):
        w = 14 + random.uniform(0, 6)
        inner = 15 + k * k * 6 + random.uniform(0, 2)  # the canyon widens into a hall before the gate
        c = box("cliff", (side * (inner + w / 2), -10 - k * 24, 80), (w, 34, 170 + random.uniform(-10, 30)), ROCK)
        c.rotation_euler.z = random.uniform(-0.15, 0.15)
        displaced(c, 6.0, 9.0, 5)
        if USE_PH:
            c.modifiers["sub"].levels = c.modifiers["sub"].render_levels = 6
if USE_PH:  # scanned boulders and rock shelves at the foot of the walls, and loose rocks along the road
    for k in range(0):  # scanned shelves read as thin shells from the road; left out for now
        side = 1 if k % 2 else -1
        y = 12 - k * 11 + random.uniform(-3, 3)
        x = side * (14 + max(0, -y - 20) * 0.35 + random.uniform(-1, 2))
        scan("namaqualand_cliff_02", (x, y, -1.5), side * math.pi / 2 + random.uniform(-0.4, 0.4), random.uniform(0.9, 1.4))
    for b_ in range(16):
        x = random.choice((-1, 1)) * random.uniform(4.5, 11)
        r_ = scan("rock_face_02", (x, random.uniform(-80, 20), -0.6), random.uniform(0, 6.3), random.uniform(0.5, 1.3))
        r_.data.materials[0] = ROCK
# The gate: two door slabs in a carved frame, open a cart's width.
FRAME_Y = -95
G = 1.9  # gate scale: the door is mountain-tall
for side in (-1, 1):
    box("frame_post", (side * 22 * G, FRAME_Y, 40 * G), (10 * G, 10 * G, 80 * G), GATE, 0.4)
    door = box("door", (side * 9.9 * G, FRAME_Y + 1, 33 * G), (17.8 * G, 3 * G, 66 * G), GATE, 0.3)
    door.rotation_euler.z = side * 0.05
    displaced(door, 0.6, 2.0, 4)
    for r in range(6):  # carved bands on each door
        box("band", (side * 9.9 * G, FRAME_Y + 1 + 1.7 * G, (6 + r * 10.5) * G), (16.5 * G, 0.6 * G, 1.2 * G), IRON, 0.1)
box("lintel", (0, FRAME_Y, 84 * G), (56 * G, 12 * G, 10 * G), GATE, 0.5)
box("gap_light", (0, FRAME_Y - 4, 30 * G), (2.6, 0.5, 60 * G), VOIDGLOW)


# ------------------------------------------------------------------ characters
def import_char(path, loc, rot_z, action, phase, keep=(), scale=1.0):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=path)
    new = [o for o in bpy.data.objects if o not in before]
    rig = next(o for o in new if o.type == "ARMATURE")
    for o in new:
        held = any(w in o.name for w in ("Sword", "Shield", "Axe", "Staff", "Crossbow", "Dagger", "Wand", "Mug", "Spellbook", "Throwable", "Knife"))
        if o.type == "MESH" and held and o.name.split(".")[0] not in keep:
            o.hide_render = o.hide_viewport = True
        if o.type == "MESH" and o.parent is None:
            o.hide_render = o.hide_viewport = True
    rig.rotation_mode = "XYZ"; rig.location = loc; rig.rotation_euler = (0, 0, rot_z); rig.scale = (scale,) * 3
    act = bpy.data.actions.get(action)
    ad = rig.animation_data_create()
    ad.action = None
    # The cycle loops on an NLA strip, offset by `phase` so the column does not march in step.
    a0, a1 = act.frame_range
    length = a1 - a0
    strip = ad.nla_tracks.new().strips.new(action, int(1 - phase * length), act)
    strip.repeat = math.ceil(200 / length) + 1
    return rig, new


def lantern(rig, bone="handslot.r", pole=1.6):
    bpy.ops.mesh.primitive_cylinder_add(radius=0.04, depth=pole, location=(0, 0, 0))
    p = bpy.context.object; p.data.materials.append(IRON)
    p.parent = rig; p.parent_type = "BONE"; p.parent_bone = bone
    p.location = (0, pole / 2 - 0.3, 0); p.rotation_euler.x = math.pi / 2
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.22, location=(0, 0, 0))
    g = bpy.context.object; g.data.materials.append(GLASS)
    g.parent = rig; g.parent_type = "BONE"; g.parent_bone = bone
    g.location = (0, pole - 0.2, 0)
    li = bpy.data.lights.new("lantern", "POINT"); li.energy = 160; li.color = (1.0, 0.62, 0.3); li.shadow_soft_size = 0.25
    lo = bpy.data.objects.new("lantern_light", li); sc.collection.objects.link(lo)
    lo.parent = rig; lo.parent_type = "BONE"; lo.parent_bone = bone; lo.location = (0, pole - 0.2, 0)


# The column: soldiers walking away from camera, down the road, each with a lantern.
column = []
for i in range(34):
    kind = random.choice(["Knight", "Barbarian", "Knight", "Rogue_Hooded"])
    x = random.uniform(-0.6, 0.6) + (1.1 if i % 2 else -1.1)
    y = 6 - i * 3.4 + random.uniform(-1.0, 1.0)
    rig, _ = import_char(KK + kind + ".glb", (x, y, 0), 0.0, "Walking_A", random.random())
    lantern(rig)
    column.append(rig)
# Tamsin (stand-in): in the foreground, turned to the column, lantern-pole raised.
tamsin, _ = import_char(KK + "Knight.glb", (-2.6, 15.0, 0), math.pi - 0.5, "Idle", 0.0, scale=1.05)
lantern(tamsin, pole=2.4)

# Marching motion: the column walks down the road at walking speed.
SPEED = 2.2 / 30
for rig in column:
    # A driver moves each soldier down the road at a steady pace (keeps the NLA walk cycle untouched).
    y0 = rig.location.y
    d = rig.driver_add("location", 1).driver
    d.expression = "%f - %f * frame" % (y0, SPEED)


# ------------------------------------------------------------------ light, air, camera
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]; bg.inputs["Color"].default_value = (0.03, 0.035, 0.06, 1); bg.inputs["Strength"].default_value = 1
if USE_PH:  # an overcast sky, dimmed and cooled to night
    env = world.node_tree.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(PH, "fouriesburg_mountain_cloudy", "fouriesburg_mountain_cloudy_1k.hdr"))
    world.node_tree.links.new(env.outputs["Color"], bg.inputs["Color"]); bg.inputs["Strength"].default_value = 0.05
vol = world.node_tree.nodes.new("ShaderNodeVolumePrincipled")
vol.inputs["Density"].default_value = 0.008; vol.inputs["Color"].default_value = (0.6, 0.62, 0.75, 1); vol.inputs["Anisotropy"].default_value = 0.4
world.node_tree.links.new(vol.outputs[0], world.node_tree.nodes["World Output"].inputs["Volume"])
moon = bpy.data.objects.new("moon", bpy.data.lights.new("moon", "SUN")); sc.collection.objects.link(moon)
moon.data.energy = 4.0; moon.data.color = (0.45, 0.58, 1.0); moon.data.angle = 0.02
moon.rotation_euler = (math.radians(20), math.radians(-25), math.radians(170))
gaplight = bpy.data.objects.new("gaplight", bpy.data.lights.new("gaplight", "AREA")); sc.collection.objects.link(gaplight)
gaplight.data.energy = 60000; gaplight.data.color = (0.7, 0.74, 0.85); gaplight.data.size = 2; gaplight.data.size_y = 50
gaplight.data.shape = "RECTANGLE"; gaplight.location = (0, FRAME_Y - 3, 57); gaplight.rotation_euler = (math.radians(-90), 0, 0)
# A broad cold wash on the gate face so its carving reads, and a beam of grey light out of the gap.
wash = bpy.data.objects.new("wash", bpy.data.lights.new("wash", "AREA")); sc.collection.objects.link(wash)
wash.data.energy = 250000; wash.data.color = (0.55, 0.62, 0.85); wash.data.size = 60
wash.location = (25, FRAME_Y + 70, 150); wash.rotation_euler = (math.radians(-45), 0, math.radians(-10))
beam = bpy.data.objects.new("beam", bpy.data.lights.new("beam", "SPOT")); sc.collection.objects.link(beam)
beam.data.energy = 1.2e7; beam.data.color = (0.75, 0.78, 0.88); beam.data.spot_size = math.radians(12); beam.data.shadow_soft_size = 1
beam.location = (0, FRAME_Y - 20, 25); beam.rotation_euler = (math.radians(-95), 0, 0)
rim = bpy.data.objects.new("rim", bpy.data.lights.new("rim", "AREA")); sc.collection.objects.link(rim)
rim.data.energy = 1400; rim.data.color = (0.6, 0.7, 1.0); rim.data.size = 6
rim.location = (5, 1, 6); rim.rotation_euler = (math.radians(-60), math.radians(-30), 0)

fill = bpy.data.objects.new("fill", bpy.data.lights.new("fill", "AREA")); sc.collection.objects.link(fill)
fill.data.energy = 120; fill.data.color = (1.0, 0.7, 0.45); fill.data.size = 3
fill.location = (2.0, 16.0, 3.0); fill.rotation_euler = (math.radians(70), 0, math.radians(200))
cam = bpy.data.objects.new("cam", bpy.data.cameras.new("cam")); sc.collection.objects.link(cam); sc.camera = cam
cam.data.lens = 24; cam.data.sensor_width = 36
cam.data.dof.use_dof = True; cam.data.dof.aperture_fstop = 4.0; cam.data.dof.focus_object = tamsin
for f, loc, rot in [(1, (3.0, 30.0, 16.0), (88, 0, 176)), (150, (2.5, 24.0, 13.0), (90, 0, 177))]:
    cam.location = loc; cam.rotation_euler = tuple(math.radians(a) for a in rot)
    cam.keyframe_insert("location", frame=f); cam.keyframe_insert("rotation_euler", frame=f)

r = sc.render
r.engine = "CYCLES"; sc.cycles.device = "CPU"
if GPU:
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
sc.cycles.samples = SAMPLES; sc.cycles.use_denoising = True
sc.cycles.volume_step_rate = 4; sc.cycles.max_bounces = 4
r.resolution_x, r.resolution_y, r.resolution_percentage = 1920, 1080, RES
r.use_motion_blur = True; r.motion_blur_shutter = 0.4
sc.view_settings.view_transform = "AgX"; sc.view_settings.look = "AgX - Medium High Contrast"; sc.view_settings.exposure = 1.0
r.image_settings.file_format = "PNG"
os.makedirs(OUT, exist_ok=True)
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    r.filepath = os.path.join(OUT, "f%04d.png" % f)
    bpy.ops.render.render(write_still=True)
