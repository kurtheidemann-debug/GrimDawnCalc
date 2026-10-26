# Stage 3 — Equipment mechanics reconciliation

Starting point: Stage 2 merge `46b526a1fcf58b04237f175aaba26f10485b4459` (PR #3).

This user-requested mechanics stage precedes the originally planned transferable-item pooling stage. It does not implement pooling, procurement, weapon-pair search or a Full Review. Current-save authority, scoring policy, materiality thresholds, uncertainty blockers and practical-search strategy are retained.

## Root cause and full modifier path

1. The save supplies each equipped item's base/affix identity and its selected component/augment.
2. The seeded decoder supplies intrinsic rolls and completion bonuses. Static component records point through `itemSkillName` to granted skills.
3. `Engine.item_parts()` already added ordinary numeric values from persistent granted skills, once per granting item/component. Its **separate maximum-resistance accumulator omitted those skills**.
4. `Engine.calculate()` therefore included both auras' ordinary Chaos resistance but computed maximum Chaos as 80 rather than `80 + 3 + 3 = 86`.
5. Capping the raw 108 resistance at that incorrect maximum produced the 80/86 discrepancy and incorrect overcap/feasibility inputs.

Both active Mal weapons carry `records/items/materia/compa_imbuedsilver.dbr`. Each grants `records/skills/itemskills/componentskills/comp_chaosresistaura_01.dbr`, a persistent toggled skill containing **`defensiveChaosMaxResist = 3`**. The correction adds each physical source's three **percentage points** to the common cap accumulator; it is not a Chaos-only rule or a Mal adjustment. Removing zero/one/two Silver components produces caps **86/83/80** and raw Chaos **108/88/68** in focused calculator tests.

## Systematic findings and corrections

|Finding|Evidence|Common correction|
|---|---|---|
|Persistent equipment-granted maximum resistance omitted|Silver's +3 Chaos cap per component; Purified Salt points to a separate persistent skill with +3 Aether cap|Accumulate rank-aware specific/all-resistance cap bonuses from qualifying persistent grants, once per granting source|
|Ascended sources depend incorrectly on attachment occupancy|Nine `records/items/lootaffixes/ascended/` records grant +2 maximum resistance. The old compact `attach[:2]` list dropped ascended caps when both attachment slots were filled; with empty slots it could append the ascended record again and double skill bonuses/modifiers|Build intrinsic records once, then append only live component/augment records. Add ascended ordinary numeric values once, because the seeded roller does not include ascended affixes. Test all nine real cap affixes under zero/one/two occupied attachment slots|
|Saved and live attachment sources coexist or duplicate|`RelativeOffense.equipment_records()`, Cadence input diagnostics and Beeztrap conversion-signature extraction combined catalog records containing saved attachments with live attachments|Use the same live record assembly for stat aggregation, offensive modifier extraction, diagnostic inputs and conversion guards. Unchanged attachment modifiers count once; removed/replaced attachments contribute nothing|
|Unambiguous seeded conversion percentage ignored in some consumers|The relative ability path read database conversion percentages even when an intrinsic seeded roll was available; Cadence already substituted unambiguous rolled values|Resolve one unambiguous intrinsic mapping from its seeded percentage in the common source assembly. Never assign that aggregate roll to a live attachment or guess allocation among several mappings|
|Primary maximum-resistance ceiling not applied|The derived-stat path allowed `80 + bonuses` above the documented 95% ceiling|Clamp the first nine primary damage-resistance caps at 95. Keep raw resistance separate so excess remains resistance-reduction headroom|

The static scan found **two directly granted persistent skills with primary maximum-resistance fields**, reached by Imbued Silver and Purified Salt, and **nine ascended cap affixes**, one for each primary resistance. This is a scoped scan of the bundled 82,744 records, not a claim that all 82,744 records were combat-simulated. No database was rebuilt or edited.

`resistance_caps()` also gives direct equipment, active buffs, passive devotions and other already recognized cap sources one rank-aware percentage-point interpretation. Cap bonuses and ordinary resistance remain separate. Temporary item buffs, low-health procs and shapeshifts are not turned into guaranteed persistent bonuses. Repeated physical grants stack; sources are not globally deduplicated merely because they reference the same skill.

## Mechanics retained and limitations

- Flat values add to flat totals. Same-type percentage modifiers sum before the existing single-precision percentage application; separate multiplier categories are not collapsed into that sum. OA/DA, health, armor, absorption and offensive scoring formulas were not rewritten.
- Conversion still follows the existing local-then-global kernel, proportional normalization when one source type exceeds 100%, and no reconversion of already converted damage. Focused tests preserve these properties. Source assembly and an unambiguous rolled percentage were corrected; the conversion formula was not replaced.
- Multiple intrinsic conversion mappings sharing an aggregate rolled field cannot be uniquely allocated from that aggregate alone. That case is **not newly certified**. Existing Cadence ambiguity blockers remain. The relative ability model's handling of ambiguous randomized conversion still needs separate calibration/uncertainty coverage; do not mistake the unambiguous fix for an exact universal routing model.
- Item-granted toggles are treated as on in the existing persistent-sheet model, as in the bundled independent exporter. Actual runtime toggle state/uptime is not established here. Temporary/conditional proc uptime, external auras, mutators, pet AI and exact combat DPS remain outside this reconciliation.
- The independent exporter is a second calculation using the same static database, not a live game measurement. Its cap collection does not establish complete coverage for ascended affixes or the >95 ceiling. Those cases have direct database/documentation tests; a future unsupported baseline disagreement must still block verification. No tolerance or exception was added to hide an oracle limitation.

Primary mechanics references:

- [Official character basics — resistances](https://www.grimdawn.com/guide/character/character-basics/): default 80% and maximum 95% primary resistances.
- [Official combat guide — conversion](https://www.grimdawn.com/guide/gameplay/combat/): conversion order, normalization and no second conversion of already converted damage.
- Bundled decoder source: `gd_edit/item_stats.clj` (`rolled-stats` covers base/prefix/suffix/modifier), `gd_edit/resistances.clj` (`granted-skills`/cap accumulation) inside `gd-edit-standalone.jar`.

## Before/after — supplied Save 9, current Ultimate difficulty

|Metric|Mal before|Mal after|Beeztrap before|Beeztrap after|
|---|---:|---:|---:|---:|
|Level|87|87|76|76|
|Maximum Chaos resistance|80|86|80|80|
|Displayed Chaos resistance|80|86|80|80|
|Uncapped Chaos resistance|108|108|127|127|
|Chaos overcap|+28|+22|+47|+47|
|OA|2581|2581|2025|2025|
|DA|2309|2309|1986|1986|
|Health|15775|15775|11499|11499|
|Armor|1858|1858|1585|1585|

Both characters now pass **Quick and Full strict current-baseline verification with zero differences and no accepted exception**. These are calculator/baseline checks, not equipment searches. Beeztrap's current Ultimate elemental-resistance shortfalls remain actual input deficits, not calculation discrepancies; passing baseline verification does not assert that current gear meets optimization floors.

The two Silver contributions are tested individually using the actual component/skill definitions. Replacing both with Purified Salt in a calculator-only test produces maximum Aether 86 and maximum Chaos 80. These perturbations are mechanics tests, not suggested loadouts or acquisition claims.

## Focused validation

Run against the private supplied ZIP; the save and profiles are not committed or edited:

```sh
GD_STAGE2_SAVE=/absolute/path/save9.zip python -m unittest test_stage2 test_equipment_mechanics -v
python -m unittest test_optimizer \
  test_practical.PracticalTests.test_saved_skills_and_devotions_cannot_change \
  test_practical.PracticalTests.test_cheap_configuration_wins_inside_materiality_band \
  test_practical.PracticalTests.test_material_offense_does_not_get_cost_override \
  test_practical.PracticalTests.test_attributes_preserved_when_not_required \
  test_practical.PracticalTests.test_no_encounter_outputs -v
python validate.py
```

The Stage 2 tests retain their stale-profile, difficulty, current equipment/attachment, skills/devotions/bindings, progression, mechanics and input-immutability checks. Their former expectation that Mal be blocked was replaced with strict success for both characters; the separate test proving unexplained OA mismatches still block both modes remains intact.

Results: **29 save-authority/mechanics tests and 12 existing regressions passed**. Compilation, diff checks and runtime integrity passed. No Full Review or equipment optimization was run.

## Files and scope

- `GrimDawn_Optimizer.py`: common live item sources, unambiguous seeded conversion percentages, cap-source accumulation and primary cap ceiling.
- `relative_offense.py`, `cadence_inputs.py`, `cadence_scenarios.py`, `beeztrap_equipment.py`: consume the common live equipment records; scoring equations/weights/scenarios unchanged.
- `test_equipment_mechanics.py`, `test_stage2.py`: source/stacking/conditional/conversion/cap tests and current-save strict acceptance.
- `Runtime_Integrity.json`: refreshed source/test hashes.
- This report, Stage 2 status note, roadmap, production guide and README: current status and limitations.

The transferable unequipped item pool, attachment procurement/access and weapon-pair search remain separate tasks. This mechanics fix unblocks strict calculator verification for both supplied characters; it does not claim completion of those features or a full v1.3.6 release.
