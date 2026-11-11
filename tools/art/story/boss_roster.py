#!/usr/bin/env python3
"""Lays out every boss on one review sheet: art/story/bosses.png (portrait, idle sprite, name, where they fight).

Run after gen_story_art.py has rendered the characters:  python3 tools/art/story/boss_roster.py
"""
from __future__ import annotations

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cast import CAST  # noqa: E402

CH = os.path.join("art", "story", "characters")
OUT = os.path.join("art", "story", "bosses.png")

ROWS = [
    ("The six Heralds (stage 2 of each land)", [
        ("herald_ourra", "Ember 2"), ("herald_gorrath", "Storm 2"), ("herald_vesper", "Nature 2"),
        ("herald_ashwick", "Water 2"), ("herald_vholt", "Earth 2"), ("herald_briar", "Void 2")]),
    ("The corrupted Wardens (stage 4 of each land)", [
        ("cinder_tyrant", "Ember 4"), ("thunderhead", "Storm 4"), ("elder_broodmother", "Nature 4"),
        ("tidal_leviathan", "Water 4"), ("mountain_titan", "Earth 4"), ("hollow_king", "Void 4")]),
    ("The Convergence and the final assault", [
        ("cassivane_ashen", "Converge 1"), ("sundered_heart", "Converge 3"), ("gatemaw", "Assault"),
        ("echo_heralds", "Assault"), ("vael_orrun", "The last battle")]),
]
HERALDS = ROWS[0][1]
ALLY_ROWS = [
    ("Champions (playable heroes)", [
        ("tamsin", "Start"), ("brannoc", "Fire"), ("kaela", "Storm"), ("sylvaine", "Nature"), ("mirelle", "Water"),
        ("gorrim", "Earth")]),
    ("Freed Wardens", [
        ("ignar", "Fire"), ("aurath", "Storm"), ("elowen", "Nature"), ("thalassa", "Water"), ("orrok", "Earth"),
        ("nyxara", "Void")]),
    ("Story allies", [
        ("corvin", "Void champion"), ("ilyra", "Void + Storm"), ("oswin_white", "Returns at dawn"), ("ysolde", "Narrator"),
        ("fennick", "Tower-Wright"), ("kaela_mounted", "Storm, mounted")]),
]
ECHO_COLS = ["ff7a3a", "c8d8ff", "8af050", "4ae0e0", "e8b040", "b070ff"]

TILE_W, TILE_H = 200, 360


def font(size, bold=False):
    for path in ("/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else
                 "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",):
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def echo_portrait():
    """The Echo-Heralds: all six Heralds as glassy grey reflections, each fringed with an element colour."""
    tile = Image.new("RGBA", (96, 96), (8, 8, 12, 255))
    for k, (cid, _) in enumerate(HERALDS):
        p = np.asarray(Image.open(os.path.join(CH, cid, "portrait_clear.png")).convert("RGBA")).astype(np.float32)
        lum = p[..., :3].mean(-1, keepdims=True)
        glass = lum * 0.7 + np.array([90, 92, 104]) * 0.45
        edge = (p[..., 3] > 0) & ~(np.roll(p[..., 3] > 0, 2, 1))
        col = np.array([int(ECHO_COLS[k][i:i + 2], 16) for i in (0, 2, 4)], np.float32)
        glass[edge] = col
        out = np.concatenate([np.clip(glass, 0, 255), p[..., 3:] * 0.85], -1).astype(np.uint8)
        im = Image.fromarray(out).resize((48, 48), Image.NEAREST)
        tile.alpha_composite(im, ((k % 3) * 32 - 8, (k // 3) * 44 + 2))
    return tile


def first_frame(cid):
    path = os.path.join(CH, cid, "idle_0.png")
    return Image.open(path).convert("RGBA") if os.path.exists(path) else None


def main():
    global ROWS, OUT
    if "--allies" in sys.argv:
        ROWS, OUT = ALLY_ROWS, os.path.join("art", "story", "allies.png")
    cols = max(len(r[1]) for r in ROWS)
    W = cols * TILE_W + 40
    H = sum(TILE_H + 50 for _ in ROWS) + 70
    sheet = Image.new("RGB", (W, H), (14, 12, 18))
    d = ImageDraw.Draw(sheet)
    d.text((20, 18), ("Allies" if "--allies" in sys.argv else "Bosses") + " of the campaign (design renders, not in the game yet)", font=font(24, True), fill=(236, 226, 200))
    y = 70
    for title, members in ROWS:
        d.text((20, y), title, font=font(18, True), fill=(200, 184, 150))
        y += 36
        for i, (cid, where) in enumerate(members):
            x = 20 + i * TILE_W
            if cid == "echo_heralds":
                por = echo_portrait()
                name, spr = "The Echo-Heralds", None
            else:
                por = Image.open(os.path.join(CH, cid, "portrait.png")).convert("RGBA")
                name, spr = CAST[cid]["title"].split(",")[0], first_frame(cid)
            d.text((x, y), name, font=font(13, True), fill=(236, 226, 200))
            d.text((x, y + 18), where, font=font(12), fill=(170, 160, 150))
            sheet.paste(por.resize((184, 184), Image.NEAREST), (x, y + 38))
            if spr is not None:  # the battle sprite, standing on a strip of ground under the portrait
                a = np.asarray(spr)[..., 3] > 0
                ys, xs = np.where(a)
                spr = spr.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1))
                f = 2 if spr.height <= 60 else 1
                spr = spr.resize((spr.width * f, spr.height * f), Image.NEAREST)
                d.rectangle((x, y + 344, x + 183, y + 346), fill=(40, 36, 44))
                sheet.paste(spr, (x + 92 - spr.width // 2, y + 344 - spr.height), spr)
        y += TILE_H + 20
    sheet.save(OUT)
    print(OUT, sheet.size)


if __name__ == "__main__":
    main()
