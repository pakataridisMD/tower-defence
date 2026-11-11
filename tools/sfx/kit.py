"""Recorded building blocks: cinematic hits, low brass, gongs, cymbals, scrapes and debris from real samples.

Everything here is cut from the CC0 VSCO 2 CE recordings (see samples.py), pitched and layered the way
film and game sound designers build impacts: a sub drop for weight, big drums for the body, a cymbal or
gong for the tail, and a found-sound layer (metal, glass, stone) for texture.
"""

from __future__ import annotations

import re

import numpy as np

from dsp import SR, decay, drive, env, hp, lp, mix, n_of, noise, osc, place, reverb, silence, stereo, sweep, svf
import samples as S
from samples import cut, load, semis, speed

P = "Percussion/"
V1 = "VSCO 1 Percussion/"
MISC = "Miscellania Raw/Misc 1/"

NOTE = {"C": 0, "C#": 1, "D": 2, "D#": 3, "E": 4, "F": 5, "F#": 6, "G": 7, "G#": 8, "A": 9, "A#": 10, "B": 11}
_NOTE_RE = re.compile(r"[_ ]([A-G]#?)(-?\d)[_.]")

BRASS = {
    "tuba": "Brass/Tuba/sus/*.wav",
    "tuba_stac": "Brass/Tuba/stac/*.wav",
    "trombone": "Brass/OldTrombone/Sustain/*.wav",
    "buzz": "Brass/OldTrombone/Buzz/*.wav",
    "fall": "Brass/OldTrombone/Fall/*.wav",
    "tenor": "Brass/Tenor Trombone/sus/*.wav",
    "horn": "Brass/F Horn/sus/*.wav",
    "horn_stac": "Brass/F Horn/stac/*.wav",
    "trumpet": "Brass/Trumpet/sus/*.wav",
    "trumpet_stac": "Brass/Trumpet/stac/*.wav",
    "cello_trem": "Strings/Cello Section/trem/*.wav",
    "bass_trem": "Strings/Solo Contrabass/Trem/*.wav",
    "violin_trem": "Strings/Violin Section/Trem/*.wav",
    "cello_spic": "Strings/Cello Section/spic/*.wav",
    "bass_spic": "Strings/Solo Contrabass/Spic/*.wav",
    "bass_pizz": "Strings/Solo Contrabass/Pizz/*.wav",
    "cello_pizz": "Strings/Cello Section/pizzT/*.wav",
    "cello": "Strings/Cello Section/susvib/*.wav",
}


def midi_of(name: str) -> int | None:
    m = _NOTE_RE.search(name)
    if not m:
        return None
    return NOTE[m.group(1)] + (int(m.group(2)) + 1) * 12


def note(kind: str, midi: float, rng: np.random.Generator | None = None, loud: bool = True) -> np.ndarray:
    """The recorded note of an instrument nearest to `midi`, repitched to it exactly."""
    found = [(midi_of(p.name), p) for p in S.files(BRASS[kind])]
    found = [(m, p) for m, p in found if m is not None]
    best = min(abs(m - midi) for m, _ in found)
    near = [p for m, p in found if abs(m - midi) == best]
    # Dynamic layers are named v1 (soft) upwards: take the loudest takes, or the softest.
    near.sort(key=lambda p: p.name)
    pool = near[len(near) // 2:] if loud else near[: max(1, len(near) // 2)]
    path = pool[int(rng.integers(len(pool)))] if rng is not None else pool[-1]
    x = S._read(str(path)).copy()
    m = midi_of(path.name)
    return semis(x, midi - m)


def held(kind: str, midi: float, seconds: float, rng=None, attack: float = 0.02, release: float = 0.3,
         loud: bool = True) -> np.ndarray:
    """A note held for `seconds` with a release; short samples are looped by crossfading takes."""
    x = note(kind, midi, rng, loud)
    need = n_of(seconds + release)
    while len(x) < need:
        y = note(kind, midi, rng, loud)
        xf = min(n_of(0.3), len(x) // 3, len(y) // 3)
        ramp = np.linspace(0, 1, xf)[:, None]
        x = np.concatenate([x[:-xf], x[-xf:] * (1 - ramp) + y[:xf] * ramp, y[xf:]])
    x = x[:need]
    e = env([(0, 0), (attack, 1), (seconds, 1), (seconds + release, 0)], seconds + release)
    return x * e[:, None]


def chord(kind: str, midis, seconds: float, rng=None, attack: float = 0.02, release: float = 0.3,
          loud: bool = True) -> np.ndarray:
    return mix(*[held(kind, m, seconds, rng, attack, release, loud) for m in midis])


def reverse(x: np.ndarray) -> np.ndarray:
    return x[::-1].copy()


def tail(x: np.ndarray, seconds: float, fade_out: float | None = None) -> np.ndarray:
    """Keeps the first `seconds` of a long ringing sample, fading out over the last part."""
    return cut(x, 0, seconds, fade_out if fade_out is not None else min(1.5, seconds * 0.5))


def sub(seconds: float, f0: float = 55.0, f1: float = 28.0, tau: float = 0.5) -> np.ndarray:
    """The sub-bass drop under every big hit (felt more than heard)."""
    body = osc(sweep(f0, f1, seconds, power=0.6), seconds) * decay(seconds, tau, 0.004)
    return drive(body * 1.5, 1.4)


# --- Percussion ---------------------------------------------------------------------------------

def timpani(rng, low: bool = True, st: float = 0.0) -> np.ndarray:
    pat = "Timpani/Timpani[12]_Hit_v4*" if low else "Timpani/Timpani[345]_Hit_v4*"
    try:
        x = load(P + pat, rng)
    except S.MissingSamples:
        x = load(P + "Timpani/Timpani*_Hit_v3*", rng)
    return semis(x, st)


def timpani_roll(rng, seconds: float, st: float = 0.0) -> np.ndarray:
    x = semis(load(P + "Timpani/Rolls/Timpani[12]_Roll_v5*", rng), st)
    return cut(x, 0, seconds, 0.4)


def bass_drum(rng, st: float = 0.0, loud: bool = True) -> np.ndarray:
    pat = V1 + "drums/bass/bdrum*_ff*" if loud else V1 + "drums/bass/bdrum*_p_*"
    return semis(load(pat, rng), st)


def concert_bass(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(P + "BDrumNewhit_v[67]*", rng), st)


def giant(rng, st: float = 0.0, kind: str = "mallet") -> np.ndarray:
    pat = {"mallet": "drums/other/ethnic/giant/mallet/*_ff_*",
           "sticks": "drums/other/ethnic/giant/sticks/*_f*",
           "hand": "drums/other/ethnic/giant/hand/*_ff_*",
           "soft": "drums/other/ethnic/giant/hand/*_p*"}[kind]
    return semis(load(V1 + pat, rng), st)


def crash(rng, st: float = 0.0, loud: bool = True) -> np.ndarray:
    pat = V1 + "varMetal/Cymbals/clash/crash_hit_fff*" if loud else V1 + "varMetal/Cymbals/clash/crash_hit_mp*"
    return semis(load(pat, rng), st)


def cymbal(rng, st: float = 0.0, mallet: str = "softmall_ff") -> np.ndarray:
    return semis(load(V1 + f"varMetal/Cymbals/susp/susp_hit_{mallet}*", rng), st)


def swell(seconds: float, rng, st: float = 0.0) -> np.ndarray:
    """A suspended-cymbal roll crescendo, trimmed so it peaks right at the end."""
    x = semis(load(P + "susCymb1-cresc-*", rng), st)
    lv = np.max(np.abs(x), axis=1)
    peak = int(np.argmax(lv))
    start = max(0, peak - n_of(seconds))
    y = x[start:peak + n_of(0.05)].copy()
    y *= np.linspace(0.2, 1, len(y))[:, None] ** 2
    return y


def reverse_crash(seconds: float, rng, st: float = 0.0) -> np.ndarray:
    """A crash played backwards, so it sucks up into the next hit."""
    x = reverse(cut(crash(rng, st), 0, seconds + 0.02, 0.0))
    return x[-n_of(seconds):]


def gong(rng, st: float = 0.0, soft: bool = False) -> np.ndarray:
    pat = "varMetal/Gong/gong_hit_mp*" if soft else "varMetal/Gong/gong_hit_ff*"
    return semis(load(V1 + pat, rng), st)


def tam_tam(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(P + "gongHit_fff*", rng), st)


def gong_roll(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(V1 + "varMetal/Gong/gong_roll_*_ff*", rng), st)


def gong_scrape(rng, st: float = 0.0) -> np.ndarray:
    pool = [V1 + "varMetal/Gong/gong_scrape_*", P + "gongscrape_*"]
    return semis(load(pool[int(rng.integers(2))], rng), st)


def bowed(rng, st: float = 0.0) -> np.ndarray:
    """A bowed cymbal: the eerie metallic singing under horror and magic sounds."""
    return semis(load(P + "susCymb1-bow-*", rng), st)


def scrape(rng, st: float = 0.0) -> np.ndarray:
    pool = [P + "susCymb1-scrape*", V1 + "varMetal/Cymbals/susp/susp_FX_scrape_[123]*"]
    return semis(load(pool[int(rng.integers(2))], rng), st)


def drum_rub(rng, st: float = 0.0) -> np.ndarray:
    """A hand rubbed across a bass drum skin: pitched down it is a growl, a groan or grinding stone."""
    return semis(load(P + "bassdrum_rub*", rng), st)


def snare(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(P + "Snare2-HitSN_v[45]*", rng), st)


def snare_roll(rng, seconds: float) -> np.ndarray:
    return cut(load(P + "Snare2-rollSN*", rng), 0, seconds, 0.2)


def toms(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(V1 + "drums/tenor/tenor_lower/*", rng), st)


def frame_drum(rng, st: float = 0.0) -> np.ndarray:
    return semis(load("Miscellania Raw/Misc 2/rtomtom_frame*", rng), st)


def timp_snare(rng, st: float = 0.0) -> np.ndarray:
    """Timpani and snare struck together: a tight cinematic hit."""
    return semis(load(MISC + "timpsnare_*f*", rng), st)


def metal(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(MISC + "metal_hit*", rng), st)


def anvil(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(P + "Anvil_Hit1_v3*", rng), st)


def brake(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(P + "BrakeDrum1_Hammer_v3*", rng), st)


def glass(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(MISC + "glass_break*", rng), st)


def chain(rng, seconds: float, st: float = 0.0) -> np.ndarray:
    x = semis(load(MISC + "chain*", rng), st)
    start = rng.uniform(0, max(0.0, len(x) / SR - seconds - 0.1))
    return cut(x, start, seconds, 0.1)


def brick(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(MISC + "brick_scrape*", rng), st)


def bubbles(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(MISC + "bubbles*", rng), st)


def zap(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(MISC + "zap*", rng), st)


def alien(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(MISC + "alien*", rng), st)


def ratchet(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(P + "Ratchet1-*", rng), st)


def guiro(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(V1 + "varWood/guiro_long*", rng), st)


def log_drum(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(V1 + "varWood/log_drum/*", rng), st)


def shaker(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(V1 + "varMetal/various/cabasa_[0-9]*", rng), st)


def tambourine(rng, st: float = 0.0) -> np.ndarray:
    return semis(load("Miscellania Raw/Misc 2/tamb3_[1-8]*", rng), st)


def flexatone(rng, st: float = 0.0) -> np.ndarray:
    return semis(load(V1 + "varMetal/various/flexatone*", rng), st)


def claves(rng, st: float = 0.0, soft: bool = False) -> np.ndarray:
    pat = V1 + "varWood/claves_mp*" if soft else V1 + "varWood/claves_mf*"
    return semis(load(pat, rng), st)


# --- Composite hits -------------------------------------------------------------------------------

def impact(rng, size: float = 1.0, metal_level: float = 0.0, crash_level: float = 0.6,
           gong_level: float = 0.0, st: float = 0.0) -> np.ndarray:
    """A cinematic impact: sub drop, giant drum, concert bass drum, low timpani, crash tail."""
    down = st - 5 * size
    parts = [
        sub(1.2 + size, 62 - 10 * size, 26, 0.35 + 0.25 * size) * 0.55,
        giant(rng, down) * 0.9,
        concert_bass(rng, down - 2) * 0.8,
        timpani(rng, True, st - 2 * size) * 0.55,
        timp_snare(rng, st - 3) * 0.35,
    ]
    if crash_level:
        parts.append(hp(crash(rng, st - 2 - 2 * size), 250) * crash_level * 0.5)
    if gong_level:
        parts.append(tam_tam(rng, st - 4 - 3 * size) * gong_level * 0.6)
    if metal_level:
        parts.append(metal(rng, st - 5 * size) * metal_level * 0.6)
    return mix(*parts)


def braam(midi: float, seconds: float, rng, dark: float = 1.0) -> np.ndarray:
    """The low brass blast of film trailers, from real tuba, trombones and horns in octaves."""
    layers = [
        held("tuba", midi, seconds, rng, 0.02, 0.6) * 1.0,
        held("trombone", midi + 12, seconds, rng, 0.02, 0.6) * 0.8,
        held("buzz", midi + 12, seconds, rng, 0.01, 0.4) * 0.5,
        held("tenor", midi + 7, seconds, rng, 0.03, 0.6) * 0.5,
        held("horn", midi + 24, seconds, rng, 0.05, 0.6) * 0.4 * (1.2 - dark * 0.4),
    ]
    out = mix(*layers)
    out = drive(out * 1.6, 1.8)
    return lp(out, 2500 + 2500 * (1 - dark))


def riser(seconds: float, rng, st: float = 0.0) -> np.ndarray:
    """A swell into a hit: cymbal roll crescendo and a reversed crash, tightening upwards."""
    return mix(swell(seconds, rng, st) * 0.8, reverse_crash(seconds, rng, st - 4) * 0.7)


def debris(rng, seconds: float, count: int = 10, st: float = 0.0) -> np.ndarray:
    """Stones and rubble settling: cut-up brick scrapes, log drum knocks and pitched-down glass."""
    out = silence(seconds)
    for i in range(count):
        t = rng.uniform(0, seconds * 0.7) * (i / max(1, count - 1)) ** 0.5
        pick = rng.integers(3)
        if pick == 0:
            g = cut(brick(rng, st + rng.uniform(-6, 0)), rng.uniform(0, 0.3), 0.25, 0.08)
        elif pick == 1:
            g = log_drum(rng, st - rng.uniform(4, 10)) * 0.6
        else:
            g = cut(claves(rng, st - rng.uniform(10, 18), soft=True), 0, 0.2, 0.05) * 0.7
        out = place(out, g, t, rng.uniform(0.2, 0.6) * (1 - 0.6 * i / count))
    return out[: n_of(seconds) + n_of(0.5)]


def water_rush(seconds: float, rng, bright: float = 1.0) -> np.ndarray:
    """A wave or a column of water: filtered noise surf under recorded bubbles."""
    surf = svf(noise(seconds, rng, "pink"), sweep(600, 3500 * bright, seconds, power=0.5), 0.7, "low")
    surf *= env([(0, 0), (seconds * 0.3, 1), (seconds, 0)], seconds)
    return mix(stereo(surf * 1.2, 0.9, rng=rng), place(silence(seconds), bubbles(rng, -3) * 0.5, seconds * 0.2))


def hall(x: np.ndarray, seconds: float = 2.6, wet: float = 0.3, rng=None) -> np.ndarray:
    return reverb(stereo(x, 0.6, rng=rng), seconds, wet, damp=6000, rng=rng, wide=True)
