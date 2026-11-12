# Tower Defence 2D

An elemental tower defence game for Steam. Each run you grow a web of skill nodes: reaching an
element's region unlocks its towers, and the bridge nodes between two neighbouring elements unlock
hybrid towers. A separate meta tree carries progress between runs.

It has a campaign of 27 stages across seven lands (one per element, then the Convergence), skirmish runs on
two maps at two difficulty levels, six elements with a hybrid tower for every pair, tower levels and
ascendancies, an in-run skill web, and a meta tree that is saved between runs, all in lit pixel art.

## Getting started

1. Install [Godot 4.7.2](https://godotengine.org/download) (the standard build, not .NET).
2. Install [Git LFS](https://git-lfs.com) and run `git lfs install` once. Art and audio in `assets/` are stored with it.
3. Clone this repository and open `project.godot` in Godot.
4. Press **F5**. Choose **Campaign** on the main menu, or pick a map and a difficulty level and choose **Play skirmish**. **Data check**
   lists the loaded data and any data errors.

## How to play

Enemies walk the brown road from IN to OUT. Each one that gets out costs lives; lose them all and the run ends.
Clear all ten waves to win.

1. Open the **skill web** (T) and take a node. An element's first node unlocks its tower and its skill, and
   the bridge between two elements unlocks their hybrid. You get three points at the start and three for each
   wave you clear; nodes cost more the further they are from the middle.
2. Pick a tower on the right (or press its number) and click an empty tile to build it. Shift-click builds
   several. Click a tower to level it up, ascend it or fuse it with another element.
3. Press **Space** to start the next wave. The top bar shows its element: enemies take half damage from that
   element and 50% more from the opposite one, so mix your towers.
4. During a wave, cast your **skills**. Each has a cooldown that runs while a wave is on.

| Skill | Element | Key | What it does | Cooldown |
| --- | --- | --- | --- | --- |
| Meteor | Fire | Q | Damage and a burn around the point you pick | 25 s |
| Surge | Storm | W | Every tower attacks 50% faster for 6 s | 45 s |
| Entangle | Nature | E | Stuns, slows and poisons around the point you pick | 35 s |
| Tidal Wave | Water | A | Pushes every enemy back along the road and slows it | 40 s |
| Earthquake | Earth | S | Hurts every enemy and cracks its armour | 45 s |
| Doom | Void | D | Enemies around the point you pick take 50% more damage for 6 s | 35 s |

A skill that needs a point is aimed: press its key (or its button), then click the board. Pressing the key a
second time casts it where the mouse is. Skill damage grows with the waves, so a skill is worth as much on
the last wave as on the first.

| Key | Action |
| --- | --- |
| Space | Start the next wave |
| T | Open or close the skill web |
| 1 to 9 | Pick a tower from the open shop page |
| Tab | Turn the shop page: base towers, duals, triples |
| Q W E A S D | Cast a skill (laid out on the panel as on the keyboard) |
| Z X C V | Press the selected tower's upgrade buttons, top to bottom |
| Delete | Sell the selected tower |
| Left click | Build, select a tower, or cast the skill you are aiming |
| Right click | Cancel building or aiming and clear the selection |
| F | Change speed (1x, 2x, 3x) |
| P | Pause |
| Esc | Close the web, stop aiming or building, clear the selection, then pause |

On the main menu, **C** opens the campaign, **M** the meta tree, and **Enter** starts a skirmish.

In the skill web, left-click takes a node; clicking a node further out takes the whole way to it when you have
the points. Right-click refunds a node you took in the current break between waves (from the tip inward),
until you start the next wave. Drag or WASD moves the web, the mouse wheel zooms and F shows all of it.

## Campaign

**Campaign** on the main menu opens a star chart of the element ring. There is a campaign for each element,
and a seventh, **the Convergence**, that opens once all six are finished: 27 stages in all.

| Campaign | Land | Horde | Signature enemies | Warden |
| --- | --- | --- | --- | --- |
| The Ember Reach | volcanic ash fields | Water, Nature, Earth | Menders, then Splitters | Cinder Tyrant (heals) |
| The Thunder Steppe | windswept plateau | Earth, Water, Void | Splitters, then Brutes | Thunderhead (fast, immune to effects) |
| The Verdant Deep | deep jungle | Void, Earth, Fire | Menders, then Warded | Elder Broodmother (sheds Shardlings, bursts into Splitters) |
| Frostmere | frozen lakeshore | Fire, Void, Storm | Runners, then Warded | Tidal Leviathan (vast, immune to effects) |
| Sunscar Canyon | red sandstone canyon | Storm, Fire, Nature | Brutes, then Splitters | Mountain Titan (22 armour) |
| The Hollow Rift | violet rift | Nature, Storm, Water | Warded, then Menders | Hollow King (splits into two Shades) |
| The Convergence | the heart of the ring | every element | everything | the Sundered Heart (changes element, summons Warded) |

- Each element campaign has four stages played in order (10, 12, 14 and 15 waves). The horde comes from the far
  side of the ring: the opposite element and its two neighbours. You may only draft the home element and its two
  neighbours, you start with the home element's first node for free, and home towers deal 20% more damage, so
  every wave is weak to something you can build.
- The last stage ends with the element's corrupted **Warden**. It keeps the home element, so it resists your home
  towers: bring a neighbour. A Warden that gets out costs 20 lives.
- Most stages have one twist, such as less range, dearer towers or more gold per wave. The rules are listed on the
  campaign map and in the run's help panel.
- The Convergence's maps have **several roads** that merge (2, then 3), every wave mixes elements group by group,
  and the last stage brings back four Wardens before the Sundered Heart.
- **Stars**: one for a win, two for keeping at least half your lives, three for losing none. The first win of a
  stage pays extra meta points (3, 6 for a Warden, more in the Convergence). Finishing a campaign earns a
  **sigil**, a small bonus in every run, skirmish included (for example +10% Fire damage).
- New enemies: **Mender** heals 4% a second unless burning or poisoned; **Splitter** bursts into three
  **Shardlings**; **Warded** ignores every status effect.

The campaign is written by `tools/campaign/gen_campaign.py`, which writes `data/campaigns/`, plus a map
(`data/maps/c_<stage>.tres`) and a wave set (`data/waves/c_<stage>.tres`) for every stage. Edit the tables in that
script rather than the files, then rerun it with the art generator. `tools/campaign/tuning.py` holds each stage's
health scale (and its boss waves' health), found by `tools/campaign_balance.gd`, which plays every stage with the
bot:

```sh
python3 tools/campaign/gen_campaign.py && python3 tools/art/gen_game_art.py && godot --headless --import
godot --headless -s tools/campaign_balance.gd                 # how the bot does on every stage
godot --headless -s tools/campaign_balance.gd -- --tune       # print new tuning.py lines
godot --headless -- --autoplay --stage=ember_4                # watch the bot play one stage
```

The bot levels and ascends its towers and casts skills, but follows one fixed plan. Tuning aims for it to keep
60%, 45%, 30% and 20% of its lives across an element campaign's four stages, and the printed numbers already
have a safety margin taken off.

## Story

The campaign tells a story in cinematics. Everything here is a first version for review: the art, voice and
music are placeholders or design drafts until they are approved.

- **The opening** plays the first time the campaign is opened, and before the first stage.
- **Cinematics every few stages.** Each element campaign has an opening scene, a scene after its Herald (the
  boss leading the last wave of its second stage) and one after its Warden. Plot scenes come after 6, 12 and
  18 stages won, and the middle one ("the night of falling stars") turns every land stage to night.
- **Cities.** Each stage defends a city. Winning tells you which city was saved, and losing which one fell.
  The last stage of the Convergence defends the capital.
- **Bosses.** Six Heralds and Cassivane, the Ashen Regent, lead stages. They have new tricks: a shield that
  softens damage to nearby allies, silencing towers, blinking forward, enraging when hurt, and (the Regent)
  escaping instead of dying. A banner and a health bar show the boss that is on the board.
- **The assault.** After the Convergence, *The Crownless Citadel* (stage `assault_1`, Nhal Vorath) is about
  30 minutes long. You bring down three buildings in turn: the Gatemaw, the Mirror Spire and the Crownless
  Throne. Each one that falls lets you build further east, closes roads or releases the Heralds again, and
  the Throne releases Vael-Orrun. The run is won when he falls. Waves start on their own 12 seconds after the
  last one. `godot --headless -s tools/assault_sim.gd` plays it with the bot and prints a timeline.

The story itself is plain JSON in `data/story/` (written from `docs/story/`):

| File | What it holds |
| --- | --- |
| `story.json` | the prologue id, plot beats (`after_stages_won`, `after_stage`, `before_stage`), `stage_scenes` (`before`, `after`, `lost`, `during: [{wave, cinematic}]`), `night_from_stages_won`, `cities`, and the `assault` (`intro`, `movements`, `outro`) |
| `characters.json` | the cast; `boss_enemy` links a character to its enemy for the boss banner |
| `cinematics/<id>.json` | `{id, title, music, shots: [{text, speaker, art_note, image, voice, duration}]}` |

Files are found by name when a shot leaves `image` or `voice` empty:

- pictures: `assets/story/images/<cinematic>/<NN>.png` (NN counts shots from 01)
- narration: `assets/story/voice/<cinematic>/<NN>.ogg` (`"voice": false` turns it off for a shot)
- portraits: `assets/story/portraits/<character>.png`
- music: `assets/story/music/<cue>.ogg`, with the cue for each cinematic in `assets/story/music/cinematic_music.json`

A shot with no picture shows a card with its art note, and a shot with no voice is timed from its words, so
the whole story can be played before its art and voice exist. In a cinematic, Space, Enter, a click or the
right arrow moves on and Esc skips. Each cinematic plays on its own once; the save remembers which.
When exporting the game, add `data/story/*.json` and `assets/story/music/*.json` to the export's
"Filters to export non-resource files".

`godot --resolution 1920x1080 --fixed-fps 30 res://tools/capture.tscn -- --out=<folder> --story` takes
screenshots of the cinematic player, two Herald fights, the assault and the campaign map with the citadel.

## Skill web

The skill web is the tree you spend points on during a run (T). It has about 400 nodes, drawn as a spider
web around the Origin, and is written by `tools/web/gen_skill_web.py` (edit its tables and rerun it, rather
than editing `data/trees/in_run/*.tres` by hand):

- Six element wedges. Each starts with the element's entry node (its tower and skill), runs out along
  spokes of small travel nodes and is crossed by ring threads at 385, 640, 895 and 1150. Notables sit on the
  threads: the core (which with other cores unlocks the dual and triple towers) at 385, the old notable at 640.
- The outer wedge has six spokes: the element's two side themes, its status, damage, attack speed and its skill.
- Two keystones at the tip of each wedge, a pick-one choice. Focus, Overcharge and Hoard still need the meta tree.
- Three bridges on each border: the old bridge that unlocks the neighbours' dual tower, a Confluence and a
  Concord that make that dual stronger.
- Costs climb with distance: 1 point for the first rings, then 2, 3, 4 and 5 at the rim, 6 for a keystone;
  a notable costs one more than its ring. Each bonus is small (2 to 6% on a travel node). Runs pay 3 points
  at the start, 3 per wave and 3 per boss (`data/rules/run_rules.tres`), so a short stage buys a path or two
  and only long runs reach the rim.

## Meta tree and saves

Runs pay **meta points** for records. Each campaign stage and skirmish map keeps the best score reached on it:
one point for each wave cleared and two more for a win, times the difficulty level's multiplier (Hard 1.5x,
Nightmare 2x). A run pays only the part of its score above that record, so clearing more waves, winning, or
winning on a harder level pays, and repeating the same result does not. A won replay that sets no record pays
one point, three times per stage or map, and nothing after that. The first win of a campaign stage also pays its
bonus once. Saves from before records existed (version 3 and older) get their records rebuilt from the stages
they have won, and any points above what that progress is worth are taken back; talents that no longer fit are
refunded. Spend the points in the **meta tree** (Talents on the main menu). It is a wheel of 172 talents, built
to fill across the whole campaign: it costs about 760 points, and a clean first pass through the campaign pays
about 550.

- Four inner wings: **Arsenal** (tower damage and speed, armour piercing, the Thornstorm bridge and the skill
  web keystones), **Command** (starting gold and lives, gold per wave, cheaper towers, a starting skill point),
  **Expeditions** (the Serpentine map, Hard and Nightmare, skill points) and **Mastery** (skills and range).
- The **Starpath**, a ring road of small travel nodes joining the wings to the outer ring.
- Six element constellations on the outer ring, one per element, each with a status arm, a speed and cost
  arm, and a keystone with a real downside at its tip (Pyre Covenant, Ball Lightning, Overgrowth, Glacial
  Heart, Fault Line, Hollow Pact). Confluence bridges between neighbours boost the dual towers of both.
- Ten **pick-one choices**: taking one side closes the other until it is refunded (`TreeNodeData.excludes`).

The screen is bigger than the window: drag or use WASD to move, the mouse wheel or + / - to zoom (the pixel
art steps between 1x, 2x and 3x), F to see the whole tree and Home to go back to the Origin. The tree is
written by `python3 tools/meta/gen_meta_tree.py` (edit its tables, not the .tres files; `--preview out.png`
draws the layout). `godot --headless -s tools/meta_pacing.gd` plays the campaign with the bot, spending its
points after every stage, and prints how full the tree is after each one (also in CI on a `[pacing]` commit).

Refunds in the meta tree are always free: right-click a node at the tip of a branch, or use **Refund all**
(it asks for a second click). A map, difficulty level or skill web node named in a meta node's `unlocks_*`
list stays locked until that meta node is taken. Anything no meta node lists is open from the start.

Progress is saved after every change to `user://save.json`. On Windows that is
`%APPDATA%\Godot\app_userdata\Tower Defence 2D\save.json`; on Linux it is
`~/.local/share/godot/app_userdata/Tower Defence 2D/save.json`. Each save is written to a temporary file and
then moved into place, and the previous save is kept as `save.json.bak`. A save that cannot be read is copied
to `save.json.corrupt` and the backup is loaded instead. To start over, delete those files.

The save is versioned JSON. When its shape changes, bump `PlayerProfile.VERSION` and teach
`PlayerProfile.migrate()` to upgrade older saves.

## Art test: lit Fire tower

**Art test: lit Fire tower** on the main menu (or `scenes/demos/fire_tower_lighting.tscn`) opens a
look test for the target art style: detailed top-down pixel art with dynamic lighting, in the spirit of
Graveyard Keeper. It is separate from the game and uses no game data.

- The scene is drawn at 640x360 and scaled up 3x with nearest filtering, so lights and shadows stay pixelated too.
- Every sprite has a normal map, so the sun, the brazier, the arrow slit and each fireball shade it.
- An ambient tint runs through day, dusk, night and dawn. Fake projected shadows turn away from the sun by day and the brazier by night.
- Grass sways and bends when slimes walk through it. Mist and fireflies fade in at night.
- Keys: **1** day, **2** dusk, **3** night, **4** dawn, **Space** runs or stops the clock, **Esc** returns to the menu.

The art is generated by `tools/art/gen_lighting_demo.py` (Python 3 with numpy and Pillow), which writes
`assets/art/lighting_demo/`. It is placeholder art for judging the look. Screenshots and a clip:

```
godot --resolution 1920x1080 res://scenes/demos/fire_tower_lighting.tscn -- --shots=<folder>
godot --resolution 1920x1080 --fixed-fps 30 --write-movie <folder>/f.png --quit-after 540 \
  res://scenes/demos/fire_tower_lighting.tscn -- --clip
```

## Game art

The game board is drawn in the same lit pixel-art style as the art test. Every tower, enemy and map has a
picture and a normal map, so the sun and the towers' own lights shade them.

- The board is drawn in art pixels at 2x with nearest filtering (32 art pixels per board cell).
- The sun goes down as the waves go on: the first waves are fought in daylight, the middle ones at dusk and the
  last ones (with the boss) at night, when the towers' own light matters most. A win ends in a dawn. Every ten
  waves a new day starts. See `scripts/game/day_night.gd`.
- Towers are light sources: the Fire brazier and the hybrids flicker, and each shot, bolt and blast flashes.
- Enemies take the colour of their element and wear gear by type (helmet for the brute, crown for the warden).
  They come in several bodies with a six-frame walk: hopping blobs, darting tadpoles (runner, shardling), shelled
  beetles on little feet (brute, warded, Broodmother, Mountain Titan), floating wisps (the Hollow King and his
  shades, the Thunderhead), a twin blob that splits, and the Leviathan's long serpent.
- Shots are made of the tower's element: fireballs, crooked bolts, thorns, water drops, tumbling rocks and dark
  void orbs, and a mixed tower's shot trails its other element. Each lands its own way (a splash, rubble, a ring
  that falls inward for Void).
- What is hurting an enemy is drawn on it: flames for a burn, bubbles for poison, frost at its feet for a slow,
  stars for a stun, a violet mark for a curse, chips falling off shattered armour, green crosses while it heals.
- A tower that levels up, fuses or ascends throws sparks and a ring; an ascended tower keeps a circle of runes
  at its foot, and an aura tower shows its reach as a ring of lights on the ground.
- Shadows are faked: a squashed silhouette cast away from the sun by day, and a soft contact blob under everything.
- Grass, flowers, stones, mushrooms and bushes are scattered off the road. A tower hides the props on its cell.
- Code: `scripts/game/board_art.gd` builds and updates the art, `scripts/game/board_view.gd` still draws the
  cursor, placement grid, range rings and health bars on top, unshaded so they stay readable at night.

All of it is generated by `tools/art/gen_game_art.py` (Python 3 with numpy and Pillow, about half a minute), which
reads the maps in `data/maps/` and writes `assets/art/game/` with an `art.json` index. To add a tower or enemy,
add a recipe to that script and run it (`--towers` or `--enemies` redraws only those):

```sh
python3 tools/art/gen_game_art.py
python3 tools/art/gen_tree_art.py
godot --headless --import
```

The skill web and the meta tree use the same pixel art (`scripts/game/tree_art.gd`, generated by
`tools/art/gen_tree_art.py` into `assets/art/game/tree/`). They show a starry backdrop and a socketed gem
in its region's colour for each node, with an icon for what the node does. A node that unlocks a tower
shows a portrait of that tower, and a bridge shows a gem split between its two regions. Taken nodes glow
and light flows along their links, while nodes you can take pulse gold. A node's icon is picked from its
stats and unlocks. To choose one yourself, set `icon` on the node (any `icon_<name>.png` in that folder).

The interface has its own pixel art in `assets/art/ui/`, generated by `tools/art/gen_ui_art.py`: the frames
of panels and buttons (`scripts/ui/ui_style.gd` builds the theme from them), an icon for every skill in
`data/skills/`, and the main menu's backdrop and title. The backdrop is a night scene put together from the
game's own tower and enemy pictures, so run `gen_game_art.py` first if those changed. A new skill needs an
icon in that script's `SKILL_ICONS`.

`tests/game/test_board_art.gd` fails if a tower, enemy or map in `data/` has no art, and
`tests/game/test_tree_art.gd` fails if a tree node, region or stat has no icon. A tower or map without art
falls back to the old flat shapes, so the game still runs while the art is being made.

## Sound effects

Every sound effect is designed by `tools/sfx/build.py` from real recordings: CC0 orchestral percussion,
brass and found sounds (VSCO 2 Community Edition), a sampled choir (FluidR3_GM, MIT) and bosses' lines spoken
by Kokoro text to speech (Apache-2.0), all free to ship commercially (`assets/audio/sfx/LICENSE.md`). See
`tools/sfx/README.md` for how the recipes work and how to add a sound.

```
tools/sfx/fetch_samples.sh                    # once: the recordings and voice model (~2.5 GB, not in Git)
python3 tools/sfx/build.py                    # writes assets/audio/sfx/ and its catalogue.json (~2 minutes)
python3 tools/sfx/build.py --only boss_gorrath  # just the sounds whose names contain the text
godot --headless --import
```

The game plays them through the `Sfx` autoload (`scripts/core/sound_player.gd`), which reads
`assets/audio/sfx/catalogue.json` for each sound's variations, bus, volume and how often it may play, and
pans board sounds by where they happen. `scripts/game/game_audio.gd` listens to the run and decides what to
play: an attack sound for every tower (built from its elements and how it fights), hits and explosions,
enemy deaths, the war horn of each wave, the base being hit, skills, building and upgrading, and for every
boss a reveal, footsteps, lines from the story in its own voice, a roar when it is badly wounded and a death. Buttons click on
their own. The buses are Master, Music, Sfx, Ui and Voice (`default_bus_layout.tres`); big moments duck the
Music bus for a few seconds.

`tests/game/test_sound.gd` fails if a tower, enemy, boss or skill in `data/` has no sound, so new content
needs a rerun of `build.py` (towers get theirs automatically from their elements).

## Running the tests

In the editor, open the **GUT** panel at the bottom and press **Run All**.

From a terminal:

```sh
godot --headless --import
godot --headless -s addons/gut/gut_cmdln.gd
```

GitHub Actions runs the same tests on every push and pull request. It also runs a smoke test, where a
scripted player (`AutoPlayer`) plays a whole run in the real game scenes, and fails if any script error appears.
You can run that yourself:

```sh
godot --headless --fixed-fps 60 -- --autoplay --quit-at-end
```

Leave out `--headless` and `--quit-at-end` to watch the bot play. The bot's runs, and every test run, keep
progress in memory and never touch your real save. Add `--save-path=user://bot_save.json` after `--` to make the
bot save somewhere else; CI does this to check that saving works.

### Tools

- `godot --headless -s tools/benchmark_sim.gd` times the simulation with 40 towers and 500 enemies on the board.
- `godot --resolution 1920x1080 --fixed-fps 30 res://tools/capture.tscn -- --out=<folder>` plays a run with the
  bot and saves screenshots of the menu, the meta tree, a wave, the skill web and the end screen. Add `--quick`
  to skip the run and only take the menu, the meta tree and the skill web, or `--ui` for the menu and the HUD
  with a tower selected and skills being cast. It needs a window, so on a server run it under `xvfb-run`.
  The **Screenshots** workflow does this for every pull request that changes how the game looks, and keeps
  the pictures with the build.
- `godot --headless -s tools/campaign_balance.gd` plays every campaign stage with the bot and prints how each
  went. `-- --tune` finds each stage's enemy health for `tools/campaign/tuning.py`, and `-- --skirmish` does
  the same for the skirmish waves. The **Balance** workflow runs both when a commit message contains `[tune]`.

## Folder layout

```
data/        game content as .tres files: elements, towers, skills, enemies, waves, maps, difficulty levels,
             rules, trees
scenes/      main.tscn (main menu), game/game.tscn (a run), meta/meta_tree.tscn, debug/data_check.tscn
scripts/
  core/      stat maths, element rules, skill trees, data loading, meta progress and saving
  data/      the classes that define each kind of data file
  sim/       the run simulation: towers, enemies, waves, status effects. No drawing, so tests can run it
  game/      the run screen: board, pixel art and lighting, HUD and skill web, which draw the simulation and
             send it player actions
  ui/        main menu, meta tree screen, shared styles, data check
tests/       GUT tests: unit tests and full simulated runs
tools/       benchmark and screenshot tools, the art generators in tools/art/ and the sound effect
             designer in tools/sfx/ (not part of the game)
assets/      art and audio. Generated art in assets/art/ and sound in assets/audio/sfx/ are plain Git
             files, everything else Git LFS
addons/gut/  the GUT test framework (MIT licence)
```

The simulation steps at a fixed 60 times per second whatever the frame rate, and speed-up just runs more steps
per frame. That keeps runs repeatable, which the balance tests rely on.

## Changing game data

All balance numbers live in `data/`. Open any `.tres` file in Godot and edit it in the Inspector.

- **New tower:** duplicate a file in `data/towers/`, give it a new `id`, and unlock it from a tree node's `unlocks_towers`.
- **New tree node:** change the tables in `tools/web/gen_skill_web.py` (or `tools/meta/gen_meta_tree.py` for the
  meta tree) and rerun it. Each node is a `TreeNodeData` file that lists the id of a node it connects to in `links`. Links work both ways. `region` is the element id in the
  skill web and the branch id (`arsenal`, `command`, `expeditions` or `mastery`) in the meta tree.
- **Meta unlocks:** list ids in a meta node's `unlocks_nodes`, `unlocks_maps` or `unlocks_difficulties`.
  Run-wide bonuses are modifiers to `starting_gold`, `starting_lives`, `starting_tree_points`, `gold_per_wave`,
  `sell_refund` or `tree_points_per_boss`; tower bonuses work as in the skill web.
- **New difficulty level:** add a `DifficultyData` file to `data/difficulties/` with its enemy health and meta
  point multipliers.
- **New skill:** add a `SkillData` file to `data/skills/` with its element, cooldown and what it does: `damage`,
  `status_effects`, `knockback`, or `modifiers` that last for `duration` seconds. `radius` above 0 makes it an
  aimed skill, and `requires_node` is the skill web node that opens it. Modifiers to `skill_cooldown` and
  `skill_damage` on tree nodes change skills (tags: `skill` and the element).
- **New enemy or wave:** add an `EnemyData` file to `data/enemies/`, then reference its id from a wave in `data/waves/`.
- **New map:** add a `MapData` file to `data/maps/` with the path's turning points as grid cells and the id of
  its wave set. The path may start and end one cell outside the grid, so enemies walk in and out. `order` sets
  its place on the main menu. `extra_lanes` adds more roads (spawn groups share their enemies out over them, or
  keep to one with `lane`), `biome` picks the ground art, and `skirmish = false` keeps it out of the skirmish list.
- **Enemy traits:** `EnemyData` can heal (`regen_per_second`), ignore status effects (`status_immune`), split
  (`split_into`, `split_count`), summon (`summon`, `summon_interval`, `summon_count`), keep its own `element`,
  or turn round the ring (`prismatic_interval`).
- **Starting gold, lives and points, and meta points per run:** `data/rules/run_rules.tres`.

Each tree node and keystone carries `Modifier` entries. Modifiers to the same stat combine in a fixed order:

```
final = (base + every FLAT) × (1 + every INCREASED added together) × (1 + each MORE, multiplied)
```

`required_tags` limits a modifier to towers carrying those tags. Every tower is tagged with its element ids,
and hybrids also get `hybrid`.

The `test_real_data_has_no_errors` test loads every data file and checks that every id it references exists,
that hybrids use neighbouring elements, that every tree node can be reached from the start, and that at least
one map and one difficulty level are open to a new player. A typo in a data file fails the tests instead of
breaking a run.

## Element ring

Fire, Storm, Nature, Water, Earth, Void, then back to Fire. Neighbours form hybrid towers, and the element
three steps away is the opposite. Each wave is aligned to one element: its enemies take 50% less damage from
that element and 50% more from the opposite one. Hybrids average the two.
