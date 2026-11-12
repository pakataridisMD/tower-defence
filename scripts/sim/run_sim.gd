class_name RunSim
extends RefCounted
## The rules of one run with no rendering. The game scene draws this state every frame,
## and tests drive it directly with step().

signal changed
signal wave_started(wave_number: int)
signal wave_cleared(wave_number: int, tree_points: int, gold: int)
signal enemy_killed(enemy: SimEnemy, killer: SimTower, bounty: int)
signal enemy_leaked(enemy: SimEnemy)
signal chain_fired(tower: SimTower, points: PackedVector2Array)
## A tower fired: a shot left it, or its chain jumped. Used for sound.
signal tower_attacked(tower: SimTower, target: SimEnemy)
signal projectile_landed(projectile: SimProjectile)
signal run_ended(won: bool)
## A skill was cast. `at` is the point picked on the board, or the board's centre for a skill
## that reaches everything.
signal skill_used(skill: SkillData, at: Vector2)
## A skill set off: the cast holds every blow still to land, so the board can draw what is coming.
signal skill_cast(cast: SimSkillCast)
## One blow of a cast landed (a strike, a stretch of a sweep, a bolt or a field closing) on `hit`.
signal skill_struck(cast: SimSkillCast, blow: SimSkillCast.Blow, hit: Array[SimEnemy])
## A skill was taken to a new level with gold.
signal skill_upgraded(skill: SkillData, level: int)
## A boss came onto the board, walking in or released by another enemy.
signal boss_arrived(enemy: SimEnemy)
## A boss silenced these towers.
signal towers_silenced(boss: SimEnemy, silenced: Array[SimTower])
## An enemy used its power (see EnemyData.power), or something happened to it: &"fall" and &"rise"
## for a grunt that falls and stands again, &"shield" when a shield comes up and &"block" when it
## stops a hit. `targets` holds the allies it healed or drove on, or the tower it burned or blocked.
signal enemy_power(enemy: SimEnemy, power: StringName, targets: Array)
## An enemy jumped forward along its road, from one point to another.
signal enemy_blinked(enemy: SimEnemy, from: Vector2)
## A boss escaped the board when badly hurt (see EnemyData.escape_below).
signal enemy_escaped(enemy: SimEnemy)
## A building of the enemy base fell in an assault.
signal structure_destroyed(structure: SimEnemy)
## Every building of an assault phase fell. `phase` is the new phase; above the stage's last phase
## once the whole base is down.
signal phase_changed(phase: int)
## A hero was placed on the board, or marched to a new cell.
signal hero_summoned(tower: SimTower)
signal hero_moved(tower: SimTower)
## A hero used its ability. `points` are where it landed: the point picked, the hero, the crowds hit
## or, for one that reaches every enemy, the board's centre.
signal hero_ability_used(tower: SimTower, ability: HeroAbility, points: PackedVector2Array)
## A hero joined the party during the run (Oswin at the capital).
signal hero_arrived(hero: HeroData)
signal hero_leveled(tower: SimTower)
## A boss changed into its next form (see EnemyData.next_form). `from` is the form it was.
signal enemy_transformed(enemy: SimEnemy, from: EnemyData)
## A boss that flees when beaten turned back toward its citadel.
signal boss_fled(enemy: SimEnemy)
## The final assault turned: from now on the player musters units against the citadel.
signal counter_attack_started
## Units marched out of our camp.
signal allies_mustered(allies: Array[SimAlly])
## A unit struck an enemy or a building.
signal ally_attacked(ally: SimAlly, target: SimEnemy)
## A unit healed these units.
signal ally_healed(ally: SimAlly, healed: Array[SimAlly])
signal ally_died(ally: SimAlly)
## A building's defences struck these units.
signal citadel_struck(structure: SimEnemy, targets: Array[SimAlly])

enum State { BUILDING, WAVE, WON, LOST }

## Simulation step used by the game scene. Tests may use bigger steps.
const STEP := 1.0 / 60.0
## In an assault, every this many attacks a tower in reach of a building it can hurt shoots the
## building, even with enemies in range, so the siege moves on during a crowded wave.
const SIEGE_EVERY := 3
## How far a dying enemy's poison can jump.
const POISON_SPREAD_RANGE := 160.0
## A unit holding the road stops an enemy this many pixels in front of it.
const CONTACT := 26.0
## Enemies one unit can hold back at once; a champion holds more.
const HOLD_COUNT := 2
const CHAMPION_HOLD_COUNT := 5
## A unit can strike a building from this many pixels further than its reach, as buildings are big.
const BUILDING_REACH := 150.0
## A unit this many pixels from the start of its road (a gate of the citadel), plus its reach,
## strikes the citadel.
const GATE_REACH := 30.0
## A beaten boss flees this many times as fast as it walked.
const FLEE_SPEED := 3.0
## In the counter-attack the horde keeps coming: the wave starts again this many seconds after its
## last enemy marched out, a little stronger each time.
const COUNTER_LOOP_GAP := 4.0
const COUNTER_LOOP_GROWTH := 0.06
## A blow at least does this share of its damage, whatever the armour.
const ALLY_MIN_DAMAGE := 0.2

var config: RunConfig
var state := State.BUILDING
var gold := 0
var lives := 0
## Lives at the start of the run, for the campaign's stars.
var starting_lives := 0
## Waves cleared so far. The next wave to start is wave_index + 1.
var wave_index := 0
var tree: TreeState
var enemies: Array[SimEnemy] = []
var towers: Array[SimTower] = []
var projectiles: Array[SimProjectile] = []
## The main road (lane 0). Maps with several entrances have one curve per lane in lane_curves.
var path_curve := Curve2D.new()
var path_length := 0.0
var lane_curves: Array[Curve2D] = []
var lane_lengths: PackedFloat32Array = []
var time_in_wave := 0.0
## Buildings of the enemy base in an assault, standing or fallen. Empty in any other run.
var structures: Array[SimEnemy] = []
## The assault phase being fought, from 1. Buildings of later phases cannot be hurt yet.
var structure_phase := 1
## True once every building of the enemy base has fallen.
var citadel_fallen := false
## Seconds until the next wave starts on its own, or below 0 when nothing is counting down.
var break_time_left := -1.0

var kills := 0
var leaks := 0
var gold_earned := 0

var _path_cells: Dictionary[Vector2i, bool] = {}
var _tower_at: Dictionary[Vector2i, SimTower] = {}
var _spawner := WaveSpawner.new()
var _hash := SpatialHash.new(128.0)
var _next_id := 1
var _taken_this_break: Dictionary[StringName, bool] = {}
var _modifiers: Array[Modifier] = []
var _wave_element := -1
## Enemies split off or summoned during a step, added once the step's loops are done.
var _arrivals: Array[SimEnemy] = []
## Seconds of wave time until each skill can be used again, by skill id.
var _skill_cooldowns: Dictionary[StringName, float] = {}
## Seconds left on each skill whose modifiers are still running, by skill id.
var _skill_time: Dictionary[StringName, float] = {}
## The modifiers a running boon lends, scaled to the level it was cast at, by skill id.
var _skill_mods: Dictionary[StringName, Array] = {}
## Each skill's level in this run, by skill id (1 when it has not been raised).
var skill_levels: Dictionary[StringName, int] = {}
## Casts still landing.
var _casts: Array[SimSkillCast] = []
## Roads whose gate has fallen in an assault: nothing more comes down them.
var _closed_lanes: Dictionary[int, bool] = {}
var _structure_cells: Dictionary[Vector2i, SimEnemy] = {}
## The enemy's war camps and the defended city (see Landmarks).
var landmarks: Array[Landmarks.Site] = []
## Cells the camps and the city stand on, to the site on each.
var _landmark_cells: Dictionary[Vector2i, Landmarks.Site] = {}
## The heroes the player can summon in this run, in key order.
var party: Array[HeroData] = []
## Summoned heroes by hero id.
var _heroes_on_board: Dictionary[StringName, SimTower] = {}
## Hero abilities still running: each a HeroAbility and its seconds left, in [ability, time, tower].
var _hero_effects: Array[Array] = []
## Ground that bursts later: [seconds left, point, radius in pixels, damage, tower].
var _bursts: Array[Array] = []
## Lives given back by kills during the running hero abilities, so each keeps to its cap.
var _lives_from_kills := 0
## The horde that died lately, for a Gravecaller to raise: [data, health multiplier, lane, progress,
## element, position, seconds ago].
var _fallen: Array[Array] = []
## Seeds a Seedsower planted: [seconds to sprout, enemy id, count, lane, progress, element, health multiplier].
var _seeds: Array[Array] = []
## How long the fallen stay fresh enough to raise, and how many are remembered.
const FALLEN_FRESH := 6.0
const FALLEN_KEEP := 40
## The player's units in the counter-attack, marching or fighting.
var allies: Array[SimAlly] = []
## True once the counter-attack has begun (see StageData.counter_wave).
var counter_started := false
## Times the counter-attack's wave has started again.
var counter_loops := 0
var _counter_loop_wait := 0.0
## Seconds until a rolling wave of the final assault brings the next one (see rolls_on()).
var _roll_wait := 0.0
## Seconds until each kind of unit can be mustered again, by ally id.
var _muster_cooldowns: Dictionary[StringName, float] = {}
## Gold from the camp's supply not yet paid out, under a whole coin.
var _supply := 0.0


func _init(p_config: RunConfig) -> void:
	config = p_config
	var rules := config.rules
	var base_gold := rules.starting_gold
	var base_lives := rules.starting_lives
	if config.stage != null:
		base_gold = config.stage.starting_gold if config.stage.starting_gold > 0 else base_gold
		base_lives = config.stage.starting_lives if config.stage.starting_lives > 0 else base_lives
	gold = roundi(StatCalculator.compute(&"starting_gold", base_gold, config.run_modifiers))
	lives = roundi(StatCalculator.compute(&"starting_lives", base_lives, config.run_modifiers))
	starting_lives = lives
	var start_points := roundi(StatCalculator.compute(&"starting_tree_points", rules.starting_tree_points, config.run_modifiers))
	tree = TreeState.new(TreeGraph.new(config.tree_nodes), start_points)
	tree.lock(config.locked_tree_nodes)
	tree.grant(config.granted_tree_nodes)
	for lane in config.map.lane_count():
		var curve := Curve2D.new()
		for point in config.map.path_points(lane):
			curve.add_point(point)
		lane_curves.append(curve)
		lane_lengths.append(curve.get_baked_length())
	path_curve = lane_curves[0]
	path_length = lane_lengths[0]
	_path_cells = config.map.path_cells()
	_place_structures()
	_place_landmarks()
	for hero in config.heroes:
		if hero != null and not party.has(hero) and party.size() < HeroData.MAX_PARTY:
			party.append(hero)
	_refresh_modifiers()


# --- Queries -----------------------------------------------------------------

func total_waves() -> int:
	return config.wave_set.waves.size()


## The wave being fought, or the next one while building. Null once the run is over. In an assault
## the last wave repeats until the enemy base falls.
func current_wave() -> WaveData:
	var index := wave_index
	if index >= total_waves():
		if is_assault() and not is_over() and total_waves() > 0:
			return config.wave_set.waves[total_waves() - 1]
		return null
	return config.wave_set.waves[index]


## 1-based number of the current or next wave. In an assault it keeps counting past the wave set,
## and enemy health keeps growing with it.
func wave_number() -> int:
	if is_assault():
		return wave_index + 1
	return mini(wave_index + 1, total_waves())


## True when the run is an assault on the enemy base: it is won by bringing down its buildings.
func is_assault() -> bool:
	return not structures.is_empty()


## True for the final assault, where the player defends, then musters units against the citadel.
func is_counter_assault() -> bool:
	return is_assault() and config.stage != null and config.stage.counter_wave > 0


## Towers and skills can hurt the enemy's buildings, except in the counter-attack, where only the
## units the player musters can.
func towers_besiege() -> bool:
	return is_assault() and not is_counter_assault()


func total_phases() -> int:
	var count := 0
	for structure in structures:
		count = maxi(count, structure.phase)
	return count


## Buildings of a phase still standing.
func structures_left(phase: int) -> Array[SimEnemy]:
	var result: Array[SimEnemy] = []
	for structure in structures:
		if structure.alive and structure.phase == phase:
			result.append(structure)
	return result


## A building can be hurt once every building of the phases before its own has fallen.
func is_vulnerable(structure: SimEnemy) -> bool:
	return structure.alive and structure.phase <= structure_phase


## True when nothing more comes down this road, because its gate has fallen.
func is_lane_closed(lane: int) -> bool:
	return _closed_lanes.has(lane)


## The rightmost column towers may be built in now, or -1 for the whole map.
func build_limit() -> int:
	if config.stage == null or config.stage.build_columns.is_empty():
		return -1
	var index := structure_phase - 1
	if index >= config.stage.build_columns.size():
		return -1
	return config.stage.build_columns[index]


## The living boss with the most health left, for the boss health bar. Buildings are not counted.
func strongest_boss() -> SimEnemy:
	var best: SimEnemy = null
	for enemy in enemies:
		if enemy.alive and enemy.data.tags.has(&"boss") and (best == null or enemy.max_health > best.max_health):
			best = enemy
	return best


func is_over() -> bool:
	return state == State.WON or state == State.LOST


func modifiers() -> Array[Modifier]:
	return _modifiers


func tower_price(tower_id: StringName) -> int:
	var data: TowerData = config.towers.get(tower_id)
	if data == null:
		return 0
	return maxi(1, roundi(StatCalculator.compute(&"cost", data.cost, _modifiers, data.all_tags())))


func is_unlocked(tower_id: StringName) -> bool:
	if tree.unlocked_towers().has(tower_id):
		return true
	var data: TowerData = config.towers.get(tower_id)
	if data == null or data.requires_nodes.is_empty():
		return false
	for node_id in data.requires_nodes:
		if not tree.is_allocated(node_id):
			return false
	return true


func tower_at(cell: Vector2i) -> SimTower:
	return _tower_at.get(cell)


# --- Skills ------------------------------------------------------------------

## Every skill of the run, in ring order of their elements.
func skill_list() -> Array[SkillData]:
	var result: Array[SkillData] = []
	result.assign(config.skills.values())
	result.sort_custom(func(a: SkillData, b: SkillData) -> bool:
		var first := config.element_index(a.element)
		var second := config.element_index(b.element)
		return first < second if first != second else String(a.id) < String(b.id))
	return result


## A skill opens when its skill web node is taken.
func is_skill_unlocked(skill_id: StringName) -> bool:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null:
		return false
	return skill.requires_node.is_empty() or tree.is_allocated(skill.requires_node)


## The skill's full cooldown in seconds, after modifiers.
func skill_cooldown(skill_id: StringName) -> float:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null:
		return 0.0
	return maxf(1.0, StatCalculator.compute(&"skill_cooldown", skill.cooldown, _modifiers, skill.all_tags()))


## Seconds of wave time until the skill is ready again. 0 when it is ready.
func skill_cooldown_left(skill_id: StringName) -> float:
	return _skill_cooldowns.get(skill_id, 0.0)


## Seconds left on a skill's lasting effect, such as faster attacks. 0 when it is not running.
func skill_time_left(skill_id: StringName) -> float:
	return _skill_time.get(skill_id, 0.0)


## Why a skill cannot be cast now, or an empty string if it can.
func skill_error(skill_id: StringName) -> String:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null:
		return "Unknown skill"
	if is_over():
		return "The run is over"
	if not is_skill_unlocked(skill_id):
		var node_data := tree.graph.node(skill.requires_node)
		if tree.is_locked(skill.requires_node):
			return "%s is closed in this run" % skill.display_name
		return "Take %s in the skill web to open %s" % [node_data.display_name if node_data != null else String(skill.requires_node), skill.display_name]
	if state != State.WAVE:
		return "Skills can only be used during a wave"
	var left := skill_cooldown_left(skill_id)
	if left > 0.0:
		return "%s is ready in %d s" % [skill.display_name, ceili(left)]
	return ""


## The level a skill is at in this run, from 1.
func skill_level(skill_id: StringName) -> int:
	return skill_levels.get(skill_id, 1)


## Gold to take the skill to its next level, or -1 when it is at its last.
func skill_upgrade_cost(skill_id: StringName) -> int:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null or skill_level(skill_id) >= skill.max_level():
		return -1
	return skill.rank(skill_level(skill_id) + 1).cost


## Why a skill cannot be taken to its next level now, or an empty string if it can.
func skill_upgrade_error(skill_id: StringName) -> String:
	var skill: SkillData = config.skills.get(skill_id)
	if skill == null:
		return "Unknown skill"
	if is_over():
		return "The run is over"
	if skill_level(skill_id) >= skill.max_level():
		return "%s is at its last level" % skill.title_at(skill_level(skill_id))
	if not is_skill_unlocked(skill_id):
		return "Open %s in the skill web first" % skill.display_name
	if gold < skill_upgrade_cost(skill_id):
		return "Not enough gold"
	return ""


## Spends gold to take a skill to its next level. Returns false and does nothing if it cannot.
func upgrade_skill(skill_id: StringName) -> bool:
	if not skill_upgrade_error(skill_id).is_empty():
		return false
	gold -= skill_upgrade_cost(skill_id)
	skill_levels[skill_id] = skill_level(skill_id) + 1
	if _skill_time.has(skill_id):
		# A boon that is running takes the new level at once.
		_skill_mods[skill_id] = _scaled_modifiers(config.skills[skill_id], skill_level(skill_id))
		_refresh_modifiers()
	skill_upgraded.emit(config.skills[skill_id], skill_level(skill_id))
	changed.emit()
	return true


## Skills that are still landing: meteors falling, waves crossing, fields burning.
func skill_casts() -> Array[SimSkillCast]:
	return _casts


## Casts a skill at a point on the board (ignored by skills that reach everything). Returns false
## and does nothing if it cannot be cast now. What lands at once lands before it returns; the rest
## (a falling meteor, a wave crossing the board) lands over the next steps.
func use_skill(skill_id: StringName, at: Vector2 = Vector2.ZERO) -> bool:
	if not skill_error(skill_id).is_empty():
		return false
	var skill: SkillData = config.skills[skill_id]
	_skill_cooldowns[skill_id] = skill_cooldown(skill_id)
	var cast := _plan_cast(skill, at)
	if skill.duration > 0.0 and not skill.modifiers.is_empty():
		_skill_time[skill_id] = skill.duration * cast.rank.hold
		_skill_mods[skill_id] = _scaled_modifiers(skill, cast.level)
		_refresh_modifiers()
	skill_used.emit(skill, cast.at)
	skill_cast.emit(cast)
	_advance_cast(cast, 0.0)
	if not cast.is_finished():
		_casts.append(cast)
	changed.emit()
	return true


## Works out every blow of a cast: where and when each lands and how hard it hits at this wave.
func _plan_cast(skill: SkillData, at: Vector2) -> SimSkillCast:
	var cast := SimSkillCast.new()
	cast.skill = skill
	cast.level = skill_level(skill.id)
	var rank := skill.rank(cast.level)
	cast.rank = rank
	var board := config.map.size_in_pixels()
	cast.at = at if skill.is_targeted() else board * 0.5
	if config.element_index(skill.element) >= 0:
		cast.elements.append(config.element_index(skill.element))
	# Skill damage keeps pace with enemy health, wave by wave.
	var growth := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	var tags := skill.all_tags()
	cast.damage = StatCalculator.compute(&"skill_damage", skill.damage + rank.damage_bonus, _modifiers, tags) * rank.power * growth
	cast.radius = skill.radius * rank.reach
	cast.knockback = (skill.knockback + rank.knockback_bonus) * rank.reach
	cast.launch = rank.launch
	for spec in skill.status_effects:
		var scaled := spec.duplicate() as StatusEffectData
		scaled.damage_per_second *= growth * rank.power
		scaled.damage_taken *= rank.power
		scaled.armour_reduction *= rank.power
		scaled.duration *= rank.hold
		cast.effects.append(scaled)
	var strikes := maxi(1, rank.strikes)
	if skill.is_targeted():
		for i in strikes:
			var blow := SimSkillCast.Blow.new()
			blow.kind = &"strike"
			blow.time = skill.impact_delay + skill.strike_gap * i
			blow.main = i == 0
			blow.at = cast.at
			blow.radius = cast.radius
			blow.damage = cast.damage
			if i > 0:
				# The rest come down in a ring round the first, smaller, each a little further round.
				var angle := float(i) * 2.39996
				blow.at = cast.at + Vector2(cos(angle), sin(angle) * 0.8) * cast.radius * (0.7 + 0.25 * float(i % 2))
				blow.radius = cast.radius * 0.65
				blow.damage = cast.damage * 0.6
			cast.blows.append(blow)
	else:
		# Waves come from the side of the board where the roads end, so they push back toward the gates.
		var ends_right := _roads_end_right()
		for i in strikes:
			var blow := SimSkillCast.Blow.new()
			blow.time = skill.impact_delay + skill.strike_gap * i
			blow.damage = cast.damage
			blow.main = i == 0
			if skill.sweep_time > 0.0:
				blow.kind = &"sweep"
				blow.at = Vector2(board.x + 40.0 if ends_right else -40.0, board.y * 0.5)
				blow.to_x = -40.0 if ends_right else board.x + 40.0
				blow.front = blow.at.x
				blow.sweep_time = skill.sweep_time
			else:
				blow.kind = &"strike"
				blow.at = cast.at
			cast.blows.append(blow)
	for i in rank.bolts:
		var bolt := SimSkillCast.Blow.new()
		bolt.kind = &"bolt"
		bolt.time = skill.impact_delay + 0.15 + skill.bolt_time * float(i) / maxf(1.0, float(rank.bolts))
		bolt.radius = SimSkillCast.BOLT_RADIUS
		bolt.damage = rank.bolt_damage * rank.power * growth
		cast.blows.append(bolt)
	return cast


## True when the roads run toward the right side of the board (their ends are right of their starts).
func _roads_end_right() -> bool:
	var drift := 0.0
	for curve in lane_curves:
		if curve.point_count >= 2:
			drift += curve.get_point_position(curve.point_count - 1).x - curve.get_point_position(0).x
	return drift >= 0.0


## A skill's modifiers at a level: its power scales what they give.
func _scaled_modifiers(skill: SkillData, level: int) -> Array[Modifier]:
	var result: Array[Modifier] = []
	var power := skill.rank(level).power
	for modifier in skill.modifiers:
		var scaled := modifier.duplicate() as Modifier
		scaled.value *= power
		result.append(scaled)
	return result


## Lands what is due of every cast still playing out, and lets their fields burn.
func _advance_casts(delta: float) -> void:
	if _casts.is_empty():
		return
	var live: Array[SimSkillCast] = []
	for cast in _casts:
		_advance_cast(cast, delta)
		if not cast.is_finished():
			live.append(cast)
	_casts = live


func _advance_cast(cast: SimSkillCast, delta: float) -> void:
	cast.age += delta
	for blow in cast.blows:
		if blow.done or cast.age < blow.time:
			continue
		match blow.kind:
			&"sweep":
				_advance_sweep(cast, blow)
			&"bolt":
				_land_bolt(cast, blow)
			_:
				_land_strike(cast, blow)
	for zone in cast.zones.duplicate():
		zone.time_left -= delta
		zone.tick -= delta
		if zone.tick <= 0.0 and zone.time_left > 0.0:
			zone.tick += SimSkillCast.ZONE_TICK
			var hit := _skill_targets(zone.at, zone.radius)
			for enemy in hit:
				_skill_hit(cast, enemy, zone.damage_per_second * SimSkillCast.ZONE_TICK, false, 0.0)
		if zone.time_left <= 0.0:
			cast.zones.erase(zone)
			if zone.finale_damage > 0.0:
				var finale := SimSkillCast.Blow.new()
				finale.kind = &"finale"
				finale.at = zone.at
				finale.radius = zone.radius
				finale.damage = zone.finale_damage
				finale.time = cast.age
				finale.done = true
				cast.blows.append(finale)
				var hit := _skill_targets(zone.at, zone.radius)
				for enemy in hit:
					_skill_hit(cast, enemy, finale.damage, false, cast.launch)
				skill_struck.emit(cast, finale, hit)


## Everything a skill can hit within `radius` of a point (0 reaches the whole board).
func _skill_targets(at: Vector2, radius: float) -> Array[SimEnemy]:
	var result: Array[SimEnemy] = []
	var pool: Array[SimEnemy] = enemies.duplicate()
	for structure in structures:
		if is_vulnerable(structure) and towers_besiege():
			pool.append(structure)
	for enemy in pool:
		if enemy.alive and (radius <= 0.0 or enemy.position.distance_to(at) <= radius):
			result.append(enemy)
	return result


func _land_strike(cast: SimSkillCast, blow: SimSkillCast.Blow) -> void:
	blow.done = true
	# A boon for the towers (Surge) lands on no enemy.
	var harms := blow.damage > 0.0 or not cast.effects.is_empty() or cast.knockback > 0.0
	var hit: Array[SimEnemy] = []
	if harms:
		hit = _skill_targets(blow.at, blow.radius)
	for enemy in hit:
		_skill_hit(cast, enemy, blow.damage, true, cast.launch)
	if blow.main and cast.rank.zone_time > 0.0:
		var zone := SimSkillCast.Zone.new()
		zone.at = blow.at
		zone.radius = maxf(blow.radius, 60.0) if blow.radius > 0.0 else 0.0
		zone.duration = cast.rank.zone_time
		zone.time_left = cast.rank.zone_time
		zone.tick = SimSkillCast.ZONE_TICK
		var growth := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
		zone.damage_per_second = cast.rank.zone_damage * cast.rank.power * growth
		zone.finale_damage = cast.rank.finale_damage * cast.rank.power * growth
		cast.zones.append(zone)
	skill_struck.emit(cast, blow, hit)


## A sweep moves its front on and hits everything it has passed since the last step.
func _advance_sweep(cast: SimSkillCast, blow: SimSkillCast.Blow) -> void:
	var front := blow.front_at(cast.age)
	var low := minf(blow.front, front)
	var high := maxf(blow.front, front)
	blow.front = front
	var hit: Array[SimEnemy] = []
	for enemy in _skill_targets(Vector2.ZERO, 0.0):
		if blow.swept.has(enemy.id) or enemy.position.x < low - 1.0 or enemy.position.x > high + 1.0:
			continue
		blow.swept[enemy.id] = true
		hit.append(enemy)
		_skill_hit(cast, enemy, blow.damage, true, cast.launch)
	if is_equal_approx(front, blow.to_x):
		blow.done = true
	if not hit.is_empty() or blow.done:
		skill_struck.emit(cast, blow, hit)


## A bolt falls on the enemy furthest along the road that this cast has not struck yet.
func _land_bolt(cast: SimSkillCast, blow: SimSkillCast.Blow) -> void:
	blow.done = true
	var struck: Dictionary[int, bool] = {}
	for other in cast.blows_of(&"bolt"):
		if other.target != null:
			struck[other.target.id] = true
	var best: SimEnemy = null
	var best_left := INF
	for enemy in enemies:
		if not enemy.alive or enemy.untouchable() or struck.has(enemy.id):
			continue
		var left := lane_lengths[enemy.lane] - enemy.progress if enemy.lane < lane_lengths.size() else 0.0
		if left < best_left:
			best_left = left
			best = enemy
	if best == null:
		for enemy in enemies:
			if enemy.alive and not enemy.untouchable():
				best = enemy
				break
	if best == null:
		return
	blow.target = best
	blow.at = best.position
	var hit := _skill_targets(blow.at, blow.radius)
	for enemy in hit:
		_skill_hit(cast, enemy, blow.damage if enemy == best else blow.damage * 0.5, false, cast.launch * 0.5)
	skill_struck.emit(cast, blow, hit)


## One enemy takes a skill's blow: its damage, its effects if `with_effects`, a throw off its feet
## and a push back along the road.
func _skill_hit(cast: SimSkillCast, enemy: SimEnemy, damage: float, with_effects: bool, launch: float) -> void:
	if not enemy.alive:
		return
	var multiplier := ElementRules.damage_multiplier(cast.elements, enemy.element)
	if damage > 0.0:
		_damage(enemy, CombatMath.hit_damage(damage, multiplier, enemy.effective_armour(), enemy.damage_taken_bonus()) * _spread_cut(enemy), null)
	if not enemy.alive:
		return
	# A field re-applies the skill's effects to whatever walks in.
	for spec in cast.effects:
		if with_effects or not enemy.has_status(spec.kind):
			enemy.apply_status(spec, null, multiplier)
	if launch > 0.0 and with_effects:
		enemy.apply_status(_launch_spec(launch), null, multiplier)
	if with_effects and cast.knockback > 0.0 and enemy.knock_back(cast.knockback) > 0.0:
		enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)


func _launch_spec(seconds: float) -> StatusEffectData:
	var spec := StatusEffectData.new()
	spec.kind = &"stun"
	spec.duration = seconds
	return spec


func _tick_skills(delta: float) -> void:
	for skill_id: StringName in _skill_cooldowns.keys():
		_skill_cooldowns[skill_id] = maxf(0.0, _skill_cooldowns[skill_id] - delta)
	var ended := false
	for skill_id: StringName in _skill_time.keys():
		_skill_time[skill_id] -= delta
		if _skill_time[skill_id] <= 0.0:
			_skill_time.erase(skill_id)
			_skill_mods.erase(skill_id)
			ended = true
	if ended:
		_refresh_modifiers()


func _place_landmarks() -> void:
	landmarks = Landmarks.find(config.map, is_path, func(cell: Vector2i) -> bool: return _structure_cells.has(cell))
	for site in landmarks:
		for cell in site.cells:
			_landmark_cells[cell] = site


## The camp or city standing on a cell, or null.
func landmark_at(cell: Vector2i) -> Landmarks.Site:
	return _landmark_cells.get(cell)


func is_path(cell: Vector2i) -> bool:
	return _path_cells.has(cell)


func path_cell_list() -> Array[Vector2i]:
	var result: Array[Vector2i] = []
	result.assign(_path_cells.keys())
	return result


## Why a tower cannot go on a cell, or an empty string if it can.
func placement_error(tower_id: StringName, cell: Vector2i) -> String:
	if is_over():
		return "The run is over"
	if not config.towers.has(tower_id):
		return "Unknown tower"
	if not is_unlocked(tower_id):
		return "Unlock this tower in the skill web first"
	if not config.map.is_inside(cell):
		return "Outside the map"
	if is_path(cell):
		return "Towers cannot go on the path"
	if _structure_cells.has(cell):
		return "The enemy's building stands here"
	if _landmark_cells.has(cell):
		return "The enemy's war camp stands here" if _landmark_cells[cell].kind == &"camp" else "The city stands here"
	var limit := build_limit()
	if limit >= 0 and cell.x > limit:
		return "The enemy still holds this ground: bring down its buildings first"
	if _tower_at.has(cell):
		return "There is already a tower here"
	if gold < tower_price(tower_id):
		return "Not enough gold"
	return ""


func can_place(tower_id: StringName, cell: Vector2i) -> bool:
	return placement_error(tower_id, cell).is_empty()


## Refunds are allowed for nodes taken since the last wave started, until the next one starts.
func can_refund_node(id: StringName) -> bool:
	return state == State.BUILDING and _taken_this_break.has(id) and tree.can_refund(id)


## Pixels an enemy still has to walk to leave the map.
func distance_to_exit(enemy: SimEnemy) -> float:
	return lane_lengths[enemy.lane] - enemy.progress


## Element index of the wave being fought or about to start, or -1.
func wave_element() -> int:
	var wave := current_wave()
	return config.element_index(wave.element) if wave != null else -1


# --- Player actions ----------------------------------------------------------

func place_tower(tower_id: StringName, cell: Vector2i) -> SimTower:
	if not can_place(tower_id, cell):
		return null
	var data: TowerData = config.towers[tower_id]
	var price := tower_price(tower_id)
	var indices: Array[int] = []
	for element_id in data.elements:
		indices.append(config.element_index(element_id))
	var tower := SimTower.new(_new_id(), data, cell, config.map.cell_center(cell), price, indices)
	gold -= price
	towers.append(tower)
	_tower_at[cell] = tower
	_recompute_towers()
	changed.emit()
	return tower


## Towers a built tower can turn into: unlocked ones with exactly one more element that keep all
## of its own. A base tower becomes a dual, and a dual becomes a triple. Ascended towers stay as they are.
func hybrid_options(tower: SimTower) -> Array[StringName]:
	var result: Array[StringName] = []
	if tower == null or tower.ascendancy != null or tower.is_hero():
		return result
	var own := tower.data.elements
	for id: StringName in config.towers:
		var data: TowerData = config.towers[id]
		if data.elements.size() != own.size() + 1 or not is_unlocked(id):
			continue
		if own.all(func(element_id: StringName) -> bool: return data.elements.has(element_id)):
			result.append(id)
	result.sort_custom(func(a: StringName, b: StringName) -> bool: return String(a) < String(b))
	return result


## Gold to turn a built base tower into a hybrid: the hybrid's price minus what the tower cost.
func hybrid_upgrade_price(tower: SimTower, hybrid_id: StringName) -> int:
	return maxi(0, tower_price(hybrid_id) - tower.type_price)


## Why a tower cannot become this hybrid, or an empty string if it can.
func hybrid_upgrade_error(tower: SimTower, hybrid_id: StringName) -> String:
	if is_over():
		return "The run is over"
	if not towers.has(tower):
		return "Unknown tower"
	if tower.ascendancy != null:
		return "Ascended towers cannot change"
	if not hybrid_options(tower).has(hybrid_id):
		return "This tower cannot become that tower"
	if gold < hybrid_upgrade_price(tower, hybrid_id):
		return "Not enough gold"
	return ""


## Turns a base tower into a hybrid in place, paying the difference in price.
func upgrade_to_hybrid(tower: SimTower, hybrid_id: StringName) -> bool:
	if not hybrid_upgrade_error(tower, hybrid_id).is_empty():
		return false
	var data: TowerData = config.towers[hybrid_id]
	var price := hybrid_upgrade_price(tower, hybrid_id)
	gold -= price
	var indices: Array[int] = []
	for element_id in data.elements:
		indices.append(config.element_index(element_id))
	tower.change_type(data, indices, tower.type_price + price, price)
	_recompute_towers()
	changed.emit()
	return true


## Why a tower cannot go up a level, or an empty string if it can.
func level_up_error(tower: SimTower) -> String:
	if is_over():
		return "The run is over"
	if not towers.has(tower):
		return "Unknown tower"
	if tower.is_hero():
		return "Heroes grow a level for every wave they fight"
	if tower.level >= SimTower.MAX_LEVEL:
		return "Already at the top level"
	if gold < tower.level_up_price():
		return "Not enough gold"
	return ""


func level_up(tower: SimTower) -> bool:
	if not level_up_error(tower).is_empty():
		return false
	var price := tower.level_up_price()
	gold -= price
	tower.price_paid += price
	tower.level += 1
	_recompute_towers()
	changed.emit()
	return true


## Why a tower cannot take this ascendancy, or an empty string if it can.
func ascend_error(tower: SimTower, ascendancy_id: StringName) -> String:
	if is_over():
		return "The run is over"
	if not towers.has(tower):
		return "Unknown tower"
	if tower.is_hero():
		return "Heroes cannot ascend"
	if tower.ascendancy != null:
		return "Already ascended"
	if tower.level < SimTower.MAX_LEVEL:
		return "Reach level %d first" % SimTower.MAX_LEVEL
	var option := tower.data.ascendancy(ascendancy_id)
	if option == null:
		return "Unknown ascendancy"
	if gold < tower.ascend_price(option):
		return "Not enough gold"
	return ""


func ascend(tower: SimTower, ascendancy_id: StringName) -> bool:
	if not ascend_error(tower, ascendancy_id).is_empty():
		return false
	var option := tower.data.ascendancy(ascendancy_id)
	var price := tower.ascend_price(option)
	gold -= price
	tower.price_paid += price
	tower.ascendancy = option
	_recompute_towers()
	changed.emit()
	return true


func sell_value(tower: SimTower) -> int:
	if tower.is_hero():
		return 0
	return floori(tower.price_paid * clampf(run_stat(&"sell_refund", config.rules.sell_refund), 0.0, 1.0))


## A run-wide number, such as gold per wave, after the meta tree's and the skill web's bonuses.
func run_stat(stat: StringName, base: float) -> float:
	return StatCalculator.compute(stat, base, _modifiers)


func sell_tower(tower: SimTower) -> int:
	if not towers.has(tower) or tower.is_hero():
		return 0
	var refund := sell_value(tower)
	gold += refund
	towers.erase(tower)
	_tower_at.erase(tower.cell)
	_recompute_towers()
	changed.emit()
	return refund


func start_next_wave() -> bool:
	if state != State.BUILDING or current_wave() == null:
		return false
	_begin_wave()
	return true


func _begin_wave() -> void:
	var wave := current_wave()
	state = State.WAVE
	time_in_wave = 0.0
	break_time_left = -1.0
	_wave_element = config.element_index(wave.element)
	_spawner.start(wave, lane_curves.size())
	_taken_this_break.clear()
	for tower in _heroes_on_board.values():
		tower.moved_this_break = false
	for hero in config.arriving_heroes:
		if hero != null and hero.arrives_at_wave == wave_number() and not party.has(hero):
			party.append(hero)
			hero_arrived.emit(hero)
	_roll_wait = config.stage.auto_wave_delay if config.stage != null else 0.0
	wave_started.emit(wave_number())
	_advance_act()
	changed.emit()


## The act of the final assault a wave belongs to: 1 while the player only defends, 2 for the wave the
## overlord comes, 3 for the counter-attack. 0 in any other run.
func assault_act(number: int = -1) -> int:
	if not is_counter_assault():
		return 0
	var n := wave_number() if number < 0 else number
	if n >= config.stage.counter_wave:
		return 3
	if config.stage.boss_wave > 0 and n >= config.stage.boss_wave:
		return 2
	return 1


## Moves the final assault on to the act of the wave just started.
func _advance_act() -> void:
	var act := assault_act()
	if act <= structure_phase or citadel_fallen:
		return
	structure_phase = act
	if act >= 3 and not counter_started:
		counter_started = true
		gold += config.stage.war_chest
		counter_attack_started.emit()
	_recompute_towers()
	phase_changed.emit(structure_phase)


func allocate_node(id: StringName) -> bool:
	if is_over() or not tree.allocate(id):
		return false
	if state == State.BUILDING:
		_taken_this_break[id] = true
	_refresh_modifiers()
	changed.emit()
	return true


func refund_node(id: StringName) -> bool:
	if not can_refund_node(id) or not tree.refund(id):
		return false
	_taken_this_break.erase(id)
	_refresh_modifiers()
	changed.emit()
	return true


# --- Simulation --------------------------------------------------------------

func step(delta: float) -> void:
	if state != State.WAVE:
		return
	time_in_wave += delta
	_tick_skills(delta)
	_tick_heroes(delta)
	_spawn(delta)
	_move_enemies(delta)
	if state != State.WAVE:
		return
	_advance_casts(delta)
	_tick_statuses(delta)
	_tick_traits(delta)
	_rebuild_hash()
	_update_towers(delta)
	_update_projectiles(delta)
	if counter_started:
		_update_allies(delta)
		_tick_structure_defences(delta)
	_remove_dead()
	if not _arrivals.is_empty():
		enemies.append_array(_arrivals)
		_arrivals.clear()
	if state != State.WAVE:
		return
	if citadel_fallen and not _overlord_alive():
		_end_run(true)
		return
	if counter_started:
		_loop_counter_wave(delta)
		return
	if rolls_on():
		if _spawner.is_finished():
			_roll_wait -= delta
			if _roll_wait <= 0.0:
				_roll_wave()
		return
	if _spawner.is_finished() and enemies.is_empty() and _seeds.is_empty():
		_finish_wave()


## In the final assault the horde never lets up while the player defends: each wave marches in a few
## seconds after the last one has left the gates, whether or not the board is clear. The wave before
## the Sunderer's ends as usual, so there is a breath before he comes.
func rolls_on() -> bool:
	return is_counter_assault() and config.stage.boss_wave > 0 and wave_number() < config.stage.boss_wave - 1


## Seconds until the next wave rolls in, or -1 when the next wave waits for a break.
func next_wave_in() -> float:
	if state == State.WAVE and rolls_on() and _spawner.is_finished():
		return maxf(0.0, _roll_wait)
	if state == State.BUILDING:
		return break_time_left
	return -1.0


## The wave being fought pays out, and the next one marches in at once.
func _roll_wave() -> void:
	var finished := current_wave()
	wave_index += 1
	var rewards := _pay_wave(finished)
	wave_cleared.emit(wave_index, rewards[0], rewards[1])
	_begin_wave()


## The counter-attack's wave never ends while the citadel stands: once its last enemy has marched
## out, it starts again, a little stronger.
func _loop_counter_wave(delta: float) -> void:
	if not _spawner.is_finished():
		_counter_loop_wait = COUNTER_LOOP_GAP
		return
	_counter_loop_wait -= delta
	if _counter_loop_wait <= 0.0 and current_wave() != null:
		counter_loops += 1
		_counter_loop_wait = COUNTER_LOOP_GAP
		_spawner.start(current_wave(), lane_curves.size())


## Counts down the break before a wave that starts on its own. Call it while building; the game
## does so every frame. Returns true when it started the wave.
func tick_break(delta: float) -> bool:
	if state != State.BUILDING or break_time_left < 0.0:
		return false
	break_time_left -= delta
	if break_time_left <= 0.0:
		return start_next_wave()
	return false


func _spawn(delta: float) -> void:
	var multiplier := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	var wave := current_wave()
	if wave != null:
		multiplier *= wave.health_multiplier
	multiplier *= 1.0 + COUNTER_LOOP_GROWTH * counter_loops
	for spawn in _spawner.advance(delta):
		var group := spawn.group
		var data: EnemyData = config.enemies.get(group.enemy)
		if data == null:
			continue
		var lane := _open_lane(spawn.lane)
		var element := _wave_element
		if not group.element.is_empty():
			element = config.element_index(group.element)
		var enemy := _make_enemy(data, multiplier, lane, element, 0.0)
		enemies.append(enemy)
		if data.tags.has(&"boss"):
			boss_arrived.emit(enemy)


## The lane itself if its gate still stands, otherwise the next open one. If every road is closed
## the enemies still come down the first one.
func _open_lane(lane: int) -> int:
	if _closed_lanes.is_empty():
		return lane
	for offset in lane_curves.size():
		var candidate := (lane + offset) % lane_curves.size()
		if not _closed_lanes.has(candidate):
			return candidate
	return lane


## A new enemy on a lane. An enemy with its own element keeps it whatever the wave.
func _make_enemy(data: EnemyData, multiplier: float, lane: int, element: int, progress: float) -> SimEnemy:
	var enemy := SimEnemy.new(_new_id(), data, multiplier)
	enemy.lane = lane
	enemy.element = config.element_index(data.element) if not data.element.is_empty() else element
	enemy.progress = maxf(0.0, progress)
	enemy.position = lane_curves[lane].sample_baked(enemy.progress)
	return enemy


## Enemies that come out of another: splitting on death, or summoned by a boss. They appear a little
## behind it on its lane, with its strength and element.
func _release_from(parent: SimEnemy, enemy_id: StringName, count: int) -> void:
	var data: EnemyData = config.enemies.get(enemy_id)
	if data == null:
		return
	for i in count:
		var child := _make_enemy(data, parent.health_multiplier, parent.lane, parent.element, parent.progress - 14.0 * i)
		_arrivals.append(child)
		if data.tags.has(&"boss"):
			boss_arrived.emit(child)


func _move_enemies(delta: float) -> void:
	if counter_started:
		_hold_the_road()
	for enemy in enemies:
		if not enemy.alive:
			continue
		if enemy.transforming > 0.0:
			enemy.transforming = maxf(0.0, enemy.transforming - delta)
			continue
		if enemy.fleeing:
			enemy.progress -= enemy.base_speed * FLEE_SPEED * delta
			if enemy.progress <= 0.0:
				enemy.alive = false
				enemy.escaped = true
				enemy_escaped.emit(enemy)
			else:
				enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)
			continue
		enemy.progress += enemy.speed() * delta
		if enemy.progress >= lane_lengths[enemy.lane] and is_warded():
			# Last Light: the gate throws it back to the start of its road.
			enemy.progress = 0.0
			enemy.position = lane_curves[enemy.lane].sample_baked(0.0)
		elif enemy.progress >= lane_lengths[enemy.lane]:
			enemy.alive = false
			enemy.leaked = true
			leaks += 1
			lives -= enemy.data.leak_damage
			enemy_leaked.emit(enemy)
			if lives <= 0:
				lives = 0
				_end_run(false)
				return
		else:
			enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)


## Healing, summoning and changing element, the horde's powers and the bosses' tricks.
func _tick_traits(delta: float) -> void:
	_tick_boss_tricks(delta)
	_tick_horde_auras(delta)
	_tick_powers(delta)
	_tick_seeds(delta)
	_age_fallen(delta)
	# Buildings only call up the horde while the wave is still marching in, so a wave can end.
	if not _spawner.is_finished():
		for structure in structures:
			if structure.alive and is_vulnerable(structure):
				_tick_summons(structure, delta)
	for enemy in enemies:
		if not enemy.alive:
			continue
		var data := enemy.data
		if enemy.is_regenerating() and enemy.health < enemy.max_health:
			enemy.health = minf(enemy.max_health, enemy.health + enemy.max_health * data.regen_per_second * delta)
		_tick_summons(enemy, delta)
		if data.prismatic_interval > 0.0:
			enemy.prism_timer -= delta
			if enemy.prism_timer <= 0.0:
				enemy.prism_timer += data.prismatic_interval
				enemy.element = (maxi(enemy.element, 0) + 1) % ElementData.RING_SIZE


func _tick_summons(enemy: SimEnemy, delta: float) -> void:
	if enemy.transforming > 0.0 or enemy.fleeing:
		return
	var data := enemy.data
	if data.summon_interval > 0.0 and not data.summon.is_empty():
		enemy.summon_timer -= delta
		if enemy.summon_timer <= 0.0:
			enemy.summon_timer += data.summon_interval
			_release_from(enemy, data.summon, data.summon_count)


## Shields, silences, blinks and rage. Buildings of the enemy base use them too, once they can be hurt.
func _tick_boss_tricks(delta: float) -> void:
	var casters: Array[SimEnemy] = []
	for enemy in enemies:
		if enemy.alive:
			enemy.ward = 0.0
			casters.append(enemy)
	for structure in structures:
		if is_vulnerable(structure):
			casters.append(structure)
	for caster in casters:
		var data := caster.data
		if caster.transforming > 0.0 or caster.fleeing:
			continue
		if data.escape_below > 0.0 and caster.health < caster.max_health * data.escape_below:
			caster.alive = false
			caster.escaped = true
			enemy_escaped.emit(caster)
			continue
		if data.enrage_below > 0.0 and not caster.enraged and caster.health < caster.max_health * data.enrage_below:
			caster.enraged = true
		if data.ward_radius > 0.0 and data.ward_reduction > 0.0:
			var reach := data.ward_radius * data.ward_radius
			for other in enemies:
				if other != caster and other.alive and other.position.distance_squared_to(caster.position) <= reach:
					other.ward = maxf(other.ward, clampf(data.ward_reduction, 0.0, 0.9))
		if data.silence_interval > 0.0 and data.silence_radius > 0.0:
			caster.silence_timer -= delta
			if caster.silence_timer <= 0.0:
				caster.silence_timer += data.silence_interval
				_silence_towers(caster)
		if data.blink_interval > 0.0 and data.blink_distance > 0.0 and not caster.structure \
				and not caster.has_status(&"stun"):
			caster.blink_timer -= delta
			if caster.blink_timer <= 0.0:
				caster.blink_timer += data.blink_interval
				var from := caster.position
				# A blink never carries it out of the map: it stops a little short of the exit.
				var room := lane_lengths[caster.lane] - 64.0 - caster.progress
				var jump := minf(data.blink_distance, room)
				if jump > 0.0:
					caster.progress += jump
					caster.position = lane_curves[caster.lane].sample_baked(caster.progress)
					enemy_blinked.emit(caster, from)


## Each kind of enemy's own power. See EnemyData.power.
func _tick_powers(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		var data := enemy.data
		enemy.haste_left = maxf(0.0, enemy.haste_left - delta)
		if enemy.downed > 0.0:
			enemy.downed -= delta
			if enemy.downed <= 0.0:
				enemy.downed = 0.0
				enemy.risen = true
				enemy.health = enemy.max_health * clampf(data.power_amount, 0.05, 1.0)
				enemy_power.emit(enemy, &"rise", [])
			continue
		if not enemy.has_power:
			continue
		enemy.power_left = maxf(0.0, enemy.power_left - delta)
		enemy.power_timer = maxf(0.0, enemy.power_timer - delta)
		if enemy.power_timer > 0.0 or not enemy.can_use_power():
			continue
		match data.power:
			&"war_cry":
				var driven: Array = []
				for ally in _allies_near(enemy, data.power_radius):
					# It drives the lesser ranks on: not runners, already as fast as they go, nor
					# brutes, its own kind.
					if not ally.data.tags.has(&"fast") and ally.data.power != &"war_cry":
						driven.append(ally)
				for ally: SimEnemy in driven:
					ally.haste = maxf(ally.haste if ally.haste_left > 0.0 else 0.0, data.power_amount)
					ally.haste_left = maxf(ally.haste_left, data.power_duration)
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"war_cry", driven)
			&"mend":
				# A healer on fire or sick with poison cannot mend anyone.
				if enemy.has_status(&"burn") or enemy.has_status(&"poison"):
					continue
				var healed: Array = []
				for ally in _allies_near(enemy, data.power_radius):
					if ally.health < ally.max_health and not ally.data.tags.has(&"boss") \
							and not ally.has_status(&"burn") and not ally.has_status(&"poison"):
						ally.health = minf(ally.max_health, ally.health + ally.max_health * data.power_amount)
						healed.append(ally)
				# It waits for someone to be hurt, so every pulse heals.
				if not healed.is_empty():
					enemy.power_timer = data.power_interval
					enemy_power.emit(enemy, &"mend", healed)
			&"block":
				if not enemy.shield_up:
					enemy.shield_up = true
					enemy_power.emit(enemy, &"shield", [])
			&"breath":
				var target := _strongest_tower_near(enemy.position, data.power_radius)
				if target != null:
					target.silenced = maxf(target.silenced, data.power_duration)
					enemy.power_timer = data.power_interval
					enemy_power.emit(enemy, &"breath", [target])
			_:
				_use_horde_power(enemy)


## Living, touchable enemies within `radius` of `caster`, the caster too.
func _allies_near(caster: SimEnemy, radius: float) -> Array[SimEnemy]:
	var found: Array[SimEnemy] = []
	var reach := radius * radius
	for other in enemies:
		if other.alive and other.downed <= 0.0 and other.position.distance_squared_to(caster.position) <= reach:
			found.append(other)
	return found


## The tower that hits hardest within `radius` of `at`, or null. With `skip_netted`, towers
## already caught in a net are passed over.
func _strongest_tower_near(at: Vector2, radius: float, skip_netted := false) -> SimTower:
	var best: SimTower = null
	var reach := radius * radius
	for tower in towers:
		if tower.position.distance_squared_to(at) > reach:
			continue
		if skip_netted and tower.net_left > 0.0:
			continue
		if best == null or tower.damage * tower.attacks_per_second > best.damage * best.attacks_per_second:
			best = tower
	return best


func _silence_towers(caster: SimEnemy) -> void:
	var hit: Array[SimTower] = []
	var reach := caster.data.silence_radius * caster.data.silence_radius
	for tower in towers:
		if tower.position.distance_squared_to(caster.position) <= reach:
			tower.silenced = maxf(tower.silenced, caster.data.silence_duration)
			hit.append(tower)
	if not hit.is_empty():
		towers_silenced.emit(caster, hit)


func _tick_statuses(delta: float) -> void:
	for enemy in enemies:
		if not enemy.alive:
			continue
		enemy.stun_immunity = maxf(0.0, enemy.stun_immunity - delta)
		for kind: StringName in enemy.statuses.keys():
			# A blow can change a boss's form, which clears what burned on the old one.
			if not enemy.statuses.has(kind):
				continue
			var status: SimStatus = enemy.statuses[kind]
			var dps := status.damage_per_second()
			if dps > 0.0:
				# A Cinderhound drinks fire, and a Greenwitch's patients drink poison: both heal them.
				if _feeds_on(enemy, kind):
					enemy.health = minf(enemy.max_health, enemy.health + dps * minf(delta, status.time_left))
				else:
					_damage(enemy, dps * minf(delta, status.time_left), status.source)
				# Dead, fallen in a heap, or changing form: its statuses are gone.
				if not enemy.alive or enemy.downed > 0.0 or enemy.transforming > 0.0 or enemy.fleeing:
					break
			# Cinderhounds shake off chills faster.
			var wear := delta
			if status.slow > 0.0 and enemy.has_power and enemy.data.power == &"fireborn":
				wear *= maxf(1.0, enemy.data.power_amount)
			status.time_left -= wear
			if status.time_left <= 0.0:
				enemy.statuses.erase(kind)
				if kind == &"stun":
					enemy.stun_immunity = SimEnemy.STUN_IMMUNITY


## Whether this damage-over-time heals the enemy instead of hurting it.
func _feeds_on(enemy: SimEnemy, kind: StringName) -> bool:
	if kind == &"burn" and enemy.has_power and enemy.data.power == &"fireborn":
		return true
	return kind == &"poison" and enemy.remedied


func _rebuild_hash() -> void:
	_hash.clear()
	for enemy in enemies:
		if enemy.alive and not enemy.untouchable():
			_hash.insert(enemy)
	if towers_besiege():
		for structure in structures:
			if is_vulnerable(structure):
				_hash.insert(structure)


func _update_towers(delta: float) -> void:
	for tower in towers:
		tower.tick_hexes(delta)
		if tower.silenced > 0.0:
			tower.silenced = maxf(0.0, tower.silenced - delta)
			continue
		tower.cooldown -= delta
		if tower.cooldown > 0.0:
			continue
		var target := _find_target(tower)
		if target == null:
			tower.cooldown = 0.0
			continue
		_attack(tower, target)
		tower.cooldown += CombatMath.attack_interval(tower.rate_now())


## The enemy in range that is closest to leaving the map. Buildings of the enemy base come last,
## except for a siege shot now and then.
func _find_target(tower: SimTower) -> SimEnemy:
	tower.shots += 1
	if towers_besiege() and tower.shots % SIEGE_EVERY == 0:
		for structure in structures:
			if is_vulnerable(structure) and structure.position.distance_to(tower.position) <= tower.range_now():
				return structure
	var best: SimEnemy = null
	var best_left := INF
	var reach := tower.range_now()
	for enemy in _hash.query(tower.position, reach):
		# An Umbral Stalker is only seen up close.
		if enemy.has_power and enemy.data.power == &"stalk" \
				and enemy.position.distance_to(tower.position) > reach * enemy.data.power_amount:
			continue
		var left := distance_to_exit(enemy) if not enemy.structure else 1.0e9 + enemy.health
		if left < best_left:
			best_left = left
			best = enemy
	return best


func _attack(tower: SimTower, target: SimEnemy) -> void:
	tower_attacked.emit(tower, target)
	if tower.chains():
		_fire_chain(tower, target)
		return
	var shot := SimProjectile.new()
	shot.position = tower.position
	shot.target = target
	shot.target_point = target.position
	shot.speed = tower.projectile_speed
	shot.source = tower
	shot.damage = tower.damage_now()
	shot.splash_radius = tower.splash_radius
	projectiles.append(shot)


func _fire_chain(tower: SimTower, first: SimEnemy) -> void:
	var points := PackedVector2Array([tower.position])
	var hit: Dictionary[int, bool] = {}
	var current := first
	for jump in range(tower.chain_count + 1):
		points.append(current.position)
		hit[current.id] = true
		_hit(tower, current, CombatMath.chain_damage(tower.damage_now(), tower.chain_falloff, jump))
		var next: SimEnemy = null
		var best_distance := INF
		for candidate in _hash.query(current.position, tower.chain_range):
			if hit.has(candidate.id):
				continue
			var distance := candidate.position.distance_squared_to(current.position)
			if distance < best_distance:
				best_distance = distance
				next = candidate
		if next == null:
			break
		current = next
	chain_fired.emit(tower, points)


func _update_projectiles(delta: float) -> void:
	for shot in projectiles:
		if shot.target != null and shot.target.alive:
			shot.target_point = shot.target.position
		var travel := shot.speed * delta
		if shot.position.distance_to(shot.target_point) <= travel:
			shot.position = shot.target_point
			_land(shot)
		else:
			shot.position = shot.position.move_toward(shot.target_point, travel)
	var flying: Array[SimProjectile] = []
	for shot in projectiles:
		if not shot.done:
			flying.append(shot)
	projectiles = flying


func _land(shot: SimProjectile) -> void:
	shot.done = true
	if shot.splash_radius > 0.0:
		for enemy in _hash.query(shot.position, shot.splash_radius):
			_hit(shot.source, enemy, shot.damage)
	elif shot.target != null and shot.target.alive:
		_hit(shot.source, shot.target, shot.damage)
	projectile_landed.emit(shot)


func _hit(tower: SimTower, enemy: SimEnemy, damage: float) -> void:
	if not enemy.alive or enemy.untouchable():
		return
	if enemy.shield_up:
		# The shield (or a Glass-Singer's ward) takes the whole hit, effects and all, and breaks.
		enemy.shield_up = false
		if enemy.data.power == &"block":
			enemy.power_timer = enemy.data.power_interval
		enemy_power.emit(enemy, &"block", [tower])
		return
	var power := enemy.data.power if enemy.has_power else &""
	if power == &"smoke":
		# Most of a Smoke Wraith is soot: every so often a blow passes straight through.
		enemy.dodge += enemy.data.power_amount
		if enemy.dodge >= 1.0:
			enemy.dodge -= 1.0
			enemy_power.emit(enemy, &"smoke", [tower])
			return
	var multiplier := _element_multiplier(tower, enemy)
	var armour := enemy.effective_armour() * (1.0 - tower.armour_ignore)
	var dealt := CombatMath.hit_damage(damage, multiplier, armour, enemy.damage_taken_bonus())
	if tower.splash_radius > 0.0 or tower.chains():
		dealt *= _spread_cut(enemy)
	_damage(enemy, dealt, tower)
	if enemy.alive:
		_struck(enemy, tower)
		if not tower.hushed:
			for spec in tower.effects:
				enemy.apply_status(spec, tower, multiplier)
		if tower.knockback > 0.0 and enemy.knock_back(tower.knockback) > 0.0:
			enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)
			enemy.momentum = 0.0


func _damage(enemy: SimEnemy, amount: float, source: SimTower) -> void:
	if not enemy.alive or amount <= 0.0 or enemy.untouchable():
		return
	if enemy.ward > 0.0:
		amount *= 1.0 - enemy.ward
	if enemy.is_hardened():
		amount *= 1.0 - clampf(enemy.data.power_amount, 0.0, 0.95)
	if enemy.shell > 0.0:
		# A Rimeback's ice soaks the blow up first.
		var soaked := minf(enemy.shell, amount)
		enemy.shell -= soaked
		amount -= soaked
		if enemy.shell <= 0.0:
			enemy.shell = 0.0
			enemy.power_timer = enemy.data.power_interval
			enemy_power.emit(enemy, &"shell_break", [])
		if amount <= 0.0:
			return
	var dealt := minf(amount, enemy.health)
	enemy.health -= amount
	if source != null:
		source.damage_dealt += dealt
	if enemy.health <= 0.0:
		if not enemy.data.next_form.is_empty() and config.enemies.has(enemy.data.next_form):
			_transform(enemy)
			return
		if enemy.data.flee_when_beaten:
			_flee(enemy)
			return
		if enemy.data.power == &"rise" and enemy.has_power and not enemy.risen and not enemy.has_status(&"burn"):
			_fall(enemy)
			return
		_kill(enemy, source)
	elif (enemy.data.power == &"harden" or enemy.data.power == &"phase") and enemy.has_power \
			and enemy.power_timer <= 0.0 and enemy.can_use_power():
		# Struck, it turns to stone or slips out of the world for a moment.
		enemy.power_left = enemy.data.power_duration
		enemy.power_timer = enemy.data.power_interval + enemy.data.power_duration
		enemy_power.emit(enemy, enemy.data.power, [])


## A boss beaten in one form rises in the next, at its full health.
func _transform(enemy: SimEnemy) -> void:
	var from := enemy.data
	enemy.become(config.enemies[from.next_form], from.transform_seconds)
	enemy_transformed.emit(enemy, from)


## A beaten boss that flees: beyond reach, it runs back up its road and leaves the board. It pays its
## bounty for the beating.
func _flee(enemy: SimEnemy) -> void:
	enemy.health = 0.0
	enemy.fleeing = true
	enemy.statuses.clear()
	var bounty := roundi(enemy.data.bounty * gold_multiplier())
	gold += bounty
	gold_earned += bounty
	boss_fled.emit(enemy)


## A grunt that would have died falls in a heap instead, out of reach, and rises a little later.
func _fall(enemy: SimEnemy) -> void:
	enemy.health = 0.0
	enemy.downed = maxf(0.1, enemy.data.power_duration)
	enemy.statuses.clear()
	enemy.haste_left = 0.0
	enemy_power.emit(enemy, &"fall", [])


func _kill(enemy: SimEnemy, killer: SimTower) -> void:
	enemy.alive = false
	kills += 1
	var bounty := enemy.data.bounty if not enemy.raised else 0
	if killer != null:
		killer.kills += 1
		bounty += killer.bounty_bonus
	bounty = roundi(bounty * gold_multiplier())
	_lives_for_kill()
	gold += bounty
	gold_earned += bounty
	_spread_statuses(enemy)
	if enemy.data.split_count > 0 and not enemy.data.split_into.is_empty():
		_release_from(enemy, enemy.data.split_into, enemy.data.split_count)
	_on_horde_death(enemy, killer)
	enemy_killed.emit(enemy, killer, bounty)
	if enemy.structure:
		_on_structure_fallen(enemy)


## Notables such as Inferno and Blight pass a dying enemy's burn or poison to its neighbours.
func _spread_statuses(dead: SimEnemy) -> void:
	var burn: SimStatus = dead.statuses.get(&"burn")
	if burn != null and burn.source != null and burn.source.burn_spread_radius > 0.0:
		var spec := burn.source.effect_spec(&"burn")
		if spec != null:
			for enemy in _hash.query(dead.position, burn.source.burn_spread_radius):
				enemy.apply_status(spec, burn.source, burn.element_multiplier)
	var poison: SimStatus = dead.statuses.get(&"poison")
	if poison != null and poison.source != null and poison.source.poison_spread_count > 0:
		var spec := poison.source.effect_spec(&"poison")
		if spec != null:
			var origin := dead.position
			var nearby := _hash.query(origin, POISON_SPREAD_RANGE)
			var closer := func(a: SimEnemy, b: SimEnemy) -> bool: return a.position.distance_squared_to(origin) < b.position.distance_squared_to(origin)
			nearby.sort_custom(closer)
			for i in mini(poison.source.poison_spread_count, nearby.size()):
				nearby[i].apply_status(spec, poison.source, poison.element_multiplier)


func _remove_dead() -> void:
	var living: Array[SimEnemy] = []
	for enemy in enemies:
		if enemy.alive:
			living.append(enemy)
	enemies = living


func _finish_wave() -> void:
	var finished := current_wave()
	wave_index += 1
	var rewards := _pay_wave(finished)
	projectiles.clear()
	_bursts.clear()
	_casts.clear()
	if wave_index >= total_waves() and not is_assault():
		_end_run(true)
	else:
		state = State.BUILDING
		if config.stage != null and config.stage.auto_wave_delay > 0.0:
			break_time_left = config.stage.auto_wave_delay
	wave_cleared.emit(wave_index, rewards[0], rewards[1])
	changed.emit()


## Tree points and gold for a wave fought, and a level for every hero: [points, gold].
func _pay_wave(finished: WaveData) -> Array[int]:
	var rules := config.rules
	var points := rules.tree_points_after_wave(wave_index, false)
	if finished.is_boss:
		points += roundi(run_stat(&"tree_points_per_boss", rules.tree_points_per_boss))
	tree.points += points
	var bonus := roundi(run_stat(&"gold_per_wave", rules.gold_per_wave))
	gold += bonus
	gold_earned += bonus
	_level_heroes()
	return [points, bonus]


func _end_run(won: bool) -> void:
	state = State.WON if won else State.LOST
	projectiles.clear()
	run_ended.emit(won)
	changed.emit()


func _refresh_modifiers() -> void:
	_modifiers.clear()
	_modifiers.append_array(config.run_modifiers)
	_modifiers.append_array(tree.modifiers())
	for skill_id: StringName in _skill_time:
		var skill: SkillData = config.skills.get(skill_id)
		if skill != null:
			_modifiers.append_array(_skill_mods.get(skill_id, skill.modifiers))
	for effect in _hero_effects:
		_modifiers.append_array((effect[0] as HeroAbility).modifiers)
	_recompute_towers()


## Recomputes every tower's stats, then hands out Void auras: each tower gets the strongest aura
## from another tower in range. Auras never boost the tower giving them.
func _recompute_towers() -> void:
	_apply_hero_auras()
	for tower in towers:
		tower.aura_bonus = 0.0
		tower.recompute(_modifiers)
	var givers: Array[SimTower] = []
	for tower in towers:
		if tower.aura_radius > 0.0 and tower.aura_damage > 0.0:
			givers.append(tower)
	if givers.is_empty():
		return
	for tower in towers:
		var best := 0.0
		for giver in givers:
			if giver != tower and giver.position.distance_to(tower.position) <= giver.aura_radius:
				best = maxf(best, giver.aura_damage)
		if best > 0.0:
			tower.aura_bonus = best
			tower.recompute(_modifiers)


# --- Assault -------------------------------------------------------------------

## Raises the buildings of an assault stage's enemy base. They stand on their road's first point
## (so whatever they release walks that road), but are drawn and targeted on their own cell.
func _place_structures() -> void:
	if config.stage == null:
		return
	var multiplier := config.wave_set.health_multiplier(1) * config.enemy_health_multiplier()
	# The citadel of the final assault is fought by units grown to the counter-attack's wave.
	if config.stage.counter_wave > 0:
		multiplier = config.wave_set.health_multiplier(config.stage.counter_wave) * config.enemy_health_multiplier()
	for spec in config.stage.structures:
		var data: EnemyData = config.enemies.get(spec.enemy) if spec != null else null
		if data == null:
			continue
		var lane := clampi(spec.lane, 0, lane_curves.size() - 1)
		var structure := _make_enemy(data, multiplier, lane, config.element_index(data.element), 0.0)
		structure.structure = true
		structure.phase = maxi(1, spec.phase)
		structure.closes_lanes = spec.closes_lanes
		structure.releases = spec.releases
		structure.release_health = spec.release_health
		structure.position = config.map.cell_center(spec.cell)
		structures.append(structure)
		_structure_cells[spec.cell] = structure
		if spec.footprint.has_area():
			for x in range(spec.footprint.position.x, spec.footprint.end.x):
				for y in range(spec.footprint.position.y, spec.footprint.end.y):
					if config.map.is_inside(Vector2i(x, y)) and not is_path(Vector2i(x, y)):
						_structure_cells[Vector2i(x, y)] = structure


func _on_structure_fallen(structure: SimEnemy) -> void:
	for lane in structure.closes_lanes:
		_closed_lanes[lane] = true
	# What comes out of a fallen building is as strong as the wave being fought.
	var multiplier := config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()
	for i in structure.releases.size():
		var data: EnemyData = config.enemies.get(structure.releases[i])
		if data == null:
			continue
		var released := _make_enemy(data, multiplier * structure.release_health, structure.lane, structure.element, 0.0)
		# They come out one after another: each waits a little behind the one before.
		released.progress = -90.0 * i
		_arrivals.append(released)
		if data.tags.has(&"boss"):
			boss_arrived.emit(released)
	for cell: Vector2i in _structure_cells.keys():
		if _structure_cells[cell] == structure:
			_structure_cells.erase(cell)
	structure_destroyed.emit(structure)
	var advanced := false
	while structure_phase <= total_phases() and structures_left(structure_phase).is_empty():
		structure_phase += 1
		advanced = true
	if structure_phase > total_phases():
		citadel_fallen = true
		# The horde breaks when its citadel falls: nothing more marches in, and whatever the last
		# building released is the final fight.
		_spawner.stop()
	if advanced:
		_recompute_towers()
		phase_changed.emit(structure_phase)


## True while anything released by the last building (the overlord) still walks.
func _overlord_alive() -> bool:
	for enemy in enemies:
		if enemy.alive and enemy.data.tags.has(&"overlord"):
			return true
	for enemy in _arrivals:
		if enemy.alive and enemy.data.tags.has(&"overlord"):
			return true
	return false


func _new_id() -> int:
	_next_id += 1
	return _next_id


# --- Heroes --------------------------------------------------------------------

## The element factor of a hit. Prismatic attackers (Seraphel, Oswin) always strike the element
## each enemy is weakest to.
func _element_multiplier(tower: SimTower, enemy: SimEnemy) -> float:
	if tower.tags.has(&"prismatic"):
		return ElementRules.OPPOSITE_ELEMENT_MULTIPLIER if enemy.element >= 0 else 1.0
	return ElementRules.damage_multiplier(tower.element_indices, enemy.element)


func hero_data(hero_id: StringName) -> HeroData:
	for hero in party:
		if hero.id == hero_id:
			return hero
	return null


## The summoned hero, or null while it is still waiting to be summoned.
func hero_tower(hero_id: StringName) -> SimTower:
	return _heroes_on_board.get(hero_id)


func hero_towers() -> Array[SimTower]:
	var result: Array[SimTower] = []
	for hero in party:
		if _heroes_on_board.has(hero.id):
			result.append(_heroes_on_board[hero.id])
	return result


## Pixels from a hero to the towers its aura reaches.
func hero_aura_radius() -> float:
	return HeroData.AURA_CELLS * config.map.cell_size


func _cell_error(cell: Vector2i) -> String:
	if not config.map.is_inside(cell):
		return "Outside the map"
	if is_path(cell):
		return "Heroes stand beside the road, not on it"
	if _landmark_cells.has(cell):
		return "The enemy's war camp stands here" if _landmark_cells[cell].kind == &"camp" else "The city stands here"
	if _tower_at.has(cell):
		return "There is already a tower here"
	return ""


## Why a hero cannot be summoned onto a cell, or an empty string if it can.
func summon_error(hero_id: StringName, cell: Vector2i) -> String:
	if is_over():
		return "The run is over"
	var hero := hero_data(hero_id)
	if hero == null:
		return "That hero is not in your party"
	if _heroes_on_board.has(hero_id):
		return "%s is already on the field" % hero.display_name
	return _cell_error(cell)


## Summons a hero onto a free cell, for free. Each hero comes once per run.
func summon_hero(hero_id: StringName, cell: Vector2i) -> SimTower:
	if not summon_error(hero_id, cell).is_empty():
		return null
	var hero := hero_data(hero_id)
	var indices: Array[int] = []
	for element_id in hero.attack.elements:
		indices.append(config.element_index(element_id))
	var tower := SimTower.new(_new_id(), hero.attack, cell, config.map.cell_center(cell), 0, indices)
	tower.hero = hero
	towers.append(tower)
	_tower_at[cell] = tower
	_heroes_on_board[hero_id] = tower
	_recompute_towers()
	hero_summoned.emit(tower)
	changed.emit()
	return tower


## Why a hero cannot march to a cell now, or an empty string if it can.
func move_error(tower: SimTower, cell: Vector2i) -> String:
	if is_over():
		return "The run is over"
	if tower == null or not tower.is_hero() or not towers.has(tower):
		return "Only heroes can move"
	if state != State.BUILDING and not rolls_on():
		return "Heroes can only move between waves"
	if tower.moved_this_break:
		return "%s has already moved this break" % tower.hero.display_name
	if cell == tower.cell:
		return "%s is already there" % tower.hero.display_name
	return _cell_error(cell)


## Marches a hero to a new cell. A hero can move once in each break.
func move_hero(tower: SimTower, cell: Vector2i) -> bool:
	if not move_error(tower, cell).is_empty():
		return false
	_tower_at.erase(tower.cell)
	tower.cell = cell
	tower.position = config.map.cell_center(cell)
	tower.moved_this_break = true
	_tower_at[cell] = tower
	_recompute_towers()
	hero_moved.emit(tower)
	changed.emit()
	return true


## Why the hero's ability cannot be used now, or an empty string if it can.
func hero_ability_error(hero_id: StringName) -> String:
	if is_over():
		return "The run is over"
	var hero := hero_data(hero_id)
	if hero == null:
		return "That hero is not in your party"
	var tower := hero_tower(hero_id)
	if tower == null:
		return "Summon %s first" % hero.display_name
	if state != State.WAVE:
		return "Abilities can only be used during a wave"
	if tower.ability_cooldown > 0.0:
		return "%s is ready in %d s" % [tower.hero_ability().display_name, ceili(tower.ability_cooldown)]
	return ""


## Uses a summoned hero's ability. `at` is the point picked for an aimed one. Returns false and
## does nothing if it cannot be used now.
func use_hero_ability(hero_id: StringName, at: Vector2 = Vector2.ZERO) -> bool:
	if not hero_ability_error(hero_id).is_empty():
		return false
	var tower := hero_tower(hero_id)
	var ability := tower.hero_ability()
	tower.ability_cooldown = ability.cooldown
	var radius := ability.radius_cells * config.map.cell_size
	var points := PackedVector2Array()
	match ability.target:
		HeroAbility.Target.AIMED:
			points.append(at)
		HeroAbility.Target.SELF:
			points.append(tower.position)
		HeroAbility.Target.CROWDS:
			points = crowded_points(ability.strikes, radius)
	var hits := 0
	var strikes := 1 if ability.target == HeroAbility.Target.CROWDS else maxi(1, ability.strikes)
	for strike in strikes:
		if ability.target == HeroAbility.Target.BOARD:
			for enemy in enemies:
				hits += _ability_hit(tower, ability, enemy)
		else:
			for point in points:
				for enemy in enemies:
					if enemy.position.distance_to(point) <= radius:
						hits += _ability_hit(tower, ability, enemy)
	if ability.burst_damage > 0.0:
		for point in points:
			_bursts.append([maxf(ability.hold_seconds, 0.1), point, radius, ability.burst_damage * _ability_growth(), tower])
	if ability.heal_lives > 0:
		lives = maxi(lives, mini(lives + ability.heal_lives, starting_lives))
	if ability.resets_skills:
		_skill_cooldowns.clear()
	if ability.resets_heroes:
		for other: SimTower in _heroes_on_board.values():
			if other != tower:
				other.ability_cooldown = 0.0
	if ability.duration > 0.0:
		_hero_effects.append([ability, ability.duration, tower])
		if ability.lives_per_kill > 0:
			_lives_from_kills = 0
		_refresh_modifiers()
	if points.is_empty():
		points.append(config.map.size_in_pixels() * 0.5)
	hero_ability_used.emit(tower, ability, points)
	changed.emit()
	return true


## Ability damage keeps pace with enemy health, as skill damage does.
func _ability_growth() -> float:
	return config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()


## One enemy struck by a hero's ability. Returns 1 if it was there to be hit.
func _ability_hit(tower: SimTower, ability: HeroAbility, enemy: SimEnemy) -> int:
	if not enemy.alive:
		return 0
	var boss := enemy.data.tags.has(&"boss")
	if ability.execute_below > 0.0 and not boss and enemy.health <= enemy.max_health * ability.execute_below:
		_damage(enemy, enemy.health + 1.0, tower)
		return 1
	var multiplier := _element_multiplier(tower, enemy)
	if ability.hits_weakness:
		multiplier = ElementRules.OPPOSITE_ELEMENT_MULTIPLIER if enemy.element >= 0 else 1.0
	if ability.damage > 0.0:
		var damage := ability.damage * _ability_growth() * (ability.boss_damage_multiplier if boss else 1.0)
		_damage(enemy, CombatMath.hit_damage(damage, multiplier, enemy.effective_armour(), enemy.damage_taken_bonus()), tower)
		if not enemy.alive:
			return 1
	for spec in ability.status_effects:
		var scaled := spec.duplicate() as StatusEffectData
		scaled.damage_per_second *= _ability_growth()
		enemy.apply_status(scaled, tower, multiplier)
	if ability.hold_seconds > 0.0:
		var hold := StatusEffectData.new()
		if boss:
			hold.kind = &"slow"
			hold.slow = 0.6
		else:
			hold.kind = &"root"
		hold.duration = ability.hold_seconds
		enemy.apply_status(hold, tower, multiplier)
	if ability.send_to_start and (ability.send_bosses or not boss):
		enemy.progress = 0.0
		enemy.position = lane_curves[enemy.lane].sample_baked(0.0)
	elif ability.knockback > 0.0 and enemy.knock_back(ability.knockback) > 0.0:
		enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)
	return 1


## Up to `count` points that each cover the most enemies within `radius`, no enemy counted twice.
func crowded_points(count: int, radius: float) -> PackedVector2Array:
	var result := PackedVector2Array()
	var taken: Dictionary[int, bool] = {}
	for i in count:
		var best := -1
		var best_point := Vector2.ZERO
		for enemy in enemies:
			if not enemy.alive or taken.has(enemy.id):
				continue
			var near := 0
			for other in enemies:
				if other.alive and not taken.has(other.id) and other.position.distance_to(enemy.position) <= radius:
					near += 1
			if near > best:
				best = near
				best_point = enemy.position
		if best <= 0:
			break
		result.append(best_point)
		for enemy in enemies:
			if enemy.position.distance_to(best_point) <= radius:
				taken[enemy.id] = true
	return result


func _tick_heroes(delta: float) -> void:
	for tower: SimTower in _heroes_on_board.values():
		tower.ability_cooldown = maxf(0.0, tower.ability_cooldown - delta)
	if not _hero_effects.is_empty():
		var running: Array[Array] = []
		for effect in _hero_effects:
			effect[1] -= delta
			if effect[1] > 0.0:
				running.append(effect)
		if running.size() != _hero_effects.size():
			_hero_effects = running
			_refresh_modifiers()
	if not _bursts.is_empty():
		var waiting: Array[Array] = []
		for burst in _bursts:
			burst[0] -= delta
			if burst[0] > 0.0:
				waiting.append(burst)
				continue
			for enemy in enemies:
				if enemy.alive and enemy.position.distance_to(burst[1]) <= burst[2]:
					_damage(enemy, CombatMath.hit_damage(burst[3], 1.0, enemy.effective_armour(), enemy.damage_taken_bonus()) * _spread_cut(enemy), burst[4])
		_bursts = waiting


## Kills pay this many times their gold while an ability such as Eclipse runs.
func gold_multiplier() -> float:
	var result := 1.0
	for effect in _hero_effects:
		result = maxf(result, (effect[0] as HeroAbility).gold_multiplier)
	return result


## True while an ability such as Last Light keeps enemies from leaking.
func is_warded() -> bool:
	for effect in _hero_effects:
		if (effect[0] as HeroAbility).ward:
			return true
	return false


## Seconds left on a hero's running ability, or 0.
func hero_effect_time(hero_id: StringName) -> float:
	var left := 0.0
	for effect in _hero_effects:
		if (effect[2] as SimTower).hero.id == hero_id:
			left = maxf(left, effect[1])
	return left


func _lives_for_kill() -> void:
	for effect in _hero_effects:
		var ability: HeroAbility = effect[0]
		if ability.lives_per_kill > 0 and _lives_from_kills < ability.lives_per_kill_max:
			var gain := mini(ability.lives_per_kill, ability.lives_per_kill_max - _lives_from_kills)
			_lives_from_kills += gain
			lives += gain
			return


## Every hero on the field gains a level for the wave it fought, and Elowen's aura gives lives back.
func _level_heroes() -> void:
	_hero_effects.clear()
	for tower: SimTower in _heroes_on_board.values():
		if tower.hero_level < HeroData.MAX_LEVEL:
			tower.hero_level += 1
			hero_leveled.emit(tower)
		var hero := tower.hero
		if hero.aura_lives_per_towers > 0:
			var near := 0
			for other in towers:
				if not other.is_hero() and other.position.distance_to(tower.position) <= hero_aura_radius():
					near += 1
			lives += mini(near / hero.aura_lives_per_towers, hero.aura_lives_max)
	_refresh_modifiers()


## Gives every tower the auras of the heroes near it, and every hero the levels Ilyra's aura adds.
func _apply_hero_auras() -> void:
	var bonus_levels := 0
	for tower: SimTower in _heroes_on_board.values():
		bonus_levels += tower.hero.aura_hero_levels
	var radius := hero_aura_radius()
	for tower in towers:
		tower.hero_aura.clear()
		if tower.is_hero():
			tower.hero_level_bonus = bonus_levels
			continue
		for hero: SimTower in _heroes_on_board.values():
			if not hero.hero.aura.is_empty() and hero.position.distance_to(tower.position) <= radius:
				tower.hero_aura.append_array(hero.hero.aura)


# ------------------------------------------------------------------ the six hordes' powers

## Share of spread-out damage (splash, chains, skills, bursts) that reaches it: less for a Geode Brute.
func _spread_cut(enemy: SimEnemy) -> float:
	if enemy.has_power and enemy.data.power == &"facets":
		return 1.0 - clampf(enemy.data.power_amount, 0.0, 0.95)
	return 1.0


## Auras the horde holds up every step: Runebearers lend armour, Menhir Walkers steady the ranks,
## Greenwitches turn poison to medicine, Voiceless hush the towers, Briarlings run faster in a pack, and
## the Spurred and the Juggernauts gain and lose their speed.
func _tick_horde_auras(delta: float) -> void:
	var bearers: Array[SimEnemy] = []
	for enemy in enemies:
		if not enemy.alive:
			continue
		enemy.bonus_armour = 0.0
		enemy.steady = false
		enemy.remedied = false
		enemy.swarm = 0.0
		if enemy.spur_left > 0.0:
			enemy.spur_left = maxf(0.0, enemy.spur_left - delta)
			if enemy.spur_left <= 0.0:
				enemy.spur = 0.0
		if enemy.has_power and enemy.downed <= 0.0:
			match enemy.data.power:
				&"bulwark", &"steadfast", &"remedy", &"hush", &"swarm":
					bearers.append(enemy)
				&"momentum":
					if enemy.is_slowed() or enemy.has_status(&"stun") or enemy.has_status(&"root"):
						enemy.momentum = 0.0
					else:
						enemy.momentum = minf(enemy.data.power_limit, enemy.momentum + enemy.data.power_amount * delta)
	for tower in towers:
		tower.hushed = false
	for bearer in bearers:
		var data := bearer.data
		var reach := data.power_radius * data.power_radius
		if data.power == &"hush":
			for tower in towers:
				if tower.position.distance_squared_to(bearer.position) <= reach:
					tower.hushed = true
			continue
		var pack := 0
		for other in enemies:
			if not other.alive or other.position.distance_squared_to(bearer.position) > reach:
				continue
			match data.power:
				&"bulwark":
					if other != bearer:
						other.bonus_armour = maxf(other.bonus_armour, data.power_amount)
				&"steadfast":
					other.steady = true
				&"remedy":
					other.remedied = true
				&"swarm":
					if other != bearer and other.data == data:
						pack += 1
		if data.power == &"swarm":
			bearer.swarm = minf(data.power_limit, data.power_amount * pack)


## A tower hit has landed on a living enemy: the powers that answer a blow.
func _struck(enemy: SimEnemy, tower: SimTower) -> void:
	if not enemy.has_power:
		return
	var data := enemy.data
	match data.power:
		&"accrete":
			if enemy.stacks < int(data.power_limit):
				enemy.stacks += 1
				enemy.armour += data.power_amount
				if enemy.stacks % 3 == 0 or enemy.stacks == int(data.power_limit):
					enemy_power.emit(enemy, &"accrete", [])
		&"meltdown":
			if enemy.armour > 0.0:
				enemy.armour = maxf(0.0, enemy.armour - data.power_amount)
				if enemy.armour <= 0.0:
					enemy_power.emit(enemy, &"meltdown", [])
		&"spur":
			enemy.spur = minf(data.power_limit, enemy.spur + data.power_amount)
			enemy.spur_left = data.power_duration
			if enemy.spur >= data.power_limit:
				enemy_power.emit(enemy, &"spur", [])


## The timed powers of the six hordes, once the power is ready (called from _tick_powers).
func _use_horde_power(enemy: SimEnemy) -> void:
	var data := enemy.data
	match data.power:
		&"douse":
			var washed: Array = []
			for ally in _allies_near(enemy, data.power_radius):
				var any := false
				for kind: StringName in ally.statuses.keys():
					var status: SimStatus = ally.statuses[kind]
					if kind == &"burn" or kind == &"poison" or status.slow > 0.0:
						ally.statuses.erase(kind)
						any = true
				if any:
					washed.append(ally)
			# It waits until someone is burning, poisoned or slowed.
			if not washed.is_empty():
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"douse", washed)
		&"net":
			var target := _strongest_tower_near(enemy.position, data.power_radius, true)
			if target != null:
				target.net = data.power_amount
				target.net_left = data.power_duration
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"net", [target])
		&"submerge":
			enemy.power_left = data.power_duration
			enemy.power_timer = data.power_interval + data.power_duration
			enemy.statuses.clear()
			enemy_power.emit(enemy, &"submerge", [])
		&"fog", &"eclipse":
			var hit: Array = []
			var reach := data.power_radius * data.power_radius
			for tower in towers:
				if tower.position.distance_squared_to(enemy.position) <= reach:
					if data.power == &"fog":
						tower.fog = data.power_amount
						tower.fog_left = data.power_duration
					else:
						tower.eclipse = data.power_amount
						tower.eclipse_left = data.power_duration
					hit.append(tower)
			if not hit.is_empty():
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, data.power, hit)
		&"rime_shell":
			if enemy.shell <= 0.0:
				enemy.shell = enemy.max_health * data.power_amount
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"rime_shell", [])
		&"charge":
			enemy.power_left = data.power_duration
			enemy.power_timer = data.power_interval + data.power_duration
			enemy.statuses.erase(&"slow")
			enemy_power.emit(enemy, &"charge", [])
		&"raise":
			var risen: Array = []
			var reach := data.power_radius * data.power_radius
			var keep: Array[Array] = []
			for dead in _fallen:
				if risen.size() < int(data.power_limit) and (dead[5] as Vector2).distance_squared_to(enemy.position) <= reach:
					var child := _make_enemy(dead[0], dead[1], dead[2], dead[4], dead[3])
					child.raised = true
					child.has_power = false
					child.shield_up = false
					child.shell = 0.0
					child.health = child.max_health * clampf(data.power_amount, 0.05, 1.0)
					_arrivals.append(child)
					risen.append(child)
				else:
					keep.append(dead)
			_fallen = keep
			if not risen.is_empty():
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"raise", risen)
		&"glass_ward":
			var warded: Array = []
			var allies := _allies_near(enemy, data.power_radius)
			# The ones furthest down the road first.
			allies.sort_custom(func(a: SimEnemy, b: SimEnemy) -> bool: return a.progress > b.progress)
			for ally in allies:
				if warded.size() >= int(data.power_limit):
					break
				if ally != enemy and not ally.shield_up and not ally.structure:
					ally.shield_up = true
					warded.append(ally)
			if not warded.is_empty():
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"glass_ward", warded)
		&"tailwind":
			var carried: Array = []
			for ally in _allies_near(enemy, data.power_radius):
				if ally.structure or ally.data.tags.has(&"boss"):
					continue
				var room := lane_lengths[ally.lane] - 64.0 - ally.progress
				var push := minf(data.power_amount, room)
				if push > 0.0:
					ally.progress += push
					ally.position = lane_curves[ally.lane].sample_baked(ally.progress)
					carried.append(ally)
			enemy.power_timer = data.power_interval
			enemy_power.emit(enemy, &"tailwind", carried)
		&"gust":
			var blown := 0
			var reach := data.power_radius * data.power_radius
			for shot in projectiles:
				if not shot.done and shot.position.distance_squared_to(enemy.position) <= reach:
					shot.done = true
					blown += 1
			if blown > 0:
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"gust", [])
		&"sow":
			enemy.power_timer = data.power_interval
			_seeds.append([data.power_duration, data.summon, maxi(1, roundi(data.power_amount)), enemy.lane, enemy.progress,
					enemy.element, enemy.health_multiplier])
			enemy_power.emit(enemy, &"sow", [])
		&"bound":
			if enemy.is_slowed():
				for kind: StringName in enemy.statuses.keys():
					if (enemy.statuses[kind] as SimStatus).slow > 0.0:
						enemy.statuses.erase(kind)
				var room := lane_lengths[enemy.lane] - 64.0 - enemy.progress
				var from := enemy.position
				enemy.progress += maxf(0.0, minf(data.power_amount, room))
				enemy.position = lane_curves[enemy.lane].sample_baked(enemy.progress)
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"bound", [from])
		&"grow":
			if enemy.stacks < int(data.power_limit):
				enemy.stacks += 1
				var more := data.max_health * enemy.health_multiplier * data.power_amount
				enemy.max_health += more
				enemy.health += more
				enemy.power_timer = data.power_interval
				enemy_power.emit(enemy, &"grow", [])


## A Seedsower's seeds sprout where they fell.
func _tick_seeds(delta: float) -> void:
	if _seeds.is_empty():
		return
	var left: Array[Array] = []
	for seed in _seeds:
		seed[0] -= delta
		if seed[0] > 0.0:
			left.append(seed)
			continue
		var data: EnemyData = config.enemies.get(seed[1])
		if data == null:
			continue
		var sprouts: Array = []
		for i in int(seed[2]):
			var child := _make_enemy(data, seed[6], _open_lane(seed[3]), seed[5], seed[4] - 10.0 * i)
			_arrivals.append(child)
			sprouts.append(child)
		enemy_power.emit(sprouts[0], &"sprout", sprouts)
	_seeds = left


## What a death sets off: a Wailing Widow's scream, a Spark Wisp's shock, a Voidmaw feeding, and the
## fallen remembered for a Gravecaller.
func _on_horde_death(enemy: SimEnemy, killer: SimTower) -> void:
	var data := enemy.data
	if enemy.has_power and data.power == &"wail":
		var hit: Array = []
		var reach := data.power_radius * data.power_radius
		for tower in towers:
			if tower.position.distance_squared_to(enemy.position) <= reach:
				tower.silenced = maxf(tower.silenced, data.power_duration)
				hit.append(tower)
		enemy_power.emit(enemy, &"wail", hit)
	if enemy.has_power and data.power == &"static" and killer != null:
		killer.silenced = maxf(killer.silenced, data.power_duration)
		enemy_power.emit(enemy, &"static", [killer])
	if enemy.structure or data.tags.has(&"boss"):
		return
	for other in enemies:
		if other.alive and other != enemy and other.has_power and other.data.power == &"devour" and other.downed <= 0.0 \
				and other.position.distance_squared_to(enemy.position) <= other.data.power_radius * other.data.power_radius:
			other.health = minf(other.max_health, other.health + other.max_health * other.data.power_amount)
			enemy_power.emit(other, &"devour", [enemy])
	if not enemy.raised:
		_fallen.append([data, enemy.health_multiplier, enemy.lane, enemy.progress, enemy.element, enemy.position, 0.0])
		if _fallen.size() > FALLEN_KEEP:
			_fallen.pop_front()


## Forgets the fallen once they have lain too long to raise.
func _age_fallen(delta: float) -> void:
	if _fallen.is_empty():
		return
	var fresh: Array[Array] = []
	for dead in _fallen:
		dead[6] += delta
		if dead[6] < FALLEN_FRESH:
			fresh.append(dead)
	_fallen = fresh


# --- The counter-attack ----------------------------------------------------------

## Every kind of unit the player can muster in this run, in panel order.
func ally_list() -> Array[AllyData]:
	var result: Array[AllyData] = []
	result.assign(config.allies.values())
	result.sort_custom(func(a: AllyData, b: AllyData) -> bool:
		return a.order < b.order if a.order != b.order else String(a.id) < String(b.id))
	return result


## How much a unit mustered now is grown: the wave's health growth, as skill damage is.
func muster_growth() -> float:
	return config.wave_set.health_multiplier(wave_number()) * config.enemy_health_multiplier()


func ally_price(ally_id: StringName) -> int:
	var data: AllyData = config.allies.get(ally_id)
	return data.cost if data != null else 0


## Seconds until another squad of this kind can be mustered. 0 when it can.
func muster_cooldown_left(ally_id: StringName) -> float:
	return _muster_cooldowns.get(ally_id, 0.0)


## Units of a kind on the field now.
func allies_alive(ally_id: StringName) -> int:
	var count := 0
	for ally in allies:
		if ally.alive and ally.data.id == ally_id:
			count += 1
	return count


## Why a squad cannot be mustered onto a road now, or an empty string if it can.
func muster_error(ally_id: StringName, lane: int = 0) -> String:
	if is_over():
		return "The run is over"
	if not is_counter_assault():
		return "Units are only mustered in the final assault"
	if not counter_started:
		return "Hold the line until the counter-attack (wave %d)" % config.stage.counter_wave
	var data: AllyData = config.allies.get(ally_id)
	if data == null:
		return "Unknown unit"
	if lane < 0 or lane >= lane_curves.size():
		return "No such road"
	if data.max_alive > 0 and allies_alive(ally_id) >= data.max_alive:
		return "%s is already on the field" % data.display_name
	var left := muster_cooldown_left(ally_id)
	if left > 0.0:
		return "%s is ready in %d s" % [data.display_name, ceili(left)]
	if gold < data.cost:
		return "Not enough gold"
	return ""


## Musters a squad onto a road: it marches out of our camp toward the citadel. Returns the units, or
## an empty list if it cannot be mustered now.
func muster(ally_id: StringName, lane: int = 0) -> Array[SimAlly]:
	var squad: Array[SimAlly] = []
	if not muster_error(ally_id, lane).is_empty():
		return squad
	var data: AllyData = config.allies[ally_id]
	gold -= data.cost
	_muster_cooldowns[ally_id] = data.cooldown
	var growth := muster_growth()
	for i in maxi(1, data.count):
		var ally := SimAlly.new(_new_id(), data, growth)
		ally.lane = lane
		ally.progress = maxf(0.0, lane_lengths[lane] - 12.0 - 22.0 * i)
		ally.position = lane_curves[lane].sample_baked(ally.progress)
		allies.append(ally)
		squad.append(ally)
	allies_mustered.emit(squad)
	changed.emit()
	return squad


## The road with the fewest enemies on it, for the bot and for a muster with no road picked.
func quietest_lane() -> int:
	var counts: Array[int] = []
	counts.resize(lane_curves.size())
	for enemy in enemies:
		if enemy.alive:
			counts[enemy.lane] += 1
	var best := 0
	for lane in counts.size():
		if not _closed_lanes.has(lane) and counts[lane] < counts[best]:
			best = lane
	return best


## The road whose end is nearest a point, for mustering where the player clicks.
func lane_near(at: Vector2) -> int:
	var best := 0
	var best_distance := INF
	for lane in lane_curves.size():
		var distance := lane_curves[lane].get_closest_point(at).distance_to(at)
		if distance < best_distance:
			best_distance = distance
			best = lane
	return best


## Units holding the road stop the enemies that walk into them. A unit holds a few at a time, and a
## boss only stops for a champion.
func _hold_the_road() -> void:
	for enemy in enemies:
		enemy.blocked_by = null
	for ally in allies:
		if not ally.alive or not ally.data.blocks or ally.data.flying:
			continue
		var limit := CHAMPION_HOLD_COUNT if ally.is_champion() else HOLD_COUNT
		var held := 0
		for enemy in enemies:
			if held >= limit:
				break
			if not enemy.alive or enemy.blocked_by != null or enemy.lane != ally.lane or enemy.untouchable():
				continue
			if enemy.data.tags.has(&"boss") and not ally.is_champion():
				continue
			var gap := ally.progress - enemy.progress
			if gap >= -CONTACT * 0.5 and gap <= CONTACT:
				enemy.blocked_by = ally
				held += 1


## Units fight, heal, march, and fall. Enemies strike the units holding them.
func _update_allies(delta: float) -> void:
	for cooldown_id: StringName in _muster_cooldowns.keys():
		_muster_cooldowns[cooldown_id] = maxf(0.0, _muster_cooldowns[cooldown_id] - delta)
	# The camp keeps the army supplied while it marches.
	_supply += config.stage.counter_income * delta
	if _supply >= 1.0:
		var paid := floori(_supply)
		_supply -= paid
		gold += paid
		gold_earned += paid
	if allies.is_empty():
		return
	_apply_banners()
	for enemy in enemies:
		if enemy.alive and enemy.blocked_by != null and enemy.blocked_by.alive:
			enemy.attack_timer -= delta
			if enemy.attack_timer <= 0.0:
				enemy.attack_timer += 1.0
				_wound(enemy.blocked_by, enemy_attack_damage(enemy))
	for ally in allies:
		if not ally.alive:
			continue
		if ally.data.heal_amount > 0.0 and ally.data.heal_interval > 0.0:
			ally.heal_timer -= delta
			if ally.heal_timer <= 0.0:
				ally.heal_timer += ally.data.heal_interval
				_heal_around(ally)
		ally.cooldown = maxf(0.0, ally.cooldown - delta)
		var target := _ally_target(ally)
		ally.fighting = target != null
		if target == null:
			ally.progress = maxf(0.0, ally.progress - ally.data.speed * delta)
			ally.position = lane_curves[ally.lane].sample_baked(ally.progress)
			continue
		ally.target = target
		if ally.cooldown <= 0.0:
			ally.cooldown = ally.data.attack_interval
			_ally_strike(ally, target)
	var standing: Array[SimAlly] = []
	for ally in allies:
		if ally.alive:
			standing.append(ally)
	allies = standing


## What a unit fights now: the enemy it holds or the nearest in its reach, else a building it can
## reach. Null while the road ahead is clear.
func _ally_target(ally: SimAlly) -> SimEnemy:
	if not ally.data.siege_only:
		var best: SimEnemy = null
		var best_distance := INF
		for enemy in _hash.query(ally.position, ally.data.attack_range):
			if enemy.structure:
				continue
			var distance := enemy.position.distance_squared_to(ally.position)
			if enemy.blocked_by == ally:
				distance = -1.0
			if distance < best_distance:
				best_distance = distance
				best = enemy
		if best != null:
			return best
	for structure in structures:
		if not is_vulnerable(structure):
			continue
		# Every road of the final assault starts at one of the citadel's gates: a unit at the gate, or
		# with the gate in its reach, strikes the citadel.
		if is_counter_assault() and ally.progress <= ally.data.attack_range + GATE_REACH:
			return structure
		if structure.position.distance_to(ally.position) <= ally.data.attack_range + BUILDING_REACH:
			return structure
	return null


## One blow, with its splash, chain and effects.
func _ally_strike(ally: SimAlly, target: SimEnemy) -> void:
	ally_attacked.emit(ally, target)
	var hit: Array[SimEnemy] = [target]
	if not target.structure:
		if ally.data.splash_radius > 0.0:
			for other in _hash.query(target.position, ally.data.splash_radius):
				if other != target and not other.structure:
					hit.append(other)
		var current := target
		for jump in ally.data.chain_count:
			var next: SimEnemy = null
			var best := INF
			for other in _hash.query(current.position, 140.0):
				if hit.has(other) or other.structure:
					continue
				var distance := other.position.distance_squared_to(current.position)
				if distance < best:
					best = distance
					next = other
			if next == null:
				break
			hit.append(next)
			current = next
	for enemy in hit:
		_ally_hit(ally, enemy, 1.0 if enemy == target else 0.6)


func _ally_hit(ally: SimAlly, enemy: SimEnemy, share: float) -> void:
	if not enemy.alive or enemy.untouchable():
		return
	if enemy.shield_up:
		enemy.shield_up = false
		enemy.power_timer = enemy.data.power_interval
		enemy_power.emit(enemy, &"block", [])
		return
	var elements: Array[int] = []
	if not ally.data.element.is_empty():
		elements.append(config.element_index(ally.data.element))
	var multiplier := ElementRules.damage_multiplier(elements, enemy.element)
	if ally.is_champion() and ally.data.element.is_empty():
		# Champions of the light strike each foe where it is weakest.
		multiplier = ElementRules.OPPOSITE_ELEMENT_MULTIPLIER if enemy.element >= 0 else 1.0
	var amount := ally.damage * share * (1.0 + ally.aura_bonus) * multiplier
	if enemy.structure:
		amount *= ally.data.siege_multiplier
	elif enemy.data.tags.has(&"boss"):
		amount *= ally.data.boss_multiplier
	amount = maxf(amount - enemy.effective_armour(), amount * ALLY_MIN_DAMAGE) * (1.0 + enemy.damage_taken_bonus())
	var before := enemy.health
	_damage(enemy, amount, null)
	ally.damage_dealt += maxf(0.0, before - maxf(enemy.health, 0.0))
	if not enemy.alive or enemy.structure:
		return
	if ally.data.slow > 0.0 and ally.data.slow_duration > 0.0:
		var slow := StatusEffectData.new()
		slow.kind = &"slow"
		slow.slow = ally.data.slow
		slow.duration = ally.data.slow_duration
		enemy.apply_status(slow, null, multiplier)
	if not ally.data.dot_kind.is_empty() and ally.dot_damage > 0.0:
		var dot := StatusEffectData.new()
		dot.kind = ally.data.dot_kind
		dot.damage_per_second = ally.dot_damage
		dot.duration = maxf(0.5, ally.data.dot_duration)
		enemy.apply_status(dot, null, multiplier)


## A banner's bonus to the units around it.
func _apply_banners() -> void:
	var bearers: Array[SimAlly] = []
	for ally in allies:
		ally.aura_bonus = 0.0
		if ally.alive and ally.data.aura_damage > 0.0:
			bearers.append(ally)
	for bearer in bearers:
		var reach := bearer.data.aura_radius * bearer.data.aura_radius
		for ally in allies:
			if ally != bearer and ally.position.distance_squared_to(bearer.position) <= reach:
				ally.aura_bonus = maxf(ally.aura_bonus, bearer.data.aura_damage)


func _heal_around(healer: SimAlly) -> void:
	var healed: Array[SimAlly] = []
	var reach := healer.data.heal_radius * healer.data.heal_radius
	for ally in allies:
		if ally.alive and ally.health < ally.max_health and ally.position.distance_squared_to(healer.position) <= reach:
			ally.health = minf(ally.max_health, ally.health + ally.max_health * healer.data.heal_amount)
			healed.append(ally)
	if not healed.is_empty():
		ally_healed.emit(healer, healed)


## Damage per blow an enemy deals to the unit holding it: one blow a second.
func enemy_attack_damage(enemy: SimEnemy) -> float:
	var base := enemy.data.attack_damage
	if base <= 0.0:
		base = 5.0 + 4.0 * minf(enemy.data.leak_damage, 10)
	return base * enemy.health_multiplier


## A unit takes a blow, less its armour.
func _wound(ally: SimAlly, amount: float) -> void:
	if not ally.alive:
		return
	ally.health -= maxf(amount - ally.data.armour, amount * ALLY_MIN_DAMAGE)
	if ally.health <= 0.0:
		ally.health = 0.0
		ally.alive = false
		for enemy in enemies:
			if enemy.blocked_by == ally:
				enemy.blocked_by = null
		ally_died.emit(ally)


## The citadel's spires strike the units that come near it.
func _tick_structure_defences(delta: float) -> void:
	for structure in structures:
		var data := structure.data
		if not is_vulnerable(structure) or data.bolt_interval <= 0.0 or data.bolt_damage <= 0.0:
			continue
		structure.bolt_timer -= delta
		if structure.bolt_timer > 0.0:
			continue
		structure.bolt_timer += data.bolt_interval
		var near: Array[SimAlly] = []
		var reach := data.bolt_radius * data.bolt_radius
		for ally in allies:
			if ally.alive and ally.position.distance_squared_to(structure.position) <= reach:
				near.append(ally)
		if near.is_empty():
			continue
		var at := structure.position
		near.sort_custom(func(a: SimAlly, b: SimAlly) -> bool: return a.position.distance_squared_to(at) < b.position.distance_squared_to(at))
		var struck: Array[SimAlly] = []
		for i in mini(maxi(1, data.bolt_count), near.size()):
			struck.append(near[i])
		citadel_struck.emit(structure, struck)
		for ally in struck:
			_wound(ally, data.bolt_damage * structure.health_multiplier)
