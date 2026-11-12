#!/usr/bin/env python3
"""Writes the meta tree (the Talents screen) to data/trees/meta/*.tres.

Edit the tables in this file and rerun; do not edit the .tres files by hand. The script deletes
the meta tree files it no longer writes, checks the layout (no two nodes too close, no link running
through a node) and prints what the whole tree costs.

    python3 tools/meta/gen_meta_tree.py            # write the tree
    python3 tools/meta/gen_meta_tree.py --preview out.png   # also draw a quick layout picture

The tree is a wheel, read from the middle out:
  * Origin in the centre.
  * Four inner wings, one per quadrant: Arsenal (north, tower power and the skill web keystones),
    Command (east, gold and lives), Expeditions (south, maps, difficulty levels and skill points)
    and Mastery (west, player skills and range). Each wing forks three ways and ends in a pick-one
    choice between two keystones.
  * The Starpath, a ring road of small travel nodes that joins the wings to each other and to the
    six gates of the outer ring.
  * Six element constellations on the outer ring, in the element ring's order. Each has a status
    arm, a speed and cost arm, a pick-one choice and a keystone with a real downside at its tip.
  * Six confluence bridges between neighbouring constellations, which boost the dual towers that
    carry both elements.

Pacing: a clean first pass through the campaign pays roughly 550 meta points; the tree costs about
750 to fill, so it keeps growing through the whole campaign and the last nodes come from replays
on Hard or Nightmare and from skirmish runs.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data", "trees", "meta")

# TreeNodeData.Kind
START, ENTRY, MINOR, NOTABLE, BRIDGE, KEYSTONE = range(6)
# Modifier.Kind
FLAT, INC, MORE = range(3)

# Element ring order (data/elements/*.tres ring_index) and the outer-ring angle of each
# constellation, in degrees clockwise from east (screen y points down).
ELEMENTS = ["fire", "storm", "nature", "water", "earth", "void"]
ELEMENT_NAMES = {"fire": "Fire", "storm": "Storm", "nature": "Nature", "water": "Water", "earth": "Earth",
                 "void": "Void"}
ELEMENT_ANGLE = {"fire": -60, "storm": 0, "nature": 60, "water": 120, "earth": 180, "void": 240}

# Wing centre angles.
WING_ANGLE = {"arsenal": -90, "command": 0, "expeditions": 90, "mastery": 180}

RING_RADIUS = 560
RING_STEP = 15  # degrees between Starpath nodes

# Smallest allowed distance between two node centres, and between a link and a node it does not
# touch, in tree units (pixels at the default zoom).
MIN_NODE_GAP = 74
MIN_LINK_CLEARANCE = 30


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
    pos: tuple[float, float]
    links: list[str] = field(default_factory=list)
    mods: list[Mod] = field(default_factory=list)
    desc: str = ""
    icon: str = ""
    excludes: list[str] = field(default_factory=list)
    unlocks_nodes: list[str] = field(default_factory=list)
    unlocks_maps: list[str] = field(default_factory=list)
    unlocks_difficulties: list[str] = field(default_factory=list)


NODES: dict[str, Node] = {}


def polar(radius: float, degrees: float) -> tuple[float, float]:
    a = math.radians(degrees)
    return (round(radius * math.cos(a)), round(radius * math.sin(a)))


def add(id: str, name: str, kind: int, region: str, cost: int, pos, links=(), mods=(), **extra) -> Node:
    assert id not in NODES, f"duplicate id {id}"
    node = Node(id, name, kind, region, cost, pos, list(links), list(mods), **extra)
    NODES[id] = node
    return node


def choice(a: Node, b: Node) -> None:
    """Makes two nodes a pick-one choice: taking either closes the other."""
    a.excludes.append(b.id)
    b.excludes.append(a.id)


# --- Descriptions ------------------------------------------------------------------------
# Built from the modifiers so the text always matches the numbers.

TAG_NAMES = {"hybrid": "Dual", "triple": "Triple", "area": "Area"}
TAG_NAMES.update(ELEMENT_NAMES)
STATUS = {  # noun, plural verb form
    "burn": ("Burns", True), "poison": ("Poison", False), "slow": ("Slows", True), "curse": ("Curses", True),
    "stun": ("Stuns", True), "shatter": ("Shatter", False),
}


def _subject(tags: list[str]) -> str:
    if not tags:
        return "Towers"
    if len(tags) == 2 and all(t in ELEMENT_NAMES for t in tags):
        return "Towers that are both %s and %s" % (ELEMENT_NAMES[tags[0]], ELEMENT_NAMES[tags[1]])
    return " ".join(TAG_NAMES[t] for t in tags) + " towers"


def _from(tags: list[str]) -> str:
    return "" if not tags else " from " + _subject(tags)[0].lower() + _subject(tags)[1:]


def _pct(value: float) -> str:
    p = abs(value) * 100.0
    return ("%d" % round(p)) if abs(p - round(p)) < 0.01 else ("%.1f" % p)


def _n(value: float) -> str:
    return "%d" % round(abs(value))


def _plural(value: float, one: str, many: str) -> str:
    return one if round(abs(value)) == 1 else many


def sentence(m: Mod) -> str:
    s, v, up = m.stat, m.value, m.value >= 0
    subj = _subject(m.tags)
    pct = _pct(v)
    if s == "damage":
        return f"{subj} deal {pct}% {'more' if up else 'less'} damage."
    if s == "attacks_per_second":
        return f"{subj} attack {pct}% {'faster' if up else 'slower'}."
    if s == "attack_range":
        return f"{subj} have {pct}% {'more' if up else 'less'} range."
    if s == "projectile_speed":
        return f"{subj} fire {pct}% faster shots."
    if s == "splash_radius":
        return f"{subj} hit {pct}% {'wider' if up else 'narrower'} areas."
    if s == "cost":
        return f"{subj} cost {pct}% {'more' if up else 'less'}."
    if s == "chain_count":
        return f"Chains{_from(m.tags)} jump to {_n(v)} more {_plural(v, 'enemy', 'enemies')}."
    if s == "chain_range":
        return f"Chains{_from(m.tags)} reach {pct}% farther."
    if s == "chain_falloff":
        return f"Chains{_from(m.tags)} lose {pct}% {'more' if up else 'less'} damage per jump."
    if s == "knockback":
        return f"{subj} push enemies back {pct}% farther."
    if s == "armour_ignore":
        return f"{subj} ignore {pct}% of enemy armour."
    if s == "bounty_bonus":
        return f"Kills{(' by ' + subj[0].lower() + subj[1:]) if m.tags else ''} pay {_n(v)} more gold."
    if s == "aura_damage":
        return f"Auras{_from(m.tags)} lend {pct}% {'more' if up else 'less'} damage."
    if s == "aura_radius":
        return f"Auras{_from(m.tags)} reach {pct}% farther."
    if s == "burn_spread_radius":
        return f"Burns{_from(m.tags)} spread {pct}% farther."
    if s == "poison_spread_count":
        return f"Poison{_from(m.tags)} spreads to {_n(v)} more {_plural(v, 'enemy', 'enemies')}."
    for status, (noun, plural) in STATUS.items():
        if s.startswith(status + "_"):
            part = s[len(status) + 1:]
            verb = {"damage": ("deal", "deals"), "duration": ("last", "lasts"), "strength": ("are", "is"),
                    "stacks": ("stack", "stacks")}[part]
            verb = verb[0] if plural else verb[1]
            if part == "damage":
                return f"{noun}{_from(m.tags)} {verb} {pct}% {'more' if up else 'less'} damage."
            if part == "duration":
                return f"{noun}{_from(m.tags)} {verb} {pct}% {'longer' if up else 'shorter'}."
            if part == "strength":
                return f"{noun}{_from(m.tags)} {verb} {pct}% {'stronger' if up else 'weaker'}."
            if part == "stacks":
                return f"{noun}{_from(m.tags)} {verb} {_n(v)} more {_plural(v, 'time', 'times')}."
    if s == "skill_damage":
        who = "Skills" if not m.tags or m.tags == ["skill"] else f"{ELEMENT_NAMES[m.tags[-1]]} skills"
        return f"{who} deal {pct}% {'more' if up else 'less'} damage."
    if s == "skill_cooldown":
        return f"Skills recharge {pct}% {'slower' if up else 'faster'}."
    if s == "starting_gold":
        if m.kind == FLAT:
            return f"Start every run with {_n(v)} more gold."
        return f"Start every run with {pct}% {'more' if up else 'less'} gold."
    if s == "starting_lives":
        if m.kind == FLAT:
            return f"Start every run with {_n(v)} more {_plural(v, 'life', 'lives')}."
        return f"Start every run with {pct}% {'more' if up else 'fewer'} lives."
    if s == "starting_tree_points":
        return f"Start every run with {_n(v)} more skill {_plural(v, 'point', 'points')}."
    if s == "gold_per_wave":
        if m.kind == FLAT:
            return f"Clearing a wave pays {_n(v)} more gold."
        return f"Clearing a wave pays {pct}% {'more' if up else 'less'} gold."
    if s == "sell_refund":
        return f"Selling a tower refunds {pct}% more of its price."
    if s == "tree_points_per_boss":
        return f"Boss waves give {_n(v)} more skill {_plural(v, 'point', 'points')}."
    raise ValueError("no description for stat %s" % s)


def describe(node: Node) -> str:
    parts = [sentence(m) for m in node.mods]
    if node.desc.startswith("Pick one"):
        parts.append(node.desc)
    elif node.desc:
        parts.insert(0, node.desc)
    return " ".join(parts)


# --- Modifier shorthands ------------------------------------------------------------------

# Strength of the bonuses. The tables below are written at full strength; the bot pacing check
# (tools/meta_pacing.gd) showed that made the campaign trivial from the second land on, so combat
# bonuses (POWER) and gold, lives and price cuts (ECON) are halved, rounded to whole numbers.
# Set META_POWER / META_ECON in the environment to try other values.
POWER = float(os.environ.get("META_POWER", "0.5"))
ECONOMY = {"cost", "starting_gold", "gold_per_wave", "sell_refund", "starting_lives", "starting_tree_points",
           "tree_points_per_boss", "bounty_bonus", "skill_cooldown"}


ECON = float(os.environ.get("META_ECON", "0.5"))


def inc(stat: str, pct: float, *tags: str) -> Mod:
    if stat not in ECONOMY and pct > 0:
        pct = max(1, round(pct * POWER))
    if stat == "cost" and pct < 0:
        pct = min(-1, round(pct * ECON))
    return Mod(stat, INC, pct / 100.0, list(tags))


def more(stat: str, pct: float, *tags: str) -> Mod:
    return Mod(stat, MORE, pct / 100.0, list(tags))


# Skill points in a run come three at a time since the skill web grew tenfold (its nodes cost 1 to
# 6 points, tools/web/gen_skill_web.py), so a talent's skill points are written in old points and
# multiplied here.
WEB_POINT_SCALE = 3


def flat(stat: str, value: float, *tags: str) -> Mod:
    if stat in ("starting_gold", "gold_per_wave", "starting_lives") and value > 0:
        value = max(1, round(value * ECON))
    if stat in ("starting_tree_points", "tree_points_per_boss"):
        value *= WEB_POINT_SCALE
    return Mod(stat, FLAT, value, list(tags))


# --- The tree ------------------------------------------------------------------------------

add("meta_start", "Origin", START, "", 0, (0, 0), desc="Every talent grows out from here.")


def wing(region: str, spec: dict) -> None:
    """One inner wing. spec maps slot names to (id, name, kind, cost, mods, extra) tuples."""
    phi = WING_ANGLE[region]
    spots = {
        "root": (112, 0), "stem": (205, 0),
        "a1": (295, -24), "a2": (385, -27), "a3": (472, -29),
        "b1": (295, 24), "b2": (385, 27), "b3": (472, 29),
        "m1": (305, 0), "m2": (400, 0),
        "c1": (482, -9), "c2": (482, 9),
        "ax": (228, -35), "bx": (228, 35), "ay": (350, -38), "by": (350, 38),
    }
    links = {
        "root": ["meta_start"], "stem": ["root"],
        "a1": ["stem"], "a2": ["a1"], "a3": ["a2"],
        "b1": ["stem"], "b2": ["b1"], "b3": ["b2"],
        "m1": ["stem"], "m2": ["m1"],
        "c1": ["m2"], "c2": ["m2"],
        "ax": ["a1"], "bx": ["b1"], "ay": ["a2"], "by": ["b2"],
    }
    made: dict[str, Node] = {}
    for slot, entry in spec.items():
        id, name, kind, cost, mods, extra = (list(entry) + [{}])[:6]
        r, da = spots[slot]
        made[slot] = add(id, name, kind, region, cost, polar(r, phi + da), mods=mods, **extra)
    for slot, node in made.items():
        node.links = [made[l].id if l in made else l for l in links[slot]]
    choice(made["c1"], made["c2"])
    # The wing's outer nodes join the Starpath.
    made["a3"].links.append(ring_id(phi - 30))
    made["b3"].links.append(ring_id(phi + 30))
    made["c1"].links.append(ring_id(phi))
    made["c2"].links.append(ring_id(phi))


def ring_id(degrees: float) -> str:
    return "starpath_%d" % (round(degrees) % 360)


# Arsenal: raw tower power, and the keystones of the in-run skill web.
wing("arsenal", {
    "root": ("arsenal_edge", "Whetstone", ENTRY, 2, [inc("damage", 3)]),
    "stem": ("arsenal_drill", "Drill Yard", MINOR, 2, [inc("attacks_per_second", 3)]),
    "a1": ("arsenal_temper", "Tempered Steel", MINOR, 3, [inc("damage", 3)]),
    "a2": ("arsenal_temper_2", "Folded Steel", MINOR, 3, [inc("damage", 3)]),
    "a3": ("arsenal_honed", "Honed Edges", NOTABLE, 5, [inc("damage", 6), inc("projectile_speed", 10)]),
    "b1": ("arsenal_cadence", "Cadence", MINOR, 3, [inc("attacks_per_second", 3)]),
    "b2": ("arsenal_cadence_2", "Steady Rhythm", MINOR, 3, [inc("attacks_per_second", 3)]),
    "b3": ("arsenal_volley", "Rapid Volley", NOTABLE, 5, [inc("attacks_per_second", 6)]),
    "m1": ("arsenal_thornstorm", "Thornstorm Bridge", NOTABLE, 6, [],
           {"desc": "Adds the Thornstorm bridge to the skill web, which unlocks the Thornstorm tower.",
            "unlocks_nodes": ["bridge_thornstorm"]}),
    "m2": ("arsenal_piercer", "Armour Piercer", NOTABLE, 5, [flat("armour_ignore", 0.1)]),
    "c1": ("arsenal_glass_cannon", "Glass Cannon", KEYSTONE, 12, [more("damage", 20), more("starting_lives", -40)],
           {"desc": "Pick one: closes Siegecraft.", "icon": "skull"}),
    "c2": ("arsenal_siegecraft", "Siegecraft", KEYSTONE, 12,
           [more("splash_radius", 25, "area"), more("damage", 10, "area"), inc("cost", 10)],
           {"desc": "Pick one: closes Glass Cannon.", "icon": "burst"}),
    "ax": ("arsenal_focus", "Focus", NOTABLE, 8, [],
           {"desc": "Adds the Focus keystone to the skill web: towers deal 40% more damage but attack 25% slower.",
            "unlocks_nodes": ["keystone_focus"]}),
    "bx": ("arsenal_overcharge", "Overcharge", NOTABLE, 8, [],
           {"desc": "Adds the Overcharge keystone to the skill web: towers attack 30% faster but cost 20% more.",
            "unlocks_nodes": ["keystone_overcharge"]}),
    "ay": ("arsenal_hoard", "Hoard", NOTABLE, 8, [],
           {"desc": "Adds the Hoard keystone to the skill web: kills earn 1 more gold but towers cost 15% more.",
            "unlocks_nodes": ["keystone_hoard"]}),
    "by": ("arsenal_hybrid", "Fusion Lore", NOTABLE, 5, [inc("damage", 8, "hybrid"), inc("damage", 8, "triple")]),
})

# Command: gold and lives.
wing("command", {
    "root": ("command_gold", "War Chest", ENTRY, 2, [flat("starting_gold", 15)]),
    "stem": ("command_purse", "Full Purse", MINOR, 2, [flat("starting_gold", 10)]),
    "a1": ("command_sentries", "Sentries", MINOR, 2, [flat("starting_lives", 2)]),
    "a2": ("command_lives", "Fortify", MINOR, 3, [flat("starting_lives", 3)]),
    "a3": ("command_walls", "Stone Walls", NOTABLE, 5, [flat("starting_lives", 5)]),
    "b1": ("command_levy", "Levy", MINOR, 2, [flat("gold_per_wave", 4)]),
    "b2": ("command_salvage", "Salvage", MINOR, 3, [flat("sell_refund", 0.1)]),
    "b3": ("command_tithe", "Tithe", NOTABLE, 5, [flat("gold_per_wave", 8)]),
    "m1": ("command_haggler", "Haggler", MINOR, 3, [inc("cost", -3)]),
    "m2": ("command_guilds", "Guild Contracts", NOTABLE, 5, [inc("cost", -5)]),
    "c1": ("command_usury", "Usury", KEYSTONE, 12, [inc("gold_per_wave", 100), more("starting_gold", -40)],
           {"desc": "Pick one: closes Royal Treasury."}),
    "c2": ("command_treasury", "Royal Treasury", KEYSTONE, 12, [more("starting_gold", 60), more("gold_per_wave", -50)],
           {"desc": "Pick one: closes Usury.", "icon": "crown"}),
    "ax": ("command_bounty", "Bounty Office", NOTABLE, 6, [flat("bounty_bonus", 1)]),
    "bx": ("command_scrap", "Scrap Dealers", MINOR, 3, [flat("sell_refund", 0.05)]),
    "ay": ("command_points", "Head Start", KEYSTONE, 15, [flat("starting_tree_points", 1)]),
    "by": ("command_ledger", "Ledgers", MINOR, 3, [flat("gold_per_wave", 4)]),
})

# Expeditions: maps, difficulty levels and skill points.
wing("expeditions", {
    "root": ("expedition_serpentine", "Serpentine", ENTRY, 4, [],
             {"desc": "Unlocks the Serpentine map, a winding road with room to build between its bends.",
              "unlocks_maps": ["serpentine"]}),
    "stem": ("expedition_scouts", "Scouts", MINOR, 2, [inc("attack_range", 3)]),
    "a1": ("expedition_trophy_rack", "Trophy Rack", MINOR, 3, [flat("starting_gold", 10)]),
    "a2": ("expedition_trophies", "Trophy Hunter", NOTABLE, 8, [flat("tree_points_per_boss", 1)]),
    "a3": ("expedition_veterans", "Veteran Officers", KEYSTONE, 14, [flat("starting_tree_points", 1)]),
    "b1": ("expedition_hardened", "Hardened", MINOR, 3, [flat("starting_lives", 2)]),
    "b2": ("expedition_hard", "Hard Mode", NOTABLE, 6, [],
           {"desc": "Unlocks Hard difficulty: enemies have 40% more health and runs earn 50% more meta points.",
            "unlocks_difficulties": ["hard"]}),
    "b3": ("expedition_nightmare", "Nightmare", KEYSTONE, 14, [],
           {"desc": "Unlocks Nightmare difficulty: enemies have 90% more health and runs earn twice the meta points.",
            "unlocks_difficulties": ["nightmare"]}),
    "m1": ("expedition_forage", "Forage", MINOR, 3, [flat("gold_per_wave", 3)]),
    "m2": ("expedition_cartographer", "Cartographer", NOTABLE, 5, [inc("attack_range", 6)]),
    "c1": ("expedition_spoils", "Spoils of War", KEYSTONE, 12, [flat("bounty_bonus", 2), more("starting_lives", -30)],
           {"desc": "Pick one: closes Scholar's Path.", "icon": "coin"}),
    "c2": ("expedition_scholar", "Scholar's Path", KEYSTONE, 12,
           [flat("starting_tree_points", 1), more("starting_gold", -25)],
           {"desc": "Pick one: closes Spoils of War.", "icon": "book"}),
    "ax": ("expedition_banners", "Battle Banners", MINOR, 3, [inc("damage", 3)]),
    "bx": ("expedition_watch", "Night Watch", MINOR, 3, [flat("starting_lives", 2)]),
    "ay": ("expedition_relics", "Relic Hunters", NOTABLE, 5, [flat("bounty_bonus", 1)]),
    "by": ("expedition_grit", "Grit", MINOR, 3, [flat("starting_lives", 3)]),
})

# Mastery: the player's skills and tower range.
wing("mastery", {
    "root": ("mastery_range", "Long Sight", ENTRY, 3, [inc("attack_range", 4)]),
    "stem": ("mastery_will", "Focused Will", MINOR, 2, [inc("skill_damage", 8)]),
    "a1": ("mastery_spellcraft", "Spellcraft", MINOR, 3, [inc("skill_damage", 8)]),
    "a2": ("mastery_spellcraft_2", "Spellweave", MINOR, 3, [inc("skill_damage", 8)]),
    "a3": ("mastery_cataclysm", "Cataclysm", NOTABLE, 5, [inc("skill_damage", 20)]),
    "b1": ("mastery_rites", "Quick Rites", MINOR, 3, [inc("skill_cooldown", -4)]),
    "b2": ("mastery_rites_2", "Practised Rites", MINOR, 3, [inc("skill_cooldown", -4)]),
    "b3": ("mastery_quickening", "Quickening", NOTABLE, 5, [inc("skill_cooldown", -8)]),
    "m1": ("mastery_far_sight", "Far Sight", MINOR, 3, [inc("attack_range", 3)]),
    "m2": ("mastery_eagle_eye", "Eagle Eye", NOTABLE, 5, [inc("attack_range", 6)]),
    "c1": ("mastery_archmage", "Archmage", KEYSTONE, 12, [more("skill_damage", 50), more("skill_cooldown", 25)],
           {"desc": "Pick one: closes Battle Trance.", "icon": "book"}),
    "c2": ("mastery_trance", "Battle Trance", KEYSTONE, 12, [more("skill_cooldown", -30), more("skill_damage", -20)],
           {"desc": "Pick one: closes Archmage.", "icon": "speed"}),
    "ax": ("mastery_sigils", "Sigils", MINOR, 3, [inc("skill_damage", 6)]),
    "bx": ("mastery_meditation", "Meditation", MINOR, 3, [inc("skill_cooldown", -3)]),
    "ay": ("mastery_lenses", "Lenses", NOTABLE, 5, [inc("attack_range", 4), inc("projectile_speed", 10)]),
    "by": ("mastery_mana_tide", "Mana Tide", NOTABLE, 5, [inc("skill_cooldown", -5), inc("skill_damage", 5)]),
})


# The Starpath: a ring road of travel nodes. The nodes where element gates leave are a little richer.
RING_GIFTS = [
    ("Pathstone", [inc("damage", 4)]),
    ("Waymark", [flat("starting_gold", 10)]),
    ("Milestone", [inc("attacks_per_second", 4)]),
    ("Cairn", [flat("starting_lives", 1)]),
    ("Lantern", [inc("attack_range", 4)]),
]
gate_angles = {ELEMENT_ANGLE[e] % 360: e for e in ELEMENTS}
ring_count = 360 // RING_STEP
for i in range(ring_count):
    deg = i * RING_STEP
    id = ring_id(deg)
    prev = ring_id(deg - RING_STEP)
    if deg in gate_angles:
        e = gate_angles[deg]
        add(id, "%s Waystone" % ELEMENT_NAMES[e], NOTABLE, "starpath", 3, polar(RING_RADIUS, deg), [prev],
            [inc("damage", 3), inc("damage", 3, e)])
    else:
        name, mods = RING_GIFTS[i % len(RING_GIFTS)]
        add(id, name, MINOR, "starpath", 2, polar(RING_RADIUS, deg), [prev], mods)


def constellation(e: str, spec: dict) -> None:
    th = ELEMENT_ANGLE[e]
    spots = {
        "gate": (655, 0), "s1": (750, 0),
        "l1": (835, -13), "l2": (925, -16), "ln": (1015, -18),
        "r1": (835, 13), "r2": (925, 16), "rn": (1015, 18),
        "s2": (870, 0), "s3": (985, 0),
        "c1": (1095, -7), "c2": (1095, 7), "k": (1205, 0),
    }
    links = {
        "gate": [ring_id(th)], "s1": ["gate"],
        "l1": ["s1"], "l2": ["l1"], "ln": ["l2"],
        "r1": ["s1"], "r2": ["r1"], "rn": ["r2"],
        "s2": ["s1"], "s3": ["s2"],
        "c1": ["s3"], "c2": ["s3"], "k": ["c1", "c2"],
    }
    made: dict[str, Node] = {}
    for slot, entry in spec.items():
        id, name, kind, cost, mods, extra = (list(entry) + [{}])[:6]
        r, da = spots[slot]
        made[slot] = add(id, name, kind, e, cost, polar(r, th + da), mods=mods, **extra)
    for slot, node in made.items():
        node.links = [made[l].id if l in made else l for l in links[slot]]
    choice(made["c1"], made["c2"])


def element_spec(e: str, status: dict, choices: tuple, keystone: tuple, icon: str) -> dict:
    E = ELEMENT_NAMES[e]
    spec = {
        "gate": ("mastery_%s" % e, "%s Attunement" % E, ENTRY, 3, [inc("damage", 5, e)], {"icon": icon}),
        "s1": ("%s_focus" % e, "%s Focus" % E, MINOR, 3, [inc("damage", 5, e)], {"icon": icon}),
        "r1": ("%s_haste" % e, "%s Haste" % E, MINOR, 3, [inc("attacks_per_second", 4, e)]),
        "r2": ("%s_thrift" % e, "%s Thrift" % E, MINOR, 3, [inc("cost", -4, e)]),
        "rn": ("%s_reach" % e, "%s Reach" % E, NOTABLE, 6, [inc("attack_range", 8, e), inc("attacks_per_second", 6, e)]),
        "s2": ("%s_power" % e, "%s Power" % E, MINOR, 3, [inc("damage", 6, e)], {"icon": icon}),
        "s3": ("%s_heart" % e, "Heart of %s" % E, NOTABLE, 6, [inc("damage", 10, e)], {"icon": icon}),
    }
    spec.update(status)
    c1, c2 = choices
    spec["c1"] = c1[:4] + (c1[4], dict(c1[5] if len(c1) > 5 else {}, desc="Pick one: closes %s." % c2[1]))
    spec["c2"] = c2[:4] + (c2[4], dict(c2[5] if len(c2) > 5 else {}, desc="Pick one: closes %s." % c1[1]))
    spec["k"] = keystone
    return spec


constellation("fire", element_spec("fire", {
    "l1": ("fire_embers", "Embers", MINOR, 3, [inc("burn_damage", 10, "fire")]),
    "l2": ("fire_smoulder", "Smoulder", MINOR, 3, [inc("burn_duration", 15, "fire")]),
    "ln": ("fire_kindling", "Kindling", NOTABLE, 6, [inc("burn_spread_radius", 20, "fire"), inc("burn_damage", 10, "fire")]),
}, (("fire_inferno", "Inferno", NOTABLE, 7, [inc("splash_radius", 15, "fire"), inc("damage", 6, "fire")]),
    ("fire_searing", "Searing", NOTABLE, 7, [flat("burn_stacks", 1, "fire"), inc("burn_damage", 8, "fire")])),
    ("fire_pyre", "Pyre Covenant", KEYSTONE, 14, [more("burn_damage", 50, "fire"), more("damage", -25, "fire")]),
    "flame"))

constellation("storm", element_spec("storm", {
    "l1": ("storm_conduit", "Conduit", MINOR, 3, [inc("chain_range", 10, "storm")]),
    "l2": ("storm_grounding", "Grounding", MINOR, 3, [inc("chain_falloff", -15, "storm")]),
    "ln": ("storm_arc", "Arc Conductor", NOTABLE, 6, [flat("chain_count", 1, "storm")]),
}, (("storm_overload", "Overload", NOTABLE, 7, [inc("damage", 12, "storm")]),
    ("storm_static", "Static Field", NOTABLE, 7, [inc("attack_range", 12, "storm")])),
    ("storm_ball_lightning", "Ball Lightning", KEYSTONE, 14, [flat("chain_count", 2, "storm"), more("damage", -20, "storm")]),
    "bolt"))

constellation("nature", element_spec("nature", {
    "l1": ("nature_venom", "Venom", MINOR, 3, [inc("poison_damage", 10, "nature")]),
    "l2": ("nature_lingering", "Lingering Rot", MINOR, 3, [inc("poison_duration", 15, "nature")]),
    "ln": ("nature_blight", "Blight Spread", NOTABLE, 6, [flat("poison_spread_count", 1, "nature")]),
}, (("nature_virulence", "Virulence", NOTABLE, 7, [flat("poison_stacks", 1, "nature")]),
    ("nature_thornwall", "Thornwall", NOTABLE, 7, [inc("attacks_per_second", 10, "nature")])),
    ("nature_overgrowth", "Overgrowth", KEYSTONE, 14, [more("poison_damage", 40, "nature"), inc("cost", 20, "nature")]),
    "leaf"))

constellation("water", element_spec("water", {
    "l1": ("water_chill", "Chill", MINOR, 3, [inc("slow_strength", 8, "water")]),
    "l2": ("water_frost", "Hoarfrost", MINOR, 3, [inc("slow_duration", 15, "water")]),
    "ln": ("water_undertow", "Undertow", NOTABLE, 6, [inc("knockback", 25, "water"), inc("slow_strength", 8, "water")]),
}, (("water_deep_freeze", "Deep Freeze", NOTABLE, 7, [inc("slow_strength", 12, "water")]),
    ("water_riptide", "Riptide", NOTABLE, 7, [inc("damage", 15, "water")])),
    ("water_glacial_heart", "Glacial Heart", KEYSTONE, 14, [more("slow_strength", 25, "water"), more("damage", -30, "water")]),
    "drop"))

constellation("earth", element_spec("earth", {
    "l1": ("earth_daze", "Daze", MINOR, 3, [inc("stun_duration", 10, "earth")]),
    "l2": ("earth_crack", "Crack Armour", MINOR, 3, [inc("shatter_strength", 10, "earth")]),
    "ln": ("earth_seismic", "Seismic", NOTABLE, 6, [inc("splash_radius", 15, "earth"), inc("stun_duration", 10, "earth")]),
}, (("earth_bedrock", "Bedrock", NOTABLE, 7, [inc("damage", 15, "earth")]),
    ("earth_tremor", "Tremor", NOTABLE, 7, [inc("stun_duration", 20, "earth")])),
    ("earth_fault_line", "Fault Line", KEYSTONE, 14, [more("damage", 30, "earth"), more("attacks_per_second", -20, "earth")]),
    "rock"))

constellation("void", element_spec("void", {
    "l1": ("void_hex", "Malice", MINOR, 3, [inc("curse_strength", 8, "void")]),
    "l2": ("void_linger", "Long Shadow", MINOR, 3, [inc("curse_duration", 15, "void")]),
    "ln": ("void_aura", "Abyssal Aura", NOTABLE, 6, [inc("aura_damage", 15, "void"), inc("aura_radius", 10, "void")]),
}, (("void_doom", "Doomsayer", NOTABLE, 7, [inc("curse_strength", 12, "void")]),
    ("void_rift", "Rift", NOTABLE, 7, [inc("damage", 15, "void")])),
    ("void_hollow_pact", "Hollow Pact", KEYSTONE, 14,
     [more("curse_strength", 40, "void"), more("aura_damage", 25, "void"), inc("cost", 25, "void")]),
    "spiral"))

# Confluence bridges between neighbouring constellations, out past their notables.
for i, a in enumerate(ELEMENTS):
    b = ELEMENTS[(i + 1) % len(ELEMENTS)]
    deg = ELEMENT_ANGLE[a] + 30
    add("confluence_%s_%s" % (a, b), "%s-%s Confluence" % (ELEMENT_NAMES[a], ELEMENT_NAMES[b]), BRIDGE, "", 8,
        polar(1080, deg), ["%s_reach" % a, {"fire": "fire_kindling", "storm": "storm_arc", "nature": "nature_blight",
                                            "water": "water_undertow", "earth": "earth_seismic",
                                            "void": "void_aura"}[b]],
        [inc("damage", 12, a, b), inc("attacks_per_second", 6, a, b)])


# --- Checks -------------------------------------------------------------------------------

def _seg_point_distance(a, b, p) -> float:
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    length2 = dx * dx + dy * dy
    t = 0.0 if length2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / length2))
    return math.hypot(ax + t * dx - px, ay + t * dy - py)


def check() -> list[str]:
    problems = []
    ids = set(NODES)
    for n in NODES.values():
        for l in n.links + n.excludes:
            if l not in ids:
                problems.append(f"{n.id}: unknown id {l}")
        if n.kind != START and not n.mods and not (n.unlocks_nodes or n.unlocks_maps or n.unlocks_difficulties):
            problems.append(f"{n.id}: does nothing")
    nodes = list(NODES.values())
    for i, a in enumerate(nodes):
        for b in nodes[i + 1:]:
            d = math.dist(a.pos, b.pos)
            if d < MIN_NODE_GAP:
                problems.append(f"{a.id} and {b.id} are only {d:.0f} apart")
    pairs = {tuple(sorted((n.id, l))) for n in nodes for l in n.links if l in ids}
    for x, y in pairs:
        for n in nodes:
            if n.id in (x, y):
                continue
            d = _seg_point_distance(NODES[x].pos, NODES[y].pos, n.pos)
            if d < MIN_LINK_CLEARANCE:
                problems.append(f"link {x}-{y} runs {d:.0f} from {n.id}")
    # Reachable from the start.
    adj = {n.id: set() for n in nodes}
    for x, y in pairs:
        adj[x].add(y)
        adj[y].add(x)
    seen = {"meta_start"}
    todo = ["meta_start"]
    while todo:
        for nxt in adj[todo.pop()]:
            if nxt not in seen:
                seen.add(nxt)
                todo.append(nxt)
    for n in nodes:
        if n.id not in seen:
            problems.append(f"{n.id}: cannot be reached")
    return problems


def total_cost() -> tuple[int, int]:
    """Cost of every node, and of the most a player can take (the dearer side of each choice)."""
    everything = sum(n.cost for n in NODES.values())
    skipped = 0
    done = set()
    for n in NODES.values():
        for other in n.excludes:
            key = tuple(sorted((n.id, other)))
            if key not in done:
                done.add(key)
                skipped += min(n.cost, NODES[other].cost)
    return everything, everything - skipped


# --- Writing ------------------------------------------------------------------------------

def _names(ids: list[str]) -> str:
    return "Array[StringName]([%s])" % ", ".join('&"%s"' % i for i in ids)


def _num(v: float) -> str:
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
                'stat = &"%s"' % m.stat, "kind = %d" % m.kind, "value = %s" % _num(m.value)]
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
    if n.excludes:
        out.append("excludes = %s" % _names(n.excludes))
    if n.mods:
        out.append('modifiers = Array[ExtResource("1_mod")]([%s])'
                   % ", ".join('SubResource("Resource_m%d")' % i for i in range(len(n.mods))))
    for field_name in ("unlocks_nodes", "unlocks_maps", "unlocks_difficulties"):
        values = getattr(n, field_name)
        if values:
            out.append("%s = %s" % (field_name, _names(values)))
    if n.icon:
        out.append('icon = &"%s"' % n.icon)
    return "\n".join(out) + "\n"


def preview(path: str) -> None:
    from PIL import Image, ImageDraw
    size = 2700
    img = Image.new("RGB", (size, size), (10, 12, 20))
    d = ImageDraw.Draw(img)
    c = size / 2
    colors = {"arsenal": (239, 111, 108), "command": (244, 201, 93), "expeditions": (76, 201, 240),
              "mastery": (179, 136, 235), "starpath": (200, 210, 235), "fire": (228, 87, 46), "storm": (242, 193, 78),
              "nature": (91, 180, 80), "water": (46, 134, 222), "earth": (160, 120, 90), "void": (142, 92, 217),
              "": (255, 255, 255)}
    for n in NODES.values():
        for l in n.links:
            a, b = n.pos, NODES[l].pos
            d.line((c + a[0], c + a[1], c + b[0], c + b[1]), fill=(60, 66, 90), width=3)
        for x in n.excludes:
            a, b = n.pos, NODES[x].pos
            d.line((c + a[0], c + a[1], c + b[0], c + b[1]), fill=(160, 40, 40), width=1)
    radius = {START: 34, ENTRY: 26, MINOR: 20, NOTABLE: 26, BRIDGE: 22, KEYSTONE: 30}
    for n in NODES.values():
        r = radius[n.kind]
        x, y = c + n.pos[0], c + n.pos[1]
        d.ellipse((x - r, y - r, x + r, y + r), fill=colors[n.region], outline=(255, 255, 255) if n.kind == KEYSTONE else None,
                  width=3)
        d.text((x - r, y + r + 2), n.name, fill=(200, 200, 200))
    img.save(path)


def main() -> None:
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
    everything, most = total_cost()
    print("%d nodes, %d meta points for every node, %d for the most a player can take" % (len(NODES), everything, most))
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])


if __name__ == "__main__":
    main()
