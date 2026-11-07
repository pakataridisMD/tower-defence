class_name SimEnemy
extends RefCounted
## One enemy walking the path during a run.

var id: int
var data: EnemyData
var max_health: float
var health: float
var armour: float
var base_speed: float
## Pixels walked along the path. Higher means closer to the exit.
var progress := 0.0
var position := Vector2.ZERO
var alive := true
var leaked := false
var statuses: Dictionary[StringName, SimStatus] = {}


func _init(p_id: int, p_data: EnemyData, health_multiplier: float) -> void:
	id = p_id
	data = p_data
	max_health = p_data.max_health * health_multiplier
	health = max_health
	armour = p_data.armour
	base_speed = p_data.speed


func speed() -> float:
	var slow := 0.0
	for status: SimStatus in statuses.values():
		slow = maxf(slow, status.slow)
	return base_speed * (1.0 - clampf(slow, 0.0, 0.9))


## Extra damage taken from curses, as a fraction.
func damage_taken_bonus() -> float:
	var bonus := 0.0
	for status: SimStatus in statuses.values():
		bonus = maxf(bonus, status.damage_taken)
	return bonus


func has_status(kind: StringName) -> bool:
	return statuses.has(kind)


func apply_status(spec: StatusEffectData, source: SimTower, element_multiplier: float) -> void:
	var status: SimStatus = statuses.get(spec.kind)
	if status == null:
		status = SimStatus.new()
		status.kind = spec.kind
		statuses[spec.kind] = status
	status.damage_per_second_per_stack = maxf(status.damage_per_second_per_stack, spec.damage_per_second)
	status.max_stacks = maxi(status.max_stacks, spec.max_stacks)
	status.stacks = mini(status.stacks + 1, status.max_stacks)
	status.time_left = maxf(status.time_left, spec.duration)
	status.slow = maxf(status.slow, spec.slow)
	status.damage_taken = maxf(status.damage_taken, spec.damage_taken)
	status.element_multiplier = element_multiplier
	status.source = source
