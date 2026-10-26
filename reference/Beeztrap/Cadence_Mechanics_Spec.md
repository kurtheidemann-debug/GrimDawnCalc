# Cadence mechanics specification

**Task 2A — mechanics verification only**  
Research date: 24 October 2026. Starting point: Grim Dawn Practical Optimizer v1.2, Cadence Checkpoint 1.

**Conclusion:** damage ownership and conversion rules are sufficiently established to specify a per-hand input model. Exact melee Cadence cycle shares are not established for Beeztrap's installed game version. Relative weapon ranking must retain that uncertainty, particularly when weapons change WPS ranks, attack speed, hand assignment, or targeted modifiers. Do not enable a single supposedly verified Cadence multiplier from these findings.

No optimizer files were modified, no formulas implemented, and no equipment searches run. Task 2B was not started. An early findings document was saved before this completed specification.

## Evidence standard

- **A — verified official/data:** explicit developer documentation, official patch notes, or fields directly inspected in the checkpoint's extracted database. Database fields verify inputs, not undocumented engine execution.
- **B — supported mechanics:** credible community guides or first-hand tests. Suitable for documented working rules, with version and scope qualifications; not developer confirmation.
- **U — unresolved:** insufficient evidence or a conflict requiring a conservative assumption or further validation.

“Optimizer v1.2” is the project's version, not proof of the installed game's patch. The extracted Cadence record matches the post-game-v1.2.1.0 charge-time value, but this does not identify the full executable build or prove its animation behavior.

## 1. Charge progression and hand selection

| Rule | Status and evidence | Implication for relative gear ranking |
|---|---|---|
| Cadence is a charged finale, with two charges preceding discharge. Its listed offensive payload belongs to the discharge, not every ordinary charge-building attack. | **A/B:** `cadence1.dbr` has `Class=Skill_WeaponPool_ChargedFinale`, `skillChargeLevel=2`; skill text describes the third single-weapon strike. [S8], corroborated by [S9]. | Separate charge-building damage from discharge damage. Do not put the discharge's weapon-damage percentage on every attack. |
| Melee charge timing is gated. Crate changed its internal charge cooldown from 0.5 to 0.35 seconds in game v1.2.1.0. | **A:** official Soldier patch notes [S2]; checkpoint `skillChargeTime=0.35`. | A pre-change cycle estimate cannot be assumed valid. This field is not the interval between all attacks. |
| Default dual-wield animations can use either hand alone or both. First-hand testing reports 25% main-only, 25% off-only, 50% double swing for the base selection. | **B:** [S3], section 2. These are animation-selection proportions, not certified discharge-damage hand proportions. | Keep hands separate. Do not assume strict alternating attacks or equal Cadence damage from each hand. |
| A second-hand hit accompanying discharge can provide a charge toward the next cycle. | **B:** [S3], section 3. Its tests also describe timing-dependent missed charges and WPS-dependent behavior. | “One discharge every three attack animations” is unsafe. Fixed saved skills do not make cycle timing independent of gear. |
| Which hand receives discharge damage is not equivalent to which animation plays. | **B/U:** [S4], post 63, reports normally main-hand discharge; post 66 distinguishes single-hand and double-hand animations. A complete probability distribution for the current installed build is absent. | Do not assume a symmetric score under weapon swapping. Stronger-main-hand advice is plausible, not numerically certified here. |

**Unresolved cycle detail:** exact discharge frequency, charge losses, and hand weighting for Beeztrap's five-WPS combination. No numerical cycle fraction is authorized. The checkpoint does not contain verified hit-frame timing. Miss/fumble effects on charging were not established in this pass.

## 2. Cadence discharge and WPS

| Rule | Status and evidence | Implication for relative gear ranking |
|---|---|---|
| Cadence is not another randomly selected entry in the WPS probability pool. | **B:** Ceno's clarification, [S9], post 14. | Do not add a 33% Cadence entry to Beeztrap's WPS weights or renormalize them against it. |
| A discharge cannot simply be treated as a normal WPS attack multiplied wholesale by Cadence. | **B:** [S4], posts 64–66: correction reports Cadence replacing one damage contribution while another hand can retain WPS damage. | Do not multiply the whole two-hand WPS payload by Cadence's percentage. Conversely, do not erase all WPS contribution from every discharge animation. |
| Hit count follows the animation, not merely the randomly selected WPS damage coefficient. | **B:** [S4], post 66: an AQC animation can retain additional hits; selecting AQC damage with a base double-swing animation does not manufacture a third hit. | AQC's effective rank and coefficient alone cannot establish its complete cycle contribution. |
| Ordinary WPS pools use activation weights; a pool exceeding 100% uses relative frequencies. | **A:** official guide, “Passively Activated Weapon Skills,” [S1]. | Beeztrap's observed raw total of 88 is an eligibility-pool input, not 88% of total cycle damage. |

**Important correction to older references:** the simplified statement that the third strike never activates WPS, found in [S7], is inadequate for calculating the entire dual-wield animation. Later first-hand corrections in [S4] preserve an offhand WPS damage contribution. [S3]'s original assumption of a plain 100%-weapon-damage offhand on base discharge was itself corrected. Neither simplified claim should be encoded as universal behavior.

## 3. Weapon-local versus global damage and speed

| Rule | Status and evidence | Implication for relative gear ranking |
|---|---|---|
| Flat damage printed directly on a weapon belongs to that weapon. Non-weapon shared flat damage contributes through weapon damage. | **A/B:** official flat-damage rule [S1]; shared-flat examples [S7]. | Keep intrinsic and added flat damage per hand; add shared buffs to each eligible hand contribution without copying one weapon's local flat damage onto the other. |
| Percentage damage bonuses apply by damage type across eligible sources. | **A:** [S1]. | Evaluate added bonuses against existing accumulated bonuses; do not treat an extra percentage-point bonus as the same percentage increase in total offense. |
| Ordinary conversion printed on a weapon is global, unlike weapon-local flat damage and armor piercing. | **A/B:** equipment conversion in [S1]; explicit dual-wield clarification [S6], posts 156–158. | The Slicer's Physical-to-Chaos roll must not be limited to the Slicer solely because that is where it appears. Preserve separately targeted skill conversion. |
| Ordinary percentage attack-speed bonuses on weapons are global. | **B:** [S5], post 5. Base weapon speed is a different input. | Do not apply a weapon's ordinary percentage speed bonus only to that hand. Do not sum base-speed adjustments as though they were the same stat. |
| Dual-wield speed is described as using an average of the weapons' speeds, and a hand swap did not change the displayed speed in the reported check. | **B, limited:** [S10], posts 4–5. **U:** exact aggregation, animation timing and cap treatment for Beeztrap. | Preserve both base speeds. The normalized +60% speed modifier is not verified attacks per second. Do not introduce an unexplained dual-wield penalty or a guaranteed damage gain beyond a speed cap. |

**Input-specific check:** direct inspection confirms that the normalized weapon rolls omit intrinsic Physical bounds. Database base ranges are Slicer 48–74 and Sabre 70–76. Those are database values, not independent confirmation of exact displayed seeded damage. The future adapter must not interpret an absent rolled field as zero or add a base range twice. [S8]

## 4. Armor piercing, conversion and Deadly Momentum

| Rule | Status and evidence | Implication for relative gear ranking |
|---|---|---|
| Skill-specific conversion precedes global conversion. Already-converted damage is not converted again. General percentage bonuses apply to the resulting type; native skill modifiers have their own treatment. | **A:** official conversion section [S1]. | Track original versus already-converted portions. Do not boost converted Chaos using global Physical bonuses. |
| Armor piercing acts after ordinary conversion, on eligible remaining Physical damage. It does not convert Internal Trauma into Pierce DoT. | **B:** [S11], conversion guide and its explicit Trauma correction. | Physical-to-Chaos conversion can divert damage before it reaches Pierce. Keep Trauma separate rather than routing it through a sword's Pierce ratio. |
| Base armor-piercing ratio is hand-specific. Increased-armor-piercing bonuses can affect both weapons' own ratios. | **B:** [S7], armor-piercing section; hand-specific distinction also [S6]. | Do not apply one sword's base ratio to the other. Do not confuse a base ratio with an increase to that ratio. |
| Armor piercing requires an eligible weapon-damage attack and can affect native flat Physical damage in such a skill, not only the weapon's intrinsic base damage. | **B:** [S7]'s Blade Arc/Laceration example. **U:** exact routing of native flat damage within mixed-hand Cadence/WPS discharge. | Do not leave every skill-native Physical bonus unconverted by default. Keep ambiguous mixed-hand contributions identified until checked. |
| Deadly Momentum is a temporary global self-buff triggered by discharge, not a direct modifier applied only to that discharge. | **A/B:** linked secondary-buff records [S8]; [S12]; current clarification [S9], post 5. | Its shared flat damage belongs in eligible weapon attacks while active, including ordinary/WPS attacks. A Cadence-only item bonus must not automatically modify the buff globally. |
| Local conversion on Cadence does not globally convert the Deadly Momentum buff. Once its flat damage is carried into a later Cadence weapon-damage attack, that attack's conversion can affect it. | **B:** [S12], buff-type secondary modifier explanation. | Differentiate conversion on the attack, conversion on the buff, and global conversion. These are not interchangeable item benefits. |

**Deadly Momentum uptime remains an assumption.** The database establishes a five-second duration, not guaranteed full uptime during leveling. The first activation and refresh ordering relative to the triggering damage were not independently resolved. Do not count its effect twice if any part is already included in calculated global totals. Preserve the raw `offensiveTotalDamageModifier` field; its name alone is not evidence for an independent multiplicative damage factor.

## Direct checkpoint evidence

Read-only inspection used `beeztrap-work/project/Optimizer/database.json.gz` and `Cadence_Input_Audit.json`. Database SHA-256: `8c699db4100c9b1b9cf584529b2712abadf03403de94e0764fece8b8c0239773`.

| Record/input | Observed value | What this verifies |
|---|---|---|
| `records/skills/playerclass01/cadence1.dbr`, effective rank 16 | `weaponDamagePct=430`, native Physical minimum 197, `skillChargeLevel=2`, `skillChargeTime=0.35`, ranged time 0.25, charge duration 8 | Rank-dependent inputs; not attack-cycle frequency or hand ownership. |
| `records/skills/playerclass01/cadence3.dbr` | `Class=SkillSecondary_BuffSelfDuration`; links `cadence3_buff.dbr` | Separate secondary buff, rather than a normal direct skill modifier. |
| Linked buff, effective rank 13 | Physical 126–167; `offensiveSlowPhysicalMin=60`; `offensiveTotalDamageModifier=108`; duration 5 seconds | Buff fields at saved effective rank; not certified uptime or total relative damage. |
| Saved WPS effective ranks | Markovian 4, Belgothian 1, AQC 5, Whirling Death 3, Execution 4; raw weight total 88 | Which WPS inputs need handling. Does not establish animation shares. |
| GD0321 / GD0322 | Each base armor-piercing field 100%; Slicer saved Physical-to-Chaos roll 13.587144613265991% | Important routing inputs. A 100% ratio does not undo prior Chaos conversion. |
| Slicer targeted modifiers | AQC: +24 `weaponDamagePct`; Whirling Death: +80 flat Pierce, +6 life-leech field | These benefits must stay attached to their named skills, rather than become generic character bonuses. |

## Minimum unresolved questions before claiming reliable rankings

1. **Version/timing:** identify the installed executable build and validate applicable melee cycle behavior. Data matching the 0.35-second patch is necessary, not sufficient.
2. **Hand attribution:** establish discharge hand weights and the treatment of accompanying offhand WPS damage for the current patch. Do not substitute base-animation probabilities.
3. **WPS timing:** determine whether changes to AQC, Shears, Whirling Death or other WPS can materially change cycle composition. A fixed invested build can still gain different effective ranks and targeted mechanics from equipment.
4. **Speed:** resolve mixed-weapon base speed, caps, and material animation differences. Exact animations need not be simulated; uncertainty must remain visible if they cannot be verified.
5. **Buff accounting:** reconcile Deadly Momentum's flat and percentage fields with existing totals; choose and disclose a practical uptime convention. First-hit ordering can remain a minor startup limitation if it cannot change the recommendation.
6. **Mixed-hand native damage:** confirm armor-piercing ownership for native Cadence/WPS flat Physical damage where hands have different ratios.

A later simple scorer could compare candidates across conservative cycle/uptime assumptions and report only robust winners. That is an implementation proposal, not a result of this task. Differences within the existing 5% materiality band—or smaller than unresolved mechanical uncertainty—should not receive a confident performance ordering.

Defense and cost remain separate: this research provides no reason to change resistance penalties, defensive floors, attachment prices, fixed skills/devotions, or the practical leveling priorities.

## Sources and exact evidence locations

- **S1 — official:** [Crate Combat Guide](https://www.grimdawn.com/guide/gameplay/combat/), sections “% Weapon Damage,” “Flat vs Percent Damage,” “Passively Activated Weapon Skills,” and “Conversion.”
- **S2 — official:** [Grim Dawn v1.2.1.0 + Hotfixes](https://forums.crateentertainment.com/t/grim-dawn-version-v1-2-1-0-hotfixes/136968/1), Zantai, 13 June 2024, Soldier/Cadence entry. Explicit charge-ICD change.
- **S3 — first-hand mechanics testing:** [Melee Cadence Mechanics, v1.2.1](https://forums.crateentertainment.com/t/melee-cadence-mechanics-v1-2-1/137729), mi023, 27 July 2024, sections 1–4. Video-backed observations; not reproduced during Task 2A.
- **S4 — correction by the same tester:** [Melee Cadence Mechanics, page 4](https://forums.crateentertainment.com/t/melee-cadence-mechanics-v1-2-1/137729?page=4), posts 63–66, December 2024–January 2025. Particularly post 64's correction and post 66's hit-count distinction.
- **S5 — community mechanics explanation:** [Which item bonuses are global?](https://forums.crateentertainment.com/t/dual-weilding-which-item-bonuses-are-global/34058), MortalKombat, post 5, August 2016. Percentage attack-speed ownership; older evidence, not a full speed formula.
- **S6 — later conversion clarification:** [All you need to know about conversion, page 8](https://forums.crateentertainment.com/t/all-you-need-to-know-about-conversion/38123?page=8), Gnomish_Inquisition, posts 156–158, February 2025. Global ordinary weapon conversion versus hand-specific armor piercing.
- **S7 — community mechanics guide:** [Mechanics Guide](https://forums.crateentertainment.com/t/mechanics-guide/99479), guide reproduced in post 8. Flat-damage ownership and armor-piercing examples. Its older abbreviated Cadence/WPS statement is not accepted as a complete discharge model.
- **S8 — supplied game data:** checkpoint database and imported audit, exact records and hash above. No new extraction, game execution or optimizer calculation performed.
- **S9 — contemporary clarification:** [Cadence issue](https://forums.crateentertainment.com/t/cadence-issue/151985), 2 March 2026, Gnomish_Inquisition post 5 and Ceno post 14. Buff identity and exclusion of Cadence from the WPS pool. General discussion, not a cycle benchmark.
- **S10 — limited speed observations:** [Dual Wield: does weapon order matter?](https://forums.crateentertainment.com/t/dual-wield-does-weapon-order-matter/45819), Raven82 post 4 and kain post 5, May–June 2018. Insufficient to certify precise current-patch timing.
- **S11 — conversion mechanics guide:** [All you need to know about conversion](https://forums.crateentertainment.com/t/all-you-need-to-know-about-conversion/38123), Halcyon; armor piercing and TankPet's Internal Trauma clarification. Community guidance, not executable source.
- **S12 — secondary-buff explanation:** [Secondary Skill Modifiers](https://forums.crateentertainment.com/t/secondary-skill-modifiers/90919/1), Stupid_Dragon, 20 October 2019, mechanics section and Deadly Momentum listing.

**Task 2A stops here. Task 2B is not authorized or started.**
