"""The Last Lantern: score for the opening story video (`prologue`), about 3:00.

One section per shot of the script (docs/story/scripts.md), each fitted to the length of the
narrator's line for that shot (SLOTS, in seconds, from the voice thread's previews).
Themes introduced here and reused by the other cues (see tools/music/README.md):
  - the Lantern (hope, the Order, Oswin)
  - Solenne (home): a 6/8 folk tune for flute and harp
  - the Hollow (Vael-Orrun): a falling tritone in low brass over a 5/4 ostinato
"""
from cues._kit import HOLLOW, HOLLOW_OST, SOLENNE, new, rep
from cues.solenne import TUNE_BASS, TUNE_CL, TUNE_HARP, TUNE_VLA

# Shot lengths (seconds) for the narration at 0.8x speed with long pauses.
SLOTS = [18.7, 13.8, 12.4, 16.7, 12.1, 13.0, 8.5, 13.2, 12.0, 14.0, 15.3, 29.3]
FINAL_TAIL = 7.3  # reverb and silence after the last chord, inside the last slot


def build():
    s = new("prologue", "The Last Lantern")
    # bigger brass and choir than the other cues
    for k in ["hn", "tbn", "tuba", "tpt"]:
        s.tracks[k].gain_db += 2
    s.track("choir", gain_db=-7)
    s.track("choir_hi", gain_db=-8)

    # 1. The sea before the world -------------------------------------------------------------
    a = s.section("1 sea", bars=4, meter=4, seconds=SLOTS[0])
    a.part("cb", "D2:16", vel="pp")
    a.part("vc", "D3+A3:16", vel="p")
    a.part("vln_trem", "A5+D6:8 Bb5+D6:4 A5+D6:4", vel="pp")
    a.part("oohs", "D4+A4:4 | D4+F4+Bb4:4 | D4+G4+Bb4:4 | D4+F4+A4:4", vel="mf")
    a.part("harp", "D3:.5 A3:.5 D4:.5 E4:.5 F4:.5 A4:.5 D5:1 | Bb2:.5 F3:.5 Bb3:.5 D4:.5 F4:.5 Bb4:.5 D5:1 | "
                   "G2:.5 D3:.5 G3:.5 Bb3:.5 D4:.5 G4:.5 Bb4:1 | D3:.5 A3:.5 D4:.5 F4:.5 A4:.5 D5:.5 F5:1", vel="mp")
    s.swell("vln_trem", [(a.at(1), -18), (a.at(4, 4), 0)])
    s.swell("oohs", [(a.at(1), -12), (a.at(4, 4), 0)])
    s.swell("vc", [(a.at(1), -10), (a.at(2), 0)])
    a.hits("gong", "1", bar=1, vel="p")
    a.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=4, vel="p")

    # 2. Seven stepped out of the sea ---------------------------------------------------------
    b = s.section("2 seven", bars=3, meter=5, seconds=SLOTS[1])
    b.part("cb", "D2:10 r:5", vel="p")
    b.part("vc", "D3:10 r:5", vel="p")
    b.part("vla", "D4:10 r:5", vel="pp")
    # six lights, one after another, then all of them together
    b.part("hn_solo", "D4:10", vel="mp")
    b.part("cl", "A4:9.25", bar=1, beat=1.75, vel="mp")
    b.part("fl", "F#5:8.5", bar=1, beat=2.5, vel="mp")
    b.part("ob", "E5:7.75", bar=1, beat=3.25, vel="p")
    b.part("vln", "A5:7", bar=1, beat=4, vel="p")
    b.part("celesta", "D5:.75 A5:.75 F#6:.75 E6:.75 A6:.75 D7:1.25 | r:5 | r:5", vel="mf")
    b.part("oohs", "r:5 | A3+D4+F#4+A4:5 | r:5", vel="mp")
    b.part("harp", "r:5 | D3:.25 A3:.25 D4:.25 E4:.25 F#4:.25 A4:.25 D5:.25 E5:.25 F#5:.25 A5:.25 D6:2.5 | r:5",
           vel="mf")
    # the seventh: no colour at all
    b.part("tuba", "r:5 | r:5 | Ab1:5", vel="f")
    b.part("tbn", "r:5 | r:5 | D3+Ab2:5", vel="mf")
    b.part("bsn", "r:5 | r:5 | D2:5", vel="mp")
    b.part("vln_trem", "r:5 | r:5 | D6+Eb6:5", vel="p")
    b.part("choir", "r:5 | r:5 | D3+Ab3:5", vel="mp")
    b.hits("sus_cym", "1", bar=2, vel="mp")
    b.hits("timp:D2", "1", bar=3, vel="f")
    b.hits("gong", "1", bar=3, vel="mp")

    # 3. Vael-Orrun. "They stopped." ---------------------------------------------------------
    c = s.section("3 vael-orrun", bars=3, meter=5, seconds=SLOTS[2])
    hollow3 = "D3:3 Ab2:2 | G2:1.5 Bb2:.5 A2:1 Eb3:2 | D3:3 Eb3:1.5> r:.5"
    c.part("hn", hollow3, vel="ff")
    c.part("tbn", hollow3, vel="f")
    c.part("tuba", hollow3, vel="f", transpose=-12)
    c.part("vc", "D2:5 | D2:5 | D2:4.5 r:.5", vel="mf")
    c.part("cb", "D2:5 | D2:5 | D2:4.5 r:.5", vel="mf")
    c.part("choir", "D3+A3:5 | D3+Ab3:5 | D3+Ab3+Eb4:4.5 r:.5", vel="mf")
    c.part("vln_trem", "D5+Eb5:5 | D5+Eb5:5 | D5+Eb5+Ab5:4.5 r:.5", vel="mp")
    s.swell("choir", [(c.at(1), -8), (c.at(3, 4), 4)])
    s.swell("vln_trem", [(c.at(1), -10), (c.at(3, 4), 2)])
    c.hits("timp:D2", "1", bar=1, vel="f", bars=3)
    c.hits("bd", "1", bar=1, vel="f", bars=3)
    c.hits("anvil", "4", bar=2, vel="mf")
    c.hits("timp:Eb2", "4", bar=3, vel="fff")
    c.hits("gong", "4", bar=3, vel="f")
    c.hits("bd", "4", bar=3, vel="ff")

    # 4. The Six join hands: the Ring --------------------------------------------------------
    d = s.section("4 the ring", bars=5, meter=4, seconds=SLOTS[3])
    d.part("hn_solo", "D4:2 A4:2 | G4:1.5 F#4:.5 E4 D4 | B3:2 E4 F#4 | D4:4 | D4:4", vel="mf")
    d.part("vln", "r:4 | r:4 | B4:2 E5 F#5 | D5:4 | D5:4", vel="mf")
    d.part("vln2", "F#4+A4:4 | G4+B4:4 | F#4+B4:2 E4+A4:2 | F#4+A4+D5:4 | F#4+A4+D5:4", vel="p")
    d.part("vla", "D4:4 | D4:2 E4:2 | D4:2 C#4:2 | D4:4 | D4+F#4:4", vel="p")
    d.part("vc", "D3:4 | G2:2 E3:2 | B2:2 A2:2 | D3:4 | D3:4", vel="mf")
    d.part("cb", "D2:4 | G1:2 E2:2 | B1:2 A1:2 | D2:4 | D2:4", vel="mf")
    d.part("choir", "r:4 | r:4 | B3+F#4:2 A3+E4:2 | A3+D4+F#4:4 | A3+D4+F#4+A4:4", vel="f")
    d.part("hn", "r:4 | r:4 | r:4 | F#3+A3+D4:4 | F#3+A3+D4:4", vel="f")
    d.part("tbn", "r:4 | r:4 | r:4 | D3+A3:4 | D3+A3:4", vel="f")
    d.part("tuba", "r:4 | r:4 | r:4 | D2:4 | D2:4", vel="f")
    d.part("harp", "D3:.5 A3:.5 D4:.5 F#4:.5 A4:.5 D4:.5 F#4:.5 A4:.5 | G2:.5 D3:.5 G3:.5 B3:.5 E3:.5 B3:.5 "
                   "E4:.5 G4:.5 | B2:.5 F#3:.5 B3:.5 D4:.5 A2:.5 E3:.5 A3:.5 C#4:.5 | "
                   "D2:.25 A2:.25 D3:.25 F#3:.25 A3:.25 D4:.25 F#4:.25 A4:.25 D5:2 | r:4", vel="mf")
    d.part("bells", "r:4 | r:4 | r:4 | D4:4 | A3:4", vel="mf")
    s.swell("vln2", [(d.at(1), -4), (d.at(3), 0), (d.at(4), 4)])
    s.swell("choir", [(d.at(3), -6), (d.at(4), 2), (d.at(5, 4), 4)])
    d.hits("sus_cym", "1", bar=4, vel="mf")
    d.hits("timp:D2", "1", bar=4, vel="f")
    d.hits("crash", "1", bar=4, vel="mf")
    d.hits("bd", "1", bar=4, vel="f")
    d.hits("timp:D2", [1 + i * 0.25 for i in range(12)], bar=5, vel="mf")

    # 5. Dawn over Solenne -------------------------------------------------------------------
    e = s.section("5 solenne", bars=8, meter=3, seconds=SLOTS[4])
    e.part("fl", SOLENNE, vel="mf", transpose=-3)
    e.part("harp", TUNE_HARP, vel="mp", transpose=-3)
    e.part("cl", TUNE_CL, vel="pp", transpose=-3)
    e.part("vla", TUNE_VLA, vel="pp", transpose=-3)
    e.part("vc", TUNE_BASS, vel="pp", transpose=9)
    e.part("glock", "r:3 | r:3 | r:3 | r:3 | r:3 | r:3 | r:3 | D6:3", vel="p")

    # 6. The Regent, the locket, the promise -------------------------------------------------
    f = s.section("6 regent", bars=4, meter=4, seconds=SLOTS[5])
    f.part("vc_solo", "B3:2 F#4:2 | E4:1.5 D4:.5 C#4 B3 | G3:2 C#4 D4 | C#4:4", vel="mf")
    f.part("bsn", "B2:4 | E3:2 D3:2 | G2:2 A2:2 | F#2:4", vel="p")
    f.part("cl", "D4:4 | G3:2 F#3:2 | B3:2 A3:2 | A#3:4", vel="pp")
    f.part("vla", "F#3:4 | B3:2 B3:2 | D4:2 E4:2 | C#4:4", vel="pp")
    f.part("cb", "B1:4 | E1:2 D2:2 | G1:2 A1:2 | F#1:4", vel="pp")
    f.part("celesta", "r:2 F#6:1 D6:1 | r:4 | r:4 | r:2 C#6:2", vel="p")
    f.part("harp", "B1+F#2:4 | r:4 | r:4 | F#1+C#2:4", vel="p")
    f.part("choir", "r:4 | r:4 | r:4 | C#3+G3:4", vel="p")

    # 7. The Black Comet ---------------------------------------------------------------------
    g = s.section("7 comet", bars=2, meter=5, seconds=SLOTS[6], rit=1.15)
    g.part("vc_spic", rep(HOLLOW_OST, 2), vel="f")
    g.part("cb_spic", rep(HOLLOW_OST, 2), vel="f", transpose=-12)
    g.part("vln_trem", "D5+Eb5:5 | Ab5+A5:5", vel="mp")
    g.part("choir", "D3+A3:5 | D3+Ab3:5", vel="mf")
    s.swell("vln_trem", [(g.at(1), -10), (g.at(2, 5), 3)])
    s.swell("vc_spic", [(g.at(1), -6), (g.at(2, 5), 0)])
    s.swell("cb_spic", [(g.at(1), -6), (g.at(2, 5), 0)])
    s.swell("choir", [(g.at(1), -6), (g.at(2, 5), 3)])
    g.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="f", bars=2)
    g.hits("bd", "1 2.5 4", bar=1, vel="f", bars=2)

    # 8. Oswin holds the Crack ---------------------------------------------------------------
    h = s.section("8 oswin holds", bars=4, meter=5, seconds=SLOTS[7])
    h.part("vc_spic", rep(HOLLOW_OST, 4), vel="ff")
    h.part("cb_spic", rep(HOLLOW_OST, 4), vel="ff", transpose=-12)
    h.part("vla_spic", rep(HOLLOW_OST, 4), vel="f", transpose=12)
    tune = "D4:2 A4:3 | G4:1.5 F#4:.5 E4:1 A4:2 | Bb4:2 A4:1 G4:1 F4:1 | G4:2 A4:3"
    h.part("hn_solo", tune, vel="ff")
    h.part("vln", tune, vel="f", transpose=12)
    h.part("tpt", "r:5 | r:5 | D5+F5:5 | C5+E5:2 C#5+E5:3", vel="f")
    h.part("tbn", "F#3+A3:5 | E3+G3:3 E3+A3:2 | F3+Bb3:5 | E3+G3:2 E3+A3:3", vel="ff")
    h.part("tuba", "D2:5 | C2:3 A1:2 | Bb1:5 | C2:2 A1:3", vel="ff")
    h.part("choir", "D4+F#4:5 | C4+E4+G4:3 C#4+E4+A4:2 | D4+F4+Bb4:5 | C4+E4+G4:2 C#4+E4+A4:3", vel="f")
    h.part("choir_hi", "r:5 | r:5 | D5:5 | E5:5", vel="f")
    s.swell("choir", [(h.at(1), -4), (h.at(3), 0), (h.at(4, 5), 4)])
    s.swell("tpt", [(h.at(3), -3), (h.at(4, 5), 4)])
    h.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="ff", bars=3)
    h.hits("bd", "1 2.5 4", bar=1, vel="ff", bars=3)
    h.hits("anvil", "4.5", bar=1, vel="f", bars=3)
    h.hits("crash", "1", bar=1, vel="f")
    h.hits("timp:A2", [1 + i * 0.25 for i in range(20)], bar=4, vel="f")
    h.hits("bd", [1 + i * 0.5 for i in range(10)], bar=4, vel="f")

    # 9. The blast of light; he falls; the lantern goes out ---------------------------------
    k = s.section("9 the fall", bars=3, meter=4, seconds=SLOTS[8], rit=0.7)
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
    s.swell("cb", [(k.at(2), -16), (k.at(3, 4), -24)])
    s.swell("solo_vln", [(k.at(1, 3.5), 0), (k.at(3, 4), -8)])
    k.hits("gong", "1", bar=1, vel="fff")
    k.hits("crash", "1", bar=1, vel="ff")
    k.hits("sus_cym", "1", bar=1, vel="f")
    k.hits("timp:D2", "1", bar=1, vel="fff")
    k.hits("bd", "1", bar=1, vel="fff")

    # 10. The Wardens go mad; the hordes march -----------------------------------------------
    m = s.section("10 the wardens", bars=4, meter=5, seconds=SLOTS[9])
    m.part("vc_spic", rep(HOLLOW_OST, 4), vel="ff")
    m.part("cb_spic", rep(HOLLOW_OST, 4), vel="ff", transpose=-12)
    m.part("vla_spic", rep(HOLLOW_OST, 4), vel="f", transpose=12)
    m.part("hn_solo", HOLLOW, vel="ff")
    m.part("tpt", HOLLOW, vel="f", transpose=12)
    m.part("tbn", HOLLOW, vel="ff", transpose=-12)
    m.part("tuba", HOLLOW, vel="ff", transpose=-24)
    m.part("choir", "D3+A3:3 D3+Ab3:2 | D3+G3:3 Eb3+G3:2 | D3+A3:3 D3+Bb3:2 | C#3+A3:3 D3+Ab3:2", vel="f")
    m.part("choir_hi", "r:5 | Eb5:2.5 D5:2.5 | r:5 | Eb5:2.5 D5:2.5", vel="ff")
    m.part("vln_trem", "D5+D6:5 | Eb5+Eb6:5 | D5+D6:5 | C#5+C#6:5", vel="f")
    m.hits("bd", "1 2.5 4", bar=1, vel="ff", bars=4)
    m.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="ff", bars=4)
    m.hits("anvil", "4.5", bar=1, vel="f", bars=4)
    m.hits("crash", "1", bar=1, vel="f", bars=4)

    # 11. The refugee road: hold the road ----------------------------------------------------
    n = s.section("11 the road", bars=4, meter=4, seconds=SLOTS[10])
    n.part("vln", "B4:2 F#5:2 | E5:1.5 D5:.5 C#5 B4 | G4:2 C#5 D5 | E5:4", vel="f")
    n.part("vla", "D4+F#4:2 D4+F#4:2 | D4+G4:2 C#4+F#4:2 | E4+G4:2 C#4+E4:2 | C#4+E4:4", vel="mp")
    n.part("vc", "B2:2 A2:2 | G2:2 F#2:2 | E2:2 A2:2 | A2:4", vel="mf")
    n.part("cb", "B1:2 A1:2 | G1:2 F#1:2 | E1:2 A1:2 | A1:4", vel="mf")
    n.part("hn", "r:4 | r:4 | G3+B3:2 A3+C#4:2 | A3+C#4+E4:4", vel="mp")
    n.part("oohs", "D4+F#4:4 | D4+G4:2 C#4+F#4:2 | E4+G4:2 C#4+E4:2 | C#4+E4+A4:4", vel="mp")
    n.part("choir", "r:4 | r:4 | r:4 | A3+C#4+E4:4", vel="mf")
    s.swell("vln", [(n.at(1), 0), (n.at(4), 2), (n.at(4, 4), 5)])
    s.swell("hn", [(n.at(3), -4), (n.at(4, 4), 4)])
    s.swell("choir", [(n.at(4), -8), (n.at(4, 4), 4)])
    n.hits("timp:A2", [1 + i * 0.25 for i in range(16)], bar=4, vel="f")

    # 12. The Queen on the walls: "Hold the road." Title. ------------------------------------
    q = s.section("12 hold the road", bars=5, meter=4, seconds=SLOTS[11] - FINAL_TAIL, rit=0.8)
    melody = "D5:2 A5:2 | B5:1.5 A5:.5 G5 F#5 | G5:1.5 F#5:.5 E5 C#5 | D5:4 | D5:4"
    q.part("vln", melody, vel="ff")
    q.part("tpt", melody, vel="ff")
    q.part("ob", melody, vel="f")
    q.part("fl", melody, vel="f", transpose=12)
    q.part("hn_solo", melody, vel="ff", transpose=-12)
    q.part("hn", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4+D5:4", vel="ff")
    q.part("tbn", "D3+A3:4 | D3+G3:2 D3+A3:2 | E3+B3:2 C#3+G3:2 | D3+A3:4 | D3+F#3+A3:4", vel="ff")
    q.part("tuba", "D2:4 | G1:2 F#2:2 | E2:2 A1:2 | D2:4 | D2:4", vel="ff")
    q.part("vla", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4:4", vel="f")
    q.part("vln2", "A4+D5:4 | B4+D5:2 A4+D5:2 | B4+E5:2 A4+E5:2 | A4+D5:4 | A4+D5+F#5:4", vel="f")
    q.part("vc", "D3:4 | G2:2 F#2:2 | E2:2 A2:2 | D3:4 | D3:4", vel="ff")
    q.part("cb", "D2:4 | G1:2 F#1:2 | E1:2 A1:2 | D2:4 | D2:4", vel="f")
    q.part("choir", "A3+D4+F#4+A4:4 | B3+D4+G4+B4:2 A3+D4+F#4+A4:2 | B3+E4+G4+B4:2 A3+C#4+E4+G4:2 | "
                    "A3+D4+F#4+A4:4 | A3+D4+F#4+A4:4", vel="f")
    q.part("choir_hi", "F#5:4 | G5:2 F#5:2 | G5:2 E5:2 | F#5:4 | A5:4", vel="ff")
    q.part("bells", "D4:4 | G3:2 F#3:2 | E3:2 A3:2 | D4:4 | D4:4", vel="f")
    q.part("harp", "r:4 | r:4 | r:4 | D3:.25 F#3:.25 A3:.25 D4:.25 F#4:.25 A4:.25 D5:.25 F#5:.25 A5:2 | r:4",
           vel="f")
    q.hits("sus_cym", "1", bar=1, vel="mf")
    q.hits("timp:D2", "1", bar=1, vel="fff")
    q.hits("crash", "1", bar=1, vel="ff")
    q.hits("bd", "1", bar=1, vel="ff")
    q.hits("timp:A2", "1 3", bar=2, vel="f")
    q.hits("timp:A2", "1 3", bar=3, vel="f")
    q.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=4, vel="f")
    q.hits("sus_cym", "1", bar=5, vel="f")
    q.hits("timp:D2", "1", bar=5, vel="fff")
    q.hits("crash", "1", bar=5, vel="ff")
    q.hits("gong", "1", bar=5, vel="ff")
    q.hits("bd", "1", bar=5, vel="fff")
    s.end_pad = FINAL_TAIL
    return s
