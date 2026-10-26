# Grim Dawn Practical Optimizer v1.3

Default workflow: upload `save.zip`, run `python review.py save.zip`, and return
the character’s generated Markdown report from `reviews/latest/`. Quick Review
is the default; it does not rebuild the database or rerun regressions for an
ordinary inventory update. It never edits a supplied save.

- Quick: `python review.py save.zip`
- Select Beeztrap: `python review.py save.zip --character Beeztrap`
- Explicit Full Refresh: `python review.py save.zip --mode full --character Mal`

Read [PRODUCTION_v1_3.md](PRODUCTION_v1_3.md) for the full workflow, profile rules,
time bounds, accepted Chaos exception, inventory policy, and validation behavior.
Read `reviews/latest/Mal_Gear_Review.md` for the current actionable Mal result.
`Production_Acceptance.json` records the measured end-to-end checks.

Requirements: Python 3.11+ and Java 17+. All decoded static game data, the seeded
item decoder, both independent profiles, source fixtures and original regression
tests are bundled. The preserved v1.2 README is in `reference/README_v1_2.md`.

Run `python validate.py` after code/database changes. A matching shipped software
validation certificate skips that suite during routine reviews. No manual
regression campaign or source game installation is needed for normal saves.

Stage 2 save-state authority and the requested Stage 3 equipment mechanics
reconciliation are implemented; remaining v1.3.6 features are not released.
See [Stage 2 results](docs/STAGE2_RESULTS.md) and [mechanics results](docs/EQUIPMENT_MECHANICS_RECONCILIATION.md).
Both current Save 9 characters pass strict baseline verification; no Full Review was run.

Stage 4 suspends inventory keep/sell reports while preserving equipment candidates.
Exact per-call Cadence packet reuse reduced a bounded fixture runtime by 38.84%;
see PRODUCTION_v1_3.md for measurements and focused validation.

Stage 5 pools uploaded characters’ equipment from bags, personal stashes and
equipped slots in both review modes, with exact owner/location reporting.
Beeztrap’s fixed weapons and suspended keep/sell workflow remain in effect.
