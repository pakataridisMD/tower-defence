# Creature test: Blender to pixel art (design only, not in the game)

Five test creatures (soldier, orc, skeleton, golem, dragon) modelled in Blender from Python and rendered to pixel sprites.

- `ckit.py`: scene, camera and lights; `skin()` builds smooth organic bodies from a few points with radii (Skin + Subdivision
  modifiers); `prim()` adds hard parts (armour, weapons, horns); `mat()` makes materials.
- `<creature>.py`: one file per creature, a `CAMERA` dict and a `build(k)` function.
- `run.py`: renders at 256 px (dragon 384), shrinks 4x, snaps to the shared palette and inks the outline (`pixelate.py`,
  the same finish as the tower pipeline).

Setup: `uv venv --python 3.13 venv && uv pip install --python venv/bin/python bpy==5.2.3 numpy pillow`, then
`venv/bin/python art/blender/creatures/run.py soldier orc skeleton golem dragon` (about 2 to 5 s each). Output goes to
`art/blender/creatures/out/` (not committed).
