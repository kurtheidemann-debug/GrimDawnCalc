"""Small cross-character pool fixtures; no decoder, game-data rebuild or Full Review."""
import collections,copy,json,tempfile,unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import production_data as data
from production_search import bounded_search
from production_report import item_source
from GrimDawn_Optimizer import Engine,SLOTS
from test_stage2 import minimal_character

class PoolTests(unittest.TestCase):
 def staged(self,mode,donors=True):
  tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name);source=root/'profiles/Beeztrap';source.mkdir(parents=True)
  (source/'profile.json').write_text('{"materiality":0.03}');(source/'catalog.json').write_text('[]')
  for f in ['materials.json','recipes.json']:(source/f).write_text('[]')
  target=minimal_character();donor={'inventory-sacks':[{'inventory-items':[{'basename':'head','seed':1}]}], 'stashes':[{'items':[{'basename':'head','seed':1}]}], 'equipment':[{'basename':'head','seed':2}], 'weapon-sets':[]}
  db={'head':{'Class':'ArmorProtective_Head'},'records/creatures/pc/playerlevels.dbr':{},'records/game/balancingadjustment_mp+difficulty_players01.dbr':{}}
  def resolve(raw,previous,work):
   result=[]
   for i,it in enumerate(raw):
    it.update(id='I'+str(i),records=[db.get(it['save']['basename'],{})],resolved=True,requirements={},rolled={},name=it['save']['basename']);result.append(it)
   return result,0
  with patch.object(data,'ROOT',root),patch.object(data,'database',return_value=db),patch.object(data,'resolve_items',side_effect=resolve),patch.object(data,'link_static'):
   path,_,_,_=data.stage_profile('Beeztrap',target,{'stash':[]},mode,root,root/'work',{'Beeztrap':target,**({'Donor':donor} if donors else {})})
  return json.loads((path/'catalog.json').read_text())
 def test_full_imports_all_three_sources_and_instances(self):
  for mode in ['full']:
   rows=[r for r in self.staged(mode) if r['owner']=='Donor']
   self.assertEqual(len(rows),3);self.assertEqual(len({x['id'] for x in rows}),3)
   self.assertEqual({x['location'].split('/')[1] for x in rows},{'inventory-sacks','stashes','equipment'})
   for row in rows:self.assertIn(row['location'],item_source(SimpleNamespace(character_name='Beeztrap'),row))
 def test_real_resolver_keeps_identical_physical_instances_distinct(self):
  raw=[{'owner':'A','location':'/stashes/0/items/0','save':{'basename':'head','seed':1}},
       {'owner':'B','location':'/equipment/0','save':{'basename':'head','seed':1}}]
  def rolled(req,*args):return [{'key':x['key'],'rolled':{},'worn-rolled':{},'completion':{},'requirements':{}} for x in req['items']]
  with tempfile.TemporaryDirectory() as tmp,patch.object(data,'database',return_value={'head':{'Class':'ArmorProtective_Head'}}),patch.object(data,'roll_source_fingerprint',return_value='fixed'),patch.object(data,'bridge',side_effect=rolled):
   rows,_=data.resolve_items(raw,[],tmp)
  self.assertNotEqual(rows[0]['id'],rows[1]['id']);self.assertEqual(rows[0]['save'],rows[1]['save'])
  self.assertEqual([r['owner'] for r in rows],['A','B'])
 def test_no_donors_preserves_target_pool(self):
  for mode in ['quick','full']:
   self.assertEqual([x for x in self.staged(mode) if x['owner']!='Donor'],self.staged(mode,False))
 def test_existing_options_reject_level_and_binding_and_legal_rejects_attributes(self):
  e=Engine.__new__(Engine);e.character_name='Target';e.mal={'character-level':50,'attribute-points':0};e.current={};e.skillbudget=0
  e.cat=[{'id':key,'owner':'Donor','records':[{'Class':'ArmorProtective_Head',**flags}],'requirements':{'strength':req},'save':{}} for key,flags,req in [('good',{},0),('level',{'levelRequirement':51},0),('bound',{'soulbound':1},0),('untradeable',{'untradeable':1},0),('attribute',{},500)]]
  e.items={x['id']:x for x in e.cat};self.assertEqual(Engine.options(e)[0],['good','attribute'])
  e.compatible=lambda *a:True;e.devotion_valid=lambda *a:{'errors':[]};e.resources=lambda *a:{'errors':[]}
  state={'gear':['attribute'],'comp':[''],'aug':[''],'skills':{},'devotions':{},'attributes':[0,0,0]}
  v={'stats':{},'physique':100,'cunning':100,'spirit':100}
  self.assertIn('attribute physique requirement',e.legal(state,v))
  state['gear']=['bound'];self.assertIn('Bound base bound',e.legal(state,v))
 def test_each_donor_source_can_win_existing_beam(self):
  # Existing beam with deterministic scalar fixture; all sources use the same path.
  for location in ['/inventory-sacks/0/inventory-items/0','/stashes/0/items/0','/equipment/0']:
   e=BeamFixture(location);r=bounded_search(e,float('inf'),width=2,rounds=1)
   self.assertEqual(r['selected']['state']['gear'][0],'donor')
   self.assertIn('Donor',item_source(e,e.items['donor']));self.assertIn(location,item_source(e,e.items['donor']))
 def test_empty_extension_matches_existing_selection(self):
  a=bounded_search(BeamFixture(None),float('inf'),width=2,rounds=1)
  b=bounded_search(BeamFixture(None),float('inf'),width=2,rounds=1)
  self.assertEqual(a['selected'],b['selected'])

class BeamFixture:
 character_name='Mal'
 def __init__(self,location):
  self.current={'gear':['old'+str(i) for i in range(14)],'comp':['']*14,'aug':['']*14,'skills':{},'devotions':{},'bindings':{},'attributes':[0,0,0]}
  self.items={k:{'id':k,'save':{'basename':k},'owner':'Mal','location':'/equipment/'+str(i)} for i,k in enumerate(self.current['gear'])}
  if location:self.items['donor']={'id':'donor','save':{'basename':'head'},'owner':'Donor','location':location}
  self.cat=list(self.items.values());self.components=[];self.augments=[];self.mal={'attribute-points':0};self.model=SimpleNamespace(index=lambda a,b:a['index']);self.d=Path('/nonexistent-stage5-fixture');self.base=self.calculate(self.current)
 def options(self):return [[k]+(['donor'] if i==0 and 'donor' in self.items else []) for i,k in enumerate(self.current['gear'])]
 def signature(self,s):return json.dumps(s,sort_keys=True)
 def calculate(self,s):
  n=110 if s['gear'][0]=='donor' else 100
  return {'offense_index':n,'defense_index':100,'health':100,'DA':100,'armor':100,'offense_model':{'index':n}}
 evaluate=calculate
 def resources(self,s):return {'errors':[]}
 def cost(self,s):return {'utility_cost':0}
 def feasible(self,s,v):return True
 def score(self,s,v,mode):return v['offense_index']
 def compatible(self,*a):return True
 def legal(self,*a):return []
 def repair_attributes(self,s):return s
 def prefer(self,a,b):return False

if __name__=='__main__':unittest.main()
