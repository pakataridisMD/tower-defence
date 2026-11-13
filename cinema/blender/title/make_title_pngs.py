"""Draw the trailer's title-card text layers as transparent 1920x1080 PNGs (run once, where Pillow is installed).

    python3 make_title_pngs.py
cut_trailer.py lays these over black, so the Mac's ffmpeg doesn't need the drawtext filter."""
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT = os.path.join(HERE, "..", "..", "..", "assets", "fonts", "PirataOne-Regular.ttf")
W, H = 1920, 1080


def layer(name, text, size, colour, centre_y):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img); f = ImageFont.truetype(FONT, size)
    x0, y0, x1, y1 = d.textbbox((0, 0), text, font=f)
    d.text(((W - (x1 - x0)) / 2 - x0, centre_y - (y1 - y0) / 2 - y0), text, font=f, fill=colour)
    img.save(os.path.join(HERE, name))


layer("title.png", "HOLD THE ROAD", H // 6, (0xE8, 0xD9, 0xB0, 255), H / 2 - H // 14)
layer("credit.png", "Developed by Pasiv Production", H // 22, (0x9A, 0x90, 0x80, 255), H / 2 + H // 10 + H // 44)
