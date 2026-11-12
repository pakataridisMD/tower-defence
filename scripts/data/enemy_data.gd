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

@export_group("Power")
## The rank and file's own power, one per kind of enemy (see RunSim._tick_powers):
## &"rise" - the first time it dies it falls in a heap for power_duration seconds, beyond reach, then
##           stands again with power_amount of its health. Not if it died burning.
## &"phase" - when it is hit and the power is ready it fades out for power_duration seconds: nothing
##            can hit it. Then it waits power_interval seconds.
## &"war_cry" - every power_interval seconds it roars: allies within power_radius pixels, itself too,
##              move power_amount faster for power_duration seconds.
## &"mend" - every power_interval seconds it heals allies within power_radius pixels, itself too, by
##           power_amount of their health. Not bosses, and not anyone burning or poisoned.
## &"harden" - when it is hit and the power is ready it turns to stone for power_duration seconds: it
##             stands still and takes power_amount less damage. Then it waits power_interval seconds.
## &"block" - its shield comes up every power_interval seconds and stops the next hit from a tower
##            outright. Skills, bursts and burns get past it.
## &"breath" - every power_interval seconds it breathes fire on the strongest tower within
##             power_radius pixels, which stops attacking for power_duration seconds.
## Stunned or rooted enemies cannot use a power.
@export var power: StringName
@export var power_interval: float = 0.0
@export var power_duration: float = 0.0
@export var power_radius: float = 0.0
@export var power_amount: float = 0.0
## Share of this kind that carries the power, 0 to 1, picked evenly as they come. Below 1 the ones
## with the power are marked out (a grunt's eyes burn).
@export_range(0.0, 1.0) var power_share: float = 1.0

@export_group("Forms")
## Id of the enemy it becomes when its health runs out, instead of dying: a boss's next, worse form.
## It stands still and cannot be hurt for transform_seconds while it changes, then fights on at the
## new form's full health.
@export var next_form: StringName
@export var transform_seconds: float = 3.0
## When its health runs out it does not die: it turns and flees back up its road, beyond reach, and
## leaves the board where it came in. It costs no lives and pays its bounty.
@export var flee_when_beaten: bool = false
@export_group("Counter-attack")
## Damage per second it deals to the player's mustered units it fights, at wave 1 (it grows with the
## enemy's health). 0 uses a default from its leak damage.
@export var attack_damage: float = 0.0
## A building's defences: every bolt_interval seconds it strikes up to bolt_count of the player's
## units within bolt_radius pixels for bolt_damage each (at wave 1, growing like its health).
@export var bolt_interval: float = 0.0
@export var bolt_damage: float = 0.0
@export var bolt_radius: float = 0.0
@export var bolt_count: int = 1
@export_group("Structure")
## A building of the enemy base in an assault: it never moves and never leaks. Towers shoot it
## once nothing that walks is in range. See StageData.structures.
@export var structure: bool = false


## One line on the enemy's power for tooltips and the codex, empty if it has none.
func power_text() -> String:
	match power:
		&"rise":
			var who := "It rises" if power_share >= 1.0 else "Those with burning eyes rise"
			return "%s again once, %d%% whole, %.1f s after falling. Kill it while it burns and it stays down." % [who, roundi(power_amount * 100.0), power_duration]
		&"phase":
			return "When struck it fades out of the world for %.1f s and shots pass through it. Then it needs %.0f s to gather itself." % [power_duration, power_interval]
		&"war_cry":
			return "Every %.0f s it roars: the lesser horde near it (not runners or brutes) marches %d%% faster for %.1f s." % [power_interval, roundi(power_amount * 100.0), power_duration]
		&"mend":
			return "Every %.0f s it heals the horde near it by %d%%. Burning or poisoned foes are not healed." % [power_interval, roundi(power_amount * 100.0)]
		&"harden":
			return "When struck it turns to stone for %.1f s: it stops and takes %d%% less damage." % [power_duration, roundi(power_amount * 100.0)]
		&"block":
			return "Raises its shield every %.1f s: the next tower hit is blocked outright." % power_interval
		&"breath":
			return "Every %.0f s it breathes fire on the strongest tower near it, silencing it for %.1f s." % [power_interval, power_duration]
	return ""


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
	if not next_form.is_empty():
		words.append("changes form")
	if flee_when_beaten:
		words.append("flees when beaten")
	match power:
		&"rise":
			words.append("rises once")
		&"phase":
			words.append("phases out")
		&"war_cry":
			words.append("war cry")
		&"mend":
			words.append("heals allies")
		&"harden":
			words.append("turns to stone")
		&"block":
			words.append("blocks hits")
		&"breath":
			words.append("scorches towers")
	if armour >= 10.0:
		words.append("heavily armoured")
	return words
