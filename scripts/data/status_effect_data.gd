class_name StatusEffectData
extends Resource
## An effect a tower applies on hit, such as burn, poison or slow.

## burn, poison, slow, stun, curse or shatter. A stun stops the enemy while it lasts, and the enemy
## then shrugs off new stuns for a moment (SimEnemy.STUN_IMMUNITY).
@export var kind: StringName
@export var damage_per_second: float = 0.0
## Fraction of movement speed removed while active: 0.3 means 30% slower.
@export_range(0.0, 1.0) var slow: float = 0.0
## Fraction of extra damage taken while active (used by curse): 0.2 means 20% more damage taken.
@export var damage_taken: float = 0.0
## Armour removed per stack while active (used by shatter).
@export var armour_reduction: float = 0.0
## Seconds.
@export var duration: float = 1.0
@export var max_stacks: int = 1
