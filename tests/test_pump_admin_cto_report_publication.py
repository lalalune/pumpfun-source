"""Real admin_cto CLI/VM publication controls; two retained cases per run.

The complete 388-case image-pinning suite remains in its existing test module.
These tests exercise publication, input preservation, and deliberate VM mismatch
receipts. They do not claim new handler coverage or binary equivalence.
"""
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
IMAGES = tuple('evidence/original/' + name + '/deployed.so' for name in ('pump', 'pump_fees', 'pump_amm')) + tuple(
    'evidence/dependencies/' + name + '/deployed.so' for name in ('spl_token', 'spl_token_2022', 'associated_token'))
DRIVER = r'''
import json, os, sys
from pathlib import Path
scripts, directory, mode, output = sys.argv[1:]
sys.path.insert(0, scripts)
import pump_admin_cto_differential as module
import pump_differential_output as publication
root = Path(directory); module.ROOT = root
selected = module.cases()[:2]
module.cases = lambda: selected
completed = []
def hook(frame, event, arg):
    if event == 'return' and frame.f_code.co_name == 'run' and frame.f_code.co_filename == module.__file__:
        completed.append(1)
        if len(completed) == 2 and mode == 'late-alias':
            os.link(root/'candidate.so', output)
sys.setprofile(hook)
if mode == 'fsync-failure':
    def fail(fd): raise OSError('injected publication fsync failure')
    publication.os.fsync = fail
elif mode in ('atomic-replace', 'recreated-stage'):
    replace = publication.os.replace
    def publish(stage, destination):
        data = json.loads(Path(stage).read_bytes())
        assert data['case_count'] == 2 and len(data['cases']) == 2
        assert Path(destination).read_bytes() == b'previous complete receipt'
        replace(stage, destination)
        if mode == 'recreated-stage':
            Path(stage).write_bytes(b'new staging owner')
            (root/'recreated-path.txt').write_text(str(stage))
    publication.os.replace = publish
sys.argv = [module.__file__, '--candidate', str(root/'candidate.so'), '--output', output]
try:
    module.main()
finally:
    sys.setprofile(None)
    (root/'executions.json').write_text(json.dumps(completed))
'''


class PumpAdminCtoReportPublicationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='admin-cto-publication-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name).resolve()
        for name in IMAGES:
            destination = self.root / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, destination)
        upstream = self.root / 'evidence/upstream'; upstream.mkdir()
        for name in ('pump', 'pump_fees', 'pump_amm'):
            shutil.copyfile(ROOT/'evidence/upstream'/(name+'.json'), upstream/(name+'.json'))
        (self.root/'scripts').symlink_to(ROOT/'scripts', target_is_directory=True)
        self.candidate = self.root/'candidate.so'
        shutil.copyfile(ROOT/IMAGES[0], self.candidate)
        self.output = self.root/'reports/output.json'

    def invoke(self, mode='normal', output=None):
        environment = dict(os.environ); environment.pop('PYTHONOPTIMIZE', None)
        return subprocess.run([sys.executable, '-B', '-c', DRIVER, str(ROOT/'scripts'), str(self.root),
                               mode, str(output or self.output)], cwd=ROOT, env=environment,
                              capture_output=True, text=True, timeout=60)

    def executed(self):
        return len(json.loads((self.root/'executions.json').read_bytes()))

    def test_normal_cli_publishes_complete_nested_report(self):
        result = self.invoke()
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        report = json.loads(self.output.read_bytes())
        self.assertEqual(report['case_count'], 2)
        self.assertEqual(report['mismatches'], [])
        self.assertEqual(self.executed(), 4)
        self.assertTrue(all(row['original']['signatures_verified'] and row['candidate']['signatures_verified']
                            for row in report['cases']))
        self.assertTrue(any(row['original']['inner'] for row in report['cases']))

    def test_candidate_and_metadata_aliases_rejected_before_execution(self):
        candidate_before = self.candidate.read_bytes()
        for source in (self.candidate, self.root/'evidence/upstream/pump.json'):
            before = source.read_bytes()
            for kind in ('direct', 'symlink', 'hardlink'):
                with self.subTest(source=source.name, kind=kind):
                    # Keep subtests independent even against the unsafe original.
                    self.candidate.write_bytes(candidate_before)
                    source.write_bytes(before)
                    destination = source if kind == 'direct' else self.root/(source.name+'-'+kind)
                    if kind == 'symlink': destination.symlink_to(source)
                    if kind == 'hardlink': os.link(source, destination)
                    result = self.invoke(output=destination)
                    self.assertNotEqual(result.returncode, 0)
                    self.assertIn('report output aliases an input', result.stderr)
                    self.assertEqual(self.executed(), 0)
                    self.assertEqual(source.read_bytes(), before)

    def test_late_candidate_alias_is_rejected_without_input_loss(self):
        self.output.parent.mkdir()
        before = self.candidate.read_bytes()
        result = self.invoke('late-alias')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('report output aliases an input', result.stderr)
        self.assertEqual(self.executed(), 4)
        self.assertEqual(self.candidate.read_bytes(), before)
        self.assertTrue(self.output.samefile(self.candidate))

    def test_fsync_failure_preserves_previous_report(self):
        self.output.parent.mkdir(); self.output.write_bytes(b'previous complete receipt')
        result = self.invoke('fsync-failure')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('injected publication fsync failure', result.stderr)
        self.assertEqual(self.executed(), 4)
        self.assertEqual(self.output.read_bytes(), b'previous complete receipt')
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_replacement_uses_complete_staged_bytes(self):
        self.output.parent.mkdir(); self.output.write_bytes(b'previous complete receipt')
        result = self.invoke('atomic-replace')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        self.assertEqual(json.loads(self.output.read_bytes())['case_count'], 2)
        self.assertEqual(list(self.output.parent.iterdir()), [self.output])

    def test_consumed_stage_is_not_deleted_after_another_writer_recreates_it(self):
        self.output.parent.mkdir(); self.output.write_bytes(b'previous complete receipt')
        result = self.invoke('recreated-stage')
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)
        recreated = Path((self.root/'recreated-path.txt').read_text())
        self.assertEqual(recreated.read_bytes(), b'new staging owner')
        self.assertEqual(json.loads(self.output.read_bytes())['case_count'], 2)

    def test_wrong_image_publishes_real_mismatch_receipt_and_exits_one(self):
        shutil.copyfile(ROOT/'evidence/original/mayhem/deployed.so', self.candidate)
        result = self.invoke()
        self.assertEqual(result.returncode, 1, result.stdout+result.stderr)
        report = json.loads(self.output.read_bytes())
        self.assertEqual(report['case_count'], 2)
        self.assertTrue(report['mismatches'])
        self.assertEqual(self.executed(), 4)


if __name__ == '__main__':
    unittest.main()
