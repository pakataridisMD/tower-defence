"""The Hollow Rift: void_intro, void_herald, void_warden."""
import math
import bpy
import cine3d as C, hero
from story.kit import aim, towers, hand_glow

VIOLET = (0.7, 0.45, 1.0)
LANDS = [(1.0, 0.3, 0.08), (0.75, 0.85, 1.0), (0.35, 1.0, 0.35), (0.3, 0.85, 1.0), (1.0, 0.7, 0.3), (0.7, 0.45, 1.0)]


def ring_map(S, rigs, lit_every=1.2):
    """The painted map of the Ring on a round table; the six Wardens' lights come on one by one."""
    m = S["here"]
    bpy.ops.mesh.primitive_cylinder_add(vertices=64, radius=1.3, depth=0.08, location=(m.x, m.y, 0.9))
    bpy.context.object.data.materials.append(C.mat("map_parchment", (0.55, 0.45, 0.3), 0.85))
    bpy.ops.mesh.primitive_torus_add(major_radius=0.85, minor_radius=0.03, location=(m.x, m.y, 0.95))
    bpy.context.object.data.materials.append(C.mat("map_ink", (0.1, 0.07, 0.05), 0.9))
    for k, rgb in enumerate(LANDS):
        a = math.pi / 2 + 2 * math.pi * k / 6
        g = C.mat("land_light_%d" % k, (0.1, 0.1, 0.1), 0.5, emit=rgb, strength=0.0)
        s = g.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
        for t, v in ((0, 0.0), (0.6 + k * lit_every, 0.0), (1.2 + k * lit_every, 12.0)):
            s.default_value = v; s.keyframe_insert("default_value", frame=C.sec(t))
        bpy.ops.mesh.primitive_uv_sphere_add(radius=0.05, location=(m.x + math.cos(a) * 0.85, m.y + math.sin(a) * 0.85, 0.98))
        bpy.context.object.data.materials.append(g)
    C.light("POINT", (m.x + 0.6, m.y - 0.8, 2.2), (0, 0, 0), 60, (1.0, 0.7, 0.4), 0.2, "candle")


def far_light(S, rigs, at=(-14, 70, -40)):
    """A small white light moving slowly along the bottom of the Rift."""
    m = S["here"]
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=(m.x + at[0], m.y + at[1], at[2]))
    o = bpy.context.object; o.data.materials.append(hero.glow_mat("grey_lantern_far", (1, 1, 0.95), 40))
    o.keyframe_insert("location", frame=1); o.location.x += 8; o.keyframe_insert("location", frame=C.sec(15))


def choir(S, rigs, who="vesper"):
    hero.wisps(rigs[who], 1.4, n=9, radius=1.4, energy=10)


SHOTS = {
    # Land hordes (Nov 12): Nyxara's dark climbs out of the Rift; the Herald is the Pale Vesper, singing her own dead awake.
    "void_intro": [
        # The Hollow Rift at night: floating stone steps, violet lanterns, the edge of the chasm.
        dict(set="void", cam=[aim(0, (-8, -16, 5), (4, 40, 4)), aim(17, (-3, -10, 4), (6, 40, 6))], lens=26),
        # Looking down into the Rift: the Gate far below.
        dict(set="rift", cam=[aim(0, (0, 15, 55), (0, -95, 2)), aim(14.7, (0, 5, 48), (0, -95, 2))], lens=35),
        # The dark spilling over the rim; the dead climbing out of their graves; the Pale Vesper singing.
        dict(set="void", cast=[("vesper", (0, 7, 0), 0, "Walking_A", {"walk": (0.3, (1, -1))})], extra=lambda S, r: choir(S, r),
             cam=[aim(0, (2.2, -4, 1.0), (0, 7, 1.9)), aim(22.3, (1.4, -2.8, 1.1), (0, 1.0, 1.9))], lens=40, focus="vesper"),
        # Sylvaine at the rim, Elowen's seed glowing green in her closed hand.
        dict(set="void", cast=[("sylvaine", (0, 0, 0), -20, "Idle")], extra=lambda S, r: hand_glow(r, "sylvaine"),
             cam=[aim(0, (1.4, -2.6, 1.5), (0, 0, 1.4)), aim(6.7, (1.1, -2.2, 1.5), (0, 0, 1.4))], lens=50, focus="sylvaine"),
        # Tamsin at Lamplight looking down into the Rift; far below a white light moving.
        dict(set="void", cast=[("tamsin", (0, 4, 0), 180, "Idle")], extra=lambda S, r: far_light(S, r),
             cam=[aim(0, (1.4, 0.4, 2.3), (-6, 60, -18)), aim(12.3, (1.1, 1.0, 2.25), (-4, 60, -20))], lens=40, focus="tamsin"),
    ],
    "void_herald": [
        # The Pale Vesper falling on the floating steps, her ghost-choir scattering, the dead dropping.
        dict(set="void", cast=[("vesper", (0, 3, 0), 0, "Death_A", {"at": 2.0})], extra=lambda S, r: choir(S, r),
             cam=[aim(0, (3.5, -3.5, 1.4), (0, 3, 1.3)), aim(11, (2.6, -2.4, 1.1), (0, 3, 0.7))], lens=35, focus="vesper"),
        # A crypt: Corvin cutting himself free of grave-wrappings and getting up.
        dict(set="hall", set_args=dict(ruined=True), cast=[("corvin", (0, 0, 0), 0, "Sit_Floor_StandUp", {"at": 9.0})],
             cam=[aim(0, (1.4, -2.6, 0.8), (0, 0, 0.8)), aim(22.8, (1.0, -2.4, 1.3), (0, 0, 1.6))], lens=45, focus="corvin"),
        # Corvin standing, looking at the player. Joins as a hero.
        dict(set="void", cast=[("corvin", (0, 0, 0), -10, "Idle")], extra=lambda S, r: towers(S, col=VIOLET),
             cam=[aim(0, (1.2, -2.8, 1.75), (0, 0, 1.7)), aim(17.1, (0.8, -2.3, 1.75), (0, 0, 1.75))], lens=50, focus="corvin"),
    ],
    "void_warden": [
        # The Hollow King breaking; Nyxara stepping out of it.
        dict(set="void", cast=[("hollow_king", (0, 5, 0), 0, "Death_A", {"at": 2.0}), ("nyxara", (1.8, 3.5, 0), -20, "Idle")],
             cam=[aim(0, (-2.5, -5, 1.2), (0.6, 4.5, 2.4)), aim(15.7, (-1.6, -3.8, 1.2), (1.2, 3.5, 2.4))], lens=32, focus="nyxara"),
        # Nyxara looking down into the Rift, the stars moving in her face.
        dict(set="void", cast=[("nyxara", (0, 4, 0), 160, "Idle")],
             cam=[aim(0, (2.4, 1.5, 2.2), (0, 4, 2.9)), aim(13.3, (2.0, 2.0, 2.2), (0, 4, 2.95))], lens=50, focus="nyxara"),
        # The six Wardens' lights on the painted map of the Ring.
        dict(set="solenne", set_args=dict(night=True), mark="square", extra=lambda S, r: ring_map(S, r),
             cam=[aim(0, (0.4, -1.6, 2.4), (0, 0, 0.95)), aim(9.3, (0.2, -1.2, 2.2), (0, 0, 0.95))], lens=40),
    ],
}
