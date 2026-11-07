class_name StatCalculator
extends RefCounted
## Combines a base value with modifiers in a fixed order: flat, then increased, then more.
##
## Example: base damage 10, +5 flat, 20% and 30% increased, 50% more
## gives (10 + 5) * (1 + 0.2 + 0.3) * 1.5 = 33.75.


static func compute(
		stat: StringName,
		base: float,
		modifiers: Array[Modifier],
		tags: Array[StringName] = []
) -> float:
	var flat := 0.0
	var increased := 0.0
	var more := 1.0
	for modifier in modifiers:
		if modifier.stat != stat or not modifier.applies_to(tags):
			continue
		match modifier.kind:
			Modifier.Kind.FLAT:
				flat += modifier.value
			Modifier.Kind.INCREASED:
				increased += modifier.value
			Modifier.Kind.MORE:
				more *= 1.0 + modifier.value
	# Large "reduced" penalties can push increased below -100%; never let a stat flip sign.
	return (base + flat) * maxf(0.0, 1.0 + increased) * maxf(0.0, more)
