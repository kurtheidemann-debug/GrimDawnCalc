"""Bounded fixture: python benchmark_search_stage4.py before|after output.json.
Before mode also runs the single optional profiling pass. Not a Full Review.
"""
import sys,copy,time,cProfile,pstats,json,pathlib
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parent))
from production_search import CadenceEngine
from GrimDawn_Optimizer import ROOT

def workload(e,states):
 rows=[]
 for s in states*3:
  v=e.evaluate(s);rows.append((e.signature(s),v,e.legal(s,v,True),e.resources(s),e.feasible_production(s,v),e.utility(s,v)))
 viable=[x for x in rows if x[4]]
 return {'rows':rows,'selected':max(viable,key=lambda x:(x[5],x[0]))[0] if viable else None}
def fixture(e):
 states=[copy.deepcopy(e.current)]
 for i,opts in enumerate(e.options()):
  for ident in opts[:2]:
   q=copy.deepcopy(e.current);q['gear'][i]=ident
   q['comp'][i]=e.items[ident]['save'].get('relic-name') or '';q['aug'][i]=e.items[ident]['save'].get('augment-name') or '';states.append(q)
  for a in [p for p in e.augments if e.compatible(p,i,e.current['gear'][i])][:2]:
   q=copy.deepcopy(e.current);q['aug'][i]=a;states.append(q)
 return states

def run():
 from production_data import link_static
 link_static(ROOT/'profiles/Beeztrap')
 e=CadenceEngine(ROOT/'profiles/Beeztrap');states=fixture(e);e.memo.clear();e.comparisons.clear()
 start=time.perf_counter();result=workload(e,states);elapsed=time.perf_counter()-start
 path=pathlib.Path(sys.argv[2]);path.write_text(json.dumps({'seconds':elapsed,'states':len(states),'requests':len(states)*3,'result':result},sort_keys=True))
 print(sys.argv[1],elapsed,len(states),flush=True)
 if sys.argv[1]=='before':
  e.memo.clear();e.comparisons.clear();p=cProfile.Profile();p.enable();workload(e,states);p.disable();p.dump_stats(str(path.with_suffix('.prof')));pstats.Stats(p).strip_dirs().sort_stats('cumulative').print_stats(30)
if __name__=='__main__':run()
