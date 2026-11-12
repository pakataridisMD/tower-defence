# Narrator and character voices

The story cinematics are narrated by one deep, calm female voice, and every other
speaking character has a voice of their own. This page covers which voice tech we
use, the licensing for a commercial Steam release, and how to regenerate the lines
when the script changes.

## What ships now: ElevenLabs v3, every speaking character voiced

`tools/voice/narrate.py` turns each shot's `text` in `data/story/cinematics/<id>.json`
into `assets/story/voice/<id>/<NN>.ogg` (one file per shot, numbered from 01), which
is what the cinematic player loads. Setup and commands are in the script's header.

- **Narrator:** Queen Ysolde (speakers `narrator` and `ysolde`) is the ElevenLabs v3
  Voice Library voice **Elariel**, picked by Doctor Paris from six auditions
  (preset `regal_el`).
- **Characters:** every other speaker has their own voice in `tools/voice/cast.json`
  (Doctor Paris asked for all of them to be voiced, 2026-11-12). A speaker missing from
  the cast stays as subtitles. Each voice gets a style in `narrate.py`'s `STYLES`:

  | Speaker | Character | Voice | Style | Why |
  |---|---|---|---|---|
  | `vael_orrun` | Vael-Orrun, the Sunderer | Victor | sovereign | Ancient, deep and slow. A dark hall and a faint sub-octave shadow, so every element in the room goes still. |
  | `cassivane` | Cassivane Dral, the Ashen Regent | Dominic | mortal | British, brooding, commanding. Not cruel: certain. |
  | `the_hush` | The Hush (secret, post-credits) | True | hush | A dark whisper, layered an octave down and a fifth up: flat, quiet, inhuman. |
  | `oswin` | Oswin, the Grey/White Lantern | Cornelius | mortal | Old British sage. Wry and endlessly patient. |
  | `fennick` | Master Tobias Fennick | Adam | mortal | Gruff, gravelly old Scot. The engineer who shouts orders. |
  | `tamsin` | Tamsin Reed | Charmion | mortal | Husky British soldier. Dry, kind, tired, unbreakable. |
  | `brannoc` | Brannoc Emberhand | Viking Bjorn | mortal | Gravelly, booming Northern raider of a smith. |
  | `kaela` | Kaela Stormrider | Blondie | mortal | Intense, powerful British rider who never retreats. |
  | `sylvaine` | Sylvaine Thornwhisper | Valory | mortal | Calm, mysterious, three hundred years patient. |
  | `mirelle` | Mirelle the Tide-Seer | Arabella | seer | Young, soft, mysterious. A touch of cold air around her. |
  | `gorrim` | Gorrim Stonebeard | Gravel Midnight | mortal | Deep, rough, gritty old shieldmaster. |
  | `corvin` | Corvin the Uncrowned | Gideon | mortal | Rugged, gravelly, Northern. Bitter restraint. |
  | `ilyra` | Ilyra the Unbroken | Grace | mortal | Soft-spoken, moody young British woman. |
  | `seraphel` | Seraphel the Dawnblade | Cate | mortal | Deep, resonant, elegant knight with one fight left. |
  | `ignar` | Ignar, the Cinder Warden | Flint | warden | Deep, raspy and warm, like a bonfire. |
  | `aurath` | Aurath of the Storms | Ethereal Husk | twin | Atmospheric, gravelly female voice doubled an octave down: two voices at once. |
  | `elowen` | Elowen the Evergreen | Beatrice | warden | Old, gentle, slow. Her land is dying. |
  | `thalassa` | Thalassa of the Deep | Tessa | warden | Mystical, deep, prophetic. She remembers everything. |
  | `orrok` | Orrok the Mountain | John Doe | titan | Very deep and very slow. He barely speaks. |
  | `nyxara` | Nyxara of the Hollow | Bella | warden | Deep, elegant, haunting. Keeper of the road of the dead. |
  | `pale_vesper` | The Pale Vesper (Herald) | Veda Sky | herald | Chilling singer's voice, hollowed out. |
  | `vholt` | Vholt Stormcrown (Herald) | Jerry B. | herald | Gruff old commander, hollowed out. |

  Styles: `mortal` is close and dry like the narrator. `warden` is a bigger, older space.
  `herald` is hollowed out, with a thin chorus and scooped mids. `sovereign` adds a dark
  hall and a sub-octave shadow. `twin` doubles the voice an octave down. `titan` sits
  2 semitones lower. `seer` has a little cold air. `hush` is layered and inhuman, and
  about 5 dB quieter than everyone else.
- **Acting:** `tools/voice/direction.json` gives every sentence an emotion, and
  `elevenlabs_tts.py` turns each emotion into a v3 audio tag such as `[shouting]`,
  `[whispers]`, `[gasps] [shocked]` or `[menacing, quietly]`. `check_direction.py` lists any
  voiced sentence without an entry.
- **Credits:** replies are cached in `tools/voice/cache/` (git-ignored), so only new or
  changed paragraphs cost credits. A full pass of every line is about 9k characters.
  Re-render only the characters with `--speakers cast`.
- **Level:** every line is mastered trailer-style (close, chest, presence, de-essed,
  compressed) and leveled to -15 LUFS with peaks under about -1 dBFS.
- **New account:** a Voice Library voice must be added to the account before it can be
  used. `cast.json` keeps each voice's library owner id for that
  (`POST /v1/voices/add/<owner>/<voice_id>`).
- **Licensing:** ElevenLabs paid plans include a commercial licence for the audio.
  Steam's AI-content disclosure must declare the AI-generated voices.

## Free fallback: Kokoro, generated locally

- **Model:** Kokoro-82M, Apache-2.0 weights. Commercial use is allowed with no fee,
  no account and no attribution requirement.
- **Presets:** `regal` (British blend of `bf_emma` and `af_kore`, slow and dramatic,
  trailer mastering), `warm`, `elder`, `whisper` and `hush`. Pick one with `--preset`
  or per shot with `"voice_preset"`, or opt a shot out with `"voice": false`.
- **Keeping it natural:** no pitch shifting (it made the voice sound electronic),
  one sentence at a time with breaths between them, a soft convolution hall, faint
  room tone under the pauses.
- **Pauses:** a blank line inside a shot's text becomes a dramatic pause.
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

Ship with ElevenLabs v3 (Doctor Paris chose it and has a paid plan): Elariel narrates,
and the cast in `cast.json` voices everyone else. Keep Kokoro for offline work. A hired
actor is still an option for the trailer. The file layout stays the same, so swapping
any voice only means replacing the .ogg files.
