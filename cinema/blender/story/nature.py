"""The Verdant Deep: nature_intro, nature_herald, nature_warden."""
import hero
from story.kit import aim, glow_moss, hand_glow, towers

GREEN = (0.4, 1.0, 0.5)


def vesper_choir(S, rigs, who="vesper"):
    hero.wisps(rigs[who], 1.4, n=9, radius=1.4, energy=10)


SHOTS = {
    "nature_intro": [
        # Giant trees, glow-moss lighting the roots like streets, a Deepwood archer on watch.
        dict(set="nature", cast=[("sylvaine", (3, 8, 0), 200, "2H_Ranged_Aiming")], extra=lambda S, r: glow_moss(S),
             cam=[aim(0, (-6, -14, 1.2), (2, 20, 6)), aim(16.8, (-2, -9, 1.6), (2, 20, 5))], lens=24),
        # The glow-moss going dark row by row; ghost-lights; the Pale Vesper singing.
        dict(set="nature", cast=[("vesper", (0, 12, 0), 0, "Walking_A", {"walk": (0.35, (1, -1))})],
             extra=lambda S, r: (glow_moss(S, dark_from=3.0), vesper_choir(S, r)),
             cam=[aim(0, (2, -6, 1.4), (0, 12, 1.8)), aim(22.3, (1.2, -2.5, 1.5), (0, 4.5, 1.9))], lens=40, focus="vesper"),
        # Tamsin at the edge of a root-road, lantern-pole raised.
        dict(set="nature", cast=[("tamsin", (0, 0, 0), -15, "Idle")], extra=lambda S, r: glow_moss(S, depth=(3, 20)),
             cam=[aim(0, (1.4, -3.6, 1.6), (0, 0, 1.6)), aim(11.9, (1.0, -3.0, 1.6), (0, 0, 1.65))], lens=45, focus="tamsin"),
    ],
    "nature_herald": [
        # The Pale Vesper falling among the roots, her ghost-choir scattering.
        dict(set="nature", cast=[("vesper", (0, 5, 0), 0, "Death_A", {"at": 3.0})], extra=lambda S, r: (glow_moss(S), vesper_choir(S, r)),
             cam=[aim(0, (4, -4, 1.6), (0, 5, 1.2)), aim(20.3, (3, -2.5, 1.2), (0, 5, 0.6))], lens=35, focus="vesper"),
        # Close on the Vesper's face; for a moment she looks like herself.
        dict(set="nature", cast=[("vesper", (0, 0, 0), 0, "Idle", {"soft": 0.4})],
             cam=[aim(0, (0.5, -1.8, 1.62), (0, 0, 1.62)), aim(12.4, (0.35, -1.4, 1.62), (0, 0, 1.64))], lens=65, fstop=2.0,
             focus="vesper"),
        # Ysolde reading a messenger's report, then folding it away.
        dict(set="solenne", set_args=dict(night=True), mark="square", key=60, cast=[("ysolde", (0, 0, 0), 0, "Use_Item")],
             cam=[aim(0, (1.2, -2.8, 1.6), (0, 0, 1.5)), aim(11.3, (0.9, -2.3, 1.6), (0, 0, 1.55))], lens=50, focus="ysolde"),
        # Sylvaine in a ring of fallen hollow things, lowering her bow.
        dict(set="nature", cast=[("sylvaine", (0, 0, 0), -10, "2H_Ranged_Aiming", {"soft": 0.5})],
             extra=lambda S, r: glow_moss(S, depth=(2, 24)),
             cam=[aim(0, (3, -5, 1.0), (0, 0, 1.4)), aim(14.4, (2.0, -3.6, 1.2), (0, 0, 1.5))], lens=40, focus="sylvaine"),
        # Sylvaine at the edge of a tower platform, arrow on the string. Joins as a hero.
        dict(set="nature", cast=[("sylvaine", (0, 0, 0), -20, "2H_Ranged_Aiming")], extra=lambda S, r: towers(S, col=GREEN),
             cam=[aim(0, (1.5, -3.2, 1.7), (0, 0, 1.6)), aim(9.6, (1.1, -2.7, 1.7), (0, 0, 1.6))], lens=50, focus="sylvaine"),
    ],
    "nature_warden": [
        # The Broodmother collapsing inside the oldest tree.
        dict(set="nature", cast=[("broodmother", (0, 4, 0), 0, "Death_A", {"at": 2.5})],
             cam=[aim(0, (4, -5, 1.0), (0, 4, 2.4)), aim(20.3, (3, -3.5, 0.9), (0, 4, 1.0))], lens=30, focus="broodmother"),
        # Elowen pressing a single glowing seed into Sylvaine's hand.
        dict(set="nature", cast=[("elowen", (0, 1.2, 0), 0, "Interact"), ("sylvaine", (0.2, -0.6, 0), 180, "Idle")],
             extra=lambda S, r: hand_glow(r, "elowen"),
             cam=[aim(0, (2.6, -1.0, 1.7), (0, 0.4, 1.9)), aim(13.4, (2.2, -0.6, 1.7), (0, 0.4, 1.9))], lens=40, focus="elowen"),
        # The glow-moss lighting again; the army on the road west.
        dict(set="nature", cast=[("sylvaine", (0, 0, 0), 90, "Walking_A", {"walk": (0.9, (0, 1))}),
                                 ("tamsin", (1.6, 0.6, 0), 90, "Walking_A", {"walk": (0.9, (0, 1)), "phase": 0.3}),
                                 ("fennick", (3.2, -0.2, 0), 90, "Walking_A", {"walk": (0.9, (0, 1)), "phase": 0.6})],
             extra=lambda S, r: glow_moss(S, light_from=0.5),
             cam=[aim(0, (-4, -8, 2.0), (1, 0, 1.2)), aim(12.5, (-12, -8, 2.4), (-9, 0, 1.2))], lens=32),
    ],
}
