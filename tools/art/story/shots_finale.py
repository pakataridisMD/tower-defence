"""Stills for the finale of the defence campaign: "dawn" (Oswin returns) and "heart_falls"."""
from __future__ import annotations

import math

import numpy as np

from cinema import (C, H, W, canvas, darken_edges, fbm, figure, finish, glow, noise1, particles, paste, poly, ridge,
                    rotate_rgba, silhouette, smoke, stars, tint, vgrad)
from rig import Pose
from shots_midpoint import houses, unbound
from shots_prologue import ELEMENT_COLS, solenne
from sdf import glow_mat, mat


def _inner_wall(img, y_top, y_bot, lit=0.5):
    img[int(y_top):int(y_bot), :] = C("8a8478") * lit
    for x in range(0, W, 22):
        img[int(y_top) - 10:int(y_top), x:x + 13] = C("9a9488") * lit
    for y in range(int(y_top), int(y_bot), 12):
        img[y, :] = C("6a6458") * lit


def dawn_shot01():
    """Battle at the inner wall. The eastern horizon tears with a line of white light."""
    img = canvas()
    vgrad(img, [(0, "040408"), (0.7, "0e0c16"), (1, "1a1420")], 0, int(H * 0.6))
    img[int(H * 0.52):int(H * 0.535), :] = C("ffffff")
    glow(img, W * 0.5, H * 0.53, 700, "e8f0ff", 0.55, 1.4, ry=60)
    ridge(img, H * 0.56, 6, 120, "0a080c", 301)
    vgrad(img, [(0, "1a161c"), (1, "0e0c10")], int(H * 0.58), H)
    rng = np.random.default_rng(301)
    for k in range(90):  # the horde below the wall, backlit
        t = rng.random()
        unbound(img, rng.uniform(0, W), H * 0.6 + t * H * 0.2, 3 + t * 7, seed=k)
    for k in range(10):  # towers firing from the wall
        x = W * (0.05 + k * 0.1)
        glow(img, x, H * 0.72, 22, ELEMENT_COLS[k % 6], 0.7, 2)
    _inner_wall(img, H * 0.8, H, lit=0.35)
    darken_edges(img, 0.45)
    return finish(img, 14)


def dawn_shot02():
    """A tall figure in glowing white robes walks up the east road through the horde; spirits freeze and fade."""
    img = canvas()
    vgrad(img, [(0, "0a0a14"), (0.55, "3a3a50"), (0.62, "e8ecf8"), (0.7, "2a2830")], 0, int(H * 0.7))
    glow(img, W * 0.5, H * 0.6, 500, "ffffff", 0.45, 1.6, ry=120)
    vgrad(img, [(0, "3a363c"), (1, "141216")], int(H * 0.66), H)
    poly(img, [(W * 0.44, H * 0.66), (W * 0.56, H * 0.66), (W * 0.82, H), (W * 0.18, H)], "4a4648")
    rng = np.random.default_rng(302)
    for k in range(70):
        t = rng.random()
        x = rng.uniform(0, W)
        y = H * 0.66 + t * H * 0.34
        d = abs(x - W * 0.5) / (W * 0.5)
        if d < 0.22:
            continue
        unbound(img, x, y, 4 + t * 12, seed=k)
        if d < 0.45:  # freezing: grey glass, fading
            img[int(y - 12 * t - 4):int(y + 2), int(x - 12 * t - 4):int(x + 12 * t + 4)] = \
                img[int(y - 12 * t - 4):int(y + 2), int(x - 12 * t - 4):int(x + 12 * t + 4)] * 0.5 + C("c8d0e0") * 0.5
    rgba, _, _, _ = figure("oswin_white", Pose(arm_n=(0.9, 0.2, 0.5), arm_f=(-0.1, 0.15, 0.3), leg_n=(0.3, 0.1),
                                               leg_f=(-0.25, 0.2), glow=1.0, cape=0.4),
                           height_px=170, yaw=0.4, pitch=0.05, rim=(255, 255, 255), rim_amt=1.8, ambient=0.25,
                           key=(0.0, 0.3, -0.9))
    paste(img, rgba, W * 0.5, H * 0.95)
    glow(img, W * 0.5, H * 0.55, 90, "fff8e0", 0.45, 1.6)
    # Nyxara at the edge, turning toward him
    nyx, _, _, _ = figure("nyxara", Pose(head_turn=0.6), height_px=230, yaw=-0.3, pitch=0.05, rim=(220, 220, 255),
                          rim_amt=1.4, ambient=0.08)
    paste(img, nyx, W * 0.13, H * 1.04)
    darken_edges(img, 0.4)
    return finish(img, 14)


def dawn_shot03():
    """Close on the lantern: white flame, six coloured sparks circling inside, a city reflected in each spark."""
    img = canvas()
    vgrad(img, [(0, "0a0a10"), (1, "1a1a24")], 0, H)
    cx, cy = W * 0.5, H * 0.5
    glow(img, cx, cy, 300, "fff6e0", 0.6, 1.4)
    # the lantern frame: brass cage
    for s in (-1, 1):
        img[int(cy - 120):int(cy + 120), int(cx + s * 70 - 5):int(cx + s * 70 + 5)] = C("d8b050")
        img[int(cy - 120):int(cy + 120), int(cx + s * 70 - 5)] = C("fff0a0")
    poly(img, [(cx - 84, cy - 120), (cx + 84, cy - 120), (cx + 40, cy - 160), (cx - 40, cy - 160)], "c89a40")
    poly(img, [(cx - 84, cy + 120), (cx + 84, cy + 120), (cx + 70, cy + 140), (cx - 70, cy + 140)], "a87a30")
    glow(img, cx, cy, 50, "ffffff", 1.4, 1.2)
    ys, xs = np.mgrid[0:H, 0:W]
    flame = (((xs - cx) / 22) ** 2 + ((ys - cy - 10) / 46) ** 2 < 1) & (ys > cy - 56 + np.abs(xs - cx) * 1.2)
    img[flame] = C("ffffff")
    for k in range(6):
        a = k / 6 * 2 * math.pi + 0.3
        x, y = cx + math.cos(a) * 46, cy + math.sin(a) * 70
        glow(img, x, y, 26, ELEMENT_COLS[k], 1.0, 2)
        # a tiny city reflected in the spark: walls and a dome
        img[int(y + 1):int(y + 4), int(x - 7):int(x + 7)] = C("ffffff")
        img[int(y - 3):int(y + 1), int(x - 3):int(x + 3)] = C("ffffff")
    return finish(img, 14)


def dawn_shot04():
    """Oswin, white-haired, standing tall at the foot of the wall below the Queen."""
    img = canvas()
    vgrad(img, [(0, "1a1e30"), (1, "4a4a5a")], 0, H)
    _inner_wall(img, H * 0.08, H * 0.78, lit=0.75)
    img[int(H * 0.78):, :] = C("3a363a")
    q, _, _, _ = figure("ysolde_blind", Pose(arm_n=(0.4, 0.1, 1.2), arm_f=(0.4, 0.1, 1.2), head=0.45), height_px=110,
                        yaw=-1.6, pitch=-0.3, rim=(255, 240, 210), rim_amt=1.2, ambient=0.2)
    paste(img, q, W * 0.66, H * 0.1)
    o, _, _, _ = figure("oswin_white", Pose(arm_n=(0.25, 0.15, 0.4), arm_f=(-0.05, 0.15, 0.3), head=-0.35, glow=0.8),
                        height_px=250, yaw=-1.3, pitch=0.1, rim=(255, 250, 230), rim_amt=1.5, ambient=0.2)
    paste(img, o, W * 0.4, H * 1.0)
    glow(img, W * 0.45, H * 0.3, 120, "fff6e0", 0.35, 1.8)
    darken_edges(img, 0.4)
    return finish(img, 14)


def dawn_shot05():
    """Oswin raises the lantern; light pours into the empty Sunstone frame; it blazes; real dawn floods the field."""
    img = canvas()
    vgrad(img, [(0, "4a6aa0"), (0.5, "e8a070"), (0.8, "ffd8a0"), (1, "fff0d0")], 0, int(H * 0.75))
    solenne(img, W * 0.5, H * 0.92, scale=0.9, sun=False, lit=0.95)
    sx, sy = W * 0.5, H * 0.18
    for u in np.linspace(0, 1, 60):  # the beam from the lantern to the frame
        glow(img, W * 0.2 + (sx - W * 0.2) * u, H * 0.75 + (sy - H * 0.75) * u, 14, "fff8e0", 0.1, 1.5)
    glow(img, sx, sy, 300, "ffe090", 0.9, 1.4)
    ys, xs = np.mgrid[0:H, 0:W]
    ring = np.abs(((xs - sx) / 120) ** 2 + ((ys - sy) / 26) ** 2 - 1) < 0.12
    img[ring] = C("fff0c0")
    img[(((xs - sx) / 112) ** 2 + ((ys - sy) / 22) ** 2) < 1] = C("ffffff")
    vgrad(img, [(0, "8a7a5a"), (1, "5a4a3a")], int(H * 0.92), H)
    o, _, _, _ = figure("oswin_white", Pose(arm_n=(2.7, 0.15, 0.1), arm_f=(0.3, 0.2, 0.5), glow=1.0, cape=0.6, head=-0.3),
                        height_px=170, yaw=-0.6, pitch=0.05, rim=(255, 255, 240), rim_amt=1.6, ambient=0.3)
    paste(img, o, W * 0.16, H * 1.02)
    darken_edges(img, 0.25)
    return finish(img, 16)


def _sundered_heart(img, cx, cy, r, collapse=0.0, seed=0):
    """A floating knot of Sunstone shards and Heartstone light, collapsing as collapse goes to 1."""
    rng = np.random.default_rng(seed)
    glow(img, cx, cy, r * 2.4, "fff0c0", 0.6 * (1 - collapse * 0.5), 1.6)
    for k in range(40):
        a = rng.uniform(0, 2 * math.pi)
        d = rng.uniform(0.3, 1.0) * r
        x = cx + math.cos(a) * d
        y = cy + math.sin(a) * d * 0.8 + collapse * rng.uniform(0, 1) * r * 1.8
        L = rng.uniform(8, 26) * (1 - collapse * 0.4)
        ang = a + rng.uniform(-0.6, 0.6)
        col = C(ELEMENT_COLS[k % 6]) * 0.6 + C("fff0d0") * 0.4
        pts = [(x - math.cos(ang) * L, y - math.sin(ang) * L), (x + math.cos(ang + 1.5) * 4, y + math.sin(ang + 1.5) * 4),
               (x + math.cos(ang) * L, y + math.sin(ang) * L), (x - math.cos(ang + 1.5) * 4, y - math.sin(ang + 1.5) * 4)]
        poly(img, pts, col)


def heart_shot01():
    """The knot of shards collapsing in dawn light. In the middle, Cassivane on his knees, ash, the locket in his hands."""
    img = canvas()
    vgrad(img, [(0, "5a6a90"), (0.6, "e8a878"), (1, "ffd8a8")], 0, int(H * 0.7))
    vgrad(img, [(0, "6a5a4a"), (1, "3a3028")], int(H * 0.7), H)
    _sundered_heart(img, W * 0.5, H * 0.42, 150, collapse=0.6, seed=3)
    rgba, _, _, _ = figure("cassivane_ashen", Pose(leg_n=(1.4, 2.2), leg_f=(1.2, 2.3), bob=-0.58, lean=0.35, head=0.5,
                                                   arm_n=(0.9, 0.1, 1.4), arm_f=(0.9, 0.1, 1.4)),
                           height_px=170, yaw=-1.2, pitch=0.05, rim=(255, 220, 170), rim_amt=1.4, ambient=0.18,
                           spec_over=dict(weapon=None, locket_hand="n", shards=[]))
    paste(img, rgba, W * 0.5, H * 1.08)
    particles(img, 140, 311, (W * 0.3, H * 0.3, W * 0.8, H * 0.9), "6a6064", (0, 1), (0.4, 0.9), add=False)
    darken_edges(img, 0.35)
    return finish(img, 14)


def heart_shot02():
    """Ilyra kneeling in front of him, taking his hands."""
    img = canvas()
    vgrad(img, [(0, "8a7a8a"), (0.6, "f0b080"), (1, "ffd8a8")], 0, int(H * 0.72))
    glow(img, W * 0.5, H * 0.6, 320, "fff0d0", 0.5, 1.6)
    vgrad(img, [(0, "6a5a4a"), (1, "3a3028")], int(H * 0.72), H)
    kneel = dict(leg_n=(1.4, 2.2), leg_f=(1.2, 2.3), bob=-0.58, lean=0.2)
    c, _, _, _ = figure("cassivane_ashen", Pose(head=0.3, arm_n=(1.3, 0.05, 0.3), arm_f=(1.3, 0.05, 0.3), **kneel),
                        height_px=230, yaw=-0.2, pitch=0.05, rim=(255, 220, 170), rim_amt=1.4, ambient=0.18,
                        spec_over=dict(weapon=None, locket_hand="n", shards=[]))
    paste(img, c, W * 0.34, H * 1.05)
    i, _, _, _ = figure("ilyra", Pose(head=0.2, arm_n=(1.4, 0.05, 0.3), arm_f=(1.4, 0.05, 0.3), **kneel),
                        height_px=200, yaw=-2.95, pitch=0.05, rim=(255, 220, 170), rim_amt=1.4, ambient=0.2)
    paste(img, i, W * 0.64, H * 1.05)
    particles(img, 80, 321, (W * 0.2, H * 0.2, W * 0.6, H * 0.8), "7a7074", (0, 1), (0.4, 0.9), add=False)
    darken_edges(img, 0.35)
    return finish(img, 14)


def heart_shot03():
    """Cassivane's face, the grey leaving his eyes; he presses the locket into her hand and crumbles into ash."""
    img = canvas()
    vgrad(img, [(0, "e8b088"), (1, "ffe0b8")], 0, H)
    glow(img, W * 0.7, H * 0.3, 300, "fff8e8", 0.6, 1.6)
    c, _, _, _ = figure("cassivane_ashen", Pose(head=0.1, arm_n=(1.1, 0.05, 0.9), arm_f=(0.2, 0.1, 0.3)),
                        height_px=600, yaw=-1.0, pitch=0.05, rim=(255, 230, 190), rim_amt=1.6, ambient=0.2,
                        key=(0.7, 0.5, 0.4), spec_over=dict(weapon=None, locket_hand="n", shards=[]),
                        mats_over=dict(eye=mat("6a7a9a", flat=1.0)))
    # crumble: drop pixels on the right side into drifting ash
    a = c[..., 3] > 0
    h, w = a.shape
    rng = np.random.default_rng(331)
    xs = np.arange(w)[None, :]
    crumble = a & (rng.random(a.shape) < np.clip((xs / w - 0.35) * 2.0, 0, 1))
    c = c.copy()
    c[crumble, 3] = 0
    paste(img, c, W * 0.4, H * 2.25)
    particles(img, 400, 332, (W * 0.45, 0, W, H), "5a5054", (0, 1), (0.5, 1.0), add=False)
    glow(img, W * 0.38, H * 0.92, 20, "ffd060", 0.8, 2)
    darken_edges(img, 0.3)
    return finish(img, 14)


def heart_shot04():
    """Ysolde on the wall, face lifted to the light, crying, smiling; the six peoples cheering in a city lit gold."""
    img = canvas()
    vgrad(img, [(0, "6a8ac0"), (0.6, "ffc890"), (1, "ffe8c0")], 0, int(H * 0.6))
    solenne(img, W * 0.62, H * 0.95, scale=0.85, sun=False, lit=1.1)
    rng = np.random.default_rng(341)
    for _ in range(300):  # banners and cheering crowds: specks of six colours
        x, y = rng.uniform(0, W), rng.uniform(H * 0.72, H)
        img[int(y), int(x)] = C(ELEMENT_COLS[int(rng.integers(0, 6))])
    q, _, _, _ = figure("ysolde_blind", Pose(arm_n=(0.4, 0.1, 1.2), arm_f=(0.4, 0.1, 1.2), head=-0.35),
                        height_px=280, yaw=-1.15, pitch=0.05, rim=(255, 230, 180), rim_amt=1.4, ambient=0.25,
                        key=(0.6, 0.7, 0.4), spec_over=dict(weapon=None))
    paste(img, q, W * 0.2, H * 1.1)
    darken_edges(img, 0.3)
    return finish(img, 16)


def heart_shot05():
    """Oswin, Corvin, Tamsin and the Wardens around the Heartstone. Oswin looking east toward the Rift."""
    img = canvas()
    vgrad(img, [(0, "2a2a3a"), (1, "4a4450")], 0, H)
    for k in range(7):  # the open hall's columns
        x = W * (0.04 + k * 0.155)
        img[:int(H * 0.8), int(x):int(x + 22)] = C("d8d0c0") * 0.7
        img[:int(H * 0.8), int(x + 16):int(x + 22)] = C("a89c88") * 0.7
    img[int(H * 0.8):, :] = C("5a5450")
    glow(img, W * 0.5, H * 0.62, 160, "fff0c0", 0.9, 1.6)
    ys, xs = np.mgrid[0:H, 0:W]
    stone = ((xs - W * 0.5) / 26) ** 2 + ((ys - H * 0.62) / 34) ** 2 < 1
    img[stone] = C("fff8e0")
    for (cid, x, hgt, yaw, pose) in (("tamsin", W * 0.24, 150, -0.9, Pose()),
                                     ("corvin", W * 0.36, 175, -0.7, Pose()),
                                     ("nyxara", W * 0.8, 240, -2.6, Pose()),
                                     ("oswin_white", W * 0.64, 185, -0.1, Pose(head_turn=-0.4))):
        rgba, _, _, _ = figure(cid, pose, height_px=hgt, yaw=yaw, pitch=0.06, rim=(255, 240, 200), rim_amt=1.3, ambient=0.2)
        paste(img, rgba, x, H * 0.98)
    darken_edges(img, 0.4)
    return finish(img, 14)


def heart_shot06():
    """The army of the Concord marches out of Solenne's gates in dawn light, toward the Rift."""
    img = canvas()
    vgrad(img, [(0, "6a8ab8"), (0.55, "ffc890"), (1, "fff0d0")], 0, int(H * 0.6))
    ridge(img, H * 0.58, 14, 120, "8a7a8a", 361, top_col="a89098")
    img[int(H * 0.56):int(H * 0.57), int(W * 0.84):int(W * 0.96)] = C("6a3aa0")  # the Rift far off
    vgrad(img, [(0, "8a8a5a"), (1, "4a5a34")], int(H * 0.6), H)
    poly(img, [(W * 0.0, H), (W * 0.1, H * 0.86), (W * 0.86, H * 0.6), (W * 0.9, H * 0.6), (W * 0.3, H)], "a89a80")
    rng = np.random.default_rng(361)
    for k in range(260):  # the column of the army along the road, banners in six colours
        t = rng.random() ** 0.7
        x = W * 0.12 + t * W * 0.74 + rng.uniform(-10, 10) * (1 - t)
        y = H * 0.93 - t * H * 0.33 + rng.uniform(-4, 4) * (1 - t)
        hh = 3 + 18 * (1 - t)
        img[int(y - hh):int(y), int(x - hh * 0.2):int(x + hh * 0.2) + 1] = C("2a2a34")
        img[int(y - hh):int(y - hh * 0.8), int(x - hh * 0.2):int(x + hh * 0.2) + 1] = C("c8c8d0")
        if k % 9 == 0:
            img[int(y - hh * 1.8):int(y - hh), int(x):int(x) + 1] = C("4a3a2a")
            img[int(y - hh * 1.8):int(y - hh * 1.4), int(x) + 1:int(x + hh * 0.5) + 2] = C(ELEMENT_COLS[k % 6])
    solenne(img, W * 0.06, H * 0.99, scale=0.55, sun=True, lit=1.0)
    darken_edges(img, 0.3)
    return finish(img, 16)


DAWN = [dawn_shot01, dawn_shot02, dawn_shot03, dawn_shot04, dawn_shot05]
HEART_FALLS = [heart_shot01, heart_shot02, heart_shot03, heart_shot04, heart_shot05, heart_shot06]
