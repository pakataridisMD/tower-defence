"""Sunscar Canyon: earth_intro, earth_herald, earth_warden."""
import math
import bpy
from mathutils import Vector
import cine3d as C, heralds, wardens as W
from story.kit import aim, towers, boulders, walking_rocks

AMBER = (1.0, 0.7, 0.3)


def doors(S, y=9.0, t0=2.0, t1=11.0):
    """The great stone doors of Grundhallow swinging shut on the dead; torches along the hall."""
    m = S["here"]; STONE = W.mountain_stone("hall_door", (0.36, 0.22, 0.16), moss=0.0)
    for sx in (-1, 1):
        hinge = bpy.data.objects.new("door_hinge", None); C.sc.collection.objects.link(hinge)
        hinge.location = (m.x + sx * 4.0, m.y + y, 0)
        d = C.box("door", (0, 0, 0), (4.0, 0.6, 9.0), STONE, bevel=0.08)
        d.parent = hinge; d.location = (-sx * 2.0, 0, 4.5)
        for t, ang in ((0, 1.35), (t0, 1.35), (t1, 0.0)):
            hinge.rotation_euler.z = sx * ang; hinge.keyframe_insert("rotation_euler", index=2, frame=C.sec(t))
        for k in range(4):
            C.brazier(m.x + sx * 3.2, m.y + y + 3 + k * 4, 0, 350)


SHOTS = {
    # Land hordes (Nov 12): Orrok's canyon walls walk; the Herald is Gorrath, who held the Kharum Pass beside Gorrim.
    "earth_intro": [
        # Red rock canyon by torchlight, cliff cities in terraces, stone faces of old kings.
        dict(set="earth", cam=[aim(0, (-10, -20, 4), (6, 50, 12)), aim(17, (-4, -14, 6), (8, 50, 14))], lens=26),
        # The walls breaking into walking stone; at their head Gorrath, a square hole in his chest.
        dict(set="earth", cast=[("gorrath", (0, 14, 0), 0, "Walking_A", {"walk": (0.5, (1, -1))})],
             extra=lambda S, r: walking_rocks(S, 8, (0, 22, 0), 9),
             cam=[aim(0, (3.2, -3, 0.6), (0, 10, 3.2)), aim(23.6, (2.6, -2.2, 0.5), (0, 4, 3.0))], lens=30, focus="gorrath"),
        # Kaela at the canyon rim, watching the walls move below.
        dict(set="earth", cast=[("kaela", (0, 0, 0), 150, "Idle")], extra=lambda S, r: walking_rocks(S, 6, (0, 30, 0), 12, 0.3),
             cam=[aim(0, (-1.8, -2.4, 1.5), (0, 0, 1.7)), aim(10.2, (-1.5, -2.0, 1.55), (0, 0.3, 1.8))], lens=45, focus="kaela"),
    ],
    "earth_herald": [
        # Gorrath breaking apart on the terraces into boulders that keep rolling, then stop.
        dict(set="earth", cast=[("gorrath", (0, 6, 0), 0, "Death_A", {"at": 2.0})],
             extra=lambda S, r: boulders(S, (0, 6, 2.0), start=2.5),
             cam=[aim(0, (6, -6, 1.8), (0, 5, 1.8)), aim(22.3, (4.5, -4.5, 1.6), (0, 4, 1.2))], lens=35, focus="gorrath"),
        # Gorrim Stonebeard in front of what is left of the shield-company.
        dict(set="earth", cast=[("gorrim", (0, 0, 0), -10, "Blocking")],
             cam=[aim(0, (1.4, -3.2, 0.9), (0, 0, 1.1)), aim(18.9, (1.0, -2.6, 0.9), (0, 0, 1.15))], lens=40, focus="gorrim"),
        # Gorrim braiding a new ring into his beard, then hefting the door-shield. Joins as a hero.
        dict(set="earth", cast=[("gorrim", (0, 0, 0), -15, "Use_Item")], extra=lambda S, r: towers(S, col=AMBER),
             cam=[aim(0, (1.0, -2.2, 1.25), (0, 0, 1.2)), aim(11, (1.0, -2.6, 1.3), (0, 0, 1.2))], lens=50, focus="gorrim"),
    ],
    "earth_warden": [
        # The Mountain Titan crashing down; under the grey, Orrok.
        dict(set="earth", cast=[("mountain_titan", (0, 10, 0), 0, "Death_A", {"at": 2.0})],
             cam=[aim(0, (-4, -6, 0.8), (0, 10, 4.5)), aim(16.3, (-3, -4.5, 0.8), (0, 10, 2.5))], lens=26),
        # Orrok, enormous, looking at the towers: "...Thank you."
        dict(set="earth", cast=[("orrok", (0, 4, 0), 0, "Idle")], extra=lambda S, r: towers(S, ((-6, 3), (6, 4)), AMBER),
             cam=[aim(0, (0.8, -3.0, 1.0), (0, 4, 4.2)), aim(4.3, (0.7, -2.7, 1.0), (0, 4, 4.3))], lens=30, focus="orrok"),
        # The great stone doors of Grundhallow closing on the dead.
        dict(set="earth", extra=lambda S, r: doors(S),
             cam=[aim(0, (0, -6, 1.7), (0, 12, 3.5)), aim(13.6, (0, -3, 1.7), (0, 12, 3.5))], lens=30),
        # Gorrim: "That's the last ring."
        dict(set="earth", cast=[("gorrim", (0, 0, 0), -10, "Use_Item")],
             cam=[aim(0, (0.8, -1.8, 1.25), (0, 0, 1.2)), aim(7.7, (0.6, -1.5, 1.25), (0, 0, 1.2))], lens=60, focus="gorrim"),
    ],
}
