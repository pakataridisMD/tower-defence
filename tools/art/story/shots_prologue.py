"""Stills for the prologue, "The Last Lantern" (data/story/cinematics/prologue.json, 12 shots)."""
from __future__ import annotations

import math

import numpy as np

from cinema import (C, H, W, black_sun, canvas, darken_edges, element_sea, fbm, figure, finish, glow, noise1, particles,
                    paste, poly, ridge, rotate_rgba, scale_nearest, silhouette, smoke, stars, tint, vgrad)
from rig import Pose
from sdf import glow_mat, mat

ELEMENT_COLS = ["e8502a", "dce8ff", "6ad04a", "2ac0c0", "d89a3a", "a060f0"]


def shot01():
    """Black. A churning sea of every colour at once, no horizon."""
    img = canvas("000000")
    element_sea(img, 0, H, seed=4, sat=0.85)
    darken_edges(img, 0.85, 1.6)
    glow(img, W * 0.5, H * 0.55, 260, "403848", 0.35)
    return finish(img, 12)


def _seven(img, base_y, height, black_idx=6, spacing=70, glow_amt=1.0):
    figs = []
    for i in range(7):
        x = W / 2 + (i - 3) * spacing
        rgba, _, _, _ = figure("oswin_white", Pose(arm_n=(0.1, 0.15, 0.3), arm_f=(-0.1, 0.15, 0.3)), height_px=height,
                               yaw=-1.5, pitch=0.05, spec_over=dict(weapon=None, hat=None, beard=None, motes=[], hem=None,
                                                                   long_hair=False, hair=None, brows=None))
        if i == black_idx:
            sil = silhouette(rgba, "040306", rim_col="5a5a66")
        else:
            col = ELEMENT_COLS[i]
            sil = silhouette(rgba, col, rim_col="ffffff")
            sil = tint(rgba, col, 0.75)
            glow(img, x, base_y - height * 0.55, height * 0.9, col, 0.55 * glow_amt, 2.4)
        figs.append((sil, x))
    return figs


def shot02():
    """Seven tall silhouettes rise from the sea in a line; the seventh is black with no colour."""
    img = canvas("000000")
    vgrad(img, [(0, "06050a"), (1, "14101c")], 0, int(H * 0.62))
    stars(img, 160, 2, int(H * 0.6), 0.6)
    element_sea(img, int(H * 0.62), H, seed=5, sat=0.7)
    for y in range(int(H * 0.62), H):  # perspective: the far sea is darker
        img[y] *= 0.45 + 0.55 * (y - H * 0.62) / (H * 0.38)
    figs = _seven(img, int(H * 0.7), 150)
    for sil, x in figs:
        paste(img, sil, x, int(H * 0.72))
    # the sea laps round their shins
    element_sea_band = canvas("000000")
    element_sea(element_sea_band, int(H * 0.68), H, seed=5, sat=0.7)
    img[int(H * 0.705):] = img[int(H * 0.705):] * 0.25 + element_sea_band[int(H * 0.705):] * 0.75
    darken_edges(img, 0.6)
    return finish(img, 14)


def shot03():
    """The black figure walks forward; colours freeze to grey glass at his feet; the black sun above."""
    img = canvas("000000")
    vgrad(img, [(0, "100c18"), (0.7, "2a2236"), (1, "3a3040")], 0, int(H * 0.6))
    stars(img, 120, 3, int(H * 0.55), 0.5)
    black_sun(img, W * 0.68, H * 0.24, 34, seed=7)
    element_sea(img, int(H * 0.6), H, seed=6, sat=0.8)
    # a cone of grey glass spreading from his feet towards the viewer
    ys, xs = np.mgrid[0:H, 0:W]
    fx, fy = W * 0.42, H * 0.66
    spread = (ys - fy) * 0.75 + 14
    glass = (ys >= fy - 6) & (np.abs(xs - fx) < spread)
    edge = fbm(H, W, 6, 9) * 18
    glass &= np.abs(xs - fx) < spread - edge
    g = fbm(H, W, 10, 11)
    grey = (np.stack([g, g, g], -1) * 90 + 70) * np.array([0.92, 0.94, 1.0])
    crack = (np.abs(np.sin(xs * 0.21 + ys * 0.13 + g * 9)) < 0.08)
    grey[crack] = grey[crack] * 1.6
    img[glass] = grey[glass]
    rgba, _, _, _ = figure("oswin_white", Pose(**{"leg_n": (0.35, 0.1), "leg_f": (-0.3, 0.2), "arm_n": (-0.2, 0.15, 0.2),
                                                  "arm_f": (0.25, 0.15, 0.2)}), height_px=130, yaw=-1.25, pitch=0.12,
                           spec_over=dict(weapon=None, beard=None, hair=None, brows=None, motes=[], hem=None, long_hair=False))
    sil = silhouette(rgba, "030205", rim_col="8a80a8", rim_side=-1)
    paste(img, sil, fx, fy + 4)
    darken_edges(img, 0.6)
    return finish(img, 14)


def shot04():
    """Top-down: the six in a ring, opposites across; the black figure flung out past the edge of the stars."""
    img = canvas("02020a")
    ys, xs = np.mgrid[0:H, 0:W]
    stars(img, 700, 4, H, 0.9)
    cx, cy, R = W * 0.42, H * 0.52, 105
    # the edge of the starfield: beyond it, nothing
    edge = (xs - W * 0.86) + (fbm(H, W, 30, 3) - 0.5) * 50 > 0
    img[edge] = C("000000")
    glow(img, cx, cy, 190, "302a50", 0.6)
    order = [0, 1, 2, 3, 4, 5]  # fire, storm, nature, water, earth, void around the ring; opposites are 3 apart
    for k, i in enumerate(order):
        a = -math.pi / 2 + k * math.pi / 3
        x, y = cx + math.cos(a) * R, cy + math.sin(a) * R
        glow(img, x, y, 46, ELEMENT_COLS[i], 1.1, 2.0)
        glow(img, x, y, 12, "ffffff", 0.9, 1.5)
        # joined hands: arcs of light between neighbours
        a2 = a + math.pi / 3
        for t in np.linspace(0, 1, 40):
            aa = a + (a2 - a) * t
            px, py = cx + math.cos(aa) * R, cy + math.sin(aa) * R
            img[int(py) - 1:int(py) + 1, int(px) - 1:int(px) + 1] += C(ELEMENT_COLS[i]) * 0.6
    # thin lines across the ring, opposite to opposite
    for k in range(3):
        a = -math.pi / 2 + k * math.pi / 3
        for t in np.linspace(-1, 1, 160):
            px, py = cx + math.cos(a) * R * t, cy + math.sin(a) * R * t
            img[int(py), int(px)] += 45
    # the black figure tumbling out through the edge, trailing grey
    bx, by = W * 0.9, H * 0.3
    for t in np.linspace(0, 1, 60):
        px, py = cx + (bx - cx) * t, cy + (by - cy) * t
        r = 2 + 5 * t
        glow(img, px, py, r * 2, "6a6a7a", 0.12 * t, 1.5)
    img[int(by) - 7:int(by) + 7, int(bx) - 5:int(bx) + 5] = C("000000")
    glow(img, bx, by, 14, "8a80b0", 0.4, 3.0)
    return finish(img, 14)


def solenne(img, cx, base_y, scale=1.0, sun=True, lit=1.0, seed=0, ruined=False):
    """Solenne from the east at dawn: six concentric walls, each a different stone, rising to the hall."""
    stones = ["e8e2d4", "d8c8a8", "c8d0d8", "b8c8b0", "d0b8a0", "c0b8d0"]
    for ring in range(6):
        rx = (300 - ring * 44) * scale
        top = base_y - (ring * 17 + 18) * scale
        wall_h = (14 + ring * 2) * scale
        col = C(stones[ring])
        # the wall: a lens-shaped band (top of the ring seen from slightly above)
        for x in range(int(cx - rx), int(cx + rx)):
            if not 0 <= x < W:
                continue
            u = (x - cx) / rx
            arc = math.sqrt(max(0, 1 - u * u))
            y_top = top + (1 - arc) * 6 * scale
            y_bot = y_top + wall_h * (0.6 + 0.4 * arc)
            light = 0.55 + 0.45 * (-u * 0.7 + 0.3)
            c = col * light * lit
            img[int(y_top):int(y_bot), x] = c
            img[int(y_top), x] = col * min(1.15, light + 0.3) * lit
            if (x // max(2, int(4 * scale))) % 2 == 0:  # crenels
                img[int(y_top) - max(1, int(2 * scale)):int(y_top), x] = c
            # roofs and windows between this wall and the next
            if ring < 5 and (x * 7 + ring * 13) % 23 < 9:
                rh = int((5 + (x * 31 + ring) % 6) * scale)
                img[int(y_top) - rh:int(y_top) - max(1, int(2 * scale)), x] = C("7a5a4a" if ring % 2 else "6a6a7a") * light * lit
            if (x * 13 + ring * 7) % 37 == 0:
                wy = int((y_top + y_bot) / 2)
                img[wy:wy + max(1, int(2 * scale)), x:x + 1] = C("ffd080") * (1.2 - lit * 0.3)
        # towers on each ring
        for k in range(5 + ring):
            u = -0.9 + 1.8 * k / max(1, 4 + ring)
            tx = cx + u * rx * 0.95
            th = (26 + ring * 3) * scale
            tw = max(3, int(5 * scale))
            ty = top + (1 - math.sqrt(max(0, 1 - u * u))) * 6 * scale
            light = 0.55 + 0.45 * (-u * 0.7 + 0.3)
            img[int(ty - th):int(ty + 2), int(tx - tw / 2):int(tx + tw / 2)] = col * light * lit
            poly(img, [(tx - tw * 0.8, ty - th), (tx + tw * 0.8, ty - th), (tx, ty - th - 9 * scale)],
                 C("4a5a8a") * light * lit)
    # the open hall and the Heartstone at the centre
    hy = base_y - 6 * 17 * scale - 30 * scale
    img[int(hy):int(hy + 26 * scale), int(cx - 26 * scale):int(cx + 26 * scale)] = C("f0ece0") * 0.8 * lit
    for k in range(7):
        x = int(cx - 24 * scale + k * 8 * scale)
        img[int(hy - 6 * scale):int(hy + 26 * scale), x:x + max(1, int(2 * scale))] = C("fffaf0") * lit
    poly(img, [(cx - 32 * scale, hy - 6 * scale), (cx + 32 * scale, hy - 6 * scale), (cx, hy - 26 * scale)], C("e8e0d0") * lit)
    glow(img, cx, hy + 8 * scale, 40 * scale, "fff0c0", 0.8 if not ruined else 0.2)
    glow(img, cx, hy + 8 * scale, 10 * scale, "ffffff", 1.0 if not ruined else 0.2)
    if sun:  # the golden Sunstone lens hanging in the sky
        sy = hy - 90 * scale
        glow(img, cx, sy, 70 * scale, "ffc860", 0.55, 1.8)
        for x in range(int(cx - 22 * scale), int(cx + 22 * scale)):
            u = (x - cx) / (22 * scale)
            hh = math.sqrt(max(0, 1 - u * u)) * 7 * scale
            img[int(sy - hh):int(sy + hh) + 1, x] = C("ffd870") * (1.0 - 0.3 * u)
        img[int(sy - 1), int(cx - 16 * scale):int(cx - 2 * scale)] = C("fffbe0")


def shot05():
    """Dawn over Solenne."""
    img = canvas()
    vgrad(img, [(0, "2a3a6a"), (0.45, "c87a5a"), (0.75, "ffc880"), (1, "ffe8b0")], 0, int(H * 0.72))
    glow(img, W * 0.18, H * 0.66, 260, "ffd890", 0.6, 1.6)
    stars(img, 40, 5, int(H * 0.25), 0.4)
    ridge(img, H * 0.62, 26, 160, "6a5a7a", 51, top_col="9a7a8a")
    ridge(img, H * 0.70, 14, 90, "4a4a5a", 52, top_col="6a5a6a")
    vgrad(img, [(0, "4a5a3a"), (1, "2a3a24")], int(H * 0.74), H)
    solenne(img, W * 0.55, H * 0.84, scale=1.0, sun=True)
    # mist at the walls' feet
    m = fbm(H, W, 40, 13)
    band = np.exp(-((np.arange(H) - H * 0.82) / 14) ** 2)[:, None]
    img += (m * band)[..., None] * C("ffe0c0") * 0.5
    darken_edges(img, 0.35)
    return finish(img, 16)


def shot06():
    """Night. Cassivane alone on a balcony with the gold locket; the crown-shaped gap faint in the stars."""
    img = canvas()
    vgrad(img, [(0, "05060e"), (0.7, "141a30"), (1, "1e2238")], 0, H)
    stars(img, 380, 6, int(H * 0.8), 0.9)
    # faint crown gap among the stars, over his shoulder
    ys, xs = np.mgrid[0:H, 0:W]
    gx, gy = W * 0.72, H * 0.28
    rel = np.arctan2(ys - gy, xs - gx)
    d = np.hypot(xs - gx, ys - gy)
    teeth = np.cos((rel + math.pi / 2) / 0.5 * math.pi * 1.5) > 0
    hole = (np.abs(((rel + math.pi / 2 + math.pi) % (2 * math.pi)) - math.pi) < 0.5) & (d < np.where(teeth, 70, 42)) & (d > 18)
    img[hole] *= 0.25
    glow(img, gx, gy, 90, "3a3058", 0.25)
    # far city lights below
    ridge(img, H * 0.8, 6, 60, "0a0c14", 61)
    particles(img, 120, 6, (0, H * 0.8, W, H), "ffc070", (0, 0), (0.2, 0.7))
    # the balcony: stone balustrade
    img[int(H * 0.78):, :int(W * 0.62)] = C("1a1820")
    for x in range(0, int(W * 0.62), 14):
        img[int(H * 0.7):int(H * 0.78), x + 3:x + 9] = C("2a2632")
        img[int(H * 0.7):int(H * 0.78), x + 3] = C("4a4458")
    img[int(H * 0.68):int(H * 0.705), :int(W * 0.62)] = C("3a3644")
    img[int(H * 0.68), :int(W * 0.62)] = C("6a6478")
    rgba, fx, fy, _ = figure("cassivane", Pose(arm_n=(0.75, 0.05, 1.6), arm_f=(0.05, 0.15, 0.25), head=0.35),
                             height_px=330, yaw=0.55, pitch=0.02, rim=(140, 160, 255), rim_amt=1.6,
                             key=(0.7, 0.3, -0.7), ambient=0.04, spec_over=dict(weapon=None, locket_hand="n"))
    paste(img, rgba, W * 0.3, H * 1.55)
    glow(img, W * 0.37, H * 0.62, 18, "ffd060", 0.5, 2.0)  # the locket catches the light
    darken_edges(img, 0.45)
    return finish(img, 14)


def shot07():
    """The Hollow Rift: violet grass, a ring of black pillars, the Black Comet, a crack of nothing."""
    img = canvas()
    vgrad(img, [(0, "0a0618"), (0.6, "2a1240"), (1, "4a2060")], 0, int(H * 0.6))
    stars(img, 260, 7, int(H * 0.55), 0.8)
    # the comet: black head, grey-violet tail
    hx, hy = W * 0.64, H * 0.16
    for t in np.linspace(0, 1, 140):
        px, py = hx - 240 * t, hy - 40 * t + 10 * t * t
        glow(img, px, py, 8 + 22 * t, "6a5a8a", 0.05 * (1 - t), 1.2)
    glow(img, hx, hy, 18, "b8a0ff", 0.6, 2.0)
    img[int(hy) - 4:int(hy) + 4, int(hx) - 4:int(hx) + 4] = C("000000")
    ridge(img, H * 0.55, 18, 120, "1e0e2e", 71, top_col="3a1a4a")
    vgrad(img, [(0, "5a2a78"), (1, "2a1240")], int(H * 0.58), H)
    g = fbm(H, W, 3, 72)
    grass = (g > 0.55) & (np.arange(H)[:, None] > H * 0.58)
    img[grass] = img[grass] * 1.35 + C("301040") * 0.2
    # the crack of nothing, opening toward us
    cx = W * 0.5
    pts_l, pts_r = [], []
    for k in range(30):
        y = H * 0.66 + k * (H * 0.34 / 29)
        wdt = 2 + (k / 29) ** 1.6 * 48
        j = (noise1(30, 6, 73)[k] - 0.5) * 30
        pts_l.append((cx + j - wdt, y))
        pts_r.append((cx + j + wdt, y))
    poly(img, pts_l + pts_r[::-1], "000000")
    for (x, y) in pts_l + pts_r:
        glow(img, x, y, 10, "b080ff", 0.12, 2)
    # ring of black pillars, singing with stolen light
    for k in range(9):
        a = math.pi * (0.05 + 0.9 * k / 8)
        px = cx + math.cos(a) * 250
        py = H * 0.68 - math.sin(a) * 50
        hgt = 70 - math.sin(a) * 25
        wdt = 9 - math.sin(a) * 3
        img[int(py - hgt):int(py), int(px - wdt / 2):int(px + wdt / 2)] = C("08060c")
        img[int(py - hgt):int(py), int(px - wdt / 2)] = C("6a4a9a")
        glow(img, px, py - hgt * 0.7, 16, ELEMENT_COLS[k % 6], 0.5, 2.0)
    darken_edges(img, 0.5)
    return finish(img, 14)


def shot08():
    """Oswin at the lip of the Crack, lantern raised; towers burning in six colours behind; grey shapes crawl out."""
    img = canvas()
    vgrad(img, [(0, "0a0814"), (0.7, "2a1830"), (1, "3a2030")], 0, int(H * 0.62))
    stars(img, 140, 8, int(H * 0.5), 0.5)
    ridge(img, H * 0.56, 16, 140, "120a18", 81)
    # Spirewright towers burning in six colours along the horizon
    for k in range(6):
        tx = W * (0.08 + k * 0.17)
        ty = H * 0.58
        img[int(ty - 46):int(ty), int(tx - 5):int(tx + 5)] = C("1a1620")
        img[int(ty - 50):int(ty - 46), int(tx - 7):int(tx + 7)] = C("24202c")
        glow(img, tx, ty - 52, 40, ELEMENT_COLS[k], 0.9, 2.0)
        glow(img, tx, ty - 52, 8, "ffffff", 0.6, 1.5)
        particles(img, 25, 80 + k, (tx - 20, ty - 120, tx + 20, ty - 50), ELEMENT_COLS[k], (0, 0), (0.3, 0.9))
    vgrad(img, [(0, "2a2026"), (1, "141016")], int(H * 0.6), H)
    # the Crack, ahead of him, full of nothing
    poly(img, [(W * 0.55, H * 0.62), (W * 0.75, H * 0.64), (W * 1.0, H * 0.78), (W * 1.0, H), (W * 0.62, H),
               (W * 0.58, H * 0.8)], "000000")
    # grey shapes crawling out
    rng = np.random.default_rng(8)
    ys, xs = np.mgrid[0:H, 0:W]
    for _ in range(16):
        x = rng.uniform(W * 0.62, W * 0.98)
        y = rng.uniform(H * 0.7, H * 0.97)
        r = rng.uniform(6, 13)
        body = (((xs - x) / r) ** 2 + ((ys - y) / (r * 0.65)) ** 2 <= 1) & (ys <= y + r * 0.2)
        img[body] = C("54545e") + (ys[body, None] - y) * -2.0
        top = body & ~np.roll(body, 1, 0)
        img[top] = C("9a9aa8")
        for dx in (-0.25, 0.25):
            img[int(y - r * 0.2), int(x + r * dx):int(x + r * dx) + 2] = C("f0f0f8")
        glow(img, x, y, r * 2.2, "8a8a98", 0.18, 2)
    rgba, _, _, r = figure("oswin_grey", Pose(arm_n=(2.4, 0.2, 0.15), arm_f=(0.6, 0.3, 0.8), lean=0.05, cape=0.6,
                                              leg_n=(0.25, 0.1), leg_f=(-0.2, 0.15), glow=1.0),
                           height_px=240, yaw=-0.7, pitch=0.08, rim=(200, 150, 255), rim_amt=1.4, key=(0.25, 0.9, 0.3),
                           ambient=0.06)
    paste(img, rgba, W * 0.36, H * 1.08)
    glow(img, W * 0.5, H * 0.12, 140, "ffc860", 0.75, 1.8)
    darken_edges(img, 0.45)
    return finish(img, 14)


def shot09():
    """A blast of white light; the Crack slams shut; Oswin falls into the dark; one spark drifts after him."""
    img = canvas("000000")
    vgrad(img, [(0, "fffaf0"), (0.35, "f0e0c0"), (0.4, "1a1418"), (1, "000000")], 0, H)
    glow(img, W * 0.5, H * 0.32, 420, "ffffff", 0.7, 1.4)
    # the rock lips of the Crack closing at the top of the frame
    poly(img, [(0, H * 0.36), (W * 0.47, H * 0.4), (W * 0.47, H * 0.44), (0, H * 0.52)], "0e0a10")
    poly(img, [(W, H * 0.34), (W * 0.53, H * 0.4), (W * 0.53, H * 0.44), (W, H * 0.55)], "0e0a10")
    rgba, _, _, _ = figure("oswin_grey", Pose(arm_n=(2.8, 0.5, 0.2), arm_f=(2.6, 0.5, 0.3), lean=-0.4, head=-0.5,
                                              leg_n=(0.6, 0.6), leg_f=(-0.2, 0.9), cape=1.0),
                           height_px=120, yaw=-0.8, pitch=-0.8, rim=(255, 250, 230), rim_amt=1.5, ambient=0.05,
                           key=(0.0, 1.0, 0.1),
                           mats_over=dict(lamp=mat("3a3020")))
    rgba = rotate_rgba(rgba, 155)
    paste(img, rgba, W * 0.47, H * 0.98)
    glow(img, W * 0.56, H * 0.6, 10, "ffd070", 0.9, 1.5)
    img[int(H * 0.6), int(W * 0.56)] = C("fff8d0")
    darken_edges(img, 0.3)
    return finish(img, 14)


def _panel(fn, x0, y0, w, h, seed):
    """Paint a small montage panel with fn(img, box) on a scratch canvas and copy it in."""
    tmp = canvas()
    fn(tmp, seed)
    sub = tmp[int(H / 2 - h / 2):int(H / 2 + h / 2), int(W / 2 - w / 2):int(W / 2 + w / 2)]
    return sub


def shot10():
    """Six quick cuts (here one montage): each land's Warden gone wrong; then the hordes pour out."""
    img = canvas("08070a")
    pw, ph = 202, 176

    cx, cy = W / 2, H / 2  # panels are cropped round the centre: x 219..421, y 96..264
    L, R, T, B = cx - 101, cx + 101, cy - 84, cy + 84

    def volcano(t, s):
        vgrad(t, [(0, "2a2830"), (0.5, "4a4650"), (1, "6a6670")], 0, H)
        smoke(t, cx + 4, T + 62, 120, "2a2a30", seed=s, lean=0.25, width=14)
        poly(t, [(L - 10, B), (cx - 18, T + 64), (cx + 16, T + 62), (R + 10, B)], "28242a")
        poly(t, [(cx - 18, T + 64), (cx + 16, T + 62), (cx + 40, B), (cx + 10, B)], "34303a")
        glow(t, cx, T + 62, 60, "e8e8f8", 0.9, 1.6)
        rng = np.random.default_rng(s)
        for k in range(5):  # rivers of grey-white fire down the slope
            x, y = cx + rng.uniform(-12, 12), T + 66
            for _ in range(70):
                x += rng.uniform(-1.2, 1.2) + (x - cx) * 0.012
                y += 1.4
                t[int(y):int(y) + 2, int(x):int(x) + 2] = C("d8d8e8")
                glow(t, x, y, 5, "8a8a9a", 0.08, 2)
        particles(t, 90, s, (L, T, R, T + 70), "c8c8d4", (0, 1), (0.3, 0.8))

    def stormcloud(t, s):
        vgrad(t, [(0, "5a6070"), (0.7, "8a90a0"), (1, "a8acb4")], 0, H)
        ridge(t, B - 30, 3, 60, "4a5040", s, top_col="6a7058")
        ys, xs = np.mgrid[0:H, 0:W]
        cloud = np.zeros((H, W), bool)
        rng = np.random.default_rng(s)
        for _ in range(16):
            bx, by, r = cx + rng.uniform(-70, 70), cy - 20 + rng.uniform(-18, 14), rng.uniform(16, 30)
            cloud |= (xs - bx) ** 2 + ((ys - by) * 1.3) ** 2 < r * r
        top = cloud & ~np.roll(cloud, 3, 0)
        t[cloud] = C("0e0e16")
        t[top] = C("3a3a4a")
        # a ring of frozen lightning round it that never strikes
        for k in range(48):
            a0, a1 = k / 48 * 2 * math.pi, (k + 1) / 48 * 2 * math.pi
            j0, j1 = rng.uniform(-6, 6), rng.uniform(-6, 6)
            x0_, y0_ = cx + math.cos(a0) * 92 + j0, cy - 20 + math.sin(a0) * 42 + j0 * 0.5
            x1_, y1_ = cx + math.cos(a1) * 92 + j1, cy - 20 + math.sin(a1) * 42 + j1 * 0.5
            for u in np.linspace(0, 1, 8):
                xx, yy = x0_ + (x1_ - x0_) * u, y0_ + (y1_ - y0_) * u
                if 0 <= int(yy) < H and 0 <= int(xx) < W:
                    t[int(yy), int(xx):int(xx) + 2] = C("f0f6ff")
            glow(t, x0_, y0_, 8, "a8c0ff", 0.15, 2)

    def tree(t, s):
        vgrad(t, [(0, "1e2018"), (1, "3a3a2a")], 0, H)
        poly(t, [(cx - 20, B), (cx - 12, T + 70), (cx + 14, T + 70), (cx + 24, B)], "3a3024")
        poly(t, [(cx - 60, B), (cx - 20, B - 24), (cx - 16, B)], "3a3024")
        poly(t, [(cx + 64, B), (cx + 22, B - 26), (cx + 18, B)], "3a3024")
        t[int(T + 70):int(B), int(cx - 6):int(cx - 4)] = C("2a221a")
        rng = np.random.default_rng(s)
        ys, xs = np.mgrid[0:H, 0:W]
        for k in range(14):  # a sagging, rotting canopy
            bx, by, r = cx + rng.uniform(-85, 85), T + 40 + rng.uniform(-22, 24) + abs(rng.uniform(-1, 1)) * 10, rng.uniform(14, 26)
            m = (xs - bx) ** 2 + (ys - by) ** 2 < r * r
            sh = np.clip((ys - by) / r * 0.5 + 0.6, 0.3, 1.1)
            t[m] = (C("5a5e3e") * (1.25 - sh))[m][:, None].squeeze() if False else np.outer(1.25 - sh[m], C("5a5e3e"))
        holes = fbm(H, W, 8, s + 1) > 0.66
        canopy = (ys < T + 80) & (ys > T)
        t[holes & canopy] = t[holes & canopy] * 0.35
        particles(t, 70, s, (L, T + 40, R, B), "8a8a6a", (0, 1), (0.4, 0.9), add=False)

    def sea(t, s):
        vgrad(t, [(0, "141c28"), (0.5, "2a3a4a"), (1, "4a5e6e")], 0, H)
        rng = np.random.default_rng(s)
        for k in range(7):  # frozen heaving waves, nearer and taller down the panel
            yb = T + 46 + k * 19
            amp = 8 + k * 4
            for x in range(int(L) - 2, int(R) + 3):
                ph = (x * (0.05 + 0.01 * k) + k * 1.7)
                crest = yb - amp * max(0.0, math.sin(ph)) ** 3
                col = C("9ab8c8") * (0.6 + 0.07 * k)
                t[int(crest):int(yb + 22), x] = col * np.linspace(1.0, 0.45, int(yb + 22) - int(crest))[:, None] \
                    if int(yb + 22) > int(crest) else t[int(crest):int(yb + 22), x]
                t[int(crest), x] = C("eef8ff")
        particles(t, 60, s, (L, T, R, B), "e8f4ff", (0, 0), (0.4, 0.9), add=False)

    def mountain(t, s):
        vgrad(t, [(0, "2a2420"), (1, "5a4a3a")], 0, H)
        poly(t, [(L - 20, B), (cx - 30, T + 10), (cx + 10, T + 2), (R + 20, B)], "4a3e32")
        poly(t, [(cx + 10, T + 2), (R + 20, B), (cx + 30, B)], "3a3028")
        for dx in (-26, 18):  # two grey eyes opening in the rock
            glow(t, cx + dx, cy + 4, 26, "a8a8b8", 0.7, 1.6)
            poly(t, [(cx + dx - 12, cy + 4), (cx + dx, cy - 1), (cx + dx + 12, cy + 4), (cx + dx, cy + 8)], "e8e8f4")
            t[int(cy + 2):int(cy + 6), int(cx + dx - 2):int(cx + dx + 2)] = C("6a6a7a")
        for k in range(9):  # dead burning pines on its shoulders
            px = L + 10 + k * 22
            py = T + 40 + abs(px - cx) * 0.55
            t[int(py - 14):int(py), int(px):int(px) + 2] = C("1a1410")
            glow(t, px, py - 14, 7, "c8c8d0", 0.5, 2)

    def starless(t, s):
        vgrad(t, [(0, "000000"), (0.7, "0e0a14"), (1, "1e1828")], 0, H)
        black_sun(t, cx, cy - 10, 30, seed=s, corona_col="9a90b8")
        ridge(t, B - 16, 6, 30, "050408", s + 2)

    fns = [volcano, stormcloud, tree, sea, mountain, starless]
    for k, fn in enumerate(fns):
        x0 = 8 + (k % 3) * (pw + 8)
        y0 = 8 + (k // 3) * (ph + 0)
        sub = _panel(fn, x0, y0, pw, ph - 8, 100 + k)
        img[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] = sub
        img[y0:y0 + sub.shape[0], x0] = C("1a1820")
        img[y0, x0:x0 + sub.shape[1]] = C("1a1820")
        # the colour drained: each panel desaturated toward grey
        blk = img[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]]
        lum = blk.mean(-1, keepdims=True)
        img[y0:y0 + sub.shape[0], x0:x0 + sub.shape[1]] = blk * 0.45 + lum * 0.55
        glow_col = ELEMENT_COLS[k]
        img[y0 + sub.shape[0] - 3:y0 + sub.shape[0], x0:x0 + sub.shape[1]] = C(glow_col) * 0.8
    return finish(img, 14)


def shot11():
    """Refugees with carts on an ash road; Tamsin waves them on with her lantern-pole; a keystone is set."""
    img = canvas()
    vgrad(img, [(0, "3a3036"), (0.6, "8a6a5a"), (1, "c89a70")], 0, int(H * 0.55))
    glow(img, W * 0.85, H * 0.4, 200, "ff9a50", 0.4)
    ridge(img, H * 0.5, 14, 120, "4a3a3a", 111, top_col="6a5048")
    vgrad(img, [(0, "6a5e58"), (1, "3a3434")], int(H * 0.52), H)
    # the road, receding to the right
    poly(img, [(0, H * 0.95), (0, H * 0.78), (W * 0.9, H * 0.53), (W, H * 0.53), (W, H * 0.56)], "8a7e74")
    particles(img, 400, 11, (0, H * 0.5, W, H), "a89a90", (0, 0), (0.05, 0.25))
    # refugees and carts as small silhouettes along the road
    rng = np.random.default_rng(11)
    for k in range(26):
        t = k / 25
        x = W * 0.95 - t * W * 0.75 + rng.uniform(-8, 8)
        y = H * 0.55 + t * H * 0.26
        s = 0.35 + t * 0.9
        h = int(22 * s)
        if k % 6 == 3:  # a cart
            img[int(y - h * 0.7):int(y - h * 0.2), int(x - h * 0.9):int(x + h * 0.6)] = C("2a2220")
            for wx in (x - h * 0.6, x + h * 0.3):
                glow(img, wx, y - h * 0.15, h * 0.3, "000000", -0.0, 1)
                img[int(y - h * 0.35):int(y), int(wx - h * 0.18):int(wx + h * 0.18)] = C("1a1414")
        else:
            img[int(y - h):int(y), int(x - h * 0.18):int(x + h * 0.18)] = C("2a2426")
            img[int(y - h * 1.18):int(y - h * 0.95), int(x - h * 0.12):int(x + h * 0.12)] = C("3a3034")
            if k % 4 == 0:  # bundles on backs
                img[int(y - h * 0.9):int(y - h * 0.55), int(x - h * 0.35):int(x - h * 0.1)] = C("4a3a2a")
    rgba, _, _, _ = figure("tamsin", Pose(arm_n=(2.3, 0.35, 0.2), arm_f=(1.2, 0.5, 0.6), lean=0.0, head=-0.1, glow=0.8,
                                          leg_n=(0.2, 0.1), leg_f=(-0.25, 0.1)),
                           height_px=150, yaw=-1.0, pitch=0.12, rim=(255, 180, 110), rim_amt=1.1)
    paste(img, rgba, W * 0.2, H * 1.0)
    # inset: a gloved hand sets a glowing keystone into a tower foundation
    ix, iy, iw, ih = int(W * 0.62), int(H * 0.62), int(W * 0.33), int(H * 0.32)
    img[iy - 2:iy + ih + 2, ix - 2:ix + iw + 2] = C("1a1418")
    sub = canvas()
    vgrad(sub, [(0, "3a3438"), (1, "2a2428")], 0, H)
    for r in range(0, H, 40):
        for cxx in range((r // 40) % 2 * 40, W, 80):
            sub[r:r + 38, cxx:cxx + 78] = C("5a5250") * (0.85 + 0.15 * ((cxx + r) % 3))
    glow(sub, W * 0.5, H * 0.55, 160, "ffc860", 1.0, 1.8)
    sub[int(H * 0.47):int(H * 0.63), int(W * 0.42):int(W * 0.58)] = C("ffe090")
    poly(sub, [(W * 0.35, H * 0.1), (W * 0.62, H * 0.1), (W * 0.6, H * 0.45), (W * 0.4, H * 0.45)], "4a3424")
    sub_s = sub[::int(H / ih) + 1, ::int(W / iw) + 1][:ih, :iw]
    img[iy:iy + sub_s.shape[0], ix:ix + sub_s.shape[1]] = sub_s
    darken_edges(img, 0.4)
    return finish(img, 14)


def shot12():
    """Queen Ysolde on the white walls of Solenne, looking east toward smoke. Title card."""
    img = canvas()
    vgrad(img, [(0, "1a2440"), (0.55, "8a6a7a"), (0.8, "d8a080"), (1, "e8c0a0")], 0, int(H * 0.7))
    # smoke columns on the eastern horizon
    for k, x in enumerate((W * 0.7, W * 0.8, W * 0.92)):
        smoke(img, x, H * 0.63, 190 - k * 25, "4a3c40", seed=k, lean=0.35, width=16 + 5 * k)
        glow(img, x, H * 0.63, 22, "ff8a40", 0.7)
    ridge(img, H * 0.64, 10, 100, "4a4050", 121, top_col="6a5a6a")
    vgrad(img, [(0, "5a5a50"), (1, "3a3a34")], int(H * 0.66), H)
    # the white wall walk she stands on
    poly(img, [(0, H * 0.72), (W * 0.6, H * 0.76), (W * 0.6, H), (0, H)], "d8d0c0")
    for x in range(0, int(W * 0.6), 18):
        y = H * 0.72 + x / (W * 0.6) * H * 0.04
        img[int(y - 12):int(y), x:x + 10] = C("e8e2d4")
        img[int(y - 12), x:x + 10] = C("fffaf0")
    img[int(H * 0.82):, :int(W * 0.6)] *= 0.8
    rgba, _, _, _ = figure("ysolde", Pose(arm_n=(0.5, 0.1, 1.3), arm_f=(0.5, 0.1, 1.3), cape=0.5, head=0.05),
                           height_px=230, yaw=0.6, pitch=0.04, rim=(255, 200, 160), rim_amt=1.5,
                           key=(0.7, 0.4, -0.4), ambient=0.1)
    paste(img, rgba, W * 0.3, H * 1.12)
    # title card
    darken_edges(img, 0.4)
    return finish(img, 16)


SHOTS = [shot01, shot02, shot03, shot04, shot05, shot06, shot07, shot08, shot09, shot10, shot11, shot12]
