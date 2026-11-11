"""Stills for the story's main line: the Regent, the Night of Falling Stars, the Long Night, the Convergence, the
siege of Solenne, the dawn, the assault on Nhal Vorath and the epilogue.

Shot docstrings are the art notes from data/story/cinematics. Backdrops are shared painters; sprites come from the
battle and story sprite sets, pasted at 1x (never scaled).
"""
from __future__ import annotations

import math

import numpy as np

import anim
import creatures
import people
from stills import CINEMATICS, DUSK, FIRELIT, H, NIGHT, RINGC, W, Scene, crown_gap, flame, hx, panel, solenne, tiny_army
from shots_lands import _face_close, attack_pose, death_pose, people_row, walk_pose

GOLD = (255, 214, 120)
GREYEYE = (190, 190, 200)
MONARCHS = ["ignar_king", "aurath_king", "elowen_queen", "thalassa_queen", "orrok_king", "nyxara_queen"]

# two extra story figures for these shots only
people.SPECS["refugee_old"] = dict(name="An old refugee", build="short", top="7a6a5a", body="robe", trim="5a4a3a",
                                   cloak="5a4e44", hair="c8c4bc", headgear="hood", skin="d8b090")
people.SPECS["ysolde_old"] = dict(people.SPECS["ysolde_blind"], name="Queen Ysolde, years later", hair="b8b4b0", cloak=None)
for _k in ("refugee_old", "ysolde_old"):
    creatures.CREATURES[_k] = people._make(_k)


# ---- sprite helpers -----------------------------------------------------------------------------------------------
def arr_of(name, pose=None, flip=False, light=(1, 1, 1)):
    s = creatures.CREATURES[name](pose, 30 if pose else 0)
    im = np.asarray(s.image()).astype(np.float32)
    fx, fy = s.w // 2, s.bh - 4 + s.pad
    if flip:
        im = im[:, ::-1].copy()
        fx = s.w - fx
    im[..., :3] *= np.array(light, np.float32)
    return im, fx, fy


def paste(sc, im, x, feet, fx, fy, alpha=1.0):
    sc._paste(im[..., :3], im[..., 3] / 255 * alpha, int(x - fx), int(feet - fy))


def grey_of(im, k=0.7):
    lum = im[..., :3].mean(-1, keepdims=True)
    im[..., :3] = im[..., :3] * (1 - k) + lum * k
    return im


def lanternguard(sc, x, feet, hollow=False, flip=False, pose=None, light=(1, 1, 1)):
    """A soldier of the Lanternguard: the footman in blue. Hollowed ones go grey with grey eyes."""
    im, fx, fy = arr_of("soldier", pose, flip, light)
    r, g, b = im[..., 0].copy(), im[..., 1].copy(), im[..., 2].copy()
    red = (r > g + 40) & (r > b + 40)
    im[red, 0], im[red, 2] = b[red] * 0.9, r[red] * 0.95
    im[red, 1] = g[red] * 1.1 + 10
    if hollow:
        grey_of(im, 0.75)
        im[..., :3] *= 0.85
    paste(sc, im, x, feet, fx, fy)
    if hollow:
        hxp = x + (-5 if flip else 5)
        sc.c[int(feet - 40), int(hxp) - 1:int(hxp) + 2] = GREYEYE
    return im


def warden(sc, i, x, feet, glow=0.55, flip=False, alpha=1.0):
    """A Warden in the monarch's true shape, burning with its kingdom's colour."""
    c = np.array(RINGC[i], np.float32)
    sc.glow(x, feet - 30, 34, RINGC[i], glow)
    im, fx, fy = arr_of(MONARCHS[i], flip=flip, light=tuple(0.55 + 0.55 * c / 255))
    body = im[..., 3] > 150
    edge = body & ~np.roll(body, 1, 1) | body & ~np.roll(body, 1, 0) | body & ~np.roll(body, -1, 1)
    im[edge, :3] = im[edge, :3] * 0.3 + c * 0.7
    paste(sc, im, x, feet, fx, fy, alpha)


def heartstone(sc, cx, cy, s=1.0, dim=1.0, seventh=False):
    """The Heartstone: a tall crystal whose six faces burn in the six kingdoms' colours."""
    sc.glow(cx, cy, 30 * s, (255, 236, 200), 0.6 * dim)
    top, bot, w = cy - 20 * s, cy + 20 * s, 9 * s
    faces = [[(cx, top), (cx - w, cy - 4 * s), (cx - w * 0.4, cy)], [(cx, top), (cx - w * 0.4, cy), (cx + w * 0.4, cy)],
             [(cx, top), (cx + w * 0.4, cy), (cx + w, cy - 4 * s)], [(cx - w, cy - 4 * s), (cx, bot), (cx - w * 0.4, cy)],
             [(cx - w * 0.4, cy), (cx, bot), (cx + w * 0.4, cy)], [(cx + w * 0.4, cy), (cx, bot), (cx + w, cy - 4 * s)]]
    for k, f in enumerate(faces):
        col = np.array(RINGC[k], np.float32) * (0.45 + 0.55 * dim)
        sc.poly(f, tuple(col))
    sc.line(cx, top, cx, top + 6 * s, (255, 255, 255))
    if seventh:
        m = np.hypot(sc.xs - cx, sc.ys - cy) < 3 * s
        sc.c[m] = (196, 204, 188)                                   # a colour nobody has a name for yet
        sc.c[int(cy), int(cx)] = (250, 252, 246)


def shard_knot(sc, cx, cy, r, col=(250, 200, 110), core=(255, 250, 230), n=22, seed=7):
    """The Sundered Heart seen from afar: a knot of bright shards around a white core."""
    rng = np.random.default_rng(seed)
    sc.glow(cx, cy, r * 1.6, col, 0.6)
    for k in range(n):
        a = rng.uniform(0, math.pi * 2)
        l = r * rng.uniform(0.5, 1.2)
        w = rng.uniform(0.1, 0.22)
        tip = (cx + math.cos(a) * l, cy + math.sin(a) * l)
        sc.poly([(cx + math.cos(a - w) * r * 0.25, cy + math.sin(a - w) * r * 0.25), tip,
                 (cx + math.cos(a + w) * r * 0.25, cy + math.sin(a + w) * r * 0.25)], col if k % 3 else (255, 240, 210))
    sc.disc(cx, cy, r * 0.25, core)


def kneel_pose(name="cassivane"):
    """Down on his knees, head bowed, the sword lowered to the ground."""
    if name in people.SPECS:
        anim.LEGS.setdefault(name, 18)                              # a person's legs are shorter than a boss's
    p = anim.death(5, 8, "titan", name)
    p["_t"] = 5
    p["weapon"], p["hand_w"] = (1.6, 0, 0), (0.6, 0, 0)
    return p


def dust(sc, n, x0, x1, y0, y1, base=(74, 66, 62), seed=0):
    """A cloud of dust as overlapping lumps, each lit from the upper left."""
    rng = np.random.default_rng(seed)
    lumps = sorted(((rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(8, 20)) for _ in range(n)), key=lambda v: -v[1])
    for x, y, r in lumps:
        k = 0.8 + 0.4 * (1 - (y - y0) / max(1, y1 - y0))
        c = np.array(base) * k
        sc.disc(x, y, r, tuple(c * 0.75))
        sc.disc(x - r * 0.18, y - r * 0.18, r * 0.78, tuple(c))
        sc.disc(x - r * 0.4, y - r * 0.4, r * 0.35, tuple(np.minimum(255, c * 1.22)))


def lantern(sc, x, y, s=1, flame=(250, 250, 255), glow=(220, 230, 255)):
    sc.glow(x, y, 14 * s, glow, 0.6)
    sc.rect(x - 3 * s, y - 5 * s, x + 3 * s, y + 4 * s, (60, 50, 40))
    sc.rect(x - 2 * s, y - 4 * s, x + 2 * s, y + 3 * s, flame)
    sc.rect(x - 1 * s, y - 7 * s, x + 1 * s, y - 5 * s, (60, 50, 40))


# ---- backdrops ----------------------------------------------------------------------------------------------------
def sky(sc, kind):
    tops = {"dusk": ("2a2240", "e08a50"), "night": ("0c0c1c", "2a2a44"), "black": ("040406", "141218"),
            "dawn": ("3a5a8a", "f0c080"), "gold": ("4a6aa0", "ffd890"), "grey": ("202024", "3a3a40")}
    a, b = tops[kind]
    sc.bands(a, b, 0, 130, n=7)
    if kind in ("night", "dusk"):
        sc.stars(80 if kind == "night" else 30, 90)


def city_wide(sc, kind="dusk", glow=True, plain="2a2430"):
    sky(sc, kind)
    sc.ridge(126, 4, "3a3040" if kind != "dawn" else "6a5060", 11, freq=0.8)
    sc.ridge(140, 3, plain, 12, freq=1.4)
    solenne(sc, 160, 140, 1.0, glow=glow)
    sc.bands(plain, "100c14", 140, 180, n=5)


def street(sc, kind="day", seed=1):
    """A Solenne street: white houses with slate roofs, a pale square, lanterns."""
    sky(sc, {"day": "gold", "dusk": "dusk", "night": "night", "black": "black"}[kind])
    rng = np.random.default_rng(seed)
    lit = kind in ("day", "dusk")
    wallc = (226, 218, 200) if kind == "day" else (150, 140, 136) if kind == "dusk" else (70, 66, 78)
    shade = tuple(int(c * 0.72) for c in wallc)
    roof = (70, 84, 110) if lit else (34, 36, 52)
    for row, (base, hmin) in enumerate(((112, 26), (132, 22))):
        x = -int(rng.integers(0, 20))
        while x < W:
            w, h = int(rng.integers(22, 36)), int(rng.integers(hmin, hmin + 16))
            sc.rect(x, base - h, x + w, base, wallc if row else shade)
            sc.rect(x + w - 3, base - h, x + w, base, shade)
            sc.poly([(x - 2, base - h), (x + w // 2, base - h - 10), (x + w + 2, base - h)], roof)
            for wx in range(x + 4, x + w - 5, 8):
                for wy in range(base - h + 4, base - 6, 9):
                    win = (255, 200, 110) if (not lit or rng.random() < 0.2) and rng.random() < 0.6 else (60, 60, 76)
                    sc.rect(wx, wy, wx + 3, wy + 4, win)
            x += w + int(rng.integers(0, 6))
    sc.bands("c8bca8" if lit else "3a3640", "8a8070" if lit else "1c1a22", 132, 180, n=5)
    for x in range(0, W, 24):                                       # paving joints
        sc.line(x, 132, x - 30, 180, (150, 140, 124) if lit else (30, 28, 36))


def battlements(sc, feet, col=(150, 144, 136), lit=(210, 204, 190), front=True):
    """Merlons behind the walkway; call wall_face() after the figures."""
    for x in range(-4, W, 18):
        sc.rect(x, feet - 12, x + 11, feet, col)
        sc.rect(x, feet - 12, x + 11, feet - 11, lit)


def wall_face(sc, feet, col=(150, 144, 136), lit=(210, 204, 190)):
    sc.rect(0, feet, W, H, col)
    sc.rect(0, feet, W, feet + 2, lit)
    for k, y in enumerate(range(feet + 8, H, 8)):
        sc.rect(0, y, W, y + 1, tuple(int(c * 0.7) for c in col))
        for x in range((k % 2) * 10, W, 20):
            sc.rect(x, y - 7, x + 1, y, tuple(int(c * 0.7) for c in col))


def plain_beyond(sc, horizon, kind="night", horde=0, cols=None, seed=3):
    sky(sc, kind)
    sc.bands("1a1620", "0c0a10", horizon, H, n=4)
    rng = np.random.default_rng(seed)
    cols = cols or [(150, 150, 160)]
    for _ in range(horde):                                          # the Unbound as points of light
        x, y = int(rng.integers(0, W)), int(rng.integers(horizon + 2, H))
        c = cols[int(rng.integers(len(cols)))]
        sc.c[y, x] = c
        if rng.random() < 0.3:
            sc.c[y - 1, x] = tuple(int(v * 0.6) for v in c)


def spire_top(sc, lens=True, kind="night", broken=False):
    """The top of the Spire of Aurel above the sleeping city, the Sunstone lens in its frame."""
    sky(sc, kind)
    sc.ridge(150, 3, "1a1824", 21, freq=1.2)
    for _ in range(120):                                            # roofs and lights far below
        x, y = int(sc.rng.integers(0, W)), int(sc.rng.integers(150, 168))
        sc.c[y, x] = (255, 200, 110) if sc.rng.random() < 0.3 else (40, 36, 50)
    sc.rect(70, 160, 250, 180, (90, 86, 96))
    sc.rect(70, 160, 250, 162, (170, 164, 170))
    for x in range(70, 250, 12):
        sc.rect(x, 162, x + 1, 180, (60, 56, 66))
    if lens:
        cx, cy = 160, 46
        sc.rect(98, 46, 104, 160, (70, 64, 70))
        sc.rect(216, 46, 222, 160, (70, 64, 70))
        if broken:
            sc.disc(cx, cy, 46, (40, 34, 30), squash=0.5)
            sc.disc(cx, cy, 42, (10, 8, 14), squash=0.5)
        else:
            sc.glow(cx, cy, 80, (255, 220, 140), 0.55)
            sc.disc(cx, cy, 46, (120, 90, 40), squash=0.5)
            sc.disc(cx, cy, 42, (250, 206, 110), squash=0.5)
            sc.disc(cx - 10, cy - 6, 18, (255, 236, 176), squash=0.45)
            sc.disc(cx - 16, cy - 8, 6, (255, 252, 230), squash=0.45)


def hall(sc, dim=1.0, throne=True):
    """The Hall of the Ring: pillars, a dais and banners in the six colours."""
    sc.bands("181620", "2a2632", 0, 140, n=5)
    for x in range(10, W, 52):
        sc.rect(x, 0, x + 14, 150, tuple(int(c * dim) for c in (90, 84, 92)))
        sc.rect(x, 0, x + 3, 150, tuple(int(c * dim) for c in (140, 132, 136)))
        sc.rect(x + 11, 0, x + 14, 150, tuple(int(c * dim) for c in (60, 56, 64)))
    for k, x in enumerate(range(36, W, 52)):
        c = tuple(int(v * 0.45 * dim) for v in RINGC[k % 6])
        sc.poly([(x, 10), (x + 12, 10), (x + 12, 60), (x + 6, 54), (x, 60)], c)
    sc.bands("4a4450", "1a1820", 150, 180, n=4)
    if throne:
        sc.rect(130, 120, 190, 152, (60, 54, 64))
        sc.rect(124, 150, 196, 160, (80, 74, 84))
        sc.rect(140, 90, 180, 150, (40, 36, 46))
        sc.rect(140, 90, 180, 92, tuple(int(v * dim) for v in (200, 160, 80)))


def hollow(sc, sun="black", fortress=True, drain=0.0):
    """The Outer Hollow: a black sky, a black sun with a crown-shaped gap, the Crownless Citadel hanging beneath."""
    sc.bands("060508", "1c1a20", 0, H, n=6)
    sc.stars(40, H, cols=((80, 80, 90), (50, 50, 60)))
    cx, cy = 160, 34
    if sun == "black":
        sc.glow(cx, cy, 44, (150, 150, 170), 0.5)
        sc.disc(cx, cy, 22, (170, 170, 186))
        sc.disc(cx, cy, 20, (6, 6, 8))
        crown_gap(sc, cx, cy + 2, 0.7, edge=(110, 110, 130))
    else:
        sc.glow(cx, cy, 70, (255, 210, 120), 0.8)
        sc.disc(cx, cy, 22, (255, 220, 140))
        sc.disc(cx, cy, 18, (255, 244, 200))
    if fortress:
        col, lit = (34, 30, 40), (70, 64, 80)
        sc.rect(80, 66, 240, 80, col)
        sc.rect(80, 66, 240, 67, lit)
        for k, (x, w, d) in enumerate(((84, 14, 38), (104, 10, 24), (122, 18, 54), (148, 24, 70), (180, 16, 50),
                                       (202, 10, 30), (220, 14, 40))):
            sc.rect(x, 80, x + w, 80 + d, col)
            sc.rect(x, 80, x + 1, 80 + d, lit)
            sc.poly([(x - 1, 80 + d), (x + w // 2, 80 + d + 10), (x + w + 1, 80 + d)], col)
            for wy in range(84, 80 + d - 4, 8):
                sc.rect(x + w // 2 - 1, wy, x + w // 2 + 1, wy + 3, (120, 110, 150))
    sc.bands("141218", "060508", 150, H, n=4)
    if drain:
        lum = sc.c.mean(-1, keepdims=True)
        sc.c[:] = sc.c * (1 - drain) + lum * drain


def glass_plain(sc, horizon=110):
    sky(sc, "black")
    sc.bands("1a1820", "0a080c", horizon, H, n=4)
    rng = np.random.default_rng(41)
    for _ in range(70):                                             # shattered glass in six colours
        x, y = int(rng.integers(0, W)), int(rng.integers(horizon + 4, H))
        c = tuple(int(v * rng.uniform(0.3, 0.7)) for v in RINGC[int(rng.integers(6))])
        s = 2 + (y - horizon) // 14
        sc.poly([(x, y), (x + s, y - s // 2), (x + s * 2, y + 1), (x + s // 2, y + s // 2)], c)
        sc.c[min(H - 1, y), x] = tuple(min(255, v * 2) for v in c)


# ---- Regent's counsel ---------------------------------------------------------------------------------------------
def regents_counsel_01():
    """Solenne's streets packed with refugees from different lands, tents in the white squares, the Sunstone gold above."""
    sc = Scene(201)
    street(sc, "day")
    sc.glow(250, 20, 40, (255, 220, 140), 0.8)
    sc.disc(250, 20, 10, (255, 230, 150), squash=0.45)
    for k, x in enumerate(range(20, 300, 38)):                      # tents in every land's colour
        c = tuple(int(v * 0.7) for v in RINGC[k % 6])
        sc.poly([(x, 150), (x + 14, 134), (x + 28, 150)], c)
        sc.poly([(x + 12, 150), (x + 14, 138), (x + 16, 150)], (30, 24, 24))
    for row, y in enumerate((158, 166, 174)):
        people_row(sc, 6 + row * 3, y, 50, step=6, cols=[tuple(int(v * 0.6) for v in c) for c in RINGC], carry=(120, 90, 60) if row == 1 else None)
    sc.vignette(0.3)
    return sc


def regents_counsel_02():
    """Cassivane Dral at the gate, red cloak, helping an old woman off a cart, smiling. Fennick grumbling over a plan."""
    sc = Scene(202)
    street(sc, "day", seed=4)
    stone, lit, dark = (204, 196, 180), (236, 230, 214), (150, 142, 128)
    sc.rect(186, 30, 320, 150, stone)                                # the gatehouse
    for k, y in enumerate(range(38, 150, 8)):
        sc.rect(186, y, 320, y + 1, dark)
        for x in range(186 + (k % 2) * 8, 320, 16):
            sc.rect(x, y - 7, x + 1, y, dark)
    for x in range(186, 320, 12):
        sc.rect(x, 22, x + 7, 30, stone)
        sc.rect(x, 22, x + 7, 23, lit)
    arch = (sc.xs >= 214) & (sc.xs < 292) & (sc.ys < 150) & ((sc.ys >= 76) | (np.hypot(sc.xs - 253, sc.ys - 76) < 39))
    sc.c[arch] = (54, 48, 46)
    ring = (np.hypot(sc.xs - 253, sc.ys - 76) < 43) & ~arch & (sc.ys < 78)
    sc.c[ring] = lit
    sc.rect(186, 30, 189, 150, lit)
    for x in (196, 300):                                              # Lanternguard banners
        sc.rect(x, 40, x + 12, 70, (52, 80, 138))
        sc.poly([(x, 70), (x + 6, 64), (x + 12, 70), (x + 12, 74), (x, 74)], (52, 80, 138))
        sc.disc(x + 6, 52, 3, (240, 200, 90))
    # the cart
    sc.rect(28, 136, 96, 148, (110, 76, 46))
    sc.rect(28, 136, 96, 138, (150, 110, 70))
    for wx in (40, 84):
        sc.disc(wx, 152, 8, (70, 50, 34))
        sc.disc(wx, 152, 5, (120, 90, 56))
        sc.disc(wx, 152, 1, (40, 30, 20))
    sc.rect(30, 124, 50, 136, (140, 120, 90))
    sc.put("refugee_old", 108, 166, flip=True)
    sc.put("cassivane_marshal", 140, 168, flip=True)
    sc.put("fennick", 222, 168, flip=True)
    sc.rect(196, 132, 214, 142, (230, 222, 196))                    # the tower plan in his hands
    sc.line(198, 134, 212, 140, (60, 80, 140))
    sc.line(198, 140, 206, 134, (60, 80, 140))
    sc.vignette(0.3)
    return sc


def regents_counsel_03():
    """Cassivane looking straight at the player, warm, fatherly. As he turns away, his thumb runs over the gold locket."""
    sc = Scene(203)
    street(sc, "day", seed=6)
    sc.blend(np.ones((H, W), bool), (40, 30, 30), 0.5)
    _face_close(sc, "cassivane", 112, 40)
    sc.glow(178, 128, 10, GOLD, 0.7)
    sc.disc(178, 128, 4, (220, 170, 60))
    sc.disc(177, 127, 2, (255, 230, 150))
    sc.vignette(0.5)
    return sc


def regents_counsel_04():
    """Night: Cassivane alone on the Spire of Aurel, looking east toward the Rift. The locket open: a girl's portrait."""
    sc = Scene(204)
    spire_top(sc)
    sc.line(300, 140, 318, 138, (160, 120, 230))                     # the Crack, far in the east
    sc.glow(310, 139, 10, (150, 110, 230), 0.4)
    sc.put("cassivane_marshal", 140, 162, light=NIGHT, rim=(255, 220, 150))
    # inset: the open locket
    import portraits
    face = np.asarray(portraits.portrait("ilyra")).astype(np.float32)[18:74, 22:74]
    oval = np.hypot((np.arange(52)[None, :] - 26) / 22, (np.arange(56)[:, None] - 28) / 26) <= 1
    sc.disc(262, 66, 32, (170, 120, 40), squash=1.15)
    sc.disc(262, 66, 29, (240, 190, 80), squash=1.15)
    sc._paste(face[..., :3], oval.astype(np.float32), 236, 38)
    panel(sc, 226, 28, 298, 106, (240, 200, 110))
    sc.vignette(0.5)
    return sc


# ---- the Night of Falling Stars -----------------------------------------------------------------------------------
def nofs_01():
    """Solenne at dusk, the Sunstone glowing over a city packed with refugees. Lanterns everywhere. Quiet."""
    sc = Scene(211)
    city_wide(sc, "dusk")
    for _ in range(140):
        x, y = int(sc.rng.integers(70, 250)), int(sc.rng.integers(100, 142))
        if sc.c[y, x].sum() > 300:
            sc.c[y, x] = (255, 200, 110)
    for _ in range(60):
        x, y = int(sc.rng.integers(20, 300)), int(sc.rng.integers(146, 176))
        sc.c[y, x] = (255, 190, 100)
    sc.vignette(0.4)
    return sc


def _gate(sc, open_=0.0, col=(170, 164, 154), lit=(220, 214, 200)):
    sc.rect(0, 20, W, 160, col)
    sc.rect(0, 20, W, 24, lit)
    for y in range(30, 160, 10):
        sc.rect(0, y, W, y + 1, tuple(int(c * 0.75) for c in col))
    sc.rect(110, 50, 210, 160, (10, 8, 12))
    sc.poly([(110, 50), (160, 30), (210, 50)], (10, 8, 12))
    d = int(50 * open_)
    sc.rect(110, 50, 160 - d, 160, (90, 60, 40))
    sc.rect(160 + d, 50, 210, 160, (90, 60, 40))
    for x in (130 - d // 2, 186 + d // 2):
        sc.rect(x, 56, x + 2, 156, (60, 40, 26))
    sc.bands("4a4440", "1a1618", 160, H, n=4)


def nofs_02():
    """The great east gate swinging open. Lanternguard stand aside, eyes empty and grey. Behind the gate, the Unbound pour in."""
    sc = Scene(212)
    sky(sc, "dusk")
    _gate(sc, open_=0.8)
    for k in range(10):                                             # the Unbound beyond the open gate
        sc.put(["ghost", "orb_fire", "skeleton", "orb_storm", "orb_void"][k % 5], 126 + (k % 4) * 18, 150 + (k // 4) * 6,
               light=(0.6, 0.6, 0.65))
    sc.glow(160, 110, 40, (150, 150, 170), 0.4)
    lanternguard(sc, 70, 172, hollow=True)
    lanternguard(sc, 250, 172, hollow=True, flip=True)
    sc.vignette(0.5)
    return sc


def nofs_03():
    """Hollowed soldiers fighting in the streets; refugees running; Lanternguard fighting their own."""
    sc = Scene(213)
    street(sc, "night", seed=9)
    for k in range(5):
        flame(sc, 30 + k * 66, 132, 14)
        sc.glow(30 + k * 66, 124, 18, (255, 140, 50), 0.5)
    people_row(sc, 10, 150, 30, step=10, cols=[(90, 70, 60), (60, 60, 90)])
    lanternguard(sc, 120, 172, hollow=False, pose=attack_pose("soldier", 3), light=FIRELIT)
    lanternguard(sc, 180, 172, hollow=True, flip=True, pose=attack_pose("soldier", 5), light=FIRELIT)
    lanternguard(sc, 260, 176, hollow=True, flip=True, light=FIRELIT)
    sc.put("ghost", 60, 168, light=(0.7, 0.7, 0.75))
    sc.vignette(0.5)
    return sc


def _gatehouse(sc):
    sc.bands("2a2228", "141016", 0, 150, n=4)
    for x in range(0, W, 40):
        sc.rect(x, 0, x + 1, 150, (60, 50, 56))
    sc.rect(0, 150, W, H, (60, 50, 46))
    sc.rect(0, 150, W, 152, (110, 96, 86))
    sc.rect(236, 30, 320, 150, (14, 10, 14))                         # the gate's mouth with bars
    for x in range(240, 320, 10):
        sc.rect(x, 30, x + 3, 150, (90, 84, 90))


def nofs_04():
    """Old Fennick in the gatehouse, spectacles on, firing half-built towers that crackle with unstable elements.
    Brannoc forging the outer bars shut with his hammer."""
    sc = Scene(214)
    _gatehouse(sc)
    for k, x in enumerate((60, 120)):
        sc.tower(x, 150, 14, 34, (90, 80, 76), (150, 136, 120), crenel=False)
        c = RINGC[(k * 3 + 1) % 6]
        sc.glow(x + 7, 112, 14, c, 0.8)
        for j in range(4):
            a = j * 1.7 + k
            sc.line(x + 7, 112, x + 7 + math.cos(a) * 10, 112 + math.sin(a) * 8, c)
    sc.put("fennick", 96, 170, light=FIRELIT, rim=(255, 200, 120))
    sc.glow(256, 100, 20, (255, 150, 50), 0.7)
    sc.put("brannoc", 226, 172, pose=attack_pose("brannoc", 4), light=FIRELIT, rim=(255, 160, 70))
    sc.particles(30, [(255, 200, 80), (255, 140, 40)], 80, 120, 236, 280)
    sc.vignette(0.5)
    return sc


def nofs_05():
    """Fennick shouting over his shoulder, then turning back to the gate as it starts to fall."""
    sc = Scene(215)
    _gatehouse(sc)
    for (x0, y0, x1, y1) in ((250, 30, 270, 70), (270, 70, 262, 110), (290, 40, 300, 90)):   # cracks in the stone
        sc.line(x0, y0, x1, y1, (240, 220, 200))
    sc.particles(80, [(140, 120, 100), (100, 86, 74)], 20, 150, 200, 320)
    sc.put("fennick", 150, 170, flip=True, light=FIRELIT, rim=(255, 200, 120))
    for k in range(3):                                              # the shout
        sc.line(126 - k * 5, 124 - k * 4, 120 - k * 5, 122 - k * 4, (230, 220, 200))
    sc.vignette(0.5)
    return sc


def nofs_06():
    """The gatehouse collapsing in a cloud of dust and coloured sparks. Silence."""
    sc = Scene(216)
    sky(sc, "night")
    sc.ridge(150, 10, "3a3436", 61, jag=6)
    dust(sc, 70, 50, 270, 70, 162, seed=6)
    for k in range(40):
        x, y = int(sc.rng.uniform(40, 280)), int(sc.rng.uniform(40, 150))
        sc.c[y, x] = RINGC[k % 6]
        sc.glow(x, y, 3, RINGC[k % 6], 0.5)
    sc.bands("2a2426", "100c0e", 160, H, n=3)
    sc.vignette(0.6)
    return sc


def nofs_07():
    """Cassivane at the top of the Spire, red armour starting to blacken, holding a crystal blade glowing six colours.
    The Sunstone lens huge above him."""
    sc = Scene(217)
    spire_top(sc)
    im, fx, fy = arr_of("cassivane_marshal", light=(0.85, 0.8, 0.8))
    low = np.arange(im.shape[0])[:, None] > fy - 34                  # blackening from the feet up
    im[..., :3][np.broadcast_to(low, im.shape[:2])] *= 0.45
    paste(sc, im, 160, 162, fx, fy)
    for k in range(6):                                              # the crystal blade
        sc.line(176 + k, 132 - k * 7, 177 + k, 126 - k * 7, RINGC[k])
    sc.glow(180, 116, 14, (255, 255, 255), 0.6)
    sc.vignette(0.5)
    return sc


def nofs_08():
    """The Sunstone shattering. Its pieces fall across the city like burning stars."""
    sc = Scene(218)
    city_wide(sc, "night", glow=False)
    sc.glow(160, 40, 50, (255, 220, 140), 0.7)
    rng = np.random.default_rng(8)
    for k in range(26):
        a = rng.uniform(0.3, math.pi - 0.3)
        d = rng.uniform(20, 140)
        x, y = 160 + math.cos(a) * d * 1.4, 40 + math.sin(a) * d * 0.7
        tx, ty = x - math.cos(a) * 14, y - math.sin(a) * 8 - 6
        sc.line(tx, ty, x, y, (255, 160, 60))
        sc.poly([(x - 2, y), (x, y - 3), (x + 2, y), (x, y + 2)], (255, 236, 170))
    sc.vignette(0.4)
    return sc


def nofs_09():
    """Ysolde in the palace courtyard, looking up as the light falls on her face; white-out. Tamsin dragging her into cover."""
    sc = Scene(219)
    street(sc, "night", seed=12)
    sc.put("ysolde", 170, 170, light=(1.2, 1.15, 1.05), rim=(255, 255, 255))
    sc.put("tamsin", 120, 172, pose=walk_pose("tamsin", 3), light=(1.1, 1.05, 1.0))
    a = np.clip(1 - (sc.ys / 140.0), 0, 1) * 1.1 + np.clip(1 - np.hypot(sc.xs - 172, sc.ys - 110) / 90, 0, 1) * 0.6
    sc.blend(np.ones((H, W), bool), (255, 252, 240), np.clip(a, 0, 1), steps=5)
    return sc


def nofs_10():
    """Cassivane, ash drifting from his armour, stepping through a rip of darkness at the top of the Spire, carrying the
    Sunstone's shards in a net of grey light."""
    sc = Scene(220)
    spire_top(sc, broken=True)
    rip = sc.poly([(186, 60), (204, 80), (210, 120), (200, 160), (190, 162), (182, 120), (178, 82)], (2, 0, 4))
    e = rip & ~(np.roll(rip, 1, 1) & np.roll(rip, -1, 1))
    sc.c[e] = (150, 110, 220)
    sc.put("cassivane", 170, 162, light=(0.8, 0.78, 0.8))
    sc.glow(132, 120, 18, (200, 200, 210), 0.6)
    for k in range(7):                                              # the net of shards
        x, y = 124 + (k % 3) * 8, 110 + (k // 3) * 8
        sc.poly([(x, y), (x + 3, y - 4), (x + 5, y)], (255, 220, 140))
    for y in range(106, 132, 4):
        sc.line(118, y, 146, y + 2, (170, 170, 180))
    sc.particles(60, [(120, 116, 116), (80, 76, 76)], 80, 160, 120, 230)
    sc.vignette(0.5)
    return sc


def nofs_11():
    """Over the dark city, one falling shard of white light drifts sideways, east, toward the distant Rift, and keeps going."""
    sc = Scene(221)
    city_wide(sc, "black", glow=False)
    sc.line(300, 124, 318, 122, (130, 100, 200))
    for k in range(40):                                             # its trail
        x = 150 + k * 3.5
        y = 50 + k * 0.9 + math.sin(k * 0.4) * 3
        sc.c[int(y), int(x)] = (200, 210, 255) if k % 2 else (120, 130, 170)
    sc.glow(290, 86, 10, (230, 236, 255), 0.8)
    sc.disc(290, 86, 2, (255, 255, 255))
    sc.vignette(0.5)
    return sc


def nofs_12():
    """Dawn hour. A black sky over Solenne. Only torches. Refugees looking up."""
    sc = Scene(222)
    street(sc, "black", seed=14)
    for k in range(4):
        x = 40 + k * 80
        sc.rect(x, 140, x + 2, 160, (60, 40, 30))
        flame(sc, x + 1, 140, 10)
        sc.glow(x + 1, 134, 20, (255, 140, 50), 0.5)
    for row, y in enumerate((164, 172)):
        people_row(sc, 10 + row * 4, y, 42, step=7, cols=[(70, 56, 50), (50, 50, 70), (80, 70, 50)])
    sc.vignette(0.6)
    return sc


# ---- the Long Night -----------------------------------------------------------------------------------------------
def long_night_01():
    """Solenne under a black sky, lit by torches and the Heartstone's faint six-coloured pulse."""
    sc = Scene(231)
    city_wide(sc, "black", glow=False)
    for k, c in enumerate(RINGC):
        sc.glow(160 + (k - 2.5) * 3, 92, 16, c, 0.25)
    sc.disc(160, 92, 2, (230, 220, 210))
    for _ in range(50):
        x, y = int(sc.rng.integers(80, 240)), int(sc.rng.integers(104, 142))
        if sc.c[y, x].sum() > 200:
            sc.c[y, x] = (255, 150, 60)
    sc.vignette(0.5)
    return sc


def long_night_02():
    """Ysolde on her throne, blindfold of black and gold, Fennick's brass measuring rod across her knees. Heroes in the dim hall."""
    sc = Scene(232)
    hall(sc, dim=0.6)
    sc.put("ysolde_blind", 160, 150, light=(0.85, 0.8, 0.85))
    for x, name in ((50, "brannoc"), (86, "sylvaine"), (234, "kaela"), (272, "gorrim")):
        sc.put(name, x, 172, flip=x > 160, light=(0.45, 0.45, 0.6))
    for x in (110, 210):
        flame(sc, x, 120, 8)
        sc.glow(x, 114, 16, (255, 150, 60), 0.5)
    sc.vignette(0.55)
    return sc


def long_night_03():
    """Tamsin at a war table under a lantern, reading from Fennick's battered notebook with his spectacles in her hand."""
    sc = Scene(233)
    sc.bands("1a1418", "0a080a", 0, H, n=4)
    lantern(sc, 160, 30, 2, flame=(255, 210, 120), glow=(255, 190, 100))
    sc.line(160, 0, 160, 20, (50, 40, 34))
    sc.glow(160, 130, 90, (255, 180, 90), 0.35)
    sc.put("tamsin", 120, 166, light=FIRELIT)
    sc.rect(130, 132, 290, 140, (100, 70, 44))                        # table with the map of the Ring
    sc.rect(140, 140, 146, 180, (70, 48, 30))
    sc.rect(276, 140, 282, 180, (70, 48, 30))
    sc.poly([(170, 132), (250, 132), (244, 128), (176, 128)], (200, 180, 140))
    for k in range(6):
        sc.c[130, 190 + k * 8] = RINGC[k]
    sc.rect(150, 124, 162, 130, (120, 80, 50))                         # the notebook
    sc.rect(152, 125, 160, 129, (220, 210, 180))
    sc.vignette(0.55)
    return sc


def long_night_04():
    """A night road lit by a line of lanterns: refugees, carts, Lanternguard, towers glowing in six colours along the way."""
    sc = Scene(234)
    sky(sc, "black")
    sc.bands("141218", "0a080c", 100, H, n=4)
    sc.poly([(150, 100), (170, 100), (300, 180), (40, 180)], (40, 36, 40))
    for k in range(12):
        t = k / 11
        y = 102 + t * 76
        for side in (-1, 1):
            x = 160 + side * (8 + t * 120)
            sc.glow(x, y - 4 - t * 6, 3 + t * 10, (255, 200, 110), 0.7)
            sc.c[int(y - 4 - t * 6), int(x)] = (255, 240, 180)
        if k % 2 and k > 2:
            x = 160 + (-1 if k % 4 == 1 else 1) * (20 + t * 140)
            sc.tower(int(x), int(y), int(3 + t * 8), int(8 + t * 26), (60, 56, 64), (100, 96, 104), win=RINGC[k % 6])
    people_row(sc, 100, 178, 18, step=7, carry=(120, 90, 60))
    people_row(sc, 140, 150, 10, step=5)
    sc.vignette(0.55)
    return sc


# ---- the Convergence ----------------------------------------------------------------------------------------------
def convergence_intro_01():
    """A map of the Ring: six lands dark, grey tides converging from every side on the centre."""
    sc = Scene(241)
    sc.c[:] = (8, 6, 8)
    sc.bands("b8a080", "8a7454", 14, 166, n=5, mask=(sc.xs > 40) & (sc.xs < 280) & (sc.ys > 14) & (sc.ys < 166))
    cx, cy = 160, 90
    for i in range(6):
        a0 = -math.pi / 2 + i * math.pi / 3 - math.pi / 6
        pts = [(cx + math.cos(a0 + k * math.pi / 18) * 34, cy + math.sin(a0 + k * math.pi / 18) * 21) for k in range(7)]
        pts += [(cx + math.cos(a0 + k * math.pi / 18) * 96, cy + math.sin(a0 + k * math.pi / 18) * 60) for k in range(6, -1, -1)]
        m = sc.poly(pts, None)
        sc.blend(m, tuple(int(v * 0.3) for v in RINGC[i]), 0.75)
        am = a0 + math.pi / 6                                       # a grey tide pushing inward
        for j in range(5):
            r0 = 90 - j * 11
            x, y = cx + math.cos(am) * r0, cy + math.sin(am) * r0 * 0.62
            sc.disc(x, y, 5 - j * 0.6, (120, 120, 126), squash=0.7)
    sc.disc(cx, cy, 14, (200, 180, 140), squash=0.62)
    sc.disc(cx, cy, 3, (255, 220, 140))
    sc.vignette(1.0)
    return sc


def convergence_intro_02():
    """Six vast figures walking across the plains toward the city, each glowing its own colour. Refugees stop to watch."""
    sc = Scene(242)
    sky(sc, "dusk")
    sc.ridge(118, 4, "3a2e40", 31, freq=0.8)
    solenne(sc, 290, 118, 0.35, glow=True)
    sc.bands("3a3040", "16121a", 118, H, n=5)
    for i in range(6):
        warden(sc, i, 30 + i * 46, 150 - (i % 2) * 8, glow=0.4)
    for row, y in enumerate((170, 176)):
        people_row(sc, 20 + row * 6, y, 34, step=8)
    sc.vignette(0.45)
    return sc


def _convergence_intro_03_v1():
    """(Superseded) The six Wardens standing in a ring around the outer walls of Solenne, the Heartstone pulsing."""
    sc = Scene(243)
    sky(sc, "night")
    sc.ridge(130, 3, "2a2434", 32)
    sc.bands("2a2434", "100c14", 130, H, n=4)
    order = [(5, 60, 112), (0, 108, 104), (1, 212, 104), (2, 260, 112)]
    for i, x, f in order:
        warden(sc, i, x, f, glow=0.35, flip=x > 160)
    solenne(sc, 160, 140, 0.8, glow=False)
    heartstone(sc, 160, 92, 0.5)
    for i, x in ((4, 40), (3, 280)):
        warden(sc, i, x, 172, glow=0.5, flip=x > 160)
    sc.vignette(0.45)
    return sc


def convergence_intro_04_crossmere():
    """Crossmere, a crossroads town at night, ringed by a grey war camp. Cassivane's standard: a red field, burned black."""
    sc = Scene(244)
    sky(sc, "night")
    sc.bands("1e1c24", "0c0a10", 110, H, n=4)
    sc.line(0, 150, 320, 120, (40, 36, 40))
    sc.line(0, 120, 320, 160, (40, 36, 40))
    for k, x in enumerate(range(110, 220, 16)):                     # the town
        h = 12 + (k * 7) % 10
        sc.rect(x, 136 - h, x + 12, 136, (60, 56, 64))
        sc.poly([(x - 1, 136 - h), (x + 6, 130 - h), (x + 13, 136 - h)], (40, 36, 44))
        sc.rect(x + 4, 130 - h // 2, x + 6, 133 - h // 2, (255, 190, 100))
    for k in range(26):                                             # the grey camp around it
        a = k / 26 * math.pi * 2
        x, y = 164 + math.cos(a) * 130, 134 + math.sin(a) * 28
        if 0 < y < H:
            sc.poly([(x - 6, y), (x, y - 8), (x + 6, y)], (110, 110, 116))
            if k % 4 == 0:
                sc.glow(x, y - 2, 6, (170, 170, 180), 0.6)
    sc.rect(250, 70, 252, 128, (60, 50, 40))                          # the standard
    sc.poly([(252, 72), (286, 76), (282, 98), (252, 96)], (60, 14, 14))
    sc.poly([(266, 74), (286, 76), (282, 98), (262, 97), (270, 86)], (20, 14, 14))
    sc.vignette(0.5)
    return sc


# ---- the crossroads -----------------------------------------------------------------------------------------------
def _fold(sc, x):
    m = sc.poly([(x, 20), (x + 30, 60), (x + 26, 120), (x + 40, 176), (x - 10, 176), (x - 4, 110), (x - 14, 60)], (2, 0, 4))
    e = m & ~(np.roll(m, 1, 1) & np.roll(m, -1, 1))
    sc.c[e] = (110, 80, 170)
    return m


def crossroads_01():
    """Cassivane, armour burned like paper, Heartstone shards growing from his shoulders, wounded, walking into a fold of darkness."""
    sc = Scene(251)
    sky(sc, "night")
    sc.bands("1e1a22", "0c0a10", 120, H, n=4)
    _fold(sc, 240)
    sc.put("cassivane", 190, 172, pose=walk_pose("cassivane", 2), light=(0.75, 0.72, 0.75))
    sc.particles(40, [(90, 86, 86), (60, 56, 56)], 100, 170, 130, 220)
    sc.vignette(0.5)
    return sc


def crossroads_02():
    """Cassivane looking back once, grey eyes, locket in hand."""
    sc = Scene(252)
    sky(sc, "night")
    _fold(sc, 250)
    sc.blend(np.ones((H, W), bool), (10, 8, 14), 0.4)
    _face_close(sc, "cassivane_ashen", 112, 40, light=(0.85, 0.85, 0.9))
    sc.glow(184, 132, 9, GOLD, 0.7)
    sc.disc(184, 132, 3, (220, 170, 60))
    sc.vignette(0.5)
    return sc


def _cage(sc, x0, x1, top, feet, broken=False):
    for k, x in enumerate(range(x0, x1 + 1, 8)):
        if broken and k in (3, 4):
            sc.line(x, feet, x + 8, top + 40, (70, 66, 74))
            continue
        sc.rect(x, top, x + 2, feet, (70, 66, 74))
        sc.rect(x, top, x + 1, feet, (120, 116, 126))
    sc.rect(x0 - 2, top - 4, x1 + 4, top, (60, 56, 64))
    sc.rect(x0 - 2, feet - 2, x1 + 4, feet + 2, (60, 56, 64))


def crossroads_03():
    """Corvin cutting open the cage. Inside, thin and wide-eyed, Ilyra, black veins on her arms, a broken astrolabe on a chain."""
    sc = Scene(253)
    sky(sc, "night")
    sc.bands("1e1a22", "0c0a10", 120, H, n=4)
    sc.put("ilyra", 200, 168, light=(0.75, 0.75, 0.85))
    _cage(sc, 168, 232, 92, 170, broken=True)
    sc.put("corvin", 132, 172, pose=attack_pose("corvin", 4), rim=(200, 180, 255))
    sc.line(160, 112, 176, 136, (230, 220, 255))
    sc.glow(170, 124, 10, (200, 180, 255), 0.6)
    sc.vignette(0.5)
    return sc


def crossroads_04():
    """Ilyra standing, lightning flickering along the black veins. Joins as a hero."""
    sc = Scene(254)
    sky(sc, "night")
    sc.bands("1e1a22", "0c0a10", 120, H, n=4)
    sc.glow(160, 130, 40, (150, 140, 255), 0.5)
    sc.put("ilyra", 160, 170, rim=(200, 200, 255))
    for side in (-1, 1):
        x, y = 160 + side * 8, 122
        for j in range(6):                                         # a crackle running down each arm and off the hand
            nx, ny = x + side * (2 + (j % 2) * 3), y + 4 + (j % 3)
            sc.line(x, y, nx, ny, (230, 230, 255))
            x, y = nx, ny
        sc.glow(x, y, 6, (180, 180, 255), 0.7)
    sc.vignette(0.5)
    return sc


# ---- the Lumen Gate -----------------------------------------------------------------------------------------------
def lumen_gate_01():
    """Glass plains under a black sky, shattered into six colours. The army of the Concord falling back toward the walls."""
    sc = Scene(261)
    glass_plain(sc)
    sc.wall(0, 70, 110, 30, (130, 124, 118), (190, 184, 176), step=6)
    sc.tower(56, 110, 10, 44, (130, 124, 118), (190, 184, 176), win=(255, 200, 110))
    tiny_army(sc, 80, 230, 150, 26, (90, 100, 140))
    for k in range(8):
        sc.put(["ghost", "orb_void", "skeleton", "orb_fire"][k % 4], 250 + (k % 3) * 22, 150 + (k // 3) * 10, light=(0.6, 0.6, 0.65))
    sc.vignette(0.5)
    return sc


def lumen_gate_02():
    """The outermost wall collapsing. Through the dust: Seraphel, tall, in white-gold plate with six dimming colours,
    drawing a greatsword of Sunstone glass that glows like dawn."""
    sc = Scene(262)
    sky(sc, "black")
    dust(sc, 60, -10, 330, 60, 168, base=(70, 64, 62), seed=62)
    sc.bands("4a4440", "1a1618", 160, H, n=3)
    for (x, y) in ((40, 150), (70, 162), (250, 156), (290, 166)):
        sc.rect(x, y, x + 20, y + 12, (130, 124, 118))
        sc.rect(x, y, x + 20, y + 2, (190, 184, 176))
    sc.glow(170, 110, 60, (255, 220, 150), 0.6)
    sc.put("seraphel", 160, 172, pose=attack_pose("seraphel", 2), rim=(255, 230, 160))
    sc.vignette(0.5)
    return sc


def lumen_gate_03():
    """Seraphel on the second wall beside the Queen, sword planted. Joins as a hero."""
    sc = Scene(263)
    plain_beyond(sc, 120, "black", horde=160, cols=[tuple(int(v * 0.6) for v in c) for c in RINGC])
    battlements(sc, 150)
    sc.put("ysolde_blind", 130, 150)
    sc.glow(190, 110, 30, (255, 220, 150), 0.5)
    sc.put("seraphel", 190, 150, rim=(255, 230, 160))
    wall_face(sc, 150)
    sc.vignette(0.45)
    return sc


# ---- the capital ----------------------------------------------------------------------------------------------------
def capital_prelude_01():
    """Wide shot of Solenne crammed with every people of the Ring, each lighting a small light in its own colour.
    The city glows like a lantern in the black."""
    sc = Scene(271)
    city_wide(sc, "black", glow=False)
    heartstone(sc, 160, 90, 0.4, dim=0.6)
    rng = np.random.default_rng(5)
    for _ in range(420):
        x, y = int(rng.integers(76, 244)), int(rng.integers(96, 142))
        if sc.c[y, x].sum() > 150:
            sc.c[y, x] = RINGC[int(rng.integers(6))]
    sc.glow(160, 120, 100, (255, 220, 160), 0.25)
    sc.vignette(0.5)
    return sc


def capital_prelude_02():
    """Ysolde climbing the inner wall, Tamsin at her arm, the heroes along the battlements."""
    sc = Scene(272)
    sky(sc, "black")
    sc.rect(0, 92, W, H, (130, 124, 118))
    for y in range(100, H, 8):
        sc.rect(0, y, W, y + 1, (100, 94, 90))
    for k in range(8):                                              # the stair up the wall
        sc.rect(60 + k * 14, 172 - k * 10, 90 + k * 14, 176 - k * 10, (170, 164, 156))
    battlements(sc, 92)
    for x, name in ((200, "kaela"), (236, "brannoc"), (272, "sylvaine"), (304, "corvin")):
        sc.put(name, x, 92, flip=True, light=(0.6, 0.6, 0.72))
    sc.put("ysolde_blind", 116, 138, light=(0.8, 0.78, 0.82))
    sc.put("tamsin", 98, 148, light=(0.8, 0.78, 0.82))
    sc.vignette(0.5)
    return sc


def capital_prelude_03():
    """Ysolde on the wall, blindfolded, facing out over the dark plain where the Unbound gather in every colour.
    In the centre of the horde, a vast floating knot of shattered light: the Sundered Heart."""
    sc = Scene(273)
    plain_beyond(sc, 110, "black", horde=500, cols=[tuple(int(v * 0.7) for v in c) for c in RINGC])
    shard_knot(sc, 220, 70, 30)
    battlements(sc, 156)
    sc.put("ysolde_blind", 90, 156, rim=(255, 220, 160))
    wall_face(sc, 156)
    sc.vignette(0.5)
    return sc


def capital_prelude_04():
    """Ysolde turning her blind face east. Tamsin looks: nothing but darkness."""
    sc = Scene(274)
    plain_beyond(sc, 110, "black", horde=60)
    sc.blend(sc.ys < 110, (0, 0, 2), np.clip((sc.xs - 180) / 140, 0, 1) * 0.8)
    battlements(sc, 156)
    sc.put("ysolde_blind", 150, 156)
    sc.put("tamsin", 112, 156)
    wall_face(sc, 156)
    sc.vignette(0.55)
    return sc


def solenne_falls_01():
    """The inner wall cracking, the Heartstone's light flickering; then the image freezes and runs backward,
    as if Ysolde is refusing the memory."""
    sc = Scene(281)
    sky(sc, "black")
    sc.rect(0, 80, W, H, (120, 114, 110))
    for y in range(86, H, 8):
        sc.rect(0, y, W, y + 1, (90, 86, 84))
    battlements(sc, 80)
    for (x0, y0, x1, y1) in ((150, 80, 140, 110), (140, 110, 156, 140), (156, 140, 146, 180), (140, 110, 120, 124),
                             (156, 140, 180, 152)):
        sc.line(x0, y0, x1, y1, (20, 16, 18))
        sc.line(x0 + 1, y0, x1 + 1, y1, (200, 190, 180))
    heartstone(sc, 160, 40, 0.6, dim=0.35)
    # the memory refusing: rows slip sideways and the colour splits
    rng = np.random.default_rng(4)
    for _ in range(9):
        y0 = int(rng.integers(0, H - 8))
        h = int(rng.integers(2, 8))
        sc.c[y0:y0 + h] = np.roll(sc.c[y0:y0 + h], int(rng.integers(-14, 14)), 1)
    r = np.roll(sc.c[..., 0], 2, 1)
    sc.c[..., 0] = r
    sc.blend(np.ones((H, W), bool), (40, 30, 50), 0.25)
    for x, y in ((14, 14), (20, 14)):                                # a rewind mark
        sc.poly([(x + 6, y), (x, y + 4), (x + 6, y + 8)], (230, 230, 240))
    sc.vignette(0.6)
    return sc


# ---- the dawn -----------------------------------------------------------------------------------------------------
def dawn_01():
    """Battle at the inner wall. The eastern horizon tears with a line of white light."""
    sc = Scene(291)
    plain_beyond(sc, 110, "black", horde=400, cols=[tuple(int(v * 0.6) for v in c) for c in RINGC])
    sc.rect(200, 108, W, 110, (255, 255, 250))
    sc.glow(280, 109, 60, (240, 240, 255), 0.6, squash=0.15)
    battlements(sc, 156)
    for x, name in ((50, "tamsin"), (100, "brannoc"), (150, "sylvaine")):
        sc.put(name, x, 156, pose=attack_pose(name, 4), light=(0.7, 0.7, 0.8))
    wall_face(sc, 156)
    sc.vignette(0.45)
    return sc


def dawn_02():
    """A tall figure in glowing white robes walking up the east road through the horde; grey-eyed spirits freeze and fade
    as he passes. Nyxara turns toward him."""
    sc = Scene(292)
    sky(sc, "black")
    sc.rect(0, 92, W, 94, (255, 255, 250))
    sc.glow(300, 93, 50, (240, 240, 255), 0.6, squash=0.15)
    sc.bands("1a1620", "0c0a10", 94, H, n=4)
    sc.poly([(296, 96), (312, 96), (220, 180), (130, 180)], (40, 38, 44))
    sc.glow(190, 130, 60, (240, 240, 255), 0.5)
    for k, (x, f) in enumerate(((110, 150), (140, 172), (250, 150), (270, 176), (90, 176))):
        d = abs(x - 190) / 100
        sc.put("ghost", x, f, light=(0.8, 0.8, 0.85), alpha=min(1.0, 0.25 + d))
    sc.put("oswin_white", 190, 170, rim=(255, 255, 255))
    warden(sc, 5, 50, 160, glow=0.4, flip=False)
    sc.vignette(0.5)
    return sc


def dawn_03():
    """Close on the lantern: white flame, six coloured sparks circling inside, the face of a city reflected in each spark."""
    sc = Scene(293)
    sc.bands("10101a", "06060a", 0, H, n=3)
    cx, cy = 160, 92
    sc.glow(cx, cy, 120, (230, 236, 255), 0.6)
    sc.rect(cx - 4, 10, cx + 4, 40, (90, 80, 60))                     # the hook and cap
    sc.poly([(cx - 34, 40), (cx + 34, 40), (cx + 26, 30), (cx - 26, 30)], (120, 100, 60))
    sc.rect(cx - 36, 40, cx + 36, 150, (200, 210, 230))
    sc.rect(cx - 32, 44, cx + 32, 146, (236, 240, 255))
    for x in (cx - 36, cx - 2, cx + 32):
        sc.rect(x, 40, x + 4, 150, (110, 92, 56))
    sc.rect(cx - 40, 150, cx + 40, 160, (120, 100, 60))
    sc.poly([(cx - 10, 136), (cx + 10, 136), (cx + 4, 90), (cx, 70), (cx - 4, 90)], (255, 255, 255))
    for k, c in enumerate(RINGC):
        a = k / 6 * math.pi * 2 + 0.3
        x, y = cx + math.cos(a) * 22, 100 + math.sin(a) * 30
        sc.glow(x, y, 7, c, 0.8)
        sc.disc(x, y, 3, c)
        sc.rect(int(x) - 1, int(y) - 1, int(x) + 2, int(y), (255, 255, 255))   # a tiny wall of a city in each spark
    return sc


def dawn_04():
    """Oswin, white-haired, standing tall, at the foot of the wall below the Queen."""
    sc = Scene(294)
    sky(sc, "black")
    sc.bands("1a1620", "0c0a10", 120, H, n=4)
    for x in range(-4, 200, 18):
        sc.rect(x, 68, x + 11, 80, (130, 124, 118))
    sc.put("ysolde_blind", 120, 80, light=(0.8, 0.78, 0.85))
    sc.rect(0, 80, 200, 160, (130, 124, 118))
    sc.rect(0, 80, 200, 82, (190, 184, 176))
    for y in range(88, 160, 8):
        sc.rect(0, y, 200, y + 1, (100, 94, 90))
    sc.glow(230, 130, 50, (240, 240, 255), 0.5)
    sc.put("oswin_white", 230, 172, flip=True, rim=(255, 255, 255))
    sc.vignette(0.5)
    return sc


def dawn_05():
    """Oswin raising the lantern. Light pours up into the empty Sunstone frame above the city; it blazes. Real dawn."""
    sc = Scene(295)
    city_wide(sc, "dawn", glow=False, plain="5a4a50")
    m = sc.poly([(156, 112), (164, 112), (176, 0), (144, 0)], None)
    sc.blend(m, (255, 250, 230), 0.75)
    sc.glow(160, 40, 60, (255, 230, 150), 0.9)
    sc.disc(160, 40, 18, (255, 236, 170), squash=0.45)
    sc.disc(160, 40, 12, (255, 252, 230), squash=0.45)
    sc.glow(320, 120, 120, (255, 210, 130), 0.5)
    sc.vignette(0.3)
    return sc


# ---- the Heart falls ----------------------------------------------------------------------------------------------
def heart_falls_01():
    """The knot of shards collapsing in dawn light. In the middle, Cassivane on his knees, ash, locket in his hands."""
    sc = Scene(301)
    sky(sc, "dawn")
    sc.bands("6a5a60", "2a2228", 130, H, n=4)
    sc.put("sundered_heart", 160, 190, pose=death_pose("sundered_heart", 4), light=(1.0, 0.95, 0.9))
    sc.put("cassivane", 160, 174, pose=kneel_pose(), light=(0.8, 0.76, 0.76))
    sc.vignette(0.4)
    return sc


def heart_falls_02():
    """Ilyra kneeling in front of him, taking his hands."""
    sc = Scene(302)
    sky(sc, "dawn")
    sc.bands("6a5a60", "2a2228", 130, H, n=4)
    for k in range(14):
        x, y = sc.rng.uniform(40, 280), sc.rng.uniform(150, 176)
        sc.poly([(x, y), (x + 4, y - 3), (x + 8, y)], (230, 190, 110))
    sc.put("cassivane", 186, 176, pose=kneel_pose(), light=(0.8, 0.76, 0.76), flip=True)
    sc.put("ilyra", 134, 176, rim=(255, 230, 180))
    sc.vignette(0.4)
    return sc


def heart_falls_03():
    """Cassivane's face, the grey leaving his eyes. He presses the locket into her hand and crumbles into ash in the dawn wind."""
    sc = Scene(303)
    sky(sc, "dawn")
    sc.bands("6a5a60", "2a2228", 130, H, n=4)
    import portraits
    im = np.asarray(portraits.portrait("cassivane")).astype(np.float32)
    rng = np.random.default_rng(3)
    keep = rng.random(im.shape[:2]) > np.clip((np.arange(96)[None, :] - 40) / 50, 0, 1)
    sc._paste(im[..., :3], im[..., 3] / 255 * keep, 112, 40)
    for _ in range(120):
        x, y = int(rng.uniform(170, 300)), int(rng.uniform(40, 140))
        sc.c[y, x] = (120, 110, 110) if rng.random() < 0.6 else (220, 200, 180)
    sc.glow(150, 150, 10, GOLD, 0.8)
    sc.disc(150, 150, 3, (230, 180, 70))
    sc.vignette(0.4)
    return sc


def heart_falls_04():
    """Ysolde on the wall, face lifted to the light, crying, smiling. The six peoples cheering in streets lit gold."""
    sc = Scene(304)
    street(sc, "day", seed=21)
    sc.glow(300, 20, 120, (255, 220, 140), 0.6)
    for row, y in enumerate((160, 168, 176)):
        people_row(sc, 4 + row * 3, y, 52, step=6, cols=[tuple(int(v * 0.7) for v in c) for c in RINGC])
    sc.rect(150, 96, 260, 132, (200, 192, 176))
    battlements(sc, 96, (200, 192, 176), (240, 234, 220))
    sc.put("ysolde_blind", 210, 96, light=(1.1, 1.0, 0.9), rim=(255, 236, 170))
    sc.c[60:63, 216] = (200, 230, 255)                              # a tear under the blindfold
    sc.vignette(0.3)
    return sc


def heart_falls_05():
    """Oswin, Corvin, Tamsin and the Wardens around the Heartstone. Oswin looking east toward the Rift."""
    sc = Scene(305)
    hall(sc, dim=1.0, throne=False)
    heartstone(sc, 160, 110, 1.4)
    for i, x in ((0, 20), (1, 50), (2, 80), (3, 240), (4, 270), (5, 300)):
        warden(sc, i, x, 150, glow=0.25, flip=x > 160, alpha=0.9)
    sc.put("tamsin", 112, 174)
    sc.put("corvin", 206, 174, flip=True)
    sc.put("oswin_white", 160, 178, rim=(255, 255, 255))
    sc.vignette(0.45)
    return sc


def heart_falls_06():
    """The army of the Concord marching out of Solenne's gates in dawn light, every hero and Warden at its head, toward the Rift."""
    sc = Scene(306)
    city_wide(sc, "gold", glow=True, plain="7a6a60")
    sc.poly([(150, 142), (170, 142), (320, 170), (320, 180), (290, 180)], (130, 116, 100))
    for k in range(8):
        tiny_army(sc, 170 + k * 18, 186 + k * 18, 146 + k * 4, 4, (80, 90, 130), rows=2)
    for i in range(6):
        sc.glow(300 - i * 5, 156 + i, 4, RINGC[i], 0.8)
    sc.vignette(0.3)
    return sc


# ---- the assault on Nhal Vorath -----------------------------------------------------------------------------------
def assault_intro_01():
    """Through the Crack: the Outer Hollow, a black sky with a black sun and a crown-shaped gap. Hanging upside down beneath
    it, a vast fortress."""
    sc = Scene(311)
    hollow(sc)
    sc.vignette(0.5)
    return sc


def assault_intro_02():
    """Close on the citadel walls: pieces of fallen cities: glass towers, a frozen ship, uprooted trees, broken Spirewright
    towers, and the Dawn Gate set as a tooth in an enormous mouth."""
    sc = Scene(312)
    sc.bands("0a080c", "1a1820", 0, H, n=4)
    sc.rect(0, 20, W, 60, (40, 36, 46))
    for (x, w, h, c) in ((10, 12, 40, (90, 140, 160)), (30, 8, 30, (120, 170, 190))):   # glass towers set in the wall
        sc.rect(x, 20 - h // 2, x + w, 50, c)
        sc.rect(x, 20 - h // 2, x + 2, 50, (190, 230, 240))
    sc.poly([(250, 30), (310, 30), (300, 44), (258, 44)], (150, 180, 200))               # a frozen ship
    sc.rect(276, 6, 278, 30, (110, 120, 130))
    sc.poly([(278, 8), (296, 18), (278, 26)], (200, 220, 230))
    for x in (70, 200):                                              # an uprooted tree, roots up
        sc.line(x, 20, x, 54, (70, 50, 40))
        for k in range(5):
            sc.line(x, 20, x - 10 + k * 5, 6, (70, 50, 40))
    sc.put("gatemaw", 160, 178, light=(0.9, 0.88, 0.95))
    sc.vignette(0.45)
    return sc


def assault_intro_03():
    """The black sun's corona flaring; every colour on screen drains to grey for a moment."""
    sc = Scene(313)
    hollow(sc, fortress=False)
    sc.glow(160, 34, 120, (220, 220, 230), 0.6)
    tiny_army(sc, 20, 300, 170, 40, (90, 100, 140))
    for i in range(6):
        sc.glow(40 + i * 48, 160, 6, RINGC[i], 0.8)
    lum = sc.c.mean(-1, keepdims=True)
    sc.c[:] = sc.c * 0.15 + lum * 0.85
    sc.vignette(0.5)
    return sc


def assault_intro_04():
    """Tamsin, lantern-pole raised, at the head of the army, the Gatemaw ahead."""
    sc = Scene(314)
    hollow(sc, fortress=False)
    sc.put("gatemaw", 250, 150, light=(0.7, 0.68, 0.75))
    tiny_army(sc, 0, 110, 172, 20, (90, 100, 140))
    sc.glow(70, 118, 24, (255, 210, 120), 0.6)
    sc.put("tamsin", 70, 176, rim=(255, 220, 150))
    sc.vignette(0.5)
    return sc


# ---- the Mirror Spire ---------------------------------------------------------------------------------------------
def mirror_spire_01():
    """A dark mirror of Solenne's six rings, upside down; on its walls the six Heralds as glassy grey Echo-Heralds."""
    sc = Scene(321)
    hollow(sc, fortress=False)
    sc.put("mirror_spire", 160, 230, light=(0.9, 0.9, 1.0))
    sc.put("echo_ashwick", 50, 176)
    sc.put("echo_vesper", 280, 186)
    sc.vignette(0.5)
    return sc


def mirror_spire_02():
    """Seraphel in the top gate, armour drained of colour, sword blazing, holding the doors apart as the army runs past."""
    sc = Scene(322)
    sc.bands("0a080c", "1a1820", 0, H, n=4)
    sc.rect(0, 0, W, 160, (40, 40, 48))
    sc.rect(100, 30, 220, 160, (6, 6, 8))
    sc.rect(70, 30, 110, 160, (60, 58, 70))                           # the doors forced apart
    sc.rect(210, 30, 250, 160, (60, 58, 70))
    sc.bands("2a2830", "0c0a10", 160, H, n=3)
    im, fx, fy = arr_of("seraphel", pose=attack_pose("seraphel", 6))
    grey_of(im, 0.85)
    sc.glow(166, 100, 40, (255, 230, 160), 0.6)
    paste(sc, im, 160, 166, fx, fy)
    tiny_army(sc, 0, 90, 176, 14, (90, 100, 140), rows=2)
    tiny_army(sc, 230, 320, 176, 14, (90, 100, 140), rows=2)
    sc.vignette(0.5)
    return sc


def mirror_spire_03():
    """Seraphel, smiling, fading."""
    sc = Scene(323)
    sc.bands("141218", "060508", 0, H, n=4)
    import portraits
    im = np.asarray(portraits.portrait("seraphel")).astype(np.float32)
    grey_of(im, 0.5)
    sc._paste(im[..., :3], im[..., 3] / 255 * 0.7, 112, 40)
    sc.particles(120, [(255, 230, 160), (255, 255, 230), (200, 180, 120)], 20, 160, 90, 230)
    sc.vignette(0.5)
    return sc


# ---- the Crownless Throne -----------------------------------------------------------------------------------------
def _void_hall(sc):
    sc.bands("060508", "121016", 0, H, n=4)
    for x in (20, 70, 250, 300):                                    # pillars that end in nothing
        sc.rect(x, 0, x + 12, 110, (26, 24, 32))
        sc.rect(x, 0, x + 2, 110, (44, 40, 54))
        sc.poly([(x, 110), (x + 6, 124), (x + 12, 110)], (26, 24, 32))
    sc.stars(30, H, cols=((60, 60, 70), (40, 40, 50)))


def crownless_throne_01():
    """A vast empty hall with no floor. In the middle, standing on nothing: a figure of black glass with a crown-shaped gap for
    a face, the Heartstone's stolen light caught in its chest."""
    sc = Scene(331)
    _void_hall(sc)
    sc.put("vael_orrun", 160, 330)
    sc.vignette(0.5)
    return sc


def crownless_throne_02():
    """Vael-Orrun turning toward the army; cracks in its glass bleeding red, then blue, then green."""
    sc = Scene(332)
    _void_hall(sc)
    sc.put("vael_orrun", 170, 300, flip=True)
    for k, (c, x0) in enumerate((((230, 60, 50), 150), ((80, 120, 240), 172), ((90, 220, 90), 190))):
        x, y = x0, 70
        for j in range(8):
            nx, ny = x + sc.rng.uniform(-6, 6), y + 10
            sc.line(x, y, nx, ny, c)
            x, y = nx, ny
        sc.glow(x0, 100, 10, c, 0.5)
    tiny_army(sc, 0, 120, 178, 18, (90, 100, 140), rows=2)
    sc.vignette(0.5)
    return sc


def crownless_throne_03():
    """Mirelle at the edge of the hall, blind eyes glowing teal, a small smile."""
    sc = Scene(333)
    _void_hall(sc)
    sc.glow(160, 88, 70, (60, 200, 200), 0.35)
    _face_close(sc, "mirelle", 112, 40)
    sc.vignette(0.5)
    return sc


# ---- the epilogue -------------------------------------------------------------------------------------------------
def epilogue_01():
    """The six Wardens in a ring around Vael-Orrun, hands joined, their light rising."""
    sc = Scene(341)
    _void_hall(sc)
    for i in range(6):
        x = 160 + math.cos(i / 6 * math.pi * 2) * 10
        m = sc.poly([(x - 4 + (i - 2.5) * 22, 150), (x + 4 + (i - 2.5) * 22, 150), (x + (i - 2.5) * 6, 0), (x + (i - 2.5) * 6 - 2, 0)], None)
        sc.blend(m, RINGC[i], 0.45)
    sc.put("vael_orrun", 160, 260, light=(0.85, 0.85, 0.95))
    for k, (i, x, f) in enumerate(((5, 40, 160), (0, 84, 168), (1, 126, 176), (2, 194, 176), (3, 236, 168), (4, 280, 160))):
        warden(sc, i, x, f, glow=0.45, flip=x > 160)
    sc.vignette(0.45)
    return sc


def epilogue_02():
    """Oswin stepping into the ring and placing the white lantern into the crown-shaped gap. Light floods the black glass."""
    sc = Scene(342)
    _void_hall(sc)
    sc.put("vael_orrun", 160, 360)
    sc.glow(160, 60, 60, (240, 240, 255), 0.8)
    lantern(sc, 160, 64, 2)
    for k in range(10):
        a = k / 10 * math.pi * 2
        sc.line(160, 64, 160 + math.cos(a) * 70, 64 + math.sin(a) * 50, (200, 200, 230))
    sc.put("oswin_white", 110, 178, rim=(255, 255, 255))
    sc.vignette(0.45)
    return sc


def epilogue_03():
    """Vael-Orrun cracking apart into pure white light, which rises, and the black sun above the citadel turns gold."""
    sc = Scene(343)
    hollow(sc, sun="gold", fortress=True)
    m = sc.poly([(150, 180), (170, 180), (180, 0), (140, 0)], None)
    sc.blend(m, (255, 255, 250), 0.6)
    im, fx, fy = arr_of("vael_orrun", light=(1, 1, 1))
    im[..., :3] = im[..., :3] * 0.2 + 220
    rng = np.random.default_rng(9)
    im[..., 3] *= rng.random(im.shape[:2]) < 0.55
    paste(sc, im, 160, 360, fx, fy)
    sc.particles(100, [(255, 255, 255), (255, 240, 200)], 40, 180, 110, 210)
    sc.vignette(0.35)
    return sc


def epilogue_04():
    """Montage: the forges relit, the Galeborn raising tents, Sylvaine planting Elowen's seed, Pearlhaven's fleet coming
    home, Seraphel's glass sword set into the rebuilt Sunstone, and Tamsin with Fennick's spectacles beside an old Oswin."""
    sc = Scene(344)
    sc.c[:] = (14, 12, 16)
    cells = [(4, 4), (108, 4), (212, 4), (4, 92), (108, 92), (212, 92)]
    for k, (x0, y0) in enumerate(cells):
        x1, y1 = x0 + 104, y0 + 84
        m = (sc.xs >= x0) & (sc.xs < x1) & (sc.ys >= y0) & (sc.ys < y1)
        sc.bands("f0c080", "a06040", y0, y1, n=4, mask=m)
        if k == 0:     # forges of Kethra
            sc.rect(x0, y0 + 50, x1, y1, (50, 30, 26))
            for j in range(3):
                sc.rect(x0 + 10 + j * 30, y0 + 34, x0 + 26 + j * 30, y0 + 50, (70, 40, 30))
                sc.glow(x0 + 18 + j * 30, y0 + 44, 10, (255, 140, 40), 0.8)
            people_row(sc, x0 + 6, y0 + 74, 12, step=8, carry=(100, 70, 50))
            sc.put("brannoc", x0 + 74, y0 + 80, flip=True, light=FIRELIT)
        elif k == 1:   # tents at Aurvanis
            sc.rect(x0, y0 + 56, x1, y1, (110, 140, 70))
            for j in range(5):
                sc.poly([(x0 + 6 + j * 20, y0 + 60), (x0 + 15 + j * 20, y0 + 46), (x0 + 24 + j * 20, y0 + 60)], (220, 210, 190))
        elif k == 2:   # the seed planted
            sc.rect(x0, y0 + 60, x1, y1, (70, 50, 36))
            sc.line(x0 + 52, y0 + 60, x0 + 52, y0 + 46, (90, 170, 60))
            sc.line(x0 + 52, y0 + 50, x0 + 46, y0 + 44, (120, 200, 70))
            sc.line(x0 + 52, y0 + 48, x0 + 58, y0 + 42, (120, 200, 70))
            sc.glow(x0 + 52, y0 + 50, 10, (140, 240, 80), 0.6)
            sc.put("sylvaine", x0 + 30, y0 + 80, light=(1.05, 0.95, 0.85))
        elif k == 3:   # the fleet coming home
            sc.rect(x0, y0 + 50, x1, y1, (60, 110, 130))
            for j in range(4):
                bx = x0 + 10 + j * 24
                sc.poly([(bx, y0 + 50), (bx + 14, y0 + 50), (bx + 12, y0 + 54), (bx + 2, y0 + 54)], (90, 60, 40))
                sc.poly([(bx + 7, y0 + 34), (bx + 7, y0 + 49), (bx + 14, y0 + 48)], (240, 236, 220))
        elif k == 4:   # Seraphel's sword set into the rebuilt Sunstone
            sc.disc(x0 + 52, y0 + 36, 22, (180, 140, 60), squash=0.6)
            sc.disc(x0 + 52, y0 + 36, 18, (255, 220, 140), squash=0.6)
            sc.rect(x0 + 50, y0 + 30, x0 + 54, y0 + 70, (255, 250, 220))
            sc.glow(x0 + 52, y0 + 36, 30, (255, 230, 160), 0.6)
        else:          # the Lantern Walk at sunset
            sc.rect(x0, y0 + 62, x1, y1, (150, 140, 130))
            sc.glow(x0 + 90, y0 + 40, 30, (255, 170, 90), 0.8)
            sc.disc(x0 + 90, y0 + 46, 8, (255, 200, 120))
            sc.rect(x0, y0 + 56, x1, y0 + 62, (120, 110, 100))
            sc.put("oswin_grey", x0 + 48, y0 + 80, light=(1.05, 0.9, 0.8))
            sc.put("tamsin", x0 + 22, y0 + 80, light=(1.05, 0.9, 0.8))
        panel(sc, x0, y0, x1, y1, (14, 12, 16))
    sc.vignette(0.3)
    return sc


def epilogue_05():
    """Ysolde, older, grey hair, still blindfolded, on the walls of a rebuilt Solenne, sun on her face. Credits roll."""
    sc = Scene(345)
    sky(sc, "gold")
    sc.glow(300, 60, 120, (255, 220, 140), 0.7)
    sc.ridge(130, 4, "8a7a7a", 51)
    solenne(sc, 70, 140, 0.5, glow=True)
    battlements(sc, 156, (200, 192, 176), (240, 234, 220))
    sc.put("ysolde_old", 200, 156, light=(1.1, 1.0, 0.9), rim=(255, 236, 170))
    wall_face(sc, 156, (200, 192, 176), (240, 234, 220))
    sc.vignette(0.3)
    return sc


def epilogue_06():
    """After the credits: the Hall of the Ring, rebuilt. The Heartstone glows in six colours... then, faintly, a seventh.
    A colour nobody has a name for yet. Cut to black."""
    sc = Scene(346)
    hall(sc, dim=0.5, throne=False)
    sc.blend(np.ones((H, W), bool), (4, 4, 6), 0.55)
    heartstone(sc, 160, 96, 2.4, seventh=True)
    sc.vignette(0.8)
    return sc

# ---- the truth about Vael-Orrun (convergence_intro) and the end (epilogue), lore of 2026-11-11 ----------------------
def fresco(sc, x0, y0, x1, y1, seed=0, burn=0.0):
    """Turn a region into an old wall painting: ochre plaster tones, a crackle of fine lines, flaked spots, a border.
    burn > 0 eats the painting from its edges inward with fire."""
    rng = np.random.default_rng(seed)
    m = (sc.xs >= x0) & (sc.xs < x1) & (sc.ys >= y0) & (sc.ys < y1)
    tones = np.array([(64, 40, 32), (120, 72, 48), (176, 120, 76), (214, 172, 120), (236, 214, 170)], np.float32)
    lum = sc.c[..., :3].mean(-1)
    idx = np.clip((lum / 200 * len(tones)).astype(int), 0, len(tones) - 1)
    painted = tones[idx] * 0.6 + sc.c * 0.4
    sc.c[m] = painted[m]
    for _ in range(26):                                               # crackle
        x, y = rng.uniform(x0, x1), rng.uniform(y0, y1)
        for _ in range(int(rng.integers(6, 16))):
            nx, ny = x + rng.uniform(-5, 5), y + rng.uniform(-5, 5)
            if x0 <= nx < x1 and y0 <= ny < y1:
                sc.line(x, y, nx, ny, (70, 50, 40))
            x, y = nx, ny
    for _ in range(18):                                               # flaked plaster
        x, y, r = rng.uniform(x0, x1), rng.uniform(y0, y1), rng.uniform(1.5, 4)
        sc.c[(np.hypot(sc.xs - x, sc.ys - y) < r) & m] = (200, 186, 160)
    for k in range(3):
        panel(sc, x0 - k, y0 - k, x1 + k, y1 + k, (90, 60, 40) if k == 1 else (40, 26, 20))
    if burn:
        d = np.minimum.reduce([sc.xs - x0, x1 - sc.xs, sc.ys - y0, y1 - sc.ys]).astype(np.float32)
        d += rng.normal(0, 3, d.shape)
        edge = burn * min(x1 - x0, y1 - y0) / 2
        gone = m & (d < edge)
        sc.c[gone] = (10, 6, 6)
        rim = m & (d >= edge) & (d < edge + 3)
        sc.c[rim] = (255, 140, 40)
        sc.blend(m & (d >= edge + 3) & (d < edge + 8), (60, 30, 20), 0.6)
        for _ in range(30):
            ys, xs = np.nonzero(rim)
            if len(xs):
                j = int(rng.integers(len(xs)))
                flame(sc, int(xs[j]), int(ys[j]), rng.uniform(4, 10))


def convergence_intro_03():
    """The six Wardens standing in a ring around the outer walls of Solenne, the Heartstone pulsing.
    Ignar kneels to the blind Queen."""
    sc = Scene(243)
    sky(sc, "night")
    sc.ridge(130, 3, "2a2434", 32)
    sc.bands("2a2434", "100c14", 130, H, n=4)
    for i, x, f in ((5, 52, 112), (1, 104, 104), (2, 216, 104), (3, 268, 112)):
        warden(sc, i, x, f, glow=0.35, flip=x > 160)
    solenne(sc, 160, 140, 0.8, glow=False)
    heartstone(sc, 160, 92, 0.5)
    warden(sc, 4, 30, 176, glow=0.5)
    sc.glow(196, 150, 34, RINGC[0], 0.5)
    im, fx, fy = arr_of("ignar_king", pose=kneel_pose("ignar_king"), flip=True, light=(1.1, 0.85, 0.7))
    paste(sc, im, 200, 176, fx, fy)
    sc.put("ysolde_blind", 150, 176, rim=(255, 200, 140))
    sc.vignette(0.45)
    return sc


def convergence_intro_04():
    """Flashback, painted like an old fresco: a young, kind-faced king in grey at a long feast table between six crowned
    monarchs, his Tidefolk queen and small son beside him. Everyone is smiling."""
    sc = Scene(245)
    x0, y0, x1, y1 = 16, 14, 304, 166
    sc.c[:] = (24, 18, 16)
    sc.bands("4a3a5a", "8a6a5a", y0, 110, n=4)
    for x in range(30, 300, 34):                                      # the hall's arches behind
        sc.rect(x, 30, x + 6, 110, (150, 120, 96))
        sc.disc(x + 20, 46, 12, (110, 86, 80))
    seats = [("ignar_king", 0), ("aurath_king", 1), ("elowen_queen", 2), ("vael_orrun_young", None), ("ysmera", None),
             ("caelan", None), ("thalassa_queen", 3), ("orrok_king", 4), ("nyxara_queen", 5)]
    for k, (name, i) in enumerate(seats):
        x = 34 + k * 31
        if i is not None:
            sc.glow(x, 92, 16, RINGC[i], 0.35)
        sc.put(name, x, 146 if name != "caelan" else 140, flip=k > 4)
    sc.rect(20, 118, 300, 128, (120, 70, 44))                         # the long table
    sc.rect(20, 118, 300, 120, (170, 110, 70))
    sc.rect(20, 128, 300, 150, (90, 52, 34))
    for k in range(9):                                                # cups, bread, candles
        x = 30 + k * 31
        sc.rect(x, 114, x + 3, 118, (210, 180, 90))
        sc.disc(x + 10, 116, 3, (200, 150, 90), squash=0.6)
    for x in (80, 160, 240):
        sc.rect(x, 108, x + 2, 118, (236, 226, 200))
        flame(sc, x + 1, 108, 5)
    sc.bands("6a4a3a", "3a2a20", 150, y1, n=3)
    fresco(sc, x0, y0, x1, y1, seed=4)
    sc.vignette(0.5)
    return sc


def convergence_intro_05():
    """The fresco catches fire: the black city of Vael burning at night, soldiers of six colours in the gates; the king on
    his knees in the ashes of the feast hall, holding a ring."""
    sc = Scene(246)
    x0, y0, x1, y1 = 16, 14, 304, 166
    sc.c[:] = (14, 8, 8)
    sc.bands("1a1018", "5a2418", y0, 120, n=5)
    for k, x in enumerate(range(20, 300, 22)):                        # the black city, burning
        h = 30 + (k * 13) % 34
        sc.rect(x, 120 - h, x + 16, 120, (24, 20, 26))
        sc.rect(x + 6, 120 - h - 8, x + 10, 120 - h, (24, 20, 26))
        flame(sc, x + 8, 120 - h, 10 + (k % 3) * 4)
        sc.glow(x + 8, 120 - h, 14, (255, 120, 40), 0.5)
    sc.rect(120, 88, 200, 120, (10, 6, 8))                            # the gates, and soldiers of six colours in them
    for k in range(12):
        x = 126 + k * 6
        c = RINGC[k % 6]
        sc.rect(x, 108, x + 3, 118, tuple(int(v * 0.8) for v in c))
        sc.rect(x + 1, 105, x + 3, 108, (60, 50, 50))
        sc.line(x + 3, 110, x + 5, 100, (180, 180, 190))
    sc.bands("3a2a24", "1a1210", 120, y1, n=3)
    sc.particles(140, [(90, 80, 76), (60, 50, 46), (255, 140, 50)], 120, y1, x0, x1)
    im, fx, fy = arr_of("vael_orrun_young", pose=kneel_pose("vael_orrun_young"), light=(1.0, 0.8, 0.7))
    sc.glow(160, 130, 30, (255, 140, 60), 0.4)
    paste(sc, im, 160, 152, fx, fy)
    sc.glow(176, 126, 6, GOLD, 0.8)
    sc.c[125:128, 175:178] = (255, 220, 120)
    fresco(sc, x0, y0, x1, y1, seed=5, burn=0.14)
    sc.vignette(0.5)
    return sc


def convergence_intro_06():
    """Nyxara, the stars in her face dim, turning away. Behind her, deep in the stars, a patch of sky with no stars in it."""
    sc = Scene(247)
    sc.bands("0a0814", "1c1630", 0, H, n=5)
    hole = np.hypot(sc.xs - 240, (sc.ys - 54) * 1.3) < 30
    rng = np.random.default_rng(47)
    for _ in range(420):
        x, y = int(rng.integers(0, W)), int(rng.integers(0, H))
        if not hole[y, x]:
            sc.c[y, x] = [(230, 230, 255), (170, 170, 210), (110, 110, 150)][int(rng.integers(3))]
    sc.blend(hole, (4, 4, 8), 0.25)
    sc.bands("141020", "08060c", 150, H, n=3)
    sc.glow(130, 120, 40, RINGC[5], 0.35)
    im, fx, fy = arr_of("nyxara_queen", flip=True, light=(0.7, 0.68, 0.8))
    paste(sc, im, 130, 172, fx, fy)
    sc.vignette(0.55)
    return sc


def convergence_intro_07():
    """Ysolde alone in the Hall of the Ring, her hand on the Heartstone, which is warm, like a crown just taken off."""
    sc = Scene(248)
    hall(sc, dim=0.55, throne=False)
    sc.blend(np.ones((H, W), bool), (6, 4, 8), 0.35)
    sc.rect(146, 130, 196, 160, (70, 64, 72))                          # the plinth
    sc.rect(146, 130, 196, 132, (120, 112, 120))
    heartstone(sc, 171, 104, 1.2)
    sc.glow(171, 110, 50, (255, 180, 100), 0.35)
    sc.put("ysolde_blind", 138, 166, light=(1.0, 0.9, 0.85), rim=(255, 200, 140))
    sc.vignette(0.6)
    return sc


def convergence_intro_08():
    return convergence_intro_04_crossmere()


def epilogue_03_young():
    """Inside the light: Vael-Orrun as he was, the kind-faced king in grey, holding his wife's ring. His eyes are not grey.
    They are only tired."""
    sc = Scene(347)
    sc.c[:] = (250, 250, 244)
    sc.glow(160, 90, 160, (255, 236, 200), 0.5)
    im = np.asarray(_portrait("vael_orrun_young")).astype(np.float32)
    sc._paste(im[..., :3], im[..., 3] / 255, 112, 30)
    sc.glow(192, 142, 8, GOLD, 0.9)
    sc.disc(192, 142, 3, (230, 180, 70))
    sc.disc(192, 142, 1.5, (250, 250, 244))
    m = np.hypot(sc.xs - 160, sc.ys - 78) > 70
    sc.blend(m, (255, 255, 250), np.clip((np.hypot(sc.xs - 160, sc.ys - 78) - 70) / 60, 0, 1), steps=4)
    return sc


def epilogue_04_past():
    """Vael-Orrun looking past the Wardens, past the heroes, at something behind the camera."""
    sc = Scene(348)
    sc.c[:] = (230, 230, 226)
    sc.bands("e8e8e0", "8a8a90", 0, H, n=5)
    im = np.asarray(_portrait("vael_orrun_young")).astype(np.float32)[:, ::-1]   # turned to us, eyes on the camera
    sc._paste(im[..., :3], im[..., 3] / 255, 112, 40)
    sc.blend(np.ones((H, W), bool), (40, 40, 60), 0.12)
    sc.vignette(0.7, col=(20, 20, 30))
    return sc


def epilogue_05_thalassa():
    """Thalassa, bells silent in her hair, the only Warden who can meet his eyes."""
    sc = Scene(349)
    _void_hall(sc)
    sc.glow(160, 88, 80, RINGC[3], 0.4)
    _face_close(sc, "thalassa", 112, 40)
    sc.vignette(0.5)
    return sc


def epilogue_09():
    """After the credits: the Hall of the Ring, rebuilt, empty, night. The Heartstone glows in six colours... then, faintly,
    a seventh. Ilyra, alone, leans in to look. Deep inside the seventh colour, something with no colour at all opens, like an eye."""
    sc = Scene(346)
    hall(sc, dim=0.5, throne=False)
    sc.blend(np.ones((H, W), bool), (4, 4, 6), 0.55)
    heartstone(sc, 170, 92, 2.4, seventh=True)
    cx, cy = 170, 92                                                   # the eye, no colour at all
    eye = (np.abs(sc.xs - cx) / 9) ** 2 + (np.abs(sc.ys - cy) / 3.2) ** 2 < 1
    sc.c[eye] = (176, 176, 176)
    sc.c[(np.hypot(sc.xs - cx, sc.ys - cy) < 2.2) & eye] = (12, 12, 12)
    sc.put("ilyra", 116, 170, light=(0.8, 0.8, 0.9), rim=(220, 220, 220))
    sc.vignette(0.8)
    return sc


def epilogue_10():
    """Black. No sound at all for a moment before the voice, and none after. Title card: TO BE CONTINUED."""
    from PIL import Image as _I, ImageDraw as _D, ImageFont as _F
    sc = Scene(350)
    sc.c[:] = (0, 0, 0)
    card = _I.new("L", (W, H), 0)
    _D.Draw(card).text((W // 2, H // 2), "TO BE CONTINUED", fill=255, font=_F.load_default(), anchor="mm")
    m = np.asarray(card) > 100
    sc.c[m] = (200, 196, 188)
    return sc


def _portrait(cid):
    import portraits
    return portraits.portrait(cid) if cid in portraits.PEOPLE or cid in portraits.HEADS else people.portrait(cid).image()


CINEMATICS.update({
    "regents_counsel": [regents_counsel_01, regents_counsel_02, regents_counsel_03, regents_counsel_04],
    "night_of_falling_stars": [nofs_01, nofs_02, nofs_03, nofs_04, nofs_05, nofs_06, nofs_07, nofs_08, nofs_09, nofs_10,
                               nofs_11, nofs_12],
    "long_night": [long_night_01, long_night_02, long_night_03, long_night_04],
    "convergence_intro": [convergence_intro_01, convergence_intro_02, convergence_intro_03, convergence_intro_04,
                          convergence_intro_05, convergence_intro_06, convergence_intro_07, convergence_intro_08],
    "crossroads": [crossroads_01, crossroads_02, crossroads_03, crossroads_04],
    "lumen_gate": [lumen_gate_01, lumen_gate_02, lumen_gate_03],
    "capital_prelude": [capital_prelude_01, capital_prelude_02, capital_prelude_03, capital_prelude_04],
    "solenne_falls": [solenne_falls_01],
    "dawn": [dawn_01, dawn_02, dawn_03, dawn_04, dawn_05],
    "heart_falls": [heart_falls_01, heart_falls_02, heart_falls_03, heart_falls_04, heart_falls_05, heart_falls_06],
    "assault_intro": [assault_intro_01, assault_intro_02, assault_intro_03, assault_intro_04],
    "mirror_spire": [mirror_spire_01, mirror_spire_02, mirror_spire_03],
    "crownless_throne": [crownless_throne_01, crownless_throne_02, crownless_throne_03],
    "epilogue": [epilogue_01, epilogue_02, epilogue_03_young, epilogue_04_past, epilogue_05_thalassa, epilogue_03, epilogue_04,
                 epilogue_05, epilogue_09, epilogue_10],
})
