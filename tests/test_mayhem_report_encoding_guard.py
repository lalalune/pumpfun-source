"""The Mayhem receipt guard must keep covering the family after PumpReport.

``scripts/test_mayhem_report_encoding.py`` used to require more than ten bare
``write_text`` receipts. Once most of the family moved to the shared
``PumpReport`` publisher, whose bytes are composed by the caller, that count no
longer matched the repository and the guard failed on ``main`` itself. It now
requires, for every script that takes ``--output``, either a pinned
``write_text`` or the ``PumpReport`` publication shape, and still requires the
family to be larger than ten report writers.

These tests pin the guard's shapes: a PumpReport writer is accepted, a direct
unpinned write is not.
"""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import test_mayhem_report_encoding as guard  # noqa: E402

PINNED = '''
import argparse, json
p = argparse.ArgumentParser()
p.add_argument('--output', type=str)
a = p.parse_args()
a.output.write_text(json.dumps({}), encoding='utf-8', newline='\\n')
'''
PUMP_REPORT = '''
import argparse
from pump_differential_output import PumpReport
p = argparse.ArgumentParser()
p.add_argument('--output', type=str)
a = p.parse_args()
publisher = PumpReport(a.output, ROOT, a.candidate, __file__)
publisher.write(b'{}')
'''
UNPINNED = '''
import argparse, json
p = argparse.ArgumentParser()
p.add_argument('--output', type=str)
a = p.parse_args()
a.output.write_text(json.dumps({}))
'''
DIRECT_OPEN = '''
import argparse
p = argparse.ArgumentParser()
p.add_argument('--output', type=str)
a = p.parse_args()
with open(a.output, 'wb') as stream:
    stream.write(b'{}')
'''


class MayhemReportEncodingGuardTests(unittest.TestCase):
    def run_guard(self, sources):
        temporary = tempfile.TemporaryDirectory(prefix='mayhem-guard-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for index, source in enumerate(sources):
            (root / f'mayhem_case_{index:02d}.py').write_text(source, encoding='utf-8')
        case = guard.MayhemReportEncodingTests('test_every_report_writer_pins_utf8_and_lf')
        result = unittest.TestResult()
        with mock.patch.object(guard, 'SCRIPTS', root):
            case.run(result)
        return result

    def test_pinned_and_published_receipts_pass(self):
        result = self.run_guard([PINNED] * 6 + [PUMP_REPORT] * 6)
        self.assertTrue(result.wasSuccessful(), [error for _, error in result.failures])

    def test_unpinned_write_text_fails(self):
        result = self.run_guard([PINNED] * 6 + [PUMP_REPORT] * 5 + [UNPINNED])
        self.assertFalse(result.wasSuccessful())
        self.assertIn('encoding', str(result.failures))

    def test_a_direct_write_that_is_not_pump_report_fails(self):
        result = self.run_guard([PINNED] * 6 + [PUMP_REPORT] * 5 + [DIRECT_OPEN])
        self.assertFalse(result.wasSuccessful())
        self.assertIn('mayhem_case_11.py', str(result.failures))

    def test_inherited_publisher_requires_a_local_publisher_import(self):
        inherited = PUMP_REPORT.replace('from pump_differential_output import PumpReport',
                                        'from mayhem_case_00 import *')
        sources = [PUMP_REPORT] + [PINNED] * 5 + [inherited] * 6
        accepted = self.run_guard(sources)
        self.assertTrue(accepted.wasSuccessful(), str(accepted.failures))
        unrelated = inherited.replace('mayhem_case_00', 'mayhem_case_01')
        refused = self.run_guard(sources[:-1] + [unrelated])
        self.assertFalse(refused.wasSuccessful())
        self.assertIn('mayhem_case_11.py', str(refused.failures))

    def test_family_smaller_than_expected_fails(self):
        result = self.run_guard([PINNED] * 3 + [PUMP_REPORT] * 3)
        self.assertFalse(result.wasSuccessful())

    def test_helpers_recognise_each_shape(self):
        self.assertTrue(guard.takes_output(__import__('ast').parse(PINNED)))
        self.assertFalse(guard.takes_output(__import__('ast').parse('x = 1\n')))
        self.assertEqual(len(guard.pinned_writes(__import__('ast').parse(PINNED))), 1)
        self.assertTrue(guard.publishes_through_pump_report(
            __import__('ast').parse(PUMP_REPORT), PUMP_REPORT))
        self.assertFalse(guard.publishes_through_pump_report(
            __import__('ast').parse(DIRECT_OPEN), DIRECT_OPEN))


if __name__ == '__main__':
    unittest.main()
