class_name TreeNodeData
extends Resource
## One node of a skill tree. The in-run web and the meta tree both use this.

enum Kind { START, ENTRY, MINOR, NOTABLE, BRIDGE, KEYSTONE }

@export var id: StringName
@export var display_name: String
## One line, shown in the tooltip.
@export var description: String
@export var kind: Kind = Kind.MINOR
## The part of the tree this node belongs to, which sets its colour: an element id in the in-run
## web, a branch id in the meta tree. Empty for the start, bridges and keystones.
@export var region: StringName
## Points needed to take this node.
@export var cost: int = 1
## Where the node is drawn on the tree screen, in pixels from the start node.
@export var position: Vector2
## Ids of connected nodes. Links work both ways, so each pair only needs listing on one side.
@export var links: Array[StringName] = []
## Ids of nodes that must ALL be taken before this one can be: a combination node (a dual or triple
## tower in the in-run tree, which needs a level of each of its elements). Such a node hangs on its
## requirements instead of on links, and none of them can be refunded while it is taken.
@export var requires: Array[StringName] = []
@export var modifiers: Array[Modifier] = []
## Ids of nodes this one is a pick-one choice with: taking either closes the others until it is
## refunded. Works both ways, so each pair only needs listing on one side.
@export var excludes: Array[StringName] = []
## A branch of options this node belongs to (in-run tree): of all the nodes with the same group, at
## most choice_limit can be taken. Empty for nodes outside any branch.
@export var choice_group: StringName
@export var choice_limit: int = 1

@export_group("Unlocks")
## In-run web: ids of towers this node lets the player build.
@export var unlocks_towers: Array[StringName] = []
## Meta tree: ids of in-run web nodes this node makes available. A node listed by any meta node
## stays locked in runs until one of them is taken.
@export var unlocks_nodes: Array[StringName] = []
## Meta tree: ids of maps this node makes available. Maps listed by no meta node are always open.
@export var unlocks_maps: Array[StringName] = []
## Meta tree: ids of difficulty levels this node makes available.
@export var unlocks_difficulties: Array[StringName] = []

@export_group("Look")
## Icon on the tree screen, by name (see assets/art/game/tree/icon_*.png). Empty picks one from what the
## node unlocks or the stat it changes.
@export var icon: StringName
