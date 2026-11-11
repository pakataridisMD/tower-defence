"""Render story music cues.

    python3 tools/music/render.py prologue            # one cue
    python3 tools/music/render.py --all               # every cue in cues/
    python3 tools/music/render.py prologue --stems    # also write each part as a WAV

Writes assets/story/music/<cue>.ogg (what the game plays), plus <cue>.mid (the score as MIDI)
and <cue>.json (length and section markers) next to it. MP3 previews go to tools/music/out/.
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import score as sc  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
ASSETS = os.path.join(ROOT, "assets", "story", "music")
OUT = os.path.join(HERE, "out")
LUFS = -18.0  # leaves room for the narrator on top


def cue_names():
    return sorted(f[:-3] for f in os.listdir(os.path.join(HERE, "cues")) if f.endswith(".py") and not f.startswith("_"))


def render(name: str, stems: bool = False) -> dict:
    t0 = time.time()
    mod = importlib.import_module(f"cues.{name}")
    score = mod.build()
    raw = sc.mix(score, OUT, stems=stems)
    files = sc.master(raw, os.path.join(OUT, name), getattr(mod, "LUFS", LUFS))
    os.remove(raw)
    os.makedirs(ASSETS, exist_ok=True)
    shutil.copy(files["ogg"], os.path.join(ASSETS, f"{name}.ogg"))
    sc.export_midi(score, os.path.join(ASSETS, f"{name}.mid"))
    sheet = sc.cue_sheet(score)
    with open(os.path.join(ASSETS, f"{name}.json"), "w") as fh:
        json.dump(sheet, fh, indent=2)
        fh.write("\n")
    print(f"{name}: {sheet['duration']:.1f}s rendered in {time.time() - t0:.0f}s -> {files['mp3']}")
    return files


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cues", nargs="*")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--stems", action="store_true")
    a = ap.parse_args()
    for n in (cue_names() if a.all else a.cues):
        render(n, a.stems)


if __name__ == "__main__":
    main()
