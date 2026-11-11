"""Stills for "The Night of Falling Stars" (night_of_falling_stars, 12 shots): the midpoint disaster."""
from __future__ import annotations

import math

import numpy as np

from cinema import (C, H, W, canvas, darken_edges, fbm, figure, finish, glow, noise1, particles, paste, poly, ridge,
                    rotate_rgba, silhouette, smoke, stars, tint, vgrad)
from rig import Pose
from shots_prologue import ELEMENT_COLS, solenne
from sdf import glow_mat, mat


def unbound(img, x, y, r, seed=0):
    """A grey-eyed Unbound spirit: a hunched grey blob with two empty white eyes."""
    ys, xs = np.mgrid[int(y - r * 1.2):int(y + r * 0.4), int(x - r * 1.2):int(x + r * 1.2)]
    ys = np.clip(ys, 0, H - 1)
    xs = np.clip(xs, 0, W - 1)
    body = (((xs - x) / r) ** 2 + ((ys - y) / (r * 0.7)) ** 2 <= 1) & (ys <= y + r * 0.25)
    img[ys[body], xs[body]] = C("5a5a66") - (ys[body, None] - y) * 1.5
    top = body & ~np.roll(body, 1, 0)
    img[ys[top], xs[top]] = C("a0a0ae")
    for dx in (-0.28, 0.28):
        ex, ey = int(x + r * dx + r * 0.2), int(y - r * 0.25)
        if 0 <= ey < H and 0 <= ex < W - 2:
            img[ey:ey + max(1, int(r / 6)), ex:ex + max(2, int(r / 4))] = C("f0f0f8")


def houses(img, y_base, side, depth=6, seed=0, lit=0.6, fire=False):
    """A street receding from one side: a row of gabled houses shrinking toward the centre."""
    rng = np.random.default_rng(seed)
    for k in range(depth):
        t = k / depth
        w = 120 * (1 - t * 0.75)
        h = 140 * (1 - t * 0.7)
        x0 = (0 if side < 0 else W) + side * -1 * (k * 70 * (1 - t * 0.4))
        x1 = x0 + side * -1 * w
        xa, xb = min(x0, x1), max(x0, x1)
        top = y_base - h - k * 2
        shade = 0.5 + 0.5 * (1 - t)
        col = C("2a2228") * shade * lit + 10
        img[int(top):int(y_base - k * 6), int(xa):int(xb)] = col
        poly(img, [(xa - 4, top), (xb + 4, top), ((xa + xb) / 2, top - h * 0.3)], C("3a2a2a") * shade * lit + 8)
        for wy in range(int(top + 14), int(y_base - 24), 26):
            for wx in range(int(xa + 10), int(xb - 12), 24):
                if rng.random() < 0.6:
                    lc = "ffb050" if not fire or rng.random() < 0.6 else "ff6a2a"
                    img[wy:wy + 10, wx:wx + 7] = C(lc) * (0.6 + 0.4 * rng.random())
                    glow(img, wx + 3, wy + 5, 14, lc, 0.12, 2)
        if fire and rng.random() < 0.5:
            glow(img, (xa + xb) / 2, top, 60, "ff6a2a", 0.5, 1.8)
            particles(img, 30, seed + k, (xa, top - 80, xb, top), "ffa040", (0, 1), (0.4, 1.0))


def shot01():
    """Solenne at dusk, the Sunstone glowing over a city packed with refugees. Lanterns everywhere. Quiet."""
    img = canvas()
    vgrad(img, [(0, "1a1a3a"), (0.5, "5a3a5a"), (0.8, "b06a5a"), (1, "d89070")], 0, int(H * 0.72))
    stars(img, 80, 21, int(H * 0.35), 0.5)
    ridge(img, H * 0.66, 12, 140, "3a2a3a", 211, top_col="5a3a4a")
    vgrad(img, [(0, "3a3036"), (1, "1e1a20")], int(H * 0.72), H)
    solenne(img, W * 0.5, H * 0.86, scale=1.0, sun=True, lit=0.62)
    # refugee camps and lanterns crowding every ring and the fields
    rng = np.random.default_rng(21)
    for _ in range(420):
        x = rng.uniform(0, W)
        y = rng.uniform(H * 0.7, H * 0.99)
        if abs(x - W / 2) < 300 * (1 - (H * 0.99 - y) / (H * 0.3)) + 20 or rng.random() < 0.5:
            img[int(y), int(x)] = C("ffc070") * rng.uniform(0.6, 1.1)
    for _ in range(40):  # tents
        x, y = rng.uniform(10, W - 10), rng.uniform(H * 0.86, H * 0.97)
        poly(img, [(x - 7, y), (x + 7, y), (x, y - 8)], C("6a5a50") * rng.uniform(0.7, 1.0))
        glow(img, x, y - 3, 8, "ffb060", 0.25, 2)
    darken_edges(img, 0.4)
    return finish(img, 14)


def _gate(img, cx, top, bottom, half_w, open_amt=1.0, light="2a3a5a"):
    """The great east gate seen from inside: a towering arch with the doors swinging in."""
    img[:int(bottom), :] = img[:int(bottom), :]
    wall = C("4a4652")
    img[int(top - 60):int(bottom), :] = wall
    for y in range(int(top - 60), int(bottom), 14):
        img[y, :] = C("3a3640")
        off = (y // 14) % 2 * 18
        for x in range(off, W, 36):
            img[y:y + 14, x] = C("3a3640")
    ys, xs = np.mgrid[0:H, 0:W]
    arch = ((np.abs(xs - cx) < half_w) & (ys > top)) | (((xs - cx) / half_w) ** 2 + ((ys - top) / (half_w * 0.6)) ** 2 < 1)
    arch &= ys < bottom
    img[arch] = C(light)
    return arch


def shot02():
    """The east gate swinging open; Lanternguard stand aside with grey empty eyes; the Unbound pour in."""
    img = canvas()
    vgrad(img, [(0, "0e0c18"), (1, "1e1a28")], 0, H)
    cx, top, bottom = W * 0.5, H * 0.32, H * 0.86
    arch = _gate(img, cx, top, bottom, 110, light="1a1830")
    # outside, under the arch: a grey glow and the horde pouring in
    glow(img, cx, H * 0.7, 160, "8a8a9a", 0.45, 1.5)
    rng = np.random.default_rng(22)
    for k in range(60):
        t = rng.random()
        y = H * 0.62 + t * H * 0.3
        x = cx + rng.uniform(-1, 1) * (40 + t * 140)
        unbound(img, x, y, 4 + t * 12, seed=k)
    # the doors swung inwards
    for s in (-1, 1):
        x0 = cx + s * 110
        poly(img, [(x0, top - 30), (x0 + s * 70, top - 10), (x0 + s * 70, bottom + 30), (x0, bottom)], "3a2a20")
        for k in range(5):
            yb = top + k * 50
            poly(img, [(x0, yb), (x0 + s * 70, yb + 8), (x0 + s * 70, yb + 12), (x0, yb + 4)], "6a6a74")
    vgrad(img, [(0, "2a2830"), (1, "141218")], int(bottom), H)
    # hollowed guards standing aside, both sides of the gate
    for k, (x, hgt, yaw) in enumerate(((W * 0.1, 150, -0.2), (W * 0.22, 130, -0.4), (W * 0.8, 130, -2.7), (W * 0.92, 150, -2.9))):
        rgba, _, _, _ = figure("lanternguard_hollow", Pose(arm_n=(0.2, 0.1, 0.3), arm_f=(-0.05, 0.1, 0.25)), height_px=hgt,
                               yaw=yaw, pitch=0.08, rim=(170, 170, 200), rim_amt=1.2, ambient=0.1)
        paste(img, rgba, x, H * 1.02)
    darken_edges(img, 0.5)
    return finish(img, 14)


def shot03():
    """Hollowed soldiers fighting in the streets; refugees running; Lanternguard fighting their own."""
    img = canvas()
    vgrad(img, [(0, "1a0e14"), (0.6, "4a1e1e"), (1, "6a2a20")], 0, int(H * 0.7))
    houses(img, H * 0.74, -1, seed=31, fire=True)
    houses(img, H * 0.74, 1, seed=32, fire=True)
    smoke(img, W * 0.55, H * 0.55, 200, "1e1418", seed=33, lean=0.2, width=30)
    vgrad(img, [(0, "3a2a26"), (1, "1a1414")], int(H * 0.72), H)
    for y in range(int(H * 0.74), H, 10):  # cobbles
        img[y, :] *= 0.8
    rng = np.random.default_rng(33)
    for k in range(18):  # refugees running away, small and dark
        x, y = rng.uniform(W * 0.3, W * 0.7), rng.uniform(H * 0.74, H * 0.8)
        hh = 10 + (y - H * 0.74) * 0.6
        img[int(y - hh):int(y), int(x - 2):int(x + 2)] = C("1a1416")
        img[int(y - hh - 3):int(y - hh), int(x - 1):int(x + 2)] = C("2a2024")
    # a loyal guard against a hollowed one
    loyal, _, _, _ = figure("tamsin", Pose(arm_n=(1.6, 0.2, 0.3), arm_f=(0.6, 0.3, 0.9), lean=0.15, leg_n=(0.5, 0.2),
                                           leg_f=(-0.4, 0.2), cape=0.3),
                            height_px=170, yaw=-0.5, pitch=0.08, rim=(255, 140, 80), rim_amt=1.3, ambient=0.1,
                            spec_over=dict(hair=None, helm="steel", weapon=dict(type="sword", blade="steel", guard="gold",
                                                                              grip="leather")))
    paste(img, loyal, W * 0.3, H * 1.03)
    foe, _, _, _ = figure("lanternguard_hollow", Pose(arm_n=(-1.2, 0.3, 1.0), arm_f=(0.5, 0.3, 0.7), lean=0.1,
                                                      leg_n=(0.4, 0.2), leg_f=(-0.4, 0.2)),
                          height_px=170, yaw=-2.6, pitch=0.08, rim=(255, 140, 80), rim_amt=1.3, ambient=0.1,
                          spec_over=dict(weapon=dict(type="sword", blade="blade", guard="steel", grip="leather")))
    paste(img, foe, W * 0.66, H * 1.03)
    glow(img, W * 0.48, H * 0.55, 30, "ffe0a0", 0.5, 2.5)  # sparks where the blades meet
    particles(img, 20, 34, (W * 0.44, H * 0.48, W * 0.54, H * 0.6), "fff0c0", (0, 0), (0.6, 1.0))
    darken_edges(img, 0.45)
    return finish(img, 14)


def _gatehouse(img):
    vgrad(img, [(0, "1e1a1e"), (1, "2a2428")], 0, H)
    for y in range(0, H, 20):
        img[y, :] = C("161214")
        for x in range((y // 20) % 2 * 30, W, 60):
            img[y:y + 20, x] = C("161214")
    # an arrow slit full of firelight
    img[int(H * 0.15):int(H * 0.6), int(W * 0.72):int(W * 0.76)] = C("ff9040")
    glow(img, W * 0.74, H * 0.38, 120, "ff7a3a", 0.5, 1.8)


def shot04():
    """Old Fennick in the gatehouse, firing half-built towers that crackle with unstable elements."""
    img = canvas()
    _gatehouse(img)
    # half-built towers on the gatehouse floor, crackling in six colours
    for k in range(4):
        tx = W * (0.5 + k * 0.13)
        ty = H * 0.9 - k * 6
        img[int(ty - 70 + k * 8):int(ty), int(tx - 12):int(tx + 12)] = C("5a5250") * (1 - k * 0.12)
        img[int(ty - 72 + k * 8):int(ty - 66 + k * 8), int(tx - 14):int(tx + 14)] = C("7a7270")
        col = ELEMENT_COLS[(k * 2 + 1) % 6]
        glow(img, tx, ty - 80 + k * 8, 40, col, 0.9, 2.0)
        rng = np.random.default_rng(40 + k)
        x, y = tx, ty - 80 + k * 8
        for _ in range(20):  # crackling arcs
            nx, ny = x + rng.uniform(-8, 8), y + rng.uniform(-8, 4)
            for u in np.linspace(0, 1, 6):
                img[int(y + (ny - y) * u), int(x + (nx - x) * u)] = C("ffffff")
            x, y = nx, ny
    img[int(H * 0.9):, :] = C("1a1416")
    rgba, _, _, _ = figure("fennick", Pose(arm_n=(1.4, 0.3, 0.3), arm_f=(0.4, 0.3, 1.2), lean=0.1, glow=1.0),
                           height_px=210, yaw=-0.5, pitch=0.08, rim=(255, 160, 90), rim_amt=1.3, ambient=0.14,
                           key=(0.6, 0.6, 0.5))
    paste(img, rgba, W * 0.24, H * 1.06)
    darken_edges(img, 0.45)
    return finish(img, 14)


def shot05():
    """Fennick shouting over his shoulder, then turning back to the gate as it starts to fall."""
    img = canvas()
    _gatehouse(img)
    particles(img, 120, 51, (0, 0, W, H * 0.6), "a89a90", (0, 1), (0.1, 0.4))
    rgba, _, _, _ = figure("fennick", Pose(arm_n=(0.4, 0.3, 1.2), arm_f=(0.2, 0.2, 0.4), head=-0.2, head_turn=-0.6),
                           height_px=520, yaw=-2.2, pitch=0.05, rim=(255, 150, 80), rim_amt=1.6, ambient=0.12,
                           key=(0.7, 0.5, -0.2), spec_over=dict(weapon=None))
    paste(img, rgba, W * 0.42, H * 2.15)
    darken_edges(img, 0.5)
    return finish(img, 14)


def shot06():
    """The gatehouse collapsing in a cloud of dust and coloured sparks. Silence."""
    img = canvas()
    vgrad(img, [(0, "0e0c14"), (1, "2a2228")], 0, H)
    ridge(img, H * 0.82, 6, 80, "141018", 61)
    # the falling gatehouse: tilted blocks
    rng = np.random.default_rng(61)
    for k in range(26):
        x = W * 0.5 + rng.normal() * 70
        y = H * 0.45 + rng.normal() * 50 + k * 3
        s = rng.uniform(8, 22)
        a = rng.uniform(0, 1.5)
        pts = [(x + math.cos(a + q * math.pi / 2) * s, y + math.sin(a + q * math.pi / 2) * s) for q in range(4)]
        poly(img, pts, C("4a4450") * rng.uniform(0.6, 1.0))
    # dust cloud
    n = fbm(H, W, 30, 62)
    ys, xs = np.mgrid[0:H, 0:W]
    d = np.hypot((xs - W * 0.5) / 260, (ys - H * 0.72) / 120)
    dust = np.clip((1 - d) * 1.6 * n, 0, 1)[..., None]
    img[:] = img * (1 - dust * 0.85) + C("8a7e78") * (0.6 + 0.6 * n[..., None]) * dust * 0.85
    for k in range(6):
        particles(img, 30, 63 + k, (W * 0.2, H * 0.2, W * 0.8, H * 0.8), ELEMENT_COLS[k], (0, 1), (0.5, 1.0))
    darken_edges(img, 0.5)
    return finish(img, 14)


def spire(img, cx, base, top, width, col="d8d0c8", lit=1.0):
    poly(img, [(cx - width, base), (cx - width * 0.35, top + 20), (cx, top), (cx + width * 0.35, top + 20), (cx + width, base)],
         C(col) * 0.55 * lit)
    poly(img, [(cx - width * 0.15, base), (cx - width * 0.35, top + 20), (cx, top), (cx, base)], C(col) * 0.8 * lit)


def shot07():
    """Cassivane at the top of the Spire, red armour blackening, a crystal blade glowing six colours; the Sunstone above."""
    img = canvas()
    vgrad(img, [(0, "0a0814"), (0.6, "1e1428"), (1, "2a1a2a")], 0, H)
    stars(img, 160, 71, int(H * 0.5), 0.6)
    # the Sunstone lens, huge above him
    sx, sy = W * 0.5, H * 0.12
    glow(img, sx, sy, 280, "ffc860", 0.55, 1.6)
    ys, xs = np.mgrid[0:H, 0:W]
    lens = ((xs - sx) / 210) ** 2 + ((ys - sy) / 46) ** 2 < 1
    img[lens] = C("ffd870") * (1.05 - (xs[lens, None] - sx) / 600)
    img[lens & (((xs - sx) / 200) ** 2 + ((ys - sy + 10) / 30) ** 2 < 1) & (ys < sy - 8)] = C("fff4c0")
    # the spire top he stands on
    poly(img, [(W * 0.25, H), (W * 0.36, H * 0.82), (W * 0.64, H * 0.82), (W * 0.75, H)], "3a3240")
    img[int(H * 0.82):int(H * 0.84), int(W * 0.36):int(W * 0.64)] = C("6a6070")
    mats = dict(enamel=mat("6a1e1e", spec=0.8, tex=0.25, tex_freq=120), crystal=glow_mat("ffffff"))
    rgba, _, _, _ = figure("cassivane", Pose(arm_n=(2.6, 0.15, 0.1), arm_f=(0.3, 0.2, 0.6), head=-0.3, cape=0.8,
                                             leg_n=(0.25, 0.1), leg_f=(-0.2, 0.1)),
                           height_px=230, yaw=-0.9, pitch=0.0, rim=(255, 200, 120), rim_amt=1.5, ambient=0.08,
                           key=(0.0, 0.9, 0.4), mats_over=mats,
                           spec_over=dict(weapon=dict(type="sword", blade="crystal", guard="gold", grip="leather")))
    paste(img, rgba, W * 0.5, H * 0.95)
    for k in range(6):
        glow(img, W * 0.53 + (k - 2.5) * 4, H * 0.18 + k * 8, 26, ELEMENT_COLS[k], 0.5, 2.0)
    particles(img, 50, 72, (W * 0.3, H * 0.4, W * 0.7, H * 0.9), "5a4a4a", (0, 1), (0.4, 0.9), add=False)
    darken_edges(img, 0.4)
    return finish(img, 14)


def shot08():
    """The Sunstone shattering; its pieces fall across the city like burning stars."""
    img = canvas()
    vgrad(img, [(0, "100818"), (0.7, "3a1a2a"), (1, "5a2a2a")], 0, int(H * 0.75))
    solenne(img, W * 0.5, H * 0.98, scale=0.75, sun=False, lit=0.45)
    rng = np.random.default_rng(81)
    cx, cy = W * 0.5, H * 0.15
    glow(img, cx, cy, 160, "ffe0a0", 0.9, 1.6)
    for k in range(70):  # burning shards with streaks
        a = rng.uniform(0.15 * math.pi, 0.85 * math.pi)
        dist = rng.uniform(20, 380)
        x, y = cx + math.cos(a) * dist * 1.4, cy + math.sin(a) * dist * 0.8
        if not (0 <= x < W and 0 <= y < H):
            continue
        L = rng.uniform(10, 40)
        for u in np.linspace(0, 1, int(L)):
            xx, yy = x - math.cos(a) * L * u, y - math.sin(a) * L * u
            if 0 <= int(yy) < H and 0 <= int(xx) < W:
                img[int(yy), int(xx)] = img[int(yy), int(xx)] * u + C("ffc060") * (1 - u)
        col = ELEMENT_COLS[k % 6] if k % 3 == 0 else "fff0c0"
        glow(img, x, y, rng.uniform(6, 16), col, 0.9, 1.8)
        img[int(y) - 1:int(y) + 2, int(x) - 1:int(x) + 2] = C("ffffff")
    darken_edges(img, 0.35)
    return finish(img, 14)


def shot09():
    """Ysolde in the palace courtyard, looking up as the light falls on her face; white-out. Tamsin drags her into cover."""
    img = canvas()
    vgrad(img, [(0, "fffaf0"), (0.4, "f8e8c8"), (1, "c8b090")], 0, H)
    glow(img, W * 0.6, 0, 500, "ffffff", 1.0, 1.2)
    # courtyard pillars, washed out
    for k in range(6):
        x = W * (0.05 + k * 0.19)
        img[int(H * 0.15):, int(x):int(x + 18)] = C("e8dcc8")
        img[int(H * 0.15):, int(x + 14):int(x + 18)] = C("c8b8a0")
    ys_, ysol, _, _ = figure("ysolde", Pose(arm_n=(0.3, 0.3, 0.6), arm_f=(0.6, 0.3, 0.9), head=-0.6, lean=-0.15),
                             height_px=220, yaw=-1.3, pitch=0.0, rim=(255, 255, 240), rim_amt=1.8, ambient=0.4,
                             key=(0.2, 0.9, 0.5))
    paste(img, ys_, W * 0.55, H * 1.05)
    tam, _, _, _ = figure("tamsin", Pose(arm_n=(1.3, 0.2, 0.3), arm_f=(1.1, 0.2, 0.5), lean=0.4, leg_n=(0.6, 0.4),
                                         leg_f=(-0.5, 0.2)),
                          height_px=200, yaw=-2.6, pitch=0.0, rim=(255, 255, 240), rim_amt=1.6, ambient=0.3,
                          key=(0.2, 0.9, 0.5), spec_over=dict(weapon=None))
    paste(img, tam, W * 0.3, H * 1.05)
    img[:] = img * 0.7 + 255 * 0.3  # the white-out
    return finish(img, 14)


def shot10():
    """Cassivane, ash drifting from his armour, stepping through a rip of darkness, carrying the shards in a net of grey light."""
    img = canvas()
    vgrad(img, [(0, "0a0810"), (1, "1e1620")], 0, H)
    stars(img, 100, 101, H, 0.4)
    # the rip: a jagged vertical tear full of nothing, with a violet rim
    pts_l, pts_r = [], []
    for k in range(40):
        y = H * 0.05 + k * H * 0.9 / 39
        w = 60 * math.sin(k / 39 * math.pi) + 6
        j = (noise1(40, 6, 102)[k] - 0.5) * 30
        pts_l.append((W * 0.62 + j - w, y))
        pts_r.append((W * 0.62 + j + w, y))
    for (x, y) in pts_l + pts_r:
        glow(img, x, y, 22, "8a40d0", 0.18, 2)
    poly(img, pts_l + pts_r[::-1], "000000")
    rgba, _, _, _ = figure("cassivane_ashen", Pose(arm_n=(0.9, 0.3, 0.6), arm_f=(0.3, 0.2, 0.4), leg_n=(0.45, 0.1),
                                                   leg_f=(-0.35, 0.2), lean=0.1, cape=0.6),
                           height_px=240, yaw=-0.4, pitch=0.05, rim=(190, 120, 255), rim_amt=1.6, ambient=0.06,
                           spec_over=dict(weapon=None))
    paste(img, rgba, W * 0.5, H * 1.02)
    # the net of grey light holding the shards
    nx, ny = W * 0.42, H * 0.58
    for k in range(10):
        a = k / 10 * 2 * math.pi
        for u in np.linspace(0, 1, 40):
            img[int(ny + math.sin(a) * 34 * u), int(nx + math.cos(a) * 40 * u)] = C("b8b8c8")
    rng = np.random.default_rng(103)
    for k in range(9):
        glow(img, nx + rng.uniform(-28, 28), ny + rng.uniform(-24, 24), 12, ELEMENT_COLS[k % 6], 0.9, 2)
    particles(img, 120, 104, (W * 0.3, H * 0.1, W * 0.7, H * 0.9), "8a8288", (0, 1), (0.3, 0.8), add=False)
    darken_edges(img, 0.45)
    return finish(img, 14)


def shot11():
    """Over the dark city, one falling shard of white light drifts sideways, east, toward the distant Rift."""
    img = canvas()
    vgrad(img, [(0, "04040a"), (1, "141020")], 0, H)
    ridge(img, H * 0.74, 10, 160, "0a080e", 111)
    solenne(img, W * 0.3, H * 0.98, scale=0.55, sun=False, lit=0.2, ruined=True)
    # the Rift far to the east: a violet line on the horizon
    img[int(H * 0.72):int(H * 0.73), int(W * 0.8):int(W * 0.98)] = C("6a3aa0")
    glow(img, W * 0.9, H * 0.72, 60, "6a3aa0", 0.3, 2)
    # the drifting shard and its long faint trail
    for u in np.linspace(0, 1, 120):
        x = W * 0.3 + u * W * 0.35
        y = H * 0.18 + u * H * 0.22 - math.sin(u * 3) * 10
        glow(img, x, y, 3 + 4 * u, "c8d0ff", 0.05 * u, 1.5)
    glow(img, W * 0.65, H * 0.4, 40, "e8f0ff", 0.9, 2)
    img[int(H * 0.4) - 1:int(H * 0.4) + 2, int(W * 0.65) - 1:int(W * 0.65) + 2] = C("ffffff")
    darken_edges(img, 0.4)
    return finish(img, 14)


def shot12():
    """Dawn hour. A black sky over Solenne. Only torches. Refugees looking up."""
    img = canvas()
    vgrad(img, [(0, "000000"), (1, "0a0a10")], 0, H)
    solenne(img, W * 0.5, H * 0.7, scale=0.6, sun=False, lit=0.18, ruined=True)
    vgrad(img, [(0, "141014"), (1, "0a080a")], int(H * 0.7), H)
    rng = np.random.default_rng(121)
    for k in range(34):  # a crowd of refugees looking up, lit by torches
        x = rng.uniform(0, W)
        y = H * 0.76 + rng.uniform(0, H * 0.24)
        hh = 18 + (y - H * 0.76) * 0.5
        img[int(y - hh):int(y), int(x - hh * 0.16):int(x + hh * 0.16)] = C("1a1618")
        img[int(y - hh * 1.22):int(y - hh * 0.98), int(x - hh * 0.12):int(x + hh * 0.12)] = C("2a2224")
        img[int(y - hh * 1.2):int(y - hh * 1.1), int(x - hh * 0.12):int(x + hh * 0.12)] = C("8a5a3a")  # torch-lit faces, upturned
        if k % 5 == 0:
            tx = x + hh * 0.3
            img[int(y - hh * 1.4):int(y - hh * 0.6), int(tx):int(tx) + 2] = C("3a2a1a")
            glow(img, tx, y - hh * 1.45, 26, "ff9a40", 0.7, 2)
            particles(img, 6, 122 + k, (tx - 6, y - hh * 1.9, tx + 6, y - hh * 1.4), "ffc060", (0, 0), (0.5, 1.0))
    darken_edges(img, 0.55)
    return finish(img, 14)


SHOTS = [shot01, shot02, shot03, shot04, shot05, shot06, shot07, shot08, shot09, shot10, shot11, shot12]
