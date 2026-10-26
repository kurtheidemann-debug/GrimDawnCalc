#!/usr/bin/env python3
"""Deterministic, inventory-constrained Grim Dawn loadout search. Python 3.11+, stdlib only.

Numerical results reproduce the supplied gd-edit baseline, not an independently
instrumented game engine. Offensive outputs are defined encounter proxies, not DPS.
"""
import argparse,collections,copy,gzip,hashlib,json,math,pathlib,random,re,struct,time
from item_identity import transferable
ROOT=pathlib.Path(__file__).resolve().parent
def read(p):
 p=pathlib.Path(p)
 with (gzip.open(p,'rt',encoding='utf8') if str(p).endswith('.gz') else p.open(encoding='utf8')) as f:return json.load(f)
def f32(v):return struct.unpack('f',struct.pack('f',float(v)))[0]
def modified(b,p):return f32(f32(b)*f32(1+f32(p/100)))
def at(v,l=1):
 if isinstance(v,(int,float)):return float(v)
 if isinstance(v,list) and v:
  z=v[max(0,min(len(v)-1,int(l or 1)-1))]
  return float(z) if isinstance(z,(int,float)) else 0.
 return 0.
def clean(s):return re.sub(r'\x1b\[[0-9;]*m','',str(s or '')).replace('^k','')
RES=['defensiveFire','defensiveCold','defensiveLightning','defensivePoison','defensivePierce','defensiveBleeding','defensiveLife','defensiveAether','defensiveChaos','defensivePhysical']
RN=['Fire','Cold','Lightning','Poison & Acid','Pierce','Bleeding','Vitality','Aether','Chaos','Physical']
SLOTS=['Head','Amulet','Chest','Legs','Feet','Hands','Ring1','Ring2','Belt','Shoulders','Medal','Relic','Weapon','Offhand']
SLOTKEY=['head','amulet','chest','legs','feet','hands','ring','ring','waist','shoulders','medal','','dagger','offhand']
ARMOR={0:('Head',15),9:('Shoulders',15),2:('Chest',26),5:('Arms',12),3:('Legs',20),4:('Feet',12)}
STORM='records/skills/playerclass06/stormtotem01.dbr';WIND='records/skills/playerclass06/squall1.dbr';RAGE='records/skills/playerclass06/squall2.dbr';MAEL='records/skills/playerclass06/squall3.dbr'
SC='records/skills/playerclass06/stormcaller1.dbr';SPHERE='records/skills/playerclass05/sphereofprotection1.dbr';INNER='records/skills/playerclass05/passive01.dbr'
def family(p,r):
 out=set()
 for s in [r.get('skillUpBitmapName',''),p]:
  s=s.lower().split('/')[-1];s=re.sub('^skillicon_','',s);s=re.sub(r'(up|down)\.tex$|\.dbr$','',s);s=re.sub(r'\d+$','',s)
  if s:out.add(s)
 return out
def resistance_caps(record,level=1):
 """Maximum-resistance bonuses are additive percentage points, not multipliers."""
 return collections.Counter({f:at(record.get(f+'MaxResist'),level)+at(record.get('defensiveAllMaxResist'),level) for f in RES})
class Engine:
 def __init__(self,directory=ROOT):
  d=pathlib.Path(directory);self.d=d;self.db=read(d/'database.json.gz');self.cat=read(d/'catalog.json');self.mal=read(d/'mal.json');self.exported=read(d/'baseline.json');self.pen=read(d/'penalties.json');self.loc=read(d/'localization.json');self.items={x['id']:x for x in self.cat};self.recipes={}
  self.character_name=self.mal.get('character-name','Mal');self.cache={};self.evaluations=0;self.seen={};self.stage='baseline';self.issues=[]
  for b in read(d/'recipes.json'):
   r=b.get('definition') or {};p=r.get('artifactName')
   if p:self.recipes[p]=r
  # Default recipes have no blueprint gate. They are the basic blacksmith menu.
  for p,r in self.db.items():
   if '/crafting/' in p and r.get('Class')=='ItemArtifactFormula' and r.get('defaultRecipe'):
    self.recipes.setdefault(r.get('artifactName'),r)
  self.available=collections.Counter({m['record']:m['quantity'] for m in read(d/'materials.json') if m['file']=='reagents.gst'})
  for x in self.cat:
   if x['records'][0].get('Class')=='ItemRelic':self.available[x['save']['basename']]+=x['save'].get('stack-count',1)
  self.const=[];self.star_to_const={}
  for p,r in self.db.items():
   if r.get('constellationDisplayTag'):
    stars=[]
    for i in range(1,20):
     ui=self.db.get(r.get(f'devotionButton{i}'),{})
     if ui.get('skillName'):stars.append(ui['skillName'])
    if stars:
     c={'name':r['constellationDisplayTag'],'path':p,'record':r,'stars':stars};self.const.append(c)
     for i,s in enumerate(stars):self.star_to_const[s]=(c,i)
  self.factions=[];self.rep={}
  fixed={0:'Player',1:"Devil's Crossing",2:'Aetherials',3:'Chthonians',4:"Cronley's Gang",5:'Beasts'}
  for i,x in enumerate(self.mal['faction-values']):
   key='Survivors' if i==1 else ('User'+str(i-6) if i>=6 else '')
   n=fixed.get(i,self.loc.get('tagFactionUser'+str(i-6),'Unknown '+str(i)));v=x['faction-value'];self.rep[key]=v
   self.factions.append({'index':i,'key':key,'name':n,'reputation':v,'rank':self.rank(v)})
  self.vendor={}
  tiers={'friendly':1500,'respected':5000,'honored':10000,'revered':25000}
  for p,r in self.db.items():
   if '/factiontables/' not in p:continue
   tier=next((t for t in tiers if t in p),None)
   if not tier:continue
   for item in r.get('marketStaticItems',[]):
    self.vendor.setdefault(item,[]).append({'table':p,'required':tiers[tier],'tier':tier})
  self.augments=[];self.components=[]
  for p,r in self.db.items():
   if r.get('Class')=='ItemEnchantment':
    src=r.get('factionSource');entries=self.vendor.get(p,[]);eligible=[e for e in entries if self.rep.get(src,-1)>=e['required']]
    if r.get('levelRequirement',0)<=self.mal['character-level'] and eligible:self.augments.append(p)
   elif r.get('Class')=='ItemRelic' and (p in self.available or p in self.recipes):
    self.components.append(p)
  self.current=self.current_state();self.skillbudget=sum(s['level'] for s in self.mal['skills'] if '/playerclass' in s['skill-name'])+self.mal['skill-points']
  self.skillpaths=[s['skill-name'] for s in self.mal['skills'] if '/playerclass' in s['skill-name'] and not '_classtraining' in s['skill-name']]
  self.devbudget=self.mal['total-devotion-points-unlocked']
  self.allocated_attributes=[round((self.mal[k]-50)/8) for k in ['physique','cunning','spirit']]
  self.attribute_total=sum(self.allocated_attributes)+self.mal['attribute-points']
  self.reset_tonics=[x['id'] for x in self.cat if x['records'][0].get('Class')=='ItemAttributeReset' and x['owner'] in [self.character_name,'Shared Stash']]
  self.minimum_offense=Engine.calculate(self,self.current)['offense_proxy']*.85
  self.db['']={};self.items['EMPTY']={'id':'EMPTY','save':{'basename':''},'records':[{}],'worn-rolled':{},'rolled':{},'completion':{}}
 @staticmethod
 def rank(v):return 'Revered' if v>=25000 else 'Honored' if v>=10000 else 'Respected' if v>=5000 else 'Friendly' if v>=1500 else 'Tolerated' if v>=0 else 'Hostile'
 def name(self,p,seen=None):
  if not p:return ''
  seen=set() if seen is None else seen
  if p in seen:return p
  seen.add(p);r=self.db.get(p,{})
  for k in ['skillDisplayName','description','itemNameTag','constellationDisplayTag']:
   if r.get(k):return clean(r[k])
  for k in ['buffSkillName','petSkillName']:
   if r.get(k):return self.name(r[k],seen)
  return clean(r.get('FileDescription') or p)
 def current_state(self):
  st={'gear':['']*14,'comp':['']*14,'aug':['']*14,'skills':{},'devotions':{},'attributes':[0,0,0],'bindings':{}}
  for x in self.cat:
   if x['owner']!=self.character_name:continue
   loc=x['location']
   if loc.startswith('/equipment/'):i=int(loc.split('/')[2])
   elif loc.startswith('/weapon-sets/0/'):i=12+int(loc.split('/')[-1])
   else:continue
   st['gear'][i]=x['id'];st['comp'][i]=x['save'].get('relic-name','');st['aug'][i]=x['save'].get('augment-name','')
  for s in self.mal['skills']:
   p=s['skill-name']
   if '/playerclass' in p and s['level']>0:st['skills'][p]=s['level']
   if '/devotion/' in p and s['level']>0 and s['enabled']:st['devotions'][p]=s['devotion-level']
   if s.get('autocast-skill-name'):st['bindings'][p]=s['autocast-skill-name']
  return st
 def numeric(self,r,level=1,positive=False):
  out={}
  for k,v in r.items():
   if k.startswith(('character','defensive','offensive','skill','pet')):
    n=at(v,level)
    if n and (not positive or n>0):out[k]=n
  return out
 def item_records(self,ident,comp,aug):
  """Intrinsic sources plus live attachments, each once; never saved attachments."""
  saved=self.items[ident]['save'];base=self.db.get(saved.get('basename'),{})
  keys=['basename','prefix-name','suffix-name','modifier-name','relic-bonus','ascended-name']
  paths=[saved.get(k) for k in keys if not (k=='modifier-name' and base.get('Class')=='ItemArtifact')]
  records=[self.db[p] for p in paths+[comp,aug] if p and p in self.db]
  rolled=self.items[ident].get('worn-rolled') or self.items[ident].get('rolled') or {}
  seeded={saved.get(k) for k in ['basename','prefix-name','suffix-name','modifier-name']
          if not (k=='modifier-name' and base.get('Class')=='ItemArtifact')}
  # A single intrinsic mapping can use its actual seeded percentage. An
  # aggregate roll with several mappings cannot safely be allocated to sources.
  out=[]
  for p in paths+[comp,aug]:
   if not p or p not in self.db:continue
   r=self.db[p]
   if p in seeded:
    for suffix in ['', '2','3','4','5','6']:
     field='conversionPercentage'+suffix
     if r.get('conversionInType'+suffix) and field in rolled and sum(bool(q.get('conversionInType'+suffix)) for q in records)==1:
      r=dict(r);r[field]=rolled[field]
   out.append(r)
  return out
 def item_parts(self,ident,comp,aug):
  key=(ident,comp,aug)
  if key in self.cache:return self.cache[key]
  x=self.items[ident];s=x['save'];base=self.db[s['basename']];records=self.item_records(ident,comp,aug)
  # The seeded roller covers base/prefix/suffix/modifier, not ascended affixes.
  attach=[self.db.get(p,{}) for p in [comp,aug,s.get('ascended-name','')] if p]
  vals=collections.Counter(x.get('worn-rolled') or x.get('rolled') or {})
  vals.update(x.get('completion') or {})
  for r in attach:vals.update(self.numeric(r))
  # Item-granted persistent skills, once per granting item/component.
  granted=[]
  for r in records:
   sr=self.db.get(r.get('itemSkillName'),{})
   if sr.get('Class') in ['Skill_Passive','Skill_BuffSelfToggled','Skill_BuffAttackRadiusToggled','Skill_BuffRadiusToggled']:
    level=r.get('itemSkillLevel',1);vals.update(self.numeric(sr,level));granted.append((sr,level))
  bonus={'all':0,'skill':collections.Counter(),'mastery':collections.Counter()}
  for r in records:
   bonus['all']+=at(r.get('augmentAllLevel'))
   for i in range(1,6):
    if r.get('augmentSkillName'+str(i)):bonus['skill'][r['augmentSkillName'+str(i)]]+=at(r.get('augmentSkillLevel'+str(i)))
   for i in range(1,4):
    if r.get('augmentMasteryName'+str(i)):bonus['mastery'][r['augmentMasteryName'+str(i)]]+=at(r.get('augmentMasteryLevel'+str(i)))
  mods=collections.defaultdict(collections.Counter)
  for r in records:
   for i in range(1,6):
    target=r.get('modifiedSkillName'+str(i));mr=self.db.get(r.get('modifierSkillName'+str(i)),{})
    if target:mods[target].update(self.numeric(mr))
  cap=collections.Counter()
  for r in records:cap.update(resistance_caps(r))
  for r,level in granted:cap.update(resistance_caps(r,level))
  ans=(vals,bonus,mods,cap);self.cache[key]=ans;return ans
 def effective(self,p,l,b):
  if l<=0:return 0
  mastery=re.search(r'playerclass\d+',p)
  v=l+b['all']+b['skill'].get(p,0)+sum(n for q,n in b['mastery'].items() if mastery and mastery[0] in q)
  if '_classtraining' in p:return l
  cap=self.db.get(p,{}).get('skillUltimateLevel',0)
  return int(min(v,cap) if cap else v)
 def calculate(self,st):
  self.evaluations+=1;t=collections.Counter();bon={'all':0,'skill':collections.Counter(),'mastery':collections.Counter()};mods=collections.defaultdict(collections.Counter);caps=collections.Counter();sets=collections.defaultdict(set)
  for i,ident in enumerate(st['gear']):
   if not ident:continue
   v,b,mo,ca=self.item_parts(ident,st['comp'][i],st['aug'][i]);t.update(v);bon['all']+=b['all'];bon['skill'].update(b['skill']);bon['mastery'].update(b['mastery']);caps.update(ca)
   for p,vals in mo.items():mods[p].update(vals)
   base=self.items[ident]['records'][0]
   if base.get('itemSetName'):sets[base['itemSetName']].add(self.items[ident]['save']['basename'])
  for p,bases in sets.items():
   r=self.db.get(p,{});cnt=len(bases);t.update(self.numeric(r,cnt));caps.update(resistance_caps(r,cnt))
   bon['all']+=at(r.get('augmentAllLevel'),cnt)
   for j in range(1,6):
    if r.get('augmentSkillName'+str(j)):bon['skill'][r['augmentSkillName'+str(j)]]+=at(r.get('augmentSkillLevel'+str(j)),cnt)
  active={s['skill-name'] for s in self.mal['skills'] if s.get('skill-active')}
  active|={p for p,l in st['skills'].items() if self.db.get(p,{}).get('Class') in ['Skill_BuffSelfToggled','Skill_BuffRadiusToggled']}
  running=set().union(*(family(p,self.db.get(p,{})) for p in active))
  eff={p:self.effective(p,l,bon) for p,l in st['skills'].items()}
  for p,l in st['skills'].items():
   if l<=0:continue
   r=self.db.get(p,{});cl=r.get('Class');e=eff[p]
   if cl in ['Skill_Mastery','Skill_Passive']:
    t.update(self.numeric(r,l if cl=='Skill_Mastery' else e));caps.update(resistance_caps(r,l if cl=='Skill_Mastery' else e))
   if cl=='Skill_Modifier' and family(p,r)&running:t.update(self.numeric(r,e,True))
   if p in active:
    t.update(self.numeric(r,e));br=self.db.get(r.get('buffSkillName'),{})
    if 'Debuf' not in br.get('Class',''):t.update(self.numeric(br,e))
    for rr in [r,br]:caps.update(resistance_caps(rr,e))
  for p,l in st['devotions'].items():
   r=self.db.get(p,{})
   if r.get('Class')=='Skill_Passive':
    t.update(self.numeric(r,1))
    caps.update(resistance_caps(r))
  phys=modified(self.mal['physique']+st['attributes'][0]*8+t['characterStrength'],t['characterStrengthModifier'])
  cun=modified(self.mal['cunning']+st['attributes'][1]*8+t['characterDexterity'],t['characterDexterityModifier'])
  spi=modified(self.mal['spirit']+st['attributes'][2]*8+t['characterIntelligence'],t['characterIntelligenceModifier'])
  hp=int(modified(250+(phys-50)*2.5+(cun-50)+(spi-50)*1.5+t['characterLife'],t['characterLifeModifier']))
  energy=int((250+2*(spi-50)+t['characterMana'])*f32(1+f32(t['characterManaModifier']/100)))
  oa=int(f32(modified(65+t['characterOffensiveAbility']+self.mal['character-level']*12+cun*.5,t['characterOffensiveAbilityModifier'])+53))
  da=int(f32(modified(65+t['characterDefensiveAbility']+self.mal['character-level']*12+phys*.5,t['characterDefensiveAbilityModifier'])+53))
  native=sum((self.items[st['gear'][i]].get('worn-rolled') or {}).get('defensiveProtection',0) for i in ARMOR)
  shared=t['defensiveProtection']-native
  def bp(i):return sum(at(self.db.get(p,{}).get('defensiveBonusProtection')) for p in [st['comp'][i],st['aug'][i]])
  shared+=sum(bp(i) for i in range(14) if i not in ARMOR)
  slots={label:modified((self.items[st['gear'][i]].get('worn-rolled') or {}).get('defensiveProtection',0)+shared+bp(i),t['defensiveProtectionModifier']) for i,(label,w) in ARMOR.items()}
  armor=int(sum(slots[label]*w/100 for label,w in ARMOR.values()))
  res=[]
  for f,n in zip(RES,RN):
   total=t[f]+(t['defensiveElementalResistance'] if f in RES[:3] else 0)+self.pen[f];cap=min(95,80+caps[f]) if f in RES[:9] else 80+caps[f]
   res.append({'name':n,'raw':total,'cap':cap,'shown':math.floor(min(cap,total)+.5),'overcap':total-cap})
  absorption=min(100,70*(1+t['defensiveAbsorptionModifier']/100))
  # Spell damage receives Spirit's magical-damage bonus. This 0.47 coefficient is
  # an explicit model assumption, not part of the baseline exported stat set.
  chance=at(self.db[SC].get('offensiveLightningModifierChance'),eff.get(SC,0))/100
  conditional=at(self.db[SC].get('offensiveLightningModifier'),eff.get(SC,0)) if eff.get(SC,0) else 0
  lightning=t['offensiveLightningModifier']-conditional*(1-chance)+t['offensiveElementalModifier']+t['offensiveTotalDamageModifier']+spi*100/215
  electrocute=t['offensiveSlowLightningModifier']+t['offensiveTotalDamageModifier']+spi*.5
  cdr=min(80,t['skillCooldownReduction']);se=eff.get(STORM,0);we=eff.get(WIND,0);me=eff.get(MAEL,0);rage_rank=eff.get(RAGE,0)
  m=mods[STORM];sr=self.db[STORM];count=sr.get('petLimit',3)+m['petLimit'];burst=sr.get('petBurstSpawn',1)+m['petBurstSpawn'];cd=max(.2,(sr.get('skillCooldownTime',4.5)+m['skillCooldownTime'])*(1-cdr/100));duration=sr.get('spawnObjectsTimeToLive',14)+m['spawnObjectsTimeToLive'];active_totems=min(count,duration/cd*burst)
  attack=self.db['records/skills/playerclass06/pets/petskill_totemstorm_chainlightning.dbr'];av=(at(attack.get('offensiveLightningMin'),se)+at(attack.get('offensiveLightningMax'),se))/2
  # Follow explicit item skill modifiers of spawned pets as well as their caster.
  petmods=collections.Counter()
  for target,v in mods.items():
   if 'totem' in target and target!=STORM:petmods.update(v)
  av+=petmods['offensiveLightningMin']
  ramp=0.
  if not getattr(self,'equipment_only',False):
   window=6.;ramp=0.;placed=0.;last=0.
   for k in range(int(window/cd)+1):
    tm=k*cd;ramp+=placed*(tm-last);placed=min(count,placed+burst);last=tm
   ramp+=placed*(window-last);ramp/=window
  practical_totems=(active_totems+ramp)/2
  storm_packet=practical_totems*av*(1+lightning/100)
  mr=self.db['records/skills/playerclass06/pets/petskill_whirlwind_stormcaller1.dbr'];mael_packet=3*(at(mr.get('offensiveLightningMin'),me)+at(mr.get('offensiveLightningMax'),me))/2*(1+lightning/100) if me else 0
  rr=-at(self.db['records/skills/playerclass06/pets/petskill_whirlwind_exposure.dbr'].get('defensiveElementalResistance'),rage_rank) if rage_rank else 0
  # RR effects are deliberately separated by stacking category. Proc uptime is
  # scenario-bound, not inferred as guaranteed from an assigned skill alone.
  widow=0;ultos=0;flat=0
  for p,l in st['devotions'].items():
   rrrec=self.db.get(p,{})
   if 'Arcane Bomb' in self.name(p) or 'Hand of Ultos' in self.name(p):
    todo=[rrrec];seen=set()
    while todo:
     q=todo.pop();qp=q.get('recordname','')
     if qp in seen:continue
     seen.add(qp)
     widow=max(widow,-at(q.get('defensiveLightning'),max(1,l)))
     ultos=max(ultos,at(q.get('offensiveElementalResistanceReductionPercentMin'),max(1,l)))
     flat=max(flat,at(q.get('offensiveTotalResistanceReductionAbsoluteMin'),max(1,l)))
     for k,v in q.items():
      if k in ['skillBlackList','skillTemplates']:continue
      if k=='spawnObjects' and isinstance(v,list):
       pp=v[max(0,min(len(v)-1,int(l)-1))];todo.append(self.db.get(pp,{}))
      elif isinstance(v,str) and v in self.db and (k in ['attackSkillName','buffSkillName','debufSkillName','projectileName'] or re.fullmatch('skillName[0-9]+',k)):todo.append(self.db[v])
  def factor(enemy,up):
   # Tested order: additive -% RR, strongest relative % reduced, strongest
   # flat reduced. Relative reduction makes an already-negative value lower.
   er=enemy-rr-widow*up
   er*=1-ultos/100*up if er>=0 else 1+ultos/100*up
   er-=flat*up
   return max(.01,1-er/100)
  packet=storm_packet+.5*mael_packet
  absorb=0;mirror_cd=0;mirror_duration=0;defense=0;proxy=0
  if not getattr(self,'equipment_only',False):
   enemy_da=2200;pth=(((oa/(enemy_da/3.5+oa))*300)*.3)+((((oa*3.25+10000-enemy_da*3.25)/100)*.7))-50
   crit_chance=max(0,min(.35,(pth-90)/100));crit_factor=min(1,pth/100)*(1+crit_chance*(.1+t['offensiveCritDamageModifier']/100))
   proxy=packet*factor(40,.6)*crit_factor
   sphere=self.db.get(self.db[SPHERE].get('buffSkillName'),self.db[SPHERE]);absorb=at(sphere.get('damageAbsorptionPercent'),eff.get(SPHERE,0)) if eff.get(SPHERE,0) else 0
   # Fixed encounter envelope, not an all-enemy EHP claim.
   pr=max(0,res[-1]['shown']);mitigated=max(1,3000*(1-pr/100)-armor*absorption/100)
   recovery=t['characterLifeRegen']*(1+t['characterLifeRegenModifier']/100)
   defense=(hp+5*max(0,recovery))/(.8*.2+.2*mitigated/3000)/(1-absorb/100)*max(.7,min(1.3,da/2000))
   mirror='records/skills/playerclass05/arcaneshield.dbr';mirr=self.db[mirror];mirrank=eff.get(mirror,0)
   mirror_cd=max(.1,(at(mirr.get('skillCooldownTime'),mirrank)+mods[mirror]['skillCooldownTime'])*(1-cdr/100)) if mirrank else 0
   mirror_duration=at(mirr.get('skillActiveDuration'),mirrank) if mirrank else 0
   # Emergency skill: only one quarter of theoretical duty cycle is credited.
   if mirrank:defense/=1-min(.2,.25*mirror_duration/mirror_cd)
  regen_lower=(1+t['characterManaRegen'])*(1+t['characterManaRegenModifier']/100)
  totem_mana=at(sr.get('skillManaCost'),se)*(1-min(100,t['skillManaCostReduction'])/100)
  upkeep=totem_mana*count/max(1,burst)/duration
  if WIND in eff:upkeep+=at(self.db[WIND].get('skillManaCost'),eff[WIND])/30
  out={'physique':int(phys),'cunning':int(cun),'spirit':int(spi),'health':hp,'energy':energy,'energy_reserved':int(t['characterManaLimitReserve']-t['characterManaLimitReserveReduction']),'OA':oa,'DA':da,'armor':armor,'armor_slots':{k:math.floor(v+.5) for k,v in slots.items()},'armor_absorption':absorption,'damage_absorption_percent':absorb,'resistances':res,'cooldown_reduction':cdr,'lightning_modifier':lightning,'lightning_gear_skill_modifier':lightning-spi*100/215,'effective_skills':eff,'invested_skills':st['skills'],'totem_count':count,'totems_per_cast':burst,'totem_cooldown':cd,'totem_duration':duration,'steady_totems':active_totems,'ramp_totems_6sec':ramp,'storm_packet':storm_packet,'maelstrom_packet':mael_packet,'offense_proxy':proxy,'offense_low':packet*factor(80,0),'offense_high':packet*factor(0,1),'defense_proxy':defense,'raging_tempest_RR':rr,'widow_RR':widow,'ultos_relative_RR':ultos,'energy_regen_flat':t['characterManaRegen'],'energy_regen_percent':t['characterManaRegenModifier'],'stats':dict(t),'bonuses':{'all':bon['all'],'skill':dict(bon['skill']),'mastery':dict(bon['mastery'])}}
  out.update({'mirror_cooldown':mirror_cd,'mirror_duration':mirror_duration,'energy_regen_lower_bound':regen_lower,'totem_wind_energy_upkeep_estimate':upkeep,'energy_margin_lower_bound':regen_lower-upkeep})
  return out
 def validate(self):
  v=Engine.calculate(self,self.current);e=self.exported;rows=[]
  def add(n,a,b,status='Reproduced export'):rows.append({'stat':n,'exported':a,'calculated':b,'difference':None if a is None or b is None else round(b-a,5),'status':status if a is not None else 'Not in export; no independent validation'})
  for a,b in [('physique','physique'),('cunning','cunning'),('spirit','spirit'),('health','health')]:add(a,e['attributes'][a],v[b])
  add('energy',e['attributes']['energy']['max'],v['energy']);add('OA',e['combat']['offensiveAbility'],v['OA']);add('DA',e['combat']['defensiveAbility'],v['DA']);add('armor',e['combat']['armour']['rating'],v['armor'])
  for k,z in e['combat']['armour']['bySlot'].items():add('armor '+k,z,v['armor_slots'][k])
  for rr,ex in zip(v['resistances'],e['resistances']):
   add(rr['name']+' resistance shown',ex['shown'],rr['shown']);add(rr['name']+' before cap',ex['beforeCap'],rr['raw'])
  for n in ['armor_absorption','lightning_modifier','cooldown_reduction','offense_proxy']:add(n,None,v[n])
  self.validation=rows;return rows
 def compatible(self,p,i,ident):
  if not p:return True
  r=self.db.get(p,{});base=self.items[ident]['records'][0];key=SLOTKEY[i]
  if i==12:key=base.get('Class','').split('_')[-1].lower()
  if i==13:key='shield' if base.get('Class')=='WeaponArmor_Shield' else 'offhand'
  return bool(key and r.get(key)) and r.get('levelRequirement',0)<=self.mal['character-level']
 def resources(self,st):
  avail=self.available.copy();iron=0;crafted=collections.Counter();need=collections.Counter();errors=[]
  # Reuse an attachment only when it remains on that same item. Replacements
  # destroy it; no free component salvaging is assumed.
  for i,p in enumerate(st['comp']):
   if p and p!=self.items[st['gear'][i]]['save'].get('relic-name'):need[p]+=1
  def acquire(p,q,depth=0):
   nonlocal iron
   use=min(q,avail[p]);avail[p]-=use;q-=use
   if q<=0:return
   r=self.recipes.get(p)
   if not r or depth>8:errors.append(f'{self.name(p)}: short {q}');return
   qty=max(1,r.get('artifactCreateQuantity',1));batches=math.ceil(q/qty);crafted[p]+=batches;avail[p]+=batches*qty-q
   try:iron+=batches*float(r.get('artifactCreationCost',0))
   except (TypeError,ValueError):errors.append('Unresolved craft cost: '+p)
   for k,v in r.items():
    if k.startswith('reagent') and k.endswith('BaseName'):
     qkey=k[:-8]+'Quantity';acquire(v,batches*r.get(qkey,1),depth+1)
  for p,q in need.items():acquire(p,q)
  augcost=0;buys=collections.Counter()
  for i,p in enumerate(st['aug']):
   if p and (p!=self.items[st['gear'][i]]['save'].get('augment-name') or self.items[st['gear'][i]]['owner'] not in [self.character_name,'Shared Stash']):
    if p not in self.augments:errors.append('Augment not purchasable: '+self.name(p))
    buys[p]+=1;augcost+=self.db[p].get('itemCost',0)
  if iron+augcost>self.mal['iron']:errors.append('Iron requirement exceeds current balance')
  return {'errors':errors,'component_need':dict(need),'crafted_batches':dict(crafted),'augment_purchases':dict(buys),'craft_iron_base':iron,'augment_iron_base':augcost,'remaining_iron_base':self.mal['iron']-iron-augcost}
 def devotion_valid(self,dev):
  total=collections.Counter();selected=set(dev);partial=[]
  for c in self.const:
   chosen=selected&set(c['stars']);r=c['record']
   if not chosen:continue
   if len(chosen)==len(c['stars']):
    for i in range(1,4):
     if r.get('affinityGivenName'+str(i)):total[r['affinityGivenName'+str(i)]]+=r.get('affinityGiven'+str(i),0)
   partial.append(c)
  errs=[]
  for c in partial:
   r=c['record']
   for i in range(1,4):
    f=r.get('affinityRequiredName'+str(i));req=r.get('affinityRequired'+str(i),0)
    if f and total[f]<req:errs.append(f"{c['name']}: {f} {total[f]} < {req}")
   for j,p in enumerate(c['stars'],1):
    if p not in selected:continue
    links=c['record'].get('devotionLinks'+str(j),[]);links=links if isinstance(links,list) else [links]
    if links and not any(isinstance(k,(int,float)) and k>0 and k<=len(c['stars']) and c['stars'][int(k)-1] in selected for k in links):errs.append(f"{c['name']}: disconnected star {j}")
  if len(selected)>self.devbudget:errs.append('Too many devotion points')
  return {'valid':not errs,'errors':errs,'affinities':dict(total),'spent':len(selected),'available':self.devbudget}
 def legal(self,st,v,full=False):
  errors=[];used=collections.Counter(st['gear'])
  if any(q>1 for p,q in used.items() if p):errors.append('Same physical item used twice')
  if st.get('respec_attributes'):
   if sum(st['attributes'])>self.mal['attribute-points'] or min(a+b for a,b in zip(self.allocated_attributes,st['attributes']))<0 or not self.reset_tonics:errors.append('Attribute budget')
  elif sum(st['attributes'])>self.mal['attribute-points'] or min(st['attributes'])<0:errors.append('Attribute budget')
  if sum(st['skills'].values())>self.skillbudget:errors.append('Skill budget')
  for p,l in st['skills'].items():
   r=self.db[p]
   if l<0 or l>r.get('skillMaxLevel',50):errors.append('Skill invested cap '+self.name(p))
  for i,ident in enumerate(st['gear']):
   x=self.items[ident];base=x['records'][0]
   if max((r or {}).get('levelRequirement',0) for r in x['records'][:4])>self.mal['character-level']:errors.append('Level '+ident)
   if not transferable(x,self.character_name):errors.append('Bound base '+ident)
   for typ in ['comp','aug']:
    if not self.compatible(st[typ][i],i,ident):errors.append(typ+' slot '+SLOTS[i])
   req=x.get('requirements') or {}
   for key,attr in [('strength','physique'),('dexterity','cunning'),('intelligence','spirit')]:
    reduction=v['stats'].get('characterGlobalReqReduction',0)
    if v[attr]+1e-5<req.get(key,0)*(1-reduction/100):errors.append(ident+' '+attr+' requirement')
  de=self.devotion_valid(st['devotions']);errors+=de['errors']
  if full:errors+=self.resources(st)['errors']
  return list(dict.fromkeys(errors))
 def quickscore(self,st,v,mode):
  deficit=sum(max(0,r['cap']-r['raw'])**2 for r in v['resistances'][:9]);da_short=max(0,1900-v['DA']);hp_short=max(0,9500-v['health']);abs_short=max(0,84-v['armor_absorption']);off_short=max(0,self.minimum_offense-v['offense_proxy'])
  if self.legal(st,v):return -1e10
  # All retained candidates eventually face the same hard gates. The penalty
  # only guides traversal through infeasible intermediate configurations.
  off=math.log(max(1,v['offense_proxy']));defe=math.log(max(1,v['defense_proxy']));weight={'balanced':.5,'offense':.9,'defense':.1}[mode]
  overcap=sum(min(20,max(0,r['overcap'])) for r in v['resistances'][:9])*.0002
  return weight*off+(1-weight)*defe+overcap-(1000 if deficit or da_short or hp_short or abs_short or off_short else 0)-deficit*.003-da_short*.003-hp_short*.0005-abs_short*.05-off_short*.0001
 def feasible(self,st,v):return not self.legal(st,v,True) and all(r['raw']>=r['cap'] for r in v['resistances'][:9]) and v['DA']>=1900 and v['health']>=9500 and v['armor_absorption']>=84 and v['offense_proxy']>=self.minimum_offense
 def options(self):
  options=[[] for _ in SLOTS]
  classes={'ArmorProtective_Head':0,'ArmorJewelry_Amulet':1,'ArmorProtective_Chest':2,'ArmorProtective_Legs':3,'ArmorProtective_Feet':4,'ArmorProtective_Hands':5,'ArmorJewelry_Ring':6,'ArmorProtective_Waist':8,'ArmorProtective_Shoulders':9,'ArmorJewelry_Medal':10,'ItemArtifact':11,'WeaponArmor_Offhand':13,'WeaponArmor_Shield':13}
  for x in self.cat:
   r=x['records'][0];cl=r.get('Class','');i=classes.get(cl)
   if cl.startswith('WeaponMelee_') and not cl.endswith('2h'):i=12
   if i is None:continue
   if max((z or {}).get('levelRequirement',0) for z in x['records'][:4])>self.mal['character-level']:continue
   if not transferable(x,self.character_name):continue
   # Soulbound attachments on borrowed items must be removed, so only the
   # unbound item is brought into the attachment search.
   options[i].append(x['id'])
   if i==6:options[7].append(x['id'])
  return options
 def initial(self,mode):
  s=copy.deepcopy(self.current);s['attributes']=[self.mal['attribute-points'],0,0]
  # Begin with actual saved skills; every respec below preserves the existing
  # dependency chain and mastery bars. No mastery may be changed.
  free=self.skillbudget-sum(s['skills'].values())
  for p in [SC,INNER,SPHERE]:
   give=min(free,max(0,self.db[p].get('skillMaxLevel',12)-s['skills'].get(p,0)));s['skills'][p]=s['skills'].get(p,0)+give;free-=give
  return s
 def devotion_seeds(self):
  out={'current':copy.deepcopy(self.current['devotions'])}
  d=copy.deepcopy(out['current'])
  for c in self.const:
   if c['name']=='Ghoul':
    for p in c['stars']:d.pop(p,None)
   if c['name'] in ['Behemoth',"Sailor's Guide"]:
    for p in c['stars']:d[p]=d.get(p,1)
  if self.devotion_valid(d)['valid']:out['sailor_behemoth']=d
  g=read(self.d/'guide70.json')['data'];d={s['name']:self.current['devotions'].get(s['name'],1) for s in g['skills'] if '/devotion/' in s['name'] and s['level']>0}
  for c in self.const:
   if c['name']=='Tree of Life':
    for p in c['stars']:d.pop(p,None)
  if self.devotion_valid(d)['valid']:out['guide_51']=d
  return out
 def signature(self,s):return json.dumps(s,sort_keys=True,separators=(',',':'))
 def equip_order_possible(self,s):
  now=copy.deepcopy(self.current);now['attributes']=s['attributes'];now['skills']=s['skills'];now['devotions']=s['devotions'];left=[i for i in range(14) if now['gear'][i]!=s['gear'][i]]
  while left:
   changed=False
   for i in left[:]:
    q=copy.deepcopy(now);q['gear'][i]='EMPTY';q['comp'][i]='';q['aug'][i]='';v=self.calculate(q);req=self.items[s['gear'][i]].get('requirements') or {};red=v['stats'].get('characterGlobalReqReduction',0)
    if 'error' in req:continue
    if all(v[a]>=req.get(k,0)*(1-red/100) for k,a in [('strength','physique'),('dexterity','cunning'),('intelligence','spirit')]):
     for key in ['gear','comp','aug']:now[key][i]=s[key][i]
     left.remove(i);changed=True
   if not changed:return False
  return True
 def search(self,rounds=4,seed=74051):
  rng=random.Random(seed);opts=self.options();allfinal=[];self.logs=[]
  # Search all eligible gear (no hand-picked item list); shortlist attachments
  # only by legal slot and actual inventory/crafting/purchase availability.
  devseeds=self.devotion_seeds()
  for mode,devlabel in [(m,d) for m in ['balanced','offense','defense'] for d in devseeds]:
   s=self.initial(mode);s['devotions']=copy.deepcopy(devseeds[devlabel]);v=self.calculate(s);sc=self.quickscore(s,v,mode)
   compopts=[];augopts=[]
   for i in range(14):
    compopts.append(['']+[p for p in self.components if self.compatible(p,i,s['gear'][i])])
    augopts.append(['']+[p for p in self.augments if self.compatible(p,i,s['gear'][i])])
   for rd in range(rounds):
    changed=0
    for i in list(range(14)):
     trials=[]
     for ident in opts[i]:
      q=copy.deepcopy(s);q['gear'][i]=ident;x=self.items[ident]
      # Start with the current compatible attachment or the item's own one.
      for typ,key in [('comp','relic-name'),('aug','augment-name')]:
       p=q[typ][i]
       if not self.compatible(p,i,ident):p=''
       q[typ][i]=p
      z=self.calculate(q);trials.append((self.quickscore(q,z,mode),q,z))
     # Joint item+component+augment moves around the best few native choices.
     trials.sort(key=lambda x:x[0],reverse=True)
     top=trials[:3]+[(sc,s,v)]
     for _,base,_ in top:
      ident=base['gear'][i];components=['']+[p for p in self.components if self.compatible(p,i,ident)]
      components=list(dict.fromkeys(components+[self.items[ident]['save'].get('relic-name','')]))
      # Component resource feasibility is tested before comparing; otherwise a
      # missing rare component could trap the search at an imaginary maximum.
      bestcomp=[]
      for p in components:
       q=copy.deepcopy(base);q['comp'][i]=p
       if self.resources(q)['errors']:continue
       z=self.calculate(q);bestcomp.append((self.quickscore(q,z,mode),q,z))
      bestcomp.sort(key=lambda x:x[0],reverse=True)
      for _,q,z in bestcomp[:3]:
       trials.append((self.quickscore(q,z,mode),q,z))
       for a in ['']+[p for p in self.augments if self.compatible(p,i,ident)]:
        qq=copy.deepcopy(q);qq['aug'][i]=a
        if self.resources(qq)['errors']:continue
        zz=self.calculate(qq);trials.append((self.quickscore(qq,zz,mode),qq,zz))
     trials.sort(key=lambda x:x[0],reverse=True)
     for score,q,z in trials:
      if score>sc+1e-8 and not self.resources(q)['errors']:
       s,v,sc=q,z,score;changed+=1;break
    # Skills are searched jointly with the full gear/attachment configuration.
    for _ in range(12):
     best=(sc,None,None)
     for p in self.skillpaths:
      minimum=1 # keep prerequisites; Panetti modifier ranks may go to zero
      if p in ['records/skills/playerclass05/arcanemissile2.dbr','records/skills/playerclass05/arcanemissile3.dbr']:minimum=0
      if s['skills'].get(p,0)<=minimum:continue
      for target in self.skillpaths:
       if target==p:continue
       if s['skills'].get(target,0)>=self.db[target].get('skillMaxLevel',50):continue
       q=copy.deepcopy(s);q['skills'][p]-=1;q['skills'][target]=q['skills'].get(target,0)+1;z=self.calculate(q);score=self.quickscore(q,z,mode)
       if score>best[0]+1e-8:best=(score,q,z)
     if best[1] is None:break
     sc,s,v=best;changed+=1
    # Exhaustively compare all ways to spend the currently unspent attributes.
    ap=self.mal['attribute-points'];best=(sc,None,None)
    for phys in range(ap+1):
     for cun in range(ap-phys+1):
      q=copy.deepcopy(s);q['attributes']=[phys,cun,ap-phys-cun];z=self.calculate(q);score=self.quickscore(q,z,mode)
      if score>best[0]+1e-8:best=(score,q,z)
    if best[1] is not None:sc,s,v=best;changed+=1
    # Explore legal additions using the two unspent devotion points.
    for _ in range(self.devbudget-len(s['devotions'])):
     best=(sc,None,None)
     for c in self.const:
      for p in c['stars']:
       if p in s['devotions']:continue
       q=copy.deepcopy(s);q['devotions'][p]=1
       if not self.devotion_valid(q['devotions'])['valid']:continue
       z=self.calculate(q);score=self.quickscore(q,z,mode)
       if score>best[0]+1e-8:best=(score,q,z)
     if best[1] is None:break
     sc,s,v=best;changed+=1
    if self.feasible(s,v):
     entry={'mode':mode,'round':rd,'state':copy.deepcopy(s),'stats':v,'resources':self.resources(s),'legality':self.legal(s,v,True)};allfinal.append(entry)
    self.logs.append({'mode':mode,'devotion_seed':devlabel,'round':rd+1,'score':sc,'health':v['health'],'DA':v['DA'],'min_resistance':min(r['shown'] for r in v['resistances'][:9]),'offense':v['offense_proxy'],'defense':v['defense_proxy'],'changed':changed,'evaluations':self.evaluations})
    print(self.logs[-1],flush=True)
    if not changed:break
   # Retain rejected endpoints too: an empty feasible set is a result, not
   # permission to label an infeasible arrangement as optimized.
   self.seen[mode+' '+devlabel]={'mode':mode,'devotion_seed':devlabel,'state':s,'stats':v,'resources':self.resources(s),'legality':self.legal(s,v,True),'feasible':self.feasible(s,v)}
  # Attribute requirements must be met before putting a replacement on, not
  # by counting that replacement's own bonuses. Repair any self-support cycle
  # with available attribute points, or reject it.
  supported=[]
  for ent in allfinal:
   # A full attribute reset is executable only with a real Tonic of Reshaping.
   # Compare all integer assignments of the actual earned attribute points.
   if self.reset_tonics:
    alternatives=[];budget=self.attribute_total
    for p in range(budget+1):
     for c in range(budget-p+1):
      st=copy.deepcopy(ent['state']);st['respec_attributes']=True;st['attributes']=[p-self.allocated_attributes[0],c-self.allocated_attributes[1],budget-p-c-self.allocated_attributes[2]];v=self.calculate(st)
      if self.feasible(st,v):alternatives.append((self.quickscore(st,v,ent['mode']),st,v))
    current_score=self.quickscore(ent['state'],ent['stats'],ent['mode'])
    for score,st,v in sorted(alternatives,key=lambda x:x[0],reverse=True):
     if score<=current_score+1e-8:break
     if self.equip_order_possible(st):ent=dict(ent,state=st,stats=v,attribute_requirement_repair=True,resources=self.resources(st),tonic=self.reset_tonics[0]);break
   if self.equip_order_possible(ent['state']):supported.append(ent);continue
   alternatives=[];ap=self.mal['attribute-points']
   for p in range(ap+1):
    for c in range(ap-p+1):
     st=copy.deepcopy(ent['state']);st['attributes']=[p,c,ap-p-c];v=self.calculate(st)
     if self.feasible(st,v):alternatives.append((self.quickscore(st,v,ent['mode']),st,v))
   for score,st,v in sorted(alternatives,key=lambda x:x[0],reverse=True):
    if self.equip_order_possible(st):
     supported.append(dict(ent,state=st,stats=v,attribute_requirement_repair=True,resources=self.resources(st)));break
  unique={self.signature(e['state']):e for e in supported};feasible=list(unique.values())
  frontier=[a for a in feasible if not any(b['stats']['offense_proxy']>=a['stats']['offense_proxy'] and b['stats']['defense_proxy']>=a['stats']['defense_proxy'] and (b['stats']['offense_proxy']>a['stats']['offense_proxy'] or b['stats']['defense_proxy']>a['stats']['defense_proxy']) for b in feasible)]
  chosen={}
  if frontier:
   chosen['offense']=max(frontier,key=lambda e:e['stats']['offense_proxy']);chosen['defense']=max(frontier,key=lambda e:e['stats']['defense_proxy']);mxo=max(e['stats']['offense_proxy'] for e in frontier);mxd=max(e['stats']['defense_proxy'] for e in frontier)
   chosen['balanced']=max(frontier,key=lambda e:(e['stats']['offense_proxy']/mxo*e['stats']['defense_proxy']/mxd)**.5)
  return {'seed':seed,'evaluations':self.evaluations,'logs':self.logs,'chosen':chosen,'frontier':frontier,'endpoints':self.seen,'search_scope':'Deterministic multi-objective coordinate search; joint native-item, component and augment moves. Best found, not global optimum proof.'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--data',type=pathlib.Path,default=ROOT);ap.add_argument('--out',type=pathlib.Path,default=ROOT/'results');ap.add_argument('--rounds',type=int,default=4);args=ap.parse_args();args.out.mkdir(exist_ok=True,parents=True)
 e=Engine(args.data);val=e.validate();(args.out/'validation.json').write_text(json.dumps(val,indent=2));bad=[r for r in val if r['difference'] is not None and abs(r['difference'])>1]
 print('BASELINE DISCREPANCIES',bad,flush=True)
 if bad:raise SystemExit('Baseline gate failed. Inspect validation.json before search.')
 result=e.search(args.rounds);result['baseline']=e.calculate(e.current);result['validation']=val;result['factions']=e.factions;result['devotion_baseline']=e.devotion_valid(e.current['devotions']);result['available_augments']=[{'path':p,'name':e.name(p),'faction':e.db[p].get('factionSource'),'required_level':e.db[p].get('levelRequirement'),'base_cost':e.db[p].get('itemCost'),'vendors':e.vendor[p]} for p in e.augments]
 (args.out/'results.json').write_text(json.dumps(result,indent=2));print('Feasible frontier',len(result['frontier']),'selected',list(result['chosen']),flush=True)
if __name__=='__main__':
 import sys
 if '--legacy' in sys.argv:
  sys.argv.remove('--legacy');main()
 else:
  from practical_optimizer import main as practical_main
  practical_main()
