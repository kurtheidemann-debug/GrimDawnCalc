"""Reproducible v1.1 resistance and offensive-factor audit, independent of search."""
import collections,copy,json,pathlib
from practical_optimizer import PracticalEngine
from GrimDawn_Optimizer import STORM,WIND,MAEL,at,RES
from relative_offense import useful_overcap,PENALTY_RECORD
ROOT=pathlib.Path(__file__).resolve().parent
def run():
 e=PracticalEngine();old=json.loads((ROOT/'archive/v1.1/practical-results/results.json').read_text());base=old['baseline'];rows={};pieces={};res={};ablation={};rerated={}
 allrows=[('current',base,e.current)]+[(k,x['stats'],x['state']) for k,x in old['chosen'].items()]
 for key,v,state in allrows:
  mods=collections.Counter();windmods=collections.Counter()
  for i,ident in enumerate(state['gear']):
   for target,vals in e.item_parts(ident,state['comp'][i],state['aug'][i])[2].items():
    if 'totem' in target:mods.update(vals)
    if any(q in target for q in ['whirlwind','squall','stormcaller']):windmods.update(vals)
  srank=v['effective_skills'][STORM];r=e.db['records/skills/playerclass06/pets/petskill_totemstorm_chainlightning.dbr']
  native=(at(r.get('offensiveLightningMin'),srank)+at(r.get('offensiveLightningMax'),srank))/2+mods['offensiveLightningMin']
  damage=1+v['lightning_modifier']/100;oa=v['OA']/2000*(1+v['stats'].get('offensiveCritDamageModifier',0)/500)
  rr=(1+(v['raging_tempest_RR']+v['widow_RR'])/100)*(1+v['ultos_relative_RR']/100)
  factors={'native_lightning':native,'damage_factor':damage+mods['offensiveLightningModifier']/100,'OA_crit_rating':oa,'RR_utility':rr,'capacity_factor':v['totem_count']/3,'deployment_factor':(4.5/v['totem_cooldown']*v['totems_per_cast'])**.35,'item_total_factor':1+mods['offensiveTotalDamageModifier']/100}
  product=1
  for x in factors.values():product*=x
  assert abs(product-v['storm_strength'])<1e-6
  rows[key]={'v11_index':v['offense_index'],'totem_rank':srank,'totem_invested':state['skills'][STORM],'totem_bonus':srank-state['skills'][STORM],'totem_maximum':v['totem_count'],'per_cast':v['totems_per_cast'],'cooldown':v['totem_cooldown'],'lightning_bonus_percent':v['lightning_modifier'],'raging_tempest_RR':v['raging_tempest_RR'],'widow_RR':v['widow_RR'],'ultos_relative_RR':v['ultos_relative_RR'],'factors':factors,'storm_relative':v['storm_strength']/base['storm_strength'],'wind_relative':v['wind_strength']/base['wind_strength'],'weighted_index_check':100*(.8*v['storm_strength']/base['storm_strength']+.2*v['wind_strength']/base['wind_strength'])}
  res[key]=[{**r,'before_difficulty':r['raw']-e.pen[f],'penalty':e.pen[f]} for f,r in zip(RES,v['resistances'][:9])]
  q=copy.deepcopy(v['resistances']);original=useful_overcap(q);q[3]['overcap']=max(0,min(20,q[3]['overcap']));ablation[key]={'useful_overcap_before':original,'useful_overcap_with_poison_excess_removed':useful_overcap(q),'score_gain_from_poison_above_cap_plus_20':original-useful_overcap(q)}
  current=e.evaluate(state);rerated[key]={'offense_index':current['offense_index'],'offense_model':current['offense_model']}
  assert all(v[k]==current[k] for k in ['health','OA','DA','armor','armor_absorption'])
  assert all(a['raw']==b['raw'] for a,b in zip(v['resistances'],current['resistances']))
  pieces[key]=[{'slot':i,'id':ident,'name':e.items[ident]['name'],'poison_from_item_attachments':e.item_parts(ident,state['comp'][i],state['aug'][i])[0].get('defensivePoison',0)} for i,ident in enumerate(state['gear'])]
 data={'saved_difficulty':e.mal['last-difficulty'],'difficulty_masked':e.mal['last-difficulty']&3,'database_record':PENALTY_RECORD,'database_penalty_arrays':e.db[PENALTY_RECORD],'extracted_penalties_match':e.pen=={f:e.db[PENALTY_RECORD].get(f,[0]*12)[8] for f in RES},'baseline_validation':e.validate(),'old_factors':rows,'v11_resistances':res,'poison_ablation':ablation,'poison_item_sources':pieces,'old_loadouts_under_revised_model':rerated}
 out=ROOT/'audit';out.mkdir(exist_ok=True);(out/'v11_audit.json').write_text(json.dumps(data,indent=2))
 print('v1.1 factor products reproduce; resistance and core stats unchanged for all old states.')
 print(json.dumps(rows,indent=2))
if __name__=='__main__':run()
