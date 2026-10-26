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

Quick imports current identity, level, attributes, unspent attributes, equipment,
and personal inventory. It reuses that profile's shared stash, build, faction
access, known recipes, crafting resources and scoring unless the selected save
explicitly supplies changed character progression. Explicit saved skill ranks,
devotion choices/bindings and reputation are imported and reported; the optimizer
keeps that actual saved configuration fixed. Missing fields retain their profile
values. Leveling alone never allocates or invents skills. Every owned catalog item
is checked again against the new level on every run; previously ineligible stash
items are not discarded. Missing personal items do not become phantom inventory.

Full is explicit. `--mode full --character Mal` updates only Mal. Omitting
`--character` in Full updates each registered profile present in the supplied
save tree. It refreshes supplied shared stash, progression, reputations, recipes
and materials, adopts actual saved skills/devotions/bindings, checks a fresh
decoder baseline export, and runs a wider complete-loadout search. Missing optional
progression files retain the prior snapshot with an explicit notice. Unknown
characters are not assigned an invented scoring profile. Neither mode changes a
profile's scoring, materiality, archetype or target difficulty merely because a
save changed. Static game data is reused.

When multiple supported characters are in a Quick upload, the persistent default
is Mal and the report says so. An explicit `--character` selects Beeztrap. A save
containing just one supported character is identified automatically.

## Independent profiles

|Setting|Mal|Beeztrap|
|---|---|---|
|Build|Lightning Druid|Dual-wield Cadence|
|Initial reference level|78|74|
|Target|Ultimate|Elite, with Ultimate resistance projection|
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

`python validate.py` runs the full preserved suite plus workflow regressions and
writes `Software_Validation.json`. The code, decoder and static database hashes
are certified. Routine gameplay snapshots are excluded. `review.py` reuses a
matching certificate; a code/database change triggers validation once before
processing. Ordinary inventory updates do not rerun regressions.

Every run still decodes/checks the save, verifies identity/level and item records,
calculates defenses, and checks the delivered complete loadout. The winner's
Mal offense or all 32 Cadence scenario scores are independently recomputed.

The accepted Mal Chaos exception is scoped to the exact original level-78
equipment/attribute/skill baseline fingerprint; inventory and source paths do not affect it: decoder **86%**, model
**80%**, both **105% uncapped**. The report treats the decoder display as
authoritative for that baseline, records the exception and preserves existing
scoring mechanics. During a review matching this accepted baseline, a conservative
minimum of 86% uncapped Chaos is required of delivered candidates; the exception
does not invent a candidate's actual cap. It is not a wildcard exception for other characters, altered
snapshots or unrelated mismatches. Full Refresh still blocks new discrepancies.
Quick baseline values are recalculated model values; they are not misrepresented
as a new independent decoder export.

## Outputs and disposal policy

Each report includes all fourteen slots, current/recommended full affixed names,
keep/change decisions, exact components/augments and reasons; before/after offense,
defense, all resistances, OA/DA, health, armor, absorption, ranks and cooldowns;
attribute spending, crafting/purchase needs and faction sources; and personal
inventory in the four requested disposition groups. JSON retains exact records,
full states, materiality audit, scenario blockers and validation details.

Safe disposal is conservative. It requires a usable owned alternative with no
weaker modeled rolls, matching supported mechanics, no higher requirements and
complete-loadout legality checks. Rings require two superior physical alternatives.
Equivalent items are ordered so they cannot all be marked for disposal. Unique
skills, sets, conversions, unsupported fields, unknown items and incomplete
requirements/rolls remain protected. Future-level items stay in the candidate
snapshot and are reevaluated on subsequent levels. An alternative-build label
means retain/no disposal proof, not a claim that an unrelated build was optimized.

The bundled original README, legacy modules/tests/results and licenses remain
available. Use this document and `review.py` for the v1.3 production workflow.
