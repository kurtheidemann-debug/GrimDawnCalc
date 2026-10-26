"""Single-slot owned-item valuation, independent of current level admission."""
import copy,math
from GrimDawn_Optimizer import Engine,SLOTS
from item_identity import full_name,fingerprint

def value_owned_equipment(e,unresolved=()):
    # Only candidate enumeration sees level 100. Calculations always use the
    # real character level, fixed progression, attributes and existing formulas.
    view=copy.copy(e);view.mal={**e.mal,'character-level':100}
    all_options=Engine.options(view);now=e.options();baseline=e.evaluate(e.current)
    beez=e.character_name=='Beeztrap';threshold=.03 if beez else .05
    utility=lambda s,v:e.utility(s,v) if beez else e.score(s,v,'balanced')
    base_score=utility(e.current,baseline);rows=[]
    for slot,ids in enumerate(all_options):
        for ident in ids:
            item=e.items[ident]
            if item.get('owner') not in [e.character_name,'Shared Stash']:continue
            level=max((r or {}).get('levelRequirement',0) for r in item['records'][:4])
            row={'id':ident,'item':full_name(item),'fingerprint':fingerprint(item),'slot':SLOTS[slot],
                 'required_level':level,'owner':item.get('owner'),'location':item.get('location'),
                 'future_level':level>e.mal['character-level'],'level_eligible_now':level<=e.mal['character-level'],
                 'current_pool_eligible':ident in now[slot],'compared_to':full_name(e.items[e.current['gear'][slot]]),
                 'classification':'Uncertain','comparison':'No reliable comparison available.',
                 'score':None,'baseline_score':base_score,'offense_index':None,'defense_index':None,'blockers':[]}
            try:
                if not item.get('resolved',True) or item.get('rolled') is None:
                    raise ValueError('Incomplete item rolls or requirements')
                state=copy.deepcopy(e.current);state['gear'][slot]=ident
                # Keep equivalent slot attachments where compatible; otherwise use
                # the item's actual native attachment. No attachment optimization.
                for field,key in [('comp','relic-name'),('aug','augment-name')]:
                    if not e.compatible(state[field][slot],slot,ident):state[field][slot]=item['save'].get(key) or ''
                stats=e.evaluate(state);score=utility(state,stats)
                if not all(math.isfinite(x) for x in [score,stats['offense_index'],stats['defense_index']]):
                    raise ValueError('Non-finite comparison')
                row.update(score=score,offense_index=stats['offense_index'],defense_index=stats['defense_index'],
                           baseline_offense_index=baseline['offense_index'],baseline_defense_index=baseline['defense_index'],
                           attachments={'component':state['comp'][slot],'augment':state['aug'][slot]})
                # Retain the numeric valuation even when non-level legality or
                # supported-mechanics checks prevent a reliable upgrade claim.
                blockers=[x for x in e.legal(state,stats,True) if x!='Level '+ident]
                if beez:
                    blockers+=e.comparisons.get(e.signature(state),{}).get('blockers',[])
                    if slot in [12,13] and ident!=e.current['gear'][slot]:blockers.append('Preserved Cadence weapon lock')
                if not e.equip_order_possible(state):blockers.append('Equipment order/attribute requirements')
                if item.get('requirements') is None:blockers.append('Unknown attribute requirements')
                row['blockers']=list(dict.fromkeys(blockers))
                meaningful=(stats['offense_index']>=baseline['offense_index']*(1+threshold) or stats['defense_index']>=baseline['defense_index']*(1+threshold))
                if blockers:
                    row['comparison']='Uncertain: '+ '; '.join(row['blockers'])
                elif meaningful and score>base_score:
                    row['classification']='Keep — Future Upgrade' if row['future_level'] else 'Superior current-level alternative'
                    row['comparison']=f'Balanced score {score:.6f} vs {base_score:.6f}; offense {stats["offense_index"]:.2f} vs {baseline["offense_index"]:.2f}; defense {stats["defense_index"]:.2f} vs {baseline["defense_index"]:.2f}. Meets {threshold*100:g}% materiality.'
                else:
                    row['classification']='Keep — No demonstrated upgrade' if row['future_level'] else 'No demonstrated upgrade'
                    row['comparison']=f'Balanced score {score:.6f} vs {base_score:.6f}; offense {stats["offense_index"]:.2f}; defense {stats["defense_index"]:.2f}. No material superiority established; not disposal evidence.'
            except (ValueError,KeyError,TypeError,IndexError,ArithmeticError) as exc:
                row['comparison']='Uncertain: '+str(exc);row['blockers']=[str(exc)]
            rows.append(row)
    # Keep unsupported equipment visible rather than silently omitting it or
    # pretending the established archetype can reliably value a different slot.
    seen={row['id'] for row in rows}
    unresolved=list(unresolved)
    for item in e.cat:
        if item['id'] in seen or item.get('owner') not in [e.character_name,'Shared Stash']:continue
        records=item.get('records') or []
        kind=(records[0] or {}).get('Class','') if records else ''
        if kind.startswith(('Armor','Weapon','ItemArtifact')):
            level=max((r or {}).get('levelRequirement',0) for r in records[:4])
            if level<=100:unresolved.append(item)
    for item in unresolved:
        records=item.get('records') or []
        level=max(((r or {}).get('levelRequirement',0) for r in records[:4]),default=0) or None
        rows.append({'id':item['id'],'item':full_name(item),'fingerprint':fingerprint(item),'slot':'Unknown',
                     'required_level':level,'owner':item.get('owner'),'location':item.get('location'),
                     'future_level':level>e.mal['character-level'] if level else None,
                     'level_eligible_now':level<=e.mal['character-level'] if level else False,
                     'current_pool_eligible':False,'classification':'Uncertain','score':None,
                     'comparison':'Uncertain: incomplete decode or equipment outside supported archetype slots; retain, never discard on this evidence.'})
    return rows
