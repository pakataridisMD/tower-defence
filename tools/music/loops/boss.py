"""The Hollow Comes: the music of a boss wave. A 55 s loop at 140 bpm (40% faster than the
battle music) in D Phrygian, built on Vael-Orrun's tritone: relentless war drums in 3+3+2,
16th-note strings that grind between D and E flat, the Hollow in eight horns and low brass,
a male choir chanting "Vael-Orrun", a screaming high choir a semitone apart, and braams.

Sections (8 bars each): A the summons, B the Hollow, C the onslaught, D the abyss and the climb
back (it ends on A, the dominant, so the loop drives straight back into the top).
The entrance (loops/boss_entrance.py) plays first and lands on this loop's first beat.
"""
from cues._kit import _in_range, film, name, new
from score import midi

LAYERS = ["fight"]
BPM = 140

BASS = {
    "A": "D2:4 | D2:4 | Eb2:4 | D2:4 | D2:4 | D2:4 | Ab1:4 | A1:4",
    "B": "D2:4 | D2:4 | D2:4 | Bb1:2 A1:2 | D2:4 | D2:4 | Eb2:4 | A1:4",
    "C": "D2:4 | Eb2:4 | D2:4 | Ab1:4 | Bb1:4 | Eb2:4 | Ab1:4 | A1:4",
    "D": "D2:4 | D2:4 | D2:4 | D2:4 | Bb1:4 | Bb1:4 | A1:4 | A1:4",
}
HOLLOW4 = "D4:3 Ab3:1 | G3:1.5 Bb3:.5 A3:1 Eb4:1 | D4:3 C4:1 | Bb3:2 A3:2"
GROUP = [3, 3, 2, 3, 3, 2]  # 16ths in a bar


def grind(bass: str, lo: int = 38) -> str:
    """16th notes on the root, flicking up a semitone at the end of each 3 and down a tone at the
    end of each 2: the cellos and basses never sit still."""
    out = []
    for tok in bass.replace("|", " ").split():
        p, b = tok.split(":")
        r = _in_range(midi(p), lo)
        for i in range(int(float(b) * 4)):
            pos, k = i % 16, 0
            for g in GROUP:
                if pos < g:
                    break
                pos -= g
            g = GROUP[[sum(GROUP[:j + 1]) > i % 16 for j in range(len(GROUP))].index(True)]
            n = r + (1 if (pos == g - 1 and g == 3) else -2 if (pos == g - 1 and g == 2) else 0)
            out.append(f"{name(n)}:.25" + (">" if pos == 0 else "") + "'")
    return " ".join(out)


def drums(sec, bars, vel="ff"):
    """War drums in 3+3+2 eighths, a snare on 16ths, toms at the end of every second bar."""
    sec.hits("taiko", "1 2.5 4", bar=1, vel=vel, bars=bars)
    sec.hits("snare", [1 + i * 0.25 for i in range(16)], bar=1, vel="mf", bars=bars)
    for b in range(2, bars + 1, 2):
        sec.hits("toms", [4 + i * 0.25 for i in range(4)], bar=b, vel="ff")


def build(layer: str = "fight"):
    import vocals as V
    from cues.prologue import chant

    s = new("boss_fight", "The Hollow Comes")
    secs = {k: s.section(k, bars=8, meter=4, bpm=BPM) for k in "ABCD"}
    s.end_pad = 5.0
    for k in ["hn", "hn_lo", "tbn", "tuba"]:
        s.tracks[k].gain_db += 2
    s.tracks["hn_lo"].double = 3

    for k in "ABC":
        film(s, secs[k], BASS[k], "drive")
        secs[k].part("vc_spic", grind(BASS[k], 38), vel="ff")
        secs[k].part("cb_spic", grind(BASS[k], 26), vel="ff")
        drums(secs[k], 8)

    # A: the summons. The choir chants his name on the tritone; brass stabs D against Ab.
    a = secs["A"]
    for i in range(8):
        chant(s, a, i + 1, "Vail:D3:1.5 Or:D3:1 Run:Ab2:1.5", men=14, gain=-2, seed=300 + i)
    a.part("tbn", " | ".join(["D3+Ab3:.5> r:1 D3+Ab3:.5> r:1 D3+Ab3:.5> r:.5"] * 8), vel="ff")
    a.part("vln_trem", "D6+Eb6:32", vel="mf")

    # B: the Hollow in eight horns, trombones and tuba; the high choir screams a semitone apart.
    b = secs["B"]
    b.part("hn_lo", HOLLOW4 + " | " + HOLLOW4, vel="fff", transpose=-12)
    b.part("hn_solo", HOLLOW4 + " | " + HOLLOW4, vel="fff")
    b.part("tbn", HOLLOW4 + " | " + HOLLOW4, vel="ff", transpose=-12)
    b.part("tuba", HOLLOW4 + " | " + HOLLOW4, vel="ff", transpose=-24)
    b.part("choir_hi", "D5+Eb5:8 | Eb5+E5:8 | D5+Eb5:8 | A4+Bb4:8", vel="ff")
    b.part("choir", "D3+Ab3:8 | D3+A3:8 | D3+Ab3:8 | Eb3+A3:8", vel="ff")

    # C: the onslaught. Tritone hits on every bar, the whole choir crying out, trumpets on top.
    c = secs["C"]
    c.part("tpt", "D5:1.5 Ab4:2.5 | Eb5:1.5 A4:2.5 | D5:1.5 Ab4:2.5 | Ab4:4 | Bb4:1.5 E4:2.5 | Eb5:1.5 A4:2.5 | "
                  "Ab4:4 | A4:4", vel="ff")
    c.part("hn_lo", "D3+Ab3:4 | Eb3+A3:4 | D3+Ab3:4 | Ab2+D3:4 | Bb2+E3:4 | Eb3+A3:4 | Ab2+D3:4 | A2+Eb3:4",
           vel="fff")
    c.part("choir", "D3+Ab3+Eb4:4 | Eb3+A3+E4:4 | D3+Ab3+Eb4:4 | Ab2+D3+A3:4 | Bb2+E3+B3:4 | Eb3+A3+E4:4 | "
                    "Ab2+D3+A3:4 | A2+Eb3+Bb3:4", vel="fff")
    c.part("choir_hi", "Eb5:4 | E5:4 | Eb5:4 | D5:4 | E5:4 | E5:4 | D5:4 | Eb5:4", vel="ff")
    c.part("vln_trem", "D6+Eb6+Ab6:32", vel="f")
    c.hits("epic", "3", bar=1, vel="fff", bars=8)
    c.hits("anvil", "2 4", bar=1, vel="f", bars=8)
    for i in range(8):
        s.place(c.at(i + 1), V.crowd("Ha!", n=18, women=2, seed=40 + i), 6, group="shout", send=0.3) if i % 2 else None

    # D: the abyss, then the climb. Drums and a clock alone; the chant whispers; everything rises.
    d = secs["D"]
    film(s, d, BASS["D"], "calm")
    d.part("cb", "D2:16 | Bb1:8 | A1:8", vel="f")
    d.part("syn_bass", "D2:16 | Bb1:8 | A1:8", vel="ff")
    d.hits("taiko", "1 2.5 4", bar=1, vel="ff", bars=4)
    d.hits("tick", [1 + i * 0.25 for i in range(64)], bar=1, vel="f")
    for i in range(4):
        chant(s, d, i + 1, "Vail:D3:1.5 Or:D3:1 Run:Ab2:1.5", men=10, gain=-6, seed=320 + i)
    d.part("vc_spic", "r:16 | " + grind("Bb1:8 | A1:8", 38), vel="ff")
    d.part("cb_spic", "r:16 | " + grind("Bb1:8 | A1:8", 26), vel="ff")
    s.swell("vc_spic", [(d.at(5) - 0.02, 0), (d.at(5), -14), (d.at(8, 4), 2)])
    s.swell("cb_spic", [(d.at(5) - 0.02, 0), (d.at(5), -14), (d.at(8, 4), 2)])
    d.hits("snare", [1 + i * 0.25 for i in range(16)], bar=5, vel="f", bars=4)
    d.hits("toms", [1 + i * 0.25 for i in range(32)], bar=7, vel="ff")
    d.hits("taiko", "1 1.5 2 2.5 3 3.5 4 4.5", bar=5, vel="ff", bars=4)
    d.part("vln_trem", "r:16 | Bb5+B5:8 | A5+Bb5:8", vel="f")
    d.part("choir", "r:16 | Bb2+E3+Bb3:8 | A2+Eb3+A3:8", vel="ff")
    s.swell("choir", [(d.at(5) - 0.02, -6), (d.at(5), -10), (d.at(8, 4), 4)])
    s.place(d.at(1), V.braam(midi("D2"), 4.0, seed=5), -6, group="sfx", send=0.25)
    s.place(d.at(1), V.sub_drop(3.0), -6, group="sfx", send=0.0)
    s.place(d.at(8, 4) + 1, V.riser(3.4, seed=8), -6, align="end", group="sfx", send=0.4)
    for k in ("A", "C"):
        s.place(secs[k].at(1), V.braam(midi("D2"), 3.0, seed=ord(k)), -6, group="sfx", send=0.25)
    s.place(secs["B"].at(1), V.braam(midi("Ab1"), 3.0, seed=2), -6, group="sfx", send=0.25)
    return s
