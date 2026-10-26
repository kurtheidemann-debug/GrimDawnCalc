"""One bounded matched source-policy fixture; no production review."""
import copy,json,time
from unittest.mock import patch
from test_stage7 import WeaponSearchTests
from production_search import bounded_search
from combat_configuration import resolve_configuration

WeaponSearchTests.setUpClass()
try:
 e=WeaponSearchTests.e;rows={}
 for label in ['stage7_swords','configured_melee']:
  if label=='configured_melee':
   for ident,kind,speed in [('upgrade0','WeaponMelee_Axe',-.25),('upgrade1','WeaponMelee_Mace',-.15)]:
    x=e.items[ident];base=copy.deepcopy(x['records'][0]);base.update(Class=kind,characterBaseAttackSpeed=speed,characterBaseAttackSpeedTag='Speed: Slow',augmentSkillName1='records/skills/playerclass01/cadence1.dbr',augmentSkillLevel1=4)
    path='fixture/'+ident;x['save']['basename']=path;x['records'][0]=base;e.db[path]=base
    for f in ['rolled','worn-rolled']:x[f]['characterBaseAttackSpeed']=speed
  pair=e.current['gear'][12:];weapons=pair if label=='stage7_swords' else pair+['upgrade0','upgrade1']
  opts=[[i] for i in e.current['gear']];opts[12]=weapons[:];opts[13]=weapons[:]
  e.cache.clear();e.costmemo.clear();e.memo.clear();e.comparisons.clear()
  configuration=resolve_configuration(e.mal,e.db,'cadence','dual_wield_melee' if label=='configured_melee' else None)
  with patch.object(e,'options',return_value=opts),patch.object(e,'components',[]),patch.object(e,'augments',[]):
   start=time.perf_counter();r=bounded_search(e,time.monotonic()+30,width=5,rounds=1);elapsed=time.perf_counter()-start
  from collections import Counter
  rows[label]={'configuration':configuration,'eligible_by_type':dict(Counter(e.items[i]['records'][0]['Class'] for i in weapons)),'weapon_configurations_evaluated':r['weapon_pair_configurations_evaluated'],'evaluations':r['evaluations'],'seconds':elapsed,'completed':not r['timed_out'],'selected_pair':r['selected']['state']['gear'][12:] if r.get('selected') else None}
 print(json.dumps(rows,indent=2));open('Stage8_Benchmark.json','w').write(json.dumps(rows,indent=2)+'\n')
finally:WeaponSearchTests.tearDownClass()
