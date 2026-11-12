"""The realm battle music: three looping tracks for each element's land and three for the
Convergence, on top of Hold the Line (loops/battle.py), so every map has four tracks to rotate
through. Each track is a seamless loop in the same three layers as Hold the Line (calm, wave,
boss), so BattleMusic plays them the same way.

Every track is written below as a small score in scale degrees: a key and mode, a tempo and metre,
one chord per bar for each 8-bar section, and an 8-bar theme. build() turns that into the
orchestra, with each element's own sound:

  fire    war drums in 3+3+2, grinding cello ostinatos, low brass and anvils
  water   rolling harp and string arpeggios, surging drums, deep horns and choir
  earth   slow and heavy: timpani, bass drums, tubas and trombones, a stamping half-time
  storm   fast: galloping snares and toms, string tremolo, trumpets, crashes
  nature  dark forest: log drums and tumbas, pizzicato, bassoons and low clarinets
  void    cold and wrong: tritones, rubbed bass drums, gongs, grinding semitones, odd metres
  heart   the Convergence: every colour at once, the biggest drums and the full choir

The sections follow one plan: A the march (ostinato and drums, no tune), B the theme, C the
dark turn (a counter-line over the relative chords), D the theme again in full. Each loop ends
on the bar that leads back into A. No celesta, glockenspiel, bells or toy synths: the game is 18+.

    python3 tools/music/render_loop.py realm_fire_1 realm_water_2 ...
    python3 tools/music/render_loop.py --realms          # all of them
"""
from __future__ import annotations

from dataclasses import dataclass

from cues._kit import _in_range, name, new, ost16
from score import midi

MODES = {
    "aeolian": [0, 2, 3, 5, 7, 8, 10],
    "dorian": [0, 2, 3, 5, 7, 9, 10],
    "phrygian": [0, 1, 3, 5, 7, 8, 10],
    "harmonic": [0, 2, 3, 5, 7, 8, 11],
    "phrygdom": [0, 1, 4, 5, 7, 8, 10],
}

LAYERS = ["calm", "wave", "boss"]
LAYER_DB = {"calm": 8.0, "wave": 1.0, "boss": 0.0}
# The realm tracks are long and many, so they ship at Vorbis quality 4 (about 128 kbps).
QUALITY = 4


@dataclass
class Track:
    id: str
    title: str
    element: str
    key: str            # tonic with octave 2, e.g. "E2"
    mode: str
    bpm: int
    meter: int          # quarter beats per bar: 3, 4 or 5
    prog: dict          # section -> 8 bar tokens: "1", "6", "5M" (major chord), "4/5" (two halves)
    theme: str          # 8 bars in degrees: "5:1.5 6:.5 | ..."; 0 = the 7th below, 8 = octave
    lead: str = "vc_solo"   # calm-layer voice of the theme
    note: str = ""


T = Track
TRACKS: list[Track] = [
    # ------------------------------------------------------------------ fire
    T("fire_1", "The Burning Road", "fire", "E2", "phrygian", 132, 4,
      {"A": "1 1 2 1 1 1 6 7", "B": "1 6 7 1 4 6 2 5M", "C": "6 6 2 2 6 4 7 7", "D": "1 6 7 1 4 2 7 5M"},
      "5:1.5 6:.5 5 4 | 3:2 2:2 | 1 2 3 5 | 4:4 | 5:1.5 6:.5 5 4 | 3:2 2 1 | 2:3 0:1 | 1:4",
      lead="hn_solo", note="132 bpm in E Phrygian, war drums in 3+3+2"),
    T("fire_2", "Ash Tithe", "fire", "D2", "harmonic", 150, 3,
      {"A": "1 1 6 6 4 4 5M 5M", "B": "1 6 4 5M 1 6 2 5M", "C": "6 6 3 3 4 4 5M 5M",
       "D": "1 6 4 5M 1 4 5M 5M"},
      "1:2 2:1 | 3:2 5:1 | 4:1.5 3:.5 2:1 | 3:3 | 1:2 2:1 | 3:2 6:1 | 5:1.5 4:.5 #7-:1 | 1:3",
      lead="vc_solo", note="a war waltz at 150 bpm in D harmonic minor"),
    T("fire_3", "Forge of Teeth", "fire", "C2", "phrygdom", 138, 5,
      {"A": "1 1 2 1 1 1 2 1", "B": "1 2 1 7 6 2 1 1", "C": "4 4 2 2 6 6 2 2", "D": "1 2 1 7 6 2 2 1"},
      "1:2 2:1 3:2 | 5:3 4:2 | 3:1 2:1 1:3 | 2:5 | 1:2 2:1 3:2 | 6:3 5:2 | 4:1 3:1 2:3 | 1:5",
      lead="tbn", note="5/4 at 138 bpm, C Phrygian dominant, anvils in the forge"),
    # ------------------------------------------------------------------ water
    T("water_1", "Black Tide", "water", "C2", "aeolian", 112, 4,
      {"A": "1 1 6 6 4 4 5 5", "B": "1 6 3 7 4 6 4 5M", "C": "6 7 1 1 4 5 6 5M", "D": "1 6 3 7 4 6 5M 5M"},
      "1:2 5:2 | 6:1.5 5:.5 4 3 | 2:2 3 4 | 5:4 | 8:2 7:1 6:1 | 5:1.5 4:.5 3 2 | 3:2 #7-:2 | 1:4",
      lead="vc_solo", note="112 bpm in C minor, rolling arpeggios"),
    T("water_2", "The Undertow", "water", "F#2", "aeolian", 126, 3,
      {"A": "1 1 7 7 6 6 5 5", "B": "1 7 6 7 1 3 4 5", "C": "4 4 1 1 6 6 5M 5M", "D": "1 7 6 7 1 4 5M 5M"},
      "5:2 4:1 | 3:2 2:1 | 1:1.5 2:.5 3:1 | 2:3 | 5:2 6:1 | 7:2 6:1 | 5:1 4:1 #7-:1 | 1:3",
      lead="hn_solo", note="a 3/4 surge at 126 bpm in F# minor"),
    T("water_3", "Leviathan Wake", "water", "A1", "phrygian", 96, 4,
      {"A": "1 1 1 2 1 1 7 2", "B": "1 2 6 7 1 2 4 5", "C": "6 6 7 7 4 4 2 2", "D": "1 2 6 7 1 2 2 1"},
      "1:3 2:1 | 1:2 0:2 | 6-:2 0:1 1:1 | 2:4 | 3:3 2:1 | 1:2 0:2 | 2:1.5 3:.5 2:1 0:1 | 1:4",
      lead="tbn", note="96 bpm half time in A Phrygian, something huge under the water"),
    # ------------------------------------------------------------------ earth
    T("earth_1", "The Stone Remembers", "earth", "C2", "aeolian", 92, 4,
      {"A": "1 1 1 1 6 6 7 7", "B": "1 7 6 7 1 4 6 5M", "C": "4 4 6 6 3 3 7 7", "D": "1 7 6 7 4 6 5M 5M"},
      "1:2 3:2 | 5:3 4:1 | 3:2 2:1 1:1 | 2:4 | 1:2 3:2 | 6:3 5:1 | 4:1.5 3:.5 2:1 #7-:1 | 1:4",
      lead="hn_solo", note="92 bpm in C minor, a stamping half-time with timpani"),
    T("earth_2", "Iron Under the Hill", "earth", "D2", "aeolian", 108, 5,
      {"A": "1 1 6 6 1 1 7 7", "B": "1 6 3 7 1 6 4 5", "C": "6 6 4 4 6 6 5 5", "D": "1 6 3 7 4 6 5 5"},
      "1:3 5:2 | 4:2 3:1 2:2 | 3:3 1:2 | 2:5 | 1:3 5:2 | 6:2 5:1 4:2 | 3:2 2:1 0:2 | 1:5",
      lead="tbn", note="5/4 at 108 bpm in D minor, a dwarven forge march"),
    T("earth_3", "The Deep Toll", "earth", "B1", "phrygian", 120, 4,
      {"A": "1 1 2 1 1 1 6 7", "B": "1 2 1 7 6 7 6 5", "C": "4 4 6 6 4 4 2 2", "D": "1 2 1 7 6 2 2 1"},
      "1:1.5 1:.5 2:1 1:1 | 5-:4 | 6-:1.5 6-:.5 0:1 1:1 | 2:4 | 3:1.5 3:.5 2:1 1:1 | 6-:4 | 0:2 2:2 | 1:4",
      lead="tuba", note="120 bpm in B Phrygian, low brass toll over an ostinato"),
    # ------------------------------------------------------------------ storm
    T("storm_1", "Thunderhead", "storm", "D2", "aeolian", 148, 4,
      {"A": "1 1 6 6 7 7 5 5", "B": "1 6 7 5 1 6 4 5M", "C": "6 7 1 1 6 7 5M 5M", "D": "1 6 7 5 1 4 5M 5M"},
      "5:1 5:.5 6:.5 5:1 4:1 | 3:2 5:2 | 6:1 6:.5 7:.5 6:1 5:1 | 4:4 | 5:1 5:.5 6:.5 5:1 4:1 | "
      "3:2 8:2 | 7:1.5 6:.5 5:1 #7-:1 | 1:4",
      lead="hn_solo", note="148 bpm in D minor, a galloping cavalry charge"),
    T("storm_2", "Riders of the Gale", "storm", "E2", "harmonic", 160, 3,
      {"A": "1 1 1 1 6 6 5M 5M", "B": "1 4 5M 1 6 4 5M 5M", "C": "4 4 1 1 6 6 5M 5M", "D": "1 4 5M 1 6 2 5M 5M"},
      "5:1 1:1 2:1 | 3:2 5:1 | 4:1 3:1 2:1 | #7-:3 | 5:1 1:1 2:1 | 3:2 6:1 | 5:1 4:1 #7-:1 | 1:3",
      lead="tpt_solo", note="a galloping 3/4 at 160 bpm in E harmonic minor"),
    T("storm_3", "Shattered Sky", "storm", "G2", "phrygian", 140, 4,
      {"A": "1 1 2 2 1 1 7 7", "B": "1 2 6 7 1 2 4 2", "C": "6 6 7 7 4 4 2 2", "D": "1 2 6 7 1 2 2 1"},
      "1:1 2:1 3:2 | 2:1 1:1 0:2 | 6-:1 0:1 1:2 | 2:4 | 3:1 4:1 5:2 | 4:1 3:1 2:2 | 1:1 2:1 3:1 2:1 | 1:4",
      lead="hn_solo", note="140 bpm in G Phrygian, string tremolo lightning"),
    # ------------------------------------------------------------------ nature
    T("nature_1", "Rotwood", "nature", "A1", "dorian", 112, 4,
      {"A": "1 1 4 4 1 1 7 7", "B": "1 4 7 1 6 4 7 1", "C": "4 4 7 7 3 3 5 5", "D": "1 4 7 1 6 4 5 5"},
      "1:1.5 3:.5 5:2 | 4:1 3:1 2:2 | 1:1.5 3:.5 6:2 | 5:4 | 4:1.5 5:.5 6:2 | 5:1 4:1 3:2 | 2:1 3:1 0:2 | 1:4",
      lead="bsn", note="112 bpm in A Dorian, log drums in a rotting wood"),
    T("nature_2", "The Thorn March", "nature", "E2", "aeolian", 132, 3,
      {"A": "1 1 7 7 6 6 7 7", "B": "1 7 6 7 1 4 6 5M", "C": "4 4 6 6 3 3 7 7", "D": "1 7 6 7 4 6 5M 5M"},
      "1:1 3:1 5:1 | 4:2 3:1 | 2:1 4:1 6:1 | 5:3 | 8:2 7:1 | 6:2 5:1 | 4:1 3:1 #7-:1 | 1:3",
      lead="cl", note="3/4 at 132 bpm in E minor, the forest marches"),
    T("nature_3", "Old Roots Wake", "nature", "D2", "dorian", 120, 5,
      {"A": "1 1 7 7 1 1 4 4", "B": "1 7 4 1 6 7 4 5", "C": "4 4 1 1 7 7 5 5", "D": "1 7 4 1 6 4 5 5"},
      "5:2 4:1 3:2 | 1:3 2:2 | 3:2 4:1 6:2 | 5:5 | 5:2 4:1 3:2 | 6:3 5:2 | 4:2 3:1 2:2 | 1:5",
      lead="hn_solo", note="5/4 at 120 bpm in D Dorian, the old roots wake"),
    # ------------------------------------------------------------------ void
    T("void_1", "Nothing Sings", "void", "D2", "phrygian", 110, 5,
      {"A": "1 1 1 2 1 1 1 2", "B": "1 2 1 #4 1 2 6 2", "C": "#4 #4 1 1 #4 #4 2 2", "D": "1 2 1 #4 6 2 2 1"},
      "1:3 #4-:2 | 4-:1.5 6-:.5 5-:1 2:2 | 1:3 0:2 | 6-:3 #4-:2 | 1:3 #4-:2 | 4-:1.5 6-:.5 5-:1 3:2 | "
      "2:3 1:2 | 1:5",
      lead="bsn", note="5/4 at 110 bpm in D Phrygian, the Hollow's tritone"),
    T("void_2", "The Unlit Choir", "void", "Bb1", "harmonic", 96, 4,
      {"A": "1 1 6 6 1 1 #4 5M", "B": "1 6 #4 5M 1 6 2 5M", "C": "6 6 #4 #4 6 6 5M 5M", "D": "1 6 #4 5M 6 2 5M 1"},
      "1:3 2:1 | 3:2 #4:2 | 5:3 6:1 | 5:4 | 8:3 7:1 | 6:2 5:2 | #4:2 2:1 #7-:1 | 1:4",
      lead="vc_solo", note="96 bpm half time in Bb harmonic minor, cold choir and gongs"),
    T("void_3", "Hollow Engine", "void", "F#2", "phrygian", 138, 4,
      {"A": "1 1 2 1 1 1 2 1", "B": "1 2 #4 1 1 2 6 2", "C": "6 6 2 2 #4 #4 2 2", "D": "1 2 #4 1 6 2 2 1"},
      "1:1 2:1 1:1 #4-:1 | 1:2 2:2 | 3:1 2:1 1:1 6-:1 | #4-:4 | 1:1 2:1 1:1 #4-:1 | 3:2 2:2 | 1:1 2:1 #4-:2 | 1:4",
      lead="tbn", note="138 bpm in F# Phrygian, a machine that grinds semitones"),
    # ------------------------------------------------------------------ heart (the Convergence)
    T("heart_1", "Seven Crowns", "heart", "D2", "aeolian", 120, 4,
      {"A": "1 1 6 6 3 3 7 7", "B": "1 6 3 7 4 6 4 5M", "C": "6 7 1 1 4 5 6 5M", "D": "1 6 3 7 4 6 5M 5M"},
      "1:2 5:2 | 4:1.5 3:.5 2 1 | 6-:2 2 3 | 2:4 | 1:2 5:2 | 6:1.5 5:.5 4 3 | 4:1.5 3:.5 2 #7-:1 | 1:4",
      lead="hn_solo", note="120 bpm in D minor, the Long Defeat as a march"),
    T("heart_2", "The Last Stand of Solenne", "heart", "G2", "harmonic", 132, 4,
      {"A": "1 1 6 6 4 4 5M 5M", "B": "1 6 4 5M 1 6 2 5M", "C": "6 6 4 4 1 1 5M 5M", "D": "1 6 4 5M 6 4 5M 5M"},
      "5:1.5 4:.5 3:1 1:1 | 2:2 #7-:2 | 1:1 2:1 3:1 5:1 | 4:4 | 5:1.5 6:.5 5:1 3:1 | 6:2 5:2 | "
      "4:1.5 3:.5 2:1 #7-:1 | 1:4",
      lead="vc_solo", note="132 bpm in G harmonic minor, the capital holds"),
    T("heart_3", "Convergence", "heart", "C2", "aeolian", 144, 3,
      {"A": "1 1 6 6 7 7 5M 5M", "B": "1 6 3 7 1 4 5M 5M", "C": "4 4 6 6 3 3 5M 5M", "D": "1 6 3 7 4 6 5M 5M"},
      "1:2 5:1 | 4:1 3:1 2:1 | 3:2 6:1 | 5:3 | 8:2 7:1 | 6:1 5:1 4:1 | 3:1 2:1 #7-:1 | 1:3",
      lead="hn_solo", note="a 3/4 storm at 144 bpm in C minor, every colour at once"),
]
BY_ID = {f"realm_{t.id}": t for t in TRACKS}


# ---------------------------------------------------------------- pitch helpers
class Key:
    def __init__(self, t: Track):
        self.root = midi(t.key)
        self.scale = MODES[t.mode]

    def degree(self, tok: str, base: int) -> int:
        """Midi pitch of a degree token ("5", "#4", "b6", "0", "6-" = 6 an octave down)."""
        shift = 0
        while tok.endswith("-"):
            shift -= 12
            tok = tok[:-1]
        while tok.endswith("+"):
            shift += 12
            tok = tok[:-1]
        acc = 0
        if tok[0] in "#b":
            acc = 1 if tok[0] == "#" else -1
            tok = tok[1:]
        d = int(tok) - 1
        return base + 12 * (d // 7) + self.scale[d % 7] + acc + shift

    def chord(self, tok: str) -> tuple[int, list[int]]:
        """(root pitch class in octave 2, triad pitches above it) of a chord token."""
        quality = ""
        if tok[-1] in "Mm":
            tok, quality = tok[:-1], tok[-1]
        root = self.degree(tok, self.root)
        acc = 1 if tok[0] == "#" else -1 if tok[0] == "b" else 0
        d = int(tok.lstrip("#b")) - 1
        third = self.degree(str(d + 3), self.root) + acc
        fifth = self.degree(str(d + 5), self.root) + acc
        if quality == "M":
            third = root + 4
        elif quality == "m":
            third = root + 3
        if (fifth - root) % 12 == 6 and quality == "M":
            fifth = root + 7
        return root, [root, third, fifth]

    def melody(self, text: str, octave_base: int) -> str:
        """Turn a theme in degrees into note names (the tonic at octave_base)."""
        out = []
        for tok in text.split():
            if tok == "|" or tok.startswith("r"):
                out.append(tok)
                continue
            head, _, dur = tok.partition(":")
            out.append(name(self.degree(head, octave_base)) + (f":{dur}" if dur else ""))
        return " ".join(out)


def bars_of(prog: str) -> list[list[str]]:
    return [b.split("/") for b in prog.split()]


def bass_line(key: Key, prog: str, meter: int, lo: int = 31) -> str:
    """One root per chord, as notation: "D2:4 | Bb1:4 ..." (lowest root at or above `lo`)."""
    bars = []
    for chords in bars_of(prog):
        d = meter / len(chords)
        bars.append(" ".join(f"{name(_in_range(key.chord(c)[0], lo))}:{d:g}" for c in chords))
    return " | ".join(bars)


def voiced(key: Key, prog: str, meter: int, lo: int, spread: bool = True) -> str:
    """Triads per chord, close or open, starting at or above `lo`."""
    bars = []
    for chords in bars_of(prog):
        d = meter / len(chords)
        cell = []
        for c in chords:
            r, tri = key.chord(c)
            base = _in_range(r, lo)
            ps = [base + (p - r) for p in tri]
            if spread:
                ps = [ps[0], ps[2], ps[1] + 12]
            cell.append("+".join(name(p) for p in ps) + f":{d:g}")
        bars.append(" ".join(cell))
    return " | ".join(bars)


def per_beat(key: Key, prog: str, meter: int, cell, step: float = 0.5, lo: int = 38) -> str:
    """An ostinato: for each chord, cell(root, third, fifth, i) gives the pitch of step i."""
    bars = []
    for chords in bars_of(prog):
        n_per = int(round(meter / len(chords) / step))
        notes = []
        for c in chords:
            r, tri = key.chord(c)
            base = _in_range(r, lo)
            t3, t5 = base + (tri[1] - r), base + (tri[2] - r)
            for i in range(n_per):
                p = cell(base, t3, t5, i)
                notes.append("r" if p is None else name(p))
        bars.append(" ".join(f"{n}:{step:g}" + ("'" if n != "r" else "") for n in notes))
    return " | ".join(bars)


def counter(key: Key, prog: str, meter: int, lo: int = 55) -> str:
    """A slow counter-line: the third of each chord, held, near `lo`."""
    bars = []
    for chords in bars_of(prog):
        d = meter / len(chords)
        bars.append(" ".join(f"{name(_in_range(key.chord(c)[1][1], lo))}:{d:g}" for c in chords))
    return " | ".join(bars)


# ---------------------------------------------------------------- drums per element
def every(sec, kind: str, beats: str, step: int, vel: str):
    """Hits on bar 1 and every `step` bars after it."""
    for bar in range(1, int(sec.bars) + 1, step):
        sec.hits(kind, beats, bar=bar, vel=vel)


def groove(sec, el: str, meter: int, level: str):
    """Element drum pattern for a section. level "wave" or "boss" (boss adds on top of wave)."""
    b = int(sec.bars)
    m = meter
    eighths = [1 + i * 0.5 for i in range(m * 2)]
    sixteenths = [1 + i * 0.25 for i in range(m * 4)]
    if level == "boss":
        sec.hits("epic", "1", bar=1, vel="fff", bars=b)
        sec.hits("crash", "1", bar=1, vel="f")
        sec.hits("toms", [m - 1 + i * 0.25 for i in range(8)], bar=4, vel="ff")
        sec.hits("toms", [1 + i * 0.25 for i in range(m * 4)], bar=b, vel="ff")
        if el in ("fire", "earth", "heart"):
            sec.hits("taiko", [1 + i for i in range(m)], bar=1, vel="ff", bars=b)
        if el in ("storm", "heart"):
            sec.hits("snare_roll", "1", bar=b - 1, vel="mf")
        if el == "void":
            sec.hits("gong", "1", bar=1, vel="f")
            sec.hits("gong", "1", bar=5, vel="mf")
        return
    fills = [m + i * 0.25 for i in range(4)]
    if el == "fire":
        pat = {4: "1 1.75 2.5 3 3.75 4.5", 3: "1 1.75 2.5 3", 5: "1 1.75 2.5 3 4 4.75"}[m]
        sec.hits("taiko", pat, bar=1, vel="ff", bars=b)
        sec.hits("snare", [x for x in sixteenths if (x - 1) % 1 in (0.0, 0.75)], bar=1, vel="mf", bars=b)
        sec.hits("anvil", "2" if m != 3 else "3", bar=2, vel="mp", bars=1)
        sec.hits("anvil", "2" if m != 3 else "3", bar=6, vel="mp", bars=1)
        every(sec, "epic", "1", 2, "fff")
    elif el == "water":
        sec.hits("taiko", "1" if m == 3 else "1 3.5" if m == 4 else "1 3.5", bar=1, vel="ff", bars=b)
        sec.hits("tumba", eighths[1::2], bar=1, vel="mf", bars=b)
        sec.hits("logdrum", [x + 0.25 for x in eighths[::2]], bar=1, vel="mp", bars=b)
        sec.hits("sus_cym", "1", bar=b - 3, vel="mf")
    elif el == "earth":
        pat = {4: "1 3", 3: "1", 5: "1 4"}[m]
        sec.hits("epic", pat, bar=1, vel="fff", bars=b)
        sec.hits("bd", [x for x in eighths if x != 1][:2], bar=1, vel="f", bars=b)
        sec.hits("timp", [1, 1.5, m - 0.5] if m > 3 else [1, 2.5], bar=1, vel="f", bars=b)
        sec.hits("anvil", str(m), bar=4, vel="mp")
        sec.hits("anvil", str(m), bar=8, vel="mp")
    elif el == "storm":
        sec.hits("snare", sixteenths, bar=1, vel="mp", bars=b)
        pat = {4: "1 1.5 2.5 3 3.5 4.5", 3: "1 1.5 2.5", 5: "1 1.5 2.5 3.5 4 5"}[m]
        sec.hits("taiko", pat, bar=1, vel="ff", bars=b)
        every(sec, "crash", "1", 4, "mf")
        sec.hits("epic", "1", bar=1, vel="fff", bars=b)
    elif el == "nature":
        pat = {4: "1 2.5 3 4", 3: "1 2 2.5", 5: "1 2.5 3 4 4.5"}[m]
        sec.hits("logdrum", pat, bar=1, vel="f", bars=b)
        sec.hits("tumba", eighths[1::2] + [m + 0.75], bar=1, vel="mf", bars=b)
        sec.hits("taiko", "1", bar=1, vel="ff", bars=b)
        sec.hits("bd", str(m - 1 if m > 3 else 2.5), bar=1, vel="f", bars=b)
    elif el == "void":
        pat = {4: "1 2.75 3.5", 3: "1 2.75", 5: "1 2.75 3.5 5"}[m]
        every(sec, "bd_rub", "1", 4, "f")
        sec.hits("taiko", pat, bar=1, vel="ff", bars=b)
        sec.hits("tick", eighths, bar=1, vel="mp", bars=b)
        sec.hits("gong", "1", bar=1, vel="mp")
        sec.hits("epic", "1", bar=1, vel="fff", bars=b)
    else:  # heart
        pat = {4: "1 2.5 3 4.5", 3: "1 2.5 3", 5: "1 2.5 3 4.5 5"}[m]
        sec.hits("epic", "1", bar=1, vel="fff", bars=b)
        sec.hits("taiko", pat, bar=1, vel="ff", bars=b)
        sec.hits("snare", [x for x in sixteenths if (x - 1) % 1 in (0.0, 0.75)], bar=1, vel="mf", bars=b)
        sec.hits("timp", "1", bar=1, vel="f", bars=b)
    sec.hits("toms", fills, bar=b, vel="ff")
    sec.hits("toms", fills, bar=4, vel="f")


# ---------------------------------------------------------------- the three layers
def reps(t: Track) -> int:
    """Short loops (fast 3/4) play each section twice, so no loop is under about 70 s."""
    return 2 if len(t.prog) * 8 * t.meter * 60 / t.bpm < 55 else 1


def _expand(t: Track) -> Track:
    n = reps(t)
    if n == 1:
        return t
    from dataclasses import replace
    return replace(t, prog={k: " ".join([v] * n) for k, v in t.prog.items()},
                   theme=" | ".join([t.theme] * n))


def _frame(t: Track, layer: str):
    s = new(f"realm_{t.id}_{layer}", t.title)
    secs = {k: s.section(k, bars=8 * reps(BY_ID["realm_" + t.id]), meter=t.meter, bpm=t.bpm) for k in t.prog}
    s.end_pad = 5.0
    return s, secs


def _theme_secs(t: Track) -> list[str]:
    return [k for k in t.prog if k in ("B", "D")]


def calm(t: Track, k: Key, s, secs):
    m = t.meter
    el = t.element
    for name_, sec in secs.items():
        prog = t.prog[name_]
        bass = bass_line(k, prog, m)
        sec.part("syn_pad_soft", voiced(k, prog, m, 50, spread=False), vel="mf")
        sec.part("syn_sub_soft", bass_line(k, prog, m, 26), vel="mf")
        sec.part("cb", bass_line(k, prog, m, 38), vel="p")
        sec.part("vc", voiced(k, prog, m, 43), vel="p")
        # the element's quiet ostinato
        if el == "water":
            sec.part("harp", per_beat(k, prog, m, lambda r, a, b, i: [r, b, r + 12, a + 12][i % 4], 0.5, 45), vel="mp")
        elif el == "nature":
            sec.part("vc_pizz", per_beat(k, prog, m, lambda r, a, b, i: [r, None, b, r][i % 4], 0.5, 38), vel="mf")
        elif el in ("storm", "void"):
            sec.part("vla_trem", counter(k, prog, m, 60), vel="pp")
        elif el in ("fire", "earth"):
            sec.part("vc_spic", per_beat(k, prog, m, lambda r, a, b, i: r if i % 2 == 0 else None, 0.5, 38),
                     vel="mp")
        else:
            sec.part("harp", per_beat(k, prog, m, lambda r, a, b, i: [r, b, r + 12, b][i % 4], 0.5, 45), vel="mp")
        # a slow heartbeat so the build phase never goes slack
        every(sec, "timp" if el != "void" else "bd_rub", "1", 2, "p")
    for name_ in _theme_secs(t):
        lo = {"tbn": 45, "bsn": 45, "tuba": 34, "vc_solo": 48, "hn_solo": 50, "cl": 52}.get(t.lead, 57)
        secs[name_].part(t.lead, k.melody(t.theme, _tonic(k, lo)), vel="mp")
    if "C" in secs:
        secs["C"].part("vla", counter(k, t.prog["C"], m, 57), vel="p")
        secs["C"].part("vln_trem", counter(k, t.prog["C"], m, 74), vel="ppp")


def _tonic(k: Key, lo: int) -> int:
    return _in_range(k.root, lo)


def wave(t: Track, k: Key, s, secs):
    m = t.meter
    el = t.element
    for name_, sec in secs.items():
        prog = t.prog[name_]
        low = bass_line(k, prog, m, 38)
        sec.part("syn_pad", voiced(k, prog, m, 50, spread=False), vel="f")
        sec.part("syn_sub", bass_line(k, prog, m, 26), vel="f")
        sec.part("syn_bass", low, vel="ff")
        if el in ("fire", "void"):
            # grind: the root flicking up a semitone, never still
            ost = per_beat(k, prog, m, lambda r, a, b, i: r + 1 if i % 4 == 2 else r, 0.25, 38)
        elif el == "water":
            ost = per_beat(k, prog, m, lambda r, a, b, i: [r, b, r + 12, b, a + 12, b, r + 12, b][i % 8], 0.25, 38)
        elif el == "earth":
            ost = per_beat(k, prog, m, lambda r, a, b, i: r if i % 2 == 0 else r + 12, 0.5, 38)
        elif el == "nature":
            ost = per_beat(k, prog, m, lambda r, a, b, i: [r, r, b, r, a + 12, r][i % 6], 0.25, 38)
        else:
            ost = ost16(low, m)
        sec.part("vc_spic16", ost, vel="f")
        sec.part("cb_spic16", ost, vel="f", transpose=-12)
        sec.part("syn_pulse", ost16(low, m), vel="mf")
        if el in ("storm", "water", "heart"):
            sec.part("vla_spic", per_beat(k, prog, m, lambda r, a, b, i: [b, a + 12, r + 12, a + 12][i % 4],
                                          0.25, 50), vel="mf")
        if el in ("storm", "void"):
            sec.part("vln_trem", voiced(k, prog, m, 67, spread=False), vel="mp")
        if el in ("earth", "fire"):
            sec.part("tuba", bass_line(k, prog, m, 33), vel="f")
        groove(sec, el, m, "wave")
    themes = _theme_secs(t)
    base_hi = _tonic(k, 60)
    for name_ in themes:
        mel = k.melody(t.theme, base_hi)
        secs[name_].part("hn_lo", mel, vel="ff", transpose=-12)
        secs[name_].part("vln" if name_ == "B" else "tpt", mel, vel="f" if name_ == "B" else "ff")
        secs[name_].part("vla", mel, vel="f", transpose=-12)
    if "C" in secs:
        secs["C"].part("tbn", voiced(k, t.prog["C"], m, 45, spread=False), vel="f")
        secs["C"].part("hn", counter(k, t.prog["C"], m, 60), vel="f")
    if "A" in secs:
        # stabs on the march
        stab = " | ".join(" ".join([c.split(":")[0] + ":1'"] + ["r:1"] * (m - 1)) for c in
                          voiced(k, t.prog["A"], m, 45, spread=False).split(" | "))
        secs["A"].part("tbn", stab, vel="ff")


def boss(t: Track, k: Key, s, secs):
    import vocals as V

    m = t.meter
    el = t.element
    for name_, sec in secs.items():
        prog = t.prog[name_]
        sec.part("choir", voiced(k, prog, m, 50), vel="f")
        sec.part("hn", voiced(k, prog, m, 55, spread=False), vel="f")
        groove(sec, el, m, "boss")
    base_hi = _tonic(k, 60)
    for name_ in _theme_secs(t):
        mel = k.melody(t.theme, base_hi)
        secs[name_].part("tpt", mel, vel="ff", transpose=12 if name_ == "D" else 0)
        secs[name_].part("choir_hi", mel, vel="f", transpose=12 if name_ == "B" else 0)
        secs[name_].part("tuba", mel, vel="ff", transpose=-24)
    if "C" in secs:
        secs["C"].part("tpt", counter(k, t.prog["C"], m, 67), vel="ff")
    for name_ in [n for n in ("A", "C") if n in secs]:
        s.place(secs[name_].at(1), V.braam(_in_range(k.root, 36), 3.0, seed=ord(name_) + len(t.id)), -8,
                group="sfx", send=0.25)


def build(track_id: str, layer: str):
    t = _expand(BY_ID[track_id])
    k = Key(t)
    s, secs = _frame(t, layer)
    {"calm": calm, "wave": wave, "boss": boss}[layer](t, k, s, secs)
    return s


class Loop:
    """What render_loop.py expects of a loop module, for one realm track."""

    def __init__(self, track_id: str):
        self.track = BY_ID[track_id]
        self.id = track_id
        self.LAYERS = LAYERS
        self.LAYER_DB = LAYER_DB
        self.BPM = self.track.bpm
        self.QUALITY = QUALITY

    def build(self, layer: str):
        return build(self.id, layer)
