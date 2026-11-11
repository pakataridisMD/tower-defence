"""Tower attacks (one sound per tower, built from its elements and how it fights), impacts,
explosions, enemy deaths and other enemy events."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from dsp import (boom, bubbles, crackle, debris, decay, drive, env, hp, lp, mix, modal, n_of, noise, osc, svf,
                 place, resonate, reverb, ring, silence, sweep, thump, trem, whoosh)
from registry import register, sound
from voice import Character, phrase, roar
from .palette import ATTACKS, IMPACTS, attack_storm, chime, pitch, reverse

ROOT = Path(__file__).resolve().parents[3]


def read_towers() -> list[dict]:
    """Elements and attack style of every tower in data/towers, so new towers get a sound automatically."""
    out = []
    for path in sorted((ROOT / "data" / "towers").glob("*.tres")):
        # Only the [resource] section: sub-resources (ascendancies) have ids and stats of their own.
        text = path.read_text().split("[resource]")[-1]
        tid = re.search(r'^id = &"([^"]+)"', text, re.M).group(1)
        elements = re.findall(r'&"(\w+)"', re.search(r"^elements = (.*)$", text, re.M).group(1))

        def num(key: str) -> float:
            m = re.search(rf"^{key} = ([\d.]+)", text, re.M)
            return float(m.group(1)) if m else 0.0

        out.append({"id": tid, "elements": elements, "splash": num("splash_radius"), "chain": num("chain_count"),
                    "knockback": num("knockback"), "aura": num("aura_radius"), "rate": num("attacks_per_second") or 1.0})
    return out


TOWERS = read_towers()


def tower_attack(tower: dict, rng: np.random.Generator) -> np.ndarray:
    elements = tower["elements"]
    size = len(elements)
    parts = []
    for i, element in enumerate(elements):
        weight = 1.0 if i == 0 else (0.7 if i == 1 else 0.55)
        if element == "storm" and tower["chain"] > 0:
            parts.append(attack_storm(rng, weight, 0.28 + 0.03 * tower["chain"]))
        else:
            parts.append(ATTACKS[element](rng, weight))
    if tower["chain"] > 0 and "storm" not in elements:
        parts.append(attack_storm(rng, 0.45, 0.2))
    if tower["knockback"] > 0:
        push = whoosh(0.3, rng, 160, 700, 1.0, [(0, 0), (0.03, 1), (0.3, 0)]) * min(1.0, tower["knockback"] / 20)
        parts.append(push)
    if size >= 2:
        parts.append(thump(0.4, 110, 45, 0.08 if size == 2 else 0.12, 0.0) * (0.35 if size == 2 else 0.6))
    out = mix(*parts)
    # Slow, heavy towers sound bigger; triples are the heaviest.
    ratio = 1.0
    if tower["rate"] <= 0.6:
        ratio *= 0.92
    if size == 3:
        ratio *= 0.9
    out = pitch(out, ratio * rng.uniform(0.97, 1.03))
    if size == 3:
        out = reverb(out, 0.6, 0.12, 6000, rng=rng)
    return out


for _tower in TOWERS:
    _size = len(_tower["elements"])
    register(
        f"tower_{_tower['id']}", "towers",
        (lambda t: (lambda rng, v: tower_attack(t, rng)))(_tower),
        variants=3 if _size == 1 else 2,
        loud=-21.0 if _size == 1 else -20.0,
        volume_db=-5.0,
        max_voices=3, min_gap=0.06, pitch_jitter=0.06, priority=1,
        description=f"{_tower['id'].replace('_', ' ')} attacks ({', '.join(_tower['elements'])})",
    )


# --- Impacts and explosions -------------------------------------------------------------

for _element, _fn in IMPACTS.items():
    register(f"impact_{_element}", "impacts", (lambda f: (lambda rng, v: f(rng)))(_fn), variants=3,
             loud=-22.0, volume_db=-6.0, max_voices=4, min_gap=0.04, pitch_jitter=0.08,
             description=f"a {_element} shot hits")


def _explosion(size: float):
    def make(rng, v):
        d = 0.8 + size * 0.6
        out = boom(d, rng, size)
        out = mix(out, debris(d, rng, int(6 + size * 10), 0.8) * 0.5)
        return reverb(out, 0.5 + size * 0.4, 0.15, 5000, rng=rng)
    return make


for _name, _size, _loud in (("explosion_small", 0.6, -20.0), ("explosion_medium", 1.0, -18.0), ("explosion_large", 1.5, -16.0)):
    register(_name, "impacts", _explosion(_size), variants=3, loud=_loud, volume_db=-5.0, max_voices=3,
             min_gap=0.08, pitch_jitter=0.06, priority=2, description=f"splash shot explodes ({_name.split('_')[1]})")


@sound("hit_armour", "impacts", variants=3, loud=-24.0, volume_db=-6.0, max_voices=2, min_gap=0.07, pitch_jitter=0.1,
       description="a shot glances off heavy armour")
def hit_armour(rng, v):
    f = rng.uniform(700, 1100)
    clang = modal(0.35, [(f, 0.12, 1.0), (f * 1.47, 0.09, 0.7), (f * 2.09, 0.06, 0.5), (f * 2.76, 0.04, 0.4), (f * 3.9, 0.03, 0.2)], rng)
    tick = hp(noise(0.02, rng), 3000) * decay(0.02, 0.003)
    return place(clang, tick, 0.0)


# --- Enemy deaths ------------------------------------------------------------------------

def _gibberish_death(ch: Character, rng, length: float) -> np.ndarray:
    return roar(ch, length, rng, rise=0.15, fall=0.75, vowel_path=("a", "aw", "o", "u"), intensity=1.0)


def body_fall(rng, weight: float = 1.0, d: float = 0.5) -> np.ndarray:
    return mix(thump(d, 90, 40, 0.06, 0.3, rng) * weight, lp(noise(d, rng, "brown"), 400) * decay(d, 0.05) * weight)


@sound("death_grunt", "enemies", variants=3, loud=-22.0, volume_db=-4.0, max_voices=3, min_gap=0.05, pitch_jitter=0.08,
       description="a grunt dies")
def death_grunt(rng, v):
    ch = Character(f0=rng.uniform(130, 170), tract=0.95, growl=0.6, breath=0.3, drive=2.5, reverb=0.5, reverb_mix=0.1,
                   octave_down=0.2)
    yell = _gibberish_death(ch, rng, rng.uniform(0.35, 0.5))
    return place(yell, body_fall(rng, 0.7), 0.25)


@sound("death_runner", "enemies", variants=3, loud=-23.0, volume_db=-4.0, max_voices=3, min_gap=0.05, pitch_jitter=0.1,
       description="a fast runner dies")
def death_runner(rng, v):
    ch = Character(f0=rng.uniform(300, 380), tract=1.25, growl=0.3, breath=0.4, drive=2.0, reverb=0.4, reverb_mix=0.1,
                   octave_down=0.0, vowels=["i", "e", "ae"])
    yelp = roar(ch, 0.28, rng, 0.1, 0.8, ("i", "e", "ae"), 1.0)
    skid = whoosh(0.25, rng, 3000, 900, 2.0, [(0, 1), (0.25, 0)]) * 0.4
    return place(yelp, skid, 0.12)


@sound("death_brute", "enemies", variants=3, loud=-20.0, volume_db=-3.0, max_voices=2, min_gap=0.08, pitch_jitter=0.06,
       description="a brute falls")
def death_brute(rng, v):
    ch = Character(f0=rng.uniform(70, 90), tract=0.7, growl=0.9, breath=0.3, drive=3.0, reverb=0.7, reverb_mix=0.15)
    groan = roar(ch, 0.8, rng, 0.2, 0.7, ("uh", "aw", "o"), 1.1)
    fall = mix(thump(0.7, 80, 32, 0.15, 0.5, rng) * 1.3, debris(0.7, rng, 6, 0.5) * 0.4)
    return place(groan, fall, 0.45)


@sound("death_mender", "enemies", variants=3, loud=-23.0, volume_db=-4.0, max_voices=2, min_gap=0.06, pitch_jitter=0.08,
       description="a mender's healing light goes out")
def death_mender(rng, v):
    gasp = roar(Character(f0=240, tract=1.1, growl=0.1, breath=0.7, drive=1.5, reverb=0.8), 0.35, rng, 0.2, 0.6, ("a", "o"), 0.8)
    fade_chime = sum(chime(f, 0.9, rng) for f in (880 * rng.uniform(0.98, 1.02), 1320, 1760)) * 0.3
    fade_chime = fade_chime * np.linspace(1, 0, len(fade_chime)) ** 2
    return mix(gasp, reverse(fade_chime) * 0.3, place(silence(0.1), fade_chime, 0.1))


@sound("death_splitter", "enemies", variants=3, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.06, pitch_jitter=0.08,
       description="a splitter bursts into shardlings")
def death_splitter(rng, v):
    squelch = svf(noise(0.3, rng), sweep(3000, 300, 0.3), 3, "band") * decay(0.3, 0.08) * 2.5
    pop = osc(sweep(400, 90, 0.15), 0.15) * decay(0.15, 0.05)
    shards = mix(*[place(silence(0.4), modal(0.2, [(rng.uniform(2500, 5000), 0.04, 1.0), (rng.uniform(6000, 8000), 0.02, 0.5)], rng), rng.uniform(0.02, 0.2)) for _ in range(6)]) * 0.35
    return mix(squelch, pop, shards)


@sound("death_shardling", "enemies", variants=3, loud=-24.0, volume_db=-4.0, max_voices=3, min_gap=0.04, pitch_jitter=0.12,
       description="a shardling shatters like glass")
def death_shardling(rng, v):
    d = 0.5
    out = hp(noise(0.04, rng), 2500) * decay(0.04, 0.01) * 1.5
    out = place(silence(d), out, 0.0)
    for _ in range(10):
        f = rng.uniform(2000, 7000)
        tink = modal(0.25, [(f, 0.06, 1.0), (f * 1.58, 0.04, 0.5), (f * 2.3, 0.02, 0.3)], rng)
        out = place(out, tink * rng.uniform(0.15, 0.5), rng.uniform(0, 0.25))
    return out


@sound("death_warded", "enemies", variants=3, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.06, pitch_jitter=0.06,
       description="a warded enemy's shield breaks")
def death_warded(rng, v):
    shield = modal(0.7, [(523 * rng.uniform(0.98, 1.02), 0.25, 1.0), (784, 0.2, 0.6), (1046, 0.15, 0.5), (1568, 0.1, 0.3)], rng)
    shield = shield * env([(0, 1), (0.08, 1), (0.1, 0.2), (0.7, 0)], 0.7)
    shatter = hp(noise(0.25, rng), 3000) * decay(0.25, 0.05) * 1.2
    zap = ring(resonate(noise(0.2, rng), 1500, 5), 70) * decay(0.2, 0.05)
    return mix(shield, place(silence(0.1), mix(shatter, zap), 0.08), place(silence(0.2), body_fall(rng, 0.6), 0.2))


@sound("death_shade", "enemies", variants=3, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.08, pitch_jitter=0.06,
       description="a hollow shade dissolves with a wail")
def death_shade(rng, v):
    ch = Character(f0=rng.uniform(250, 330), tract=1.0, growl=0.05, breath=0.8, voices=2, detune=25, drive=1.4,
                   reverb=2.2, reverb_mix=0.45, effect="void", octave_down=0.0, vowels=["o", "u", "a"])
    wail = roar(ch, 0.9, rng, 0.1, 0.85, ("o", "u", "u"), 0.8)
    return mix(wail, reverse(lp(noise(0.3, rng), 2000) * decay(0.3, 0.08)) * 0.5)


@sound("enemy_split", "enemies", variants=2, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.1,
       description="an enemy breaks into smaller ones")
def enemy_split(rng, v):
    tear = svf(noise(0.35, rng), sweep(400, 2500, 0.35), 4, "band") * env([(0, 0), (0.25, 1), (0.35, 0)], 0.35) * 2
    pops = mix(*[place(silence(0.5), osc(sweep(300, 900, 0.06), 0.06) * decay(0.06, 0.02), 0.3 + i * 0.05) for i in range(3)])
    return mix(tear, pops * 0.7)


@sound("enemy_summon", "enemies", variants=2, loud=-19.0, volume_db=-2.0, max_voices=2, min_gap=0.4, priority=2,
       description="a boss calls up more enemies")
def enemy_summon(rng, v):
    d = 1.2
    portal = ring(resonate(noise(d, rng, "pink"), sweep(200, 1400, d, power=0.6), 6), 47) * env([(0, 0), (0.6, 1), (d, 0)], d) * 2
    low = osc(sweep(50, 80, d), d) * env([(0, 0), (0.7, 1), (d, 0)], d)
    pop = boom(0.6, rng, 0.5) * 0.6
    return reverb(place(mix(portal, low), pop, 0.7), 1.2, 0.3, rng=rng)


@sound("status_burn", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy catches fire")
def status_burn(rng, v):
    d = 0.5
    return mix(whoosh(d, rng, 400, 1800, 1.0, [(0, 0), (0.05, 1), (d, 0)]), crackle(d, rng, 150, 2500) * decay(d, 0.2) * 0.8)


@sound("status_freeze", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is slowed by water and frost")
def status_freeze(rng, v):
    d = 0.6
    crystals = mix(*[place(silence(d), chime(rng.uniform(2500, 5000), 0.3, rng), rng.uniform(0, 0.25)) for _ in range(5)]) * 0.3
    crackling = hp(crackle(d, rng, 200, 6000), 4000) * decay(d, 0.2)
    return mix(crystals, crackling)


@sound("status_poison", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is poisoned")
def status_poison(rng, v):
    d = 0.6
    return mix(bubbles(d, rng, 40, (150, 600)) * 0.8, svf(noise(d, rng), 600, 3, "band") * decay(d, 0.2) * 0.8)


@sound("status_stun", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is stunned")
def status_stun(rng, v):
    d = 0.5
    tweet = sum(osc(sweep(f, f * 1.3, d), d) for f in (1800, 2400)) * trem(decay(d, 0.2), 14, 0.9) * 0.4
    return mix(tweet, attack_storm(rng, 0.4, 0.15))


@sound("status_curse", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is cursed by the void")
def status_curse(rng, v):
    d = 0.7
    whisper = resonate(noise(d, rng, "pink"), sweep(1200, 500, d), 5) * env([(0, 0), (0.2, 1), (d, 0)], d) * 2
    return ring(whisper, 31) * 0.7 + whisper * 0.3


# Which death sound each enemy uses. Enemies not listed fall back by tag in the game (fast, armoured).
ENEMY_DEATHS = {
    "grunt": "death_grunt", "runner": "death_runner", "brute": "death_brute", "mender": "death_mender",
    "splitter": "death_splitter", "shardling": "death_shardling", "warded": "death_warded",
    "hollow_shade": "death_shade",
}


@sound("status_shatter", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy's armour cracks")
def status_shatter(rng, v):
    d = 0.4
    crack = mix(hp(noise(0.04, rng), 1500) * decay(0.04, 0.008) * 1.5,
                modal(0.3, [(rng.uniform(500, 700), 0.05, 1.0), (1400, 0.03, 0.5), (2900, 0.02, 0.3)], rng))
    return mix(crack, place(silence(d), debris(0.3, rng, 5, 0.9) * 0.5, 0.05))
