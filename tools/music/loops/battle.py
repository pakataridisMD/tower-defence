"""Hold the Line: the music under a run while the player defends. A 96 s loop in D minor at
100 bpm, in three layers that play in sync:

  calm   the build phase between waves: pads, low strings, a harp ostinato, a ticking clock and
         the themes on solo cello and horn. Complete on its own.
  wave   added while a wave is running: 16th-note string and synth ostinatos, the drum ensemble,
         synth bass and eight low horns on the themes.
  boss   added on boss waves, the last wave, or when lives run low: choir, trumpets, a chanting
         male choir ("Te-ne-te vi-am", hold the road), more drums and braams.

Sections (8 bars each): A the march (i-VI-III-VII), B the Long Defeat (the Lantern in the minor),
C the Hollow (Vael-Orrun's tritone over a pedal), D the stand (the Lantern theme in full),
E the march again, turning on the dominant back into A.
"""
from cues._kit import DEFEAT_A, DEFEAT_B, film, new
from score import midi

LAYERS = ["calm", "wave", "boss"]
# Layer balance: the calm layer plays alone through every build phase, so it is lifted.
LAYER_DB = {"calm": 8.0, "boss": 2.0}
BPM = 100

BASS = {
    "A": "D2:4 | D2:4 | Bb1:4 | Bb1:4 | F2:4 | F2:4 | C2:4 | C2:4",
    "B": "D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4 | D2:4 | G1:4 | G1:2 A1:2 | D2:4",
    "C": "D2:4 | D2:4 | D2:4 | Bb1:2 A1:2 | D2:4 | D2:4 | D2:4 | Bb1:2 A1:2",
    "D": "D2:4 | G1:4 | G1:2 A1:2 | D2:4 | D2:4 | Bb1:4 | C2:4 | A1:4",
    "E": "D2:4 | D2:4 | Bb1:4 | Bb1:4 | G1:4 | G1:4 | A1:4 | A1:4",
}
HOLLOW4 = "D4:3 Ab3:1 | G3:1.5 Bb3:.5 A3:1 Eb4:1 | D4:3 C4:1 | Bb3:2 A3:2"
STAND = ("D5:2 A5:2 | Bb5:1.5 A5:.5 G5 F5 | G5:1.5 F5:.5 E5 C#5 | D5:4 | "
         "D5:2 A5:2 | Bb5:1.5 A5:.5 G5 F5 | E5:2 F5:1 G5:1 | A5:4")


def _frame(layer):
    s = new(f"battle_{layer}", "Hold the Line")
    secs = {k: s.section(k, bars=8, meter=4, bpm=BPM) for k in "ABCDE"}
    s.end_pad = 5.0
    return s, secs


def _arp(bass: str) -> str:
    """Harp eighths on each root: root, fifth, octave, fifth (no third, so it fits any chord)."""
    from cues._kit import _in_range, name

    out = []
    for tok in bass.split():
        if tok == "|":
            out.append("|")
            continue
        p, d = tok.split(":")
        r = _in_range(midi(p), 50)
        cell = [r, r + 7, r + 12, r + 7]
        n = int(float(d) * 2)
        out += [f"{name(cell[i % 4])}:.5" for i in range(n)]
    return " ".join(out)


def _roots(bass: str, octave_lo: int) -> str:
    from cues._kit import _in_range, _map, name

    return _map(bass, lambda m: name(_in_range(m, octave_lo)))


def calm(s, secs):
    for k, sec in secs.items():
        film(s, sec, BASS[k], "calm", vel="mf")
        sec.part("cb", _roots(BASS[k], 26 + 12), vel="p")
        sec.part("harp", _arp(BASS[k]), vel="mp")
    secs["A"].hits("tick", [1 + i * 0.5 for i in range(8)], bar=1, vel="mp", bars=8)
    secs["E"].hits("tick", [1 + i * 0.5 for i in range(8)], bar=1, vel="mp", bars=8)
    secs["A"].part("vla_trem", "A4:32", vel="pp")
    secs["B"].part("vc_solo", DEFEAT_A + " | " + DEFEAT_B, vel="mp", transpose=-12)
    secs["C"].part("bsn", HOLLOW4 + " | " + HOLLOW4, vel="mp", transpose=-12)
    secs["C"].part("vln_trem", "D6+Eb6:32", vel="ppp")
    secs["D"].part("hn_solo", STAND, vel="mp", transpose=-12)
    secs["E"].part("vla_trem", "A4:16 | Bb4:8 | A4:8", vel="pp")
    secs["E"].part("celesta", "D6:4 | r:4 | Bb5:4 | r:4 | G5:4 | r:4 | A5:4 | C#6:4", vel="p")


def wave(s, secs):
    film(s, secs["A"], BASS["A"], "drive")
    film(s, secs["B"], BASS["B"], "drive", melody=DEFEAT_A + " | " + DEFEAT_B, mel_transpose=-12)
    secs["B"].part("hn_solo", DEFEAT_A + " | " + DEFEAT_B, vel="f")
    film(s, secs["C"], BASS["C"], "drive", melody=HOLLOW4 + " | " + HOLLOW4, mel_transpose=-12)
    secs["C"].part("tbn", HOLLOW4 + " | " + HOLLOW4, vel="f", transpose=-12)
    film(s, secs["D"], BASS["D"], "drive", melody=STAND, mel_transpose=-24)
    secs["D"].part("vln", STAND, vel="f")
    film(s, secs["E"], BASS["E"], "drive")
    secs["E"].part("tbn", "D3+A3:2 r:2 | r:4 | Bb2+F3:2 r:2 | r:4 | G2+D3:2 r:2 | r:4 | A2+E3:2 r:2 | "
                          "A2+E3+A3:4", vel="f")


def boss(s, secs):
    import vocals as V
    from cues.prologue import chant

    choir = {"A": "D3+A3+D4:8 | Bb2+F3+D4:8 | F3+C4+F4:8 | C3+G3+E4:8",
             "B": "D3+A3+F4:4 | G3+D4+Bb4:2 A3+E4+C#5:2 | Bb3+F4+D5:2 C4+G4+E5:2 | A3+E4+C#5:4 | "
                  "D3+A3+F4:4 | G3+D4+Bb4:4 | G3+D4+Bb4:2 A3+E4+C#5:2 | D3+A3+F4:4",
             "C": "D3+A3:4 | D3+Ab3:4 | D3+A3:4 | Bb2+F3:2 A2+E3:2 | D3+A3:4 | D3+Ab3:4 | D3+A3:4 | "
                  "Bb2+F3:2 A2+E3:2",
             "D": "D3+A3+F4:4 | G3+D4+Bb4:4 | G3+D4+Bb4:2 A3+E4+C#5:2 | D3+A3+F4:4 | D3+A3+F4:4 | "
                  "Bb2+F3+D4:4 | C3+G3+E4:4 | A2+E3+C#4:4",
             "E": "D3+A3+D4:8 | Bb2+F3+D4:8 | G2+D3+Bb3:8 | A2+E3+C#4:8"}
    for k, sec in secs.items():
        sec.part("choir", choir[k], vel="f")
        sec.hits("epic", "3", bar=1, vel="ff", bars=8)
        sec.hits("toms", [3 + i * 0.25 for i in range(8)], bar=4, vel="ff")
        sec.hits("toms", [1 + i * 0.25 for i in range(16)], bar=8, vel="ff")
        sec.hits("crash", "1", bar=1, vel="f")
    secs["B"].part("tpt", DEFEAT_A + " | " + DEFEAT_B, vel="f", transpose=12)
    secs["B"].part("choir_hi", DEFEAT_A + " | " + DEFEAT_B, vel="f", transpose=12)
    secs["C"].part("tpt", HOLLOW4 + " | " + HOLLOW4, vel="ff")
    secs["C"].part("tuba", HOLLOW4 + " | " + HOLLOW4, vel="ff", transpose=-24)
    secs["D"].part("tpt", STAND, vel="ff")
    secs["D"].part("choir_hi", STAND, vel="f")
    secs["D"].part("hn", "F4+A4:4 | G4+Bb4:4 | G4+Bb4:2 E4+A4:2 | F4+A4:4 | F4+A4:4 | F4+Bb4:4 | "
                         "E4+G4:4 | E4+A4:4", vel="ff")
    # the army chants on the march (sections A and E)
    roots = {"A": ["D3", "D3", "Bb2", "Bb2", "F3", "F3", "C3", "C3"],
             "E": ["D3", "D3", "Bb2", "Bb2", "G2", "G2", "A2", "A2"]}
    for k, rs in roots.items():
        for i, r in enumerate(rs):
            chant(s, secs[k], i + 1, f"Teh:{r}:.5 Neh:{r}:.5 Teh:{r}:1 Vee:{r}:1 Ahm:{r}:1", men=12, gain=-4,
                  seed=200 + i)
    for k, note in [("A", "D2"), ("C", "D2"), ("D", "D2")]:
        s.place(secs[k].at(1), V.braam(midi(note), 3.0, seed=ord(k)), -8, group="sfx", send=0.25)


def build(layer: str):
    s, secs = _frame(layer)
    {"calm": calm, "wave": wave, "boss": boss}[layer](s, secs)
    return s
