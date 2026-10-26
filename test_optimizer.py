import copy,unittest
from GrimDawn_Optimizer import Engine,STORM
class ModelTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.e=Engine()
 def test_baseline_reproduces_all_exported_values(self):
  for row in self.e.validate():
   if row['difference'] is not None:self.assertEqual(row['difference'],0,row['stat'])
 def test_duplicate_physical_ring_is_illegal(self):
  s=copy.deepcopy(self.e.current);s['gear'][7]=s['gear'][6]
  self.assertIn('Same physical item used twice',self.e.legal(s,self.e.calculate(s)))
 def test_point_budget_is_enforced(self):
  s=copy.deepcopy(self.e.current);s['attributes']=[100,0,0]
  self.assertIn('Attribute budget',self.e.legal(s,self.e.calculate(s)))
 def test_relic_cannot_take_component(self):
  s=self.e.current;p=next(x for x in self.e.components if self.e.db[x].get('head'))
  self.assertFalse(self.e.compatible(p,11,s['gear'][11]))
 def test_actual_reputation_controls_armor_augments(self):
  solar='records/items/enchants/c08a_enchant.dbr'
  self.assertIn(solar,self.e.augments)
  self.assertEqual(self.e.rep['User2'],25000)
 def test_guide_55_points_rejected_for_mal(self):
  import json
  g=json.load(open(self.e.d/'guide70.json'))['data'];d={s['name']:1 for s in g['skills'] if '/devotion/' in s['name'] and s['level']}
  self.assertFalse(self.e.devotion_valid(d)['valid'])
 def test_skill_hard_cap(self):
  bonuses={'all':100,'skill':{},'mastery':{}}
  self.assertEqual(self.e.effective(STORM,16,bonuses),26)
if __name__=='__main__':unittest.main()
