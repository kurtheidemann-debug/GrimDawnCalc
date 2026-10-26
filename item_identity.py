"""Display names include exactly one prefix/base/suffix; identity is separate."""
import hashlib,json,re

def text(value):
    return re.sub(r'\^[a-zA-Z]|\{\^[^}]+\}|\x1b\[[0-9;]*m','',str(value or '')).strip()

def full_name(item):
    records=item.get('records') or []
    base=(records[0] or {}) if records else {}
    prefix=(records[1] or {}) if len(records)>1 else {}
    suffix=(records[2] or {}) if len(records)>2 else {}
    p=text(prefix.get('lootRandomizerName'));s=text(suffix.get('lootRandomizerName'))
    b=text(base.get('itemNameTag') or base.get('description') or item.get('name'))
    if not b or b.startswith('tag'):
        return text(item.get('name')) or 'Unidentified item (preserve)'
    # Epic/legendary/set unique names do not acquire display affixes.
    if base.get('itemSetName') or base.get('itemClassification') in ['Epic','Legendary']:return b
    return ' '.join(x for x in [p,b,s] if x)

def fingerprint(item):
    saved=item.get('save',{})
    stable={k:saved.get(k) for k in ('basename','prefix-name','suffix-name','seed','modifier-name','ascended-name','transmute-name')}
    return hashlib.sha256(json.dumps(stable,sort_keys=True).encode()).hexdigest()[:12]


def transferable(item, target):
    """Retain target/shared ownership; donor bases must not carry binding flags."""
    if item.get('owner') in [target, 'Shared Stash']:return True
    base=(item.get('records') or [{}])[0] or {}
    return not (base.get('soulbound') or base.get('untradeable'))
