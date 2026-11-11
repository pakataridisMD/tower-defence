# 2D pixel-art creatures (design only, not in the game)

Look approved by Doctor Paris on 2026-11-11. Nothing here is wired into the game yet.

Fourteen creatures (soldier/footman, orc, skeleton, golem, dragon, elf, dwarf, ghost and six elemental orbs) drawn
directly as pixel art by `tools/art/pix2d/`:

- `kit.py` paints each part (ellipse, polygon, capsule) as a rounded, cel-shaded form lit from the upper left with a
  hue-shifted colour ramp, adds a dark line where parts overlap and an ink outline, and writes a normal map.
- `creatures.py` has one function per creature. Each names its pose groups (`s.g("leg_n", x, y)`, `weapon`, `head`,
  `wing`, `tail`...) and the joint each group turns about.
- `gen.py` writes the rest poses here (`<name>.png`, `<name>_n.png`).
- `anim.py` writes walk (8 frames), attack (6) and death (6) strips to `anim/` with normal maps and `anim.json`
  (frame size, feet point, fps). Every frame is redrawn from the shapes, never rotated from finished pixels.

Rebuild: `python3 tools/art/pix2d/gen.py && python3 tools/art/pix2d/anim.py`.
