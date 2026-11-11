class_name CampaignScreen
extends Control
## The campaign map: the element ring as a star chart. Each element's campaign runs down a spoke
## from the rim toward the centre, one gem per stage, ending at its corrupted Warden. The spokes
## meet in the middle at the Convergence, which opens once all six are done.
##
## Click a stage to read about it, then Begin. Esc goes back to the main menu.

const MENU_SCENE := "res://scenes/main.tscn"
const GAME_SCENE := "res://scenes/game/game.tscn"
const CENTER := Vector2(650, 548)
## Distance from the centre of the first and the last stage of an element campaign.
const OUTER := 395.0
const INNER := 160.0
## The Convergence's first stages sit this far from the centre; its last stage is the centre.
const CONVERGE_RADIUS := 82.0
const ASSAULT_SPOT := Vector2(1150, 120)
const PANEL_LEFT := 1290.0
const GROUND_ART := "res://assets/art/game/ground/%s.png"

## The stage shown in the side panel.
var selected: StringName = &""

var _font: Font
var _elements: Dictionary[StringName, ElementData] = {}
var _positions: Dictionary[StringName, Vector2] = {}
var _hovered: StringName = &""
var _time := 0.0

var _panel: PanelContainer
var _campaign_title: RichTextLabel
var _stage_title: Label
var _story: Label
var _preview: TextureRect
var _details: RichTextLabel
var _begin: Button
var _party_title: Label
var _party_grid: GridContainer
var _party_buttons: Dictionary[StringName, KeyButton] = {}


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UiStyle.make_theme()
	_font = ThemeDB.fallback_font
	for element: ElementData in DataRegistry.elements.values():
		_elements[element.id] = element
	_layout()
	_build_panel()
	var meta := Progress.meta
	var start := Progress.active_stage
	if start.is_empty() or not DataRegistry.stages.has(start):
		start = _first_open_stage()
	select(start)


func _process(delta: float) -> void:
	_time += delta
	queue_redraw()


## Where each stage's gem goes.
func _layout() -> void:
	for campaign in Progress.meta.campaigns_in_order():
		var count := campaign.stages.size()
		if _is_assault(campaign):
			# The assault on the enemy citadel sits apart, in the top right corner.
			for i in count:
				_positions[campaign.stages[i].id] = ASSAULT_SPOT + Vector2(0, 90 * i)
			continue
		if campaign.element.is_empty():
			for i in count:
				var at := CENTER
				if i < count - 1:
					var angle := PI * 0.5 + TAU * (i + 0.5) / maxf(1.0, count - 1.0)
					at = CENTER + Vector2.from_angle(angle) * CONVERGE_RADIUS
				_positions[campaign.stages[i].id] = at
			continue
		var direction := _spoke(campaign.element)
		for i in count:
			var t := float(i) / maxf(1.0, count - 1.0)
			_positions[campaign.stages[i].id] = CENTER + direction * lerpf(OUTER, INNER, t)


func _spoke(element_id: StringName) -> Vector2:
	var element: ElementData = _elements.get(element_id)
	var index := element.ring_index if element != null else 0
	return Vector2.from_angle(-PI / 2.0 + TAU * index / ElementData.RING_SIZE)


func _first_open_stage() -> StringName:
	for campaign in Progress.meta.campaigns_in_order():
		var stage := Progress.meta.next_stage(campaign)
		if stage != null:
			return stage.id
	var campaigns := Progress.meta.campaigns_in_order()
	return campaigns[0].stages[0].id if not campaigns.is_empty() else &""


# --- Side panel ------------------------------------------------------------------

func _build_panel() -> void:
	_panel = PanelContainer.new()
	_panel.position = Vector2(PANEL_LEFT, 40)
	_panel.custom_minimum_size = Vector2(1880 - PANEL_LEFT, 1000)
	_panel.size = _panel.custom_minimum_size
	add_child(_panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	_panel.add_child(column)
	_campaign_title = RichTextLabel.new()
	_campaign_title.bbcode_enabled = true
	_campaign_title.fit_content = true
	_campaign_title.scroll_active = false
	_campaign_title.add_theme_font_size_override("normal_font_size", 20)
	column.add_child(_campaign_title)
	_stage_title = UiStyle.label("", 34)
	column.add_child(_stage_title)
	_story = UiStyle.label("", 18, UiStyle.TEXT_DIM)
	_story.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_story.custom_minimum_size = Vector2(540, 0)
	column.add_child(_story)
	_preview = TextureRect.new()
	_preview.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_preview.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_preview.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_preview.custom_minimum_size = Vector2(540, 230)
	column.add_child(_preview)
	_details = RichTextLabel.new()
	_details.bbcode_enabled = true
	_details.fit_content = true
	_details.scroll_active = false
	_details.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_details.add_theme_font_size_override("normal_font_size", 17)
	_details.add_theme_font_size_override("bold_font_size", 17)
	column.add_child(_details)
	_build_party(column)
	var buttons := HBoxContainer.new()
	buttons.add_theme_constant_override("separation", 12)
	column.add_child(buttons)
	_begin = UiStyle.button("Begin stage", 26)
	_begin.custom_minimum_size = Vector2(300, 60)
	_begin.pressed.connect(begin)
	buttons.add_child(_begin)
	var back := UiStyle.button("Back (Esc)", 20)
	back.custom_minimum_size = Vector2(200, 60)
	back.pressed.connect(back_to_menu)
	buttons.add_child(back)


## The heroes who have joined, to pick the party from. Gold frames mark the ones going.
func _build_party(column: VBoxContainer) -> void:
	_party_title = UiStyle.label("", 20)
	column.add_child(_party_title)
	_party_grid = GridContainer.new()
	_party_grid.columns = 8
	_party_grid.add_theme_constant_override("h_separation", 6)
	_party_grid.add_theme_constant_override("v_separation", 6)
	column.add_child(_party_grid)
	for hero in Progress.meta.heroes_in_order():
		var hero_id := hero.id
		var button := UiStyle.key_button("", 14)
		button.icon = Hud.hero_portrait(hero_id)
		button.expand_icon = true
		button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		button.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		button.custom_minimum_size = Vector2(60, 60)
		button.pressed.connect(func() -> void:
			Progress.toggle_party_hero(hero_id)
			SoundPlayer.sfx(&"ui_toggle")
			_refresh_party())
		_party_grid.add_child(button)
		_party_buttons[hero_id] = button
	_refresh_party()


func _refresh_party() -> void:
	var meta := Progress.meta
	var party := meta.party()
	var joined := meta.joined_heroes()
	_party_title.text = "Heroes  ·  pick up to %d  ·  F1-F3 in a run" % HeroData.MAX_PARTY
	for hero in meta.heroes_in_order():
		var button := _party_buttons[hero.id]
		var has_joined := joined.has(hero)
		button.visible = has_joined
		var slot := party.find(hero)
		button.outline = UiStyle.GOLD if slot >= 0 else Color(0, 0, 0, 0)
		button.key_text = "F%d" % (slot + 1) if slot >= 0 else ""
		button.modulate = Color.WHITE if slot >= 0 else Color(1, 1, 1, 0.6)
		button.tooltip_text = "%s, %s\n%s\n%s" % [hero.display_name, hero.title, hero.blurb,
				"In the party. Click to leave behind." if slot >= 0 else "Click to bring."]


func select(stage_id: StringName) -> void:
	var stage: StageData = DataRegistry.stages.get(stage_id)
	if stage == null:
		return
	selected = stage_id
	var meta := Progress.meta
	var campaign := DataRegistry.campaign_of(stage_id)
	var color := _campaign_color(campaign)
	var index := campaign.stage_index(stage_id)
	_campaign_title.text = "[color=#%s][b]%s[/b][/color]  ·  %s  ·  stage %d of %d" % [
		color.to_html(false), campaign.display_name, campaign.tagline, index + 1, campaign.stages.size()]
	_stage_title.text = stage.display_name + ("  ·  Warden" if stage.is_guardian else "")
	_story.text = stage.description
	var map: MapData = DataRegistry.maps.get(stage.map)
	_preview.texture = load(GROUND_ART % stage.map) if map != null and ResourceLoader.exists(GROUND_ART % stage.map) else null
	_details.text = _details_text(stage, campaign)
	var unlocked := meta.is_stage_unlocked(stage_id)
	_begin.disabled = not unlocked
	_begin.text = "Begin stage" if meta.stars(stage_id) == 0 else "Play again"
	if not unlocked:
		_begin.text = "Locked"
	queue_redraw()


func _details_text(stage: StageData, campaign: CampaignData) -> String:
	var meta := Progress.meta
	var lines: PackedStringArray = []
	var wave_set := _wave_set(stage)
	var stars := meta.stars(stage.id)
	var star_text := "[color=#%s]%s[/color][color=#5a6275]%s[/color]" % [
		UiStyle.GOLD.to_html(false), "★".repeat(stars), "★".repeat(3 - stars)]
	lines.append("%s   %d waves%s" % [star_text, wave_set.waves.size() if wave_set != null else 0,
		"  ·  %d roads" % DataRegistry.maps[stage.map].lane_count() if DataRegistry.maps.has(stage.map) and DataRegistry.maps[stage.map].lane_count() > 1 else ""])
	if not meta.is_stage_unlocked(stage.id):
		if not meta.is_campaign_unlocked(campaign.id):
			lines.append("[color=#%s]Opens when every element campaign is finished.[/color]" % UiStyle.BAD.to_html(false))
		else:
			lines.append("[color=#%s]Win the stage before it to open this one.[/color]" % UiStyle.BAD.to_html(false))
	lines.append("")
	lines.append("[b]Rules[/b]")
	for rule in stage.rule_text:
		lines.append("·  " + rule)
	var enemies := _enemy_names(wave_set)
	if not enemies.is_empty():
		lines.append("")
		lines.append("[b]Enemies[/b]  " + ", ".join(enemies))
	lines.append("")
	lines.append("[b]Reward[/b]  %d meta points for the first win%s. Stars: win, keep half your lives, lose none." % [
		stage.first_clear_points, "" if stars == 0 else " (claimed)"])
	if not campaign.reward_name.is_empty():
		var done := meta.is_campaign_complete(campaign.id)
		lines.append("[b]%s[/b]%s  %s" % [campaign.reward_name,
			" [color=#%s](earned)[/color]" % UiStyle.GOOD.to_html(false) if done else " for finishing the campaign:",
			campaign.reward_description])
	return "\n".join(lines)


func _wave_set(stage: StageData) -> WaveSet:
	if not stage.wave_set.is_empty():
		return DataRegistry.wave_sets.get(stage.wave_set)
	var map: MapData = DataRegistry.maps.get(stage.map)
	return DataRegistry.wave_sets.get(map.wave_set) if map != null else null


## Every enemy the stage's waves send, bosses first, with their traits.
func _enemy_names(wave_set: WaveSet) -> PackedStringArray:
	var seen: Array[EnemyData] = []
	if wave_set == null:
		return PackedStringArray()
	for wave in wave_set.waves:
		for group in wave.groups:
			var data: EnemyData = DataRegistry.enemies.get(group.enemy)
			if data != null and not seen.has(data):
				seen.append(data)
	seen.sort_custom(func(a: EnemyData, b: EnemyData) -> bool: return a.tags.has(&"boss") and not b.tags.has(&"boss"))
	var result: PackedStringArray = []
	for data in seen:
		var words := data.trait_words()
		var name := data.display_name
		if data.tags.has(&"boss"):
			name = "[color=#%s]%s[/color]" % [UiStyle.KEYSTONE.to_html(false), name]
		result.append(name + (" (%s)" % ", ".join(words) if not words.is_empty() else ""))
	return result


func begin() -> void:
	if Progress.play_stage(selected):
		Progress.play_story(get_tree(), Progress.meta.story_before_stage(Story.shared(), selected), GAME_SCENE)


func back_to_menu() -> void:
	get_tree().change_scene_to_file(MENU_SCENE)


# --- Input -----------------------------------------------------------------------

func _gui_input(event: InputEvent) -> void:
	var motion := event as InputEventMouseMotion
	if motion != null:
		_hovered = stage_at(motion.position)
		mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND if not _hovered.is_empty() else Control.CURSOR_ARROW
	var button := event as InputEventMouseButton
	if button != null and button.pressed and button.button_index == MOUSE_BUTTON_LEFT:
		var hit := stage_at(button.position)
		if not hit.is_empty():
			if hit == selected and button.double_click:
				begin()
			select(hit)
			accept_event()


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	if key.keycode == KEY_ESCAPE:
		get_viewport().set_input_as_handled()
		back_to_menu()
	elif key.keycode in [KEY_ENTER, KEY_KP_ENTER]:
		get_viewport().set_input_as_handled()
		begin()


## The stage whose gem is under a point, or empty.
func stage_at(point: Vector2) -> StringName:
	for id in _positions:
		if point.distance_to(_positions[id]) <= _radius(id) + 6.0:
			return id
	return &""


func stage_position(stage_id: StringName) -> Vector2:
	return _positions.get(stage_id, Vector2.ZERO)


# --- Drawing ---------------------------------------------------------------------

## The march on the enemy citadel, unlocked by the Convergence.
func _is_assault(campaign: CampaignData) -> bool:
	return campaign != null and campaign.element.is_empty() and campaign.requires_campaigns.has(&"convergence")


func _campaign_color(campaign: CampaignData) -> Color:
	if _is_assault(campaign):
		return Color("e0524a")
	if campaign == null or campaign.element.is_empty():
		return Color("f4e7c0")
	var element: ElementData = _elements.get(campaign.element)
	return element.color if element != null else Color.WHITE


func _style(stage: StageData, campaign: CampaignData) -> String:
	if _is_assault(campaign):
		return "keystone"
	if campaign.element.is_empty() and campaign.stage_index(stage.id) == campaign.stages.size() - 1:
		return "start"
	return "keystone" if stage.is_guardian else "notable"


func _radius(stage_id: StringName) -> float:
	var stage: StageData = DataRegistry.stages[stage_id]
	return TreeArt.SIZES[StringName(_style(stage, DataRegistry.campaign_of(stage_id)))] * TreeArt.SCALE * 0.5


func _draw() -> void:
	_draw_backdrop()
	var meta := Progress.meta
	draw_string(_font, Vector2(48, 70), "Campaign", HORIZONTAL_ALIGNMENT_LEFT, -1, 44, UiStyle.TEXT)
	var total := 0
	var earned := 0
	for campaign in meta.campaigns_in_order():
		total += campaign.stages.size() * 3
		earned += meta.campaign_stars(campaign)
	_draw_art(TreeArt.icon(&"star"), Vector2(46, 86))
	draw_string(_font, Vector2(80, 112), "%d / %d stars" % [earned, total], HORIZONTAL_ALIGNMENT_LEFT, -1, 24, UiStyle.GOLD)
	draw_multiline_string(_font, Vector2(48, 146), "Six elements, six lands, six fallen Wardens. Free them all and the roads converge on the heart of the ring.",
		HORIZONTAL_ALIGNMENT_LEFT, 420, 18, -1, UiStyle.TEXT_DIM)
	draw_arc(CENTER, OUTER + 46.0, 0.0, TAU, 128, Color(1, 1, 1, 0.07), 2.0, true)
	draw_arc(CENTER, INNER - 40.0, 0.0, TAU, 96, Color(1, 1, 1, 0.07), 2.0, true)
	for campaign in meta.campaigns_in_order():
		_draw_trail(campaign)
	for campaign in meta.campaigns_in_order():
		_draw_campaign_label(campaign)
		for stage in campaign.stages:
			_draw_stage(stage, campaign)


func _draw_backdrop() -> void:
	var backdrop := TreeArt.texture("backdrop")
	if backdrop == null:
		draw_rect(Rect2(Vector2.ZERO, size), UiStyle.BACKGROUND)
		return
	var fit := maxf(size.x / backdrop.get_width(), size.y / backdrop.get_height())
	var art_scale := maxf(TreeArt.SCALE, ceilf(fit))
	var drawn := backdrop.get_size() * art_scale
	draw_texture_rect(backdrop, Rect2(_snap((size - drawn) * 0.5), drawn), false)
	var aura := TreeArt.texture("aura")
	if aura != null:
		for campaign in Progress.meta.campaigns_in_order():
			if campaign.element.is_empty():
				continue
			var at := CENTER + _spoke(campaign.element) * (OUTER + INNER) * 0.5
			var glow := Color(_campaign_color(campaign), 0.16)
			draw_texture_rect(aura, Rect2(at - Vector2(260, 260), Vector2(520, 520)), false, glow)
		var heart_glow := 0.12 + 0.06 * sin(_time * 1.5)
		draw_texture_rect(aura, Rect2(CENTER - Vector2(200, 200), Vector2(400, 400)), false, Color(1, 0.95, 0.8, heart_glow))


## The road between a campaign's stages: dim when ahead, lit with flowing light once walked.
func _draw_trail(campaign: CampaignData) -> void:
	var meta := Progress.meta
	var color := _campaign_color(campaign)
	var points: Array[Vector2] = []
	for stage in campaign.stages:
		points.append(_positions[stage.id])
	if _is_assault(campaign):
		# A dark road from the heart of the Convergence to the citadel.
		var source: CampaignData = DataRegistry.campaigns.get(&"convergence")
		if source != null and not source.stages.is_empty():
			var lit := meta.is_campaign_complete(source.id)
			draw_line(_positions[source.stages[-1].id], points[0], Color(color, 0.6 if lit else 0.14), 4.0 if lit else 2.0, true)
	# The Convergence's first stages hang off the six Wardens.
	elif campaign.element.is_empty():
		for other in meta.campaigns_in_order():
			if other.element.is_empty() or other.stages.is_empty():
				continue
			var warden := _positions[other.stages[-1].id]
			var lit := meta.is_campaign_complete(other.id)
			var target := points[0] if _spoke(other.element).x <= 0.0 else points[mini(1, points.size() - 1)]
			draw_line(warden, target, Color(_campaign_color(other), 0.55 if lit else 0.12), 3.0 if lit else 2.0, true)
	for i in range(1, points.size()):
		var walked := meta.stars(campaign.stages[i - 1].id) > 0
		draw_line(points[i - 1], points[i], Color(color, 0.7 if walked else 0.16), 4.0 if walked else 2.0, true)
		if walked:
			var t := fposmod(_time * 0.35 + i * 0.3, 1.0)
			draw_circle(points[i - 1].lerp(points[i], t), 3.0, Color(color.lightened(0.5), 0.9))


func _draw_campaign_label(campaign: CampaignData) -> void:
	var meta := Progress.meta
	var color := _campaign_color(campaign)
	if _is_assault(campaign):
		var title_width := _font.get_string_size(campaign.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 22).x
		var at: Vector2 = _positions[campaign.stages[0].id] + Vector2(-title_width * 0.5, -48)
		draw_string_outline(_font, at, campaign.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, 6, Color(0, 0, 0, 0.6))
		draw_string(_font, at, campaign.display_name, HORIZONTAL_ALIGNMENT_LEFT, -1, 22, color.lightened(0.25))
		return
	if campaign.element.is_empty():
		return
	var direction := _spoke(campaign.element)
	var anchor := CENTER + direction * (OUTER + 70.0)
	var title := campaign.display_name
	var width := _font.get_string_size(title, HORIZONTAL_ALIGNMENT_LEFT, -1, 24).x
	var x := anchor.x - width * 0.5
	if direction.x > 0.3:
		x = anchor.x - 30.0
	elif direction.x < -0.3:
		x = anchor.x - width + 30.0
	var y := anchor.y + direction.y * 16.0
	_draw_art_centered(TreeArt.emblem(campaign.element), Vector2(x - 20.0, y - 8.0), Color(color.lightened(0.3), 1.0))
	draw_string_outline(_font, Vector2(x, y), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, 6, Color(0, 0, 0, 0.6))
	draw_string(_font, Vector2(x, y), title, HORIZONTAL_ALIGNMENT_LEFT, -1, 24, color.lightened(0.25))
	var sub := "%d / %d ★" % [meta.campaign_stars(campaign), campaign.stages.size() * 3]
	if meta.is_campaign_complete(campaign.id):
		sub += "  ·  " + campaign.reward_name
	draw_string(_font, Vector2(x, y + 24.0), sub, HORIZONTAL_ALIGNMENT_LEFT, -1, 17, UiStyle.TEXT_DIM)


func _draw_stage(stage: StageData, campaign: CampaignData) -> void:
	var meta := Progress.meta
	var at: Vector2 = _positions[stage.id]
	var style := _style(stage, campaign)
	var half: float = TreeArt.SIZES[StringName(style)] * TreeArt.SCALE * 0.5
	var top_left := at - Vector2(half, half)
	var color := _campaign_color(campaign)
	var unlocked := meta.is_stage_unlocked(stage.id)
	var stars := meta.stars(stage.id)
	var lit := 1.0 if stars > 0 else (0.6 if unlocked else 0.12)
	if stars > 0:
		_draw_art_centered(TreeArt.texture("glow"), at, Color(color, 0.45 + 0.1 * sin(_time * 2.0 + at.x)))
	if stage.id == selected:
		_draw_art_centered(TreeArt.texture("halo_" + style), at, Color(UiStyle.GOLD, 0.95))
	elif unlocked and stars == 0:
		var pulse := 0.5 + 0.5 * sin(_time * 4.0)
		_draw_art_centered(TreeArt.texture("halo_" + style), at, Color(UiStyle.GOLD, 0.3 + 0.5 * pulse))
	elif stage.id == _hovered:
		_draw_art_centered(TreeArt.texture("halo_" + style), at, Color(1, 1, 1, 0.5))
	var gem := color.lerp(Color(0.2, 0.22, 0.28), 1.0 - lit)
	if campaign.element.is_empty() and not _is_assault(campaign) and lit > 0.5:
		# The Convergence's gems shimmer through every element's colour.
		var colors: Array[Color] = []
		for element: ElementData in _elements.values():
			colors.append(element.color)
		var phase := fposmod(_time * 0.4 + at.x * 0.01, 1.0) * colors.size()
		gem = colors[int(phase) % colors.size()].lerp(colors[(int(phase) + 1) % colors.size()], fposmod(phase, 1.0))
	_draw_art(TreeArt.texture("gem_" + style), top_left, Color(gem.r * (0.55 + 0.45 * lit), gem.g * (0.55 + 0.45 * lit), gem.b * (0.55 + 0.45 * lit)))
	_draw_art(TreeArt.texture("shine_" + style), top_left, Color(1, 1, 1, lit * 0.8))
	var frame := 0.5 + 0.5 * lit
	_draw_art(TreeArt.texture("frame_" + style), top_left, Color(frame, frame, frame))
	if not unlocked:
		_draw_art_centered(TreeArt.icon(&"lock"), at, Color(0.8, 0.8, 0.85))
	elif stage.is_guardian:
		_draw_art_centered(TreeArt.icon(&"skull"), at, Color(1, 1, 1, 0.9))
	elif style == "start":
		_draw_art_centered(TreeArt.icon(&"sun"), at)
	else:
		var number := str(campaign.stage_index(stage.id) + 1)
		var width := _font.get_string_size(number, HORIZONTAL_ALIGNMENT_LEFT, -1, 20).x
		draw_string_outline(_font, at + Vector2(-width * 0.5, 7), number, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, 5, Color(0, 0, 0, 0.7))
		draw_string(_font, at + Vector2(-width * 0.5, 7), number, HORIZONTAL_ALIGNMENT_LEFT, -1, 20, Color.WHITE)
	if unlocked:
		var star := TreeArt.icon(&"star")
		var spacing := 22.0
		for i in 3:
			var spot := at + Vector2((i - 1) * spacing, half + 14.0)
			_draw_art_centered(star, spot, UiStyle.GOLD if i < stars else Color(0.3, 0.32, 0.4, 0.9))


static func _snap(point: Vector2) -> Vector2:
	return (point * 0.5).round() * 2.0


func _draw_art(texture: Texture2D, top_left: Vector2, tint := Color.WHITE) -> void:
	if texture != null:
		draw_texture_rect(texture, Rect2(_snap(top_left), texture.get_size() * TreeArt.SCALE), false, tint)


func _draw_art_centered(texture: Texture2D, center: Vector2, tint := Color.WHITE) -> void:
	if texture != null:
		_draw_art(texture, center - texture.get_size() * TreeArt.SCALE * 0.5, tint)
