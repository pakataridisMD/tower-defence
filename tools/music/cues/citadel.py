"""The Crownless Citadel: the final assault (`assault_intro`, `mirror_spire`,
`crownless_throne`). About 1:05. The Lantern and the Hollow fight each other, 5/4 against 4/4,
until the Lantern wins in D major.
"""
from cues._kit import DEFEAT_B, HOLLOW, HOLLOW_OST, LANTERN_B, new, rep, film

OST4 = "D3:.5> D3:.5 D3:.5 D3:.5 D3:.5> D3:.5 D3:.5 D3:.5"


def build():
    s = new("citadel", "The Crownless Citadel")

    a = s.section("the black gate", bars=2, meter=5, bpm=88)
    a.part("vc_spic", rep(HOLLOW_OST, 2), vel="f")
    a.part("cb_spic", rep(HOLLOW_OST, 2), vel="f", transpose=-12)
    a.part("vla_spic", rep(HOLLOW_OST, 2), vel="mf", transpose=12)
    a.part("choir", "D3+A3:5 | D3+Ab3:5", vel="mf")
    a.hits("bd", "1 2.5 4", bar=1, vel="f", bars=2)
    a.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="f", bars=2)

    b = s.section("the lantern charges", bars=4, meter=5, bpm=88)
    b.part("vc_spic", rep(HOLLOW_OST, 4), vel="f")
    b.part("cb_spic", rep(HOLLOW_OST, 4), vel="f", transpose=-12)
    lantern5 = "D4:2 A4:3 | G4:1.5 F4:.5 E4:1 A4:2 | Bb4:2 A4:1 G4:1 F4:1 | E4:5"
    b.part("hn_solo", lantern5, vel="ff")
    b.part("vln", lantern5, vel="f", transpose=12)
    b.part("tbn", "D3+F3:5 | C3+E3:3 C#3+E3:2 | D3+F3:5 | C#3+E3:5", vel="f")
    b.part("tuba", "D2:5 | C2:3 A1:2 | Bb1:5 | A1:5", vel="f")
    b.part("choir", "D4+F4:5 | C4+E4+G4:3 C#4+E4+A4:2 | D4+F4+Bb4:5 | C#4+E4+A4:5", vel="mf")
    b.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="f", bars=4)
    b.hits("bd", "1", bar=1, vel="f", bars=4)
    b.hits("crash", "1", bar=1, vel="f")

    c = s.section("the hollow answers", bars=4, meter=5, bpm=88)
    c.part("vc_spic", rep(HOLLOW_OST, 4), vel="ff")
    c.part("cb_spic", rep(HOLLOW_OST, 4), vel="ff", transpose=-12)
    c.part("hn_solo", HOLLOW, vel="ff")
    c.part("tbn", HOLLOW, vel="ff", transpose=-12)
    c.part("tuba", HOLLOW, vel="f", transpose=-24)
    c.part("vln_trem", "D6:5 | Eb6:5 | D6:5 | C#6:5", vel="f")
    c.part("tpt", "D5:2 A5:3 | r:5 | D5:2 A5:3 | r:5", vel="f")
    c.part("choir", "D3+A3:3 D3+Ab3:2 | D3+G3:3 Eb3+G3:2 | D3+A3:3 D3+Bb3:2 | C#3+A3:3 D3+Ab3:2", vel="f")
    c.part("choir_hi", "r:5 | Eb5:2.5 D5:2.5 | r:5 | Eb5:2.5 D5:2.5", vel="ff")
    c.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="ff", bars=4)
    c.hits("bd", "1 2.5 4", bar=1, vel="ff", bars=4)
    c.hits("anvil", "4.5", bar=1, vel="f", bars=4)

    d = s.section("the mirror spire", bars=4, meter=4, bpm=96)
    d.part("vc_spic", rep(OST4, 2) + " | G2:.5> G2:.5 G2:.5 G2:.5 A2:.5> A2:.5 A2:.5 A2:.5 | " + OST4, vel="f")
    d.part("cb_spic", rep(OST4, 2) + " | G2:.5> G2:.5 G2:.5 G2:.5 A2:.5> A2:.5 A2:.5 A2:.5 | " + OST4,
           vel="f", transpose=-12)
    d.part("vln", DEFEAT_B, vel="ff", transpose=12)
    d.part("hn_solo", DEFEAT_B, vel="ff")
    d.part("vla", "F4+A4:4 | G4+Bb4:4 | G4+Bb4:2 E4+A4:2 | F4+A4:4", vel="f")
    d.part("tbn", "D3+A3:4 | D3+G3:4 | D3+G3:2 C#3+E3:2 | D3+F3:4", vel="f")
    d.part("tuba", "D2:4 | G1:4 | G1:2 A1:2 | D2:4", vel="f")
    d.part("choir", "A3+D4+F4:4 | Bb3+D4+G4:4 | Bb3+D4+G4:2 A3+C#4+E4:2 | A3+D4+F4:4", vel="f")
    d.hits("timp:D2", "1 3", bar=1, vel="f", bars=2)
    d.hits("timp:A2", "1 2 3 4", bar=3, vel="f")
    d.hits("timp:D2", "1", bar=4, vel="ff")
    d.hits("crash", "1", bar=1, vel="f")

    e = s.section("the turn", bars=2, meter=4, bpm=96)
    e.part("hn", "Bb3+D4+F4:4 | C4+E4+G4:2 C#4+E4+A4:2", vel="ff")
    e.part("tbn", "Bb2+F3:4 | C3+G3:2 A2+E3:2", vel="ff")
    e.part("tuba", "Bb1:4 | C2:2 A1:2", vel="ff")
    e.part("vln_trem", "F5+Bb5+D6:4 | G5+C6+E6:2 A5+C#6+E6:2", vel="ff")
    e.part("vc", "Bb2:4 | C3:2 A2:2", vel="ff")
    e.part("cb", "Bb1:4 | C2:2 A1:2", vel="f")
    e.part("choir", "Bb3+D4+F4:4 | C4+E4+G4:2 C#4+E4+A4:2", vel="ff")
    e.hits("timp:A2", [1 + i * 0.25 for i in range(32)], bar=1, vel="f")
    e.hits("sus_cym", "1", bar=1, vel="f")

    f = s.section("the lantern wins", bars=5, meter=4, bpm=90, end_bpm=72)
    tune = LANTERN_B.replace("D4:4", "D4:4 | D4:4")
    f.part("vln", tune, vel="ff", transpose=12)
    f.part("tpt", tune, vel="ff", transpose=12)
    f.part("fl", tune, vel="f", transpose=24)
    f.part("hn_solo", tune, vel="ff")
    f.part("hn", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4+D5:4", vel="f")
    f.part("vla", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4:4", vel="f")
    f.part("tbn", "D3+A3:4 | D3+G3:2 D3+A3:2 | E3+B3:2 C#3+G3:2 | D3+A3:4 | D3+F#3+A3:4", vel="ff")
    f.part("vc", "D3:4 | G2:2 F#2:2 | E2:2 A2:2 | D3:4 | D3:4", vel="f")
    f.part("cb", "D2:4 | G1:2 F#1:2 | E1:2 A1:2 | D2:4 | D2:4", vel="mf")
    f.part("tuba", "D2:4 | G1:2 F#2:2 | E2:2 A1:2 | D2:4 | D2:4", vel="f")
    f.part("choir", "A3+D4+F#4+A4:4 | B3+D4+G4+B4:2 A3+D4+F#4+A4:2 | B3+E4+G4+B4:2 A3+C#4+E4+G4:2 | "
                    "A3+D4+F#4+A4:4 | A3+D4+F#4+A4:4", vel="f")
    f.part("bells", "D4:4 | G3:2 F#3:2 | E3:2 A3:2 | D4:4 | D4:4", vel="f")
    f.hits("crash", "1", bar=1, vel="ff")
    f.hits("timp:D2", "1", bar=1, vel="ff")
    f.hits("bd", "1", bar=1, vel="ff")
    f.hits("timp:A2", "1 3", bar=3, vel="f")
    f.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=4, vel="f")
    f.hits("timp:D2", "1", bar=5, vel="fff")
    f.hits("crash", "1", bar=5, vel="ff")
    f.hits("gong", "1", bar=5, vel="f")
    # film-trailer layer
    film(s, a, "D2:10", "build")
    film(s, b, "D2:5 | C2:3 A1:2 | Bb1:5 | A1:5", "drive", melody=lantern5)
    film(s, c, "D2:20", "drive", melody=HOLLOW)
    film(s, d, "D2:4 | G1:4 | G1:2 A1:2 | D2:4", "drive", melody=DEFEAT_B)
    film(s, e, "Bb1:4 | C2:2 A1:2", "build")
    film(s, f, "D2:4 | G1:2 F#1:2 | E1:2 A1:2 | D2:4 | D2:4", "drive", melody=tune)
    s.end_pad = 7.0
    return s
