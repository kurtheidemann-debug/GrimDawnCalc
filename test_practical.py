import copy,json,pathlib,unittest
from practical_optimizer import PracticalEngine,STORM
class PracticalTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.e=PracticalEngine()
 def test_saved_skills_and_devotions_cannot_change(self):
  for field in ['skills','devotions','bindings']:
   q=copy.deepcopy(self.e.current)
   if q[field]:q[field].pop(next(iter(q[field])))
   else:q[field]['invalid']=1
   # invariant guard independently of calculator validation of unknown records
   if field=='skills':q[field]=dict(self.e.current[field]);q[field][STORM]+=1
   self.assertIn('Fixed saved '+field+' changed',self.e.legal(q,self.e.calculate(q)))
 def test_cheap_configuration_wins_inside_materiality_band(self):
  cheap={'stats':{'offense_index':100,'defense_index':100},'cost':{'utility_cost':2}}
  expensive={'stats':{'offense_index':104,'defense_index':102},'cost':{'utility_cost':20}}
  self.assertTrue(self.e.prefer(cheap,expensive));self.assertFalse(self.e.prefer(expensive,cheap))
 def test_actual_attachment_cost_breaks_immaterial_tie(self):
  e=self.e;i=0;ident=e.current['gear'][i]
  ps=[p for p in e.components if e.compatible(p,i,ident)]
  low=min(ps,key=e.component_cost);high=max(ps,key=e.component_cost)
  a=copy.deepcopy(e.current);b=copy.deepcopy(a);a['comp'][i]=low;b['comp'][i]=high
  self.assertLess(e.cost(a)['utility_cost'],e.cost(b)['utility_cost'])
  self.assertTrue(e.prefer({'stats':{'offense_index':100,'defense_index':100},'cost':e.cost(a)}, {'stats':{'offense_index':104,'defense_index':100},'cost':e.cost(b)}))
 def test_material_offense_does_not_get_cost_override(self):
  cheap={'stats':{'offense_index':100,'defense_index':100},'cost':{'utility_cost':2}}
  expensive={'stats':{'offense_index':110,'defense_index':100},'cost':{'utility_cost':20}}
  self.assertFalse(self.e.prefer(cheap,expensive))
 def test_components_have_opportunity_cost_even_when_owned(self):
  p=next(p for p in self.e.components if self.e.available[p]>0)
  self.assertGreater(self.e.component_cost(p),0)
 def test_attributes_preserved_when_not_required(self):
  s=self.e.repair_attributes(self.e.current)
  self.assertIsNotNone(s);self.assertEqual(s['attributes'],[0,0,0]);self.assertFalse(s.get('respec_attributes',False))
 def test_no_encounter_outputs(self):
  z=self.e.evaluate(self.e.current)
  self.assertNotIn('offense_proxy',z);self.assertNotIn('ramp_totems_6sec',z);self.assertEqual(z['offense_index'],100)
 def test_search_preserves_save_build_and_input(self):
  e=self.e;original=copy.deepcopy(e.current);opts=e.options;components=e.components;aug=e.augments
  e.options=lambda:[[x] for x in e.current['gear']];e.components=[];e.augments=[]
  # Suppress external benchmark starts only for this constrained regression.
  olddir=e.d;oldcalc=e.calculate;observed=[]
  def checked(state):
   for key in ['skills','devotions','bindings']:self.assertEqual(state[key],original[key])
   observed.append(1);return oldcalc(state)
  e.calculate=checked
  import tempfile
  try:
   with tempfile.TemporaryDirectory() as tmp:
    e.d=pathlib.Path(tmp);r=e.search_practical(width=2,rounds=1)
   for entry in r['chosen'].values():
    for key in ['skills','devotions','bindings']:self.assertEqual(entry['state'][key],original[key])
   self.assertEqual(e.current,original);self.assertTrue(observed)
  finally:e.calculate=oldcalc;e.d=olddir;e.options=opts;e.components=components;e.augments=aug
 def test_delivered_results_invariants(self):
  p=self.e.d/'practical-results/results.json'
  if not p.exists():self.skipTest('No computed report yet')
  r=json.loads(p.read_text());self.assertEqual(set(r['chosen']),{'minimal','balanced','offense'})
  for entry in r['chosen'].values():
   s=entry['state']
   for k in ['skills','devotions','bindings']:self.assertEqual(s[k],self.e.current[k])
   self.assertTrue(self.e.feasible(s,self.e.evaluate(s)));self.assertFalse(s.get('respec_attributes',False))
if __name__=='__main__':unittest.main()
