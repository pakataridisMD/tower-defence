# Tower Defence 2D

An elemental tower defence game for Steam. Each run you grow a web of skill nodes: reaching an
element's region unlocks its towers, and the bridge nodes between two neighbouring elements unlock
hybrid towers. A separate meta tree carries progress between runs.

This repository is at **step 3 of 4**: a playable prototype with one map, ten waves, three elements
(Fire, Storm and Nature), two hybrid towers and a small in-run skill web. All art is placeholder shapes.
Step 4 adds the meta tree and saving.

## Getting started

1. Install [Godot 4.7.2](https://godotengine.org/download) (the standard build, not .NET).
2. Install [Git LFS](https://git-lfs.com) and run `git lfs install` once. Art and audio in `assets/` are stored with it.
3. Clone this repository and open `project.godot` in Godot.
4. Press **F5** and choose **Play**. **Data check** on the main menu lists the loaded data and any data errors.

## How to play

Enemies walk the brown road from IN to OUT. Each one that gets out costs lives; lose them all and the run ends.
Clear all ten waves to win.

1. Open the **skill web** (T) and take a node. An element's first node unlocks its tower, and the bridge
   between two elements unlocks their hybrid. You get one point at the start and one for each wave you clear.
2. Pick a tower on the right (or press 1 to 5) and click an empty tile to build it. Shift-click builds several.
3. Press **Space** to start the next wave. The top bar shows its element: enemies take half damage from that
   element and 50% more from the opposite one, so mix your towers.

| Key | Action |
| --- | --- |
| Space | Start the next wave |
| T | Open or close the skill web |
| 1 to 5 | Pick a tower to build |
| Left click | Build, or select a tower to see its stats and sell it |
| Right click | Cancel building and clear the selection |
| F | Change speed (1x, 2x, 3x) |
| P | Pause |
| Esc | Close the web, cancel building, clear the selection, then pause |

In the skill web, left-click takes a node. Right-click refunds a node you took in the current break between
waves, until you start the next wave.

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

Leave out `--headless` and `--quit-at-end` to watch the bot play.

### Tools

- `godot --headless -s tools/benchmark_sim.gd` times the simulation with 40 towers and 500 enemies on the board.
- `godot --resolution 1920x1080 --fixed-fps 30 res://tools/capture.tscn -- --out=<folder>` plays a run with the
  bot and saves screenshots of the menu, a wave, the skill web and the end screen. It needs a window, so on a
  server run it under `xvfb-run`.

## Folder layout

```
data/        game content as .tres files: elements, towers, enemies, waves, maps, rules, trees
scenes/      main.tscn (main menu), game/game.tscn (a run), debug/data_check.tscn
scripts/
  core/      stat maths, element rules, skill trees, data loading
  data/      the classes that define each kind of data file
  sim/       the run simulation: towers, enemies, waves, status effects. No drawing, so tests can run it
  game/      the run screen: board, HUD and skill web, which draw the simulation and send it player actions
  ui/        main menu, shared styles, data check
tests/       GUT tests: unit tests and full simulated runs
tools/       benchmark and screenshot tools (not part of the game)
assets/      art and audio (Git LFS)
addons/gut/  the GUT test framework (MIT licence)
```

The simulation steps at a fixed 60 times per second whatever the frame rate, and speed-up just runs more steps
per frame. That keeps runs repeatable, which the balance tests rely on.

## Changing game data

All balance numbers live in `data/`. Open any `.tres` file in Godot and edit it in the Inspector.

- **New tower:** duplicate a file in `data/towers/`, give it a new `id`, and unlock it from a tree node's `unlocks_towers`.
- **New tree node:** add a `TreeNodeData` file to `data/trees/in_run/` and list the id of a node it connects to in `links`. Links work both ways.
- **New enemy or wave:** add an `EnemyData` file to `data/enemies/`, then reference its id from a wave in `data/waves/`.
- **New map:** add a `MapData` file to `data/maps/` with the path's turning points as grid cells and the id of
  its wave set. The path may start and end one cell outside the grid, so enemies walk in and out.
- **Starting gold, lives and points:** `data/rules/run_rules.tres`.

Each tree node and keystone carries `Modifier` entries. Modifiers to the same stat combine in a fixed order:

```
final = (base + every FLAT) × (1 + every INCREASED added together) × (1 + each MORE, multiplied)
```

`required_tags` limits a modifier to towers carrying those tags. Every tower is tagged with its element ids,
and hybrids also get `hybrid`.

The `test_real_data_has_no_errors` test loads every data file and checks that every id it references exists,
that hybrids use neighbouring elements, and that every tree node can be reached from the start. A typo in a
data file fails the tests instead of breaking a run.

## Element ring

Fire, Storm, Nature, Water, Earth, Void, then back to Fire. Neighbours form hybrid towers, and the element
three steps away is the opposite. Each wave is aligned to one element: its enemies take 50% less damage from
that element and 50% more from the opposite one. Hybrids average the two.
