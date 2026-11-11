class_name SimEnemy
extends RefCounted
## One enemy walking the path during a run.

## Seconds an enemy ignores new stuns after one wears off, so stuns cannot lock it in place.
const STUN_IMMUNITY := 1.0
## Pixels of knockback one enemy can take in total.
const MAX_KNOCKBACK := 240.0

var id: int
var data: EnemyData
## Health multiplier it spawned with, passed on to anything it splits into or summons.
var health_multiplier := 1.0
## Which lane of the map it walks.
var lane := 0
## Ring index of its element, or -1 when unaligned. Damage from towers depends on it.
var element := -1
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
var stun_immunity := 0.0
var knockback_taken := 0.0
var summon_timer := 0.0
var prism_timer := 0.0
var blink_timer := 0.0
var silence_timer := 0.0
## Share of damage a nearby shielding boss takes off this enemy's hits, recomputed every step.
var ward := 0.0
## True once it has dropped below its enrage threshold. It stays enraged.
var enraged := false
## A building of the enemy base (see StageData.structures): it stands still and never leaks.
var structure := false
## Assault phase a building belongs to, and what happens when it falls.
var phase := 0
var closes_lanes: PackedInt32Array = []
var releases: Array[StringName] = []
var release_health := 1.0
## True when it left the board by escaping (see EnemyData.escape_below).
var escaped := false


func _init(p_id: int, p_data: EnemyData, p_health_multiplier: float) -> void:
	id = p_id
	data = p_data
	health_multiplier = p_health_multiplier
	summon_timer = p_data.summon_interval
	prism_timer = p_data.prismatic_interval
	blink_timer = p_data.blink_interval
	silence_timer = p_data.silence_interval
	structure = p_data.structure
	max_health = p_data.max_health * p_health_multiplier
	health = max_health
	armour = p_data.armour
	base_speed = p_data.speed


func speed() -> float:
	if structure or statuses.has(&"stun"):
		return 0.0
	var slow := 0.0
	for status: SimStatus in statuses.values():
		slow = maxf(slow, status.slow)
	var rage := data.enrage_speed if enraged else 1.0
	return base_speed * rage * (1.0 - clampf(slow, 0.0, 0.9))


## Extra damage taken from curses, as a fraction.
func damage_taken_bonus() -> float:
	var bonus := 0.0
	for status: SimStatus in statuses.values():
		bonus = maxf(bonus, status.damage_taken)
	return bonus


## Armour after shatter, never below 0.
func effective_armour() -> float:
	var shatter: SimStatus = statuses.get(&"shatter")
	if shatter == null:
		return armour
	return maxf(0.0, armour - shatter.armour_reduction * shatter.stacks)


## Pushes the enemy back along the path, up to its knockback allowance. Bosses take half.
## Returns how far it moved.
func knock_back(distance: float) -> float:
	if data.tags.has(&"boss"):
		distance *= 0.5
	var moved := minf(minf(distance, MAX_KNOCKBACK - knockback_taken), progress)
	if moved <= 0.0:
		return 0.0
	knockback_taken += moved
	progress -= moved
	return moved


func has_status(kind: StringName) -> bool:
	return statuses.has(kind)


## True while it heals: it has regeneration and is neither burning nor poisoned.
func is_regenerating() -> bool:
	return data.regen_per_second > 0.0 and not statuses.has(&"burn") and not statuses.has(&"poison")


func apply_status(spec: StatusEffectData, source: SimTower, element_multiplier: float) -> void:
	if data.status_immune:
		return
	# A stun is never extended or re-applied early, and bosses cannot be stunned at all.
	if spec.kind == &"stun" and (statuses.has(&"stun") or stun_immunity > 0.0 or data.tags.has(&"boss")):
		return
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
	status.armour_reduction = maxf(status.armour_reduction, spec.armour_reduction)
	status.element_multiplier = element_multiplier
	status.source = source
