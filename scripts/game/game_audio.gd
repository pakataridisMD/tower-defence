class_name GameAudio
extends Node
## The sound of a run. Listens to the simulation and plays what happens on the board through the
## Sfx autoload: tower attacks and hits, deaths, the base being hit, waves, skills, building and
## upgrading, and everything a boss does (its reveal, footsteps, speech, rage and death).
##
## It only reads the simulation, so the simulation stays the same with or without sound. Boss
## events from the story branch (boss_arrived, towers_silenced, enemy_blinked, enemy_escaped,
## structure_destroyed, phase_changed) are used when RunSim has them.

## Share of the starting lives at which the "base nearly lost" warning sounds, once per run.
const LIVES_WARNING_SHARE := 0.25
## Most tower attack sounds and hit sounds started per second; a big board would be a wall of noise.
const ATTACKS_PER_SECOND := 14.0
const HITS_PER_SECOND := 12.0
## Enemies this armoured clank when shot.
const ARMOUR_CLANK := 8.0
## A boss says something every this many seconds of wave time (random in between).
const TALK_EVERY := Vector2(13.0, 21.0)
## Seconds after its reveal that a boss first speaks (the reveal already carries a spoken line).
const FIRST_WORDS := 8.5
## Below this share of its health a boss roars (if the simulation has no enrage of its own).
const WOUNDED_SHARE := 0.35
## Bosses that are part of a bigger one and get no reveal or footsteps of their own.
const MINOR_BOSSES: Array[StringName] = [&"hollow_shade"]
const STAR_DELAY := 1.3
const STAR_STEP := 0.45

var sim: RunSim
## Where the board sits on screen: simulation positions are board pixels.
var board_offset := Vector2.ZERO

var _towers: Dictionary[int, Array] = {}
var _tree_nodes := 0
var _max_enemy_id := -1
## Enemy id -> {set, step, talk, wounded, summon}.
var _bosses: Dictionary[int, Dictionary] = {}
var _revealed: Dictionary[StringName, bool] = {}
var _skill_waiting: Dictionary[StringName, bool] = {}
var _warned_lives := false
var _sim_time := 0.0
var _attack_budget := ATTACKS_PER_SECOND
var _hit_budget := HITS_PER_SECOND
## Sounds waiting for their moment: [wave time, name, enemy id or -1].
var _queue: Array[Array] = []


func setup(p_sim: RunSim, p_board_offset: Vector2) -> void:
	sim = p_sim
	board_offset = p_board_offset
	sim.wave_started.connect(_on_wave_started)
	sim.wave_cleared.connect(_on_wave_cleared)
	sim.enemy_killed.connect(_on_enemy_killed)
	sim.enemy_leaked.connect(_on_enemy_leaked)
	sim.chain_fired.connect(_on_chain_fired)
	sim.projectile_landed.connect(_on_projectile_landed)
	sim.run_ended.connect(_on_run_ended)
	sim.skill_used.connect(_on_skill_used)
	sim.tower_attacked.connect(_on_tower_attacked)
	sim.changed.connect(_on_changed)
	sim.tree.changed.connect(_on_tree_changed)
	for signal_name: StringName in [&"boss_arrived", &"towers_silenced", &"enemy_blinked", &"enemy_escaped",
			&"structure_destroyed", &"phase_changed"]:
		if sim.has_signal(signal_name):
			sim.connect(signal_name, Callable(self, "_on_" + signal_name))
	_snapshot_towers()
	_tree_nodes = sim.tree.allocated_ids().size()


func play(sound: StringName, at: Variant = null, volume_db: float = 0.0) -> bool:
	if at is Vector2:
		at = (at as Vector2) + board_offset
	return SoundPlayer.sfx(sound, at, volume_db)


## Stars after a campaign stage, one chime each, after the victory fanfare has started.
func play_stars(count: int) -> void:
	for i in clampi(count, 0, 3):
		get_tree().create_timer(STAR_DELAY + i * STAR_STEP).timeout.connect(
			func() -> void: SoundPlayer.sfx(StringName("star_%d" % (i + 1))))


## The boss sound set an enemy uses, or empty if it is not a boss.
static func boss_set_of(data: EnemyData) -> StringName:
	var player := SoundPlayer.instance
	if player != null and player.boss_sets.has(data.id):
		return player.boss_sets[data.id]
	if data.tags.has(&"boss") and not MINOR_BOSSES.has(data.id) and not data.element.is_empty():
		return data.element
	return &""


## The death sound of an ordinary enemy.
static func death_sound_of(data: EnemyData) -> StringName:
	var player := SoundPlayer.instance
	if player != null and player.enemy_deaths.has(data.id):
		return player.enemy_deaths[data.id]
	if data.tags.has(&"fast"):
		return &"death_runner"
	if data.tags.has(&"armoured") or data.armour >= ARMOUR_CLANK:
		return &"death_brute"
	return &"death_grunt"


func _process(delta: float) -> void:
	if sim == null:
		return
	_attack_budget = minf(ATTACKS_PER_SECOND * 0.5, _attack_budget + ATTACKS_PER_SECOND * delta)
	_hit_budget = minf(HITS_PER_SECOND * 0.5, _hit_budget + HITS_PER_SECOND * delta)
	if sim.state != RunSim.State.WAVE:
		return
	# Wave time moves with the game speed and stops when the game is paused.
	var step := sim.time_in_wave - _sim_time
	_sim_time = sim.time_in_wave
	if step <= 0.0:
		return
	_find_new_bosses()
	_tick_bosses(step)
	_tick_queue()
	_tick_skills()


# --- Waves and the base ----------------------------------------------------------------

func _on_wave_started(number: int) -> void:
	_sim_time = 0.0
	_queue.clear()
	var wave := sim.current_wave()
	if number >= sim.total_waves():
		play(&"wave_start_final")
	elif wave != null and wave.is_boss:
		# The battle music plays its own boss entrance; two stingers at once would be mush.
		if not _has_battle_music():
			play(&"wave_start_boss")
	else:
		play(&"wave_start")


static func _has_battle_music() -> bool:
	for entry: Dictionary in ProjectSettings.get_global_class_list():
		if entry.get("class", &"") == &"BattleMusic":
			return true
	return false


func _on_wave_cleared(_number: int, _points: int, gold: int) -> void:
	if sim.is_over():
		return
	play(&"wave_cleared")
	if gold > 0:
		get_tree().create_timer(0.6).timeout.connect(func() -> void: play(&"gold_bonus"))


func _on_enemy_leaked(enemy: SimEnemy) -> void:
	if not _bosses.is_empty() and _bosses.has(enemy.id):
		_bosses.erase(enemy.id)
		play(&"base_hit_boss")
	else:
		play(&"base_hit")
	if not _warned_lives and sim.lives > 0 and sim.lives <= ceili(sim.starting_lives * LIVES_WARNING_SHARE):
		_warned_lives = true
		get_tree().create_timer(0.5).timeout.connect(func() -> void: play(&"lives_low"))


func _on_run_ended(won: bool) -> void:
	_queue.clear()
	play(&"victory" if won else &"defeat")


const HERO_ATTACK_SOUNDS: Dictionary[StringName, StringName] = {
	&"fire": &"tower_fire_brazier", &"storm": &"tower_storm_spire", &"nature": &"tower_nature_thornbush",
	&"water": &"tower_water_wellspring", &"earth": &"tower_earth_monolith", &"void": &"tower_void_obelisk",
}


# --- Combat ------------------------------------------------------------------------------

func _on_tower_attacked(tower: SimTower, _target: SimEnemy) -> void:
	if _attack_budget < 1.0:
		return
	if play(_attack_sound(tower), tower.position):
		_attack_budget -= 1.0


## A tower's attack sound. A hero borrows the sound of its element's base tower.
func _attack_sound(tower: SimTower) -> StringName:
	if not tower.is_hero():
		return StringName("tower_" + tower.data.id)
	return HERO_ATTACK_SOUNDS.get(tower.hero.element, &"tower_triple_starfall")


func _on_projectile_landed(shot: SimProjectile) -> void:
	if shot.source == null or _hit_budget < 1.0:
		return
	var sound: StringName
	if shot.splash_radius > 0.0:
		sound = &"explosion_small" if shot.splash_radius <= 60.0 else (&"explosion_medium" if shot.splash_radius <= 80.0 else &"explosion_large")
	else:
		sound = _impact_of(shot.source)
	if play(sound, shot.position):
		_hit_budget -= 1.0
	var target := shot.target
	if target != null and target.alive:
		if target.armour >= ARMOUR_CLANK:
			play(&"hit_armour", shot.position)
		if not shot.source.effects.is_empty() and not target.data.status_immune:
			play(StringName("status_" + _status_word(shot.source.effects[0].kind)), shot.position)


func _on_chain_fired(tower: SimTower, points: PackedVector2Array) -> void:
	if points.size() >= 2 and _hit_budget >= 1.0:
		if play(&"impact_storm", points[points.size() - 1], -3.0):
			_hit_budget -= 1.0


func _on_enemy_killed(enemy: SimEnemy, _killer: SimTower, bounty: int) -> void:
	if _bosses.has(enemy.id):
		var set_name: StringName = _bosses[enemy.id]["set"]
		_bosses.erase(enemy.id)
		play(StringName("boss_%s_death" % set_name), enemy.position)
	else:
		play(death_sound_of(enemy.data), enemy.position)
	if enemy.data.split_count > 0 and not enemy.data.split_into.is_empty():
		play(&"enemy_split", enemy.position)
	if bounty > 0:
		play(&"coin", enemy.position)


func _on_skill_used(skill: SkillData, at: Vector2) -> void:
	play(StringName("skill_" + skill.id), at)
	_skill_waiting[skill.id] = true


func _impact_of(tower: SimTower) -> StringName:
	var elements := tower.data.elements
	return StringName("impact_" + (elements[0] if not elements.is_empty() else "earth"))


static func _status_word(kind: StringName) -> String:
	match kind:
		&"slow":
			return "freeze"
		_:
			return str(kind)


# --- Building, upgrades and the skill web ---------------------------------------------------

func _snapshot_towers() -> void:
	_towers.clear()
	for tower in sim.towers:
		_towers[tower.id] = _tower_state(tower)


static func _tower_state(tower: SimTower) -> Array:
	return [tower.data.id, tower.level, tower.ascendancy.id if tower.ascendancy != null else &""]


func _on_changed() -> void:
	if sim.is_over():
		return
	var seen: Dictionary[int, bool] = {}
	for tower in sim.towers:
		seen[tower.id] = true
		var now := _tower_state(tower)
		if not _towers.has(tower.id):
			var element: String = tower.data.elements[0] if not tower.data.elements.is_empty() else "earth"
			play(StringName("tower_place_" + element), tower.position)
		else:
			var before: Array = _towers[tower.id]
			if now[0] != before[0]:
				play(&"tower_hybrid", tower.position)
			elif now[2] != before[2]:
				play(&"tower_ascend", tower.position)
			elif now[1] > before[1]:
				play(&"tower_level_up", tower.position)
		_towers[tower.id] = now
	for id: int in _towers.keys():
		if not seen.has(id):
			_towers.erase(id)
			play(&"tower_sell")


func _on_tree_changed() -> void:
	var count := sim.tree.allocated_ids().size()
	if count > _tree_nodes:
		SoundPlayer.sfx(&"node_take")
	elif count < _tree_nodes:
		SoundPlayer.sfx(&"node_refund")
	_tree_nodes = count


func _tick_skills() -> void:
	for skill_id: StringName in _skill_waiting.keys():
		if sim.skill_cooldown_left(skill_id) <= 0.0:
			_skill_waiting.erase(skill_id)
			SoundPlayer.sfx(&"skill_ready")


# --- Bosses ----------------------------------------------------------------------------------

## New enemies are always added at the end of the list with a higher id, so only the tail is read.
func _find_new_bosses() -> void:
	var enemies := sim.enemies
	var newest := _max_enemy_id
	for i in range(enemies.size() - 1, -1, -1):
		var enemy := enemies[i]
		if enemy.id <= _max_enemy_id:
			break
		newest = maxi(newest, enemy.id)
		_track_boss(enemy)
	_max_enemy_id = newest


func _on_boss_arrived(enemy: SimEnemy) -> void:
	_track_boss(enemy)


func _track_boss(enemy: SimEnemy) -> void:
	if _bosses.has(enemy.id) or not enemy.alive or enemy.get(&"structure") == true:
		return
	var set_name := boss_set_of(enemy.data)
	if set_name.is_empty():
		return
	_bosses[enemy.id] = {"set": set_name, "step": 0.6, "talk": randf_range(TALK_EVERY.x, TALK_EVERY.y),
		"wounded": false, "summon": enemy.summon_timer}
	if not _revealed.has(enemy.data.id):
		_revealed[enemy.data.id] = true
		play(StringName("boss_%s_reveal" % set_name), enemy.position)
		_queue.append([_sim_time + FIRST_WORDS, StringName("boss_%s_voice" % set_name), enemy.id])


func _tick_bosses(step: float) -> void:
	for id: int in _bosses.keys():
		var enemy := _enemy(id)
		if enemy == null or not enemy.alive:
			_bosses.erase(id)
			continue
		var state: Dictionary = _bosses[id]
		var set_name: StringName = state["set"]
		var speed := enemy.speed()
		if speed > 0.0:
			state["step"] -= step
			if state["step"] <= 0.0:
				state["step"] = clampf(30.0 / speed, 0.45, 1.3)
				play(StringName("boss_%s_step" % set_name), enemy.position)
		state["talk"] -= step
		if state["talk"] <= 0.0:
			state["talk"] = randf_range(TALK_EVERY.x, TALK_EVERY.y)
			play(StringName("boss_%s_voice" % set_name), enemy.position)
		var enraged: Variant = enemy.get(&"enraged")
		var wounded: bool = enraged if enraged is bool else enemy.health < enemy.max_health * WOUNDED_SHARE
		if wounded and not state["wounded"]:
			state["wounded"] = true
			play(StringName("boss_%s_enrage" % set_name), enemy.position)
		if enemy.summon_timer > state["summon"] + 0.5:
			play(&"enemy_summon", enemy.position)
		state["summon"] = enemy.summon_timer


func _tick_queue() -> void:
	var waiting: Array[Array] = []
	for item in _queue:
		if item[0] > _sim_time:
			waiting.append(item)
			continue
		var enemy: SimEnemy = _enemy(item[2]) if item[2] >= 0 else null
		if item[2] < 0 or (enemy != null and enemy.alive):
			play(item[1], enemy.position if enemy != null else null)
	_queue = waiting


func _enemy(id: int) -> SimEnemy:
	for enemy in sim.enemies:
		if enemy.id == id:
			return enemy
	return null


# --- Story branch boss tricks (used when RunSim has these signals) -------------------------------

func _on_towers_silenced(boss: SimEnemy, _silenced: Array) -> void:
	play(&"boss_silence", boss.position)


func _on_enemy_blinked(enemy: SimEnemy, _from: Vector2) -> void:
	play(&"boss_blink", enemy.position)


func _on_enemy_escaped(enemy: SimEnemy) -> void:
	_bosses.erase(enemy.id)
	play(&"boss_escape")


func _on_structure_destroyed(structure: SimEnemy) -> void:
	play(&"structure_collapse", structure.position)


func _on_phase_changed(_phase: int) -> void:
	play(&"assault_phase")
