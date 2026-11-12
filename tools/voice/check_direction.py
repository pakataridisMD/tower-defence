#!/usr/bin/env python3
"""Check that every voiced sentence in the cinematics has an emotion in direction.json.

    python3 tools/voice/check_direction.py [--scripts DIR] [--prune]

Lists sentences with no direction (they would be read flat) and entries that no
longer match any line (left over from an older script). --prune deletes the stale
entries. Exits 1 if anything is missing.
"""
import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import narrate  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--scripts", type=Path, default=narrate.CINEMATICS)
ap.add_argument("--prune", action="store_true")
args = ap.parse_args()

doc = json.loads(narrate.DIRECTION_FILE.read_text(encoding="utf-8"))
lines = doc["lines"]
missing, used = [], set()
for f in sorted(args.scripts.glob("*.json")):
    cid = f.stem
    for n, shot in enumerate(narrate.shots_of(json.loads(f.read_text(encoding="utf-8"))), start=1):
        if shot.get("voice") is False or narrate.speaker_preset(shot.get("speaker", "narrator")) is None:
            continue
        for para in (shot.get("text") or "").split("\n\n"):
            for s in [x for x in re.split(r"(?<=[.!?])\s+", " ".join(para.split())) if x]:
                if s in lines.get(cid, {}):
                    used.add((cid, s))
                else:
                    missing.append(f"{cid}/{n:02d} {shot.get('speaker', 'narrator')}: {s}")
stale = [(c, s) for c, m in lines.items() for s in m if (c, s) not in used]
print(f"missing {len(missing)}", *missing, sep="\n  ")
print(f"stale {len(stale)}", *(f"{c}: {s}" for c, s in stale), sep="\n  ")
if args.prune and stale:
    for c, s in stale:
        del lines[c][s]
    narrate.DIRECTION_FILE.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("pruned")
sys.exit(1 if missing else 0)
