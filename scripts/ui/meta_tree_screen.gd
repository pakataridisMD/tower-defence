extends Control
## The meta tree, opened from the main menu. Every finished run pays meta points, and the nodes
## bought with them count in every later run. Each change is saved straight away, and refunds are
## always free.

const MENU_SCENE := "res://scenes/main.tscn"
const REFUND_ALL_TEXT := "Refund all"
const CONFIRM_TEXT := "Click again to refund all"
## How long the refund-all button waits for the confirming second click.
const CONFIRM_SECONDS := 3.0

var web: SkillWebView
var refund_all: Button
var _confirming := false


## Regions for the meta tree: one per branch, in the branch colour.
static func branch_regions() -> Dictionary[StringName, SkillWebView.Region]:
	var result: Dictionary[StringName, SkillWebView.Region] = {}
	for id in MetaProgress.BRANCH_NAMES:
		result[id] = SkillWebView.Region.new(MetaProgress.BRANCH_NAMES[id], MetaProgress.BRANCH_COLORS[id])
	return result


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UiStyle.make_theme()
	var rules := DataRegistry.run_rules
	web = SkillWebView.new()
	web.title = "Meta tree"
	web.subtitle = ("Every run pays meta points, won or lost: %d for each wave cleared and %d more for a win. " +
		"What you take here counts in every run. Refunds are always free: right-click a node at the tip " +
		"of a branch.") % [rules.meta_points_per_wave, rules.meta_points_for_win]
	web.points_noun = "meta point"
	web.close_text = "Back (Esc)"
	web.taken_text = "Taken. Refund the nodes past it first."
	web.can_refund = func(id: StringName) -> bool: return Progress.meta.tree.can_refund(id)
	add_child(web)
	web.close_requested.connect(back_to_menu)
	web.node_clicked.connect(func(id: StringName) -> void: Progress.allocate_meta(id))
	web.node_refund_requested.connect(func(id: StringName) -> void: Progress.refund_meta(id))
	refund_all = UiStyle.button(REFUND_ALL_TEXT, 20)
	refund_all.custom_minimum_size = Vector2(290, 0)
	refund_all.pressed.connect(_on_refund_all)
	web.add_header_button(refund_all)
	Progress.changed.connect(_refresh)
	_refresh()


func back_to_menu() -> void:
	get_tree().change_scene_to_file(MENU_SCENE)


func _unhandled_input(event: InputEvent) -> void:
	var key := event as InputEventKey
	if key != null and key.pressed and not key.echo and key.keycode == KEY_ESCAPE:
		get_viewport().set_input_as_handled()
		back_to_menu()


## Shows the current tree, and turns refund-all off when there is nothing to refund.
func _refresh() -> void:
	if web.tree != Progress.meta.tree:
		web.show_tree(Progress.meta.tree, branch_regions())
	refund_all.disabled = Progress.meta.tree.allocated_ids().size() <= 1
	if refund_all.disabled:
		_cancel_confirm()


## Refunding everything takes two clicks, so a stray click does not undo a whole tree.
func _on_refund_all() -> void:
	if not _confirming:
		_confirming = true
		refund_all.text = CONFIRM_TEXT
		get_tree().create_timer(CONFIRM_SECONDS).timeout.connect(_cancel_confirm)
		return
	_cancel_confirm()
	Progress.reset_meta()


func _cancel_confirm() -> void:
	_confirming = false
	refund_all.text = REFUND_ALL_TEXT
