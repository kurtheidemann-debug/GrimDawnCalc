"""Practical equipment-only search over the preserved checkpoint engine. Stdlib only."""
import argparse,copy,hashlib,json,math,pathlib,time
from GrimDawn_Optimizer import Engine,ROOT,STORM,WIND,MAEL,SLOTS,SPHERE,RES,at
from relative_offense import RelativeOffense,difficulty_penalties,useful_overcap
from item_identity import full_name,fingerprint as item_fingerprint
VERSION='practical-1.2'
class PracticalEngine(Engine):
 def __init__(self,directory=ROOT):
  super().__init__(directory);self.equipment_only=True
  selected=int(self.mal.get('last-difficulty',0))&3;expected=difficulty_penalties(self.db,selected)
  if self.pen!=expected:raise ValueError('Extracted penalties disagree with game database and selected difficulty. Refresh snapshot.')
  self.model=RelativeOffense(self);self.memo={};self.costmemo={};self.base=self.calculate(self.current);self.eval_count=0
 def calculate(self,s):
  v=super().calculate(s)
  # Reuse the preserved attribute/passive/item calculator. Discard its legacy
  # encounter outputs; this search never ranks hits, ticks, ramps or encounters.
  v['offense_model']=self.model.summarize(s,v)
  for field,row in zip(RES,v['resistances']):
   row['difficulty_adjusted_before_cap']=row['raw'];row['difficulty_penalty']=self.pen[field];row['before_difficulty_penalty']=row['raw']-self.pen[field]
  for k in ['offense_proxy','offense_low','offense_high','defense_proxy','storm_packet','maelstrom_packet','ramp_totems_6sec','steady_totems','mirror_cooldown','mirror_duration','totem_wind_energy_upkeep_estimate','energy_margin_lower_bound']:v.pop(k,None)
  return v
 def evaluate(self,s):
  key=self.signature(s)
  if key in self.memo:return self.memo[key]
  v=self.calculate(s);b=self.base
  v['offense_index']=self.model.index(v['offense_model'],b['offense_model'])
  # Geometric utility of explicit defense stats. Useful overcaps stop at +20.
  over=useful_overcap(v['resistances'])
  pr=max(0,v['resistances'][-1]['raw'])
  v['defense_index']=100*((v['health']/b['health'])**.3*(v['DA']/b['DA'])**.3*(v['armor']/b['armor'])**.15*(v['armor_absorption']/b['armor_absorption'])**.15*((100+pr)/(100+max(0,b['resistances'][-1]['raw'])))**.1)*(1+.1*over)/(1+.1*sum(min(20,max(0,r['overcap'])) for r in b['resistances'][:9])/180)
  self.memo[key]=v;self.eval_count+=1;return v
 def legal(self,s,v,full=False):
  errors=super().legal(s,v,full)
  for k in ['skills','devotions','bindings']:
   if s[k]!=self.current[k]:errors.append('Fixed saved '+k+' changed')
  if s.get('respec_attributes'):errors.append('Attribute resets disabled')
  return errors
 def component_cost(self,p,seen=None):
  if not p:return 0
  if p in self.costmemo:return self.costmemo[p]
  seen=set() if seen is None else seen
  if p in seen:return 100
  seen=seen|{p};r=self.recipes.get(p);base=self.db.get(p,{})
  # Utility points, NOT iron. Rare owned attachments retain opportunity cost.
  if not r:cost=2 if self.available[p]>0 and base.get('itemClassification') in ['Common','Magical',None] else 18
  else:
   cost=1+float(r.get('artifactCreationCost',0))/5000
   for k,mat in r.items():
    if k.startswith('reagent') and k.endswith('BaseName'):
     q=r.get(k[:-8]+'Quantity',1)
     cost+=q*(self.component_cost(mat,seen) if mat in self.recipes else (1 if self.db.get(mat,{}).get('Class')=='ItemRelic' else 15))
   cost/=max(1,r.get('artifactCreateQuantity',1))
  self.costmemo[p]=cost;return cost
 def cost(self,s):
  rare=destroy=changes=attachments=0
  for i,ident in enumerate(s['gear']):
   item=self.items[ident];saved=item['save'];changes+=ident!=self.current['gear'][i]
   c=s['comp'][i]
   if c!=saved.get('relic-name',''):
    attachments+=bool(c);rare+=self.component_cost(c);destroy+=bool(saved.get('relic-name'))
  aug=sum(bool(p) and (p!=self.items[s['gear'][i]]['save'].get('augment-name') or self.items[s['gear'][i]]['owner'] not in [self.character_name,'Shared Stash']) for i,p in enumerate(s['aug']))
  mult=2 if self.mal['character-level']<100 else 1
  total=changes*4+destroy*8+rare*mult+attachments+aug*.15+sum(s['attributes'])*2
  return {'utility_cost':total,'equipment_changes':changes,'component_replacements':attachments,'destroyed_attached_components':destroy,'component_opportunity_cost':rare,'augment_purchases':aug,'attribute_points_spent':sum(s['attributes'])}
 def deficits(self,v):
  return sum(max(0,r['cap']-r['raw']) for r in v['resistances'][:9])+max(0,1900-v['DA'])/10+max(0,9500-v['health'])/50+max(0,84-v['armor_absorption'])*2
 def score(self,s,v,mode):
  off=v['offense_index'];defense=v['defense_index'];cost=self.cost(s)['utility_cost']
  weight={'minimal':.25,'balanced':.5,'offense':.85}[mode]
  return weight*math.log(max(1,off))+(1-weight)*math.log(max(1,defense))-cost*{'minimal':.003,'balanced':.0008,'offense':.0002}[mode]-self.deficits(v)*.06
 def feasible(self,s,v):
  return not self.legal(s,v,True) and self.deficits(v)<1e-7 and v['offense_index']>=95 and self.equip_order_possible(s)
 def prefer(self,a,b):
  """Within 5% offense and 5% defense, use cheaper configuration."""
  av,bv=a['stats'],b['stats']
  comparable=av['offense_index']>=.95*bv['offense_index'] and av['defense_index']>=.95*bv['defense_index'] and all(av.get(k,1)>=.95*bv.get(k,1) for k in ['health','DA','armor_absorption']) and av.get('armor',1)>=.9*bv.get('armor',1)
  return comparable and a['cost']['utility_cost']<b['cost']['utility_cost']
 def repair_attributes(self,s):
  s=copy.deepcopy(s);s['attributes']=[0,0,0]
  # Only spend for an unmet requirement, never because extra points raise score.
  for _ in range(self.mal['attribute-points']+1):
   v=self.evaluate(s);errs=self.legal(s,v)
   attr=next((j for j,k in enumerate(['physique','cunning','spirit']) if any(k+' requirement' in er for er in errs)),None)
   if attr is None:
    if self.equip_order_possible(s):return s
    # Equip-order-only dependency: add the most deficient attribute without item.
    gaps=[0,0,0]
    for i,ident in enumerate(s['gear']):
     if ident==self.current['gear'][i]:continue
     q=copy.deepcopy(s);q['gear'][i]='EMPTY';q['comp'][i]=q['aug'][i]='';z=self.calculate(q);req=self.items[ident].get('requirements') or {};red=z['stats'].get('characterGlobalReqReduction',0)
     for j,(k,a) in enumerate(zip(['strength','dexterity','intelligence'],['physique','cunning','spirit'])):gaps[j]=max(gaps[j],req.get(k,0)*(1-red/100)-z[a])
    if max(gaps)<=0:return None
    attr=max(range(3),key=lambda j:gaps[j])
   if sum(s['attributes'])>=self.mal['attribute-points']:return None
   s['attributes'][attr]+=1
  return None
 def search_practical(self,width=16,rounds=2):
  started=time.monotonic();opts=self.options();seeds=[copy.deepcopy(self.current)]
  archive=self.d/'archive/results/results.json'
  if archive.exists():
   for ent in json.loads(archive.read_text()).get('chosen',{}).values():
    s=copy.deepcopy(self.current)
    for k in ['gear','comp','aug']:s[k]=ent['state'][k]
    seeds.append(s)
  finalists={};logs=[]
  for mode in ['minimal','balanced','offense']:
   # Static per-slot joint bundles. Retain several alternatives for complementary
   # resistance/skill tradeoffs; complete-loadout beam allows coordinated moves.
   anchor=copy.deepcopy(self.current);bundles=[]
   for i in range(14):
    native=[]
    for ident in opts[i]:
     q=copy.deepcopy(anchor);q['gear'][i]=ident
     for k,sk in [('comp','relic-name'),('aug','augment-name')]:q[k][i]=self.items[ident]['save'].get(sk,'')
     z=self.evaluate(q);native.append((self.score(q,z,mode),q))
    native.sort(key=lambda x:x[0],reverse=True)
    ids=list(dict.fromkeys([x[1]['gear'][i] for x in native[:6]]+[s['gear'][i] for s in seeds]))
    pool={}
    for ident in ids:
     q=copy.deepcopy(anchor);q['gear'][i]=ident
     for k,sk in [('comp','relic-name'),('aug','augment-name')]:q[k][i]=self.items[ident]['save'].get(sk,'')
     comps=list(dict.fromkeys([q['comp'][i],'']+[p for p in self.components if self.compatible(p,i,ident)]));ct=[]
     for c in comps:
      if not self.compatible(c,i,ident):continue
      t=copy.deepcopy(q);t['comp'][i]=c
      if self.resources(t)['errors']:continue
      z=self.evaluate(t);ct.append((self.score(t,z,mode),t))
     ct.sort(key=lambda x:x[0],reverse=True)
     for _,t in ct[:4]:
      for a in list(dict.fromkeys([t['aug'][i],'']+[p for p in self.augments if self.compatible(p,i,ident)])):
       u=copy.deepcopy(t);u['aug'][i]=a
       if self.resources(u)['errors']:continue
       z=self.evaluate(u);bundle=tuple(u[k][i] for k in ['gear','comp','aug']);pool[bundle]=self.score(u,z,mode)
    # Include current and benchmark attachment bundles even when single-slot score
    # is poor. This is essential for bridge moves across several slots.
    ranked=sorted(pool,key=pool.get,reverse=True)[:12]
    for s in seeds:
     b=tuple(s[k][i] for k in ['gear','comp','aug'])
     if b not in ranked:ranked.append(b)
    bundles.append(ranked)
   beam=seeds
   for rd in range(rounds):
    for i in range(14):
     candidates={}
     for s in beam:
      for bundle in bundles[i]:
       q=copy.deepcopy(s)
       for k,val in zip(['gear','comp','aug'],bundle):q[k][i]=val
       if len(set(q['gear']))<14:continue
       z=self.evaluate(q)
       # Keep requirement-deficient intermediates for coordinated support swaps.
       errors=self.legal(q,z)
       if any('requirement' not in er for er in errors) or self.resources(q)['errors']:continue
       key=self.signature(q);candidates[key]=(self.score(q,z,mode),q)
     if candidates:beam=[x[1] for x in sorted(candidates.values(),key=lambda x:x[0],reverse=True)[:width]]
    # Branch from all modes' endpoints as well as current to cross local basins.
    for s in beam:
     q=self.repair_attributes(s)
     if q is None:continue
     z=self.evaluate(q)
     if self.feasible(q,z):finalists[self.signature(q)]={'state':q,'stats':z,'cost':self.cost(q),'resources':self.resources(q)}
    logs.append({'mode':mode,'round':rd+1,'evaluations':self.eval_count,'feasible':len(finalists)});print(logs[-1],flush=True)
   seeds+=beam[:2]
  fs=list(finalists.values());chosen={}
  if fs:
   for mode in ['minimal','balanced','offense']:
    best=min(fs,key=lambda e:e['cost']['utility_cost']) if mode=='minimal' else max(fs,key=lambda e:e['stats']['offense_index']) if mode=='offense' else max(fs,key=lambda e:self.score(e['state'],e['stats'],mode))
    # Select cheapest from a fixed band around winner, avoiding chained 5% drift.
    near=[e for e in fs if self.prefer(e,best)]
    if near:best=min(near+[best],key=lambda e:e['cost']['utility_cost'])
    chosen[mode]=best
  return {'version':VERSION,'chosen':chosen,'baseline':self.evaluate(self.current),'search_log':logs,'seconds':round(time.monotonic()-started,2),'evaluations':self.eval_count,'feasible_candidates':len(fs),'skills_fixed':self.current['skills'],'devotions_fixed':self.current['devotions'],'bindings_fixed':self.current['bindings'],'scope':'Finite joint bundle beam search; no global optimum claim','cost_units':'Preference utility, not iron; actual base iron in resources','defensive_floors':{'DA':1900,'health':9500,'armor_absorption':84,'standard_resistances':'all capped','offense_index':95}}
def fingerprint(d,args):
 h=hashlib.sha256(pathlib.Path(__file__).read_bytes())
 for name in ['GrimDawn_Optimizer.py','database.json.gz','catalog.json','mal.json','baseline.json','penalties.json','localization.json','materials.json','recipes.json','archive/results/results.json','relative_offense.py','offense_profile.json']:
  p=d/name
  if p.exists():h.update(p.read_bytes())
 h.update(str((args.width,args.rounds)).encode());return h.hexdigest()
def report(e,r,path):
 names={'minimal':'Minimal-cost improvements','balanced':'Balanced progression','offense':'Maximum practical offense'}
 lines=['# Mal practical equipment results','','Skills, devotion stars, proc ranks and bindings are fixed to the imported save. Effective skill ranks can change through equipment. No attribute resets.','','Relative offense indices use database-discovered ability mechanics, not DPS. Defense index is a weighted utility of health, DA, armor, absorption, physical resistance and up to +20 resistance overcap. No encounter simulation is used for selection.','','|Build|Offense index|Defense index|Health|OA|DA|Armor|Absorption|New attribute points|Cost utility|','|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|']
 for key,en in [('current',{'stats':r['baseline'],'state':e.current,'cost':e.cost(e.current)})]+list(r['chosen'].items()):
  v=en['stats'];lines.append(f"|{names.get(key,'Current')}|{v['offense_index']:.1f}|{v['defense_index']:.1f}|{v['health']}|{v['OA']}|{v['DA']}|{v['armor']}|{v['armor_absorption']:.1f}%|{sum(en['state']['attributes'])}|{en['cost']['utility_cost']:.1f}|")
 for key,en in r['chosen'].items():
  s=en['state'];v=en['stats'];lines+=['',f'## {names[key]}','','|Slot|Fingerprint|Full item name|Source (location may change)|Component|Augment|Change|','|---|---|---|---|---|---|---|']
  for i,ident in enumerate(s['gear']):
   x=e.items[ident];actions=[]
   if ident!=e.current['gear'][i]:actions.append('Equip item')
   if s['comp'][i]!=x['save'].get('relic-name',''):actions.append('Replace component'+(' (destroys old)' if x['save'].get('relic-name') else ''))
   if s['aug'][i]!=x['save'].get('augment-name',''):actions.append('Apply augment')
   if x['owner'] not in [e.character_name,'Shared Stash'] and x['save'].get('augment-name'):actions.append('Remove donor augment before transfer')
   name=full_name(x)
   lines.append('|'+ '|'.join(str(y).replace('|','/') for y in [SLOTS[i],item_fingerprint(x),name,x['owner']+' (location at import: '+x['location']+')',e.name(s['comp'][i]) or 'None',e.name(s['aug'][i]) or 'None','; '.join(actions) or 'Keep'])+'|')
  lines+=['',f"Effective ranks: Storm Totem {v['effective_skills'].get(STORM,0)}, Wind Devil {v['effective_skills'].get(WIND,0)}, Maelstrom {v['effective_skills'].get(MAEL,0)}. Cooldown reduction {v['cooldown_reduction']:.1f}%. Static lightning modifier {v['lightning_modifier']:.1f}%. Raging Tempest RR {v['raging_tempest_RR']:.1f}; Widow RR {v['widow_RR']:.1f}.",'',f"Attribute points spent now (Physique/Cunning/Spirit): {s['attributes']}. Remaining unspent: {e.mal['attribute-points']-sum(s['attributes'])}.",'','Resistance columns below are after the saved difficulty penalty; do not subtract it again. Signed margin is overcap (+) or shortfall (-).','','|Resistance|Effective before cap|Displayed|Cap|Margin|','|---|---:|---:|---:|---:|']
  for a in v['resistances'][:9]:lines.append(f"|{a['name']}|{a['raw']:.1f}%|{a['shown']}%|{a['cap']:.1f}%|{a['overcap']:+.1f}|")
  lines+=['','Ability factors:']
  for ability in v['offense_model']['abilities'].values():
   pop=ability['population'];lines.append(f"- {ability['name']}: rank {ability['rank']}; max {pop['maximum']:.1f}, sustainable {pop['sustainable']:.2f}, practical {pop['practical']:.2f}; cooldown {ability['cooldown']:.2f}s.")
  lines+=['','Augment eligibility:']
  for p,q in en['resources']['augment_purchases'].items():
   fact=e.db[p].get('factionSource');faction=next((f['name'] for f in e.factions if f['key']==fact),fact);vendor=min(e.vendor[p],key=lambda x:x['required']);lines.append(f"- {q} × {e.name(p)} ({faction}): reputation {e.rep.get(fact)} / {vendor['required']} required; level {e.db[p].get('levelRequirement',0)}; eligible.")
  lines+=['',f"Base crafting iron: {en['resources']['craft_iron_base']}; base augment iron: {en['resources']['augment_iron_base']}. Vendor adjustments and removal fees are additional.",f"Cost breakdown: {json.dumps(en['cost'])}."]
 lines+=['','## Scope and reruns','','Candidates retaining at least 95% of the reference offense and defense index prefer lower cost, with health/DA/absorption within 5% and armor within 10% of the reference. Stronger cheaper alternatives also qualify. The three objectives can legitimately select the same loadout. All selected builds satisfy caps and listed defensive floors, resource eligibility, fixed-save invariants and equip-order checks. Search uses a finite bundle shortlist and beam; no global optimum claim. Current level and available items come from the snapshot; refresh the save before advising later levels. Existing decoder limitations remain. Item IDs are snapshot-specific.','','Run `python practical_optimizer.py` for an input-hashed cached rerun. Run `python practical_optimizer.py --force` to recompute. Run `python -m unittest discover -v` for preserved and new tests. Refresh with the existing `refresh_data.py` before new levels; use `--data` to point at refreshed extracted data. No source save is written.','','Detailed component/augment record paths, stats, resources and states are in practical-results/results.json. Previous results and original optimizer remain under archive/.']
 if not r['chosen']:lines+=['','No feasible loadout found. No defensive-floor waiver was applied.']
 path.write_text('\n'.join(lines))
def main():
 p=argparse.ArgumentParser();p.add_argument('--data',type=pathlib.Path,default=ROOT);p.add_argument('--out',type=pathlib.Path,default=ROOT/'practical-results');p.add_argument('--width',type=int,default=16);p.add_argument('--rounds',type=int,default=2);p.add_argument('--force',action='store_true');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
 key=fingerprint(a.data,a);target=a.out/'results.json'
 if target.exists() and not a.force:
  r=json.loads(target.read_text())
  if r.get('input_hash')==key:print('Cached results unchanged:',target);return
 e=PracticalEngine(a.data);validation=e.validate()
 if any(x['difference'] for x in validation if x['difference'] is not None):raise SystemExit('Baseline mismatch')
 r=e.search_practical(a.width,a.rounds);r['input_hash']=key;r['validation']=validation
 target.write_text(json.dumps(r,indent=2));report(e,r,a.out/'Mal_Practical_Results.md');print('Saved',target,flush=True)
if __name__=='__main__':main()
