"""Stills for the Ember Reach: ember_intro (3 shots), ember_herald (3) and ember_warden (3).

The fire land is the template for the other five element campaigns: basalt terraces, lava, forges,
the Herald's element arriving as an invader (here the sea), the champion freed, the Warden freed.
"""
from __future__ import annotations

import math

import numpy as np

from cinema import (C, H, W, canvas, darken_edges, fbm, figure, finish, glow, noise1, particles, paste, poly, ridge,
                    silhouette, smoke, stars, tint, vgrad)
from rig import Pose
from shots_midpoint import unbound

LAVA = "ff7a2a"


def _terraces(img, y0, steps=5, seed=0, lit=1.0, lava=True):
    """Stepped black basalt terraces climbing to the right, with lava runs between them."""
    rng = np.random.default_rng(seed)
    for k in range(steps):
        t = k / steps
        top = y0 + (H - y0) * t
        prof = top - (noise1(W, 90, seed + k) - 0.5) * 18 - np.linspace(0, 40 * (1 - t), W)
        shade = (0.55 + 0.45 * t) * lit
        for x in range(W):
            ya = int(max(0, prof[x]))
            img[ya:H, x] = C("1c1618") * shade + 6
            img[ya:ya + 2, x] = C("4a3a36") * shade + 10
        if lava and k < steps - 1:
            yl = int(top + (H - y0) / steps * 0.8)
            xs = rng.uniform(0, W)
            for x in range(W):
                if (x - xs) % 260 < 120:
                    yy = int(yl + math.sin(x * 0.05 + k) * 3)
                    if 0 <= yy < H - 2:
                        img[yy:yy + 2, x] = C(LAVA) * (0.8 + 0.2 * math.sin(x * 0.3))
            glow(img, xs + 60, yl, 160, LAVA, 0.25 * lit, 2.0, ry=24)


def _forge(img, x, y, w, h, lit=1.0):
    """A squat stone forge with a glowing mouth and a chimney."""
    img[int(y - h):int(y), int(x - w / 2):int(x + w / 2)] = C("2a2224") * lit
    img[int(y - h):int(y - h) + 2, int(x - w / 2):int(x + w / 2)] = C("5a4640") * lit
    mw, mh = w * 0.35, h * 0.4
    img[int(y - mh):int(y), int(x - mw / 2):int(x + mw / 2)] = C("ffb050")
    glow(img, x, y - mh / 2, w * 1.4, "ff8a3a", 0.5 * lit, 2.0)
    img[int(y - h * 1.9):int(y - h), int(x + w * 0.2):int(x + w * 0.38)] = C("221c1e") * lit
    smoke(img, x + w * 0.29, y - h * 1.9, 90, "3a3034", seed=int(x), lean=0.6, width=8, amt=0.6)


def _banner(img, x, top, h, col="a0281e"):
    img[int(top):int(top + h + 20), int(x):int(x + 2)] = C("2a2020")
    poly(img, [(x + 2, top), (x + 26, top + 3), (x + 22, top + h), (x + 14, top + h - 8), (x + 2, top + h)], col)
    img[int(top):int(top + 2), int(x + 2):int(x + 26)] = C("d8a040")


def _emberfolk(img, x, y, hgt, seed=0, pot=False, back=False):
    """A small Emberfolk worker: Brannoc's render, scaled down, recoloured to ash and leather."""
    pose = Pose(arm_n=(0.5, 0.1, 1.2), arm_f=(0.4, 0.1, 1.3)) if pot else Pose(leg_n=(0.3, 0.1), leg_f=(-0.2, 0.2))
    rgba, _, _, _ = figure("brannoc", pose, height_px=hgt, yaw=0.5 if back else -0.9, rim=(255, 150, 80),
                           spec_over=dict(weapon=None, beard=None if seed % 2 else "beard"),
                           mats_over=dict(mail=CAST_ASH))
    paste(img, rgba, x, y)
    if pot:
        glow(img, x + hgt * 0.12, y - hgt * 0.5, hgt * 0.35, "ffa040", 0.8, 2.0)
        img[int(y - hgt * 0.55):int(y - hgt * 0.45), int(x + hgt * 0.04):int(x + hgt * 0.2)] = C("2a2426")
        img[int(y - hgt * 0.56):int(y - hgt * 0.54), int(x + hgt * 0.06):int(x + hgt * 0.18)] = C("ffc060")


from sdf import mat  # noqa: E402

CAST_ASH = mat("6a5a52", tex=0.2, tex_freq=90)


def _tide(img, y_top, seed=0, steam=True):
    """A black tide surging up the slope: dark water with grey foam and grey-eyed spirits in it."""
    prof = y_top + (noise1(W, 50, seed) - 0.5) * 30 + np.linspace(40, -30, W)
    n = fbm(H, W, 24, seed + 3, 3)
    for x in range(W):
        ya = int(max(0, prof[x]))
        img[ya:H, x] = C("0c1418") + n[ya:H, x, None] * 26
        img[ya:ya + 2, x] = C("8a96a0")
    rng = np.random.default_rng(seed)
    for k in range(40):
        x = rng.uniform(0, W)
        y = prof[int(x)] + rng.uniform(10, 120)
        if y < H - 4:
            unbound(img, x, y, rng.uniform(4, 10), seed=k)
    if steam:
        for k in range(10):
            x = rng.uniform(0, W)
            smoke(img, x, prof[int(x)], 120, "a8a8b0", seed=k + seed, lean=-0.3, width=22, amt=0.45)
    return prof


def _water_column(img, cx, base, top, w, seed=0, burst=0.0):
    """The Saltmother's column of black water, lit grey from within."""
    rng = np.random.default_rng(seed)
    for y in range(int(top), int(base)):
        t = (y - top) / (base - top)
        half = w * (0.5 + 0.5 * t) * (1 + 0.08 * math.sin(y * 0.11 + seed))
        if burst:
            half *= 1 + burst * (1 - t) * 1.8
        xa, xb = int(cx - half), int(cx + half)
        img[y, max(0, xa):min(W, xb)] = C("16242c") * (0.8 + 0.4 * (1 - t)) + 8
        img[y, max(0, xa):max(0, xa) + 2] = C("8aa0b0")
    glow(img, cx, (top + base) / 2, w * 2.2, "c8d0dc", 0.25, 2.0, ry=(base - top) * 0.6)
    if burst:
        particles(img, int(400 * burst), seed, (cx - w * 3, top - 40, cx + w * 3, base), "a8c0d0", (0, 2), (0.4, 1.0),
                  add=False)
        for k in range(14):  # drowned lanterns and fish thrown out
            x, y = cx + rng.uniform(-w * 3, w * 3), rng.uniform(top - 20, base - 20)
            if rng.random() < 0.5:
                img[int(y):int(y + 5), int(x):int(x + 3)] = C("6a7a6a")
                glow(img, x + 1, y + 2, 10, "c8d8a0", 0.4, 2)
            else:
                poly(img, [(x, y), (x + 9, y - 3), (x + 9, y + 3)], "8aa0a8")


def _spray(img, cx, cy, seed=0):
    """The water-column bursting: drops and sheets of black water thrown outwards, lit grey."""
    rng = np.random.default_rng(seed)
    glow(img, cx, cy, 220, "c8d0dc", 0.3, 1.8)
    ys, xs = np.mgrid[0:H, 0:W]
    for k in range(70):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(30, 230) ** 1.0
        x, y = cx + math.cos(a) * d * 1.3, cy + math.sin(a) * d * 0.8
        r = rng.uniform(3, 12) * (1.2 - d / 300)
        m = ((xs - x) / (r * 1.6)) ** 2 + ((ys - y) / r) ** 2 <= 1
        img[m] = C("1a2a34") + rng.uniform(0, 30)
        top = m & ~np.roll(m, 2, 0)
        img[top] = C("a8c0d0")
    for k in range(14):  # drowned lanterns and fish thrown out
        x, y = cx + rng.uniform(-260, 260), cy + rng.uniform(-140, 100)
        if rng.random() < 0.5:
            img[int(y):int(y + 6), int(x):int(x + 4)] = C("6a7a6a")
            glow(img, x + 2, y + 3, 12, "c8d8a0", 0.5, 2)
        else:
            poly(img, [(x, y), (x + 10, y - 3), (x + 10, y + 3)], "8aa0a8")
    particles(img, 300, seed, (cx - 300, cy - 160, cx + 300, cy + 140), "a8c0d0", (0, 1), (0.4, 1.0), add=False)


# ------------------------------------------------------------------ ember_intro

def intro_shot01():
    """Black basalt terraces, lava rivers, glassworks glowing, red and brass banners. Emberfolk at anvils."""
    img = canvas()
    vgrad(img, [(0, "1a0a0c"), (0.5, "5a1e14"), (0.9, "c0502a"), (1, "e07a3a")], 0, int(H * 0.5))
    glow(img, W * 0.72, H * 0.12, 120, "ffd080", 0.3, 2)
    ridge(img, H * 0.36, 30, 130, "2a1416", 501, jag=18)
    poly(img, [(W * 0.6, H * 0.36), (W * 0.7, H * 0.08), (W * 0.76, H * 0.08), (W * 0.88, H * 0.36)], "1e1012")
    glow(img, W * 0.73, H * 0.08, 60, LAVA, 0.9, 1.6)
    smoke(img, W * 0.73, H * 0.08, 140, "3a2224", seed=3, lean=0.5, width=30, amt=0.7)
    _terraces(img, H * 0.42, 5, seed=11)
    for k, x in enumerate((70, 210, 380, 520)):
        _forge(img, x, H * (0.6 + 0.08 * (k % 2)), 40, 26)
    for x in (130, 300, 460, 600):
        _banner(img, x, H * 0.46, 30, "a0281e" if x % 3 else "c8902a")
    for k, (x, y, h) in enumerate(((150, H * 0.95, 70), (250, H * 0.93, 62), (450, H * 0.97, 74))):
        _emberfolk(img, x, y, h, seed=k)
        img[int(y - 14):int(y - 6), int(x + 18):int(x + 40)] = C("2a2a30")  # anvil
        particles(img, 20, k, (x + 18, y - 40, x + 44, y - 14), "ffd080", (0, 1), (0.6, 1.0))
    particles(img, 140, 5, (0, 0, W, H * 0.7), "ffa040", (0, 1), (0.3, 0.9))
    darken_edges(img, 0.5)
    return finish(img, 15)


def intro_shot02():
    """A black tide climbing the slopes, steam where it touches lava; inside it walks the Saltmother's column."""
    img = canvas()
    vgrad(img, [(0, "0a0a10"), (0.6, "2a2026"), (1, "6a3a2a")], 0, int(H * 0.55))
    ridge(img, H * 0.3, 26, 120, "1a1214", 503, jag=12)
    glow(img, W * 0.8, H * 0.3, 140, LAVA, 0.45, 2.0, ry=40)
    _terraces(img, H * 0.36, 4, seed=13, lit=0.8)
    prof = _tide(img, H * 0.56, seed=21)
    _water_column(img, W * 0.32, prof[int(W * 0.32)] + 20, H * 0.12, 30, seed=4)
    for dx in (-8, 6):
        img[int(H * 0.18):int(H * 0.18) + 3, int(W * 0.32 + dx):int(W * 0.32 + dx + 5)] = C("f0f0f8")
    glow(img, W * 0.32, H * 0.185, 30, "e0e0ff", 0.5, 2)
    darken_edges(img, 0.55)
    return finish(img, 14)


def intro_shot03():
    """Tamsin Reed at the ash road, lantern-pole raised, the forges of Kethra behind her. Carts moving west."""
    img = canvas()
    vgrad(img, [(0, "160a0c"), (0.6, "4a1a14"), (1, "a0482a")], 0, int(H * 0.6))
    ridge(img, H * 0.42, 20, 100, "221416", 507)
    for k, x in enumerate((360, 430, 500, 580)):
        _forge(img, x, H * 0.6, 30, 20, lit=0.8)
    vgrad(img, [(0, "3a302c"), (1, "1a1416")], int(H * 0.6), H)
    poly(img, [(W * 0.1, H), (W * 0.42, H * 0.6), (W * 0.5, H * 0.6), (W * 0.55, H)], "4a403a")
    particles(img, 220, 9, (0, 0, W, H), "8a807a", (0, 1), (0.3, 0.7), add=False)  # falling ash
    for k in range(3):  # carts moving west
        x = W * (0.3 - k * 0.1)
        y = H * (0.68 + k * 0.06)
        img[int(y - 14 - 3 * k):int(y - 4), int(x - 20 - 4 * k):int(x + 20 + 4 * k)] = C("3a2a22")
        for wx in (-14, 14):
            img[int(y - 6):int(y), int(x + wx - 3):int(x + wx + 3)] = C("1a1414")
        glow(img, x, y - 16, 18, "ffa040", 0.3, 2)
    t, _, _, _ = figure("tamsin", Pose(arm_n=(2.5, 0.2, 0.2), arm_f=(0.2, 0.15, 0.4), head_turn=-0.3), height_px=190,
                        yaw=-1.0, rim=(255, 160, 90))
    paste(img, t, W * 0.74, H * 1.02)
    glow(img, W * 0.77, H * 0.38, 60, "ffd080", 0.5, 2)
    darken_edges(img, 0.5)
    return finish(img, 15)


# ------------------------------------------------------------------ ember_herald

def herald_shot01():
    """The Saltmother's water-column bursting apart on the steps; her empty grey eyes going dark."""
    img = canvas()
    vgrad(img, [(0, "0a0c12"), (0.7, "1e2228"), (1, "3a3030")], 0, int(H * 0.7))
    for k in range(6):  # basalt steps
        y = H * (0.62 + k * 0.065)
        img[int(y):H, :] = C("201a1c") * (0.7 + 0.06 * k)
        img[int(y):int(y) + 2, :] = C("4a3e3a")
    _spray(img, W * 0.5, H * 0.42, seed=7)
    o, _, _, _ = figure("herald_ourra", Pose(arm_n=(1.6, 0.6, 0.2), arm_f=(1.4, 0.6, 0.2), head=-0.4, fall=0.15),
                        height_px=170, yaw=-0.25, rim=(180, 200, 220), spec_over=dict(extra=None, motes=[]))
    o = tint(o, "6a7480", 0.35)
    paste(img, o, W * 0.5, H * 0.7)
    particles(img, 60, 17, (W * 0.3, H * 0.1, W * 0.7, H * 0.7), "dcdce6", (0, 1), (0.3, 0.8))
    darken_edges(img, 0.55)
    return finish(img, 14)


def herald_shot02():
    """A cage of crusted salt breaking open; Brannoc staggers out and grabs his hammer, its head flaring."""
    img = canvas()
    vgrad(img, [(0, "0e0c10"), (1, "2a2224")], 0, H)
    glow(img, W * 0.5, H * 0.55, 260, "c8c0b8", 0.18, 1.6)
    rng = np.random.default_rng(31)
    for k in range(16):  # salt cage shards blown outwards
        a = -math.pi * (0.05 + 0.9 * k / 15)
        r0, r1 = 120 + rng.uniform(0, 40), 200 + rng.uniform(0, 60)
        cx, cy = W * 0.45, H * 0.85
        p0 = (cx + math.cos(a) * r0, cy + math.sin(a) * r0 * 0.9)
        p1 = (cx + math.cos(a) * r1, cy + math.sin(a) * r1 * 0.9)
        nx, ny = -math.sin(a) * 9, math.cos(a) * 9
        poly(img, [(p0[0] - nx, p0[1] - ny), (p0[0] + nx, p0[1] + ny), p1], "d8d4cc" if k % 2 else "a8a49c")
    particles(img, 260, 32, (W * 0.1, H * 0.1, W * 0.9, H * 0.9), "e8e4dc", (0, 1), (0.4, 1.0), add=False)
    img[int(H * 0.88):H, :] = C("2a2426")
    b, _, _, _ = figure("brannoc", Pose(lean=0.25, arm_n=(1.2, 0.1, 0.5), arm_f=(-0.3, 0.3, 0.6), leg_n=(0.5, 0.3),
                                        leg_f=(-0.3, 0.2), glow=1.0, head=0.1), height_px=220, yaw=-0.85,
                        rim=(255, 170, 100))
    paste(img, b, W * 0.45, H * 1.02)
    glow(img, W * 0.6, H * 0.6, 50, "ffa040", 0.7, 1.8)
    darken_edges(img, 0.5)
    return finish(img, 15)


def herald_shot03():
    """Brannoc on the wall of Brazier Hold, hammer on his shoulder, grinning."""
    img = canvas()
    vgrad(img, [(0, "1a0e14"), (0.6, "6a2a1e"), (1, "d0703a")], 0, int(H * 0.62))
    ridge(img, H * 0.5, 22, 120, "2a1416", 511)
    for x in (80, 180, 300):
        _forge(img, x, H * 0.62, 26, 18, lit=0.7)
    img[int(H * 0.7):H, :] = C("3a302e")
    for x in range(0, W, 40):
        img[int(H * 0.64):int(H * 0.7), x:x + 24] = C("4a3e3a")
        img[int(H * 0.64):int(H * 0.64) + 2, x:x + 24] = C("6a5a52")
    for y in range(int(H * 0.72), H, 14):
        img[y, :] = C("2a2220")
    _banner(img, W * 0.18, H * 0.38, 40)
    _banner(img, W * 0.9, H * 0.36, 40, "c8902a")
    b, _, _, _ = figure("brannoc", Pose(arm_n=(2.6, 0.25, 1.9), arm_f=(0.1, 0.25, 0.6), head_turn=-0.3, weapon=1.4),
                        height_px=230, yaw=-0.6, rim=(255, 170, 100))
    paste(img, b, W * 0.58, H * 0.98)
    particles(img, 80, 41, (0, 0, W, H * 0.7), "ffa040", (0, 1), (0.3, 0.9))
    darken_edges(img, 0.45)
    return finish(img, 15)


# ------------------------------------------------------------------ ember_warden

def _caldera(img, lit=1.0):
    vgrad(img, [(0, "0c0608"), (0.6, "2a1012"), (1, "5a2014")], 0, int(H * 0.6))
    poly(img, [(0, H * 0.2), (W * 0.25, H * 0.35), (W * 0.75, H * 0.35), (W, H * 0.2), (W, H), (0, H)], "1a1214")
    vgrad(img, [(0, "ff9a40"), (1, "a0300e")], int(H * 0.78), H)
    n = fbm(H, W, 16, 61, 3)
    sub = img[int(H * 0.78):]
    k = np.clip((n[int(H * 0.78):, :] - 0.45) * 5, 0, 1)[..., None]
    sub[:] = sub * (1 - k) + C("2a1a16") * k
    glow(img, W * 0.5, H * 0.85, 400, LAVA, 0.35 * lit, 2.0, ry=80)


def warden_shot01():
    """The Cinder Tyrant collapsing in grey fire; from the cracked basalt steps rises Ignar, orange heart burning."""
    img = canvas()
    _caldera(img)
    # the Cinder Tyrant: a huge collapsing shape of grey-white fire, left
    rng = np.random.default_rng(71)
    for k in range(40):
        x = W * 0.2 + rng.normal(0, 40)
        y = H * 0.45 + rng.normal(0, 50) + k * 1.2
        glow(img, x, y, rng.uniform(14, 34), "d0ccd0", 0.35, 1.6)
    smoke(img, W * 0.2, H * 0.7, 200, "8a8690", seed=7, lean=-0.2, width=40, amt=0.6)
    particles(img, 160, 72, (0, H * 0.1, W * 0.45, H * 0.8), "dcdce6", (0, 1), (0.3, 0.9))
    for k in range(5):  # cracked steps
        y = H * (0.62 + k * 0.035)
        img[int(y):int(y) + 8, int(W * 0.45 - k * 20):int(W * 0.95 + k * 10)] = C("241c1e") * (0.8 + 0.05 * k)
        img[int(y):int(y) + 1, int(W * 0.45 - k * 20):int(W * 0.95 + k * 10)] = C("ff8a3a") * 0.6
    i, _, _, _ = figure("ignar", Pose(arm_n=(0.3, 0.3, 0.4), arm_f=(0.2, 0.3, 0.4), head=-0.15, glow=0.6),
                        height_px=200, yaw=-1.0, rim=(255, 150, 80), ambient=0.24)
    paste(img, i, W * 0.7, H * 0.75)
    glow(img, W * 0.72, H * 0.42, 60, LAVA, 0.5, 1.8)
    darken_edges(img, 0.5)
    return finish(img, 14)


def warden_shot02():
    """Ignar kneeling to Brannoc and the Emberfolk, his heart-light warming their faces."""
    img = canvas()
    vgrad(img, [(0, "0a0608"), (1, "2a1412")], 0, H)
    img[int(H * 0.86):H, :] = C("2a2224")
    i, _, _, _ = figure("ignar", Pose(head=0.6, lean=0.3, arm_n=(1.0, 0.1, 1.7), arm_f=(0.1, 0.2, 0.3)),
                        height_px=250, yaw=-2.4, rim=(255, 150, 80), ambient=0.24)
    paste(img, i, W * 0.7, H * 0.94)
    glow(img, W * 0.55, H * 0.55, 230, "ff9a40", 0.45, 1.8)
    b, _, _, _ = figure("brannoc", Pose(arm_n=(0.1, 0.15, 0.4), arm_f=(-0.1, 0.15, 0.4), head=-0.1), height_px=170,
                        yaw=-0.7, rim=(255, 170, 100), key=(0.75, 0.4, 0.5))
    paste(img, b, W * 0.3, H * 0.94)
    for k, (x, h) in enumerate(((W * 0.12, 120), (W * 0.2, 104), (W * 0.42, 110))):
        _emberfolk(img, x, H * 0.94, h, seed=k + 1)
    darken_edges(img, 0.5)
    return finish(img, 15)


def warden_shot03():
    """Pyrrhenhall flooding with steam; Emberfolk carry glowing iron pots west toward the gold light of Solenne."""
    img = canvas()
    vgrad(img, [(0, "0a0a12"), (0.6, "2a2430"), (0.85, "6a5a50"), (1, "c8a060")], 0, int(H * 0.5))
    glow(img, W * 0.06, H * 0.48, 160, "ffd890", 0.6, 1.8, ry=40)  # Solenne in the west
    stars(img, 60, 81, int(H * 0.3), 0.5)
    ridge(img, H * 0.5, 14, 110, "1a1618", 513)
    smoke(img, W * 0.86, H * 0.5, 220, "c8c4c8", seed=9, lean=0.2, width=70, amt=0.55)  # the flooded caldera
    glow(img, W * 0.86, H * 0.42, 120, "ff8a3a", 0.25, 2.0)
    vgrad(img, [(0, "2a2224"), (1, "120e10")], int(H * 0.5), H)
    path = [(W * (1 - t), H * (0.55 + 0.38 * t ** 1.5)) for t in np.linspace(0, 1, 18)][::-1]
    rng = np.random.default_rng(83)
    for k, (x, y) in enumerate(path[2:16]):  # a line of lights going down the mountain
        h = 10 + (y - H * 0.55) * 0.5
        if h < 30:
            img[int(y - h):int(y), int(x - 1):int(x + 2)] = C("1a1416")
            glow(img, x + 2, y - h * 0.5, 8, "ffa040", 0.9, 2)
        else:
            _emberfolk(img, x + rng.uniform(-8, 8), y, h, seed=k, pot=True, back=False)
    i, _, _, _ = figure("ignar", Pose(leg_n=(0.3, 0.1), leg_f=(-0.2, 0.2), arm_n=(0.2, 0.1, 0.3)), height_px=250,
                        yaw=-2.3, rim=(255, 200, 140), ambient=0.22)
    paste(img, i, W * 0.78, H * 1.02)
    darken_edges(img, 0.5)
    return finish(img, 15)


INTRO = [intro_shot01, intro_shot02, intro_shot03]
HERALD = [herald_shot01, herald_shot02, herald_shot03]
WARDEN = [warden_shot01, warden_shot02, warden_shot03]
SHOTS = INTRO
