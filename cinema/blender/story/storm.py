"""The Thunder Steppe: storm_intro, storm_herald, storm_warden. Characters face -Y at 0 degrees; camera keys come
from kit.aim (position, target), relative to the set's mark."""
import sets
import cine3d as C
from story.kit import aim, stones, shards, towers, bird_circle, bird_down

TEAL = (0.45, 0.75, 1.0)

SHOTS = {
    # Land hordes (Nov 12): Aurath's storms strike the Galeborn camps; the Herald is Vholt, who taught Kaela to ride.
    "storm_intro": [
        # Endless high grass under a racing sky, standing stones, tent-cities.
        dict(set="storm", extra=lambda S, r: stones(S, (8, 34, 0)),
             cam=[aim(0, (-22, -30, 9), (10, 40, 2)), aim(19, (-8, -20, 6), (12, 40, 3))], lens=28),
        # Lightning on a burning tent camp; over it, on a thunderbird of black cloud, Vholt.
        dict(set="storm", cast=[("vholt", (0, 0, 0), 0, "Sit_Chair_Idle")],
             extra=lambda S, r: (bird_circle(S, r, (0, 34, 16), 14, 24), camp_fires(S)),
             cam=[aim(0, (-4, -10, 1.4), (0, 30, 12)), aim(23.6, (-2, -8, 1.4), (-6, 34, 14))], lens=28),
        # Fennick, holding his hat on, pointing at a camp of standing stones.
        dict(set="storm", extra=lambda S, r: stones(S, (6, 28, 0)),
             cast=[("fennick", (0, 0, 0), 160, "Interact"), ("tamsin", (-1.5, 0.8, 0), 170, "Idle")],
             cam=[aim(0, (1.8, -3.8, 1.6), (2, 20, 1.6)), aim(14.9, (1.4, -3.2, 1.6), (3, 20, 2))], lens=32, focus="fennick"),
    ],
    "storm_herald": [
        # The black thunderbird crashed on the ridge at Highwind; Kaela over it, lance crackling.
        dict(set="storm", cast=[("kaela", (-0.6, -0.8, 0), 200, "2H_Melee_Idle")], extra=lambda S, r: bird_down(S, r, (1.5, 3.0, 0)),
             cam=[aim(0, (4, -5, 1.6), (0.5, 2, 1.2)), aim(18.9, (3, -4, 1.4), (0.5, 2, 1.0))], lens=32, focus="kaela"),
        # Vholt crawling free of the wreck, the grey light flickering out of his eyes as he looks up at her.
        dict(set="storm", cast=[("vholt", (0, 0, 0), 0, "Sit_Floor_Idle")], extra=lambda S, r: bird_down(S, r, (2.5, 3.5, 0)),
             cam=[aim(0, (0.4, -1.5, 0.75), (0, 0, 0.95)), aim(14, (0.3, -1.2, 0.75), (0, 0, 0.97))], lens=65, fstop=2.0, focus="vholt"),
        # Kaela standing over the fallen warchief, lance lowered, rain starting.
        dict(set="storm", cast=[("kaela", (0, -0.6, 0), 180, "2H_Melee_Idle"), ("vholt", (0, 1.0, 0), 0, "Death_A_Pose")],
             extra=lambda S, r: bird_down(S, r, (2.5, 4.0, 0)),
             cam=[aim(0, (-3, -3.5, 2.2), (0, 0.3, 0.8)), aim(6.2, (-2.6, -3.0, 2.1), (0, 0.3, 0.8))], lens=35, focus="kaela"),
        # Kaela reining in beside the towers, looking back at Highwind. Joins as a hero.
        dict(set="storm", cast=[("kaela", (0, 0, 0), -20, "Idle")], extra=lambda S, r: towers(S, col=TEAL),
             cam=[aim(0, (1.6, -3.6, 1.7), (0, 0, 1.6)), aim(9.7, (1.1, -2.9, 1.7), (0, 0, 1.65))], lens=50, focus="kaela"),
    ],
    "storm_warden": [
        # The black cloud shattering, frozen lightning falling like glass.
        dict(set="storm", cast=[("thunderhead", (0, 22, 0), 0, "Death_A", {"at": 1.5, "scale": 4.0})],
             extra=lambda S, r: shards(S, (0, 14, 0), n=220, top=30, spread=14, over=11.0),
             cam=[aim(0, (-3, -6, 0.8), (0, 22, 12)), aim(17.6, (-2, -4, 0.7), (0, 22, 7))], lens=24),
        # Aurath, a rider-shape of cloud and lightning, bowing over the towers.
        dict(set="storm", cast=[("aurath", (0, 3, 0), 0, "Idle")], extra=lambda S, r: towers(S, ((-7, 6), (6, 8)), TEAL),
             cam=[aim(0, (1.5, -3.5, 0.9), (0, 3, 2.6)), aim(13.6, (1.0, -2.6, 0.9), (0, 3, 2.7))], lens=35, focus="aurath"),
        # Galeborn raising their tents again; Kaela watching.
        dict(set="storm", cast=[("kaela", (0, 0, 0), 180, "Idle")], extra=lambda S, r: stones(S, (8, 34, 0)),
             cam=[aim(0, (1.2, -4, 1.8), (2, 30, 2)), aim(10.6, (0.6, -3.2, 1.8), (2, 30, 2.5))], lens=35, focus="kaela"),
    ],
}


def camp_fires(S, n=5, seed=9):
    """Tents burning where the lightning struck."""
    import random
    R = random.Random(seed)
    for k in range(n):
        x, y = R.uniform(-30, 30), R.uniform(18, 60)
        C.brazier(x, y, 0, 1500)
