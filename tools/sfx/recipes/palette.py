"""Shared instruments and the six element palettes (attack, impact, aura) used by the recipes."""

from __future__ import annotations

import numpy as np
from scipy import signal

from dsp import (SR, boom, bubbles, chirp, crackle, debris, decay, drive, env, fade, harmonics, hp, lp, mix,
                 modal, n_of, noise, osc, place, resonate, reverb, ring, silence, stereo, svf, sweep, thump,
                 times, trem, whoosh, rumble, bp, peak_eq)

ELEMENTS = ["fire", "storm", "nature", "water", "earth", "void"]


def semis(f: float, s: float) -> float:
    return f * 2 ** (s / 12)


def pitch(x: np.ndarray, ratio: float) -> np.ndarray:
    """Plays a sound faster (ratio > 1, higher) or slower (lower), like changing tape speed."""
    if abs(ratio - 1.0) < 1e-3:
        return x
    up = int(round(1000 / ratio))
    return signal.resample_poly(x, up, 1000, axis=0)


def reverse(x: np.ndarray) -> np.ndarray:
    return x[::-1].copy()


def pluck(freq: float, seconds: float, rng: np.random.Generator, damping: float = 0.996, bright: float = 0.5) -> np.ndarray:
    """Karplus-Strong string: a bowstring or vine twang."""
    period = max(2, int(SR / freq))
    n = n_of(seconds)
    out = np.zeros(n + period + 1)
    burst = rng.uniform(-1, 1, period)
    burst = lp(burst, 1500 + bright * 8000)
    out[:period] = burst
    for start in range(period, n + period, period):
        end = min(start + period, n + period)
        prev = out[start - period:end - period]
        prev2 = out[start - period - 1:end - period - 1] if start - period - 1 >= 0 else np.concatenate([[0.0], prev[:-1]])
        if len(prev2) < len(prev):
            prev2 = np.concatenate([[0.0], prev[:-1]])
        out[start:end] = damping * 0.5 * (prev + prev2[:len(prev)])
    return out[:n]


# --- Instruments ----------------------------------------------------------------------

def brass(freq: float, seconds: float, rng: np.random.Generator, bright: float = 1.0, vib: float = 0.012,
          attack: float = 0.06) -> np.ndarray:
    """Synth brass: detuned saws, a filter that opens with the breath, a small pitch scoop."""
    t = times(seconds)
    scoop = 1.0 - 0.05 * np.exp(-t / 0.04)
    vibrato = 1.0 + vib * np.sin(2 * np.pi * 5.3 * t) * np.clip((t - 0.25) / 0.3, 0, 1)
    f = freq * scoop * vibrato
    tone = sum(osc(f * 2 ** (c / 1200), seconds, "saw", rng.random()) for c in (-7, 0, 6)) / 3
    cut = (500 + 2600 * bright) * env([(0, 0.25), (attack * 1.5, 1.0), (seconds * 0.6, 0.75), (seconds, 0.6)], seconds)
    out = svf(tone, cut + freq, 0.9, "low")
    out = peak_eq(out, 1200, 4, 1.2)
    breath = resonate(noise(seconds, rng, "pink"), freq * 3, 4) * 0.08
    a = env([(0, 0), (attack, 1), (seconds - 0.12, 0.85), (seconds, 0)], seconds)
    return drive((out + breath) * a * 1.4, 1.5)


def horn_call(notes: list[tuple[float, float, float]], rng: np.random.Generator, layers=(1.0, 0.5),
              bright: float = 0.8) -> np.ndarray:
    """notes: (frequency, start, length). layers: levels for the note and its lower octave."""
    total = max(s + d for _, s, d in notes) + 0.2
    out = silence(total)
    for f, s, d in notes:
        part = brass(f, d, rng, bright) * layers[0]
        if len(layers) > 1 and layers[1] > 0:
            part = mix(part, brass(f / 2, d, rng, bright * 0.7) * layers[1])
        out = place(out, part, s)
    return out


def bell(freq: float, seconds: float, rng: np.random.Generator, tone: float = 1.0) -> np.ndarray:
    """Church bell: hum, prime, minor third, fifth and nominal partials."""
    ratios = [0.5, 1.0, 1.19, 1.5, 2.0, 2.52, 2.67, 3.01, 4.17]
    amps = [0.5, 1.0, 0.6, 0.35, 0.55, 0.25, 0.2, 0.15, 0.1]
    decays = [seconds * 0.9, seconds * 0.6, seconds * 0.5, seconds * 0.35, seconds * 0.3, 0.6, 0.5, 0.35, 0.25]
    modes = [(freq * r * (1 + rng.uniform(-0.002, 0.002)), d * tone, a) for r, a, d in zip(ratios, amps, decays)]
    strike = hp(noise(0.02, rng), 2000) * decay(0.02, 0.004)
    return place(modal(seconds, modes, rng), strike * 0.4, 0.0)


def chime(freq: float, seconds: float, rng: np.random.Generator, shimmer: float = 0.0) -> np.ndarray:
    """Glassy chime (tubular bell partials)."""
    modes = [(freq, seconds * 0.5, 1.0), (freq * 2.756, seconds * 0.25, 0.4), (freq * 5.404, seconds * 0.12, 0.2),
             (freq * 8.933, seconds * 0.06, 0.08)]
    out = modal(seconds, modes, rng)
    if shimmer:
        out = trem(out, 7.0, shimmer)
    return out * np.clip(times(seconds) / 0.002, 0, 1)


def gong(freq: float, seconds: float, rng: np.random.Generator) -> np.ndarray:
    ratios = [1.0, 1.52, 2.11, 2.44, 2.93, 3.4, 4.1, 5.2, 6.3]
    modes = [(freq * r * rng.uniform(0.995, 1.005), seconds * rng.uniform(0.3, 0.9), 1.0 / (1 + i * 0.5))
             for i, r in enumerate(ratios)]
    body = modal(seconds, modes, rng)
    # A gong's shimmer: higher partials swell after the strike.
    swell = resonate(noise(seconds, rng), 2200, 3) * env([(0, 0), (0.3, 0.6), (seconds, 0)], seconds) * 0.6
    hit = lp(noise(0.05, rng), 1500) * decay(0.05, 0.01)
    return place(body + swell, hit, 0.0)


def taiko(seconds: float, rng: np.random.Generator, f: float = 75.0, size: float = 1.0) -> np.ndarray:
    head = thump(seconds, f * 2.2, f, 0.18 * size, 0.0, rng)
    skin = lp(noise(seconds, rng), 900) * decay(seconds, 0.05 * size) * 0.7
    shell = modal(seconds, [(f * 2.6, 0.08, 0.3), (f * 4.1, 0.05, 0.15)], rng)
    return drive(head + skin + shell, 1.4)


def braam(freq: float, seconds: float, rng: np.random.Generator, open_time: float = 0.25, bright: float = 1.0) -> np.ndarray:
    """The big brassy trailer hit: a stack of detuned saws an octave apart, filter opening hard."""
    t = times(seconds)
    tone = np.zeros(len(t))
    for mult, level in ((1.0, 1.0), (0.5, 0.8), (1.5, 0.35), (2.0, 0.4)):
        for c in (-11, -4, 3, 10):
            tone += osc(freq * mult * 2 ** (c / 1200), seconds, "saw", rng.random()) * level
    cut = 120 + (1800 * bright) * env([(0, 0), (open_time, 1), (seconds * 0.5, 0.5), (seconds, 0.2)], seconds)
    out = svf(tone / 8, cut, 1.4, "low")
    a = env([(0, 0), (0.03, 1), (seconds * 0.4, 0.8), (seconds, 0)], seconds, 1.4)
    return drive(out * a * 2.2, 2.2)


def riser(seconds: float, rng: np.random.Generator, f0: float = 200.0, f1: float = 3000.0) -> np.ndarray:
    nz = resonate(noise(seconds, rng, "pink"), sweep(f0, f1, seconds, power=1.8), 3) * 2
    tone = osc(sweep(f0 / 2, f1 / 4, seconds, power=1.8), seconds, "saw") * 0.15
    return (nz + lp(tone, 3000)) * env([(0, 0), (seconds * 0.9, 1), (seconds, 0)], seconds, 2.0)


def choir(freqs: list[float], seconds: float, rng: np.random.Generator, vowel: tuple = (650, 1080, 2650),
          attack: float = 0.4, dark: float = 1.0) -> np.ndarray:
    """A choir pad: detuned buzzing voices through fixed vowel formants."""
    t = times(seconds)
    src = np.zeros(len(t))
    for f in freqs:
        for c in (-9, -3, 4, 10):
            vib = 1 + 0.006 * np.sin(2 * np.pi * rng.uniform(4.5, 5.8) * t + rng.random() * 6)
            src += osc(f * 2 ** (c / 1200) * vib, seconds, "saw", rng.random())
    src /= len(freqs) * 4
    out = sum(resonate(src, fm * dark, q) * g for fm, q, g in zip(vowel, (5, 8, 10), (1.0, 0.5, 0.25)))
    out += resonate(noise(seconds, rng, "pink"), vowel[1] * dark, 4) * 0.04
    a = env([(0, 0), (attack, 1), (seconds - 0.4, 0.9), (seconds, 0)], seconds, 1.2)
    return out * a * 3


def arp(notes: list[float], step: float, note_len: float, rng: np.random.Generator, inst=chime) -> np.ndarray:
    out = silence(step * len(notes) + note_len)
    for i, f in enumerate(notes):
        out = place(out, inst(f, note_len, rng), i * step)
    return out


# --- Element palette: attacks ---------------------------------------------------------

def attack_fire(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.45
    body = thump(d, 160, 70, 0.07, 0.0) * 0.6
    fw = whoosh(d, rng, rng.uniform(250, 380), rng.uniform(1600, 2400), 1.2, [(0, 0), (0.04, 1), (d, 0)])
    roar = lp(noise(d, rng, "brown"), 500) * decay(d, 0.12) * 1.5
    crk = crackle(d, rng, 140, 2500) * decay(d, 0.2) * 0.6
    return (body + fw * 1.2 + roar + crk) * weight


def attack_storm(rng: np.random.Generator, weight: float = 1.0, length: float = 0.32) -> np.ndarray:
    d = length
    n = n_of(d)
    # Sample-and-hold pitch: an arc jumps between frequencies.
    steps = rng.uniform(900, 5000, int(d / 0.004) + 2)
    f = np.repeat(steps, int(0.004 * SR))[:n]
    f = pad_track(f, n)
    arc = osc(f, d, "square") * 0.35 + hp(noise(d, rng), 2500) * 0.8
    arc *= np.repeat(rng.uniform(0.2, 1.0, int(d / 0.012) + 2), int(0.012 * SR))[:n] if n > 0 else 1
    arc *= decay(d, d * 0.45, 0.0005)
    crack = hp(noise(0.03, rng), 1500) * decay(0.03, 0.006) * 1.6
    buzz = osc(120 * rng.uniform(0.95, 1.05), d, "square") * decay(d, 0.08) * 0.25
    zap = osc(sweep(3200, 400, 0.08), 0.08) * decay(0.08, 0.03) * 0.5
    out = place(arc + lp(buzz, 2000), crack, 0.0)
    out = place(out, zap, 0.0)
    return out * weight


def pad_track(x: np.ndarray, n: int) -> np.ndarray:
    if len(x) >= n:
        return x[:n]
    return np.concatenate([x, np.full(n - len(x), x[-1] if len(x) else 0.0)])


def attack_nature(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.4
    out = silence(d)
    twang = pluck(rng.uniform(140, 190), d, rng, 0.993, 0.3)
    out = place(out, twang * 0.7, 0.0)
    for i in range(int(rng.integers(3, 6))):
        thwip = whoosh(0.07, rng, 5000, 1400, 2.5, [(0, 0), (0.01, 1), (0.07, 0)])
        out = place(out, thwip * rng.uniform(0.5, 0.9), 0.015 + i * rng.uniform(0.018, 0.03))
    rustle = hp(noise(d, rng), 3000) * trem(decay(d, 0.08), 40, 0.7) * 0.3
    return (out[:n_of(d)] + rustle) * weight


def attack_water(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.42
    f0 = rng.uniform(220, 300)
    bloop = osc(sweep(f0, f0 * 3.5, 0.12, power=0.7), 0.12) * decay(0.12, 0.05, 0.003)
    gush = svf(noise(d, rng, "pink"), sweep(400, 2400, d, power=0.4), 1.5, "low") * decay(d, 0.1) * 1.2
    bub = bubbles(d, rng, 50, (500, 1800)) * decay(d, 0.18) * 0.7
    out = place(gush + bub, bloop * 0.9, 0.0)
    return out * weight


def attack_earth(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.55
    heave = whoosh(d, rng, 120, 520, 1.1, [(0, 0), (0.08, 1), (d, 0)]) * 1.4
    knock = modal(0.25, [(rng.uniform(150, 190), 0.07, 1.0), (430, 0.04, 0.6), (870, 0.025, 0.4), (1600, 0.012, 0.25)], rng)
    grind = lp(noise(0.2, rng, "brown"), 700) * trem(decay(0.2, 0.08), 30, 0.7) * 1.3
    low = thump(d, 90, 38, 0.12, 0.0) * 0.8
    out = mix(heave, low)
    out = place(out, knock, 0.0)
    out = place(out, grind, 0.01)
    return out * weight


def attack_void(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.5
    swell = svf(noise(0.18, rng, "pink"), sweep(300, 3000, 0.18), 3, "band") * env([(0, 0), (0.17, 1), (0.18, 0)], 0.18, 2.5) * 2
    drop = osc(sweep(900, 70, 0.32, power=0.5), 0.32) * decay(0.32, 0.12)
    drop = drop * 0.6 + ring(drop, 41) * 0.4
    sub = osc(sweep(70, 40, d), d) * decay(d, 0.15, 0.01) * 0.8
    shimmer = resonate(noise(d, rng), sweep(2500, 600, d), 12) * decay(d, 0.2) * 0.6
    out = place(swell, mix(drop, sub, shimmer), 0.16)
    return out * weight


ATTACKS = {"fire": attack_fire, "storm": attack_storm, "nature": attack_nature, "water": attack_water,
           "earth": attack_earth, "void": attack_void}


# --- Element palette: impacts ---------------------------------------------------------

def impact_fire(rng: np.random.Generator) -> np.ndarray:
    d = 0.6
    pop = boom(d, rng, 0.45) * 0.8
    whomp = whoosh(0.25, rng, 1800, 300, 1.0, [(0, 1), (0.25, 0)]) * 0.8
    crk = crackle(d, rng, sweep(200, 20, d), 2500) * decay(d, 0.22) * 0.8
    hiss = hp(noise(d, rng), 4000) * decay(d, 0.15) * 0.25
    return mix(pop, whomp, crk, hiss)


def impact_storm(rng: np.random.Generator) -> np.ndarray:
    d = 0.4
    crack = hp(noise(0.05, rng), 1200) * decay(0.05, 0.008) * 2.0
    snap = osc(sweep(5000, 600, 0.04), 0.04) * decay(0.04, 0.01)
    buzz = osc(rng.choice([100, 120, 150]), d, "square") * hp(noise(d, rng), 200) * 1.2
    buzz = lp(buzz, 3500) * trem(decay(d, 0.09), 60, 0.8) * 0.6
    sizzle = crackle(d, rng, 300, 5000) * decay(d, 0.12) * 0.6
    return mix(place(silence(d), crack + 0, 0.0)[: n_of(d)], place(silence(0.04), snap, 0), buzz, sizzle)


def impact_nature(rng: np.random.Generator) -> np.ndarray:
    d = 0.35
    f = rng.uniform(320, 420)
    thunk = modal(d, [(f, 0.05, 1.0), (f * 2.3, 0.03, 0.5), (f * 3.9, 0.02, 0.3)], rng)
    thunk += lp(noise(d, rng), 1500) * decay(d, 0.015) * 0.8
    leaves = hp(noise(d, rng), 2500) * trem(env([(0, 0), (0.02, 1), (d, 0)], d), 55, 0.8) * 0.35
    return thunk + leaves


def impact_water(rng: np.random.Generator) -> np.ndarray:
    d = 0.6
    splash = svf(noise(d, rng, "pink"), sweep(5000, 500, d, power=0.5), 0.8, "low") * decay(d, 0.12, 0.003) * 1.6
    plop = osc(sweep(180, 520, 0.08), 0.08) * decay(0.08, 0.03) * 0.8
    bub = bubbles(d, rng, 30, (700, 2400)) * decay(d, 0.25) * 0.5
    drops = bubbles(d, rng, 18, (1800, 4200)) * env([(0, 0), (0.1, 1), (d, 0)], d) * 0.35
    return mix(splash, plop, bub, drops)


def impact_earth(rng: np.random.Generator) -> np.ndarray:
    d = 0.6
    hit = thump(d, 120, 45, 0.08, 0.6, rng)
    crunch = modal(0.2, [(rng.uniform(200, 260), 0.05, 1.0), (610, 0.03, 0.6), (1300, 0.02, 0.4), (2700, 0.01, 0.3)], rng)
    crunch += lp(noise(0.2, rng), 3000) * decay(0.2, 0.03) * 1.2
    deb = debris(d, rng, 10, 0.6) * 0.8
    return mix(hit, crunch, deb)


def impact_void(rng: np.random.Generator) -> np.ndarray:
    d = 0.55
    suck = reverse(lp(noise(0.16, rng, "pink"), 2500) * decay(0.16, 0.05)) * 1.6
    pop = osc(sweep(260, 45, 0.3, power=0.4), 0.3) * decay(0.3, 0.1) * 1.2
    zz = ring(resonate(noise(0.3, rng), 1200, 4), 33) * decay(0.3, 0.08) * 0.8
    out = place(suck, mix(pop, zz), 0.15)
    return out


IMPACTS = {"fire": impact_fire, "storm": impact_storm, "nature": impact_nature, "water": impact_water,
           "earth": impact_earth, "void": impact_void}


# --- Element flourishes for build/boss/skill layers -------------------------------------

def flourish(element: str, seconds: float, rng: np.random.Generator) -> np.ndarray:
    """A sustained element texture: fire roar, storm crackle, rustling leaves, water, grinding rock, void hum."""
    d = seconds
    if element == "fire":
        return (lp(noise(d, rng, "brown"), 700) * 2 + crackle(d, rng, 120, 2500) * 0.7) * env([(0, 0), (d * 0.2, 1), (d, 0)], d)
    if element == "storm":
        sizz = crackle(d, rng, 400, 5000) * 0.7
        arcs = silence(d)
        for _ in range(int(d * 5)):
            arcs = place(arcs, attack_storm(rng, 0.5, 0.12), rng.uniform(0, d * 0.9))
        return (sizz + arcs[:n_of(d)]) * env([(0, 0), (d * 0.1, 1), (d, 0)], d)
    if element == "nature":
        rustle = hp(noise(d, rng), 2000) * trem(np.ones(n_of(d)), 23, 0.8) * 0.5
        creak = resonate(trem(noise(d, rng), 31, 0.95), sweep(300, 700, d), 8) * 1.5
        return (rustle + creak) * env([(0, 0), (d * 0.2, 1), (d, 0)], d)
    if element == "water":
        wash = svf(noise(d, rng, "pink"), 900 + 600 * osc(0.8, d), 0.8, "low") * 1.5
        return (wash + bubbles(d, rng, 30, (300, 1500)) * 0.6) * env([(0, 0), (d * 0.3, 1), (d, 0)], d)
    if element == "earth":
        return (rumble(d, rng, 160, 6) * 1.2 + debris(d, rng, int(d * 14), 0.5) * 0.7) * env([(0, 0), (d * 0.1, 1), (d, 0)], d)
    if element == "void":
        hum = sum(osc(f, d) for f in (55, 58.3, 82.4)) / 3
        hum = hum * 0.6 + ring(resonate(noise(d, rng), 900, 6), 29) * 0.6
        return hum * env([(0, 0), (d * 0.3, 1), (d, 0)], d)
    return silence(d)


ELEMENT_ROOT = {"fire": 196.0, "storm": 246.9, "nature": 174.6, "water": 220.0, "earth": 130.8, "void": 155.6}
