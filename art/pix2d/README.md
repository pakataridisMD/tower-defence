# 2D pixel-art creatures (design only, not in the game)

Look approved by Doctor Paris on 2026-11-11. Nothing here is wired into the game yet.

Fourteen creatures (soldier/footman, orc, skeleton, golem, dragon, elf, dwarf, ghost and six elemental orbs) drawn
directly as pixel art by `tools/art/pix2d/`:

- `kit.py` paints each part (ellipse, polygon, capsule) as a rounded, cel-shaded form lit from the upper left with a
  hue-shifted colour ramp, adds a dark line where parts overlap and an ink outline, and writes a normal map.
- `creatures.py` has one function per creature. Each names its pose groups (`s.g("leg_n", x, y)`, `weapon`, `head`,
  `wing`, `tail`...) and the joint each group turns about.
- `gen.py` writes the rest poses here (`<name>.png`, `<name>_n.png`).
- `anim.py` writes idle (6 frames), walk (8), attack (8) and death (8) strips to `anim/` with normal maps and
  `anim.json` (frame size, feet point, fps). Groups chain through joints (thigh > shin, upper arm > forearm > weapon,
  neck > head > jaw, tail > tail tip) and loose parts (plume, cloak, hair, beard) trail the motion. Every frame is
  redrawn from the shapes, never rotated from finished pixels.

Rebuild: `python3 tools/art/pix2d/gen.py && python3 tools/art/pix2d/anim.py`.
