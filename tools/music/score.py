"""Write music as text, render it with the orchestra, mix and master it.

A cue is a Score made of Sections. Each section has its own tempo and metre. Parts are
written in a compact notation, one string per line of music:

    "D4:2 A4:2 | G4:1.5 F#4:.5 E4 D4 | B3+D4+G4:4 | r:2 !ff A4:2~ | A4:4"

- PITCH[:BEATS] plays a note (default one beat). Beats are quarter notes; 1/3 works for triplets.
- A+B+C plays a chord. `r` is a rest. A trailing `~` ties into the next note of the same pitch.
- A trailing `'` plays short (staccato), `>` adds an accent.
- `!pp` .. `!fff` set the dynamic for the following notes.
- `|` is a bar line and is checked against the section's metre, so wrong rhythms fail loudly.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass, field
from fractions import Fraction

import numpy as np
import soundfile as sf
from scipy import signal

import orchestra as orc
from orchestra import SR

DYN = {"ppp": 16, "pp": 30, "p": 46, "mp": 62, "mf": 78, "f": 96, "ff": 112, "fff": 127}
PITCH_RE = re.compile(r"^([A-G])(#|b)?(-?\d)$")
STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def midi(p: str) -> int:
    m = PITCH_RE.match(p)
    if not m:
        raise ValueError(f"bad pitch {p!r}")
    n = 12 * (int(m.group(3)) + 1) + STEP[m.group(1)]
    return n + (1 if m.group(2) == "#" else -1 if m.group(2) == "b" else 0)


# Percussion trims so a forte hit sits inside the orchestra rather than on top of it.
PERC_DB = {"timp": -13, "bd": -12, "crash": -18, "sus_cym": -20, "gong": -14, "anvil": -20,
           "snare_roll": -18, "taiko": -12}


SWELLS = {"sus_cym": 7.2}  # seconds from sample start to the loudest point


@dataclass
class Note:
    beat: float  # global beat
    dur: float  # beats
    pitch: int
    vel: int
    short: bool = False


@dataclass
class Part:
    inst: str
    notes: list = field(default_factory=list)
    hits: list = field(default_factory=list)  # (beat, kind, vel) for unpitched percussion


def parse(text: str, start: float, meter: float, vel: int = 78, transpose: int = 0) -> list[Note]:
    """Parse notation starting at global beat `start`. Returns notes; bar lines are checked
    relative to `start`, which must be on a bar line."""
    notes: list[Note] = []
    t = Fraction(0)
    open_ties: dict[int, Note] = {}
    for tok in text.split():
        if tok == "|":
            if t % Fraction(meter).limit_denominator(64) != 0:
                raise ValueError(f"bar line at beat {float(t)} is not on a bar (metre {meter}) in: {text[:60]}...")
            continue
        if tok.startswith("!"):
            vel = DYN[tok[1:]]
            continue
        tie = tok.endswith("~")
        tok = tok.rstrip("~")
        short = tok.endswith("'")
        tok = tok.rstrip("'")
        accent = tok.endswith(">")
        tok = tok.rstrip(">")
        if ":" in tok:
            head, d = tok.split(":")
            dur = Fraction(d) if "/" in d else Fraction(d).limit_denominator(48)
        else:
            head, dur = tok, Fraction(1)
        if head != "r":
            v = min(127, vel + (14 if accent else 0))
            for p in head.split("+"):
                m = midi(p) + transpose
                prev = open_ties.pop(m, None)
                if prev is not None:
                    prev.dur += float(dur)
                    n = prev
                else:
                    n = Note(start + float(t), float(dur), m, v, short)
                    notes.append(n)
                if tie:
                    open_ties[m] = n
        t += dur
    return notes


def length_beats(text: str) -> float:
    t = Fraction(0)
    for tok in text.split():
        if tok == "|" or tok.startswith("!"):
            continue
        tok = tok.rstrip("~'>")
        if ":" in tok:
            d = tok.split(":")[1]
            t += Fraction(d) if "/" in d else Fraction(d).limit_denominator(48)
        else:
            t += 1
    return float(t)


class Section:
    def __init__(self, score: "Score", name: str, bars: float, meter: float, bpm: float,
                 end_bpm: float | None, start: float):
        self.score, self.name, self.bars, self.meter = score, name, bars, meter
        self.bpm, self.end_bpm, self.start = bpm, end_bpm or bpm, start

    @property
    def beats(self) -> float:
        return self.bars * self.meter

    def at(self, bar: float = 1, beat: float = 1) -> float:
        """Global beat of `bar` (1-based) and `beat` (1-based) inside this section."""
        return self.start + (bar - 1) * self.meter + (beat - 1)

    def part(self, inst: str, text: str, bar: float = 1, beat: float = 1, vel: str = "mf",
             transpose: int = 0, **opts):
        s = self.at(bar, beat)
        if beat != 1:
            # Pickups: bar lines are counted from the next bar.
            pick = self.meter - (beat - 1)
            first, _, rest = text.partition("|")
            if rest and abs(length_beats(first) - pick) > 1e-6:
                raise ValueError(f"pickup in {self.name} is {length_beats(first)} beats, expected {pick}")
        if beat == 1:
            notes = parse(text, s, self.meter, DYN[vel], transpose)
        elif "|" in text:
            notes = self._parse_pickup(text, s, DYN[vel], transpose)
        else:
            notes = parse(text, s, 1e9, DYN[vel], transpose)
        self.score._add(inst, notes, **opts)
        end = max((n.beat + n.dur for n in notes), default=s)
        if end > self.start + self.beats + 1e-6:
            raise ValueError(f"{inst} runs past the end of section {self.name}")
        return self

    def _parse_pickup(self, text, s, vel, transpose):
        first, _, rest = text.partition("|")
        a = parse(first, s, 1e9, vel, transpose)
        b = parse(rest, s + length_beats(first), self.meter, vel, transpose)
        return a + b

    def hits(self, kind: str, beats: list[float] | str, bar: float = 1, vel: str = "f", every_bar: int = 0,
             bars: int = 1):
        """Unpitched percussion. `beats` are 1-based beat positions within the bar."""
        if isinstance(beats, str):
            beats = [float(b) for b in beats.split()]
        out = []
        for k in range(bars):
            for b in beats:
                out.append((self.at(bar + k, b), kind, DYN[vel]))
        self.score._hits(out)
        return self


@dataclass
class Track:
    inst: str
    notes: list = field(default_factory=list)
    attack: float = 0.0
    release: float = 0.35
    legato: float = 1.0  # multiply held length (overlap for slurs)
    pan: float = 0.0
    gain_db: float = 0.0
    send: float = 0.35  # reverb send
    double: int = 0  # extra detuned copies to thicken a solo sample into a section
    tail: float | None = None
    hpf: float = 0.0  # high-pass cutoff in Hz (0 = off)


class Score:
    def __init__(self, name: str, title: str, seed: int = 1):
        self.name, self.title, self.seed = name, title, seed
        self.sections: list[Section] = []
        self.tracks: dict[str, Track] = {}
        self.perc: list[tuple[float, str, int]] = []
        self.expr: dict[str, list[tuple[float, float]]] = {}
        self.markers: list[tuple[float, str]] = []
        self.end_pad = 6.0

    # ----- structure -----
    def section(self, name: str, bars: float, meter: float = 4, bpm: float = 72, end_bpm: float | None = None,
                seconds: float | None = None, rit: float = 1.0):
        """A run of bars in one metre. Give `seconds` (and optionally `rit`, end tempo / start tempo)
        to fit the section to a shot length instead of a fixed `bpm`."""
        if seconds is not None:
            beats = bars * meter
            if abs(rit - 1.0) < 1e-6:
                bpm, end_bpm = beats * 60.0 / seconds, None
            else:
                bpm = beats * 60.0 * np.log(rit) / ((rit - 1.0) * seconds)
                end_bpm = bpm * rit
        start = self.sections[-1].start + self.sections[-1].beats if self.sections else 0.0
        s = Section(self, name, bars, meter, bpm, end_bpm, start)
        self.sections.append(s)
        self.markers.append((start, name))
        return s

    def track(self, key: str, inst: str | None = None, **opts) -> Track:
        if key not in self.tracks:
            self.tracks[key] = Track(inst or key)
        for k, v in opts.items():
            setattr(self.tracks[key], k, v)
        return self.tracks[key]

    def _add(self, key, notes, **opts):
        tr = self.track(key, opts.pop("inst", None), **opts)
        tr.notes.extend(notes)

    def _hits(self, hits):
        self.perc.extend(hits)

    def swell(self, key: str, points: list[tuple[float, float]]):
        """Expression curve for a track: (global beat, dB). Linear in dB between points."""
        self.expr.setdefault(key, []).extend(points)

    # ----- time -----
    def time_of(self, beat: float) -> float:
        t = 0.0
        if beat <= 0:
            return beat * 60.0 / self.sections[0].bpm
        for s in self.sections:
            b = min(beat, s.start + s.beats) - s.start
            if s.bpm == s.end_bpm:
                t += b * 60.0 / s.bpm
            else:
                # tempo changes linearly across the section (in beats)
                k = (s.end_bpm - s.bpm) / s.beats
                if abs(k) < 1e-9:
                    t += b * 60.0 / s.bpm
                else:
                    t += 60.0 / k * np.log((s.bpm + k * b) / s.bpm)
            if beat <= s.start + s.beats:
                return t
        last = self.sections[-1]
        return t + (beat - last.start - last.beats) * 60.0 / last.end_bpm

    @property
    def total_beats(self):
        s = self.sections[-1]
        return s.start + s.beats

    @property
    def duration(self):
        return self.time_of(self.total_beats) + self.end_pad

    # ----- render -----
    def _humanize(self, key: str, n: Note, i: int):
        rng = np.random.default_rng(hash((self.seed, key, i)) & 0xFFFFFFFF)
        return float(rng.normal(0, 0.008)), int(rng.integers(-5, 6))

    def render_track(self, key: str, tr: Track) -> np.ndarray:
        total = int(self.duration * SR)
        buf = np.zeros((total + SR * 12, 2), np.float32)
        if tr.inst in orc.GM:
            notes = []
            for n in tr.notes:
                s = self.time_of(n.beat)
                e = self.time_of(n.beat + n.dur * tr.legato)
                notes.append((s, e - s, n.pitch, n.vel))
            expr = None
            if key in self.expr:
                pts = sorted(self.expr[key])
                ts = np.arange(0, self.duration, 0.05)
                db = np.interp([self._beat_at(t) for t in ts], [p[0] for p in pts], [p[1] for p in pts])
                expr = list(zip(ts, (10 ** (db / 20)).clip(0, 1)))
            y = orc.render_gm(orc.GM[tr.inst], notes, self.duration + 12, expr)
            buf[: len(y)] += y[: len(buf)]
            return buf[:total]
        for i, n in enumerate(sorted(tr.notes, key=lambda n: (n.beat, n.pitch))):
            dt, dv = self._humanize(key, n, i)
            s = max(0.0, self.time_of(n.beat) + dt)
            e = self.time_of(n.beat + n.dur * (0.5 if n.short else tr.legato))
            vel = int(np.clip(n.vel + dv, 1, 127))
            copies = [(0.0, 0)] + [((-1) ** k * 0.11 * ((k + 2) // 2), k + 1) for k in range(tr.double)]
            for cents, ci in copies:
                y = orc.render_note(tr.inst, n.pitch + cents, vel, max(0.05, e - s), tr.attack,
                                    tr.release if not n.short else 0.12, seed=i + ci * 7, tail=tr.tail)
                off = int((s + 0.006 * ci) * SR)
                if ci:
                    y = y[:, ::-1] * 0.8
                end = min(len(buf), off + len(y))
                buf[off:end] += y[: end - off]
        buf = buf[:total]
        if key in self.expr:
            buf *= self._expr_curve(key, total)[:, None]
        return buf

    def _beat_at(self, t: float) -> float:
        lo, hi = 0.0, self.total_beats + 64
        for _ in range(40):
            mid = (lo + hi) / 2
            if self.time_of(mid) < t:
                lo = mid
            else:
                hi = mid
        return lo

    def _expr_curve(self, key: str, total: int) -> np.ndarray:
        pts = sorted(self.expr[key])
        bt = np.array([self.time_of(p[0]) for p in pts])
        db = np.array([p[1] for p in pts])
        ts = np.arange(total) / SR
        return (10 ** (np.interp(ts, bt, db) / 20)).astype(np.float32)

    def render_perc(self) -> np.ndarray:
        total = int(self.duration * SR)
        buf = np.zeros((total + SR * 12, 2), np.float32)
        for i, (beat, kind, vel) in enumerate(sorted(self.perc)):
            if kind.startswith("timp:"):
                y = orc.render_note("timp", midi(kind[5:]), vel, 3.0, seed=i)
            else:
                y = orc.render_perc(kind, vel, seed=i)
            y = y * 10 ** (PERC_DB.get(kind.split(":")[0], -10) / 20)
            off = int(self.time_of(beat) * SR)
            if kind in SWELLS:
                # swells are placed so that their peak lands on the beat
                off -= int(SWELLS[kind] * SR)
                if off < 0:
                    y, off = y[-off:], 0
            end = min(len(buf), off + len(y))
            buf[off:end] += y[: end - off]
        return buf[:total]


# ---------------------------------------------------------------- mixing

def hall_ir(rt60: float = 3.2, predelay: float = 0.03, seed: int = 7) -> np.ndarray:
    """Synthetic concert-hall impulse response: early reflections and a decaying, darkening tail."""
    rng = np.random.default_rng(seed)
    n = int((rt60 * 1.3 + predelay) * SR)
    t = np.arange(n) / SR
    ir = np.zeros((n, 2), np.float32)
    bands = [(None, 600, 1.0), (600, 3000, 0.8), (3000, None, 0.5)]  # (lo, hi, rt60 factor)
    for ch in range(2):
        noise = rng.standard_normal(n).astype(np.float32)
        tail = np.zeros(n, np.float32)
        for lo, hi, f in bands:
            if lo is None:
                b, a = signal.butter(2, hi / (SR / 2), "low")
            elif hi is None:
                b, a = signal.butter(2, lo / (SR / 2), "high")
            else:
                b, a = signal.butter(2, [lo / (SR / 2), hi / (SR / 2)], "band")
            band = signal.lfilter(b, a, noise)
            tail += band * np.exp(-6.91 * t / (rt60 * f))
        onset = np.clip((t - predelay) / 0.08, 0, 1)
        tail *= onset
        for k in range(14):
            d = predelay * 0.4 + rng.uniform(0.005, 0.07)
            i = int(d * SR)
            tail[i] += rng.uniform(0.2, 0.6) * (1 if rng.random() > 0.5 else -1)
        ir[:, ch] = tail
    ir /= np.sqrt((ir ** 2).sum(axis=0, keepdims=True))
    return ir


def pan_stereo(x: np.ndarray, pan: float) -> np.ndarray:
    l = np.cos((pan + 1) * np.pi / 4) * np.sqrt(2)
    r = np.sin((pan + 1) * np.pi / 4) * np.sqrt(2)
    return x * np.array([l, r], np.float32)


def mix(score: Score, out_dir: str, stems: bool = False) -> str:
    os.makedirs(out_dir, exist_ok=True)
    total = int(score.duration * SR)
    dry = np.zeros((total, 2), np.float32)
    send = np.zeros((total, 2), np.float32)
    for key, tr in score.tracks.items():
        y = score.render_track(key, tr)
        if tr.hpf:
            sos = signal.butter(4, tr.hpf / (SR / 2), "high", output="sos")
            y = signal.sosfilt(sos, y, axis=0).astype(np.float32)
        y = pan_stereo(y, tr.pan) * 10 ** (tr.gain_db / 20)
        dry += y
        send += y * tr.send
        if stems:
            sf.write(os.path.join(out_dir, f"{score.name}__{key}.wav"), y, SR)
    if score.perc:
        p = score.render_perc()
        if stems:
            sf.write(os.path.join(out_dir, f"{score.name}__perc.wav"), p, SR)
        dry += p
        send += p * 0.3
    ir = hall_ir()
    wet = np.stack([signal.oaconvolve(send[:, c], ir[:, c])[:total] for c in range(2)], axis=1)
    out = dry * 0.85 + wet * 0.55
    # tidy the low end and master
    sos = signal.butter(4, 34 / (SR / 2), "high", output="sos")
    out = signal.sosfilt(sos, out, axis=0).astype(np.float32)
    peak = np.abs(out).max() + 1e-9
    out = out / peak * 0.5
    # fade the very end
    k = int(1.5 * SR)
    out[-k:] *= np.linspace(1, 0, k)[:, None]
    raw = os.path.join(out_dir, f"{score.name}.raw.wav")
    sf.write(raw, out, SR, subtype="FLOAT")
    return raw


def master(raw: str, out_base: str, lufs: float = -16.0) -> dict:
    """Loudness-normalise with a limiter and write Ogg Vorbis (game) and MP3 (preview)."""
    wav = out_base + ".wav"
    lim = "alimiter=limit=0.89:attack=5:release=80:level=false"
    probe = subprocess.run(["ffmpeg", "-hide_banner", "-i", raw, "-af",
                            f"{lim},loudnorm=I={lufs}:TP=-1.0:LRA=20:print_format=json", "-f", "null", "-"],
                           capture_output=True, text=True, check=True).stderr
    m = json.loads(probe[probe.rindex("{"): probe.rindex("}") + 1])
    af = (f"{lim},loudnorm=I={lufs}:TP=-1.0:LRA=20:linear=true:measured_I={m['input_i']}:"
          f"measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:"
          f"offset={m['target_offset']}")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", raw, "-af", af, "-ar", str(SR), wav], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "6",
                    out_base + ".ogg"], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "192k",
                    out_base + ".mp3"], check=True)
    return {"wav": wav, "ogg": out_base + ".ogg", "mp3": out_base + ".mp3"}


def export_midi(score: Score, path: str):
    """Standard MIDI file of every part, so a composer can re-voice the cue with other libraries."""
    import mido

    tpb = 960
    mid = mido.MidiFile(ticks_per_beat=tpb, type=1)
    meta = mido.MidiTrack()
    mid.tracks.append(meta)
    meta.append(mido.MetaMessage("track_name", name=score.title, time=0))
    events = []
    for s in score.sections:
        events.append((s.start, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(s.bpm))))
        num = int(s.meter) if float(s.meter).is_integer() else int(s.meter * 2)
        den = 4 if float(s.meter).is_integer() else 8
        events.append((s.start, mido.MetaMessage("time_signature", numerator=num, denominator=den)))
        events.append((s.start, mido.MetaMessage("marker", text=s.name)))
    last = 0
    for b, m in sorted(events, key=lambda e: e[0]):
        tick = int(round(b * tpb))
        m.time = tick - last
        last = tick
        meta.append(m)
    for ch, (key, tr) in enumerate(score.tracks.items()):
        t = mido.MidiTrack()
        mid.tracks.append(t)
        t.append(mido.MetaMessage("track_name", name=key, time=0))
        c = ch % 15 + (1 if ch % 15 >= 9 else 0)
        ev = []
        for n in tr.notes:
            ev.append((n.beat, 1, mido.Message("note_on", note=n.pitch, velocity=n.vel, channel=c)))
            ev.append((n.beat + n.dur * (0.5 if n.short else 1), 0,
                       mido.Message("note_off", note=n.pitch, velocity=0, channel=c)))
        ev.sort(key=lambda e: (e[0], e[1]))
        last = 0
        for b, _, m in ev:
            tick = int(round(b * tpb))
            m.time = max(0, tick - last)
            last = max(last, tick)
            t.append(m)
    mid.save(path)


def cue_sheet(score: Score) -> dict:
    return {
        "id": score.name,
        "title": score.title,
        "duration": round(score.duration, 2),
        "markers": [{"time": round(score.time_of(b), 2), "name": n} for b, n in score.markers],
    }
