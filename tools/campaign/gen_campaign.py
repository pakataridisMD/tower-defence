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
# The last campaign: after the capital holds, the player takes the war to Nhal Vorath, the Crownless
# Citadel. One long stage of 40 waves (about 30 minutes) on a map whose right side is the citadel.
# The horde pours out of its three gates. Act 1 (waves 1-38): hold the roads; towers cannot touch the
# citadel. Act 2 (wave 39): Vael-Orrun comes down the road himself, and changes into a worse form
# twice before he breaks and flees back inside. Act 3 (wave 40): the roles turn. The player musters
# soldiers, war machines and every hero (data/allies, tools/allies/gen_allies.py) who march up the
# roads; the citadel defends with its spires and a horde that never stops coming, and the towers hold
# our camp. Only the units can bring the citadel down. When it falls, the truth about Vael-Orrun.
ASSAULT = {
    "id": "assault", "name": "The Crownless Citadel", "element": "",
    "tagline": "Through the Crack, into Nhal Vorath",
    "description": "Solenne held. Now we stop running. Through the Crack lies Nhal Vorath, the Crownless Citadel, "
                   "the root of every horde. Hold its roads, break the Sunderer when he comes, then march on it "
                   "with every soldier and hero we have.",
    "requires": ["convergence"],
    "reward": ("Lantern of the White Order", "Every tower deals 5% more damage and costs 5% less in every run.",
               [("damage", 2, 0.05, []), ("cost", 1, -0.05, [])]),
    "stage": {
        "id": "assault_1", "name": "Nhal Vorath",
        "story": "The citadel's three gates open toward our camp. Hold the roads until the Sunderer comes, "
                 "break him, then muster the army and take the citadel down.",
        # Three roads out of the citadel's gates on its west face.
        "lanes": [
            [(19, 7), (15, 7), (15, 10), (10, 10), (10, 7), (-1, 7)],
            [(19, 5), (17, 5), (17, 2), (7, 2), (7, 7), (-1, 7)],
            [(19, 9), (17, 9), (17, 13), (12, 13), (12, 10), (10, 10), (10, 7), (-1, 7)],
        ],
        # The roads keep this many columns at the right edge of the board free: the citadel stands there.
        "reserve": 8,
        # (enemy, centre cell, phase, footprint corners) in board cells of the finished map.
        "citadel": ("nhal_vorath", (36, 12), 3, ((31, 2), (41, 23))),
        # Towers can be built up to this column (board cells); the gates open at column 30.
        "build_column": 28,
        "auto_wave_delay": 8.0,
        "waves": 40,
        "boss_wave": 39,
        "counter_wave": 40,
        "war_chest": 1500,
        "counter_income": 14.0,
        "first_clear": 20,
        # An Echo of one of the six Heralds every sixth wave, and the Wardens' mad shapes with them later.
        "echoes": {6: ["saltmother"], 12: ["gorrath", "thunderhead"], 18: ["pale_vesper"],
                   24: ["ashwick", "broodmother", "leviathan"], 30: ["vholt", "mountain_titan", "cinder_tyrant"],
                   36: ["mother_briar", "hollow_king", "sundered_heart"]},
        # Wave 39: Vael-Orrun himself, with the horde around him.
        "sunderer": ["vael_orrun"],
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


def build_roads(stage_id, roads, holes=0, fixed_cells=(), jitter=True):
    """The stage's roads on the big board: [(waypoints, curve, is_hole)], sketch lanes first."""
    sketch = roads["lanes"] if isinstance(roads, dict) else [roads]
    return maps.build(stage_id, sketch, holes=holes, fixed_cells=fixed_cells, jitter=jitter)


def write_map(stage_id, name, roads, order, biome, wave_set, holes=0, fixed_cells=(), skirmish=False,
              map_id=None, jitter=True, built=None):
    t = Tres("MapData")
    script = t.script("res://scripts/data/map_data.gd")
    lanes = built or build_roads(stage_id, roads, holes=holes, fixed_cells=fixed_cells, jitter=jitter)
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
# A wave is a short story told in beats: it opens (a marching column or stragglers), builds through
# a few middle beats (runner packs, brutes under escort, a flank attack down a second road, the
# campaign's own enemies in packs...) and closes with a surge that gets faster and faster. Later
# waves and later stages have more middle beats, so they last longer; the enemies walk no slower.
# Beats overlap a little so there is always something on the road, with short breathers between.
WAVE = "res://scripts/data/wave_data.gd"
GROUP = "res://scripts/data/spawn_group.gd"

# SpawnGroup.Pattern
STREAM, PACKS, SURGE, SCATTER = 0, 1, 2, 3

ENEMY_NAMES = {"grunt": "Grunt", "runner": "Runner", "brute": "Brute", "mender": "Mender", "splitter": "Splitter",
               "warded": "Warded", "shardling": "Shardling"}


def G(enemy, count, interval, delay=0.0, pattern=STREAM, lane=-1, pack=5, gap=4.0, element=None):
    """One spawn group. Counts are rounded and never below one."""
    return {"enemy": enemy, "count": max(1, int(round(count))), "interval": round(interval, 3),
            "delay": round(delay, 2), "pattern": pattern, "lane": lane, "pack": pack, "gap": gap, "element": element}


def span(g):
    """Seconds from a group's first enemy to its last, as SpawnGroup.spawn_times lays them out
    (SCATTER on average)."""
    n, i = g["count"], g["interval"]
    if n <= 1:
        return 0.0
    if g["pattern"] == PACKS:
        packs = (n - 1) // max(g["pack"], 1)
        return (n - 1) * i + packs * g["gap"]
    if g["pattern"] == SURGE:
        return sum(i * (2.0 + (0.34 - 2.0) * k / (n - 1)) for k in range(1, n))
    return (n - 1) * i


def group(t, g):
    fields = [f"enemy = {sn(g['enemy'])}", f"count = {g['count']}", f"spawn_interval = {g['interval']}"]
    if g["delay"]:
        fields.append(f"start_delay = {g['delay']}")
    if g.get("element"):
        fields.append(f"element = {sn(g['element'])}")
    if g["lane"] >= 0:
        fields.append(f"lane = {g['lane']}")
    if g["pattern"] != STREAM:
        fields.append(f"pattern = {g['pattern']}")
    if g["pattern"] == PACKS:
        fields += [f"pack_size = {g['pack']}", f"pack_gap = {g['gap']}"]
    return t.sub(GROUP, fields)


class Wave:
    """Collects a wave's beats. Each beat starts where the last one began to tail off."""

    def __init__(self, ctx):
        self.ctx = ctx
        self.groups = []
        self.words = []
        self.t = 0.0

    def beat(self, word, groups, overlap=0.75, rest=1.5):
        start = self.t
        length = 0.0
        for g in groups:
            g["delay"] = round(g["delay"] + start, 2)
            length = max(length, g["delay"] - start + span(g))
        self.groups += groups
        if word and word not in self.words:
            self.words.append(word)
        self.t = start + length * overlap + rest
        return start

    def length(self):
        return max((g["delay"] + span(g) for g in self.groups), default=0.0)


def tight(c, interval):
    """How close together a fast pack runs: loose in a stage's first waves, while the player has only
    a few towers (a tower fires a few times a second however weak the enemy), tight from wave 5 on."""
    ease = min(max((c["w"] - 1) / 4.0, 0.0), 1.0)
    return interval + (0.6 - interval) * (1.0 - ease)


def interval_for(enemy, slow=1.1, fast=0.5):
    return fast if enemy in ("runner", "shardling") else slow


# The beats. Each takes the wave's context (pressure p, lanes, the campaign's enemies) and adds itself.
def beat_column(w, c):
    w.beat("a marching column", [G("grunt", 6 * c["p"], 0.8)])


def beat_stragglers(w, c):
    w.beat("stragglers", [G("grunt", 4 * c["p"], 1.0, pattern=SCATTER), G("runner", 3 * c["p"], 1.3, 1.5, SCATTER)])


def beat_runner_packs(w, c):
    size = 4 + min(int(c["p"]), 3)
    packs = 2 + int(c["p"] * 0.8)
    w.beat("runner packs", [G("runner", size * packs, tight(c, 0.28), pattern=PACKS, pack=size, gap=3.5)])


def beat_escort(w, c):
    brutes = 1 + int(c["p"])
    # Three grunts round each brute: a pack every three seconds, in step with the brutes.
    w.beat("brutes under escort", [G("brute", brutes, 3.0, 0.6),
                                   G("grunt", 3 * brutes, 0.35, pattern=PACKS, pack=3, gap=3.0 - 3 * 0.35)])


def beat_flank(w, c):
    if c["lanes"] > 1:
        side = 1 + (c["w"] % (c["lanes"] - 1))
        w.beat("a flank attack", [G("grunt", 4 * c["p"], 0.9, lane=0),
                                  G("runner", 5 * (1 + int(c["p"] * 0.6)), tight(c, 0.3), 2.0, PACKS, lane=side, pack=5, gap=3.0)])
    else:
        # One road: a lull, then a tight rush.
        w.beat("an ambush", [G("runner", 6 + 3 * c["p"], tight(c, 0.22), 3.0, PACKS, pack=6 + int(c["p"]), gap=2.5)], rest=1.0)


def beat_pincer(w, c):
    lanes = c["lanes"]
    a, b = c["w"] % lanes, (c["w"] + 1) % lanes
    n = 4 + int(c["p"] * 2)
    w.beat("a pincer", [G("grunt", n, 0.3, 0.0, PACKS, lane=a, pack=4, gap=3.0),
                        G("grunt", n, 0.3, 0.0, PACKS, lane=b, pack=4, gap=3.0),
                        G("runner", 2 + c["p"] * 2, 0.4, 2.0, lane=-1)])


def beat_signature(w, c):
    sig = c["sig"]
    n = 2 + c["w"] // 2 + c["stage"]
    if sig == "runner":
        w.beat("runner packs", [G("runner", n * 2, tight(c, 0.25), pattern=PACKS, pack=5, gap=3.0)])
    else:
        w.beat(ENEMY_NAMES[sig] + " packs", [G(sig, n, 0.55, 0.0, PACKS, pack=3, gap=3.0),
                                            G("grunt", 3 * c["p"], 0.9, 1.0)])


def beat_second(w, c):
    second = c["second"]
    n = 2 + c["w"] // 3
    w.beat(ENEMY_NAMES[second] + "s in a line", [G(second, n, interval_for(second, 1.2), 0.0),
                                                 G("runner", 2 * c["p"], 0.6, 2.0, SCATTER)])


def beat_swarm(w, c):
    kind = "splitter" if c["w"] % 2 else "mender"
    w.beat("a mixed swarm", [G(kind, 2 + c["w"] // 3, 1.0, pattern=SCATTER), G("grunt", 3 * c["p"], 0.7, 1.0, SCATTER)])


def beat_surge(w, c):
    w.beat("a closing surge", [G("grunt", 6 * c["p"], 0.7, pattern=SURGE),
                               G("runner", 3 * c["p"], 0.55, 2.0, SURGE)], rest=0.0)


def beat_bosses(w, bosses, gap):
    w.beat("", [G(b, 1, 1.0, gap * i) for i, b in enumerate(bosses)], overlap=0.0, rest=4.0)


def compose(c, required, closer=True):
    """A wave from its context: an opener, the required beats, more middle beats picked from the
    pool by the wave's number, and the closing surge."""
    w = Wave(c)
    (beat_column if c["w"] == 1 or c["w"] % 3 != 0 else beat_stragglers)(w, c)
    pool = [beat_runner_packs, beat_flank] if c["w"] > 2 else [beat_stragglers, beat_runner_packs]
    if c["w"] >= 3:
        pool.append(beat_escort)
    if c["lanes"] > 1 and c["w"] >= 4:
        pool.append(beat_pincer)
    extra = max(c["beats"] - len(required), 1)
    start = (c["w"] * 2 + c["stage"]) % len(pool)
    picked = [pool[(start + k) % len(pool)] for k in range(extra)]
    # Picked and required beats take turns, so the campaign's own enemies come in the middle.
    middle = []
    for k in range(max(len(picked), len(required))):
        middle += picked[k:k + 1] + required[k:k + 1]
    for b in middle:
        b(w, c)
    if closer:
        beat_surge(w, c)
    return w


def context(campaign, stage_index, w, n, lanes, converge=False):
    p = 1.0 + 0.08 * (w - 1) + 0.15 * stage_index + (0.25 if converge else 0.0)
    # The first waves are a warm-up while the player has only their first towers: fewer beats,
    # and the waves after it build up slowly.
    beats = 1 + w // 3 + stage_index // 2 + (1 if converge else 0)
    p *= 0.7 + 0.3 * min((w - 1) / 4.0, 1.0)
    return {"w": w, "n": n, "stage": stage_index, "p": p, "beats": beats, "lanes": lanes,
            "sig": campaign.get("signature", "grunt"), "second": campaign.get("second", "brute")}


def plan_waves(campaign, stage_index, n, extra, lanes=1):
    """The waves of one stage: (element, boss flag, groups, description) for each."""
    home = campaign["element"]
    sig = campaign["signature"]
    converge = not home
    if converge:
        cycle = RING
    else:
        far = opposite(home)
        cycle = [far, neighbours(far)[0], far, neighbours(far)[1]]
    waves = []
    for w in range(1, n + 1):
        el = cycle[(w - 1 + stage_index) % len(cycle)]
        c = context(campaign, stage_index, w, n, lanes, converge)
        required = []
        # The campaign's signature enemy from the second stage on (and late in the first), and its
        # second one from the third stage on.
        if (stage_index >= 1 and w >= 2) or (stage_index == 0 and w >= n - 3):
            required.append(beat_signature)
        if stage_index >= 2 and w >= 4 and w % 2 == 0:
            required.append(beat_second)
        if converge and w >= 3:
            required.append(beat_swarm)
        boss = False
        if w == n and "boss" in extra:
            # The Warden: an opening column, then the Warden under escort, its brood behind it.
            boss = True
            wave = Wave(c)
            beat_column(wave, c)
            beat_bosses(wave, [extra["boss"]], 0.0)
            beat_escort(wave, c)
            beat_signature(wave, c)
            beat_flank(wave, c)
            beat_surge(wave, c)
            # The Warden leads the list (the game and the tests look for it there).
            wave.groups.sort(key=lambda g: 0 if g["enemy"] == extra["boss"] else 1)
        elif w == n and "boss_pair" in extra:
            boss = True
            wave = Wave(c)
            beat_column(wave, c)
            beat_bosses(wave, extra["boss_pair"], 6.0)
            beat_runner_packs(wave, c)
            beat_swarm(wave, c)
            (beat_pincer if lanes > 1 else beat_flank)(wave, c)
            beat_surge(wave, c)
            wave.groups.sort(key=lambda g: 0 if g["enemy"] in extra["boss_pair"] else 1)
        elif "echoes" in extra and w in extra["echoes"]:
            boss = True
            wave = Wave(c)
            beat_stragglers(wave, c)
            beat_bosses(wave, extra["echoes"][w], 8.0)
            beat_runner_packs(wave, c)
            beat_swarm(wave, c)
            beat_flank(wave, c)
            beat_surge(wave, c)
        else:
            wave = compose(c, required, closer=not (w == n and ("lieutenant" in extra or stage_index == 2)))
            if w == n and "lieutenant" in extra:
                # The Herald walks in after the opening beats, then the horde surges behind it.
                boss = True
                beat_bosses(wave, [extra["lieutenant"]], 0.0)
                beat_surge(wave, c)
            elif w == n and stage_index == 2:
                boss = True
                beat_bosses(wave, ["warden"], 0.0)
                beat_surge(wave, c)
        groups = wave.groups
        # In the Convergence each group of a wave carries its own element, so every wave mixes.
        if converge:
            for k, g in enumerate(groups):
                g["element"] = RING[(w + k * 2) % 6]
        waves.append((el, boss, groups, describe(wave.words)))
    return waves


def describe(words):
    """'A marching column, runner packs and a closing surge.'"""
    if not words:
        return ""
    text = words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]
    return text[0].upper() + text[1:] + "."


def wave_fields(t, el, boss, groups, text, boss_health):
    grefs = [group(t, g) for g in groups]
    fields = [f"element = {sn(el)}"]
    if boss:
        fields.append("is_boss = true")
        fields.append(f"health_multiplier = {boss_health}")
    if text:
        fields.append(f"description = {string(text)}")
    fields.append(f"groups = {typed(t, GROUP, grefs)}")
    return fields


def write_waves(campaign, stage_index, stage_id, name, n, extra, lanes=1):
    tune = TUNING.get(stage_id, {})
    t = Tres("WaveSet")
    script = t.script("res://scripts/data/wave_set.gd")
    refs = []
    for el, boss, groups, text in plan_waves(campaign, stage_index, n, extra, lanes):
        refs.append(t.sub(WAVE, wave_fields(t, el, boss, groups, text, tune.get("boss", 1.0))))
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
        holes = HOLES[min(i, len(HOLES) - 1)] if home else CONVERGE_HOLES
        built = build_roads(sid, roads, holes=holes)
        wave_set = write_waves(c, i, sid, name, n, extra, len(built))
        write_map(sid, name, roads, 100 + order * 10 + i, biome, wave_set, built=built)
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
    coming back as Echoes. Its waves start on their own, so they stay a little shorter than a
    campaign stage's late waves. The boss wave brings the Sunderer; the counter-attack's wave is the
    citadel's garrison, which comes again and again until the citadel falls."""
    waves = []
    extras = ["mender", "splitter", "warded", "brute"]
    lanes = len(stage["lanes"])
    for w in range(1, stage["waves"] + 1):
        horde = {"signature": extras[w % 4], "second": extras[(w + 1) % 4]}
        c = context(horde, 1, w, stage["waves"], lanes)
        # Forty waves have to fit in about half an hour, so each is short: one beat and a surge early,
        # three by the end.
        c["p"] = 1.0 + 0.04 * (min(w, stage["boss_wave"]) - 1)
        c["beats"] = 1 + w // 15
        required = []
        if w >= 4:
            required.append(beat_signature)
        if w >= 15 and w % 2 == 1 and horde["second"] != "runner":
            required.append(beat_second)
        if w % 3 == 0:
            required.append(beat_escort)
        if w == stage["counter_wave"]:
            # The garrison: a steady march down every road, lighter than a late wave, because it
            # never stops coming and the towers fight it while the army marches.
            c["p"] = 0.9
            c["beats"] = 2
            wave = compose(c, [beat_signature, beat_escort], closer=False)
            text = "The citadel's garrison. It keeps coming until Nhal Vorath falls."
        else:
            wave = compose(c, required, closer=False)
            text = None
        boss = w in stage["echoes"] or w == stage["boss_wave"]
        if w in stage["echoes"]:
            beat_bosses(wave, stage["echoes"][w], 7.0)
        if w == stage["boss_wave"]:
            beat_bosses(wave, stage["sunderer"], 0.0)
        if w != stage["counter_wave"]:
            beat_surge(wave, c)
        for k, g in enumerate(wave.groups):
            g["element"] = RING[(w + k * 2) % 6]
        waves.append((RING[w % 6], boss, wave.groups, text or describe(wave.words)))
    return waves


# ------------------------------------------------------------------------------------ skirmish
# The skirmish waves (data/waves/prototype.tres), shared by every skirmish map: ten waves of the
# first horde (Grunts, Runners, Brutes) cycling Fire, Storm and Nature, and a Warden at the end.
SKIRMISH = {"id": "prototype", "name": "Skirmish waves", "waves": 10, "growth": 1.12,
            "elements": ["fire", "storm", "nature"], "boss": "warden"}


def plan_skirmish_waves(sk):
    waves = []
    horde = {"signature": "brute", "second": "brute"}
    n = sk["waves"]
    for w in range(1, n + 1):
        el = sk["elements"][(w - 1) % len(sk["elements"])]
        c = context(horde, 0, w, n, 1)
        boss = w == n
        wave = compose(c, [], closer=not boss)
        if boss:
            beat_bosses(wave, [sk["boss"]], 0.0)
            beat_surge(wave, c)
            wave.groups.sort(key=lambda g: 0 if g["enemy"] == sk["boss"] else 1)
        waves.append((el, boss, wave.groups, describe(wave.words)))
    return waves


def write_skirmish(sk):
    tune = TUNING.get(sk["id"], {})
    t = Tres("WaveSet")
    script = t.script("res://scripts/data/wave_set.gd")
    refs = [t.sub(WAVE, wave_fields(t, el, boss, groups, text, tune.get("boss", 1.0)))
            for el, boss, groups, text in plan_skirmish_waves(sk)]
    t.write(f"data/waves/{sk['id']}.tres", [
        f"script = {script}", f"id = {sn(sk['id'])}", f"display_name = {string(sk['name'])}",
        f"health_growth = {tune.get('growth', sk['growth'])}", f"health_scale = {tune.get('health', 1.0)}",
        f"waves = {typed(t, WAVE, refs)}"])


STRUCTURE = "res://scripts/data/structure_spec.gd"


def write_assault(order, c):
    st = c["stage"]
    sid = st["id"]
    tune = TUNING.get(sid, {})
    # Waves
    t = Tres("WaveSet")
    script = t.script("res://scripts/data/wave_set.gd")
    refs = []
    for el, boss, groups, text in plan_assault_waves(st):
        refs.append(t.sub(WAVE, wave_fields(t, el, boss, groups, text, tune.get("boss", 1.0))))
    wave_set = "c_" + sid
    t.write(f"data/waves/{wave_set}.tres", [
        f"script = {script}", f"id = {sn(wave_set)}", f"display_name = {string(st['name'])}",
        f"health_growth = {tune.get('growth', 1.09)}", f"health_scale = {tune.get('health', 1.0)}",
        f"waves = {typed(t, WAVE, refs)}"])
    enemy, (x, y), phase, ((ax, ay), (bx, by)) = st["citadel"]
    with maps.reserve_right(st["reserve"]):
        write_map(sid, st["name"], {"lanes": st["lanes"]}, 100 + order * 10, "void", wave_set, jitter=False)
    # Campaign and stage
    t = Tres("CampaignData")
    script = t.script("res://scripts/data/campaign_data.gd")
    fields = [f"enemy = {sn(enemy)}", f"cell = Vector2i({x}, {y})", f"phase = {phase}", "lane = 0",
              f"footprint = Rect2i({ax}, {ay}, {bx - ax + 1}, {by - ay + 1})"]
    srefs = [t.sub(STRUCTURE, fields)]
    front = st["build_column"]
    rules = [
        "Every element can be drafted. The horde pours out of the citadel's three gates.",
        "Waves 1 to %d: hold the roads. Nothing you build can touch the citadel." % (st["boss_wave"] - 1),
        "Wave %d: Vael-Orrun comes himself. Break him three times, in three forms, before he reaches your camp." % st["boss_wave"],
        "Wave %d: the counter-attack. Muster soldiers, war machines and every hero onto the roads to take the "
        "citadel down. Your towers hold the camp; the garrison keeps coming until the citadel falls." % st["counter_wave"],
        "Waves start on their own %d seconds after the last one (Space calls the next one early)." % int(st["auto_wave_delay"]),
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
               "build_columns = PackedInt32Array(%d, %d, %d)" % (front, front, front),
               f"auto_wave_delay = {float(st['auto_wave_delay'])}",
               f"boss_wave = {st['boss_wave']}", f"counter_wave = {st['counter_wave']}",
               f"war_chest = {tune.get('war_chest', st['war_chest'])}",
               f"counter_income = {float(st['counter_income'])}"]
    stage_ref = t.sub(STAGE, fields)
    reward_name, reward_text, reward_mods = c["reward"]
    rmods = [modifier(t, *m) for m in reward_mods]
    fields = [f"script = {script}", f"id = {sn(c['id'])}", f"display_name = {string(c['name'])}",
              f"order = {order}", f"element = {sn('')}", f"tagline = {string(c['tagline'])}",
              f"description = {string(c['description'])}", f"requires_campaigns = {sn_array(c['requires'])}",
              f"stages = {typed(t, STAGE, [stage_ref])}", f"reward_name = {string(reward_name)}",
              f"reward_description = {string(reward_text)}", f"reward_modifiers = {typed(t, MOD, rmods)}"]
    t.write(f"data/campaigns/{c['id']}.tres", fields)


# The six lands are fought in order, each opening when the one before it is finished: every stage is
# tuned for the meta tree, sigils and heroes a player has by then (tools/meta_pacing.gd), which only
# holds if they arrive in that order.
def chain_lands():
    lands = [c for c in CAMPAIGNS if c["element"]]
    for before, land in zip(lands, lands[1:]):
        land.setdefault("requires", [before["id"]])


def main():
    chain_lands()
    for order, c in enumerate(CAMPAIGNS):
        write_campaign(order, c)
    write_assault(len(CAMPAIGNS), ASSAULT)
    write_skirmish_maps()
    write_skirmish(SKIRMISH)
    print("Wrote %d campaigns and %d stages" % (len(CAMPAIGNS) + 1, sum(len(c["stages"]) for c in CAMPAIGNS) + 1))


if __name__ == "__main__":
    main()
