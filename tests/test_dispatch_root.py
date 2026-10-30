#!/usr/bin/env python3
"""Dispatch recovery must select programs from the supplied evidence root."""
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'scripts'))
import recover_dispatch


class DispatchRootTests(unittest.TestCase):
    def evidence_root(self, names):
        workspace = tempfile.TemporaryDirectory()
        self.addCleanup(workspace.cleanup)
        root = Path(workspace.name)
        (root / 'evidence/upstream').mkdir(parents=True)
        for name in names:
            shutil.copytree(REPO / 'evidence/original' / name,
                            root / 'evidence/original' / name)
            shutil.copyfile(REPO / 'evidence/upstream' / f'{name}.json',
                            root / 'evidence/upstream' / f'{name}.json')
        return root

    def test_partial_capture_root_selects_only_its_present_program(self):
        root = self.evidence_root(('pump_fees',))
        result = recover_dispatch.dispatch(root)
        self.assertEqual(list(result), ['pump_fees'])
        self.assertEqual(result['pump_fees'],
                         recover_dispatch.recover('pump_fees', root))
        self.assertEqual(sum(bool(row['matches'])
                             for row in result['pump_fees']['instructions'].values()), 31)

    def test_supplied_roots_archived_selector_controls_membership_and_order(self):
        root = self.evidence_root(('pump_fees', 'pump_amm'))
        (root / 'repro').mkdir()
        selector = {
            name: json.loads((root / 'evidence/original' / name / 'capture.json')
                             .read_text(encoding='utf-8'))['program']
            for name in ('pump_fees', 'pump_amm')
        }
        (root / 'repro/programs.json').write_text(json.dumps(selector), encoding='utf-8')
        result = recover_dispatch.dispatch(root)
        self.assertEqual(list(result), list(selector))
        for name in selector:
            self.assertEqual(result[name], recover_dispatch.recover(name, root))

    def test_default_root_retains_the_published_dispatch_report(self):
        expected = json.loads((REPO / 'evidence/dispatch-map.json').read_text(encoding='utf-8'))
        self.assertEqual(recover_dispatch.dispatch(), expected)


if __name__ == '__main__':
    unittest.main()
