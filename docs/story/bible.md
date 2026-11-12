# Story Bible: The Black Gate

This is the canon for the campaign story (version 2, approved by Doctor Paris on 2026-11-12). The art,
voice, cinematics and heroes work all builds from it. If anything disagrees with it (a stage description,
a codex text, an older doc), this file wins and the other text should be changed to match.

Companion files:

- [characters.md](characters.md): the cast sheet (looks, colours, weapons, key scenes) for art and voice.
- [scripts.md](scripts.md): the opening and every cinematic, shot by shot. Generated from
  `tools/story/story_content.py`.
- [README.md](README.md): how the story maps onto the 27 stages, the capital and the final level.

**The two rules this version is built on.** Everything in the plot is physical: a real place you can walk
to, a real object, a plain cause. And the player wins: every stage won saves its town, every land is taken
back, and the war ends with us storming the enemy's fortress.

---

## 1. The story in one breath

**The world.** Orrhen is six lands in a ring around one capital, Solenne. Each land has its own element:
Fire, Storm, Nature, Water, Earth, Void. In the far east, in the Void land, the ground splits open into the
**Rift**, a chasm miles deep. At the bottom of the Rift stands the **Black Gate**, a stone door as tall as
a mountain. Behind it is **the Hollow**, a sunless cavern land under the world.

**Two thousand years ago.** Vael-Orrun was king of the middle kingdom, where Solenne stands today. The six
monarchs of the other kingdoms came to his peace feast as friends, burned his city and killed his wife
and son. That night something in the dark taught him a power that stops all magic, and he made war on all
six. They beat him, drove him and his army down the Rift and shut the Black Gate on them. They made the
Gate's key from his own crown: a six-coloured jewel, the **Heartstone**, which they kept far from the
lock, in the capital later built on his ruins. Locked, the Gate lets nothing of the Hollow out, not even
through a crack, though anyone can still go in. Then the six monarchs gave their lives to hold the Gate
shut. Their spirits sleep inside their lands as the six **Wardens**, and while all six sleep in peace,
their oath binds him by name.

**What starts the war.** Six years ago, Ilyra, daughter of Solenne's Lord Marshal Cassivane, climbed down
to the Gate, slipped inside through a crack, and was caught. A voice from behind the Gate told Cassivane
she would come home if he unlocked it. He chipped a sliver off the Heartstone and, this spring, used it to
unlock the Gate and force it open. Oswin, master of our Order, turned the light of all his towers on the
Gate and pushed it back until only a gap a cart wide was left, and fell through.

**The war.** A gap that size lets an army through a few at a time, but not Vael-Orrun himself: the
Wardens' oath binds him while they sleep in peace. So he sends six generals, the **Heralds**, one to each
land, to drive its Warden mad. When a land's Warden goes mad, the land can no longer keep out the element
opposite its own, and that element floods in with the Herald's army: the sea climbs the volcano, the stone
climbs the steppe.

**Us.** We are the **Order of the Spire**, who build towers that hold an element. We go land by land,
hold the road in front of each town until the attack breaks, kill the Herald and free the mad Warden.
Every town we hold is saved. The last of the six lands is the Rift itself.

**The end.** With all six Wardens free, the oath holds him again, and only the whole Heartstone can undo
it, so everything Vael-Orrun has left marches on Solenne for it. We hold the capital. Then we march down
the road into the Rift, through the gap in the Gate on foot, and take his fortress in the Hollow.

### Plain answers

| Question | Answer |
|---|---|
| Where is the enemy? | Behind the Black Gate, a stone door at the bottom of the Rift, in the Hollow, a cavern land under the world. |
| How did they get out? | Cassivane unlocked the Gate with a sliver of the Heartstone. Oswin pushed it back to a gap a cart wide, and the armies come out through that gap. |
| Why doesn't Vael-Orrun walk out himself? | The six Wardens' oath binds him by name while they sleep in peace. Driving them mad weakens it; the whole Heartstone would undo it. |
| Why is each land attacked by its opposite? | Each Warden holds its own element and keeps the opposite one out. Mad, it can't, and the opposite floods in with the Herald's army. Free the Warden and the flood stops. |
| Do we lose towns? | No. Winning a stage saves its town. The only wall we lose is Solenne's outer wall, the Lumen Gate. |
| Why is it night for half the game? | The Sunstone's light held the Hollow's darkness down in the Rift. When Cassivane breaks it, the darkness climbs out and covers the sky. When Oswin relights it, the darkness sinks back. |
| How do we reach his fortress? | We walk down the road cut into the Rift's wall and through the gap in the Gate in single file. |

---

## 2. Origins: the War of Seven Crowns

Known history begins with seven kingdoms. Everything before them is song.

### The Seven Kingdoms

Six kingdoms lay in a ring around the middle of the world. Each was ruled by a monarch bound by blood to the
element of their land, and each hated the kingdom across the ring from it, because that kingdom's element
was the one that most opposed its own.

| Kingdom | Element | Founding monarch (later the Warden) | Seat |
|---|---|---|---|
| **The Ember Throne** | Fire | **Ignar**, the Forge-King | Pyrrhenhall, in the caldera |
| **The Wind Crown** | Storm | **Aurath**, the Horse-King, who ruled from the saddle | Aurvanis, the Sky-Moot |
| **The Green Realm** | Nature | **Elowen**, the Green Queen | Sylvanmere, the Tree-City |
| **The Tide Throne** | Water | **Thalassa**, the Sea-Queen | Pearlhaven |
| **The Stone Kingdom of Kharum** | Earth | **Orrok**, the Mountain-King | Grundhallow, the Deep Halls |
| **The Star Kingdom** | Void | **Nyxara**, the Star-Queen | Umbrael |

The seventh kingdom was **Orrun**, the Middle Kingdom, and its capital was **Vael**, a city of black stone at
the crossroads where every road of the world met. Orrun had no element of its own. Its people were
traders and go-betweens, and its kings called themselves the Keepers of the Crossroads: they settled the
quarrels between the six, and they grew rich on them.

### The Seven Arts

The elements are the raw stuff of the world, but nobody in Orrhen simply "uses fire". Each kingdom
learned to work its element in its own way, with its own alchemy, its own magic and its own price. These
arts outlived the kingdoms, and the six peoples still practise them. Every tower, hero, Herald and Warden
in the game draws its power from one of them.

| Art | Kingdom | How it works | Its price | Practitioners |
|---|---|---|---|---|
| **Kindling** (cinder alchemy) | The Ember Throne (fire) | Fire is fed, never commanded. Kindlers write ember-runes into metal and glass, then quench them, trapping heat as power. Their great works are transmutations: sand into glass, ore into steel, a man's anger into a blade. | The caster's own heat. Old Kindlers are always cold, and their glowing rune tattoos are where the fire went. | Forge-wrights, glass-singers, the smith-lords |
| **Stormsong** | The Wind Crown (storm) | Weather is music. Galeborn stormsingers chant in rhythm with the sky, and the sky answers in kind; a war-chant calls lightning down, a lullaby stills a gale. Their horses are part of the song. | Breath and voice. A stormsinger who sings too long goes hoarse, then silent, forever. | Stormsingers, sky-riders |
| **Rootcraft** (green alchemy) | The Green Realm (nature) | Slow magic of seed, graft, venom and remedy. A spell is planted rather than cast, and grows into its effect: a thorn that becomes a wall, a poison brewed over a season. Healing and poison are the same craft. | Time. Great rootcraft takes years, and the Deepwood live long to pay for it. | Grovewardens, apothecaries, bow-shapers |
| **Tidelore** (rime memory) | The Tide Throne (water) | Water remembers everything it has touched. Tidefolk seers read memory and the future in ice, freeze moments in place (slowing, holding) and call drowned things back up. Initiates are drowned under the ice and brought back. | Their own memories, given to the water in trade. Great seers forget their own names. | Ice-seers, tide-priests, the Saltmothers |
| **Runecarving** (deepcraft) | Kharum (earth) | Oaths cut into stone hold forever. Stoneborn carve runes of weight, ward and breaking into rock, armour and gates; their golems are oaths given a body. | Permanence. A rune can never be uncarved, and a Stoneborn who breaks a carved oath turns, slowly, to stone. | Runewrights, shieldmasters, oath-keepers |
| **Starcraft** (veil astromancy) | The Star Kingdom (void) | The stars are a map of every hidden road, including the roads under the world. Veilwalkers chart a spell in the stars, then walk it: curses, shadows, pulls of gravity, and the dark places under the earth. | Light. Every starcraft spell darkens something of the caster's (their hair, their eyes, their shadow). | Astronomers, deathwalkers, rangers of the Rift |
| **The Grand Alchemy** | Orrun, the Middle Kingdom (no element) | Orrun had no element of its own, so its scholars studied all six arts and learned how each was put together, so that they could trade in them. The Grand Alchemy was the science of magic itself: how to combine the arts, and how to take them apart. | Nothing, at first. That was what made it dangerous. | The alchemist-merchants of Vael |

**The Unmaking** was the last and worst discovery of the Grand Alchemy. If you know how an art is put
together, you can pull it apart. The High King learned to unpick any art down to nothing, so that fire
forgets to burn and a stormsong ends mid-note. That is what makes the elements *stop* where his armies
march, and what drains the colour out of the Unbound.

**Spirecraft**, the art of the Order of the Spire, came a thousand years later. Aurel rediscovered the
half of the Grand Alchemy that combines arts, never the half that unpicks them: a Spirewright binds a
kingdom's art into worked stone, and a tower holding two or three arts at once (the game's hybrid and
triple towers) is stronger than any of them alone. Few in the Order know where their art first came from.
Oswin did.


### The Keeper of the Crossroads (the truth the songs bury)

What follows is what really happened. The songs of the Concord, and the prologue (which Ysolde narrates
as the songs tell it), give only the winners' version: a greedy tyrant and six brave kingdoms. The truth
comes out in hints over the campaign, and all at once in The Truth, after his fortress falls.

The last king of Orrun was **Vael-Orrun**, and for forty years he was the best king the world had. Orrun
had no element and no army worth the name; what it had was the crossroads and the Grand Alchemy, and Vael-
Orrun used both to keep the peace. He sat between Ember and Tide, Wind and Stone, Green and Star, and
talked them out of a hundred wars. He opened Orrun's schools to all six peoples. He married **Ysmera**, a
Tidefolk healer, and they had a son, **Caelan**. Vael, his city, was the only place in the world where a
Kindler and a Tidelore seer would sit at the same table. He took the name of his city and his kingdom
because he believed a king should belong to his people, not the other way round.

The six monarchs loved him in public and feared him in private. Orrun's alchemists understood every one of
their arts better than they did. Orrun grew rich on their quarrels. And a king who can end any war can,
in principle, start one.

### The Night of Six Knives

In the forty-first year of his reign, Vael-Orrun called the six monarchs to Vael for the **Feast of the
Crossroads**, to sign a peace that would last forever. They came as friends. Each had already agreed,
secretly, with the others: Orrun would be broken that night and its alchemy divided six ways. It was the
first time in history the six had ever agreed on anything.

At midnight their soldiers opened the gates. Vael burned. **Ysmera and Caelan died in the fire**, in the
hall where the peace was to be signed. Vael-Orrun lived, because his alchemists dragged him out through
the vaults beneath the city.

> *Six hold the door. Six hold each other. When the Six hold knives, the door will open.*
> The Veilwalker warning is not a prophecy. It is a memory of that night, cut into stone by Nyxara's
> people, who were the only ones ashamed enough to keep it.

### The Voice in the Vault

In the deepest vault of the Grand Alchemy, under his burning city, with his wife's ring in his hand,
Vael-Orrun heard a voice for the first time. It was very quiet. It said it was sorry. It said there was a
way to make sure nobody ever burned a city again: take the magic out of the world, all of it, and keep it
in one place, where it could be watched. It taught him **the Unmaking**.

He believed the voice was his own grief, talking him through the dark. It was not. (See section 7.6.)


### The War of Seven Crowns

What the songs call a tyrant's conquest began as a widower's justice. Vael-Orrun had a crown made with six
empty sockets, one for each crown that had come to his feast, and named himself the **High King**. For
forty years his armies marched out of the ruins of Vael, and where they marched, magic stopped: fire that
would not burn, wind that lay down, water hanging mid-fall. Each year the voice asked a little more of him,
and each year he gave it, and each year there was a little less of the king who had kept the peace.

At the **Siege of Vael**, the six monarchs stood together a second time, each beside its oldest enemy.
Ignar with Thalassa. Aurath with Orrok. Elowen with Nyxara. Opposites in balance were the one thing the
Unmaking could not unpick. They broke what was left of Vael and drove him and his army east, to the Rift.

### The Black Gate and the Heartstone

They could not kill him; he had unmade his own death long before. So they drove him and his army down the
Rift and through the **Black Gate**, an ancient stone door at its bottom, into **the Hollow**, the sunless
cavern land under the world. The ruins of Vael sank with him into the dark below.

A door needs a lock. The six monarchs took the High King's crown, set a piece of themselves into each of
its six empty sockets, and fused it into a single stone that shines in all six colours: the **Heartstone**,
the Gate's key. They kept it as far from the lock as they could, at the centre of the world, where his
throne had stood.

What each gave shaped them ever after. Ignar gave his **appetite**, so the fire of the Reach warms instead
of devouring. Aurath gave his **stillness**, so the sky of the Steppe can never rest. Elowen gave her
**seasons**, so the Deep is always green and she is always slowly ageing. Thalassa gave her
**forgetting**, so she remembers everything. Orrok gave his **voice**, so he barely speaks. Nyxara gave
her **face**, so where her face should be there are only stars.

**The rules of the Gate** (the whole plot rests on these):

1. **Locked, the Gate lets nothing of the Hollow out**, not even through the cracks in its stone. Anyone
   can still go in. Ilyra did.
2. **The Heartstone is the key.** A sliver of it can unlock the Gate. The whole stone can undo everything.
3. **The Wardens' oath binds Vael-Orrun by name.** The six monarchs gave their mortal lives and went to
   sleep inside their lands (a volcano, a storm, a tree, a sea, a mountain, the dark over the Rift). While
   all six sleep in peace, he cannot pass the Gate even when it stands open.
4. **Each Warden holds its own element and keeps the opposite one out.** A mad Warden can't, and the
   opposite element floods its land.
5. **The Sunstone's light** (hung over Solenne a thousand years later) burns hollow things and holds the
   Hollow's darkness down in the Rift.

His last words before the Gate shut are kept only in Thalassa's memory: *"You did this. Remember that you
did this."*

Their kingdoms, crownless now, became the six peoples. Mortals call the sleepers the **Wardens**, and most
have forgotten they were ever kings and queens. Vael's name was cursed and then forgotten.

### What two thousand years did to him

Vael-Orrun has spent two thousand years in the Hollow with the voice. It has made a monster of him: the
huge, horned, demon-faced High King the player fights is what the dark and the Hush made of the man. But
he remembers. The Heartstone is his crown. Solenne stands on the ruins of his city, on the hall where his
wife and son burned. The six who betrayed him still hold him by name, and nobody alive remembers what they
did. He wants his crown back, because it is the key to his prison, and he wants the six to answer for the
Night of Six Knives.

He is wrong about one thing. He thinks the war is his.

---

## 3. History of the mortal world

### The Six Peoples

The six kingdoms, without their monarchs, became six peoples, each still shaped by its sleeping Warden:

| People | Land | Character |
|---|---|---|
| **The Emberfolk** | The Ember Reach (fire) | Smiths and glassmakers on the slopes of the caldera. Loud, proud, generous. Their word is iron. |
| **The Galeborn** | The Thunder Steppe (storm) | Nomad riders of the high grass, who read the weather like scripture and sing to their horses. |
| **The Deepwood Clans** | The Verdant Deep (nature) | Archers and healers who live in, not under, the oldest trees. Slow to anger, impossible to forget. |
| **The Tidefolk** | Frostmere (water) | Fishers, sailors and seers of the great frozen lake. They keep every memory in songs and in ice. |
| **The Stoneborn** | Sunscar Canyon (earth) | Miners and masons who carve whole cities into canyon walls. Stubborn as their mountain. |
| **The Veilwalkers** | The Hollow Rift (void) | Astronomers and keepers of the dead, and the guards of the Rift. They have watched the Black Gate from its rim for two thousand years. |


### The Opposites War (Year -300 to 0)

The Six Peoples kept the peace for a long age after the Siege of Vael, and then forgot why. For three
hundred years they fought, always against their opposites: Emberfolk against Tidefolk, Galeborn against
Stoneborn, Deepwood against Veilwalker. No one remembered that this was exactly what the High King had
counted on.

### Aurel and the First Spire (Year 0)

A Galeborn shepherd named **Aurel**, digging in the ruins of Vael, found the scraps of the Grand Alchemy
and learned that any of the six arts could be *bound*: poured into worked stone and held there, still and
useful, the way the Wardens held their lands. She called it **Spirecraft**. She built the first **Spire** on the
ruins of Vael at the centre of the world, where the Heartstone glowed, and showed all six peoples that a tower of
Kindling stood strongest when a tower of Tidelore stood beside it, and that one tower could hold two arts
at once.

Aurel united the peoples in the **Concord of the Ring**, founded the **Order of the Spire** to train
tower-binders (**Spirewrights**), and raised the city of **Solenne** around the Heartstone. Above the city
she hung the **Sunstone**, a lens that gathers the light of all six lands into a second sun. Its light burns hollow things,
and it holds the Hollow's darkness down in the Rift. The Concord
counts its years from that day.

### The Thousand Years (Year 0 to 1012)

Solenne became the Crowned Heart, the most beautiful city anyone has built, white walls stepped in six
rings around the Heartstone, each ring faced with the stone of one land. The Order of the Spire kept the
roads. The **Lanternguard**, Solenne's own soldiers, kept the gates. The Wardens slept.

The Veilwalkers alone kept the old warning, cut into the walls of their observatory at Umbrael:

> *Six hold the door. Six hold each other. When the Six hold knives, the door will open.*


### The present: Year 1012 of the Concord

Queen **Ysolde** rules Solenne. She came to the throne at fourteen, and for ten years the realm was
governed by her regent, the Lord Marshal **Cassivane Dral**, a brilliant and well-loved soldier. When
Ysolde came of age he stayed at her side as her first counsellor and commander of the armies. Nobody in
Solenne is more trusted.

---

## 4. How the war began

| When | What happened | Who knows |
|---|---|---|
| Year 1006 | Ilyra, Cassivane's only daughter, goes down the Rift with the Veilwalkers to study the Gate, slips inside through a crack, and is caught. Through the crack a voice tells Cassivane she lives and will come home if he unlocks the Gate. | Cassivane |
| Year 1006 | Cassivane chips a sliver off the Heartstone. A Veilwalker of the Hall sees him do it and is killed. Corvin, the Queen's half-brother, accuses Cassivane, is found over the body, and is exiled for the murder. | Cassivane, Corvin |
| Year 1010 | Cassivane secretly sends six of the Concord's champions to the Rift "to study the Gate". They come back emptied, as the Heralds, and wait in the Rift. | Cassivane |
| Year 1012, spring | Cassivane unlocks the Gate with the sliver and forces it open. Oswin rides to the Rift, turns the light of every tower on the Gate and drives it back until the gap is a cart wide, then falls through when the ground gives way. His lantern is still lit. | Everyone, except who did it |
| Year 1012 | Six armies file out through the gap and up the Rift road, one to each land, each led by a Herald. | Everyone |

### Why each land is attacked, and by what

The Heralds go to the six sleeping Wardens and whisper to them until they go mad. A mad Warden's land can
no longer keep out the element opposite its own, and that element floods in with the Herald's army:

| Land | Warden (mad form) | Floods in | Herald |
|---|---|---|---|
| The Ember Reach (Fire) | Ignar (the Cinder Tyrant) | The sea climbs the volcano | Saltmother Ourra |
| The Thunder Steppe (Storm) | Aurath (the Thunderhead) | Walking stone climbs the plateau | Gorrath the Quarried |
| The Verdant Deep (Nature) | Elowen (the Elder Broodmother) | The Hollow's dark creeps under the trees | The Pale Vesper |
| Frostmere (Water) | Thalassa (the Tidal Leviathan) | Fire runs across the ice | Ashwick the Kindled |
| Sunscar Canyon (Earth) | Orrok (the Mountain Titan) | Armoured lightning walks down the walls | Vholt Stormcrown |
| The Hollow Rift (Void) | Nyxara (the Hollow King) | Thorns and walking dead trees | Mother Briar |

Freeing a Warden ends that land's war: the flood drains away and the Herald's army scatters.

### The Unbound

Every common enemy is one of the **Unbound**, in three kinds:

- **Hollowed**: living people the Unmaking has emptied (grey, empty eyes). Brutes, Menders, the Warded.
- **Risen**: the dead, marching. The dead of the old war shut behind the Gate with him (Grunts), and the
  dead the Pale Vesper sings out of the ground.
- **Wild**: beasts and spirits of the invading element. Runners, Splitters and Shardlings, Ashdrakes.

They cannot stand the Sunstone's light, and they scatter when their land's Warden is freed. Never describe
them as orcs, elves or dwarves, and never call an enemy a "Warden" (the dragon is an **Ashdrake**).

**Who we are:** the Spirewright (the player), last apprentice of Oswin, with what is left of the Order of
the Spire and the Lanternguard.

---

## 5. Places

### The Six Lands and their campaigns

The lands open in a fixed order, so the story runs straight through.

| Land | Element | Campaign | Invaded by | Look |
|---|---|---|---|---|
| **The Ember Reach** | Fire | stages 1-4 | The sea | Black basalt terraces, lava rivers, glassworks, banners of red and brass. |
| **The Thunder Steppe** | Storm | stages 5-8 | The Stone | Endless high grass, standing stones, tent-cities, a sky that should never be still. |
| **The Verdant Deep** | Nature | stages 9-12 | The Hollow | Trees the size of towers, rope bridges, glow-moss, roots like roads. |
| **Frostmere** | Water | stages 13-16 (night) | The Flame | A frozen sea, stilt towns, pearl-white harbours. |
| **Sunscar Canyon** | Earth | stages 17-20 (night) | The Sky | Red rock, cliff cities carved in terraces, giant stone faces of old kings. |
| **The Hollow Rift** | Void | stages 21-24 (night) | The Grove | Violet grass, floating stone steps, the observatory city, and the chasm with the Gate at its bottom. |
| **The Heartland** | All | Convergence, stages 25-27 | Everything he has left | Prism glass plains, the six-ringed white city of Solenne. |

### Solenne, the Crowned Heart (capital)

Six concentric walls, each faced with the stone of one land: red basalt, storm-grey granite, living
greenwood, blue ice-glass, sun-red sandstone and black stone. At the centre, the **Heartstone** in its
open-roofed Hall of the Ring. Above the city, on the **Spire of Aurel**, hangs the **Sunstone** lens.

Key places: the **east gate** (where Fennick dies at the midpoint), the **Lumen Gate** (the outermost
wall, lost at Convergence 2), the **Hall of the Ring**, the **Spire of Aurel**, the **Lantern Walk** (the
wall-top road of the Lanternguard).

### The Rift and the Black Gate

A chasm miles deep in the east of the Hollow Rift land. A road is cut into its wall, winding down to the
bottom; it takes a day to walk. At the bottom stands the Black Gate, a stone door as tall as a mountain.
Since the prologue it stands open by a gap the width of a cart. From the rim you can see the Gate and the
grey columns still climbing out.

### The Hollow and Nhal Vorath (the final level)

Behind the Gate is the Hollow: a cavern under the world so big its roof is lost in the dark, a stone sky
lit only by grey fire. A day's march in stands **Nhal Vorath**, Vael-Orrun's fortress, built from the
ruins of his old city Vael, which sank with him when he was driven down.

---

## 6. The towns we save

Every stage defends one town at the end of its road. Winning the stage saves it; the game shows "**<town>
is saved.**" and one line. The only exception is the Lumen Gate, Solenne's outer wall, which falls in the
story even when its stage is won. The exact lines are in `tools/story/story_content.py` (`CITIES`).

| Stage | Town | Stage | Town |
|---|---|---|---|
| Ember 1 | Kethra, a forge-town | Water 1 | Netmend |
| Ember 2 | Brazier Hold (Saltmother) | Water 2 | Reedhaven (Ashwick) |
| Ember 3 | Vitrea, the Glass City | Water 3 | Glasswater |
| Ember 4 | Pyrrhenhall (Ignar) | Water 4 | Pearlhaven (Thalassa) |
| Storm 1 | Stonering Camp | Earth 1 | Dustmark |
| Storm 2 | Highwind (Gorrath) | Earth 2 | The Kharum Terraces (Vholt) |
| Storm 3 | Tarrow's Rest | Earth 3 | Mesa Kharn |
| Storm 4 | Aurvanis, the Sky-Moot (Aurath) | Earth 4 | Grundhallow (Orrok) |
| Nature 1 | Fernholt | Void 1 | Lamplight, a waystation |
| Nature 2 | Elderhollow (Pale Vesper) | Void 2 | Vesperhold (Mother Briar) |
| Nature 3 | Thornwall | Void 3 | Twinmoor |
| Nature 4 | Sylvanmere, the Tree-City (Elowen) | Void 4 | Umbrael, the Observatory City (Nyxara) |
| Converge 1 | Crossmere (Cassivane) | Converge 2 | **The Lumen Gate (falls)** |
| Converge 3 | **Solenne** (the Sundered Heart) | Final level | Nhal Vorath (Vael-Orrun) |

The story's losses come from its big moments instead: Fennick, the Sunstone, the Queen's sight, the Lumen
Gate, Seraphel.

---

## 7. The cast

Full looks, colours and scene lists are in [characters.md](characters.md). This section is who they are.

### 7.1 The Spirewright (the player)

The last apprentice of Oswin. Never named, never seen up close, never speaks. Characters address the
player as "Spirewright". The player's hand is visible in cinematics only as a gloved hand setting a glowing
keystone into a tower.

### 7.2 The narrator

**Queen Ysolde of Solenne** narrates the whole game in a deep, calm, low female voice, speaking from years
after the war. She never gives a secret away before its scene. She is also a character on screen.

### 7.3 Heroes (playable)

Sixteen heroes join over the campaign: one at the start, one mortal champion per land (rescued when that
land's Herald falls at stage 2), the six Wardens (freed at stage 4 of their land), two in the Convergence,
and Oswin, who comes back at the capital.

| # | Hero | Element | Joins | Who they are |
|---|---|---|---|---|
| 1 | **Tamsin Reed**, Captain of the Lanternguard | None (lantern light) | Start | Solenne's toughest soldier, raised in the gutters of the Lantern Walk. Always the last one through the gate. Drags the blind Queen clear on the midpoint night, then reads Fennick's notes to the player. Dry, kind, tired, unbreakable. |
| 2 | **Brannoc Emberhand**, Smith-Lord of the Reach | Fire | Ember 2 | The giant smith who forged Solenne's gates. The Saltmother kept him in a salt cage for nine days to make him forge her chains, and he refused every day. Breaks Vael-Orrun's gate in the final level ("Gates are my trade"). |
| 3 | **Kaela Stormrider**, Marshal of the Steppe | Storm | Storm 2 | War-leader of the Galeborn, who fought the Stone alone for eleven days and hates riding away. Kills her old teacher, the Herald Vholt, facing him. |
| 4 | **Sylvaine Thornwhisper**, Bow of the Deep | Nature | Nature 2 | The Deepwood's best archer, three hundred years old. Held Elderhollow's root-doors until every child was out. Carries Elowen's last seed and plants it in Solenne in the epilogue. |
| 5 | **Mirelle the Tide-Seer** | Water | Water 2 | A blind young Tidefolk seer who reads the future in ice; kept forty children alive inside a tower of ice. Has seen a death at the end of the war and won't say whose. It is Vael-Orrun's. |
| 6 | **Gorrim Stonebeard**, Shield of the Canyon | Earth | Earth 2 | Stoneborn shieldmaster with an iron ring in his beard for every friend he has buried (thirty-one when he joins). Braids one more for Grundhallow's dead and swears it is his last. |
| 7 | **Corvin the Uncrowned**, Ranger of the Rift | Void | Void 2 | The Queen's elder half-brother. Accused Cassivane, was framed for murder and exiled, and watched the Gate from the rim for six years. The man who was right all along. |
| 8-13 | **Ignar, Aurath, Elowen, Thalassa, Orrok, Nyxara**, the six Wardens | Their own | Stage 4 of their land | The six monarchs who betrayed Vael-Orrun. Freed from madness, they fight for us and keep their old crime secret until his fortress falls. |
| 14 | **Ilyra the Unbroken** | Void + Storm | Converge 1 | Cassivane's daughter, caught inside the Gate six years ago and sent back empty. Left in her father's cage, she finds herself again on her own, which proves his bargain was a lie. Behind the Gate she heard two voices: "One of them wept. The other never did." |
| 15 | **Seraphel the Dawnblade**, Knight of the Sunstone | All six | Converge 2 | The Sunstone's light has kept her alive for a thousand years; since it broke she has been dying. Holds the fortress's inner gate open in the final level until the last of us are through, and dies. |
| 16 | **Oswin the White Lantern** | All six (light) | Converge 3, wave 17 | Fell through the Gate in the prologue, walked back under the world through the Hollow, found the last piece of the Sunstone at the bottom of the Rift and climbs out in time to relight it. |

**Each hero's art.** Tamsin has no magic, only Lanternguard drill and a lantern that is an old Spirecraft
relic. Brannoc is a master Kindler. Kaela is a stormsinger. Sylvaine works Rootcraft through her bow.
Mirelle is a Tidelore seer. Gorrim is a runewright, and his door-shield is carved with Kharum's oldest
oath-runes. Corvin works Starcraft, and his silver hair is what it has cost him. The six Wardens founded
their kingdoms' arts. Ilyra knows Starcraft and Stormsong, and from six years behind the Gate, a little of
the Unmaking, which frightens everyone, including her. Seraphel and Oswin work Spirecraft.

### 7.3a Hero backstory details (canon)

The full hero stories are in the heroes doc, "Heroes of the Ring: hero stories"
(https://claude.ai/artifact/G1tjkeYAfvc4UBZz5oda6p). Where it disagrees with this file, this file wins.
These details from it are canon:

- **Tamsin** was born on the Lantern Walk and joined the Guard unable to read; she learned from the
  Order's tower manuals.
- **Brannoc** forged Solenne's east gate and signed his name inside it.
- **Kaela** was born in a storm on the road to Aurvanis and won the Long Race on Thunderclap.
- **Mirelle** was born blind in Reedhaven and became a seer by drowning under the ice; the fish in her staff
  swam beside her. She can no longer remember her mother's face: that was her Tidelore price.
- **Gorrim** held the Kharum Pass beside Gorrath. His "no more rings" is a carved oath. When Seraphel dies
  his fingertips go grey; he says she did not fall, she went where she meant to go, and gives her no ring.
- **Corvin** taught Ysolde and Ilyra the stars when they were children.
- **Ilyra** is the one alone in the Hall of the Ring after the credits, because at Vael-Orrun's "It was
  never my own voice" she understood that the weeping voice behind the Gate was his, and the other was not.
- **Seraphel** was the last of the twelve Knights of the Sunstone, and taught Ysolde to fight. After the
  war her sword is set into the rebuilt Sunstone.
- **Oswin** came to Solenne as a tinker's boy from nowhere. Giving up his lantern in The Truth leaves him
  grey and old again; he lives to see Solenne rebuilt and describes the sunsets to the Queen.
- **The Wardens and the Night of Six Knives.** Ignar's Kindlers set the fire ("It was my fire"). Aurath's
  riders were first through the gates. Elowen asked for Ysmera and Caelan to be sent out before midnight;
  nobody did it, and she did not check. Ysmera was one of Thalassa's Tidefolk; Thalassa tells the truth
  after his fortress falls and answers his last words with "We remember." Orrok swore the peace aloud at
  the feast knowing it would be broken. Nyxara's mad form is a crowned king because she came to his feast
  wearing a crown.

### 7.4 Major allies (non-playable)

- **Queen Ysolde**, 24, ruler of Solenne and the Concord. Clever, sharp-tongued, braver than she lets anyone
  see. She trusted Cassivane like a father and signed Corvin's exile. Blinded at the midpoint while running
  with the Heartstone, she rules by voice for the rest of the war and stands on the walls anyway.
- **Master Tobias Fennick**, 70, Chief Tower-Wright of the Order. Designed every tower the player builds
  and briefs the player from the first land ("Fire burns, water slows, and you, child, will place them
  where I tell you"). Dies at the midpoint holding Solenne's east gate. After that Tamsin reads his notes.
- **Oswin**, the Grey Lantern (before his return). Old, wry, endlessly patient. Seen in the prologue.

### 7.5 Villains: one chain, each link thinks it is the top

| Who | What they want | What is true | How it ends |
|---|---|---|---|
| **The Hush** (never named in Part 1) | Silence: no magic, no world. | Older than the world, deep under the Hollow. It taught Vael-Orrun the Unmaking and has lived inside him since. It cannot reach our world by itself. | When Vael-Orrun's light goes home into the Heartstone, it comes with him. Post-credits: an eye opens inside the Heartstone. |
| **Vael-Orrun, the High King** | Justice for the Night of Six Knives, and his crown, the key to his prison. | Two thousand years in the dark with the Hush made him a monster. He bargained with Cassivane himself, and never knew he was the Hush's tool. | Beaten on wave 39, flees into his fortress; when it falls the Wardens confess, he sees the truth, and his light goes home to his crown. |
| **Cassivane Dral, the Ashen Regent** | His daughter back. | Vael-Orrun gave Ilyra back empty and promised she would be whole once he is free. That is why Cassivane fights on after he has her. | Fused with the broken Sunstone as the Sundered Heart, he dies at Solenne's inner wall in Ilyra's arms, seeing she has healed without any of it. |
| **The six Heralds** | Nothing. They are emptied. | Six champions Cassivane sent to the Rift. Each leads one army to one land and drives its Warden mad. | Each dies at stage 2 of its land; echoes of them return in the final level. |
| **The six mad Wardens** | Nothing. They are mad. | The six old monarchs, whose sleep holds the Gate. | Each is fought and freed at stage 4 of its land, and joins us. |

**Vael-Orrun** is a tragic villain, not a monster at heart, and the game should let the player pity him by
the end. He speaks rarely. His three forms on wave 39 are **the High King** (crowned, armoured), **the
Sunderer** (the six stolen magics at once) and **the Unmade** (a beast, the Hush showing through him).
He wears a crown-shaped wound in his brow where his crown once sat.

**Cassivane** is not cruel; he is certain. He appears as an ally until the midpoint. Boss of Crossmere
(Converge 1), where he retreats; final form at the capital as **the Sundered Heart** (Converge 3).

**The Six Heralds** (stage 2 of each land):

| Herald | Element | Fought at | Who they were | What they do now |
|---|---|---|---|---|
| **Saltmother Ourra**, the Drowned Herald | Water | Brazier Hold (Ember 2) | High priestess of the Tidefolk. | Walks inside a column of black seawater. Held Brannoc in a salt cage. |
| **Gorrath the Quarried**, the Stone Herald | Earth | Highwind (Storm 2) | A Stoneborn general who held the Kharum Pass for a month. | A carved stone for a heart; breaks into boulders that keep walking. |
| **The Pale Vesper**, the Hollow Herald | Void | Elderhollow (Nature 2) | A Veilwalker singer who sang at funerals. | Sings the dead awake. Dying, says "The Marshal sent us to the Rift." Nobody believes her. |
| **Ashwick the Kindled**, the Flame Herald | Fire | Reedhaven (Water 2) | The Concord's youngest messenger. | An ever-burning boy who never stops running. His satchel still holds a letter under Cassivane's seal. |
| **Vholt Stormcrown**, the Sky Herald | Storm | the Kharum Terraces (Earth 2) | A Galeborn warchief, Kaela's teacher. | Rides a thunderbird of black cloud. Dies at Kaela's lance. |
| **Mother Briar**, the Thorn Herald | Nature | Vesperhold (Void 2) | The wisest healer of the Deepwood. | A thicket in the shape of a woman. Kept Corvin bound in thorns. |

**The mad Wardens** (stage 4 of each land): Cinder Tyrant (Ignar), Thunderhead (Aurath), Elder
Broodmother (Elowen), Tidal Leviathan (Thalassa), Mountain Titan (Orrok), Hollow King (Nyxara). The Hollow
King is Nyxara fighting her madness from inside, which is why it splits in two when it falls.

### 7.6 The secret villain: the Hush (revealed only after the credits, for Part 2)

**Never named, never shown, never explained in Part 1.** Its working name in our docs is the Hush; its
true name is saved for Part 2. It lives deep under the Hollow, older than the Wardens, and cannot reach
the world by itself. It found Vael-Orrun in the vault under burning Vael and taught him the Unmaking, which
is its own breath: magic stopping is the world going quiet. It has lived inside him ever since. When
Vael-Orrun bargained with Cassivane through the crack in the Gate, it was Vael-Orrun speaking; he did not
know whose words they really were. When we turn him to light in The Truth and his light goes home into the
Heartstone, the Hush comes with it, into the middle of our world.

Clues (subtle, none named): Ysolde ends the songs with "That is how the songs tell it"; Aurath and Ignar
both say a voice whispered to them in their madness; Ilyra heard two voices behind the Gate, one that
wept and one that never did; Vael-Orrun's "It was never my own voice. It is still listening."

---

## 8. The story, beat by beat

| # | When | Scene (cinematic id) | What happens |
|---|---|---|---|
| A | Before stage 1 | The Last Lantern (`prologue`) | The songs' version of the old war; Cassivane's lost daughter (grief only); the Gate opens, nobody knows who unlocked it; Oswin drives it back to a cart-wide gap and falls through; the Heralds and the opposite-element floods; Ysolde gives the player the plan: hold each town's road, kill its Herald, free its Warden. |
| B | Before Ember 1 | The Ember Reach (`ember_intro`) | Ignar is mad, the sea climbs the volcano with the Saltmother's army. Fennick briefs us. |
| C | After Ember 2 | The Drowned Herald (`ember_herald`) | The Saltmother (who went to the Rift two years ago, nobody knew why) dies. Brannoc joins. |
| D | After Ember 4 | Ignar, Freed (`ember_warden`) | "Someone whispered in my sleep." The sea drains, the forges relight. Fennick: "One land back. Five to go." |
| E | Before Storm 1 | The Thunder Steppe (`storm_intro`) | Aurath is mad, the storms are still, the Stone climbs the plateau behind Gorrath. |
| F | After Storm 2 | The Stone Herald (`storm_herald`) | Gorrath, also sent to the Rift two years ago, falls. Kaela joins. |
| G | After Storm 4, then 8 stages won | Aurath, Freed (`storm_warden`), then The Refugee Road (`regents_counsel`) | The sky moves again. In Solenne, Cassivane at his kindest: "Every life we lose out there will be paid back." Ysolde recalls exiling Corvin on his word. |
| H | Before Nature 1 | The Verdant Deep (`nature_intro`) | Elowen is mad; the Hollow creeps in behind the Pale Vesper, who raises the Deepwood's dead. |
| I | After Nature 2 | The Hollow Herald (`nature_herald`) | The dying Vesper: "The Marshal sent us to the Rift." Ysolde doesn't believe her. Sylvaine joins. |
| J | After Nature 4, then 12 won | Elowen, Freed (`nature_warden`), then The Night of Falling Stars (`night_of_falling_stars`) | Elowen gives Sylvaine the last seed. That night Cassivane's emptied soldiers open the east gate; Fennick dies holding it; Cassivane breaks the Sunstone and comes for the Heartstone (a sliver of it opened the Gate). Ysolde runs with it and is blinded by the falling light; Tamsin drags her clear. "He has my daughter." Cassivane flees east with the shards; one piece falls into the Rift. The darkness climbs out and covers the sky: the Long Night. |
| K | Water 1-4 (night) | `water_intro`, `water_herald`, `water_warden` | Thalassa is mad, fire runs over the ice. Ashwick dies with a letter under Cassivane's seal; Mirelle joins. Thalassa is freed. Mirelle sees a death at the end of the war. |
| L | Earth 1-4 (night) | `earth_intro`, `earth_herald`, `long_night` (18 won), `earth_warden` | Orrok is mad, armoured lightning in the canyon under Vholt. Kaela kills her teacher; Gorrim joins. The war in the dark; Tamsin reads Fennick's notes. Orrok is freed; Gorrim's last ring. |
| M | Void 1-4 (night) | `void_intro`, `void_herald`, `void_warden` | The Gate seen from the rim; a white light walking at the bottom. Mother Briar dies; Corvin is cut free and says why the murdered man died. Nyxara is freed: "Your Grey Lantern is alive." |
| N | Before Converge 1 | The Convergence (`convergence_intro`) | The oath holds again; only the whole Heartstone can break it, so everything he has left marches on Solenne. Thalassa: "When this is over, I will tell you what we did at Vael." |
| O | After Converge 1 | The Ashen Regent (`crossroads`) | Crossmere saved. Cassivane: "Yes. I opened the Gate... She will be whole when he is free." He leaves Ilyra behind; she recovers on her own and joins. |
| P | After Converge 2 | The Lumen Gate (`lumen_gate`) | Solenne's outer wall falls, the only wall we lose. Seraphel joins. |
| Q | Converge 3 | `capital_prelude`, `dawn` (wave 17), `heart_falls` (or `solenne_falls` if lost) | The Sundered Heart comes for the Heartstone. Ysolde sees a light on the east road. Oswin walks up it with the last piece of the Sunstone and relights it; the dark sinks back into the Rift. Cassivane dies in Ilyra's arms. We march east. |
| R | Final level | `assault_intro`, `the_high_king` (wave 39), `the_turning` (wave 40) | Down the Rift road, through the gap, dig in before Nhal Vorath. 38 waves of defence, Echo-Heralds every sixth wave. Wave 39: Vael-Orrun's three forms, then he flees. Wave 40: we attack the fortress; Brannoc breaks the gate. |
| S | Fortress falls | The Truth (`the_truth`) | Seraphel dies at the inner gate. The Wardens confess the Night of Six Knives. "It was never my own voice." Mirelle's foreseen death was his. Oswin's lantern in the wound in his brow; his light goes home to the Heartstone. |
| T | Then | The Seventh Colour (`epilogue`) | The Wardens seal the Gate. The towns rebuild; Sylvaine plants the seed; Fennick and Seraphel are buried. "I have felt every one of them." Credits. |
| U | After the credits | One Door (`the_hush`) | The Hush's reveal. "Seven crowns. One door. Thank you." |

### Secrets and their payoffs

| Secret | Planted | Hinted | Paid off |
|---|---|---|---|
| Cassivane let the enemy in | Prologue: his lost daughter; nobody knows who unlocked the Gate | Heralds all "went to the Rift two years ago"; Refugee Road: his locket and Corvin's exile; Nature 2: the Vesper names him | Midpoint: he opens the gate and breaks the Sunstone. Water 2: his seal on Ashwick's letter. Void 2: Corvin proved right. Converge 1: his confession. |
| Oswin is alive | Prologue: he falls with his lantern lit | Midpoint: a piece of the Sunstone falls into the Rift; Void 1: a white light walks at the bottom; Nyxara hears him; capital: blind Ysolde sees a light | Converge 3, wave 17: he brings the piece back and relights the Sunstone. |
| Vael-Orrun was wronged, and something used him | Prologue: "That is how the songs tell it." | Ignar and Aurath heard a voice; Thalassa's promise; Ilyra's two voices; Mirelle's foreseen death | The Truth; post-credits: the Hush. |

---

## 9. Final level: 40 waves under Nhal Vorath

The final-level thread builds the mechanics; this is the story fitted to it.

| Wave | What happens | Scene or line |
|---|---|---|
| Before 1 | We come through the Gate and dig in before the fortress. | `assault_intro`. Vael-Orrun, unseen: "You built your city on my city, and you lock my door with my own crown. Come in, then." Tamsin: "For once we're not holding a road, Spirewright. We're on his." |
| 1-38 | Hold the camp. Every sixth wave (6, 12, 18, 24, 30, 36) an echo of one of the six Heralds leads the attack. | Optional barks from the hero each Herald once held. |
| 39 | His army is spent, so he comes out himself, in three forms. After the third he breaks and flees into the fortress. | `the_high_king`: "Six of you. Always six. Ask them what they did at my table." None of the Wardens answer. |
| 40 | The towers keep the camp; heroes and troops attack the fortress. | `the_turning`. Brannoc: "Gates are my trade. Let me." |
| Fortress falls | The truth. | `the_truth` (Seraphel's death opens it), then `epilogue`, then `the_hush`. |

In `data/story/story.json`, `assault.waves` holds the wave scenes and `assault.truth`, `assault.outro` and
`assault.post_credits` play in that order after the win.

### Endings

- **Losing the capital:** a short "Solenne Falls" scene, then retry. There is no bad canon ending.
- **Victory:** The Truth, the Epilogue, the credits, and the post-credits reveal. To be continued in Part 2.

---

## 10. Themes and tone

- **We win, and it costs.** Every town is saved, every land taken back; the price is paid by people we
  know: Fennick, Seraphel, the Queen's eyes.
- **Balance, not purity.** Every element is needed, especially the one across from you. This is the game's
  tower mechanic and its moral.
- **Grief can be a door.** Vael-Orrun and Cassivane are the same story two thousand years apart: good men
  broken by loss, who took the help of a voice in the dark. Never make either a cackling villain.
- **Light is carried.** The Lanternguard, Oswin's lantern, the Long Night, the dawn. Light is the visual
  motif for hope, and it is literal in the lighting system.
- **Tone:** 18+, grave, dark, warm, sometimes funny in small human ways (Tamsin and Brannoc especially),
  never ironic. No modern slang. Short sentences when things are bad.

### Style guide for writing more

- **Write for a player who knows nothing.** Every scene says where we are, what is attacking and why, and
  what changed. Name people and places and give causes. If a line could sit in any fantasy game, cut it or
  make it about this one.
- **Everything physical.** No cracks in the sky, nothing beyond the stars, no road of the dead. Cut terms:
  the Crack, the Outer Hollow, the Unwritten Star, the Ledger of Fallen Cities, the Gatemaw, the Mirror
  Spire, the Crownless Throne. `tools/story/story_content.py` refuses the worst of these.
- Names: Emberfolk names are hard and short (Brannoc, Kethra). Galeborn are breathy (Aurath, Kaela, Vholt).
  Deepwood are soft and long (Sylvaine, Elowen). Tidefolk are liquid (Mirelle, Thalassa, Ourra).
  Stoneborn are heavy (Gorrim, Orrok, Grund, Kharn). Veilwalkers are dark and sharp (Nyxara, Corvin,
  Vesper, Umbrael).
- The six elements are always written Fire, Storm, Nature, Water, Earth, Void (capitalised, ring order).
- Characters talk about their art ("a Kindler", "she sang the storm down", "runecarved steel"), not about
  "using Fire". Arts: Kindling, Stormsong, Rootcraft, Tidelore, Runecarving, Starcraft, the Grand Alchemy
  and its Unmaking, Spirecraft.
- "Warden" means only the six monarchs. Enemies are the Unbound (Hollowed, Risen, Wild). Never "orc",
  "elf" or "dwarf".
- Never call Vael-Orrun "the Dark Lord". He is the High King.
