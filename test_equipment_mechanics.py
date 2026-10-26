"""Source/stacking regressions. No search, profiles, or game database required."""
import collections
import copy
from types import SimpleNamespace
import unittest
from GrimDawn_Optimizer import Engine, RES, resistance_caps, modified
from relative_offense import RelativeOffense, convert_payload
from cadence_inputs import targeted_modifiers
from cadence_scenarios import selected_records
from beeztrap_equipment import BeeztrapEquipment


def fixture():
    e=Engine.__new__(Engine);e.cache={};e.evaluations=0
    e.db={'base':{'Class':'WeaponMelee_Sword'},
          'silver':{'itemSkillName':'chaos-aura','itemSkillLevel':1},
          'salt':{'itemSkillName':'aether-aura','itemSkillLevel':1},
          'chaos-aura':{'Class':'Skill_BuffSelfToggled','defensiveChaosMaxResist':3,'defensiveChaos':20},
          'aether-aura':{'Class':'Skill_BuffSelfToggled','defensiveAetherMaxResist':3,'defensiveAether':20}}
    e.items={}
    for ident in ['one','two']:
        e.items[ident]={'id':ident,'save':{'basename':'base','seed':1,'relic-name':'silver'},
                        'rolled':{},'worn-rolled':{},'completion':{},'records':[e.db['base'],e.db['silver']]}
    return e


class EquipmentMechanicsTests(unittest.TestCase):
    def test_silver_stacks_per_physical_component_as_percentage_points(self):
        e=fixture();caps=collections.Counter();raw=0
        for ident in ['one','two']:
            vals,_,_,cap=e.item_parts(ident,'silver','');caps.update(cap);raw+=vals['defensiveChaos']
        self.assertEqual(caps['defensiveChaos'],6)
        self.assertEqual(80+caps['defensiveChaos'],86)
        self.assertEqual(raw,40)  # Extra cap is not +6 ordinary resistance or x1.06.

    def test_salt_uses_same_path_and_removing_attachment_removes_aura(self):
        e=fixture()
        self.assertEqual(e.item_parts('one','salt','')[3]['defensiveAether'],3)
        vals,_,_,caps=e.item_parts('one','','')
        self.assertEqual(caps['defensiveChaos'],0);self.assertEqual(vals['defensiveChaos'],0)

    def test_base_component_augment_persistent_grants_are_each_counted(self):
        e=fixture();e.db['base']['itemSkillName']='chaos-aura'
        e.db['augment']={'itemSkillName':'chaos-aura'}
        self.assertEqual(e.item_parts('one','silver','augment')[3]['defensiveChaos'],9)

    def test_temporary_conditional_and_transformation_grants_not_always_on(self):
        for cl in ['Skill_BuffSelfDuration','Skill_PassiveOnLifeBuffSelf','Skill_Shapeshift']:
            e=fixture();e.db['chaos-aura']['Class']=cl
            vals,_,_,cap=e.item_parts('one','silver','')
            self.assertEqual(vals['defensiveChaos'],0);self.assertEqual(cap['defensiveChaos'],0)

    def test_granted_rank_and_all_max_resistance_are_additive(self):
        e=fixture();e.db['silver']['itemSkillLevel']=2
        e.db['chaos-aura'].update(defensiveChaosMaxResist=[1,3],defensiveAllMaxResist=[1,2])
        cap=e.item_parts('one','silver','')[3]
        self.assertEqual(cap['defensiveChaos'],5);self.assertEqual(cap['defensiveFire'],2)

    def test_ascended_stats_ranks_modifiers_caps_independent_of_empty_attachment_slots(self):
        for component,augment in [('', ''),('silver',''),('silver','salt')]:
            e=fixture();e.db['ascended']={'augmentAllLevel':2,'characterOffensiveAbility':7,
                'defensiveFireMaxResist':2,'modifiedSkillName1':'totem','modifierSkillName1':'totem-mod'}
            e.db['totem-mod']={'petLimit':1};e.items['one']['save']['ascended-name']='ascended'
            vals,bon,mods,cap=e.item_parts('one',component,augment)
            self.assertEqual(vals['characterOffensiveAbility'],7)
            self.assertEqual(bon['all'],2);self.assertEqual(mods['totem']['petLimit'],1)
            self.assertEqual(cap['defensiveFire'],2)

    def test_live_sources_match_cadence_sources_without_ghost_saved_attachments(self):
        e=fixture();e.db['old']={'modifiedSkillName1':'totem','modifierSkillName1':'old-mod'}
        e.db['new']={'modifiedSkillName1':'totem','modifierSkillName1':'new-mod'}
        e.db['old-mod']={'petLimit':5};e.db['new-mod']={'petLimit':1}
        e.items['one']['save']['relic-name']='old';e.items['one']['records']=[e.db['base'],e.db['old']]
        state={'gear':['one'],'comp':['new'],'aug':['']}
        model=RelativeOffense.__new__(RelativeOffense);model.e=e;model.db=e.db
        sources,mods=model.equipment_records(state)
        self.assertEqual([r for r,l in sources],selected_records(e,state,0))
        self.assertNotIn(e.db['old'],[r for r,l in sources])
        self.assertEqual(mods['totem'],[(e.db['new-mod'],1)])
        self.assertEqual(len(targeted_modifiers(e,state)['totem']),1)

    def test_unchanged_attachment_modifier_is_not_doubled(self):
        e=fixture();e.db['silver'].update(modifiedSkillName1='totem',modifierSkillName1='mod')
        e.db['mod']={'skillCooldownTime':-1}
        m=RelativeOffense.__new__(RelativeOffense);m.e=e;m.db=e.db
        _,mods=m.equipment_records({'gear':['one'],'comp':['silver'],'aug':['']})
        self.assertEqual(len(mods['totem']),1)

    def test_conversion_signature_uses_live_attachment_once(self):
        e=fixture();e.db['old']={'conversionInType':'Physical','conversionOutType':'Fire','conversionPercentage':30}
        e.db['new']={'conversionInType':'Physical','conversionOutType':'Cold','conversionPercentage':40}
        e.items['one']['records']=[e.db['base'],e.db['old']];e.convcache={}
        state={'gear':['one'],'comp':['new'],'aug':['']}
        self.assertEqual(BeeztrapEquipment.conversion_signature(e,state),[('Physical','Cold','40')])

    def test_unambiguous_intrinsic_conversion_uses_seeded_roll(self):
        e=fixture();e.db['base'].update(conversionInType='Physical',conversionOutType='Fire',conversionPercentage=25)
        e.items['one']['worn-rolled']={'conversionPercentage':29.0115}
        records=e.item_records('one','','')
        self.assertEqual(records[0]['conversionPercentage'],29.0115)
        self.assertEqual(e.db['base']['conversionPercentage'],25)  # Static data not mutated.
        # Live attachment conversions retain their own value rather than borrowing the base roll.
        e.db['new']={'conversionInType':'Physical','conversionOutType':'Cold','conversionPercentage':40}
        records=e.item_records('one','new','')
        self.assertEqual([r['conversionPercentage'] for r in records],[25,40])

    def test_same_type_percentage_modifiers_sum_before_application(self):
        self.assertAlmostEqual(modified(100,10+20),130)
        self.assertEqual(resistance_caps({'defensiveChaosMaxResist':3})['defensiveChaos'],3)

    def test_conversion_normalization_and_no_reconversion(self):
        # Official conversion order: local then global, each original damage unit once.
        v=convert_payload({'Physical':100}, [('Physical','Fire',50)], [('Physical','Cold',100),('Fire','Chaos',100)])
        self.assertEqual(v,{'Fire':50,'Cold':50,'Physical':0})
        v=convert_payload({'Physical':100},[],[('Physical','Fire',75),('Physical','Cold',75)])
        self.assertAlmostEqual(v['Fire'],50);self.assertAlmostEqual(v['Cold'],50)

    def test_primary_resistance_ceiling_is_95(self):
        # Exercise the derived-stat path with an otherwise empty synthetic character.
        from GrimDawn_Optimizer import STORM,WIND,MAEL,SC,SPHERE
        e=fixture();e.equipment_only=True
        e.db.update({p:{} for p in [STORM,WIND,MAEL,SC,SPHERE,
            'records/skills/playerclass06/pets/petskill_totemstorm_chainlightning.dbr',
            'records/skills/playerclass06/pets/petskill_whirlwind_stormcaller1.dbr']})
        e.db['base']['defensiveAllMaxResist']=30
        e.mal={'skills':[],'physique':50,'cunning':50,'spirit':50,'character-level':1}
        e.pen={f:0 for f in RES};e.name=lambda p:p
        e.items['one']['worn-rolled']={f:200 for f in RES}
        state={'gear':['one']*14,'comp':['']*14,'aug':['']*14,'skills':{},'devotions':{},'attributes':[0,0,0]}
        v=e.calculate(state)
        self.assertEqual([r['cap'] for r in v['resistances'][:9]],[95]*9)
        self.assertEqual([r['shown'] for r in v['resistances'][:9]],[95]*9)


if __name__=='__main__':unittest.main()
