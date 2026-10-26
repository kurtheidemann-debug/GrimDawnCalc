# Beeztrap Cadence validation — Task 2C

**Result:** the standalone scorer passes its bounded validation after correcting a material duplicate-attachment defect. Search integration remains **DISABLED**. No full equipment search, new loadout recommendation, skill/devotion change, or subsequent optimization phase was performed.

The corrected baseline is 100 in all 32 scenarios. Eleven predetermined real-item comparisons were evaluated. No tested candidate qualifies as a robust offensive improvement. Unsupported candidates retain diagnostic direct-offense indices, which are not certified total-DPS rankings.

## Material defect found and corrected

The normalized catalog's `records` array already contains saved components and augments. Task 2B's scorer appended the selected attachments to that array again. Consequences:

- Saved attachment effects entered conversion and conditional-bonus accounting twice.
- Replacing an attachment could leave the old saved attachment in the scorer's semantic records.
- The current two Bloodrose Thorn augments each have a 10%-chance +200% all-damage field. The chance discount was erroneously 720 percentage points instead of 360. Existing full-strength all-damage total 445 therefore became an invalid -275, rather than the corrected expected-value total 85 before scenario Momentum. This was material to damage scaling and candidate comparisons.

The fix rebuilds live source records from base item, affixes, completion/ascended records and the selected attachments, each once. Targeted skill modifiers use those same live records. It does not alter the preserved stat calculator, normalized inventory, save decoder or search engine.

The Task 2B assumptions also incorrectly attributed those chance fields to Vicious Spikes. They are Bloodrose Thorn augment fields. The current assumptions document corrects the label. Pristine Task 2B module, assumptions and baseline output are archived inside this checkpoint.

## Baseline and accounting checks

- Current weapons: GD0321 main hand, GD0322 offhand. Saved Elite difficulty.
- All 32 baseline normalized indices: 100.000000 within floating-point tolerance. Full per-scenario strengths, scenario branches and comparisons are retained in `Cadence_Task2C_Comparisons.json`.
- OA 2175; DA 1852; health 10242; armor 1453; absorption 90.3%; physical resistance 3%. These reproduce the imported calculator baseline; no live game measurement is claimed.
- Recognized global attack-speed modifier: +60%. This is not verified attacks per second.
- Both hands have a 100% base armor-piercing field; their flat payloads remain separate. The Slicer's 13.587144613265991% Physical-to-Chaos conversion is global.
- Deadly Momentum: effective rank 13; five-second duration. Its Physical flat 126–167 and additive damage field 108 enter each buff-on branch once. The saved inactive flag contributes nothing to the pre-scenario baseline. Marking it active in a regression fixture yields identical corrected scenario scores after removal from inherited totals.
- Fixed invested skills, devotions, bindings and saved character data remain unchanged. Effective ranks can change with candidate gear; these are reported in the machine-readable comparisons.

## Controlled real-item comparisons

Every replacement below keeps the original slot's Vicious Spikes and Bloodrose Thorn selected, so weapon differences can be inspected without mixing in attachment changes. These attachments are hypothetical applications to the replacement weapon, not claims that its source copy already carries them. Source attachment IDs are preserved in the comparison JSON. The current-equipment and weapon-swap controls retain their actual attachment pairs.

These are validation controls, not equip instructions. No crafting-cost optimization or new shopping list was produced.

| Control | Main / offhand IDs | Min index | Max index | Robust >5% in every scenario? | Blocker |
|---|---|---:|---:|---|---|
| Current equipment | GD0321 / GD0322 | 100.000 | 100.000 | No | None |
| Swap current swords | GD0322 / GD0321 | 100.000 | 101.281 | No | None |
| Shared Sabre in offhand | GD0321 / GD0509 | 103.636 | 103.678 | No | None |
| Shared Sabre in main hand | GD0509 / GD0322 | 104.910 | 108.580 | No | Unsupported delta |
| Empowered Willie's Razor in main hand | GD0191 / GD0322 | 102.848 | 104.959 | No | Unsupported delta |
| Empowered Willie's Razor in offhand | GD0321 / GD0191 | 100.914 | 102.091 | No | Unsupported delta |
| Puncturing Slicer in main hand | GD0196 / GD0322 | 96.352 | 97.960 | No | Unsupported delta |
| Crystallum in main hand | GD0241 / GD0322 | 78.414 | 86.366 | No | Unsupported delta |
| Crystallum in offhand | GD0321 / GD0241 | 81.060 | 90.532 | No | Unsupported delta |
| Armaggedon in main hand | GD0431 / GD0322 | 79.487 | 87.955 | No | Unsupported delta |
| Edge of Death in offhand | GD0321 / GD0433 | 84.411 | 91.937 | No | Unsupported delta |

A value above 105 in only some scenarios is insufficient. The main-hand shared Sabre's 104.910–108.580 range fails the strict threshold even before its blocker. The unblocked offhand shared Sabre is consistently better in this direct model, but its approximately 3.6% gain is immaterial under the existing rule.

### Exact real items and source locations

| ID | Item | Owner | Inventory location |
|---|---|---|---|
| GD0321 | Void-Touched Dermapteran Slicer of Alacrity | Beeztrap | `/weapon-sets/0/items/0` |
| GD0322 | Empowered Duelist's Sabre | Beeztrap | `/weapon-sets/0/items/1` |
| GD0509 | Empowered Duelist's Sabre | Shared Stash | `/stash/1/inventory-items/32` |
| GD0191 | Empowered Willie's Razor | Maldirge | `/stashes/0/items/21` |
| GD0196 | Puncturing Dermapteran Slicer of Untamed Fangs | Maldirge | `/stashes/0/items/26` |
| GD0241 | Crystallum | Maldirge | `/stashes/1/items/24` |
| GD0431 | Armaggedon | Shared Stash | `/stash/0/inventory-items/26` |
| GD0433 | Edge of Death | Shared Stash | `/stash/0/inventory-items/28` |

Each selected component is `records/items/materia/compa_viciousspikes.dbr`; each selected augment is `records/items/enchants/b05a_enchant.dbr`. Availability means present in the imported catalog, not necessarily owned by Beeztrap personally. These controls use distinct real item IDs, never a duplicated copy of the same inventory object.

### Defensive changes from current equipment

Values below are deltas except absorption, which is a percentage-point delta. Armor and physical resistance are listed independently from offense. No defensive utility is hidden in the offense indices.

| Control | Health Δ | OA Δ | DA Δ | Armor Δ | Absorption Δ | Physical res Δ | Level / final attributes |
|---|---:|---:|---:|---:|---:|---:|---|
| Current equipment | +0 | +0 | +0 | +0 | +0.0 | +0 | Pass |
| Swap current swords | +0 | +0 | +0 | +0 | +0.0 | +0 | Pass |
| Shared Sabre in offhand | +2 | +0 | +0 | +0 | +0.0 | +0 | Pass |
| Shared Sabre in main hand | -196 | +0 | +0 | +0 | +0.0 | +0 | Pass |
| Empowered Willie's Razor in main hand | -411 | +105 | +0 | +34 | +0.0 | +0 | Pass |
| Empowered Willie's Razor in offhand | -213 | +105 | +0 | +34 | +0.0 | +0 | Pass |
| Puncturing Slicer in main hand | -105 | +26 | +0 | +0 | +0.0 | +0 | Pass |
| Crystallum in main hand | -429 | +0 | +0 | +0 | +0.0 | +0 | Pass |
| Crystallum in offhand | -231 | +0 | +0 | +0 | +0.0 | +0 | Pass |
| Armaggedon in main hand | -429 | +0 | +0 | +0 | +0.0 | +0 | Pass |
| Edge of Death in offhand | +347 | +29 | +18 | +10 | +2.1 | +0 | Pass |

“Pass” checks level and final equipment attribute requirements with the current four unspent attribute points untouched. It is not an equip-order, stock, attachment-cost or defensive-floor certification.

### Elite resistance values before caps

The table uses saved-Elite penalties and uncapped effective values. For these controls the standard caps remain 80%; displayed values are capped there. Projected Ultimate values are 25 points lower in each of these nine columns. Physical resistance is unchanged by difficulty.

| Control | Fire | Cold | Lightning | Poison/Acid | Pierce | Bleeding | Vitality | Aether | Chaos |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Current equipment | 72.0 | 92.0 | 72.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Swap current swords | 72.0 | 92.0 | 72.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Shared Sabre in offhand | 72.0 | 92.0 | 72.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Shared Sabre in main hand | 72.0 | 92.0 | 72.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Empowered Willie's Razor in main hand | 72.0 | 92.0 | 72.0 | 90.0 | 160.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Empowered Willie's Razor in offhand | 72.0 | 92.0 | 72.0 | 90.0 | 160.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Puncturing Slicer in main hand | 72.0 | 92.0 | 72.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Crystallum in main hand | 84.0 | 104.0 | 84.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Crystallum in offhand | 84.0 | 104.0 | 84.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Armaggedon in main hand | 72.0 | 92.0 | 72.0 | 90.0 | 157.0 | 89.0 | 65.0 | 88.0 | 89.0 |
| Edge of Death in offhand | 74.0 | 94.0 | 74.0 | 90.0 | 157.0 | 93.0 | 65.0 | 88.0 | 89.0 |

## Explainability checks

**Weapon swapping:** unchanged global speed, conversion, OA and defenses; symmetric-hand scenarios remain at 100. Main-heavy scenarios favor the Sabre's greater intrinsic Physical mean (73 versus 61), producing up to 1.281% gain. This is sensitivity to the documented hand-weighting assumption, not proof of exact in-game discharge selection.

**Attack speed:** GD0509 is another real Empowered Duelist's Sabre. In the offhand it increases the recognized global attack-speed modifier from 60 to 65 while leaving conversion unchanged. Its Pierce roll/bonus also differs. The observed 3.636–3.678% increase is therefore not presented as a pure attack-speed experiment. Separate speed-function regression controls confirm monotonicity below the assumed cap, saturation at the cap, and slower-hand sensitivity.

**Conversion and armor piercing:** routing a control payload of 100 native Physical through baseline global conversion and a 100% piercing hand yields:
`{"Chaos": 13.587144613265991, "Pierce": 86.41285538673401}`

The Chaos portion is not pierced again. Removing the Slicer removes its global Chaos conversion from both hands. Crystallum and other non-piercing swords preserve far more damage outside Beeztrap's strongest Pierce channel, explaining their lower diagnostic direct indices despite reasonable intrinsic base damage. Those candidates also change unsupported effects, so this is a model explanation rather than a certified overall ranking.

**Cadence/WPS modifiers:** the Slicer retains +24 weaponDamagePct specifically on AQC, and +80 Pierce specifically on Whirling Death. Replacement with another Slicer retains those targeted records; replacement with a Sabre removes them. No such modifier becomes generic character flat damage or multiplies the entire two-hand discharge. WPS effective-rank and crit/DoT changes can trigger blockers.

**Deadly Momentum:** every scenario was checked against the weighted whole buff-off/buff-on branches. Buff-on direct offense exceeds buff-off. The active-in-save reconciliation regression passes. No rotation or encounter timeline was simulated.

## Unsupported-mechanics blockers by candidate

The exact common blocker is `DoT, crit, RR or conditional/proc mechanics changed outside the direct-offense envelope`. The following changed field names explain why certification was withheld; they do not imply every listed field is offensive or harmful. The conservative signature can over-block benign changes.

- **Shared Sabre in main hand:** `offensiveSlowBleedingDurationMin`, `offensiveSlowBleedingMin`, `offensiveSlowDefensiveAbilityDurationMin`, `offensiveSlowDefensiveAbilityMin`.
- **Empowered Willie's Razor in main hand:** `defensiveCold`, `defensiveLife`, `defensivePierce`, `defensivePoison`, `offensiveCritDamageModifier`, `offensivePercentCurrentLifeMin`, `offensiveSlowBleedingDurationMin`, `offensiveSlowBleedingDurationModifier`, `offensiveSlowBleedingMax`, `offensiveSlowBleedingMin`, `offensiveSlowBleedingModifier`, `offensiveSlowColdDurationMin`, `offensiveSlowColdMin`, `offensiveSlowColdModifier`, `offensiveSlowLifeDurationModifier`, `offensiveSlowLifeModifier`.
- **Empowered Willie's Razor in offhand:** `defensiveCold`, `defensiveLife`, `defensivePierce`, `defensivePoison`, `itemSkillName`, `offensiveCritDamageModifier`, `offensivePercentCurrentLifeMin`, `offensiveSlowBleedingDurationMin`, `offensiveSlowBleedingDurationModifier`, `offensiveSlowBleedingMax`, `offensiveSlowBleedingMin`, `offensiveSlowBleedingModifier`, `offensiveSlowColdDurationMin`, `offensiveSlowColdMin`, `offensiveSlowColdModifier`, `offensiveSlowDefensiveAbilityDurationMin`, `offensiveSlowDefensiveAbilityMin`, `offensiveSlowLifeDurationModifier`, `offensiveSlowLifeModifier`.
- **Puncturing Slicer in main hand:** `offensiveCritDamageModifier`, `offensiveSlowBleedingModifier`, `offensiveTotalDamageModifierChance`.
- **Crystallum in main hand:** `itemSkillName`, `offensiveCritDamageModifier`, `offensiveSlowBleedingDurationMin`, `offensiveSlowBleedingMin`, `offensiveSlowBleedingModifier`, `offensiveSlowLightningModifier`, `offensiveTotalDamageModifierChance`.
- **Crystallum in offhand:** `itemSkillName`, `offensiveCritDamageModifier`, `offensiveSlowBleedingModifier`, `offensiveSlowDefensiveAbilityDurationMin`, `offensiveSlowDefensiveAbilityMin`, `offensiveSlowLightningModifier`, `offensiveTotalDamageModifierChance`.
- **Armaggedon in main hand:** `itemSkillName`, `offensiveCritDamageModifier`, `offensiveSlowBleedingDurationMin`, `offensiveSlowBleedingMin`, `offensiveSlowBleedingModifier`, `offensiveSlowPhysicalModifier`, `offensiveTotalDamageModifierChance`.
- **Edge of Death in offhand:** `itemSkillName`, `offensiveCritDamageModifier`, `offensiveSlowBleedingDurationMin`, `offensiveSlowBleedingMin`, `offensiveSlowBleedingModifier`, `offensiveSlowDefensiveAbilityDurationMin`, `offensiveSlowDefensiveAbilityMin`, `offensiveSlowLifeModifier`, `offensiveSlowPhysicalDurationMin`, `offensiveSlowPhysicalMax`, `offensiveSlowPhysicalMin`, `offensiveSlowPhysicalModifier`, `offensiveTotalDamageModifierChance`.

## Limitations and disposition

- The duplicate-attachment error was material and has been corrected only in the standalone scorer. Its earlier numerical comparisons should not be relied on. Baseline normalization alone would not have exposed it, because any broken scorer can divide itself by itself and return 100.
- No additional change to the scenario model was made. Its frequencies, accompanying-hand credit, base-speed proxies and Momentum uptime remain assumptions, not proven bounds.
- Omitted DoT, RR, crit/proc uptime, arbitrary new mechanics and exact seeded intrinsic damage remain limitations. Diagnostic indices must not be treated as total DPS, especially when blockers are present.
- The scaler's special cases for generated Physical damage and conversion conservation pass the retained tests. Mixed-hand native skill-flat routing remains approximate as documented in Task 2A.
- Current baseline defenses have gaps on Elite and larger projected Ultimate gaps. None of the weapon-only validation controls repairs the full defensive loadout. Existing defensive recommendations remain unchanged.
- Search integration stays **DISABLED**, including after this correction. The exercise establishes a more defensible standalone comparison tool, not permission to launch an optimizer search.

## Regression and preservation results

All **42 tests passed**: all 38 existing tests plus four focused validation regressions. The new tests cover single-count chance augments, replacement without stale attachment records, the real shared Sabre's global speed change, and whole-branch Momentum averaging. The preservation validator also passed its 34 baseline numeric checks, fixed-build checks, prior selected-loadout checks and original-v1.2/Mal preservation checks.

The supplied Task 2B checkpoint ZIP was checked against its retained SHA-256 and all ZIP CRCs before work. The complete Task 2C checkpoint is independently CRC-tested and accompanied by a SHA-256 verification file. No full equipment optimization was performed. Task 2C stops here.

