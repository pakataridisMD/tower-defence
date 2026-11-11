"""Boss sounds: a reveal, footsteps, made-up speech, an enrage roar and a death for every boss.

The six Heralds, the Ashen Regent, the Sundered Heart and Vael-Orrun follow their descriptions in
docs/story (lore thread). The Wardens of the element campaigns share one set per element, and the
plain Warden has its own. Each set is a Character (see voice.py) plus an element and a footstep style.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from dsp import (boom, bubbles, crackle, debris, decay, drive, env, hp, lp, mix, modal, n_of, noise, osc,
                 place, resonate, reverb, ring, rumble, silence, stereo, svf, sweep, thump, times, trem, whoosh)
from registry import sound, register
from voice import Character, phrase, roar, song
from .palette import (ELEMENT_ROOT, attack_storm, bell, braam, chime, choir, flourish, gong, impact_earth, pitch,
                      reverse, riser, semis, taiko)


@dataclass
class BossSet:
    title: str
    element: str          # fire storm nature water earth void, or cosmos for Vael-Orrun
    voice: Character
    step: str             # footstep style
    enemies: tuple[str, ...]


SETS: dict[str, BossSet] = {
    "saltmother": BossSet("Saltmother Ourra, the Drowned Herald", "water",
                          Character(f0=150, tract=0.82, growl=0.35, breath=0.45, voices=2, detune=14, effect="water",
                                    rate=3.6, vowels=["o", "u", "a", "aw"], reverb=2.4, reverb_mix=0.35, octave_down=0.3),
                          "slosh", ("saltmother",)),
    "gorrath": BossSet("Gorrath the Quarried, the Stone Herald", "earth",
                       Character(f0=52, tract=0.55, growl=0.95, breath=0.15, effect="stone", rate=3.0, octave_down=0.5,
                                 drive=3.0, reverb=1.8),
                       "boulder", ("gorrath",)),
    "pale_vesper": BossSet("The Pale Vesper, the Hollow Herald", "void",
                           Character(f0=233, tract=1.0, growl=0.04, breath=0.35, voices=3, detune=10, sing=True,
                                     effect="void", reverb=3.5, reverb_mix=0.45, octave_down=0.0,
                                     vowels=["a", "o", "u", "e"], drive=1.3),
                           "ghost", ("pale_vesper",)),
    "ashwick": BossSet("Ashwick the Kindled, the Flame Herald", "fire",
                       Character(f0=270, tract=1.12, growl=0.25, breath=0.4, rate=6.5, effect="fire", octave_down=0.0,
                                 pitch_range=0.5, vowels=["a", "e", "i", "ae", "o"], reverb=1.2),
                       "run", ("ashwick",)),
    "vholt": BossSet("Vholt Stormcrown, the Sky Herald", "storm",
                     Character(f0=78, tract=0.7, growl=0.6, breath=0.3, rate=3.8, effect="wind", octave_down=0.4,
                               reverb=2.5, reverb_mix=0.35),
                     "wings", ("vholt",)),
    "mother_briar": BossSet("Mother Briar, the Thorn Herald", "nature",
                            Character(f0=125, tract=0.88, growl=0.55, breath=0.6, rate=3.4, effect="wood",
                                      octave_down=0.15, vowels=["e", "a", "i", "o", "ae"], reverb=1.8),
                            "roots", ("mother_briar",)),
    "ashen_regent": BossSet("Cassivane Dral, the Ashen Regent", "fire",
                            Character(f0=88, tract=0.78, growl=0.3, breath=0.25, rate=3.6, effect="ember",
                                      octave_down=0.35, reverb=2.2, reverb_mix=0.3),
                            "armour", ("ashen_regent",)),
    "sundered_heart": BossSet("The Sundered Heart", "void",
                              Character(f0=70, tract=0.65, growl=0.6, voices=2, detune=20, effect="ember",
                                        octave_down=0.5, reverb=2.6, reverb_mix=0.35),
                              "heart", ("sundered_heart",)),
    "vael_orrun": BossSet("Vael-Orrun, the Sunderer", "cosmos",
                          Character(f0=44, tract=0.5, growl=0.75, voices=4, detune=28, effect="cosmos", reverb=4.0,
                                    reverb_mix=0.4, octave_down=0.6, rate=2.6, drive=3.0),
                          "colossus", ("vael_orrun",)),
    "warden": BossSet("A corrupted Warden", "earth",
                      Character(f0=64, tract=0.62, growl=0.7, effect="stone", octave_down=0.4, rate=3.2),
                      "armour", ("warden",)),
    # The corrupted Wardens of each element campaign.
    "fire": BossSet("Fire Warden (Cinder Tyrant)", "fire",
                    Character(f0=68, tract=0.62, growl=0.75, effect="fire", octave_down=0.45, rate=3.2),
                    "stomp_fire", ("cinder_tyrant",)),
    "storm": BossSet("Storm Warden (Thunderhead)", "storm",
                     Character(f0=82, tract=0.68, growl=0.6, effect="wind", octave_down=0.35, rate=3.8),
                     "thunder", ("thunderhead",)),
    "nature": BossSet("Nature Warden (Broodmother)", "nature",
                      Character(f0=140, tract=0.8, growl=0.8, breath=0.5, effect="wood", octave_down=0.2, rate=5.0,
                                consonants=["k", "kh", "s", "sh", "k", "z"], vowels=["i", "e", "ae", "uh"]),
                      "skitter", ("broodmother",)),
    "water": BossSet("Water Warden (Leviathan)", "water",
                     Character(f0=48, tract=0.5, growl=0.45, breath=0.3, effect="water", octave_down=0.5, rate=2.4,
                               vowels=["o", "u", "aw"], reverb=3.0, reverb_mix=0.4, sing=True),
                     "slosh", ("leviathan",)),
    "earth": BossSet("Earth Warden (Mountain Titan)", "earth",
                     Character(f0=42, tract=0.48, growl=0.9, effect="stone", octave_down=0.55, rate=2.6, drive=3.0),
                     "boulder", ("mountain_titan",)),
    "void": BossSet("Void Warden (Hollow King)", "void",
                    Character(f0=72, tract=0.66, growl=0.5, voices=2, detune=22, effect="void", octave_down=0.4,
                              reverb=3.0, reverb_mix=0.4),
                    "drag", ("hollow_king",)),
}

ROOTS = dict(ELEMENT_ROOT, cosmos=110.0)
REVEAL = dict(positional=False, priority=8)


def _element_layer(element: str, seconds: float, rng) -> np.ndarray:
    if element == "cosmos":
        return mix(*[flourish(e, seconds, rng) * 0.4 for e in ("fire", "storm", "nature", "water", "earth", "void")])
    return flourish(element, seconds, rng)


# --- Footsteps ----------------------------------------------------------------------------

def step(style: str, rng) -> np.ndarray:
    if style == "boulder":
        return mix(thump(0.8, 70, 26, 0.2, 0.6, rng) * 1.4, debris(0.8, rng, 10, 0.45) * 0.6,
                   modal(0.3, [(rng.uniform(110, 140), 0.08, 1.0), (320, 0.05, 0.5)], rng) * 0.5)
    if style == "slosh":
        splash = svf(noise(0.8, rng, "pink"), sweep(2500, 300, 0.8, power=0.5), 0.8, "low") * decay(0.8, 0.18) * 1.5
        return mix(thump(0.7, 80, 35, 0.12, 0.0) * 1.0, splash, bubbles(0.8, rng, 30, (200, 900)) * 0.4)
    if style == "ghost":
        breath = resonate(noise(0.9, rng, "pink"), sweep(600, 1400, 0.9), 4) * env([(0, 0), (0.4, 1), (0.9, 0)], 0.9) * 1.2
        toll = chime(rng.choice([466, 523, 554]), 1.2, rng) * 0.25
        return mix(ring(breath, 29) * 0.6 + breath * 0.4, toll)
    if style == "run":
        out = silence(0.5)
        for i in range(2):
            fall = mix(thump(0.15, 180, 90, 0.03, 0.4, rng) * 0.7, crackle(0.25, rng, 200, 2500) * decay(0.25, 0.08) * 0.8)
            out = place(out, fall, i * 0.18 + rng.uniform(0, 0.02))
        return mix(out, whoosh(0.5, rng, 600, 1800, 1.0) * 0.3)
    if style == "wings":
        flap = whoosh(0.55, rng, 120, 500, 0.9, [(0, 0), (0.15, 1), (0.55, 0)]) * 2.0
        thunder = lp(noise(1.0, rng, "brown"), 250) * env([(0, 0), (0.2, 1), (1.0, 0)], 1.0) * 1.2
        return mix(flap, thunder * rng.uniform(0.3, 0.8), crackle(0.6, rng, 40, 4000) * 0.3)
    if style == "roots":
        drag = resonate(trem(noise(0.9, rng), rng.uniform(20, 35), 0.95), sweep(250, 500, 0.9), 9) * env([(0, 0), (0.2, 1), (0.9, 0)], 0.9) * 2.5
        thud = thump(0.5, 100, 45, 0.1, 0.3, rng) * 0.8
        rustle = hp(noise(0.7, rng), 2500) * trem(env([(0, 0), (0.1, 1), (0.7, 0)], 0.7), 45, 0.8) * 0.4
        return mix(thud, drag, rustle)
    if style == "armour":
        boot = thump(0.5, 110, 50, 0.09, 0.5, rng)
        f = rng.uniform(500, 650)
        clank = modal(0.4, [(f, 0.12, 1.0), (f * 1.52, 0.09, 0.7), (f * 2.3, 0.05, 0.4), (f * 3.7, 0.03, 0.2)], rng) * 0.6
        return mix(boot, place(silence(0.5), clank, 0.01), crackle(0.4, rng, 60, 2500) * 0.3)
    if style == "heart":
        lub = thump(0.4, 75, 35, 0.1, 0.0) * 1.3
        dub = thump(0.4, 62, 30, 0.08, 0.0) * 1.0
        wet = lp(noise(0.3, rng, "brown"), 300) * decay(0.3, 0.05) * 0.6
        return place(mix(lub, wet), mix(dub, wet * 0.7), 0.24)
    if style == "colossus":
        hit = mix(boom(1.6, rng, 1.6) * 0.6, thump(1.6, 55, 20, 0.45, 0.6, rng) * 1.4, debris(1.6, rng, 25, 0.4) * 0.5)
        hum = ring(osc(55, 1.6), 23) * decay(1.6, 0.5) * 0.25
        return mix(hit, hum)
    if style == "stomp_fire":
        return mix(thump(0.8, 85, 30, 0.16, 0.5, rng) * 1.3, flourish("fire", 0.7, rng) * 0.5)
    if style == "thunder":
        return mix(thump(0.7, 90, 35, 0.12, 0.4, rng), attack_storm(rng, 0.5, 0.2),
                   lp(noise(1.0, rng, "brown"), 250) * decay(1.0, 0.3) * 0.8)
    if style == "skitter":
        out = silence(0.7)
        for i in range(14):
            click = mix(modal(0.04, [(rng.uniform(1800, 3500), 0.008, 1.0)], rng), hp(noise(0.02, rng), 3000) * decay(0.02, 0.003))
            out = place(out, click * rng.uniform(0.3, 0.8), i * 0.04 + rng.uniform(0, 0.015))
        return mix(out, thump(0.5, 90, 45, 0.08, 0.0) * 0.8)
    if style == "drag":
        scrape = lp(noise(0.9, rng, "brown"), 600) * trem(env([(0, 0), (0.3, 1), (0.9, 0)], 0.9), 18, 0.6) * 2
        return mix(thump(0.7, 75, 32, 0.14, 0.4, rng), scrape, flourish("void", 0.9, rng) * 0.3)
    raise ValueError(style)


# --- Reveal, enrage, death ---------------------------------------------------------------------

def reveal(bs: BossSet, rng) -> np.ndarray:
    root = ROOTS[bs.element] / 2
    d = 5.0
    hit = mix(braam(root / 2 if bs.element != "cosmos" else 27.5, 3.0, rng, 0.15),
              taiko(2.0, rng, 48, 2.2) * 0.9, gong(root, 4.0, rng) * 0.35)
    swell = _element_layer(bs.element, 3.5, rng) * 0.8
    lead = riser(0.9, rng, 150, 2000) * 0.4
    if bs.voice.sing:
        notes = [(0, 0.5, "a"), (3, 0.4, "o"), (7, 0.5, "a"), (6, 1.4, "u")]
        voice = song(bs.voice, notes, rng)
    else:
        voice = roar(bs.voice, 2.0, rng, 0.25, 0.45)
    out = place(silence(d), lead, 0.0)
    out = place(out, mix(hit, swell), 0.85)
    out = place(out, voice * 1.1, 1.25)
    if bs.element == "cosmos":
        # Six element hits in a row for the overlord.
        for i, e in enumerate(("fire", "storm", "nature", "water", "earth", "void")):
            out = place(out, flourish(e, 0.5, rng) * 0.8, 1.0 + i * 0.12)
    return reverb(stereo(out, 0.7, rng=rng), 2.8, 0.3, rng=rng, wide=True)


def enrage(bs: BossSet, rng) -> np.ndarray:
    if bs.voice.sing:
        voice = song(bs.voice, [(12, 0.3, "a"), (13, 0.3, "a"), (18, 1.0, "i")], rng)
    else:
        voice = roar(bs.voice, 1.8, rng, 0.2, 0.5, ("a", "aw", "a", "o"), 1.8)
    burst = mix(_element_layer(bs.element, 1.6, rng), taiko(1.2, rng, 55, 1.6) * 0.7)
    return reverb(stereo(mix(voice, burst * 0.7), 0.6, rng=rng), 2.0, 0.25, rng=rng)


def death(bs: BossSet, rng, key: str) -> np.ndarray:
    d = 6.0
    if bs.voice.sing:
        cry = song(bs.voice, [(12, 0.4, "a"), (11, 0.4, "a"), (6, 0.6, "o"), (-1, 1.8, "u")], rng)
    else:
        cry = roar(bs.voice, 2.6, rng, 0.15, 0.8, ("a", "aw", "o", "u"), 1.5)
    collapse = mix(boom(3.5, rng, 2.0) * 0.9, debris(3.5, rng, 40, 0.5) * 0.5)
    layer = _death_layer(key, bs, rng)
    out = place(silence(d), cry, 0.0)
    out = place(out, collapse, 1.6)
    out = place(out, layer, 0.8)
    return reverb(stereo(out, 0.7, rng=rng), 3.2, 0.3, rng=rng, wide=True)


def _death_layer(key: str, bs: BossSet, rng) -> np.ndarray:
    if key == "saltmother":
        # The column of seawater falls: a great wash, then draining gurgles.
        wash = svf(noise(3.0, rng, "pink"), sweep(4000, 300, 3.0, power=0.4), 0.8, "low") * decay(3.0, 0.9, 0.05) * 2.2
        return mix(wash, place(silence(4), bubbles(2.5, rng, 60, (150, 700)) * 0.7, 1.2))
    if key == "gorrath":
        # He breaks into three walking boulders.
        out = silence(3.5)
        for i in range(3):
            out = place(out, mix(impact_earth(rng), thump(0.8, 70, 28, 0.2, 0.5, rng)) * 1.1, 1.2 + i * 0.45)
        return mix(out, rumble(3.5, rng, 140, 5) * env([(0, 0), (0.5, 1), (3.5, 0)], 3.5))
    if key == "pale_vesper":
        # The song cracks into a choir of the dead letting go.
        pad = choir([semis(116.5, s) for s in (0, 1, 6, 11)], 3.5, rng, (500, 900, 2500), 0.3) * 0.7
        return mix(pad, reverse(resonate(noise(1.5, rng, "pink"), 1200, 3) * decay(1.5, 0.5)) * 0.6)
    if key in ("ashwick", "fire"):
        # The fire goes out: a last flare and a long steam hiss.
        flare = flourish("fire", 1.0, rng) * 1.2
        hiss = hp(noise(3.0, rng), 2500) * env([(0, 0), (0.8, 1), (3.0, 0)], 3.0) * 0.6
        return mix(flare, place(silence(3.5), hiss, 0.7))
    if key in ("vholt", "storm"):
        thunder = mix(hp(noise(0.2, rng), 600) * decay(0.2, 0.03) * 2, lp(noise(4.0, rng, "brown"), 250) * decay(4.0, 1.2) * 2.5)
        screech = roar(Character(f0=700, tract=1.4, growl=0.4, breath=0.4, octave_down=0.0, reverb=1.5), 1.2, rng,
                       0.1, 0.8, ("i", "e", "a"), 1.2)
        return mix(thunder, screech * 0.6, place(silence(4), whoosh(2.5, rng, 1500, 200, 0.8) * 0.6, 0.8))
    if key in ("mother_briar", "nature"):
        out = silence(3.5)
        for i in range(10):
            snap = mix(modal(0.2, [(rng.uniform(300, 900), 0.04, 1.0), (rng.uniform(1200, 2000), 0.02, 0.5)], rng),
                       hp(noise(0.06, rng), 1500) * decay(0.06, 0.01))
            out = place(out, snap * rng.uniform(0.5, 1.0), rng.uniform(0, 2.0))
        sigh = roar(Character(f0=110, tract=0.9, growl=0.1, breath=0.9, octave_down=0.0, reverb=2.0), 1.6, rng,
                    0.2, 0.7, ("a", "o", "u"), 0.6)
        return mix(out, flourish("nature", 3.0, rng) * 0.6, place(silence(4), sigh * 0.6, 1.8))
    if key in ("ashen_regent",):
        # Armour hits the ground; embers scatter.
        f = 420
        clang = modal(2.0, [(f, 0.6, 1.0), (f * 1.52, 0.4, 0.7), (f * 2.3, 0.3, 0.5), (f * 3.7, 0.2, 0.3)], rng)
        return mix(place(silence(3), clang * 0.7, 0.6), flourish("fire", 2.5, rng) * 0.5, flourish("void", 2.5, rng) * 0.4)
    if key == "sundered_heart":
        out = silence(3.5)
        for i, t in enumerate((0.0, 0.7, 1.5, 2.5)):
            beat = step("heart", rng) * (1.2 - i * 0.25)
            out = place(out, pitch(beat, 1.0 - i * 0.08), t)
        return mix(out, place(silence(3.5), choir([semis(110, s) for s in (0, 7, 12)], 2.5, rng, attack=0.8) * 0.5, 1.0))
    if key == "vael_orrun":
        out = silence(5.0)
        for i, e in enumerate(("void", "earth", "water", "nature", "storm", "fire")):
            out = place(out, mix(flourish(e, 0.9, rng), boom(0.9, rng, 0.8) * 0.5), 0.2 + i * 0.35)
        implode = reverse(reverb(boom(1.5, rng, 1.5), 1.5, 0.7, rng=rng))[: n_of(1.5)] * 0.9
        return mix(out, place(silence(5.0), implode, 2.2), place(silence(5.0), boom(2.5, rng, 2.2), 3.7),
                   place(silence(5.0), choir([semis(55, s) for s in (0, 7, 12, 16, 19)], 1.3, rng, attack=0.4) * 0.6, 3.7))
    if key in ("water",):
        return svf(noise(3.0, rng, "pink"), sweep(3000, 200, 3.0, power=0.5), 0.8, "low") * decay(3.0, 0.8, 0.05) * 2
    if key in ("earth", "warden"):
        return mix(rumble(3.0, rng, 140, 5) * env([(0, 0), (0.3, 1), (3.0, 0)], 3.0) * 1.2, debris(3.0, rng, 30, 0.5) * 0.7)
    if key == "void":
        return mix(reverse(resonate(noise(1.5, rng, "pink"), 900, 2) * decay(1.5, 0.5)) * 0.8, flourish("void", 3.0, rng) * 0.7)
    return _element_layer(bs.element, 3.0, rng)


def voice_line(bs: BossSet, rng, v: int) -> np.ndarray:
    if bs.voice.sing and bs.element != "water":
        melodies = [[(0, 0.4, "a"), (2, 0.3, "o"), (3, 0.6, "a"), (-2, 0.9, "u")],
                    [(7, 0.5, "o"), (5, 0.3, "a"), (3, 0.3, "e"), (2, 1.0, "a")],
                    [(-5, 0.4, "u"), (0, 0.4, "o"), (1, 0.4, "a"), (0, 1.1, "o")]]
        return song(bs.voice, melodies[v % 3], rng)
    if bs.voice.sing:
        # The Leviathan: a whale-like moan.
        return roar(bs.voice, 2.2, rng, 0.4, 0.5, ("u", "o", "u"), 0.9)
    length = [1.8, 2.3, 1.4][v % 3]
    return phrase(bs.voice, length, rng, intensity=1.0 + 0.2 * v, question=(v == 1))


def _register_set(key: str, bs: BossSet) -> None:
    folder = f"bosses/{key}"
    register(f"boss_{key}_reveal", folder, lambda rng, v: reveal(bs, rng), loud=-11.0, duck_db=-12.0, duck_time=4.0,
             **REVEAL, description=f"{bs.title} appears")
    register(f"boss_{key}_step", folder, lambda rng, v: step(bs.step, rng), variants=3, loud=-19.0, max_voices=2,
             min_gap=0.15, pitch_jitter=0.05, priority=3, description=f"{bs.title} walks")
    register(f"boss_{key}_voice", folder, lambda rng, v: voice_line(bs, rng, v), variants=3, loud=-15.0, max_voices=1,
             min_gap=1.0, priority=6, duck_db=-5.0, duck_time=2.5, description=f"{bs.title} speaks")
    register(f"boss_{key}_enrage", folder, lambda rng, v: enrage(bs, rng), loud=-13.0, max_voices=1, priority=7,
             duck_db=-6.0, duck_time=2.0, description=f"{bs.title} is wounded and enraged")
    register(f"boss_{key}_death", folder, lambda rng, v: death(bs, rng, key), loud=-11.0, max_voices=1, priority=8,
             duck_db=-12.0, duck_time=4.0, positional=False, description=f"{bs.title} dies")


for _key, _bs in SETS.items():
    _register_set(_key, _bs)


# --- Boss tricks and the assault ---------------------------------------------------------------

@sound("boss_silence", "bosses", loud=-16.0, max_voices=1, min_gap=1.0, priority=6,
       description="a boss silences nearby towers")
def boss_silence(rng, v):
    d = 1.6
    suck = reverse(resonate(noise(0.8, rng, "pink"), sweep(400, 3000, 0.8), 3) * decay(0.8, 0.3)) * 1.5
    whine = osc(sweep(3000, 4200, d), d) * env([(0, 0), (0.75, 0), (0.8, 0.3), (d, 0)], d) * 0.15
    thud = ring(thump(0.8, 90, 40, 0.2, 0.0), 31) * 1.0
    return reverb(mix(suck, whine, place(silence(d), thud, 0.75)), 2.0, 0.4, rng=rng)


@sound("boss_blink", "bosses", loud=-17.0, max_voices=1, min_gap=0.5, priority=5,
       description="a boss steps forward through shadow")
def boss_blink(rng, v):
    out_ = reverse(whoosh(0.35, rng, 300, 2500, 1.5)) * 1.2
    pop = ring(osc(sweep(800, 120, 0.15), 0.15), 40) * decay(0.15, 0.05)
    arrive = whoosh(0.4, rng, 2500, 300, 1.5, [(0, 1), (0.4, 0)]) * 0.8
    return reverb(mix(out_, place(silence(0.8), mix(pop, arrive), 0.33)), 1.2, 0.3, rng=rng)


@sound("boss_escape", "bosses", loud=-15.0, max_voices=1, priority=7, positional=False,
       description="a beaten boss escapes the board")
def boss_escape(rng, v):
    d = 2.5
    rise = riser(1.2, rng, 200, 4000) * 0.6
    vanish = mix(reverse(reverb(boom(0.8, rng, 0.8), 1.0, 0.5, rng=rng))[: n_of(0.8)] * 0.8,
                 whoosh(1.2, rng, 3000, 150, 0.8) * 0.8)
    laugh = phrase(SETS["ashen_regent"].voice, 1.2, rng, 1.2)
    out = mix(rise, place(silence(d), vanish, 1.0), place(silence(d), laugh * 0.7, 0.0))
    return reverb(stereo(out, 0.6, rng=rng), 2.0, 0.3, rng=rng)


@sound("structure_collapse", "bosses", variants=2, loud=-12.0, max_voices=1, priority=7, duck_db=-8.0, duck_time=3.0,
       description="a building of the enemy citadel falls")
def structure_collapse(rng, v):
    d = 5.0
    out = silence(d)
    for i in range(6):
        out = place(out, mix(impact_earth(rng), thump(0.8, 80, 30, 0.2, 0.6, rng)) * rng.uniform(0.6, 1.0), i * rng.uniform(0.25, 0.4))
    out = mix(out, boom(4.0, rng, 2.2) * 0.8, debris(d, rng, 80, 0.5) * 0.6,
              rumble(d, rng, 120, 4) * env([(0, 0), (0.5, 1), (d, 0)], d))
    return reverb(stereo(out, 0.7, rng=rng), 3.0, 0.3, rng=rng)


@sound("assault_phase", "bosses", loud=-13.0, duck_db=-8.0, duck_time=3.0, positional=False, priority=6,
       description="the assault moves on to its next part")
def assault_phase(rng, v):
    from .palette import horn_call
    horn = horn_call([(98.0, 0.0, 0.6), (130.8, 0.7, 0.6), (146.8, 1.4, 2.0)], rng, layers=(1.0, 0.7))
    drums = silence(3.6)
    for i in range(6):
        drums = place(drums, taiko(1.0, rng, 60, 1.5), i * 0.35)
    return reverb(stereo(mix(horn, drums * 0.8), 0.6, rng=rng), 2.6, 0.35, rng=rng)


def boss_sets() -> dict[str, str]:
    """Which sound set each boss enemy uses."""
    out = {}
    for key, bs in SETS.items():
        for enemy in bs.enemies:
            out[enemy] = key
    return out
