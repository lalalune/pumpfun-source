"""Nested Pump reports retain inputs and prior reports during failed runs."""
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from pump_differential_output import PumpReport
import pump_differential_output as publication

SCRIPTS = (
    'pump_create_nested_differential.py', 'pump_creator_collect_v2_differential.py',
    'pump_earned_cashback_differential.py', 'pump_fee_sweep_differential.py',
    'pump_global_init_differential.py', 'pump_legacy_cashback_differential.py',
    'pump_minimum_fee_differential.py', 'pump_set_params_differential.py',
    'pump_tokenkeg_two_curve_differential.py',
)
HAS_RUNTIME = importlib.util.find_spec('solders') is not None


class PumpReportPublicationTests(unittest.TestCase):
    def test_nested_parent_and_intentional_replacement(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'new' / 'nested' / 'report.json'
            output = PumpReport(path, root, None, __file__)
            self.assertTrue(path.parent.is_dir())
            output.write(b'first complete report')
            output.write(b'second complete report')
            self.assertEqual(path.read_bytes(), b'second complete report')

    def test_input_aliases_rejected_before_parent_mutation(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate = root / 'candidate.so'
            candidate.write_bytes(b'candidate bytes')
            link, hard = root / 'symlink.so', root / 'hardlink.so'
            link.symlink_to(candidate)
            os.link(candidate, hard)
            for output in (candidate, link, hard):
                with self.subTest(output=output), self.assertRaisesRegex(ValueError, 'aliases an input'):
                    PumpReport(output, root, candidate, __file__)
            self.assertEqual(candidate.read_bytes(), b'candidate bytes')

    def test_late_input_alias_rejected_before_publication(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate, path = root / 'candidate.so', root / 'report.json'
            candidate.write_bytes(b'candidate bytes')
            output = PumpReport(path, root, candidate, __file__)
            path.symlink_to(candidate)
            with self.assertRaisesRegex(ValueError, 'aliases an input'):
                output.write(b'receipt')
            self.assertEqual(candidate.read_bytes(), b'candidate bytes')

    def test_staging_and_replace_failures_preserve_previous_report(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'report.json'
            path.write_bytes(b'previous complete report')
            output = PumpReport(path, root, None, __file__)
            for operation in ('fsync', 'replace'):
                with self.subTest(operation=operation), \
                        mock.patch.object(publication.os, operation, side_effect=OSError('failed publication')):
                    with self.assertRaisesRegex(OSError, 'failed publication'):
                        output.write(b'new receipt')
                self.assertEqual(path.read_bytes(), b'previous complete report')
                self.assertEqual(list(root.glob('.report.json.*')), [])

    def test_success_does_not_remove_recreated_staging_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'report.json'
            output = PumpReport(path, root, None, __file__)
            replace = os.replace
            created = []
            def replace_and_recreate(source, destination):
                replace(source, destination)
                source.write_bytes(b'later writer')
                created.append(source)
            with mock.patch.object(publication.os, 'replace', replace_and_recreate):
                output.write(b'complete receipt')
            self.assertEqual(path.read_bytes(), b'complete receipt')
            self.assertEqual(created[0].read_bytes(), b'later writer')

    def test_fresh_output_refuses_existing_and_late_receipts(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / 'report.json'
            output = PumpReport(path, root, None, __file__, overwrite=False)
            path.write_bytes(b'later writer')
            with self.assertRaises(FileExistsError):
                output.write(b'new receipt')
            with self.assertRaises(FileExistsError):
                PumpReport(path, root, None, __file__, overwrite=False)
            self.assertEqual(path.read_bytes(), b'later writer')


@unittest.skipUnless(HAS_RUNTIME, 'solders is needed for actual differential CLI controls')
class PumpOutputCliTests(unittest.TestCase):
    def command(self, name, candidate, output):
        return [sys.executable, '-B', str(ROOT / 'scripts' / name),
                '--candidate', str(candidate), '--output', str(output)]

    def test_all_nine_clis_reject_public_candidate_alias(self):
        with tempfile.TemporaryDirectory() as temporary:
            candidate = Path(temporary) / 'candidate.so'
            candidate.write_bytes((ROOT / 'evidence/original/pump/deployed.so').read_bytes())
            digest = hashlib.sha256(candidate.read_bytes()).hexdigest()
            for name in SCRIPTS:
                with self.subTest(script=name):
                    result = subprocess.run(self.command(name, candidate, candidate),
                                            capture_output=True, text=True, timeout=45)
                    self.assertNotEqual(result.returncode, 0, result.stdout)
                    self.assertIn('report output aliases an input', result.stderr)
                    self.assertEqual(hashlib.sha256(candidate.read_bytes()).hexdigest(), digest)

    def test_real_vm_cases_publish_in_new_nested_parents(self):
        # Keep actual fixture construction, VM execution and comparisons; select
        # one existing case in the large families to bound this publication test.
        driver = r'''
import importlib, sys
sys.path.insert(0, sys.argv.pop(1))
name = sys.argv.pop(1)
m = importlib.import_module(name)
cases = m.cases
def first_case():
    result = cases()
    return (result[0][:1], result[1]) if isinstance(result, tuple) else result[:1]
m.cases = first_case
m.main()
'''
        with tempfile.TemporaryDirectory() as temporary:
            for name in SCRIPTS[:-1]:
                with self.subTest(script=name):
                    output = Path(temporary) / name / 'nested' / 'report.json'
                    candidate = ROOT / 'evidence/original/pump/deployed.so'
                    if name == 'pump_global_init_differential.py':
                        command = self.command(name, candidate, output)
                    else:
                        command = [sys.executable, '-B', '-c', driver, str(ROOT / 'scripts'), name[:-3],
                                   '--candidate', str(candidate), '--output', str(output)]
                    result = subprocess.run(command, capture_output=True, text=True, timeout=90)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    raw = output.read_bytes()
                    receipt = json.loads(gzip.decompress(raw) if raw[:2] == b'\x1f\x8b' else raw)
                    self.assertGreaterEqual(receipt['case_count'], 1)
                    self.assertEqual(receipt['mismatches'], [])
                    self.assertEqual(list(output.parent.glob('.report.json.*')), [])

    def test_real_vm_failure_preserves_existing_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            candidate, output = root / 'invalid.so', root / 'report.json'
            candidate.write_bytes(b'not an ELF')
            output.write_bytes(b'previous complete receipt')
            result = subprocess.run(self.command('pump_global_init_differential.py', candidate, output),
                                    capture_output=True, text=True, timeout=45)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(output.read_bytes(), b'previous complete receipt')
            self.assertEqual(list(root.glob('.report.json.*')), [])

    def test_two_curve_admission_prepares_parent_and_preserves_prior_receipt(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output = root / 'new' / 'nested' / 'report.json'
            candidate = ROOT / 'evidence/original/pump/deployed.so'
            command = self.command(SCRIPTS[-1], candidate, output)
            result = subprocess.run(command + ['--build-report', str(root / 'absent-build.json')],
                                    capture_output=True, text=True, timeout=45)
            self.assertNotEqual(result.returncode, 0)
            self.assertTrue(output.parent.is_dir())
            self.assertFalse(output.exists())
            output.write_bytes(b'previous complete receipt')
            result = subprocess.run(command, capture_output=True, text=True, timeout=45)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn('output must be fresh', result.stderr)
            self.assertEqual(output.read_bytes(), b'previous complete receipt')


if __name__ == '__main__':
    unittest.main()
