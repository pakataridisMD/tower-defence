"""Trailer-style voices and sound design for the score.

- crowd(): gang shouts ("HEY!", "HA!", "HOLD!") from many Kokoro TTS voices, varied in pitch and
  timing, driven hard and spread across the stereo field.
- sung(): a chanting choir. Every voice speaks the syllable, then TD-PSOLA flattens it onto the
  written note and holds the vowel, so the words land on pitch. Layer it over the "choir" pad.
- braam(), sub_drop(), riser(), impact(): synthesised trailer hits.

Kokoro-82M is Apache-2.0 (commercial use is fine). Fetch it with tools/voice/fetch_model.sh or set
KOKORO_DIR. Rendered syllables are cached in tools/music/.cache/tts.
"""
from __future__ import annotations

import functools
import hashlib
import os

import numpy as np
from scipy import signal

from orchestra import CACHE, SR

KOKORO_DIR = os.environ.get("KOKORO_DIR", os.path.join(os.path.dirname(__file__), "..", "voice", "model"))
MEN = ["am_adam", "am_echo", "am_eric", "am_fenrir", "am_liam", "am_michael", "am_onyx", "am_puck",
       "bm_daniel", "bm_fable", "bm_george", "bm_lewis"]
WOMEN = ["af_kore", "af_nova", "af_sarah", "af_jessica", "bf_emma", "bf_isabella", "bf_alice", "af_river"]


@functools.lru_cache(maxsize=1)
def _kokoro():
    from kokoro_onnx import Kokoro

    return Kokoro(os.path.join(KOKORO_DIR, "kokoro-v1.0.onnx"), os.path.join(KOKORO_DIR, "voices-v1.0.bin"))


def tts(text: str, voice: str, speed: float = 1.0) -> np.ndarray:
    """Mono float32 at SR, trimmed to the spoken sound."""
    os.makedirs(os.path.join(CACHE, "tts"), exist_ok=True)
    key = hashlib.sha1(f"{text}|{voice}|{speed}".encode()).hexdigest()[:16]
    path = os.path.join(CACHE, "tts", key + ".npy")
    if os.path.exists(path):
        return np.load(path)
    lang = "en-gb" if voice.startswith("b") else "en-us"
    y, sr = _kokoro().create(text, voice=voice, speed=speed, lang=lang)
    y = np.asarray(y, np.float32)
    if sr != SR:
        y = signal.resample_poly(y, SR, sr).astype(np.float32)
    env = np.abs(y)
    idx = np.nonzero(env > env.max() * 0.03)[0]
    y = y[max(0, idx[0] - 200): idx[-1] + 400] if len(idx) else y
    np.save(path, y)
    return y


def _resample(x: np.ndarray, semis: float) -> np.ndarray:
    r = 2 ** (semis / 12)
    idx = np.arange(0, len(x) - 1, r)
    return np.interp(idx, np.arange(len(x)), x).astype(np.float32)


def _drive(x: np.ndarray, amount: float) -> np.ndarray:
    peak = np.abs(x).max() + 1e-9
    return (np.tanh(x / peak * amount) / np.tanh(amount)).astype(np.float32)


def _spread(layers: list[np.ndarray], rng, max_delay: float = 0.035) -> np.ndarray:
    n = max(len(l) for l in layers) + int(max_delay * SR) + 1
    out = np.zeros((n, 2), np.float32)
    for i, l in enumerate(layers):
        d = int(rng.uniform(0, max_delay) * SR)
        pan = rng.uniform(-0.85, 0.85)
        g = np.array([np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)], np.float32) * np.sqrt(2)
        out[d:d + len(l)] += l[:, None] * g
    return out


def crowd(text: str, n: int = 14, women: int = 4, seed: int = 0, drive: float = 2.5) -> np.ndarray:
    """A gang shout. Returns stereo with the shout's onset at sample 0, peak-normalised to 0.5."""
    rng = np.random.default_rng(seed + len(text))
    voices = [MEN[i % len(MEN)] for i in range(n - women)] + [WOMEN[i % len(WOMEN)] for i in range(women)]
    layers = []
    for i, v in enumerate(voices):
        y = tts(text, v, speed=1.15)
        y = _resample(y, rng.uniform(-2.5, 1.0))
        y = _drive(y, drive)
        b, a = signal.butter(2, [120 / (SR / 2), 7000 / (SR / 2)], "band")
        layers.append(signal.lfilter(b, a, y).astype(np.float32))
    out = _spread(layers, rng)
    return out / (np.abs(out).max() + 1e-9) * 0.5


# ------------------------------------------------------------------ TD-PSOLA

def _f0_track(x: np.ndarray, hop: int, frame: int) -> np.ndarray:
    f0 = []
    for s in range(0, max(1, len(x) - frame), hop):
        seg = x[s:s + frame] - x[s:s + frame].mean()
        if np.abs(seg).max() < 0.02 * (np.abs(x).max() + 1e-9):
            f0.append(0.0)
            continue
        ac = np.correlate(seg, seg, "full")[frame - 1:]
        lo, hi = int(SR / 400), int(SR / 70)
        if hi >= len(ac):
            f0.append(0.0)
            continue
        lag = lo + int(np.argmax(ac[lo:hi]))
        f0.append(SR / lag if ac[lag] > 0.35 * ac[0] else 0.0)
    return np.array(f0)


def psola(x: np.ndarray, target_hz: float, out_len: int, hold_from: float = 0.55) -> np.ndarray:
    """Put speech on one pitch and stretch it to out_len samples. The stretch happens in the vowel
    (from `hold_from` of the way through the voiced part), so the consonants keep their timing."""
    hop, frame = 220, 1024
    f0 = _f0_track(x, hop, frame)
    voiced = np.nonzero(f0 > 0)[0]
    if len(voiced) < 3:
        y = np.zeros(out_len, np.float32)
        y[: min(out_len, len(x))] = x[:out_len]
        return y
    # analysis marks: one per period through voiced frames, every 5 ms elsewhere
    marks = []
    t = 0
    while t < len(x) - 1:
        fi = min(len(f0) - 1, t // hop)
        period = int(SR / f0[fi]) if f0[fi] > 0 else int(0.005 * SR)
        marks.append((t, f0[fi] > 0, period))
        t += period
    v_start = voiced[0] * hop
    v_end = voiced[-1] * hop + frame // 2
    hold_at = v_start + hold_from * (v_end - v_start)
    tp = int(SR / target_hz)
    pre = [m for m in marks if m[0] < hold_at]
    post = [m for m in marks if m[0] >= hold_at]
    hold = [m for m in pre if m[1]][-4:] or pre[-1:]  # the vowel cycle to sustain
    tail_len = sum(m[2] for m in post)
    y = np.zeros(out_len + 4 * tp + 4096, np.float32)
    out_t = 0
    seq = list(pre)
    # how long the sustain must last so pre + hold + post fills out_len
    pre_len = int(hold_at)
    need = max(0, out_len - pre_len - tail_len)
    def put(m, at):
        c, is_v, per = m
        w = 2 * (tp if is_v else per)
        a, b = max(0, c - w // 2), min(len(x), c + w // 2)
        g = x[a:b] * np.hanning(b - a).astype(np.float32)
        s = at - (c - a)
        if s < 0:
            g, s = g[-s:], 0
        e = min(len(y), s + len(g))
        if e > s:
            y[s:e] += g[: e - s]
    for m in seq:
        put(m, out_t)
        out_t += tp if m[1] else m[2]
    k = 0
    end_hold = out_t + need
    while out_t < end_hold:
        put(hold[k % len(hold)], out_t)
        out_t += tp
        k += 1
    for m in post:
        put(m, out_t)
        out_t += tp if m[1] else m[2]
    return y[:out_len]


def sung(text: str, midi: int, dur: float, n: int = 10, women: int = 0, seed: int = 0,
         speed: float = 0.9) -> np.ndarray:
    """A chanted syllable or word on one pitch, by n voices; stereo, onset at 0."""
    rng = np.random.default_rng(seed + midi)
    voices = [MEN[(i + seed) % len(MEN)] for i in range(n - women)] + \
             [WOMEN[(i + seed) % len(WOMEN)] for i in range(women)]
    hz = 440 * 2 ** ((midi - 69) / 12)
    out_len = int(dur * SR)
    layers = []
    for v in voices:
        x = tts(text, v, speed=speed)
        x = x / (np.abs(x).max() + 1e-9)
        y = psola(x, hz * 2 ** (rng.normal(0, 0.08) / 12), out_len)
        k = min(len(y), int(0.08 * SR))
        y[-k:] *= np.linspace(1, 0, k)
        layers.append(y)
    out = _spread(layers, rng, 0.025)
    return out / (np.abs(out).max() + 1e-9) * 0.5


# ------------------------------------------------------------------ sound design

def braam(midi: int = 38, dur: float = 3.0, seed: int = 0) -> np.ndarray:
    """A detuned, distorted low brass-synth blast with a filter that closes."""
    rng = np.random.default_rng(seed)
    t = np.arange(int(dur * SR)) / SR
    f = 440 * 2 ** ((midi - 69) / 12)
    x = np.zeros_like(t)
    for k, det in enumerate([-0.12, -0.05, 0.0, 0.06, 0.13]):
        ph = rng.uniform(0, 1)
        for oct_mul, g in [(1, 1.0), (0.5, 0.7), (2, 0.25)]:
            x += g * signal.sawtooth(2 * np.pi * f * oct_mul * 2 ** (det / 12) * t + ph)
    x = np.tanh(x * 0.6)
    env = np.minimum(1, t / 0.04) * np.exp(-t / (dur * 0.45))
    cut = 200 + 2400 * np.exp(-t / 0.5)
    y = np.zeros_like(x)
    # time-varying low-pass in short blocks
    blk = 1024
    zi = None
    for s in range(0, len(x), blk):
        b, a = signal.butter(2, min(0.99, cut[s] / (SR / 2)), "low")
        seg, zi = signal.lfilter(b, a, x[s:s + blk], zi=zi if zi is not None else signal.lfilter_zi(b, a) * 0)
        y[s:s + blk] = seg
    y = (y * env).astype(np.float32)
    st = np.stack([y, np.roll(y, 37)], axis=1)
    return st / (np.abs(st).max() + 1e-9) * 0.5


def sub_drop(dur: float = 2.0, f0: float = 70, f1: float = 28) -> np.ndarray:
    t = np.arange(int(dur * SR)) / SR
    f = f1 + (f0 - f1) * np.exp(-t / (dur * 0.35))
    ph = 2 * np.pi * np.cumsum(f) / SR
    y = np.sin(ph) * np.minimum(1, t / 0.01) * np.exp(-t / (dur * 0.5))
    y = np.tanh(y * 1.5).astype(np.float32)
    return np.stack([y, y], axis=1) * 0.5


def riser(dur: float = 3.0, seed: int = 0) -> np.ndarray:
    """Noise swell with a rising band-pass and a rising tone; ends at its loudest."""
    rng = np.random.default_rng(seed)
    n = int(dur * SR)
    t = np.arange(n) / SR
    noise = rng.standard_normal((n, 2)).astype(np.float32)
    out = np.zeros_like(noise)
    blk = 2048
    for s in range(0, n, blk):
        frac = s / n
        fc = 300 * (30 ** frac)
        b, a = signal.butter(2, [fc / (SR / 2) * 0.7, min(0.99, fc / (SR / 2) * 1.4)], "band")
        out[s:s + blk] = signal.lfilter(b, a, noise[s:s + blk], axis=0)
    tone = np.sin(2 * np.pi * np.cumsum(110 * (8 ** (t / dur))) / SR)[:, None]
    env = (t / dur) ** 2.2
    y = (out * 1.0 + tone * 0.25) * env[:, None]
    return (y / (np.abs(y).max() + 1e-9) * 0.5).astype(np.float32)


def impact(seed: int = 0) -> np.ndarray:
    """Low boom plus a noise crack, for trailer hits (stacked under orchestral percussion)."""
    rng = np.random.default_rng(seed)
    n = int(2.5 * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(45 + 80 * np.exp(-t / 0.05)) / SR) * np.exp(-t / 0.7)
    crack = rng.standard_normal(n) * np.exp(-t / 0.04)
    b, a = signal.butter(2, 1500 / (SR / 2), "high")
    crack = signal.lfilter(b, a, crack)
    y = np.tanh(boom * 1.8) + crack * 0.35
    st = np.stack([y, y], axis=1).astype(np.float32)
    return st / (np.abs(st).max() + 1e-9) * 0.5
