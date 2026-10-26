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

Stage 2 save-state authority is implemented; later v1.3.6 stages are not released.
See [Stage 2 results](docs/STAGE2_RESULTS.md) for focused tests, cache provenance,
saved-difficulty behavior, and the current Mal maximum-Chaos-resistance blocker.
