"""Bounded v1.2 equipment search with unscored weapon damage and conservative guards.
No Cadence, dual-wield, WPS or combat mechanics are implemented here.
"""
import copy,json,pathlib,hashlib,argparse,shutil,time,itertools
from practical_optimizer import PracticalEngine
from GrimDawn_Optimizer import Engine,ROOT,SLOTS,RES,at
from relative_offense import difficulty_penalties
DATA=ROOT/'characters/Beeztrap'
class UnscoredWeaponOffense:
 def summarize(self,s,v):return {'status':'NOT_RANKED','reason':'v1.2 does not model weaponDamagePct, Cadence charged finale, Deadly Momentum uptime or dual-wield WPS sequencing.'}
 def index(self,current,baseline):return 100.0 # neutral search placeholder, NEVER reported as performance
class BeeztrapEquipment(PracticalEngine):
 def __init__(self,directory=DATA):
  super().__init__(directory);self.model=UnscoredWeaponOffense();self.memo={};self.base=self.calculate(self.current);self.eval_count=0
  self.anchor=self.base;self.ultimate_pen=difficulty_penalties(self.db,2);self.target_ultimate=(int(self.mal['last-difficulty'])&3)==2
  self.protected=[p for p in self.current['skills'] if p.endswith(('cadence1.dbr','cadence2.dbr','cadence3.dbr','wpattack0.dbr','nightbladeenchant1.dbr')) or self.db[p].get('skillChanceWeight')]
  self.guard_stats=['characterAttackSpeedModifier','offensivePierceModifier','offensivePhysicalModifier','offensiveSlowPhysicalModifier','offensiveLifeLeechMin']
  self.convcache={};self.endpoint_audit=[]
  self.saved_configuration=hashlib.sha256(json.dumps({k:self.mal.get(k) for k in ['skills','hotbars','skill-sets','weapon-sets','use-alt-weaponset','alt-weapon-set']},sort_keys=True).encode()).hexdigest()
 def compatible(self,p,i,ident):return super().compatible(p,12 if i==13 else i,ident)
 def options(self):
  if getattr(self,'attachments_only',False):return [[x] for x in self.current['gear']]
  opts=super().options()
  for i,ids in enumerate(opts):
   opts[i]=[ident for ident in ids if ident==self.current['gear'][i] or all((self.items[ident].get('requirements') or {}).get(field,0)*(1-self.anchor['stats'].get('characterGlobalReqReduction',0)/100)<=self.anchor[attr]+self.mal['attribute-points']*10 for field,attr in [('strength','physique'),('dexterity','cunning'),('intelligence','spirit')])]
  opts[1]=[self.current['gear'][1]];opts[11]=[self.current['gear'][11]];opts[12]=[self.current['gear'][12]];opts[13]=[self.current['gear'][13]]
  return opts
 def conversion_signature(self,s):
  values=[]
  for i,ident in enumerate(s['gear']):
   key=(ident,s['comp'][i],s['aug'][i])
   if key not in self.convcache:
    rs=self.item_records(ident,s['comp'][i],s['aug'][i])
    records=list(rs)
    for r in rs:
     for j in range(1,6):
      if r.get('modifierSkillName'+str(j)):records.append(self.db.get(r['modifierSkillName'+str(j)],{}))
    self.convcache[key]=sorted((r.get('conversionInType'+j),r.get('conversionOutType'+j),str(r.get('conversionPercentage'+j))) for r in records for j in ['', '2','3','4','5'] if r.get('conversionInType'+j))
   values+=self.convcache[key]
  return sorted(values)
 def legal(self,s,v,full=False):
  errs=super().legal(s,v,full)
  for k in ['gear','comp','aug']:
   if s[k][12:]!=self.current[k][12:]:errs.append('Locked dual-wield weapons and weapon attachments')
  if self.conversion_signature(s)!=self.conversion_signature(self.current):errs.append('Unranked damage-conversion change')
  for i,ident in enumerate(s['gear']):
   for field,attr,stat in [('strength','physique','Strength'),('dexterity','cunning','Dexterity'),('intelligence','spirit','Intelligence')]:
    error=ident+' '+attr+' requirement'
    if error in errs and self.requirement_met(ident,i,v,field,attr,stat):errs.remove(error)
  return errs
 def requirement_met(self,ident,i,v,field,attr,stat):
  group='Weapon' if i in [12,13] else 'Jewelry' if self.items[ident]['records'][0].get('Class','').startswith('ArmorJewelry') else 'Armor'
  global_red=max(0,1-v['stats'].get('characterGlobalReqReduction',0)/100)
  specific=max(0,1-v['stats'].get('character'+group+stat+'ReqReduction',0)/100)
  return v[attr]+1e-5>=(self.items[ident].get('requirements') or {}).get(field,0)*global_red*specific
 def equip_order_possible(self,s):
  now=copy.deepcopy(self.current);now['attributes']=s['attributes'];left=[i for i in range(14) if now['gear'][i]!=s['gear'][i]]
  while left:
   changed=False
   for i in left[:]:
    q=copy.deepcopy(now);q['gear'][i]='EMPTY';q['comp'][i]=q['aug'][i]='';v=self.calculate(q)
    if all(self.requirement_met(s['gear'][i],i,v,f,a,t) for f,a,t in [('strength','physique','Strength'),('dexterity','cunning','Dexterity'),('intelligence','spirit','Intelligence')]):
     for key in ['gear','comp','aug']:now[key][i]=s[key][i]
     left.remove(i);changed=True
   if not changed:return False
  return True
 def offense_guard_gaps(self,v):
  gaps=[]
  for p in self.protected:
   short=self.anchor['effective_skills'].get(p,0)-v['effective_skills'].get(p,0)
   if short>0:gaps.append(('rank '+self.name(p),float(short)))
  if v['OA']<.99*self.anchor['OA']:gaps.append(('OA',(.99*self.anchor['OA']-v['OA'])/20))
  for p in self.guard_stats:
   old=self.anchor['stats'].get(p,0);new=v['stats'].get(p,0)
   minimum=.95*(100+old)-100 if p in ['offensivePierceModifier','offensivePhysicalModifier','offensiveSlowPhysicalModifier'] else old
   if new+1e-6<minimum:gaps.append((p,(minimum-new)/max(1,abs(old))*20))
  return gaps
 def ultimate_rows(self,v):
  return [{**r,'raw':r['raw']-self.pen[f]+self.ultimate_pen[f],'shown':min(r['cap'],r['raw']-self.pen[f]+self.ultimate_pen[f]),'overcap':r['raw']-self.pen[f]+self.ultimate_pen[f]-r['cap']} for f,r in zip(RES,v['resistances'])]
 def deficits(self,v):
  rows=self.ultimate_rows(v) if self.target_ultimate else v['resistances']
  return sum(max(0,r['cap']-r['raw']) for r in rows[:9])+max(0,1900-v['DA'])/10+max(0,self.anchor['health']-v['health'])/50+max(0,90-v['armor_absorption'])*2+max(0,.95*self.anchor['armor']-v['armor'])/20+sum(x for _,x in self.offense_guard_gaps(v))
 def repair_attributes(self,s):
  q=super().repair_attributes(s)
  if q is None:
   v=self.evaluate(s);self.endpoint_audit.append({'state':s,'attribute_repair_failed':True,'legal':self.legal(s,v,True),'deficits':self.deficits(v),'offense_gaps':self.offense_guard_gaps(v)})
  if q is not None:
   v=self.evaluate(q);self.endpoint_audit.append({'state':q,'health':v['health'],'DA':v['DA'],'armor':v['armor'],'absorption':v['armor_absorption'],'offense_gaps':self.offense_guard_gaps(v),'deficits':self.deficits(v),'elite_resistances':[r['raw'] for r in v['resistances'][:9]],'ultimate_resistances':[r['raw'] for r in self.ultimate_rows(v)[:9]],'legal':self.legal(q,v,True)})
  return q
 def score(self,s,v,mode):
  score=super().score(s,v,mode)
  if self.deficits(v)>1e-7:score-=10
  for i,ident in enumerate(s['gear']):
   for f,a,t in [('strength','physique','Strength'),('dexterity','cunning','Dexterity'),('intelligence','spirit','Intelligence')]:
    if not self.requirement_met(ident,i,v,f,a,t):score-=.05
  return score
 def run(self,width=16,rounds=2):
  # Existing search, cost model and anchored 5% preference rule are inherited.
  result=self.search_practical(width,rounds)
  result['rejected_endpoint_audit']=self.endpoint_audit
  result=self.repair_endpoints(result)
  result['defensive_floors']={'health':self.anchor['health'],'DA':1900,'armor':.95*self.anchor['armor'],'armor_absorption':90,'resistances':'All nine capped on selected target difficulty'}
  result['maximum_offense_status']='NOT_ESTABLISHED'
  result['offense_status']='NOT_RANKED; internal offense_index=100 is neutral, not a gain estimate.'
  result['interpretation']='Defensive equipment candidates retaining both swords, attachments and recognized offensive inputs. Maximum overall offense is not established by v1.2.'
  result['target_difficulty']=('Normal','Elite','Ultimate')[int(self.mal['last-difficulty'])&3]
  result['baseline']=self.evaluate(self.current);result['baseline_state']=self.current;result['baseline_validation']=self.validate()
  result['saved_configuration_hash']=self.saved_configuration;result['skills_fixed']=self.current['skills'];result['devotions_fixed']=self.current['devotions'];result['bindings_fixed']=self.current['bindings']
  for en in result['chosen'].values():
   v=en['stats'];en['ultimate_resistances']=self.ultimate_rows(v);en['offensive_guard_gaps']=self.offense_guard_gaps(v)
  now=hashlib.sha256(json.dumps({k:self.mal.get(k) for k in ['skills','hotbars','skill-sets','weapon-sets','use-alt-weaponset','alt-weapon-set']},sort_keys=True).encode()).hexdigest();assert now==self.saved_configuration
  return result

 def repair_endpoints(self,result):
  # Bounded reversions to already-owned current gear; no new combat scoring.
  starts=[];seen=set()
  for row in sorted(result.get('rejected_endpoint_audit',[]),key=lambda x:x.get('deficits',1e9)):
   state=row['state'];sig=self.signature(state)
   if sig not in seen:starts.append(state);seen.add(sig)
   if len(starts)>=6:break
  pool={self.signature(x['state']):x for x in result.get('chosen',{}).values()};examined=0
  for start in starts:
   slots=[i for i in range(12) if any(start[k][i]!=self.current[k][i] for k in ['gear','comp'])]
   for count in range(3):
    for sub in itertools.combinations(slots,count):
     q=copy.deepcopy(start)
     for i in sub:
      q['gear'][i]=self.current['gear'][i];q['comp'][i]=self.current['comp'][i]
      if not self.compatible(q['aug'][i],i,q['gear'][i]):q['aug'][i]=self.current['aug'][i]
     v=self.evaluate(q);examined+=1
     if self.deficits(v)>1e-7:continue
     q=self.repair_attributes(q)
     if q is None:continue
     v=self.evaluate(q)
     if self.feasible(q,v):pool[self.signature(q)]={'state':q,'stats':v,'cost':self.cost(q),'resources':self.resources(q)}
  fs=list(pool.values());chosen={}
  if fs:
   for mode in ['minimal','balanced','offense']:
    best=min(fs,key=lambda e:e['cost']['utility_cost']) if mode=='minimal' else max(fs,key=lambda e:self.score(e['state'],e['stats'],mode))
    near=[e for e in fs if self.prefer(e,best)]
    if near:best=min(near+[best],key=lambda e:e['cost']['utility_cost'])
    chosen[mode]=best
  result['chosen']=chosen;result['bounded_reversion_candidates_examined']=examined;result['feasible_repaired_candidates']=len(fs)
  return result

def key_for(args):
 h=hashlib.sha256(pathlib.Path(__file__).read_bytes())
 for name in ['GrimDawn_Optimizer.py','practical_optimizer.py','relative_offense.py']:
  h.update((ROOT/name).read_bytes())
 for name in ['database.json.gz','catalog.json','mal.json','baseline.json','penalties.json','materials.json','recipes.json','localization.json']:h.update((DATA/name).read_bytes())
 h.update(str((args.width,args.rounds)).encode());return h.hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--width',type=int,default=16);ap.add_argument('--rounds',type=int,default=2);ap.add_argument('--attachments-only',action='store_true');ap.add_argument('--force',action='store_true');a=ap.parse_args()
 # Shared database bytes are restored locally after extracting the compact ZIP.
 for name in ['database.json.gz','localization.json','guide70.json','guide83.json']:
  if not (DATA/name).exists():shutil.copy2(ROOT/name,DATA/name)
 out=DATA/'results';out.mkdir(exist_ok=True);key=key_for(a);target=out/'results.json'
 if target.exists() and not a.force and json.loads(target.read_text()).get('input_hash')==key:print('Cached Beeztrap candidates unchanged:',target);return
 e=BeeztrapEquipment();e.attachments_only=a.attachments_only
 discrepancies=[x for x in e.validate() if x['difference']]
 if discrepancies:raise SystemExit('Baseline validation failed: '+str(discrepancies))
 r=e.run(a.width,a.rounds);r['input_hash']=key;target.write_text(json.dumps(r,indent=2));print('Final candidates:',list(r['chosen']),flush=True)
if __name__=='__main__':main()
