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
## Damage of shots in flight towards it from towers that target the weakest enemy.
var incoming := 0.0
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

# Its power (see EnemyData.power).
## True when this one carries its kind's power (see EnemyData.power_share).
var has_power := false
## Seconds until the power can be used again.
var power_timer := 0.0
## Seconds left of a power that lasts: phased out, or turned to stone.
var power_left := 0.0
## Seconds left lying in a heap before it rises (power "rise"). Above 0 it is down.
var downed := 0.0
## True once it has risen, so it stays dead the next time.
var risen := false
## True while its shield is up (power "block").
var shield_up := false
## Seconds left of a war cry's speed, and how much faster it runs meanwhile.
var haste_left := 0.0
var haste := 0.0
# The six hordes' powers (see EnemyData.power).
## What is left of its ice shell (power "rime_shell").
var shell := 0.0
## Hits stacked up (power "accrete") or times grown (power "grow").
var stacks := 0
## Armour lent by a Runebearer nearby, recomputed every step.
var bonus_armour := 0.0
## True while a Menhir Walker stands near it: no slow holds it and nothing pushes it back. Every step.
var steady := false
## True while a Greenwitch is near it: poison heals it. Every step.
var remedied := false
## Counts up by the share of hits it dodges; a hit passes through each time it reaches 1 (power "smoke").
var dodge := 0.0
## Speed gained by walking unchecked (power "momentum") and from the pack (power "swarm").
var momentum := 0.0
var swarm := 0.0
## Speed from being struck (power "spur"), and for how long.
var spur := 0.0
var spur_left := 0.0
## Raised by a Gravecaller: it pays no bounty and cannot be raised again.
var raised := false
## Seconds left while it changes into its next form: it stands still and nothing can touch it.
var transforming := 0.0
## How many times it has changed form, from 0.
var form := 0
## True once a boss that flees when beaten has turned back toward its citadel.
var fleeing := false
## The mustered unit holding it on the road, or null.
var blocked_by: SimAlly
## Seconds until it can strike the unit holding it, and until a building's defences fire again.
var attack_timer := 0.0
var bolt_timer := 0.0


func _init(p_id: int, p_data: EnemyData, p_health_multiplier: float) -> void:
	id = p_id
	data = p_data
	health_multiplier = p_health_multiplier
	summon_timer = p_data.summon_interval
	prism_timer = p_data.prismatic_interval
	blink_timer = p_data.blink_interval
	silence_timer = p_data.silence_interval
	# A power is first used halfway through its interval, so a fresh enemy shows it soon.
	power_timer = p_data.power_interval * 0.5
	# Spread so a pack does not all use its power at the same moment.
	power_timer *= 0.4 + 1.2 * fposmod(float(p_id) * 0.381966, 1.0)
	# Spread evenly: the golden ratio walks round the unit interval without bunching.
	has_power = not p_data.power.is_empty() and fposmod(float(p_id) * 0.618034, 1.0) < p_data.power_share
	shield_up = has_power and p_data.power == &"block"
	if has_power and p_data.power == &"rime_shell":
		shell = p_data.max_health * p_health_multiplier * p_data.power_amount
	structure = p_data.structure
	max_health = p_data.max_health * p_health_multiplier
	health = max_health
	armour = p_data.armour
	base_speed = p_data.speed
	bolt_timer = p_data.bolt_interval


## Turns it into another kind of enemy at the same strength: a boss's next form. It comes back at the
## new form's full health and starts its tricks afresh.
func become(p_data: EnemyData, seconds: float) -> void:
	data = p_data
	max_health = p_data.max_health * health_multiplier
	health = max_health
	armour = p_data.armour
	base_speed = p_data.speed
	summon_timer = p_data.summon_interval
	prism_timer = p_data.prismatic_interval
	blink_timer = p_data.blink_interval
	silence_timer = p_data.silence_interval
	enraged = false
	statuses.clear()
	knockback_taken = 0.0
	form += 1
	transforming = maxf(0.1, seconds)


func speed() -> float:
	if structure or statuses.has(&"stun") or statuses.has(&"root") or downed > 0.0 or is_hardened() \
			or transforming > 0.0 or blocked_by != null:
		return 0.0
	var slow := 0.0
	if not unshakable():
		for status: SimStatus in statuses.values():
			slow = maxf(slow, status.slow)
	var rage := data.enrage_speed if enraged else 1.0
	var cry := 1.0 + haste if haste_left > 0.0 else 1.0
	var boost := 1.0 + momentum + swarm + (spur if spur_left > 0.0 else 0.0)
	if power_left > 0.0 and (data.power == &"charge" or data.power == &"submerge"):
		boost += data.power_amount
	return base_speed * rage * cry * boost * (1.0 - clampf(slow, 0.0, 0.9))


## True when nothing can slow it or push it back: a Menhir Walker stands near, or it is charging.
func unshakable() -> bool:
	return steady or (power_left > 0.0 and data.power == &"charge")


## True while it is under the road (power "submerge").
func is_submerged() -> bool:
	return power_left > 0.0 and data.power == &"submerge"


## True while any status slows it.
func is_slowed() -> bool:
	for status: SimStatus in statuses.values():
		if status.slow > 0.0:
			return true
	return false


## True while it is phased out (power "phase").
func is_phased() -> bool:
	return power_left > 0.0 and data.power == &"phase"


## True while it is stone (power "harden").
func is_hardened() -> bool:
	return power_left > 0.0 and data.power == &"harden"


## True while nothing can touch it: lying in a heap before it rises, phased out, changing form or
## fleeing. Towers do not aim at it, and hits, effects and pushes pass it by.
func untouchable() -> bool:
	return downed > 0.0 or is_phased() or is_submerged() or transforming > 0.0 or fleeing


## True when it is free to use its power: it has one, and nothing holds it.
func can_use_power() -> bool:
	return has_power and downed <= 0.0 and not statuses.has(&"stun") and not statuses.has(&"root")


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
		return armour + bonus_armour
	return maxf(0.0, armour + bonus_armour - shatter.armour_reduction * shatter.stacks)


## Pushes the enemy back along the path, up to its knockback allowance. Bosses take half.
## Returns how far it moved.
func knock_back(distance: float) -> float:
	if untouchable() or unshakable():
		return 0.0
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
	if data.status_immune or untouchable():
		return
	# A root (from a hero) holds anything but a boss, whatever stuns came before.
	if spec.kind == &"root" and data.tags.has(&"boss"):
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
