#!/usr/bin/env python3
"""The thirty kinds of the Unbound hordes: five for each land's invaders, each with its own power.

This table is the source of truth for their names, numbers, powers, one-line descriptions and lore.
Running it writes data/enemies/<id>.tres for each (overwriting them) and docs/story/horde.md, the
bestiary. Art: tools/art/pix2d/horde.py draws them, tools/art/gen_horde_art.py animates them into the
game. Waves: tools/campaign/gen_campaign.py brings each horde into its land (HOSTS below).

    python3 tools/campaign/horde.py
    python3 tools/campaign/gen_campaign.py
    python3 tools/art/gen_horde_art.py && python3 tools/art/gen_game_art.py --enemies && godot --headless --import

The powers themselves live in RunSim (scripts/sim/run_sim.gd, see EnemyData.power for the list).
"""
import os

# Which land each horde invades (bible section 5), the Herald who leads it, and the art it was made by.
HOSTS = {
    "tide": {"name": "the Tide", "element": "water", "campaign": "ember_reach", "art": "Tidelore",
             "herald": "Saltmother Ourra"},
    "stone": {"name": "the Stone", "element": "earth", "campaign": "thunder_steppe", "art": "Runecarving",
              "herald": "Gorrath the Quarried"},
    "hollow": {"name": "the Hollow", "element": "void", "campaign": "verdant_deep", "art": "Starcraft",
               "herald": "the Pale Vesper"},
    "flame": {"name": "the Flame", "element": "fire", "campaign": "frostmere", "art": "Kindling",
              "herald": "Ashwick the Kindled"},
    "sky": {"name": "the Sky", "element": "storm", "campaign": "sunscar_canyon", "art": "Stormsong",
            "herald": "Vholt Stormcrown"},
    "grove": {"name": "the Grove", "element": "nature", "campaign": "hollow_rift", "art": "Rootcraft",
              "herald": "Mother Briar"},
}

# id, name, host, health, speed, armour, bounty, leak, tags, power, power numbers
# (interval, duration, radius, amount, limit), description (one line), lore (a short paragraph).
# A kind's place in the list is the order its land meets it: the first two from the land's first
# stage, then one more each stage.
ROSTER = [
    # ------------------------------------------------------------------------------------ the Tide
    ("brinecaller", "Brinecaller", "tide", 70, 66, 0, 5, 1, [], "douse", dict(interval=6.0, radius=150.0),
     "A drowned tide-priest. Its brine puts out burns and washes poison and frost off the horde around it.",
     "Tidefolk priests are drowned under the ice to be initiated and brought back up by their own people. "
     "These were brought back by the Saltmother instead. They came up still praying, salt in their mouths, "
     "ladling the cold sea over anything that burns."),
    ("netcaster", "Drowned Netcaster", "tide", 80, 64, 1, 5, 1, [], "net",
     dict(interval=7.0, duration=3.5, radius=210.0, amount=0.5),
     "A drowned fisherman who casts a weighted net over the strongest tower near him.",
     "The fleets of Pearlhaven went down in the first winter of the Opposites War. Their crews never stopped "
     "fishing. Now they cast for whatever stands on the shore, and a tower caught in their nets swings slow "
     "and heavy as a drowned man's arm."),
    ("mire_eel", "Mire Eel", "tide", 46, 92, 0, 4, 1, ["fast"], "submerge",
     dict(interval=7.0, duration=2.0, amount=0.6),
     "A drowned eel as long as a boat. Every few seconds it dives under the road, out of reach, and swims faster.",
     "Tidelore remembers everything water has touched, and the deep remembers its eels. They slide up the "
     "flooded roads in the dark of the Tide's rain, a lantern lure swinging over a mouth of needles, and vanish "
     "under the mud the moment anything looks at them."),
    ("fogwife", "Fogwife", "tide", 55, 70, 0, 5, 1, [], "fog",
     dict(interval=8.0, duration=4.0, radius=170.0, amount=0.3),
     "A faceless drowned seer. She breathes sea-fog over the towers near her, and they cannot see as far.",
     "The great seers of the Tide Throne paid for every vision with a memory. The Fogwives paid with all of them, "
     "their names, their faces, their children. What is left breathes the fog of a sea that has forgotten "
     "where the shore is."),
    ("rimeback", "Rimeback", "tide", 120, 50, 3, 7, 2, ["armoured"], "rime_shell",
     dict(interval=8.0, amount=0.4),
     "A crab the size of a cart, crusted in old ice. Its rime shell soaks up blows until it breaks, then grows back.",
     "Dragged up from under Frostmere's ice by the mad Sea-Queen's voice, the Rimebacks carry a winter on their "
     "backs. Break the crust and the cold grows it back over them, layer on layer, the way the lake freezes "
     "a little more each night."),
    # ------------------------------------------------------------------------------------ the Stone
    ("oathbroken", "Oathbroken", "stone", 110, 58, 1, 6, 1, ["armoured"], "accrete",
     dict(amount=1.0, limit=10.0),
     "A Stoneborn turning to stone for a broken oath. Every blow it takes grows more stone over it.",
     "A rune can never be uncarved, and a Stoneborn who breaks a carved oath turns slowly to stone. The Mountain-King's "
     "madness broke every oath in Kharum at once. The Oathbroken march with granite growing through their "
     "skin, and hurting them only hurries it."),
    ("quarry_hound", "Quarry Hound", "stone", 70, 82, 1, 5, 1, [], "charge",
     dict(interval=7.0, duration=1.6, amount=1.2),
     "A hunting hound carved from quarry stone. It charges down the road now and then, too heavy to slow or push.",
     "Runewrights of the Deep Halls carved hounds to run down oath-breakers, and an oath of pursuit gave them "
     "legs. Orrok's madness pointed them at the Steppe. When one catches the scent it charges, and nothing "
     "short of a mountain slows it."),
    ("runebearer", "Runebearer", "stone", 140, 50, 3, 8, 2, ["armoured"], "bulwark",
     dict(radius=140.0, amount=5.0),
     "Carries a carved oath-stone on its back. Every ally near it gains 5 armour.",
     "Oath-keepers carry the great vows of Kharum carved in standing stones, so that whole companies can swear "
     "by them. The runes still burn. Every Stoneborn within sight of one stands as if the mountain stood "
     "behind it."),
    ("geode", "Geode Brute", "stone", 160, 50, 2, 9, 2, ["armoured"], "facets",
     dict(amount=0.65),
     "A boulder split open on a heart of crystal. Splash, chains and bursts lose most of their bite on its facets.",
     "The deepest halls of Kharum hold stones that were never cut, only listened to. Orrok's voice woke them. They "
     "stand up split open on hearts of violet crystal, and any blow spread thin across them is scattered "
     "like light through a prism."),
    ("menhir", "Menhir Walker", "stone", 200, 42, 4, 10, 2, ["armoured"], "steadfast",
     dict(radius=150.0),
     "A walking standing stone. The horde near it cannot be slowed or pushed back.",
     "The standing stones of the Thunder Steppe were set by the Galeborn to hold the sky still for a moment "
     "of prayer. Someone carved a king's face into one. Now it walks, and where it stands the ground holds "
     "fast: frost, tide and thunder cannot move what walks beside it."),
    # ------------------------------------------------------------------------------------ the Hollow
    ("lightdrinker", "Lightdrinker", "hollow", 65, 68, 0, 5, 1, [], "eclipse",
     dict(interval=9.0, duration=4.0, radius=170.0, amount=0.35),
     "A Veilwalker who spent all her light on starcraft. Her black lantern dims the towers near her.",
     "Every spell of starcraft darkens something of the caster: hair, eyes, shadow. Lightdrinkers kept casting "
     "after the light ran out, and now they borrow it. Her lantern burns black, and towers in its gloom "
     "strike like men fighting in the dark."),
    ("umbral_stalker", "Umbral Stalker", "hollow", 45, 108, 0, 4, 1, ["fast"], "stalk",
     dict(amount=0.5),
     "A great cat made of the dark between stars. Towers only see it when it comes within half their range.",
     "The Star-Queen's hunters rode cats of living night on the road of the dead. Without their riders they hunt "
     "alone, pelts full of tiny stars. You do not see one coming. You see it arrive."),
    ("gravecaller", "Gravecaller", "hollow", 80, 60, 0, 6, 1, [], "raise",
     dict(interval=8.0, radius=180.0, amount=0.4, limit=2.0),
     "A deathwalker who walks the road of the dead the wrong way. He calls the horde's fallen back up.",
     "Veilwalkers walk the dead to the edge of the dark and leave them there. The Gravecallers walk back carrying "
     "them. Where the horde falls near one, the dead get up again, slower, quieter, still marching."),
    ("wailing_widow", "Wailing Widow", "hollow", 60, 70, 0, 5, 1, [], "wail",
     dict(duration=3.0, radius=160.0),
     "A widow who followed her husband down the road of the dead. Her dying scream silences the towers near her.",
     "She would not let him walk the road alone. Nyxara's madness opened it, and she went down it after him, and "
     "found it empty. She has been screaming ever since. Struck down, the scream breaks loose, and nothing near "
     "her can work its art until it fades."),
    ("voidmaw", "Voidmaw", "hollow", 130, 55, 2, 8, 2, [], "devour",
     dict(radius=160.0, amount=0.15),
     "A thing that is nearly all mouth. It heals whenever the horde dies near it.",
     "Something grew in the dark at the bottom of the Rift while the Veilwalkers mapped the stars above it. It "
     "has a crown of eyes and a mouth full of other stars, and it follows the horde for what falls."),
    # ------------------------------------------------------------------------------------ the Flame
    ("cinderhound", "Cinderhound", "flame", 50, 104, 0, 4, 1, ["fast"], "fireborn",
     dict(amount=2.0),
     "A hound of living cinder. Burns heal it instead of hurting it, and frost melts off it twice as fast.",
     "The Forge-King's hunting dogs lay down in his forges when he slept and got up when he went mad. Their ribs glow "
     "through the cinder of their hides. Feed them fire and they only run harder."),
    ("smoke_wraith", "Smoke Wraith", "flame", 50, 86, 0, 5, 1, [], "smoke",
     dict(amount=0.35),
     "The smoke of a burned town that would not blow away. About one blow in three goes straight through it.",
     "When the first towns of the Ember Reach burned, their smoke did not rise. It walked. There is an ember at the "
     "heart of each one, the last warm hearth of a house no one lives in, and most of what is thrown at it "
     "passes through soot."),
    ("glass_singer", "Glass-Singer", "flame", 65, 66, 0, 6, 1, [], "glass_ward",
     dict(interval=7.0, radius=160.0, limit=3.0),
     "A cold old Kindler who sings glass into being. She wards three allies with glass that stops a tower's blow.",
     "Kindlers pay with their own heat. The Glass-Singers sang sand into glass until they had none left: their arms "
     "are blue, their rune tattoos still glowing. Their song hangs panes of ringing glass before the horde, "
     "and each one stops a single blow before it shatters."),
    ("slagwalker", "Slagwalker", "flame", 120, 50, 12, 8, 2, ["armoured"], "meltdown",
     dict(amount=1.5),
     "A smith-lord sealed in plates of slag. Heavily armoured, but every hit knocks some of the slag away.",
     "The smith-lords of Pyrrhenhall turned anger into blades. When the Forge-King went mad, some turned themselves. "
     "They walk in fused plates of slag with the furnace still white inside, and every blow that lands "
     "knocks loose a plate that never grows back."),
    ("brass_juggernaut", "Brass Juggernaut", "flame", 220, 40, 5, 12, 3, ["armoured"], "momentum",
     dict(amount=0.08, limit=0.8),
     "A walking siege furnace. It gets faster the longer it walks unchecked; a slow, stun or push resets it.",
     "Siege engines of the Ember Throne, fed on coal and kindled runes, built to batter down the gates of Pearlhaven. "
     "The Forge-King's madness woke the fires in their bellies. They start slow. Left alone, they do not stay slow."),
    # ------------------------------------------------------------------------------------ the Sky
    ("gale_harpy", "Gale Harpy", "sky", 45, 98, 0, 4, 1, ["fast"], "tailwind",
     dict(interval=8.0, radius=130.0, amount=110.0),
     "A storm-winged hunter. Now and then a gust of its wings carries it and the horde near it down the road.",
     "Galeborn sky-riders flew with hunting birds the size of men. The mad storm made riders and birds one thing, "
     "screaming. When they beat their wings the whole road leans with the wind."),
    ("spark_wisp", "Spark Wisp", "sky", 28, 118, 0, 3, 1, ["fast"], "static",
     dict(duration=2.0),
     "A crackling scrap of a dead stormsinger's last note. The tower that kills it is shocked silent for 2 s.",
     "A stormsinger's last note does not end when the singer does. On the Steppe they drift in shoals, skulls of white "
     "light inside balls of lightning, and they give the shock back to whatever puts them out."),
    ("voiceless", "Voiceless", "sky", 70, 64, 0, 6, 1, [], "hush",
     dict(radius=160.0),
     "A stormsinger who sang her voice away. Towers near her deal damage but their burns, slows and curses do nothing.",
     "Stormsong costs the singer's breath and voice. The Voiceless sang until both were gone and kept on singing, "
     "mouths sewn shut, hands conducting. Where they walk, the towers' arts fall as silent as they are."),
    ("stormrider", "Stormrider", "sky", 85, 88, 1, 6, 1, [], "spur",
     dict(duration=2.0, amount=0.15, limit=0.6),
     "A dead sky-rider on a lightning-maned horse. Every hit it takes spurs it faster for a moment.",
     "Aurath ruled from the saddle, and his riders died in it. The storm still rides them. Lance couched, mane "
     "crackling, a Stormrider takes every wound as the touch of a spur."),
    ("squall_witch", "Squall Witch", "sky", 60, 66, 0, 6, 1, [], "gust",
     dict(interval=6.0, radius=150.0),
     "A hag riding a gust. Every few seconds she flings the wind out and blows the towers' shots out of the air.",
     "She sold her voice to the wind of the high passes for a broom and a bad temper, and the storm took the rest. "
     "When she throws out her arm, arrows turn, bolts tumble and fire goes out mid-flight."),
    # ------------------------------------------------------------------------------------ the Grove
    ("briarling", "Briarling", "grove", 26, 100, 0, 2, 1, ["fast"], "swarm",
     dict(radius=90.0, amount=0.08, limit=0.5),
     "A running knot of bramble. Each Briarling near it makes it a little faster.",
     "What comes up where a Seedsower's seed falls. Knee-high, red berries for eyes, they come in handfuls and run "
     "together like a pack of thorny hares."),
    ("seedsower", "Seedsower", "grove", 90, 58, 0, 6, 1, [], "sow",
     dict(interval=6.0, duration=5.0, amount=2.0),
     "A grove-planter flinging glowing seeds. Each seed sprouts two Briarlings on the road a few seconds later.",
     "Rootcraft is planted, not cast, and grows into its effect. The Seedsowers have been sowing for three hundred "
     "years and no longer remember what they meant to grow. What comes up has thorns."),
    ("greenwitch", "Greenwitch", "grove", 70, 64, 0, 6, 1, [], "remedy",
     dict(radius=150.0),
     "A Deepwood apothecary. Poison on the horde near her heals it instead of hurting it.",
     "Healing and poison are the same craft in the Green Realm, a matter of dose. The Greenwitches never forgot it. "
     "Around her, the venom of Nature's own towers turns to medicine."),
    ("briar_stag", "Briar Stag", "grove", 75, 86, 0, 6, 1, [], "bound",
     dict(interval=6.0, amount=90.0),
     "A great stag grown through with bramble. Slowed or caught, it bounds clear down the road and shakes it off.",
     "The white stag of the Green Queen's hunts, gone dark and wound with thorns, wearing a crown of blood-red "
     "flowers. Frost and mud cannot hold it: catch it and it leaps clear."),
    ("barkhulk", "Barkhulk", "grove", 180, 42, 3, 11, 3, ["armoured"], "grow",
     dict(interval=6.0, amount=0.1, limit=5.0),
     "An ancient oak torn up and walking. Every 6 s it grows, gaining a tenth more health, up to five times.",
     "Rootcraft costs time, and the Barkhulks are made of it: oaks older than the Concord, torn up by the roots when "
     "the Green Queen's madness called them. They keep growing as they walk. The longer one lives, the bigger "
     "it gets."),
]

# Seedsower's seeds sprout these.
SOWS = {"seedsower": "briarling"}


def ids_of(host):
    return [r[0] for r in ROSTER if r[2] == host]


def sn(v):
    return f'&"{v}"'


def string(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


# Which of the Unbound's three kinds each one is (bible section 4): Hollowed (living people the
# Unmaking emptied), Risen (the dead, marching) or Wild (beasts and spirits of the invading element).
# Its description starts with the kind, as the first horde's do.
KIND = {
    "brinecaller": "Risen", "netcaster": "Risen", "mire_eel": "Wild", "fogwife": "Hollowed", "rimeback": "Wild",
    "oathbroken": "Hollowed", "quarry_hound": "Wild", "runebearer": "Hollowed", "geode": "Wild", "menhir": "Wild",
    "lightdrinker": "Hollowed", "umbral_stalker": "Wild", "gravecaller": "Hollowed", "wailing_widow": "Risen",
    "voidmaw": "Wild", "cinderhound": "Wild", "smoke_wraith": "Wild", "glass_singer": "Hollowed",
    "slagwalker": "Hollowed", "brass_juggernaut": "Wild", "gale_harpy": "Wild", "spark_wisp": "Wild",
    "voiceless": "Hollowed", "stormrider": "Risen", "squall_witch": "Hollowed", "briarling": "Wild",
    "seedsower": "Hollowed", "greenwitch": "Hollowed", "briar_stag": "Wild", "barkhulk": "Wild",
}


# How each kind takes damage from the elements (ElementRules.PROFILES in scripts/core/element_rules.gd):
# attuned = immune to its own element, double from the opposite; warded = immune to its own, half from both
# neighbours, double from the opposite; tank = a quarter from its own, 0.6x from the rest, double from the
# opposite. The rest are plain (half from its own, 1.5x from the opposite). One of each per horde where
# it fits, so every land asks for its opposite element and punishes a one-element build.
AFFINITY = {
    "brinecaller": "attuned", "fogwife": "warded", "rimeback": "tank",
    "quarry_hound": "attuned", "runebearer": "warded", "menhir": "tank",
    "lightdrinker": "attuned", "wailing_widow": "warded", "voidmaw": "tank",
    "cinderhound": "attuned", "glass_singer": "warded", "brass_juggernaut": "tank",
    "spark_wisp": "attuned", "voiceless": "warded",
    "greenwitch": "attuned", "seedsower": "warded", "barkhulk": "tank",
}


def write_enemy(row):
    eid, name, host, hp, speed, armour, bounty, leak, tags, power, nums, desc, lore = row
    h = HOSTS[host]
    lines = ['[gd_resource type="Resource" script_class="EnemyData" format=3]', "",
             '[ext_resource type="Script" path="res://scripts/data/enemy_data.gd" id="1_enemy"]', "", "[resource]",
             'script = ExtResource("1_enemy")', f"id = {sn(eid)}", f"display_name = {string(name)}",
             f"max_health = {float(hp)}", f"speed = {float(speed)}"]
    if armour:
        lines.append(f"armour = {float(armour)}")
    lines += [f"bounty = {bounty}", f"leak_damage = {leak}"]
    if tags:
        lines.append("tags = Array[StringName]([%s])" % ", ".join(sn(t) for t in tags))
    lines.append(f"description = {string(KIND[eid] + '. ' + desc)}")
    lines.append(f"element = {sn(h['element'])}")
    if eid in AFFINITY:
        lines.append(f"affinity = {sn(AFFINITY[eid])}")
    lines.append(f"power = {sn(power)}")
    for key, field in (("interval", "power_interval"), ("duration", "power_duration"), ("radius", "power_radius"),
                       ("amount", "power_amount"), ("limit", "power_limit")):
        if key in nums:
            lines.append(f"{field} = {float(nums[key])}")
    if eid in SOWS:
        lines.append(f"summon = {sn(SOWS[eid])}")
    lines += [f"horde = {sn(host)}", f"lore = {string(lore)}"]
    with open(f"data/enemies/{eid}.tres", "w") as fh:
        fh.write("\n".join(lines) + "\n")


def write_bestiary():
    out = ["# The Unbound: a bestiary of the six hordes", "",
           "Generated by `tools/campaign/horde.py` (edit the table there, not this file). Each land is invaded by "
           "the horde from across the ring, led by that horde's Herald. Every kind of the horde "
           "was shaped by the art of its kingdom, and every one has a power of its own.", ""]
    for host, h in HOSTS.items():
        out += [f"## {h['name'][0].upper() + h['name'][1:]} ({h['art']}), invading {h['campaign'].replace('_', ' ').title()}",
                "", f"Led by {h['herald']}. Element: {h['element'].title()}.", ""]
        for row in ROSTER:
            if row[2] != host:
                continue
            eid, name, _h, hp, speed, armour, bounty, leak, tags, power, nums, desc, lore = row
            out += [f"### {name}", "", f"*{KIND[eid]}. {desc}*", "", lore, "",
                    f"Health {hp}, speed {speed}, armour {armour}, bounty {bounty}, lives {leak}. Power: `{power}`."
                    + (f" Affinity: {AFFINITY[eid]}." if eid in AFFINITY else ""), ""]
    with open("docs/story/horde.md", "w") as fh:
        fh.write("\n".join(out))


def main():
    assert set(KIND) == {r[0] for r in ROSTER}
    assert set(AFFINITY) <= set(KIND) and set(AFFINITY.values()) <= {"attuned", "warded", "tank"}
    assert len(ROSTER) == 30 and len({r[0] for r in ROSTER}) == 30 and len({r[9] for r in ROSTER}) == 30
    for row in ROSTER:
        write_enemy(row)
    write_bestiary()
    print("Wrote %d enemies and docs/story/horde.md" % len(ROSTER))


if __name__ == "__main__":
    os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    main()
