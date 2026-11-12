#!/usr/bin/env python3
"""Bring the bosses' move sets (tools/art/pix2d/boss_moves.py, run on the story-art branch) into the game.

For every boss that drawn.json already knows (matched by its art "source" id), copies the strips of its
new moves into assets/art/game/drawn/, adds them to drawn.json, cuts them into the
assets/art/game/enemies/<id>_<move>_<n>.png frames the game reads, adds them to art.json, and writes
the Godot import files for new pictures. Walk and death are left as they are.

usage: python3 tools/art/import_boss_moves.py DIR      (DIR = boss_moves.py --out)
then:  godot --headless --import
"""
from __future__ import annotations

import json
import os
import shutil
import sys

from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_game_art  # noqa: E402

DRAWN = os.path.join("assets", "art", "game", "drawn")
OUT = os.path.join("assets", "art", "game")
MOVES = ["idle", "talk", "attack", "roar", "cast", "slam", "guard", "hurt", "rise"]


def main() -> None:
    src = sys.argv[1]
    moves = json.load(open(os.path.join(src, "moves.json")))
    drawn_path = os.path.join(DRAWN, "drawn.json")
    drawn = json.load(open(drawn_path))
    art_path = os.path.join(OUT, "art.json")
    art = json.load(open(art_path))
    done = []
    for gid, info in sorted(drawn.items()):
        art_id = info.get("source", gid)
        made = moves.get(art_id)
        if made is None or gid not in art["enemies"]:
            continue
        if list(made["frame"]) != list(info["frame"]):
            sys.exit(f"{gid}: frame {made['frame']} from boss_moves.py, {info['frame']} in drawn.json")
        w, h = info["frame"]
        for move in MOVES:
            spec = made["anims"].get(move)
            if spec is None:
                continue
            for suffix in ("", "_n"):
                shutil.copyfile(os.path.join(src, f"{art_id}_{move}{suffix}.png"), os.path.join(DRAWN, f"{gid}_{move}{suffix}.png"))
                strip = Image.open(os.path.join(DRAWN, f"{gid}_{move}{suffix}.png")).convert("RGBA")
                for f in range(spec["frames"]):
                    strip.crop((f * w, 0, f * w + w, h)).save(os.path.join(OUT, "enemies", f"{gid}_{move}_{f}{suffix}.png"))
            info["anims"][move] = spec
            art["enemies"][gid][move] = {"frames": spec["frames"], "fps": spec["fps"], "hold": spec.get("hold", -1)}
        done.append(gid)
    json.dump(drawn, open(drawn_path, "w"), indent=1, sort_keys=True)
    with open(art_path, "w") as fh:
        json.dump(art, fh, indent=1)
    print("moves for", len(done), "bosses:", " ".join(done))
    print(gen_game_art.write_missing_imports(), "import files")


if __name__ == "__main__":
    main()
