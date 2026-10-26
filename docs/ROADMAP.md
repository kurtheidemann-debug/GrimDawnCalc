# Production Roadmap

Status: Stages 1 and 2 implemented. Stages 3–6 remain planned and must be separately implemented and verified. See `STAGE2_RESULTS.md` for the separate Mal mechanics blocker; this is not the complete v1.3.6 release.

## Execution discipline

One bounded stage per Work session. Start from the GitHub repository, use a feature branch, change only stage-relevant code, run focused tests, publish a commit/PR, and stop. Do not expand into project recovery, database rebuilding, wholesale refactoring or unrelated regression campaigns. Report blockers with exact module and evidence. A search-effort guideline is **not** an end-to-end session timeout. Full integration testing belongs in Stage 6, except where a specific earlier change requires broader tests.

## Stage 1 — Document the contract

Create `ARCHITECTURE.md`, `PRODUCTION_CONTRACT.md` and this roadmap. No production code or database changes. **Completion:** documentation committed in GitHub.

## Stage 2 — Save-state authority

Ensure saved difficulty and selected-character current state override all historical profile snapshots. Retain persistent build-scoring policy only. Verify current level, skills, devotions, bindings, reputation and progression from current ZIP; scope independent model/calibration discrepancies rather than suppressing material defects. **Completion:** focused Beeztrap/Mal save-state tests pass.

## Stage 3 — Transferable owned-item pool

Collect all eligible unequipped transferable items across all characters and shared storage; retain target's equipped baseline, exclude other characters' equipped items, preserve physical-instance identities and locations. **Completion:** inventory enumeration and transfer/duplicate tests pass against `save9.zip`.

## Stage 4 — Attachment and acquisition feasibility

Connect owned augments/components, recipes, shared crafting resources, faction reputation and quest-based vendor/blacksmith access. Distinguish owned/craftable/purchasable/unverified. Incomplete vendor price coverage should qualify acquisition recommendations, not invalidate supported equipment search. **Completion:** focused legality/resource/access tests and actionable attachment output.

## Stage 5 — Complete supported equipment search

Enable Cadence dual-weapon pair comparisons and all eligible equipment slots while preserving existing scoring, materiality, defensive constraints and uncertainty blockers. Maintain Mal's simultaneous Storm Totem/cooldown scoring. **Completion:** weapon-pair comparison tests and both mechanics regression checks pass.

## Stage 6 — End-to-end acceptance and release

Run `save9.zip` for Beeztrap and Mal with no other user inputs. Produce complete loadout, attachments, locations and conservative inventory disposition. Run integration/regression checks and document residual limitations. **Completion:** reproducible production reports and published v1.3.6, or a precise documented blocker if not ready.

## Beyond v1.3.6

Add mechanics evaluators incrementally as new builds appear: whirlwind/channeling, pets, procs and combinations. Design a shared module interface only when demonstrated by a concrete third module; preserve existing validated Cadence and Storm Totem behavior.
