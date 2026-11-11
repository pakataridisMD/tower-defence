"""Bring the hand-drawn 2D art (tools/art/pix2d on the story-art branch) into the game.

Copies, from a git ref of that branch:
  - each enemy's walk strip and normal-map strip into assets/art/game/drawn/, with drawn.json
    (frame size, feet point, frame count); gen_game_art.py cuts them into the game's frames,
  - the portraits into assets/story/portraits/<character id>.png (hidden characters left out),
  - the cinematic stills into assets/story/images/<cinematic id>/<NN>.png.

Then run:  python3 tools/art/gen_game_art.py --enemies && godot --headless --import

Usage:  python3 tools/art/import_pix2d.py [git ref]   (default origin/claude/project-thread-b06oys)
"""
from __future__ import annotations

import json
import os
import subprocess
import sys

REF = sys.argv[1] if len(sys.argv) > 1 else "origin/claude/project-thread-b06oys"

# Art id -> game enemy id, where they differ. The horde's rank and file are drawn as creatures of
# the new style: the dead and the shades of the Hollow, its orcs and stone, its turned elves and
# dwarves.
ENEMY_IDS = {
    "ourra": "saltmother",
    "vesper": "pale_vesper",
    "cassivane": "ashen_regent",
    "elder_broodmother": "broodmother",
    "tidal_leviathan": "leviathan",
    "skeleton": "grunt",
    "ghost": "runner",
    "orc": "brute",
    "elf": "mender",
    "golem": "splitter",
    "orb_earth": "shardling",
    "dwarf": "warded",
    "dragon": "warden",
}


def show(path: str) -> bytes:
    return subprocess.run(["git", "show", f"{REF}:{path}"], capture_output=True, check=True).stdout


def ls(path: str) -> list[str]:
    out = subprocess.run(["git", "ls-tree", "-r", "--name-only", REF, path], capture_output=True, text=True)
    return out.stdout.split()


def main() -> None:
    game_enemies = {os.path.splitext(f)[0] for f in os.listdir("data/enemies") if f.endswith(".tres")}
    anim = json.loads(show("art/pix2d/anim/anim.json"))
    drawn = {}
    os.makedirs("assets/art/game/drawn", exist_ok=True)
    for art_id, info in anim.items():
        gid = ENEMY_IDS.get(art_id, art_id)
        if gid not in game_enemies:
            continue
        for suffix in ("", "_n"):
            with open(f"assets/art/game/drawn/{gid}_walk{suffix}.png", "wb") as fh:
                fh.write(show(f"art/pix2d/anim/{art_id}_walk{suffix}.png"))
        drawn[gid] = {"source": art_id, **info}
    with open("assets/art/game/drawn/drawn.json", "w") as fh:
        json.dump(drawn, fh, indent=1, sort_keys=True)

    people = {c["id"]: c for c in json.load(open("data/story/characters.json"))}
    portraits = 0
    os.makedirs("assets/story/portraits", exist_ok=True)
    for path in ls("art/pix2d/portraits/"):
        cid = os.path.splitext(os.path.basename(path))[0]
        if cid in people and not people[cid].get("hidden"):
            with open(f"assets/story/portraits/{cid}.png", "wb") as fh:
                fh.write(show(path))
            portraits += 1

    stills = 0
    for path in ls("art/pix2d/stills/"):
        parts = path.split("/")
        if len(parts) != 5 or not parts[4][:2].isdigit():
            continue
        os.makedirs(f"assets/story/images/{parts[3]}", exist_ok=True)
        with open(f"assets/story/images/{parts[3]}/{parts[4]}", "wb") as fh:
            fh.write(show(path))
        stills += 1
    missing = []
    for name in sorted(os.listdir("data/story/cinematics")):
        cid = name[:-5]
        shots = len(json.load(open(f"data/story/cinematics/{name}"))["shots"])
        folder = f"assets/story/images/{cid}"
        have = len([f for f in os.listdir(folder) if f.endswith(".png")]) if os.path.isdir(folder) else 0
        if have != shots:
            missing.append(f"{cid} ({have} of {shots})")
    print(f"{len(drawn)} enemies, {portraits} portraits, {stills} stills")
    if missing:
        print("Stills do not match the shot list:", ", ".join(missing))


if __name__ == "__main__":
    main()
