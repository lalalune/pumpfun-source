"""Execute real signed donation sequences while checking input/receipt binding."""
from contextlib import ExitStack, redirect_stdout
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
spec = importlib.util.spec_from_file_location('donation_sequence', ROOT / 'scripts/fees_donation_sequence.py')
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)
import probe_report


class DonationSequencePinnedImageTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='donation-sequence-binding-')
        self.addCleanup(temporary.cleanup)
        self.base = Path(temporary.name)

    def fixture(self, name='case'):
        root = self.base / name
        for source in [
            'scripts/fees_donation_sequence.py',
            'evidence/original/pump_fees/deployed.so',
            'evidence/dependencies/donation_relay/deployed.so',
            'evidence/dependencies/spl_token/deployed.so',
            'evidence/dependencies/associated_token/deployed.so',
            'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
            'evidence/upstream/pump_fees.json',
        ]:
            destination = root / source
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / source, destination)
        shutil.copyfile(root / 'evidence/original/pump_fees/deployed.so', root / 'candidate.so')
        return root

    def inputs(self, root):
        return {
            'candidate': root / 'candidate.so',
            'original': root / 'evidence/original/pump_fees/deployed.so',
            **{name: root / f'evidence/dependencies/{name}/deployed.so'
               for name in ('donation_relay', 'spl_token', 'associated_token')},
            'mint_fixture': root / 'research/imported-lab/analysis/pump_fun/amm-v2-trade-fixture.json',
            'idl': root / 'evidence/upstream/pump_fees.json',
        }

    def invoke(self, root, *, mutate=None, output=None):
        output = output or root / 'report.json'
        real_send = driver.Recorder.send_transaction
        calls = 0

        def send(recorder, tx):
            nonlocal calls
            result = real_send(recorder, tx)
            calls += 1
            if calls == 1 and mutate is not None:
                mutate()
            return result

        with ExitStack() as stack:
            stack.enter_context(patch.object(driver, 'ROOT', root))
            stack.enter_context(patch.object(driver, '__file__', str(root / 'scripts/fees_donation_sequence.py')))
            stack.enter_context(patch.object(driver.Recorder, 'send_transaction', send))
            stack.enter_context(patch.object(sys, 'argv', ['sequence', '--candidate', str(root / 'candidate.so'),
                                                         '--output', str(output)]))
            stack.enter_context(redirect_stdout(io.StringIO()))
            driver.main()
        return json.loads(output.read_bytes())

    def assert_sequence(self, report):
        self.assertEqual(len(report['steps']), 10)
        self.assertEqual(report['mismatches'], [])
        self.assertEqual(report['unexpected_errors'], [])
        for step in report['steps']:
            self.assertTrue(step['match'])
            for side in ['original', 'candidate']:
                self.assertTrue(step[side]['signature_verification'])
                self.assertIsNone(step[side]['error'])
        self.assertTrue(any(step['original']['events'] for step in report['steps']))
        self.assertEqual(report['original_sha256'], driver.RETAINED_SHA256['original'])
        self.assertEqual(report['candidate_sha256'], driver.RETAINED_SHA256['original'])
        self.assertEqual(report['dependency_hashes'], {name: digest for name, digest in driver.RETAINED_SHA256.items()
                                                      if name != 'original'})

    def test_real_sequence_and_all_consumed_image_hashes(self):
        self.assert_sequence(self.invoke(self.fixture()))

    def test_late_image_and_fixture_changes_do_not_change_execution_or_hashes(self):
        for name in self.inputs(self.base):
            with self.subTest(input=name):
                root = self.fixture(name)
                path = self.inputs(root)[name]
                expected = hashlib.sha256(path.read_bytes()).hexdigest()
                report = self.invoke(root, mutate=lambda: path.write_bytes(b'changed after first signed transaction'))
                self.assert_sequence(report)
                if name in ('mint_fixture', 'idl'):
                    self.assertEqual(report['fixture_input_hashes'][str(path.relative_to(root))], expected)
                self.assertNotEqual(hashlib.sha256(path.read_bytes()).hexdigest(), expected)

    def test_wrong_retained_programs_fail_before_any_sequence(self):
        for name in driver.RETAINED_SHA256:
            with self.subTest(input=name):
                root = self.fixture(name)
                shutil.copyfile(ROOT / 'evidence/original/pump/deployed.so', self.inputs(root)[name])
                with self.assertRaisesRegex(ValueError, 'image hash mismatch'):
                    self.invoke(root)
                self.assertFalse((root / 'report.json').exists())

    def test_wrong_candidate_is_rejected_by_real_creation(self):
        root = self.fixture()
        shutil.copyfile(ROOT / 'evidence/original/pump/deployed.so', root / 'candidate.so')
        prior = b'prior receipt\n'
        (root / 'report.json').write_bytes(prior)
        with self.assertRaisesRegex(AssertionError, 'Creation failed'):
            self.invoke(root)
        self.assertEqual((root / 'report.json').read_bytes(), prior)

    def test_changed_imported_idl_cannot_be_reported_as_the_fixture_used(self):
        root = self.fixture()
        path = self.inputs(root)['idl']
        document = json.loads(path.read_bytes())
        document['address'] = str(driver.crank.RELAY)
        path.write_text(json.dumps(document))
        with self.assertRaisesRegex(ValueError, 'IDL changed since fixture import'):
            self.invoke(root)
        self.assertFalse((root / 'report.json').exists())

    def test_reruns_replace_reports_but_failed_publication_preserves_them(self):
        root = self.fixture()
        output = root / 'report.json'
        output.write_bytes(b'prior receipt\n')
        self.assert_sequence(self.invoke(root))
        prior = output.read_bytes()
        with patch.object(probe_report.os, 'replace', side_effect=OSError('late publication failure')):
            with self.assertRaisesRegex(OSError, 'late publication failure'):
                self.invoke(root)
        self.assertEqual(output.read_bytes(), prior)
        self.assertEqual(list(root.glob('.report.json.*')), [])

    def test_output_cannot_alias_any_input(self):
        root = self.fixture()
        for name, path in self.inputs(root).items():
            with self.subTest(input=name):
                before = path.read_bytes()
                with self.assertRaisesRegex(ValueError, 'output aliases an input'):
                    self.invoke(root, output=path)
                self.assertEqual(path.read_bytes(), before)
        for kind in ('symlink', 'hardlink'):
            alias = root / kind
            try:
                if kind == 'symlink': alias.symlink_to(root / 'candidate.so')
                else: os.link(root / 'candidate.so', alias)
            except OSError as error:
                self.skipTest(str(error))
            with self.assertRaisesRegex(ValueError, 'output aliases an input'):
                self.invoke(root, output=alias)
            self.assertEqual((root / 'candidate.so').read_bytes(),
                             (root / 'evidence/original/pump_fees/deployed.so').read_bytes())

    def test_empty_sequences_cannot_be_a_successful_comparison(self):
        root = self.fixture()
        with patch.object(driver, 'execute', return_value=[]):
            with self.assertRaisesRegex(ValueError, 'must contain signed transactions'):
                self.invoke(root)
        self.assertFalse((root / 'report.json').exists())

    def test_optimized_mode_is_explicitly_unsupported_by_signed_fixture(self):
        output = self.base / 'optimized.json'
        result = subprocess.run([sys.executable, '-O', str(ROOT / 'scripts/fees_donation_sequence.py'),
                                 '--candidate', str(ROOT / 'evidence/original/pump_fees/deployed.so'),
                                 '--output', str(output)], capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('Normal Python is required', result.stderr)
        self.assertFalse(output.exists())


if __name__ == '__main__':
    unittest.main()
