"""Tower attacks (one sound per tower, built from its elements and how it fights), impacts,
explosions, enemy deaths and other enemy events."""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from dsp import SR, crackle, decay, env, hp, lp, mix, n_of, noise, place, reverb, silence, svf, sweep, whoosh
import creature as C
from creature import Voice
import kit
from kit import cut, tail
from registry import register, sound
from samples import mono
from .palette import ATTACKS, IMPACTS, _grain, _short, attack_storm, pitch, reverse

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
        parts.append(_short(kit.giant(rng, -4 if size == 2 else -7, "hand"), 0.4) * (0.35 if size == 2 else 0.6))
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
        d = 0.8 + size * 0.7
        out = tail(kit.impact(rng, size * 0.7, crash_level=0.25 * size), d)
        out = mix(out, kit.debris(rng, d, int(4 + size * 6), 0) * 0.5)
        return reverb(out, 0.5 + size * 0.4, 0.15, 5000, rng=rng)
    return make


for _name, _size, _loud in (("explosion_small", 0.6, -20.0), ("explosion_medium", 1.0, -18.0), ("explosion_large", 1.5, -16.0)):
    register(_name, "impacts", _explosion(_size), variants=3, loud=_loud, volume_db=-5.0, max_voices=3,
             min_gap=0.08, pitch_jitter=0.06, priority=2, description=f"splash shot explodes ({_name.split('_')[1]})")


@sound("hit_armour", "impacts", variants=3, loud=-24.0, volume_db=-6.0, max_voices=2, min_gap=0.07, pitch_jitter=0.1,
       description="a shot glances off heavy armour")
def hit_armour(rng, v):
    src = [kit.metal, kit.anvil, kit.brake][v](rng, rng.uniform(-3, 3))
    clang = _short(src, 0.3)
    tick = hp(noise(0.02, rng), 3000) * decay(0.02, 0.003)
    return place(clang, tick, 0.0)


# --- Enemy deaths ------------------------------------------------------------------------
# Short cries are spoken with Kokoro and pushed into small creature voices (see creature.py).

GRUNT = Voice("am_michael", 1.0, depth=-3, sub=0.2, grit=0.45, growl=0.3, room=0.6, wet=0.1)
RUNNER = Voice("am_puck", 1.1, depth=3, sub=0.0, grit=0.35, growl=0.1, room=0.5, wet=0.1)
BRUTE = Voice("am_onyx", 0.9, depth=-6, sub=0.45, grit=0.5, growl=0.45, room=0.8, wet=0.12, roar_depth=-4)
MENDER = Voice("af_heart", 0.9, depth=0, formant=True, sub=0.0, whisper=0.4, grit=0.0, room=1.2, wet=0.25)
SHADE = Voice("af_nicole", 0.8, depth=-2, formant=True, sub=0.0, up=0.3, whisper=0.6, chorus=2, grit=0.0,
              room=2.2, wet=0.45)


def _cry(voice: Voice, word: str, rng, shout: bool = True) -> np.ndarray:
    return C.speech(word, voice, rng, shout=shout)


def body_fall(rng, weight: float = 1.0, d: float = 0.5) -> np.ndarray:
    thud = _short(kit.giant(rng, -2 - 4 * weight, "hand"), d) * weight
    dust = lp(noise(d, rng, "brown"), 400) * decay(d, 0.05) * 0.4 * weight
    return mix(thud, dust)


@sound("death_grunt", "enemies", variants=3, loud=-22.0, volume_db=-4.0, max_voices=3, min_gap=0.05, pitch_jitter=0.08,
       description="a grunt dies")
def death_grunt(rng, v):
    yell = _cry(GRUNT, ["Ugh!", "Argh!", "Hurk!"][v], rng)
    return place(yell, body_fall(rng, 0.7), min(0.3, len(yell) / SR * 0.6))


@sound("death_runner", "enemies", variants=3, loud=-23.0, volume_db=-4.0, max_voices=3, min_gap=0.05, pitch_jitter=0.1,
       description="a fast runner dies")
def death_runner(rng, v):
    yelp = _cry(RUNNER, ["Yip!", "Eek!", "Yah!"][v], rng)
    skid = whoosh(0.25, rng, 3000, 900, 2.0, [(0, 1), (0.25, 0)]) * 0.4
    return mix(yelp, place(silence(0.5), mix(skid, body_fall(rng, 0.4, 0.3)), 0.15))


@sound("death_brute", "enemies", variants=3, loud=-20.0, volume_db=-3.0, max_voices=2, min_gap=0.08, pitch_jitter=0.06,
       description="a brute falls")
def death_brute(rng, v):
    groan = C.roar(BRUTE, rng, ["Hhuuurgh!", "Graaagh!", "Oooough!"][v], 0.8, -4, 0.8)
    fall = mix(_short(kit.giant(rng, -8), 0.8) * 1.2, mono(kit.debris(rng, 0.7, 4, -3)) * 0.4)
    return place(groan, fall, 0.45)


@sound("death_mender", "enemies", variants=3, loud=-23.0, volume_db=-4.0, max_voices=2, min_gap=0.06, pitch_jitter=0.08,
       description="a mender's healing light goes out")
def death_mender(rng, v):
    gasp = _cry(MENDER, ["Ahh...", "Oh...", "Haa..."][v], rng, shout=False)
    light = reverse(_short(kit.bowed(rng, 3 + v), 0.6)) * 0.4
    return mix(gasp, place(silence(0.9), _short(kit.bowed(rng, 5), 0.7) * 0.25, 0.1), light)


@sound("death_splitter", "enemies", variants=3, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.06, pitch_jitter=0.08,
       description="a splitter bursts into shardlings")
def death_splitter(rng, v):
    squelch = svf(noise(0.3, rng), sweep(3000, 300, 0.3), 3, "band") * decay(0.3, 0.08) * 2.0
    gloop = _grain(kit.bubbles(rng, -4), rng, 0.3, 0.003, 1.0) * 0.7
    shards = _short(kit.glass(rng, rng.uniform(2, 6)), 0.4) * 0.45
    return mix(squelch, gloop, place(silence(0.5), shards, 0.04))


@sound("death_shardling", "enemies", variants=3, loud=-24.0, volume_db=-4.0, max_voices=3, min_gap=0.04, pitch_jitter=0.12,
       description="a shardling shatters like glass")
def death_shardling(rng, v):
    return _short(kit.glass(rng, rng.uniform(3, 9)), 0.5)


@sound("death_warded", "enemies", variants=3, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.06, pitch_jitter=0.06,
       description="a warded enemy's shield breaks")
def death_warded(rng, v):
    shield = _short(kit.cymbal(rng, 2, "hardmall_f"), 0.6) * env([(0, 1), (0.08, 1), (0.1, 0.25), (0.6, 0)], 0.6)
    shatter = _short(kit.glass(rng, 0), 0.5) * 0.8
    return mix(shield, place(silence(0.1), shatter, 0.06), place(silence(0.2), body_fall(rng, 0.6), 0.2))


@sound("death_shade", "enemies", variants=3, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.08, pitch_jitter=0.06,
       description="a hollow shade dissolves with a wail")
def death_shade(rng, v):
    wail = _cry(SHADE, ["Ooooh...", "Haaaa...", "Nooo..."][v], rng, shout=False)
    wail = C.glide(wail, 0, -5, 1.4)
    return mix(wail, reverse(_short(kit.cymbal(rng, -3), 0.4)) * 0.4)


@sound("enemy_split", "enemies", variants=2, loud=-21.0, volume_db=-3.0, max_voices=2, min_gap=0.1,
       description="an enemy breaks into smaller ones")
def enemy_split(rng, v):
    tear = svf(noise(0.35, rng), sweep(400, 2500, 0.35), 4, "band") * env([(0, 0), (0.25, 1), (0.35, 0)], 0.35) * 2
    pops = _grain(kit.bubbles(rng, 2), rng, 0.3, 0.003, 1.0) * 0.7
    return mix(tear, place(silence(0.6), pops, 0.28))


@sound("enemy_summon", "enemies", variants=2, loud=-19.0, volume_db=-2.0, max_voices=2, min_gap=0.4, priority=2,
       description="a boss calls up more enemies")
def enemy_summon(rng, v):
    d = 1.6
    portal = reverse(tail(kit.tam_tam(rng, -8), 0.75, 0.0)) * 0.8
    hum = mono(tail(kit.bowed(rng, -5), 1.4)) * env([(0, 0), (0.6, 1), (1.4, 0)], 1.4) * 0.5
    arrive = _short(kit.giant(rng, -5), 0.8)
    return reverb(mix(place(silence(d), portal, 0.0), hum, place(silence(d), arrive, 0.72)), 1.2, 0.3, rng=rng)


@sound("status_burn", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy catches fire")
def status_burn(rng, v):
    d = 0.5
    roar = _grain(lp(kit.gong_roll(rng, -12), 2500), rng, d, 0.02, 4.0) * env([(0, 0), (0.05, 1), (d, 0)], d)
    return mix(whoosh(d, rng, 400, 1800, 1.0, [(0, 0), (0.05, 1), (d, 0)]) * 0.7, roar,
               crackle(d, rng, 150, 2500) * decay(d, 0.2) * 0.8)


@sound("status_freeze", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is slowed by water and frost")
def status_freeze(rng, v):
    d = 0.6
    ice = hp(_short(kit.glass(rng, 8 + 3 * v), 0.4), 2000) * 0.6
    crackling = hp(crackle(d, rng, 200, 6000), 4000) * decay(d, 0.2)
    return mix(place(silence(d), ice, 0.02), crackling)


@sound("status_poison", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is poisoned")
def status_poison(rng, v):
    d = 0.6
    return mix(_grain(kit.bubbles(rng, -6), rng, d, 0.01, 1.5), svf(noise(d, rng), 600, 3, "band") * decay(d, 0.2) * 0.6)


@sound("status_stun", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is stunned")
def status_stun(rng, v):
    ring_ = hp(_short(kit.cymbal(rng, 5, "metal_2_mf"), 0.5), 1500) * 0.4
    return mix(attack_storm(rng, 0.6, 0.18), ring_)


@sound("status_curse", "enemies", variants=2, loud=-26.0, volume_db=-8.0, max_voices=1, min_gap=0.35, pitch_jitter=0.1,
       description="an enemy is cursed by the void")
def status_curse(rng, v):
    words = C.speech(["Hush.", "Be still."][v], SHADE, rng)
    whisper = C.whisper_of(words, rng)
    return mix(whisper * 0.9, reverse(_short(kit.cymbal(rng, -5), 0.4)) * 0.4)


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
    crack = mix(hp(noise(0.04, rng), 1500) * decay(0.04, 0.008) * 1.5, _short(kit.glass(rng, -3), 0.3) * 0.6)
    return mix(crack, place(silence(d), _grain(kit.brick(rng, 0), rng, 0.25, 0.003, 0.3) * 0.5, 0.05))
