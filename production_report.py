"""Actionable names, validated comparisons, and conservative inventory decisions."""
import copy,json,math,time
from GrimDawn_Optimizer import SLOTS,STORM,WIND,MAEL
from item_identity import full_name,fingerprint
from production_data import physical_key
from production_data import difficulty_name

def safe_name(item):return full_name(item).replace('|','/')

def attachment_action(before,after):
    before=before or '';after=after or ''
    if before==after:return 'Keep'
    if not before:return 'Add'
    if not after:return 'Remove'
    return 'Replace'

def attachment_names(e,before,after):
    def label(record):return (e.name(record) or 'None').replace('|','/') if record else 'None'
    return label(before),label(after)

def item_source(e,item):
    """Report only ownership/location evidence present in this catalog snapshot."""
    owner=item.get('owner');location=item.get('source_location',item.get('location')) or ''
    parts=location.strip('/').split('/')
    detail=''
    if owner=='Shared Stash' and location.startswith('/stash/'):
        detail='Shared stash → Tab '+str(int(parts[1])+1)
    elif location.startswith('/equipment/') and owner:
        index=int(parts[1]);detail=f'{owner} → Equipped → '+(SLOTS[index] if index<len(SLOTS) else str(index))
    elif location.startswith('/weapon-sets/') and owner:
        detail=f'{owner} → Equipped weapon set {int(parts[1])+1} → '+('Main hand' if parts[-1]=='0' else 'Offhand')
    elif location.startswith('/inventory-sacks/') and owner:
        detail=f'{owner} → Inventory bag {int(parts[1])+1}'
    elif location.startswith('/stashes/') and owner:
        detail=f'{owner} → Personal stash tab {int(parts[1])+1}'
    if detail:
        return detail+' → '+location
    return 'Unknown — availability unverified; locate before equipping ('+str(owner)+' '+location+')'


def slot_actions(e,state):
    rows=[]
    for i,ident in enumerate(state['gear']):
        old=e.items[e.current['gear'][i]];new=e.items[ident]
        row={'slot':SLOTS[i],'old':old,'item':new,'equipment':'Keep' if ident==e.current['gear'][i] else 'Replace',
             'component':attachment_action(e.current['comp'][i],state['comp'][i]),
             'augment':attachment_action(e.current['aug'][i],state['aug'][i]),
             'component_names':attachment_names(e,e.current['comp'][i],state['comp'][i]),
             'augment_names':attachment_names(e,e.current['aug'][i],state['aug'][i]),'index':i}
        rows.append(row)
    return rows

def action_checklist(e,state):
    lines=['','## Actions Required',''];changed=False
    for row in slot_actions(e,state):
        if all(row[k]=='Keep' for k in ['equipment','component','augment']):continue
        changed=True;i=row['index'];lines+=['### '+row['slot'],'']
        if row['equipment']=='Replace':
            lines+=['- Replace **'+safe_name(row['old'])+'** (roll `'+fingerprint(row['old'])+'`) with **'+safe_name(row['item'])+'** (roll `'+fingerprint(row['item'])+'`).',
                    '- Location: '+item_source(e,row['item'])+'.']
            source=row['item']['save']
            comp,aug=attachment_names(e,source.get('relic-name'),source.get('augment-name'))
            lines+=['- Replacement item currently carries component **'+comp+'** and augment **'+aug+'**.']
        else:lines+=['- Keep existing equipment: **'+safe_name(row['old'])+'**.']
        for label,key,field in [('component','component','comp'),('augment','augment','aug')]:
            action=row[key];before,after=row[key+'_names']
            if row['equipment']=='Replace':
                sourcekey='relic-name' if field=='comp' else 'augment-name'
                native=row['item']['save'].get(sourcekey) or '';target=state[field][i] or ''
                action=attachment_action(native,target)
                before,after=attachment_names(e,native,target)
            borrowed=row['item'].get('owner') not in [e.character_name,'Shared Stash']
            if borrowed and label=='augment' and after!='None' and action=='Keep':
                lines+=['- Acquire/reapply augment under '+e.character_name+' eligibility: **'+after+'** (source character’s purchase access is not inherited).']
                continue
            if action=='Keep':
                lines+=['- Keep '+('replacement item’s ' if row['equipment']=='Replace' else 'existing ')+label+': **'+after+'**.']
            elif action=='Replace':lines+=['- Replace '+label+': **'+before+'** → **'+after+'**.']
            elif action=='Add':lines+=['- Add '+label+': **'+after+'**.']
            else:lines+=['- Remove '+label+': **'+before+'**.']
        lines+=['']
    if not changed:lines+=['No equipment, component or augment changes required.']
    if any(state['attributes']):
        lines+=['','Attribute points to spend (Physique / Cunning / Spirit): **'+' / '.join(str(x) for x in state['attributes'])+'**.']
    return lines

def item_level(it):return max((r or {}).get('levelRequirement',0) for r in it.get('records',[])[:4])

def familiar(it):
    """Pareto disposal only for simple, fully decoded same-mechanics gear."""
    if not it.get('resolved',True) or not it.get('records') or not it['records'][0]:return False
    s=it['save']
    if any(s.get(k) for k in ['relic-name','augment-name','ascended-name','relic-bonus','modifier-name']):return False
    for r in it['records']:
        if not r:continue
        if r.get('itemSetName') or r.get('itemSkillName') or any(k.startswith(('modifiedSkillName','conversionInType','petBonusName')) and v for k,v in r.items()):return False
    return True


def dominates(e,better,worse):
    if not familiar(better) or not familiar(worse):return False
    a,b=better['save'],worse['save']
    # Match unmodeled mechanics/skill bonuses; compare every modeled numeric roll.
    if better['records'][0].get('Class')!=worse['records'][0].get('Class'):return False
    if better['records'][0].get('Class','').startswith('Weapon') and a.get('basename')!=b.get('basename'):return False
    av0,ab,am,ac=e.item_parts(better['id'],'','');bv0,bb,bm,bc=e.item_parts(worse['id'],'','')
    if am!=bm or ac!=bc or ab!=bb:return False
    av,bv=better.get('worn-rolled') or better['rolled'],worse.get('worn-rolled') or worse['rolled']
    if any(v<0 for v in list(av.values())+list(bv.values()) if isinstance(v,(int,float))):return False
    # Fields whose direction cannot safely be treated as positive invalidate proof.
    if any(any(t in k.lower() for t in ['duration','interval','cost','conversion','cooldown','speedreduction']) for k in set(av)|set(bv)):return False
    if any(av.get(k,0)+1e-8<bv.get(k,0) for k in set(av)|set(bv)):return False
    # Strict ordering prevents two equivalent copies from both being sold.
    if sum(av.values())==sum(bv.values()) and better['id']>=worse['id']:return False
    return all((better.get('requirements') or {}).get(k,0)<=(worse.get('requirements') or {}).get(k,0) for k in ['strength','dexterity','intelligence'])


def disposition(e,selected,unresolved,deadline):
    options=e.options();slots={}
    for i,ids in enumerate(options):
        for ident in ids:slots.setdefault(ident,[]).append(i)
    owned=[x for x in e.cat if x['owner'] in [e.character_name,'Shared Stash']]
    personal=[x for x in owned if x['owner']==e.character_name and not x['location'].startswith('/equipment/') and not x['location'].startswith('/weapon-sets/0/')]+unresolved
    rows=[];chosen=set(selected['gear']) if selected else set();checks=0
    for it in sorted(personal,key=lambda x:(safe_name(x),x['id'])):
        level=item_level(it);name=safe_name(it);reason='';category='Keep for alternative builds'
        if it['id'] in chosen:category='Equip now';reason='Selected in the validated complete loadout.'
        elif not it.get('resolved',True):reason='Protected: '+it.get('unresolved_reason','Incomplete decode')+'. Never marked safe to sell.'
        elif level>e.mal['character-level']:category='Keep for future levels';reason=f'Requires level {level}; retained and reevaluated on every level increase. Future usefulness is not guaranteed.'
        elif it['location'].startswith('/weapon-sets/1/'):reason='Protected alternate weapon set.'
        elif not it['records'][0].get('Class','').startswith(('Armor','Weapon','ItemArtifact')):reason='Protected crafting material, consumable, blueprint or other utility item.'
        elif time.monotonic()>=deadline:reason='Protected: disposal proof deferred by the runtime bound.'
        else:
            better=[x for x in owned if x['id']!=it['id'] and item_level(x)<=e.mal['character-level'] and dominates(e,x,it)]
            # A pair of rings needs two superior physical alternatives, not one.
            need=2 if it['records'][0].get('Class')=='ArmorJewelry_Ring' else 1
            proof=[]
            for alt in sorted(better,key=lambda x:(-sum((x.get('worn-rolled') or {}).values()),x['id'])):
                if time.monotonic()>=deadline:break
                okay=True
                for context in [e.current]+([selected] if selected else []):
                    viable=False
                    for i in slots.get(it['id'],[]):
                        if alt['id'] in context['gear'] and context['gear'][i]!=alt['id']:continue
                        q=copy.deepcopy(context);q['gear'][i]=alt['id'];q['comp'][i]=alt['save'].get('relic-name') or '';q['aug'][i]=alt['save'].get('augment-name') or ''
                        v=e.evaluate(q);checks+=1
                        if not e.legal(q,v,True) and e.equip_order_possible(q):viable=True;break
                    if not viable:okay=False;break
                if okay:proof.append(alt)
                if len(proof)>=need:break
            if len(proof)>=need:
                category='Safe to sell/dismantle under current profile';reason='Compatible gear with matching skill/mechanics signatures, no weaker modeled rolls and no higher requirements; usable alternatives: '+', '.join(safe_name(x) for x in proof[:need])+'. Complete-loadout legality checked.'
            else:
                reason='No safe dominance proof; preserve as an alternative.'
                vals,bon,mods,caps=e.item_parts(it['id'],it['save'].get('relic-name') or '',it['save'].get('augment-name') or '')
                strengths=[]
                if bon['all'] or bon['mastery'] or bon['skill']:strengths.append('skill bonuses')
                if vals.get('offensiveLightningModifier',0) or vals.get('offensiveElementalModifier',0):strengths.append('lightning/elemental support')
                if sum(bool(vals.get(k)) for k in ['defensiveFire','defensiveCold','defensiveLightning','defensivePoison','defensivePierce','defensiveBleeding','defensiveLife','defensiveAether','defensiveChaos'])>=3:strengths.append('multiple resistances')
                if any(r and (r.get('itemSkillName') or r.get('itemSetName')) for r in it['records']):strengths.append('unique skill or set mechanics')
                if strengths:reason+=' Potential role: '+', '.join(strengths)+'.'
                reason+=' Not selected for this loadout.'
        rows.append({'item':name,'fingerprint':fingerprint(it),'id':it['id'],'category':category,'required_level':level,'reason':reason,'source':it['location']})
    return rows,checks


def known_exception(e,config,source_character):
    from production_data import exception_identity
    for ex in config.get('accepted_exceptions',[]):
        chaos=e.evaluate(e.current)['resistances'][8]
        if (e.character_name=='Mal' and exception_identity(source_character)==ex.get('character_digest')
            and e.mal['character-level']==78 and chaos['raw']==105 and chaos['shown']==80):
            return {**ex,'accepted':True,'note':'Decoder 86% is authoritative for this exact baseline display; original optimizer scoring retained.'}
    return None


def report(e,r,path):
    b=r['baseline'];selected=r.get('selected');ex=r.get('accepted_exception');name=e.character_name
    lines=[f'# {name} — Gear Review v1.3.4','',f"Level **{e.mal['character-level']}** · {difficulty_name(e.mal)} · {r['mode'].title()} mode · materiality **{r['materiality_percent']}%**.",'',f"Status: **{r['status']}**. {r.get('scope','')}."]
    if r.get('combat_configuration'):lines+=['','Combat configuration: `'+r['combat_configuration']['selected']+'` ('+r['combat_configuration']['source']+'); reference: current uploaded loadout.']
    if name=='Beeztrap':lines+=['',f"Weapon search: {r.get('eligible_weapon_candidates',0)} eligible supported one-handed melee weapons; {r.get('weapon_pair_configurations_evaluated',0)} distinct ordered physical pairs evaluated. Weapons without validated class/numeric speed inputs are excluded. Pair coverage is bounded by the existing joint attachment shortlists and beam."]
    if r.get('timed_out'):lines+=['','The runtime bound was reached. This is the best fully evaluated feasible loadout retained before the bound.']
    if ex:lines+=['','Accepted baseline exception: **Chaos displays 86% in the decoder, 80% in the optimizer; both have 105% uncapped**. Decoder 86% is authoritative for this exact baseline. The established scoring model is preserved.']
    if selected:lines+=action_checklist(e,selected['state'])
    else:lines+=['','## Actions Required','','No validated replacement loadout; keep current equipment.']
    lines+=['','## Recommended loadout','','Attachment actions compare the currently equipped slot with its recommended configuration. For equipment replacements, the checklist gives the actual attachment work needed on the source item; existing attachments on the old item can stay there.','']
    if not selected:lines+=['**No fully feasible loadout found within the bound.** Keep the current gear pending a wider search; no incomplete state is presented as a recommendation.']
    else:
        s=selected['state'];v=selected['stats']
        lines+=['|Slot|Current full item name|Recommended full item name / roll|Equipment|Source|Component action (existing → recommended)|Augment action (existing → recommended)|','|---|---|---|---|---|---|---|']
        for row in slot_actions(e,s):
            component=row['component']+': '+' → '.join(row['component_names'])
            augment=row['augment']+': '+' → '.join(row['augment_names'])
            source=item_source(e,row['item']) if row['equipment']=='Replace' else 'Already equipped'
            lines.append('|'+ '|'.join([row['slot'],safe_name(row['old']),safe_name(row['item'])+' / `'+fingerprint(row['item'])+'`',row['equipment'],source,component,augment])+'|')
        lines+=['','## Before / after','', '|Metric|Current|Recommended|Change|','|---|---:|---:|---:|']
        for key,label in [('offense_index','Offensive score'),('defense_index','Defensive score'),('OA','OA'),('DA','DA'),('health','Health'),('armor','Armor'),('armor_absorption','Armor absorption (%)'),('cooldown_reduction','Cooldown reduction (%)')]:
            old=b.get(key,100);new=v.get(key,100);lines.append(f'|{label}|{old:.2f}|{new:.2f}|{new-old:+.2f}|')
        if name=='Mal':
            lines+=[f"|Lightning modifier (%)|{b['lightning_modifier']:.1f}|{v['lightning_modifier']:.1f}|{v['lightning_modifier']-b['lightning_modifier']:+.1f}|"]
            for p,label in [(STORM,'Storm Totem effective rank'),(WIND,'Wind Devil effective rank'),(MAEL,'Maelstrom effective rank')]:
                old=b['effective_skills'].get(p,0);new=v['effective_skills'].get(p,0);lines.append(f'|{label}|{old}|{new}|{new-old:+}|')
            lines+=['',f"Expected relative offensive-model change: **{v['offense_index']-100:+.2f}%**. This is a comparison utility, not measured DPS."]
            lines+=['','|Primary ability|Current cooldown|Recommended cooldown|','|---|---:|---:|']
            for p,a in b['offense_model'].get('abilities',{}).items():
                other=v['offense_model'].get('abilities',{}).get(p,{})
                if 'cooldown' in a:lines.append(f"|{a['name']}|{a['cooldown']:.2f}s|{other.get('cooldown',a['cooldown']):.2f}s|")
        else:
            c=selected['standalone_comparison'];lines+=['',f"Cadence direct-offense range: **{c['minimum_index']:.2f}–{c['maximum_index']:.2f}** across all **32 scenarios**. Classification: `{c['classification']}`.",'',f"Uncertainty blockers: {c['blockers'] or 'None detected within the existing scenario envelope.'}"]
            if c['blockers']:lines+=['No certified offensive gain is claimed. The feasible defensive recommendation remains actionable with these limits.']
        lines+=['','|Resistance|Current display|Recommended display|Current uncapped|Recommended uncapped|Recommended overcap|','|---|---:|---:|---:|---:|---:|']
        for i,(old,new) in enumerate(zip(b['resistances'],v['resistances'])):
            shown=ex['decoder_shown'] if ex and i==8 else old['shown']
            same=s==e.current;shown_after=ex['decoder_shown'] if ex and i==8 and same else new['shown']
            margin=f"{new['overcap']:+.1f}%" if i<9 else 'n/a'
            lines.append(f"|{old['name']}|{shown:.0f}%|{shown_after:.0f}%|{old['raw']:.1f}%|{new['raw']:.1f}%|{margin}|")
        if name=='Beeztrap':
            lines+=['','Ultimate preparation (projected uncapped / overcap): '+', '.join(f"{x['name']} {x['raw']:.0f}/{x['overcap']:+.0f}" for x in e.ultimate_rows(v)[:9])+'.']
        trade=[f"{label} {v[key]-b[key]:+.1f}" for key,label in [('health','health'),('DA','DA'),('armor','armor'),('armor_absorption','absorption'),('cooldown_reduction','cooldown reduction')] if v[key]<b[key]-1e-8]
        lines+=['','Tradeoffs: '+('; '.join(trade) if trade else 'No reduction in health, DA, armor or armor absorption.')]
        lines+=['',f"Attribute allocation (Physique / Cunning / Spirit): **{s['attributes'][0]} / {s['attributes'][1]} / {s['attributes'][2]}**; {e.mal['attribute-points']-sum(s['attributes'])} points remain. Only bounded requirement repairs and loadout improvements were considered; no reset."]
        resources=selected['resources'];lines+=['','## Apply the loadout','',f"Equipment changes: {selected['cost']['equipment_changes']}; destroyed attached components: {selected['cost']['destroyed_attached_components']}. Cost utility: {selected['cost']['utility_cost']:.2f} (preference units). Base crafting iron: {resources['craft_iron_base']:g}; base augment iron: {resources['augment_iron_base']:g}. Vendor adjustments/removal fees are additional.",'']
        for p,q in resources['component_need'].items():lines.append(f"- Component: **{e.name(p)} ×{q}**; stock {e.available[p]}, craft batches {resources['crafted_batches'].get(p,0)}.")
        for p,q in resources['augment_purchases'].items():
            f=e.db[p].get('factionSource');fact=next((x['name'] for x in e.factions if x['key']==f),f)
            lines.append(f"- Augment: **{e.name(p)} ×{q}**, {fact}; level {e.db[p].get('levelRequirement',0)}; reputation eligibility checked.")
    lines+=['','Inventory keep/sell processing is suspended; equipment inventory availability is unchanged.']
    lines+=['','## Run checks','',f"Character/save decoded; identity and level checked. Newly rolled items: {r['new_item_rolls']}. Complete-loadout evaluations: {r.get('evaluations',0)}; feasible candidates: {r.get('feasible_candidates',0)}. Elapsed: {r['elapsed_seconds']:.2f}s. Regression suite is reserved for code/database changes."]
    if selected:lines+=['','Winner passed equipment/attachment requirements, level eligibility, unique physical item use, resource checks, fixed skills/devotions/bindings, equipment order, defensive floors, materiality policy and independent offensive recomputation.']
    lines+=['','Assumptions and notices:']
    for note in r.get('notices',[]):lines.append('- '+note)
    lines+=['','No save was modified. All reported scores inherit the verified model’s limits. Item placement and equip order may require removing gear temporarily; a checked equip order exists.']
    path.write_text('\n'.join(lines)+'\n')
