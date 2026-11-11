"""Writes the main menu's art into assets/art/menu/ and the pixel fonts into assets/fonts/.

    python3 tools/art/menu/gen_menu_assets.py

- backdrop.png: Solenne at dusk, 1920x1080 (painted at 640x360, x3, with bloom). Needs the 2D creature strips in
  art/pix2d/anim (tools/art/pix2d/anim.py).
- panel.png, button_<state>.png, tab_<state>.png: 9-slice pictures already doubled to screen pixels. The
  middle and edges are tiled, not stretched (UiStyle sets axis_stretch to TILE), so the dither stays crisp.
- icon_<name>.png (32x32), lock.png: small pictures for menu buttons.
- Fonts are copied from PIXEL_FONTS (SIL Open Font License; the licence text goes next to them).
"""
from __future__ import annotations

import os
import shutil
import sys

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)
import ui as U  # noqa: E402

OUT = os.path.join(ROOT, "assets", "art", "menu")
FONTS = os.path.join(ROOT, "assets", "fonts")
SCALE = 2


def cut(ui, box):
    x0, y0, x1, y1 = box
    im = ui.im.crop(box)
    return im.resize((im.width * SCALE, im.height * SCALE), Image.NEAREST)


def piece(draw, w, h):
    ui = U.UI()
    draw(ui, w, h)
    return cut(ui, (0, 0, w, h))


def main():
    os.makedirs(OUT, exist_ok=True)
    # 9-slices: 32 interface pixels square, corners of 8 (16 screen pixels)
    piece(lambda u, w, h: u.panel(0, 0, w, h), 32, 32).save(os.path.join(OUT, "panel.png"))
    piece(lambda u, w, h: u.panel(0, 0, w, h, ornate=False), 32, 32).save(os.path.join(OUT, "panel_plain.png"))
    for state, kind in (("normal", "normal"), ("hover", "hover"), ("pressed", "selected"), ("picked", "selected"),
                        ("disabled", "disabled")):
        def draw(u, w, h, kind=kind):
            u.button(4, 0, w, h, "", kind, marker=False)
        im = piece(draw, 36, 24).crop((4 * SCALE, 0, 36 * SCALE, 24 * SCALE))
        im.save(os.path.join(OUT, f"button_{state}.png"))
    for state, on in (("on", True), ("off", False)):
        ui = U.UI()
        ui.tabs(0, 0, [""], 0 if on else 1, w=32)
        cut(ui, (0, 0, 32, 24)).save(os.path.join(OUT, f"tab_{state}.png"))
    # icons
    for name in U.ICONS:
        ui = U.UI()
        ui.icon(name, 0, 0)
        cut(ui, (0, 0, 16, 16)).save(os.path.join(OUT, f"icon_{name}.png"))
    ui = U.UI()
    ui.lock(0, 0)
    cut(ui, (0, 0, 14, 17)).save(os.path.join(OUT, "lock.png"))
    # backdrop
    import pages
    pages.backdrop().convert("RGB").save(os.path.join(OUT, "backdrop.png"), optimize=True)
    # fonts
    os.makedirs(FONTS, exist_ok=True)
    for f in ("PirataOne-Regular.ttf", "Jersey10-Regular.ttf", "PixelifySans.ttf", "Silkscreen-Regular.ttf"):
        shutil.copy(os.path.join(U.FONT_DIR, f), os.path.join(FONTS, f))
    print("wrote", OUT, "and", FONTS)


if __name__ == "__main__":
    main()
