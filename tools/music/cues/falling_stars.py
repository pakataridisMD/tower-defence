"""The Night of Falling Stars: the midpoint (`night_of_falling_stars`), about 2:05.
One section per shot of the script. The darkest cue: Solenne's tune, betrayal, Fennick's
stand, the sun broken, and one shard of hope drifting east.
"""
from cues._kit import DEFEAT_A, HOLLOW, HOLLOW_OST, new, rep


def build():
    s = new("falling_stars", "The Night of Falling Stars")

    # 1. Solenne at dusk, still bright
    a = s.section("1 still bright", bars=5, meter=3, bpm=96)
    a.part("celesta", "F5:1 G5:.5 A5:1 C6:.5 | D6:1.5 C6:1 A5:.5 | G5:1 A5:.5 F5:1 D5:.5 | C5:1.5 F5:1 G5:.5 | "
                      "A5:3", vel="mp")
    a.part("fl", "r:3 | r:3 | r:3 | r:3 | A5:3", vel="p")
    a.part("harp", "F2+C3+A3:3 | Bb1+F2+D3:3 | G2+D3+Bb3:3 | C2+G2+E3:3 | F2+C3+A3:3", vel="mp")
    a.part("vla", "C4:3 | D4:3 | D4:3 | C4:3 | C4:3", vel="pp")
    a.part("vln2", "A4:3 | Bb4:3 | Bb4:3 | G4:3 | A4:3", vel="pp")
    a.part("vc", "F3:3 | Bb2:3 | G2:3 | C3:3 | F2:3", vel="pp")

    # 2. The Dawn Gate opens from the inside
    b = s.section("2 the gate opens", bars=2, meter=5, bpm=76)
    b.part("hn", "D3+Ab3+D4:2> r:3 | r:5", vel="ff")
    b.part("tbn", "D2+Ab2:2> r:3 | r:5", vel="ff")
    b.part("tuba", "D1:2 r:3 | r:5", vel="ff")
    b.part("vc_spic", "r:5 | " + HOLLOW_OST, vel="mp")
    b.part("cb_spic", "r:5 | " + HOLLOW_OST, vel="mp", transpose=-12)
    b.part("vln_trem", "D5+Eb5:10", vel="p")
    b.hits("gong", "1", bar=1, vel="f")
    b.hits("timp:D2", "1", bar=1, vel="ff")
    b.hits("timp:D2", "1 2.5 4 4.5", bar=2, vel="mf")

    # 3. Fighting in the streets
    c = s.section("3 the streets", bars=3, meter=5, bpm=84)
    c.part("vc_spic", rep(HOLLOW_OST, 3), vel="f")
    c.part("cb_spic", rep(HOLLOW_OST, 3), vel="f", transpose=-12)
    c.part("vla_spic", rep(HOLLOW_OST, 3), vel="mf", transpose=12)
    c.part("hn_solo", " | ".join(HOLLOW.split(" | ")[:3]), vel="f")
    c.part("tbn", " | ".join(HOLLOW.split(" | ")[:3]), vel="f", transpose=-12)
    c.part("choir", "D3+A3:3 D3+Ab3:2 | D3+G3:3 Eb3+G3:2 | D3+A3:5", vel="mf")
    c.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="f", bars=3)
    c.hits("bd", "1 4", bar=1, vel="mf", bars=3)
    c.hits("anvil", "4.5", bar=1, vel="mf", bars=3)

    # 4. Fennick holds the gate
    d = s.section("4 fennick holds", bars=4, meter=4, bpm=96)
    ost4 = "D3:.5> D3:.5 D3:.5 D3:.5 D3:.5> D3:.5 D3:.5 D3:.5"
    d.part("vc_spic", rep(ost4, 4), vel="f")
    d.part("cb_spic", rep(ost4, 4), vel="f", transpose=-12)
    d.part("hn_solo", DEFEAT_A, vel="ff")
    d.part("vln", DEFEAT_A, vel="f", transpose=12)
    d.part("vla", "F3+A3:4 | G3+Bb3:2 G3+C#4:2 | F3+Bb3:2 G3+C4:2 | E3+A3:4", vel="mf")
    d.part("tbn", "D3+F3:4 | D3+G3:2 C#3+E3:2 | D3+F3:2 C3+E3:2 | C#3+E3:4", vel="mf")
    d.part("tuba", "D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4", vel="mf")
    d.hits("timp:D2", "1 3", bar=1, vel="f", bars=2)
    d.hits("timp:A2", "1 2 3 4", bar=3, vel="f", bars=2)
    d.hits("bd", "1", bar=1, vel="f")

    # 5. "Spirewright! Fire burns, water slows..."
    e = s.section("5 fennick's words", bars=3, meter=4, bpm=96)
    e.part("hn", "A3+D4+F4:4 | Bb3+D4+G4:4 | A3+C#4+E4:4", vel="mf")
    e.part("vc_trem", "D3:4 | G2:4 | A2:4", vel="mp")
    e.part("cb", "D2:4 | G1:4 | A1:4", vel="mp")
    e.part("vln_trem", "F5+A5:4 | G5+Bb5:4 | E5+A5:4", vel="p")
    s.swell("vln_trem", [(e.at(1), -6), (e.at(3, 4), 4)])
    s.swell("hn", [(e.at(1), -4), (e.at(3, 4), 4)])
    e.hits("timp:A2", [1 + i * 0.25 for i in range(16)], bar=3, vel="mf")

    # 6. The gatehouse falls. Silence. A lament.
    f = s.section("6 the gatehouse falls", bars=2, meter=5, bpm=60)
    f.part("hn", "D3+A3+D4:1> r:4 | r:5", vel="fff")
    f.part("tbn", "D2+A2:1> r:4 | r:5", vel="fff")
    f.part("vc", "D2+D3:1 r:4 | r:5", vel="ff")
    f.part("cb", "D2:1 r:4 | D2:5", vel="ff")
    f.part("ob", "r:1.5 D5:1.5 A5:2 | G5:1.5 F5:.5 E5:1 D5:2", vel="mp")
    f.part("vla", "r:1.5 F4:3.5 | Bb3:2.5 A3:2.5", vel="pp")
    f.part("vc_solo", "r:1.5 D3:3.5 | G2:2.5 A2:2.5", vel="pp")
    s.swell("cb", [(f.at(1, 2), -18), (f.at(2, 5), -24)])
    f.hits("crash", "1", bar=1, vel="ff")
    f.hits("bd", "1", bar=1, vel="ff")
    f.hits("timp:D2", "1", bar=1, vel="fff")
    f.hits("gong", "1", bar=1, vel="f")

    # 7. The Lord Marshal on the Spire of Aurel
    g = s.section("7 the spire", bars=3, meter=4, bpm=72)
    g.part("vc", "B2:2 F#3:2 | E3:1.5 D3:.5 C#3 B2 | G2:2 C#3 D3", vel="mf")
    g.part("cb", "B1:4 | E1:2 F#1:2 | G1:4", vel="mp")
    g.part("vln_trem", "B5+C6:4 | C6+D6:4 | D6+Eb6:4", vel="p")
    g.part("choir", "B3+F#4:4 | C4+G4:4 | D4+Ab4:4", vel="mp")
    g.part("tbn", "r:4 | r:4 | G2+Db3:4", vel="mp")
    s.swell("vln_trem", [(g.at(1), -6), (g.at(3, 4), 6)])
    s.swell("choir", [(g.at(1), -6), (g.at(3, 4), 6)])
    g.hits("sus_cym", "1", bar=1, vel="f")  # its peak lands on the shatter below
    g.hits("timp:G2", [1 + i * 0.25 for i in range(16)], bar=3, vel="mf")

    # 8. "...and he broke the sun"
    h = s.section("8 the sun breaks", bars=1, meter=4, bpm=60)
    h.part("tpt", "D5+Eb5:1.5> r:2.5", vel="fff")
    h.part("hn", "D4+Ab4+D5:1.5 r:2.5", vel="fff")
    h.part("tbn", "D3+Ab3:1.5 r:2.5", vel="fff")
    h.part("tuba", "D2:1.5 r:2.5", vel="fff")
    h.part("vln", "D6+Eb6:1.5 r:2.5", vel="fff")
    h.part("choir", "D4+Ab4+D5+Eb5:1.5 r:2.5", vel="fff")
    # the shards falling like stars
    h.part("celesta", "r:.5 D7:.25 A6:.25 F6:.25 D6:.25 Bb5:.25 A5:.25 F5:.25 D5:.25 A4:.25 F4:.25 D4:1", vel="f")
    h.part("glock", "r:.75 C8:.25 A7:.25 F7:.25 D7:.25 Bb6:.25 A6:.25 F6:.25 D6:.25 A5:1", vel="mf")
    h.part("harp", "r:1 D6:.125 A5:.125 F5:.125 D5:.125 A4:.125 F4:.125 D4:.125 A3:.125 F3:.125 D3:.125 "
                   "A2:.125 F2:.125 D2:1.5", vel="f")
    h.hits("crash", "1", vel="ff")
    h.hits("gong", "1", vel="fff")
    h.hits("timp:D2", "1", vel="fff")
    h.hits("bd", "1", vel="ff")

    # 9. The light falls on the Queen. White-out.
    k = s.section("9 the queen", bars=2, meter=5, bpm=66)
    k.part("vln_trem", "D6+A6:10", vel="p")
    k.part("oohs", "D5+A5:10", vel="p")
    k.part("solo_vln", "A6:10", vel="pp")
    s.swell("vln_trem", [(k.at(1), 0), (k.at(2, 5), -16)])
    s.swell("oohs", [(k.at(1), 0), (k.at(2, 5), -14)])

    # 10. "There is a world without death, Ysolde..."
    m = s.section("10 the regent's promise", bars=3, meter=4, bpm=66)
    m.part("vc_solo", "B3:2 F#4:2 | E4:1.5 D4:.5 C#4 B3 | G3:2 C4:1 B3:1", vel="mf")
    m.part("vla", "D4:4 | G3:2 F#3:2 | Eb3:4", vel="pp")
    m.part("cb", "B1:4 | E1:2 B1:2 | C2:4", vel="pp")
    m.part("bsn", "r:4 | r:4 | Ab2:4", vel="p")
    m.part("choir", "r:4 | r:4 | C3+G3:4", vel="p")

    # 11. One shard drifts east, and does not land
    n = s.section("11 one shard", bars=4, meter=4, bpm=72)
    n.part("celesta", "D6:2 A6:2 | G6:1.5 F#6:.5 E6 D6 | r:4 | r:4", vel="mp")
    n.part("solo_vln", "r:4 | r:4 | D6:2 A6:2 | A6:4", vel="pp")
    n.part("vln2", "F#5+A5:4 | G5+B5:4 | F#5+A5:4 | F#5+A5:4", vel="ppp")
    n.part("vla", "D5:4 | D5:4 | D5:4 | D5:4", vel="ppp")
    n.part("harp", "D3:.5 A3:.5 D4:.5 F#4:.5 A4:2 | G2:.5 D3:.5 G3:.5 B3:.5 D4:2 | D3:.5 A3:.5 D4:.5 F#4:.5 A4:2 |"
                   " r:4", vel="p")
    s.swell("vln2", [(n.at(1), -4), (n.at(4, 4), -14)])

    # 12. When the sun should have risen, it did not.
    q = s.section("12 no dawn", bars=2, meter=4, bpm=60)
    q.part("cb", "D2:8", vel="p")
    q.part("vc", "D3+A3:8", vel="pp")
    q.part("tbn", "D3+F3:4 D3+Ab3:4", vel="pp")
    q.part("choir", "D3+A3:4 D3+Ab3:4", vel="pp")
    q.part("bsn", "F2:8", vel="pp")
    q.hits("timp:D2", "1", bar=1, vel="p")
    q.hits("gong", "1", bar=2, vel="p")
    s.end_pad = 7.0
    return s
