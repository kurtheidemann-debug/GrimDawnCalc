# Mal optimization results so far

Completed: decoded inventory, baseline reconstruction, three candidate builds, resource and legality audits. Two deterministic optimizer runs produced byte-identical results.

These are calculated estimates from the supplied saves and game data. Offense is a scenario proxy, not measured DPS. The search does not prove a global optimum. The formatted PDF and optimization Excel report remain unfinished.

## Comparison

|Metric|Current|A Balanced|B Offense|C Defense|
|---|---:|---:|---:|---:|
|health|9,509.0|16,538.0|10,753.0|16,336.0|
|OA|2,123.0|2,097.0|2,592.0|1,988.0|
|DA|1,793.0|2,067.0|1,902.0|2,190.0|
|armor|1,213.0|2,030.0|1,295.0|2,031.0|
|armor_absorption|70.0|95.2|89.6|95.2|
|offense_proxy|19,681.1|33,488.9|56,440.4|22,380.5|

All three proposed builds pass the saved source-data legality audits and cap all nine standard resistances. 34 baseline numerical comparisons match the export exactly; this is decoder agreement, not independent live-game validation.

## Inventory workbook

The separate inventory workbook contains the original sortable inventory, with character and shared stash sheets. Stable inventory IDs below identify the proposed items.

## A Balanced

### Equipment

|Slot|Item ID|Item|Owner / location|Component|Augment|
|---|---|---|---|---|---|
|Head|GD0117|Magestorm Ascended Diadem of Attack|Mal /equipment/0|Leathery Hide|Flameweave Powder|
|Amulet|GD0157|Maniacal Putrid Necklace of Mending|Mal /inventory-sacks/0/inventory-items/28|Corpse Dust|Hexxer's Delight|
|Chest|GD0553|Empowered Chestguard of Perdition|Shared Stash /stash/1/inventory-items/28|Ancient Armor Plate|Solarstorm Powder|
|Legs|GD0070|Empowered Swampdweller's Legguards|Beeztrap /inventory-sacks/0/inventory-items/1|Ancient Armor Plate|None|
|Feet|GD0388|Golemborn Greaves|Maldirge /stashes/1/items/35|Mark of the Traveler|None|
|Hands|GD0122|Touch of the Everliving Grove|Mal /equipment/5|Mutated Scales|None|
|Ring1|GD0063|Empowered Obsidian Seal|Beeztrap /equipment/6|Corpse Dust|Hexxer's Delight|
|Ring2|GD0163|Stalwart Imperial Signet of Arcane Balance|Mal /inventory-sacks/1/inventory-items/0|Corpse Dust|Hexxer's Delight|
|Belt|GD0125|Solar Girdle of Tormented Souls|Mal /equipment/8|Dense Fur|Solarstorm Powder|
|Shoulders|GD0486|Dawnguard Epaulets|Shared Stash /stash/0/inventory-items/24|Scaled Hide|Flameweave Powder|
|Medal|GD0127|Druid's Crest of Readiness|Mal /equipment/10|Corpse Dust|None|
|Relic|GD0128|Iskandra's Balance|Mal /equipment/11|None|None|
|Weapon|GD0207|Mystic Ugdenbog Stormstrife of Celerity|Mal /weapon-sets/0/items/0|Imbued Silver|Stardust|
|Offhand|GD0153|Thunderstruck Groble Sky Effigy of Thunder|Mal /inventory-sacks/0/inventory-items/24|Imbued Silver|Stardust|

Final earned attribute points: **47 Physique / 2 Cunning / 26 Spirit**. Use one Tonic of Reshaping (shared stash GD0515) before assigning these totals.

### Skills

|Skill|Invested points|Effective rank|Change|
|---|---:|---:|---:|
|Arcanist|25|25|0|
|Maiven's Sphere of Protection|12|13|0|
|Inner Focus|10|11|-2|
|Mirror of Ereoctes|1|2|0|
|Iskandra's Elemental Exchange|1|4|0|
|Overload|1|4|0|
|Elemental Balance|1|2|-9|
|Panetti's Replicating Missile|1|2|0|
|Distortion|0|0|-1|
|Supercharged|0|0|-1|
|Shaman|50|50|0|
|Mogdrogen's Pact|19|22|9|
|Heart of the Wild|8|11|-1|
|Oak Skin|10|17|1|
|Stormcaller's Pact|1|7|-6|
|Wendigo Totem|1|2|0|
|Wind Devil|1|2|-3|
|Raging Tempest|19|22|7|
|Maelstrom|21|22|9|
|Storm Totem|16|21|0|

### Devotions

|Constellation|Selected star numbers|
|---|---|
|Crossroads|1|
|Tortoise|1,2,3,4,5|
|Crossroads|1|
|Scholar's Light|1,2,3|
|Widow|1,2,3,4,5,6|
|Lotus|1,2,3,4|
|Crossroads|1|
|Panther|1,2,3,4|
|Jackal|1,2,3|
|Ultos, Shepherd of Storms|1,2,4,5,6|
|Sailor's Guide|1,2,3,4|
|Eel|1,2,3|
|Behemoth|1,2,3,4,5,6|
|Korvaak, the Eldritch Sun|1,2,3,4,5|

### Bindings

|Power|Bind to|Proc level|
|---|---|---:|
|Eye of Korvaak|Wind Devil|1|
|Turtle Shell|Mogdrogen's Pact|17|
|Arcane Bomb|Panetti's Replicating Missile|14|
|Giant's Blood|Maiven's Sphere of Protection|14|
|Hand of Ultos|Storm Totem|3|

### Augment purchases

|Augment|Quantity|Faction|Base total iron|
|---|---:|---|---:|
|Flameweave Powder|2|Homestead|8000|
|Hexxer's Delight|3|Coven of Ugdenbog|4500|
|Solarstorm Powder|2|Homestead|8000|
|Stardust|2|Coven of Ugdenbog|3000|

## B Offense

### Equipment

|Slot|Item ID|Item|Owner / location|Component|Augment|
|---|---|---|---|---|---|
|Head|GD0117|Magestorm Ascended Diadem of Attack|Mal /equipment/0|Sanctified Bone|Solarstorm Powder|
|Amulet|GD0162|Stanching Imperial Necklace of Supremacy|Mal /inventory-sacks/0/inventory-items/33|Arcane Lens|Hexxer's Delight|
|Chest|GD0669|Empowered Wildcaller's Skins|Shared Stash /stash/4/inventory-items/5|Chains of Oleron|Solarstorm Powder|
|Legs|GD0070|Empowered Swampdweller's Legguards|Beeztrap /inventory-sacks/0/inventory-items/1|Ancient Armor Plate|Solarstorm Powder|
|Feet|GD0186|Magestorm Exalted Sabatons of Readiness|Mal /inventory-sacks/3/inventory-items/3|Dense Fur|Solarstorm Powder|
|Hands|GD0648|Runic Bracers|Shared Stash /stash/3/inventory-items/31|Spellwoven Threads|Flameweave Powder|
|Ring1|GD0163|Stalwart Imperial Signet of Arcane Balance|Mal /inventory-sacks/1/inventory-items/0|Vengeful Wraith|Hexxer's Delight|
|Ring2|GD0136|Impervious Imperial Signet of Squalls|Mal /inventory-sacks/0/inventory-items/7|Vengeful Wraith|Hexxer's Delight|
|Belt|GD0125|Solar Girdle of Tormented Souls|Mal /equipment/8|Rigid Shell|Flameweave Powder|
|Shoulders|GD0126|Chosen Mantle|Mal /equipment/9|Scaled Hide|None|
|Medal|GD0127|Druid's Crest of Readiness|Mal /equipment/10|Wardstone|None|
|Relic|GD0128|Iskandra's Balance|Mal /equipment/11|None|None|
|Weapon|GD0207|Mystic Ugdenbog Stormstrife of Celerity|Mal /weapon-sets/0/items/0|Oleron's Blood|Stardust|
|Offhand|GD0153|Thunderstruck Groble Sky Effigy of Thunder|Mal /inventory-sacks/0/inventory-items/24|Oleron's Blood|Raincaller Powder|

Final earned attribute points: **37 Physique / 2 Cunning / 36 Spirit**. Use one Tonic of Reshaping (shared stash GD0515) before assigning these totals.

### Skills

|Skill|Invested points|Effective rank|Change|
|---|---:|---:|---:|
|Arcanist|25|25|0|
|Maiven's Sphere of Protection|1|2|-11|
|Inner Focus|11|12|-1|
|Mirror of Ereoctes|1|2|0|
|Iskandra's Elemental Exchange|21|22|20|
|Overload|8|11|7|
|Elemental Balance|1|2|-9|
|Panetti's Replicating Missile|1|2|0|
|Distortion|0|0|-1|
|Supercharged|0|0|-1|
|Shaman|50|50|0|
|Mogdrogen's Pact|1|4|-9|
|Heart of the Wild|1|2|-8|
|Oak Skin|7|10|-2|
|Stormcaller's Pact|12|18|5|
|Wendigo Totem|1|2|0|
|Wind Devil|1|2|-3|
|Raging Tempest|19|22|7|
|Maelstrom|21|22|9|
|Storm Totem|16|23|0|

### Devotions

|Constellation|Selected star numbers|
|---|---|
|Kraken|1,4|
|Crossroads|1|
|Ghoul|1,2,3,4,5|
|Crossroads|1|
|Tortoise|1,2,3,4,5|
|Crossroads|1|
|Scholar's Light|1,2,3|
|Widow|1,2,3,4,5,6|
|Lotus|1,2,3,4|
|Crossroads|1|
|Raven|1,2,3,4|
|Panther|1,2,3,4|
|Jackal|1,2,3|
|Ultos, Shepherd of Storms|1,2,3,4,5,6|
|Behemoth|1,2,3,4,6|

### Bindings

|Power|Bind to|Proc level|
|---|---|---:|
|Arcane Bomb|Panetti's Replicating Missile|14|
|Giant's Blood|Maiven's Sphere of Protection|14|
|Ghoulish Hunger|Stormcaller's Pact|15|
|Turtle Shell|Mogdrogen's Pact|17|
|Hand of Ultos|Storm Totem|3|

### Augment purchases

|Augment|Quantity|Faction|Base total iron|
|---|---:|---|---:|
|Solarstorm Powder|4|Homestead|16000|
|Hexxer's Delight|3|Coven of Ugdenbog|4500|
|Flameweave Powder|2|Homestead|8000|
|Stardust|1|Coven of Ugdenbog|1500|

## C Defense

### Equipment

|Slot|Item ID|Item|Owner / location|Component|Augment|
|---|---|---|---|---|---|
|Head|GD0117|Magestorm Ascended Diadem of Attack|Mal /equipment/0|Leathery Hide|Flameweave Powder|
|Amulet|GD0171|Interrogator's Sylvarria's Root of Mending|Mal /inventory-sacks/1/inventory-items/8|Wardstone|Hexxer's Delight|
|Chest|GD0553|Empowered Chestguard of Perdition|Shared Stash /stash/1/inventory-items/28|Ancient Armor Plate|Flameweave Powder|
|Legs|GD0070|Empowered Swampdweller's Legguards|Beeztrap /inventory-sacks/0/inventory-items/1|Ancient Armor Plate|Solarstorm Powder|
|Feet|GD0388|Golemborn Greaves|Maldirge /stashes/1/items/35|Mark of the Traveler|None|
|Hands|GD0122|Touch of the Everliving Grove|Mal /equipment/5|Mutated Scales|None|
|Ring1|GD0063|Empowered Obsidian Seal|Beeztrap /equipment/6|Corpse Dust|Hexxer's Delight|
|Ring2|GD0732|Empowered Lifebloom Band|Shared Stash /stash/4/inventory-items/68|Corpse Dust|Hexxer's Delight|
|Belt|GD0363|Empowered Frizzick's Utility Pack|Maldirge /stashes/1/items/10|Dense Fur|Solarstorm Powder|
|Shoulders|GD0486|Dawnguard Epaulets|Shared Stash /stash/0/inventory-items/24|Scaled Hide|Flameweave Powder|
|Medal|GD0709|Devastating Imperial Crest of Protection|Shared Stash /stash/4/inventory-items/45|Corpse Dust|None|
|Relic|GD0128|Iskandra's Balance|Mal /equipment/11|None|None|
|Weapon|GD0207|Mystic Ugdenbog Stormstrife of Celerity|Mal /weapon-sets/0/items/0|Imbued Silver|Troll Wart Powder|
|Offhand|GD0153|Thunderstruck Groble Sky Effigy of Thunder|Mal /inventory-sacks/0/inventory-items/24|Purified Salt|Troll Wart Powder|

Final earned attribute points: **73 Physique / 2 Cunning / 0 Spirit**. Use one Tonic of Reshaping (shared stash GD0515) before assigning these totals.

### Skills

|Skill|Invested points|Effective rank|Change|
|---|---:|---:|---:|
|Arcanist|25|25|0|
|Maiven's Sphere of Protection|12|13|0|
|Inner Focus|11|12|-1|
|Mirror of Ereoctes|11|12|10|
|Iskandra's Elemental Exchange|1|2|0|
|Overload|1|2|0|
|Elemental Balance|1|2|-9|
|Panetti's Replicating Missile|1|2|0|
|Distortion|0|0|-1|
|Supercharged|0|0|-1|
|Shaman|50|50|0|
|Mogdrogen's Pact|18|22|8|
|Heart of the Wild|10|12|1|
|Oak Skin|10|18|1|
|Stormcaller's Pact|1|6|-6|
|Wendigo Totem|1|1|0|
|Wind Devil|1|1|-3|
|Raging Tempest|12|14|0|
|Maelstrom|16|16|4|
|Storm Totem|16|20|0|

### Devotions

|Constellation|Selected star numbers|
|---|---|
|Crossroads|1|
|Tortoise|1,2,3,4,5|
|Crossroads|1|
|Scholar's Light|1,2,3|
|Widow|1,2,3,4,5,6|
|Lotus|1,2,3,4|
|Crossroads|1|
|Panther|1,2,3,4|
|Jackal|1,2,3|
|Ultos, Shepherd of Storms|1,2,4,5,6|
|Sailor's Guide|1,2,3,4|
|Eel|1,2,3|
|Behemoth|1,2,3,4,5,6|
|Korvaak, the Eldritch Sun|1,2,3,4,5|

### Bindings

|Power|Bind to|Proc level|
|---|---|---:|
|Eye of Korvaak|Wind Devil|1|
|Turtle Shell|Mogdrogen's Pact|17|
|Arcane Bomb|Panetti's Replicating Missile|14|
|Giant's Blood|Maiven's Sphere of Protection|14|
|Hand of Ultos|Storm Totem|3|

### Augment purchases

|Augment|Quantity|Faction|Base total iron|
|---|---:|---|---:|
|Flameweave Powder|3|Homestead|12000|
|Hexxer's Delight|3|Coven of Ugdenbog|4500|
|Solarstorm Powder|2|Homestead|8000|
|Troll Wart Powder|2|Rovers|2000|

## Limits and application

Buy and apply attachments for one alternative at a time. Donor augments must be removed before transferring affected items. Replaced components may be destroyed. Vendor adjustments, removal fees and respec fees are additional to listed base costs.

Damage and defense comparisons use explicitly simplified encounter models. Proc damage, conversion, damage-over-time stacking and a complete energy rotation are not fully modeled. Inspect results/report-data.json for the exact legality checks, equip order, devotion acquisition order, resistance overcaps and supporting records. Review the changes in game before committing irreversible component replacements.