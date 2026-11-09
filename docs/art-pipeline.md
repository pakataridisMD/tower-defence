# Art pipeline: Blender to sprite sheets

This is a second way to make tower art, next to the hand-coded pixel art that the game draws today
(`tools/art/gen_game_art.py`, drawn by `scripts/game/board_art.gd`). Towers are modelled in Blender
**from Python scripts** and rendered to sprite sheets. It is not wired into the game yet; see
"Feeding renders into the game" below. The default output is **hi-bit pixel art** aimed at the look of Graveyard Keeper,
Romestead and Emberville: chunky readable shapes, a warm shared palette with hue-shifted shading,
dark ink outlines and rich lighting. This is the "3D to pixel art" technique Dead Cells made famous:
render the model large, shrink it by a whole factor, snap every pixel to the palette and outline it.

Nothing is hand-placed in the Blender UI, so every tower is reproducible, diffable and
easy for Claude (or you) to tweak: change a number, re-run, and the sheet updates.

```
art/blender/
  kit.py               camera, lights, render settings, materials, mesh helpers (shared)
  render_tower.py      renders one tower to art/blender/out/<id>/ (not committed)
  pixelate.py          shrink, palette snap, outline and flat shadows (numpy only)
  towers/<id>.py       one file per tower: builds the model and its idle animation
art/blender/out/<id>/
  <id>.png             the sheet: one row per aim direction, one column per animation frame
  <id>_n.png           matching normal map sheet (pixel style), for Godot 2D lighting
  <id>.json            frame size, anchor, directions, frames, fps, filter
docs/art-pipeline/     sample sheets for the Fire Brazier and Storm Spire
```

## Rendering a tower

Either use Blender 5.2 (or newer) itself:

```sh
blender -b -P art/blender/render_tower.py -- fire_brazier
```

or the `bpy` module, which is Blender packaged for Python 3.13 (no Blender install needed):

```sh
python3.13 -m venv ~/bpyenv && ~/bpyenv/bin/pip install bpy==5.2.3
~/bpyenv/bin/python art/blender/render_tower.py fire_brazier
```

A pixel-art sheet (16 directions x 8 frames) takes about 8 minutes on 4 CPU cores, much less with
a GPU. Useful options:

| Option | What it does |
| --- | --- |
| `--style hd` | Smooth 256 px frames drawn at half size, instead of pixel art. |
| `--preview out.png` | One frame (pixel art blown up 8x), plus `out_board.png` on the game's board colour. Use this while modelling (about 4 s). |
| `--directions 8 --frames 4` | Fewer frames for quick checks. |
| `--samples 32` | Faster, noisier renders (the denoiser cleans most of it up). |
| `--no-outline` | Skip the dark outline pass. |


## Conventions

- **One board cell is 1 Blender unit.** The game's cells are 64 screen pixels and a frame is 2 cells
  wide. Pixel art frames are 64 px (32 art pixels per cell), drawn at 2x with nearest filtering, so
  one art pixel is 2x2 screen pixels at 1080p. HD frames are 256 px drawn at half size.
- **One palette for everything.** `pixelate.py` builds 12 ramps of 7 colours (stone, slate, earth,
  bronze, ember, blood, sun, moss, sea, storm, ice, arcane) plus ink and paper. Shadows lean violet
  and highlights lean warm, the way pixel artists hue-shift by hand. `palette_swatch()` exports it
  for Aseprite if you want to paint over a render. Every tower snaps to it, so the set stays coherent.
- **Calm textures for pixel art.** With `kit.FLAT` on (pixel style), stone and metal noise is larger
  and softer, because fine noise turns into speckle at 32 pixels per cell. Keep glows below clipping
  (see `GLOW` in `storm_spire.py`), or bright parts all snap to the same pale colour.
- **Fixed camera.** Orthographic, looking down at 50 degrees from the south. Every tower uses the same
  camera and the same three lights (warm key from the upper left, cool rim from behind, blue sky
  fill), so they look like one set. Change these in `kit.py` only, and re-render everything.
- **The head turns, the base does not.** Each tower module returns a `head` pivot. The renderer spins
  it through 16 screen directions. The yaw is corrected for the camera tilt, so row *d* really points
  at screen angle *d* x 22.5 degrees (0 = right, clockwise, like Godot).
- **Loops.** `animate(phase)` gets a phase from 0 to 1 and must look the same at 0 and 1. Move noise
  along a circle or use whole-number multiples of `phase * 2 * pi`, as `fire_brazier.py` does.
- **Shadows are baked in** with a shadow catcher. In pixel style they become one flat, see-through
  shadow colour, and solid parts get a one-pixel ink outline; glowing parts get a darker shade of
  their own colour instead, so fire and crystals keep a soft edge.
- **Standard view transform**, not AgX. AgX turns hot oranges pale pink at sprite size.
- **Normal maps come free.** Each frame is rendered a second time with every surface showing its
  camera-facing normal, then shrunk to the same pixels. Godot's `PointLight2D` and
  `DirectionalLight2D` use it, so a torch or a fire tower lights the stone on the side that faces
  it, the same way the game's hand-coded art is lit.

## Adding a tower

1. Copy `art/blender/towers/fire_brazier.py` or `storm_spire.py` to `towers/<tower id>.py` (the id from `data/towers`).
2. Build the base from `kit.cylinder`, `kit.tube`, `kit.bowl` and the material helpers, and parent
   anything that aims to the head pivot. Keep the footprint inside a radius of about 0.43.
3. Iterate with `--preview` until it looks right, then render the sheet.
4. To use it in the game, see "Feeding renders into the game" below.

## Feeding renders into the game

The game's art lives in `assets/art/game/` in the format `BoardArt` reads: one upright tower
picture (`towers/<id>.png`), its normal map (`_n.png`), a glow layer (`_glow.png`) and an entry in
`art.json` with the anchor, muzzle and light. A Blender tower can replace a hand-coded one by
exporting a frame in that format: take the frame facing down from the sheet, crop it to the tower,
split pixels brighter than the glow threshold into `_glow.png`, and write the anchor. The normal map
already uses the same convention (OpenGL, green up the screen).

The sheets also have 16 aim directions and an idle loop, which the hand-coded art does not. Using
them needs the board to turn towers towards their target and step through frames.

## Recommendations: getting great art for the whole game

Research from November 2026 (web articles, tool sites and posts on X; X itself blocks direct reading,
so only search summaries were used from there).

1. **Pre-rendered 3D turned into pixel art, as here, is the best fit for towers.** Dead Cells
   built its whole look this way, and the lighting-rich pixel art of Graveyard Keeper and Romestead
   is the target. Hand touch-ups in Aseprite on top of the renders are the usual last 10%. It gives
   consistent lighting, smooth rotations and animation for free. Claude is strongest at hard-surface
   and architectural shapes in code, which is exactly what towers are. Community advice for
   Claude + Blender is consistent: work in small steps, render a preview after each step and correct
   against the picture, and keep everything in scripts so a bad step is easy to undo.
2. **Blender MCP for live iteration.** With the Blender MCP add-on, Claude Desktop drives your own
   Blender: you watch the model appear, nudge it, and ask for changes. It fits the same scripts.
3. **Enemies and creatures: generate a mesh, then render it here.** Organic shapes are where code
   modelling is weakest. Image-to-3D tools (Tripo, Meshy, Hunyuan3D, Rodin) turn a concept image into
   a mesh; import it into this scene so it gets the same camera, lights and outline as the towers.
   Walk cycles can come from Mixamo-style auto-rigging.
4. **2D-only tools for icons, UI and backgrounds.** PixelLab (pixel art, rotations and animations) and
   Scenario (train a model on your own style) are the tools indie developers mention most for
   keeping 2D assets in one style.
5. **Pay an artist for the Steam capsule and key art.** The store capsule decides click-through more
   than anything in-game, and it is worth a human illustrator who can match the in-game look.
6. **Steam disclosure.** Since January 2026 Steam's form asks about AI-generated content that players
   see, not tools used behind the scenes. Art produced from AI-written scripts or AI-generated meshes
   is safest disclosed; check the current wording when you set up the store page.
