# The Story

The campaign story of the game. The Black Gate at the bottom of the Rift has been forced open; six armies
come out of it, one to each land around the capital, Solenne. We take the six lands back one at a time,
saving every town on the way, hold Solenne, then march down into the Rift and through the Gate to end it.

| File | What it is | Who uses it |
|---|---|---|
| [bible.md](bible.md) | The canon: history, the rules of the Gate, why each land is attacked, places, the towns, every character, the story beat by beat, the final level, tone and style rules. | Everyone. Read this first. |
| [characters.md](characters.md) | Cast sheet: look, colours, weapon, signature shape and key scenes for every hero, ally, Herald, Warden and villain. | Character art, animation, voice. |
| [scripts.md](scripts.md) | The opening (about 2:30) and all 35 cinematics, shot by shot, with art notes. Generated. | Voice, cinematics, art. |
| `tools/story/story_content.py` | The source of every cinematic, the trigger table, the town lines and the character list. | Edit story text here. |
| `data/story/` | What the game reads: `story.json` (when scenes play, the town per stage, stage bosses, the final level), `cinematics/<id>.json`, `characters.json`. Generated. | Game code, voice tool. |

To change story text, edit `tools/story/story_content.py` and run:

    python3 tools/story/story_content.py

It rewrites `data/story/` and `docs/story/scripts.md` and checks that every cinematic is played somewhere,
every speaker is a known character, all 27 stages have a town, and no cut term (the Crack, the Outer
Hollow, orcs and so on) has crept back in.

## The shape of it

The lands open in a fixed order: Ember Reach, Thunder Steppe, Verdant Deep, Frostmere, Sunscar Canyon,
Hollow Rift, then the Convergence and the final level.

- **Prologue** (before stage 1): the songs' version of the old war, the Gate forced open, Oswin drives it
  back to a cart-wide gap and falls through, the six Heralds go out, the plan.
- **Each land:** a scene before stage 1 (whose Warden is mad, what is flooding in, which Herald), after
  stage 2 (the Herald dies, a champion hero joins) and after stage 4 (the Warden is freed and joins).
- **After 8 wins:** the Refugee Road (the Regent, still trusted).
- **After 12 wins:** the Night of Falling Stars. The Regent betrays Solenne, Fennick dies, the Queen is
  blinded saving the Heartstone and the Sunstone is broken. The Long Night begins and the remaining land
  stages are fought at night.
- **After 18 wins:** There Was No Dawn.
- **Convergence** (stages 25-27): the Regent at Crossmere (Ilyra joins), the Lumen Gate (Seraphel joins),
  the siege of Solenne. At wave 17 of the capital, Oswin returns and relights the Sunstone.
- **Final level** (40 waves under Nhal Vorath): through the Gate; wave 39 Vael-Orrun himself; wave 40 the
  counter-attack; then The Truth, the Epilogue, and the post-credits scene.

Sixteen playable heroes join along the way (see bible section 7.3).
