"""Small sound-synthesis toolkit used by the sound effect recipes.

Everything here is plain numpy/scipy: oscillators, noise, envelopes, filters (static and swept),
modal resonators, crackle, distortion and a synthetic reverb. No samples are used anywhere, so every
sound made with it is original and owned by the project.

Signals are float64 numpy arrays at SR. Mono is 1-D, stereo is shape (n, 2).
"""

from __future__ import annotations

import numpy as np
from scipy import signal

SR = 44100


# --- Time and envelopes ------------------------------------------------------------

def n_of(seconds: float) -> int:
    return max(1, int(round(seconds * SR)))


def times(seconds: float) -> np.ndarray:
    return np.arange(n_of(seconds)) / SR


def silence(seconds: float) -> np.ndarray:
    return np.zeros(n_of(seconds))


def env(points: list[tuple[float, float]], seconds: float | None = None, curve: float = 1.0) -> np.ndarray:
    """Piecewise envelope through (time, value) points. curve > 1 bends segments towards exponential."""
    if seconds is None:
        seconds = points[-1][0]
    t = times(seconds)
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    out = np.interp(t, xs, ys)
    if curve != 1.0:
        lo, hi = min(ys), max(ys)
        if hi > lo:
            out = lo + (hi - lo) * ((out - lo) / (hi - lo)) ** curve
    return out


def decay(seconds: float, tau: float, attack: float = 0.002) -> np.ndarray:
    """Fast attack then exponential decay with time constant tau."""
    t = times(seconds)
    out = np.exp(-t / max(tau, 1e-4))
    if attack > 0:
        out *= np.clip(t / attack, 0.0, 1.0)
    return out


def fade(x: np.ndarray, fade_in: float = 0.002, fade_out: float = 0.01) -> np.ndarray:
    """Short raised-cosine fades so nothing starts or ends with a click."""
    y = x.copy()
    n = len(y)
    a = min(n // 2, n_of(fade_in)) if fade_in > 0 else 0
    b = min(n // 2, n_of(fade_out)) if fade_out > 0 else 0
    if a > 0:
        ramp = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, a))
        y[:a] = (y[:a].T * ramp).T
    if b > 0:
        ramp = 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, b))
        y[-b:] = (y[-b:].T * ramp).T
    return y


# --- Sources -----------------------------------------------------------------------

def _as_track(value, n: int) -> np.ndarray:
    if np.isscalar(value):
        return np.full(n, float(value))
    value = np.asarray(value, dtype=float)
    if len(value) >= n:
        return value[:n]
    return np.concatenate([value, np.full(n - len(value), value[-1])])


def phase_of(freq, seconds: float) -> np.ndarray:
    """Running phase in cycles for a (possibly swept) frequency."""
    n = n_of(seconds)
    f = _as_track(freq, n)
    return np.cumsum(f) / SR


def _poly_blep(p: np.ndarray, dt: np.ndarray) -> np.ndarray:
    out = np.zeros_like(p)
    dt = np.maximum(dt, 1e-9)
    m = p < dt
    x = p[m] / dt[m]
    out[m] = x + x - x * x - 1.0
    m2 = p > 1.0 - dt
    x = (p[m2] - 1.0) / dt[m2]
    out[m2] = x * x + x + x + 1.0
    return out


def osc(freq, seconds: float, shape: str = "sine", phase0: float = 0.0, pw: float = 0.5) -> np.ndarray:
    """Band-limited-ish oscillator: sine, saw, square, tri. freq can be a track (array)."""
    n = n_of(seconds)
    f = _as_track(freq, n)
    ph = (np.cumsum(f) / SR + phase0) % 1.0
    dt = np.abs(f) / SR
    if shape == "sine":
        return np.sin(2 * np.pi * ph)
    if shape == "saw":
        return 2.0 * ph - 1.0 - _poly_blep(ph, dt)
    if shape == "square":
        sq = np.where(ph < pw, 1.0, -1.0)
        sq += _poly_blep(ph, dt)
        sq -= _poly_blep((ph - pw) % 1.0, dt)
        return sq
    if shape == "tri":
        return 2.0 * np.abs(2.0 * ph - 1.0) - 1.0
    raise ValueError(shape)


def harmonics(freq, seconds: float, amps: list[float], phase_jitter: np.random.Generator | None = None) -> np.ndarray:
    """Additive tone: amps[k] is the level of harmonic k+1."""
    ph = phase_of(freq, seconds)
    out = np.zeros(len(ph))
    f = _as_track(freq, len(ph))
    for k, a in enumerate(amps, start=1):
        if a == 0:
            continue
        p0 = phase_jitter.random() if phase_jitter is not None else 0.0
        part = a * np.sin(2 * np.pi * (k * ph + p0))
        part[k * f > SR * 0.45] = 0.0
        out += part
    return out


def noise(seconds: float, rng: np.random.Generator, color: str = "white") -> np.ndarray:
    n = n_of(seconds)
    w = rng.standard_normal(n)
    if color == "white":
        return w / 3.0
    spec = np.fft.rfft(w)
    freqs = np.fft.rfftfreq(n, 1 / SR)
    freqs[0] = freqs[1] if n > 1 else 1.0
    if color == "pink":
        spec /= np.sqrt(freqs)
    elif color == "brown":
        spec /= freqs
    elif color == "blue":
        spec *= np.sqrt(freqs)
    out = np.fft.irfft(spec, n)
    return out / (np.max(np.abs(out)) + 1e-12) * 0.5


def crackle(seconds: float, rng: np.random.Generator, rate: float = 60.0, bright: float = 4000.0,
            sizes: tuple[float, float] = (0.2, 1.0)) -> np.ndarray:
    """Random pops and crackles, like fire or static. rate is pops per second (can be a track)."""
    n = n_of(seconds)
    r = _as_track(rate, n)
    hits = rng.random(n) < (r / SR)
    out = np.zeros(n)
    idx = np.nonzero(hits)[0]
    for i in idx:
        length = int(rng.uniform(0.0006, 0.004) * SR)
        if i + length >= n:
            continue
        burst = rng.standard_normal(length) * np.exp(-np.linspace(0, 6, length))
        out[i:i + length] += burst * rng.uniform(*sizes)
    return hp(out, bright * 0.25) if bright else out


def modal(seconds: float, modes: list[tuple[float, float, float]], rng: np.random.Generator | None = None) -> np.ndarray:
    """Struck resonant body: modes are (frequency, decay seconds, amplitude)."""
    t = times(seconds)
    out = np.zeros(len(t))
    for f, tau, a in modes:
        if f >= SR * 0.45:
            continue
        p = rng.random() * 2 * np.pi if rng is not None else 0.0
        out += a * np.sin(2 * np.pi * f * t + p) * np.exp(-t / tau)
    return out


def chirp(f0: float, f1: float, seconds: float, shape: str = "sine", curve: str = "exp") -> np.ndarray:
    t = times(seconds)
    if curve == "exp":
        f = f0 * (f1 / f0) ** (t / seconds)
    else:
        f = f0 + (f1 - f0) * t / seconds
    return osc(f, seconds, shape)


def sweep(f0: float, f1: float, seconds: float, curve: str = "exp", power: float = 1.0) -> np.ndarray:
    """A frequency track from f0 to f1."""
    t = times(seconds) / seconds
    t = t ** power
    if curve == "exp":
        return f0 * (f1 / f0) ** t
    return f0 + (f1 - f0) * t


# --- Filters -----------------------------------------------------------------------

def _clip_freq(f):
    return np.clip(f, 10.0, SR * 0.49)


def _static(x: np.ndarray, kind: str, freq, order: int = 2) -> np.ndarray:
    if kind == "bandpass":
        lo, hi = freq
        sos = signal.butter(order, [_clip_freq(lo), _clip_freq(hi)], btype="bandpass", fs=SR, output="sos")
    else:
        sos = signal.butter(order, _clip_freq(freq), btype=kind, fs=SR, output="sos")
    return signal.sosfilt(sos, x, axis=0)


def lp(x: np.ndarray, freq, order: int = 2) -> np.ndarray:
    if not np.isscalar(freq):
        return svf(x, freq, 0.707, "low")
    return _static(x, "lowpass", freq, order)


def hp(x: np.ndarray, freq, order: int = 2) -> np.ndarray:
    if not np.isscalar(freq):
        return svf(x, freq, 0.707, "high")
    return _static(x, "highpass", freq, order)


def bp(x: np.ndarray, lo: float, hi: float, order: int = 2) -> np.ndarray:
    return _static(x, "bandpass", (lo, hi), order)


def _biquad(kind: str, f: float, q: float, gain_db: float = 0.0):
    w0 = 2 * np.pi * f / SR
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2 * q)
    a_lin = 10 ** (gain_db / 40)
    if kind == "low":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "high":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "band":
        b = [alpha, 0.0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        b = [1 + alpha * a_lin, -2 * cw, 1 - alpha * a_lin]
        a = [1 + alpha / a_lin, -2 * cw, 1 - alpha / a_lin]
    else:
        raise ValueError(kind)
    b = np.array(b) / a[0]
    a = np.array(a) / a[0]
    return b, a


def svf(x: np.ndarray, freq, q=0.707, kind: str = "low", block: int = 64) -> np.ndarray:
    """Biquad whose cutoff (and q) follow tracks, updated every block samples."""
    n = len(x)
    f = _clip_freq(_as_track(freq, n))
    qs = _as_track(q, n)
    out = np.zeros(n)
    zi = np.zeros(2)
    for start in range(0, n, block):
        end = min(n, start + block)
        b, a = _biquad(kind, f[start], max(qs[start], 0.1))
        out[start:end], zi = signal.lfilter(b, a, x[start:end], zi=zi)
    return out


def peak_eq(x: np.ndarray, freq: float, gain_db: float, q: float = 1.0) -> np.ndarray:
    b, a = _biquad("peak", freq, q, gain_db)
    return signal.lfilter(b, a, x, axis=0)


def resonate(x: np.ndarray, freq, q: float = 8.0) -> np.ndarray:
    """Band-pass resonance (constant peak gain), cutoff can be a track."""
    if np.isscalar(freq):
        b, a = _biquad("band", freq, q)
        return signal.lfilter(b, a, x)
    return svf(x, freq, q, "band")


def comb(x: np.ndarray, delay_s: float, feedback: float, seconds_tail: float = 0.0) -> np.ndarray:
    d = max(1, int(delay_s * SR))
    y = np.concatenate([x, np.zeros(n_of(seconds_tail))]) if seconds_tail else x.copy()
    b = np.zeros(d + 1)
    b[0] = 1.0
    a = np.zeros(d + 1)
    a[0] = 1.0
    a[d] = -feedback
    return signal.lfilter(b, a, y)


# --- Shaping -----------------------------------------------------------------------

def drive(x: np.ndarray, amount: float = 2.0) -> np.ndarray:
    """Soft saturation, level kept roughly the same."""
    return np.tanh(x * amount) / np.tanh(amount)


def fold(x: np.ndarray, amount: float = 2.0) -> np.ndarray:
    return np.sin(x * amount * np.pi / 2)


def crush(x: np.ndarray, bits: int = 6, keep: int = 1) -> np.ndarray:
    steps = 2 ** bits
    y = np.round(x * steps) / steps
    if keep > 1:
        y = np.repeat(y[::keep], keep)[:len(x)]
    return y


def ring(x: np.ndarray, freq) -> np.ndarray:
    return x * osc(freq, len(x) / SR)


def gain_db(x: np.ndarray, db: float) -> np.ndarray:
    return x * 10 ** (db / 20)


def trem(x: np.ndarray, rate, depth: float = 0.5, shape: str = "sine") -> np.ndarray:
    lfo = 0.5 + 0.5 * osc(rate, len(x) / SR, shape)
    return x * (1 - depth + depth * lfo)


# --- Mixing ------------------------------------------------------------------------

def pad_to(x: np.ndarray, n: int) -> np.ndarray:
    if len(x) >= n:
        return x
    shape = (n - len(x),) + x.shape[1:]
    return np.concatenate([x, np.zeros(shape)])


def mix(*parts: np.ndarray) -> np.ndarray:
    parts = [p for p in parts if p is not None]
    n = max(len(p) for p in parts)
    stereo = any(p.ndim == 2 for p in parts)
    out = np.zeros((n, 2)) if stereo else np.zeros(n)
    for p in parts:
        if stereo and p.ndim == 1:
            p = np.stack([p, p], axis=1)
        out[:len(p)] += p
    return out


def place(base: np.ndarray, part: np.ndarray, at: float, level: float = 1.0) -> np.ndarray:
    """Adds part into base starting at `at` seconds, growing base if needed."""
    start = n_of(at) if at > 0 else 0
    end = start + len(part)
    if base.ndim == 2 and part.ndim == 1:
        part = np.stack([part, part], axis=1)
    if part.ndim == 2 and base.ndim == 1:
        base = np.stack([base, base], axis=1)
    base = pad_to(base, end)
    base[start:end] += part * level
    return base


def stereo(x: np.ndarray, width: float = 0.0, pan: float = 0.0, rng: np.random.Generator | None = None) -> np.ndarray:
    """Mono to stereo with a small decorrelation (width 0..1) and pan (-1..1)."""
    if x.ndim == 2:
        return x
    left = x.copy()
    right = x.copy()
    if width > 0:
        d = int(0.011 * SR * width)
        right = np.concatenate([np.zeros(d), x])[:len(x)]
        mid = (left + right) / 2
        side = (left - right) / 2 * width
        left, right = mid + side, mid - side
    l_gain = np.sqrt(0.5 * (1 - pan))
    r_gain = np.sqrt(0.5 * (1 + pan))
    return np.stack([left * l_gain * 1.414, right * r_gain * 1.414], axis=1)


def reverb(x: np.ndarray, seconds: float = 1.2, mix_level: float = 0.25, damp: float = 5000.0,
           predelay: float = 0.012, rng: np.random.Generator | None = None, wide: bool = False) -> np.ndarray:
    """Synthetic hall: exponentially decaying noise with high frequencies dying faster."""
    rng = rng or np.random.default_rng(7)
    tail = seconds
    t = times(tail)
    chans = 2 if wide or x.ndim == 2 else 1
    irs = []
    for _ in range(chans):
        nz = rng.standard_normal(len(t))
        lowpart = lp(nz, damp * 0.25) * np.exp(-6.9 * t / seconds)
        highpart = hp(nz, damp * 0.25) * np.exp(-6.9 * t / (seconds * 0.45))
        ir = lp(lowpart + highpart * 0.6, damp)
        ir = np.concatenate([np.zeros(n_of(predelay)), ir])
        ir[: n_of(0.004)] *= np.linspace(0, 1, n_of(0.004))
        ir /= np.sqrt(np.sum(ir ** 2)) + 1e-12
        irs.append(ir)
    dry = x if x.ndim == 1 else x
    if chans == 2:
        src = dry if dry.ndim == 2 else np.stack([dry, dry], axis=1)
        wet = np.stack([signal.fftconvolve(src[:, i], irs[i]) for i in range(2)], axis=1)
        out = mix(src * (1 - mix_level * 0.5), wet * mix_level)
    else:
        wet = signal.fftconvolve(dry, irs[0])
        out = mix(dry * (1 - mix_level * 0.5), wet * mix_level)
    return out


def trim(x: np.ndarray, threshold_db: float = -70.0, tail: float = 0.03) -> np.ndarray:
    """Cuts trailing silence and fades the end."""
    mono = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
    peak = mono.max() + 1e-12
    above = np.nonzero(mono > peak * 10 ** (threshold_db / 20))[0]
    if len(above) == 0:
        return x
    end = min(len(x), above[-1] + n_of(tail))
    return fade(x[:end], 0.0, min(0.05, tail * 2))


def dc_block(x: np.ndarray) -> np.ndarray:
    return hp(x, 18.0, 1)


# --- Common building blocks ----------------------------------------------------------

def thump(seconds: float, f0: float = 110.0, f1: float = 40.0, tau: float = 0.12, click: float = 0.3,
          rng: np.random.Generator | None = None) -> np.ndarray:
    """Kick-drum style low hit: falling sine with a click."""
    f = sweep(f0, f1, seconds, power=0.35)
    body = osc(f, seconds) * decay(seconds, tau, 0.001)
    if click > 0 and rng is not None:
        c = hp(noise(0.012, rng), 1500) * decay(0.012, 0.003, 0.0)
        body = place(body, c * click, 0.0)
    return body


def whoosh(seconds: float, rng: np.random.Generator, f0: float = 400.0, f1: float = 2500.0, q: float = 1.5,
           shape: list[tuple[float, float]] | None = None) -> np.ndarray:
    """Air moving past: swept band-passed noise."""
    nz = noise(seconds, rng, "pink")
    cut = sweep(f0, f1, seconds)
    out = resonate(nz, cut, q) * 3.0
    e = env(shape or [(0, 0), (seconds * 0.6, 1), (seconds, 0)], seconds, 1.5)
    return out * e


def rumble(seconds: float, rng: np.random.Generator, cutoff: float = 120.0, wobble: float = 3.0) -> np.ndarray:
    nz = noise(seconds, rng, "brown")
    out = lp(nz, cutoff, 4) * 4.0
    return trem(out, wobble, 0.4)


def debris(seconds: float, rng: np.random.Generator, count: int = 20, pitch: float = 1.0, bright: float = 3000.0) -> np.ndarray:
    """Small stones or splinters falling and bouncing."""
    out = silence(seconds)
    for _ in range(count):
        at = rng.uniform(0, seconds * 0.8) ** 1.3 / (seconds * 0.8) ** 0.3
        f = rng.uniform(900, 3200) * pitch
        piece = modal(0.08, [(f, 0.012, 1.0), (f * 1.73, 0.008, 0.5), (f * 2.41, 0.005, 0.3)], rng)
        piece += hp(noise(0.08, rng), bright) * decay(0.08, 0.006)
        out = place(out, piece * rng.uniform(0.15, 0.6), at)
    return out[: n_of(seconds)]


def bubbles(seconds: float, rng: np.random.Generator, rate: float = 25.0, f_range=(300.0, 1400.0)) -> np.ndarray:
    """Bubbles: short sine blips whose pitch rises as they pop."""
    out = silence(seconds)
    count = int(rate * seconds)
    for _ in range(count):
        at = rng.uniform(0, seconds)
        f = rng.uniform(*f_range)
        d = rng.uniform(0.02, 0.07)
        blip = osc(sweep(f, f * rng.uniform(1.4, 2.4), d), d) * decay(d, d * 0.35, 0.002)
        out = place(out, blip * rng.uniform(0.2, 0.7), at)
    return out[: n_of(seconds)]


def boom(seconds: float, rng: np.random.Generator, size: float = 1.0) -> np.ndarray:
    """Explosion: sub thump, noise body, crackle tail. size 0.5 (small) to 2 (huge)."""
    low = thump(seconds, 90 / size ** 0.3, 32, 0.15 * size, 0.0) * 0.9
    body_cut = sweep(6000 / size ** 0.5, 300, seconds, power=0.4)
    body = lp(noise(seconds, rng, "pink"), body_cut) * decay(seconds, 0.12 * size ** 1.2, 0.001) * 1.6
    tail = lp(noise(seconds, rng, "brown"), 400) * decay(seconds, 0.35 * size, 0.02) * 1.2
    crk = crackle(seconds, rng, sweep(220, 10, seconds), 3000) * decay(seconds, 0.25 * size, 0.01) * 0.5
    return drive(low + body + tail + crk, 1.6)
