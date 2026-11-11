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
import re
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
# Optional keys: "semitones" (pitch shift; sounds robotic, avoid), "room" (hall wetness, default 0.16),
# "rt60" (hall length in seconds, default 1.1).
PRESETS = {
    # Low, calm, storybook-ancient. Kore is the lowest Kokoro female voice;
    # a little Nicole adds breath and intimacy.
    "elder": {
        "voices": {"af_kore": 0.7, "af_nicole": 0.3},
        "lang": "en-us", "speed": 0.88,
    },
    # Breathier, closer to the mic: for quiet or sad beats.
    "whisper": {
        "voices": {"af_nicole": 1.0},
        "lang": "en-us", "speed": 0.9, "room": 0.1,
    },
    # The narrator (chosen by Doctor Paris, 2026-11-11): British, crisp, regal.
    "regal": {
        "voices": {"bf_emma": 0.6, "af_kore": 0.4},
        "lang": "en-gb", "speed": 0.88, "room": 0.2, "rt60": 1.6,
    },
    # Warmer and more British, same cinematic hall: the other finalist.
    "warm": {
        "voices": {"bf_emma": 0.8, "af_kore": 0.2},
        "lang": "en-gb", "speed": 0.9, "room": 0.2, "rt60": 1.6,
    },
}

# Speaker ids voiced by the narrator. Queen Ysolde is the narrator, so her
# in-scene lines use the same voice.
NARRATOR_SPEAKERS = {"narrator", "ysolde"}

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


SENTENCE_GAP = 0.32   # seconds between sentences
PARAGRAPH_GAP = 0.9   # seconds for a blank line in the text


def _trim(x: np.ndarray, sr: int, floor: float = 0.004) -> np.ndarray:
    """Cut the model's own leading/trailing silence so our pauses are exact."""
    loud = np.flatnonzero(np.abs(x) > floor)
    if loud.size == 0:
        return x[:0]
    pad = int(sr * 0.03)
    return x[max(0, loud[0] - pad): loud[-1] + pad]


def speak(text: str, preset: dict) -> tuple[np.ndarray, int]:
    """Raw speech, one sentence at a time with natural breaths between them.
    A blank line in the text becomes a longer, dramatic pause."""
    k, voice = kokoro(), style(preset)
    out, sr = [], 24000
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    for pi, para in enumerate(paras):
        sentences = [x for x in re.split(r"(?<=[.!?])\s+", " ".join(para.split())) if x]
        for si, sentence in enumerate(sentences):
            samples, sr = k.create(sentence, voice=voice, speed=preset["speed"], lang=preset["lang"])
            out.append(_trim(samples, sr))
            last_in_para = si == len(sentences) - 1
            if not (last_in_para and pi == len(paras) - 1):
                gap = PARAGRAPH_GAP if last_in_para else SENTENCE_GAP
                out.append(np.zeros(int(sr * gap), dtype=np.float32))
    return np.concatenate(out).astype(np.float32), sr


def _room(x: np.ndarray, sr: int, rt60: float = 1.1, wet: float = 0.16) -> np.ndarray:
    """A soft, dark hall: convolution with decaying filtered noise. Unlike a
    few discrete echoes, this has no metallic ring."""
    rng = np.random.default_rng(7)
    n = int(sr * rt60 * 1.2)
    t = np.arange(n) / sr
    ir = rng.standard_normal(n) * np.exp(-6.91 * t / rt60)
    ir = np.convolve(ir, np.ones(12) / 12, mode="same")    # darken the tail
    ir = np.concatenate([np.zeros(int(sr * 0.025)), ir])   # 25 ms pre-delay
    ir /= np.sqrt(np.sum(ir ** 2))
    size = len(x) + len(ir) - 1
    nfft = 1 << (size - 1).bit_length()
    tail = np.fft.irfft(np.fft.rfft(x, nfft) * np.fft.rfft(ir, nfft), nfft)[:size]
    dry = np.concatenate([x, np.zeros(len(ir) - 1)])
    y = dry + wet * tail * (np.max(np.abs(x)) / (np.max(np.abs(tail)) + 1e-9))
    # Faint, dark room tone so pauses aren't digital dead air.
    tone = np.convolve(rng.standard_normal(len(y)), np.ones(40) / 40, mode="same")
    return y + tone * np.max(np.abs(x)) * 10 ** (-58 / 20) / (np.std(tone) + 1e-9)


def master(wav_in: Path, ogg_out: Path, preset: dict) -> None:
    filters = []
    if preset.get("semitones"):  # pitch shifting adds a robotic edge; avoid if possible
        filters.append(f"rubberband=pitch={2 ** (preset['semitones'] / 12):.4f}:formant=preserved")
    filters += [
        "highpass=f=70",
        "lowshelf=f=200:g=2",                # warmth
        "equalizer=f=5500:t=q:w=2:g=-2.5",    # tame the synthetic fizz/sibilance
        "lowpass=f=12500",                    # remove vocoder hiss above the voice
        "acompressor=threshold=-22dB:ratio=2:attack=20:release=250",
        "apad=pad_dur=0.6",
        "loudnorm=I=-16:TP=-1.5:LRA=11",
        "aresample=44100",
    ]
    with tempfile.TemporaryDirectory() as tmp:
        x, sr = sf.read(wav_in)
        roomy = Path(tmp) / "room.wav"
        sf.write(roomy, _room(x, sr, rt60=preset.get("rt60", 1.1), wet=preset.get("room", 0.16)),
                 sr, subtype="FLOAT")
        mastered = Path(tmp) / "m.wav"
        subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(roomy),
                        "-af", ",".join(filters), "-ac", "1", str(mastered)], check=True)
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


def narrate_cinematic(path: Path, preset_name: str, out_root: Path = VOICE_OUT) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    cid = doc.get("id", path.stem) if isinstance(doc, dict) else path.stem
    out_dir = out_root / cid
    for n, shot in enumerate(shots_of(doc), start=1):
        text = (shot.get("text") or "").strip()
        if not text or shot.get("voice") is False:
            continue
        if shot.get("speaker", "narrator") not in NARRATOR_SPEAKERS:
            continue  # other characters stay as subtitles until they get voices
        preset = PRESETS[shot.get("voice_preset", preset_name)]
        out = out_dir / f"{n:02d}.ogg"
        secs = render(text, out, preset)
        print(f"{out}  {secs:5.1f}s")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("cinematics", nargs="*", help="cinematic ids (default: all)")
    ap.add_argument("--preset", default="regal", choices=sorted(PRESETS))
    ap.add_argument("--text", help="speak this text instead of cinematics")
    ap.add_argument("--out", type=Path, help="output .ogg for --text, or output root for cinematics")
    ap.add_argument("--scripts", type=Path, default=CINEMATICS, help="folder of cinematic .json files")
    args = ap.parse_args()

    if args.text:
        out = args.out or Path("narration.ogg")
        print(f"{out}  {render(args.text.replace('\\n', '\n'), out, PRESETS[args.preset]):.1f}s")
        return
    files = sorted(args.scripts.glob("*.json"))
    if args.cinematics:
        files = [args.scripts / f"{c}.json" for c in args.cinematics]
    if not files:
        sys.exit(f"No cinematics found in {args.scripts}")
    for f in files:
        narrate_cinematic(f, args.preset, args.out or VOICE_OUT)


if __name__ == "__main__":
    main()
