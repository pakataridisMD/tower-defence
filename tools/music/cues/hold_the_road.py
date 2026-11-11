"""Hold the Road: a march for the land intros (`ember_intro` .. `void_intro`) and
`convergence_intro`. About 0:45.

The Lantern in the minor over a driving string ostinato, turning to the major at the end:
we will lose the land, and we will still save its people.
"""
from cues._kit import DEFEAT_A, LANTERN_B, new, rep, film

OST = "D3:.5> D3:.5 D3:.5 D3:.5 D3:.5> D3:.5 D3:.5 D3:.5"


def build():
    s = new("hold_the_road", "Hold the Road")

    a = s.section("ostinato", bars=2, meter=4, bpm=92)
    a.part("vc_spic", rep(OST, 2), vel="mf")
    a.part("cb_spic", rep(OST, 2), vel="mf", transpose=-12)
    a.part("vla_trem", "D4+A4:8", vel="p")
    a.hits("timp:D2", "1 3", bar=1, vel="mf", bars=2)
    s.swell("vla_trem", [(a.at(1), -10), (a.at(2, 4), 0)])

    b = s.section("horns", bars=4, meter=4, bpm=92)
    b.part("hn_solo", DEFEAT_A, vel="f")
    b.part("vc_spic", "D3:.5> D3:.5 D3:.5 D3:.5 D3:.5> D3:.5 D3:.5 D3:.5 | "
                      "G2:.5> G2:.5 G2:.5 G2:.5 A2:.5> A2:.5 A2:.5 A2:.5 | "
                      "Bb2:.5> Bb2:.5 Bb2:.5 Bb2:.5 C3:.5> C3:.5 C3:.5 C3:.5 | "
                      "A2:.5> A2:.5 A2:.5 A2:.5 A2:.5> A2:.5 A2:.5 A2:.5", vel="mf")
    b.part("cb", "D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4", vel="mp")
    b.part("vla", "F3+A3:4 | G3+Bb3:2 G3+C#4:2 | F3+Bb3:2 G3+C4:2 | E3+A3:4", vel="mp")
    b.part("tbn", "r:4 | r:4 | r:4 | A2+E3:4", vel="mp")
    b.hits("timp:D2", "1 3", bar=1, vel="mf")
    b.hits("timp:A2", "1 3", bar=2, vel="mf")
    b.hits("timp:A2", "1 2 3 4", bar=4, vel="mf")

    c = s.section("strings", bars=4, meter=4, bpm=92)
    melody = "D5:2 A5:2 | Bb5:1.5 A5:.5 G5 F5 | G5:1.5 F5:.5 E5 C#5 | D5:4"
    c.part("vln", melody, vel="f")
    c.part("ob", melody, vel="mf")
    c.part("vla", "F4+A4:4 | G4+Bb4:4 | G4+Bb4:2 E4+A4:2 | F4+A4:4", vel="mp")
    c.part("hn", "D4+F4:4 | D4+G4:4 | D4+G4:2 C#4+E4:2 | D4+F4:4", vel="mp")
    c.part("vc_spic", rep(OST, 1) + " | " + "G2:.5> G2:.5 G2:.5 G2:.5 G2:.5> G2:.5 G2:.5 G2:.5 | "
                      "G2:.5> G2:.5 G2:.5 G2:.5 A2:.5> A2:.5 A2:.5 A2:.5 | " + OST, vel="mf")
    c.part("cb", "D2:4 | G1:4 | G1:2 A1:2 | D2:4", vel="mf")
    c.part("tuba", "D2:4 | G1:4 | G1:2 A1:2 | D2:4", vel="mp")
    c.hits("timp:D2", "1 3", bar=1, vel="f")
    c.hits("timp:A2", "3", bar=3, vel="f")
    c.hits("timp:D2", "1", bar=4, vel="f")
    c.hits("bd", "1", bar=1, vel="mf")

    d = s.section("build", bars=2, meter=4, bpm=92)
    d.part("vc_spic", "Bb2:.5> Bb2:.5 Bb2:.5 Bb2:.5 Bb2:.5> Bb2:.5 Bb2:.5 Bb2:.5 | "
                      "C3:.5> C3:.5 C3:.5 C3:.5 C3:.5> C3:.5 C3:.5 C3:.5", vel="f")
    d.part("cb_spic", "Bb2:.5> Bb2:.5 Bb2:.5 Bb2:.5 Bb2:.5> Bb2:.5 Bb2:.5 Bb2:.5 | "
                      "C3:.5> C3:.5 C3:.5 C3:.5 C3:.5> C3:.5 C3:.5 C3:.5", vel="f", transpose=-12)
    d.part("hn", "Bb3+D4+F4:4 | C4+E4+G4:2 C#4+E4+A4:2", vel="f")
    d.part("vln_trem", "F5+Bb5:4 | G5+C6:2 A5+C#6:2", vel="mf")
    d.part("choir", "Bb3+D4+F4:4 | C4+E4+G4:2 C#4+E4+A4:2", vel="mf")
    d.hits("timp:A2", [1 + i * 0.25 for i in range(16)], bar=1, vel="mp", bars=1)
    d.hits("timp:A2", [1 + i * 0.25 for i in range(16)], bar=2, vel="mf", bars=1)
    d.hits("sus_cym", "1", bar=2, vel="mf")
    s.swell("vln_trem", [(d.at(1), -6), (d.at(2, 4), 2)])

    e = s.section("hold", bars=5, meter=4, bpm=88, end_bpm=76)
    tune = LANTERN_B.replace("D4:4", "D4:4 | D4:4")
    e.part("vln", tune, vel="ff", transpose=12)
    e.part("tpt", tune, vel="f", transpose=12)
    e.part("hn_solo", tune, vel="ff")
    e.part("hn", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4+D5:4", vel="f")
    e.part("vla", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4:4", vel="f")
    e.part("tbn", "D3+A3:4 | D3+G3:2 D3+A3:2 | E3+B3:2 C#3+G3:2 | D3+A3:4 | D3+F#3+A3:4", vel="f")
    e.part("vc", "D3:4 | G2:2 F#2:2 | E2:2 A2:2 | D3:4 | D3:4", vel="f")
    e.part("cb", "D2:4 | G1:2 F#1:2 | E1:2 A1:2 | D2:4 | D2:4", vel="mf")
    e.part("tuba", "D2:4 | G1:2 F#2:2 | E2:2 A1:2 | D2:4 | D2:4", vel="f")
    e.part("choir", "A3+D4+F#4:4 | B3+D4+G4:2 A3+D4+F#4:2 | B3+E4+G4:2 A3+C#4+E4:2 | A3+D4+F#4:4 | "
                    "A3+D4+F#4:4", vel="f")
    e.hits("timp:D2", "1", bar=1, vel="ff")
    e.hits("crash", "1", bar=1, vel="f")
    e.hits("timp:A2", "1 3", bar=3, vel="f")
    e.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=4, vel="f")
    e.hits("timp:D2", "1", bar=5, vel="ff")
    e.hits("bd", "1", bar=5, vel="f")
    e.hits("crash", "1", bar=5, vel="f")
    # film-trailer layer
    film(s, a, "D2:8", "build")
    film(s, b, "D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4", "drive", melody=DEFEAT_A)
    film(s, c, "D2:4 | G1:4 | G1:2 A1:2 | D2:4", "drive", melody=melody, mel_transpose=-24)
    film(s, d, "Bb1:4 | C2:2 C#2:2", "build")
    film(s, e, "D2:4 | G1:2 F#1:2 | E1:2 A1:2 | D2:4 | D2:4", "drive", melody=tune)
    s.end_pad = 6.0
    return s
