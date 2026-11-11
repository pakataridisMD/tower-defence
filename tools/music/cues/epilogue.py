"""The Seventh Colour: the epilogue (`epilogue`), about 1:25, then the credits.
Solenne's tune going home, the Lantern at peace in D major, and a last chord with one
note nobody has a name for yet (a raised fourth, G#, over D).
"""
from cues._kit import LANTERN_A, LANTERN_B, SOLENNE, new


def build():
    s = new("epilogue", "The Seventh Colour")

    a = s.section("ash and morning", bars=8, meter=3, bpm=88)
    a.part("cl", SOLENNE, vel="mf", transpose=-12)
    a.part("harp", "F2+C3+A3:3 | Bb1+F2+D3:3 | G2+D3+Bb3:3 | C2+G2+E3:3 | F2+C3+A3:3 | A1+E2+C3:3 | "
                   "Bb1+F2+D3:1.5 C2+G2+E3:1.5 | F2+C3+A3:3", vel="p")
    a.part("vla", "C4:3 | D4:3 | D4:3 | C4:3 | C4:3 | C4:3 | D4:1.5 C4:1.5 | C4:3", vel="pp")
    a.part("vc", "F2:3 | Bb2:3 | G2:3 | C3:3 | F2:3 | A2:3 | Bb2:1.5 C3:1.5 | F2:3", vel="pp")

    b = s.section("going home", bars=8, meter=3, bpm=88)
    b.part("fl", SOLENNE, vel="mf")
    b.part("vln", SOLENNE, vel="mf", transpose=-12)
    b.part("vln2", "A4:3 | F4:3 | F4:3 | F4:1.5 E4:1.5 | F4:3 | E4:3 | F4:1.5 E4:1.5 | F4:3", vel="p")
    b.part("vla", "C4:3 | D4:3 | D4:3 | C4:3 | C4:1.5 D4:1.5 | C4:3 | D4:1.5 C4:1.5 | C4:3", vel="pp")
    b.part("vc", "F2:3 | Bb2:3 | G2:3 | C3:3 | F2:1.5 D3:1.5 | A2:3 | Bb2:1.5 C3:1.5 | F2:3", vel="pp")
    b.part("cb", "F2:3 | Bb1:3 | G1:3 | C2:3 | F2:1.5 D2:1.5 | A1:3 | Bb1:1.5 C2:1.5 | F1:3", vel="pp")
    b.part("hn", "A3+C4:3 | Bb3+D4:3 | Bb3+D4:3 | G3+C4:3 | A3+C4:3 | A3+C4:3 | Bb3+D4:1.5 G3+C4:1.5 | A3+C4:3",
           vel="pp")
    b.part("harp", "F2:.5 C3:.5 F3:.5 A3:.5 C4:.5 A3:.5 | Bb1:.5 F2:.5 Bb2:.5 D3:.5 F3:.5 D3:.5 | "
                   "G2:.5 D3:.5 F3:.5 Bb3:.5 D4:.5 Bb3:.5 | C2:.5 G2:.5 C3:.5 F3:.5 E3:.5 G3:.5 | "
                   "F2:.5 C3:.5 A3:.5 D2:.5 A2:.5 F3:.5 | A1:.5 E2:.5 A2:.5 C3:.5 E3:.5 C3:.5 | "
                   "Bb1:.5 F2:.5 D3:.5 C2:.5 G2:.5 E3:.5 | F2:.5 C3:.5 F3:.5 A3:1.5", vel="mp")

    c = s.section("turning", bars=1, meter=4, bpm=66)
    c.part("vln2", "G4+C#5+E5:4", vel="p")
    c.part("vla", "A3:4", vel="p")
    c.part("vc", "A2:4", vel="p")
    c.part("cb", "A1:4", vel="pp")
    c.part("harp", "A2:.5 E3:.5 G3:.5 C#4:.5 E4:.5 G4:.5 A4:1", vel="p")

    d = s.section("the lantern at rest", bars=8, meter=4, bpm=66)
    d.part("hn_solo", LANTERN_A, vel="mf")
    d.part("vln", "r:4 | r:4 | r:4 | r:4 | " + LANTERN_B, vel="f", transpose=12)
    d.part("vc_solo", "r:4 | r:4 | r:4 | r:4 | " + LANTERN_B, vel="mp", transpose=-12)
    d.part("vln2", "F#4+A4:4 | G4+B4:4 | F#4+B4:2 E4+A4:2 | E4+A4:4 | F#4+A4:4 | G4+B4:2 F#4+A4:2 | "
                   "G4+B4:2 E4+G4:2 | F#4+A4:4", vel="pp")
    d.part("vla", "D4:4 | D4:2 E4:2 | D4:2 C#4:2 | C#4:4 | D4:4 | D4:2 D4:2 | E4:2 C#4:2 | D4:4", vel="pp")
    d.part("cb", "D2:4 | G1:2 E2:2 | B1:2 A1:2 | A1:4 | D2:4 | G1:2 F#1:2 | E1:2 A1:2 | D2:4", vel="p")
    d.part("oohs", "r:4 | r:4 | r:4 | r:4 | A3+D4+F#4:4 | B3+D4+G4:2 A3+D4+F#4:2 | B3+E4+G4:2 A3+C#4+E4:2 | "
                   "A3+D4+F#4:4", vel="p")
    d.part("harp", "D3:.5 A3:.5 D4:.5 F#4:.5 A4:2 | G2:.5 D3:.5 G3:.5 B3:.5 E3:.5 B3:.5 E4:.5 G4:.5 | "
                   "B2:.5 F#3:.5 B3:.5 D4:.5 A2:.5 E3:.5 A3:.5 C#4:.5 | A2:.5 E3:.5 A3:.5 C#4:.5 E4:2 | "
                   "D3:.5 A3:.5 D4:.5 F#4:.5 A4:2 | G2:.5 D3:.5 G3:.5 B3:.5 F#2:.5 D3:.5 F#3:.5 A3:.5 | "
                   "E2:.5 B2:.5 E3:.5 G3:.5 A2:.5 E3:.5 G3:.5 C#4:.5 | D2:.25 A2:.25 D3:.25 F#3:.25 A3:.25 D4:.25 "
                   "F#4:.25 A4:.25 D5:2", vel="mp")
    d.hits("timp:D2", "1", bar=5, vel="p")

    e = s.section("the seventh colour", bars=3, meter=4, bpm=56, end_bpm=46)
    e.part("vln2", "F#4+A4+D5:4 | F#4+A4+D5:4 | F#4+G#4+D5:4", vel="mp")
    e.part("vla", "D4:8 C#4:4", vel="p")
    e.part("vc", "D3:12", vel="p")
    e.part("cb", "D2:12", vel="pp")
    e.part("oohs", "A3+D4+F#4:8 A3+D4+G#4:4", vel="p")
    e.part("celesta", "A6:1 F#6:1 D6:1 A5:1 | r:4 | G#6:4", vel="mp")
    e.part("glock", "r:4 | r:4 | G#6:4", vel="p")
    e.part("solo_vln", "r:4 | r:4 | G#6:4", vel="pp")
    for k in ["vln2", "vla", "vc", "cb", "oohs"]:
        s.swell(k, [(e.at(1), 0), (e.at(3, 4), -6)])
    s.end_pad = 8.0
    return s
