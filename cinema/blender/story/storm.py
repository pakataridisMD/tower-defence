"""The Thunder Steppe: storm_intro, storm_herald, storm_warden. Characters face -Y at 0 degrees; camera keys come
from kit.aim (position, target), relative to the set's mark."""
import sets
from story.kit import aim, stones, shards, boulders, towers

TEAL = (0.45, 0.75, 1.0)

SHOTS = {
    "storm_intro": [
        # Endless high grass under a racing sky, standing stones, tent-cities.
        dict(set="storm", extra=lambda S, r: stones(S, (8, 34, 0)),
             cam=[aim(0, (-22, -30, 9), (10, 40, 2)), aim(19, (-8, -20, 6), (12, 40, 3))], lens=28),
        # A frozen, motionless sky; the earth climbing the plateau; at its head Gorrath.
        dict(set="storm", set_args=dict(lightning=False),
             cast=[("gorrath", (0, 14, 0), 0, "Walking_A", {"walk": (0.55, (1, -1))})],
             cam=[aim(0, (3.2, -3, 0.6), (0, 10, 3.2)), aim(20, (2.6, -2.2, 0.5), (0, 4, 3.0))], lens=30, focus="gorrath"),
        # Fennick, holding his hat on, pointing at a camp of standing stones.
        dict(set="storm", extra=lambda S, r: stones(S, (6, 28, 0)),
             cast=[("fennick", (0, 0, 0), 160, "Interact"), ("tamsin", (-1.5, 0.8, 0), 170, "Idle")],
             cam=[aim(0, (1.8, -3.8, 1.6), (2, 20, 1.6)), aim(9.7, (1.4, -3.2, 1.6), (3, 20, 2))], lens=32, focus="fennick"),
    ],
    "storm_herald": [
        # Gorrath breaking apart on the ridge into boulders that keep rolling, then stop.
        dict(set="storm", cast=[("gorrath", (0, 6, 0), 0, "Death_A", {"at": 2.0})],
             extra=lambda S, r: boulders(S, (0, 6, 2.0), start=2.5),
             cam=[aim(0, (6, -6, 1.8), (0, 5, 1.8)), aim(20.4, (4.5, -4.5, 1.6), (0, 4, 1.2))], lens=35, focus="gorrath"),
        # Kaela bursting out of the dust, lightning lance crackling.
        dict(set="storm", cast=[("kaela", (0, 30, 0), 0, "Running_A", {"walk": (3.2, (1, -1))})],
             extra=lambda S, r: sets.bounded_fog(),
             cam=[aim(0, (2.4, -4, 0.9), (0, 20, 1.5)), aim(15.5, (2.0, -4, 0.9), (0, -2, 1.3))], lens=50, focus="kaela"),
        # Kaela reining in beside the towers, looking back. Joins as a hero.
        dict(set="storm", cast=[("kaela", (0, 0, 0), -20, "Idle")], extra=lambda S, r: towers(S, col=TEAL),
             cam=[aim(0, (1.6, -3.6, 1.7), (0, 0, 1.6)), aim(11, (1.1, -2.9, 1.7), (0, 0, 1.65))], lens=50, focus="kaela"),
    ],
    "storm_warden": [
        # The black cloud shattering, frozen lightning falling like glass.
        dict(set="storm", cast=[("thunderhead", (0, 22, 0), 0, "Death_A", {"at": 1.5, "scale": 4.0})],
             extra=lambda S, r: shards(S, (0, 14, 0), n=220, top=30, spread=14, over=11.0),
             cam=[aim(0, (-3, -6, 0.8), (0, 22, 12)), aim(18.7, (-2, -4, 0.7), (0, 22, 7))], lens=24),
        # Aurath, a rider-shape of cloud and lightning, bowing over the towers.
        dict(set="storm", cast=[("aurath", (0, 3, 0), 0, "Idle")], extra=lambda S, r: towers(S, ((-7, 6), (6, 8)), TEAL),
             cam=[aim(0, (1.5, -3.5, 0.9), (0, 3, 2.6)), aim(15.6, (1.0, -2.6, 0.9), (0, 3, 2.7))], lens=35, focus="aurath"),
        # Galeborn raising their tents again; Kaela watching.
        dict(set="storm", cast=[("kaela", (0, 0, 0), 180, "Idle")], extra=lambda S, r: stones(S, (8, 34, 0)),
             cam=[aim(0, (1.2, -4, 1.8), (2, 30, 2)), aim(14.3, (0.6, -3.2, 1.8), (2, 30, 2.5))], lens=35, focus="kaela"),
    ],
}
