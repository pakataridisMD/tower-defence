#!/usr/bin/env python3
"""Turn tools/capture.gd --bosses output into a film with the bosses' voices.

usage: python3 tools/art/boss_film.py <out>/bosses film.mp4 [--fps 30] [--scale 1280]
Reads f_NNNN.png and cues.json ([{frame, file}], files under assets/audio/voice/bosses/).
"""
import argparse
import json
import os
import subprocess

VOICE = os.path.join("assets", "audio", "voice", "bosses")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("out")
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--scale", type=int, default=1280)
    a = ap.parse_args()
    cues = json.load(open(os.path.join(a.folder, "cues.json")))
    frames = len([f for f in os.listdir(a.folder) if f.startswith("f_")])
    length = frames / a.fps
    cmd = ["ffmpeg", "-loglevel", "error", "-y", "-framerate", str(a.fps), "-i", os.path.join(a.folder, "f_%04d.png")]
    for cue in cues:
        cmd += ["-i", os.path.join(VOICE, cue["file"])]
    if cues:
        parts = [f"[{i + 1}:a]adelay={int(c['frame'] / a.fps * 1000)}:all=1[v{i}]" for i, c in enumerate(cues)]
        mix = "".join(f"[v{i}]" for i in range(len(cues)))
        graph = ";".join(parts) + f";{mix}amix=inputs={len(cues)}:normalize=0,apad,atrim=0:{length:.2f}[a]"
        cmd += ["-filter_complex", graph, "-map", "0:v", "-map", "[a]", "-c:a", "aac", "-b:a", "160k"]
    cmd += ["-vf", f"scale={a.scale}:-2:flags=lanczos", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
            "-t", f"{length:.2f}", a.out]
    subprocess.run(cmd, check=True)
    print(a.out, f"{length:.1f}s", len(cues), "lines")


if __name__ == "__main__":
    main()
