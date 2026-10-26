"""Post-search checks and readable report tables. Does not alter user saves."""
import collections,copy,hashlib,json,pathlib,sys,math,re
from GrimDawn_Optimizer import Engine,ROOT,SLOTS,RES,RN,ARMOR,STORM,WIND,SC,SPHERE,INNER,RAGE,MAEL,read
def dump(p,o):p.write_text(json.dumps(o,indent=2,ensure_ascii=False))
def sequence(e,dev):
 target=set(dev);selected=set();steps=[];remaining=[]
 for c in e.const:
  part=set(c['stars'])&target
  if part:remaining.append((c,part))
 while remaining:
  progressed=False
  for c,part in list(remaining):
   cur=e.devotion_valid({p:dev.get(p,1) for p in selected});aff=cur['affinities'];r=c['record']
   if any(aff.get(r.get('affinityRequiredName'+str(i)),0)<r.get('affinityRequired'+str(i),0) for i in range(1,4)):continue
   if len(selected)+len(part-selected)>e.devbudget:continue
   seq=[];left=part.copy()
   while left:
    moved=False
    for j,p in enumerate(c['stars'],1):
     if p not in left:continue
     links=r.get('devotionLinks'+str(j),[]);links=links if isinstance(links,list) else [links]
     if not links or any(isinstance(k,(int,float)) and k>0 and c['stars'][int(k)-1] in selected for k in links):
      selected.add(p);left.remove(p);seq.append(j);moved=True
    if not moved:return {'verified':False,'steps':steps,'reason':'Unresolved node prerequisites'}
   steps.append({'constellation':c['name'],'stars_in_order':seq,'spent_after':len(selected)});remaining.remove((c,part));progressed=True
  if not progressed:
   # Temporary Crossroads are a documented respec construction tool. Keep the
   # maximum intermediate spent within Mal's earned point count.
   cross=[c for c in e.const if c['name']=='Crossroads' and not set(c['stars'])&selected]
   if cross and len(selected)<e.devbudget:
    c=cross[0];selected.update(c['stars']);steps.append({'constellation':'Temporary Crossroads','stars_in_order':c['stars'],'spent_after':len(selected)});continue
   return {'verified':False,'steps':steps,'reason':'No acquisition order proven within earned points'}
  # Remove unnecessary temporary points as soon as the target can self-support.
  for p in list(selected-target):
   q=selected-{p}
   if e.devotion_valid({a:dev.get(a,1) for a in q})['valid']:selected=q;steps.append({'remove_temporary':p,'spent_after':len(selected)})
  if len(selected)>e.devbudget:return {'verified':False,'steps':steps,'reason':'Intermediate devotion budget exceeded'}
 return {'verified':selected==target,'steps':steps,'reason':'' if selected==target else 'Temporary point retained'}
def bindings(e,s):
 procs=[p for p in s['devotions'] if e.db[p].get('templateAutoCast')];out=[];used=set()
 preferred={'Arcane Bomb':WIND,'Hand of Ultos':STORM,"Giant's Blood":SPHERE,'Turtle Shell':'records/skills/playerclass06/natureblessing1.dbr','Ghoulish Hunger':SC,'Eye of Korvaak':WIND}
 procs.sort(key=lambda p:0 if e.name(p)=='Eye of Korvaak' else 1)
 for p in procs:
  r=e.db[p];target=preferred.get(e.name(p));templates=r.get('skillTemplates',[]);allowed={e.db.get(t,{}).get('Class') for t in templates}
  def fits(q):return q in s['skills'] and s['skills'][q]>0 and q not in used and (not allowed or e.db[q].get('Class') in allowed)
  if not target or not fits(target):target=next((q for q in [WIND,STORM,'records/skills/playerclass05/arcanemissile.dbr',SPHERE,'records/skills/playerclass06/natureblessing1.dbr',SC] if fits(q)),None)
  if target:used.add(target)
  controller=e.db.get(r.get('templateAutoCast'),{})
  out.append({'power':e.name(p),'power_record':p,'bind_to':e.name(target) if target else 'UNRESOLVED','target_record':target,'valid_template':bool(target),'proc_level':s['devotions'][p],'trigger':controller.get('triggerType',''),'chance':controller.get('chanceToRun'),'cooldown':r.get('skillCooldownTime'),'controller':controller})
 return out
def equip_sequence(e,s):
 # A conservative swap proof excludes the item being taken off when testing
 # the replacement's attribute requirements. No self-support cycle is used.
 e.db['']={};e.items['EMPTY']={'id':'EMPTY','save':{'basename':''},'records':[{}],'worn-rolled':{},'rolled':{},'completion':{}}
 now=copy.deepcopy(e.current);now['attributes']=s['attributes'];now['skills']=s['skills'];now['devotions']=s['devotions'];steps=[];left=[i for i in range(14) if now['gear'][i]!=s['gear'][i]]
 while left:
  progressed=False
  for i in left[:]:
   q=copy.deepcopy(now);q['gear'][i]='EMPTY';q['comp'][i]='';q['aug'][i]='';v=e.calculate(q);r=e.items[s['gear'][i]].get('requirements') or {};reduction=v['stats'].get('characterGlobalReqReduction',0)
   if 'error' in r:continue
   if all(v[a]>=r.get(k,0)*(1-reduction/100) for k,a in [('strength','physique'),('dexterity','cunning'),('intelligence','spirit')]):
    for k in ['gear','comp','aug']:now[k][i]=s[k][i]
    steps.append({'slot':SLOTS[i],'item':s['gear'][i],'attributes_without_item':[v['physique'],v['cunning'],v['spirit']],'requirements':r});left.remove(i);progressed=True
  if not progressed:break
 return {'verified':not left,'steps':steps,'unresolved_slots':[SLOTS[i] for i in left]}
def skill_legality(e,s):
 errors=[];thresholds=[1,5,10,15,20,25,32,40,50]
 for p,l in s['skills'].items():
  if l<=0:continue
  r=e.db[p]
  if '_classtraining' in p:continue
  mastery=re.search('playerclass[0-9]+',p)[0];bar=next((v for k,v in s['skills'].items() if mastery in k and '_classtraining' in k),0);tier=int(r.get('skillTier',1))
  required=thresholds[max(0,min(len(thresholds)-1,tier-1))]
  if bar<required:errors.append(f'{e.name(p)} requires mastery {required}, have {bar}')
 # Existing chains are retained; only the two optional Panetti modifiers may
 # be refunded completely. Check their prerequisite explicitly.
 if s['skills'].get('records/skills/playerclass05/arcanemissile3.dbr',0)>0 and not s['skills'].get('records/skills/playerclass05/arcanemissile2.dbr',0):errors.append('Supercharged missing Distortion prerequisite')
 return errors
def vendors(e,p):
 tables={v['table'] for v in e.vendor.get(p,[]) if e.rep.get(e.db[p].get('factionSource'),-1)>=v['required']};markets={q for q,r in e.db.items() if 'factionmarket.tpl' in r.get('templateName','') and any(isinstance(v,str) and v in tables for v in r.values())}
 out=[]
 for q,r in e.db.items():
  market=r.get('marketFileName');market=market if isinstance(market,list) else [market]
  if any(p in markets for p in market):out.append(r.get('description') or q)
 return sorted(set(out))
def build():
 e=Engine();r=json.loads((ROOT/'results/results.json').read_text());tables={};baseline=r['baseline'];chosen=r['chosen'];audits={};loadouts={};purchases=[];skillrows=[];devrows=[];bindrows=[];summary=[];resrows=[]
 for key,label in [('balanced','A Balanced'),('offense','B Offense'),('defense','C Defense')]:
  x=chosen[key];s=x['state'];v=x['stats'];b=bindings(e,s);seq=equip_sequence(e,s);devseq=sequence(e,s['devotions']);sl=skill_legality(e,s)
  audit={'equipment_errors':e.legal(s,e.calculate(s),True),'equip_order':seq,'devotion_acquisition':devseq,'devotion_final':e.devotion_valid(s['devotions']),'skill_errors':sl,'bindings':b,'baseline_gate':all(z['difference']==0 for z in r['validation'] if z['difference'] is not None)}
  audit['legal_verified']=not audit['equipment_errors'] and seq['verified'] and devseq['verified'] and not sl and all(z['valid_template'] for z in b)
  audits[key]=audit;lr=[]
  for i,ident in enumerate(s['gear']):
   it=e.items[ident];ss=it['save'];loc=it['location'];borrow=it['owner'] not in ['Mal','Shared Stash'];actions=[]
   if borrow:actions.append('Transfer from '+it['owner'])
   if borrow and ss.get('augment-name'):actions.append('Remove donor augment before shared-stash transfer')
   if borrow and it['save'].get('transmute-name'):actions.append('Check/remove donor illusion binding before transfer')
   if ss.get('relic-name')!=s['comp'][i]:actions.append('Replace component; old component destroyed')
   if ss.get('augment-name')!=s['aug'][i] or borrow and s['aug'][i]:actions.append('Apply listed augment' if s['aug'][i] else 'Remove old augment')
   row={'slot':SLOTS[i],'id':ident,'item':it['name'],'owner':it['owner'],'location':loc,'component':e.name(s['comp'][i]) or 'None','component_record':s['comp'][i],'augment':e.name(s['aug'][i]) or 'None','augment_record':s['aug'][i],'requirements':it['requirements'],'actions':'; '.join(actions) or 'Keep attachments','changed_from_current':ident!=e.current['gear'][i] or s['comp'][i]!=e.current['comp'][i] or s['aug'][i]!=e.current['aug'][i]}
   lr.append(row)
  loadouts[key]=lr
  for p,q in x['resources']['augment_purchases'].items():
   faction=next((f for f in e.factions if f['key']==e.db[p].get('factionSource')),{});eligible=[z for z in e.vendor[p] if faction.get('reputation',-1)>=z['required']]
   purchases.append({'build':label,'augment':e.name(p),'quantity':q,'faction':faction.get('name'),'reputation':faction.get('reputation'),'required':min(z['required'] for z in eligible),'vendors':', '.join(vendors(e,p)),'base_unit_cost':e.db[p].get('itemCost'),'base_total':q*e.db[p].get('itemCost',0)})
  for p,l in s['skills'].items():
   skillrows.append({'build':label,'skill':e.name(p),'record':p,'baseline_invested':e.current['skills'].get(p,0),'invested':l,'effective':v['effective_skills'][p],'delta_invested':l-e.current['skills'].get(p,0),'softcap':e.db[p].get('skillMaxLevel'),'hardcap':e.db[p].get('skillUltimateLevel')})
  for c in e.const:
   take=[j+1 for j,p in enumerate(c['stars']) if p in s['devotions']]
   if take:
    cn=c['name']+(' ('+str(c['record'].get('affinityGivenName1',''))+')' if c['name']=='Crossroads' else '')
    detail=[]
    for j in take:
     p=c['stars'][j-1];sr=e.db[p];detail.append(str(j)+': '+e.name(p)+' '+json.dumps(e.numeric(sr),separators=(',',':')))
    devrows.append({'build':label,'constellation':cn,'stars':','.join(map(str,take)),'count':len(take),'total':len(c['stars']),'star_details':' ; '.join(detail)})
  bindrows += [dict(build=label,**z) for z in b]
  for rr in v['resistances']:resrows.append(dict(build=label,**rr))
  for metric in ['health','energy','OA','DA','armor','armor_absorption','damage_absorption_percent','cooldown_reduction','offense_proxy','defense_proxy','totem_count','totems_per_cast','totem_cooldown','raging_tempest_RR','widow_RR','ultos_relative_RR','mirror_cooldown','energy_regen_lower_bound','totem_wind_energy_upkeep_estimate','energy_margin_lower_bound']:
   summary.append({'build':label,'metric':metric,'baseline':baseline.get(metric),'result':v.get(metric),'status':'Calculated estimate' if metric not in ['health','energy','OA','DA','armor'] else 'Calculated; baseline reproduced export'})
 # Reference gear: no original random seeds were provided by Grimtools. Preserve
 # unrolled definitions as an explicitly estimated reference, never as inventory.
 g=read(ROOT/'guide70.json')['data'];guideitems=[]
 guidekeys=['head','amulet','chest','legs','feet','hands','ring1','ring2','belt','shoulders','medal','relic','weapon1','weapon2']
 for i,key in enumerate(guidekeys):
  it=g['equipment'].get(key,{})
  if not it and key=='belt':it=g['equipment'].get('waist',{})
  base=e.db.get(it.get('item'),{});guideitems.append({'slot':SLOTS[i],'item':e.name(it.get('item')),'record':it.get('item'),'component':e.name(it.get('component')),'augment':e.name(it.get('augment')),'required_level':base.get('levelRequirement'),'owned_same_base':[x['id'] for x in e.cat if x['save']['basename']==it.get('item')],'comparison_status':'Reference definitions; original random rolls unavailable'})
 # Sensitivity ratios across explicit target/proc assumptions. These are not
 # statistical confidence intervals and do not convert this proxy into DPS.
 def offense(v,enemy,up,da):
  packet=v['storm_packet']+.5*v['maelstrom_packet'];rr=enemy-v['raging_tempest_RR']-v['widow_RR']*up;rr*=1-v['ultos_relative_RR']/100*up if rr>=0 else 1+v['ultos_relative_RR']/100*up
  oa=v['OA'];pth=(((oa/(da/3.5+oa))*300)*.3)+((((oa*3.25+10000-da*3.25)/100)*.7))-50;crit=max(0,min(.35,(pth-90)/100));factor=min(1,pth/100)*(1+crit*(.1+v['stats'].get('offensiveCritDamageModifier',0)/100))
  return packet*max(.01,1-rr/100)*factor
 sensitivity=[]
 for key,x in chosen.items():
  for enemy in [0,40,80]:
   for up in [0,.6,1]:
    for da in [1800,2200,2600]:
     b=offense(baseline,enemy,up,da);a=offense(x['stats'],enemy,up,da);sensitivity.append({'build':key,'enemy_resistance':enemy,'proc_uptime':up,'enemy_DA':da,'baseline_proxy':b,'build_proxy':a,'ratio':a/b})
 final={'results':r,'audits':audits,'loadouts':loadouts,'summary':summary,'purchases':purchases,'skills':skillrows,'devotions':devrows,'bindings':bindrows,'resistances':resrows,'guide_items':guideitems,'sensitivity':sensitivity,'candidate_counts':[len(o) for o in e.options()],'components_considered':len(e.components),'augments_considered':len(e.augments)}
 variants=read(ROOT/'guide-variants.json');guide_stats=[];guide_spend=None
 for sample,gear in enumerate(variants):
  s=copy.deepcopy(chosen['balanced']['state']);s['skills']={a['name']:a['level'] for a in g['skills'] if '/playerclass' in a['name'] and a['level']>0};s['devotions']=e.devotion_seeds()['guide_51'];s['gear']=[];s['comp']=[];s['aug']=[]
  for i,it in enumerate(gear):
   key=guidekeys[i];src=g['equipment'].get('waist' if key=='belt' else key,{});save=it['save'];ident=f'GUIDE{sample:02d}_{i:02d}'
   save.update({'relic-name':src.get('component',''),'augment-name':src.get('augment','')})
   records=[e.db.get(save.get(k),{}) for k in ['basename','prefix-name','suffix-name','modifier-name','relic-name','augment-name','relic-bonus','ascended-name']]
   e.items[ident]={'id':ident,'name':e.name(save['basename']),'owner':'Guide reference','location':'Reference only','save':save,'records':records,'rolled':it['rolled'],'worn-rolled':it['rolled'],'completion':it.get('completion') or {},'requirements':{}}
   s['gear'].append(ident);s['comp'].append(src.get('component',''));s['aug'].append(src.get('augment',''))
  # Spend the eight additional skill points the original reference leaves
  # available under Mal's actual 198-point budget, on a common objective.
  while sum(s['skills'].values())<e.skillbudget:
   options=[]
   for p,l in s['skills'].items():
    if '_classtraining' in p or l>=e.db[p].get('skillMaxLevel',1):continue
    q=copy.deepcopy(s);q['skills'][p]+=1;z=e.calculate(q);options.append((math.log(max(1,z['offense_proxy']))+math.log(max(1,z['defense_proxy'])),p))
   if not options:break
   s['skills'][max(options)[1]]+=1
  guide_stats.append(e.calculate(s));guide_spend=s['skills']
 final['guide_reference']={'samples':32,'status':'Estimated reference: fixed guide affixes, 32 synthetic seed sets; not original guide rolls or owned gear. Uses Mal level, earned attributes and 198 skill points; guide Tree of Life partial removed to fit 51 devotion points.','skills':guide_spend,'stats':guide_stats,'minimum':{k:min(v[k] for v in guide_stats) for k in ['health','OA','DA','armor','offense_proxy']},'maximum':{k:max(v[k] for v in guide_stats) for k in ['health','OA','DA','armor','offense_proxy']}}
 dump(ROOT/'results/report-data.json',final)
 for k,a in audits.items():print(k,'LEGAL',a['legal_verified'],'equip',a['equip_order']['unresolved_slots'],'skill',a['skill_errors'],'dev',a['devotion_acquisition']['reason'],'binding',[(b['power'],b['bind_to'],b['valid_template']) for b in a['bindings']])
 return final
if __name__=='__main__':build()
