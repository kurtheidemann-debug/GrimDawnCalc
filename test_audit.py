import collections,copy,json,pathlib,unittest
from relative_offense import RelativeOffense,instance_budget,convert_payload,rr_categories,difficulty_penalties,useful_overcap,payload_of
from practical_optimizer import PracticalEngine
class AuditTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.e=PracticalEngine()
 def test_difficulty_penalties_are_totals_not_cumulative(self):
  e=self.e
  normal=difficulty_penalties(e.db,0);elite=difficulty_penalties(e.db,1);ultimate=difficulty_penalties(e.db,2)
  self.assertTrue(all(v==0 for v in normal.values()))
  for field in ['defensiveFire','defensiveCold','defensiveLightning','defensivePoison','defensivePierce']:
   self.assertEqual(elite[field],-25);self.assertEqual(ultimate[field],-50)
  for field in ['defensiveBleeding','defensiveLife','defensiveAether','defensiveChaos']:
   self.assertEqual(elite[field],0);self.assertEqual(ultimate[field],-25)
  self.assertEqual(ultimate['defensivePhysical'],0);self.assertEqual(e.pen,ultimate)
  v=e.evaluate(e.current);self.assertEqual(v['resistances'][3]['raw'],33)
  for row in v['resistances']:self.assertEqual(row['before_difficulty_penalty']+row['difficulty_penalty'],row['difficulty_adjusted_before_cap'])
 def test_deployables_bounded_by_lifetime_and_cooldown(self):
  slow=instance_budget(5,1,10,10);fast=instance_budget(5,1,2,10)
  self.assertEqual(slow['sustainable'],1);self.assertLessEqual(slow['practical'],1)
  self.assertGreater(fast['practical'],slow['practical']);self.assertLessEqual(fast['practical'],5)
  self.assertEqual(instance_budget(1,1,1,10)['sustainable'],instance_budget(1,1,2,10)['sustainable'])
 def test_permanent_and_temporary_summons_differ(self):
  permanent=instance_budget(3,1,30,None);temporary=instance_budget(3,1,30,10)
  self.assertEqual(permanent['practical'],3);self.assertAlmostEqual(temporary['sustainable'],1/3)
  self.assertEqual(permanent['practical'],instance_budget(3,1,3,None)['practical'])
 def test_conversion_once_and_additive_damage_bonus(self):
  v=convert_payload({'Physical':100},[('Physical','Lightning',100)],[('Lightning','Cold',100)])
  self.assertEqual(v['Lightning'],100);self.assertEqual(v.get('Cold',0),0)
  # This tests the additive denominator used by the generic channel model.
  self.assertAlmostEqual((1+1700/100)/(1+1600/100),18/17)
  self.assertEqual(payload_of({'offensiveFireMin':[10,20],'offensiveFireMax':[20,40]},2)['Fire'],30)
 def test_rr_source_dedup_and_nonstacking_categories(self):
  r=rr_categories([('same',{'defensiveLightning':-20},1),('same',{'defensiveLightning':-20},1),('other',{'defensiveLightning':-15},1),('a',{'offensiveTotalResistanceReductionAbsoluteMin':10,'offensiveElementalResistanceReductionPercentMin':20},1),('b',{'offensiveTotalResistanceReductionAbsoluteMin':8,'offensiveElementalResistanceReductionPercentMin':15},1)])
  self.assertEqual(r['Lightning'],{'additive':35,'flat':10,'relative':20})
 def test_excess_poison_has_zero_incremental_value(self):
  rows=copy.deepcopy(self.e.evaluate(self.e.current)['resistances']);rows[3]['overcap']=20
  x=useful_overcap(rows);rows[3]['overcap']=89
  self.assertEqual(x,useful_overcap(rows));rows[3]['overcap']=43;self.assertEqual(x,useful_overcap(rows))
 def test_direct_damage_and_pet_domains_using_data_records(self):
  class Fixture:
   def __init__(self):
    self.d=pathlib.Path('/nonexistent');self.mal={'character-name':'Fixture','character-level':50};self.current={'skills':{'spell':1,'summon':1,'bonus':1}}
    self.db={'spell':{'Class':'Skill_AttackProjectile','offensiveFireMin':100},'summon':{'Class':'Skill_TargetedSpawnPet','petLimit':2,'spawnObjects':['pet']},'pet':{'Class':'Pet','skillName1':'bite','skillLevel1':1},'bite':{'Class':'Skill_AttackMelee','offensivePhysicalMin':50},'bonus':{'Class':'Skill_Passive','petBonusName':'petbonus','petBonusLevel':1},'petbonus':{}}
   def name(self,p):return p
  model=RelativeOffense(Fixture());state={'gear':[],'comp':[],'aug':[],'bindings':{},'devotions':{}}
  def stats(cast=0,fire=0,pet=0):
   return {'effective_skills':{'spell':1,'summon':1,'bonus':1},'cooldown_reduction':0,'OA':2000,'spirit':0,'cunning':0,'stats':{'characterSpellCastSpeedModifier':cast,'offensiveFireModifier':fire,'pet':pet}}
  a=model.summarize(state,stats());b=model.summarize(state,stats(cast=100,fire=100))
  self.assertEqual(b['abilities']['spell']['strength']/a['abilities']['spell']['strength'],4)
  self.assertEqual(b['abilities']['summon']['strength'],a['abilities']['summon']['strength'])
  self.assertEqual(a['abilities']['summon']['population']['practical'],2)
  model.db['petbonus'].update({'offensivePhysicalModifier':100,'characterAttackSpeedModifier':100})
  petboost=model.summarize(state,stats())
  self.assertEqual(petboost['abilities']['summon']['strength']/a['abilities']['summon']['strength'],4)
  self.assertEqual(petboost['abilities']['spell']['strength'],a['abilities']['spell']['strength'])
  model.db['summon'].update({'spawnObjectsTimeToLive':10,'skillCooldownTime':20})
  slow=model.summarize(state,stats());quick=stats();quick['cooldown_reduction']=50;fast=model.summarize(state,quick)
  self.assertGreater(fast['abilities']['summon']['population']['sustainable'],slow['abilities']['summon']['population']['sustainable'])
 def test_mal_pet_aura_and_autonomous_speed_not_multiplied(self):
  e=self.e;v=e.calculate(e.current);summary=v['offense_model'];wind=next(a for a in summary['abilities'].values() if a['name']=='Wind Devil')
  self.assertEqual(wind['population']['lifetime'],'permanent')
  self.assertTrue(any(p['instances']==1 and p['debuff_aura'] for p in wind['parts']))
  self.assertTrue(any(p['instances']==3 and not p['debuff_aura'] for p in wind['parts']))
  faster=copy.deepcopy(v);faster['stats']['characterSpellCastSpeedModifier']=1000
  x=e.model.summarize(e.current,faster)
  self.assertEqual(x['abilities']['records/skills/playerclass06/squall1.dbr']['strength'],wind['strength'])
if __name__=='__main__':unittest.main()
