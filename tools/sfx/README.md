# Sound effects

`build.py` renders every sound effect of the game into `assets/audio/sfx/<group>/` as Ogg Vorbis, and writes
`assets/audio/sfx/catalogue.json` for the game's `Sfx` autoload. Sounds are designed from real recordings
(orchestral percussion and brass, found sounds, a sampled choir) and spoken lines, layered the way film and
game sound designers build them, plus code-made noise, crackle and sub-bass.

```
tools/sfx/fetch_samples.sh               # once: recordings and the voice model into tools/sfx/.samples (~2.5 GB)
pip install numpy scipy soundfile kokoro-onnx   # plus ffmpeg (libvorbis, rubberband) and fluidsynth + fluid-soundfont-gm
python3 tools/sfx/build.py               # everything (about 2 minutes on 4 cores)
python3 tools/sfx/build.py --only boss_,skill_   # names containing any of these
python3 tools/sfx/build.py --list        # the catalogue with a line on each sound
python3 tools/sfx/build.py --preview DIR # also MP3 copies and DIR/preview.json, for a listening page
```

Rendering is repeatable: each file's random numbers are seeded from its name, and generated speech and choir
notes are cached in `tools/sfx/.cache`, so the same code gives the same sounds.

## Licence

See `assets/audio/sfx/LICENSE.md`. The recordings are VSCO 2 Community Edition (CC0), the choir is the
FluidR3_GM sound font (MIT) and the voices are Kokoro-82M text to speech (Apache-2.0). All of them allow use
in a commercial game. The voices count as AI-generated audio for Steam's disclosure.

## How it is laid out

- `samples.py`: loads VSCO recordings (trimmed to their attack, normalised), pitch changes (tape-style
  `semis`/`speed`, and Rubber Band `stretch` that keeps the timing), Kokoro speech (`speak`, voices can be
  blended) and the sampled choir (`choir`, rendered by FluidSynth).
- `kit.py`: recorded building blocks: timpani, giant drums, bass drums, cymbals and swells, gongs and tam-tams,
  bowed cymbals, scrapes, metal, glass, chains, brick, bubbles, zaps, wood; real brass and string notes at any
  pitch (`note`, `held`, `chord`); and composites: the cinematic `impact` (sub drop, giant drum, bass drum,
  timpani, crash), the low-brass `braam`, `riser`, `debris`, `water_rush`, `hall`.
- `creature.py`: boss voices. A spoken line is shifted down in pitch and formants, doubled an octave down,
  given a whisper double of the same words, distorted in parallel, rasped like a huge throat and put in a big
  room. `roar()` pushes a shouted vowel much further and layers a hand-rubbed bass drum (throat), a trombone
  blat (bark) and a sub that follows the voice.
- `dsp.py`: oscillators, noise, envelopes, filters, distortion, a synthetic reverb and helpers such as
  `whoosh` and `crackle`.
- `recipes/textures.py`: element beds (sea surge, furnace roar, grinding stone, wind and thunder, creaking
  wood, the void's hum) and short element bursts, all from recordings.
- `recipes/palette.py`: the six element palettes: a tower attack and a shot impact for each element.
- `recipes/combat.py`: one attack sound for every tower in `data/towers`, built from its elements and how it
  fights (chains crackle, knockback adds a push, duals and triples are heavier). New towers get a sound
  automatically on the next build. Also impacts, explosions by splash size, armour clanks, enemy deaths
  (short spoken cries), splitting, summoning and status effects.
- `recipes/events.py`: interface sounds (drum-skin presses, no chimes), building and upgrading (brass stabs,
  choir), war-horn wave calls, victory and defeat, the base being rammed, the low-lives warning and the six
  player skills.
- `recipes/bosses.py`: five sounds (reveal, footsteps, voice, enrage, death) for each boss. The Heralds, the
  Ashen Regent, the Sundered Heart and Vael-Orrun speak lines from the story (`lines` in each `BossSet`); the
  Leviathan and the Broodmother only roar; the corrupted Wardens are doubled by Vael-Orrun's whisper and
  their deaths end in a choir chord, because beating them frees them. Also the boss tricks of the story
  branch (silence, blink, escape), a citadel building collapsing and the assault's horns.

## Adding or changing a sound

Write a recipe that returns a numpy array (mono, or stereo as shape (n, 2)) and register it:

```python
@sound("ui_click", "ui", variants=2, loud=-24.0, max_voices=2, min_gap=0.03, bus="Ui", positional=False)
def ui_click(rng, v):
    ...
```

- `loud` is the render loudness (the loudest 200 ms, LUFS-like). Rendering trims silence, normalises to
  it and keeps peaks under -1 dBFS.
- `volume_db`, `bus`, `positional`, `max_voices`, `min_gap`, `pitch_jitter`, `priority`, `duck_db` and
  `duck_time` go into the catalogue and control how the game plays it.
- A new boss needs a `BossSet` in `recipes/bosses.py` with its enemy ids, a `Voice` and its lines; a new
  ordinary enemy can get a death sound in `ENEMY_DEATHS` (otherwise it falls back by its tags).
- To change what a boss says, edit its `lines` and rerender: the speech is generated again.

Then rerun `build.py` and `godot --headless --import`. `tests/game/test_sound.gd` checks that every tower,
enemy, boss and skill in `data/` has its sounds and that every file loads.

You can't listen in a cloud session, so check new sounds by their numbers (`build.py` prints length, peak
and loudness) and by spectrogram, then ask someone to listen. Godot 4.7 runs in cloud sessions for the
import and the tests (see the repo notes).
