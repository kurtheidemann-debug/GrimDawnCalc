"""One matched, bounded fixed/unlocked benchmark; never a Full Review."""
import json,subprocess,types
from test_stage7 import WeaponSearchTests

if __name__=='__main__':
 original=types.ModuleType('fixed_baseline')
 exec(subprocess.check_output(['git','show','f5b1b0b0a3c09311f65581c76c5ff46ab6ad62eb:production_search.py']).decode(),original.__dict__)
 WeaponSearchTests.setUpClass()
 try:
  case=WeaponSearchTests();case.test_quick_local_and_full_donor_weapon_scope();rows={}
  for label,fixed,search in [('fixed',True,original.bounded_search),('unlocked',False,__import__('production_search').bounded_search)]:
   e=case.e;e.cache.clear();e.costmemo.clear()
   r,elapsed=case.run_search(fixed=fixed,search=search)
   pairs={tuple(json.loads(k)['gear'][12:]) for k in e.comparisons if len(set(json.loads(k)['gear'][12:]))==2}
   rows[label]={'eligible_weapons':2 if fixed else 4,'ordered_pairs_scored':len(pairs),'search_evaluations':r['evaluations'],'seconds':elapsed,'completed':not r['timed_out'],'selected_pair':r['selected']['state']['gear'][12:],'offense_index':r['selected']['stats']['offense_index']}
  print(json.dumps(rows,indent=2));open('Stage7_Benchmark.json','w').write(json.dumps(rows,indent=2)+'\n')
 finally:WeaponSearchTests.tearDownClass()
