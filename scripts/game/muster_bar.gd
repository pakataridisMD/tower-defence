class_name MusterBar
extends PanelContainer
## The muster bar of the counter-attack: one button per unit the player can send up the roads, in
## pages (the troops, then the heroes as champions), with their price, cooldown and how many are on
## the field, and the road they march up. Hidden until the counter-attack begins.
##
## Keys while it shows: 1-9 and 0 muster from the open page, Tab turns the page, R picks the road.

signal muster_pressed(ally_id: StringName)

const KEYS: Array[Key] = [KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9, KEY_0]
const PAGE_SIZE := 10
const BUTTON_SIZE := Vector2(132, 92)
const ICON_HEIGHT := 46.0

var sim: RunSim
## The road the next squad marches up, or -1 for the road with the fewest enemies on it.
var lane := -1
var page := 0

var _pages: Array = []
var _page_names: PackedStringArray = []
var _buttons: Dictionary[StringName, KeyButton] = {}
var _rows: Array[HBoxContainer] = []
var _tabs: Array[Button] = []
var _road_button: Button
var _army_label: Label


func setup(p_sim: RunSim) -> void:
	sim = p_sim
	theme_type_variation = &"SlimPanel"
	mouse_filter = Control.MOUSE_FILTER_STOP
	visible = false
	var troops: Array[AllyData] = []
	var champions: Array[AllyData] = []
	for data in sim.ally_list():
		(champions if data.is_champion() else troops).append(data)
	for i in range(0, troops.size(), PAGE_SIZE):
		_pages.append(troops.slice(i, i + PAGE_SIZE))
		_page_names.append("Troops" if troops.size() <= PAGE_SIZE else "Troops %d" % (_pages.size()))
	for i in range(0, champions.size(), PAGE_SIZE):
		_pages.append(champions.slice(i, i + PAGE_SIZE))
		_page_names.append("Champions" if champions.size() <= PAGE_SIZE else "Champions %d" % (i / PAGE_SIZE + 1))
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	add_child(column)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 8)
	column.add_child(head)
	head.add_child(UiStyle.label("Muster", 22, UiStyle.GOLD))
	for i in _pages.size():
		var tab := UiStyle.key_button(_page_names[i], 15)
		tab.toggle_mode = true
		tab.custom_minimum_size = Vector2(118, 30)
		tab.add_theme_stylebox_override("pressed", UiStyle.button_box("picked", 5, 4))
		tab.add_theme_stylebox_override("hover_pressed", UiStyle.button_box("picked", 5, 4))
		tab.pressed.connect(show_page.bind(i))
		head.add_child(tab)
		_tabs.append(tab)
	_road_button = UiStyle.key_button("", 15)
	_road_button.key_text = "R"
	_road_button.custom_minimum_size = Vector2(190, 30)
	_road_button.pressed.connect(cycle_road)
	head.add_child(_road_button)
	_army_label = UiStyle.label("", 15, UiStyle.TEXT_DIM)
	_army_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_army_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	head.add_child(_army_label)
	head.add_child(UiStyle.label("1-0 muster  ·  Tab page", 14, UiStyle.TEXT_DIM))
	for i in _pages.size():
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 5)
		column.add_child(row)
		_rows.append(row)
		var slot := 0
		for data: AllyData in _pages[i]:
			row.add_child(_make_button(data, slot))
			slot += 1
	show_page(0)


func _make_button(data: AllyData, slot: int) -> KeyButton:
	var button := UiStyle.key_button("%d" % data.cost, 15)
	button.custom_minimum_size = BUTTON_SIZE
	button.icon = portrait(data)
	button.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	button.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
	button.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	button.expand_icon = false
	button.clip_text = true
	button.key_text = OS.get_keycode_string(KEYS[slot])
	button.tooltip_text = tooltip(data)
	var ally_id := data.id
	button.pressed.connect(func() -> void: muster_pressed.emit(ally_id))
	_buttons[data.id] = button
	return button


## The unit's picture: the first frame of its walk, cropped, or the hero's board sprite.
static func portrait(data: AllyData) -> Texture2D:
	if data.is_champion():
		var path := AllyArt.HERO_DIR + "%s.png" % data.hero
		if not ResourceLoader.exists(path):
			return null
		return _fit(load(path), Rect2(Vector2.ZERO, (load(path) as Texture2D).get_size()))
	var info: Dictionary = AllyArt.meta().get(String(data.id), {})
	if info.is_empty():
		return null
	var strip: Texture2D = load(AllyArt.DIR + "%s_walk.png" % data.id)
	var frame: Array = info["frame"]
	var image := strip.get_image()
	var used := image.get_region(Rect2i(0, 0, frame[0], frame[1])).get_used_rect()
	return _fit(strip, Rect2(used))


static func _fit(texture: Texture2D, region: Rect2) -> AtlasTexture:
	var atlas := AtlasTexture.new()
	atlas.atlas = texture
	atlas.region = region
	return atlas


static func tooltip(data: AllyData) -> String:
	var lines := PackedStringArray()
	lines.append("%s — %s" % [data.display_name, data.title])
	lines.append("%s  ·  %d gold  ·  %d in a squad%s" % [AllyData.role_name(data.role), data.cost, data.count,
		"  ·  at most %d on the field" % data.max_alive if data.max_alive > 0 else ""])
	lines.append("Health %d  ·  damage %.0f a second  ·  armour %d" % [roundi(data.max_health), data.damage_per_second(), roundi(data.armour)])
	var traits := PackedStringArray()
	if data.flying:
		traits.append("flies over the horde")
	if data.siege_only:
		traits.append("only fights buildings")
	elif data.siege_multiplier > 1.0:
		traits.append("x%.1f against the citadel" % data.siege_multiplier)
	if data.boss_multiplier > 1.0:
		traits.append("x%.1f against bosses" % data.boss_multiplier)
	if data.heal_amount > 0.0:
		traits.append("heals the units around it")
	if data.aura_damage > 0.0:
		traits.append("units near it deal %d%% more" % roundi(data.aura_damage * 100.0))
	if not data.blocks:
		traits.append("does not hold the road")
	if not traits.is_empty():
		var text := ", ".join(traits)
		lines.append(text.left(1).to_upper() + text.substr(1))
	lines.append(data.description)
	return "\n".join(lines)


func show_page(index: int) -> void:
	page = clampi(index, 0, maxi(0, _pages.size() - 1))
	for i in _rows.size():
		_rows[i].visible = i == page
		_tabs[i].set_pressed_no_signal(i == page)


func cycle_page() -> void:
	if not _pages.is_empty():
		show_page((page + 1) % _pages.size())


func cycle_road() -> void:
	lane += 1
	if lane >= sim.lane_curves.size():
		lane = -1


## The road the next squad takes.
func target_lane() -> int:
	return lane if lane >= 0 else sim.quietest_lane()


func ally_for_hotkey(index: int) -> StringName:
	if _pages.is_empty() or index < 0 or index >= (_pages[page] as Array).size():
		return &""
	return (_pages[page][index] as AllyData).id


func _process(_delta: float) -> void:
	if sim == null:
		return
	visible = sim.is_counter_assault() and sim.counter_started and not sim.is_over()
	if not visible:
		return
	_road_button.text = "Road: quietest" if lane < 0 else "Road %d" % (lane + 1)
	var on_field := 0
	for ally in sim.allies:
		if ally.alive:
			on_field += 1
	_army_label.text = "%d on the field" % on_field
	for ally_id in _buttons:
		var button := _buttons[ally_id]
		if not button.is_visible_in_tree():
			continue
		var data: AllyData = sim.config.allies[ally_id]
		var left := sim.muster_cooldown_left(ally_id)
		button.cooldown = left / maxf(0.1, data.cooldown)
		button.cooldown_text = "%d" % ceili(left) if left > 0.0 else ""
		var alive := sim.allies_alive(ally_id)
		button.badge_text = ("%d/%d" % [alive, data.max_alive]) if data.max_alive > 0 else (("%d" % alive) if alive > 0 else "")
		var error := sim.muster_error(ally_id, target_lane())
		button.disabled = not error.is_empty()
		button.add_theme_color_override("font_color", UiStyle.GOLD if sim.gold >= data.cost else UiStyle.BAD)
