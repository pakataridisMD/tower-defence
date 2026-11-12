#!/usr/bin/env python3
"""The campaign story: every cinematic, the town saved by each stage, and the cast, as data.

This file is the source of truth for story text. It writes:

    data/story/story.json                 when each cinematic plays, and the town each stage saves
    data/story/cinematics/<id>.json       one file per cinematic: shots with narration and art notes
    data/story/characters.json            heroes, villains and the overlord
    docs/story/scripts.md                 the same scripts as a readable screenplay

Run:   python3 tools/story/story_content.py            (writes into the repo)
       python3 tools/story/story_content.py --out DIR  (writes data/ and docs/ under DIR instead)

The canon behind it (world, history, characters) is docs/story/bible.md. The looks of each character
are in docs/story/characters.md.

Writing rules (the voice tool reads each shot's "text"):
- Write for a player who knows nothing. Every scene says where we are, what is attacking and why, and what
  changed. Name people and places; give the cause of things. No vague poetry standing in for plot: if a
  line could sit in any fantasy game, cut it or make it about this one.
- Everything is physical. The Black Gate is a stone door at the bottom of the Rift, the Hollow is a cavern
  land under the world, the Heartstone is the Gate's key. Nothing happens "in the sky" or "beyond the stars".
- Short sentences. A blank line inside a text is a dramatic pause; "..." is a short hesitation.
- The narrator is Queen Ysolde, speaking after the war. She never gives away a secret before its scene.
- The lands open in a fixed order (Ember, Storm, Nature, Water, Earth, Void), so land scenes may refer to
  earlier ones. From the midpoint (12 stages won) the lands are fought at night.
- Winning a stage saves its town. Never write that we lose or give up a town (except the Lumen Gate).
- Every enemy is one of the Unbound (Hollowed, Risen or Wild). "Warden" means only the six monarchs.
"""
import json
import os
import re
import sys

WORDS_PER_SECOND = 2.3  # slow, deep narration
PAD_SECONDS = 1.5


def shot(text, art, speaker="narrator", duration=None):
    words = len(re.findall(r"[\w'-]+", text))
    pauses = text.count("\n\n") * 0.8 + text.count("...") * 0.4
    secs = duration if duration is not None else round(words / WORDS_PER_SECOND + pauses + PAD_SECONDS, 1)
    return {"text": text, "speaker": speaker, "art_note": art, "image": "", "voice": "", "duration": secs}


# --------------------------------------------------------------------------------------- cinematics
# Each: id -> (title, when (for the screenplay), shots)
CINEMATICS = {}


def cin(cid, title, when, *shots):
    CINEMATICS[cid] = {"title": title, "when": when, "shots": list(shots)}


# ----------------------------------------------------------------------------- the opening (~2:00)
cin("prologue", "The Last Lantern", "Before the first stage. The opening story video, about 2 minutes.",
    shot("Two thousand years ago there were seven kingdoms: six in a ring, each with its own magic, and "
         "Orrun in the middle, where all their roads met.",
         "An old painted map coming out of darkness: six kingdoms in a ring, each under its own crown and "
         "colour (red, blue-white, green, teal, ochre, violet), and a seventh, colourless, in the middle."),
    shot("The songs say Orrun's king, Vael-Orrun, wanted all six crowns. He learned a power that makes magic "
         "stop. Where his armies walked, fire would not burn.",
         "The High King's armies crossing a burning land; behind them the flames freeze into grey glass, the "
         "grass stops moving, a river hangs still in mid-fall."),
    shot("The six monarchs beat him. They drove him and his army down the Rift, a chasm miles deep, and "
         "shut them behind the Black Gate at the bottom.",
         "A chasm splitting the eastern land, its walls dropping into darkness. Far below, a stone door as tall "
         "as a mountain swinging shut on a grey army. The six monarchs on the rim, pushing."),
    shot("They made its key from his crown: the Heartstone. Then they gave their lives to keep the Gate "
         "shut. Their spirits sleep in their lands. We call them the Wardens.",
         "The crown shattering into a six-coloured crystal, the Heartstone. The six monarchs fading into a "
         "volcano, a storm, a tree, a sea, a mountain, a starless sky."),
    shot("On his ruins we built Solenne, my city, with the Heartstone at its heart and the Sunstone above "
         "it, a lens whose light the things of the dark cannot bear.\n\nThat is how the songs tell it.",
         "Dawn over Solenne: six white walls rising on black ruins, the Heartstone glowing at the centre, the "
         "golden Sunstone above."),
    shot("Six years ago, my Lord Marshal, Cassivane, lost his daughter Ilyra in the Rift.",
         "Night. Cassivane Dral, the Lord Marshal, alone on a balcony, holding an open gold locket with a "
         "girl's portrait. His face is in shadow."),
    shot("This spring, somebody unlocked the Black Gate. We did not know who.",
         "The bottom of the Rift. The Black Gate grinding open; grey shapes pressing out of the dark behind "
         "it."),
    shot("Oswin, the master of our Order, turned the light of all his towers on it and drove it back, until "
         "the gap was only as wide as a cart.",
         "Oswin, old, grey robes and hat, at the foot of the Gate with his lantern-staff raised. Behind him a "
         "line of Spirewright towers burning in six colours, their beams on the door."),
    shot("Then the ground gave way, and he fell through.\n\nHis lantern was still lit.",
         "The ground under Oswin gives way. He falls through the gap into the dark. Last frame: the small "
         "white light of his lantern, still burning, falling away."),
    shot("Six armies came out through the gap, each led by a grey-eyed champion we called a Herald. Each "
         "went to one land, to drive its Warden mad.",
         "A single-file column of the Unbound marching out of the gap and up the Rift road, splitting into "
         "six. At the head of each column, a grey-eyed Herald."),
    shot("A land whose Warden is mad cannot keep out the element opposite its own. The sea climbs the "
         "volcano. Stone climbs the plains. The Herald's army comes in with it.",
         "Six quick cuts: black seawater climbing a volcano, boulders walking up a grassy plateau, grey mist "
         "under giant trees, burning runners on a frozen sea, armoured lightning in a red canyon, thorns over "
         "the Rift."),
    shot("I am Ysolde, Queen of Solenne. You are a Spirewright, the last of Oswin's apprentices. You build "
         "the towers.\n\nWe take the lands back one at a time. Hold the road to each town. Kill its "
         "Herald. Free its Warden.\n\nHold the road.",
         "Queen Ysolde on the white walls of Solenne, looking east toward smoke on the horizon. Title card."),
    )

# ------------------------------------------------------------------------------- the Ember Reach
cin("ember_intro", "The Ember Reach", "Before the first stage of the Ember Reach.",
    shot("The Ember Reach is a land of volcanoes, and the Emberfolk forge in their heat. Its Warden, Ignar, "
         "sleeps in the fire under the mountain of Pyrrhenhall.",
         "Black basalt terraces, lava rivers, glassworks glowing, red and brass banners. Emberfolk at anvils."),
    shot("Ignar had gone mad, and the sea was climbing the mountain. Inside the water came the Herald's "
         "army: the drowned, led by the Saltmother. The town of Kethra was first on their road.",
         "A black tide of seawater and grey-eyed drowned climbing the slopes, steam rising where it touches "
         "lava. Inside the tide, a tall column of water walks: the Saltmother, glimpsed. Kethra below it."),
    shot("I'm Fennick. I design the towers; you build them. Fire burns, water slows, and you, child, will "
         "place them where I tell you.\n\nHold the road to Kethra. The Saltmother is somewhere up that "
         "mountain. Kill her, and her army loses its head.",
         "Master Fennick, old, spectacles, leather apron, pointing at a tower plan on a cart. Tamsin behind "
         "him waving carts of Emberfolk to safety.",
         speaker="fennick"),
    )

cin("ember_herald", "The Drowned Herald", "After Brazier Hold (Ember 2). Brannoc Emberhand joins.",
    shot("At Brazier Hold the Saltmother came up the road herself, inside a column of black seawater. She "
         "had been the high priestess of the Tidefolk. Two years ago she went east to the Rift, and nobody "
         "knew why.",
         "The Saltmother's water-column bursting apart on the steps, fish and drowned lanterns scattering. Her "
         "empty grey eyes going dark."),
    shot("When she fell, we found a cage of salt on the steps. In it was Brannoc Emberhand, the smith who "
         "forged Solenne's gates. She had kept him nine days to make him forge chains for her army.",
         "A cage of crusted salt breaking open. Brannoc Emberhand, huge, bald, brass-ringed beard, staggering "
         "out and grabbing his hammer from the rubble; its head flares orange."),
    shot("Nine days she asked me for chains. Nine days I told her no.\n\nNow give me a wall to stand on.",
         "Brannoc on the wall of Brazier Hold, hammer on his shoulder, grinning. Joins as a hero.",
         speaker="brannoc"),
    )

cin("ember_warden", "Ignar, Freed", "After Pyrrhenhall (Ember 4). Ignar joins.",
    shot("Under Pyrrhenhall we fought the thing Ignar had become, the Cinder Tyrant, a giant of grey fire. "
         "When it fell, the grey burned off it, and Ignar woke.",
         "The Cinder Tyrant collapsing in the caldera, grey-white fire guttering. From the cracked basalt "
         "steps a tall black-stone figure with an orange molten heart: Ignar."),
    shot("Someone whispered in my sleep until I forgot what I was. I am awake now. I will burn for you.",
         "Ignar kneeling to Brannoc and the Emberfolk, his heart-light warming their faces.",
         speaker="ignar"),
    shot("With its Warden awake, the Reach could keep the sea out again. By morning the water had run back "
         "down the mountain, and the Emberfolk lit their forges.",
         "Steam clearing off the slopes of Pyrrhenhall, the sea draining away. Emberfolk relighting forges; "
         "Ignar standing among them, much taller than anyone."),
    shot("One land back. Five to go. Pack your tools, Spirewright. The Thunder Steppe is next.",
         "Fennick rolling up a tower plan, the lit forges of the Reach behind him.", speaker="fennick"),
    )

# ------------------------------------------------------------------------------- the Thunder Steppe
cin("storm_intro", "The Thunder Steppe", "Before the first stage of the Thunder Steppe.",
    shot("The Thunder Steppe is grassland on a high plateau. The Galeborn live there on horseback and steer "
         "by the storms. Its Warden, Aurath, sleeps in the storms themselves.",
         "Endless high grass under a racing sky, standing stones, tent-cities, riders on grey horses."),
    shot("Aurath had gone mad, and the storms had stopped moving. Without them the Steppe could not keep "
         "out the earth. Walking stone climbed the cliffs, led by the Herald Gorrath.",
         "A frozen, motionless sky. Armoured earth spirits climbing the plateau edge. At their head a giant "
         "Stoneborn general with a square hole in his chest: Gorrath."),
    shot("The Galeborn don't build walls. Your towers are the only walls they've got. Start at Stonering "
         "Camp.",
         "Fennick on horseback, badly, holding his hat on, pointing at a camp of standing stones.",
         speaker="fennick"),
    )

cin("storm_herald", "The Stone Herald", "After Highwind (Storm 2). Kaela Stormrider joins.",
    shot("Gorrath had been a Stoneborn general, the man who held the Kharum Pass for a month. He went to "
         "the Rift two years ago, like the Saltmother. He came back with his heart cut out and a carved "
         "stone in its place.",
         "Gorrath breaking apart on the ridge into boulders that keep rolling, then stop. The carved stone "
         "heart in his chest cracks."),
    shot("Out of the dust rode Kaela Stormrider, the Galeborn's war-leader. She had been fighting his army "
         "alone for eleven days, falling back from camp to camp.",
         "Kaela Stormrider bursting out of the dust on her grey stallion Thunderclap, lightning lance "
         "crackling, white war-paint across her face."),
    shot("Eleven days I've been riding away from that thing. I hate riding away. Point me at the next one.",
         "Kaela reining in beside the player's towers, looking back at Highwind. Joins as a hero.",
         speaker="kaela"),
    )

cin("storm_warden", "Aurath, Freed", "After Aurvanis (Storm 4). Aurath joins.",
    shot("Over Aurvanis we brought down the Thunderhead, a storm gone solid as black glass. It was Aurath's "
         "madness. It shattered, and the sky moved again for the first time in a month.",
         "The black solid cloud shattering, frozen lightning falling like glass. Rain. Riders lifting their "
         "faces to it."),
    shot("A voice told me to be still. So I was still, and the stone walked in. Never again. My winds are "
         "yours.",
         "Aurath, a rider-shape of cloud and lightning, flickering, bowing over the towers.",
         speaker="aurath"),
    shot("The walking stone fell where it stood. The Galeborn rode home to Aurvanis. Two lands were free.",
         "Boulders crumbling on the plateau. Galeborn raising their tents again at Aurvanis; Kaela watching "
         "from her horse."),
    )

# ------------------------------------------------------------------------------- the Verdant Deep
cin("nature_intro", "The Verdant Deep", "Before the first stage of the Verdant Deep.",
    shot("The Verdant Deep is a forest of trees as tall as towers. The Deepwood live in the branches. Its "
         "Warden, Elowen, sleeps in the oldest tree of all, at Sylvanmere.",
         "Giant trees, rope bridges, glow-moss lighting the roots like streets, Deepwood archers."),
    shot("Elowen had gone mad, and the forest could not keep out the Hollow, the dark from behind the Gate. "
         "It crept in under the trees. With it came a Herald who sang the dead back onto their feet: the "
         "Pale Vesper.",
         "The glow-moss going dark row by row. Pale violet ghost-lights drifting between the roots, and a "
         "tall grey-veiled singer with her mouth open: the Pale Vesper."),
    shot("The Deepwood have buried their dead under these trees for a thousand years. Now we know where her "
         "army comes from.",
         "Tamsin at the edge of a root-road, lantern-pole raised, as grey shapes climb out of the moss.",
         speaker="tamsin"),
    )

cin("nature_herald", "The Hollow Herald", "After Elderhollow (Nature 2). Sylvaine Thornwhisper joins.",
    shot("At Elderhollow the Pale Vesper fell. She had been a Veilwalker singer who sang at funerals. She "
         "too had gone to the Rift two years ago. Before she died, the grey went out of her eyes.",
         "The Pale Vesper falling among the roots, her ghost-choir scattering like moths."),
    shot("The Marshal sent us to the Rift. Six of us. Study the Gate, he said...\n\nHe knew what was behind "
         "it.",
         "Close on the Vesper's face, the grey light leaving her eyes; for a moment she looks like herself.",
         speaker="pale_vesper"),
    shot("Cassivane was my Marshal and my friend. I did not believe her. I thought it was the Hollow "
         "talking.",
         "Ysolde in the Hall of the Ring reading a messenger's report, then folding it away."),
    shot("In the root-halls we found Sylvaine Thornwhisper, the Deepwood's best archer. She had held the "
         "root-doors alone while the whole town climbed out.",
         "Sylvaine Thornwhisper standing amid a ring of fallen hollow things, a pale leafing longbow in her "
         "hands, moss cloak. She lowers the bow."),
    shot("They're all out. Every child. Now show me where to stand.",
         "Sylvaine at the edge of a tower platform, arrow on the string. Joins as a hero.",
         speaker="sylvaine"),
    )

cin("nature_warden", "Elowen, Freed", "After Sylvanmere (Nature 4). Elowen joins.",
    shot("At Sylvanmere we cut Elowen out of the Elder Broodmother, the rotten thing that had grown over "
         "her inside the oldest tree. She was very old, and very tired.",
         "The Broodmother collapsing; grey bark peeling away to reveal Elowen, bent, with white-blossom hair."),
    shot("The tree is dying. It has one seed left. Take it, child, and plant it somewhere the dark can't "
         "reach.",
         "Elowen pressing a single glowing seed into Sylvaine's hand.", speaker="elowen"),
    shot("The Hollow drew back out of the forest. Three lands were free, and we went home to Solenne for "
         "one night's rest.",
         "Grey mist pulling back from the roots; the glow-moss lighting again. The army on the road west, "
         "Sylvaine's closed hand glowing green."),
    )

# ------------------------------------------------------------------------------- Frostmere
cin("water_intro", "Frostmere", "Before the first stage of Frostmere (fought at night).",
    shot("Frostmere is a frozen sea in the north. The Tidefolk build their towns on the ice. Its Warden, "
         "Thalassa, sleeps in the water under it.",
         "A vast frozen sea in the dark, stilt towns, pearl-white harbours lit by torches."),
    shot("We fought there in the dark. Thalassa had gone mad, and the ice could not keep out fire. Burning "
         "runners came across it, and the ice melted behind them. They were led by a boy made of embers, "
         "the Herald Ashwick.",
         "Burning runners skating across the ice, leaving black water behind them. At their head a boy made "
         "of white embers with a messenger's satchel: Ashwick."),
    shot("Fennick always said water slows. Out here we're standing on it. Let's prove him right.",
         "Tamsin on the ice at Netmend with Fennick's spectacles hanging round her neck.", speaker="tamsin"),
    )

cin("water_herald", "The Flame Herald", "After Reedhaven (Water 2). Mirelle the Tide-Seer joins.",
    shot("Ashwick had been the Concord's youngest messenger. Two years ago he ran east to the Rift with a "
         "letter, and never came back. When he fell in the reeds, his satchel split open. The letter was "
         "still in it, under Cassivane's seal.",
         "Ashwick stumbling in the reeds, embers scattering, the satchel falling open: a letter stamped "
         "with the Lord Marshal's seal lands in the snow."),
    shot("In the middle of the burning reeds stood a tower of ice that had not melted. Inside it was "
         "Mirelle, a blind Tidefolk seer who reads the future in ice. She had kept forty children alive in "
         "there.",
         "A tower of ice in a ring of fire; inside, Mirelle, small, pearls sewn on everything, blind eyes "
         "glowing teal, holding an ice staff, children huddled behind her."),
    shot("You're late. Only a little. I saw that too.",
         "Mirelle stepping out onto the frost, barefoot. Joins as a hero.", speaker="mirelle"),
    )

cin("water_warden", "Thalassa, Freed", "After Pearlhaven (Water 4). Thalassa joins.",
    shot("Under Pearlhaven we brought down the Tidal Leviathan, an eel of grey ice as long as the harbour. "
         "It broke apart, and Thalassa rose out of the water.",
         "The ice-eel collapsing; drowned bronze bells rising out of the water and ringing. Thalassa rising "
         "from the sea, sea-glass and current, the bells floating in her hair."),
    shot("I remember every ship that ever sailed this sea, and every child on it. I will remember what you "
         "did here.",
         "Thalassa looking down at the towers and heroes.", speaker="thalassa"),
    shot("The fire went out on the ice, and the sea froze over again. That night Mirelle looked into the "
         "ice for a long time. She said she had seen a death at the very end of the war.\n\nShe would not "
         "say whose.",
         "Mirelle alone on the shore with the ice staff, her blind eyes glowing, reflections in the ice of "
         "something we cannot make out. Behind her, Pearlhaven's harbour freezing over."),
    )

# ------------------------------------------------------------------------------- Sunscar Canyon
cin("earth_intro", "Sunscar Canyon", "Before the first stage of Sunscar Canyon (fought at night).",
    shot("Sunscar Canyon is red rock. The Stoneborn live in cities carved into its walls. Its Warden, "
         "Orrok, sleeps in the mountain at its head, under Grundhallow.",
         "Red rock canyon by torchlight, cliff cities in terraces, giant stone faces of old kings."),
    shot("Orrok had gone mad, and the canyon could not keep out the storm. Lightning in armour walked down "
         "the walls. Over it, on a bird of black cloud, rode the Herald Vholt Stormcrown: a Galeborn "
         "warchief, and Kaela's old teacher.",
         "Storm spirits in armour pouring down the walls. Above them, on a thunderbird of black cloud, an old "
         "warchief with a crown of lightning: Vholt."),
    shot("He taught me to ride. He taught me never to turn my back on a fight. If I have to kill him, I'll "
         "do it facing him.",
         "Kaela on Thunderclap at the canyon rim, watching the black bird circle.", speaker="kaela"),
    )

cin("earth_herald", "The Sky Herald", "After the Kharum Terraces (Earth 2). Gorrim Stonebeard joins.",
    shot("Over the Kharum Terraces, Kaela brought Vholt's bird down with her own lance. She was there when "
         "he hit the ground.",
         "The black thunderbird crashing on the terraces. Vholt crawling free. Kaela stands over him with "
         "her lance."),
    shot("Kaela... I went to the Rift because the Marshal asked me to. I'm sorry, girl. Finish it. Clean, "
         "the way I taught you.",
         "Vholt's face, the grey light flickering out of his eyes as he looks up.", speaker="vholt"),
    shot("Behind a fallen terrace we found what was left of the Canyon's shield-company. Gorrim Stonebeard "
         "was standing in front of them, with a stone door for a shield.",
         "Gorrim Stonebeard, short and wide, a carved stone door as a shield, iron rings in his beard, "
         "standing in front of exhausted soldiers."),
    shot("One iron ring in my beard for every friend I've buried. Thirty-one. Let's not make it thirty-two.",
         "Gorrim hefting the door-shield onto his back. Joins as a hero.", speaker="gorrim"),
    )

cin("earth_warden", "Orrok, Freed", "After Grundhallow (Earth 4). Orrok joins.",
    shot("Under Grundhallow the Mountain Titan fell, a giant of grey stone. The grey came off it like dust, "
         "and under it was Orrok.",
         "The Titan crashing down; grey lichen falling from its eyes; amber geode eyes opening. Orrok."),
    shot("...Thank you.", "Orrok, enormous, looking at the towers.", speaker="orrok", duration=4.0),
    shot("It was the first thing he had said in two thousand years. The storm left the canyon, and the "
         "Stoneborn buried their dead in the Deep Halls.",
         "The great stone doors of Grundhallow closing on the dead, torches along the hall."),
    shot("That's the last ring. Hear me say it. No more.",
         "Gorrim braiding one more iron ring into his beard.", speaker="gorrim"),
    )

# ------------------------------------------------------------------------------- the Hollow Rift
cin("void_intro", "The Hollow Rift", "Before the first stage of the Hollow Rift (fought at night).",
    shot("The last land was the Hollow Rift, where the war began. The Veilwalkers guard it. Their Warden, "
         "Nyxara, sleeps in the dark along its edge.",
         "The Hollow Rift at night: violet grass, floating stone steps, and the edge of the chasm."),
    shot("From the edge you can see the Black Gate, miles down, and the gap in it, and a grey line of "
         "soldiers still coming out.",
         "Looking down into the Rift: the Gate far below, the cart-wide gap, a thin grey column climbing the "
         "road cut into the wall."),
    shot("Nyxara had gone mad, and the Rift could not keep out the forest. Thorns grew over everything, and "
         "dead trees walked. Their Herald was Mother Briar, once the Deepwood's best healer.",
         "Black thorns choking the Veilwalker towns; a thicket-woman with grey flowers in her hair walking "
         "among them: Mother Briar."),
    shot("The Veilwalkers at Lamplight say some nights a white light moves along the bottom of the Rift. "
         "Slowly. Like someone walking with a lantern.",
         "Tamsin at the Lamplight waystation, looking down into the Rift. Far below, very small, a white "
         "light moving.",
         speaker="tamsin"),
    )

cin("void_herald", "The Thorn Herald", "After Vesperhold (Void 2). Corvin the Uncrowned joins.",
    shot("Mother Briar fell on the steps of Vesperhold, and the thorns that had grown through her went "
         "brown and crumbled.",
         "The thicket-woman falling apart on the floating steps, grey flowers wilting, black thorns crumbling."),
    shot("Tied in her thorns was my half-brother, Corvin. Six years ago he was found over a dead man, and I "
         "exiled him for murder. He had lived on the edge of the Rift ever since, watching the Gate.",
         "Corvin the Uncrowned cutting himself free with a black glass blade, hood back, silver hair, a scar "
         "through his eyebrow."),
    shot("Six years I told them it was the Marshal. Now they believe me.\n\nThe man I was exiled for "
         "killing saw Cassivane cut a piece off the Heartstone. That's why he died.",
         "Corvin standing, looking at the player. Joins as a hero.", speaker="corvin"),
    )

cin("void_warden", "Nyxara, Freed", "After Umbrael (Void 4). Nyxara joins.",
    shot("At Umbrael we fought the Hollow King, Nyxara's madness wearing an iron crown. When it broke, "
         "Nyxara stepped out of it with the crown in her hand.",
         "The Hollow King breaking into two shades; one dissolves, the other becomes Nyxara, tall, a starfield "
         "for a face, holding a broken iron crown."),
    shot("I fought it the whole time.\n\nAnd your Grey Lantern is alive. I hear him walking under my land, "
         "toward you.",
         "Nyxara looking down into the Rift, the stars in her face moving.", speaker="nyxara"),
    shot("All six Wardens were free, and every land was ours again.",
         "The six Wardens' lights, one in each land, seen on the painted map of the Ring."),
    )

# ------------------------------------------------------------------------- the spine (stage-count beats)
cin("regents_counsel", "The Refugee Road", "After 8 stages won (after Aurath is freed). Solenne and the Regent.",
    shot("People who fled before we reached their towns came up the roads to Solenne. We gave them the "
         "squares, then the gardens, then the halls of my palace.",
         "Solenne's streets packed with refugees from different lands, tents in the white squares, the "
         "Sunstone glowing gold above."),
    shot("The Lord Marshal Cassivane commanded our armies. He met every cart at the gate himself. Six years "
         "after he lost his daughter, he still wore her picture in a gold locket.",
         "Cassivane Dral at the gate, red cloak, helping an old woman off a cart, smiling. Fennick beside him "
         "grumbling over a tower plan."),
    shot("You are winning, Spirewright. Every life we lose out there will be paid back. I promise you that.",
         "Cassivane looking straight at the player, warm, fatherly. As he turns away, his thumb runs over the "
         "gold locket.", speaker="cassivane"),
    shot("Six years before, my half-brother Corvin had called him a traitor. Then Corvin was found over a "
         "dead man, and I exiled him. I believed Cassivane.",
         "Night: Cassivane alone on the Spire of Aurel, looking east toward the Rift. The locket open in his "
         "hand. A girl's portrait inside."),
    )

cin("night_of_falling_stars", "The Night of Falling Stars",
    "After 12 stages won (after Elowen is freed). The midpoint disaster, about 2:30.",
    shot("We came home to Solenne for one night. Three lands were free. We thought the worst was over.",
         "Solenne at dusk, the Sunstone glowing over a city packed with refugees. Lanterns everywhere. Quiet."),
    shot("At midnight, the east gate opened from the inside. Our own soldiers opened it. Their eyes were "
         "grey and empty.",
         "The great east gate swinging open. Soldiers in Lanternguard blue standing aside... their eyes empty "
         "and grey."),
    shot("Cassivane had been emptying our soldiers for months, the way the Heralds were emptied, and keeping "
         "them in the barracks under our own colours. Two thousand of them.",
         "Hollowed soldiers fighting in the streets; refugees running; Lanternguard fighting their own."),
    shot("Fennick held the gatehouse with half-built towers and a hammer.",
         "Old Fennick in the gatehouse, spectacles on, firing half-built towers that crackle with unstable "
         "elements."),
    shot("Don't stand there, Spirewright! Get to the palace and get the Queen out. I've got the gate.",
         "Fennick shouting over his shoulder, then turning back to the gate as it starts to fall.",
         speaker="fennick"),
    shot("The gatehouse came down on him. He held the gate until it did.",
         "The gatehouse collapsing in a cloud of dust and coloured sparks. Silence."),
    shot("Cassivane climbed the Spire of Aurel to the Sunstone. Its light burned the things of the dark, and "
         "he had become one of them. He broke it.",
         "Cassivane at the top of the Spire, his red armour blackening, smashing the huge lens. Its pieces "
         "fall across the city like burning stars."),
    shot("Then he came down for the Heartstone, the key to the Black Gate. Six years ago he had chipped a "
         "sliver off it, and that sliver opened the Gate. Now he wanted the rest.",
         "Cassivane striding into the Hall of the Ring, a six-coloured crystal sliver glowing in his fist."),
    shot("I got there first. I took the Heartstone and ran. The pieces of the Sunstone were falling all "
         "around me, and their light was the last thing I ever saw.",
         "Ysolde running from the hall with the Heartstone in her arms, looking up as the falling light hits "
         "her face; white-out."),
    shot("Give me the stone, Ysolde! He has my daughter. He gives her back when the Gate is open!",
         "Cassivane in the smoke of the courtyard, hand out, grey creeping into his eyes. Tamsin dragging the "
         "blind Queen into cover, the Heartstone clutched between them.", speaker="cassivane"),
    shot("Tamsin got me out. Cassivane gathered up the pieces of the Sunstone and fled east. One piece he "
         "never found. It had fallen all the way to the Rift.",
         "Cassivane leaving through the broken gate with the glowing shards in a net. Far to the east, one "
         "small white shard falling into the Rift."),
    shot("With the Sunstone broken, nothing held the dark down in the Rift any more. Before morning it came "
         "up and spread across the sky. The sun did not rise.\n\nThat was the start of the Long Night.",
         "A wall of darkness rising out of the eastern horizon and rolling over the sky. Dawn hour: a black "
         "sky over Solenne. Only torches. Refugees looking up."),
    )

cin("long_night", "There Was No Dawn", "After 18 stages won (after the Kharum Terraces). The war in the dark.",
    shot("By then it had been dark for months. Crops failed. Solenne lived by torchlight on rationed bread.",
         "Solenne under a black sky, lit by torches and the Heartstone's faint six-coloured pulse. A bread "
         "line in the square."),
    shot("I ruled by voice. I learned people by their footsteps.",
         "Ysolde on her throne, blindfold of black and gold, Fennick's brass measuring rod across her knees. "
         "Heroes standing in the dim hall."),
    shot("Fennick wrote everything down. Which towers work where, and why. I'll read it to you, "
         "Spirewright. Badly.",
         "Tamsin at a war table under a lantern, reading from Fennick's battered notebook with his "
         "spectacles in her hand.", speaker="tamsin"),
    shot("The dark came from the Rift, and the further east we went, the thicker it got. East was where we "
         "were going.",
         "A night road lit by a line of lanterns: the army, carts, towers glowing in six colours along the "
         "way, heading east."),
    )

# ------------------------------------------------------------------------------- the Convergence
cin("convergence_intro", "The Convergence", "Before Shattered Crossroads (Converge 1).",
    shot("With all six Wardens awake, their oath held Vael-Orrun again, and the gap in the Gate could get "
         "no wider. Only the whole Heartstone could break the oath now.",
         "A map of the Ring: six lands lit again, the Rift in the east, the Heartstone glowing at Solenne in "
         "the centre."),
    shot("So everything he had left came out of the Rift at once and marched west for Solenne, with "
         "Cassivane at its head. We raced it home.",
         "A grey tide pouring out of the Rift and across the plains toward the centre of the map; the "
         "Concord's army on a parallel road, ahead of it."),
    shot("The Wardens walked with us.",
         "Six vast figures walking across the plains toward the city, each glowing its own colour: Ignar, "
         "Aurath, Elowen, Thalassa, Orrok, Nyxara. Refugees stop to watch them pass."),
    shot("Queen of Solenne. When this is over, I will tell you what we did at Vael.\n\nNot before.",
         "Thalassa bending low to the blind Queen at Solenne's gate; the other Wardens look away.",
         speaker="thalassa"),
    shot("Cassivane's army was camped at Crossmere, the town where every road on the Ring meets, a day east "
         "of Solenne. We had to go through him.",
         "Crossmere, a crossroads town at night, ringed by a grey war camp. Cassivane's standard: a red field, "
         "now burned black."),
    )

cin("crossroads", "The Ashen Regent", "After Shattered Crossroads (Converge 1). Crossmere is saved. Ilyra joins.",
    shot("We held Crossmere. Cassivane fought like the hero he used to be, then pulled back with what was "
         "left of his army.",
         "Cassivane, armour burned like paper, Heartstone shards growing from his shoulders, wounded, falling "
         "back through his burning camp."),
    shot("Yes. I opened the Gate. He had my daughter. He gave her back to me empty.\n\nShe will be whole "
         "when he is free.",
         "Cassivane stopping beside a cage of grey light, his hand on its bars, looking back at us with grey "
         "eyes.", speaker="cassivane"),
    shot("He left her behind. In the cage was Ilyra, six years gone. She was alive, but she did not know "
         "her own name.",
         "Corvin cutting open the cage. Inside, thin and wide-eyed, Ilyra, black veins on her arms, a broken "
         "astrolabe on a chain."),
    shot("Corvin sat with her all night. By morning she knew his name. By the next, she knew her own.",
         "Dawn-less morning by a campfire; Corvin and Ilyra, her eyes clearer."),
    shot("Behind the Gate I heard two voices. One of them wept. The other never did. My father only ever "
         "heard the first.\n\nLet me help you stop him.",
         "Ilyra standing, lightning flickering along the black veins. Joins as a hero.", speaker="ilyra"),
    )

cin("lumen_gate", "The Lumen Gate", "After Prism Wastes (Converge 2). Seraphel joins.",
    shot("Prism Wastes is the glass plain in front of Solenne. Cassivane's whole army came across it, and "
         "we fell back to the walls.",
         "Glass plains under a black sky, shattered into six colours. The army of the Concord falling back "
         "toward the city walls."),
    shot("That night the Lumen Gate fell, the outer wall of Solenne. It was the only wall we lost in the "
         "whole war.",
         "The outermost wall collapsing in dust."),
    shot("Behind it, Seraphel drew her sword. She was the last knight of the Sunstone, and its light had "
         "kept her alive for a thousand years. Since it broke, she had been dying.",
         "Through the dust: Seraphel, tall, in white-gold plate with six dimming colours, drawing a greatsword "
         "of Sunstone glass that glows like dawn."),
    shot("I have a few days left. Let me spend them on your wall.",
         "Seraphel on the second wall beside the Queen, sword planted. Joins as a hero.", speaker="seraphel"),
    )

cin("capital_prelude", "The Crowned Heart", "Before Heart of the Ring (Converge 3), the capital.",
    shot("Every land we had freed sent its fighters to Solenne: Emberfolk smiths, Galeborn riders, Deepwood "
         "archers, Tidefolk, Stoneborn and Veilwalkers.",
         "Wide shot of Solenne crammed with every people of the Ring, each lighting a small light in its "
         "own colour. The city glows like a lantern in the black."),
    shot("Cassivane came for the Heartstone himself. He had fused the pieces of the Sunstone into his own "
         "body. We called what he had become the Sundered Heart.",
         "On the dark plain, in the centre of the horde, a vast floating knot of shattered light with a man's "
         "shape inside: the Sundered Heart."),
    shot("If he takes the Heartstone, the Gate opens all the way and Vael-Orrun walks out. So he does not "
         "take it.\n\nHold this wall.",
         "Ysolde on the inner wall, blindfolded, Tamsin at her arm, the heroes along the battlements.",
         speaker="ysolde"),
    shot("...There's a light on the east road. Does nobody else see it?",
         "Ysolde turning her blind face east. Tamsin looks: nothing but darkness.", speaker="ysolde"),
    )

cin("dawn", "The White Lantern", "During Heart of the Ring, at wave 17. Oswin returns; dawn breaks.",
    shot("The Sundered Heart had reached the inner wall when a white light came up the east road.",
         "Battle at the inner wall. Far down the east road, a small white light."),
    shot("It was Oswin. He had fallen through the Gate at the start of the war and walked back under the "
         "world, through the Hollow, and climbed up out of the Rift. The Unbound would not go near his "
         "lantern.",
         "A tall figure in glowing white robes walking up the east road through the horde; grey-eyed "
         "Unbound shrink back and fade as he passes."),
    shot("Hello, Ysolde. I'm sorry I'm late. I found this at the bottom of the Rift. I think it's yours.",
         "Oswin, white-haired, standing tall at the foot of the wall below the Queen, holding up the last "
         "white shard of the Sunstone.", speaker="oswin"),
    shot("He climbed the Spire, set the last piece in the Sunstone's frame, and lit it with his lantern.\n\n"
         "The dark sank back into the Rift, and the sun came up over Solenne for the first time in months.",
         "Oswin raising the lantern. Light pours up into the Sunstone frame above the city; it blazes. Real "
         "dawn floods the battlefield. (Game lighting: night to dawn.) Oswin joins as a hero."),
    shot("The Unbound around the walls burned in it. Only the Sundered Heart kept coming.",
         "Grey shapes flaring and falling in the sunlight; the Sundered Heart pushing on through the glare."),
    )

cin("heart_falls", "Dawn", "After Heart of the Ring (Converge 3) is won.",
    shot("When the Sundered Heart broke, Cassivane was inside it, burned grey, holding his locket.",
         "The knot of shards collapsing in dawn light. In the middle, Cassivane on his knees, ash, locket in "
         "his hands."),
    shot("Father. Look at me. I'm whole. I got better on my own.\n\nHe lied to you.",
         "Ilyra kneeling in front of him, taking his hands.", speaker="ilyra"),
    shot("He looked at her for a long time. He put the locket in her hand. Then he died.",
         "Cassivane's face, the grey leaving his eyes. He presses the locket into her hand and crumbles into "
         "ash in the dawn wind."),
    shot("I felt the sun on my face. I could not see it, but I felt it.\n\nSolenne stood.",
         "Ysolde on the wall, face lifted to the light, crying, smiling. The six peoples cheering in the "
         "streets of a city lit gold."),
    shot("The Gate is still open a cart's width, and he is still behind it. While it's open, he will keep "
         "sending armies through. So we go down there and end it.",
         "Oswin, Corvin, Tamsin and the Wardens around the Heartstone. Oswin looking east toward the Rift.",
         speaker="oswin"),
    shot("For the first time in the war, we did not wait for him to come to us.\n\nWe marched east, to the "
         "Rift.",
         "The army of the Concord marching out of Solenne's gates in dawn light, every hero and Warden at its "
         "head, toward the Rift."),
    )

cin("solenne_falls", "Solenne Falls", "If Heart of the Ring is lost. Then retry.",
    shot("The inner wall broke, and Cassivane took the Heartstone.\n\nNo. That is not how it happened.\n\n"
         "Again.",
         "The inner wall cracking, the Heartstone's light flickering; then the image freezes and runs "
         "backward, as if Ysolde is refusing the memory."),
    )

# ------------------------------------------------------------------------------- the final level
cin("assault_intro", "Through the Gate", "Before the final level (40 waves under Nhal Vorath).",
    shot("A road is cut into the wall of the Rift. It took us a day to walk down it. At the bottom we went "
         "through the gap in the Black Gate one at a time, the way his armies had come out.",
         "The army winding down the Rift road in a long line of lanterns; at the bottom, soldiers filing "
         "through the cart-wide gap in the colossal Gate."),
    shot("Behind the Gate is the Hollow, a cavern under the world so big its roof is lost in the dark. The "
         "only light is grey fire. A day's march in stood his fortress, Nhal Vorath, built from the ruins of "
         "his old city, which sank with him.",
         "The Hollow: a stone sky, grey fires, and on a broken plain a vast black fortress built of ancient "
         "ruined walls, towers and gates."),
    shot("His army was still too big to storm. So we dug in in front of his walls, built our towers, and "
         "let it come to us.",
         "The Concord's camp on the broken ground before the fortress; Spirewright towers going up."),
    shot("You built your city on my city, and you lock my door with my own crown.\n\nCome in, then.",
         "The fortress gates; a huge shape in the dark above them. Every colour on screen drains to grey for "
         "a moment.", speaker="vael_orrun"),
    shot("For once we're not holding a road, Spirewright. We're on his.",
         "Tamsin, lantern-pole raised, at the head of the camp.", speaker="tamsin"),
    )

cin("the_high_king", "The High King", "Final level, wave 39: Vael-Orrun comes out himself.",
    shot("When his army was spent, he came out himself.",
         "The fortress gates opening. Vael-Orrun walking out: huge, bare, dark hard-muscled hide, the molten "
         "core burning behind his ribs."),
    shot("Six of you. Always six. Ask them what they did at my table.",
         "Vael-Orrun turning toward the six Wardens.", speaker="vael_orrun"),
    shot("None of the Wardens answered him.",
         "The six Wardens, silent. Thalassa is the only one who meets his eyes."),
    )

cin("the_turning", "The Turning", "Final level, wave 40: he has fled into the fortress, and we attack it.",
    shot("We beat him three times, and the third time he broke and ran back into his fortress. Now it was "
         "our turn. We left the towers to hold the camp and sent everyone we had at his gate.",
         "Vael-Orrun, half beast, fleeing through the fortress gate. The heroes and the Concord's troops "
         "forming up in front of the towers."),
    shot("Gates are my trade. Let me.",
         "Brannoc walking out in front of the army toward the fortress gate, hammer glowing.", speaker="brannoc"),
    )

cin("the_truth", "The Truth", "After the fortress falls (end of the final level). About 2 minutes.",
    shot("Brannoc broke the outer gate. Seraphel held the inner gate open with her back until the last of "
         "us were through. Then her light went out.",
         "Seraphel in the inner gate, armour drained of colour, sword blazing, holding the doors apart as the "
         "army runs past her. Her light goes out."),
    shot("Tell Ysolde I saw one more dawn. That was all I wanted.", "Seraphel, smiling, fading.",
         speaker="seraphel"),
    shot("We found him in his ruined throne hall, on his knees. The monster's shape was cracking off him, "
         "and there was a tired man inside it.",
         "The throne hall in ruins. Vael-Orrun on his knees; the monster shape cracks, and a man in grey is "
         "inside it."),
    shot("I gave away my forgetting, so I remember everything. You should know what we did.",
         "The six Wardens standing round him. Thalassa steps forward.", speaker="thalassa"),
    shot("He kept the peace between us for forty years. We feared him, and we wanted his gold.",
         "A painted memory: the Feast of the Crossroads. A kind king in grey, his wife and small son, six "
         "crowned guests, all smiling.", speaker="thalassa"),
    shot("They came to his feast as friends. At midnight they opened his gates. His city burned, and his "
         "wife and son burned with it.\n\nThe songs call it a victory. The Wardens call it the Night of Six "
         "Knives.",
         "The painting catches fire: the city of Vael burning at night, soldiers of six colours in the gates; "
         "the king on his knees in the ashes of the feast hall, holding a ring."),
    shot("It was my fire.", "Ignar, his heart-light dim, head bowed.", speaker="ignar", duration=3.0),
    shot("You did this. Remember that you did this.", "Vael-Orrun looking up at the six.",
         speaker="vael_orrun"),
    shot("We remember.", "Thalassa, bells silent in her hair, the only Warden who can meet his eyes.",
         speaker="thalassa", duration=3.0),
    shot("That night a voice in the dark taught me how to make magic stop. I thought it was my own grief. "
         "It was never my own voice.\n\nIt is still listening.",
         "The grey going out of Vael-Orrun's eyes. He looks past the Wardens, at something behind the "
         "camera.", speaker="vael_orrun"),
    shot("Mirelle had seen a death at the end of the war. It was his.",
         "Mirelle at the edge of the hall, blind eyes glowing teal."),
    shot("Oswin pressed his lantern into the burning core in his chest. He turned to light, and the light "
         "went up out of the Hollow, home to Solenne, into the Heartstone that had been his crown.",
         "Oswin pressing the white lantern into the molten core behind Vael-Orrun's ribs. Vael-Orrun turns "
         "to white light, which rises through the stone sky."),
    shot("He wanted the middle of the world. So we gave it to him. Not as its king.\n\nAs its light.",
         "Solenne at dawn: a beam of white light coming down out of the sky into the Hall of the Ring, and "
         "the Heartstone blazing."),
    )

cin("epilogue", "The Seventh Colour", "After The Truth. Then the credits.",
    shot("We walked back up the Rift road. When the last of us was through, the six Wardens shut the Black "
         "Gate and sealed it with their oath. It has not opened since.",
         "The six Wardens at the foot of the Gate, pushing it shut; the gap closing with a boom that shakes "
         "the Rift."),
    shot("Every town we had held was still standing, and its people went home.",
         "Montage: Emberfolk at the forges of Kethra; Galeborn tents at Aurvanis; Pearlhaven's fleet coming "
         "home; Stoneborn opening Grundhallow; Veilwalkers relighting Lamplight; Sylvaine planting Elowen's "
         "seed in a Solenne garden."),
    shot("We buried Fennick under the east gate he held, and Seraphel beside the Sunstone.",
         "Tamsin, alive, sitting on the rebuilt east gate with Fennick's spectacles; Seraphel's glass sword "
         "set into the Sunstone's frame. Oswin, grey and old again, beside her."),
    shot("I am Ysolde, Queen of Solenne. I am old now, and I have never seen a dawn since.\n\nBut I have "
         "felt every one of them.",
         "Ysolde, older, grey hair, still blindfolded, on the walls of a rebuilt Solenne, sun on her face. "
         "Credits roll."),
    )

# The post-credits reveal (Part 2 tease). Only the Hush speaks: no narrator, almost no sound. It shows,
# without naming it, that it taught Vael-Orrun, used him to reach Cassivane, and came home inside his light.
cin("the_hush", "One Door", "Straight after the epilogue's credits.",
    shot("", "After the credits: the Hall of the Ring, rebuilt, empty, night. The Heartstone glows in six "
         "colours... then, faintly, a seventh. Ilyra, alone, leans in to look.", duration=5.0),
    shot("He was the first to listen.\n\nI taught him how a world goes quiet.",
         "Two thousand years ago: the vault under burning Vael. The young king, Vael-Orrun, kneels in the "
         "dark with his wife's ring in his fist, listening. Grey creeps into his eyes from the edges.",
         speaker="the_hush"),
    shot("The Regent bargained with a king.\n\nThe king was mine.",
         "Six years ago: Cassivane at the foot of the Black Gate, his ear to a crack in the stone, his face "
         "wet.", speaker="the_hush"),
    shot("I could never cross into your world.\n\nSo you carried me home.",
         "The beam of white light rising out of the Hollow toward Solenne, as at the end of The Truth; inside "
         "it, something with no colour at all.", speaker="the_hush"),
    shot("Your High King was never my enemy. He was my hand.\n\nSo were you.",
         "Ilyra, frozen in front of the Heartstone. Reflected in both her eyes, very small, something with no "
         "colour at all.", speaker="the_hush"),
    shot("", "Deep inside the seventh colour of the Heartstone, something with no colour at all opens, like "
         "an eye.", duration=4.0),
    shot("Seven crowns. One door.\n\nThank you.",
         "Black. No sound at all for a moment before the voice, and none after. Title card: TO BE CONTINUED.",
         speaker="the_hush"),
    )

# ------------------------------------------------------------------------------- when they play
STAGE_SCENES = {
    # stage_id: {"before": cinematic, "after": cinematic, "during": [{"wave": N, "cinematic": id}]}
    "ember_1": {"before": "ember_intro"}, "ember_2": {"after": "ember_herald"}, "ember_4": {"after": "ember_warden"},
    "storm_1": {"before": "storm_intro"}, "storm_2": {"after": "storm_herald"}, "storm_4": {"after": "storm_warden"},
    "nature_1": {"before": "nature_intro"}, "nature_2": {"after": "nature_herald"},
    "nature_4": {"after": "nature_warden"},
    "water_1": {"before": "water_intro"}, "water_2": {"after": "water_herald"}, "water_4": {"after": "water_warden"},
    "earth_1": {"before": "earth_intro"}, "earth_2": {"after": "earth_herald"}, "earth_4": {"after": "earth_warden"},
    "void_1": {"before": "void_intro"}, "void_2": {"after": "void_herald"}, "void_4": {"after": "void_warden"},
    "converge_1": {"before": "convergence_intro", "after": "crossroads"},
    "converge_2": {"after": "lumen_gate"},
    "converge_3": {"before": "capital_prelude", "during": [{"wave": 17, "cinematic": "dawn"}],
                   "after": "heart_falls", "lost": "solenne_falls"},
}

# Plot beats keyed to the number of stages won. The lands open in a fixed order (Ember, Storm, Nature,
# Water, Earth, Void), so these land after Aurath is freed, after Elowen is freed and after the Kharum Terraces.
# When a beat and a stage scene fall on the same win, the stage scene plays first.
BEATS = [
    {"id": "refugee_road", "cinematic": "regents_counsel", "after_stages_won": 8},
    {"id": "midpoint", "cinematic": "night_of_falling_stars", "after_stages_won": 12},
    {"id": "long_night", "cinematic": "long_night", "after_stages_won": 18},
]

# From this many stages won on, the land stages are fought at night (the Sunstone is broken).
NIGHT_FROM_STAGES_WON = 12

# Stage boss of the Heralds and the Regent (new enemies for the gameplay thread to add).
STAGE_BOSSES = {
    "ember_2": "saltmother", "storm_2": "gorrath", "nature_2": "pale_vesper", "water_2": "ashwick",
    "earth_2": "vholt", "void_2": "mother_briar", "converge_1": "ashen_regent",
}

# The town each stage defends. Winning the stage saves it (shown as "<town> is saved. <line>"). The one
# exception is the Lumen Gate, Solenne's outer wall, which falls in the story even when the stage is won.
LOST = {"converge_2"}
CITIES = {
    "ember_1": ("Kethra", "The sea stopped at the edge of town. Its forges never went out."),
    "ember_2": ("Brazier Hold", "The Saltmother is dead, and her cage is open."),
    "ember_3": ("Vitrea", "Not one glass tower cracked."),
    "ember_4": ("Pyrrhenhall", "Ignar is awake, and the sea is draining off the mountain."),
    "storm_1": ("Stonering Camp", "The standing stones still stand."),
    "storm_2": ("Highwind", "Gorrath is broken. Kaela Stormrider rides with us."),
    "storm_3": ("Tarrow's Rest", "The horses are safe in their pens."),
    "storm_4": ("Aurvanis", "Aurath is awake, and the sky is moving again."),
    "nature_1": ("Fernholt", "Its people are back in the branches."),
    "nature_2": ("Elderhollow", "The Pale Vesper is silent. Sylvaine Thornwhisper fights with us."),
    "nature_3": ("Thornwall", "The dead under its trees lie still again."),
    "nature_4": ("Sylvanmere", "Elowen is awake, and the Hollow is leaving the forest."),
    "water_1": ("Netmend", "The ice under it held."),
    "water_2": ("Reedhaven", "Ashwick is dead. Mirelle and forty children walked out of the ice."),
    "water_3": ("Glasswater", "The lake froze over again behind the last runner."),
    "water_4": ("Pearlhaven", "Thalassa is awake, and the sea is freezing over."),
    "earth_1": ("Dustmark", "The storm broke on its walls."),
    "earth_2": ("The Kharum Terraces", "Vholt is dead. Gorrim Stonebeard fights with us."),
    "earth_3": ("Mesa Kharn", "The lightning never reached the mesa."),
    "earth_4": ("Grundhallow", "Orrok is awake, and the storm is leaving the canyon."),
    "void_1": ("Lamplight", "Its lamps are still burning."),
    "void_2": ("Vesperhold", "Mother Briar is dead. Corvin is free."),
    "void_3": ("Twinmoor", "The thorns are dying back."),
    "void_4": ("Umbrael", "Nyxara is awake. All six Wardens are free."),
    "converge_1": ("Crossmere", "Cassivane has fallen back, and left his daughter behind."),
    "converge_2": ("The Lumen Gate", "Solenne's outer wall is down. The other five still stand."),
    "converge_3": ("Solenne", "The Heartstone is safe, and the sun is up."),
}

# ------------------------------------------------------------------------------- characters
# side: hero | ally | villain | herald | warden_boss | overlord. joins: when a hero joins.
CHARACTERS = [
    # heroes
    ("tamsin", "Tamsin Reed", "Captain of the Lanternguard", "hero", "", "start",
     "Solenne's toughest soldier, always the last one through the gate. She dragged the blind Queen clear "
     "on the Night of Falling Stars, and reads Fennick's notes to the Spirewright since he died."),
    ("brannoc", "Brannoc Emberhand", "Smith-Lord of the Reach", "hero", "fire", "after ember_2",
     "The giant smith who forged Solenne's gates. The Saltmother kept him in a salt cage for nine days to "
     "make him forge her chains, and he refused every day. His hammer never cools."),
    ("kaela", "Kaela Stormrider", "Marshal of the Steppe", "hero", "storm", "after storm_2",
     "War-leader of the Galeborn, who fought the Stone alone for eleven days. Lightning lance, and a grey "
     "stallion called Thunderclap. The Herald Vholt was her teacher."),
    ("sylvaine", "Sylvaine Thornwhisper", "Bow of the Deep", "hero", "nature", "after nature_2",
     "The Deepwood's best archer, three hundred years old. She held Elderhollow's root-doors alone until "
     "every child was out, and carries the last seed of the oldest tree."),
    ("mirelle", "Mirelle the Tide-Seer", "Seer of Frostmere", "hero", "water", "after water_2",
     "A blind young seer who reads the future in ice. She kept forty children alive inside a tower of ice. "
     "She has seen a death at the end of the war, and will not say whose."),
    ("gorrim", "Gorrim Stonebeard", "Shield of the Canyon", "hero", "earth", "after earth_2",
     "A Stoneborn shieldmaster with an iron ring in his beard for every friend he has buried. His shield is a "
     "carved stone door."),
    ("corvin", "Corvin the Uncrowned", "Ranger of the Rift", "hero", "void", "after void_2",
     "The Queen's half-brother. He accused Cassivane of treason, was framed for murder and exiled, and spent "
     "six years watching the Black Gate from the edge of the Rift."),
    ("ignar", "Ignar", "the Cinder Warden", "hero", "fire", "after ember_4",
     "The Warden of Fire, one of the six monarchs who sleep to hold the Black Gate shut. Driven mad as the "
     "Cinder Tyrant, freed under Pyrrhenhall. Black stone and a molten heart."),
    ("aurath", "Aurath", "of the Storms", "hero", "storm", "after storm_4",
     "The Warden of Storm, freed from the Thunderhead over Aurvanis. A rider of cloud and lightning who is "
     "never quite still."),
    ("elowen", "Elowen", "the Evergreen", "hero", "nature", "after nature_4",
     "The Warden of Nature, cut out of the Elder Broodmother at Sylvanmere. Very old, very tired, and still "
     "growing."),
    ("thalassa", "Thalassa", "of the Deep", "hero", "water", "after water_4",
     "The Warden of Water, freed from the Tidal Leviathan under Pearlhaven. She gave away her forgetting, so "
     "she remembers everything, including what the six did at Vael."),
    ("orrok", "Orrok", "the Mountain", "hero", "earth", "after earth_4",
     "The Warden of Earth, freed from the Mountain Titan under Grundhallow. A slow stone giant with trees on "
     "his shoulders, who had not spoken in two thousand years."),
    ("nyxara", "Nyxara", "of the Hollow", "hero", "void", "after void_4",
     "The Warden of Void, who fought the Hollow King's crown from the inside at Umbrael. She can hear what "
     "walks under her land."),
    ("ilyra", "Ilyra the Unbroken", "Daughter of the Regent", "hero", "void,storm", "after converge_1",
     "Cassivane's daughter. Six years ago she slipped into the Black Gate and was caught; she came back "
     "empty, and found herself again on her own once she was free of her father's cage."),
    ("seraphel", "Seraphel the Dawnblade", "Knight of the Sunstone", "hero", "all", "after converge_2",
     "The last knight of the Sunstone, kept alive by its light for a thousand years. Since it broke she has "
     "been dying, and she has one fight left."),
    ("oswin", "Oswin the White Lantern", "Master of the Order of the Spire", "hero", "all",
     "during converge_3",
     "Pushed the Black Gate back to a cart-wide gap at the start of the war and fell through it. He walked "
     "back under the world, found the last piece of the Sunstone at the bottom of the Rift, and relit it."),
    # allies
    ("ysolde", "Queen Ysolde", "Queen of Solenne, the narrator", "ally", "", "",
     "Ruler of the Concord. Blinded on the Night of Falling Stars while she ran with the Heartstone; she rules "
     "by voice and tells the story."),
    ("fennick", "Master Tobias Fennick", "Chief Tower-Wright", "ally", "", "",
     "The gruff old engineer who designed every tower and briefs the Spirewright. He died holding Solenne's "
     "east gate on the Night of Falling Stars."),
    # villains
    ("cassivane", "Cassivane Dral", "the Ashen Regent", "villain", "fire,void", "",
     "Lord Marshal of the Concord. He cut a sliver off the Heartstone and unlocked the Black Gate, because "
     "Vael-Orrun promised to give back his daughter."),
    ("saltmother", "Saltmother Ourra", "the Drowned Herald", "herald", "water", "",
     "Once the Tidefolk's high priestess, sent to the Rift by Cassivane and sent back empty. Walks inside a "
     "column of black seawater. Boss of Brazier Hold."),
    ("gorrath", "Gorrath the Quarried", "the Stone Herald", "herald", "earth", "",
     "A Stoneborn general who held the Kharum Pass for a month, sent back from the Rift with a stone for a "
     "heart. Breaks into walking boulders. Boss of Highwind."),
    ("pale_vesper", "The Pale Vesper", "the Hollow Herald", "herald", "void", "",
     "A Veilwalker singer who sang at funerals, and now sings the dead awake. Dying, she names the Marshal. "
     "Boss of Elderhollow."),
    ("ashwick", "Ashwick the Kindled", "the Flame Herald", "herald", "fire", "",
     "The Concord's youngest messenger, sent to the Rift with a letter under Cassivane's seal. An ever-burning "
     "boy who never stops running. Boss of Reedhaven."),
    ("vholt", "Vholt Stormcrown", "the Sky Herald", "herald", "storm", "",
     "Kaela's old teacher, riding a thunderbird of black cloud. Boss of the Kharum Terraces."),
    ("mother_briar", "Mother Briar", "the Thorn Herald", "herald", "nature", "",
     "The Deepwood's wisest healer, grown through with thorns. Boss of Vesperhold."),
    ("the_hush", "???", "", "secret", "", "",
     "Revealed only in the post-credits scene. The villain of Part 2. Keep hidden from every codex and menu."),
    ("vael_orrun", "Vael-Orrun", "the High King", "overlord", "", "",
     "King of Orrun, the middle kingdom, two thousand years ago. The songs call him a tyrant, beaten and shut "
     "behind the Black Gate. He wants his crown back: the Heartstone, the key to his prison."),
]

# Existing boss enemies (data/enemies) per character, and the ones the gameplay thread will add.
BOSS_ENEMY = {
    "ignar": "cinder_tyrant", "aurath": "thunderhead", "elowen": "broodmother", "thalassa": "leviathan",
    "orrok": "mountain_titan", "nyxara": "hollow_king", "cassivane": "sundered_heart",
    "saltmother": "saltmother", "gorrath": "gorrath", "pale_vesper": "pale_vesper", "ashwick": "ashwick",
    "vholt": "vholt", "mother_briar": "mother_briar", "vael_orrun": "vael_orrun",
}

# The final level under Nhal Vorath (40 waves, being rebuilt by the final-level thread):
# intro before wave 1; "waves" are scenes at the start of a wave (39: Vael-Orrun comes out himself,
# 40: the counter-attack); "truth" plays when the fortress falls, then the outro (epilogue and credits),
# then "post_credits". "movements" keeps the current three-phase assault playable until the rebuild lands.
ASSAULT = {
    "intro": "assault_intro",
    "waves": [
        {"wave": 39, "cinematic": "the_high_king"},
        {"wave": 40, "cinematic": "the_turning"},
    ],
    "movements": [
        {"name": "The Camp", "minutes": 10, "boss": "echo_heralds", "cinematic": ""},
        {"name": "The Outer Gate", "minutes": 10, "boss": "", "cinematic": ""},
        {"name": "The High King", "minutes": 10, "boss": "vael_orrun", "cinematic": "the_high_king"},
    ],
    "truth": "the_truth",
    "outro": "epilogue",
    "post_credits": "the_hush",
}


# ------------------------------------------------------------------------------- writers
def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def characters_json():
    out = []
    for cid, name, title, side, element, joins, blurb in CHARACTERS:
        out.append({"id": cid, "name": name, "title": title, "side": side, "element": element,
                    "joins": joins, "blurb": blurb, "boss_enemy": BOSS_ENEMY.get(cid, ""),
                    "hidden": side == "secret"})
    return out


def story_json():
    return {
        "prologue": "prologue",
        "beats": BEATS,
        "stage_scenes": STAGE_SCENES,
        "night_from_stages_won": NIGHT_FROM_STAGES_WON,
        "stage_bosses": STAGE_BOSSES,
        "cities": {sid: {"name": n, "fall_text": t, "saved": sid not in LOST, "capital": sid == "converge_3"}
                   for sid, (n, t) in CITIES.items()},
        "assault": ASSAULT,
    }


SPEAKERS = {c[0]: c[1] for c in CHARACTERS}
SPEAKERS["narrator"] = "Narrator (Ysolde)"


def screenplay():
    total = 0.0
    lines = ["# Scripts: the Opening and Every Cinematic", "",
             "Generated by `tools/story/story_content.py` (edit that file, then rerun it). Canon is in "
             "[bible.md](bible.md), looks in [characters.md](characters.md).", "",
             "Narration is read by the narrator (Queen Ysolde, deep calm female voice). Lines with another "
             "speaker are spoken by that character (or shown as subtitles if not voiced). A blank line inside "
             "a line is a dramatic pause. Durations are estimates at a slow narration pace.", ""]
    lines += ["## When each cinematic plays", "",
              "| Cinematic | Title | When |", "|---|---|---|"]
    for cid, c in CINEMATICS.items():
        lines.append(f"| `{cid}` | {c['title']} | {c['when']} |")
    lines += ["", "Beats keyed to stages won (the lands open in a fixed order): "
              + ", ".join(f"`{b['cinematic']}` after {b['after_stages_won']}" for b in BEATS)
              + f". Land stages are fought at night from {NIGHT_FROM_STAGES_WON} stages won on.", ""]
    for cid, c in CINEMATICS.items():
        secs = sum(s["duration"] for s in c["shots"])
        total += secs
        lines += ["---", "", f"## {c['title']} (`{cid}`)", "",
                  f"*{c['when']}* About {int(secs // 60)}:{int(secs % 60):02d}.", ""]
        for i, s in enumerate(c["shots"], 1):
            who = SPEAKERS.get(s["speaker"], s["speaker"])
            lines.append(f"**{i}. [{s['art_note']}]**")
            lines.append("")
            if s["text"]:
                text = s["text"].replace("\n\n", "  \n*(pause)*  \n")
                lines.append(f"> **{who.upper()}:** {text}")
                lines.append("")
    lines += ["---", "", "## The towns", "",
              "Shown after each stage win as \"<town> is saved. <line>\" (the Lumen Gate: \"has fallen\").", "",
              "| Stage | Town | Line |", "|---|---|---|"]
    for sid, (n, t) in CITIES.items():
        lines.append(f"| {sid} | {n} | {t} |")
    lines += ["", f"Total cinematic running time: about {int(total // 60)} minutes.", ""]
    return "\n".join(lines)


def main():
    root = os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if "--out" in sys.argv:
        root = sys.argv[sys.argv.index("--out") + 1]
    for cid, c in CINEMATICS.items():
        write_json(os.path.join(root, "data/story/cinematics", f"{cid}.json"),
                   {"id": cid, "title": c["title"], "shots": c["shots"]})
    write_json(os.path.join(root, "data/story/story.json"), story_json())
    write_json(os.path.join(root, "data/story/characters.json"), characters_json())
    os.makedirs(os.path.join(root, "docs/story"), exist_ok=True)
    with open(os.path.join(root, "docs/story/scripts.md"), "w", encoding="utf-8") as f:
        f.write(screenplay())
    # sanity checks
    used = {"prologue"} | {ASSAULT[k] for k in ("intro", "truth", "outro", "post_credits")}
    used |= {b["cinematic"] for b in BEATS}
    used |= {m["cinematic"] for m in ASSAULT["movements"] if m["cinematic"]}
    used |= {w["cinematic"] for w in ASSAULT["waves"]}
    for s in STAGE_SCENES.values():
        used |= {s.get(k) for k in ("before", "after", "lost") if s.get(k)}
        used |= {d["cinematic"] for d in s.get("during", [])}
    missing, unused = used - set(CINEMATICS), set(CINEMATICS) - used
    assert not missing, f"cinematics referenced but not written: {missing}"
    assert not unused, f"cinematics written but never played: {unused}"
    assert len(CITIES) == 27 and LOST <= set(CITIES)
    banned = re.compile(r"\b(crack in the sky|the Crack|Outer Hollow|beyond the stars|edge of the stars|"
                        r"road of the dead|Ledger|orcs?|elves|elf|dwarf|dwarves|Unwritten Star)\b", re.I)
    for cid, c in CINEMATICS.items():
        for i, s in enumerate(c["shots"], 1):
            hit = banned.search(s["text"] + " " + s["art_note"])
            assert not hit, f"{cid} shot {i} uses cut canon: {hit.group(0)!r}"
    speakers = {s["speaker"] for c in CINEMATICS.values() for s in c["shots"]}
    assert speakers <= set(SPEAKERS), f"unknown speakers: {speakers - set(SPEAKERS)}"
    print(f"wrote {len(CINEMATICS)} cinematics, {len(CHARACTERS)} characters, {len(CITIES)} cities to {root}")
    print("opening runs", round(sum(s["duration"] for s in CINEMATICS["prologue"]["shots"])), "seconds")


if __name__ == "__main__":
    main()
