class_name SimSkillCast
extends RefCounted
## A skill on its way: what it does at the level it was cast at, and the blows still to land. A meteor
## takes a moment to fall, a wave takes a while to cross the board, lightning strikes one bolt after
## another and burning ground stays a few seconds. RunSim plays them out step by step; the board reads
## them to draw what is coming.

## Bolts are this wide where they land.
const BOLT_RADIUS := 44.0
## A field hurts what stands in it this often.
const ZONE_TICK := 0.5


## One blow: a strike on a point, a sweep across the board, a bolt on an enemy, or a field closing.
class Blow:
	## &"strike" (an area round `at`, or the whole board when `radius` is 0), &"sweep" (a front that
	## crosses the board from `at.x` to `to_x`), &"bolt" (on an enemy picked when it lands) or
	## &"finale" (the field at `at` collapses).
	var kind: StringName
	## Seconds after the cast that it lands (a sweep sets off then).
	var time := 0.0
	var at := Vector2.ZERO
	var radius := 0.0
	var damage := 0.0
	## The first strike of an aimed skill, which leaves the field behind.
	var main := false
	## A sweep's far side and how long it takes to get there.
	var to_x := 0.0
	var sweep_time := 0.0
	## Where the sweep's front has got to, and who it has already hit.
	var front := 0.0
	var swept: Dictionary[int, bool] = {}
	## The enemy a bolt fell on, once it has landed.
	var target: SimEnemy
	var done := false

	## A sweep's front, between its start and its far side, `age` seconds after the cast.
	func front_at(age: float) -> float:
		var t := clampf((age - time) / maxf(0.01, sweep_time), 0.0, 1.0)
		return lerpf(at.x, to_x, t)


## A field left where the skill landed.
class Zone:
	var at := Vector2.ZERO
	var radius := 0.0
	var time_left := 0.0
	var duration := 0.0
	var tick := 0.0
	var damage_per_second := 0.0
	var finale_damage := 0.0


var skill: SkillData
var level := 1
var rank: SkillRank
## The point it was cast at, or the board's centre for a skill that needs no aim.
var at := Vector2.ZERO
## Seconds since it was cast.
var age := 0.0
var blows: Array[Blow] = []
var zones: Array[Zone] = []
## What it does to each enemy it reaches, at this level and this wave.
var damage := 0.0
var radius := 0.0
var knockback := 0.0
var launch := 0.0
var effects: Array[StatusEffectData] = []
## Its element as an index, for weaknesses and resistances (empty when it has none).
var elements: Array[int] = []


## True once every blow has landed and every field has closed.
func is_finished() -> bool:
	if not zones.is_empty():
		return false
	for blow in blows:
		if not blow.done:
			return false
	return true


## The blows of a kind, landed or not.
func blows_of(kind: StringName) -> Array[Blow]:
	var result: Array[Blow] = []
	for blow in blows:
		if blow.kind == kind:
			result.append(blow)
	return result


## Seconds from the cast until it is all over (the last blow, sweep or field).
func length() -> float:
	var end := 0.0
	for blow in blows:
		end = maxf(end, blow.time + blow.sweep_time)
	if rank != null and rank.zone_time > 0.0:
		end = maxf(end, skill.impact_delay + rank.zone_time)
	return end
