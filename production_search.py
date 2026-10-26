"""Bounded complete-loadout search over unchanged v1.2 calculators and policies."""
import copy,json,math,time,itertools
from pathlib import Path
from GrimDawn_Optimizer import Engine,ROOT,SLOTS
from practical_optimizer import PracticalEngine
from production_data import physical_key
from beeztrap_production import ProductionEngine
from beeztrap_equipment import BeeztrapEquipment
from beeztrap_materiality import BeeztrapMateriality
from cadence_scenarios import SCENARIOS,compare_scores
from combat_configuration import cadence_weapon_reason,filter_options,detect_configuration,configuration_for_classes

class Deadline(Exception):pass

class MalEngine(PracticalEngine):
    def __init__(self,directory):
        super().__init__(directory);self.target_ultimate=(int(self.mal['last-difficulty'])&3)==2
        self.combat_configuration=detect_configuration(self.mal,self.db)
    def options(self):
        return filter_options(self,Engine.options(self),self.combat_configuration)
    def legal(self,s,v,full=False):
        errors=super().legal(s,v,full)
        try:
            actual=configuration_for_classes(*(self.items[i]['records'][0].get('Class','') for i in s['gear'][12:]))
            if actual!=self.combat_configuration:errors.append('Equipment does not match combat configuration '+self.combat_configuration)
        except ValueError as ex:errors.append(str(ex))
        return errors
    def deficits(self,v):
        # Scoped accepted baseline cap is a conservative review floor, not a new mechanic.
        return super().deficits(v)+max(0,getattr(self,'minimum_chaos_raw',0)-v['resistances'][8]['raw'])

class CadenceEngine(ProductionEngine):
    """Production Cadence adapter with bounded supported-sword pair transitions."""
    def __init__(self,directory):
        BeeztrapEquipment.__init__(self,directory);self.target_ultimate=(int(self.mal['last-difficulty'])&3)==2
        self.scorer=BeeztrapMateriality(self);self.scenario_baseline=self.scorer.snapshot(self.current)
        self.raw_baseline={s.name:self.scorer.strength(self.scenario_baseline,s) for s in SCENARIOS}
        self.memo={};self.comparisons={}
    def options(self):
        opts=Engine.options(self)
        opts=filter_options(self,opts,getattr(self,'combat_configuration','dual_wield_melee'))
        swords=[ident for ident in opts[12] if self.supported_weapon(ident)]
        opts[12]=swords;opts[13]=swords[:]
        return opts
    def supported_weapon(self,ident):
        return cadence_weapon_reason(self.items[ident]) is None
    def legal(self,s,v,full=False):
        errors=super().legal(s,v,full)
        if not all(self.supported_weapon(i) for i in s['gear'][12:]):
            errors.append('Unsupported Cadence pair: requires two one-handed swords/axes/maces with valid numeric base-speed adjustments')
        return errors


def seed_states(e,directory):
    states=[copy.deepcopy(e.current)];lookup={}
    for it in e.cat:lookup.setdefault(physical_key(it),[]).append(it)
    p=Path(directory)/'seeds.json'
    if p.exists():
        for entry in json.loads(p.read_text()):
            s=copy.deepcopy(e.current);used=set();valid=True
            for i,saved in enumerate(entry['items']):
                matches=[x for x in lookup.get(physical_key(saved),[]) if x['id'] not in used]
                if not matches:valid=False;break
                ident=matches[0]['id'];used.add(ident);s['gear'][i]=ident
                s['comp'][i]=entry['comp'][i];s['aug'][i]=entry['aug'][i]
            if valid:states.append(s)
    return states


def export_seeds(e,states):
    return [{'items':[e.items[i]['save'] for i in s['gear']],'comp':s['comp'],'aug':s['aug']} for s in states]


def bounded_search(e,deadline,width=5,rounds=1,full=False):
    beez=e.character_name=='Beeztrap';start=time.monotonic();finalists={};logs=[];evaluated=0;timed_out=False;weapon_pairs=set()
    options=e.options();seeds=seed_states(e,e.d);beam=seeds[:]
    joint_weapons=beez and (options[12]!=[e.current['gear'][12]] or options[13]!=[e.current['gear'][13]])
    def check():
        if time.monotonic()>=deadline:raise Deadline()
    def utility(s,v):return e.utility(s,v) if beez else e.score(s,v,'balanced')
    def feasible(s,v):return e.feasible_production(s,v) if beez else e.feasible(s,v)
    def retain(s,v=None):
        nonlocal evaluated
        v=e.evaluate(s) if v is None else v;evaluated+=1
        if beez and len(set(s['gear'][12:]))==2:weapon_pairs.add(tuple(s['gear'][12:]))
        if feasible(s,v):
            key=e.signature(s)
            finalists[key]={'state':copy.deepcopy(s),'stats':v,'cost':e.cost(s),'resources':e.resources(s)}
        return v
    def rank(s,v):return (utility(s,v),e.signature(s))
    # Validate useful seeds first, before any shortlist or beam can consume budget.
    for s in seeds:
        if beez:q=s
        else:q=e.repair_attributes(s)
        if q is not None:retain(q)
    # Bias attachment search toward a previously feasible complete seed.
    anchor=max((x['state'] for x in finalists.values()),key=lambda s:rank(s,e.evaluate(s)),default=seeds[0])
    bundles=[]
    try:
        for i in range(14):
            check();native=[]
            for ident in sorted(set(options[i]+[s['gear'][i] for s in seeds])):
                check();q=copy.deepcopy(anchor);q['gear'][i]=ident
                for k,sk in [('comp','relic-name'),('aug','augment-name')]:q[k][i]=e.items[ident]['save'].get(sk,'') or ''
                if any(not e.compatible(q[k][i],i,ident) for k in ['comp','aug']):continue
                if e.resources(q)['errors']:continue
                v=e.evaluate(q);native.append((rank(q,v),ident));retain(q,v)
            ids=[x[1] for x in sorted(native,reverse=True)[:(5 if full else 3)]]
            ids=list(dict.fromkeys(ids+[s['gear'][i] for s in seeds]));pool={}
            for ident in ids:
                check();q=copy.deepcopy(anchor);q['gear'][i]=ident
                for k,sk in [('comp','relic-name'),('aug','augment-name')]:q[k][i]=e.items[ident]['save'].get(sk,'') or ''
                comps=sorted(set([q['comp'][i],anchor['comp'][i],'']+[p for p in e.components if e.compatible(p,i,ident)]));cr=[]
                for c in comps:
                    check()
                    if not e.compatible(c,i,ident):continue
                    t=copy.deepcopy(q);t['comp'][i]=c
                    if e.resources(t)['errors']:continue
                    v=e.evaluate(t);cr.append((rank(t,v),c));retain(t,v)
                for _,c in sorted(cr,reverse=True)[:(3 if full else 2)]:
                    for a in sorted(set([q['aug'][i],anchor['aug'][i],'']+[p for p in e.augments if e.compatible(p,i,ident)])):
                        check()
                        if not e.compatible(a,i,ident):continue
                        t=copy.deepcopy(q);t['comp'][i]=c;t['aug'][i]=a
                        if e.resources(t)['errors']:continue
                        v=e.evaluate(t);pool[(ident,c,a)]=rank(t,v);retain(t,v)
            ranked=sorted(pool,key=lambda b:(pool[b],b),reverse=True)[:(10 if full else 6)]
            for s in seeds:
                b=tuple(s[k][i] for k in ['gear','comp','aug'])
                if b not in ranked:ranked.append(b)
            bundles.append(ranked)
            # Weapon slots form one transition: swaps must not require using
            # one physical sword twice in an intermediate state.
            if joint_weapons and i==12:
                logs.append({'slot':SLOTS[i],'evaluations':evaluated,'feasible':len(finalists)})
                continue
            # Grow a complete-loadout beam immediately; never wait for all slots.
            trials={}
            for s in beam:
                choices=itertools.product(bundles[12],ranked) if joint_weapons and i==13 else ((b,) for b in ranked)
                for combined in choices:
                    check();q=copy.deepcopy(s)
                    for slot,bundle in zip([12,13] if joint_weapons and i==13 else [i],combined):
                        for k,z in zip(['gear','comp','aug'],bundle):q[k][slot]=z
                    if len(set(q['gear']))<14 or e.resources(q)['errors']:continue
                    v=e.evaluate(q)
                    if any('requirement' not in er for er in e.legal(q,v)):continue
                    trials[e.signature(q)]=(rank(q,v),q);retain(q,v)
            if trials:beam=[x[1] for x in sorted(trials.values(),key=lambda x:x[0],reverse=True)[:width]]
            for q in beam:
                check();s=q if beez else e.repair_attributes(q)
                if s is not None:retain(s)
            logs.append({'slot':SLOTS[i],'evaluations':evaluated,'feasible':len(finalists)})
        for rd in range(1,rounds):
            for i,pool in enumerate(bundles):
                if joint_weapons and i==13:continue
                trials={}
                for s in beam:
                    choices=itertools.product(pool,bundles[13]) if joint_weapons and i==12 else ((b,) for b in pool)
                    for combined in choices:
                        check();q=copy.deepcopy(s)
                        for slot,bundle in zip([12,13] if joint_weapons and i==12 else [i],combined):
                            for k,z in zip(['gear','comp','aug'],bundle):q[k][slot]=z
                        if len(set(q['gear']))<14 or e.resources(q)['errors']:continue
                        v=e.evaluate(q)
                        if any('requirement' not in er for er in e.legal(q,v)):continue
                        trials[e.signature(q)]=(rank(q,v),q);retain(q,v)
                if trials:beam=[x[1] for x in sorted(trials.values(),key=lambda x:x[0],reverse=True)[:width]]
        # Voluntary allocations are bounded; cost and unchanged gates decide value.
        for entry in list(sorted(finalists.values(),key=lambda x:rank(x['state'],x['stats']),reverse=True)[:3]):
            s=entry['state'];remaining=e.mal['attribute-points']-sum(s['attributes'])
            for j in [0,2]:
                if remaining<=0:continue
                check();q=copy.deepcopy(s);q['attributes'][j]+=remaining
                retain(q)
    except Deadline:timed_out=True
    coverage={'eligible_weapon_candidates':len(set(options[12]+options[13])),'weapon_pair_configurations_evaluated':len(weapon_pairs)} if beez else {}
    if not finalists:
        return {**coverage,'status':'no_feasible_loadout','timed_out':timed_out,'evaluations':evaluated,'logs':logs,'feasible_candidates':0,'selected':None}
    choices=list(finalists.values());best=max(choices,key=lambda x:rank(x['state'],x['stats']));reference=best
    if beez:
        near=[x for x in choices if x['stats']['offense_index']>=.97*best['stats']['offense_index'] and x['stats']['health']>=.95*best['stats']['health'] and x['stats']['DA']>=.95*best['stats']['DA'] and x['stats']['armor']>=.95*best['stats']['armor'] and x['cost']['utility_cost']<=best['cost']['utility_cost']]
    else:near=[x for x in choices if e.prefer(x,best)]
    if near:best=min(near+[best],key=lambda x:(x['cost']['utility_cost'],-utility(x['state'],x['stats']),e.signature(x['state'])))
    baseline=e.evaluate(e.current)
    repair_needed=not feasible(e.current,baseline)
    meaningful=(best['stats']['offense_index']>=100*(1+(0.03 if beez else 0.05)) or best['stats']['defense_index']>=100*(1+(0.03 if beez else 0.05)))
    if not beez and not repair_needed and not meaningful:
        best={'state':copy.deepcopy(e.current),'stats':baseline,'cost':e.cost(e.current),'resources':e.resources(e.current)}
    materiality_audit={'reference_offense':reference['stats']['offense_index'],'reference_defense':reference['stats']['defense_index'],'anchored_policy_applied':True,'defensive_repair_required':repair_needed,'meaningful_gain_or_repair':meaningful or repair_needed,'decision':'defensive repair' if repair_needed else 'material improvement' if meaningful else 'keep current; gains immaterial'}
    # Recompute the winner from calculators without the search memo.
    s=best['state'];v=e.calculate(s)
    if beez:
        comparison=e.scorer.compare(s)
        if abs(comparison['minimum_index']-best['stats']['offense_index'])>1e-7:raise ValueError('Cadence standalone recomputation mismatch')
        v['offense_index']=comparison['minimum_index'];v['offense_max_index']=comparison['maximum_index'];best['standalone_comparison']=comparison
        # Practical evaluate's defense utility is unchanged by the Cadence override.
        v['defense_index']=e.evaluate(s)['defense_index']
    else:
        from relative_offense import useful_overcap
        recomputed=e.model.index(v['offense_model'],e.base['offense_model'])
        if abs(recomputed-best['stats']['offense_index'])>1e-7:raise ValueError('Offense recomputation mismatch')
        v['offense_index']=recomputed;v['defense_index']=e.evaluate(s)['defense_index']
    if not feasible(s,v):raise ValueError('Final winner failed full legality, resources, defenses or equip order')
    best['stats']=v
    return {**coverage,'status':'best_found_within_limits','timed_out':timed_out,'evaluations':evaluated,'logs':logs,'feasible_candidates':len(finalists),'selected':best,'reference':{'stats':reference['stats'],'cost':reference['cost']},'seconds_search':time.monotonic()-start,'scope':'Bounded complete-loadout beam; no global optimum proof','materiality_percent':3 if beez else 5,'materiality_audit':materiality_audit}
