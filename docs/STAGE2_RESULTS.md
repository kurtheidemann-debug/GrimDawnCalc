# Stage 2 — Save-state authority

Status: **Complete for Stage 2 save-state authority**. This is the historical Stage 2 record. The subsequently requested [equipment mechanics reconciliation](EQUIPMENT_MECHANICS_RECONCILIATION.md) resolves the Mal cap blocker described below; both current saves now pass strict verification. The remaining planned optimization features are not released.

Starting point: Stage 1 merge `361d4ca7fed393eb0db7c412b1566163c6444683` (PR #2).

## Demonstrated behavior

Both Quick and Full use the selected save's level, base attributes, unspent points, complete saved skill/devotion/binding configuration, current equipment/attachments, faction reputation and difficulty. No historical character snapshot fills missing fields. Missing required current fields now produce a precise input/decoder error. Optional hotbars/skill sets are not backfilled. Profile difficulty/reference level are derived output metadata; build emphasis, materiality and other scoring policy remain persistent.

|Current Save 9 field|Beeztrap|Mal|
|---|---|---|
|Decoded level|76|87|
|Saved calculation difficulty|Ultimate (2)|Ultimate (2)|
|Saved base Physique / Cunning / Spirit|378 / 226 / 114|530 / 90 / 154|
|Unspent attribute / skill points|6 / 2|11 / 6|
|Allocated devotion stars / bindings|55 / 6|55 / 6|
|Current mechanics check|Cadence investments 8/1/11; effective ranks 9/2/12; 32 scenarios|Storm Totem invested 16, effective 24; cap 5, burst 2, cooldown 2.46 s, duration 14 s|
|Independent OA / production OA after fresh roll derivation|2025 / 2025|2581 / 2581|
|Independent baseline gate|Pass; no new exception|Blocks only the Chaos display/cap mismatch below|

Normal, Elite and Ultimate constructor/penalty tests pass for both engines. No production difficulty override is provided; the legacy `--elite` override was removed. Cadence/Storm Totem formulas, scenario definitions, defense policy, thresholds, uncertainty blockers, search strategy and inventory retention are unchanged.

Main-campaign `quests.gdd` files are decoded with the bundled reader into `quest-progress`, including per-difficulty tokens/tasks. Quest-file content hashes participate in the raw decode cache key. Missing quest files are disclosed without historical substitution. This supplies progression state only: vendor/blacksmith acquisition rules are still Stage 4 work.

## 2025-versus-1991 OA: resolved without calibration changes

The two calculators used the current saved character. The production path reused an unversioned profile item cache whose entry for the equipped **Bladedancer's Talisman** omitted the current saved relic completion bonus, **`characterOffensiveAbilityModifier = 2`**. Fresh seeded completion decoding from the same save yields that bonus. Including it gives 2025 OA in the unchanged production formula, matching the independent export.

`resolve_items()` now accepts cached derivations only when their saved roll key and decoder/database provenance match. The provenance covers `database.json.gz`, `gd-edit-standalone.jar` and `save_bridge.clj`. Existing unversioned caches are recomputed once; subsequent matching derivations can be reused. No profile state, database content, OA formula, comparison tolerance or whitelist was changed to make the figures agree.

## Separate material-calibration issue: Mal's maximum Chaos resistance

Mal has **Imbued Silver on each active weapon**. Each grants the persistent skill `records/skills/itemskills/componentskills/comp_chaosresistaura_01.dbr`, with **+3 maximum Chaos resistance**. The bundled independent export accumulates caps from item-granted persistent skills. `GrimDawn_Optimizer.Engine.item_parts()` adds those skills' ordinary numeric values but does not add their maximum-resistance contributions to its cap accumulator.

Consequently, the current level-87 Mal baseline agrees on OA, attributes, armor and uncapped Chaos **108**, but the independent Chaos cap/display is **86** and the production cap/display is **80**. This is a separate mechanics omission, not stale character state, decoding, saved difficulty or a rounding difference. Stage 2 does not modify that cap mechanic or expand the old, fingerprint-scoped level-78 Chaos exception.

The strict independent baseline comparison remains active, with no increased tolerance. It now runs in **Quick as well as Full**, preventing Quick from bypassing this known feasibility discrepancy. Tests demonstrate rejection in both modes. The test that expects rejection is a safeguard test, not a declaration that Mal passes calibration or can receive a certified loadout.

A focused mechanics correction and its tests are required before Mal can pass the current baseline gate. That correction is explicitly outstanding; do not bypass the gate during Stage 3 or Stage 6.

## Acceptance and focused regression results

Private input: supplied `save9(1).zip` (Save 9), SHA-256 `46049da6af652e694c27d6711581096eb2d8afc4259b809f77c3cee59f349838`.

- **14 Stage 2 tests passed** (`test_stage2.py`, 74.020 seconds on the acceptance run): explicit character selection, stale profile rejection as authority in both modes, all saved fields and attachments, quest state, all three difficulties in both engines, relic-cache provenance, unchanged mechanics outputs, Normal report labeling, strict mismatch blocking and source ZIP immutability.
- **12 relevant existing tests passed** (6.882 seconds): all seven `test_optimizer.ModelTests` plus five selected `test_practical.PracticalTests` covering fixed saved configuration, materiality/cost preference, attribute preservation and current model outputs.
- Python compilation and `git diff --check` passed.
- Runtime integrity manifest refreshed for changed source and the new test; `python validate.py` verifies it. This is an integrity check, not a full regression campaign.
- No equipment search, full optimization, save edit, database rebuild, cross-character pooling, new attachment/acquisition behavior or weapon-pair implementation was run or introduced.

To reproduce:

```sh
GD_STAGE2_SAVE=/absolute/path/save9.zip python -m unittest test_stage2 -v
python -m unittest test_optimizer \
  test_practical.PracticalTests.test_saved_skills_and_devotions_cannot_change \
  test_practical.PracticalTests.test_cheap_configuration_wins_inside_materiality_band \
  test_practical.PracticalTests.test_material_offense_does_not_get_cost_override \
  test_practical.PracticalTests.test_attributes_preserved_when_not_required \
  test_practical.PracticalTests.test_no_encounter_outputs -v
python validate.py
```

The save-dependent tests skip unless `GD_STAGE2_SAVE` is supplied. The private ZIP and decoded state are not committed. Acceptance uses temporary staged profiles with deliberately wrong historical level, attributes, points, difficulty, equipment and progression. Actual saved values must win. Current game mechanics are not mocked; the static database is shared in memory to avoid repeated parsing.

## Exact files changed

|File|Change|
|---|---|
|`production_data.py`|Required current-state validation, removal of historical fallbacks/difficulty overrides, optional-progression notices, derived cache provenance|
|`save_bridge.clj`|Expose current per-difficulty main-campaign quest progression|
|`review.py`|Quest-aware decode cache invalidation; strict current baseline verification in both modes|
|`production_search.py`|Saved-difficulty engine targets for Mal and Beeztrap|
|`beeztrap_equipment.py`|Saved-difficulty target/label; remove legacy difficulty override|
|`beeztrap_production.py`|Saved-difficulty target and current-state report labels|
|`production_report.py`|Correct Normal/Elite/Ultimate report label|
|`test_stage2.py`|Focused unit and private-save acceptance tests; no search|
|`Runtime_Integrity.json`|Updated hashes and new focused-test entry|
|`README.md`|Stage 2 status/results link|
|`PRODUCTION_v1_3.md`|Current-state authority, difficulty, validation/cache behavior and deferred account limitations|
|`docs/ROADMAP.md`|Stage 2 completion status, later stages still pending|
|`docs/STAGE2_RESULTS.md`|This evidence and remaining mechanics blocker|

## Stage 3 handoff

Implement the specified transferable unequipped item pool separately. Selected-character equipped items remain its baseline; other characters' equipped items stay unavailable. Current save authority and saved difficulty must remain intact. Quick mode still reuses account stash/recipe/resource snapshots; full account handling and procurement remain later-stage work. Preserve per-difficulty progression rather than treating quest access as a single faction-reputation number. The separate Mal maximum-Chaos-cap discrepancy remains a certification blocker until corrected and tested.
