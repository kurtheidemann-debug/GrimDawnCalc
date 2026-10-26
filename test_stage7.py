"""Real Cadence scorer + production beam over a small synthetic gear fixture."""
import copy,json,tempfile,unittest,time
from pathlib import Path
from unittest.mock import patch
import GrimDawn_Optimizer as core
from production_data import link_static
from production_search import CadenceEngine,bounded_search
from production_report import item_source

class WeaponSearchTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.d=Path(cls.tmp.name)
  import shutil
  shutil.copytree(core.ROOT/'profiles/Beeztrap',cls.d,dirs_exist_ok=True);link_static(cls.d);(cls.d/'seeds.json').unlink(missing_ok=True)
  cat=json.loads((cls.d/'catalog.json').read_text())
  # Strengthen fixture defenses without altering production gates or formulas.
  head=next(x for x in cat if x['owner']=='Beeztrap' and x['location']=='/equipment/0')
  for field in ['rolled','worn-rolled']:
   vals=head[field]
   for key in core.RES[:9]:vals[key]=vals.get(key,0)+200
   vals['characterDefensiveAbility']=vals.get('characterDefensiveAbility',0)+1000
   vals['characterLife']=vals.get('characterLife',0)+10000
  weapons=[next(x for x in cat if x['owner']=='Beeztrap' and x['location']==f'/weapon-sets/0/items/{i}') for i in [0,1]]
  for i in [0,1]:
   x=copy.deepcopy(weapons[i]);x['id']='upgrade'+str(i);x['owner']='Donor';x['location']='/stashes/0/items/'+str(i)
   x['save']['seed']=9000+i;x['save']['augment-name']='';x['save']['relic-name']=''
   for field in ['rolled','worn-rolled']:
    x[field]['offensivePhysicalMin']=600-100*i;x[field]['offensivePhysicalMax']=700-100*i
   cat.append(x)
  (cls.d/'catalog.json').write_text(json.dumps(cat));cls.e=CadenceEngine(cls.d)
  assert cls.e.feasible_production(cls.e.current,cls.e.evaluate(cls.e.current)),cls.e.legal(cls.e.current,cls.e.evaluate(cls.e.current),True)
 @classmethod
 def tearDownClass(cls):cls.tmp.cleanup()
 def run_search(self,main=None,off=None,fixed=False,search=bounded_search):
  e=self.e;original=CadenceEngine.options(e);opts=[[x] for x in e.current['gear']]
  opts[12]=main if main is not None else [e.current['gear'][12],'upgrade0','upgrade1',e.current['gear'][13]]
  opts[13]=off if off is not None else [e.current['gear'][13],'upgrade0','upgrade1',e.current['gear'][12]]
  if fixed:opts[12:]=[[e.current['gear'][12]],[e.current['gear'][13]]]
  e.memo.clear();e.comparisons.clear()
  with patch.object(e,'options',return_value=opts),patch.object(e,'components',[]),patch.object(e,'augments',[]):
   start=time.perf_counter();r=search(e,time.monotonic()+30,width=5,rounds=1);elapsed=time.perf_counter()-start
  self.assertFalse(r['timed_out']);self.assertIsNotNone(r['selected']);self.assertEqual(e.legal(r['selected']['state'],r['selected']['stats'],True),[])
  return r,elapsed
 def test_main_only_replacement_selected(self):
  e=self.e;r,_=self.run_search([e.current['gear'][12],'upgrade0'],[e.current['gear'][13]])
  self.assertEqual(r['selected']['state']['gear'][12:],[ 'upgrade0',e.current['gear'][13]])
 def test_offhand_only_replacement_selected(self):
  e=self.e;r,_=self.run_search([e.current['gear'][12]],[e.current['gear'][13],'upgrade1'])
  self.assertEqual(r['selected']['state']['gear'][12:],[e.current['gear'][12],'upgrade1'])
 def test_two_replacements_selected_with_provenance(self):
  r,_=self.run_search();pair=r['selected']['state']['gear'][12:];self.assertEqual(set(pair),{'upgrade0','upgrade1'})
  for ident in pair:self.assertIn('Donor',item_source(self.e,self.e.items[ident]));self.assertIn('/stashes/0/items/',item_source(self.e,self.e.items[ident]))
 def test_reversed_hand_assignments_are_evaluated(self):
  e=self.e;pair=e.current['gear'][12:];r,_=self.run_search(pair,pair)
  signatures=[json.loads(k)['gear'][12:] for k in e.comparisons]
  self.assertIn(pair[::-1],signatures)
  swapped=copy.deepcopy(e.current);swapped['gear'][12:]=pair[::-1]
  for key in ['comp','aug']:swapped[key][12:]=swapped[key][12:][::-1]
  comparison=e.scorer.compare(swapped)
  self.assertTrue(any(abs(v-100)>1e-6 for v in comparison['scenario_indices'].values()))
 def test_original_only_scores_and_selection_unchanged(self):
  import subprocess,types
  original=types.ModuleType('fixed_baseline')
  exec(subprocess.check_output(['git','show','f5b1b0b0a3c09311f65581c76c5ff46ab6ad62eb:production_search.py']).decode(),original.__dict__)
  before,_=self.run_search(fixed=True,search=original.bounded_search);after,_=self.run_search(fixed=True)
  self.assertEqual(before['selected'],after['selected'])
 def test_illegal_pairs_and_attachment_resources(self):
  e=self.e;s=copy.deepcopy(e.current);s['gear'][13]=s['gear'][12];v=e.evaluate(s)
  self.assertIn('Same physical item used twice',e.legal(s,v,True))
  original=e.items['upgrade0']['records'][0]
  with patch.dict(e.items['upgrade0'],{'records':[{'Class':'WeaponMelee_Sword2h','characterBaseAttackSpeedTag':'Speed:  Very Fast'}]}):
   self.assertFalse(e.supported_weapon('upgrade0'))
  with patch.dict(e.items['upgrade0'],{'worn-rolled':{},'rolled':{},'records':[{'Class':'WeaponMelee_Sword','characterBaseAttackSpeed':float('nan'),'characterBaseAttackSpeedTag':'Speed:  Slow'}]}):self.assertFalse(e.supported_weapon('upgrade0'))
  s=copy.deepcopy(e.current);s['comp'][12]='records/items/materia/compa_wardstone.dbr'
  self.assertIn('comp slot Weapon',e.legal(s,e.evaluate(s),True))
  self.assertTrue(e.compatible(e.current['comp'][12],13,e.current['gear'][13]))
  s=copy.deepcopy(e.current);s['aug'][13]='records/items/enchants/c08a_enchant.dbr'
  self.assertIn('aug slot Offhand',e.legal(s,e.evaluate(s),True))
 def test_quick_local_and_full_donor_weapon_scope(self):
  e=self.e;full=e.cat
  with patch.object(e,'cat',[x for x in full if x['owner'] in ['Beeztrap','Shared Stash']]):
   self.assertNotIn('upgrade0',CadenceEngine.options(e)[12])
  self.assertIn('upgrade0',CadenceEngine.options(e)[12])
 def test_supported_options_use_same_sword_pool_for_both_hands(self):
  opts=CadenceEngine.options(self.e);self.assertEqual(opts[12],opts[13]);self.assertIn('upgrade0',opts[12]);self.assertIn('upgrade1',opts[13])

if __name__=='__main__':unittest.main()
