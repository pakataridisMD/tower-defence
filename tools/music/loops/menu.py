"""The Last Watch: the title screen's music. A 103 s seamless loop in D minor at 84 bpm, one layer.

It sits under the menu, so it breathes: it starts low and dark, gathers, breaks into the full
orchestra and drums for two sections, and sinks back to embers before it comes round again.

Sections (8 bars each, E is 4): A embers (the Long Defeat on a solo cello over low strings),
B the watch (the theme on horns, string ostinato swelling in, taiko), C the Hollow (Vael-Orrun's
tritone on trombones and tuba, drums, choir), D the stand (the Lantern theme on violins, horns
and choir, full drums), E ashes (falling back to the pedal, turning on the dominant into A).

No celesta, glockenspiel or bells (see cues/_kit.py).
"""
from cues._kit import DEFEAT_A, DEFEAT_B, film, new

LAYERS = ["main"]
LUFS = -18.0  # a little under the battle music: it plays behind a menu
BPM = 84

BASS = {
    "A": "D2:4 | D2:4 | Bb1:4 | Bb1:4 | G1:4 | G1:4 | A1:4 | A1:4",
    "B": "D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4 | D2:4 | G1:4 | G1:2 A1:2 | D2:4",
    "C": "D2:4 | D2:4 | D2:4 | Bb1:2 A1:2 | D2:4 | D2:4 | D2:4 | Bb1:2 A1:2",
    "D": "D2:4 | G1:4 | G1:2 A1:2 | D2:4 | D2:4 | Bb1:4 | C2:4 | A1:4",
    "E": "D2:4 | Bb1:4 | G1:4 | A1:4",
}
HOLLOW4 = "D4:3 Ab3:1 | G3:1.5 Bb3:.5 A3:1 Eb4:1 | D4:3 C4:1 | Bb3:2 A3:2"
STAND = ("D5:2 A5:2 | Bb5:1.5 A5:.5 G5 F5 | G5:1.5 F5:.5 E5 C#5 | D5:4 | "
         "D5:2 A5:2 | Bb5:1.5 A5:.5 G5 F5 | E5:2 F5:1 G5:1 | A5:4")
CHOIR = {
    "B": "D3+A3+F4:4 | G3+D4+Bb4:2 A3+E4+C#5:2 | Bb3+F4+D5:2 C4+G4+E5:2 | A3+E4+C#5:4 | "
         "D3+A3+F4:4 | G3+D4+Bb4:4 | G3+D4+Bb4:2 A3+E4+C#5:2 | D3+A3+F4:4",
    "C": "D3+A3:4 | D3+Ab3:4 | D3+A3:4 | Bb2+F3:2 A2+E3:2 | D3+A3:4 | D3+Ab3:4 | D3+A3:4 | Bb2+F3:2 A2+E3:2",
    "D": "D3+A3+F4:4 | G3+D4+Bb4:4 | G3+D4+Bb4:2 A3+E4+C#5:2 | D3+A3+F4:4 | D3+A3+F4:4 | "
         "Bb2+F3+D4:4 | C3+G3+E4:4 | A2+E3+C#4:4",
}


def _roots(bass: str, octave_lo: int) -> str:
    from cues._kit import _in_range, _map, name

    return _map(bass, lambda m: name(_in_range(m, octave_lo)))


def build(layer: str):
    s = new("menu_main", "The Last Watch")
    secs = {k: s.section(k, bars=4 if k == "E" else 8, meter=4, bpm=BPM) for k in "ABCDE"}
    s.end_pad = 6.0

    # A: embers
    a = secs["A"]
    film(s, a, BASS["A"], "calm", vel="mf")
    a.part("cb", _roots(BASS["A"], 38), vel="p")
    a.part("vc", _roots(BASS["A"], 50), vel="pp")
    a.part("vla_trem", "A4:32", vel="pp")
    a.part("vc_solo", DEFEAT_A + " | " + DEFEAT_B, vel="mp", transpose=-12)
    a.hits("toms", "1", bar=1, vel="mp", bars=8)
    a.hits("taiko", "1 3", bar=5, vel="mp", bars=4)

    # B: the watch
    b = secs["B"]
    film(s, b, BASS["B"], "build", vel="f")
    b.part("cb", _roots(BASS["B"], 38), vel="mf")
    b.part("hn_solo", DEFEAT_A + " | " + DEFEAT_B, vel="mf")
    b.part("oohs", CHOIR["B"], vel="mp")
    b.part("vla_trem", "A4:16 | D5:16", vel="p")

    # C: the Hollow
    c = secs["C"]
    film(s, c, BASS["C"], "drive", melody=HOLLOW4 + " | " + HOLLOW4, mel_transpose=-12, vel="f")
    c.part("tbn", HOLLOW4 + " | " + HOLLOW4, vel="f", transpose=-12)
    c.part("tuba", HOLLOW4 + " | " + HOLLOW4, vel="f", transpose=-24)
    c.part("choir", CHOIR["C"], vel="mf")
    c.part("vln_trem", "D6+Eb6:32", vel="pp")
    c.hits("crash", "1", bar=1, vel="mf")

    # D: the stand
    d = secs["D"]
    film(s, d, BASS["D"], "drive", melody=STAND, mel_transpose=-24, vel="f")
    d.part("vln", STAND, vel="f")
    d.part("vln2", STAND, vel="mf", transpose=-12)
    d.part("choir", CHOIR["D"], vel="f")
    d.part("hn", "F4+A4:4 | G4+Bb4:4 | G4+Bb4:2 E4+A4:2 | F4+A4:4 | F4+A4:4 | F4+Bb4:4 | "
                 "E4+G4:4 | E4+A4:4", vel="f")
    d.part("tpt", "r:4 | r:4 | r:4 | D5:4 | r:4 | r:4 | r:4 | C#5:4", vel="mf")
    d.hits("crash", "1", bar=1, vel="f")

    # E: ashes, back to the pedal, turning into A
    e = secs["E"]
    film(s, e, BASS["E"], "calm", vel="mf")
    e.part("cb", _roots(BASS["E"], 38), vel="p")
    e.part("vc", "D3:4 | D3:4 | D3:4 | C#3:4", vel="pp")
    e.part("solo_vln", "A5:2 G5:2 | F5:4 | E5:2 D5:2 | C#5:4", vel="p")
    e.part("vla_trem", "A4:16", vel="pp")
    # the stand's last chord rings into the quiet, so the drop is not a cliff
    e.hits("epic", "1", bar=1, vel="ff")
    e.part("choir", "D3+A3+D4:8", vel="mf")
    e.part("hn_lo", "D3+A3:6", vel="f")
    return s
