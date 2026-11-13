#!/usr/bin/env python3
"""Writes the in-game skill tree (the T screen in a run) to data/trees/in_run/*.tres.

Edit the tables in this file and rerun; do not edit the .tres files by hand. The script deletes the
tree files it no longer writes, checks the layout (no two nodes too close, no link running through a
node, every node reachable) and prints what the tree costs.

    python3 tools/web/gen_skill_web.py                      # write the tree
    python3 tools/web/gen_skill_web.py --preview out.png    # also draw a quick layout picture

The tree works like Element TD 2's element levels, only bigger. It is where towers are unlocked
during a run. (The Talents tree, tools/meta/gen_meta_tree.py, is the other half of the design: it
stays between runs, gives lasting bonuses and decides which towers this tree may offer at all.)

  * Six columns, one per element, side by side in ring order. Each climbs from the Origin at the
    bottom through six element levels (Fire I to Fire VI): the vertical path of that element.
  * Level I opens the element's own tower and its skill; level III its long-range tower.
  * Every dual and triple tower is a node of its own (a combination node, TreeNodeData.requires):
    it shows the tower's picture, needs a level of each of its elements and is taken with points
    like any node. Neighbour elements' duals sit on the level II line between their two columns
    and need level II of both. Duals of elements two apart and all twenty triples need level III
    and sit in blocks on the level III line. Duals of opposite elements need level IV and sit on
    the level IV line. (The Talents tree's Forge talents decide which of these nodes are open.)
  * Between two levels sits a branch: a row of three or four options. The path up runs through the
    branch, so a level can only be taken once at least one option of the branch below it is. A
    branch of three lets the player pick one option, a branch of four lets them pick two
    (TreeNodeData.choice_group and choice_limit).
  * Above level VI, two keystones: a pick-one choice. Three of them (Focus, Overcharge, Hoard) stay
    locked until the Talents tree adds them.

Costs climb with the level (1, 1, 2, 3, 4, 5 for the levels, 1 to 4 for the options of the branches
between them, 6 for a keystone). Runs pay three skill points a wave (data/rules/run_rules.tres), so
two neighbour elements reach level II (and their dual tower) after the first wave.

Ids other files use are kept: <element>_entry (level I: stage starting nodes, skills), <element>_core
(level III, in the long-range towers' requires_nodes), <element>_notable (level IV) and the
keystones' ids. A combination node's id is tower_<tower id>.
"""

from __future__ import annotations

import math
import os
import re
import sys
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data", "trees", "in_run")
TOWER_DIR = os.path.join(ROOT, "data", "towers")

# TreeNodeData.Kind
START, ENTRY, MINOR, NOTABLE, BRIDGE, KEYSTONE = range(6)
# Modifier.Kind
FLAT, INC, MORE = range(3)

ELEMENTS = ["fire", "storm", "nature", "water", "earth", "void"]
NAMES = {"fire": "Fire", "storm": "Storm", "nature": "Nature", "water": "Water", "earth": "Earth", "void": "Void"}
SKILLS = {"fire": "Meteor", "storm": "Surge", "nature": "Entangle", "water": "Tidal Wave", "earth": "Earthquake",
          "void": "Doom"}
ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

# Layout, in tree units (pixels at the default zoom); screen y points down, so the tree climbs
# towards negative y. scripts/game/game.gd draws a line and a label at each level (WEB_LEVELS).
COLUMN_WIDTH = 400
LEVEL_COUNT = 6
FIRST_LEVEL_Y = -230
LEVEL_STEP = 270  # from one level to the next; the branch between them sits halfway
OPTION_GAP = 92  # between two options of a branch
KEYSTONE_RISE = 160
KEYSTONE_SPREAD = 85

# Ids of the six levels of an element. Levels I, III and IV keep the old web's ids.
LEVEL_IDS = ["%s_entry", "%s_level2", "%s_core", "%s_notable", "%s_level5", "%s_level6"]
LEVEL_COST = [1, 1, 2, 3, 4, 5]
# The branch above level k (k from 1): what one of its options costs, and how many may be picked.
BRANCH_COST = [1, 1, 2, 3, 4]
KEYSTONE_COST = 6
# Combination nodes: what a dual costs by how far apart its elements are on the ring, and a triple.
DUAL_COST = {1: 1, 2: 2, 3: 3}
TRIPLE_COST = 3
# The level a dual's node needs of both its elements, by how far apart they are; a triple needs III.
DUAL_LEVEL = {1: 2, 2: 3, 3: 4}
TRIPLE_LEVEL = 3
# Where the nodes of a block stand around the middle of the gap between two columns on the level
# III line: three above the line, then two or three below it.
BLOCK_GAP_X = 90
# The dual of the first and last element of the row stands this far right of the last column.
WRAP_DUAL_OFFSET = 150
BLOCK_GAP_Y = 45

MIN_NODE_GAP = 70
MIN_LINK_CLEARANCE = 28


@dataclass
class Mod:
    stat: str
    kind: int
    value: float
    tags: list[str] = field(default_factory=list)


@dataclass
class Node:
    id: str
    name: str
    kind: int
    region: str
    cost: int
    pos: tuple[int, int]
    links: list[str] = field(default_factory=list)
    mods: list[Mod] = field(default_factory=list)
    desc: str = ""
    icon: str = ""
    excludes: list[str] = field(default_factory=list)
    unlocks_towers: list[str] = field(default_factory=list)
    group: str = ""
    limit: int = 1
    requires: list[str] = field(default_factory=list)


NODES: dict[str, Node] = {}


def column_x(e: str) -> int:
    return round((ELEMENTS.index(e) - (len(ELEMENTS) - 1) / 2) * COLUMN_WIDTH)


def level_y(level: int) -> int:
    """Height of level 1..LEVEL_COUNT."""
    return FIRST_LEVEL_Y - (level - 1) * LEVEL_STEP


def level_id(e: str, level: int) -> str:
    return LEVEL_IDS[level - 1] % e


def add(node: Node) -> Node:
    assert node.id not in NODES, "duplicate id %s" % node.id
    NODES[node.id] = node
    return node


def link(a: str, b: str) -> None:
    if b not in NODES[a].links and a not in NODES[b].links:
        NODES[a].links.append(b)


# --- Modifier shorthands -------------------------------------------------------------------------

def inc(stat: str, pct: float, *tags: str) -> Mod:
    return Mod(stat, INC, pct / 100.0, list(tags))


def more(stat: str, pct: float, *tags: str) -> Mod:
    return Mod(stat, MORE, pct / 100.0, list(tags))


def flat(stat: str, value: float, *tags: str) -> Mod:
    return Mod(stat, FLAT, value, list(tags))


# --- Descriptions --------------------------------------------------------------------------------
# Built from the modifiers so the text always matches the numbers.

STATUS = {"burn": ("Burns", True), "poison": ("Poison", False), "slow": ("Slows", True), "curse": ("Curses", True),
          "stun": ("Stuns", True), "shatter": ("Shatter", False)}


def _subject(tags: list[str]) -> str:
    if not tags:
        return "All towers"
    if tags[0] == "skill":
        return "Skills" if len(tags) == 1 else "The %s skill" % SKILLS[tags[1]]
    if len(tags) == 2 and tags[1] == "hybrid":
        return "Dual and triple towers with %s in them" % NAMES[tags[0]]
    if len(tags) == 2 and all(t in NAMES for t in tags):
        return "Towers that are both %s and %s" % (NAMES[tags[0]], NAMES[tags[1]])
    return " ".join(NAMES.get(t, t.capitalize()) for t in tags) + " towers"


def _from(tags: list[str]) -> str:
    if not tags:
        return ""
    s = _subject(tags)
    return " from " + s[0].lower() + s[1:]


def _pct(value: float) -> str:
    p = abs(value) * 100.0
    return ("%d" % round(p)) if abs(p - round(p)) < 0.01 else ("%.1f" % p)


def _num(value: float) -> str:
    v = abs(value)
    return ("%d" % round(v)) if abs(v - round(v)) < 0.01 else ("%.1f" % v)


def _plural(value: float, one: str, many: str) -> str:
    return one if abs(abs(value) - 1.0) < 0.01 else many


def sentence(m: Mod) -> str:
    s, v, up = m.stat, m.value, m.value >= 0
    subj = _subject(m.tags)
    pct = _pct(v)
    word = "more" if up else "less"
    if s == "damage":
        return f"{subj} deal {pct}% {word} damage."
    if s == "attacks_per_second":
        return f"{subj} attack {pct}% {'faster' if up else 'slower'}."
    if s == "attack_range":
        return f"{subj} have {pct}% {word} range."
    if s == "projectile_speed":
        return f"{subj} fire {pct}% faster shots."
    if s == "splash_radius":
        if m.kind == FLAT:
            return f"{subj} crush every enemy within {_num(v)} of the target."
        return f"{subj} hit {pct}% {'wider' if up else 'narrower'} areas."
    if s == "cost":
        return f"{subj} cost {pct}% {word} gold."
    if s == "chain_count":
        return f"{subj} chain to {_num(v)} {'more' if up else 'fewer'} {_plural(v, 'enemy', 'enemies')}."
    if s == "chain_range":
        return f"Chains{_from(m.tags)} jump {pct}% farther."
    if s == "chain_falloff":
        return f"Chains{_from(m.tags)} lose {pct}% {word} damage as they jump."
    if s == "knockback":
        return f"{subj} push enemies back {pct}% farther."
    if s == "armour_ignore":
        return f"{subj} ignore {pct}% of enemy armour."
    if s == "bounty_bonus":
        who = (" by " + subj[0].lower() + subj[1:]) if m.tags else ""
        return f"Kills{who} earn {_num(v)} extra {_plural(v, 'gold', 'gold')}."
    if s == "aura_damage":
        return f"Auras{_from(m.tags)} grant {pct}% more increased damage."
    if s == "aura_radius":
        return f"Auras{_from(m.tags)} reach {pct}% farther."
    if s == "burn_spread_radius":
        if m.kind == FLAT:
            return f"Burning enemies spread their burn to enemies within {_num(v)} when they die."
        return f"Burns{_from(m.tags)} spread {pct}% farther."
    if s == "poison_spread_count":
        return (f"When a poisoned enemy dies, its poison spreads to {_num(v)} more nearby "
                f"{_plural(v, 'enemy', 'enemies')}.")
    if s == "skill_damage":
        return f"{subj} deals {pct}% {word} damage." if m.tags[1:] else f"{subj} deal {pct}% {word} damage."
    if s == "skill_cooldown":
        return f"{subj} recharges {pct}% {'slower' if up else 'faster'}." if m.tags[1:] else \
            f"{subj} recharge {pct}% {'slower' if up else 'faster'}."
    for status, (noun, plural) in STATUS.items():
        if s.startswith(status + "_"):
            part = s[len(status) + 1:]
            verbs = {"damage": ("deal", "deals"), "duration": ("last", "lasts"), "strength": ("are", "is"),
                     "stacks": ("stack", "stacks")}[part]
            verb = verbs[0] if plural else verbs[1]
            if part == "damage":
                return f"{noun}{_from(m.tags)} {verb} {pct}% {word} damage."
            if part == "duration":
                if m.kind == FLAT:
                    return f"{noun}{_from(m.tags)} {verb} {_num(v) if v >= 1 else '%.1f' % v} " \
                           f"{_plural(v, 'second', 'seconds')} {'longer' if up else 'shorter'}."
                return f"{noun}{_from(m.tags)} {verb} {pct}% {'longer' if up else 'shorter'}."
            if part == "strength":
                return f"{noun}{_from(m.tags)} {verb} {pct}% {'stronger' if up else 'weaker'}."
            if part == "stacks":
                return f"{noun}{_from(m.tags)} {verb} {_num(v)} more {_plural(v, 'time', 'times')}."
    raise ValueError("no description for stat %s" % s)


def describe(node: Node) -> str:
    parts = [sentence(m) for m in node.mods]
    if node.desc:
        parts.insert(0, node.desc)
    return " ".join(parts)



# --- What each element's tree holds ---------------------------------------------------------------
# LEVELS: what levels II to VI give besides the towers they open (level I gives the element's tower
# and skill). BRANCHES: the five rows of options between the levels, each option (name, modifiers).
# The first option of every branch is the plain one: a click on a far level takes it on the way
# (TreeState.path_to), and so does the test bot.

ENTRY_NAMES = {"fire": "Kindle", "storm": "Static", "nature": "Seedling", "water": "Spring", "earth": "Bedrock",
               "void": "Whisper"}
BASE_TOWERS = {"fire": "fire_brazier", "storm": "storm_spire", "nature": "nature_thornbush",
               "water": "water_wellspring", "earth": "earth_monolith", "void": "void_obelisk"}

LEVELS = {
    "fire": [[inc("damage", 5, "fire")], [inc("damage", 8, "fire")], [flat("burn_spread_radius", 50, "fire")],
             [inc("attacks_per_second", 6, "fire")], [inc("damage", 10, "fire"), inc("attack_range", 5, "fire")]],
    "storm": [[inc("attacks_per_second", 4, "storm")], [inc("attacks_per_second", 6, "storm")],
              [more("chain_falloff", -50, "storm")], [inc("damage", 6, "storm")],
              [inc("attacks_per_second", 8, "storm"), inc("chain_range", 10, "storm")]],
    "nature": [[inc("poison_damage", 6, "nature")], [inc("poison_damage", 8, "nature")],
               [flat("poison_spread_count", 1, "nature")], [inc("attack_range", 5, "nature")],
               [inc("poison_damage", 12, "nature"), inc("attacks_per_second", 5, "nature")]],
    "water": [[inc("damage", 5, "water")], [inc("damage", 8, "water")], [inc("slow_strength", 15, "water")],
              [inc("slow_duration", 10, "water")], [inc("damage", 10, "water"), inc("knockback", 10, "water")]],
    "earth": [[inc("damage", 5, "earth")], [inc("shatter_strength", 15, "earth")], [flat("splash_radius", 25, "earth")],
              [inc("stun_duration", 10, "earth")], [inc("damage", 12, "earth"), inc("splash_radius", 8, "earth")]],
    "void": [[inc("attacks_per_second", 4, "void")], [inc("attacks_per_second", 6, "void")],
             [flat("aura_damage", 0.05, "void")], [inc("curse_strength", 8, "void")],
             [inc("attacks_per_second", 8, "void"), inc("aura_radius", 10, "void")]],
}


def bond(e: str) -> list[Mod]:
    return [inc("damage", 10, e, "hybrid")]


def rite(e: str) -> list[Mod]:
    return [inc("skill_cooldown", -10, "skill", e)]


def lore(e: str) -> list[Mod]:
    return [inc("skill_damage", 20, "skill", e)]


BRANCHES = {
    "fire": [
        [("Stoked Coals", [inc("damage", 4, "fire")]), ("Heat Haze", [inc("attack_range", 5, "fire")]),
         ("Lingering Flame", [inc("burn_duration", 10, "fire")])],
        [("Bellows", [inc("attacks_per_second", 5, "fire")]), ("Searing Heat", [inc("burn_damage", 10, "fire")]),
         ("Long Flames", [inc("attack_range", 4, "fire"), inc("projectile_speed", 15, "fire")]),
         ("Cheap Coal", [inc("cost", -4, "fire")])],
        [("Blaze", [inc("damage", 8, "fire")]),
         ("Searing Brand", [inc("burn_duration", 12, "fire"), inc("burn_damage", 10, "fire")]),
         ("Starfall", lore("fire"))],
        [("Wildfire Pace", [inc("attacks_per_second", 6, "fire")]), ("Wildfire", [flat("burn_stacks", 1, "fire")]),
         ("Meteor Rite", rite("fire")), ("Forge Bond", bond("fire"))],
        [("Pyre Lord", [inc("damage", 8, "fire"), inc("splash_radius", 10, "fire")]),
         ("Ashen Ground", [inc("burn_damage", 15, "fire"), inc("burn_duration", 15, "fire")]),
         ("Firestorm", [inc("attacks_per_second", 8, "fire"), inc("attack_range", 4, "fire")])],
    ],
    "storm": [
        [("Charged Air", [inc("damage", 4, "storm")]), ("Thunderhead", [inc("attack_range", 5, "storm")]),
         ("Long Arc", [inc("chain_range", 10, "storm")])],
        [("Charge", [inc("attacks_per_second", 5, "storm")]), ("Live Wire", [inc("chain_range", 10, "storm")]),
         ("Grounded Path", [inc("chain_falloff", -10, "storm")]), ("Cheap Copper", [inc("cost", -4, "storm")])],
        [("Static Charge", [inc("damage", 6, "storm"), inc("attacks_per_second", 3, "storm")]),
         ("Forked Path", [inc("chain_range", 15, "storm")]), ("Overload", lore("storm"))],
        [("Strike", [inc("damage", 6, "storm")]), ("Branching Bolts", [flat("chain_count", 1, "storm")]),
         ("Surge Rite", rite("storm")), ("Storm Bond", bond("storm"))],
        [("Sky Hammer", [inc("damage", 8, "storm"), inc("attack_range", 5, "storm")]),
         ("Arc Lattice", [inc("chain_range", 20, "storm"), inc("chain_falloff", -15, "storm")]),
         ("Tempest", [inc("attacks_per_second", 8, "storm"), inc("projectile_speed", 15, "storm")])],
    ],
    "nature": [
        [("Quick Thorns", [inc("attacks_per_second", 4, "nature")]), ("Tall Canopy", [inc("attack_range", 5, "nature")]),
         ("Slow Rot", [inc("poison_duration", 10, "nature")])],
        [("Venom", [inc("poison_damage", 8, "nature")]), ("Thorn", [inc("damage", 6, "nature")]),
         ("Cheap Seed", [inc("cost", -4, "nature")]), ("Bounty of the Wild", [flat("bounty_bonus", 1, "nature")])],
        [("Deep Roots", [inc("attack_range", 5, "nature"), inc("attacks_per_second", 3, "nature")]),
         ("Thorn Wall", [inc("poison_duration", 15, "nature"), inc("cost", -4, "nature")]),
         ("Strangling Vines", lore("nature"))],
        [("Wild Growth", [inc("attacks_per_second", 6, "nature")]), ("Festering", [flat("poison_stacks", 1, "nature")]),
         ("Entangle Rite", rite("nature")), ("Wild Bond", bond("nature"))],
        [("Plague Garden", [inc("poison_damage", 15, "nature")]),
         ("Old Growth", [inc("attack_range", 6, "nature"), inc("poison_duration", 15, "nature")]),
         ("Briar Heart", [inc("damage", 8, "nature"), inc("attacks_per_second", 4, "nature")])],
    ],
    "water": [
        [("Pressure", [inc("damage", 4, "water")]), ("Wide Basin", [inc("attack_range", 5, "water")]),
         ("Cold Snap", [inc("slow_duration", 10, "water")])],
        [("Rapids", [inc("attacks_per_second", 5, "water")]), ("Undertow", [inc("knockback", 10, "water")]),
         ("Rime", [inc("slow_strength", 6, "water")]), ("Free Flow", [inc("cost", -4, "water")])],
        [("Riptide", [inc("knockback", 15, "water"), inc("damage", 4, "water")]),
         ("Hoarfrost", [inc("slow_duration", 15, "water")]), ("Rogue Wave", lore("water"))],
        [("Torrent", [inc("damage", 6, "water")]),
         ("Black Ice", [inc("slow_strength", 10, "water"), inc("slow_duration", 10, "water")]),
         ("Tidal Rite", rite("water")), ("Tide Bond", bond("water"))],
        [("Permafrost", [inc("slow_duration", 20, "water"), inc("damage", 5, "water")]),
         ("Maelstrom", [inc("knockback", 20, "water"), inc("attacks_per_second", 4, "water")]),
         ("Deep Current", [inc("damage", 8, "water"), inc("attack_range", 5, "water")])],
    ],
    "earth": [
        [("Stonework", [inc("damage", 4, "earth")]), ("Rolling Stone", [inc("attacks_per_second", 4, "earth")]),
         ("Tremor", [inc("stun_duration", 10, "earth")])],
        [("Granite", [inc("damage", 6, "earth")]), ("Crumble", [inc("shatter_strength", 10, "earth")]),
         ("Landslide", [inc("attacks_per_second", 5, "earth")]), ("Quarry", [inc("cost", -4, "earth")])],
        [("Mountain's Weight", [inc("damage", 8, "earth")]), ("Aftershock", [inc("stun_duration", 15, "earth")]),
         ("Tectonic Fury", lore("earth"))],
        [("Boulder", [inc("damage", 6, "earth")]), ("Sundering", [inc("shatter_strength", 20, "earth")]),
         ("Earthquake Rite", rite("earth")), ("Stone Bond", bond("earth"))],
        [("Titan's Fist", [inc("damage", 10, "earth"), inc("splash_radius", 10, "earth")]),
         ("Seismic Lock", [inc("stun_duration", 20, "earth"), inc("attacks_per_second", 3, "earth")]),
         ("High Ground", [inc("attack_range", 6, "earth"), inc("damage", 5, "earth")])],
    ],
    "void": [
        [("Null Edge", [inc("damage", 4, "void")]), ("Wide Shadow", [inc("aura_radius", 10, "void")]),
         ("Hex", [inc("curse_strength", 8, "void")])],
        [("Pulse", [inc("attacks_per_second", 5, "void")]), ("Long Night", [inc("curse_duration", 10, "void")]),
         ("Withering", [inc("curse_strength", 8, "void")]), ("Hollow Coin", [inc("cost", -4, "void")])],
        [("Malediction", [inc("curse_strength", 15, "void")]), ("Eclipse", [inc("aura_radius", 15, "void")]),
         ("Final Hour", lore("void"))],
        [("Flicker", [inc("attacks_per_second", 6, "void")]),
         ("Creeping Doom", [inc("curse_duration", 15, "void"), inc("curse_strength", 8, "void")]),
         ("Doom Rite", rite("void")), ("Void Bond", bond("void"))],
        [("Unmaking", [inc("curse_strength", 20, "void"), inc("attacks_per_second", 3, "void")]),
         ("Black Sun", [inc("aura_radius", 20, "void"), inc("damage", 4, "void")]),
         ("Oblivion", [inc("damage", 10, "void"), inc("attack_range", 4, "void")])],
    ],
}

# Keystones above level VI: (left, right), each (id, name, modifiers, icon). The first three ids are
# the old keystones, still unlocked by the Talents tree.
KEYSTONES = {
    "fire": (("keystone_focus", "Focus", [more("damage", 40), more("attacks_per_second", -25)], "eye"),
             ("keystone_cinderheart", "Cinderheart",
              [more("burn_damage", 50, "fire"), more("damage", -20, "fire")], "flame")),
    "storm": (("keystone_overcharge", "Overcharge", [more("attacks_per_second", 30), more("cost", 20)], "bolt"),
              ("keystone_eye_of_the_storm", "Eye of the Storm",
               [flat("chain_count", 2, "storm"), more("damage", -25, "storm")], "bolt")),
    "nature": (("keystone_overgrowth", "Overgrowth",
                [more("attacks_per_second", 30, "nature"), more("attack_range", -15)], "bubbles"),
               ("keystone_hoard", "Hoard", [flat("bounty_bonus", 1), more("cost", 15)], "coin")),
    "water": (("keystone_undertow", "Undertow", [more("knockback", 50, "water"), more("damage", -20, "water")], "push"),
              ("keystone_deep_freeze", "Deep Freeze",
               [more("slow_strength", 30, "water"), more("slow_duration", -30, "water")], "snowflake")),
    "earth": (("keystone_juggernaut", "Unstoppable",
               [more("damage", 40, "earth"), more("attacks_per_second", -20, "earth")], "hammer"),
              ("keystone_bedrock", "Living Rock", [more("stun_duration", 50, "earth"), more("cost", 15, "earth")], "shield")),
    "void": (("keystone_event_horizon", "Event Horizon",
              [more("aura_radius", 40, "void"), more("damage", -30, "void")], "aura"),
             ("keystone_hollow_pact", "Hollow Pact", [more("curse_strength", 50, "void"), more("cost", 10)], "spiral")),
}


# --- The towers each level opens, read from data/towers ---------------------------------------

def read_towers() -> list[tuple[str, str, list[str], list[str]]]:
    """(id, display name, elements, requires_nodes) of every tower."""
    towers = []
    for name in sorted(os.listdir(TOWER_DIR)):
        if not name.endswith(".tres"):
            continue
        text = open(os.path.join(TOWER_DIR, name)).read().split("[resource]")[1]

        def value(key: str) -> str:
            match = re.search(r'^%s = (.*)$' % key, text, re.M)
            return match.group(1) if match else ""
        towers.append((re.findall(r'&"(\w+)"', value("id"))[0], value("display_name").strip('"'),
                       re.findall(r'&"(\w+)"', value("elements")), re.findall(r'&"(\w+)"', value("requires_nodes"))))
    return towers


def apart(a: str, b: str) -> int:
    """Steps between two elements on the ring: 1 neighbours, 2 two apart, 3 opposite."""
    i, j = ELEMENTS.index(a), ELEMENTS.index(b)
    return min((i - j) % len(ELEMENTS), (j - i) % len(ELEMENTS))


def combo_needs(elements: list[str]) -> list[str]:
    """The level nodes a dual or triple tower's node requires."""
    level = TRIPLE_LEVEL if len(elements) == 3 else DUAL_LEVEL[apart(*elements)]
    return [level_id(e, level) for e in elements]


def level_of(node_id: str) -> tuple[str, int]:
    """(element, level) of a level node's id."""
    for e in ELEMENTS:
        for level in range(1, LEVEL_COUNT + 1):
            if level_id(e, level) == node_id:
                return e, level
    raise ValueError("%s is not a level of an element" % node_id)


def level_name(node_id: str) -> str:
    e, level = level_of(node_id)
    return "%s %s" % (NAMES[e], ROMAN[level - 1])


def _and(words: list[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def opens_text(e: str, level: int, towers: list) -> str:
    """What a level opens, and which combination nodes need it."""
    me = level_id(e, level)
    alone, duals, triples = [], [], 0
    for _id, name, elements, needs in towers:
        if len(elements) > 1:
            needs = combo_needs(elements)
            if me not in needs:
                continue
            if len(elements) == 2:
                duals.append("%s (with %s)" % (name, level_name([n for n in needs if n != me][0])))
            else:
                triples += 1
        elif me in needs:
            alone.append(name)
    parts = []
    if alone:
        parts.append("Opens the %s tower." % " and the ".join(alone))
    if duals:
        parts.append("Needed for the dual towers %s." % _and(duals))
    if triples:
        parts.append("Needed for every triple tower with %s in it." % NAMES[e])
    return " ".join(parts)


# --- Building the tree ----------------------------------------------------------------------------

def build() -> None:
    NODES.clear()
    add(Node("start", "Origin", START, "", 0, (0, 0),
             desc="Every run starts here. Each element climbs its own path from level I to level VI."))
    towers = read_towers()
    for e in ELEMENTS:
        build_column(e, towers)
    build_combinations(towers)


def gap_x(gap: float) -> int:
    """The middle of the gap after column `gap` (0 to 4 between columns, 5 right of the last)."""
    return round(column_x(ELEMENTS[0]) + (gap + 0.5) * COLUMN_WIDTH)


def build_combinations(towers: list) -> None:
    """One node for every dual and triple tower, where the levels it needs are."""
    combos = [(id, name, elements) for id, name, elements, _needs in towers if len(elements) > 1]

    def combo(id: str, name: str, elements: list[str], pos: tuple[int, int]) -> None:
        needs = combo_needs(elements)
        cost = TRIPLE_COST if len(elements) == 3 else DUAL_COST[apart(*elements)]
        add(Node("tower_" + id, name, BRIDGE, "", cost, pos, requires=needs, unlocks_towers=[id],
                 desc="Unlocks the %s tower (%s). Needs %s." % (
                     name, " + ".join(NAMES[e] for e in elements), _and([level_name(n) for n in needs]))))

    def middle(elements: list[str]) -> float:
        return sum(ELEMENTS.index(e) for e in elements) / len(elements)

    block = []
    for id, name, elements in combos:
        if len(elements) == 2 and apart(*elements) == 1:
            # Neighbours: on the level II line between their columns. Void and Fire are the two ends
            # of the row, so theirs stands right of the last column.
            first = min(ELEMENTS.index(e) for e in elements)
            wraps = sorted(ELEMENTS.index(e) for e in elements) == [0, len(ELEMENTS) - 1]
            x = column_x(ELEMENTS[-1]) + WRAP_DUAL_OFFSET if wraps else gap_x(first)
            combo(id, name, elements, (x, level_y(2)))
        elif len(elements) == 2 and apart(*elements) == 3:
            # Opposites: on the level IV line, halfway between their columns.
            combo(id, name, elements, (gap_x(middle(elements) - 0.5), level_y(4)))
        else:
            block.append((middle(elements), len(elements), name, id, elements))
    # Level III: the duals of elements two apart and the triples, left to right by where their
    # elements are, dealt into one block per gap between columns (duals first in a block).
    block.sort()
    gaps = len(ELEMENTS) - 1
    start = 0
    for gap in range(gaps):
        size = len(block) // gaps + (1 if gap == gaps // 2 and len(block) % gaps else 0)
        group = sorted(block[start:start + size], key=lambda item: (item[1], item[0], item[2]))
        start += size
        assert len(group) <= 6, "a block holds six nodes"
        top = group[:3]
        bottom = group[3:]
        for row, dy in ((top, -BLOCK_GAP_Y), (bottom, BLOCK_GAP_Y)):
            for i, (_mid, _n, name, id, elements) in enumerate(row):
                dx = (i - (len(row) - 1) / 2) * BLOCK_GAP_X
                combo(id, name, elements, (round(gap_x(gap) + dx), level_y(TRIPLE_LEVEL) + dy))
    assert start == len(block), "every level III combination has a place"


def build_column(e: str, towers: list) -> None:
    x = column_x(e)
    E = NAMES[e]
    for level in range(1, LEVEL_COUNT + 1):
        id = level_id(e, level)
        opens = opens_text(e, level, towers)
        if level == 1:
            add(Node(id, "%s I" % E, ENTRY, e, LEVEL_COST[0], (x, level_y(1)), links=["start"],
                     desc=("%s. Opens the %s tower and the %s skill. %s" % (
                         ENTRY_NAMES[e], dict((t[0], t[1]) for t in towers)[BASE_TOWERS[e]], SKILLS[e], opens)).strip(),
                     unlocks_towers=[BASE_TOWERS[e]]))
        else:
            add(Node(id, "%s %s" % (E, ROMAN[level - 1]), NOTABLE, e, LEVEL_COST[level - 1], (x, level_y(level)),
                     mods=list(LEVELS[e][level - 2]),
                     desc=("%s level %s. Needs one pick from the branch below it. %s" % (E, ROMAN[level - 1], opens)).strip()))
    # The branches: every option joins the level below it and the level above it.
    for row, options in enumerate(BRANCHES[e], start=1):
        y = level_y(row) - LEVEL_STEP // 2
        limit = 2 if len(options) == 4 else 1
        rule = "Pick one of these three." if limit == 1 else "Pick up to two of these four."
        for i, (name, mods) in enumerate(options):
            # The first (plain) option sits in the middle of the row, the others around it.
            slot = [0, -1, 1] if len(options) == 3 else [-0.5, -1.5, 0.5, 1.5]
            add(Node("%s_b%d_%s" % (e, row, "abcd"[i]), name, MINOR, e, BRANCH_COST[row - 1],
                     (round(x + slot[i] * OPTION_GAP), y), links=[level_id(e, row), level_id(e, row + 1)],
                     mods=list(mods), desc=rule, group="%s_b%d" % (e, row), limit=limit))
    # Keystones above the last level: a pick-one pair.
    left, right = KEYSTONES[e]
    made = []
    for (id, name, mods, icon), side in ((left, -1), (right, 1)):
        made.append(add(Node(id, name, KEYSTONE, "", KEYSTONE_COST,
                             (x + side * KEYSTONE_SPREAD, level_y(LEVEL_COUNT) - KEYSTONE_RISE),
                             links=[level_id(e, LEVEL_COUNT)], mods=list(mods), icon=icon)))
    made[0].excludes.append(made[1].id)
    made[0].desc = "Pick one: closes %s." % made[1].name
    made[1].desc = "Pick one: closes %s." % made[0].name


# --- Checks ------------------------------------------------------------------------------------

def _seg_point_distance(a, b, p) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    length = dx * dx + dy * dy
    t = 0.0 if length == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length))
    return math.dist((ax + t * dx, ay + t * dy), (px, py))


def check() -> list[str]:
    problems = []
    ids = set(NODES)
    for n in NODES.values():
        for other in n.links + n.excludes + n.requires:
            if other not in ids:
                problems.append("%s: unknown id %s" % (n.id, other))
        if n.requires and n.links:
            problems.append("%s: a combination node hangs on its requirements, not on links" % n.id)
        if n.kind != START and not n.mods and not n.unlocks_towers:
            problems.append("%s: does nothing" % n.id)
        if not n.region and n.kind in (MINOR, NOTABLE, ENTRY):
            problems.append("%s: needs a region" % n.id)
    nodes = list(NODES.values())
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            d = math.dist(a.pos, b.pos)
            if d < MIN_NODE_GAP:
                problems.append("%s and %s are only %.0f apart" % (a.id, b.id, d))
    pairs = {tuple(sorted((n.id, l))) for n in nodes for l in n.links if l in ids}
    for x, y in pairs:
        for n in nodes:
            if n.id in (x, y):
                continue
            d = _seg_point_distance(NODES[x].pos, NODES[y].pos, n.pos)
            if d < MIN_LINK_CLEARANCE:
                problems.append("link %s-%s runs %.0f from %s" % (x, y, d, n.id))
    # A node with no region (bridge or keystone) may only touch element nodes, so a stage that
    # closes an element also closes it (MetaProgress.closed_nodes).
    for x, y in pairs:
        if not NODES[x].region and not NODES[y].region and START not in (NODES[x].kind, NODES[y].kind):
            problems.append("link %s-%s joins two nodes without a region" % (x, y))
    adj = {n.id: set() for n in nodes}
    for x, y in pairs:
        adj[x].add(y)
        adj[y].add(x)
    seen = {"start"}
    todo = ["start"]
    while todo:
        for nxt in adj[todo.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    for n in nodes:
        if n.requires and all(r in seen for r in n.requires):
            continue
        if n.id not in seen:
            problems.append("%s: cannot be reached" % n.id)
    combos = sorted(n.unlocks_towers[0] for n in nodes if n.requires)
    wanted = sorted(id for id, _name, elements, _needs in read_towers() if len(elements) > 1)
    if combos != wanted:
        problems.append("combination nodes and dual/triple towers differ: %s" % sorted(set(combos) ^ set(wanted)))
    for n in nodes:
        try:
            describe(n)
        except (ValueError, KeyError) as error:
            problems.append("%s: %s" % (n.id, error))
    return problems


def path_cost(target: str) -> int:
    """Cheapest number of points from the Origin to a node, counting the node itself."""
    best = {"start": 0}
    adj: dict[str, set[str]] = {n: set() for n in NODES}
    for n in NODES.values():
        for l in n.links:
            adj[n.id].add(l)
            adj[l].add(n.id)
    todo = [(0, "start")]
    import heapq
    while todo:
        cost, node = heapq.heappop(todo)
        if node == target:
            return cost
        if cost > best.get(node, 1 << 30):
            continue
        for nxt in adj[node]:
            c = cost + NODES[nxt].cost
            if c < best.get(nxt, 1 << 30):
                best[nxt] = c
                heapq.heappush(todo, (c, nxt))
    return -1


# --- Writing -----------------------------------------------------------------------------------

def _names(ids: list[str]) -> str:
    return "Array[StringName]([%s])" % ", ".join('&"%s"' % i for i in ids)


def _value(v: float) -> str:
    if abs(v - round(v)) < 1e-9:
        return "%.1f" % v
    return repr(round(v, 6))


def tres(n: Node) -> str:
    out = ['[gd_resource type="Resource" script_class="TreeNodeData" format=3]', ""]
    if n.mods:
        out.append('[ext_resource type="Script" path="res://scripts/data/modifier.gd" id="1_mod"]')
    out.append('[ext_resource type="Script" path="res://scripts/data/tree_node_data.gd" id="2_node"]')
    out.append("")
    for i, m in enumerate(n.mods):
        out += ['[sub_resource type="Resource" id="Resource_m%d"]' % i, 'script = ExtResource("1_mod")',
                'stat = &"%s"' % m.stat, "kind = %d" % m.kind, "value = %s" % _value(m.value)]
        if m.tags:
            out.append("required_tags = %s" % _names(m.tags))
        out.append("")
    out += ["[resource]", 'script = ExtResource("2_node")', 'id = &"%s"' % n.id,
            'display_name = "%s"' % n.name, 'description = "%s"' % describe(n).replace('"', '\\"'),
            "kind = %d" % n.kind]
    if n.region:
        out.append('region = &"%s"' % n.region)
    out.append("cost = %d" % n.cost)
    out.append("position = Vector2(%d, %d)" % n.pos)
    if n.links:
        out.append("links = %s" % _names(n.links))
    if n.requires:
        out.append("requires = %s" % _names(n.requires))
    if n.excludes:
        out.append("excludes = %s" % _names(n.excludes))
    if n.group:
        out.append('choice_group = &"%s"' % n.group)
        out.append("choice_limit = %d" % n.limit)
    if n.mods:
        out.append('modifiers = Array[ExtResource("1_mod")]([%s])'
                   % ", ".join('SubResource("Resource_m%d")' % i for i in range(len(n.mods))))
    if n.unlocks_towers:
        out.append("unlocks_towers = %s" % _names(n.unlocks_towers))
    if n.icon:
        out.append('icon = &"%s"' % n.icon)
    return "\n".join(out) + "\n"


def preview(path: str) -> None:
    from PIL import Image, ImageDraw
    width, height = 3000, 2000
    img = Image.new("RGB", (width, height), (10, 12, 20))
    d = ImageDraw.Draw(img)
    cx, cy = width / 2, height - 80
    colors = {"fire": (228, 87, 46), "storm": (242, 193, 78), "nature": (91, 180, 80), "water": (46, 134, 222),
              "earth": (160, 120, 90), "void": (142, 92, 217), "": (255, 255, 255)}
    for level in range(1, LEVEL_COUNT + 1):
        y = cy + level_y(level)
        d.line((40, y, width - 40, y), fill=(30, 34, 50), width=1)
        d.text((44, y - 14), "Level %s" % ROMAN[level - 1], fill=(120, 130, 160))
    for n in NODES.values():
        for l in n.links:
            a, b = n.pos, NODES[l].pos
            d.line((cx + a[0], cy + a[1], cx + b[0], cy + b[1]), fill=(70, 76, 100), width=3)
        for x in n.excludes:
            a, b = n.pos, NODES[x].pos
            d.line((cx + a[0], cy + a[1], cx + b[0], cy + b[1]), fill=(160, 40, 40), width=1)
        for x in n.requires:
            a, b = n.pos, NODES[x].pos
            d.line((cx + a[0], cy + a[1], cx + b[0], cy + b[1]), fill=(40, 60, 60), width=1)
    radius = {START: 30, ENTRY: 26, MINOR: 15, NOTABLE: 26, BRIDGE: 20, KEYSTONE: 28}
    for n in NODES.values():
        r = radius[n.kind]
        x, y = cx + n.pos[0], cy + n.pos[1]
        d.ellipse((x - r, y - r, x + r, y + r), fill=colors[n.region],
                  outline=(255, 255, 255) if n.kind in (KEYSTONE, NOTABLE, ENTRY) else None, width=3)
        d.text((x - r, y + r + 2), "%s (%d)" % (n.name, n.cost), fill=(200, 200, 200))
    img.save(path)


def main() -> None:
    build()
    problems = check()
    if problems:
        print("\n".join(problems))
        sys.exit(1)
    os.makedirs(OUT_DIR, exist_ok=True)
    written = set()
    for n in NODES.values():
        name = n.id + ".tres"
        with open(os.path.join(OUT_DIR, name), "w") as f:
            f.write(tres(n))
        written.add(name)
    for name in os.listdir(OUT_DIR):
        if name.endswith(".tres") and name not in written:
            os.remove(os.path.join(OUT_DIR, name))
            uid = os.path.join(OUT_DIR, name + ".uid")
            if os.path.exists(uid):
                os.remove(uid)
    total = sum(n.cost for n in NODES.values())
    print("%d nodes, %d points for every node" % (len(NODES), total))
    for target in ("fire_level2", "fire_core", "fire_notable", "fire_level6", "keystone_focus"):
        print("  %s: %d points from the Origin" % (target, path_cost(target)))
    print("  %d combination nodes (dual and triple towers)" % sum(1 for n in NODES.values() if n.requires))
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])


if __name__ == "__main__":
    main()
