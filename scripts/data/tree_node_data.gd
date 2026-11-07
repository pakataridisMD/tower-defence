class_name TreeNodeData
extends Resource
## One node of a skill tree. The in-run web and the meta tree both use this.

enum Kind { START, ENTRY, MINOR, NOTABLE, BRIDGE, KEYSTONE }

@export var id: StringName
@export var display_name: String
## One line, shown in the tooltip.
@export var description: String
@export var kind: Kind = Kind.MINOR
## Id of the element region this node belongs to. Empty for the start, bridges and keystones.
@export var element: StringName
## Points needed to take this node.
@export var cost: int = 1
## Where the node is drawn on the tree screen, in pixels from the start node.
@export var position: Vector2
## Ids of connected nodes. Links work both ways, so each pair only needs listing on one side.
@export var links: Array[StringName] = []
@export var modifiers: Array[Modifier] = []
## Ids of towers this node lets the player build.
@export var unlocks_towers: Array[StringName] = []
