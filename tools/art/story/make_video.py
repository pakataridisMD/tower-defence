#!/usr/bin/env python3
"""Cuts a draft video of one cinematic from its stills: slow pan and zoom per shot, crossfades and
subtitles from data/story/cinematics/<id>.json. For review only; the game plays the stills itself.

Run from the repository root:
  python3 tools/art/story/make_video.py prologue --json PATH --out FILE.mp4 [--audio FILE]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import textwrap

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FPS = 24
OW, OH = 1280, 720
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"


def ken_burns(img: Image.Image, t: float, k: int) -> Image.Image:
    w, h = img.size
    z0, z1 = (1.0, 1.08) if k % 2 == 0 else (1.08, 1.0)
    z = z0 + (z1 - z0) * t
    cw, ch = w / z, h / z
    dx = (w - cw) * (0.5 + (0.35 if k % 3 == 0 else -0.35 if k % 3 == 1 else 0) * (t - 0.5))
    dy = (h - ch) * 0.5
    box = (dx, dy, dx + cw, dy + ch)
    return img.resize((OW, OH), Image.NEAREST, box=box)


def subtitle(frame: Image.Image, text: str, alpha: float, font) -> None:
    if not text or alpha <= 0:
        return
    lines = []
    for para in text.split("\n"):
        if para.strip():
            lines += textwrap.wrap(para.strip(), 70)
    lines = lines[-3:]
    d = ImageDraw.Draw(frame, "RGBA")
    lh = 34
    y0 = OH - 40 - lh * len(lines)
    d.rectangle((0, y0 - 14, OW, OH), fill=(0, 0, 0, int(150 * alpha)))
    for i, ln in enumerate(lines):
        tw = d.textlength(ln, font=font)
        x = (OW - tw) / 2
        d.text((x + 2, y0 + i * lh + 2), ln, font=font, fill=(0, 0, 0, int(255 * alpha)))
        d.text((x, y0 + i * lh), ln, font=font, fill=(245, 236, 214, int(255 * alpha)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cid")
    ap.add_argument("--json", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audio", default="")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--cues", default="", help="music cue sheet: shot k starts at markers[k], ends at the next")
    args = ap.parse_args()
    data = json.load(open(args.json))
    folder = os.path.join("art", "story", "cinematics", args.cid)
    font = ImageFont.truetype(FONT, 26)
    title_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf", 64)
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{OW}x{OH}", "-r", str(FPS),
           "-i", "-"]
    if args.audio:
        cmd += ["-i", args.audio, "-c:a", "aac", "-b:a", "160k"]
    if args.cues:
        cmd += ["-t", str(json.load(open(args.cues))["duration"])]
    cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "24", args.out]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    fade = int(0.7 * FPS)
    shots = data["shots"]
    if args.cues:
        cues = json.load(open(args.cues))
        times = [m["time"] for m in cues["markers"]] + [cues["duration"]]
        for k, shot in enumerate(shots):
            shot["duration"] = times[k + 1] - times[k]
    prev_tail = None
    for k, shot in enumerate(shots):
        path = os.path.join(folder, f"{k + 1:02d}.png")
        img = Image.open(path).convert("RGB")
        n = int(round(max(3.0, shot.get("duration", 6.0) / args.speed) * FPS))
        for f in range(n):
            t = f / max(1, n - 1)
            fr = ken_burns(img, t, k)
            if k == 0 and f < FPS:  # fade in from black
                fr = Image.blend(Image.new("RGB", fr.size), fr, f / FPS)
            if prev_tail is not None and f < fade:
                fr = Image.blend(prev_tail, fr, f / fade)
            a = min(1.0, f / (0.5 * FPS), (n - f) / (0.4 * FPS))
            subtitle(fr, shot.get("text", ""), a, font)
            if k == len(shots) - 1 and t > 0.55:
                d = ImageDraw.Draw(fr, "RGBA")
                ta = min(1.0, (t - 0.55) / 0.15)
                ttl = data.get("title", "")
                tw = d.textlength(ttl, font=title_font)
                d.text(((OW - tw) / 2 + 3, OH * 0.2 + 3), ttl, font=title_font, fill=(0, 0, 0, int(220 * ta)))
                d.text(((OW - tw) / 2, OH * 0.2), ttl, font=title_font, fill=(255, 226, 160, int(255 * ta)))
            if k == len(shots) - 1 and f > n - FPS:
                fr = Image.blend(fr, Image.new("RGB", fr.size), (f - (n - FPS)) / FPS)
            proc.stdin.write(np.asarray(fr).tobytes())
        prev_tail = ken_burns(img, 1.0, k)
    proc.stdin.close()
    proc.wait()


if __name__ == "__main__":
    main()
