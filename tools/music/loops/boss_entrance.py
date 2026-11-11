"""The boss entrance: about 5 s that play the moment a boss wave starts, then hand over to the
boss loop (loops/boss.py) on its first beat. The impact is at 0.0 s: a tritone braam, the drum
ensemble, gong and the whole choir crying out; two bars of war drums accelerate under trombone
and tuba stabs while a riser climbs into the loop.
"""
from score import midi

LAYERS = ["hit"]
ONESHOT = True
BPM = 140
BARS = 3


def build(layer: str = "hit"):
    import vocals as V
    from cues._kit import new
    from cues.prologue import hit

    s = new("boss_entrance", "The Hollow Comes (entrance)")
    for k in ["tbn", "tuba", "hn_lo"]:
        s.tracks[k].gain_db += 3
    s.tracks["hn_lo"].double = 3
    e = s.section("entrance", bars=BARS, meter=4, bpm=BPM)
    s.end_pad = 4.0
    e.part("hn_lo", "D3+Ab3:3 r:1 | r:4 | r:4", vel="fff")
    e.part("tbn", "D3+Ab3:3 r:1 | D3+Ab3:.5> r:1 D3+Ab3:.5> r:1 D3+Ab3:.5> r:.5 | "
                  "Eb3+A3:.5> r:.5 Eb3+A3:.5> r:.5 Eb3+A3:.5> r:.5 Eb3+A3:.5> r:.5", vel="fff")
    e.part("tuba", "D2:3 r:1 | D2:.5> r:1 D2:.5> r:1 D2:.5> r:.5 | Eb2:.5> r:.5 Eb2:.5> r:.5 Eb2:.5> r:.5 "
                   "Eb2:.5> r:.5", vel="fff")
    e.part("choir", "D3+Ab3+Eb4:3 r:1 | r:4 | r:4", vel="fff")
    e.part("choir_hi", "D5+Eb5:3 r:1 | r:4 | Eb5+E5:4", vel="fff")
    e.part("vln_trem", "r:4 | D6+Eb6:8", vel="f")
    e.part("syn_sub", "D1:4 | D1:8", vel="fff")
    e.part("syn_bass", "D2:3 r:1 | D2:4 | Eb2:4", vel="fff")
    e.hits("epic", "1", bar=1, vel="fff")
    e.hits("gong", "1", bar=1, vel="fff")
    e.hits("crash", "1", bar=1, vel="ff")
    e.hits("timp:D2", "1", bar=1, vel="fff")
    e.hits("taiko", "1 2.5 4", bar=2, vel="ff")
    e.hits("taiko", "1 1.5 2 2.5 3 3.5 4 4.5", bar=3, vel="fff")
    e.hits("toms", [1 + i * 0.25 for i in range(16)], bar=3, vel="fff")
    e.hits("snare", [1 + i * 0.25 for i in range(32)], bar=2, vel="f")
    hit(s, e.at(1), "D2", gain=6, seed=11)
    s.place(e.at(1), V.braam(midi("Ab1"), 3.5, seed=12), 0, group="sfx", send=0.25)
    for note, women in [("D3", 0), ("Ab3", 0), ("D4", 8), ("Eb4", 8)]:
        s.place(e.at(1), V.sung("Ah", midi(note), 1.4, n=10 if not women else 0, women=women, seed=midi(note)),
                0, group="chant", send=0.5)
    s.place(e.at(BARS, 4) + 1, V.riser(3.0, seed=4), -2, align="end", group="sfx", send=0.4)
    return s
