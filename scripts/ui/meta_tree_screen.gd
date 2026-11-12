extends Control
## The meta tree, opened from the main menu as Talents. Every finished run pays meta points, and each
## talent bought with them adds one tower (a dual, a triple or a long-range tower) to every later run. Each change is saved straight away, and refunds
## are always free. The tree is far bigger than the screen: drag or WASD to move, wheel to zoom.

const MENU_SCENE := "res://scenes/main.tscn"
const REFUND_ALL_TEXT := "Refund all"
const CONFIRM_TEXT := "Click again to refund all"
## How long the refund-all button waits for the confirming second click.
const CONFIRM_SECONDS := 3.0
## The rings the talents sit on, drawn as dotted circles behind them (see tools/meta/gen_meta_tree.py).
const RING_RADII: Array[float] = [250.0, 470.0, 700.0, 950.0, 1190.0]

var web: SkillWebView
var refund_all: Button
var whole_tree: Button
var _confirming := false


## Regions for the meta tree: one per branch, in the branch colour.
static func branch_regions() -> Dictionary[StringName, SkillWebView.Region]:
	var result: Dictionary[StringName, SkillWebView.Region] = {}
	for id in MetaProgress.BRANCH_NAMES:
		result[id] = SkillWebView.Region.new(MetaProgress.BRANCH_NAMES[id], MetaProgress.BRANCH_COLORS[id])
	# Every branch circles the whole wheel, so a glow at its middle would sit on the Origin, and a
	# name by its farthest node would label only one spot of it.
	for region: SkillWebView.Region in result.values():
		region.aura = false
		region.label = false
	return result


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	theme = UiStyle.make_theme()
	var rules := DataRegistry.run_rules
	web = SkillWebView.new()
	web.title = "Talents"
	web.navigable = true
	web.ring_radii = RING_RADII
	web.count_noun = "talents"
	web.subtitle = ("Every talent adds a tower to all your runs, and any talent can be bought at any time; the six " +
		"base towers are always yours. Meta points pay for records: %d per new wave cleared on a stage or map, %d " +
		"for its first win, %d for a replay without a record (%d times per stage). Right-click refunds for free.") % [
		rules.meta_points_per_wave, rules.meta_points_for_win, MetaProgress.REPLAY_WIN_POINTS, MetaProgress.REPLAY_LIMIT]
	web.points_noun = "meta point"
	web.close_text = "Back (Esc)"
	web.taken_text = "Taken. Right-click to refund."
	web.can_refund = func(id: StringName) -> bool: return Progress.meta.tree.can_refund(id)
	add_child(web)
	web.close_requested.connect(back_to_menu)
	web.node_clicked.connect(func(id: StringName) -> void: Progress.allocate_meta(id))
	web.node_refund_requested.connect(func(id: StringName) -> void: Progress.refund_meta(id))
	refund_all = UiStyle.button(REFUND_ALL_TEXT, 20)
	refund_all.custom_minimum_size = Vector2(290, 0)
	refund_all.pressed.connect(_on_refund_all)
	web.add_header_button(refund_all)
	whole_tree = UiStyle.button("Whole tree (F)", 20)
	whole_tree.pressed.connect(func() -> void: web.show_whole_tree())
	web.add_header_button(whole_tree)
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
