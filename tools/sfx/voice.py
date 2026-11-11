"""Creature voice synthesis for the bosses: roars, growls, death cries and made-up speech.

A glottal source (additive harmonics with jitter, shimmer and a sub-octave growl) goes through three
swept formant resonators that glide from vowel to vowel, with noise consonants between syllables.
Each boss gets a Character with its own pitch, vocal-tract size, roughness and effects, so their
"speech" sounds like a language of its own without any real words. Subtitles carry the meaning.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dsp import (SR, bubbles, crackle, decay, drive, env, fade, hp, lp, mix, n_of, noise, osc, place,
                 resonate, reverb, ring, svf, sweep, times, trem)

# Formant centres (F1, F2, F3) for an adult voice. A bigger creature scales them down.
VOWELS = {
    "a": (730, 1090, 2440),
    "o": (570, 840, 2410),
    "u": (300, 870, 2240),
    "e": (530, 1840, 2480),
    "i": (390, 1990, 2550),
    "ae": (660, 1720, 2410),
    "uh": (520, 1190, 2390),
    "aw": (640, 920, 2400),
}
DARK_VOWELS = ["a", "o", "u", "uh", "aw"]
CONSONANTS = ["k", "g", "r", "sh", "s", "th", "h", "z", "kh", "v"]


@dataclass
class Character:
    """How one boss sounds when it speaks or roars."""
    f0: float = 90.0               # speaking pitch in Hz
    tract: float = 0.75            # formant scale: below 1 is a bigger throat
    growl: float = 0.5             # sub-octave roughness 0..1
    breath: float = 0.2            # aspiration noise 0..1
    rate: float = 4.2              # syllables per second
    vowels: list[str] = field(default_factory=lambda: DARK_VOWELS)
    consonants: list[str] = field(default_factory=lambda: CONSONANTS)
    voices: int = 1                # stacked voices (choir or many-throated)
    detune: float = 0.0            # cents between stacked voices
    octave_down: float = 0.35      # level of a voice an octave below
    drive: float = 2.0
    reverb: float = 1.6
    reverb_mix: float = 0.3
    effect: str = ""               # water, fire, stone, wind, wood, void, ember, cosmos
    pitch_range: float = 0.35      # how much the pitch moves in a phrase (fraction)
    sing: bool = False             # held, sung vowels with vibrato instead of speech


def _glottal(f0_track: np.ndarray, seconds: float, rng: np.random.Generator, growl: float,
             bright: float = 1.0) -> np.ndarray:
    """Harmonic-rich voice source with jitter, shimmer and a sub-harmonic growl."""
    n = n_of(seconds)
    jitter = 1.0 + 0.012 * lp(rng.standard_normal(n), 30) * 8
    f = f0_track[:n] * jitter
    ph = np.cumsum(f) / SR
    out = np.zeros(n)
    k_max = int(min(70, (SR * 0.42) / max(30.0, float(np.min(f)))))
    tilt = 1.15 / bright
    for k in range(1, k_max + 1):
        a = 1.0 / k ** tilt
        part = np.sin(2 * np.pi * k * ph + rng.random() * 0.3)
        part[k * f > SR * 0.42] = 0.0
        out += a * part
    shimmer = 1.0 + 0.15 * lp(rng.standard_normal(n), 40) * 6
    out *= shimmer
    if growl > 0:
        # Period doubling: every other cycle louder, which is what makes a voice sound rough.
        sub = 0.5 + 0.5 * np.sign(np.sin(np.pi * ph))
        rough = lp(rng.standard_normal(n), 90) * 6
        out *= 1.0 - growl * 0.6 + growl * 0.6 * sub + growl * 0.25 * rough
    return out / (np.max(np.abs(out)) + 1e-9)


def _formant_tracks(sequence: list[tuple[float, str]], seconds: float, tract: float) -> list[np.ndarray]:
    """Glides between vowel targets placed at times. Returns F1..F3 tracks."""
    t = times(seconds)
    xs = [s[0] for s in sequence]
    tracks = []
    for i in range(3):
        ys = [VOWELS[s[1]][i] * tract for s in sequence]
        tracks.append(np.interp(t, xs, ys))
    return tracks


def _filter_voice(src: np.ndarray, tracks: list[np.ndarray], tract: float) -> np.ndarray:
    bands = [(tracks[0], 6.0, 1.0), (tracks[1], 9.0, 0.55), (tracks[2], 12.0, 0.28)]
    out = np.zeros(len(src))
    for track, q, gain in bands:
        out += resonate(src, track, q) * gain
    # A little of the raw source keeps the chest in it.
    out += lp(src, 260 * tract) * 0.25
    return out


def _consonant(kind: str, rng: np.random.Generator, tract: float) -> np.ndarray:
    d = {"s": 0.09, "sh": 0.1, "z": 0.08, "th": 0.07, "h": 0.07, "v": 0.06}.get(kind, 0.05)
    nz = noise(d, rng)
    if kind in ("s", "z"):
        x = hp(nz, 4200 * tract ** 0.5) * 0.9
    elif kind == "sh":
        x = resonate(nz, 2400 * tract ** 0.5, 2.5) * 1.6
    elif kind in ("th", "v"):
        x = lp(hp(nz, 1200), 6000) * 0.5
    elif kind in ("h", "kh"):
        x = resonate(nz, 1300 * tract, 1.5) * 1.4
    elif kind == "r":
        x = trem(lp(nz, 900), 28, 0.9) * 0.9
    else:  # k, g: a plosive burst
        x = resonate(nz, 1800 * tract, 3) * 2.0 * decay(d, 0.012, 0.0)
    return fade(x * env([(0, 0), (d * 0.3, 1), (d, 0)], d), 0.002, 0.01)


def _effect_layer(effect: str, seconds: float, rng: np.random.Generator, amp_env: np.ndarray) -> np.ndarray:
    n = len(amp_env)
    if effect == "water":
        return bubbles(seconds, rng, 45, (180, 900))[:n] * amp_env * 0.5
    if effect in ("fire", "ember"):
        hiss = hp(noise(seconds, rng), 3000)[:n] * 0.12
        return (crackle(seconds, rng, 90, 2500)[:n] * 0.6 + hiss) * (0.3 + amp_env)
    if effect == "stone":
        grind = lp(noise(seconds, rng, "brown"), 300)[:n] * 2.0
        return trem(grind, 13, 0.8) * amp_env * 0.5
    if effect == "wind":
        w = resonate(noise(seconds, rng, "pink"), sweep(500, 1500, seconds), 2)[:n] * 2
        return w * (0.3 + amp_env) * 0.4
    if effect == "wood":
        creak = resonate(trem(noise(seconds, rng), 35, 0.95), 700, 6)[:n] * 2.5
        return creak * amp_env * 0.6
    return np.zeros(n)


def phrase(ch: Character, seconds: float, rng: np.random.Generator, intensity: float = 1.0,
           question: bool = False) -> np.ndarray:
    """Made-up speech: a run of syllables with a natural pitch arc. Mono."""
    syll = max(2, int(seconds * ch.rate))
    # Words: groups of 1 to 3 syllables with short gaps.
    starts = []
    t = 0.05
    while len(starts) < syll and t < seconds - 0.2:
        word = int(rng.integers(1, 4))
        for _ in range(word):
            d = rng.uniform(0.7, 1.3) / ch.rate
            starts.append((t, d))
            t += d
        t += rng.uniform(0.05, 0.16)
    total = max(seconds, t + 0.3)
    n = n_of(total)
    tt = times(total)

    # Pitch: declination over the phrase, accents on word starts, a rise at the end for a question.
    base = ch.f0 * (1.0 + ch.pitch_range * 0.3 * np.cos(np.pi * tt / total) - ch.pitch_range * 0.25 * tt / total)
    accents = np.zeros(n)
    for (s, d) in starts:
        accents = place(accents, np.hanning(n_of(d)) * rng.uniform(0.0, ch.pitch_range), s)[:n]
    f0 = base * (1.0 + accents[:n])
    if question:
        f0 *= 1.0 + 0.3 * np.clip((tt - total * 0.75) / (total * 0.25), 0, 1)
    if ch.sing:
        f0 *= 1.0 + 0.02 * np.sin(2 * np.pi * 5.2 * tt)

    seq = []
    amp = np.zeros(n)
    cons = np.zeros(n)
    for (s, d) in starts:
        v = ch.vowels[int(rng.integers(len(ch.vowels)))]
        seq.append((s + d * 0.15, v))
        seq.append((s + d * 0.8, v))
        shape = env([(0, 0), (d * 0.12, 1), (d * 0.7, 0.85), (d, 0)], d, 1.0) * rng.uniform(0.7, 1.0)
        amp = place(amp, shape, s)[:n]
        if rng.random() < 0.75:
            c = _consonant(ch.consonants[int(rng.integers(len(ch.consonants)))], rng, ch.tract)
            cons = place(cons, c, max(0.0, s - 0.03))[:n]
    seq.sort()
    seq = [(0.0, seq[0][1])] + seq + [(total, seq[-1][1])]
    tracks = _formant_tracks(seq, total, ch.tract)

    voice = np.zeros(n)
    for v in range(ch.voices):
        cents = (v - (ch.voices - 1) / 2) * ch.detune
        f = f0 * 2 ** (cents / 1200)
        src = _glottal(f, total, rng, ch.growl, 1.0 + 0.3 * intensity)
        voice += _filter_voice(src, tracks, ch.tract)
    if ch.octave_down > 0:
        src = _glottal(f0 * 0.5, total, rng, min(1.0, ch.growl + 0.2))
        voice += _filter_voice(src, [x * 0.8 for x in tracks], ch.tract) * ch.octave_down
    voice /= np.max(np.abs(voice)) + 1e-9
    breath = resonate(noise(total, rng, "pink"), tracks[1], 3)[:n] * ch.breath * 2
    out = (voice + breath) * amp + cons * 0.5 * intensity
    out += _effect_layer(ch.effect, total, rng, amp) * 0.6
    out = drive(out * (1 + intensity), ch.drive)
    out = _post(out, ch, rng)
    return out


def _post(x: np.ndarray, ch: Character, rng: np.random.Generator) -> np.ndarray:
    if ch.effect == "void":
        x = x * 0.6 + ring(x, 37.0) * 0.4
    if ch.effect == "cosmos":
        x = x * 0.5 + ring(x, 23.0) * 0.3 + ring(x, 61.0) * 0.2
    if ch.effect == "water":
        x = svf(x, 900 + 500 * osc(3.1, len(x) / SR), 1.2, "low") * 1.3
    x = hp(x, 45)
    return reverb(x, ch.reverb, ch.reverb_mix, 4500, rng=rng)


def roar(ch: Character, seconds: float, rng: np.random.Generator, rise: float = 0.25, fall: float = 0.5,
         vowel_path: tuple[str, ...] = ("uh", "a", "aw", "o"), intensity: float = 1.3) -> np.ndarray:
    """A sustained roar: pitch rises, holds, falls; mouth opens then closes."""
    total = seconds
    tt = times(total)
    f0 = ch.f0 * 0.9 * np.interp(tt, [0, total * rise, total * (1 - fall), total],
                                 [0.75, 1.25, 1.1, 0.6])
    f0 *= 1.0 + 0.03 * lp(rng.standard_normal(len(tt)), 8) * 10
    seq = [(total * i / (len(vowel_path) - 1), v) for i, v in enumerate(vowel_path)]
    tracks = _formant_tracks(seq, total, ch.tract)
    voice = np.zeros(len(tt))
    for v in range(max(ch.voices, 2)):
        cents = (v - (max(ch.voices, 2) - 1) / 2) * max(ch.detune, 18)
        src = _glottal(f0 * 2 ** (cents / 1200), total, rng, min(1.0, ch.growl + 0.3), 1.4)
        voice += _filter_voice(src, tracks, ch.tract)
    src = _glottal(f0 * 0.5, total, rng, 1.0)
    voice += _filter_voice(src, [x * 0.8 for x in tracks], ch.tract) * (ch.octave_down + 0.3)
    voice /= np.max(np.abs(voice)) + 1e-9
    a = env([(0, 0), (total * 0.08, 0.8), (total * rise, 1), (total * (1 - fall), 0.85), (total, 0)], total, 1.3)
    noise_layer = resonate(noise(total, rng, "pink"), tracks[0] * 1.5, 1.2) * 1.5 * ch.breath * 2
    out = (voice + noise_layer) * a
    out += _effect_layer(ch.effect, total, rng, a) * 0.8
    out = drive(out * intensity * 1.5, ch.drive + 1)
    return _post(out, ch, rng)


def song(ch: Character, notes: list[tuple[float, float, str]], rng: np.random.Generator) -> np.ndarray:
    """Sung notes (semitones from f0, seconds, vowel) for the Pale Vesper. Mono."""
    total = sum(d for _, d, _ in notes) + 0.2
    n = n_of(total)
    tt = times(total)
    f0 = np.zeros(n)
    seq = []
    amp = np.zeros(n)
    t = 0.0
    for semis, d, v in notes:
        f = ch.f0 * 2 ** (semis / 12)
        seg = np.full(n_of(d), f)
        f0 = place(f0, seg, t)[:n]
        seq += [(t + 0.02, v), (t + d * 0.9, v)]
        amp = place(amp, env([(0, 0), (min(0.12, d * 0.3), 1), (d * 0.8, 0.9), (d, 0.15)], d), t)[:n]
        t += d
    f0[f0 == 0] = ch.f0
    # Glide between notes.
    f0 = lp(f0, 12)
    f0 *= 1.0 + 0.018 * np.sin(2 * np.pi * 5.4 * tt) * np.clip(tt * 2, 0, 1)
    seq = [(0.0, seq[0][1])] + seq + [(total, seq[-1][1])]
    tracks = _formant_tracks(seq, total, ch.tract)
    voice = np.zeros(n)
    for v in range(ch.voices):
        cents = (v - (ch.voices - 1) / 2) * ch.detune
        src = _glottal(f0 * 2 ** (cents / 1200), total, rng, ch.growl, 1.0)
        voice += _filter_voice(src, tracks, ch.tract)
    voice /= np.max(np.abs(voice)) + 1e-9
    breath = resonate(noise(total, rng, "pink"), tracks[1], 2.5) * ch.breath * 1.5
    out = drive((voice + breath) * amp * 1.4, ch.drive)
    return _post(out, ch, rng)
