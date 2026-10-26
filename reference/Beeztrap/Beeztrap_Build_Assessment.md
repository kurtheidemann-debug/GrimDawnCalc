# Beeztrap build assessment

**Level 74 Soldier/Nightblade Blademaster, saved difficulty Elite. Dual-wield Cadence is preserved.** Imported 761 inventory entries across the characters and shared stash. Native-bound donor items remain excluded; this selected repair borrows no gear.

## What v1.2 can and cannot establish

The core stat calculator reproduces all 34 imported baseline numerical comparisons exactly. Current values are 10,242 health, 2,175 OA, 1,852 DA, 1,453 armor and 90.3% absorption. This confirms agreement with the decoder export, not an independent live-game measurement.

v1.2 does not implement the primary mechanics needed for this build: `weaponDamagePct`, charged-finale Cadence, Deadly Momentum timed-buff coverage, dual-wield weapon allocation, armor-piercing routing and Cadence/WPS sequencing. Automatic offensive discovery selects Blitz/Shadow Strike/Ring of Steel rather than Cadence. Using that index to optimize this build would be misleading. No aggregate offense number, maximum-offense proof, or weapon-upgrade claim is made here.

The scope was therefore limited to validated defensive attachment repairs. Both swords, their weapon components and weapon augments are unchanged. Gear, all invested skills, devotions, devotion bindings and the primary hotbar are unchanged. The three constrained profiles converge on one repair; the requested maximum-offense configuration is **not established**.

## Saved skill configuration

|Skill|Invested|Current effective|Selected effective|DB WPS weight if applicable|
|---|---:|---:|---:|---:|
|Cadence|15|16|16|—|
|Fighting Form|1|2|2|—|
|Deadly Momentum|12|13|13|—|
|Oleron's Rage|12|15|15|—|
|Field Command|4|7|7|—|
|Markovian's Advantage|1|4|4|20.0|
|Pneumatic Burst|2|5|5|—|
|Dual Blades|16|16|16|—|
|Belgothian's Shears|1|1|1|12.0|
|Amarasta's Quick Cut|1|5|5|20.0|
|Whirling Death|1|3|3|17.0|
|Execution|4|4|4|19.0|

Cadence’s effective rank 16 has a **430% weapon-damage field** and charge-level field 2. v1.2 omits that weapon-damage payload. Deadly Momentum is effective rank 13; its linked buff lasts 5 seconds and carries 108% total-damage modifier in the supplied database. WPS weights above are raw DB activation weights, not proportions of the full Cadence cycle. They are not multiplied into a simulated attack sequence.

## Damage, conversion and sustain

The current swords are a Void-Touched Dermapteran Slicer of Alacrity and an Empowered Duelist’s Sabre. Both records have a 100% armor-piercing field. The Slicer’s Void-Touched affix also has rolled Physical-to-Chaos conversion. The build therefore needs physical/pierce routing and its off-type conversion handled correctly before ranking replacements. Current global recognized bonuses are +1419% Pierce, +586% Physical and +453% Internal Trauma, before separately accounting for attributes/conditional effects. The source data includes Cold and other secondary WPS damage. These do not justify abandoning the saved build.

Recognized attack-speed bonus is +60%; absolute displayed attack speed/APS is not validated. Recognized attack damage converted to health is 5%; active Pneumatic Burst is effective rank 5. The persistent flat regeneration input is 18, not a complete in-combat regeneration/healing estimate. No boss-healing simulation was added.

## Defensive finding and selected changes

Current Elite Fire and Lightning are 72% and Vitality is 65%, below their 80% caps. The repair caps all nine Elite resistances, raises DA to 1900, health to 10603, armor to 1512 and absorption to 93.8%, with no equipment swaps and no attribute spending. The exact two component changes and eight augment actions are:
- Head: Augment None → Solarstorm Powder
- Amulet: Augment Bloodrose Thorn → Colossus Spine
- Chest: Augment None → Solarstorm Powder
- Legs: Augment None → Kingsguard Powder
- Feet: Augment None → Mankind's Vigil
- Hands: Augment None → Mankind's Vigil
- Ring1: Component Roiling Blood → Mark of Illusions (old component destroyed); Augment Bloodrose Thorn → Arkovian Rose Powder
- Ring2: Component None → Soul Shard; Augment None → Hexxer's Delight

Projected Ultimate gaps are reported separately in Beeztrap_Practical_Results.md; Elite success is not Ultimate readiness.

A small Beeztrap-only requirement check accounts for weapon/jewelry-specific attribute requirement reductions conservatively (multiplicatively with global reduction). The v1.2 generic check ignored these and falsely demanded Spirit for an already eligible ring. The core stat calculator was not changed. The four unspent attribute points are preserved.

## Verification and limits

- Existing v1.2 regression suite: 24 tests pass; files and Mal benchmark results preserved.
- Selected-state checks: all 34 baseline comparisons, no skill/devotion/binding changes, no weapon/weapon-attachment changes, all Elite caps, material stock, faction eligibility, equip order and attribute budget pass.
- Component-cost arithmetic and the anchored 5% preference function are inherited unchanged. Since total weapon offense is unscored, that preference cannot certify a 5% Cadence-DPS band.
- No full melee scoring implementation, new combat mechanics, PDF or Excel reports were introduced.

Sources: supplied save and normalized game database. [Crate combat guide](https://www.grimdawn.com/guide/gameplay/combat/) explains weapon damage and life steal; [Cadence/DW/WPS testing](https://forums.crateentertainment.com/t/cadence-dual-wield-and-wps-explained/102470) illustrates why a naive multiplier is insufficient. These are reasons to withhold unsupported offensive rankings, not to simulate a different build.