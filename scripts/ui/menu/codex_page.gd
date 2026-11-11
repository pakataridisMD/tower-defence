class_name CodexPage
extends MenuPage
## Codex: every tower and every foe, with their picture, numbers and description, and the six
## elements with what each one does. Tabs along the top, a list on the left, the entry on the right.

const TABS: Array[String] = ["Towers", "Enemies", "Elements"]
const ART := "res://assets/art/game/"

var tab := 0
var selected: StringName = &""
var tab_buttons: Array[Button] = []
var _list: VBoxContainer
var _picture: TextureRect
var _name: Label
var _caption: Label
var _text: Label
var _stats: GridContainer
var _count: Label


func _init() -> void:
	super("Codex", "Everything you meet on the road.")
	var tabs := HBoxContainer.new()
	tabs.position = Vector2(0, 0)
	tabs.add_theme_constant_override("separation", 8)
	body.add_child(tabs)
	var group := ButtonGroup.new()
	for i in TABS.size():
		var b := UiStyle.menu_choice(TABS[i], group, 40)
		b.custom_minimum_size = Vector2(240, 56)
		b.button_pressed = i == 0
		var index := i
		b.toggled.connect(func(on: bool) -> void:
			if on:
				show_tab(index))
		tabs.add_child(b)
		tab_buttons.append(b)

	var list_panel := add_panel(Vector2(0, 68), Vector2(620, 784))
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	list_panel.add_child(scroll)
	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 6)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_list)

	var detail_panel := add_panel(Vector2(644, 68), Vector2(1180, 784))
	var detail := HBoxContainer.new()
	detail.add_theme_constant_override("separation", 32)
	detail_panel.add_child(detail)
	var stage := PanelContainer.new()
	var dark := StyleBoxFlat.new()
	dark.bg_color = Color("120e18")
	stage.add_theme_stylebox_override("panel", dark)
	stage.custom_minimum_size = Vector2(380, 460)
	stage.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	detail.add_child(stage)
	_picture = TextureRect.new()
	_picture.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	stage.add_child(_picture)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 12)
	column.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_child(column)
	_name = UiStyle.menu_title("", 80)
	column.add_child(_name)
	_caption = UiStyle.menu_label("", "small", 16, UiStyle.MENU_GOLD)
	column.add_child(_caption)
	_text = UiStyle.menu_label("", "body", 32, UiStyle.MENU_DIM)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(660, 0)
	column.add_child(_text)
	_stats = GridContainer.new()
	_stats.columns = 4
	_stats.add_theme_constant_override("h_separation", 24)
	_stats.add_theme_constant_override("v_separation", 6)
	column.add_child(_stats)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	column.add_child(spacer)
	_count = UiStyle.menu_label("", "small", 16, UiStyle.MENU_DIM)
	_count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	column.add_child(_count)
	show_tab(0)


func show_tab(index: int) -> void:
	tab = index
	for i in tab_buttons.size():
		tab_buttons[i].set_pressed_no_signal(i == index)
	for child in _list.get_children():
		child.queue_free()
	var entries := _entries()
	var group := ButtonGroup.new()
	for entry: Array in entries:
		var id: StringName = entry[0]
		var row := UiStyle.menu_choice(entry[1], group, 40)
		row.alignment = HORIZONTAL_ALIGNMENT_LEFT
		row.custom_minimum_size = Vector2(540, 64)
		row.icon = entry[2]
		row.expand_icon = false
		row.icon_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		row.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		row.add_theme_constant_override("icon_max_width", 48)
		row.toggled.connect(func(on: bool) -> void:
			if on:
				select(id))
		_list.add_child(row)
	_count.text = "%s: %d" % [TABS[index].to_upper(), entries.size()]
	if not entries.is_empty():
		(_list.get_child(_list.get_child_count() - entries.size()) as Button).set_pressed_no_signal(true)
		select(entries[0][0])


## [id, name, small picture] for every entry on the open tab, in a sensible order.
func _entries() -> Array[Array]:
	var result: Array[Array] = []
	match tab:
		0:
			var towers: Array[TowerData] = []
			towers.assign(DataRegistry.towers.values())
			towers.sort_custom(func(a: TowerData, b: TowerData) -> bool:
				return a.elements.size() < b.elements.size() if a.elements.size() != b.elements.size() else a.display_name < b.display_name)
			for t in towers:
				if DataRegistry.heroes.has(t.id):
					continue  # a hero's attack is kept as a tower; it belongs to the Heroes page
				result.append([t.id, t.display_name, BoardArt.tower_picture(t.id)])
		1:
			var foes: Array[EnemyData] = []
			foes.assign(DataRegistry.enemies.values())
			foes.sort_custom(func(a: EnemyData, b: EnemyData) -> bool: return a.max_health < b.max_health)
			for e in foes:
				result.append([e.id, e.display_name, _enemy_picture(e.id)])
		_:
			var elements: Array[ElementData] = []
			elements.assign(DataRegistry.elements.values())
			elements.sort_custom(func(a: ElementData, b: ElementData) -> bool: return a.ring_index < b.ring_index)
			for el in elements:
				result.append([el.id, el.display_name, null])
	return result


func select(id: StringName) -> void:
	selected = id
	for child in _stats.get_children():
		child.queue_free()
	match tab:
		0:
			var t: TowerData = DataRegistry.towers.get(id)
			_name.text = t.display_name
			var names: PackedStringArray = []
			for el in t.elements:
				names.append(String(el).to_upper())
			_caption.text = "  -  ".join(names) + "  -  %d GOLD" % t.cost
			_text.text = t.description
			_picture.texture = BoardArt.tower_picture(id)
			_picture.modulate = Color.WHITE
			_stat("Damage", "%d" % roundi(t.damage))
			_stat("Speed", "%.1f / s" % t.attacks_per_second)
			_stat("Range", "%d" % roundi(t.attack_range))
			if t.splash_radius > 0.0:
				_stat("Splash", "%d" % roundi(t.splash_radius))
			if t.chain_count > 0:
				_stat("Chains", "%d" % t.chain_count)
		1:
			var e: EnemyData = DataRegistry.enemies.get(id)
			_name.text = e.display_name
			var parts: PackedStringArray = []
			if not e.element.is_empty():
				parts.append(String(e.element).to_upper())
			for tag in e.tags:
				parts.append(String(tag).to_upper())
			_caption.text = "  -  ".join(parts)
			_text.text = e.description
			if not e.power_text().is_empty():
				_text.text += "\n\n" + e.power_text()
			_picture.texture = _enemy_picture(id)
			_picture.modulate = _enemy_tint(e)
			_stat("Health", "%d" % roundi(e.max_health))
			_stat("Speed", "%d" % roundi(e.speed))
			_stat("Armour", "%d" % roundi(e.armour))
			_stat("Bounty", "%d" % e.bounty)
		_:
			var el: ElementData = DataRegistry.elements.get(id)
			_name.text = el.display_name
			_caption.text = el.role.to_upper()
			_text.text = el.signature
			_picture.texture = null


func _stat(label: String, value: String) -> void:
	_stats.add_child(UiStyle.menu_label(label, "button", 40, UiStyle.MENU_DIM))
	_stats.add_child(UiStyle.menu_label(value, "button", 40, UiStyle.MENU_TEXT))


static func _enemy_picture(enemy_id: StringName) -> Texture2D:
	var path := ART + "enemies/%s_0.png" % enemy_id
	return load(path) if ResourceLoader.exists(path) else null


## Plain enemy bodies are grey and take their element's colour in battle; hand-drawn ones keep theirs.
static func _enemy_tint(e: EnemyData) -> Color:
	if bool(BoardArt.enemy_info(e.id).get("drawn", false)):
		return Color.WHITE
	var el: ElementData = DataRegistry.elements.get(e.element)
	return el.color.lightened(0.25) if el != null else Color.WHITE
