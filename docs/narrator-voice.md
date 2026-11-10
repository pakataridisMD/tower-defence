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
- **Voice:** a blend of Kokoro's lowest female voice (`af_kore`) with a little
  breathy `af_nicole`, slowed to 0.82x, pitched down 1.5 semitones, warmed in the
  low mids, given a small stone-hall echo and normalised to -16 LUFS.
- **Presets:** `elder` (default narrator), `whisper` (quiet or sad beats), `regal`
  (British, for royal and city scenes). A shot can pick one with `"voice_preset"`,
  or opt out of narration with `"voice": false`.
- **Pauses:** a blank line inside a shot's text becomes a 0.9 s dramatic pause.
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
