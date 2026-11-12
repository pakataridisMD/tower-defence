"""Sunscar Canyon: earth_intro, earth_herald, earth_warden."""
import math
import bpy
from mathutils import Vector
import cine3d as C, heralds, wardens as W
from story.kit import aim, towers

AMBER = (1.0, 0.7, 0.3)


def bird_circle(S, rigs, centre=(0, 30, 18), r=14.0, secs=24.0, rider="vholt"):
    """Vholt on his black thunderbird, circling high over the canyon."""
    c = S["marks"]["hero"] + Vector(centre)
    root, saddle = heralds.thunderbird(loc=tuple(c), span=8.0)
    if rider in rigs:
        heralds.mount(rigs[rider], saddle)
    for k in range(9):
        a = math.pi * 0.2 + k * (math.pi * 0.9 / 8); t = secs * k / 8
        root.location = (c.x + math.cos(a) * r, c.y + math.sin(a) * r * 0.6, c.z + math.sin(k) * 1.5)
        root.rotation_euler = (0, -0.25, a + math.pi)   # banking into the turn, beak along the path
        root.keyframe_insert("location", frame=C.sec(t)); root.keyframe_insert("rotation_euler", frame=C.sec(t))


def bird_down(S, rigs, at=(2.5, 3.5, 0)):
    """The thunderbird crashed on the terraces, wings spread, still smoking."""
    root, _ = heralds.thunderbird(loc=tuple(S["marks"]["hero"] + Vector(at) + Vector((0, 0, 0.9))), span=8.0, flap=0)
    root.rotation_euler = (0.25, 0.15, 2.4)


def doors(S, y=9.0, t0=2.0, t1=11.0):
    """The great stone doors of Grundhallow swinging shut on the dead; torches along the hall."""
    m = S["marks"]["hero"]; STONE = W.mountain_stone("hall_door", (0.36, 0.22, 0.16), moss=0.0)
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
    "earth_intro": [
        # Red rock canyon by torchlight, cliff cities in terraces, stone faces of old kings.
        dict(set="earth", cam=[aim(0, (-10, -20, 4), (6, 50, 12)), aim(17, (-4, -14, 6), (8, 50, 14))], lens=26),
        # Storm spirits pouring down the walls; above them, on a thunderbird, Vholt.
        dict(set="earth", cast=[("vholt", (0, 0, 0), 0, "Sit_Chair_Idle")], extra=lambda S, r: bird_circle(S, r, secs=25),
             cam=[aim(0, (2, -10, 1.5), (0, 30, 14)), aim(24.8, (0, -8, 1.5), (-6, 34, 16))], lens=28),
        # Kaela at the canyon rim, watching the black bird circle.
        dict(set="earth", cast=[("kaela", (0, 0, 0), 150, "Idle")], extra=lambda S, r: bird_circle(S, r, (0, 40, 22), 16, 12),
             cam=[aim(0, (-1.8, -2.4, 1.5), (0, 0, 1.7)), aim(11.2, (-1.5, -2.0, 1.55), (0, 0.3, 1.8))], lens=45, focus="kaela"),
    ],
    "earth_herald": [
        # The thunderbird crashed on the terraces, Vholt crawling free, Kaela over him with her lance.
        dict(set="earth", cast=[("vholt", (0, 0.8, 0), 0, "Sit_Floor_Idle"), ("kaela", (-0.4, -0.9, 0), 160, "2H_Melee_Idle")],
             extra=lambda S, r: bird_down(S, r),
             cam=[aim(0, (3.4, -3.4, 1.4), (0, 0.4, 0.9)), aim(11.3, (2.8, -2.6, 1.2), (0, 0.4, 0.8))], lens=35, focus="vholt"),
        # Vholt's face, the grey light going out of his eyes.
        dict(set="earth", cast=[("vholt", (0, 0, 0), 0, "Sit_Floor_Idle")],
             cam=[aim(0, (0.4, -1.5, 0.75), (0, 0, 0.95)), aim(16.6, (0.3, -1.2, 0.75), (0, 0, 0.97))], lens=65, fstop=2.0,
             focus="vholt"),
        # Gorrim Stonebeard in front of what is left of the shield-company.
        dict(set="earth", cast=[("gorrim", (0, 0, 0), -10, "Blocking")],
             cam=[aim(0, (1.4, -3.2, 0.9), (0, 0, 1.1)), aim(13.7, (1.0, -2.6, 0.9), (0, 0, 1.15))], lens=40, focus="gorrim"),
        # Gorrim hefting the door-shield. Joins as a hero.
        dict(set="earth", cast=[("gorrim", (0, 0, 0), -15, "Idle")], extra=lambda S, r: towers(S, col=AMBER),
             cam=[aim(0, (1.2, -2.6, 1.3), (0, 0, 1.2)), aim(11.8, (0.9, -2.2, 1.3), (0, 0, 1.25))], lens=50, focus="gorrim"),
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
             cam=[aim(0, (0, -6, 1.7), (0, 12, 3.5)), aim(15.2, (0, -3, 1.7), (0, 12, 3.5))], lens=30),
        # Gorrim braiding one more iron ring into his beard.
        dict(set="earth", cast=[("gorrim", (0, 0, 0), -10, "Use_Item")],
             cam=[aim(0, (0.8, -1.8, 1.25), (0, 0, 1.2)), aim(7.7, (0.6, -1.5, 1.25), (0, 0, 1.2))], lens=60, focus="gorrim"),
    ],
}
