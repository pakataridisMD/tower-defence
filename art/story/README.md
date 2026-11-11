# Story art (design renders for review)

Portraits, animated battle sprites and cinematic stills for the campaign story. **None of this is loaded
by the game yet**: it is here for review, and gets copied into `assets/story/` once approved.

The cast and the shot list come from the lore thread: `data/story/characters.json`,
`data/story/cinematics/<id>.json` and `docs/story/`.

## Layout

| Path | What |
|---|---|
| `characters/<id>/portrait.png` | 96x96 bust on a painted background (`portrait_clear.png` without it) |
| `characters/<id>/<anim>_<n>.png` | battle sprite frames: idle 4, walk 6, attack 6, cast 6, hurt 2, death 6, facing right, with `_n.png` normal maps and `_glow.png` where something glows |
| `characters/<id>/sheet.png`, `preview.gif`, `card.png` | every animation on one sheet, played back, and a review card |
| `cinematics/<cinematic_id>/<NN>.png` | one 640x360 still per shot (painted at 320x180, shown 2x) |

## How it is made

`tools/art/story/` turns small 3D figures into pixel art, so every character gets the same light
direction, outline and hue-shifted shading as the towers and enemies, and every pose can be reused in a
cinematic:

- `sdf.py`: sphere-traces rounded primitives through an orthographic camera, lights them (key from the
  upper left as in `gen_game_art.py`, coloured rim, ambient occlusion), snaps light to per-material
  colour ramps, adds a 1 px ink outline, and writes normal and glow maps.
- `rig.py`: a humanoid rig with outfit parts (robes, plate, capes, hoods, hats, beards, horns, crowns,
  staffs, swords, lanterns) and the six animations.
- `cast.py`: one entry per character (materials, outfit, body, portrait framing).
- `cinema.py` + `shots_<cinematic>.py`: paint the stills (skies, ridges, cities, glows, smoke) and place
  characters, then finish at 320x180 with ordered dithering.

Commands (from the repository root, Python 3 with numpy and Pillow):

```
python3 tools/art/story/gen_story_art.py [ids...]          # characters
python3 tools/art/story/gen_cinematics.py [cinematic_id]   # stills
python3 tools/art/story/make_video.py prologue --json data/story/cinematics/prologue.json --out prologue.mp4
```

## Review sheets

`bosses.png` and `allies.png` put every boss and ally on one page (portrait, battle sprite, where they appear).
Rebuild with `python3 tools/art/story/boss_roster.py` and `--allies`.

## Ids when copying into the game

The cinematic player reads `assets/story/portraits/<id>.png` with ids from `data/story/characters.json`. Most folders
here already use those ids; the Heralds and a few others differ:

| here | game id |
|---|---|
| herald_ourra | saltmother |
| herald_gorrath | gorrath |
| herald_vesper | pale_vesper |
| herald_ashwick | ashwick |
| herald_vholt | vholt |
| herald_briar | mother_briar |
| oswin_grey / oswin_white | oswin |
| cassivane / cassivane_ashen | cassivane |
