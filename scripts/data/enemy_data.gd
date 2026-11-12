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
## How it takes damage from each element round the ring from its own: &"" (plain: half from its own,
## 1.5x from the opposite), &"attuned", &"warded" or &"tank" (see ElementRules.PROFILES).
@export var affinity: StringName

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

@export_group("Boss abilities")
## The bosses' own abilities (see BossAbilities). Each one is off while its interval is 0.
## Every heal_interval seconds it heals heal_amount of its max health. Not while burning or poisoned.
@export var heal_interval: float = 0.0
@export var heal_amount: float = 0.0
## Every shield_interval seconds it raises a barrier worth shield_amount of its max health that soaks
## up damage for shield_duration seconds, then fades.
@export var shield_interval: float = 0.0
@export var shield_amount: float = 0.0
@export var shield_duration: float = 0.0
## Every bind_interval seconds it binds the bind_count strongest towers within bind_radius pixels:
## they cannot attack for bind_duration seconds.
@export var bind_interval: float = 0.0
@export var bind_count: int = 1
@export var bind_duration: float = 0.0
@export var bind_radius: float = 0.0
## Every doom_interval seconds it hurls a fireball at the strongest tower (not a hero) within
## doom_radius pixels (0 is anywhere on the board). The tower is destroyed, and its burning ruin
## blocks the cell until the wave ends.
@export var doom_interval: float = 0.0
@export var doom_radius: float = 0.0

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
## The thirty kinds of the six hordes (tools/campaign/horde.py) have one power each:
## &"douse" - every power_interval s it washes burns, poison and slows off allies within power_radius.
## &"net" - every power_interval s it nets the strongest tower within power_radius: it attacks
##          power_amount slower for power_duration s.
## &"submerge" - every power_interval s it dives under the road for power_duration s: out of reach, and
##               power_amount faster.
## &"fog" - every power_interval s towers within power_radius lose power_amount of their range for
##          power_duration s.
## &"rime_shell" - a shell worth power_amount of its health soaks up damage; it grows back power_interval s
##                 after it breaks.
## &"accrete" - every tower hit adds power_amount armour, up to power_limit hits.
## &"charge" - every power_interval s it charges for power_duration s: power_amount faster, and it cannot be
##             slowed or pushed back meanwhile.
## &"bulwark" - other enemies within power_radius gain power_amount armour.
## &"facets" - splash, chain, skill and burst damage to it is cut by power_amount.
## &"steadfast" - enemies within power_radius, itself too, cannot be slowed or pushed back.
## &"eclipse" - every power_interval s towers within power_radius deal power_amount less damage for
##              power_duration s.
## &"stalk" - towers only see it within power_amount of their range.
## &"raise" - every power_interval s it raises up to power_limit of the horde that died within power_radius
##            in the last few seconds, at power_amount of their health and paying no bounty.
## &"wail" - when it dies, towers within power_radius are silenced for power_duration s.
## &"devour" - when another enemy dies within power_radius, it heals power_amount of its health.
## &"fireborn" - burns heal it instead of hurting it, and slows wear off power_amount times as fast.
## &"smoke" - power_amount of tower hits pass straight through it (every third or so, in turn).
## &"glass_ward" - every power_interval s it wards up to power_limit allies within power_radius: each ward
##                 blocks the next tower hit, as a shield does.
## &"meltdown" - every tower hit strips power_amount armour off it.
## &"momentum" - it gains power_amount speed a second, up to power_limit; a slow, stun, root or push resets it.
## &"tailwind" - every power_interval s it and the enemies within power_radius are carried power_amount
##               pixels down the road.
## &"static" - the tower that kills it is silenced for power_duration s.
## &"hush" - towers within power_radius still hit but put no effects on anyone.
## &"spur" - every tower hit makes it power_amount faster for power_duration s, stacking up to power_limit.
## &"gust" - every power_interval s it blows every tower shot within power_radius out of the air.
## &"swarm" - every other enemy of its kind within power_radius makes it power_amount faster, up to power_limit.
## &"sow" - every power_interval s it plants a seed on the road that sprouts power_amount of the `summon`
##          enemy power_duration s later.
## &"remedy" - poison on enemies within power_radius, itself too, heals them instead.
## &"bound" - when it is slowed and the power is ready, it leaps power_amount pixels down the road and
##            shakes the slow off. Then it waits power_interval s.
## &"grow" - every power_interval s it grows by power_amount of its health, up to power_limit times.
## Stunned or rooted enemies cannot use a power.
@export var power: StringName
@export var power_interval: float = 0.0
@export var power_duration: float = 0.0
@export var power_radius: float = 0.0
@export var power_amount: float = 0.0
## Share of this kind that carries the power, 0 to 1, picked evenly as they come. Below 1 the ones
## with the power are marked out (a grunt's eyes burn).
@export_range(0.0, 1.0) var power_share: float = 1.0
## A cap some powers need: stacks of accrete or grow, allies warded, the dead raised, the most speed gained.
@export var power_limit: float = 0.0

@export_group("Lore")
## Which land's horde it marches with: &"tide", &"stone", &"hollow", &"flame", &"sky" or &"grove". Empty
## for the first horde and the bosses.
@export var horde: StringName
## A short paragraph for the codex.
@export_multiline var lore: String

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
		&"douse":
			return "Every %.0f s it washes burns, poison and slows off the horde around it." % power_interval
		&"net":
			return "Every %.0f s it nets the strongest tower near it: that tower attacks %d%% slower for %.1f s." % [power_interval, roundi(power_amount * 100.0), power_duration]
		&"submerge":
			return "Every %.0f s it dives under the road for %.1f s: nothing can reach it, and it swims %d%% faster." % [power_interval, power_duration, roundi(power_amount * 100.0)]
		&"fog":
			return "Every %.0f s its fog takes %d%% off the range of the towers near it for %.1f s." % [power_interval, roundi(power_amount * 100.0), power_duration]
		&"rime_shell":
			return "An ice shell worth %d%% of its health soaks up damage. It grows back %.0f s after it breaks." % [roundi(power_amount * 100.0), power_interval]
		&"accrete":
			return "Every tower hit grows %d more armour over it, up to %d." % [roundi(power_amount), roundi(power_amount * power_limit)]
		&"charge":
			return "Every %.0f s it charges for %.1f s, %d%% faster. Charging, it cannot be slowed or pushed." % [power_interval, power_duration, roundi(power_amount * 100.0)]
		&"bulwark":
			return "The horde near it has %d more armour." % roundi(power_amount)
		&"facets":
			return "Splash, chains, skills and bursts deal %d%% less damage to it." % roundi(power_amount * 100.0)
		&"steadfast":
			return "The horde near it, and it, cannot be slowed or pushed back."
		&"eclipse":
			return "Every %.0f s its black lantern dims the towers near it: %d%% less damage for %.1f s." % [power_interval, roundi(power_amount * 100.0), power_duration]
		&"stalk":
			return "Towers only see it within %d%% of their range." % roundi(power_amount * 100.0)
		&"raise":
			return "Every %.0f s it raises up to %d of the horde that fell near it, at %d%% health." % [power_interval, roundi(power_limit), roundi(power_amount * 100.0)]
		&"wail":
			return "When it dies, the towers near it are silenced for %.1f s." % power_duration
		&"devour":
			return "When the horde dies near it, it heals %d%% of its health." % roundi(power_amount * 100.0)
		&"fireborn":
			return "Burns heal it instead of hurting it, and slows wear off %d times as fast." % roundi(power_amount)
		&"smoke":
			return "About %d%% of tower hits go straight through it." % roundi(power_amount * 100.0)
		&"glass_ward":
			return "Every %.0f s it wards up to %d of the horde near it in glass that blocks the next tower hit." % [power_interval, roundi(power_limit)]
		&"meltdown":
			return "Every tower hit knocks %.1f armour off its slag plate." % power_amount
		&"momentum":
			return "It gains %d%% speed every second, up to %d%%. A slow, stun or push resets it." % [roundi(power_amount * 100.0), roundi(power_limit * 100.0)]
		&"tailwind":
			return "Every %.0f s its wings carry it and the horde near it down the road." % power_interval
		&"static":
			return "The tower that kills it is silenced for %.1f s." % power_duration
		&"hush":
			return "Towers near it put no burns, slows, stuns or curses on anyone."
		&"spur":
			return "Every hit makes it %d%% faster for %.0f s, stacking up to %d%%." % [roundi(power_amount * 100.0), power_duration, roundi(power_limit * 100.0)]
		&"gust":
			return "Every %.0f s it blows the towers' shots near it out of the air." % power_interval
		&"swarm":
			return "Every other of its kind near it makes it %d%% faster, up to %d%%." % [roundi(power_amount * 100.0), roundi(power_limit * 100.0)]
		&"sow":
			return "Every %.0f s it plants a seed that sprouts %d more %.0f s later." % [power_interval, roundi(power_amount), power_duration]
		&"remedy":
			return "Poison heals the horde near her instead of hurting it."
		&"bound":
			return "Slowed, it leaps clear down the road and shakes it off. Then it needs %.0f s." % power_interval
		&"grow":
			return "Every %.0f s it grows %d%% more health, up to %d times." % [power_interval, roundi(power_amount * 100.0), roundi(power_limit)]
	return ""


## A line on each of a boss's abilities for the codex, empty if it has none.
func boss_text() -> String:
	var lines: PackedStringArray = []
	if heal_interval > 0.0 and heal_amount > 0.0:
		lines.append("Every %.0f s it heals %s%% of its life, but not while burning or poisoned." % [heal_interval, String.num(heal_amount * 100.0, 2)])
	if shield_interval > 0.0 and shield_amount > 0.0:
		lines.append("Every %.0f s it raises a barrier worth %s%% of its life for %.0f s." % [shield_interval, String.num(shield_amount * 100.0, 1), shield_duration])
	if bind_interval > 0.0 and bind_duration > 0.0:
		var towers := "tower" if bind_count == 1 else "%d towers" % bind_count
		lines.append("Every %.0f s it binds the strongest %s near it: they cannot fire for %.1f s." % [bind_interval, towers, bind_duration])
	if silence_interval > 0.0 and silence_radius > 0.0:
		lines.append("Every %.0f s it silences every tower near it for %.1f s." % [silence_interval, silence_duration])
	if doom_interval > 0.0:
		lines.append("Every %.0f s it hurls a fireball that destroys a tower. Its ruin burns until the wave ends." % doom_interval)
	return "\n".join(lines)


## Short words for the traits, for tooltips and the campaign screen.
func trait_words() -> PackedStringArray:
	var words: PackedStringArray = []
	match affinity:
		&"attuned":
			words.append("immune to its element")
		&"warded":
			words.append("immune to its element, resists neighbours")
		&"tank":
			words.append("tank")
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
	if heal_interval > 0.0 and heal_amount > 0.0:
		words.append("heals itself")
	if shield_interval > 0.0 and shield_amount > 0.0:
		words.append("raises a barrier")
	if bind_interval > 0.0 and bind_duration > 0.0:
		words.append("binds towers")
	if doom_interval > 0.0:
		words.append("destroys towers")
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
		&"douse":
			words.append("cleanses the horde")
		&"net":
			words.append("nets towers")
		&"submerge":
			words.append("dives under")
		&"fog":
			words.append("fogs towers")
		&"rime_shell":
			words.append("ice shell")
		&"accrete":
			words.append("armours up when hit")
		&"charge":
			words.append("charges")
		&"bulwark":
			words.append("armours the horde")
		&"facets":
			words.append("resists splash")
		&"steadfast":
			words.append("steadies the horde")
		&"eclipse":
			words.append("dims towers")
		&"stalk":
			words.append("hidden")
		&"raise":
			words.append("raises the dead")
		&"wail":
			words.append("death wail")
		&"devour":
			words.append("feeds on the dead")
		&"fireborn":
			words.append("healed by fire")
		&"smoke":
			words.append("dodges hits")
		&"glass_ward":
			words.append("wards the horde")
		&"meltdown":
			words.append("armour melts")
		&"momentum":
			words.append("builds speed")
		&"tailwind":
			words.append("tailwind")
		&"static":
			words.append("shocks its killer")
		&"hush":
			words.append("hushes towers")
		&"spur":
			words.append("spurred by hits")
		&"gust":
			words.append("blows shots away")
		&"swarm":
			words.append("pack speed")
		&"sow":
			words.append("sows Briarlings")
		&"remedy":
			words.append("poison heals")
		&"bound":
			words.append("leaps free")
		&"grow":
			words.append("grows")
	if armour >= 10.0:
		words.append("heavily armoured")
	return words
