"""Weapon structure is independent of skill scoring; capabilities stay explicit."""
import math
CONFIGURATIONS=('dual_wield_melee','one_hand_shield','two_hand_melee','one_hand_caster_offhand','ranged')
CADENCE_MELEE={'WeaponMelee_Sword','WeaponMelee_Axe','WeaponMelee_Mace'}
ONE_HAND=CADENCE_MELEE|{'WeaponMelee_Dagger','WeaponMelee_Scepter'}
MODULE_CONFIGURATIONS={'cadence':{'dual_wield_melee'},'totem':{'one_hand_caster_offhand'}}

def configuration_for_classes(main,off):
    if main in ONE_HAND and off in ONE_HAND:return 'dual_wield_melee'
    if main in ONE_HAND and off=='WeaponArmor_Shield':return 'one_hand_shield'
    if main in ONE_HAND and off=='WeaponArmor_Offhand':return 'one_hand_caster_offhand'
    if main.startswith('WeaponMelee_') and main.endswith('2h') and not off:return 'two_hand_melee'
    if main.startswith('WeaponHunting_'):
        if main.endswith('2h') and not off:return 'ranged'
        if main.endswith('1h') and (not off or off=='WeaponHunting_Ranged1h' or off in ['WeaponArmor_Shield','WeaponArmor_Offhand']):return 'ranged'
    raise ValueError(f'Unrecognized active weapon configuration: {main or "empty"} + {off or "empty"}')

def detect_configuration(character,db):
    active=1 if character['use-alt-weaponset'] else 0
    items=character['weapon-sets'][active]['items']
    return configuration_for_classes(*(db.get(x.get('basename'),{}).get('Class','') for x in items))

def resolve_configuration(character,db,module,override=None):
    if override is not None and override not in CONFIGURATIONS:raise ValueError('Unknown combat configuration: '+override)
    detected=detect_configuration(character,db);requested=override or detected
    if requested not in MODULE_CONFIGURATIONS.get(module,set()):
        raise ValueError(f'Scoring module {module} does not support configuration {requested}; no recommendation generated')
    if requested!=detected:
        raise ValueError(f'Cannot establish a validated {requested} reference from saved {detected}: {module} has no validated cross-configuration reference builder; no optimization or attachment changes generated')
    return {'detected':detected,'selected':requested,'source':'override' if override else 'active_save','reference':'current_uploaded_loadout'}

def cadence_weapon_reason(item):
    base=(item.get('records') or [{}])[0] or {}
    if base.get('Class') not in CADENCE_MELEE:return 'Cadence supports one-handed melee swords, axes and maces only'
    rolled=item.get('worn-rolled') or item.get('rolled') or {}
    speed=rolled.get('characterBaseAttackSpeed',base.get('characterBaseAttackSpeed'))
    if type(speed) not in [int,float] or not math.isfinite(speed) or speed<=-1:
        return 'Missing or invalid numeric weapon base-speed adjustment; display speed tags are not a substitute'
    return None

def filter_options(e,opts,configuration):
    """Filter the existing admitted pool; never add inventory or rank weapons."""
    admitted=list(dict.fromkeys(opts[12]+opts[13]))
    def kind(i):return e.items[i]['records'][0].get('Class','')
    if configuration=='dual_wield_melee':
        one=[i for i in admitted if kind(i) in ONE_HAND];opts[12]=one;opts[13]=one[:]
    elif configuration in ['one_hand_shield','one_hand_caster_offhand']:
        opts[12]=[i for i in admitted if kind(i) in ONE_HAND]
        off='WeaponArmor_Shield' if configuration=='one_hand_shield' else 'WeaponArmor_Offhand'
        opts[13]=[i for i in admitted if kind(i)==off]
    elif configuration=='two_hand_melee':
        # Core candidate enumeration does not yet admit 2H/empty combinations.
        raise ValueError('Two-handed configuration requires an unimplemented scoring/search adapter')
    elif configuration=='ranged':raise ValueError('Ranged configuration requires an unimplemented scoring/search adapter')
    return opts
