class_name HeroesPage
extends MenuPage
## Heroes: every champion of the six crowns. Heroes who have not joined yet are shown dark with a
## lock and where they join. Picking one shows their story line, aura and abilities; the button
## takes them into the next battle's party (up to HeroData.MAX_PARTY) or leaves them behind.

const CELL := Vector2(208, 196)

var selected: StringName = &""
var party_button: MenuItemButton
var _cells: Dictionary[StringName, Button] = {}
var _name: Label
var _caption: Label
var _blurb: Label
var _aura: Label
var _ability: Label
var _ultimate: Label
var _figure: TextureRect
var _party_row: HBoxContainer


func _init() -> void:
	super("Heroes", "Champions of the six crowns. Take up to %d into each battle." % HeroData.MAX_PARTY)
	var grid_panel := add_panel(Vector2(0, 0), Vector2(904, 852))
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 4)
	grid_panel.add_child(grid)
	var group := ButtonGroup.new()
	for hero in Progress.meta.heroes_in_order():
		var cell := UiStyle.menu_choice(hero.display_name.get_slice(" ", 0), group, 30)
		cell.custom_minimum_size = CELL
		cell.icon = Hud.hero_portrait(hero.id)
		cell.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cell.vertical_icon_alignment = VERTICAL_ALIGNMENT_TOP
		cell.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		var hero_id := hero.id
		cell.toggled.connect(func(on: bool) -> void:
			if on:
				select(hero_id))
		_cells[hero.id] = cell
		grid.add_child(cell)

	var detail_panel := add_panel(Vector2(928, 0), Vector2(896, 852))
	var detail := HBoxContainer.new()
	detail.add_theme_constant_override("separation", 28)
	detail_panel.add_child(detail)
	var left := VBoxContainer.new()
	left.add_theme_constant_override("separation", 12)
	detail.add_child(left)
	var stage := PanelContainer.new()
	var dark := StyleBoxFlat.new()
	dark.bg_color = Color("120e18")
	stage.add_theme_stylebox_override("panel", dark)
	stage.custom_minimum_size = Vector2(220, 420)
	left.add_child(stage)
	_figure = TextureRect.new()
	_figure.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	_figure.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_figure.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stage.add_child(_figure)
	left.add_child(UiStyle.menu_label("PARTY", "small", 16, UiStyle.MENU_GOLD))
	_party_row = HBoxContainer.new()
	_party_row.add_theme_constant_override("separation", 8)
	left.add_child(_party_row)

	var right := VBoxContainer.new()
	right.add_theme_constant_override("separation", 10)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	detail.add_child(right)
	_name = UiStyle.menu_title("", 64)
	right.add_child(_name)
	_caption = UiStyle.menu_label("", "small", 16, UiStyle.MENU_GOLD)
	right.add_child(_caption)
	_blurb = _wrapped(right, UiStyle.MENU_DIM)
	right.add_child(UiStyle.menu_label("AURA", "small", 16, UiStyle.MENU_GOLD))
	_aura = _wrapped(right, UiStyle.MENU_TEXT)
	right.add_child(UiStyle.menu_label("ABILITY", "small", 16, UiStyle.MENU_GOLD))
	_ability = _wrapped(right, UiStyle.MENU_TEXT)
	_ultimate = _wrapped(right, UiStyle.MENU_DIM)
	var spacer := Control.new()
	spacer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.add_child(spacer)
	party_button = MenuItemButton.new("Take into battle", "Enter")
	party_button.custom_minimum_size = Vector2(0, 72)
	party_button.pressed.connect(toggle_party)
	right.add_child(party_button)
	refresh()


func _wrapped(column: VBoxContainer, color: Color) -> Label:
	var result := UiStyle.menu_label("", "body", 32, color)
	result.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	result.custom_minimum_size = Vector2(560, 0)
	column.add_child(result)
	return result


func refresh() -> void:
	var meta := Progress.meta
	for hero in meta.heroes_in_order():
		var cell := _cells[hero.id]
		var joined := meta.is_hero_joined(hero.id)
		var in_party := meta.party().has(hero)
		cell.modulate = Color.WHITE if joined else Color(0.42, 0.38, 0.5)
		cell.text = hero.display_name.get_slice(" ", 0) + ("  *" if in_party else "")
		cell.tooltip_text = "%s, %s" % [hero.display_name, hero.title] if joined else "%s joins later in the campaign." % hero.display_name
	if selected.is_empty() or not _cells.has(selected):
		var party := meta.party()
		selected = party[0].id if not party.is_empty() else meta.heroes_in_order()[0].id
	_cells[selected].set_pressed_no_signal(true)
	_show(selected)


func select(hero_id: StringName) -> void:
	selected = hero_id
	_show(hero_id)


func _show(hero_id: StringName) -> void:
	var meta := Progress.meta
	var hero: HeroData = DataRegistry.heroes.get(hero_id)
	if hero == null:
		return
	var joined := meta.is_hero_joined(hero_id)
	_name.text = hero.display_name
	var element: ElementData = DataRegistry.elements.get(hero.element)
	var parts: PackedStringArray = [hero.title.to_upper()]
	if element != null:
		parts.append(element.display_name.to_upper())
	_caption.text = "  -  ".join(parts)
	_blurb.text = hero.blurb
	_aura.text = hero.aura_text if not hero.aura_text.is_empty() else "None"
	if hero.ability != null:
		_ability.text = "%s: %s" % [hero.ability.display_name, hero.ability.description]
	else:
		_ability.text = "None"
	_ultimate.text = ("From level %d: %s" % [HeroData.ULTIMATE_LEVEL, hero.ultimate_text]) if not hero.ultimate_text.is_empty() else ""
	var board := "res://assets/art/heroes/board/%s.png" % hero_id
	_figure.texture = load(board) if ResourceLoader.exists(board) else Hud.hero_portrait(hero_id)
	_figure.modulate = Color.WHITE if joined else Color(0.15, 0.12, 0.2)
	var in_party := meta.party().has(hero)
	party_button.disabled = not joined
	party_button.text = "Joins later" if not joined else ("Leave behind" if in_party else "Take into battle")
	for child in _party_row.get_children():
		child.queue_free()
	for member in meta.party():
		var face := TextureRect.new()
		face.texture = Hud.hero_portrait(member.id)
		face.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		face.custom_minimum_size = Vector2(68, 68)
		face.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		face.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT
		face.tooltip_text = member.display_name
		_party_row.add_child(face)


func toggle_party() -> void:
	if Progress.toggle_party_hero(selected):
		refresh()
