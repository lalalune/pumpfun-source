"""A failed imported-lab verification must not publish a partial tree."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest import mock


SCRIPTS = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


class ImportedLabPublicationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix='imported-lab-publication-')
        self.root = Path(self.temporary.name)
        snapshot = self.root / 'research/imported-lab'
        (snapshot / 'scripts').mkdir(parents=True)
        (snapshot / 'inputs/pump_fun').mkdir(parents=True)
        (snapshot / 'analysis/pump_fun').mkdir(parents=True)
        for name in [
                'pump_fun_verify_offline', 'pump_fun_admin_surfpool_verify',
                'pump_fun_amm_v2_surfpool_verify',
                'pump_fun_curve_fresh_surfpool_verify',
                'pump_fun_curve_migration_surfpool_verify',
                'pump_fun_post_migration_amm_surfpool_verify',
                'pump_fun_fees_withdraw_surfpool_verify',
                'pump_fun_admin_surfpool', 'pump_fun_amm_buy_v2_surfpool',
                'pump_fun_curve_create_v2_surfpool',
                'pump_fun_fees_withdraw_surfpool']:
            (snapshot / 'scripts' / (name + '.py')).write_text('raise SystemExit(0)\n')
        blob = b'captured program'
        files = []
        for name in ('pump', 'pump_amm', 'pump_fees'):
            relative = f'inputs/pump_fun/{name}.so'
            (snapshot / relative).write_bytes(blob)
            original = self.root / f'evidence/original/{name}/deployed.so'
            original.parent.mkdir(parents=True)
            original.write_bytes(blob)
            files.append({'path': relative, 'sha256': sha(blob)})
        notes = snapshot / 'notes.txt'
        notes.write_text('lab notes\n')
        files.append({'path': 'notes.txt', 'sha256': sha(notes.read_bytes())})
        (self.root / 'research/import-manifest.json').write_text(json.dumps({
            'commit': 'fixture', 'files': files,
        }))
        (snapshot / 'analysis/pump_fun/program-manifest.json').write_text(json.dumps({
            'official_docs_commit': 'a' * 40,
        }))
        self.docs = self.root / 'docs'
        self.docs.mkdir()

        spec = importlib.util.spec_from_file_location(
            'imported_lab_under_test', SCRIPTS / 'verify_imported_lab.py')
        tool = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(tool)
        tool.ROOT = self.root
        self.tool = tool

    def tearDown(self):
        self.temporary.cleanup()

    def arguments(self, output):
        return types.SimpleNamespace(
            docs_checkout=self.docs, output=output, surfpool=None)

    def test_clone_failure_leaves_no_partial_lab(self):
        output = self.root / 'verification'
        real_run = self.tool.subprocess.run

        def fail_clone(command, *args, **kwargs):
            if command[:2] == ['git', '-C'] and 'cat-file' in command:
                return types.SimpleNamespace(returncode=0)
            if command[:2] == ['git', 'clone']:
                raise OSError('injected docs clone failure')
            return real_run(command, *args, **kwargs)

        with mock.patch.object(self.tool.subprocess, 'run', fail_clone), \
                mock.patch.object(sys, 'argv', [
                    'verify_imported_lab.py', '--docs-checkout', str(self.docs),
                    '--output', str(output)]):
            with self.assertRaisesRegex(OSError, 'injected docs clone failure'):
                self.tool.main()

        self.assertFalse(output.exists(), 'failed verification published a partial tree')
        self.assertEqual(list(output.parent.glob('.verification.*')), [])

    def test_complete_verification_is_published(self):
        output = self.root / 'verification'
        real_run = self.tool.subprocess.run

        def complete_clone(command, *args, **kwargs):
            if command[:2] == ['git', '-C'] and 'cat-file' in command:
                return types.SimpleNamespace(returncode=0)
            if command[:2] == ['git', 'clone']:
                Path(command[-1]).mkdir(parents=True)
                return types.SimpleNamespace(returncode=0)
            if command[:2] == ['git', '-C'] and 'checkout' in command:
                return types.SimpleNamespace(returncode=0)
            return real_run(command, *args, **kwargs)

        with mock.patch.object(self.tool.subprocess, 'run', complete_clone), \
                mock.patch.object(sys, 'argv', [
                    'verify_imported_lab.py', '--docs-checkout', str(self.docs),
                    '--output', str(output)]):
            self.tool.main()

        report = json.loads((output / 'integration-verification.json').read_text())
        self.assertTrue(report['saved_receipt_verifiers_passed'])
        self.assertEqual(list(output.parent.glob('.verification.*')), [])

    def test_late_empty_output_is_not_replaced(self):
        output = self.root / 'verification'
        def complete_verification(args, staging):
            (staging / 'integration-verification.json').write_text('{}\n')
            output.mkdir()
            return True, None
        with mock.patch.object(self.tool, 'verify', complete_verification), \
                mock.patch.object(sys, 'argv', [
                    'verify_imported_lab.py', '--docs-checkout', str(self.docs),
                    '--output', str(output)]):
            with self.assertRaises(FileExistsError):
                self.tool.main()
        self.assertEqual(list(output.iterdir()), [])
        self.assertEqual(list(output.parent.glob('.verification.*')), [])

    def test_output_cannot_overlap_imported_inputs_or_docs(self):
        for parent in (self.root / 'research/imported-lab', self.docs):
            with self.subTest(parent=parent), mock.patch.object(self.tool, 'verify') as verify, \
                    mock.patch.object(sys, 'argv', [
                        'verify_imported_lab.py', '--docs-checkout', str(self.docs),
                        '--output', str(parent / 'new-output')]):
                before = sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*'))
                with self.assertRaisesRegex(ValueError, 'output must not overlap'):
                    self.tool.main()
                verify.assert_not_called()
                self.assertEqual(sorted(str(path.relative_to(self.root)) for path in self.root.rglob('*')), before)

    @unittest.skipUnless(os.name == 'posix', 'POSIX mode check')
    def test_new_output_follows_umask(self):
        output = self.root / 'verification'
        def complete_verification(args, staging):
            (staging / 'integration-verification.json').write_text('{}\n')
            return True, None
        old = os.umask(0o027)
        try:
            with mock.patch.object(self.tool, 'verify', complete_verification), \
                    mock.patch.object(sys, 'argv', [
                        'verify_imported_lab.py', '--docs-checkout', str(self.docs),
                        '--output', str(output)]):
                self.tool.main()
        finally:
            os.umask(old)
        self.assertEqual(output.stat().st_mode & 0o777, 0o750)


if __name__ == '__main__':
    unittest.main()
