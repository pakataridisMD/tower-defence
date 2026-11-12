#!/usr/bin/env python3
"""Writes the meta tree (the Talents screen) to data/trees/meta/*.tres.

Edit the tables in this file and rerun; do not edit the .tres files by hand. The script deletes
the meta tree files it no longer writes, checks the layout (no two nodes too close, no link running
through a node) and prints what the whole tree costs.

    python3 tools/meta/gen_meta_tree.py            # write the tree
    python3 tools/meta/gen_meta_tree.py --preview out.png   # also draw a quick layout picture

Every talent unlocks one tower, and nothing else: no stat bonuses, no maps, no difficulty levels.
The six base towers are always open. Each of the other 38 towers (15 duals, 20 triples and the three
long-range towers) stays out of every run until its talent is taken. Inside a run the skill web
still decides when a tower can be built (its bridge, or the cores and notables it needs), so a
talent puts a tower in the player's arsenal and the web opens it during the run.

Any talent can be bought from the very start (MetaProgress sets TreeState.free_pick): the links
only show how the towers grow out of each other, they do not gate anything.

The tree is a wheel, read from the middle out, laid out on the element ring (fire at the top
right, then clockwise storm, nature, water, earth, void):
  * Origin in the centre.
  * Ring 1: the six neighbour duals (each between its two elements) and the three long-range
    towers (on their element). These are the cheap first steps.
  * Ring 2: the six duals of elements two apart, each on the element between them, reached from
    the two neighbour duals beside it.
  * Ring 3: the three duals of opposite elements, each between two ring 2 duals that carry both
    its elements.
  * Ring 3, between them: the six triples of three elements in a row, past the ring 2 dual of
    their outer two elements.
  * Ring 4: twelve triples fanned out past the opposite dual they contain, four per fan.
  * Ring 5: the two triples of every other element, at the very edge.

Pacing: a clean first pass through the campaign pays roughly 530 meta points (tools/meta_pacing.gd);
the whole tree costs about 690, so new towers keep coming through the whole campaign and the last
triples come from replays on harder levels and from skirmish runs.
"""

from __future__ import annotations

import math
import os
import re
import sys
from dataclasses import dataclass, field

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT_DIR = os.path.join(ROOT, "data", "trees", "meta")
TOWER_DIR = os.path.join(ROOT, "data", "towers")
WEB_DIR = os.path.join(ROOT, "data", "trees", "in_run")

# TreeNodeData.Kind
START, ENTRY, MINOR, NOTABLE, BRIDGE, KEYSTONE = range(6)

# Element ring order (data/elements/*.tres ring_index) and the angle of each element on the wheel,
# in degrees clockwise from east (screen y points down).
ELEMENTS = ["fire", "storm", "nature", "water", "earth", "void"]
ELEMENT_NAMES = {"fire": "Fire", "storm": "Storm", "nature": "Nature", "water": "Water", "earth": "Earth",
                 "void": "Void"}
ELEMENT_ANGLE = {"fire": -60, "storm": 0, "nature": 60, "water": 120, "earth": 180, "void": 240}

# Radius of each ring, in tree units (pixels at the default zoom). The Talents screen draws a
# dotted circle on each (scripts/ui/meta_tree_screen.gd RING_RADII).
RING_1 = 250
RING_2 = 470
RING_3 = 700
RING_4 = 950
RING_5 = 1190

# Meta points for each kind of talent.
COST_NEIGHBOUR_DUAL = 8
COST_LONGSHOT = 10
COST_TWO_STEP_DUAL = 14
COST_OPPOSITE_DUAL = 18
COST_ROW_TRIPLE = 20
COST_FAN_TRIPLE = 24
COST_SPREAD_TRIPLE = 30

# Smallest allowed distance between two node centres, and between a link and a node it does not
# touch, in tree units.
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
    unlocks_towers: list[str] = field(default_factory=list)
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


# --- The towers, read from data/ -------------------------------------------------------------

@dataclass
class Tower:
    id: str
    name: str
    elements: list[str]
    requires: list[str]


def _field(text: str, name: str) -> str | None:
    match = re.search(r'^%s = (.*)$' % name, text, re.M)
    return match.group(1) if match else None


def _ids(value: str | None) -> list[str]:
    return re.findall(r'&"(\w+)"', value or "")


def read_towers() -> dict[str, Tower]:
    towers = {}
    for name in sorted(os.listdir(TOWER_DIR)):
        if not name.endswith(".tres"):
            continue
        text = open(os.path.join(TOWER_DIR, name)).read().split("[resource]")[1]
        id = _ids(_field(text, "id"))[0]
        towers[id] = Tower(id, _field(text, "display_name").strip('"'), _ids(_field(text, "elements")),
                           _ids(_field(text, "requires_nodes")))
    return towers


def read_web() -> dict[str, tuple[str, list[str]]]:
    """In-run web nodes: id -> (display name, towers it unlocks)."""
    web = {}
    for name in sorted(os.listdir(WEB_DIR)):
        if name.endswith(".tres"):
            text = open(os.path.join(WEB_DIR, name)).read().split("[resource]")[1]
            web[_ids(_field(text, "id"))[0]] = (_field(text, "display_name").strip('"'),
                                                 _ids(_field(text, "unlocks_towers")))
    return web


TOWERS = read_towers()
WEB = read_web()


def tower_of(*elements: str, longshot: bool = False) -> Tower:
    want = set(elements)
    found = [t for t in TOWERS.values() if set(t.elements) == want and t.id.startswith(
        ("hybrid_", "triple_") if len(want) > 1 else ())]
    if longshot:
        found = [t for t in TOWERS.values() if t.elements == list(elements) and t.requires]
    assert len(found) == 1, f"expected one tower of {elements}, found {[t.id for t in found]}"
    return found[0]


def _and(words: list[str]) -> str:
    return words[0] if len(words) == 1 else ", ".join(words[:-1]) + " and " + words[-1]


def how_to_build(tower: Tower) -> str:
    """Where the skill web opens the tower during a run."""
    if tower.requires:
        return "In a run, take %s in the skill web to build it." % _and([WEB[n][0] for n in tower.requires])
    for node_id, (name, unlocks) in WEB.items():
        if tower.id in unlocks:
            return "In a run, take the %s bridge in the skill web to build it." % name
    raise ValueError("nothing in the skill web opens %s" % tower.id)


def talent(tower: Tower, kind: int, region: str, cost: int, pos, links) -> Node:
    elements = " + ".join(ELEMENT_NAMES[e] for e in tower.elements)
    desc = "Adds the %s (%s) to your towers. %s" % (tower.name, elements, how_to_build(tower))
    return add("talent_" + tower.id, tower.name, kind, region, cost, pos, links, desc=desc,
               unlocks_towers=[tower.id])


def describe(node: Node) -> str:
    return node.desc


# --- The tree ------------------------------------------------------------------------------

add("meta_start", "Origin", START, "", 0, (0, 0),
    desc="Every talent grows out from here. The six base towers are always yours; each talent adds "
         "another tower to every run.")


def ring(i: int) -> str:
    return ELEMENTS[i % len(ELEMENTS)]


def angle(i: int) -> float:
    return ELEMENT_ANGLE[ring(i)]


# Ring 1: the neighbour duals, between their elements, and the long-range towers on theirs.
neighbour = {}
for i in range(6):
    a, b = ring(i), ring(i + 1)
    neighbour[i] = talent(tower_of(a, b), ENTRY, "duals", COST_NEIGHBOUR_DUAL, polar(RING_1, angle(i) + 30),
                          ["meta_start"])
for e in ELEMENTS:
    shots = [t for t in TOWERS.values() if t.elements == [e] and t.requires]
    for tower in shots:
        talent(tower, ENTRY, "longshots", COST_LONGSHOT, polar(RING_1, ELEMENT_ANGLE[e]), ["meta_start"])

# Ring 2: duals of elements two apart, on the element between them.
two_step = {}
for i in range(6):
    two_step[i] = talent(tower_of(ring(i - 1), ring(i + 1)), NOTABLE, "duals", COST_TWO_STEP_DUAL,
                         polar(RING_2, angle(i)), [neighbour[(i - 1) % 6].id, neighbour[i].id])

# Ring 3: opposite duals, between the two ring 2 duals that carry both their elements, and the
# triples of three elements in a row, past the ring 2 dual of their outer elements.
opposite = {}
for i in (1, 3, 5):  # at the angles of storm+30, water+30, void+30
    deg = angle(i) + 30
    # two_step[i] carries ring(i - 1), two_step[i + 1] carries ring(i + 2): opposite elements.
    opposite[i] = talent(tower_of(ring(i - 1), ring(i + 2)), NOTABLE, "duals", COST_OPPOSITE_DUAL, polar(RING_3, deg),
                         [two_step[i].id, two_step[(i + 1) % 6].id])
for i in range(6):
    talent(tower_of(ring(i - 1), ring(i), ring(i + 1)), NOTABLE, "triples", COST_ROW_TRIPLE,
           polar(RING_3, angle(i)), [two_step[i].id])

# Ring 4: each opposite dual fans out into the four triples that contain it, ordered so the third
# element sits on its own side of the wheel.
for i, dual in opposite.items():
    deg = angle(i) + 30
    pair = TOWERS[dual.unlocks_towers[0]].elements
    others = [e for e in ELEMENTS if e not in pair]

    def side(e: str) -> float:
        d = (ELEMENT_ANGLE[e] - deg + 180) % 360 - 180
        return d
    others.sort(key=side)
    for j, e in enumerate(others):
        talent(tower_of(pair[0], pair[1], e), KEYSTONE, "triples", COST_FAN_TRIPLE,
               polar(RING_4, deg + (-48, -16, 16, 48)[j]), [dual.id])

# Ring 5: the two triples of every other element, at the edge, past the opposite dual's fan.
for start, deg in ((0, 330), (1, 90)):
    elements = [ring(start), ring(start + 2), ring(start + 4)]
    tower = tower_of(*elements)
    near = min((n for n in NODES.values() if n.region == "triples" and n.kind == KEYSTONE),
               key=lambda n: math.dist(n.pos, polar(RING_5, deg)))
    talent(tower, KEYSTONE, "triples", COST_SPREAD_TRIPLE, polar(RING_5, deg), [near.id])

assert len(NODES) - 1 == sum(1 for t in TOWERS.values() if t.requires or len(t.elements) > 1), \
    "every tower but the six base towers needs a talent"


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
        if n.kind != START and not n.mods and not (n.unlocks_towers or n.unlocks_nodes or n.unlocks_maps or n.unlocks_difficulties):
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
    for field_name in ("unlocks_towers", "unlocks_nodes", "unlocks_maps", "unlocks_difficulties"):
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
    colors = {"longshots": (239, 111, 108), "duals": (76, 201, 240), "triples": (179, 136, 235), "": (255, 255, 255)}
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
