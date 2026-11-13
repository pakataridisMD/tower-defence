"""The Ember Reach: ember_intro, ember_herald, ember_warden. Camera keys are (seconds, position, rotation) relative
to the set's mark; characters face -Y (towards a camera on the -Y side) at 0 degrees."""
import math, random
import bpy
from mathutils import Vector
import cine3d as C, hero, heralds, sets
from story.kit import aim, cart, chains


def salt_cage(S, rigs, at=(0.4, 1.2, 0), broken=True):
    """A cage of crusted salt on the steps (ember_herald 2): white crystal bars, half of them snapped."""
    SALT = C.mat("salt", (0.86, 0.85, 0.8), 0.7)
    R = random.Random(4); m = S["here"] + Vector(at)
    for k in range(14):
        a = 2 * math.pi * k / 14
        h = 2.6 if not (broken and k % 3 == 0) else R.uniform(0.5, 1.2)
        bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.07, depth=h, location=(m.x + math.cos(a) * 1.1, m.y + math.sin(a) * 1.1, h / 2))
        b = bpy.context.object; b.data.materials.append(SALT); b.rotation_euler = (R.uniform(-0.1, 0.1), R.uniform(-0.1, 0.1), 0)
        tx = bpy.data.textures.new("salt_crust", "VORONOI"); tx.noise_scale = 0.05
        d = b.modifiers.new("crust", "DISPLACE"); d.texture = tx; d.strength = 0.05
    for k in range(25):   # salt rubble
        bpy.ops.mesh.primitive_ico_sphere_add(radius=R.uniform(0.05, 0.18), subdivisions=1,
                                              location=(m.x + R.uniform(-1.6, 1.6), m.y + R.uniform(-1.6, 1.6), 0.05))
        bpy.context.object.data.materials.append(SALT)


def flare(S, rigs, who="brannoc", at=1.0, energy=600):
    """A hand-held prop flares orange at `at` seconds (Brannoc's hammer head)."""
    rig = rigs[who]
    L = C.light("POINT", (0, 0, 0), (0, 0, 0), 0, (1.0, 0.45, 0.12), 0.2, "flare")
    if "grip.r" in rig:
        g = bpy.data.objects[rig["grip.r"]]; L.parent = g; L.location = (0, 0, 0.6)
    else:   # a sprite card: the flare in front of him at hammer height
        L.parent = rig; L.location = (0.5, -0.3, 1.4)
    for t, e in ((0, 0), (at, 0), (at + 0.3, energy), (at + 2.0, energy * 0.4)):
        L.data.energy = e; L.data.keyframe_insert("energy", frame=C.sec(t))


SHOTS = {
    # Land hordes (Nov 12): Ignar's own fire turns on the Emberfolk; the Herald is Ashwick, born in Kethra.
    "ember_intro": [
        dict(set="ember", cast=[], cam=[(0, (-14, -40, 9), (80, 0, -12)), (14, (-4, -30, 7), (82, 0, 4))], lens=28),
        # Lava out of the slopes; out of it the horde; at its head runs a boy of white embers: Ashwick.
        dict(set="ember", cast=[("ashwick", (0, 13, 0), 0, "Running_A", {"walk": (0.42, (1, -1))})],
             extra=lambda S, r: sets.ash_fall(),
             cam=[aim(0, (3.2, -6, 0.7), (0, 13, 1.4)), aim(1, (2.4, -6.5, 0.8), (0, -1.5, 1.3))], norm=True, lens=40, focus="ashwick"),
        # Fennick pointing at a tower plan on a cart; Tamsin behind waving the carts through.
        dict(set="ember", cast=[("fennick", (0.4, 0, 0), -15, "Interact"), ("tamsin", (-1.8, 2.6, 0), -30, "Interact")],
             extra=lambda S, r: cart(S, (1.5, 0.5, 0)),
             cam=[(0, (1.4, -4.6, 1.6), (88, 0, 14)), (24.9, (0.9, -3.6, 1.55), (88, 0, 10))], lens=45, focus="fennick"),
    ],
    "ember_herald": [
        # Ashwick stumbling on the steps of Brazier Hold, embers scattering, his empty satchel falling open.
        dict(set="ember", cast=[("ashwick", (0, 3, 0), 0, "Death_A", {"at": 3.0}), ("tamsin", (-2.5, -1, 0), 20, "Idle")],
             extra=lambda S, r: sets.ash_fall(2500, 30, 12),
             cam=[aim(0, (3.4, -3.6, 1.6), (0, 3, 1.1)), aim(22.3, (2.4, -2.4, 1.2), (0, 3, 0.4))], lens=40, focus="ashwick"),
        # A cold forge: Brannoc wrenching out of chains of his own iron, grabbing his hammer; its head flares.
        dict(set="ember", cast=[("brannoc", (0.4, 1.2, 0), -10, "PickUp", {"at": 4.0})],
             extra=lambda S, r: (chains(S, (0.4, 1.2, 0)), flare(S, r, at=8.0)),
             cam=[(0, (2.2, -4.5, 1.4), (90, 0, 18)), (16.2, (1.6, -3.4, 1.6), (88, 0, 14))], lens=40, focus="brannoc"),
        # Brannoc on the wall of Brazier Hold, hammer on his shoulder, not smiling. Joins as a hero.
        dict(set="ember", cast=[("brannoc", (0, 0, 0), -10, "Idle")], extra=lambda S, r: flare(S, r, at=0.0, energy=300),
             cam=[(0, (1.2, -3.6, 1.9), (88, 0, 12)), (14.9, (0.8, -3.0, 1.9), (88, 0, 10))], lens=50, focus="brannoc"),
    ],
    "ember_warden": [
        dict(set="ember", cast=[("cinder_tyrant", (0, 12, 0), 0, "Death_A", {"at": 2.0, "scale": 2.4})],
             cam=[(0, (7, -12, 3), (82, 0, 26)), (18, (5, -9, 3.5), (80, 0, 22))], lens=32),
        # Ignar kneeling to Brannoc and the Emberfolk, his heart-light warming their faces.
        dict(set="ember", cast=[("ignar", (0.8, 2.6, 0), 200, "Sit_Floor_Idle"), ("brannoc", (-0.8, -0.4, 0), -160, "Idle"),
                                ("tamsin", (-2.4, 0.2, 0), -150, "Idle")],
             cam=[(0, (3.5, -5.5, 2.0), (86, 0, 30)), (18.4, (3.0, -4.6, 2.2), (84, 0, 28))], lens=40, focus="ignar"),
        # Smoke clearing off the slopes; Emberfolk relighting forges; Ignar standing among them.
        dict(set="ember", cast=[("ignar", (2, 7, 0), 10, "Idle"), ("brannoc", (-1, 4, 0), 30, "Interact"), ("fennick", (-2.6, 5.5, 0), -20, "Idle")],
             extra=lambda S, r: sets.ash_fall(1500, 40, 20, glowing=0.0),
             cam=[aim(0, (-6, -8, 2.2), (0, 6, 2.6)), aim(13.6, (-4, -6, 2.4), (0.5, 6, 3.0))], lens=30),
        dict(set="ember", cast=[("fennick", (0, 0, 0), -10, "Idle"), ("tamsin", (-1.4, 1.2, 0), -20, "Idle")],
             cam=[(0, (1.2, -3.8, 1.5), (88, 0, 14)), (9.7, (0.9, -3.3, 1.5), (88, 0, 12))], lens=45, focus="fennick"),
    ],
}
