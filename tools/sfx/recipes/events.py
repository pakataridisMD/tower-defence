"""Interface, building, waves, the base being hit, victory and defeat, and the six player skills.

Built on recordings (kit.py): real French horns, trumpets, trombones and tuba for every call and
fanfare, a sampled choir, timpani, giant drums, cymbals and gongs for the hits, tambourine jingles for
gold, and drum skins, wood, metal and stone for the interface. No synthesised bells or chimes.
"""

from __future__ import annotations

import numpy as np

from dsp import SR, decay, env, hp, lp, mix, n_of, noise, place, silence, stereo, sweep, svf, trem, whoosh
import kit
import samples as S
from kit import cut, tail
from registry import sound
from .palette import ELEMENTS
from .textures import bed, burst, fire_crackle, thunder

UI = dict(bus="Ui", positional=False)
STING = dict(positional=False, priority=5)


def _thock(rng, st: float = 0.0, length: float = 0.14) -> np.ndarray:
    """A soft leather-and-wood press: a big hand drum pitched up, with a touch of latch."""
    body = cut(kit.giant(rng, 12 + st, "hand"), 0, length, length * 0.6)
    latch = hp(cut(kit.metal(rng, 14 + st), 0, 0.03, 0.02), 2500) * 0.08
    return mix(body, latch)


def _swish(seconds: float, rng, f0=500.0, f1=3500.0, peak=0.6) -> np.ndarray:
    return whoosh(seconds, rng, f0, f1, 1.2, [(0, 0), (seconds * peak, 1), (seconds, 0)])


def _brass_stab(rng, midis, seconds=0.5, kinds=("horn_stac", "trumpet_stac")) -> np.ndarray:
    parts = []
    for i, m in enumerate(midis):
        kind = kinds[i % len(kinds)]
        parts.append(tail(kit.note(kind, m, rng), seconds))
    return mix(*parts)


def _horns(rng, notes, kinds=("horn", "trombone"), octave=(0, -12), levels=(1.0, 0.6)) -> np.ndarray:
    """A horn call from real held notes: (midi, start, length)."""
    end = max(s + l for _, s, l in notes) + 1.0
    out = silence(end)
    for midi, start, length in notes:
        for kind, oct_, lvl in zip(kinds, octave, levels):
            out = place(out, kit.held(kind, midi + oct_, length, rng, 0.04, 0.35) * lvl, start)
    return out


# --- Interface -----------------------------------------------------------------------

@sound("ui_hover", "ui", loud=-36.0, max_voices=2, min_gap=0.03, pitch_jitter=0.04, **UI,
       description="the mouse moves onto a button")
def ui_hover(rng, v):
    return hp(cut(kit.shaker(rng, 3), 0, 0.06, 0.04), 1800)


@sound("ui_click", "ui", variants=2, loud=-24.0, max_voices=2, min_gap=0.03, pitch_jitter=0.03, **UI,
       description="a button is pressed")
def ui_click(rng, v):
    return _thock(rng, [0, -1.5][v])


@sound("ui_back", "ui", loud=-26.0, max_voices=1, min_gap=0.05, **UI, description="closing or going back")
def ui_back(rng, v):
    return place(_thock(rng, 0) * 0.8, _thock(rng, -4), 0.06)


@sound("ui_error", "ui", loud=-22.0, max_voices=1, min_gap=0.15, **UI,
       description="not allowed: not enough gold, can't build here, skill not ready")
def ui_error(rng, v):
    blat = mix(tail(kit.note("tuba_stac", 35, rng), 0.18, 0.08), tail(kit.note("tuba_stac", 36, rng), 0.18, 0.08))
    thud = cut(kit.giant(rng, 4, "hand"), 0, 0.2, 0.1) * 0.6
    one = mix(blat, thud)
    return place(place(silence(0.4), one, 0.0), one * 0.8, 0.15)


@sound("ui_open", "ui", loud=-24.0, max_voices=1, min_gap=0.1, **UI, description="the skill web or a panel opens")
def ui_open(rng, v):
    swish = _swish(0.32, rng, 500, 3500) * 0.7
    shimmer = hp(tail(kit.bowed(rng, 7), 0.6), 1500) * 0.15
    return mix(swish, place(silence(0.7), mix(_thock(rng, -3), shimmer), 0.2))


@sound("ui_close", "ui", loud=-26.0, max_voices=1, min_gap=0.1, **UI, description="a panel closes")
def ui_close(rng, v):
    swish = _swish(0.25, rng, 3000, 500, 0.3) * 0.7
    return mix(swish, place(silence(0.4), _thock(rng, -5), 0.12))


@sound("ui_tab", "ui", loud=-27.0, max_voices=1, min_gap=0.05, **UI, description="the shop turns a page")
def ui_tab(rng, v):
    flick = hp(noise(0.09, rng), 1500) * env([(0, 0), (0.02, 1), (0.09, 0)], 0.09) * 0.9
    return mix(flick, place(silence(0.2), _thock(rng, 2) * 0.5, 0.04))


@sound("ui_toggle", "ui", loud=-25.0, max_voices=1, min_gap=0.05, **UI, description="game speed changes")
def ui_toggle(rng, v):
    return place(_thock(rng, 0, 0.08), _thock(rng, 3, 0.1), 0.05)


@sound("ui_pause", "ui", loud=-25.0, max_voices=1, min_gap=0.1, **UI, description="the game pauses")
def ui_pause(rng, v):
    strings = kit.chord("cello", [50, 57], 0.35, rng, 0.05, 0.4) * 0.6
    return mix(_thock(rng, -2), place(silence(0.9), strings, 0.02))


@sound("ui_resume", "ui", loud=-25.0, max_voices=1, min_gap=0.1, **UI, description="the game resumes")
def ui_resume(rng, v):
    strings = kit.chord("cello", [50, 57, 62], 0.3, rng, 0.03, 0.35) * 0.6
    return mix(_thock(rng, 1), place(silence(0.9), strings, 0.02))


@sound("ui_confirm", "ui", loud=-20.0, max_voices=1, min_gap=0.2, **UI,
       description="a big choice is confirmed: start a stage or a run")
def ui_confirm(rng, v):
    swell = kit.swell(0.5, rng, 2) * 0.5
    hit = mix(tail(kit.impact(rng, 0.4, crash_level=0.5), 1.6), _brass_stab(rng, [50, 57, 62, 66], 0.9) * 0.7)
    return kit.hall(place(swell, hit, 0.48), 1.6, 0.22, rng)


@sound("node_take", "ui", variants=3, loud=-21.0, max_voices=2, min_gap=0.06, **UI,
       description="a skill web node is taken")
def node_take(rng, v):
    root = 50 + [0, 2, 4][v]
    stab = _brass_stab(rng, [root, root + 7, root + 12], 0.7)
    drum = tail(kit.timpani(rng, False, [0, 2, 4][v] - 2), 0.8) * 0.5
    glow = hp(tail(kit.bowed(rng, 5 + v), 0.9), 1200) * 0.2
    return kit.hall(mix(stab, drum, glow, _swish(0.3, rng, 600, 3500) * 0.25), 1.3, 0.25, rng)


@sound("node_refund", "ui", loud=-24.0, max_voices=1, min_gap=0.08, **UI, description="a skill web node is given back")
def node_refund(rng, v):
    suck = kit.reverse(tail(kit.cymbal(rng, 0), 0.4, 0.0)) * 0.6
    pizz = mix(cut(kit.note("cello_spic", 50, rng), 0, 0.4, 0.2), cut(kit.note("cello_spic", 45, rng), 0, 0.4, 0.2))
    return mix(place(silence(0.9), suck, 0.0), place(silence(0.9), pizz * 0.8, 0.38))


def _make_star(v):
    def make(rng, _v):
        root = [50, 53, 57][v]
        chord_ = [root, root + 4, root + 7, root + 12] if v < 2 else [root - 12, root, root + 4, root + 7, root + 12]
        stab = mix(_brass_stab(rng, chord_, 1.2), kit.chord("horn", [root - 12, root - 5], 0.7, rng, 0.02, 0.6) * 0.5)
        drum = mix(tail(kit.timpani(rng, v == 0, v * 2), 1.4) * 0.7, tail(kit.giant(rng, -2 + v), 1.0) * 0.6)
        out = mix(stab, drum, tail(kit.cymbal(rng, 0), 2.0) * (0.25 + 0.2 * v))
        if v == 2:
            out = mix(out, tail(kit.crash(rng, -2), 2.5) * 0.4, tail(S.choir([(62, 0, 1.6, 90), (66, 0, 1.6, 85), (69, 0, 1.6, 85)]), 2.0) * 0.4)
        return kit.hall(out, 1.8, 0.25, rng)
    return make


for _i in range(3):
    sound(f"star_{_i + 1}", "ui", loud=-18.0, max_voices=3, **UI,
          description=f"campaign star {_i + 1} is earned")(_make_star(_i))


@sound("coin", "ui", variants=3, loud=-31.0, volume_db=-6.0, max_voices=2, min_gap=0.07, pitch_jitter=0.05,
       bus="Ui", positional=True, description="gold from a kill")
def coin(rng, v):
    jingle = cut(kit.tambourine(rng, [4, 6, 8][v]), 0, 0.3, 0.15)
    return hp(mix(jingle, place(silence(0.4), cut(kit.tambourine(rng, 9), 0, 0.2, 0.1) * 0.4, 0.05)), 900)


@sound("gold_bonus", "ui", loud=-22.0, max_voices=1, **UI, description="wave bonus gold arrives")
def gold_bonus(rng, v):
    out = silence(1.2)
    for i in range(9):
        out = place(out, cut(kit.tambourine(rng, rng.uniform(2, 8)), 0, 0.3, 0.15) * rng.uniform(0.4, 0.9),
                    i * 0.07 + rng.uniform(0, 0.02))
    pouch = cut(kit.giant(rng, 8, "hand"), 0, 0.2, 0.1) * 0.5
    return hp(mix(out, place(silence(1.2), pouch, 0.65)), 300)


@sound("skill_ready", "ui", loud=-26.0, max_voices=1, min_gap=0.25, **UI, description="a skill's cooldown is over")
def skill_ready(rng, v):
    call = mix(tail(kit.note("horn_stac", 57, rng), 0.35), place(silence(0.8), tail(kit.note("horn_stac", 62, rng), 0.5), 0.1))
    return kit.hall(call, 1.0, 0.2, rng)


@sound("skill_aim", "ui", loud=-29.0, max_voices=1, min_gap=0.1, **UI, description="a skill is being aimed")
def skill_aim(rng, v):
    trem_ = kit.held("cello_trem", 45, 0.3, rng, 0.08, 0.15) * 0.6
    return mix(_swish(0.3, rng, 600, 2500) * 0.6, trem_)


# --- Building towers ------------------------------------------------------------------

def _place_base(rng) -> np.ndarray:
    thud = tail(kit.giant(rng, -2, "hand"), 0.5) * 1.0
    stone = cut(kit.brick(rng, -2), 0, 0.35, 0.15) * 0.5
    knock = tail(kit.log_drum(rng, -5), 0.3) * 0.5
    clank = cut(kit.metal(rng, 2), 0, 0.25, 0.15) * 0.15
    return mix(thud, stone, place(silence(0.5), knock, 0.04), place(silence(0.5), clank, 0.09))


for _el in ELEMENTS:
    def _make_place(el):
        def make(rng, v):
            base = _place_base(rng)
            return mix(base, place(silence(0.2), cut(burst(el, rng), 0, 0.9, 0.4) * 0.3, 0.06))
        return make
    sound(f"tower_place_{_el}", "build", variants=2, loud=-19.0, max_voices=2, min_gap=0.05,
          description=f"a {_el} tower is built")(_make_place(_el))


@sound("tower_sell", "build", loud=-20.0, max_voices=1, min_gap=0.1, description="a tower is sold")
def tower_sell(rng, v):
    crumble = mix(kit.debris(rng, 0.9, 8, 0) * 0.9, tail(kit.giant(rng, -4, "soft"), 0.6) * 0.6)
    coins = silence(1.0)
    for i in range(5):
        coins = place(coins, cut(kit.tambourine(rng, rng.uniform(3, 8)), 0, 0.25, 0.1) * rng.uniform(0.4, 0.8), 0.2 + i * 0.08)
    return mix(crumble, hp(coins, 900) * 0.6)


@sound("tower_level_up", "build", loud=-18.0, max_voices=1, min_gap=0.1, description="a tower gains a level")
def tower_level_up(rng, v):
    out = silence(1.4)
    for i, (m, t) in enumerate(((50, 0.0), (54, 0.09), (57, 0.18), (62, 0.27))):
        out = place(out, tail(kit.note("horn_stac" if i < 3 else "trumpet_stac", m, rng), 0.5) * (0.7 + 0.1 * i), t)
    out = mix(out, place(silence(1.4), tail(kit.timpani(rng, False, 0), 1.0) * 0.5, 0.27),
              kit.swell(0.3, rng, 4) * 0.3)
    return kit.hall(out, 1.4, 0.22, rng)


@sound("tower_ascend", "build", loud=-15.0, max_voices=1, duck_db=-6.0, duck_time=2.0, priority=4,
       description="a tower ascends into its specialisation")
def tower_ascend(rng, v):
    d = 3.0
    rise = kit.riser(0.9, rng, 2)
    brass = mix(kit.chord("horn", [55, 59, 62], 1.6, rng, 0.03, 0.8), kit.chord("trumpet", [67, 71], 1.4, rng, 0.03, 0.7) * 0.6,
                kit.chord("trombone", [43, 50], 1.6, rng, 0.03, 0.8) * 0.7)
    ah = tail(S.choir([(55, 0, 2.0, 95), (59, 0, 2.0, 90), (62, 0, 2.0, 90), (67, 0, 2.0, 85)]), 2.4) * 0.5
    hit = tail(kit.impact(rng, 0.7, crash_level=0.7), 2.2)
    out = place(silence(d), rise * 0.6, 0.0)
    out = place(out, mix(hit, brass * 0.8, ah), 0.9)
    return kit.hall(out, 2.2, 0.3, rng)


@sound("tower_hybrid", "build", loud=-16.0, max_voices=1, duck_db=-4.0, duck_time=1.5, priority=4,
       description="a tower fuses into a dual or triple tower")
def tower_hybrid(rng, v):
    d = 2.6
    pull = mix(kit.reverse(tail(kit.gong(rng, -2), 0.9, 0.0)) * 0.6, _swish(0.9, rng, 300, 3000, 0.9) * 0.5)
    merge = mix(tail(kit.impact(rng, 0.6, gong_level=0.5), 2.0),
                kit.chord("horn", [52, 59, 64], 1.2, rng, 0.03, 0.7) * 0.7,
                tail(S.choir([(52, 0, 1.4, 90), (59, 0, 1.4, 85), (64, 0, 1.4, 85), (68, 0, 1.4, 80)]), 1.8) * 0.45)
    out = place(place(silence(d), pull, 0.0), merge, 0.9)
    return kit.hall(out, 2.0, 0.3, rng)


# --- Waves -----------------------------------------------------------------------------

def _drums(rng, times_, st=-4, kind="sticks", levels=None) -> np.ndarray:
    out = silence(max(times_) + 1.2)
    for i, t in enumerate(times_):
        lvl = levels[i] if levels else 1.0
        out = place(out, tail(kit.giant(rng, st, kind), 1.0) * lvl, t)
    return out


@sound("wave_start", "waves", loud=-15.0, duck_db=-5.0, duck_time=2.5, **STING, description="a wave starts: war horn and drums")
def wave_start(rng, v):
    horn = _horns(rng, [(50, 0.0, 0.45), (50, 0.55, 0.3), (57, 0.9, 1.4)])
    drums = _drums(rng, [0.0, 0.55, 0.9, 1.15, 1.4], -4, "sticks", [1.0, 0.8, 1.0, 0.6, 0.9])
    return kit.hall(mix(horn * 0.9, drums * 0.8, place(silence(3), tail(kit.timpani(rng), 1.5) * 0.5, 0.9)), 2.2, 0.3, rng)


@sound("wave_start_boss", "waves", loud=-13.0, duck_db=-3.0, duck_time=3.0, **STING,
       description="a boss wave starts: deep horns, gong and drums")
def wave_start_boss(rng, v):
    low = _horns(rng, [(38, 0.0, 1.0), (37, 1.1, 1.8)], ("tuba", "trombone", "horn"), (0, 12, 12), (1.0, 0.8, 0.5))
    gong_ = tail(kit.tam_tam(rng, -5), 3.5) * 0.6
    drums = _drums(rng, [1.1 + i * 0.16 for i in range(8)], -6, "mallet", [0.5 + i * 0.07 for i in range(8)])
    big = tail(kit.impact(rng, 1.0, gong_level=0.4), 2.5)
    out = mix(low, gong_, drums * 0.7, place(silence(4.0), big, 2.6))
    return kit.hall(out, 2.8, 0.33, rng)


@sound("wave_start_final", "waves", loud=-13.0, duck_db=-8.0, duck_time=3.5, **STING,
       description="the last wave starts: horns and a rising choir")
def wave_start_final(rng, v):
    ah = tail(S.choir([(45, 0, 3.2, 90), (52, 0, 3.2, 90), (57, 0.1, 3.1, 95), (60, 0.2, 3.0, 95)]), 3.6) * 0.7
    horn = _horns(rng, [(45, 0.0, 0.6), (48, 0.7, 0.6), (52, 1.4, 1.6)])
    drums = _drums(rng, [0.0, 0.7, 1.4, 1.6, 1.8, 2.0], -5, "mallet")
    out = mix(ah, horn * 0.9, drums * 0.8, kit.riser(1.4, rng) * 0.3)
    return kit.hall(out, 2.6, 0.33, rng)


@sound("wave_cleared", "waves", loud=-17.0, duck_db=-4.0, duck_time=1.5, **STING, description="a wave is beaten")
def wave_cleared(rng, v):
    horn = _horns(rng, [(62, 0.0, 0.16), (66, 0.16, 0.16), (69, 0.32, 0.9)], ("horn", "trumpet"), (-12, 0), (1.0, 0.5))
    hit = mix(tail(kit.giant(rng, -2, "sticks"), 1.0) * 0.6, tail(kit.cymbal(rng, 0), 1.6) * 0.3)
    return kit.hall(mix(horn * 0.8, place(silence(1.6), hit, 0.32)), 1.8, 0.3, rng)


@sound("victory", "waves", loud=-13.0, duck_db=-14.0, duck_time=5.0, **STING, description="the run or stage is won")
def victory(rng, v):
    notes = [(62, 0.0, 0.2), (62, 0.22, 0.2), (62, 0.44, 0.2), (67, 0.66, 0.7), (66, 1.4, 0.35),
             (67, 1.78, 0.35), (69, 2.16, 0.35), (74, 2.55, 1.8)]
    fanfare = _horns(rng, notes, ("trumpet", "horn", "trombone"), (0, -12, -24), (0.9, 0.8, 0.5))
    ah = tail(S.choir([(50, 0, 2.2, 95), (57, 0, 2.2, 90), (62, 0, 2.2, 95), (66, 0, 2.2, 90), (69, 0, 2.2, 90)]), 2.8) * 0.5
    drums = mix(_drums(rng, [0.0, 0.66, 1.4, 2.16], -4, "sticks"), place(silence(5), tail(kit.timpani_roll(rng, 0.7), 0.7) * 0.6, 1.85))
    final = mix(tail(kit.impact(rng, 0.8, crash_level=1.0), 3.0), tail(kit.timpani(rng), 2.0) * 0.6)
    out = mix(fanfare, drums * 0.8, place(silence(5.0), mix(ah, final), 2.55))
    return kit.hall(out, 2.6, 0.3, rng)


@sound("defeat", "waves", loud=-14.0, duck_db=-14.0, duck_time=5.0, **STING, description="the base falls and the run is lost")
def defeat(rng, v):
    low = _horns(rng, [(45, 0.0, 0.8), (44, 0.8, 0.8), (43, 1.6, 0.8), (38, 2.4, 2.2)], ("trombone", "tuba", "horn"),
                 (0, -12, 12), (0.9, 0.8, 0.4))
    tolls = mix(*[place(silence(6.0), tail(kit.tam_tam(rng, -6 - 2 * i), 2.5) * 0.5, t) for i, t in enumerate((0.0, 1.6, 3.2))])
    oh = tail(S.choir([(38, 0, 3.0, 85), (41, 0, 3.0, 80), (45, 0, 3.0, 80), (50, 0, 3.0, 75)]), 3.4) * 0.5
    roll = place(silence(6.0), kit.reverse(tail(kit.timpani_roll(rng, 2.0, -2), 2.0, 0.0)) * 0.4, 0.4)
    out = mix(low, tolls, place(silence(6.0), oh, 2.2), roll)
    return kit.hall(out, 3.2, 0.35, rng)


# --- The base ----------------------------------------------------------------------------

def _alarm(rng, n: int, gap: float, root: int = 45) -> np.ndarray:
    """Soldiers' warning: short low brass blasts instead of bells."""
    out = silence(n * gap + 0.6)
    for i in range(n):
        blast = mix(tail(kit.note("trombone", root, rng), 0.28, 0.12), tail(kit.note("tuba", root - 12, rng), 0.3, 0.12) * 0.7,
                    tail(kit.note("buzz", root + 1, rng), 0.25, 0.1) * 0.3)
        out = place(out, blast, i * gap)
    return out


@sound("base_hit", "base", variants=3, loud=-15.0, max_voices=2, min_gap=0.25, priority=4, positional=False,
       description="a monster gets through and the base takes damage")
def base_hit(rng, v):
    ram = mix(tail(kit.giant(rng, -6 - v), 1.2) * 1.0, tail(kit.concert_bass(rng, -5), 1.2) * 0.7,
              tail(kit.timp_snare(rng, -3), 0.8) * 0.5)
    gate = mix(cut(kit.metal(rng, -6 - 2 * v), 0, 1.0, 0.5) * 0.45, kit.chain(rng, 0.7, -2) * 0.3)
    crack = kit.debris(rng, 1.2, 8, -2) * 0.5
    out = mix(ram, gate, crack, place(silence(1.6), _alarm(rng, 2, 0.24, 45 + [0, 2, -2][v]) * 0.35, 0.12))
    return kit.hall(out, 1.4, 0.2, rng)


@sound("base_hit_boss", "base", loud=-11.0, max_voices=1, priority=6, positional=False, duck_db=-10.0, duck_time=3.0,
       description="a boss breaks into the base")
def base_hit_boss(rng, v):
    smash = tail(kit.impact(rng, 1.5, metal_level=0.8, gong_level=0.6, crash_level=0.9), 3.5)
    rubble = mix(kit.debris(rng, 2.8, 30, -3) * 0.8, bed("earth", 2.8, rng) * 0.5)
    shatter = mix(tail(kit.glass(rng, -4), 1.0) * 0.4, place(silence(1.0), tail(kit.glass(rng, -8), 1.0) * 0.3, 0.15))
    out = mix(smash, rubble, shatter, place(silence(3.6), _alarm(rng, 4, 0.32, 44) * 0.4, 0.4))
    return kit.hall(out, 2.4, 0.3, rng)


@sound("lives_low", "base", loud=-17.0, max_voices=1, priority=5, positional=False,
       description="warning: the base is nearly lost")
def lives_low(rng, v):
    out = silence(3.0)
    for i in range(3):
        lub = tail(kit.bass_drum(rng, -2, False), 0.4)
        dub = tail(kit.bass_drum(rng, -4, False), 0.4) * 0.7
        out = place(out, mix(lub, place(silence(0.5), dub, 0.2)), i * 0.78)
    strings = mix(kit.held("cello_trem", 45, 2.3, rng, 0.3, 0.5), kit.held("cello_trem", 46, 2.3, rng, 0.3, 0.5) * 0.8,
                  kit.held("bass_trem", 33, 2.3, rng, 0.3, 0.5) * 0.6)
    horn = _horns(rng, [(50, 0.1, 0.5), (49, 0.8, 1.0)], ("horn",), (-12,), (1.0,))
    return stereo(mix(out, strings * 0.45, horn * 0.4), 0.4, rng=rng)


# --- Player skills ----------------------------------------------------------------------

@sound("skill_meteor", "skills", loud=-11.0, max_voices=1, priority=5, duck_db=-6.0, duck_time=2.0,
       description="Meteor: a burning rock falls from the sky")
def skill_meteor(rng, v):
    fall = 0.7
    incoming = mix(kit.reverse_crash(fall, rng, -6) * 0.6, _swish(fall, rng, 200, 2500, 0.95) * 1.0,
                   S.stretch(cut(lp(kit.gong_roll(rng, -10), 2000), 0, fall, 0.05), 0, 1.0) * np.linspace(0.1, 1, n_of(fall))[:, None] * 0.6)
    boom_ = tail(kit.impact(rng, 1.4, crash_level=0.9), 3.0)
    tail_ = mix(kit.debris(rng, 2.5, 20, -2) * 0.6, stereo(fire_crackle(2.5, rng, 1.5), 0.8, rng=rng) * decay(2.5, 1.0)[:, None] * 0.5)
    out = place(incoming, mix(boom_, burst("fire", rng) * 0.6, tail_), fall)
    return kit.hall(out, 2.2, 0.28, rng)


@sound("skill_surge", "skills", loud=-12.0, max_voices=1, priority=5, positional=False, duck_db=-5.0, duck_time=2.0,
       description="Surge: every tower crackles with storm power")
def skill_surge(rng, v):
    charge = mix(kit.swell(0.7, rng, 3) * 0.7, cut(kit.zap(rng, -5), 0, 0.7, 0.05) * 0.5)
    strike = mix(thunder(rng, 2.6) * 1.0, tail(kit.zap(rng, 0), 1.4) * 0.8,
                 place(silence(2.0), tail(kit.zap(rng, 3), 1.0) * 0.6, 0.25), place(silence(2.0), tail(kit.zap(rng, -3), 1.0) * 0.5, 0.5),
                 tail(kit.crash(rng, -4), 2.0) * 0.4)
    return kit.hall(place(charge, strike, 0.68), 2.4, 0.3, rng)


@sound("skill_entangle", "skills", loud=-13.0, max_voices=1, priority=5, description="Entangle: roots burst from the ground")
def skill_entangle(rng, v):
    burst_ = mix(tail(kit.giant(rng, -5), 0.9), cut(kit.brick(rng, -6), 0, 0.6, 0.2) * 0.6)
    creaks = silence(2.4)
    for i in range(5):
        creaks = place(creaks, cut(kit.guiro(rng, -8 - rng.uniform(0, 6)), 0, 0.5, 0.15) * rng.uniform(0.5, 0.9), 0.1 + i * 0.25)
    snaps = silence(2.4)
    for _ in range(8):
        snaps = place(snaps, cut(kit.claves(rng, -rng.uniform(6, 14)), 0, 0.12, 0.05) * rng.uniform(0.3, 0.7), rng.uniform(0.1, 1.5))
    out = mix(burst_, creaks, snaps, bed("nature", 2.2, rng) * 0.6, cut(kit.ratchet(rng, -7), 0, 1.0, 0.4) * 0.4)
    return kit.hall(out, 1.5, 0.25, rng)


@sound("skill_tidal_wave", "skills", loud=-11.0, max_voices=1, priority=5, positional=False, duck_db=-6.0, duck_time=3.0,
       description="Tidal Wave: a wave sweeps the road")
def skill_tidal_wave(rng, v):
    d = 3.6
    rush = kit.water_rush(d, rng, 1.0) * 1.3
    crash_ = mix(tail(kit.impact(rng, 0.9, crash_level=0.0), 2.4) * 0.7, burst("water", rng) * 0.9,
                 tail(kit.cymbal(rng, -7), 2.0) * 0.4)
    low = kit.held("bass_trem", 28, d - 0.6, rng, 0.8, 0.8) * 0.4
    out = mix(rush, low, place(silence(d), crash_, 1.3), place(silence(d), kit.bubbles(rng, 0) * 0.5, 1.8))
    pan = np.stack([np.linspace(1.25, 0.45, len(out)), np.linspace(0.45, 1.25, len(out))], axis=1)
    return kit.hall(out * pan, 2.0, 0.28, rng)


@sound("skill_earthquake", "skills", loud=-11.0, max_voices=1, priority=5, positional=False, duck_db=-6.0, duck_time=3.0,
       description="Earthquake: the ground shakes and cracks")
def skill_earthquake(rng, v):
    d = 3.4
    out = mix(bed("earth", d, rng) * 1.0, tail(kit.timpani_roll(rng, d, -3), d) * 0.6, kit.chain(rng, d - 0.5, -10) * 0.3)
    for i in range(5):
        out = place(out, tail(kit.giant(rng, -9 - rng.uniform(0, 3)), 1.2) * rng.uniform(0.6, 1.0), 0.1 + i * rng.uniform(0.35, 0.55))
    out = mix(out, kit.debris(rng, d, 40, -3) * 0.6, kit.sub(d, 38, 26, 1.5) * 0.4)
    return kit.hall(out, 2.0, 0.22, rng)


@sound("skill_doom", "skills", loud=-12.0, max_voices=1, priority=5, duck_db=-6.0, duck_time=2.5,
       description="Doom: the void marks everything in an area")
def skill_doom(rng, v):
    d = 3.2
    suck = kit.reverse(tail(kit.tam_tam(rng, -6), 1.0, 0.0)) * 0.8
    hit = mix(tail(kit.tam_tam(rng, -14), 2.2), tail(kit.impact(rng, 0.9, crash_level=0.0), 2.2) * 0.7, kit.sub(1.8, 50, 24, 0.6) * 0.5)
    oh = tail(S.choir([(38, 0, 1.8, 95), (39, 0, 1.8, 90), (44, 0, 1.8, 90), (50, 0, 1.8, 85)]), 2.2) * 0.55
    hum = tail(kit.bowed(rng, -9), 2.2) * 0.4
    out = mix(place(silence(d), suck, 0.0), place(silence(d), mix(hit, oh, hum), 0.98))
    return kit.hall(out, 3.0, 0.33, rng)
