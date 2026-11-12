"""Stills for the land-hordes rewrite (2026-11-12): each land is now attacked by its own element, led by a Herald born
there. Ember Reach: Ashwick. Thunder Steppe: Vholt. Verdant Deep: Mother Briar. Frostmere: the Saltmother.
Sunscar Canyon: Gorrath. Hollow Rift: the Pale Vesper.

Shot docstrings are the art notes from tools/story/story_content.py on branch claude/project-thread-j0flpm.
Painted back to front in separate Scene calls, vignette last, so cinema/tools/layer_stills.py can cut layers.

usage: python3 tools/art/pix2d/shots_hordes.py --out art/pix2d/stills [--sheet sheet.png]
"""
from __future__ import annotations

import argparse
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from stills import H, W, Scene, flame
from shots_lands import (GREYL, _face_close, _rider, death_pose, earth_bg, ember_bg, nature_bg, storm_bg, void_bg,
                         walk_pose, water_bg)
from shots_story import arr_of, paste

BRIDGES = ((50, 40, 80), (40, 120, 170), (64, 204, 250))       # nature_bg's rope bridges: (y, x0, x1)


# ---- helpers ------------------------------------------------------------------------------------------------------
def put_pad(sc, name, x, feet, pose, pad=60, light=(1, 1, 1), flip=False, recolour=None):
    """Like Scene.put, with room for a whole-body tilt ({"_all": (angle, dx, dy)}, positive = pitching forward)."""
    import creatures
    s = creatures.CREATURES[name](pose, pad)
    im = np.asarray(s.image()).astype(np.float32)
    fx, fy = s.w // 2, s.bh - 4 + s.pad
    if flip:
        im = im[:, ::-1].copy()
        fx = s.w - fx
    im[..., :3] *= np.array(light, np.float32)
    if recolour:
        recolour(im)
    paste(sc, im, x, feet, fx, fy)


def walking_oak(sc, x, feet, s=1.0, grey=True, felled=False):
    """An ancient oak torn out of the ground and walking on its roots, black thorns in its crown, grey knots for eyes."""
    bark, lit, dark = (74, 56, 40), (120, 94, 64), (44, 32, 24)
    if felled:                                                   # lying on its side, roots in the air
        sc.poly([(x - 60 * s, feet), (x + 50 * s, feet - 4 * s), (x + 50 * s, feet - 16 * s), (x - 60 * s, feet - 12 * s)], bark)
        sc.line(x - 60 * s, feet - 12 * s, x + 50 * s, feet - 16 * s, lit)
        for k in range(5):
            a = -0.9 + k * 0.45
            sc.line(x + 50 * s, feet - 10 * s, x + 50 * s + math.cos(a) * 22 * s, feet - 10 * s + math.sin(a) * 22 * s, dark)
        for k in range(6):
            sc.disc(x - 66 * s - k * 6 * s, feet - 10 * s - (k % 2) * 6 * s, 9 * s, (40, 50, 30))
        return
    for side in (-1, 1):                                         # root legs, one forward
        sc.poly([(x + side * 6 * s, feet - 30 * s), (x + side * 22 * s, feet - 6 * s), (x + side * 26 * s, feet),
                 (x + side * 16 * s, feet), (x + side * 2 * s, feet - 24 * s)], dark if side > 0 else bark)
        for k in range(3):
            sc.line(x + side * (20 + k * 4) * s, feet, x + side * (24 + k * 6) * s, feet + 2, dark)
    sc.poly([(x - 14 * s, feet - 30 * s), (x + 14 * s, feet - 30 * s), (x + 10 * s, feet - 92 * s), (x - 12 * s, feet - 92 * s)], bark)
    sc.poly([(x - 14 * s, feet - 30 * s), (x - 9 * s, feet - 30 * s), (x - 7 * s, feet - 92 * s), (x - 12 * s, feet - 92 * s)], lit)
    for y in range(int(feet - 88 * s), int(feet - 32 * s), int(8 * s) or 1):
        sc.line(x - 2 * s, y, x + 2 * s, y + 5 * s, dark)
    for a in (-2.4, -1.9, -1.2, -0.7):                              # branches like arms
        sc.line(x, feet - 86 * s, x + math.cos(a) * 40 * s, feet - 86 * s + math.sin(a) * 30 * s, bark)
        sc.line(x, feet - 87 * s, x + math.cos(a) * 40 * s, feet - 87 * s + math.sin(a) * 30 * s, bark)
    for k in range(9):                                           # a dark crown full of black thorns
        cx = x + (k - 4) * 9 * s
        cy = feet - 112 * s + abs(k - 4) * 4 * s
        sc.disc(cx, cy, 13 * s, (34, 46, 28))
        sc.disc(cx - 3 * s, cy - 3 * s, 8 * s, (52, 68, 38))
    for k in range(14):
        tx, ty = x + sc.rng.uniform(-40, 40) * s, feet - sc.rng.uniform(96, 124) * s
        sc.poly([(tx, ty), (tx + 2, ty - 5 * s), (tx + 3, ty)], (16, 12, 14))
    eye = (176, 176, 186) if grey else (160, 230, 120)
    for ex in (-5, 5):
        sc.rect(int(x + ex * s) - 1, int(feet - 70 * s), int(x + ex * s) + 2, int(feet - 68 * s), eye)
    sc.rect(int(x - 5 * s), int(feet - 58 * s), int(x + 6 * s), int(feet - 55 * s), dark)


def thorns_on_bridges(sc):
    """Black thorn vines choking nature_bg's rope bridges."""
    for y0, x0, x1 in BRIDGES:
        for x in range(x0, x1, 2):
            y = int(y0 + 6 * math.sin((x - x0) / (x1 - x0) * math.pi)) - 1 + int(2 * math.sin(x * 0.7))
            sc.c[y, x] = (16, 12, 14)
            sc.c[y + 1, x] = (30, 22, 24)
            if x % 6 == 0:
                sc.poly([(x, y), (x + 2, y - 4), (x + 3, y)], (16, 12, 14))


def brown_of(im):
    """Wilt a creature to dead brown thorns."""
    lum = im[..., :3].mean(-1, keepdims=True)
    im[..., :3] = lum * np.array((0.95, 0.72, 0.5), np.float32)
    return im


def drowned(im):
    """The rank-and-file dead as drowned fishermen: wet, blue-grey, a little green."""
    lum = im[..., :3].mean(-1, keepdims=True)
    im[..., :3] = im[..., :3] * 0.35 + lum * np.array((0.55, 0.7, 0.75), np.float32)
    return im


def steps(sc, y0=130, col=(40, 30, 32), rim=(90, 50, 40)):
    for i, y in enumerate(range(y0, 180, 10)):                   # the Cinder Steps of Brazier Hold
        sc.rect(0, y, 320, y + 10, tuple(max(0, c - i * 4) for c in col))
        sc.rect(0, y, 320, y + 1, rim)


def rain(sc, n=240, col=(130, 140, 160), seed=0):
    rng = np.random.default_rng(seed)
    for _ in range(n):
        x, y = int(rng.integers(0, W + 20)), int(rng.integers(-6, H))
        sc.line(x, y, x - 2, y + 5, col)


def bolt(sc, x, y0, y1, seed=0, col=(240, 240, 255)):
    rng = np.random.default_rng(seed)
    y = y0
    while y < y1:
        nx, ny = x + rng.uniform(-6, 6), y + rng.uniform(6, 12)
        sc.line(x, y, nx, ny, col)
        x, y = nx, ny
    sc.glow(x, y, 18, (200, 200, 255), 0.6)


# ---- Ember Reach: Ashwick -------------------------------------------------------------------------------------------
def ember_herald_01():
    """Ashwick stumbling on the steps of Brazier Hold, embers scattering off him, his empty messenger's satchel falling
    open. His grey eyes going dark."""
    sc = Scene(504)
    ember_bg(sc, lava=False)
    steps(sc)
    sc.glow(160, 150, 40, (255, 150, 60), 0.4)
    put_pad(sc, "ashwick", 150, 166, {"_all": (0.9, 4, 0)}, light=(1.0, 0.95, 0.9))
    sc.poly([(196, 168), (212, 166), (214, 174), (198, 176)], (110, 76, 46))    # the satchel, open and empty
    sc.poly([(196, 168), (212, 166), (208, 162), (194, 164)], (140, 100, 62))
    sc.particles(90, [(255, 200, 90), (255, 140, 40), (255, 240, 180)], 90, 170, 100, 230)
    sc.vignette(0.5)
    return sc


def ember_herald_02():
    """A cold forge. Brannoc Emberhand, huge, bald, brass-ringed beard, wrenching out of chains of his own iron and
    grabbing his hammer from the rubble; its head flares orange."""
    sc = Scene(505)
    sc.bands("1a1416", "2a2224", 0, 150, n=4)
    for x in range(0, W, 34):                                    # the forge hall's stone
        sc.rect(x, 0, x + 1, 150, (44, 38, 40))
    sc.rect(20, 60, 110, 150, (50, 44, 46))                        # the cold hearth, ash grey, no fire
    sc.poly([(14, 60), (65, 26), (116, 60)], (44, 38, 40))
    sc.rect(36, 96, 94, 150, (16, 14, 16))
    sc.particles(40, [(90, 86, 84), (70, 66, 64)], 120, 150, 40, 90)
    sc.rect(222, 126, 262, 134, (60, 60, 66))                       # the anvil
    sc.poly([(214, 126), (222, 126), (222, 130)], (60, 60, 66))
    sc.rect(232, 134, 252, 150, (50, 50, 56))
    sc.rect(222, 126, 262, 127, (110, 110, 118))
    sc.bands("3a3234", "1a1416", 150, H, n=3)
    sc.put("brannoc", 160, 172, pose=death_pose("brannoc", 1), light=(0.95, 0.85, 0.8), rim=(255, 160, 70))
    for side in (-1, 1):                                         # chains of his own iron, snapping
        cx = 160 + side * 26
        for k in range(6):
            x, y = cx + side * k * 7, 128 + k * 3
            sc.disc(x, y, 3, (90, 90, 98))
            sc.disc(x, y, 1.4, (30, 28, 32))
        sc.particles(8, [(255, 220, 140)], 124, 132, cx - 4, cx + 4)
    sc.glow(196, 108, 22, (255, 140, 40), 0.8)                       # the hammer's head flaring orange
    sc.vignette(0.5)
    return sc


# ---- Thunder Steppe: Vholt ------------------------------------------------------------------------------------------
def storm_intro_02():
    """Lightning striking a burning tent camp. Dead riders on lightning-maned horses charging through the grass, harpies
    and balls of lightning over them. Above, on a thunderbird of black cloud, an old warchief with a crown of lightning:
    Vholt."""
    sc = Scene(512)
    storm_bg(sc, frozen=True)
    for x in range(30, 300, 30):                                 # the tent camp, burning
        sc.poly([(x, 112), (x + 9, 98), (x + 18, 112)], (190, 180, 160))
        flame(sc, x + 9, 104, 10)
        sc.glow(x + 9, 102, 12, (255, 140, 50), 0.5)
    bolt(sc, 96, 0, 104, seed=3)
    bolt(sc, 236, 0, 100, seed=4)
    for x, y in ((40, 70), (290, 64)):
        sc.put("orb_storm", x, y, light=GREYL)
    sc.put("vholt", 168, 108, light=(0.85, 0.85, 0.92))
    for k, x in enumerate((70, 150, 240)):                       # dead riders, horses with lightning in their manes
        _rider(sc, x, 176 - (k % 2) * 4, name="skeleton", hip=30, light=(0.8, 0.82, 0.9), horse_light=(0.55, 0.58, 0.7))
        for j in range(4):
            sc.line(x + 12 + j * 3, 132 + j * 4, x + 16 + j * 3, 128 + j * 4, (230, 230, 255))
    sc.vignette(0.45)
    return sc


def storm_herald_01():
    """The black thunderbird crashing on the ridge at Highwind. Kaela on her grey stallion Thunderclap, lightning lance
    crackling, white war-paint across her face."""
    sc = Scene(513)
    storm_bg(sc)
    put_pad(sc, "vholt", 96, 180, {"_all": (0.5, 10, 6), "wing": (-0.7, 0, 0)}, light=(0.85, 0.85, 0.9))
    sc.particles(140, [(120, 120, 130), (90, 90, 100), (60, 60, 70)], 120, 176, 40, 220)
    _rider(sc, 262, 174)
    bolt(sc, 286, 64, 86, seed=8)
    sc.vignette(0.4)
    return sc


def storm_herald_02():
    """Vholt crawling free of the wreck, the grey light flickering out of his eyes as he looks up at Kaela and her lance."""
    sc = Scene(514)
    storm_bg(sc)
    sc.c *= 0.6
    _face_close(sc, "vholt", 112, 42)
    sc.line(250, 10, 214, 120, (200, 200, 210))                        # Kaela's lance, coming into frame
    sc.poly([(250, 10), (258, 0), (262, 4)], (230, 230, 240))
    sc.vignette(0.6)
    return sc


def storm_herald_03():
    """Kaela standing over the fallen warchief, lance lowered, rain starting."""
    sc = Scene(515)
    storm_bg(sc)
    sc.c *= 0.8
    put_pad(sc, "vholt", 92, 186, {"_all": (0.75, 14, 10), "wing": (-1.0, 0, 0)}, light=(0.7, 0.7, 0.75))
    sc.put("kaela", 270, 174, flip=True, light=(0.9, 0.9, 0.95))
    rain(sc, 160, seed=15)
    sc.vignette(0.45)
    return sc


# ---- Verdant Deep: Mother Briar -------------------------------------------------------------------------------------
def nature_intro_02():
    """Black thorns choking the rope bridges; an ancient oak tearing its roots out of the ground and walking;
    bramble-creatures running ahead. Among them a thicket in the shape of a woman with grey flowers in her hair:
    Mother Briar."""
    sc = Scene(522)
    nature_bg(sc, dark=True)
    thorns_on_bridges(sc)
    sc.put("mother_briar", 120, 178, light=(0.9, 0.88, 0.85))
    walking_oak(sc, 246, 172)
    for k, x in enumerate((30, 58, 186, 206, 300)):                  # bramble-creatures running ahead
        sc.put("orb_nature", x, 176 - (k % 2) * 4, light=(0.45, 0.4, 0.4))
    sc.vignette(0.5)
    return sc


def nature_herald_01():
    """The thicket-woman falling among the roots, grey flowers wilting, black thorns crumbling to brown."""
    sc = Scene(523)
    nature_bg(sc, dark=True)
    im, fx, fy = arr_of("mother_briar", pose=death_pose("mother_briar", 4))
    brown_of(im)
    paste(sc, im, 160, 176, fx, fy)
    sc.particles(120, [(120, 84, 50), (90, 64, 40), (150, 110, 70)], 120, 178, 100, 230)
    sc.vignette(0.5)
    return sc


def nature_herald_02():
    """Close on Mother Briar's face, the grey light leaving her eyes; for a moment she looks like herself, an old woman
    with healer's hands."""
    sc = Scene(524)
    nature_bg(sc)
    sc.c *= 0.55
    sc.glow(160, 90, 70, (200, 230, 160), 0.35)
    _face_close(sc, "mother_briar", 112, 42)
    sc.vignette(0.6)
    return sc


def nature_herald_04():
    """Sylvaine Thornwhisper standing amid a ring of fallen thorn-creatures and a felled walking oak, a pale leafing
    longbow in her hands, moss cloak. She lowers the bow."""
    sc = Scene(125)
    nature_bg(sc)
    walking_oak(sc, 250, 178, s=0.9, felled=True)
    for x in (50, 84, 112, 206, 232):                                 # fallen thorn-creatures, dead and brown
        put_pad(sc, "orb_nature", x, 178, {"_all": (1.4, 0, 0)}, recolour=brown_of, light=(0.8, 0.8, 0.8))
    sc.put("sylvaine", 160, 174, light=(0.95, 1.0, 0.9), rim=(180, 255, 150))
    sc.vignette(0.45)
    return sc


# ---- Frostmere: the Saltmother --------------------------------------------------------------------------------------
def water_intro_02():
    """The ice of Frostmere cracking open from below. Drowned fishermen with nets and drowned priests climbing out of
    the black holes, crabs crusted with ice behind them. Inside a tall column of black seawater, a woman walks: the
    Saltmother."""
    sc = Scene(532)
    water_bg(sc)
    for (x0, y0, x1, y1) in ((20, 130, 120, 150), (120, 150, 200, 140), (200, 140, 300, 160), (60, 170, 160, 160)):
        sc.line(x0, y0, x1, y1, (40, 70, 90))                       # cracks running through the ice
    sc.put("ourra", 220, 172, light=(0.85, 0.9, 0.95))
    for k, (x, y) in enumerate(((70, 150), (130, 166), (290, 168))):   # holes, and the drowned climbing out
        sc.disc(x, y, 16, (8, 16, 24), squash=0.35)
        sc.disc(x - 3, y - 2, 13, (14, 26, 36), squash=0.3)
        im, fx, fy = arr_of("skeleton", pose=walk_pose("skeleton", k * 3), flip=k == 2)
        drowned(im)
        im[fy - 16:, :, 3] = 0                                          # waist-deep in the black water
        paste(sc, im, x, y + 16, fx, fy)
        sc.c[((((sc.xs - x) / 16) ** 2 + ((sc.ys - y) / 5.6) ** 2) < 1) & (sc.ys >= y + 1)] = (8, 16, 24)
        sc.line(x - 14, y + 4, x + 14, y + 4, (220, 236, 244))         # the near lip of the ice
    for x, y in ((40, 172), (176, 176), (250, 178)):                    # crabs crusted with ice
        sc.disc(x, y, 4, (110, 70, 60), squash=0.6)
        sc.disc(x - 1, y - 1, 2, (220, 236, 244), squash=0.6)
        for d in (-5, 5):
            sc.line(x + d, y, x + d * 1.4, y - 3, (110, 70, 60))
    sc.vignette(0.45)
    return sc


# ---- Sunscar Canyon: Gorrath ----------------------------------------------------------------------------------------
def earth_intro_02():
    """Canyon walls cracking; boulders standing up and walking. Stoneborn with granite growing through their skin
    marching among them. At their head a giant Stoneborn general with a square hole in his chest: Gorrath."""
    sc = Scene(542)
    earth_bg(sc)
    for (x0, y0, x1, y1) in ((60, 30, 72, 80), (72, 80, 64, 120), (250, 20, 236, 70), (236, 70, 246, 110)):
        sc.line(x0, y0, x1, y1, (40, 20, 14))
        sc.line(x0 + 1, y0, x1 + 1, y1, (200, 130, 80))
    sc.particles(80, [(140, 90, 60), (100, 64, 40)], 40, 150, 0, W)
    for x in (40, 96, 236, 286):
        sc.put("golem", x, 172, light=(0.85, 0.75, 0.7))
    sc.put("gorrath", 166, 182, light=(0.9, 0.85, 0.82))
    sc.vignette(0.45)
    return sc


def earth_herald_01():
    """Gorrath breaking apart on the terraces into boulders that keep rolling, then stop. The carved stone heart in his
    chest cracks in two."""
    sc = Scene(543)
    earth_bg(sc)
    sc.put("gorrath", 150, 176, light=(0.9, 0.85, 0.82), pose=death_pose("gorrath", 5))
    for x, y, r in ((60, 166, 8), (90, 172, 6), (230, 170, 9), (262, 174, 5), (200, 176, 4)):
        sc.disc(x, y, r, (140, 96, 64))
        sc.disc(x - r // 3, y - r // 3, max(1, r // 3), (190, 140, 96))
    sc.particles(120, [(200, 150, 110), (160, 110, 80)], 60, 170, 80, 240)
    sc.vignette(0.4)
    return sc


# ---- Hollow Rift: the Pale Vesper -----------------------------------------------------------------------------------
def void_herald_01():
    """The Pale Vesper falling on the floating steps, her ghost-choir scattering like moths, the dead dropping where
    they stand."""
    sc = Scene(554)
    void_bg(sc, crack=False)
    sc.rect(80, 150, 240, 158, (50, 40, 64))
    sc.rect(80, 150, 240, 151, (100, 84, 130))
    put_pad(sc, "vesper", 166, 154, {"_all": (-0.6, -6, 0)}, pad=90, light=(0.85, 0.85, 0.95))
    for x, i in ((40, 4), (276, 6), (300, 5)):
        sc.put("skeleton", x, 176, light=(0.6, 0.58, 0.7), pose=death_pose("skeleton", i))
    for _ in range(18):
        x, y = sc.rng.uniform(40, 300), sc.rng.uniform(20, 120)
        sc.disc(x, y, 2, (176, 150, 226))
        sc.glow(x, y, 6, (176, 150, 226), 0.5)
    sc.vignette(0.5)
    return sc


SHOTS = {
    ("ember_herald", 1): ember_herald_01, ("ember_herald", 2): ember_herald_02,
    ("storm_intro", 2): storm_intro_02,
    ("storm_herald", 1): storm_herald_01, ("storm_herald", 2): storm_herald_02, ("storm_herald", 3): storm_herald_03,
    ("nature_intro", 2): nature_intro_02,
    ("nature_herald", 1): nature_herald_01, ("nature_herald", 2): nature_herald_02, ("nature_herald", 4): nature_herald_04,
    ("water_intro", 2): water_intro_02,
    ("earth_intro", 2): earth_intro_02, ("earth_herald", 1): earth_herald_01,
    ("void_herald", 1): void_herald_01,
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join("art", "pix2d", "stills"))
    ap.add_argument("--sheet")
    a = ap.parse_args()
    ims = []
    for (cid, n), fn in SHOTS.items():
        os.makedirs(os.path.join(a.out, cid), exist_ok=True)
        im = fn().image()
        im.save(os.path.join(a.out, cid, f"{n:02d}.png"))
        ims.append((f"{cid} {n:02d}", im))
    if a.sheet:
        cols, rows = 3, (len(ims) + 2) // 3
        sheet = Image.new("RGB", (cols * 650, rows * 384), (20, 18, 24))
        d = ImageDraw.Draw(sheet)
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 14)
        for i, (lab, im) in enumerate(ims):
            x, y = (i % cols) * 650 + 5, (i // cols) * 384 + 4
            sheet.paste(im, (x, y))
            d.text((x + 4, y + 362), lab, font=font, fill=(220, 214, 196))
        sheet.save(a.sheet)
        print(a.sheet, sheet.size)


if __name__ == "__main__":
    main()
