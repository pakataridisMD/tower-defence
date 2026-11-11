#!/usr/bin/env python3
"""Renders every sound effect of the game from its recipe.

    python3 tools/sfx/build.py                 # everything, into assets/audio/sfx
    python3 tools/sfx/build.py --only boss_    # names containing boss_
    python3 tools/sfx/build.py --preview DIR   # also MP3 copies and an index for a listening page
    python3 tools/sfx/build.py --list          # print the catalogue

Writes assets/audio/sfx/<group>/<name>[_<n>].ogg and assets/audio/sfx/catalogue.json, which the
Sfx autoload reads. Every sound is synthesised here from scratch (see dsp.py), so the output is
original work owned by the project. Rendering is deterministic: the same code gives the same files.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import zlib
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
from scipy.ndimage import minimum_filter1d

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from dsp import SR, dc_block, fade, trim  # noqa: E402
from registry import SOUNDS, Spec  # noqa: E402
import recipes  # noqa: E402,F401  (registers every sound)

ROOT = HERE.parent.parent
OUT = ROOT / "assets" / "audio" / "sfx"
CEILING_DB = -1.0


def k_weight(x: np.ndarray) -> np.ndarray:
    """ITU-R BS.1770 K-weighting (pre-filter shelf and RLB high-pass) at 44.1 kHz."""
    b1 = [1.53090959, -2.65116903, 1.16916686]
    a1 = [1.0, -1.66375011, 0.71265753]
    b2 = [1.0, -2.0, 1.0]
    a2 = [1.0, -1.98998549, 0.99003355]
    y = signal.lfilter(b1, a1, x, axis=0)
    return signal.lfilter(b2, a2, y, axis=0)


def loudness(x: np.ndarray, window: float = 0.2) -> float:
    """Loudest 200 ms of the sound, in LUFS-like units."""
    y = k_weight(x)
    power = y ** 2 if y.ndim == 1 else np.sum(y ** 2, axis=1)
    w = int(window * SR)
    if len(power) < w:
        power = np.concatenate([power, np.zeros(w - len(power))])
    csum = np.concatenate([[0.0], np.cumsum(power)])
    hop = max(1, w // 4)
    means = (csum[w::hop] - csum[:-w:hop]) / w
    return -0.691 + 10 * np.log10(np.max(means) + 1e-12)


def limit(x: np.ndarray, ceiling_db: float = CEILING_DB) -> np.ndarray:
    """Soft-knee peak limiter: gain follows a smoothed envelope so peaks never pass the ceiling."""
    ceiling = 10 ** (ceiling_db / 20)
    mono = np.abs(x) if x.ndim == 1 else np.max(np.abs(x), axis=1)
    if mono.max() <= ceiling:
        return x
    need = np.minimum(1.0, ceiling / np.maximum(mono, 1e-9))
    # Hold the gain reduction a few ms around each peak, then release smoothly.
    hold = int(0.004 * SR)
    gain = minimum_filter1d(need, size=hold * 2 + 1)
    rel = np.exp(-1.0 / (0.05 * SR))
    smooth = signal.lfilter([1 - rel], [1, -rel], gain - 1.0) + 1.0
    gain = np.minimum(gain, smooth)
    gain = minimum_filter1d(gain, size=hold)
    y = (x.T * gain).T
    return np.clip(y, -ceiling, ceiling)


def finish(spec: Spec, x: np.ndarray) -> np.ndarray:
    x = np.nan_to_num(np.asarray(x, dtype=float))
    x = dc_block(x)
    x = trim(x, -62.0, 0.04)
    peak = np.max(np.abs(x)) + 1e-12
    x = x / peak * 0.5
    x *= 10 ** ((spec.loud - loudness(x)) / 20)
    x = limit(x)
    return fade(x, 0.0008, 0.02)


def file_names(spec: Spec) -> list[str]:
    if spec.variants == 1:
        return [f"{spec.group}/{spec.name}.ogg"]
    return [f"{spec.group}/{spec.name}_{i + 1}.ogg" for i in range(spec.variants)]


def render_one(job: tuple[str, int, str, str | None]) -> dict:
    name, variant, rel, preview = job
    spec = SOUNDS[name]
    seed = zlib.crc32(f"{name}:{variant}".encode())
    rng = np.random.default_rng(seed)
    x = finish(spec, spec.recipe(rng, variant))
    path = OUT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "x.wav"
        sf.write(wav, x.astype(np.float32), SR, subtype="PCM_16")
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-c:a", "libvorbis",
                        "-q:a", "5", "-map_metadata", "-1", "-fflags", "+bitexact", str(path)], check=True)
        if preview:
            mp3 = Path(preview) / rel.replace(".ogg", ".mp3")
            mp3.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-c:a", "libmp3lame",
                            "-q:a", "6", str(mp3)], check=True)
    peak = float(np.max(np.abs(x)))
    return {"file": rel, "seconds": round(len(x) / SR, 3), "peak_db": round(20 * np.log10(peak + 1e-12), 1),
            "loud": round(loudness(x), 1), "channels": 1 if x.ndim == 1 else 2}


def catalogue() -> dict:
    from recipes.bosses import boss_sets
    from recipes.combat import ENEMY_DEATHS
    out = {}
    for spec in SOUNDS.values():
        out[spec.name] = {
            "files": file_names(spec),
            "bus": spec.bus,
            "volume_db": spec.volume_db,
            "positional": spec.positional,
            "max_voices": spec.max_voices,
            "min_gap": spec.min_gap,
            "pitch_jitter": spec.pitch_jitter,
            "priority": spec.priority,
            "duck_db": spec.duck_db,
            "duck_time": spec.duck_time,
        }
    return {"sounds": out, "boss_sets": boss_sets(), "enemy_deaths": ENEMY_DEATHS}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="", help="render only names containing this text (comma list)")
    ap.add_argument("--preview", default=None, help="folder for MP3 previews and preview.json")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--jobs", type=int, default=os.cpu_count() or 2)
    args = ap.parse_args()

    if args.list:
        for spec in SOUNDS.values():
            print(f"{spec.group:10s} {spec.name:32s} x{spec.variants}  {spec.description}")
        print(f"{len(SOUNDS)} sounds, {sum(s.variants for s in SOUNDS.values())} files")
        return

    keys = [k for k in args.only.split(",") if k]
    jobs = []
    for spec in SOUNDS.values():
        if keys and not any(k in spec.name for k in keys):
            continue
        for i, rel in enumerate(file_names(spec)):
            jobs.append((spec.name, i, rel, args.preview))
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        for job, res in zip(jobs, pool.map(render_one, jobs)):
            results[job[2]] = res
            print(f"{res['file']:48s} {res['seconds']:6.2f}s  peak {res['peak_db']:6.1f} dB  loud {res['loud']:6.1f}")

    if not keys:
        # Drop files of sounds that no longer exist.
        wanted = {rel for spec in SOUNDS.values() for rel in file_names(spec)}
        for path in OUT.rglob("*.ogg"):
            rel = path.relative_to(OUT).as_posix()
            if rel not in wanted:
                path.unlink()
                imp = path.with_suffix(".ogg.import")
                if imp.exists():
                    imp.unlink()
    (OUT / "catalogue.json").write_text(json.dumps(catalogue(), indent=1, sort_keys=True) + "\n")

    if args.preview:
        index_path = Path(args.preview) / "preview.json"
        old = json.loads(index_path.read_text()) if index_path.exists() else {}
        for spec in SOUNDS.values():
            files = [results.get(rel) or old.get(spec.name, {}).get("files", {}).get(rel)
                     for rel in file_names(spec)]
            if any(f is None for f in files):
                continue
            old[spec.name] = {"group": spec.group, "description": spec.description,
                              "files": {f["file"]: f for f in files}}
        index_path.write_text(json.dumps(old, indent=1))
    print(f"{len(jobs)} files rendered")


if __name__ == "__main__":
    main()
