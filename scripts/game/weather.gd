class_name Weather
extends RefCounted
## The weather over a battle: the wind that bends the trees and grass of every map, and the spells of
## rain, storm, snow, ash or dust that roll over a mission for a wave or two and then pass.
##
## It is only for the eyes: the simulation never reads it, so it changes no balance. Each run rolls its
## own weather at random: one or two spells (never more), each lasting one or two waves, and only the
## kinds that fit the land (no snow in the fire lands, no ash over the frozen sea). The wind itself is
## the map's own and stays the same every time.

enum Kind { CLEAR, RAIN, STORM, SNOW, BLIZZARD, ASH, DUST }

## Most spells of weather in one level.
const MAX_SPELLS := 2
## Fewest and most waves one spell lasts.
const MIN_WAVES := 1
const MAX_WAVES := 2
## The first wave is always clear, so the player sees the land as it is before the sky turns.
const FIRST_WAVE := 2
## Clear waves at least between two spells.
const GAP := 2
## The weather that fits each land. Anything not listed here never falls there.
##   meadow / nature: green country, so rain and thunder.
##   storm: the windswept heights: thunderstorms and rain.
##   water: the frozen sea and its icy shores: snow and blizzards (never ash or dust).
##   fire: the burning lands: ash from the fires and hot dust off the cinder plains (never snow or rain).
##   earth: the red canyons: dust storms and rain.
##   void: the starless lands: falling void ash and dark storms.
##   heart: the Convergence, where every land meets: rain, thunder and snow.
const SPELLS := {
	&"meadow": [Kind.RAIN, Kind.STORM],
	&"nature": [Kind.RAIN, Kind.STORM],
	&"storm": [Kind.STORM, Kind.RAIN],
	&"water": [Kind.SNOW, Kind.BLIZZARD],
	&"fire": [Kind.ASH, Kind.DUST],
	&"earth": [Kind.DUST, Kind.RAIN],
	&"void": [Kind.ASH, Kind.STORM],
	&"heart": [Kind.RAIN, Kind.STORM, Kind.SNOW],
}
## How hard the wind blows in each land on a clear day (1 is a fair breeze).
const WIND := {
	&"meadow": 0.9, &"nature": 0.8, &"storm": 1.8, &"water": 1.2, &"fire": 0.7, &"earth": 1.3,
	&"void": 0.6, &"heart": 0.9,
}
## How much harder the wind blows during each kind of weather.
const WIND_BOOST := {
	Kind.CLEAR: 1.0, Kind.RAIN: 1.35, Kind.STORM: 2.0, Kind.SNOW: 1.15, Kind.BLIZZARD: 2.1,
	Kind.ASH: 1.1, Kind.DUST: 2.0,
}
const NAMES := {
	Kind.CLEAR: "Clear", Kind.RAIN: "Rain", Kind.STORM: "Thunderstorm", Kind.SNOW: "Snow",
	Kind.BLIZZARD: "Blizzard", Kind.ASH: "Ashfall", Kind.DUST: "Dust storm",
}
## What the banner says as each kind rolls in.
const ARRIVALS := {
	Kind.RAIN: "Rain sweeps in", Kind.STORM: "A thunderstorm breaks", Kind.SNOW: "Snow begins to fall",
	Kind.BLIZZARD: "A blizzard howls in", Kind.ASH: "Ash falls from the sky",
	Kind.DUST: "A dust storm rolls in",
}

var map_id: StringName
var biome: StringName = &"meadow"
## Waves the plan covers (the level's waves; an endless run gets no weather past them).
var waves := 0
## The spells of this run, in order, as [kind, first wave, last wave] (1-based waves).
var plan: Array = []
## The clear-day wind of this map.
var wind := 1.0
## Which way the wind blows, mostly across the map so the trees lean sideways.
var wind_dir := Vector2.RIGHT


static func for_map(map: MapData, wave_count: int = 0) -> Weather:
	return make(map.id, map.biome, wave_count)


## The weather of one run on a map. `seed_value` fixes the dice (tests and captures); left at -1 every
## run rolls new weather.
static func make(id: StringName, land: StringName, wave_count: int = 0, seed_value: int = -1) -> Weather:
	var weather := Weather.new()
	weather.map_id = id
	weather.biome = land if SPELLS.has(land) else &"meadow"
	# The wind belongs to the map: the same every time it is played.
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(String(id)) & 0x7fffffff
	weather.wind = WIND[weather.biome] * rng.randf_range(0.85, 1.15)
	var side := -1.0 if rng.randf() < 0.4 else 1.0
	weather.wind_dir = Vector2(side, rng.randf_range(-0.35, 0.35)).normalized()
	# The spells are rolled fresh for each run.
	var dice := RandomNumberGenerator.new()
	if seed_value >= 0:
		dice.seed = seed_value
	else:
		dice.randomize()
	weather.waves = wave_count if wave_count > 0 else 12
	weather.plan = roll(weather.biome, weather.waves, dice)
	return weather


## One or two spells over `wave_count` waves, each one or two waves long, at random waves, with clear
## waves between them. A short level (or a lucky roll) gets only one.
static func roll(land: StringName, wave_count: int, dice: RandomNumberGenerator) -> Array:
	var kinds: Array = (SPELLS[land] if SPELLS.has(land) else SPELLS[&"meadow"]).duplicate()
	var out: Array = []
	var last_wave := wave_count
	if last_wave < FIRST_WAVE:
		return out
	var count := 2 if dice.randf() < 0.6 else 1
	# Two spells only fit when there is room for both with a gap between them.
	if last_wave - FIRST_WAVE + 1 < 2 * MAX_WAVES + GAP + 1:
		count = 1
	# Cut the level into `count` stretches and drop one spell somewhere in each.
	var span := float(last_wave - FIRST_WAVE + 1) / count
	for i in count:
		var lo := FIRST_WAVE + int(floor(span * i))
		var hi := FIRST_WAVE + int(floor(span * (i + 1))) - 1
		if i > 0:
			lo = maxi(lo, int(out[-1][2]) + GAP + 1)
		var length := dice.randi_range(MIN_WAVES, MAX_WAVES)
		var start_max := hi - length + 1
		if start_max < lo:
			length = MIN_WAVES
			start_max = hi
		if start_max < lo:
			break
		var start := dice.randi_range(lo, start_max)
		# Two spells in one level are two different kinds when the land has more than one.
		var pick: Array = kinds.duplicate()
		if not out.is_empty() and pick.size() > 1:
			pick.erase(out[-1][0])
		var kind: Kind = pick[dice.randi() % pick.size()]
		out.append([kind, start, mini(start + length - 1, last_wave)])
	return out


## True while the run has any weather at all.
func has_spells() -> bool:
	return not plan.is_empty()


## The weather during this wave (1-based, as RunSim.wave_number counts). While the player builds, the
## next wave's weather is already rolling in.
func kind_at(wave_number: int) -> Kind:
	var spell := spell_at(wave_number)
	return Kind.CLEAR if spell.is_empty() else spell[0]


## The spell over this wave as [kind, first wave, last wave], or [] when the sky is clear.
func spell_at(wave_number: int) -> Array:
	for spell: Array in plan:
		if wave_number >= int(spell[1]) and wave_number <= int(spell[2]):
			return spell
	return []


## The next spell that starts after this wave, or [].
func next_spell(wave_number: int) -> Array:
	for spell: Array in plan:
		if int(spell[1]) > wave_number:
			return spell
	return []


## Every spell over the first `wave_count` waves, as [kind, first wave, last wave].
func spells(wave_count: int) -> Array:
	return plan.filter(func(spell: Array) -> bool: return int(spell[1]) <= wave_count)


## The kinds of weather that can fall in a land.
static func allowed(land: StringName) -> Array:
	return SPELLS[land] if SPELLS.has(land) else SPELLS[&"meadow"]


static func describe(kind: Kind) -> String:
	return NAMES[kind]


static func is_wet(kind: Kind) -> bool:
	return kind == Kind.RAIN or kind == Kind.STORM


static func is_snow(kind: Kind) -> bool:
	return kind == Kind.SNOW or kind == Kind.BLIZZARD
