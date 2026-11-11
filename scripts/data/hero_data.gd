class_name HeroData
extends Resource
## A playable hero: a champion who joins over the campaign. A run takes a party of up to
## MAX_PARTY heroes. Each is summoned once onto a free build cell, fights like a strong tower (about as
## much as two good towers, so the towers the player builds still carry the run), grows a level for every wave it fights, lifts the towers around it with its
## aura and has one signature ability on its own key.

const MAX_PARTY := 3
const MAX_LEVEL := 10
## The ability becomes `ultimate` from this level on.
const ULTIMATE_LEVEL := 6
## Each level above the first adds this much damage and range.
const DAMAGE_PER_LEVEL := 0.06
const RANGE_PER_LEVEL := 0.02
## Towers this many cells from a hero get its aura.
const AURA_CELLS := 2.0

@export var id: StringName
@export var display_name: String
@export var title: String
## One line for tooltips and the party picker.
@export_multiline var blurb: String
## Order heroes join in. Used to sort the party picker and the default party.
@export var order: int = 0
## The element shown on the hero's frame, or empty for none. Its attack's elements are in `attack`.
@export var element: StringName
## Campaign stage whose first win brings the hero, or empty for a hero there from the start.
@export var joins_after: StringName
## A hero who arrives during a stage instead: that stage and the wave they arrive at. They join
## for good when the stage is won.
@export var arrives_in: StringName
@export var arrives_at_wave: int = 0
## How the hero attacks, as a tower. Its id should be the hero's id.
@export var attack: TowerData

@export_group("Aura")
## Modifiers for every tower within AURA_CELLS cells. Heroes do not get each other's auras.
@export var aura: Array[Modifier] = []
## Shown on the hero's panel, such as "+25% attack speed".
@export var aura_text: String
## Every hero in the party fights this many levels higher.
@export var aura_hero_levels: int = 0
## After each wave, a life back for every this many towers in the aura (0 turns it off), up to
## aura_lives_max.
@export var aura_lives_per_towers: int = 0
@export var aura_lives_max: int = 0

@export_group("Ability")
@export var ability: HeroAbility
## The stronger ability used from ULTIMATE_LEVEL on.
@export var ultimate: HeroAbility
## Extra modifiers on the hero's own attack from ULTIMATE_LEVEL on.
@export var ultimate_modifiers: Array[Modifier] = []
## One line about what the ultimate adds, for the hero's panel.
@export var ultimate_text: String

@export_group("Voice")
## Short lines shown when the hero is summoned or casts.
@export var barks: PackedStringArray = []


## The ability the hero uses at a level.
func ability_at(level: int) -> HeroAbility:
	return ultimate if level >= ULTIMATE_LEVEL and ultimate != null else ability
