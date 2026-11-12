"""Frostmere: water_intro, water_herald, water_warden."""
import bpy
import cine3d as C, heralds
from story.kit import aim, reeds, ice_cage, stilt_town, rise, towers, ice_holes, floodwater

ICE_BLUE = (0.5, 0.85, 1.0)


def black_wake(S, rigs, who="ashwick", length=28):
    """A strip of black open water behind a running figure."""
    m = S["here"]
    bpy.ops.mesh.primitive_plane_add(size=1, location=(m.x, m.y + length / 2 + 6, 0.02))
    o = bpy.context.object; o.scale = (1.6, length, 1); o.data.materials.append(heralds.black_water("wake_water"))


def letter(S, at=(0.6, -0.8, 0.01)):
    """An oilskin packet split open on the ice: an order under the Lord Marshal's red seal."""
    m = S["here"]
    bpy.ops.mesh.primitive_plane_add(size=0.22, location=(m.x + at[0], m.y + at[1], at[2]))
    o = bpy.context.object; o.scale = (1, 0.7, 1); o.rotation_euler.z = 0.4
    o.data.materials.append(C.mat("letter", (0.85, 0.8, 0.68), 0.8))
    bpy.ops.mesh.primitive_cylinder_add(radius=0.025, depth=0.006, location=(m.x + at[0], m.y + at[1], 0.015))
    bpy.context.object.data.materials.append(C.mat("seal_wax", (0.5, 0.03, 0.02), 0.4))


SHOTS = {
    # Land hordes (Nov 12): Thalassa's sea breaks the ice under Frostmere; the Herald is the Saltmother, the Tidefolk's
    # own high priestess (Ourra), walking inside her column of black seawater.
    "water_intro": [
        # A vast frozen sea in the dark, stilt towns, harbours lit by torches.
        dict(set="water", extra=lambda S, r: stilt_town(S),
             cam=[aim(0, (-20, -25, 8), (25, 70, 2)), aim(15.9, (-10, -16, 6), (28, 70, 3))], lens=28),
        # The ice cracking open from below, the drowned climbing out; inside a column of black seawater, the Saltmother.
        dict(set="water", cast=[("ourra", (0, 16, 0), 0, "Walking_A", {"walk": (0.45, (1, -1))})],
             extra=lambda S, r: ice_holes(S),
             cam=[aim(0, (4, -6, 1.0), (0, 16, 2.2)), aim(25, (2.6, -4, 1.0), (0, 6, 2.2))], lens=35, focus="ourra"),
        # Tamsin on the ice at Netmend, Fennick's spectacles round her neck, his notebook open.
        dict(set="water", cast=[("tamsin", (0, 0, 0), -15, "Use_Item")], extra=lambda S, r: (stilt_town(S, (10, 30, 0), 6), ice_holes(S, 4, (6, 10), (2, 8, 0))),
             cam=[aim(0, (1.4, -3.6, 1.6), (0, 0, 1.6)), aim(12.7, (1.0, -3.0, 1.6), (0, 0, 1.65))], lens=45, focus="tamsin"),
    ],
    "water_herald": [
        # The Saltmother's column bursting apart on the ice; beside her an oilskin packet with the Marshal's seal.
        dict(set="water", cast=[("ourra", (0, 1.5, 0), 0, "Death_A", {"at": 3.0})], extra=lambda S, r: (ice_holes(S, 5, (6, 6), (0, 4, 0)), letter(S)),
             cam=[aim(0, (3.4, -4.2, 1.6), (0, 1.0, 1.3)), aim(21.9, (2.0, -2.6, 1.0), (0.4, -0.4, 0.2))], lens=35, focus="ourra"),
        # A tower of ice standing in black floodwater; inside, Mirelle with her ice staff.
        dict(set="water", cast=[("mirelle", (0, 2, 0), 0, "Idle")],
             extra=lambda S, r: (ice_cage(S, (0, 2, 0)), floodwater(S, 7.0, (0, 2, 0))),
             cam=[aim(0, (0, -9, 1.4), (0, 2, 2.0)), aim(18.9, (0.5, -5.5, 1.3), (0, 2, 1.3))], lens=35, focus="mirelle"),
        # Mirelle stepping out onto the frost. Joins as a hero.
        dict(set="water", cast=[("mirelle", (0, 1.2, 0), 0, "Walking_A", {"walk": (0.35, (1, -1))})],
             extra=lambda S, r: towers(S, col=ICE_BLUE),
             cam=[aim(0, (1.0, -2.6, 1.3), (0, 1, 1.3)), aim(7.5, (0.8, -2.2, 1.3), (0, -1, 1.3))], lens=50, focus="mirelle"),
    ],
    "water_warden": [
        # Thalassa rising from the sea as the ice-eel breaks apart.
        dict(set="water", set_args=dict(frozen=False), cast=[("thalassa", (0, 10, 0), 0, "Idle")],
             extra=lambda S, r: rise(r, "thalassa", 3.6, 1.0, 9.0),
             cam=[aim(0, (-3, -7, 0.6), (0, 10, 3)), aim(16.2, (-2, -5, 0.6), (0, 10, 3.6))], lens=28, focus="thalassa"),
        # Thalassa looking down at the towers and heroes.
        dict(set="water", cast=[("thalassa", (0, 4, 0), 0, "Idle"), ("mirelle", (-1.2, -1.5, 0), 180, "Idle"),
                                ("tamsin", (1.0, -1.8, 0), 180, "Idle")],
             extra=lambda S, r: towers(S, ((-6, 3), (6, 4)), ICE_BLUE),
             cam=[aim(0, (0.6, -4.6, 0.8), (0, 4, 3.0)), aim(13.2, (0.4, -4.0, 0.8), (0, 4, 3.2))], lens=30, focus="thalassa"),
        # Mirelle alone on the shore; behind her the black holes in the harbour freezing over.
        dict(set="water", cast=[("mirelle", (0, 0, 0), 10, "Idle")],
             extra=lambda S, r: (stilt_town(S, (20, 50, 0), 10), ice_holes(S, 8, (14, 20), (4, 18, 0), freeze=(3.0, 16.0))),
             cam=[aim(0, (2.6, -5, 1.3), (0, 0, 1.2)), aim(21, (1.2, -3, 1.3), (0, 0, 1.25))], lens=45, focus="mirelle"),
    ],
}
