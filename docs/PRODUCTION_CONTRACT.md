# Save-driven Production Contract

Status: **proposed v1.3.6 acceptance contract**, not a claim about v1.3.5 capabilities.

## Inputs

Exactly two required user inputs: (1) a complete `saveX.zip`, (2) the target character's name. No historical report, cached character-state baseline, manual inventory refresh, difficulty choice or separate character inventory upload is required.

## Authority

The selected character's **current saved difficulty is authoritative**. Do not override it with a stored profile, automatically target Ultimate, or prompt for a different difficulty. If the user saved in the wrong difficulty, the user must resave and upload a corrected ZIP.

Read level, attributes, invested skills, effective ranks, devotions, bindings, equipment, reputation, progression and ownership from the current save. Static game databases may resolve mechanics and requirements; persistent profiles may define **build-specific scoring policy**, never overwrite current saved state.

## Candidate inventory

Use **all transferable items that are not currently equipped on any character**, across all characters' inventories, personal storage and shared stash. Include the target character's equipped items as the starting loadout, allowing them to be retained or replaced. Exclude other characters' equipped items and nontransferable items. Preserve physical item identity, quantity, ownership, location, affixes, attached components and augments. Do not conflate alternate weapon-set ownership with a freely available item without checking equipped status.

## Loadout and attachments

Search all eligible equipment slots and supported weapon pairs. Maintain legal class, level, attribute, slot, transfer, resource and attachment constraints; retain existing defensive, materiality and uncertainty policies. Evaluate components and augments in context, accounting for owned stock, crafting recipes/resources, reputation and quest-based access where supported.

Distinguish **legally eligible**, **already owned**, **currently craftable**, **currently purchasable**, and **availability or price unverified**. An incomplete vendor price table must not block otherwise supported owned-item optimization; it may limit acquisition or cost claims. Do not assume access to unverified vendors.

## Build-specific scoring

- **Beeztrap**: existing Cadence scenarios and offensive mechanics; permit supported comparisons of alternate dual-wield weapon pairs. Do not bypass unsupported mechanics blockers.
- **Mal**: existing Storm Totem model, including effective skill ranks, simultaneous totem capacity, cooldown and relevant item modifiers.
- Future characters: additional mechanics evaluators without rebuilding the common ingestion, inventory and reporting pipeline. Multi-module scoring is a future design allowance, not a v1.3.6 prerequisite.

## Deliverables

A complete best-practical-found loadout, every changed equipment slot, exact item source/location, component and augment actions, feasibility and defensive summary, acquisition/crafting qualifications, and conservative keep/sell inventory dispositions. Protect uncertain, future-use or unsupported items from automatic safe-to-sell claims.

## Acceptance

With `save9.zip` and `Beeztrap` or `Mal`, the workflow must read current state, use saved difficulty, include eligible cross-character inventory, respect other characters' equipped items, and produce a legal actionable result or a precise evidence-based blocker. Cadence weapon-pair search must be enabled where supported; Storm Totem stack/cooldown behavior must remain correct. Verify unique physical items and transfer restrictions, attachment feasibility, and no historical character-state overrides.

The previously reported save audit found seven readable characters, 330 main shared-stash entries and 759 resolved item instances, plus recipe/resource/reputation/binding data. These are **audit reference figures**, not hardcoded expectations for future ZIPs. Full vendor access and price-rule coverage remain unverified.

## Non-goals

No save edits, no mathematically certified exhaustive global optimum, no automatic difficulty override, no mandatory refactor of validated scoring engines, and no unsupported acquisition or disposal claims.
