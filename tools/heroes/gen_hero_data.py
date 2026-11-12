#!/usr/bin/env python3
"""Writes data/heroes/<id>.tres for every playable hero.

The heroes, their joining points and their numbers come from the heroes design doc
("Heroes of the Ring: design") and the lore bible (section 7.3). Edit HEROES below and run:

    python3 tools/heroes/gen_hero_data.py

Kinds of modifier: 0 adds (FLAT), 1 is increased (summed), 2 is more (multiplied).
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "data" / "heroes"
CELL = 64

FLAT, INC, MORE = 0, 1, 2
AIMED, SELF, BOARD, CROWDS = 0, 1, 2, 3


def mod(stat, kind, value, tags=()):
    return {"stat": stat, "kind": kind, "value": value, "tags": list(tags)}


def fx(kind, **values):
    return {"kind": kind, **values}


HEROES = [
    dict(
        id="tamsin", name="Tamsin Reed", title="Captain of the Lanternguard", element="", joins="",
        blurb="Solenne's toughest soldier, always the last one through the gate.",
        attack=dict(desc="Lantern-pole thrusts that run through two enemies.", damage=10.0, aps=1.2, range=160.0,
                    chain_count=1, chain_range=70.0),
        aura=[mod("damage", INC, 0.08)], aura_text="+8% damage",
        ability=dict(name="Lanternguard's Stand", cooldown=100.0, target=SELF, radius=2.5, damage=50.0, hold=1.5,
                     desc="Every enemy within 2.5 cells of her is held for 1.5 seconds and takes a blow."),
        ultimate=dict(name="Lanternguard's Stand", cooldown=100.0, target=SELF, radius=2.5, damage=70.0, hold=2.5,
                      duration=5.0, modifiers=[mod("attacks_per_second", INC, 0.12)],
                      desc="Holds every enemy within 2.5 cells for 2.5 seconds, and every tower attacks 12% faster for 5 seconds."),
        ultimate_text="Holds for 2.5 s, and towers attack 12% faster for 5 s",
        barks=["Last one through the gate. As always.", "Lanterns up!", "Hold the line."],
    ),
    dict(
        id="brannoc", name="Brannoc Emberhand", title="Smith-Lord of the Reach", element="fire", joins="ember_2",
        blurb="A giant smith who forged half the gates of Solenne. His forge-hammer never cools.",
        attack=dict(desc="Throws a white-hot hammer that bursts and sets enemies burning.", elements=["fire"],
                    damage=10.0, aps=0.7, range=150.0, splash=50.0, projectile_speed=520.0,
                    effects=[fx("burn", damage_per_second=5.0, duration=4.0)]),
        aura=[mod("burn_damage", INC, 0.15)], aura_text="+15% burn damage",
        ability=dict(name="Forgefall", cooldown=90.0, target=AIMED, radius=1.25, damage=40.0,
                     effects=[fx("burn", damage_per_second=5.0, duration=4.0)],
                     desc="A molten hammer falls where you choose: a blast that leaves everything burning."),
        ultimate=dict(name="Forgefall", cooldown=90.0, target=AIMED, radius=1.25, damage=50.0,
                      effects=[fx("burn", damage_per_second=8.0, duration=6.0)],
                      desc="A molten hammer falls where you choose and leaves a pool of lava that burns for 6 seconds."),
        ultimate_text="Leaves lava that burns far harder for 6 s",
        barks=["The forge is lit!", "Strike while it's hot!", "Ha! Stand still, I'm aiming."],
    ),
    dict(
        id="kaela", name="Kaela Stormrider", title="Marshal of the Steppe", element="storm", joins="storm_2",
        blurb="First rider of the Galeborn, who had never ridden in the direction of retreat.",
        attack=dict(desc="A lance of lightning that jumps through three enemies.", elements=["storm"],
                    damage=6.0, aps=1.4, range=170.0, chain_count=2, chain_range=120.0, chain_falloff=0.15),
        aura=[mod("attacks_per_second", INC, 0.12)], aura_text="+12% attack speed",
        ability=dict(name="Thunder Charge", cooldown=120.0, target=BOARD, damage=10.0, knockback=1.0 * CELL,
                     desc="Kaela rides the road on Thunderclap, knocking every enemy back one cell."),
        ultimate=dict(name="Thunder Charge", cooldown=120.0, target=BOARD, damage=12.0, knockback=1.0 * CELL, hold=1.0,
                      desc="Kaela rides the road, knocking every enemy back one cell and stunning them for 1 second."),
        ultimate_text="Also stuns for 1 s",
        barks=["Ride!", "Thunderclap, with me!", "We don't ride backwards."],
    ),
    dict(
        id="sylvaine", name="Sylvaine Thornwhisper", title="Bow of the Deep", element="nature", joins="nature_2",
        blurb="Three hundred years old, she held Elderhollow alone for nine days.",
        attack=dict(desc="Very long range arrows that poison. Poison jumps on when an enemy dies.", elements=["nature"],
                    damage=7.0, aps=1.0, range=220.0, projectile_speed=900.0, poison_spread=1,
                    effects=[fx("poison", damage_per_second=4.0, duration=5.0, max_stacks=2)]),
        aura=[mod("attack_range", INC, 0.1)], aura_text="+10% range",
        ability=dict(name="Hail of Thorns", cooldown=80.0, target=AIMED, radius=1.5, damage=20.0,
                     effects=[fx("poison", damage_per_second=6.0, duration=5.0)],
                     desc="A rain of arrows where you choose. Heavy poison that spreads when they die."),
        ultimate=dict(name="Hail of Thorns", cooldown=80.0, target=AIMED, radius=1.5, damage=25.0,
                      effects=[fx("poison", damage_per_second=9.0, duration=5.0)],
                      desc="A rain of arrows where you choose. Heavier poison that spreads twice when they die."),
        ultimate_modifiers=[mod("poison_spread_count", FLAT, 1)],
        ultimate_text="Heavier poison that spreads twice",
        barks=["Patience.", "One arrow. One.", "The Deep remembers."],
    ),
    dict(
        id="mirelle", name="Mirelle the Tide-Seer", title="Seer of Frostmere", element="water", joins="water_2",
        blurb="A blind young seer who reads the future in ice.",
        attack=dict(desc="Ice shards that slow by 25%.", elements=["water"], damage=8.0, aps=1.0, range=170.0,
                    effects=[fx("slow", slow=0.25, duration=2.0)]),
        aura=[mod("slow_strength", INC, 0.12)], aura_text="+12% slow strength",
        ability=dict(name="Frozen Hour", cooldown=150.0, target=BOARD, hold=1.5,
                     desc="The whole board freezes for 1.5 seconds. Bosses are slowed instead."),
        ultimate=dict(name="Frozen Hour", cooldown=150.0, target=BOARD, hold=2.0,
                      effects=[fx("curse", damage_taken=0.15, duration=2.0)],
                      desc="The whole board freezes for 2 seconds, and frozen enemies take 15% more damage."),
        ultimate_text="Holds for 2 s, and frozen enemies take 15% more damage",
        barks=["Not that one. The next one.", "I know. I saw.", "Cold now. Then quiet."],
    ),
    dict(
        id="gorrim", name="Gorrim Stonebeard", title="Shield of the Canyon", element="earth", joins="earth_2",
        blurb="A Stoneborn shieldmaster with a ring braided into his beard for every comrade he has buried.",
        attack=dict(desc="A heavy pick that cracks armour.", elements=["earth"], damage=21.0, aps=0.5, range=140.0,
                    projectile_speed=480.0, effects=[fx("shatter", armour_reduction=1.0, duration=5.0, max_stacks=3)]),
        aura=[mod("armour_ignore", FLAT, 0.1)], aura_text="Towers ignore 10% of armour",
        ability=dict(name="Bulwark", cooldown=100.0, target=AIMED, radius=1.0, hold=2.5,
                     desc="Gorrim's stone-door shield lands on the road where you choose and holds everything there for 2.5 seconds."),
        ultimate=dict(name="Bulwark", cooldown=100.0, target=AIMED, radius=1.0, hold=3.0, burst=60.0,
                      desc="Holds everything where you choose for 3 seconds, then the wall bursts and hurts them."),
        ultimate_text="Holds for 3 s, and the wall bursts when it falls",
        barks=["Hold.", "No more rings.", "Stone doesn't move. Neither do I."],
    ),
    dict(
        id="corvin", name="Corvin the Uncrowned", title="Ranger of the Rift", element="void", joins="void_2",
        blurb="The exiled heir of the Veilwalkers, who was right about the Regent all along.",
        attack=dict(desc="A blade of star-glass that curses: cursed enemies take 12% more damage.", elements=["void"],
                    damage=10.0, aps=1.1, range=170.0, effects=[fx("curse", damage_taken=0.12, duration=3.0)]),
        aura=[mod("damage", INC, 0.1)], aura_text="+10% damage",
        ability=dict(name="Oath of the Fallen", cooldown=130.0, target=BOARD, damage=20.0,
                     desc="A column of oathbound shades walks every road backwards, striking every enemy they pass."),
        ultimate=dict(name="Oath of the Fallen", cooldown=130.0, target=BOARD, damage=25.0,
                      effects=[fx("curse", damage_taken=0.15, duration=4.0)],
                      desc="The shades walk every road backwards, striking and cursing every enemy they pass."),
        ultimate_text="The shades curse what they hit",
        barks=["I see them.", "The dark is a road. I know it well.", "Told you."],
    ),
    dict(
        id="ignar", name="Ignar", title="the Cinder Warden", element="fire", joins="ember_4",
        blurb="The Warden of Fire, freed from madness: black stone with a molten heart.",
        attack=dict(desc="A cone of fire breath that sets everything burning.", elements=["fire"], damage=10.0,
                    aps=0.9, range=160.0, splash=55.0, projectile_speed=600.0,
                    effects=[fx("burn", damage_per_second=7.0, duration=4.0)]),
        aura=[mod("damage", INC, 0.1, ["fire"]), mod("burn_spread_radius", FLAT, 40.0, ["fire"])],
        aura_text="Fire towers deal 10% more damage, and their burns spread a little",
        ability=dict(name="Cataclysm", cooldown=100.0, target=CROWDS, radius=1.0, strikes=2, damage=35.0,
                     effects=[fx("burn", damage_per_second=4.0, duration=4.0)],
                     desc="The caldera opens: two meteors fall on the most crowded spots."),
        ultimate=dict(name="Cataclysm", cooldown=100.0, target=CROWDS, radius=1.0, strikes=3, damage=35.0,
                      effects=[fx("burn", damage_per_second=4.0, duration=4.0)],
                      desc="The caldera opens: three meteors fall on the most crowded spots."),
        ultimate_text="Three meteors",
        barks=["Burn, and be warm.", "I am awake. I am awake.", "Little ones, stand back."],
    ),
    dict(
        id="aurath", name="Aurath", title="of the Storms", element="storm", joins="storm_4",
        blurb="The Warden of Storm: a rider of cloud and lightning, never quite still.",
        attack=dict(desc="Lightning that leaps through three enemies.", elements=["storm"], damage=6.0, aps=0.9,
                    range=170.0, chain_count=2, chain_range=140.0, chain_falloff=0.15),
        aura=[mod("chain_count", FLAT, 1, ["storm"])], aura_text="Storm towers jump to 1 more enemy",
        ability=dict(name="Skyfall", cooldown=130.0, target=BOARD, damage=15.0,
                     desc="A season of held-back storm let go at once: lightning strikes every enemy on the board."),
        ultimate=dict(name="Skyfall", cooldown=130.0, target=BOARD, damage=15.0, strikes=2,
                      desc="Lightning strikes every enemy on the board, twice."),
        ultimate_text="Strikes twice",
        barks=["We are the wind behind you.", "Moving! Moving!", "We remember the road."],
    ),
    dict(
        id="elowen", name="Elowen", title="the Evergreen", element="nature", joins="nature_4",
        blurb="The Warden of Nature: an ancient woman of bark and blossom.",
        attack=dict(desc="Bursts of thorn that root enemies for a moment and poison them.", elements=["nature"],
                    damage=9.0, aps=0.8, range=160.0, splash=50.0, projectile_speed=520.0,
                    effects=[fx("stun", duration=0.25), fx("poison", damage_per_second=3.0, duration=4.0, max_stacks=2)]),
        aura_lives=(6, 1), aura_text="A life back after each wave if 6 towers stand near her",
        ability=dict(name="Wildgrowth", cooldown=110.0, target=SELF, radius=3.0, hold=2.0,
                     effects=[fx("poison", damage_per_second=4.0, duration=4.0)],
                     desc="Roots hold every enemy within 3 cells of her for 2 seconds and poison them."),
        ultimate=dict(name="Wildgrowth", cooldown=110.0, target=SELF, radius=3.0, hold=2.5, duration=2.5,
                      lives_per_kill=1, lives_per_kill_max=2,
                      effects=[fx("poison", damage_per_second=5.0, duration=4.0)],
                      desc="Roots hold and poison every enemy within 3 cells for 2.5 seconds; each kill meanwhile gives a life back, up to 2."),
        ultimate_text="A life back for each kill during the roots, up to 2",
        barks=["Grow.", "Rest now, little ones. Rest.", "Everything returns."],
    ),
    dict(
        id="thalassa", name="Thalassa", title="of the Deep", element="water", joins="water_4",
        blurb="The Warden of Water, who remembers everything.",
        attack=dict(desc="A jet of water that slows and pushes enemies back.", elements=["water"], damage=10.0,
                    aps=0.9, range=180.0, knockback=12.0, effects=[fx("slow", slow=0.2, duration=1.5)]),
        aura=[mod("attack_range", INC, 0.12, ["water"]), mod("attack_range", INC, 0.05)],
        aura_text="+5% range, and +12% more for water towers",
        ability=dict(name="Great Flood", cooldown=150.0, target=BOARD, knockback=3.0 * CELL,
                     desc="The tide comes in: every enemy is swept three cells back along its road. Bosses move half as far."),
        ultimate=dict(name="Great Flood", cooldown=150.0, target=BOARD, send_to_start=True,
                      desc="The tide comes in: every enemy but the bosses is swept back to the start of its road."),
        ultimate_text="Sweeps all but the bosses back to the start",
        barks=["I remember.", "Be still, and sink.", "Every one of you. Every one."],
    ),
    dict(
        id="orrok", name="Orrok", title="the Mountain", element="earth", joins="earth_4",
        blurb="The Warden of Earth: a slow stone giant who says almost nothing.",
        attack=dict(desc="Boulders with a huge splash that stun.", elements=["earth"], damage=25.0, aps=0.4,
                    range=160.0, splash=70.0, projectile_speed=420.0, effects=[fx("stun", duration=0.3)]),
        aura=[mod("damage", INC, 0.2, ["earth"])], aura_text="Earth towers deal 20% more damage",
        ability=dict(name="Worldbreaker", cooldown=110.0, target=AIMED, radius=1.0, damage=30.0, execute=0.2,
                     desc="A fissure opens where you choose. Every enemy in it under 20% health falls in."),
        ultimate=dict(name="Worldbreaker", cooldown=110.0, target=AIMED, radius=1.0, damage=40.0, execute=0.3,
                      desc="A fissure opens where you choose. Every enemy in it under 30% health falls in."),
        ultimate_text="Swallows enemies under 30% health",
        barks=["Hold.", "Stand.", "..."],
    ),
    dict(
        id="nyxara", name="Nyxara", title="of the Hollow", element="void", joins="void_4",
        blurb="The Warden of Void, keeper of the road of the dead.",
        attack=dict(desc="A soul drain that curses: cursed enemies take 15% more damage.", elements=["void"],
                    damage=11.0, aps=1.0, range=180.0, effects=[fx("curse", damage_taken=0.15, duration=3.0)]),
        aura=[mod("aura_damage", MORE, 0.4, ["void"])], aura_text="Void towers' auras are 40% stronger",
        ability=dict(name="Eclipse", cooldown=130.0, target=BOARD, duration=5.0, gold=1.5,
                     modifiers=[mod("damage", MORE, 0.2)],
                     desc="Her night, given to the living: for 5 seconds every tower deals 20% more damage and kills pay 50% more gold."),
        ultimate=dict(name="Eclipse", cooldown=130.0, target=BOARD, duration=8.0, gold=1.5,
                      modifiers=[mod("damage", MORE, 0.2)],
                      desc="For 8 seconds every tower deals 20% more damage and kills pay 50% more gold."),
        ultimate_text="Lasts 8 s",
        barks=["Walk on.", "Your road ends here.", "I see every star."],
    ),
    dict(
        id="ilyra", name="Ilyra the Unbroken", title="Daughter of the Regent", element="void", joins="converge_1",
        blurb="The Regent's lost daughter, six years in the Outer Hollow, and the reason he will be stopped.",
        attack=dict(desc="Black lightning that curses and jumps to one more enemy.", elements=["void", "storm"], damage=8.0,
                    aps=1.0, range=170.0, chain_count=1, chain_range=120.0, chain_falloff=0.15,
                    effects=[fx("curse", damage_taken=0.1, duration=3.0)]),
        aura_hero_levels=1, aura_text="Every hero in the party fights one level higher",
        ability=dict(name="Last Light", cooldown=180.0, target=BOARD, duration=4.0, ward=True,
                     desc="For 4 seconds nothing gets past the gate: whatever reaches it is thrown back to the start."),
        ultimate=dict(name="Last Light", cooldown=180.0, target=BOARD, duration=6.0, ward=True, heal=2,
                      desc="For 6 seconds whatever reaches the gate is thrown back to the start, and 2 lives come back."),
        ultimate_text="Lasts 6 s and heals 2 lives",
        barks=["I know this dark. It doesn't know me any more.", "Three heartbeats. Now.", "One of them wept. The other never did."],
    ),
    dict(
        id="seraphel", name="Seraphel the Dawnblade", title="Knight of the Sunstone", element="", joins="converge_2",
        blurb="The last knight of the Sunstone, who has one fight left in her.",
        attack=dict(desc="A prismatic sword wave that always strikes the element each enemy is weakest to.",
                    tags=["prismatic"], damage=8.0, aps=1.0, range=170.0, splash=35.0, projectile_speed=800.0),
        aura=[mod("damage", INC, 0.08), mod("attacks_per_second", INC, 0.08)], aura_text="+8% damage and attack speed",
        ability=dict(name="Dawnbreak", cooldown=110.0, target=BOARD, damage=25.0, weakness=True,
                     desc="A beam of the Sunstone's light down every road, in each enemy's weakest element."),
        ultimate=dict(name="Dawnbreak", cooldown=110.0, target=BOARD, damage=25.0, weakness=True, resets_skills=True,
                      desc="A beam down every road in each enemy's weakest element, and every skill is ready again."),
        ultimate_text="Every skill is ready again",
        barks=["Stand in the light.", "I have seen worse. Not much worse.", "For the Sunstone. For the dawn."],
    ),
    dict(
        id="oswin", name="Oswin the White Lantern", title="Master of the Order of the Spire", element="", joins="",
        arrives=("converge_3", 17),
        blurb="The Grey Lantern, back from the road of the dead with the light of every fallen city.",
        attack=dict(desc="White flame that runs through three enemies, in each one's weakest element.",
                    tags=["prismatic"], damage=14.0, aps=0.9, range=200.0, chain_count=2, chain_range=130.0),
        aura=[mod("damage", INC, 0.12), mod("attack_range", INC, 0.05)], aura_text="+12% damage and +5% range",
        ability=dict(name="White Flame", cooldown=140.0, target=SELF, radius=3.0, damage=60.0, boss_mult=3.0, execute=0.25,
                     desc="Every enemy within 3 cells under a quarter of its health burns away. Bosses take a heavy blow."),
        ultimate=dict(name="White Flame", cooldown=140.0, target=SELF, radius=3.0, damage=60.0, boss_mult=3.0,
                      execute=0.25, resets_heroes=True,
                      desc="Burns away every weakened enemy within 3 cells, hits bosses hard, and every hero's ability is ready again."),
        ultimate_text="Every other hero's ability is ready again",
        barks=["Light's on. Let's go.", "Every light you lost, I kept.", "A long way round. Worth it."],
    ),
]


def gd_string(text):
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def gd_float(value):
    return repr(float(value))


class Writer:
    def __init__(self):
        self.subs = []
        self.count = 0

    def sub(self, script, fields):
        self.count += 1
        sid = "S%d" % self.count
        lines = ['[sub_resource type="Resource" id="%s"]' % sid, 'script = ExtResource("%s")' % script]
        lines += ["%s = %s" % (k, v) for k, v in fields]
        self.subs.append("\n".join(lines))
        return 'SubResource("%s")' % sid

    def modifier(self, m):
        fields = [("stat", '&"%s"' % m["stat"])]
        if m["kind"]:
            fields.append(("kind", str(m["kind"])))
        fields.append(("value", gd_float(m["value"])))
        if m["tags"]:
            fields.append(("required_tags", "Array[StringName]([%s])" % ", ".join('&"%s"' % t for t in m["tags"])))
        return self.sub("mod", fields)

    def modifiers(self, items):
        return 'Array[ExtResource("mod")]([%s])' % ", ".join(self.modifier(m) for m in items)

    def effect(self, e):
        fields = [("kind", '&"%s"' % e["kind"])]
        for key in ("damage_per_second", "slow", "damage_taken", "armour_reduction", "duration"):
            if key in e:
                fields.append((key, gd_float(e[key])))
        if "max_stacks" in e:
            fields.append(("max_stacks", str(e["max_stacks"])))
        return self.sub("status", fields)

    def effects(self, items):
        return 'Array[ExtResource("status")]([%s])' % ", ".join(self.effect(e) for e in items)

    def attack(self, hero):
        a = hero["attack"]
        fields = [("id", '&"%s"' % hero["id"]), ("display_name", gd_string(hero["name"])),
                  ("description", gd_string(a["desc"]))]
        fields.append(("elements", "Array[StringName]([%s])" % ", ".join('&"%s"' % e for e in a.get("elements", []))))
        fields.append(("tags", "Array[StringName]([%s])" % ", ".join('&"%s"' % t for t in ["hero"] + a.get("tags", []))))
        fields.append(("cost", "1"))
        fields.append(("damage", gd_float(a["damage"])))
        fields.append(("attacks_per_second", gd_float(a["aps"])))
        fields.append(("attack_range", gd_float(a["range"])))
        for key, name in (("projectile_speed", "projectile_speed"), ("splash", "splash_radius"),
                          ("chain_range", "chain_range"), ("chain_falloff", "chain_falloff"), ("knockback", "knockback")):
            if key in a:
                fields.append((name, gd_float(a[key])))
        if "chain_count" in a:
            fields.append(("chain_count", str(a["chain_count"])))
        if "poison_spread" in a:
            fields.append(("poison_spread_count", str(a["poison_spread"])))
        if a.get("effects"):
            fields.append(("status_effects", self.effects(a["effects"])))
        return self.sub("tower", fields)

    def ability(self, ab):
        fields = [("display_name", gd_string(ab["name"])), ("description", gd_string(ab["desc"])),
                  ("cooldown", gd_float(ab["cooldown"])), ("target", str(ab["target"]))]
        optional = [("radius", "radius_cells", gd_float), ("strikes", "strikes", str), ("damage", "damage", gd_float),
                    ("boss_mult", "boss_damage_multiplier", gd_float), ("execute", "execute_below", gd_float),
                    ("hold", "hold_seconds", gd_float), ("knockback", "knockback", gd_float),
                    ("burst", "burst_damage", gd_float), ("duration", "duration", gd_float),
                    ("gold", "gold_multiplier", gd_float), ("lives_per_kill", "lives_per_kill", str),
                    ("lives_per_kill_max", "lives_per_kill_max", str), ("heal", "heal_lives", str)]
        for key, name, conv in optional:
            if key in ab:
                fields.append((name, conv(ab[key])))
        for key, name in (("weakness", "hits_weakness"), ("send_to_start", "send_to_start"),
                          ("send_bosses", "send_bosses"), ("ward", "ward"), ("resets_skills", "resets_skills"),
                          ("resets_heroes", "resets_heroes")):
            if ab.get(key):
                fields.append((name, "true"))
        if ab.get("effects"):
            fields.append(("status_effects", self.effects(ab["effects"])))
        if ab.get("modifiers"):
            fields.append(("modifiers", self.modifiers(ab["modifiers"])))
        return self.sub("ability", fields)


def write_hero(order, hero):
    w = Writer()
    attack = w.attack(hero)
    ability = w.ability(hero["ability"])
    ultimate = w.ability(hero["ultimate"])
    fields = [("id", '&"%s"' % hero["id"]), ("display_name", gd_string(hero["name"])),
              ("title", gd_string(hero["title"])), ("blurb", gd_string(hero["blurb"])), ("order", str(order))]
    if hero["element"]:
        fields.append(("element", '&"%s"' % hero["element"]))
    if hero["joins"]:
        fields.append(("joins_after", '&"%s"' % hero["joins"]))
    if "arrives" in hero:
        fields.append(("arrives_in", '&"%s"' % hero["arrives"][0]))
        fields.append(("arrives_at_wave", str(hero["arrives"][1])))
    fields.append(("attack", attack))
    if hero.get("aura"):
        fields.append(("aura", w.modifiers(hero["aura"])))
    fields.append(("aura_text", gd_string(hero["aura_text"])))
    if hero.get("aura_hero_levels"):
        fields.append(("aura_hero_levels", str(hero["aura_hero_levels"])))
    if hero.get("aura_lives"):
        fields.append(("aura_lives_per_towers", str(hero["aura_lives"][0])))
        fields.append(("aura_lives_max", str(hero["aura_lives"][1])))
    fields.append(("ability", ability))
    fields.append(("ultimate", ultimate))
    if hero.get("ultimate_modifiers"):
        fields.append(("ultimate_modifiers", w.modifiers(hero["ultimate_modifiers"])))
    fields.append(("ultimate_text", gd_string(hero["ultimate_text"])))
    fields.append(("barks", "PackedStringArray(%s)" % ", ".join(gd_string(b) for b in hero["barks"])))
    head = [
        '[gd_resource type="Resource" script_class="HeroData" load_steps=%d format=3]' % (len(w.subs) + 6),
        "",
        '[ext_resource type="Script" path="res://scripts/data/hero_data.gd" id="hero"]',
        '[ext_resource type="Script" path="res://scripts/data/hero_ability.gd" id="ability"]',
        '[ext_resource type="Script" path="res://scripts/data/tower_data.gd" id="tower"]',
        '[ext_resource type="Script" path="res://scripts/data/status_effect_data.gd" id="status"]',
        '[ext_resource type="Script" path="res://scripts/data/modifier.gd" id="mod"]',
        "",
    ]
    body = "\n\n".join(w.subs)
    main = "[resource]\nscript = ExtResource(\"hero\")\n" + "\n".join("%s = %s" % f for f in fields)
    text = "\n".join(head) + body + "\n\n" + main + "\n"
    (OUT / ("%s.tres" % hero["id"])).write_text(text)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for order, hero in enumerate(HEROES):
        write_hero(order, hero)
    print("Wrote %d heroes to %s" % (len(HEROES), OUT))


if __name__ == "__main__":
    main()
