#!/usr/bin/env python3
"""The studio splash's sound: one file cut to the splash's timeline (scripts/ui/splash/studio_splash.gd).

    python3 tools/sfx/intro.py            # writes assets/audio/intro/studio_intro.ogg
    python3 tools/sfx/intro.py --mp3 DIR  # also an MP3 copy to listen to

  0.00  silence, a low drone creeping in
  0.55  the fuse catches: a flare, then a spitting, crackling hiss that runs to the bomb
        (panned from the right, where the fuse starts, to the centre), over a cymbal swell and a
        reversed crash that suck up into the blast; the hiss cuts out just before it
  2.60  the blast: a cracking transient, a sub drop, a giant drum, concert bass drum, timpani, crash
        and tam-tam from real recordings, a roaring noise body, iron shrapnel and a long rumble
  2.95  the studio's name is forged: a low brass braam (tuba, trombones, horns) on D with a
        bowed tam-tam, ringing out as the name cools
  6.50  everything fades with the picture by 7.2

Same sources as the other sound effects (see README.md): VSCO 2 CE recordings (CC0) and code-made
noise. Deterministic: the same code gives the same file.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.ndimage import minimum_filter1d

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import kit as K  # noqa: E402
from dsp import (SR, crackle, dc_block, decay, drive, env, hp, lp, mix, n_of, noise, place, reverb,  # noqa: E402
                 rumble, silence, stereo, sweep, svf, thump)
from dsp import debris as fine_debris  # noqa: E402

OUT = HERE.parent.parent / "assets" / "audio" / "intro" / "studio_intro.ogg"

# Must match StudioSplash.
FUSE_LIT = 0.55
HIT = 2.6
LOGO_IN = 2.95
FADE_OUT = 6.5
LENGTH = 7.2


def pan_track(x: np.ndarray, pans: np.ndarray) -> np.ndarray:
    """Mono to stereo with a pan that moves over time (-1 left .. 1 right)."""
    p = np.clip(pans, -1, 1)
    return np.stack([x * np.sqrt(0.5 * (1 - p)) * 1.414, x * np.sqrt(0.5 * (1 + p)) * 1.414], axis=1)


def shaped(x: np.ndarray, points: list[tuple[float, float]], curve: float = 1.0) -> np.ndarray:
    """x times an envelope given in seconds; silent after the last point."""
    e = env(points, points[-1][0], curve)
    e = np.concatenate([e, np.zeros(max(0, len(x) - len(e)))])[: len(x)]
    return x * (e[:, None] if x.ndim == 2 else e)


def fuse(rng: np.random.Generator) -> np.ndarray:
    seconds = HIT - FUSE_LIT
    burn = seconds - 0.1  # the hiss stops a moment before the blast: the breath before the bang
    # the flare as it catches
    flare = svf(noise(0.5, rng, "pink"), sweep(9000, 2500, 0.5), 0.9, "band") * env(
        [(0, 0), (0.01, 1), (0.08, 0.5), (0.5, 0)], 0.5) * 2.2
    flare = mix(flare, lp(noise(0.4, rng, "brown"), 300) * env([(0, 0), (0.03, 1), (0.4, 0)], 0.4) * 2.0)
    # the hiss: bright noise that sputters, with sparks spitting
    hiss = lp(svf(noise(burn, rng, "white"), 4200, 0.6, "band"), 9000) * 0.45
    hiss += svf(noise(burn, rng, "pink"), 1700, 0.8, "band") * 0.45
    sputter = np.repeat(rng.uniform(0.45, 1.0, int(burn * 60) + 1), n_of(1 / 60))[: n_of(burn)]
    sputter = lp(sputter, 30)
    hiss *= sputter
    spits = crackle(burn, rng, 70.0, 5500.0) * 0.9 + crackle(burn, rng, 18.0, 2500.0) * 0.6
    body = (hiss + spits) * env([(0, 0.6), (burn * 0.8, 1.0), (burn - 0.02, 1.0), (burn, 0)], burn)
    # the fuse tip runs from the right towards the bomb in the middle
    moving = pan_track(body, np.linspace(0.45, 0.0, len(body)))
    out = place(silence(seconds), stereo(flare, 0.3, 0.45), 0.0)
    return place(out, moving, 0.0)


def tension(rng: np.random.Generator) -> np.ndarray:
    """A low drone under the fuse and the suck into the blast."""
    lead = HIT
    drone = K.held("bass_trem", 26 + 12, lead, rng, attack=1.2, release=0.05) * 0.55
    drone = mix(drone, K.held("cello_trem", 38 + 12, lead, rng, attack=1.6, release=0.05) * 0.3)
    drone = shaped(drone, [(0, 0), (lead * 0.5, 0.6), (lead - 0.12, 1.0), (lead, 0)])
    out = place(silence(lead), stereo(drone, 0.7, rng=rng), 0.0)
    rise = 1.6
    out = place(out, K.riser(rise, rng) * 0.6, lead - rise)
    return out


def blast(rng: np.random.Generator) -> np.ndarray:
    seconds = LENGTH - HIT + 1.0
    out = silence(seconds)
    # the crack: a few milliseconds of hard, bright pressure
    crack = drive(hp(noise(0.04, rng, "white"), 900) * decay(0.04, 0.006, 0.0) * 3.0, 2.5)
    out = place(out, stereo(crack, 0.4), 0.0, 1.0)
    # the weight: sub drop and a low thump
    out = place(out, stereo(K.sub(4.5, 64, 22, 1.0) * 1.1), 0.0)
    out = place(out, stereo(thump(1.2, 120, 34, 0.22, 0.6, rng) * 1.0), 0.0)
    # the drums and metal (real recordings)
    out = place(out, K.impact(rng, size=1.6, metal_level=0.7, crash_level=0.9, gong_level=0.7, st=-1.0) * 1.1, 0.0)
    out = place(out, stereo(K.giant(rng, -7) * 0.7, 0.6, rng=rng), 0.015)
    # the roar: noise whose top end closes as the fireball cools
    roar_s = 3.2
    roar = svf(noise(roar_s, rng, "pink"), sweep(9000, 180, roar_s, power=0.35), 0.8, "low")
    roar *= env([(0, 0), (0.006, 1.0), (0.25, 0.7), (1.0, 0.3), (roar_s, 0)], roar_s, 1.6) * 2.2
    out = place(out, stereo(drive(roar, 1.5), 0.9, rng=rng), 0.0)
    # rumble rolling away
    rum = rumble(5.0, rng, 110, 2.0) * env([(0, 0), (0.1, 1.0), (1.5, 0.7), (5.0, 0)], 5.0) * 1.6
    out = place(out, stereo(rum, 0.8, rng=rng), 0.05)
    # crackle of burning and the shrapnel coming down
    burn = crackle(3.5, rng, sweep(160, 8, 3.5), 3500) * decay(3.5, 0.9, 0.01) * 0.5
    out = place(out, stereo(burn, 0.9, rng=rng), 0.05)
    out = place(out, K.debris(rng, 3.0, count=14, st=-2) * 0.9, 0.35)
    out = place(out, stereo(fine_debris(2.5, rng, 26, 0.8, 2500), 0.9, rng=rng) * 0.45, 0.25)
    return out


def forge(rng: np.random.Generator) -> np.ndarray:
    """The name forged in the fire: a dark brass braam and a bowed tam-tam."""
    seconds = LENGTH - LOGO_IN + 0.5
    braam = K.braam(26 + 12, 3.2, rng, dark=1.0)
    braam = shaped(braam, [(0, 0), (0.05, 1.0), (1.2, 0.6), (3.2, 0)], 1.3)
    out = place(silence(seconds), stereo(braam, 0.6, rng=rng) * 0.9, 0.0)
    bowed = K.bowed(rng, -3)
    out = place(out, stereo(bowed, 0.8, rng=rng) * 0.5, 0.15)
    out = place(out, stereo(K.tam_tam(rng, -6), 0.8, rng=rng) * 0.35, 0.0)
    return out


def limit(x: np.ndarray, ceiling: float = 0.89, release: float = 0.15) -> np.ndarray:
    peak = np.max(np.abs(x), axis=1)
    need = minimum_filter1d(np.minimum(1.0, ceiling / np.maximum(peak, 1e-9)), size=n_of(0.004) * 2 + 1)
    g = np.empty_like(need)
    a = np.exp(-1.0 / (release * SR))
    cur = 1.0
    for i in range(len(need)):
        cur = need[i] if need[i] < cur else need[i] + (cur - need[i]) * a
        g[i] = cur
    return x * g[:, None]


def render() -> np.ndarray:
    rng = np.random.default_rng(20261112)
    out = silence(LENGTH)
    out = place(out, tension(rng) * 0.8, 0.0)
    out = place(out, fuse(rng) * 0.6, FUSE_LIT)
    out = place(out, reverb(blast(rng), 3.4, 0.28, damp=5000, rng=rng, wide=True), HIT)
    out = place(out, reverb(forge(rng), 3.0, 0.3, damp=6000, rng=rng, wide=True) * 0.8, LOGO_IN)
    if out.ndim == 1:
        out = np.stack([out, out], axis=1)
    out = dc_block(out) if out.ndim == 1 else np.stack([dc_block(out[:, 0]), dc_block(out[:, 1])], axis=1)
    out = out[: n_of(LENGTH)]
    fade = env([(0, 1), (FADE_OUT, 1), (LENGTH, 0)], LENGTH, 1.5)[: len(out)]
    out = out * fade[:, None]
    # the blast is the loudest moment of the game's opening: peaks to -1 dBFS
    out = out / (np.max(np.abs(out)) + 1e-9) * 1.12
    return limit(out)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mp3", help="also write an MP3 copy into this folder")
    a = ap.parse_args()
    x = render()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = os.path.join(tmp, "intro.wav")
        sf.write(wav, x.astype(np.float32), SR, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "7",
                        str(OUT)], check=True)
        if a.mp3:
            os.makedirs(a.mp3, exist_ok=True)
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libmp3lame", "-b:a", "224k",
                            os.path.join(a.mp3, "studio_intro.mp3")], check=True)
    print(f"{OUT.relative_to(HERE.parent.parent)}: {len(x) / SR:.2f}s, peak {20 * np.log10(np.abs(x).max()):.1f} dBFS")


if __name__ == "__main__":
    main()
