class_name SpawnGroup
extends Resource
## A batch of one enemy type inside a wave, and the rhythm it arrives in.

## How the group's enemies are spaced out in time.
enum Pattern {
	## Evenly, one every spawn_interval.
	STREAM,
	## In tight packs of pack_size (spawn_interval apart inside a pack), pack_gap seconds between packs.
	## A pack keeps to one road when the group shares itself out over the lanes.
	PACKS,
	## Slow at first, then faster and faster: from twice spawn_interval down to a third of it.
	SURGE,
	## Unevenly, anywhere from a quarter to one and three quarters of spawn_interval apart.
	SCATTER,
}

## Id of an EnemyData.
@export var enemy: StringName
@export var count: int = 10
## Seconds between spawns (inside a pack for PACKS; the average for SCATTER).
@export var spawn_interval: float = 0.8
## Seconds after the wave starts before this group begins.
@export var start_delay: float = 0.0
## Id of an ElementData for this group only. Empty uses the wave's element.
@export var element: StringName
## Which lane of the map this group walks (0 is the map's main path). -1 shares the group out over
## every lane in turn: one enemy at a time, or one pack at a time for PACKS.
@export var lane: int = -1
@export var pattern: Pattern = Pattern.STREAM
## Enemies in each pack (PACKS only).
@export var pack_size: int = 5
## Seconds from the last enemy of a pack to the first of the next (PACKS only).
@export var pack_gap: float = 4.0


## Seconds after start_delay at which each enemy of the group appears, in order. SCATTER uses
## `seed` so the same wave always scatters the same way.
func spawn_times(seed: int = 0) -> PackedFloat32Array:
	var times := PackedFloat32Array()
	var interval := maxf(spawn_interval, 0.0)
	var t := 0.0
	match pattern:
		Pattern.PACKS:
			var size := maxi(pack_size, 1)
			for i in count:
				if i > 0:
					t += pack_gap + interval if i % size == 0 else interval
				times.append(t)
		Pattern.SURGE:
			for i in count:
				if i > 0:
					var share := float(i) / float(maxi(count - 1, 1))
					t += interval * lerpf(2.0, 0.34, share)
				times.append(t)
		Pattern.SCATTER:
			var rng := RandomNumberGenerator.new()
			rng.seed = hash([seed, String(enemy), count])
			for i in count:
				if i > 0:
					t += interval * rng.randf_range(0.25, 1.75)
				times.append(t)
		_:
			for i in count:
				times.append(i * interval)
	return times


## Which pack an enemy belongs to: its index for every pattern but PACKS.
func pack_of(index: int) -> int:
	return index / maxi(pack_size, 1) if pattern == Pattern.PACKS else index


## Seconds from the group's first enemy to its last.
func duration() -> float:
	var times := spawn_times()
	return times[-1] if not times.is_empty() else 0.0
