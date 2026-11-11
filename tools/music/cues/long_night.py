"""There Was No Dawn: the Long Night lament (`long_night`, also `solenne_falls`). About 0:50.
The Lantern in the minor on a solo violin, lanterns flickering on the celesta.
"""
from cues._kit import DEFEAT_A, DEFEAT_B, new


def build():
    s = new("long_night", "There Was No Dawn")
    s.track("solo_vln", gain_db=-2)

    a = s.section("darkness", bars=2, meter=4, bpm=58)
    a.part("cb", "D2:8", vel="pp")
    a.part("vc", "D3+A3:8", vel="ppp")
    a.part("celesta", "r:1 A5:1 r:1.5 D6:.5 | r:1 F5:1 r:1 E5:1", vel="p")
    a.part("harp", "D2+A2:4 | r:4", vel="p")

    b = s.section("solo violin", bars=4, meter=4, bpm=58)
    b.part("solo_vln", DEFEAT_A, vel="mp", transpose=12)
    b.part("vla", "F3+A3:4 | G3+Bb3:2 G3+C#4:2 | F3+Bb3:2 G3+C4:2 | E3+A3:4", vel="pp")
    b.part("vc", "D3:4 | G2:2 A2:2 | Bb2:2 C3:2 | A2:4", vel="p")
    b.part("cb", "D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4", vel="pp")
    b.part("celesta", "r:4 | r:3 A6:1 | r:4 | r:2 E6:2", vel="pp")

    c = s.section("all strings", bars=4, meter=4, bpm=58)
    c.part("vln", DEFEAT_B, vel="mf", transpose=12)
    c.part("vc_solo", DEFEAT_B, vel="mp", transpose=-12)
    c.part("ob", "F5:4 | D5:4 | Bb4:2 A4:2 | A4:4", vel="p")
    c.part("vla", "F4+A4:4 | G4+Bb4:4 | G4+Bb4:2 E4+G4:2 | F4+A4:4", vel="mp")
    c.part("cb", "D2:4 | G1:4 | G1:2 A1:2 | D2:4", vel="mp")
    c.part("hn", "A3+D4:4 | Bb3+D4:4 | Bb3+D4:2 A3+C#4:2 | A3+D4:4", vel="pp")
    s.swell("vln", [(c.at(1), -2), (c.at(3), 2), (c.at(4, 4), -4)])

    d = s.section("lanterns", bars=2, meter=4, bpm=58, end_bpm=50)
    d.part("vln2", "D5+E5+A5:8", vel="pp")
    d.part("vla", "F4:8", vel="pp")
    d.part("vc", "D3:8", vel="pp")
    d.part("cb", "D2:8", vel="pp")
    d.part("celesta", "A5:1 r:1 E6:1 r:1 | D6:4", vel="p")
    s.swell("vln2", [(d.at(1), 0), (d.at(2, 4), -12)])
    s.end_pad = 7.0
    return s
