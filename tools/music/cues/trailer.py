"""Trailer cue for the 48 s teaser: quiet 3 s intro, a pulse that builds under the gameplay
montage, a riser from 0:40, the big hit at 0:42 on the logo card, ring-out to 0:48.
`build_short()` is the 23 s cut for the vertical short (hit at 0:19).
"""
from cues._kit import DEFEAT_A, DEFEAT_B, new, rep, ost16

PULSE = "D3:.5> D3:.5 D3:.5 D3:.5 D3:.5> D3:.5 D3:.5 D3:.5"
HOLLOW4 = "D3:.5> D3:.5 D3:.5 Eb3:.5> D3:.5 D3:.5 C3:.5> Ab2:.5"


def _intro(s, seconds):
    a = s.section("intro", bars=1, meter=4, seconds=seconds)
    a.part("cb", "D2:4", vel="p")
    a.part("vc", "D3+A3:4", vel="pp")
    a.part("celesta", "r:1 A5:1 D6:2", vel="mp")
    a.hits("gong", "1", vel="p")


def _riser_and_hit(s, riser_s, ring_s):
    r = s.section("riser", bars=1, meter=4, seconds=riser_s)
    r.part("vln_trem", "F5+Bb5+D6:2 G5+C6+E6:1 A5+C#6+E6:1", vel="f")
    r.part("hn", "Bb3+D4+F4:2 C4+E4+G4:1 C#4+E4+A4:1", vel="ff")
    r.part("tbn", "Bb2+F3:2 C3+G3:1 A2+E3:1", vel="ff")
    r.part("choir", "Bb3+D4+F4:2 C4+E4+G4:1 C#4+E4+A4:1", vel="ff")
    r.part("cb", "Bb1:2 C2:1 A1:1", vel="f")
    r.hits("timp:A2", [1 + i * 0.25 for i in range(16)], vel="f")
    r.hits("snare_roll", "1", vel="mf")
    s.swell("vln_trem", [(r.at(1), -8), (r.at(1, 4.9), 4)])
    s.swell("choir", [(r.at(1), -6), (r.at(1, 4.9), 4)])
    h = s.section("hit", bars=2, meter=4, seconds=ring_s)
    h.part("tpt", "D5+F#5+A5:3 r:5", vel="fff")
    h.part("hn", "D4+F#4+A4+D5:3 r:5", vel="fff")
    h.part("hn_solo", "D4:3 r:5", vel="fff")
    h.part("tbn", "D3+A3:3 r:5", vel="fff")
    h.part("tuba", "D2:3 r:5", vel="fff")
    h.part("vln", "D5+A5+D6:3 r:5", vel="fff")
    h.part("vla", "F#4+A4:3 r:5", vel="fff")
    h.part("vc", "D3+A3:3 r:5", vel="fff")
    h.part("cb", "D2:3 r:5", vel="ff")
    h.part("choir", "D4+F#4+A4+D5:3 r:5", vel="fff")
    h.part("choir_hi", "F#5+A5:3 r:5", vel="fff")
    h.part("bells", "D4:8", vel="f")
    h.part("celesta", "r:4 A6:1 F#6:1 D6:2", vel="mp")
    h.hits("gong", "1", vel="fff")
    h.hits("crash", "1", vel="ff")
    h.hits("sus_cym", "1", vel="f")
    h.hits("timp:D2", "1", vel="fff")
    h.hits("bd", "1", vel="fff")
    s.end_pad = 0.01


def _film(s, p, bars, bass, horn, drive, horn_transpose=-12):
    """Hybrid film-trailer layer over the pulse section: synth pulse from the start, then from bar
    `drive` a 16th-note string ostinato, synth bass, drum ensemble and the army chanting; shouts on
    the last three downbeats. `bass` is the root line, `horn` the part for eight low horns."""
    from cues._kit import _in_range, _map, name
    from cues.prologue import chant, shout

    low = _map(bass, lambda m: name(_in_range(m, 38)))
    sub = _map(bass, lambda m: name(_in_range(m, 26)))
    pad = _map(bass, lambda m: "+".join(name(_in_range(m, 50) + k) for k in (0, 7, 12)))
    p.part("syn_pulse", ost16(low, 4), vel="ff")
    p.part("syn_sub", sub, vel="ff")
    p.part("syn_pad", pad, vel="f")
    p.part("hn_lo", horn, vel="ff", transpose=horn_transpose)
    p.part("vc_spic16", ost16(low, 4), vel="ff")
    p.part("cb_spic16", ost16(low, 4), vel="ff", transpose=-12)
    p.part("syn_bass", low, vel="ff")
    end = p.at(bars, 4)
    s.swell("syn_pulse", [(p.at(1), -12), (p.at(drive), 0), (end, 3)])
    s.swell("syn_pad", [(p.at(1), -16), (end, 0)])
    for k in ("vc_spic16", "cb_spic16", "syn_bass"):
        s.swell(k, [(p.at(1), -60), (p.at(drive) - 0.05, -60), (p.at(drive), -3), (end, 2)])
    if drive > 4:
        p.hits("taiko", "1 3", bar=drive - 4, vel="f", bars=4)
    p.hits("epic", "1", bar=drive, vel="fff", bars=bars - drive + 1)
    p.hits("taiko", "2.5 3 4.5", bar=drive, vel="ff", bars=bars - drive + 1)
    p.hits("snare", [1 + i * 0.25 for i in range(16) if i % 4 in (0, 3)], bar=bars - 2, vel="f", bars=3)
    p.hits("toms", [1 + i * 0.25 for i in range(16)], bar=bars, vel="ff")
    words = "Teh:D3:.5 Neh:D3:.5 Teh:D3:1 Vee:D3:1 Ahm:D3:1"
    for b in range(drive, bars - 2):
        chant(s, p, b, words, men=14, gain=-2, seed=100 + b)
    for i, b in enumerate(range(bars - 2, bars + 1)):
        shout(s, p.at(b), "Ha!", gain=-2, seed=10 + i)


def _film_hit(s):
    from cues.prologue import hit, rise, shout

    r, h = s.sections[-2], s.sections[-1]
    r.hits("toms", [1 + i * 0.25 for i in range(16)], vel="fff")
    rise(s, h.at(1), s.time_of(h.at(1)) - s.time_of(r.at(1)), gain=2)
    h.part("syn_bass", "D2:3 r:5", vel="fff")
    h.part("syn_sub", "D1:8", vel="fff")
    h.hits("epic", "1", vel="fff")
    shout(s, h.at(1), "Hey!", gain=0, seed=3, n=20, women=6)
    hit(s, h.at(1), "D2", gain=4, seed=9)


def build():
    s = new("trailer", "Hold the Road (trailer)")
    for k in ["hn", "tbn", "tuba", "tpt"]:
        s.tracks[k].gain_db += 2
    s.track("choir", gain_db=-7)
    _intro(s, 3.0)

    p = s.section("pulse", bars=15, meter=4, seconds=37.0)
    # bars 1-4: the pulse alone, then drums
    # bars 5-8: the Lantern in the minor on horns
    # bars 9-12: strings take it, choir and brass join
    # bars 13-15: the Hollow pushes back, everything climbs
    p.part("vc_spic", rep(PULSE, 12) + " | " + rep(HOLLOW4, 3), vel="mf")
    p.part("cb_spic", rep(PULSE, 12) + " | " + rep(HOLLOW4, 3), vel="mf", transpose=-12)
    p.part("vla_spic", "r:4 | r:4 | " + rep(PULSE, 10) + " | " + rep(HOLLOW4, 3), vel="mp", transpose=12)
    p.part("hn_solo", "r:4 | r:4 | r:4 | r:4 | " + DEFEAT_A + " | r:4 | r:4 | r:4 | r:4 | D4:4 | Eb4:4 | E4:4",
           vel="f")
    p.part("vln", "r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | " + DEFEAT_B + " | D5:4 | Eb5:4 | E5:4",
           vel="f", transpose=0)
    p.part("hn", "r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | A3+D4:4 | Bb3+D4:4 | Bb3+D4:2 A3+C#4:2 | "
                 "A3+D4:4 | A3+D4:4 | Ab3+Eb4:4 | A3+E4:4", vel="f")
    p.part("tbn", "r:4 | r:4 | r:4 | r:4 | D3:4 | G2:2 A2:2 | Bb2:2 C3:2 | A2:4 | D3+A3:4 | G2+D3:4 | "
                  "G2+D3:2 A2+E3:2 | D3+A3:4 | D3+A3:4 | Eb3+Ab3:4 | E3+A3:4", vel="mf")
    p.part("choir", "r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | r:4 | A3+D4+F4:4 | Bb3+D4+G4:4 | "
                    "Bb3+D4+G4:2 A3+C#4+E4:2 | A3+D4+F4:4 | D3+A3+D4:4 | Eb3+Ab3+Eb4:4 | E3+A3+E4:4", vel="f")
    p.part("vln_trem", "D5:4 | D5:4 | D5:4 | D5:4", vel="pp")
    s.swell("vc_spic", [(p.at(1), -8), (p.at(5), 0), (p.at(15, 4), 3)])
    s.swell("cb_spic", [(p.at(1), -8), (p.at(5), 0), (p.at(15, 4), 3)])
    s.swell("choir", [(p.at(9), -4), (p.at(13), 0), (p.at(15, 4), 5)])
    p.hits("timp:D2", "1 3", bar=3, vel="mf", bars=6)
    p.hits("bd", "1", bar=5, vel="f", bars=4)
    p.hits("timp:D2", "1 2.5 3 4", bar=9, vel="f", bars=4)
    p.hits("bd", "1 2.5 3", bar=9, vel="f", bars=4)
    p.hits("crash", "1", bar=9, vel="f")
    p.hits("timp:D2", "1 1.5 2 2.5 3 3.5 4 4.5", bar=13, vel="ff", bars=3)
    p.hits("bd", "1 2 3 4", bar=13, vel="ff", bars=3)
    p.hits("anvil", "4.5", bar=13, vel="f", bars=3)
    p.hits("crash", "1", bar=13, vel="f")

    _film(s, p, 15, "D2:16 | D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4 | D2:4 | G1:4 | G1:2 A1:2 | D2:4 | "
                    "D2:4 | Eb2:4 | E2:4",
          "r:16 | " + DEFEAT_A + " | r:16 | D4:4 | Eb4:4 | E4:4", drive=9)
    _riser_and_hit(s, 2.0, 6.0)
    _film_hit(s)
    return s


def build_short():
    s = new("trailer_short", "Hold the Road (short)")
    for k in ["hn", "tbn", "tuba", "tpt"]:
        s.tracks[k].gain_db += 2
    s.track("choir", gain_db=-7)
    _intro(s, 1.5)
    p = s.section("pulse", bars=6, meter=4, seconds=15.5)
    p.part("vc_spic", rep(PULSE, 4) + " | " + rep(HOLLOW4, 2), vel="f")
    p.part("cb_spic", rep(PULSE, 4) + " | " + rep(HOLLOW4, 2), vel="f", transpose=-12)
    p.part("vla_spic", "r:4 | " + rep(PULSE, 3) + " | " + rep(HOLLOW4, 2), vel="mf", transpose=12)
    p.part("hn_solo", DEFEAT_A + " | D4:4 | E4:4", vel="ff")
    p.part("vln", "r:4 | r:4 | r:4 | r:4 | D5:4 | E5:4", vel="f")
    p.part("tbn", "D3:4 | G2:2 A2:2 | Bb2:2 C3:2 | A2:4 | Eb3+Ab3:4 | E3+A3:4", vel="mf")
    p.part("choir", "r:4 | r:4 | Bb3+D4+F4:2 C4+E4+G4:2 | A3+C#4+E4:4 | Eb3+Ab3+Eb4:4 | E3+A3+E4:4", vel="f")
    p.hits("timp:D2", "1 2.5 3 4", bar=1, vel="f", bars=4)
    p.hits("bd", "1 3", bar=1, vel="f", bars=4)
    p.hits("timp:D2", "1 1.5 2 2.5 3 3.5 4 4.5", bar=5, vel="ff", bars=2)
    p.hits("bd", "1 2 3 4", bar=5, vel="ff", bars=2)
    p.hits("crash", "1", bar=5, vel="f")
    _film(s, p, 6, "D2:4 | G1:2 A1:2 | Bb1:2 C2:2 | A1:4 | Eb2:4 | E2:4", DEFEAT_A + " | D4:4 | E4:4", drive=1)
    _riser_and_hit(s, 2.0, 4.0)
    _film_hit(s)
    return s
