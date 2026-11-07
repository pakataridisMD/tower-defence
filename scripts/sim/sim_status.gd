class_name SimStatus
extends RefCounted
## A status effect active on one enemy. Each application adds a stack (up to max_stacks)
## and refreshes the duration. Damage over time ignores armour.

var kind: StringName
var damage_per_second_per_stack := 0.0
var stacks := 0
var max_stacks := 1
var time_left := 0.0
var slow := 0.0
var damage_taken := 0.0
## Damage multiplier from the wave's element, fixed when the effect was applied.
var element_multiplier := 1.0
## The tower credited with kills from this effect.
var source: SimTower


func damage_per_second() -> float:
	return damage_per_second_per_stack * stacks * element_multiplier
