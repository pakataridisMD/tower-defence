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
## Boss enemy ids already announced in this run: a boss is announced once.
var _announced: Dictionary[StringName, bool] = {}
## A big line of text across the board, such as the city being defended or a building falling.
var _headline := ""
var _subline := ""
var _headline_color := UiStyle.GOLD
var _headline_time := 0.0


func setup(p_sim: RunSim, p_story: Story) -> void:
	sim = p_sim
	story = p_story
	_font = ThemeDB.fallback_font
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	sim.boss_arrived.connect(_on_boss_arrived)
	sim.structure_destroyed.connect(_on_structure_destroyed)
	sim.enemy_escaped.connect(func(enemy: SimEnemy) -> void:
		headline("%s escapes!" % enemy.data.display_name, "Beaten, but not finished.", UiStyle.BAD))
	var stage := sim.config.stage
	if stage != null:
		var city := story.city(stage.id)
		if not city.is_empty():
			var saved: bool = city.get("saved", false)
			headline("Defend %s" % city.get("name", ""), "The last city. It must not fall." if saved \
					else "Hold the road until its people are away.")
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
	if sim.citadel_fallen:
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
	if _banner == null and not _banners.is_empty():
		_banner = _banners.pop_front()
		_banner_time = BANNER_TIME
	queue_redraw()


# --- Drawing ---------------------------------------------------------------------

func _draw() -> void:
	if sim == null:
		return
	_draw_boss_bar()
	if sim.is_assault() and not sim.is_over():
		_draw_objective()
	if _headline_time > 0.0 and _banner == null:
		_draw_headline()
	if _banner != null:
		_draw_banner()


func _character(enemy: SimEnemy) -> Dictionary:
	return story.character_for_enemy(enemy.data.id) if story != null else {}


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


func _draw_objective() -> void:
	var movement := story.assault_movement(sim.structure_phase)
	var lines: PackedStringArray = []
	if sim.citadel_fallen:
		lines.append("The citadel is broken. Unmake the Sunderer!")
	else:
		var title := str(movement.get("name", "Phase %d" % sim.structure_phase))
		lines.append("%s  (%d of %d)" % [title, sim.structure_phase, sim.total_phases()])
		for structure in sim.structures_left(sim.structure_phase):
			lines.append("Bring down %s: %d%%" % [structure.data.display_name, ceili(100.0 * structure.health / structure.max_health)])
	if sim.state == RunSim.State.BUILDING and sim.break_time_left >= 0.0:
		lines.append("Next wave in %d s (Space: now)" % ceili(sim.break_time_left))
	var top := BOARD_TOP + (64.0 if sim.strongest_boss() != null else 12.0)
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
	var portrait := Story.portrait(StringName(str(person.get("id", "")))) if not person.is_empty() else null
	var picture_rect := Rect2(rect.position + Vector2(14, 14), Vector2(104, 104))
	draw_rect(picture_rect, Color(0, 0, 0, 0.6))
	if portrait != null:
		draw_texture_rect(portrait, picture_rect, false)
	else:
		var frame: Texture2D = load(BoardArt.ART + "enemies/%s_0.png" % _banner.data.id) \
				if ResourceLoader.exists(BoardArt.ART + "enemies/%s_0.png" % _banner.data.id) else null
		if frame != null:
			var fit := minf(picture_rect.size.x / frame.get_width(), picture_rect.size.y / frame.get_height())
			var drawn := frame.get_size() * floorf(maxf(1.0, fit))
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


static func _sentence(text: String) -> String:
	return text.substr(0, 1).to_upper() + text.substr(1) if not text.is_empty() else ""
