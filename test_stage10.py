"""Focused finite-stock crafting and default-menu regressions."""
import collections,copy,unittest,ast
from pathlib import Path
from routine_crafting import ingredient_cost_units,default_recipes
from GrimDawn_Optimizer import Engine
class CraftingTests(unittest.TestCase):
 def engine(self,level=77):
  e=Engine.__new__(Engine);e.available=collections.Counter({'tier1':6,'tier2':4});e.recipes={'component':{'artifactName':'component','artifactCreationCost':'1500','reagentBaseBaseName':'tier1','reagentBaseQuantity':3,'reagent1BaseName':'tier2','reagent1Quantity':2}};e.mal={'iron':10000,'character-level':level};e.items={'a':{'owner':'Beeztrap','save':{}},'b':{'owner':'Beeztrap','save':{}}};e.character_name='Beeztrap';e.name=lambda p:p;e.db={};e.augments=[];return e
 def state(self,n=1):return {'gear':['a','b'][:n],'comp':['component']*n,'aug':['']*n}
 def test_tier1_and_tier2_stock_can_craft_missing_component(self):
  r=self.engine().resources(self.state());self.assertEqual(r['errors'],[]);self.assertEqual(r['craft_iron_base'],1500);self.assertEqual(r['ingredient_consumption'],{'tier1':3,'tier2':2})
 def test_two_crafts_conserve_finite_ingredients(self):
  e=self.engine();r=e.resources(self.state(2));self.assertEqual(r['craft_iron_base'],3000);self.assertEqual(r['ingredient_consumption'],{'tier1':6,'tier2':4});self.assertFalse(r['errors']);e.available['tier1']=5;self.assertIn('tier1: short 1',e.resources(self.state(2))['errors'])
 def test_tier3_never_assumed_at_any_level(self):
  for level in [77,100]:
   e=self.engine(level);e.recipes['component']['reagent1BaseName']='tier3';self.assertIn('tier3: short 2',e.resources(self.state())['errors']);e.available['tier3']=2;self.assertFalse(e.resources(self.state())['errors']);self.assertIn('tier3: short 2',e.resources(self.state(2))['errors'])
 def test_unknown_recipe_and_unknown_material_blocked(self):
  e=self.engine();e.recipes={};self.assertIn('component: short 1',e.resources(self.state())['errors']);e=self.engine();e.recipes['component']['reagent1BaseName']='unknown';self.assertIn('unknown: short 2',e.resources(self.state())['errors'])
 def test_attached_component_not_salvaged(self):
  e=self.engine();e.items['b']['save']['relic-name']='component';e.available.clear();e.recipes.clear();self.assertIn('component: short 1',e.resources(self.state())['errors'])
 def test_completed_stock_avoids_crafting(self):
  e=self.engine();e.available['component']=1;r=e.resources(self.state());self.assertFalse(r['errors']);self.assertEqual(r['crafted_batches'],{});self.assertEqual(r['craft_iron_base'],0)
 def test_attached_component_retained(self):
  e=self.engine();e.items['a']['save']['relic-name']='component';e.available.clear();r=e.resources(self.state());self.assertFalse(r['errors']);self.assertEqual(r['craft_iron_base'],0)
 def test_iron_constraint(self):
  e=self.engine();e.mal['iron']=1499;self.assertIn('Iron requirement exceeds current balance',e.resources(self.state())['errors'])
 def test_default_menu_loaded_in_shared_engine(self):
  path='records/items/crafting/recipe.dbr';recipe={'Class':'ItemArtifactFormula','artifactName':'component','levelRequirement':15};db={path:recipe,'component':{},'records/ui/inventor/craftingpanel/crafting_table.dbr':{'craftingDefaultRecipes':[path]}}
  self.assertEqual(dict(default_recipes(db,77)),{'component':recipe});self.assertEqual(dict(default_recipes(db,10)),{})
  db['records/ui/inventor/craftingpanel/crafting_table.dbr']['craftingDefaultRecipes']=[];self.assertEqual(dict(default_recipes(db,77)),{})
 def test_ordinary_crystal_cost_is_not_quest_rarity(self):
  self.assertEqual(ingredient_cost_units({},'records/items/materia/compa_aethercrystal.dbr'),1)
  self.assertEqual(ingredient_cost_units({},'unknown_special'),15)
if __name__=='__main__':unittest.main()
