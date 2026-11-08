"""Shared building blocks for the tower sprite pipeline.

Everything here is plain bpy so it runs both inside Blender (`blender -b -P render_tower.py -- ...`)
and with the `bpy` module from PyPI (`python render_tower.py ...`).

Conventions
-----------
* One board cell is 1.0 Blender unit. A tower stands on the origin, facing +X by default.
* The camera is orthographic and fixed. Towers turn by rotating their `head` pivot around Z,
  so every direction is lit and shadowed the same way.
* Directions are *screen* angles in Godot's convention: 0 is right, angles grow clockwise on
  screen (Godot's y axis points down). `world_yaw_for_screen_angle` converts them so the
  spout really points at the enemy on screen, even though the camera looks down at an angle.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import bpy
import bmesh
from mathutils import Vector


#: Set by the renderer for the pixel-art style: calmer textures, because fine noise turns into
#: speckle once the render is shrunk to a few pixels per detail.
FLAT = False


def _calm(dark, light, amount: float):
    """Pull two ramp colours towards each other when FLAT is on."""
    if not FLAT:
        return dark, light
    mid = [(a + b) / 2 for a, b in zip(dark, light)]
    return (tuple(a + (m - a) * amount for a, m in zip(dark, mid)),
            tuple(b + (m - b) * amount for b, m in zip(light, mid)))


# --- Camera and render settings ------------------------------------------------------------

#: Degrees the camera looks down from the horizon. 90 would be straight top-down.
CAMERA_ELEVATION = 50.0
#: Degrees the camera is turned around the tower. -90 looks from -Y (the "south" side).
CAMERA_AZIMUTH = -90.0
#: Width of the frame in board cells.
FRAME_CELLS = 2.0
#: How far below the frame centre the cell centre sits, as a fraction of the frame.
ANCHOR_DROP = 0.15


@dataclass
class RenderSettings:
    size: int = 256
    samples: int = 64
    #: Sprites are rendered at 2x so they stay sharp on 4K screens; Godot draws them at half size.
    display_scale: float = 0.5


@dataclass
class TowerRig:
    """What a tower module hands back to the renderer."""

    id: str
    head: bpy.types.Object
    #: Called with a loop phase in [0, 1) before each frame is rendered.
    animate: Callable[[float], None]
    frames: int = 8
    fps: float = 10.0
    extra: dict = field(default_factory=dict)


def reset_scene() -> bpy.types.Scene:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    return scene


def setup_render(scene: bpy.types.Scene, settings: RenderSettings) -> None:
    scene.render.engine = "CYCLES"
    cycles = scene.cycles
    cycles.device = "CPU"
    cycles.samples = settings.samples
    cycles.use_adaptive_sampling = True
    cycles.adaptive_threshold = 0.02
    cycles.use_denoising = True
    cycles.denoiser = "OPENIMAGEDENOISE"
    cycles.max_bounces = 6
    cycles.transparent_max_bounces = 8
    cycles.caustics_reflective = False
    cycles.caustics_refractive = False
    cycles.blur_glossy = 1.0
    scene.render.film_transparent = True
    scene.render.filter_size = 1.2
    scene.render.resolution_x = settings.size
    scene.render.resolution_y = settings.size
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.color_depth = "8"
    # Standard keeps fire and glow colours saturated. AgX looks more filmic but turns hot
    # oranges pink and pale, which reads badly at sprite size.
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.view_settings.exposure = 0.0


def setup_camera(scene: bpy.types.Scene) -> bpy.types.Object:
    data = bpy.data.cameras.new("SpriteCamera")
    data.type = "ORTHO"
    data.ortho_scale = FRAME_CELLS
    # Positive shift moves the view up, so the tower's foot lands below the frame centre.
    data.shift_y = ANCHOR_DROP
    data.clip_start = 0.1
    data.clip_end = 100.0
    cam = bpy.data.objects.new("SpriteCamera", data)
    scene.collection.objects.link(cam)
    elevation = math.radians(CAMERA_ELEVATION)
    azimuth = math.radians(CAMERA_AZIMUTH)
    distance = 20.0
    cam.location = Vector((
        distance * math.cos(elevation) * math.cos(azimuth),
        distance * math.cos(elevation) * math.sin(azimuth),
        distance * math.sin(elevation),
    ))
    direction = Vector((0.0, 0.0, 0.0)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    return cam


def anchor_pixel(settings: RenderSettings) -> tuple[float, float]:
    """Pixel (from the top-left) where the ground point under the tower appears."""
    half = settings.size / 2.0
    return half, half + ANCHOR_DROP * settings.size


def world_yaw_for_screen_angle(screen_angle: float) -> float:
    """World yaw around Z that appears at `screen_angle` (Godot convention) from this camera.

    The ground is seen foreshortened by sin(elevation) along the camera's depth axis, so equal
    screen steps are not equal world steps.
    """
    squash = math.sin(math.radians(CAMERA_ELEVATION))
    screen_x = math.cos(screen_angle)
    screen_down = math.sin(screen_angle)
    # Screen right is world +X and screen down is world -Y when the camera sits on the -Y side.
    world_x = screen_x
    world_y = -screen_down / squash
    yaw = math.atan2(world_y, world_x)
    # Account for the camera azimuth (the default -90 needs no turn).
    return yaw + math.radians(CAMERA_AZIMUTH + 90.0)


def setup_lighting(scene: bpy.types.Scene, warm: tuple[float, float, float] = (1.0, 0.93, 0.85)) -> None:
    world = bpy.data.worlds.new("SpriteWorld")
    scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    background = nodes.get("Background")
    # A dim blue sky fills shadows so dark materials keep their shape against the dark board.
    background.inputs["Color"].default_value = (0.20, 0.26, 0.38, 1.0)
    background.inputs["Strength"].default_value = 0.55

    def add_light(name: str, kind: str, energy: float, color, rotation_deg, location=(0, 0, 10), **extra):
        light = bpy.data.lights.new(name, kind)
        light.energy = energy
        light.color = color
        for key, value in extra.items():
            setattr(light, key, value)
        obj = bpy.data.objects.new(name, light)
        obj.location = location
        obj.rotation_euler = [math.radians(a) for a in rotation_deg]
        scene.collection.objects.link(obj)
        return obj

    # Key light from the upper left of the screen, matching the game's UI shading.
    # Sun lamps shine along their local -Z axis. The key comes from the upper left of the screen,
    # so shadows fall down and to the right, the way the game's UI is shaded.
    add_light("Key", "SUN", 3.6 if FLAT else 3.0, warm, (-28, 0, 45), angle=math.radians(4))
    # Cool rim from behind the tower to separate its silhouette from the dark board.
    add_light("Rim", "SUN", 2.4, (0.6, 0.75, 1.0), (-72, 0, -35), angle=math.radians(8))


def add_shadow_catcher(scene: bpy.types.Scene, size: float = FRAME_CELLS * 2) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, 0))
    plane = bpy.context.active_object
    plane.name = "ShadowCatcher"
    plane.is_shadow_catcher = True
    return plane


def normal_override_material() -> bpy.types.Material:
    """Emits each surface's camera-space normal as a colour, for normal-map sheets.

    Camera space has X right, Y up and Z towards the viewer, which is the OpenGL convention Godot
    uses for 2D normal maps, so the colour can be used as-is.
    """
    mat = bpy.data.materials.new("NormalPass")
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out = nodes.new("ShaderNodeOutputMaterial")
    geometry = nodes.new("ShaderNodeNewGeometry")
    to_camera = nodes.new("ShaderNodeVectorTransform")
    to_camera.vector_type = "NORMAL"
    to_camera.convert_from = "WORLD"
    to_camera.convert_to = "CAMERA"
    links.new(geometry.outputs["Normal"], to_camera.inputs["Vector"])
    # Cycles' camera space points +Z into the scene, so flip Z to make "towards the viewer" positive.
    half = nodes.new("ShaderNodeVectorMath")
    half.operation = "MULTIPLY_ADD"
    half.inputs[1].default_value = (0.5, 0.5, -0.5)
    half.inputs[2].default_value = (0.5, 0.5, 0.5)
    links.new(to_camera.outputs["Vector"], half.inputs[0])
    emission = nodes.new("ShaderNodeEmission")
    links.new(half.outputs["Vector"], emission.inputs["Color"])
    links.new(emission.outputs[0], out.inputs["Surface"])
    return mat


class NormalPass:
    """Context manager that switches the scene to a raw, single-sample normal render."""

    def __init__(self, scene: bpy.types.Scene, material: bpy.types.Material):
        self.scene = scene
        self.material = material

    def __enter__(self):
        scene = self.scene
        self.saved = (scene.cycles.samples, scene.cycles.use_denoising, scene.view_settings.view_transform,
                      scene.view_settings.look)
        scene.cycles.samples = 4
        scene.cycles.use_denoising = False
        scene.view_settings.view_transform = "Raw"
        scene.view_layers[0].material_override = self.material
        self.hidden = []
        for obj in scene.objects:
            if obj.type == "MESH" and (obj.is_shadow_catcher or not obj.visible_shadow):
                # The shadow catcher would render as a solid floor, and flames and sparks have no
                # surface worth lighting.
                if not obj.hide_render:
                    obj.hide_render = True
                    self.hidden.append(obj)
        return self

    def __exit__(self, *exc):
        scene = self.scene
        scene.cycles.samples, scene.cycles.use_denoising = self.saved[0], self.saved[1]
        scene.view_settings.view_transform = self.saved[2]
        scene.view_settings.look = self.saved[3]
        scene.view_layers[0].material_override = None
        for obj in self.hidden:
            obj.hide_render = False
        return False


# --- Materials ---------------------------------------------------------------------------

def _principled(mat: bpy.types.Material) -> bpy.types.Node:
    mat.use_nodes = True
    return mat.node_tree.nodes.get("Principled BSDF")


def _link(mat, out_socket, in_socket):
    mat.node_tree.links.new(out_socket, in_socket)


def stone_material(name: str, dark, light, scale: float = 9.0, roughness: float = 0.82) -> bpy.types.Material:
    """Mottled stone: two-tone noise for colour, a finer noise for bumps, darker crevices."""
    mat = bpy.data.materials.new(name)
    bsdf = _principled(mat)
    nodes = mat.node_tree.nodes
    dark, light = _calm(dark, light, 0.6)
    if FLAT:
        scale *= 0.45
    coords = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = scale
    noise.inputs["Detail"].default_value = 6.0
    noise.inputs["Roughness"].default_value = 0.62
    _link(mat, coords.outputs["Object"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (*dark, 1.0)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (*light, 1.0)
    _link(mat, noise.outputs["Fac"], ramp.inputs["Fac"])
    # Ambient occlusion darkens the seams between blocks, which reads well at sprite sizes.
    ao = nodes.new("ShaderNodeAmbientOcclusion")
    ao.inputs["Distance"].default_value = 0.08
    _link(mat, ramp.outputs["Color"], ao.inputs["Color"])
    mix = nodes.new("ShaderNodeMix")
    mix.data_type = "RGBA"
    mix.blend_type = "MULTIPLY"
    mix.inputs["Factor"].default_value = 0.65
    _link(mat, ao.outputs["Color"], mix.inputs["A"])
    _link(mat, ao.outputs["AO"], mix.inputs["B"])
    _link(mat, mix.outputs["Result"], bsdf.inputs["Base Color"])
    bump_noise = nodes.new("ShaderNodeTexNoise")
    bump_noise.inputs["Scale"].default_value = scale * 4.0
    bump_noise.inputs["Detail"].default_value = 8.0
    _link(mat, coords.outputs["Object"], bump_noise.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.08 if FLAT else 0.35
    bump.inputs["Distance"].default_value = 0.02
    _link(mat, bump_noise.outputs["Fac"], bump.inputs["Height"])
    _link(mat, bump.outputs["Normal"], bsdf.inputs["Normal"])
    bsdf.inputs["Roughness"].default_value = roughness
    return mat


def metal_material(name: str, color, roughness: float = 0.32, wear: float = 0.25) -> bpy.types.Material:
    """Worn metal: edges catch light (via pointiness-free curvature fake) and a little grime."""
    mat = bpy.data.materials.new(name)
    bsdf = _principled(mat)
    nodes = mat.node_tree.nodes
    bsdf.inputs["Metallic"].default_value = 1.0
    coords = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 14.0
    noise.inputs["Detail"].default_value = 4.0
    _link(mat, coords.outputs["Object"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.45
    worn, clean = _calm((color[0] * 0.55, color[1] * 0.5, color[2] * 0.45), color, 0.7)
    ramp.color_ramp.elements[0].color = (*worn, 1.0)
    ramp.color_ramp.elements[1].position = 0.75
    ramp.color_ramp.elements[1].color = (*clean, 1.0)
    _link(mat, noise.outputs["Fac"], ramp.inputs["Fac"])
    _link(mat, ramp.outputs["Color"], bsdf.inputs["Base Color"])
    rough = nodes.new("ShaderNodeMapRange")
    rough.inputs["To Min"].default_value = roughness
    rough.inputs["To Max"].default_value = min(1.0, roughness + wear)
    _link(mat, noise.outputs["Fac"], rough.inputs["Value"])
    _link(mat, rough.outputs["Result"], bsdf.inputs["Roughness"])
    return mat


def gloss_material(name: str, color, roughness: float = 0.18) -> bpy.types.Material:
    """Glassy dark stone such as obsidian."""
    mat = bpy.data.materials.new(name)
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Specular IOR Level"].default_value = 0.5
    bsdf.inputs["Coat Weight"].default_value = 0.25
    bsdf.inputs["Coat Roughness"].default_value = 0.08
    return mat


def emission_material(name: str, color, strength: float) -> bpy.types.Material:
    mat = bpy.data.materials.new(name)
    bsdf = _principled(mat)
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Color"].default_value = (*color, 1.0)
    bsdf.inputs["Emission Strength"].default_value = strength
    return mat


def set_emission(mat: bpy.types.Material, strength: float) -> None:
    mat.node_tree.nodes.get("Principled BSDF").inputs["Emission Strength"].default_value = strength


def flame_material(name: str, phase_holder: dict) -> bpy.types.Material:
    """Emissive flame: hot core at the bottom fading to deep red tips, with moving noise.

    The noise is sampled from a position offset along a circle by the loop phase, so the
    animation loops seamlessly. `phase_holder["mapping"]` is the Mapping node to animate.
    """
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    for node in list(nodes):
        nodes.remove(node)
    out = nodes.new("ShaderNodeOutputMaterial")
    coords = nodes.new("ShaderNodeTexCoord")
    mapping = nodes.new("ShaderNodeMapping")
    links.new(coords.outputs["Object"], mapping.inputs["Vector"])
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 4.5
    noise.inputs["Detail"].default_value = 5.0
    noise.inputs["Roughness"].default_value = 0.55
    links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
    # Height in object space: 0 at the bottom of the flame mesh, ~1 at the tip.
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(coords.outputs["Object"], sep.inputs["Vector"])
    height = nodes.new("ShaderNodeMapRange")
    height.inputs["From Min"].default_value = -1.0
    height.inputs["From Max"].default_value = 1.0
    links.new(sep.outputs["Z"], height.inputs["Value"])
    heat = nodes.new("ShaderNodeMath")
    heat.operation = "SUBTRACT"
    links.new(height.outputs["Result"], heat.inputs[0])
    scaled_noise = nodes.new("ShaderNodeMath")
    scaled_noise.operation = "MULTIPLY"
    scaled_noise.inputs[1].default_value = 0.55
    links.new(noise.outputs["Fac"], scaled_noise.inputs[0])
    links.new(scaled_noise.outputs[0], heat.inputs[1])
    ramp = nodes.new("ShaderNodeValToRGB")
    elements = ramp.color_ramp.elements
    elements[0].position = 0.0
    elements[0].color = (1.0, 0.78, 0.28, 1.0)
    elements[1].position = 0.75
    elements[1].color = (0.55, 0.04, 0.0, 1.0)
    mid = elements.new(0.3)
    mid.color = (1.0, 0.32, 0.02, 1.0)
    links.new(heat.outputs[0], ramp.inputs["Fac"])
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.3 if FLAT else 1.9
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    # Transparency: tips and noise gaps fade out, giving a ragged flame silhouette.
    alpha = nodes.new("ShaderNodeMapRange")
    alpha.inputs["From Min"].default_value = 0.55
    alpha.inputs["From Max"].default_value = 0.25
    links.new(heat.outputs[0], alpha.inputs["Value"])
    transparent = nodes.new("ShaderNodeBsdfTransparent")
    mix = nodes.new("ShaderNodeMixShader")
    links.new(alpha.outputs["Result"], mix.inputs["Fac"])
    links.new(transparent.outputs[0], mix.inputs[1])
    links.new(emission.outputs[0], mix.inputs[2])
    links.new(mix.outputs[0], out.inputs["Surface"])
    phase_holder["mapping"] = mapping
    return mat


# --- Mesh helpers ------------------------------------------------------------------------

def assign(obj: bpy.types.Object, mat: bpy.types.Material) -> bpy.types.Object:
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    return obj


def shade_smooth(obj: bpy.types.Object, auto_angle: float = 35.0) -> None:
    obj.data.polygons.foreach_set("use_smooth", [True] * len(obj.data.polygons))
    obj.data.update()
    try:
        with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj]):
            bpy.ops.object.shade_auto_smooth(angle=math.radians(auto_angle))
    except (RuntimeError, AttributeError, TypeError):
        pass


def bevel(obj: bpy.types.Object, width: float = 0.012, segments: int = 2) -> bpy.types.Object:
    mod = obj.modifiers.new("Bevel", "BEVEL")
    mod.width = width
    mod.segments = segments
    mod.limit_method = "ANGLE"
    mod.harden_normals = False
    return obj


def cylinder(name: str, radius: float, depth: float, z: float, vertices: int = 32,
             rotation_z: float = 0.0, radius_top: float | None = None) -> bpy.types.Object:
    """Upright cylinder (or cone frustum) whose bottom sits at height `z`."""
    if radius_top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=depth,
                                            location=(0, 0, z + depth / 2))
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices, radius1=radius, radius2=radius_top,
                                        depth=depth, location=(0, 0, z + depth / 2))
    obj = bpy.context.active_object
    obj.name = name
    obj.rotation_euler.z = rotation_z
    return obj


def torus(name: str, major: float, minor: float, z: float, segments: int = 48) -> bpy.types.Object:
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor, major_segments=segments,
                                     minor_segments=12, location=(0, 0, z))
    obj = bpy.context.active_object
    obj.name = name
    return obj


def bowl(name: str, radius: float, depth: float, thickness: float, z: float, segments: int = 40) -> bpy.types.Object:
    """Open half-sphere bowl, rim at height `z + depth`."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = 10
    verts = []
    for ring in range(rings + 1):
        t = ring / rings
        angle = t * math.pi / 2
        r = radius * math.sin(angle)
        h = depth * (1 - math.cos(angle))
        row = []
        for seg in range(segments):
            a = seg / segments * math.tau
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z + h)))
        verts.append(row)
    for ring in range(rings):
        for seg in range(segments):
            nxt = (seg + 1) % segments
            bm.faces.new((verts[ring][seg], verts[ring][nxt], verts[ring + 1][nxt], verts[ring + 1][seg]))
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    solid = obj.modifiers.new("Solidify", "SOLIDIFY")
    solid.thickness = thickness
    solid.offset = 1.0
    shade_smooth(obj, 60)
    return obj


def tube(name: str, points: list[Vector], radii: list[float], sides: int = 8) -> bpy.types.Object:
    """A tube swept along `points` with a radius per point, closed at both ends. Good for horns,
    claws, roots and pipes. Rings are oriented along the path so bends stay round."""
    mesh = bpy.data.meshes.new(name)
    bm = bmesh.new()
    rings = []
    for i, (point, radius) in enumerate(zip(points, radii)):
        ahead = points[min(i + 1, len(points) - 1)] - points[max(i - 1, 0)]
        ahead.normalize()
        side = ahead.cross(Vector((0, 0, 1)) if abs(ahead.z) < 0.99 else Vector((1, 0, 0)))
        side.normalize()
        up = side.cross(ahead)
        ring = []
        for k in range(sides):
            a = k / sides * math.tau
            ring.append(bm.verts.new(point + (side * math.cos(a) + up * math.sin(a)) * radius))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for k in range(sides):
            n = (k + 1) % sides
            bm.faces.new((a[k], a[n], b[n], b[k]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(mesh)
    bm.free()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    shade_smooth(obj, 70)
    return obj


def bezier(p0: Vector, p1: Vector, p2: Vector, steps: int) -> list[Vector]:
    """Points along a quadratic Bezier curve, both ends included."""
    out = []
    for i in range(steps + 1):
        t = i / steps
        out.append(p0 * (1 - t) ** 2 + p1 * 2 * (1 - t) * t + p2 * t * t)
    return out


def parent(child: bpy.types.Object, parent_obj: bpy.types.Object) -> None:
    """Parent keeping the child's current world transform."""
    bpy.context.view_layer.update()
    world = child.matrix_world.copy()
    child.parent = parent_obj
    child.matrix_world = world
