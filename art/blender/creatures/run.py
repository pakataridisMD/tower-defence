"""Render creature modules to pixel sprites. usage: python run.py name [name...]  -> out/<name>.png (+ _big.png, _hd.png)"""
import importlib, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import ckit as k
import pixelate

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
for name in sys.argv[1:]:
    mod = importlib.import_module(name)
    k._mats.clear()
    s = k.reset()
    cfg = getattr(mod, "CAMERA", {})
    size = cfg.pop("size", 256) if "size" in cfg else 256
    k.setup(s, size=size, **{kk: v for kk, v in cfg.items() if kk != "size"})
    mod.build(k)
    hd = os.path.join(OUT, name + "_hd.png")
    k.render(s, hd)
    fr = np.asarray(Image.open(hd).convert("RGBA")).astype(np.float64) / 255
    px = pixelate.pixelate(fr, 4)
    im = Image.fromarray((np.clip(px, 0, 1) * 255).astype(np.uint8))
    im.save(os.path.join(OUT, name + ".png"))
    im.resize((im.width * 5, im.height * 5), Image.NEAREST).save(os.path.join(OUT, name + "_big.png"))
    print("done", name, im.size)
