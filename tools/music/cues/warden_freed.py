"""Freed: a corrupted Warden comes back to itself. For `ember_warden` .. `void_warden` and
`lumen_gate`. About 0:45. The Lantern in Eb, first on a solo horn, then on the strings.
"""
from cues._kit import LANTERN_A, LANTERN_B, new


def build():
    s = new("warden_freed", "Freed")

    a = s.section("corruption lifts", bars=2, meter=4, bpm=60)
    a.part("vln_trem", "Eb5+G5+C6:4 | Eb5+Ab5+C6:4", vel="pp")
    a.part("vc", "C3:4 | Ab2:4", vel="p")
    a.part("cb", "C2:4 | Ab1:4", vel="pp")
    a.part("oohs", "Eb4+G4:4 | Eb4+Ab4:4", vel="p")
    a.part("harp", "C3:.5 G3:.5 C4:.5 Eb4:.5 G4:.5 C5:.5 Eb5:.5 G5:.5 | "
                   "Ab2:.5 Eb3:.5 Ab3:.5 C4:.5 Eb4:.5 Ab4:.5 C5:.5 Eb5:.5", vel="mp")
    a.part("celesta", "r:2 G6:1 Eb6:1 | r:2 Ab6:1 Eb6:1", vel="p")
    s.swell("vln_trem", [(a.at(1), -10), (a.at(2, 4), 0)])

    b = s.section("horn", bars=4, meter=4, bpm=64)
    b.part("hn_solo", LANTERN_A, vel="mf", transpose=1)
    b.part("vln2", "G4+Bb4:4 | Ab4+C5:2 Ab4+C5:2 | G4+C5:2 F4+Bb4:2 | F4+Bb4:2 F4+Ab4+Bb4:2", vel="p")
    b.part("vla", "Eb4:4 | Eb4:2 F4:2 | Eb4:2 D4:2 | Eb4:2 D4:2", vel="p")
    b.part("vc", "Eb3:4 | Ab2:2 F2:2 | C3:2 Bb2:2 | Bb2:4", vel="mp")
    b.part("cb", "Eb2:4 | Ab1:2 F1:2 | C2:2 Bb1:2 | Bb1:4", vel="p")
    b.part("harp", "Eb2:.5 Bb2:.5 Eb3:.5 G3:.5 Bb3:.5 G3:.5 Eb3:.5 Bb2:.5 | "
                   "Ab1:.5 Eb2:.5 Ab2:.5 C3:.5 F2:.5 C3:.5 F3:.5 Ab3:.5 | "
                   "C2:.5 G2:.5 C3:.5 Eb3:.5 Bb1:.5 F2:.5 Bb2:.5 D3:.5 | "
                   "Bb1:.5 F2:.5 Bb2:.5 Eb3:.5 Bb1:.5 F2:.5 Bb2:.5 D3:.5", vel="mp")

    c = s.section("strings", bars=4, meter=4, bpm=62, end_bpm=56)
    c.part("vln", LANTERN_B, vel="f", transpose=13)
    c.part("fl", LANTERN_B, vel="mf", transpose=25)
    c.part("vln2", "Bb4+Eb5:4 | C5+Eb5:2 Bb4+Eb5:2 | C5+F5:2 Bb4+D5:2 | Bb4+Eb5:4", vel="mf")
    c.part("vla", "G4:4 | Ab4:2 G4:2 | Ab4:2 Ab4:2 | G4:4", vel="mf")
    c.part("hn", "Eb4+G4:4 | Eb4+Ab4:2 Eb4+G4:2 | F4+Ab4:2 D4+F4:2 | Eb4+G4:4", vel="mf")
    c.part("vc", "Eb3:4 | Ab2:2 G2:2 | F2:2 Bb2:2 | Eb2:4", vel="mf")
    c.part("cb", "Eb2:4 | Ab1:2 G1:2 | F1:2 Bb1:2 | Eb1:4", vel="mp")
    c.part("choir", "G3+Bb3+Eb4:4 | Ab3+C4+Eb4:2 G3+Bb3+Eb4:2 | Ab3+C4+F4:2 Ab3+Bb3+D4:2 | G3+Bb3+Eb4:4",
           vel="mf")
    c.part("harp", "r:4 | r:4 | r:4 | Eb2:.25 Bb2:.25 Eb3:.25 G3:.25 Bb3:.25 Eb4:.25 G4:.25 Bb4:.25 Eb5:2",
           vel="mf")
    c.hits("timp:Eb2", "1", bar=1, vel="mf")
    c.hits("timp:Bb2", "1", bar=3, vel="mp")
    c.hits("timp:Eb2", "1", bar=4, vel="mf")
    c.hits("sus_cym", "1", bar=1, vel="p")

    d = s.section("light", bars=2, meter=4, bpm=56)
    d.part("vln2", "Bb4+Eb5+G5:8", vel="p")
    d.part("vla", "G4:8", vel="p")
    d.part("vc", "Eb3:8", vel="p")
    d.part("oohs", "G4+Bb4+Eb5:8", vel="p")
    d.part("celesta", "Bb6:1 G6:1 Eb6:1 Bb5:1 | Eb7:4", vel="mp")
    d.part("glock", "r:4 | Eb6:4", vel="p")
    s.swell("vln2", [(d.at(1), 0), (d.at(2, 4), -10)])
    s.swell("vla", [(d.at(1), 0), (d.at(2, 4), -10)])
    s.swell("vc", [(d.at(1), 0), (d.at(2, 4), -10)])
    s.end_pad = 6.0
    return s
