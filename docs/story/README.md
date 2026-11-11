# The Story

The campaign story of the game: a long fighting retreat across a ring of six elemental lands, where every
stage won saves a city's people and loses the city, until the last city, Solenne, is the one we hold. Then
we go through the Crack and take the fight to the Sunderer.

| File | What it is | Who uses it |
|---|---|---|
| [bible.md](bible.md) | The canon: cosmology, history, why we are attacked, who we are, places, the 27 cities, every character, the midpoint, the hero who returns, the final assault, tone. | Everyone. Read this first. |
| [characters.md](characters.md) | Cast sheet: look, colours, weapon, signature shape and key scenes for every hero, ally, Herald, Warden and villain. | Character art, animation, voice. |
| [scripts.md](scripts.md) | The opening narration (about 2 minutes) and all 33 cinematics, shot by shot, with art notes. Generated. | Voice, cinematics, art. |
| `tools/story/story_content.py` | The source of every cinematic, the trigger table, the Ledger of Fallen Cities and the character list. | Edit story text here. |
| `data/story/` | What the game reads: `story.json` (when scenes play, the city lost per stage, stage bosses, the assault), `cinematics/<id>.json`, `characters.json`. Generated. | Game code, voice tool. |

To change story text, edit `tools/story/story_content.py` and run:

    python3 tools/story/story_content.py

It rewrites `data/story/` and `docs/story/scripts.md` and checks that every cinematic is played somewhere,
every speaker is a known character and all 27 stages have a city.

## The shape of it

- **Prologue** (before stage 1): the Black Comet, the Crack, Oswin the Grey Lantern falls.
- **Act I** (6 lands, in any order; canon order Ember Reach, Thunder Steppe): a cinematic before each land,
  after its stage 2 (a Herald falls, a champion hero joins) and after its stage 4 (its corrupted Warden is
  freed and joins). That is a cinematic every two stages.
- **After 6 wins:** the Refugee Road (the Regent, still trusted).
- **After 12 wins:** the Night of Falling Stars. The Regent betrays Solenne, Fennick dies, the Queen is
  blinded and the Sunstone is shattered. The Long Night begins and the remaining land stages are fought
  at night.
- **After 18 wins:** There Was No Dawn.
- **Convergence** (stages 25-27): the Regent at Crossmere (Ilyra joins), the Lumen Gate (Seraphel joins),
  the siege of Solenne. At wave 17 of the capital, Oswin returns as the White Lantern and dawn breaks.
- **Final assault** (about 30 minutes, three movements): the Black Gate, the Mirror Spire, the Crownless
  Throne. Epilogue and a post-credits tease.

Sixteen playable heroes join along the way (see bible section 7.3).
