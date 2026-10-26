# Grim Dawn practical equipment optimizer

Continue the supplied checkpoint without re-extracting the game databases. Python 3.11+; standard library only for optimization and tests. Java 17 is required only when refreshing original game/save extraction.

## Run

From this folder:

```
python practical_optimizer.py
python -m unittest discover -v
```

`python GrimDawn_Optimizer.py` also runs the practical search. Identical inputs return cached results without loading the game database into the engine. `--force` recomputes; `--width 24 --rounds 3` broadens the finite search. Default width 16, two passes, deterministic. `--data PATH --out PATH` supports refreshed snapshots. Results live in practical-results/results.json and Mal_Practical_Results.md.

## Fixed character build

Invested skills, devotion selections, devotion experience/ranks and bindings come from mal.json and cannot change. The invariant is enforced in legality checks and regression tests. Gear can increase effective ranks, including relevant passive, mastery and devotion effects. Saved unused skill/devotion points stay unused. No attribute reset is considered. Attribute points are spent only to meet equipment requirements, including the inherited equip-order proof. Otherwise they stay unspent.

## Equipment search

The preserved engine provides decoding, item rolls, crafting/material availability, faction mapping, slot restrictions, unique physical item checks and character-stat calculations. Default legacy calculator behavior and all original tests remain. The practical path skips the legacy encounter ramp and hit/defense scoring and discards legacy comparison outputs.

Each slot receives joint item/component/augment bundles. The search shortlists six native gear alternatives per slot, four component alternatives for each, then tests eligible augments and retains twelve bundles plus current and archived benchmark bundles. A beam of complete loadouts combines these across all fourteen slots, including intermediate states that temporarily fail resistance or attribute requirements. Final results must pass requirements, equip order and shared resource checks. Benchmark starts import equipment only: their old skills/devotions/attributes are never imported. Search is bounded; shortlist and beam choices can miss better configurations.

All outcomes require nine capped standard resistances, DA >=1900, health >=9500, armor absorption >=84%, and offense index >=95 (current=100). These are explicit progression policy defaults, not universal safe-play thresholds. Useful overcaps are rewarded through +20; higher amounts remain reported but earn no extra index benefit. Physical resistance, DA, health, armor and absorption all contribute directly to the defense index. No enemy hit or encounter is simulated.

## Relative offense

Static Storm Totem strength uses the rank-dependent native lightning coefficient, applicable flat/lightning/total item modifiers, effective spell ranks, lightning/elemental/total bonuses, Spirit, a monotonic OA and crit-damage rating factor, totem capacity, burst deployment and cooldown utility, and the fixed build's resistance reduction. Deployment is `(4.5 / cooldown * burst)^0.35`; this is a utility weight, not estimated casts per second. Wind Devil uses effective Wind Devil + 1.5 times Maelstrom ranks, relevant recognized item modifiers and a small CDR utility. The overall offense index is 80% relative Totem strength + 20% relative Wind Devil strength. Current=100. OA factor is OA/2000 times (1+crit damage/500). RR is a static comparative utility, not resistance against a hypothetical enemy. No individual hits, ticks, damage-over-time duration/stacking, proc uptime, combat encounter or measured DPS is calculated for selection. Cold contributions, conversions and non-lightning proc damage are not comprehensively modeled. These approximations favor repeatability over false precision.

Defense is a geometric utility relative to current: health weight .30, DA .30, armor .15, absorption .15, and (100+physical resistance) .10, with up to 10% utility from useful standard resistance overcaps. This is not EHP. All actual estimated stats are separately reported.

## Practical cost and 5% rule

Costs below are preference units, not iron quotations:

- Equipment change: 4; destroyed attached component: 8; new component application: 1.
- New faction augment purchase: 0.15; new attribute point: 2.
- Owned common/magical components: 2 opportunity units; other components without an available recipe: 18.
- Craftable component: 1 plus base iron/5000 plus recursive ingredient costs divided by recipe yield. Non-component recipe materials add 15 per unit; component ingredients are recursively valued when recipes exist, or add 1 for a simple ItemRelic reagent. Thus rare material sinks stay costly even when stock is available.
- Component opportunity costs are doubled below level 100. Existing attachments on the same item are free to retain. Shared stock and known/default recipes remain gated by the original resource checker.

Minimal cost selects the least-cost feasible endpoint. Balanced uses equal log weights for offense and defense with a cost penalty. Maximum offense selects the highest relative offense among feasible endpoints, then applies the materiality rule. It is the optional ceiling: it can use expensive components when the gain is material. Review that cost before buying a temporary level-74 upgrade.

The materiality rule chooses a cheaper endpoint retaining at least 95% of reference offense and defense utility, provided health/DA/absorption retain 95% and armor retains 90%. A stronger cheaper endpoint also qualifies. The comparison stays anchored to the original winner to avoid chained 5% degradation. Three objectives may return the same configuration; distinctions are not manufactured.

## Refresh and incremental reruns

Use the existing read-only extractor, with the real game and save paths:

```
python refresh_data.py --game "E:\SteamLibrary\steamapps\common\Grim Dawn" --save "C:\Program Files (x86)\Steam\userdata\40109294\219990\remote\save" --out refreshed
python practical_optimizer.py --data refreshed --out refreshed-results
```

Verify that the save path contains the actual current player/stash files. No live saves are edited. The existing decoder is unchanged. Optimization reuses extracted JSON/gzip data and memoizes states and item/attachment calculations within a run. Result reuse is keyed by code, relevant extracted inputs, archived starts and search settings. Changed inputs trigger a new bounded search, not game re-extraction. It does not yet reuse individual evaluated states across changed snapshots. Refresh after leveling or changing inventory; do not extrapolate level-74 stats to 100. Item IDs belong to their snapshot.

## Archives and verification

archive/results holds the original results unchanged. archive/GrimDawn_Optimizer_original.py is the untouched original source for reference. `python GrimDawn_Optimizer.py --legacy` explicitly invokes the retained old optimizer; its skill/devotion/respec recommendations are archived benchmarks and are outside the revised workflow.

All seven original tests remain unchanged. New tests cover fixed skills/devotions/bindings in search and delivered outputs, the actual attachment cost model, the 5% materiality rule, preservation of unspent attributes and removal of encounter comparison outputs. Baseline audit still reproduces all 34 exported numerical values. This validates agreement with the original decoder formulas, not independent live-game instrumentation.

The bundled gd-edit jar is third-party software; see LICENSE.txt. PDF and Excel formatting are deferred pending review.
