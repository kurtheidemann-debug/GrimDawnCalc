"""Bounded direct-offense comparisons for fixed dual-wield Cadence (not DPS).
Standalone: never installed into search. Unsupported deltas prevent robust claims.
"""
from dataclasses import dataclass, asdict
from itertools import product
from collections import Counter
import argparse, copy, json, math
from pathlib import Path
from GrimDawn_Optimizer import at, family
from relative_offense import payload_of, conversions, convert_payload, TYPES
from cadence_inputs import extract_inputs, restore_shared_inputs

CADENCE='records/skills/playerclass01/cadence1.dbr'
MOMENTUM='records/skills/playerclass01/cadence3.dbr'

@dataclass(frozen=True)
class Scenario:
    discharge: float
    main_weight: float
    wps_credit: float
    speed: str
    momentum_uptime: float
    @property
    def name(self):
        return f'c{self.discharge:g}-h{self.main_weight:g}-w{self.wps_credit:g}-{self.speed}-dm{self.momentum_uptime:g}'

SCENARIOS=tuple(Scenario(*x) for x in product((1/3, .5), (.5, 1.), (.5, 1.), ('mean','slow'), (.5,1.)))



def selected_records(engine, state, slot):
    """Catalog records include SAVED attachments: rebuild only live sources once."""
    return engine.item_records(state['gear'][slot],state['comp'][slot],state['aug'][slot])


def selected_modifiers(engine,state):
    out={}
    for slot,ident in enumerate(state['gear']):
        for r in selected_records(engine,state,slot):
            for i in range(1,6):
                target=r.get('modifiedSkillName'+str(i));path=r.get('modifierSkillName'+str(i))
                if target and path:
                    out.setdefault(target,[]).append({'modifier_record':path,'item_id':ident,'slot':slot})
    return out

def direct(record, rank=1):
    return {k:v for k,v in payload_of(record,rank).items() if k in TYPES}


def route(payload, local, global_conversion, piercing):
    # Existing convert_payload freezes converted output. Adding piercing as the
    # final allocation of residual Physical avoids converting that output twice.
    # Carry frozen local conversions independently rather than re-convert them.
    # Delegate all stages at once, with piercing added to residual global stage
    # by explicitly separating native Physical not consumed by global conversion.
    out=convert_payload(payload,local,global_conversion)
    # Determine unconverted native Physical using the same normalized allocations.
    remaining=payload.get('Physical',0.)
    for stage in (local,global_conversion):
        remaining*=max(0,1-min(100,sum(p for a,b,p in stage if a=='Physical'))/100)
    amount=remaining*max(0,min(100,piercing))/100
    out['Physical']=out.get('Physical',0)-amount
    out['Pierce']=out.get('Pierce',0)+amount
    return {k:max(0,v) for k,v in out.items() if v>1e-12}


def speed_factor(adjustments, percent, mode):
    # Dimensionless sword-speed proxy, not attacks/sec. Conventional 200%
    # ceiling is an assumption. Slow-hand case deliberately discounts mixed speed.
    hands=[max(.1,1+x) for x in adjustments]
    base=sum(hands)/2 if mode=='mean' else min(hands)
    return base*max(.1,min(2.,1+percent/100))


def compare_scores(candidate, baseline):
    if set(candidate)!=set(baseline) or set(candidate)!={s.name for s in SCENARIOS}:
        raise ValueError('All configured scenarios must be present in both scores')
    if any(not math.isfinite(v) or v<=0 for v in list(candidate.values())+list(baseline.values())):
        raise ValueError('Scenario strengths must be finite and positive')
    indices={k:100*candidate[k]/baseline[k] for k in baseline}
    if any(not math.isfinite(v) or v<=0 for v in indices.values()):
        raise ValueError('Nonpositive or nonfinite scenario score')
    low,high=min(indices.values()),max(indices.values())
    return {'scenario_indices':indices,'minimum_index':low,'maximum_index':high,
            'robust_improvement':low>105.+1e-9,
            'classification':'ROBUST_DIRECT_OFFENSE_IMPROVEMENT' if low>105.+1e-9 else 'NO_ROBUST_IMPROVEMENT'}


class CadenceScorer:
    def __init__(self, engine):
        self.e=engine
        self.reference=copy.deepcopy(engine.current)
        self.saved=copy.deepcopy(engine.mal)

    def equipment_sources(self,state):
        """Same normalized rolls/attachments as v1.2, with ownership retained."""
        shared=[];local=[[],[]];global_records=[];limitations=[]
        for slot,ident in enumerate(state['gear']):
            item=self.e.items[ident];base=self.e.db.get(item['save'].get('basename'),{})
            vals=copy.deepcopy(item.get('worn-rolled') or item.get('rolled') or {})
            completion=item.get('completion') or {}
            attachments=[self.e.db.get(state[k][slot],{}) for k in ('comp','aug')]
            sources=[vals,completion]+[self.e.numeric(r) for r in attachments]
            (local[slot-12] if slot in (12,13) else shared).extend(sources)
            records=selected_records(self.e,state,slot)
            # Roll replacements belong to an item, not the entire gear total.
            for r in records:
                q=copy.deepcopy(r)
                for suffix in ('','2','3','4','5','6'):
                    field='conversionPercentage'+suffix
                    if q.get('conversionInType'+suffix) and field in vals:
                        count=sum(bool(x.get('conversionInType'+suffix)) for x in records)
                        if count!=1:limitations.append('Ambiguous seeded conversion mapping on '+ident)
                        else:q[field]=vals[field]
                global_records.append((q,1))
            for r in [base]+attachments:
                sr=self.e.db.get(r.get('itemSkillName'),{})
                if sr.get('Class') in ['Skill_Passive','Skill_BuffSelfToggled','Skill_BuffAttackRadiusToggled','Skill_BuffRadiusToggled']:
                    shared.append(self.e.numeric(sr,r.get('itemSkillLevel',1)))
                    global_records.append((sr,r.get('itemSkillLevel',1)))
        return shared,local,global_records,limitations

    def snapshot(self,state):
        e=self.e
        for key in ('skills','devotions','bindings'):
            if state[key]!=self.reference[key]:raise ValueError('Fixed saved '+key+' changed')
        if state.get('respec_attributes'):raise ValueError('Attribute respec unsupported')
        v=e.calculate(state);audit=extract_inputs(e,state,v)
        if audit['primary_attack']!=CADENCE:raise ValueError('This bounded adapter supports saved Cadence only')
        if not all(w['class']=='WeaponMelee_Sword' for w in audit['weapons']):
            raise ValueError('Mixed weapon classes have no supported speed envelope')
        shared,local,global_records,limits=self.equipment_sources(state)
        for weapon in audit['weapons']:
            if weapon['speed_tag']!='Speed:  Very Fast':
                limits.append('Unverified base-speed tag outside the two current Very Fast swords')
        eff=v['effective_skills'];active={s['skill-name'] for s in e.mal['skills'] if s.get('skill-active')}
        active|={p for p in state['skills'] if e.db[p].get('Class') in ['Skill_BuffSelfToggled','Skill_BuffRadiusToggled']}
        running=set().union(*(family(p,e.db.get(p,{})) for p in active))
        stats=Counter(v['stats']);removed=Counter();sets={}
        for ident in state['gear']:
            item=e.items[ident];r=item['records'][0] or {}
            if r.get('itemSetName'):sets.setdefault(r['itemSetName'],set()).add(item['save']['basename'])
        for p,bases in sets.items():
            shared.append(e.numeric(e.db[p],len(bases)));global_records.append((e.db[p],len(bases)))
        for p,l in state['skills'].items():
            r=e.db[p];rank=eff.get(p,l);cl=r.get('Class');contrib=[]
            if cl in ['Skill_Mastery','Skill_Passive']:contrib.append(e.numeric(r,l if cl=='Skill_Mastery' else rank))
            if cl=='Skill_Modifier' and family(p,r)&running:contrib.append(e.numeric(r,rank,True))
            if p in active:
                contrib.append(e.numeric(r,rank));br=e.db.get(r.get('buffSkillName'),{})
                if 'Debuf' not in br.get('Class',''):contrib.append(e.numeric(br,rank))
            # Remove conditional Momentum and Cadence-native modifiers if the
            # legacy calculator happened to include them as active/global.
            conditional=p==MOMENTUM or (cl=='Skill_Modifier' and family(p,r)&family(CADENCE,e.db[CADENCE]))
            if conditional:
                for q in contrib:removed.update(q)
            else:
                shared+=contrib
                if contrib:
                    global_records.append((r,rank))
                    if p in active:global_records.append((e.db.get(r.get('buffSkillName'),{}),rank))
        for p,l in state['devotions'].items():
            if e.db[p].get('Class')=='Skill_Passive':
                shared.append(e.numeric(e.db[p],1));global_records.append((e.db[p],1))
        stats.subtract(removed)
        # Existing totals count chance-based percentage bonuses at full strength.
        # Expected bonus is linear; fixed source chances are not proc uptime.
        chance_adjustment=Counter()
        for q,l in global_records:
            for key,chance in q.items():
                if key.endswith('ModifierChance'):
                    field=key[:-6]
                    chance_adjustment[field]+=at(q.get(field),l)*(1-max(0,min(100,at(chance,l)))/100)
        stats.subtract(chance_adjustment)
        # Global flat is reconstructed source-by-source; it is NOT lifted out
        # of aggregated totals that contain BOTH weapons' local flat damage.
        flat=Counter()
        for q in shared:flat.update(direct(q))
        hands=[]
        for h,w in enumerate(audit['weapons']):
            flat_local=Counter()
            for q in local[h]:flat_local.update(direct(q))
            # Intrinsic Physical base is absent from normal normalized rolls.
            # If supplied in rolls it is already included in local[h].
            rolled=w['rolled_item_fields']
            if 'offensivePhysicalMin' not in rolled and 'offensivePhysicalMax' not in rolled:
                flat_local['Physical']+=w['intrinsic_physical_mean']
            hands.append({'flat':dict(flat_local),'piercing':min(100,w['armor_piercing_percent']*(1+stats.get('offensivePierceRatioModifier',0)/100)),
                          'speed_adjustment':w['base_speed_adjustment']})
        dm_rank=eff.get(MOMENTUM,0);dm_root=e.db.get(MOMENTUM,{})
        dm=e.db.get(dm_root.get('buffSkillName'),{}) if dm_rank else {}
        mods=selected_modifiers(e,state);skills=[]
        for p,entry in audit['skills'].items():
            if p==MOMENTUM:continue
            r=e.db[p];rank=entry['effective_rank']
            if p==CADENCE or r.get('skillChanceWeight'):
                records=[(r,rank)]
                if p==CADENCE:
                    records += [(e.db[q],eff[q]) for q in state['skills'] if e.db[q].get('Class')=='Skill_Modifier' and family(q,e.db[q])&family(CADENCE,r)]
                records += [(e.db.get(m['modifier_record'],{}),1) for m in mods.get(p,[])]
                skills.append({'path':p,'records':records,'weight':at(r.get('skillChanceWeight'),rank)})
        snap={'stats':dict(stats),'flat':dict(flat),'hands':hands,'skills':skills,
              'conversions':conversions(global_records),'dm':e.numeric(dm,dm_rank),
              'OA':v['OA'],'cunning':v['cunning'],'spirit':v['spirit'],
              'removed_from_totals':dict(removed),'chance_adjustment':dict(chance_adjustment),'limits':limits,
              'defenses':{k:v[k] for k in ('health','DA','armor','armor_absorption','resistances')},
              'audit':audit}
        # Changes outside the direct envelope cannot be certified by this model.
        # Preserve exact signatures rather than inventing uptime, DoT or RR.
        semantic=[]
        for q,l in global_records + [(e.db[p],eff.get(p,l)) for p,l in state['skills'].items()] + [(e.db[p],max(1,l)) for p,l in state['devotions'].items()]:
            semantic.append({k:(at(x,l) if isinstance(x,(int,float,list)) else x) for k,x in q.items()
                             if ('ResistanceReduction' in k or k.startswith('offensiveSlow') or k.startswith('defensive') and at(x,l)<0 or k in ('itemSkillName','itemSkillLevel','offensiveCritDamageModifier','offensivePercentCurrentLifeMin','skillChance'))})
        for skill in skills:
            for q,l in skill['records'][1:]:
                semantic.append({k:at(v,l) for k,v in q.items() if k.startswith('offensiveSlow') or 'ResistanceReduction' in k or k in ('offensiveCritDamageModifier','offensivePercentCurrentLifeMin','skillCooldownTime','skillChanceWeight')})
        # Include attachment/item flat DoT and conditional damage rolls too.
        for ident,c,a in zip(state['gear'],state['comp'],state['aug']):
            vals=e.item_parts(ident,c,a)[0]
            semantic.append({k:x for k,x in vals.items() if k.startswith('offensiveSlow') or k.endswith('ModifierChance') or k=='offensiveCritDamageModifier'})
        snap['unsupported_signature']=sorted(json.dumps(x,sort_keys=True) for x in semantic if x)
        if e.mal!=self.saved:raise AssertionError('Saved configuration was mutated')
        return snap

    def strength(self,x,scenario,dm_on=None):
        if dm_on is None:
            u=scenario.momentum_uptime
            return (1-u)*self.strength(x,scenario,0)+u*self.strength(x,scenario,1)
        dm=x['dm'];up=dm_on
        stats=Counter(x['stats']);stats.update({k:v*up for k,v in dm.items()})
        shared=Counter(x['flat']);shared.update({k:v*up for k,v in direct(dm).items()})
        conv=x['conversions'];wp=[s for s in x['skills'] if s['weight']>0]
        total=sum(s['weight'] for s in wp);den=max(100,total)
        # One strength call has fixed snapshot and Momentum state. Ordinary
        # hands are requested twice; reuse their exact scalar packets locally.
        packet_values={}
        def packet(hand,skill=None):
            key=(hand,skill['path'] if skill else None)
            if key in packet_values:return packet_values[key]
            records=skill['records'] if skill else []
            wdp=at(records[0][0].get('weaponDamagePct',100),records[0][1]) if records else 100
            wdp+=sum(at(r.get('weaponDamagePct'),l) for r,l in records[1:])
            payload=Counter(x['hands'][hand]['flat']);payload.update(shared)
            payload={k:v*wdp/100 for k,v in payload.items()}
            for r,l in records:
                for k,v in direct(r,l).items():payload[k]=payload.get(k,0)+v
            local_pct={typ:sum(at(r.get('offensive'+typ+'Modifier'),l)+at(r.get('offensiveTotalDamageModifier'),l)+(at(r.get('offensiveElementalModifier'),l) if typ in ('Fire','Cold','Lightning') else 0) for r,l in records) for typ in payload}
            routed=route(payload,conversions(records),conv,x['hands'][hand]['piercing'])
            bonus=route({typ:flat*local_pct[typ]/100 for typ,flat in payload.items()},conversions(records),conv,x['hands'][hand]['piercing'])
            value=0
            for typ,flat in routed.items():
                pct=stats.get('offensive'+typ+'Modifier',0)+stats.get('offensiveTotalDamageModifier',0)
                if typ in ('Fire','Cold','Lightning'):pct+=stats.get('offensiveElementalModifier',0)
                pct+=x['cunning']*.41 if typ in ('Physical','Pierce') else x['spirit']*100/215
                value+=flat*max(.01,1+pct/100)+bonus.get(typ,0)
            packet_values[key]=value
            return value
        def ordinary(hand):
            plain=packet(hand)
            wps=sum(s['weight']/den*packet(hand,s) for s in wp)+max(0,1-total/den)*plain
            return plain+scenario.wps_credit*(wps-plain)
        cadence=next(s for s in x['skills'] if s['path']==CADENCE)
        cw=scenario.main_weight
        # Main-heavy and symmetric attribution span unresolved discharge hand.
        charged=cw*packet(0,cadence)+(1-cw)*packet(1,cadence)
        # Accompanying hand receives a discounted ordinary/WPS payload, never
        # Cadence multiplication. This is an assumption, not animation logic.
        accompanying=.5*scenario.wps_credit*(cw*ordinary(1)+(1-cw)*ordinary(0))
        regular=.75*(ordinary(0)+ordinary(1))
        per_action=(1-scenario.discharge)*regular+scenario.discharge*(charged+accompanying)
        return per_action*speed_factor([h['speed_adjustment'] for h in x['hands']],stats.get('characterAttackSpeedModifier',0),scenario.speed)*max(.1,x['OA']/2000)

    def compare(self,candidate,baseline=None):
        base=self.snapshot(self.reference if baseline is None else baseline);new=self.snapshot(candidate)
        b={s.name:self.strength(base,s) for s in SCENARIOS};c={s.name:self.strength(new,s) for s in SCENARIOS}
        result=compare_scores(c,b)
        blockers=base['limits']+new['limits']
        if new['unsupported_signature']!=base['unsupported_signature']:
            blockers.append('DoT, crit, RR or conditional/proc mechanics changed outside the direct-offense envelope')
        if blockers:
            result['robust_improvement']=False;result['classification']='UNSUPPORTED_DELTA_NO_CERTIFIED_RANK'
        result.update({'scope':'SCENARIO_RELATIVE_DIRECT_OFFENSE_NOT_TOTAL_DPS','blockers':sorted(set(blockers)),
                       'baseline_defenses':base['defenses'],'candidate_defenses':new['defenses'],
                       'momentum_removed_from_existing_totals':new['removed_from_totals'],
                       'chance_bonus_discount':new['chance_adjustment'],
                       'scenarios':[asdict(s)|{'name':s.name} for s in SCENARIOS],
                       'search_integration':'DISABLED; standalone comparison only'})
        return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--candidate',type=Path);ap.add_argument('--output',type=Path,default=Path('Cadence_Scenario_Baseline.json'));a=ap.parse_args()
    from beeztrap_equipment import BeeztrapEquipment
    restore_shared_inputs();e=BeeztrapEquipment();scorer=CadenceScorer(e)
    state=json.loads(a.candidate.read_text()) if a.candidate else e.current
    a.output.write_text(json.dumps(scorer.compare(state),indent=2)+'\n')
    print('Saved standalone comparison:',a.output)
if __name__=='__main__':main()
