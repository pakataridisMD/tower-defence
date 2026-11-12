class_name StoryOverlay
extends Control
## The story on top of a run: a banner when a boss walks in (with its portrait, name and tricks), a
## health bar for the strongest boss on the board, the city being defended, and in an assault the
## objective of the current movement and the countdown to the next wave.

const BANNER_TIME := 5.0
const BANNER_SIZE := Vector2(720, 132)
const BAR_WIDTH := 720.0
## The board's area on screen, matching Game.BOARD_OFFSET and the map size.
const BOARD_LEFT := 24.0
const BOARD_TOP := 96.0

var sim: RunSim
var story: Story

var _font: Font
## Bosses waiting for their banner, first one next, and the one being shown.
var _banners: Array[SimEnemy] = []
var _banner: SimEnemy
var _banner_time := 0.0
## The banner's picture, loaded when it appears (a texture first loaded inside _draw shows blank).
var _banner_picture: Texture2D
var _banner_is_portrait := false
## Boss enemy ids already announced in this run: a boss is announced once.
var _announced: Dictionary[StringName, bool] = {}
## A big line of text across the board, such as the city being defended or a building falling.
var _headline := ""
var _subline := ""
var _headline_color := UiStyle.GOLD
var _headline_time := 0.0
## The citadel's bar in the counter-attack: the share of health shown by the pale trail behind the red
## (it eases down after each blow, so the damage shows), and a flash when it is struck.
var _citadel_trail := 1.0
var _citadel_last := 1.0
var _citadel_flash := 0.0


func setup(p_sim: RunSim, p_story: Story) -> void:
	sim = p_sim
	story = p_story
	_font = ThemeDB.fallback_font
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	sim.boss_arrived.connect(_on_boss_arrived)
	sim.structure_destroyed.connect(_on_structure_destroyed)
	sim.enemy_transformed.connect(func(enemy: SimEnemy, _from: EnemyData) -> void:
		headline("%s rises" % enemy.data.display_name, "Form %d of 3" % (enemy.form + 1), UiStyle.BAD))
	sim.counter_attack_started.connect(func() -> void:
		headline("The roles turn", "Muster your army (1-0, Tab, R) and break the citadel. Your towers hold the camp.", UiStyle.GOLD))
	sim.enemy_escaped.connect(func(enemy: SimEnemy) -> void:
		headline("%s escapes!" % enemy.data.display_name, "Beaten, but not finished.", UiStyle.BAD))
	var stage := sim.config.stage
	if stage != null:
		var city := story.city(stage.id)
		if not city.is_empty():
			var line := "Hold the road. Its people are behind you."
			if bool(city.get("capital", false)):
				line = "The capital. It must not fall."
			elif not bool(city.get("saved", true)):
				line = "Hold the wall as long as it stands."
			headline("Defend %s" % city.get("name", ""), line)
		if sim.is_assault():
			var first := story.assault_movement(1)
			headline(stage.display_name, str(first.get("name", "")))


## Shows a line across the board for a few seconds.
func headline(text: String, sub: String = "", color: Color = UiStyle.GOLD) -> void:
	_headline = text
	_subline = sub
	_headline_color = color
	_headline_time = 4.0


## The boss shown on the banner now, or null.
func banner_boss() -> SimEnemy:
	return _banner


func _on_boss_arrived(enemy: SimEnemy) -> void:
	if _announced.has(enemy.data.id):
		return
	_announced[enemy.data.id] = true
	_banners.append(enemy)


func _on_structure_destroyed(structure: SimEnemy) -> void:
	var next := story.assault_movement(sim.structure_phase)
	if sim.is_counter_assault() and sim.citadel_fallen:
		headline("%s falls!" % structure.data.display_name, "The root of the horde is torn out.", UiStyle.GOOD)
	elif sim.citadel_fallen:
		headline("%s is broken!" % structure.data.display_name, "Finish what came out of it.", UiStyle.GOOD)
	elif not next.is_empty() and structure.phase < sim.structure_phase:
		headline("%s falls!" % structure.data.display_name, "Next: %s. The ground you hold moves east." % next.get("name", ""), UiStyle.GOOD)
	else:
		headline("%s falls!" % structure.data.display_name, "", UiStyle.GOOD)


func _process(delta: float) -> void:
	if sim == null:
		return
	_headline_time = maxf(0.0, _headline_time - delta)
	if _banner != null:
		_banner_time -= delta
		if _banner_time <= 0.0:
			_banner = null
	var citadel := citadel_under_attack()
	if citadel != null:
		var share := clampf(citadel.health / citadel.max_health, 0.0, 1.0)
		if share < _citadel_last - 0.0001:
			_citadel_flash = 1.0
		_citadel_last = share
		_citadel_trail = maxf(share, move_toward(_citadel_trail, share, delta * 0.1))
		_citadel_flash = maxf(0.0, _citadel_flash - delta * 3.0)
	if _banner == null and not _banners.is_empty():
		_banner = _banners.pop_front()
		_load_banner_picture()
		_banner_time = BANNER_TIME
	queue_redraw()


# --- Drawing ---------------------------------------------------------------------

func _draw() -> void:
	if sim == null:
		return
	_draw_boss_bar()
	_draw_citadel_bar()
	if sim.is_assault() and not sim.is_over():
		_draw_objective()
	if _headline_time > 0.0 and _banner == null:
		_draw_headline()
	if _banner != null:
		_draw_banner()


func _character(enemy: SimEnemy) -> Dictionary:
	return story.character_for_enemy(enemy.data.id) if story != null else {}


## The final level in acts: hold the camp, break the High King, then take the citadel.
func _counter_objective(movement: Dictionary, lines: PackedStringArray) -> void:
	var stage := sim.config.stage
	var act := sim.structure_phase
	lines.append("%s  (act %d of 3)" % [movement.get("name", "Act %d" % act), mini(act, 3)] if act <= 3 else str(movement.get("name", "")))
	match act:
		1:
			lines.append("Hold the camp: wave %d of %d" % [sim.wave_number(), stage.boss_wave - 1])
		2:
			var king := sim.strongest_boss()
			if king != null:
				lines.append("Break %s (form %d of 3)" % [king.data.display_name, king.form + 1])
			else:
				lines.append(str(movement.get("objective", "")))
		3:
			for structure in sim.structures_left(3):
				lines.append("Bring down %s: %d%%" % [structure.data.display_name, ceili(100.0 * structure.health / structure.max_health)])
		_:
			lines.append(str(movement.get("objective", "")))


func _draw_boss_bar() -> void:
	var boss := sim.strongest_boss()
	if boss == null or sim.is_over():
		return
	var person := _character(boss)
	var name := str(person.get("name", boss.data.display_name))
	var left := BOARD_LEFT + (1536.0 - BAR_WIDTH) * 0.5
	var top := BOARD_TOP + 12.0
	draw_rect(Rect2(left - 4, top - 4, BAR_WIDTH + 8, 46), Color(0, 0, 0, 0.6))
	var fill := clampf(boss.health / boss.max_health, 0.0, 1.0)
	var color := sim.config.element_color_at(boss.element).lerp(UiStyle.BAD, 0.4)
	draw_rect(Rect2(left, top + 22, BAR_WIDTH, 14), Color(0.15, 0.12, 0.18))
	draw_rect(Rect2(left, top + 22, BAR_WIDTH * fill, 14), color)
	var states: PackedStringArray = []
	if boss.enraged:
		states.append("ENRAGED")
	if boss.data.ward_radius > 0.0:
		states.append("shielding")
	var label := name + ("   " + "  ·  ".join(states) if not states.is_empty() else "")
	draw_string_outline(_font, Vector2(left, top + 16), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, 4, Color.BLACK)
	draw_string(_font, Vector2(left, top + 16), label, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, UiStyle.TEXT)
	var percent := "%d%%" % ceili(fill * 100.0)
	draw_string(_font, Vector2(left + BAR_WIDTH - 50, top + 16), percent, HORIZONTAL_ALIGNMENT_LEFT, -1, 18, UiStyle.TEXT_DIM)


## The citadel the army is breaking in the counter-attack, or null before it can be hurt or once it falls.
func citadel_under_attack() -> SimEnemy:
	if not sim.is_counter_assault() or sim.is_over():
		return null
	for structure in sim.structures:
		if structure.alive and sim.is_vulnerable(structure):
			return structure
	return null


## A long bar across the top of the board for the citadel while the army breaks it: its name, its
## health in numbers, a notch every quarter, the damage just done in a pale trail, and a flash when
## it is struck. The boss bar takes the place when a boss is on the board.
func _draw_citadel_bar() -> void:
	var citadel := citadel_under_attack()
	if citadel == null or sim.strongest_boss() != null:
		return
	var width := BAR_WIDTH + 120.0
	var left := BOARD_LEFT + (1536.0 - width) * 0.5
	var top := BOARD_TOP + 10.0
	var share := clampf(citadel.health / citadel.max_health, 0.0, 1.0)
	var shake := Vector2(sin(Time.get_ticks_msec() * 0.09) * 2.0 * _citadel_flash, 0)
	var frame := Rect2(Vector2(left - 6, top - 6) + shake, Vector2(width + 12, 58))
	draw_rect(frame, Color(0.03, 0.02, 0.05, 0.78))
	draw_rect(frame, Color(0.75, 0.22, 0.28, 0.85), false, 2.0)
	var bar := Rect2(Vector2(left, top + 26) + shake, Vector2(width, 18))
	draw_rect(bar, Color(0.16, 0.08, 0.12))
	draw_rect(Rect2(bar.position, Vector2(width * _citadel_trail, bar.size.y)), Color(1.0, 0.86, 0.75, 0.75))
	var red := UiStyle.BAD.lerp(Color(1.0, 0.95, 0.9), _citadel_flash * 0.6)
	draw_rect(Rect2(bar.position, Vector2(width * share, bar.size.y)), red)
	draw_rect(Rect2(bar.position, Vector2(width * share, 4)), Color(1, 1, 1, 0.18))
	for q in [0.25, 0.5, 0.75]:
		draw_rect(Rect2(bar.position + Vector2(width * q - 1, 0), Vector2(2, bar.size.y)), Color(0, 0, 0, 0.6))
	var name := citadel.data.display_name.to_upper()
	draw_string_outline(_font, Vector2(left, top + 17) + shake, name, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, 4, Color.BLACK)
	draw_string(_font, Vector2(left, top + 17) + shake, name, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color(1.0, 0.82, 0.78))
	var army := 0
	for ally in sim.allies:
		if ally.alive:
			army += 1
	var numbers := "Your army: %d     %s / %s   %d%%" % [army, _thousands(ceili(maxf(0.0, citadel.health))),
		_thousands(ceili(citadel.max_health)), ceili(share * 100.0)]
	var numbers_width := _font.get_string_size(numbers, HORIZONTAL_ALIGNMENT_LEFT, -1, 16).x
	draw_string(_font, Vector2(left + width - numbers_width, top + 17) + shake, numbers, HORIZONTAL_ALIGNMENT_LEFT, -1, 16, UiStyle.TEXT)


static func _thousands(value: int) -> String:
	var text := str(value)
	var out := ""
	while text.length() > 3:
		out = "," + text.right(3) + out
		text = text.left(text.length() - 3)
	return text + out


func _draw_objective() -> void:
	var movement := story.assault_movement(sim.structure_phase)
	var lines: PackedStringArray = []
	if sim.is_counter_assault():
		_counter_objective(movement, lines)
	elif sim.citadel_fallen:
		lines.append("The citadel is broken. Unmake the Sunderer!")
	else:
		var title := str(movement.get("name", "Phase %d" % sim.structure_phase))
		lines.append("%s  (%d of %d)" % [title, sim.structure_phase, sim.total_phases()])
		for structure in sim.structures_left(sim.structure_phase):
			lines.append("Bring down %s: %d%%" % [structure.data.display_name, ceili(100.0 * structure.health / structure.max_health)])
	if sim.state == RunSim.State.BUILDING and sim.break_time_left >= 0.0:
		lines.append("Next wave in %d s (Space: now)" % ceili(sim.break_time_left))
	elif sim.state == RunSim.State.WAVE and sim.rolls_on() and sim.next_wave_in() > 0.0:
		lines.append("Next wave in %d s" % ceili(sim.next_wave_in()))
	var top := BOARD_TOP + (64.0 if sim.strongest_boss() != null or citadel_under_attack() != null else 12.0)
	var height := 12.0 + lines.size() * 26.0
	draw_rect(Rect2(BOARD_LEFT + 12, top, 470, height), Color(0, 0, 0, 0.55))
	for i in lines.size():
		var color := UiStyle.GOLD if i == 0 else UiStyle.TEXT
		draw_string(_font, Vector2(BOARD_LEFT + 24, top + 28 + i * 26), lines[i], HORIZONTAL_ALIGNMENT_LEFT, -1, 19 if i == 0 else 17, color)


func _draw_headline() -> void:
	var alpha := clampf(_headline_time / 0.6, 0.0, 1.0) * clampf((4.0 - _headline_time) / 0.3, 0.0, 1.0)
	var center := Vector2(BOARD_LEFT + 768.0, BOARD_TOP + 300.0)
	var width := _font.get_string_size(_headline, HORIZONTAL_ALIGNMENT_LEFT, -1, 54).x
	draw_rect(Rect2(0, center.y - 64, size.x, 110 if not _subline.is_empty() else 84), Color(0, 0, 0, 0.45 * alpha))
	draw_string_outline(_font, Vector2(center.x - width * 0.5, center.y), _headline, HORIZONTAL_ALIGNMENT_LEFT, -1, 54, 8, Color(0, 0, 0, alpha))
	draw_string(_font, Vector2(center.x - width * 0.5, center.y), _headline, HORIZONTAL_ALIGNMENT_LEFT, -1, 54, Color(_headline_color, alpha))
	if not _subline.is_empty():
		var sub_width := _font.get_string_size(_subline, HORIZONTAL_ALIGNMENT_LEFT, -1, 22).x
		draw_string(_font, Vector2(center.x - sub_width * 0.5, center.y + 36), _subline, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, Color(UiStyle.TEXT, alpha))


## A boss's entrance: its portrait (or its board picture), name, title and what it does.
func _draw_banner() -> void:
	var t := BANNER_TIME - _banner_time
	var slide := clampf(t / 0.35, 0.0, 1.0) * clampf(_banner_time / 0.35, 0.0, 1.0)
	var top_left := Vector2(BOARD_LEFT + (1536.0 - BANNER_SIZE.x) * 0.5, lerpf(-BANNER_SIZE.y, BOARD_TOP + 70.0, slide))
	var rect := Rect2(top_left, BANNER_SIZE)
	var person := _character(_banner)
	var color := sim.config.element_color_at(_banner.element)
	draw_rect(rect, Color(0.06, 0.05, 0.09, 0.92))
	draw_rect(rect, Color(color, 0.9), false, 3.0)
	draw_rect(Rect2(rect.position + Vector2(0, rect.size.y - 6), Vector2(rect.size.x, 6)), Color(color, 0.6))
	var picture_rect := Rect2(rect.position + Vector2(14, 14), Vector2(104, 104))
	draw_rect(picture_rect, Color(0, 0, 0, 0.6))
	if _banner_picture != null and _banner_is_portrait:
		draw_texture_rect(_banner_picture, picture_rect, false)
	elif _banner_picture != null:
		var frame := _banner_picture
		var fit := minf(picture_rect.size.x / frame.get_width(), picture_rect.size.y / frame.get_height())
		var drawn := frame.get_size() * (floorf(fit) if fit >= 1.0 else fit)
		draw_texture_rect(frame, Rect2(picture_rect.get_center() - drawn * 0.5, drawn), false, color.lerp(Color.WHITE, 0.3))
	var name := str(person.get("name", _banner.data.display_name))
	var title := str(person.get("title", ""))
	var x := rect.position.x + 136
	draw_string(_font, Vector2(x, rect.position.y + 40), "BOSS", HORIZONTAL_ALIGNMENT_LEFT, -1, 15, Color(UiStyle.BAD, 0.9))
	draw_string(_font, Vector2(x, rect.position.y + 72), name, HORIZONTAL_ALIGNMENT_LEFT, -1, 32, UiStyle.GOLD)
	if not title.is_empty():
		var name_width := _font.get_string_size(name, HORIZONTAL_ALIGNMENT_LEFT, -1, 32).x
		draw_string(_font, Vector2(x + name_width + 14, rect.position.y + 72), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, UiStyle.TEXT_DIM)
	var words := _banner.data.trait_words()
	draw_string(_font, Vector2(x, rect.position.y + 104), _sentence(", ".join(words)), HORIZONTAL_ALIGNMENT_LEFT, BANNER_SIZE.x - 150, 18, UiStyle.TEXT)


func _load_banner_picture() -> void:
	_banner_picture = null
	_banner_is_portrait = false
	if _banner == null:
		return
	var person := _character(_banner)
	if not person.is_empty():
		_banner_picture = Story.portrait(StringName(str(person.get("id", ""))))
		_banner_is_portrait = _banner_picture != null
	if _banner_picture == null:
		var path := BoardArt.ART + "enemies/%s_0.png" % _banner.data.id
		_banner_picture = load(path) if ResourceLoader.exists(path) else null


static func _sentence(text: String) -> String:
	return text.substr(0, 1).to_upper() + text.substr(1) if not text.is_empty() else ""
