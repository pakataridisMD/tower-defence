"""Boss voices and roars made from recorded speech.

A spoken line (Kokoro, see samples.speak) goes through the chain film sound designers use for demons
and giants: pitch and formants shifted down for size, an octave-down double, a breathy whisper double
made from the same words, parallel distortion for grit, a fast amplitude rasp for a growl, unison
copies for a choir of mouths, and a big room. Roars are a shouted vowel pushed much further and
layered with real recordings: a bass drum skin rubbed by hand (the throat rumble), a trombone blat
(the bark), and a sub that follows the voice.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy import signal

from dsp import SR, drive, env, hp, lp, mix, n_of, noise, osc, peak_eq, place, reverb, silence, stereo, times
import kit
import samples as S


@dataclass
class Voice:
    speaker: str = "am_onyx"     # Kokoro voice, or a blend "am_onyx:0.6,bm_george:0.4"
    rate: float = 0.85
    lang: str = "en-us"
    depth: float = -4.0          # semitones; pitch and formants together (bigger body)
    formant: bool = False        # True keeps the formants, so only the pitch moves
    sub: float = 0.35            # octave-down double
    up: float = 0.0              # octave-up ghost double
    whisper: float = 0.0         # breathy double of the same words
    grit: float = 0.25           # parallel distortion
    growl: float = 0.0           # throat rasp (fast amplitude modulation)
    chorus: int = 1              # mouths in unison
    room: float = 2.4
    wet: float = 0.28
    roar_depth: float = -10.0    # extra shift for roars
    roar_word: str = "Raaaaaaagh!"
    beast: bool = False          # no words at all: lines are roars
    lines: dict = field(default_factory=dict)


def follow(x: np.ndarray, cutoff: float = 25.0) -> np.ndarray:
    """Amplitude envelope of a sound."""
    m = np.abs(S.mono(x))
    e = lp(lp(m, cutoff), cutoff)
    return np.maximum(e, 0) / (np.max(e) + 1e-12)


def glide(x: np.ndarray, st0: float, st1: float, power: float = 1.0) -> np.ndarray:
    """Tape-style pitch bend from st0 to st1 semitones across the sound (the length changes too)."""
    n = len(x)
    t = np.linspace(0, 1, n) ** power
    rate = 2 ** ((st0 + (st1 - st0) * t) / 12)
    pos = np.concatenate([[0.0], np.cumsum(rate)[:-1]])
    pos = pos[pos < n - 1]
    idx = np.arange(n)
    if x.ndim == 1:
        return np.interp(pos, idx, x)
    return np.stack([np.interp(pos, idx, x[:, c]) for c in range(x.shape[1])], axis=1)


def whisper_of(x: np.ndarray, rng) -> np.ndarray:
    """The same words with the voicing replaced by breath: keep the spectrum, scramble the phase."""
    f, t, Z = signal.stft(x, SR, nperseg=1024, noverlap=768)
    phase = np.exp(1j * rng.uniform(0, 2 * np.pi, Z.shape))
    _, y = signal.istft(np.abs(Z) * phase, SR, nperseg=1024, noverlap=768)
    y = hp(y[: len(x)], 900)
    return y / (np.max(np.abs(y)) + 1e-12)


def rasp(x: np.ndarray, rng, amount: float, rate: float = 42.0) -> np.ndarray:
    """Vocal fry: amplitude chopped at a jittery 30-60 Hz, like air rattling through a huge throat."""
    if amount <= 0:
        return x
    n = len(x)
    wobble = np.cumsum(rng.normal(0, 1, n)) / SR * 30
    f = rate * (1 + 0.25 * np.sin(2 * np.pi * 0.7 * times(n / SR)) + 0.1 * wobble / (np.abs(wobble).max() + 1e-9))
    ph = np.cumsum(f) / SR
    m = 0.5 + 0.5 * np.sin(2 * np.pi * ph)
    m = m ** 2
    g = (1 - amount) + amount * m
    return (x.T * g).T if x.ndim == 2 else x * g


def _shape(x: np.ndarray, v: Voice, rng, depth: float, sub_level: float | None = None,
           grit: float | None = None, growl: float | None = None) -> np.ndarray:
    grit = v.grit if grit is None else grit
    growl = v.growl if growl is None else growl
    sub_level = v.sub if sub_level is None else sub_level
    main = S.stretch(x, depth, formant=v.formant)
    parts = [main]
    if sub_level:
        low = S.stretch(x, depth - 12, formant=False)
        parts.append(lp(low, 900) * sub_level)
    if v.up:
        hi = S.stretch(x, depth + 12, formant=True)
        parts.append(place(silence(0.05), hp(hi, 600), 0.035) * v.up)
    for i in range(1, v.chorus):
        d = S.stretch(x, depth + rng.uniform(-0.25, 0.25), formant=v.formant)
        parts.append(place(silence(0.05), d, rng.uniform(0.012, 0.045)) * (0.7 / i ** 0.3))
    if v.whisper:
        w = whisper_of(S.stretch(x, depth * 0.5, formant=True), rng)
        parts.append(place(silence(0.05), w, 0.02) * v.whisper)
    body = mix(*parts)
    if grit:
        dirty = drive(hp(body, 120) * (2 + 6 * grit), 2.5)
        body = mix(body, lp(dirty, 5000) * grit * 0.6)
    body = rasp(body, rng, growl)
    f = min(len(body) // 4, int(0.01 * SR))
    body[:f] = (body[:f].T * np.linspace(0, 1, f)).T
    body = peak_eq(body, 140, 3.0, 0.8)
    body = peak_eq(body, 3000, 2.0, 1.0)
    return body / (np.max(np.abs(body)) + 1e-12)


def speech(text: str, v: Voice, rng, shout: bool = False, extra_depth: float = 0.0) -> np.ndarray:
    """A boss saying a line, processed, mono (the caller adds the room)."""
    x = S.speak(text, v.speaker, v.rate * (1.05 if shout else 1.0), v.lang)
    return _shape(x, v, rng, v.depth + extra_depth, grit=v.grit * (1.8 if shout else 1.0) + (0.15 if shout else 0),
                  growl=min(0.9, v.growl * (1.4 if shout else 1.0)))


def roar(v: Voice, rng, word: str | None = None, length: float = 1.0, fall: float = -3.0,
         intensity: float = 1.0) -> np.ndarray:
    """A creature roar: a shouted vowel taken far down, with throat, bark and sub layers."""
    x = S.speak(word or v.roar_word, v.speaker, float(np.clip(0.75 / max(0.3, length), 0.5, 1.5)), v.lang)
    if length > 1.4:
        x = S.stretch(x, 0.0, tempo=1.4 / length)
    depth = v.depth + v.roar_depth
    core = _shape(x, v, rng, depth, sub_level=0.5, grit=min(1.0, 0.45 + 0.35 * intensity),
                  growl=min(0.95, 0.45 + 0.3 * intensity))
    core = glide(core, 0.0, fall, 1.6)
    e = follow(core, 18)
    n = len(core)
    seconds = n / SR
    throat = kit.drum_rub(rng, -10 - 4 * intensity)
    throat = S.mono(throat)[:n]
    throat = np.concatenate([throat, np.zeros(n - len(throat))]) * e
    bark = S.mono(kit.held("buzz", 34 + rng.uniform(-3, 3) + depth * 0.3, seconds, rng, 0.03, 0.2))[:n]
    bark = glide(np.concatenate([bark, np.zeros(max(0, n - len(bark)))]), 0, fall, 1.3)[:n]
    bark = np.concatenate([bark, np.zeros(n - len(bark))]) * e
    low = osc(45 * 2 ** (np.linspace(0, fall, n) / 12), seconds) * e * 0.5
    breath = hp(noise(seconds, rng, "pink"), 1500) * e ** 1.5 * 0.25
    return mix(core * 1.0, hp(throat, 60) * 0.7 * intensity, drive(bark * 2, 2) * 0.35, low, breath)


def room(x: np.ndarray, v: Voice, rng, scale: float = 1.0) -> np.ndarray:
    return reverb(stereo(x, 0.5, rng=rng), v.room * scale, v.wet, damp=5500, predelay=0.03, rng=rng, wide=True)
