# Grim Dawn practical equipment optimizer v1.2

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

The preserved engine provides decoding, item rolls, crafting/material availability, faction mapping, slot restrictions, unique physical item checks and character-stat calculations. Default legacy calculator behavior and all original tests remain. The practical path skips the legacy encounter ramp and hit/defense scoring and discards legacy comparison outputs. relative_offense.py supplies reusable ability scoring. The search, cost coefficients, materiality rule, fixed-build guards and defensive floors remain intact.

Each slot receives joint item/component/augment bundles. The search shortlists six native gear alternatives per slot, four component alternatives for each, then tests eligible augments and retains twelve bundles plus current and archived benchmark bundles. A beam of complete loadouts combines these across all fourteen slots, including intermediate states that temporarily fail resistance or attribute requirements. Final results must pass requirements, equip order and shared resource checks. Benchmark starts import equipment only: their old skills/devotions/attributes are never imported. Search is bounded; shortlist and beam choices can miss better configurations.

All outcomes require nine capped standard resistances, DA >=1900, health >=9500, armor absorption >=84%, and offense index >=95 (current=100). These are explicit progression policy defaults, not universal safe-play thresholds. Useful overcaps are rewarded through +20; higher amounts remain reported but earn no extra index benefit. Physical resistance, DA, health, armor and absorption all contribute directly to the defense index. No enemy hit or encounter is simulated.

## Relative offense and resistance audit

See Mal_Practical_Audit_v1_2.md for verified v1.1 arithmetic and all nine resistances for each old and revised build. `python audit_v11.py` reproduces the old factor products, compares old states with the preserved stat calculator, and writes audit/v11_audit.json. It does not rerun the old search.

The new scoring layer discovers attack records through learned roots, ranked spawnObjects, actor skillName/skillLevel links, buff/debuff/projectile links and saved secondary petSkillName links. Zero-level pet modifier hooks are excluded unless the saved build activates them. Targeted item modifiers are read from their exact modifiedSkillName records. The framework has no Storm Totem or Wind Devil path-name tests.

Scoring separates player direct attacks/spells, temporary deployables/summons and permanent pets. Each damaging node uses its rank-dependent DB flat damage and relevant damage bonuses. Player- and pet-scaling domains remain separate. The current character name selects owned gear from the normalized catalog; the existing raw decoder is unchanged.

For temporary instances, sustainable population is bounded by `min(maximum, duration * burst / deployment_interval)`. A closed-form eight-second setup utility, averaged with sustainable availability, discounts slow establishment. This is a declared comparison policy, not an encounter timeline. Permanent pets receive full post-setup population and no attack multiplier from the owner's CDR or cast speed. Player cast speed can shorten a summon action only when action time, rather than cooldown, limits deployment.

An explicit DB target interval is used for autonomous frequency. Missing animation frequency uses a normalized 1, with a limitation in the output; player attack/cast speed never accelerates autonomous player-scaling pets. Regular pet speed bonuses come from petBonusName records. Direct abilities use normalized one-second base actions and their appropriate speed/cooldown limits. AI priorities, animation time, active-buff recast gaps, projectile overlaps, WPS, weapon payload and survival are not solved. A weapon-dependent payload is flagged and omitted rather than invented; a build with no supported damaging payload fails the offense gate instead of receiving fabricated strength.

Percentage damage is additive within its category, evaluated relative to existing bonuses. Elemental flat damage splits three ways while % Elemental applies fully to direct Fire/Cold/Lightning. Corresponding DoT bonuses remain separate. Skill modifiers precede local conversion, then global conversion of remaining unconverted damage, then destination global damage bonuses. Converted damage never converts again. Recognized flat skill modifiers are included. Ambiguous root modifiers are assigned conservatively to one primary attack; explicit attack targets retain their scope. Weapon/global flat payload, multi-stage pet-buff conversion and special engine behaviors require verification before trusting those build types.

DoT receives same-source refresh coverage, not an attacks-per-second stacking multiplier. Attacking pet instances can contribute independent sources. Identical debuff auras apply once, including their damage. No lingering extra DoT population from retired summons is credited. Duration bonuses can improve coverage; no individual ticks are simulated.

RR categories are kept separate: distinct named additive debuffs sum, repeated same-source debuffs deduplicate, strongest relative reduction and strongest flat reduction apply. The actual order is additive, relative, flat. Since this is enemy-free comparison, additive+flat RR receive a static utility and relative RR is reported without inventing an unconditional damage multiplier. Only profiled damage/support abilities and offensively bound saved devotion powers enter RR. Uptime/proc probability is not predicted; categories describe available potential, not guaranteed coverage.

The small offense_profile.json file retains Mal's policy of 80% Totem / 20% Wind Devil emphasis. Paths and weights are data, not framework rules. Removing the file or importing a different character automatically discovers learned damaging roots and uses their baseline contribution weights; review that emphasis before using another build. Saved skills and devotion experience remain fixed. Unsupported mechanics are listed in results.json. This is a simple relative utility, never measured DPS.

Defense remains the v1.1 geometric utility: health .30, DA .30, armor .15, absorption .15, physical resistance .10, plus at most 10% across useful overcaps. Each resistance's overcap contribution stops at +20. Incidental excess is not penalized. Poison 123 and 169 both receive the same resistance utility.

The report's legacy JSON `raw` key means **difficulty-adjusted, before cap**. New explicit aliases record before_difficulty_penalty, difficulty_penalty and difficulty_adjusted_before_cap. Ultimate penalties are taken once from the supplied DB balancing record: -50 for Fire/Cold/Lightning/Poison/Pierce; -25 for Bleeding/Vitality/Aether/Chaos; none for Physical. They are difficulty-specific totals, not Elite plus Ultimate. Startup checks reject stale penalties.json. Character-sheet totals are calculated, not stored in player.gdc. Baseline export agreement remains a shared-decoder check, not an independent live screenshot measurement.

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
python refresh_data.py --character Mal --game "E:\SteamLibrary\steamapps\common\Grim Dawn" --save "C:\Program Files (x86)\Steam\userdata\40109294\219990\remote\save" --out refreshed
python practical_optimizer.py --data refreshed --out refreshed-results
```

Verify that the save path contains the actual current player/stash files. No live saves are edited. The existing decoder is unchanged. Optimization reuses extracted JSON/gzip data and memoizes states and item/attachment calculations within a run. Result reuse is keyed by code, relative_offense.py, offense_profile.json, relevant extracted inputs, archived starts and search settings. Changed inputs trigger a new bounded search, not game re-extraction. It does not yet reuse individual evaluated states across changed snapshots. Refresh after leveling or changing inventory; do not extrapolate level-74 stats to 100. Item IDs belong to their snapshot.

## Archives and verification

archive/results holds the original results unchanged. archive/v1.1 holds the previous practical source and results unchanged. archive/GrimDawn_Optimizer_original.py is the untouched original source for reference. `python GrimDawn_Optimizer.py --legacy` explicitly invokes the retained old optimizer; its skill/devotion/respec recommendations are archived benchmarks and are outside the revised workflow.

All sixteen v1.1 tests remain unchanged. Eight focused audit tests additionally cover DB difficulty totals, duration-limited and permanent populations, direct damage versus pet scaling, conversion, RR category stacking and overcap saturation. Existing tests cover fixed skills/devotions/bindings in search and delivered outputs, the actual attachment cost model, the 5% materiality rule, preservation of unspent attributes and removal of encounter comparison outputs. Baseline audit still reproduces all 34 exported numerical values. This validates agreement with the original decoder formulas, not independent live-game instrumentation.

The bundled gd-edit jar is third-party software; see LICENSE.txt. PDF and Excel formatting are deferred pending review.

For another character, use `refresh_data.py --character NAME ... --out NEW_FOLDER`, then `practical_optimizer.py --data NEW_FOLDER --out NEW_RESULTS`. The refresh selector changes only which already-decoded character is exported. Other calculator limitations remain subject to the baseline validation gate. No claims of universal full skill coverage are made.
