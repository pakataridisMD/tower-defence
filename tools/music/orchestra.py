"""A small sampler that plays the CC0 Versilian Chamber Orchestra 2 samples.

Each instrument is a folder of one-shot WAVs named with a note, a velocity layer and
sometimes a round robin. The sampler picks the nearest sample, repitches it, stretches
long notes with crossfaded loops and shapes the envelope. Choir, celesta and tubular
bells are not in VSCO 2, so those parts are rendered by FluidSynth from FluidR3_GM (MIT).
"""
from __future__ import annotations

import functools
import glob
import json
import os
import re
import subprocess
import tempfile

import numpy as np
import soundfile as sf

SR = 44100
HERE = os.path.dirname(os.path.abspath(__file__))
VSCO = os.environ.get("VSCO_DIR", os.path.join(HERE, ".samples", "VSCO-2-CE"))
SF2 = os.environ.get("GM_SF2", "/usr/share/sounds/sf2/FluidR3_GM.sf2")
CACHE = os.path.join(HERE, ".cache")

NOTE_RE = re.compile(r"_([A-G])(#|b)?(-?\d)(?=_|\.)")
VEL_RE = re.compile(r"_v(\d)")
DYN_ORDER = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]
DYN_RE = re.compile(r"_(ppp|pp|p|mp|mf|f|ff|fff)(?=_|\.)")
STEP = {"C": 0, "D": 2, "E": 4, "F": 5, "G": 7, "A": 9, "B": 11}


def name_to_midi(letter: str, acc: str | None, octave: int) -> int:
    m = 12 * (octave + 1) + STEP[letter]
    if acc == "#":
        m += 1
    elif acc == "b":
        m -= 1
    return m


# name: (folder under VSCO, kind, options)
#   oct: octave correction for this folder's file names (VSCO folders disagree; checked by ear-free
#        pitch detection in `python3 orchestra.py --check`)
#   loop: allow loop-stretching for long notes
#   gain: level trim so sections sit together at equal velocity
INSTRUMENTS: dict[str, dict] = {
    "vln": dict(dir="Strings/Violin Section/susVib", loop=True, gain=1.0),
    "vln_trem": dict(dir="Strings/Violin Section/Trem", loop=True, gain=0.8),
    "vln_pizz": dict(dir="Strings/Violin Section/Pizz", gain=1.2),
    "vln_spic": dict(dir="Strings/Violin Section/Spic", gain=1.0),
    "vla": dict(dir="Strings/Viola Section/susvib", loop=True, gain=1.0),
    "vla_spic": dict(dir="Strings/Viola Section/spic", gain=1.0),
    "vla_trem": dict(dir="Strings/Viola Section/trem", loop=True, gain=0.8),
    "vc": dict(dir="Strings/Cello Section/susvib", loop=True, gain=1.0),
    "vc_spic": dict(dir="Strings/Cello Section/spic", gain=1.0),
    "vc_pizz": dict(dir="Strings/Cello Section/pizzT", gain=1.2),
    "vc_trem": dict(dir="Strings/Cello Section/trem", loop=True, gain=0.8),
    "cb": dict(dir="Strings/Solo Contrabass/SusVib", loop=True, gain=1.3),
    "cb_pizz": dict(dir="Strings/Solo Contrabass/Pizz", gain=1.3),
    "cb_spic": dict(dir="Strings/Solo Contrabass/Spic", gain=1.3),
    "solo_vln": dict(dir="Strings/Solo Violin/Arco Vib", loop=True, gain=1.0),
    "harp": dict(dir="Strings/Harp", gain=1.0),
    "hn": dict(dir="Brass/F Horn/sus", loop=True, gain=1.0),
    "hn_stac": dict(dir="Brass/F Horn/stac", gain=1.0),
    "tpt": dict(dir="Brass/Trumpet/sus", loop=True, gain=0.9),
    "tbn": dict(dir="Brass/Tenor Trombone/sus", loop=True, gain=1.0),
    "tuba": dict(dir="Brass/Tuba/sus", loop=True, gain=1.0),
    "fl": dict(dir="Woodwinds/Flute/susvib", loop=True, gain=1.0),
    "ob": dict(dir="Woodwinds/Oboe/Vib", loop=True, gain=1.0),
    "cl": dict(dir="Woodwinds/Clarinet/susLong", loop=True, gain=1.0),
    "bsn": dict(dir="Woodwinds/Bassoon/sus", loop=True, gain=1.0),
    "glock": dict(dir="Percussion/Glock", gain=0.8),
}

# Unpitched and timpani: picked by file pattern.
PERC = {
    "timp": "Percussion/Timpani/Timpani*_Hit_*.wav",
    "bd": "Percussion/BDrumNewhit_*.wav",
    "crash": "Percussion/cymbal-crash1_*.wav",
    "sus_cym": "Percussion/susCymb1-cresc-Long*",
    "gong": "Percussion/gongHit_*.wav",
    "anvil": "Percussion/Anvil_Hit1_*.wav",
    "snare_roll": "Percussion/Snare2-rollSN*",
    "bd_rub": "Percussion/bassdrum_rub*",
    "snare": "Percussion/Snare2-HitSN_*",
    "logdrum": "Percussion/LogDrumLo_*",
    "tumba": "Percussion/Tumba-HitN_*",
    "tenor": "Percussion/timpsnaretenor_*",
}

# General MIDI programs rendered with FluidSynth.
GM = {"choir": 52, "oohs": 53, "celesta": 8, "bells": 14, "voice_solo": 53}


def _trim(x: np.ndarray, thresh_db: float = -54.0) -> np.ndarray:
    mono = np.abs(x).max(axis=1)
    peak = mono.max() + 1e-9
    idx = np.nonzero(mono > peak * 10 ** (thresh_db / 20))[0]
    if len(idx) == 0:
        return x
    start = max(0, idx[0] - int(0.004 * SR))
    end = min(len(x), idx[-1] + int(0.05 * SR))
    return x[start:end]


@functools.lru_cache(maxsize=8192)
def level(path: str) -> float:
    """RMS of the body of a sample, used to even out recording levels between files."""
    x = load(path)
    seg = x[int(0.05 * SR): int(1.5 * SR)]
    if len(seg) < SR // 10:
        seg = x
    return float(np.sqrt((seg ** 2).mean()) + 1e-6)


TARGET_RMS = 0.1


@functools.lru_cache(maxsize=4096)
def load(path: str) -> np.ndarray:
    x, sr = sf.read(path, dtype="float32", always_2d=True)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    if sr != SR:
        n = int(len(x) * SR / sr)
        t = np.arange(n) * (sr / SR)
        x = np.stack([np.interp(t, np.arange(len(x)), x[:, c]) for c in range(2)], axis=1).astype(np.float32)
    return _trim(x)


def detect_f0(x: np.ndarray, lo: float = 25.0, hi: float = 2200.0) -> float:
    """Autocorrelation pitch of a stable stretch of the sample (YIN-style difference)."""
    mono = x.mean(axis=1)
    a = int(0.25 * SR)
    seg = mono[a:a + int(0.5 * SR)]
    if len(seg) < 4096:
        seg = mono[: int(0.5 * SR)]
    seg = seg - seg.mean()
    n = len(seg)
    f = np.fft.rfft(seg, 2 * n)
    ac = np.fft.irfft(f * np.conj(f))[:n]
    energy = np.cumsum(seg[::-1] ** 2)[::-1]
    d = energy[0] + energy - 2 * ac
    d[0] = 1
    cmnd = d * np.arange(n) / np.maximum(np.cumsum(d), 1e-12)
    lag_lo, lag_hi = int(SR / hi), min(int(SR / lo), n - 1)
    seg_c = cmnd[lag_lo:lag_hi]
    below = np.nonzero(seg_c < 0.15)[0]
    if len(below):
        i = below[0]
        while i + 1 < len(seg_c) and seg_c[i + 1] < seg_c[i]:
            i += 1
    else:
        i = int(np.argmin(seg_c))
    lag = i + lag_lo
    return SR / lag


def midi_of(f: float) -> float:
    return 69 + 12 * np.log2(f / 440.0)


class Zone:
    __slots__ = ("path", "root", "vel", "rr")

    def __init__(self, path, root, vel, rr):
        self.path, self.root, self.vel, self.rr = path, root, vel, rr


def _scan_pitched(name: str) -> list[Zone]:
    spec = INSTRUMENTS[name]
    files = sorted(glob.glob(os.path.join(VSCO, spec["dir"], "*.wav")))
    if not files:
        raise FileNotFoundError(f"no samples for {name} in {spec['dir']} (run fetch_samples.sh)")
    parsed = []
    for p in files:
        base = os.path.basename(p)
        m = NOTE_RE.search(base)
        if not m:
            continue
        named = name_to_midi(m.group(1), m.group(2), int(m.group(3)))
        v = VEL_RE.search(base)
        if v:
            vel = int(v.group(1))
        else:
            dm = DYN_RE.search(base)
            vel = DYN_ORDER.index(dm.group(1)) + 1 if dm else 1
        parsed.append((p, named, vel))
    # Octave correction: compare names with detected pitch on a few files.
    offs = []
    for p, named, _ in parsed[:: max(1, len(parsed) // 8)]:
        try:
            d = midi_of(detect_f0(load(p)))
        except Exception:
            continue
        offs.append(int(round((d - named) / 12.0)) * 12)
    off = max(set(offs), key=offs.count) if offs else 0
    zones = []
    rr_count: dict = {}
    for p, named, v in parsed:
        key = (named, v)
        rr_count[key] = rr_count.get(key, 0) + 1
        zones.append(Zone(p, named + off, v, rr_count[key]))
    return zones


def _scan_timp() -> list[Zone]:
    zones = []
    for p in sorted(glob.glob(os.path.join(VSCO, PERC["timp"]))):
        x = load(p)
        # Timpani: strongest spectral peak 60-260 Hz in the ring after the stick noise.
        seg = x[int(0.08 * SR): int(0.9 * SR)].mean(axis=1)
        spec = np.abs(np.fft.rfft(seg * np.hanning(len(seg))))
        freqs = np.fft.rfftfreq(len(seg), 1 / SR)
        band = (freqs > 60) & (freqs < 260)
        f = freqs[band][np.argmax(spec[band])]
        v = VEL_RE.search(os.path.basename(p))
        zones.append(Zone(p, midi_of(f), int(v.group(1)) if v else 1, 1))
    return zones


@functools.lru_cache(maxsize=None)
def zones_for(name: str) -> list[Zone]:
    os.makedirs(CACHE, exist_ok=True)
    cpath = os.path.join(CACHE, f"zones_{name}.json")
    if os.path.exists(cpath):
        with open(cpath) as fh:
            return [Zone(*z) for z in json.load(fh)]
    zs = _scan_timp() if name == "timp" else _scan_pitched(name)
    with open(cpath, "w") as fh:
        json.dump([[z.path, z.root, z.vel, z.rr] for z in zs], fh)
    return zs


def _stretch(x: np.ndarray, need: int) -> np.ndarray:
    """Make a sustained sample at least `need` frames long with crossfaded loops of its body."""
    if len(x) >= need:
        return x
    a, b = int(len(x) * 0.25), int(len(x) * 0.8)
    body = x[a:b]
    xf = min(int(0.35 * SR), len(body) // 3)
    out = x[:b].copy()
    fade = np.sin(np.linspace(0, np.pi / 2, xf))[:, None].astype(np.float32)
    rng = np.random.default_rng(len(x) + need)
    while len(out) < need:
        # start each loop at a slightly different point so the repeats are less obvious
        s = int(rng.integers(0, max(1, len(body) // 3)))
        piece = body[s:]
        head = out[-xf:] * fade[::-1] + piece[:xf] * fade
        out = np.concatenate([out[:-xf], head, piece[xf:]])
    return out


def pick(zones: list[Zone], pitch: float, vel: int, rr_seed: int) -> Zone:
    roots = sorted({z.root for z in zones}, key=lambda r: (abs(r - pitch), r < pitch))
    root = roots[0]
    cands = [z for z in zones if z.root == root]
    layers = sorted({z.vel for z in cands})
    want = layers[min(len(layers) - 1, int(vel / 128 * len(layers)))]
    cands = [z for z in cands if z.vel == want]
    return cands[rr_seed % len(cands)]


def render_note(inst: str, pitch: float, vel: int, dur: float, attack: float = 0.0,
                release: float = 0.35, seed: int = 0, tail: float | None = None) -> np.ndarray:
    """Render one note. `dur` is the held time in seconds; the release is added after it.
    `tail` (seconds) caps one-shots such as plucks; None keeps the natural ring."""
    zones = zones_for(inst)
    z = pick(zones, pitch, vel, seed)
    x = load(z.path)
    ratio = 2 ** ((pitch - z.root) / 12.0)
    spec = INSTRUMENTS.get(inst, {})
    sustained = spec.get("loop", False)
    if sustained:
        out_len = int((dur + release) * SR)
    else:
        ring = len(x) / ratio / SR
        out_len = int(min(ring, tail if tail is not None else ring) * SR)
    need_in = int(out_len * ratio) + 2
    if sustained:
        x = _stretch(x, need_in)
    idx = np.arange(out_len) * ratio
    idx = idx[idx < len(x) - 1]
    i0 = idx.astype(np.int64)
    frac = (idx - i0)[:, None].astype(np.float32)
    y = x[i0] * (1 - frac) + x[i0 + 1] * frac
    n = len(y)
    env = np.ones(n, dtype=np.float32)
    if attack > 0:
        k = min(n, int(attack * SR))
        env[:k] = np.sin(np.linspace(0, np.pi / 2, k)) ** 2
    if sustained:
        rs = int(dur * SR)
        if rs < n:
            k = n - rs
            env[rs:] *= np.cos(np.linspace(0, np.pi / 2, k)) ** 2
    elif tail is not None:
        k = min(n, int(0.08 * SR))
        env[n - k:] *= np.linspace(1, 0, k)
    norm = min(TARGET_RMS / level(z.path), 30.0)
    gain = norm * spec.get("gain", 1.0) * (0.12 + 0.88 * (vel / 127.0) ** 1.7)
    return (y * env[:, None] * gain).astype(np.float32)


def render_perc(kind: str, vel: int, seed: int = 0) -> np.ndarray:
    files = sorted(glob.glob(os.path.join(VSCO, PERC[kind])))
    if not files:
        raise FileNotFoundError(kind)
    vels = sorted({int(m.group(1)) for f in files if (m := VEL_RE.search(os.path.basename(f)))})
    if vels:
        want = vels[min(len(vels) - 1, int(vel / 128 * len(vels)))]
        cand = [f for f in files if f"_v{want}" in os.path.basename(f)] or files
    else:
        # dynamic words in names (pp/mp/mf/f/ff/fff)
        order = ["ppp", "pp", "p", "mp", "mf", "f", "ff", "fff"]
        dyn = {f: next((d for d in order[::-1] if f"_{d}" in os.path.basename(f)), "mf") for f in files}
        levels = sorted(set(dyn.values()), key=order.index)
        want = levels[min(len(levels) - 1, int(vel / 128 * len(levels)))]
        cand = [f for f in files if dyn[f] == want]
    path = cand[seed % len(cand)]
    x = load(path) * min(TARGET_RMS * 1.5 / level(path), 30.0)
    return (x * (0.15 + 0.85 * (vel / 127.0) ** 1.5)).astype(np.float32)


def render_gm(program: int, notes: list[tuple[float, float, int, int]], total: float,
              expr: list[tuple[float, float]] | None = None) -> np.ndarray:
    """Render notes (start_s, dur_s, midi, vel) on one GM program with FluidSynth.
    `expr` is a list of (time_s, gain 0..1) sent as CC11."""
    import mido

    mid = mido.MidiFile(ticks_per_beat=960)
    tr = mido.MidiTrack()
    mid.tracks.append(tr)
    tempo = 500000  # 120 bpm, so one second = 1920 ticks
    tr.append(mido.MetaMessage("set_tempo", tempo=tempo, time=0))
    tr.append(mido.Message("program_change", program=program, channel=0, time=0))
    tr.append(mido.Message("control_change", control=7, value=110, channel=0, time=0))
    ev = []
    for s, d, m, v in notes:
        ev.append((s, 1, mido.Message("note_on", note=int(m), velocity=int(v), channel=0)))
        ev.append((s + d, 0, mido.Message("note_off", note=int(m), velocity=0, channel=0)))
    for t, g in expr or []:
        ev.append((t, 0, mido.Message("control_change", control=11, value=int(max(0, min(127, g * 127))), channel=0)))
    ev.sort(key=lambda e: (e[0], e[1]))
    last = 0
    for t, _, msg in ev:
        tick = int(round(t * 1920))
        msg.time = max(0, tick - last)
        last = max(last, tick)
        tr.append(msg)
    tr.append(mido.MetaMessage("end_of_track", time=int(2 * 1920)))
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "p.mid")
        wp = os.path.join(td, "p.wav")
        mid.save(mp)
        subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.6", "-r", str(SR), "-R", "0", "-C", "0",
                        "-F", wp, SF2, mp], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        y, _ = sf.read(wp, dtype="float32", always_2d=True)
        y *= 4.0
    n = int(total * SR)
    if len(y) < n:
        y = np.concatenate([y, np.zeros((n - len(y), 2), np.float32)])
    return y


if __name__ == "__main__":
    import sys

    if "--check" in sys.argv:
        for name in list(INSTRUMENTS) + ["timp"]:
            zs = zones_for(name)
            roots = sorted({round(z.root) for z in zs})
            print(f"{name:10s} {len(zs):3d} files  roots {roots[0]}..{roots[-1]}")
