class_name WaveSpawner
extends RefCounted
## Turns a wave's spawn groups into a timeline and releases enemies, with the lane each walks, as
## their time comes.

## One due enemy: its spawn group and its lane.
class Spawn:
	var group: SpawnGroup
	var lane: int

	func _init(spawn_group: SpawnGroup, spawn_lane: int) -> void:
		group = spawn_group
		lane = spawn_lane


var _times: PackedFloat32Array = []
var _spawns: Array[Spawn] = []
var _next := 0
var _time := 0.0
## Next lane for groups that share themselves out over every lane. It carries on from wave to wave.
var _lane_turn := 0


## Lays out the wave. Groups with lane -1 share their enemies (or packs) out over `lane_count` lanes.
func start(wave: WaveData, lane_count: int = 1) -> void:
	lane_count = maxi(lane_count, 1)
	var entries: Array = []
	for g in wave.groups.size():
		var group := wave.groups[g]
		var times := group.spawn_times(g)
		var pack_lane := -1
		for i in times.size():
			var lane := group.lane
			if lane < 0:
				# A new pack (every enemy, outside PACKS) takes the next lane.
				if i == 0 or group.pack_of(i) != group.pack_of(i - 1):
					pack_lane = _lane_turn
					_lane_turn = (_lane_turn + 1) % lane_count
				lane = pack_lane
			# Order: time, then group, then position in the group, so ties keep their order.
			entries.append([group.start_delay + times[i], g, i, Spawn.new(group, mini(lane, lane_count - 1))])
	entries.sort_custom(func(a: Array, b: Array) -> bool:
		if a[0] != b[0]:
			return a[0] < b[0]
		if a[1] != b[1]:
			return a[1] < b[1]
		return a[2] < b[2])
	_times.clear()
	_spawns.clear()
	for entry: Array in entries:
		_times.append(entry[0])
		_spawns.append(entry[3])
	_next = 0
	_time = 0.0


## Every enemy due since the last call, in spawn order.
func advance(delta: float) -> Array[Spawn]:
	_time += delta
	var due: Array[Spawn] = []
	while _next < _times.size() and _times[_next] <= _time:
		due.append(_spawns[_next])
		_next += 1
	return due


func is_finished() -> bool:
	return _next >= _times.size()


func remaining() -> int:
	return _times.size() - _next


## Seconds from the wave's start to its last spawn.
func spawn_window() -> float:
	return _times[-1] if not _times.is_empty() else 0.0


## Drops the rest of the wave: nothing more spawns.
func stop() -> void:
	_next = _times.size()
