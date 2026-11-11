"""The Crowned Heart: Solenne, home. For `regents_counsel` and `capital_prelude`. About 1:10.

The home tune on flute, then violins, then the Lantern in a lilting 6/8 for horn and cellos,
then everyone, and a quiet close. F major. 6/8 is written as three quarter beats per bar.
"""
from cues._kit import SOLENNE, new

HARP = {
    "F": "F2:.5 C3:.5 F3:.5 A3:.5 C4:.5 A3:.5",
    "Bb": "Bb1:.5 F2:.5 Bb2:.5 D3:.5 F3:.5 D3:.5",
    "Gm7": "G2:.5 D3:.5 F3:.5 Bb3:.5 D4:.5 Bb3:.5",
    "Csus": "C2:.5 G2:.5 C3:.5 F3:.5 E3:.5 G3:.5",
    "F-Dm": "F2:.5 C3:.5 A3:.5 D2:.5 A2:.5 F3:.5",
    "Am": "A1:.5 E2:.5 A2:.5 C3:.5 E3:.5 C3:.5",
    "Bb-C": "Bb1:.5 F2:.5 D3:.5 C2:.5 G2:.5 E3:.5",
    "Fend": "F2:.5 C3:.5 F3:.5 A3:1.5",
}
TUNE_HARP = " | ".join(HARP[k] for k in ["F", "Bb", "Gm7", "Csus", "F-Dm", "Am", "Bb-C", "Fend"])
TUNE_BASS = "F2:3 | Bb1:3 | G1:3 | C2:3 | F2:1.5 D2:1.5 | A1:3 | Bb1:1.5 C2:1.5 | F1:3"
TUNE_CL = "A4:3 | F4:3 | F4:3 | F4:1.5 E4:1.5 | F4:3 | E4:3 | F4:1.5 E4:1.5 | F4:3"
TUNE_VLA = "C4:3 | D4:3 | D4:3 | C4:3 | C4:1.5 D4:1.5 | C4:3 | D4:1.5 C4:1.5 | C4:3"
# the Lantern in F, in 6/8
LANTERN_68 = ("F3:1.5 C4:1.5 | Bb3:1 A3:.5 G3:1 F3:.5 | D3:1.5 G3:1 A3:.5 | G3:3 | "
              "F3:1.5 C4:1.5 | D4:1 C4:.5 Bb3:1 A3:.5 | Bb3:1 A3:.5 G3:1 E3:.5 | F3:3")


def build():
    s = new("solenne", "The Crowned Heart")
    s.track("vln", gain_db=-3)

    a = s.section("intro", bars=2, meter=3, bpm=100)
    a.part("harp", HARP["F"] + " | " + HARP["Bb"], vel="mp")
    a.part("vc_pizz", "F2:3 | Bb1:3", vel="mp")

    b = s.section("tune on flute", bars=8, meter=3, bpm=100)
    b.part("fl", SOLENNE, vel="mp")
    b.part("harp", TUNE_HARP, vel="mp")
    b.part("cl", TUNE_CL, vel="pp")
    b.part("vc_pizz", TUNE_BASS.replace("F1:3", "F2:3"), vel="mp")

    c = s.section("tune on violins", bars=8, meter=3, bpm=100)
    c.part("vln", SOLENNE, vel="mf", transpose=-12)
    c.part("fl", "C6:3 | D6:3 | D6:3 | C6:3 | C6:1.5 D6:1.5 | C6:3 | D6:1.5 C6:1.5 | C6:3", vel="p")
    c.part("harp", TUNE_HARP, vel="p")
    c.part("vla", TUNE_VLA, vel="pp")
    c.part("vc", TUNE_BASS.replace("F1:3", "F2:3"), vel="pp", transpose=12)
    c.part("cb", TUNE_BASS.replace("F1:3", "F2:3"), vel="pp")
    c.part("hn", "A3+C4:3 | Bb3+D4:3 | Bb3+D4:3 | G3+C4:3 | A3+C4:3 | A3+C4:3 | Bb3+D4:1.5 G3+C4:1.5 | A3+C4:3",
           vel="pp")

    d = s.section("the lantern", bars=8, meter=3, bpm=96)
    d.part("hn_solo", LANTERN_68, vel="mf")
    d.part("vc_solo", LANTERN_68, vel="mp")
    d.part("vln2", "A4+C5:3 | Bb4+D5:3 | A4+D5:1.5 G4+C5:1.5 | G4+C5:3 | A4+C5:3 | Bb4+D5:1.5 A4+C5:1.5 | "
                   "Bb4+D5:1.5 Bb4+C5:1.5 | A4+C5:3", vel="p")
    d.part("fl", "C6:3 | D6:3 | A5:3 | G5:3 | A5:3 | F5:3 | G5:1.5 E5:1.5 | F5:3", vel="p")
    d.part("cb", "F2:3 | Bb1:1.5 G1:1.5 | D2:1.5 C2:1.5 | C2:3 | F2:3 | Bb1:1.5 A1:1.5 | G1:1.5 C2:1.5 | F1:3",
           vel="p")
    d.part("harp", "F2+C3+F3+A3:3 | Bb1+F2+Bb2+D3:3 | D2+A2+D3+F3:3 | C2+G2+C3+E3:3 | F2+C3+F3+A3:3 | "
                   "Bb1+F2+Bb2+D3:3 | G1+D2+G2+Bb2:3 | F2+C3+F3+A3:3", vel="mp")
    s.swell("vln2", [(d.at(1), -3), (d.at(8), 2)])

    e = s.section("everyone", bars=8, meter=3, bpm=96)
    e.part("vln", SOLENNE, vel="ff", transpose=-12)
    e.part("fl", SOLENNE, vel="mf")
    e.part("ob", SOLENNE, vel="mf", transpose=-12)
    e.part("vln2", "C5:3 | D5:3 | D5:3 | C5:3 | C5:1.5 D5:1.5 | C5:3 | D5:1.5 C5:1.5 | C5:3", vel="mp")
    e.part("vla", TUNE_VLA, vel="mf")
    e.part("cl", TUNE_CL, vel="mp")
    e.part("hn", "A3+C4+F4:3 | Bb3+D4+F4:3 | Bb3+D4+F4:3 | G3+C4+E4:3 | A3+C4+F4:3 | A3+C4+E4:3 | "
                 "Bb3+D4+F4:1.5 G3+C4+E4:1.5 | A3+C4+F4:3", vel="mp")
    e.part("vc", TUNE_BASS, vel="mp", transpose=12)
    e.part("cb", TUNE_BASS, vel="mp", transpose=12)
    e.part("harp", TUNE_HARP, vel="mf")
    e.hits("timp:F2", "1", bar=1, vel="mp")
    e.hits("timp:C3", "1", bar=4, vel="mp")
    e.hits("timp:F2", "1", bar=8, vel="mf")
    e.part("glock", "r:3 | r:3 | r:3 | r:3 | r:3 | r:3 | r:3 | A6:3", vel="mp")

    f = s.section("close", bars=6, meter=3, bpm=90, end_bpm=66)
    f.part("fl", "F5:1 G5:.5 A5:1 C6:.5 | D6:3 | C6:1.5 A5:1.5 | F5:3 | r:3 | r:3", vel="mf")
    f.part("harp", HARP["F"] + " | " + HARP["Bb"] + " | " + HARP["F"] + " | " + HARP["F"] +
           " | F2:.25 C3:.25 F3:.25 A3:.25 C4:.25 F4:.25 A4:1.5 | r:3", vel="p")
    f.part("vla", "C4:3 | D4:3 | C4:3 | C4:9", vel="pp")
    f.part("vln2", "A4:3 | Bb4:3 | A4:3 | A4:9", vel="pp")
    f.part("vc", "F3:3 | Bb2:3 | F3:3 | F2:9", vel="pp")
    f.part("glock", "r:3 | r:3 | r:3 | r:3 | C7:3 | r:3", vel="p")
    s.end_pad = 6.0
    return s
