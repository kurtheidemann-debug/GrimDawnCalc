"""Focused save-authority checks; no equipment search.

Unit tests: python -m unittest test_stage2 -v
Save acceptance: GD_STAGE2_SAVE=/absolute/save.zip python -m unittest test_stage2 -v
The optional save stays private; no uploaded character fixture is committed.
"""
import copy
import gc
import hashlib
import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

import GrimDawn_Optimizer as core
import production_data as data
from production_search import CadenceEngine, MalEngine
from relative_offense import difficulty_penalties
from review import verify_baseline

ROOT = Path(__file__).resolve().parent


def minimal_character():
    item = {'basename': ''}
    return {'character-name': 'Beeztrap', 'character-level': 76,
            'physique': 378., 'cunning': 226., 'spirit': 114., 'iron': 560873,
            'last-difficulty': 2, 'use-alt-weaponset': False,
            'attribute-points': 6, 'skill-points': 2, 'devotion-points': 0,
            'total-devotion-points-unlocked': 55,
            'skills': [{'skill-name': 'records/skills/playerclass01/cadence1.dbr',
                        'level': 8, 'devotion-level': 0, 'enabled': True,
                        'skill-active': False, 'autocast-skill-name': '',
                        'autocast-controller-name': ''}],
            'equipment': [dict(item) for _ in range(12)],
            'weapon-sets': [{'items': [dict(item), dict(item)]} for _ in range(2)],
            'faction-values': [{'faction-value': 16104.879}],
            'inventory-sacks': [], 'stashes': []}


class CurrentStateTests(unittest.TestCase):
    def test_complete_save_and_difficulty_flags(self):
        c = minimal_character()
        for difficulty, label in enumerate(['Normal', 'Elite', 'Ultimate']):
            c['last-difficulty'] = difficulty | 8
            data.require_current_state(c)
            self.assertEqual(data.difficulty_name(c), label)

    def test_missing_state_never_falls_back(self):
        for field in ['skills', 'skill-points', 'devotion-points',
                      'total-devotion-points-unlocked', 'attribute-points',
                      'physique', 'cunning', 'spirit', 'last-difficulty',
                      'faction-values', 'equipment', 'weapon-sets', 'use-alt-weaponset']:
            with self.subTest(field=field):
                c = minimal_character(); del c[field]
                with self.assertRaisesRegex(ValueError, 'no historical fallback'):
                    data.require_current_state(c)

    def test_nonfinite_and_invalid_difficulty_rejected(self):
        for key, value in [('physique', float('nan')), ('last-difficulty', 3),
                           ('faction-values', [{'faction-value': float('inf')}])]:
            c = minimal_character(); c[key] = value
            with self.assertRaises(ValueError): data.require_current_state(c)

    def test_missing_binding_field_is_not_a_historical_binding(self):
        c = minimal_character(); del c['skills'][0]['autocast-skill-name']
        with self.assertRaisesRegex(ValueError, 'autocast-skill-name'):
            data.require_current_state(c)

    def test_unversioned_roll_cache_cannot_hide_completion_bonus(self):
        saved = {'basename': 'relic', 'seed': 1, 'modifier-name': 'bonus'}
        raw = [{'owner': 'Beeztrap', 'location': '/equipment/11', 'save': saved}]
        stale = [dict(raw[0], rolled={}, completion={}, requirements={})]
        fresh = {'key': data.roll_key(saved), 'rolled': {}, 'worn-rolled': {},
                 'completion': {'characterOffensiveAbilityModifier': 2.}, 'requirements': {}}
        with patch.object(data, 'database', return_value={'relic': {}, 'bonus': {}}), \
             patch.object(data, 'roll_source_fingerprint', return_value='current'), \
             patch.object(data, 'bridge', return_value=[fresh]) as decode:
            items, count = data.resolve_items(copy.deepcopy(raw), stale, Path('unused'))
            self.assertEqual(count, 1); decode.assert_called_once()
            self.assertEqual(items[0]['completion'], fresh['completion'])
            self.assertEqual(items[0]['roll_source'], 'current')
            # Matching provenance plus exact saved roll key is reusable static derivation.
            with patch.object(data, 'bridge', side_effect=AssertionError('unexpected decode')):
                again, count = data.resolve_items(copy.deepcopy(raw), items, Path('unused'))
                self.assertEqual(count, 0); self.assertEqual(again[0]['completion'], fresh['completion'])

    def test_baseline_mismatch_still_blocks(self):
        class Mismatch:
            def validate(self): return [{'stat': 'OA', 'exported': 2025,
                                         'calculated': 1991, 'difference': -34}]
        with tempfile.TemporaryDirectory() as tmp:
            e = Mismatch(); e.d = Path(tmp)
            with patch('review.known_exception', return_value=None), patch('review.bridge', return_value={}):
                for mode in ['quick', 'full']:
                    with self.assertRaisesRegex(ValueError, 'New baseline mismatch'):
                        verify_baseline(e, mode, {}, {}, tmp)

    def test_report_uses_normal_label(self):
        from types import SimpleNamespace
        from production_report import report
        e = SimpleNamespace(character_name='Mal', mal={'character-level':76,'last-difficulty':0})
        r = {'baseline':{},'selected':None,'mode':'quick','materiality_percent':5,
             'status':'blocked','inventory':[],'item_valuations':[],
             'new_item_rolls':0,'elapsed_seconds':0}
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'report.md'; report(e,r,p)
            self.assertIn('· Normal ·', p.read_text())


@unittest.skipUnless(os.environ.get('GD_STAGE2_SAVE'), 'Set GD_STAGE2_SAVE for private save acceptance')
class Save9AcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='gd-stage2-')
        cls.work = Path(cls.tmp.name)
        cls.save = Path(os.environ['GD_STAGE2_SAVE']).resolve()
        cls.before = hashlib.sha256(cls.save.read_bytes()).hexdigest()
        paths, stash = data.extract_zip(cls.save, cls.work/'save')
        decoded = data.bridge({'operation': 'decode', 'characters': [str(p) for p in paths],
                               'stash': str(stash)}, cls.work/'bridge', timeout=180)
        for name in ['Beeztrap','Mal']:
            selected, candidates = data.select_character(decoded, name)
            if selected != name or candidates[name]['character-name'] != name:
                raise AssertionError('Requested character not selected')
        cls.decoded = {x['data']['character-name']: x['data'] for x in decoded['characters']}
        cls.stash = decoded['stash']; cls.db = data.database()
        cls.real_read = core.read
        # Share the immutable game database in tests; no scorer or stat formula is mocked.
        cls.reader = patch.object(core, 'read', side_effect=lambda p: cls.db if Path(p).name == 'database.json.gz' else cls.real_read(p))
        cls.reader.start()
        cls.fake = cls.work/'stale-profiles'; cls.fake.mkdir()
        for f in data.STATIC+['gd-edit-standalone.jar','save_bridge.clj']: (cls.fake/f).symlink_to(ROOT/f)
        cls.staged = {}
        for name in ['Beeztrap', 'Mal']:
            source = cls.fake/'profiles'/name
            shutil.copytree(ROOT/'profiles'/name, source, ignore=shutil.ignore_patterns(*data.STATIC))
            # Poison every historical character value, including stale difficulty and progression.
            old = minimal_character(); old.update({'character-name': name, 'character-level': 1,
                   'physique': 99999., 'cunning': 99999., 'spirit': 99999., 'attribute-points': 99,
                   'last-difficulty': 0, 'skill-points': 99, 'stale-only': 'must not leak'})
            (source/'mal.json').write_text(json.dumps(old))
            config = json.loads((source/'profile.json').read_text()); config['difficulty'] = 0
            (source/'profile.json').write_text(json.dumps(config))
            # Full mode recomputes the unversioned historical rolls. Quick reuses only those verified derivations.
            for mode in ['full', 'quick']:
                with patch.object(data, 'ROOT', cls.fake):
                    staged, config, notices, count = data.stage_profile(name, cls.decoded[name], cls.stash,
                                mode, cls.work/'save', cls.work/mode)
                cls.staged[name, mode] = (staged, config, notices)
                if mode == 'full': shutil.copy2(staged/'catalog.json', source/'catalog.json')

    @classmethod
    def tearDownClass(cls):
        cls.reader.stop(); cls.tmp.cleanup(); gc.collect()

    def engine(self, name, mode='full'):
        return (CadenceEngine if name == 'Beeztrap' else MalEngine)(self.staged[name, mode][0])

    def test_selected_identity_level_attributes_and_points(self):
        for name, level in [('Beeztrap', 76), ('Mal', 87)]:
            for mode in ['quick', 'full']:
                e = self.engine(name, mode); c = self.decoded[name]
                self.assertEqual(e.character_name, name); self.assertEqual(e.mal['character-level'], level)
                for key in ['physique','cunning','spirit','attribute-points','skill-points','faction-values']:
                    self.assertEqual(e.mal[key], c[key], (name, mode, key))
                self.assertNotIn('stale-only', e.mal)
                del e

    def test_current_build_equipment_attachments_and_progression(self):
        for name in ['Beeztrap', 'Mal']:
            for mode in ['quick', 'full']:
                e = self.engine(name, mode); c = self.decoded[name]
                for key in ['skills','devotion-points','total-devotion-points-unlocked','hotbars','skill-sets','quest-progress']:
                    self.assertEqual(e.mal[key], c[key], (name, mode, key))
                for i, ident in enumerate(e.current['gear']):
                    expected = c['equipment'][i] if i < 12 else c['weapon-sets'][0]['items'][i-12]
                    self.assertEqual(e.items[ident]['save'], expected)
                    self.assertEqual(e.current['comp'][i], expected.get('relic-name',''))
                    self.assertEqual(e.current['aug'][i], expected.get('augment-name',''))
                self.assertEqual(len(e.current['devotions']), 55)
                self.assertEqual(len(e.current['bindings']), 6)
                self.assertEqual(set(c['quest-progress']), {'normal','elite','ultimate'})
                del e

    def test_independent_baseline_and_material_calibration_guard(self):
        for name in ['Beeztrap', 'Mal']:
            e = self.engine(name); directory, config, notices = self.staged[name, 'full']
            for mode in ['full','quick']:
                exception, rows = verify_baseline(e, mode, config, self.decoded[name], self.work)
                self.assertIsNone(exception)
                self.assertFalse([r for r in rows if r.get('difference')])
            self.assertEqual(e.evaluate(e.current)['OA'], 2025 if name == 'Beeztrap' else 2581)
            chaos=next(x for x in e.evaluate(e.current)['resistances'] if x['name']=='Chaos')
            self.assertEqual(chaos['cap'],80 if name=='Beeztrap' else 86)
            del e

    def test_saved_ultimate_penalties_and_feasibility(self):
        for name in ['Beeztrap','Mal']:
            for mode in ['full','quick']:
                e = self.engine(name, mode)
                self.assertEqual(e.mal['last-difficulty'] & 3, 2); self.assertTrue(e.target_ultimate)
                self.assertEqual(e.pen, difficulty_penalties(self.db, 2))
                if name == 'Beeztrap':
                    v = e.evaluate(e.current)
                    self.assertEqual([x['shown'] for x in v['resistances'][:3]], [68,64,68])
                    self.assertFalse(e.feasible_production(e.current,v))
                del e

    def test_actual_silver_and_salt_cap_contributions(self):
        e=self.engine('Mal');s=copy.deepcopy(e.current)
        self.assertEqual([e.name(s['comp'][i]) for i in [12,13]],['Imbued Silver','Imbued Silver'])
        for i in [12,13]:
            self.assertEqual(e.item_parts(s['gear'][i],s['comp'][i],s['aug'][i])[3]['defensiveChaos'],3)
        for removed,expected in [(0,86),(1,83),(2,80)]:
            q=copy.deepcopy(s)
            for i in [12,13][:removed]:q['comp'][i]=''
            chaos=next(r for r in e.calculate(q)['resistances'] if r['name']=='Chaos')
            self.assertEqual(chaos['cap'],expected)
            self.assertEqual(chaos['raw'],108-20*removed)
        q=copy.deepcopy(s)
        for i in [12,13]:q['comp'][i]='records/items/materia/compa_purifiedsalt.dbr'
        rows=e.calculate(q)['resistances']
        self.assertEqual(next(r for r in rows if r['name']=='Aether')['cap'],86)
        self.assertEqual(next(r for r in rows if r['name']=='Chaos')['cap'],80)

    def test_all_real_ascended_max_resist_records(self):
        from GrimDawn_Optimizer import Engine
        records=[(p,r) for p,r in self.db.items() if '/lootaffixes/ascended/' in p
                 and any(r.get(f+'MaxResist',0) for f in core.RES)]
        self.assertEqual(len(records),9)
        e=Engine.__new__(Engine);e.db=self.db;e.cache={}
        e.items={'x':{'save':{'basename':'synthetic-base'},'rolled':{},'completion':{}}}
        # Only the base wrapper is synthetic; affix and component definitions are real.
        e.db=dict(self.db);e.db['synthetic-base']={'Class':'ArmorProtective_Head'}
        for path,r in records:
            for component,augment in [('', ''),('records/items/materia/compa_runestone.dbr',''),
                                      ('records/items/materia/compa_runestone.dbr','records/items/enchants/c08a_enchant.dbr')]:
                e.items['x']['save']['ascended-name']=path;e.cache.clear()
                cap=e.item_parts('x',component,augment)[3]
                for f in core.RES:
                    self.assertEqual(cap[f],r.get(f+'MaxResist',0))

    def test_normal_elite_ultimate_use_saved_penalties_in_both_engines(self):
        # Synthetic difficulty changes test only the adapter/constructors, never write a player save.
        for name in ['Beeztrap','Mal']:
            for difficulty, label in enumerate(['Normal','Elite','Ultimate']):
                source = self.staged[name,'full'][0]; dest = self.work/(name+label)
                shutil.copytree(source,dest,symlinks=True)
                c = copy.deepcopy(self.decoded[name]); c['last-difficulty'] = difficulty
                (dest/'mal.json').write_text(json.dumps(c))
                (dest/'penalties.json').write_text(json.dumps(difficulty_penalties(self.db,difficulty)))
                e = (CadenceEngine if name=='Beeztrap' else MalEngine)(dest)
                self.assertEqual(e.target_ultimate,difficulty==2)
                v = e.evaluate(e.current)
                for f, row in zip(core.RES, v['resistances']):
                    raw = v['stats'].get(f,0)+(v['stats'].get('defensiveElementalResistance',0) if f in core.RES[:3] else 0)+e.pen[f]
                    self.assertAlmostEqual(row['raw'],raw)
                self.assertEqual(data.difficulty_name(c),label)
                if name=='Beeztrap':
                    expected = sum(max(0,x['cap']-x['raw']) for x in v['resistances'][:9])+max(0,1900-v['DA'])/10+max(0,e.anchor['health']-v['health'])/50+max(0,90-v['armor_absorption'])*2+max(0,.95*e.anchor['armor']-v['armor'])/20+sum(x for _,x in e.offense_guard_gaps(v))
                    self.assertAlmostEqual(e.deficits(v),expected)
                del e

    def test_mechanics_invariants_on_current_save(self):
        from cadence_scenarios import SCENARIOS
        e = self.engine('Beeztrap'); v = e.evaluate(e.current)
        self.assertEqual(len(SCENARIOS),32)
        self.assertEqual([v['effective_skills']['records/skills/playerclass01/cadence'+str(i)+'.dbr'] for i in [1,2,3]], [9,2,12])
        comparison = e.scorer.compare(e.current)
        self.assertAlmostEqual(comparison['minimum_index'],100)
        self.assertAlmostEqual(comparison['maximum_index'],100)
        self.assertEqual(comparison['offensive_materiality_percent'],3)
        e = self.engine('Mal'); v = e.evaluate(e.current)
        self.assertEqual(v['effective_skills'][core.STORM],24)
        self.assertEqual(v['totem_count'],5); self.assertEqual(v['totems_per_cast'],2)
        self.assertAlmostEqual(v['totem_cooldown'],2.46)
        self.assertEqual(v['totem_duration'],14)

    def test_save_is_unchanged(self):
        self.assertEqual(hashlib.sha256(self.save.read_bytes()).hexdigest(),self.before)


if __name__ == '__main__': unittest.main()
