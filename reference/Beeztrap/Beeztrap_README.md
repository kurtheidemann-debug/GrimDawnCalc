# Beeztrap checkpoint on Practical Optimizer v1.2

Read Beeztrap_Build_Assessment.md and Beeztrap_Practical_Results.md first.

This is a limited defensive attachment repair on current dual-wield Cadence equipment. It is not a new combat model or a verified maximum-offense loadout. The original v1.2 modules and Mal snapshots/results remain untouched.

From Optimizer/:

```
python beeztrap_equipment.py --elite --attachments-only
python -m unittest discover -v
python verify_beeztrap.py
```

The first command reuses a hash cache when inputs match. Do not treat its neutral internal offense index as measured/ranked Cadence effectiveness. `--force` repeats the bounded attachment search and limited reversions to current attachments. Original full-equipment attempts were rejected under conservative guards; no claim of global infeasibility is made.

The Beeztrap adapter freezes invested skills, devotions, bindings and current gear. Weapon attachments stay fixed. Key effective ranks, attack speed and life-steal inputs are protected; small reductions in other recognized offensive inputs are explicitly limited/reported. The v1.2 component-cost arithmetic and 5% preference method are unchanged. Since full Cadence offense is unscored, the method cannot prove a 5% total-DPS band.

The original stat calculator, inventory database, faction mapping and raw-save decoder are unchanged. The adapter handles the second sword as a sword for attachment eligibility. It also uses observed weapon/jewelry-specific requirement reductions conservatively, avoiding unnecessary Spirit spending from the original generic check. No save is edited.

Beeztrap's imported data are in characters/Beeztrap/. The shared database/localization files are omitted from that subfolder in the ZIP to avoid storing duplicate copies. The run command restores these files from the root on first use. No network download is needed. All current Mal data and archived outputs remain at their original paths.

The original v1.2 checkpoint supplied back to this task was truncated. All 24 complete entries matched the preserved v1.2 project files. A separate rebuilt archive of those same preserved files (not a rewritten optimizer) was fully ZIP/CRC-tested for backup. The Beeztrap checkpoint is also ZIP/CRC-tested before delivery.

The fresh raw save snapshot is retained under source-saves/save.zip. Re-importing only the save using existing normalized game data is available through extract_snapshot.clj with the unchanged bundled decoder jar. It is a read-only wrapper; no ARZ re-extraction is required.
