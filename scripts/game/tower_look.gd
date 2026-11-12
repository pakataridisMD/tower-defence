class_name TowerLook
extends RefCounted
## How a tower's animation sheet is read (see tools/art/pix2d/tower_anim.py): one row per look, the
## three levels then each ascendancy, and across each row its idle frames then its attack frames.
##
## A level is a minor upgrade and adds pieces to the same building (a collar, ward lanterns, banners);
## an ascendancy is a major one and remakes it (raised on a dais, Exalted in gold or Dread in black iron).


const INDEX := "res://assets/art/game/towers/anim/anim.json"

static var _index: Dictionary = {}


## The tower's sheet: where it is, its cell and anchor, its looks and its frame counts. Empty if it has none.
static func sheet_info(tower_id: StringName) -> Dictionary:
	if _index.is_empty() and FileAccess.file_exists(INDEX):
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(INDEX))
		if parsed is Dictionary:
			_index = parsed
	return _index.get(String(tower_id), {})


## True when the tower has a sheet BoardArt can play.
static func has_sheet(anim: Dictionary) -> bool:
	return anim.has("sheet") and anim.has("cell") and anim.has("anchor") and anim.has("stages") \
			and ResourceLoader.exists(BoardArt.ART + String(anim["sheet"]) + ".png")


## The look a tower shows: 0-2 for levels 1-3, then 3 + the index of the ascendancy it took.
static func stage_index(tower: SimTower, stage_count := 5) -> int:
	var stage := clampi(tower.level - 1, 0, 2)
	if tower.ascendancy != null:
		var index := maxi(0, tower.data.ascendancies.find(tower.ascendancy))
		stage = 3 + index
	return clampi(stage, 0, stage_count - 1)


static func columns(anim: Dictionary) -> int:
	return int(anim.get("idle", 1)) + int(anim.get("attack", 0))


## How far an ascended tower's crown is raised by its dais, in art pixels.
static func lift(anim: Dictionary, stage: int) -> float:
	var lifts: Array = anim.get("lift", [])
	return float(lifts[stage]) if stage < lifts.size() else 0.0


static func attack_length(anim: Dictionary) -> float:
	return float(anim.get("attack", 0)) / maxf(1.0, float(anim.get("attack_fps", 12)))


## The sheet frame for this moment: the idle loop, or the attack while attack_time is 0 or more.
static func frame(anim: Dictionary, stage: int, idle_time: float, attack_time: float) -> int:
	var idle := int(anim.get("idle", 1))
	var attack := int(anim.get("attack", 0))
	var column := int(idle_time * float(anim.get("idle_fps", 8))) % maxi(1, idle)
	if attack_time >= 0.0 and attack > 0:
		column = idle + mini(attack - 1, int(attack_time * float(anim.get("attack_fps", 12))))
	return stage * columns(anim) + column


## 0..1: how hard the tower kicks back on its strike (peaks on the release frame, then eases off).
static func recoil(anim: Dictionary, attack_time: float) -> float:
	if attack_time < 0.0:
		return 0.0
	var fps := float(anim.get("attack_fps", 12))
	var peak := (float(anim.get("attack_peak", 2)) + 0.5) / fps
	if attack_time < peak:
		return -0.4 * attack_time / peak
	return maxf(0.0, 1.0 - (attack_time - peak) / (attack_length(anim) - peak + 0.001))
