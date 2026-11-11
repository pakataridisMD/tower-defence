"""Render seamless, layered music loops for gameplay.

    python3 tools/music/render_loop.py battle            # tools/music/loops/battle.py
    python3 tools/music/render_loop.py battle --stems    # also write each part as a WAV

A loop module defines LAYERS (names, quietest first) and build(layer) -> Score. Every layer's
score has the same sections, so the layers line up sample for sample and the game can play them
together and fade each in and out. The reverb tail after the loop end is folded back onto the
start, so the loop has no seam. All layers get the same gain (set so the full mix reaches LUFS)
and the same peak limiting, so any combination of them sums correctly.

Writes assets/game/music/<loop>_<layer>.ogg and <loop>.json (loop length, tempo, layers, section
markers). MP3 previews of each layer combination go to tools/music/out/.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import subprocess
import sys
import time

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import score as sc  # noqa: E402
from orchestra import SR  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(ROOT, "assets", "game", "music")
OUT = os.path.join(HERE, "out")
LUFS = -16.0
CEILING = 0.85  # about -1.4 dBFS sample peak, leaves room for Vorbis overshoot


def loudness(x: np.ndarray) -> float:
    path = os.path.join(OUT, "_measure.wav")
    sf.write(path, x, SR, subtype="FLOAT")
    err = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    os.remove(path)
    line = [l for l in err.splitlines() if l.strip().startswith("I:")][-1]
    return float(line.split()[1])


def limiter_gain(x: np.ndarray, ceiling: float, release: float = 0.12, look: float = 0.005) -> np.ndarray:
    """Gain envelope (<= 1) that keeps x under the ceiling: instant attack with lookahead, smooth
    release. Applied identically to every layer."""
    peak = np.abs(x).max(axis=1)
    need = np.minimum(1.0, ceiling / np.maximum(peak, 1e-9))
    k = int(look * SR)
    # lookahead: each sample takes the smallest gain needed in the next k samples
    from scipy.ndimage import minimum_filter1d
    need = minimum_filter1d(need, size=2 * k + 1, origin=0)
    g = np.empty_like(need)
    a = np.exp(-1.0 / (release * SR))
    cur = 1.0
    for i in range(len(need)):  # simple one-pole release
        cur = need[i] if need[i] < cur else need[i] + (cur - need[i]) * a
        g[i] = cur
    return g.astype(np.float32)


def fold(x: np.ndarray, n: int) -> np.ndarray:
    """Wrap everything after sample n (reverb and release tails) back onto the start."""
    y = x[:n].copy()
    rest = x[n:]
    while len(rest):
        m = min(n, len(rest))
        y[:m] += rest[:m]
        rest = rest[m:]
    return y


def encode(wav: str, base: str):
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", wav, "-c:a", "libvorbis", "-q:a", "6",
                    base + ".ogg"], check=True)


def preview(x: np.ndarray, path: str, loops: int = 1):
    tmp = path + ".wav"
    sf.write(tmp, np.concatenate([x] * loops), SR, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", tmp, "-c:a", "libmp3lame", "-b:a", "192k", path],
                   check=True)
    os.remove(tmp)


def render(name: str, stems: bool = False):
    t0 = time.time()
    mod = importlib.import_module(f"loops.{name}")
    layers = {}
    first = None
    os.makedirs(ASSETS, exist_ok=True)
    for layer in mod.LAYERS:
        s = mod.build(layer)
        first = first or s
        sc.export_midi(s, os.path.join(ASSETS, f"{name}_{layer}.mid"))
        n = int(round(s.time_of(s.total_beats) * SR))
        y = sc.mix_array(s, OUT, stems)
        if getattr(mod, "ONESHOT", False):
            # a one-shot keeps its tail and fades out its last half second
            k = int(0.5 * SR)
            y[-k:] *= np.linspace(1, 0, k)[:, None]
            layers[layer] = y * 10 ** (getattr(mod, "LAYER_DB", {}).get(layer, 0.0) / 20)
            continue
        layers[layer] = fold(y, n) * 10 ** (getattr(mod, "LAYER_DB", {}).get(layer, 0.0) / 20)
        print(f"  {layer}: rendered")
    full = sum(layers.values())
    gain = 10 ** ((getattr(mod, "LUFS", LUFS) - loudness(full)) / 20)
    env = limiter_gain(full * gain, CEILING)
    os.makedirs(ASSETS, exist_ok=True)
    for layer, y in layers.items():
        y = y * gain * env[:, None]
        layers[layer] = y
        wav = os.path.join(OUT, f"{name}_{layer}.wav")
        sf.write(wav, y, SR, subtype="PCM_16")
        encode(wav, os.path.join(ASSETS, f"{name}_{layer}"))
    # previews: each layer added in turn, two times round so the seam is heard
    acc = np.zeros_like(full)
    for layer in mod.LAYERS:
        acc = acc + layers[layer]
        preview(acc, os.path.join(OUT, f"{name}_upto_{layer}.mp3"),
                loops=1 if getattr(mod, "ONESHOT", False) else 2)
    sheet = sc.cue_sheet(first)
    oneshot = getattr(mod, "ONESHOT", False)
    body = first.time_of(first.total_beats)
    sheet.update({"loop": not oneshot, "loop_seconds": round(len(full) / SR, 4), "loop_samples": len(full),
                  "handover_seconds": round(body, 4),
                  "bpm": first.sections[0].bpm, "layers": list(mod.LAYERS),
                  "files": {l: f"{name}_{l}.ogg" for l in mod.LAYERS}})
    sheet["duration"] = sheet["loop_seconds"]
    with open(os.path.join(ASSETS, f"{name}.json"), "w") as fh:
        json.dump(sheet, fh, indent=2)
        fh.write("\n")
    print(f"{name}: {len(full) / SR:.2f}s loop, {len(layers)} layers, peak reduction "
          f"{20 * np.log10(env.min()):.1f} dB, rendered in {time.time() - t0:.0f}s")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("loops", nargs="+")
    ap.add_argument("--stems", action="store_true")
    a = ap.parse_args()
    for n in a.loops:
        render(n, a.stems)


if __name__ == "__main__":
    main()
