# Sound effects synthesiser

`build.py` renders every sound effect of the game from code into `assets/audio/sfx/<group>/` as Ogg Vorbis,
and writes `assets/audio/sfx/catalogue.json` for the game's `Sfx` autoload.

```
pip install numpy scipy soundfile        # and ffmpeg with libvorbis on the PATH
python3 tools/sfx/build.py               # everything (about 20 s on 4 cores)
python3 tools/sfx/build.py --only tower_,impact_   # names containing any of these
python3 tools/sfx/build.py --list        # the catalogue with a line on each sound
python3 tools/sfx/build.py --preview DIR # also MP3 copies and DIR/preview.json, for a listening page
```

Rendering is deterministic: each file's random numbers are seeded from its name, so the same code always
gives the same sound.

## Licence

Nothing here uses recordings, samples, sound libraries or AI audio models. Every sound is built from
oscillators, filtered noise, resonators and envelopes in `dsp.py` and `voice.py`, so the output is original
work of this project and can ship in the commercial game with no credit or fee owed to anyone. The Python
libraries used to render (numpy, scipy, soundfile, ffmpeg) put no conditions on what they render.

## How it is laid out

- `dsp.py`: oscillators, noise, envelopes, static and swept filters, modal resonators (struck bodies),
  crackle, Karplus-Strong strings, distortion and a synthetic reverb, plus building blocks such as `thump`,
  `whoosh`, `boom`, `debris` and `bubbles`.
- `voice.py`: the creature voices. A glottal source with jitter, shimmer and a sub-octave growl runs through
  three swept formant filters that glide from vowel to vowel, with noise consonants in between. Each boss has
  a `Character` (pitch, throat size, roughness, breath, stacked voices, an effect such as water, stone, fire,
  wind, wood, void or cosmos). `phrase()` makes up speech in no real language (the story's subtitles carry
  the meaning), `roar()` a sustained roar and `song()` sung notes (the Pale Vesper sings).
- `recipes/palette.py`: shared instruments (synth brass, bells, chimes, gong, taiko, braam, riser, choir)
  and the six element palettes: an attack, an impact and a sustained texture for each element.
- `recipes/combat.py`: one attack sound for every tower in `data/towers`, built from its elements and how it
  fights (chains crackle, knockback adds a push, duals and triples are heavier). New towers get a sound
  automatically on the next build. Also impacts, explosions by splash size, armour clanks, enemy deaths,
  splitting, summoning and status effects.
- `recipes/events.py`: interface sounds, building and upgrading, wave horns, victory and defeat, the base
  being hit, the low-lives warning and the six player skills.
- `recipes/bosses.py`: a set of five sounds (reveal, footsteps, voice, enrage, death) for each boss: the six
  Heralds, the Ashen Regent, the Sundered Heart and Vael-Orrun as the lore describes them, one set per
  element for the corrupted Wardens, and the plain Warden. Also the boss tricks of the story branch
  (silence, blink, escape), a citadel building collapsing and the assault's horn.

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
- A new boss needs a `BossSet` in `recipes/bosses.py` with its enemy ids; a new ordinary enemy can get a
  death sound in `ENEMY_DEATHS` (otherwise it falls back by its tags).

Then rerun `build.py` and `godot --headless --import`. `tests/game/test_sound.gd` checks that every tower,
enemy, boss and skill in `data/` has its sounds and that every file loads.

You can't listen in a cloud session, so check new sounds by their numbers (`build.py` prints length, peak
and loudness) and by spectrogram, then ask someone to listen.
