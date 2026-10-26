# Cadence adaptation — checkpoint 1

Status: input adapter complete; offensive ranking remains disabled. Existing Beeztrap and Mal recommendations have not been changed.

## Completed

Added `cadence_inputs.py`, a read-only adapter over the existing v1.2 decoder, normalized inventory, game database, and stat calculator. It exports both weapons separately, their intrinsic physical damage bounds, saved rolls and locations, attachment IDs, conversion fields, armor-piercing fields, speed metadata, effective charged-finale skill ranks, linked Deadly Momentum buff data, learned WPS fields, and targeted item modifiers. It uses the existing skill-family metadata instead of incorrectly choosing Blitz or Shadow Strike as the primary attack.

The adapter retains unrecognized numerical skill mechanics for later interpretation. Conversion scope and damage-routing assumptions are explicitly unresolved. The small relative comparison kernel accepts only already-resolved direct-damage factors, refuses unverified use, and is not connected to the optimizer. Its existence does not certify a Cadence score.

## Verified against the imported snapshot

- GD0321: database intrinsic Physical 48–74 (mean 61); saved Physical-to-Chaos conversion 13.587144613265991%; armor-piercing field 100%.
- GD0322: database intrinsic Physical 70–76 (mean 73); armor-piercing field 100%.
- Intrinsic Physical weapon damage was absent from the normalized rolled fields. The adapter recovers the database base range rather than treating it as zero. A seeded range, when available, overrides the base; it is never added twice. Database base values are identified as such, not represented as independently verified exact in-game rolls.
- Cadence effective rank 16: weaponDamagePct 430; native Physical flat 197; charge-level field 2. These are database inputs, not an inferred attack-cycle frequency.
- Deadly Momentum effective rank 13: linked buff duration 5 seconds; native Physical 126–167; offensiveTotalDamageModifier 108. No uptime or extra multiplier has been invented.
- Five learned WPS have raw weights totaling 88. This is not presented as their share of total Cadence-cycle damage.
- Dermapteran Slicer's targeted modifiers are retained: +24 weaponDamagePct to Amarasta's Quick Cut; +80 flat Pierce and +6 life-leech field to Whirling Death. Their application remains separate from global character stats.

Six added tests cover saved-build preservation, real skill ranks/buff data, intrinsic damage recovery, rolled override, targeted item modifiers, and fail-closed scoring. All 30 tests passed on the final code. Existing Beeztrap preservation checks were also rerun; see bundled logs.

## Still required for useful weapon rankings

1. Verify melee hand selection, charge carryover, and WPS/discharge interaction. Do not use a blanket every-third-animation rule or infer multi-hit counts from WPS weights.
2. Separate weapon-local and shared flat damage, conversion, speed, and percentage bonuses. Reconcile which Deadly Momentum effects the existing calculator already includes to avoid double counting.
3. Resolve conversion/armor-piercing order and which skill-native flat damage receives armor piercing.
4. Implement the algebraic cycle average and conservative Momentum uptime, then OA/RR and relevant DoT contributions. Validate a hand-checked Beeztrap baseline and a few monotonic gear comparisons before enabling search.

No equipment search was run with the incomplete adapter. The 5% materiality preference, cost model, fixed build, defenses, cached databases, and archived results are unchanged. No overall-DPS-within-5% claim is made.

## Resume commands

From the extracted `Optimizer` folder:

```bash
python cadence_inputs.py --output Cadence_Input_Audit.json
python -m unittest discover -v
python verify_beeztrap.py
```

The adapter restores compact-checkpoint shared snapshots from the existing root database files when necessary. It does not re-extract ARZ archives.

## Evidence to resolve next

The available player test discussions contain qualifications and disagreement about melee versus ranged charge behavior. They are leads to validate, not a certified scoring formula:

- https://forums.crateentertainment.com/t/cadence-dual-wield-and-wps-explained/102470
- https://forums.crateentertainment.com/t/can-anyone-explain-why-cadence-at-100-wps-sometime-hits-every-2-and-sometimes-every-3-attacks/133573

A next bounded work session should resolve cycle mechanics and local/global routing first. Do not enable the comparison kernel merely by setting its verification flag.
