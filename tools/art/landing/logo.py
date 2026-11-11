"""Pixel logo (same construction as tools/art/gen_ui_art.py make_logo), copied from the promo kit keyart.py."""
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

FONT = {
    "T": ["#####", "..#..", "..#..", "..#..", "..#..", "..#..", "..#.."],
    "O": [".###.", "#...#", "#...#", "#...#", "#...#", "#...#", ".###."],
    "W": ["#...#", "#...#", "#...#", "#.#.#", "#.#.#", "##.##", "#...#"],
    "E": ["#####", "#....", "#....", "####.", "#....", "#....", "#####"],
    "R": ["####.", "#...#", "#...#", "####.", "#.#..", "#..#.", "#...#"],
    "D": ["####.", "#...#", "#...#", "#...#", "#...#", "#...#", "####."],
    "F": ["#####", "#....", "#....", "####.", "#....", "#....", "#...."],
    "N": ["#...#", "##..#", "##..#", "#.#.#", "#..##", "#..##", "#...#"],
    "C": [".####", "#....", "#....", "#....", "#....", "#....", ".####"],
    "2": [".###.", "#...#", "....#", "...#.", "..#..", ".#...", "#####"],
}
GOLD = [(255, 246, 208), (255, 224, 138), (242, 193, 78), (216, 154, 50), (168, 106, 34)]
BLUE = [(240, 248, 255), (191, 224, 255), (122, 184, 240), (74, 134, 208), (47, 90, 160)]
INK = (22, 16, 28)


def logo(text="TOWER DEFENCE 2D", accent_from=14, unit=3):
    """Same construction as tools/art/gen_ui_art.py make_logo, returned as RGBA art pixels."""
    cols = []
    for i, ch in enumerate(text):
        if ch == " ":
            cols.append((np.zeros((7, 3), bool), False)); continue
        cols.append((np.array([[c == "#" for c in r] for r in FONT[ch]]), i >= accent_from))
        cols.append((np.zeros((7, 1), bool), False))
    width = sum(c.shape[1] for c, _ in cols) * unit
    pad = 3
    H, W = 7 * unit + pad * 2 + 3, width + pad * 2
    mask = np.zeros((H, W), bool); acc = np.zeros((H, W), bool)
    x = pad
    for g, a in cols:
        big = np.kron(g, np.ones((unit, unit), bool))
        mask[pad:pad + 7 * unit, x:x + big.shape[1]] = big
        acc[pad:pad + 7 * unit, x:x + big.shape[1]] = a
        x += big.shape[1]
    ys = np.mgrid[0:H, 0:W][0]
    t = np.clip((ys - pad) / (7 * unit - 1), 0, 1)
    bay = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0
    bay = np.tile(bay, (H // 4 + 1, W // 4 + 1))[:H, :W]
    band = np.clip((t * 4 + (bay - 0.5) * 0.9 + 0.5).astype(int), 0, 4)
    rgb = np.where(acc[..., None], np.array(BLUE)[band], np.array(GOLD)[band]).astype(np.float32)
    top = mask & ~np.roll(mask, 1, 0)
    rgb[top] = 255
    alpha = np.where(mask, 255.0, 0.0)
    dil = mask.copy()
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            dil |= np.roll(np.roll(mask, dy, 0), dx, 1)
    ink = dil & ~mask
    rgb[ink] = INK; alpha[ink] = 255
    solid = mask | ink
    sh = np.roll(solid, 2, 0) & ~solid
    rgb[sh] = (5, 5, 10); alpha[sh] = 150
    return Image.fromarray(np.dstack([rgb, alpha]).astype(np.uint8), "RGBA")


def stacked_logo():
    a, b = logo("TOWER", 99), logo("DEFENCE 2D", 8)
    im = Image.new("RGBA", (max(a.width, b.width), a.height + b.height - 4), (0, 0, 0, 0))
    im.alpha_composite(a, ((im.width - a.width) // 2, 0))
    im.alpha_composite(b, ((im.width - b.width) // 2, a.height - 4))
    return im


def paste_logo(img, cx, cy, frac, glow=True, stacked=False):
    """Paste the logo at frac of the image width (integer pixel scale), centred at (cx, cy)."""
    lg = stacked_logo() if stacked else logo()
    px = max(1, int(img.width * frac / lg.width))
    lg = lg.resize((lg.width * px, lg.height * px), Image.NEAREST)
    x, y = int(cx - lg.width / 2), int(cy - lg.height / 2)
    if glow:
        a = lg.split()[3].point(lambda v: 255 if v > 200 else 0)
        halo = Image.new("RGBA", img.size, (0, 0, 0, 0))
        halo.paste(Image.new("RGBA", lg.size, (255, 190, 90, 150)), (x, y), a)
        halo = halo.filter(ImageFilter.GaussianBlur(px * 6))
        img.alpha_composite(halo)
        dark = Image.new("RGBA", img.size, (0, 0, 0, 0))
        dark.paste(Image.new("RGBA", lg.size, (0, 0, 0, 160)), (x, y + px), a)
        img.alpha_composite(dark.filter(ImageFilter.GaussianBlur(px * 3)))
        # Darken the band behind the logo so it reads on any background.
        band = Image.new("L", img.size, 0)
        ImageDraw.Draw(band).ellipse((x - px * 20, y - px * 14, x + lg.width + px * 20, y + lg.height + px * 22), fill=170)
        band = band.filter(ImageFilter.GaussianBlur(px * 14))
        img.alpha_composite(Image.merge("RGBA", (*[Image.new("L", img.size, 6)] * 3, band)))
    img.alpha_composite(lg, (x, y))
    return (x, y, lg.width, lg.height)


