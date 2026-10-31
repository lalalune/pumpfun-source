"""Each smoke case named missing-accounts must reach the account check it names.

Runs the real smoke test on the captured Pump and AMM images. Anchor reports
AccountNotEnoughKeys as 3005 and InstructionDidNotDeserialize as 102.
"""
import contextlib
import io
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile
import unittest
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))
import local_validation

ROOT = Path(__file__).resolve().parents[1]
PROGRAMS = ('pump', 'pump_amm')


def custom_code(case):
    match = re.search(r'Custom\((\d+)\)', case['error'] or '')
    return match and int(match.group(1))


class MissingAccountCases(unittest.TestCase):
    def test_cases_stop_at_the_account_check(self):
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            (repo / 'evidence/upstream').mkdir(parents=True)
            for name in PROGRAMS:
                shutil.copytree(ROOT / 'evidence/original' / name, repo / 'evidence/original' / name)
                shutil.copy(ROOT / f'evidence/upstream/{name}.json', repo / 'evidence/upstream')
            with mock.patch.object(local_validation, 'ROOT', repo), \
                    contextlib.redirect_stdout(io.StringIO()):
                local_validation.main()
            report = json.loads((repo / 'audit/local-validation.json').read_text(encoding='utf-8'))
        for name in PROGRAMS:
            with self.subTest(program=name):
                cases = [case for case in report['programs'][name]['cases']
                         if case['case'].endswith('-missing-accounts')]
                self.assertGreater(len(cases), 30)
                stopped = sorted(case['case'] for case in cases if custom_code(case) != 3005)
                self.assertEqual(stopped, [], f'{len(stopped)} of {len(cases)} cases')


if __name__ == '__main__':
    unittest.main()
