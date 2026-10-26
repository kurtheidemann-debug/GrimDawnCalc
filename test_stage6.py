"""Mode-scope and resource-source fixtures. No Full Review or game-data rebuild."""
import copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace,MethodType
from unittest.mock import patch
import production_data as data
from production_report import item_source
from production_search import bounded_search,seed_states
from GrimDawn_Optimizer import Engine
from test_stage2 import minimal_character
from test_stage5 import BeamFixture

class AlignmentTests(unittest.TestCase):
 def stage(self,mode,shared=True,donors=True,resources=False):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name);src=root/'profiles/Beeztrap';src.mkdir(parents=True)
  (src/'profile.json').write_text('{"materiality":0.03,"reference_level":1}')
  # Poison a persisted Full catalog and account snapshots.
  (src/'catalog.json').write_text(json.dumps([{'owner':'Shared Stash','location':'/stash/0/inventory-items/0','save':{'basename':'stale'}}]))
  (src/'materials.json').write_text('[{"file":"reagents.gst","record":"component","quantity":999}]');(src/'recipes.json').write_text('[{"definition":{"artifactName":"stale"}}]')
  target=minimal_character();target['equipment'][0]={'basename':'local-equipped','seed':1}
  target['inventory-sacks']=[{'inventory-items':[{'basename':'local-bag','seed':2}]}];target['stashes']=[{'items':[{'basename':'local-stash','seed':3}]}]
  target['skills'][0]['level']=9;target['skills'][0]['autocast-skill-name']='saved-devotion';target['skills'].append({'skill-name':'records/skills/devotion/test.dbr','level':1,'devotion-level':7,'enabled':True,'skill-active':True,'autocast-skill-name':'','autocast-controller-name':''})
  donor={'inventory-sacks':[{'inventory-items':[{'basename':'donor','seed':4}]}]}
  stash={'stash':[{'inventory-items':[{'basename':'shared','seed':5},{'basename':'component','stack-count':2}]}]} if shared else None
  db={k:{'Class':'ArmorProtective_Head'} for k in ['local-equipped','local-bag','local-stash','shared','donor','stale']}
  db['component']={'Class':'ItemRelic'};db['records/game/balancingadjustment_mp+difficulty_players01.dbr']={}
  if resources:(root/'reagents.gst').write_bytes(b'fixture');(root/'formulas.gst').write_bytes(b'records/items/crafting/test.dbr');db['records/items/crafting/test.dbr']={'artifactName':'component'}
  def resolve(raw,prev,work):
   for i,it in enumerate(raw):it.update(id='I'+str(i),records=[db[it['save']['basename']]],resolved=True,requirements={},rolled={},name=it['save']['basename'])
   return raw,0
  with patch.object(data,'ROOT',root),patch.object(data,'database',return_value=db),patch.object(data,'resolve_items',side_effect=resolve),patch.object(data,'link_static'),patch.object(data,'read_materials',return_value=[{'file':'reagents.gst','record':'component','quantity':3}]):
   path,_,notices,_=data.stage_profile('Beeztrap',target,stash,mode,root,root/'work',{'Beeztrap':target,**({'Donor':donor} if donors else {})})
  return path,target,notices
 def test_fresh_character_state_both_modes(self):
  for mode in ['quick','full']:
   p,target,_=self.stage(mode);actual=json.loads((p/'mal.json').read_text());self.assertEqual(actual,target)
   for key in ['character-level','physique','attribute-points','last-difficulty','skills','devotion-points','equipment','faction-values']:self.assertEqual(actual[key],target[key])
 def test_mode_pool_and_resources_cannot_leak_from_full_cache(self):
  for mode,expected in [('quick',{'local-equipped','local-bag','local-stash','component'}),('full',{'local-equipped','local-bag','local-stash','component','shared','donor'})]:
   p,_,_=self.stage(mode);rows=json.loads((p/'catalog.json').read_text());self.assertEqual({r['save']['basename'] for r in rows},expected)
   self.assertEqual(json.loads((p/'materials.json').read_text()),[]);self.assertEqual(json.loads((p/'recipes.json').read_text()),[])
   for r in rows:self.assertIn(r['location'],item_source(SimpleNamespace(character_name='Beeztrap'),r))
 def test_both_modes_refresh_supplied_resources_without_admitting_shared_gear(self):
  for mode in ['quick','full']:
   p,_,_=self.stage(mode,resources=True);self.assertEqual(json.loads((p/'materials.json').read_text())[0]['quantity'],3);self.assertEqual(len(json.loads((p/'recipes.json').read_text())),1)
 def test_missing_shared_never_uses_previous_catalog(self):
  for mode in ['quick','full']:
   p,_,_=self.stage(mode,shared=False);rows=json.loads((p/'catalog.json').read_text());self.assertNotIn('Shared Stash',{r['owner'] for r in rows})
 def test_matched_search_donor_wins_full_only_and_same_pool_matches(self):
  runs={}
  for mode in ['quick','full']:
   p,_,_=self.stage(mode);rows=json.loads((p/'catalog.json').read_text());e=mode_beam(rows);r=bounded_search(e,float('inf'),width=2,rounds=1);runs[mode]=(r,e)
   name=e.items[r['selected']['state']['gear'][0]]['save']['basename'];self.assertEqual(name,'donor' if mode=='full' else 'local-stash')
   self.assertEqual(len(e.options()[0]),5 if mode=='full' else 3)
  self.assertGreater(runs['full'][0]['evaluations'],runs['quick'][0]['evaluations'])
  self.fixture_counts={mode:{'candidates':sum(map(len,e.options())),'evaluations':r['evaluations']} for mode,(r,e) in runs.items()}
  for mode in ['quick','full']:
   p,_,_=self.stage(mode,shared=False,donors=False);e=mode_beam(json.loads((p/'catalog.json').read_text()));r=bounded_search(e,float('inf'),width=2,rounds=1)
   if mode=='quick':reference=r['selected']
   else:self.assertEqual(r['selected'],reference)
 def test_full_seed_cannot_reintroduce_excluded_donor(self):
  p,_,_=self.stage('quick');e=mode_beam(json.loads((p/'catalog.json').read_text()))
  saved={'items':[e.items[i]['save'] for i in e.current['gear']],'comp':['']*14,'aug':['']*14};saved['items'][0]={'basename':'donor','seed':4}
  (p/'seeds.json').write_text(json.dumps([saved]));self.assertEqual(seed_states(e,p),[e.current])
 def test_resource_shortfall_still_blocks(self):
  e=Engine.__new__(Engine);e.available=__import__('collections').Counter();e.recipes={};e.mal={'iron':0};e.items={'head':{'owner':'Beeztrap','save':{}}};e.character_name='Beeztrap';e.name=lambda p:p;e.db={};e.augments=[]
  s={'gear':['head'],'comp':['missing'],'aug':['']};self.assertIn('missing: short 1',e.resources(s)['errors'])

def mode_beam(rows):
 e=BeamFixture(None);e.character_name='Mal';equipment=[r for r in rows if r['records'][0]['Class'].startswith('Armor')];e.items.update({x['id']:x for x in rows});e.cat=list(e.items.values());e.current['gear'][0]=next(x['id'] for x in equipment if x['save']['basename']=='local-equipped')
 e.options=lambda:[[x['id'] for x in equipment]]+[[x] for x in e.current['gear'][1:]]
 def stats(self,s):
  n={'local-equipped':100,'local-bag':104,'local-stash':108,'shared':110,'donor':115}[self.items[s['gear'][0]]['save']['basename']]
  return {'offense_index':n,'defense_index':100,'health':100,'DA':100,'armor':100,'offense_model':{'index':n}}
 e.calculate=MethodType(stats,e);e.evaluate=e.calculate;e.base=e.calculate(e.current);return e

if __name__=='__main__':unittest.main()
