class_name BossDirector
extends Node
## Makes the bosses act: picks which of their moves (BoardArt.BOSS_MOVES) the board shows and which
## line BossVoice says, from what the simulation reports. It only reads the simulation.
##
## A boss rises out of the dark when it first appears and speaks; strikes or slams the ground every
## few seconds while it taunts; raises its hands to heal, bind or silence; holds a guard while its
## barrier stands; roars in rage or over a burnt tower; reels at each quarter of its life lost; and
## rises again in a new form. RunSim.boss_ability (from the boss-abilities work) is used when it exists.

## Seconds of wave time between a boss's strikes, when it has nothing else to do (random in between).
const STRIKE_EVERY := Vector2(8.0, 13.0)
## Seconds after it first appears that it speaks (its rise plays first).
const FIRST_WORDS := 1.2
## It reels each time its health falls past one of these shares; at the middle one it also speaks.
const HURT_AT: Array[float] = [0.75, 0.5, 0.25]
## How long a guard is held if the barrier is never seen to break.
const GUARD_HOLD := 2.5
## How long the talking jaw keeps going after the line, at most.
const TALK_TAIL := 0.15

## Ability (RunSim.boss_ability) -> [move, line kind]. An empty kind says nothing.
const ABILITY := {
	&"heal": [&"cast", &"heal"],
	&"shield": [&"guard", &"shield"],
	&"shield_break": [&"hurt", &"hurt"],
	&"bind": [&"cast", &"bind"],
	&"silence": [&"cast", &"bind"],
	&"fireball": [&"attack", &"fireball"],
	&"destroy_tower": [&"roar", &"destroy"],
	&"summon": [&"slam", &"summon"],
	&"blink": [&"rise", &""],
	&"enrage": [&"roar", &"enrage"],
}

var sim: RunSim
var art: BoardArt
var voice: BossVoice

## Enemy id -> {strike, hurt (index into HURT_AT), guard (seconds left), pending: [move, kind, delay]}.
var _bosses: Dictionary[int, Dictionary] = {}
var _max_enemy_id := -1
var _sim_time := 0.0
## Moves and lines asked for before the board had drawn the boss: [enemy id, move, kind, wave time].
var _waiting: Array[Array] = []


func setup(p_sim: RunSim, p_art: BoardArt) -> void:
	sim = p_sim
	art = p_art
	voice = BossVoice.new()
	add_child(voice)
	voice.spoke.connect(_on_spoke)
	sim.wave_started.connect(func(_n: int) -> void: _sim_time = 0.0)
	sim.enemy_killed.connect(_on_enemy_killed)
	for signal_name: StringName in [&"boss_ability", &"towers_silenced", &"enemy_blinked", &"enemy_transformed",
			&"boss_fled", &"enemy_escaped"]:
		if sim.has_signal(signal_name):
			sim.connect(signal_name, Callable(self, "_on_" + signal_name))


static func is_boss(enemy: SimEnemy) -> bool:
	return enemy.data.tags.has(&"boss") and enemy.get(&"structure") != true


func _process(_delta: float) -> void:
	if sim == null or sim.state != RunSim.State.WAVE:
		return
	var step := sim.time_in_wave - _sim_time
	_sim_time = sim.time_in_wave
	if step <= 0.0:
		return
	_find_new_bosses()
	_tick(step)
	_retry_waiting()


func _find_new_bosses() -> void:
	var enemies := sim.enemies
	var newest := _max_enemy_id
	for i in range(enemies.size() - 1, -1, -1):
		var enemy := enemies[i]
		if enemy.id <= _max_enemy_id:
			break
		newest = maxi(newest, enemy.id)
		if enemy.alive and is_boss(enemy):
			_meet(enemy, &"arrive")
	_max_enemy_id = newest


## A boss first seen (or seen in a new form): it rises, then speaks.
func _meet(enemy: SimEnemy, kind: StringName) -> void:
	_bosses[enemy.id] = {"strike": randf_range(STRIKE_EVERY.x, STRIKE_EVERY.y), "hurt": _hurt_index(enemy),
		"guard": 0.0, "slam": randf() < 0.5}
	act(enemy, &"rise", &"")
	if not kind.is_empty():
		_waiting.append([enemy.id, &"", kind, _sim_time + FIRST_WORDS])


func _hurt_index(enemy: SimEnemy) -> int:
	var share := enemy.health / maxf(1.0, enemy.max_health)
	var index := 0
	while index < HURT_AT.size() and share < HURT_AT[index]:
		index += 1
	return index


func _tick(step: float) -> void:
	for id: int in _bosses.keys():
		var enemy := _enemy(id)
		if enemy == null or not enemy.alive:
			_bosses.erase(id)
			continue
		var state: Dictionary = _bosses[id]
		if state["guard"] > 0.0:
			state["guard"] -= step
			if state["guard"] <= 0.0 and art != null:
				art.release_boss_move(enemy, &"guard")
		var index: int = state["hurt"]
		if index < HURT_AT.size() and enemy.health < enemy.max_health * HURT_AT[index]:
			state["hurt"] = index + 1
			act(enemy, &"hurt", &"hurt" if HURT_AT[index] == 0.5 else &"")
			continue
		state["strike"] -= step
		if state["strike"] <= 0.0 and not _busy(enemy):
			state["strike"] = randf_range(STRIKE_EVERY.x, STRIKE_EVERY.y)
			# It strikes and slams in turn, taunting as it does.
			state["slam"] = not state["slam"]
			act(enemy, &"slam" if state["slam"] and _has_move(enemy, &"slam") else &"attack", &"taunt")


func _busy(enemy: SimEnemy) -> bool:
	return art != null and not art.boss_move_of(enemy).is_empty()


func _has_move(enemy: SimEnemy, move: StringName) -> bool:
	return BoardArt.has_boss_move(enemy.data.id, move)


## Plays a move and says a line of that kind (either may be empty). If the board has not drawn the
## boss yet, both wait a moment for it.
func act(enemy: SimEnemy, move: StringName, kind: StringName, hold := false) -> void:
	if not move.is_empty() and art != null and _has_move(enemy, move):
		if art.play_boss_move(enemy, move, hold) <= 0.0:
			_waiting.append([enemy.id, move, kind, _sim_time + 0.05])
			return
	if not kind.is_empty() and voice != null:
		voice.say(enemy.data.id, kind)


func _retry_waiting() -> void:
	var still: Array[Array] = []
	for item in _waiting:
		if item[3] > _sim_time:
			still.append(item)
			continue
		var enemy := _enemy(item[0])
		if enemy == null or not enemy.alive:
			continue
		if not (item[1] as StringName).is_empty() and art != null and _has_move(enemy, item[1]) \
				and art.play_boss_move(enemy, item[1]) <= 0.0:
			# Still not on the board: give it up after a second.
			if _sim_time - item[3] < 1.0:
				still.append(item)
			continue
		if not (item[2] as StringName).is_empty():
			voice.say(enemy.data.id, item[2])
	_waiting = still


func _on_spoke(boss_id: StringName, _kind: StringName, _text: String, seconds: float) -> void:
	if art == null:
		return
	for enemy in sim.enemies:
		if enemy.alive and enemy.data.id == boss_id:
			art.set_boss_talking(enemy, seconds + TALK_TAIL)
			return


func _enemy(id: int) -> SimEnemy:
	for enemy in sim.enemies:
		if enemy.id == id:
			return enemy
	return null


# --- What the simulation reports ----------------------------------------------------------------

func _on_boss_ability(boss: SimEnemy, ability: StringName, _targets: Array) -> void:
	var plan: Array = ABILITY.get(ability, [&"cast", &""])
	if not _bosses.has(boss.id) and boss.alive:
		_bosses[boss.id] = {"strike": STRIKE_EVERY.x, "hurt": _hurt_index(boss), "guard": 0.0, "slam": false}
	if ability == &"shield":
		act(boss, &"guard", &"shield", true)
		if _bosses.has(boss.id):
			_bosses[boss.id]["guard"] = GUARD_HOLD
		return
	if ability == &"shield_break" and art != null:
		art.release_boss_move(boss, &"guard")
	act(boss, plan[0], plan[1])
	if _bosses.has(boss.id):
		# It just did something: its next strike can wait.
		_bosses[boss.id]["strike"] = maxf(_bosses[boss.id]["strike"], STRIKE_EVERY.x * 0.5)


func _on_towers_silenced(boss: SimEnemy, _silenced: Array) -> void:
	# boss_ability reports silences itself where it exists.
	if not sim.has_signal(&"boss_ability"):
		act(boss, &"cast", &"bind")


func _on_enemy_blinked(enemy: SimEnemy, _from: Vector2) -> void:
	if is_boss(enemy) and not sim.has_signal(&"boss_ability"):
		act(enemy, &"rise", &"")


## A new form: the old one's last words, then the new one rises and speaks.
func _on_enemy_transformed(enemy: SimEnemy, from: EnemyData) -> void:
	if not is_boss(enemy):
		return
	voice.say(from.id, &"transform")
	_meet(enemy, &"arrive")
	# Its arrival line comes after the old form's last words.
	_waiting.back()[3] = _sim_time + 3.0


func _on_boss_fled(enemy: SimEnemy) -> void:
	_bosses.erase(enemy.id)
	voice.say(enemy.data.id, &"flee")


func _on_enemy_escaped(enemy: SimEnemy) -> void:
	if is_boss(enemy):
		_bosses.erase(enemy.id)
		voice.say(enemy.data.id, &"flee")


func _on_enemy_killed(enemy: SimEnemy, _killer: SimTower, _bounty: int) -> void:
	if is_boss(enemy):
		_bosses.erase(enemy.id)
		voice.say(enemy.data.id, &"death")
