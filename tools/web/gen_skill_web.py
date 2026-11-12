#!/usr/bin/env python3
"""Writes the in-run skill web (the T screen in a run) to data/trees/in_run/*.tres.

Edit the tables in this file and rerun; do not edit the .tres files by hand. The script deletes the
skill web files it no longer writes, checks the layout (no two nodes too close, no link running
through a node, every node reachable) and prints what the web costs.

    python3 tools/web/gen_skill_web.py                      # write the web
    python3 tools/web/gen_skill_web.py --preview out.png    # also draw a quick layout picture

The web is ten times the size of the first one (about 400 nodes against 40). It is drawn as a
spider web: six element wedges around the Origin, each held up by spokes that run outward and
crossed by ring threads at a few radii.

  * Inner wedge (out to radius 640): the old five nodes of each element (entry, cw, ccw, core,
    notable) on three spokes, with travel nodes between them and two short spokes beside the core.
  * Outer wedge (radius 725 to 1150): six spokes. From the counter-clockwise side: the element's
    ccw theme, its status, raw damage, attack speed, its skill, and its cw theme. Notables sit on the
    ring threads at 640, 895 and 1150.
  * Two keystones at the tip of each wedge, a pick-one choice. Three of them (Focus, Overcharge,
    Hoard) stay locked until the meta tree adds them, as before.
  * Three bridges on each border between neighbouring elements: the old bridge that unlocks the
    dual tower, a Confluence and an outer Bridge that make that pair's dual towers stronger.

Costs climb with distance from the Origin (1 point near it, up to 5 at the rim and 6 for a
keystone; notables cost one more than the ring they sit on), and every bonus is smaller than the
old web's. Runs pay three skill points where they used to pay one (data/rules/run_rules.tres), so
the first rings cost about what the old web did and the outer rings are a long-run investment.

Old node ids are kept, so stage starting nodes, tower requirements (cores and notables), skills
(entries) and meta unlocks still find them.
"""

from __future__ import annotations

import math
import os
import sys
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data", "trees", "in_run")

# TreeNodeData.Kind
START, ENTRY, MINOR, NOTABLE, BRIDGE, KEYSTONE = range(6)
# Modifier.Kind
FLAT, INC, MORE = range(3)

ELEMENTS = ["fire", "storm", "nature", "water", "earth", "void"]
NAMES = {"fire": "Fire", "storm": "Storm", "nature": "Nature", "water": "Water", "earth": "Earth", "void": "Void"}
# Centre angle of each wedge, in degrees clockwise from east (screen y points down). Fire is at the
# top and the ring runs clockwise, as in the old web.
ANGLE = {e: -90 + 60 * i for i, e in enumerate(ELEMENTS)}
SKILLS = {"fire": "Meteor", "storm": "Surge", "nature": "Entangle", "water": "Tidal Wave", "earth": "Earthquake",
          "void": "Doom"}

# Ring radii, in tree units from the Origin.
ROWS = [130, 215, 300, 385, 470, 555, 640, 725, 810, 895, 980, 1065, 1150]
KEYSTONE_RADIUS = 1245
INNER_LAST = 640
# Spokes: angle from the wedge's centre line. The inner spokes run out to 640, the outer ones from 725.
INNER_SPOKES = {"c": 0.0, "l2": -20.0, "r2": 20.0, "l1": -10.0, "r1": 10.0}
INNER_START = {"c": 130, "l2": 215, "r2": 215, "l1": 470, "r1": 470}
OUTER_SPOKES = {"o_l3": -24.0, "o_l2": -14.4, "o_l1": -4.8, "o_r1": 4.8, "o_r2": 14.4, "o_r3": 24.0}
# Where each outer spoke grows from, on the 640 ring.
OUTER_PARENT = {"o_l3": "l2", "o_l2": "l1", "o_l1": "c", "o_r1": "c", "o_r2": "r1", "o_r3": "r2"}
# Rings whose neighbouring nodes are joined to each other (the web's threads).
THREADS = [385, 640, 895, 1150]
# Bridges on each border: radius, and the row whose nodes on both sides they join.
BRIDGE_ROWS = {"inner": (430, [385]), "confluence": (852, [810, 895]), "outer": (1150, [1150])}

# Cost of a minor node on each ring; notables cost one more, the keystones KEYSTONE_COST.
ROW_COST = {130: 1, 215: 1, 300: 1, 385: 1, 470: 2, 555: 2, 640: 2, 725: 3, 810: 3, 895: 3, 980: 4, 1065: 4, 1150: 5}
KEYSTONE_COST = 6
BRIDGE_COST = {"inner": 2, "confluence": 4, "outer": 6}

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


NODES: dict[str, Node] = {}


def polar(radius: float, degrees: float) -> tuple[int, int]:
    a = math.radians(degrees)
    return (round(radius * math.cos(a)), round(radius * math.sin(a)))


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


# --- What each element's nodes do ---------------------------------------------------------------
# A theme is a list of modifiers for one minor node, written for the inner rings; the outer rings
# (725 and beyond) are a touch stronger, as they cost more (see minor_mods).
#
# Themes per spoke: ccw / cw are the old side nodes' themes, "power" is the centre spoke, "left" and
# "right" the short spokes beside the core, "status" the outer status spoke. The outer damage and
# speed spokes and the skill spoke are the same for every element.

THEMES = {
    "fire": {"power": ("Stoked Coals", [inc("damage", 3, "fire")]),
             "ccw": ("Lingering Flame", [inc("burn_duration", 5, "fire")]),
             "cw": ("Heat Haze", [inc("attack_range", 2, "fire")]),
             "left": ("Searing Heat", [inc("burn_damage", 5, "fire")]),
             "right": ("Bellows", [inc("attacks_per_second", 2, "fire")]),
             "status": ("Cinders", [inc("burn_damage", 5, "fire")])},
    "storm": {"power": ("Charge", [inc("attacks_per_second", 2, "storm")]),
              "ccw": ("Long Arc", [inc("chain_range", 5, "storm")]),
              "cw": ("Charged Air", [inc("damage", 3, "storm")]),
              "left": ("Live Wire", [inc("chain_range", 5, "storm")]),
              "right": ("Thunderhead", [inc("attack_range", 2, "storm")]),
              "status": ("Grounded Path", [inc("chain_falloff", -5, "storm")])},
    "nature": {"power": ("Venom", [inc("poison_damage", 4, "nature")]),
               "ccw": ("Tall Canopy", [inc("attack_range", 2, "nature")]),
               "cw": ("Slow Rot", [inc("poison_duration", 5, "nature")]),
               "left": ("Quick Thorns", [inc("attacks_per_second", 2, "nature")]),
               "right": ("Cheap Seed", [inc("cost", -2, "nature")]),
               "status": ("Blight", [inc("poison_damage", 4, "nature")])},
    "water": {"power": ("Pressure", [inc("damage", 3, "water")]),
              "ccw": ("Undertow", [inc("knockback", 5, "water")]),
              "cw": ("Cold Snap", [inc("slow_duration", 5, "water")]),
              "left": ("Wide Basin", [inc("attack_range", 2, "water")]),
              "right": ("Rapids", [inc("attacks_per_second", 2, "water")]),
              "status": ("Rime", [inc("slow_strength", 3, "water")])},
    "earth": {"power": ("Fault Line", [inc("shatter_strength", 5, "earth")]),
              "ccw": ("Stonework", [inc("damage", 3, "earth")]),
              "cw": ("Tremor", [inc("stun_duration", 5, "earth")]),
              "left": ("Granite", [inc("damage", 3, "earth")]),
              "right": ("Rolling Stone", [inc("attacks_per_second", 2, "earth")]),
              "status": ("Crumble", [inc("shatter_strength", 5, "earth")])},
    "void": {"power": ("Pulse", [inc("attacks_per_second", 2, "void")]),
             "ccw": ("Wide Shadow", [inc("aura_radius", 5, "void")]),
             "cw": ("Hex", [inc("curse_strength", 5, "void")]),
             "left": ("Long Night", [inc("curse_duration", 5, "void")]),
             "right": ("Null Edge", [inc("damage", 3, "void")]),
             "status": ("Withering", [inc("curse_strength", 5, "void")])},
}

DAMAGE_NAMES = {"fire": "Blaze", "storm": "Strike", "nature": "Thorn", "water": "Torrent", "earth": "Boulder",
                "void": "Rend"}
SPEED_NAMES = {"fire": "Wildfire Pace", "storm": "Quickening", "nature": "Wild Growth", "water": "Swift Current",
               "earth": "Landslide", "void": "Flicker"}


def outer_damage(e: str) -> tuple[str, list[Mod]]:
    return DAMAGE_NAMES[e], [inc("damage", 3, e)]


def outer_speed(e: str) -> tuple[str, list[Mod]]:
    return SPEED_NAMES[e], [inc("attacks_per_second", 2, e)]


def outer_skill(e: str, row: int) -> tuple[str, list[Mod]]:
    # Damage and recharge take turns along the spoke.
    if ROWS.index(row) % 2:
        return "%s Rite" % SKILLS[e], [inc("skill_cooldown", -3, "skill", e)]
    return "%s Lore" % SKILLS[e], [inc("skill_damage", 6, "skill", e)]


def minor_mods(mods: list[Mod], row: int) -> list[Mod]:
    """Outer rings give a little more for their higher price: +1 to whole-percent values from 725 and
    another +1 from 980."""
    step = (1 if row >= 725 else 0) + (1 if row >= 980 else 0)
    out = []
    for m in mods:
        if m.kind == INC and step:
            pct = round(m.value * 100)
            pct += step if pct > 0 else -step
            out.append(Mod(m.stat, m.kind, pct / 100.0, m.tags))
        else:
            out.append(Mod(m.stat, m.kind, m.value, m.tags))
    return out


# Named nodes of each wedge: slot -> (id or "", name, kind, modifiers, extra). The slot is the spoke
# and the ring, as in "c@385". Old ids are used where the old web had a node.
def named(e: str) -> dict[str, tuple]:
    E = NAMES[e]
    table = {
        "fire": {
            "c@385": ("fire_core", "Stoked Coals", NOTABLE, [inc("damage", 8, "fire")]),
            "c@640": ("fire_notable", "Inferno", NOTABLE, [flat("burn_spread_radius", 50, "fire")]),
            "l2@640": ("", "Searing Brand", NOTABLE, [inc("burn_duration", 12, "fire"), inc("burn_damage", 10, "fire")]),
            "r2@640": ("", "Long Flames", NOTABLE, [inc("attack_range", 5, "fire"), inc("projectile_speed", 15, "fire")]),
            "o_l2@895": ("", "Wildfire", NOTABLE, [flat("burn_stacks", 1, "fire")]),
            "o_r2@895": ("", "Starfall", NOTABLE, [inc("skill_damage", 20, "skill", "fire")]),
            "o_l3@1150": ("", "Ashen Ground", NOTABLE, [inc("burn_damage", 15, "fire"), inc("burn_duration", 15, "fire")]),
            "o_r3@1150": ("", "Pyre Lord", NOTABLE, [inc("damage", 8, "fire"), inc("splash_radius", 10, "fire")]),
        },
        "storm": {
            "c@385": ("storm_core", "Gathering Storm", NOTABLE, [inc("attacks_per_second", 6, "storm")]),
            "c@640": ("storm_notable", "Superconductor", NOTABLE, [more("chain_falloff", -50, "storm")]),
            "l2@640": ("", "Forked Path", NOTABLE, [inc("chain_range", 15, "storm")]),
            "r2@640": ("", "Static Charge", NOTABLE, [inc("damage", 6, "storm"), inc("attacks_per_second", 3, "storm")]),
            "o_l2@895": ("", "Branching Bolts", NOTABLE, [flat("chain_count", 1, "storm")]),
            "o_r2@895": ("", "Overload", NOTABLE, [inc("skill_damage", 20, "skill", "storm")]),
            "o_l3@1150": ("", "Arc Lattice", NOTABLE, [inc("chain_range", 20, "storm"), inc("chain_falloff", -15, "storm")]),
            "o_r3@1150": ("", "Sky Hammer", NOTABLE, [inc("damage", 8, "storm"), inc("attack_range", 5, "storm")]),
        },
        "nature": {
            "c@385": ("nature_core", "Toxic Sap", NOTABLE, [inc("poison_damage", 8, "nature")]),
            "c@640": ("nature_notable", "Contagion", NOTABLE, [flat("poison_spread_count", 1, "nature")]),
            "l2@640": ("", "Deep Roots", NOTABLE, [inc("attack_range", 5, "nature"), inc("attacks_per_second", 3, "nature")]),
            "r2@640": ("", "Bounty of the Wild", NOTABLE, [flat("bounty_bonus", 1, "nature")]),
            "o_l2@895": ("", "Festering", NOTABLE, [flat("poison_stacks", 1, "nature")]),
            "o_r2@895": ("", "Strangling Vines", NOTABLE, [inc("skill_damage", 20, "skill", "nature")]),
            "o_l3@1150": ("", "Old Growth", NOTABLE, [inc("attack_range", 6, "nature"), inc("poison_duration", 15, "nature")]),
            "o_r3@1150": ("", "Plague Garden", NOTABLE, [inc("poison_damage", 15, "nature")]),
        },
        "water": {
            "c@385": ("water_core", "Deep Water", NOTABLE, [inc("damage", 8, "water")]),
            "c@640": ("water_notable", "Glacier", NOTABLE, [inc("slow_strength", 15, "water")]),
            "l2@640": ("", "Riptide", NOTABLE, [inc("knockback", 15, "water"), inc("damage", 4, "water")]),
            "r2@640": ("", "Hoarfrost", NOTABLE, [inc("slow_duration", 15, "water")]),
            "o_l2@895": ("", "Black Ice", NOTABLE, [inc("slow_strength", 10, "water"), inc("slow_duration", 10, "water")]),
            "o_r2@895": ("", "Rogue Wave", NOTABLE, [inc("skill_damage", 20, "skill", "water")]),
            "o_l3@1150": ("", "Maelstrom", NOTABLE, [inc("knockback", 20, "water"), inc("attacks_per_second", 4, "water")]),
            "o_r3@1150": ("", "Permafrost", NOTABLE, [inc("slow_duration", 20, "water"), inc("damage", 5, "water")]),
        },
        "earth": {
            "c@385": ("earth_core", "Fault Line", NOTABLE, [inc("shatter_strength", 15, "earth")]),
            "c@640": ("earth_notable", "Avalanche", NOTABLE, [flat("splash_radius", 25, "earth")]),
            "l2@640": ("", "Mountain's Weight", NOTABLE, [inc("damage", 8, "earth")]),
            "r2@640": ("", "Aftershock", NOTABLE, [inc("stun_duration", 15, "earth")]),
            "o_l2@895": ("", "Sundering", NOTABLE, [inc("shatter_strength", 20, "earth")]),
            "o_r2@895": ("", "Tectonic Fury", NOTABLE, [inc("skill_damage", 20, "skill", "earth")]),
            "o_l3@1150": ("", "Titan's Fist", NOTABLE, [inc("damage", 10, "earth"), inc("splash_radius", 10, "earth")]),
            "o_r3@1150": ("", "Seismic Lock", NOTABLE, [inc("stun_duration", 20, "earth"), inc("attacks_per_second", 3, "earth")]),
        },
        "void": {
            "c@385": ("void_core", "Hungry Dark", NOTABLE, [inc("attacks_per_second", 6, "void")]),
            "c@640": ("void_notable", "Abyssal Pull", NOTABLE, [flat("aura_damage", 0.05, "void")]),
            "l2@640": ("", "Eclipse", NOTABLE, [inc("aura_radius", 15, "void")]),
            "r2@640": ("", "Malediction", NOTABLE, [inc("curse_strength", 15, "void")]),
            "o_l2@895": ("", "Creeping Doom", NOTABLE, [inc("curse_duration", 15, "void"), inc("curse_strength", 8, "void")]),
            "o_r2@895": ("", "Final Hour", NOTABLE, [inc("skill_damage", 20, "skill", "void")]),
            "o_l3@1150": ("", "Black Sun", NOTABLE, [inc("aura_radius", 20, "void"), inc("damage", 4, "void")]),
            "o_r3@1150": ("", "Unmaking", NOTABLE, [inc("curse_strength", 20, "void"), inc("attacks_per_second", 3, "void")]),
        },
    }[e]
    # The old side nodes keep their ids; their text comes from the spoke themes.
    table["l2@215"] = ("%s_ccw" % e, "", MINOR, THEMES[e]["ccw"][1])
    table["r2@215"] = ("%s_cw" % e, "", MINOR, THEMES[e]["cw"][1])
    return table


# Keystones at the tip of each wedge: (left, right), each (id, name, modifiers, icon). The first
# three ids are the old keystones, still unlocked by the meta tree.
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

# The bridges: the tower each old bridge unlocks, and names for the confluence and outer bridge of
# each pair (element, its clockwise neighbour).
BRIDGES = {
    ("fire", "storm"): ("bridge_plasma", "Plasma", "hybrid_plasma"),
    ("storm", "nature"): ("bridge_thornstorm", "Thornstorm", "hybrid_thornstorm"),
    ("nature", "water"): ("bridge_bog", "Bog", "hybrid_bog"),
    ("water", "earth"): ("bridge_quagmire", "Quagmire", "hybrid_quagmire"),
    ("earth", "void"): ("bridge_gravity_well", "Gravity Well", "hybrid_gravity_well"),
    ("void", "fire"): ("bridge_soulflame", "Soulflame", "hybrid_soulflame"),
}
TOWER_NAMES = {"hybrid_plasma": "Plasma Coil", "hybrid_thornstorm": "Thornstorm", "hybrid_bog": "Bog",
               "hybrid_quagmire": "Quagmire", "hybrid_gravity_well": "Gravity Well", "hybrid_soulflame": "Soulflame"}

ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


# --- Building the web ----------------------------------------------------------------------------

def slot_id(e: str, spoke: str, row: int) -> str:
    return "%s_%s_%d" % (e, spoke, row)


def build() -> None:
    NODES.clear()
    add(Node("start", "Origin", START, "", 0, (0, 0), desc="Every run starts here."))
    for e in ELEMENTS:
        build_wedge(e)
    for i, e in enumerate(ELEMENTS):
        build_bridges(e, ELEMENTS[(i + 1) % 6])


def build_wedge(e: str) -> None:
    phi = ANGLE[e]
    table = named(e)
    themes = THEMES[e]
    spoke_theme = {"c": "power", "l2": "ccw", "r2": "cw", "l1": "left", "r1": "right"}
    ids: dict[str, str] = {}  # slot -> node id
    counters: dict[str, int] = {}

    def make(spoke: str, row: int, angle: float, theme: tuple[str, list[Mod]]) -> None:
        slot = "%s@%d" % (spoke, row)
        if slot in table and not table[slot][1]:
            # An old node on a themed spoke: its own id, the spoke's name and numbering.
            name, mods = theme
            counters[name] = counters.get(name, 0) + 1
            id = table[slot][0]
            add(Node(id, "%s %s" % (name, ROMAN[counters[name] - 1]), MINOR, e, ROW_COST[row], polar(row, phi + angle),
                     mods=minor_mods(mods, row)))
        elif slot in table:
            id, name, kind, mods = table[slot]
            id = id or slot_id(e, spoke, row)
            cost = ROW_COST[row] + (1 if kind == NOTABLE else 0)
            add(Node(id, name, kind, e, cost, polar(row, phi + angle), mods=list(mods)))
        else:
            name, mods = theme
            counters[name] = counters.get(name, 0) + 1
            id = slot_id(e, spoke, row)
            add(Node(id, "%s %s" % (name, ROMAN[counters[name] - 1]), MINOR, e, ROW_COST[row], polar(row, phi + angle),
                     mods=minor_mods(mods, row)))
        ids[slot] = id

    # The entry: unlocks the element's tower and skill.
    entry = "%s_entry" % e
    base_towers = {"fire": "fire_brazier", "storm": "storm_spire", "nature": "nature_thornbush",
                   "water": "water_wellspring", "earth": "earth_monolith", "void": "void_obelisk"}
    tower_names = {"fire": "Brazier", "storm": "Spire", "nature": "Thornbush", "water": "Wellspring",
                   "earth": "Monolith", "void": "Obelisk"}
    entry_names = {"fire": "Kindle", "storm": "Static", "nature": "Seedling", "water": "Spring", "earth": "Bedrock",
                   "void": "Whisper"}
    add(Node(entry, entry_names[e], ENTRY, e, 1, polar(130, phi), links=["start"],
             desc="Unlocks the %s tower and the %s skill." % (tower_names[e], SKILLS[e]),
             unlocks_towers=[base_towers[e]]))
    ids["c@130"] = entry

    for spoke, angle in INNER_SPOKES.items():
        for row in ROWS:
            if row < INNER_START[spoke] or row > INNER_LAST or (spoke == "c" and row == 130):
                continue
            make(spoke, row, angle, themes[spoke_theme[spoke]])
    for spoke, angle in OUTER_SPOKES.items():
        for row in ROWS:
            if row <= INNER_LAST:
                continue
            if spoke == "o_l3":
                theme = (themes["ccw"][0], themes["ccw"][1])
            elif spoke == "o_r3":
                theme = (themes["cw"][0], themes["cw"][1])
            elif spoke == "o_l2":
                theme = themes["status"]
            elif spoke == "o_l1":
                theme = outer_damage(e)
            elif spoke == "o_r1":
                theme = outer_speed(e)
            else:
                theme = outer_skill(e, row)
            make(spoke, row, angle, theme)

    # Spokes: each node joins the one before it on its spoke.
    for spoke in list(INNER_SPOKES) + list(OUTER_SPOKES):
        prev = None
        for row in ROWS:
            slot = "%s@%d" % (spoke, row)
            if slot not in ids:
                continue
            if prev is not None:
                link(ids[slot], ids[prev])
            prev = slot
    # Where the spokes start: the side spokes from the entry, the short spokes from the core, the
    # outer spokes from the 640 ring.
    link(ids["l2@215"], entry)
    link(ids["r2@215"], entry)
    link(ids["l1@470"], ids["c@385"])
    link(ids["r1@470"], ids["c@385"])
    for spoke, parent in OUTER_PARENT.items():
        link(ids["%s@725" % spoke], ids["%s@640" % parent])
    # Threads: neighbours on a ring, left to right.
    order_inner = ["l2", "l1", "c", "r1", "r2"]
    order_outer = ["o_l3", "o_l2", "o_l1", "o_r1", "o_r2", "o_r3"]
    for row in THREADS:
        order = order_inner if row <= INNER_LAST else order_outer
        present = [ids["%s@%d" % (s, row)] for s in order if "%s@%d" % (s, row) in ids]
        for a, b in zip(present, present[1:]):
            link(a, b)

    # Keystones at the tip: a pick-one pair.
    left, right = KEYSTONES[e]
    made = []
    for (id, name, mods, icon), spoke, side in ((left, "o_l1", -1), (right, "o_r1", 1)):
        node = add(Node(id, name, KEYSTONE, "", KEYSTONE_COST, polar(KEYSTONE_RADIUS, phi + side * 7.5),
                        links=[ids["%s@1150" % spoke]], mods=list(mods), icon=icon))
        made.append(node)
    made[0].excludes.append(made[1].id)
    made[0].desc = "Pick one: closes %s." % made[1].name
    made[1].desc = "Pick one: closes %s." % made[0].name


def build_bridges(a: str, b: str) -> None:
    """The three bridges on the border between element a and its clockwise neighbour b."""
    border = ANGLE[a] + 30
    old_id, pair_name, tower = BRIDGES[(a, b)]
    radius, rows = BRIDGE_ROWS["inner"]
    add(Node(old_id, pair_name, BRIDGE, "", BRIDGE_COST["inner"], polar(radius, border),
             links=[slot_id(a, "r2", rows[0]), slot_id(b, "l2", rows[0])],
             desc="Unlocks the %s tower." % TOWER_NAMES[tower], unlocks_towers=[tower]))
    radius, rows = BRIDGE_ROWS["confluence"]
    links = [slot_id(x, s, r) for r in rows for x, s in ((a, "o_r3"), (b, "o_l3"))]
    add(Node("confluence_%s_%s" % (a, b), "%s Confluence" % pair_name, BRIDGE, "", BRIDGE_COST["confluence"],
             polar(radius, border), links=links, mods=[inc("damage", 8, a, b), inc("attack_range", 4, a, b)]))
    radius, rows = BRIDGE_ROWS["outer"]
    add(Node("concord_%s_%s" % (a, b), "%s Concord" % pair_name, BRIDGE, "", BRIDGE_COST["outer"],
             polar(radius, border), links=[slot_id(a, "o_r3", rows[0]), slot_id(b, "o_l3", rows[0])],
             mods=[inc("attacks_per_second", 8, a, b), inc("damage", 8, a, b)]))


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
        for other in n.links + n.excludes:
            if other not in ids:
                problems.append("%s: unknown id %s" % (n.id, other))
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
        if n.id not in seen:
            problems.append("%s: cannot be reached" % n.id)
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
    if n.excludes:
        out.append("excludes = %s" % _names(n.excludes))
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
    size = 2800
    img = Image.new("RGB", (size, size), (10, 12, 20))
    d = ImageDraw.Draw(img)
    c = size / 2
    colors = {"fire": (228, 87, 46), "storm": (242, 193, 78), "nature": (91, 180, 80), "water": (46, 134, 222),
              "earth": (160, 120, 90), "void": (142, 92, 217), "": (255, 255, 255)}
    for n in NODES.values():
        for l in n.links:
            a, b = n.pos, NODES[l].pos
            d.line((c + a[0], c + a[1], c + b[0], c + b[1]), fill=(70, 76, 100), width=3)
        for x in n.excludes:
            a, b = n.pos, NODES[x].pos
            d.line((c + a[0], c + a[1], c + b[0], c + b[1]), fill=(160, 40, 40), width=1)
    radius = {START: 30, ENTRY: 24, MINOR: 14, NOTABLE: 22, BRIDGE: 20, KEYSTONE: 28}
    for n in NODES.values():
        r = radius[n.kind]
        x, y = c + n.pos[0], c + n.pos[1]
        d.ellipse((x - r, y - r, x + r, y + r), fill=colors[n.region],
                  outline=(255, 255, 255) if n.kind in (KEYSTONE, NOTABLE) else None, width=3)
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
    total = sum(n.cost for n in NODES.values())
    print("%d nodes, %d points for every node" % (len(NODES), total))
    for target in ("fire_core", "fire_notable", "bridge_plasma", "confluence_fire_storm", "keystone_focus"):
        print("  %s: %d points from the Origin" % (target, path_cost(target)))
    if "--preview" in sys.argv:
        preview(sys.argv[sys.argv.index("--preview") + 1])


if __name__ == "__main__":
    main()
