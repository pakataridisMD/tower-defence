"""Creature kit: organic bodies from a skinned skeleton, hard parts from bevelled primitives, one camera and light rig."""
import math
import bpy
import bmesh
import numpy as np
from mathutils import Vector, Euler


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    return bpy.context.scene


def setup(scene, size=384, samples=48, ortho=3.2, elev=22.0, azim=-62.0, center=(0, 0, 0.9)):
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = False
    scene.cycles.device = "CPU"
    scene.render.resolution_x = scene.render.resolution_y = size
    scene.render.film_transparent = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.view_settings.view_transform = "Standard"
    cam_d = bpy.data.cameras.new("cam")
    cam_d.type = "ORTHO"
    cam_d.ortho_scale = ortho
    cam = bpy.data.objects.new("cam", cam_d)
    scene.collection.objects.link(cam)
    e, a = math.radians(elev), math.radians(azim)
    c = Vector(center)
    d = Vector((math.cos(e) * math.cos(a), math.cos(e) * math.sin(a), math.sin(e)))
    cam.location = c + d * 20
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    # key from upper left (screen), warm; cool fill; rim from behind right
    def sun(name, rot, energy, col):
        l = bpy.data.lights.new(name, "SUN")
        l.energy = energy
        l.color = col
        l.angle = math.radians(8)
        o = bpy.data.objects.new(name, l)
        o.rotation_euler = Euler([math.radians(v) for v in rot])
        scene.collection.objects.link(o)
    sun("key", (48, 0, -150), 4.2, (1.0, 0.94, 0.84))
    sun("fill", (70, 0, 20), 0.9, (0.6, 0.7, 1.0))
    sun("rim", (115, 0, 60), 1.4, (0.85, 0.88, 1.0))
    w = bpy.data.worlds.new("w")
    w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.3, 0.28, 0.3, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    scene.world = w
    return cam


_mats = {}


def mat(name, color, rough=0.75, metal=0.0, emit=0.0, noise=0.0, noise_scale=8.0):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    c = tuple(pow(int(color[i:i + 2], 16) / 255, 2.2) for i in (0, 2, 4)) + (1,)
    b.inputs["Base Color"].default_value = c
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emit:
        b.inputs["Emission Color"].default_value = c
        b.inputs["Emission Strength"].default_value = emit
    if noise:
        n = nt.nodes.new("ShaderNodeTexNoise")
        n.inputs["Scale"].default_value = noise_scale
        n.inputs["Detail"].default_value = 6
        mix = nt.nodes.new("ShaderNodeMixRGB")
        mix.blend_type = "MULTIPLY"
        mix.inputs[0].default_value = noise
        mix.inputs[1].default_value = c
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.35
        ramp.color_ramp.elements[1].position = 0.7
        nt.links.new(n.outputs["Fac"], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], mix.inputs[2])
        nt.links.new(mix.outputs[0], b.inputs["Base Color"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = noise * 0.6
        nt.links.new(n.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs[0], b.inputs["Normal"])
    _mats[name] = m
    return m


def _finish(obj, material, smooth=True):
    bpy.context.scene.collection.objects.link(obj) if obj.name not in bpy.context.scene.collection.objects else None
    obj.data.materials.append(material)
    if smooth:
        for p in obj.data.polygons:
            p.use_smooth = True
    return obj


def skin(name, pts, edges, material, sub=2):
    """Organic body: pts = [(x,y,z,radius) or (x,y,z,rx,ry)], edges = [(i,j)]; skin + subdivision."""
    me = bpy.data.meshes.new(name)
    me.from_pydata([p[:3] for p in pts], edges, [])
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    mod = obj.modifiers.new("skin", "SKIN")
    mod.use_smooth_shade = True
    for i, p in enumerate(pts):
        v = me.skin_vertices[0].data[i]
        v.radius = (p[3], p[4] if len(p) > 4 else p[3])
    me.skin_vertices[0].data[0].use_root = True
    s = obj.modifiers.new("sub", "SUBSURF")
    s.levels = s.render_levels = sub
    obj.data.materials.append(material)
    return obj


def prim(kind, name, material, loc=(0, 0, 0), scale=(1, 1, 1), rot=(0, 0, 0), bevel=0.0, sub=0, smooth=True, **kw):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    if kind == "cube":
        bmesh.ops.create_cube(bm, size=1.0)
    elif kind == "sphere":
        bmesh.ops.create_uvsphere(bm, u_segments=kw.get("seg", 20), v_segments=kw.get("rings", 12), radius=0.5)
    elif kind == "ico":
        bmesh.ops.create_icosphere(bm, subdivisions=kw.get("subdiv", 1), radius=0.5)
    elif kind == "cyl":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get("seg", 16), radius1=0.5, radius2=0.5 * kw.get("taper", 1.0),
                              depth=1.0)
    elif kind == "cone":
        bmesh.ops.create_cone(bm, cap_ends=True, segments=kw.get("seg", 12), radius1=0.5, radius2=0.0, depth=1.0)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    obj.location = loc
    obj.scale = scale
    obj.rotation_euler = Euler([math.radians(v) for v in rot])
    if bevel:
        b = obj.modifiers.new("bev", "BEVEL")
        b.width = bevel
        b.segments = 2
    if sub:
        s = obj.modifiers.new("sub", "SUBSURF")
        s.levels = s.render_levels = sub
    obj.data.materials.append(material)
    if smooth and kind in ("sphere", "ico", "cyl", "cone"):
        for p in me.polygons:
            p.use_smooth = True
    return obj


def displace(obj, strength=0.05, scale=0.5, kind="CLOUDS"):
    t = bpy.data.textures.new(obj.name + "_t", kind)
    t.noise_scale = scale
    d = obj.modifiers.new("disp", "DISPLACE")
    d.texture = t
    d.strength = strength
    return obj


def render(scene, path):
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
