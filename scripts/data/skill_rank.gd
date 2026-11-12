class_name SkillRank
extends Resource
## One level of a skill. A skill starts at its first rank and the player buys the next ones with gold
## during the run. Each rank lists the whole skill at that level (not what it adds to the last one),
## so a rank can be read on its own. Numbers scale the skill's own base values in SkillData.

## The skill's name at this level, such as "Comet Shower". Empty keeps the skill's own name.
@export var title: String
## One line on what this level does that the last one did not, for the tooltip.
@export var description: String
## Gold to reach this level. The first rank is free (the skill comes with its element).
@export var cost: int = 0
## Scales the skill's damage, the damage over time of its effects, its field's damage and the
## modifiers it lends (such as Surge's faster attacks).
@export var power: float = 1.0
## Scales the skill's radius and how far it pushes.
@export var reach: float = 1.0
## Scales how long its effects (and its modifiers) last.
@export var hold: float = 1.0
## Added to the skill's base damage before `power`, for a skill that did no damage at first.
@export var damage_bonus: float = 0.0
## Added to the skill's base push before `reach`.
@export var knockback_bonus: float = 0.0
## Seconds that what it hits is thrown off its feet (a stun). Bosses keep their feet.
@export var launch: float = 0.0
## Times it lands. An aimed skill drops the rest around the point; a skill that reaches the whole
## board (such as a wave) sweeps it again.
@export var strikes: int = 1
## Extra blows on enemies picked across the board, such as lightning or falling rocks.
@export var bolts: int = 0
## Damage of each of those blows, before the waves' growth and `power`.
@export var bolt_damage: float = 0.0
## Seconds that a field stays where it landed (burning ground, brambles, an open rift). What walks
## into it takes the skill's effects again.
@export var zone_time: float = 0.0
## Damage per second to what stands in that field, before the waves' growth and `power`.
@export var zone_damage: float = 0.0
## Damage when the field closes (it collapses on what is inside), before growth and `power`.
@export var finale_damage: float = 0.0
