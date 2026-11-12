# Cinema: trailers and cinematics rendered in Godot

Design draft. Nothing here is used by the game yet.

This folder is its own small Godot 4.7 project (the game skips it through `.gdignore`). It stages trailer and story
shots with the game's own pixel art and renders them offline with Godot's Movie Maker, so every frame is perfect
however heavy the lights, fog and particles are.

## Layout

| Path | What |
|---|---|
| `kit/director.gd` | Plays a film: one timeline of shots, overlay (flash, subtitles, title cards, letterbox) and post pass (grade, vignette, grain, impact frames, chromatic aberration). |
| `kit/stage.gd` | One shot's stage: parallax camera rig over depth layers, and builders for split stills, animated lit actors, people, lights, glows, fog, sky, ridges, drifting particles, bursts and lightning. |
| `kit/*.gdshader` | Smooth pixel-art sampling (with and without normal maps), sky, fog, post. |
| `films/seven_crowns.gd` | The 78 s "War of Seven Crowns" story trailer, 18 shots. |
| `films/cutscene.gd` | Any game cutscene, built from `data/story/cinematics/<SCENE>.json`, its images, voice lines and music cue. `films/scenes/<SCENE>.gd` can stage single shots by hand (`func shot_NN(st, init, info)`). |
| `art/stills/<cinematic>_<NN>/` | Story stills split into depth layers (`0.png` back ... `front`), made by `tools/layer_stills.py`. |
| `art/anim`, `art/people`, `art/land` | Copies of the pix2d sprites (with normal maps), hero figures and landing art. |
| `fonts/Cinzel.ttf` | Cinzel by Natanael Gama, SIL Open Font License 1.1 (free for commercial use). |
| `render.sh` | Renders a film in parallel chunks, joins them, adds bloom and the audio. |

## Render

```sh
godot --headless --path cinema --import            # once
GODOT=godot cinema/render.sh out.mp4 cinema/audio/seven_crowns_mix.ogg seven_crowns
```

A game cutscene builds its own sound (music ducked under each voice line):

```sh
SCENE=earth_herald GODOT=godot cinema/render.sh earth_herald.mp4 auto cutscene
```

`STORY_ROOT=<other checkout>` takes the story data, images and voices from another branch.

On a Mac or PC with a graphics card this runs close to real time. In a cloud box without a GPU it falls back to
`xvfb-run` + software OpenGL and takes about 1 to 2 hours for 78 s.

Quick checks: `CINE=seven_crowns T0=38 T1=38.1 godot --path cinema --write-movie /tmp/f.png --fixed-fps 30`
renders three frames from 38 s. `T0`/`T1` limit any render to part of the film.

## Writing a shot

A shot is `func my_shot(st, init: bool)`. When `init` is true it builds its stage; afterwards it animates from
`st.t` (0 to `st.T`). Set `st.cam` and `st.k` (zoom) for the camera, and `st.ambient`, `st.flash`, `st.impact`,
`st.shake_amount`, `st.light_flash`, `st.fade`, `st.subtitle(...)` and `st.card(...)` for the look. World units are
the 640x360 still space; a layer with parallax `p` moves `p` times as far as the focal plane when the camera moves.

## Splitting stills into layers

`tools/layer_stills.py` replays a still from `tools/art/pix2d/stills.py` (art branch), snapshots the canvas after
every painting call and cuts it into depth layers where `CUTS` says. Far layers keep their full picture behind near
ones, so parallax never opens holes. Run it on a checkout that has the stills painter:

```sh
python3 cinema/tools/layer_stills.py --list prologue 7     # see the calls of one still
python3 cinema/tools/layer_stills.py                        # write every still in CUTS
```

Bloom is added in ffmpeg (blend in RGB with `format=gbrp`, or colours shift purple).

`audio/seven_crowns_mix.ogg` is the finished sound of the v2 trailer (music, Elariel voice, effects), so the picture can be compared shot for shot.
