"""Disposition only: item value and equipment eligibility are independent."""
import copy,math

def assess(e,row):
    item=e.items.get(row['id']);blockers=list(row.get('blockers',[]))
    eligibility=('Future Level' if row.get('future_level') else 'Unknown' if not item or item.get('requirements') is None else 'Attribute/Equipment Dependency' if blockers else 'Equippable Now')
    result={'item_value':'Insufficient Data','equipment_eligibility':eligibility,
            'eligibility_blockers':blockers,'disposition':'Uncertain — Value',
            'value_reason':'Incomplete or unsupported item valuation; retain.'}
    if not item or any(row.get(k) is None or not math.isfinite(row[k]) for k in ['score','baseline_score','offense_index','defense_index']):return result
    # These are value-model limitations, unlike attribute/resource/order gates.
    value_limits=[x for x in blockers if any(t in x.lower() for t in ['unsupported','scenario','direct-offense envelope','cadence weapon lock','dot, crit'])]
    if value_limits:
        result['value_reason']='Isolated valuation is unreliable: '+'; '.join(value_limits);return result
    slot=__import__('GrimDawn_Optimizer').SLOTS.index(row['slot'])
    state=copy.deepcopy(e.current);state['gear'][slot]=row['id']
    state['comp'][slot]=row['attachments']['component'];state['aug'][slot]=row['attachments']['augment']
    stats=e.evaluate(state);base=e.evaluate(e.current)
    gains=[];losses=[]
    for key,label in [('OA','OA'),('DA','DA'),('health','health'),('armor','armor'),('armor_absorption','armor absorption'),('cooldown_reduction','cooldown reduction')]:
        delta=stats[key]-base[key]
        if delta>1e-7:gains.append(f'{label} +{delta:g}')
        elif delta< -1e-7:losses.append(f'{label} {delta:g}')
    for a,b in zip(stats['resistances'],base['resistances']):
        # Do not call excess overcaps a meaningful alternative indefinitely.
        if min(a['raw'],a['cap']+20)>min(b['raw'],b['cap']+20)+1e-7:gains.append(a['name']+' resistance tradeoff')
    new,bon,mods,caps=e.item_parts(item['id'],'','')
    old,oldbon,oldmods,oldcaps=e.item_parts(e.current['gear'][slot],'','')
    for key in ['offensiveLightningModifier','offensiveElementalModifier','offensiveLightningMin','offensiveLightningMax']:
        if new.get(key,0)>old.get(key,0)+1e-7:gains.append('relevant lightning/elemental support')
    # Only bonuses to actual current skills/masteries establish build synergy.
    if any(stats['effective_skills'].get(p,0)>base['effective_skills'].get(p,0) for p in e.current['skills']):gains.append('relevant skill rank improvement')
    relevant=set(e.current['skills'])|set(e.current['devotions'])
    special=[]
    for record in item.get('records',[]):
        if not record:continue
        if record.get('itemSetName'):
            companions={x['save'].get('basename') for x in e.cat if x['id']!=item['id'] and x.get('records') and (x['records'][0] or {}).get('itemSetName')==record['itemSetName'] and x['save'].get('basename')!=item['save'].get('basename')}
            if companions:special.append('owned multi-piece set interaction not compared as a configuration')
        if record.get('itemSkillName'):
            granted=e.db.get(record['itemSkillName'],{})
            if granted.get('Class') not in ['Skill_Passive','Skill_BuffSelfToggled','Skill_BuffAttackRadiusToggled','Skill_BuffRadiusToggled']:
                special.append('conditional item skill/proc '+str(record['itemSkillName'])+' outside the existing fixed-ability score')
        if any(k.startswith('modifiedSkillName') and v in relevant for k,v in record.items()):gains.append('modifier to an actual saved skill')
        # Existing calculators already include persistent item buffs, ordinary
        # damage conversion and current set bonuses. Their presence is not itself
        # missing data. Pet-only bonuses are not synergy for player-scaled totems.
        if record.get('petBonusName') and any(x.get('scaling')=='pet' for x in base.get('offense_model',{}).get('abilities',{}).values()):special.append('pet interaction outside isolated comparison')
    off=row['offense_index'];defense=row['defense_index'];bo=row.get('baseline_offense_index',100);bd=row.get('baseline_defense_index',100)
    comparison=f'Balanced {row["score"]:.4f} vs {row["baseline_score"]:.4f}; offense {off:.2f} vs {bo:.2f}; defense {defense:.2f} vs {bd:.2f}.'
    # Reuse the existing character comparison envelope from PracticalEngine
    # prefer / the Cadence production shortlist, not a new retention cutoff.
    if e.character_name=='Beeztrap':
        comparable=off>=.97*bo and all(stats[k]>=.95*base[k] for k in ['health','DA','armor'])
        policy='existing Cadence 3% offense / 5% health, DA and armor comparison envelope'
    else:
        comparable=off>=.95*bo and defense>=.95*bd and all(stats[k]>=.95*base[k] for k in ['health','DA','armor_absorption']) and stats['armor']>=.9*base['armor']
        policy='existing 5% offense/defense, health, DA and absorption / 10% armor comparison envelope'
    gain_text=', '.join(dict.fromkeys(gains)) or 'no isolated improvement'
    loss_text=', '.join(losses) or 'no reduction in displayed core defensive metrics'
    breakpoint=[]
    old_abilities=base.get('offense_model',{}).get('abilities',{})
    for skill,ability in stats.get('offense_model',{}).get('abilities',{}).items():
        old=old_abilities.get(skill,{})
        maximum=ability.get('population',{}).get('maximum');previous=old.get('population',{}).get('maximum')
        if maximum is not None and previous is not None and maximum!=previous:
            breakpoint.append(f'{ability.get("name",skill)} maximum instances {previous:g} → {maximum:g}')
    tradeoffs=' Benefits: '+gain_text+'. Costs: '+loss_text+'.'+(' Skill breakpoint: '+'; '.join(breakpoint)+'.' if breakpoint else '')
    if off>=bo-1e-7 and defense>=bd-1e-7 and row['score']>row['baseline_score']+1e-7 and not special:
        result.update(item_value='Superior',disposition='Keep — Future Upgrade' if row.get('future_level') else 'Keep — Upgrade' if eligibility=='Equippable Now' else 'Keep — Alternative',value_reason=comparison+' Superior with fixed current progression.')
    elif comparable and not special:
        result.update(item_value='Competitive / Plausible Alternative',disposition='Keep — Alternative',value_reason=comparison+' Competitive net configuration within '+policy+'.'+tradeoffs)
    elif special:
        result['value_reason']=comparison+' Isolated comparison cannot resolve '+', '.join(dict.fromkeys(special))+'.'
    elif not comparable and row['score']<row['baseline_score']-1e-7:
        result.update(item_value='Inferior',disposition='Sell/Dismantle',value_reason=comparison+' Net tradeoff is worse and outside '+policy+'; isolated benefits do not compensate.'+tradeoffs+' Eligibility did not determine value.')
    elif row['score']>row['baseline_score']+1e-7:
        result.update(item_value='Competitive / Plausible Alternative',disposition='Keep — Alternative',value_reason=comparison+' The existing Balanced scorer favors this complete single-slot configuration despite its tradeoff.'+tradeoffs)
    else:
        result['value_reason']=comparison+' Neither competitive net value nor reliable inferiority is established by the existing comparison.'+tradeoffs
    return result

def apply_dispositions(e,valuations,inventory,selected=None):
    groups={}
    for row in valuations:
        decoded=e.items.get(row['id'])
        if decoded:
            style=(decoded['records'][0] or {}).get('itemStyleTag','')
            if style and not row['item'].startswith(style+' '):row['item']=style+' '+row['item']
        row.update(assess(e,row));row['classification']=row['disposition'];row['comparison']=row['value_reason']
        groups.setdefault(row['id'],[]).append(row)
    chosen=set(selected['gear']) if selected else set()
    for item in inventory:
        choices=groups.get(item['id'],[])
        # Rings and interdependent slots are sellable only if every comparison
        # independently establishes inferior value.
        best=next((x for x in choices if x['item_value']=='Superior'),None) or next((x for x in choices if x['item_value']=='Competitive / Plausible Alternative'),None) or next((x for x in choices if x['item_value']=='Insufficient Data'),None) or (choices[0] if choices else None)
        if best:item.update({k:best[k] for k in ['item_value','equipment_eligibility','eligibility_blockers','disposition','value_reason']})
        else:item.update(item_value='Competitive / Plausible Alternative',equipment_eligibility='Unknown',eligibility_blockers=[],disposition='Keep — Alternative',value_reason=item.get('reason','Protected utility item; no equipment comparison.'))
        if item['id'] in chosen:item.update(disposition='Keep — Upgrade' if item['item_value']=='Superior' else 'Keep — Alternative',value_reason='Selected in the validated current loadout. '+item['value_reason'])
        item.update(category=item['disposition'],reason=item['value_reason'])
    return inventory

def disposition_rows(e,valuations,inventory,selected=None):
    groups={}
    for row in valuations:groups.setdefault(row['id'],[]).append(row)
    rows={row['id']:dict(row) for row in inventory}
    for ident,choices in groups.items():
        best=next((x for x in choices if x['item_value']=='Superior'),None) or next((x for x in choices if x['item_value']=='Competitive / Plausible Alternative'),None) or next((x for x in choices if x['item_value']=='Insufficient Data'),None) or choices[0]
        if ident not in rows:rows[ident]={**best,'reason':best['value_reason'],'source':best.get('location','')}
        rows[ident]['item']=best['item']
    chosen=set(selected['gear']) if selected else set()
    for ident,row in rows.items():
        if ident in chosen or ident in e.current['gear']:
            row['disposition']='Keep — Upgrade' if row['item_value']=='Superior' and row['equipment_eligibility']=='Equippable Now' else 'Keep — Alternative'
            row['reason']='Selected recommendation or currently equipped; retain. '+row.get('reason',row.get('value_reason',''))
    return sorted(rows.values(),key=lambda x:(x['disposition'],x['item'],x['id']))

def write_inventory_report(e,result,path):
    from collections import Counter
    from production_report import item_source
    rows=disposition_rows(e,result['item_valuations'],result['inventory'],result['selected']['state'] if result.get('selected') else None)
    counts=dict(Counter(row['disposition'] for row in rows))
    lines=[f'# {e.character_name} — Inventory disposition v1.3.5','',f'Current level: {e.mal["character-level"]}. All owned equipment through level 100 plus personal inventory/utility items; cached shared stash included. Each physical item counted once.','',
           'Value and eligibility are separate. Ineligibility never proves inferior value. Existing scores use fixed current progression; no future build is simulated.','',
           '|Disposition|Count|','|---|---:|']
    for key,count in sorted(counts.items()):lines.append(f'|{key}|{count}|')
    lines+=['',f'Total: **{len(rows)}** items.','', '|Full item name / fingerprint|Location|Item value|Equipment eligibility|Disposition|Value reason / comparison|Eligibility blockers|','|---|---|---|---|---|---|---|']
    for row in rows:
        item=e.items.get(row['id'],row)
        cells=[row['item']+' / `'+row.get('fingerprint','unknown')+'`',item_source(e,item),row['item_value'],row['equipment_eligibility'],row['disposition'],row.get('reason',row.get('value_reason','')), '; '.join(row['eligibility_blockers']) or 'None']
        lines.append('|'+ '|'.join(str(x).replace('|','/') for x in cells)+'|')
    path.write_text('\n'.join(lines)+'\n')
    return counts,rows
