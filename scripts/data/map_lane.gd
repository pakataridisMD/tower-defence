class_name MapLane
extends Resource
## An extra road on a map with more than one entrance. Same rules as MapData.waypoints and MapData.curve.

@export var waypoints: Array[Vector2i] = []
## The road's centre line in cells, as in MapData.curve. Empty means straight lines between waypoints.
@export var curve: PackedVector2Array = []
