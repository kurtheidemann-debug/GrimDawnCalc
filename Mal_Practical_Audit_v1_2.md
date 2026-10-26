# Practical Optimizer v1.2 audit

**Resistance math was correct. Offensive scoring needed correction.** The v1.1 search, costs, 5% rule, fixed skills/devotions and defensive floors remain. New results use a small generic scoring layer. The databases and raw save decoder were retained; no game data was re-extracted.

## 1. Ultimate resistance verification

Mal’s imported `last-difficulty` is 2, whose masked difficulty is Ultimate. `records/game/balancingadjustment_mp+difficulty_players01.dbr` stores 12 entries per resistance: four multiplayer sizes for each difficulty. Entries 0, 4 and 8 select Normal, Elite and Ultimate. All four values within each difficulty agree. The imported penalties.json exactly matches entry 8.

Ultimate applies **−50 percentage points** to Fire, Cold, Lightning, Poison & Acid and Pierce; **−25** to Bleeding, Vitality, Aether and Chaos. Physical receives none. These are difficulty-specific totals. Do not subtract Elite’s −25 again. The calculator already adds the selected negative penalty once, before capping and before checking feasible resistance caps/overcaps.

The v1.1 word `raw` meant **after difficulty penalty, before cap**. Its JSON alias remains for compatibility. Explicit before-penalty, penalty and difficulty-adjusted fields were added, and startup now rejects an extracted penalty table that disagrees with the selected difficulty and database. No resistance arithmetic or resistance optimization rule changed.

### v1.1 results on Ultimate

Each cell is **effective before cap / displayed / signed overcap or shortfall**. All nine caps here are 80%. A positive margin is overcap, a negative margin is missing resistance.

|Resistance|Imported current|Minimal cost v1.1|Balanced v1.1|Maximum offense v1.1|
|---|---:|---:|---:|---:|
|Fire|77 / 77 / -3|126 / 80 / +46|120 / 80 / +40|107 / 80 / +27|
|Cold|77 / 77 / -3|102 / 80 / +22|84 / 80 / +4|125 / 80 / +45|
|Lightning|77 / 77 / -3|114 / 80 / +34|108 / 80 / +28|95 / 80 / +15|
|Poison & Acid|33 / 33 / -47|169 / 80 / +89|123 / 80 / +43|125 / 80 / +45|
|Pierce|104 / 80 / +24|103 / 80 / +23|103 / 80 / +23|104 / 80 / +24|
|Bleeding|51 / 51 / -29|106 / 80 / +26|103 / 80 / +23|109 / 80 / +29|
|Vitality|49 / 49 / -31|88 / 80 / +8|85 / 80 / +5|83 / 80 / +3|
|Aether|136 / 80 / +56|81 / 80 / +1|81 / 80 / +1|98 / 80 / +18|
|Chaos|31 / 31 / -49|82 / 80 / +2|82 / 80 / +2|125 / 80 / +45|

Thus 169% Poison is 219% before penalty, 169% after Ultimate, displayed 80%, with +89 overcap. Balanced’s 123% is 173% before penalty, 123% after Ultimate, displayed 80%, with +43 overcap. Both are capped. Imported current equipment calculates to 33% Poison on Ultimate and is short by 47 points. These are different equipment configurations, not conflicting readings of the current save.

All 34 exported baseline numerical comparisons still agree exactly. The save stores equipment/skills, not final resistance totals; agreement is with the imported decoder export and source records, **not an independent live-game screenshot measurement**. The audit also recalculates every old selected state: its resistance totals, health, OA, DA, armor and armor absorption remain unchanged.

## 2. Why v1.1 showed 164.2, 164.4 and 216.2

The old index was 80% relative Totem score + 20% relative Wind Devil score. Its arithmetic reproduces exactly. These were utility-index increases, never measured DPS.

|v1.1 factor|Current|Minimal|Balanced|Maximum offense|
|---|---:|---:|---:|---:|
|Totem effective rank|21|21|21|23|
|Gear bonus to invested rank 16|+5|+5|+5|+7|
|Maximum Totems|4|5|5|5|
|Totems per cast|2|2|2|2|
|Totem cooldown seconds|3.69|2.34|2.34|2.34|
|Lightning bonus percentage points|1615.9|1967.9|1938.9|2019.4|
|Index|100.0|164.2|164.4|216.2|

The snapshot has +5 Totem ranks in current/minimal/balanced gear and +7 in the old offense build. It does not show +9 to an already maxed skill. Effective ranks are read from actual gear and capped by the skill record.

|Old Totem factor relative to current|Minimal|Balanced|Maximum offense|
|---|---:|---:|---:|
|Native rank-based lightning|1.0000×|1.0000×|1.0916×|
|Additive damage-bonus factor|1.2051×|1.1882×|1.2351×|
|OA/critical rating utility|0.9909×|1.0059×|1.1808×|
|Maximum-instance factor|1.2500×|1.2500×|1.2500×|
|Additional cooldown utility|1.1728×|1.1728×|1.1728×|
|Resistance-reduction utility|1.0000×|1.0000×|1.0000×|

Multiplying those rows reproduces the old Totem score. Combining it with the old Wind Devil ratio reproduces each index. Raging Tempest −33, Widow −31 Lightning and Ultos 13% relative reduction were unchanged across these old states, so RR contributed **no relative increase**. Extra Totem capacity and the independent cooldown factor were major contributors.

### Corrections and bounds

- **Generic ability metadata:** follow ranked spawn objects, actor skill links, saved secondary pet modifiers and explicit item-modifier targets. Ability-specific names are no longer embedded in scoring code. Mal’s 80/20 emphasis lives in offense_profile.json; other characters can auto-discover learned damaging abilities and review their baseline contribution weights. The refresh wrapper now accepts `--character NAME`; the underlying decoder is unchanged.
- **Maintainable population:** temporary instances are bounded by maximum count, burst, lifetime and deployment rate, with a closed-form setup discount. Current gear sustains max 4 Totems; old proposed gear sustains max 5. Duration is 14 seconds. Both can maintain their maximum; shorter cooldown is not a second sustained-damage multiplier. Permanent summons are distinguished from temporary ones.
- **Relevant cadence:** player speed affects direct actions and potentially summon deployment. It does not accelerate autonomous player-scaling attacks. Permanent Wind Devils receive no sustained attack increase from player CDR. Maelstrom has a 2-second DB target interval. Missing animation/AI cadence is normalized and flagged.
- **Damage channels:** effective ranks select actual base damage. Relevant additive damage bonuses, recognized flat skill modifiers and one-time local/global conversion use their respective damage channels. Player stats and regular-pet bonuses are separate. DoT refresh is capped by coverage; same-source repeat applications do not multiply it by attack frequency. Separate attacking summons can contribute separate DoT sources; identical debuff auras apply once.
- **RR:** distinct additive debuffs sum; same-source effects deduplicate; flat/relative categories take their strongest applicable value. Order is additive, relative, flat. The model reports all categories. Without inventing an enemy resistance, it uses an additive+flat comparison utility and gives relative reduction no unconditional damage multiplier. It includes saved profiled support skills and offensive devotion bindings. Proc uptime is not claimed.

For context, another +100 percentage points of Lightning at the current +1615.9% is about **5.8% more direct Lightning**, not +100% more total damage. At the old minimal build’s +1967.9%, it is about **4.8%**. Other damage channels reduce its overall impact. Player cast speed adds no autonomous Totem attack-speed multiplier.

### Same old gear, revised index

This isolates the scoring correction from subsequent equipment search changes. These are model-relative indices, not precise damage forecasts.

|Old equipment state|v1.1 index|Revised index on the same gear|
|---|---:|---:|
|Current|100.0|100.0|
|Minimal cost|164.2|137.4|
|Balanced|164.4|138.2|
|Maximum offense|216.2|181.1|

## 3. Excess resistance valuation

The existing formula was already correct: each resistance earns modest benefit through +20 overcap, then stops. It never subtracts value for incidental excess. Removing Poison above cap+20 from each old result produces **exactly zero change** in resistance utility. Poison at 100, 123 or 169 therefore earns the same Poison score. The optimizer cannot earn a higher score merely by moving Poison from 123 to 169 while losing other stats. It can choose a Poison-heavy item because of its health, other resistances, skills or low cost.

No resistance-weight change was needed. A regression protects this saturation. Capped resistance is still a hard requirement, so gaining required Poison while losing optional damage can be an intentional survival trade. Useful overcap remains a modest secondary benefit; excessive Poison is neither a target nor a penalty.

## 4. Regenerated equipment results

The scoring correction changed some recommendations. Full item IDs, source locations, all components/augments, current-equipment actions and faction eligibility are in Mal_Practical_Results.md. The three outputs below retain fixed saved skill/devotion selections and bindings; no attribute reset is used.

|Build|Offense index|Health|OA|DA|Armor|Absorption|Physical resist|New attribute points|
|---|---:|---:|---:|---:|---:|---:|---:|---:|
|Minimal cost|137.4|11217|2053|1994|1426|100.0%|2%|1|
|Balanced|137.4|11721|2053|1994|1426|100.0%|2%|1|
|Maximum offense|182.6|12641|2461|1929|1210|98.0%|5%|1|

### Revised resistance totals on Ultimate

Cells again mean **effective before cap / displayed / signed margin**. All caps here are 80%.

|Resistance|Minimal|Balanced|Maximum offense|
|---|---:|---:|---:|
|Fire|126 / 80 / +46|126 / 80 / +46|101 / 80 / +21|
|Cold|102 / 80 / +22|102 / 80 / +22|107 / 80 / +27|
|Lightning|114 / 80 / +34|114 / 80 / +34|89 / 80 / +9|
|Poison & Acid|169 / 80 / +89|169 / 80 / +89|138 / 80 / +58|
|Pierce|103 / 80 / +23|103 / 80 / +23|86 / 80 / +6|
|Bleeding|106 / 80 / +26|106 / 80 / +26|86 / 80 / +6|
|Vitality|88 / 80 / +8|88 / 80 / +8|93 / 80 / +13|
|Aether|81 / 80 / +1|81 / 80 / +1|98 / 80 / +18|
|Chaos|82 / 80 / +2|82 / 80 / +2|91 / 80 / +11|

### Changes from each v1.1 recommendation

These are differences from the previous recommendation, not from current equipped gear. The separate results file lists actions from current gear.

**Minimal cost**
- Equipment and attachments unchanged.

**Balanced**
- Chest: GD0553 Empowered Chestguard of Perdition → GD0669 Empowered Wildcaller's Skins; augment: records/items/enchants/c08a_enchant.dbr → None
- Hands: component: None → records/items/materia/compa_mutatedscales.dbr
- Ring2: component: records/items/materia/compa_corpsedust.dbr → records/items/materia/compa_soulshard.dbr; augment: records/items/enchants/a114a_enchant.dbr → records/items/enchants/a18a_enchant.dbr
- Medal: component: records/items/materia/compa_corpsedust.dbr → records/items/materia/compa_wardstone.dbr
- New attribute spending: [8, 0, 0] → [1, 0, 0] (Physique/Cunning/Spirit).

**Maximum offense**
- Amulet: GD0171 Interrogator's Sylvarria's Root of Mending → GD0157 Maniacal Putrid Necklace of Mending; component: records/items/materia/compa_wardstone.dbr → records/items/materia/compa_corpsedust.dbr
- Shoulders: component: records/items/materia/compa_silkswatch.dbr → records/items/materia/compa_scalyhide.dbr; augment: None → records/items/enchants/c08a_enchant.dbr
- Weapon: augment: records/items/enchants/a27a_enchant.dbr → records/items/enchants/a101a_enchant.dbr
- Offhand: augment: records/items/enchants/a27a_enchant.dbr → records/items/enchants/a101a_enchant.dbr

## Limits, checks and retained behavior

24 tests pass: the original 16 plus eight focused resistance, direct-damage, deployable, pet, conversion/RR and saturation checks. All original test files remain unchanged. The final selected states pass resource checks, fixed-build guards, equip-order checks, defensive floors and all nine caps. An unchanged-input rerun uses the existing hash cache, now including the scoring module and profile.

The model does not solve animations, pet survival/AI, shotgun overlap, WPS/weapon payload or all special engine interactions. Unsupported weapon payload is omitted and flagged; a build without supported offensive payload cannot receive invented strength. Root modifiers with uncertain distribution receive conservative scope. DoT left behind by retired summons is not credited. Rank/instance mechanics from DB are strong evidence; the setup window, ability weights, OA rating and RR utility remain explicit comparison policies. The goal is stable gear ranking, not simulated DPS or a global optimum. No formatted PDF/Excel report was added.

Primary mechanics references:
- [Crate combat guide: damage bonuses, pets, stacking and conversion](https://www.grimdawn.com/guide/gameplay/combat/).
- [Controlled RR stacking/order tests](https://forums.crateentertainment.com/t/actual-resist-reduction-formula/47174).
- [DB-backed discussion of attacking pseudo-pets versus nonstacking debuff auras](https://forums.crateentertainment.com/t/stacking-dot-on-pseudo-pets/110592).
- Supplied game database: the balancing record above and ability/actor records listed in results.json. Database values, rather than a web summary, determine the penalties and native skill mechanics used here.