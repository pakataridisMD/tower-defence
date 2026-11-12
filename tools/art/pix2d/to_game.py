#!/usr/bin/env python3
"""Puts the hand-drawn towers into the game: python3 tools/art/pix2d/to_game.py [tower ids]

Writes assets/art/game/towers/<id>.png, _n.png, _glow.png and replaces each tower's entry in art.json (size, anchor,
muzzle, light, emitter). Towers without a hand-drawn version keep their old art. Then run
`godot --headless --import` so Godot picks the pictures up.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import towers  # noqa: E402
import gen_game_art as old  # noqa: E402

OUT = os.path.join("assets", "art", "game")


def main():
    names = sys.argv[1:] or list(towers.TOWERS)
    art_path = os.path.join(OUT, "art.json")
    art = json.load(open(art_path))
    folder = os.path.join(OUT, "towers")
    for n in names:
        s, meta = towers.TOWERS[n]()
        s.image().save(os.path.join(folder, n + ".png"))
        s.normal_image().save(os.path.join(folder, n + "_n.png"))
        towers.glow_image(s).save(os.path.join(folder, n + "_glow.png"))
        art["towers"][n] = meta
        print("tower", n, s.w, "x", s.h)
    with open(art_path, "w") as fh:
        json.dump(art, fh, indent=1)
    print("import files written:", old.write_missing_imports())


if __name__ == "__main__":
    main()
