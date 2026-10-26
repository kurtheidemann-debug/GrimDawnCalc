"""Read-only save import, incremental seeded rolls, and transactional profiles."""
import copy, functools, gzip, hashlib, json, os, pathlib, shutil, struct, subprocess, tempfile, zipfile
from GrimDawn_Optimizer import ROOT
from item_identity import full_name

FIELDS = ['basename','prefix-name','suffix-name','modifier-name','relic-name','augment-name','relic-bonus','ascended-name']
STATIC = ['database.json.gz','localization.json','guide70.json','guide83.json']
LOCKED = ['skills','skill-points','devotion-points','total-devotion-points-unlocked','hotbars','skill-sets']
PROGRESSION = ['skills','skill-points','devotion-points','total-devotion-points-unlocked']

def progression_missing(character):
    """Fields needed to import ranks, allocations, bindings and budgets together."""
    missing=[]
    for field in PROGRESSION[1:]:
        value=character.get(field)
        if type(value) is not int or value<0:missing.append(field)
    skills=character.get('skills')
    if not isinstance(skills,list) or not skills:
        missing.append('skills');return missing
    for i,skill in enumerate(skills):
        if not isinstance(skill,dict):missing.append(f'skills[{i}]');continue
        types={'skill-name':str,'level':int,'devotion-level':int,'enabled':bool,
               'skill-active':bool,'autocast-skill-name':str,'autocast-controller-name':str}
        for field,kind in types.items():
            value=skill.get(field)
            if type(value) is not kind or (kind is int and value<0) or (field=='skill-name' and not value):
                missing.append(f'skills[{i}].{field}')
    return missing

def import_quick_progression(current,previous,notices):
    """Use one complete progression snapshot; never fill individual missing fields."""
    missing=progression_missing(current)
    source=current
    if missing:
        if progression_missing(previous):
            raise ValueError('Incomplete progression decode; no complete previous snapshot. Missing/unusable fields: '+', '.join(missing))
        source=previous
        notices.append('WARNING: Incomplete progression decode. Missing/unusable fields: '+', '.join(missing)+'. Using the ENTIRE previous progression snapshot (skills, devotions, bindings and unspent points); no new progression fields were mixed in.')
    else:
        notices.append('Current save progression imported authoritatively: skill ranks, devotion allocations and bindings; unspent skill points '+str(current['skill-points'])+', unspent devotion points '+str(current['devotion-points'])+'. Equipment scoring uses this snapshot; no skill or devotion points allocated.')
    for field in PROGRESSION:current[field]=copy.deepcopy(source[field])

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def exception_identity(character):
    keys=['character-name','character-level','physique','cunning','spirit','skills','equipment','last-difficulty','use-alt-weaponset']
    data={k:character.get(k) for k in keys}
    sets=character.get('weapon-sets') or []
    active=1 if character.get('use-alt-weaponset') else 0
    data['active-weapons']=sets[active] if len(sets)>active else None
    return digest(data)

def physical_key(item):
    s=item.get('save',item)
    return digest({k:s.get(k) or '' for k in ['basename','prefix-name','suffix-name','seed','modifier-name','ascended-name','relic-bonus']})

def roll_key(s):
    return digest({k:s.get(k) or '' for k in FIELDS+['seed','relic-seed','relic-completion-level']})

@functools.lru_cache(maxsize=1)
def database():
    with gzip.open(ROOT/'database.json.gz','rt') as f:return json.load(f)


def bridge(request,work,timeout=25):
    work=pathlib.Path(work);work.mkdir(parents=True,exist_ok=True)
    token=digest(request);inp=work/(token+'.request.json');out=work/(token+'.response.json')
    inp.write_text(json.dumps(request))
    proc=subprocess.run(['java','-Xmx'+('3g' if request.get('operation')=='baseline' else '768m'),'-cp',str(ROOT/'gd-edit-standalone.jar'),'clojure.main',str(ROOT/'save_bridge.clj'),str(inp),str(out)],capture_output=True,text=True,timeout=timeout)
    if proc.returncode:raise ValueError('Save decoder failed: '+proc.stderr[-2000:])
    result=json.loads(out.read_text());inp.unlink();out.unlink();return result


def extract_zip(source,destination):
    """Extract only progression files; reject path traversal, duplicates, and bombs."""
    dest=pathlib.Path(destination);seen=set();total=0
    with zipfile.ZipFile(source) as z:
        for info in z.infolist():
            p=pathlib.PurePosixPath(info.filename.replace('\\','/'))
            if p.is_absolute() or '..' in p.parts:raise ValueError('Unsafe ZIP path')
            if info.is_dir():continue
            if p.name!='player.gdc' and p.suffix not in ['.gst','.gdd','.gdc']:continue
            if str(p) in seen:raise ValueError('Duplicate ZIP entry: '+str(p))
            seen.add(str(p));total+=info.file_size
            if info.file_size>32*1024**2 or total>256*1024**2:raise ValueError('Save archive exceeds supported size')
            target=dest/pathlib.Path(*p.parts);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(z.read(info))
    chars=sorted(dest.rglob('player.gdc'))
    if not chars:raise ValueError('No player.gdc character save found')
    stashes=sorted(dest.rglob('transfer.gst'))
    if len(stashes)>1:raise ValueError('Multiple shared stashes; provide one save tree')
    return chars,stashes[0] if stashes else None


def scan_items(value,owner,location=''):
    if isinstance(value,dict):
        if value.get('basename'):
            yield {'owner':owner,'location':location,'save':value};return
        for k,v in value.items():
            if isinstance(v,(list,dict)) and k!='meta-block-list':yield from scan_items(v,owner,location+'/'+k)
    elif isinstance(value,list):
        for i,v in enumerate(value):yield from scan_items(v,owner,location+'/'+str(i))


def resolve_items(raw,previous,work):
    db=database();cache={roll_key(x['save']):x for x in previous if x.get('resolved',True) and x.get('rolled') is not None}
    pending={};records={}
    for x in raw:
        missing=[x['save'].get(f) for f in FIELDS if x['save'].get(f) and x['save'][f] not in db]
        if missing:x['unresolved_reason']='Missing database records: '+', '.join(missing);continue
        key=roll_key(x['save'])
        if key not in cache:
            pending[key]={'key':key,'save':x['save']}
            for f in FIELDS:
                p=x['save'].get(f)
                if p:records[p]=db[p]
    if pending:
        for path,record in db.items():
            if path.startswith('records/game/') or path=='records/creatures/pc/playerlevels.dbr':
                records[path]=record
        for r in bridge({'operation':'roll','items':list(pending.values()),'records':records},work):cache[r['key']]=r
    result=[];occurrences={}
    for x in raw:
        r=cache.get(roll_key(x['save']),{});base=db.get(x['save']['basename'],{})
        x.update({k:copy.deepcopy(r.get(k)) for k in ['rolled','worn-rolled','completion','requirements']})
        x['records']=[db.get(x['save'].get(f)) for f in FIELDS]
        x['resolved']=not x.get('unresolved_reason') and r.get('rolled') is not None and not (r.get('requirements') or {}).get('error')
        if not x['resolved']:x.setdefault('unresolved_reason','Seeded rolls or requirements could not be decoded')
        identity=physical_key(x);n=occurrences.get(identity,0);occurrences[identity]=n+1
        x['id']='I'+identity[:18]+'-'+str(n)
        x['name']=full_name(x);result.append(x)
    return result,len(pending)


def link_static(destination):
    d=pathlib.Path(destination)
    for f in STATIC:
        target=d/f
        if target.exists() or target.is_symlink():target.unlink()
        try:os.link(ROOT/f,target)
        except OSError:shutil.copy2(ROOT/f,target)


def select_character(decoded,requested=None):
    candidates={x['data']['character-name']:x['data'] for x in decoded['characters']}
    if len(candidates)!=len(decoded['characters']):raise ValueError('Duplicate character identities in upload')
    supported=[n for n in candidates if (ROOT/'profiles'/n/'profile.json').exists()]
    if requested:
        if requested not in supported:raise ValueError('Requested profile missing from supplied save: '+requested)
        return requested,candidates
    if len(supported)==1:return supported[0],candidates
    default=json.loads((ROOT/'settings.json').read_text())['default_character']
    if default in supported:return default,candidates
    raise ValueError('No supported character in upload; use a registered profile')


def read_materials(path):
    from reagents import Reader
    r=Reader(path.read_bytes());magic=r.u();block=r.u();size=r.u(False);start=r.p;version=r.u();r.u(False);r.st();count=r.u()
    if magic!=1 or block not in [20,21] or version!=1:raise ValueError('Unsupported material file: '+path.name)
    result=[]
    for _ in range(count):
        r.u();length=r.u(False);pos=r.p;record=r.st();quantity=r.u() if r.p-pos<length else 1
        if r.p-pos!=length:raise ValueError('Invalid material entry')
        chk=struct.unpack_from('<I',r.b,r.p)[0];r.p+=4
        if chk!=r.s:raise ValueError('Material checksum mismatch')
        result.append({'file':path.name,'record':record,'quantity':quantity})
    if r.p-start!=size:raise ValueError('Material block length mismatch')
    chk=struct.unpack_from('<I',r.b,r.p)[0];r.p+=4
    if chk!=r.s or r.p!=len(r.b):raise ValueError('Material file checksum mismatch')
    return result


def stage_profile(name,character,raw_stash,mode,save_root,work):
    source=ROOT/'profiles'/name;d=pathlib.Path(work)/'profiles'/name;shutil.copytree(source,d,ignore=shutil.ignore_patterns(*STATIC))
    config=json.loads((source/'profile.json').read_text());old=json.loads((source/'mal.json').read_text());previous=json.loads((source/'catalog.json').read_text());notices=[]
    m=copy.deepcopy(character)
    if m['character-name']!=name or not 1<=m['character-level']<=100:raise ValueError('Invalid character identity or level')
    if mode=='quick':
        import_quick_progression(m,old,notices)
        for k in ['hotbars','skill-sets']:
            if k not in character and k in old:
                m[k]=copy.deepcopy(old[k]);notices.append('No explicit '+k+' data; retained profile value.')
            elif character.get(k)!=old.get(k):
                notices.append('Explicit saved '+k+' change imported; optimizer keeps the imported configuration fixed.')
        if 'faction-values' not in character:
            m['faction-values']=copy.deepcopy(old['faction-values'])
        elif character['faction-values']!=old['faction-values']:
            notices.append('Explicit saved faction reputation updated; eligible augments recalculated.')
        m['last-difficulty']=(m['last-difficulty']&~3)|config['difficulty']
        notices.append('Shared stash, recipes and crafting resources reused from this profile; explicit character progression takes precedence.')
    else:
        saved_difficulty=int(m['last-difficulty'])&3
        m['last-difficulty']=(m['last-difficulty']&~3)|config['difficulty']
        if saved_difficulty!=config['difficulty']:notices.append('Saved difficulty differs; retained the independent profile optimization target.')
    # Current calculator addresses the active set as weapon-set 0.
    if m.get('use-alt-weaponset'):
        m['weapon-sets'][0],m['weapon-sets'][1]=m['weapon-sets'][1],m['weapon-sets'][0]
        m['use-alt-weaponset']=False;notices.append('Active alternate weapon set normalized for equipment evaluation; source save untouched.')
    raw=list(scan_items(m,name))
    if mode=='full' and raw_stash is not None:raw+=list(scan_items(raw_stash,'Shared Stash'))
    else:raw+=[{'owner':x['owner'],'location':x['location'],'save':x['save']} for x in previous if x['owner']=='Shared Stash']
    catalog,new_count=resolve_items(raw,previous,pathlib.Path(work)/'bridge')
    for x in catalog:
        if x['owner']==name and (x['location'].startswith('/equipment/') or x['location'].startswith('/weapon-sets/0/')) and not x['resolved']:
            raise ValueError('Equipped item is unresolved: '+x['name']+'; '+x['unresolved_reason'])
    (d/'mal.json').write_text(json.dumps(m));(d/'catalog.json').write_text(json.dumps([x for x in catalog if x['resolved']]))
    (d/'unresolved.json').write_text(json.dumps([x for x in catalog if not x['resolved']]))
    from relative_offense import difficulty_penalties
    (d/'penalties.json').write_text(json.dumps(difficulty_penalties(database(),int(m['last-difficulty'])&3)))
    if mode=='full':
        materials=[];availability={}
        for f in ['reagents.gst','potions.gst']:
            paths=list(pathlib.Path(save_root).rglob(f))
            if len(paths)>1:raise ValueError('Multiple '+f+' files')
            availability[f]=bool(paths)
            if paths:materials+=read_materials(paths[0])
        if availability.get('reagents.gst'):(d/'materials.json').write_text(json.dumps(materials))
        else:notices.append('No reagent progression supplied; previous material snapshot retained.')
        formulas=list(pathlib.Path(save_root).rglob('formulas.gst'))
        if formulas:
            import re
            paths=set(re.findall(rb'records/[a-zA-Z0-9_/.-]+\.dbr',formulas[0].read_bytes()))
            recipes=[]
            for p in sorted(x.decode() for x in paths):
                rec=database().get(p)
                if rec and rec.get('artifactName'):recipes.append({'record':p,'definition':rec,'result':database().get(rec['artifactName'])})
            if not recipes:raise ValueError('Supplied formulas.gst did not resolve recipes; refusing to erase known recipes')
            (d/'recipes.json').write_text(json.dumps(recipes))
        else:notices.append('No recipe progression supplied; previous recipe snapshot retained.')
        if raw_stash is None:notices.append('No shared stash supplied; previous stash retained.')
    config.update(reference_level=m['character-level'],revision=config.get('revision',0)+1)
    (d/'profile.json').write_text(json.dumps(config,indent=2));link_static(d)
    return d,config,notices,new_count


def commit_profile(staged,name):
    """Atomic directory swap with rollback; caller holds the workflow lock."""
    source=ROOT/'profiles'/name;backup=ROOT/'profiles'/('.'+name+'.previous')
    if backup.exists():shutil.rmtree(backup)
    source.rename(backup)
    try:
        shutil.copytree(staged,source,symlinks=False,ignore=shutil.ignore_patterns(*STATIC))
        link_static(source)
    except BaseException:
        if source.exists():shutil.rmtree(source)
        backup.rename(source);raise
    shutil.rmtree(backup)
