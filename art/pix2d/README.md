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

## Story bosses (design only)

`tools/art/pix2d/bosses.py` (the six Heralds, Cinder Tyrant, Vael-Orrun), `wardens.py` (Mountain Titan, Thunderhead,
Elder Broodmother, Tidal Leviathan, Hollow King and its Hollow Shade) and `final_bosses.py` (Cassivane the Ashen
Regent, the Sundered Heart, the Gatemaw, the Mirror Spire, the Crownless Throne and the six Echo-Heralds, which are
the Heralds redrawn as glassy grey reflections that flicker between the elements). All at 32 art px per board cell,
so they can go on the board without rescaling. Extra animation styles: `titan` (kneels and crumbles), `sink` (sea
beast goes down), `maw` (structures: the jaw or glyphs flare, then they crumble). `sheet.py` makes labelled review
sheets with the footman for scale.

Rebuild a boss: `python3 tools/art/pix2d/gen.py gatemaw && python3 tools/art/pix2d/anim.py gatemaw`.

## Cinematic stills (design only)

127 stills for all 33 story cinematics, one per shot, 640x360 (painted at 320x180 and doubled with whole pixels):
`stills/<cinematic id>/<NN>.png`, in the shot order of `data/story/cinematics/<id>.json`.

- `tools/art/pix2d/stills.py [ids] --out art/pix2d/stills [--sheet sheet.png]` renders them.
- `stills.py` holds the `Scene` painter, shared pieces (Solenne, flames, armies) and the prologue.
- `shots_lands.py` holds the six land campaigns; `shots_story.py` the main line from the Regent to the epilogue.
- Each shot function's docstring is its art note. Sprites are pasted at 1x, never scaled.
