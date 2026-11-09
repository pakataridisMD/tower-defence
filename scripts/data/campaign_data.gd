class_name CampaignData
extends Resource
## A campaign: a chain of stages played in order. There is one for each element, and the
## Convergence, which opens once all six are done.

@export var id: StringName
@export var display_name: String
## Position on the campaign map, lowest first.
@export var order: int = 0
## Id of the element this campaign belongs to. Empty for the Convergence.
@export var element: StringName
## Short subtitle, such as "The Tide against the Volcano".
@export var tagline: String
@export_multiline var description: String
## Ids of campaigns that must be finished before this one opens.
@export var requires_campaigns: Array[StringName] = []
@export var stages: Array[StageData] = []

@export_group("Reward")
## Name of the lasting reward for finishing the campaign, such as "Sigil of Embers".
@export var reward_name: String
@export var reward_description: String
## Modifiers added to every run, skirmish or campaign, once the campaign is finished.
@export var reward_modifiers: Array[Modifier] = []


func stage_index(stage_id: StringName) -> int:
	for i in stages.size():
		if stages[i].id == stage_id:
			return i
	return -1
