class_name HeroAbility
extends Resource
## A hero's signature ability, cast on its own key during a wave. A hero has two: the one it starts
## with and a stronger one it uses from HeroData.ULTIMATE_LEVEL on.

## Where the ability lands.
## AIMED: a point the player picks. SELF: around the hero. BOARD: every enemy on the board.
## CROWDS: the most crowded spots, picked for the player (see `strikes`).
enum Target { AIMED, SELF, BOARD, CROWDS }

@export var display_name: String
@export_multiline var description: String
## Seconds of wave time before it can be used again.
@export var cooldown: float = 60.0
@export var target: Target = Target.AIMED
## Cells around the point (AIMED, CROWDS) or the hero (SELF). Ignored by BOARD.
@export var radius_cells: float = 2.0
## Times it lands. CROWDS lands once on each of this many crowded spots; the rest hit again.
@export var strikes: int = 1

@export_group("Damage")
## Damage to every enemy it reaches, before armour. Grows with the waves like skill damage does.
@export var damage: float = 0.0
## Bosses take this much more of the damage.
@export var boss_damage_multiplier: float = 1.0
## Every non-boss it reaches below this share of its health dies at once. 0 turns it off.
@export_range(0.0, 1.0) var execute_below: float = 0.0
## Deals the element each enemy is weakest to, instead of the hero's own.
@export var hits_weakness: bool = false
@export var status_effects: Array[StatusEffectData] = []

@export_group("Control")
## Seconds every enemy it reaches is held in place. Bosses cannot be held and are slowed instead.
@export var hold_seconds: float = 0.0
## Pixels every enemy it reaches is pushed back along the road. Bosses move half as far.
@export var knockback: float = 0.0
## Sends every enemy it reaches back to the start of its road.
@export var send_to_start: bool = false
## Bosses are sent back too.
@export var send_bosses: bool = false
## Seconds after the cast when the held ground bursts for `burst_damage` around the same point.
@export var burst_damage: float = 0.0

@export_group("For a while")
## How long the effects below last.
@export var duration: float = 0.0
## Modifiers for every tower while it lasts, such as faster attacks.
@export var modifiers: Array[Modifier] = []
## Kills pay this many times their gold while it lasts.
@export var gold_multiplier: float = 1.0
## While it lasts, enemies that reach the end of the road are thrown back to the start instead of
## costing lives.
@export var ward: bool = false
## Lives back for every kill while it lasts, up to `lives_per_kill_max`.
@export var lives_per_kill: int = 0
@export var lives_per_kill_max: int = 0

@export_group("At once")
## Lives healed when cast.
@export var heal_lives: int = 0
## Every skill is ready again.
@export var resets_skills: bool = false
## Every other hero's ability is ready again.
@export var resets_heroes: bool = false


func is_aimed() -> bool:
	return target == Target.AIMED
