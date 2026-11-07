class_name WaveSpawner
extends RefCounted
## Turns a wave's spawn groups into a timeline and releases enemy ids as their time comes.

var _times: PackedFloat32Array = []
var _enemies: Array[StringName] = []
var _next := 0
var _time := 0.0


func start(wave: WaveData) -> void:
	var entries: Array = []
	for group in wave.groups:
		for i in group.count:
			entries.append([group.start_delay + i * group.spawn_interval, group.enemy])
	entries.sort_custom(func(a: Array, b: Array) -> bool: return a[0] < b[0])
	_times.clear()
	_enemies.clear()
	for entry: Array in entries:
		_times.append(entry[0])
		_enemies.append(entry[1])
	_next = 0
	_time = 0.0


## Enemy ids due since the last call, in spawn order.
func advance(delta: float) -> Array[StringName]:
	_time += delta
	var due: Array[StringName] = []
	while _next < _times.size() and _times[_next] <= _time:
		due.append(_enemies[_next])
		_next += 1
	return due


func is_finished() -> bool:
	return _next >= _times.size()


func remaining() -> int:
	return _times.size() - _next
