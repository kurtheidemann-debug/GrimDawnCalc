# Task 2B — bounded Cadence relative offense

**Delivered:** `cadence_scenarios.py`, a standalone, stdlib-only scorer for Beeztrap's fixed dual-wield Cadence build. No search integration, equipment search, skill/devotion changes, or Mal recommendation changes. This checkpoint does not begin Task 2C.

## Scope and interpretation

The result is **relative direct offense**, with the comparison baseline equal to 100 in each scenario. It is not total DPS. Defenses are returned separately using the existing calculator: health, DA, armor, absorption, and all resistance rows. A robust offensive label is not a defensive approval or an equipment-legality check.

A candidate is labeled `ROBUST_DIRECT_OFFENSE_IMPROVEMENT` only if its index exceeds 105 in **every one of the 32 scenarios**, and no unsupported mechanical changes are detected. Exactly 105 is insufficient. Missing scenarios are rejected. Other results are either `NO_ROBUST_IMPROVEMENT` or `UNSUPPORTED_DELTA_NO_CERTIFIED_RANK`. Unsupported comparisons may contain diagnostic indices but cannot receive the robust label.

These are explicit sensitivity assumptions, not verified engine bounds. Winning every selected scenario does not prove superiority under every possible animation, target, or play pattern. In particular, an unchanged omitted contribution can dilute a gain in total offense. The 5% threshold therefore applies to the reported direct-offense model, not all character damage.

## The 32 scenarios

All combinations of these five two-value assumptions are evaluated; favorable assumptions are not bundled together into one optimistic scenario.

| Uncertainty | Assumptions | Meaning and limitation |
|---|---|---|
| Cadence discharge share | 1/3 and 1/2 of normalized attack actions | Slow/fast cycle sensitivity; not a measured frequency or guaranteed bounds. No animation or charge-event simulation. |
| Discharge hand weighting | 50% main / 50% off; 100% main | Symmetric versus main-heavy attribution. The specification does not establish exact current-patch weights. |
| WPS contribution credit | 50% and 100% of the modeled WPS increment | Discounted versus full native WPS coefficient/flat contribution. This deliberately avoids inventing verified AQC multi-hit or recovery-frame multipliers. |
| Mixed-weapon speed | Mean of normalized hand base-speed factors; slower hand | Base factors use 1 plus each recorded speed adjustment. Applies only to the current Very Fast sword category; other classes are rejected and other speed tags block certification. Neither case claims exact attacks/sec. |
| Deadly Momentum uptime | 50% and 100% | Compute whole buff-off and buff-on scores, then weight those complete scores. Do not separately average its flat and percentage bonuses and create an artificial uptime cross-term. |

Normal actions use the default dual-wield 0.75 contribution per hand as a working average. Discharge uses one weighted Cadence payload plus a discounted accompanying other-hand ordinary/WPS payload. That accompanying contribution is 0.5 times the WPS-credit assumption; this is an explicit envelope choice, not a verified discharge animation rule.

WPS probability weights are taken at effective ranks, normalized only when their total exceeds 100. Any remaining ordinary-attack share is retained. Cadence is not inserted into that WPS pool. No WPS hit count is inferred solely from its coefficient.

Ordinary global percentage attack speed is applied once, with a conventional dimensionless 200%-speed ceiling as an assumption. Special maximum-speed changes are not independently modeled. OA uses the existing framework's simple linear relative utility; it is not an enemy-specific hit/crit probability. Crit mechanics and RR are not recomputed here.

## Damage ownership and routing

- Intrinsic weapon Physical damage and flat damage from each weapon and its attachments remain in that hand's payload. Shared flat damage is reconstructed from non-weapon gear, persistent skills, passives, sets and passive devotions. It is not copied from global totals containing both hands' local damage.
- Missing intrinsic Physical roll fields fall back to the extracted database base range. A supplied seeded range overrides that base; it is not added twice. Exact in-game seeded base weapon damage remains an input limitation inherited from Checkpoint 1.
- Ordinary equipment/buff conversion is global, including the Slicer's seeded Physical-to-Chaos percentage. Skill-specific conversion precedes it. Converted damage is frozen against reconversion.
- Each hand's armor-piercing ratio applies last to eligible unconverted native Physical damage. Physical created by another conversion is not pierced again. Increased-armor-piercing modifiers scale each hand's own base ratio, capped at 100%.
- General damage bonuses and attribute bonuses are applied to the resulting damage types. Skill-specific percentage damage is routed with its source damage and added alongside global bonuses, rather than silently multiplying all character damage.
- Cadence/Fighting Form and WPS targeted item modifiers remain in their named skill packets. The Slicer's AQC weapon-damage modifier and Whirling Death Pierce flat are retained. They are not added to generic character flat damage or to every attack.

These rules are grounded in `Cadence_Mechanics_Spec.md`, bundled unchanged with this checkpoint. Scenario numbers above are assumptions, not extra verified mechanics.

## Preventing double counting

The adapter reconstructs which skill contributions the preserved calculator placed in its totals. It removes Deadly Momentum's conditional root/buff contribution, and any Cadence-native modifier erroneously included as a global active modifier, before building scenarios. Shared flat damage is reconstructed independently and excludes those same conditional sources. Momentum is then applied once per buff-on branch. A regression test marks Momentum active in the imported data and verifies identical scenario results after this reconciliation.

Chance-based percentage damage sources are discounted to expected contributions, not counted at full magnitude. In the current baseline the two Bloodrose Thorn augment records each contribute a 10%-chance +200% damage field; the scorer subtracts the unearned 90% portion of each from the inherited total. This correction is local to the standalone scorer. Conditional/proc changes outside this convention are not certified.

## Unsupported changes and remaining limitations

The comparison blocks robust certification when tracked DoT, crit, resistance-reduction, current-life damage, or conditional/proc signatures change, or when seeded conversion mappings are ambiguous. Signatures include effective-rank fields and relevant targeted modifiers. These guards are conservative; an unsupported label is not a judgment that the item is bad.

Existing unchanged DoT, RR, crit effects and item procs are not added as an invented damage multiplier. This is a direct-attack comparison only. Proc activation graphs, arbitrary new targeted mechanics, special speed-cap changes, exact native skill-flat attribution in mixed-hand discharges, and precise startup Momentum timing remain unsupported. Do not use this module to certify items whose decisive benefit is one of those effects. The signatures are a bounded check, not an exhaustive detector of every game mechanic.

The old optimizer's unscored Beeztrap search remains disabled for weapon ranking. No state is written into the save. Skills, devotions, bindings and the imported hotbar configuration are preserved; the scorer does not offer changes to them.

## Use

From the extracted `Optimizer` directory:

```bash
python cadence_scenarios.py --output Cadence_Scenario_Baseline.json
python cadence_scenarios.py --candidate candidate_state.json --output candidate_comparison.json
python -m unittest discover -v
python verify_beeztrap.py
```

The candidate JSON uses the existing state format (`gear`, `comp`, `aug`, `skills`, `devotions`, `bindings`, `attributes`). It must preserve the saved invested skills, devotions and bindings. This module compares a supplied state; it does not enumerate equipment or spend attributes. The compact checkpoint restores shared database snapshots from existing root files as needed, without extracting game archives.

## Validation and checkpoint status

Eight new tests cover conversion order/no reconversion, per-hand flat ownership, weapon swapping under symmetric/main-heavy assumptions, attack-speed increase/cap/slow-hand sensitivity, every-scenario materiality, Momentum reconciliation, targeted modifiers and fixed-build protection, and unsupported-delta rejection. Existing regression and preservation checks are retained. See `Cadence_Task2B_Test_Results.txt` and `Cadence_Task2B_Preservation.txt` for actual run results.

**Task 2B ends at this standalone comparison checkpoint. No Task 2C search or recommendations have been generated.**

## Task 2C correction

Validation found that Task 2B appended selected attachments to catalog records that already contained saved attachments. `selected_records` now reconstructs live records once from base/affixes and current attachments. This prevents doubled chance discounts/conversions and stale attachments after replacement. The baseline chance discount is 360 percentage points, not the erroneous 720. The chance +200% fields belong to Bloodrose Thorn augments, not Vicious Spikes components. See `Beeztrap_Cadence_Validation.md`.
