class_name DayNight
extends RefCounted
## The light over a run. The sun goes down as the waves go on: the first waves are fought in daylight,
## the middle ones at dusk and the last ones (with the boss) at night, when the towers' own light
## matters most. Every ten waves the cycle starts again with a new day.
##
## Time of day runs from 0 to 1: about 0.08 is midday, 0.3 dusk, 0.55 deep night, 0.92 dawn.

const DAY := 0.08
const DUSK := 0.3
const NIGHT := 0.58
const DAWN := 0.92
## Waves in one day.
const WAVES_PER_DAY := 10
## Rough length of a wave in seconds, used to move the sun during a wave.
const WAVE_SECONDS := 35.0
## How fast the shown time catches up with the target, in days per second.
const CATCH_UP := 0.02

## Running time: the whole part counts days, the fraction is the time of day.
var clock := DAY
var _target := DAY

var _ambient := _ramp(
		[Color(0.88, 0.88, 0.86), Color(0.9, 0.86, 0.8), Color(0.9, 0.66, 0.58), Color(0.5, 0.46, 0.66),
		Color(0.32, 0.35, 0.54), Color(0.32, 0.35, 0.54), Color(0.66, 0.64, 0.8), Color(0.88, 0.88, 0.86)],
		[0.0, 0.2, 0.3, 0.4, 0.5, 0.82, 0.92, 1.0])
var _night := _ramp(
		[Color(0, 0, 0), Color(0, 0, 0), Color(0.85, 0, 0), Color(1, 0, 0), Color(1, 0, 0), Color(0, 0, 0), Color(0, 0, 0)],
		[0.0, 0.24, 0.42, 0.5, 0.82, 0.95, 1.0])


static func _ramp(colors: Array, offsets: Array) -> Gradient:
	var g := Gradient.new()
	g.colors = PackedColorArray(colors)
	g.offsets = PackedFloat32Array(offsets)
	return g


## Where the sun should be for a run at this point. wave_index counts cleared waves.
static func target_for(wave_index: int, in_wave: bool, time_in_wave: float, won: bool) -> float:
	var day := floorf(float(wave_index) / WAVES_PER_DAY)
	var within := float(wave_index % WAVES_PER_DAY)
	if in_wave:
		within += clampf(time_in_wave / WAVE_SECONDS, 0.0, 1.0)
	var t := within / WAVES_PER_DAY
	if won:
		# The night of the last wave ends in a dawn.
		return floorf(float(maxi(wave_index - 1, 0)) / WAVES_PER_DAY) + DAWN
	# After a day's last wave, the break before the next one brings the next morning.
	return day + lerpf(DAY, NIGHT, t)


func set_target(value: float) -> void:
	_target = value


## Jump straight to the target, without the slow sunset.
func snap() -> void:
	clock = _target


func advance(delta: float) -> void:
	if clock < _target:
		clock = minf(_target, clock + CATCH_UP * delta + (_target - clock) * minf(1.0, delta * 0.8))


func time_of_day() -> float:
	return fposmod(clock, 1.0)


func ambient() -> Color:
	return _ambient.sample(time_of_day())


## 0 in daylight, 1 at night.
func night() -> float:
	return _night.sample(time_of_day()).r


func sun_energy() -> float:
	return (1.0 - night()) * 0.42


func sun_color() -> Color:
	var evening := clampf((time_of_day() - 0.18) / 0.14, 0.0, 1.0) * (1.0 - night())
	return Color(1.0, 0.93, 0.8).lerp(Color(1.0, 0.62, 0.42), evening)
