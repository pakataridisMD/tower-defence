#!/usr/bin/env python3
"""Record what the bosses say in battle (data/story/boss_lines.json) with ElevenLabs v3.

Each line is voiced by its boss's cast.json speaker (the same voice as in the cinematics), mastered in
the boss's style (narrate.py STYLES) and written to assets/audio/voice/bosses/<boss>/<kind>_<n>.ogg.
assets/audio/voice/bosses/lines.json lists every line with its text and length for BossVoice.

Replies are cached in tools/voice/cache/, so only new or changed lines cost credits.

usage:
    python3 tools/voice/boss_lines.py                  # every boss
    python3 tools/voice/boss_lines.py gorrath ashwick  # some bosses (lines.json keeps the others)
    python3 tools/voice/boss_lines.py --cost           # characters it would send, nothing recorded
Needs ELEVENLABS_API_KEY (or the cloud network secret), ffmpeg with rubberband.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
import elevenlabs_tts as el  # noqa: E402
import narrate  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LINES = ROOT / "data" / "story" / "boss_lines.json"
OUT = ROOT / "assets" / "audio" / "voice" / "bosses"


def preset_for(entry: dict) -> dict:
    role = narrate.cast().get(entry["speaker"])
    if role is None:
        sys.exit(f"{entry['speaker']} is not in tools/voice/cast.json")
    style = entry.get("style") or role.get("style", "mortal")
    return {**narrate.PRESETS["regal_el"], **narrate.STYLES[style], "voice_id": role["voice_id"],
            "stability": entry.get("stability", 0.0)}


def voiced_length(path: Path) -> float:
    """Seconds to the last word, before the hall's echo dies away (the boss's jaw stops there)."""
    x, sr = sf.read(path)
    win = max(1, int(sr * 0.03))
    env = np.convolve(np.abs(x), np.ones(win) / win, "same")
    loud = np.flatnonzero(env > 0.12 * env.max())
    return round(float(loud[-1]) / sr + 0.1, 2) if loud.size else 0.0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("bosses", nargs="*")
    ap.add_argument("--cost", action="store_true")
    a = ap.parse_args()
    bosses = json.loads(LINES.read_text(encoding="utf-8"))["bosses"]
    index_path = OUT / "lines.json"
    index = json.loads(index_path.read_text()) if index_path.exists() else {}
    chars = cached = 0
    for boss, entry in bosses.items():
        if a.bosses and boss not in a.bosses:
            continue
        item = {k: entry[k] for k in ("share", "only") if k in entry}
        if "lines" in entry:
            preset = preset_for(entry)
            item["lines"] = {}
            for kind, texts in entry["lines"].items():
                for n, text in enumerate(texts, 1):
                    body = {"text": text, "model_id": "eleven_v3", "voice_settings": {"stability": preset["stability"]}}
                    hit = el.CACHE / f"{el.cache_key(preset['voice_id'], body)}.mp3"
                    chars += 0 if hit.exists() else len(text)
                    cached += hit.exists()
                    if a.cost:
                        continue
                    rel = f"{boss}/{kind}_{n}.ogg"
                    out = OUT / rel
                    out.parent.mkdir(parents=True, exist_ok=True)
                    audio, sr = el.decode(el.tts(text, preset["voice_id"], preset["stability"]))
                    with narrate.tempfile.TemporaryDirectory() as tmp:
                        raw = Path(tmp) / "raw.wav"
                        sf.write(raw, narrate._trim(audio, sr), sr)
                        narrate.master(raw, out, preset)
                    secs = round(sf.info(out).duration - 0.6, 2)   # master() pads 0.6 s of tail
                    item["lines"].setdefault(kind, []).append({"file": rel, "text": text, "secs": secs,
                                                               "voiced": voiced_length(out)})
                    print(f"{rel:38} {secs:4.1f}s  {text}")
        index[boss] = item
    if a.cost:
        print(f"{chars} characters to send ({cached} lines already cached)")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=1, sort_keys=True) + "\n")
    print(f"{index_path}: {len(index)} bosses")


if __name__ == "__main__":
    main()
