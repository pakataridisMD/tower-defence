"""Real recordings for the sound recipes: orchestral and found-sound samples, sampled choir and spoken voices.

Sources, all free for commercial games (details in assets/audio/sfx/LICENSE.md):

* VSCO 2 Community Edition by Versilian Studios: CC0 1.0. Percussion, brass, strings and the
  "Miscellania" found sounds (metal and glass hits, chains, scrapes, bowed cymbals, gong scrapes).
  `fetch_samples.sh` clones it at a pinned commit into tools/sfx/.samples/vsco.
* FluidR3_GM sound font: MIT licence. Only the sampled choir ("Aahs" and "Oohs"), rendered by FluidSynth.
* Kokoro-82M text to speech: Apache-2.0. Speaks the bosses' lines and shouts; the model comes from
  the kokoro-onnx GitHub releases into tools/sfx/.samples/kokoro.

Nothing here is copied into the game as is: every sample is cut, pitched, layered and mixed into new sounds.
Generated speech is cached in tools/sfx/.cache so rerenders are fast and stay the same.
"""

from __future__ import annotations

import functools
import hashlib
import os
import struct
import subprocess
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from dsp import SR, n_of

HERE = Path(__file__).resolve().parent
SAMPLES = Path(os.environ.get("SFX_SAMPLES", HERE / ".samples"))
VSCO = SAMPLES / "vsco"
KOKORO = Path(os.environ.get("KOKORO_DIR", SAMPLES / "kokoro"))
CACHE = HERE / ".cache"
SOUND_FONT = Path(os.environ.get("SFX_SOUNDFONT", "/usr/share/sounds/sf2/FluidR3_GM.sf2"))


class MissingSamples(RuntimeError):
    pass


def _check(path: Path) -> Path:
    if not path.exists():
        raise MissingSamples(f"{path} is missing: run tools/sfx/fetch_samples.sh first")
    return path


@functools.lru_cache(maxsize=None)
def files(pattern: str) -> tuple[Path, ...]:
    """Sorted VSCO files matching a glob relative to the library root."""
    found = tuple(sorted(_check(VSCO).glob(pattern)))
    if not found:
        raise MissingSamples(f"no samples match {pattern} in {VSCO}")
    return found


@functools.lru_cache(maxsize=512)
def _read(path: str) -> np.ndarray:
    x, sr = sf.read(path, always_2d=True, dtype="float64")
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    x = x[:, :2]
    if sr != SR:
        g = np.gcd(sr, SR)
        x = signal.resample_poly(x, SR // g, sr // g, axis=0)
    # Cut the silence before the attack so hits land where they are placed.
    level = np.max(np.abs(x), axis=1)
    peak = level.max() + 1e-12
    start = int(np.argmax(level > peak * 0.02))
    start = max(0, start - int(0.002 * SR))
    x = x[start:] / peak
    x.setflags(write=False)
    return x


def load(pattern: str, rng: np.random.Generator | None = None, index: int | None = None) -> np.ndarray:
    """One stereo sample, normalised to peak 1: a random match, or the index-th match."""
    found = files(pattern)
    if index is None:
        index = int(rng.integers(len(found))) if rng is not None else 0
    return _read(str(found[index % len(found)])).copy()


def mono(x: np.ndarray) -> np.ndarray:
    return x.mean(axis=1) if x.ndim == 2 else x


def cut(x: np.ndarray, start: float, seconds: float | None = None, fade_out: float = 0.05) -> np.ndarray:
    a = n_of(start) if start > 0 else 0
    y = x[a:] if seconds is None else x[a:a + n_of(seconds)]
    y = y.copy()
    f = min(len(y), n_of(fade_out))
    if f > 1:
        ramp = np.linspace(1, 0, f)
        y[-f:] = (y[-f:].T * ramp).T
    return y


def speed(x: np.ndarray, ratio: float) -> np.ndarray:
    """Tape-style pitch change: ratio 0.5 is an octave down and twice as long."""
    if abs(ratio - 1) < 1e-4:
        return x.copy()
    up, down = _ratio(1 / ratio)
    return signal.resample_poly(x, up, down, axis=0)


def semis(x: np.ndarray, st: float) -> np.ndarray:
    return speed(x, 2 ** (st / 12))


def _ratio(r: float) -> tuple[int, int]:
    from fractions import Fraction
    f = Fraction(r).limit_denominator(400)
    return max(1, f.numerator), max(1, f.denominator)


def stretch(x: np.ndarray, st: float = 0.0, tempo: float = 1.0, formant: bool = False) -> np.ndarray:
    """Pitch and tempo change independently (Rubber Band through ffmpeg)."""
    if abs(st) < 1e-3 and abs(tempo - 1) < 1e-3:
        return x.copy()
    stereo_in = x.ndim == 2
    with tempfile.TemporaryDirectory() as tmp:
        src, dst = Path(tmp) / "in.wav", Path(tmp) / "out.wav"
        sf.write(src, x.astype(np.float32), SR, subtype="FLOAT")
        opts = f"pitch={2 ** (st / 12):.6f}:tempo={tempo:.6f}:pitchq=quality:window=standard"
        if formant:
            opts += ":formant=preserved"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(src), "-af", f"rubberband={opts}",
                        "-ar", str(SR), str(dst)], check=True)
        y, _ = sf.read(dst, always_2d=stereo_in, dtype="float64")
    return y


# --- Spoken voices ------------------------------------------------------------------------------

_kokoro = None


def _model():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(str(_check(KOKORO / "kokoro-v1.0.onnx")), str(_check(KOKORO / "voices-v1.0.bin")))
    return _kokoro


def speak(text: str, voice: str = "am_onyx", rate: float = 0.9, lang: str = "en-us") -> np.ndarray:
    """A spoken line as mono at SR, cached on disk. `voice` may blend two voices: "am_onyx:0.6,bm_george:0.4"."""
    key = hashlib.sha1(f"{text}|{voice}|{rate}|{lang}|v1".encode()).hexdigest()[:16]
    path = CACHE / "speech" / f"{key}.wav"
    if not path.exists():
        model = _model()
        if ":" in voice:
            style = None
            for part in voice.split(","):
                name, w = part.split(":")
                s = model.get_voice_style(name) * float(w)
                style = s if style is None else style + s
        else:
            style = voice
        audio, sr = model.create(text, voice=style, speed=rate, lang=lang)
        audio = np.asarray(audio, dtype="float64")
        g = np.gcd(sr, SR)
        audio = signal.resample_poly(audio, SR // g, sr // g)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(f".{os.getpid()}.tmp.wav")
        sf.write(tmp, audio.astype(np.float32), SR, subtype="FLOAT")
        tmp.replace(path)
    x, _ = sf.read(path, dtype="float64")
    level = np.abs(x)
    nz = np.nonzero(level > level.max() * 0.01)[0]
    if len(nz):
        x = x[max(0, nz[0] - 400): nz[-1] + 2000]
    f = min(len(x) // 4, int(0.012 * SR))
    x[:f] *= np.linspace(0, 1, f) ** 2
    x[-f:] *= np.linspace(1, 0, f)
    return x / (np.max(np.abs(x)) + 1e-12)


# --- Sampled choir (FluidR3_GM through FluidSynth) ----------------------------------------------

CHOIR_AAHS = 52
VOICE_OOHS = 53


def _midi(notes: list[tuple[int, float, float, int]], program: int, bpm_ticks: int = 480) -> bytes:
    """A one-track MIDI file. notes: (midi note, start s, length s, velocity). 120 bpm, so 1 s = 2 beats."""
    events = []
    for note, start, length, vel in notes:
        events.append((start, 0x90, note, vel))
        events.append((start + length, 0x80, note, 0))
    events.sort(key=lambda e: (e[0], e[1] == 0x90))
    ticks_per_s = bpm_ticks * 2

    def vlq(v: int) -> bytes:
        out = [v & 0x7F]
        v >>= 7
        while v:
            out.insert(0, (v & 0x7F) | 0x80)
            v >>= 7
        return bytes(out)

    body = bytearray(vlq(0) + bytes([0xC0, program]))
    body += vlq(0) + bytes([0xB0, 91, 0])  # no sound-font reverb: the recipes add their own space
    body += vlq(0) + bytes([0xB0, 93, 0])
    now = 0
    for t, kind, note, vel in events:
        tick = int(round(t * ticks_per_s))
        body += vlq(tick - now) + bytes([kind, note, vel])
        now = tick
    body += vlq(int(ticks_per_s)) + b"\xff\x2f\x00"
    header = b"MThd" + struct.pack(">IHHH", 6, 0, 1, bpm_ticks)
    return header + b"MTrk" + struct.pack(">I", len(body)) + bytes(body)


def choir(notes: list[tuple[int, float, float, int]], program: int = CHOIR_AAHS) -> np.ndarray:
    """Sampled choir playing notes (midi, start, length, velocity), stereo at SR, cached."""
    key = hashlib.sha1(f"{notes}|{program}|v1".encode()).hexdigest()[:16]
    path = CACHE / "choir" / f"{key}.wav"
    if not path.exists():
        _check(SOUND_FONT)
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            mid = Path(tmp) / "x.mid"
            mid.write_bytes(_midi(notes, program))
            out = Path(tmp) / "x.wav"
            subprocess.run(["fluidsynth", "-ni", "-q", "-g", "0.6", "-r", str(SR), "-R", "0", "-C", "0",
                            "-F", str(out), str(SOUND_FONT), str(mid)], check=True,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            x, _ = sf.read(out, always_2d=True, dtype="float64")
            tmp_path = path.with_suffix(f".{os.getpid()}.tmp.wav")
            sf.write(tmp_path, x.astype(np.float32), SR, subtype="FLOAT")
            tmp_path.replace(path)
    x, _ = sf.read(path, always_2d=True, dtype="float64")
    return x / (np.max(np.abs(x)) + 1e-12)
