"""Interface, building, waves, the base being hit, victory and defeat, and the six player skills."""

from __future__ import annotations

import numpy as np

from dsp import (boom, bubbles, crackle, debris, decay, drive, env, fade, hp, lp, mix, modal, n_of, noise,
                 osc, place, resonate, reverb, ring, rumble, silence, stereo, svf, sweep, thump, times, trem, whoosh)
from registry import sound
from .palette import (ELEMENT_ROOT, ELEMENTS, arp, bell, braam, brass, chime, choir, flourish, gong, horn_call,
                      impact_earth, pitch, pluck, reverse, riser, semis, taiko)

UI = dict(bus="Ui", positional=False)
STING = dict(positional=False, priority=5)


# --- Interface -----------------------------------------------------------------------

@sound("ui_hover", "ui", loud=-34.0, max_voices=2, min_gap=0.03, pitch_jitter=0.04, **UI,
       description="the mouse moves onto a button")
def ui_hover(rng, v):
    return chime(2400, 0.06, rng) * decay(0.06, 0.012) * 0.6


@sound("ui_click", "ui", variants=2, loud=-24.0, max_voices=2, min_gap=0.03, pitch_jitter=0.03, **UI,
       description="a button is pressed")
def ui_click(rng, v):
    f = 1250 if v == 0 else 1180
    knock = modal(0.12, [(f, 0.025, 1.0), (f * 2.2, 0.015, 0.5), (f * 3.6, 0.008, 0.25)], rng)
    low = thump(0.1, 260, 120, 0.02, 0.0) * 0.5
    return mix(knock, low)


@sound("ui_back", "ui", loud=-25.0, max_voices=1, min_gap=0.05, **UI, description="closing or going back")
def ui_back(rng, v):
    a = modal(0.1, [(1100, 0.02, 1.0), (2400, 0.01, 0.4)], rng)
    b = modal(0.12, [(820, 0.025, 1.0), (1800, 0.012, 0.4)], rng)
    return place(a, b, 0.05)


@sound("ui_error", "ui", loud=-22.0, max_voices=1, min_gap=0.15, **UI,
       description="not allowed: not enough gold, can't build here, skill not ready")
def ui_error(rng, v):
    d = 0.11
    beep = lp(osc(165, d, "square") + osc(175, d, "square"), 1800) * env([(0, 0), (0.005, 1), (d - 0.02, 0.8), (d, 0)], d) * 0.5
    thud = thump(0.12, 150, 90, 0.03, 0.0) * 0.6
    out = place(silence(0.3), mix(beep, thud), 0.0)
    return place(out, mix(beep, thud) * 0.85, 0.14)


@sound("ui_open", "ui", loud=-23.0, max_voices=1, min_gap=0.1, **UI, description="the skill web or a panel opens")
def ui_open(rng, v):
    swish = whoosh(0.3, rng, 600, 4000, 1.4, [(0, 0), (0.18, 1), (0.3, 0)]) * 0.6
    notes = arp([semis(880, s) for s in (0, 4, 7, 12)], 0.04, 0.5, rng)
    return mix(swish, place(silence(0.1), notes * 0.5, 0.08))


@sound("ui_close", "ui", loud=-25.0, max_voices=1, min_gap=0.1, **UI, description="a panel closes")
def ui_close(rng, v):
    swish = whoosh(0.25, rng, 3500, 500, 1.4, [(0, 0), (0.05, 1), (0.25, 0)]) * 0.6
    notes = arp([semis(880, s) for s in (12, 7, 4)], 0.035, 0.35, rng)
    return mix(swish, notes * 0.4)


@sound("ui_tab", "ui", loud=-27.0, max_voices=1, min_gap=0.05, **UI, description="the shop turns a page")
def ui_tab(rng, v):
    flick = hp(noise(0.09, rng), 1500) * env([(0, 0), (0.02, 1), (0.09, 0)], 0.09) * 0.9
    tap = modal(0.08, [(900, 0.02, 1.0)], rng) * 0.4
    return mix(flick, place(silence(0.05), tap, 0.04))


@sound("ui_toggle", "ui", loud=-25.0, max_voices=1, min_gap=0.05, **UI, description="game speed changes")
def ui_toggle(rng, v):
    a = modal(0.05, [(1700, 0.01, 1.0), (3500, 0.006, 0.4)], rng)
    b = modal(0.06, [(2200, 0.012, 1.0), (4400, 0.006, 0.4)], rng)
    return place(a, b, 0.035)


@sound("ui_pause", "ui", loud=-24.0, max_voices=1, min_gap=0.1, **UI, description="the game pauses")
def ui_pause(rng, v):
    return mix(chime(659, 0.5, rng), place(silence(0.1), chime(523, 0.6, rng), 0.09)) * 0.7


@sound("ui_resume", "ui", loud=-24.0, max_voices=1, min_gap=0.1, **UI, description="the game resumes")
def ui_resume(rng, v):
    return mix(chime(523, 0.5, rng), place(silence(0.1), chime(659, 0.6, rng), 0.09)) * 0.7


@sound("ui_confirm", "ui", loud=-21.0, max_voices=1, min_gap=0.2, **UI,
       description="a big choice is confirmed: start a stage or a run")
def ui_confirm(rng, v):
    swell = whoosh(0.5, rng, 300, 3000, 1.2, [(0, 0), (0.42, 1), (0.5, 0)]) * 0.5
    hit = mix(thump(0.6, 120, 45, 0.12, 0.3, rng), chime(1046, 1.0, rng) * 0.4, chime(1568, 0.9, rng) * 0.25)
    return reverb(place(swell, hit, 0.45), 1.2, 0.2, rng=rng)


@sound("node_take", "ui", variants=3, loud=-22.0, max_voices=2, min_gap=0.06, **UI,
       description="a skill web node is taken")
def node_take(rng, v):
    root = semis(523.25, [0, 2, 4][v])
    notes = arp([root, semis(root, 7), semis(root, 12)], 0.05, 0.9, rng)
    glow = resonate(noise(0.6, rng, "pink"), sweep(800, 3500, 0.6), 6) * env([(0, 0), (0.15, 1), (0.6, 0)], 0.6) * 0.5
    sparkle = mix(*[place(silence(0.8), chime(rng.uniform(3000, 6000), 0.25, rng) * 0.15, rng.uniform(0.05, 0.5)) for _ in range(6)])
    return reverb(mix(notes * 0.7, glow, sparkle), 1.0, 0.25, rng=rng)


@sound("node_refund", "ui", loud=-24.0, max_voices=1, min_gap=0.08, **UI, description="a skill web node is given back")
def node_refund(rng, v):
    root = 523.25
    notes = arp([semis(root, 12), semis(root, 7), root], 0.05, 0.6, rng)
    suck = reverse(resonate(noise(0.4, rng, "pink"), sweep(800, 3000, 0.4), 6) * decay(0.4, 0.15)) * 0.5
    return mix(notes * 0.6, suck)


def _make_star(v):
    def make(rng, _v):
        root = semis(659.25, [0, 3, 7][v])
        notes = mix(chime(root, 1.4, rng), chime(semis(root, 7), 1.2, rng) * 0.5, chime(root * 2, 1.0, rng) * 0.4)
        shine = resonate(noise(0.8, rng), sweep(3000, 8000, 0.8), 8) * decay(0.8, 0.25) * 0.3
        hit = thump(0.3, 200, 90, 0.05, 0.0) * 0.4
        return reverb(mix(notes, shine, hit), 1.4, 0.25, rng=rng, wide=True)
    return make


for _i in range(3):
    sound(f"star_{_i + 1}", "ui", loud=-19.0, max_voices=3, **UI,
          description=f"campaign star {_i + 1} is earned")(_make_star(_i))


@sound("coin", "ui", variants=3, loud=-30.0, volume_db=-6.0, max_voices=2, min_gap=0.07, pitch_jitter=0.05,
       bus="Ui", positional=True, description="gold from a kill")
def coin(rng, v):
    f = [2093, 2349, 2637][v]
    clink = modal(0.3, [(f, 0.1, 1.0), (f * 2.4, 0.05, 0.5), (f * 3.1, 0.04, 0.3)], rng)
    second = modal(0.25, [(f * 1.33, 0.08, 1.0), (f * 3.2, 0.04, 0.4)], rng)
    return place(clink, second * 0.6, 0.05)


@sound("gold_bonus", "ui", loud=-22.0, max_voices=1, **UI, description="wave bonus gold arrives")
def gold_bonus(rng, v):
    out = silence(1.0)
    for i in range(14):
        f = rng.uniform(1800, 3200)
        c = modal(0.25, [(f, 0.07, 1.0), (f * 2.6, 0.04, 0.4)], rng)
        out = place(out, c * rng.uniform(0.3, 0.8), i * 0.045 + rng.uniform(0, 0.02))
    return out


@sound("skill_ready", "ui", loud=-27.0, max_voices=1, min_gap=0.25, **UI, description="a skill's cooldown is over")
def skill_ready(rng, v):
    return mix(chime(1318.5, 0.6, rng, 0.3), place(silence(0.1), chime(1975.5, 0.5, rng), 0.06) * 0.6)


@sound("skill_aim", "ui", loud=-28.0, max_voices=1, min_gap=0.1, **UI, description="a skill is being aimed")
def skill_aim(rng, v):
    return resonate(noise(0.25, rng), sweep(800, 2400, 0.25), 8) * env([(0, 0), (0.1, 1), (0.25, 0)], 0.25) * 2


# --- Building towers ------------------------------------------------------------------

def _place_base(rng) -> np.ndarray:
    set_down = thump(0.4, 140, 60, 0.07, 0.4, rng) * 1.2
    knock = modal(0.2, [(rng.uniform(300, 360), 0.05, 1.0), (820, 0.03, 0.5), (1500, 0.015, 0.3)], rng) * 0.8
    dust = lp(hp(noise(0.5, rng), 600), 4000) * env([(0, 0), (0.03, 1), (0.5, 0)], 0.5) * 0.25
    clank = mix(*[place(silence(0.4), modal(0.1, [(rng.uniform(1500, 2600), 0.03, 1.0)], rng), 0.1 + i * 0.07) for i in range(2)]) * 0.3
    return mix(set_down, knock, dust, clank)


for _el in ELEMENTS:
    def _make_place(el):
        def make(rng, v):
            base = _place_base(rng)
            root = ELEMENT_ROOT[el] * 2
            shimmer = mix(chime(root, 0.8, rng) * 0.25, chime(semis(root, 7), 0.7, rng) * 0.15)
            layer = flourish(el, 0.6, rng) * 0.35
            return mix(base, place(silence(0.1), mix(shimmer, layer), 0.08))
        return make
    sound(f"tower_place_{_el}", "build", variants=2, loud=-19.0, max_voices=2, min_gap=0.05,
          description=f"a {_el} tower is built")(_make_place(_el))


@sound("tower_sell", "build", loud=-20.0, max_voices=1, min_gap=0.1, description="a tower is sold")
def tower_sell(rng, v):
    crumble = mix(debris(0.8, rng, 18, 0.7) * 0.8, lp(noise(0.8, rng, "brown"), 600) * decay(0.8, 0.2) * 0.8)
    coins = silence(0.9)
    for i in range(8):
        f = rng.uniform(1800, 3000)
        coins = place(coins, modal(0.25, [(f, 0.07, 1.0), (f * 2.6, 0.04, 0.4)], rng) * rng.uniform(0.3, 0.7), 0.15 + i * 0.06)
    return mix(crumble, coins * 0.8)


@sound("tower_level_up", "build", loud=-19.0, max_voices=1, min_gap=0.1, description="a tower gains a level")
def tower_level_up(rng, v):
    notes = arp([semis(392, s) for s in (0, 4, 7, 12, 16)], 0.06, 0.8, rng)
    swell = whoosh(0.5, rng, 500, 5000, 2.0, [(0, 0), (0.35, 1), (0.5, 0)]) * 0.4
    hit = mix(thump(0.3, 180, 80, 0.05, 0.0) * 0.6, chime(1568, 1.0, rng) * 0.3)
    out = mix(notes * 0.7, swell, place(silence(0.4), hit, 0.3))
    return reverb(out, 1.2, 0.2, rng=rng)


@sound("tower_ascend", "build", loud=-16.0, max_voices=1, duck_db=-6.0, duck_time=2.0, priority=4,
       description="a tower ascends into its specialisation")
def tower_ascend(rng, v):
    d = 2.6
    rise = riser(1.0, rng, 300, 4000) * 0.5
    pad = choir([semis(196, s) for s in (0, 7, 12, 16)], d - 0.6, rng, attack=0.8) * 0.7
    hit = mix(boom(1.2, rng, 0.8) * 0.6, bell(392, 2.0, rng) * 0.6, gong(130, 2.0, rng) * 0.3)
    sparkle = mix(*[place(silence(d), chime(rng.uniform(2500, 6000), 0.4, rng) * 0.15, rng.uniform(1.0, 2.2)) for _ in range(12)])
    out = mix(rise, place(silence(d), pad, 0.6), place(silence(d), hit, 0.95), sparkle)
    return reverb(stereo(out, 0.6, rng=rng), 2.0, 0.3, rng=rng)


@sound("tower_hybrid", "build", loud=-17.0, max_voices=1, duck_db=-4.0, duck_time=1.5, priority=4,
       description="a tower fuses into a dual or triple tower")
def tower_hybrid(rng, v):
    d = 2.0
    a = osc(sweep(300, 523, 1.0), 1.0) * env([(0, 0), (0.6, 1), (1.0, 0.6)], 1.0)
    b = osc(sweep(800, 523 * 1.5, 1.0), 1.0) * env([(0, 0), (0.6, 1), (1.0, 0.6)], 1.0)
    swirl = trem(resonate(noise(1.0, rng, "pink"), sweep(400, 3000, 1.0), 4) * 2, sweep(3, 18, 1.0), 0.8) * 0.4
    merge = mix(boom(0.9, rng, 0.7) * 0.6, chime(523, 1.2, rng) * 0.5, chime(784, 1.1, rng) * 0.4, chime(1046, 1.0, rng) * 0.3)
    out = place(mix(a * 0.3, b * 0.3, swirl), merge, 0.95)
    return reverb(stereo(out, 0.5, rng=rng), 1.6, 0.3, rng=rng)


# --- Waves -----------------------------------------------------------------------------

@sound("wave_start", "waves", loud=-15.0, duck_db=-5.0, duck_time=2.5, **STING, description="a wave starts: war horn and drums")
def wave_start(rng, v):
    horn = horn_call([(146.8, 0.0, 0.45), (146.8, 0.55, 0.3), (220.0, 0.9, 1.6)], rng)
    drums = silence(2.8)
    for i, t in enumerate((0.0, 0.55, 0.9, 1.15, 1.4)):
        drums = place(drums, taiko(0.8, rng, 70 if i % 2 == 0 else 85, 1.2) * (1.0 if i != 3 else 0.6), t)
    out = mix(horn * 0.9, drums * 0.8)
    return reverb(stereo(out, 0.5, rng=rng), 2.2, 0.3, rng=rng)


@sound("wave_start_boss", "waves", loud=-13.0, duck_db=-3.0, duck_time=3.0, **STING,
       description="a boss wave starts: deep horns, gong and drums")
def wave_start_boss(rng, v):
    horn = horn_call([(73.4, 0.0, 1.0), (69.3, 1.1, 1.8)], rng, layers=(1.0, 0.8), bright=0.6)
    horn2 = horn_call([(110.0, 0.0, 1.0), (103.8, 1.1, 1.8)], rng, layers=(0.7,), bright=0.7)
    g = gong(73.4, 3.5, rng) * 0.6
    drums = silence(3.6)
    for i in range(8):
        drums = place(drums, taiko(0.9, rng, 62, 1.4) * (0.5 + i * 0.07), 1.1 + i * 0.16)
    big = taiko(1.5, rng, 50, 2.0)
    out = mix(horn, horn2 * 0.7, g, drums * 0.7, place(silence(3.6), big, 2.6))
    return reverb(stereo(out, 0.6, rng=rng), 2.8, 0.35, rng=rng)


@sound("wave_start_final", "waves", loud=-13.0, duck_db=-8.0, duck_time=3.5, **STING,
       description="the last wave starts: horns and a rising choir")
def wave_start_final(rng, v):
    pad = choir([semis(110, s) for s in (0, 7, 12, 15)], 3.2, rng, attack=1.2) * 0.8
    horn = horn_call([(110.0, 0.0, 0.6), (130.8, 0.7, 0.6), (164.8, 1.4, 1.6)], rng)
    drums = silence(3.4)
    for i, t in enumerate((0.0, 0.7, 1.4, 1.6, 1.8, 2.0)):
        drums = place(drums, taiko(0.9, rng, 65, 1.3), t)
    out = mix(pad, horn * 0.9, drums * 0.8, place(silence(3.4), riser(1.4, rng, 200, 2500) * 0.3, 0.0))
    return reverb(stereo(out, 0.6, rng=rng), 2.6, 0.35, rng=rng)


@sound("wave_cleared", "waves", loud=-17.0, duck_db=-4.0, duck_time=1.5, **STING, description="a wave is beaten")
def wave_cleared(rng, v):
    horn = horn_call([(293.7, 0.0, 0.16), (370.0, 0.16, 0.16), (440.0, 0.32, 0.9)], rng, layers=(1.0, 0.4), bright=1.0)
    bells = mix(chime(880, 1.2, rng) * 0.3, chime(1318.5, 1.0, rng) * 0.2)
    drum = taiko(0.6, rng, 90, 1.0) * 0.5
    out = mix(horn * 0.8, place(silence(1.4), bells, 0.32), place(silence(1.4), drum, 0.32))
    return reverb(stereo(out, 0.5, rng=rng), 1.8, 0.3, rng=rng)


@sound("victory", "waves", loud=-13.0, duck_db=-14.0, duck_time=5.0, **STING, description="the run or stage is won")
def victory(rng, v):
    notes = [(293.7, 0.0, 0.2), (293.7, 0.22, 0.2), (293.7, 0.44, 0.2), (392.0, 0.66, 0.7), (370.0, 1.4, 0.35),
             (392.0, 1.78, 0.35), (440.0, 2.16, 0.35), (587.3, 2.55, 1.8)]
    horn = horn_call(notes, rng, layers=(1.0, 0.5), bright=1.1)
    pad = choir([semis(146.8, s) for s in (0, 7, 12, 16, 19)], 2.2, rng, attack=0.5) * 0.6
    drums = silence(4.6)
    for t in (0.0, 0.66, 1.4, 2.16, 2.55):
        drums = place(drums, taiko(1.0, rng, 70, 1.3), t)
    roll = silence(1.0)
    for i in range(10):
        roll = place(roll, taiko(0.4, rng, 95, 0.6) * (0.3 + i * 0.05), i * 0.06)
    bells = mix(*[place(silence(4.6), chime(f, 2.0, rng) * 0.25, 2.55 + i * 0.08) for i, f in enumerate((1174.7, 1480, 1760, 2349))])
    out = mix(horn, place(silence(4.6), pad, 2.4), drums * 0.8, place(silence(4.6), roll, 1.9), bells)
    return reverb(stereo(out, 0.7, rng=rng), 2.6, 0.3, rng=rng)


@sound("defeat", "waves", loud=-14.0, duck_db=-14.0, duck_time=5.0, **STING, description="the base falls and the run is lost")
def defeat(rng, v):
    horn = horn_call([(220.0, 0.0, 0.8), (207.7, 0.8, 0.8), (196.0, 1.6, 0.8), (146.8, 2.4, 2.2)], rng,
                     layers=(0.8, 0.8), bright=0.45)
    toll = mix(*[place(silence(5.5), bell(110, 3.0, rng) * 0.7, t) for t in (0.0, 1.6, 3.2)])
    pad = choir([semis(73.4, s) for s in (0, 3, 7, 12)], 3.2, rng, (570, 840, 2410), 1.0) * 0.6
    boomer = boom(2.5, rng, 1.6) * 0.5
    out = mix(horn, toll, place(silence(5.5), pad, 2.2), boomer)
    return reverb(stereo(out, 0.6, rng=rng), 3.2, 0.35, rng=rng)


# --- The base ----------------------------------------------------------------------------

@sound("base_hit", "base", variants=3, loud=-16.0, max_voices=2, min_gap=0.25, priority=4, positional=False,
       description="a monster gets through and the base takes damage")
def base_hit(rng, v):
    slam = mix(thump(0.9, 110, 38, 0.18, 0.6, rng) * 1.3, modal(0.6, [(170, 0.2, 1.0), (233, 0.15, 0.6), (420, 0.08, 0.4)], rng) * 0.5)
    crack = mix(debris(0.8, rng, 10, 0.6) * 0.5, lp(noise(0.3, rng), 2500) * decay(0.3, 0.05) * 0.7)
    alarm = mix(*[place(silence(1.2), bell(880, 0.6, rng, 0.5) * 0.35, 0.12 + i * 0.22) for i in range(3)])
    hurt = osc(sweep(330, 180, 0.5), 0.5, "saw") * decay(0.5, 0.2) * 0.12
    out = mix(slam, crack, alarm, lp(hurt, 1500))
    return reverb(stereo(out, 0.3, rng=rng), 1.2, 0.2, rng=rng)


@sound("base_hit_boss", "base", loud=-12.0, max_voices=1, priority=6, positional=False, duck_db=-10.0, duck_time=3.0,
       description="a boss breaks into the base")
def base_hit_boss(rng, v):
    smash = mix(boom(2.5, rng, 2.0), thump(2.0, 80, 25, 0.5, 0.8, rng))
    rubble = debris(2.5, rng, 40, 0.5) * 0.8
    alarm = mix(*[place(silence(3), bell(659, 1.0, rng) * 0.4, 0.2 + i * 0.3) for i in range(6)])
    out = mix(smash, rubble, alarm)
    return reverb(stereo(out, 0.6, rng=rng), 2.4, 0.3, rng=rng)


@sound("lives_low", "base", loud=-17.0, max_voices=1, priority=5, positional=False,
       description="warning: the base is nearly lost")
def lives_low(rng, v):
    out = silence(2.6)
    for i in range(3):
        beat = mix(thump(0.3, 70, 40, 0.06, 0.0) * 1.0, place(silence(0.4), thump(0.3, 65, 38, 0.05, 0.0) * 0.7, 0.18))
        out = place(out, beat, i * 0.75)
    bell_line = mix(*[place(silence(2.6), bell(587, 1.0, rng, 0.6) * 0.3, i * 0.75 + 0.05) for i in range(3)])
    return stereo(mix(out, bell_line), 0.3, rng=rng)


# --- Player skills ----------------------------------------------------------------------

@sound("skill_meteor", "skills", loud=-12.0, max_voices=1, priority=5, duck_db=-6.0, duck_time=2.0,
       description="Meteor: a burning rock falls from the sky")
def skill_meteor(rng, v):
    fall = whoosh(0.45, rng, 300, 2500, 1.5, [(0, 0), (0.4, 1), (0.45, 0.6)]) * 1.2
    scream = osc(sweep(1800, 500, 0.45), 0.45, "saw") * env([(0, 0), (0.4, 1), (0.45, 0)], 0.45) * 0.08
    impact = mix(boom(2.5, rng, 1.8) * 1.2, debris(2.5, rng, 40, 0.6) * 0.6, flourish("fire", 2.5, rng) * 0.6)
    out = place(mix(fall, lp(scream, 3000)), impact, 0.42)
    return reverb(stereo(out, 0.5, rng=rng), 2.2, 0.3, rng=rng)


@sound("skill_surge", "skills", loud=-13.0, max_voices=1, priority=5, positional=False, duck_db=-5.0, duck_time=2.0,
       description="Surge: every tower crackles with storm power")
def skill_surge(rng, v):
    charge = osc(sweep(80, 900, 0.7, power=2.0), 0.7, "saw") * env([(0, 0), (0.65, 1), (0.7, 0)], 0.7) * 0.25
    charge = lp(charge, 4000) + crackle(0.7, rng, sweep(20, 600, 0.7), 5000) * 0.6
    thunder = mix(hp(noise(0.1, rng), 800) * decay(0.1, 0.02) * 2, lp(noise(2.5, rng, "brown"), 300) * decay(2.5, 0.6) * 2.5)
    arcs = flourish("storm", 1.8, rng) * 0.7
    out = place(charge, mix(thunder, arcs), 0.68)
    return reverb(stereo(out, 0.8, rng=rng), 2.5, 0.3, rng=rng)


@sound("skill_entangle", "skills", loud=-14.0, max_voices=1, priority=5, description="Entangle: roots burst from the ground")
def skill_entangle(rng, v):
    burst = mix(thump(0.6, 120, 50, 0.1, 0.4, rng), lp(noise(0.5, rng, "brown"), 800) * decay(0.5, 0.12) * 1.2)
    creaks = silence(2.0)
    for i in range(6):
        c = resonate(trem(noise(0.4, rng), rng.uniform(25, 45), 0.95), sweep(rng.uniform(250, 400), rng.uniform(500, 900), 0.4), 10)
        creaks = place(creaks, c * env([(0, 0), (0.1, 1), (0.4, 0)], 0.4) * 2.5, 0.1 + i * 0.22)
    snaps = mix(*[place(silence(2.0), mix(modal(0.1, [(rng.uniform(600, 1200), 0.02, 1.0)], rng), hp(noise(0.03, rng), 2000) * decay(0.03, 0.005)), rng.uniform(0.1, 1.4)) for _ in range(8)]) * 0.6
    rustle = flourish("nature", 2.0, rng) * 0.6
    return reverb(stereo(mix(burst, creaks, snaps, rustle), 0.5, rng=rng), 1.4, 0.25, rng=rng)


@sound("skill_tidal_wave", "skills", loud=-12.0, max_voices=1, priority=5, positional=False, duck_db=-6.0, duck_time=3.0,
       description="Tidal Wave: a wave sweeps the road")
def skill_tidal_wave(rng, v):
    d = 3.5
    swell = svf(noise(d, rng, "pink"), sweep(200, 3000, d, power=0.6), 0.9, "low") * env([(0, 0), (1.2, 1), (1.5, 1.2), (d, 0)], d, 1.3) * 2
    crash = mix(boom(2.0, rng, 1.3) * 0.6, hp(noise(2.0, rng), 1500) * decay(2.0, 0.5) * 0.8)
    foam = bubbles(2.0, rng, 80, (600, 3000)) * decay(2.0, 0.8) * 0.6
    low = osc(sweep(45, 30, d), d) * env([(0, 0), (1.3, 1), (d, 0)], d) * 0.6
    left = mix(swell, low, place(silence(d), mix(crash, foam), 1.3))
    out = np.stack([left * np.linspace(1.2, 0.5, len(left)), left * np.linspace(0.5, 1.2, len(left))], axis=1)
    return reverb(out, 2.0, 0.3, rng=rng)


@sound("skill_earthquake", "skills", loud=-12.0, max_voices=1, priority=5, positional=False, duck_db=-6.0, duck_time=3.0,
       description="Earthquake: the ground shakes and cracks")
def skill_earthquake(rng, v):
    d = 3.2
    shake = rumble(d, rng, 90, 7) * env([(0, 0), (0.3, 1), (2.2, 1), (d, 0)], d) * 2.0
    sub = osc(32 + 4 * osc(5, d), d) * env([(0, 0), (0.3, 1), (d, 0)], d) * 0.8
    cracks = silence(d)
    for i in range(7):
        cracks = place(cracks, impact_earth(rng) * rng.uniform(0.4, 0.9), 0.1 + i * rng.uniform(0.25, 0.4))
    rocks = debris(d, rng, 60, 0.5) * 0.6
    return reverb(stereo(mix(shake, sub, cracks, rocks), 0.8, rng=rng), 2.0, 0.25, rng=rng)


@sound("skill_doom", "skills", loud=-13.0, max_voices=1, priority=5, duck_db=-6.0, duck_time=2.5,
       description="Doom: the void marks everything in an area")
def skill_doom(rng, v):
    d = 2.8
    suck = reverse(reverb(boom(1.0, rng, 1.0), 1.0, 0.6, rng=rng))[: n_of(1.0)] * 0.8
    pad = choir([semis(73.4, s) for s in (0, 1, 6, 12)], 2.2, rng, (400, 800, 2400), 0.15) * 0.8
    hit = mix(thump(1.5, 70, 28, 0.4, 0.3, rng) * 1.2, ring(resonate(noise(1.5, rng), 600, 3), 37) * decay(1.5, 0.4) * 0.6)
    out = mix(place(silence(d), suck, 0.0), place(silence(d), mix(hit, pad), 0.95))
    return reverb(stereo(out, 0.7, rng=rng), 3.0, 0.35, rng=rng)
