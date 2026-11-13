#!/usr/bin/env python3
"""Writes the 20 triple-element towers to data/towers/triple_*.tres.

Every set of three elements has one tower, as in Element TD. A triple has a node of its own in the
in-game skill tree (tools/web/gen_skill_web.py), which needs level III of each of its three elements,
and a dual hybrid can turn into it in place.
Edit the TRIPLES table and rerun; do not edit the .tres files by hand.

Run from the repository root:  python3 tools/towers/gen_triples.py
Then  python3 tools/art/gen_game_art.py  (the art is built from each tower's elements).
"""
from __future__ import annotations

import os

RING = ["fire", "storm", "nature", "water", "earth", "void"]
FLAT, INC, MORE = 0, 1, 2

# Status effects, by short name: kind and its numbers.
def burn(dps, stacks=4, duration=3.0):
    return dict(kind="burn", damage_per_second=float(dps), duration=duration, max_stacks=stacks)


def poison(dps, stacks=5, duration=4.0):
    return dict(kind="poison", damage_per_second=float(dps), duration=duration, max_stacks=stacks)


def slow(amount, duration=2.0):
    return dict(kind="slow", slow=amount, duration=duration)


def stun(duration=0.3):
    return dict(kind="stun", duration=duration)


def curse(amount=0.2, duration=3.0):
    return dict(kind="curse", damage_taken=amount, duration=duration)


def shatter(armour, stacks=5, duration=5.0):
    return dict(kind="shatter", armour_reduction=float(armour), duration=duration, max_stacks=stacks)


def chain(count, falloff=0.1, reach=135.0):
    return dict(chain_count=count, chain_range=reach, chain_falloff=falloff)


def splash(radius, speed=420.0):
    return dict(splash_radius=float(radius), projectile_speed=speed)


def aura(radius=150.0, damage=0.2):
    return dict(aura_radius=radius, aura_damage=damage)


# id, name, elements, description, cost, stats, effects, two ascendancies (id, name, description, modifiers).
TRIPLES = [
    # Three neighbours on the ring.
    ("cinderstorm", "Cinderstorm", "fire storm nature",
     "A burning thundercloud: its bolts chain through the wave, setting it alight and seeding it with poison.",
     300, dict(damage=20.0, attacks_per_second=1.3, attack_range=190.0, **chain(4, 0.15, 140.0)),
     [burn(7), poison(6)],
     [("firefront", "Firefront", "Burn and poison deal 70% more damage.", [("burn_damage", MORE, 0.7), ("poison_damage", MORE, 0.7)]),
      ("stormcrown", "Stormcrown", "Chains to 3 more enemies and attacks 25% faster.", [("chain_count", FLAT, 3), ("attacks_per_second", INC, 0.25)])]),
    ("rainwild", "Rainwild", "storm nature water",
     "A living storm over the jungle: chilling rain, lightning and venom in every bolt.",
     300, dict(damage=16.0, attacks_per_second=1.5, attack_range=185.0, bounty_bonus=1, **chain(4, 0.15, 130.0)),
     [poison(7), slow(0.3)],
     [("deluge", "Deluge", "Slows are 50% stronger and last 50% longer.", [("slow_strength", INC, 0.5), ("slow_duration", INC, 0.5)]),
      ("canopy_king", "Canopy King", "Poison deals double damage and kills earn 2 more gold.", [("poison_damage", MORE, 1.0), ("bounty_bonus", FLAT, 2)])]),
    ("mire_colossus", "Mire Colossus", "nature water earth",
     "A walking swamp of stone and root: crushing splashes that poison, slow and crack armour.",
     300, dict(damage=30.0, attacks_per_second=0.6, attack_range=165.0, **splash(80, 400.0)),
     [poison(8), slow(0.4, 2.5), shatter(2, 4)],
     [("sinking_earth", "Sinking Earth", "Splashes 40% wider and slows are 30% stronger.", [("splash_radius", INC, 0.4), ("slow_strength", INC, 0.3)]),
      ("ancient_rot", "Ancient Rot", "Poison deals double damage and shatter is twice as strong.", [("poison_damage", MORE, 1.0), ("shatter_strength", INC, 1.0)])]),
    ("abyssal_trench", "Abyssal Trench", "water earth void",
     "Opens the deep under their feet: the whole group is dragged back, stunned and cursed.",
     300, dict(damage=34.0, attacks_per_second=0.5, attack_range=170.0, knockback=30.0, **splash(70, 380.0)),
     [slow(0.35), stun(0.35), curse(0.2)],
     [("undertow_king", "Undertow King", "Drags enemies back 24 further and the collapse is 30% wider.", [("knockback", FLAT, 24), ("splash_radius", INC, 0.3)]),
      ("crushing_depth", "Crushing Depth", "Deals double damage and curses are 50% stronger.", [("damage", MORE, 1.0), ("curse_strength", INC, 0.5)])]),
    ("hellforge", "Hellforge", "earth void fire",
     "A cursed furnace hurling slag: it burns, melts armour and marks its victims for death.",
     300, dict(damage=40.0, attacks_per_second=0.5, attack_range=165.0, **splash(75, 380.0)),
     [burn(10), shatter(1.5), curse(0.2)],
     [("slag_rain", "Slag Rain", "Splashes 50% wider and burn deals 60% more damage.", [("splash_radius", INC, 0.5), ("burn_damage", MORE, 0.6)]),
      ("soul_anvil", "Soul Anvil", "Deals double damage and curses are 60% stronger.", [("damage", MORE, 1.0), ("curse_strength", INC, 0.6)])]),
    ("starfall", "Starfall", "void fire storm",
     "Pulls burning stars from the void: cursed chains of fire, and an aura that empowers every tower nearby.",
     300, dict(damage=18.0, attacks_per_second=1.2, attack_range=190.0, **chain(3, 0.15, 140.0), **aura()),
     [burn(8), curse(0.2)],
     [("constellation", "Constellation", "The aura reaches 40% further and grants 10% more increased damage.", [("aura_radius", INC, 0.4), ("aura_damage", FLAT, 0.1)]),
      ("supernova", "Supernova", "Chains to 3 more enemies and burn deals double damage.", [("chain_count", FLAT, 3), ("burn_damage", MORE, 1.0)])]),
    # Every other element: the two triangles.
    ("worldforge", "Worldforge", "fire nature earth",
     "The living mountain: eruptions of magma and thorn that burn, poison and shatter.",
     320, dict(damage=36.0, attacks_per_second=0.55, attack_range=170.0, bounty_bonus=1, **splash(85, 400.0)),
     [burn(9), poison(8), shatter(1.5)],
     [("eruption", "Eruption", "Splashes 50% wider and burn leaps to enemies within 90 when its victim dies.", [("splash_radius", INC, 0.5), ("burn_spread_radius", FLAT, 90)]),
      ("heartwood", "Heartwood", "Burn and poison deal 80% more damage and kills earn 2 more gold.", [("burn_damage", MORE, 0.8), ("poison_damage", MORE, 0.8), ("bounty_bonus", FLAT, 2)])]),
    ("storm_eye", "Eye of the Storm", "storm water void",
     "A calm and terrible eye: long chains that slow and curse, pushing the wave back.",
     320, dict(damage=14.0, attacks_per_second=1.4, attack_range=195.0, knockback=8.0, **chain(5, 0.1, 140.0)),
     [slow(0.3), curse(0.2)],
     [("cyclone", "Cyclone", "Chains to 3 more enemies and pushes them back 8 further.", [("chain_count", FLAT, 3), ("knockback", FLAT, 8)]),
      ("dead_calm", "Dead Calm", "Slows are 50% stronger and curses 60% stronger.", [("slow_strength", INC, 0.5), ("curse_strength", INC, 0.6)])]),
    # An opposite pair plus one more element: the costliest and strongest.
    ("thunder_geyser", "Thunder Geyser", "fire storm water",
     "Superheated steam charged with lightning: scalding chains that slow everything they touch.",
     340, dict(damage=22.0, attacks_per_second=1.1, attack_range=185.0, **chain(4)),
     [burn(9), slow(0.35)],
     [("pressure_cooker", "Pressure Cooker", "Deals 70% more damage and burn stacks 3 more times.", [("damage", MORE, 0.7), ("burn_stacks", FLAT, 3)]),
      ("live_wire", "Live Wire", "Chains to 3 more enemies and attacks 30% faster.", [("chain_count", FLAT, 3), ("attacks_per_second", INC, 0.3)])]),
    ("boiling_marsh", "Boiling Marsh", "fire nature water",
     "A cauldron of swamp gas: wide scalding splashes that burn, poison and slow.",
     340, dict(damage=24.0, attacks_per_second=0.7, attack_range=160.0, **splash(95, 450.0)),
     [burn(8), poison(8), slow(0.35)],
     [("fever_swamp", "Fever Swamp", "Burn and poison deal 80% more damage.", [("burn_damage", MORE, 0.8), ("poison_damage", MORE, 0.8)]),
      ("tar_cauldron", "Tar Cauldron", "Splashes 40% wider and slows are 40% stronger.", [("splash_radius", INC, 0.4), ("slow_strength", INC, 0.4)])]),
    ("obsidian_geyser", "Obsidian Geyser", "fire water earth",
     "Erupts in shards of volcanic glass: burns, slows, stuns and tears armour apart.",
     340, dict(damage=42.0, attacks_per_second=0.5, attack_range=165.0, **splash(80)),
     [burn(9), slow(0.35), shatter(2), stun(0.3)],
     [("glass_storm", "Glass Storm", "Splashes 50% wider and shatter is twice as strong.", [("splash_radius", INC, 0.5), ("shatter_strength", INC, 1.0)]),
      ("caldera_heart", "Caldera Heart", "Deals double damage and stuns last 60% longer.", [("damage", MORE, 1.0), ("stun_duration", INC, 0.6)])]),
    ("mistwraith", "Mistwraith", "fire water void",
     "A haunted fog bank: it scalds and curses all inside it, and veils nearby towers in power.",
     340, dict(damage=20.0, attacks_per_second=0.8, attack_range=165.0, **splash(90, 500.0), **aura()),
     [burn(8), slow(0.3), curse(0.25)],
     [("shroud", "Shroud", "The aura reaches 40% further and grants 10% more increased damage.", [("aura_radius", INC, 0.4), ("aura_damage", FLAT, 0.1)]),
      ("banshee", "Banshee", "Curses are 80% stronger and burn deals 60% more damage.", [("curse_strength", INC, 0.8), ("burn_damage", MORE, 0.6)])]),
    ("thunderforge", "Thunderforge", "fire storm earth",
     "A hammer of lightning on a molten anvil: heavy chains that burn, stun and shatter.",
     340, dict(damage=34.0, attacks_per_second=0.8, attack_range=185.0, **chain(4)),
     [burn(8), stun(0.3), shatter(1.5)],
     [("anvil_of_storms", "Anvil of Storms", "Deals double damage but chains to 1 fewer enemy.", [("damage", MORE, 1.0), ("chain_count", FLAT, -1)]),
      ("forge_lightning", "Forge Lightning", "Chains to 3 more enemies and loses no damage as it jumps.", [("chain_count", FLAT, 3), ("chain_falloff", MORE, -1.0)])]),
    ("amber_spire", "Amber Spire", "storm nature earth",
     "Lightning trapped in ancient amber: chains that poison and stun, and pay out in gold.",
     340, dict(damage=26.0, attacks_per_second=0.9, attack_range=185.0, bounty_bonus=2, **chain(4)),
     [poison(8), stun(0.3), shatter(1, 4)],
     [("golden_age", "Golden Age", "Kills earn 3 more gold and range is 20% longer.", [("bounty_bonus", FLAT, 3), ("attack_range", INC, 0.2)]),
      ("fossil_venom", "Fossil Venom", "Poison deals double damage and spreads to 3 enemies on death.", [("poison_damage", MORE, 1.0), ("poison_spread_count", FLAT, 3)])]),
    ("tidal_dynamo", "Tidal Dynamo", "storm water earth",
     "A tide-driven engine: surging chains that slow, stun and hurl enemies back.",
     340, dict(damage=24.0, attacks_per_second=1.0, attack_range=185.0, knockback=14.0, **chain(4)),
     [slow(0.35), stun(0.3), shatter(1, 4)],
     [("spring_tide", "Spring Tide", "Pushes enemies back 14 further and slows are 40% stronger.", [("knockback", FLAT, 14), ("slow_strength", INC, 0.4)]),
      ("overload", "Overload", "Deals 80% more damage and chains to 2 more enemies.", [("damage", MORE, 0.8), ("chain_count", FLAT, 2)])]),
    ("polar_rift", "Polar Rift", "storm earth void",
     "A magnetic tear in the sky: cursed, stunning chains and a field that charges nearby towers.",
     340, dict(damage=24.0, attacks_per_second=0.9, attack_range=190.0, **chain(4), **aura()),
     [stun(0.3), curse(0.2), shatter(1, 4)],
     [("aurora", "Aurora", "The aura reaches 40% further and grants 10% more increased damage.", [("aura_radius", INC, 0.4), ("aura_damage", FLAT, 0.1)]),
      ("null_field", "Null Field", "Curses are 60% stronger and stuns last 60% longer.", [("curse_strength", INC, 0.6), ("stun_duration", INC, 0.6)])]),
    ("witchfire", "Witchfire Tree", "fire nature void",
     "A burning, cursed tree: its fire and venom leap from every corpse.",
     340, dict(damage=14.0, attacks_per_second=1.2, attack_range=175.0, projectile_speed=650.0, poison_spread_count=3),
     [burn(9, 5), poison(9, 6), curse(0.25)],
     [("funeral_pyre", "Funeral Pyre", "Burn deals 60% more damage and leaps to enemies within 100 when its victim dies.", [("burn_damage", MORE, 0.6), ("burn_spread_radius", FLAT, 100)]),
      ("hexbloom", "Hexbloom", "Curses are 80% stronger and poison deals 80% more damage.", [("curse_strength", INC, 0.8), ("poison_damage", MORE, 0.8)])]),
    ("plague_storm", "Plague Storm", "storm nature void",
     "A cursed stormfront raining pestilence: chains of poison that spread from the dead.",
     340, dict(damage=12.0, attacks_per_second=1.4, attack_range=185.0, poison_spread_count=3, **chain(4, 0.15)),
     [poison(9, 6, 5.0), curse(0.2)],
     [("pandemic", "Pandemic", "Poison deals 60% more damage and spreads to 4 more enemies on death.", [("poison_damage", MORE, 0.6), ("poison_spread_count", FLAT, 4)]),
      ("black_lightning", "Black Lightning", "Chains to 3 more enemies and curses are 60% stronger.", [("chain_count", FLAT, 3), ("curse_strength", INC, 0.6)])]),
    ("drowned_garden", "Drowned Garden", "nature water void",
     "A sunken, haunted garden: splashes of black water that poison, slow and curse.",
     340, dict(damage=18.0, attacks_per_second=0.75, attack_range=165.0, knockback=10.0, **splash(85)),
     [poison(9, 6), slow(0.35, 2.5), curse(0.25)],
     [("kelp_forest", "Kelp Forest", "Slows are 50% stronger and hits drag enemies back 14 further.", [("slow_strength", INC, 0.5), ("knockback", FLAT, 14)]),
      ("siren_bloom", "Siren Bloom", "Poison deals double damage and curses are 50% stronger.", [("poison_damage", MORE, 1.0), ("curse_strength", INC, 0.5)])]),
    ("tombroot", "Tombroot", "nature earth void",
     "Roots through a graveyard: heavy cursed thorns that shatter armour and feed on the dead.",
     340, dict(damage=46.0, attacks_per_second=0.7, attack_range=175.0, projectile_speed=700.0, bounty_bonus=2, poison_spread_count=2),
     [poison(10), shatter(2), curse(0.25)],
     [("grave_harvest", "Grave Harvest", "Kills earn 3 more gold and poison spreads to 3 more enemies on death.", [("bounty_bonus", FLAT, 3), ("poison_spread_count", FLAT, 3)]),
      ("bone_spear", "Bone Spear", "Deals double damage and shatter is twice as strong.", [("damage", MORE, 1.0), ("shatter_strength", INC, 1.0)])]),
]

AREA_STATS = ("splash_radius",)
# Property order inside the .tres file, as Godot's inspector would save it.
STAT_ORDER = ["cost", "damage", "attacks_per_second", "attack_range", "projectile_speed", "splash_radius", "chain_count",
              "chain_range", "chain_falloff", "knockback", "bounty_bonus", "poison_spread_count", "aura_radius", "aura_damage"]


def fmt(value) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        return repr(value)
    raise TypeError(value)


def names(ids) -> str:
    return "Array[StringName]([%s])" % ", ".join('&"%s"' % i for i in ids)


def write_tower(short_id, name, elements, description, cost, stats, effects, ascendancies) -> str:
    tower_id = "triple_" + short_id
    out = ['[gd_resource type="Resource" script_class="TowerData" format=3]', "",
           '[ext_resource type="Script" path="res://scripts/data/tower_data.gd" id="1_tower"]',
           '[ext_resource type="Script" path="res://scripts/data/status_effect_data.gd" id="2_status"]',
           '[ext_resource type="Script" path="res://scripts/data/ascendancy_data.gd" id="3_asc"]',
           '[ext_resource type="Script" path="res://scripts/data/modifier.gd" id="4_mod"]', ""]
    for i, effect in enumerate(effects):
        out += ['[sub_resource type="Resource" id="Effect_%d"]' % i, 'script = ExtResource("2_status")', 'kind = &"%s"' % effect["kind"]]
        out += ["%s = %s" % (key, fmt(value)) for key, value in effect.items() if key != "kind"]
        out.append("")
    asc_ids = []
    for asc_id, asc_name, asc_description, modifiers in ascendancies:
        mod_ids = []
        for j, (stat, kind, value) in enumerate(modifiers):
            mod_id = "Asc_%s_m%d" % (asc_id, j)
            mod_ids.append(mod_id)
            out += ['[sub_resource type="Resource" id="%s"]' % mod_id, 'script = ExtResource("4_mod")', 'stat = &"%s"' % stat]
            if kind:
                out.append("kind = %d" % kind)
            out += ["value = %s" % fmt(float(value)), ""]
        asc_ids.append("Asc_" + asc_id)
        out += ['[sub_resource type="Resource" id="Asc_%s"]' % asc_id, 'script = ExtResource("3_asc")', 'id = &"%s"' % asc_id,
                'display_name = "%s"' % asc_name, 'description = "%s"' % asc_description,
                'modifiers = Array[ExtResource("4_mod")]([%s])' % ", ".join('SubResource("%s")' % m for m in mod_ids), ""]
    stats = dict(stats, cost=cost)
    out += ["[resource]", 'script = ExtResource("1_tower")', 'id = &"%s"' % tower_id, 'display_name = "%s"' % name,
            'description = "%s"' % description, "elements = %s" % names(elements)]
    if any(stats.get(key, 0) for key in AREA_STATS):
        out.append("tags = %s" % names(["area"]))
    assert set(stats) <= set(STAT_ORDER), set(stats) - set(STAT_ORDER)
    out += ["%s = %s" % (key, fmt(stats[key])) for key in STAT_ORDER if key in stats]
    out.append('status_effects = Array[ExtResource("2_status")]([%s])' % ", ".join('SubResource("Effect_%d")' % i for i in range(len(effects))))
    out.append('ascendancies = Array[ExtResource("3_asc")]([%s])' % ", ".join('SubResource("%s")' % a for a in asc_ids))
    with open(os.path.join("data", "towers", tower_id + ".tres"), "w") as fh:
        fh.write("\n".join(out) + "\n")
    return tower_id


def main() -> None:
    seen = set()
    for short_id, name, elements, description, cost, stats, effects, ascendancies in TRIPLES:
        elements = elements.split()
        key = frozenset(elements)
        assert len(key) == 3 and key <= set(RING), elements
        assert key not in seen, "two towers for %s" % sorted(key)
        assert len(ascendancies) == 2
        seen.add(key)
        write_tower(short_id, name, elements, description, cost, stats, effects, ascendancies)
    assert len(seen) == 20, "expected one tower for each of the 20 element triples, got %d" % len(seen)
    print("Wrote %d triple towers" % len(seen))


if __name__ == "__main__":
    main()
