# Practical Optimizer Architecture

Status: **target architecture**, documented in Stage 1; implementation remains v1.3.5 until subsequent stages are merged.

## Core pipeline

1. Extract a user-supplied `saveX.zip` without modifying it.
2. Decode every character and shared storage; select the requested character.
3. Construct the current character state solely from the selected save: level, attributes, skills, devotions and bindings, equipment, faction reputation, quest/progression state, and saved difficulty.
4. Build an owned-item catalog with stable physical-instance identities, storage locations, transfer eligibility, and attachments.
5. Evaluate legal equipment, components, augments, crafting and acquisition constraints.
6. Score full loadouts through shared defense/feasibility calculations and build-specific offensive mechanics.
7. Perform a practical bounded search, then report equipment, attachments, item sources, acquisition uncertainty, and conservative inventory dispositions.

## Responsibility boundaries

- **Save adapter**: current-state decoding; never substitutes persistent historical character snapshots.
- **Inventory/ownership**: candidate pool comprises all transferable, unequipped items in all decoded characters' inventories/personal storage and shared stash, plus the selected character's currently equipped items as its baseline. Items equipped on other characters are unavailable. Preserve identity, location and transfer restrictions; alternate weapon sets must be classified according to actual equipped status, not assumed free.
- **Static data/eligibility**: item bases, affixes, requirements, attachment compatibility, faction thresholds, recipe and resource requirements, quest/vendor availability. Distinguish owned, craftable, purchasable, eligible, and unverified.
- **Mechanics evaluators**: build-specific offensive scoring and supported interactions. Existing Cadence and Storm Totem implementations are retained, not rewritten in Stage 1.
- **Common optimizer**: shared defensive metrics, legality, resource accounting, materiality/uncertainty policies, bounded equipment search, and reporting.
- **Reports**: explain changes, exact physical item sources, component/augment actions, assumptions, limitations, and evidence before any sell/dismantle recommendation.

## Existing implementation landmarks (v1.3.5)

- `review.py`: workflow orchestration, decoding, profile staging, validation, search and reports.
- `production_data.py` and `save_bridge.clj`: save ingestion/decoding.
- `production_search.py`: `MalEngine`, `CadenceEngine`, bounded search.
- `cadence_scenarios.py`, `beeztrap_production.py`, `beeztrap_equipment.py`, `beeztrap_materiality.py`: Cadence evaluation and constraints.
- `production_report.py`, `item_valuation.py`, `inventory_decisions.py`: reporting and disposition.

These are landmarks, **not assertions that the target contract is already implemented**. In v1.3.5, `review.py` stages persistent profiles; `production_search.py` explicitly fixes Cadence weapon slots; cross-character pooling and some acquisition constraints are incomplete.

## Mechanics evolution

Cadence and Storm Totem are the first build-specific evaluators. Future modules may model channeling/whirlwind, pets, procs, and other skill interactions. A character may eventually combine several modules; avoid imposing a permanent one-module-per-character assumption. Preserve the validated existing models. Document and introduce the smallest necessary interface when another build requires it; **do not preemptively refactor** working scorers.

The module should ultimately receive current decoded character state, candidate loadout, and resolved static mechanics data; return offensive estimates, supported constraints, uncertainty flags and diagnostic breakdowns. Common eligibility, defense, inventory, search and reporting remain independent of individual skills.

## Search quality and failure handling

A bounded heuristic returns the best practical feasible candidate **found**, not a certified global optimum. Search effort bounds are not whole-workflow timeouts. Unsupported mechanics, missing acquisition rules or model discrepancies must be disclosed and scoped; never silently fabricate eligibility, certify unsupported comparisons, or classify uncertain items as safe to vendor.
