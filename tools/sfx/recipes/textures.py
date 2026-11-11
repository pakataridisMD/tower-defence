"""Element textures from real recordings, shared by bosses, skills and the base.

`bed(element, seconds)` is a sustained layer (a sea surge, a furnace roar, grinding stone, wind,
creaking wood, the hum of the void). `burst(element)` is a short hit of the element. Both are cut from
the VSCO recordings in kit.py, with noise only where nature is noise anyway (surf, wind, fire crackle).
"""

from __future__ import annotations

import numpy as np

from dsp import (SR, crackle, decay, drive, env, hp, lp, mix, n_of, noise, place, resonate, silence, stereo,
                 sweep, svf, trem)
import kit
from kit import cut, tail
from samples import mono, semis


def _fit(x: np.ndarray, seconds: float, fade: float = 0.4) -> np.ndarray:
    n = n_of(seconds)
    if len(x) < n:
        x = np.concatenate([x, np.zeros((n - len(x),) + x.shape[1:])])
    return cut(x, 0, seconds, min(fade, seconds * 0.5))


def _shape(x: np.ndarray, seconds: float, attack: float = 0.3) -> np.ndarray:
    x = _fit(x, seconds)
    e = env([(0, 0), (min(attack, seconds * 0.4), 1), (seconds * 0.6, 0.8), (seconds, 0)], seconds)
    return x * e[:, None] if x.ndim == 2 else x * e


def fire_crackle(seconds: float, rng, density: float = 1.0) -> np.ndarray:
    pops = crackle(seconds, rng, 90 * density, 3000) * 0.5
    roar = lp(noise(seconds, rng, "brown"), 400) * 0.6
    hiss = hp(noise(seconds, rng, "pink"), 3000) * 0.15
    return trem(mix(pops, roar, hiss), rng.uniform(5, 9), 0.25)


def wind(seconds: float, rng, low: float = 300, high: float = 1600) -> np.ndarray:
    f = low + (high - low) * (0.5 + 0.5 * np.sin(np.linspace(0, rng.uniform(2, 5), n_of(seconds))))
    return stereo(resonate(noise(seconds, rng, "pink"), f, 2.5) * 1.6, 0.9, rng=rng)


def thunder(rng, seconds: float = 3.0) -> np.ndarray:
    """A crack, then the roll: a bass drum and crash taken two octaves down under brown noise."""
    crack = hp(noise(0.12, rng), 1500) * decay(0.12, 0.02) * 1.5
    roll = mix(tail(kit.concert_bass(rng, -12), seconds) * 0.8, tail(kit.crash(rng, -19), seconds) * 0.7,
               lp(noise(seconds, rng, "brown"), 220) * decay(seconds, seconds * 0.35, 0.05) * 1.3)
    return mix(place(silence(seconds), roll, 0.04), crack)


def bed(element: str, seconds: float, rng) -> np.ndarray:
    if element == "water":
        rush = kit.water_rush(seconds, rng, 0.8)
        low = kit.held("bass_trem", 28 + rng.integers(0, 4), seconds, rng, 0.4, 0.5) * 0.35
        return mix(rush, _fit(low, seconds))
    if element == "fire":
        furnace = _shape(lp(kit.gong_roll(rng, -14), 1400), seconds) * 0.9
        return mix(furnace, stereo(fire_crackle(seconds, rng), 0.8, rng=rng) * 0.6)
    if element == "earth":
        grind = _shape(lp(kit.drum_rub(rng, -12), 900), seconds) * 1.1
        stones = kit.debris(rng, seconds, int(6 + seconds * 3), -4) * 0.6
        return mix(grind, _fit(stones, seconds))
    if element == "storm":
        return mix(wind(seconds, rng) * 0.6, _fit(thunder(rng, seconds) * 0.7, seconds))
    if element == "nature":
        creak = _shape(lp(kit.guiro(rng, -14), 1800), seconds, 0.5) * 0.7
        rustle = _shape(hp(kit.shaker(rng, -3), 1500), seconds, 0.2) * 0.4
        knock = silence(seconds)
        for i in range(int(seconds * 2)):
            knock = place(knock, kit.log_drum(rng, -rng.uniform(3, 9)) * 0.5, rng.uniform(0, seconds * 0.8))
        return mix(creak, rustle, _fit(knock, seconds), _shape(kit.ratchet(rng, -10), seconds) * 0.35)
    if element == "void":
        hum = _shape(reverse_or_not(kit.bowed(rng, -7), rng), seconds, 0.6) * 0.9
        scrape = _shape(lp(kit.gong_scrape(rng, -12), 2500), seconds, 0.4) * 0.6
        return mix(hum, scrape)
    if element == "cosmos":
        glass = _shape(kit.bowed(rng, -2), seconds, 0.5) * 0.6
        deep = _shape(kit.bowed(rng, -14), seconds, 0.5) * 0.7
        return mix(glass, deep, _shape(lp(kit.gong_roll(rng, -12), 1500), seconds) * 0.6)
    raise ValueError(element)


def reverse_or_not(x: np.ndarray, rng) -> np.ndarray:
    return x[::-1].copy() if rng.random() < 0.5 else x


def burst(element: str, rng, size: float = 1.0) -> np.ndarray:
    """A short, punchy hit of the element (about 1-2 s)."""
    if element == "water":
        splash = svf(noise(1.2, rng, "pink"), sweep(5000, 400, 1.2, power=0.5), 0.7, "low") * decay(1.2, 0.3, 0.005)
        return mix(stereo(splash * 1.4, 0.8, rng=rng), kit.bubbles(rng, -2) * 0.4, tail(kit.giant(rng, -6), 1.0) * 0.5)
    if element == "fire":
        whoomp = svf(noise(1.2, rng, "pink"), sweep(300, 2500, 1.2, power=0.3), 0.9, "low") * env(
            [(0, 0), (0.08, 1), (1.2, 0)], 1.2) * 1.4
        return mix(stereo(whoomp, 0.8, rng=rng), stereo(fire_crackle(1.2, rng, 2) * decay(1.2, 0.5), 0.7, rng=rng) * 0.6,
                   tail(kit.timpani(rng, True, -5), 1.0) * 0.4)
    if element == "earth":
        return mix(tail(kit.giant(rng, -8), 1.4) * 0.9, kit.debris(rng, 1.4, 8, -2) * 0.7,
                   cut(kit.brick(rng, -7), 0, 0.8, 0.3) * 0.6)
    if element == "storm":
        return mix(tail(kit.zap(rng, -2), 1.2) * 0.8, thunder(rng, 1.6) * 0.8)
    if element == "nature":
        snaps = silence(1.0)
        for i in range(5):
            snaps = place(snaps, cut(kit.claves(rng, -rng.uniform(5, 12)), 0, 0.15, 0.05), i * rng.uniform(0.04, 0.09),
                          rng.uniform(0.4, 0.8))
        return mix(snaps, tail(kit.guiro(rng, -7), 0.9) * 0.5, tail(kit.log_drum(rng, -8), 0.6) * 0.6)
    if element == "void":
        suck = kit.reverse(tail(kit.gong(rng, -10), 0.8, 0.0))
        return mix(place(silence(1.6), suck * 0.8, 0.0), place(silence(1.6), tail(kit.tam_tam(rng, -12), 1.2) * 0.8, 0.8))
    if element == "cosmos":
        return mix(*[burst(e, rng) * 0.35 for e in ("fire", "storm", "nature", "water", "earth", "void")])
    raise ValueError(element)
