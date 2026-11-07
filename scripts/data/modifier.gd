class_name Modifier
extends Resource
## One stat change granted by a tower, a tree node or a keystone.
##
## Modifiers to the same stat combine in a fixed order (see StatCalculator):
## final = (base + all FLAT) * (1 + all INCREASED added together) * (1 + each MORE, multiplied)

enum Kind { FLAT, INCREASED, MORE }

## Name of the stat to change, for example damage, attacks_per_second or burn_duration.
@export var stat: StringName
@export var kind: Kind = Kind.FLAT
## FLAT adds this amount. INCREASED and MORE use fractions: 0.2 means 20%.
@export var value: float = 0.0
## The modifier only applies to things carrying every one of these tags. Empty applies to everything.
@export var required_tags: Array[StringName] = []


func applies_to(tags: Array[StringName]) -> bool:
	for tag in required_tags:
		if not tags.has(tag):
			return false
	return true


static func create(
		p_stat: StringName,
		p_kind: Kind,
		p_value: float,
		p_tags: Array[StringName] = []
) -> Modifier:
	var modifier := Modifier.new()
	modifier.stat = p_stat
	modifier.kind = p_kind
	modifier.value = p_value
	modifier.required_tags = p_tags
	return modifier
