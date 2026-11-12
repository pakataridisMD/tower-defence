class_name SimAlly
extends RefCounted
## One unit the player mustered in the counter-attack, marching up its road from our camp toward the
## enemy citadel. Its progress counts down: the road's full length at our end, 0 at the citadel's gate.

var id: int
var data: AllyData
var lane := 0
## Distance along the road from its start (the citadel's gate).
var progress := 0.0
var position := Vector2.ZERO
var max_health := 1.0
var health := 1.0
## Damage of one blow after the muster's growth.
var damage := 0.0
## Damage per second of its burn or poison after growth.
var dot_damage := 0.0
var alive := true
## Seconds until it can strike again.
var cooldown := 0.0
var heal_timer := 0.0
## What it struck last, for drawing: an enemy, a building, or null.
var target: SimEnemy
## True while it stands still to fight.
var fighting := false
## Damage it has dealt, for the end screen.
var damage_dealt := 0.0
## Bonus damage share from a banner nearby, set each step.
var aura_bonus := 0.0


func _init(p_id: int, p_data: AllyData, growth: float) -> void:
	id = p_id
	data = p_data
	max_health = p_data.max_health * growth
	health = max_health
	damage = p_data.damage * growth
	dot_damage = p_data.dot_damage * growth
	heal_timer = p_data.heal_interval * 0.5
	# A squad does not swing as one.
	cooldown = p_data.attack_interval * fposmod(float(p_id) * 0.618034, 1.0)


func is_champion() -> bool:
	return data.is_champion()
