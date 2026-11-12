class_name ArmyVoice
extends Node
## The army's voice in the counter-attack: squads shout as they march out, units call out when they
## meet the horde, now and then in a fight, at the citadel's gate, when badly hurt and when the
## citadel's spires fire on them; they cry out when they fall; the whole army roars each time the
## citadel loses a quarter of its health and when it falls. Heroes marching as champions speak in
## their own voices.
##
## It keeps it occasional: one line at a time, a few seconds of quiet after each, each kind of line
## resting before it comes back, and the lines of a kind shuffled so they do not repeat. A hero's
## words come first when it has something to say. The speaker raises its weapon for its war cry
## while it speaks (AllyArt.cry) and its words show over its head (BoardView.say).
##
## The lines are in data/army/shouts.json (written by tools/army/shouts.py) and the recordings in
## assets/audio/army/<voice or hero>/<line id>.ogg. A line with no recording still shows its words.
## It only reads the simulation, and draws its chances from its own generator, so a run plays out
## the same with or without it.

const DATA_PATH := "res://data/army/shouts.json"
const AUDIO_DIR := "res://assets/audio/army/"
## Seconds of quiet after a line before the next ordinary one (random in between).
const GAP := Vector2(2.4, 4.8)
## Seconds between lines from a fight, when nothing else was said.
const FIGHT_EVERY := Vector2(4.5, 8.5)
## Seconds a voice rests before it calls out the same kind of thing again.
const KIND_REST := 9.0
## Seconds a hero rests between its own lines.
const CHAMPION_REST := 10.0
## Seconds between two death cries.
const DEATH_REST := 1.4
## A unit calls out once when its health falls below this share.
const HURT_SHARE := 0.33
## Chances that a unit says something when it could.
const MUSTER_CHANCE := 0.85
const CHARGE_CHANCE := 0.45
const SIEGE_CHANCE := 0.4
const HURT_CHANCE := 0.5
const BOLT_CHANCE := 0.25
## Units this close to the speaker raise their weapons with it when the army roars.
const ROAR_RADIUS := 320.0
const VOICE_DB := -2.0
const CRY_DB := -9.0

## A line was spoken (tests listen): the line's id, its kind and who said it.
signal spoke(line_id: String, kind: StringName, ally: SimAlly)

var sim: RunSim
var board: BoardView
## Troop voice -> kind -> lines ({id, text}), and hero id -> kind -> lines.
var lines: Dictionary = {}
var champions: Dictionary = {}
## Unit id -> its voice.
var unit_voice: Dictionary[StringName, StringName] = {}
## Every line spoken this run, oldest first: {id, kind, ally}.
var said: Array[Dictionary] = []

var _rng := RandomNumberGenerator.new()
## Seconds until an ordinary line may start, and until the line being spoken ends.
var _quiet := 0.0
var _busy := 0.0
var _fight_timer := 0.0
var _death_rest := 0.0
## "voice:kind" or hero id -> seconds of rest left.
var _rest: Dictionary[String, float] = {}
var _hurt_said: Dictionary[int, bool] = {}
var _fighting: Dictionary[int, bool] = {}
var _at_gate: Dictionary[int, bool] = {}
## Quarters of the citadel's health already gone (each one roared once).
var _quarters := 0
## Shuffled lines waiting to be said, per "voice:kind".
var _bags: Dictionary[String, Array] = {}
var _streams: Dictionary[String, AudioStream] = {}
var _speech: AudioStreamPlayer2D
var _cries: AudioStreamPlayer2D
var _silent := false


func setup(p_sim: RunSim, p_board: BoardView, seed_value: int = 0) -> void:
	sim = p_sim
	board = p_board
	_rng.seed = seed_value if seed_value != 0 else hash(Time.get_ticks_usec())
	_fight_timer = _rng.randf_range(FIGHT_EVERY.x, FIGHT_EVERY.y)
	_silent = AudioServer.get_driver_name() == "Dummy" or DisplayServer.get_name() == "headless"
	load_lines()
	_speech = _player()
	_cries = _player()
	sim.allies_mustered.connect(_on_allies_mustered)
	sim.ally_attacked.connect(_on_ally_attacked)
	sim.ally_died.connect(_on_ally_died)
	sim.citadel_struck.connect(_on_citadel_struck)
	sim.structure_destroyed.connect(_on_structure_destroyed)


func load_lines() -> void:
	if not FileAccess.file_exists(DATA_PATH):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(DATA_PATH))
	if not parsed is Dictionary:
		return
	lines = parsed.get("lines", {})
	champions = parsed.get("champions", {})
	var voices: Dictionary = parsed.get("voices", {})
	for voice: String in voices:
		for unit: String in voices[voice].get("units", []):
			unit_voice[StringName(unit)] = StringName(voice)


func _player() -> AudioStreamPlayer2D:
	var player := AudioStreamPlayer2D.new()
	player.bus = &"Voice" if AudioServer.get_bus_index(&"Voice") >= 0 else &"Master"
	player.max_distance = 3200.0
	add_child(player)
	return player


## The voice a unit speaks with: its hero for a champion, its troop voice, or empty (the hounds).
func voice_of(ally: SimAlly) -> StringName:
	if ally.is_champion():
		return ally.data.hero if champions.has(String(ally.data.hero)) else &""
	return unit_voice.get(ally.data.id, &"")


## The words of a line as shown: without the [tags] that direct the voice.
static func shown_text(text: String) -> String:
	var out := text.strip_edges()
	while out.begins_with("["):
		var close := out.find("]")
		if close < 0:
			break
		out = out.substr(close + 1).strip_edges()
	return out


func _process(delta: float) -> void:
	if sim == null or not sim.is_counter_assault():
		return
	step(delta)


## Advances the voice by delta seconds: looks for units meeting the horde, hurt badly, in a fight,
## and for the citadel losing a quarter. Tests call it directly.
func step(delta: float) -> void:
	_quiet = maxf(0.0, _quiet - delta)
	_busy = maxf(0.0, _busy - delta)
	_death_rest = maxf(0.0, _death_rest - delta)
	for key in _rest.keys():
		_rest[key] = maxf(0.0, _rest[key] - delta)
	_check_citadel()
	var fighters: Array[SimAlly] = []
	for ally in sim.allies:
		if not ally.alive:
			continue
		if ally.fighting:
			fighters.append(ally)
			if not _fighting.get(ally.id, false):
				_fighting[ally.id] = true
				if ally.target != null and not ally.target.structure and _rng.randf() < CHARGE_CHANCE:
					_try(ally, &"charge")
		else:
			_fighting[ally.id] = false
		if not _hurt_said.has(ally.id) and ally.health < ally.max_health * HURT_SHARE:
			_hurt_said[ally.id] = true
			if _rng.randf() < HURT_CHANCE or ally.is_champion():
				_try(ally, &"hurt", ally.is_champion())
	_fight_timer -= delta
	if _fight_timer <= 0.0:
		_fight_timer = _rng.randf_range(FIGHT_EVERY.x, FIGHT_EVERY.y)
		if not fighters.is_empty():
			# A hero in the fight speaks first now and then; otherwise anyone in it.
			var heroes := fighters.filter(func(a: SimAlly) -> bool: return a.is_champion())
			var pick: SimAlly = heroes[_rng.randi() % heroes.size()] if not heroes.is_empty() and _rng.randf() < 0.4 \
					else fighters[_rng.randi() % fighters.size()]
			_try(pick, &"fight")


func _check_citadel() -> void:
	for structure in sim.structures:
		if not structure.alive or not sim.is_vulnerable(structure):
			continue
		var gone := floori((1.0 - clampf(structure.health / structure.max_health, 0.0, 1.0)) * 4.0)
		if gone > _quarters and gone < 4:
			_quarters = gone
			_roar(&"crack")
		return


func _on_allies_mustered(squad: Array[SimAlly]) -> void:
	if squad.is_empty():
		return
	var speaker := squad[0]
	if speaker.is_champion():
		_try(speaker, &"muster", true)
	elif _rng.randf() < MUSTER_CHANCE:
		if _try(speaker, &"muster"):
			for ally in squad:
				if ally != speaker:
					_cry(ally, _busy)


func _on_ally_attacked(ally: SimAlly, target: SimEnemy) -> void:
	if target == null or not target.structure or _at_gate.has(ally.id):
		return
	_at_gate[ally.id] = true
	if _rng.randf() < SIEGE_CHANCE or ally.is_champion():
		_try(ally, &"siege")


func _on_ally_died(ally: SimAlly) -> void:
	var voice := voice_of(ally)
	if voice.is_empty():
		return
	if ally.is_champion():
		# A hero's last words always come, and wait for nothing.
		var entry := _pick(voice, &"death")
		if not entry.is_empty():
			_play(_speech, String(voice), entry, ally, VOICE_DB)
			_record(entry, &"death", ally)
		return
	if _death_rest > 0.0:
		return
	var cry := _pick(voice, &"death")
	if cry.is_empty():
		return
	_death_rest = DEATH_REST + _rng.randf() * 1.2
	_play(_cries, String(voice), cry, ally, CRY_DB)
	_record(cry, &"death", ally)


func _on_citadel_struck(_structure: SimEnemy, targets: Array[SimAlly]) -> void:
	if targets.is_empty() or _rng.randf() >= BOLT_CHANCE:
		return
	var ally: SimAlly = targets[_rng.randi() % targets.size()]
	if ally.alive and not ally.is_champion():
		_try(ally, &"bolt")


func _on_structure_destroyed(structure: SimEnemy) -> void:
	if sim.is_counter_assault() and sim.citadel_fallen:
		_roar(&"victory")


## The whole army reacts: one voice (a hero first, if the hero has a line for it) and every unit
## near the speaker raises its weapon.
func _roar(kind: StringName) -> void:
	var speakers: Array[SimAlly] = []
	var heroes: Array[SimAlly] = []
	for ally in sim.allies:
		if ally.alive and not voice_of(ally).is_empty():
			speakers.append(ally)
			if ally.is_champion() and champions.get(String(ally.data.hero), {}).has(String(kind)):
				heroes.append(ally)
	if speakers.is_empty():
		return
	var speaker: SimAlly = heroes[_rng.randi() % heroes.size()] if not heroes.is_empty() else speakers[_rng.randi() % speakers.size()]
	if not _try(speaker, kind, true):
		return
	var length := maxf(_busy, 1.0)
	for ally in sim.allies:
		if ally != speaker and ally.alive and ally.position.distance_to(speaker.position) <= ROAR_RADIUS:
			_cry(ally, length * _rng.randf_range(0.7, 1.0))


## Says a line of this kind through the unit if the moment allows: ordinary lines wait for the quiet
## after the last, urgent ones (a hero's arrival, the army's roar) only for the last to end.
func _try(ally: SimAlly, kind: StringName, urgent: bool = false) -> bool:
	var voice := voice_of(ally)
	if voice.is_empty():
		return false
	if _busy > 0.0 or (not urgent and _quiet > 0.0):
		return false
	var rest_key := String(voice) if ally.is_champion() else "%s:%s" % [voice, kind]
	if _rest.get(rest_key, 0.0) > 0.0 and not (urgent and kind != &"fight"):
		return false
	var entry := _pick(voice, kind)
	if entry.is_empty():
		return false
	var length := _play(_speech, String(voice), entry, ally, VOICE_DB)
	_busy = length
	_quiet = length + _rng.randf_range(GAP.x, GAP.y)
	_rest[rest_key] = CHAMPION_REST if ally.is_champion() else KIND_REST
	if board != null:
		board.say(ally, shown_text(String(entry["text"])), length + 0.5)
	_cry(ally, length)
	_record(entry, kind, ally)
	return true


func _cry(ally: SimAlly, seconds: float) -> void:
	if board != null and board.art != null:
		board.art.army.cry(ally, seconds)


func _record(entry: Dictionary, kind: StringName, ally: SimAlly) -> void:
	said.append({"id": String(entry["id"]), "kind": kind, "ally": ally})
	spoke.emit(String(entry["id"]), kind, ally)


## The next line of a kind for a voice, from its shuffled bag. Empty when it has none.
func _pick(voice: StringName, kind: StringName) -> Dictionary:
	var table: Dictionary = champions.get(String(voice), {}) if champions.has(String(voice)) else lines.get(String(voice), {})
	var options: Array = table.get(String(kind), [])
	if options.is_empty():
		return {}
	var key := "%s:%s" % [voice, kind]
	var bag: Array = _bags.get(key, [])
	if bag.is_empty():
		bag = options.duplicate()
		for i in range(bag.size() - 1, 0, -1):
			var j := _rng.randi_range(0, i)
			var held: Variant = bag[i]
			bag[i] = bag[j]
			bag[j] = held
		_bags[key] = bag
	return bag.pop_back()


## Plays a line where the unit stands and returns how long it lasts (a guess from its words when it
## has no recording yet).
func _play(player: AudioStreamPlayer2D, folder: String, entry: Dictionary, ally: SimAlly, volume_db: float) -> float:
	var stream := _stream(folder, String(entry["id"]))
	if stream == null:
		return 0.9 + 0.055 * shown_text(String(entry["text"])).length()
	if not _silent:
		player.stream = stream
		player.volume_db = volume_db
		var at := board.art.army.anchor(ally) if board != null and board.art != null else ally.position
		player.global_position = board.to_global(at) if board != null else at
		player.play()
	return stream.get_length()


func _stream(folder: String, line_id: String) -> AudioStream:
	var path := AUDIO_DIR + "%s/%s.ogg" % [folder, line_id]
	if _streams.has(path):
		return _streams[path]
	var stream: AudioStream = load(path) if ResourceLoader.exists(path) else null
	_streams[path] = stream
	return stream


## Seconds left of the line being spoken.
func busy() -> float:
	return _busy
