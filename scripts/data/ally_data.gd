class_name AllyData
extends Resource
## A unit the player musters in the counter-attack of the final assault: a soldier, a war machine or
## one of the heroes, marching up a road toward the enemy citadel. Units fight what they meet on the
## road, and only they can hurt the citadel. Made by tools/allies/gen_allies.py.
##
## Health and damage are given for wave 1 and grow with the wave's health multiplier when the unit is
## mustered, the way skill damage does, so a unit keeps pace with the horde it meets.

## What a unit does, for the muster panel and the bot.
enum Role { MELEE, RANGED, SIEGE, HEALER, SUPPORT, CHAMPION }

@export var id: StringName
@export var display_name: String
## A few words on what it is, such as "Shield wall".
@export var title: String
@export_multiline var description: String
@export var role: Role = Role.MELEE
## Id of an ElementData its blows are made of, or empty for plain steel.
@export var element: StringName
## Set for a hero who marches as a champion. In the counter-attack every hero answers the call.
@export var hero: StringName
## Sort order in the muster panel.
@export var order: int = 0

@export_group("Muster")
## Gold to muster one squad.
@export var cost: int = 50
## Seconds before another squad of this kind can be mustered.
@export var cooldown: float = 4.0
## Units in a squad.
@export var count: int = 1
## At most this many of the kind on the field at once. 0 is no limit. Champions are 1.
@export var max_alive: int = 0

@export_group("Body")
@export var max_health: float = 60.0
## Flat damage removed from each blow it takes.
@export var armour: float = 0.0
## Pixels per second along the road.
@export var speed: float = 60.0
## Flies over the road: the horde cannot stop it, and it does not hold the horde back.
@export var flying: bool = false
## Holds back the enemies it fights: they stop on the road until it falls. Ranged units do not.
@export var blocks: bool = true

@export_group("Attack")
@export var damage: float = 10.0
## Seconds between blows.
@export var attack_interval: float = 1.0
## Pixels. Melee units reach about 40.
@export var attack_range: float = 40.0
## Above 0, each blow also hits every enemy this many pixels around its target.
@export var splash_radius: float = 0.0
## Each blow jumps on to this many more enemies near the target.
@export var chain_count: int = 0
## Damage against buildings of the enemy base is multiplied by this.
@export var siege_multiplier: float = 1.0
## Damage against bosses is multiplied by this.
@export var boss_multiplier: float = 1.0
## Only fights buildings: walks past the horde (a battering ram).
@export var siege_only: bool = false
## Slows what it hits by this share for slow_duration seconds.
@export_range(0.0, 0.9) var slow: float = 0.0
@export var slow_duration: float = 0.0
## Burns or poisons what it hits: damage per second at wave 1, for dot_duration seconds.
@export var dot_kind: StringName
@export var dot_damage: float = 0.0
@export var dot_duration: float = 0.0

@export_group("Support")
## Every heal_interval seconds it heals allies within heal_radius pixels, itself too, by heal_amount
## of their health.
@export var heal_amount: float = 0.0
@export var heal_radius: float = 0.0
@export var heal_interval: float = 0.0
## Allies within aura_radius pixels deal aura_damage more (0.2 is 20%). Not the bearer itself.
@export var aura_damage: float = 0.0
@export var aura_radius: float = 0.0


func is_champion() -> bool:
	return not hero.is_empty()


func is_ranged() -> bool:
	return attack_range > 70.0


## Damage per second against one enemy at wave 1, for the panel and the bot.
func damage_per_second() -> float:
	var hits := 1.0 + chain_count + (1.5 if splash_radius > 0.0 else 0.0)
	return damage * hits / maxf(0.1, attack_interval) + dot_damage


static func role_name(value: Role) -> String:
	match value:
		Role.MELEE:
			return "Line"
		Role.RANGED:
			return "Ranged"
		Role.SIEGE:
			return "Siege"
		Role.HEALER:
			return "Healer"
		Role.SUPPORT:
			return "Support"
		Role.CHAMPION:
			return "Champion"
	return ""
