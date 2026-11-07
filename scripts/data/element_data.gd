class_name ElementData
extends Resource
## One of the six elements. Elements sit on a ring: neighbours can form hybrid towers,
## and the element three steps around the ring is the opposite.

const RING_SIZE := 6

@export var id: StringName
@export var display_name: String
## Position on the ring, 0 to 5. Ring order: Fire, Storm, Nature, Water, Earth, Void.
@export_range(0, 5) var ring_index: int = 0
## Placeholder colour until real art exists.
@export var color: Color = Color.WHITE
@export var role: String
@export_multiline var signature: String
