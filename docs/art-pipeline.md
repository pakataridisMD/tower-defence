# Art pipeline: Blender to sprite sheets

Tower art is modelled in Blender **from Python scripts** and rendered to sprite sheets that the game
draws in 2D. The default output is **hi-bit pixel art** aimed at the look of Graveyard Keeper,
Romestead and Emberville: chunky readable shapes, a warm shared palette with hue-shifted shading,
dark ink outlines and rich lighting. This is the "3D to pixel art" technique Dead Cells made famous:
render the model large, shrink it by a whole factor, snap every pixel to the palette and outline it. Nothing is hand-placed in the Blender UI, so every tower is reproducible, diffable and
easy for Claude (or you) to tweak: change a number, re-run, and the sheet updates.

```
art/blender/
  kit.py               camera, lights, render settings, materials, mesh helpers (shared)
  render_tower.py      renders one tower to assets/sprites/towers/<id>/
  pixelate.py          shrink, palette snap, outline and flat shadows (numpy only)
  towers/<id>.py       one file per tower: builds the model and its idle animation
assets/sprites/towers/<id>/
  <id>.png             the sheet (Git LFS)
  <id>_n.png           matching normal map sheet (pixel style), for Godot 2D lighting
  <id>.json            frame size, anchor, directions, frames, fps, filter
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

Then open Godot once so it imports the new PNG, and commit the PNG, its `.import` file and the JSON.

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
  it. This is how Graveyard Keeper-style lighting works on pixel art; nothing uses it yet, but it is
  ready for a day-night cycle and glowing towers.

## Adding a tower

1. Copy `art/blender/towers/fire_brazier.py` or `storm_spire.py` to `towers/<tower id>.py` (the id from `data/towers`).
2. Build the base from `kit.cylinder`, `kit.tube`, `kit.bowl` and the material helpers, and parent
   anything that aims to the head pivot. Keep the footprint inside a radius of about 0.43.
3. Iterate with `--preview` until it looks right, then render the sheet.
4. Nothing else is needed in the game: `TowerSpriteSet.for_tower(id)` finds the art, the board draws
   it and the shop uses a close-up as the button icon. Towers without art keep their placeholder shapes.

## In the game

`scripts/game/tower_sprite_set.gd` loads a sheet and its JSON, and draws pixel art with nearest
filtering and HD sheets with mipmaps. `BoardView` draws each tower's frame
for its `SimTower.facing` angle (the direction of its last attack), sorted by height so nearer towers
overlap the ones behind them, and offsets the animation per tower so neighbours do not flicker in
sync. `tests/unit/test_tower_sprite_set.gd` checks every sheet against its JSON.

When the game gets an export preset, add `*.json` to its non-resource export filter, or the sprite
JSON files will be left out of the build.

## Recommendations: getting great art for the whole game

Research from November 2026 (web articles, tool sites and posts on X; X itself blocks direct reading,
so only search summaries were used from there).

1. **Pre-rendered 3D turned into pixel art, as here, is the best fit for towers.** Dead Cells
   built its whole look this way, and the lighting-rich pixel art of Graveyard Keeper and Romestead
   is the target. Hand touch-ups in Aseprite on top of the renders are the usual last 10%. It is how many polished 2D games get
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
