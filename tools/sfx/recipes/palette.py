"""The six element palettes: a tower's attack and a shot's impact for each element.

Built from recordings (kit.py): fire is a furnace roar (a gong roll taken down two octaves) and crackle,
storm is real spring-and-metal zaps with a noise crack, nature is a contrabass pizzicato bowstring and
arrow swishes, water is recorded bubbles under a gush, earth is a big hand drum and scraped brick, and
the void is a reversed cymbal falling into a tam-tam.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

from dsp import SR, crackle, decay, env, hp, lp, mix, n_of, noise, osc, place, silence, svf, sweep, whoosh
import kit
from kit import cut
from samples import mono

ELEMENTS = ["fire", "storm", "nature", "water", "earth", "void"]


def pitch(x: np.ndarray, ratio: float) -> np.ndarray:
    """Plays a sound faster (ratio > 1, higher) or slower (lower), like changing tape speed."""
    if abs(ratio - 1.0) < 1e-3:
        return x
    up = int(round(1000 / ratio))
    return signal.resample_poly(x, up, 1000, axis=0)


def reverse(x: np.ndarray) -> np.ndarray:
    return x[::-1].copy()


def _grain(x: np.ndarray, rng, seconds: float, attack: float = 0.004, start_max: float = 0.5) -> np.ndarray:
    """A short slice from somewhere inside a longer recording, with a fast fade in."""
    room = max(0.0, len(x) / SR - seconds)
    start = rng.uniform(0, min(room, start_max))
    y = mono(cut(x, start, seconds, seconds * 0.5))
    a = min(len(y), n_of(attack))
    y[:a] *= np.linspace(0, 1, a)
    return y


def _short(x: np.ndarray, seconds: float) -> np.ndarray:
    return mono(cut(x, 0, seconds, seconds * 0.6))


# --- Attacks ----------------------------------------------------------------------------

def attack_fire(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.45
    roar = _grain(lp(kit.gong_roll(rng, -14 + rng.uniform(-2, 2)), 2500), rng, d, 0.02, 4.0) * env(
        [(0, 0), (0.03, 1), (d, 0)], d) * 1.2
    fw = whoosh(d, rng, rng.uniform(250, 380), rng.uniform(1600, 2400), 1.2, [(0, 0), (0.04, 1), (d, 0)])
    crk = crackle(d, rng, 140, 2500) * decay(d, 0.2) * 0.6
    body = _short(kit.frame_drum(rng, -7), 0.3) * 0.5
    return mix(roar, fw * 0.9, crk, body) * weight


def attack_storm(rng: np.random.Generator, weight: float = 1.0, length: float = 0.32) -> np.ndarray:
    d = length
    zap = _grain(kit.zap(rng, rng.uniform(-3, 3)), rng, d, 0.002, 0.6) * decay(d, d * 0.5, 0.001) * 1.2
    crack = hp(noise(0.03, rng), 1500) * decay(0.03, 0.006) * 1.4
    sizzle = crackle(d, rng, 300, 5000) * decay(d, d * 0.3) * 0.5
    return mix(zap, crack, sizzle) * weight


def attack_nature(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.4
    string = _short(kit.note("bass_pizz", rng.uniform(31, 38), rng), d) * 0.9
    out = place(silence(d), string, 0.0)
    for i in range(int(rng.integers(2, 4))):
        thwip = whoosh(0.08, rng, 5000, 1400, 2.5, [(0, 0), (0.01, 1), (0.08, 0)])
        out = place(out, thwip * rng.uniform(0.4, 0.8), 0.02 + i * rng.uniform(0.02, 0.035))
    rustle = hp(_grain(kit.shaker(rng, 0), rng, d, 0.01, 0.2), 2500) * decay(d, 0.1) * 0.3
    return mix(out[:n_of(d)], rustle) * weight


def attack_water(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.42
    gush = svf(noise(d, rng, "pink"), sweep(400, 2400, d, power=0.4), 1.5, "low") * decay(d, 0.1) * 1.1
    bub = _grain(kit.bubbles(rng, rng.uniform(-2, 4)), rng, d, 0.005, 1.5) * decay(d, 0.2) * 0.8
    drop = _short(kit.giant(rng, 8, "hand"), 0.15) * 0.3
    return mix(gush, bub, drop) * weight


def attack_earth(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.55
    heave = whoosh(d, rng, 120, 520, 1.1, [(0, 0), (0.08, 1), (d, 0)]) * 1.0
    knock = _short(kit.giant(rng, -4 + rng.uniform(-2, 2), "hand"), 0.45) * 1.0
    grind = _grain(kit.brick(rng, -3), rng, 0.25, 0.01, 0.4) * 0.6
    return mix(heave, knock, place(silence(d), grind, 0.01)) * weight


def attack_void(rng: np.random.Generator, weight: float = 1.0) -> np.ndarray:
    d = 0.55
    suck = reverse(_short(kit.cymbal(rng, -4), 0.2)) * 0.8
    drop = _short(kit.tam_tam(rng, -12 + rng.uniform(-2, 2)), 0.4) * 1.0
    sub = osc(sweep(70, 40, 0.4), 0.4) * decay(0.4, 0.12, 0.01) * 0.5
    return place(suck, mix(drop, sub), 0.18)[: n_of(d)] * weight


ATTACKS = {"fire": attack_fire, "storm": attack_storm, "nature": attack_nature, "water": attack_water,
           "earth": attack_earth, "void": attack_void}


# --- Impacts ----------------------------------------------------------------------------

def impact_fire(rng: np.random.Generator) -> np.ndarray:
    d = 0.6
    pop = _short(kit.concert_bass(rng, -2), 0.4) * 0.8
    whomp = whoosh(0.25, rng, 1800, 300, 1.0, [(0, 1), (0.25, 0)]) * 0.7
    crk = crackle(d, rng, sweep(200, 20, d), 2500) * decay(d, 0.22) * 0.8
    return mix(pop, whomp, crk)


def impact_storm(rng: np.random.Generator) -> np.ndarray:
    d = 0.4
    crack = hp(noise(0.05, rng), 1200) * decay(0.05, 0.008) * 1.8
    zap = _grain(kit.zap(rng, rng.uniform(0, 5)), rng, 0.3, 0.002, 0.8) * decay(0.3, 0.08) * 1.0
    sizzle = crackle(d, rng, 300, 5000) * decay(d, 0.12) * 0.5
    return mix(crack, zap, sizzle)


def impact_nature(rng: np.random.Generator) -> np.ndarray:
    d = 0.35
    thunk = _short(kit.log_drum(rng, -7 + rng.uniform(-2, 2)), 0.3) * 0.9
    snap = _short(kit.claves(rng, -10), 0.12) * 0.5
    leaves = hp(noise(d, rng), 2500) * env([(0, 0), (0.02, 1), (d, 0)], d) * 0.25
    return mix(thunk, snap, leaves)


def impact_water(rng: np.random.Generator) -> np.ndarray:
    d = 0.6
    splash = svf(noise(d, rng, "pink"), sweep(5000, 500, d, power=0.5), 0.8, "low") * decay(d, 0.12, 0.003) * 1.4
    bub = _grain(kit.bubbles(rng, rng.uniform(0, 5)), rng, d, 0.005, 1.5) * decay(d, 0.25) * 0.7
    return mix(splash, bub)


def impact_earth(rng: np.random.Generator) -> np.ndarray:
    d = 0.6
    hit = _short(kit.giant(rng, -3 + rng.uniform(-2, 2)), 0.5)
    crunch = _grain(kit.brick(rng, 0), rng, 0.2, 0.002, 0.3) * 0.7
    pebbles = mono(kit.debris(rng, d, 4, 2)) * 0.5
    return mix(hit, crunch, pebbles[: n_of(d)])


def impact_void(rng: np.random.Generator) -> np.ndarray:
    suck = reverse(_short(kit.cymbal(rng, -2), 0.14)) * 0.9
    pop = _short(kit.tam_tam(rng, -9 + rng.uniform(-2, 2)), 0.4) * 1.0
    return place(suck, pop, 0.13)


IMPACTS = {"fire": impact_fire, "storm": impact_storm, "nature": impact_nature, "water": impact_water,
           "earth": impact_earth, "void": impact_void}
