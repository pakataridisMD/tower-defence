# Story music

Original orchestral score for the story cinematics: ten cues built from three themes, written as
text scores in `cues/` and rendered with a small sampler. Everything here is design work for review.

## Licensing (safe to sell on Steam)

| Part | Source | Licence |
|---|---|---|
| Melodies, harmony, orchestration | written for this game in `cues/*.py` | ours |
| Strings, brass, woodwinds, harp, timpani, percussion | Versilian Studios Chamber Orchestra 2, Community Edition (`fetch_samples.sh`) | CC0 1.0 (public domain), no attribution needed |
| Choir, celesta, tubular bells | FluidR3_GM soundfont (Debian `fluid-soundfont-gm`), played by FluidSynth | MIT |

No AI music model and no existing score was used. The themes are written to evoke the
epic-fantasy film tradition (folk tunes for home, horn calls for hope, low brass in odd metres for
the enemy) without borrowing any melody. The rendered `.ogg` files are ours to sell; a credits line
for Versilian Studios is a courtesy, not a requirement.

## The themes

| Theme | What it means | Shape | First heard |
|---|---|---|---|
| **The Lantern** | hope, the Order of the Spire, Oswin | rising fifth, then a stepwise fall: `D A | G F# E D | B E F# | E` | horn, prologue shot 4 |
| **The Long Defeat** | the Lantern in the minor: losing ground, saving people | `D A | G F E D | Bb E F | E` | prologue shot 11 |
| **Solenne** | home, the Crowned Heart | a 6/8 folk tune for flute and harp, in F | prologue shot 5 |
| **The Hollow** | Vael-Orrun and his Heralds | a falling tritone in low brass (`D Ab | G Bb A Eb`) over a 5/4 string ostinato | prologue shot 3 |
| **The Seventh Colour** | the mystery after the end | D major with a raised fourth (G#) and a major seventh | epilogue, last chord |

## The cues

`assets/story/music/cinematic_music.json` says which cue plays under each of the 33 cinematics.

| Cue | Title | Length | Plays under |
|---|---|---|---|
| `prologue` | The Last Lantern | 2:59 | `prologue`, scored shot by shot to the narration |
| `hold_the_road` | Hold the Road | 0:52 | the six land intros, `convergence_intro` |
| `herald` | The Heralds of the Hollow | 0:57 | the six Herald scenes, `crossroads` |
| `warden_freed` | Freed | 0:54 | the six Warden scenes, `lumen_gate` |
| `solenne` | The Crowned Heart | 1:22 | `regents_counsel`, `capital_prelude` |
| `falling_stars` | The Night of Falling Stars | 1:58 | `night_of_falling_stars`, shot by shot |
| `long_night` | There Was No Dawn | 0:57 | `long_night`, `solenne_falls` |
| `white_lantern` | The White Lantern | 1:20 | `dawn`, `heart_falls` |
| `citadel` | The Crownless Citadel | 1:11 | `assault_intro`, `mirror_spire`, `crownless_throne` |
| `epilogue` | The Seventh Colour | 1:28 | `epilogue` |

Each cue ships as `<cue>.ogg` (44.1 kHz stereo, -18 LUFS integrated, true peak at most -1 dBFS, so the
narrator sits on top), `<cue>.json` (length and section markers, so shots can be timed to the music)
and `<cue>.mid` (the score as MIDI, so a composer can re-voice it with a commercial library later).

Playback: start the cue with the cinematic, fade it out over about 1.5 s if the scene ends first,
and duck it 6 to 8 dB under narration.

## Rendering

    sudo apt-get install fluidsynth fluid-soundfont-gm ffmpeg
    pip install numpy scipy soundfile mido
    tools/music/fetch_samples.sh                 # about 5 GB, into tools/music/.samples (ignored)
    python3 tools/music/render.py --all          # or a cue name; add --stems for per-part WAVs
    python3 tools/music/levels.py prologue       # per-section stem levels (after --stems)

MP3 previews land in `tools/music/out/` (ignored). A cue renders in 10 to 45 seconds.

## Writing music

A cue is a `Score` of `Section`s, each with its own metre and tempo (or `seconds=` to fit a shot).
Parts are written one line of music per string, for example
`"D4:2 A4:2 | G4:1.5 F#4:.5 E4 D4 | B3+D4+G4:4"`: pitch and length in beats, `+` for chords,
`r` for rests, `~` to tie, `'` for short, `>` for accents, `!pp`..`!fff` for dynamics. Bar lines are
checked against the metre, so a wrong rhythm fails loudly. See `score.py` for the full notation and
`cues/_kit.py` for the orchestra seating and the themes.

## Next steps worth considering

- The sampler is good for direction and timing, not for a final release mix. For launch, either
  re-render the MIDI with a commercial-licence library (for example Spitfire BBC Symphony Orchestra
  Discover or Core, whose licences allow use in sold games), or hire a composer/orchestrator to
  produce the final mix from these themes.
- Gameplay music (menus, battle loops per element) can reuse the same themes and tools.
