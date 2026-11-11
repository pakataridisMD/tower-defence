"""Pixel-art interface kit for the menu mock-ups (design only).

Screens are drawn at 960x540 interface pixels and shown at 2x (1920x1080). Backdrops are painted at 640x360 and
shown at 3x, the same as the battle board. Everything is hard pixels: no anti-aliased text, no gradients.

Fonts (SIL Open Font License, free for commercial games): Pirata One for titles, Jersey 10 for buttons and labels,
Pixelify Sans for body text, Silkscreen for small captions. Put the .ttf files in FONT_DIR.
"""
from __future__ import annotations

import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_DIR = os.environ.get("PIXEL_FONTS", "/home/user/fonts")
UW, UH = 960, 540


def hx(h, a=255):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


INK = hx("0c0910")
TEXT = hx("efe3c8")
DIM = hx("9d92a8")
GOLD = hx("d8ac60")
GOLD_HI = hx("f6d690")
GOLD_LO = hx("8a6430")
STONE = [hx("231d2e"), hx("3a3248"), hx("554a66"), hx("776a8a")]   # dark .. light frame
FILL = hx("16121e", 236)
FILL2 = hx("221b2e")
ELEM = {"fire": hx("f0602a"), "storm": hx("f6ce50"), "nature": hx("60c852"), "water": hx("4696ec"),
        "earth": hx("ba804c"), "void": hx("a060ec")}


def font(kind, size=None):
    name, default = {"title": ("PirataOne-Regular.ttf", 24), "button": ("Jersey10-Regular.ttf", 20),
                     "body": ("PixelifySans.ttf", 16), "small": ("Silkscreen-Regular.ttf", 8)}[kind]
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size or default)


class UI:
    def __init__(self):
        self.im = Image.new("RGBA", (UW, UH), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)
        self.d.fontmode = "1"

    # ---- text --------------------------------------------------------------------------------------
    def text(self, xy, s, kind="body", fill=TEXT, size=None, anchor="la", shadow=True):
        f = font(kind, size)
        x, y = xy
        if shadow:
            self.d.text((x, y + 1), s, font=f, fill=INK, anchor=anchor)
            self.d.text((x + 1, y + 1), s, font=f, fill=INK, anchor=anchor)
        self.d.text((x, y), s, font=f, fill=fill, anchor=anchor)

    def wrap(self, xy, s, width, kind="body", fill=DIM, size=None, gap=4):
        f = font(kind, size)
        x, y = xy
        line = ""
        for word in s.split():
            t = (line + " " + word).strip()
            if self.d.textlength(t, font=f) > width:
                self.text((x, y), line, kind, fill, size)
                y += f.size + gap
                line = word
            else:
                line = t
        if line:
            self.text((x, y), line, kind, fill, size)
            y += f.size + gap
        return y

    def title(self, xy, s, size=48, fill=GOLD_HI, anchor="la"):
        """Blackletter title in gold with a dark outline and a lower dark band (two-tone metal)."""
        f = font("title", size)
        x, y = xy
        for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1), (1, 1), (0, 2), (1, 2), (2, 2)):
            self.d.text((x + dx, y + dy), s, font=f, fill=INK, anchor=anchor)
        layer = Image.new("RGBA", self.im.size, (0, 0, 0, 0))
        ld = ImageDraw.Draw(layer)
        ld.fontmode = "1"
        ld.text((x, y), s, font=f, fill=fill, anchor=anchor)
        a = np.asarray(layer).copy()
        ys = np.nonzero(a[..., 3])[0]
        if len(ys):
            mid = ys.min() + (ys.max() - ys.min()) * 0.55
            lower = (np.arange(UH)[:, None] > mid) & (a[..., 3] > 0)
            a[lower] = GOLD
            top = (np.arange(UH)[:, None] < ys.min() + 2) & (a[..., 3] > 0)
            a[top] = hx("fff6d8")
        self.im.alpha_composite(Image.fromarray(a))

    # ---- shapes ------------------------------------------------------------------------------------
    def rect(self, x0, y0, x1, y1, c):
        x0, y0, x1, y1 = int(round(x0)), int(round(y0)), int(round(x1)), int(round(y1))
        if x1 <= x0 or y1 <= y0:
            return
        self.d.rectangle((x0, y0, x1 - 1, y1 - 1), fill=c)

    def panel(self, x0, y0, x1, y1, fill=FILL, trim=GOLD, ornate=True):
        """Stone frame with a bevel lit from the upper left, gold hairline, rivets in the corners."""
        r = self.rect
        r(x0, y0, x1, y1, INK)
        r(x0 + 1, y0 + 1, x1 - 1, y1 - 1, STONE[1])
        r(x0 + 1, y0 + 1, x1 - 1, y0 + 2, STONE[3])
        r(x0 + 1, y0 + 1, x0 + 2, y1 - 1, STONE[2])
        r(x0 + 1, y1 - 2, x1 - 1, y1 - 1, STONE[0])
        r(x1 - 2, y0 + 1, x1 - 1, y1 - 1, STONE[0])
        r(x0 + 4, y0 + 4, x1 - 4, y1 - 4, INK)
        r(x0 + 5, y0 + 5, x1 - 5, y1 - 5, trim)
        r(x0 + 5, y0 + 5, x1 - 5, y0 + 6, GOLD_HI if trim == GOLD else trim)
        r(x0 + 6, y0 + 6, x1 - 6, y1 - 6, fill)
        # faint dither on the fill so it reads as cloth/slate, not flat UI
        for yy in range(y0 + 7, y1 - 7, 2):
            for xx in range(x0 + 7 + (yy // 2) % 2 * 2, x1 - 7, 4):
                self.im.putpixel((xx, yy), FILL2)
        if ornate:
            for cx, cy in ((x0 + 2, y0 + 2), (x1 - 7, y0 + 2), (x0 + 2, y1 - 7), (x1 - 7, y1 - 7)):
                r(cx, cy, cx + 5, cy + 5, INK)
                r(cx + 1, cy + 1, cx + 4, cy + 4, GOLD)
                r(cx + 1, cy + 1, cx + 3, cy + 2, GOLD_HI)
                r(cx + 3, cy + 3, cx + 4, cy + 4, GOLD_LO)

    def button(self, x0, y0, x1, y1, label, state="normal", key=None, icon=None, size=20, sub=None, align="left"):
        """state: normal, hover (gold frame, warm fill, marker), selected, disabled."""
        r = self.rect
        hot = state in ("hover", "selected")
        r(x0, y0, x1, y1, INK)
        if hot:
            r(x0 + 1, y0 + 1, x1 - 1, y1 - 1, GOLD)
            r(x0 + 1, y0 + 1, x1 - 1, y0 + 2, GOLD_HI)
            r(x0 + 1, y1 - 2, x1 - 1, y1 - 1, GOLD_LO)
            r(x0 + 3, y0 + 3, x1 - 3, y1 - 3, INK)
            r(x0 + 4, y0 + 4, x1 - 4, y1 - 4, hx("3a2618"))
            r(x0 + 4, y0 + 4, x1 - 4, y0 + 6, hx("5a3a20"))
        else:
            r(x0 + 1, y0 + 1, x1 - 1, y1 - 1, STONE[1])
            r(x0 + 1, y0 + 1, x1 - 1, y0 + 2, STONE[3])
            r(x0 + 1, y0 + 1, x0 + 2, y1 - 1, STONE[2])
            r(x0 + 1, y1 - 2, x1 - 1, y1 - 1, STONE[0])
            r(x0 + 3, y0 + 3, x1 - 3, y1 - 3, hx("1e1828") if state != "disabled" else hx("1a1620"))
        fill = TEXT if state == "normal" else (hx("fff6d8") if hot else hx("5e566a"))
        tx = x0 + 14
        cy = (y0 + y1) // 2
        if hot:
            # gem marker on the left edge
            gx = x0 - 4
            for i in range(5):
                r(gx + i, cy - i, gx + i + 1, cy + i + 1, INK)
            for i in range(4):
                r(gx + 1 + i, cy - i + 1, gx + 2 + i, cy + i, GOLD_HI if i < 2 else GOLD)
        if icon is not None:
            self.icon(icon, x0 + 10, cy - 8)
            tx = x0 + 34
        if align == "center":
            right = x1 - ((max(14, 8 + len(key) * 6) + 14) if key else 0)
            self.text(((x0 + right) // 2, cy - 1), label, "button", fill, size, anchor="mm")
        else:
            self.text((tx, cy - 1), label, "button", fill, size, anchor="lm")
        if sub:
            self.text((x1 - 10, cy), sub, "small", GOLD if hot else DIM, anchor="rm", shadow=False)
        if key:
            kw = max(14, 8 + len(key) * 6)
            right = x1 - 10 - (int(self.d.textlength(sub, font=font("small"))) + 8 if sub else 0)
            self.keycap(right - kw, cy - 7, key)

    def keycap(self, x, y, k):
        w = max(14, 8 + len(k) * 6)
        r = self.rect
        r(x, y, x + w, y + 14, INK)
        r(x + 1, y + 1, x + w - 1, y + 13, STONE[2])
        r(x + 1, y + 11, x + w - 1, y + 13, STONE[0])
        self.text((x + w // 2, y + 6), k, "small", TEXT, anchor="mm", shadow=False)

    def tabs(self, x, y, names, active, w=110):
        for i, n in enumerate(names):
            x0 = x + i * (w + 4)
            on = i == active
            r = self.rect
            r(x0, y, x0 + w, y + 24, INK)
            r(x0 + 1, y + 1, x0 + w - 1, y + 24, GOLD if on else STONE[1])
            r(x0 + 1, y + 1, x0 + w - 1, y + 2, GOLD_HI if on else STONE[3])
            r(x0 + 3, y + 3, x0 + w - 3, y + 24, hx("3a2618") if on else hx("1e1828"))
            self.text((x0 + w // 2, y + 13), n, "button", hx("fff6d8") if on else DIM, anchor="mm")

    def slider(self, x, y, w, value, label, shown=None):
        self.text((x, y), label, "button", TEXT)
        sx = x + 190
        r = self.rect
        r(sx, y + 6, sx + w, y + 14, INK)
        r(sx + 1, y + 7, sx + w - 1, y + 13, hx("0f0c15"))
        fw = int((w - 2) * value)
        r(sx + 1, y + 7, sx + 1 + fw, y + 13, GOLD)
        r(sx + 1, y + 7, sx + 1 + fw, y + 9, GOLD_HI)
        for t in range(1, 10):
            r(sx + w * t // 10, y + 12, sx + w * t // 10 + 1, y + 13, INK)
        kx = sx + fw
        r(kx - 5, y + 2, kx + 6, y + 18, INK)
        r(kx - 4, y + 3, kx + 5, y + 17, STONE[3])
        r(kx - 2, y + 5, kx + 3, y + 15, GOLD)
        r(kx - 2, y + 5, kx + 1, y + 8, GOLD_HI)
        self.text((sx + w + 14, y), shown or f"{int(value * 100)}%", "button", GOLD_HI)

    def toggle(self, x, y, on, label):
        r = self.rect
        r(x, y + 2, x + 16, y + 18, INK)
        r(x + 1, y + 3, x + 15, y + 17, STONE[1])
        r(x + 3, y + 5, x + 13, y + 15, hx("0f0c15"))
        if on:
            for i, (px, py) in enumerate(((4, 9), (5, 10), (6, 11), (7, 12), (8, 11), (9, 10), (10, 9), (11, 8),
                                          (12, 7))):
                r(x + px, y + py, x + px + 2, y + py + 2, GOLD_HI if i > 3 else GOLD)
        self.text((x + 26, y), label, "button", TEXT if on else DIM)

    def choice(self, x, y, label, options, active, w=96):
        self.text((x, y), label, "button", TEXT)
        sx = x + 190
        for i, o in enumerate(options):
            x0 = sx + i * (w + 4)
            self.button(x0, y - 3, x0 + w, y + 21, o, "selected" if i == active else "normal", size=20,
                        align="center")

    def divider(self, x0, x1, y):
        r = self.rect
        r(x0, y, x1, y + 1, GOLD_LO)
        r(x0, y + 1, x1, y + 2, INK)
        mx = (x0 + x1) // 2
        for i in range(4):
            r(mx - i, y - 3 + i, mx + i + 1, y - 2 + i, GOLD)
            r(mx - i, y + 4 - i, mx + i + 1, y + 5 - i, GOLD)

    def bar(self, x, y, w, frac, c):
        r = self.rect
        r(x, y, x + w, y + 6, INK)
        r(x + 1, y + 1, x + w - 1, y + 5, hx("0f0c15"))
        r(x + 1, y + 1, x + 1 + int((w - 2) * frac), y + 5, c)
        r(x + 1, y + 1, x + 1 + int((w - 2) * frac), y + 2, tuple(min(255, v + 60) for v in c[:3]) + (255,))

    def gem(self, x, y, c, r=4):
        """A small faceted gem: element pip."""
        for i in range(r + 1):
            self.rect(x - i, y - r + i, x + i + 1, y - r + i + 1, INK)
            self.rect(x - i, y + r - i, x + i + 1, y + r - i + 1, INK)
        for i in range(r):
            self.rect(x - i + 1, y - r + i + 1, x + i, y - r + i + 2, c)
            self.rect(x - i + 1, y + r - i - 1, x + i, y + r - i, tuple(int(v * 0.6) for v in c[:3]) + (255,))
        self.rect(x - 1, y - r + 2, x, y - r + 4, (255, 255, 255, 255))

    def node(self, x, y, r, c, owned):
        """Talent node: a round socket. Owned ones glow in their colour, locked ones are dark with a dim rim."""
        d = self.d
        d.ellipse((x - r - 1, y - r - 1, x + r + 1, y + r + 1), fill=INK)
        d.ellipse((x - r, y - r, x + r, y + r), fill=STONE[2] if owned else STONE[1])
        ri = r - 2
        if owned:
            d.ellipse((x - ri, y - ri, x + ri, y + ri), fill=c)
            hi = tuple(min(255, v + 90) for v in c[:3]) + (255,)
            d.ellipse((x - ri + 1, y - ri + 1, x, y), fill=hi)
            self.rect(x - ri // 2, y - ri // 2, x - ri // 2 + 2, y - ri // 2 + 2, (255, 255, 255, 255))
        else:
            d.ellipse((x - ri, y - ri, x + ri, y + ri), fill=hx("120e18"))
            dc = tuple(int(v * 0.45) for v in c[:3]) + (255,)
            d.ellipse((x - ri + 2, y - ri + 2, x + ri - 2, y + ri - 2), outline=dc)

    def lock(self, x, y, c=None):
        c = c or GOLD
        r = self.rect
        r(x + 3, y, x + 11, y + 2, INK); r(x + 2, y + 1, x + 4, y + 8, INK); r(x + 10, y + 1, x + 12, y + 8, INK)
        r(x + 4, y + 1, x + 10, y + 2, STONE[3]); r(x + 3, y + 2, x + 4, y + 7, STONE[3]); r(x + 10, y + 2, x + 11, y + 7, STONE[2])
        r(x, y + 7, x + 14, y + 17, INK)
        r(x + 1, y + 8, x + 13, y + 16, c)
        r(x + 1, y + 8, x + 13, y + 9, GOLD_HI)
        r(x + 6, y + 10, x + 8, y + 14, INK)

    def paste(self, img, x, y, scale=1):
        if scale != 1:
            img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
        self.im.alpha_composite(img.convert("RGBA"), (int(x), int(y)))

    def icon(self, name, x, y):
        """16x16 pixel icons drawn from tiny maps."""
        maps = ICONS.get(name)
        if not maps:
            return
        pal = {"k": INK, "g": GOLD, "h": GOLD_HI, "l": GOLD_LO, "w": TEXT, "s": STONE[3], "d": STONE[1],
               "r": hx("c43030"), "v": hx("a060ec"), "b": hx("4696ec"), "e": hx("60c852"), "o": hx("f0602a")}
        for j, row in enumerate(maps):
            for i, ch in enumerate(row):
                if ch in pal:
                    self.im.putpixel((x + i, y + j), pal[ch])


ICONS = {
    "continue": ["................", "....kk..........", "....khk.........", "....khgk........", "....khggk.......",
                 "....khgggk......", "....khggggk.....", "....khgggggk....", "....khggggk.....", "....khgggk......",
                 "....khggk.......", "....khgk........", "....kgk.........", "....kk..........", "................",
                 "................"],
    "campaign": ["................", "..kkkkkkkkkkkk..", ".khhwwwwwwwwwhk.", ".kwwwwrwwwwwwwk.", ".kwwwwkrwwwwwwk.",
                 ".kwwwwwwkwwwwwk.", ".kwwwwwwwkwwwwk.", ".kwwwwwwwwkwrwk.", ".kwwwwwwwwwkrkk.", ".kwwkkwwwwwwkwk.",
                 ".kwkrrkwwwwwwwk.", ".kwwkkwwwwwwwwk.", ".kgwwwwwwwwwwgk.", "..kkkkkkkkkkkk..", "................",
                 "................"],
    "skirmish": ["................", "k.............k.", "kk...........kk.", ".kwk.......kwk..", "..kwk.....kwk...",
                 "...kwk...kwk....", "....kwk.kwk.....", ".....kwkwk......", "......kwk.......", ".....kwkwk......",
                 "..kkkwk.kwkkk...", "..kgk.....kgk...", ".kgk.......kgk..", "kgk.........kgk.", "kk...........kk.",
                 "................"],
    "heroes": ["................", ".....kkkkkk.....", "....kssssssk....", "...kssddddssk...", "...ksdkddkdsk...",
               "...ksdddddds k..", "....kssssssk....", ".....kddddk.....", "...kkrrrrrrkk...", "..krrrgrrgrrrk..",
               "..krrrrggrrrrk..", "..krrrrggrrrrk..", "..kkrrrrrrrrkk..", "...kddkkkkddk...", "...kk......kk...",
               "................"],
    "talents": ["................", ".......kk.......", "......khgk......", ".......kk.......", "...kk...k...kk...",
                "..kbbk..k..kvvk.", "...kk.kkkkk.kk..", "......kgggk.....", "......kghgk.....", "......kgggk.....",
                "...kk.kkkkk.kk..", "..keek..k..kook.", "...kk...k...kk..", ".......kk.......", "......kook......",
                ".......kk......."],
    "codex": ["................", "..kkkkkk.kkkkkk.", ".kwwwwwwkwwwwwwk", ".kwkkkwwkwwkkkwk", ".kwwwwwwkwwwwwwk",
              ".kwkkkkwkwkkkkwk", ".kwwwwwwkwwwwwwk", ".kwkkkwwkwwkkkwk", ".kwwwwwwkwwwwwwk", ".kwkkkkwkwkkkkwk",
              ".kwwwwwwkwwwwwwk", ".klllllkkklllllk", "..kkkkkk.kkkkkk.", "................", "................",
              "................"],
    "settings": ["................", "......kkkk......", "..kk.kssssk.kk..", ".kssksddddksssk.", ".ksdddddddddsk..",
                 "..kdddkkkkdddk..", ".ksddk....kddsk.", ".ksdk......kdsk.", ".ksdk......kdsk.", ".ksddk....kddsk.",
                 "..kdddkkkkdddk..", ".ksdddddddddsk..", ".kssksddddksssk.", "..kk.kssssk.kk..", "......kkkk......",
                 "................"],
    "credits": ["................", ".......kk.......", "......kgk.......", ".....kghgk......", "kk..kghhgk..kk..",
                "kgk.kgggk..kgk..", ".kgkkggggkkgk...", ".kggggggggggk...", ".kghhgggghhgk...", ".kgggggggggggk..",
                ".kkkkkkkkkkkk...", ".klllllllllllk..", ".kkkkkkkkkkkkk..", "................", "................",
                "................"],
    "quit": ["................", "...kkkkkkkk.....", "...kddddddk.....", "...kdkkkkdk.....", "...kdk..kdk..k..",
             "...kdk..kdk..kk.", "...kdk..kdkkkhk.", "...kdkgkkdkhhhhk", "...kdk..kdkkkhk.", "...kdk..kdk..kk.",
             "...kdk..kdk..k..", "...kdkkkkdk.....", "...kddddddk.....", "...kkkkkkkk.....", "................",
             "................"],
}
