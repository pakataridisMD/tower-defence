#!/usr/bin/env python3
"""Preview a cinematic as audio: narration lines laid over its music, the music
ducking under the voice the way the game will play it.

    python3 tools/voice/mix_preview.py VOICE_DIR MUSIC OUT.mp3 [--cues CUES.json]

VOICE_DIR holds 01.ogg, 02.ogg ... for one cinematic. Without --cues, lines play
back to back with a pause between them, starting after a short music intro. With
--cues (a JSON list of shot start times in seconds, or {"shots": [{"start": s}, ...]}
or {"markers": [...]}), each line starts at its shot's time. Needs ffmpeg.
"""
import argparse
import json
import subprocess
from pathlib import Path

ap = argparse.ArgumentParser()
ap.add_argument("voice_dir", type=Path)
ap.add_argument("music", type=Path)
ap.add_argument("out", type=Path)
ap.add_argument("--cues", type=Path)
ap.add_argument("--intro", type=float, default=4.0, help="music before the first line (no cues)")
ap.add_argument("--gap", type=float, default=1.2, help="pause between lines (no cues)")
ap.add_argument("--music-db", type=float, default=-4.0, help="music level before ducking")
args = ap.parse_args()

lines = sorted(args.voice_dir.glob("*.ogg"))
durs = [float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                       "-of", "csv=p=0", str(f)])) for f in lines]
starts = []
if args.cues:
    doc = json.loads(args.cues.read_text())
    items = doc if isinstance(doc, list) else doc.get("shots") or doc.get("markers") or []
    times = [x if isinstance(x, (int, float)) else x.get("start", x.get("time")) for x in items]
    # Voice files are numbered by shot index; map each to its shot's start.
    starts = [float(times[int(f.stem) - 1]) + 0.4 for f in lines]
else:
    t = args.intro
    for d in durs:
        starts.append(t)
        t += d + args.gap

inputs = ["-i", str(args.music)]
for f in lines:
    inputs += ["-i", str(f)]
parts = [f"[{i + 1}:a]aresample=44100,aformat=channel_layouts=stereo,adelay={int(s * 1000)}:all=1[v{i}]"
         for i, s in enumerate(starts)]
vmix = "".join(f"[v{i}]" for i in range(len(lines)))
parts.append(f"{vmix}amix=inputs={len(lines)}:normalize=0,apad,asplit=2[voice][key]")
parts.append(f"[0:a]aresample=44100,aformat=channel_layouts=stereo,volume={args.music_db}dB[mus]")
parts.append("[mus][key]sidechaincompress=threshold=0.03:ratio=6:attack=80:release=900:makeup=1[ducked]")
parts.append("[ducked][voice]amix=inputs=2:normalize=0:duration=first,loudnorm=I=-14:TP=-1[out]")
args.out.parent.mkdir(parents=True, exist_ok=True)
subprocess.run(["ffmpeg", "-loglevel", "error", "-y", *inputs, "-filter_complex", ";".join(parts),
                "-map", "[out]", "-b:a", "192k", str(args.out)], check=True)
print(args.out)
