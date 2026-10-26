"""Small, data-driven relative ability model; no enemies, hits, ticks or rotation simulation.
Unsupported cadence, AI, weapon payload and stacking are explicitly flagged.
"""
import ast,collections,json,math,pathlib,re
from GrimDawn_Optimizer import at,family
TYPES=['Physical','Pierce','Fire','Cold','Lightning','Poison','Life','Aether','Chaos','Bleeding']
DOT={'Physical':'SlowPhysical','Fire':'SlowFire','Cold':'SlowCold','Lightning':'SlowLightning','Poison':'SlowPoison','Life':'SlowLife','Bleeding':'SlowBleeding'}
ELEMENTS=['Fire','Cold','Lightning'];MAGIC=set(TYPES)-{'Physical','Pierce','Bleeding'}
PENALTY_RECORD='records/game/balancingadjustment_mp+difficulty_players01.dbr'
def difficulty_penalties(db,difficulty):
 if difficulty not in [0,1,2]:raise ValueError('Unsupported difficulty')
 r=db[PENALTY_RECORD];fields=['defensive'+x for x in ['Fire','Cold','Lightning','Poison','Pierce','Bleeding','Life','Aether','Chaos','Physical']]
 return {f:float(r.get(f,[0]*12)[difficulty*4]) for f in fields}
def useful_overcap(rows):return sum(min(20,max(0,r['overcap'])) for r in rows[:9])/180

def level_value(x,rank=1,charlevel=1):
 if isinstance(x,str):
  try:
   def walk(n):
    if isinstance(n,ast.Expression):return walk(n.body)
    if isinstance(n,ast.Constant) and isinstance(n.value,(int,float)):return n.value
    if isinstance(n,ast.Name) and n.id=='charLevel':return charlevel
    if isinstance(n,ast.BinOp):
     a,b=walk(n.left),walk(n.right)
     if isinstance(n.op,ast.Add):return a+b
     if isinstance(n.op,ast.Sub):return a-b
     if isinstance(n.op,ast.Mult):return a*b
     if isinstance(n.op,ast.Div):return a/b
    raise ValueError('Unsupported DB equation')
   return max(0,walk(ast.parse(x,mode='eval')))
  except (ValueError,SyntaxError,ZeroDivisionError):return None
 return at(x,rank)

def instance_budget(cap,burst,cooldown,duration,window=8):
 """Closed-form population availability. No individual spawn events simulated.
 Permanent pets: full population after setup; cooldown cannot boost their attacks.
 Temporary: bound by duration/deployment and discount filling a fresh population.
 """
 cap=max(0,cap);burst=max(.01,burst);interval=max(.05,cooldown)
 if duration is None:return {'maximum':cap,'sustainable':cap,'practical':cap,'lifetime':'permanent','deployment_interval':interval,'setup_seconds':max(0,math.ceil(cap/burst)-1)*interval}
 duration=max(0,duration);rate=burst/interval;steady=min(cap,duration*rate)
 first=min(steady,burst);fill=max(0,(steady-first)/rate);h=max(.1,window)
 startup=steady-(steady-first)*fill/(2*h) if fill<=h else first+rate*h/2
 practical=min(steady,(steady+startup)/2)
 return {'maximum':cap,'sustainable':steady,'practical':practical,'lifetime':duration,'deployment_interval':interval,'setup_seconds':fill}

def conversions(records,rank=1):
 out=[]
 for r,l in records:
  for i in ['', '2','3','4','5','6']:
   src=r.get('conversionInType'+i);dst=r.get('conversionOutType'+i);pct=at(r.get('conversionPercentage'+i),l)
   if src and dst and pct>0:out.append((src,dst,pct))
 return out

def convert_payload(payload,local,global_):
 """Each original unit converts once. Excess allocations normalize per source."""
 frozen=collections.Counter();remaining=collections.Counter(payload)
 for stage in [local,global_]:
  after=collections.Counter();by=collections.defaultdict(list)
  for a,b,p in stage:
   if a=='Elemental':
    for z in ELEMENTS:by[z].append((b,p))
   else:by[a].append((b,p))
  for src,value in remaining.items():
   dot=src.startswith('Slow');base=next((t for t,d in DOT.items() if d==src),src)
   opts=by.get(base,[]);scale=max(100,sum(p for _,p in opts));used=0
   for dst,p in opts:
    dsts=ELEMENTS if dst=='Elemental' else [dst]
    # Conversion to a type with no corresponding DoT leaves that DoT unchanged.
    valid=[DOT.get(d) if dot else d for d in dsts]
    if any(d is None for d in valid):continue
    n=value*p/scale;used+=n
    for d in valid:frozen[d]+=n/len(valid)
   after[src]+=value-used
  remaining=after
 frozen.update(remaining);return dict(frozen)

def rr_categories(sources):
 """Different named additive debuffs sum; flat/relative reduction take strongest.
 Repeated instances of the same source are deduplicated. Applies no enemy model.
 """
 additive=collections.defaultdict(dict);flat=collections.Counter();relative=collections.Counter()
 for source,r,l in sources:
  for typ in TYPES:
   a=at(r.get('defensive'+typ),l)
   if typ in ELEMENTS:a+=at(r.get('defensiveElementalResistance'),l)
   if a<0:additive[typ][source]=max(additive[typ].get(source,0),-a)
   for category,dest,suffix in [('flat',flat,'AbsoluteMin'),('relative',relative,'PercentMin')]:
    vals=[at(r.get('offensiveTotalResistanceReduction'+suffix),l),at(r.get('offensive'+typ+'ResistanceReduction'+suffix),l)]
    if typ in ELEMENTS:vals.append(at(r.get('offensiveElementalResistanceReduction'+suffix),l))
    dest[typ]=max(dest[typ],*vals)
 return {t:{'additive':sum(additive[t].values()),'flat':flat[t],'relative':relative[t]} for t in TYPES}

def payload_of(r,rank):
 out=collections.Counter()
 for typ in TYPES+list(DOT.values()):
  lo=r.get('offensive'+typ+'Min');hi=r.get('offensive'+typ+'Max',lo)
  if lo is not None or hi is not None:out[typ]+=(at(lo if lo is not None else hi,rank)+at(hi,rank))/2
 lo=r.get('offensiveElementalMin');hi=r.get('offensiveElementalMax',lo)
 if lo is not None:
  for t in ELEMENTS:out[t]+=(at(lo,rank)+at(hi,rank))/6
 return out

class RelativeOffense:
 def __init__(self,engine):
  self.e=engine;self.db=engine.db;self.metadata={};self.graphcache={}
  p=engine.d/'offense_profile.json';self.profile=json.loads(p.read_text()) if p.exists() else {}
  if self.profile.get('character') not in [None,engine.mal.get('character-name')]:self.profile={}
  self.window=self.profile.get('deployment_window_seconds',8);self.action=self.profile.get('assumed_player_action_seconds',1)
  self.roots=[p for p in engine.current['skills'] if self.db.get(p,{}).get('spawnObjects') or self.db.get(p,{}).get('Class','').startswith(('Skill_Attack','Skill_Projectile','Skill_Channel'))]
  self.weights=self.profile.get('abilities',{})
  self.support=self.profile.get('support_skills',[])
 def graph(self,path,rank):
  key=(path,rank)
  if key in self.graphcache:return self.graphcache[key]
  todo=[(path,rank)];out=[];seen=set()
  while todo and len(out)<100:
   p,l=todo.pop()
   if p in seen or not p:continue
   seen.add(p);r=self.db.get(p,{})
   if not r:continue
   out.append((p,r,l))
   for k in ['buffSkillName','debufSkillName','attackSkillName','projectileName','skillProjectileName','petSkillName']:
    if r.get(k) in self.db:todo.append((r[k],l))
   if r.get('spawnObjects'):
    a=r['spawnObjects'];q=a[max(0,min(len(a)-1,int(l)-1))] if isinstance(a,list) else a
    todo.append((q,l))
   # Actor skills with a zero level are item-modifier hooks, not learned attacks.
   for k,q in r.items():
    m=re.fullmatch(r'skillName(\d+)',k)
    if not m:continue
    x=level_value(r.get('skillLevel'+m[1],0),l,self.e.mal['character-level'])
    if x is not None and x>0 and q in self.db:todo.append((q,max(1,int(x))))
  self.graphcache[key]=out;return out
 def equipment_records(self,s):
  out=[];mods=collections.defaultdict(list)
  for i,ident in enumerate(s['gear']):
   x=self.e.items[ident]
   rs=[r for r in x['records'] if r]+[self.db.get(s[k][i],{}) for k in ['comp','aug']]
   for r in rs:
    out.append((r,1))
    for j in range(1,6):
     target=r.get('modifiedSkillName'+str(j));rec=self.db.get(r.get('modifierSkillName'+str(j)),{})
     if target:mods[target].append((rec,1))
  return out,mods
 def describe(self,root,eff,mods):
  rank=eff.get(root,0);nodes=list(self.graph(root,rank));paths={p for p,_,_ in nodes}
  hooks={v for _,q,_ in nodes for k,v in q.items() if re.fullmatch(r'skillName\d+',k)}
  r=self.db[root];spawn=bool(r.get('spawnObjects'));actor=next((q for _,q,_ in nodes if q.get('Class') in ['Pet','PetPlayerScaling']),None)
  # Secondary saved pet modifiers are linked explicitly by petSkillName.
  for p,l in eff.items():
   q=self.db.get(p,{})
   if q.get('Class')=='SkillSecondary_PetModifier' and q.get('petSkillName') in paths|hooks:
    target=q['petSkillName'];branch=self.graph(target,l);branchpaths={a for a,_,_ in branch};nodes=[(a,b,c) for a,b,c in nodes if a not in branchpaths]+branch;paths.update(branchpaths)
   elif q.get('Class') in ['Skill_Modifier','Skill_Transmuter'] and family(p,q)&family(root,r):nodes.append((p,q,l))
  localmods=[]
  for p in {root}|paths:localmods+=mods.get(p,[])
  return nodes,localmods,actor
 def rr(self,s,v,mods):
  sources=[];roots=list(self.weights) if self.weights else self.roots
  selected=set(roots+self.support)
  for root in selected:
   if root not in v['effective_skills']:continue
   nodes,lm,_=self.describe(root,v['effective_skills'],mods)
   for p,r,l in nodes:sources.append((p,r,l))
   for j,(r,l) in enumerate(lm):sources.append((root+' modifier '+str(j),r,l))
  # Only assigned devotion powers with an offensive source/support skill are used.
  assigned={q for p,q in s['bindings'].items() if p in selected}
  for power,l in s['devotions'].items():
   if power not in assigned:continue
   for p,r,rank in self.graph(power,max(1,l)):sources.append((power+' '+p,r,rank))
  return rr_categories(sources)
 def global_records(self,s,v,equip):
  out=list(equip)
  for p,l in v['effective_skills'].items():
   r=self.db.get(p,{})
   if r.get('Class') in ['Skill_Passive','Skill_BuffSelfToggled','Skill_BuffRadiusToggled','Skill_BuffAttackRadiusToggled']:
    out.append((r,l))
    if r.get('buffSkillName'):out.append((self.db.get(r['buffSkillName'],{}),l))
  for p,l in s['devotions'].items():
   r=self.db.get(p,{})
   if r.get('Class')=='Skill_Passive':out.append((r,1))
  return out
 def ability(self,root,s,v,equip,mods,rr,global_records):
  nodes,localmods,actor=self.describe(root,v['effective_skills'],mods);r=self.db[root];rank=v['effective_skills'].get(root,0);notes=[]
  rootmods=mods.get(root,[]);delta=lambda key:sum(at(q.get(key),l) for q,l in rootmods)
  spawn=bool(r.get('spawnObjects'));pet_scaling=bool(actor and actor.get('Class')=='Pet');domain='pet' if pet_scaling else 'player'
  cdr=v['cooldown_reduction'] # summoner cooldown, never autonomous attack cadence
  cd=max(0,(at(r.get('skillCooldownTime'),rank)+delta('skillCooldownTime'))*(1-cdr/100))
  # Player action time only limits deployment. It never accelerates autonomous pets.
  speed=max(.1,1+v['stats'].get('characterSpellCastSpeedModifier',0)/100)
  interval=max(cd,self.action/speed)
  cap=at(r.get('petLimit',1),rank)+delta('petLimit');burst=at(r.get('petBurstSpawn',1),rank)+delta('petBurstSpawn')
  duration=at(r['spawnObjectsTimeToLive'],rank)+delta('spawnObjectsTimeToLive') if 'spawnObjectsTimeToLive' in r else None
  population=instance_budget(cap,burst,interval,duration,self.window) if spawn else {'maximum':1,'sustainable':1,'practical':1,'lifetime':None,'deployment_interval':interval,'setup_seconds':0}
  stats=v['stats'];globalconv=conversions(global_records);localconv=conversions(localmods)
  if pet_scaling:
   # Pet bonuses are a separate domain. Do not give a pet the owner's spell stats.
   petstats=collections.Counter()
   for q,l in global_records:
    br=self.db.get(q.get('petBonusName'),{})
    pl=at(q.get('petBonusLevel',1),l) or 1
    petstats.update({k:at(x,pl) for k,x in br.items() if isinstance(x,(list,int,float))})
   stats=petstats;globalconv=conversions([(self.db.get(q.get('petBonusName'),{}),l) for q,l in global_records]);notes.append('Pet life/AI/survival not predicted; permanent population is after setup.')
  channels=collections.Counter();parts=[];seen=set();modpaths={p for p,q,l in nodes if q.get('Class') in ['Skill_Modifier','Skill_Transmuter']}
  parentmods=[(q,l) for p,q,l in nodes if p in modpaths]+localmods
  primary=max(((p,sum(payload_of(q,l).values())) for p,q,l in nodes if q.get('Class','').startswith('Skill_Attack')),key=lambda x:x[1],default=('',0))[0]
  for p,q,l in nodes:
   if p in seen or p in modpaths:continue
   seen.add(p);base=payload_of(q,l)
   if not base:continue
   # Attach learned modifiers to their containing ability; actor attack modifiers
   # are not applied to unrelated pet attacks unless explicit item target matches.
   addmods=parentmods if not spawn else ([(mr,ml) for path,mr,ml in nodes if path in modpaths] if q.get('Class')=='SkillBuff_Debuf' else [])+mods.get(p,[])+(mods.get(root,[]) if p==primary else [])
   payload=collections.Counter(base)
   for mr,ml in addmods:payload.update(payload_of(mr,ml))
   for t in list(payload):
    pct=sum(at(mr.get('offensive'+t+'Modifier'),ml)+at(mr.get('offensiveTotalDamageModifier'),ml)+(at(mr.get('offensiveElementalModifier'),ml) if t in ELEMENTS else 0) for mr,ml in addmods)
    payload[t]*=max(0,1+pct/100)
   converted=convert_payload(payload,conversions(addmods),globalconv)
   aura=q.get('Class') in ['SkillBuff_Debuf','Skill_BuffRadius','Skill_Debuff','SkillBuff_Debuff']
   instances=min(1,population['practical']) if aura else population['practical']
   if spawn and at(q.get('skillActiveDuration'),l)>0:notes.append('Autonomous active-buff recast gaps unknown; fixed baseline cadence, no claimed exact uptime.')
   if aura:notes.append('Identical debuff aura does not stack across instances.')
   # Interval is database-defined autonomous cadence where available. Unknown
   # animation cadence is a normalized 1, with no player speed inheritance.
   native_interval=at(q.get('skillTargetInterval'),l) or at(q.get('skillCooldownTime'),l)
   frequency=1/max(.1,native_interval) if native_interval else 1
   if pet_scaling and not native_interval:
    is_attack='Attack' in q.get('Class','')
    frequency*=max(.1,1+stats.get('characterAttackSpeedModifier' if is_attack else 'characterSpellCastSpeedModifier',0)/100)
   if spawn and not native_interval:notes.append('Autonomous animation cadence unknown: normalized to 1; no player attack/cast-speed multiplier.')
   if not spawn:
    attack=('Weapon' in q.get('Class','') or at(q.get('offensiveWeaponDamage'),l)>0)
    spd=1+stats.get('characterAttackSpeedModifier' if attack else 'characterSpellCastSpeedModifier',0)/100
    frequency=1/max(cd,self.action/max(.1,spd));notes.append('Action animation unavailable: normalized base action of 1 second.')
   part=0
   for typ,flat in converted.items():
    if flat<=0:continue
    dot=typ.startswith('Slow');physical=typ in ['Physical','Pierce','SlowPhysical','SlowBleeding','Bleeding'];target=next((t for t,x in DOT.items() if x==typ),typ)
    pct=stats.get('offensive'+typ+'Modifier',0)+stats.get('offensiveTotalDamageModifier',0)
    if typ in ELEMENTS:pct+=stats.get('offensiveElementalModifier',0)
    if not pet_scaling:pct+=(v['cunning']*.41 if physical else v['spirit']*100/215)
    # Chance-based damage bonuses are expected, not counted at full magnitude.
    for mr,ml in global_records if not pet_scaling else []:
     chance=mr.get('offensive'+typ+'ModifierChance')
     if chance is not None:pct-=at(mr.get('offensive'+typ+'Modifier'),ml)*(1-at(chance,ml)/100)
    boost=max(.01,1+pct/100)
    rate=frequency
    if dot:
     dur=(at(q.get('offensive'+typ+'DurationMin'),l) or 1)*max(0,1+stats.get('offensive'+typ+'DurationModifier',0)/100)
     rate=min(1,frequency*dur) # refresh coverage, never ticks-per-second stacking
    cats=rr.get(target,{});rrutility=1+(cats.get('additive',0)+cats.get('flat',0))/100
    # Relative RR depends on starting enemy resistance. Keep/report category,
    # but give no unconditional multiplier without an enemy reference.
    if cats.get('relative',0):notes.append('Relative % reduced RR reported separately; no enemy-independent damage multiplier credited.')
    oa=max(.1,v['OA']/2000)*(1+stats.get('offensiveCritDamageModifier',0)/500) if not pet_scaling else max(.1,(at(actor.get('characterOffensiveAbility'),rank) or self.e.mal['character-level']*9+90)/2000)*(1+stats.get('characterOffensiveAbilityModifier',0)/100)
    contribution=flat*boost*rate*instances*oa*rrutility;part+=contribution;channels[typ]+=contribution
   parts.append({'record':p,'rank':l,'base_payload':dict(base),'converted_payload':converted,'instances':instances,'frequency':frequency,'debuff_aura':aura,'strength':part})
  if any(at(q.get('offensiveWeaponDamage'),l)>0 for _,q,l in nodes):notes.append('Weapon-damage payload/WPS/dual-wield selection unresolved; omitted, not invented. Compare weapon-focused builds only after adding a data profile with verified payload support.')
  return {'name':self.e.name(root),'rank':rank,'scaling':domain,'population':population,'cooldown':cd,'strength':sum(channels.values()),'channels':dict(channels),'parts':parts,'limitations':sorted(set(notes))}
 def summarize(self,s,v):
  equip,mods=self.equipment_records(s);gr=self.global_records(s,v,equip);rr=self.rr(s,v,mods)
  roots=list(self.weights) if self.weights else self.roots
  abilities={p:self.ability(p,s,v,equip,mods,rr,gr) for p in roots if v['effective_skills'].get(p,0)>0}
  return {'abilities':abilities,'resistance_reduction':rr,'resistance_reduction_order':'different additive debuffs summed, then strongest relative reduced, then strongest flat reduced; no enemy resistance substituted','policy':{'deployment_window_seconds':self.window,'player_action_seconds':self.action,'weights':self.weights or 'automatic baseline strength contributions'},'limitations':['RR categories preserve stacking; numeric RR value is a static additive+flat utility, not post-resistance damage.','Source lifetime limits DoT population; no extra lingering DoTs from retired summons are credited.','Pet AI, animation speed, survival, shotgun/projectile overlaps and weapon payload are not simulated.']}
 def index(self,summary,baseline):
  if self.weights:
   weights={p:w for p,w in self.weights.items() if baseline['abilities'].get(p,{}).get('strength',0)>0}
  else:weights={p:a['strength'] for p,a in baseline['abilities'].items() if a['strength']>0}
  total=sum(weights.values())
  if total<=0:raise ValueError('No supported offensive payload found. Add a verified ability profile before recommending gear.')
  return 100*sum(w*summary['abilities'].get(p,{}).get('strength',0)/baseline['abilities'][p]['strength'] for p,w in weights.items())/total
