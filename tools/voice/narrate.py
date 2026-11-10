#!/usr/bin/env python3
"""Narrator voice for the story cinematics.

Reads data/story/cinematics/<id>.json and writes one Ogg Vorbis file per shot to
assets/story/voice/<id>/<NN>.ogg (NN = 01, 02, ...), which the cinematic player
picks up. Shots without "text" are skipped.

The voice is Kokoro-82M (Apache-2.0 weights, safe for a commercial Steam release),
run locally with kokoro-onnx, then mastered with ffmpeg to sound deeper and larger:
a small pitch drop, warmth in the low mids, a soft hall, loudness to -16 LUFS.

Setup (once):
    python3 -m venv .venv-voice
    .venv-voice/bin/pip install kokoro-onnx soundfile
    tools/voice/fetch_model.sh          # ~350 MB into tools/voice/model/ (git-ignored)

Use:
    .venv-voice/bin/python tools/voice/narrate.py                 # every cinematic
    .venv-voice/bin/python tools/voice/narrate.py opening         # one cinematic
    .venv-voice/bin/python tools/voice/narrate.py --text "Line" --out line.ogg
    .venv-voice/bin/python tools/voice/narrate.py --preset elder opening

Needs ffmpeg with the rubberband filter on PATH.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
MODEL_DIR = Path(__file__).resolve().parent / "model"
CINEMATICS = ROOT / "data" / "story" / "cinematics"
VOICE_OUT = ROOT / "assets" / "story" / "voice"

# Voice = weighted blend of Kokoro voice styles + delivery + mastering.
PRESETS = {
    # Low, calm, storybook-ancient. Kore is the lowest Kokoro female voice;
    # a little Nicole adds breath and intimacy.
    "elder": {
        "voices": {"af_kore": 0.7, "af_nicole": 0.3},
        "lang": "en-us", "speed": 0.82, "semitones": -1.5,
    },
    # Breathier, closer to the mic: for quiet or sad beats.
    "whisper": {
        "voices": {"af_nicole": 1.0},
        "lang": "en-us", "speed": 0.85, "semitones": -2.0,
    },
    # The narrator (chosen by Doctor Paris, 2026-11-11): British, crisp, regal.
    "regal": {
        "voices": {"bf_emma": 0.6, "af_kore": 0.4},
        "lang": "en-gb", "speed": 0.84, "semitones": -2.0,
    },
}

_kokoro = None


def kokoro():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        onnx, voices = MODEL_DIR / "kokoro-v1.0.onnx", MODEL_DIR / "voices-v1.0.bin"
        if not onnx.exists():
            sys.exit(f"Model missing: run tools/voice/fetch_model.sh (looked in {MODEL_DIR})")
        _kokoro = Kokoro(str(onnx), str(voices))
    return _kokoro


def style(preset: dict):
    k = kokoro()
    mix = None
    for name, weight in preset["voices"].items():
        s = k.get_voice_style(name) * weight
        mix = s if mix is None else mix + s
    return mix


def speak(text: str, preset: dict) -> tuple[np.ndarray, int]:
    """Raw speech. Blank lines in the text become longer, dramatic pauses."""
    k, voice = kokoro(), style(preset)
    out, sr = [], 24000
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    for i, para in enumerate(paras):
        samples, sr = k.create(" ".join(para.split()), voice=voice,
                               speed=preset["speed"], lang=preset["lang"])
        out.append(samples)
        if i < len(paras) - 1:
            out.append(np.zeros(int(sr * 0.9), dtype=samples.dtype))
    return np.concatenate(out), sr


def master(wav_in: Path, ogg_out: Path, preset: dict) -> None:
    pitch = 2 ** (preset["semitones"] / 12)
    chain = ",".join([
        f"rubberband=pitch={pitch:.4f}:formant=preserved",
        "highpass=f=60",
        "lowshelf=f=180:g=3",              # chest
        "equalizer=f=3200:t=q:w=1.2:g=-2",  # soften synthetic edge
        "equalizer=f=8000:t=q:w=1:g=1.5",   # air
        "acompressor=threshold=-20dB:ratio=3:attack=10:release=200",
        "aecho=0.8:0.5:60|110|170:0.22|0.15|0.09",  # small stone hall
        "apad=pad_dur=0.6",
        "loudnorm=I=-16:TP=-1.5:LRA=9",
        "aresample=44100",
    ])
    with tempfile.TemporaryDirectory() as tmp:
        mastered = Path(tmp) / "m.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav_in),
                        "-af", chain, "-ac", "1", str(mastered)], check=True)
        data, sr = sf.read(mastered)
        ogg_out.parent.mkdir(parents=True, exist_ok=True)
        # libsndfile's Vorbis encoder can crash on one huge write: feed it in blocks.
        with sf.SoundFile(ogg_out, "w", sr, 1, format="OGG", subtype="VORBIS") as f:
            for i in range(0, len(data), 8192):
                f.write(data[i:i + 8192].astype(np.float32))


def render(text: str, out: Path, preset: dict) -> float:
    samples, sr = speak(text, preset)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw.wav"
        sf.write(raw, samples, sr)
        master(raw, out, preset)
    return sf.info(out).duration


def shots_of(doc) -> list[dict]:
    if isinstance(doc, list):
        return [s for s in doc if isinstance(s, dict)]
    for key in ("shots", "lines", "beats"):
        if isinstance(doc.get(key), list):
            return doc[key]
    return []


def narrate_cinematic(path: Path, preset_name: str) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    cid = doc.get("id", path.stem) if isinstance(doc, dict) else path.stem
    out_dir = VOICE_OUT / cid
    for n, shot in enumerate(shots_of(doc), start=1):
        text = (shot.get("text") or "").strip()
        if not text or shot.get("voice") is False:
            continue
        preset = PRESETS[shot.get("voice_preset", preset_name)]
        out = out_dir / f"{n:02d}.ogg"
        secs = render(text, out, preset)
        print(f"{out.relative_to(ROOT)}  {secs:5.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cinematics", nargs="*", help="cinematic ids (default: all)")
    ap.add_argument("--preset", default="regal", choices=sorted(PRESETS))
    ap.add_argument("--text", help="speak this text instead of cinematics")
    ap.add_argument("--out", type=Path, help="output .ogg for --text")
    args = ap.parse_args()

    if args.text:
        out = args.out or Path("narration.ogg")
        print(f"{out}  {render(args.text.replace('\\n', '\n'), out, PRESETS[args.preset]):.1f}s")
        return
    files = sorted(CINEMATICS.glob("*.json"))
    if args.cinematics:
        files = [CINEMATICS / f"{c}.json" for c in args.cinematics]
    if not files:
        sys.exit(f"No cinematics found in {CINEMATICS}")
    for f in files:
        narrate_cinematic(f, args.preset)


if __name__ == "__main__":
    main()
