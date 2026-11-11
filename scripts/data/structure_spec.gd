class_name StructureSpec
extends Resource
## One building of the enemy base in an assault stage: which enemy it is, where it stands, and in
## which phase it can be hurt. It can close roads and release enemies when it falls.

## Id of an EnemyData with `structure` set.
@export var enemy: StringName
## Grid cell it stands on. Towers cannot be built there.
@export var cell: Vector2i
## Phase of the assault it belongs to, from 1. Buildings of a later phase are shielded until every
## building of the phases before it has fallen.
@export var phase: int = 1
## The road its releases and summons walk (0 is the map's main path).
@export var lane: int = 0
## Roads that close when it falls: nothing more comes down them.
@export var closes_lanes: PackedInt32Array = []
## Enemies that come out when it falls, one of each, at the strength of the wave being fought.
@export var releases: Array[StringName] = []
## Health of what it releases, as a share of a normal enemy of its kind at this wave. Echoes are
## weaker copies.
@export var release_health: float = 1.0
