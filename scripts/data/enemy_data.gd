class_name EnemyData
extends Resource
## An enemy type. Health is scaled per wave by the wave set.

@export var id: StringName
@export var display_name: String
@export var max_health: float = 40.0
## Pixels per second along the path.
@export var speed: float = 80.0
## Flat damage removed from each hit.
@export var armour: float = 0.0
## Gold paid when killed.
@export var bounty: int = 3
## Lives lost if this enemy reaches the exit.
@export var leak_damage: int = 1
@export var tags: Array[StringName] = []
## One line for the campaign screen and the wave preview.
@export_multiline var description: String
## Id of an ElementData. A set element overrides the wave's, so a Fire guardian stays Fire in any
## wave. Empty takes the spawn group's element, then the wave's.
@export var element: StringName

@export_group("Traits")
## Share of max health healed each second. Burning or poisoned enemies do not heal.
@export var regen_per_second: float = 0.0
## Ignores every status effect: burns, poison, slows, stuns, curses and shatter.
@export var status_immune: bool = false
## Id of the enemy that bursts out when this one dies, and how many.
@export var split_into: StringName
@export var split_count: int = 0
## Id of the enemy this one calls up while it walks, how often in seconds, and how many each time.
@export var summon: StringName
@export var summon_interval: float = 0.0
@export var summon_count: int = 1
## Above 0, the enemy's element moves one step round the ring every this many seconds.
@export var prismatic_interval: float = 0.0

@export_group("Boss tricks")
## Allies within ward_radius pixels take this share less damage (0 to 0.9). Not the enemy itself.
@export var ward_radius: float = 0.0
@export var ward_reduction: float = 0.0
## Every silence_interval seconds, towers within silence_radius pixels stop attacking for
## silence_duration seconds.
@export var silence_interval: float = 0.0
@export var silence_radius: float = 0.0
@export var silence_duration: float = 0.0
## Every blink_interval seconds, the enemy jumps blink_distance pixels forward along its road.
@export var blink_interval: float = 0.0
@export var blink_distance: float = 0.0
## Below this share of its health, the enemy moves enrage_speed times as fast. 0 never enrages.
@export var enrage_below: float = 0.0
@export var enrage_speed: float = 1.0
## Below this share of its health, the enemy escapes: it leaves the board, costing no lives and
## paying no bounty. 0 never escapes.
@export var escape_below: float = 0.0

@export_group("Structure")
## A building of the enemy base in an assault: it never moves and never leaks. Towers shoot it
## once nothing that walks is in range. See StageData.structures.
@export var structure: bool = false


## Short words for the traits, for tooltips and the campaign screen.
func trait_words() -> PackedStringArray:
	var words: PackedStringArray = []
	if regen_per_second > 0.0:
		words.append("regenerates")
	if status_immune:
		words.append("immune to effects")
	if not split_into.is_empty() and split_count > 0:
		words.append("splits on death")
	if not summon.is_empty() and summon_interval > 0.0:
		words.append("summons")
	if prismatic_interval > 0.0:
		words.append("changes element")
	if ward_radius > 0.0 and ward_reduction > 0.0:
		words.append("shields allies")
	if silence_interval > 0.0 and silence_radius > 0.0:
		words.append("silences towers")
	if blink_interval > 0.0 and blink_distance > 0.0:
		words.append("blinks forward")
	if enrage_below > 0.0 and enrage_speed > 1.0:
		words.append("enrages")
	if escape_below > 0.0:
		words.append("escapes when beaten")
	if armour >= 10.0:
		words.append("heavily armoured")
	return words
