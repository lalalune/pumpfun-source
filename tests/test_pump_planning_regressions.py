"""Roadmap totals must cover full inventories without asserting match membership."""
import contextlib
import io
import itertools
import json
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import reconstruction_roadmap as rr


class FunctionalTests(unittest.TestCase):
    def test_real_capture_phases_use_all_eligible_windows(self):
        with tempfile.TemporaryDirectory() as temporary:
            out = Path(temporary) / 'out'
            with contextlib.redirect_stdout(io.StringIO()):
                rr.generate_roadmap(out)
            rows = []
            for path in out.glob('*-details.json'):
                data = json.loads(path.read_text())
                rows.extend((data['program'], w) for w in data['window_details'] if not w['name'])
            predicates = [
                lambda w: w['size'] <= 512 and bool(w['likely_callers']),
                lambda w: 512 < w['size'] <= 4096 and bool(w['likely_callers'] or w['likely_callees']),
                lambda w: w['size'] > 4096,
            ]
            plan = json.loads((out / 'reconstruction-plan.json').read_text())
            self.assertEqual(len(plan['phases']), 3)
            total_count = total_bytes = 0
            for phase, predicate, limit in zip(plan['phases'], predicates, (50, 50, 30)):
                eligible = {(name, w['address']): w for name, w in rows if predicate(w)}
                self.assertGreater(len(eligible), 0)
                # Assert full-inventory math before checking newly added metadata:
                # this fails numerically on the original capped implementation.
                self.assertEqual(phase['window_count'], len(eligible))
                self.assertEqual(phase['total_bytes'], sum(w['size'] for w in eligible.values()))
                self.assertEqual(phase['display_limit'], limit)
                self.assertEqual(phase['displayed_window_count'], min(limit, len(eligible)))
                displayed = [(w['program'], w['address']) for w in phase['windows']]
                self.assertEqual(len(displayed), len(set(displayed)))
                self.assertEqual(len(displayed), phase['displayed_window_count'])
                self.assertTrue(set(displayed) <= eligible.keys())
                total_count += len(eligible)
                total_bytes += sum(w['size'] for w in eligible.values())
            self.assertEqual(plan['total_planning_candidates'], total_count)
            self.assertEqual(plan['total_planning_bytes'], total_bytes)
            self.assertNotIn('total_estimated_windows_to_close', plan)
            self.assertIn('not unmatched membership', plan['candidate_basis'])
            readme = (out / 'README.md').read_text()
            self.assertIn('every eligible unnamed window', readme)
            self.assertIn('50, 50 and 30', readme)
            self.assertIn('not a completion deficit', readme)

    def test_bridge_window_joins_both_existing_clusters(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'deployed.so').write_bytes(b'fixture')
            attributes = {
                0: {'likely_callers': [('A', 1)]},
                8: {'likely_callers': [('B', 1)]},
                16: {'likely_callers': [('A', 1), ('B', 1)]},
            }
            elf = SimpleNamespace(entries=[0, 8, 16], hi=24, funcs=[], calls={},
                                  relocations={}, b=(b'\x95' + bytes(7)) * 3)
            with patch.object(rr, 'REPO', root), patch.object(
                rr, 'PROGRAMS', {'fixture': {'deployed': 'deployed.so',
                                            'frontier_normalized': 0, 'frontier_raw': 0}}
            ), patch.object(rr, 'Elf', return_value=elf), patch.object(
                rr, 'trace_handler_attribution', return_value=attributes
            ), patch.object(rr, 'analyze_cross_references', return_value={}), \
                    contextlib.redirect_stdout(io.StringIO()):
                rr.generate_roadmap(root / 'out')
            data = json.loads((root / 'out/fixture-details.json').read_text())
            self.assertEqual(len(data['reconstruction_clusters']), 1)
            cluster = data['reconstruction_clusters'][0]
            self.assertEqual(cluster['window_count'], 3)
            self.assertEqual(cluster['total_bytes'], 24)
            self.assertEqual(set(cluster['callers']), {'A', 'B'})
            self.assertEqual(set(cluster['windows']), {'0x0', '0x8', '0x10'})

    def test_cluster_totals_are_not_limited_to_display(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / 'deployed.so').write_bytes(b'fixture')
            starts = list(range(0, 80 * 8, 8))
            attrs = {start: {'likely_callers': [(f'caller_{start}', 1)]} for start in starts}
            elf = SimpleNamespace(entries=starts, hi=80 * 8, funcs=[], calls={},
                                  relocations={}, b=(b'\x95' + bytes(7)) * 80)
            with patch.object(rr, 'REPO', root), patch.object(
                rr, 'PROGRAMS', {'fixture': {'deployed': 'deployed.so',
                                            'frontier_normalized': 0, 'frontier_raw': 0}}
            ), patch.object(rr, 'Elf', return_value=elf), patch.object(
                rr, 'trace_handler_attribution', return_value=attrs
            ), patch.object(rr, 'analyze_cross_references', return_value={}), \
                    contextlib.redirect_stdout(io.StringIO()):
                rr.generate_roadmap(root / 'out')
            summary = json.loads((root / 'out/summary.json').read_text())['programs']['fixture']
            data = json.loads((root / 'out/fixture-details.json').read_text())
            self.assertEqual(summary['reconstruction_clusters'], 80)
            self.assertEqual(summary['displayed_reconstruction_clusters'], 50)
            self.assertEqual(len(data['reconstruction_clusters']), 50)

    def test_multiple_bridges_form_same_components_in_any_order(self):
        windows = [
            {'address': name, 'size': size, 'likely_callers': [(c, 1) for c in callers]}
            for name, size, callers in [
                ('a', 8, ['A']), ('b', 16, ['B']), ('c', 24, ['C']),
                ('ab', 32, ['A', 'B']), ('bc', 40, ['B', 'C'])
            ]
        ]
        separate = {'address': 'd', 'size': 48, 'likely_callers': [('D', 1)]}
        uncalled = {'address': 'none', 'size': 64, 'likely_callers': []}
        for ordering in itertools.permutations(windows):
            clusters = rr.cluster_windows([*ordering, separate, uncalled])
            actual = {(frozenset(c['callers']), frozenset(c['windows']), c['total_bytes'])
                      for c in clusters}
            self.assertEqual(actual, {
                (frozenset('ABC'), frozenset(['a', 'b', 'c', 'ab', 'bc']), 120),
                (frozenset('D'), frozenset(['d']), 48),
            })


if __name__ == '__main__':
    unittest.main(verbosity=2)
