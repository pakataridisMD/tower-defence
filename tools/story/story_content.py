#!/usr/bin/env python3
"""The campaign story: every cinematic, the Ledger of Fallen Cities and the cast, as data.

This file is the source of truth for story text. It writes:

    data/story/story.json                 when each cinematic plays, and the city lost after each stage
    data/story/cinematics/<id>.json       one file per cinematic: shots with narration and art notes
    data/story/characters.json            heroes, villains and the overlord
    docs/story/scripts.md                 the same scripts as a readable screenplay

Run:   python3 tools/story/story_content.py            (writes into the repo)
       python3 tools/story/story_content.py --out DIR  (writes data/ and docs/ under DIR instead)

The canon behind it (world, history, characters) is docs/story/bible.md. The looks of each character
are in docs/story/characters.md.

Writing rules for narration (the voice tool reads each shot's "text"):
- Short sentences. A blank line inside a text is a dramatic pause; "..." is a short hesitation.
- The narrator is Queen Ysolde, speaking after the war. She never says how it ends.
- Land scenes must read correctly in any campaign order, so they never mention day or night, or what
  happened in another land. Only the "beats" (keyed to the number of stages won) move the main plot.
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


# ----------------------------------------------------------------------------- the opening (~1:50)
cin("prologue", "The Last Lantern", "Before the first stage. The opening story video, 1 to 2 minutes.",
    shot("Before the Concord, before the Spire, before anyone kept count of the years... there were seven "
         "kingdoms.",
         "An old painted map coming out of darkness: six kingdoms in a ring, each under its own crown and "
         "colour (red, blue-white, green, teal, ochre, violet), and a seventh, colourless, in the middle."),
    shot("Each had its own magic. Forge-runes and storm-songs. Root-craft and tide-memory. Stone-oaths and "
         "star-charts. The seventh kingdom studied them all.\n\nAnd its king wanted all of it.",
         "Six crowned monarchs, each working their art: a forge-king hammering glowing runes, a horse-king "
         "singing lightning down, a green queen with a sprouting seed, a sea-queen reading ice, a "
         "mountain-king carving a rune into rock, a star-queen tracing a star-chart in the air. Then the middle kingdom's black-walled capital, and on its "
         "throne a king in black with a tall crown of six empty sockets."),
    shot("His name was Vael-Orrun, the High King. He learned to unmake magic. Where his armies marched, fire "
         "would not burn, and the wind lay down and died.",
         "The High King's armies crossing a burning land; behind them the flames freeze into grey glass, the "
         "grass stops moving, a river hangs still in mid-fall."),
    shot("The six hated one another. They stood together anyway, each beside its oldest enemy, and drove him "
         "out past the edge of the stars.\n\nWe call it the Ring.",
         "The six monarchs in a ring around the burning black city, hands joined, Fire across from Water, Storm "
         "across from Earth, Nature across from Void. The High King is flung out through the edge of a "
         "starfield into darkness."),
    shot("They could not kill him. So they locked the door with his own crown, and gave their lives to hold "
         "it. On the ruins of his city, we built Solenne.\n\nMy city. That is how the songs tell it.",
         "The crown shattering into a six-coloured crystal, the Heartstone. The six monarchs fading into a "
         "volcano, a storm, a tree, a sea, a mountain, a starless sky. Then dawn over Solenne: six white "
         "walls rising on black ruins, the Heartstone glowing at the centre, the golden Sunstone above."),
    shot("Six years ago, a man I loved like a father lost his daughter to the dark. The exiled king made him "
         "a promise.",
         "Night. Cassivane Dral, the Lord Marshal, alone on a balcony, holding a gold locket. Over his "
         "shoulder, in the stars, the faint crown-shaped gap. His face is in shadow."),
    shot("On the night of the Black Comet, the edge of the world split open.",
         "The Hollow Rift: violet grass, a ring of black pillars singing with stolen light. A black comet "
         "crosses the sky. The ground at the centre tears open into a crack full of nothing."),
    shot("Oswin, the Grey Lantern, held it for one night. At dawn, he walked to the edge... and gave it every "
         "light he had.",
         "Oswin, old, grey robes and hat, walks to the lip of the Crack with his lantern-staff raised. Behind "
         "him a line of Spirewright towers burning in six colours. Grey shapes crawling out of the Crack."),
    shot("The Crack closed to a hairline.\n\nAnd Oswin fell. His lantern went out.",
         "A blast of white light; the Crack slams almost shut. The ground under Oswin gives way. He falls into "
         "the dark, the lantern going out. Last frame: one tiny spark still drifting down after him."),
    shot("But a voice can pass through a hairline. It drove the six sleeping monarchs mad, and set each land "
         "against the one across from it.\n\nThe High King has come back for what was his.",
         "Six quick cuts: a volcano burning grey, a stormcloud gone solid black, a giant tree rotting, a "
         "frozen sea heaving, a mountain opening grey eyes, a starless sky with a crown. Then hordes of "
         "grey-eyed elemental spirits pouring across the land toward each other."),
    shot("We cannot win back the lands. We can only hold the roads until their people escape.\n\nEvery road we "
         "hold will cost us a city.",
         "A long line of refugees with carts on an ash road. Tamsin Reed with her lantern-pole waving them on. "
         "A gloved hand sets a glowing keystone into the foundation of a stone tower."),
    shot("I am Ysolde, Queen of a city that is running out of cities. And you, Spirewright, are the last of "
         "Oswin's apprentices.\n\nHold the road.",
         "Queen Ysolde on the white walls of Solenne, looking east toward smoke on the horizon. Title card."),
    )

# ------------------------------------------------------------------------------- the Ember Reach
cin("ember_intro", "The Ember Reach", "Before the first stage of the Ember Reach.",
    shot("The Ember Reach was the forge of the world. Its people sang to their fires, and the fires sang back.",
         "Black basalt terraces, lava rivers, glassworks glowing, red and brass banners. Emberfolk at anvils."),
    shot("Then the sea came up the mountain.",
         "A black tide of seawater and grey-eyed water spirits climbing the slopes, steam rising where it "
         "touches lava. Inside the tide, a tall column of water walks: the Saltmother, glimpsed."),
    shot("Fennick says fire burns and water slows. Fennick says a great many things.\n\nBurn them anyway.",
         "Tamsin Reed at the ash road, lantern-pole raised, Kethra's forges behind her. Carts moving west.",
         speaker="tamsin"),
    )

cin("ember_herald", "The Drowned Herald", "After Cinder Steps (Ember 2). Brannoc Emberhand joins.",
    shot("Saltmother Ourra once sang the tides into Frostmere's harbours. She came back from the Rift with "
         "nothing behind her eyes.",
         "The Saltmother's water-column bursting apart on the steps, fish and drowned lanterns scattering. Her "
         "empty grey eyes going dark."),
    shot("In her tide-cage, we found the Smith-Lord of the Reach. He had been swearing at her for nine days.",
         "A cage of crusted salt breaking open. Brannoc Emberhand, huge, bald, brass-ringed beard, staggering "
         "out and grabbing his hammer from the rubble; its head flares orange."),
    shot("Nine days, and not one decent insult in her whole drowned choir. Give me a wall to stand on, "
         "Spirewright.",
         "Brannoc on the wall of Brazier Hold, hammer on his shoulder, grinning. Joins as a hero.",
         speaker="brannoc"),
    )

cin("ember_warden", "Ignar, Freed", "After Throne of Cinders (Ember 4). Ignar joins.",
    shot("At the caldera, the Warden of Fire burned grey. When the Cinder Tyrant fell, the grey went out of "
         "it all at once.",
         "The Cinder Tyrant collapsing in the caldera, grey-white fire guttering. From the cracked basalt "
         "steps a tall black-stone figure with an orange molten heart: Ignar."),
    shot("I dreamed I was a cold thing. I am sorry, little ones. I will burn for you now.",
         "Ignar kneeling to Brannoc and the Emberfolk, his heart-light warming their faces.",
         speaker="ignar"),
    shot("But a land cannot be unburned. The caldera flooded that night, and the Emberfolk walked west, "
         "carrying their forge-fires in iron pots.",
         "Pyrrhenhall flooding with steam. A line of Emberfolk carrying glowing iron pots down the mountain "
         "toward the distant gold light of Solenne. Ignar walks with them, much taller than anyone."),
    )

# ------------------------------------------------------------------------------- the Thunder Steppe
cin("storm_intro", "The Thunder Steppe", "Before the first stage of the Thunder Steppe.",
    shot("On the Thunder Steppe the sky had never once been still. The Galeborn read the storms the way we "
         "read books.",
         "Endless high grass under a racing sky, standing stones, tent-cities, riders on grey horses."),
    shot("Now the clouds hung motionless, and the Stone came climbing up the plateau.",
         "A frozen, motionless sky. Armoured earth spirits climbing the plateau edge. At their head a giant "
         "Stoneborn general with a square hole in his chest: Gorrath."),
    )

cin("storm_herald", "The Stone Herald", "After Galeback Ridge (Storm 2). Kaela Stormrider joins.",
    shot("Gorrath the Quarried once held the Kharum Pass for a month. He carved out his own heart to hold "
         "the Rift for his new master.",
         "Gorrath breaking apart on the ridge into boulders that keep rolling, then stop. The carved stone "
         "heart in his chest cracks."),
    shot("Out of the ridge-dust rode the Marshal of the Steppe, who had been hunted across the plateau for "
         "eleven days, and had not once ridden in the direction of retreat.",
         "Kaela Stormrider bursting out of the dust on her grey stallion Thunderclap, lightning lance "
         "crackling, white war-paint across her face."),
    shot("Retreat? The Galeborn have no word for it. You will have to teach me one.",
         "Kaela reining in beside the player's towers, looking back at Highwind. Joins as a hero.",
         speaker="kaela"),
    )

cin("storm_warden", "Aurath, Freed", "After Eye of the Storm (Storm 4). Aurath joins.",
    shot("When the Thunderhead broke, the sky moved again for the first time in a season. The Galeborn wept "
         "in the rain.",
         "The black solid cloud shattering, frozen lightning falling like glass. Rain. Riders lifting their "
         "faces to it."),
    shot("We are moving. We are moving again. Who held the road? We will remember it.",
         "Aurath, a rider-shape of cloud and lightning, flickering, bowing over the towers.",
         speaker="aurath"),
    shot("The Galeborn packed the Sky-Moot onto ten thousand horses and rode for Solenne. Kaela rode last. "
         "That is how she learned the word.",
         "The great tent-city of Aurvanis being folded onto horses; a sea of riders heading toward the "
         "horizon. Kaela at the back, looking over her shoulder at the empty tent poles."),
    )

# ------------------------------------------------------------------------------- the Verdant Deep
cin("nature_intro", "The Verdant Deep", "Before the first stage of the Verdant Deep.",
    shot("The Verdant Deep was older than the Ring. Its people lived in trees the size of towers, and they "
         "forgot nothing.",
         "Giant trees, rope bridges, glow-moss lighting the roots like streets, Deepwood archers."),
    shot("Something hollow had crept in under the canopy. At night it sang.",
         "The glow-moss going dark row by row. Pale violet ghost-lights drifting between the roots, and a "
         "tall grey-veiled singer with her mouth open: the Pale Vesper."),
    )

cin("nature_herald", "The Hollow Herald", "After Rootway (Nature 2). Sylvaine Thornwhisper joins.",
    shot("The Pale Vesper once walked the dead to their rest. Now she sang them awake. Before the end, she "
         "sang something else.",
         "The Pale Vesper falling among the roots, her ghost-choir scattering like moths."),
    shot("The Marshal sent us to the Rift. The Marshal let us in. He is so... sorry.",
         "Close on the Vesper's face, the grey light leaving her eyes; for a moment she looks like herself.",
         speaker="pale_vesper"),
    shot("In the root-halls of Elderhollow we found the archer who had held them alone for nine days. "
         "Her bow had grown leaves.",
         "Sylvaine Thornwhisper standing amid a ring of fallen hollow things, a pale leafing longbow in her "
         "hands, moss cloak. She lowers the bow."),
    shot("Nine days. I counted every arrow. Show me where the next ones go.",
         "Sylvaine at the edge of a tower platform, arrow on the string. Joins as a hero.",
         speaker="sylvaine"),
    )

cin("nature_warden", "Elowen, Freed", "After Heart of the Grove (Nature 4). Elowen joins.",
    shot("The Elder Broodmother fell in the oldest tree in the world. What climbed out of the grey bark "
         "was a very old woman, and she was tired.",
         "The Broodmother collapsing; grey bark peeling away to reveal Elowen, bent, with white-blossom hair."),
    shot("The tree will live. It will not live long. Take its seeds, child. Take them somewhere with light.",
         "Elowen pressing a single glowing seed into Sylvaine's hand.", speaker="elowen"),
    shot("The people of Sylvanmere left by the highest branches. Sylvaine carried the seed to Solenne in "
         "her hand the whole way.",
         "Deepwood folk climbing up and away along the crown of the great tree; Sylvaine last, hand closed "
         "around a small green light."),
    )

# ------------------------------------------------------------------------------- Frostmere
cin("water_intro", "Frostmere", "Before the first stage of Frostmere.",
    shot("Frostmere was a frozen sea, and the Tidefolk kept every memory of the world in its ice.",
         "A vast frozen lake, stilt towns, pearl-white harbours, aurora overhead."),
    shot("Then the Flame came running across it, and the memories began to melt.",
         "Burning runners skating across the ice, leaving black water behind them. At their head a boy made "
         "of white embers with a messenger's satchel: Ashwick."),
    )

cin("water_herald", "The Flame Herald", "After Saltmarsh Bends (Water 2). Mirelle the Tide-Seer joins.",
    shot("Ashwick was the youngest runner ever to carry the Concord's messages. He was still running when "
         "he fell. I think he had forgotten where to.",
         "Ashwick stumbling in the reeds, embers scattering, the satchel falling open: old letters stamped "
         "with the Concord seal blow away."),
    shot("At the heart of the burning reeds stood a tower of ice that had not melted. Inside it waited a "
         "blind girl who said she had been expecting us.",
         "A tower of ice in a ring of fire; inside, Mirelle, small, pearls sewn on everything, blind eyes "
         "glowing teal, holding an ice staff with a fish frozen inside."),
    shot("You're late. Only a little. I saw that too.",
         "Mirelle stepping out onto the frost, barefoot. Joins as a hero.", speaker="mirelle"),
    )

cin("water_warden", "Thalassa, Freed", "After The Drowned Throne (Water 4). Thalassa joins.",
    shot("The Tidal Leviathan sank into the black water, and the bells in it rang true again.",
         "The ice-eel collapsing; drowned bronze bells rising out of the water and ringing. Thalassa rising "
         "from the lake, sea-glass and current, the bells floating in her hair."),
    shot("I remember all of it. Every ship. Every child. I will remember you, too.",
         "Thalassa looking down at the towers and heroes.", speaker="thalassa"),
    shot("That night, Mirelle looked into the ice for a long time. She said she had seen a death at the "
         "very end of the war.\n\nShe would not say whose.",
         "Mirelle alone on the shore with the ice staff, her blind eyes glowing, reflections in the ice of "
         "something we cannot make out. Behind her, the fleet of Pearlhaven sailing west, the harbour "
         "steaming."),
    )

# ------------------------------------------------------------------------------- Sunscar Canyon
cin("earth_intro", "Sunscar Canyon", "Before the first stage of Sunscar Canyon.",
    shot("The Stoneborn carve their cities into the canyon walls, and they carve the faces of their kings "
         "above the doors, so the kings can watch the road forever.",
         "Red rock canyon, cliff cities in terraces, giant stone faces of old kings."),
    shot("The Sky came down the canyon in armour, and the kings watched that, too.",
         "Storm spirits in armour pouring down the walls. Above them, on a thunderbird of black cloud, an old "
         "warchief with a crown of lightning: Vholt."),
    )

cin("earth_herald", "The Sky Herald", "After Canyon Switchbacks (Earth 2). Gorrim Stonebeard joins.",
    shot("Vholt Stormcrown taught Kaela to ride. When his thunderbird fell, she was the one waiting at the "
         "bottom of the canyon.",
         "The black thunderbird crashing on the terraces. Vholt crawling free. If Kaela is in the party, she "
         "stands over him with her lance; otherwise, a lone Galeborn rider."),
    shot("You always did hold the reins too tight. Go on, girl.",
         "Vholt's face, the grey light flickering out of his eyes as he looks up.", speaker="vholt"),
    shot("Behind a collapsed terrace we found what was left of the Canyon's shield-company. One of them was "
         "still standing, holding a door.",
         "Gorrim Stonebeard, short and wide, a carved stone door as a shield, iron rings in his beard, "
         "standing in front of exhausted soldiers."),
    shot("One ring for each friend I've buried. I've no room left on this beard, Spirewright. Let's keep it "
         "that way.",
         "Gorrim hefting the door-shield onto his back. Joins as a hero.", speaker="gorrim"),
    )

cin("earth_warden", "Orrok, Freed", "After Titan's Cradle (Earth 4). Orrok joins.",
    shot("When the Mountain Titan fell, the trees on its shoulders stopped burning.",
         "The Titan crashing down; grey lichen falling from its eyes; amber geode eyes opening. Orrok."),
    shot("...Thank you.", "Orrok, enormous, looking at the towers. It is the first thing he has said in a "
         "thousand years.", speaker="orrok", duration=4.0),
    shot("The Stoneborn sealed the Deep Halls of Grundhallow with their ancestors inside. Gorrim put a new "
         "ring in his beard, and did not speak of it.",
         "The great stone doors of Grundhallow closing. Gorrim braiding an iron ring into his beard."),
    )

# ------------------------------------------------------------------------------- the Hollow Rift
cin("void_intro", "The Hollow Rift", "Before the first stage of the Hollow Rift.",
    shot("We came back to the place where it began. No stars over the road. The grass glowed faintly, like "
         "the ghost of a bruise.",
         "The Hollow Rift: starless sky, violet grass, floating stone steps, and far off, the hairline Crack."),
    shot("At the Lamplight waystation, one lantern was burning. Nobody had lit it.",
         "An empty waystation, every lantern cold except one, burning a small white flame. Tamsin staring at it."),
    shot("Leave it. Whoever lit it might need it to find their way back.",
         "Tamsin turning away from the lantern, leaving it burning.", speaker="tamsin"),
    )

cin("void_herald", "The Thorn Herald", "After Fractured Steps (Void 2). Corvin the Uncrowned joins.",
    shot("Mother Briar was the wisest healer in the Deepwood. The thorns had grown all the way through her.",
         "The thicket-woman falling apart on the floating steps, grey flowers wilting, black thorns crumbling."),
    shot("In the thorns, bound and bleeding, was a man the Concord had exiled for murder. The Queen's own "
         "brother.",
         "Corvin the Uncrowned cutting himself free with a black glass blade full of stars, hood back, silver "
         "hair, a scar through his eyebrow."),
    shot("I told them it was the Marshal. Six years I told them. Nobody listened... Will you?",
         "Corvin standing, looking at the player. Joins as a hero.", speaker="corvin"),
    )

cin("void_warden", "Nyxara, Freed", "After Throne of the Hollow King (Void 4). Nyxara joins.",
    shot("The Hollow King split in two when he fell. One half was a crown. The other half was a woman made "
         "of stars, holding it in her hand.",
         "The Hollow King breaking into two shades; one dissolves, the other becomes Nyxara, tall, a starfield "
         "for a face, holding a broken iron crown."),
    shot("I fought it. All this time, I fought it from inside.\n\nAnd your Grey Lantern walks my road. He is "
         "not finished.",
         "Nyxara looking past the player, toward the Crack, the stars in her face moving.", speaker="nyxara"),
    shot("None of us understood her. Not yet.",
         "Umbrael's great telescope turning one last time to face the Crack, then toppling slowly."),
    )

# ------------------------------------------------------------------------- the spine (stage-count beats)
cin("regents_counsel", "The Refugee Road", "After 6 stages won. Solenne fills with refugees; the Regent.",
    shot("Every day more of them came up the roads to Solenne. We gave them the gardens, then the squares, "
         "then the halls of the palace.",
         "Solenne's streets packed with refugees from different lands, tents in the white squares, the "
         "Sunstone glowing gold above."),
    shot("The Lord Marshal found room for every one of them. He was always the first at the gates, and the "
         "last to leave.",
         "Cassivane Dral at the gate, red cloak, helping an old woman off a cart, smiling. Fennick beside him "
         "grumbling over a tower plan."),
    shot("Hold a little longer, Spirewright. Every city you give up is a city that will be paid back. I "
         "promise you that.",
         "Cassivane looking straight at the player, warm, fatherly. As he turns away, his thumb runs over the "
         "gold locket.", speaker="cassivane"),
    shot("I remember thinking how kind that was.",
         "Night: Cassivane alone on the Spire of Aurel, looking east toward the Rift. The locket open in his "
         "hand. A girl's portrait inside."),
    )

cin("night_of_falling_stars", "The Night of Falling Stars",
    "After 12 stages won. The midpoint disaster, about 2 minutes.",
    shot("We had lost twelve cities by then. Solenne was still bright. We thought that meant something.",
         "Solenne at dusk, the Sunstone glowing over a city packed with refugees. Lanterns everywhere. Quiet."),
    shot("At midnight, the Dawn Gate opened from the inside.",
         "The great east gate swinging open. Soldiers in Lanternguard blue standing aside... their eyes empty "
         "and grey. Behind the gate, the Unbound pour in."),
    shot("They were soldiers we had fed and armed. He had been keeping them in our own barracks, under our "
         "own colours.",
         "Hollowed soldiers fighting in the streets; refugees running; Lanternguard fighting their own."),
    shot("Fennick held the gate. He had a handful of half-built towers, and a hammer, and a temper.",
         "Old Fennick in the gatehouse, spectacles on, firing half-built towers that crackle with unstable "
         "elements. Brannoc forging the outer bars shut with his hammer if he is with us."),
    shot("Spirewright! Fire burns, water slows... and you place them where I tell you.\n\nGo. Get her out.",
         "Fennick shouting over his shoulder, then turning back to the gate as it starts to fall.",
         speaker="fennick"),
    shot("The gatehouse came down on him. He did not let go of the gate until it did.",
         "The gatehouse collapsing in a cloud of dust and coloured sparks. Silence."),
    shot("Above it all, on the Spire of Aurel, the Lord Marshal raised a blade made from a piece of our "
         "Heartstone...",
         "Cassivane at the top of the Spire, his red armour starting to blacken, holding a crystal blade "
         "glowing six colours. The Sunstone lens huge above him."),
    shot("...and he broke the sun.",
         "The Sunstone shattering. Its pieces fall across the city like burning stars."),
    shot("The light fell on me as I ran. It was the last thing I ever saw.",
         "Ysolde in the palace courtyard, looking up as the light falls on her face; white-out. Tamsin "
         "dragging her into cover."),
    shot("There is a world without death, Ysolde. I am going to bring her home. I am going to bring all of "
         "them home.",
         "Cassivane, ash drifting from his armour, stepping through a rip of darkness at the top of the "
         "Spire, carrying the Sunstone's shards in a net of grey light.", speaker="cassivane"),
    shot("Not all of the shards went with him. One of them fell east, and did not land. Nobody saw it but "
         "me... and I did not know what I had seen.",
         "Over the dark city, one falling shard of white light drifts sideways, east, toward the distant "
         "Rift, and keeps going."),
    shot("When the sun should have risen, it did not.\n\nThat was the beginning of the Long Night.",
         "Dawn hour. A black sky over Solenne. Only torches. Refugees looking up."),
    )

cin("long_night", "There Was No Dawn", "After 18 stages won. The war in the dark.",
    shot("There was no dawn. There has not been one since.",
         "Solenne under a black sky, lit by torches and the Heartstone's faint six-coloured pulse."),
    shot("I hold court by voice now. I have learned which footsteps are good news.",
         "Ysolde on her throne, blindfold of black and gold, Fennick's brass measuring rod across her knees. "
         "Heroes standing in the dim hall."),
    shot("He kept notes. Pages and pages of them. Fire burns, water slows. I'll read them to you, "
         "Spirewright. Badly.",
         "Tamsin at a war table under a lantern, reading from Fennick's battered notebook with his "
         "spectacles in her hand.", speaker="tamsin"),
    shot("Out on the roads, in the dark, we kept losing cities. And we kept saving their people.\n\nIt was "
         "the only thing we were still good at.",
         "A night road lit by a line of lanterns: refugees, carts, Lanternguard, towers glowing in six colours "
         "along the way."),
    )

# ------------------------------------------------------------------------------- the Convergence
cin("convergence_intro", "The Convergence", "Before Shattered Crossroads (Converge 1).",
    shot("Six lands were gone. Every Warden was free, and every horde that was left turned toward the "
         "Heartland at once.",
         "A map of the Ring: six lands dark, grey tides converging from every side on the centre."),
    shot("So the Wardens walked to Solenne.",
         "Six vast figures walking across the plains toward the city, each glowing its own colour: Ignar, "
         "Aurath, Elowen, Thalassa, Orrok, Nyxara. Refugees stop to watch them pass."),
    shot("We will hold your walls, little Queen. But before we do, you should know whose walls they are.",
         "The six Wardens standing in a ring around the outer walls of Solenne, the Heartstone pulsing. Ignar "
         "kneels to the blind Queen.", speaker="ignar"),
    shot("I gave away my forgetting. So I remember. Vael-Orrun kept the peace between us for forty years. We "
         "feared his alchemy, and we wanted his gold.",
         "Flashback, painted like an old fresco: a young, kind-faced king in grey at a long feast table "
         "between six crowned monarchs, his Tidefolk queen and small son beside him. Everyone is smiling.",
         speaker="thalassa"),
    shot("They came to his feast as friends. At midnight they opened his gates. His city burned, and his "
         "wife and his son burned with it.\n\nThe songs call it the Siege of Vael. The Wardens call it the "
         "Night of Six Knives.",
         "The fresco catches fire: the black city of Vael burning at night, soldiers of six colours in the "
         "gates; the king on his knees in the ashes of the feast hall, holding a ring."),
    shot("He did not begin as a tyrant. We made him one. And something was waiting in the dark to finish "
         "the work.",
         "Nyxara, the stars in her face dim, turning away. Behind her, deep in the stars, a patch of sky with "
         "no stars in it at all.", speaker="nyxara"),
    shot("The songs had lied for two thousand years. It did not change what we had to do.\n\nIt only "
         "changed how it felt.",
         "Ysolde alone in the Hall of the Ring, her hand on the Heartstone, which is warm, like a crown just "
         "taken off."),
    shot("The Lord Marshal's army was camped at Crossmere, where every road on the Ring meets. That was "
         "where we went to meet him.",
         "Crossmere, a crossroads town at night, ringed by a grey war camp. Cassivane's standard: a red field, "
         "now burned black."),
    )

cin("crossroads", "The Ashen Regent", "After Shattered Crossroads (Converge 1). Ilyra joins.",
    shot("He fought like the hero he had been. And when it was done, he did not run. He walked away, the "
         "way a man walks out of a room he is finished with.",
         "Cassivane, armour burned like paper, Heartstone shards growing from his shoulders, wounded, walking "
         "into a fold of darkness."),
    shot("Spirewright. You have cost me a great deal of time.\n\nIt does not matter. At the Heart, I will "
         "have all the time there is.",
         "Cassivane looking back once, grey eyes, locket in hand.", speaker="cassivane"),
    shot("In his camp we found a cage of grey light, and in it, a girl with white hair who had been gone "
         "for six years.",
         "Corvin cutting open the cage. Inside, thin and wide-eyed, Ilyra, black veins on her arms, a broken "
         "astrolabe on a chain."),
    shot("He didn't come to save me. He came to keep me. Let me help you stop him... I'm the only one he "
         "might stop for.",
         "Ilyra standing, lightning flickering along the black veins. Joins as a hero.", speaker="ilyra"),
    )

cin("lumen_gate", "The Lumen Gate", "After Prism Wastes (Converge 2). Seraphel joins.",
    shot("Prism Wastes was the last open ground before Solenne. When we left it, there was nowhere left to "
         "go back to.",
         "Glass plains under a black sky, shattered into six colours. The army of the Concord falling back "
         "toward the city walls."),
    shot("The Lumen Gate, the first of our six walls, fell that night. Behind it, a knight who should have "
         "died nine hundred years ago drew her sword.",
         "The outermost wall collapsing. Through the dust: Seraphel, tall, in white-gold plate with six "
         "dimming colours, drawing a greatsword of Sunstone glass that glows like dawn."),
    shot("I swore myself to the Sunstone. It is broken, and I am dying with it. Let me spend what is left "
         "where it counts.",
         "Seraphel on the second wall beside the Queen, sword planted. Joins as a hero.", speaker="seraphel"),
    )

cin("capital_prelude", "The Crowned Heart", "Before Heart of the Ring (Converge 3), the capital.",
    shot("Every survivor of every city was inside Solenne now. The Emberfolk with their iron pots of fire. "
         "The Galeborn and their horses. The Deepwood with their seed. Pearlhaven's children. The Stoneborn. "
         "The Veilwalkers.",
         "Wide shot of Solenne crammed with every people of the Ring, each lighting a small light in its "
         "own colour. The city glows like a lantern in the black."),
    shot("We had no more cities to give.",
         "Ysolde climbing the inner wall, Tamsin at her arm, the heroes along the battlements."),
    shot("For twenty-six cities we bought time with stone. There is no more stone. There is only us.\n\n"
         "Hold this wall, and nobody has to run again.",
         "Ysolde on the wall, blindfolded, facing out over the dark plain where the Unbound are gathering in "
         "every colour. In the centre of the horde, a vast floating knot of shattered light: the Sundered "
         "Heart.", speaker="ysolde"),
    shot("...There's a light on the east road. Does nobody else see it?",
         "Ysolde turning her blind face east. Tamsin looks: nothing but darkness.", speaker="ysolde"),
    )

cin("dawn", "The White Lantern", "During Heart of the Ring, in the last waves. Oswin returns; dawn breaks.",
    shot("The Heart had reached the inner wall when the night split open in the east.",
         "Battle at the inner wall. The eastern horizon tears with a line of white light."),
    shot("He came up the road on foot. The Unbound fell still around him as he passed, the way the dead "
         "fall still at the end of a long walk.",
         "A tall figure in glowing white robes walking up the east road through the horde; grey-eyed spirits "
         "freeze and fade as he passes. Nyxara turns toward him."),
    shot("He had walked the road of the dead the whole way round the world. Every light we lost had passed "
         "him going the other way.\n\nHe had kept them.",
         "Close on the lantern: white flame, six coloured sparks circling inside, the face of a city reflected "
         "in each spark."),
    shot("Hello, Ysolde. I'm sorry I'm late. It was a long way round.",
         "Oswin, white-haired, standing tall, at the foot of the wall below the Queen.", speaker="oswin"),
    shot("He lifted the lantern to the broken frame of the Sunstone.\n\nAnd the sun came up over Solenne.",
         "Oswin raising the lantern. Light pours up into the empty Sunstone frame above the city; it blazes. "
         "Real dawn floods the battlefield. (Game lighting: night to dawn.) Oswin joins as a hero."),
    )

cin("heart_falls", "Dawn", "After Heart of the Ring (Converge 3) is won.",
    shot("When the Sundered Heart fell, there was a man inside it. Very small, and very grey, curled around "
         "a locket.",
         "The knot of shards collapsing in dawn light. In the middle, Cassivane on his knees, ash, locket in "
         "his hands."),
    shot("Father. I'm here. I was always here. You just had to stop.",
         "Ilyra kneeling in front of him, taking his hands.", speaker="ilyra"),
    shot("He looked at her for a long time. Then he gave her the locket, and the ash took him.",
         "Cassivane's face, the grey leaving his eyes. He presses the locket into her hand and crumbles into "
         "ash in the dawn wind."),
    shot("I felt the sun on my face. I could not see it, but I felt it.\n\nSolenne stood.",
         "Ysolde on the wall, face lifted to the light, crying, smiling. The six peoples cheering in the "
         "streets of a city lit gold."),
    shot("The Crack is still open. He is still out there. And for the first time since this began, we have "
         "something to bring to his door.",
         "Oswin, Corvin, Tamsin and the Wardens around the Heartstone. Oswin looking east toward the Rift.",
         speaker="oswin"),
    shot("We had spent the whole war running.\n\nNow we went to find him.",
         "The army of the Concord marching out of Solenne's gates in dawn light, every hero and Warden at its "
         "head, toward the Rift."),
    )

cin("solenne_falls", "Solenne Falls", "If Heart of the Ring is lost. Then retry.",
    shot("The inner wall broke. The Heartstone dimmed.\n\nNo.\n\nNot like this. Not yet. Again.",
         "The inner wall cracking, the Heartstone's light flickering; then the image freezes and runs "
         "backward, as if Ysolde is refusing the memory."),
    )

# ------------------------------------------------------------------------------- the final assault
cin("assault_intro", "The Crownless Citadel", "Before the final assault (about 30 minutes).",
    shot("Beyond the Crack, nothing is the right way up.",
         "Through the Crack: the Outer Hollow, a black sky with a black sun and a crown-shaped gap. Hanging "
         "upside down beneath it, a vast fortress."),
    shot("Nhal Vorath. He built it out of everything his Unbound tore from our world. I am told the walls of "
         "Kethra are in it. And Vitrea. And our Dawn Gate.",
         "Close on the citadel walls: recognisable pieces of fallen cities: glass towers, a frozen ship, "
         "uprooted trees, broken Spirewright towers, and the Dawn Gate set as a tooth in an enormous mouth."),
    shot("You built your city on my city. You hang my crown over it like a lamp. I have come home for both.",
         "The black sun's corona flaring; every colour on screen drains to grey for a moment.",
         speaker="vael_orrun"),
    shot("Then it's a good thing we only need to make it once. Spirewright... for the first time in this "
         "war, we are not holding the road.\n\nWe are taking it.",
         "Tamsin, lantern-pole raised, at the head of the army, the Gatemaw ahead.", speaker="tamsin"),
    )

cin("mirror_spire", "The Mirror Spire", "During the final assault, at the start of the second movement.",
    shot("The Spire was Solenne, made wrong. Six walls of stolen stone, and on every one, a Herald we had "
         "already buried.",
         "A dark mirror of Solenne's six rings, upside down; on its walls the six Heralds as glassy grey "
         "Echo-Heralds."),
    shot("At the top gate, the Dawnblade turned and held it open for all of us. Her armour had gone grey. "
         "She held it until the last of us were through.",
         "Seraphel in the top gate, armour drained of colour, sword blazing, holding the doors apart as the "
         "army runs past her. Her light goes out. (Seraphel leaves the party.)"),
    shot("Tell Ysolde I saw one more dawn. That was all I wanted.", "Seraphel, smiling, fading.",
         speaker="seraphel"),
    )

cin("crownless_throne", "The Crownless Throne",
    "During the final assault, at the start of the third movement (the Vael-Orrun fight).",
    shot("He had no throne. He would not sit on anything that was not the centre of the world.",
         "A vast empty hall with no floor. In the middle, standing on nothing: a figure of black glass with a "
         "crown-shaped gap for a face, the Heartstone's stolen light caught in its chest."),
    shot("Six of you. Always six. You wear their crowns, little Queen. Ask them what they did at my table.",
         "Vael-Orrun turning toward the army and the six Wardens; cracks in its glass bleeding red, then "
         "blue, then green.", speaker="vael_orrun"),
    shot("Mirelle had seen a death at the end of the war. She told me later what it was.\n\nIt was the "
         "Seventh's.",
         "Mirelle at the edge of the hall, blind eyes glowing teal, a small smile."),
    )

cin("epilogue", "The Seventh Colour", "After the final assault is won. Then the credits.",
    shot("At the end, the six Wardens joined hands around him, the way they had at the beginning of the "
         "world.",
         "The six Wardens in a ring around Vael-Orrun, hands joined, their light rising."),
    shot("And Oswin set his lantern in the empty crown.",
         "Oswin stepping into the ring and placing the white lantern into the crown-shaped gap. Light floods "
         "the black glass from the inside."),
    shot("For a moment, in the light, he was a man again. Grey, and tired, and much younger than I had "
         "imagined.",
         "Inside the light: Vael-Orrun as he was, the kind-faced king in grey, holding his wife's ring. His "
         "eyes are not grey. They are only tired."),
    shot("It was never my voice in the dark. It spoke to me too.\n\nIt is still listening.",
         "Vael-Orrun looking past the Wardens, past the heroes, at something behind the camera.",
         speaker="vael_orrun"),
    shot("We remember.",
         "Thalassa, bells silent in her hair, the only Warden who can meet his eyes.", speaker="thalassa",
         duration=3.0),
    shot("We did not kill him. I do not think he could be killed. He wanted the middle of the world, so we "
         "gave it to him. Not as its king.\n\nAs its light.",
         "Vael-Orrun cracking apart into pure white light, which rises, and the black sun above the citadel "
         "turns gold."),
    shot("We went home to twenty-six cities of ash. Every one of their people walked back to rebuild them.\n\n"
         "That is what we fought for. Not the land. Them.",
         "Montage: Emberfolk relighting the forges of Kethra from their iron pots; Galeborn raising tents at "
         "Aurvanis; Sylvaine planting Elowen's seed; Pearlhaven's fleet coming home; Stoneborn unsealing "
         "Grundhallow through a door that is part of Orrok; Veilwalkers raising the telescope at Umbrael; "
         "Seraphel's glass sword set into the rebuilt Sunstone; Nyxara walking slowly beside Elowen through "
         "the ash of Sylvanmere. Tamsin, alive, sitting on the Lantern Walk with Fennick's spectacles, and "
         "Oswin, grey and old again, beside her, pointing at the sunset for the Queen."),
    shot("I am Ysolde, Queen of Solenne. I am old now, and I have never seen a dawn since.\n\nBut I have "
         "felt every one of them.",
         "Ysolde, older, grey hair, still blindfolded, on the walls of a rebuilt Solenne, sun on her face. "
         "Credits roll."),
    )

# The post-credits reveal (Part 2 tease). Only the Hush speaks: no narrator, almost no sound. It shows,
# without naming it, that Vael-Orrun and the Regent were both its hands, and that the war was its door.
cin("the_hush", "One Door", "Straight after the epilogue's credits.",
    shot("", "After the credits: the Hall of the Ring, rebuilt, empty, night. The Heartstone glows in six "
         "colours... then, faintly, a seventh. Ilyra, alone, leans in to look.", duration=5.0),
    shot("He was the first to listen.\n\nI taught him how a world goes quiet.",
         "Two thousand years ago: the vault under burning Vael. The young Keeper, Vael-Orrun, kneels in the "
         "dark with his wife's ring in his fist, listening. Grey creeps into his eyes from the edges.",
         speaker="the_hush"),
    shot("The Regent thought he bargained with a king.\n\nHe bargained with me, wearing a king's voice.",
         "Six years ago: Cassivane at his daughter's grave in the rain. Above him, a thin crack of starless "
         "dark opens in the night sky.", speaker="the_hush"),
    shot("I could never open the door from my side.\n\nYou opened it from yours.",
         "The Crack in the Hollow Rift seen from the far side, from the Outer Hollow: wide open where the "
         "Concord marched through. The six Wardens' light spills in from the world beyond it.",
         speaker="the_hush"),
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

# Plot beats keyed to the number of stages won, so they land in the right place in any order.
# When a beat and a stage scene fall on the same win, the stage scene plays first.
BEATS = [
    {"id": "refugee_road", "cinematic": "regents_counsel", "after_stages_won": 6},
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

CITIES = {
    "ember_1": ("Kethra", "Kethra's forges go cold under a black tide of seawater and ash."),
    "ember_2": ("Brazier Hold", "The Lanternguard bring down Brazier Hold's gate behind the last cart."),
    "ember_3": ("Vitrea", "Vitrea's glass towers ring like bells as they shatter, all at once."),
    "ember_4": ("Pyrrhenhall", "The caldera floods. The Emberfolk walk west carrying their forge-fires in iron pots."),
    "storm_1": ("Stonering Camp", "The standing stones of Stonering Camp topple inward like a closing hand."),
    "storm_2": ("Highwind", "Highwind's wind-bridges are cut, so nothing can follow."),
    "storm_3": ("Tarrow's Rest", "The Galeborn set the grass alight behind Tarrow's Rest to slow the Stone."),
    "storm_4": ("Aurvanis", "The Sky-Moot rides away on ten thousand horses. Only the tent poles remain."),
    "nature_1": ("Fernholt", "The moss of Fernholt stops glowing. The village is silent by morning."),
    "nature_2": ("Elderhollow", "The Deepwood seal Elderhollow's root-doors with their own hands."),
    "nature_3": ("Thornwall", "The thorns of Thornwall turn on their own wall."),
    "nature_4": ("Sylvanmere", "The Tree-City's people leave by its highest branches."),
    "water_1": ("Netmend", "Netmend's nets burn on the ice."),
    "water_2": ("Reedhaven", "The reeds are fired, and Reedhaven's stilts go with them."),
    "water_3": ("Glasswater", "The ice under Glasswater cracks, and the lake takes it whole."),
    "water_4": ("Pearlhaven", "Pearlhaven's fleet sails west with every child of Frostmere aboard. The harbour boils."),
    "earth_1": ("Dustmark", "A dust storm buries Dustmark to its roofs."),
    "earth_2": ("The Kharum Terraces", "The Stoneborn collapse the switchbacks onto the road themselves."),
    "earth_3": ("Mesa Kharn", "Lightning splits Mesa Kharn in two."),
    "earth_4": ("Grundhallow", "The Stoneborn seal the Deep Halls with their ancestors inside."),
    "void_1": ("Lamplight", "Lamplight's lamps are left burning for anyone still on the road."),
    "void_2": ("Vesperhold", "Vesperhold's floating steps drift apart into the dark."),
    "void_3": ("Twinmoor", "Twinmoor's reflection walks away without it."),
    "void_4": ("Umbrael", "Umbrael's great telescope turns to face the Crack one last time, and falls."),
    "converge_1": ("Crossmere", "Every road on the Ring met at Crossmere. Now none do."),
    "converge_2": ("The Lumen Gate", "The first of Solenne's six walls falls. There is nowhere left to retreat to."),
    "converge_3": ("Solenne", "Solenne stands."),  # the capital is saved, not lost
}

# ------------------------------------------------------------------------------- characters
# side: hero | ally | villain | herald | warden_boss | overlord. joins: when a hero joins.
CHARACTERS = [
    # heroes
    ("tamsin", "Tamsin Reed", "Captain of the Lanternguard", "hero", "", "start",
     "Solenne's toughest soldier, always the last one through the gate. She leads every evacuation of the war."),
    ("brannoc", "Brannoc Emberhand", "Smith-Lord of the Reach", "hero", "fire", "after ember_2",
     "A giant smith who forged half the gates of Solenne, freed from the Saltmother's tide-cage still swearing. "
     "His forge-hammer never cools."),
    ("kaela", "Kaela Stormrider", "Marshal of the Steppe", "hero", "storm", "after storm_2",
     "First rider of the Galeborn, who had never ridden in the direction of retreat. Lightning lance, and a grey "
     "stallion called Thunderclap."),
    ("sylvaine", "Sylvaine Thornwhisper", "Warden-Archer of the Deep", "hero", "nature", "after nature_2",
     "Three hundred years old, she held Elderhollow alone for nine days. Her arrows grow where they land."),
    ("mirelle", "Mirelle the Tide-Seer", "Seer of Frostmere", "hero", "water", "after water_2",
     "A blind young seer who reads the future in ice. She has seen a death at the end of the war, and will not "
     "say whose."),
    ("gorrim", "Gorrim Stonebeard", "Shield of the Canyon", "hero", "earth", "after earth_2",
     "A Stoneborn shieldmaster with an iron ring in his beard for every friend he has buried. His shield is a "
     "carved stone door."),
    ("corvin", "Corvin the Uncrowned", "Ranger-King of the Rift", "hero", "void", "after void_2",
     "The Queen's exiled half-brother, framed for murder by the Regent. He knew the truth for six years and "
     "nobody listened."),
    ("ignar", "Ignar", "the Cinder Warden", "hero", "fire", "after ember_4",
     "The Warden of Fire, freed from the madness that made him the Cinder Tyrant. Black stone and a molten heart."),
    ("aurath", "Aurath", "of the Storms", "hero", "storm", "after storm_4",
     "The Warden of Storm, freed from the Thunderhead. A rider of cloud and lightning who is never quite still."),
    ("elowen", "Elowen", "the Evergreen", "hero", "nature", "after nature_4",
     "The Warden of Nature, freed from the Elder Broodmother. Very old, very tired, and still growing."),
    ("thalassa", "Thalassa", "of the Deep", "hero", "water", "after water_4",
     "The Warden of Water, freed from the Tidal Leviathan. She remembers every ship and every child."),
    ("orrok", "Orrok", "the Mountain", "hero", "earth", "after earth_4",
     "The Warden of Earth, freed from the Mountain Titan. A slow stone giant with trees on his shoulders."),
    ("nyxara", "Nyxara", "of the Hollow", "hero", "void", "after void_4",
     "The Warden of Void, who fought the Hollow King's crown from the inside. Keeper of the road of the dead."),
    ("ilyra", "Ilyra the Unbroken", "Daughter of the Regent", "hero", "void,storm", "after converge_1",
     "The Regent's lost daughter, six years a captive of the dark. She bends the Outer Hollow, and she is the "
     "only one her father might stop for."),
    ("seraphel", "Seraphel the Dawnblade", "Knight of the Sunstone", "hero", "all", "after converge_2",
     "The last knight of the Sunstone, kept alive by its light for nine hundred years. It is broken, and she "
     "has one fight left."),
    ("oswin", "Oswin the White Lantern", "Master of the Order of the Spire", "hero", "all",
     "during converge_3",
     "The Grey Lantern fell into the Crack at the start of the war. He walked the road of the dead the whole "
     "way round the world, and came back carrying every light the war put out."),
    # allies
    ("ysolde", "Queen Ysolde", "Queen of Solenne, the narrator", "ally", "", "",
     "Ruler of the Concord. Blinded when the Sunstone broke, she rules by voice and tells the story."),
    ("fennick", "Master Tobias Fennick", "Chief Tower-Wright", "ally", "", "",
     "The gruff old engineer who designed every tower. He held the Dawn Gate on the Night of Falling Stars."),
    # villains
    ("cassivane", "Cassivane Dral", "the Ashen Regent", "villain", "fire,void", "",
     "Lord Marshal of the Concord, who opened the Crack to bring his daughter back from the dead."),
    ("saltmother", "Saltmother Ourra", "the Drowned Herald", "herald", "water", "",
     "Once the Tidefolk's high priestess. Walks inside a column of black seawater. Boss of Cinder Steps."),
    ("gorrath", "Gorrath the Quarried", "the Stone Herald", "herald", "earth", "",
     "A Stoneborn general who carved out his own heart. Breaks into walking boulders. Boss of Galeback Ridge."),
    ("pale_vesper", "The Pale Vesper", "the Hollow Herald", "herald", "void", "",
     "A Veilwalker singer who walked the dead to rest and now sings them awake. Boss of Rootway."),
    ("ashwick", "Ashwick the Kindled", "the Flame Herald", "herald", "fire", "",
     "The Concord's youngest messenger, an ever-burning boy who never stops running. Boss of Saltmarsh Bends."),
    ("vholt", "Vholt Stormcrown", "the Sky Herald", "herald", "storm", "",
     "Kaela's old teacher, riding a thunderbird of black cloud. Boss of Canyon Switchbacks."),
    ("mother_briar", "Mother Briar", "the Thorn Herald", "herald", "nature", "",
     "The Deepwood's wisest healer, grown through with thorns. Boss of Fractured Steps."),
    ("the_hush", "???", "", "secret", "", "",
     "Revealed only in the post-credits scene. The villain of Part 2. Keep hidden from every codex and menu."),
    ("vael_orrun", "Vael-Orrun", "the Sunderer", "overlord", "", "",
     "Once the good king who kept the peace between the seven kingdoms, betrayed and burned out by the other "
     "six. He turned to the Unmaking for justice and became a tyrant, and has come back to reclaim his crown "
     "and his throne."),
]

# Existing boss enemies (data/enemies) per character, and the ones the gameplay thread will add.
BOSS_ENEMY = {
    "ignar": "cinder_tyrant", "aurath": "thunderhead", "elowen": "broodmother", "thalassa": "leviathan",
    "orrok": "mountain_titan", "nyxara": "hollow_king", "cassivane": "sundered_heart",
    "saltmother": "saltmother", "gorrath": "gorrath", "pale_vesper": "pale_vesper", "ashwick": "ashwick",
    "vholt": "vholt", "mother_briar": "mother_briar", "vael_orrun": "vael_orrun",
}

# The final assault: three movements, roughly ten minutes each.
ASSAULT = {
    "intro": "assault_intro",
    "movements": [
        {"name": "The Black Gate", "minutes": 10, "boss": "gatemaw", "cinematic": ""},
        {"name": "The Mirror Spire", "minutes": 10, "boss": "echo_heralds", "cinematic": "mirror_spire"},
        {"name": "The Crownless Throne", "minutes": 10, "boss": "vael_orrun", "cinematic": "crownless_throne"},
    ],
    "outro": "epilogue",
    # Plays straight after the outro: the reveal of the Hush.
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
        "cities": {sid: {"name": n, "fall_text": t, "saved": sid == "converge_3"} for sid, (n, t) in CITIES.items()},
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
    lines += ["", "Beats keyed to stages won (any campaign order): "
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
    lines += ["---", "", "## The Ledger of Fallen Cities", "",
              "Shown after each stage win.", "", "| Stage | City | Line |", "|---|---|---|"]
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
    used = {"prologue", ASSAULT["intro"], ASSAULT["outro"], ASSAULT["post_credits"]} | {b["cinematic"] for b in BEATS}
    used |= {m["cinematic"] for m in ASSAULT["movements"] if m["cinematic"]}
    for s in STAGE_SCENES.values():
        used |= {s.get(k) for k in ("before", "after", "lost") if s.get(k)}
        used |= {d["cinematic"] for d in s.get("during", [])}
    missing, unused = used - set(CINEMATICS), set(CINEMATICS) - used
    assert not missing, f"cinematics referenced but not written: {missing}"
    assert not unused, f"cinematics written but never played: {unused}"
    assert len(CITIES) == 27
    speakers = {s["speaker"] for c in CINEMATICS.values() for s in c["shots"]}
    assert speakers <= set(SPEAKERS), f"unknown speakers: {speakers - set(SPEAKERS)}"
    print(f"wrote {len(CINEMATICS)} cinematics, {len(CHARACTERS)} characters, {len(CITIES)} cities to {root}")
    print("opening runs", round(sum(s["duration"] for s in CINEMATICS["prologue"]["shots"])), "seconds")


if __name__ == "__main__":
    main()
