"""Beeztrap-only selection policy. Does not change cadence_scenarios scoring."""
import copy
from cadence_scenarios import CadenceScorer

OFFENSIVE_MATERIALITY_PERCENT = 3.0
INEXPENSIVE_UTILITY_LIMIT = 12.0


def defensively_neutral(candidate, baseline):
    """No loss in core defense or useful resistance headroom (up to +20)."""
    for key in ('health', 'DA', 'armor', 'armor_absorption'):
        if candidate[key] + 1e-8 < baseline[key]:
            return False
    for new, old in zip(candidate['resistances'], baseline['resistances']):
        if new['name'] != old['name']:
            return False
        # Physical resistance has no useful-overcap convention here.
        new_value = new['raw'] if new['name'] == 'Physical' else min(new['raw'], new['cap'] + 20)
        old_value = old['raw'] if old['name'] == 'Physical' else min(old['raw'], old['cap'] + 20)
        if new_value + 1e-8 < old_value:
            return False
    return len(candidate['resistances']) == len(baseline['resistances'])


def apply_policy(comparison, cost, *, sustain_neutral=True):
    result = copy.deepcopy(comparison)
    supported = not result['blockers']
    robust = supported and result['minimum_index'] > 100 + OFFENSIVE_MATERIALITY_PERCENT + 1e-9
    neutral = defensively_neutral(result['candidate_defenses'], result['baseline_defenses']) and sustain_neutral
    cheap = (cost['utility_cost'] <= INEXPENSIVE_UTILITY_LIMIT
             and cost['destroyed_attached_components'] == 0
             and cost['attribute_points_spent'] == 0
             and cost['component_opportunity_cost'] <= 4)
    result['offensive_materiality_percent'] = OFFENSIVE_MATERIALITY_PERCENT
    result['robust_improvement'] = robust
    if supported:
        result['classification'] = 'ROBUST_DIRECT_OFFENSE_IMPROVEMENT' if robust else 'NO_ROBUST_IMPROVEMENT'
    result['defensively_neutral'] = neutral
    result['inexpensive'] = cheap
    result['cost'] = copy.deepcopy(cost)
    result['favor_for_progression'] = robust and neutral and cheap
    result['policy_scope'] = 'Beeztrap only; scorer, scenarios, blockers and Mal unchanged'
    return result


class BeeztrapMateriality(CadenceScorer):
    """Opt-in policy wrapper; no search integration or offense-model changes."""
    def __init__(self, engine):
        if engine.character_name != 'Beeztrap':
            raise ValueError('Three-percent override is restricted to Beeztrap')
        super().__init__(engine)

    def compare(self, candidate, baseline=None):
        result = super().compare(candidate, baseline)
        old = self.e.calculate(self.reference if baseline is None else baseline)
        new = self.e.calculate(candidate)
        sustain = all(new['stats'].get(k, 0) + 1e-8 >= old['stats'].get(k, 0)
                      for k in ('offensiveLifeLeechMin', 'characterLifeRegen', 'characterLifeRegenModifier'))
        return apply_policy(result, self.e.cost(candidate), sustain_neutral=sustain)
