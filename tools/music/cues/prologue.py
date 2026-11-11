"""The Last Lantern: score for the opening story video (`prologue`), about 2:25.

One section per shot of the script (docs/story/scripts.md), in the order the narrator reads them.
Themes introduced here and reused by the other cues (see themes.md):
  - the Lantern (hope, the Order, Oswin): D4 A4 | G4. F#8 E4 D4 | B3 E4 F#4 | ...
  - Solenne (home): a 6/8 folk tune for flute and harp
  - the Hollow (Vael-Orrun): a falling tritone in low brass over a 5/4 ostinato
"""
from score import Score

# 5/4 ostinato of the Hollow (eighths grouped 3+3+2+2)
OST = "D3:.5> D3:.5 D3:.5 D3:.5> D3:.5 Eb3:.5 D3:.5> D3:.5 C3:.5> Ab2:.5"


def ost(n):
    return " | ".join([OST] * n)


def build():
    s = Score("prologue", "The Last Lantern")
    # strings
    s.track("vln", pan=-0.45, attack=0.08, legato=1.06, release=0.6, gain_db=-1)
    s.track("vln2", inst="vln", pan=-0.2, attack=0.12, legato=1.06, release=0.6, gain_db=-4)
    s.track("vln_trem", pan=-0.3, attack=0.4, release=0.8, gain_db=-8)
    s.track("vla", pan=0.15, attack=0.12, legato=1.05, release=0.6, gain_db=-4)
    s.track("vc", pan=0.35, attack=0.1, legato=1.05, release=0.6, gain_db=-2)
    s.track("vc_solo", inst="vc", pan=0.2, attack=0.09, legato=1.08, release=0.7, gain_db=0)
    s.track("cb", pan=0.5, attack=0.12, double=1, release=0.6, gain_db=-3, hpf=36)
    s.track("vla_spic", pan=0.15, gain_db=-12)
    s.track("vc_spic", pan=0.35, gain_db=-9)
    s.track("cb_spic", pan=0.5, gain_db=-10, hpf=36)
    s.track("solo_vln", pan=-0.2, attack=0.6, release=1.2, gain_db=-8)
    # winds and brass
    s.track("fl", pan=-0.25, attack=0.05, legato=1.04, gain_db=-4)
    s.track("ob", pan=-0.1, attack=0.05, legato=1.04, gain_db=-6)
    s.track("cl", pan=0.1, attack=0.08, legato=1.04, gain_db=-6)
    s.track("bsn", pan=0.25, attack=0.06, gain_db=-5)
    s.track("hn", pan=-0.2, attack=0.07, legato=1.04, release=0.5, gain_db=-5)
    s.track("hn_solo", inst="hn", pan=-0.1, attack=0.06, legato=1.05, release=0.5, gain_db=2)
    s.track("tpt", pan=0.1, attack=0.03, legato=1.03, gain_db=-5)
    s.track("tbn", pan=0.3, attack=0.05, legato=1.03, gain_db=-5)
    s.track("tuba", pan=0.45, attack=0.05, legato=1.03, gain_db=-5)
    # colour
    s.track("harp", pan=-0.55, gain_db=-10)
    s.track("celesta", pan=-0.35, gain_db=-6)
    s.track("glock", pan=-0.4, gain_db=-12)
    s.track("choir", pan=0.0, legato=1.05, gain_db=-11)
    s.track("choir_hi", inst="choir", pan=-0.1, gain_db=-12)
    s.track("oohs", pan=0.05, gain_db=-7)

    # 1. The sea before the world ------------------------------------------------ ~13s
    a = s.section("1 sea", bars=3, meter=4, bpm=56)
    a.part("cb", "D2:12", vel="pp")
    a.part("vc", "D3+A3:12", vel="pp")
    a.part("vln_trem", "A5+D6:8 Bb5+D6:4", vel="ppp")
    a.part("oohs", "D4+A4:4 | D4+F4+Bb4:4 | D4+G4+Bb4:4", vel="p")
    a.part("harp", "D3:.5 A3:.5 D4:.5 E4:.5 F4:.5 A4:.5 D5:1 | Bb2:.5 F3:.5 Bb3:.5 D4:.5 F4:.5 Bb4:.5 D5:1 | "
                   "G2:.5 D3:.5 G3:.5 Bb3:.5 D4:.5 G4:.5 Bb4:1", vel="mp")
    s.swell("vln_trem", [(a.at(1), -18), (a.at(3, 4), 0)])
    s.swell("oohs", [(a.at(1), -12), (a.at(3, 4), 0)])
    s.swell("vc", [(a.at(1), -10), (a.at(2), 0)])

    # 2. Seven stepped out of the sea -------------------------------------------- ~10s
    b = s.section("2 seven", bars=2, meter=5, bpm=60)
    b.part("cb", "D2:5 | r:5", vel="p")
    b.part("vc", "D3:5 | r:5", vel="p")
    b.part("vla", "D4:5 | r:5", vel="pp")
    # six lights, one after another
    b.part("hn_solo", "D4:5", vel="mp")
    b.part("cl", "A4:4.25", bar=1, beat=1.75, vel="mp")
    b.part("fl", "F#5:3.5", bar=1, beat=2.5, vel="mp")
    b.part("ob", "E5:2.75", bar=1, beat=3.25, vel="p")
    b.part("vln", "A5:2", bar=1, beat=4, vel="p")
    b.part("celesta", "D5:.75 A5:.75 F#6:.75 E6:.75 A6:.75 D7:1.25", vel="mf")
    # the seventh: no colour at all
    b.part("tuba", "r:5 | Ab1:5", vel="mf")
    b.part("tbn", "r:5 | D3+Ab2:5", vel="mp")
    b.part("bsn", "r:5 | D2:5", vel="mp")
    b.part("vln_trem", "r:5 | D6+Eb6:5", vel="pp")
    b.part("choir", "r:5 | D3+Ab3:5", vel="p")
    b.hits("timp:D2", "1", bar=2, vel="mp")
    b.hits("sus_cym", "1", bar=1, vel="mp")

    # 3. Vael-Orrun. "They stopped." --------------------------------------------- ~10s
    c = s.section("3 vael-orrun", bars=2, meter=5, bpm=60)
    hollow = "D3:3 Ab2:2 | G2:1.5 Bb2:.5 A2:1 Eb3:1> r:1"
    c.part("hn", hollow, vel="f")
    c.part("tbn", hollow, vel="mf")
    c.part("tuba", hollow, vel="mf", transpose=-12)
    c.part("vc", "D2:5 | D2:4 r:1", vel="mp")
    c.part("cb", "D2:5 | D2:4 r:1", vel="mp")
    c.part("choir", "D3+A3:5 | D3+Ab3:4 r:1", vel="mp")
    s.swell("choir", [(c.at(1), -8), (c.at(2, 4), 0)])
    c.hits("timp:D2", "1", bar=1, vel="f")
    c.hits("timp:D2", "1", bar=2, vel="f")
    c.hits("timp:Eb2", "4", bar=2, vel="ff")
    c.hits("gong", "4", bar=2, vel="mf")

    # 4. The Six join hands: the Ring --------------------------------------------- ~15s
    d = s.section("4 the ring", bars=4, meter=4, bpm=66)
    d.part("hn_solo", "D4:2 A4:2 | G4:1.5 F#4:.5 E4 D4 | B3:2 E4 F#4 | D4:4", vel="mp")
    d.part("vln2", "F#4+A4:4 | G4+B4:4 | F#4+B4:2 E4+A4:2 | F#4+A4+D5:4", vel="p")
    d.part("vla", "D4:4 | D4:2 E4:2 | D4:2 C#4:2 | D4:4", vel="p")
    d.part("vc", "D3:4 | G2:2 E3:2 | B2:2 A2:2 | D3:4", vel="mp")
    d.part("cb", "D2:4 | G1:2 E2:2 | B1:2 A1:2 | D2:4", vel="mp")
    d.part("choir", "r:4 | r:4 | B3+F#4:2 A3+E4:2 | A3+D4+F#4:4", vel="mf")
    d.part("harp", "D3:.5 A3:.5 D4:.5 F#4:.5 A4:.5 D4:.5 F#4:.5 A4:.5 | G2:.5 D3:.5 G3:.5 B3:.5 E3:.5 B3:.5 "
                   "E4:.5 G4:.5 | B2:.5 F#3:.5 B3:.5 D4:.5 A2:.5 E3:.5 A3:.5 C#4:.5 | "
                   "D2:.25 A2:.25 D3:.25 F#3:.25 A3:.25 D4:.25 F#4:.25 A4:.25 D5:2", vel="mp")
    d.part("fl", "r:4 | r:4 | r:4 | A5:4", vel="p")
    s.swell("vln2", [(d.at(1), -4), (d.at(3), 0), (d.at(4), 4)])
    s.swell("vc", [(d.at(1), 0), (d.at(4), 3)])
    d.hits("timp:D2", "1", bar=4, vel="mf")
    d.hits("sus_cym", "1", bar=4, vel="p")

    # 5. Dawn over Solenne -------------------------------------------------------- ~8s
    e = s.section("5 solenne", bars=5, meter=3, bpm=108)
    e.part("fl", "D5:1 E5:.5 F#5:1 A5:.5 | B5:1.5 A5:1 F#5:.5 | E5:1 F#5:.5 D5:1 B4:.5 | A4:1.5 D5:1 E5:.5 | "
                 "F#5:3", vel="mp")
    e.part("harp", "D3:.5 A3:.5 D4:.5 F#4:.5 A4:.5 D4:.5 | G2:.5 D3:.5 G3:.5 B3:.5 D4:.5 G3:.5 | "
                   "E3:.5 B3:.5 D4:.5 G4:.5 D4:.5 B3:.5 | A2:.5 E3:.5 A3:.5 D4:.5 C#4:.5 E4:.5 | "
                   "D3:.5 A3:.5 D4:.5 F#4:1.5", vel="mp")
    e.part("cl", "F#4:3 | G4:3 | G4:3 | E4:3 | F#4:3", vel="pp")
    e.part("vla", "A3:3 | B3:3 | B3:3 | C#4:3 | A3:3", vel="pp")
    e.part("vc", "D3:3 | G2:3 | E3:3 | A2:3 | D3:3", vel="pp")
    e.part("glock", "r:3 | r:3 | r:3 | r:3 | D6:3", vel="p")

    # 6. The Regent, the locket, the promise -------------------------------------- ~13s
    f = s.section("6 regent", bars=4, meter=4, bpm=72)
    f.part("vc_solo", "B3:2 F#4:2 | E4:1.5 D4:.5 C#4 B3 | G3:2 C#4 D4 | C#4:4", vel="mp")
    f.part("bsn", "B2:4 | E3:2 D3:2 | G2:2 A2:2 | F#2:4", vel="p")
    f.part("cl", "D4:4 | G3:2 F#3:2 | B3:2 A3:2 | A#3:4", vel="pp")
    f.part("vla", "F#3:4 | B3:2 B3:2 | D4:2 E4:2 | C#4:4", vel="pp")
    f.part("cb", "B1:4 | E1:2 D2:2 | G1:2 A1:2 | F#1:4", vel="pp")
    f.part("celesta", "r:2 F#6:1 D6:1 | r:4 | r:4 | r:2 C#6:2", vel="p")
    f.part("harp", "B1+F#2:4 | r:4 | r:4 | F#1+C#2:4", vel="p")

    # 7. The Black Comet ---------------------------------------------------------- ~7s
    g = s.section("7 comet", bars=2, meter=5, bpm=84)
    g.part("vc_spic", ost(2), vel="mp")
    g.part("cb_spic", ost(2), vel="mp", transpose=-12)
    g.part("vln_trem", "D5+Eb5:5 | Ab5+A5:5", vel="pp")
    g.part("choir", "D3+A3:5 | D3+Ab3:5", vel="p")
    s.swell("vln_trem", [(g.at(1), -10), (g.at(2, 5), 2)])
    s.swell("vc_spic", [(g.at(1), -6), (g.at(2, 5), 0)])
    s.swell("cb_spic", [(g.at(1), -6), (g.at(2, 5), 0)])
    g.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="mf", bars=2)

    # 8. Oswin holds the Crack ---------------------------------------------------- ~11s
    h = s.section("8 oswin holds", bars=3, meter=5, bpm=84)
    h.part("vc_spic", ost(3), vel="f")
    h.part("cb_spic", ost(3), vel="f", transpose=-12)
    h.part("vla_spic", ost(3), vel="mf", transpose=12)
    h.part("hn_solo", "D4:2 A4:3 | G4:1.5 F#4:.5 E4:1 A4:2 | D5:5", vel="f")
    h.part("vln", "D5:2 A5:3 | G5:1.5 F#5:.5 E5:1 A5:2 | D6:5", vel="f")
    h.part("tpt", "r:5 | r:5 | D5:5", vel="f")
    h.part("tbn", "F#3+A3:5 | E3+G3:3 E3+A3:2 | F3+Bb3:5", vel="f")
    h.part("tuba", "D2:5 | C2:3 A1:2 | Bb1:5", vel="f")
    h.part("choir", "D4+F#4:5 | C4+E4+G4:3 C#4+E4+A4:2 | D4+F4+Bb4:5", vel="mf")
    s.swell("choir", [(h.at(1), -6), (h.at(3), 0), (h.at(3, 5), 4)])
    h.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="f", bars=2)
    h.hits("timp:Bb2", [1 + i * 0.25 for i in range(20)], bar=3, vel="mf")
    h.hits("sus_cym", "1", bar=1, vel="mf")

    # 9. The blast of light; he falls; the lantern goes out ----------------------- ~8s
    k = s.section("9 the fall", bars=2, meter=4, bpm=60)
    k.part("tpt", "D5+F#5:2.5 r:1.5 | r:4", vel="fff")
    k.part("hn", "D4+F#4+A4+D5:2.5 r:1.5 | r:4", vel="fff")
    k.part("tbn", "D3+A3:2.5 r:1.5 | r:4", vel="fff")
    k.part("tuba", "D2:2.5 r:1.5 | r:4", vel="fff")
    k.part("vln", "D5+A5+D6:2.5 r:1.5 | r:4", vel="fff")
    k.part("vla", "F#4+A4:2.5 r:1.5 | r:4", vel="fff")
    k.part("vc", "D3+A3:2.5 r:1.5 | r:4", vel="fff")
    k.part("cb", "D2:2.5 r:1.5 | D2:4", vel="ff")
    k.part("choir", "D4+F#4+A4+D5:2.5 r:1.5 | r:4", vel="fff")
    k.part("solo_vln", "r:3.5 A6:4.5", vel="ppp")
    k.part("celesta", "r:4 | A6:1 F#6:1 D6:1 A5:1", vel="p")
    s.swell("cb", [(k.at(2), -14), (k.at(2, 4), -20)])
    k.hits("gong", "1", bar=1, vel="fff")
    k.hits("sus_cym", "1", bar=1, vel="f")
    k.hits("crash", "1", bar=1, vel="ff")
    k.hits("timp:D2", "1", bar=1, vel="fff")
    k.hits("bd", "1", bar=1, vel="ff")

    # 10. The Wardens go mad; the hordes march ------------------------------------ ~12s
    m = s.section("10 the wardens", bars=3, meter=5, bpm=76)
    m.part("vc_spic", ost(3), vel="ff")
    m.part("cb_spic", ost(3), vel="ff", transpose=-12)
    m.part("vla_spic", ost(3), vel="f", transpose=12)
    m.part("hn_solo", "D4:3 Ab3:2 | G3:1.5 Bb3:.5 A3:1 Eb4:2 | D4:3 C4:1 Bb3:1", vel="ff")
    m.part("tbn", "D3:3 Ab2:2 | G2:1.5 Bb2:.5 A2:1 Eb3:2 | D3:3 C3:1 Bb2:1", vel="ff")
    m.part("tuba", "D2:3 Ab1:2 | G1:1.5 Bb1:.5 A1:1 Eb2:2 | D2:3 C2:1 Bb1:1", vel="ff")
    m.part("choir", "D3+A3:3 D3+Ab3:2 | D3+G3:3 Eb3+G3:2 | D3+A3:5", vel="f")
    m.part("choir_hi", "r:5 | r:5 | Eb5:2.5 D5:2.5", vel="ff")
    m.part("vln_trem", "D5+D6:5 | Eb5+Eb6:5 | D5+D6:5", vel="mf")
    m.hits("bd", "1 2.5 4", bar=1, vel="ff", bars=3)
    m.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="ff", bars=3)
    m.hits("anvil", "4.5", bar=1, vel="f", bars=3)
    m.hits("crash", "1", bar=3, vel="f")

    # 11. The refugee road: hold the road ----------------------------------------- ~13s
    n = s.section("11 the road", bars=4, meter=4, bpm=72)
    n.part("vln", "B4:2 F#5:2 | E5:1.5 D5:.5 C#5 B4 | G4:2 C#5 D5 | E5:4", vel="mf")
    n.part("vla", "D4+F#4:2 D4+F#4:2 | D4+G4:2 C#4+F#4:2 | E4+G4:2 C#4+E4:2 | C#4+E4:4", vel="mp")
    n.part("vc", "B2:2 A2:2 | G2:2 F#2:2 | E2:2 A2:2 | A2:4", vel="mp")
    n.part("cb", "B1:2 A1:2 | G1:2 F#1:2 | E1:2 A1:2 | A1:4", vel="mp")
    n.part("hn", "r:4 | r:4 | G3+B3:2 A3+C#4:2 | A3+E4:4", vel="p")
    n.part("oohs", "D4+F#4:4 | D4+G4:2 C#4+F#4:2 | E4+G4:2 C#4+E4:2 | C#4+E4+A4:4", vel="p")
    s.swell("vln", [(n.at(1), 0), (n.at(4), 2), (n.at(4, 4), 5)])
    s.swell("hn", [(n.at(3), -4), (n.at(4, 4), 3)])
    n.hits("timp:A2", [1 + i * 0.25 for i in range(16)], bar=4, vel="mp")

    # 12. The Queen on the walls: "Hold the road." Title. ------------------------- ~18s
    q = s.section("12 hold the road", bars=5, meter=4, bpm=63, end_bpm=52)
    melody = "D5:2 A5:2 | B5:1.5 A5:.5 G5 F#5 | G5:1.5 F#5:.5 E5 C#5 | D5:4 | D5:4"
    q.part("vln", melody, vel="ff")
    q.part("tpt", melody, vel="f")
    q.part("ob", melody, vel="f")
    q.part("fl", melody, vel="f", transpose=12)
    q.part("hn_solo", melody, vel="ff", transpose=-12)
    q.part("hn", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4+D5:4", vel="f")
    q.part("tbn", "D3+A3:4 | D3+G3:2 D3+A3:2 | E3+B3:2 C#3+G3:2 | D3+A3:4 | D3+F#3+A3:4", vel="ff")
    q.part("tuba", "D2:4 | G1:2 F#2:2 | E2:2 A1:2 | D2:4 | D2:4", vel="ff")
    q.part("vla", "F#4+A4:4 | G4+B4:2 F#4+A4:2 | G4+B4:2 E4+G4:2 | F#4+A4:4 | F#4+A4:4", vel="f")
    q.part("vln2", "A4+D5:4 | B4+D5:2 A4+D5:2 | B4+E5:2 A4+E5:2 | A4+D5:4 | A4+D5+F#5:4", vel="f")
    q.part("vc", "D3:4 | G2:2 F#2:2 | E2:2 A2:2 | D3:4 | D3:4", vel="ff")
    q.part("cb", "D2:4 | G1:2 F#1:2 | E1:2 A1:2 | D2:4 | D2:4", vel="ff")
    q.part("choir", "A3+D4+F#4+A4:4 | B3+D4+G4+B4:2 A3+D4+F#4+A4:2 | B3+E4+G4+B4:2 A3+C#4+E4+G4:2 | "
                    "A3+D4+F#4+A4:4 | A3+D4+F#4+A4:4", vel="ff")
    q.part("harp", "r:4 | r:4 | r:4 | D3:.25 F#3:.25 A3:.25 D4:.25 F#4:.25 A4:.25 D5:.25 F#5:.25 A5:2 | r:4",
           vel="f")
    q.hits("timp:D2", "1", bar=1, vel="ff")
    q.hits("timp:A2", "1 3", bar=3, vel="f")
    q.hits("timp:D2", [1 + i * 0.25 for i in range(16)], bar=4, vel="f")
    q.hits("timp:D2", "1", bar=5, vel="fff")
    q.hits("crash", "1", bar=5, vel="ff")
    q.hits("gong", "1", bar=5, vel="f")
    q.hits("bd", "1", bar=5, vel="ff")
    s.end_pad = 7.0
    return s
