#!/usr/bin/env python3
"""Writes data/allies/*.tres: the units the player musters in the counter-attack of the final assault.

Twenty troops of the Concord (the six peoples and Solenne's own) and the sixteen heroes as champions.
Health and damage are for wave 1; the game grows them with the wave when a unit is mustered (see
RunSim.muster_growth), so these numbers set how units compare with each other and with the horde.

Usage: python3 tools/allies/gen_allies.py
"""
import os
import re

ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(ROOT, "data", "allies")

MELEE, RANGED, SIEGE, HEALER, SUPPORT, CHAMPION = range(6)

# id: (name, title, role, element, cost, cooldown, count, stats, description)
# stats keys: hp armour speed dmg every reach splash chain siege boss siege_only slow slow_s dot dot_dps dot_s
#             heal heal_r heal_s aura aura_r flying blocks max
TROOPS = [
    ("footman", "Solenne Footmen", "Shield wall", MELEE, "", 60, 3.0, 3,
     dict(hp=70, armour=2, speed=55, dmg=9, every=1.0, reach=36),
     "Red plate, steel and a heater shield. Three of them hold a road against twice their number."),
    ("pikeman", "Lantern Pikemen", "Long pikes", MELEE, "", 80, 4.0, 3,
     dict(hp=60, armour=1, speed=52, dmg=11, every=1.1, reach=54, boss=2.0),
     "The Lanternguard's pike line. Their long reach strikes first, and they brace against the big ones."),
    ("crossbowman", "Wallguard Crossbows", "Bolts from behind", RANGED, "", 75, 4.0, 3,
     dict(hp=35, speed=55, dmg=12, every=1.4, reach=190, blocks=False),
     "Solenne's wall archers, marching for once. They shoot over the shield wall and do not hold the road."),
    ("warhound", "Emberfolk Warhounds", "Fast pack", MELEE, "", 70, 4.0, 4,
     dict(hp=35, speed=120, dmg=7, every=0.7, reach=30),
     "Forge-bred hounds with iron collars. Fast and cheap: they reach the horde first and tie it up."),
    ("ember_knight", "Emberfolk Forge-Knights", "Burning blades", MELEE, "fire", 150, 8.0, 2,
     dict(hp=220, armour=6, speed=48, dmg=18, every=1.2, reach=38, dot="burn", dot_dps=6, dot_s=3),
     "Kindlers in blackened plate. Their swords keep the heat of their bodies and set the horde alight."),
    ("gale_lancer", "Galeborn Sky-Lancers", "Storm cavalry", MELEE, "storm", 140, 7.0, 2,
     dict(hp=130, armour=3, speed=110, dmg=26, every=1.5, reach=44),
     "Riders of the Steppe. They hit like thunder and get where they are going before anyone else."),
    ("root_archer", "Deepwood Archers", "Poison arrows", RANGED, "nature", 110, 6.0, 3,
     dict(hp=40, speed=58, dmg=10, every=1.0, reach=230, dot="poison", dot_dps=5, dot_s=4, blocks=False),
     "Archers of the Deepwood. Their arrows are cut from thorn and keep working after they land."),
    ("tide_priestess", "Tidefolk Ice-Seers", "Healing tide", HEALER, "water", 120, 10.0, 1,
     dict(hp=60, speed=52, dmg=5, every=1.2, reach=150, heal=0.08, heal_r=140, heal_s=2.0, blocks=False),
     "Tidefolk seers of Frostmere. They give away a memory with every wound they close."),
    ("ironbreaker", "Stoneborn Shieldbreakers", "Wall breakers", SIEGE, "earth", 170, 9.0, 2,
     dict(hp=260, armour=10, speed=40, dmg=20, every=1.4, reach=38, siege=2.5),
     "Stoneborn of the Canyon with rune-cut hammers. Slow, very hard to kill, and terrible to walls."),
    ("veil_blade", "Veilwalker Shades", "Shadow duellists", MELEE, "void", 130, 7.0, 2,
     dict(hp=70, speed=80, dmg=30, every=0.9, reach=36, boss=1.5, blocks=False),
     "Veilwalker duellists who step between shadows. They do not hold a road; they cut through it."),
    ("firebrand", "Emberfolk Firebrands", "Fire volleys", RANGED, "fire", 140, 8.0, 2,
     dict(hp=40, speed=52, dmg=14, every=1.6, reach=170, splash=60, blocks=False),
     "Battle-kindlers who throw fire in arcs. Every volley costs them a little of their own warmth."),
    ("stormcaller", "Galeborn Stormcallers", "Chain lightning", RANGED, "storm", 150, 8.0, 2,
     dict(hp=40, speed=52, dmg=13, every=1.4, reach=180, chain=3, blocks=False),
     "They sing the lightning down and send it leaping from one of the horde to the next."),
    ("pearl_marine", "Pearlhaven Harpooners", "Harpoons", MELEE, "water", 100, 5.0, 3,
     dict(hp=80, armour=3, speed=54, dmg=10, every=1.0, reach=60, slow=0.35, slow_s=1.5),
     "Sailors of the Pearl Fleet with harpoons and nets. What they hook, they slow."),
    ("hollow_hunter", "Veilwalker Hollow-Hunters", "Boss killers", RANGED, "void", 160, 9.0, 2,
     dict(hp=45, speed=56, dmg=30, every=2.0, reach=240, boss=3.0, blocks=False),
     "Veilwalkers who have walked the Outer Hollow and learned where the big things are soft."),
    ("lantern_cleric", "Order Lantern-Bearers", "Light and mending", HEALER, "", 140, 12.0, 1,
     dict(hp=80, armour=2, speed=50, dmg=6, every=1.0, reach=40, heal=0.05, heal_r=180, heal_s=1.5),
     "Brothers and sisters of the Order of the Spire with white lanterns. The light heals whoever stands in it."),
    ("banner_bearer", "Banner of Solenne", "Battle standard", SUPPORT, "", 120, 15.0, 1,
     dict(hp=120, armour=4, speed=50, dmg=6, every=1.0, reach=36, aura=0.25, aura_r=150, max=3),
     "The Queen's standard. Every unit near it fights a quarter harder. At most three on the field."),
    ("griffin_rider", "Highwind Hawk-Riders", "From the sky", MELEE, "storm", 200, 10.0, 2,
     dict(hp=120, armour=2, speed=120, dmg=22, every=1.0, reach=60, siege=1.5, flying=True, blocks=False),
     "Galeborn riders on the great storm-hawks of the high Steppe. They fly over the horde and strike the citadel's walls."),
    ("spire_golem", "Spirewright Golem", "Living rampart", MELEE, "earth", 240, 14.0, 1,
     dict(hp=600, armour=14, speed=30, dmg=30, every=1.8, reach=44, splash=40, siege=1.5),
     "Chiselled stone bound by the Order's Spirecraft. It walks into the horde and does not stop."),
    ("battering_ram", "Spirewright Ram", "Gate breaker", SIEGE, "", 220, 14.0, 1,
     dict(hp=420, armour=12, speed=34, dmg=70, every=2.5, reach=40, siege=4.0, siege_only=True, blocks=False),
     "The Order's iron-headed ram under a roof of hides. It ignores the horde and only stops at the citadel."),
    ("sunstone_catapult", "Spirewright Sunstone Catapult", "Long-range siege", SIEGE, "", 260, 16.0, 1,
     dict(hp=150, armour=4, speed=30, dmg=40, every=3.0, reach=320, splash=70, siege=2.5, blocks=False),
     "Throws shards of the broken Sunstone. It outranges the citadel's spires."),
]

# The heroes march as champions. hero id: (role, element, stats, line)
CHAMPIONS = {
    "tamsin": (CHAMPION, dict(hp=480, armour=8, speed=58, dmg=30, every=0.9, reach=44, aura=0.15, aura_r=140),
               "Captain of the Lanternguard. Her company fights harder near her."),
    "brannoc": (CHAMPION, dict(hp=560, armour=10, speed=50, dmg=44, every=1.3, reach=44, splash=50, siege=2.5),
                "The Smith-Lord's hammer was made for gates."),
    "kaela": (CHAMPION, dict(hp=460, armour=6, speed=120, dmg=40, every=1.1, reach=48),
              "The Marshal of the Steppe rides ahead of everyone."),
    "sylvaine": (CHAMPION, dict(hp=360, armour=4, speed=60, dmg=34, every=0.8, reach=260, dot="poison", dot_dps=12, dot_s=4, blocks=False),
                 "Her arrows never miss and never stop hurting."),
    "mirelle": (CHAMPION, dict(hp=380, armour=4, speed=55, dmg=20, every=1.0, reach=200, slow=0.4, slow_s=2, heal=0.06, heal_r=180, heal_s=2, blocks=False),
                "The Tide-Seer slows the horde and mends the line."),
    "gorrim": (CHAMPION, dict(hp=900, armour=18, speed=42, dmg=26, every=1.2, reach=40),
               "The Shield of the Canyon. Nothing gets past him."),
    "corvin": (CHAMPION, dict(hp=440, armour=6, speed=80, dmg=46, every=0.8, reach=40, boss=1.8),
               "The Uncrowned's star-glass blade finds every weak point."),
    "ignar": (CHAMPION, dict(hp=800, armour=10, speed=44, dmg=50, every=1.4, reach=56, splash=80, dot="burn", dot_dps=14, dot_s=3),
              "The Cinder Warden walks into the horde as a fire walks into a field."),
    "aurath": (CHAMPION, dict(hp=600, armour=6, speed=70, dmg=38, every=1.2, reach=220, chain=5, blocks=False),
               "The storm itself, come to break the citadel's sky."),
    "elowen": (CHAMPION, dict(hp=700, armour=8, speed=40, dmg=22, every=1.2, reach=60, heal=0.07, heal_r=220, heal_s=1.5),
               "The Evergreen. Wherever she stands, the wounded stand again."),
    "thalassa": (CHAMPION, dict(hp=640, armour=8, speed=48, dmg=34, every=1.3, reach=200, splash=90, slow=0.5, slow_s=2, blocks=False),
                 "The Deep rises behind her and falls on the horde."),
    "orrok": (CHAMPION, dict(hp=1200, armour=20, speed=30, dmg=60, every=2.0, reach=52, splash=70, siege=3.5),
              "The Mountain walks. Walls do not survive him."),
    "nyxara": (CHAMPION, dict(hp=560, armour=6, speed=60, dmg=70, every=1.6, reach=240, boss=2.0, blocks=False),
               "Where her face should be, there are only stars. The horde cannot look at her."),
    "ilyra": (CHAMPION, dict(hp=520, armour=6, speed=70, dmg=48, every=0.9, reach=44, boss=2.5),
              "She learned a little of the Unmaking in the Outer Hollow. She uses it now."),
    "seraphel": (CHAMPION, dict(hp=620, armour=12, speed=62, dmg=52, every=1.0, reach=46, boss=2.0, siege=1.5),
                 "The Dawnblade's glass sword burns brightest against the dark."),
    "oswin": (CHAMPION, dict(hp=700, armour=8, speed=55, dmg=36, every=1.0, reach=200, aura=0.3, aura_r=200, heal=0.04, heal_r=200, heal_s=2, blocks=False),
              "The White Lantern. In his light the whole army fights as one."),
}
CHAMPION_COST = 320
CHAMPION_COOLDOWN = 45.0


def sn(v):
    return f'&"{v}"'


def string(v):
    return '"' + v.replace("\\", "\\\\").replace('"', '\\"') + '"'


def hero_info(hero_id):
    text = open(os.path.join(ROOT, "data", "heroes", f"{hero_id}.tres")).read()
    get = lambda k: (re.search(r'^%s = "(.*)"$' % k, text, re.M) or [None, ""])[1]
    element = (re.search(r'^element = &"(.*)"$', text, re.M) or [None, ""])[1]
    order = int((re.search(r'^order = (\d+)$', text, re.M) or [None, "0"])[1])
    return get("display_name"), get("title"), element, order


def write(aid, name, title, role, element, cost, cooldown, count, st, desc, order, hero=""):
    f = ["[gd_resource type=\"Resource\" script_class=\"AllyData\" format=3]", "",
         "[ext_resource type=\"Script\" path=\"res://scripts/data/ally_data.gd\" id=\"1_ally\"]", "",
         "[resource]", "script = ExtResource(\"1_ally\")",
         f"id = {sn(aid)}", f"display_name = {string(name)}", f"title = {string(title)}",
         f"description = {string(desc)}", f"role = {role}", f"element = {sn(element)}"]
    if hero:
        f.append(f"hero = {sn(hero)}")
    f += [f"order = {order}", f"cost = {cost}", f"cooldown = {float(cooldown)}", f"count = {count}"]
    if st.get("max") or hero:
        f.append(f"max_alive = {st.get('max', 1)}")
    f += [f"max_health = {float(st['hp'])}", f"armour = {float(st.get('armour', 0))}", f"speed = {float(st['speed'])}"]
    if st.get("flying"):
        f.append("flying = true")
    if not st.get("blocks", True):
        f.append("blocks = false")
    f += [f"damage = {float(st['dmg'])}", f"attack_interval = {float(st['every'])}", f"attack_range = {float(st['reach'])}"]
    for key, field in [("splash", "splash_radius"), ("siege", "siege_multiplier"), ("boss", "boss_multiplier"),
                       ("slow", "slow"), ("slow_s", "slow_duration"), ("dot_dps", "dot_damage"), ("dot_s", "dot_duration"),
                       ("heal", "heal_amount"), ("heal_r", "heal_radius"), ("heal_s", "heal_interval"),
                       ("aura", "aura_damage"), ("aura_r", "aura_radius")]:
        if key in st:
            f.append(f"{field} = {float(st[key])}")
    if "chain" in st:
        f.append(f"chain_count = {st['chain']}")
    if st.get("siege_only"):
        f.append("siege_only = true")
    if "dot" in st:
        f.append(f"dot_kind = {sn(st['dot'])}")
    with open(os.path.join(OUT, f"{aid}.tres"), "w") as fh:
        fh.write("\n".join(f) + "\n")


def main():
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        if old.endswith(".tres"):
            os.remove(os.path.join(OUT, old))
    for i, (aid, name, title, role, element, cost, cooldown, count, st, desc) in enumerate(TROOPS):
        write(aid, name, title, role, element, cost, cooldown, count, st, desc, i)
    for hero_id, (role, st, line) in CHAMPIONS.items():
        name, title, element, order = hero_info(hero_id)
        write(f"champion_{hero_id}", name, title, role, element, CHAMPION_COST, CHAMPION_COOLDOWN, 1, st, line,
              100 + order, hero=hero_id)
    print(f"Wrote {len(TROOPS)} troops and {len(CHAMPIONS)} champions to {OUT}")


if __name__ == "__main__":
    main()
