# Narrator voice

The story cinematics are narrated by one deep, calm female voice. This page covers
which voice tech we use, the licensing for a commercial Steam release, and how to
regenerate the lines when the script changes.

## What ships now: Kokoro, generated locally

`tools/voice/narrate.py` turns each shot's `text` in `data/story/cinematics/<id>.json`
into `assets/story/voice/<id>/<NN>.ogg` (one file per shot, numbered from 01), which
is what the cinematic player loads. Setup and commands are in the script's header.

- **Model:** Kokoro-82M, Apache-2.0 weights. Commercial use is allowed with no fee,
  no account and no attribution requirement, so the audio can ship in a paid game.
- **Voice:** the `regal` preset, chosen by Doctor Paris: a British blend of Kokoro's
  `bf_emma` (60%) and its lowest female voice `af_kore` (40%), slow and dramatic
  (0.8x speed, 0.75 s between sentences, 1.6 s at blank lines), with
  movie-trailer mastering (Doctor Paris asked for a clearer, trailer-like voice): close
  and dry, chest boost, presence at 3 kHz, de-essed, tightly compressed. `warm` (80/20, slightly lighter) is the other finalist.
- **Keeping it natural:** no pitch shifting (it made the voice sound electronic),
  one sentence at a time with 0.32 s breaths between them, a soft convolution hall
  instead of discrete echoes, faint room tone under the pauses, the synthetic fizz
  around 5.5 kHz tamed, normalised to -16 LUFS.
- **Who is voiced:** shots whose `speaker` is `narrator` or `ysolde` (Queen Ysolde
  is the narrator). Other characters stay as subtitles until they get voices.
- **Presets:** `regal` (default narrator), `elder` (lower, American, storybook),
  `whisper` (quiet or sad beats). A shot can pick one with `"voice_preset"`,
  or opt out of narration with `"voice": false`.
- **Pauses:** a blank line inside a shot's text becomes a 0.9 s dramatic pause.
- `tools/voice/mix_preview.py` lays a cinematic's lines over its music, starting each
  line at its shot marker from the music cue sheet. Trailer style: the music is boosted
  and compressed, dips only about 5 dB under the voice and is notched at 2-4 kHz so the
  words cut through; the mix ends at -12 LUFS.
- `--scripts DIR` reads cinematics from another folder (for example a branch
  checkout) and `--out DIR` writes the voice files somewhere else.
- Regenerating every cinematic takes seconds per line on a CPU, so the script can
  change freely until the end of development.

## Options considered

| Option | Quality | Commercial licence | Cost | Notes |
| --- | --- | --- | --- | --- |
| Kokoro-82M (local) | Good, a little flat in emotion | Apache-2.0, free | Free | In the repo pipeline now |
| ElevenLabs | Best AI acting, real emotion and whispers | Only on a paid plan; the free tier is non-commercial and needs attribution | About $5-22 a month; one month is enough to render the final script | Needs Doctor Paris's account and card |
| Human voice actor | Best, and players trust it | Buyout contract | Roughly a few hundred dollars for a few minutes of finished narration | Needs casting and a contract |

Steam requires a game to disclose AI-generated content that players see or hear,
so AI narration (Kokoro or ElevenLabs) must be declared in the Steamworks content
survey. A human actor avoids that and the reviews that sometimes come with it.

## Recommendation

Develop with Kokoro: it is free, already wired in and regenerates whenever the
lore changes. Before launch, re-record the final script once, either with an
ElevenLabs paid month (fast, cheap) or with a hired actor (best for the trailer
and reviews). The file layout stays the same, so swapping voices is only a
matter of replacing the .ogg files.
