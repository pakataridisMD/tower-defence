# Tower Defence 2D

An elemental tower defence game for Steam. Each run you grow a web of skill nodes: reaching an
element's region unlocks its towers, and the bridge nodes between two neighbouring elements unlock
hybrid towers. A separate meta tree carries progress between runs.

This repository is at **step 2 of 4**: the project skeleton, the data model and the starter data.
The playable prototype (one map, waves, three elements and a small in-run tree) comes in step 3.

## Getting started

1. Install [Godot 4.7.2](https://godotengine.org/download) (the standard build, not .NET).
2. Install [Git LFS](https://git-lfs.com) and run `git lfs install` once. Art and audio in `assets/` are stored with it.
3. Clone this repository and open `project.godot` in Godot.
4. Press **F5**. The start screen lists the loaded data and shows any data errors.

## Running the tests

In the editor, open the **GUT** panel at the bottom and press **Run All**.

From a terminal:

```sh
godot --headless --import
godot --headless -s addons/gut/gut_cmdln.gd
```

GitHub Actions runs the same tests on every push and pull request.

## Folder layout

```
data/        game content as .tres files: elements, towers, enemies, waves, rules, trees
scenes/      Godot scenes (main.tscn is the start screen for now)
scripts/
  core/      game logic: stat maths, element rules, skill trees, data loading
  data/      the classes that define each kind of data file
  ui/        screens and widgets
tests/       GUT unit tests
assets/      art and audio (Git LFS)
addons/gut/  the GUT test framework (MIT licence)
```

## Changing game data

All balance numbers live in `data/`. Open any `.tres` file in Godot and edit it in the Inspector.

- **New tower:** duplicate a file in `data/towers/`, give it a new `id`, and unlock it from a tree node's `unlocks_towers`.
- **New tree node:** add a `TreeNodeData` file to `data/trees/in_run/` and list the id of a node it connects to in `links`. Links work both ways.
- **New enemy or wave:** add an `EnemyData` file to `data/enemies/`, then reference its id from a wave in `data/waves/`.

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
