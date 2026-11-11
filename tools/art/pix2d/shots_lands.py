"""Stills for the six land campaigns: each land's intro, Herald and Warden cinematics.

Each land has one backdrop painter; shots compose it with sprites and effects. Shot docstrings are the art notes.
"""
from __future__ import annotations

import math

import numpy as np

import anim
from stills import (CINEMATICS, DUSK, FIRELIT, H, NIGHT, RINGC, W, Scene, flame, hx, panel, solenne, tiny_army)

GREYL = (0.62, 0.62, 0.68)


def pose_of(fn, i, n, style, name):
    p = fn(i, n, style, name)
    p["_t"] = i
    return p


def death_pose(name, i):
    return pose_of(anim.death, i, 8, anim.DEATH.get(name, anim.STYLE.get(name, "swing")), name)


def attack_pose(name, i):
    return pose_of(anim.attack, i, 8, anim.STYLE.get(name, "swing"), name)


def walk_pose(name, i):
    return pose_of(anim.walk, i, 8, anim.STYLE.get(name, "swing"), name)


def people_row(sc, x0, feet, n, cols=((70, 50, 40), (50, 44, 60), (90, 70, 50)), step=6, skin=(200, 160, 130), carry=None):
    """A row of small background folk, a few pixels tall."""
    for k in range(n):
        x = int(x0 + k * step + sc.rng.uniform(-1, 1))
        c = cols[k % len(cols)]
        sc.rect(x, feet - 7, x + 3, feet, c)
        sc.rect(x + 1, feet - 9, x + 3, feet - 7, skin)
        if carry and k % 2 == 0:
            sc.rect(x + 3, feet - 6, x + 5, feet - 3, carry)
            sc.c[feet - 6, x + 4] = (255, 200, 90)


def ripple_lines(sc, y0, y1, col, step=5):
    for y in range(y0, y1, step):
        for x in range(int(sc.rng.integers(0, 12)), W, int(sc.rng.integers(18, 30))):
            sc.line(x, y, x + int(sc.rng.integers(4, 10)), y, col)


# ---- Ember Reach --------------------------------------------------------------------------------------------------
def ember_bg(sc, night=False, lava=True):
    sc.bands("1a0a10" if night else "3a1418", "6a2418" if night else "d0602a", 0, 110, n=7)
    sc.glow(230, 96, 120, (255, 120, 40), 0.45, squash=0.45)
    sc.ridge(96, 10, "2a1418", 21, freq=0.7, rim="6a2a1c", jag=4)
    for i, (base, col, rim) in enumerate(((112, "1e1014", "4a2018"), (128, "18100e", "3a1a14"), (146, "141010", "2e1612"))):
        m = sc.ridge(base, 3, col, 22 + i, freq=0.4 + i * 0.3, rim=rim)
        for x in range(0, W, 26 + i * 6):                     # basalt columns at the terrace edges
            sc.rect(x, base - 6, x + 3, base + 4, (40, 30, 34))
            sc.rect(x, base - 6, x + 1, base + 4, (90, 50, 40))
    if lava:
        for y0, x0, x1 in ((118, 0, 140), (136, 120, 320), (160, 0, 200)):
            for x in range(x0, x1):
                y = int(y0 + 3 * math.sin(x / 17.0))
                sc.c[y, x] = (255, 140, 40)
                sc.c[y + 1, x] = (200, 70, 20)
            sc.glow((x0 + x1) / 2, y0, (x1 - x0) / 2, (255, 110, 30), 0.35, squash=0.15)
    sc.particles(60, [(255, 170, 60), (255, 220, 140)], 0, 140)


def ember_intro_01():
    """Black basalt terraces, lava rivers, glassworks glowing, red and brass banners. Emberfolk at anvils."""
    sc = Scene(101)
    ember_bg(sc)
    for x, h in ((40, 30), (196, 40), (262, 34)):               # glassworks: domed kilns, glowing mouths
        sc.disc(x + 10, 128 - h + 10, 12, (40, 30, 34))
        sc.rect(x, 128 - h + 10, x + 20, 128, (40, 30, 34))
        sc.rect(x + 7, 116, x + 13, 128, (255, 160, 60))
        sc.glow(x + 10, 120, 16, (255, 140, 50), 0.6)
    for x in (80, 140, 230, 300):                                # red and brass banners
        sc.rect(x, 80, x + 1, 128, (90, 70, 40))
        sc.rect(x + 1, 80, x + 8, 96, (170, 40, 34))
        sc.rect(x + 1, 96, x + 8, 98, (200, 150, 60))
    for x in (100, 150, 250):
        sc.rect(x, 150, x + 10, 156, (60, 58, 66))
        sc.rect(x + 3, 156, x + 7, 162, (40, 38, 44))
        people_row(sc, x - 8, 162, 1, cols=((110, 60, 40),))
        sc.particles(6, [(255, 200, 90)], 144, 150, x, x + 10)
    sc.put("dwarf", 172, 172, light=FIRELIT)
    sc.vignette(0.45)
    return sc


def ember_intro_02():
    """A black tide of seawater and grey-eyed water spirits climbing the slopes, steam where it touches lava; inside it the Saltmother."""
    sc = Scene(102)
    ember_bg(sc)
    tide = sc.poly([(0, 120), (60, 112), (120, 124), (180, 118), (240, 130), (320, 126), (320, 180), (0, 180)], (12, 22, 30))
    ripple_lines(sc, 124, 178, (40, 70, 84))
    for x in range(0, 320, 14):                                   # steam where water meets lava
        sc.glow(x + 6, 116, 10, (200, 200, 206), 0.45)
    for x in (40, 90, 150, 250, 290):
        sc.put("orb_water", x, 150, light=GREYL)
    sc.put("ourra", 206, 186, light=(0.75, 0.8, 0.85))
    sc.vignette(0.5)
    return sc


def ember_intro_03():
    """Tamsin Reed at the ash road, lantern-pole raised, Kethra's forges behind her. Carts moving west."""
    sc = Scene(103)
    ember_bg(sc, lava=False)
    for x in (180, 220, 268, 300):
        sc.tower(x, 120, 12, 26, (34, 24, 26), (90, 50, 40), win=(255, 150, 50))
        sc.glow(x + 6, 96, 14, (255, 120, 40), 0.5)
    sc.poly([(0, 172), (320, 146), (320, 160), (0, 180)], (90, 80, 78))
    for x in range(10, 160, 30):
        y = int(176 - x * 0.08)
        sc.rect(x, y - 8, x + 14, y - 1, (70, 50, 34))
        sc.disc(x + 3, y, 2, (30, 24, 20))
        sc.disc(x + 11, y, 2, (30, 24, 20))
        people_row(sc, x + 16, y, 2)
    sc.glow(224, 116, 20, (255, 210, 120), 0.5)
    sc.put("tamsin", 228, 176, light=FIRELIT, rim=(255, 210, 150))
    sc.particles(80, [(150, 140, 140), (200, 190, 186)], 0, 140)
    sc.vignette(0.45)
    return sc


def ember_herald_01():
    """The Saltmother's water-column bursting apart on the steps, fish and drowned lanterns scattering; her empty eyes going dark."""
    sc = Scene(104)
    ember_bg(sc, lava=False)
    for i, y in enumerate(range(130, 180, 10)):                   # the Cinder Steps
        sc.rect(0, y, 320, y + 10, (40 - i * 4, 30 - i * 3, 32 - i * 3))
        sc.rect(0, y, 320, y + 1, (90, 50, 40))
    sc.put("ourra", 160, 176, light=(0.8, 0.8, 0.85), pose=death_pose("ourra", 4))
    for _ in range(40):                                           # the column bursting: spray, fish, lanterns
        a, r = sc.rng.uniform(math.pi, 2 * math.pi), sc.rng.uniform(20, 80)
        x, y = 160 + math.cos(a) * r, 110 + math.sin(a) * r * 0.7
        sc.rect(int(x), int(y), int(x) + 2, int(y) + 1, (40, 90, 110))
    for x, y in ((110, 70), (210, 64), (240, 100), (90, 104)):
        sc.rect(x, y, x + 4, y + 5, (90, 70, 40))
        sc.rect(x + 1, y + 1, x + 3, y + 4, (255, 190, 90))
    sc.vignette(0.5)
    return sc


def ember_herald_02():
    """A cage of crusted salt breaking open: Brannoc Emberhand staggers out and grabs his hammer; its head flares orange."""
    sc = Scene(105)
    ember_bg(sc, lava=False)
    sc.bands("2a1a1c", "120c0e", 140, 180, n=4)
    salt, lit, shade = (214, 206, 190), (250, 246, 234), (150, 140, 128)
    for k, (x, lean) in enumerate(((104, -10), (124, -4), (196, 5), (214, 12))):   # crusted bars, bent outward
        top = 64 + (k % 2) * 10
        sc.poly([(x, 160), (x + 7, 160), (x + 7 + lean, top), (x + lean, top + 4)], salt)
        sc.poly([(x, 160), (x + 2, 160), (x + 2 + lean, top + 2), (x + lean, top + 4)], lit)
        sc.poly([(x + 5, 160), (x + 7, 160), (x + 7 + lean, top), (x + 5 + lean, top)], shade)
        for j in range(5):                                         # salt crust lumps
            yy = 150 - j * 18 - k * 3
            xx = x + int(lean * (160 - yy) / (160 - top))
            sc.disc(xx + 3, yy, 3, salt)
            sc.disc(xx + 2, yy - 1, 1.4, lit)
    sc.poly([(98, 72), (160, 44), (222, 72), (214, 66), (160, 50), (106, 66)], salt)   # broken dome of the cage
    sc.poly([(98, 72), (160, 44), (166, 46), (104, 72)], lit)
    for (x, y) in ((86, 166), (120, 170), (214, 168), (238, 164), (150, 172)):         # fallen chunks
        sc.poly([(x, y), (x + 5, y - 6), (x + 11, y - 2), (x + 8, y + 2)], salt)
        sc.poly([(x, y), (x + 5, y - 6), (x + 6, y - 4)], lit)
    sc.particles(80, [(230, 226, 214), (200, 196, 184)], 100, 170, 90, 240)
    sc.glow(180, 104, 26, (255, 140, 40), 0.7)
    sc.put("brannoc", 162, 166, light=FIRELIT, rim=(255, 160, 70), pose=attack_pose("brannoc", 2))
    sc.vignette(0.5)
    return sc


def ember_herald_03():
    """Brannoc on the wall of Brazier Hold, hammer on his shoulder, grinning."""
    sc = Scene(106)
    ember_bg(sc)
    sc.wall(0, 320, 150, 18, (50, 34, 34), (110, 70, 54), step=8)
    sc.rect(0, 150, 320, 180, (36, 26, 28))
    for x in (40, 280):
        sc.tower(x, 150, 14, 46, (50, 34, 34), (110, 70, 54), win=(255, 150, 50))
        sc.glow(x + 7, 100, 12, (255, 140, 50), 0.6)
    sc.put("brannoc", 160, 134, light=FIRELIT, rim=(255, 190, 120))
    sc.vignette(0.4)
    return sc


def _ignar(sc, x, feet, light=(1, 1, 1)):
    import creatures
    import portraits
    fr = portraits.freed(creatures.CREATURES["cinder_tyrant"](), portraits.FIRE)
    arr = np.asarray(fr.image()).astype(np.float32)
    arr[..., :3] *= np.array(light, np.float32)
    sc._paste(arr[..., :3], arr[..., 3] / 255, int(x - fr.w // 2), int(feet - (fr.bh - 4)))


def ember_warden_01b():
    sc = Scene(107)
    ember_bg(sc, night=True)
    sc.bands("2a1414", "0e0a0a", 150, 180, n=4)
    sc.put("cinder_tyrant", 96, 200, light=(0.75, 0.75, 0.8), pose=death_pose("cinder_tyrant", 4), alpha=0.9)
    sc.glow(234, 110, 50, (255, 120, 30), 0.6)
    _ignar(sc, 234, 196)
    sc.vignette(0.5)
    return sc


def ember_warden_02():
    """Ignar kneeling to Brannoc and the Emberfolk, his heart-light warming their faces."""
    sc = Scene(108)
    ember_bg(sc, lava=False)
    sc.bands("2a1a18", "141010", 150, 180, n=4)
    sc.glow(190, 120, 70, (255, 130, 40), 0.5)
    import creatures
    import portraits
    fr = portraits.freed(creatures.CREATURES["cinder_tyrant"](anim.death(2, 8, "titan", "cinder_tyrant"), 66), portraits.FIRE)
    arr = np.asarray(fr.image()).astype(np.float32)
    sc._paste(arr[..., :3], arr[..., 3] / 255, int(210 - fr.w // 2), int(198 - (fr.bh - 4 + fr.pad)))
    sc.put("brannoc", 86, 170, light=FIRELIT, rim=(255, 170, 80))
    for x in (40, 60, 120):
        sc.put("dwarf", x, 174, light=FIRELIT, rim=(255, 160, 70))
    sc.vignette(0.45)
    return sc


def ember_warden_03():
    """Pyrrhenhall flooding with steam; Emberfolk carry glowing iron pots down toward the gold light of Solenne; Ignar walks with them."""
    sc = Scene(109)
    sc.bands("2a1a2a", "a06050", 0, 110, n=7)
    sc.glow(30, 104, 30, (255, 220, 140), 0.7)
    sc.disc(30, 104, 2, (255, 250, 220))
    sc.ridge(104, 8, "3a2428", 31, freq=0.8, rim="7a4a3a")
    for x in range(200, 320, 10):
        sc.glow(x, 60 + (x % 30), 22, (200, 196, 200), 0.5)
    sc.bands("2a1c1c", "120e0e", 120, 180, n=5)
    sc.poly([(0, 150), (320, 128), (320, 140), (0, 168)], (60, 44, 40))
    people_row(sc, 20, 160, 22, step=8, carry=(60, 56, 60))
    _ignar(sc, 250, 172, light=(0.95, 0.9, 0.9))
    sc.vignette(0.45)
    return sc


# ---- the Storm Steppe ---------------------------------------------------------------------------------------------
def storm_bg(sc, frozen=False):
    sc.bands("2a3450" if not frozen else "3a3a44", "8a9ab0" if not frozen else "6a6a72", 0, 110, n=7)
    for k in range(5):                                            # racing cloud bands
        y = 16 + k * 16
        x0 = int(sc.rng.integers(-40, 200))
        sc.poly([(x0, y), (x0 + 160, y - 4), (x0 + 200, y + 3), (x0 + 30, y + 6)], (90, 100, 124) if not frozen else (110, 110, 116))
    sc.ridge(104, 4, "4a5a4a", 41, freq=0.6, rim="8a9a6a")
    sc.bands("8a9a58", "4a5a34", 108, 180, n=6)
    for _ in range(500):                                          # high grass strokes
        x, y = int(sc.rng.integers(0, W)), int(sc.rng.integers(112, H))
        sc.line(x, y, x + 1, y - 3, (170, 180, 100) if sc.rng.random() < 0.5 else (90, 110, 60))


def storm_intro_01():
    """Endless high grass under a racing sky, standing stones, tent-cities, riders on grey horses."""
    sc = Scene(111)
    storm_bg(sc)
    for x in (40, 52, 64, 280):
        sc.rect(x, 90, x + 6, 114, (90, 90, 96))
        sc.rect(x, 90, x + 1, 114, (150, 150, 156))
    for x in range(120, 260, 16):                                # tent city
        sc.poly([(x, 112), (x + 7, 100), (x + 14, 112)], (200, 190, 170))
        sc.line(x + 7, 100, x + 7, 96, (90, 70, 50))
    for k, x in enumerate((70, 180, 240)):
        sc.disc(x, 150, 8, (150, 150, 156), squash=0.5)
        sc.rect(x - 7, 150, x - 5, 160, (120, 120, 126))
        sc.rect(x + 4, 150, x + 6, 160, (120, 120, 126))
        sc.rect(x + 6, 140, x + 9, 150, (150, 150, 156))
        sc.rect(x - 1, 138, x + 2, 146, (60, 70, 110))
        sc.disc(x, 136, 2, (200, 160, 130))
    sc.vignette(0.35)
    return sc


def storm_intro_02():
    """A frozen, motionless sky. Armoured earth spirits climbing the plateau edge; at their head Gorrath, a square hole in his chest."""
    sc = Scene(112)
    storm_bg(sc, frozen=True)
    sc.poly([(0, 130), (320, 120), (320, 180), (0, 180)], (90, 74, 56))
    for x in (40, 90, 250, 290):
        sc.put("golem", x, 170, light=GREYL)
    sc.put("gorrath", 166, 182, light=(0.85, 0.85, 0.9))
    sc.vignette(0.45)
    return sc


def storm_herald_01():
    """Gorrath breaking apart on the ridge into boulders that keep rolling, then stop; the carved stone heart cracks."""
    sc = Scene(113)
    storm_bg(sc, frozen=False)
    sc.put("gorrath", 150, 176, light=(0.9, 0.88, 0.85), pose=death_pose("gorrath", 5))
    for x, y, r in ((60, 166, 8), (90, 172, 6), (230, 170, 9), (262, 174, 5), (200, 176, 4)):
        sc.disc(x, y, r, (140, 110, 74))
        sc.disc(x - r // 3, y - r // 3, max(1, r // 3), (180, 150, 104))
    sc.particles(120, [(200, 200, 210), (160, 160, 170)], 60, 170, 80, 240)
    sc.vignette(0.4)
    return sc


def _rider(sc, x, feet, name="kaela", lance=True, light=(1, 1, 1), grey=(150, 150, 156), rear=False):
    """A rider on a grey horse. The horse is drawn here with the kit; the rider is the hero's sprite cut at the
    hips and set into the saddle, with the near leg drawn down the horse's flank."""
    import creatures
    from kit import Sprite, ramp
    s = Sprite(92, 70)
    G = ramp("a4a4ac", spread=0.5)
    M = ramp("3e3e48")
    hoof = ramp("2a2a30")
    f = 66                                                   # hooves
    lift = 6 if rear else 0
    # far legs, darker
    s.part(s.capsule(24, 36, 20, 50, 3.4, 2.6), G, bias=-0.3)
    s.part(s.capsule(20, 50, 22, f - 2, 2.4, 2.0), G, bias=-0.3, edge=False)
    s.part(s.capsule(60, 38, 66, 48 - lift, 3.2, 2.4), G, bias=-0.3)
    s.part(s.capsule(66, 48 - lift, 64, f - 2 - lift, 2.2, 1.8), G, bias=-0.3, edge=False)
    # tail
    s.part(s.poly([(18, 26), (6, 30), (2, 48), (8, 44), (12, 36), (20, 32)]), M)
    # body
    s.part(s.ellipse(42, 33, 25, 11), G)
    s.part(s.ellipse(22, 32, 9, 9), G)
    # neck and head
    s.part(s.poly([(56, 30), (60, 18), (68, 8), (76, 8), (72, 20), (68, 36)]), G)
    s.part(s.poly([(68, 6), (84, 14), (86, 20), (80, 22), (70, 16)]), G)
    s.part(s.poly([(66, 4), (69, 0), (71, 5)]), G)
    s.part(s.poly([(66, 4), (58, 16), (54, 28), (58, 26), (64, 14), (70, 6)]), M)
    s.px(76, 11, (20, 20, 24))
    s.px(84, 18, (40, 40, 46))
    # near legs, with knees
    s.part(s.capsule(28, 38, 30, 52, 3.8, 2.8), G)
    s.part(s.capsule(30, 52, 26, f - 2, 2.6, 2.2), G, edge=False)
    s.part(s.capsule(58, 38, 60, 52 - lift, 3.4, 2.6), G)
    s.part(s.capsule(60, 52 - lift, 60, f - 2 - lift, 2.4, 2.0), G, edge=False)
    for hx_, hy in ((22, f), (64, f - lift), (26, f), (60, f - lift)):
        s.fill(s.rect(hx_ - 2, hy - 3, hx_ + 2, hy), hoof[1])
    # saddle cloth and the near leg of the rider
    s.part(s.poly([(36, 22), (52, 22), (54, 34), (38, 36)]), ramp("4a5a8a"), flat=True)
    s.part(s.capsule(46, 26, 50, 38, 3.4, 3.0), ramp("2e2c36"))
    s.part(s.capsule(50, 38, 47, 47, 2.8, 2.4), ramp("2a2a30"), edge=False)
    s.ink()
    arr = np.asarray(s.image()).astype(np.float32)
    arr[..., :3] *= np.array(light, np.float32)
    x0, y0 = int(x - 46), int(feet - f)
    r = creatures.CREATURES[name]()
    ri = np.asarray(r.image()).astype(np.float32)[:50]
    ri[..., :3] *= np.array(light, np.float32)
    sc._paste(arr[..., :3], arr[..., 3] / 255, x0, y0)
    sc._paste(ri[..., :3], ri[..., 3] / 255, x0 + 46 - r.w // 2 + 2, y0 + 26 - 44)


def storm_herald_02():
    """Kaela Stormrider bursting out of the dust on her grey stallion Thunderclap, lightning lance crackling."""
    sc = Scene(114)
    storm_bg(sc)
    for k in range(14):
        sc.glow(60 + k * 12, 150 - (k % 3) * 6, 20, (170, 160, 140), 0.55)
    _rider(sc, 170, 170)
    sc.line(200, 84, 214, 62, (240, 240, 255))
    sc.line(214, 62, 210, 54, (240, 240, 255))
    sc.glow(210, 70, 12, (200, 200, 255), 0.6)
    sc.vignette(0.4)
    return sc


def storm_herald_03():
    """Kaela reining in beside the player's towers, looking back at Highwind."""
    sc = Scene(115)
    storm_bg(sc)
    for x in (40, 96):
        sc.tower(x, 160, 14, 44, (120, 116, 110), (180, 176, 166), win=(150, 170, 255))
        sc.glow(x + 7, 112, 10, (150, 170, 255), 0.6)
    for x in range(230, 300, 12):
        sc.poly([(x, 112), (x + 6, 102), (x + 12, 112)], (170, 160, 140))
    _rider(sc, 170, 170, light=(0.95, 0.95, 1.0))
    sc.vignette(0.4)
    return sc


def storm_warden_01():
    """The black solid cloud shattering, frozen lightning falling like glass. Rain. Riders lifting their faces to it."""
    sc = Scene(116)
    storm_bg(sc)
    sc.put("thunderhead", 170, 150, light=(0.8, 0.8, 0.9), pose=death_pose("thunderhead", 4))
    for _ in range(26):                                          # lightning falling like glass
        x, y = sc.rng.uniform(40, 300), sc.rng.uniform(20, 140)
        sc.line(x, y, x + 2, y + 6, (230, 230, 255))
    for _ in range(300):
        x, y = int(sc.rng.integers(0, W)), int(sc.rng.integers(0, H - 4))
        sc.line(x, y, x - 1, y + 3, (160, 170, 200))
    for x in (40, 290):
        sc.put("soldier", x, 176, light=(0.8, 0.85, 0.95))
    sc.vignette(0.4)
    return sc


def storm_warden_02():
    """Aurath, a rider-shape of cloud and lightning, flickering, bowing over the towers."""
    sc = Scene(117)
    storm_bg(sc)
    import creatures
    import portraits
    fr = portraits.freed(creatures.CREATURES["thunderhead"](anim.death(2, 8, "float", "thunderhead"), 30), portraits.STORM)
    arr = np.asarray(fr.image()).astype(np.float32)
    arr[..., :3] = arr[..., :3] * 0.6 + np.array((150, 160, 200)) * 0.4          # cloud, not black: freed and pale
    sc._paste(arr[..., :3], arr[..., 3] / 255 * 0.9, int(180 - fr.w // 2), int(170 - (fr.bh - 4 + fr.pad)))
    for x in (40, 90, 270):
        sc.tower(x, 170, 12, 36, (120, 116, 110), (180, 176, 166), win=(150, 170, 255))
    sc.vignette(0.4)
    return sc


def storm_warden_03():
    """The tent-city of Aurvanis folded onto horses; a sea of riders heading for the horizon; Kaela at the back, looking back."""
    sc = Scene(118)
    storm_bg(sc)
    for x in range(140, 300, 10):                                # empty tent poles
        sc.line(x, 112, x, 100, (90, 70, 50))
    for k in range(40):
        x = 20 + k * 7
        y = 120 + (k % 4) * 3
        sc.disc(x, y, 3, (140, 140, 146), squash=0.5)
        sc.rect(x - 1, y - 5, x + 1, y - 1, (60, 70, 100))
    _rider(sc, 220, 172)
    sc.vignette(0.4)
    return sc


# ---- the Deepwood ---------------------------------------------------------------------------------------------------
def nature_bg(sc, dark=False):
    sc.bands("0e1a12" if dark else "1a3420", "2a4a2a" if dark else "6a8a4a", 0, 180, n=8)
    for i, (x, w) in enumerate(((10, 30), (80, 40), (170, 34), (250, 46))):    # giant trunks
        col = (34 + i * 4, 28, 22) if not dark else (24, 20, 18)
        sc.rect(x, 0, x + w, 180, col)
        sc.rect(x, 0, x + 2, 180, (70, 56, 40) if not dark else (40, 34, 30))
        for y in range(10, 180, 14):
            sc.line(x + 6, y, x + 8, y + 8, (24, 20, 16))
    for y0, x0, x1 in ((50, 40, 80), (40, 120, 170), (64, 204, 250)):         # rope bridges
        for x in range(x0, x1):
            y = int(y0 + 6 * math.sin((x - x0) / (x1 - x0) * math.pi))
            sc.c[y, x] = (120, 90, 60)
            if x % 4 == 0:
                sc.line(x, y, x, y - 5, (90, 70, 50))
    sc.bands("2a3a20", "121a10", 150, 180, n=4)
    if not dark:
        for _ in range(200):                                     # glow-moss along the roots like streets
            x, y = int(sc.rng.integers(0, W)), int(sc.rng.integers(140, H))
            sc.c[y, x] = (150, 240, 120) if sc.rng.random() < 0.5 else (90, 180, 90)
        sc.fog(140, 170, (120, 200, 110), 0.25)


def nature_intro_01():
    """Giant trees, rope bridges, glow-moss lighting the roots like streets, Deepwood archers."""
    sc = Scene(121)
    nature_bg(sc)
    for x in (130, 220, 300):
        sc.put("elf", x, 170, light=(0.85, 1.0, 0.85))
    sc.vignette(0.45)
    return sc


def nature_intro_02():
    """The glow-moss going dark row by row; pale violet ghost-lights drifting; the Pale Vesper singing."""
    sc = Scene(122)
    nature_bg(sc)
    dark = sc.xs < 200
    sc.c[dark] *= 0.5
    sc.put("vesper", 140, 176, light=(0.85, 0.85, 0.95))
    sc.vignette(0.5)
    return sc


def nature_herald_01():
    """The Pale Vesper falling among the roots, her ghost-choir scattering like moths."""
    sc = Scene(123)
    nature_bg(sc, dark=True)
    sc.put("vesper", 160, 176, light=(0.85, 0.85, 0.95), pose=death_pose("vesper", 3))
    for _ in range(18):
        x, y = sc.rng.uniform(40, 300), sc.rng.uniform(20, 120)
        sc.disc(x, y, 2, (176, 150, 226))
        sc.glow(x, y, 6, (176, 150, 226), 0.5)
    sc.vignette(0.5)
    return sc


def _face_close(sc, gid, x0=112, y0=42, light=(1, 1, 1), grey=False):
    import portraits
    im = portraits.portrait(gid)
    arr = np.asarray(im).astype(np.float32)
    arr[..., :3] *= np.array(light, np.float32)
    if grey:
        lum = arr[..., :3].mean(-1, keepdims=True)
        arr[..., :3] = arr[..., :3] * 0.4 + lum * 0.6
    sc._paste(arr[..., :3], arr[..., 3] / 255, x0, y0)


def nature_herald_02():
    """Close on the Vesper's face, the grey light leaving her eyes; for a moment she looks like herself."""
    sc = Scene(124)
    nature_bg(sc, dark=True)
    sc.c *= 0.6
    _face_close(sc, "pale_vesper", 112, 42)
    sc.vignette(0.6)
    return sc


def nature_herald_03():
    """Sylvaine Thornwhisper amid a ring of fallen hollow things, a pale leafing longbow in her hands. She lowers the bow."""
    sc = Scene(125)
    nature_bg(sc)
    for x in (90, 120, 210, 240):
        sc.put("ghost", x, 176, light=(0.5, 0.5, 0.55), pose=death_pose("ghost", 6))
    sc.put("sylvaine", 166, 174, light=(0.95, 1.0, 0.9), rim=(180, 255, 150))
    sc.vignette(0.45)
    return sc


def nature_herald_04():
    """Sylvaine at the edge of a tower platform, arrow on the string."""
    sc = Scene(126)
    nature_bg(sc)
    sc.rect(120, 140, 240, 150, (90, 70, 50))
    sc.rect(120, 140, 240, 141, (150, 120, 80))
    sc.put("elf", 180, 140, light=(0.95, 1.0, 0.9), pose=attack_pose("elf", 3))
    sc.put("sylvaine", 150, 140, light=(0.95, 1.0, 0.9), rim=(180, 255, 150))
    sc.vignette(0.45)
    return sc


def nature_warden_01():
    """The Broodmother collapsing; grey bark peeling away to reveal Elowen, bent, with white-blossom hair."""
    sc = Scene(127)
    nature_bg(sc, dark=True)
    sc.put("elder_broodmother", 140, 200, light=(0.8, 0.8, 0.82), pose=death_pose("elder_broodmother", 4), alpha=0.85)
    sc.glow(220, 130, 40, (200, 255, 180), 0.5)
    sc.put("elowen_warden", 222, 170, light=(1.0, 1.0, 0.95), rim=(220, 255, 200))
    sc.vignette(0.5)
    return sc


def nature_warden_02():
    """Elowen pressing a single glowing seed into Sylvaine's hand."""
    sc = Scene(128)
    nature_bg(sc)
    sc.put("elowen_warden", 178, 170, flip=True)
    sc.put("sylvaine", 140, 170)
    sc.glow(160, 140, 10, (180, 255, 120), 0.9)
    sc.disc(160, 140, 1, (240, 255, 220))
    sc.vignette(0.5)
    return sc


def nature_warden_03():
    """Deepwood folk climbing up and away along the crown of the great tree; Sylvaine last, a small green light in her hand."""
    sc = Scene(129)
    nature_bg(sc)
    for k in range(12):
        x = 60 + k * 18
        y = 150 - k * 9
        sc.rect(x, y - 8, x + 3, y, (60, 80, 50))
        sc.rect(x + 1, y - 10, x + 3, y - 8, (220, 190, 150))
    sc.put("sylvaine", 46, 176)
    sc.glow(56, 140, 8, (180, 255, 120), 0.9)
    sc.vignette(0.5)
    return sc


# ---- the Frostmere --------------------------------------------------------------------------------------------------
def water_bg(sc, fire=False):
    sc.bands("0a1424", "2a4a6a", 0, 110, n=7)
    sc.stars(60, 60)
    for k in range(3):                                            # aurora
        for x in range(W):
            y = int(30 + k * 10 + 10 * math.sin(x / 40 + k))
            for d in range(8):
                if 0 <= y + d < H:
                    sc.c[y + d, x] = sc.c[y + d, x] * 0.6 + np.array((80, 220, 170) if k != 1 else (90, 180, 230)) * 0.4 * (1 - d / 8)
    sc.ridge(104, 4, "1a2a3a", 51, freq=0.6, rim="6a8aa0")
    sc.bands("c8dce8", "6a8aa0", 108, 180, n=6)                   # the frozen lake
    for _ in range(60):
        x, y = int(sc.rng.integers(0, W)), int(sc.rng.integers(110, H))
        sc.line(x, y, x + int(sc.rng.integers(6, 20)), y + int(sc.rng.integers(-2, 3)), (230, 244, 250))
    if fire:
        for x in range(0, W, 8):
            flame(sc, x, 120, 10 + (x * 5) % 9)


def water_intro_01():
    """A vast frozen lake, stilt towns, pearl-white harbours, aurora overhead."""
    sc = Scene(131)
    water_bg(sc)
    for x in (40, 70, 230, 260, 290):                            # stilt towns
        sc.rect(x, 96, x + 20, 106, (90, 80, 76))
        sc.poly([(x - 2, 96), (x + 10, 88), (x + 22, 96)], (160, 150, 150))
        for k in range(x + 2, x + 20, 6):
            sc.rect(k, 106, k + 1, 116, (60, 56, 54))
    sc.vignette(0.4)
    return sc


def water_intro_02():
    """Burning runners skating across the ice, leaving black water behind; at their head Ashwick, a boy of white embers."""
    sc = Scene(132)
    water_bg(sc)
    for k, x in enumerate((60, 120, 210, 260)):
        y = 150 + (k % 2) * 10
        sc.poly([(0, y + 2), (x, y), (x, y + 4), (0, y + 6)], (10, 20, 30))
        sc.put("orb_fire", x, y, light=(1, 1, 1))
    sc.put("ashwick", 170, 174)
    sc.vignette(0.45)
    return sc


def water_herald_01():
    """Ashwick stumbling in the reeds, embers scattering, the satchel falling open: old letters with the Concord seal blow away."""
    sc = Scene(133)
    water_bg(sc)
    for _ in range(300):
        x, y = int(sc.rng.integers(0, W)), int(sc.rng.integers(120, H))
        sc.line(x, y, x + 1, y - 8, (110, 120, 80))
    sc.put("ashwick", 150, 170, pose=death_pose("ashwick", 3))
    for k in range(9):                                           # letters blowing away
        x, y = 190 + k * 12, 120 - k * 7
        sc.rect(x, y, x + 6, y + 4, (230, 220, 190))
        sc.c[y + 2, x + 3] = (180, 40, 40)
    sc.vignette(0.45)
    return sc


def water_herald_02():
    """A tower of ice in a ring of fire; inside, Mirelle, pearls on everything, blind eyes glowing teal, holding her ice staff."""
    sc = Scene(134)
    water_bg(sc, fire=True)
    sc.poly([(120, 172), (130, 40), (160, 20), (190, 40), (200, 172)], (170, 214, 230))
    sc.poly([(126, 170), (136, 46), (160, 28), (184, 46), (194, 170)], (120, 170, 196))
    sc.line(132, 160, 140, 46, (240, 250, 255))
    sc.glow(160, 140, 30, (120, 240, 240), 0.4)
    sc.put("mirelle", 160, 168, light=(0.85, 0.95, 1.0), rim=(150, 255, 255))
    sc.vignette(0.45)
    return sc


def water_herald_03():
    """Mirelle stepping out onto the frost, barefoot."""
    sc = Scene(135)
    water_bg(sc)
    sc.put("mirelle", 160, 172, rim=(150, 255, 255), pose=walk_pose("mirelle", 2))
    for x in range(140, 180, 4):
        sc.c[174, x] = (250, 255, 255)
    sc.vignette(0.45)
    return sc


def water_warden_01():
    """The ice-eel collapsing; drowned bronze bells rising out of the water and ringing; Thalassa rising from the lake."""
    sc = Scene(136)
    water_bg(sc)
    sc.put("tidal_leviathan", 110, 200, light=(0.85, 0.9, 0.95), pose=death_pose("tidal_leviathan", 4))
    for x, y in ((210, 90), (230, 70), (260, 100), (196, 60)):
        sc.poly([(x - 2, y), (x + 2, y), (x + 4, y + 6), (x - 4, y + 6)], (196, 150, 70))
        sc.glow(x, y + 3, 7, (255, 220, 140), 0.4)
    sc.glow(240, 130, 40, (140, 240, 240), 0.5)
    sc.put("thalassa_warden", 240, 172, rim=(180, 255, 255))
    sc.vignette(0.45)
    return sc


def water_warden_02():
    """Thalassa looking down at the towers and heroes."""
    sc = Scene(137)
    water_bg(sc)
    sc.c *= 0.85
    _face_close(sc, "thalassa", 140, 30, light=(0.95, 1.0, 1.0))
    for x in (30, 70, 250, 290):
        sc.tower(x, 176, 12, 34, (150, 170, 190), (220, 236, 246), win=(120, 240, 240))
    sc.vignette(0.45)
    return sc


def water_warden_03():
    """Mirelle alone on the shore with her ice staff, blind eyes glowing; behind her the fleet of Pearlhaven sails west."""
    sc = Scene(138)
    water_bg(sc)
    for k, x in enumerate(range(20, 160, 30)):
        y = 100 + (k % 2) * 4
        sc.poly([(x, y), (x + 18, y), (x + 14, y + 4), (x + 4, y + 4)], (90, 70, 50))
        sc.poly([(x + 8, y), (x + 8, y - 14), (x + 16, y - 2)], (230, 226, 214))
    for x in range(200, 320, 12):
        sc.glow(x, 96, 10, (220, 220, 226), 0.5)
    sc.put("mirelle", 230, 172, rim=(150, 255, 255))
    sc.vignette(0.5)
    return sc


# ---- the Canyon -----------------------------------------------------------------------------------------------------
def earth_bg(sc):
    """Red rock canyon: two cliff walls cut into stepped terraces of houses, strata, a far mesa in the gap."""
    sc.bands("6a3a2a", "e0a060", 0, 80, n=6)
    sc.ridge(78, 4, "b07048", 301, freq=0.6, jag=1.0)
    rng = np.random.default_rng(302)
    for i, (x0, x1, top) in enumerate(((0, 116, 18), (204, 320, 12))):
        col, lit, dark = (hx("8a4a2a"), hx("c07a48"), hx("5a2e1c")) if i == 0 else (hx("7a4026"), hx("b06c40"), hx("4e281a"))
        inner = x1 if i == 0 else x0                              # the edge that faces the canyon
        step = 1 if i == 0 else -1
        for k, y in enumerate(range(top, 170, 22)):               # each terrace steps back from the gap
            ex = inner - step * k * 5
            lo, hi = (x0, ex) if i == 0 else (ex, x1)
            sc.rect(lo, y, hi, 180, col)
            sc.rect(lo, y, hi, y + 2, lit)                        # lit ledge
            for sy in (y + 8, y + 15):                            # strata
                sc.rect(lo, sy, hi, sy + 1, dark)
            for x in range(lo + 4 + (k % 2) * 6, hi - 10, 16):    # houses on the ledge
                hh = 8 + int(rng.integers(0, 4))
                sc.rect(x, y - hh, x + 10, y, lit)
                sc.rect(x + 7, y - hh, x + 10, y, col)
                sc.rect(x, y - hh - 1, x + 10, y - hh, (220, 160, 100))
                sc.rect(x + 3, y - 5, x + 5, y, (255, 190, 90) if rng.random() < 0.5 else (40, 20, 14))
            edge = (hi - 2, hi) if i == 0 else (lo, lo + 2)
            sc.rect(edge[0], y, edge[1], y + 22, lit if i == 0 else dark)
    sc.bands("a06040", "5a3020", 80, 180, n=6, mask=(sc.xs >= 116) & (sc.xs < 204))
    sc.bands("6a3a24", "3a2014", 150, 180, n=4)
    sc.particles(30, [(240, 200, 150)], 20, 150)


def _stone_face(sc, x, y, s=1.0):
    sc.rect(int(x), int(y), int(x + 26 * s), int(y + 36 * s), (120, 70, 40))
    sc.rect(int(x), int(y), int(x + 26 * s), int(y + 4 * s), (160, 100, 60))
    for ex in (6, 16):
        sc.rect(int(x + ex * s), int(y + 12 * s), int(x + (ex + 5) * s), int(y + 15 * s), (50, 26, 16))
    sc.rect(int(x + 10 * s), int(y + 16 * s), int(x + 14 * s), int(y + 24 * s), (100, 56, 30))
    sc.rect(int(x + 6 * s), int(y + 27 * s), int(x + 20 * s), int(y + 29 * s), (50, 26, 16))


def earth_intro_01():
    """Red rock canyon, cliff cities in terraces, giant stone faces of old kings."""
    sc = Scene(141)
    earth_bg(sc)
    _stone_face(sc, 30, 40, 1.4)
    _stone_face(sc, 240, 34, 1.6)
    sc.put("dwarf", 160, 172, light=(1.05, 0.9, 0.8))
    sc.vignette(0.4)
    return sc


def earth_intro_02():
    """Storm spirits in armour pouring down the walls; above them on a thunderbird of black cloud, Vholt with a crown of lightning."""
    sc = Scene(142)
    earth_bg(sc)
    for x, y in ((40, 100), (70, 130), (250, 90), (280, 140)):
        sc.put("orb_storm", x, y, light=GREYL)
    sc.put("vholt", 170, 120)
    sc.vignette(0.45)
    return sc


def earth_herald_01():
    """The black thunderbird crashing on the terraces; Vholt crawling free; Kaela stands over him with her lance."""
    sc = Scene(143)
    earth_bg(sc)
    sc.put("vholt", 140, 182, pose=death_pose("vholt", 2), light=(0.85, 0.85, 0.9))
    sc.particles(100, [(160, 120, 90), (120, 90, 70)], 120, 180, 60, 240)
    sc.put("kaela", 240, 174, flip=True, light=(1.0, 0.95, 0.9))
    sc.vignette(0.45)
    return sc


def earth_herald_02():
    """Vholt's face, the grey light flickering out of his eyes as he looks up."""
    sc = Scene(144)
    earth_bg(sc)
    sc.c *= 0.6
    _face_close(sc, "vholt", 112, 42)
    sc.vignette(0.6)
    return sc


def earth_herald_03():
    """Gorrim Stonebeard, a carved stone door for a shield, standing in front of exhausted soldiers."""
    sc = Scene(145)
    earth_bg(sc)
    for x in (100, 120, 220, 240):
        sc.put("soldier", x, 168, light=(0.75, 0.72, 0.7), pose=death_pose("soldier", 1))
    sc.put("gorrim", 170, 174, rim=(255, 200, 140))
    sc.vignette(0.45)
    return sc


def earth_herald_04():
    """Gorrim hefting the door-shield onto his back."""
    sc = Scene(146)
    earth_bg(sc)
    sc.put("gorrim", 160, 174, flip=True, rim=(255, 200, 140), pose=walk_pose("gorrim", 1))
    sc.vignette(0.45)
    return sc


def earth_warden_01():
    """The Titan crashing down; grey lichen falling from its eyes; amber geode eyes opening. Orrok."""
    sc = Scene(147)
    earth_bg(sc)
    import creatures
    import portraits
    fr = portraits.freed(creatures.CREATURES["mountain_titan"](anim.death(3, 8, "titan", "mountain_titan"), 64), portraits.AMBER)
    arr = np.asarray(fr.image()).astype(np.float32)
    sc._paste(arr[..., :3], arr[..., 3] / 255, int(160 - fr.w // 2), int(214 - (fr.bh - 4 + fr.pad)))
    sc.particles(60, [(150, 152, 154), (186, 188, 188)], 40, 170, 100, 240)
    sc.vignette(0.45)
    return sc


def earth_warden_02():
    """Orrok, enormous, looking at the towers; the first thing he has said in a thousand years."""
    sc = Scene(148)
    earth_bg(sc)
    _face_close(sc, "orrok", 100, 20, light=(1.0, 0.95, 0.9))
    for x in (30, 250, 290):
        sc.tower(x, 176, 12, 30, (120, 80, 50), (180, 130, 80), win=(255, 200, 100))
    sc.vignette(0.45)
    return sc


def earth_warden_03():
    """The great stone doors of Grundhallow closing; Gorrim braiding an iron ring into his beard."""
    sc = Scene(149)
    earth_bg(sc)
    sc.rect(100, 30, 220, 160, (50, 30, 20))
    sc.rect(104, 34, 158, 160, (130, 90, 60))
    sc.rect(162, 34, 216, 160, (120, 84, 56))
    sc.rect(158, 34, 162, 160, (20, 12, 10))
    for y in range(50, 160, 24):
        sc.rect(108, y, 154, y + 2, (90, 60, 40))
        sc.rect(166, y, 212, y + 2, (84, 56, 36))
    sc.put("gorrim", 260, 176, flip=True)
    sc.vignette(0.5)
    return sc


# ---- the Hollow Rift ----------------------------------------------------------------------------------------------------
def void_bg(sc, crack=True):
    sc.bands("06040c", "2a1a40", 0, 120, n=7)
    sc.ridge(116, 4, "1e1430", 61, freq=1.0, rim="4a3070")
    sc.bands("3a2860", "160e24", 118, 180, n=5)
    sc.particles(400, [(110, 80, 160), (80, 56, 120), (140, 110, 190)], 118, 180)
    for x, y, w in ((40, 90, 30), (110, 70, 22), (250, 80, 34)):    # floating stone steps
        sc.rect(x, y, x + w, y + 6, (50, 40, 64))
        sc.rect(x, y, x + w, y + 1, (100, 84, 130))
        sc.poly([(x + 4, y + 6), (x + w - 4, y + 6), (x + w // 2, y + 14)], (36, 28, 48))
    if crack:
        sc.line(200, 116, 206, 106, (220, 190, 255))
        sc.line(206, 106, 204, 96, (220, 190, 255))
        sc.glow(204, 108, 10, (180, 140, 255), 0.5)


def void_intro_01():
    """The Hollow Rift: starless sky, violet grass, floating stone steps, and far off the hairline Crack."""
    sc = Scene(151)
    void_bg(sc)
    sc.vignette(0.5)
    return sc


def _waystation(sc):
    sc.rect(80, 70, 240, 160, (40, 34, 46))
    sc.rect(80, 70, 240, 72, (80, 70, 90))
    sc.poly([(70, 72), (160, 40), (250, 72)], (30, 26, 36))
    for x in (100, 130, 190, 220):
        sc.rect(x, 90, x + 4, 96, (60, 56, 64))
    sc.rect(158, 90, 162, 96, (200, 160, 80))
    sc.glow(160, 92, 12, (255, 255, 240), 0.7)
    sc.c[92, 160] = (255, 255, 255)


def void_intro_02():
    """An empty waystation, every lantern cold except one, burning a small white flame. Tamsin staring at it."""
    sc = Scene(152)
    void_bg(sc, crack=False)
    _waystation(sc)
    sc.put("tamsin", 190, 170, flip=True, light=(0.8, 0.8, 0.9), rim=(255, 255, 240))
    sc.vignette(0.55)
    return sc


def void_intro_03():
    """Tamsin turning away from the lantern, leaving it burning."""
    sc = Scene(153)
    void_bg(sc, crack=False)
    _waystation(sc)
    sc.put("tamsin", 210, 172, light=(0.8, 0.8, 0.9), pose=walk_pose("tamsin", 3))
    sc.vignette(0.55)
    return sc


def void_herald_01():
    """The thicket-woman falling apart on the floating steps, grey flowers wilting, black thorns crumbling."""
    sc = Scene(154)
    void_bg(sc)
    sc.rect(80, 150, 240, 158, (50, 40, 64))
    sc.put("mother_briar", 160, 152, pose=death_pose("mother_briar", 4))
    sc.vignette(0.5)
    return sc


def void_herald_02():
    """Corvin the Uncrowned cutting himself free with a black glass blade full of stars, hood back, silver hair."""
    sc = Scene(155)
    void_bg(sc)
    thorn, tip = (34, 26, 40), (70, 56, 84)
    for k in range(9):                                              # a thorn cage, cut open on the right
        a = math.pi * (0.55 + k / 8 * 1.05)
        x0, y0 = 160 + math.cos(a) * 40, 172
        x1, y1 = 160 + math.cos(a) * 30, 96 + abs(k - 4) * 4
        for w in range(-1, 2):
            sc.line(x0 + w, y0, x1 + w, y1, thorn)
        for j in range(5):                                          # hooked thorns along each stem
            fx = x0 + (x1 - x0) * (j + 0.5) / 5
            fy = y0 + (y1 - y0) * (j + 0.5) / 5
            d = -1 if j % 2 else 1
            sc.poly([(fx, fy), (fx + d * 6, fy - 3), (fx, fy - 3)], tip)
    for (x, y, l) in ((196, 120, 18), (204, 140, 14), (190, 156, 20)):   # cut stems falling away
        sc.line(x, y, x + l, y + 6, thorn)
        sc.line(x, y + 1, x + l, y + 7, thorn)
    for k in range(3):                                              # starlit slashes from the cut
        sc.line(178 + k * 6, 104 + k * 18, 214 + k * 4, 96 + k * 22, (210, 200, 255))
        sc.glow(196 + k * 5, 102 + k * 20, 8, (180, 160, 255), 0.6)
    sc.put("corvin", 160, 172, pose=attack_pose("corvin", 5), rim=(200, 180, 255))
    sc.vignette(0.5)
    return sc


def void_herald_03():
    """Corvin standing, looking at the player."""
    sc = Scene(156)
    void_bg(sc)
    _face_close(sc, "corvin", 112, 40)
    sc.vignette(0.55)
    return sc


def void_warden_01():
    """The Hollow King breaking into two shades; one dissolves, the other becomes Nyxara, a starfield for a face, a broken crown in hand."""
    sc = Scene(157)
    void_bg(sc)
    sc.put("hollow_shade", 100, 168, pose=death_pose("hollow_shade", 4))
    sc.glow(210, 120, 40, (180, 140, 255), 0.4)
    sc.put("nyxara_queen", 210, 170, rim=(220, 200, 255))
    sc.vignette(0.5)
    return sc


def void_warden_02():
    """Nyxara looking past the player toward the Crack, the stars in her face moving."""
    sc = Scene(158)
    void_bg(sc)
    _face_close(sc, "nyxara", 112, 42)
    sc.vignette(0.55)
    return sc


def void_warden_03():
    """Umbrael's great telescope turning one last time to face the Crack, then toppling slowly."""
    sc = Scene(159)
    void_bg(sc)
    stone, slit, dark = (52, 44, 66), (84, 74, 104), (30, 26, 40)
    sc.rect(54, 92, 126, 170, stone)                                 # the observatory drum
    sc.rect(54, 92, 60, 170, slit)
    sc.rect(118, 92, 126, 170, dark)
    for y in range(100, 170, 10):
        sc.rect(54, y, 126, y + 1, dark)
    sc.poly([(48, 92), (90, 66), (132, 92)], (64, 54, 80))           # split dome, opened toward the Crack
    sc.poly([(48, 92), (90, 66), (92, 70), (54, 92)], (96, 86, 120))
    sc.rect(84, 70, 96, 92, dark)
    # the brass tube, rings and lens, tilted past its stop and starting to fall
    a = -0.62
    def at(d, o=0.0):
        return 90 + math.cos(a) * d - math.sin(a) * o, 86 + math.sin(a) * d + math.cos(a) * o
    for d0, d1, r, col in ((-10, 124, 7, (150, 110, 56)), (-10, 124, 5, (196, 150, 76)), (-10, 124, 2, (230, 190, 110))):
        p = [at(d0, -r), at(d1, -r * 0.8), at(d1, r * 0.8), at(d0, r)]
        sc.poly(p, col)
    for d in (10, 46, 82, 112):
        p = [at(d, -8), at(d + 4, -8), at(d + 4, 8), at(d, 8)]
        sc.poly(p, (110, 76, 36))
    lx, ly = at(126)
    sc.disc(lx, ly, 7, (90, 66, 36))
    sc.disc(lx, ly, 5, (150, 170, 230))
    sc.disc(lx - 1, ly - 1, 2, (230, 240, 255))
    sc.glow(lx, ly, 10, (180, 190, 255), 0.5)
    for (x, y) in ((136, 166), (148, 170), (126, 172), (40, 168)):   # stones falling from the drum
        sc.poly([(x, y), (x + 6, y - 5), (x + 10, y)], stone)
    sc.particles(40, [(90, 80, 110), (60, 54, 80)], 140, 176, 30, 160)
    sc.vignette(0.5)
    return sc


CINEMATICS.update({
    "ember_intro": [ember_intro_01, ember_intro_02, ember_intro_03],
    "ember_herald": [ember_herald_01, ember_herald_02, ember_herald_03],
    "ember_warden": [ember_warden_01b, ember_warden_02, ember_warden_03],
    "storm_intro": [storm_intro_01, storm_intro_02],
    "storm_herald": [storm_herald_01, storm_herald_02, storm_herald_03],
    "storm_warden": [storm_warden_01, storm_warden_02, storm_warden_03],
    "nature_intro": [nature_intro_01, nature_intro_02],
    "nature_herald": [nature_herald_01, nature_herald_02, nature_herald_03, nature_herald_04],
    "nature_warden": [nature_warden_01, nature_warden_02, nature_warden_03],
    "water_intro": [water_intro_01, water_intro_02],
    "water_herald": [water_herald_01, water_herald_02, water_herald_03],
    "water_warden": [water_warden_01, water_warden_02, water_warden_03],
    "earth_intro": [earth_intro_01, earth_intro_02],
    "earth_herald": [earth_herald_01, earth_herald_02, earth_herald_03, earth_herald_04],
    "earth_warden": [earth_warden_01, earth_warden_02, earth_warden_03],
    "void_intro": [void_intro_01, void_intro_02, void_intro_03],
    "void_herald": [void_herald_01, void_herald_02, void_herald_03],
    "void_warden": [void_warden_01, void_warden_02, void_warden_03],
})
