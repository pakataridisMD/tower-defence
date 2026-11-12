"""The Ember Reach: ember_intro, ember_herald, ember_warden. Camera keys are (seconds, position, rotation) relative
to the set's mark; characters face -Y (towards a camera on the -Y side) at 0 degrees."""
import math, random
import bpy
from mathutils import Vector
import cine3d as C, hero, heralds, sets


def salt_cage(S, rigs, at=(0.4, 1.2, 0), broken=True):
    """A cage of crusted salt on the steps (ember_herald 2): white crystal bars, half of them snapped."""
    SALT = C.mat("salt", (0.86, 0.85, 0.8), 0.7)
    R = random.Random(4); m = S["marks"]["hero"] + Vector(at)
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
    g = bpy.data.objects[rig["grip.r"]]; L.parent = g; L.location = (0, 0, 0.6)
    for t, e in ((0, 0), (at, 0), (at + 0.3, energy), (at + 2.0, energy * 0.4)):
        L.data.energy = e; L.data.keyframe_insert("energy", frame=C.sec(t))


SHOTS = {
    "ember_intro": [
        dict(set="ember", cast=[], cam=[(0, (-14, -40, 9), (80, 0, -12)), (14, (-4, -30, 7), (82, 0, 4))], lens=28),
        dict(set="ember", cast=[("ourra", (0, 22, 0), 0, "Walking_A", {"walk": (0.6, (1, -1))})],
             cam=[(0, (6, -6, 2.2), (84, 0, 18)), (19, (4, -2, 2.6), (82, 0, 12))], lens=40),
        dict(set="ember", cast=[("fennick", (0.4, 0, 0), -15, "Interact"), ("tamsin", (-1.6, 2.4, 0), -30, "Idle")],
             cam=[(0, (1.4, -4.6, 1.6), (88, 0, 14)), (21, (0.9, -3.6, 1.55), (88, 0, 10))], lens=45, focus="fennick"),
    ],
    "ember_herald": [
        dict(set="ember", cast=[("ourra", (0, 6, 0), 0, "Death_A"), ("tamsin", (-2.5, -1, 0), 20, "Idle")],
             cam=[(0, (5, -9, 2.8), (84, 0, 24)), (21, (3.5, -7, 2.4), (84, 0, 20))], lens=35),
        dict(set="ember", cast=[("brannoc", (0.4, 1.2, 0), -10, "PickUp")], extra=lambda S, r: (salt_cage(S, r), flare(S, r, at=6.0)),
             cam=[(0, (2.2, -4.5, 1.4), (90, 0, 18)), (20, (1.6, -3.4, 1.6), (88, 0, 14))], lens=40, focus="brannoc"),
        dict(set="ember", cast=[("brannoc", (0, 0, 0), -10, "Cheer")], extra=lambda S, r: flare(S, r, at=0.0, energy=300),
             cam=[(0, (1.2, -3.6, 1.9), (88, 0, 12)), (13, (0.8, -3.0, 1.9), (88, 0, 10))], lens=50, focus="brannoc"),
    ],
    "ember_warden": [
        dict(set="ember", cast=[("cinder_tyrant", (0, 8, 0), 0, "Death_A")],
             cam=[(0, (7, -12, 3), (82, 0, 26)), (18, (5, -9, 3.5), (80, 0, 22))], lens=32),
        dict(set="ember", cast=[("ignar", (0.8, 2.6, 0), 200, "Sit_Floor_Idle"), ("brannoc", (-0.8, -0.4, 0), -160, "Idle"),
                                ("tamsin", (-2.4, 0.2, 0), -150, "Idle")],
             cam=[(0, (3.5, -5.5, 2.0), (86, 0, 30)), (12.6, (3.0, -4.6, 2.2), (84, 0, 28))], lens=40, focus="ignar"),
        dict(set="ember", cast=[("ignar", (3, 10, 0), 0, "Walking_A", {"walk": (0.5, (1, -1))})],
             cam=[(0, (-10, -24, 7), (80, 0, -20)), (15, (-6, -18, 5), (82, 0, -14))], lens=30),
        dict(set="ember", cast=[("fennick", (0, 0, 0), -10, "Idle"), ("tamsin", (-1.4, 1.2, 0), -20, "Idle")],
             cam=[(0, (1.2, -3.8, 1.5), (88, 0, 14)), (9.7, (0.9, -3.3, 1.5), (88, 0, 12))], lens=45, focus="fennick"),
    ],
}
