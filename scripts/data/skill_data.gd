class_name SkillData
extends Resource
## A skill the player casts during a wave, such as a meteor. Each belongs to an element and opens
## when that element is taken in the skill web. A skill that has been used is on cooldown for a while.

@export var id: StringName
@export var display_name: String
## One or two lines for the tooltip.
@export_multiline var description: String
## Id of an ElementData. The skill deals that element's damage, so a wave resists it or fears it
## the same way it does a tower.
@export var element: StringName
## Skill web node that opens the skill. Empty opens it from the start of the run.
@export var requires_node: StringName
## Seconds of wave time before it can be used again.
@export var cooldown: float = 30.0
## Radius of the area it hits around the point the player picks. 0 reaches every enemy on the
## board and needs no aiming.
@export var radius: float = 0.0
## Damage to every enemy it reaches, before armour. It grows with the waves as enemy health does,
## so a skill is worth as much on the last wave as on the first.
@export var damage: float = 0.0
## Effects put on every enemy it reaches. Their damage over time grows with the waves too.
@export var status_effects: Array[StatusEffectData] = []
## Pushes every enemy it reaches back along the road. Bosses move half as far.
@export var knockback: float = 0.0
## Modifiers that hold for `duration` seconds, such as faster attacks for every tower.
@export var modifiers: Array[Modifier] = []
@export var duration: float = 0.0
## Seconds from the cast until it lands, such as a meteor's fall.
@export var impact_delay: float = 0.0
## Seconds between one strike and the next, when a level lands more than once.
@export var strike_gap: float = 0.35
## Seconds a skill that reaches the whole board takes to cross it, as a wave does, hitting each
## enemy as it passes. 0 hits everything at once.
@export var sweep_time: float = 0.0
## Seconds over which a level's bolts (lightning, falling rocks) come down.
@export var bolt_time: float = 1.6
## Its levels, bought with gold during the run. The first is the skill as it comes with its element.
## Empty means it has only one level, made of the numbers above.
@export var ranks: Array[SkillRank] = []


## How many levels it has.
func max_level() -> int:
	return maxi(1, ranks.size())


## The rank at a level counted from 1, or a plain one when it has no ranks.
func rank(level: int) -> SkillRank:
	if ranks.is_empty():
		return SkillRank.new()
	return ranks[clampi(level, 1, ranks.size()) - 1]


## Its name at a level, such as "Comet Shower".
func title_at(level: int) -> String:
	var title := rank(level).title
	return display_name if title.is_empty() else title


## True when the player has to pick a point on the board.
func is_targeted() -> bool:
	return radius > 0.0


## Tags for modifiers that change skills: "skill" and the element.
func all_tags() -> Array[StringName]:
	var result: Array[StringName] = [&"skill"]
	if not element.is_empty():
		result.append(element)
	return result
