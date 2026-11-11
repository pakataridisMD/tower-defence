#!/usr/bin/env python3
"""Writes the campaign: data/campaigns/*.tres, plus one map (data/maps/c_*.tres) and one wave set
(data/waves/c_*.tres) for every stage.

There is a campaign for each of the six elements and a seventh, the Convergence, that opens once
all six are finished. Each element campaign is fought in that element's land against a horde from
the far side of the ring: the opposite element and its two neighbours. Every wave is therefore weak
to one of the three elements the stage allows (the home element and its neighbours), and the
home element's towers get a bonus. The last stage of each campaign ends with the element's own
corrupted Warden, which resists the home element, so the player has to lean on a neighbour.

The files are plain Godot resources and can be edited in the editor, but running this script again
overwrites them. Change the tables below instead, then run:

    python3 tools/campaign/gen_campaign.py
    python3 tools/art/gen_game_art.py      # ground art for the maps
    godot --headless --import
    godot --headless -s tools/campaign_balance.gd   # the bot plays every stage
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import maps  # noqa: E402  (the big winding maps are grown from the sketches below)

RING = ["fire", "storm", "nature", "water", "earth", "void"]
NAMES = {"fire": "Fire", "storm": "Storm", "nature": "Nature", "water": "Water", "earth": "Earth", "void": "Void"}
ENTRY = {e: f"{e}_entry" for e in RING}


def opposite(e):
    return RING[(RING.index(e) + 3) % 6]


def neighbours(e):
    i = RING.index(e)
    return [RING[(i + 1) % 6], RING[(i - 1) % 6]]


# ------------------------------------------------------------------------------------ campaigns
# Each stage: id, name, story, waypoints (or lanes), waves, health scale, twist (stat, kind, value,
# tags, text) or None, and extra stage settings.
# Waypoints are a sketch of the road on a 24 x 15 grid: the cells where it turns, with the ends just
# outside the grid. tools/campaign/maps.py grows each sketch into the real map (maps.GRID, about three
# times the area), bends the straights into curves and adds spawn holes (HOLES below).
CAMPAIGNS = [
    {
        "id": "ember_reach", "element": "fire", "name": "The Ember Reach",
        "tagline": "The Tide against the Volcano",
        "description": "The Warden of Fire has gone silent, and the sea has come up the mountain. Hold the "
                       "ash roads with flame while the Tide's Menders knit their wounds shut.",
        "signature": "mender", "second": "splitter",
        "reward": ("Sigil of Embers", "Fire towers deal 10% increased damage in every run.",
                   [("damage", 1, 0.10, ["fire"])]),
        "stages": [
            ("ember_1", "Ashfall Road", "The first villages smoulder under a grey sky. The Tide comes in small, wet packs.",
             [(-1, 7), (7, 7), (7, 3), (16, 3), (16, 11), (24, 11)], 10, 1.0, None),
            ("ember_2", "Cinder Steps", "Menders walk with the Tide now. Keep them burning, or they will heal.",
             [(-1, 2), (5, 2), (5, 12), (11, 12), (11, 4), (17, 4), (17, 12), (24, 12)], 12, 1.0,
             ("gold_per_wave", 0, 10, [], "Rich veins: +10 gold after every wave."), {"lieutenant": "saltmother"}),
            ("ember_3", "Obsidian Crossing", "The road crosses itself on a field of black glass. Every tower there fires twice.",
             [(-1, 4), (18, 4), (18, 11), (9, 11), (9, -1)], 14, 1.0,
             ("attack_range", 1, -0.10, [], "Ash clouds: towers have 10% less range.")),
            ("ember_4", "Throne of Cinders", "At the caldera the Cinder Tyrant waits: the Warden of Fire, burning wrong. "
             "It shrugs off flame. Bring Storm or Void.",
             [(12, -1), (12, 2), (2, 2), (2, 12), (21, 12), (21, 2), (16, 2), (16, 8), (7, 8), (7, 15)], 15, 1.0, None,
             {"boss": "cinder_tyrant"}),
        ],
    },
    {
        "id": "thunder_steppe", "element": "storm", "name": "The Thunder Steppe",
        "tagline": "The Stone against the Sky",
        "description": "The high grass is flattened and the storms have stopped. Earth's horde climbs the "
                       "plateau, and the Splitters break into swarms that only lightning can catch.",
        "signature": "splitter", "second": "brute",
        "reward": ("Sigil of Thunder", "Storm towers attack 8% faster in every run.",
                   [("attacks_per_second", 1, 0.08, ["storm"])]),
        "stages": [
            ("storm_1", "Windswept Pass", "A narrow pass between standing stones. Thunder is waiting to be called.",
             [(-1, 11), (6, 11), (6, 4), (13, 4), (13, 10), (24, 10)], 10, 1.0, None),
            ("storm_2", "Galeback Ridge", "Splitters crack open on the ridge. Chain lightning loves a crowd.",
             [(-1, 3), (20, 3), (20, 7), (3, 7), (3, 11), (24, 11)], 12, 1.0,
             ("attacks_per_second", 1, 0.10, [], "Tailwind: towers attack 10% faster."), {"lieutenant": "gorrath"}),
            ("storm_3", "The Long Squall", "The road dives down and climbs back up three times. Long, but never far from a spire.",
             [(3, -1), (3, 12), (9, 12), (9, 2), (15, 2), (15, 12), (21, 12), (21, -1)], 14, 1.0,
             ("cost", 1, 0.15, [], "Thin air: towers cost 15% more.")),
            ("storm_4", "Eye of the Storm", "The Thunderhead spins at the centre of the last storm. Nothing slows it, "
             "and lightning only tickles. Fire and Nature will have to do.",
             [(-1, 1), (22, 1), (22, 13), (1, 13), (1, 4), (19, 4), (19, 10), (5, 10), (5, 7), (24, 7)], 15, 1.0, None,
             {"boss": "thunderhead"}),
        ],
    },
    {
        "id": "verdant_deep", "element": "nature", "name": "The Verdant Deep",
        "tagline": "The Hollow against the Grove",
        "description": "Something hollow has crept under the canopy. Its Menders walk the roots at night. "
                       "Poison stops their healing, and it spreads.",
        "signature": "mender", "second": "warded",
        "reward": ("Sigil of the Grove", "Nature towers deal 10% increased damage in every run.",
                   [("damage", 1, 0.10, ["nature"])]),
        "stages": [
            ("nature_1", "Mossy Trail", "Soft ground and quiet birds. The first hollow things are slow.",
             [(-1, 4), (9, 4), (9, 10), (17, 10), (17, 5), (24, 5)], 10, 1.0, None),
            ("nature_2", "Rootway", "The road threads between the roots of trees older than the ring.",
             [(-1, 12), (4, 12), (4, 2), (12, 2), (12, 12), (19, 12), (19, 2), (24, 2)], 12, 1.0,
             ("starting_lives", 0, 5, [], "Deep roots: +5 lives."), {"lieutenant": "pale_vesper"}),
            ("nature_3", "Bramble Maze", "Thorns everywhere. Warded beasts walk through poison as if it were rain.",
             [(-1, 7), (4, 7), (4, 1), (10, 1), (10, 13), (16, 13), (16, 1), (21, 1), (21, 9), (24, 9)], 14, 1.0,
             ("sell_refund", 0, 0.2, [], "Recycling: selling refunds 20% more.")),
            ("nature_4", "Heart of the Grove", "The Elder Broodmother nests in the oldest tree, shedding young as she walks. "
             "Fire and Storm will thin the brood.",
             [(11, 15), (11, 10), (2, 10), (2, 2), (21, 2), (21, 12), (15, 12), (15, 6), (7, 6), (7, -1)], 15, 1.0, None,
             {"boss": "broodmother"}),
        ],
    },
    {
        "id": "frostmere", "element": "water", "name": "Frostmere",
        "tagline": "The Flame against the Ice",
        "description": "The lake is boiling at the edges. Fire's horde marches across the ice, and its runners are "
                       "fast. Slow them, freeze them, drown them.",
        "signature": "runner", "second": "warded",
        "reward": ("Sigil of the Tide", "Water towers have 8% increased range in every run.",
                   [("attack_range", 1, 0.08, ["water"])]),
        "stages": [
            ("water_1", "Tidepool Shore", "Fishing huts and frozen nets. The first sparks skitter across the shingle.",
             [(-1, 2), (6, 2), (6, 9), (14, 9), (14, 5), (24, 5)], 10, 1.0, None),
            ("water_2", "Saltmarsh Bends", "Reed beds and narrow causeways. Runners come in long, quick lines.",
             [(-1, 6), (3, 6), (3, 12), (9, 12), (9, 3), (15, 3), (15, 12), (20, 12), (20, 6), (24, 6)], 12, 1.0,
             ("starting_gold", 0, 60, [], "Fishing fleet: start with 60 more gold."), {"lieutenant": "ashwick"}),
            ("water_3", "Frozen Causeway", "The causeway crosses the lake four times. The ice groans under the Warded.",
             [(-1, 13), (21, 13), (21, 9), (2, 9), (2, 5), (21, 5), (21, 1), (-1, 1)], 14, 1.0,
             ("gold_per_wave", 1, -0.3, [], "Frozen trade: 30% less gold after each wave.")),
            ("water_4", "The Drowned Throne", "The Tidal Leviathan rises from the black water: too big to slow, too old "
             "to freeze. Nature and Earth must break it.",
             [(-1, 7), (5, 7), (5, 2), (18, 2), (18, 12), (10, 12), (10, 5), (14, 5), (14, 15)], 15, 1.0, None,
             {"boss": "leviathan"}),
        ],
    },
    {
        "id": "sunscar_canyon", "element": "earth", "name": "Sunscar Canyon",
        "tagline": "The Sky against the Stone",
        "description": "Storm's horde pours down the canyon walls in armour. Earth's heavy blows and "
                       "shattering hits crack what lightning cannot.",
        "signature": "brute", "second": "splitter",
        "reward": ("Sigil of Stone", "Earth towers deal 10% increased damage in every run.",
                   [("damage", 1, 0.10, ["earth"])]),
        "stages": [
            ("earth_1", "Red Gulch", "Dust devils and red rock. The armoured ones are slow, at least.",
             [(4, -1), (4, 8), (12, 8), (12, 4), (19, 4), (19, 15)], 10, 1.0, None),
            ("earth_2", "Canyon Switchbacks", "The road zigzags down the canyon wall, five long terraces.",
             [(-1, 1), (21, 1), (21, 5), (2, 5), (2, 9), (21, 9), (21, 13), (-1, 13)], 12, 1.0,
             ("damage", 1, 0.10, ["earth"], "Bedrock: Earth towers deal a further 10% more damage."), {"lieutenant": "vholt"}),
            ("earth_3", "Mesa Loop", "A loop around a flat-topped mesa, then a sprint for the exit.",
             [(-1, 10), (7, 10), (7, 3), (16, 3), (16, 10), (10, 10), (10, 13), (24, 13)], 14, 1.0,
             ("starting_lives", 1, -0.25, [], "Rockfall: 25% fewer lives.")),
            ("earth_4", "Titan's Cradle", "The Mountain Titan wakes. Every hit under 22 damage bounces off its hide. "
             "Big blows, burns and poison find a way.",
             [(-1, 3), (6, 3), (6, 12), (17, 12), (17, 3), (10, 3), (10, 8), (24, 8)], 15, 1.0, None,
             {"boss": "mountain_titan"}),
        ],
    },
    {
        "id": "hollow_rift", "element": "void", "name": "The Hollow Rift",
        "tagline": "The Grove against the Dark",
        "description": "The rift where the ring cracked first. Nature's horde grows wild here, warded in bark, "
                       "and only the Void's curses and auras can tear it down.",
        "signature": "warded", "second": "mender",
        "reward": ("Sigil of the Hollow", "Void towers deal 10% increased damage in every run.",
                   [("damage", 1, 0.10, ["void"])]),
        "stages": [
            ("void_1", "Starless Path", "No stars over this road. The grass glows faintly purple.",
             [(-1, 5), (8, 5), (8, 11), (16, 11), (16, 3), (24, 3)], 10, 1.0, None),
            ("void_2", "Fractured Steps", "The ground is broken into floating steps.",
             [(-1, 12), (5, 12), (5, 8), (10, 8), (10, 3), (15, 3), (15, 10), (20, 10), (20, 1), (24, 1)], 12, 1.0,
             ("bounty_bonus", 0, 1, [], "Soul tithe: +1 gold for every kill."), {"lieutenant": "mother_briar"}),
            ("void_3", "Mirror Rift", "The road comes in at the top and leaves an arm's length away, the long way round.",
             [(11, -1), (11, 4), (3, 4), (3, 11), (20, 11), (20, 4), (13, 4), (13, -1)], 14, 1.0,
             ("attack_range", 1, 0.10, [], "Thin veil: towers have 10% more range.")),
            ("void_4", "Throne of the Hollow King", "The Hollow King rules the rift. Strike him down and he splits in two.",
             [(-1, 1), (19, 1), (19, 10), (3, 10), (3, 5), (14, 5), (14, 15)], 15, 1.0, None,
             {"boss": "hollow_king"}),
        ],
    },
    {
        "id": "convergence", "element": "", "name": "The Convergence",
        "tagline": "Every element, every road",
        "description": "With the six Wardens freed, every road on the ring leads to its broken heart. All six "
                       "elements are yours again, and every horde comes at once.",
        "requires": ["ember_reach", "thunder_steppe", "verdant_deep", "frostmere", "sunscar_canyon", "hollow_rift"],
        "signature": "warded", "second": "splitter",
        "reward": ("Crown of the Ring", "One more skill point at the start of every run, and every tower deals 5% more damage.",
                   [("starting_tree_points", 0, 1, []), ("damage", 2, 0.05, [])]),
        "stages": [
            ("converge_1", "Shattered Crossroads", "Two roads meet at the edge of the heartland. Two hordes walk them.",
             {"lanes": [[(-1, 2), (13, 2), (13, 9), (18, 9), (18, 5), (24, 5)],
                        [(4, 15), (4, 9), (13, 9), (18, 9), (18, 5), (24, 5)]]}, 16, 1.0, None,
             {"first_clear": 5, "lieutenant": "ashen_regent"}),
            ("converge_2", "Prism Wastes", "Glass plains where light splits into six colours. Three roads, one gate.",
             {"lanes": [[(-1, 2), (5, 2), (5, 7), (12, 7), (16, 7), (16, 12), (24, 12)],
                        [(9, -1), (9, 4), (12, 4), (12, 7), (16, 7), (16, 12), (24, 12)],
                        [(3, 15), (3, 11), (12, 11), (12, 7), (16, 7), (16, 12), (24, 12)]]}, 18, 1.0, None,
             {"first_clear": 5, "boss_pair": ["broodmother", "hollow_king"]}),
            ("converge_3", "Heart of the Ring", "Every road ends here. The Sundered Heart beats in the middle, a different "
             "colour with every beat.",
             {"lanes": [[(-1, 2), (4, 2), (4, 7), (12, 7), (12, 11), (19, 11), (19, 3), (22, 3), (22, 15)],
                        [(15, -1), (15, 5), (12, 5), (12, 7), (12, 11), (19, 11), (19, 3), (22, 3), (22, 15)],
                        [(6, 15), (6, 10), (9, 10), (9, 7), (12, 7), (12, 11), (19, 11), (19, 3), (22, 3), (22, 15)]]},
             20, 1.0, None,
             {"boss": "sundered_heart", "first_clear": 12,
              "echoes": {10: ["cinder_tyrant", "leviathan"], 15: ["thunderhead", "mountain_titan"]}}),
        ],
    },
]

# The horde's lieutenants, one per element campaign, at the end of its second stage. Their names and
# tricks live in data/enemies/<id>.tres; the names here are only for the rule text.
LIEUTENANT_NAMES = {
    "saltmother": "Saltmother Ourra, the Drowned Herald (shields the horde)",
    "gorrath": "Gorrath the Quarried, the Stone Herald (armoured, charges when wounded, breaks into boulders)",
    "pale_vesper": "the Pale Vesper, the Hollow Herald (raises shades, blinks down the road)",
    "ashwick": "Ashwick the Kindled, the Flame Herald (fast, silences towers)",
    "vholt": "Vholt Stormcrown, the Sky Herald (blinks, silences towers)",
    "mother_briar": "Mother Briar, the Thorn Herald (immune to effects, shields the horde, chokes towers)",
    "ashen_regent": "Cassivane, the Ashen Regent (shields his guard, silences towers, escapes when beaten)",
}

# ------------------------------------------------------------------------------------ the assault
# The last campaign: after the capital holds, the player takes the war to the enemy's fortress. One
# long stage (about 30 minutes) on a map whose right side is the enemy base. The horde comes down
# three roads; two of them have a gate. Phase 1: bring down the gates. Phase 2: the spires of the
# inner keep, which silence towers. Phase 3: the Black Throne, which releases the overlord. Towers
# may only be built up to a column that moves right with each phase. Waves start on their own after
# a short break and the last one repeats, stronger each time, until the fortress falls.
ASSAULT = {
    "id": "assault", "name": "The Crownless Citadel", "element": "",
    "tagline": "Through the Crack, into Nhal Vorath",
    "description": "Solenne held. Now we stop running. Through the Crack lies Nhal Vorath, the Crownless Citadel: "
                   "break its living gate, climb the Mirror Spire, and unmake the Sunderer on his throne.",
    "requires": ["convergence"],
    "reward": ("Lantern of the White Order", "Every tower deals 5% more damage and costs 5% less in every run.",
               [("damage", 2, 0.05, []), ("cost", 1, -0.05, [])]),
    "stage": {
        "id": "assault_1", "name": "Nhal Vorath",
        "story": "The citadel's roads run west toward our camp. Hold them, push your towers east, and bring Nhal Vorath "
                 "down piece by piece. It will not end until the Sunderer is finished.",
        "lanes": [
            [(22, 7), (16, 7), (16, 10), (10, 10), (10, 7), (-1, 7)],
            [(24, 2), (14, 2), (14, 4), (7, 4), (7, 7), (-1, 7)],
            [(24, 13), (13, 13), (13, 10), (10, 10), (10, 7), (-1, 7)],
        ],
        # (enemy, cell, phase, lane it releases onto, roads it closes when it falls, what it releases and
        # at what share of their health)
        "structures": [
            ("gatemaw", (17, 7), 1, 0, [1, 2], ["saltmother", "gorrath", "pale_vesper", "ashwick", "vholt", "mother_briar"], 0.15),
            ("mirror_spire", (20, 4), 2, 0, [], [], 1.0),
            ("crownless_throne", (23, 7), 3, 0, [], ["vael_orrun"], 0.15),
        ],
        "build_columns": [15, 18, -1],
        "auto_wave_delay": 12.0,
        "waves": 40,
        "first_clear": 20,
        "echoes": {12: ["thunderhead"], 20: ["broodmother", "leviathan"], 28: ["mountain_titan", "cinder_tyrant"],
                   36: ["hollow_king", "sundered_heart"]},
    },
}


# Per-stage numbers the balance pass tunes: health scale, starting gold, health growth per wave.
TUNING = {}
TUNING_PATH = os.path.join(os.path.dirname(__file__), "tuning.py")
if os.path.exists(TUNING_PATH):
    exec(open(TUNING_PATH).read())


# ------------------------------------------------------------------------------------ writers
class Tres:
    """Collects ext and sub resources for one .tres file."""

    def __init__(self, script_class: str):
        self.script_class = script_class
        self.ext = {}
        self.subs = []

    def script(self, path: str) -> str:
        if path not in self.ext:
            self.ext[path] = f"{len(self.ext) + 1}_s"
        return f'ExtResource("{self.ext[path]}")'

    def sub(self, script_path: str, fields: list) -> str:
        sid = f"r{len(self.subs) + 1}"
        self.subs.append((sid, [f"script = {self.script(script_path)}"] + fields))
        return f'SubResource("{sid}")'

    def write(self, path: str, fields: list) -> None:
        out = [f'[gd_resource type="Resource" script_class="{self.script_class}" format=3]', ""]
        for p, eid in self.ext.items():
            out.append(f'[ext_resource type="Script" path="{p}" id="{eid}"]')
        out.append("")
        for sid, f in self.subs:
            out.append(f'[sub_resource type="Resource" id="{sid}"]')
            out += f
            out.append("")
        out.append("[resource]")
        out += fields
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w") as fh:
            fh.write("\n".join(out) + "\n")


def sn(v: str) -> str:
    return f'&"{v}"'


def sn_array(values) -> str:
    return "Array[StringName]([%s])" % ", ".join(sn(v) for v in values)


def string(v: str) -> str:
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def cells(points) -> str:
    return "Array[Vector2i]([%s])" % ", ".join(f"Vector2i({x}, {y})" for x, y in points)


def typed(t: Tres, script_path: str, refs) -> str:
    return "Array[%s]([%s])" % (t.script(script_path), ", ".join(refs))


MOD = "res://scripts/data/modifier.gd"


def modifier(t: Tres, stat, kind, value, tags) -> str:
    fields = [f"stat = {sn(stat)}", f"kind = {kind}", f"value = {float(value)}"]
    if tags:
        fields.append(f"required_tags = {sn_array(tags)}")
    return t.sub(MOD, fields)


# ------------------------------------------------------------------------------------ maps
# Spawn holes per stage, by its place in an element campaign (the last is the Warden's stage). The
# Convergence and the skirmish maps get one each; the assault has gates instead.
HOLES = [1, 1, 1, 2]
CONVERGE_HOLES = 1
SKIRMISH_HOLES = 1


def curve_text(points) -> str:
    return "PackedVector2Array(%s)" % ", ".join(f"{x:g}, {y:g}" for x, y in points)


def write_map(stage_id, name, roads, order, biome, wave_set, holes=0, fixed_cells=(), skirmish=False,
              map_id=None, jitter=True):
    t = Tres("MapData")
    script = t.script("res://scripts/data/map_data.gd")
    sketch = roads["lanes"] if isinstance(roads, dict) else [roads]
    lanes = maps.build(stage_id, sketch, holes=holes, fixed_cells=fixed_cells, jitter=jitter)
    map_id = map_id or "c_" + stage_id
    fields = [f"script = {script}", f"id = {sn(map_id)}", f"display_name = {string(name)}",
              f"order = {order}", f"grid_size = Vector2i({maps.GRID[0]}, {maps.GRID[1]})", "cell_size = 64",
              f"waypoints = {cells(lanes[0][0])}", f"curve = {curve_text(lanes[0][1])}", f"wave_set = {sn(wave_set)}"]
    if len(lanes) > 1:
        refs = [t.sub("res://scripts/data/map_lane.gd", [f"waypoints = {cells(w)}", f"curve = {curve_text(c)}"])
                for w, c, _hole in lanes[1:]]
        fields.append(f"extra_lanes = {typed(t, 'res://scripts/data/map_lane.gd', refs)}")
    hole_lanes = [i for i, (_w, _c, hole) in enumerate(lanes) if hole]
    if hole_lanes:
        fields.append("hole_lanes = PackedInt32Array(%s)" % ", ".join(str(i) for i in hole_lanes))
    fields += [f"biome = {sn(biome)}"]
    if not skirmish:
        fields.append("skirmish = false")
    # Ext resources must come before sub resources that use them; Tres sorts that out.
    t.write(f"data/maps/{map_id}.tres", fields)
    return len(lanes)


# The skirmish maps, sketched the same way.
SKIRMISH_MAPS = [
    ("switchback", "Switchback", 0, [(-1, 2), (19, 2), (19, 6), (4, 6), (4, 10), (19, 10), (19, 13), (24, 13)]),
    ("serpentine", "Serpentine", 1, [(-1, 12), (4, 12), (4, 2), (10, 2), (10, 12), (16, 12), (16, 2), (21, 2), (21, 12), (24, 12)]),
]


def write_skirmish_maps():
    for map_id, name, order, sketch in SKIRMISH_MAPS:
        write_map(map_id, name, sketch, order, "meadow", "prototype", holes=SKIRMISH_HOLES, skirmish=True, map_id=map_id)


# ------------------------------------------------------------------------------------ waves
WAVE = "res://scripts/data/wave_data.gd"
GROUP = "res://scripts/data/spawn_group.gd"


def group(t, enemy, count, interval, delay=0.0, element=None, lane=-1):
    fields = [f"enemy = {sn(enemy)}", f"count = {max(1, int(count))}", f"spawn_interval = {interval}"]
    if delay:
        fields.append(f"start_delay = {delay}")
    if element:
        fields.append(f"element = {sn(element)}")
    if lane >= 0:
        fields.append(f"lane = {lane}")
    return t.sub(GROUP, fields)


def plan_waves(campaign, stage_index, n, extra):
    """The waves of one stage as lists of (enemy, count, interval, delay, element) with the wave's
    element and boss flag."""
    home = campaign["element"]
    sig, second = campaign["signature"], campaign["second"]
    converge = not home
    if converge:
        cycle = RING
    else:
        far = opposite(home)
        cycle = [far, neighbours(far)[0], far, neighbours(far)[1]]
    waves = []
    for w in range(1, n + 1):
        el = cycle[(w - 1 + stage_index) % len(cycle)]
        size = 8 + w + stage_index * 2
        kind = (w + stage_index) % 4
        groups = []
        if kind == 1:
            groups.append(("grunt", size, 0.8, 0.0))
        elif kind == 2:
            groups.append(("runner", size * 1.2, 0.5, 0.0))
        elif kind == 3:
            groups.append(("grunt", size * 0.7, 0.7, 0.0))
            groups.append(("brute", 1 + w // 3, 1.6, 4.0))
        else:
            groups.append(("grunt", size * 0.8, 0.6, 0.0))
            groups.append(("runner", size * 0.5, 0.45, 3.0))
        # The campaign's signature enemy from the second stage on (and late in the first), and its
        # second one from the third stage on.
        if (stage_index >= 1 and w >= 2) or (stage_index == 0 and w >= n - 3):
            groups.append((sig, 2 + w // 2 + stage_index, 1.1 if sig != "runner" else 0.5, 2.0))
        if stage_index >= 2 and w >= 4 and w % 2 == 0:
            groups.append((second, 2 + w // 3, 1.2 if second != "runner" else 0.5, 5.0))
        if converge and w >= 3:
            groups.append(("splitter" if w % 2 else "mender", 2 + w // 3, 1.0, 3.0))
        boss = False
        if w == n and "boss" in extra:
            boss = True
            groups = [(extra["boss"], 1, 1.0, 0.0), ("grunt", size * 0.6, 0.7, 3.0), (sig, 3 + stage_index, 1.0, 6.0)]
        elif w == n and "lieutenant" in extra:
            boss = True
            groups.append((extra["lieutenant"], 1, 1.0, 4.0))
        elif w == n and "boss_pair" in extra:
            boss = True
            groups = [(b, 1, 1.0, 6.0 * i) for i, b in enumerate(extra["boss_pair"])] + [("grunt", size * 0.6, 0.7, 3.0)]
        elif w == n and stage_index == 2:
            boss = True
            groups.append(("warden", 1, 1.0, 1.0))
        elif "echoes" in extra and w in extra["echoes"]:
            boss = True
            groups = [(b, 1, 1.0, 8.0 * i) for i, b in enumerate(extra["echoes"][w])] + [("runner", size * 0.6, 0.5, 2.0)]
        # In the Convergence each group of a wave carries its own element, so every wave mixes.
        if converge:
            groups = [g + (RING[(w + k * 2) % 6],) for k, g in enumerate(groups)]
        else:
            groups = [g + (None,) for g in groups]
        waves.append((el, boss, groups))
    return waves


def write_waves(campaign, stage_index, stage_id, name, n, extra):
    tune = TUNING.get(stage_id, {})
    t = Tres("WaveSet")
    script = t.script("res://scripts/data/wave_set.gd")
    refs = []
    for el, boss, groups in plan_waves(campaign, stage_index, n, extra):
        grefs = [group(t, e, c, i, d, ge) for e, c, i, d, ge in groups]
        fields = [f"element = {sn(el)}"]
        if boss:
            fields.append("is_boss = true")
            fields.append(f"health_multiplier = {tune.get('boss', 1.0)}")
        fields.append(f"groups = {typed(t, GROUP, grefs)}")
        refs.append(t.sub(WAVE, fields))
    wave_set = "c_" + stage_id
    t.write(f"data/waves/{wave_set}.tres", [
        f"script = {script}", f"id = {sn(wave_set)}", f"display_name = {string(name)}",
        f"health_growth = {tune.get('growth', 1.1)}", f"health_scale = {tune.get('health', 1.0)}",
        f"waves = {typed(t, WAVE, refs)}"])
    return wave_set


# ------------------------------------------------------------------------------------ campaigns
STAGE = "res://scripts/data/stage_data.gd"


def write_campaign(order, c):
    t = Tres("CampaignData")
    script = t.script("res://scripts/data/campaign_data.gd")
    home = c["element"]
    stage_refs = []
    biome = home or "heart"
    for i, stage in enumerate(c["stages"]):
        sid, name, story, roads, n, _health, twist = stage[:7]
        extra = stage[7] if len(stage) > 7 else {}
        tune = TUNING.get(sid, {})
        wave_set = write_waves(c, i, sid, name, n, extra)
        write_map(sid, name, roads, 100 + order * 10 + i, biome, wave_set,
                  holes=HOLES[min(i, len(HOLES) - 1)] if home else CONVERGE_HOLES)
        mods, rules = [], []
        allowed, starting = [], []
        if home:
            allowed = [home] + neighbours(home)
            starting = [ENTRY[home]]
            mods.append(modifier(t, "damage", 1, 0.20, [home]))
            rules.append(f"Home ground: {NAMES[home]} towers deal 20% more damage.")
            rules.append("Only %s, %s and %s can be drafted. You start with %s." % (
                NAMES[home], NAMES[allowed[1]], NAMES[allowed[2]], NAMES[home]))
            if extra.get("boss"):
                rules.append(f"The Warden resists {NAMES[home]}: bring a neighbour.")
        if extra.get("lieutenant"):
            rules.append(f"The last wave is led by {LIEUTENANT_NAMES[extra['lieutenant']]}.")
        else:
            rules.append("Every element can be drafted. Every wave mixes elements, and enemies come from several roads.")
        if twist:
            stat, kind, value, tags, text = twist
            mods.append(modifier(t, stat, kind, value, tags))
            rules.append(text)
        fields = [f"id = {sn(sid)}", f"display_name = {string(name)}",
                  f"description = {string(story)}", f"map = {sn('c_' + sid)}"]
        if extra.get("boss") or extra.get("boss_pair"):
            fields.append("is_guardian = true")
        if allowed:
            fields.append(f"allowed_elements = {sn_array(allowed)}")
        if starting:
            fields.append(f"starting_nodes = {sn_array(starting)}")
        fields.append(f"modifiers = {typed(t, MOD, mods)}")
        fields.append("rule_text = PackedStringArray(%s)" % ", ".join(string(r) for r in rules))
        if tune.get("gold"):
            fields.append(f"starting_gold = {tune['gold']}")
        if tune.get("lives"):
            fields.append(f"starting_lives = {tune['lives']}")
        first = extra.get("first_clear", 6 if extra.get("boss") else 3)
        fields.append(f"first_clear_points = {first}")
        stage_refs.append(t.sub(STAGE, fields))
    reward_name, reward_text, reward_mods = c["reward"]
    rmods = [modifier(t, *m) for m in reward_mods]
    fields = [f"script = {script}", f"id = {sn(c['id'])}", f"display_name = {string(c['name'])}",
              f"order = {order}", f"element = {sn(home)}", f"tagline = {string(c['tagline'])}",
              f"description = {string(c['description'])}"]
    if c.get("requires"):
        fields.append(f"requires_campaigns = {sn_array(c['requires'])}")
    fields += [f"stages = {typed(t, STAGE, stage_refs)}", f"reward_name = {string(reward_name)}",
               f"reward_description = {string(reward_text)}", f"reward_modifiers = {typed(t, MOD, rmods)}"]
    t.write(f"data/campaigns/{c['id']}.tres", fields)


def plan_assault_waves(stage):
    """The assault's waves: every group its own element, the mix growing heavier, and old bosses
    coming back every ten waves."""
    waves = []
    extras = ["mender", "splitter", "warded", "brute"]
    for w in range(1, stage["waves"] + 1):
        size = 10 + w
        groups = [("grunt", size * 0.7, 0.6, 0.0), ("runner", size * 0.5, 0.45, 3.0)]
        if w % 3 == 0:
            groups.append(("brute", 1 + w // 4, 1.4, 5.0))
        if w >= 4:
            groups.append((extras[w % 4], 2 + w // 4, 1.0, 6.0))
        if w >= 15 and w % 2 == 1:
            groups.append((extras[(w + 1) % 4], 2 + w // 6, 1.0, 9.0))
        boss = w in stage["echoes"]
        if boss:
            groups += [(b, 1, 1.0, 4.0 + 7.0 * i) for i, b in enumerate(stage["echoes"][w])]
        groups = [g + (RING[(w + k * 2) % 6],) for k, g in enumerate(groups)]
        waves.append((RING[w % 6], boss, groups))
    return waves


STRUCTURE = "res://scripts/data/structure_spec.gd"


def write_assault(order, c):
    st = c["stage"]
    sid = st["id"]
    tune = TUNING.get(sid, {})
    # Waves
    t = Tres("WaveSet")
    script = t.script("res://scripts/data/wave_set.gd")
    refs = []
    for el, boss, groups in plan_assault_waves(st):
        grefs = [group(t, e, n, i, d, ge) for e, n, i, d, ge in groups]
        fields = [f"element = {sn(el)}"]
        if boss:
            fields.append("is_boss = true")
            fields.append(f"health_multiplier = {tune.get('boss', 1.0)}")
        fields.append(f"groups = {typed(t, GROUP, grefs)}")
        refs.append(t.sub(WAVE, fields))
    wave_set = "c_" + sid
    t.write(f"data/waves/{wave_set}.tres", [
        f"script = {script}", f"id = {sn(wave_set)}", f"display_name = {string(st['name'])}",
        f"health_growth = {tune.get('growth', 1.09)}", f"health_scale = {tune.get('health', 1.0)}",
        f"waves = {typed(t, WAVE, refs)}"])
    cells_at = {e: maps.scale_cell(cell, st["lanes"]) for e, cell, *_ in st["structures"]}
    write_map(sid, st["name"], {"lanes": st["lanes"]}, 100 + order * 10, "void", wave_set,
              fixed_cells=[cell for _e, cell, *_ in st["structures"]], jitter=False)
    # Campaign and stage
    t = Tres("CampaignData")
    script = t.script("res://scripts/data/campaign_data.gd")
    srefs = []
    for e, _cell, ph, lane, closes, releases, release_health in st["structures"]:
        x, y = cells_at[e]
        fields = [f"enemy = {sn(e)}", f"cell = Vector2i({x}, {y})", f"phase = {ph}", f"lane = {lane}"]
        if closes:
            fields.append("closes_lanes = PackedInt32Array(%s)" % ", ".join(str(v) for v in closes))
        if releases:
            fields.append(f"releases = {sn_array(releases)}")
            if release_health != 1.0:
                fields.append(f"release_health = {release_health}")
        srefs.append(t.sub(STRUCTURE, fields))
    rules = [
        "Every element can be drafted. The horde comes down three roads from the fortress.",
        "The Black Gate: bring down the Gatemaw. It closes the two flank roads, and the six Heralds return as Echoes.",
        "The Mirror Spire: topple it. It silences towers near it.",
        "The Crownless Throne: break it, then unmake Vael-Orrun before he reaches your camp.",
        "You can only build on ground you hold: it moves east as each phase falls.",
        "Waves start on their own %d seconds after the last one (Space calls the next one early). "
        "When the waves run out, the last one comes again, stronger." % int(st["auto_wave_delay"]),
    ]
    fields = [f"id = {sn(sid)}", f"display_name = {string(st['name'])}", f"description = {string(st['story'])}",
              f"map = {sn('c_' + sid)}", "is_guardian = true", f"modifiers = {typed(t, MOD, [])}",
              "rule_text = PackedStringArray(%s)" % ", ".join(string(r) for r in rules)]
    if tune.get("gold"):
        fields.append(f"starting_gold = {tune['gold']}")
    if tune.get("lives"):
        fields.append(f"starting_lives = {tune['lives']}")
    fields += [f"first_clear_points = {st['first_clear']}",
               f"structures = {typed(t, STRUCTURE, srefs)}",
               "build_columns = PackedInt32Array(%s)" % ", ".join(
                   str(maps.scale_column(v, st["lanes"])) for v in st["build_columns"]),
               f"auto_wave_delay = {float(st['auto_wave_delay'])}"]
    stage_ref = t.sub(STAGE, fields)
    reward_name, reward_text, reward_mods = c["reward"]
    rmods = [modifier(t, *m) for m in reward_mods]
    fields = [f"script = {script}", f"id = {sn(c['id'])}", f"display_name = {string(c['name'])}",
              f"order = {order}", f"element = {sn('')}", f"tagline = {string(c['tagline'])}",
              f"description = {string(c['description'])}", f"requires_campaigns = {sn_array(c['requires'])}",
              f"stages = {typed(t, STAGE, [stage_ref])}", f"reward_name = {string(reward_name)}",
              f"reward_description = {string(reward_text)}", f"reward_modifiers = {typed(t, MOD, rmods)}"]
    t.write(f"data/campaigns/{c['id']}.tres", fields)


def main():
    for order, c in enumerate(CAMPAIGNS):
        write_campaign(order, c)
    write_assault(len(CAMPAIGNS), ASSAULT)
    write_skirmish_maps()
    print("Wrote %d campaigns and %d stages" % (len(CAMPAIGNS) + 1, sum(len(c["stages"]) for c in CAMPAIGNS) + 1))


if __name__ == "__main__":
    main()
