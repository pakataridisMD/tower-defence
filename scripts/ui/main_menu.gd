class_name MainMenu
extends Control
## The title screen: what the player sees when the game opens. A painted dusk view of Solenne with
## the menu on the left: Continue, Campaign, Skirmish, Heroes, Talents, Codex, Settings, Credits
## and Quit, each with its key. Skirmish, Heroes, Codex, Settings and Credits open as pages over the
## picture; Campaign and Talents open their own screens. Esc goes back from a page, and on the
## title screen asks before quitting. Music plays behind it all (MenuMusic). When the game opens,
## the studio splash (StudioSplash, scenes/splash.tscn) plays first.
##
## Starts a run straight away when the game is launched with --autoplay (add --stage=<id> to play a
## campaign stage, open or not).

const GAME_SCENE := "res://scenes/game/game.tscn"
const META_TREE_SCENE := "res://scenes/meta/meta_tree.tscn"
const CAMPAIGN_SCENE := "res://scenes/campaign/campaign_map.tscn"
const LOGO_SCALE := 3.0
const MENU_WIDTH := 616.0

## Every page the menu can open, by name.
var pages: Dictionary[StringName, MenuPage] = {}
## The page on screen, or empty on the title screen.
var page: StringName = &""
var buttons: Dictionary[StringName, MenuItemButton] = {}
var quit_dialog: Control
var _home: Control
## The stage Continue plays, or empty when there is none.
var continue_stage: StringName = &""
## The title screen's music (off in Settings > Sound > Menu music).
var music: MenuMusic


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if OS.get_cmdline_user_args().has("--autoplay"):
		for arg in OS.get_cmdline_user_args():
			if arg.begins_with("--stage="):
				Progress.active_stage = StringName(arg.trim_prefix("--stage="))
		get_tree().change_scene_to_file.call_deferred(GAME_SCENE)
		return
	VideoSettings.load_saved()
	theme = UiStyle.menu_theme()
	_build_backdrop()
	_home = Control.new()
	_home.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_home.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_home)
	_build_title()
	_build_menu()
	_build_story_card()
	_build_quit_dialog()
	music = MenuMusic.new()
	add_child(music)
	if StudioSplash.fade_into_menu:
		StudioSplash.fade_into_menu = false
		_fade_in_from_black()


## After the studio splash: the title screen rises out of the splash's black.
func _fade_in_from_black() -> void:
	var black := ColorRect.new()
	black.color = Color(0, 0, 0, 1)
	black.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	black.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(black)
	var tween := black.create_tween()
	tween.tween_property(black, "color:a", 0.0, 1.2).set_ease(Tween.EASE_OUT)
	tween.tween_callback(black.queue_free)


# --- The title screen --------------------------------------------------------------

func _build_backdrop() -> void:
	var picture := TextureRect.new()
	picture.texture = UiStyle.menu_art("backdrop")
	picture.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	picture.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	picture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	picture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	picture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(picture)
	if picture.texture == null:
		var flat := ColorRect.new()
		flat.color = UiStyle.BACKGROUND
		flat.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
		flat.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(flat)


func _build_title() -> void:
	var logo := UiStyle.art("logo")
	if logo != null:
		var title := TextureRect.new()
		title.texture = logo
		title.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		title.stretch_mode = TextureRect.STRETCH_SCALE
		title.position = Vector2(64, 48)
		title.size = logo.get_size() * LOGO_SCALE * 0.6667
		title.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_home.add_child(title)
	else:
		var text := UiStyle.menu_title("Tower Defence 2D", 96)
		text.position = Vector2(64, 30)
		_home.add_child(text)
	var subtitle := UiStyle.menu_title("The War of Seven Crowns", 56)
	subtitle.position = Vector2(72, 116)
	subtitle.add_theme_color_override("font_color", Color("e8d8b8"))
	_home.add_child(subtitle)


func _build_menu() -> void:
	var meta := Progress.meta
	var panel := PanelContainer.new()
	panel.position = Vector2(56, 208)
	panel.custom_minimum_size = Vector2(MENU_WIDTH, 0)
	panel.add_theme_stylebox_override("panel", UiStyle.menu_panel_box(32, 28))
	_home.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 6)
	panel.add_child(column)

	continue_stage = next_story_stage()
	if not continue_stage.is_empty():
		_add(column, &"continue", "Continue", "Enter", "continue", "", continue_story, 78)
		column.add_child(MenuPage.Divider.new())
	var stars := _campaign_stars()
	_add(column, &"campaign", "Campaign", "C", "campaign", stars, open_campaign)
	_add(column, &"skirmish", "Skirmish", "S", "skirmish", "", open_page.bind(&"skirmish"))
	var joined := meta.joined_heroes().size()
	_add(column, &"heroes", "Heroes", "H", "heroes", "%d of %d" % [joined, meta.heroes_in_order().size()],
			open_page.bind(&"heroes"))
	var points := meta.points()
	_add(column, &"talents", "Talents", "T", "talents", ("%d point%s" % [points, "" if points == 1 else "s"]) if points > 0 else "",
			open_meta_tree)
	_add(column, &"codex", "Codex", "K", "codex", "", open_page.bind(&"codex"))
	_add(column, &"settings", "Settings", "O", "settings", "", open_page.bind(&"settings"))
	column.add_child(MenuPage.Divider.new())
	_add(column, &"credits", "Credits", "", "credits", "", open_page.bind(&"credits"))
	_add(column, &"quit", "Quit", "", "quit", "", ask_to_quit)
	var gap := Control.new()
	gap.custom_minimum_size = Vector2(0, 4)
	column.add_child(gap)
	column.add_child(UiStyle.menu_label(_records_text(), "small", 16, UiStyle.MENU_DIM))


func _add(column: VBoxContainer, id: StringName, text: String, key: String, icon_name: String, note: String,
		action: Callable, height: float = 64.0) -> void:
	var button := MenuItemButton.new(text, key, icon_name, note)
	button.custom_minimum_size = Vector2(0, height)
	if height > 70.0:
		button.add_theme_font_size_override("font_size", 50)
	button.pressed.connect(action)
	column.add_child(button)
	buttons[id] = button


## A card in the corner that says what comes next in the story.
func _build_story_card() -> void:
	if continue_stage.is_empty():
		return
	var stage: StageData = DataRegistry.stages.get(continue_stage)
	var campaign: CampaignData = DataRegistry.campaign_of(continue_stage)
	if stage == null or campaign == null:
		return
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", UiStyle.menu_panel_box(28, 20, false))
	card.custom_minimum_size = Vector2(600, 0)
	card.position = Vector2(1272, 856)
	_home.add_child(card)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 2)
	card.add_child(column)
	column.add_child(UiStyle.menu_label("NEXT IN THE STORY", "small", 16, UiStyle.MENU_GOLD))
	column.add_child(UiStyle.menu_label(stage.display_name, "button", 40))
	column.add_child(UiStyle.menu_label(_stage_note(stage).to_upper(), "small", 16, UiStyle.MENU_DIM))


## The stage Continue plays: the next open stage of the land the player is furthest into, or empty
## before the first win (then Campaign is the way in, with its prologue).
func next_story_stage() -> StringName:
	var meta := Progress.meta
	var best: StageData = null
	var best_stars := 0
	for campaign in meta.campaigns_in_order():
		var earned := meta.campaign_stars(campaign)
		var next := meta.next_stage(campaign)
		if next != null and earned > best_stars:
			best = next
			best_stars = earned
	return best.id if best != null else &""


func _stage_note(stage: StageData) -> String:
	if stage == null:
		return ""
	var campaign: CampaignData = DataRegistry.campaign_of(stage.id)
	if campaign == null:
		return stage.display_name
	return "%s, stage %d" % [campaign.display_name, campaign.stage_index(stage.id) + 1]


func _campaign_stars() -> String:
	var meta := Progress.meta
	var earned := 0
	var total := 0
	for campaign in meta.campaigns_in_order():
		earned += meta.campaign_stars(campaign)
		total += campaign.stages.size() * 3
	return "%d / %d stars" % [earned, total] if earned > 0 else ""


func _records_text() -> String:
	var profile := Progress.meta.profile
	if profile.runs_played == 0:
		return "NO RUNS YET"
	return "RUNS %d  -  WINS %d  -  BEST %d WAVES  -  %d FOES" % [
		profile.runs_played, profile.runs_won, profile.best_waves, profile.enemies_killed]


# --- Going places ------------------------------------------------------------------

## Opens a page by name: skirmish, heroes, codex, settings or credits.
func open_page(id: StringName) -> void:
	var target := _page(id)
	if target == null:
		return
	close_page()
	target.refresh()
	target.show()
	_home.hide()
	page = id


## Back to the title screen.
func close_page() -> void:
	if page.is_empty():
		return
	pages[page].hide()
	page = &""
	_home.show()


func _page(id: StringName) -> MenuPage:
	if pages.has(id):
		return pages[id]
	var made: MenuPage = null
	match id:
		&"skirmish":
			var skirmish := SkirmishPage.new()
			skirmish.play_requested.connect(play_skirmish)
			made = skirmish
		&"heroes":
			made = HeroesPage.new()
		&"codex":
			made = CodexPage.new()
		&"settings":
			made = SettingsPage.new()
		&"credits":
			made = CreditsPage.new()
	if made == null:
		return null
	made.hide()
	made.back_requested.connect(close_page)
	add_child(made)
	move_child(quit_dialog, -1)
	pages[id] = made
	return made


func continue_story() -> void:
	if continue_stage.is_empty() or not Progress.play_stage(continue_stage):
		open_campaign()
		return
	Progress.play_story(get_tree(), Progress.meta.story_before_stage(Story.shared(), continue_stage), GAME_SCENE)


## Opens the campaign map. The first time, the story's prologue plays first.
func open_campaign() -> void:
	var story := Story.shared()
	var first: Array[StringName] = []
	if story.has_cinematic(story.prologue) and not Progress.meta.has_seen(story.prologue):
		first.append(story.prologue)
	Progress.play_story(get_tree(), first, CAMPAIGN_SCENE)


func open_meta_tree() -> void:
	get_tree().change_scene_to_file(META_TREE_SCENE)


func play_skirmish() -> void:
	Progress.play_skirmish()
	get_tree().change_scene_to_file(GAME_SCENE)


## Where to unlock a locked map or difficulty level, such as "Unlock it in Talents: Hard Mode
## (Expeditions)."
static func unlock_hint(field: StringName, id: StringName) -> String:
	var node := Progress.meta.unlocked_by(field, id)
	if node == null:
		return ""
	var branch: String = MetaProgress.BRANCH_NAMES.get(node.region, "")
	if branch.is_empty():
		return "Unlock it in Talents: %s." % node.display_name
	return "Unlock it in Talents: %s (%s)." % [node.display_name, branch]


# --- Quitting ----------------------------------------------------------------------

func _build_quit_dialog() -> void:
	quit_dialog = Control.new()
	quit_dialog.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	quit_dialog.mouse_filter = Control.MOUSE_FILTER_STOP
	quit_dialog.hide()
	add_child(quit_dialog)
	var shade := ColorRect.new()
	shade.color = Color(0.02, 0.02, 0.04, 0.6)
	shade.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	quit_dialog.add_child(shade)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	quit_dialog.add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UiStyle.menu_panel_box(48, 32))
	center.add_child(panel)
	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 18)
	panel.add_child(column)
	var title := UiStyle.menu_title("Leave Solenne?", 72)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(title)
	var text := UiStyle.menu_label("The watch fires will burn until you return.\nYour progress is saved.", "body", 32,
			UiStyle.MENU_DIM)
	text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	column.add_child(text)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 24)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	column.add_child(row)
	var stay := MenuItemButton.new("Stay", "Esc")
	stay.custom_minimum_size = Vector2(280, 64)
	stay.pressed.connect(func() -> void: quit_dialog.hide())
	row.add_child(stay)
	var leave := MenuItemButton.new("Quit", "Q")
	leave.custom_minimum_size = Vector2(280, 64)
	leave.pressed.connect(func() -> void: get_tree().quit())
	row.add_child(leave)


func ask_to_quit() -> void:
	quit_dialog.show()


# --- Keys --------------------------------------------------------------------------

## On the title screen: Enter continues, and every menu entry has its letter. On a page, Esc goes
## back (Enter plays on the Skirmish page). Esc on the title screen asks before quitting.
func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key == null or not key.pressed or key.echo:
		return
	if quit_dialog.visible:
		match key.keycode:
			KEY_ESCAPE:
				quit_dialog.hide()
			KEY_Q, KEY_ENTER, KEY_KP_ENTER:
				get_tree().quit()
			_:
				return
		get_viewport().set_input_as_handled()
		return
	if not page.is_empty():
		match key.keycode:
			KEY_ESCAPE, KEY_BACKSPACE:
				close_page()
			KEY_ENTER, KEY_KP_ENTER:
				if page == &"skirmish":
					play_skirmish()
				elif page == &"heroes":
					(pages[page] as HeroesPage).toggle_party()
				else:
					return
			_:
				return
		get_viewport().set_input_as_handled()
		return
	match key.keycode:
		KEY_ENTER, KEY_KP_ENTER:
			if continue_stage.is_empty():
				open_campaign()
			else:
				continue_story()
		KEY_C:
			open_campaign()
		KEY_S:
			open_page(&"skirmish")
		KEY_H:
			open_page(&"heroes")
		KEY_T, KEY_M:
			open_meta_tree()
		KEY_K:
			open_page(&"codex")
		KEY_O:
			open_page(&"settings")
		KEY_ESCAPE:
			ask_to_quit()
		_:
			return
	get_viewport().set_input_as_handled()
