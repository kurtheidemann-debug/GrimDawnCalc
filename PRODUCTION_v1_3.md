# Grim Dawn Practical Optimizer v1.3

## Normal workflow

Upload the new `save.zip`. Run `python review.py save.zip`. Return the generated
`reviews/latest/Mal_Gear_Review.md` (or the selected character report). The default
is Quick Review. Do not run legacy scripts or regressions manually for an ordinary
inventory update. Do not rebuild the game database.

The bundle is self-contained: Python 3.11+ and Java 17+ are the only runtime
requirements. The decoder and seeded item-stat engine are included. No network
access, game installation, or original game archives are needed for routine saves.

```sh
python review.py save.zip
python review.py save.zip --character Beeztrap
python review.py save.zip --mode full --character Mal
```

Quick mode has a 60-second total target. It reserves time for final checks and
reporting, and returns the best fully evaluated feasible loadout retained within
its bounded search. This is not a global optimum claim. `--seconds 120 --width 10`
can run a separate wider review. If no feasible loadout is found, the report says
so and does not certify an incomplete candidate. A keep-current outcome is valid.
No command writes to a supplied save. Reports recommend changes for manual use.

## Quick and Full modes

Quick and Full import the selected character's current level, base attributes,
unspent points, skills, devotions/bindings, equipment/attachments, faction state,
and saved difficulty authoritatively. Missing required character fields block
with an explicit decoder/input error; historical character values are never
substituted. Optional hotbar/skill-set fields are not backfilled. Main-campaign
quest files, when supplied, are decoded into `quest-progress`; absent quest files
are disclosed. Quest-based purchase/service eligibility remains Stage 4 work.

Equipment scope is explicit:

|Source|Quick|Full|
|---|---|---|
|Selected character: equipped gear, both weapon sets, bags, personal stash|Yes|Yes|
|Shared stash equipment|No|Yes|
|Other uploaded characters: bags, personal stashes, equipped gear, weapon sets|No|Yes|

Both modes rebuild these pools from the uploaded save. Quick never imports old
Full equipment or donor candidates; cached winners must remap entirely into the
current permitted catalog. Full does not substitute a prior shared stash when
one is missing. Source omissions are reported. Unknown target characters still
require a registered scoring policy; static databases/build policy are reused.

Resources are independent of equipment scope. Both modes decode supplied shared
storage and refresh supplied reagent/recipe files with the existing importer.
Quick admits only loose shared components (`ItemRelic`) for resource accounting,
not shared equipment. Donor consumables/material stacks remain excluded. Missing
reagent files clear cached reagent stock; missing recipe files exclude cached
blueprint recipes (default recipes remain). Missing shared storage excludes its
loose components. Existing native attachments can stay on their own selected
items; new attachments still require current stock/crafting or eligible augment
purchases, target reputation/level, and sufficient iron. No unknown cached stock
funds recommendations. Quest-gated service/vendor access remains unmodeled.

Saved difficulty alone controls resistance penalties and the calculation target:
Normal -> Normal, Elite -> Elite, Ultimate -> Ultimate. Stored profile difficulty
and reference level are output metadata, not inputs. There is no difficulty
choice/override in the production workflow. Resave/reupload to change difficulty.

When multiple supported characters are in a Quick upload, the persistent default
is Mal and the report says so. An explicit `--character` selects Beeztrap. A save
containing just one supported character is identified automatically.

## Independent profiles

|Setting|Mal|Beeztrap|
|---|---|---|
|Build|Lightning Druid|Dual-wield Cadence|
|Initial reference level|78|74|
|Target|Saved Normal / Elite / Ultimate|Saved Normal / Elite / Ultimate|
|Materiality|5%|3%|
|Offense|Preserved Mal model; 80% Totem / 20% Wind Devil|Preserved 32 Cadence scenarios and uncertainty blockers|
|Quick skills / devotions / bindings|Locked|Locked|

`profiles/<name>/` contains the current data and policy for that character.
Updates are staged and committed only after checks. `--no-commit` produces a
report without updating the persistent profile. One profile's update does not
write to the other profile. A shared static database is linked locally rather
than rebuilt. An OS file lock prevents overlapping profile transactions.

## Search and attributes

The original calculators, resource/cost rules and scoring modules are retained.
Quick uses one bounded Balanced beam with joint gear/component/augment bundles,
small per-slot shortlists, stable ordering and deterministic tie breaks. Candidate
ranking always evaluates complete loadouts; a temporary resistance or requirement
shortfall may be traversed but never delivered as a feasible winner. Current
gear and physically remapped previous winners are seeds, not invented inventory.
Final checks cover level, attributes, attachments, reputation, crafting stock,
unique item instances, defensive floors, equip order, and fixed build data.

Attribute candidates include the existing minimum requirement repair plus bounded
voluntary Physique/Spirit allocations. The unchanged cost/defensive policies select
among them. The report states the exact point allocation and remaining points.
No reset is allowed. Beeztrap's supported dual-wield model and offense uncertainty guards still apply. A defensive repair may be useful without claiming
a certified offensive gain when Cadence blockers remain.

Mal's 5% rule is applied after search to select meaningful, cost-aware changes;
it never decides whether search is permitted. The materiality band stays anchored
to its original winner, preventing chained degradation. Repairs of an infeasible
current defense baseline remain eligible. A current feasible loadout is kept
when neither offense nor defense gains are material.

## Validation

`python validate.py` verifies the published runtime integrity manifest. It does not
run the regression suite. Code/data changes require appropriate focused tests and
an updated manifest; see `test_stage2.py` and `docs/STAGE2_RESULTS.md` for Stage 2.
Routine reviews do not run a regression campaign.

Both Quick and Full independently export/recalculate the **current imported**
baseline before search, and block unexplained differences. They also check current
identity, equipment legality/resources, unique instances and finite defensive
metrics. The winner's Mal offense or all 32 Cadence scenario scores are independently
recomputed. Derived item-roll caches require matching decoder/database provenance;
older unversioned profile rolls are recomputed, including relic completion bonuses.

The accepted Mal Chaos exception is scoped to the exact original level-78
equipment/attribute/skill baseline fingerprint; inventory and source paths do not affect it: decoder **86%**, model
**80%**, both **105% uncapped**. The report treats the decoder display as
authoritative for that baseline, records the exception and preserves existing
scoring mechanics. During a review matching this accepted baseline, a conservative
minimum of 86% uncapped Chaos is required of delivered candidates; the exception
does not invent a candidate's actual cap. It is not a wildcard exception for other characters, altered
snapshots or unrelated mismatches. Both review modes block new discrepancies. The current level-87 Mal save now
reconciles maximum Chaos at 86 through general item-granted cap accumulation;
no historical exception, new tolerance or character adjustment is needed.
See `docs/EQUIPMENT_MECHANICS_RECONCILIATION.md` for the confirmed related fixes
and remaining model limitations.

## Outputs and suspended inventory disposition

Quick and Full produce equipment reports and results JSON. Inventory keep/sell
valuation and inventory-disposition reports are suspended. All existing item
imports and equipment candidate availability remain unchanged; valuation modules
are preserved for later reactivation. A stale disposition report in the selected
output directory is removed. No future-level keep/sell tables are generated.

## Stage 4 performance

One bounded profile of the shipped Beeztrap fixture (53 states, 159 evaluation
requests) attributed 14.51 of 15.64 profiled seconds (92.8%) to Cadence strength
scoring; packet calculations accounted for 14.27 seconds. Character calculations
were 0.31 seconds and legality checks 0.17 seconds. Attachment enumeration was
fixture setup outside the timer; this measurement does not assign it a runtime
share. Memoization already reduced 159 requests to 39 unique scored states.

The sole search optimization caches exact hand/skill packet values within one
strength call. It avoids repeated ordinary-hand packet calculation and expires
at function return, preserving Momentum state, scenarios and arithmetic order.
One matched unprofiled workload took **4.20445 s before / 2.57160 s after**,
**38.84% less time (1.63x)**, with exact equality of all result rows, scores,
legality/resource checks and feasibility flags. This is not an end-to-end speedup
claim. The previous Save 10 Full Review reference remains 458.79 seconds search /
510.25 seconds overall; no complete Full Review was rerun.

Focused validation: 22 unit tests passed (review routing, retained importer/search,
Stage 2 input authority and strict mismatch guards, Stage 3 equipment mechanics).
A separate fixed Save 10 fixture compared the original and optimized scorer on
three complete states, including two feasible loadouts: all scenario scores,
metrics, legality, utility and selected equipment matched exactly.

The bundled original README, legacy modules/tests/results and licenses remain
available. Use this document and `review.py` for the v1.3 production workflow.

## Stage 5: uploaded cross-character equipment

Full imports equipment from every uploaded character's bags, personal stash,
equipped slots and weapon sets into the selected character's existing pool.
Stage 6 restricts Quick to its own character, as specified above. Target and shared items retain their order/IDs; donor instances
are appended in character-name order. Donor consumables/material stacks are not
pooled; equipment pooling remains separate from the resource handling above.
No donor profile or source save is changed. Characters absent from a new upload
are not silently reintroduced from old donor snapshots.

Donor bases with `soulbound` or `untradeable` metadata are rejected in candidate
admission and final legality. Existing target/shared ownership exceptions remain.
Level, attribute, equipment type, resources, faction augment eligibility, defenses
retain the existing checks. Stage 7 enables supported Cadence sword-pair changes. Attached augments on donor
gear do not grant the target the donor's faction purchase eligibility.

Reports show character, bag/stash tab or occupied equipped slot, and the exact
zero-based decoder path/item index. Weapon sets identify set and hand. JSON
`equipment_sources` records selected instance IDs, original owner/location and
complete saved identity/attachment/position data. Active alternate target weapon
normalization retains its original source path. Duplicate physical copies keep
separate occurrence IDs even when their rolled identity matches.

Focused fixtures expose three extra donor equipment instances (bag/stash/worn),
each selectable by the unchanged production beam. A one-candidate extension
increased fixture evaluations 71→102 and feasible states 1→2; no coverage was
pruned. This is workload evidence, not a Save 10 runtime estimate. 28 focused
tests cover import/routing in both modes, provenance, distinct IDs, binding/level/
attribute gates, no-donor equivalence, Stage 2/3 safeguards, unchanged search and
Stage 4 scorer, and suspended disposition. No complete Full Review was run.

## Stage 6 validation

35 focused tests passed, including current imported character state in both
modes, local-only Quick after a poisoned Full cache, Full donor selection, exact
source paths, cached-seed rejection, resource refresh and shortages, identical
selection/scores for identical pools, and Stage 2–5 safeguards. The shared scorer, general legality code, search limits and Stage 4 optimization
are preserved. Stage 7 adds supported weapon-pair transitions as described below.

Matched deterministic fixture (same beam width/rounds, no attachments): Quick
exposed 16 slot candidates (3 head choices + 13 fixed slots), 106 evaluations;
Full exposed 18 (adding shared + donor head choices), 111 evaluations. Full chose
the donor item; Quick chose its personal-stash item. Counts demonstrate source
coverage differences, not a claimed real-save speedup. No Full Review was run.

## Stage 7: supported Cadence weapon pairs

Production `CadenceEngine.options` previously pinned weapon slots 12 and 13 to
the current IDs. It now supplies both slots with the existing pool of level- and
transfer-eligible Very Fast one-handed swords. Unsupported weapon classes (axes,
maces, ranged, shields/offhands, two-handed weapons) and unverified speed tags
remain outside this scorer's supported comparison envelope; this stage does not
add their combat mechanics. Attribute/level/resource checks and unique physical
instances remain mandatory. Quick/Full source policies and provenance are unchanged.

Each sword/attachment candidate is evaluated as a complete loadout by the unchanged
32-scenario Cadence scorer. No independent weapon score is added. The existing
per-slot shortlists are joined for one weapon-pair beam transition, including
ordered hand assignments. This permits swaps and double replacements without an
illegal intermediate duplicate sword. Beam width, deadlines, materiality, cost,
defensive floors and standalone winner recomputation are preserved. Only shortlisted
joint bundles enter the pair transition; coverage remains bounded, not exhaustive.
When only the original assignments are admitted, the prior transition is retained.

Results/reporting record eligible sword-instance counts and distinct ordered
physical pairs evaluated, alongside total evaluations and timeout status. Pair
counts exclude using the same instance in both hands. The Stage 4 packet cache
and all scoring formulas are unchanged. Unsupported conversion/proc/DoT mechanics
retain the existing comparison flags; no new damage approximation is introduced.

Controlled real-scorer fixtures strengthen synthetic defenses to satisfy existing
gates and add two distinct high-damage sword instances. The production beam selects
main-only, offhand-only and simultaneous two-weapon upgrades. Reversed assignments
are evaluated and change scenario indices. Original-only results match the prior
fixed implementation. Additional checks cover duplicate/type/speed rejection,
weapon attachment compatibility, donor provenance, Quick/Full source scope and
suspended keep/sell. Relevant existing Stage 2–6 tests pass; no Full Review is run.
See `Stage7_Benchmark.json` for the one matched fixed/unlocked benchmark and
`benchmark_stage7.py` for its bounded reproducible fixture.

Matched benchmark (same synthetic fixture, width 5, one round, 30-second bound):

|Implementation|Eligible sword instances|Ordered pairs scored|Evaluations|Seconds|Completed|
|---|---:|---:|---:|---:|---|
|Prior fixed search|2|1|310|11.2321|Yes|
|Unlocked pair search|4|7|449|26.8859|Yes|

The unlocked fixture selected both added swords; fixed search retained the
original pair. Seven scored pairs is bounded coverage, not all twelve possible
ordered distinct pairs among four swords. This deliberately accepts additional
computation; it does not change the production timeout or imply real-save timings.

## Stage 8: combat configuration and module capabilities

`review.py --combat-configuration CONFIG` accepts `dual_wield_melee`,
`one_hand_shield`, `two_hand_melee`, `one_hand_caster_offhand`, or `ranged`.
Without the flag, the configuration is derived only from the uploaded active
weapon set. Inactive sets, inventory contents, character names and historical
profiles do not determine the configuration. The normal registered character
profile still selects its scoring module. Unknown profiles fail explicitly.

|Scoring module|Validated configuration in production|
|---|---|
|Cadence|dual_wield_melee: one-handed swords, axes, maces with finite numeric base-speed adjustments greater than -1|
|Lightning Totem|one_hand_caster_offhand|
|Werewolf / pets / unregistered profiles|No new support introduced|

No speed-tag preference or speed minimum is used. The existing formulas already
consume each weapon's numeric base-speed adjustment, local damage, piercing and
skill modifiers; class/speed admission guards are generalized without changing
Cadence strength arithmetic, scenario weights or the Stage 4 packet cache.
Missing/invalid numeric speed data and other melee classes remain explicit
unsupported cases. The generic policy recognizes shield, 2H and ranged structures
but recognition alone does not enable a scoring/search adapter.

A same-configuration explicit override is accepted and reported. **Style-changing
overrides remain blocked**: neither current module has a validated reference
builder for switching configurations. For example, a saved shield setup requested
as Cadence DW fails before engine construction/search with a specific reference
blocker; Maldirge fails because no validated scoring profile is registered.
No baseline is fabricated. A successful shield-to-DW reference/materiality test
cannot be claimed in this stage; it requires a separately validated adapter.

For supported requests, the reference remains the current uploaded loadout.
Existing implementation-cost weights and materiality rules are reused once;
there is no new penalty or attachment redistribution layer. The blocked
style-change fixture verifies unchanged character/attachment data and no
recommendation. Quick/Full sources, provenance, resource accounting and Stage 7
ordered pair transitions are preserved. Keep/sell remains suspended.

Focused checks cover active-set inference for all five structures, same-style
override, explicit rejection of unsupported module/style changes, numeric-speed
admission, real-scorer slower axe selection with Cadence rank bonuses, mace
admission, and exact equality of prior sword snapshots and all 32 scenario scores.
Relevant Stage 2–6 safeguards pass. See Stage8_Benchmark.json for the single
bounded matched fixture; no production Quick/Full Review was run.

Matched fixture (width 5, one round, 30-second bound): inferred sword DW admitted
2 swords, evaluated 2 ordered configurations / 379 loadouts in 16.4628 seconds;
explicit DW admitted 2 swords + 1 axe + 1 mace, evaluated 8 configurations / 418
loadouts in 19.5078 seconds. Both completed within the bound. The latter selected
the slower axe and mace. This is source/admission coverage, not a speedup claim.

## Stage 10: routine component crafting (verified subset)

Both review modes load the game's `craftingDefaultRecipes` menu as well as uploaded known recipes. A completed component need not already exist: the shared planner recursively crafts it from actual finite ingredients, charges crafting iron and augment purchases, and reports ingredient consumption. Attached components remain on their physical item; salvage is not assumed. No inventory is fabricated at any level, including Tier III below or above level 100. Unknown recipes or missing special inputs still block the package.

Aether Crystal is a verified ordinary ingredient despite its `QuestItem` database class; it uses the existing ordinary-material cost unit (1) instead of the special-material unit (15). All scoring, cost weights, materiality thresholds, search limits and equipment scopes remain unchanged.

Limitation: the database has no reliable universal Tier I/II/III ingredient labels. This release supports verified default/known recipes with finite saved stocks, not assumed supplies for every Tier I/II material or every special blacksmith service. No broad tier classification or vendor expansion is claimed.

Save11 regression: the 18% attack-speed Sabre with crafted Vicious Spikes passes resources (3 Serrated Spikes + 3 Aether Crystals + 1,500 iron). A controlled two-Sabre search with both matched packages seeded symmetrically selects it, offense 135.53, in 803 evaluations / 74.36 seconds without timeout. This is focused verification, not a Full Review or proof of unseeded global coverage. Public resource tests are in `test_stage10.py`; the actual Save11 fixture and its regression remain private.
