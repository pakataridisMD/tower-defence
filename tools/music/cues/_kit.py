"""Shared orchestra seating and themes for every cue (see tools/music/themes.md)."""
from score import Score


def seat(s: Score) -> Score:
    """Standard orchestra: pans roughly follow a concert stage, gains balance the sample sets."""
    t = s.track
    t("vln", pan=-0.45, attack=0.08, legato=1.06, release=0.6, gain_db=-1)
    t("vln2", inst="vln", pan=-0.2, attack=0.12, legato=1.06, release=0.6, gain_db=-4)
    t("vln_trem", pan=-0.3, attack=0.4, release=0.8, gain_db=-8)
    t("vla", pan=0.15, attack=0.12, legato=1.05, release=0.6, gain_db=-4)
    t("vla_trem", pan=0.15, attack=0.3, release=0.8, gain_db=-10)
    t("vc", pan=0.35, attack=0.1, legato=1.05, release=0.6, gain_db=-2)
    t("vc_solo", inst="vc", pan=0.2, attack=0.09, legato=1.08, release=0.7, gain_db=0)
    t("vc_trem", pan=0.35, attack=0.3, release=0.8, gain_db=-8)
    t("cb", pan=0.5, attack=0.12, double=1, release=0.6, gain_db=-3, hpf=36)
    t("vla_spic", pan=0.15, gain_db=-12)
    t("vc_spic", pan=0.35, gain_db=-9)
    t("cb_spic", pan=0.5, gain_db=-10, hpf=36)
    t("vln_pizz", pan=-0.4, gain_db=-8)
    t("vc_pizz", pan=0.35, gain_db=-8)
    t("solo_vln", pan=-0.2, attack=0.15, legato=1.06, release=0.9, gain_db=-4)
    t("fl", pan=-0.25, attack=0.05, legato=1.04, gain_db=-4)
    t("ob", pan=-0.1, attack=0.05, legato=1.04, gain_db=-6)
    t("cl", pan=0.1, attack=0.08, legato=1.04, gain_db=-6)
    t("bsn", pan=0.25, attack=0.06, gain_db=-5)
    t("hn", pan=-0.2, attack=0.07, legato=1.04, release=0.5, gain_db=-5)
    t("hn_solo", inst="hn", pan=-0.1, attack=0.06, legato=1.05, release=0.5, gain_db=2)
    t("tpt", pan=0.1, attack=0.03, legato=1.03, gain_db=-5)
    t("tpt_solo", inst="tpt", pan=0.05, attack=0.05, legato=1.04, release=0.6, gain_db=-2)
    t("tbn", pan=0.3, attack=0.05, legato=1.03, gain_db=-5)
    t("tuba", pan=0.45, attack=0.05, legato=1.03, gain_db=-5)
    t("harp", pan=-0.55, gain_db=-10)
    t("celesta", pan=-0.35, gain_db=-6)
    t("bells", pan=0.3, gain_db=-10)
    t("glock", pan=-0.4, gain_db=-12)
    t("choir", pan=0.0, legato=1.05, gain_db=-11)
    t("choir_hi", inst="choir", pan=-0.1, gain_db=-12)
    t("oohs", pan=0.05, gain_db=-7)
    return s


def new(name: str, title: str) -> Score:
    return seat(Score(name, title))


# ---------------------------------------------------------------- themes (in D, transpose as needed)
# The Lantern: hope, the Order of the Spire, Oswin. 8 bars of 4/4.
LANTERN_A = "D4:2 A4:2 | G4:1.5 F#4:.5 E4 D4 | B3:2 E4 F#4 | E4:4"
LANTERN_B = "D4:2 A4:2 | B4:1.5 A4:.5 G4 F#4 | G4:1.5 F#4:.5 E4 C#4 | D4:4"
# The Lantern in the minor (the Long Defeat)
DEFEAT_A = "D4:2 A4:2 | G4:1.5 F4:.5 E4 D4 | Bb3:2 E4 F4 | E4:4"
DEFEAT_B = "D4:2 A4:2 | Bb4:1.5 A4:.5 G4 F4 | G4:1.5 F4:.5 E4 C#4 | D4:4"
# The Hollow: Vael-Orrun's falling tritone, 5/4
HOLLOW = "D4:3 Ab3:2 | G3:1.5 Bb3:.5 A3:1 Eb4:2 | D4:3 C4:1 Bb3:1 | A3:3 Ab3:2"
HOLLOW_OST = "D3:.5> D3:.5 D3:.5 D3:.5> D3:.5 Eb3:.5 D3:.5> D3:.5 C3:.5> Ab2:.5"
# Solenne: the home tune, 6/8 written as three quarter beats per bar, in F
SOLENNE = ("F5:1 G5:.5 A5:1 C6:.5 | D6:1.5 C6:1 A5:.5 | G5:1 A5:.5 F5:1 D5:.5 | C5:1.5 F5:1 G5:.5 | "
           "A5:1 C6:.5 D6:1 F6:.5 | E6:1.5 D6:1 C6:.5 | D6:1 C6:.5 A5:1 G5:.5 | F5:3")


def rep(text: str, n: int) -> str:
    return " | ".join([text] * n)
