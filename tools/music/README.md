# Story music

Original orchestral score for the story cinematics: ten cues built from three themes, written as
text scores in `cues/` and rendered with a small sampler. Everything here is design work for review.

## Licensing (safe to sell on Steam)

| Part | Source | Licence |
|---|---|---|
| Melodies, harmony, orchestration | written for this game in `cues/*.py` | ours |
| Strings, brass, woodwinds, harp, timpani, percussion | Versilian Studios Chamber Orchestra 2, Community Edition (`fetch_samples.sh`) | CC0 1.0 (public domain), no attribution needed |
| Choir, celesta, tubular bells | FluidR3_GM soundfont (Debian `fluid-soundfont-gm`), played by FluidSynth | MIT |
| Sung chant words and gang shouts (prologue) | Kokoro-82M text-to-speech voices, put on pitch by `vocals.py` | Apache-2.0 (commercial use allowed) |
| Braams, risers, impacts, sub drops | synthesised in `vocals.py` | ours |
| Synth pulse, pads, sub and bass; drum-ensemble booms | synthesised in `hybrid.py` (drum ensembles layer the CC0 VSCO drums) | ours |

No AI music model and no existing score was used. The chant and shout voices come from a
text-to-speech model (Kokoro), so they count as AI-generated audio for Steam's AI content
disclosure, the same as the narrator. The themes are written to evoke the
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
| `prologue` | The Last Lantern | 3:14 | `prologue`, scored shot by shot to the narration, with a trailer layer (sung chant, gang shouts in the gaps between lines, braams, risers, taiko) |
| `hold_the_road` | Hold the Road | 0:52 | the six land intros, `convergence_intro` |
| `herald` | The Heralds of the Hollow | 0:57 | the six Herald scenes, `crossroads` |
| `warden_freed` | Freed | 0:54 | the six Warden scenes, `lumen_gate` |
| `solenne` | The Crowned Heart | 1:22 | `regents_counsel`, `capital_prelude` |
| `falling_stars` | The Night of Falling Stars | 2:05 | `night_of_falling_stars`, shot by shot |
| `long_night` | There Was No Dawn | 0:57 | `long_night`, `solenne_falls` |
| `white_lantern` | The White Lantern | 1:20 | `dawn`, `heart_falls` |
| `citadel` | The Crownless Citadel | 1:11 | `assault_intro`, `mirror_spire`, `crownless_throne` |
| `epilogue` | The Seventh Colour | 1:28 | `epilogue` |
| `trailer`, `trailer_short` | Hold the Road (trailer) | 0:48, 0:23 | promo teaser and vertical short (hit at 0:42 and 0:19) |

Each cue ships as `<cue>.ogg` (44.1 kHz stereo, -18 LUFS integrated, true peak at most -1 dBFS, so the
narrator sits on top), `<cue>.json` (length and section markers, so shots can be timed to the music)
and `<cue>.mid` (the score as MIDI, so a composer can re-voice it with a commercial library later).

Playback: start the cue with the cinematic, fade it out over about 1.5 s if the scene ends first,
and duck it 6 to 8 dB under narration.

## Battle music (gameplay)

`loops/battle.py` is **Hold the Line**, the music under a run: a 96 s loop in D minor at 100 bpm,
in three layers that play in sync (`assets/game/music/battle_<layer>.ogg`, plus `battle.json`):

| Layer | When it plays | What it adds |
|---|---|---|
| `calm` | always (alone during the build phase) | pads, low strings, a harp ostinato, a ticking clock, the themes on solo cello, bassoon and horn |
| `wave` | while a wave is running | 16th-note string and synth ostinatos, the drum ensemble, synth bass, eight low horns on the themes |
| `boss` | the last wave, and at 30% of lives or less | choir, trumpets, a chanting male choir ("Te-ne-te vi-am"), more drums, braams |

Sections of 8 bars: the march (i-VI-III-VII), the Long Defeat, the Hollow, the full Lantern theme,
and the march again turning on the dominant back to the top. In the game, `scripts/game/battle_music.gd`
plays the layers as one `AudioStreamSynchronized` on the `Music` bus and fades them (in over 1.5 s,
out over 4 s). Loudness: calm alone about -24 LUFS, with the wave layer -18, everything -16.

    python3 tools/music/render_loop.py battle    # about 2 minutes

`render_loop.py` folds the reverb tail back onto the start so the loop has no seam, and gives
every layer the same gain and peak limiting, so any combination sums correctly.

### Boss waves

A boss wave gets its own, faster and nastier music, **The Hollow Comes**, in D Phrygian at 140 bpm:

- `loops/boss_entrance.py` is a one-shot stinger (`boss_entrance_hit.ogg`). It opens on a hit at 0.0 s:
  low brass on a tritone, a fff choir, a war-drum ensemble, gong, a braam and sub drop, and a sung
  cluster. Then come 2 bars of brass stabs, accelerating taiko and a riser into the downbeat at
  3 bars (5.143 s, `handover_seconds` in `boss_entrance.json`).
- `loops/boss.py` is the 55 s fight loop (`boss_fight.ogg`). It has a grinding 16th-note ostinato in
  3+3+2, taiko on 1, 2.5 and 4, snare 16ths and tom fills, and a male choir chanting the overlord's
  name ("Vail Or Run"). The Hollow theme is on eight horns, trombones and tuba against choirs a
  semitone apart, then trumpets, anvils and shouts. It ends with a ticking, whispered build that
  swells back into the top.

When a boss wave starts, `BattleMusic` cuts the battle layers out over 0.4 s and plays the
entrance. At `BattleMusic.ENTRANCE_SECONDS` it starts the boss loop. When the wave ends, the loop
fades out over 3 s and the calm layer comes back. Both are about -16 LUFS.

    python3 tools/music/render_loop.py boss boss_entrance    # about 1 minute

## Rendering

    sudo apt-get install fluidsynth fluid-soundfont-gm ffmpeg
    pip install numpy scipy soundfile mido
    tools/music/fetch_samples.sh                 # about 5 GB, into tools/music/.samples (ignored)
    python3 tools/music/render.py --all          # or a cue name; add --stems for per-part WAVs
    python3 tools/music/levels.py prologue       # per-section stem levels (after --stems)

MP3 previews land in `tools/music/out/` (ignored). A cue renders in 10 to 45 seconds.

## Film-trailer layer: hybrid orchestra

Every cue carries a modern epic film-score layer on top of the orchestra (in the manner of big
action scores; no melody or cue is borrowed). `hybrid.py` adds synth instruments that are written
like any part (`syn_pulse`, `syn_pad`, `syn_sub`, `syn_bass`) and drum ensembles used as
percussion kinds (`taiko`, `epic`, `toms`, `snare`, `tick`). `cues/_kit.py` has `ost16()`, a
16th-note string ostinato with 3+3+2 accents, and `film(score, section, bass, level, melody)`, which
adds the whole layer to a section from its bass line: `calm` (soft pad and sub), `build` (the
ostinato swells in and the drums gather), `drive` (full ostinato, synth bass, drum ensemble and
eight low horns doubling the melody) or `hit` (one wall-of-sound downbeat). The master bus has
gentle glue compression before the limiter.

## Trailer layer: voices and sound design

`vocals.py` makes the trailer-style layer. `crowd("Hold the road!")` is a gang shout from 16 to 20
voices. `sung("Teh", midi, seconds)` is a choir voice: each voice speaks the syllable, then TD-PSOLA
puts it on the written note and holds the vowel. `braam`, `riser`, `impact` and `sub_drop` are
synthesised. In a cue, `Score.place(beat, audio, gain_db, align="end")` drops rendered audio on a
beat (`align="end"` makes a riser finish on it). Shouts go in the gaps between narrated lines, while
the chant can sit under the speech. The chant words are original: "Te-ne-te vi-am" (Latin, "hold the
road"), "Lu-men" and "Vael-Orrun". Rendering the voices needs `pip install kokoro-onnx` and the
model from `tools/voice/fetch_model.sh` (or `KOKORO_DIR=<folder>`).

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
