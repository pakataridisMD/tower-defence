class_name SavesPage
extends MenuPage
## Saved games, Fallout style: one autosave for each playthrough (each New Game), which the game keeps
## up to date by itself, and ten slots the player saves into by hand. Each row shows the game ("Game
## 2"), where (the stage or skirmish map), the wave, gold, lives, difficulty, the campaign's stars and
## when it was saved. The Save tab writes into a slot (asking before writing over one); the Load tab
## loads a save (asking first) or deletes it.
##
## The title screen opens it on Load only (can_save false). During a run the Esc menu opens it with
## both tabs, and a save keeps the run: as it is in a break, or as it was in the break before the wave
## being fought.
## Keys: Esc closes the question or the page, Enter says yes, Tab switches between Save and Load,
## and 1 to 9 and 0 pick slots 1 to 10.

## The player picked a save to load (a SaveSlots key) and said yes. The page has loaded nothing yet:
## the owner calls Progress.load_save and changes scene.
signal load_confirmed(key: String)
## A slot was written.
signal saved(slot: int)

const ROW_HEIGHT := 78.0
const DATE_WIDTH := 230.0
const ACTION_WIDTH := 200.0
const DELETE_WIDTH := 170.0

## &"save" or &"load".
var mode: StringName = &"load"
## False hides the Save tab (the title screen: saving happens in a battle, and by itself).
var can_save := true:
	set(value):
		can_save = value
		if save_tab != null:
			save_tab.visible = value
			load_tab.visible = value
## Returns the run to keep with a save (a RunSnapshot), or an empty dictionary outside a run. Set by
## Game; the main menu leaves it empty.
var run_source: Callable
## Shown under the title: what a save keeps from here.
var save_note := "Saving keeps your campaign stars, talents and heroes."
var load_note := "Every game you start keeps its own autosave (A)."

var save_tab: Button
var load_tab: Button
var note_label: Label
## One row per manual slot, slot 1 first.
var rows: Array[SlotRow] = []
## One row per playthrough's autosave, the newest first. Rebuilt on refresh; shown on the Load tab.
var auto_rows: Array[SlotRow] = []
var dialog: Control
var dialog_title: Label
var dialog_text: Label
var dialog_yes: MenuItemButton
## The question being asked: [action, key], action &"save", &"load" or &"delete". Empty when none.
var pending: Array = []

var _column: VBoxContainer
var _scroll: ScrollContainer


func _init() -> void:
	super("Saved games")
	note_label = UiStyle.menu_label("", "body", 32, UiStyle.MENU_DIM)
	note_label.position = Vector2(272, 116)
	add_child(note_label)
	var group := ButtonGroup.new()
	save_tab = UiStyle.menu_choice("Save", group, 40)
	save_tab.position = Vector2(1412, 40)
	save_tab.size = Vector2(220, 56)
	save_tab.toggled.connect(func(on: bool) -> void:
		if on:
			show_mode(&"save"))
	add_child(save_tab)
	load_tab = UiStyle.menu_choice("Load", group, 40)
	load_tab.position = Vector2(1652, 40)
	load_tab.size = Vector2(220, 56)
	load_tab.toggled.connect(func(on: bool) -> void:
		if on:
			show_mode(&"load"))
	add_child(load_tab)
	_scroll = ScrollContainer.new()
	_scroll.position = Vector2.ZERO
	_scroll.size = body.size
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.mouse_filter = Control.MOUSE_FILTER_PASS
	body.add_child(_scroll)
	_column = VBoxContainer.new()
	_column.add_theme_constant_override("separation", 6)
	_column.custom_minimum_size = Vector2(body.size.x - 16, 0)
	_scroll.add_child(_column)
	for slot in range(1, SaveSlots.COUNT + 1):
		var row := _make_row(SaveSlots.slot_key(slot), str(slot))
		row.slot = slot
		rows.append(row)
	_build_dialog()


func _make_row(key: String, number: String) -> SlotRow:
	var row := SlotRow.new(key, number)
	row.custom_minimum_size = Vector2(body.size.x - 16, ROW_HEIGHT)
	row.action_button.pressed.connect(_act.bind(key))
	row.delete_button.pressed.connect(ask.bind(&"delete", key))
	_column.add_child(row)
	return row


## Shows the page on a tab: &"save" or &"load".
func open(on_mode: StringName) -> void:
	show_mode(on_mode)
	show()


func show_mode(on_mode: StringName) -> void:
	mode = on_mode if can_save else &"load"
	# With nothing to switch to, the tabs go.
	save_tab.visible = can_save
	load_tab.visible = can_save
	save_tab.set_pressed_no_signal(mode == &"save")
	load_tab.set_pressed_no_signal(mode == &"load")
	close_dialog()
	refresh()
	_scroll.scroll_vertical = 0


func refresh() -> void:
	note_label.text = save_note if mode == &"save" else load_note
	note_label.add_theme_color_override("font_color", UiStyle.MENU_DIM)
	# The autosaves, newest first, above the slots on the Load tab.
	for row in auto_rows:
		_column.remove_child(row)
		row.queue_free()
	auto_rows.clear()
	if mode == &"load":
		var index := 0
		for id in Progress.slots.autosave_ids():
			var row := _make_row(SaveSlots.auto_key(id), "A")
			_column.move_child(row, index)
			auto_rows.append(row)
			index += 1
	var playing := Progress.meta.profile.playthrough_id
	for row in auto_rows + rows:
		var info := Progress.slots.info_key(row.key)
		row.show_slot(info, mode, int(info.get("game_id", 0)) == playing)


## Saves at once into an empty slot, and asks first before writing over one. Loads after asking.
func _act(key: String) -> void:
	if mode == &"save":
		if Progress.slots.has_key(key):
			ask(&"save", key)
		else:
			save_into(key.trim_prefix("slot_").to_int())
	elif Progress.slots.has_key(key):
		ask(&"load", key)


## Picks a slot from the keyboard: the same as pressing its button.
func pick(slot: int) -> void:
	if SaveSlots.is_valid_slot(slot) and not rows[slot - 1].action_button.disabled:
		_act(SaveSlots.slot_key(slot))


func save_into(slot: int) -> void:
	var run: Dictionary = run_source.call() if run_source.is_valid() else {}
	var error := Progress.save_to_slot(slot, run)
	close_dialog()
	refresh()
	if error == OK:
		note_label.text = "Saved in slot %d." % slot
		note_label.add_theme_color_override("font_color", UiStyle.MENU_GOLD_LIGHT)
		SoundPlayer.sfx(&"ui_confirm")
		saved.emit(slot)
	else:
		note_label.text = "Slot %d could not be saved: %s" % [slot, error_string(error)]
		note_label.add_theme_color_override("font_color", UiStyle.BAD)


# --- The question ------------------------------------------------------------------

func _build_dialog() -> void:
	dialog = Control.new()
	dialog.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dialog.mouse_filter = Control.MOUSE_FILTER_STOP
	dialog.hide()
	add_child(dialog)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.02, 0.04, 0.6)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dialog.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dialog.add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.menu_panel_box(48, 32))
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 18)
	panel.add_child(column)
	dialog_title = UiStyle.menu_title("", 72)
	dialog_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(dialog_title)
	dialog_text = UiStyle.menu_label("", "body", 32, UiStyle.MENU_DIM)
	dialog_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	dialog_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	dialog_text.custom_minimum_size = Vector2(900, 0)
	column.add_child(dialog_text)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_child(row)
	var no := MenuItemButton.new("Cancel", "Esc")
	no.custom_minimum_size = Vector2(300, 64)
	no.pressed.connect(close_dialog)
	row.add_child(no)
	dialog_yes = MenuItemButton.new("", "Enter")
	dialog_yes.custom_minimum_size = Vector2(300, 64)
	dialog_yes.pressed.connect(confirm)
	row.add_child(dialog_yes)


## Asks before writing over a slot, loading a save or deleting one. `target` is a slot number or a
## SaveSlots key.
func ask(action: StringName, target: Variant) -> void:
	var key: String = SaveSlots.slot_key(target) if target is int else str(target)
	var info := Progress.slots.info_key(key)
	var auto := key.begins_with("auto_")
	var label := ("%s's autosave" % info.get("game", "Game")) if auto else "Slot %s" % key.trim_prefix("slot_").to_int()
	var name := "%s: %s, %s" % [label, info.get("title", ""), SaveSlots.date_text(int(info.get("saved_at", 0)))]
	match action:
		&"save":
			dialog_title.text = "Overwrite %s?" % label.to_lower()
			dialog_text.text = "%s will be replaced." % name
			dialog_yes.text = "Overwrite"
		&"load":
			dialog_title.text = "Load %s?" % ("autosave" if auto else label.to_lower())
			dialog_text.text = "%s.\nAnything since your game's last autosave is lost." % name
			dialog_yes.text = "Load"
		&"delete":
			dialog_title.text = "Delete %s?" % ("autosave" if auto else label.to_lower())
			dialog_text.text = "%s will be gone for good." % name
			dialog_yes.text = "Delete"
		_:
			return
	pending = [action, key]
	dialog.show()


func is_asking() -> bool:
	return not pending.is_empty()


func close_dialog() -> void:
	pending = []
	if dialog != null:
		dialog.hide()


## "Yes" to the question.
func confirm() -> void:
	if not is_asking():
		return
	var action: StringName = pending[0]
	var key: String = pending[1]
	close_dialog()
	match action:
		&"save":
			save_into(key.trim_prefix("slot_").to_int())
		&"load":
			load_confirmed.emit(key)
		&"delete":
			Progress.slots.erase_key(key)
			refresh()
			note_label.text = "Deleted."


## Keys on this page. Returns true when the key was used; Esc with no question open is left to the
## owner, which closes the page.
func handle_key(keycode: Key) -> bool:
	if is_asking():
		match keycode:
			KEY_ESCAPE, KEY_BACKSPACE:
				close_dialog()
			KEY_ENTER, KEY_KP_ENTER:
				confirm()
		return true
	match keycode:
		KEY_TAB:
			if can_save:
				show_mode(&"load" if mode == &"save" else &"save")
			return true
		KEY_1, KEY_2, KEY_3, KEY_4, KEY_5, KEY_6, KEY_7, KEY_8, KEY_9:
			pick(keycode - KEY_0)
			return true
		KEY_0:
			pick(10)
			return true
	return false


## One save in the list: its number (A for an autosave), what is in it, when it was saved and its
## buttons.
class SlotRow:
	extends PanelContainer

	## The SaveSlots key, and the slot number (0 for an autosave).
	var key: String
	var slot := 0
	var number_label: Label
	var title_label: Label
	var detail_label: Label
	var date_label: Label
	var action_button: Button
	var delete_button: Button

	func _init(p_key: String, number: String) -> void:
		key = p_key
		add_theme_stylebox_override("panel", UiStyle.menu_panel_box(20, 4, false))
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 20)
		add_child(row)
		number_label = UiStyle.menu_title(number, 56)
		number_label.custom_minimum_size = Vector2(64, 0)
		number_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		number_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(number_label)
		var text := VBoxContainer.new()
		# The button font's line has room under the letters: pull the details line up into it.
		text.add_theme_constant_override("separation", -8)
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		text.alignment = BoxContainer.ALIGNMENT_CENTER
		row.add_child(text)
		title_label = UiStyle.menu_label("", "button", 40)
		title_label.clip_text = true
		text.add_child(title_label)
		detail_label = UiStyle.menu_label("", "small", 16, UiStyle.MENU_DIM)
		detail_label.clip_text = true
		text.add_child(detail_label)
		date_label = UiStyle.menu_label("", "small", 16, UiStyle.MENU_DIM)
		date_label.custom_minimum_size = Vector2(SavesPage.DATE_WIDTH, 0)
		date_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		date_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(date_label)
		action_button = UiStyle.menu_button("", 40)
		action_button.custom_minimum_size = Vector2(SavesPage.ACTION_WIDTH, 56)
		action_button.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		row.add_child(action_button)
		delete_button = UiStyle.menu_button("Delete", 40)
		delete_button.custom_minimum_size = Vector2(SavesPage.DELETE_WIDTH, 56)
		delete_button.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		delete_button.add_theme_color_override("font_hover_color", UiStyle.LIFE)
		row.add_child(delete_button)

	func is_autosave() -> bool:
		return key.begins_with("auto_")

	## Fills the row from a save's info (empty for an empty slot), for the Save or Load tab. `playing`
	## marks a save of the game being played.
	func show_slot(info: Dictionary, mode: StringName, playing: bool = false) -> void:
		var empty := info.is_empty()
		title_label.text = "Empty slot" if empty else str(info.get("title", "Saved game"))
		title_label.add_theme_color_override("font_color", UiStyle.MENU_DIM if empty else UiStyle.MENU_TEXT)
		detail_label.text = "" if empty else SlotRow.details(info, is_autosave()).to_upper()
		detail_label.add_theme_color_override("font_color", UiStyle.MENU_GOLD if playing and not empty else UiStyle.MENU_DIM)
		date_label.text = "" if empty else SaveSlots.date_text(int(info.get("saved_at", 0))).to_upper()
		if mode == &"save":
			action_button.text = "Save" if empty else "Overwrite"
			action_button.disabled = false
		else:
			action_button.text = "Load"
			action_button.disabled = empty
		# Delete keeps its place when hidden, so the Save and Load buttons line up down the list.
		var can_delete := mode == &"load" and not empty
		delete_button.disabled = not can_delete
		delete_button.modulate.a = 1.0 if can_delete else 0.0
		delete_button.mouse_filter = Control.MOUSE_FILTER_STOP if can_delete else Control.MOUSE_FILTER_IGNORE

	## The line under the title: which game, where, which wave, gold, lives, difficulty and stars.
	static func details(info: Dictionary, autosave: bool = false) -> String:
		var parts: Array[String] = []
		var game := str(info.get("game", ""))
		if not game.is_empty():
			parts.append("%s autosave" % game if autosave else game)
		var where := str(info.get("where", ""))
		if not where.is_empty():
			parts.append(where)
		if info.get("kind", "") == "run":
			var wave := int(info.get("wave", 0))
			var waves := int(info.get("waves", 0))
			if info.get("assault", false) == true or info.get("endless", false) == true or waves <= 0:
				parts.append("Wave %d" % wave)
			else:
				parts.append("Wave %d of %d" % [mini(wave, waves), waves])
			parts.append("%d gold" % int(info.get("gold", 0)))
			parts.append("%d lives" % int(info.get("lives", 0)))
			var difficulty := str(info.get("difficulty", ""))
			if not difficulty.is_empty():
				parts.append(difficulty)
		var total := int(info.get("stars_total", 0))
		if total > 0:
			parts.append("%d of %d stars" % [int(info.get("stars", 0)), total])
		var heroes := int(info.get("heroes", 0))
		if heroes > 0 and info.get("kind", "") != "run":
			parts.append("%d hero%s" % [heroes, "" if heroes == 1 else "es"])
		return "  -  ".join(parts)
