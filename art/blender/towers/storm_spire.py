"""Storm tower "Spire": a hexagonal slate plinth with a copper-coiled pillar, crowned by a floating
storm crystal. The head is a copper fork that turns to point at its target, with sparks arcing
between its prongs.

The loop bobs and spins the crystal, orbits three shards around it, pulses the glow and flickers
the arcs.
"""

from __future__ import annotations

import math
import random

import bpy
from mathutils import Vector

import kit

ID = "storm_spire"

SLATE_DARK = (0.025, 0.03, 0.045)
SLATE_LIGHT = (0.13, 0.15, 0.2)
STONE_DARK = (0.04, 0.045, 0.06)
STONE_LIGHT = (0.2, 0.22, 0.27)
COPPER = (0.95, 0.5, 0.3)
DARK_COPPER = (0.4, 0.2, 0.12)
STORM = (0.12, 0.45, 1.0)
SPARK = (0.75, 0.9, 1.0)

SHARDS = 3
HEAD_ORIGIN = (0.0, 0.0, 0.63)


def _arc_points(start: Vector, end: Vector, rng: random.Random, kinks: int = 6, jitter: float = 0.03) -> list[Vector]:
    points = [start]
    for k in range(1, kinks):
        t = k / kinks
        offset = Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * jitter
        points.append(start.lerp(end, t) + offset)
    points.append(end)
    return points


def build(scene: bpy.types.Scene) -> kit.TowerRig:
    slate = kit.stone_material("Slate", SLATE_DARK, SLATE_LIGHT, scale=7.0)
    stone = kit.stone_material("Stone", STONE_DARK, STONE_LIGHT, scale=11.0, roughness=0.7)
    copper = kit.metal_material("Copper", COPPER, roughness=0.26)
    dark_copper = kit.metal_material("DarkCopper", DARK_COPPER, roughness=0.45, wear=0.3)
    seam_glow = kit.emission_material("SeamGlow", STORM, 1.2)
    crystal_glow = kit.emission_material("Crystal", STORM, 1.5)
    crystal_bsdf = crystal_glow.node_tree.nodes.get("Principled BSDF")
    crystal_bsdf.inputs["Roughness"].default_value = 0.08
    crystal_bsdf.inputs["Coat Weight"].default_value = 1.0
    spark_glow = kit.emission_material("Spark", SPARK, 4.0)

    # --- Base (static), same footprint as the other towers so the set lines up ------------------
    plinth = kit.assign(kit.cylinder("Plinth", 0.43, 0.11, 0.0, vertices=6, radius_top=0.40), slate)
    kit.bevel(plinth, 0.014, 3)
    kit.assign(kit.cylinder("Seam", 0.275, 0.03, 0.1, vertices=6, rotation_z=math.radians(30)), seam_glow)
    for i in range(6):
        angle = math.radians(60 * i)
        block = kit.assign(kit.cylinder(f"Corner{i}", 0.05, 0.16, 0.0, vertices=4, radius_top=0.035), slate)
        block.location.x = 0.38 * math.cos(angle)
        block.location.y = 0.38 * math.sin(angle)
        block.rotation_euler.z = angle + math.radians(45)
        kit.bevel(block, 0.008, 2)
    pillar = kit.assign(kit.cylinder("Pillar", 0.25, 0.5, 0.13, vertices=6, rotation_z=math.radians(30),
                                     radius_top=0.14), stone)
    kit.bevel(pillar, 0.012, 3)
    # Copper coils wind up the pillar, narrowing with it.
    for i, z in enumerate((0.24, 0.36, 0.48)):
        t = (z - 0.13) / 0.5
        radius = 0.25 + (0.14 - 0.25) * t
        coil = kit.assign(kit.torus(f"Coil{i}", radius * 0.95, 0.022, z, segments=32), copper)
        coil.scale.z = 1.3
    # Three copper conductor rods lean against the pillar, ending in glowing studs.
    for i, degrees in enumerate((90, 210, 330)):
        angle = math.radians(degrees)
        out = Vector((math.cos(angle), math.sin(angle), 0.0))
        path = kit.bezier(out * 0.33 + Vector((0, 0, 0.1)), out * 0.3 + Vector((0, 0, 0.42)),
                          out * 0.17 + Vector((0, 0, 0.62)), 10)
        kit.assign(kit.tube(f"Rod{i}", path, [0.022] * len(path), sides=8), dark_copper)
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.03, location=path[-1], segments=16, ring_count=8)
        stud = bpy.context.active_object
        kit.assign(stud, crystal_glow)
        kit.shade_smooth(stud, 80)

    # --- Head (turns to aim) -------------------------------------------------------------
    head = bpy.data.objects.new("Head", None)
    head.location = HEAD_ORIGIN
    scene.collection.objects.link(head)
    cap = kit.assign(kit.cylinder("Cap", 0.13, 0.05, 0.62, vertices=24, radius_top=0.11), dark_copper)
    kit.bevel(cap, 0.008, 2)
    ring = kit.assign(kit.torus("CapRing", 0.12, 0.016, 0.66, segments=32), copper)
    # The fork: two prongs reaching forward (+X) and up, sparks jump between their tips.
    prong_tips = []
    prongs = []
    for side in (-1, 1):
        path = kit.bezier(Vector((0.02, side * 0.07, 0.66)), Vector((0.26, side * 0.15, 0.64)),
                          Vector((0.36, side * 0.06, 0.78)), 12)
        radii = [0.03 * (1.0 - t / 12) ** 0.6 + 0.006 for t in range(13)]
        prongs.append(kit.assign(kit.tube(f"Prong{side}", path, radii, sides=8), copper))
        prong_tips.append(path[-1] - Vector(HEAD_ORIGIN))

    # The storm crystal floats above the cap: an elongated octahedron with an inner glow.
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.11, radius2=0.0, depth=0.28, location=(0, 0, 1.02))
    crystal_top = bpy.context.active_object
    bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.11, radius2=0.0, depth=0.14, location=(0, 0, 0.81))
    crystal_bottom = bpy.context.active_object
    crystal_bottom.rotation_euler.x = math.pi
    for piece in (crystal_top, crystal_bottom):
        kit.assign(piece, crystal_glow)
    crystal = bpy.data.objects.new("Crystal", None)
    crystal.location = (0, 0, 0.88)
    scene.collection.objects.link(crystal)
    kit.parent(crystal_top, crystal)
    kit.parent(crystal_bottom, crystal)

    light_data = bpy.data.lights.new("StormLight", "POINT")
    light_data.color = STORM
    light_data.shadow_soft_size = 0.05
    storm_light = bpy.data.objects.new("StormLight", light_data)
    storm_light.location = (0, 0, 0.9)
    scene.collection.objects.link(storm_light)

    shards = []
    for i in range(SHARDS):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.025, radius2=0.0, depth=0.07, location=(0, 0, 0.86))
        shard = bpy.context.active_object
        shard.name = f"Shard{i}"
        kit.assign(shard, crystal_glow)
        shards.append(shard)

    arcs: list[bpy.types.Object] = []

    for part in (cap, ring, *prongs, crystal, storm_light, *shards):
        kit.parent(part, head)

    def make_arcs(phase: float) -> None:
        for arc in arcs:
            bpy.data.objects.remove(arc, do_unlink=True)
        arcs.clear()
        frame_seed = int(round(phase * 1000))
        rng = random.Random(frame_seed)
        # One arc between the prong tips, and one or two from the crystal down to a prong.
        pairs = [(prong_tips[0], prong_tips[1])]
        crystal_low = Vector((0.0, 0.0, 0.74 - HEAD_ORIGIN[2] + 0.025 * math.sin(phase * math.tau)))
        pairs.append((crystal_low, prong_tips[rng.randrange(2)]))
        if rng.random() < 0.5:
            pairs.append((crystal_low, prong_tips[rng.randrange(2)]))
        for k, (a, b) in enumerate(pairs):
            points = _arc_points(a, b, rng)
            arc = kit.assign(kit.tube(f"Arc{k}", points, [0.007] * len(points), sides=5), spark_glow)
            arc.visible_shadow = False
            # Arcs are built in the head's local space, so parent without moving them.
            arc.parent = head
            arcs.append(arc)

    # Pixel art needs glows below clipping, or every bright pixel snaps to the same pale colour.
    GLOW = 0.6 if kit.FLAT else 1.0

    def animate(phase: float) -> None:
        turn = phase * math.tau
        crystal.location.z = 0.88 - HEAD_ORIGIN[2] + 0.025 * math.sin(turn)
        # A square crystal looks the same every quarter turn, so a quarter turn per loop is seamless.
        crystal.rotation_euler.z = turn / 4
        for i, shard in enumerate(shards):
            a = turn + i * math.tau / SHARDS
            shard.location = (0.2 * math.cos(a), 0.2 * math.sin(a), 0.9 - HEAD_ORIGIN[2] + 0.04 * math.sin(a * 2))
            shard.rotation_euler = (0.4 * math.cos(a), 0.4 * math.sin(a), a)
        pulse = 0.5 + 0.5 * math.sin(turn * 2)
        kit.set_emission(crystal_glow, (1.3 + 0.6 * pulse) * GLOW)
        kit.set_emission(seam_glow, 1.1 + 0.4 * math.sin(turn))
        light_data.energy = 2.5 + 1.2 * pulse
        make_arcs(phase)

    return kit.TowerRig(id=ID, head=head, animate=animate, frames=8, fps=12.0)
