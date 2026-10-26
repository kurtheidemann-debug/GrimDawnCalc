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

Quick still reuses the profile's shared-stash, recipe and crafting-resource
snapshots. Full refreshes the supplied shared stash, recipes and resources. Missing
optional account files retain their prior snapshot with an explicit notice; this
account refresh behavior is unchanged in Stage 2. Cross-character equipment pooling is enabled in both modes (Stage 5). Unknown characters do not receive an invented
scoring policy. Static databases and persistent build policy are reused.

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
No reset is allowed. Beeztrap's preserved dual-wield, conversion and offense
uncertainty guards still apply. A defensive repair may be useful without claiming
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

Both Quick and Full import equipment from every uploaded character's bags,
personal stash, equipped slots and weapon sets into the selected character's
existing pool. Target and shared items retain their order/IDs; donor instances
are appended in character-name order. Donor consumables/material stacks are not
pooled; this stage expands equipment availability only. Quick retains its existing
cached shared-stash/resource behavior; Full refreshes uploaded shared storage.
No donor profile or source save is changed. Characters absent from a new upload
are not silently reintroduced from old donor snapshots.

Donor bases with `soulbound` or `untradeable` metadata are rejected in candidate
admission and final legality. Existing target/shared ownership exceptions remain.
Level, attribute, equipment type, resources, faction augment eligibility, defenses
and fixed Beeztrap weapons retain the existing checks. Attached augments on donor
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
