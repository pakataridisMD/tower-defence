"""Boss sounds: a reveal, footsteps, speech, an enrage and a death for every boss.

Built from recordings (see kit.py, creature.py, samples.py): real orchestral hits, low brass, gongs and
found sounds for the body, and spoken lines processed into monstrous voices. Each boss says lines that
fit the lore (docs/story/bible.md and data/story/characters.json on the lore branch): the Heralds, the
Ashen Regent, the Sundered Heart and the High King Vael-Orrun speak; the Leviathan and the Broodmother
are beasts and only roar. The corrupted Wardens are freed when beaten, so their deaths end in release.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from dsp import SR, decay, env, hp, lp, mix, n_of, noise, place, silence, stereo, sweep, whoosh
import creature as C
from creature import Voice
import kit
import samples as S
from kit import cut, tail
from registry import register, sound
from .textures import bed, burst, fire_crackle, thunder, wind


@dataclass
class BossSet:
    title: str
    element: str          # fire storm nature water earth void, or cosmos for Vael-Orrun
    voice: Voice
    step: str             # footstep style
    enemies: tuple[str, ...]
    lines: dict = field(default_factory=dict)   # reveal, talk (3), enrage, death
    root: int = 31        # midi note of the reveal's low brass
    size: float = 1.0     # how big the hits are
    freed: bool = False   # a Warden: beating it frees it


def _lines(reveal, talk, enrage, death):
    return {"reveal": reveal, "talk": talk, "enrage": enrage, "death": death}


SETS: dict[str, BossSet] = {
    "saltmother": BossSet(
        "Saltmother Ourra, the Drowned Herald", "water",
        Voice("bf_isabella:0.6,af_bella:0.4", 0.82, depth=-3, sub=0.3, whisper=0.35, chorus=2, grit=0.1, growl=0.12,
              room=3.4, wet=0.36, roar_word="Haaaaaaah!"),
        "slosh", ("saltmother",),
        _lines("The sea has come for you.",
               ["The tide remembers.", "Come down to the deep, little ones.", "All shores drown in the end."],
               "You will drown!", "The tide... goes out."),
        root=30),
    "gorrath": BossSet(
        "Gorrath the Quarried, the Stone Herald", "earth",
        Voice("am_onyx", 0.8, depth=-6, sub=0.5, grit=0.4, growl=0.35, room=2.6),
        "boulder", ("gorrath",),
        _lines("I carved out my own heart. Yours is next.",
               ["Stone does not bleed.", "Break against me.", "Grind them to dust!"],
               "Crush them!", "Stone... returns to stone."),
        root=28, size=1.3),
    "pale_vesper": BossSet(
        "The Pale Vesper, the Hollow Herald", "void",
        Voice("af_nicole:0.5,bf_emma:0.5", 0.8, depth=-1, formant=True, sub=0.0, up=0.3, whisper=0.6, chorus=3,
              grit=0.0, room=4.6, wet=0.45, roar_depth=-4, roar_word="Aaaaaaaah!"),
        "ghost", ("pale_vesper",),
        _lines("Wake, my sleeping ones. Wake.",
               ["Hush now. Sing with me.", "The dead are listening.", "Rise, and walk with me."],
               "Rise! All of you, rise!", "Let them... rest."),
        root=34),
    "ashwick": BossSet(
        "Ashwick the Kindled, the Flame Herald", "fire",
        Voice("am_puck", 1.12, depth=1.5, sub=0.0, grit=0.35, growl=0.05, room=1.6, wet=0.22, roar_depth=-5,
              roar_word="Haaaaaaa!"),
        "run", ("ashwick",),
        _lines("Too slow! You are all too slow!",
               ["Can't catch me!", "Burn, burn, burn!", "Faster! Faster!"],
               "I'll burn it all!", "So... cold..."),
        root=33, size=0.8),
    "vholt": BossSet(
        "Vholt Stormcrown, the Sky Herald", "storm",
        Voice("bm_george", 0.82, depth=-3, sub=0.35, grit=0.2, growl=0.1, room=3.4, wet=0.33),
        "wings", ("vholt",),
        _lines("Kneel before the storm.",
               ["The sky does not forgive.", "I taught her everything. Not this.", "Feel the wind turn."],
               "Feel the thunder!", "The sky... is quiet, at last."),
        root=31),
    "mother_briar": BossSet(
        "Mother Briar, the Thorn Herald", "nature",
        Voice("af_sarah:0.5,bf_lily:0.5", 0.8, depth=-2.5, sub=0.15, whisper=0.4, chorus=2, grit=0.15, growl=0.22,
              room=2.2, wet=0.3, roar_word="Haaaaaaagh!"),
        "roots", ("mother_briar",),
        _lines("Shh. The thorns will hold you.",
               ["Let me heal you... forever.", "Grow, my darlings. Grow.", "Every wound becomes a root."],
               "Tear them apart!", "Bloom... again."),
        root=32),
    "ashen_regent": BossSet(
        "Cassivane Dral, the Ashen Regent", "fire",
        Voice("bm_lewis:0.6,bm_george:0.4", 0.85, depth=-2, sub=0.25, grit=0.12, growl=0.0, room=3.0, wet=0.3),
        "armour", ("ashen_regent",),
        _lines("Stand aside, or turn to ash.",
               ["Ilyra, I am so close.", "Everything I burn, I burn for her.", "You cannot stop what love began."],
               "You will not take her from me!", "Ilyra... forgive me."),
        root=29, size=1.1),
    "sundered_heart": BossSet(
        "The Sundered Heart", "void",
        Voice("bm_lewis:0.5,am_onyx:0.5", 0.8, depth=-5, sub=0.6, whisper=0.4, chorus=3, grit=0.35, growl=0.4,
              room=3.6, wet=0.36),
        "heart", ("sundered_heart",),
        _lines("We are one now.",
               ["The Crack is open.", "Her heart beats in mine.", "There is no Regent. Only the Heart."],
               "We will not fall!", "Daughter..."),
        root=27, size=1.4),
    "vael_orrun": BossSet(
        "Vael-Orrun, the Sunderer", "cosmos",
        Voice("am_onyx:0.5,bm_george:0.5", 0.75, depth=-7, sub=0.6, whisper=0.5, chorus=3, grit=0.2, growl=0.15,
              room=4.8, wet=0.4),
        "colossus", ("vael_orrun",),
        _lines("Kneel. Your king has returned.",
               ["This was my city. This is my crown.", "Six crowns. One king.", "I have waited two thousand years."],
               "I am the High King!", "The crown... was always... mine."),
        root=26, size=1.6),
    "warden": BossSet(
        "A corrupted Warden", "earth",
        Voice("am_fenrir", 0.8, depth=-6, sub=0.45, whisper=0.45, grit=0.3, growl=0.3, room=2.8),
        "armour", ("warden",),
        _lines("He whispers. I obey.", ["Burn the Ring.", "Wake, and destroy.", "The High King calls."],
               "Destroy them!", "Free... at last."),
        root=29, freed=True),
    # The corrupted Wardens of each element campaign. Vael-Orrun's whisper doubles their voices.
    "fire": BossSet(
        "Fire Warden (Cinder Tyrant)", "fire",
        Voice("am_onyx", 0.78, depth=-8, sub=0.5, whisper=0.3, grit=0.5, growl=0.5, room=2.6),
        "stomp_fire", ("cinder_tyrant",),
        _lines("The mountain wakes!", ["Burn.", "Ash. All of it, ash.", "The fire hungers."],
               "Burn!", "The fire... is mine again."),
        root=28, size=1.3, freed=True),
    "storm": BossSet(
        "Storm Warden (Thunderhead)", "storm",
        Voice("bm_george:0.5,am_fenrir:0.5", 0.8, depth=-6, sub=0.45, whisper=0.3, grit=0.3, growl=0.25, room=3.4),
        "thunder", ("thunderhead",),
        _lines("The storm stands still.", ["Thunder obeys him.", "Fall.", "No wind. No mercy."],
               "Fall!", "The wind... moves again."),
        root=30, size=1.2, freed=True),
    "nature": BossSet(
        "Nature Warden (Broodmother)", "nature",
        Voice("af_kore", 1.0, depth=3, sub=0.2, whisper=0.6, chorus=3, grit=0.5, growl=0.6, room=2.0,
              roar_depth=-9, roar_word="Kshaaaaaaa!", beast=True),
        "skitter", ("broodmother",),
        _lines("", [], "", ""),
        root=32, freed=True),
    "water": BossSet(
        "Water Warden (Leviathan)", "water",
        Voice("am_onyx", 0.7, depth=-10, sub=0.6, grit=0.15, growl=0.15, room=4.5, wet=0.45, roar_depth=-6,
              roar_word="Ooooooooooh!", beast=True),
        "slosh", ("leviathan",),
        _lines("", [], "", ""),
        root=26, size=1.4, freed=True),
    "earth": BossSet(
        "Earth Warden (Mountain Titan)", "earth",
        Voice("am_onyx", 0.7, depth=-10, sub=0.6, grit=0.45, growl=0.4, room=3.0),
        "boulder", ("mountain_titan",),
        _lines("I am the mountain.", ["Fall beneath me.", "Crush.", "The ground is mine."],
               "Crush!", "The stone... sleeps."),
        root=26, size=1.5, freed=True),
    "void": BossSet(
        "Void Warden (Hollow King)", "void",
        Voice("am_onyx:0.5,am_fenrir:0.5", 0.75, depth=-6, sub=0.45, whisper=0.7, chorus=2, grit=0.25, growl=0.3,
              room=4.0, wet=0.4),
        "drag", ("hollow_king",),
        _lines("The Hollow hungers.", ["Come into the dark.", "Nothing remains.", "Hush. Be empty."],
               "Nothing will remain!", "I see... the light."),
        root=27, size=1.2, freed=True),
}

REVEAL = dict(positional=False, priority=8)
LEAD = 0.9   # seconds of swell before a reveal's hit


def _room(x, bs: BossSet, rng, scale=1.0):
    return C.room(x, bs.voice, rng, scale)


def _say(bs: BossSet, text: str, rng, shout: bool = False) -> np.ndarray:
    return C.speech(text, bs.voice, rng, shout)


def _roar(bs: BossSet, rng, length=1.0, fall=-3.0, intensity=1.0, word=None) -> np.ndarray:
    v = bs.voice
    if bs.step == "skitter":
        # The Broodmother: an insect shriek over chittering mandibles.
        cry = C.roar(v, rng, word or v.roar_word, length, fall + 2, intensity)
        chit = silence(len(cry) / SR)
        for i in range(int(len(cry) / SR * 28)):
            chit = place(chit, cut(kit.claves(rng, rng.uniform(2, 9), True), 0, 0.05, 0.02), i / 28 + rng.uniform(0, 0.01),
                         rng.uniform(0.15, 0.4))
        e = C.follow(cry, 8)
        chit = S.mono(chit)[:len(e)]
        return mix(cry, chit * e[:len(chit)])
    if bs.element == "water" and v.beast:
        # The Leviathan: a whale-deep moan that bends down, under a contrabass tremolo.
        moan = C.roar(v, rng, word or v.roar_word, length * 1.3, fall - 2, intensity * 0.8)
        moan = C.glide(moan, 1.5, -2.5, 0.8)
        trem = S.mono(kit.held("bass_trem", 28, len(moan) / SR, rng, 0.3, 0.4)) * 0.35
        return mix(moan, trem)
    return C.roar(v, rng, word, length, fall, intensity)


def _shout(bs: BossSet, rng) -> np.ndarray:
    if bs.voice.beast or not bs.lines["enrage"]:
        return _roar(bs, rng, 1.3, -4, 1.4)
    return _say(bs, bs.lines["enrage"], rng, shout=True)


# --- Footsteps ----------------------------------------------------------------------------

def step(style: str, rng) -> np.ndarray:
    if style == "boulder":
        return mix(tail(kit.giant(rng, -10), 0.9) * 1.0, tail(kit.concert_bass(rng, -9), 0.9) * 0.7,
                   kit.debris(rng, 0.8, 5, -6) * 0.5)
    if style == "slosh":
        return mix(tail(kit.giant(rng, -6, "hand"), 0.7) * 0.7, burst("water", rng) * 0.45)
    if style == "ghost":
        breath = kit.reverse(tail(kit.bowed(rng, -3 + rng.uniform(-1, 1)), 0.9, 0.3))
        sigh = hp(noise(0.9, rng, "pink"), 1200) * env([(0, 0), (0.6, 1), (0.9, 0)], 0.9) * 0.3
        return mix(breath, sigh)
    if style == "run":
        out = silence(0.55)
        for i in range(2):
            out = place(out, tail(kit.frame_drum(rng, -2), 0.25) * 0.8, i * 0.17 + rng.uniform(0, 0.02))
        flame = whoosh(0.5, rng, 500, 2200, 1.0) * 0.5
        return mix(out, stereo(mix(flame, fire_crackle(0.5, rng, 1.5) * decay(0.5, 0.2) * 0.6), 0.6, rng=rng))
    if style == "wings":
        flap = whoosh(0.6, rng, 110, 600, 0.9, [(0, 0), (0.18, 1), (0.6, 0)]) * 1.6
        return mix(stereo(flap, 0.7, rng=rng), cut(thunder(rng, 1.2), 0, 1.2, 0.6) * rng.uniform(0.15, 0.4))
    if style == "roots":
        creak = cut(kit.guiro(rng, -9 - rng.uniform(0, 4)), 0, 0.6, 0.2) * 0.6
        return mix(tail(kit.log_drum(rng, -10), 0.4) * 0.8, creak, cut(kit.brick(rng, -9), 0, 0.5, 0.2) * 0.5,
                   tail(kit.giant(rng, -6, "soft"), 0.6) * 0.6)
    if style == "armour":
        clank = cut(kit.metal(rng, -5 - rng.uniform(0, 3)), 0, 0.5, 0.25) * 0.45
        return mix(tail(kit.giant(rng, -4, "hand"), 0.5) * 0.8, place(silence(0.6), clank, 0.01),
                   kit.chain(rng, 0.4, -2) * 0.35)
    if style == "heart":
        lub = tail(kit.bass_drum(rng, -3, False), 0.5)
        dub = tail(kit.bass_drum(rng, -5, False), 0.5) * 0.75
        return mix(place(silence(0.8), lub, 0.0), place(silence(0.8), dub, 0.22),
                   kit.sub(0.6, 60, 40, 0.15) * 0.4)
    if style == "colossus":
        return mix(tail(kit.impact(rng, 1.4, crash_level=0.0), 1.6), kit.debris(rng, 1.4, 8, -6) * 0.5,
                   tail(kit.bowed(rng, -12), 1.4) * 0.15)
    if style == "stomp_fire":
        return mix(tail(kit.giant(rng, -8), 0.9), tail(kit.concert_bass(rng, -7), 0.9) * 0.6,
                   stereo(fire_crackle(0.8, rng, 2) * decay(0.8, 0.3), 0.7, rng=rng) * 0.5)
    if style == "thunder":
        return mix(tail(kit.giant(rng, -7), 0.9), cut(thunder(rng, 1.2), 0, 1.2, 0.5) * 0.5)
    if style == "skitter":
        out = silence(0.7)
        for i in range(12):
            out = place(out, cut(kit.claves(rng, rng.uniform(-4, 4), True), 0, 0.06, 0.02) * rng.uniform(0.3, 0.8),
                        i * 0.045 + rng.uniform(0, 0.012))
        return mix(out, tail(kit.giant(rng, -4, "soft"), 0.5) * 0.6, cut(kit.shaker(rng, -4), 0, 0.5, 0.2) * 0.3)
    if style == "drag":
        return mix(tail(kit.giant(rng, -7, "hand"), 0.7) * 0.7, cut(kit.gong_scrape(rng, -10), 0.2, 0.9, 0.4) * 0.6,
                   kit.chain(rng, 0.8, -6) * 0.4)
    raise ValueError(style)


# --- Reveal, speech, enrage, death -------------------------------------------------------------------

def _hit(bs: BossSet, rng, seconds: float = 3.5) -> np.ndarray:
    size = bs.size
    metal = 0.6 if bs.step in ("armour", "colossus") else 0.0
    core = tail(kit.impact(rng, size, metal_level=metal, gong_level=0.6 if bs.element in ("void", "cosmos") else 0.3),
                seconds + 1.0)
    brass = kit.braam(bs.root, 1.6 + 0.4 * size, rng, dark=0.8)
    return mix(core, brass * 0.5, bed(bs.element, seconds, rng) * 0.6)


def reveal(bs: BossSet, rng) -> np.ndarray:
    lead = kit.riser(LEAD, rng, -2)
    out = place(silence(6.0), lead * 0.7, 0.0)
    out = place(out, _hit(bs, rng, 4.0), LEAD)
    if bs.key == "pale_vesper":
        hum = S.choir([(50, 0, 3.0, 90), (53, 0.2, 2.8, 80), (56, 0.4, 2.6, 80), (61, 0.6, 2.4, 70)], S.VOICE_OOHS)
        out = place(out, tail(hum, 4.0) * 0.5, LEAD + 0.1)
        cry = _roar(bs, rng, 1.4, -1, 0.6)
    elif bs.element == "cosmos":
        # The six crowns struck one after another, then the High King's voice.
        for i, e in enumerate(("fire", "storm", "nature", "water", "earth", "void")):
            out = place(out, burst(e, rng) * 0.35, LEAD + 0.25 + i * 0.12)
        cry = None
    else:
        cry = _roar(bs, rng, 1.2, -3, 1.1)
    if cry is not None:
        out = place(out, cry * 0.9, LEAD + 0.15)
    line = bs.lines["reveal"]
    if line and not bs.voice.beast:
        at = LEAD + (0.4 if cry is None else 0.15 + len(cry) / SR - 0.2)
        out = place(out, _say(bs, line, rng) * 1.05, at)
    return _room(out, bs, rng)


def voice_line(bs: BossSet, rng, v: int) -> np.ndarray:
    if bs.voice.beast or not bs.lines["talk"]:
        return _room(_roar(bs, rng, [0.9, 1.3, 0.7][v % 3], [-2, -4, 1][v % 3], [0.8, 1.0, 0.6][v % 3]), bs, rng)
    x = _say(bs, bs.lines["talk"][v % 3], rng)
    if bs.key == "pale_vesper":
        hum = S.choir([(49 + 2 * v, 0, 2.2, 70), (56 + v, 0.15, 2.0, 60)], S.VOICE_OOHS)
        x = mix(x, S.mono(tail(hum, len(x) / SR + 0.4)) * 0.25)
    if bs.element == "cosmos" or bs.freed:
        # Vael-Orrun's whisper under the words.
        x = mix(x, place(silence(0.1), C.whisper_of(x, rng) * 0.25, 0.06))
    return _room(x, bs, rng)


def enrage(bs: BossSet, rng) -> np.ndarray:
    out = silence(3.0)
    out = place(out, tail(kit.impact(rng, bs.size * 0.8, crash_level=0.8), 2.6) * 0.8, 0.0)
    out = place(out, burst(bs.element, rng) * 0.6, 0.05)
    out = place(out, _shout(bs, rng), 0.12)
    if not bs.voice.beast and bs.lines["enrage"]:
        out = place(out, _roar(bs, rng, 0.8, -3, 1.3) * 0.6, len(out) / SR - 1.2)
    return _room(out, bs, rng, 0.9)


def death(bs: BossSet, rng) -> np.ndarray:
    d = 7.0
    out = silence(d)
    cry = _roar(bs, rng, 1.6, -7, 1.4)
    out = place(out, cry, 0.0)
    at = len(cry) / SR * 0.7
    if not bs.voice.beast and bs.lines["death"]:
        out = place(out, _say(bs, bs.lines["death"], rng) * 1.0, at)
        at += 0.5
    fall = mix(tail(kit.impact(rng, bs.size * 1.2, gong_level=0.7, crash_level=0.8), 4.0),
               kit.debris(rng, 3.0, 14, -4) * 0.6)
    out = place(out, fall, at)
    out = place(out, _death_layer(bs, rng), at + 0.1)
    if bs.freed:
        # The madness lifts: a warm choir chord in a major key, rising out of the dust.
        ah = S.choir([(48, 0, 3.0, 70), (55, 0.1, 2.9, 70), (64, 0.25, 2.75, 75), (67, 0.4, 2.6, 70)])
        out = place(out, tail(ah, 3.5) * 0.45, at + 1.2)
    return _room(out, bs, rng, 1.2)


def _death_layer(bs: BossSet, rng) -> np.ndarray:
    key = bs.key
    if key == "saltmother":
        # Her column of black seawater falls.
        return mix(kit.water_rush(3.5, rng, 1.0) * 1.2, place(silence(4.0), kit.bubbles(rng, -5) * 0.6, 1.5))
    if key == "gorrath":
        # He breaks into walking boulders.
        out = silence(3.5)
        for i in range(3):
            out = place(out, tail(kit.giant(rng, -9 + i), 1.0) * 0.9, 0.6 + i * 0.45)
        return mix(out, bed("earth", 3.5, rng) * 0.7)
    if key == "pale_vesper":
        # The song cracks, and the dead she sang awake go back to sleep.
        crack = S.choir([(50, 0, 1.2, 100), (51, 0, 1.2, 100), (56, 0, 1.2, 100), (61, 0, 1.2, 90)])
        rest = S.choir([(50, 1.4, 2.5, 70), (57, 1.4, 2.5, 60), (62, 1.6, 2.3, 60)], S.VOICE_OOHS)
        return mix(tail(crack, 1.5) * 0.6, tail(rest, 4.2) * 0.5, kit.reverse(tail(kit.bowed(rng, -2), 1.4, 0.1)) * 0.4)
    if key in ("ashwick", "fire"):
        # The fire goes out in a long hiss of steam.
        hiss = hp(noise(3.0, rng), 2500) * env([(0, 0), (0.5, 1), (3.0, 0)], 3.0) * 0.5
        return mix(burst("fire", rng), place(silence(3.5), stereo(hiss, 0.9, rng=rng), 0.6))
    if key in ("vholt", "storm"):
        screech = C.roar(Voice("af_kore", 1.0, depth=4, sub=0.0, grit=0.4, growl=0.2), rng, "Kreeeeeeee!", 1.0, -6, 1.0)
        return mix(thunder(rng, 4.0), place(silence(4.0), screech * 0.5, 0.2), wind(3.5, rng) * 0.4)
    if key in ("mother_briar", "nature"):
        snaps = silence(3.0)
        for i in range(12):
            snaps = place(snaps, cut(kit.claves(rng, -rng.uniform(4, 12)), 0, 0.15, 0.05), rng.uniform(0, 2.2),
                          rng.uniform(0.3, 0.8))
        return mix(snaps, bed("nature", 3.0, rng) * 0.6)
    if key == "ashen_regent":
        # His armour hits the stones; chains and embers.
        clang = mix(tail(kit.anvil(rng, -5), 2.0) * 0.7, tail(kit.metal(rng, -7), 2.0) * 0.6)
        return mix(place(silence(3.0), clang, 0.4), kit.chain(rng, 1.6, -3) * 0.4, burst("fire", rng) * 0.5)
    if key == "sundered_heart":
        out = silence(4.0)
        for i, t in enumerate((0.0, 0.8, 1.8, 3.0)):
            out = place(out, step("heart", rng) * (1.2 - i * 0.25), t)
        return mix(out, place(silence(4.0), tail(kit.glass(rng, -12), 1.5) * 0.6, 0.3))
    if key == "vael_orrun":
        out = silence(5.0)
        for i, e in enumerate(("void", "earth", "water", "nature", "storm", "fire")):
            out = place(out, burst(e, rng) * 0.6, 0.2 + i * 0.3)
        implode = kit.reverse(tail(kit.tam_tam(rng, -10), 1.6, 0.0))
        out = place(out, implode, 2.0)
        out = place(out, tail(kit.impact(rng, 1.8, gong_level=1.0), 3.0), 3.6)
        shards = mix(*[place(silence(2.0), tail(kit.glass(rng, -rng.uniform(0, 8)), 0.8), rng.uniform(0, 0.6))
                       for _ in range(4)])
        return mix(out, place(silence(5.0), shards * 0.6, 3.6))
    if key == "water":
        return kit.water_rush(4.0, rng, 0.7) * 1.2
    if key in ("earth", "warden"):
        return bed("earth", 3.5, rng)
    if key == "void":
        return mix(bed("void", 3.5, rng) * 0.8, kit.reverse(tail(kit.bowed(rng, 0), 1.5, 0.1)) * 0.4)
    return bed(bs.element, 3.0, rng)


def _register_set(key: str, bs: BossSet) -> None:
    folder = f"bosses/{key}"
    register(f"boss_{key}_reveal", folder, lambda rng, v: reveal(bs, rng), loud=-11.0, duck_db=-3.0, duck_time=3.0,
             **REVEAL, description=f"{bs.title} appears")
    register(f"boss_{key}_step", folder, lambda rng, v: step(bs.step, rng), variants=3, loud=-19.0, max_voices=2,
             min_gap=0.15, pitch_jitter=0.05, priority=3, description=f"{bs.title} walks")
    register(f"boss_{key}_voice", folder, lambda rng, v: voice_line(bs, rng, v), variants=3, loud=-14.0, max_voices=1,
             min_gap=1.0, priority=6, duck_db=-5.0, duck_time=2.5, description=f"{bs.title} speaks")
    register(f"boss_{key}_enrage", folder, lambda rng, v: enrage(bs, rng), loud=-12.0, max_voices=1, priority=7,
             duck_db=-6.0, duck_time=2.0, description=f"{bs.title} is wounded and enraged")
    register(f"boss_{key}_death", folder, lambda rng, v: death(bs, rng), loud=-11.0, max_voices=1, priority=8,
             duck_db=-12.0, duck_time=4.0, positional=False, description=f"{bs.title} dies")


for _key, _bs in SETS.items():
    _bs.key = _key
    _register_set(_key, _bs)


# --- Boss tricks and the assault ---------------------------------------------------------------

@sound("boss_silence", "bosses", loud=-16.0, max_voices=1, min_gap=1.0, priority=6,
       description="a boss silences nearby towers")
def boss_silence(rng, v):
    suck = kit.reverse(tail(kit.gong(rng, -5), 0.9, 0.0))
    thud = tail(kit.tam_tam(rng, -14), 1.4)
    hush = tail(kit.bowed(rng, 2), 1.2) * 0.3
    return kit.hall(mix(place(silence(2.2), suck * 0.8, 0.0), place(silence(2.2), mix(thud, hush), 0.88)), 2.0, 0.35, rng)


@sound("boss_blink", "bosses", loud=-17.0, max_voices=1, min_gap=0.5, priority=5,
       description="a boss steps forward through shadow")
def boss_blink(rng, v):
    gone = kit.reverse(tail(kit.cymbal(rng, -6), 0.45, 0.0))
    arrive = mix(tail(kit.giant(rng, -6, "hand"), 0.6) * 0.6, whoosh(0.4, rng, 2500, 300, 1.5, [(0, 1), (0.4, 0)]) * 0.5)
    return kit.hall(mix(place(silence(1.0), gone * 0.8, 0.0), place(silence(1.0), arrive, 0.44)), 1.4, 0.3, rng)


@sound("boss_escape", "bosses", loud=-15.0, max_voices=1, priority=7, positional=False,
       description="a beaten boss escapes the board")
def boss_escape(rng, v):
    regent = SETS["ashen_regent"]
    line = _say(regent, "We will meet again.", rng)
    vanish = mix(kit.reverse(tail(kit.crash(rng, -5), 1.0, 0.0)) * 0.7, whoosh(1.2, rng, 3000, 150, 0.8) * 0.6)
    out = place(silence(3.0), line, 0.0)
    out = place(out, vanish, len(line) / SR - 0.2)
    return _room(out, regent, rng)


@sound("structure_collapse", "bosses", variants=2, loud=-12.0, max_voices=1, priority=7, duck_db=-8.0, duck_time=3.0,
       description="a building of the enemy citadel falls")
def structure_collapse(rng, v):
    d = 5.5
    out = silence(d)
    for i in range(5):
        out = place(out, tail(kit.giant(rng, -8 - rng.uniform(0, 4)), 1.2) * rng.uniform(0.6, 1.0),
                    i * rng.uniform(0.25, 0.45))
    out = mix(out, tail(kit.impact(rng, 1.4, crash_level=0.7), 4.5) * 0.8, kit.debris(rng, d - 0.5, 40, -3) * 0.8,
              bed("earth", d - 0.5, rng) * 0.7, place(silence(d), tail(kit.glass(rng, -6), 1.0) * 0.4, 0.3))
    return kit.hall(out, 3.0, 0.3, rng)


@sound("assault_phase", "bosses", loud=-13.0, duck_db=-8.0, duck_time=3.0, positional=False, priority=6,
       description="the assault moves on to its next part")
def assault_phase(rng, v):
    horns = mix(kit.chord("horn", [43, 50, 55], 2.6, rng, 0.08, 0.8), kit.chord("trombone", [31, 38], 2.6, rng, 0.08, 0.8) * 0.7)
    drums = silence(3.6)
    for i in range(6):
        drums = place(drums, tail(kit.giant(rng, -4, "sticks"), 0.8), i * 0.33)
    drums = place(drums, tail(kit.impact(rng, 1.0), 2.5), 6 * 0.33)
    return kit.hall(mix(place(silence(4.5), horns * 0.8, 0.2), drums), 2.6, 0.3, rng)


def boss_sets() -> dict[str, str]:
    """Which sound set each boss enemy uses."""
    out = {}
    for key, bs in SETS.items():
        for enemy in bs.enemies:
            out[enemy] = key
    return out
