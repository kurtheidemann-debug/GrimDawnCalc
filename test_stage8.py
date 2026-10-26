"""Configuration, module capabilities and real Cadence class/speed admission."""
import copy,unittest,json,subprocess,types
from unittest.mock import patch
from combat_configuration import *
from test_stage2 import minimal_character
from test_stage7 import WeaponSearchTests
from production_search import CadenceEngine

class ConfigurationTests(unittest.TestCase):
 def character(self,main='sword',off='shield',alt=False):
  c=minimal_character();c['weapon-sets']=[{'items':[{'basename':main},{'basename':off}]},{'items':[{'basename':'axe'},{'basename':'mace'}]}];c['use-alt-weaponset']=alt;return c
 @property
 def db(self):return {k:{'Class':v} for k,v in [('sword','WeaponMelee_Sword'),('axe','WeaponMelee_Axe'),('mace','WeaponMelee_Mace'),('shield','WeaponArmor_Shield'),('caster','WeaponArmor_Offhand'),('two','WeaponMelee_Sword2h'),('gun','WeaponHunting_Ranged1h')]}
 def test_active_set_only_and_structures(self):
  for main,off,expected in [('sword','axe','dual_wield_melee'),('sword','shield','one_hand_shield'),('two','','two_hand_melee'),('sword','caster','one_hand_caster_offhand'),('gun','','ranged')]:self.assertEqual(detect_configuration(self.character(main,off),self.db),expected)
  self.assertEqual(detect_configuration(self.character(alt=True),self.db),'dual_wield_melee')
 def test_explicit_same_configuration_override(self):
  c=self.character('axe','mace');before=copy.deepcopy(c);r=resolve_configuration(c,self.db,'cadence','dual_wield_melee');self.assertEqual(r['source'],'override');self.assertEqual(c,before)
 def test_style_change_has_no_fabricated_reference_or_attachment_churn(self):
  c=self.character();before=copy.deepcopy(c)
  with self.assertRaisesRegex(ValueError,'no optimization or attachment changes'):resolve_configuration(c,self.db,'cadence','dual_wield_melee')
  self.assertEqual(c,before)
 def test_unvalidated_modules_and_configurations_fail(self):
  for module in ['werewolf','pets','totem']:
   with self.assertRaisesRegex(ValueError,'does not support'):resolve_configuration(self.character('axe','mace'),self.db,module,'dual_wield_melee')
 def test_numeric_speeds_not_display_tags(self):
  for kind in CADENCE_MELEE:
   for speed in [-.4,-.1,0,.1]:
    x={'records':[{'Class':kind,'characterBaseAttackSpeed':speed,'characterBaseAttackSpeedTag':'any label'}]};self.assertIsNone(cadence_weapon_reason(x))
  for value in [None,float('nan'),-1]:self.assertIsNotNone(cadence_weapon_reason({'records':[{'Class':'WeaponMelee_Axe','characterBaseAttackSpeed':value}]}))
 def test_illegal_structure(self):
  with self.assertRaises(ValueError):configuration_for_classes('WeaponMelee_Sword2h','WeaponArmor_Shield')
  with self.assertRaises(ValueError):configuration_for_classes('WeaponHunting_Ranged2h','WeaponArmor_Shield')

class CadenceClassTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):WeaponSearchTests.setUpClass();cls.e=WeaponSearchTests.e
 @classmethod
 def tearDownClass(cls):WeaponSearchTests.tearDownClass()
 def test_sword_scores_identical_to_stage7(self):
  e=self.e;original=types.ModuleType('original_scorer');import sys;sys.modules['original_scorer']=original
  exec(subprocess.check_output(['git','show','021fad95a9fae23d06810207337f256c38df9aff:cadence_scenarios.py']).decode(),original.__dict__)
  from cadence_scenarios import SCENARIOS
  before=original.CadenceScorer(e);after=e.scorer
  for s in [e.current,copy.deepcopy(e.current)]:
   old=before.snapshot(s);new=after.snapshot(s)
   self.assertEqual(old,new)
   self.assertEqual([before.strength(old,q) for q in SCENARIOS],[after.strength(new,q) for q in SCENARIOS])
 def test_axes_maces_and_slow_skill_bonus_weapon_can_win(self):
  e=self.e;case=WeaponSearchTests();ids=['upgrade0','upgrade1'];db_before={};items_before={i:copy.deepcopy(e.items[i]) for i in ids}
  try:
   for i,kind,speed in [('upgrade0','WeaponMelee_Axe',-.25),('upgrade1','WeaponMelee_Mace',-.15)]:
    item=e.items[i];base=copy.deepcopy(item['records'][0]);base['Class']=kind;base['characterBaseAttackSpeed']=speed;base['characterBaseAttackSpeedTag']='Speed: Slow';base['augmentSkillName1']='records/skills/playerclass01/cadence1.dbr';base['augmentSkillLevel1']=4
    path='fixture/'+i;item['save']['basename']=path;e.db[path]=base;item['records'][0]=base
    for field in ['rolled','worn-rolled']:item[field]['characterBaseAttackSpeed']=speed
   self.assertIn('upgrade0',CadenceEngine.options(e)[12]);self.assertIn('upgrade1',CadenceEngine.options(e)[13])
   r,elapsed=case.run_search([e.current['gear'][12],'upgrade0'],[e.current['gear'][13]])
   self.assertEqual(r['selected']['state']['gear'][12],'upgrade0')
   self.assertGreater(r['selected']['stats']['effective_skills']['records/skills/playerclass01/cadence1.dbr'],e.evaluate(e.current)['effective_skills']['records/skills/playerclass01/cadence1.dbr'])
   type(self).benchmark={'configuration':'dual_wield_melee','source':'active_save','eligible_by_type':{'sword':2,'axe':1,'mace':1},'pair_configurations_evaluated':r['weapon_pair_configurations_evaluated'],'evaluations':r['evaluations'],'seconds':elapsed,'completed':not r['timed_out']}
  finally:
   for i in ids:e.items[i].clear();e.items[i].update(items_before[i]);e.db.pop('fixture/'+i,None)
   e.memo.clear();e.comparisons.clear()

if __name__=='__main__':unittest.main()
