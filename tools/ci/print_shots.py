#!/usr/bin/env python3
"""Prints screenshots into the build log as base64 JPEGs, so they can be read back from the log
when the build's files cannot be downloaded.

  python3 tools/ci/print_shots.py <folder> [--width=<pixels>] [--quality=<1-95>]

Each picture is printed between "@@SHOT <name>" and "@@END" lines. To get them back, save the log
and run:  python3 tools/ci/print_shots.py --read <log file> <folder>
"""
from __future__ import annotations

import base64
import glob
import io
import os
import re
import sys


def write(folder: str, width: int, quality: int) -> None:
    from PIL import Image

    for path in sorted(glob.glob(os.path.join(folder, "*.png"))):
        image = Image.open(path).convert("RGB")
        if width and image.width > width:
            image = image.resize((width, round(image.height * width / image.width)), Image.LANCZOS)
        data = io.BytesIO()
        image.save(data, "JPEG", quality=quality)
        text = base64.b64encode(data.getvalue()).decode()
        # The folder goes in the name, so two folders can each hold a "menu".
        print("@@SHOT %s_%s" % (os.path.basename(os.path.normpath(folder)), os.path.splitext(os.path.basename(path))[0]))
        for start in range(0, len(text), 2000):
            print(text[start:start + 2000])
        print("@@END")


def read(log_path: str, folder: str) -> None:
    os.makedirs(folder, exist_ok=True)
    name, chunks = None, []
    for line in open(log_path, errors="replace"):
        # Build logs put a timestamp in front of every line.
        line = re.sub(r"^\S+Z ", "", line.rstrip("\n"))
        if line.startswith("@@SHOT "):
            name, chunks = line[7:].strip(), []
        elif line.startswith("@@END") and name:
            with open(os.path.join(folder, name + ".jpg"), "wb") as fh:
                fh.write(base64.b64decode("".join(chunks)))
            print("read", name)
            name = None
        elif name:
            chunks.append(line.strip())


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    options = dict(a[2:].split("=", 1) if "=" in a else (a[2:], "1") for a in sys.argv[1:] if a.startswith("--"))
    if "read" in options:
        read(args[0], args[1])
    else:
        write(args[0], int(options.get("width", 0)), int(options.get("quality", 72)))
