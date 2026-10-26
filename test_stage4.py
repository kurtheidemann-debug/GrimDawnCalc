"""Focused review routing and packet reuse checks; no Full Review."""
import copy, json, tempfile, unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import review
from cadence_scenarios import CadenceScorer, SCENARIOS

class ReviewRoutingTests(unittest.TestCase):
 def test_quick_and_full_suspend_disposition_without_touching_import(self):
  for mode in ['quick','full']:
   with self.subTest(mode=mode), tempfile.TemporaryDirectory() as t:
    root=Path(t);stage=root/'stage';stage.mkdir();out=root/'out';out.mkdir()
    (out/'Beeztrap_Inventory_Disposition.md').write_text('stale')
    calls=[]
    def stage_import(*args):
     calls.append(args[-1]);return stage,{'materiality':.03,'revision':1},[],0
    current={'gear':list(range(14)),'skills':{},'devotions':{},'bindings':{}}
    e=SimpleNamespace(cat=[],current=current,mal={'character-level':76},evaluate=lambda s:{})
    def decode(req,work):return {'characters':[], 'stash':{'present':True}}
    with patch.multiple(review,workflow_lock=__import__('contextlib').nullcontext,extract_zip=lambda *a:([],None),bridge=decode,select_character=lambda *a:('Beeztrap',{'Beeztrap':{},'Donor':{}}),stage_profile=stage_import,CadenceEngine=lambda *a:e,verify_baseline=lambda *a:(None,[]),bounded_search=lambda *a,**k:{'selected':None},report=lambda *a:None), patch('item_valuation.value_owned_equipment',side_effect=AssertionError('valuation invoked')),patch('inventory_decisions.apply_dispositions',side_effect=AssertionError('disposition invoked')),patch('inventory_decisions.write_inventory_report',side_effect=AssertionError('report invoked')),patch('production_report.disposition',side_effect=AssertionError('disposition invoked')):
     r=review.perform(root/'unused.zip',mode,'Beeztrap',out,60,commit=False)['Beeztrap']
    self.assertIn('Donor',calls[0])
    self.assertEqual(r['inventory_disposition'],'suspended')
    self.assertNotIn('inventory',r);self.assertNotIn('item_valuations',r)
    self.assertFalse((out/'Beeztrap_Inventory_Disposition.md').exists())
 def test_import_and_search_candidate_code_unchanged(self):
  import subprocess
  for p in ['beeztrap_equipment.py']:
   self.assertEqual(Path(p).read_bytes(),subprocess.check_output(['git','show','c9339ece9ddc324894ee0d9c73e5b9854936eedc:'+p]))
  self.assertEqual(Path('cadence_scenarios.py').read_bytes(),subprocess.check_output(['git','show','1cb13dbcc1debcd7bd668f1d319e10fa1ccb280c:cadence_scenarios.py']))

if __name__=='__main__':unittest.main()
