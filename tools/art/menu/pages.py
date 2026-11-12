"""Main menu and its pages as pixel-art mock-ups (design only).

    python3 tools/art/menu/pages.py --out DIR

Writes one 1920x1080 PNG per screen (00_main_menu.png .. 09_quit.png) and a contact sheet. The backdrop is a
calm dusk view of Solenne painted with the landing-art kit; the interface is drawn with ui.py at 960x540, x2.
"""
from __future__ import annotations

import argparse
import math
import os
import random
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tools", "art", "landing"))
import landing as L  # noqa: E402
import logo as LOGO  # noqa: E402
from ui import (UI, UW, UH, hx, INK, TEXT, DIM, GOLD, GOLD_HI, GOLD_LO, STONE, ELEM, font)  # noqa: E402

PF = "/mnt/project-files"
HEROES = [("tamsin", "Tamsin Reed", "Captain of the Lanternguard", None),
          ("brannoc", "Brannoc Emberhand", "Smith-Lord of the Reach", "fire"),
          ("kaela", "Kaela Stormrider", "Marshal of the Steppe", "storm"),
          ("sylvaine", "Sylvaine Thornwhisper", "Warden-Archer of the Deep", "nature"),
          ("mirelle", "Mirelle", "the Tide-Seer", "water"),
          ("gorrim", "Gorrim Stonebeard", "Shield of the Canyon", "earth"),
          ("corvin", "Corvin", "the Uncrowned, Ranger-King of the Rift", "void"),
          ("ignar", "Ignar", "the Cinder Warden", "fire"), ("aurath", "Aurath", "of the Storms", "storm"),
          ("elowen", "Elowen", "the Evergreen", "nature"), ("thalassa", "Thalassa", "of the Deep", "water"),
          ("orrok", "Orrok", "the Mountain", "earth"), ("nyxara", "Nyxara", "of the Hollow", "void"),
          ("ilyra", "Ilyra", "the Unbroken", None), ("seraphel", "Seraphel", "the Dawnblade", None),
          ("oswin", "Oswin", "the White Lantern", None)]
LANDS = [("Ember Reach", "fire"), ("Thunder Steppe", "storm"), ("Verdant Deep", "nature"),
         ("Frostmere", "water"), ("Sunscar Canyon", "earth"), ("Hollow Rift", "void")]


# =====================================================================================================
def backdrop():
    """Solenne at dusk from the road: the city and its six lit towers on the right, open sky on the left for
    the menu, a campfire watch on the ridge. Calm, no battle."""
    L.rng.seed(11)
    cv = L.Canvas()
    L.sky(cv)
    # a hairline crack far up in the sky: the Rift, only a promise of trouble
    x, y = 250.0, 14.0
    for i in range(60):
        x += L.rng.uniform(0.2, 1.4); y += L.rng.uniform(-0.6, 1.2)
        cv.rgb[int(y), int(x)] = L.col("d0a8ff"); cv.emit[int(y), int(x)] += L.col("a060ff") * 0.9
        if L.rng.random() < 0.15:
            cv.rgb[int(y) + 1, int(x)] = L.col("8a50d0")
    L.mountains(cv)
    towers, sun = L.solenne(cv)
    # gentle beams: the towers feed the Sunstone, no war yet
    sx, sy = sun
    for tx, ty, c in towers:
        n = int(math.hypot(sx - tx, sy - ty))
        for i in range(0, n, 2):
            t = i / n
            px, py = int(tx + (sx - tx) * t), int(ty + (sy - ty) * t)
            cv.rgb[py, px] = np.maximum(cv.rgb[py, px], c * 0.8)
            cv.emit[py, px] += c * 0.45
    cv.light(sx, 150, L.col("ffc860"), 170, 0.10, 0.0)
    top = L.ground(cv)

    def gy(x):
        return int(top[int(x)]) + 3
    # campfire watch on the ridge, facing the fire (soldiers come from the right, flipped)
    fx = 372
    fy = gy(fx) + 22
    D = dict(flip=True, rim=(L.col("ffb040"), -1.0), tint=(0.9, 0.82, 0.8))
    cv.creature("soldier", "idle", 1, fx + 30, fy + 2, **D)
    cv.creature("dwarf", "idle", 3, fx + 52, fy + 10, **D)
    cv.creature("elf", "idle", 2, fx - 30, fy + 4, rim=(L.col("ffb040"), 1.0), tint=(0.9, 0.82, 0.8))
    cv.creature("soldier", "idle", 4, fx - 54, fy + 12, rim=(L.col("ffb040"), 1.0), tint=(0.8, 0.74, 0.78))
    # the fire: logs and flame tongues
    cv.rgb[fy - 2:fy, fx - 7:fx + 8] = L.col("3a2216")
    cv.rgb[fy - 3, fx - 5:fx + 6] = L.col("5a3620")
    for i in range(70):
        t = L.rng.random()
        px = fx + L.rng.gauss(0, 1) * (1 - t) * 3.5
        py = fy - 3 - t * 16
        c = L.col("fff2c0") if t < 0.3 else (L.col("ffb040") if t < 0.65 else L.col("e0501e"))
        cv.rgb[int(py), int(px)] = c
        cv.emit[int(py), int(px)] += c * 1.2
    cv.light(fx, fy - 6, L.col("ff9a40"), 80, 0.30, 0.15)
    for i in range(24):  # sparks
        px, py = fx + L.rng.uniform(-10, 12), fy - 20 - L.rng.uniform(0, 40)
        cv.rgb[int(py), int(px)] = L.col("ffc860"); cv.emit[int(py), int(px)] += L.col("ff9030")
    # fireflies over the grass
    for i in range(40):
        px, py = L.rng.uniform(0, 640), L.rng.uniform(250, 340)
        cv.rgb[int(py), int(px)] = L.col("d8ff90"); cv.emit[int(py), int(px)] += L.col("b0ff60") * 0.8
    L.foreground(cv)
    L.vignette(cv)
    return L.finish(cv, 3).convert("RGBA")


def dim(img, k=0.45, tint=(18, 12, 26)):
    over = Image.new("RGBA", img.size, tint + (int(255 * k),))
    out = img.copy()
    out.alpha_composite(over)
    return out


def compose(bg, ui):
    out = bg.copy()
    out.alpha_composite(ui.im.resize((UW * 2, UH * 2), Image.NEAREST))
    return out.convert("RGB")


def header(ui, title, sub=None):
    ui.button(24, 18, 112, 44, "Back", key="Esc", size=20)
    ui.title((132, 10), title, 48)
    if sub:
        ui.text((136, 62), sub, "body", DIM)
    ui.divider(24, UW - 24, 84)


def sprite(name, anim="idle", frame=0):
    import json
    meta = json.load(open(os.path.join(ROOT, "art", "pix2d", "anim", "anim.json")))[name]
    fw, fh = meta["frame"]
    im = Image.open(os.path.join(ROOT, "art", "pix2d", "anim", f"{name}_{anim}.png")).convert("RGBA")
    f = im.crop((frame * fw, 0, (frame + 1) * fw, fh))
    return f.crop(f.getbbox())


def hero_img(hid, kind="portraits", size="_64"):
    p = os.path.join(PF, "heroes", kind, f"{hid}{size}.png")
    return Image.open(p).convert("RGBA")


# =====================================================================================================
def main_menu(bg, quit_dialog=False):
    ui = UI()
    lg = LOGO.logo()
    ui.paste(lg, 32, 26)
    ui.title((36, 66), "The War of Seven Crowns", 24, fill=hx("e8d8b8"))
    items = [("Continue", "continue", None, "Ember Reach  -  stage 3"), ("Campaign", "campaign", "C", None),
             ("Skirmish", "skirmish", "S", None), ("Heroes", "heroes", "H", "3 of 16"),
             ("Talents", "talents", "T", "8 points"), ("Codex", "codex", "K", None),
             ("Settings", "settings", "O", None), ("Credits", "credits", None, None), ("Quit", "quit", None, None)]
    ui.panel(28, 104, 336, 494)
    y = 120
    for i, (name, ic, key, sub) in enumerate(items):
        state = "hover" if (i == 0 and not quit_dialog) or (quit_dialog and name == "Quit") else "normal"
        h = 40 if i == 0 else 34
        ui.button(44, y, 320, y + h - 4, name, state, key=key, icon=ic, size=20 if i else 24, sub=sub)
        y += h + (8 if i in (0, 6) else 2)
        if i in (0, 6):
            ui.divider(60, 304, y - 6)
    ui.text((44, 470), "Runs 3  -  Wins 1  -  Best 10 waves  -  412 foes", "small", DIM, shadow=False)
    # a small card on the right: what is next in the story
    ui.panel(640, 432, 936, 518, ornate=False)
    ui.text((654, 446), "NEXT IN THE STORY", "small", GOLD, shadow=False)
    ui.text((654, 460), "Free the Cinder Warden", "button", TEXT)
    ui.text((654, 482), "Ember Reach, stage 4  -  Herald slain", "small", DIM, shadow=False)
    ui.text((936, 530), "v0.4 prototype", "small", hx("6a6078"), anchor="ra", shadow=False)
    if quit_dialog:
        ov = Image.new("RGBA", (UW, UH), (6, 4, 10, 150))
        ui.im.alpha_composite(ov)
        ui.panel(290, 180, 670, 366)
        ui.title((480, 196), "Leave Solenne?", 36, anchor="ma")
        ui.wrap((316, 244), "The watch fires will burn until you return. Your progress is saved.", 330, size=16,
                fill=DIM)
        ui.button(316, 316, 470, 346, "Stay", "hover", key="Esc", align="center")
        ui.button(490, 316, 644, 346, "Quit", "normal", key="Q", align="center")
    return compose(bg, ui)


def campaign(bg):
    ui = UI()
    header(ui, "Campaign", "The Ring of six lands. Win a land's stages to free its Warden.")
    # ---- painted map -----------------------------------------------------------------------------
    x0, y0, x1, y1 = 24, 96, 628, 522
    ui.panel(x0, y0, x1, y1)
    mw, mh = x1 - x0 - 14, y1 - y0 - 14
    rng = random.Random(4)
    ys, xs = np.mgrid[0:mh, 0:mw]
    cx, cy = mw / 2, mh / 2 + 4
    ang = (np.degrees(np.arctan2(ys - cy, xs - cx)) + 90 + 360) % 360
    rr = np.hypot((xs - cx) / 1.25, ys - cy)
    noise = np.zeros((mh, mw))
    for k in range(6):
        noise += np.sin(xs / (7 + k * 3) + k * 2) * np.cos(ys / (5 + k * 4) - k) / (k + 1)
    land = rr + noise * 6 < 190
    sector = ((ang + noise * 4) // 60).astype(int) % 6
    base = np.zeros((mh, mw, 3))
    sea = np.array([30, 44, 70]); sea2 = np.array([40, 60, 92])
    bay = np.tile(np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0,
                  (mh // 4 + 1, mw // 4 + 1))[:mh, :mw]
    base[:] = np.where((np.sin(ys / 3 + xs / 9) > 0.7)[..., None], sea2, sea)
    tints = [np.array(c) for c in ((168, 78, 48), (176, 156, 82), (74, 128, 64), (70, 110, 150), (150, 110, 70),
                                   (96, 70, 130))]
    for s in range(6):
        m = land & (sector == s)
        t = tints[s]
        shade = np.clip(np.floor((noise + 1.5) * 1.3 + bay), 0, 3)[..., None]
        base = np.where(m[..., None], t * (0.7 + 0.1 * shade), base)
    core = rr + noise * 3 < 62
    base = np.where(core[..., None], np.array([196, 182, 150]) * (0.85 + 0.05 * np.clip(np.floor(noise * 2 + bay), 0, 2))[..., None], base)
    # coasts and borders in ink
    edge = land & ~(np.roll(land, 1, 0) & np.roll(land, -1, 0) & np.roll(land, 1, 1) & np.roll(land, -1, 1))
    border = land & ~core & (sector != np.roll(sector, 1, 1))
    base[edge] = (20, 16, 26)
    base[np.roll(edge, 1, 0) & ~land] = (90, 120, 150)
    base[border & (bay > 0.5)] = (40, 30, 36)
    cedge = core & ~(np.roll(core, 1, 0) & np.roll(core, -1, 1))
    base[cedge] = (60, 46, 40)
    img = Image.fromarray(base.astype(np.uint8)).convert("RGBA")
    ui.paste(img, x0 + 7, y0 + 7)
    ox, oy = x0 + 7, y0 + 7
    d = ui.d
    # terrain marks per land
    marks = {0: "volcano", 1: "grass", 2: "tree", 3: "wave", 4: "mesa", 5: "shard"}
    for s in range(6):
        a = math.radians(s * 60 + 30 - 90)
        for k in range(14):
            r = rng.uniform(80, 170); aa = a + rng.uniform(-0.42, 0.42)
            px, py = int(cx + math.cos(aa) * r * 1.25), int(cy + math.sin(aa) * r)
            if not (0 < px < mw - 8 and 0 < py < mh - 8) or not land[py, px]:
                continue
            X, Y = ox + px, oy + py
            m = marks[s]
            if m == "tree":
                ui.rect(X, Y - 6, X + 5, Y - 1, hx("2c5a2a")); ui.rect(X + 1, Y - 6, X + 3, Y - 4, hx("4a8a3a"))
                ui.rect(X + 2, Y - 1, X + 3, Y + 1, hx("3a2618"))
            elif m == "volcano":
                for i in range(5):
                    ui.rect(X - i, Y - 5 + i, X + i + 1, Y - 4 + i, hx("4a2a22") if i else hx("ff7a3a"))
            elif m == "grass":
                ui.rect(X, Y - 2, X + 1, Y, hx("d8c070")); ui.rect(X + 2, Y - 3, X + 3, Y, hx("d8c070"))
            elif m == "wave":
                ui.rect(X, Y, X + 2, Y + 1, hx("c8e0ff")); ui.rect(X + 2, Y - 1, X + 4, Y, hx("c8e0ff"))
            elif m == "mesa":
                ui.rect(X - 3, Y - 4, X + 4, Y, hx("7a4a2a")); ui.rect(X - 3, Y - 4, X + 4, Y - 3, hx("d09a60"))
            else:
                ui.rect(X, Y - 5, X + 2, Y, hx("c090ff")); ui.rect(X, Y - 5, X + 1, Y - 3, hx("f0e0ff"))
    # Solenne at the centre
    sx, sy = ox + cx, oy + cy
    for i, (w, h) in enumerate(((22, 10), (14, 18), (6, 28))):
        ui.rect(sx - w // 2, sy - h, sx + w // 2, sy + 4, INK)
        ui.rect(sx - w // 2 + 1, sy - h + 1, sx + w // 2 - 1, sy + 3, hx("e6dcc6"))
        ui.rect(sx - w // 2 + 1, sy - h + 1, sx - w // 2 + 3, sy + 3, hx("fff6e0"))
    ui.gem(int(sx), int(sy) - 34, hx("ffd27a"), 4)
    ui.text((sx, sy + 8), "SOLENNE", "small", INK, anchor="ma", shadow=False)
    # stage nodes: four per land from the coast in towards Solenne, a dotted road between them
    done = {0: 2, 1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
    for s, (name, el) in enumerate(LANDS):
        a = math.radians(s * 60 + 30 - 90)
        pts = []
        for k in range(4):
            r = 168 - k * 28
            wob = math.sin(k * 1.7 + s) * 0.18
            pts.append((sx + math.cos(a + wob) * r * 1.25, sy + math.sin(a + wob) * r))
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = int(math.hypot(bx - ax, by - ay))
            for i in range(0, n, 3):
                ui.rect(ax + (bx - ax) * i / n, ay + (by - ay) * i / n, ax + (bx - ax) * i / n + 2,
                        ay + (by - ay) * i / n + 2, hx("2a1e18"))
        for k, (px, py) in enumerate(pts):
            won, cur = k < done[s], k == done[s] and s == 0
            locked = not won and not cur and s != 0
            c = GOLD if won else (ELEM[el] if not locked else hx("4a4258"))
            ui.rect(px - 6, py - 6, px + 7, py + 7, INK)
            ui.rect(px - 5, py - 5, px + 6, py + 6, c)
            ui.rect(px - 5, py - 5, px + 6, py - 3, GOLD_HI if won else tuple(min(255, v + 70) for v in c[:3]) + (255,))
            ui.text((px + 1, py), str(k + 1) if k < 3 else "W", "small", INK, anchor="mm", shadow=False)
            if cur:
                for rr_ in (10, 11):
                    d.ellipse((px - rr_, py - rr_, px + rr_, py + rr_), outline=hx("fff6d8"))
        # land banner
        lx, ly = sx + math.cos(a) * 210 * 1.25, sy + math.sin(a) * 200
        lx = min(max(lx, ox + 74), ox + mw - 74); ly = min(max(ly, oy + 10), oy + mh - 18)
        ui.title((lx, ly), name, 24, anchor="ma", fill=GOLD_HI if s == 0 else hx("d8ccb0"))
    # compass rose and frame label
    ui.text((x1 - 16, y1 - 22), "THE RING OF ORRHEN", "small", GOLD, anchor="ra")
    # ---- land panel --------------------------------------------------------------------------------
    ui.panel(640, 96, 936, 522)
    ui.gem(664, 124, ELEM["fire"], 6)
    ui.title((680, 104), "Ember Reach", 36)
    ui.text((662, 146), "LAND OF KINDLING  -  WARDEN: IGNAR", "small", GOLD, shadow=False)
    y = ui.wrap((660, 162), "The forges of Pyrrhenhall still burn, but salt-cages rise on the ash roads. "
                "The Herald Ashwick holds the pass.", 260, size=16)
    stages = [("1  Cinder Road", "won", 3), ("2  The Salt Gate", "won", 2),
              ("3  Pyrrhenhall Burning", "open", 0), ("4  Heart of the Forge", "locked", 0)]
    y += 6
    for i, (n, st, stars) in enumerate(stages):
        state = "hover" if st == "open" else ("disabled" if st == "locked" else "normal")
        ui.button(660, y, 916, y + 30, n, state, size=20)
        for k in range(3):
            ui.gem(860 + k * 16, y + 15, GOLD if k < stars else hx("4a4258"), 6) if st != "locked" else None
        y += 36
    ui.text((660, y + 4), "Difficulty", "button", TEXT)
    for i, n in enumerate(("Story", "Normal", "Hard")):
        ui.button(740 + i * 60, y, 796 + i * 60, y + 26, n, "selected" if i == 1 else "normal", size=20, align="center")
    y += 40
    ui.text((660, y), "Hero", "button", TEXT)
    ui.paste(hero_img("tamsin").resize((32, 32), Image.NEAREST), 740, y - 6)
    ui.text((780, y), "Tamsin Reed", "button", GOLD_HI)
    ui.button(660, 474, 916, 508, "Start stage 3", "hover", key="Enter", size=24, align="center")
    return compose(dim(bg, 0.72), ui)


def skirmish(bg):
    ui = UI()
    header(ui, "Skirmish", "One map, one run. Build, fuse, survive.")
    maps = [("Switchback", True), ("Serpentine", True), ("Crossroads", False), ("The Spiral", False)]
    ui.panel(24, 96, 380, 522)
    ui.text((40, 110), "MAPS", "small", GOLD, shadow=False)
    shots = ["switchback_placing.png", "early_wave.png"]
    for i, (n, open_) in enumerate(maps):
        x, y = 40 + (i % 2) * 166, 126 + (i // 2) * 136
        sel = i == 0
        ui.rect(x - 2, y - 2, x + 154, y + 114, GOLD if sel else INK)
        ui.rect(x, y, x + 152, y + 86, hx("101018"))
        if open_:
            sh = Image.open(os.path.join(PF, "screenshots", "game-art", shots[i])).convert("RGBA")
            sh = sh.crop((0, 66, 1568, 948)).resize((152, 86), Image.BOX)
            ui.paste(sh, x, y)
        else:
            ui.lock(x + 69, y + 26)
            ui.text((x + 76, y + 56), "LOCKED", "small", DIM, anchor="mm", shadow=False)
        ui.rect(x, y + 86, x + 152, y + 112, hx("3a2618") if sel else hx("1e1828"))
        ui.text((x + 8, y + 99), n, "button", hx("fff6d8") if sel else (TEXT if open_ else DIM), anchor="lm")
        if not open_:
            ui.text((x + 146, y + 99), "TALENTS", "small", DIM, anchor="rm", shadow=False)
    ui.wrap((40, 404), "Switchback: one long road that folds back on itself three times. Good for splash "
            "towers on the bends.", 324, size=16)
    ui.panel(392, 96, 936, 522)
    ui.text((410, 110), "RULES", "small", GOLD, shadow=False)
    ui.choice(410, 132, "Difficulty", ["Normal", "Hard", "Nightmare"], 0, w=100)
    ui.text((410, 172), "Start element", "button", TEXT)
    for i, e in enumerate(ELEM):
        x = 600 + i * 46
        ui.rect(x - 2, 166, x + 38, 196, GOLD if i == 0 else INK)
        ui.rect(x, 168, x + 36, 194, hx("3a2618") if i == 0 else hx("1e1828"))
        ui.gem(x + 18, 181, ELEM[e], 7)
    ui.text((600, 200), "FIRE  -  OPPOSITE: WATER", "small", DIM, shadow=False)
    ui.choice(410, 226, "Waves", ["30", "50", "Endless"], 0, w=100)
    ui.divider(410, 920, 262)
    ui.text((410, 276), "MODIFIERS", "small", GOLD, shadow=False)
    mods = [("Blood moon: enemies +25% speed, +50% gold", True), ("Iron towers: no selling", False),
            ("Herald hunt: a Herald every 10 waves", True), ("No skills", False)]
    for i, (m, on) in enumerate(mods):
        ui.toggle(410, 294 + i * 28, on, m)
    ui.divider(410, 920, 414)
    ui.text((410, 428), "Score x1.6", "button", GOLD_HI)
    ui.text((410, 450), "Best on Switchback  -  wave 10", "small", DIM, shadow=False)
    ui.button(660, 438, 916, 506, "Begin", "hover", key="Enter", size=32, align="center")
    return compose(dim(bg, 0.72), ui)


def heroes(bg):
    ui = UI()
    header(ui, "Heroes", "Champions of the six crowns. Take one hero into each battle.")
    ui.panel(24, 96, 420, 522)
    unlocked = {"tamsin", "brannoc", "ignar"}
    for i, (hid, name, title, el) in enumerate(HEROES):
        x, y = 42 + (i % 4) * 94, 112 + (i // 4) * 100
        sel = hid == "brannoc"
        ui.rect(x - 2, y - 2, x + 82, y + 90, GOLD if sel else INK)
        ui.rect(x, y, x + 80, y + 88, hx("3a2618") if sel else hx("1e1828"))
        p = hero_img(hid)
        if hid not in unlocked:
            a = np.asarray(p).copy()
            a[..., :3] = (a[..., :3].mean(-1, keepdims=True) * 0.25 + np.array([14, 10, 22])).astype(np.uint8)
            p = Image.fromarray(a)
        ui.paste(p, x + 8, y + 4)
        ui.text((x + 40, y + 74), name.split()[0].upper(), "small", TEXT if hid in unlocked else DIM, anchor="ma",
                shadow=False)
        if el:
            ui.gem(x + 72, y + 9, ELEM[el] if hid in unlocked else hx("3a3248"), 4)
        if hid not in unlocked:
            ui.lock(x + 33, y + 30)
    # detail
    ui.panel(432, 96, 936, 522)
    full = hero_img("brannoc", "full_body", "_48x80")
    ui.rect(450, 112, 606, 368, hx("120e18"))
    for k in range(8):  # forge glow behind him
        r = 70 - k * 8
        ui.d.ellipse((528 - r, 300 - r, 528 + r, 300 + r // 2), fill=(90 + k * 18, 40 + k * 6, 20, 255))
    ui.paste(full, 528 - 72, 360 - 240, scale=3)
    ui.gem(628, 128, ELEM["fire"], 6)
    ui.title((644, 106), "Brannoc Emberhand", 36)
    ui.text((628, 148), "SMITH-LORD OF THE REACH  -  FIRE  -  DEFENDER", "small", GOLD, shadow=False)
    y = ui.wrap((626, 166), "Smith-lord of Pyrrhenhall, brass rings in his beard. His forge-hammer glows at "
                "the seams; he forged the bars of the Dawn Gate shut.", 292, size=16)
    stats = [("Might", 0.8, ELEM["fire"]), ("Guard", 0.65, hx("c8c0d8")), ("Reach", 0.3, ELEM["storm"]),
             ("Pace", 0.35, ELEM["nature"])]
    for i, (n, v, c) in enumerate(stats):
        ui.text((626, y + 4 + i * 18), n, "button", TEXT, size=20)
        ui.bar(690, y + 10 + i * 18, 220, v, c)
    y += 84
    ui.text((626, y), "ABILITIES", "small", GOLD, shadow=False)
    abil = [("Q", "Anvil Fall", "SLAMS THE ROAD: STUN AND BURN"), ("W", "Temper", "FIRE TOWERS NEARBY +30% RATE"),
            ("R", "Seal the Gate", "ULTIMATE: A WALL OF MOLTEN BARS")]
    for i, (k, n, t) in enumerate(abil):
        yy = y + 16 + i * 32
        ui.keycap(626, yy + 2, k)
        ui.text((648, yy - 2), n, "button", GOLD_HI)
        ui.text((648, yy + 18), t, "small", DIM, shadow=False)
    ui.text((450, 380), "LEVEL 4", "small", GOLD, shadow=False)
    ui.bar(450, 394, 156, 0.6, GOLD)
    ui.text((450, 404), "1,240 / 2,000 XP", "small", DIM, shadow=False)
    ui.button(450, 474, 606, 506, "Skins", "normal", size=20, align="center")
    ui.button(626, 474, 916, 506, "Take into battle", "hover", key="Enter", size=24, align="center")
    return compose(dim(bg, 0.72), ui)


def talents(bg):
    ui = UI()
    header(ui, "Talents", "Spend crown-shards from every run. Each branch strengthens one art.")
    ui.panel(24, 96, 676, 522)
    cx, cy = 350, 312
    els = list(ELEM)
    rng = random.Random(3)
    nodes = [(cx, cy, None, True)]
    edges = []
    for i, e in enumerate(els):
        a = math.radians(i * 60 - 90)
        prev = 0
        for k in range(1, 5):
            r = 40 + k * 38
            for side in ((0,) if k % 2 else (-0.16, 0.16)):
                x, y = cx + math.cos(a + side) * r * 1.35, cy + math.sin(a + side) * r
                owned = (i == 0 and k <= 3) or (i == 1 and k <= 1) or (i == 3 and k <= 2)
                nodes.append((x, y, e, owned))
                edges.append((prev, len(nodes) - 1, owned))
            prev = len(nodes) - 1
    for a_, b_, owned in edges:
        (ax, ay, *_), (bx, by, *_) = nodes[a_], nodes[b_]
        n = int(math.hypot(bx - ax, by - ay))
        for t in range(n):
            px, py = ax + (bx - ax) * t / n, ay + (by - ay) * t / n
            ui.rect(px, py, px + 2, py + 2, GOLD if owned else hx("3a3248"))
    for _ in range(140):  # starfield behind the web
        x, y = rng.uniform(40, 660), rng.uniform(110, 510)
        ui.rect(x, y, x + 1, y + 1, hx("6a6090"))
    for i, (x, y, e, owned) in enumerate(nodes):
        big = i == 0 or (i % 5 == 0)
        c = (GOLD if e is None else ELEM[e]) if owned else hx("3a3248")
        ui.node(int(x), int(y), 11 if i == 0 else (8 if big else 6), (GOLD if e is None else ELEM[e]), owned)
    sel = nodes[9]
    ui.d.ellipse((sel[0] - 12, sel[1] - 12, sel[0] + 12, sel[1] + 12), outline=hx("fff6d8"))
    ui.d.ellipse((sel[0] - 13, sel[1] - 13, sel[0] + 13, sel[1] + 13), outline=GOLD)
    ui.text((40, 110), "CROWN-SHARDS", "small", GOLD, shadow=False)
    ui.text((40, 122), "8", "title", GOLD_HI, size=36)
    # tooltip panel
    ui.panel(688, 96, 936, 522)
    ui.gem(712, 124, ELEM["storm"], 6)
    ui.title((728, 104), "Stormsong II", 36)
    ui.text((708, 146), "STORM BRANCH  -  RANK 0 / 3", "small", GOLD, shadow=False)
    y = ui.wrap((706, 164), "Chain lightning jumps to one more target. At rank 3 the last jump stuns.", 214, size=16)
    ui.text((706, y + 6), "Cost: 2 shards", "button", GOLD_HI)
    ui.text((706, y + 30), "Needs: Stormsong I", "small", DIM, shadow=False)
    ui.divider(706, 918, 330)
    ui.text((706, 344), "BRANCHES", "small", GOLD, shadow=False)
    for i, (n, e) in enumerate(zip(("Kindling", "Stormsong", "Rootcraft", "Tidelore", "Runecarving", "Starcraft"),
                                   els)):
        ui.gem(714, 366 + i * 16, ELEM[e], 4)
        ui.text((726, 360 + i * 16), n, "small", TEXT, shadow=False)
        ui.text((916, 360 + i * 16), ("3/12", "1/12", "0/12", "2/12", "0/12", "0/12")[i], "small", DIM,
                anchor="ra", shadow=False)
    ui.button(706, 474, 800, 506, "Reset", "normal", size=20, align="center")
    ui.button(808, 474, 918, 506, "Learn", "hover", key="Enter", size=24, align="center")
    return compose(dim(bg, 0.72), ui)


def codex(bg):
    ui = UI()
    header(ui, "Codex", "Everything you have met on the road, and the story so far.")
    ui.tabs(24, 96, ["Towers", "Enemies", "Heroes", "Story"], 1, w=120)
    ui.panel(24, 120, 330, 522)
    entries = [("skeleton", "Bone Walker", True), ("orc", "Gorrath Raider", True), ("ghost", "Hollow Shade", True),
               ("golem", "Rune Golem", True), ("dragon", "Ashwing Drake", True), ("dwarf", "?", False),
               ("orb_void", "Void Wisp", True), ("orb_fire", "Ember Wisp", True)]
    for i, (sp, n, seen) in enumerate(entries):
        y = 136 + i * 44
        sel = sp == "golem"
        ui.button(40, y, 314, y + 40, n if seen else "Not yet met", "selected" if sel else ("normal" if seen else
                                                                                           "disabled"), size=20)
        if seen:
            s = sprite(sp)
            s.thumbnail((34, 34), Image.NEAREST)
            ui.paste(s, 278 - s.width // 2, y + 20 - s.height // 2)
    # detail
    ui.panel(342, 120, 936, 522)
    g = sprite("golem", "idle", 0)
    ui.rect(362, 140, 562, 380, hx("120e18"))
    ui.d.ellipse((392, 340, 532, 372), fill=hx("0a0810"))
    ui.paste(g, 462 - g.width, 362 - g.height * 2, scale=2)
    ui.title((582, 130), "Rune Golem", 48)
    ui.text((584, 182), "UNBOUND  -  EARTH  -  ARMOURED", "small", GOLD, shadow=False)
    y = ui.wrap((582, 200), "Chiselled from the walls of fallen keeps and driven by a rune the Unmaking "
                "carved into its chest. Slow, and almost deaf to arrows.", 334, size=16)
    stats = [("Health", "1,800"), ("Armour", "High"), ("Speed", "Slow"), ("Weak to", "Storm"),
             ("Resists", "Earth"), ("Found", "Sunscar 1")]
    for i, (k, v) in enumerate(stats):
        x, yy = 582 + (i % 2) * 170, y + 12 + (i // 2) * 24
        ui.text((x, yy), k, "button", DIM, size=20)
        ui.text((x + 80, yy), v, "button", GOLD_HI if k == "Weak to" else TEXT, size=20)
    ui.divider(362, 916, 400)
    ui.text((362, 414), "FIELD NOTE  -  MASTER FENNICK", "small", GOLD, shadow=False)
    ui.wrap((362, 430), "\"Lightning finds the rune. Hit it there and the whole thing remembers it is only "
            "stone.\"", 554, size=16, fill=hx("d8ccb0"))
    ui.text((916, 500), "Enemies met: 23 / 41", "small", DIM, anchor="ra", shadow=False)
    return compose(dim(bg, 0.72), ui)


def settings(bg):
    ui = UI()
    header(ui, "Settings")
    ui.tabs(24, 96, ["Game", "Video", "Audio", "Controls"], 2, w=120)
    ui.panel(24, 120, 936, 522)
    ui.text((44, 138), "VOLUME", "small", GOLD, shadow=False)
    for i, (n, v) in enumerate((("Master", 0.8), ("Music", 0.6), ("Effects", 0.9), ("Narrator", 1.0),
                                ("Ambience", 0.5))):
        ui.slider(44, 156 + i * 34, 300, v, n)
    ui.divider(44, 916, 334)
    ui.text((44, 348), "OPTIONS", "small", GOLD, shadow=False)
    ui.toggle(44, 364, True, "Subtitles for the narrator")
    ui.toggle(44, 392, True, "Mute when the game is in the background")
    ui.toggle(44, 420, False, "Mono sound")
    ui.choice(500, 364, "Output", ["Speakers", "Headphones"], 0, w=110)
    ui.choice(500, 400, "Music style", ["Score", "Calm"], 0, w=110)
    ui.button(44, 474, 200, 506, "Defaults", "normal", size=20, align="center")
    ui.button(760, 474, 916, 506, "Apply", "hover", key="Enter", size=24, align="center")
    return compose(dim(bg, 0.72), ui)


def settings_video(bg):
    ui = UI()
    header(ui, "Settings")
    ui.tabs(24, 96, ["Game", "Video", "Audio", "Controls"], 1, w=120)
    ui.panel(24, 120, 936, 522)
    ui.text((44, 138), "DISPLAY", "small", GOLD, shadow=False)
    ui.choice(44, 160, "Window", ["Fullscreen", "Borderless", "Windowed"], 0, w=110)
    ui.choice(44, 196, "Resolution", ["1280x720", "1920x1080", "2560x1440"], 1, w=110)
    ui.choice(44, 232, "Frame cap", ["60", "144", "Off"], 1, w=110)
    ui.toggle(44, 268, True, "V-Sync")
    ui.divider(44, 916, 304)
    ui.text((44, 318), "LOOK", "small", GOLD, shadow=False)
    ui.slider(44, 336, 300, 0.7, "Brightness")
    ui.slider(44, 370, 300, 0.5, "Screen shake")
    ui.toggle(44, 404, True, "Day and night lighting")
    ui.toggle(44, 432, True, "Bloom on spells and towers")
    ui.toggle(500, 404, False, "Colour-blind element marks")
    ui.toggle(500, 432, True, "Show damage numbers")
    ui.button(44, 474, 200, 506, "Defaults", "normal", size=20, align="center")
    ui.button(760, 474, 916, 506, "Apply", "hover", key="Enter", size=24, align="center")
    return compose(dim(bg, 0.72), ui)


def credits(bg):
    ui = UI()
    header(ui, "Credits")
    ui.panel(230, 100, 730, 522)
    y = 118
    blocks = [("Developed by", ["Pasiv Production"]), ("A game by", ["Doctor Paris and Thanos"]),
              ("Story", ["The War of Seven Crowns"]), ("Narrator", ["Elariel (ElevenLabs)"]),
              ("Music", ["Original score"]), ("Fonts", ["Pirata One, Jersey 10, Pixelify Sans, Silkscreen",
                                                       "SIL Open Font License"]),
              ("Engine", ["Godot Engine"]), ("Thank you for holding the road.", [])]
    for h, lines in blocks:
        if not lines:
            ui.divider(260, 700, y + 8)
            ui.title((480, y + 20), h, 24, anchor="ma")
            break
        ui.text((480, y), h.upper(), "small", GOLD, anchor="ma", shadow=False)
        y += 14
        for l in lines:
            ui.text((480, y), l, "button", TEXT, anchor="ma")
            y += 22
        y += 10
    return compose(dim(bg, 0.72), ui)


def sheet(paths, out):
    ims = [Image.open(p) for p in paths]
    tw, th = 640, 360
    cols = 3
    rows = math.ceil(len(ims) / cols)
    sh = Image.new("RGB", (cols * tw + (cols + 1) * 12, rows * th + (rows + 1) * 12), (14, 10, 20))
    for i, im in enumerate(ims):
        sh.paste(im.resize((tw, th), Image.LANCZOS), (12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 12)))
    sh.save(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(ROOT, "art", "menu"))
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)
    bg = backdrop()
    bg.convert("RGB").save(os.path.join(args.out, "menu_backdrop_1920x1080.png"))
    screens = [("00_main_menu", main_menu), ("01_campaign", campaign), ("02_skirmish", skirmish),
               ("03_heroes", heroes), ("04_talents", talents), ("05_codex", codex), ("06_settings_audio", settings),
               ("07_settings_video", settings_video), ("08_credits", credits),
               ("09_quit", lambda b: main_menu(b, True))]
    paths = []
    for name, fn in screens:
        p = os.path.join(args.out, f"{name}.png")
        fn(bg).save(p)
        paths.append(p)
        print("wrote", p)
    sheet(paths, os.path.join(args.out, "all_screens.png"))


if __name__ == "__main__":
    main()
