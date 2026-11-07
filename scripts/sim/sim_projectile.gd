class_name SimProjectile
extends RefCounted
## A shot in flight. It follows its target; if the target dies first it flies on to the last
## point it aimed at, where a splash shot still explodes and a single-target shot misses.

var position: Vector2
var target: SimEnemy
var target_point: Vector2
var speed := 700.0
var source: SimTower
var damage := 0.0
var splash_radius := 0.0
var done := false
