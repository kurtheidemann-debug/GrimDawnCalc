"""Repeatable bounded gear run using previously decoded snapshot."""
import argparse,json,pathlib,time,sys
from practical_optimizer import PracticalEngine,report
p=argparse.ArgumentParser()
p.add_argument('--data',type=pathlib.Path,required=True)
p.add_argument('--out',type=pathlib.Path,default=pathlib.Path('quick-results'))
p.add_argument('--width',type=int,default=4)
p.add_argument('--rounds',type=int,default=1)
a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
t=time.monotonic();e=PracticalEngine(a.data)
v=e.validate();m=[x for x in v if x.get('difference') is not None and x['difference']]
exceptions=[]
for x in m:
 if 'chaos' in str(x).lower() and len(m)==1:
  exceptions.append(x)
 else:
  (a.out/'status.json').write_text(json.dumps({'status':'blocked','mismatches':m},indent=2));sys.exit('Unexpected baseline mismatch')
print('Baseline checked; accepted exceptions:',len(exceptions),flush=True)
r=e.search_practical(a.width,a.rounds);r['validation_exceptions']=exceptions
r['elapsed_total']=round(time.monotonic()-t,1)
r['status']='complete' if r['chosen'] else 'no_feasible_loadout'
(a.out/'results.json').write_text(json.dumps(r,indent=2))
report(e,r,a.out/'Mal_Practical_Results.md')
print('Finished:',r['status'],'in',r['elapsed_total'],'seconds',flush=True)
