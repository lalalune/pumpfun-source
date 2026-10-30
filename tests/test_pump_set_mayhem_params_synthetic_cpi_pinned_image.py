"""Full signed synthetic-CPI CLI runs use admitted image and fixture bytes.

The historical caller is test-only. Captured Pump bytes serve as a diagnostic
candidate, not as reconstructed source or evidence of a production Mayhem route.
"""
import gzip
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'tests/fixtures/mayhem-synthetic-cpi'
ORIGINAL = ROOT / 'evidence/original/pump/deployed.so'
OTHER = ROOT / 'evidence/original/pump_fees/deployed.so'
TOKEN_NAMES = ('capture.json', 'program-account.bin', 'programdata-account.bin')
PRIOR = b'previous complete report'
DRIVER = r'''
import os, sys, shutil
from pathlib import Path
scripts, directory, replacement, mode, output = sys.argv[1:]
sys.path.insert(0, scripts)
import pump_set_mayhem_params_synthetic_cpi as module
root = Path(directory)
module.TOKEN_INPUTS = {name: root / name for name in ('capture.json', 'program-account.bin', 'programdata-account.bin')}
returned = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == 'run' and frame.f_code.co_filename == module.__file__:
        returned.append(1)
        if len(returned) == 1:
            sys.setprofile(None)
            if mode == 'mutate':
                for name in ('target.so', 'candidate.so', 'caller.so'):
                    shutil.copyfile(replacement, root / name)
                for name in ('fixture.json.gz', *module.TOKEN_INPUTS):
                    (root / name).write_bytes(b'replaced after first target')
            elif mode == 'late-alias':
                Path(output).unlink()
                Path(output).hardlink_to(root / 'target.so')
if mode in ('mutate', 'late-alias'):
    sys.setprofile(hook)
if mode == 'publication-failure':
    def fail(*args, **kwargs):
        raise OSError('injected publication failure')
    module.os.replace = fail
sys.argv = [module.__file__, '--target', str(root / 'target.so'), '--caller', str(root / 'caller.so'),
            '--fixture', str(root / 'fixture.json.gz'), '--output', output]
if mode != 'original-only':
    sys.argv += ['--candidate', str(root / 'candidate.so')]
try:
    module.main()
finally:
    sys.setprofile(None)
    if mode in ('mutate', 'late-alias') and not returned:
        raise RuntimeError('no target case executed')
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class SyntheticMayhemParamsPinnedImageTests(unittest.TestCase):
    def stage(self, mode='normal', alias=None, alias_kind='direct'):
        temporary = tempfile.TemporaryDirectory(prefix='synthetic-mayhem-binding-')
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        for name in ('target.so', 'candidate.so'):
            shutil.copyfile(ORIGINAL, root / name)
        shutil.copyfile(FIXTURES / 'synthetic-caller.so', root / 'caller.so')
        shutil.copyfile(FIXTURES / 'account-snapshot.json.gz', root / 'fixture.json.gz')
        for name in TOKEN_NAMES:
            shutil.copyfile(ROOT / 'evidence/dependencies/spl_token_2022' / name, root / name)
        if mode == 'wrong-candidate':
            shutil.copyfile(OTHER, root / 'candidate.so')
        if mode == 'wrong-target':
            shutil.copyfile(OTHER, root / 'target.so')
        if mode == 'wrong-caller':
            shutil.copyfile(OTHER, root / 'caller.so')
        output = root / 'report.json.gz'
        output.write_bytes(PRIOR)
        if alias:
            source = root / alias
            if alias_kind == 'direct':
                output = source
            else:
                output.unlink()
                if alias_kind == 'hardlink':
                    output.hardlink_to(source)
                else:
                    output.symlink_to(source)
        before = {path.name: sha(path) for path in root.iterdir() if path.is_file() and path.name != 'report.json.gz'}
        environment = dict(os.environ)
        environment.pop('PYTHONOPTIMIZE', None)
        result = subprocess.run([sys.executable, '-B', '-c', DRIVER, str(ROOT / 'scripts'), str(root),
                                 str(OTHER), mode, str(output)],
                                cwd=ROOT, env=environment, capture_output=True, text=True, timeout=120)
        return result, root, output, before

    def assert_report(self, output, candidate=True):
        report = json.loads(gzip.decompress(output.read_bytes()))
        self.assertEqual(len(report['cases']), 25)
        self.assertEqual(sum(row['error'] is None for row in report['cases']), 13)
        self.assertTrue(all(row['pump_instruction_reached'] and row['signatures_valid'] for row in report['cases']))
        if candidate:
            self.assertEqual(len(report['candidate_cases']), 25)
            self.assertEqual(sum(row['error'] is None for row in report['candidate_cases']), 13)
            self.assertTrue(all(all(row['equal'].values()) for row in report['comparison']))
        return report

    def test_all_program_and_metadata_snapshots_survive_replacement(self):
        result, root, output, before = self.stage('mutate')
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        report = self.assert_report(output)
        for name, digest in before.items():
            self.assertNotEqual(sha(root / name), digest, name + ' not replaced')
        self.assertEqual(report['target_sha256'], before['target.so'])
        self.assertEqual(report['candidate_sha256'], before['candidate.so'])
        self.assertEqual(report['synthetic_caller_sha256'], before['caller.so'])
        self.assertEqual(report['fixture_sha256'], before['fixture.json.gz'])
        self.assertEqual(report['token_program_input_sha256'], {name: before[name] for name in TOKEN_NAMES})
        self.assertTrue(all(row['binary_sha256'] == before['target.so'] for row in report['cases']))
        self.assertTrue(all(row['binary_sha256'] == before['candidate.so'] for row in report['candidate_cases']))

    def test_complete_cli_and_original_only_replace_prior_reports(self):
        for mode in ('normal', 'original-only'):
            with self.subTest(mode=mode):
                result, _, output, _ = self.stage(mode)
                self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
                self.assertNotEqual(output.read_bytes(), PRIOR)
                report = self.assert_report(output, candidate=mode == 'normal')
                if mode == 'original-only':
                    self.assertNotIn('candidate_cases', report)

    def test_wrong_program_images_fail_and_preserve_prior_report(self):
        for mode in ('wrong-target', 'wrong-candidate', 'wrong-caller'):
            with self.subTest(mode=mode):
                result, _, output, _ = self.stage(mode)
                self.assertEqual(result.returncode, 1)
                self.assertIn('AssertionError', result.stderr)
                if mode == 'wrong-candidate':
                    self.assertIn('candidate diverges from captured target', result.stderr)
                self.assertEqual(output.read_bytes(), PRIOR)

    def test_output_cannot_alias_original_inputs(self):
        for source in ('target.so', 'candidate.so', 'caller.so', 'fixture.json.gz', 'programdata-account.bin'):
            for kind in ('direct', 'hardlink', 'symlink'):
                with self.subTest(source=source, kind=kind):
                    result, root, output, before = self.stage(alias=source, alias_kind=kind)
                    self.assertEqual(result.returncode, 2, result.stderr[-2000:])
                    self.assertIn('output aliases an input', result.stderr)
                    for name, digest in before.items():
                        self.assertEqual(sha(root / name), digest)
                    self.assertEqual(sha(output), sha(root / source))

    def test_late_output_alias_preserves_original(self):
        result, root, output, before = self.stage('late-alias')
        self.assertEqual(result.returncode, 2, result.stderr[-2000:])
        self.assertIn('output aliases an input', result.stderr)
        self.assertEqual(sha(root / 'target.so'), before['target.so'])
        self.assertEqual(sha(output), before['target.so'])

    def test_default_cli_has_complete_retained_inputs(self):
        temporary = tempfile.TemporaryDirectory(prefix='synthetic-mayhem-default-')
        self.addCleanup(temporary.cleanup)
        output = Path(temporary.name) / 'report.json.gz'
        result = subprocess.run([sys.executable, '-B', str(ROOT / 'scripts/pump_set_mayhem_params_synthetic_cpi.py'),
                                 '--output', str(output)], cwd=ROOT, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stdout[-2000:] + result.stderr[-2000:])
        self.assert_report(output, candidate=False)

    def test_successful_publication_preserves_recreated_staging_path(self):
        sys.path.insert(0, str(ROOT / 'scripts'))
        import pump_set_mayhem_params_synthetic_cpi as module
        temporary = tempfile.TemporaryDirectory(prefix='synthetic-mayhem-publish-')
        self.addCleanup(temporary.cleanup)
        output = Path(temporary.name) / 'report.json'
        replace = os.replace
        recreated = []
        def replace_and_recreate(source, target):
            replace(source, target)
            Path(source).write_bytes(b'new file from another writer')
            recreated.append(Path(source))
        with mock.patch.object(module.os, 'replace', replace_and_recreate):
            module.write_report(output, b'complete report')
        self.assertEqual(output.read_bytes(), b'complete report')
        self.assertEqual(recreated[0].read_bytes(), b'new file from another writer')

    def test_failed_atomic_publication_preserves_prior_report(self):
        result, root, output, before = self.stage('publication-failure')
        self.assertEqual(result.returncode, 1)
        self.assertIn('injected publication failure', result.stderr)
        self.assertEqual(output.read_bytes(), PRIOR)
        self.assertEqual(list(root.glob('.report.json.gz.*')), [])


if __name__ == '__main__':
    unittest.main()
