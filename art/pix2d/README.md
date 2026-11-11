# 2D pixel-art test (design only, not in the game)

Five test creatures (soldier, orc, skeleton, golem, dragon) drawn directly as pixel art by `tools/art/pix2d/`:
`kit.py` paints each part (ellipse, polygon, capsule) as a rounded, cel-shaded form lit from the upper left with a
hue-shifted colour ramp, adds a dark line where parts overlap and an ink outline, and writes a normal map;
`creatures.py` has one function per creature. Rebuild with `python3 tools/art/pix2d/gen.py`.
