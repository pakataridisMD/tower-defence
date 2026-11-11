"""The Last Lantern: score for the opening story video (`prologue`), about 4:05.

v6 (Doctor Paris: "too boring, more epic, AAA, higher tempo in the stress period, drums"):
the war in the middle runs at 136 to 150 bpm instead of 60 to 90. Vael-Orrun's march, the Ring,
the Black Comet, Oswin's stand and the Wardens have war drums in 3+3+2, a grinding 16th-note
ostinato, stacked low horns, a chanting choir and braams, in the manner of a modern game trailer.
The quiet shots (the sea, the six kingdoms, Solenne, the Regent, the fall, the road) stay slow,
so the fast ones hit harder. Every shot is fitted to the narrator's Elariel take (LINES).
v5 added the film layer, v4 the trailer voices. Words are original: "Te-ne-te vi-am" (Latin,
"hold the road"), "Lu-men", "Vael-Orrun".

One section per shot of the script (docs/story/scripts.md). Themes (see tools/music/README.md):
  - the Lantern (hope, the Order, Oswin), and the Long Defeat (the Lantern in the minor)
  - Solenne (home): a 6/8 folk tune for flute and harp
  - the Hollow (Vael-Orrun): a falling tritone in low brass
"""
import numpy as np

import vocals as V
from cues._kit import film, new, ost16
from cues.solenne import TUNE_BASS, TUNE_CL, TUNE_HARP, TUNE_VLA
from cues._kit import SOLENNE
from loops.boss import HOLLOW4, drums, grind
from score import midi

# Narrated line lengths (seconds, with a 0.6 s tail), from the narrator's Elariel take of 2026-11-11
# (/mnt/project-files/audio/voice/line_durations.json).
LINES = [14.35, 26.73, 18.81, 17.82, 21.30, 13.76, 7.89, 13.95, 10.66, 20.00, 15.29, 17.47]
# Each line starts 0.4 s into its slot (shot 1: 3.8 s, after the 3.2 s title card) and gets about
# 2 s of music after it.
TITLE = 3.4
SLOTS = [round((TITLE if i == 0 else 0) + 0.4 + line + 2.0, 2) for i, line in enumerate(LINES)]
# Shot 12: 10 bars slowing to 0.8x; the final hit (bar 9) lands 3 s after her last words, leaving
# room for the army's call-back.
FINAL_TAIL = 7.3  # reverb and silence after the last chord, inside the last slot
RIT12 = 0.8
HIT_SHARE = float(np.log(1 + (RIT12 - 1) * 32 / 40) / np.log(RIT12))
SLOTS[11] = round((0.4 + LINES[11] + 3.0) / HIT_SHARE + FINAL_TAIL, 2)


class Span:
    """Bars bar0 .. bar0+bars-1 of a section, seen as a section of their own (for film(), drums())."""

    def __init__(self, sec, bar0, bars):
        self.sec, self.bar0, self.bars, self.meter, self.name = sec, bar0, bars, sec.meter, sec.name

    def at(self, bar=1, beat=1):
        return self.sec.at(self.bar0 + bar - 1, beat)

    def part(self, inst, text, bar=1, **kw):
        self.sec.part(inst, text, bar=self.bar0 + bar - 1, **kw)
        return self

    def hits(self, kind, beats, bar=1, **kw):
        self.sec.hits(kind, beats, bar=self.bar0 + bar - 1, **kw)
        return self


def sw(s, sec, key, pts):
    """A swell that starts from and returns to 0 dB at the edges of its section, so it never leaks
    into the next shot (an expression curve holds its last value)."""
    end = sec.start + sec.beats
    s.swell(key, [(pts[0][0] - 0.01, 0.0)] + pts + [(end - 0.01, pts[-1][1]), (end, 0.0)])


def chords(harm, voicing):
    return " | ".join(f"{voicing[h]}:4" for h in harm)


def build():
    s = new("prologue", "The Last Lantern")
    for k in ["hn", "tbn", "tuba", "tpt", "hn_lo"]:
        s.tracks[k].gain_db += 2
    for k in ["hn_solo", "hn"]:
        s.tracks[k].double = 2
    s.tracks["tbn"].double = 1
    s.tracks["hn_lo"].double = 3
    s.tracks["vc_spic"].gain_db += 2
    s.tracks["cb_spic"].gain_db += 2
    s.track("choir", gain_db=-7)
    s.track("choir_hi", gain_db=-8)
    s.perc_db = -4.0  # the drums sit 6 to 9 dB over the orchestra otherwise
    shots = [sea, seven, vael_orrun, ring, solenne, regent, comet, oswin, fall, wardens, road, hold_the_road]
    for i, shot in enumerate(shots):
        shot(s, SLOTS[i])
    s.end_pad = FINAL_TAIL
    return s


# 1. Before the Concord... there were seven kingdoms. -----------------------------------------------
def sea(s, sec_len):
    a = s.section("1 sea", bars=4, meter=4, seconds=sec_len)
    a.part("cb", "D2:16", vel="pp")
    a.part("vc", "D3+A3:16", vel="p")
    a.part("vln_trem", "A5+D6:8 Bb5+D6:4 A5+D6:4", vel="pp")
    a.part("oohs", "D4+A4:4 | D4+F4+Bb4:4 | D4+G4+Bb4:4 | D4+F4+A4:4", vel="mf")
    a.part("harp", "D3:.5 A3:.5 D4:.5 E4:.5 F4:.5 A4:.5 D5:1 | Bb2:.5 F3:.5 Bb3:.5 D4:.5 F4:.5 Bb4:.5 D5:1 | "
                   "G2:.5 D3:.5 G3:.5 Bb3:.5 D4:.5 G4:.5 Bb4:1 | D3:.5 A3:.5 D4:.5 F4:.5 A4:.5 D5:.5 F5:1", vel="mp")
    sw(s, a, "vln_trem", [(a.at(1), -18), (a.at(4, 4), 0)])
    sw(s, a, "oohs", [(a.at(1), -12), (a.at(4, 4), 0)])
    sw(s, a, "vc", [(a.at(1), -10), (a.at(2), 0)])
    a.hits("gong", "1", bar=1, vel="p")
    a.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=4, vel="p")
    # one low note that grows out of nothing, and a heartbeat
    a.part("syn_pad", "D2+A2+D3:16", vel="mf")
    a.part("syn_sub", "D1:16", vel="f")
    a.part("hn_lo", "r:12 | D3:4", vel="mf")
    sw(s, a, "syn_pad", [(a.at(1), -26), (a.at(4, 4), -2)])
    sw(s, a, "syn_sub", [(a.at(1), -30), (a.at(4, 4), -4)])
    sw(s, a, "hn_lo", [(a.at(4), -14), (a.at(4, 4), 0)])
    a.hits("epic", "1", bar=1, vel="mf")
    a.hits("taiko", "1", bar=2, vel="p", bars=2)
    a.hits("taiko", "1 3", bar=4, vel="mf")
    rise(s, a.at(4, 4) + 1, 2.0, gain=-6, seed=11)


# 2. Six kingdoms, six magics; the seventh studied them all. And its king wanted all of it. ---------
def seven(s, sec_len):
    b = s.section("2 seven", bars=6, meter=5, seconds=sec_len)
    # six lights, one every two and a half beats, each held until the seventh
    b.part("hn_solo", "D4:20", vel="mp")
    b.part("cl", "A4:17.5", bar=1, beat=3.5, vel="mp")
    b.part("fl", "F#5:15", bar=2, vel="mp")
    b.part("ob", "E5:12.5", bar=2, beat=3.5, vel="p")
    b.part("vln", "A5:10", bar=3, vel="p")
    b.part("oohs", "A3+D4+F#4+A4:7.5", bar=3, beat=3.5, vel="mp")
    b.part("celesta", "D5:2.5 A5:2.5 | F#6:2.5 E6:2.5 | A6:2.5 D7:2.5", vel="mf")
    b.part("harp", " | ".join(["D3:.5 A3:.5 D4:.5 E4:.5 F#4:.5 A4:.5 D5:.5 A4:.5 F#4:.5 E4:.5"] * 4), vel="mp")
    b.part("cb", "D2:20", vel="p")
    b.part("vc", "D3:20", vel="p")
    b.part("vla", "D4:20", vel="pp")
    film(s, Span(b, 1, 2), "D2:5 | D2:5", "calm")
    film(s, Span(b, 3, 2), "D2:5 | D2:5", "build")
    # the seventh: no colour at all, and the war begins to stir under it
    b.part("tuba", "Ab1:10", bar=5, vel="f")
    b.part("tbn", "D3+Ab2:10", bar=5, vel="f")
    b.part("hn_lo", "Ab2+D3:10", bar=5, vel="ff")
    b.part("bsn", "D2:10", bar=5, vel="mp")
    b.part("vln_trem", "D6+Eb6:10", bar=5, vel="mp")
    b.part("choir", "D3+Ab3:10", bar=5, vel="mf")
    b.part("syn_bass", "Ab1:10", bar=5, vel="ff")
    b.part("syn_sub", "Ab1:10", bar=5, vel="ff")
    sw(s, b, "vln_trem", [(b.at(5), -6), (b.at(6, 5), 4)])
    sw(s, b, "choir", [(b.at(5), -6), (b.at(6, 5), 4)])
    b.part("vc_spic", ost16("D2:5", 5), bar=6, vel="ff")
    b.part("cb_spic", ost16("D2:5", 5), bar=6, vel="ff", transpose=-12)
    sw(s, b, "vc_spic", [(b.at(6), -16), (b.at(6, 5), 0)])
    sw(s, b, "cb_spic", [(b.at(6), -16), (b.at(6, 5), 0)])
    b.hits("epic", "1", bar=5, vel="fff")
    b.hits("gong", "1", bar=5, vel="mf")
    b.hits("sus_cym", "1", bar=4, vel="mp")
    hit(s, b.at(5), "Ab1", gain=-3, seed=2)
    b.hits("taiko", "1 2.5 4", bar=6, vel="ff")
    b.hits("toms", [4 + i * 0.25 for i in range(8)], bar=6, vel="ff")
    rise(s, b.at(6, 5) + 1, 2.5, gain=-2, seed=12)


# 3. Vael-Orrun, the High King. Where his armies marched, fire would not burn. ----------------------
# The war starts here: 136 bpm.
BASS3 = "D2:4 | D2:4 | D2:4 | Eb2:4 | D2:4 | D2:4 | Ab1:4 | A1:4 | D2:4 | Eb2:4 | Ab1:4 | A1:4"


def vael_orrun(s, sec_len):
    c = s.section("3 vael-orrun", bars=12, meter=4, seconds=sec_len)
    bars = BASS3.split(" | ")
    film(s, Span(c, 1, 4), " | ".join(bars[:4]), "build")
    film(s, Span(c, 5, 8), " | ".join(bars[4:]), "drive")
    c.part("vc_spic", grind(BASS3, 38), vel="ff")
    c.part("cb_spic", grind(BASS3, 26), vel="ff")
    sw(s, c, "vc_spic", [(c.at(1), -10), (c.at(5), 0)])
    sw(s, c, "cb_spic", [(c.at(1), -10), (c.at(5), 0)])
    c.hits("taiko", "1 2.5 4", bar=1, vel="f", bars=4)
    drums(Span(c, 5, 8), 8)
    hit(s, c.at(1), "D2", gain=0, seed=1)
    # the summons: the men chant his name on the tritone; trombones stab D against Ab
    for i in range(4):
        chant(s, c, i + 1, "Vail:D3:1.5 Or:D3:1 Run:Ab2:1.5", men=14, gain=-2, seed=300 + i)
    c.part("tbn", " | ".join(["D3+Ab3:.5> r:1 D3+Ab3:.5> r:1 D3+Ab3:.5> r:.5"] * 4), vel="ff")
    c.part("vln_trem", "D6+Eb6:16", vel="mf")
    # the Hollow in eight horns, trombones and tuba; a high choir screams a semitone apart
    c.part("hn_lo", HOLLOW4, bar=5, vel="fff", transpose=-12)
    c.part("hn_solo", HOLLOW4, bar=5, vel="fff")
    c.part("tbn", HOLLOW4, bar=5, vel="ff", transpose=-12)
    c.part("tuba", HOLLOW4, bar=5, vel="ff", transpose=-24)
    c.part("choir_hi", "D5+Eb5:8 | Eb5+E5:8", bar=5, vel="ff")
    c.part("choir", "D3+Ab3:8 | Ab2+D3+A3:8", bar=5, vel="ff")
    hit(s, c.at(5), "Ab1", gain=-2, seed=3)
    # the onslaught: tritone walls, trumpets on top, anvils
    c.part("tpt", "D5:1.5 Ab4:2.5 | Eb5:1.5 A4:2.5 | Ab4:4 | A4:4", bar=9, vel="ff")
    c.part("hn_lo", "D3+Ab3:4 | Eb3+A3:4 | Ab2+D3:4 | A2+Eb3:4", bar=9, vel="fff")
    c.part("choir", "D3+Ab3+Eb4:4 | Eb3+A3+E4:4 | Ab2+D3+A3:4 | A2+Eb3+Bb3:4", bar=9, vel="fff")
    c.part("choir_hi", "Eb5:4 | E5:4 | D5:4 | Eb5:4", bar=9, vel="ff")
    c.part("vln_trem", "D6+Eb6+Ab6:16", bar=9, vel="f")
    c.hits("epic", "3", bar=9, vel="fff", bars=4)
    c.hits("anvil", "2 4", bar=5, vel="f", bars=8)
    shout(s, c.at(10), "Ha!", seed=1)
    shout(s, c.at(12), "Ha!", seed=2, gain=2)
    rise(s, c.at(12, 4) + 1, 1.8, gain=0, seed=13)


# 4. The six stood together anyway, and drove him out past the edge of the stars. The Ring. --------
# The Lantern at 142 bpm, in broad horns over the drums: the first hero moment.
H4 = ["D", "D", "G", "D/F#", "Em", "A", "D", "D", "Bb", "C", "Dhit", "Dhit"]


def ring(s, sec_len):
    d = s.section("4 the ring", bars=12, meter=4, seconds=sec_len)
    melody = "D4:4 | A4:4 | B4:3 A4:1 | G4:2 F#4:2 | G4:3 F#4:1 | E4:2 C#4:2 | D4:4 | D4:4"
    push = "F4:2 G4:2 | G4:2 A4:2 | D5:8"
    bass = "D2:4 | D2:4 | G1:4 | F#1:4 | E2:4 | A1:4 | D2:4 | D2:4"
    film(s, Span(d, 1, 8), bass, "drive", melody=melody, mel_transpose=-12)
    film(s, Span(d, 9, 2), "Bb1:4 | C2:4", "drive", melody="F4:2 G4:2 | G4:2 A4:2", mel_transpose=-12)
    film(s, Span(d, 11, 2), "D2:4 | D2:4", "hit")
    drums(Span(d, 1, 10), 10)
    d.part("hn_solo", melody + " | " + push, vel="fff")
    d.part("vln", melody + " | " + push, vel="ff", transpose=12)
    d.part("tpt", "r:4 | r:4 | r:4 | r:4 | " + "G4:3 F#4:1 | E4:2 C#4:2 | D4:4 | D4:4 | " + push, vel="ff",
           transpose=12)
    v = {
        "choir": {"D": "D4+F#4+A4", "D/F#": "D4+F#4+A4", "G": "D4+G4+B4", "Em": "E4+G4+B4", "A": "C#4+E4+A4",
                  "Bb": "D4+F4+Bb4", "C": "E4+G4+C5", "Dhit": "D4+F#4+A4+D5"},
        "hn": {"D": "F#3+A3+D4", "D/F#": "F#3+A3+D4", "G": "G3+B3+D4", "Em": "G3+B3+E4", "A": "E3+A3+C#4",
               "Bb": "F3+Bb3+D4", "C": "G3+C4+E4", "Dhit": "F#3+A3+D4"},
        "tbn": {"D": "D3+A3", "D/F#": "F#2+D3", "G": "G2+D3", "Em": "E3+B3", "A": "A2+E3", "Bb": "Bb2+F3",
                "C": "C3+G3", "Dhit": "D3+A3"},
        "tuba": {"D": "D2", "D/F#": "F#1", "G": "G1", "Em": "E2", "A": "A1", "Bb": "Bb1", "C": "C2", "Dhit": "D2"},
        "vla": {"D": "F#4+A4", "D/F#": "F#4+A4", "G": "G4+B4", "Em": "G4+B4", "A": "E4+A4", "Bb": "F4+Bb4",
                "C": "G4+C5", "Dhit": "F#4+A4"},
    }
    for inst, vo in v.items():
        d.part(inst, chords(H4, vo), vel="ff")
    d.part("cb", chords(H4, v["tuba"]), vel="ff")
    d.part("vc", chords(H4, v["tuba"]), vel="ff", transpose=12)
    d.part("choir_hi", "r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | D5:4 | E5:4 | F#5:4 | F#5:4", vel="ff")
    d.part("bells", "r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | D4:4 | A3:4", vel="f")
    d.part("vln_trem", "Bb5+D6:4 | C6+E6:4", bar=9, vel="f")
    sw(s, d, "vln_trem", [(d.at(9), -8), (d.at(10, 4), 3)])
    hit(s, d.at(1), "D2", gain=-1, seed=4)
    d.hits("crash", "1", bar=1, vel="ff")
    d.hits("toms", [1 + i * 0.25 for i in range(16)], bar=10, vel="ff")
    rise(s, d.at(11), 2.0, gain=-2, seed=14)
    hit(s, d.at(11), "D2", gain=2, seed=5)
    d.hits("gong", "1", bar=11, vel="ff")
    d.hits("crash", "1", bar=11, vel="ff")
    d.hits("timp:D2", "1", bar=11, vel="fff")
    # "We call it the Ring": the choir sings "Lu-men" on the arrival
    chant(s, d, 11, "Loo:A3:2 Men:A3:2 | Loo:A3:2 Men:A3:2", men=10, women=6, gain=0, seed=11)
    chant(s, d, 11, "Loo:D3:2 Men:D3:2 | Loo:D3:2 Men:D3:2", men=10, gain=-2, seed=13)


# 5. The crown shattered into the Heartstone; they gave their lives to hold the door. Solenne. -----
def solenne(s, sec_len):
    e = s.section("5 solenne", bars=16, meter=3, seconds=sec_len)
    # the crown shatters: glitter falling, a gong, a low boom
    shards = "D7:.25 A6:.25 F6:.25 D6:.25 A5:.25 F5:.25 D5:1.5"
    e.part("celesta", shards, vel="f")
    e.part("glock", shards, vel="mf")
    e.hits("gong", "1", bar=1, vel="f")
    e.hits("crash", "1", bar=1, vel="f")
    hit(s, e.at(1), "D2", gain=-4, seed=6)
    # the six give their lives: a slow chorale, a heartbeat under it
    e.part("choir", "D3+A3+D4+F4:6 Bb2+F3+Bb3+D4:6 G2+D3+G3+Bb3:6 A2+E3+A3+C#4:6", vel="f")
    e.part("vln", "F5:6 F5:6 D5:6 C#5:6", vel="f")
    e.part("vln2", "A4+D5:6 Bb4+D5:6 G4+Bb4:6 A4+E5:6", vel="mf")
    e.part("vla", "F4:6 F4:6 D4:6 E4:6", vel="mf")
    e.part("vc", "D3:6 Bb2:6 G2:6 A2:6", vel="f")
    e.part("cb", "D2:6 Bb1:6 G1:6 A1:6", vel="f")
    e.part("hn", "F3+A3+D4:6 F3+Bb3+D4:6 G3+Bb3+D4:6 E3+A3+C#4:6", vel="f")
    e.part("tbn", "D3:6 Bb2:6 G2:6 A2:6", vel="mf")
    sw(s, e, "choir", [(e.at(1), -2), (e.at(6), 2), (e.at(8, 3), -4)])
    sw(s, e, "vln", [(e.at(1), 0), (e.at(6), 2), (e.at(8, 3), -6)])
    film(s, Span(e, 1, 8), "D2:6 Bb1:6 G1:6 A1:6", "calm")
    e.hits("taiko", "1", bar=2, vel="mf", bars=6)
    e.hits("timp:A2", [1 + i * 0.25 for i in range(12)], bar=8, vel="mf")
    # dawn: the home tune, the city rising
    tune_bass = "D2:3 | G1:3 | E1:3 | A1:3 | D2:1.5 B1:1.5 | F#1:3 | G1:1.5 A1:1.5 | D1:3"
    f = Span(e, 9, 8)
    f.part("fl", SOLENNE, vel="mf", transpose=-3)
    f.part("harp", TUNE_HARP, vel="mp", transpose=-3)
    f.part("cl", TUNE_CL, vel="pp", transpose=-3)
    f.part("vla", TUNE_VLA, vel="pp", transpose=-3)
    f.part("vc", TUNE_BASS, vel="mp", transpose=9)
    f.part("cb", tune_bass, vel="p")
    second = " | ".join(x.strip() for x in SOLENNE.split("|")[4:])
    f.part("vln", second, bar=5, vel="mf", transpose=-15)
    f.part("hn", "D3+F#3+A3:3 | D3+G3+B3:3 | D3+F#3+A3:3", bar=6, vel="mp")
    f.part("glock", "r:3 | r:3 | r:3 | r:3 | r:3 | r:3 | r:3 | D6:3", vel="p")
    film(s, f, tune_bass, "calm")
    e.hits("sus_cym", "1", bar=9, vel="mp")


# 6. The Regent, the locket, the promise ------------------------------------------------------------
def regent(s, sec_len):
    f = s.section("6 regent", bars=4, meter=4, seconds=sec_len)
    f.part("vc_solo", "B3:2 F#4:2 | E4:1.5 D4:.5 C#4 B3 | G3:2 C#4 D4 | C#4:4", vel="mf")
    f.part("bsn", "B2:4 | E3:2 D3:2 | G2:2 A2:2 | F#2:4", vel="p")
    f.part("cl", "D4:4 | G3:2 F#3:2 | B3:2 A3:2 | A#3:4", vel="pp")
    f.part("vla", "F#3:4 | B3:2 B3:2 | D4:2 E4:2 | C#4:4", vel="pp")
    f.part("cb", "B1:4 | E1:2 D2:2 | G1:2 A1:2 | F#1:4", vel="pp")
    f.part("celesta", "r:2 F#6:1 D6:1 | r:4 | r:4 | r:2 C#6:2", vel="p")
    f.part("harp", "B1+F#2:4 | r:4 | r:4 | F#1+C#2:4", vel="p")
    f.part("choir", "r:4 | r:4 | r:4 | C#3+G3:4", vel="p")
    f.part("syn_pad", "B2+F#3+D4:4 | E3+B3+D4:2 D3+A3+D4:2 | G2+D3+B3:2 A2+E3+C#4:2 | F#2+C#3+A#3:4", vel="mp")
    sw(s, f, "syn_pad", [(f.at(1), -12), (f.at(4, 4), -6)])
    f.hits("tick", [1 + i * 1.0 for i in range(4)], bar=4, vel="mf")


# 7. On the night of the Black Comet, the edge of the world split open. ------------------------------
# Six bars that speed up from 130 to 150 bpm.
def comet(s, sec_len):
    g = s.section("7 comet", bars=6, meter=4, seconds=sec_len, rit=1.15)
    g.hits("tick", [1 + i * 0.25 for i in range(16)], bar=1, vel="f", bars=6)
    g.part("vc_spic", grind("D2:24", 38), vel="ff")
    g.part("cb_spic", grind("D2:24", 26), vel="ff")
    sw(s, g, "vc_spic", [(g.at(1), -12), (g.at(6, 4), 2)])
    sw(s, g, "cb_spic", [(g.at(1), -12), (g.at(6, 4), 2)])
    g.part("vln_trem", "D5+Eb5:12 Ab5+A5:12", vel="mf")
    g.part("choir", "D3+A3:12 D3+Ab3+Eb4:12", vel="f")
    g.part("choir_hi", "r:12 Eb5+E5:12", vel="f")
    sw(s, g, "vln_trem", [(g.at(1), -10), (g.at(6, 4), 4)])
    sw(s, g, "choir", [(g.at(1), -8), (g.at(6, 4), 4)])
    film(s, Span(g, 1, 6), "D2:24", "build")
    hit(s, g.at(1), "Eb2", gain=-1, seed=8)
    g.hits("taiko", "1 2.5 4", bar=1, vel="f", bars=3)
    g.hits("taiko", "1 2 2.5 3.5 4 4.5", bar=4, vel="ff", bars=2)
    g.hits("snare", [1 + i * 0.25 for i in range(16)], bar=5, vel="f", bars=2)
    g.hits("toms", [1 + i * 0.25 for i in range(16)], bar=6, vel="fff")
    rise(s, g.at(6, 4) + 1, 2.2, gain=1, seed=2)


# 8. Oswin held it for one night. At dawn he walked to the edge, and gave it every light he had. ----
# The Long Defeat (the Lantern in the minor) at 147 bpm, the men chanting "hold the road".
def oswin(s, sec_len):
    h = s.section("8 oswin holds", bars=10, meter=4, seconds=sec_len)
    melody = "D4:4 | A4:4 | Bb4:3 A4:1 | G4:2 F4:2 | G4:3 F4:1 | E4:2 C#4:2 | D4:4 | D4:4"
    bass = "D2:4 | D2:4 | Bb1:4 | G1:4 | C2:4 | A1:4 | D2:4 | D2:4"
    climb = "Bb1:4 | A1:4"
    film(s, Span(h, 1, 8), bass, "drive", melody=melody, mel_transpose=-12)
    film(s, Span(h, 9, 2), climb, "drive")
    h.part("vc_spic", grind(bass + " | " + climb, 38), vel="ff")
    h.part("cb_spic", grind(bass + " | " + climb, 26), vel="ff")
    drums(Span(h, 1, 10), 10)
    h.part("hn_solo", melody, vel="fff")
    h.part("vln", melody, vel="ff", transpose=12)
    h.part("tpt", "G4:3 F4:1 | E4:2 C#4:2 | D4:4 | D4:4", bar=5, vel="ff", transpose=12)
    harm = ["Dm", "Dm", "Bb", "Gm", "C", "A", "Dm", "Dm", "Bb", "A"]
    v = {
        "choir": {"Dm": "D4+F4+A4", "Bb": "D4+F4+Bb4", "Gm": "D4+G4+Bb4", "C": "E4+G4+C5", "A": "C#4+E4+A4"},
        "hn": {"Dm": "F3+A3+D4", "Bb": "F3+Bb3+D4", "Gm": "G3+Bb3+D4", "C": "G3+C4+E4", "A": "E3+A3+C#4"},
        "tbn": {"Dm": "D3+A3", "Bb": "Bb2+F3", "Gm": "G2+D3", "C": "C3+G3", "A": "A2+E3"},
        "tuba": {"Dm": "D2", "Bb": "Bb1", "Gm": "G1", "C": "C2", "A": "A1"},
    }
    for inst, vo in v.items():
        h.part(inst, chords(harm, vo), vel="ff")
    h.part("choir_hi", "D5:4 | E5:4 | D5:4 | D5:4 | F5:4 | E5:4", bar=5, vel="ff")
    sw(s, h, "choir", [(h.at(1), -4), (h.at(5), 0), (h.at(10, 4), 5)])
    h.part("vln_trem", "Bb5+D6:4 | A5+C#6+E6:4", bar=9, vel="f")
    sw(s, h, "vln_trem", [(h.at(9), -6), (h.at(10, 4), 4)])
    for i, r in enumerate(["D3", "D3", "Bb2", "G2", "C3", "A2", "D3", "D3"]):
        chant(s, h, i + 1, f"Teh:{r}:.5 Neh:{r}:.5 Teh:{r}:1 Vee:{r}:1 Ahm:{r}:1", men=14, gain=-1,
              seed=20 + i * 5)
    hit(s, h.at(1), "D2", gain=0, seed=9)
    h.hits("crash", "1", bar=1, vel="f")
    h.hits("anvil", "4.5", bar=1, vel="f", bars=8)
    h.hits("toms", [1 + i * 0.25 for i in range(16)], bar=10, vel="fff")
    h.hits("timp:A2", [1 + i * 0.25 for i in range(16)], bar=10, vel="ff")
    shout(s, h.at(10), "Ha!", seed=2, gain=2)
    rise(s, h.at(10, 4) + 1, 2.0, gain=2, seed=3)


# 9. The Crack closed to a hairline. And Oswin fell. His lantern went out. ---------------------------
def fall(s, sec_len):
    k = s.section("9 the fall", bars=3, meter=4, seconds=sec_len, rit=0.7)
    k.part("tpt", "D5+F#5+A5:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("hn", "D4+F#4+A4+D5:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("hn_solo", "D4:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("tbn", "D3+A3:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("tuba", "D2:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("vln", "D5+A5+D6:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("vla", "F#4+A4:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("vc", "D3+A3:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("cb", "D2:2.5 r:1.5 | D2:8", vel="ff")
    k.part("choir", "D4+F#4+A4+D5:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("choir_hi", "F#5+A5:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("solo_vln", "r:3.5 A6:8.5", vel="ppp")
    k.part("celesta", "r:4 | A6:1 F#6:1 D6:1 A5:1 | r:2 D5:2", vel="p")
    sw(s, k, "cb", [(k.at(1), 0), (k.at(1, 2.5), 0), (k.at(2), -16), (k.at(3, 4), -24)])
    sw(s, k, "solo_vln", [(k.at(1, 3.5), 0), (k.at(3, 4), -8)])
    k.hits("gong", "1", bar=1, vel="fff")
    k.hits("crash", "1", bar=1, vel="ff")
    k.hits("sus_cym", "1", bar=1, vel="f")
    k.hits("timp:D2", "1", bar=1, vel="fff")
    k.hits("bd", "1", bar=1, vel="fff")
    k.part("syn_bass", "D2:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("syn_sub", "D1:12", vel="ff")
    k.part("hn_lo", "D3+A3:2.5 r:1.5 | r:4 | r:4", vel="fff")
    k.part("syn_pad", "r:4 | D4+A4+D5:8", vel="p")
    sw(s, k, "syn_sub", [(k.at(1), 0), (k.at(3, 4), -26)])
    sw(s, k, "syn_pad", [(k.at(2), -18), (k.at(3), -8), (k.at(3, 4), -14)])
    k.hits("epic", "1", bar=1, vel="fff")
    # the whole choir cries out, then nothing
    for note, women in [("D3", 0), ("A3", 0), ("F#4", 8), ("D4", 8)]:
        dur = s.time_of(k.at(1, 3.5)) - s.time_of(k.at(1))
        s.place(k.at(1), V.sung("Ah", midi(note), dur, n=8 if not women else 0, women=women, seed=midi(note)),
                CHANT_DB + 2, group="chant", send=0.5)
    hit(s, k.at(1), "D2", gain=3, seed=4)


# 10. A voice through the hairline drove the six monarchs mad. The High King has come back. --------
# The fastest shot: 150 bpm. A whisper, six cuts (one hit per land), the Hollow, a last wall.
BASS10 = "D2:4 | Eb2:4 | D2:4 | Ab1:4 | Bb1:4 | A1:4 | D2:4 | D2:4 | D2:4 | Bb1:2 A1:2 | Ab1:4"


def wardens(s, sec_len):
    m = s.section("10 the wardens", bars=14, meter=4, seconds=sec_len)
    # the whisper
    film(s, Span(m, 1, 2), "D2:4 | D2:4", "calm")
    m.part("cb", "D2:8", vel="mp")
    m.hits("tick", [1 + i * 0.25 for i in range(16)], bar=1, vel="f", bars=2)
    m.hits("taiko", "1 2.5", bar=1, vel="mf", bars=2)
    for i in range(2):
        chant(s, m, i + 1, "Vail:D3:1.5 Or:D3:1 Run:Ab2:1.5", men=10, gain=-7, seed=330 + i)
    rise(s, m.at(3), 1.6, gain=-1, seed=15)
    # six cuts, one land each, then the Hollow
    w = Span(m, 3, 11)
    film(s, w, BASS10, "drive")
    w.part("vc_spic", grind(BASS10, 38), vel="ff")
    w.part("cb_spic", grind(BASS10, 26), vel="ff")
    drums(w, 11)
    w.hits("anvil", "2 4", bar=1, vel="f", bars=6)
    cuts = ["D3+Ab3", "Eb3+A3", "D3+Ab3", "Ab2+D3", "Bb2+E3", "A2+Eb3"]
    w.part("hn_lo", " | ".join(f"{c}:1.5> {c}:.5 r:.5 {c}:1.5" for c in cuts), vel="fff")
    w.part("tbn", " | ".join(f"{c}:1.5> {c}:.5 r:.5 {c}:1.5" for c in cuts), vel="ff")
    w.part("tuba", "D2:4 | Eb2:4 | D2:4 | Ab1:4 | Bb1:4 | A1:4", vel="ff")
    w.part("choir", "D3+Ab3+Eb4:4 | Eb3+A3+E4:4 | D3+Ab3+Eb4:4 | Ab2+D3+A3:4 | Bb2+E3+B3:4 | A2+Eb3+Bb3:4",
           vel="fff")
    w.part("choir_hi", "Eb5:4 | E5:4 | Eb5:4 | D5:4 | E5:4 | Eb5:4", vel="ff")
    w.part("tpt", "D5:1.5 Ab4:2.5 | Eb5:1.5 A4:2.5 | D5:1.5 Ab4:2.5 | Ab4:4 | Bb4:1.5 E4:2.5 | Eb5:1.5 A4:2.5",
           vel="ff")
    for i in range(6):
        hit(s, w.at(i + 1), ["D2", "Eb2", "D2", "Ab1", "Bb1", "A1"][i], gain=-4, seed=40 + i)
    # the Hollow, the men chanting his name on it
    w.part("hn_lo", HOLLOW4, bar=7, vel="fff", transpose=-12)
    w.part("hn_solo", HOLLOW4, bar=7, vel="fff")
    w.part("tbn", HOLLOW4, bar=7, vel="ff", transpose=-12)
    w.part("tuba", HOLLOW4, bar=7, vel="ff", transpose=-24)
    w.part("choir_hi", "D5+Eb5:8 | Eb5+E5:8", bar=7, vel="ff")
    w.part("choir", "D3+Ab3:8 | D3+A3:8", bar=7, vel="ff")
    chant(s, w, 7, "Vail:D3:3 Or:Ab2:1 | Run:G2:2 Vail:A2:1 Or:Eb3:1 | Run:D3:3 Vail:C3:1 | Or:Bb2:2 Run:A2:2",
          men=14, gain=0, seed=40)
    w.part("vln_trem", "D6+Eb6:24 | Ab5+D6+Eb6:4", vel="f")
    # the last wall: everything on the tritone, then one hit and silence
    w.part("hn_lo", "Ab2+D3:4", bar=11, vel="fff")
    w.part("tpt", "D5+Ab5:4", bar=11, vel="fff")
    w.part("choir", "Ab2+D3+Ab3+Eb4:4", bar=11, vel="fff")
    w.hits("toms", [1 + i * 0.25 for i in range(16)], bar=11, vel="fff")
    film(s, Span(m, 14, 1), "D2:4", "hit")
    m.part("hn_lo", "D3+Ab3:3 r:1", bar=14, vel="fff")
    m.part("tbn", "D3+Ab3:3 r:1", bar=14, vel="fff")
    m.part("tuba", "D2:3 r:1", bar=14, vel="fff")
    m.part("choir", "D3+Ab3+D4:3 r:1", bar=14, vel="fff")
    m.hits("gong", "1", bar=14, vel="fff")
    m.hits("crash", "1", bar=14, vel="ff")
    rise(s, m.at(14), 2.0, gain=0, seed=16)
    hit(s, m.at(14), "D2", gain=4, seed=17)
    shout(s, m.at(14), "Ha!", seed=3, gain=3)


# 11. We cannot win back the lands. We can only hold the roads. Every road will cost us a city. ------
def road(s, sec_len):
    n = s.section("11 the road", bars=8, meter=4, seconds=sec_len)
    grief = "B1:2 A1:2 | G1:2 F#1:2 | E1:2 A1:2 | A1:4"
    n.part("vln", "B4:2 F#5:2 | E5:1.5 D5:.5 C#5 B4 | G4:2 C#5 D5 | E5:4 | "
                  "B4:2 C#5:2 | E5:4 | D5:2 B4:2 | C#5:2 E5:2", vel="f")
    n.part("vla", "D4+F#4:2 D4+F#4:2 | D4+G4:2 C#4+F#4:2 | E4+G4:2 C#4+E4:2 | C#4+E4:4 | "
                  "E4+G4:4 | E4+A4:4 | D4+G4:4 | E4+A4:4", vel="mp")
    n.part("vc", "B2:2 A2:2 | G2:2 F#2:2 | E2:2 A2:2 | A2:4 | E2:4 | A2:4 | G2:4 | A2:4", vel="mf")
    n.part("cb", grief + " | E1:4 | A1:4 | G1:4 | A1:4", vel="mf")
    n.part("oohs", "D4+F#4:4 | D4+G4:2 C#4+F#4:2 | E4+G4:2 C#4+E4:2 | C#4+E4+A4:4", vel="mp")
    n.part("hn", "r:4 | r:4 | G3+B3:2 A3+C#4:2 | A3+C#4+E4:4 | G3+B3+E4:4 | A3+C#4+E4:4 | G3+B3+D4:4 | "
                 "A3+C#4+E4:4", vel="f")
    n.part("choir", "r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | B3+D4+G4:4 | A3+C#4+E4+A4:4", vel="f")
    sw(s, n, "vln", [(n.at(1), 0), (n.at(5), 2), (n.at(8, 4), 5)])
    sw(s, n, "hn", [(n.at(3), -4), (n.at(8, 4), 4)])
    sw(s, n, "choir", [(n.at(7), -8), (n.at(8, 4), 4)])
    film(s, Span(n, 1, 4), grief, "calm")
    film(s, Span(n, 5, 4), "E2:4 | A1:4 | G1:4 | A1:4", "build")
    n.hits("taiko", "1 2.5 4", bar=7, vel="ff", bars=2)
    n.hits("snare", [1 + i * 0.25 for i in range(16)], bar=8, vel="f")
    n.hits("timp:A2", [1 + i * 0.25 for i in range(16)], bar=8, vel="f")
    rise(s, n.at(8, 4) + 1, 2.0, gain=-1, seed=5)


# 12. I am Ysolde. You, Spirewright, are the last of Oswin's apprentices. Hold the road. -------------
# The Lantern in full, broad over the drums, slowing to the final hit.
H12 = ["D", "D", "G", "D/F#", "Em", "A", "D", "D", "Dfin", "Dfin"]


def hold_the_road(s, sec_len):
    q = s.section("12 hold the road", bars=10, meter=4, seconds=sec_len - FINAL_TAIL, rit=RIT12)
    melody = "D5:4 | A5:4 | B5:3 A5:1 | G5:2 F#5:2 | G5:3 F#5:1 | E5:2 C#5:2 | D5:4 | D5:4 | D5:4 | D5:4"
    q.part("vln", melody, vel="ff")
    q.part("tpt", melody, vel="ff")
    q.part("ob", melody, vel="f")
    q.part("fl", melody, vel="f", transpose=12)
    q.part("hn_solo", melody, vel="fff", transpose=-12)
    v = {
        "hn": {"D": "F#4+A4", "D/F#": "F#4+A4", "G": "G4+B4", "Em": "G4+B4", "A": "E4+G4", "Dfin": "F#4+A4+D5"},
        "tbn": {"D": "D3+A3", "D/F#": "F#2+D3", "G": "D3+G3", "Em": "E3+B3", "A": "C#3+G3", "Dfin": "D3+F#3+A3"},
        "tuba": {"D": "D2", "D/F#": "F#1", "G": "G1", "Em": "E2", "A": "A1", "Dfin": "D2"},
        "vla": {"D": "F#4+A4", "D/F#": "F#4+A4", "G": "G4+B4", "Em": "G4+B4", "A": "E4+G4", "Dfin": "F#4+A4"},
        "vln2": {"D": "A4+D5", "D/F#": "A4+D5", "G": "B4+D5", "Em": "B4+E5", "A": "A4+E5", "Dfin": "A4+D5+F#5"},
        "vc": {"D": "D3", "D/F#": "F#2", "G": "G2", "Em": "E2", "A": "A2", "Dfin": "D3"},
        "choir": {"D": "A3+D4+F#4+A4", "D/F#": "A3+D4+F#4+A4", "G": "B3+D4+G4+B4", "Em": "B3+E4+G4+B4",
                  "A": "A3+C#4+E4+G4", "Dfin": "A3+D4+F#4+A4"},
        "choir_hi": {"D": "F#5", "D/F#": "F#5", "G": "G5", "Em": "G5", "A": "E5", "Dfin": "A5"},
        "bells": {"D": "D4", "D/F#": "F#3", "G": "G3", "Em": "E3", "A": "A3", "Dfin": "D4"},
    }
    for inst, vo in v.items():
        q.part(inst, chords(H12, vo), vel="ff" if inst != "bells" else "f")
    q.part("cb", chords(H12, v["tuba"]), vel="f")
    q.part("harp", "D3:.25 F#3:.25 A3:.25 D4:.25 F#4:.25 A4:.25 D5:.25 F#5:.25 A5:2", bar=8, vel="f")
    bass = "D2:4 | D2:4 | G1:4 | F#1:4 | E2:4 | A1:4 | D2:4 | D2:4"
    film(s, Span(q, 1, 8), bass, "drive", melody=melody.rsplit(" | ", 2)[0], mel_transpose=-12)
    film(s, Span(q, 9, 2), "D2:4 | D2:4", "hit")
    q.hits("epic", "3", bar=1, vel="fff", bars=6)
    q.hits("taiko", "1 2.5 4", bar=1, vel="ff", bars=6)
    q.hits("toms", [1 + i * 0.25 for i in range(32)], bar=7, vel="ff")
    q.hits("sus_cym", "1", bar=1, vel="mf")
    q.hits("timp:D2", "1", bar=1, vel="fff")
    q.hits("crash", "1", bar=1, vel="ff")
    q.hits("timp:A2", "1 3", bar=2, vel="f", bars=5)
    q.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=8, vel="f")
    for kind in ["sus_cym", "crash", "gong"]:
        q.hits(kind, "1", bar=9, vel="ff")
    q.hits("timp:D2", "1", bar=9, vel="fff")
    hit(s, q.at(1), "D2", gain=1, seed=18)
    # the choir sings "hold the road" in Latin under her; the army answers her; the final hit
    words = ("Teh:D4:4 | Neh:A4:4 | Teh:B4:3 Vee:A4:1 | Ah:G4:2 Ahm:F#4:2 | Teh:G4:3 Neh:F#4:1 | "
             "Teh:E4:2 Vee:C#4:2 | Ahm:D4:4 | r:4")
    chant(s, q, 1, words, men=0, women=8, gain=-1, seed=60)
    chant(s, q, 1, words, men=14, gain=0, seed=70, transpose=-12)
    line_end = s.time_of(q.at(1)) + 0.4 + LINES[11]
    shout(s, s._beat_at(line_end + 0.5), "Hold the road!", gain=1, seed=4, n=20, women=6)
    rise(s, q.at(9), 2.0, gain=0, seed=6)
    shout(s, q.at(9), "Hey!", gain=-1, seed=5, n=20, women=6)
    for note, women in [("D3", 0), ("A3", 0), ("D4", 8), ("F#4", 8)]:
        s.place(q.at(9), V.sung("Ah", midi(note), 4.0, n=10 if not women else 0, women=women, seed=midi(note) + 1),
                CHANT_DB + 2, group="chant", send=0.5)
    hit(s, q.at(9), "D2", gain=4, seed=7)


# ------------------------------------------------------------------------------- trailer voices
# Narrated lines start 0.4 s into each slot, so shouts go in the ~2 s gap at the end of a slot
# (or on a hit that the line leads into). Sung chant can sit under the speech: it is ducked there.
SHOUT_DB, CHANT_DB = 9.0, -3.0


def chant(s, sec, bar, text, men=10, women=0, gain=0.0, seed=0, transpose=0):
    """Sing words on notes: "Syl:PITCH:beats ...", bars separated by |, r:beats for rests."""
    b = sec.at(bar)
    for tok in text.replace("|", " ").split():
        parts = tok.split(":")
        beats = float(parts[-1])
        if parts[0] != "r":
            t0, t1 = s.time_of(b), s.time_of(b + beats * 0.96)
            m = midi(parts[1]) + transpose
            if men:
                s.place(b, V.sung(parts[0], m, t1 - t0, n=men, seed=seed), CHANT_DB + gain, group="chant",
                        send=0.45)
            if women:
                s.place(b, V.sung(parts[0], m + 12, t1 - t0, n=women, women=women, seed=seed + 7),
                        CHANT_DB + gain - 2, group="chant", send=0.45)
        b += beats
        seed += 1


def shout(s, beat, text, gain=0.0, seed=0, n=16, women=4):
    s.place(beat, V.crowd(text, n=n, women=women, seed=seed), SHOUT_DB + gain, group="shout", send=0.3)


def hit(s, beat, note="D2", gain=0.0, seed=0):
    """Braam + impact + sub drop on a downbeat."""
    s.place(beat, V.braam(midi(note), 3.5, seed=seed), -6 + gain, group="sfx", send=0.25)
    s.place(beat, V.impact(seed=seed), -5 + gain, group="sfx", send=0.2)
    s.place(beat, V.sub_drop(2.5), -7 + gain, group="sfx", send=0.0)


def rise(s, beat, seconds=2.0, gain=0.0, seed=0):
    s.place(beat, V.riser(seconds, seed=seed), -9 + gain, align="end", group="sfx", send=0.4)
