"""The main story (everything that is not one land's intro, herald or warden film): the prologue, the night Solenne
fell, the long night, the march on Solenne, the dawn, the Hollow and the truth, and the epilogue.

Shot n of a film is SHOTS[film][n - 1]; most cameras use kit.push / kit.drift, whose key times run 0..1 over the
shot. `reuse` shots come from the trailer renders (shots/sNN_*.py); `montage` shots are cut from other films' shots.
Vael-Orrun's monster form is not built yet: until it is, the Keeper (his human memory) stands in, scaled up."""
import hero
from story.kit import aim, push, drift, doors, darkness, sundered_heart, falling_stars, hand_glow, shards, towers, silent, glow_moss
from story.void import ring_map

if "vael_orrun" not in hero.HUMANS:   # stand-in until the demon king is modelled
    hero.HUMANS["vael_orrun"] = hero.HUMANS["keeper"]; hero.SCALE["vael_orrun"] = 2.3

SIX = ["ignar", "aurath", "elowen", "thalassa", "orrok", "nyxara"]
KINGS = ["ignar_king", "aurath_king", "elowen_queen", "thalassa_queen", "orrok_king", "nyxara_queen"]
WHITE = (0.95, 0.95, 1.0)


def ring_of(names, r=4.0, centre=(0, 6, 0), facing_in=True):
    """Cast entries standing in a ring round a point (the dais), each facing it."""
    import math
    out = []
    for k, who in enumerate(names):
        a = math.radians(-90 + 360 * k / len(names) + 30)
        x, y = centre[0] + math.cos(a) * r, centre[1] + math.sin(a) * r
        face = math.degrees(a) + (90 if facing_in else -90)
        out.append((who, (x, y, centre[2]), face, "Idle", {"phase": k * 0.17}))
    return out


def line_of(names, y=0.0, gap=3.2, face=0, action="Idle"):
    n = len(names)
    return [(w, ((k - (n - 1) / 2) * gap, y, 0), face, action, {"phase": k * 0.13}) for k, w in enumerate(names)]


def marching(names, y=0.0, gap=2.0, speed=1.0, face=0):
    """A line abreast walking the way it faces: 0 = toward the camera (-Y), 90 = +X, 180 = +Y, -90 = -X."""
    axis = {0: (1, -1), 90: (0, 1), 180: (1, 1), -90: (0, -1)}[face]
    return [(w, p, f, "Walking_A", dict(o, walk=(speed, axis))) for w, p, f, a, o in line_of(names, y, gap, face)]


SOLENNE_NIGHT = dict(set="solenne", set_args=dict(night=True), key=50)
SOLENNE_DAWN = dict(set="solenne", set_args=dict(night=False, sun_lit=1.0))
HALL = dict(set="hall")
THRONE = dict(set="hall", set_args=dict(ruined=True))
HOLLOW = dict(set="hollow")


def S(base, **kw):
    d = dict(base); d.update(kw); return d


SHOTS = {
    "prologue": [
        S(HALL, set_args=dict(heart=False), extra=lambda S_, r: ring_map(S_, r, lit_every=1.6),
          **drift((0, -0.6, 4.2), (0, -0.4, 3.2), (0, 0, 0.95), lens=35)),
        S(dict(set="ember"), cast=[("vael_orrun", (0, 14, 0), 0, "Walking_A", {"walk": (0.6, (1, -1))})],
          **drift((6, -10, 1.5), (4, -7, 1.6), (0, 10, 3.5), (0, 6, 3.5), lens=32, focus="vael_orrun")),
        dict(reuse="s02_gate_shut"),
        S(HALL, cast=ring_of(KINGS), **drift((0, -6, 3.6), (0, -3, 3.0), (0, 6, 1.8), lens=28)),
        S(SOLENNE_DAWN, cam="aerial", lens=30),
        S(SOLENNE_NIGHT, mark="inner_wall", cast=[("cassivane", (0, 0, 0), 200, "Use_Item")],
          **push((0, 0, 1.7), (3.0, 2.4), side=-0.5, lens=50, focus="cassivane")),
        dict(reuse="s03_gate_opens"),
        dict(reuse="s05_oswin"),
        dict(reuse="s06_fall"),
        dict(reuse="s07_unbound"),
        dict(montage=["ember_intro_2", "storm_intro_2", "nature_intro_2", "water_intro_2", "earth_intro_2", "void_intro_3"]),
        dict(reuse="s09_queen"),
    ],
    "regents_counsel": [
        S(SOLENNE_NIGHT, set_args=dict(night=False), mark="square", cast=line_of(["tamsin", "brannoc", "fennick"], y=6, gap=4),
          **drift((-8, -10, 4), (-4, -8, 3), (0, 6, 1.5), lens=30)),
        S(SOLENNE_NIGHT, set_args=dict(night=False), mark="gate", cast=[("cassivane", (0, 0, 0), -10, "Interact"),
                                                                        ("fennick", (1.8, 0.6, 0), -40, "Idle")],
          **drift((3, -5, 1.7), (2.2, -4, 1.7), (0.8, 0, 1.5), lens=40, focus="cassivane")),
        S(SOLENNE_NIGHT, set_args=dict(night=False), mark="square", cast=[("cassivane", (0, 0, 0), -5, "Idle")],
          **push((0, 0, 1.75), (2.4, 1.9), side=0.2, lens=55, focus="cassivane")),
        S(SOLENNE_NIGHT, mark="spire", cast=[("cassivane", (0, 0, 0), 180, "Use_Item")],
          **drift((3, -3, 2.0), (2.4, -2.4, 2.0), (0, 0, 1.6), lens=40, focus="cassivane")),
    ],
    "night_of_falling_stars": [
        S(SOLENNE_NIGHT, cam="aerial", lens=30),
        S(SOLENNE_NIGHT, mark="gate", extra=lambda S_, r: doors(S_, y=0, half=5, h=11, t0=2, t1=12, opening=True, rgb=(0.2, 0.13, 0.08)),
          **drift((0, 22, 2.0), (0, 16, 2.0), (0, 0, 4), lens=30)),
        S(SOLENNE_NIGHT, mark="square", cast=[("tamsin", (0, 0, 0), 20, "1H_Melee_Attack_Chop"), ("brannoc", (2.2, 1.5, 0), -30, "2H_Melee_Attack_Chop")],
          **drift((4, -6, 1.8), (2, -5, 1.6), (1, 0, 1.4), lens=32)),
        S(SOLENNE_NIGHT, mark="gate", cast=[("fennick", (0, 10, 0), 170, "Interact")], extra=lambda S_, r: towers(S_, ((-5, 14), (5, 15)), (1, 0.6, 0.3)),
          **push((0, 10, 1.4), (3.0, 2.4), side=0.5, lens=40, focus="fennick")),
        S(SOLENNE_NIGHT, mark="gate", cast=[("fennick", (0, 10, 0), 200, "Cheer")],
          **push((0, 10, 1.45), (2.2, 1.8), side=-0.3, lens=50, focus="fennick")),
        S(SOLENNE_NIGHT, mark="gate", extra=lambda S_, r: shards(S_, (0, 8, 0), n=90, top=16, spread=6, start=0.8, rgb=(0.6, 0.58, 0.55)),
          **drift((6, 30, 3), (5, 28, 3), (0, 8, 5), lens=30)),
        S(SOLENNE_NIGHT, mark="spire", cast=[("cassivane", (0, 0, 0), 180, "2H_Melee_Attack_Chop")],
          extra=lambda S_, r: falling_stars(S_, start=6.0), **drift((5, -6, -1), (4, -5, -0.5), (0, 0, 4), lens=26, focus="cassivane")),
        S(HALL, mark="door", cast=[("cassivane", (0, 0, 0), 180, "Walking_A", {"walk": (0.9, (1, 1))})],
          extra=lambda S_, r: hand_glow(r, "cassivane", (1, 0.85, 0.6), 60),
          **drift((2, -3, 1.6), (1.5, 2, 1.8), (0, 4, 1.5), (0, 14, 1.5), lens=32, focus="cassivane")),
        S(HALL, mark="dais", cast=[("ysolde", (0, -2, -0.9), 0, "Running_A", {"walk": (2.6, (1, -1))})],
          extra=lambda S_, r: (hand_glow(r, "ysolde", (1, 0.9, 0.8), 80), falling_stars(S_, 12, start=3.0)),
          **drift((1.5, -6, 1.5), (1.5, -18, 1.5), (0, -2, 1.3), (0, -16, 1.3), lens=35, focus="ysolde")),
        S(SOLENNE_NIGHT, mark="square", cast=[("cassivane", (0, 2, 0), 0, "Interact"), ("tamsin", (-1.6, -1.4, 0), 120, "Idle"),
                                              ("ysolde", (-2.3, -1.8, 0), 120, "Idle")],
          **drift((2.5, -4, 1.6), (2.0, -3.4, 1.6), (0, 2, 1.7), lens=40, focus="cassivane")),
        S(SOLENNE_NIGHT, mark="gate", cast=[("cassivane", (0, 6, 0), 0, "Walking_A", {"walk": (0.9, (1, -1))})],
          extra=lambda S_, r: hand_glow(r, "cassivane", (1, 0.85, 0.6), 80, size=0.09),
          **drift((0, 14, 2.0), (0, 12, 2.2), (0, 0, 1.6), (0, -10, 1.6), lens=35, focus="cassivane")),
        S(SOLENNE_NIGHT, set_args=dict(night=False), cam="wall", extra=lambda S_, r: darkness(S_), lens=24),
    ],
    "long_night": [
        S(SOLENNE_NIGHT, mark="square", cast=line_of(["tamsin", "fennick", "brannoc"], y=8, gap=3, face=10),
          **drift((-6, -8, 4), (-3, -6, 3), (0, 6, 1.4), lens=30)),
        S(HALL, mark="dais", cast=[("ysolde_blind", (0, 0, 0), 0, "Sit_Chair_Idle")],
          **push((0, 0, 1.3), (3.2, 2.6), side=0.2, lens=45, focus="ysolde_blind")),
        S(HALL, cast=[("tamsin", (0, 0, 0), 0, "Use_Item")],
          extra=lambda S_, r: hand_glow(r, "tamsin", (1, 0.75, 0.4), 30, size=0.02),
          **push((0, 0, 1.4), (2.4, 1.9), side=0.4, lens=50, focus="tamsin")),
        S(dict(set="storm", set_args=dict(lightning=False)), cast=marching(["tamsin", "kaela", "brannoc", "gorrim"], gap=2.5, face=90),
          extra=lambda S_, r: towers(S_, ((-12, 8), (10, 10)), (0.9, 0.7, 0.4)),
          **drift((-6, -14, 3), (-2, -12, 3), (0, 0, 1.4), lens=30)),
    ],
    "lumen_gate": [
        S(SOLENNE_NIGHT, cam="aerial", lens=24),
        S(SOLENNE_NIGHT, mark="gate", extra=lambda S_, r: shards(S_, (0, 0, 0), n=140, top=18, spread=14, start=0.6, rgb=(0.8, 0.78, 0.74)),
          **drift((10, -30, 4), (8, -26, 4), (0, 0, 7), lens=30)),
        S(SOLENNE_NIGHT, mark="gate", cast=[("seraphel", (0, 4, 0), -10, "2H_Melee_Idle")],
          **push((0, 4, 1.8), (4.0, 3.0), side=0.4, lens=40, focus="seraphel")),
        S(SOLENNE_NIGHT, mark="inner_wall", cast=[("seraphel", (0, 0, 0), -10, "2H_Melee_Idle"), ("ysolde_blind", (-1.6, 0.6, 0), -10, "Idle")],
          **push((-0.6, 0, 1.7), (3.4, 2.8), side=0.5, lens=40, focus="seraphel")),
    ],
    "convergence_intro": [
        S(HALL, set_args=dict(heart=False), extra=lambda S_, r: ring_map(S_, r, lit_every=0.4),
          **drift((0, -0.5, 3.6), (0, -0.3, 3.0), (0, 0, 0.95), lens=35)),
        S(dict(set="storm", set_args=dict(lightning=False)), cast=marching(["tamsin", "kaela", "brannoc"], gap=2.5, face=90),
          **drift((-30, -40, 14), (-20, -34, 12), (0, 20, 0), lens=24)),
        S(dict(set="storm", set_args=dict(lightning=False)), cast=marching(SIX, y=10, gap=7, face=90, speed=1.3),
          **drift((-6, -8, 1.0), (-2, -6, 1.0), (0, 10, 4), lens=24)),
        S(SOLENNE_NIGHT, mark="gate", cast=[("thalassa", (0, 4, 0), 180, "Interact"), ("ysolde_blind", (0, 1.4, 0), 0, "Idle")],
          **drift((3.5, 0, 1.4), (3.0, 0.6, 1.4), (0, 2.5, 2.2), lens=32, focus="ysolde_blind")),
        S(dict(set="storm", set_args=dict(lightning=False)), extra=lambda S_, r: towers(S_, ((-10, 30), (12, 34), (0, 40)), (0.6, 0.6, 0.65)),
          **drift((0, -20, 8), (6, -16, 7), (0, 30, 2), lens=28)),
    ],
    "crossroads": [
        S(dict(set="ember"), cast=[("cassivane_ash", (0, 4, 0), 180, "Walking_Backwards")],
          **drift((3, -3, 1.6), (2.4, -1.5, 1.6), (0, 4, 1.5), (0, 6, 1.5), lens=35, focus="cassivane_ash")),
        S(dict(set="ember"), cast=[("cassivane_ash", (0, 0, 0), -20, "Interact")],
          **push((0, 0, 1.75), (2.6, 2.0), side=0.3, lens=50, focus="cassivane_ash")),
        S(dict(set="void"), cast=[("corvin", (1.2, 1.0, 0), 60, "1H_Melee_Attack_Slice_Diagonal"), ("ilyra", (0, 1.4, 0), -20, "Sit_Floor_Idle")],
          **drift((2, -3.4, 1.2), (1.4, -2.6, 1.1), (0.4, 1.2, 0.9), lens=40, focus="ilyra")),
        S(dict(set="void"), cast=[("corvin", (0.7, 0, 0), -60, "Sit_Floor_Idle"), ("ilyra", (-0.4, 0.2, 0), 50, "Sit_Floor_Idle")],
          extra=lambda S_, r: hand_glow(r, "corvin", (1, 0.5, 0.2), 120, size=0.01),
          **drift((0.4, -3, 1.0), (0.2, -2.4, 0.95), (0.1, 0.1, 0.7), lens=45)),
        S(dict(set="void"), cast=[("ilyra", (0, 0, 0), -10, "Idle")], extra=lambda S_, r: towers(S_, col=(0.7, 0.45, 1.0)),
          **push((0, 0, 1.6), (2.6, 2.0), side=0.4, lens=50, focus="ilyra")),
    ],
    "capital_prelude": [
        S(SOLENNE_NIGHT, cam="aerial", lens=28),
        S(dict(set="storm", set_args=dict(lightning=False)), cast=[("cassivane_ash", (0, 20, 3), 0, "Idle")],
          extra=lambda S_, r: sundered_heart(r, r=3.0), **drift((0, -6, 1.0), (2, -4, 1.0), (0, 20, 5), lens=30)),
        S(SOLENNE_NIGHT, mark="inner_wall", cast=[("ysolde_blind", (0, 0, 0), 0, "Idle"), ("tamsin", (1.0, 0.4, 0), -10, "Idle")],
          **drift((2.6, -3.4, 1.4), (2.0, -2.8, 1.5), (0.4, 0, 1.6), lens=40, focus="ysolde_blind")),
        S(SOLENNE_NIGHT, mark="inner_wall", cast=[("ysolde_blind", (0, 0, 0), 80, "Idle"), ("tamsin", (-0.8, 0.6, 0), 80, "Idle")],
          **push((0, 0, 1.6), (2.2, 1.8), side=-0.6, lens=55, focus="ysolde_blind")),
    ],
    "dawn": [
        S(SOLENNE_NIGHT, cam="wall", lens=40),
        S(SOLENNE_NIGHT, mark="gate", cast=[("oswin", (0, -30, 0), 0, "Walking_A", {"walk": (0.9, (1, 1))})],
          **drift((2, 4, 1.2), (2, 2, 1.2), (0, -30, 1.8), (0, -18, 1.8), lens=50, focus="oswin")),
        S(SOLENNE_NIGHT, mark="gate", cast=[("oswin", (0, 0, 0), -10, "Use_Item")],
          extra=lambda S_, r: hand_glow(r, "oswin", WHITE, 120, size=0.07),
          **push((0, 0, 1.7), (3.0, 2.4), side=0.3, lift=-0.4, lens=45, focus="oswin")),
        S(SOLENNE_DAWN, mark="spire", cast=[("oswin", (0, 0, 0), 180, "Spellcast_Raise")],
          **drift((4, -6, 1.0), (3, -5, 1.4), (0, 0, 2.0), (0, 2, 5), lens=28, focus="oswin")),
        S(SOLENNE_DAWN, cam="aerial", lens=26),
    ],
    "heart_falls": [
        S(dict(set="storm", set_args=dict(lightning=False)), cast=[("cassivane_ash", (0, 0, 0), 0, "Idle")],
          extra=lambda S_, r: sundered_heart(r, n=30), **drift((3, -4, 1.2), (2, -3, 1.0), (0, 0, 0.9), lens=40, focus="cassivane_ash")),
        S(dict(set="storm", set_args=dict(lightning=False)), cast=[("cassivane_ash", (0, 0.6, 0), 0, "Idle"), ("ilyra", (0, -0.4, 0), 180, "Sit_Floor_Idle")],
          **drift((1.6, -1.4, 1.0), (1.3, -1.1, 1.0), (0, 0.2, 0.9), lens=45, focus="ilyra")),
        S(dict(set="storm", set_args=dict(lightning=False)), cast=[("cassivane_ash", (0, 0, 0), 0, "Idle")],
          extra=lambda S_, r: hand_glow(r, "cassivane_ash", (1, 0.8, 0.4), 15, size=0.025),
          **push((0, 0, 1.7), (2.2, 1.7), side=0.2, lens=65, fstop=2.0, focus="cassivane_ash")),
        S(SOLENNE_DAWN, mark="inner_wall", cast=[("ysolde_blind", (0, 0, 0), 0, "Idle")],
          **push((0, 0, 1.65), (2.4, 1.9), side=0.3, lens=55, focus="ysolde_blind")),
        S(HALL, mark="dais", cast=[("oswin", (0, -2.2, -0.9), 30, "Idle"), ("corvin", (-1.8, -2.6, -0.9), 10, "Idle"), ("tamsin", (1.8, -2.8, -0.9), -10, "Idle")],
          **drift((0, -8, 2.0), (0, -6.5, 1.9), (0, -1, 1.2), lens=32)),
        S(SOLENNE_DAWN, mark="gate", cast=marching(["tamsin", "kaela", "brannoc", "gorrim", "sylvaine", "mirelle"], y=6, gap=1.8),
          **drift((5, -14, 1.5), (4, -12, 1.5), (0, 0, 1.6), lens=35)),
    ],
    "assault_intro": [
        S(dict(set="rift"), **drift((0, 10, 40), (0, 0, 34), (0, -95, 2), lens=30)),
        S(HOLLOW, cam="wide", lens=24),
        S(HOLLOW, cast=line_of(["tamsin", "kaela", "brannoc"], y=4, gap=2.4, face=180), extra=lambda S_, r: towers(S_, ((-8, 8), (8, 10)), (0.9, 0.7, 0.4)),
          **drift((-6, -6, 4), (-3, -5, 3), (0, 20, 3), lens=28)),
        S(HOLLOW, mark="gate", cast=[("vael_orrun", (0, 2, 24), 0, "Idle")], **drift((0, -40, 4), (0, -34, 4), (0, 0, 20), lens=28)),
        S(HOLLOW, cast=[("tamsin", (0, 0, 0), 0, "Cheer")], **push((0, 0, 1.6), (2.6, 2.0), side=0.4, lens=50, focus="tamsin")),
    ],
    "the_turning": [
        S(HOLLOW, mark="gate", cast=[("vael_orrun", (0, -6, 0), 180, "Running_A", {"walk": (2.5, (1, 1))})],
          **drift((8, -26, 3), (6, -22, 3), (0, -6, 4), (0, 0, 6), lens=28)),
        S(HOLLOW, cast=[("brannoc", (0, 0, 0), 180, "Walking_A", {"walk": (0.8, (1, 1))})],
          **drift((1.8, -3, 1.4), (1.8, -1, 1.4), (0, 0, 1.4), (0, 5, 1.6), lens=40, focus="brannoc")),
    ],
    "the_high_king": [
        S(HOLLOW, mark="gate", cast=[("vael_orrun", (0, 0, 0), 0, "Walking_A", {"walk": (0.5, (1, -1))})],
          **drift((3, -14, 1.0), (2.5, -12, 1.0), (0, 0, 3), lens=28, focus="vael_orrun")),
        S(HOLLOW, mark="gate", cast=[("vael_orrun", (0, 0, 0), -40, "Idle")], **push((0, 0, 3.8), (6, 4.8), side=0.3, lift=-0.8, lens=40)),
        S(HOLLOW, mark="gate", cast=line_of(SIX, y=-12, gap=6, face=180), **drift((0, -30, 3), (0, -28, 3), (0, -12, 3.5), lens=26)),
    ],
    "the_truth": [
        S(HOLLOW, mark="gate", cast=[("seraphel_grey", (0, 0, 0), 0, "Blocking")], **push((0, 0, 1.7), (4, 3), side=0.4, lens=40, focus="seraphel_grey")),
        S(HOLLOW, mark="gate", cast=[("seraphel_grey", (0, 0, 0), 0, "Idle")], **push((0, 0, 1.0), (1.8, 1.4), side=0.3, lens=60, focus="seraphel_grey")),
        S(THRONE, cast=[("vael_orrun", (0, 6, 0), 0, "Idle")], **drift((4, -6, 2), (3, -4, 1.8), (0, 6, 2.5), lens=30)),
        S(THRONE, cast=[("vael_orrun", (0, 6, 0), 0, "Idle")] + ring_of(SIX, r=6.5, centre=(0, 6, 0)),
          **drift((0, -8, 4), (0, -6, 3.5), (0, 6, 2), lens=26)),
        S(HALL, cast=[("keeper", (0, 4, 0), 0, "Sit_Chair_Idle")] + line_of(KINGS[:3], y=6, gap=2, face=0)
          + [(w, (x + 0.0, y, z), f, a, o) for w, (x, y, z), f, a, o in line_of(KINGS[3:], y=2, gap=2, face=180)],
          **drift((5, -4, 2.4), (4, -3, 2.2), (0, 4, 1.4), lens=30)),
        S(THRONE, cast=[("keeper", (0, 2, 0), 0, "Idle")], extra=lambda S_, r: hand_glow(r, "keeper", (1, 0.85, 0.5), 10, size=0.012),
          **drift((3, -3, 1.4), (2, -2, 1.2), (0, 2, 0.9), lens=40, focus="keeper")),
        S(THRONE, cast=[("ignar", (0, 0, 0), 0, "Idle")], **push((0, 0, 3.1), (4.0, 3.2), side=0.4, lift=-0.4, lens=40, focus="ignar")),
        S(THRONE, cast=[("vael_orrun", (0, 0, 0), 0, "Idle")], **push((0, 0, 3.9), (6.0, 5.0), side=0.3, lift=-1.2, lens=40)),
        S(THRONE, cast=[("thalassa", (0, 0, 0), 0, "Idle")], **push((0, 0, 3.1), (3.6, 3.0), side=-0.3, lift=-0.3, lens=45, focus="thalassa")),
        S(THRONE, cast=[("vael_orrun", (0, 0, 0), 0, "Idle")], **push((0, 0, 3.9), (4.5, 3.6), side=0.0, lift=-1.0, lens=50)),
        S(THRONE, cast=[("mirelle", (0, 0, 0), -10, "Idle")], **push((0, 0, 1.45), (2.2, 1.8), side=0.4, lens=55, focus="mirelle")),
        S(THRONE, cast=[("vael_orrun", (0, 2, 0), 0, "Idle"), ("oswin", (0.4, 0.4, 0), 20, "Interact")],
          extra=lambda S_, r: hand_glow(r, "oswin", WHITE, 300, size=0.07), **drift((4, -3, 2), (3, -2, 2.2), (0, 1.5, 2.0), lens=32)),
        S(HALL, set_args=dict(dawn=True), **drift((0, -10, 2), (0, -8, 2.4), (0, 6, 3), (0, 6, 5), lens=28)),
    ],
    "the_hush": [
        silent(5.0),
        S(THRONE, cast=[("keeper", (0, 0, 0), 0, "Idle")], extra=lambda S_, r: hand_glow(r, "keeper", (1, 0.85, 0.5), 5, size=0.012),
          **push((0, 0, 1.65), (2.6, 2.0), side=0.2, lens=55, focus="keeper")),
        S(dict(set="rift"), cast=[("vael_orrun", (0, -92, 0), 0, "Idle")],
          **push((0, -92, 3.8), (5, 4), side=0.5, lens=40)),
        S(dict(set="rift"), extra=lambda S_, r: falling_stars(S_, 1, start=0.5), **drift((0, -40, 10), (0, -30, 30), (0, -60, 20), (0, 0, 60), lens=24)),
        S(HALL, cast=[("ilyra", (0, 3.6, 0), 180, "Idle")], **push((0, 3.6, 1.6), (1.6, 1.2), side=0.1, lens=65, fstop=2.0, focus="ilyra")),
        silent(4.0),
        S(dict(set="void"), seconds=10.0, cam=[aim(0, (0, -6, 2), (0, 30, 2))], lens=35),
    ],
    "solenne_falls": [
        S(SOLENNE_NIGHT, mark="inner_wall", extra=lambda S_, r: shards(S_, (0, 0, 0), n=60, top=12, spread=8, start=1.0, rgb=(0.8, 0.78, 0.74)),
          **drift((10, -18, 3), (8, -15, 3), (0, 0, 4), lens=30)),
    ],
    "epilogue": [
        S(dict(set="rift"), cast=line_of(SIX, y=-80, gap=7, face=180), **drift((0, -40, 6), (0, -46, 5), (0, -90, 6), lens=26)),
        dict(montage=["ember_warden_3", "storm_warden_3", "water_warden_3", "earth_warden_3", "void_intro_1", "nature_warden_3"]),
        S(SOLENNE_DAWN, mark="gate", cast=[("tamsin", (0, 0, 0), 0, "Sit_Floor_Idle"), ("oswin", (1.2, 0.4, 0), -20, "Idle")],
          **drift((2.4, -4, 1.4), (1.8, -3.2, 1.4), (0.5, 0, 1.0), lens=40, focus="tamsin")),
        S(SOLENNE_DAWN, mark="east_wall", cast=[("ysolde_blind", (0, 0, 0), 0, "Idle")],
          **push((0, 0, 1.6), (3.0, 2.0), side=0.4, lens=50, focus="ysolde_blind")),
    ],
}
