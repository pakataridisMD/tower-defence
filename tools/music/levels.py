"""Print each stem's level (dB RMS) per section, to check balance: python3 levels.py <cue>"""
import glob
import json
import os
import sys

import numpy as np
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
name = sys.argv[1]
sheet = json.load(open(os.path.join(HERE, "..", "..", "assets", "story", "music", f"{name}.json")))
ms = [m["time"] for m in sheet["markers"]] + [sheet["duration"]]
print(" " * 12 + " ".join(m["name"][:7].rjust(7) for m in sheet["markers"]))
for f in sorted(glob.glob(os.path.join(HERE, "out", f"{name}__*.wav"))) + [os.path.join(HERE, "out", f"{name}.wav")]:
    x, sr = sf.read(f)
    m = x.mean(1)
    row = []
    for i in range(len(ms) - 1):
        seg = m[int(ms[i] * sr):int(ms[i + 1] * sr)]
        v = 20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9)
        row.append(f"{v:7.0f}" if v > -70 else "      .")
    print(os.path.basename(f)[len(name):-4].strip("_").ljust(12)[:12] + " ".join(row))
