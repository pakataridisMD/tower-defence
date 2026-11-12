#!/usr/bin/env python3
"""The army's battle shouts in the counter-attack of the final level: who says what, and when.

Running it writes data/army/shouts.json, which scripts/game/army_voice.gd reads. tools/army/voice_shouts.py
records every line with ElevenLabs into assets/audio/army/<voice>/<line id>.ogg.

Events (army_voice.gd decides when they fire, and keeps them occasional):
  muster    a squad marches out of the camp          charge   a unit meets the horde
  fight     now and then in a fight                  siege    a unit strikes the citadel
  hurt      a unit falls below a third of its health death    a unit falls (a cry, no words)
  bolt      the citadel's spires strike the army     crack    the citadel loses a quarter of its health
  victory   the citadel falls

Lines follow the canon (lore/CANON.md): we came down the Rift road and through the gap in the Black Gate;
Nhal Vorath is built from the ruins of old Vael; the enemy are the Unbound; Solenne lost its outer wall,
the Lumen Gate. Every line names something real in the story: no filler.

usage: python3 tools/army/shouts.py
"""
import json
import os

# Troop voices: which units speak with which voice, and how the voice is described for casting.
VOICES = {
    "line": {
        "who": "Solenne Footmen, Lantern Pikemen, Forge-Knights, the Banner",
        "cast": "gruff, battle-worn male infantry sergeant, British, 40s",
        "units": ["footman", "pikeman", "ember_knight", "banner_bearer"],
    },
    "wall": {
        "who": "Wallguard Crossbows, Firebrands, Pearlhaven Harpooners",
        "cast": "hard, loud female soldier, 30s, rough edge",
        "units": ["crossbowman", "firebrand", "pearl_marine"],
    },
    "stone": {
        "who": "Stoneborn Shieldbreakers",
        "cast": "very deep, gravelly old male, slow and heavy",
        "units": ["ironbreaker"],
    },
    "veil": {
        "who": "Deepwood Archers, Veilwalker Shades and Hollow-Hunters",
        "cast": "cold, quiet, dangerous male, low and controlled",
        "units": ["root_archer", "veil_blade", "hollow_hunter"],
    },
    "order": {
        "who": "Order Lantern-Bearers, Tidefolk Ice-Seers",
        "cast": "steady, warm female cleric, calm under fire",
        "units": ["lantern_cleric", "tide_priestess"],
    },
    "gale": {
        "who": "Galeborn Sky-Lancers, Stormcallers, Hawk-Riders",
        "cast": "wild, fierce young female rider, shouting over wind",
        "units": ["gale_lancer", "stormcaller", "griffin_rider"],
    },
    "crew": {
        "who": "Spirewright crews of the Ram, the Catapult and the Golem",
        "cast": "Master Fennick's voice: gruff old Scottish engineer barking orders",
        "units": ["battering_ram", "sunstone_catapult", "spire_golem"],
    },
}
# The warhounds have no voice of their own: they howl with the army (their war cry strip).

# Troop lines: voice -> event -> [text]. A v3 audio tag can lead a line in [brackets]; the bubble hides it.
LINES = {
    "line": {
        "muster": ["Solenne, with me! Up the road!", "Shields up! We march on Nhal Vorath!", "Form the line! The Lanternguard goes first!"],
        "charge": ["Here they come! Hold the line!", "Unbound ahead! Shields together!"],
        "fight": ["Push! Push them back to the Gate!", "Don't give them a step!", "Close the gap! Close it!"],
        "siege": ["We're at the wall! Hit it!", "Break the gate! Again!"],
        "hurt": ["[pained] I'm hit! Keep going!"],
        "death": ["[pained scream] Aaargh!", "[choking gasp] Nnh... no..."],
        "bolt": ["Spires! Raise shields!"],
        "crack": ["It's cracking! Keep hitting it!", "The wall's giving way!"],
        "victory": ["[triumphant roar] Nhal Vorath is down! For Solenne!"],
    },
    "wall": {
        "muster": ["Crossbows, forward! Stay behind the shields!", "Wallguard! Loose on my mark!", "Fire up! Let's burn them out!"],
        "charge": ["Unbound in range! Loose!", "Target the big ones!"],
        "fight": ["Reload! Reload!", "Keep it coming! Don't stop shooting!", "That's for the Lumen Gate!"],
        "siege": ["Aim for the gate! Bring it down!", "Every bolt on that wall!"],
        "hurt": ["[pained] Argh, I'm bleeding! Cover me!"],
        "death": ["[pained scream] Aaah!", "[sharp cry] Nngh!"],
        "bolt": ["Down! The spires are firing!"],
        "crack": ["Look at it shake! Keep shooting!", "We're breaking it!"],
        "victory": ["[triumphant] It's falling! It's really falling!"],
    },
    "stone": {
        "muster": ["Stoneborn! Hammers up!", "We built walls for two thousand years. We know how to break one.", "Out of the way. We've a wall to knock down."],
        "charge": ["Let them come. Stone doesn't move.", "Into them, lads!"],
        "fight": ["[grunts] Is that all the Hollow's got?", "Stand firm! Like the Canyon!", "Hit it again!"],
        "siege": ["Find the seam. Then hit the seam.", "Rune-hammers on the gate! Now!"],
        "hurt": ["[grunts] Barely a scratch. Keep swinging."],
        "death": ["[deep groan] Hrrgh...", "[roar, cut short] Raaah--"],
        "bolt": ["Let the spires spit. Keep hammering."],
        "crack": ["Hear that? That's the stone giving up.", "There's the seam! Wider!"],
        "victory": ["[booming laugh] Down it comes! Mind your heads!"],
    },
    "veil": {
        "muster": ["We know the dark. Follow us in.", "Quietly now. Let the shield wall make the noise.", "Into the shadows. Find the big ones."],
        "charge": ["There. Under the arm. Strike.", "They can't see us. Go."],
        "fight": ["Thorn-arrows. Let them rot.", "One more. Then the next.", "I walked the Hollow. You don't frighten me."],
        "siege": ["The gate has weak joints. Here, and here.", "Cut the ropes behind the gate!"],
        "hurt": ["[hisses in pain] Careless. Won't happen again."],
        "death": ["[sharp gasp] Ah...", "[low groan] Mmh..."],
        "bolt": ["Spires. Into the shadows."],
        "crack": ["It's bleeding. Keep cutting.", "The stone's splitting."],
        "victory": ["[quietly, satisfied] It's done. Vael's house falls."],
    },
    "order": {
        "muster": ["Lanterns lit! Stay in the light!", "The Order marches. Wounded, come to me!", "The Tidefolk are with you. We'll close your wounds."],
        "charge": ["Stay close to the lanterns!", "Hold on, I'm coming!"],
        "fight": ["Stand in the light! It will mend you!", "Breathe. You're not done yet.", "Who's hurt? Here!"],
        "siege": ["Push them to the gate! We'll keep you standing!", "Lanterns forward! Light the wall!"],
        "hurt": ["[pained] I can still heal, keep going!"],
        "death": ["[soft cry] Oh...", "[gasp] Ahh..."],
        "bolt": ["Wounded! Back to the lanterns!"],
        "crack": ["The wall is breaking! Hold on!", "Almost there! Don't fall now!"],
        "victory": ["[joyful, through tears] It's down. Light the lanterns, all of them!"],
    },
    "gale": {
        "muster": ["Galeborn! Ride!", "Hawks up! Over the horde and onto the walls!", "Storm's coming! Get out of our way!"],
        "charge": ["Lances down! Charge!", "Hit them like thunder!"],
        "fight": ["Lightning, take them! Next one!", "Faster! Faster!", "Hah! Did you see that?"],
        "siege": ["Hit the spires from above!", "Bring the lightning down on that gate!"],
        "hurt": ["[pained] I'm hit! Still flying!"],
        "death": ["[falling scream] Aaaah!", "[cry] No!"],
        "bolt": ["Spire fire! Break left!"],
        "crack": ["It's cracking! Again! Again!", "Look at the walls! They're coming down!"],
        "victory": ["[whooping] It's down! Ride, ride, ride!"],
    },
    "crew": {
        "muster": ["Get that ram moving! Put your backs into it!", "Catapult up! Sunstone shards, and mind your fingers!", "Spirewrights! Wake the golem and walk it in!"],
        "charge": ["Don't stop for the horde! The gate's the job!", "Keep rolling, lads!"],
        "fight": ["Keep the wheels turning!", "Load! Wind! Loose!", "Steady, steady!"],
        "siege": ["And swing! And swing!", "Right on the gate! Beautiful!"],
        "hurt": ["[grunts] She's taking a beating, keep pushing!"],
        "death": ["[groan] Agh... keep it going...", "[shout, cut short] Look out--"],
        "bolt": ["Spire fire! Get under the roof!"],
        "crack": ["She's cracking! Hit the same spot!", "That gate's going! Once more!"],
        "victory": ["[gruff laugh] Ha! Told you she'd come down!"],
    },
}

# Heroes marching as champions: one voice each, from tools/voice/cast.json. Events: muster, fight, siege, hurt, death,
# crack (when a quarter of the citadel falls and the hero is on the field).
CHAMPIONS = {
    "tamsin": {
        "muster": "Lanternguard, on me! We take that gate today.",
        "fight": "Keep your shields up. I'm not writing any more letters home.",
        "siege": "We came through the Rift for this. Hit it!",
        "hurt": "[pained] I've had worse. Keep moving!",
        "death": "[weakly] Finish it... for Solenne...",
        "crack": "It's coming down! Everyone, together!",
    },
    "brannoc": {
        "muster": "Out of my way! This hammer was made for gates!",
        "fight": "Come here, Unbound! I'll beat you flat like iron!",
        "siege": "Every blow I strike is for the Reach! Again!",
        "hurt": "[grunts] Ha! You hit like a cold forge!",
        "death": "[roaring, then fading] The fire... goes out...",
        "crack": "Hear it ring? It's breaking!",
    },
    "kaela": {
        "muster": "Galeborn, follow me! Nobody rides ahead of the Marshal!",
        "fight": "Too slow! The Steppe rides faster than you!",
        "siege": "Straight at the gate! Don't stop for anything!",
        "hurt": "[pained] I'm still in the saddle!",
        "death": "[gasping] Ride... ride on without me...",
        "crack": "It's cracking! Don't give them time to breathe!",
    },
    "sylvaine": {
        "muster": "The Deepwood's archers are with you. Keep your heads down.",
        "fight": "Every arrow finds its mark.",
        "siege": "The gate has joints. My arrows will find them.",
        "hurt": "[pained] A scratch. My bow is steady.",
        "death": "[softly] The Deepwood... will remember...",
        "crack": "The wall is splitting. Keep at it.",
    },
    "mirelle": {
        "muster": "I've seen this moment. We win it if we hold together.",
        "fight": "Ice, take their feet! Now strike!",
        "siege": "The tide is with us. Push them to the gate!",
        "hurt": "[pained] I didn't see that one coming.",
        "death": "[fading] I saw... the ending... it's good...",
        "crack": "It's breaking! Just like I saw!",
    },
    "gorrim": {
        "muster": "Behind my shield. Nothing gets past Gorrim.",
        "fight": "Hit my shield all day. Won't do you any good.",
        "siege": "Stone breaks stone. Let me at that gate.",
        "hurt": "[grunts] My shield's dented. I'm not.",
        "death": "[deep groan] Hold... the line...",
        "crack": "There! The wall's giving! Push!",
    },
    "corvin": {
        "muster": "I've walked the Rift my whole life. I know the way in.",
        "fight": "You're slow. That's going to cost you.",
        "siege": "Every wall has a weak point. That one's mine.",
        "hurt": "[hisses] Clever. Not clever enough.",
        "death": "[quiet] Should have... seen that one...",
        "crack": "It's cracking. Keep cutting!",
    },
    "ilyra": {
        "muster": "I've been inside these walls. I know how they break.",
        "fight": "You kept me in the dark for years. Now you'll see what I learned.",
        "siege": "Down, Nhal Vorath! I'm not your prisoner anymore!",
        "hurt": "[pained] I've felt worse in your cells!",
        "death": "[whispering] Father... I'm sorry...",
        "crack": "It's breaking! Tear it all down!",
    },
    "seraphel": {
        "muster": "The Dawnblade is drawn! Into the dark!",
        "fight": "Sunstone light burns hollow things! Burn!",
        "siege": "Let the light into Nhal Vorath!",
        "hurt": "[pained] The light still burns!",
        "death": "[fading] Carry... the light...",
        "crack": "The walls are breaking! Shine through!",
    },
    "oswin": {
        "muster": "I held this Gate shut with my own hands. Now we go through.",
        "fight": "Stand in my light, all of you. It holds.",
        "siege": "Old Vael was a beautiful city once. Bring down what he made of it.",
        "hurt": "[pained, wry] I'm too old for this. Keep going!",
        "death": "[softly] Keep... the lantern lit...",
        "crack": "There! It breaks! Don't stop!",
    },
    "ignar": {
        "muster": "Two thousand years ago I helped shut you in here, Vael-Orrun. I've come to finish it.",
        "fight": "Burn, Unbound! Burn to ash!",
        "siege": "Fire against stone! Melt it down!",
        "hurt": "[roars] You can't put out a fire like me!",
        "death": "[fading rumble] The cinders... cool...",
        "crack": "Your house is burning, Vael!",
    },
    "aurath": {
        "muster": "The storm has come down the Rift! Nhal Vorath will hear it!",
        "fight": "Lightning! Take them all!",
        "siege": "Break, walls! Break under the storm!",
        "hurt": "[snarls] You cannot wound the sky!",
        "death": "[fading] The storm... passes...",
        "crack": "Thunder on your walls, Vael-Orrun!",
    },
    "elowen": {
        "muster": "Stand up, wounded! The Evergreen is here!",
        "fight": "Roots, hold them! Grow, and hold!",
        "siege": "Roots break stone. Slowly, then all at once.",
        "hurt": "[pained] I bend. I don't break.",
        "death": "[softly] Plant me... somewhere green...",
        "crack": "The roots are in the walls! It's splitting!",
    },
    "thalassa": {
        "muster": "The Deep has followed me down the Rift. It's hungry.",
        "fight": "Drown in it!",
        "siege": "Water breaks every wall in time. Today it's quick.",
        "hurt": "[pained] The tide always comes back.",
        "death": "[fading] Back... to the Deep...",
        "crack": "The walls are breaking! Flood them!",
    },
    "orrok": {
        "muster": "The Mountain walks. Walls of Vael, you are mine.",
        "fight": "Small things. Out of my path.",
        "siege": "I am older than these walls. I will outlast them.",
        "hurt": "[deep rumble] A pebble against a mountain.",
        "death": "[deep, fading] The mountain... sleeps...",
        "crack": "Crumble.",
    },
    "nyxara": {
        "muster": "I know this dark. I shut you into it myself, Vael-Orrun.",
        "fight": "Look at me, Unbound. You can't, can you?",
        "siege": "Your walls were never yours, Vael. They were your prison.",
        "hurt": "[hisses] You'll pay for that.",
        "death": "[whispering] Into the dark... again...",
        "crack": "It's breaking. Your prison is breaking, Vael.",
    },
}


def _id(voice, event, n):
    return f"{voice}_{event}_{n + 1}"


def build():
    voices, lines = {}, {}
    for voice, spec in VOICES.items():
        voices[voice] = {"who": spec["who"], "units": spec["units"]}
        lines[voice] = {event: [{"id": _id(voice, event, n), "text": text} for n, text in enumerate(texts)]
                        for event, texts in LINES[voice].items()}
    champions = {hero: {event: [{"id": f"{hero}_{event}", "text": text}] for event, text in spec.items()}
                 for hero, spec in CHAMPIONS.items()}
    return {"_about": "Battle shouts of the counter-attack. Written by tools/army/shouts.py; do not edit by hand. "
                      "Audio: assets/audio/army/<voice or hero>/<id>.ogg. A [tag] leading a line is for the voice only.",
            "voices": voices, "lines": lines, "champions": champions}


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "data", "army", "shouts.json")
    data = build()
    with open(path, "w") as fh:
        json.dump(data, fh, indent=1)
        fh.write("\n")
    count = sum(len(v) for e in data["lines"].values() for v in e.values()) + sum(len(v) for e in data["champions"].values() for v in e.values())
    chars = sum(len(x["text"]) for e in data["lines"].values() for v in e.values() for x in v) + \
        sum(len(x["text"]) for e in data["champions"].values() for v in e.values() for x in v)
    print(f"{path}: {count} lines, {chars} characters")


if __name__ == "__main__":
    main()
