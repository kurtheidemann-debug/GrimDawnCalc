"""Cadence adaptation checkpoint 1: auditable inputs, no invented cycle multiplier.

Read-only adapter over v1.2 snapshots. Existing recommendations are not changed.
Run: python cadence_inputs.py --output Cadence_Input_Audit.json
"""
import argparse
import copy
import hashlib
import json
import shutil
from pathlib import Path
from GrimDawn_Optimizer import at
from relative_offense import payload_of

FIXED_KEYS = ('skills', 'devotions', 'bindings', 'attributes')


def configuration_hash(state):
    return hashlib.sha256(json.dumps({k: state[k] for k in FIXED_KEYS},
                                     sort_keys=True).encode()).hexdigest()


def ranked_numbers(record, rank):
    """Preserve numerical mechanics at effective rank, including unfamiliar fields."""
    return {k: at(v, rank) for k, v in record.items()
            if isinstance(v, (int, float)) or
            isinstance(v, list) and v and isinstance(v[0], (int, float))}


def weapon_input(engine, state, slot):
    item = engine.items[state['gear'][slot]]
    base = engine.db[item['save']['basename']]
    rolled = item.get('worn-rolled') or item.get('rolled') or {}
    # Normalized rolls omit intrinsic physical weapon damage. Prefer rolled
    # bounds when present; otherwise retain database bounds, never add both.
    intrinsic = {}
    provenance = {}
    for bound in ('Min', 'Max'):
        field = 'offensivePhysical' + bound
        intrinsic[field] = rolled.get(field, base.get(field, base.get('offensivePhysicalMin', 0)))
        provenance[field] = 'seeded roll' if field in rolled else 'database base'
    lo, hi = intrinsic.values()
    if lo < 0 or hi < lo:
        raise ValueError('Invalid intrinsic weapon damage range')
    records = engine.item_records(item['id'], state['comp'][slot], state['aug'][slot])
    conversions = []
    for record in records:
        for suffix in ('', '2', '3', '4', '5', '6'):
            src = record.get('conversionInType' + suffix)
            dst = record.get('conversionOutType' + suffix)
            if not src or not dst:
                continue
            field = 'conversionPercentage' + suffix
            # A roll is usable only if the item has one unambiguous mapping
            # for this field. Multiple mappings remain separately visible.
            mappings = sum(bool(r.get('conversionInType' + suffix)) for r in records)
            use_roll = mappings == 1 and field in rolled
            conversions.append({'source': src, 'destination': dst,
                                'percent': rolled[field] if use_roll else at(record.get(field)),
                                'provenance': 'seeded roll' if use_roll else 'database base',
                                'scope': 'UNVERIFIED: local versus global'})
    return {'slot': slot, 'id': item['id'], 'name': item['name'],
            'owner': item['owner'], 'location': item['location'],
            'record': item['save']['basename'], 'class': base.get('Class'),
            'intrinsic_physical_range': intrinsic,
            'intrinsic_physical_mean': (lo + hi) / 2,
            'damage_provenance': provenance,
            'rolled_item_fields': copy.deepcopy(rolled),
            'armor_piercing_percent': rolled.get('offensivePierceRatioMin', at(base.get('offensivePierceRatioMin'))),
            'conversions': conversions,
            'component': state['comp'][slot], 'augment': state['aug'][slot],
            'speed_tag': base.get('characterBaseAttackSpeedTag'),
            'base_speed_adjustment': rolled.get('characterBaseAttackSpeed', at(base.get('characterBaseAttackSpeed')))}


def targeted_modifiers(engine, state):
    out = {}
    for slot, ident in enumerate(state['gear']):
        records = engine.item_records(ident, state['comp'][slot], state['aug'][slot])
        for record in records:
            for i in range(1, 6):
                target = record.get('modifiedSkillName' + str(i))
                path = record.get('modifierSkillName' + str(i))
                if target and path:
                    out.setdefault(target, []).append({'item_id': ident, 'slot': slot,
                        'modifier_record': path, 'fields': ranked_numbers(engine.db.get(path, {}), 1)})
    return out


def extract_inputs(engine, state=None, calculated=None):
    state = engine.current if state is None else state
    before = copy.deepcopy(state)
    v = engine.evaluate(state) if calculated is None else calculated
    eff = v['effective_skills']
    roots = [p for p in state['skills']
             if engine.db[p].get('Class') == 'Skill_WeaponPool_ChargedFinale']
    if len(roots) != 1:
        raise ValueError('Exactly one saved charged-finale primary attack is required')
    root = roots[0]
    mods = targeted_modifiers(engine, state)
    skills = {}
    # Discover the family through existing database family metadata rather than
    # selecting secondary attacks because they happen to expose flat damage.
    from GrimDawn_Optimizer import family
    root_family = family(root, engine.db[root])
    for path, invested in state['skills'].items():
        record = engine.db[path]
        if not (root_family & family(path, record) or record.get('skillChanceWeight')):
            continue
        rank = eff.get(path, invested)
        entry = {'name': engine.name(path), 'invested_rank': invested,
                 'effective_rank': rank, 'class': record.get('Class'),
                 'fields': ranked_numbers(record, rank),
                 'native_payload': dict(payload_of(record, rank)),
                 'item_modifiers': mods.get(path, [])}
        if record.get('buffSkillName'):
            buff = record['buffSkillName']
            entry['linked_buff'] = {'record': buff,
                'fields': ranked_numbers(engine.db.get(buff, {}), rank),
                'native_payload': dict(payload_of(engine.db.get(buff, {}), rank))}
        skills[path] = entry
    assert state == before, 'Input extraction mutated saved build'
    return {'schema': 1, 'status': 'INPUT_ADAPTER_READY_CYCLE_NOT_VERIFIED',
            'offense_rankable': False, 'character': engine.character_name,
            'primary_attack': root, 'configuration_hash': configuration_hash(state),
            'weapons': [weapon_input(engine, state, i) for i in (12, 13)],
            'skills': skills,
            'raw_wps_weight_sum': sum(x['fields'].get('skillChanceWeight', 0) for x in skills.values()),
            'stats': {k: v[k] for k in ('OA', 'DA', 'health', 'armor', 'armor_absorption', 'cunning', 'spirit')},
            'recognized_global_fields': copy.deepcopy(v['stats']),
            'resistances': copy.deepcopy(v['resistances']),
            'unresolved': [
                'Melee dual-wield hand selection and charge carryover; no fixed every-third-attack assumption.',
                'WPS hand counts, animation rates and interaction with the discharge; weights are not full-cycle shares.',
                'Weapon-local versus shared flat damage, conversion and attack speed; do not sum both hands as global bonuses.',
                'Deadly Momentum duration is known; uptime and inclusion in existing global totals must be reconciled.',
                'Armor-piercing/conversion ordering and applicability to skill-native flat damage.',
                'DoT refresh, OA/crit and conditional devotion uptime remain outside certified scoring.'
            ]}


def relative_direct_index(candidate, baseline, *, verified=False):
    """Final comparison kernel, only for already-resolved direct-damage factors.

    Callers must resolve cycle/hand/uptime and damage routing first. This is not
    a Cadence scorer and cannot be used on the extracted raw database payloads.
    """
    if not verified:
        raise ValueError('Unverified Cadence mechanics: ranking is disabled')
    def strength(x):
        factors = (x['damage_per_action'], x['actions_per_second'], x['oa_rr_factor'])
        if any(not isinstance(a, (int, float)) or not 0 < a < float('inf') for a in factors):
            raise ValueError('Resolved direct-damage factors must be finite and positive')
        return factors[0] * factors[1] * factors[2]
    return 100 * strength(candidate) / strength(baseline)


def restore_shared_inputs():
    """Restore compact-checkpoint shared snapshots without extracting game archives."""
    from GrimDawn_Optimizer import ROOT
    data = ROOT / "characters/Beeztrap"
    for name in ("database.json.gz", "localization.json", "guide70.json", "guide83.json"):
        if not (data / name).exists():
            shutil.copy2(ROOT / name, data / name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=Path('Cadence_Input_Audit.json'))
    args = parser.parse_args()
    from beeztrap_equipment import BeeztrapEquipment
    restore_shared_inputs()
    engine = BeeztrapEquipment()
    audit = extract_inputs(engine)
    args.output.write_text(json.dumps(audit, indent=2) + '\n')
    print(audit['status'], args.output)

if __name__ == '__main__':
    main()
