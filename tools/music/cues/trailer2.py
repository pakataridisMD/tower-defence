"""Story trailer (v2) for the promo thread: dark, fast, heavy drums, no bells or chimes.

78 s, every event on a fixed time so the edit can cut to it:
  0:00-0:18  ominous low build under four narrated lines (0:01, 0:05.5, 0:09.5, 0:14.5)
  0:18.0     huge hit and braam: Vael-Orrun revealed
  0:18-0:54  160 bpm battle: grinding ostinato, war drums, eight horns, chant and shouts;
             accent hits for boss reveals at 0:24, 0:30, 0:36, 0:42 and 0:48
  0:54-1:06  breakdown: low strings and choir under three lines (0:55, 0:59, 1:02.5)
  1:06-1:10  riser; the army shouts "Light the towers!" at 1:06.5
  1:10.0     the final hit on the title, then the ring-out to 1:18
`trailer2_short` is the 30 s cut (hit at 0:24). Mastered to -16 LUFS: the promo ducks it under the voice.
"""
import vocals as V
from cues._kit import film, new
from cues.prologue import Span, chant, hit, rise, shout, sw
from loops.boss import HOLLOW4, drums, grind
from score import midi

LUFS = -16.0
DEFEAT = "D4:4 | A4:4 | Bb4:3 A4:1 | G4:2 F4:2 | G4:3 F4:1 | E4:2 C#4:2 | D4:4 | D4:4"


def setup(name, title):
    s = new(name, title)
    for k in ["hn", "tbn", "tuba", "tpt", "hn_lo"]:
        s.tracks[k].gain_db += 2
    s.tracks["hn_lo"].double = 3
    s.tracks["hn_solo"].double = 2
    s.tracks["vc_spic"].gain_db += 2
    s.tracks["cb_spic"].gain_db += 2
    s.track("choir", gain_db=-7)
    s.track("choir_hi", gain_db=-8)
    s.perc_db = -3.0
    return s


def low_build(s, bars, seconds):
    """A clock, a heartbeat and the Hollow whispered, with room for the voice (120 bpm)."""
    a = s.section("build", bars=bars, meter=4, seconds=seconds)
    a.part("cb", f"D2:{bars * 4}", vel="mp")
    a.part("vc", f"D3+A3:{bars * 4}", vel="p")
    a.part("vln_trem", f"D6+Eb6:{bars * 4}", vel="pp")
    a.part("choir", f"D3+Ab3:{bars * 4}", vel="mp")
    sw(s, a, "vln_trem", [(a.at(1), -20), (a.at(bars, 4), 0)])
    sw(s, a, "choir", [(a.at(1), -14), (a.at(bars, 4), 0)])
    a.hits("gong", "1", bar=1, vel="mf")
    hit(s, a.at(1), "D1", gain=-6, seed=21)
    a.hits("tick", [1 + i * 0.5 for i in range(8)], bar=1, vel="f", bars=bars)
    a.hits("taiko", "1", bar=2, vel="mf", bars=bars - 1)
    half = max(1, bars // 2)
    film(s, Span(a, 1, half), " | ".join(["D2:4"] * half), "calm")
    film(s, Span(a, half + 1, bars - half), " | ".join(["D2:4"] * (bars - half - 1) + ["A1:4"]), "build")
    a.part("hn_lo", "D3:3 Ab2:1 | G2:3 Eb3:1", bar=bars - 1, vel="ff")
    sw(s, a, "hn_lo", [(a.at(bars - 1), -10), (a.at(bars, 4), 0)])
    for i in range(bars):
        chant(s, a, i + 1, "Vail:D3:1.5 Or:D3:1 Run:Ab2:1.5", men=10, gain=-10, seed=500 + i)
    a.hits("toms", [3 + i * 0.25 for i in range(8)], bar=bars, vel="ff")
    rise(s, a.at(bars, 4) + 1, 2.5, gain=-2, seed=31)
    return a


BATTLE_BASS = ["D2:4 | D2:4 | Eb2:4 | D2:4", "D2:4 | D2:4 | Ab1:4 | A1:4",
               "D2:4 | D2:4 | Bb1:4 | A1:4", "D2:4 | Eb2:4 | Ab1:4 | A1:4",
               "Bb1:4 | C2:4 | Eb2:4 | A1:4", "D2:4 | Eb2:4 | Ab1:4 | A1:4"]


def battle(s, blocks, seconds, accents=True):
    """160 bpm, four bars per block; every block opens on a boss-reveal hit."""
    b = s.section("battle", bars=4 * blocks, meter=4, seconds=seconds)
    bass = " | ".join(BATTLE_BASS[i % len(BATTLE_BASS)] for i in range(blocks))
    film(s, b, bass, "drive")
    b.part("vc_spic", grind(bass, 38), vel="ff")
    b.part("cb_spic", grind(bass, 26), vel="ff")
    drums(b, 4 * blocks)
    hit(s, b.at(1), "D2", gain=4, seed=1)
    b.hits("gong", "1", bar=1, vel="ff")
    b.hits("crash", "1", bar=1, vel="ff")
    shout(s, b.at(1), "Ha!", seed=3, gain=2)
    stab = "D3+Ab3:.5> r:1 D3+Ab3:.5> r:1 D3+Ab3:.5> r:.5"
    for k in range(blocks):
        blk = Span(b, 1 + 4 * k, 4)
        kind = k % 3
        if kind == 0:  # the summons: chant and trombone stabs
            for i in range(4):
                chant(s, blk, i + 1, "Vail:D3:1.5 Or:D3:1 Run:Ab2:1.5", men=14, gain=-2, seed=300 + 4 * k + i)
            blk.part("tbn", " | ".join([stab] * 4), vel="ff")
            blk.part("vln_trem", "D6+Eb6:16", vel="mf")
        elif kind == 1:  # the Hollow in eight horns, the high choir a semitone apart
            blk.part("hn_lo", HOLLOW4, vel="fff", transpose=-12)
            blk.part("hn_solo", HOLLOW4, vel="fff")
            blk.part("tuba", HOLLOW4, vel="ff", transpose=-24)
            blk.part("choir_hi", "D5+Eb5:8 | Eb5+E5:8", vel="ff")
            blk.part("choir", "D3+Ab3:8 | D3+A3:8", vel="ff")
        else:  # the onslaught: tritone walls and trumpets, anvils
            blk.part("tpt", "D5:1.5 Ab4:2.5 | Eb5:1.5 A4:2.5 | Ab4:4 | A4:4", vel="ff")
            blk.part("hn_lo", "D3+Ab3:4 | Eb3+A3:4 | Ab2+D3:4 | A2+Eb3:4", vel="fff")
            blk.part("choir", "D3+Ab3+Eb4:4 | Eb3+A3+E4:4 | Ab2+D3+A3:4 | A2+Eb3+Bb3:4", vel="fff")
            blk.hits("anvil", "2 4", bar=1, vel="f", bars=4)
            blk.hits("epic", "3", bar=1, vel="fff", bars=4)
        if accents and k > 0:  # boss reveal
            hit(s, blk.at(1), ["D2", "Eb2", "Ab1", "Bb1", "A1", "D2"][k % 6], gain=2, seed=60 + k)
            blk.hits("crash", "1", bar=1, vel="ff")
            blk.hits("gong", "1", bar=1, vel="f")
            if k % 2 == 0:
                shout(s, blk.at(1), "Ha!", seed=10 + k, gain=1)
        blk.hits("toms", [1 + i * 0.25 for i in range(16)], bar=4, vel="ff")
    return b


def breakdown(s, bars, seconds):
    """Strip back: low strings and a choir pad under the voice."""
    d = s.section("breakdown", bars=bars, meter=4, seconds=seconds)
    n = bars * 4
    d.part("cb", f"D2:{n}", vel="mf")
    d.part("vc", f"D3:{n // 2} Bb2:{n - n // 2}", vel="mf")
    d.part("vla", f"F3+A3:{n // 2} F3+Bb3:{n - n // 2}", vel="p")
    d.part("choir", f"D3+A3+D4:{n // 2} D3+F3+Bb3:{n - n // 2}", vel="mf")
    d.part("syn_pad_soft", f"D2+A2+D3:{n}", vel="mf")
    d.part("syn_sub_soft", f"D1:{n}", vel="mf")
    sw(s, d, "choir", [(d.at(1), -6), (d.at(bars, 4), -2)])
    d.hits("taiko", "1", bar=1, vel="mf", bars=bars)
    return d


def riser_and_title(s, rise_s, ring_s, ring_bars=2):
    r = s.section("riser", bars=2, meter=4, seconds=rise_s)
    film(s, r, "Bb1:4 | A1:4", "drive")
    r.part("vc_spic", grind("Bb1:4 | A1:4", 38), vel="ff")
    r.part("cb_spic", grind("Bb1:4 | A1:4", 26), vel="ff")
    r.part("hn_lo", "Bb2+F3:4 | A2+E3:4", vel="fff")
    r.part("choir", "Bb3+D4+F4:4 | A3+C#4+E4:4", vel="fff")
    r.part("vln_trem", "Bb5+D6:4 | A5+C#6+E6:4", vel="f")
    sw(s, r, "choir", [(r.at(1), -6), (r.at(2, 4), 4)])
    sw(s, r, "vln_trem", [(r.at(1), -8), (r.at(2, 4), 4)])
    r.hits("snare", [1 + i * 0.25 for i in range(16)], bar=1, vel="f", bars=2)
    r.hits("toms", [1 + i * 0.25 for i in range(16)], bar=2, vel="fff")
    r.hits("taiko", "1 2 3 4", bar=1, vel="ff", bars=2)
    shout(s, s._beat_at(s.time_of(r.at(1)) + 0.5), "Light the towers!", gain=2, seed=4, n=20, women=6)
    t = s.section("title", bars=ring_bars, meter=4, seconds=ring_s)
    n = ring_bars * 4
    rise(s, t.at(1), 2.0, gain=1, seed=6)
    hit(s, t.at(1), "D2", gain=5, seed=7)
    for k in ["sus_cym", "crash", "gong"]:
        t.hits(k, "1", vel="ff")
    t.hits("epic", "1", vel="fff")
    t.hits("timp:D2", "1", vel="fff")
    t.part("hn_lo", f"D3+A3+D4:{n}", vel="fff")
    t.part("tbn", f"D3+A3:{n}", vel="fff")
    t.part("tuba", f"D2:{n}", vel="fff")
    t.part("cb", f"D2:{n}", vel="ff")
    t.part("vc", f"D3:{n}", vel="ff")
    t.part("choir", f"A3+D4+F4+A4:{n}", vel="fff")
    t.part("syn_sub", f"D1:{n}", vel="ff")
    t.part("syn_pad", f"D3+A3+D4:{n}", vel="f")
    for k in ["hn_lo", "tbn", "tuba", "choir", "syn_sub", "syn_pad", "cb", "vc"]:
        sw(s, t, k, [(t.at(1), 0), (t.at(ring_bars, 4), -24)])
    shout(s, t.at(1), "Hey!", gain=-1, seed=5, n=20, women=6)
    for note, women in [("D3", 0), ("A3", 0), ("D4", 8), ("F4", 8)]:
        s.place(t.at(1), V.sung("Ah", midi(note), 4.0, n=10 if not women else 0, women=women, seed=midi(note) + 3),
                -1.0, group="chant", send=0.5)


def build():
    s = setup("trailer2", "The Last Lantern (story trailer)")
    low_build(s, bars=9, seconds=18.0)          # 0:00-0:18, 120 bpm
    battle(s, blocks=6, seconds=36.0)           # 0:18-0:54, 160 bpm, accents every 6 s
    breakdown(s, bars=4, seconds=12.0)          # 0:54-1:06, 80 bpm
    riser_and_title(s, rise_s=4.0, ring_s=7.5)  # 1:06-1:10, hit at 1:10, ring to 1:17.5
    s.ducks = [(17.82, 18.0, -18.0), (69.62, 70.0, -40.0)]  # drop-outs before the two big hits
    s.end_pad = 0.5
    return s
