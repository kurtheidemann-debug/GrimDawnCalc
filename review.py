#!/usr/bin/env python3
"""Upload save.zip -> review. Full progression refresh is explicit: --mode full."""
import argparse, contextlib, copy, hashlib, json, os, pathlib, shutil, sys, tempfile, time
from GrimDawn_Optimizer import ROOT
from production_data import bridge,database,extract_zip,select_character,stage_profile,commit_profile,digest,link_static
from production_search import MalEngine,CadenceEngine,bounded_search,export_seeds
from production_report import report,known_exception

@contextlib.contextmanager
def workflow_lock():
    path=ROOT/'profiles'/'.review.lock';path.parent.mkdir(exist_ok=True)
    with path.open('a+b') as stream:
        try:
            if os.name=='nt':
                import msvcrt
                stream.seek(0);stream.write(b'0');stream.flush();stream.seek(0)
                msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
        except OSError:raise ValueError('Another review is updating profiles; retry after it finishes')
        try:yield
        finally:
            if os.name=='nt':
                stream.seek(0);msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def verify_baseline(e,mode,config,source_character,work):
    exception=known_exception(e,config,source_character);rows=[]
    # Both import modes use current save state. Quick must not bypass a material
    # model discrepancy merely because it reuses account-resource snapshots.
    if mode in ['quick','full']:
        baseline=bridge({'operation':'baseline','database':str(ROOT/'database.json.gz'),'localization':str(ROOT/'localization.json'),'character':str(e.d/'mal.json')},pathlib.Path(work)/'bridge',timeout=90)
        e.exported=baseline;rows=e.validate()
        mismatches=[r for r in rows if r.get('difference')]
        for row in mismatches:
            allowed=(exception and row['stat']=='Chaos resistance shown' and row['exported']==86 and row['calculated']==80)
            if not allowed:raise ValueError('New baseline mismatch: '+json.dumps(row)+'; no accepted exception applies')
        (e.d/'baseline.json').write_text(json.dumps(baseline))
    # Every run checks full imported current state without enforcing defensive floors.
    current=e.evaluate(e.current);errors=e.legal(e.current,current,True)
    if errors:raise ValueError('Imported equipment/build is illegal: '+json.dumps(errors))
    if len(set(e.current['gear']))!=14:raise ValueError('Duplicate equipped item instance')
    if not all(__import__('math').isfinite(current[k]) for k in ['health','OA','DA','armor','armor_absorption']):raise ValueError('Invalid defensive calculation')
    return exception,rows


def perform(source,mode='quick',character=None,out=None,seconds=60,width=5,commit=True):
    start=time.monotonic();out=pathlib.Path(out or ROOT/'reviews'/'latest').resolve();out.mkdir(parents=True,exist_ok=True)
    if seconds<10:raise ValueError('Budget must be at least 10 seconds')
    with workflow_lock(),tempfile.TemporaryDirectory(prefix='gd-review-',dir=ROOT) as tmp:
        work=pathlib.Path(tmp);chars,stash=extract_zip(source,work/'save')
        request={'operation':'decode','characters':[str(p) for p in chars]}
        if mode=='full' and stash:request['stash']=str(stash)
        # Cache only raw read-only decoder output, keyed by every selected byte.
        key=digest({'characters':[(p.relative_to(work/'save').as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in chars],
                    'quests':[(p.relative_to(work/'save').as_posix(),hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted((work/'save').rglob('quests.gdd'))],
                    'stash':hashlib.sha256(stash.read_bytes()).hexdigest() if mode=='full' and stash else None,
                    'decoder':hashlib.sha256((ROOT/'gd-edit-standalone.jar').read_bytes()).hexdigest(),
                    'bridge':hashlib.sha256((ROOT/'save_bridge.clj').read_bytes()).hexdigest()})
        cache=ROOT/'cache'/'decoded';cache.mkdir(parents=True,exist_ok=True);cached=cache/(key+'.json')
        if cached.exists():decoded=json.loads(cached.read_text())
        else:
            decoded=bridge(request,work/'bridge');cached.write_text(json.dumps(decoded))
        selected,candidates=select_character(decoded,character)
        names=[selected] if mode=='quick' or character else [n for n in candidates if (ROOT/'profiles'/n/'profile.json').exists()]
        updates=[];all_results={}
        for name in names:
            staged,config,notices,new_count=stage_profile(name,candidates[name],decoded.get('stash'),mode,work/'save',work,candidates)
            if len(candidates)>1 and character is None and mode=='quick':notices.append('Multiple characters uploaded; selected persistent default '+name+'. Use --character to select another profile.')
            e=(MalEngine if name=='Mal' else CadenceEngine)(staged)
            exception,validation=verify_baseline(e,mode,config,candidates[name],work)
            if exception and name=='Mal':
                e.minimum_chaos_raw=exception['decoder_cap']
                notices.append('For this accepted baseline, uncapped Chaos must reach at least 86% in every feasible recommendation. Other candidate caps are not inferred from the exception.')
            baseline=e.evaluate(e.current)
            # Reserve reporting and final validation time. Full mode intentionally wider.
            deadline=(start+seconds-6) if mode=='quick' else time.monotonic()+seconds
            result=bounded_search(e,deadline,width=width,rounds=1 if mode=='quick' else 3,full=mode=='full')
            winner=result.get('selected');state=winner['state'] if winner else None
            result.update(version='1.3.4',character=name,level=e.mal['character-level'],mode=mode,baseline=baseline,baseline_state=e.current,accepted_exception=exception,baseline_validation=validation,materiality_percent=config['materiality']*100,notices=notices,new_item_rolls=new_count,inventory_disposition='suspended',elapsed_seconds=time.monotonic()-start,profile_revision=config['revision'])
            result['equipment_sources']=[{'id':item['id'],'owner':item['owner'],
                'location':item.get('source_location',item['location']),'save':item['save']}
                for item in e.cat if winner and item['id'] in winner['state']['gear']]
            if winner:
                # Report independent fixed state and source fingerprints, no save writes.
                assert all(winner['state'][k]==e.current[k] for k in ['skills','devotions','bindings'])
                seeds=export_seeds(e,[winner['state']]);(staged/'seeds.json').write_text(json.dumps(seeds))
            # Snapshot current baseline separately; never pass this self-calculation off as an independent export.
            (staged/'current_calculated_baseline.json').write_text(json.dumps(baseline))
            target=out if len(names)==1 else out/name;target.mkdir(parents=True,exist_ok=True)
            # Remove a stale report from an earlier run; valuation code stays available.
            (target/(name+'_Inventory_Disposition.md')).unlink(missing_ok=True)
            report(e,result,target/(name+'_Gear_Review.md'));(target/'results.json').write_text(json.dumps(result,indent=2));all_results[name]=result;updates.append((staged,name))
        if commit:
            for staged,name in updates:commit_profile(staged,name)
        (out/'status.json').unlink(missing_ok=True)
        return all_results


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('save',type=pathlib.Path);p.add_argument('--mode',choices=['quick','full'],default='quick');p.add_argument('--character',choices=['Mal','Beeztrap']);p.add_argument('--out',type=pathlib.Path);p.add_argument('--seconds',type=float,default=60);p.add_argument('--width',type=int,default=5);p.add_argument('--no-commit',action='store_true');a=p.parse_args()
    try:
        from validate import ensure_software
        ensure_software()
        result=perform(a.save.resolve(),a.mode,a.character,a.out,a.seconds,a.width,not a.no_commit)
        for name,r in result.items():print(f"{name}: {r['status']} — level {r['level']}, {r['feasible_candidates']} feasible, {r['elapsed_seconds']:.2f}s",flush=True)
    except Exception as ex:
        out=pathlib.Path(a.out or ROOT/'reviews'/'latest');out.mkdir(parents=True,exist_ok=True)
        (out/'status.json').write_text(json.dumps({'status':'blocked','error':str(ex),'version':'1.3'},indent=2));print('Review blocked: '+str(ex),file=sys.stderr);return 2
    return 0
if __name__=='__main__':raise SystemExit(main())
