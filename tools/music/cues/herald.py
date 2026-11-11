"""The Heralds: the Hollow theme for the Herald scenes (`ember_herald` .. `void_herald`),
`crossroads` and boss reveals. About 0:50. 5/4.
"""
from cues._kit import HOLLOW, HOLLOW_OST, new, rep, film


def build():
    s = new("herald", "The Heralds of the Hollow")
    s.track("hn_solo", gain_db=0)

    a = s.section("dread", bars=2, meter=5, bpm=78)
    a.part("cb", "D2:10", vel="p")
    a.part("vc_trem", "D3:10", vel="pp")
    a.part("choir", "D3+A3:5 | D3+Ab3:5", vel="p")
    a.part("bsn", "r:5 | Ab2:5", vel="p")
    a.part("vln_trem", "r:5 | D6+Eb6:5", vel="ppp")
    s.swell("vc_trem", [(a.at(1), -12), (a.at(2, 5), 0)])
    a.hits("gong", "1", bar=1, vel="p")

    b = s.section("ostinato", bars=2, meter=5, bpm=78)
    b.part("vc_spic", rep(HOLLOW_OST, 2), vel="mf")
    b.part("cb_spic", rep(HOLLOW_OST, 2), vel="mf", transpose=-12)
    b.part("choir", "D3+A3:5 | D3+Ab3:5", vel="mp")
    b.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="mf", bars=2)

    c = s.section("hollow", bars=4, meter=5, bpm=78)
    c.part("vc_spic", rep(HOLLOW_OST, 4), vel="f")
    c.part("cb_spic", rep(HOLLOW_OST, 4), vel="f", transpose=-12)
    c.part("hn_solo", HOLLOW, vel="f")
    c.part("tbn", HOLLOW, vel="f", transpose=-12)
    c.part("tuba", HOLLOW, vel="mf", transpose=-24)
    c.part("choir", "D3+A3:3 D3+Ab3:2 | D3+G3:3 Eb3+G3:2 | D3+A3:3 D3+Bb3:2 | C#3+A3:3 D3+Ab3:2", vel="mf")
    c.part("vln_trem", "D5:5 | Eb5:5 | D5:5 | Eb5:5", vel="p")
    c.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="f", bars=4)
    c.hits("anvil", "4.5", bar=2, vel="mf", bars=3)

    d = s.section("hollow, full", bars=4, meter=5, bpm=78)
    d.part("vc_spic", rep(HOLLOW_OST, 4), vel="ff")
    d.part("cb_spic", rep(HOLLOW_OST, 4), vel="ff", transpose=-12)
    d.part("vla_spic", rep(HOLLOW_OST, 4), vel="f", transpose=12)
    d.part("tpt", HOLLOW, vel="f", transpose=12)
    d.part("vln", HOLLOW, vel="ff", transpose=12)
    d.part("hn_solo", HOLLOW, vel="ff")
    d.part("tbn", HOLLOW, vel="ff", transpose=-12)
    d.part("tuba", HOLLOW, vel="f", transpose=-24)
    d.part("choir", "D3+A3+D4:3 D3+Ab3+D4:2 | D3+G3+Bb3:3 Eb3+G3+Bb3:2 | D3+A3+D4:3 D3+Bb3+D4:2 | "
                    "C#3+A3+E4:3 D3+Ab3+D4:2", vel="f")
    d.part("choir_hi", "r:5 | Eb5:2.5 D5:2.5 | r:5 | Eb5:2.5 D5:2.5", vel="ff")
    d.hits("bd", "1 2.5 4", bar=1, vel="f", bars=4)
    d.hits("timp:D2", "1 2.5 4 4.5", bar=1, vel="ff", bars=4)
    d.hits("anvil", "4.5", bar=1, vel="f", bars=4)
    d.hits("crash", "1", bar=1, vel="f")
    d.hits("sus_cym", "1", bar=1, vel="mf")

    e = s.section("strike", bars=1, meter=5, bpm=78)
    e.part("hn", "D3+Ab3+D4:1.5> r:3.5", vel="fff")
    e.part("tbn", "D2+Ab2:1.5> r:3.5", vel="fff")
    e.part("tuba", "D1:1.5 r:3.5", vel="fff")
    e.part("vln", "D5+Eb5+D6:1.5 r:3.5", vel="fff")
    e.part("vc", "D2+D3:1.5 r:3.5", vel="fff")
    e.part("cb", "D2:1.5 r:3.5", vel="fff")
    e.part("choir", "D3+Ab3+D4+Eb4:1.5 r:3.5", vel="ff")
    e.hits("gong", "1", vel="fff")
    e.hits("timp:D2", "1", vel="fff")
    e.hits("bd", "1", vel="ff")
    # film-trailer layer
    film(s, a, "D2:10", "calm")
    film(s, b, "D2:10", "build")
    film(s, c, "D2:20", "drive", melody=HOLLOW)
    film(s, d, "D2:20", "drive", melody=HOLLOW, mel_transpose=-24)
    film(s, e, "D2:5", "hit")
    s.end_pad = 7.0
    return s
