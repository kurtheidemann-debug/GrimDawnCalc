"""Bounded Balanced production run over preserved v1.2 modules. No mechanics changes."""
import argparse,copy,hashlib,json,math,time
from pathlib import Path
from beeztrap_equipment import BeeztrapEquipment,DATA
from practical_optimizer import PracticalEngine
from GrimDawn_Optimizer import Engine,ROOT,SLOTS
from cadence_scenarios import SCENARIOS,compare_scores
from beeztrap_materiality import BeeztrapMateriality,apply_policy

class ProductionEngine(BeeztrapEquipment):
 def __init__(self):
  super().__init__();self.target_ultimate=False
  self.scorer=BeeztrapMateriality(self);self.scenario_baseline=self.scorer.snapshot(self.current)
  self.raw_baseline={s.name:self.scorer.strength(self.scenario_baseline,s) for s in SCENARIOS};self.memo={};self.comparisons={}
 def legal(self,s,v,full=False):
  errors=PracticalEngine.legal(self,s,v,full)
  for i,ident in enumerate(s['gear']):
   for f,a,t in [('strength','physique','Strength'),('dexterity','cunning','Dexterity'),('intelligence','spirit','Intelligence')]:
    msg=ident+' '+a+' requirement'
    if msg in errors and self.requirement_met(ident,i,v,f,a,t):errors.remove(msg)
  return errors
 def evaluate(self,s):
  key=self.signature(s)
  if key in self.memo:return self.memo[key]
  v=PracticalEngine.evaluate(self,s)
  x=self.scorer.snapshot(s);raw={q.name:self.scorer.strength(x,q) for q in SCENARIOS}
  comp=compare_scores(raw,self.raw_baseline);blockers=x['limits']+self.scenario_baseline['limits']
  if x['unsupported_signature']!=self.scenario_baseline['unsupported_signature']:blockers.append('DoT, crit, RR or conditional/proc mechanics changed outside the direct-offense envelope')
  comp.update(blockers=sorted(set(blockers)),candidate_defenses=x['defenses'],baseline_defenses=self.scenario_baseline['defenses'])
  if blockers:comp['classification']='UNSUPPORTED_DELTA_NO_CERTIFIED_RANK'
  sustain=all(v['stats'].get(k,0)>=self.anchor['stats'].get(k,0) for k in ['offensiveLifeLeechMin','characterLifeRegen','characterLifeRegenModifier'])
  comp=apply_policy(comp,self.cost(s),sustain_neutral=sustain)
  v['offense_index']=comp['minimum_index'];v['offense_max_index']=comp['maximum_index'];v['offense_supported']=not blockers
  self.comparisons[key]=comp;return v
 def defense_gap(self,v):
  return sum(max(0,r['cap']-r['raw']) for r in v['resistances'][:9])+max(0,1900-v['DA'])/10+max(0,self.anchor['health']-v['health'])/50+max(0,90-v['armor_absorption'])*2+max(0,.95*self.anchor['armor']-v['armor'])/20+max(0,self.anchor['resistances'][-1]['raw']-v['resistances'][-1]['raw'])*3
 def utility(self,s,v,quick=False):
  off=100 if quick else v['offense_index'];over=sum(min(20,max(0,r['overcap'])) for r in v['resistances'][:9])
  defensive=(v['health']/self.anchor['health'])**.3*(v['DA']/self.anchor['DA'])**.3*(max(1,v['armor'])/self.anchor['armor'])**.2*(max(1,v['armor_absorption'])/self.anchor['armor_absorption'])**.2
  # Existing cost points and defense calculator; offense uses the worst scenario.
  return .5*math.log(max(1,off)/100)+.5*math.log(defensive)-.0008*self.cost(s)['utility_cost']-.04*self.defense_gap(v)+.00008*over-(0 if quick or v.get('offense_supported') else .025)
 def quick(self,s):
  return self.calculate(s)
 def feasible_production(self,s,v):
  return not self.legal(s,v,True) and self.defense_gap(v)<1e-7 and self.equip_order_possible(s)

def fingerprint():
 h=hashlib.sha256()
 for p in [ROOT/'beeztrap_production.py',ROOT/'cadence_scenarios.py',ROOT/'beeztrap_materiality.py',ROOT/'practical_optimizer.py',ROOT/'GrimDawn_Optimizer.py',ROOT/'relative_offense.py',ROOT/'beeztrap_equipment.py',DATA/'catalog.json',DATA/'mal.json',DATA/'materials.json',DATA/'recipes.json',ROOT/'database.json.gz']:
  h.update(p.read_bytes())
 return h.hexdigest()

def run(e,seconds=100,width=5):
 start=time.monotonic();deadline=start+seconds;seeds=[copy.deepcopy(e.current)]
 old=DATA/'results/results.json'
 if old.exists():
  for row in json.loads(old.read_text()).get('chosen',{}).values():
   if row['state'] not in seeds:seeds.append(copy.deepcopy(row['state']))
 # All owned/catalog gear participates in cheap stat shortlist, but retain only
 # two alternative items per slot before the complete-loadout scenario beam.
 options=Engine.options(e);swords=[id for id in options[12] if e.items[id]['records'][0].get('Class')=='WeaponMelee_Sword' and e.items[id]['records'][0].get('characterBaseAttackSpeedTag')=='Speed:  Very Fast']
 options[12]=swords;options[13]=swords
 anchor=seeds[-1];bundles=[];shortlisted=0
 for i in range(14):
  native=[]
  for ident in list(dict.fromkeys([anchor['gear'][i],e.current['gear'][i]]+options[i])):
   q=copy.deepcopy(anchor);q['gear'][i]=ident
   for k,sk in [('comp','relic-name'),('aug','augment-name')]:q[k][i]=e.items[ident]['save'].get(sk,'')
   if any(not e.compatible(q[k][i],i,ident) for k in ['comp','aug']):continue
   if e.resources(q)['errors']:continue
   v=e.quick(q);native.append((e.utility(q,v,True),ident))
  ids=list(dict.fromkeys([anchor['gear'][i],e.current['gear'][i]]+[x[1] for x in sorted(native,reverse=True)[:2]]))
  pool={}
  for ident in ids:
   q=copy.deepcopy(anchor);q['gear'][i]=ident
   for k,sk in [('comp','relic-name'),('aug','augment-name')]:q[k][i]=e.items[ident]['save'].get(sk,'')
   comps=list(dict.fromkeys([q['comp'][i],anchor['comp'][i],e.current['comp'][i]]+[p for p in e.components if e.component_cost(p)<=4 and e.compatible(p,i,ident)]))
   comp_rank=[]
   for c in comps:
    if not e.compatible(c,i,ident):continue
    t=copy.deepcopy(q);t['comp'][i]=c
    if e.resources(t)['errors']:continue
    comp_rank.append((e.utility(t,e.quick(t),True),c))
   for _,c in sorted(comp_rank,reverse=True)[:2]:
    for a in list(dict.fromkeys([q['aug'][i],anchor['aug'][i],e.current['aug'][i]]+[p for p in e.augments if e.compatible(p,i,ident)])):
     if not e.compatible(a,i,ident):continue
     t=copy.deepcopy(q);t['comp'][i]=c;t['aug'][i]=a
     if e.resources(t)['errors']:continue
     pool[(ident,c,a)]=e.utility(t,e.quick(t),True)
  ranked=sorted(pool,key=pool.get,reverse=True)[:4]
  for seed in seeds:
   bundle=tuple(seed[k][i] for k in ['gear','comp','aug'])
   if bundle not in ranked:ranked.append(bundle)
  bundles.append(ranked);shortlisted+=len(ranked)
  if time.monotonic()>deadline:break
 beam=seeds;finalists={};logs=[]
 def retain(s):
  v=e.evaluate(s)
  if e.feasible_production(s,v):finalists[e.signature(s)]={'state':copy.deepcopy(s),'stats':v,'cost':e.cost(s),'resources':e.resources(s)}
 for s in seeds:retain(s)
 for i,pool in enumerate(bundles):
  trials={}
  for seed in beam:
   for bundle in pool:
    s=copy.deepcopy(seed)
    for k,value in zip(['gear','comp','aug'],bundle):s[k][i]=value
    if len(set(s['gear']))!=14 or e.resources(s)['errors']:continue
    v=e.evaluate(s)
    if any('requirement' not in msg for msg in e.legal(s,v)):continue
    trials[e.signature(s)]=(e.utility(s,v),s)
    if time.monotonic()>deadline:break
   if time.monotonic()>deadline:break
  if trials:beam=[s for _,s in sorted(trials.values(),key=lambda x:x[0],reverse=True)[:width]]
  for s in beam:retain(s)
  logs.append({'slot':SLOTS[i],'evaluations':len(e.comparisons),'feasible':len(finalists)});print(logs[-1],flush=True)
  if time.monotonic()>deadline:break
 if not finalists:raise RuntimeError('No validated defensive candidate; no recommendation generated')
 choices=list(finalists.values());best=max(choices,key=lambda x:e.utility(x['state'],x['stats']))
 # Preserve 3% offensive materiality: prefer cheaper, comparably defensive
 # complete candidates within 3% of the fixed winner; never chain drift.
 near=[x for x in choices if x['stats']['offense_index']>=.97*best['stats']['offense_index'] and x['stats']['health']>=.95*best['stats']['health'] and x['stats']['DA']>=.95*best['stats']['DA'] and x['stats']['armor']>=.95*best['stats']['armor'] and x['cost']['utility_cost']<=best['cost']['utility_cost']]
 if near:best=min(near,key=lambda x:x['cost']['utility_cost'])
 final=e.scorer.compare(best['state']) # independent standalone recomputation
 assert abs(final['minimum_index']-best['stats']['offense_index'])<1e-8
 best['standalone_comparison']=final;best['ultimate_resistances']=e.ultimate_rows(best['stats'])
 return {'selected':best,'baseline':e.calculate(e.current),'baseline_state':e.current,'logs':logs,'seconds':time.monotonic()-start,'shortlisted_bundles':shortlisted,'feasible_candidates':len(finalists),'validation':{'legal_errors':e.legal(best['state'],best['stats'],True),'equip_order':e.equip_order_possible(best['state']),'defense_gap':e.defense_gap(best['stats']),'fixed_build':all(best['state'][k]==e.current[k] for k in ['skills','devotions','bindings']),'attributes_preserved':best['state']['attributes']==[0,0,0]},'scope':'One bounded Balanced beam; no global optimum claim; uncertainty blockers retained'}

def report(e,r,path):
 sel=r['selected'];s=sel['state'];v=sel['stats'];b=r['baseline'];c=sel['standalone_comparison'];lines=['# Beeztrap — Balanced production recommendation','','Level 74, saved Elite; fixed dual-wield Cadence, skills, devotions and bindings. Four unspent attribute points preserved.','','## Outcome','',f"Relative direct offense: **{c['minimum_index']:.3f}–{c['maximum_index']:.3f}** (current =100). Classification: `{c['classification']}`. Beeztrap materiality is 3% across all 32 scenarios; these are not total-DPS estimates.",'',f"Unsupported-mechanics warnings: {c['blockers'] or 'None detected for this comparison; existing scenario limitations still apply.'}",'',f"Health **{v['health']}** (current {b['health']}); OA **{v['OA']}**; DA **{v['DA']}**; armor **{v['armor']}**; absorption **{v['armor_absorption']:.1f}%**; physical resistance **{v['resistances'][-1]['raw']:.1f}%**.",'','## Exact equipment and attachments','','|Slot|ID / item|Source owner / location|Component|Augment|Required change|','|---|---|---|---|---|---|']
 for i,id in enumerate(s['gear']):
  it=e.items[id];changes=[]
  if id!=e.current['gear'][i]:changes.append('Equip item')
  for k,label in [('comp','component'),('aug','augment')]:
   if s[k][i]!=e.current[k][i]:changes.append('Replace '+label)
  if id!=e.current['gear'][i]:
   for k,sk in [('comp','relic-name'),('aug','augment-name')]:
    if s[k][i]!=it['save'].get(sk,''):changes.append('Apply '+k+' to replacement')
  lines.append(f"|{SLOTS[i]}|{id}: {it['name']}|{it['owner']} `{it['location']}`|{e.name(s['comp'][i]) or 'None'} `{s['comp'][i]}`|{e.name(s['aug'][i]) or 'None'} `{s['aug'][i]}`|{', '.join(changes) or 'Keep'}|")
 lines+=['','## Resistances','','Effective before cap / displayed / overcap (negative means shortfall). Ultimate is a projection, not the selected difficulty.','','|Resistance|Elite before cap|Elite displayed|Elite over/short|Ultimate before cap|Ultimate displayed|Ultimate over/short|','|---|---:|---:|---:|---:|---:|---:|']
 for a,u in zip(v['resistances'][:9],sel['ultimate_resistances'][:9]):lines.append(f"|{a['name']}|{a['raw']:.1f}|{min(a['cap'],a['raw']):.1f}|{a['overcap']:+.1f}|{u['raw']:.1f}|{min(u['cap'],u['raw']):.1f}|{u['overcap']:+.1f}|")
 res=sel['resources'];lines+=['','## Resources and faction eligibility','',f"Existing cost utility: {sel['cost']}. Utility is a preference penalty, not currency.",f"Base crafting iron: {res['craft_iron_base']}; augment iron: {res['augment_iron_base']}; current iron: {e.mal['iron']}; remaining base estimate: {res['remaining_iron_base']}. Vendor pricing may vary; no purchases performed.",'','Components required:']
 for p,n in res['component_need'].items():lines.append(f"- {e.name(p)} ×{n}; owned {e.available[p]}; crafted batches {res['crafted_batches'].get(p,0)}; `{p}`")
 lines+=['','Selected augment access:']
 for p in sorted(set(s['aug'])-{''}):
  rec=e.db[p];faction=next((x for x in e.factions if x['key']==rec.get('factionSource')),None);eligible=[x for x in e.vendor.get(p,[]) if e.rep.get(rec.get('factionSource'),-1)>=x['required']]
  lines.append(f"- {e.name(p)} (`{p}`): level {rec.get('levelRequirement',0)}, {faction['name'] if faction else rec.get('factionSource')}, reputation {faction['reputation'] if faction else 'unknown'}; eligible tier(s) {', '.join(sorted({x['tier'] for x in eligible}))}; new purchases {res['augment_purchases'].get(p,0)}.")
 lines+=['','## Validation and rerun','',json.dumps(r['validation'],indent=2),'',f"Resource errors: {res['errors']}. Search evaluated {len(e.comparisons)} complete-loadout scenarios sets; {r['feasible_candidates']} feasible candidates retained in {r['seconds']:.1f} seconds. Final standalone recomputation matched the search indices.",'','Saved build/hotbar data are unchanged. No attribute respec or spending. Existing Mal code/results and prior Beeztrap recommendations are retained. Gear is restricted to catalog-owned items and verified Very Fast sword classes; replacement requirements, component stock/crafting, eligible faction augments and equipment order are checked. Baseline stats reproduce the imported decoder export, not a new live-game measurement.','', 'A flagged offense comparison is diagnostic: this recommendation repairs defenses without claiming a robust overall offensive gain. Useful resistance overcap is valued only up to +20; incidental excess is not penalized. Ultimate shortfalls above remain preparation priorities.','', 'Run `python beeztrap_production.py`; unchanged reruns use the cached result. Use `--force --seconds 75 --width 4` for another bounded run.']
 path.write_text('\n'.join(lines)+'\n')

def main():
 from cadence_inputs import restore_shared_inputs
 restore_shared_inputs();ap=argparse.ArgumentParser();ap.add_argument('--seconds',type=int,default=75);ap.add_argument('--width',type=int,default=4);ap.add_argument('--force',action='store_true');a=ap.parse_args()
 dest=ROOT/'production-results';dest.mkdir(exist_ok=True);target=dest/'Beeztrap_Balanced.json';key=fingerprint()+str((a.seconds,a.width))
 if target.exists() and not a.force and json.loads(target.read_text()).get('input_hash')==key:print('Cached production result:',target);return
 e=ProductionEngine();r=run(e,a.seconds,a.width);r['input_hash']=key;target.write_text(json.dumps(r,indent=2)+'\n');report(e,r,dest/'Beeztrap_Balanced.md');print('Validated production result:',target,flush=True)
if __name__=='__main__':main()
