"""Fire tower "Brazier": a two-tier basalt plinth with glowing seams and obsidian claws, holding a
bronze fire bowl with a mortar spout that turns to lob fireballs.

The base is static. Everything that turns is parented to the `head` pivot.
The loop animates the flames, the coals, the light they throw, rising embers and the seam glow.
"""

from __future__ import annotations

import math

import bpy
from mathutils import Vector

import kit

ID = "fire_brazier"

BASALT_DARK = (0.035, 0.03, 0.032)
BASALT_LIGHT = (0.16, 0.13, 0.12)
SLATE_DARK = (0.06, 0.05, 0.05)
SLATE_LIGHT = (0.17, 0.13, 0.11)
BRONZE = (0.85, 0.47, 0.20)
DARK_BRONZE = (0.45, 0.22, 0.09)
OBSIDIAN = (0.012, 0.008, 0.012)
EMBER = (1.0, 0.36, 0.05)

EMBER_COUNT = 7
#: Extra height of the upper tier, which raises the whole head.
LIFT = 0.09


def build(scene: bpy.types.Scene) -> kit.TowerRig:
    basalt = kit.stone_material("Basalt", BASALT_DARK, BASALT_LIGHT, scale=7.0)
    slate = kit.stone_material("Slate", SLATE_DARK, SLATE_LIGHT, scale=11.0, roughness=0.7)
    bronze = kit.metal_material("Bronze", BRONZE, roughness=0.28)
    dark_bronze = kit.metal_material("DarkBronze", DARK_BRONZE, roughness=0.45, wear=0.3)
    obsidian = kit.gloss_material("Obsidian", OBSIDIAN, roughness=0.35)
    seam_glow = kit.emission_material("SeamGlow", EMBER, 2.5)
    coal_glow = kit.emission_material("Coals", (1.0, 0.16, 0.01), 1.3)
    mouth_glow = kit.emission_material("MouthGlow", (1.0, 0.35, 0.04), 3.0)
    ember_glow = kit.emission_material("Embers", (1.0, 0.45, 0.08), 8.0)
    flame_state: dict = {}
    flame = kit.flame_material("Flame", flame_state)

    # --- Base (static) -------------------------------------------------------------------
    plinth = kit.assign(kit.cylinder("Plinth", 0.43, 0.11, 0.0, vertices=6, radius_top=0.40), basalt)
    kit.bevel(plinth, 0.014, 3)
    seam = kit.assign(kit.cylinder("Seam", 0.368, 0.03, 0.105, vertices=6, rotation_z=math.radians(30)), seam_glow)
    tier = kit.assign(kit.cylinder("Tier", 0.36, 0.13 + LIFT, 0.13, vertices=6, rotation_z=math.radians(30),
                                   radius_top=0.31), slate)
    kit.bevel(tier, 0.012, 3)
    # A glowing rune slit on each face of the upper tier.
    tier_mid = 0.13 + (0.13 + LIFT) * 0.5
    apothem = (0.36 + 0.31) / 2 * math.cos(math.radians(30))
    for i in range(6):
        angle = math.radians(30 + 60 * i)
        bpy.ops.mesh.primitive_cube_add(size=1, location=(
            (apothem - 0.004) * math.cos(angle), (apothem - 0.004) * math.sin(angle), tier_mid))
        rune = bpy.context.active_object
        rune.name = f"Rune{i}"
        rune.scale = (0.02, 0.028, 0.12)
        # Tilt with the tapered face so the slit sits flush.
        rune.rotation_mode = "ZYX"
        rune.rotation_euler = (0.0, -math.atan2(0.05, 0.13 + LIFT), angle)
        kit.assign(rune, seam_glow)
    # Small stepped blocks at the plinth corners give the base a built, carved look.
    for i in range(6):
        angle = math.radians(60 * i)
        block = kit.assign(kit.cylinder(f"Corner{i}", 0.05, 0.16, 0.0, vertices=4, radius_top=0.035), basalt)
        block.location.x = 0.38 * math.cos(angle)
        block.location.y = 0.38 * math.sin(angle)
        block.rotation_euler.z = angle + math.radians(45)
        kit.bevel(block, 0.008, 2)
    collar = kit.assign(kit.cylinder("Collar", 0.2, 0.05, 0.26 + LIFT, vertices=24), dark_bronze)
    kit.bevel(collar, 0.008, 2)
    # Obsidian claws curl up around the bowl. The front ones sit to the sides so the bowl stays visible.
    for i, degrees in enumerate((90, 205, 335)):
        angle = math.radians(degrees)
        out = Vector((math.cos(angle), math.sin(angle), 0.0))
        path = kit.bezier(out * 0.34 + Vector((0, 0, 0.08)), out * 0.4 + Vector((0, 0, 0.5)),
                          out * 0.25 + Vector((0, 0, 0.86)), 14)
        radii = [0.072 * (1.0 - t / 14) ** 0.8 + 0.004 for t in range(15)]
        claw = kit.assign(kit.tube(f"Claw{i}", path, radii, sides=7), obsidian)
        claw.location = (0, 0, 0)
        band_at = path[4]
        band = kit.assign(kit.torus(f"ClawBand{i}", radii[4] + 0.006, 0.013, band_at.z, segments=16), bronze)
        band.location.x, band.location.y = band_at.x, band_at.y

    # --- Head (turns to aim) -------------------------------------------------------------
    head = bpy.data.objects.new("Head", None)
    head.location = (0, 0, 0.31)
    scene.collection.objects.link(head)

    swivel = kit.assign(kit.torus("Swivel", 0.15, 0.025, 0.315, segments=32), bronze)
    stem = kit.assign(kit.cylinder("Stem", 0.085, 0.07, 0.3, vertices=24, radius_top=0.06), dark_bronze)
    vessel = kit.assign(kit.bowl("Bowl", 0.21, 0.13, 0.022, 0.355), bronze)
    rim = kit.assign(kit.torus("Rim", 0.215, 0.02, 0.485, segments=48), bronze)
    coals = kit.assign(kit.cylinder("Coals", 0.19, 0.03, 0.44, vertices=32, radius_top=0.17), coal_glow)
    # Decorative fins on both sides of the bowl.
    fins = []
    for side in (-1, 1):
        bpy.ops.mesh.primitive_cube_add(size=1, location=(-0.03, side * 0.215, 0.43))
        fin = bpy.context.active_object
        fin.name = f"Fin{side}"
        fin.scale = (0.14, 0.022, 0.09)
        fin.rotation_euler.x = math.radians(-side * 12)
        kit.assign(fin, dark_bronze)
        kit.bevel(fin, 0.01, 2)
        fins.append(fin)
    # Mortar spout pointing along +X and tilted up: this is what shows the aim direction.
    pitch = math.radians(38)
    spout_len = 0.3
    spout_base = Vector((0.13, 0.0, 0.44))
    direction = Vector((math.cos(pitch), 0.0, math.sin(pitch)))
    spout_centre = spout_base + direction * (spout_len / 2)
    bpy.ops.mesh.primitive_cylinder_add(vertices=24, radius=0.075, depth=spout_len, location=spout_centre)
    spout = bpy.context.active_object
    spout.name = "Spout"
    spout.rotation_euler = (0.0, math.pi / 2 - pitch, 0.0)
    kit.assign(spout, dark_bronze)
    kit.bevel(spout, 0.008, 2)
    mouth_pos = spout_base + direction * spout_len
    bpy.ops.mesh.primitive_torus_add(major_radius=0.085, minor_radius=0.026, major_segments=32, minor_segments=12,
                                     location=mouth_pos)
    mouth = bpy.context.active_object
    mouth.name = "Mouth"
    mouth.rotation_euler = (0.0, math.pi / 2 - pitch, 0.0)
    kit.assign(mouth, bronze)
    bpy.ops.mesh.primitive_circle_add(vertices=24, radius=0.064, fill_type="NGON",
                                      location=mouth_pos - direction * 0.004)
    mouth_core = bpy.context.active_object
    mouth_core.name = "MouthCore"
    mouth_core.rotation_euler = (0.0, math.pi / 2 - pitch, 0.0)
    kit.assign(mouth_core, mouth_glow)
    # Reinforcing hoops along the spout.
    hoops = []
    for t in (0.3, 0.62):
        bpy.ops.mesh.primitive_torus_add(major_radius=0.079, minor_radius=0.014, major_segments=24,
                                         minor_segments=8, location=spout_base + direction * spout_len * t)
        hoop = bpy.context.active_object
        hoop.rotation_euler = (0.0, math.pi / 2 - pitch, 0.0)
        kit.assign(hoop, bronze)
        hoops.append(hoop)

    # Flames: three noisy tongues of fire rising from the coals.
    noise_driver = bpy.data.objects.new("FlameNoiseDriver", None)
    scene.collection.objects.link(noise_driver)
    cloud = bpy.data.textures.new("FlameClouds", "CLOUDS")
    cloud.noise_scale = 0.09
    cloud.noise_depth = 2
    tongues = []
    for i, (x, y, height, radius) in enumerate(((0.0, 0.0, 0.34, 0.12), (-0.07, 0.06, 0.24, 0.08),
                                                 (-0.05, -0.07, 0.27, 0.085))):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=4, radius=1.0, location=(x, y, 0.47 + height * 0.85))
        tongue = bpy.context.active_object
        tongue.name = f"Flame{i}"
        tongue.scale = (radius, radius, height)
        displace = tongue.modifiers.new("Lick", "DISPLACE")
        displace.texture = cloud
        displace.texture_coords = "OBJECT"
        displace.texture_coords_object = noise_driver
        displace.strength = 0.22
        displace.mid_level = 0.5
        kit.assign(tongue, flame)
        kit.shade_smooth(tongue, 80)
        # Flames give light but should not block the key light from the bowl.
        tongue.visible_shadow = False
        tongues.append((tongue, height))

    light_data = bpy.data.lights.new("FireLight", "POINT")
    light_data.color = (1.0, 0.55, 0.2)
    light_data.shadow_soft_size = 0.06
    fire_light = bpy.data.objects.new("FireLight", light_data)
    fire_light.location = (0.0, 0.0, 0.62)
    scene.collection.objects.link(fire_light)

    embers = []
    for i in range(EMBER_COUNT):
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=0.012, location=(0, 0, 0.6))
        ember = bpy.context.active_object
        ember.name = f"Ember{i}"
        ember.visible_shadow = False
        kit.assign(ember, ember_glow)
        embers.append(ember)

    for part in (swivel, stem, vessel, rim, coals, spout, mouth, mouth_core, fire_light, noise_driver,
                 *fins, *hoops, *(t for t, _ in tongues), *embers):
        kit.parent(part, head)
    # The head parts were modelled for a low plinth; lift them onto the taller one in one go.
    head.location.z += LIFT

    def animate(phase: float) -> None:
        turn = phase * math.tau
        noise_driver.location = (0.18 * math.cos(turn), 0.18 * math.sin(turn), -0.35 * phase)
        flame_state["mapping"].inputs["Location"].default_value = (
            0.6 * math.cos(turn), 0.6 * math.sin(turn), 0.0)
        for i, (tongue, height) in enumerate(tongues):
            wobble = 1.0 + 0.12 * math.sin(turn * 2 + i * 2.1)
            tongue.scale.z = height * wobble
        light_data.energy = 6.0 + 1.8 * math.sin(turn * 3) + 1.2 * math.sin(turn * 5 + 1.0)
        kit.set_emission(coal_glow, 1.3 + 0.4 * math.sin(turn * 2))
        kit.set_emission(seam_glow, 2.2 + 0.9 * math.sin(turn))
        for i, ember in enumerate(embers):
            local = (phase + i / EMBER_COUNT) % 1.0
            spin = math.tau * (i * 0.37 + local * 0.6)
            radius = 0.06 + 0.1 * local
            # Embers are parented to the head, so positions are relative to the pivot.
            ember.location = (radius * math.cos(spin), radius * math.sin(spin), 0.27 + 0.5 * local)
            ember.scale = [max(0.05, 1.0 - local) * (0.8 + 0.4 * ((i * 7) % 3) / 2)] * 3

    return kit.TowerRig(id=ID, head=head, animate=animate, frames=8, fps=10.0)
