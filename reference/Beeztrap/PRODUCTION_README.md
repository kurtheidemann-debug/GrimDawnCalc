# Beeztrap minimum viable production

Python 3.11+; standard library only. Start inside the extracted `Optimizer` folder.

```bash
python beeztrap_production.py
python -m unittest discover -v
```

The included cached Balanced result is in `production-results/Beeztrap_Balanced.md` with exact IDs, source locations, selected components/augments, costs, faction access, Elite/Ultimate resistances, validation and offense warnings. The JSON beside it retains the full state and all 32 final comparison indices.

Default reruns use a hash-checked cache. To repeat the same bounded search:

```bash
python beeztrap_production.py --force --seconds 75 --width 4
```

This is one Balanced beam over owned equipment, shared stash, eligible augments and affordable/owned components. It starts from current gear and the existing validated defensive repair, builds small per-slot joint bundles, and evaluates complete loadouts with the unchanged standalone Cadence scorer. It is not a global optimum proof. The hard defensive gates are all nine Elite resistances capped, health at least current, DA>=1900, armor>=95% current, absorption>=90%, and physical resistance at least current. Ultimate shortfalls are projected explicitly. Four unspent attributes and fixed saved skills/devotions/bindings are retained.

Beeztrap's 3% policy is applied after all 32 scenario scores and blockers. Unsupported comparisons remain diagnostic, never certified offensive gains. The selected defensive repair has a 97.43–97.47 direct-offense estimate with a blocker. Costs use existing preference utility plus separately reported base iron. Mal retains original modules/results and its 5% policy.

No game save is modified. No game archives or normalized databases are rebuilt. Shared database snapshots in the character folder are restored from the included root files if needed. Raw supplied saves, decoder JAR, normalized inventory/database, recipes, tests and archived benchmarks are included.

Restore disclosure: the local Task 2C input ZIP was truncated. The already-extracted checkpoint was retained; 73 completed ZIP entries were CRC-checked against it and all 53 original v1.2 file hashes verified before applying the CRC-verified policy patch. No previously completed work was recreated.

The complete production ZIP is also supplied in three smaller backup parts because large ZIP transfers have been truncated in this session. Keep the parts, `restore_production_zip.py` and `Production_Verification.json` together; run the script to reconstruct and SHA-256/CRC-verify the exact full ZIP if needed. These are byte segments, not separate extractable archives.
