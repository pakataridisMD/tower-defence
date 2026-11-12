class_name Weather
extends RefCounted
## The weather over a battle: the wind that bends the trees and grass of every map, and the spells of
## rain, storm, snow, ash or dust that roll over some missions for a few waves and then pass.
##
## It is only for the eyes: the simulation never reads it, so it changes no balance. Each map always
## gets the same weather (it is worked out from the map's id), and it keeps going in endless runs:
## the waves are cut into blocks of BLOCK, and each block may get one spell.

enum Kind { CLEAR, RAIN, STORM, SNOW, BLIZZARD, ASH, DUST }

## Waves in one block; each block can hold one spell of weather.
const BLOCK := 8
## The spells each land can get. Storm and the frozen water land always get weather; the others get
## it in about two missions out of three.
const SPELLS := {
	&"meadow": [Kind.RAIN, Kind.RAIN, Kind.STORM],
	&"nature": [Kind.RAIN, Kind.STORM, Kind.RAIN],
	&"storm": [Kind.STORM, Kind.RAIN, Kind.STORM],
	&"water": [Kind.SNOW, Kind.BLIZZARD, Kind.SNOW],
	&"fire": [Kind.ASH],
	&"earth": [Kind.DUST],
	&"void": [Kind.ASH],
	&"heart": [Kind.RAIN, Kind.SNOW, Kind.STORM],
}
const ALWAYS: Array[StringName] = [&"storm", &"water"]
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

var map_id: StringName
var biome: StringName = &"meadow"
## False for a mission that stays clear the whole time (it still has wind).
var has_spells := true
## The clear-day wind of this map.
var wind := 1.0
## Which way the wind blows, mostly across the map so the trees lean sideways.
var wind_dir := Vector2.RIGHT

var _seed := 0


static func for_map(map: MapData) -> Weather:
	return make(map.id, map.biome)


static func make(id: StringName, land: StringName) -> Weather:
	var weather := Weather.new()
	weather.map_id = id
	weather.biome = land if SPELLS.has(land) else &"meadow"
	weather._seed = hash(String(id)) & 0x7fffffff
	var rng := RandomNumberGenerator.new()
	rng.seed = weather._seed
	weather.has_spells = weather.biome in ALWAYS or rng.randf() < 0.67
	weather.wind = WIND[weather.biome] * rng.randf_range(0.85, 1.15)
	var side := -1.0 if rng.randf() < 0.4 else 1.0
	weather.wind_dir = Vector2(side, rng.randf_range(-0.35, 0.35)).normalized()
	return weather


## The weather during this wave (1-based, as RunSim.wave_number counts). While the player builds, the
## next wave's weather is already rolling in.
func kind_at(wave_number: int) -> Kind:
	if not has_spells or wave_number < 1:
		return Kind.CLEAR
	@warning_ignore("integer_division")
	var block := (wave_number - 1) / BLOCK
	var rng := RandomNumberGenerator.new()
	rng.seed = _seed ^ ((block + 1) * 7919)
	# The first block always gets its spell, a little way in, so the player sees it early. A later
	# spell starts after its block's first wave, so two spells never run together.
	if block > 0 and rng.randf() > 0.75:
		return Kind.CLEAR
	var start := rng.randi_range(2, 4) if block == 0 else rng.randi_range(1, BLOCK - 3)
	var spells: Array = SPELLS[biome]
	var kind: Kind = spells[rng.randi() % spells.size()]
	var length := rng.randi_range(2, 3)
	var within := (wave_number - 1) % BLOCK
	return kind if within >= start and within < start + length else Kind.CLEAR


## Every spell over the first `waves` waves, as [kind, first wave, last wave].
func spells(waves: int) -> Array:
	var out: Array = []
	var current := Kind.CLEAR
	for n in range(1, waves + 1):
		var kind := kind_at(n)
		if kind != current and kind != Kind.CLEAR:
			out.append([kind, n, n])
		elif kind != Kind.CLEAR:
			out[-1][2] = n
		current = kind
	return out


static func describe(kind: Kind) -> String:
	return NAMES[kind]


static func is_wet(kind: Kind) -> bool:
	return kind == Kind.RAIN or kind == Kind.STORM


static func is_snow(kind: Kind) -> bool:
	return kind == Kind.SNOW or kind == Kind.BLIZZARD
