# Beeztrap: 3% offensive materiality

Selection policy only. The standalone `cadence_scenarios.py` model, all 32 scenarios, damage calculations and uncertainty blockers remain unchanged. Mal/generic scoring remains at 5%. No equipment search or recommendation regeneration was performed.

Use `BeeztrapMateriality(engine).compare(candidate_state)` from `beeztrap_materiality.py`. This wrapper requires a supported advantage greater than 3% in every scenario. Exactly 3% is insufficient. It returns the unchanged scenario indices and blockers, with the Beeztrap-specific decision policy. The original scorer API retains its historical default. Search integration remains disabled.

Favor progression upgrades only when the gain is robust, the configuration is defensively neutral and its existing-model cost is inexpensive. Neutral means no decrease in health, DA, armor, absorption, physical resistance, useful standard resistance headroom (up to cap+20), or recognized life steal/regeneration inputs. Incidental resistance beyond cap+20 can decrease without penalty. Other existing defensive floors and eligibility checks still apply.

The explicit inexpensive gate is utility cost <=12, component opportunity cost <=4, zero destroyed attachments and zero attribute points spent. These are conservative policy limits, not iron prices. No existing component price or cost arithmetic was altered.

The shared-stash Sabre offhand comparison remains 103.636–103.678. It now clears the 3% threshold, but the inherited cost model prices its assumed component installation at 18 opportunity-cost points (41.15 total utility), so it does not automatically pass the inexpensive gate.

All 45 regression tests pass, including three policy tests for threshold/blockers, defense/cost gates, and identical real-item scenario indices. All 53 original v1.2 files remain unchanged.

This ZIP is a small additive update: extract its `Optimizer` contents into the existing Task 2C project. It contains the policy wrapper, its tests, these notes and regression results; it does not replace the extracted databases or original modules.
