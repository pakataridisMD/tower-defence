"""The White Lantern: Oswin returns and dawn breaks (`dawn`, `heart_falls`). About 1:15.
A light on the east road, the Hollow falling quiet around him, then the Lantern in full,
lifted from D to E major, with choir and bells.
"""
from cues._kit import LANTERN_A, LANTERN_B, new, rep

E_OST = "E2:.5> E2:.5 E2:.5 E2:.5 E2:.5> E2:.5 E2:.5 E2:.5"


def build():
    s = new("white_lantern", "The White Lantern")

    a = s.section("a light on the east road", bars=3, meter=4, bpm=60)
    a.part("cb", "D2:12", vel="ppp")
    a.part("vc", "D3+A3:8 D3+G#3:4", vel="ppp")
    a.part("vln_trem", "r:4 E6+B6:8", vel="ppp")
    a.part("oohs", "r:4 E5+B5:8", vel="pp")
    a.part("tpt_solo", "r:4 | E4:2 B4:2 | A4:4", vel="p")
    a.part("celesta", "r:4 | r:2 B6:1 E7:1 | r:4", vel="p")
    s.swell("vln_trem", [(a.at(2), -12), (a.at(3, 4), 0)])

    b = s.section("he walks through them", bars=4, meter=4, bpm=66)
    b.part("hn_solo", LANTERN_A, vel="mf", transpose=2)
    b.part("vc_spic", rep(E_OST, 4), vel="mp", transpose=12)
    b.part("cb", "E2:4 | A1:2 F#1:2 | C#2:2 B1:2 | B1:4", vel="mp")
    b.part("vln2", "G#4+B4:4 | A4+C#5:2 A4+C#5:2 | G#4+C#5:2 F#4+B4:2 | F#4+A4+B4:4", vel="p")
    b.part("vla", "E4:4 | E4:2 F#4:2 | E4:2 D#4:2 | D#4:4", vel="p")
    b.part("harp", "E2:.5 B2:.5 E3:.5 G#3:.5 B3:.5 E4:.5 G#4:.5 B4:.5 | A1:.5 E2:.5 A2:.5 C#3:.5 F#2:.5 C#3:.5 "
                   "F#3:.5 A3:.5 | C#2:.5 G#2:.5 C#3:.5 E3:.5 B1:.5 F#2:.5 B2:.5 D#3:.5 | "
                   "B1:.5 F#2:.5 B2:.5 D#3:.5 F#3:.5 A3:.5 B3:.5 D#4:.5", vel="mp")
    s.swell("vln2", [(b.at(1), -4), (b.at(4, 4), 4)])
    s.swell("vc_spic", [(b.at(1), 0), (b.at(4, 4), 4)])
    b.hits("timp:E2", "1", bar=1, vel="mp")
    b.hits("timp:B2", "1", bar=4, vel="mf")

    c = s.section("the sky splits", bars=2, meter=4, bpm=66)
    c.part("hn", "C4+E4+G4:4 | D4+F#4+A4:4", vel="f")
    c.part("tbn", "C3+G3:4 | D3+A3:4", vel="f")
    c.part("tuba", "C2:4 | D2:4", vel="f")
    c.part("vln_trem", "E5+G5+C6:4 | F#5+A5+D6:4", vel="f")
    c.part("vla_trem", "G4+C5:4 | A4+D5:4", vel="mf")
    c.part("vc", "C3:4 | D3:4", vel="f")
    c.part("cb", "C2:4 | D2:4", vel="f")
    c.part("choir", "C4+E4+G4:4 | D4+F#4+A4:4", vel="f")
    s.swell("choir", [(c.at(1), -6), (c.at(2, 4), 4)])
    s.swell("vln_trem", [(c.at(1), -6), (c.at(2, 4), 4)])
    c.hits("timp:C3", [1 + i * 0.25 for i in range(16)], bar=1, vel="mf")
    c.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=2, vel="f")
    c.hits("sus_cym", "1", bar=1, vel="f")  # peaks as dawn breaks

    d = s.section("dawn", bars=8, meter=4, bpm=63)
    tune = LANTERN_A + " | " + LANTERN_B
    d.part("vln", tune, vel="ff", transpose=14)
    d.part("tpt", tune, vel="f", transpose=14)
    d.part("fl", tune, vel="f", transpose=26)
    d.part("hn_solo", tune, vel="ff", transpose=2)
    d.part("vln2", "G#4+B4+E5:4 | A4+C#5+E5:2 A4+C#5+F#5:2 | G#4+C#5+E5:2 F#4+B4+D#5:2 | F#4+B4+D#5:4 | "
                   "G#4+B4+E5:4 | A4+C#5+E5:2 G#4+B4+E5:2 | A4+C#5+F#5:2 A4+B4+D#5:2 | G#4+B4+E5:4", vel="mf")
    d.part("vla", "E4+G#4:4 | E4+A4:2 F#4+A4:2 | E4+G#4:2 D#4+F#4:2 | D#4+F#4:4 | E4+G#4:4 | E4+A4:2 E4+G#4:2 | "
                  "F#4+A4:2 D#4+A4:2 | E4+G#4:4", vel="f")
    d.part("hn", "G#3+B3:4 | A3+C#4:4 | G#3+C#4:2 F#3+B3:2 | F#3+B3:4 | G#3+B3:4 | A3+C#4:2 G#3+B3:2 | "
                 "A3+C#4:2 A3+B3:2 | G#3+B3:4", vel="f")
    d.part("tbn", "E3+B3:4 | A2+E3:2 F#2+C#3:2 | C#3+G#3:2 B2+F#3:2 | B2+F#3:4 | E3+B3:4 | A2+E3:2 G#2+E3:2 | "
                  "F#2+C#3:2 B2+A3:2 | E3+B3:4", vel="ff")
    bass = "E2:4 | A1:2 F#1:2 | C#2:2 B1:2 | B1:4 | E2:4 | A1:2 G#1:2 | F#1:2 B1:2 | E2:4"
    d.part("vc", bass, vel="f", transpose=12)
    d.part("cb", bass, vel="mf")
    d.part("tuba", bass, vel="f")
    d.part("choir", "G#3+B3+E4+G#4:4 | A3+C#4+E4+A4:2 A3+C#4+F#4+A4:2 | G#3+C#4+E4+G#4:2 F#3+B3+D#4+F#4:2 | "
                    "F#3+B3+D#4+F#4:4 | G#3+B3+E4+G#4:4 | A3+C#4+E4+A4:2 G#3+B3+E4+G#4:2 | "
                    "A3+C#4+F#4+A4:2 A3+B3+D#4+F#4:2 | G#3+B3+E4+G#4:4", vel="f")
    d.part("bells", "E4:4 | A3:4 | C#4:4 | B3:4 | E4:4 | A3:4 | F#3:2 B3:2 | E4:4", vel="f")
    d.part("harp", "r:4 | r:4 | r:4 | B1:.25 F#2:.25 B2:.25 D#3:.25 F#3:.25 B3:.25 D#4:.25 F#4:.25 B4:2 | "
                   "r:4 | r:4 | r:4 | E2:.25 B2:.25 E3:.25 G#3:.25 B3:.25 E4:.25 G#4:.25 B4:.25 E5:2", vel="f")
    d.hits("crash", "1", bar=1, vel="ff")
    d.hits("gong", "1", bar=1, vel="f")
    d.hits("bd", "1", bar=1, vel="ff")
    d.hits("timp:E2", "1", bar=1, vel="ff")
    d.hits("timp:B2", "1 3", bar=4, vel="f")
    d.hits("timp:E2", "1", bar=5, vel="ff")
    d.hits("crash", "1", bar=5, vel="f")
    d.hits("timp:B2", [1 + i * 0.25 for i in range(16)], bar=7, vel="f")
    d.hits("timp:E2", "1", bar=8, vel="ff")

    e = s.section("morning", bars=2, meter=4, bpm=56, end_bpm=48)
    e.part("vln2", "G#4+B4+E5:8", vel="mf")
    e.part("vla", "E4+G#4:8", vel="mf")
    e.part("vc", "E3:8", vel="mf")
    e.part("cb", "E2:8", vel="mp")
    e.part("hn", "G#3+B3+E4:8", vel="mp")
    e.part("choir", "G#3+B3+E4+G#4:8", vel="mf")
    e.part("bells", "E4:4 B3:4", vel="mp")
    e.part("glock", "B6:2 G#6:2 | E7:4", vel="mp")
    e.part("celesta", "r:2 E6:1 G#6:1 | B6:4", vel="mp")
    for k in ["vln2", "vla", "vc", "cb", "hn", "choir"]:
        s.swell(k, [(e.at(1), 0), (e.at(2, 4), -8)])
    s.end_pad = 7.0
    return s
